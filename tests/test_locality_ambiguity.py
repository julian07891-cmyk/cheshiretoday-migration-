"""Offline locality regression; retained-case summaries, not live source fetches."""
import copy

import pytest

from tests.test_local_rss_manual_review_routing import (
    FULL_REWRITE, Perplexity, candidate, run_import, server,
)


TITLE = "Planning committee set to review demolition plans for Heswall pub"
TEXT = (
    "Wirral Council will decide the plans for the Glegg Arms in Heswall. "
    "The pub is on Chester Road in Heswall."
)
REASON = "locality_ambiguous_out_of_area"

M53_TITLE = (
    "Man in hospital and severe delays through Wallasey Tunnel and M53 "
    "following crash"
)
M53_RSS_TEXT = (
    "Liverpool crash leaves pedestrian in hospital as Hunter Street closure "
    "causes delays on Kingsway and Queensway tunnels, M53 and bus routes on "
    "October 14."
)
M53_REWRITE = """A man was taken to hospital after being hit by a vehicle in Liverpool, causing significant delays for traffic travelling between Wirral and the city centre.

The collision happened on Hunter Street at about 6.05am on Wednesday, October 14. Merseyside Police said the male pedestrian was taken to hospital for assessment, while the driver stopped at the scene.

Hunter Street was closed eastbound between the A59 Byrom Street and A580 Islington. Police advised motorists to avoid the area where possible.

The closure led to queues stretching towards the Kingsway Tunnel and back along the M53 through Birkenhead. Delays were also reported at the Queensway Tunnel.

Traffic monitoring information showed delays of about 28 minutes on the eastbound Kingsway Tunnel, with average speeds of around 5mph. Northbound traffic on the M53 was delayed by about 21 minutes between junction two for the Moreton Spur and the A59.

Northbound traffic approaching the Queensway Tunnel faced delays of about 14 minutes, also travelling at around 5mph.

Bus services were affected, with Merseytravel reporting that services 26 and 53 leaving Liverpool city centre were diverted. The revised route ran via St Johns Lane, Lime Street, London Road and Norton Street to St Anne Street, where services resumed their normal routes.

The Hunter Street closure was reported to have ended at about 8.50am, with delays on the Kingsway Tunnel and M53 easing shortly after 9am.

Anyone who witnessed the collision or was travelling through the area with dashcam footage has been asked to contact Merseyside Police via @MerPolCC or 101, quoting reference 117."""


def m53_wallasey_candidate(**values):
    document = {
        "content": M53_RSS_TEXT,
        "source": "Chester Standard",
        "source_url": (
            "https://www.chesterstandard.co.uk/news/"
            "26634733.man-hospitalised-crash---severe-delays-kingsway-tunnel-m53/"
            "?ref=rss"
        ),
        "location": "chester",
        "is_local_feed": True,
        "is_local_source": True,
        "is_cheshire_related": True,
    }
    document.update(values)
    return candidate(M53_TITLE, **document)


def test_wallasey_m53_rss_candidate_routes_to_review_before_provider(monkeypatch):
    provider_calls = []
    story = m53_wallasey_candidate()

    result, inserted = run_import(
        monkeypatch,
        [story],
        rewrites={M53_TITLE: M53_REWRITE},
        provider_calls=provider_calls,
    )

    assert provider_calls == []
    assert result["public_imported"] == 0
    assert result["manual_review_imported"] == 1
    assert len(inserted) == 1
    assert inserted[0]["manual_review_hidden_from_public"] is True
    assert inserted[0]["manual_review_reason"] == REASON
    assert inserted[0]["verification_status"] == "needs_manual_review"
    assert inserted[0]["rewrite_status"] == "manual_review_required"
    assert not inserted[0].get("archived")


def test_wallasey_m53_rewrite_is_caught_by_final_locality_guard():
    story = m53_wallasey_candidate(content=M53_REWRITE)

    assert server.count_article_words(M53_REWRITE) >= 200
    assert (
        server.find_local_location_review_reason(story, M53_REWRITE, M53_TITLE)
        == REASON
    )

    saved = server.apply_ai_manual_review_guard(
        story,
        M53_REWRITE,
        True,
        M53_TITLE,
    )

    assert saved["manual_review_hidden_from_public"] is True
    assert REASON in saved["manual_review_reason"]
    assert saved["verification_status"] == "needs_manual_review"
    assert saved["rewrite_status"] == "manual_review_required"
    assert not saved.get("archived")


def m53_complete_conflict_reason(extra_text):
    content = f"{M53_REWRITE}\n\n{extra_text}"
    story = m53_wallasey_candidate(content=content)
    return server.find_local_location_review_reason(story, content, M53_TITLE)


def test_complete_m53_conflict_incidental_chester_reference_still_routes_to_review():
    assert m53_complete_conflict_reason(
        "The M53 provides regional links towards Chester."
    ) == REASON


@pytest.mark.parametrize(
    "unrelated_same_sentence_reference",
    [
        (
            "The collision affected traffic in Birkenhead, while Chester was "
            "mentioned only as regional background."
        ),
        (
            "The collision delayed traffic in Wallasey, while a Cheshire West "
            "school transport service was discussed in unrelated background."
        ),
    ],
)
def test_complete_m53_conflict_requires_impact_attributed_to_cheshire(
    unrelated_same_sentence_reference,
):
    assert m53_complete_conflict_reason(unrelated_same_sentence_reference) == REASON


@pytest.mark.parametrize(
    "material_impact",
    [
        "Traffic queues extended to Hooton, affecting journeys towards Ellesmere Port.",
        "The collision disrupted a named Cheshire West school transport service.",
        "Hooton traffic was delayed by the collision.",
        "Traffic was disrupted in Hooton; queues extended towards Ellesmere Port.",
    ],
)
def test_complete_m53_conflict_with_confirmed_cheshire_impact_remains_eligible(
    material_impact,
):
    assert m53_complete_conflict_reason(material_impact) == ""


def test_complete_m53_conflict_unrelated_cheshire_service_still_routes_to_review():
    assert m53_complete_conflict_reason(
        "A Cheshire West school transport service was mentioned in unrelated "
        "background and was not affected by the collision."
    ) == REASON


@pytest.mark.parametrize(
    "unconfirmed_impact",
    [
        "No disruption was reported at Hooton.",
        "Traffic may affect Ellesmere Port.",
    ],
)
def test_complete_m53_conflict_unconfirmed_cheshire_impact_routes_to_review(
    unconfirmed_impact,
):
    assert m53_complete_conflict_reason(unconfirmed_impact) == REASON


@pytest.mark.parametrize(
    "title,text",
    [
        (
            "£50m M53 works set to start between Ellesmere Port and Wirral",
            "Four bridges on the M53 between Ellesmere Port and Wirral will be replaced.",
        ),
        (
            "M53 disruption affects Hooton services",
            "An M53 closure at Hooton is disrupting local bus and rail connections.",
        ),
        (
            "M53 disruption affects Ellesmere Port",
            "Traffic is delayed on the M53 at Ellesmere Port after an incident.",
        ),
        (
            "Liverpool incident disrupts named Cheshire service",
            "A Liverpool road closure has disrupted a Cheshire West school transport service.",
        ),
    ],
)
def test_material_cross_border_m53_or_service_impact_remains_eligible(title, text):
    article = candidate(
        title,
        content=text,
        source="Chester Standard",
        location="chester",
        is_local_feed=True,
        is_local_source=True,
    )

    assert server.find_local_location_review_reason(article, text, title) == ""


@pytest.mark.parametrize("location", ["chester", None])
def test_heswall_final_guard_hides_road_only_locality(location):
    article = candidate(TITLE, content=TEXT, location=location)
    saved = server.apply_ai_manual_review_guard(article, TEXT, False, TITLE)
    assert saved.get("manual_review_hidden_from_public") is True
    assert REASON in saved["manual_review_reason"]
    assert saved["verification_status"] == "needs_manual_review"
    assert not saved.get("archived")


@pytest.mark.parametrize("title,text", [
    # Explicitly synthetic: no retained Chester-city + Chester Road case found.
    ("Chester planning decision", "A site in Chester on Chester Road will be improved."),
    ("Ellesmere Port care home", "The home on Chester Road in Ellesmere Port was assessed."),
    ("Haslington homes", "Cheshire East considers homes off Crewe Road, Haslington."),
    ("Cranage road works", "Cheshire East Highways will work on Knutsford Road in Cranage."),
    ("Culcheth housing", "Homes are proposed off Warrington Road in Culcheth."),
    ("Great Sutton redevelopment", "Work starts on Old Chester Road in Great Sutton."),
    ("Chester Zoo investment", "Chester Zoo confirmed the investment."),
    ("Wilmslow cafe", "A Knutsford Road cafe in Wilmslow took inspiration from Italy."),
    ("Chester redevelopment", "A Chester site will be improved. A previous project involved Wirral Council in Heswall on Chester Road."),
    ("Road development", "A site on Chester Road will be improved. Background comparisons refer to Wirral Council and Heswall."),
])
def test_legitimate_or_background_road_mentions_preserve_existing_locality(title, text):
    article = candidate(title, content=text, source="Chester Standard")
    assert server.find_local_location_review_reason(article, text, title) == ""


def test_feed_metadata_alone_still_does_not_establish_locality():
    article = candidate("Planning decision", content="The council will decide.")
    assert server.find_local_location_review_reason(article, article["content"], article["title"])


def test_existing_stronger_archive_state_is_not_removed():
    article = candidate(TITLE, content=TEXT, archived=True, archive_reason="existing_review")
    saved = server.apply_ai_manual_review_guard(article, TEXT, False, TITLE)
    assert saved["archived"] is True
    assert saved["archive_reason"] == "existing_review"
    assert REASON in saved["manual_review_reason"]


@pytest.mark.parametrize("location", ["chester", None])
def test_early_review_skips_provider_and_leaves_local_and_topic_capacity(monkeypatch, location):
    calls = []
    async def rewrite(self, **kwargs):
        calls.append(kwargs["title"])
        return FULL_REWRITE
    monkeypatch.setattr(Perplexity, "generate_article_content", rewrite)
    original_request = server.HybridNewsRequest
    def one_local(**kwargs):
        return original_request(**{**kwargs, "cheshire_articles": 1})
    monkeypatch.setattr(server, "HybridNewsRequest", one_local)
    first = candidate(TITLE, content=TEXT, location=location, source="Chester Standard")
    original = copy.deepcopy(first)
    later = candidate("Chester council approves plans for 50 new homes")
    result, inserted = run_import(monkeypatch, [first, later])
    assert calls == [later["title"]]
    assert result["public_imported"] == 1
    assert result["manual_review_imported"] == 1
    assert result["cheshire_from_rss"] == 1
    assert len(inserted) == 2
    assert inserted[0]["manual_review_hidden_from_public"] is True
    assert inserted[0]["manual_review_reason"] == REASON
    assert inserted[0]["verification_status"] == "needs_manual_review"
    assert not inserted[0].get("archived")
    assert not inserted[1].get("manual_review_hidden_from_public")
    assert first == original


def test_body_only_conflict_hides_final_record_and_preserves_final_accounting(monkeypatch):
    title = "Planning committee considers pub development"
    first = candidate(title, content="Plans concern a pub on Chester Road.")
    later = candidate("Chester council approves plans for 50 new homes")
    result, inserted = run_import(monkeypatch, [first, later], rewrites={title: TEXT + "\n\n" + FULL_REWRITE})
    assert result["public_imported"] == 0
    assert result["manual_review_imported"] == 2
    assert result["cheshire_from_rss"] == 1
    assert REASON in inserted[0]["manual_review_reason"]
    assert inserted[0]["manual_review_hidden_from_public"] is True
    assert not inserted[0].get("archived")
    assert "planning_housing" in inserted[1]["manual_review_reason"]
