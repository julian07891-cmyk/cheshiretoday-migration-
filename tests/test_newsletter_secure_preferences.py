import os
from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")
os.environ.pop("NEWSLETTER_LINK_SECRET", None)

from backend import server


TOKEN = "offline-secure-preference-token"
MANAGEMENT_ID = "a40ad20d-2439-4b5a-b4ce-f256c79a3daf"
TOKEN_VERSION = 3

GENERIC_503 = "Secure newsletter management is not yet available."
GENERIC_401 = "This newsletter management link is invalid or has expired."
GENERIC_403 = "This newsletter management link cannot be used for this action."
REACTIVATION_409 = (
    "Please reactivate your subscription before managing email preferences."
)
CONFLICT_409 = "Your email preferences could not be updated. Please try again."

VERIFY_PATH = "/api/newsletter/preferences/verify"
UPDATE_PATH = "/api/newsletter/preferences/secure"

DORMANT_ROUTES = (
    ("POST", "/api/newsletter/preferences/request-link", {"email": "reader@example.com"}),
    ("POST", "/api/newsletter/unsubscribe/confirm", {"token": TOKEN}),
    ("POST", "/api/newsletter/unsubscribe/one-click", None),
    ("POST", "/api/newsletter/unsubscribe/request-link", {"email": "reader@example.com"}),
    ("POST", "/api/newsletter/reactivate/request-link", {"email": "reader@example.com"}),
    (
        "POST",
        "/api/newsletter/reactivate/confirm",
        {
            "token": TOKEN,
            "daily_brief": True,
            "weekly_roundup": False,
            "breaking_news": False,
        },
    ),
)


def _active_subscriber(**overrides):
    subscriber = {
        "_id": "private-mongo-id",
        "id": "private-subscriber-id",
        "email": "private@example.com",
        "newsletter_management_id": MANAGEMENT_ID,
        "newsletter_token_version": TOKEN_VERSION,
        "active": True,
        "daily_brief": True,
        "weekly_roundup": False,
        "breaking_news": False,
        "preferences": {"categories": ["Local News"], "frequency": "daily"},
        "subscribed_at": "private-timestamp",
        "signup_source": "private-source",
    }
    subscriber.update(overrides)
    return subscriber


class FakeTokenService:
    def __init__(self, error=None, claims=None):
        self.error = error
        self.claims = claims or SimpleNamespace(
            subscriber_management_id=MANAGEMENT_ID,
            token_version=TOKEN_VERSION,
        )
        self.calls = []

    def verify_newsletter_token(self, token, expected_purpose):
        self.calls.append((token, expected_purpose))
        if self.error:
            raise self.error
        return self.claims


class FakeSubscriberCollection:
    def __init__(self, subscriber=None, matched_count=1, find_error=None, update_error=None):
        self.subscriber = deepcopy(subscriber)
        self.matched_count = matched_count
        self.find_error = find_error
        self.update_error = update_error
        self.find_calls = []
        self.update_calls = []

    async def find_one(self, query, projection, **kwargs):
        self.find_calls.append(
            (deepcopy(query), deepcopy(projection), dict(kwargs))
        )
        if self.find_error:
            raise self.find_error
        return deepcopy(self.subscriber)

    async def update_one(self, query, update, **kwargs):
        self.update_calls.append(
            (deepcopy(query), deepcopy(update), dict(kwargs))
        )
        if self.update_error:
            raise self.update_error
        return SimpleNamespace(matched_count=self.matched_count)


class FakeChallengeRepository:
    def __init__(self, result=None, error=None):
        self.result = (
            SimpleNamespace(
                succeeded=True,
                reason=server.ChallengeResultReason.ELIGIBLE,
            )
            if result is None
            else result
        )
        self.error = error
        self.read_calls = []
        self.consume_calls = []
        self.consumed = False

    async def read_eligible_preference(self, **kwargs):
        self.read_calls.append(deepcopy(kwargs))
        if self.error:
            raise self.error
        return self.result

    async def consume(self, **kwargs):
        self.consume_calls.append(dict(kwargs))
        if self.error:
            raise self.error
        if self.consumed:
            return SimpleNamespace(
                succeeded=False,
                reason=server.ChallengeResultReason.NOT_ELIGIBLE,
            )
        self.consumed = True
        return SimpleNamespace(
            succeeded=True,
            reason=server.ChallengeResultReason.CONSUMED,
        )


class FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False


class FakeSession:
    def start_transaction(self):
        return FakeTransaction()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False


class FakeTransactionClient:
    async def start_session(self):
        return FakeSession()


def _install(
    monkeypatch,
    *,
    subscriber=None,
    token_error=None,
    claims=None,
    matched_count=1,
    find_error=None,
    update_error=None,
    challenge_result=None,
    challenge_error=None,
):
    token_service = FakeTokenService(error=token_error, claims=claims)
    subscribers = FakeSubscriberCollection(
        subscriber=subscriber,
        matched_count=matched_count,
        find_error=find_error,
        update_error=update_error,
    )
    monkeypatch.setattr(
        server,
        "newsletter_token_service_from_environment",
        lambda: token_service,
    )
    challenge_repository = FakeChallengeRepository(
        result=challenge_result,
        error=challenge_error,
    )
    monkeypatch.setattr(
        server,
        "NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED",
        True,
    )
    monkeypatch.setattr(
        server,
        "_create_newsletter_preference_challenge_repository",
        lambda: challenge_repository,
    )
    monkeypatch.setattr(
        server,
        "_create_newsletter_preference_transaction_client",
        lambda: FakeTransactionClient(),
    )
    monkeypatch.setattr(server, "db", SimpleNamespace(subscribers=subscribers))
    return (
        TestClient(server.app),
        token_service,
        subscribers,
        challenge_repository,
    )


@pytest.mark.parametrize("route", (VERIFY_PATH, UPDATE_PATH))
def test_missing_or_weak_secret_returns_503_before_subscriber_lookup(
    monkeypatch,
    route,
):
    subscribers = FakeSubscriberCollection(subscriber=_active_subscriber())

    def fail_closed_factory():
        raise server.NewsletterTokenConfigurationError(
            "safe configuration failure"
        )

    monkeypatch.setattr(
        server,
        "newsletter_token_service_from_environment",
        fail_closed_factory,
    )
    monkeypatch.setattr(
        server,
        "NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED",
        True,
    )
    monkeypatch.setattr(server, "db", SimpleNamespace(subscribers=subscribers))
    payload = {"token": TOKEN}
    if route == UPDATE_PATH:
        payload.update(
            daily_brief=True,
            weekly_roundup=False,
            breaking_news=False,
        )

    response = TestClient(server.app).request(
        "POST" if route == VERIFY_PATH else "PUT",
        route,
        json=payload,
    )

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert subscribers.find_calls == []
    assert subscribers.update_calls == []


def test_application_import_succeeds_without_newsletter_secret():
    assert "NEWSLETTER_LINK_SECRET" not in os.environ
    assert server.app is not None


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_detail"),
    (
        (
            server.InvalidNewsletterTokenError("safe invalid token"),
            401,
            GENERIC_401,
        ),
        (
            server.ExpiredNewsletterTokenError("safe expired token"),
            401,
            GENERIC_401,
        ),
        (
            server.NewsletterTokenVersionMismatchError("safe mismatch"),
            401,
            GENERIC_401,
        ),
        (
            server.WrongNewsletterTokenPurposeError("safe wrong purpose"),
            403,
            GENERIC_403,
        ),
    ),
)
def test_token_failures_are_safely_mapped_before_lookup(
    monkeypatch,
    error,
    expected_status,
    expected_detail,
):
    client, token_service, subscribers, _ = _install(
        monkeypatch,
        subscriber=_active_subscriber(),
        token_error=error,
    )

    response = client.post(VERIFY_PATH, json={"token": TOKEN})

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}
    assert token_service.calls == [(TOKEN, server.PREFERENCES_PURPOSE)]
    assert subscribers.find_calls == []
    assert subscribers.update_calls == []

    rendered = response.text
    for private_value in (
        TOKEN,
        MANAGEMENT_ID,
        "private@example.com",
        "safe invalid token",
        "safe expired token",
        "safe mismatch",
        "safe wrong purpose",
    ):
        assert private_value not in rendered


def test_subscriber_lookup_uses_management_id_and_minimal_projection(monkeypatch):
    client, _, subscribers, _ = _install(
        monkeypatch,
        subscriber=_active_subscriber(),
    )

    response = client.post(VERIFY_PATH, json={"token": TOKEN})

    assert response.status_code == 200
    assert subscribers.find_calls == [
        (
            {"newsletter_management_id": MANAGEMENT_ID},
            {
                "_id": 0,
                "newsletter_management_id": 1,
                "newsletter_token_version": 1,
                "active": 1,
                "daily_brief": 1,
                "weekly_roundup": 1,
                "breaking_news": 1,
            },
            {},
        )
    ]


@pytest.mark.parametrize(
    "subscriber",
    (
        None,
        _active_subscriber(newsletter_token_version=None),
        _active_subscriber(newsletter_token_version=True),
        _active_subscriber(newsletter_token_version=0),
        _active_subscriber(newsletter_token_version="3"),
        _active_subscriber(newsletter_token_version=TOKEN_VERSION + 1),
    ),
)
def test_missing_subscriber_or_invalid_stored_version_is_generic_401(
    monkeypatch,
    subscriber,
):
    client, _, subscribers, _ = _install(
        monkeypatch,
        subscriber=subscriber,
    )

    response = client.post(VERIFY_PATH, json={"token": TOKEN})

    assert response.status_code == 401
    assert response.json() == {"detail": GENERIC_401}
    assert subscribers.update_calls == []
    assert "subscriber" not in response.text.lower()
    assert MANAGEMENT_ID not in response.text


def test_inactive_subscriber_requires_reactivation_without_write(monkeypatch):
    client, _, subscribers, _ = _install(
        monkeypatch,
        subscriber=_active_subscriber(active=False),
    )

    response = client.post(VERIFY_PATH, json={"token": TOKEN})

    assert response.status_code == 409
    assert response.json() == {"detail": REACTIVATION_409}
    assert subscribers.update_calls == []
    assert MANAGEMENT_ID not in response.text


def test_verify_returns_only_three_preferences_and_performs_no_write(monkeypatch):
    client, _, subscribers, _ = _install(
        monkeypatch,
        subscriber=_active_subscriber(
            daily_brief=False,
            weekly_roundup=True,
            breaking_news=True,
        ),
    )

    response = client.post(VERIFY_PATH, json={"token": TOKEN})

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "preferences": {
            "daily_brief": False,
            "weekly_roundup": True,
            "breaking_news": True,
        },
    }
    assert subscribers.update_calls == []
    rendered = response.text
    for private_value in (
        "email",
        "active",
        "_id",
        "management",
        "token_version",
        "subscribed_at",
        "frequency",
        "categories",
    ):
        assert private_value not in rendered


def test_secure_update_changes_only_tiers_and_timestamp_with_conditions(monkeypatch):
    client, _, subscribers, _ = _install(
        monkeypatch,
        subscriber=_active_subscriber(),
    )

    response = client.put(
        UPDATE_PATH,
        json={
            "token": TOKEN,
            "daily_brief": False,
            "weekly_roundup": True,
            "breaking_news": False,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Your email preferences have been updated.",
    }
    assert len(subscribers.update_calls) == 1
    query, update, options = subscribers.update_calls[0]
    assert query == {
        "newsletter_management_id": MANAGEMENT_ID,
        "newsletter_token_version": TOKEN_VERSION,
        "active": True,
    }
    assert set(update) == {"$set"}
    assert set(update["$set"]) == {
        "daily_brief",
        "weekly_roundup",
        "breaking_news",
        "preferences_updated_at",
    }
    assert update["$set"]["daily_brief"] is False
    assert update["$set"]["weekly_roundup"] is True
    assert update["$set"]["breaking_news"] is False
    assert isinstance(update["$set"]["preferences_updated_at"], datetime)
    assert update["$set"]["preferences_updated_at"].tzinfo == timezone.utc
    assert "newsletter_token_version" not in update["$set"]
    assert options.keys() == {"session"}


def test_all_false_preferences_are_accepted(monkeypatch):
    client, _, subscribers, _ = _install(
        monkeypatch,
        subscriber=_active_subscriber(),
    )

    response = client.put(
        UPDATE_PATH,
        json={
            "token": TOKEN,
            "daily_brief": False,
            "weekly_roundup": False,
            "breaking_news": False,
        },
    )

    assert response.status_code == 200
    assert subscribers.update_calls[0][1]["$set"]["daily_brief"] is False
    assert subscribers.update_calls[0][1]["$set"]["weekly_roundup"] is False
    assert subscribers.update_calls[0][1]["$set"]["breaking_news"] is False


def test_replay_is_rejected_and_does_not_increment_version(monkeypatch):
    client, _, subscribers, challenge_repository = _install(
        monkeypatch,
        subscriber=_active_subscriber(),
    )
    payload = {
        "token": TOKEN,
        "daily_brief": True,
        "weekly_roundup": False,
        "breaking_news": False,
    }

    first = client.put(UPDATE_PATH, json=payload)
    second = client.put(UPDATE_PATH, json=payload)

    assert first.status_code == 200
    assert second.status_code == 401
    assert second.json() == {"detail": GENERIC_401}
    assert len(subscribers.update_calls) == 1
    assert len(challenge_repository.consume_calls) == 2
    assert (
        "newsletter_token_version"
        not in subscribers.update_calls[0][1]["$set"]
    )


def test_conditional_update_conflict_returns_generic_409(monkeypatch):
    client, _, subscribers, _ = _install(
        monkeypatch,
        subscriber=_active_subscriber(),
        matched_count=0,
    )

    response = client.put(
        UPDATE_PATH,
        json={
            "token": TOKEN,
            "daily_brief": True,
            "weekly_roundup": False,
            "breaking_news": False,
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": CONFLICT_409}
    assert MANAGEMENT_ID not in response.text
    assert TOKEN not in response.text


@pytest.mark.parametrize(("method", "path", "payload"), DORMANT_ROUTES)
def test_other_six_secure_routes_remain_exact_generic_503(
    monkeypatch,
    method,
    path,
    payload,
):
    subscribers = FakeSubscriberCollection(subscriber=_active_subscriber())
    monkeypatch.setattr(server, "db", SimpleNamespace(subscribers=subscribers))

    client = TestClient(server.app)
    if path.endswith("/one-click"):
        response = client.request(
            method,
            path,
            content="List-Unsubscribe=One-Click",
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
    else:
        response = client.request(method, path, json=payload)

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert subscribers.find_calls == []
    assert subscribers.update_calls == []


def test_verify_uses_challenge_but_no_email_or_rate_limit_collaborator(
    monkeypatch,
):
    class FailOnAccess:
        def __getattr__(self, name):
            raise AssertionError(f"unexpected collaborator access: {name}")

    client, _, _, challenge_repository = _install(
        monkeypatch,
        subscriber=_active_subscriber(),
    )
    monkeypatch.setattr(server, "email_service", FailOnAccess())

    response = client.post(VERIFY_PATH, json={"token": TOKEN})

    assert response.status_code == 200
    assert len(challenge_repository.read_calls) == 1
    source = open(server.__file__, encoding="utf-8").read()
    secure_section = source[
        source.index("def _create_secure_newsletter_token_service"):
        source.index('@api_router.get("/newsletter/categories")')
    ]
    assert "rate_limit" not in secure_section
    assert "email_service" not in secure_section


@pytest.mark.parametrize("route", (VERIFY_PATH, UPDATE_PATH))
def test_database_failure_is_generic_503(monkeypatch, route):
    client, _, _, _ = _install(
        monkeypatch,
        subscriber=_active_subscriber(),
        find_error=RuntimeError("private database payload"),
    )
    payload = {"token": TOKEN}
    if route == UPDATE_PATH:
        payload.update(
            daily_brief=True,
            weekly_roundup=False,
            breaking_news=False,
        )

    response = client.request(
        "POST" if route == VERIFY_PATH else "PUT",
        route,
        json=payload,
    )

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert "private database payload" not in response.text
