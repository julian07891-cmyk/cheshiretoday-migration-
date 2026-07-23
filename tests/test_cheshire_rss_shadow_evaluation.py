import asyncio
import copy
import importlib
import inspect
import json
import subprocess
import sys
from datetime import datetime, timezone

import pytest

from backend.app.news_feed_service import RSS_FEEDS
from backend.scripts import evaluate_cheshire_rss_shadow as shadow


AS_OF = datetime(2026, 7, 22, 12, 0, tzinfo=timezone.utc)


def rss(items):
    rendered = []
    for item in items:
        categories = "".join(
            f"<category><![CDATA[{c}]]></category>" for c in item.get("categories", [])
        )
        media = item.get("media", "")
        content = item.get("content", "")
        rendered.append(
            f"""
            <item>
              <title><![CDATA[{item['title']}]]></title>
              <link>{item.get('link', '')}</link>
              <description><![CDATA[{item.get('summary', '')}]]></description>
              <content:encoded><![CDATA[{content}]]></content:encoded>
              <pubDate>{item.get('date', 'Tue, 21 Jul 2026 09:00:00 +0000')}</pubDate>
              {categories}{media}
            </item>
            """
        )
    return (
        '<?xml version="1.0"?><rss xmlns:content="http://purl.org/rss/1.0/modules/content/" '
        'xmlns:media="http://search.yahoo.com/mrss/"><channel>'
        + "".join(rendered)
        + "</channel></rss>"
    ).encode()


def item(title, link="https://example.test/story", **overrides):
    base = {
        "title": title,
        "link": link,
        "summary": "Nantwich council approves investment in transport infrastructure.",
        "media": '<media:content url="https://img.example.test/story.jpg" type="image/jpeg"/>',
    }
    base.update(overrides)
    return base


class FakeFetch:
    def __init__(self, bodies):
        self.bodies = bodies
        self.calls = []

    async def __call__(self, url):
        self.calls.append(url)
        result = self.bodies[url]
        if isinstance(result, Exception):
            raise result
        return result


def feed(
    key="candidate",
    source="Candidate",
    url="https://feed.test/rss",
    terms=("nantwich",),
    wordpress=False,
):
    return shadow.CandidateFeed(key, source, url, terms, wordpress)


def run_one(items, *, candidate=None, comparison=()):
    candidate = candidate or feed()
    fetch = FakeFetch(
        {
            candidate.url: shadow.FetchResult(200, rss(items), "application/rss+xml"),
        }
    )
    return asyncio.run(
        shadow.evaluate(
            fetch=fetch,
            as_of=AS_OF,
            candidate_feeds=(candidate,),
            comparison_feeds=comparison,
        )
    )


def test_import_isolation_and_no_database_or_runtime_imports(monkeypatch):
    monkeypatch.setattr(
        "httpx.AsyncClient", lambda *a, **k: pytest.fail("network access")
    )
    reloaded = importlib.reload(shadow)
    source = inspect.getsource(reloaded)
    assert "backend.server" not in source
    assert "pymongo" not in source
    assert "motor" not in source
    assert "insert_one" not in source
    assert "update_one" not in source
    assert "delete_one" not in source


def test_newsquest_media_content_and_thumbnail_are_extracted():
    parsed = shadow.parse_feed(
        rss(
            [
                item(
                    "Nantwich council investment plan",
                    media='<media:content url="https://img.test/full.jpg" type="image/jpeg"/>',
                ),
                item(
                    "Nantwich school transport plan",
                    link="https://example.test/two",
                    media='<media:thumbnail url="https://img.test/thumb.jpg"/>',
                ),
            ]
        ),
        feed(),
    )
    assert [entry.image for entry in parsed] == [
        "https://img.test/full.jpg",
        "https://img.test/thumb.jpg",
    ]


def test_wordpress_content_encoded_featured_image_and_ldrs_are_recognised():
    candidate = feed(wordpress=True)
    parsed = shadow.parse_feed(
        rss(
            [
                item(
                    "Nantwich schools investment",
                    media="",
                    content='<img src="https://img.test/wp.jpg"><p>By a Local Democracy Reporter</p>',
                )
            ]
        ),
        candidate,
    )
    assert parsed[0].image == "https://img.test/wp.jpg"
    assert parsed[0].ldrs_attribution is True


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("https://EXAMPLE.test/a/?ref=rss&utm_source=x#part", "https://example.test/a"),
        ("https://example.test/a?keep=1&fbclid=x", "https://example.test/a?keep=1"),
        ("https://example.test:invalid/a", ""),
        ("not a url", ""),
    ],
)
def test_canonical_url_normalisation(raw, expected):
    assert shadow.canonicalize_url(raw) == expected


@pytest.mark.parametrize(
    "title, reason",
    [
        ("Nantwich man jailed after court hearing", "crime/court"),
        ("Nantwich football league match report", "sport"),
        ("Sponsored Nantwich casino partner content", "promotional/sponsored"),
        ("Nantwich celebrity restaurant review", "lifestyle/low utility"),
    ],
)
def test_editorial_rejection_reasons(title, reason):
    report = run_one([item(title)])
    rejected = report["feeds"][0]["rejected_titles"][0]
    assert reason in rejected["reasons"]


def test_non_local_missing_image_and_stale_are_grouped():
    report = run_one(
        [
            item(
                "National investment announcement",
                summary="A national business announcement.",
                media="",
                date="Mon, 01 Jun 2026 09:00:00 +0000",
            )
        ]
    )
    reasons = report["feeds"][0]["rejection_reasons"]
    assert reasons["non-local"] == 1
    assert reasons["missing image"] == 1
    assert reasons["stale"] == 1
    assert reasons["crime/court"] == 0


def test_priority_local_story_is_accepted():
    report = run_one([item("Nantwich council approves railway investment")])
    assert report["feeds"][0]["accepted_titles"] == [
        "Nantwich council approves railway investment"
    ]


def test_missing_source_url_is_rejected_and_reported():
    report = run_one([item("Nantwich council approves investment", link="")])
    assert report["feeds"][0]["items_with_source_urls"] == 0
    assert report["feeds"][0]["rejection_reasons"]["missing source URL"] == 1


def test_town_relevance_uses_feed_specific_terms():
    candidate = feed(terms=("runcorn", "widnes", "halton"))
    report = run_one([item("Northwich council investment plan")], candidate=candidate)
    assert "non-local" in report["feeds"][0]["rejected_titles"][0]["reasons"]


def test_exact_title_and_canonical_url_duplicates_are_rejected_across_feeds():
    first = feed("one", "One", "https://one.test/rss")
    second = feed("two", "Two", "https://two.test/rss")
    bodies = {
        first.url: shadow.FetchResult(
            200,
            rss(
                [
                    item(
                        "Nantwich council investment",
                        "https://publisher.test/story?ref=rss",
                    )
                ]
            ),
        ),
        second.url: shadow.FetchResult(
            200,
            rss(
                [
                    item(
                        "Nantwich council investment",
                        "https://publisher.test/story?utm_source=feed",
                    )
                ]
            ),
        ),
    }
    report = asyncio.run(
        shadow.evaluate(
            fetch=FakeFetch(bodies),
            as_of=AS_OF,
            candidate_feeds=(first, second),
            comparison_feeds=(),
        )
    )
    reasons = report["feeds"][1]["rejected_titles"][0]["reasons"]
    assert "duplicate exact title" in reasons
    assert "duplicate canonical URL" in reasons


def test_rejected_candidate_does_not_suppress_later_acceptable_version():
    first = feed("one", "One", "https://one.test/rss")
    second = feed("two", "Two", "https://two.test/rss")
    title = "Nantwich council approves railway investment"
    url = "https://publisher.test/investment"
    bodies = {
        first.url: shadow.FetchResult(
            200,
            rss(
                [
                    item(
                        title,
                        url,
                        summary="Nantwich court reports crime after an arrest.",
                    )
                ]
            ),
        ),
        second.url: shadow.FetchResult(200, rss([item(title, url)])),
    }
    report = asyncio.run(
        shadow.evaluate(
            fetch=FakeFetch(bodies),
            as_of=AS_OF,
            candidate_feeds=(first, second),
            comparison_feeds=(),
        )
    )
    assert report["feeds"][0]["accepted_count"] == 0
    assert report["feeds"][1]["accepted_titles"] == [title]


def test_accepted_candidate_still_suppresses_later_duplicate():
    first = feed("one", "One", "https://one.test/rss")
    second = feed("two", "Two", "https://two.test/rss")
    title = "Nantwich council approves railway investment"
    url = "https://publisher.test/investment"
    bodies = {
        first.url: shadow.FetchResult(200, rss([item(title, url)])),
        second.url: shadow.FetchResult(200, rss([item(title, url)])),
    }
    report = asyncio.run(
        shadow.evaluate(
            fetch=FakeFetch(bodies),
            as_of=AS_OF,
            candidate_feeds=(first, second),
            comparison_feeds=(),
        )
    )
    assert report["feeds"][0]["accepted_count"] == 1
    reasons = report["feeds"][1]["rejected_titles"][0]["reasons"]
    assert "duplicate exact title" in reasons
    assert "duplicate canonical URL" in reasons


def test_probable_similar_headline_is_reported():
    report = run_one(
        [
            item("Nantwich council approves major railway investment plan"),
            item(
                "Nantwich council backs major railway investment plan",
                link="https://example.test/other",
            ),
        ]
    )
    assert (
        "probable similar headline"
        in report["feeds"][0]["rejected_titles"][0]["reasons"]
        or "probable similar headline"
        in report["feeds"][0]["rejected_titles"][1]["reasons"]
    )


def test_comparison_feed_samples_participate_in_deduplication():
    baseline = feed("baseline", "Existing", "https://baseline.test/rss")
    candidate = feed()
    bodies = {
        baseline.url: shadow.FetchResult(
            200,
            rss(
                [
                    item(
                        "Nantwich housing investment",
                        "https://source.test/item?ref=rss",
                    )
                ]
            ),
        ),
        candidate.url: shadow.FetchResult(
            200, rss([item("Nantwich housing investment", "https://source.test/item")])
        ),
    }
    report = asyncio.run(
        shadow.evaluate(
            fetch=FakeFetch(bodies),
            as_of=AS_OF,
            candidate_feeds=(candidate,),
            comparison_feeds=(baseline,),
        )
    )
    assert report["configured_sample_feeds_succeeded"] == 1
    assert report["feeds"][0]["accepted_count"] == 0


def test_failed_feed_is_isolated_from_successful_feed():
    failed = feed("failed", "Failed", "https://failed.test/rss")
    good = feed("good", "Good", "https://good.test/rss")
    fetch = FakeFetch(
        {
            failed.url: OSError("offline"),
            good.url: shadow.FetchResult(
                200, rss([item("Nantwich council jobs investment")])
            ),
        }
    )
    report = asyncio.run(
        shadow.evaluate(
            fetch=fetch,
            as_of=AS_OF,
            candidate_feeds=(failed, good),
            comparison_feeds=(),
        )
    )
    assert report["feeds"][0]["feed_success"] is False
    assert report["feeds"][0]["error"] == "fetch or parse failure: OSError"
    assert report["feeds"][1]["accepted_count"] == 1


def test_http_non_200_has_safe_error():
    candidate = feed()
    fetch = FakeFetch({candidate.url: shadow.FetchResult(503, b"unavailable")})
    report = asyncio.run(
        shadow.evaluate(
            fetch=fetch,
            as_of=AS_OF,
            candidate_feeds=(candidate,),
            comparison_feeds=(),
        )
    )
    assert report["feeds"][0]["feed_success"] is False
    assert report["feeds"][0]["error"] == "HTTP 503"


@pytest.mark.parametrize(
    "content_type, body",
    [
        ("text/html; charset=UTF-8", b"<html><body>not found</body></html>"),
        ("application/octet-stream", b"<!DOCTYPE html><title>not found</title>"),
    ],
)
def test_http_200_html_not_found_page_is_rejected(content_type, body):
    candidate = feed()
    fetch = FakeFetch({candidate.url: shadow.FetchResult(200, body, content_type)})
    report = asyncio.run(
        shadow.evaluate(
            fetch=fetch,
            as_of=AS_OF,
            candidate_feeds=(candidate,),
            comparison_feeds=(),
        )
    )
    assert report["feeds"][0]["feed_success"] is False
    assert report["feeds"][0]["error"] == "response was HTML, not RSS/XML"


def test_malformed_xml_has_safe_error():
    candidate = feed()
    fetch = FakeFetch(
        {
            candidate.url: shadow.FetchResult(
                200, b"<rss><channel><item>", "application/rss+xml"
            )
        }
    )
    report = asyncio.run(
        shadow.evaluate(
            fetch=fetch,
            as_of=AS_OF,
            candidate_feeds=(candidate,),
            comparison_feeds=(),
        )
    )
    assert report["feeds"][0]["feed_success"] is False
    assert report["feeds"][0]["error"] == "response contained malformed XML"


def test_module_cli_help_succeeds_without_fetching():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "backend.scripts.evaluate_cheshire_rss_shadow",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Supported invocation" in result.stdout


def test_report_is_json_serialisable_and_contains_titles_not_bodies():
    secret_body = "synthetic publisher body must not appear"
    report = run_one(
        [item("Nantwich council investment", content=f"<p>{secret_body}</p>")]
    )
    rendered = json.dumps(report)
    assert "Nantwich council investment" in rendered
    assert secret_body not in rendered
    assert report["database_writes"] == 0


def test_no_database_write_contract_and_no_production_config_change():
    before = copy.deepcopy(RSS_FEEDS)
    report = run_one([item("Nantwich council investment")])
    assert RSS_FEEDS == before
    assert report["database_writes"] == 0
    assert not any(
        hasattr(shadow, name)
        for name in ("db", "database", "articles_collection", "mongo_client")
    )
