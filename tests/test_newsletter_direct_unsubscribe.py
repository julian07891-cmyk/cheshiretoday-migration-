"""Offline route tests with real signed credentials and a guarded storage double."""

import os
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server
from app.newsletter_token_service import NewsletterTokenService


SECRET = "D" * 43
MANAGEMENT_ID = "123e4567-e89b-42d3-a456-426614174000"
CONFIRM = "/api/newsletter/unsubscribe/confirm"
ONE_CLICK = "/api/newsletter/unsubscribe/one-click"


class GuardedSubscribers:
    def __init__(self):
        self.record = {
            "newsletter_management_id": MANAGEMENT_ID,
            "newsletter_token_version": 4,
            "active": True,
            "daily_brief": True,
            "weekly_roundup": True,
            "breaking_news": True,
            "unrelated": "preserved",
        }
        self.before_write = None
        self.writes = []
        self.reads = []

    def matches(self, query):
        # Assert the complete scalar-type guard as well as evaluating equality.
        assert query["$expr"] == {
            "$and": [
                {"$eq": [{"$type": "$newsletter_management_id"}, "string"]},
                {"$in": [{"$type": "$newsletter_token_version"}, ["int", "long"]]},
                {"$eq": [{"$type": "$active"}, "bool"]},
            ]
        }
        record = self.record
        return bool(record) and (
            type(record.get("newsletter_management_id")) is str
            and type(record.get("newsletter_token_version")) is int
            and type(record.get("active")) is bool
            and all(record.get(k) == v for k, v in query.items() if k != "$expr")
        )

    async def update_one(self, query, update):
        self.writes.append((deepcopy(query), deepcopy(update)))
        if self.before_write:
            self.before_write()
        matched = self.matches(query)
        if matched:
            self.record.update(update["$set"])
        return SimpleNamespace(matched_count=int(matched))

    async def find_one(self, query, projection):
        self.reads.append(deepcopy(query))
        return deepcopy(self.record) if self.matches(query) else None


@pytest.fixture
def direct(monkeypatch):
    service = NewsletterTokenService(SECRET)
    subscribers = GuardedSubscribers()
    monkeypatch.setattr(server, "db", SimpleNamespace(subscribers=subscribers))
    monkeypatch.setattr(
        server, "newsletter_token_service_from_environment", lambda: service
    )
    monkeypatch.setattr(server, "NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED", True)

    def forbidden():
        raise AssertionError("Direct tokens must not access recovery challenges")

    monkeypatch.setattr(
        server, "_create_newsletter_preference_challenge_repository", forbidden
    )
    return TestClient(server.app), service, subscribers


def post(client, route, token):
    if route == CONFIRM:
        return client.post(route, json={"token": token})
    return client.post(
        route, params={"token": token}, data={"List-Unsubscribe": "One-Click"}
    )


@pytest.mark.parametrize("route", [CONFIRM, ONE_CLICK])
def test_direct_confirmation_without_challenge_and_replay(direct, route):
    client, service, subscribers = direct
    token = service.issue_direct_unsubscribe_token(MANAGEMENT_ID, 4)
    assert post(client, route, token).status_code == 200
    record = deepcopy(subscribers.record)
    assert all(
        record[field] is False
        for field in ("active", "daily_brief", "weekly_roundup", "breaking_news")
    )
    assert record["unsubscribe_method"] == "secure_token"
    assert isinstance(record["unsubscribed_at"], datetime)
    assert record["unrelated"] == "preserved"
    assert post(client, route, token).status_code == 200
    assert subscribers.record == record


@pytest.mark.parametrize("route", [CONFIRM, ONE_CLICK])
@pytest.mark.parametrize(
    "kind", ["malformed", "expired", "wrong_class", "wrong_purpose", "signature"]
)
def test_invalid_direct_never_reaches_storage(direct, route, kind):
    client, service, subscribers = direct
    now = datetime.now(timezone.utc)
    if kind == "expired":
        now -= timedelta(days=91)
    token = service.issue_direct_unsubscribe_token(MANAGEMENT_ID, 4, now)
    if kind in ("wrong_class", "wrong_purpose"):
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        payload["credential_class" if kind == "wrong_class" else "purpose"] = (
            "preferences"
        )
        token = jwt.encode(payload, SECRET, algorithm="HS256")
    elif kind == "signature":
        token = NewsletterTokenService("E" * 43).issue_direct_unsubscribe_token(
            MANAGEMENT_ID, 4
        )
    elif kind == "malformed":
        token = "malformed"
    assert post(client, route, token).status_code in (401, 403)
    assert subscribers.writes == []
    assert subscribers.reads == []


@pytest.mark.parametrize("route", [CONFIRM, ONE_CLICK])
@pytest.mark.parametrize("active", [True, False])
@pytest.mark.parametrize("version", [5, None, True, 4.0, "4", [4], 0, -1])
def test_stale_or_invalid_stored_version_cannot_authorize(
    direct, route, active, version
):
    client, service, subscribers = direct
    subscribers.record.update(active=active, newsletter_token_version=version)
    before = deepcopy(subscribers.record)
    token = service.issue_direct_unsubscribe_token(MANAGEMENT_ID, 4)
    assert post(client, route, token).status_code == 401
    assert subscribers.record == before


@pytest.mark.parametrize("route", [CONFIRM, ONE_CLICK])
def test_reactivation_at_write_boundary_defeats_old_token(direct, route):
    client, service, subscribers = direct
    token = service.issue_direct_unsubscribe_token(MANAGEMENT_ID, 4)

    def reactivate():
        subscribers.record.update(newsletter_token_version=5, active=True)

    subscribers.before_write = reactivate
    assert post(client, route, token).status_code == 401
    assert subscribers.record["active"] is True
    assert "unsubscribed_at" not in subscribers.record
    assert subscribers.writes[0][0]["newsletter_token_version"] == 4


@pytest.mark.parametrize("route", [CONFIRM, ONE_CLICK])
def test_missing_subscriber_is_bounded(direct, route):
    client, service, subscribers = direct
    subscribers.record = None
    token = service.issue_direct_unsubscribe_token(MANAGEMENT_ID, 4)
    assert post(client, route, token).status_code == 401


@pytest.mark.parametrize("route", [CONFIRM, ONE_CLICK])
def test_previously_inactive_preserves_historical_metadata(direct, route):
    client, service, subscribers = direct
    subscribers.record.update(
        active=False,
        daily_brief=False,
        weekly_roundup=False,
        breaking_news=False,
        unsubscribed_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        unsubscribe_method="historical",
    )
    before = deepcopy(subscribers.record)
    token = service.issue_direct_unsubscribe_token(MANAGEMENT_ID, 4)
    assert post(client, route, token).status_code == 200
    assert subscribers.record == before


@pytest.mark.parametrize("identity", [None, "wrong", [MANAGEMENT_ID]])
def test_wrong_stored_identity_cannot_mutate(direct, identity):
    client, service, subscribers = direct
    subscribers.record["newsletter_management_id"] = identity
    before = deepcopy(subscribers.record)
    token = service.issue_direct_unsubscribe_token(MANAGEMENT_ID, 4)
    assert post(client, CONFIRM, token).status_code == 401
    assert subscribers.record == before


def test_direct_one_click_supports_multipart(direct):
    client, service, _ = direct
    token = service.issue_direct_unsubscribe_token(MANAGEMENT_ID, 4)
    response = client.post(
        ONE_CLICK,
        params={"token": token},
        files={"List-Unsubscribe": (None, "One-Click")},
    )
    assert response.status_code == 200


@pytest.mark.parametrize("route", ["/unsubscribe", CONFIRM, ONE_CLICK])
def test_get_cannot_mutate(direct, route):
    client, service, subscribers = direct
    token = service.issue_direct_unsubscribe_token(MANAGEMENT_ID, 4)
    client.get(route, params={"token": token})
    assert subscribers.writes == []
    assert subscribers.reads == []


@pytest.mark.parametrize(
    "content,content_type",
    [
        ("", "application/x-www-form-urlencoded"),
        ("List-Unsubscribe=Wrong", "application/x-www-form-urlencoded"),
        ("List-Unsubscribe=One-Click&extra=1", "application/x-www-form-urlencoded"),
        ("List-Unsubscribe=One-Click", "application/json"),
    ],
)
def test_protocol_failure_cannot_mutate(direct, content, content_type):
    client, service, subscribers = direct
    token = service.issue_direct_unsubscribe_token(MANAGEMENT_ID, 4)
    response = client.post(
        ONE_CLICK,
        params={"token": token},
        content=content,
        headers={"content-type": content_type},
    )
    assert response.status_code == 400
    assert subscribers.writes == []


@pytest.mark.parametrize("route", [CONFIRM, ONE_CLICK])
def test_recovery_dispatch_still_requires_challenge(direct, monkeypatch, route):
    client, service, subscribers = direct
    token = service.issue_newsletter_token(
        MANAGEMENT_ID, "unsubscribe", 4, "website_unsubscribe"
    )
    calls = []

    async def recovery(token, token_service, *, allow_inactive_replay):
        claims = token_service.verify_newsletter_token(token, "unsubscribe")
        calls.append(claims)
        raise server.HTTPException(
            status_code=401, detail=server.SECURE_NEWSLETTER_TOKEN_INVALID
        )

    monkeypatch.setattr(server, "_process_secure_newsletter_unsubscribe", recovery)
    assert post(client, route, token).status_code == 401
    assert len(calls) == 1
    assert subscribers.writes == []


@pytest.mark.parametrize("route", [CONFIRM, ONE_CLICK])
def test_database_failure_is_bounded(direct, route):
    client, service, subscribers = direct

    def fail():
        raise RuntimeError("fixture storage failure")

    subscribers.before_write = fail
    token = service.issue_direct_unsubscribe_token(MANAGEMENT_ID, 4)
    response = post(client, route, token)
    assert response.status_code == 503
    assert "fixture storage failure" not in response.text
