import asyncio
import os
from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from pymongo.errors import DuplicateKeyError


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


def _matches(document, query):
    for key, expected in query.items():
        actual = document.get(key)
        if isinstance(expected, dict) and "$in" in expected:
            if actual not in expected["$in"]:
                return False
        elif actual != expected:
            return False
    return True


class Result:
    def __init__(self, *, inserted_id=None, matched_count=1, modified_count=0):
        self.inserted_id = inserted_id
        self.matched_count = matched_count
        self.modified_count = modified_count


class AsyncCursor:
    def __init__(self, rows):
        self.rows = list(rows)
        self.index = 0

    def limit(self, count):
        self.rows = self.rows[:count]
        return self

    async def to_list(self, length):
        return deepcopy(self.rows[:length])

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.rows):
            raise StopAsyncIteration
        row = deepcopy(self.rows[self.index])
        self.index += 1
        return row


class DigestLog:
    def __init__(self, documents=None):
        self.documents = deepcopy(documents or [])
        self.next_id = len(self.documents) + 1
        self.created_indexes = []
        self.indexes = {
            "digest_time_date_key_unique_v3",
            "digest_time_date_key_unique_sparse",
        }
        self.fail_completion_once = False

    @staticmethod
    def identity(document):
        return (
            document.get("digest_time"),
            document.get("date_key"),
            document.get("weekly_roundup_batch_slot"),
        )

    async def insert_one(self, document):
        identity = self.identity(document)
        if any(self.identity(existing) == identity for existing in self.documents):
            raise DuplicateKeyError("duplicate digest identity")
        stored = deepcopy(document)
        stored["_id"] = self.next_id
        self.next_id += 1
        self.documents.append(stored)
        return Result(inserted_id=stored["_id"])

    async def find_one(self, query):
        return next((deepcopy(row) for row in self.documents if _matches(row, query)), None)

    async def find_one_and_update(self, query, update, return_document=None):
        for row in self.documents:
            if _matches(row, query):
                row.update(deepcopy(update.get("$set", {})))
                for key in update.get("$unset", {}):
                    row.pop(key, None)
                return deepcopy(row)
        return None

    async def update_one(self, query, update, upsert=False):
        status = update.get("$set", {}).get("status")
        if self.fail_completion_once and status in {"sent", "partial", "failed"}:
            self.fail_completion_once = False
            raise RuntimeError("simulated completion persistence failure")
        for row in self.documents:
            if _matches(row, query):
                row.update(deepcopy(update.get("$set", {})))
                for key in update.get("$unset", {}):
                    row.pop(key, None)
                return Result(matched_count=1)
        return Result(matched_count=0)

    async def update_many(self, query, update):
        modified = 0
        for row in self.documents:
            if row.get("digest_time") != "WeeklyRoundup":
                continue
            if row.get("weekly_roundup_batch_slot") is None:
                row.update(deepcopy(update["$set"]))
                modified += 1
        return Result(modified_count=modified)

    def aggregate(self, _pipeline):
        grouped = {}
        for row in self.documents:
            if row.get("digest_time") is None or row.get("date_key") is None:
                continue
            identity = self.identity(row)
            grouped.setdefault(identity, []).append(row)
        duplicates = []
        for identity, rows in grouped.items():
            if len(rows) > 1:
                duplicates.append({
                    "_id": {
                        "digest_time": identity[0],
                        "date_key": identity[1],
                        "weekly_roundup_batch_slot": identity[2],
                    },
                    "count": len(rows),
                    "docs": [
                        {"_id": row["_id"], "sent_at": row.get("sent_at"), "status": row.get("status")}
                        for row in rows
                    ],
                })
        return AsyncCursor(duplicates)

    async def delete_one(self, query):
        for index, row in enumerate(self.documents):
            if _matches(row, query):
                self.documents.pop(index)
                break
        return Result()

    async def count_documents(self, _query):
        return 0

    def find(self, _query):
        return AsyncCursor([])

    async def create_index(self, keys, **options):
        self.created_indexes.append((list(keys), dict(options)))
        self.indexes.add(options["name"])
        return options["name"]

    async def drop_index(self, name):
        if name not in self.indexes:
            raise RuntimeError("index not found")
        self.indexes.remove(name)


class SchedulerLocks:
    def __init__(self):
        self.rows = {}

    async def update_one(self, query, update, upsert=False):
        self.rows.setdefault(query["job"], {"job": query["job"], "locked_at": None, "lock_id": None})
        return Result()

    async def find_one_and_update(self, query, update, return_document=None):
        row = self.rows[query["job"]]
        row.update(deepcopy(update["$set"]))
        return deepcopy(row)

    async def delete_one(self, query):
        row = self.rows.get(query["job"])
        if row and ("lock_id" not in query or row.get("lock_id") == query["lock_id"]):
            self.rows.pop(query["job"], None)
        return Result()


class StaticCollection:
    def __init__(self, rows=None):
        self.rows = deepcopy(rows or [])
        self.updates = []

    def find(self, _query, _projection=None, **_kwargs):
        return AsyncCursor(self.rows)

    async def find_one(self, _query, **_kwargs):
        return deepcopy(self.rows[0]) if self.rows else None

    async def update_one(self, query, update, upsert=False):
        self.updates.append((deepcopy(query), deepcopy(update), upsert))
        return Result()


class Articles(StaticCollection):
    def find(self, _query, _projection=None, **_kwargs):
        return AsyncCursor(self.rows[1:])


class Provider:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0
        self.last_accepted_recipients = []
        self.resend_enabled = True

    def send_weekly_roundup(self, *, to_emails, **_kwargs):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        status = next(
            row.get("status")
            for row in server.db.digest_log.documents
            if row.get("weekly_roundup_batch_slot") == 1
        )
        assert status == "sending"
        if isinstance(outcome, Exception):
            raise outcome
        accepted = int(outcome)
        self.last_accepted_recipients = list(to_emails[:accepted])
        return accepted, f"weekly-tracking-{self.calls}"


def build_runtime(outcomes, *, digest_documents=None):
    digest_log = DigestLog(digest_documents)
    database = SimpleNamespace(
        digest_log=digest_log,
        scheduler_locks=SchedulerLocks(),
        subscribers=StaticCollection([{
            "email": "reader@cheshiretoday.co.uk",
            "priority_daily_brief": True,
            "signup_source": "website",
        }]),
        email_analytics=StaticCollection([]),
        articles=Articles([
            {"_id": "article-1", "title": "Big read", "content": "Complete report"},
            {"_id": "article-2", "title": "Second story", "content": "Complete report"},
        ]),
        email_send_opportunities=StaticCollection([]),
        email_batch_cursors=StaticCollection([]),
    )
    return database, Provider(outcomes)


def run(coro):
    return asyncio.run(coro)


def test_slot_aware_migration_backfills_and_preserves_four_batches(monkeypatch):
    documents = [
        {"_id": 1, "digest_time": "WeeklyRoundup", "date_key": "20260823", "status": "sent"},
        {"_id": 2, "digest_time": "WeeklyRoundup", "date_key": "20260823", "weekly_roundup_batch_slot": 2, "status": "sent"},
        {"_id": 3, "digest_time": "WeeklyRoundup", "date_key": "20260823", "weekly_roundup_batch_slot": 3, "status": "sent"},
        {"_id": 4, "digest_time": "WeeklyRoundup", "date_key": "20260823", "weekly_roundup_batch_slot": 4, "status": "sent"},
        {"_id": 5, "digest_time": "DailyBrief", "date_key": "20260823", "status": "sent"},
    ]
    digest_log = DigestLog(documents)
    monkeypatch.setattr(server, "db", SimpleNamespace(digest_log=digest_log))

    assert run(server._ensure_digest_log_slot_aware_index()) is True
    assert run(server._ensure_digest_log_slot_aware_index()) is True

    weekly = [row for row in digest_log.documents if row["digest_time"] == "WeeklyRoundup"]
    assert sorted(row["weekly_roundup_batch_slot"] for row in weekly) == [1, 2, 3, 4]
    daily = [row for row in digest_log.documents if row["digest_time"] == "DailyBrief"]
    assert len(daily) == 1 and "weekly_roundup_batch_slot" not in daily[0]
    keys, options = digest_log.created_indexes[-1]
    assert keys == [
        ("digest_time", 1),
        ("date_key", 1),
        ("weekly_roundup_batch_slot", 1),
    ]
    assert options == {
        "unique": True,
        "sparse": False,
        "background": True,
        "name": "digest_time_date_key_weekly_slot_unique_v1",
    }
    assert "digest_time_date_key_unique_v3" not in digest_log.indexes
    assert "digest_time_date_key_unique_sparse" not in digest_log.indexes


def test_compound_identity_rejects_same_slot_and_same_date_daily_duplicate():
    digest_log = DigestLog([
        {"_id": 1, "digest_time": "WeeklyRoundup", "date_key": "20260823", "weekly_roundup_batch_slot": 1},
        {"_id": 2, "digest_time": "DailyBrief", "date_key": "20260823"},
    ])
    with pytest.raises(DuplicateKeyError):
        run(digest_log.insert_one({
            "digest_time": "WeeklyRoundup",
            "date_key": "20260823",
            "weekly_roundup_batch_slot": 1,
        }))
    with pytest.raises(DuplicateKeyError):
        run(digest_log.insert_one({"digest_time": "DailyBrief", "date_key": "20260823"}))
    run(digest_log.insert_one({
        "digest_time": "WeeklyRoundup",
        "date_key": "20260823",
        "weekly_roundup_batch_slot": 2,
    }))


@pytest.mark.parametrize("blocking_status", ["sent", "partial", "sending", "ambiguous"])
def test_non_retryable_states_do_not_call_provider(monkeypatch, blocking_status):
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    database, provider = build_runtime([], digest_documents=[{
        "_id": 1,
        "digest_time": "WeeklyRoundup",
        "date_key": today,
        "weekly_roundup_batch_slot": 1,
        "status": blocking_status,
        "success_count": 1,
        "accepted_count": 1,
    }])
    monkeypatch.setattr(server, "db", database)
    monkeypatch.setattr(server, "email_service", provider)
    monkeypatch.setattr(server, "weekly_roundup_digest_index_ready", True)

    run(server.send_weekly_roundup_email(1))
    assert provider.calls == 0


def test_sent_batch_is_durable_and_later_slot_is_independent(monkeypatch):
    database, provider = build_runtime([1, 0])
    monkeypatch.setattr(server, "db", database)
    monkeypatch.setattr(server, "email_service", provider)
    monkeypatch.setattr(server, "weekly_roundup_digest_index_ready", True)

    run(server.send_weekly_roundup_email(1))
    run(server.send_weekly_roundup_email(1))
    run(server.send_weekly_roundup_email(2))

    assert provider.calls == 1
    states = {
        row["weekly_roundup_batch_slot"]: row["status"]
        for row in database.digest_log.documents
    }
    assert states == {1: "sent", 2: "failed"}
    ledger_update = database.email_send_opportunities.updates[0][1]["$set"]
    assert ledger_update["date_key"]
    assert ledger_update["weekly_roundup_batch_slot"] == 1
    assert ledger_update["batch_key"].endswith(":batch:1")
    assert ledger_update["recipient_hashes"] and "reader@cheshiretoday.co.uk" not in str(ledger_update)


def test_partial_and_provider_exception_are_not_retried(monkeypatch):
    database, provider = build_runtime([1], digest_documents=None)
    database.subscribers.rows.append({
        "email": "second@cheshiretoday.co.uk",
        "priority_daily_brief": True,
        "signup_source": "website",
    })
    monkeypatch.setattr(server, "db", database)
    monkeypatch.setattr(server, "email_service", provider)
    monkeypatch.setattr(server, "weekly_roundup_digest_index_ready", True)

    run(server.send_weekly_roundup_email(1))
    run(server.send_weekly_roundup_email(1))
    assert provider.calls == 1
    assert database.digest_log.documents[0]["status"] == "partial"

    second_database, second_provider = build_runtime([RuntimeError("provider outcome unknown")])
    monkeypatch.setattr(server, "db", second_database)
    monkeypatch.setattr(server, "email_service", second_provider)
    run(server.send_weekly_roundup_email(1))
    run(server.send_weekly_roundup_email(1))
    assert second_provider.calls == 1
    assert second_database.digest_log.documents[0]["status"] == "ambiguous"


def test_zero_acceptance_failed_state_is_retryable(monkeypatch):
    database, provider = build_runtime([0, 1])
    monkeypatch.setattr(server, "db", database)
    monkeypatch.setattr(server, "email_service", provider)
    monkeypatch.setattr(server, "weekly_roundup_digest_index_ready", True)

    run(server.send_weekly_roundup_email(1))
    assert database.digest_log.documents[0]["status"] == "failed"
    run(server.send_weekly_roundup_email(1))
    assert provider.calls == 2
    assert database.digest_log.documents[0]["status"] == "sent"


def test_failure_before_provider_contact_remains_retryable(monkeypatch):
    database, provider = build_runtime([1])
    database.subscribers.rows = []
    monkeypatch.setattr(server, "db", database)
    monkeypatch.setattr(server, "email_service", provider)
    monkeypatch.setattr(server, "weekly_roundup_digest_index_ready", True)

    run(server.send_weekly_roundup_email(1))
    run(server.send_weekly_roundup_email(1))

    assert provider.calls == 0
    assert len(database.digest_log.documents) == 1
    assert database.digest_log.documents[0]["status"] == "failed"
    assert database.digest_log.documents[0]["success_count"] == 0
    assert database.digest_log.documents[0]["accepted_count"] == 0


def test_completion_persistence_failure_becomes_ambiguous(monkeypatch):
    database, provider = build_runtime([1])
    database.digest_log.fail_completion_once = True
    monkeypatch.setattr(server, "db", database)
    monkeypatch.setattr(server, "email_service", provider)
    monkeypatch.setattr(server, "weekly_roundup_digest_index_ready", True)

    run(server.send_weekly_roundup_email(1))
    run(server.send_weekly_roundup_email(1))

    assert provider.calls == 1
    assert database.digest_log.documents[0]["status"] == "ambiguous"


def test_weekly_send_fails_closed_when_index_migration_is_not_ready(monkeypatch):
    database, provider = build_runtime([1])
    monkeypatch.setattr(server, "db", database)
    monkeypatch.setattr(server, "email_service", provider)
    monkeypatch.setattr(server, "weekly_roundup_digest_index_ready", False)

    run(server.send_weekly_roundup_email(1))

    assert provider.calls == 0
    assert database.digest_log.documents == []


def test_scheduler_and_daily_brief_contracts_remain_unchanged():
    import inspect

    source = inspect.getsource(server)
    daily_source = inspect.getsource(server.send_scheduled_news_digest)
    assert "[(9, 1), (10, 2), (11, 3), (12, 4)]" in source
    assert "weekly_roundup_{date_key}_batch_{roundup_batch_slot}" in source
    assert "DAILY_BRIEF_SEND_CAP" in daily_source
    assert "WEEKLY_ROUNDUP_DIGEST_TIME" not in daily_source
