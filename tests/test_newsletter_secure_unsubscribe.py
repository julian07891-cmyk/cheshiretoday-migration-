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


TOKEN = "offline-secure-unsubscribe-token"
MANAGEMENT_ID = "ee764040-6937-42c1-9237-437a922f5598"
TOKEN_VERSION = 4
CONFIRM_PATH = "/api/newsletter/unsubscribe/confirm"
ONE_CLICK_PATH = "/api/newsletter/unsubscribe/one-click"
SUCCESS_BODY = {
    "success": True,
    "message": "Your unsubscribe request has been processed.",
}
GENERIC_503 = "Secure newsletter management is not yet available."
GENERIC_401 = "This newsletter management link is invalid or has expired."
GENERIC_403 = "This newsletter management link cannot be used for this action."
CONFLICT_409 = "Your unsubscribe request could not be processed. Please try again."
INVALID_FORM_400 = "The one-click unsubscribe request is invalid."


def _subscriber(**overrides):
    value = {
        "newsletter_management_id": MANAGEMENT_ID,
        "newsletter_token_version": TOKEN_VERSION,
        "active": True,
        "daily_brief": True,
        "weekly_roundup": True,
        "breaking_news": True,
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
        find_results=None,
        matched_count=1,
        find_error=None,
        update_error=None,
    ):
        self.find_results = [
            deepcopy(item)
            for item in (find_results if find_results is not None else [_subscriber()])
        ]
        self.matched_count = matched_count
        self.find_error = find_error
        self.update_error = update_error
        self.find_calls = []
        self.update_calls = []

    async def find_one(self, query, projection):
        self.find_calls.append((deepcopy(query), deepcopy(projection)))
        if self.find_error:
            raise self.find_error
        if not self.find_results:
            return None
        if len(self.find_results) == 1:
            return deepcopy(self.find_results[0])
        return deepcopy(self.find_results.pop(0))

    async def update_one(self, query, update):
        self.update_calls.append((deepcopy(query), deepcopy(update)))
        if self.update_error:
            raise self.update_error
        return SimpleNamespace(matched_count=self.matched_count)

    def __getattr__(self, name):
        raise AssertionError(f"unexpected subscriber operation: {name}")


def _install(
    monkeypatch,
    *,
    token_error=None,
    find_results=None,
    matched_count=1,
    find_error=None,
    update_error=None,
):
    token_service = FakeTokenService(error=token_error)
    subscribers = FakeSubscribers(
        find_results=find_results,
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


def _confirm(client):
    return client.post(CONFIRM_PATH, json={"token": TOKEN})


def _one_click(client, *, token=TOKEN, data=None, files=None, content=None, headers=None):
    suffix = "" if token is None else f"?token={token}"
    return client.post(
        ONE_CLICK_PATH + suffix,
        data=data,
        files=files,
        content=content,
        headers=headers,
    )


@pytest.mark.parametrize("path", (CONFIRM_PATH, ONE_CLICK_PATH))
@pytest.mark.parametrize(
    ("configuration", "secret_value"),
    (
        ("missing", None),
        ("weak", "too-short"),
    ),
)
def test_missing_and_weak_secrets_return_503_before_lookup(
    monkeypatch,
    path,
    configuration,
    secret_value,
):
    subscribers = FakeSubscribers()
    if configuration == "missing":
        monkeypatch.delenv("NEWSLETTER_LINK_SECRET", raising=False)
    else:
        monkeypatch.setenv("NEWSLETTER_LINK_SECRET", secret_value)
    monkeypatch.setattr(server, "db", SimpleNamespace(subscribers=subscribers))
    client = TestClient(server.app)

    response = (
        client.post(path, json={"token": TOKEN})
        if path == CONFIRM_PATH
        else _one_click(client, data={"List-Unsubscribe": "One-Click"})
    )

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert subscribers.find_calls == []
    assert subscribers.update_calls == []
    assert TOKEN not in response.text
    if secret_value:
        assert secret_value not in response.text


def test_application_startup_does_not_require_newsletter_secret():
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
def test_token_failures_are_safe_and_stop_before_lookup(
    monkeypatch,
    error,
    status,
    detail,
):
    client, token_service, subscribers = _install(
        monkeypatch,
        token_error=error,
    )

    response = _confirm(client)

    assert response.status_code == status
    assert response.json() == {"detail": detail}
    assert token_service.calls == [(TOKEN, server.UNSUBSCRIBE_PURPOSE)]
    assert subscribers.find_calls == []
    assert subscribers.update_calls == []
    for private_value in (TOKEN, MANAGEMENT_ID, "private payload", "email"):
        assert private_value not in response.text


@pytest.mark.parametrize(
    "find_results",
    (
        [None],
        [_subscriber(newsletter_token_version=0)],
        [_subscriber(newsletter_token_version=True)],
        [_subscriber(newsletter_token_version="4")],
        [_subscriber(newsletter_token_version=TOKEN_VERSION + 1)],
    ),
)
def test_missing_subscriber_or_invalid_version_returns_generic_401(
    monkeypatch,
    find_results,
):
    client, _, subscribers = _install(
        monkeypatch,
        find_results=find_results,
    )

    response = _confirm(client)

    assert response.status_code == 401
    assert response.json() == {"detail": GENERIC_401}
    assert subscribers.update_calls == []


def test_human_confirmation_soft_unsubscribes_only_approved_fields(monkeypatch):
    client, token_service, subscribers = _install(monkeypatch)

    response = _confirm(client)

    assert response.status_code == 200
    assert response.json() == SUCCESS_BODY
    assert token_service.calls == [(TOKEN, server.UNSUBSCRIBE_PURPOSE)]
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
        "active": True,
    }
    assert set(update) == {"$set"}
    assert set(update["$set"]) == {
        "active",
        "daily_brief",
        "weekly_roundup",
        "breaking_news",
        "unsubscribed_at",
        "unsubscribe_method",
    }
    assert update["$set"]["active"] is False
    assert update["$set"]["daily_brief"] is False
    assert update["$set"]["weekly_roundup"] is False
    assert update["$set"]["breaking_news"] is False
    assert update["$set"]["unsubscribe_method"] == "secure_token"
    assert "newsletter_token_version" not in update["$set"]


def test_already_inactive_is_idempotent_without_write(monkeypatch):
    client, _, subscribers = _install(
        monkeypatch,
        find_results=[_subscriber(active=False)],
    )

    first = _confirm(client)
    second = _confirm(client)

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json() == SUCCESS_BODY
    assert subscribers.update_calls == []


@pytest.mark.parametrize(
    "malformed_active",
    (
        pytest.param("missing", id="missing"),
        pytest.param(None, id="null"),
        pytest.param("false", id="string"),
        pytest.param(0, id="integer"),
        pytest.param([], id="other"),
    ),
)
def test_malformed_initial_active_state_fails_safely(
    monkeypatch,
    malformed_active,
):
    subscriber = _subscriber()
    if malformed_active == "missing":
        subscriber.pop("active")
    else:
        subscriber["active"] = malformed_active
    client, _, subscribers = _install(
        monkeypatch,
        find_results=[subscriber],
    )

    response = _confirm(client)

    assert response.status_code == 409
    assert response.json() == {"detail": CONFLICT_409}
    assert subscribers.update_calls == []
    for private_value in (TOKEN, MANAGEMENT_ID, "private@example.com"):
        assert private_value not in response.text


@pytest.mark.parametrize(
    "malformed_active",
    (
        pytest.param("missing", id="missing"),
        pytest.param(None, id="null"),
        pytest.param("false", id="string"),
        pytest.param(0, id="integer"),
        pytest.param({}, id="other"),
    ),
)
def test_malformed_active_state_after_failed_update_is_not_idempotent(
    monkeypatch,
    malformed_active,
):
    current = _subscriber()
    if malformed_active == "missing":
        current.pop("active")
    else:
        current["active"] = malformed_active
    client, _, subscribers = _install(
        monkeypatch,
        find_results=[_subscriber(active=True), current],
        matched_count=0,
    )

    response = _confirm(client)

    assert response.status_code == 409
    assert response.json() == {"detail": CONFLICT_409}
    assert len(subscribers.update_calls) == 1
    for private_value in (TOKEN, MANAGEMENT_ID, "private@example.com"):
        assert private_value not in response.text


def test_concurrent_idempotent_unsubscribe_returns_success(monkeypatch):
    client, _, subscribers = _install(
        monkeypatch,
        find_results=[_subscriber(active=True), _subscriber(active=False)],
        matched_count=0,
    )

    response = _confirm(client)

    assert response.status_code == 200
    assert response.json() == SUCCESS_BODY
    assert len(subscribers.update_calls) == 1
    assert len(subscribers.find_calls) == 2


def test_true_conditional_conflict_returns_409(monkeypatch):
    client, _, subscribers = _install(
        monkeypatch,
        find_results=[
            _subscriber(active=True),
            _subscriber(active=True, newsletter_token_version=TOKEN_VERSION + 1),
        ],
        matched_count=0,
    )

    response = _confirm(client)

    assert response.status_code == 409
    assert response.json() == {"detail": CONFLICT_409}
    assert len(subscribers.update_calls) == 1


@pytest.mark.parametrize("operation", ("find", "update"))
def test_database_failure_returns_generic_503(monkeypatch, operation):
    client, _, subscribers = _install(
        monkeypatch,
        find_error=RuntimeError("private database detail") if operation == "find" else None,
        update_error=RuntimeError("private database detail") if operation == "update" else None,
    )

    response = _confirm(client)

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert "private database detail" not in response.text
    if operation == "find":
        assert subscribers.update_calls == []


@pytest.mark.parametrize(
    "request_kwargs",
    (
        {"data": {"List-Unsubscribe": "One-Click"}},
        {"files": {"List-Unsubscribe": (None, "One-Click")}},
    ),
)
def test_rfc_one_click_accepts_exact_form_and_multipart(monkeypatch, request_kwargs):
    client, token_service, subscribers = _install(monkeypatch)

    response = _one_click(client, **request_kwargs)

    assert response.status_code == 200
    assert response.json() == SUCCESS_BODY
    assert response.history == []
    assert "set-cookie" not in response.headers
    assert token_service.calls == [(TOKEN, server.UNSUBSCRIBE_PURPOSE)]
    assert len(subscribers.update_calls) == 1


@pytest.mark.parametrize(
    "request_kwargs",
    (
        {"token": None, "data": {"List-Unsubscribe": "One-Click"}},
        {"token": "   ", "data": {"List-Unsubscribe": "One-Click"}},
        {"data": {}},
        {"data": {"List-Unsubscribe": "one-click"}},
        {"data": {"List-Unsubscribe": "One-Click", "extra": "value"}},
        {
            "content": '{"List-Unsubscribe":"One-Click"}',
            "headers": {"content-type": "application/json"},
        },
        {
            "content": "not-a-form",
            "headers": {"content-type": "text/plain"},
        },
    ),
)
def test_rfc_one_click_rejects_missing_token_or_malformed_form(
    monkeypatch,
    request_kwargs,
):
    client, token_service, subscribers = _install(monkeypatch)

    response = _one_click(client, **request_kwargs)

    assert response.status_code == 400
    assert response.json() == {"detail": INVALID_FORM_400}
    assert token_service.calls == []
    assert subscribers.find_calls == []
    assert subscribers.update_calls == []


def test_get_one_click_cannot_mutate(monkeypatch):
    client, token_service, subscribers = _install(monkeypatch)

    response = client.get(f"{ONE_CLICK_PATH}?token={TOKEN}")

    assert response.status_code in (404, 405)
    assert token_service.calls == []
    assert subscribers.find_calls == []
    assert subscribers.update_calls == []


def test_one_click_does_not_depend_on_authorization_or_cookies(monkeypatch):
    client, _, _ = _install(monkeypatch)

    response = client.post(
        f"{ONE_CLICK_PATH}?token={TOKEN}",
        data={"List-Unsubscribe": "One-Click"},
    )

    assert response.status_code == 200
    assert response.json() == SUCCESS_BODY


def test_four_remaining_secure_routes_stay_dormant(monkeypatch):
    class FailOnAccess:
        def __getattr__(self, name):
            raise AssertionError(f"unexpected access: {name}")

    monkeypatch.setattr(server, "db", FailOnAccess())
    monkeypatch.setattr(server, "email_service", FailOnAccess())
    client = TestClient(server.app)
    routes = (
        ("POST", "/api/newsletter/preferences/request-link", {"email": "reader@example.com"}),
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

    for method, path, payload in routes:
        response = client.request(method, path, json=payload)
        assert response.status_code == 503
        assert response.json() == {"detail": GENERIC_503}


def test_stage_4b_and_legacy_routes_remain_singly_registered():
    expected = (
        ("POST", "/api/newsletter/preferences/verify"),
        ("PUT", "/api/newsletter/preferences/secure"),
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
