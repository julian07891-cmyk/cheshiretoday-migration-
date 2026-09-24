"""Offline Breaking News email integration; push delivery remains separate."""
import asyncio
import ast
import inspect
import subprocess
from types import SimpleNamespace

import httpx
import pytest

from backend import server
from app.email_service import EmailService
from app.newsletter_delivery import PreparedNewsletterDelivery, RecipientDeliveryContext, NewsletterDeliveryError, prepare_direct_delivery
from app.newsletter_token_service import NewsletterTokenService
from tests.test_newsletter_daily_delivery import subscriber, deliveries, TOKEN_SERVICE, check_message, Collection
from tests.test_weekly_roundup_idempotence import AsyncCursor


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a, **k):
        raise AssertionError("Real transport forbidden")
    monkeypatch.setattr("app.email_service.httpx.post", forbidden)
    monkeypatch.setattr("app.email_service.smtplib.SMTP", forbidden)
    monkeypatch.setattr("app.email_service.smtplib.SMTP_SSL", forbidden)
    monkeypatch.setattr(server, "newsletter_token_service_from_environment", lambda: TOKEN_SERVICE)


def send(service, prepared, **kwargs):
    return service.send_breaking_news(prepared_deliveries=prepared, token_service=TOKEN_SERVICE,
        headline="Cheshire update", bullet_points=["Verified detail"],
        article_url="https://cheshiretoday.co.uk/article/live", **kwargs)


@pytest.mark.parametrize("resend", [False, True])
@pytest.mark.parametrize("outcome", ["all", "partial", "zero", "unavailable"])
def test_transport_isolation_and_accounting(monkeypatch, resend, outcome):
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
        messages.append({"to": to, "html": html, "text": text, "headers": newsletter_headers})
        return outcome == "all" or outcome == "partial" and len(messages) == 101
    monkeypatch.setattr("app.email_service.httpx.post", post)
    if outcome != "unavailable":
        monkeypatch.setattr(service, "_send_email", smtp)
    prepared = deliveries(101)
    service.last_accepted_recipients = ["stale"]
    service.last_provider_contacted = True
    count, tracking = send(service, prepared)
    expected = 101 if outcome == "all" else 1 if outcome == "partial" else 0
    assert count == expected
    assert service.last_provider_contacted is (outcome != "unavailable")
    assert service.last_accepted_recipients == ([a.context.email for a in prepared] if expected == 101 else
                                              [prepared[-1].context.email] if expected == 1 else [])
    if resend and outcome != "unavailable":
        assert chunks == [100, 1]
    for message, artifact in zip(messages, prepared):
        check_message(message, artifact)
        assert message["to"] == artifact.context.email
        assert f'href="{artifact.human_unsubscribe_url}"' in message["html"]
        assert service._get_tracked_url(tracking, "https://cheshiretoday.co.uk/article/live") in message["html"]


@pytest.mark.parametrize("resend", [False, True])
@pytest.mark.parametrize("kind", ["swap", "human", "native", "malformed", "forged", "uuid", "version"])
def test_complete_batch_binding_before_transport(monkeypatch, resend, kind):
    a, b = deliveries(2)
    bad = {
        "swap": PreparedNewsletterDelivery(a.context, b.human_unsubscribe_url, b.native_headers),
        "human": PreparedNewsletterDelivery(a.context, b.human_unsubscribe_url, a.native_headers),
        "native": PreparedNewsletterDelivery(a.context, a.human_unsubscribe_url, b.native_headers),
        "malformed": PreparedNewsletterDelivery(a.context, a.human_unsubscribe_url + "&extra=1", a.native_headers),
        "forged": prepare_direct_delivery(a.context, NewsletterTokenService("E" * 43)),
        "uuid": PreparedNewsletterDelivery(b.context, a.human_unsubscribe_url, a.native_headers),
        "version": PreparedNewsletterDelivery(RecipientDeliveryContext(a.context.email,
            a.context.newsletter_management_id, 2), a.human_unsubscribe_url, a.native_headers),
    }[kind]
    service = EmailService()
    service.resend_enabled = resend
    calls = []
    monkeypatch.setattr(service, "_send_email", lambda *a, **k: calls.append(1))
    monkeypatch.setattr(service, "_send_resend_batch", lambda *a, **k: calls.append(1))
    service.last_accepted_recipients = ["stale"]
    service.last_provider_contacted = True
    with pytest.raises(NewsletterDeliveryError, match="^invalid_prepared_delivery$"):
        send(service, [a, bad, b])
    assert not calls and not service.last_accepted_recipients and not service.last_provider_contacted


class Subscribers:
    def __init__(self, rows):
        self.rows = rows
    def find(self, query, projection):
        assert query == {"$and": [{"breaking_news": True},
            {"$or": [{"active": True}, {"active": {"$exists": False}}]},
            {"provider_suppressed": {"$ne": True}}]}
        assert set(projection) == {"_id", "email", "active", "newsletter_management_id", "newsletter_token_version", "provider_suppressed"}
        # Scalar fixtures: boolean Mongo equality must not treat numeric 1 as True.
        return AsyncCursor([r for r in self.rows if r.get("breaking_news") is True
                            and ("active" not in r or r["active"] is True)
                            and r.get("provider_suppressed") is not True])


def run_endpoint(monkeypatch, rows, service):
    db = SimpleNamespace(subscribers=Subscribers(rows), digest_log=Collection())
    monkeypatch.setattr(server, "db", db)
    monkeypatch.setattr(server, "email_service", service)
    result = asyncio.run(server.send_breaking_news_alert(server.BreakingNewsRequest(
        headline="Cheshire update", bullet_points=["Verified detail"])))
    return db, result


def test_provider_suppressed_excluded_before_breaking_selection(monkeypatch):
    rows = [subscriber(1, breaking_news=True, provider_suppressed=True),
            subscriber(2, breaking_news=True), subscriber(3, breaking_news=True)]
    service = EmailService()
    service.resend_enabled = False
    calls = []
    monkeypatch.setattr(service, "_send_email", lambda to, *a, **k: calls.append(to) or True)
    db, _ = run_endpoint(monkeypatch, rows, service)
    assert calls == [rows[1]["email"], rows[2]["email"]]
    record = db.digest_log.inserts[0]
    assert record["selected_count"] == record["prepared_count"] == record["accepted_count"] == 2
    assert record["skipped_count"] == 0


@pytest.mark.parametrize("invalid", ["missing_active", "missing_id", "bad_id", "bad_version"])
def test_selected_invalid_no_backfill_and_query_exclusions(monkeypatch, invalid):
    rows = [subscriber(i, breaking_news=True) for i in range(1, 1002)]
    if invalid == "missing_active": rows[0].pop("active")
    if invalid == "missing_id": rows[0].pop("newsletter_management_id")
    if invalid == "bad_id": rows[0]["newsletter_management_id"] = "bad"
    if invalid == "bad_version": rows[0]["newsletter_token_version"] = True
    excluded = [subscriber(2000, breaking_news=True, active=False),
                subscriber(2001, breaking_news=False), subscriber(2002, breaking_news=True, active=1)]
    service = EmailService()
    service.resend_enabled = False
    calls = []
    def smtp(to, *a, **k):
        service.last_provider_contacted = True
        calls.append(to)
        return True
    monkeypatch.setattr(service, "_send_email", smtp)
    db, _ = run_endpoint(monkeypatch, excluded + rows, service)
    record = db.digest_log.inserts[0]
    assert calls == [r["email"] for r in rows[1:1000]]
    assert (record["selected_count"], record["prepared_count"], record["skipped_count"], record["accepted_count"]) == (1000, 999, 1, 999)
    if invalid == "missing_active": assert record["skip_reasons"] == {"invalid_active_state": 1}
    assert record["provider_contacted"] is True
    assert "#token=" not in str(record) and "synthetic.invalid" not in str(record)


@pytest.mark.parametrize("failure", ["signing", "transport"])
def test_private_failure_and_digest_accounting(monkeypatch, caplog, failure):
    service = EmailService()
    service.resend_enabled = False
    service.smtp_enabled = False
    def fail(*a, **k):
        raise ValueError("PRIVATE_TOKEN recipient@synthetic.invalid")
    if failure == "signing":
        monkeypatch.setattr(server, "newsletter_token_service_from_environment", fail)
        db, _ = run_endpoint(monkeypatch, [subscriber(breaking_news=True)], service)
        record = db.digest_log.inserts[0]
        assert record["skip_reasons"] == {"direct_delivery_preparation_failed": 1}
        assert record["accepted_count"] == 0 and record["provider_contacted"] is False
    else:
        monkeypatch.setattr(service, "_send_email", fail)
        with pytest.raises(server.HTTPException) as error:
            run_endpoint(monkeypatch, [subscriber(breaking_news=True)], service)
        assert error.value.detail == "Breaking News email unavailable"
    assert "PRIVATE_TOKEN" not in caplog.text and "recipient@" not in caplog.text


def test_no_email_only_or_preview_escape():
    service = EmailService()
    with pytest.raises(NewsletterDeliveryError):
        service.send_breaking_news(to_emails=["reader@synthetic.invalid"], headline="Alert", bullet_points=[])
    with pytest.raises(TypeError):
        send(service, deliveries(1), preview=True)


@pytest.mark.parametrize("accepted", [0, 1, 2])
def test_endpoint_aggregate_acceptance(monkeypatch, accepted):
    service = EmailService()
    service.resend_enabled = False
    calls = []
    def smtp(to, *a, **k):
        service.last_provider_contacted = True
        calls.append(to)
        return len(calls) <= accepted
    monkeypatch.setattr(service, "_send_email", smtp)
    rows = [subscriber(i, breaking_news=True) for i in (1, 2)]
    db, _ = run_endpoint(monkeypatch, rows, service)
    record = db.digest_log.inserts[0]
    assert record["selected_count"] == record["prepared_count"] == 2
    assert record["skipped_count"] == 0 and record["skip_reasons"] == {}
    assert record["success_count"] == record["accepted_count"] == accepted
    assert record["provider_contacted"] is True
    assert service.last_accepted_recipients == calls[:accepted]
    assert set(record) == {"sent_at", "digest_time", "type", "headline", "subscribers_count",
        "success_count", "accepted_count", "provider_contacted", "selected_count", "prepared_count",
        "skipped_count", "skip_reasons", "tracking_id"}


@pytest.mark.parametrize("field", ["email", "newsletter_management_id"])
def test_candidate_ambiguity_rejects_all_duplicate_positions(monkeypatch, field):
    rows = [subscriber(i, breaking_news=True) for i in (1, 2)]
    rows[1][field] = rows[0][field]
    service = EmailService()
    service.resend_enabled = False
    service.smtp_enabled = False
    db, _ = run_endpoint(monkeypatch, rows, service)
    record = db.digest_log.inserts[0]
    assert record["selected_count"] == record["skipped_count"] == 2
    assert record["prepared_count"] == record["accepted_count"] == 0
    assert record["provider_contacted"] is False


@pytest.mark.parametrize("bad_email, expected_reason", [(None, "invalid_record"), ("", "invalid_email"), (123, "invalid_record")])
def test_invalid_email_position_is_counted_without_backfill(monkeypatch, bad_email, expected_reason):
    rows = [subscriber(i, breaking_news=True) for i in range(1, 1002)]
    if bad_email is None:
        rows[0].pop("email")
    else:
        rows[0]["email"] = bad_email
    service = EmailService()
    service.resend_enabled = False
    calls = []
    def smtp(to, *a, **k):
        service.last_provider_contacted = True
        calls.append(to)
        return True
    monkeypatch.setattr(service, "_send_email", smtp)
    db, _ = run_endpoint(monkeypatch, rows, service)
    record = db.digest_log.inserts[0]
    assert len(calls) == 999
    assert calls == [r["email"] for r in rows[1:1000]]
    assert (record["selected_count"], record["prepared_count"], record["skipped_count"], record["accepted_count"]) == (1000, 999, 1, 999)
    assert record["skip_reasons"] == {expected_reason: 1}
    assert record["provider_contacted"] is True


def test_daily_weekly_and_push_sources_unchanged():
    def function(source, name):
        tree = ast.parse(source)
        node = next(n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)
        return ast.dump(node, include_attributes=False)
    for path, names in [("backend/server.py", ["send_breaking_news_notification"]),
                        ("backend/app/email_service.py", ["send_daily_brief", "send_weekly_roundup"])]:
        baseline = subprocess.check_output(["git", "show", "fc8b34c:" + path], text=True)
        from pathlib import Path
        current = Path(path).read_text()
        for name in names:
            assert function(current, name) == function(baseline, name)
    assert "Depends(get_admin_auth)" in inspect.getsource(server.send_breaking_news_alert)
