import os
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


PATH = "/api/newsletter/reactivate/confirm"
TOKEN = "offline-secure-reactivation-token"
TOKEN_HASH = "a" * 64
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


class IntSubclass(int):
    pass


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
    def __init__(self, order, error=None):
        self.order = order
        self.error = error
        self.calls = []

    def verify_newsletter_token(self, token, expected_purpose):
        self.calls.append((token, expected_purpose))
        self.order.append(("token",))
        if self.error:
            raise self.error
        return SimpleNamespace(
            subscriber_management_id=MANAGEMENT_ID,
            token_version=TOKEN_VERSION,
        )


class FakeState:
    def __init__(self, subscriber):
        self.subscriber = deepcopy(subscriber)
        self.challenge_consumed = False


class FakeSubscribers:
    def __init__(
        self,
        state,
        order,
        *,
        update_result=None,
        find_error=False,
        transaction_find_error=False,
        update_error=False,
        transaction_subscriber=None,
    ):
        self.state = state
        self.order = order
        self.update_result = update_result
        self.find_error = find_error
        self.transaction_find_error = transaction_find_error
        self.update_error = update_error
        self.transaction_subscriber = transaction_subscriber
        self.find_calls = []
        self.update_calls = []

    async def find_one(self, query, projection, **kwargs):
        call = (deepcopy(query), deepcopy(projection), dict(kwargs))
        self.find_calls.append(call)
        in_transaction = "session" in kwargs
        self.order.append(
            ("subscriber_transaction" if in_transaction else "subscriber_pre",)
        )
        if self.find_error and not in_transaction:
            raise RuntimeError("private database detail")
        if self.transaction_find_error and in_transaction:
            raise RuntimeError("private database detail")
        source = (
            self.transaction_subscriber
            if in_transaction and self.transaction_subscriber is not None
            else self.state.subscriber
        )
        if source is None:
            return None
        return {
            key: deepcopy(value)
            for key, value in source.items()
            if key != "_id" and projection.get(key) == 1
        }

    async def update_one(self, query, update, **kwargs):
        self.order.append(("subscriber_update",))
        self.update_calls.append(
            (deepcopy(query), deepcopy(update), dict(kwargs))
        )
        if self.update_error:
            raise RuntimeError("private database detail")
        if self.update_result is not None:
            return self.update_result
        matches = (
            self.state.subscriber is not None
            and all(
                self.state.subscriber.get(key) == value
                for key, value in query.items()
            )
        )
        matched_count = 1 if matches else 0
        if matched_count == 1:
            self.state.subscriber.update(deepcopy(update["$set"]))
        return SimpleNamespace(matched_count=matched_count)

    def __getattr__(self, name):
        raise AssertionError(f"unexpected subscriber operation: {name}")


class FakeChallengeRepository:
    def __init__(self, state, order, *, reason=None, error=False):
        self.state = state
        self.order = order
        self.reason = reason
        self.error = error
        self.consume_calls = []
        self.successful_consumptions = 0

    async def consume(self, **kwargs):
        self.order.append(("consume",))
        self.consume_calls.append(dict(kwargs))
        if self.error:
            raise RuntimeError("private challenge detail")
        if self.reason is not None:
            return SimpleNamespace(succeeded=False, reason=self.reason)
        if self.state.challenge_consumed:
            return SimpleNamespace(
                succeeded=False,
                reason=server.ChallengeResultReason.NOT_ELIGIBLE,
            )
        self.state.challenge_consumed = True
        self.successful_consumptions += 1
        return SimpleNamespace(
            succeeded=True,
            reason=server.ChallengeResultReason.CONSUMED,
        )


class FakeTransaction:
    def __init__(
        self,
        state,
        order,
        *,
        commit_error=False,
        indeterminate_commit=False,
        abort_error=False,
    ):
        self.state = state
        self.order = order
        self.commit_error = commit_error
        self.indeterminate_commit = indeterminate_commit
        self.abort_error = abort_error
        self.commit_attempts = 0

    async def __aenter__(self):
        self.order.append(("transaction_start",))
        self.subscriber_before = deepcopy(self.state.subscriber)
        self.challenge_before = self.state.challenge_consumed
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        if exc_type is not None or self.commit_error:
            self.state.subscriber = self.subscriber_before
            self.state.challenge_consumed = self.challenge_before
            self.order.append(("transaction_abort",))
        if exc_type is not None and self.abort_error:
            raise RuntimeError("private abort detail")
        if exc_type is None:
            self.commit_attempts += 1
        if exc_type is None and self.indeterminate_commit:
            self.order.append(("transaction_commit_indeterminate",))
            raise RuntimeError("private indeterminate detail")
        if exc_type is None and self.commit_error:
            raise RuntimeError("private commit detail")
        if exc_type is None:
            self.order.append(("transaction_commit",))
        return False


class FakeSession:
    def __init__(
        self,
        state,
        order,
        *,
        start_error=False,
        commit_error=False,
        indeterminate_commit=False,
        abort_error=False,
    ):
        self.state = state
        self.order = order
        self.start_error = start_error
        self.commit_error = commit_error
        self.indeterminate_commit = indeterminate_commit
        self.abort_error = abort_error
        self.transaction = None

    async def __aenter__(self):
        self.order.append(("session_enter",))
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        self.order.append(("session_exit",))
        return False

    def start_transaction(self):
        if self.start_error:
            raise RuntimeError("private transaction start detail")
        self.transaction = FakeTransaction(
            self.state,
            self.order,
            commit_error=self.commit_error,
            indeterminate_commit=self.indeterminate_commit,
            abort_error=self.abort_error,
        )
        return self.transaction


class FakeClient:
    def __init__(
        self,
        state,
        order,
        *,
        session_error=False,
        start_error=False,
        commit_error=False,
        indeterminate_commit=False,
        abort_error=False,
    ):
        self.state = state
        self.order = order
        self.session_error = session_error
        self.start_error = start_error
        self.commit_error = commit_error
        self.indeterminate_commit = indeterminate_commit
        self.abort_error = abort_error
        self.session = None
        self.start_session_calls = 0

    async def start_session(self):
        self.start_session_calls += 1
        self.order.append(("session_create",))
        if self.session_error:
            raise RuntimeError("private session detail")
        self.session = FakeSession(
            self.state,
            self.order,
            start_error=self.start_error,
            commit_error=self.commit_error,
            indeterminate_commit=self.indeterminate_commit,
            abort_error=self.abort_error,
        )
        return self.session


def _install(
    monkeypatch,
    *,
    subscriber=None,
    token_error=None,
    challenge_reason=None,
    challenge_error=False,
    update_result=None,
    find_error=False,
    transaction_find_error=False,
    update_error=False,
    transaction_subscriber=None,
    client_error=False,
    session_error=False,
    start_error=False,
    commit_error=False,
    indeterminate_commit=False,
    abort_error=False,
):
    order = []
    state = FakeState(_subscriber() if subscriber is None else subscriber)
    token_service = FakeTokenService(order, error=token_error)
    subscribers = FakeSubscribers(
        state,
        order,
        update_result=update_result,
        find_error=find_error,
        transaction_find_error=transaction_find_error,
        update_error=update_error,
        transaction_subscriber=transaction_subscriber,
    )
    challenge_repository = FakeChallengeRepository(
        state,
        order,
        reason=challenge_reason,
        error=challenge_error,
    )
    transaction_client = FakeClient(
        state,
        order,
        session_error=session_error,
        start_error=start_error,
        commit_error=commit_error,
        indeterminate_commit=indeterminate_commit,
        abort_error=abort_error,
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

    def client_factory():
        order.append(("client_factory",))
        if client_error:
            raise RuntimeError("private client detail")
        return transaction_client

    monkeypatch.setattr(
        server, "NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED", True
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
    monkeypatch.setattr(
        server,
        "_create_newsletter_preference_transaction_client",
        client_factory,
    )
    monkeypatch.setattr(server, "db", SimpleNamespace(subscribers=subscribers))
    return (
        TestClient(server.app),
        order,
        state,
        token_service,
        subscribers,
        challenge_repository,
        transaction_client,
    )


def _payload(**overrides):
    value = {
        "token": TOKEN,
        "daily_brief": True,
        "weekly_roundup": False,
        "breaking_news": False,
    }
    value.update(overrides)
    return value


def test_disabled_gate_precedes_every_collaborator(monkeypatch):
    class FailOnAccess:
        def __getattr__(self, name):
            raise AssertionError(f"unexpected access: {name}")

    monkeypatch.setattr(
        server, "NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED", False
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
        lambda: (_ for _ in ()).throw(AssertionError("client called")),
    )
    monkeypatch.setattr(server, "db", FailOnAccess())

    response = TestClient(server.app).post(PATH, json=_payload())

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
def test_token_errors_are_safe_and_stop_before_lookup(
    monkeypatch, error, status, detail
):
    client, _, _, token_service, subscribers, challenge, transaction_client = (
        _install(monkeypatch, token_error=error)
    )

    response = client.post(PATH, json=_payload())

    assert response.status_code == status
    assert response.json() == {"detail": detail}
    assert token_service.calls == [(TOKEN, server.REACTIVATE_PURPOSE)]
    assert subscribers.find_calls == []
    assert challenge.consume_calls == []
    assert transaction_client.start_session_calls == 0


@pytest.mark.parametrize(
    "subscriber",
    (
        None,
        _subscriber(newsletter_management_id="wrong"),
        _subscriber(newsletter_token_version=0),
        _subscriber(newsletter_token_version=True),
        _subscriber(newsletter_token_version="7"),
        _subscriber(newsletter_token_version=TOKEN_VERSION + 1),
    ),
)
def test_missing_subscriber_or_invalid_identity_returns_generic_401(
    monkeypatch, subscriber
):
    client, _, state, _, subscribers, challenge, transaction_client = _install(
        monkeypatch, subscriber=subscriber
    )
    if subscriber is None:
        state.subscriber = None

    response = client.post(PATH, json=_payload())

    assert response.status_code == 401
    assert response.json() == {"detail": GENERIC_401}
    assert subscribers.update_calls == []
    assert challenge.consume_calls == []
    assert transaction_client.start_session_calls == 0


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
def test_only_literal_false_is_eligible(monkeypatch, active_value):
    subscriber = _subscriber()
    if active_value == "missing":
        subscriber.pop("active")
    else:
        subscriber["active"] = active_value
    client, _, _, _, subscribers, challenge, transaction_client = _install(
        monkeypatch, subscriber=subscriber
    )

    response = client.post(PATH, json=_payload())

    assert response.status_code == 409
    assert response.json() == {"detail": CONFLICT_409}
    assert subscribers.update_calls == []
    assert challenge.consume_calls == []
    assert transaction_client.start_session_calls == 0


@pytest.mark.parametrize(
    ("daily_brief", "weekly_roundup", "breaking_news"),
    ((True, False, False), (False, False, False), (False, True, True)),
)
def test_successful_transaction_uses_same_session_and_exact_update(
    monkeypatch, daily_brief, weekly_roundup, breaking_news
):
    original = _subscriber()
    client, order, state, token_service, subscribers, challenge, tx_client = (
        _install(monkeypatch, subscriber=original)
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
    assert [step[0] for step in order] == [
        "token_factory",
        "token",
        "subscriber_pre",
        "hash",
        "challenge_factory",
        "client_factory",
        "session_create",
        "session_enter",
        "transaction_start",
        "subscriber_transaction",
        "consume",
        "subscriber_update",
        "transaction_commit",
        "session_exit",
    ]
    assert len(subscribers.find_calls) == 2
    session = tx_client.session
    assert subscribers.find_calls[0][2] == {}
    assert subscribers.find_calls[1][2] == {"session": session}
    consume = challenge.consume_calls[0]
    assert consume["token_hash"] == TOKEN_HASH
    assert consume["subscriber_management_id"] == MANAGEMENT_ID
    assert consume["expected_purpose"] == server.REACTIVATE_PURPOSE
    assert consume["session"] is session
    query, update, kwargs = subscribers.update_calls[0]
    assert kwargs == {"session": session}
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
        assert state.subscriber[preserved] == original[preserved]
    assert tx_client.session.transaction.commit_attempts == 1


def test_subscriber_is_revalidated_inside_transaction(monkeypatch):
    changed = _subscriber(newsletter_token_version=TOKEN_VERSION + 1)
    client, _, state, _, subscribers, challenge, _ = _install(
        monkeypatch, transaction_subscriber=changed
    )

    response = client.post(PATH, json=_payload())

    assert response.status_code == 401
    assert response.json() == {"detail": GENERIC_401}
    assert challenge.consume_calls == []
    assert subscribers.update_calls == []
    assert state.challenge_consumed is False
    assert state.subscriber["active"] is False


def test_active_state_change_inside_transaction_stops_before_consumption(
    monkeypatch,
):
    changed = _subscriber(active=True)
    client, _, state, _, subscribers, challenge, _ = _install(
        monkeypatch, transaction_subscriber=changed
    )

    response = client.post(PATH, json=_payload())

    assert response.status_code == 409
    assert response.json() == {"detail": CONFLICT_409}
    assert challenge.consume_calls == []
    assert subscribers.update_calls == []
    assert state.challenge_consumed is False
    assert state.subscriber["active"] is False


@pytest.mark.parametrize(
    "reason",
    (
        server.ChallengeResultReason.NOT_ELIGIBLE,
        server.ChallengeResultReason.DUPLICATE,
        object(),
    ),
)
def test_ineligible_or_malformed_challenge_is_generic_401(
    monkeypatch, reason
):
    client, _, state, _, subscribers, challenge, _ = _install(
        monkeypatch, challenge_reason=reason
    )

    response = client.post(PATH, json=_payload())

    assert response.status_code == 401
    assert response.json() == {"detail": GENERIC_401}
    assert subscribers.update_calls == []
    assert state.challenge_consumed is False
    assert len(challenge.consume_calls) == 1


def test_challenge_storage_failure_is_generic_503(monkeypatch):
    client, _, state, _, subscribers, _, _ = _install(
        monkeypatch,
        challenge_reason=server.ChallengeResultReason.STORAGE_ERROR,
    )

    response = client.post(PATH, json=_payload())

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert subscribers.update_calls == []
    assert state.challenge_consumed is False


class MissingMatchedCount:
    pass


@pytest.mark.parametrize(
    "update_result",
    (
        MissingMatchedCount(),
        SimpleNamespace(matched_count=True),
        SimpleNamespace(matched_count=None),
        SimpleNamespace(matched_count="1"),
        SimpleNamespace(matched_count=1.0),
        SimpleNamespace(matched_count=Decimal("1")),
        SimpleNamespace(matched_count=IntSubclass(1)),
        SimpleNamespace(matched_count=-1),
        SimpleNamespace(matched_count=2),
        SimpleNamespace(matched_count=object()),
    ),
)
def test_malformed_update_result_is_503_and_rolls_back(
    monkeypatch, update_result
):
    client, _, state, _, _, challenge, tx_client = _install(
        monkeypatch, update_result=update_result
    )

    response = client.post(PATH, json=_payload())

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert state.challenge_consumed is False
    assert state.subscriber["active"] is False
    assert state.subscriber["newsletter_token_version"] == TOKEN_VERSION
    assert challenge.successful_consumptions == 1
    assert "transaction_abort" in [step[0] for step in tx_client.session.order]


def test_exact_zero_is_conflict_and_rolls_back(monkeypatch):
    client, _, state, _, _, challenge, _ = _install(
        monkeypatch, update_result=SimpleNamespace(matched_count=0)
    )

    response = client.post(PATH, json=_payload())

    assert response.status_code == 409
    assert response.json() == {"detail": CONFLICT_409}
    assert state.challenge_consumed is False
    assert state.subscriber["active"] is False
    assert challenge.successful_consumptions == 1


@pytest.mark.parametrize(
    "failure",
    (
        "client",
        "session",
        "start",
        "find",
        "update",
        "commit",
        "indeterminate",
        "abort",
    ),
)
def test_transaction_failures_are_generic_without_retry(monkeypatch, failure):
    kwargs = {
        "client_error": failure == "client",
        "session_error": failure == "session",
        "start_error": failure == "start",
        "transaction_find_error": failure == "find",
        "update_error": failure == "update",
        "commit_error": failure == "commit",
        "indeterminate_commit": failure == "indeterminate",
        "abort_error": failure == "abort",
        "challenge_reason": (
            server.ChallengeResultReason.NOT_ELIGIBLE
            if failure == "abort"
            else None
        ),
    }
    client, order, state, _, subscribers, challenge, tx_client = _install(
        monkeypatch, **kwargs
    )

    response = client.post(PATH, json=_payload())

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert tx_client.start_session_calls <= 1
    assert len(challenge.consume_calls) <= 1
    assert len(subscribers.update_calls) <= 1
    assert [step[0] for step in order].count("transaction_commit") <= 1
    assert "private" not in response.text
    if failure not in {"indeterminate"}:
        assert state.challenge_consumed is False
        assert state.subscriber["active"] is False


def test_replay_is_rejected_before_second_transaction(monkeypatch):
    client, _, state, _, subscribers, challenge, tx_client = _install(
        monkeypatch
    )

    first = client.post(PATH, json=_payload())
    replay = client.post(PATH, json=_payload())

    assert first.status_code == 200
    assert replay.status_code == 401
    assert replay.json() == {"detail": GENERIC_401}
    assert state.subscriber["active"] is True
    assert state.subscriber["newsletter_token_version"] == TOKEN_VERSION + 1
    assert challenge.successful_consumptions == 1
    assert len(challenge.consume_calls) == 1
    assert len(subscribers.update_calls) == 1
    assert tx_client.start_session_calls == 1
    assert tx_client.session.transaction.commit_attempts == 1


def test_privacy_safe_failures(monkeypatch):
    client, _, _, _, _, _, _ = _install(
        monkeypatch, update_error=True
    )

    response = client.post(PATH, json=_payload())

    assert response.status_code == 503
    for private in (
        TOKEN,
        TOKEN_HASH,
        MANAGEMENT_ID,
        "private@example.com",
        "private database detail",
    ):
        assert private not in response.text


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
