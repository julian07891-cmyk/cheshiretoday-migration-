import copy
import inspect
import json
import subprocess
import sys
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from backend.app.news_feed_service import RSS_FEEDS
from backend.scripts import evaluate_story_ranking_shadow as ranking


AS_OF = datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc)


def payload(candidate_id="one", **overrides):
    value = {
        "candidate_id": candidate_id,
        "title": "Northwich council approves town centre investment",
        "source": "Independent Northwich",
        "source_url": f"https://example.test/{candidate_id}?utm_source=rss",
        "published_at": "2026-07-23T10:00:00Z",
        "category": "Local News",
        "is_local_source": True,
        "locality": "town",
        "originality": "original",
        "business_value": 3,
        "editorial_fit": 3,
        "publisher_type": "independent",
        "syndication": "none",
        "has_image": True,
        "image_width": 1200,
        "image_height": 675,
        "current_importer_selected": False,
        "assessment_source": "fixture",
    }
    value.update(overrides)
    return value


def candidate(candidate_id="one", **overrides):
    return ranking.parse_candidate(payload(candidate_id, **overrides))


def test_import_isolation_and_zero_write_surface():
    source = inspect.getsource(ranking)
    for forbidden in (
        "backend.server",
        "pymongo",
        "motor",
        "httpx",
        "requests",
        "insert_one",
        "update_one",
        "delete_one",
    ):
        assert forbidden not in source
    assert not any(
        hasattr(ranking, name)
        for name in ("db", "database", "articles", "mongo_client", "feed_service")
    )


def test_models_are_immutable():
    item = candidate()
    with pytest.raises(FrozenInstanceError):
        item.title = "changed"
    weights = ranking.RankingWeights()
    with pytest.raises(FrozenInstanceError):
        weights.original_reporting = 99


@pytest.mark.parametrize(
    "field, value",
    [
        ("candidate_id", ""),
        ("title", ""),
        ("source", ""),
        ("published_at", "not-a-date"),
        ("published_at", "2026-07-23T10:00:00"),
        ("is_local_source", 1),
        ("has_image", "true"),
        ("current_importer_selected", 0),
        ("business_value", True),
        ("business_value", 4),
        ("editorial_fit", -1),
        ("image_width", True),
        ("image_height", 0),
        ("originality", "invented"),
        ("locality", "street"),
        ("publisher_type", "blog"),
        ("syndication", "maybe"),
        ("assessment_source", "guess"),
    ],
)
def test_candidate_validation(field, value):
    with pytest.raises(ranking.ShadowRankingError):
        ranking.parse_candidate(payload(**{field: value}))


def test_weights_are_configurable_and_strict():
    weights = ranking.RankingWeights.from_mapping({"original_reporting": 50})
    assert weights.original_reporting == 50
    assert weights.town_locality == ranking.RankingWeights().town_locality
    with pytest.raises(ranking.ShadowRankingError):
        ranking.RankingWeights.from_mapping({"unknown": 1})
    with pytest.raises(ranking.ShadowRankingError):
        ranking.RankingWeights.from_mapping({"original_reporting": True})


@pytest.mark.parametrize(
    "left, right",
    [
        ({"story_key": "same"}, {"story_key": "same"}),
        (
            {"source_url": "https://example.test/story?ref=rss"},
            {"source_url": "https://example.test/story?utm_source=feed"},
        ),
        (
            {"title": "Northwich council approves railway investment"},
            {"title": "Northwich council approves railway investment"},
        ),
        (
            {"title": "Northwich council approves major railway investment plan"},
            {"title": "Northwich council backs major railway investment plan"},
        ),
    ],
)
def test_related_story_grouping(left, right):
    first = candidate("one", **left)
    second = candidate("two", **right)
    assert len(ranking.group_candidates((first, second))) == 1


def test_group_report_explains_grouping_signal():
    first = candidate("one", story_key="same")
    second = candidate("two", story_key="same")
    group = ranking.evaluate((first, second), as_of=AS_OF)["groups"][0]
    assert group["grouping_signals"] == [
        {
            "candidate_ids": ["one", "two"],
            "evidence": [
                {"signal": "explicit story_key", "strength": "hard"},
                {"signal": "exact normalized title", "strength": "hard"},
            ],
        }
    ]
    assert group["grouping_basis"] == "hard"


def test_probable_similarity_is_reported_as_heuristic():
    first = candidate(
        "one",
        title="Northwich council approves major railway investment plan",
    )
    second = candidate(
        "two",
        title="Northwich council backs major railway investment plan",
    )
    group = ranking.evaluate((first, second), as_of=AS_OF)["groups"][0]
    assert group["grouping_basis"] == "heuristic"
    assert group["grouping_signals"][0]["evidence"] == [
        {"signal": "probable similar headline", "strength": "heuristic"}
    ]


def test_probable_similarity_does_not_bridge_unrelated_endpoints():
    first = candidate(
        "a",
        title=(
            "Northwich council approves major railway investment "
            "and town centre regeneration"
        ),
    )
    bridge = candidate(
        "b",
        title=(
            "Northwich council approves major railway investment "
            "and town centre housing regeneration"
        ),
    )
    last = candidate(
        "c",
        title=(
            "Northwich council backs major housing investment "
            "and town centre housing regeneration"
        ),
    )
    groups = ranking.group_candidates((first, bridge, last))
    assert sorted(len(group) for group in groups) == [1, 2]
    assert not any(
        {item.candidate_id for item in group} == {"a", "b", "c"} for group in groups
    )


def test_hard_grouping_can_bridge_hard_relations():
    first = candidate("a", story_key="shared")
    bridge = candidate(
        "b",
        story_key="shared",
        source_url="https://example.test/shared",
    )
    last = candidate("c", source_url="https://example.test/shared")
    groups = ranking.group_candidates((first, bridge, last))
    assert len(groups) == 1
    assert {item.candidate_id for item in groups[0]} == {"a", "b", "c"}


def test_unrelated_stories_remain_separate():
    first = candidate("one")
    second = candidate(
        "two",
        title="Widnes hospital opens a new diagnostic centre",
        source_url="https://other.test/hospital",
    )
    assert len(ranking.group_candidates((first, second))) == 2


def test_current_importer_score_mirrors_transparent_current_factors():
    item = candidate(category="Business")
    score, factors = ranking.current_importer_score(item)
    assert score == 7
    assert {factor["factor"] for factor in factors} == {
        "local_source",
        "priority_category",
        "economic_title",
    }


def test_all_shadow_factors_are_reported_even_when_zero():
    score, factors = ranking.shadow_score(
        candidate(), as_of=AS_OF, weights=ranking.RankingWeights()
    )
    assert score > 0
    assert [factor["factor"] for factor in factors] == [
        "original_reporting",
        "locality",
        "business_value",
        "editorial_fit",
        "image_quality",
        "freshness",
        "syndication",
        "publisher_type",
        "source_url",
    ]


def test_original_local_fresh_independent_story_beats_syndicated_version():
    current = candidate(
        "current",
        source="County Group",
        originality="syndicated",
        locality="cheshire",
        publisher_type="established",
        syndication="syndicated",
        business_value=2,
        current_importer_selected=True,
        story_key="investment",
    )
    independent = candidate(
        "preferred",
        source="Independent Northwich",
        story_key="investment",
    )
    report = ranking.evaluate((current, independent), as_of=AS_OF)
    group = report["groups"][0]
    assert group["current_importer_choice"] == "current"
    assert group["shadow_preferred_choice"] == "preferred"
    assert group["choice_changed"] is True
    assert group["score_margin"] > 0


def test_explicit_current_choice_is_used_when_present():
    current = candidate("current", current_importer_selected=True, story_key="same")
    other = candidate("other", story_key="same")
    group = ranking.evaluate((current, other), as_of=AS_OF)["groups"][0]
    assert group["current_choice_basis"] == "input marker"
    assert group["current_importer_choice"] == "current"


def test_current_choice_is_simulated_stably_when_marker_absent():
    first = candidate("first", story_key="same")
    second = candidate("second", story_key="same")
    group = ranking.evaluate((first, second), as_of=AS_OF)["groups"][0]
    assert group["current_choice_basis"] == "simulated current stable score"
    assert group["current_importer_choice"] == "first"
    assert group["current_choice_ordering_tiebreak"] is True
    assert group["current_choice_tied_candidate_ids"] == ["first", "second"]
    assert "input position 0" in group["current_choice_ordering_note"]
    positions = {
        item["candidate_id"]: item["input_position"] for item in group["candidates"]
    }
    assert positions == {"first": 0, "second": 1}


def test_reordering_exposes_current_order_effect_but_not_shadow_winner_or_group_id():
    first = candidate("first", story_key="same")
    second = candidate("second", story_key="same")
    original = ranking.evaluate((first, second), as_of=AS_OF)["groups"][0]
    reordered = ranking.evaluate((second, first), as_of=AS_OF)["groups"][0]
    assert original["group_id"] == reordered["group_id"]
    assert original["shadow_preferred_choice"] == reordered["shadow_preferred_choice"]
    assert original["current_importer_choice"] == "first"
    assert reordered["current_importer_choice"] == "second"
    assert original["current_choice_ordering_tiebreak"] is True
    assert reordered["current_choice_ordering_tiebreak"] is True
    assert "input position 0" in reordered["current_choice_ordering_note"]


def test_multiple_explicit_current_choices_in_group_fail_safely():
    with pytest.raises(ranking.ShadowRankingError):
        ranking.evaluate(
            (
                candidate("one", story_key="same", current_importer_selected=True),
                candidate("two", story_key="same", current_importer_selected=True),
            ),
            as_of=AS_OF,
        )


@pytest.mark.parametrize(
    "overrides, factor, expected_detail",
    [
        (
            {"has_image": False, "image_width": None, "image_height": None},
            "image_quality",
            "missing",
        ),
        ({"published_at": "2026-07-24T10:00:00Z"}, "freshness", "future dated"),
        ({"syndication": "ldrs"}, "syndication", "ldrs"),
        ({"source_url": ""}, "source_url", "missing or invalid"),
    ],
)
def test_diagnostics_explain_penalties(overrides, factor, expected_detail):
    _, factors = ranking.shadow_score(
        candidate(**overrides), as_of=AS_OF, weights=ranking.RankingWeights()
    )
    found = next(item for item in factors if item["factor"] == factor)
    assert found["detail"] == expected_detail
    assert found["value"] < 0


def test_output_is_deterministic_and_json_serialisable():
    candidates = (
        candidate("one", story_key="same"),
        candidate("two", story_key="same", published_at="2026-07-23T09:00:00Z"),
    )
    first = ranking.evaluate(candidates, as_of=AS_OF)
    second = ranking.evaluate(candidates, as_of=AS_OF)
    assert first == second
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_tie_breaker_is_freshness_then_candidate_id():
    older = candidate("z", story_key="same", published_at="2026-07-23T08:00:00Z")
    newer = candidate("a", story_key="same", published_at="2026-07-23T10:00:00Z")
    preferred = ranking.evaluate((older, newer), as_of=AS_OF)["groups"][0][
        "shadow_preferred_choice"
    ]
    assert preferred == "a"


def test_duplicate_candidate_ids_and_empty_input_are_rejected():
    with pytest.raises(ranking.ShadowRankingError):
        ranking.evaluate((), as_of=AS_OF)
    with pytest.raises(ranking.ShadowRankingError):
        ranking.evaluate((candidate("same"), candidate("same")), as_of=AS_OF)


def test_report_has_explicit_zero_write_diagnostics():
    report = ranking.evaluate((candidate(),), as_of=AS_OF)
    assert report["database_writes"] == 0
    assert report["production_importer_calls"] == 0
    assert "local-target" in report["current_importer_model"]


def test_configuration_preservation_contract():
    before = copy.deepcopy(RSS_FEEDS)
    ranking.evaluate((candidate(),), as_of=AS_OF)
    assert RSS_FEEDS == before


@pytest.mark.parametrize(
    "assessment_source",
    ["manual_review", "feed_metadata", "rule_based", "fixture"],
)
def test_assessment_provenance_is_required_and_reported(assessment_source):
    item = candidate(
        assessment_source=assessment_source,
        assessment_note="Concise evidence summary",
    )
    reported = ranking.evaluate((item,), as_of=AS_OF)["groups"][0]["candidates"][0]
    assert reported["assessment_source"] == assessment_source
    assert reported["assessment_note"] == "Concise evidence summary"


def test_missing_unknown_and_excessive_assessment_provenance_is_rejected():
    missing = payload()
    missing.pop("assessment_source")
    with pytest.raises(ranking.ShadowRankingError):
        ranking.parse_candidate(missing)
    with pytest.raises(ranking.ShadowRankingError):
        ranking.parse_candidate(payload(assessment_note="x" * 161))
    with pytest.raises(ranking.ShadowRankingError):
        ranking.parse_candidate(payload(assessment_note="line one\nline two"))


@pytest.mark.parametrize(
    "field",
    ["article_body", "body", "content", "description", "raw_content", "summary"],
)
def test_article_body_fields_are_rejected(field):
    with pytest.raises(ranking.ShadowRankingError, match="body fields"):
        ranking.parse_candidate(payload(**{field: "publisher content"}))


def test_input_loader_accepts_array_and_wrapped_array():
    assert len(ranking.load_input([payload()])) == 1
    assert len(ranking.load_input({"candidates": [payload()]})) == 1
    with pytest.raises(ranking.ShadowRankingError):
        ranking.load_input({})


def test_module_cli_help_succeeds():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "backend.scripts.evaluate_story_ranking_shadow",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--input" in result.stdout
    assert "--as-of" in result.stdout


def test_cli_generates_json_report_from_offline_snapshot(tmp_path):
    snapshot = tmp_path / "candidates.json"
    snapshot.write_text(json.dumps([payload()]), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "backend.scripts.evaluate_story_ranking_shadow",
            "--input",
            str(snapshot),
            "--as-of",
            "2026-07-23T12:00:00Z",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["mode"] == "read_only_story_ranking_shadow"
    assert report["database_writes"] == 0
    assert "read-only" in result.stderr


def test_cli_failure_is_private(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"candidates":[{"title":"private content"}]}', encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "backend.scripts.evaluate_story_ranking_shadow",
            "--input",
            str(bad),
            "--as-of",
            "2026-07-23T12:00:00Z",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "private content" not in result.stderr
    assert "private content" not in result.stdout
