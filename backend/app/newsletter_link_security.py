"""Storage contracts and privacy-safe helpers for secure newsletter links.

This module owns no database client, reads no environment variables, sends no
email, and creates no indexes. Callers must inject MongoDB-like collections
explicitly.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from types import MappingProxyType
from typing import Final, Iterable, Mapping, Sequence
from uuid import UUID

try:
    from pymongo import ReturnDocument
    from pymongo.errors import DuplicateKeyError
except ImportError:  # pragma: no cover - production requirements include PyMongo
    class ReturnDocument:  # type: ignore[no-redef]
        AFTER = True

    class DuplicateKeyError(Exception):  # type: ignore[no-redef]
        pass


RATE_LIMIT_COLLECTION_NAME: Final = "newsletter_link_request_limits"
CHALLENGE_COLLECTION_NAME: Final = "newsletter_link_challenges"

EMAIL_DIMENSION: Final = "email"
IP_DIMENSION: Final = "ip"
ALLOWED_DIMENSIONS: Final = frozenset({EMAIL_DIMENSION, IP_DIMENSION})

PREFERENCES_OPERATION: Final = "preferences"
UNSUBSCRIBE_OPERATION: Final = "unsubscribe"
REACTIVATE_OPERATION: Final = "reactivate"
ALLOWED_OPERATIONS: Final = frozenset(
    {PREFERENCES_OPERATION, UNSUBSCRIBE_OPERATION, REACTIVATE_OPERATION}
)

PENDING_DELIVERY: Final = "pending"
DELIVERED_DELIVERY: Final = "delivered"
FAILED_DELIVERY: Final = "failed"
ALLOWED_DELIVERY_STATUSES: Final = frozenset(
    {PENDING_DELIVERY, DELIVERED_DELIVERY, FAILED_DELIVERY}
)

EMAIL_COOLDOWN: Final = timedelta(minutes=15)
ROLLING_HOUR: Final = timedelta(hours=1)
ROLLING_DAY: Final = timedelta(hours=24)
EMAIL_HOURLY_LIMIT: Final = 3
EMAIL_DAILY_LIMIT: Final = 6
IP_HOURLY_LIMIT: Final = 10
IP_DAILY_LIMIT: Final = 50

_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")


class NewsletterLinkSecurityError(Exception):
    """Base class for safe, redacted repository failures."""


class NewsletterLinkValidationError(NewsletterLinkSecurityError):
    """Input does not satisfy the frozen storage contract."""


class NewsletterLinkStorageError(NewsletterLinkSecurityError):
    """A storage operation failed without exposing database details."""


class NewsletterLinkDuplicateChallengeError(NewsletterLinkSecurityError):
    """A challenge token hash already exists."""


class NewsletterLinkIndexConflictError(NewsletterLinkSecurityError):
    """An existing index is not semantically identical to the requirement."""


class RateLimitReason(str, Enum):
    ALLOWED = "allowed"
    COOLDOWN = "cooldown"
    HOURLY_LIMIT = "hourly_limit"
    DAILY_LIMIT = "daily_limit"
    INVALID_INPUT = "invalid_input"
    STORAGE_ERROR = "storage_error"


class ChallengeResultReason(str, Enum):
    CREATED = "created"
    DELIVERED = "delivered"
    FAILED = "failed"
    ELIGIBLE = "eligible"
    CONSUMED = "consumed"
    NOT_ELIGIBLE = "not_eligible"
    DUPLICATE = "duplicate"
    STORAGE_ERROR = "storage_error"


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    reason: RateLimitReason
    next_eligible_at: datetime | None = None


@dataclass(frozen=True)
class RateLimitState:
    accepted_at: tuple[datetime, ...]
    last_accepted_at: datetime | None
    expires_at: datetime


@dataclass(frozen=True)
class ChallengeResult:
    succeeded: bool
    reason: ChallengeResultReason


@dataclass(frozen=True)
class IndexDefinition:
    keys: tuple[tuple[str, int], ...]
    name: str
    unique: bool | None = None
    expire_after_seconds: int | None = None


RATE_LIMIT_UNIQUE_INDEX: Final = IndexDefinition(
    keys=(("dimension", 1), ("hash", 1), ("operation", 1)),
    unique=True,
    name="newsletter_link_request_limit_unique",
)
RATE_LIMIT_TTL_INDEX: Final = IndexDefinition(
    keys=(("expires_at", 1),),
    expire_after_seconds=0,
    name="newsletter_link_request_limit_ttl",
)
CHALLENGE_TOKEN_HASH_UNIQUE_INDEX: Final = IndexDefinition(
    keys=(("token_hash", 1),),
    unique=True,
    name="newsletter_link_challenge_token_hash_unique",
)
CHALLENGE_TTL_INDEX: Final = IndexDefinition(
    keys=(("expires_at", 1),),
    expire_after_seconds=0,
    name="newsletter_link_challenge_ttl",
)

RATE_LIMIT_INDEX_DEFINITIONS: Final = (
    RATE_LIMIT_UNIQUE_INDEX,
    RATE_LIMIT_TTL_INDEX,
)
CHALLENGE_INDEX_DEFINITIONS: Final = (
    CHALLENGE_TOKEN_HASH_UNIQUE_INDEX,
    CHALLENGE_TTL_INDEX,
)

_SEMANTIC_INDEX_OPTIONS: Final = frozenset(
    {
        "unique",
        "sparse",
        "partialFilterExpression",
        "hidden",
        "collation",
        "expireAfterSeconds",
    }
)


def _require_nonempty(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise NewsletterLinkValidationError(f"{label} is invalid.")
    return value.strip()


def _sha256_text(value: object, label: str) -> str:
    safe_value = _require_nonempty(value, label)
    return hashlib.sha256(safe_value.encode("utf-8")).hexdigest()


def normalize_email(email: object) -> str:
    return _require_nonempty(email, "Email").lower()


def hash_normalized_email(email: object) -> str:
    return hashlib.sha256(normalize_email(email).encode("utf-8")).hexdigest()


def hash_source_ip(source_ip: object) -> str:
    return _sha256_text(source_ip, "Source IP")


def hash_token(token: object) -> str:
    return _sha256_text(token, "Token")


def safe_fingerprint(value: object) -> str:
    return _sha256_text(value, "Value")[:12]


def _validate_hash(value: object, label: str = "Hash") -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise NewsletterLinkValidationError(f"{label} is invalid.")
    return value


def _validate_dimension(value: object) -> str:
    if not isinstance(value, str) or value not in ALLOWED_DIMENSIONS:
        raise NewsletterLinkValidationError("Rate-limit dimension is invalid.")
    return value


def _validate_operation(value: object) -> str:
    if not isinstance(value, str) or value not in ALLOWED_OPERATIONS:
        raise NewsletterLinkValidationError("Newsletter link operation is invalid.")
    return value


def _validate_delivery_status(value: object) -> str:
    if not isinstance(value, str) or value not in ALLOWED_DELIVERY_STATUSES:
        raise NewsletterLinkValidationError("Challenge delivery status is invalid.")
    return value


def _require_utc(value: object, label: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() != timedelta(0)
    ):
        raise NewsletterLinkValidationError(f"{label} must be UTC-aware.")
    return value


def _canonical_uuid4(value: object) -> str:
    if not isinstance(value, str):
        raise NewsletterLinkValidationError(
            "Subscriber management identifier is invalid."
        )
    try:
        parsed = UUID(value)
    except (ValueError, AttributeError, TypeError) as exc:
        raise NewsletterLinkValidationError(
            "Subscriber management identifier is invalid."
        ) from exc
    if parsed.version != 4 or str(parsed) != value:
        raise NewsletterLinkValidationError(
            "Subscriber management identifier is invalid."
        )
    return value


def _validate_positive_limit(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise NewsletterLinkValidationError(f"{label} is invalid.")
    return value


def _limits_for_dimension(dimension: str) -> tuple[timedelta | None, int, int]:
    if dimension == EMAIL_DIMENSION:
        return EMAIL_COOLDOWN, EMAIL_HOURLY_LIMIT, EMAIL_DAILY_LIMIT
    return None, IP_HOURLY_LIMIT, IP_DAILY_LIMIT


def evaluate_rate_limit(
    *,
    dimension: str,
    accepted_at: Iterable[datetime],
    now: datetime,
    cooldown: timedelta | None = None,
    hourly_limit: int | None = None,
    daily_limit: int | None = None,
) -> tuple[RateLimitDecision, RateLimitState]:
    """Pure rolling-window decision used by repositories and offline tests."""

    approved_dimension = _validate_dimension(dimension)
    current = _require_utc(now, "Current time")
    default_cooldown, default_hourly, default_daily = _limits_for_dimension(
        approved_dimension
    )
    effective_cooldown = default_cooldown if cooldown is None else cooldown
    effective_hourly = (
        default_hourly
        if hourly_limit is None
        else _validate_positive_limit(hourly_limit, "Hourly limit")
    )
    effective_daily = (
        default_daily
        if daily_limit is None
        else _validate_positive_limit(daily_limit, "Daily limit")
    )
    if effective_cooldown is not None and (
        not isinstance(effective_cooldown, timedelta)
        or effective_cooldown < timedelta(0)
    ):
        raise NewsletterLinkValidationError("Cooldown is invalid.")

    recent = sorted(
        (
            _require_utc(timestamp, "Accepted timestamp")
            for timestamp in accepted_at
            if _require_utc(timestamp, "Accepted timestamp")
            > current - ROLLING_DAY
        )
    )
    last = recent[-1] if recent else None
    expires_at = (last or current) + ROLLING_DAY

    if effective_cooldown and last and current < last + effective_cooldown:
        return (
            RateLimitDecision(
                False,
                RateLimitReason.COOLDOWN,
                last + effective_cooldown,
            ),
            RateLimitState(tuple(recent), last, expires_at),
        )

    hourly = [timestamp for timestamp in recent if timestamp > current - ROLLING_HOUR]
    if len(hourly) >= effective_hourly:
        return (
            RateLimitDecision(
                False,
                RateLimitReason.HOURLY_LIMIT,
                hourly[0] + ROLLING_HOUR,
            ),
            RateLimitState(tuple(recent), last, expires_at),
        )
    if len(recent) >= effective_daily:
        return (
            RateLimitDecision(
                False,
                RateLimitReason.DAILY_LIMIT,
                recent[0] + ROLLING_DAY,
            ),
            RateLimitState(tuple(recent), last, expires_at),
        )

    recent.append(current)
    return (
        RateLimitDecision(True, RateLimitReason.ALLOWED, current),
        RateLimitState(tuple(recent), current, current + ROLLING_DAY),
    )


def _mongo_rate_limit_pipeline(now: datetime) -> list[dict]:
    day_cutoff = now - ROLLING_DAY
    return [
        {
            "$set": {
                "accepted_at": {
                    "$concatArrays": [
                        {
                            "$filter": {
                                "input": {"$ifNull": ["$accepted_at", []]},
                                "as": "accepted",
                                "cond": {"$gt": ["$$accepted", day_cutoff]},
                            }
                        },
                        [now],
                    ]
                },
                "last_accepted_at": now,
                "expires_at": now + ROLLING_DAY,
            }
        }
    ]


def _mongo_rate_limit_expression(dimension: str, now: datetime) -> dict:
    cooldown, hourly_limit, daily_limit = _limits_for_dimension(dimension)
    recent_day = {
        "$filter": {
            "input": {"$ifNull": ["$accepted_at", []]},
            "as": "accepted",
            "cond": {"$gt": ["$$accepted", now - ROLLING_DAY]},
        }
    }
    recent_hour = {
        "$filter": {
            "input": {"$ifNull": ["$accepted_at", []]},
            "as": "accepted",
            "cond": {"$gt": ["$$accepted", now - ROLLING_HOUR]},
        }
    }
    conditions: list[dict] = [
        {"$lt": [{"$size": recent_hour}, hourly_limit]},
        {"$lt": [{"$size": recent_day}, daily_limit]},
    ]
    if cooldown:
        conditions.insert(
            0,
            {
                "$or": [
                    {"$eq": [{"$ifNull": ["$last_accepted_at", None]}, None]},
                    {
                        "$lte": [
                            "$last_accepted_at",
                            now - cooldown,
                        ]
                    },
                ]
            },
        )
    return {"$and": conditions}


class NewsletterRateLimitRepository:
    """Atomic reservation repository over an injected MongoDB-like collection."""

    def __init__(self, collection):
        self._collection = collection

    async def reserve_request(
        self,
        *,
        dimension: str,
        subject_hash: str,
        operation: str,
        now: datetime,
    ) -> RateLimitDecision:
        try:
            approved_dimension = _validate_dimension(dimension)
            approved_hash = _validate_hash(subject_hash, "Subject hash")
            approved_operation = _validate_operation(operation)
            current = _require_utc(now, "Current time")
        except NewsletterLinkValidationError:
            return RateLimitDecision(False, RateLimitReason.INVALID_INPUT)

        identity = {
            "dimension": approved_dimension,
            "hash": approved_hash,
            "operation": approved_operation,
        }
        atomic_filter = {
            **identity,
            "$expr": _mongo_rate_limit_expression(approved_dimension, current),
        }
        try:
            document = await self._collection.find_one_and_update(
                atomic_filter,
                _mongo_rate_limit_pipeline(current),
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
        except DuplicateKeyError:
            document = None
        except Exception:
            return RateLimitDecision(False, RateLimitReason.STORAGE_ERROR)

        if document is not None:
            return RateLimitDecision(True, RateLimitReason.ALLOWED, current)

        try:
            current_document = await self._collection.find_one(
                identity,
                {"_id": 0, "accepted_at": 1},
            )
            accepted = (
                current_document.get("accepted_at", [])
                if current_document
                else []
            )
            decision, _ = evaluate_rate_limit(
                dimension=approved_dimension,
                accepted_at=accepted,
                now=current,
            )
            return decision
        except Exception:
            return RateLimitDecision(False, RateLimitReason.STORAGE_ERROR)


def build_pending_challenge(
    *,
    token_hash: str,
    subscriber_management_id: str,
    purpose: str,
    issued_at: datetime,
    expires_at: datetime,
) -> Mapping[str, object]:
    approved_token_hash = _validate_hash(token_hash, "Token hash")
    approved_management_id = _canonical_uuid4(subscriber_management_id)
    approved_purpose = _validate_operation(purpose)
    issued = _require_utc(issued_at, "Issued time")
    expires = _require_utc(expires_at, "Expiry time")
    if expires <= issued:
        raise NewsletterLinkValidationError(
            "Challenge expiry must be later than issuance."
        )
    return MappingProxyType(
        {
            "token_hash": approved_token_hash,
            "subscriber_management_id": approved_management_id,
            "purpose": approved_purpose,
            "issued_at": issued,
            "expires_at": expires,
            "consumed_at": None,
            "delivery_status": PENDING_DELIVERY,
        }
    )


def validate_challenge_record(
    record: Mapping[str, object],
) -> Mapping[str, object]:
    """Validate an existing challenge without returning private extra fields."""

    expected_fields = {
        "token_hash",
        "subscriber_management_id",
        "purpose",
        "issued_at",
        "expires_at",
        "consumed_at",
        "delivery_status",
    }
    if not isinstance(record, Mapping) or set(record) != expected_fields:
        raise NewsletterLinkValidationError("Challenge record is invalid.")
    token_hash = _validate_hash(record["token_hash"], "Token hash")
    management_id = _canonical_uuid4(record["subscriber_management_id"])
    purpose = _validate_operation(record["purpose"])
    issued_at = _require_utc(record["issued_at"], "Issued time")
    expires_at = _require_utc(record["expires_at"], "Expiry time")
    if expires_at <= issued_at:
        raise NewsletterLinkValidationError(
            "Challenge expiry must be later than issuance."
        )
    consumed_value = record["consumed_at"]
    consumed_at = (
        None
        if consumed_value is None
        else _require_utc(consumed_value, "Consumed time")
    )
    delivery_status = _validate_delivery_status(record["delivery_status"])
    return MappingProxyType(
        {
            "token_hash": token_hash,
            "subscriber_management_id": management_id,
            "purpose": purpose,
            "issued_at": issued_at,
            "expires_at": expires_at,
            "consumed_at": consumed_at,
            "delivery_status": delivery_status,
        }
    )


class NewsletterChallengeRepository:
    """Lifecycle operations over an injected challenge collection."""

    def __init__(self, collection):
        self._collection = collection

    async def create_pending(
        self,
        *,
        token_hash: str,
        subscriber_management_id: str,
        purpose: str,
        issued_at: datetime,
        expires_at: datetime,
    ) -> ChallengeResult:
        document = dict(
            build_pending_challenge(
                token_hash=token_hash,
                subscriber_management_id=subscriber_management_id,
                purpose=purpose,
                issued_at=issued_at,
                expires_at=expires_at,
            )
        )
        try:
            await self._collection.insert_one(document)
            return ChallengeResult(True, ChallengeResultReason.CREATED)
        except DuplicateKeyError:
            return ChallengeResult(False, ChallengeResultReason.DUPLICATE)
        except Exception:
            return ChallengeResult(False, ChallengeResultReason.STORAGE_ERROR)

    async def _mark_delivery(
        self,
        token_hash: str,
        delivery_status: str,
    ) -> ChallengeResult:
        approved_hash = _validate_hash(token_hash, "Token hash")
        approved_status = _validate_delivery_status(delivery_status)
        if approved_status not in {DELIVERED_DELIVERY, FAILED_DELIVERY}:
            raise NewsletterLinkValidationError(
                "Challenge delivery transition is invalid."
            )
        try:
            result = await self._collection.update_one(
                {
                    "token_hash": approved_hash,
                    "delivery_status": PENDING_DELIVERY,
                    "consumed_at": None,
                },
                {"$set": {"delivery_status": approved_status}},
            )
        except Exception:
            return ChallengeResult(False, ChallengeResultReason.STORAGE_ERROR)
        if result.matched_count != 1:
            return ChallengeResult(False, ChallengeResultReason.NOT_ELIGIBLE)
        reason = (
            ChallengeResultReason.DELIVERED
            if approved_status == DELIVERED_DELIVERY
            else ChallengeResultReason.FAILED
        )
        return ChallengeResult(True, reason)

    async def mark_delivered(self, token_hash: str) -> ChallengeResult:
        return await self._mark_delivery(token_hash, DELIVERED_DELIVERY)

    async def mark_failed(self, token_hash: str) -> ChallengeResult:
        return await self._mark_delivery(token_hash, FAILED_DELIVERY)

    async def read_eligible_preference(
        self,
        *,
        token_hash: str,
        subscriber_management_id: str,
        now: datetime,
        session=None,
    ) -> ChallengeResult:
        approved_hash = _validate_hash(token_hash, "Token hash")
        approved_management_id = _canonical_uuid4(subscriber_management_id)
        current = _require_utc(now, "Current time")
        session_options = {"session": session} if session is not None else {}
        try:
            document = await self._collection.find_one(
                {
                    "token_hash": approved_hash,
                    "subscriber_management_id": approved_management_id,
                    "purpose": PREFERENCES_OPERATION,
                    "delivery_status": DELIVERED_DELIVERY,
                    "consumed_at": None,
                    "expires_at": {"$gt": current},
                },
                {"_id": 1},
                **session_options,
            )
        except Exception:
            return ChallengeResult(False, ChallengeResultReason.STORAGE_ERROR)
        if not document:
            return ChallengeResult(False, ChallengeResultReason.NOT_ELIGIBLE)
        return ChallengeResult(True, ChallengeResultReason.ELIGIBLE)

    async def consume(
        self,
        *,
        token_hash: str,
        expected_purpose: str,
        now: datetime,
    ) -> ChallengeResult:
        approved_hash = _validate_hash(token_hash, "Token hash")
        approved_purpose = _validate_operation(expected_purpose)
        current = _require_utc(now, "Current time")
        try:
            document = await self._collection.find_one_and_update(
                {
                    "token_hash": approved_hash,
                    "purpose": approved_purpose,
                    "delivery_status": DELIVERED_DELIVERY,
                    "consumed_at": None,
                    "expires_at": {"$gt": current},
                },
                {"$set": {"consumed_at": current}},
                return_document=ReturnDocument.AFTER,
            )
        except Exception:
            return ChallengeResult(False, ChallengeResultReason.STORAGE_ERROR)
        if not document:
            return ChallengeResult(False, ChallengeResultReason.NOT_ELIGIBLE)
        return ChallengeResult(True, ChallengeResultReason.CONSUMED)


def _normalise_index_keys(metadata: Mapping[str, object]) -> tuple[tuple[str, int], ...]:
    raw_keys = metadata.get("key")
    if isinstance(raw_keys, Mapping):
        items = tuple(raw_keys.items())
    if isinstance(raw_keys, Sequence) and not isinstance(raw_keys, (str, bytes)):
        items = tuple(raw_keys)
    elif not isinstance(raw_keys, Mapping):
        raise NewsletterLinkIndexConflictError("Index definition conflicts.")

    normalised = []
    for item in items:
        if (
            not isinstance(item, Sequence)
            or isinstance(item, (str, bytes))
            or len(item) != 2
        ):
            raise NewsletterLinkIndexConflictError(
                "Index definition conflicts."
            )
        key, direction = item
        if (
            not isinstance(key, str)
            or type(direction) is not int
            or direction not in {-1, 1}
        ):
            raise NewsletterLinkIndexConflictError(
                "Index definition conflicts."
            )
        normalised.append((key, direction))
    return tuple(normalised)


def validate_index_definition(
    metadata: Mapping[str, object],
    expected: IndexDefinition,
) -> None:
    """Accept only a semantically exact future index definition."""

    try:
        if metadata.get("name") != expected.name:
            raise NewsletterLinkIndexConflictError("Index definition conflicts.")
        if _normalise_index_keys(metadata) != expected.keys:
            raise NewsletterLinkIndexConflictError("Index definition conflicts.")
        if expected.unique is True:
            if metadata.get("unique") is not True:
                raise NewsletterLinkIndexConflictError(
                    "Index definition conflicts."
                )
        elif "unique" in metadata and metadata["unique"] is not False:
            raise NewsletterLinkIndexConflictError(
                "Index definition conflicts."
            )
        if expected.expire_after_seconds is None:
            if "expireAfterSeconds" in metadata:
                raise NewsletterLinkIndexConflictError(
                    "Index definition conflicts."
                )
        elif (
            type(metadata.get("expireAfterSeconds")) is not int
            or metadata.get("expireAfterSeconds")
            != expected.expire_after_seconds
        ):
            raise NewsletterLinkIndexConflictError(
                "Index definition conflicts."
            )
        if metadata.get("sparse", False):
            raise NewsletterLinkIndexConflictError("Index definition conflicts.")
        if metadata.get("hidden", False):
            raise NewsletterLinkIndexConflictError("Index definition conflicts.")
        if "partialFilterExpression" in metadata:
            raise NewsletterLinkIndexConflictError("Index definition conflicts.")
        if "collation" in metadata:
            raise NewsletterLinkIndexConflictError("Index definition conflicts.")
        allowed = {"name", "key", "v", "ns", "background"} | _SEMANTIC_INDEX_OPTIONS
        if any(key not in allowed for key in metadata):
            raise NewsletterLinkIndexConflictError("Index definition conflicts.")
    except NewsletterLinkIndexConflictError:
        raise
    except Exception as exc:
        raise NewsletterLinkIndexConflictError(
            "Index definition conflicts."
        ) from exc


def validate_required_indexes(
    existing: Iterable[Mapping[str, object]],
    expected: Iterable[IndexDefinition],
) -> None:
    by_name = {
        str(metadata.get("name")): metadata
        for metadata in existing
        if metadata.get("name")
    }
    for definition in expected:
        metadata = by_name.get(definition.name)
        if metadata is None:
            raise NewsletterLinkIndexConflictError(
                "Required index definition is missing."
            )
        validate_index_definition(metadata, definition)
