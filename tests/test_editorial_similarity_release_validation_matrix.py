"""RED validation matrix for future Editorial Similarity hardening.

These deterministic fixtures encode reviewed editorial distinctions. They do not
change routing and deliberately avoid reproducing complete publisher articles.
"""

import pytest

from backend.app.editorial_similarity import (
    event_anchor_evidence,
    score_editorial_similarity,
)


def article(title, text, host, published_at, **overrides):
    record = {
        "title": title,
        "summary": text,
        "content": text,
        "source_url": f"https://{host}/story",
        "publishedDate": published_at,
    }
    record.update(overrides)
    return record


IMF_SKY_STRAIGHT = article(
    "UK economy to grow more than expected, IMF says",
    (
        "The International Monetary Fund October 2026 World Economic Outlook "
        "forecast UK GDP growth of 1.3% in 2026 and 1.2% in 2027. Inflation was "
        "forecast at 3.3% in 2026 and 2.8% in 2027."
    ),
    "news.sky.com",
    "2026-10-13T00:16:00+00:00",
)

IMF_BBC_STRAIGHT = article(
    "UK growth upgraded but energy prices and rates to bite in 2027",
    (
        "The IMF October 2026 World Economic Outlook upgraded UK economy growth to "
        "1.3% for 2026 and forecast 1.2% for 2027. It forecast inflation of 3.3% "
        "in 2026 and 2.8% in 2027."
    ),
    "bbc.co.uk",
    "2026-10-13T03:14:13+00:00",
)

IMF_BBC_ANALYSIS = article(
    "Three things we've learnt about the UK economy from the IMF",
    (
        "Three findings from the IMF October 2026 World Economic Outlook explain "
        "the outlook for growth, inflation and borrowing. UK growth was forecast "
        "at 1.3% in 2026, while the analysis also considers the 2031 borrowing projection."
    ),
    "bbc.co.uk",
    "2026-10-13T11:58:43+00:00",
)

GROCERY_SKY = article(
    "Grocery inflation ticks up again as energy costs weigh on shoppers",
    (
        "Worldpanel by Numerator measured grocery price inflation at 2.5%, up "
        "from 2.3%, in the four weeks ending 4 October 2026."
    ),
    "news.sky.com",
    "2026-10-13T07:00:00+00:00",
)

GROCERY_GUARDIAN = article(
    "UK shoppers seek deals as grocery price inflation rises again",
    (
        "Worldpanel by Numerator said grocery inflation rose from 2.3% to 2.5% "
        "during the four weeks ending 4 October 2026 as promotional spending grew."
    ),
    "theguardian.com",
    "2026-10-13T10:37:00+00:00",
)


def same_run(first, second):
    return event_anchor_evidence(first, second, provenance="same_run")


def has_reporting_period(evidence):
    return any(
        value.startswith("reporting_period:") for value in evidence.shared_quantities
    )


def test_imf_straight_reports_share_release_phrase_and_forecast_figures():
    evidence = same_run(IMF_SKY_STRAIGHT, IMF_BBC_STRAIGHT)

    assert {
        "percentage:1.2",
        "percentage:1.3",
        "percentage:2.8",
        "percentage:3.3",
    }.issubset(evidence.shared_quantities)
    assert evidence.shared_event_phrases


def test_imf_straight_reports_recognise_issuing_organisation():
    evidence = same_run(IMF_SKY_STRAIGHT, IMF_BBC_STRAIGHT)

    assert "international monetary fund" in evidence.shared_entities


def test_imf_straight_reports_recognise_explicit_outlook_release_period():
    evidence = same_run(IMF_SKY_STRAIGHT, IMF_BBC_STRAIGHT)

    assert has_reporting_period(evidence)


def test_imf_straight_reports_have_duplicate_review_compatible_release_identity():
    evidence = same_run(IMF_SKY_STRAIGHT, IMF_BBC_STRAIGHT)

    assert "reporting_period_conflict" not in evidence.evidence_codes
    assert "statistical_release_identity" in evidence.evidence_codes
    assert evidence.same_run_cross_source_compatible is True


def test_imf_release_identity_does_not_depend_on_headline_overlap():
    differently_headlined = {
        **IMF_BBC_STRAIGHT,
        "title": "Economic outlook publication issued after annual review",
    }

    evidence = same_run(IMF_SKY_STRAIGHT, differently_headlined)

    assert evidence.shared_event_phrases
    assert evidence.same_run_cross_source_compatible is True


def test_imf_analysis_format_protects_distinct_editorial_purpose():
    evidence = same_run(IMF_SKY_STRAIGHT, IMF_BBC_ANALYSIS)

    assert evidence.shared_event_phrases
    assert evidence.format_relation == "guard"
    assert evidence.same_run_cross_source_compatible is False


@pytest.mark.parametrize(
    "title",
    (
        "Analysis: What the IMF forecast says about the UK economy",
        "Commentary: The choices facing the UK economy",
        "What we learned about the UK economy from the IMF",
        "Five things we've learnt about the UK economy",
        "What it means for households",
        "How it works: the IMF economic forecast",
    ),
)
def test_clear_analysis_and_explainer_headlines_receive_format_guard(title):
    analytical = {**IMF_BBC_ANALYSIS, "title": title}

    evidence = same_run(IMF_SKY_STRAIGHT, analytical)

    assert evidence.format_relation == "guard"
    assert evidence.same_run_cross_source_compatible is False


@pytest.mark.parametrize(
    "title",
    (
        "Three people arrested in Chester",
        "Five businesses fined for safety breaches",
        "Four councillors resign from committee",
        "Two companies announce new jobs",
        "Three schools receive funding",
        "Will interest rates rise next year?",
    ),
)
def test_numbered_news_and_ordinary_questions_remain_straight_reporting(title):
    candidate = {**IMF_BBC_STRAIGHT, "title": title}

    evidence = same_run(IMF_SKY_STRAIGHT, candidate)

    assert evidence.format_relation == "compatible"


def test_contextual_analysis_in_body_does_not_change_straight_report_format():
    candidate = {
        **IMF_BBC_STRAIGHT,
        "title": "UK growth forecast published by international body",
        "content": (
            "The report includes background, consequences and analysis of what the "
            "figures could mean, but the headline is ordinary straight reporting."
        ),
    }

    evidence = same_run(IMF_SKY_STRAIGHT, candidate)

    assert evidence.format_relation == "compatible"


def test_official_imf_correction_is_a_material_development_not_straight_duplication():
    original = article(
        "IMF forecasts UK growth of 1.3%",
        "The IMF forecast UK GDP growth of 1.3% in its October 2026 outlook.",
        "one.example",
        "2026-10-13T08:00:00+00:00",
    )
    correction = article(
        "IMF corrects UK growth forecast to 1.1%",
        (
            "An official IMF correction revised its October 2026 UK GDP growth "
            "forecast from 1.3% to 1.1%."
        ),
        "two.example",
        "2026-10-13T10:00:00+00:00",
    )

    evidence = same_run(original, correction)

    assert evidence.stage_relation == "material_transition"
    assert "stage_transition_guard" in evidence.evidence_codes
    assert evidence.same_run_cross_source_compatible is False


def test_worldpanel_release_shares_verified_distinctive_figures():
    evidence = same_run(GROCERY_SKY, GROCERY_GUARDIAN)

    assert {"percentage:2.3", "percentage:2.5"}.issubset(
        evidence.shared_quantities
    )


def test_worldpanel_release_recognises_issuing_organisation():
    evidence = same_run(GROCERY_SKY, GROCERY_GUARDIAN)

    assert "worldpanel by numerator" in evidence.shared_entities


def test_worldpanel_release_recognises_four_week_reporting_period():
    evidence = same_run(GROCERY_SKY, GROCERY_GUARDIAN)

    assert has_reporting_period(evidence)


def test_worldpanel_release_identity_requires_full_evidence_conjunction():
    evidence = same_run(GROCERY_SKY, GROCERY_GUARDIAN)

    assert evidence.shared_event_phrases
    assert "statistical_release_identity" in evidence.evidence_codes
    assert evidence.same_run_cross_source_compatible is True


def test_shared_grocery_percentages_without_same_issuer_or_period_are_insufficient():
    first = article(
        "Retail survey measures food inflation",
        "Retail Group measured food inflation at 2.5%, up from 2.3%, in September.",
        "one.example",
        "2026-10-13T08:00:00+00:00",
    )
    second = article(
        "Independent index records price changes",
        "Market Institute recorded 2.5%, up from 2.3%, in the quarter to June.",
        "two.example",
        "2026-10-13T09:00:00+00:00",
    )

    evidence = same_run(first, second)

    assert {"percentage:2.3", "percentage:2.5"}.issubset(
        evidence.shared_quantities
    )
    assert evidence.shared_entities == ()
    assert evidence.shared_event_phrases == ()
    assert evidence.same_run_cross_source_compatible is False


def test_different_monthly_imf_releases_are_not_one_release():
    september = article(
        "IMF publishes September UK outlook",
        "The IMF September 2026 outlook forecast UK GDP growth of 1.3%.",
        "one.example",
        "2026-09-13T08:00:00+00:00",
    )
    october = article(
        "IMF publishes October UK outlook",
        "The IMF October 2026 outlook forecast UK GDP growth of 1.3%.",
        "two.example",
        "2026-10-13T08:00:00+00:00",
    )

    evidence = same_run(september, october)

    assert "reporting_period_conflict" in evidence.evidence_codes
    assert evidence.same_run_cross_source_compatible is False


def test_same_target_year_in_different_imf_outlooks_is_not_same_release():
    september = article(
        "September IMF outlook forecasts 2027 growth",
        (
            "The IMF September 2026 World Economic Outlook forecast UK economy "
            "growth of 1.2% in 2027."
        ),
        "one.example",
        "2026-09-13T08:00:00+00:00",
    )
    october = article(
        "October IMF outlook forecasts 2027 growth",
        (
            "The IMF October 2026 World Economic Outlook forecast UK economy "
            "growth of 1.2% in 2027."
        ),
        "two.example",
        "2026-10-13T08:00:00+00:00",
    )

    evidence = same_run(september, october)

    assert "reporting_period_conflict" in evidence.evidence_codes
    assert evidence.same_run_cross_source_compatible is False


def test_successive_worldpanel_reporting_periods_are_not_same_release():
    september = article(
        "Grocery inflation rises in September",
        (
            "Worldpanel by Numerator measured grocery inflation at 2.5% in the "
            "four weeks ending 6 September 2026."
        ),
        "one.example",
        "2026-09-08T08:00:00+00:00",
    )
    october = article(
        "Grocery inflation rises in October",
        (
            "Worldpanel measured grocery inflation at 2.5% in the four-week period "
            "to 4 October 2026."
        ),
        "two.example",
        "2026-10-13T08:00:00+00:00",
    )

    evidence = same_run(september, october)

    assert "reporting_period_conflict" in evidence.evidence_codes
    assert evidence.same_run_cross_source_compatible is False


def test_worldpanel_and_unrelated_grocery_research_do_not_share_release_identity():
    unrelated = article(
        "Independent grocery survey reports inflation",
        (
            "Market Institute measured grocery inflation at 2.5%, up from 2.3%, "
            "in the four weeks ending 4 October 2026."
        ),
        "other.example",
        "2026-10-13T09:00:00+00:00",
    )

    evidence = same_run(GROCERY_SKY, unrelated)

    assert "statistical_release_identity" not in evidence.evidence_codes
    assert evidence.same_run_cross_source_compatible is False


def test_incidental_imf_mention_without_release_context_is_not_issuer_identity():
    incidental = article(
        "Charity conference considers international institutions",
        "Speakers mentioned the IMF while discussing education and community work.",
        "one.example",
        "2026-10-13T08:00:00+00:00",
    )
    unrelated = article(
        "Local event discusses overseas organisations",
        "A panel referred to the IMF during a general conversation about charities.",
        "two.example",
        "2026-10-13T09:00:00+00:00",
    )

    evidence = same_run(incidental, unrelated)

    assert "international monetary fund" not in evidence.shared_entities
    assert "statistical_release_identity" not in evidence.evidence_codes


def test_separate_regional_economic_releases_remain_distinct():
    north_west = article(
        "North West quarterly economic report",
        "A regional survey reported business growth of 1.3% in Q3 2026.",
        "one.example",
        "2026-10-13T08:00:00+00:00",
    )
    scotland = article(
        "Scotland quarterly economic report",
        "A separate regional survey reported growth of 1.3% in Q3 2026.",
        "two.example",
        "2026-10-13T09:00:00+00:00",
    )

    evidence = same_run(north_west, scotland)

    assert "statistical_release_identity" not in evidence.evidence_codes
    assert evidence.same_run_cross_source_compatible is False


def test_explicit_annual_statistical_release_period_is_recognised():
    first = article(
        "IMF annual economic outlook",
        "The IMF 2026 annual outlook forecast UK economy growth of 1.3%.",
        "one.example",
        "2026-10-13T08:00:00+00:00",
    )
    second = article(
        "UK growth forecast in annual IMF publication",
        "The IMF annual outlook for 2026 forecast UK economy growth of 1.3%.",
        "two.example",
        "2026-10-13T09:00:00+00:00",
    )

    evidence = same_run(first, second)

    assert "reporting_period:annual:2026" in evidence.shared_quantities
    assert "statistical_release_identity" in evidence.evidence_codes


def test_forecast_target_years_do_not_become_release_period_identity():
    first = article(
        "IMF forecasts UK economy growth",
        "The IMF forecast UK GDP growth of 1.3% in 2026 and 1.2% in 2027.",
        "one.example",
        "2026-10-13T08:00:00+00:00",
    )
    second = article(
        "UK economy growth forecast published",
        "The IMF forecast growth of 1.3% for 2026 and 1.2% for 2027.",
        "two.example",
        "2026-10-13T09:00:00+00:00",
    )

    evidence = same_run(first, second)

    assert "reporting_period_conflict" not in evidence.evidence_codes
    assert has_reporting_period(evidence) is False
    assert "statistical_release_identity" not in evidence.evidence_codes
    assert evidence.same_run_cross_source_compatible is False


def test_ordinary_updated_or_historical_revision_wording_is_not_a_correction_stage():
    first = article(
        "Updated coverage of the UK economic outlook",
        "Updated coverage discusses an initial UK GDP growth forecast of 1.3%.",
        "one.example",
        "2026-10-13T08:00:00+00:00",
    )
    second = article(
        "UK economy outlook examines earlier revisions",
        (
            "Background analysis notes that forecasts were revised in earlier years, "
            "while the current UK GDP growth forecast remains 1.3%."
        ),
        "two.example",
        "2026-10-13T09:00:00+00:00",
    )

    evidence = same_run(first, second)

    assert evidence.stage_relation != "material_transition"
    assert "stage_transition_guard" not in evidence.evidence_codes


def test_explicit_correction_transition_evidence_is_symmetric():
    original = article(
        "IMF forecasts UK growth of 1.3%",
        "The IMF forecast UK GDP growth of 1.3% in its October 2026 outlook.",
        "one.example",
        "2026-10-13T08:00:00+00:00",
    )
    correction = article(
        "IMF corrects UK growth forecast to 1.1%",
        "An official IMF correction revised the forecast from 1.3% to 1.1%.",
        "two.example",
        "2026-10-13T10:00:00+00:00",
    )

    assert same_run(original, correction) == same_run(correction, original)


def test_explicit_release_period_conflict_is_symmetric():
    september = article(
        "September UK outlook",
        "The September 2026 outlook forecast UK economy growth of 1.3%.",
        "one.example",
        "2026-09-13T08:00:00+00:00",
    )
    october = article(
        "October UK outlook",
        "The October 2026 outlook forecast UK economy growth of 1.3%.",
        "two.example",
        "2026-10-13T08:00:00+00:00",
    )

    assert same_run(september, october) == same_run(october, september)


def test_unrelated_cheshire_planning_applications_remain_separate():
    crewe = article(
        "Plans lodged for 100 homes in Crewe",
        "Application 26/1001 proposes 100 homes at Site Alpha in Crewe.",
        "one.example",
        "2026-10-13T08:00:00+00:00",
        location="Crewe",
    )
    wilmslow = article(
        "Plans lodged for 100 homes in Wilmslow",
        "Application 26/2002 proposes 100 homes at Site Beta in Wilmslow.",
        "two.example",
        "2026-10-13T09:00:00+00:00",
        location="Wilmslow",
    )

    assert same_run(crewe, wilmslow).same_run_cross_source_compatible is False


def test_planning_proposal_followed_by_refusal_retains_transition_guard():
    proposal = article(
        "Plans submitted for 100 homes in Crewe",
        "Application 26/1001 proposes 100 homes at Site Alpha in Crewe.",
        "one.example",
        "2026-10-01T08:00:00+00:00",
        location="Crewe",
    )
    refusal = article(
        "Council refuses 100-home Crewe scheme",
        "Application 26/1001 for 100 homes at Site Alpha in Crewe was refused.",
        "two.example",
        "2026-10-13T10:00:00+00:00",
        location="Crewe",
    )

    score = score_editorial_similarity(proposal, refusal)
    evidence = same_run(proposal, refusal)

    assert score.band == "very_likely"
    assert evidence.stage_relation == "material_transition"
    assert evidence.same_run_cross_source_compatible is False


def test_local_consequence_of_national_announcement_remains_distinct():
    national = article(
        "UK Government announces national rail funding",
        "The UK Government announced £2 billion for rail projects across Britain.",
        "one.example",
        "2026-10-13T08:00:00+00:00",
    )
    local = article(
        "Chester station to receive funding after national announcement",
        "Chester station will receive £20 million from the UK Government rail fund.",
        "two.example",
        "2026-10-13T10:00:00+00:00",
        location="Chester",
    )

    assert same_run(national, local).same_run_cross_source_compatible is False


def test_unrelated_broad_economic_topics_remain_distinct():
    growth = article(
        "UK economic growth forecast published",
        "A forecast considered GDP growth and investment during 2026.",
        "one.example",
        "2026-10-13T08:00:00+00:00",
    )
    employment = article(
        "UK employment figures released",
        "Separate labour-market figures covered employment during 2026.",
        "two.example",
        "2026-10-13T09:00:00+00:00",
    )

    assert same_run(growth, employment).same_run_cross_source_compatible is False


def test_pair_evidence_is_symmetric_when_candidate_availability_is_equal():
    forward = same_run(GROCERY_SKY, GROCERY_GUARDIAN)
    reverse = same_run(GROCERY_GUARDIAN, GROCERY_SKY)

    assert forward == reverse


def test_exact_title_and_url_protections_remain_ineligible():
    same_title = {**IMF_SKY_STRAIGHT, "source_url": "https://other.example/item"}
    same_url = {**IMF_BBC_STRAIGHT, "source_url": IMF_SKY_STRAIGHT["source_url"]}

    assert score_editorial_similarity(IMF_SKY_STRAIGHT, same_title).band == "ineligible"
    assert score_editorial_similarity(IMF_SKY_STRAIGHT, same_url).band == "ineligible"
