"""Offline accepted-send denominator and read-only/privacy contracts."""
import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from types import SimpleNamespace

import pytest

from backend import server
from app.newsletter_cold_report import build_cold_report, ELIGIBLE


NOW = datetime(2026, 9, 23, tzinfo=timezone.utc)
EMAIL = "reader@external.example"
H = hashlib.sha256(EMAIL.encode()).hexdigest()[:8]


def matches(row, query):
    for key, value in query.items():
        if key == "$and":
            if not all(matches(row, q) for q in value):
                return False
        elif key == "$or":
            if not any(matches(row, q) for q in value):
                return False
        elif isinstance(value, dict):
            if "$exists" in value and (key in row) != value["$exists"]:
                return False
            if "$ne" in value and row.get(key) == value["$ne"]:
                return False
        elif row.get(key) != value:
            return False
    return True


class Cursor:
    def __init__(self, records):
        self.records = iter(records)
        self.closed = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.records)
        except StopIteration:
            raise StopAsyncIteration

    async def close(self):
        self.closed = True


class Collection:
    def __init__(self, records):
        self.records = deepcopy(records)
        self.cursors = []
        self.queries = []

    def find(self, query, projection):
        self.queries.append(query)
        cursor = Cursor([{k: v for k, v in row.items() if projection.get(k)}
                         for row in self.records if matches(row, query)])
        self.cursors.append(cursor)
        return cursor

    def __getattr__(self, name):
        raise AssertionError("No database operations besides find permitted")


def subscriber(**changes):
    return dict(email=EMAIL, active=True, daily_brief=True,
                subscribed_at=NOW - timedelta(days=170), **changes)


def ledger(n):
    return [dict(tracking_id=f"DailyBrief_{i}", digest_key="DailyBrief",
                 provider="resend", accepted_count=1, recipient_hashes=[H],
                 accepted_at=NOW - timedelta(days=10 + i)) for i in range(n)]


def database(subs=None, sends=None, analytics=None):
    return SimpleNamespace(
        subscribers=Collection(subs if subs is not None else [subscriber()]),
        email_send_opportunities=Collection(sends if sends is not None else ledger(5)),
        email_analytics=Collection(analytics or []),
    )


def report(db):
    before = deepcopy([c.records for c in vars(db).values()])
    result = asyncio.run(build_cold_report(
        db, server.is_deliverable_newsletter_email,
        days=90, recent_days=21, min_accepted_sends=5, now=NOW,
    ))
    assert before == [c.records for c in vars(db).values()]
    assert all(c.closed for collection in vars(db).values() for c in collection.cursors)
    assert db.subscribers.queries == [ELIGIBLE]
    text = json.dumps(result)
    assert all(private not in text for private in (EMAIL, H, "DailyBrief_0", "private-token"))
    assert "sample" not in result
    assert "cold_candidates_with_no_recent_tracking_seen" not in text
    assert "cold_candidates_with_tracking_but_no_engagement" not in text
    assert result["dry_run"] is True
    return result


@pytest.mark.parametrize("n,expected", [(0, 0), (1, 0), (4, 0), (5, 1), (6, 1)])
def test_threshold_without_analytics(n, expected):
    result = report(database(sends=ledger(n)))
    assert result["summary"]["cold_candidates_total"] == expected
    assert result["summary"]["insufficient_accepted_send_evidence"] == int(n < 5)
    assert result["accepted_send_count_distribution"] == {str(n): 1}


@pytest.mark.parametrize("engagement", [
    {"opens": 1}, {"clicks": 1},
    {"opens": 1, "last_opened": NOW - timedelta(days=200)},
    {"last_clicked": NOW},
])
def test_any_recorded_engagement_vetoes(engagement):
    result = report(database(analytics=[{"tracking_id": f"DailyBrief_x_{H}", **engagement}]))
    assert result["summary"]["cold_candidates_total"] == 0
    assert result["summary"]["engaged_recipient_count"] == 1


def test_zero_counters_are_not_engagement():
    result = report(database(analytics=[{"tracking_id": f"DailyBrief_x_{H}", "opens": 0, "clicks": 0}]))
    assert result["summary"]["cold_candidates_total"] == 1


def test_duplicate_hashes_and_duplicate_opportunity_do_not_inflate():
    sends = ledger(4)
    sends[0]["recipient_hashes"] = [H, H]
    sends.append(deepcopy(sends[0]))
    result = report(database(sends=sends))
    assert result["summary"]["cold_candidates_total"] == 0
    assert result["accepted_send_count_distribution"] == {"4": 1}


@pytest.mark.parametrize("change,excluded", [
    ({"priority_daily_brief": True}, "protected_or_organic_excluded"),
    ({"signup_source": "website"}, "protected_or_organic_excluded"),
    ({"subscriber_origin": "organic_website"}, "protected_or_organic_excluded"),
    ({"email": "reader@cheshiretoday.co.uk"}, "protected_or_organic_excluded"),
    ({"email": "not-an-email"}, "invalid_excluded"),
    ({"email": 123}, "invalid_excluded"),
    ({"subscribed_at": NOW}, "recent_subscribers_excluded"),
    ({"subscribed_at": "2026-09-22T01:00:00"}, "recent_subscribers_excluded"),
    ({"subscribed_at": "broken"}, "unknown_subscription_date_excluded"),
])
def test_exclusions(change, excluded):
    row = subscriber()
    row.update(change)
    result = report(database(subs=[row]))
    assert result["summary"]["cold_candidates_total"] == 0
    assert result["summary"][excluded] == 1


@pytest.mark.parametrize("change", [{"active": False}, {"daily_brief": False}])
def test_production_query_excludes_ineligible(change):
    row = subscriber()
    row.update(change)
    result = report(database(subs=[row]))
    assert result["summary"]["active_daily_unique"] == 0


@pytest.mark.parametrize("date", [
    NOW - timedelta(days=170), (NOW - timedelta(days=170)).replace(tzinfo=None),
    "2026-04-06T00:00:00Z", "2026-04-06T00:00:00", "2026-04-06T01:00:00+01:00",
])
def test_old_date_forms_and_legacy_eligibility(date):
    row = {"email": EMAIL, "subscribed_at": date}
    assert report(database(subs=[row]))["summary"]["cold_candidates_total"] == 1


def test_created_at_fallback():
    row = {"email": EMAIL, "created_at": "2026-04-06T00:00:00Z"}
    assert report(database(subs=[row]))["summary"]["cold_candidates_total"] == 1


@pytest.mark.parametrize("change", [
    {"accepted_count": 0}, {"accepted_count": True}, {"accepted_count": 2},
    {"provider": "unknown"}, {"digest_key": "unknown"}, {"tracking_id": ""},
    {"recipient_hashes": ["private-token"]}, {"accepted_at": "broken"},
    {"accepted_at": NOW + timedelta(days=1)},
])
def test_invalid_acceptance_evidence_excluded(change):
    sends = ledger(5)
    sends[0].update(change)
    result = report(database(sends=sends))
    assert result["summary"]["cold_candidates_total"] == 0
    assert result["ledger_coverage"]["invalid_rows_excluded"] == 1


def test_window_and_coverage():
    sends = ledger(5)
    sends[0]["accepted_at"] = NOW - timedelta(days=100)
    result = report(database(sends=sends))
    assert result["summary"]["cold_candidates_total"] == 0
    assert result["ledger_coverage"]["earliest_accepted_at"] == sends[0]["accepted_at"].isoformat()


def test_duplicate_protected_peer_cannot_be_hidden():
    protected = subscriber(priority_daily_brief=True)
    assert report(database(subs=[subscriber(), protected]))["summary"]["cold_candidates_total"] == 0


def test_endpoint_bounds_and_private_failure(monkeypatch):
    import app.newsletter_cold_report as module
    seen = {}
    async def capture(db, validator, **kwargs):
        seen.update(kwargs)
        return {"dry_run": True}
    monkeypatch.setattr(module, "build_cold_report", capture)
    asyncio.run(server.get_cold_subscriber_report(days=900, recent_days=0, min_accepted_sends=1))
    assert (seen["days"], seen["recent_days"], seen["min_accepted_sends"]) == (180, 1, 5)
    async def fail(*args, **kwargs):
        raise RuntimeError("private-token " + EMAIL)
    monkeypatch.setattr(module, "build_cold_report", fail)
    with pytest.raises(server.HTTPException) as error:
        asyncio.run(server.get_cold_subscriber_report())
    assert error.value.status_code == 503
    assert error.value.detail == "Cold subscriber report unavailable"


def test_endpoint_requires_admin():
    route = next(r for r in server.app.routes if getattr(r, "path", "") == "/api/admin/subscribers/cold-report")
    assert server.get_admin_auth in [d.call for d in route.dependant.dependencies]


def test_endpoint_real_read_only_path_and_legacy_sample_argument(monkeypatch):
    db = database()
    monkeypatch.setattr(server, "db", db)
    class Clock:
        @staticmethod
        def now(tz):
            return NOW
    monkeypatch.setattr(server, "datetime", Clock)
    before = deepcopy([c.records for c in vars(db).values()])
    result = asyncio.run(server.get_cold_subscriber_report(days=90, sample_limit=250))
    assert result["summary"]["cold_candidates_total"] == 1
    assert result["min_accepted_sends"] == 5
    assert "sample" not in result and EMAIL not in json.dumps(result) and H not in json.dumps(result)
    assert before == [c.records for c in vars(db).values()]


def test_stream_failure_returns_bounded_error(monkeypatch, caplog):
    db = database()
    def fail(*args):
        raise RuntimeError("private-token " + EMAIL)
    monkeypatch.setattr(db.email_analytics, "find", fail)
    monkeypatch.setattr(server, "db", db)
    with pytest.raises(server.HTTPException) as error:
        asyncio.run(server.get_cold_subscriber_report())
    assert error.value.status_code == 503
    assert EMAIL not in caplog.text and "private-token" not in caplog.text


def test_unrelated_server_functions_unchanged():
    import ast
    from pathlib import Path
    import subprocess
    current = Path(server.__file__).read_text()
    baseline = subprocess.check_output(
        ["git", "show", "HEAD:backend/server.py"], text=True)
    def functions(source):
        return {node.name: ast.dump(node) for node in ast.parse(source).body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name != "get_cold_subscriber_report"}
    assert functions(current) == functions(baseline)
