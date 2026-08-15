from copy import deepcopy
from dataclasses import dataclass

import pytest

from backend.app import editorial_similarity as similarity


def article(title, text, host, *, location=""):
    return {
        "title": title,
        "summary": text,
        "content": text,
        "source_url": f"https://{host}/story",
        "location": location,
    }


@dataclass(frozen=True)
class LabelledPair:
    pair_id: str
    label: str
    provenance: str
    candidate: dict
    existing: dict


def pair(pair_id, label, provenance, first, second):
    return LabelledPair(pair_id, label, provenance, first, second)


LABELLED_PAIRS = (
    pair(
        "P-WATER",
        "positive",
        "same_run",
        article(
            "Five Water Companies Granted Permission to Raise Bills",
            "Thames Water and Southern Water were permitted extra funding for water bills of £43.",
            "sky.example",
        ),
        article(
            "Water bills set to rise after firms permitted extra funding",
            "Southern Water and Thames Water may raise water bills by £43 after the funding decision.",
            "bbc.example",
        ),
    ),
    pair(
        "P-GDP",
        "positive",
        "same_run",
        article(
            "UK economy grows 0.4%",
            "UK GDP growth reached 0.4% in Q2 2026.",
            "sky.example",
        ),
        article(
            "UK economy grows",
            "The UK economy recorded GDP growth of 0.4% in 2026 Q2.",
            "bbc.example",
        ),
    ),
    pair(
        "U-GDP-ANALYSIS",
        "uncertain",
        "same_run",
        article(
            "UK economy grows", "UK GDP growth was recorded in Q2 2026.", "bbc.example"
        ),
        article(
            "UK economy resilience analysis | Richard Partington",
            "Analysis of UK GDP growth in Q2 2026.",
            "guardian.example",
        ),
    ),
    pair(
        "P-TWITCH-REGISTER",
        "positive",
        "historical",
        article(
            "Twitch feeds streams to Amazon AI",
            "Twitch content is used for AI training.",
            "register.example",
        ),
        article(
            "Twitch users can block Amazon AI",
            "Twitch content can be excluded from AI training.",
            "bbc.example",
        ),
    ),
    pair(
        "U-TWITCH-VIDEO",
        "uncertain",
        "historical",
        article(
            "Video: Amazon uses Twitch to train AI",
            "Twitch content is used for AI training.",
            "bbc.example",
        ),
        article(
            "Twitch users can block Amazon AI",
            "Twitch content can be excluded from AI training.",
            "other.example",
        ),
    ),
    pair(
        "P-CREWE-CSTANDARD",
        "positive",
        "historical",
        article(
            "2,100-home estate proposed near Crewe",
            "Plans submitted for 2,100 homes in Crewe.",
            "standard.example",
            location="Crewe",
        ),
        article(
            "Plans for 2,100 homes in Crewe",
            "Planning proposal for 2,100 homes in Crewe.",
            "nantwich.example",
            location="Crewe",
        ),
    ),
    pair(
        "P-CREWE-CLIVE",
        "positive",
        "historical",
        article(
            "Plans lodged for 2,100 Crewe homes",
            "Plans submitted for 2,100 homes in Crewe.",
            "live.example",
            location="Crewe",
        ),
        article(
            "Plans for 2,100 homes in Crewe",
            "Planning proposal for 2,100 homes in Crewe.",
            "nantwich.example",
            location="Crewe",
        ),
    ),
    pair(
        "P-CREWE-LATER",
        "positive",
        "historical",
        article(
            "Plans lodged for 2,100 Crewe homes",
            "Plans submitted for 2,100 homes in Crewe.",
            "live.example",
            location="Crewe",
        ),
        article(
            "2,100-home estate proposed near Crewe",
            "Planning proposal for 2,100 homes in Crewe.",
            "standard.example",
            location="Crewe",
        ),
    ),
    pair(
        "N-SCHOOLS",
        "negative",
        "same_run",
        article(
            "Queen's Park High School celebrates A-level results",
            "School results in Chester.",
            "standard.example",
            location="Chester",
        ),
        article(
            "Ellesmere Port High School celebrates results",
            "Different school results.",
            "standard.example",
            location="Chester",
        ),
    ),
    pair(
        "N-HEATWAVE-FORECAST",
        "negative",
        "historical",
        article("Heatwave peaks", "Hottest day warning.", "guardian.example"),
        article("Heatwave begins", "Heat health alert.", "bbc.example"),
    ),
    pair(
        "N-HEATWAVE-STAGE",
        "negative",
        "historical",
        article("Final day of heatwave", "Cooldown follows.", "bbc.example"),
        article("Heatwave peaks", "Hottest day.", "guardian.example"),
    ),
    pair(
        "N-ROUNDUP-DERAIL",
        "negative",
        "historical",
        article(
            "The Papers: hottest day roundup",
            "A train derails among many stories.",
            "bbc.example",
        ),
        article(
            "Train derailment closes routes",
            "Single derailment report.",
            "guardian.example",
        ),
    ),
    pair(
        "N-HOUSING",
        "negative",
        "historical",
        article(
            "Plans for 452 homes", "A housing proposal at Site Alpha.", "live.example"
        ),
        article(
            "Plans for 2,100 homes",
            "A housing proposal at Site Beta.",
            "nantwich.example",
        ),
    ),
    pair(
        "N-ALEVEL-NATIONAL",
        "negative",
        "same_run",
        article(
            "Catholic High School Chester A-level results",
            "Local school results.",
            "standard.example",
        ),
        article(
            "Northern Ireland A-level grades rise",
            "National results statistics.",
            "bbc.example",
        ),
    ),
    pair(
        "N-WATER-SECTOR",
        "negative",
        "historical",
        article(
            "Water bills set to rise",
            "Thames Water bill funding decision.",
            "bbc.example",
        ),
        article(
            "Thames Water finance boss fee",
            "A £1 million signing fee.",
            "finance.example",
        ),
    ),
    pair(
        "P-BRITISH-STEEL",
        "positive",
        "same_run",
        article(
            "British Steel nationalised",
            "British Steel entered public ownership.",
            "bbc.example",
        ),
        article(
            "British Steel taken into public ownership",
            "The British Steel nationalisation decision.",
            "sky.example",
        ),
    ),
    pair(
        "P-PUBS-MEXICO",
        "positive",
        "same_run",
        article(
            "Pubs allowed to stay open until 5am for England Mexico match",
            "England face Mexico and pubs can open until 5am.",
            "bbc.example",
        ),
        article(
            "Starmer allows pubs to open until 5am for England v Mexico",
            "Pubs may open for the England Mexico match.",
            "guardian.example",
        ),
    ),
    pair(
        "P-BIGZY",
        "positive",
        "same_run",
        article(
            "Bigzy county drug line controller",
            "Bigzy flooded the town with cocaine and heroin.",
            "standard.example",
        ),
        article(
            "Bigzy drug line controller",
            "Bigzy flooded Widnes with cocaine and heroin.",
            "world.example",
        ),
    ),
    pair(
        "P-CHINESE-ROBOTS",
        "positive",
        "same_run",
        article(
            "US bans Chinese humanoid robots",
            "America bans imported Chinese robots for security reasons.",
            "bbc.example",
        ),
        article(
            "America bans imported robots",
            "The ban covers Chinese humanoid robots and supply-chain security.",
            "register.example",
        ),
    ),
    pair(
        "N-CHESTER-SCHOOLS",
        "negative",
        "same_run",
        article(
            "Catholic High School Chester results",
            "Students celebrate.",
            "standard.example",
            location="Chester",
        ),
        article(
            "Bishops Blue Coat School results",
            "Different students celebrate.",
            "standard.example",
            location="Chester",
        ),
    ),
    pair(
        "N-CHESTER-ENTITIES",
        "negative",
        "historical",
        article(
            "Chester hotel revamp",
            "A hotel reopened.",
            "live.example",
            location="Chester",
        ),
        article(
            "Chester emergency incident",
            "Emergency at other premises.",
            "standard.example",
            location="Chester",
        ),
    ),
    pair(
        "N-SCHOOL-STAGE",
        "negative",
        "historical",
        article(
            "Plans for new school set to clear vital hurdle",
            "A proposal is expected to receive a decision.",
            "standard.example",
        ),
        article(
            "Green light for new school",
            "The school was approved and construction will begin.",
            "live.example",
        ),
    ),
    pair(
        "N-SEA-UPDATE",
        "negative",
        "historical",
        article(
            "Man critical after sea rescue",
            "An emergency rescue incident.",
            "bbc.example",
        ),
        article(
            "Man and woman die after sea rescue",
            "A confirmed fatal outcome after the incident.",
            "other.example",
        ),
    ),
    pair(
        "N-BURNHAM-EVENTS",
        "negative",
        "historical",
        article(
            "Andy Burnham unveils drilling plans", "North Sea policy.", "bbc.example"
        ),
        article(
            "Inflation falls",
            "An unrelated reference to Andy Burnham.",
            "guardian.example",
        ),
    ),
    pair(
        "N-100-HOMES",
        "negative",
        "historical",
        article(
            "Plans for 100 homes at chemical works",
            "100 homes proposed at Site Alpha.",
            "live.example",
        ),
        article(
            "100 homes face refusal near Jodrell Bank",
            "100 homes at Site Beta.",
            "other.example",
        ),
    ),
    pair(
        "N-ENERGY-ANALYSIS",
        "negative",
        "same_run",
        article(
            "What will energy cap changes mean for bills?",
            "Ofgem cap explainer at £1,862.",
            "bbc.example",
        ),
        article(
            "Energy cap rise pushes millions into poverty",
            "Ofgem impact report at £1,862.",
            "guardian.example",
        ),
    ),
    pair(
        "N-FARAGE-FORMAT",
        "negative",
        "historical",
        article(
            "Why is Nigel Farage facing scrutiny?",
            "Reform UK finances explainer.",
            "bbc.example",
        ),
        article(
            "Nigel Farage gift row - UK politics live",
            "Reform UK live blog.",
            "guardian.example",
        ),
    ),
)

# Immutable outcomes from the two approved read-only calibration rounds. The
# bounded article fixtures above exercise the new evidence layer; these values
# retain the original scorer evidence without pretending reconstructed excerpts
# are byte-exact production documents.
CALIBRATION_RESULTS = {
    "P-WATER": (31, "low"),
    "P-GDP": (17, "low"),
    "U-GDP-ANALYSIS": (21, "low"),
    "P-TWITCH-REGISTER": (24, "low"),
    "U-TWITCH-VIDEO": (40, "low"),
    "P-CREWE-CSTANDARD": (67, "possible"),
    "P-CREWE-CLIVE": (57, "possible"),
    "P-CREWE-LATER": (51, "possible"),
    "N-SCHOOLS": (50, "possible"),
    "N-HEATWAVE-FORECAST": (24, "low"),
    "N-HEATWAVE-STAGE": (24, "low"),
    "N-ROUNDUP-DERAIL": (12, "low"),
    "N-HOUSING": (33, "low"),
    "N-ALEVEL-NATIONAL": (17, "low"),
    "N-WATER-SECTOR": (0, "low"),
    "P-BRITISH-STEEL": (28, "low"),
    "P-PUBS-MEXICO": (37, "low"),
    "P-BIGZY": (36, "low"),
    "P-CHINESE-ROBOTS": (31, "low"),
    "N-CHESTER-SCHOOLS": (43, "low"),
    "N-CHESTER-ENTITIES": (41, "low"),
    "N-SCHOOL-STAGE": (47, "low"),
    "N-SEA-UPDATE": (31, "low"),
    "N-BURNHAM-EVENTS": (14, "low"),
    "N-100-HOMES": (16, "low"),
    "N-ENERGY-ANALYSIS": (47, "low"),
    "N-FARAGE-FORMAT": (40, "low"),
}


def evidence(item):
    return similarity.event_anchor_evidence(
        item.candidate,
        item.existing,
        provenance=item.provenance,
    )


def test_complete_labelled_matrix_is_preserved():
    assert len(LABELLED_PAIRS) == 27
    assert sum(item.label == "positive" for item in LABELLED_PAIRS) == 10
    assert sum(item.label == "negative" for item in LABELLED_PAIRS) == 15
    assert sum(item.label == "uncertain" for item in LABELLED_PAIRS) == 2
    assert len({item.pair_id for item in LABELLED_PAIRS}) == 27
    assert set(CALIBRATION_RESULTS) == {item.pair_id for item in LABELLED_PAIRS}
    assert (
        min(
            CALIBRATION_RESULTS[item.pair_id][0]
            for item in LABELLED_PAIRS
            if item.label == "positive"
        )
        == 17
    )
    assert (
        max(
            CALIBRATION_RESULTS[item.pair_id][0]
            for item in LABELLED_PAIRS
            if item.label == "negative"
        )
        == 50
    )


def test_six_same_run_cross_source_positives_have_compatible_shadow_evidence():
    items = [
        item
        for item in LABELLED_PAIRS
        if item.label == "positive" and item.provenance == "same_run"
    ]
    assert len(items) == 6
    assert all(evidence(item).same_run_cross_source_compatible for item in items)


def test_no_definite_negative_satisfies_conservative_shadow_contract():
    negatives = [item for item in LABELLED_PAIRS if item.label == "negative"]
    assert len(negatives) == 15
    assert not any(
        evidence(item).same_run_cross_source_compatible for item in negatives
    )


def test_uncertain_pairs_remain_non_decisive():
    uncertain = [item for item in LABELLED_PAIRS if item.label == "uncertain"]
    assert len(uncertain) == 2
    assert not any(
        evidence(item).same_run_cross_source_compatible for item in uncertain
    )
    assert evidence(uncertain[0]).format_relation == "guard"
    assert evidence(uncertain[1]).format_relation == "guard"


def test_historical_positives_can_expose_anchors_but_never_pass_same_run_contract():
    historical = [
        item
        for item in LABELLED_PAIRS
        if item.label == "positive" and item.provenance == "historical"
    ]
    assert len(historical) == 4
    assert all(evidence(item).shared_event_phrases for item in historical)
    assert not any(
        evidence(item).same_run_cross_source_compatible for item in historical
    )


@pytest.mark.parametrize(
    ("pair_id", "expected_anchor"),
    (
        ("P-WATER", "water_bill_funding_decision"),
        ("P-GDP", "uk_economic_growth_release"),
        ("P-TWITCH-REGISTER", "twitch_ai_training_policy"),
        ("P-CREWE-CSTANDARD", "crewe_2100_home_plan"),
        ("P-BRITISH-STEEL", "british_steel_public_ownership"),
        ("P-PUBS-MEXICO", "england_mexico_pub_hours"),
        ("P-BIGZY", "bigzy_drug_line"),
        ("P-CHINESE-ROBOTS", "china_robot_import_prohibition"),
    ),
)
def test_reviewed_positive_event_phrases(pair_id, expected_anchor):
    item = next(item for item in LABELLED_PAIRS if item.pair_id == pair_id)
    assert expected_anchor in evidence(item).shared_event_phrases


def test_exact_entity_and_locality_boundaries_do_not_conflate_chester_records():
    schools = next(
        item for item in LABELLED_PAIRS if item.pair_id == "N-CHESTER-SCHOOLS"
    )
    result = evidence(schools)
    assert result.shared_localities == ("chester",)
    assert set(similarity._event_entity_anchors(schools.candidate)).isdisjoint(
        similarity._event_entity_anchors(schools.existing)
    )
    false_hough = similarity.event_anchor_evidence(
        article("Traffic through town", "A route through Crewe.", "one.example"),
        article("Hough planning update", "A proposal in Hough.", "two.example"),
        provenance="same_run",
    )
    assert "hough" not in false_hough.shared_localities


def test_quantity_normalisation_is_typed_bounded_and_never_sufficient_alone():
    first = article(
        "Figures", "£1,862, 0.4%, 2,100 homes, 5am, 31C and Q2 2026.", "one.example"
    )
    second = article(
        "Other figures", "£1,862 and 2,100 homes at 5am in 2026 Q2.", "two.example"
    )
    result = similarity.event_anchor_evidence(first, second, provenance="same_run")
    assert {
        "currency:gbp:1862",
        "percentage:0.4",
        "count:2100:home",
        "time:05:00",
        "reporting_period:2026:q2",
    } >= set(result.shared_quantities)
    assert "currency:gbp:1862" in result.shared_quantities
    assert "count:2100:home" in result.shared_quantities
    assert result.same_run_cross_source_compatible is False
    assert (
        len(similarity._event_quantitative_anchors(first))
        <= similarity.MAX_EVENT_QUANTITY_ANCHORS
    )


def test_stage_transitions_and_format_guards_are_explicit():
    school = next(item for item in LABELLED_PAIRS if item.pair_id == "N-SCHOOL-STAGE")
    rescue = next(item for item in LABELLED_PAIRS if item.pair_id == "N-SEA-UPDATE")
    energy = next(
        item for item in LABELLED_PAIRS if item.pair_id == "N-ENERGY-ANALYSIS"
    )
    farage = next(item for item in LABELLED_PAIRS if item.pair_id == "N-FARAGE-FORMAT")
    assert evidence(school).stage_relation == "material_transition"
    assert evidence(rescue).stage_relation == "material_transition"
    assert evidence(energy).format_relation == "guard"
    assert evidence(farage).format_relation == "guard"


def test_same_entity_different_event_and_same_number_different_site_do_not_pass():
    company = next(item for item in LABELLED_PAIRS if item.pair_id == "N-WATER-SECTOR")
    homes = next(item for item in LABELLED_PAIRS if item.pair_id == "N-100-HOMES")
    person = next(item for item in LABELLED_PAIRS if item.pair_id == "N-BURNHAM-EVENTS")
    assert not evidence(company).same_run_cross_source_compatible
    assert not evidence(homes).same_run_cross_source_compatible
    assert not evidence(person).same_run_cross_source_compatible


def test_www_variant_is_not_mistaken_for_a_cross_source_pair():
    candidate = article(
        "British Steel nationalised",
        "British Steel entered public ownership.",
        "www.publisher.example",
    )
    existing = article(
        "British Steel public ownership",
        "British Steel was nationalised.",
        "publisher.example",
    )
    assert not similarity.event_anchor_evidence(
        candidate, existing, provenance="same_run"
    ).same_run_cross_source_compatible


def test_evidence_is_bounded_deterministic_fail_safe_and_non_mutating():
    candidate = article(
        "British Steel nationalised " * 100, "£1 " * 1_000, "one.example"
    )
    existing = article(
        "British Steel public ownership " * 100, "£1 " * 1_000, "two.example"
    )
    before = (deepcopy(candidate), deepcopy(existing))
    first = similarity.event_anchor_evidence(candidate, existing, provenance="same_run")
    second = similarity.event_anchor_evidence(
        candidate, existing, provenance="same_run"
    )
    assert first == second
    assert (candidate, existing) == before
    assert len(first.shared_entities) <= similarity.MAX_EVENT_ENTITY_ANCHORS
    assert len(first.shared_event_phrases) <= similarity.MAX_EVENT_PHRASE_ANCHORS
    assert len(first.shared_quantities) <= similarity.MAX_EVENT_QUANTITY_ANCHORS
    assert len(first.shared_localities) <= similarity.MAX_EVENT_LOCALITY_ANCHORS
    assert len(first.evidence_codes) <= similarity.MAX_EVENT_EVIDENCE_CODES
    assert all(
        len(value) <= similarity.MAX_EVENT_ANCHOR_CHARACTERS
        for values in (
            first.shared_entities,
            first.shared_event_phrases,
            first.shared_quantities,
            first.shared_localities,
        )
        for value in values
    )
    assert (
        similarity.event_anchor_evidence(
            {"title": object()}, {}, provenance="same_run"
        ).same_run_cross_source_compatible
        is False
    )


def test_feature_never_adds_or_changes_publication_state():
    candidate = article(
        "British Steel nationalised",
        "British Steel entered public ownership.",
        "one.example",
    )
    existing = article(
        "British Steel public ownership",
        "British Steel was nationalised.",
        "two.example",
    )
    candidate.update(
        manual_review_hidden_from_public=False,
        verification_status="verified",
        rewrite_status="complete",
        force_live=True,
    )
    before = deepcopy(candidate)
    similarity.event_anchor_evidence(candidate, existing, provenance="same_run")
    assert candidate == before
    for field in ("archive_reason", "archived"):
        assert field not in candidate


def test_event_evidence_does_not_change_existing_score_or_band():
    item = next(item for item in LABELLED_PAIRS if item.pair_id == "P-WATER")
    before = similarity.score_editorial_similarity(item.candidate, item.existing)
    similarity.event_anchor_evidence(
        item.candidate, item.existing, provenance=item.provenance
    )
    after = similarity.score_editorial_similarity(item.candidate, item.existing)
    assert after == before
