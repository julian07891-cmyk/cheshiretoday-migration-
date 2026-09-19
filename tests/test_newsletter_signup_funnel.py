import asyncio
import logging
from datetime import datetime, timezone

import pytest

from backend.app.newsletter_signup_funnel import (
    CANONICAL_PLACEMENTS,
    NEWSLETTER_SIGNUP_FUNNEL_INDEXES,
    ensure_newsletter_signup_funnel_indexes,
    newsletter_signup_funnel_period,
    normalise_newsletter_signup_placement,
    record_newsletter_signup_outcome,
    record_newsletter_signup_outcome_safely,
)


class RecordingCollection:
    def __init__(self, error=None):
        self.error = error
        self.updates = []
        self.indexes = []

    async def update_one(self, query, update, upsert=False):
        if self.error:
            raise self.error
        self.updates.append((query, update, upsert))

    async def create_index(self, keys, **options):
        self.indexes.append((keys, options))


class Database:
    def __init__(self, collection):
        self.newsletter_signup_funnel_daily = collection


@pytest.mark.parametrize("placement", sorted(CANONICAL_PLACEMENTS))
def test_canonical_placements_remain_canonical(placement):
    assert normalise_newsletter_signup_placement(placement) == placement


@pytest.mark.parametrize(
    "placement", [None, "", "website", " Homepage ", "unknown-value", 42, {}]
)
def test_missing_legacy_and_malformed_placements_are_unknown(placement):
    assert normalise_newsletter_signup_placement(placement) == "unknown"


@pytest.mark.parametrize("outcome", ["created", "existing", "failed"])
def test_one_atomic_update_records_one_attempt_and_one_outcome(outcome):
    collection = RecordingCollection()
    now = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)

    asyncio.run(
        record_newsletter_signup_outcome(collection, "footer", outcome, now=now)
    )

    assert len(collection.updates) == 1
    query, update, upsert = collection.updates[0]
    assert query == {"date_key": "2026-01-15", "placement": "footer"}
    assert upsert is True
    expected_inc = {
        "attempts": 1,
        "created": 1 if outcome == "created" else 0,
        "existing": 1 if outcome == "existing" else 0,
        "failed": 1 if outcome == "failed" else 0,
        "server_error": 1 if outcome == "failed" else 0,
    }
    assert update["$inc"] == expected_inc
    assert set(update) == {"$inc", "$set", "$setOnInsert"}
    assert set(update["$setOnInsert"]) == {
        "schema_version",
        "date_key",
        "day_start_utc",
        "placement",
        "created_at",
    }
    assert set(update["$set"]) == {"updated_at", "expires_at"}
    assert (
        set(update["$inc"])
        | set(update["$set"])
        | set(update["$setOnInsert"])
    ) == {
        "schema_version",
        "date_key",
        "day_start_utc",
        "placement",
        "attempts",
        "created",
        "existing",
        "failed",
        "server_error",
        "created_at",
        "updated_at",
        "expires_at",
    }
    rendered = repr((query, update)).lower()
    for prohibited in (
        "email",
        "hash",
        "ip",
        "user_agent",
        "session",
        "page_url",
        "article_id",
        "utm",
        "request_body",
    ):
        assert prohibited not in rendered


def test_retries_are_independent_atomic_attempts():
    collection = RecordingCollection()
    for _ in range(2):
        asyncio.run(record_newsletter_signup_outcome(collection, "popup", "existing"))
    assert len(collection.updates) == 2
    assert all(
        update[1]["$inc"]
        == {
            "attempts": 1,
            "created": 0,
            "existing": 1,
            "failed": 0,
            "server_error": 0,
        }
        for update in collection.updates
    )


@pytest.mark.parametrize(
    ("now", "date_key", "day_start", "expires_at"),
    [
        (
            datetime(2026, 1, 15, 12, tzinfo=timezone.utc),
            "2026-01-15",
            datetime(2026, 1, 15, 0, tzinfo=timezone.utc),
            datetime(2027, 2, 15, 0, tzinfo=timezone.utc),
        ),
        (
            datetime(2026, 7, 15, 12, tzinfo=timezone.utc),
            "2026-07-15",
            datetime(2026, 7, 14, 23, tzinfo=timezone.utc),
            datetime(2027, 8, 14, 23, tzinfo=timezone.utc),
        ),
        (
            datetime(2026, 3, 29, 0, 30, tzinfo=timezone.utc),
            "2026-03-29",
            datetime(2026, 3, 29, 0, tzinfo=timezone.utc),
            datetime(2027, 4, 28, 23, tzinfo=timezone.utc),
        ),
        (
            datetime(2026, 3, 29, 23, 30, tzinfo=timezone.utc),
            "2026-03-30",
            datetime(2026, 3, 29, 23, tzinfo=timezone.utc),
            datetime(2027, 4, 29, 23, tzinfo=timezone.utc),
        ),
    ],
)
def test_london_day_and_exact_calendar_retention(now, date_key, day_start, expires_at):
    period = newsletter_signup_funnel_period(now)
    assert period["date_key"] == date_key
    assert period["day_start_utc"] == day_start
    assert period["expires_at"] == expires_at


def test_indexes_are_exact_and_idempotently_requested():
    collection = RecordingCollection()
    asyncio.run(ensure_newsletter_signup_funnel_indexes(collection))
    asyncio.run(ensure_newsletter_signup_funnel_indexes(collection))
    expected = [
        (index["keys"], index["options"])
        for index in NEWSLETTER_SIGNUP_FUNNEL_INDEXES
    ]
    assert collection.indexes == expected + expected
    assert expected[0][1]["unique"] is True
    assert expected[1][1]["expireAfterSeconds"] == 0
    assert expected[2][0] == [("day_start_utc", 1), ("placement", 1)]


def test_measurement_failure_is_fail_open_and_bounded(caplog):
    database = Database(RecordingCollection(RuntimeError("private email value")))
    with caplog.at_level(logging.WARNING):
        recorded = asyncio.run(
            record_newsletter_signup_outcome_safely(
                database, "article", "created", logger=logging.getLogger("test")
            )
        )
    assert recorded is False
    assert "private email value" not in caplog.text
    assert "article" not in caplog.text
    assert "outcome=created" in caplog.text
