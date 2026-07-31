import asyncio
import os
from datetime import datetime, timedelta, timezone

import pytest
from bson import ObjectId


os.environ["MONGO_URL"] = "mongodb://localhost:27017"
os.environ["DB_NAME"] = "cheshire_test"
os.environ["LOCAL_DEV_NO_DB"] = "1"
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")


NOW = datetime(2026, 7, 30, 15, 45, tzinfo=timezone.utc)


class FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return NOW if tz else NOW.replace(tzinfo=None)


class AggregateResult:
    def __init__(self, records):
        self.records = records
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.records):
            raise StopAsyncIteration
        record = self.records[self.index]
        self.index += 1
        return record


class ArticleViewsSpy:
    def __init__(self, records):
        self.records = records
        self.pipeline = None

    def aggregate(self, pipeline):
        self.pipeline = pipeline
        return AggregateResult(self.records)


class ArticlesSpy:
    def __init__(self, records):
        self.records = records
        self.find_calls = []

    async def find_one(self, query):
        self.find_calls.append(query)
        for article in self.records:
            if "_id" in query and query["_id"] == article.get("_id"):
                return dict(article)
            if "id" in query and query["id"] == article.get("id"):
                return dict(article)
        return None

    def find(self, *args, **kwargs):
        raise AssertionError("Most Read must not query lifetime article view_count")


class DatabaseSpy:
    def __init__(self, views, articles):
        self.article_views = ArticleViewsSpy(views)
        self.articles = ArticlesSpy(articles)


def run_most_read(monkeypatch, period="today", limit=5, views=None, articles=None):
    from backend import server

    database = DatabaseSpy(views or [], articles or [])
    monkeypatch.setattr(server, "db", database)
    monkeypatch.setattr(server, "datetime", FixedDateTime)
    result = asyncio.run(server.get_most_read_articles(period=period, limit=limit))
    return result, database


@pytest.mark.parametrize(
    ("period", "expected_start"),
    [
        ("today", NOW.replace(hour=0, minute=0, second=0, microsecond=0)),
        ("week", NOW - timedelta(days=7)),
        ("month", NOW - timedelta(days=30)),
    ],
)
def test_period_uses_only_events_inside_requested_window(
    monkeypatch, period, expected_start
):
    result, database = run_most_read(monkeypatch, period=period)

    assert result == {"success": True, "period": period, "articles": []}
    assert database.article_views.pipeline[0] == {
        "$match": {"viewed_at": {"$gte": expected_start}}
    }


def test_no_period_views_returns_empty_without_lifetime_fallback(monkeypatch):
    result, database = run_most_read(monkeypatch, period="week")

    assert result["articles"] == []
    assert database.articles.find_calls == []


def test_hidden_articles_do_not_consume_limit_and_visible_articles_remain_ranked(
    monkeypatch,
):
    archived_id = ObjectId()
    manual_id = ObjectId()
    first_id = ObjectId()
    second_id = ObjectId()
    views = [
        {"_id": str(archived_id), "views": 20},
        {"_id": str(first_id), "views": 15},
        {"_id": str(manual_id), "views": 12},
        {"_id": str(second_id), "views": 8},
    ]
    articles = [
        {"_id": archived_id, "title": "Archived", "archived": True},
        {"_id": first_id, "title": "First", "category": "Local News"},
        {
            "_id": manual_id,
            "title": "Manual",
            "manual_review_hidden_from_public": True,
        },
        {"_id": second_id, "title": "Second", "category": "Business"},
    ]

    result, _ = run_most_read(
        monkeypatch, period="month", limit=2, views=views, articles=articles
    )

    assert [(item["title"], item["views"]) for item in result["articles"]] == [
        ("First", 15),
        ("Second", 8),
    ]


def test_invalid_period_preserves_existing_today_window_and_response(monkeypatch):
    result, database = run_most_read(monkeypatch, period="invalid")

    assert result == {"success": True, "period": "invalid", "articles": []}
    assert database.article_views.pipeline[0] == {
        "$match": {
            "viewed_at": {
                "$gte": NOW.replace(hour=0, minute=0, second=0, microsecond=0)
            }
        }
    }
