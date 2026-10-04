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
