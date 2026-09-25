"""Weekly direct delivery: synthetic candidates, storage and transports only."""
import asyncio
import hashlib
from types import SimpleNamespace

import httpx
import pytest

from backend import server
from app.email_service import EmailService
from app.newsletter_delivery import PreparedNewsletterDelivery, NewsletterDeliveryError
from tests.test_newsletter_daily_delivery import subscriber, deliveries, TOKEN_SERVICE, ARTICLE, check_message
from tests.test_weekly_roundup_idempotence import build_runtime, Articles, StaticCollection, AsyncCursor


class WeeklySubscribers(StaticCollection):
    """Apply the real active predicate to these scalar-state fixtures only.

    Other audience predicates remain outside this narrow test double. In
    particular, Python's 1 == True must not stand in for Mongo boolean equality.
    """
    def find(self, query, _projection=None, **_kwargs):
        assert query["$and"][0] == {
            "$or": [{"active": True}, {"active": {"$exists": False}}]
        }
        assert {"provider_suppressed": {"$ne": True}} in query["$and"]
        assert all(not isinstance(row.get("active"), (list, dict)) for row in self.rows)
        return AsyncCursor([row for row in self.rows
                            if ("active" not in row or row["active"] is True)
                            and row.get("provider_suppressed") is not True])


@pytest.fixture(autouse=True)
def isolate(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Real transport forbidden")
    monkeypatch.setattr("app.email_service.httpx.post", forbidden)
    monkeypatch.setattr("app.email_service.smtplib.SMTP", forbidden)
    monkeypatch.setattr("app.email_service.smtplib.SMTP_SSL", forbidden)
    monkeypatch.setattr(server, "newsletter_token_service_from_environment", lambda: TOKEN_SERVICE)
    monkeypatch.setattr(server, "weekly_roundup_digest_index_ready", True)


def send(service, prepared, **kwargs):
    return service.send_weekly_roundup(prepared_deliveries=prepared,
        token_service=TOKEN_SERVICE, big_read=ARTICLE, icymi_articles=[], **kwargs)


@pytest.mark.parametrize("transport", ["smtp", "resend"])
def test_weekly_isolation_at_chunk_boundary(monkeypatch, transport):
    service = EmailService()
    service.resend_enabled = transport == "resend"
    service.resend_api_key = "synthetic"
    service.from_email = "sender@synthetic.invalid"
    prepared = deliveries(101)
    messages, chunks = [], []
    def post(url, *, json, **kwargs):
        chunks.append(len(json))
        messages.extend([{**m, "to": m["to"][0]} for m in json])
        return httpx.Response(200, request=httpx.Request("POST", "https://synthetic.invalid"))
    def smtp(to, subject, html, text, *, newsletter_headers, feedback_id):
        assert feedback_id == "weekly:::cheshtoday"
        service.last_provider_contacted = True
        messages.append({"to": to, "html": html, "text": text, "headers": newsletter_headers})
        return True
    monkeypatch.setattr("app.email_service.httpx.post", post)
    monkeypatch.setattr(service, "_send_email", smtp)
    count, tracking = send(service, prepared)
    assert count == 101 and service.last_provider_contacted
    assert chunks == ([100, 1] if transport == "resend" else [])
    for message, artifact in zip(messages, prepared):
        check_message(message, artifact)
        assert message["to"] == artifact.context.email
        assert service._recipient_tracking_id(tracking, artifact.context.email) in message["html"]
    assert service.last_accepted_recipients == [a.context.email for a in prepared]


@pytest.mark.parametrize("resend", [False, True])
@pytest.mark.parametrize("kind", ["swap", "human", "native", "malformed", "forged", "version"])
def test_entire_weekly_batch_rejected_before_contact(monkeypatch, resend, kind):
    from app.newsletter_delivery import prepare_direct_delivery, RecipientDeliveryContext
    from app.newsletter_token_service import NewsletterTokenService
    a, b = deliveries(2)
    choices = {
        "swap": PreparedNewsletterDelivery(a.context, b.human_unsubscribe_url, b.native_headers),
        "human": PreparedNewsletterDelivery(a.context, b.human_unsubscribe_url, a.native_headers),
        "native": PreparedNewsletterDelivery(a.context, a.human_unsubscribe_url, b.native_headers),
        "malformed": PreparedNewsletterDelivery(a.context, a.human_unsubscribe_url + "&token=x", a.native_headers),
        "forged": prepare_direct_delivery(a.context, NewsletterTokenService("E" * 43)),
        "version": PreparedNewsletterDelivery(RecipientDeliveryContext(a.context.email,
            a.context.newsletter_management_id, 2), a.human_unsubscribe_url, a.native_headers),
    }
    service = EmailService()
    service.resend_enabled = resend
    calls = []
    monkeypatch.setattr(service, "_send_email", lambda *a, **k: calls.append(1))
    monkeypatch.setattr(service, "_send_resend_batch", lambda *a, **k: calls.append(1))
    service.last_accepted_recipients = ["stale"]
    service.last_provider_contacted = True
    with pytest.raises(NewsletterDeliveryError, match="^invalid_prepared_delivery$"):
        send(service, [a, choices[kind], b])
    assert not calls and not service.last_accepted_recipients and not service.last_provider_contacted


def runtime(monkeypatch, rows):
    db, _ = build_runtime([])
    db.subscribers = WeeklySubscribers(rows)
    db.email_analytics.rows = [{"tracking_id": "weekly_" + hashlib.sha256(r["email"].encode()).hexdigest()[:8],
                               "opens": 1} for r in rows]
    service = EmailService()
    service.resend_enabled = False
    monkeypatch.setattr(server, "db", db)
    monkeypatch.setattr(server, "email_service", service)
    return db, service


@pytest.mark.parametrize("invalid_index", [0, 1])
def test_selected_missing_active_priority_or_rotating_consumes_slot(monkeypatch, invalid_index):
    rows = [subscriber(1, priority_daily_brief=True), subscriber(2), subscriber(3)]
    del rows[invalid_index]["active"]
    db, service = runtime(monkeypatch, rows)
    monkeypatch.setenv("WEEKLY_ROUNDUP_SEND_CAP", "2")
    calls = []
    def smtp(to, *a, **k):
        service.last_provider_contacted = True
        calls.append(to)
        return True
    monkeypatch.setattr(service, "_send_email", smtp)
    asyncio.run(server.send_weekly_roundup_email(1))
    record = db.digest_log.documents[0]
    assert calls == [rows[1 - invalid_index]["email"]]
    assert (record["selected_count"], record["prepared_count"], record["skipped_count"], record["accepted_count"]) == (2, 1, 1, 1)
    assert record["status"] == "partial"
    assert record["skip_reasons"] == {"invalid_active_state": 1}
    assert db.email_batch_cursors.updates[-1][1]["$set"]["next_index"] == 1


@pytest.mark.parametrize("outcome", ["inactive", "signing", "smtp_disabled", "resend_missing", "zero", "partial", "all"])
def test_scheduled_contact_retry_and_cursor(monkeypatch, outcome):
    rows = [subscriber(1, priority_daily_brief=True), subscriber(2, priority_daily_brief=True)]
    if outcome == "inactive":
        for row in rows:
            row.pop("active")
    db, service = runtime(monkeypatch, rows)
    calls = []
    if outcome == "signing":
        def fail():
            raise ValueError("synthetic secret must not escape")
        monkeypatch.setattr(server, "newsletter_token_service_from_environment", fail)
    service.smtp_enabled = False
    if outcome == "resend_missing":
        service.resend_enabled = True
        service.resend_api_key = None
    if outcome in {"zero", "partial", "all"}:
        def smtp(to, *a, **k):
            service.last_provider_contacted = True
            calls.append(to)
            return outcome == "all" or (outcome == "partial" and len(calls) == 1)
        monkeypatch.setattr(service, "_send_email", smtp)
    asyncio.run(server.send_weekly_roundup_email(1))
    first_owner = db.digest_log.documents[0]["instance_id"]
    record = db.digest_log.documents[0]
    accepted = {"all": 2, "partial": 1}.get(outcome, 0)
    assert record["accepted_count"] == accepted
    assert bool(db.email_batch_cursors.updates) == bool(accepted)
    contacted = outcome in {"zero", "partial", "all"}
    assert record["provider_contacted"] is contacted
    asyncio.run(server.send_weekly_roundup_email(1))
    assert (db.digest_log.documents[0]["instance_id"] == first_owner) is contacted
    assert len(calls) == (2 if contacted else 0)


def test_preview_endpoint_has_no_subscriber_access(monkeypatch):
    service = EmailService()
    service.resend_enabled = False
    calls = []
    monkeypatch.setattr(service, "_send_email", lambda *a, **k: calls.append((a, k)) or True)
    monkeypatch.setattr(server, "email_service", service)
    monkeypatch.setattr(server, "db", SimpleNamespace(articles=Articles([ARTICLE])))
    result = asyncio.run(server.send_weekly_roundup_test("preview@synthetic.invalid"))
    assert result["emails_sent"] == 1
    assert calls[0][1] == {} and "#token=" not in str(calls)
    for recipients in [[], ["a", "b"]]:
        with pytest.raises(NewsletterDeliveryError):
            service.send_weekly_roundup(to_emails=recipients, preview=True, big_read=ARTICLE, icymi_articles=[])
    with pytest.raises(NewsletterDeliveryError):
        send(service, deliveries(1), preview=True)
    with pytest.raises(NewsletterDeliveryError):
        send(service, deliveries(1), to_emails=["override@synthetic.invalid"])


def test_batch_diagnostic_real_delivery_without_accounting(monkeypatch):
    rows = [subscriber(1), subscriber(2), subscriber(3)]
    del rows[0]["active"]
    db, service = runtime(monkeypatch, rows)
    calls = []
    monkeypatch.setattr(service, "_send_email", lambda *a, **k: calls.append((a, k)) or True)
    result = asyncio.run(server.send_weekly_roundup_batch_test(2))
    assert result["delivery_counts"] == {"selected_count": 2, "prepared_count": 1,
        "skipped_count": 1, "skip_reasons": {"invalid_active_state": 1}, "accepted_count": 1}
    assert calls[0][0][0] == rows[1]["email"]
    assert "#token=" in calls[0][0][2] and calls[0][1]["newsletter_headers"]
    assert not db.digest_log.documents and not db.email_batch_cursors.updates
    assert not db.email_send_opportunities.updates


def test_weekly_diagnostic_excludes_provider_suppressed_before_selection(monkeypatch):
    rows = [subscriber(1, provider_suppressed=True), subscriber(2), subscriber(3)]
    db, service = runtime(monkeypatch, rows)
    calls = []
    monkeypatch.setattr(service, "_send_email", lambda to, *a, **k: calls.append(to) or True)
    result = asyncio.run(server.send_weekly_roundup_batch_test(2))
    assert calls == [rows[1]["email"], rows[2]["email"]]
    assert result["delivery_counts"]["selected_count"] == 2


@pytest.mark.parametrize("diagnostic", [False, True])
@pytest.mark.parametrize("state", [False, None, 1, "true"])
def test_weekly_query_excludes_nonmatching_active_before_selection(monkeypatch, diagnostic, state):
    rows = [subscriber(1, active=state, priority_daily_brief=True), subscriber(2), subscriber(3)]
    db, service = runtime(monkeypatch, rows)
    monkeypatch.setenv("WEEKLY_ROUNDUP_SEND_CAP", "2")
    candidates_seen = []
    original = server._newsletter_candidate_contexts
    def capture_candidates(records):
        candidates_seen.extend(row["email"] for row in records)
        return original(records)
    monkeypatch.setattr(server, "_newsletter_candidate_contexts", capture_candidates)
    calls = []
    def smtp(to, *a, **k):
        service.last_provider_contacted = True
        calls.append(to)
        return True
    monkeypatch.setattr(service, "_send_email", smtp)
    if diagnostic:
        counts = asyncio.run(server.send_weekly_roundup_batch_test(2))["delivery_counts"]
        assert not db.digest_log.documents and not db.email_batch_cursors.updates
    else:
        asyncio.run(server.send_weekly_roundup_email(1))
        counts = db.digest_log.documents[0]
    assert candidates_seen == calls == [row["email"] for row in rows[1:]]
    assert (counts["selected_count"], counts["prepared_count"], counts["skipped_count"]) == (2, 2, 0)
    assert counts["skip_reasons"] == {}


def test_weekly_query_excludes_provider_suppressed_before_selection(monkeypatch):
    rows = [subscriber(1, provider_suppressed=True, priority_daily_brief=True),
            subscriber(2), subscriber(3)]
    db, service = runtime(monkeypatch, rows)
    monkeypatch.setenv("WEEKLY_ROUNDUP_SEND_CAP", "2")
    candidates_seen = []
    original = server._newsletter_candidate_contexts
    def capture_candidates(records):
        candidates_seen.extend(row["email"] for row in records)
        return original(records)
    monkeypatch.setattr(server, "_newsletter_candidate_contexts", capture_candidates)
    calls = []
    def smtp(to, *a, **k):
        service.last_provider_contacted = True
        calls.append(to)
        return True
    monkeypatch.setattr(service, "_send_email", smtp)
    asyncio.run(server.send_weekly_roundup_email(1))
    assert candidates_seen == calls == [rows[1]["email"], rows[2]["email"]]


def test_four_slots_no_wraparound(monkeypatch):
    rows = [subscriber(1, priority_daily_brief=True)] + [subscriber(i) for i in range(2, 8)]
    db, service = runtime(monkeypatch, rows)
    monkeypatch.setenv("WEEKLY_ROUNDUP_SEND_CAP", "2")
    calls = []
    def smtp(to, *a, **k):
        service.last_provider_contacted = True
        calls.append(to)
        return True
    monkeypatch.setattr(service, "_send_email", smtp)
    for slot in range(1, 5):
        asyncio.run(server.send_weekly_roundup_email(slot))
        asyncio.run(server.send_weekly_roundup_email(slot))
    assert calls == [r["email"] for r in rows]
    assert len(db.digest_log.documents) == 4
    assert all(r["status"] == "sent" for r in db.digest_log.documents)


def test_resend_partial_chunks_keep_only_accepted_recipients(monkeypatch):
    service = EmailService()
    service.resend_enabled = True
    service.resend_api_key = "synthetic"
    service.from_email = "sender@synthetic.invalid"
    sizes = []
    def post(url, *, json, **kwargs):
        sizes.append(len(json))
        return httpx.Response(400 if len(sizes) == 1 else 200,
                              request=httpx.Request("POST", "https://synthetic.invalid"))
    monkeypatch.setattr("app.email_service.httpx.post", post)
    prepared = deliveries(101)
    assert send(service, prepared)[0] == 1
    assert sizes == [100, 1] and service.last_provider_contacted
    assert service.last_accepted_recipients == [prepared[-1].context.email]


def test_scheduled_binding_failure_is_private_and_retryable(monkeypatch, caplog):
    db, service = runtime(monkeypatch, [subscriber(1, priority_daily_brief=True)])
    a, b = deliveries(2)
    bad = PreparedNewsletterDelivery(a.context, b.human_unsubscribe_url, b.native_headers)
    monkeypatch.setattr(server, "prepare_direct_delivery", lambda *args: bad)
    calls = []
    monkeypatch.setattr(service, "_send_email", lambda *a, **k: calls.append(1))
    asyncio.run(server.send_weekly_roundup_email(1))
    owner = db.digest_log.documents[0]["instance_id"]
    asyncio.run(server.send_weekly_roundup_email(1))
    record = db.digest_log.documents[0]
    assert record["status"] == "failed" and record["provider_contacted"] is False
    assert record["instance_id"] != owner
    assert not calls and not db.email_batch_cursors.updates
    diagnostics = str(db.digest_log.documents) + caplog.text
    assert "#token=" not in diagnostics and a.context.email not in diagnostics


@pytest.mark.parametrize("duplicate", ["email", "id"])
def test_weekly_candidate_ambiguity_precedes_selection(monkeypatch, duplicate):
    rows = [subscriber(1, priority_daily_brief=True), subscriber(2, priority_daily_brief=True)]
    field = "email" if duplicate == "email" else "newsletter_management_id"
    rows[1][field] = rows[0][field]
    db, service = runtime(monkeypatch, rows)
    monkeypatch.setenv("WEEKLY_ROUNDUP_SEND_CAP", "1")
    calls = []
    monkeypatch.setattr(service, "_send_email", lambda *a, **k: calls.append(1))
    asyncio.run(server.send_weekly_roundup_email(1))
    record = db.digest_log.documents[0]
    assert record["selected_count"] == record["skipped_count"] == 1
    assert record["prepared_count"] == 0 and not calls
