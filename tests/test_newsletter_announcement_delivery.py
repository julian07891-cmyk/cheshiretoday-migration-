"""Offline announcement delivery and deliberately broad migration semantics."""
import asyncio
import ast
import subprocess
from types import SimpleNamespace

import httpx
import pytest

from backend import server
from app.email_service import EmailService
from app.newsletter_delivery import NewsletterDeliveryError, PreparedNewsletterDelivery, RecipientDeliveryContext, prepare_direct_delivery
from app.newsletter_token_service import NewsletterTokenService
from tests.test_newsletter_daily_delivery import subscriber, deliveries, TOKEN_SERVICE, check_message, Collection
from tests.test_weekly_roundup_idempotence import AsyncCursor


ACTIVE = {"$or": [{"active": True}, {"active": {"$exists": False}}]}


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a, **k):
        raise AssertionError("Real transport forbidden")
    monkeypatch.setattr("app.email_service.httpx.post", forbidden)
    monkeypatch.setattr("app.email_service.smtplib.SMTP", forbidden)
    monkeypatch.setattr("app.email_service.smtplib.SMTP_SSL", forbidden)
    monkeypatch.setattr(server, "newsletter_token_service_from_environment", lambda: TOKEN_SERVICE)


def send(service, prepared):
    return service.send_announcement_email(prepared_deliveries=prepared, token_service=TOKEN_SERVICE)


@pytest.mark.parametrize("resend", [False, True])
@pytest.mark.parametrize("outcome", ["all", "partial", "zero", "unavailable"])
def test_transport_isolation(monkeypatch, resend, outcome):
    service = EmailService()
    service.resend_enabled = resend
    service.smtp_enabled = False
    service.resend_api_key = None if outcome == "unavailable" else "synthetic"
    service.from_email = "sender@synthetic.invalid"
    messages, chunks = [], []
    def post(url, *, json, **kwargs):
        chunks.append(len(json))
        messages.extend([{**m, "to": m["to"][0]} for m in json])
        ok = outcome == "all" or outcome == "partial" and len(chunks) == 2
        return httpx.Response(200 if ok else 400, request=httpx.Request("POST", "https://synthetic.invalid"))
    def smtp(to, subject, html, text, *, newsletter_headers):
        service.last_provider_contacted = True
        messages.append({"to": to, "subject": subject, "html": html, "text": text, "headers": newsletter_headers})
        return outcome == "all" or outcome == "partial" and len(messages) == 101
    monkeypatch.setattr("app.email_service.httpx.post", post)
    if outcome != "unavailable":
        monkeypatch.setattr(service, "_send_email", smtp)
    prepared = deliveries(101)
    service.last_accepted_recipients = ["stale"]
    service.last_provider_contacted = True
    count = send(service, prepared)
    expected = 101 if outcome == "all" else 1 if outcome == "partial" else 0
    assert count == expected
    assert service.last_provider_contacted is (outcome != "unavailable")
    assert service.last_accepted_recipients == ([a.context.email for a in prepared] if expected == 101 else
                                              [prepared[-1].context.email] if expected == 1 else [])
    if resend and outcome != "unavailable": assert chunks == [100, 1]
    for message, artifact in zip(messages, prepared):
        check_message(message, artifact)
        assert message["to"] == artifact.context.email
        assert message["subject"] == "We've made some changes to Cheshire Today 📩"
        assert f'href="{artifact.human_unsubscribe_url}"' in message["html"]
        assert "automatically moved to The Daily Brief" in message["text"]


@pytest.mark.parametrize("resend", [False, True])
@pytest.mark.parametrize("kind", ["swap", "human", "native", "malformed", "forged", "uuid", "version", "headers"])
def test_whole_batch_rejected(monkeypatch, resend, kind):
    a, b = deliveries(2)
    broken_headers = object.__new__(PreparedNewsletterDelivery)
    for key, value in [("context", a.context), ("human_unsubscribe_url", a.human_unsubscribe_url),
                       ("native_headers", {**dict(a.native_headers), "Unexpected": "header"})]:
        object.__setattr__(broken_headers, key, value)
    bad = {
        "swap": PreparedNewsletterDelivery(a.context, b.human_unsubscribe_url, b.native_headers),
        "human": PreparedNewsletterDelivery(a.context, b.human_unsubscribe_url, a.native_headers),
        "native": PreparedNewsletterDelivery(a.context, a.human_unsubscribe_url, b.native_headers),
        "malformed": PreparedNewsletterDelivery(a.context, a.human_unsubscribe_url + "&token=x", a.native_headers),
        "forged": prepare_direct_delivery(a.context, NewsletterTokenService("E" * 43)),
        "uuid": PreparedNewsletterDelivery(b.context, a.human_unsubscribe_url, a.native_headers),
        "version": PreparedNewsletterDelivery(RecipientDeliveryContext(a.context.email,
            a.context.newsletter_management_id, 2), a.human_unsubscribe_url, a.native_headers),
        "headers": broken_headers,
    }[kind]
    service = EmailService()
    service.resend_enabled = resend
    calls = []
    monkeypatch.setattr(service, "_send_email", lambda *a, **k: calls.append(1))
    monkeypatch.setattr(service, "_send_resend_batch", lambda *a, **k: calls.append(1))
    with pytest.raises(NewsletterDeliveryError, match="^invalid_prepared_delivery$"):
        send(service, [a, bad, b])
    assert not calls and not service.last_provider_contacted and not service.last_accepted_recipients


@pytest.mark.parametrize("kwargs", [{}, {"to_emails": ["raw@synthetic.invalid"]},
    {"prepared_deliveries": deliveries(1)},
    {"prepared_deliveries": deliveries(1), "to_emails": ["raw@synthetic.invalid"], "token_service": TOKEN_SERVICE}])
def test_no_raw_or_unvalidated_contract(kwargs):
    service = EmailService()
    service.last_provider_contacted = True
    service.last_accepted_recipients = ["stale"]
    with pytest.raises(NewsletterDeliveryError): service.send_announcement_email(**kwargs)
    assert not service.last_provider_contacted and not service.last_accepted_recipients


class Subscribers:
    def __init__(self, rows, events):
        self.rows, self.events, self.updates = rows, events, []
    @staticmethod
    def matches(row):
        return "active" not in row or row["active"] is True
    def find(self, query, projection):
        assert query == {"$and": [ACTIVE, {"provider_suppressed": {"$ne": True}}]}
        assert set(projection) == {"_id", "email", "active", "newsletter_management_id", "newsletter_token_version", "provider_suppressed"}
        return AsyncCursor([r for r in self.rows if self.matches(r) and r.get("provider_suppressed") is not True])
    async def update_many(self, query, update):
        assert query == ACTIVE and update == {"$set": {"daily_brief": True}}
        assert self.events[-1] == "send_returned"
        self.events.append("update_many")
        self.updates.append((query, update))
        for row in self.rows:
            if self.matches(row): row.update(update["$set"])


def setup(monkeypatch, rows, outcome=0):
    events = []
    db = SimpleNamespace(subscribers=Subscribers(rows, events), digest_log=Collection())
    service = EmailService()
    service.resend_enabled = False
    calls = []
    def smtp(to, *a, **k):
        service.last_provider_contacted = True
        calls.append(to)
        return len(calls) <= outcome
    monkeypatch.setattr(service, "_send_email", smtp)
    original = service.send_announcement_email
    def wrapped(**kwargs):
        events.append("send_called")
        count = original(**kwargs)
        events.append("send_returned")
        return count
    monkeypatch.setattr(service, "send_announcement_email", wrapped)
    monkeypatch.setattr(server, "db", db)
    monkeypatch.setattr(server, "email_service", service)
    return db, service, events, calls


@pytest.mark.parametrize("accepted", [0, 1, 2])
def test_full_population_migration_after_normal_send(monkeypatch, accepted):
    rows = [subscriber(i) for i in range(1, 10002)]
    # Only two prepared messages, but every fetched slot remains selected.
    for row in rows[2:10000]: row.pop("newsletter_management_id")
    rows[2].pop("active")
    excluded = [subscriber(20000 + i, active=state) for i, state in enumerate([False, None, 1, "true"])]
    db, service, events, calls = setup(monkeypatch, excluded + rows, accepted)
    result = asyncio.run(server.send_migration_announcement())
    assert calls == [r["email"] for r in rows[:2]]
    assert events == ["send_called", "send_returned", "update_many"]
    assert all(r["daily_brief"] is True for r in rows)  # Includes row 10,001 and missing active.
    assert all("daily_brief" not in r for r in excluded)
    record = db.digest_log.inserts[0]
    assert (record["selected_count"], record["prepared_count"], record["skipped_count"], record["accepted_count"]) == (10000, 2, 9998, accepted)
    assert record["provider_contacted"] is True
    assert result["subscribers_migrated"] == 10000  # Preserve historical response field semantics.
    assert "#token=" not in str(record) and "synthetic.invalid" not in str(record)


def test_provider_suppressed_not_sent_but_still_migrated(monkeypatch):
    suppressed = subscriber(1, provider_suppressed=True, daily_brief=False)
    eligible = subscriber(2, daily_brief=False)
    db, _, events, calls = setup(monkeypatch, [suppressed, eligible], 1)
    result = asyncio.run(server.send_migration_announcement())
    assert calls == [eligible["email"]]
    assert events == ["send_called", "send_returned", "update_many"]
    assert suppressed["daily_brief"] is True
    assert eligible["daily_brief"] is True
    record = db.digest_log.inserts[0]
    assert (record["selected_count"], record["prepared_count"], record["skipped_count"], record["accepted_count"]) == (1, 1, 0, 1)
    assert result["subscribers_migrated"] == 1


@pytest.mark.parametrize("invalid", ["missing", None, "", 123, "missing_active", "bad_id", "bad_version"])
def test_invalid_positions_are_counted(monkeypatch, invalid):
    row = subscriber()
    if invalid == "missing": row.pop("email")
    elif invalid == "missing_active": row.pop("active")
    elif invalid == "bad_id": row["newsletter_management_id"] = "bad"
    elif invalid == "bad_version": row["newsletter_token_version"] = True
    else: row["email"] = invalid
    db, service, events, calls = setup(monkeypatch, [row])
    asyncio.run(server.send_migration_announcement())
    record = db.digest_log.inserts[0]
    assert record["selected_count"] == record["skipped_count"] == 1
    assert record["prepared_count"] == record["accepted_count"] == 0
    assert record["provider_contacted"] is False and not calls
    if invalid == "missing_active": assert record["skip_reasons"] == {"invalid_active_state": 1}
    assert row["daily_brief"] is True and events[-1] == "update_many"


@pytest.mark.parametrize("field", ["email", "newsletter_management_id"])
def test_ambiguity_fails_closed(monkeypatch, field):
    rows = [subscriber(1), subscriber(2)]
    rows[1][field] = rows[0][field]
    db, _, _, calls = setup(monkeypatch, rows)
    asyncio.run(server.send_migration_announcement())
    assert not calls and db.digest_log.inserts[0]["skipped_count"] == 2


@pytest.mark.parametrize("failure", ["signer", "sender"])
def test_private_failure_mutation_order(monkeypatch, caplog, failure):
    rows = [subscriber()]
    db, service, events, calls = setup(monkeypatch, rows)
    def fail(*a, **k): raise ValueError("PRIVATE_TOKEN secret@synthetic.invalid")
    if failure == "signer":
        monkeypatch.setattr(server, "newsletter_token_service_from_environment", fail)
        asyncio.run(server.send_migration_announcement())
        assert db.subscribers.updates and not calls
        assert db.digest_log.inserts[0]["skip_reasons"] == {"direct_delivery_preparation_failed": 1}
    else:
        monkeypatch.setattr(service, "_send_email", fail)
        with pytest.raises(server.HTTPException) as error: asyncio.run(server.send_migration_announcement())
        assert error.value.detail == "Announcement email unavailable"
        assert not db.subscribers.updates and not db.digest_log.inserts
        assert events == ["send_called"]
    assert "PRIVATE_TOKEN" not in caplog.text and "secret@" not in caplog.text


def test_announcement_commit_only_changed_announcement_functions():
    for path, allowed in [("backend/server.py", "send_migration_announcement"),
                          ("backend/app/email_service.py", "send_announcement_email")]:
        old = subprocess.check_output(["git", "show", "14e2f01:" + path], text=True)
        # This historical slice is committed; later slices have their own live scope guard.
        new = subprocess.check_output(["git", "show", "14d05a9:" + path], text=True)
        def without_target(source):
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == allowed:
                    node.body = []
                    node.args = None
            return ast.dump(tree, include_attributes=False)
        assert without_target(old) == without_target(new)


@pytest.mark.parametrize("resend", [False, True])
def test_unavailable_transport_still_migrates_on_normal_return(monkeypatch, resend):
    rows = [subscriber()]
    db, service, events, calls = setup(monkeypatch, rows)
    service.resend_enabled = resend
    service.resend_api_key = None
    service.smtp_enabled = False
    # Restore the real SMTP helper so its pre-contact configuration gate executes.
    monkeypatch.setattr(service, "_send_email", EmailService._send_email.__get__(service))
    asyncio.run(server.send_migration_announcement())
    assert events == ["send_called", "send_returned", "update_many"]
    assert rows[0]["daily_brief"] is True
    record = db.digest_log.inserts[0]
    assert record["prepared_count"] == 1 and record["accepted_count"] == 0
    assert record["provider_contacted"] is False and not calls
