"""Offline integration coverage for the bounded category-RSS format gate."""
import asyncio
import copy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from test_rss_preview_quality import (
    server, FakeCollection, FakePerplexity, complete_rewrite, rss_candidate,
)

LIVE = 'https://www.theguardian.com/politics/live/2026/oct/02/zack-polanski-green-party-conference-speech-kemi-badenoch-andy-burnham-general-election-latest-news-updates'
REASON = 'source_format_review_guardian_politics_liveblog'


def candidate(url=LIVE, content=None, **values):
    item = rss_candidate()
    item.update(source_url=url, category='UK News', title='Government announces policy timetable',
                content=complete_rewrite() if content is None else content)
    item.update(values)
    return item


def run(monkeypatch, items, cap=None):
    articles, archived = FakeCollection(), FakeCollection()
    provider = FakePerplexity(complete_rewrite())

    async def feeds():
        return copy.deepcopy(items)

    async def local():
        return []

    async def no_cap(**kwargs):
        pass

    monkeypatch.setattr(server, 'db', SimpleNamespace(articles=articles, archived_articles=archived))
    monkeypatch.setattr(server, 'news_feed_service', SimpleNamespace(fetch_all_feeds=feeds, fetch_local_feeds_only=local))
    monkeypatch.setattr(server, 'perplexity_service', provider)
    monkeypatch.setattr(server, 'ai_budget_available', lambda _: True)
    monkeypatch.setattr(server, 'cap_visible_articles', no_cap)
    result = asyncio.run(server._import_hybrid_news_internal(server.HybridNewsRequest(
        cheshire_articles=0, uk_articles=3, business_articles=0, tech_articles=0,
        public_import_limit=cap, use_perplexity=True)))
    return result, articles.inserted, provider


@pytest.mark.parametrize('url', [LIVE, 'https://theguardian.com/politics/live/2026/sep/29/uk-politics-live'])
@pytest.mark.parametrize('content', ['A confirmed policy announcement.', complete_rewrite()])
def test_liveblog_review_before_generation(monkeypatch, url, content):
    result, rows, provider = run(monkeypatch, [candidate(url, content)])
    assert provider.rewrite_calls == 0
    assert len(rows) == 1
    row = rows[0]
    assert row['manual_review_hidden_from_public'] is True
    assert row['verification_status'] == 'needs_manual_review'
    assert row['rewrite_status'] == 'manual_review_required'
    assert REASON in row['manual_review_reason']
    assert row['archive_reason'] == 'needs_manual_review'
    assert row['category'] == 'UK News' and row['scope'] == 'uk'
    assert row['source_url'] == url
    assert 'editorial_metadata' in row
    assert result['public_imported'] == 0
    assert result['manual_review_imported'] == 1


@pytest.mark.parametrize('url', [
    'https://www.theguardian.com/politics/2026/oct/02/policy',
    'https://www.theguardian.com/money/2026/oct/02/uk-diesel-price-record-high-iran-war-oil',
    'https://www.theguardian.com/business/2026/oct/02/uk-is-not-facing-diesel-shortage-despite-fears-of-trump-export-ban-minister-says',
    'https://www.cheshire-live.co.uk/politics/live/2026/oct/02/news',
    'https://example.com/politics/live/2026/oct/02/news',
    'https://www.theguardian.com/politics/story?next=/politics/live/2026/oct/02/news',
    'https://www.theguardian.com/business/live/2026/oct/02/news',
    'https://[broken', '',
])
def test_other_sources_unchanged(monkeypatch, url):
    result, rows, provider = run(monkeypatch, [candidate(url, title='Workers live near new offices')])
    assert provider.rewrite_calls == 1
    assert result['public_imported'] == 1
    assert REASON not in rows[0].get('manual_review_reason', '')


def test_review_does_not_consume_public_slot_and_deduplicates(monkeypatch):
    live = candidate()
    ordinary = candidate('https://example.com/news', title='Published financial support figures', image='https://example.com/other.jpg')
    result, rows, provider = run(monkeypatch, [live, live, ordinary], cap=1)
    assert len(rows) == 2
    assert provider.rewrite_calls == 1
    assert result['public_imported'] == 1
    assert result['manual_review_imported'] == 1


@pytest.mark.parametrize('changes', [
    {'image': ''},
    {'publishedDate': (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()},
    {'title': 'Police arrest suspect'},
])
def test_prior_rejections_preserved(monkeypatch, changes):
    result, rows, provider = run(monkeypatch, [candidate(**changes)])
    assert not rows
    assert provider.rewrite_calls == 0


def test_business_live_reference_is_not_source_format(monkeypatch):
    result, rows, provider = run(monkeypatch, [candidate('https://example.com/news', content='Business live. ' + complete_rewrite())])
    assert provider.rewrite_calls == 1
    assert result['public_imported'] == 1
