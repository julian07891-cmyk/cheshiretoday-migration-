import hashlib
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


VERIFY_PATH = "/api/newsletter/preferences/verify"
TOKEN = "offline-stage-4e6a-token"
TOKEN_HASH = hashlib.sha256(TOKEN.encode()).hexdigest()
MANAGEMENT_ID = "a40ad20d-2439-4b5a-b4ce-f256c79a3daf"
GENERIC_503 = "Secure newsletter management is not yet available."
GENERIC_401 = "This newsletter management link is invalid or has expired."


class OrderedTokenService:
    def __init__(self, order):
        self.order = order

    def verify_newsletter_token(self, token, expected_purpose):
        self.order.append(("token", token, expected_purpose))
        return SimpleNamespace(
            subscriber_management_id=MANAGEMENT_ID,
            token_version=3,
        )


class OrderedSubscribers:
    def __init__(self, order):
        self.order = order
        self.update_calls = []

    async def find_one(self, query, projection):
        self.order.append(("subscriber", deepcopy(query), deepcopy(projection)))
        return {
            "newsletter_management_id": MANAGEMENT_ID,
            "newsletter_token_version": 3,
            "active": True,
            "daily_brief": True,
            "weekly_roundup": False,
            "breaking_news": False,
        }

    async def update_one(self, query, update):
        self.update_calls.append((deepcopy(query), deepcopy(update)))
        return SimpleNamespace(matched_count=1)


class OrderedChallengeRepository:
    def __init__(self, order, result=None, error=None):
        self.order = order
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

    async def read_eligible_preference(self, **kwargs):
        self.order.append(("challenge",))
        self.read_calls.append(deepcopy(kwargs))
        if self.error:
            raise self.error
        return self.result

    async def consume(self, **kwargs):
        self.consume_calls.append(deepcopy(kwargs))
        raise AssertionError("Stage 4E6A preference verification is read-only")


def _install_enabled(monkeypatch, *, challenge_result=None, challenge_error=None):
    order = []
    token_service = OrderedTokenService(order)
    subscribers = OrderedSubscribers(order)
    challenge_repository = OrderedChallengeRepository(
        order,
        result=challenge_result,
        error=challenge_error,
    )

    def token_factory():
        order.append(("token_factory",))
        return token_service

    def token_hasher(token):
        order.append(("hash", token))
        return TOKEN_HASH

    def challenge_factory():
        order.append(("challenge_factory",))
        return challenge_repository

    monkeypatch.setattr(
        server,
        "NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED",
        True,
    )
    monkeypatch.setattr(
        server,
        "newsletter_token_service_from_environment",
        token_factory,
    )
    monkeypatch.setattr(
        server,
        "hash_newsletter_challenge_token",
        token_hasher,
    )
    monkeypatch.setattr(
        server,
        "_create_newsletter_preference_challenge_repository",
        challenge_factory,
    )
    monkeypatch.setattr(server, "db", SimpleNamespace(subscribers=subscribers))
    return (
        TestClient(server.app),
        order,
        subscribers,
        challenge_repository,
    )


def test_confirmation_enforcement_gate_is_literal_false_in_source():
    source = open(server.__file__, encoding="utf-8").read()
    assert "NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED = False" in source
    assert server.NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED is False


def test_disabled_gate_precedes_every_collaborator(monkeypatch):
    class FailOnAccess:
        def __getattr__(self, name):
            raise AssertionError(f"unexpected access: {name}")

    monkeypatch.setattr(
        server,
        "NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED",
        False,
    )
    monkeypatch.setattr(
        server,
        "newsletter_token_service_from_environment",
        lambda: (_ for _ in ()).throw(AssertionError("token service called")),
    )
    monkeypatch.setattr(
        server,
        "hash_newsletter_challenge_token",
        lambda _token: (_ for _ in ()).throw(AssertionError("hash called")),
    )
    monkeypatch.setattr(
        server,
        "_create_newsletter_preference_challenge_repository",
        lambda: (_ for _ in ()).throw(AssertionError("challenge called")),
    )
    monkeypatch.setattr(server, "db", FailOnAccess())

    response = TestClient(server.app).post(
        VERIFY_PATH,
        json={"token": TOKEN},
    )

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}


def test_valid_challenge_backed_preference_verification_is_read_only(
    monkeypatch,
):
    client, order, subscribers, challenge_repository = _install_enabled(
        monkeypatch
    )

    response = client.post(VERIFY_PATH, json={"token": TOKEN})

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "preferences": {
            "daily_brief": True,
            "weekly_roundup": False,
            "breaking_news": False,
        },
    }
    assert [step[0] for step in order] == [
        "token_factory",
        "token",
        "subscriber",
        "hash",
        "challenge_factory",
        "challenge",
    ]
    assert challenge_repository.read_calls[0]["token_hash"] == TOKEN_HASH
    assert (
        challenge_repository.read_calls[0]["subscriber_management_id"]
        == MANAGEMENT_ID
    )
    assert challenge_repository.consume_calls == []
    assert subscribers.update_calls == []


@pytest.mark.parametrize(
    "result",
    (
        SimpleNamespace(
            succeeded=False,
            reason=server.ChallengeResultReason.NOT_ELIGIBLE,
        ),
        SimpleNamespace(
            succeeded=False,
            reason=server.ChallengeResultReason.FAILED,
        ),
        SimpleNamespace(
            succeeded=False,
            reason=server.ChallengeResultReason.CONSUMED,
        ),
        SimpleNamespace(succeeded=True, reason="malformed"),
        SimpleNamespace(succeeded=False),
    ),
)
def test_ineligible_or_malformed_challenge_result_is_generic_401(
    monkeypatch,
    result,
):
    client, _, _, _ = _install_enabled(
        monkeypatch,
        challenge_result=result,
    )

    response = client.post(VERIFY_PATH, json={"token": TOKEN})

    assert response.status_code == 401
    assert response.json() == {"detail": GENERIC_401}
    assert TOKEN not in response.text
    assert TOKEN_HASH not in response.text
    assert MANAGEMENT_ID not in response.text


def test_challenge_storage_result_is_generic_503(monkeypatch):
    client, _, _, _ = _install_enabled(
        monkeypatch,
        challenge_result=SimpleNamespace(
            succeeded=False,
            reason=server.ChallengeResultReason.STORAGE_ERROR,
        ),
    )

    response = client.post(VERIFY_PATH, json={"token": TOKEN})

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}


@pytest.mark.parametrize(
    "failure",
    (
        RuntimeError("private factory detail"),
        RuntimeError("private storage detail"),
    ),
)
def test_challenge_factory_or_read_exception_is_generic_503(
    monkeypatch,
    failure,
):
    client, _, _, challenge_repository = _install_enabled(
        monkeypatch,
        challenge_error=failure,
    )
    if "factory" in str(failure):
        monkeypatch.setattr(
            server,
            "_create_newsletter_preference_challenge_repository",
            lambda: (_ for _ in ()).throw(failure),
        )
    else:
        challenge_repository.error = failure

    response = client.post(VERIFY_PATH, json={"token": TOKEN})

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert str(failure) not in response.text


def test_route_registration_and_unrelated_routes_are_preserved():
    routes = [
        (method, route.path)
        for route in server.app.routes
        for method in getattr(route, "methods", set())
    ]
    expected = (
        ("POST", "/api/newsletter/preferences/verify"),
        ("PUT", "/api/newsletter/preferences/secure"),
        ("POST", "/api/newsletter/unsubscribe/confirm"),
        ("POST", "/api/newsletter/unsubscribe/one-click"),
        ("POST", "/api/newsletter/reactivate/confirm"),
        ("POST", "/api/newsletter/preferences/request-link"),
        ("POST", "/api/newsletter/unsubscribe/request-link"),
        ("POST", "/api/newsletter/reactivate/request-link"),
        ("POST", "/api/subscribe"),
        ("POST", "/api/newsletter/subscribe"),
        ("GET", "/api/newsletter/preferences/{email}"),
        ("PUT", "/api/newsletter/preferences"),
        ("POST", "/api/newsletter/email-preferences"),
        ("PUT", "/api/newsletter/email-preferences"),
        ("GET", "/api/newsletter/email-preferences/{email}"),
        ("POST", "/api/newsletter/unsubscribe"),
    )
    for registration in expected:
        assert routes.count(registration) == 1


def test_no_runtime_activation_or_production_collaborators_exist():
    source = open(server.__file__, encoding="utf-8").read()
    assert "NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED = False" in source
    assert "NewsletterChallengeRepository(" not in source
    assert "create_index(" not in source[
        source.index("NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED"):
        source.index('@api_router.get("/newsletter/categories")')
    ]
