import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from backend.app import editorial_similarity_shadow as shadow
from backend.app.editorial_similarity import EditorialSimilarityResult


def existing_article(**overrides):
    article = {
        "_id": "existing-id",
        "_editorial_similarity_provenance": "active",
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
        "source_url": "https://one.example/hough",
        "location": "Hough",
        "publishedDate": "2026-08-02T07:00:00+00:00",
    }
    article.update(overrides)
    return article


def candidate_article(**overrides):
    article = {
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
        "source_url": "https://two.example/final-phase",
        "location": "Hough",
        "publishedDate": "2026-08-02T09:10:00+00:00",
    }
    article.update(overrides)
    return article


class RecordingCollection:
    def __init__(self, *, failure=None):
        self.failure = failure
        self.inserted = []

    async def insert_one(self, article):
        self.inserted.append(deepcopy(article))
        if self.failure:
            raise self.failure
        return SimpleNamespace(inserted_id="candidate-id")


class RecordingLogger:
    def __init__(self, *, fail=False):
        self.fail = fail
        self.messages = []

    def info(self, message):
        if self.fail:
            raise RuntimeError("logger failure")
        self.messages.append(message)


def _log_fields(message):
    parts = message.split()
    assert parts[0] == "editorial_similarity_shadow"
    return dict(part.split("=", 1) for part in parts[1:])


def test_snapshot_is_independently_bounded_and_excludes_unapproved_fields():
    original = {
        "title": "t" * 500,
        "summary": "s" * 2_500,
        "content": "c" * 4_500,
        "source_url": "u" * 3_000,
        "location": "l" * 500,
        "priority_location": "p" * 500,
        "publishedDate": "d" * 500,
        "image": "secret-image",
        "manual_review_reason": "secret-review-state",
    }
    before = deepcopy(original)

    snapshot = shadow.bounded_article_snapshot(original)

    assert original == before
    assert len(snapshot["title"]) == 300
    assert len(snapshot["summary"]) == 2_000
    assert len(snapshot["content"]) == 4_000
    assert len(snapshot["source_url"]) == 2_048
    assert len(snapshot["location"]) == 300
    assert len(snapshot["priority_location"]) == 300
    assert len(snapshot["publishedDate"]) == 128
    assert "image" not in snapshot
    assert "manual_review_reason" not in snapshot


def test_shortlist_and_scorer_calls_are_capped_at_twenty(monkeypatch):
    records = [
        existing_article(
            _id=f"record-{index:02d}",
            source_url=f"https://example.test/{index}",
            publishedDate=f"2026-08-{index % 28 + 1:02d}T07:00:00+00:00",
        )
        for index in range(60)
    ]
    calls = []

    def fake_score(candidate, existing):
        calls.append(existing["source_url"])
        return EditorialSimilarityResult(True, 50, "possible", ())

    monkeypatch.setattr(shadow, "score_editorial_similarity", fake_score)
    evaluation = shadow.EditorialSimilarityShadowEvaluator(records).evaluate(
        candidate_article()
    )

    assert evaluation.comparison_count == 60
    assert evaluation.shortlist_count == shadow.SHORTLIST_LIMIT
    assert len(calls) == shadow.SHORTLIST_LIMIT


def test_shortlist_order_is_deterministic_and_uses_newest_then_id(monkeypatch):
    records = [
        existing_article(
            _id=article_id,
            publishedDate=published,
            source_url=f"https://example.test/{article_id}",
        )
        for article_id, published in (
            ("older", "2026-08-01T08:00:00+00:00"),
            ("z-id", "2026-08-03T08:00:00+00:00"),
            ("a-id", "2026-08-03T08:00:00+00:00"),
        )
    ]
    calls = []

    def fake_score(candidate, existing):
        calls.append(existing["source_url"].rsplit("/", 1)[-1])
        return EditorialSimilarityResult(True, 50, "possible", ())

    monkeypatch.setattr(shadow, "score_editorial_similarity", fake_score)
    evaluator = shadow.EditorialSimilarityShadowEvaluator(records)
    evaluator.evaluate(candidate_article())
    first = list(calls)
    calls.clear()
    evaluator.evaluate(candidate_article())

    assert first == ["a-id", "z-id", "older"]
    assert calls == first


def test_generic_news_words_do_not_shortlist_every_record(monkeypatch):
    calls = []
    monkeypatch.setattr(
        shadow,
        "score_editorial_similarity",
        lambda candidate, existing: calls.append(existing)
        or EditorialSimilarityResult(True, 0, "low", ()),
    )
    records = [
        existing_article(
            _id=f"generic-{index}",
            title="Cheshire local council news report",
            summary="Local news story announced by council",
            content="A report about Cheshire news.",
            location="Cheshire",
            source_url=f"https://example.test/generic-{index}",
        )
        for index in range(40)
    ]

    evaluation = shadow.EditorialSimilarityShadowEvaluator(records).evaluate(
        candidate_article(
            title="Cheshire council news report",
            summary="Local news article",
            content="The Cheshire story was reported.",
            location="Cheshire",
        )
    )

    assert evaluation.shortlist_count == 0
    assert calls == []


def test_hough_cross_feed_fixture_reaches_shortlist_and_likely_band():
    evaluation = shadow.EditorialSimilarityShadowEvaluator(
        [existing_article()]
    ).evaluate(candidate_article())

    assert evaluation.shortlist_count == 1
    assert evaluation.band == "likely"
    assert evaluation.score == 79
    assert evaluation.matched_article_id == "existing-id"
    assert evaluation.matched_provenance == "active"


@pytest.mark.parametrize(
    ("candidate_text", "existing_text", "minimum_score"),
    (
        ("Reference 24/1234N.", "Planning application no. 24/1234N.", 100),
        ("47 apartments.", "47 apartments.", 70),
    ),
)
def test_planning_reference_and_distinctive_fact_reach_shortlist(
    candidate_text, existing_text, minimum_score
):
    existing = existing_article(
        title="Separate headline about an application",
        summary=existing_text,
        content="Different supporting words.",
        location="",
    )
    candidate = candidate_article(
        title="Another publisher covers the decision",
        summary=candidate_text,
        content="Unrelated vocabulary otherwise.",
        location="",
    )

    evaluation = shadow.EditorialSimilarityShadowEvaluator([existing]).evaluate(
        candidate
    )

    assert evaluation.shortlist_count == 1
    assert shadow._shortlist_score(candidate, existing) >= minimum_score


def test_selection_uses_score_then_band_then_time_then_id(monkeypatch):
    records = [
        existing_article(
            _id=article_id,
            source_url=f"https://example.test/{article_id}",
            publishedDate=published,
        )
        for article_id, published in (
            ("lower-score", "2026-08-04T00:00:00+00:00"),
            ("lower-band", "2026-08-04T00:00:00+00:00"),
            ("older", "2026-08-02T00:00:00+00:00"),
            ("z-id", "2026-08-03T00:00:00+00:00"),
            ("a-id", "2026-08-03T00:00:00+00:00"),
        )
    ]
    results = {
        "lower-score": (79, "likely"),
        "lower-band": (80, "possible"),
        "older": (80, "likely"),
        "z-id": (80, "likely"),
        "a-id": (80, "likely"),
    }

    def fake_score(candidate, existing):
        article_id = existing["source_url"].rsplit("/", 1)[-1]
        score, band = results[article_id]
        return EditorialSimilarityResult(True, score, band, ())

    monkeypatch.setattr(shadow, "score_editorial_similarity", fake_score)
    evaluation = shadow.EditorialSimilarityShadowEvaluator(records).evaluate(
        candidate_article()
    )

    assert evaluation.matched_article_id == "a-id"


def test_ineligible_cannot_displace_meaningful_eligible_match(monkeypatch):
    records = [
        existing_article(_id="exact", source_url="https://example.test/exact"),
        existing_article(_id="useful", source_url="https://example.test/useful"),
    ]

    def fake_score(candidate, existing):
        if existing["source_url"].endswith("/exact"):
            return EditorialSimilarityResult(False, 0, "ineligible", ())
        return EditorialSimilarityResult(True, 70, "likely", ())

    monkeypatch.setattr(shadow, "score_editorial_similarity", fake_score)
    evaluation = shadow.EditorialSimilarityShadowEvaluator(records).evaluate(
        candidate_article()
    )

    assert evaluation.matched_article_id == "useful"
    assert evaluation.eligible is True


def test_provenance_is_allow_listed_and_same_run_is_added_after_success():
    evaluator = shadow.EditorialSimilarityShadowEvaluator(
        [
            existing_article(
                _id="archived-id",
                _editorial_similarity_provenance="archived",
            )
        ]
    )
    archived = evaluator.evaluate(candidate_article())
    assert archived.matched_provenance == "archived"

    evaluator = shadow.EditorialSimilarityShadowEvaluator(
        [
            existing_article(
                _id="archived-id",
                _editorial_similarity_provenance="archived",
                title="Library opening hours change",
                summary="The city library will open later.",
                content="Readers can visit on weekday evenings.",
                source_url="https://example.test/library",
                location="Chester",
            )
        ]
    )
    evaluator.add(existing_article(), "same-run-id", provenance="same_run")
    same_run = evaluator.evaluate(
        candidate_article(title="A later report about the former kennels")
    )
    assert same_run.matched_provenance == "same_run"


def test_missing_or_unsafe_ids_are_excluded_without_calling_custom_str(monkeypatch):
    class SecretIdentifier:
        def __str__(self):
            raise AssertionError("secret identifier conversion must not run")

    calls = []
    monkeypatch.setattr(
        shadow,
        "score_editorial_similarity",
        lambda candidate, existing: calls.append(existing)
        or EditorialSimilarityResult(True, 70, "likely", ()),
    )
    evaluator = shadow.EditorialSimilarityShadowEvaluator(
        [
            existing_article(_id=None),
            existing_article(_id=SecretIdentifier()),
            existing_article(_id="safe-id"),
        ]
    )

    evaluation = evaluator.evaluate(candidate_article())

    assert evaluator.pool_size == 1
    assert evaluation.matched_article_id == "safe-id"
    assert len(calls) == 1


def test_snapshot_failure_skips_only_the_malformed_record():
    class BrokenRecord(dict):
        def get(self, *_args, **_kwargs):
            raise RuntimeError("unsafe snapshot detail")

    evaluator = shadow.EditorialSimilarityShadowEvaluator(
        [BrokenRecord(), existing_article()]
    )

    assert evaluator.pool_size == 1
    assert evaluator.evaluate(candidate_article()).matched_article_id == "existing-id"


def test_corpus_cap_evicts_genuinely_oldest_record():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    records = [
        existing_article(
            _id=f"record-{index:03d}",
            publishedDate=start + timedelta(hours=index),
            source_url=f"https://example.test/{index}",
        )
        for index in range(shadow.COMPARISON_POOL_LIMIT)
    ]
    evaluator = shadow.EditorialSimilarityShadowEvaluator(records)
    evaluator.add(
        existing_article(
            publishedDate=start + timedelta(hours=200),
            source_url="https://example.test/newest",
        ),
        "newest",
    )

    assert evaluator.pool_size == shadow.COMPARISON_POOL_LIMIT
    assert [record.article_id for record in evaluator._records][0] == "record-001"
    assert [record.article_id for record in evaluator._records][-1] == "newest"


def test_candidate_cannot_match_itself(monkeypatch):
    calls = []
    monkeypatch.setattr(
        shadow,
        "score_editorial_similarity",
        lambda candidate, existing: calls.append(existing)
        or EditorialSimilarityResult(True, 70, "likely", ()),
    )
    evaluator = shadow.EditorialSimilarityShadowEvaluator(
        [existing_article(_id="candidate-id")]
    )

    evaluation = evaluator.evaluate(candidate_article(_id="candidate-id"))

    assert evaluation.shortlist_count == 0
    assert calls == []


def test_log_has_exact_allow_listed_schema_and_safe_values():
    evaluation = shadow.EditorialSimilarityShadowEvaluator(
        [existing_article()]
    ).evaluate(candidate_article())
    fields = _log_fields(
        shadow.format_shadow_log(
            evaluation,
            candidate_article_id="candidate-id",
            context="local_rss",
        )
    )

    assert set(fields) == {
        "status",
        "context",
        "candidate_article_id",
        "matched_article_id",
        "matched_provenance",
        "eligible",
        "score",
        "band",
        "comparison_count",
        "shortlist_count",
        "reason_codes",
        "scorer_version",
        "shadow_mode",
    }
    assert fields["context"] == "local_rss"
    assert fields["matched_provenance"] == "active"
    assert int(fields["score"]) in range(101)
    assert int(fields["comparison_count"]) in range(101)
    assert int(fields["shortlist_count"]) in range(21)
    assert fields["band"] in shadow.ALLOWED_BANDS


def test_invalid_log_values_are_normalised_without_custom_string_leakage():
    class SecretValue:
        def __str__(self):
            return "secretvalue"

    evaluation = shadow.EditorialSimilarityShadowEvaluation(
        eligible="unsafe",
        score=1_000,
        band="secret-band",
        reason_codes=("secret-reason", "location"),
        comparison_count=1_000,
        shortlist_count=1_000,
        matched_article_id="unsafe id",
        matched_provenance="secret-source",
    )
    message = shadow.format_shadow_log(
        evaluation,
        candidate_article_id=SecretValue(),
        context="secret-context",
    )
    fields = _log_fields(message)

    assert "secretvalue" not in message
    assert "secret-band" not in message
    assert "secret-reason" not in message
    assert fields["candidate_article_id"] == "none"
    assert fields["matched_article_id"] == "none"
    assert fields["matched_provenance"] == "none"
    assert fields["context"] == "unknown"
    assert fields["band"] == "low"
    assert fields["score"] == "0"
    assert fields["comparison_count"] == "100"
    assert fields["shortlist_count"] == "20"


def test_no_match_log_is_emitted_after_successful_insert():
    evaluator = shadow.EditorialSimilarityShadowEvaluator([])
    collection = RecordingCollection()
    logger = RecordingLogger()

    asyncio.run(
        shadow.insert_with_editorial_similarity_shadow(
            collection,
            candidate_article(),
            context="category_rss",
            evaluator=evaluator,
            logger=logger,
        )
    )

    fields = _log_fields(logger.messages[0])
    assert len(collection.inserted) == 1
    assert fields["status"] == "no_match"
    assert fields["matched_article_id"] == "none"
    assert fields["shortlist_count"] == "0"


def test_ineligible_result_does_not_block_or_add_article_metadata():
    article = candidate_article()
    before = deepcopy(article)
    evaluator = shadow.EditorialSimilarityShadowEvaluator(
        [candidate_article(_id="existing-id")]
    )
    collection = RecordingCollection()
    logger = RecordingLogger()

    asyncio.run(
        shadow.insert_with_editorial_similarity_shadow(
            collection,
            article,
            context="category_rss",
            evaluator=evaluator,
            logger=logger,
        )
    )

    assert collection.inserted == [before]
    assert article == before
    assert "editorial_similarity" not in article


def test_disabled_shadow_is_exactly_one_insert_and_no_log():
    collection = RecordingCollection()
    logger = RecordingLogger()

    asyncio.run(
        shadow.insert_with_editorial_similarity_shadow(
            collection,
            candidate_article(),
            context="local_rss",
            evaluator=None,
            logger=logger,
        )
    )

    assert len(collection.inserted) == 1
    assert logger.messages == []


def test_scorer_failure_logs_bounded_no_match_and_still_inserts(monkeypatch):
    evaluator = shadow.EditorialSimilarityShadowEvaluator([existing_article()])
    monkeypatch.setattr(
        shadow,
        "score_editorial_similarity",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("secret body")),
    )
    collection = RecordingCollection()
    logger = RecordingLogger()

    result = asyncio.run(
        shadow.insert_with_editorial_similarity_shadow(
            collection,
            candidate_article(),
            context="local_rss",
            evaluator=evaluator,
            logger=logger,
        )
    )

    assert result.inserted_id == "candidate-id"
    assert len(collection.inserted) == 1
    fields = _log_fields(logger.messages[0])
    assert fields["status"] == "no_match"
    assert fields["score"] == "0"


def test_logger_failure_is_non_fatal_and_does_not_retry_insert():
    collection = RecordingCollection()

    result = asyncio.run(
        shadow.insert_with_editorial_similarity_shadow(
            collection,
            candidate_article(),
            context="local_rss",
            evaluator=shadow.EditorialSimilarityShadowEvaluator([existing_article()]),
            logger=RecordingLogger(fail=True),
        )
    )

    assert result.inserted_id == "candidate-id"
    assert len(collection.inserted) == 1


def test_failed_insert_is_not_logged_or_added_to_corpus():
    evaluator = shadow.EditorialSimilarityShadowEvaluator([existing_article()])
    initial_size = evaluator.pool_size
    collection = RecordingCollection(failure=RuntimeError("insert failed"))
    logger = RecordingLogger()

    with pytest.raises(RuntimeError, match="insert failed"):
        asyncio.run(
            shadow.insert_with_editorial_similarity_shadow(
                collection,
                candidate_article(),
                context="cheshire_fallback",
                evaluator=evaluator,
                logger=logger,
            )
        )

    assert evaluator.pool_size == initial_size
    assert logger.messages == []
