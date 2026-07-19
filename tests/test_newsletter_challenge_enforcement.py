import asyncio
import hashlib
import os
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pymongo import ReturnDocument


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")
os.environ.pop("NEWSLETTER_LINK_SECRET", None)

from backend import server
from app import newsletter_link_security as link_security


VERIFY_PATH = "/api/newsletter/preferences/verify"
UPDATE_PATH = "/api/newsletter/preferences/secure"
UNSUBSCRIBE_CONFIRM_PATH = "/api/newsletter/unsubscribe/confirm"
UNSUBSCRIBE_ONE_CLICK_PATH = "/api/newsletter/unsubscribe/one-click"
REACTIVATE_CONFIRM_PATH = "/api/newsletter/reactivate/confirm"
TOKEN = "offline-stage-4e6a-token"
TOKEN_HASH = hashlib.sha256(TOKEN.encode()).hexdigest()
MANAGEMENT_ID = "a40ad20d-2439-4b5a-b4ce-f256c79a3daf"
GENERIC_503 = "Secure newsletter management is not yet available."
GENERIC_401 = "This newsletter management link is invalid or has expired."


class IntSubclass(int):
    pass


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

    async def find_one(self, query, projection, **kwargs):
        self.order.append(
            (
                "subscriber",
                deepcopy(query),
                deepcopy(projection),
                dict(kwargs),
            )
        )
        return {
            "newsletter_management_id": MANAGEMENT_ID,
            "newsletter_token_version": 3,
            "active": True,
            "daily_brief": True,
            "weekly_roundup": False,
            "breaking_news": False,
        }

    async def update_one(self, query, update, **kwargs):
        self.update_calls.append(
            (deepcopy(query), deepcopy(update), dict(kwargs))
        )
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


class TransactionalState:
    def __init__(self, subscriber=None):
        self.subscriber = deepcopy(subscriber) if subscriber is not None else {
            "newsletter_management_id": MANAGEMENT_ID,
            "newsletter_token_version": 3,
            "active": True,
            "daily_brief": True,
            "weekly_roundup": False,
            "breaking_news": False,
        }
        self.challenge_consumed = False


class TransactionalSubscribers:
    def __init__(
        self,
        state,
        order,
        *,
        matched_count=1,
        update_result=None,
        transaction_subscriber=None,
    ):
        self.state = state
        self.order = order
        self.matched_count = matched_count
        self.update_result = update_result
        self.transaction_subscriber = transaction_subscriber
        self.find_calls = []
        self.update_calls = []

    async def find_one(self, query, projection, **kwargs):
        call = (deepcopy(query), deepcopy(projection), dict(kwargs))
        self.find_calls.append(call)
        self.order.append(
            ("subscriber_tx" if kwargs.get("session") else "subscriber_pre",)
        )
        if kwargs.get("session") and self.transaction_subscriber is not None:
            return deepcopy(self.transaction_subscriber)
        return deepcopy(self.state.subscriber)

    async def update_one(self, query, update, **kwargs):
        call = (deepcopy(query), deepcopy(update), dict(kwargs))
        self.update_calls.append(call)
        self.order.append(("subscriber_update",))
        if self.update_result is not None:
            return self.update_result
        if self.matched_count != 1:
            return SimpleNamespace(matched_count=self.matched_count)
        self.state.subscriber.update(deepcopy(update["$set"]))
        return SimpleNamespace(matched_count=1)


class TransactionalChallengeRepository:
    def __init__(
        self,
        state,
        order,
        *,
        storage_error=False,
        result_reason=None,
    ):
        self.state = state
        self.order = order
        self.storage_error = storage_error
        self.result_reason = result_reason
        self.consume_calls = []
        self.successful_consumptions = 0
        self.read_calls = []

    async def consume(self, **kwargs):
        self.consume_calls.append(dict(kwargs))
        self.order.append(("consume",))
        if self.storage_error:
            return SimpleNamespace(
                succeeded=False,
                reason=server.ChallengeResultReason.STORAGE_ERROR,
            )
        if self.result_reason is not None:
            return SimpleNamespace(
                succeeded=False,
                reason=self.result_reason,
            )
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

    async def read_eligible_preference(self, **kwargs):
        self.read_calls.append(dict(kwargs))
        return SimpleNamespace(
            succeeded=not self.state.challenge_consumed,
            reason=(
                server.ChallengeResultReason.ELIGIBLE
                if not self.state.challenge_consumed
                else server.ChallengeResultReason.NOT_ELIGIBLE
            ),
        )


class PostConsumptionChallengeCollection:
    def __init__(self):
        self.document = {
            "token_hash": TOKEN_HASH,
            "subscriber_management_id": MANAGEMENT_ID,
            "purpose": link_security.PREFERENCES_OPERATION,
            "delivery_status": link_security.DELIVERED_DELIVERY,
            "consumed_at": None,
            "expires_at": datetime(2099, 1, 1, tzinfo=timezone.utc),
        }

    def _matches(self, query):
        for key, expected in query.items():
            if key == "expires_at":
                if self.document[key] <= expected["$gt"]:
                    return False
            elif self.document.get(key) != expected:
                return False
        return True

    async def find_one_and_update(
        self,
        query,
        update,
        *,
        return_document=ReturnDocument.AFTER,
        **_kwargs,
    ):
        if not self._matches(query):
            return None
        self.document.update(deepcopy(update["$set"]))
        return deepcopy(self.document)

    async def find_one(self, query, projection, **_kwargs):
        if not self._matches(query):
            return None
        return {"_id": "internal-only"}


class TransactionContext:
    def __init__(
        self,
        state,
        order,
        *,
        abort_error=False,
        commit_error=False,
        indeterminate_commit=False,
    ):
        self.state = state
        self.order = order
        self.abort_error = abort_error
        self.commit_error = commit_error
        self.indeterminate_commit = indeterminate_commit
        self.commit_attempts = 0
        self.subscriber_before = None
        self.challenge_before = None

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
            raise RuntimeError("private indeterminate commit detail")
        if exc_type is None and self.commit_error:
            raise RuntimeError("private commit detail")
        if exc_type is None:
            self.order.append(("transaction_commit",))
        return False


class TransactionSession:
    def __init__(
        self,
        state,
        order,
        *,
        start_error=False,
        abort_error=False,
        commit_error=False,
        indeterminate_commit=False,
    ):
        self.state = state
        self.order = order
        self.start_error = start_error
        self.abort_error = abort_error
        self.commit_error = commit_error
        self.indeterminate_commit = indeterminate_commit
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
        self.transaction = TransactionContext(
            self.state,
            self.order,
            abort_error=self.abort_error,
            commit_error=self.commit_error,
            indeterminate_commit=self.indeterminate_commit,
        )
        return self.transaction


class TransactionClient:
    def __init__(
        self,
        state,
        order,
        *,
        session_error=False,
        start_error=False,
        abort_error=False,
        commit_error=False,
        indeterminate_commit=False,
    ):
        self.state = state
        self.order = order
        self.session_error = session_error
        self.start_error = start_error
        self.abort_error = abort_error
        self.commit_error = commit_error
        self.indeterminate_commit = indeterminate_commit
        self.session = None

    async def start_session(self):
        self.order.append(("session_create",))
        if self.session_error:
            raise RuntimeError("private session detail")
        self.session = TransactionSession(
            self.state,
            self.order,
            start_error=self.start_error,
            abort_error=self.abort_error,
            commit_error=self.commit_error,
            indeterminate_commit=self.indeterminate_commit,
        )
        return self.session


def _install_transactional_update(
    monkeypatch,
    *,
    matched_count=1,
    update_result=None,
    storage_error=False,
    challenge_reason=None,
    session_error=False,
    start_error=False,
    abort_error=False,
    commit_error=False,
    indeterminate_commit=False,
    transaction_subscriber=None,
    initial_subscriber=None,
):
    order = []
    state = TransactionalState(initial_subscriber)
    token_service = OrderedTokenService(order)
    subscribers = TransactionalSubscribers(
        state,
        order,
        matched_count=matched_count,
        update_result=update_result,
        transaction_subscriber=transaction_subscriber,
    )
    challenge_repository = TransactionalChallengeRepository(
        state,
        order,
        storage_error=storage_error,
        result_reason=challenge_reason,
    )
    transaction_client = TransactionClient(
        state,
        order,
        session_error=session_error,
        start_error=start_error,
        abort_error=abort_error,
        commit_error=commit_error,
        indeterminate_commit=indeterminate_commit,
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

    def transaction_factory():
        order.append(("transaction_factory",))
        return transaction_client

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
    monkeypatch.setattr(
        server,
        "_create_newsletter_preference_transaction_client",
        transaction_factory,
    )
    monkeypatch.setattr(server, "db", SimpleNamespace(subscribers=subscribers))
    return (
        TestClient(server.app),
        order,
        state,
        subscribers,
        challenge_repository,
        transaction_client,
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


def test_update_disabled_gate_precedes_session_and_every_collaborator(
    monkeypatch,
):
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

    response = TestClient(server.app).put(
        UPDATE_PATH,
        json={
            "token": TOKEN,
            "daily_brief": False,
            "weekly_roundup": True,
            "breaking_news": False,
        },
    )

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}


def test_transactional_preference_update_consumes_once_with_same_session(
    monkeypatch,
):
    (
        client,
        order,
        state,
        subscribers,
        challenge_repository,
        transaction_client,
    ) = _install_transactional_update(monkeypatch)
    payload = {
        "token": TOKEN,
        "daily_brief": False,
        "weekly_roundup": True,
        "breaking_news": False,
    }

    response = client.put(UPDATE_PATH, json=payload)

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Your email preferences have been updated.",
    }
    assert [step[0] for step in order] == [
        "token_factory",
        "token",
        "subscriber_pre",
        "hash",
        "challenge_factory",
        "transaction_factory",
        "session_create",
        "session_enter",
        "transaction_start",
        "subscriber_tx",
        "consume",
        "subscriber_update",
        "transaction_commit",
        "session_exit",
    ]
    session = transaction_client.session
    assert challenge_repository.consume_calls[0]["session"] is session
    assert subscribers.find_calls[1][2]["session"] is session
    assert subscribers.update_calls[0][2]["session"] is session
    assert challenge_repository.consume_calls[0][
        "subscriber_management_id"
    ] == MANAGEMENT_ID
    assert challenge_repository.consume_calls[0][
        "expected_purpose"
    ] == server.PREFERENCES_PURPOSE
    query, update, options = subscribers.update_calls[0]
    assert query == {
        "newsletter_management_id": MANAGEMENT_ID,
        "newsletter_token_version": 3,
        "active": True,
    }
    assert set(update) == {"$set"}
    assert set(update["$set"]) == {
        "daily_brief",
        "weekly_roundup",
        "breaking_news",
        "preferences_updated_at",
    }
    assert options == {"session": session}
    assert state.challenge_consumed is True
    assert state.subscriber["newsletter_token_version"] == 3
    assert transaction_client.session.transaction.commit_attempts == 1
    assert challenge_repository.successful_consumptions == 1

    replay = client.put(UPDATE_PATH, json=payload)
    assert replay.status_code == 401
    assert replay.json() == {"detail": GENERIC_401}
    assert len(subscribers.update_calls) == 1
    assert challenge_repository.successful_consumptions == 1
    assert [step[0] for step in order].count("transaction_commit") == 1
    assert [step[0] for step in order].count(
        "transaction_commit_indeterminate"
    ) == 0


def test_successful_update_makes_actual_repository_read_ineligible(
    monkeypatch,
):
    client, _, _, _, _, _ = _install_transactional_update(monkeypatch)
    collection = PostConsumptionChallengeCollection()
    repository = link_security.NewsletterChallengeRepository(collection)
    monkeypatch.setattr(
        server,
        "_create_newsletter_preference_challenge_repository",
        lambda: repository,
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
    eligibility = asyncio.run(
        repository.read_eligible_preference(
            token_hash=TOKEN_HASH,
            subscriber_management_id=MANAGEMENT_ID,
            now=datetime.now(timezone.utc),
        )
    )

    assert response.status_code == 200
    assert collection.document["consumed_at"] is not None
    assert eligibility == link_security.ChallengeResult(
        False,
        link_security.ChallengeResultReason.NOT_ELIGIBLE,
    )
    assert not hasattr(eligibility, "token_hash")
    assert not hasattr(eligibility, "subscriber_management_id")


def test_subscriber_conflict_rolls_back_challenge_consumption(monkeypatch):
    client, order, state, subscribers, _, _ = (
        _install_transactional_update(monkeypatch, matched_count=0)
    )
    before = deepcopy(state.subscriber)

    response = client.put(
        UPDATE_PATH,
        json={
            "token": TOKEN,
            "daily_brief": False,
            "weekly_roundup": True,
            "breaking_news": False,
        },
    )

    assert response.status_code == 409
    assert state.challenge_consumed is False
    assert state.subscriber == before
    assert len(subscribers.update_calls) == 1
    assert "transaction_abort" in [step[0] for step in order]


@pytest.mark.parametrize(
    ("changes", "expected_status"),
    (
        ({"newsletter_management_id": "invalid"}, 401),
        ({"newsletter_token_version": True}, 401),
        ({"newsletter_token_version": 4}, 401),
        ({"active": False}, 409),
        ({"active": "true"}, 409),
    ),
)
def test_subscriber_is_revalidated_inside_transaction(
    monkeypatch,
    changes,
    expected_status,
):
    transaction_subscriber = deepcopy(TransactionalState().subscriber)
    transaction_subscriber.update(changes)
    client, _, state, subscribers, challenge_repository, _ = (
        _install_transactional_update(
            monkeypatch,
            transaction_subscriber=transaction_subscriber,
        )
    )
    before = deepcopy(state.subscriber)

    response = client.put(
        UPDATE_PATH,
        json={
            "token": TOKEN,
            "daily_brief": False,
            "weekly_roundup": True,
            "breaking_news": False,
        },
    )

    assert response.status_code == expected_status
    assert state.subscriber == before
    assert state.challenge_consumed is False
    assert challenge_repository.consume_calls == []
    assert subscribers.update_calls == []


def test_commit_failure_rolls_back_challenge_and_preferences(monkeypatch):
    client, order, state, _, _, _ = _install_transactional_update(
        monkeypatch,
        commit_error=True,
    )
    before = deepcopy(state.subscriber)

    response = client.put(
        UPDATE_PATH,
        json={
            "token": TOKEN,
            "daily_brief": False,
            "weekly_roundup": True,
            "breaking_news": False,
        },
    )

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert state.challenge_consumed is False
    assert state.subscriber == before
    assert "transaction_abort" in [step[0] for step in order]
    assert "private commit detail" not in response.text


@pytest.mark.parametrize(
    "malformed_result",
    (
        SimpleNamespace(),
        SimpleNamespace(matched_count=None),
        SimpleNamespace(matched_count=True),
        SimpleNamespace(matched_count="1"),
        SimpleNamespace(matched_count=1.0),
        SimpleNamespace(matched_count=Decimal("1")),
        SimpleNamespace(matched_count=IntSubclass(1)),
        SimpleNamespace(matched_count=-1),
        SimpleNamespace(matched_count=2),
    ),
)
def test_malformed_update_result_aborts_without_partial_success(
    monkeypatch,
    malformed_result,
):
    client, order, state, subscribers, challenge_repository, _ = (
        _install_transactional_update(
            monkeypatch,
            update_result=malformed_result,
        )
    )
    before = deepcopy(state.subscriber)

    response = client.put(
        UPDATE_PATH,
        json={
            "token": TOKEN,
            "daily_brief": False,
            "weekly_roundup": True,
            "breaking_news": False,
        },
    )

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert state.challenge_consumed is False
    assert state.subscriber == before
    assert len(subscribers.update_calls) == 1
    assert challenge_repository.successful_consumptions == 1
    assert [step[0] for step in order].count("transaction_abort") == 1
    assert [step[0] for step in order].count("subscriber_update") == 1
    rendered = response.text
    for private_value in (
        TOKEN,
        TOKEN_HASH,
        MANAGEMENT_ID,
        "matched_count",
        "transaction",
        "database",
    ):
        assert private_value not in rendered


def test_indeterminate_commit_fails_closed_without_retry_or_fallback(
    monkeypatch,
):
    client, order, _, subscribers, challenge_repository, transaction_client = (
        _install_transactional_update(
            monkeypatch,
            indeterminate_commit=True,
        )
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

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert len(subscribers.update_calls) == 1
    assert len(challenge_repository.consume_calls) == 1
    assert challenge_repository.successful_consumptions == 1
    assert transaction_client.session.transaction.commit_attempts == 1
    assert [step[0] for step in order].count(
        "transaction_commit_indeterminate"
    ) == 1
    assert [step[0] for step in order].count("subscriber_update") == 1
    assert [step[0] for step in order].count("consume") == 1
    assert "private indeterminate commit detail" not in response.text
    assert "success" not in response.text.lower()


def test_abort_failure_is_generic_and_exposes_no_transaction_detail(
    monkeypatch,
):
    client, _, state, _, _, _ = _install_transactional_update(
        monkeypatch,
        matched_count=0,
        abort_error=True,
    )
    before = deepcopy(state.subscriber)

    response = client.put(
        UPDATE_PATH,
        json={
            "token": TOKEN,
            "daily_brief": False,
            "weekly_roundup": True,
            "breaking_news": False,
        },
    )

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert state.challenge_consumed is False
    assert state.subscriber == before
    assert "private abort detail" not in response.text


def test_transactional_human_unsubscribe_uses_same_session_and_updates_once(
    monkeypatch,
):
    client, order, state, subscribers, challenge_repository, tx_client = (
        _install_transactional_update(monkeypatch)
    )

    response = client.post(
        UNSUBSCRIBE_CONFIRM_PATH,
        json={"token": TOKEN},
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Your unsubscribe request has been processed.",
    }
    session = tx_client.session
    assert subscribers.find_calls[1][2] == {"session": session}
    assert challenge_repository.consume_calls[0]["session"] is session
    assert challenge_repository.consume_calls[0][
        "expected_purpose"
    ] == server.UNSUBSCRIBE_PURPOSE
    assert subscribers.update_calls[0][2] == {"session": session}
    assert set(subscribers.update_calls[0][1]["$set"]) == {
        "active",
        "daily_brief",
        "weekly_roundup",
        "breaking_news",
        "unsubscribed_at",
        "unsubscribe_method",
    }
    assert state.subscriber["active"] is False
    assert state.subscriber["newsletter_token_version"] == 3
    assert [step[0] for step in order].count("transaction_commit") == 1


def test_inactive_human_unsubscribe_consumes_once_without_subscriber_update(
    monkeypatch,
):
    client, order, state, subscribers, challenge_repository, _ = (
        _install_transactional_update(monkeypatch)
    )
    state.subscriber["active"] = False

    first = client.post(UNSUBSCRIBE_CONFIRM_PATH, json={"token": TOKEN})
    replay = client.post(UNSUBSCRIBE_CONFIRM_PATH, json={"token": TOKEN})

    assert first.status_code == 200
    assert replay.status_code == 401
    assert subscribers.update_calls == []
    assert challenge_repository.successful_consumptions == 1
    assert [step[0] for step in order].count("transaction_commit") == 1


def test_rfc_one_click_replay_is_idempotent_without_second_commit(
    monkeypatch,
):
    client, order, state, subscribers, challenge_repository, _ = (
        _install_transactional_update(monkeypatch)
    )
    path = f"{UNSUBSCRIBE_ONE_CLICK_PATH}?token={TOKEN}"
    form = {"List-Unsubscribe": "One-Click"}

    first = client.post(path, data=form)
    replay = client.post(path, data=form)

    assert first.status_code == replay.status_code == 200
    assert state.subscriber["active"] is False
    assert len(subscribers.update_calls) == 1
    assert challenge_repository.successful_consumptions == 1
    assert [step[0] for step in order].count("transaction_commit") == 1


def test_unsubscribe_conflict_rolls_back_challenge_and_subscriber(monkeypatch):
    client, order, state, _, _, _ = _install_transactional_update(
        monkeypatch,
        matched_count=0,
    )
    before = deepcopy(state.subscriber)

    response = client.post(
        UNSUBSCRIBE_CONFIRM_PATH,
        json={"token": TOKEN},
    )

    assert response.status_code == 409
    assert state.challenge_consumed is False
    assert state.subscriber == before
    assert [step[0] for step in order].count("transaction_abort") == 1


def test_malformed_unsubscribe_result_rolls_back_known_changes(monkeypatch):
    client, order, state, subscribers, challenge_repository, _ = (
        _install_transactional_update(
            monkeypatch,
            update_result=SimpleNamespace(matched_count=True),
        )
    )
    before = deepcopy(state.subscriber)

    response = client.post(
        UNSUBSCRIBE_CONFIRM_PATH,
        json={"token": TOKEN},
    )

    assert response.status_code == 503
    assert state.challenge_consumed is False
    assert state.subscriber == before
    assert len(subscribers.update_calls) == 1
    assert challenge_repository.successful_consumptions == 1
    assert [step[0] for step in order].count("transaction_abort") == 1


@pytest.mark.parametrize(
    "failure_options",
    (
        {"storage_error": True},
        {"session_error": True},
        {"start_error": True},
        {"commit_error": True},
        {"indeterminate_commit": True},
    ),
)
def test_unsubscribe_transaction_failures_are_generic_without_retry(
    monkeypatch,
    failure_options,
):
    client, order, state, subscribers, challenge_repository, tx_client = (
        _install_transactional_update(monkeypatch, **failure_options)
    )
    before = deepcopy(state.subscriber)

    response = client.post(
        UNSUBSCRIBE_CONFIRM_PATH,
        json={"token": TOKEN},
    )

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert [step[0] for step in order].count("subscriber_update") <= 1
    assert [step[0] for step in order].count("consume") <= 1
    if failure_options.get("commit_error"):
        assert state.subscriber == before
        assert state.challenge_consumed is False
    if failure_options.get("indeterminate_commit"):
        assert tx_client.session.transaction.commit_attempts == 1
        assert [step[0] for step in order].count(
            "transaction_commit_indeterminate"
        ) == 1
    for private_value in (
        TOKEN,
        TOKEN_HASH,
        MANAGEMENT_ID,
        "private",
        "transaction",
        "database",
    ):
        assert private_value not in response.text


@pytest.mark.parametrize(
    "failure_options",
    (
        {"storage_error": True},
        {"session_error": True},
        {"start_error": True},
    ),
)
def test_storage_or_session_failure_is_generic_503_without_partial_change(
    monkeypatch,
    failure_options,
):
    client, _, state, subscribers, _, _ = _install_transactional_update(
        monkeypatch,
        **failure_options,
    )
    before = deepcopy(state.subscriber)

    response = client.put(
        UPDATE_PATH,
        json={
            "token": TOKEN,
            "daily_brief": False,
            "weekly_roundup": True,
            "breaking_news": False,
        },
    )

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert state.challenge_consumed is False
    assert state.subscriber == before
    assert subscribers.update_calls == []


@pytest.mark.parametrize(
    "reason",
    (
        server.ChallengeResultReason.NOT_ELIGIBLE,
        server.ChallengeResultReason.FAILED,
        server.ChallengeResultReason.CONSUMED,
        "malformed",
    ),
)
def test_ineligible_challenge_outcomes_abort_without_subscriber_update(
    monkeypatch,
    reason,
):
    client, _, state, subscribers, _, _ = _install_transactional_update(
        monkeypatch,
        challenge_reason=reason,
    )
    before = deepcopy(state.subscriber)

    response = client.put(
        UPDATE_PATH,
        json={
            "token": TOKEN,
            "daily_brief": False,
            "weekly_roundup": True,
            "breaking_news": False,
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": GENERIC_401}
    assert state.challenge_consumed is False
    assert state.subscriber == before
    assert subscribers.update_calls == []
    assert TOKEN not in response.text
    assert TOKEN_HASH not in response.text
    assert MANAGEMENT_ID not in response.text


def test_unavailable_update_challenge_factory_is_generic_503(monkeypatch):
    client, _, state, subscribers, _, _ = _install_transactional_update(
        monkeypatch
    )
    before = deepcopy(state.subscriber)
    monkeypatch.setattr(
        server,
        "_create_newsletter_preference_challenge_repository",
        lambda: (_ for _ in ()).throw(
            RuntimeError("private challenge factory detail")
        ),
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

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert state.subscriber == before
    assert subscribers.update_calls == []
    assert "private challenge factory detail" not in response.text


def test_unavailable_transaction_client_factory_is_generic_503(monkeypatch):
    client, _, state, subscribers, _, _ = _install_transactional_update(
        monkeypatch
    )
    before = deepcopy(state.subscriber)
    monkeypatch.setattr(
        server,
        "_create_newsletter_preference_transaction_client",
        lambda: (_ for _ in ()).throw(
            RuntimeError("private transaction factory detail")
        ),
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

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert state.subscriber == before
    assert subscribers.update_calls == []
    assert "private transaction factory detail" not in response.text


def _reactivation_subscriber():
    return {
        "newsletter_management_id": MANAGEMENT_ID,
        "newsletter_token_version": 3,
        "active": False,
        "daily_brief": False,
        "weekly_roundup": False,
        "breaking_news": False,
        "unsubscribed_at": "historical-unsubscribe-time",
        "unsubscribe_method": "secure_token",
    }


def _reactivation_payload():
    return {
        "token": TOKEN,
        "daily_brief": False,
        "weekly_roundup": True,
        "breaking_news": False,
    }


def test_reactivation_gate_precedes_session_and_every_collaborator(
    monkeypatch,
):
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

    response = TestClient(server.app).post(
        REACTIVATE_CONFIRM_PATH,
        json=_reactivation_payload(),
    )

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}


def test_transactional_reactivation_uses_same_session_and_increments_once(
    monkeypatch,
):
    (
        client,
        order,
        state,
        subscribers,
        challenge_repository,
        transaction_client,
    ) = _install_transactional_update(
        monkeypatch,
        initial_subscriber=_reactivation_subscriber(),
    )

    response = client.post(
        REACTIVATE_CONFIRM_PATH,
        json=_reactivation_payload(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Your subscription preferences have been confirmed.",
    }
    session = transaction_client.session
    assert len(subscribers.find_calls) == 2
    assert subscribers.find_calls[0][2] == {}
    assert subscribers.find_calls[1][2] == {"session": session}
    consume = challenge_repository.consume_calls[0]
    assert consume["token_hash"] == TOKEN_HASH
    assert consume["subscriber_management_id"] == MANAGEMENT_ID
    assert consume["expected_purpose"] == server.REACTIVATE_PURPOSE
    assert consume["session"] is session
    query, update, kwargs = subscribers.update_calls[0]
    assert kwargs == {"session": session}
    assert query == {
        "newsletter_management_id": MANAGEMENT_ID,
        "newsletter_token_version": 3,
        "active": False,
    }
    assert update["$set"]["daily_brief"] is False
    assert update["$set"]["weekly_roundup"] is True
    assert update["$set"]["breaking_news"] is False
    assert update["$set"]["newsletter_token_version"] == 4
    assert state.subscriber["unsubscribed_at"] == "historical-unsubscribe-time"
    assert state.subscriber["unsubscribe_method"] == "secure_token"
    assert transaction_client.session.transaction.commit_attempts == 1
    assert [step[0] for step in order].count("transaction_commit") == 1


def test_reactivation_conflict_rolls_back_challenge_and_subscriber(
    monkeypatch,
):
    (
        client,
        order,
        state,
        subscribers,
        challenge_repository,
        transaction_client,
    ) = _install_transactional_update(
        monkeypatch,
        matched_count=0,
        initial_subscriber=_reactivation_subscriber(),
    )

    response = client.post(
        REACTIVATE_CONFIRM_PATH,
        json=_reactivation_payload(),
    )

    assert response.status_code == 409
    assert state.challenge_consumed is False
    assert state.subscriber == _reactivation_subscriber()
    assert challenge_repository.successful_consumptions == 1
    assert len(subscribers.update_calls) == 1
    assert transaction_client.session.transaction.commit_attempts == 0


def test_malformed_reactivation_result_rolls_back_known_changes(monkeypatch):
    (
        client,
        order,
        state,
        _,
        challenge_repository,
        transaction_client,
    ) = _install_transactional_update(
        monkeypatch,
        update_result=SimpleNamespace(matched_count=True),
        initial_subscriber=_reactivation_subscriber(),
    )

    response = client.post(
        REACTIVATE_CONFIRM_PATH,
        json=_reactivation_payload(),
    )

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert state.challenge_consumed is False
    assert state.subscriber == _reactivation_subscriber()
    assert challenge_repository.successful_consumptions == 1
    assert transaction_client.session.transaction.commit_attempts == 0


@pytest.mark.parametrize(
    ("failure", "known_rollback"),
    (("commit", True), ("indeterminate", False)),
)
def test_reactivation_commit_failures_are_generic_without_retry(
    monkeypatch,
    failure,
    known_rollback,
):
    (
        client,
        order,
        state,
        subscribers,
        challenge_repository,
        transaction_client,
    ) = _install_transactional_update(
        monkeypatch,
        commit_error=failure == "commit",
        indeterminate_commit=failure == "indeterminate",
        initial_subscriber=_reactivation_subscriber(),
    )

    response = client.post(
        REACTIVATE_CONFIRM_PATH,
        json=_reactivation_payload(),
    )

    assert response.status_code == 503
    assert response.json() == {"detail": GENERIC_503}
    assert len(challenge_repository.consume_calls) == 1
    assert len(subscribers.update_calls) == 1
    assert transaction_client.session.transaction.commit_attempts == 1
    assert [step[0] for step in order].count("session_create") == 1
    if known_rollback:
        assert state.challenge_consumed is False
        assert state.subscriber == _reactivation_subscriber()


def test_reactivation_replay_has_no_second_consume_update_or_commit(
    monkeypatch,
):
    (
        client,
        order,
        state,
        subscribers,
        challenge_repository,
        transaction_client,
    ) = _install_transactional_update(
        monkeypatch,
        initial_subscriber=_reactivation_subscriber(),
    )

    first = client.post(
        REACTIVATE_CONFIRM_PATH,
        json=_reactivation_payload(),
    )
    replay = client.post(
        REACTIVATE_CONFIRM_PATH,
        json=_reactivation_payload(),
    )

    assert first.status_code == 200
    assert replay.status_code == 401
    assert replay.json() == {"detail": GENERIC_401}
    assert state.subscriber["newsletter_token_version"] == 4
    assert challenge_repository.successful_consumptions == 1
    assert len(challenge_repository.consume_calls) == 1
    assert len(subscribers.update_calls) == 1
    assert [step[0] for step in order].count("session_create") == 1
    assert transaction_client.session.transaction.commit_attempts == 1


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


def test_runtime_collaborators_exist_but_activation_remains_disabled():
    source = open(server.__file__, encoding="utf-8").read()
    assert "NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED = False" in source
    factory_marker = (
        "def _create_newsletter_preference_challenge_repository():"
    )
    assert factory_marker in source
    assert "NewsletterChallengeRepository(" not in source.split(
        factory_marker,
        1,
    )[0]
    assert "create_index(" not in source[
        source.index("NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED"):
        source.index('@api_router.get("/newsletter/categories")')
    ]
