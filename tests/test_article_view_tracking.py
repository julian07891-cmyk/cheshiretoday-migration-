import asyncio
import os
from datetime import datetime, timezone

import pytest
from bson import ObjectId
from fastapi import HTTPException
from starlette.requests import Request


os.environ["MONGO_URL"] = "mongodb://localhost:27017"
os.environ["DB_NAME"] = "cheshire_test"
os.environ["LOCAL_DEV_NO_DB"] = "1"
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")


class ArticlesSpy:
    def __init__(self, article=None, find_error=None):
        self.article = article
        self.find_error = find_error
        self.find_calls = []
        self.update_calls = []

    async def find_one(self, query):
        self.find_calls.append(query)
        if self.find_error:
            raise self.find_error
        if not self.article:
            return None
        if query.get("_id") == self.article.get("_id"):
            return dict(self.article)
        if query.get("id") == self.article.get("id"):
            return dict(self.article)
        return None

    async def update_one(self, *args):
        self.update_calls.append(args)


class ArticleViewsSpy:
    def __init__(self, existing=None):
        self.existing = existing
        self.find_calls = []
        self.insert_calls = []

    async def find_one(self, query):
        self.find_calls.append(query)
        return self.existing

    async def insert_one(self, document):
        self.insert_calls.append(document)


class DatabaseSpy:
    def __init__(self, article=None, existing_view=None, find_error=None):
        self.articles = ArticlesSpy(article, find_error)
        self.article_views = ArticleViewsSpy(existing_view)


def request():
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/articles/example/view",
            "headers": [],
            "client": ("203.0.113.10", 1234),
        }
    )


def run_tracking(monkeypatch, database, article_id):
    from backend import server

    monkeypatch.setattr(server, "db", database)
    return asyncio.run(server.track_article_view(article_id, request()))


def test_public_article_records_view_and_increments_resolved_article(monkeypatch):
    mongo_id = ObjectId()
    database = DatabaseSpy({"_id": mongo_id, "id": "legacy-id", "archived": False})

    result = run_tracking(monkeypatch, database, str(mongo_id))

    assert result == {"success": True, "counted": True}
    assert database.article_views.insert_calls[0]["article_id"] == str(mongo_id)
    assert isinstance(database.article_views.insert_calls[0]["viewed_at"], datetime)
    assert database.article_views.insert_calls[0]["viewed_at"].tzinfo == timezone.utc
    assert database.articles.update_calls == [
        (({"_id": mongo_id}, {"$inc": {"view_count": 1}}))
    ]


@pytest.mark.parametrize(
    "article",
    [
        None,
        {"_id": ObjectId(), "id": "archived", "archived": True},
        {
            "_id": ObjectId(),
            "id": "manual-review",
            "manual_review_hidden_from_public": True,
        },
    ],
    ids=["nonexistent", "archived", "manual-review"],
)
def test_ineligible_article_is_rejected_before_any_view_write(monkeypatch, article):
    database = DatabaseSpy(article)
    article_id = str(article["_id"]) if article else str(ObjectId())

    with pytest.raises(HTTPException) as exc_info:
        run_tracking(monkeypatch, database, article_id)

    assert exc_info.value.status_code == 404
    assert database.article_views.find_calls == []
    assert database.article_views.insert_calls == []
    assert database.articles.update_calls == []


def test_legacy_id_is_canonicalised_to_resolved_mongo_id(monkeypatch):
    mongo_id = ObjectId()
    database = DatabaseSpy({"_id": mongo_id, "id": "legacy-id"})

    result = run_tracking(monkeypatch, database, "legacy-id")

    assert result["counted"] is True
    assert database.article_views.find_calls[0]["article_id"] == str(mongo_id)
    assert database.article_views.insert_calls[0]["article_id"] == str(mongo_id)
    assert database.articles.update_calls[0][0] == {"_id": mongo_id}


def test_valid_legacy_id_records_and_increments_resolved_article(monkeypatch):
    mongo_id = ObjectId()
    database = DatabaseSpy({"_id": mongo_id, "id": "legacy-string-id"})

    result = run_tracking(monkeypatch, database, "legacy-string-id")

    assert result == {"success": True, "counted": True}
    assert database.article_views.insert_calls[0]["article_id"] == str(mongo_id)
    assert database.articles.update_calls == [
        ({"_id": mongo_id}, {"$inc": {"view_count": 1}})
    ]


def test_duplicate_view_is_suppressed_without_insert_or_increment(monkeypatch):
    mongo_id = ObjectId()
    database = DatabaseSpy(
        {"_id": mongo_id, "id": "legacy-id"},
        existing_view={"article_id": str(mongo_id)},
    )

    result = run_tracking(monkeypatch, database, str(mongo_id))

    assert result["success"] is True
    assert result["counted"] is False
    assert database.article_views.insert_calls == []
    assert database.articles.update_calls == []


def test_unexpected_resolution_failure_creates_no_partial_analytics_write(monkeypatch):
    database = DatabaseSpy(find_error=RuntimeError("database unavailable"))

    result = run_tracking(monkeypatch, database, "legacy-id")

    assert result["success"] is False
    assert database.article_views.find_calls == []
    assert database.article_views.insert_calls == []
    assert database.articles.update_calls == []
