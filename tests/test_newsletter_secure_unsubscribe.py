import os
import hashlib
from copy import deepcopy
from decimal import Decimal
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
TOKEN_HASH = hashlib.sha256(TOKEN.encode()).hexdigest()
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


class IntSubclass(int):
    pass


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

    async def find_one(self, query, projection, **kwargs):
        self.find_calls.append(
            (deepcopy(query), deepcopy(projection), dict(kwargs))
        )
        if self.find_error:
            raise self.find_error
        if not self.find_results:
            return None
        if len(self.find_results) == 1:
            return deepcopy(self.find_results[0])
        return deepcopy(self.find_results.pop(0))

    async def update_one(self, query, update, **kwargs):
        self.update_calls.append(
            (deepcopy(query), deepcopy(update), dict(kwargs))
        )
        if self.update_error:
            raise self.update_error
        return SimpleNamespace(matched_count=self.matched_count)

    def __getattr__(self, name):
        raise AssertionError(f"unexpected subscriber operation: {name}")


class FakeChallengeRepository:
    def __init__(self):
        self.consumed = False
        self.consume_calls = []
        self.successful_consumptions = 0

    async def consume(self, **kwargs):
        self.consume_calls.append(dict(kwargs))
        if self.consumed:
            return SimpleNamespace(
                succeeded=False,
                reason=server.ChallengeResultReason.NOT_ELIGIBLE,
            )
        self.consumed = True
        self.successful_consumptions += 1
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
    def __init__(self):
        self.transaction = FakeTransaction()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    def start_transaction(self):
        return self.transaction


class FakeTransactionClient:
    def __init__(self):
        self.sessions = []

    async def start_session(self):
        session = FakeSession()
        self.sessions.append(session)
        return session


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
    challenge_repository = FakeChallengeRepository()
    transaction_client = FakeTransactionClient()
    subscribers.challenge_repository = challenge_repository
    subscribers.transaction_client = transaction_client
    monkeypatch.setattr(
        server,
        "NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED",
        True,
    )
    monkeypatch.setattr(
        server,
        "newsletter_token_service_from_environment",
        lambda: token_service,
    )
    monkeypatch.setattr(
        server,
        "hash_newsletter_challenge_token",
        lambda token: hashlib.sha256(token.encode()).hexdigest(),
    )
    monkeypatch.setattr(
        server,
        "_create_newsletter_preference_challenge_repository",
        lambda: challenge_repository,
    )
    monkeypatch.setattr(
        server,
        "_create_newsletter_preference_transaction_client",
        lambda: transaction_client,
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


@pytest.mark.parametrize("path", (CONFIRM_PATH, ONE_CLICK_PATH))
def test_disabled_gate_stops_before_every_collaborator(monkeypatch, path):
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
    monkeypatch.setattr(
        server,
        "_create_newsletter_preference_transaction_client",
        lambda: (_ for _ in ()).throw(AssertionError("session called")),
    )
    monkeypatch.setattr(server, "db", FailOnAccess())

    response = (
        TestClient(server.app).post(path, json={"token": TOKEN})
        if path == CONFIRM_PATH
        else TestClient(server.app).post(
            f"{path}?token={TOKEN}",
            data={"List-Unsubscribe": "One-Click"},
        )
    )

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}


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
    assert len(subscribers.find_calls) == 2
    for query, projection, _options in subscribers.find_calls:
        assert query == {"newsletter_management_id": MANAGEMENT_ID}
        assert projection == {
            "_id": 0,
            "newsletter_management_id": 1,
            "newsletter_token_version": 1,
            "active": 1,
        }
    assert subscribers.find_calls[0][2] == {}
    session = subscribers.find_calls[1][2]["session"]
    query, update, options = subscribers.update_calls[0]
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
    assert options == {"session": session}


def test_human_inactive_challenge_is_consumed_once_then_replay_fails(monkeypatch):
    client, _, subscribers = _install(
        monkeypatch,
        find_results=[_subscriber(active=False)],
    )

    first = _confirm(client)
    second = _confirm(client)

    assert first.status_code == 200
    assert first.json() == SUCCESS_BODY
    assert second.status_code == 401
    assert second.json() == {"detail": GENERIC_401}
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
    assert subscribers.update_calls == []
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
    assert subscribers.update_calls == []
    assert len(subscribers.find_calls) == 2


def test_in_transaction_version_change_returns_generic_401(monkeypatch):
    client, _, subscribers = _install(
        monkeypatch,
        find_results=[
            _subscriber(active=True),
            _subscriber(active=True, newsletter_token_version=TOKEN_VERSION + 1),
        ],
        matched_count=0,
    )

    response = _confirm(client)

    assert response.status_code == 401
    assert response.json() == {"detail": GENERIC_401}
    assert subscribers.update_calls == []


@pytest.mark.parametrize(
    "result",
    (
        SimpleNamespace(),
        SimpleNamespace(matched_count=None),
        SimpleNamespace(matched_count=True),
        SimpleNamespace(matched_count=False),
        SimpleNamespace(matched_count="1"),
        SimpleNamespace(matched_count=1.0),
        SimpleNamespace(matched_count=Decimal("1")),
        SimpleNamespace(matched_count=IntSubclass(1)),
        SimpleNamespace(matched_count=-1),
        SimpleNamespace(matched_count=2),
        SimpleNamespace(matched_count=object()),
    ),
)
def test_malformed_update_result_fails_closed(monkeypatch, result):
    client, _, subscribers = _install(monkeypatch)

    async def malformed_update(query, update, **kwargs):
        subscribers.update_calls.append(
            (deepcopy(query), deepcopy(update), dict(kwargs))
        )
        return result

    subscribers.update_one = malformed_update
    response = _confirm(client)

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert len(subscribers.update_calls) == 1
    for private_value in (TOKEN, TOKEN_HASH, MANAGEMENT_ID, "matched_count"):
        assert private_value not in response.text


def test_exact_zero_update_conflict_returns_409(monkeypatch):
    client, _, subscribers = _install(monkeypatch, matched_count=0)

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


def test_rfc_one_click_replay_is_successful_without_second_mutation(monkeypatch):
    client, _, subscribers = _install(
        monkeypatch,
        find_results=[
            _subscriber(active=True),
            _subscriber(active=True),
            _subscriber(active=False),
            _subscriber(active=False),
        ],
    )

    first = _one_click(
        client,
        data={"List-Unsubscribe": "One-Click"},
    )
    replay = _one_click(
        client,
        data={"List-Unsubscribe": "One-Click"},
    )

    assert first.status_code == replay.status_code == 200
    assert first.json() == replay.json() == SUCCESS_BODY
    assert len(subscribers.update_calls) == 1
    assert subscribers.challenge_repository.successful_consumptions == 1
    assert len(subscribers.transaction_client.sessions) == 2


def test_active_unsubscribe_uses_bound_challenge_and_same_session(monkeypatch):
    client, _, subscribers = _install(monkeypatch)

    response = _confirm(client)

    assert response.status_code == 200
    session = subscribers.transaction_client.sessions[0]
    consume = subscribers.challenge_repository.consume_calls[0]
    assert consume["token_hash"] == TOKEN_HASH
    assert consume["subscriber_management_id"] == MANAGEMENT_ID
    assert consume["expected_purpose"] == server.UNSUBSCRIBE_PURPOSE
    assert consume["session"] is session
    assert subscribers.find_calls[1][2] == {"session": session}
    assert subscribers.update_calls[0][2] == {"session": session}


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
            reason=server.ChallengeResultReason.ELIGIBLE,
        ),
        SimpleNamespace(succeeded=False, reason="malformed"),
        SimpleNamespace(),
    ),
)
def test_ineligible_challenge_states_are_generic_401(monkeypatch, result):
    client, _, subscribers = _install(monkeypatch)

    async def consume(**kwargs):
        subscribers.challenge_repository.consume_calls.append(dict(kwargs))
        return result

    subscribers.challenge_repository.consume = consume
    response = _confirm(client)

    assert response.status_code == 401
    assert response.json() == {"detail": GENERIC_401}
    assert subscribers.update_calls == []
    for private_value in (TOKEN, TOKEN_HASH, MANAGEMENT_ID):
        assert private_value not in response.text


def test_challenge_storage_failure_is_generic_503(monkeypatch):
    client, _, subscribers = _install(monkeypatch)

    async def consume(**kwargs):
        subscribers.challenge_repository.consume_calls.append(dict(kwargs))
        return SimpleNamespace(
            succeeded=False,
            reason=server.ChallengeResultReason.STORAGE_ERROR,
        )

    subscribers.challenge_repository.consume = consume
    response = _confirm(client)

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert subscribers.update_calls == []


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
