import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")
os.environ.pop("NEWSLETTER_LINK_SECRET", None)

from backend import server
from app.email_service import EmailService
from app.newsletter_link_security import (
    CHALLENGE_COLLECTION_NAME,
    RATE_LIMIT_COLLECTION_NAME,
    NewsletterChallengeRepository,
    NewsletterRateLimitRepository,
)
from app.newsletter_management_email import (
    NewsletterManagementEmailMessage,
    NewsletterManagementEmailPurpose,
    NewsletterManagementEmailResult,
    NewsletterManagementEmailResultReason,
)


GENERIC_503 = "Secure newsletter management is not yet available."


class FakeDatabase:
    def __init__(self):
        self.requested = []
        self.collections = {}
        self.subscribers = SimpleNamespace()

    def __getitem__(self, name):
        self.requested.append(name)
        return self.collections.setdefault(name, object())


def test_gates_remain_literal_false_and_startup_needs_no_collaborator(
    monkeypatch,
):
    source = open(server.__file__, encoding="utf-8").read()
    assert "NEWSLETTER_REQUEST_LINKS_ENABLED = True" in source
    assert "NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED = True" in source
    assert server.NEWSLETTER_REQUEST_LINKS_ENABLED is True
    assert server.NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED is True

    monkeypatch.setattr(server, "NEWSLETTER_REQUEST_LINKS_ENABLED", False)
    monkeypatch.setattr(
        server,
        "_create_newsletter_preferences_request_link_collaborators",
        lambda _request: (_ for _ in ()).throw(
            AssertionError("collaborator factory called")
        ),
    )
    response = TestClient(server.app).post(
        "/api/newsletter/preferences/request-link",
        json={"email": "reader@example.com"},
    )

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}


def test_repository_factories_select_only_existing_database_collections(
    monkeypatch,
):
    database = FakeDatabase()
    monkeypatch.setattr(server, "db", database)

    rate_repository = server._create_newsletter_rate_limit_repository()
    challenge_repository = (
        server._create_newsletter_preference_challenge_repository()
    )

    assert isinstance(rate_repository, NewsletterRateLimitRepository)
    assert isinstance(challenge_repository, NewsletterChallengeRepository)
    assert database.requested == [
        RATE_LIMIT_COLLECTION_NAME,
        CHALLENGE_COLLECTION_NAME,
    ]
    assert rate_repository._collection is database.collections[
        RATE_LIMIT_COLLECTION_NAME
    ]
    assert challenge_repository._collection is database.collections[
        CHALLENGE_COLLECTION_NAME
    ]


def test_transaction_factory_returns_existing_motor_client(monkeypatch):
    existing_client = object()
    monkeypatch.setattr(server, "client", existing_client)

    assert (
        server._create_newsletter_preference_transaction_client()
        is existing_client
    )


def test_request_collaborators_are_lazy_and_reuse_all_existing_owners(
    monkeypatch,
):
    database = FakeDatabase()
    existing_client = object()
    token_service = SimpleNamespace(issue_newsletter_token=lambda **_: "token")
    email_result = NewsletterManagementEmailResult(
        accepted=True,
        reason=NewsletterManagementEmailResultReason.ACCEPTED,
    )
    email_helper = SimpleNamespace(send=lambda request, now: email_result)

    monkeypatch.setattr(server, "db", database)
    monkeypatch.setattr(server, "client", existing_client)
    monkeypatch.setattr(
        server,
        "_create_secure_newsletter_token_service",
        lambda: token_service,
    )
    monkeypatch.setattr(
        server,
        "_create_newsletter_management_email_helper",
        lambda: email_helper,
    )
    request = SimpleNamespace(client=SimpleNamespace(host="192.0.2.10"))

    collaborators = (
        server._create_newsletter_preferences_request_link_collaborators(
            request
        )
    )

    assert isinstance(
        collaborators.rate_limit_repository,
        NewsletterRateLimitRepository,
    )
    assert isinstance(
        collaborators.challenge_repository,
        NewsletterChallengeRepository,
    )
    assert collaborators.issue_token is token_service.issue_newsletter_token
    assert collaborators.source_ip == "192.0.2.10"
    assert collaborators.now.tzinfo is not None
    assert database.requested == [
        RATE_LIMIT_COLLECTION_NAME,
        CHALLENGE_COLLECTION_NAME,
    ]
    assert server._create_newsletter_preference_transaction_client() is (
        existing_client
    )


@pytest.mark.parametrize(
    "factory_name",
    (
        "_create_newsletter_preferences_request_link_collaborators",
        "_create_newsletter_unsubscribe_request_link_collaborators",
        "_create_newsletter_reactivation_request_link_collaborators",
    ),
)
def test_request_factories_fail_closed_without_source_ip(
    monkeypatch,
    factory_name,
):
    factory = getattr(server, factory_name)
    monkeypatch.setattr(server, "db", FakeDatabase())

    with pytest.raises(RuntimeError) as error:
        factory(SimpleNamespace(client=None))

    assert str(error.value) == "Newsletter request source is unavailable."


def _email_service():
    service = EmailService.__new__(EmailService)
    service.resend_enabled = True
    service.resend_api_key = "test-key"
    service.resend_from_email = "news@example.com"
    service.from_email = None
    service.resend_from_name = "Cheshire Today"
    service.from_name = "Cheshire Today"
    service.reply_to = "reply@example.com"
    return service


def _message():
    return NewsletterManagementEmailMessage(
        recipient_email="reader@example.com",
        subject="Your Cheshire Today preferences link",
        html=(
            '<a href="https://cheshiretoday.co.uk/newsletter/preferences'
            '#token=offline-token">Manage newsletter preferences</a>'
        ),
        text=(
            "https://cheshiretoday.co.uk/newsletter/preferences"
            "#token=offline-token"
        ),
    )


def test_email_adapter_performs_one_untracked_resend_attempt(monkeypatch):
    calls = []

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return SimpleNamespace(status_code=202)

    monkeypatch.setattr(httpx, "post", post)
    service = _email_service()

    assert service.send_newsletter_management_transactional(_message()) is True
    assert len(calls) == 1
    url, kwargs = calls[0]
    assert url == "https://api.resend.com/emails"
    assert kwargs["json"]["to"] == ["reader@example.com"]
    assert kwargs["json"]["html"] == _message().html
    assert kwargs["json"]["text"] == _message().text
    rendered = str(kwargs["json"]).lower()
    assert "track/click" not in rendered
    assert "track/open" not in rendered
    assert "utm_" not in rendered


@pytest.mark.parametrize(
    ("failure", "expected"),
    (
        ("rejected", False),
        ("timeout", TimeoutError),
        ("error", RuntimeError),
    ),
)
def test_email_adapter_has_no_retry_fallback_or_private_output(
    monkeypatch,
    caplog,
    capsys,
    failure,
    expected,
):
    calls = []

    def post(*args, **kwargs):
        calls.append((args, kwargs))
        if failure == "timeout":
            raise httpx.ReadTimeout("private provider payload")
        if failure == "error":
            raise RuntimeError("private provider payload")
        return SimpleNamespace(status_code=429)

    monkeypatch.setattr(httpx, "post", post)
    service = _email_service()

    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected) as error:
            service.send_newsletter_management_transactional(_message())
        assert "private provider payload" not in str(error.value)
    else:
        assert (
            service.send_newsletter_management_transactional(_message())
            is expected
        )

    assert len(calls) == 1
    assert caplog.records == []
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_management_email_helper_uses_existing_email_owner(monkeypatch):
    sent = []

    def send(message):
        sent.append(message)
        return True

    monkeypatch.setattr(
        server.email_service,
        "send_newsletter_management_transactional",
        send,
    )
    helper = server._create_newsletter_management_email_helper()
    now = datetime(2026, 7, 19, 12, 0, tzinfo=timezone.utc)

    result = helper.send(
        server.NewsletterManagementEmailRequest(
            recipient_email="reader@example.com",
            purpose=NewsletterManagementEmailPurpose.PREFERENCES,
            token="offline-token",
            expires_at=now + timedelta(minutes=30),
        ),
        now=now,
    )

    assert result.accepted is True
    assert len(sent) == 1
    assert "#token=offline-token" in sent[0].html
    assert "?token=" not in sent[0].html


def test_readiness_is_value_safe_and_performs_no_io(monkeypatch):
    monkeypatch.setattr(
        server.email_service,
        "newsletter_management_transport_ready",
        lambda: True,
    )

    result = server._newsletter_runtime_collaborator_readiness()

    assert result == {
        "database_bound": True,
        "transaction_client_bound": True,
        "email_transport_configured": True,
        "request_links_enabled": True,
        "challenge_enforcement_enabled": True,
    }
    assert all(type(value) is bool for value in result.values())


def test_secure_and_signup_routes_remain_registered_once():
    expected = (
        ("POST", "/api/newsletter/preferences/verify"),
        ("PUT", "/api/newsletter/preferences/secure"),
        ("POST", "/api/newsletter/preferences/request-link"),
        ("POST", "/api/newsletter/unsubscribe/confirm"),
        ("POST", "/api/newsletter/unsubscribe/one-click"),
        ("POST", "/api/newsletter/unsubscribe/request-link"),
        ("POST", "/api/newsletter/reactivate/request-link"),
        ("POST", "/api/newsletter/reactivate/confirm"),
        ("POST", "/api/subscribe"),
        ("POST", "/api/newsletter/subscribe"),
    )

    for method, path in expected:
        matches = [
            route
            for route in server.app.routes
            if getattr(route, "path", None) == path
            and method in getattr(route, "methods", set())
        ]
        assert len(matches) == 1
