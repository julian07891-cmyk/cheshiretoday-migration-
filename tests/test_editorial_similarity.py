import ast
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields
import inspect
import logging

import pytest

import backend.app.editorial_similarity as editorial_similarity
from backend.app.editorial_similarity import (
    EditorialSimilarityResult,
    score_editorial_similarity,
)


def article(**overrides):
    record = {
        "id": "existing-id",
        "title": "Council approves homes at former kennels in Hough",
        "summary": (
            "Cheshire East Council approved eight homes at the former kennels "
            "site beside Birchwood House in Hough."
        ),
        "content": (
            "The planning committee gave permission for eight homes at the former "
            "kennels beside Birchwood House. Cheshire East Council considered the "
            "application and contributions for affordable housing."
        ),
        "source": "Publisher One",
        "source_url": "https://one.example/hough-kennels-decision",
        "location": "Hough",
        "publishedDate": "2026-08-02T07:00:00+00:00",
    }
    record.update(overrides)
    return record


def hough_candidate(**overrides):
    record = {
        "id": "candidate-id",
        "title": "Green light for final phase on site of former kennels",
        "summary": (
            "Eight homes have received approval at Birchwood House near Shavington "
            "after a Cheshire East Council planning decision."
        ),
        "content": (
            "Councillors approved the final eight-home scheme at the former kennels "
            "in Hough. The Birchwood House proposal includes an affordable housing "
            "contribution following the planning committee decision."
        ),
        "source": "Publisher Two",
        "source_url": "https://two.example/final-phase-hough?ref=rss",
        "location": "Hough",
        "publishedDate": "2026-08-02T09:10:00+00:00",
    }
    record.update(overrides)
    return record


def unrelated_pair(**candidate_overrides):
    candidate = {
        "title": "Alpha report about a library",
        "summary": "A local library announced new opening hours.",
        "content": "Residents can visit the library on weekday evenings.",
        "source_url": "https://alpha.example/library",
    }
    candidate.update(candidate_overrides)
    existing = {
        "title": "Bravo report about a market",
        "summary": "A town market announced new weekend stalls.",
        "content": "Traders will attend the market on Saturday mornings.",
        "source_url": "https://bravo.example/market",
    }
    return candidate, existing


def test_hough_cross_feed_fixture_remains_likely_at_calibrated_score():
    result = score_editorial_similarity(hough_candidate(), article())

    assert result == EditorialSimilarityResult(
        eligible=True,
        score=79,
        band="likely",
        reasons=(
            "Same named site or locality",
            "Matching distinctive numerical fact",
            "High textual similarity",
            "Shared distinctive terms",
            "Shared named organisation",
        ),
    )


def test_public_result_has_only_approved_immutable_fields():
    result = score_editorial_similarity(hough_candidate(), article())

    assert tuple(field.name for field in fields(result)) == (
        "eligible",
        "score",
        "band",
        "reasons",
    )
    assert not hasattr(result, "matched_article_id")
    with pytest.raises(FrozenInstanceError):
        result.score = 1


@pytest.mark.parametrize(
    ("candidate", "existing"),
    [
        (
            article(
                id="candidate",
                title="Hough school launches breakfast club",
                summary="A primary school in Hough opened a breakfast club.",
                content="Families attended the village school opening.",
                source_url="https://school.example/breakfast",
            ),
            article(),
        ),
        (
            article(
                id="candidate",
                title="Cheshire East Council publishes waste collection dates",
                summary="The council confirmed revised bin collection dates.",
                content="Waste collections change over the bank holiday.",
                source_url="https://council.example/bins",
                location="Crewe",
            ),
            article(),
        ),
        (
            article(
                id="candidate",
                title="Construction starts on eight homes at former Hough kennels",
                summary="Building work began at Birchwood House.",
                content="The approved eight-home scheme is under construction.",
                source_url="https://followup.example/construction",
                publishedDate="2026-08-20T09:00:00+00:00",
            ),
            article(),
        ),
        (
            article(
                id="candidate",
                title="Developer completes access road at former Hough kennels",
                summary="A later update covers the Birchwood House access road.",
                content="Work finished several days after the housing approval.",
                source_url="https://followup.example/access-road",
                publishedDate="2026-08-09T09:00:00+00:00",
            ),
            article(),
        ),
        (
            article(
                id="candidate",
                title="National housing policy receives a Cheshire response",
                summary="A councillor commented on national housing policy.",
                content="The announcement covers planning policy across England.",
                source_url="https://national.example/housing-policy",
                location="Cheshire",
            ),
            article(),
        ),
    ],
)
def test_negative_fixtures_remain_below_likely(candidate, existing):
    result = score_editorial_similarity(candidate, existing)

    assert result.band in {"low", "possible"}
    assert result.score < 70


def test_exact_normalised_title_is_ineligible_without_returning_identity():
    candidate = article(
        id="candidate-secret",
        title="  COUNCIL approves homes at former kennels in Hough  ",
        source_url="https://different.example/story",
    )

    assert score_editorial_similarity(
        candidate, article()
    ) == EditorialSimilarityResult(
        eligible=False,
        score=0,
        band="ineligible",
        reasons=(),
    )


def test_exact_canonical_source_url_is_ineligible():
    candidate = article(
        title="A completely different publisher headline",
        source_url=(
            "https://one.example/hough-kennels-decision"
            "?utm_medium=social&fbclid=tracking#top"
        ),
    )

    result = score_editorial_similarity(candidate, article())

    assert result.eligible is False
    assert result.band == "ineligible"
    assert result.score == 0
    assert result.reasons == ()


@pytest.mark.parametrize("field", ["title", "source_url"])
def test_equal_non_string_identity_values_are_ignored(field):
    candidate, existing = unrelated_pair()
    candidate[field] = 123
    existing[field] = 123

    result = score_editorial_similarity(candidate, existing)

    assert result.eligible is True
    assert result.band != "ineligible"


def test_matching_object_representations_do_not_trigger_exact_duplicate():
    class MatchingRepresentation:
        def __repr__(self):
            return "matching"

    candidate, existing = unrelated_pair(
        title=MatchingRepresentation(), source_url=MatchingRepresentation()
    )
    existing["title"] = MatchingRepresentation()
    existing["source_url"] = MatchingRepresentation()

    assert score_editorial_similarity(candidate, existing).eligible is True


def test_punctuation_change_is_not_a_version_one_exact_title():
    candidate = article(
        title="Council approves homes: at former kennels in Hough",
        source_url="https://other.example/different",
    )

    assert score_editorial_similarity(candidate, article()).eligible is True


@pytest.mark.parametrize(
    ("field", "limit"),
    [
        ("title", 300),
        ("summary", 2_000),
        ("content", 4_000),
    ],
)
def test_text_after_each_independent_field_bound_cannot_change_score(field, limit):
    candidate, existing = unrelated_pair()
    prefix = "x" * limit
    candidate[field] = prefix
    existing[field] = "different bounded value"
    baseline = score_editorial_similarity(candidate, existing)

    candidate[field] = prefix + " shared planning reference 24/1234N"
    existing[field] += " shared planning reference 24/1234N"

    assert score_editorial_similarity(candidate, existing) == baseline


def test_field_bounds_are_independent_and_content_is_not_consumed_by_prior_fields():
    candidate, existing = unrelated_pair()
    candidate.update(
        title="a" * 300,
        summary="b" * 2_000,
        content="Planning reference 24/1234N appears in the bounded content.",
    )
    existing.update(
        title="c" * 300,
        summary="d" * 2_000,
        content="Application 24/1234N was considered independently.",
    )

    result = score_editorial_similarity(candidate, existing)

    assert result.score >= 30
    assert "24/1234N" in editorial_similarity._article_text(candidate)
    assert "24/1234N" in editorial_similarity._article_text(existing)


def test_tokenisation_is_capped_at_600_tokens():
    tokens = editorial_similarity._tokens(
        " ".join(f"t{index}" for index in range(1_000))
    )

    assert len(tokens) == 600


def test_mapping_get_failure_returns_safe_fallback_without_leaking(caplog):
    class FailingMapping(dict):
        def get(self, *_args, **_kwargs):
            raise RuntimeError("secret body")

    with caplog.at_level(logging.DEBUG):
        result = score_editorial_similarity(FailingMapping(), {})

    assert result == EditorialSimilarityResult(True, 0, "low", ())
    assert "secret body" not in repr(result)
    assert "secret body" not in caplog.text


def test_failing_string_conversion_is_ignored_without_leaking(caplog):
    class FailingString:
        def __str__(self):
            raise RuntimeError("secret body")

    candidate, existing = unrelated_pair(
        title=FailingString(),
        summary=FailingString(),
        content=FailingString(),
        source_url=FailingString(),
        publishedDate=FailingString(),
    )

    with caplog.at_level(logging.DEBUG):
        result = score_editorial_similarity(candidate, existing)

    assert result.eligible is True
    assert result.band == "low"
    assert "secret body" not in repr(result)
    assert "secret body" not in caplog.text


def test_missing_and_malformed_fields_return_a_valid_deterministic_result():
    candidate = {"title": None, "content": object(), "publishedDate": "not-a-date"}
    existing = {"_id": 123, "summary": None, "source_url": "not a url"}

    first = score_editorial_similarity(candidate, existing)
    second = score_editorial_similarity(candidate, existing)

    assert first == second == EditorialSimilarityResult(True, 0, "low", ())


def test_input_records_are_not_mutated():
    candidate = hough_candidate(tags=["Local News"])
    existing = article(metadata={"nested": True})
    candidate_before = deepcopy(candidate)
    existing_before = deepcopy(existing)

    score_editorial_similarity(candidate, existing)

    assert candidate == candidate_before
    assert existing == existing_before


def test_score_band_and_reasons_are_bounded_and_allow_listed():
    allowed = {
        "Matching planning or application reference",
        "Same named site or locality",
        "Matching distinctive numerical fact",
        "High headline overlap",
        "Meaningful headline overlap",
        "High textual similarity",
        "Meaningful textual similarity",
        "Shared distinctive terms",
        "Shared named organisation",
        "Published within six hours",
    }
    result = score_editorial_similarity(hough_candidate(), article())

    assert isinstance(result.score, int)
    assert 0 <= result.score <= 100
    assert result.band in {
        "ineligible",
        "low",
        "possible",
        "likely",
        "very_likely",
    }
    assert isinstance(result.reasons, tuple)
    assert len(result.reasons) <= 5
    assert len(result.reasons) == len(set(result.reasons))
    assert set(result.reasons) <= allowed


def test_image_fields_have_no_influence():
    candidate = hough_candidate(image="https://images.example/first.jpg")
    existing = article(image="https://images.example/second.jpg")
    baseline = score_editorial_similarity(candidate, existing)

    candidate["image"] = object()
    existing["image"] = "secret-image-value"

    assert score_editorial_similarity(candidate, existing) == baseline


def test_module_has_no_runtime_database_network_provider_or_file_dependencies():
    source = inspect.getsource(editorial_similarity)
    tree = ast.parse(source)
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    assert imported_roots.isdisjoint(
        {
            "backend",
            "motor",
            "pymongo",
            "requests",
            "httpx",
            "aiohttp",
            "openai",
            "anthropic",
            "PIL",
            "cv2",
            "imagehash",
            "pathlib",
        }
    )
    lowered = source.casefold()
    assert "os.environ" not in lowered
    assert "open(" not in lowered
    assert "urlopen" not in lowered
    assert "mongo" not in lowered
    assert "database" not in lowered
