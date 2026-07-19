import asyncio
import hashlib
import inspect
import logging
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path
from uuid import uuid4

import pytest

from backend.app import newsletter_link_security as security


NOW = datetime(2026, 7, 19, 12, 0, tzinfo=timezone.utc)
MANAGEMENT_ID = str(uuid4())
TOKEN = "isolated-test-token"
TOKEN_HASH = hashlib.sha256(TOKEN.encode()).hexdigest()
EMAIL = " Person@Example.COM "
IP = "203.0.113.44"


def async_test(function):
    @wraps(function)
    def run_in_isolated_event_loop(*args, **kwargs):
        return asyncio.run(function(*args, **kwargs))

    return run_in_isolated_event_loop


class Result:
    def __init__(self, matched_count=0):
        self.matched_count = matched_count


def matches(document, query):
    for key, expected in query.items():
        if key == "$expr":
            continue
        actual = document.get(key)
        if isinstance(expected, dict) and "$gt" in expected:
            if actual is None or not actual > expected["$gt"]:
                return False
        elif actual != expected:
            return False
    return True


def evaluate_mongo_expression(expression, document, variables=None):
    """Evaluate the exact operator subset emitted by the repository."""

    variables = variables or {}
    if isinstance(expression, str):
        if expression.startswith("$$"):
            return variables[expression[2:]]
        if expression.startswith("$"):
            return document.get(expression[1:])
        return expression
    if isinstance(expression, list):
        return [
            evaluate_mongo_expression(item, document, variables)
            for item in expression
        ]
    if not isinstance(expression, dict):
        return expression
    if len(expression) != 1:
        return {
            key: evaluate_mongo_expression(value, document, variables)
            for key, value in expression.items()
        }

    operator, value = next(iter(expression.items()))
    if operator == "$ifNull":
        candidate, fallback = value
        evaluated = evaluate_mongo_expression(candidate, document, variables)
        return (
            evaluate_mongo_expression(fallback, document, variables)
            if evaluated is None
            else evaluated
        )
    if operator == "$filter":
        source = evaluate_mongo_expression(value["input"], document, variables)
        if not isinstance(source, list):
            raise TypeError("malformed stored timestamp state")
        retained = []
        for item in source:
            scoped = {**variables, value["as"]: item}
            if evaluate_mongo_expression(value["cond"], document, scoped):
                retained.append(item)
        return retained
    if operator == "$concatArrays":
        arrays = evaluate_mongo_expression(value, document, variables)
        if any(not isinstance(array, list) for array in arrays):
            raise TypeError("malformed array expression")
        return [item for array in arrays for item in array]
    if operator == "$size":
        return len(evaluate_mongo_expression(value, document, variables))
    if operator in {"$gt", "$lt", "$lte", "$eq"}:
        left, right = evaluate_mongo_expression(value, document, variables)
        return {
            "$gt": lambda: left > right,
            "$lt": lambda: left < right,
            "$lte": lambda: left <= right,
            "$eq": lambda: left == right,
        }[operator]()
    if operator == "$and":
        return all(
            evaluate_mongo_expression(item, document, variables)
            for item in value
        )
    if operator == "$or":
        return any(
            evaluate_mongo_expression(item, document, variables)
            for item in value
        )
    raise AssertionError(f"Unsupported generated Mongo operator: {operator}")


def apply_mongo_pipeline(document, pipeline):
    updated = deepcopy(document)
    for stage in pipeline:
        assert set(stage) == {"$set"}
        original = deepcopy(updated)
        for field, expression in stage["$set"].items():
            updated[field] = evaluate_mongo_expression(expression, original)
    return updated


class FakeRateLimitCollection:
    def __init__(self):
        self.documents = {}
        self.writes = 0
        self.fail = False
        self.lock = asyncio.Lock()
        self.last_filter = None
        self.last_pipeline = None
        self.duplicate_conflicts = 0

    async def find_one_and_update(
        self, query, update, *, upsert=False, return_document=None
    ):
        if self.fail:
            raise RuntimeError("raw database payload should never escape")
        self.last_filter = deepcopy(query)
        self.last_pipeline = deepcopy(update)
        identity = tuple(query[key] for key in ("dimension", "hash", "operation"))
        async with self.lock:
            document = self.documents.get(identity)
            base = deepcopy(document) if document else {
                "dimension": query["dimension"],
                "hash": query["hash"],
                "operation": query["operation"],
            }
            if not evaluate_mongo_expression(query["$expr"], base):
                if upsert and document is not None:
                    self.duplicate_conflicts += 1
                    raise security.DuplicateKeyError(
                        "simulated unique-index conflict"
                    )
                return None
            stored = apply_mongo_pipeline(base, update)
            self.documents[identity] = stored
            self.writes += 1
            return deepcopy(stored)

    async def find_one(self, query, projection=None):
        if self.fail:
            raise RuntimeError("raw database payload should never escape")
        identity = tuple(query[key] for key in ("dimension", "hash", "operation"))
        document = self.documents.get(identity)
        return deepcopy(document) if document else None


class FakeChallengeCollection:
    def __init__(self):
        self.documents = {}
        self.fail = False
        self.index_calls = 0
        self.lock = asyncio.Lock()

    async def insert_one(self, document):
        if self.fail:
            raise RuntimeError("raw insert payload should never escape")
        token_hash = document["token_hash"]
        if token_hash in self.documents:
            raise security.DuplicateKeyError("duplicate internals")
        self.documents[token_hash] = deepcopy(document)
        return Result(1)

    async def update_one(self, query, update):
        if self.fail:
            raise RuntimeError("raw update payload should never escape")
        async with self.lock:
            document = self.documents.get(query["token_hash"])
            if not document or not matches(document, query):
                return Result(0)
            document.update(deepcopy(update["$set"]))
            return Result(1)

    async def find_one(self, query, projection=None):
        if self.fail:
            raise RuntimeError("raw find payload should never escape")
        document = self.documents.get(query["token_hash"])
        if not document or not matches(document, query):
            return None
        return {"_id": "internal-only"} if projection else deepcopy(document)

    async def find_one_and_update(
        self, query, update, *, return_document=None
    ):
        if self.fail:
            raise RuntimeError("raw atomic payload should never escape")
        async with self.lock:
            document = self.documents.get(query["token_hash"])
            if not document or not matches(document, query):
                return None
            document.update(deepcopy(update["$set"]))
            return deepcopy(document)

    async def create_index(self, *args, **kwargs):
        self.index_calls += 1


def challenge_repository(status=security.PENDING_DELIVERY, consumed_at=None):
    collection = FakeChallengeCollection()
    document = dict(
        security.build_pending_challenge(
            token_hash=TOKEN_HASH,
            subscriber_management_id=MANAGEMENT_ID,
            purpose=security.PREFERENCES_OPERATION,
            issued_at=NOW,
            expires_at=NOW + timedelta(minutes=30),
        )
    )
    document["delivery_status"] = status
    document["consumed_at"] = consumed_at
    collection.documents[TOKEN_HASH] = document
    return security.NewsletterChallengeRepository(collection), collection


def exact_index_metadata(definition):
    metadata = {"name": definition.name, "key": list(definition.keys)}
    if definition.unique is not None:
        metadata["unique"] = definition.unique
    if definition.expire_after_seconds is not None:
        metadata["expireAfterSeconds"] = definition.expire_after_seconds
    return metadata


def test_email_normalization_and_full_hash():
    assert security.normalize_email(EMAIL) == "person@example.com"
    assert security.hash_normalized_email(EMAIL) == hashlib.sha256(
        b"person@example.com"
    ).hexdigest()
    assert len(security.hash_normalized_email(EMAIL)) == 64


def test_ip_and_token_hashes_are_full_lowercase_sha256():
    assert security.hash_source_ip(IP) == hashlib.sha256(IP.encode()).hexdigest()
    assert security.hash_token(TOKEN) == TOKEN_HASH
    assert security._SHA256_RE.fullmatch(security.hash_source_ip(IP))


@pytest.mark.parametrize(
    "helper,value",
    [
        (security.normalize_email, ""),
        (security.normalize_email, "   "),
        (security.hash_source_ip, ""),
        (security.hash_source_ip, " "),
        (security.hash_token, ""),
        (security.hash_token, " "),
    ],
)
def test_empty_private_inputs_are_rejected_without_leak(helper, value):
    with pytest.raises(security.NewsletterLinkValidationError) as error:
        helper(value)
    assert value.strip() not in str(error.value) or not value.strip()


def test_safe_fingerprint_is_short_deterministic_hex():
    first = security.safe_fingerprint(TOKEN)
    assert first == security.safe_fingerprint(TOKEN)
    assert len(first) == 12
    assert all(character in "0123456789abcdef" for character in first)
    assert TOKEN not in first


@pytest.mark.parametrize("dimension", ["email", "ip"])
@pytest.mark.parametrize("operation", ["preferences", "unsubscribe", "reactivate"])
def test_approved_rate_limit_identity_values(dimension, operation):
    decision, _ = security.evaluate_rate_limit(
        dimension=dimension,
        accepted_at=[],
        now=NOW,
    )
    assert decision.allowed
    assert operation in security.ALLOWED_OPERATIONS


@pytest.mark.parametrize("dimension", ["", "user", True, 1])
def test_invalid_rate_limit_dimension_rejected(dimension):
    with pytest.raises(security.NewsletterLinkValidationError):
        security.evaluate_rate_limit(
            dimension=dimension,
            accepted_at=[],
            now=NOW,
        )


@pytest.mark.parametrize("operation", ["", "email", True, 1])
@async_test
async def test_invalid_operation_fails_closed(operation):
    repository = security.NewsletterRateLimitRepository(
        FakeRateLimitCollection()
    )
    decision = await repository.reserve_request(
        dimension="email",
        subject_hash=security.hash_normalized_email(EMAIL),
        operation=operation,
        now=NOW,
    )
    assert decision == security.RateLimitDecision(
        False, security.RateLimitReason.INVALID_INPUT
    )


@async_test
async def test_malformed_hash_fails_closed():
    repository = security.NewsletterRateLimitRepository(
        FakeRateLimitCollection()
    )
    decision = await repository.reserve_request(
        dimension="email",
        subject_hash="not-a-hash",
        operation="preferences",
        now=NOW,
    )
    assert decision.reason is security.RateLimitReason.INVALID_INPUT


def test_naive_rate_limit_time_rejected():
    with pytest.raises(security.NewsletterLinkValidationError):
        security.evaluate_rate_limit(
            dimension="email",
            accepted_at=[],
            now=NOW.replace(tzinfo=None),
        )


@pytest.mark.parametrize("value", [True, False, 0, -1, "3"])
def test_boolean_and_invalid_integer_limits_rejected(value):
    with pytest.raises(security.NewsletterLinkValidationError):
        security.evaluate_rate_limit(
            dimension="email",
            accepted_at=[],
            now=NOW,
            hourly_limit=value,
        )


def test_email_first_request_allowed_and_cooldown_enforced():
    first, state = security.evaluate_rate_limit(
        dimension="email", accepted_at=[], now=NOW
    )
    second, unchanged = security.evaluate_rate_limit(
        dimension="email",
        accepted_at=state.accepted_at,
        now=NOW + timedelta(minutes=14, seconds=59),
    )
    assert first.allowed
    assert second.reason is security.RateLimitReason.COOLDOWN
    assert second.next_eligible_at == NOW + timedelta(minutes=15)
    assert unchanged.accepted_at == state.accepted_at


def test_email_request_at_cooldown_boundary_allowed():
    decision, state = security.evaluate_rate_limit(
        dimension="email",
        accepted_at=[NOW],
        now=NOW + timedelta(minutes=15),
    )
    assert decision.allowed
    assert len(state.accepted_at) == 2


def test_fourth_email_request_in_rolling_hour_blocked():
    accepted = [
        NOW - timedelta(minutes=46),
        NOW - timedelta(minutes=30),
        NOW - timedelta(minutes=15),
    ]
    decision, state = security.evaluate_rate_limit(
        dimension="email", accepted_at=accepted, now=NOW
    )
    assert decision.reason is security.RateLimitReason.HOURLY_LIMIT
    assert len(state.accepted_at) == 3


def test_seventh_email_request_in_rolling_day_blocked():
    accepted = [NOW - timedelta(hours=23 - index * 3) for index in range(6)]
    decision, state = security.evaluate_rate_limit(
        dimension="email", accepted_at=accepted, now=NOW
    )
    assert decision.reason is security.RateLimitReason.DAILY_LIMIT
    assert len(state.accepted_at) == 6


def test_timestamps_at_or_older_than_24_hours_are_pruned():
    decision, state = security.evaluate_rate_limit(
        dimension="email",
        accepted_at=[
            NOW - timedelta(days=2),
            NOW - timedelta(hours=24),
            NOW - timedelta(minutes=20),
        ],
        now=NOW,
    )
    assert decision.allowed
    assert state.accepted_at == (NOW - timedelta(minutes=20), NOW)


def test_ip_has_no_email_cooldown():
    decision, state = security.evaluate_rate_limit(
        dimension="ip", accepted_at=[NOW - timedelta(seconds=1)], now=NOW
    )
    assert decision.allowed
    assert len(state.accepted_at) == 2


def test_eleventh_ip_request_in_hour_blocked():
    accepted = [NOW - timedelta(minutes=50 - index * 5) for index in range(10)]
    decision, state = security.evaluate_rate_limit(
        dimension="ip", accepted_at=accepted, now=NOW
    )
    assert decision.reason is security.RateLimitReason.HOURLY_LIMIT
    assert len(state.accepted_at) == 10


def test_fifty_first_ip_request_in_day_blocked():
    accepted = [NOW - timedelta(minutes=20 * (index + 1)) for index in range(50)]
    decision, state = security.evaluate_rate_limit(
        dimension="ip", accepted_at=accepted, now=NOW
    )
    assert decision.reason is security.RateLimitReason.DAILY_LIMIT
    assert len(state.accepted_at) == 50


@async_test
async def test_allowed_reservation_persists_only_approved_fields():
    collection = FakeRateLimitCollection()
    repository = security.NewsletterRateLimitRepository(collection)
    decision = await repository.reserve_request(
        dimension="email",
        subject_hash=security.hash_normalized_email(EMAIL),
        operation="preferences",
        now=NOW,
    )
    assert decision.allowed
    assert set(next(iter(collection.documents.values()))) == {
        "dimension",
        "hash",
        "operation",
        "accepted_at",
        "last_accepted_at",
        "expires_at",
    }


@async_test
async def test_blocked_reservation_does_not_append():
    collection = FakeRateLimitCollection()
    repository = security.NewsletterRateLimitRepository(collection)
    kwargs = {
        "dimension": "email",
        "subject_hash": security.hash_normalized_email(EMAIL),
        "operation": "preferences",
    }
    await repository.reserve_request(**kwargs, now=NOW)
    blocked = await repository.reserve_request(
        **kwargs, now=NOW + timedelta(minutes=1)
    )
    assert blocked.reason is security.RateLimitReason.COOLDOWN
    assert collection.writes == 1


@async_test
async def test_rate_limit_storage_failure_fails_closed_safely():
    collection = FakeRateLimitCollection()
    collection.fail = True
    repository = security.NewsletterRateLimitRepository(collection)
    decision = await repository.reserve_request(
        dimension="ip",
        subject_hash=security.hash_source_ip(IP),
        operation="preferences",
        now=NOW,
    )
    assert decision.reason is security.RateLimitReason.STORAGE_ERROR
    assert "raw database" not in repr(decision)


@async_test
async def test_concurrent_reservations_cannot_exceed_limit():
    collection = FakeRateLimitCollection()
    repository = security.NewsletterRateLimitRepository(collection)
    subject_hash = security.hash_source_ip(IP)
    results = await asyncio.gather(
        *[
            repository.reserve_request(
                dimension="ip",
                subject_hash=subject_hash,
                operation="preferences",
                now=NOW,
            )
            for _ in range(11)
        ]
    )
    assert sum(result.allowed for result in results) == 10


@async_test
async def test_ip_reservation_is_not_rolled_back_by_email_failure():
    collection = FakeRateLimitCollection()
    repository = security.NewsletterRateLimitRepository(collection)
    ip_result = await repository.reserve_request(
        dimension="ip",
        subject_hash=security.hash_source_ip(IP),
        operation="preferences",
        now=NOW,
    )
    collection.fail = True
    email_result = await repository.reserve_request(
        dimension="email",
        subject_hash=security.hash_normalized_email(EMAIL),
        operation="preferences",
        now=NOW,
    )
    assert ip_result.allowed
    assert email_result.reason is security.RateLimitReason.STORAGE_ERROR
    assert collection.writes == 1


@pytest.mark.parametrize(
    "definition",
    security.RATE_LIMIT_INDEX_DEFINITIONS
    + security.CHALLENGE_INDEX_DEFINITIONS,
)
def test_exact_index_definitions_accepted(definition):
    security.validate_index_definition(
        exact_index_metadata(definition), definition
    )


@pytest.mark.parametrize("unique", ["true", "false", 1, 0, None, [], {}])
def test_unique_index_rejects_every_non_boolean_unique_value(unique):
    definition = security.RATE_LIMIT_UNIQUE_INDEX
    metadata = exact_index_metadata(definition)
    metadata["unique"] = unique
    with pytest.raises(security.NewsletterLinkIndexConflictError):
        security.validate_index_definition(metadata, definition)


def test_nonunique_index_accepts_only_absent_or_literal_false():
    definition = security.RATE_LIMIT_TTL_INDEX
    absent = exact_index_metadata(definition)
    security.validate_index_definition(absent, definition)
    explicit_false = {**absent, "unique": False}
    security.validate_index_definition(explicit_false, definition)


@pytest.mark.parametrize("unique", ["true", "false", 1, 0, None, [], {}])
def test_nonunique_index_rejects_non_boolean_unique_value(unique):
    definition = security.RATE_LIMIT_TTL_INDEX
    metadata = {**exact_index_metadata(definition), "unique": unique}
    with pytest.raises(security.NewsletterLinkIndexConflictError):
        security.validate_index_definition(metadata, definition)


@pytest.mark.parametrize(
    "direction",
    [True, False, "1", "-1", 0, 2, -2, None, [], {}, 1.0, -1.0],
)
def test_index_key_direction_rejects_non_exact_integer_values(direction):
    definition = security.CHALLENGE_TOKEN_HASH_UNIQUE_INDEX
    metadata = exact_index_metadata(definition)
    metadata["key"] = [("token_hash", direction)]
    with pytest.raises(security.NewsletterLinkIndexConflictError):
        security.validate_index_definition(metadata, definition)


@pytest.mark.parametrize("direction", [1, -1])
def test_index_key_direction_accepts_only_approved_integers(direction):
    definition = security.IndexDefinition(
        keys=(("token_hash", direction),),
        unique=True,
        name=f"test_direction_{direction}",
    )
    security.validate_index_definition(
        {
            "name": definition.name,
            "key": [("token_hash", direction)],
            "unique": True,
        },
        definition,
    )


@pytest.mark.parametrize(
    "mutation",
    [
        {"partialFilterExpression": {"active": True}},
        {"sparse": True},
        {"hidden": True},
        {"collation": {"locale": "en"}},
        {"name": "wrong"},
        {"key": [("wrong", 1)]},
        {"unexpectedSemanticOption": True},
    ],
)
def test_semantically_different_indexes_rejected(mutation):
    definition = security.RATE_LIMIT_UNIQUE_INDEX
    metadata = exact_index_metadata(definition)
    metadata.update(mutation)
    with pytest.raises(security.NewsletterLinkIndexConflictError):
        security.validate_index_definition(metadata, definition)


def test_nonunique_compound_and_wrong_ttl_rejected():
    unique_metadata = exact_index_metadata(security.RATE_LIMIT_UNIQUE_INDEX)
    unique_metadata["unique"] = False
    with pytest.raises(security.NewsletterLinkIndexConflictError):
        security.validate_index_definition(
            unique_metadata, security.RATE_LIMIT_UNIQUE_INDEX
        )
    ttl_metadata = exact_index_metadata(security.RATE_LIMIT_TTL_INDEX)
    ttl_metadata["expireAfterSeconds"] = 60
    with pytest.raises(security.NewsletterLinkIndexConflictError):
        security.validate_index_definition(
            ttl_metadata, security.RATE_LIMIT_TTL_INDEX
        )


def test_required_index_validator_rejects_missing_definition():
    with pytest.raises(security.NewsletterLinkIndexConflictError):
        security.validate_required_indexes(
            [], security.RATE_LIMIT_INDEX_DEFINITIONS
        )


@async_test
async def test_generated_filter_and_pipeline_are_exercised_for_first_insert():
    collection = FakeRateLimitCollection()
    repository = security.NewsletterRateLimitRepository(collection)
    subject_hash = security.hash_normalized_email(EMAIL)
    result = await repository.reserve_request(
        dimension="email",
        subject_hash=subject_hash,
        operation="preferences",
        now=NOW,
    )
    assert result.allowed
    assert collection.last_filter == {
        "dimension": "email",
        "hash": subject_hash,
        "operation": "preferences",
        "$expr": security._mongo_rate_limit_expression("email", NOW),
    }
    assert collection.last_pipeline == security._mongo_rate_limit_pipeline(NOW)
    stored = next(iter(collection.documents.values()))
    assert stored["accepted_at"] == [NOW]
    assert stored["last_accepted_at"] == NOW
    assert stored["expires_at"] == NOW + timedelta(hours=24)


@async_test
async def test_blocked_upsert_uses_duplicate_key_conflict_then_classifies():
    collection = FakeRateLimitCollection()
    repository = security.NewsletterRateLimitRepository(collection)
    arguments = {
        "dimension": "email",
        "subject_hash": security.hash_normalized_email(EMAIL),
        "operation": "preferences",
    }
    await repository.reserve_request(**arguments, now=NOW)
    blocked = await repository.reserve_request(
        **arguments, now=NOW + timedelta(minutes=1)
    )
    assert blocked.reason is security.RateLimitReason.COOLDOWN
    assert collection.duplicate_conflicts == 1
    assert collection.writes == 1


@async_test
async def test_generated_pipeline_prunes_rolling_day_state():
    collection = FakeRateLimitCollection()
    repository = security.NewsletterRateLimitRepository(collection)
    subject_hash = security.hash_normalized_email(EMAIL)
    identity = ("email", subject_hash, "preferences")
    collection.documents[identity] = {
        "dimension": "email",
        "hash": subject_hash,
        "operation": "preferences",
        "accepted_at": [
            NOW - timedelta(days=2),
            NOW - timedelta(hours=24),
            NOW - timedelta(minutes=20),
        ],
        "last_accepted_at": NOW - timedelta(minutes=20),
        "expires_at": NOW + timedelta(hours=4),
    }
    result = await repository.reserve_request(
        dimension="email",
        subject_hash=subject_hash,
        operation="preferences",
        now=NOW,
    )
    assert result.allowed
    assert collection.documents[identity]["accepted_at"] == [
        NOW - timedelta(minutes=20),
        NOW,
    ]


@async_test
async def test_generated_filter_accepts_exact_email_cooldown_boundary():
    collection = FakeRateLimitCollection()
    repository = security.NewsletterRateLimitRepository(collection)
    subject_hash = security.hash_normalized_email(EMAIL)
    identity = ("email", subject_hash, "preferences")
    collection.documents[identity] = {
        "dimension": "email",
        "hash": subject_hash,
        "operation": "preferences",
        "accepted_at": [NOW - timedelta(minutes=15)],
        "last_accepted_at": NOW - timedelta(minutes=15),
        "expires_at": NOW + timedelta(hours=23, minutes=45),
    }
    result = await repository.reserve_request(
        dimension="email",
        subject_hash=subject_hash,
        operation="preferences",
        now=NOW,
    )
    assert result.allowed
    assert collection.documents[identity]["accepted_at"][-1] == NOW


@async_test
async def test_generated_filter_rejects_email_hourly_boundary():
    collection = FakeRateLimitCollection()
    repository = security.NewsletterRateLimitRepository(collection)
    subject_hash = security.hash_normalized_email(EMAIL)
    identity = ("email", subject_hash, "preferences")
    accepted = [
        NOW - timedelta(minutes=59),
        NOW - timedelta(minutes=30),
        NOW - timedelta(minutes=15),
    ]
    collection.documents[identity] = {
        "dimension": "email",
        "hash": subject_hash,
        "operation": "preferences",
        "accepted_at": accepted,
        "last_accepted_at": accepted[-1],
        "expires_at": accepted[-1] + timedelta(hours=24),
    }
    result = await repository.reserve_request(
        dimension="email",
        subject_hash=subject_hash,
        operation="preferences",
        now=NOW,
    )
    assert result.reason is security.RateLimitReason.HOURLY_LIMIT
    assert collection.documents[identity]["accepted_at"] == accepted


@async_test
async def test_generated_filter_rejects_ip_daily_boundary():
    collection = FakeRateLimitCollection()
    repository = security.NewsletterRateLimitRepository(collection)
    subject_hash = security.hash_source_ip(IP)
    identity = ("ip", subject_hash, "preferences")
    accepted = [
        NOW - timedelta(minutes=20 + index * 25)
        for index in range(50)
    ]
    collection.documents[identity] = {
        "dimension": "ip",
        "hash": subject_hash,
        "operation": "preferences",
        "accepted_at": accepted,
        "last_accepted_at": max(accepted),
        "expires_at": max(accepted) + timedelta(hours=24),
    }
    result = await repository.reserve_request(
        dimension="ip",
        subject_hash=subject_hash,
        operation="preferences",
        now=NOW,
    )
    assert result.reason is security.RateLimitReason.DAILY_LIMIT
    assert collection.documents[identity]["accepted_at"] == accepted


@async_test
async def test_generated_filter_rejects_malformed_stored_timestamp_state():
    collection = FakeRateLimitCollection()
    repository = security.NewsletterRateLimitRepository(collection)
    subject_hash = security.hash_source_ip(IP)
    identity = ("ip", subject_hash, "preferences")
    collection.documents[identity] = {
        "dimension": "ip",
        "hash": subject_hash,
        "operation": "preferences",
        "accepted_at": "not-an-array",
        "last_accepted_at": NOW,
        "expires_at": NOW + timedelta(hours=24),
    }
    result = await repository.reserve_request(
        dimension="ip",
        subject_hash=subject_hash,
        operation="preferences",
        now=NOW,
    )
    assert result.reason is security.RateLimitReason.STORAGE_ERROR
    assert collection.writes == 0


def test_canonical_uuid_and_pending_challenge_contract():
    document = security.build_pending_challenge(
        token_hash=TOKEN_HASH,
        subscriber_management_id=MANAGEMENT_ID,
        purpose="preferences",
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=30),
    )
    assert set(document) == {
        "token_hash",
        "subscriber_management_id",
        "purpose",
        "issued_at",
        "expires_at",
        "consumed_at",
        "delivery_status",
    }
    assert document["delivery_status"] == "pending"
    assert TOKEN not in repr(document)


@pytest.mark.parametrize(
    "management_id",
    ["bad", str(uuid4()).upper(), "{" + str(uuid4()) + "}"],
)
def test_malformed_or_noncanonical_uuid_rejected(management_id):
    with pytest.raises(security.NewsletterLinkValidationError):
        security.build_pending_challenge(
            token_hash=TOKEN_HASH,
            subscriber_management_id=management_id,
            purpose="preferences",
            issued_at=NOW,
            expires_at=NOW + timedelta(minutes=1),
        )


@pytest.mark.parametrize("purpose", ["preferences", "unsubscribe", "reactivate"])
def test_all_approved_challenge_purposes(purpose):
    document = security.build_pending_challenge(
        token_hash=TOKEN_HASH,
        subscriber_management_id=MANAGEMENT_ID,
        purpose=purpose,
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
    )
    assert document["purpose"] == purpose


def test_invalid_challenge_purpose_and_delivery_state_rejected():
    with pytest.raises(security.NewsletterLinkValidationError):
        security.build_pending_challenge(
            token_hash=TOKEN_HASH,
            subscriber_management_id=MANAGEMENT_ID,
            purpose="admin",
            issued_at=NOW,
            expires_at=NOW + timedelta(minutes=1),
        )
    with pytest.raises(security.NewsletterLinkValidationError):
        security._validate_delivery_status("sent")


@pytest.mark.parametrize(
    "consumed_at",
    [NOW.replace(tzinfo=None), True, 1, "2026-07-19T12:00:00Z"],
)
def test_invalid_consumed_timestamp_types_rejected(consumed_at):
    record = dict(
        security.build_pending_challenge(
            token_hash=TOKEN_HASH,
            subscriber_management_id=MANAGEMENT_ID,
            purpose="preferences",
            issued_at=NOW,
            expires_at=NOW + timedelta(minutes=1),
        )
    )
    record["consumed_at"] = consumed_at
    with pytest.raises(security.NewsletterLinkValidationError):
        security.validate_challenge_record(record)


def test_valid_consumed_timestamp_and_delivery_states_are_accepted():
    for status in security.ALLOWED_DELIVERY_STATUSES:
        record = dict(
            security.build_pending_challenge(
                token_hash=TOKEN_HASH,
                subscriber_management_id=MANAGEMENT_ID,
                purpose="preferences",
                issued_at=NOW,
                expires_at=NOW + timedelta(minutes=2),
            )
        )
        record["consumed_at"] = NOW + timedelta(minutes=1)
        record["delivery_status"] = status
        validated = security.validate_challenge_record(record)
        assert validated["consumed_at"] == NOW + timedelta(minutes=1)
        assert validated["delivery_status"] == status


def test_challenge_record_rejects_unapproved_extra_fields():
    record = dict(
        security.build_pending_challenge(
            token_hash=TOKEN_HASH,
            subscriber_management_id=MANAGEMENT_ID,
            purpose="preferences",
            issued_at=NOW,
            expires_at=NOW + timedelta(minutes=1),
        )
    )
    record["email"] = "private@example.invalid"
    with pytest.raises(security.NewsletterLinkValidationError):
        security.validate_challenge_record(record)


@pytest.mark.parametrize(
    "issued,expires",
    [
        (NOW, NOW),
        (NOW, NOW - timedelta(seconds=1)),
        (NOW.replace(tzinfo=None), NOW + timedelta(minutes=1)),
        (NOW, (NOW + timedelta(minutes=1)).replace(tzinfo=None)),
    ],
)
def test_invalid_challenge_times_rejected(issued, expires):
    with pytest.raises(security.NewsletterLinkValidationError):
        security.build_pending_challenge(
            token_hash=TOKEN_HASH,
            subscriber_management_id=MANAGEMENT_ID,
            purpose="preferences",
            issued_at=issued,
            expires_at=expires,
        )


def test_raw_token_cannot_be_used_as_stored_hash():
    with pytest.raises(security.NewsletterLinkValidationError):
        security.build_pending_challenge(
            token_hash=TOKEN,
            subscriber_management_id=MANAGEMENT_ID,
            purpose="preferences",
            issued_at=NOW,
            expires_at=NOW + timedelta(minutes=1),
        )


@async_test
async def test_create_pending_stores_only_approved_fields_and_duplicate_is_safe():
    collection = FakeChallengeCollection()
    repository = security.NewsletterChallengeRepository(collection)
    kwargs = {
        "token_hash": TOKEN_HASH,
        "subscriber_management_id": MANAGEMENT_ID,
        "purpose": "preferences",
        "issued_at": NOW,
        "expires_at": NOW + timedelta(minutes=30),
    }
    assert (await repository.create_pending(**kwargs)).succeeded
    duplicate = await repository.create_pending(**kwargs)
    assert duplicate.reason is security.ChallengeResultReason.DUPLICATE
    stored = collection.documents[TOKEN_HASH]
    assert set(stored) == set(security.build_pending_challenge(**kwargs))
    assert "email" not in stored
    assert "preferences" not in stored


@async_test
async def test_pending_delivery_lifecycle_transitions():
    repository, collection = challenge_repository()
    delivered = await repository.mark_delivered(TOKEN_HASH)
    assert delivered.reason is security.ChallengeResultReason.DELIVERED
    assert collection.documents[TOKEN_HASH]["delivery_status"] == "delivered"
    assert not (await repository.mark_failed(TOKEN_HASH)).succeeded


@async_test
async def test_pending_can_fail_and_failed_cannot_deliver():
    repository, collection = challenge_repository()
    failed = await repository.mark_failed(TOKEN_HASH)
    assert failed.reason is security.ChallengeResultReason.FAILED
    assert collection.documents[TOKEN_HASH]["delivery_status"] == "failed"
    assert not (await repository.mark_delivered(TOKEN_HASH)).succeeded


@async_test
async def test_consumed_challenge_delivery_cannot_change():
    repository, _ = challenge_repository(
        consumed_at=NOW - timedelta(minutes=1)
    )
    assert not (await repository.mark_delivered(TOKEN_HASH)).succeeded
    assert not (await repository.mark_failed(TOKEN_HASH)).succeeded


@async_test
async def test_delivery_storage_failure_fails_closed_without_details():
    repository, collection = challenge_repository()
    collection.fail = True
    result = await repository.mark_delivered(TOKEN_HASH)
    assert result.reason is security.ChallengeResultReason.STORAGE_ERROR
    assert "raw" not in repr(result)


@async_test
async def test_delivered_preference_challenge_is_read_without_consumption():
    repository, collection = challenge_repository(
        status=security.DELIVERED_DELIVERY
    )
    result = await repository.read_eligible_preference(
        token_hash=TOKEN_HASH, now=NOW + timedelta(minutes=1)
    )
    assert result.reason is security.ChallengeResultReason.ELIGIBLE
    assert collection.documents[TOKEN_HASH]["consumed_at"] is None


@pytest.mark.parametrize(
    "status,consumed,now",
    [
        ("pending", None, NOW + timedelta(minutes=1)),
        ("failed", None, NOW + timedelta(minutes=1)),
        ("delivered", NOW, NOW + timedelta(minutes=1)),
        ("delivered", None, NOW + timedelta(hours=1)),
    ],
)
@async_test
async def test_ineligible_preference_challenges_rejected(status, consumed, now):
    repository, _ = challenge_repository(status=status, consumed_at=consumed)
    result = await repository.read_eligible_preference(
        token_hash=TOKEN_HASH, now=now
    )
    assert result.reason is security.ChallengeResultReason.NOT_ELIGIBLE


@async_test
async def test_wrong_purpose_cannot_be_consumed():
    repository, _ = challenge_repository(
        status=security.DELIVERED_DELIVERY
    )
    result = await repository.consume(
        token_hash=TOKEN_HASH,
        expected_purpose="unsubscribe",
        now=NOW + timedelta(minutes=1),
    )
    assert result.reason is security.ChallengeResultReason.NOT_ELIGIBLE


@async_test
async def test_atomic_consume_succeeds_once_and_only_changes_consumed_at():
    repository, collection = challenge_repository(
        status=security.DELIVERED_DELIVERY
    )
    before = deepcopy(collection.documents[TOKEN_HASH])
    first, second = await asyncio.gather(
        repository.consume(
            token_hash=TOKEN_HASH,
            expected_purpose="preferences",
            now=NOW + timedelta(minutes=1),
        ),
        repository.consume(
            token_hash=TOKEN_HASH,
            expected_purpose="preferences",
            now=NOW + timedelta(minutes=1),
        ),
    )
    assert sum(result.succeeded for result in (first, second)) == 1
    after = collection.documents[TOKEN_HASH]
    changed = {key for key in before if before[key] != after[key]}
    assert changed == {"consumed_at"}


@async_test
async def test_failed_challenge_cannot_be_consumed():
    repository, _ = challenge_repository(status=security.FAILED_DELIVERY)
    result = await repository.consume(
        token_hash=TOKEN_HASH,
        expected_purpose="preferences",
        now=NOW + timedelta(minutes=1),
    )
    assert result.reason is security.ChallengeResultReason.NOT_ELIGIBLE


@async_test
async def test_challenge_storage_failure_fails_closed():
    repository, collection = challenge_repository(
        status=security.DELIVERED_DELIVERY
    )
    collection.fail = True
    result = await repository.consume(
        token_hash=TOKEN_HASH,
        expected_purpose="preferences",
        now=NOW + timedelta(minutes=1),
    )
    assert result.reason is security.ChallengeResultReason.STORAGE_ERROR


def test_module_has_no_environment_database_email_or_runtime_imports():
    source = Path(security.__file__).read_text()
    assert "os.environ" not in source
    assert "AsyncIOMotorClient" not in source
    assert "MongoClient(" not in source
    assert "backend.server" not in source
    assert "email_service" not in source
    assert "create_index(" not in source
    assert "logging." not in source


def test_runtime_modules_do_not_import_isolated_module():
    root = Path(__file__).resolve().parents[1]
    for relative in (
        "backend/server.py",
        "backend/app/email_service.py",
        "backend/scheduler/tasks.py",
        "backend/scripts/migrate_newsletter_management_ids.py",
    ):
        assert "newsletter_link_security" not in (root / relative).read_text()


def test_import_performs_no_index_or_collection_work():
    source = inspect.getsource(security)
    assert ".create_index(" not in source
    assert "create_collection" not in source
    collection = FakeChallengeCollection()
    assert collection.index_calls == 0


def test_errors_and_logs_contain_no_private_values(caplog):
    caplog.set_level(logging.DEBUG)
    with pytest.raises(security.NewsletterLinkValidationError) as error:
        security.build_pending_challenge(
            token_hash=TOKEN,
            subscriber_management_id=MANAGEMENT_ID,
            purpose="preferences",
            issued_at=NOW,
            expires_at=NOW + timedelta(minutes=1),
        )
    combined = str(error.value) + caplog.text
    assert TOKEN not in combined
    assert MANAGEMENT_ID not in combined
    assert EMAIL.strip() not in combined
    assert IP not in combined
