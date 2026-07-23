#!/usr/bin/env python3
"""Read-only shadow evaluation for proposed Cheshire RSS sources.

The command writes one JSON document to stdout and a short human summary to
stderr. It has no database dependency and no mutation mode. The supported CLI
invocation is ``python3 -m backend.scripts.evaluate_cheshire_rss_shadow`` from
the repository root.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from html import unescape
from typing import Awaitable, Callable, Iterable, Sequence
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from xml.etree import ElementTree as ET

import httpx

from backend.app.news_feed_service import NewsFeedService, is_spam_or_product_article


CONTENT_NS = "http://purl.org/rss/1.0/modules/content/"
MEDIA_NS = "http://search.yahoo.com/mrss/"
TRACKING_PARAMETERS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "source",
}
PRIORITY_TERMS = (
    "planning",
    "council",
    "committee",
    "consultation",
    "housing",
    "homes",
    "property policy",
    "business",
    "investment",
    "jobs",
    "employment",
    "transport",
    "rail",
    "road",
    "nhs",
    "hospital",
    "school",
    "college",
    "university",
    "infrastructure",
    "environment",
    "regeneration",
)
REASON_PATTERNS = {
    "crime/court": (
        "arrest",
        "assault",
        "burglary",
        "charged",
        "court",
        "crime",
        "drug dealer",
        "jailed",
        "murder",
        "police appeal",
        "robbery",
        "sentenced",
        "shoplifting",
        "wanted man",
    ),
    "sport": (
        "football",
        "fixture",
        "league",
        "match report",
        "rugby",
        "scored",
        "sport",
        "transfer",
    ),
    "promotional/sponsored": (
        "ad feature",
        "advertorial",
        "affiliate",
        "casino",
        "free spins",
        "partner content",
        "promoted",
        "sponsored",
        "we earn a commission",
    ),
    "lifestyle/low utility": (
        "best places to live",
        "celebrity",
        "festival guide",
        "gaming",
        "horoscope",
        "recipe",
        "restaurant review",
        "showbiz",
        "things to do this weekend",
        "what's on",
        "whats on",
    ),
}
REJECTION_REASONS = (
    "crime/court",
    "sport",
    "promotional/sponsored",
    "lifestyle/low utility",
    "non-local",
    "missing image",
    "missing source URL",
    "stale",
    "duplicate exact title",
    "duplicate canonical URL",
    "probable similar headline",
)


@dataclass(frozen=True)
class CandidateFeed:
    key: str
    source: str
    url: str
    local_terms: tuple[str, ...]
    wordpress: bool = False


@dataclass(frozen=True)
class FetchResult:
    status_code: int
    content: bytes
    content_type: str = ""


@dataclass(frozen=True)
class ParsedItem:
    source: str
    title: str
    source_url: str
    canonical_url: str
    summary: str
    categories: tuple[str, ...]
    image: str | None
    published_at: datetime | None
    ldrs_attribution: bool
    press_release_signal: bool


CANDIDATE_FEEDS = (
    CandidateFeed(
        "nantwich_news",
        "Nantwich News",
        "https://thenantwichnews.co.uk/feed/",
        ("nantwich", "cheshire east"),
        wordpress=True,
    ),
    CandidateFeed(
        "northwich_guardian",
        "Northwich Guardian",
        "https://www.northwichguardian.co.uk/news/rss/",
        ("northwich", "winsford", "middlewich", "cheshire west"),
    ),
    CandidateFeed(
        "knutsford_guardian",
        "Knutsford Guardian",
        "https://www.knutsfordguardian.co.uk/news/rss/",
        ("knutsford", "wilmslow", "alderley edge", "handforth"),
    ),
    CandidateFeed(
        "runcorn_widnes_world",
        "Runcorn & Widnes World",
        "https://www.runcornandwidnesworld.co.uk/news/rss/",
        ("runcorn", "widnes", "halton"),
    ),
)


def canonicalize_url(value: str) -> str:
    """Return a comparison URL without fragments or tracking parameters."""
    try:
        parts = urlsplit((value or "").strip())
    except ValueError:
        return ""
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        return ""
    kept = [
        (key, val)
        for key, val in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in TRACKING_PARAMETERS and not key.lower().startswith("utm_")
    ]
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    if path != "/":
        path = path.rstrip("/")
    netloc = parts.hostname.lower()
    try:
        port = parts.port
    except ValueError:
        return ""
    if port and not (
        (parts.scheme.lower() == "https" and port == 443)
        or (parts.scheme.lower() == "http" and port == 80)
    ):
        netloc = f"{netloc}:{port}"
    return urlunsplit((parts.scheme.lower(), netloc, path, urlencode(kept), ""))


def normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", unescape(value or "").lower()).strip()


def _child_text(item: ET.Element, name: str) -> str:
    child = item.find(name)
    return (child.text or "").strip() if child is not None and child.text else ""


def _first_html_image(value: str) -> str | None:
    match = re.search(r"<img[^>]+src=[\"']([^\"']+)[\"']", value or "", re.I)
    return unescape(match.group(1)) if match else None


def parse_feed(
    content: bytes,
    feed: CandidateFeed,
    parser: NewsFeedService | None = None,
) -> list[ParsedItem]:
    """Parse candidate RSS using the production parser's safe primitives."""
    parser = parser or NewsFeedService()
    root = ET.fromstring(content)
    namespaces = {"media": MEDIA_NS, "content": CONTENT_NS}
    parsed: list[ParsedItem] = []
    for item in root.findall(".//item"):
        title = parser._clean_html(_child_text(item, "title"))
        source_url = _child_text(item, "link")
        if not title:
            continue
        raw_summary = _child_text(item, "description")
        raw_content = _child_text(item, f"{{{CONTENT_NS}}}encoded")
        summary = parser._clean_html(raw_summary)
        categories = tuple(
            parser._clean_html(category.text or "").lower()
            for category in item.findall("category")
            if category.text
        )
        image = parser._extract_image_from_item(item, namespaces)
        if not image and feed.wordpress:
            image = _first_html_image(raw_content) or _first_html_image(raw_summary)
        raw_date = _child_text(item, "pubDate")
        published_at = parser._parse_date(raw_date) if raw_date else None
        attribution_text = f"{raw_summary} {raw_content}".lower()
        parsed.append(
            ParsedItem(
                source=feed.source,
                title=title,
                source_url=source_url,
                canonical_url=canonicalize_url(source_url),
                summary=summary,
                categories=categories,
                image=image,
                published_at=published_at,
                ldrs_attribution=(
                    "local democracy reporter" in attribution_text
                    or "local democracy reporting service" in attribution_text
                ),
                press_release_signal=(
                    "press release" in attribution_text
                    or "issued on behalf of" in attribution_text
                ),
            )
        )
    return parsed


def validate_feed_response(response: FetchResult) -> str | None:
    """Return a safe diagnostic when an HTTP response is not parseable XML."""
    if response.status_code != 200:
        return f"HTTP {response.status_code}"
    content_type = response.content_type.lower()
    body_start = response.content.lstrip()[:256].lower()
    if "text/html" in content_type or body_start.startswith(
        (b"<!doctype html", b"<html")
    ):
        return "response was HTML, not RSS/XML"
    try:
        ET.fromstring(response.content)
    except ET.ParseError:
        return "response contained malformed XML"
    return None


def _contains_any(text: str, terms: Iterable[str]) -> bool:
    return any(
        re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text) is not None
        for term in terms
    )


def _probable_similar(title: str, titles: Sequence[str]) -> bool:
    if len(title) < 20:
        return False
    return any(SequenceMatcher(None, title, other).ratio() >= 0.84 for other in titles)


def classify_item(
    item: ParsedItem,
    feed: CandidateFeed,
    *,
    as_of: datetime,
    seen_titles: set[str],
    seen_urls: set[str],
    comparison_titles: Sequence[str],
) -> tuple[list[str], bool]:
    text = " ".join((item.title, item.summary, " ".join(item.categories))).lower()
    reasons: list[str] = []
    for reason, patterns in REASON_PATTERNS.items():
        if _contains_any(text, patterns):
            reasons.append(reason)
    if is_spam_or_product_article(item.title, item.summary):
        reasons.append("promotional/sponsored")
    if any(
        marker in text
        for marker in ("advertisement features", "promoted content", "partner content")
    ):
        if "promotional/sponsored" not in reasons:
            reasons.append("promotional/sponsored")
    local = _contains_any(text, feed.local_terms)
    if not local:
        reasons.append("non-local")
    if not item.image:
        reasons.append("missing image")
    if not item.canonical_url:
        reasons.append("missing source URL")
    if item.published_at is None or item.published_at < as_of - timedelta(days=14):
        reasons.append("stale")
    normalized = normalize_title(item.title)
    if normalized in seen_titles:
        reasons.append("duplicate exact title")
    if item.canonical_url and item.canonical_url in seen_urls:
        reasons.append("duplicate canonical URL")
    if normalized not in seen_titles and _probable_similar(
        normalized, comparison_titles
    ):
        reasons.append("probable similar headline")
    has_priority = _contains_any(text, PRIORITY_TERMS)
    if not has_priority and not reasons:
        reasons.append("lifestyle/low utility")
    return list(dict.fromkeys(reasons)), local


async def default_fetch(url: str) -> FetchResult:
    async with httpx.AsyncClient(
        follow_redirects=True,
        headers={"User-Agent": "CheshireToday-ReadOnly-Feed-Evaluation/1.0"},
        timeout=20.0,
    ) as client:
        response = await client.get(url)
    return FetchResult(
        status_code=response.status_code,
        content=response.content,
        content_type=response.headers.get("content-type", ""),
    )


def configured_sample_feeds() -> tuple[CandidateFeed, ...]:
    """Read, but never alter, the current production local-feed registry."""
    service = NewsFeedService()
    samples: list[CandidateFeed] = []
    for key, config in service.feeds.items():
        if not config.get("is_local"):
            continue
        samples.append(
            CandidateFeed(
                key=key,
                source=config["source"],
                url=config["url"],
                local_terms=("cheshire",),
            )
        )
    return tuple(samples)


async def evaluate(
    *,
    fetch: Callable[[str], Awaitable[FetchResult]],
    as_of: datetime,
    candidate_feeds: Sequence[CandidateFeed] = CANDIDATE_FEEDS,
    comparison_feeds: Sequence[CandidateFeed] | None = None,
) -> dict:
    if as_of.tzinfo is None or as_of.utcoffset() != timedelta(0):
        raise ValueError("as_of must be timezone-aware UTC")
    parser = NewsFeedService()
    comparison_feeds = (
        configured_sample_feeds() if comparison_feeds is None else comparison_feeds
    )
    baseline_titles: set[str] = set()
    baseline_urls: set[str] = set()
    baseline_success = 0
    for feed in comparison_feeds:
        try:
            response = await fetch(feed.url)
            if validate_feed_response(response) is not None:
                continue
            items = parse_feed(response.content, feed, parser)
            baseline_success += 1
            baseline_titles.update(normalize_title(item.title) for item in items)
            baseline_urls.update(
                item.canonical_url for item in items if item.canonical_url
            )
        except (ET.ParseError, OSError, ValueError, httpx.HTTPError):
            continue

    seen_titles = set(baseline_titles)
    seen_urls = set(baseline_urls)
    reports: list[dict] = []
    for feed in candidate_feeds:
        report = {
            "key": feed.key,
            "source": feed.source,
            "url": feed.url,
            "feed_success": False,
            "error": None,
            "http_status": None,
            "content_type": "",
            "items_fetched": 0,
            "items_with_usable_images": 0,
            "items_with_source_urls": 0,
            "fresh_items": 0,
            "newest_publication_date": None,
            "oldest_publication_date": None,
            "locally_relevant_items": 0,
            "accepted_count": 0,
            "rejected_count": 0,
            "rejection_reasons": {reason: 0 for reason in REJECTION_REASONS},
            "accepted_titles": [],
            "rejected_titles": [],
            "ldrs_attributed_count": 0,
            "press_release_signal_count": 0,
        }
        try:
            response = await fetch(feed.url)
            report["http_status"] = response.status_code
            report["content_type"] = response.content_type
            response_error = validate_feed_response(response)
            if response_error is not None:
                report["error"] = response_error
                reports.append(report)
                continue
            items = parse_feed(response.content, feed, parser)
            report["feed_success"] = True
            report["items_fetched"] = len(items)
            report["items_with_usable_images"] = sum(bool(i.image) for i in items)
            report["items_with_source_urls"] = sum(bool(i.canonical_url) for i in items)
            report["fresh_items"] = sum(
                i.published_at is not None
                and i.published_at >= as_of - timedelta(days=14)
                for i in items
            )
            publication_dates = sorted(
                i.published_at for i in items if i.published_at is not None
            )
            if publication_dates:
                report["oldest_publication_date"] = publication_dates[0].isoformat()
                report["newest_publication_date"] = publication_dates[-1].isoformat()
            report["ldrs_attributed_count"] = sum(i.ldrs_attribution for i in items)
            report["press_release_signal_count"] = sum(
                i.press_release_signal for i in items
            )
            for item in items:
                comparison_titles = tuple(seen_titles)
                reasons, local = classify_item(
                    item,
                    feed,
                    as_of=as_of,
                    seen_titles=seen_titles,
                    seen_urls=seen_urls,
                    comparison_titles=comparison_titles,
                )
                report["locally_relevant_items"] += int(local)
                normalized = normalize_title(item.title)
                if reasons:
                    report["rejected_titles"].append(
                        {"title": item.title, "reasons": reasons}
                    )
                    for reason in reasons:
                        report["rejection_reasons"][reason] = (
                            report["rejection_reasons"].get(reason, 0) + 1
                        )
                else:
                    report["accepted_titles"].append(item.title)
                    seen_titles.add(normalized)
                    if item.canonical_url:
                        seen_urls.add(item.canonical_url)
            report["accepted_count"] = len(report["accepted_titles"])
            report["rejected_count"] = len(report["rejected_titles"])
        except (ET.ParseError, OSError, ValueError, httpx.HTTPError) as exc:
            report["feed_success"] = False
            report["error"] = f"fetch or parse failure: {type(exc).__name__}"
        reports.append(report)

    return {
        "mode": "read_only_shadow_evaluation",
        "as_of": as_of.isoformat(),
        "database_writes": 0,
        "configured_sample_feeds_checked": len(comparison_feeds),
        "configured_sample_feeds_succeeded": baseline_success,
        "feeds": reports,
        "totals": {
            "feeds": len(reports),
            "successful_feeds": sum(r["feed_success"] for r in reports),
            "items": sum(r["items_fetched"] for r in reports),
            "accepted": sum(r["accepted_count"] for r in reports),
            "rejected": sum(r["rejected_count"] for r in reports),
        },
    }


def _parse_as_of(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise argparse.ArgumentTypeError("--as-of must be timezone-aware UTC")
    return parsed


def _summary(report: dict) -> str:
    totals = report["totals"]
    lines = [
        "Cheshire RSS shadow evaluation (read-only)",
        f"Feeds: {totals['successful_feeds']}/{totals['feeds']} successful",
        f"Items: {totals['items']} | accepted: {totals['accepted']} | rejected: {totals['rejected']}",
    ]
    for feed in report["feeds"]:
        lines.append(
            f"- {feed['source']}: {feed['accepted_count']} accepted, "
            f"{feed['rejected_count']} rejected"
        )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "Supported invocation: python3 -m "
            "backend.scripts.evaluate_cheshire_rss_shadow"
        ),
    )
    parser.add_argument(
        "--as-of",
        help="UTC ISO-8601 evaluation time (defaults to current UTC time)",
    )
    args = parser.parse_args(argv)
    try:
        as_of = _parse_as_of(args.as_of)
        report = asyncio.run(evaluate(fetch=default_fetch, as_of=as_of))
    except (OSError, ValueError):
        print("Shadow evaluation failed safely.", file=sys.stderr)
        return 1
    print(_summary(report), file=sys.stderr)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["totals"]["successful_feeds"] == len(CANDIDATE_FEEDS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
