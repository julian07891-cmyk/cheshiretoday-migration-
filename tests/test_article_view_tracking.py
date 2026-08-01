import asyncio
import json
import os
from datetime import datetime, timezone

import pytest
from bson import ObjectId
from fastapi import HTTPException
from fastapi.testclient import TestClient
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


def request(body=b""):
    sent = False

    async def receive():
        nonlocal sent
        if sent:
            return {"type": "http.request", "body": b"", "more_body": False}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/articles/example/view",
            "headers": [(b"content-type", b"application/json")] if body else [],
            "client": ("203.0.113.10", 1234),
        },
        receive,
    )


def run_tracking(monkeypatch, database, article_id, tracking_input=None):
    from backend import server

    monkeypatch.setattr(server, "db", database)
    body = b""
    if tracking_input is not None:
        body = json.dumps(tracking_input.model_dump()).encode("utf-8")
    return asyncio.run(server.track_article_view(article_id, request(body)))


def test_public_article_records_view_and_increments_resolved_article(monkeypatch):
    mongo_id = ObjectId()
    database = DatabaseSpy({"_id": mongo_id, "id": "legacy-id", "archived": False})

    result = run_tracking(monkeypatch, database, str(mongo_id))

    assert result == {"success": True, "counted": True}
    assert database.article_views.insert_calls[0]["article_id"] == str(mongo_id)
    assert database.article_views.insert_calls[0]["source"] == "unknown"
    assert database.article_views.insert_calls[0]["medium"] == "unknown"
    assert database.article_views.insert_calls[0]["campaign"] == "unknown"
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


def test_valid_facebook_attribution_stores_only_server_owned_enums(monkeypatch):
    from backend.app.article_view_attribution import ArticleViewTrackingInput

    mongo_id = ObjectId()
    database = DatabaseSpy({"_id": mongo_id, "id": "legacy-id"})
    tracking_input = ArticleViewTrackingInput.model_validate(
        {
            "attribution": {
                "utm_source": "facebook",
                "utm_medium": "social",
                "utm_campaign": "social_publishing",
                "referrer_hostname": "www.facebook.com",
            }
        }
    )

    result = run_tracking(monkeypatch, database, str(mongo_id), tracking_input)

    assert result["counted"] is True
    stored = database.article_views.insert_calls[0]
    assert stored["source"] == "facebook"
    assert stored["medium"] == "social"
    assert stored["campaign"] == "social_publishing"
    assert "referrer_hostname" not in stored
    assert "utm_source" not in stored
    assert "url" not in stored
    assert "query" not in stored


@pytest.mark.parametrize(
    "payload",
    [
        {"utm_source": "private-campaign", "utm_medium": "social", "utm_campaign": "secret"},
        {"utm_source": "facebook", "utm_medium": "email", "utm_campaign": "social_publishing"},
        {"utm_source": "facebook", "utm_medium": "social", "utm_campaign": "unapproved"},
    ],
)
def test_arbitrary_attribution_is_never_stored_verbatim(monkeypatch, payload):
    from backend.app.article_view_attribution import ArticleViewTrackingInput

    mongo_id = ObjectId()
    database = DatabaseSpy({"_id": mongo_id})
    tracking_input = ArticleViewTrackingInput.model_validate({"attribution": payload})

    run_tracking(monkeypatch, database, str(mongo_id), tracking_input)

    stored = database.article_views.insert_calls[0]
    assert {stored["source"], stored["medium"], stored["campaign"]} == {"unknown"}
    assert not set(payload.values()).intersection(stored.values())


def test_duplicate_does_not_overwrite_first_attribution(monkeypatch):
    from backend.app.article_view_attribution import ArticleViewTrackingInput

    mongo_id = ObjectId()
    existing = {
        "article_id": str(mongo_id),
        "source": "unknown",
        "medium": "unknown",
        "campaign": "unknown",
    }
    database = DatabaseSpy({"_id": mongo_id}, existing_view=existing)
    tracking_input = ArticleViewTrackingInput.model_validate(
        {"attribution": {"utm_source": "facebook", "utm_medium": "social", "utm_campaign": "social_publishing"}}
    )

    result = run_tracking(monkeypatch, database, str(mongo_id), tracking_input)

    assert result["counted"] is False
    assert database.article_views.insert_calls == []
    assert database.articles.update_calls == []
    assert database.article_views.find_calls[0].keys() == {
        "article_id", "ip_hash", "viewed_at"
    }


def test_attribution_request_model_rejects_unknown_oversized_and_non_string_values():
    from pydantic import ValidationError
    from backend.app.article_view_attribution import ArticleViewTrackingInput

    invalid_payloads = [
        {"attribution": {"private": "value"}},
        {"attribution": {"utm_source": "f" * 33}},
        {"attribution": {"utm_medium": 1}},
        {"attribution": {"utm_campaign": ["social_publishing"]}},
        {"unknown": {}},
    ]
    for payload in invalid_payloads:
        with pytest.raises(ValidationError):
            ArticleViewTrackingInput.model_validate(payload)


def test_http_route_accepts_bodyless_and_narrow_facebook_requests(monkeypatch):
    from backend import server

    mongo_id = ObjectId()
    bodyless_database = DatabaseSpy({"_id": mongo_id})
    monkeypatch.setattr(server, "db", bodyless_database)
    client = TestClient(server.app)

    bodyless = client.post(f"/api/articles/{mongo_id}/view")
    assert bodyless.status_code == 200
    assert bodyless_database.article_views.insert_calls[0]["source"] == "unknown"

    facebook_database = DatabaseSpy({"_id": mongo_id})
    monkeypatch.setattr(server, "db", facebook_database)
    facebook = client.post(
        f"/api/articles/{mongo_id}/view",
        json={
            "attribution": {
                "utm_source": "facebook",
                "utm_medium": "social",
                "utm_campaign": "social_publishing",
                "referrer_hostname": "www.facebook.com",
            }
        },
    )
    assert facebook.status_code == 200
    assert facebook_database.article_views.insert_calls[0]["source"] == "facebook"

    invalid = client.post(
        f"/api/articles/{mongo_id}/view",
        json={"attribution": {"utm_source": "f" * 33}},
    )
    assert invalid.status_code == 422
    assert len(facebook_database.article_views.insert_calls) == 1


@pytest.mark.parametrize(
    "raw_body,secret_value",
    [
        (
            json.dumps({"attribution": {"utm_source": "SOURCE_SECRET_" * 4}}).encode(),
            "SOURCE_SECRET_",
        ),
        (
            json.dumps({"attribution": {"utm_campaign": "CAMPAIGN_SECRET_" * 4}}).encode(),
            "CAMPAIGN_SECRET_",
        ),
        (json.dumps({"attribution": {"utm_medium": 987654321}}).encode(), "987654321"),
        (json.dumps({"attribution": {"PRIVATE_SECRET_FIELD": "value"}}).encode(), "PRIVATE_SECRET_FIELD"),
        (json.dumps({"TOP_LEVEL_SECRET_FIELD": "value"}).encode(), "TOP_LEVEL_SECRET_FIELD"),
        (b'{"attribution":{"utm_source":"MALFORMED_SECRET"', "MALFORMED_SECRET"),
    ],
)
def test_invalid_http_attribution_is_generic_and_precedes_database_access(
    monkeypatch, caplog, raw_body, secret_value
):
    from backend import server

    class UntouchedDatabase:
        def __getattr__(self, name):
            raise AssertionError("invalid attribution must not access the database")

    monkeypatch.setattr(server, "db", UntouchedDatabase())
    response = TestClient(server.app).post(
        f"/api/articles/{ObjectId()}/view",
        content=raw_body,
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid article-view attribution"}
    assert secret_value not in response.text
    assert secret_value not in repr(response.json())
    assert secret_value not in caplog.text


def test_unexpected_resolution_failure_creates_no_partial_analytics_write(monkeypatch):
    database = DatabaseSpy(find_error=RuntimeError("database unavailable"))

    result = run_tracking(monkeypatch, database, "legacy-id")

    assert result["success"] is False
    assert database.article_views.find_calls == []
    assert database.article_views.insert_calls == []
    assert database.articles.update_calls == []
