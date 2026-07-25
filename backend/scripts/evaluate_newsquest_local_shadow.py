#!/usr/bin/env python3
"""Read-only shadow evaluation for proposed Cheshire Newsquest RSS feeds.

Supported invocation::

    python3 -m backend.scripts.evaluate_newsquest_local_shadow

The evaluator fetches public RSS/API inputs and emits a JSON report. It has no
database dependency, mutation mode, scheduler hook, or production-import hook.
An optional existing-article snapshot may contain only ``title`` and
``source_url`` fields.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable, Sequence

import httpx

from backend.app.local_rss_editorial_policy import (
    is_crime_like,
    is_obituary_like,
    is_useful_local_article,
    local_manual_review_editorial_reason,
)
from backend.scripts.evaluate_cheshire_rss_shadow import (
    CandidateFeed,
    FetchResult,
    _probable_similar,
    canonicalize_url,
    classify_item,
    configured_sample_feeds,
    default_fetch,
    normalize_title,
    parse_feed,
    validate_feed_response,
)


NEWSQUEST_FEEDS = (
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

HARD_REASONS = {
    "crime/court",
    "sport",
    "promotional/sponsored",
    "non-local",
    "missing image",
    "missing source URL",
    "stale",
    "duplicate exact title",
    "duplicate canonical URL",
    "probable similar headline",
}
def _text(item) -> str:
    return " ".join((item.title, item.summary, " ".join(item.categories))).lower()


def _policy_article(item) -> dict:
    return {
        "title": item.title,
        "summary": item.summary,
        "content": "",
        "category": " ".join(item.categories),
        "source_url": item.source_url,
    }


def _load_existing_snapshot(path: Path | None) -> tuple[set[str], set[str], int]:
    if path is None:
        return set(), set(), 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("existing snapshot must be a JSON array")
    titles: set[str] = set()
    urls: set[str] = set()
    for record in payload:
        if not isinstance(record, dict):
            raise ValueError("existing snapshot records must be objects")
        if set(record) - {"title", "source_url"}:
            raise ValueError("existing snapshot may contain only title and source_url")
        title = normalize_title(record.get("title", ""))
        url = canonicalize_url(record.get("source_url", ""))
        if title:
            titles.add(title)
        if url:
            urls.add(url)
    return titles, urls, len(payload)


async def _sample_feed_sets(
    fetch: Callable[[str], Awaitable[FetchResult]],
    feeds: Sequence[CandidateFeed],
) -> tuple[set[str], set[str], int]:
    titles: set[str] = set()
    urls: set[str] = set()
    succeeded = 0
    for feed in feeds:
        try:
            response = await fetch(feed.url)
            if validate_feed_response(response) is not None:
                continue
            items = parse_feed(response.content, feed)
            succeeded += 1
            titles.update(normalize_title(item.title) for item in items)
            urls.update(item.canonical_url for item in items if item.canonical_url)
        except (OSError, ValueError, httpx.HTTPError):
            continue
    return titles, urls, succeeded


async def evaluate(
    *,
    fetch: Callable[[str], Awaitable[FetchResult]],
    as_of: datetime,
    feeds: Sequence[CandidateFeed] = NEWSQUEST_FEEDS,
    comparison_feeds: Sequence[CandidateFeed] | None = None,
    existing_titles: set[str] | None = None,
    existing_urls: set[str] | None = None,
) -> dict:
    """Evaluate feeds deterministically without writing or publishing anything."""
    existing_titles = set(existing_titles or ())
    existing_urls = set(existing_urls or ())
    comparison_feeds = (
        configured_sample_feeds() if comparison_feeds is None else comparison_feeds
    )
    configured_titles, configured_urls, configured_succeeded = await _sample_feed_sets(
        fetch, comparison_feeds
    )
    accepted_titles: set[str] = set()
    accepted_urls: set[str] = set()
    accepted_title_sources: dict[str, str] = {}
    reports = []
    parsed_by_key = {}
    errors_by_key = {}
    for feed in feeds:
        try:
            response = await fetch(feed.url)
            error = validate_feed_response(response)
            if error:
                errors_by_key[feed.key] = error
                continue
            parsed_by_key[feed.key] = parse_feed(response.content, feed)
        except (OSError, ValueError, httpx.HTTPError) as exc:
            errors_by_key[feed.key] = (
                f"fetch or parse failure: {type(exc).__name__}"
            )
    title_sources: dict[str, set[str]] = {}
    for feed in feeds:
        for item in parsed_by_key.get(feed.key, ()):
            title_sources.setdefault(normalize_title(item.title), set()).add(feed.key)

    for feed in feeds:
        report = {
            "key": feed.key,
            "source": feed.source,
            "url": feed.url,
            "feed_success": False,
            "error": None,
            "raw_articles": 0,
            "usable_images": 0,
            "town_relevant": 0,
            "auto_publication_path": [],
            "manual_review": [],
            "hard_rejected": [],
            "duplicate_counts": {
                "existing_cheshire_today": 0,
                "configured_local_feed": 0,
                "evaluated_newsquest_feed": 0,
                "probable_syndicated_or_county_wide": 0,
            },
            "outcome_counts": {
                "auto_publication_path": 0,
                "manual_review": 0,
                "hard_rejected": 0,
            },
            "reason_counts": {},
        }
        try:
            if feed.key in errors_by_key:
                report["error"] = errors_by_key[feed.key]
                reports.append(report)
                continue
            items = parsed_by_key[feed.key]
            report["feed_success"] = True
            report["raw_articles"] = len(items)
            report["usable_images"] = sum(bool(item.image) for item in items)
            for item in items:
                normalized = normalize_title(item.title)
                local_seen_titles = configured_titles | accepted_titles
                local_seen_urls = configured_urls | accepted_urls
                reasons, local = classify_item(
                    item,
                    feed,
                    as_of=as_of,
                    seen_titles=local_seen_titles,
                    seen_urls=local_seen_urls,
                    comparison_titles=tuple(local_seen_titles),
                )
                report["town_relevant"] += int(local)

                duplicate_reasons = []
                blocking_duplicate = False
                if normalized in existing_titles or item.canonical_url in existing_urls:
                    duplicate_reasons.append("existing Cheshire Today article")
                    report["duplicate_counts"]["existing_cheshire_today"] += 1
                    blocking_duplicate = True
                if (
                    normalized in configured_titles
                    or item.canonical_url in configured_urls
                ):
                    duplicate_reasons.append("configured local feed")
                    report["duplicate_counts"]["configured_local_feed"] += 1
                    blocking_duplicate = True
                if normalized in accepted_titles or item.canonical_url in accepted_urls:
                    duplicate_reasons.append("evaluated Newsquest feed")
                    blocking_duplicate = True
                if len(title_sources.get(normalized, ())) > 1:
                    if "evaluated Newsquest feed" not in duplicate_reasons:
                        duplicate_reasons.append("evaluated Newsquest feed")
                    report["duplicate_counts"]["evaluated_newsquest_feed"] += 1
                if (
                    normalized not in accepted_titles
                    and _probable_similar(normalized, tuple(accepted_titles))
                ):
                    duplicate_reasons.append("probable syndicated/county-wide story")
                    report["duplicate_counts"][
                        "probable_syndicated_or_county_wide"
                    ] += 1

                hard_reasons = [reason for reason in reasons if reason in HARD_REASONS]
                policy_article = _policy_article(item)
                if is_crime_like(policy_article):
                    hard_reasons.append("crime/court")
                if is_obituary_like(policy_article):
                    hard_reasons.append("obituary")
                if blocking_duplicate and not any(
                    reason.startswith("duplicate") or reason == "probable similar headline"
                    for reason in hard_reasons
                ):
                    hard_reasons.append("duplicate")
                if hard_reasons:
                    all_reasons = list(dict.fromkeys(hard_reasons + duplicate_reasons))
                    report["hard_rejected"].append(
                        {"title": item.title, "reasons": all_reasons}
                    )
                    for reason in all_reasons:
                        report["reason_counts"][reason] = (
                            report["reason_counts"].get(reason, 0) + 1
                        )
                    continue

                if not is_useful_local_article(policy_article):
                    reason = local_manual_review_editorial_reason(
                        policy_article
                    ).removeprefix("Local RSS article needs manual review: ")
                    report["manual_review"].append(
                        {"title": item.title, "reason": reason}
                    )
                else:
                    report["auto_publication_path"].append(
                        {
                            "title": item.title,
                            "reason": "civic/economic candidate",
                        }
                    )

                # Only usable candidates suppress later evaluated-feed versions.
                accepted_titles.add(normalized)
                accepted_title_sources[normalized] = feed.source
                if item.canonical_url:
                    accepted_urls.add(item.canonical_url)

            for outcome in report["outcome_counts"]:
                report["outcome_counts"][outcome] = len(report[outcome])
        except (OSError, ValueError, httpx.HTTPError) as exc:
            report["error"] = f"fetch or parse failure: {type(exc).__name__}"
        reports.append(report)

    totals = {
        "feeds": len(reports),
        "successful_feeds": sum(report["feed_success"] for report in reports),
        "raw_articles": sum(report["raw_articles"] for report in reports),
        "usable_images": sum(report["usable_images"] for report in reports),
        "town_relevant": sum(report["town_relevant"] for report in reports),
        "auto_publication_path": sum(
            report["outcome_counts"]["auto_publication_path"] for report in reports
        ),
        "manual_review": sum(
            report["outcome_counts"]["manual_review"] for report in reports
        ),
        "hard_rejected": sum(
            report["outcome_counts"]["hard_rejected"] for report in reports
        ),
    }
    totals["unique_usable_yield"] = (
        totals["auto_publication_path"] + totals["manual_review"]
    )
    return {
        "mode": "read_only_newsquest_local_shadow",
        "as_of": as_of.isoformat(),
        "database_reads": 0,
        "database_writes": 0,
        "publication_writes": 0,
        "manual_review_writes": 0,
        "configured_feeds_checked": len(comparison_feeds),
        "configured_feeds_succeeded": configured_succeeded,
        "existing_snapshot_records": 0,
        "feeds": reports,
        "totals": totals,
    }


def _summary(report: dict) -> str:
    totals = report["totals"]
    lines = [
        "Newsquest Local RSS shadow evaluation (read-only)",
        (
            f"Raw: {totals['raw_articles']} | unique usable: "
            f"{totals['unique_usable_yield']} | hard rejected: "
            f"{totals['hard_rejected']}"
        ),
    ]
    for feed in report["feeds"]:
        outcomes = feed["outcome_counts"]
        lines.append(
            f"- {feed['source']}: raw {feed['raw_articles']}, "
            f"auto-path {outcomes['auto_publication_path']}, "
            f"Manual Review {outcomes['manual_review']}, "
            f"hard reject {outcomes['hard_rejected']}"
        )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--as-of",
        help="UTC ISO-8601 evaluation time; defaults to current UTC time",
    )
    parser.add_argument(
        "--existing-articles-json",
        type=Path,
        help="Optional read-only JSON array containing only title/source_url fields",
    )
    args = parser.parse_args(argv)
    try:
        as_of = (
            datetime.fromisoformat(args.as_of.replace("Z", "+00:00"))
            if args.as_of
            else datetime.now(timezone.utc)
        )
        if as_of.tzinfo is None:
            raise ValueError("as-of must be timezone aware")
        existing_titles, existing_urls, existing_count = _load_existing_snapshot(
            args.existing_articles_json
        )
        report = asyncio.run(
            evaluate(
                fetch=default_fetch,
                as_of=as_of,
                existing_titles=existing_titles,
                existing_urls=existing_urls,
            )
        )
        report["existing_snapshot_records"] = existing_count
    except (OSError, ValueError, json.JSONDecodeError):
        print("Newsquest shadow evaluation failed safely.", file=sys.stderr)
        return 1
    print(_summary(report), file=sys.stderr)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["totals"]["successful_feeds"] == len(NEWSQUEST_FEEDS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
