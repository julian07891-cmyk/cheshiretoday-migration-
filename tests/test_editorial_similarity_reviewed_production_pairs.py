"""RED matrix for reviewed real-world Editorial Similarity pairs.

The fixtures contain only bounded scorer evidence copied read-only from the
named production records.  They deliberately do not reproduce complete source
articles and they do not define or enable any routing behaviour.
"""

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import asyncio
import pytest

from backend.app import editorial_similarity_shadow as shadow
from backend.app.editorial_similarity import (
    event_anchor_evidence,
    score_editorial_similarity,
)


def reviewed_article(
    mongo_id,
    title,
    summary,
    evidence_excerpt,
    source,
    source_url,
    published_date,
    created_at,
    category="Business",
):
    return {
        "_id": mongo_id,
        "title": title,
        "summary": summary,
        "content": evidence_excerpt,
        "source": source,
        "source_url": source_url,
        "publishedDate": published_date,
        "created_at": created_at,
        "category": category,
    }


IMF_SKY_STRAIGHT = reviewed_article(
    "6acdbb4c7f3ca9839f358815",
    "UK economy to grow more than expected - but households face sharper rise in inflation, IMF says",
    (
        "The UK economy is set to grow faster than expected this year, though "
        "households are expected to face higher rates of inflation, according "
        "to forecasts from the International Monetary Fund (IMF)."
    ),
    (
        "The IMF's latest World Economic Outlook predicts UK GDP growth of 1.3% "
        "in 2026 and 1.2% in 2027. Inflation is forecast at 3.3% in 2026 and "
        "2.8% in 2027."
    ),
    "Sky News",
    "https://news.sky.com/story/uk-economy-to-grow-more-than-expected-but-households-face-sharper-rise-in-inflation-imf-says-13598675",
    "2026-10-13T00:16:00",
    "2026-10-13T05:00:08.289982+00:00",
)

IMF_BBC_STRAIGHT = reviewed_article(
    "6acdbb447f3ca9839f358813",
    "UK growth upgraded but energy prices and rates to bite in 2027",
    "The IMF report comes as final preparations are made for the first Budget.",
    (
        "The UK economy is expected to grow faster than previously forecast. "
        "The International Monetary Fund raised UK growth for 2026 from 1% to "
        "1.3% and expects 1.2% in 2027. Its World Economic Outlook forecasts "
        "inflation of 3.3% in 2026 and 2.8% in 2027."
    ),
    "BBC News",
    "https://www.bbc.co.uk/news/articles/cmglw0r21zexo?at_medium=RSS&at_campaign=rss",
    "2026-10-13T03:14:13",
    "2026-10-13T05:00:06.102349+00:00",
)

IMF_BBC_ANALYSIS = reviewed_article(
    "6ace64153b3f12b82f0b64fb",
    "Three things we've learnt about the UK economy from the IMF",
    (
        "The influential economics body upgraded its UK growth forecast, but "
        "risks remain."
    ),
    (
        "Three findings examine growth, inflation and borrowing. The IMF expects "
        "growth of 1.3% in 2026, inflation of 3.3%, and considers a 2031 borrowing "
        "projection."
    ),
    "BBC News",
    "https://www.bbc.co.uk/news/articles/cmly05l1g15yo?at_medium=RSS&at_campaign=rss",
    "2026-10-13T11:58:43",
    "2026-10-13T17:00:03.213408+00:00",
)

GROCERY_SKY = reviewed_article(
    "6ace0fab3a756a8baef24f2c",
    "Grocery inflation ticks up again - as energy costs weigh on shoppers",
    "A closely-watched measure of grocery inflation has risen again.",
    (
        "Grocery price inflation has risen for a second consecutive month, adding "
        "to pressure on household budgets as energy and fuel costs increase. "
        "Worldpanel by Numerator said grocery price inflation reached an annual "
        "rate of 2.5% in the four weeks to 4 October. The figure was up from 2.3% "
        "in its previous report. The research tracks prices and sales across major "
        "supermarket chains. It found that prices rose fastest for water, cordials "
        "and skincare products during the period. Prices fell most sharply for "
        "butter, cheese and chocolate, according to the data. The report also "
        "pointed to changes in shopping habits as households respond to rising "
        "energy costs and uncertainty about future bills."
    ),
    "Sky News",
    "https://news.sky.com/story/grocery-inflation-ticks-up-again-as-energy-costs-weigh-on-shoppers-13598268",
    "2026-10-13T07:00:00",
    "2026-10-13T11:00:06.735760+00:00",
)

GROCERY_GUARDIAN = reviewed_article(
    "6ace0f463a756a8baef24f10",
    "UK shoppers seek deals as grocery price inflation rises again",
    "Shoppers are turning to offers as grocery price inflation rises.",
    (
        "UK shoppers are increasingly turning to supermarket special offers as "
        "grocery price inflation rises, while chocolate confectionery prices have "
        "fallen ahead of Halloween. Prices were 2.5% higher in the four weeks to "
        "4 October than during the same period last year, according to Worldpanel "
        "by Numerator data. The figure was up from 2.3% in the previous four-week "
        "period. Spending on promotional offers increased by more than £250m "
        "compared with last year. Overall take-home grocery sales rose by 1% year "
        "on year. Price changes varied across categories, with water, cordials and "
        "skincare among the fastest increases and butter, cheese and chocolate "
        "recording falls."
    ),
    "The Guardian",
    "https://www.theguardian.com/business/2026/oct/13/uk-shoppers-deals-grocery-price-inflation-supermarkets-prices-halloween",
    "2026-10-13T10:37:00",
    "2026-10-13T11:00:07.687068+00:00",
    "UK News",
)

SURGERY_VIDEO = reviewed_article(
    "6ace0f4f3a756a8baef24f12",
    "'I woke from surgery to find it hadn't been done'",
    "Kelly O'Shea says she lost faith in women's health after paying £20,000.",
    (
        "Kelly O'Shea says she has lost faith in women's healthcare after waking "
        "from operations to discover the endometriosis treatment she needed had "
        "not been carried out. The 32-year-old lives with chronic pain and said "
        "she had been in daily pain for about three and a half years. Her "
        "endometriosis affects her bowel, meaning she needs bowel and bladder "
        "specialists alongside endometriosis specialists during surgery. Following "
        "one operation, she was told the bowel surgeon had not been available and "
        "the endometriosis was left untreated. On another occasion, surgery was "
        "stopped because the theatre was needed for an urgent case. She said she "
        "felt she had no alternative but to pay £20,000 for treatment."
    ),
    "BBC News",
    "https://www.bbc.co.uk/news/videos/cj62yz73y9rvo?at_medium=RSS&at_campaign=rss",
    "2026-10-13T10:29:09",
    "2026-10-13T11:00:06.503266+00:00",
    "UK News",
)

SURGERY_ARTICLE = reviewed_article(
    "6acdbae57f3ca9839f358807",
    "I've woken from operations to find the surgery hasn't been done - women's health is broken",
    "Kelly O'Shea felt forced to pay £20,000 for treatment.",
    (
        "Kelly O'Shea says she woke from more than one operation to learn that "
        "surgeons had been unable to carry out the endometriosis treatment she "
        "needed. The 32-year-old, who lives with chronic pain, said she felt forced "
        "to pay £20,000 for private treatment. Kelly has experienced daily pain "
        "for about three and a half years. Her endometriosis affects her bowel, "
        "meaning operations require bowel and bladder specialists as well as "
        "endometriosis specialists. After her most recent operation, she was told "
        "that a bowel surgeon had not been available and her endometriosis was "
        "left untreated. On another occasion, her operation was stopped early "
        "because the theatre was needed for an urgent case."
    ),
    "BBC News",
    "https://www.bbc.co.uk/news/articles/cq99znm9j7plo?at_medium=RSS&at_campaign=rss",
    "2026-10-13T04:56:04",
    "2026-10-13T05:00:03.375445+00:00",
    "UK News",
)


@dataclass(frozen=True)
class ReviewedPair:
    name: str
    first: dict
    second: dict
    editorial_label: str
    current_score: int
    current_band: str
    observed_full_record_score: int
    observed_full_record_band: str


REVIEWED_PAIRS = (
    ReviewedPair(
        "imf_straight",
        IMF_SKY_STRAIGHT,
        IMF_BBC_STRAIGHT,
        "same release, substantially repeated straight reporting",
        30,
        "low",
        30,
        "low",
    ),
    ReviewedPair(
        "grocery_straight",
        GROCERY_SKY,
        GROCERY_GUARDIAN,
        "same release, substantially repeated straight reporting",
        34,
        "low",
        34,
        "low",
    ),
    ReviewedPair(
        "surgery_companion",
        SURGERY_VIDEO,
        SURGERY_ARTICLE,
        "same event, substantially repeated video/article reporting",
        40,
        "low",
        60,
        "possible",
    ),
)


@pytest.mark.parametrize("pair", REVIEWED_PAIRS, ids=lambda pair: pair.name)
def test_reviewed_pair_current_score_is_pinned_separately_from_editorial_label(pair):
    result = score_editorial_similarity(pair.first, pair.second)

    assert result.score == pair.current_score
    assert result.band == pair.current_band
    assert pair.observed_full_record_score >= pair.current_score
    assert pair.observed_full_record_band in shadow.ALLOWED_BANDS
    assert pair.editorial_label


def test_imf_straight_reports_extract_specific_outlook_evidence_but_stay_inconclusive():
    """RED only for the missing WEO anchor; no release period is manufactured."""
    evidence = event_anchor_evidence(
        IMF_SKY_STRAIGHT, IMF_BBC_STRAIGHT, provenance="same_run"
    )

    assert "international monetary fund" in evidence.shared_entities
    assert "uk_economic_growth_release" in evidence.shared_event_phrases
    assert {
        "percentage:1.2",
        "percentage:1.3",
        "percentage:2.8",
        "percentage:3.3",
    }.issubset(evidence.shared_quantities)
    assert not any(
        value.startswith("reporting_period:") for value in evidence.shared_quantities
    )
    assert "reporting_period_conflict" not in evidence.evidence_codes
    assert evidence.stage_relation == "compatible"
    assert evidence.format_relation == "compatible"
    assert "imf_world_economic_outlook_release" in evidence.shared_event_phrases
    assert "statistical_release_identity" not in evidence.evidence_codes
    assert evidence.same_run_cross_source_compatible is False


def test_worldpanel_reports_extract_year_unspecified_four_week_period_safely():
    """RED only for the shared day/month evidence; the omitted year stays unknown."""
    evidence = event_anchor_evidence(
        GROCERY_SKY, GROCERY_GUARDIAN, provenance="same_run"
    )

    assert "worldpanel by numerator" in evidence.shared_entities
    assert {"percentage:2.3", "percentage:2.5"}.issubset(
        evidence.shared_quantities
    )
    assert "reporting_period:four_weeks_ending:10-04:year_unspecified" in (
        evidence.shared_quantities
    )
    assert "reporting_period_conflict" not in evidence.evidence_codes
    assert evidence.stage_relation in {"compatible", "unknown"}
    assert evidence.format_relation == "compatible"
    assert "worldpanel_grocery_inflation_release" in evidence.shared_event_phrases
    assert "statistical_release_identity" not in evidence.evidence_codes
    assert evidence.same_run_cross_source_compatible is False


def test_surgery_companions_require_correlated_account_evidence_not_format_alone():
    """RED: same publisher/format is insufficient without a bounded event anchor."""
    evidence = event_anchor_evidence(
        SURGERY_VIDEO, SURGERY_ARTICLE, provenance="same_run"
    )

    assert "currency:gbp:20000" in evidence.shared_quantities
    assert evidence.format_relation == "compatible"
    assert evidence.stage_relation in {"compatible", "unknown"}
    for article in (SURGERY_VIDEO, SURGERY_ARTICLE):
        stored_evidence = " ".join(
            (article["title"], article["summary"], article["content"])
        ).casefold()
        assert "kelly o'shea" in stored_evidence
        assert "endometriosis" in stored_evidence
        assert "bowel surgeon" in stored_evidence
        assert "£20,000" in stored_evidence
    assert (
        "endometriosis_surgery_not_completed_account"
        in evidence.shared_event_phrases
    )
    assert "event_phrase_overlap" in evidence.evidence_codes
    # This is deliberately not a cross-source compatibility contract.  A future
    # routing policy would require separate approval and additional safeguards.
    assert evidence.same_run_cross_source_compatible is False


def test_real_imf_analysis_companion_retains_format_protection():
    evidence = event_anchor_evidence(
        IMF_SKY_STRAIGHT, IMF_BBC_ANALYSIS, provenance="same_run"
    )

    assert evidence.format_relation == "guard"
    assert "format_guard" in evidence.evidence_codes
    assert evidence.same_run_cross_source_compatible is False


@pytest.mark.parametrize(
    "first,second",
    (
        (IMF_SKY_STRAIGHT, IMF_BBC_STRAIGHT),
        (GROCERY_SKY, GROCERY_GUARDIAN),
    ),
)
def test_current_release_identity_gap_is_explicit_not_manufactured(first, second):
    """Characterise today's insufficient-evidence result separately from RED."""
    evidence = event_anchor_evidence(first, second, provenance="same_run")

    assert evidence.shared_entities
    assert "statistical_release_identity" not in evidence.evidence_codes
    assert evidence.same_run_cross_source_compatible is False


def test_generic_imf_forecasts_do_not_gain_world_economic_outlook_anchor():
    first = {
        **IMF_SKY_STRAIGHT,
        "content": "The IMF forecast UK GDP growth of 1.3% in 2026.",
    }
    second = {
        **IMF_BBC_STRAIGHT,
        "content": "An IMF forecast put UK growth at 1.3% for 2026.",
    }

    evidence = event_anchor_evidence(first, second, provenance="same_run")

    assert "imf_world_economic_outlook_release" not in evidence.shared_event_phrases
    assert "statistical_release_identity" not in evidence.evidence_codes


def test_different_explicit_imf_outlooks_keep_period_conflict_guard():
    september = {
        **IMF_SKY_STRAIGHT,
        "content": (
            "The IMF September 2026 World Economic Outlook forecast UK GDP "
            "growth of 1.3%."
        ),
    }
    october = {
        **IMF_BBC_STRAIGHT,
        "content": (
            "The IMF October 2026 World Economic Outlook forecast UK GDP "
            "growth of 1.3%."
        ),
    }

    evidence = event_anchor_evidence(september, october, provenance="same_run")

    assert "imf_world_economic_outlook_release" in evidence.shared_event_phrases
    assert "reporting_period_conflict" in evidence.evidence_codes
    assert evidence.same_run_cross_source_compatible is False


def test_year_unspecified_worldpanel_period_does_not_match_explicit_year():
    explicit = {
        **GROCERY_SKY,
        "content": (
            "Worldpanel grocery inflation was 2.5% in the four weeks to "
            "4 October 2026."
        ),
    }
    unspecified = {
        **GROCERY_GUARDIAN,
        "content": (
            "Worldpanel grocery inflation was 2.5% in the four weeks to 4 October."
        ),
    }

    evidence = event_anchor_evidence(explicit, unspecified, provenance="same_run")

    assert not any(
        value.startswith("reporting_period:") for value in evidence.shared_quantities
    )
    assert "reporting_period_conflict" not in evidence.evidence_codes
    assert "statistical_release_identity" not in evidence.evidence_codes
    assert evidence.same_run_cross_source_compatible is False


def test_unrelated_grocery_dataset_does_not_gain_worldpanel_release_anchor():
    unrelated = {
        **GROCERY_GUARDIAN,
        "content": (
            "Market Institute grocery inflation was 2.5% in the four weeks to "
            "4 October."
        ),
        "summary": "A separate grocery dataset reported inflation of 2.5%.",
    }

    evidence = event_anchor_evidence(GROCERY_SKY, unrelated, provenance="same_run")

    assert "worldpanel by numerator" not in evidence.shared_entities
    assert "worldpanel_grocery_inflation_release" not in evidence.shared_event_phrases
    assert evidence.same_run_cross_source_compatible is False


def test_unrelated_endometriosis_patient_does_not_gain_account_anchor():
    unrelated = {
        **SURGERY_ARTICLE,
        "title": "Different patient receives endometriosis treatment",
        "summary": "A different patient discussed a separate operation.",
        "content": (
            "Jane Smith underwent endometriosis surgery with a specialist team "
            "and later paid £20,000 for separate care."
        ),
        "source_url": "https://other.example/different-patient",
    }

    evidence = event_anchor_evidence(SURGERY_VIDEO, unrelated, provenance="same_run")

    assert (
        "endometriosis_surgery_not_completed_account"
        not in evidence.shared_event_phrases
    )
    assert evidence.same_run_cross_source_compatible is False


def test_generic_medical_companions_do_not_gain_account_anchor():
    video = {
        **SURGERY_VIDEO,
        "content": "A patient discussed endometriosis treatment in a hospital video.",
    }
    article = {
        **SURGERY_ARTICLE,
        "content": "An article covered general endometriosis surgery waiting times.",
    }

    evidence = event_anchor_evidence(video, article, provenance="same_run")

    assert evidence.shared_event_phrases == ()
    assert evidence.same_run_cross_source_compatible is False


def test_later_successful_treatment_is_not_the_failed_surgery_account():
    development = {
        **SURGERY_ARTICLE,
        "title": "Kelly O'Shea receives successful specialist treatment",
        "summary": "A later operation was completed by a full specialist team.",
        "content": (
            "Kelly O'Shea later received completed endometriosis treatment from "
            "a bowel surgeon and specialist team."
        ),
        "source_url": "https://other.example/later-treatment",
    }

    evidence = event_anchor_evidence(SURGERY_VIDEO, development, provenance="same_run")

    assert (
        "endometriosis_surgery_not_completed_account"
        not in evidence.shared_event_phrases
    )
    assert evidence.same_run_cross_source_compatible is False


@pytest.mark.parametrize(
    "first,second",
    (
        (IMF_SKY_STRAIGHT, IMF_BBC_STRAIGHT),
        (GROCERY_SKY, GROCERY_GUARDIAN),
        (SURGERY_VIDEO, SURGERY_ARTICLE),
    ),
)
def test_new_reviewed_pair_event_evidence_is_symmetric(first, second):
    assert event_anchor_evidence(first, second, provenance="same_run") == (
        event_anchor_evidence(second, first, provenance="same_run")
    )


def test_official_correction_and_later_planning_decision_remain_protected():
    original = reviewed_article(
        "control-original",
        "IMF forecasts UK growth of 1.3%",
        "The IMF forecast growth of 1.3% in its October outlook.",
        "The original forecast was 1.3%.",
        "Publisher One",
        "https://one.example/imf-original",
        "2026-10-13T08:00:00+00:00",
        "2026-10-13T08:05:00+00:00",
    )
    correction = reviewed_article(
        "control-correction",
        "IMF corrects UK growth forecast to 1.1%",
        "An official IMF correction revised the forecast from 1.3% to 1.1%.",
        "The corrected forecast is 1.1%.",
        "Publisher Two",
        "https://two.example/imf-correction",
        "2026-10-13T10:00:00+00:00",
        "2026-10-13T10:05:00+00:00",
    )
    proposal = reviewed_article(
        "control-proposal",
        "Plans submitted for 100 homes in Crewe",
        "Application 26/1001 proposes 100 homes at Site Alpha in Crewe.",
        "The application has been submitted.",
        "Publisher One",
        "https://one.example/proposal",
        "2026-10-01T08:00:00+00:00",
        "2026-10-01T08:05:00+00:00",
        "Local News",
    )
    refusal = reviewed_article(
        "control-refusal",
        "Council refuses 100-home Crewe scheme",
        "Application 26/1001 for Site Alpha was refused.",
        "The council refused the application.",
        "Publisher Two",
        "https://two.example/refusal",
        "2026-10-13T10:00:00+00:00",
        "2026-10-13T10:05:00+00:00",
        "Local News",
    )

    for first, second in ((original, correction), (proposal, refusal)):
        evidence = event_anchor_evidence(first, second, provenance="same_run")
        assert evidence.stage_relation == "material_transition"
        assert "stage_transition_guard" in evidence.evidence_codes
        assert evidence.same_run_cross_source_compatible is False


def filler(index, *, overlap=False):
    title = (
        "UK shoppers seek deals as grocery price inflation rises again"
        if overlap
        else f"Unrelated community record {index}"
    )
    text = (
        (
            "Worldpanel by Numerator grocery price inflation rose from 2.3% to "
            f"2.5% in the four weeks to 4 October. Fixture evidence {index}."
        )
        if overlap
        else f"A separate community event with identifier {index}."
    )
    return reviewed_article(
        f"filler-{index:03d}",
        title,
        text,
        text,
        "Fixture Publisher",
        f"https://fixture.example/{index}",
        datetime(2026, 10, 13, 12, tzinfo=timezone.utc) + timedelta(minutes=index),
        datetime(2026, 10, 13, 12, tzinfo=timezone.utc) + timedelta(minutes=index),
    )


def test_same_run_reviewed_pair_is_reachable_but_still_scores_low():
    evaluator = shadow.EditorialSimilarityShadowEvaluator([IMF_SKY_STRAIGHT])
    evaluation = evaluator.evaluate(IMF_BBC_STRAIGHT)

    assert evaluation.shortlist_count == 1
    assert evaluation.matched_article_id == IMF_SKY_STRAIGHT["_id"]
    assert evaluation.matched_provenance == "active"
    assert evaluation.score == 30
    assert evaluation.band == "low"


def test_expected_pool_eviction_is_characterised_not_a_red_failure():
    evaluator = shadow.EditorialSimilarityShadowEvaluator([IMF_SKY_STRAIGHT])
    for index in range(shadow.COMPARISON_POOL_LIMIT):
        evaluator.add(filler(index), f"filler-{index:03d}", provenance="same_run")

    evaluation = evaluator.evaluate(IMF_BBC_STRAIGHT)

    assert evaluator.pool_size == shadow.COMPARISON_POOL_LIMIT
    assert IMF_SKY_STRAIGHT["_id"] not in {
        record.article_id for record in evaluator._records
    }
    assert evaluation.matched_article_id != IMF_SKY_STRAIGHT["_id"]


def test_expected_top_twenty_shortlist_displacement_is_characterised():
    evaluator = shadow.EditorialSimilarityShadowEvaluator([GROCERY_SKY])
    for index in range(shadow.SHORTLIST_LIMIT):
        evaluator.add(filler(index, overlap=True), f"filler-{index:03d}")

    evaluation = evaluator.evaluate(GROCERY_GUARDIAN)

    assert evaluation.shortlist_count == shadow.SHORTLIST_LIMIT
    assert evaluation.matched_article_id != GROCERY_SKY["_id"]


class RecordingCollection:
    def __init__(self):
        self.inserted = []

    async def insert_one(self, article):
        self.inserted.append(deepcopy(article))
        return SimpleNamespace(inserted_id="new-article")


class RecordingLogger:
    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(message)


def test_scorer_failure_remains_advisory_and_does_not_mutate_article(monkeypatch):
    article = deepcopy(IMF_BBC_STRAIGHT)
    before = deepcopy(article)
    evaluator = shadow.EditorialSimilarityShadowEvaluator([IMF_SKY_STRAIGHT])
    collection = RecordingCollection()
    logger = RecordingLogger()
    monkeypatch.setattr(
        shadow,
        "score_editorial_similarity",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("private evidence")),
    )

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
    assert len(logger.messages) == 1
    assert "private evidence" not in logger.messages[0]


@pytest.mark.parametrize(
    "overrides",
    (
        {"publishedDate": "not-a-date", "created_at": None},
        {"publishedDate": None, "created_at": None},
        {"summary": "", "content": "", "source": ""},
    ),
)
def test_missing_or_malformed_evidence_fails_open_without_routing(overrides):
    candidate = {**IMF_BBC_STRAIGHT, **overrides}
    evaluator = shadow.EditorialSimilarityShadowEvaluator([IMF_SKY_STRAIGHT])

    evaluation = evaluator.evaluate(candidate)

    assert evaluation.eligible is True
    assert evaluation.band in shadow.ALLOWED_BANDS
