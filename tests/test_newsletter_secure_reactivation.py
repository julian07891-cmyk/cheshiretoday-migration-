import os
from copy import deepcopy
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")
os.environ.pop("NEWSLETTER_LINK_SECRET", None)

from backend import server


PATH = "/api/newsletter/reactivate/confirm"
TOKEN = "offline-secure-reactivation-token"
MANAGEMENT_ID = "2d2e6acd-d310-4053-8eb7-a22b63517588"
TOKEN_VERSION = 7
SUCCESS_BODY = {
    "success": True,
    "message": "Your subscription preferences have been confirmed.",
}
GENERIC_503 = "Secure newsletter management is not yet available."
GENERIC_401 = "This newsletter management link is invalid or has expired."
GENERIC_403 = "This newsletter management link cannot be used for this action."
CONFLICT_409 = "Your subscription could not be confirmed. Please request a new link."


def _subscriber(**overrides):
    value = {
        "_id": "private-mongo-id",
        "id": "private-subscriber-id",
        "email": "private@example.com",
        "newsletter_management_id": MANAGEMENT_ID,
        "newsletter_token_version": TOKEN_VERSION,
        "active": False,
        "daily_brief": False,
        "weekly_roundup": False,
        "breaking_news": False,
        "unsubscribed_at": "historical-unsubscribe-time",
        "unsubscribe_method": "secure_token",
        "categories": ["Local News"],
        "frequency": "daily",
        "created_at": "private-created-time",
        "signup_source": "private-source",
        "delivery_history": {"private": True},
    }
    value.update(overrides)
    return value


class FakeTokenService:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def verify_newsletter_token(self, token, expected_purpose):
        self.calls.append((token, expected_purpose))
        if self.error:
            raise self.error
        return SimpleNamespace(
            subscriber_management_id=MANAGEMENT_ID,
            token_version=TOKEN_VERSION,
        )


class FakeSubscribers:
    def __init__(
        self,
        subscriber=None,
        matched_count=1,
        find_error=None,
        update_error=None,
    ):
        self.subscriber = deepcopy(subscriber)
        self.matched_count = matched_count
        self.find_error = find_error
        self.update_error = update_error
        self.find_calls = []
        self.update_calls = []

    async def find_one(self, query, projection):
        self.find_calls.append((deepcopy(query), deepcopy(projection)))
        if self.find_error:
            raise self.find_error
        if self.subscriber is None:
            return None
        return {
            key: deepcopy(value)
            for key, value in self.subscriber.items()
            if key != "_id" and projection.get(key) == 1
        }

    async def update_one(self, query, update):
        self.update_calls.append((deepcopy(query), deepcopy(update)))
        if self.update_error:
            raise self.update_error
        matches = (
            self.subscriber is not None
            and all(self.subscriber.get(key) == value for key, value in query.items())
        )
        matched_count = self.matched_count if matches else 0
        if matched_count == 1:
            self.subscriber.update(deepcopy(update["$set"]))
        return SimpleNamespace(matched_count=matched_count)

    def __getattr__(self, name):
        raise AssertionError(f"unexpected subscriber operation: {name}")


def _install(
    monkeypatch,
    *,
    subscriber=None,
    token_error=None,
    matched_count=1,
    find_error=None,
    update_error=None,
):
    token_service = FakeTokenService(error=token_error)
    subscribers = FakeSubscribers(
        subscriber=_subscriber() if subscriber is None else subscriber,
        matched_count=matched_count,
        find_error=find_error,
        update_error=update_error,
    )
    monkeypatch.setattr(
        server,
        "newsletter_token_service_from_environment",
        lambda: token_service,
    )
    monkeypatch.setattr(server, "db", SimpleNamespace(subscribers=subscribers))
    return TestClient(server.app), token_service, subscribers


def _payload(**overrides):
    value = {
        "token": TOKEN,
        "daily_brief": True,
        "weekly_roundup": False,
        "breaking_news": False,
    }
    value.update(overrides)
    return value


@pytest.mark.parametrize(
    ("configuration", "secret_value"),
    (
        ("missing", None),
        ("weak", "too-short"),
    ),
)
def test_missing_and_weak_secret_fail_before_subscriber_access(
    monkeypatch,
    configuration,
    secret_value,
):
    subscribers = FakeSubscribers(subscriber=_subscriber())
    if configuration == "missing":
        monkeypatch.delenv("NEWSLETTER_LINK_SECRET", raising=False)
    else:
        monkeypatch.setenv("NEWSLETTER_LINK_SECRET", secret_value)
    monkeypatch.setattr(server, "db", SimpleNamespace(subscribers=subscribers))

    response = TestClient(server.app).post(PATH, json=_payload())

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert subscribers.find_calls == []
    assert subscribers.update_calls == []
    assert TOKEN not in response.text
    if secret_value:
        assert secret_value not in response.text


def test_application_startup_remains_healthy_without_secret():
    assert "NEWSLETTER_LINK_SECRET" not in os.environ
    assert server.app is not None


@pytest.mark.parametrize(
    ("error", "status", "detail"),
    (
        (server.InvalidNewsletterTokenError("private payload"), 401, GENERIC_401),
        (server.ExpiredNewsletterTokenError("private payload"), 401, GENERIC_401),
        (
            server.NewsletterTokenVersionMismatchError("private payload"),
            401,
            GENERIC_401,
        ),
        (
            server.WrongNewsletterTokenPurposeError("private payload"),
            403,
            GENERIC_403,
        ),
    ),
)
def test_token_errors_are_safe_and_stop_before_lookup(
    monkeypatch,
    error,
    status,
    detail,
):
    client, token_service, subscribers = _install(
        monkeypatch,
        token_error=error,
    )

    response = client.post(PATH, json=_payload())

    assert response.status_code == status
    assert response.json() == {"detail": detail}
    assert token_service.calls == [(TOKEN, server.REACTIVATE_PURPOSE)]
    assert subscribers.find_calls == []
    assert subscribers.update_calls == []
    for private_value in (TOKEN, MANAGEMENT_ID, "private payload", "email"):
        assert private_value not in response.text


@pytest.mark.parametrize(
    "subscriber",
    (
        None,
        _subscriber(newsletter_token_version=0),
        _subscriber(newsletter_token_version=True),
        _subscriber(newsletter_token_version="7"),
        _subscriber(newsletter_token_version=TOKEN_VERSION + 1),
    ),
)
def test_missing_subscriber_or_invalid_version_returns_generic_401(
    monkeypatch,
    subscriber,
):
    client, _, subscribers = _install(
        monkeypatch,
        subscriber=subscriber,
    )
    if subscriber is None:
        subscribers.subscriber = None

    response = client.post(PATH, json=_payload())

    assert response.status_code == 401
    assert response.json() == {"detail": GENERIC_401}
    assert subscribers.update_calls == []


@pytest.mark.parametrize(
    "active_value",
    (
        pytest.param(True, id="already-active"),
        pytest.param("missing", id="missing"),
        pytest.param(None, id="null"),
        pytest.param("false", id="string"),
        pytest.param(0, id="integer"),
        pytest.param([], id="list"),
        pytest.param({}, id="dictionary"),
    ),
)
def test_only_literal_false_is_eligible_for_reactivation(
    monkeypatch,
    active_value,
):
    subscriber = _subscriber()
    if active_value == "missing":
        subscriber.pop("active")
    else:
        subscriber["active"] = active_value
    client, _, subscribers = _install(
        monkeypatch,
        subscriber=subscriber,
    )

    response = client.post(PATH, json=_payload())

    assert response.status_code == 409
    assert response.json() == {"detail": CONFLICT_409}
    assert subscribers.update_calls == []
    for private_value in (TOKEN, MANAGEMENT_ID, "private@example.com"):
        assert private_value not in response.text


@pytest.mark.parametrize(
    ("daily_brief", "weekly_roundup", "breaking_news"),
    (
        (True, False, False),
        (False, False, False),
        (False, True, True),
    ),
)
def test_successful_reactivation_updates_exact_approved_fields(
    monkeypatch,
    daily_brief,
    weekly_roundup,
    breaking_news,
):
    original = _subscriber()
    client, token_service, subscribers = _install(
        monkeypatch,
        subscriber=original,
    )

    response = client.post(
        PATH,
        json=_payload(
            daily_brief=daily_brief,
            weekly_roundup=weekly_roundup,
            breaking_news=breaking_news,
        ),
    )

    assert response.status_code == 200
    assert response.json() == SUCCESS_BODY
    assert token_service.calls == [(TOKEN, server.REACTIVATE_PURPOSE)]
    assert subscribers.find_calls == [
        (
            {"newsletter_management_id": MANAGEMENT_ID},
            {
                "_id": 0,
                "newsletter_token_version": 1,
                "active": 1,
            },
        )
    ]
    query, update = subscribers.update_calls[0]
    assert query == {
        "newsletter_management_id": MANAGEMENT_ID,
        "newsletter_token_version": TOKEN_VERSION,
        "active": False,
    }
    assert set(update) == {"$set"}
    assert set(update["$set"]) == {
        "active",
        "daily_brief",
        "weekly_roundup",
        "breaking_news",
        "reactivated_at",
        "reactivation_method",
        "preferences_updated_at",
        "newsletter_token_version",
    }
    assert update["$set"]["active"] is True
    assert update["$set"]["daily_brief"] is daily_brief
    assert update["$set"]["weekly_roundup"] is weekly_roundup
    assert update["$set"]["breaking_news"] is breaking_news
    assert update["$set"]["reactivation_method"] == "verified_email"
    assert update["$set"]["newsletter_token_version"] == TOKEN_VERSION + 1
    assert update["$set"]["reactivated_at"].tzinfo is not None
    assert (
        update["$set"]["preferences_updated_at"]
        == update["$set"]["reactivated_at"]
    )
    for preserved in (
        "email",
        "id",
        "newsletter_management_id",
        "unsubscribed_at",
        "unsubscribe_method",
        "categories",
        "frequency",
        "created_at",
        "signup_source",
        "delivery_history",
    ):
        assert subscribers.subscriber[preserved] == original[preserved]
    assert set(response.json()) == {"success", "message"}


def test_replayed_token_fails_without_second_update(monkeypatch):
    client, _, subscribers = _install(monkeypatch)

    first = client.post(PATH, json=_payload())
    replay = client.post(PATH, json=_payload())

    assert first.status_code == 200
    assert replay.status_code == 401
    assert replay.json() == {"detail": GENERIC_401}
    assert len(subscribers.update_calls) == 1


def test_conditional_conflict_rechecks_then_returns_409(monkeypatch):
    client, _, subscribers = _install(
        monkeypatch,
        matched_count=0,
    )

    response = client.post(PATH, json=_payload())

    assert response.status_code == 409
    assert response.json() == {"detail": CONFLICT_409}
    assert len(subscribers.find_calls) == 2
    assert len(subscribers.update_calls) == 1


@pytest.mark.parametrize("operation", ("find", "update"))
def test_database_failure_returns_generic_503(monkeypatch, operation):
    client, _, subscribers = _install(
        monkeypatch,
        find_error=RuntimeError("private database detail") if operation == "find" else None,
        update_error=RuntimeError("private database detail") if operation == "update" else None,
    )

    response = client.post(PATH, json=_payload())

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert "private database detail" not in response.text
    if operation == "find":
        assert subscribers.update_calls == []


def test_three_request_link_routes_remain_dormant(monkeypatch):
    class FailOnAccess:
        def __getattr__(self, name):
            raise AssertionError(f"unexpected collaborator access: {name}")

    monkeypatch.setattr(server, "db", FailOnAccess())
    monkeypatch.setattr(server, "email_service", FailOnAccess())
    client = TestClient(server.app)
    routes = (
        ("/api/newsletter/preferences/request-link", {"email": "reader@example.com"}),
        ("/api/newsletter/unsubscribe/request-link", {"email": "reader@example.com"}),
        ("/api/newsletter/reactivate/request-link", {"email": "reader@example.com"}),
    )

    for path, payload in routes:
        response = client.post(path, json=payload)
        assert response.status_code == 503
        assert response.json() == {"detail": GENERIC_503}


def test_earlier_secure_and_legacy_routes_remain_singly_registered():
    expected = (
        ("POST", "/api/newsletter/preferences/verify"),
        ("PUT", "/api/newsletter/preferences/secure"),
        ("POST", "/api/newsletter/unsubscribe/confirm"),
        ("POST", "/api/newsletter/unsubscribe/one-click"),
        ("POST", "/api/subscribe"),
        ("POST", "/api/newsletter/subscribe"),
        ("GET", "/api/newsletter/preferences/{email}"),
        ("PUT", "/api/newsletter/preferences"),
        ("POST", "/api/newsletter/email-preferences"),
        ("PUT", "/api/newsletter/email-preferences"),
        ("GET", "/api/newsletter/email-preferences/{email}"),
        ("POST", "/api/newsletter/unsubscribe"),
    )

    for method, path in expected:
        routes = [
            route
            for route in server.app.routes
            if getattr(route, "path", None) == path
            and method in getattr(route, "methods", set())
        ]
        assert len(routes) == 1

