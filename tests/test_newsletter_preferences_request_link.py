import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")
os.environ.pop("NEWSLETTER_LINK_SECRET", None)

from backend import server


PATH = "/api/newsletter/preferences/request-link"
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


class FailOnAccess:
    def __init__(self, label):
        self.label = label
        self.touched = False

    def __getattr__(self, name):
        self.touched = True
        raise AssertionError(f"{self.label} must remain untouched")


class FakeRateLimitRepository:
    def __init__(self, decisions=None, error=None, events=None):
        self.decisions = list(decisions or [True, True])
        self.error = error
        self.calls = []
        self.events = events

    async def reserve_request(self, **kwargs):
        self.calls.append(kwargs)
        if self.events is not None:
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
        self.delivered_confirmed = []
        self.failed = []
        self.failed_confirmed = []

    async def create_pending(self, **kwargs):
        self.created.append(kwargs)
        if self.events is not None:
            self.events.append("create_pending")
        if self.create_error:
            raise self.create_error
        return SimpleNamespace(succeeded=self.create_succeeds)

    async def mark_delivered(self, token_hash):
        self.delivered.append(token_hash)
        if self.events is not None:
            self.events.append("mark_delivered")
        if self.delivered_error:
            raise self.delivered_error
        self.delivered_confirmed.append(token_hash)
        return SimpleNamespace(succeeded=True)

    async def mark_failed(self, token_hash):
        self.failed.append(token_hash)
        if self.events is not None:
            self.events.append("mark_failed")
        if self.failed_error:
            raise self.failed_error
        self.failed_confirmed.append(token_hash)
        return SimpleNamespace(succeeded=True)


class CollaboratorHarness:
    def __init__(
        self,
        *,
        subscriber=None,
        rate_decisions=None,
        rate_error=None,
        challenge_succeeds=True,
        challenge_error=None,
        email_accepted=True,
        email_error=None,
        lookup_error=None,
        token_result=TOKEN,
        token_error=None,
        delivered_error=None,
        failed_error=None,
        events=None,
    ):
        self.events = events if events is not None else []
        self.subscriber = subscriber
        self.lookup_error = lookup_error
        self.token_result = token_result
        self.token_error = token_error
        self.lookup_calls = []
        self.issue_calls = []
        self.email_calls = []
        self.email_accepted = email_accepted
        self.email_error = email_error
        self.rate_repository = FakeRateLimitRepository(
            rate_decisions,
            rate_error,
            self.events,
        )
        self.challenge_repository = FakeChallengeRepository(
            challenge_succeeds,
            challenge_error,
            delivered_error,
            failed_error,
            self.events,
        )
        self.collaborators = (
            server.NewsletterPreferencesRequestLinkCollaborators(
                rate_limit_repository=self.rate_repository,
                challenge_repository=self.challenge_repository,
                lookup_subscriber=self.lookup_subscriber,
                issue_token=self.issue_token,
                send_management_email=self.send_management_email,
                source_ip=SOURCE_IP,
                now=NOW,
            )
        )

    async def lookup_subscriber(self, email, projection):
        self.lookup_calls.append((email, projection))
        self.events.append("subscriber_lookup")
        if self.lookup_error:
            raise self.lookup_error
        return self.subscriber

    def issue_token(self, **kwargs):
        self.issue_calls.append(kwargs)
        self.events.append("issue_token")
        if self.token_error:
            raise self.token_error
        return self.token_result

    def send_management_email(self, **kwargs):
        self.email_calls.append(kwargs)
        self.events.append("send_email")
        if self.email_error:
            raise self.email_error
        return SimpleNamespace(accepted=self.email_accepted)


def active_subscriber(**overrides):
    subscriber = {
        "newsletter_management_id": MANAGEMENT_ID,
        "newsletter_token_version": 1,
        "active": True,
    }
    subscriber.update(overrides)
    return subscriber


def call_route(monkeypatch, harness=None):
    monkeypatch.setattr(server, "NEWSLETTER_REQUEST_LINKS_ENABLED", True)
    if harness is None:
        harness = CollaboratorHarness(subscriber=active_subscriber())

    original_normalize = server._normalize_and_hash_newsletter_request

    def factory(_request):
        harness.events.append("factory")
        return harness.collaborators

    def normalize_and_hash(email, source_ip):
        harness.events.append("normalize_hash")
        return original_normalize(email, source_ip)

    monkeypatch.setattr(
        server,
        "_create_newsletter_preferences_request_link_collaborators",
        factory,
    )
    monkeypatch.setattr(
        server,
        "_normalize_and_hash_newsletter_request",
        normalize_and_hash,
    )
    response = TestClient(server.app).post(PATH, json={"email": EMAIL})
    return response, harness


def assert_generic_accepted(response):
    assert response.status_code == 202
    assert response.json() == {"success": True, "message": ACCEPTED}
    rendered = response.text.lower()
    for prohibited in (
        EMAIL.lower(),
        MANAGEMENT_ID,
        TOKEN,
        "active",
        "subscriber",
        "rate limit",
        "provider",
        "token_version",
    ):
        assert prohibited.lower() not in rendered


def test_readiness_gate_defaults_off():
    assert server.NEWSLETTER_REQUEST_LINKS_ENABLED is False


def test_disabled_gate_returns_exact_503_before_all_business_access(monkeypatch):
    factory_called = False

    def fail_factory(_request):
        nonlocal factory_called
        factory_called = True
        raise AssertionError("collaborators must not be created")

    database = FailOnAccess("database")
    email = FailOnAccess("email")
    monkeypatch.setattr(server, "db", database)
    monkeypatch.setattr(server, "email_service", email)
    monkeypatch.setattr(
        server,
        "_create_newsletter_preferences_request_link_collaborators",
        fail_factory,
    )

    response = TestClient(server.app).post(PATH, json={"email": EMAIL})

    assert response.status_code == 503
    assert response.json() == {"detail": UNAVAILABLE}
    assert factory_called is False
    assert database.touched is False
    assert email.touched is False


def test_active_subscriber_uses_preferences_purpose(monkeypatch):
    response, harness = call_route(
        monkeypatch,
        CollaboratorHarness(subscriber=active_subscriber()),
    )
    assert_generic_accepted(response)
    assert harness.issue_calls[0]["purpose"] == "preferences"
    assert harness.issue_calls[0]["expiry_profile"] == "website_preferences"
    assert "expires_at" not in harness.issue_calls[0]
    email_request = harness.email_calls[0]
    assert email_request["purpose"] == "preferences"
    assert email_request["recipient_email"] == NORMALIZED_EMAIL
    assert email_request["now"] == NOW


def test_inactive_subscriber_switches_internally_to_reactivate(monkeypatch):
    response, harness = call_route(
        monkeypatch,
        CollaboratorHarness(
            subscriber=active_subscriber(active=False),
        ),
    )
    assert_generic_accepted(response)
    assert harness.issue_calls[0]["purpose"] == "reactivate"
    assert harness.issue_calls[0]["expiry_profile"] == "reactivation"
    assert "expires_at" not in harness.issue_calls[0]
    assert harness.challenge_repository.created[0]["purpose"] == "reactivate"
    assert harness.email_calls[0]["purpose"] == "reactivate"


def test_email_is_normalized_and_lookup_projection_is_minimal(monkeypatch):
    response, harness = call_route(monkeypatch)
    assert_generic_accepted(response)
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


def test_ip_and_email_rate_limits_are_reserved_before_lookup(monkeypatch):
    response, harness = call_route(monkeypatch)
    assert_generic_accepted(response)
    calls = harness.rate_repository.calls
    assert [call["dimension"] for call in calls] == ["ip", "email"]
    assert all(call["operation"] == "preferences" for call in calls)
    assert calls[0]["subject_hash"] == hashlib.sha256(
        SOURCE_IP.encode()
    ).hexdigest()
    assert calls[1]["subject_hash"] == hashlib.sha256(
        NORMALIZED_EMAIL.encode()
    ).hexdigest()


def test_unknown_subscriber_returns_same_response_without_token_or_email(monkeypatch):
    response, harness = call_route(
        monkeypatch,
        CollaboratorHarness(subscriber=None),
    )
    assert_generic_accepted(response)
    assert harness.issue_calls == []
    assert harness.email_calls == []
    assert harness.challenge_repository.created == []


@pytest.mark.parametrize(
    "subscriber",
    [
        active_subscriber(newsletter_management_id=None),
        active_subscriber(newsletter_management_id="invalid"),
        active_subscriber(
            newsletter_management_id="{" + MANAGEMENT_ID + "}"
        ),
        active_subscriber(
            newsletter_management_id=MANAGEMENT_ID.upper()
        ),
        active_subscriber(newsletter_management_id=UUID_V1),
        active_subscriber(newsletter_token_version=None),
        active_subscriber(newsletter_token_version=0),
        active_subscriber(newsletter_token_version=-1),
        active_subscriber(newsletter_token_version=True),
        active_subscriber(newsletter_token_version="1"),
        active_subscriber(active=None),
        active_subscriber(active="true"),
        active_subscriber(active="false"),
        active_subscriber(active=1),
        active_subscriber(active=0),
        active_subscriber(active=[]),
        active_subscriber(active={}),
    ],
)
def test_invalid_management_fields_are_non_enumerating_and_do_no_work(
    monkeypatch,
    subscriber,
):
    response, harness = call_route(
        monkeypatch,
        CollaboratorHarness(subscriber=subscriber),
    )
    assert_generic_accepted(response)
    assert harness.issue_calls == []
    assert harness.email_calls == []
    assert harness.challenge_repository.created == []


@pytest.mark.parametrize("decisions", [[False], [True, False]])
def test_rate_limited_requests_return_same_response_without_lookup(
    monkeypatch,
    decisions,
):
    response, harness = call_route(
        monkeypatch,
        CollaboratorHarness(
            subscriber=active_subscriber(),
            rate_decisions=decisions,
        ),
    )
    assert_generic_accepted(response)
    assert harness.lookup_calls == []
    assert harness.issue_calls == []
    assert harness.email_calls == []


def test_repository_failure_returns_same_response_without_later_work(monkeypatch):
    response, harness = call_route(
        monkeypatch,
        CollaboratorHarness(
            subscriber=active_subscriber(),
            rate_error=RuntimeError("private storage details"),
        ),
    )
    assert_generic_accepted(response)
    assert harness.lookup_calls == []
    assert harness.issue_calls == []
    assert harness.email_calls == []


def test_subscriber_lookup_failure_is_non_enumerating(monkeypatch):
    response, harness = call_route(
        monkeypatch,
        CollaboratorHarness(
            lookup_error=RuntimeError("private subscriber details"),
        ),
    )
    assert_generic_accepted(response)
    assert harness.issue_calls == []
    assert harness.email_calls == []


@pytest.mark.parametrize(
    ("token_result", "token_error"),
    [
        (None, None),
        (TOKEN, RuntimeError(f"private token failure {TOKEN}")),
    ],
)
def test_token_issuance_failure_is_non_enumerating_and_stops_work(
    monkeypatch,
    token_result,
    token_error,
):
    response, harness = call_route(
        monkeypatch,
        CollaboratorHarness(
            subscriber=active_subscriber(),
            token_result=token_result,
            token_error=token_error,
        ),
    )
    assert_generic_accepted(response)
    assert len(harness.issue_calls) == 1
    assert harness.challenge_repository.created == []
    assert harness.email_calls == []
    assert TOKEN not in response.text


def test_enabled_gate_with_unavailable_factory_is_non_enumerating(monkeypatch):
    monkeypatch.setattr(server, "NEWSLETTER_REQUEST_LINKS_ENABLED", True)
    normalize_called = False

    def unavailable_factory(_request):
        raise RuntimeError("private collaborator details")

    def fail_normalize(_email, _source_ip):
        nonlocal normalize_called
        normalize_called = True
        raise AssertionError("normalization must not start")

    monkeypatch.setattr(
        server,
        "_create_newsletter_preferences_request_link_collaborators",
        unavailable_factory,
    )
    monkeypatch.setattr(
        server,
        "_normalize_and_hash_newsletter_request",
        fail_normalize,
    )
    response = TestClient(server.app).post(PATH, json={"email": EMAIL})

    assert_generic_accepted(response)
    assert normalize_called is False


def test_challenge_creation_failure_returns_same_response_without_email(monkeypatch):
    response, harness = call_route(
        monkeypatch,
        CollaboratorHarness(
            subscriber=active_subscriber(),
            challenge_succeeds=False,
        ),
    )
    assert_generic_accepted(response)
    assert len(harness.issue_calls) == 1
    assert len(harness.challenge_repository.created) == 1
    assert harness.email_calls == []


def test_email_helper_rejection_marks_challenge_failed(monkeypatch):
    response, harness = call_route(
        monkeypatch,
        CollaboratorHarness(
            subscriber=active_subscriber(),
            email_accepted=False,
        ),
    )
    assert_generic_accepted(response)
    expected_hash = hashlib.sha256(TOKEN.encode()).hexdigest()
    assert harness.challenge_repository.failed == [expected_hash]
    assert harness.challenge_repository.delivered == []


def test_email_helper_exception_marks_challenge_failed_without_leak(monkeypatch):
    response, harness = call_route(
        monkeypatch,
        CollaboratorHarness(
            subscriber=active_subscriber(),
            email_error=RuntimeError(f"{EMAIL} {TOKEN}"),
        ),
    )
    assert_generic_accepted(response)
    assert len(harness.challenge_repository.failed) == 1
    assert harness.challenge_repository.delivered == []


def test_accepted_email_marks_challenge_delivered(monkeypatch):
    response, harness = call_route(monkeypatch)
    assert_generic_accepted(response)
    expected_hash = hashlib.sha256(TOKEN.encode()).hexdigest()
    assert harness.challenge_repository.delivered == [expected_hash]
    assert harness.challenge_repository.failed == []


def test_delivered_transition_failure_does_not_retry_or_assume_delivery(monkeypatch):
    response, harness = call_route(
        monkeypatch,
        CollaboratorHarness(
            subscriber=active_subscriber(),
            delivered_error=RuntimeError("private delivery transition"),
        ),
    )
    assert_generic_accepted(response)
    assert len(harness.issue_calls) == 1
    assert len(harness.challenge_repository.created) == 1
    assert len(harness.email_calls) == 1
    assert len(harness.challenge_repository.delivered) == 1
    assert harness.challenge_repository.delivered_confirmed == []
    assert harness.challenge_repository.failed == []


@pytest.mark.parametrize(
    ("email_accepted", "email_error"),
    [
        (False, None),
        (True, RuntimeError("private transport error")),
    ],
)
def test_failed_transition_failure_does_not_retry_or_leak(
    monkeypatch,
    email_accepted,
    email_error,
):
    response, harness = call_route(
        monkeypatch,
        CollaboratorHarness(
            subscriber=active_subscriber(),
            email_accepted=email_accepted,
            email_error=email_error,
            failed_error=RuntimeError("private failed transition"),
        ),
    )
    assert_generic_accepted(response)
    assert len(harness.issue_calls) == 1
    assert len(harness.challenge_repository.created) == 1
    assert len(harness.email_calls) == 1
    assert len(harness.challenge_repository.failed) == 1
    assert harness.challenge_repository.failed_confirmed == []
    assert harness.challenge_repository.delivered == []


def test_invalid_email_is_rejected_before_orchestration(monkeypatch):
    factory_called = False

    def factory(_request):
        nonlocal factory_called
        factory_called = True
        raise AssertionError("orchestration must not start")

    monkeypatch.setattr(server, "NEWSLETTER_REQUEST_LINKS_ENABLED", True)
    monkeypatch.setattr(
        server,
        "_create_newsletter_preferences_request_link_collaborators",
        factory,
    )
    response = TestClient(server.app).post(PATH, json={"email": "invalid"})
    assert response.status_code == 422
    assert factory_called is False


def test_successful_orchestration_order_is_exact(monkeypatch):
    harness = CollaboratorHarness(subscriber=active_subscriber())
    response, harness = call_route(monkeypatch, harness)
    assert_generic_accepted(response)
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


def test_rejected_delivery_order_is_exact(monkeypatch):
    harness = CollaboratorHarness(
        subscriber=active_subscriber(),
        email_accepted=False,
    )
    response, harness = call_route(monkeypatch, harness)
    assert_generic_accepted(response)
    assert harness.events == [
        "factory",
        "normalize_hash",
        "ip_limit",
        "email_limit",
        "subscriber_lookup",
        "issue_token",
        "create_pending",
        "send_email",
        "mark_failed",
    ]
    assert len(harness.email_calls) == 1
    assert harness.challenge_repository.delivered == []


@pytest.mark.parametrize(
    "reason",
    ["cooldown", "hourly_limit", "daily_limit"],
)
def test_distinct_email_limiter_denials_are_non_enumerating(monkeypatch, reason):
    denied = SimpleNamespace(allowed=False, reason=reason)
    response, harness = call_route(
        monkeypatch,
        CollaboratorHarness(
            subscriber=active_subscriber(),
            rate_decisions=[True, denied],
        ),
    )
    assert_generic_accepted(response)
    assert [call["dimension"] for call in harness.rate_repository.calls] == [
        "ip",
        "email",
    ]
    assert harness.lookup_calls == []
    assert harness.issue_calls == []
    assert harness.challenge_repository.created == []
    assert harness.email_calls == []
    assert reason not in response.text


def test_limiter_storage_error_is_non_enumerating(monkeypatch):
    response, harness = call_route(
        monkeypatch,
        CollaboratorHarness(
            subscriber=active_subscriber(),
            rate_error=RuntimeError("private storage failure"),
        ),
    )
    assert_generic_accepted(response)
    assert len(harness.rate_repository.calls) == 1
    assert harness.lookup_calls == []
    assert harness.issue_calls == []
    assert harness.challenge_repository.created == []
    assert harness.email_calls == []


def test_token_and_challenge_use_only_validated_management_fields(monkeypatch):
    response, harness = call_route(monkeypatch)
    assert_generic_accepted(response)
    issue = harness.issue_calls[0]
    assert issue["subscriber_management_id"] == MANAGEMENT_ID
    assert issue["token_version"] == 1
    assert issue["now"] == NOW
    assert issue["expiry_profile"] == "website_preferences"
    assert "expires_at" not in issue
    challenge = harness.challenge_repository.created[0]
    assert challenge["subscriber_management_id"] == MANAGEMENT_ID
    assert challenge["issued_at"] == NOW
    assert challenge["expires_at"] == NOW.replace(minute=30)
    assert challenge["token_hash"] == hashlib.sha256(TOKEN.encode()).hexdigest()


def test_route_is_registered_exactly_once_and_keeps_existing_endpoint():
    routes = [
        route
        for route in server.app.routes
        if getattr(route, "path", None) == PATH
        and "POST" in getattr(route, "methods", set())
    ]
    assert len(routes) == 1
    assert routes[0].endpoint is server.request_secure_newsletter_preferences_link


def test_stage_4e5_reactivation_request_link_is_non_enumerating(monkeypatch):
    monkeypatch.setattr(server, "NEWSLETTER_REQUEST_LINKS_ENABLED", True)
    response = TestClient(server.app).post(
        "/api/newsletter/reactivate/request-link",
        json={"email": EMAIL},
    )
    assert_generic_accepted(response)


ROUTE_CONTRACTS = (
    (
        "POST",
        "/api/newsletter/preferences/verify",
        "verify_secure_newsletter_preferences",
        "NewsletterTokenRequest",
        "NewsletterSecurePreferencesResponse",
    ),
    (
        "PUT",
        "/api/newsletter/preferences/secure",
        "update_secure_newsletter_preferences",
        "SecureNewsletterPreferencesUpdateRequest",
        "NewsletterGenericResponse",
    ),
    (
        "POST",
        "/api/newsletter/unsubscribe/confirm",
        "confirm_secure_newsletter_unsubscribe",
        "NewsletterTokenRequest",
        "NewsletterGenericResponse",
    ),
    (
        "POST",
        "/api/newsletter/unsubscribe/one-click",
        "one_click_secure_newsletter_unsubscribe",
        None,
        "NewsletterGenericResponse",
    ),
    (
        "POST",
        "/api/newsletter/reactivate/confirm",
        "confirm_secure_newsletter_reactivation",
        "NewsletterReactivationConfirmRequest",
        "NewsletterGenericResponse",
    ),
    (
        "POST",
        "/api/newsletter/unsubscribe/request-link",
        "request_secure_newsletter_unsubscribe_link",
        "NewsletterSecureLinkRequest",
        "NewsletterGenericResponse",
    ),
    (
        "POST",
        "/api/newsletter/reactivate/request-link",
        "request_secure_newsletter_reactivation_link",
        "NewsletterSecureLinkRequest",
        "NewsletterGenericResponse",
    ),
    (
        "POST",
        "/api/subscribe",
        "subscribe_newsletter",
        "SubscribeRequest",
        "SubscribeResponse",
    ),
    (
        "POST",
        "/api/newsletter/subscribe",
        "subscribe_newsletter",
        "SubscribeRequest",
        "SubscribeResponse",
    ),
    (
        "GET",
        "/api/newsletter/preferences/{email}",
        "get_newsletter_preferences",
        None,
        None,
    ),
    (
        "PUT",
        "/api/newsletter/preferences",
        "update_newsletter_preferences",
        "UpdatePreferencesRequest",
        None,
    ),
    (
        "POST",
        "/api/newsletter/email-preferences",
        "update_email_preferences",
        "PreferencesUpdateRequest",
        None,
    ),
    (
        "PUT",
        "/api/newsletter/email-preferences",
        "update_email_preferences",
        "UpdateEmailPreferencesRequest",
        None,
    ),
    (
        "GET",
        "/api/newsletter/email-preferences/{email}",
        "get_email_preferences",
        None,
        None,
    ),
    (
        "POST",
        "/api/newsletter/unsubscribe",
        "unsubscribe_newsletter",
        "UnsubscribeRequest",
        None,
    ),
)


def _schema_name(schema):
    reference = schema.get("$ref") if isinstance(schema, dict) else None
    return reference.rsplit("/", 1)[-1] if reference else None


@pytest.mark.parametrize(
    ("method", "path", "endpoint_name", "request_model", "response_model"),
    ROUTE_CONTRACTS,
)
def test_existing_route_contracts_are_exact(
    method,
    path,
    endpoint_name,
    request_model,
    response_model,
):
    routes = [
        route
        for route in server.app.routes
        if getattr(route, "path", None) == path
        and method in getattr(route, "methods", set())
    ]
    assert len(routes) == 1
    route = routes[0]
    assert route.endpoint.__name__ == endpoint_name
    assert route.dependant.dependencies == []

    operation = server.app.openapi()["paths"][path][method.lower()]
    request_schema = (
        operation.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
    )
    response_schema = (
        operation["responses"]
        .get("200", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
    )
    assert _schema_name(request_schema) == request_model
    assert _schema_name(response_schema) == response_model


def test_no_secret_provider_frontend_or_production_dependency_is_used():
    route_source = Path(server.__file__).read_text()
    orchestration = route_source[
        route_source.index("async def _run_newsletter_preferences_request_link"):
        route_source.index("def _create_secure_newsletter_token_service")
    ]
    assert "NEWSLETTER_LINK_SECRET" not in orchestration
    assert "email_service" not in orchestration
    assert "newsletter_token_service_from_environment" not in orchestration
    assert "db." not in orchestration
    assert os.environ.get("NEWSLETTER_LINK_SECRET") is None
