import asyncio
import inspect
import json
from datetime import datetime, timezone

import pytest

from backend.app import local_rss_editorial_policy as production_policy
from backend.scripts import evaluate_newsquest_local_shadow as shadow
from backend.scripts.evaluate_cheshire_rss_shadow import FetchResult


AS_OF = datetime(2026, 7, 25, 12, 0, tzinfo=timezone.utc)


def rss(items):
    rendered = []
    for item in items:
        rendered.append(
            f"""
            <item>
              <title><![CDATA[{item["title"]}]]></title>
              <link>{item.get("url", "https://publisher.test/story")}</link>
              <description><![CDATA[{item.get("summary", "")}]]></description>
              <pubDate>{item.get("date", "Fri, 24 Jul 2026 09:00:00 +0000")}</pubDate>
              {item.get("media", '<media:content url="https://img.test/story.jpg" type="image/jpeg"/>')}
            </item>
            """
        )
    return (
        '<?xml version="1.0"?><rss xmlns:media="http://search.yahoo.com/mrss/">'
        "<channel>" + "".join(rendered) + "</channel></rss>"
    ).encode()


class Fetch:
    def __init__(self, bodies):
        self.bodies = bodies

    async def __call__(self, url):
        return FetchResult(200, self.bodies[url], "application/rss+xml")


def feed(key, source, url, terms):
    from backend.scripts.evaluate_cheshire_rss_shadow import CandidateFeed

    return CandidateFeed(key, source, url, terms)


def evaluate(feeds, bodies, **kwargs):
    return asyncio.run(
        shadow.evaluate(
            fetch=Fetch(bodies),
            as_of=AS_OF,
            feeds=feeds,
            comparison_feeds=(),
            **kwargs,
        )
    )


def test_zero_write_and_no_database_or_production_import_contract():
    source = inspect.getsource(shadow)
    policy_source = inspect.getsource(production_policy)
    assert "backend.server" not in source
    assert "pymongo" not in source
    assert "motor" not in source
    assert "insert_one" not in source
    assert "update_one" not in source
    assert "delete_one" not in source
    assert "RSS_FEEDS[" not in source
    assert "pymongo" not in policy_source
    assert "import motor" not in policy_source
    assert "from motor" not in policy_source
    assert "insert_one" not in policy_source
    assert "update_one" not in policy_source
    assert "delete_one" not in policy_source
    assert "PRODUCTION_LOCAL_CRIME_RE" not in source
    assert "CIVIC_ECONOMIC_TERMS" not in source


def test_cross_newsquest_duplicate_detection():
    first = feed("north", "Northwich", "https://one.test/rss", ("northwich",))
    second = feed("knuts", "Knutsford", "https://two.test/rss", ("knutsford",))
    title = "Council approves major Cheshire railway investment"
    report = evaluate(
        (first, second),
        {
            first.url: rss(
                [
                    {
                        "title": title,
                        "url": "https://one.test/story",
                        "summary": "Northwich council confirms railway investment.",
                    }
                ]
            ),
            second.url: rss(
                [
                    {
                        "title": title,
                        "url": "https://two.test/story",
                        "summary": "Knutsford council confirms railway investment.",
                    }
                ]
            ),
        },
    )
    assert report["feeds"][0]["outcome_counts"]["auto_publication_path"] == 1
    assert report["feeds"][1]["duplicate_counts"]["evaluated_newsquest_feed"] == 1
    assert "duplicate exact title" in report["feeds"][1]["hard_rejected"][0]["reasons"]


def test_town_relevance_failure_is_hard_rejected():
    candidate = feed("north", "Northwich", "https://one.test/rss", ("northwich",))
    report = evaluate(
        (candidate,),
        {
            candidate.url: rss(
                [
                    {
                        "title": "Council approves major railway investment",
                        "summary": "A project in Birmingham has been approved.",
                    }
                ]
            )
        },
    )
    assert report["feeds"][0]["town_relevant"] == 0
    assert "non-local" in report["feeds"][0]["hard_rejected"][0]["reasons"]


def test_crime_and_court_are_hard_rejected():
    candidate = feed("north", "Northwich", "https://one.test/rss", ("northwich",))
    report = evaluate(
        (candidate,),
        {
            candidate.url: rss(
                [
                    {
                        "title": "Northwich man jailed after court case",
                        "summary": "Police said he was sentenced.",
                    }
                ]
            )
        },
    )
    assert "crime/court" in report["feeds"][0]["hard_rejected"][0]["reasons"]


def test_obituary_is_hard_rejected_by_shared_policy():
    candidate = feed("knuts", "Knutsford", "https://one.test/rss", ("knutsford",))
    report = evaluate(
        (candidate,),
        {
            candidate.url: rss(
                [
                    {
                        "title": "Knutsford death notices and funeral announcements",
                        "summary": "Family announcements from Knutsford.",
                    }
                ]
            )
        },
    )
    assert "obituary" in report["feeds"][0]["hard_rejected"][0]["reasons"]


def test_promotional_or_sponsored_item_is_hard_rejected():
    candidate = feed("north", "Northwich", "https://one.test/rss", ("northwich",))
    report = evaluate(
        (candidate,),
        {
            candidate.url: rss(
                [
                    {
                        "title": "Sponsored Northwich shopping deal",
                        "summary": "Partner content promoting an affiliate casino.",
                    }
                ]
            )
        },
    )
    assert (
        "promotional/sponsored"
        in report["feeds"][0]["hard_rejected"][0]["reasons"]
    )


def test_production_local_crime_vocabulary_cannot_enter_manual_review():
    candidate = feed("north", "Northwich", "https://one.test/rss", ("northwich",))
    report = evaluate(
        (candidate,),
        {
            candidate.url: rss(
                [
                    {
                        "title": "Appeal after motorbike stolen outside Northwich home",
                        "summary": "Police asked witnesses to come forward.",
                    }
                ]
            )
        },
    )
    assert report["feeds"][0]["outcome_counts"]["manual_review"] == 0
    assert "crime/court" in report["feeds"][0]["hard_rejected"][0]["reasons"]


def test_usable_image_recognition_and_missing_image_rejection():
    candidate = feed("north", "Northwich", "https://one.test/rss", ("northwich",))
    report = evaluate(
        (candidate,),
        {
            candidate.url: rss(
                [
                    {
                        "title": "Northwich council investment approved",
                        "summary": "Northwich transport investment.",
                    },
                    {
                        "title": "Northwich school investment approved",
                        "url": "https://one.test/no-image",
                        "summary": "Northwich school investment.",
                        "media": "",
                    },
                ]
            )
        },
    )
    assert report["feeds"][0]["usable_images"] == 1
    assert "missing image" in report["feeds"][0]["hard_rejected"][0]["reasons"]


def test_civic_economic_story_enters_strict_auto_publication_path():
    candidate = feed("north", "Northwich", "https://one.test/rss", ("northwich",))
    report = evaluate(
        (candidate,),
        {
            candidate.url: rss(
                [
                    {
                        "title": "Northwich council backs town centre investment",
                        "summary": "New transport and business funding was approved.",
                    }
                ]
            )
        },
    )
    outcome = report["feeds"][0]["auto_publication_path"]
    assert outcome == [
        {
            "title": "Northwich council backs town centre investment",
            "reason": "civic/economic candidate",
        }
    ]


def test_soft_local_story_is_routed_to_manual_review():
    candidate = feed("knuts", "Knutsford", "https://one.test/rss", ("knutsford",))
    report = evaluate(
        (candidate,),
        {
            candidate.url: rss(
                [
                    {
                        "title": "Knutsford community celebrates volunteer",
                        "summary": "Residents gathered to celebrate a local volunteer.",
                    }
                ]
            )
        },
    )
    assert report["feeds"][0]["manual_review"] == [
        {
            "title": "Knutsford community celebrates volunteer",
            "reason": "Community feature",
        }
    ]


def test_existing_article_and_configured_feed_duplicates_are_distinguished():
    candidate = feed("north", "Northwich", "https://one.test/rss", ("northwich",))
    existing_title = "Northwich council transport investment"
    report = evaluate(
        (candidate,),
        {
            candidate.url: rss(
                [
                    {
                        "title": existing_title,
                        "summary": "Northwich council transport investment.",
                    }
                ]
            )
        },
        existing_titles={shadow.normalize_title(existing_title)},
    )
    assert report["feeds"][0]["duplicate_counts"]["existing_cheshire_today"] == 1


def test_existing_snapshot_canonical_url_duplicate_is_rejected():
    candidate = feed("north", "Northwich", "https://one.test/rss", ("northwich",))
    report = evaluate(
        (candidate,),
        {
            candidate.url: rss(
                [
                    {
                        "title": "Northwich council confirms transport funding",
                        "url": "https://publisher.test/story?utm_source=rss",
                        "summary": "Northwich council transport investment.",
                    }
                ]
            )
        },
        existing_urls={"https://publisher.test/story"},
    )
    rejected = report["feeds"][0]["hard_rejected"][0]
    assert "existing Cheshire Today article" in rejected["reasons"]
    assert report["feeds"][0]["duplicate_counts"]["existing_cheshire_today"] == 1


def test_existing_snapshot_rejects_unapproved_fields(tmp_path):
    snapshot = tmp_path / "existing.json"
    snapshot.write_text(
        json.dumps(
            [
                {
                    "title": "Allowed title",
                    "source_url": "https://example.test/story",
                    "content": "must not be accepted",
                }
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="only title and source_url"):
        shadow._load_existing_snapshot(snapshot)


def test_multiple_usable_candidates_are_reported_without_writes():
    candidate = feed("halton", "Halton", "https://one.test/rss", ("runcorn",))
    report = evaluate(
        (candidate,),
        {
            candidate.url: rss(
                [
                    {
                        "title": "Runcorn council approves housing investment",
                        "url": "https://one.test/one",
                        "summary": "Runcorn housing and infrastructure investment.",
                    },
                    {
                        "title": "Runcorn community marks local anniversary",
                        "url": "https://one.test/two",
                        "summary": "The Runcorn community held a celebration.",
                    },
                ]
            )
        },
    )
    assert report["totals"]["unique_usable_yield"] == 2
    assert report["database_writes"] == 0
    assert report["publication_writes"] == 0
    assert report["manual_review_writes"] == 0


def test_rejected_cross_feed_story_is_diagnosed_but_does_not_poison_later_use():
    first = feed("north", "Northwich", "https://one.test/rss", ("northwich",))
    second = feed("knuts", "Knutsford", "https://two.test/rss", ("knutsford",))
    title = "Council approves major railway investment"
    report = evaluate(
        (first, second),
        {
            first.url: rss(
                [
                    {
                        "title": title,
                        "url": "https://one.test/story",
                        "summary": "A Knutsford council railway investment.",
                    }
                ]
            ),
            second.url: rss(
                [
                    {
                        "title": title,
                        "url": "https://two.test/story",
                        "summary": "Knutsford council confirms railway investment.",
                    }
                ]
            ),
        },
    )
    assert report["feeds"][0]["duplicate_counts"]["evaluated_newsquest_feed"] == 1
    assert report["feeds"][1]["duplicate_counts"]["evaluated_newsquest_feed"] == 1
    assert report["feeds"][1]["outcome_counts"]["auto_publication_path"] == 1


def test_one_feed_failure_fails_safely_without_affecting_other_feed():
    failed = feed("failed", "Failed", "https://failed.test/rss", ("northwich",))
    healthy = feed("healthy", "Healthy", "https://healthy.test/rss", ("knutsford",))

    class MixedFetch:
        async def __call__(self, url):
            if url == failed.url:
                return FetchResult(503, b"", "text/plain")
            return FetchResult(
                200,
                rss(
                    [
                        {
                            "title": "Knutsford council transport investment",
                            "summary": "Knutsford infrastructure funding.",
                        }
                    ]
                ),
                "application/rss+xml",
            )

    report = asyncio.run(
        shadow.evaluate(
            fetch=MixedFetch(),
            as_of=AS_OF,
            feeds=(failed, healthy),
            comparison_feeds=(),
        )
    )
    assert report["feeds"][0]["error"] == "HTTP 503"
    assert report["feeds"][0]["raw_articles"] == 0
    assert report["feeds"][1]["outcome_counts"]["auto_publication_path"] == 1
    assert report["database_writes"] == 0
    assert report["publication_writes"] == 0
    assert report["manual_review_writes"] == 0
