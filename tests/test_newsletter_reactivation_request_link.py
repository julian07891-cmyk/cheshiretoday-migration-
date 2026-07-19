import hashlib
import os
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


PATH = "/api/newsletter/reactivate/request-link"
EMAIL = "Reader@Example.com"
NORMALIZED_EMAIL = "reader@example.com"
SOURCE_IP = "203.0.113.42"
NOW = datetime(2026, 7, 19, 14, 0, tzinfo=timezone.utc)
MANAGEMENT_ID = "123e4567-e89b-42d3-a456-426614174000"
UUID_V1 = "123e4567-e89b-12d3-a456-426614174000"
TOKEN = "offline-injected-token"
UNAVAILABLE = "Secure newsletter management is not yet available."
ACCEPTED = (
    "If the address is eligible, an email with the next step will be sent "
    "shortly."
)


class FakeRateLimitRepository:
    def __init__(self, decisions=None, error=None, events=None):
        self.decisions = list(decisions or [True, True])
        self.error = error
        self.events = events
        self.calls = []

    async def reserve_request(self, **kwargs):
        self.calls.append(kwargs)
        self.events.append(f"{kwargs['dimension']}_limit")
        if self.error:
            raise self.error
        decision = self.decisions.pop(0)
        if isinstance(decision, bool):
            return SimpleNamespace(allowed=decision)
        return decision


class FakeChallengeRepository:
    def __init__(
        self,
        *,
        create_succeeds=True,
        create_error=None,
        delivered_error=None,
        failed_error=None,
        events=None,
    ):
        self.create_succeeds = create_succeeds
        self.create_error = create_error
        self.delivered_error = delivered_error
        self.failed_error = failed_error
        self.events = events
        self.created = []
        self.delivered = []
        self.failed = []

    async def create_pending(self, **kwargs):
        self.created.append(kwargs)
        self.events.append("create_pending")
        if self.create_error:
            raise self.create_error
        return SimpleNamespace(succeeded=self.create_succeeds)

    async def mark_delivered(self, token_hash):
        self.delivered.append(token_hash)
        self.events.append("mark_delivered")
        if self.delivered_error:
            raise self.delivered_error
        return SimpleNamespace(succeeded=True)

    async def mark_failed(self, token_hash):
        self.failed.append(token_hash)
        self.events.append("mark_failed")
        if self.failed_error:
            raise self.failed_error
        return SimpleNamespace(succeeded=True)


class Harness:
    def __init__(
        self,
        *,
        subscriber=None,
        rate_decisions=None,
        rate_error=None,
        lookup_error=None,
        token_result=TOKEN,
        token_error=None,
        challenge_succeeds=True,
        challenge_error=None,
        email_accepted=True,
        email_error=None,
        delivered_error=None,
        failed_error=None,
    ):
        self.events = []
        self.subscriber = subscriber
        self.lookup_error = lookup_error
        self.token_result = token_result
        self.token_error = token_error
        self.email_accepted = email_accepted
        self.email_error = email_error
        self.lookup_calls = []
        self.issue_calls = []
        self.email_calls = []
        self.rate_repository = FakeRateLimitRepository(
            rate_decisions, rate_error, self.events
        )
        self.challenge_repository = FakeChallengeRepository(
            create_succeeds=challenge_succeeds,
            create_error=challenge_error,
            delivered_error=delivered_error,
            failed_error=failed_error,
            events=self.events,
        )
        self.collaborators = server.NewsletterReactivationRequestLinkCollaborators(
            rate_limit_repository=self.rate_repository,
            challenge_repository=self.challenge_repository,
            lookup_subscriber=self.lookup_subscriber,
            issue_token=self.issue_token,
            send_management_email=self.send_management_email,
            source_ip=SOURCE_IP,
            now=NOW,
        )

    async def lookup_subscriber(self, email, projection):
        self.events.append("subscriber_lookup")
        self.lookup_calls.append((email, projection))
        if self.lookup_error:
            raise self.lookup_error
        return self.subscriber

    def issue_token(self, **kwargs):
        self.events.append("issue_token")
        self.issue_calls.append(kwargs)
        if self.token_error:
            raise self.token_error
        return self.token_result

    def send_management_email(self, **kwargs):
        self.events.append("send_email")
        self.email_calls.append(kwargs)
        if self.email_error:
            raise self.email_error
        return SimpleNamespace(accepted=self.email_accepted)


def inactive_subscriber(**overrides):
    value = {
        "newsletter_management_id": MANAGEMENT_ID,
        "newsletter_token_version": 1,
        "active": False,
    }
    value.update(overrides)
    return value


def call_route(monkeypatch, harness=None):
    harness = harness or Harness(subscriber=inactive_subscriber())
    monkeypatch.setattr(server, "NEWSLETTER_REQUEST_LINKS_ENABLED", True)
    original_normalize = server._normalize_and_hash_newsletter_request

    def factory(_request):
        harness.events.append("factory")
        return harness.collaborators

    def normalize(email, source_ip):
        harness.events.append("normalize_hash")
        return original_normalize(email, source_ip)

    monkeypatch.setattr(
        server,
        "_create_newsletter_reactivation_request_link_collaborators",
        factory,
    )
    monkeypatch.setattr(
        server,
        "_normalize_and_hash_newsletter_request",
        normalize,
    )
    response = TestClient(server.app).post(PATH, json={"email": EMAIL})
    return response, harness


def assert_generic(response):
    assert response.status_code == 202
    assert response.json() == {"success": True, "message": ACCEPTED}
    for private in (
        EMAIL.lower(),
        MANAGEMENT_ID,
        TOKEN,
        "subscriber",
        "active",
        "provider",
        "rate limit",
    ):
        assert private.lower() not in response.text.lower()


def test_readiness_gate_remains_literal_false():
    assert server.NEWSLETTER_REQUEST_LINKS_ENABLED is False


def test_disabled_gate_returns_exact_503_before_factory(monkeypatch):
    touched = False

    def factory(_request):
        nonlocal touched
        touched = True
        raise AssertionError("factory must not run")

    monkeypatch.setattr(
        server,
        "_create_newsletter_reactivation_request_link_collaborators",
        factory,
    )
    response = TestClient(server.app).post(PATH, json={"email": EMAIL})
    assert response.status_code == 503
    assert response.json() == {"detail": UNAVAILABLE}
    assert touched is False


def test_invalid_email_is_rejected_before_orchestration(monkeypatch):
    monkeypatch.setattr(server, "NEWSLETTER_REQUEST_LINKS_ENABLED", True)
    response = TestClient(server.app).post(PATH, json={"email": "invalid"})
    assert response.status_code == 422


def test_inactive_subscriber_is_eligible(monkeypatch):
    response, harness = call_route(monkeypatch)
    assert_generic(response)
    assert len(harness.issue_calls) == 1
    assert len(harness.email_calls) == 1


def test_email_normalization_projection_and_limiter_order(monkeypatch):
    response, harness = call_route(monkeypatch)
    assert_generic(response)
    assert [call["dimension"] for call in harness.rate_repository.calls] == [
        "ip",
        "email",
    ]
    assert all(
        call["operation"] == "reactivate"
        for call in harness.rate_repository.calls
    )
    assert harness.rate_repository.calls[0]["subject_hash"] == hashlib.sha256(
        SOURCE_IP.encode()
    ).hexdigest()
    assert harness.rate_repository.calls[1]["subject_hash"] == hashlib.sha256(
        NORMALIZED_EMAIL.encode()
    ).hexdigest()
    assert harness.lookup_calls == [
        (
            NORMALIZED_EMAIL,
            {
                "_id": 0,
                "newsletter_management_id": 1,
                "newsletter_token_version": 1,
                "active": 1,
            },
        )
    ]


@pytest.mark.parametrize(
    "decisions",
    [
        [False],
        [SimpleNamespace(allowed=False, reason="cooldown")],
        [SimpleNamespace(allowed=False, reason="hourly_limit")],
        [SimpleNamespace(allowed=False, reason="daily_limit")],
        [True, False],
        [True, SimpleNamespace(allowed=False, reason="cooldown")],
        [True, SimpleNamespace(allowed=False, reason="hourly_limit")],
        [True, SimpleNamespace(allowed=False, reason="daily_limit")],
    ],
)
def test_limiter_denials_stop_all_later_work(monkeypatch, decisions):
    response, harness = call_route(
        monkeypatch,
        Harness(subscriber=inactive_subscriber(), rate_decisions=decisions),
    )
    assert_generic(response)
    assert harness.lookup_calls == []
    assert harness.issue_calls == []
    assert harness.challenge_repository.created == []
    assert harness.email_calls == []


def test_limiter_storage_failure_is_non_enumerating(monkeypatch):
    response, harness = call_route(
        monkeypatch,
        Harness(rate_error=RuntimeError("private storage details")),
    )
    assert_generic(response)
    assert len(harness.rate_repository.calls) == 1
    assert harness.lookup_calls == []


@pytest.mark.parametrize(
    "value",
    [
        None,
        inactive_subscriber(active=True),
        inactive_subscriber(active=None),
        inactive_subscriber(active="false"),
        inactive_subscriber(active=0),
        inactive_subscriber(active=[]),
        inactive_subscriber(active={}),
        inactive_subscriber(newsletter_management_id=None),
        inactive_subscriber(newsletter_management_id="invalid"),
        inactive_subscriber(newsletter_management_id=MANAGEMENT_ID.upper()),
        inactive_subscriber(
            newsletter_management_id="{" + MANAGEMENT_ID + "}"
        ),
        inactive_subscriber(newsletter_management_id=UUID_V1),
        inactive_subscriber(newsletter_token_version=None),
        inactive_subscriber(newsletter_token_version=True),
        inactive_subscriber(newsletter_token_version="1"),
        inactive_subscriber(newsletter_token_version=0),
        inactive_subscriber(newsletter_token_version=-1),
    ],
)
def test_ineligible_subscribers_do_no_token_challenge_or_email(
    monkeypatch, value
):
    response, harness = call_route(monkeypatch, Harness(subscriber=value))
    assert_generic(response)
    assert harness.issue_calls == []
    assert harness.challenge_repository.created == []
    assert harness.email_calls == []


def test_token_uses_only_reactivate_purpose_and_reactivation_profile(monkeypatch):
    response, harness = call_route(monkeypatch)
    assert_generic(response)
    assert harness.issue_calls == [
        {
            "subscriber_management_id": MANAGEMENT_ID,
            "purpose": "reactivate",
            "token_version": 1,
            "expiry_profile": "reactivation",
            "now": NOW,
        }
    ]


@pytest.mark.parametrize(
    ("token_result", "token_error"),
    [
        (None, None),
        ("", None),
        (TOKEN, RuntimeError("private token failure")),
    ],
)
def test_token_failure_stops_challenge_and_email(
    monkeypatch, token_result, token_error
):
    response, harness = call_route(
        monkeypatch,
        Harness(
            subscriber=inactive_subscriber(),
            token_result=token_result,
            token_error=token_error,
        ),
    )
    assert_generic(response)
    assert harness.challenge_repository.created == []
    assert harness.email_calls == []


@pytest.mark.parametrize(
    ("succeeds", "error"),
    [(False, None), (True, RuntimeError("private duplicate conflict"))],
)
def test_challenge_failure_stops_email(monkeypatch, succeeds, error):
    response, harness = call_route(
        monkeypatch,
        Harness(
            subscriber=inactive_subscriber(),
            challenge_succeeds=succeeds,
            challenge_error=error,
        ),
    )
    assert_generic(response)
    assert len(harness.issue_calls) == 1
    assert len(harness.challenge_repository.created) == 1
    assert harness.email_calls == []


def test_pending_challenge_contains_only_approved_values(monkeypatch):
    response, harness = call_route(monkeypatch)
    assert_generic(response)
    challenge = harness.challenge_repository.created[0]
    assert challenge == {
        "token_hash": hashlib.sha256(TOKEN.encode()).hexdigest(),
        "subscriber_management_id": MANAGEMENT_ID,
        "purpose": "reactivate",
        "issued_at": NOW,
        "expires_at": NOW.replace(minute=30),
    }
    assert TOKEN not in challenge.values()
    assert NORMALIZED_EMAIL not in challenge.values()
    assert SOURCE_IP not in challenge.values()


def test_management_email_is_attempted_exactly_once(monkeypatch):
    response, harness = call_route(monkeypatch)
    assert_generic(response)
    assert harness.email_calls == [
        {
            "recipient_email": NORMALIZED_EMAIL,
            "purpose": "reactivate",
            "token": TOKEN,
            "expires_at": NOW.replace(minute=30),
            "now": NOW,
        }
    ]


@pytest.mark.parametrize(
    ("accepted", "email_error", "transition"),
    [
        (True, None, "delivered"),
        (False, None, "failed"),
        (True, RuntimeError("private provider failure"), "failed"),
    ],
)
def test_delivery_result_transitions_once_without_retry(
    monkeypatch, accepted, email_error, transition
):
    response, harness = call_route(
        monkeypatch,
        Harness(
            subscriber=inactive_subscriber(),
            email_accepted=accepted,
            email_error=email_error,
        ),
    )
    assert_generic(response)
    assert len(harness.email_calls) == 1
    assert len(harness.challenge_repository.delivered) == (
        1 if transition == "delivered" else 0
    )
    assert len(harness.challenge_repository.failed) == (
        1 if transition == "failed" else 0
    )


@pytest.mark.parametrize(
    ("accepted", "delivered_error", "failed_error"),
    [
        (True, RuntimeError("private transition failure"), None),
        (False, None, RuntimeError("private transition failure")),
    ],
)
def test_transition_failure_is_generic_and_does_not_retry(
    monkeypatch, accepted, delivered_error, failed_error
):
    response, harness = call_route(
        monkeypatch,
        Harness(
            subscriber=inactive_subscriber(),
            email_accepted=accepted,
            delivered_error=delivered_error,
            failed_error=failed_error,
        ),
    )
    assert_generic(response)
    assert len(harness.issue_calls) == 1
    assert len(harness.challenge_repository.created) == 1
    assert len(harness.email_calls) == 1


def test_successful_orchestration_order_is_exact(monkeypatch):
    response, harness = call_route(monkeypatch)
    assert_generic(response)
    assert harness.events == [
        "factory",
        "normalize_hash",
        "ip_limit",
        "email_limit",
        "subscriber_lookup",
        "issue_token",
        "create_pending",
        "send_email",
        "mark_delivered",
    ]


def test_lookup_and_factory_failures_are_non_enumerating(monkeypatch):
    response, harness = call_route(
        monkeypatch,
        Harness(lookup_error=RuntimeError("private database details")),
    )
    assert_generic(response)
    assert harness.issue_calls == []
    monkeypatch.setattr(server, "NEWSLETTER_REQUEST_LINKS_ENABLED", True)
    monkeypatch.setattr(
        server,
        "_create_newsletter_reactivation_request_link_collaborators",
        lambda _request: (_ for _ in ()).throw(RuntimeError("private factory")),
    )
    response = TestClient(server.app).post(PATH, json={"email": EMAIL})
    assert_generic(response)


def test_route_is_registered_exactly_once():
    routes = [
        route
        for route in server.app.routes
        if getattr(route, "path", None) == PATH
        and "POST" in getattr(route, "methods", set())
    ]
    assert len(routes) == 1
    assert routes[0].endpoint is server.request_secure_newsletter_reactivation_link


@pytest.mark.parametrize(
    ("method", "path", "endpoint"),
    [
        ("POST", "/api/newsletter/preferences/request-link",
         "request_secure_newsletter_preferences_link"),
        ("POST", "/api/newsletter/unsubscribe/request-link",
         "request_secure_newsletter_unsubscribe_link"),
        ("POST", "/api/newsletter/preferences/verify",
         "verify_secure_newsletter_preferences"),
        ("PUT", "/api/newsletter/preferences/secure",
         "update_secure_newsletter_preferences"),
        ("POST", "/api/newsletter/unsubscribe/confirm",
         "confirm_secure_newsletter_unsubscribe"),
        ("POST", "/api/newsletter/unsubscribe/one-click",
         "one_click_secure_newsletter_unsubscribe"),
        ("POST", "/api/newsletter/reactivate/confirm",
         "confirm_secure_newsletter_reactivation"),
        ("POST", "/api/subscribe", "subscribe_newsletter"),
        ("POST", "/api/newsletter/subscribe", "subscribe_newsletter"),
        ("GET", "/api/newsletter/preferences/{email}",
         "get_newsletter_preferences"),
        ("PUT", "/api/newsletter/preferences",
         "update_newsletter_preferences"),
        ("POST", "/api/newsletter/email-preferences",
         "update_email_preferences"),
        ("PUT", "/api/newsletter/email-preferences",
         "update_email_preferences"),
        ("GET", "/api/newsletter/email-preferences/{email}",
         "get_email_preferences"),
        ("POST", "/api/newsletter/unsubscribe",
         "unsubscribe_newsletter"),
    ],
)
def test_existing_routes_remain_registered_once(method, path, endpoint):
    matches = [
        route
        for route in server.app.routes
        if getattr(route, "path", None) == path
        and method in getattr(route, "methods", set())
    ]
    assert len(matches) == 1
    assert matches[0].endpoint.__name__ == endpoint
