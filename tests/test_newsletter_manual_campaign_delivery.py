"""Slice 6 offline campaign delivery, preview isolation and fetched-slot contracts."""
import asyncio
import ast
from copy import deepcopy
from email import message_from_string
from pathlib import Path
import smtplib
import subprocess
from types import SimpleNamespace

import httpx
import pytest

from backend import server
from app.email_service import EmailService
from app.newsletter_delivery import (
    NewsletterDeliveryError, PreparedNewsletterDelivery, RecipientDeliveryContext,
    prepare_direct_delivery,
)
from app.newsletter_token_service import NewsletterTokenService
from tests.test_newsletter_daily_delivery import subscriber, deliveries, TOKEN_SERVICE, check_message


ACTIVE = {"$or": [{"active": True}, {"active": {"$exists": False}}]}
PROVIDER_ELIGIBLE = {"$and": [ACTIVE, {"provider_suppressed": {"$ne": True}}]}
SUBJECT = "Arbitrary campaign — September & beyond"
HTML = '<body><h2>Custom campaign</h2><a href="__PREFS_URL__">Preferences</a><a href="__UNSUB_URL__">Unsubscribe</a></body>'
TEXT = "Custom campaign\nPreferences: __PREFS_URL__\nUnsubscribe: __UNSUB_URL__"
TRACKING = "ManualCampaign_synthetic"
PREFS = "https://cheshiretoday.co.uk/newsletter/preferences"
GENERIC = "https://cheshiretoday.co.uk/unsubscribe"
COUNTS = {"selected_count", "prepared_count", "skipped_count", "skip_reasons", "accepted_count", "provider_contacted"}
HISTORICAL = {"sent_at", "digest_time", "type", "subscribers_count", "success_count", "mode", "subject", "tracking_id"}


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Real transport forbidden")
    monkeypatch.setattr("app.email_service.httpx.post", forbidden)
    monkeypatch.setattr("app.email_service.smtplib.SMTP", forbidden)
    monkeypatch.setattr("app.email_service.smtplib.SMTP_SSL", forbidden)
    monkeypatch.setattr(server, "newsletter_token_service_from_environment", lambda: TOKEN_SERVICE)


def send(service, prepared, **content):
    return service.send_manual_campaign(subject=SUBJECT, tracking_id=TRACKING,
        prepared_deliveries=prepared, token_service=TOKEN_SERVICE,
        **({"html": HTML, "text": TEXT} | content))


@pytest.mark.parametrize("resend", [False, True])
@pytest.mark.parametrize("outcome", ["all", "partial", "zero", "unavailable", "exception"])
def test_transports_isolation_and_acceptance(monkeypatch, caplog, resend, outcome):
    service = EmailService()
    service.resend_enabled = resend
    service.resend_api_key = None if outcome == "unavailable" else "synthetic"
    service.smtp_enabled = False
    service.from_email = "sender@synthetic.invalid"
    messages, chunks = [], []
    def post(url, *, json, **kwargs):
        chunks.append(len(json))
        messages.extend([{**m, "to": m["to"][0]} for m in json])
        if outcome == "exception": raise httpx.ConnectError("PRIVATE_TOKEN secret@synthetic.invalid")
        ok = outcome == "all" or outcome == "partial" and len(chunks) == 2
        return httpx.Response(200 if ok else 400, request=httpx.Request("POST", "https://synthetic.invalid"))
    def smtp(to, subject, html, text, *, newsletter_headers, feedback_id):
        assert feedback_id == "manual:::cheshtoday"
        service.last_provider_contacted = True
        messages.append({"to": to, "subject": subject, "html": html, "text": text, "headers": newsletter_headers})
        return outcome == "all" or outcome == "partial" and len(messages) == 101
    monkeypatch.setattr("app.email_service.httpx.post", post)
    if outcome != "unavailable": monkeypatch.setattr(service, "_send_email", smtp)
    service.last_accepted_recipients, service.last_provider_contacted = ["stale"], True
    service.resend_last_successful_chunks = service.resend_last_failed_chunks = 99
    service.resend_last_error = "stale"
    prepared = deliveries(101)
    count = send(service, prepared)
    expected = 101 if outcome == "all" else 1 if outcome == "partial" else 0
    assert type(count) is int and count == expected
    assert service.last_provider_contacted is (outcome != "unavailable")
    assert service.last_accepted_recipients == ([a.context.email for a in prepared] if expected == 101 else
                                              [prepared[-1].context.email] if expected == 1 else [])
    if resend and outcome != "unavailable":
        assert chunks == [100, 1]
        successful = 2 if outcome == "all" else 1 if outcome == "partial" else 0
        assert service.resend_last_successful_chunks == successful
        assert service.resend_last_failed_chunks == 2 - successful
    else:
        assert service.resend_last_successful_chunks == service.resend_last_failed_chunks == 0
        assert service.resend_last_error is None
    for message, artifact in zip(messages, prepared):
        check_message(message, artifact)
        assert message["to"] == artifact.context.email and message["subject"] == SUBJECT
        assert f'href="{artifact.human_unsubscribe_url}"' in message["html"]
        assert f"/email/track/open/{TRACKING}" in message["html"]
        assert "/email/track/click/" not in message["html"]
        assert artifact.human_unsubscribe_url not in caplog.text
        assert artifact.context.email not in caplog.text
        assert prepared[-1 if artifact is prepared[0] else 0].human_unsubscribe_url not in message["html"]
    assert "PRIVATE_TOKEN" not in caplog.text and "secret@" not in caplog.text


@pytest.mark.parametrize("count", [100, 101])
def test_resend_exact_chunk_boundary(monkeypatch, count):
    service = EmailService()
    service.resend_enabled, service.resend_api_key = True, "synthetic"
    service.from_email = "sender@synthetic.invalid"
    chunks = []
    def post(url, *, json, **kwargs):
        chunks.append(len(json))
        return httpx.Response(200, request=httpx.Request("POST", "https://synthetic.invalid"))
    monkeypatch.setattr("app.email_service.httpx.post", post)
    assert send(service, deliveries(count)) == count
    assert chunks == ([100] if count == 100 else [100, 1])


@pytest.mark.parametrize("resend", [False, True])
@pytest.mark.parametrize("html,text", [(HTML, None), (None, TEXT), (HTML, TEXT),
    ("<p>__PREFS_URL__ __UNSUB_URL__</p>", None), ("<b>Unmodified custom markup</b>", "Unmodified text")])
def test_arbitrary_content_and_placeholder_semantics(monkeypatch, resend, html, text):
    service = EmailService()
    service.resend_enabled = resend
    messages = []
    def batch(items):
        messages.extend(items)
        return len(items)
    def smtp(to, subject, html, text, *, newsletter_headers, feedback_id):
        messages.append({"to": to, "subject": subject, "html": html, "text": text,
                         "headers": newsletter_headers, "feedback_id": feedback_id})
        return True
    monkeypatch.setattr(service, "_send_resend_batch", batch)
    monkeypatch.setattr(service, "_send_email", smtp)
    a = deliveries(1)[0]
    assert send(service, [a], html=html, text=text) == 1
    replace = lambda value: value.replace("__PREFS_URL__", PREFS).replace("__UNSUB_URL__", a.human_unsubscribe_url)
    expected_text = replace(text) if text else None
    if html:
        pixel = service._get_tracking_pixel(TRACKING)
        expected_html = replace(html.replace("</body>", pixel + "</body>") if "</body>" in html else html + pixel)
    else:
        expected_html = "<p>" + (expected_text or "") + "</p>"
    assert messages == [{"to": a.context.email, "subject": SUBJECT, "html": expected_html,
                         "text": expected_text, "headers": a.native_headers,
                         "feedback_id": "manual:::cheshtoday"}]


@pytest.mark.parametrize("port", [465, 587])
@pytest.mark.parametrize("outcome", ["all", "partial", "zero"])
def test_smtp_mime_headers_and_contact(monkeypatch, port, outcome):
    service = EmailService()
    service.resend_enabled, service.smtp_enabled = False, True
    service.smtp_host, service.smtp_port = "smtp.synthetic.invalid", port
    service.smtp_user, service.smtp_password = "synthetic", "synthetic"
    service.from_email = "sender@synthetic.invalid"
    messages = []
    class SMTP:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def ehlo(self): pass
        def starttls(self, **kwargs): pass
        def login(self, *args): pass
        def sendmail(self, from_email, to, content):
            msg = message_from_string(content)
            body = {p.get_content_type(): p.get_payload(decode=True).decode() for p in msg.get_payload()}
            messages.append({"html": body["text/html"], "text": body["text/plain"], "headers": dict(msg.items())})
            assert msg["To"] == to
            if outcome == "zero" or outcome == "partial" and len(messages) == 1:
                raise smtplib.SMTPRecipientsRefused({to: (550, b"synthetic")})
    monkeypatch.setattr("app.email_service.smtplib.SMTP", SMTP)
    monkeypatch.setattr("app.email_service.smtplib.SMTP_SSL", SMTP)
    prepared = deliveries(2)
    assert send(service, prepared) == (2 if outcome == "all" else 1 if outcome == "partial" else 0)
    assert service.last_provider_contacted
    assert service.last_accepted_recipients == ([a.context.email for a in prepared] if outcome == "all" else
                                              [prepared[1].context.email] if outcome == "partial" else [])
    for message, a in zip(messages, prepared): check_message(message, a)


@pytest.mark.parametrize("resend", [False, True])
@pytest.mark.parametrize("kind", ["swap", "human", "native", "malformed", "forged", "uuid", "version", "headers"])
def test_complete_batch_rejection_before_rendering(monkeypatch, resend, kind):
    a, b = deliveries(2)
    broken = object.__new__(PreparedNewsletterDelivery)
    for key, value in [("context", a.context), ("human_unsubscribe_url", a.human_unsubscribe_url),
                       ("native_headers", {**dict(a.native_headers), "Unexpected": "header"})]:
        object.__setattr__(broken, key, value)
    bad = {
        "swap": PreparedNewsletterDelivery(a.context, b.human_unsubscribe_url, b.native_headers),
        "human": PreparedNewsletterDelivery(a.context, b.human_unsubscribe_url, a.native_headers),
        "native": PreparedNewsletterDelivery(a.context, a.human_unsubscribe_url, b.native_headers),
        "malformed": PreparedNewsletterDelivery(a.context, a.human_unsubscribe_url + "&token=x", a.native_headers),
        "forged": prepare_direct_delivery(a.context, NewsletterTokenService("E" * 43)),
        "uuid": PreparedNewsletterDelivery(b.context, a.human_unsubscribe_url, a.native_headers),
        "version": PreparedNewsletterDelivery(RecipientDeliveryContext(a.context.email,
            a.context.newsletter_management_id, 2), a.human_unsubscribe_url, a.native_headers),
        "headers": broken,
    }[kind]
    service = EmailService()
    service.resend_enabled = resend
    calls = []
    for method in ["_get_tracking_pixel", "_send_email", "_send_resend_batch"]:
        monkeypatch.setattr(service, method, lambda *a, **k: calls.append(1))
    with pytest.raises(NewsletterDeliveryError, match="^invalid_prepared_delivery$"):
        send(service, [a, bad, b])
    assert not calls and not service.last_provider_contacted and not service.last_accepted_recipients


@pytest.mark.parametrize("kwargs", [{}, {"to_emails": []}, {"to_emails": ["raw@synthetic.invalid"]},
    {"prepared_deliveries": deliveries(1)},
    {"prepared_deliveries": deliveries(1), "to_emails": ["raw@synthetic.invalid"], "token_service": TOKEN_SERVICE}])
def test_prepared_only_contract_resets_diagnostics(kwargs):
    service = EmailService()
    service.last_provider_contacted, service.last_accepted_recipients = True, ["stale"]
    service.resend_last_error = "stale"
    service.resend_last_successful_chunks = service.resend_last_failed_chunks = 99
    with pytest.raises(NewsletterDeliveryError):
        service.send_manual_campaign(subject=SUBJECT, tracking_id=TRACKING, **kwargs)
    assert not service.last_provider_contacted and not service.last_accepted_recipients
    assert service.resend_last_error is None
    assert service.resend_last_successful_chunks == service.resend_last_failed_chunks == 0


def test_empty_prepared_set_returns_integer_zero_without_rendering(monkeypatch):
    service = EmailService()
    monkeypatch.setattr(service, "_get_tracking_pixel", lambda *a: pytest.fail("Rendered empty batch"))
    count = service.send_manual_campaign(subject=SUBJECT, html=HTML, tracking_id=TRACKING, prepared_deliveries=[])
    assert type(count) is int and count == 0
    assert not service.last_provider_contacted and not service.last_accepted_recipients


class Subscribers:
    def __init__(self, rows):
        self.rows, self.queries, self.limits = deepcopy(rows), [], []
    def find(self, query, projection):
        self.queries.append((query, projection))
        assert query == PROVIDER_ELIGIBLE
        assert projection == {"_id": 0, "email": 1, "active": 1, "newsletter_management_id": 1, "newsletter_token_version": 1, "provider_suppressed": 1}
        rows = [r for r in self.rows if ("active" not in r or r["active"] is True
                or isinstance(r["active"], list) and any(v is True for v in r["active"]))
                and r.get("provider_suppressed") is not True]
        collection = self
        class Cursor:
            async def to_list(self, limit):
                collection.limits.append(limit)
                return [{k: deepcopy(v) for k, v in row.items() if projection.get(k)} for row in rows[:limit]]
        return Cursor()


def setup(monkeypatch, rows=(), outcome="all", resend=False):
    service = EmailService()
    service.resend_enabled, service.smtp_enabled = resend, False
    service.resend_api_key = None if outcome == "unavailable" else "synthetic"
    service.from_email = "sender@synthetic.invalid"
    calls, logs, chunks, tracking_calls = [], [], [], []
    def tracking(kind):
        tracking_calls.append(kind)
        return TRACKING
    monkeypatch.setattr(service, "_generate_tracking_id", tracking)
    def smtp(to, subject, html, text, **kwargs):
        service.last_provider_contacted = True
        calls.append({"to": to, "subject": subject, "html": html, "text": text, **kwargs})
        return outcome == "all" or outcome == "partial" and len(calls) == 101
    if outcome != "unavailable": monkeypatch.setattr(service, "_send_email", smtp)
    def post(url, *, json, **kwargs):
        chunks.append(len(json))
        calls.extend(json)
        ok = outcome == "all" or outcome == "partial" and len(chunks) == 2
        return httpx.Response(200 if ok else 400, request=httpx.Request("POST", "https://synthetic.invalid"))
    monkeypatch.setattr("app.email_service.httpx.post", post)
    async def insert(record):
        logs.append(record)
    db = SimpleNamespace(subscribers=Subscribers(rows), digest_log=SimpleNamespace(insert_one=insert))
    monkeypatch.setattr(server, "db", db)
    monkeypatch.setattr(server, "email_service", service)
    return SimpleNamespace(db=db, service=service, calls=calls, logs=logs, chunks=chunks, tracking_calls=tracking_calls)


def endpoint(**kwargs):
    request = server.CampaignEmailRequest(**({"subject": SUBJECT, "html": HTML, "text": TEXT, "mode": "all"} | kwargs))
    return asyncio.run(server.admin_send_campaign_email(request))


def assert_record(record, selected, prepared, accepted, contacted):
    assert set(record) == HISTORICAL | COUNTS
    assert record["digest_time"] == record["type"] == "ManualCampaign"
    assert record["mode"] == "all" and record["subject"] == SUBJECT and record["tracking_id"] == TRACKING
    assert record["selected_count"] == record["subscribers_count"] == selected
    assert record["prepared_count"] == prepared
    assert record["skipped_count"] == sum(record["skip_reasons"].values()) == selected - prepared
    assert record["accepted_count"] == record["success_count"] == accepted
    assert record["provider_contacted"] is contacted
    assert "synthetic.invalid" not in str(record) and "token=" not in str(record)


@pytest.mark.parametrize("resend", [False, True])
@pytest.mark.parametrize("outcome", ["all", "partial", "zero", "unavailable"])
def test_endpoint_provider_and_digest_accounting(monkeypatch, resend, outcome):
    state = setup(monkeypatch, [subscriber(i) for i in range(1, 102)], outcome, resend)
    result = endpoint()
    expected = 101 if outcome == "all" else 1 if outcome == "partial" else 0
    assert_record(state.logs[0], 101, 101, expected, outcome != "unavailable")
    assert state.db.subscribers.limits == [10000]
    assert state.tracking_calls == ["ManualCampaign"]
    assert result == {"success": True, "message": f"Campaign sent to {expected}/101 recipients", "mode": "all", "tracking_id": TRACKING}
    assert len(state.service.last_accepted_recipients) == expected


def test_real_query_cap_invalid_positions_no_backfill(monkeypatch):
    rows = [subscriber(i) for i in range(1, 10002)]
    for row in rows[1:10000]: row.pop("newsletter_management_id")
    excluded = [subscriber(20000 + i, active=state) for i, state in enumerate([False, None, 1, "true", [False]])]
    excluded.append(subscriber(20010, provider_suppressed=True))
    state = setup(monkeypatch, excluded + rows)
    result = endpoint()
    assert_record(state.logs[0], 10000, 1, 1, True)
    assert len(state.calls) == 1 and state.calls[0]["to"] == rows[0]["email"]
    assert result["message"] == "Campaign sent to 1/10000 recipients"


@pytest.mark.parametrize("field,value", [("email", "missing"), ("email", None), ("email", 123), ("email", ""),
    ("active", "missing"), ("active", [True]), ("newsletter_management_id", "missing"),
    ("newsletter_management_id", "bad"), ("newsletter_token_version", "missing"),
    ("newsletter_token_version", True), ("newsletter_token_version", "1"), ("newsletter_token_version", 0)])
def test_invalid_fetched_slot_is_counted(monkeypatch, field, value):
    row = subscriber()
    if value == "missing": row.pop(field)
    else: row[field] = value
    state = setup(monkeypatch, [row])
    assert endpoint()["success"] is True
    assert_record(state.logs[0], 1, 0, 0, False)
    if field == "active": assert state.logs[0]["skip_reasons"] == {"invalid_active_state": 1}
    assert not state.calls


@pytest.mark.parametrize("field", ["email", "newsletter_management_id"])
@pytest.mark.parametrize("reverse", [False, True])
def test_full_candidate_ambiguity(monkeypatch, field, reverse):
    rows = [subscriber(), subscriber(2)]
    rows[1][field] = rows[0][field].upper() if field == "email" else rows[0][field]
    state = setup(monkeypatch, rows[::-1] if reverse else rows)
    endpoint()
    assert_record(state.logs[0], 2, 0, 0, False)
    assert not state.calls


@pytest.mark.parametrize("rows", [[], [subscriber(active=False)]])
def test_no_subscribers_preserves_response(monkeypatch, rows):
    state = setup(monkeypatch, rows)
    assert endpoint() == {"success": False, "message": "No subscribers found"}
    assert not state.calls and not state.logs and not state.tracking_calls


@pytest.mark.parametrize("resend", [False, True])
@pytest.mark.parametrize("html,text", [(HTML, None), (None, TEXT), (HTML, TEXT)])
@pytest.mark.parametrize("test_email", [" PREVIEW@synthetic.invalid ", None])
def test_preview_has_no_subscriber_or_direct_delivery_path(monkeypatch, resend, html, text, test_email):
    state = setup(monkeypatch, resend=resend)
    monkeypatch.setattr(server, "ADMIN_USERNAME", "ADMIN@synthetic.invalid")
    def forbidden(*args, **kwargs): pytest.fail("Preview crossed subscriber boundary")
    monkeypatch.setattr(state.db.subscribers, "find", forbidden)
    for name in ["_newsletter_candidate_contexts", "_prepare_selected_newsletter_deliveries",
                 "prepare_direct_delivery", "newsletter_token_service_from_environment"]:
        monkeypatch.setattr(server, name, forbidden)
    monkeypatch.setattr(state.service, "send_manual_campaign", forbidden)
    monkeypatch.setattr(state.service, "_send_resend_batch", forbidden)
    result = endpoint(mode="test", test_email=test_email, html=html, text=text)
    assert len(state.calls) == 1 and state.calls[0]["to"] == ("preview@synthetic.invalid" if test_email else "admin@synthetic.invalid")
    message = state.calls[0]
    assert "newsletter_headers" not in message and "headers" not in message
    replace = lambda value: value.replace("__PREFS_URL__", PREFS).replace("__UNSUB_URL__", GENERIC)
    expected_text = replace(text) if text else None
    pixel = state.service._get_tracking_pixel(TRACKING)
    expected_html = replace(html.replace("</body>", pixel + "</body>")) if html else "<p>" + expected_text + "</p>"
    assert message["html"] == expected_html and message["text"] == expected_text
    assert "token=" not in str(message) and not hasattr(state.service, "last_accepted_recipients")
    # Retain the historical explicitly test-mode record, without subscriber delivery accounting.
    assert set(state.logs[0]) == HISTORICAL
    assert state.logs[0]["mode"] == "test" and state.logs[0]["subscribers_count"] == 1
    assert result["mode"] == "test" and state.tracking_calls == ["ManualCampaign"]


@pytest.mark.parametrize("changes,detail", [({"subject": " "}, "Subject is required"),
    ({"html": " ", "text": None}, "Provide at least html or text content"),
    ({"mode": "other"}, "mode must be 'test' or 'all'"),
    ({"mode": "test", "test_email": " "}, "test_email is required for test mode")])
def test_validation_unchanged(monkeypatch, changes, detail):
    state = setup(monkeypatch)
    with pytest.raises(server.HTTPException) as error: endpoint(**changes)
    assert error.value.status_code == 400 and error.value.detail == detail
    assert not state.db.subscribers.queries and not state.calls and not state.logs


@pytest.mark.parametrize("failure", ["configuration", "signing", "query", "sender", "http_exception", "digest"])
def test_private_failures(monkeypatch, caplog, failure):
    state = setup(monkeypatch, [subscriber()])
    def fail(*args, **kwargs): raise ValueError("PRIVATE_TOKEN secret@synthetic.invalid")
    if failure in ("configuration", "signing"):
        monkeypatch.setattr(server, "newsletter_token_service_from_environment" if failure == "configuration" else "prepare_direct_delivery", fail)
        endpoint()
        assert_record(state.logs[0], 1, 0, 0, False)
        assert state.logs[0]["skip_reasons"] == {"direct_delivery_preparation_failed": 1}
        assert not state.calls
    else:
        if failure == "query": monkeypatch.setattr(state.db.subscribers, "find", fail)
        elif failure in ("sender", "http_exception"):
            if failure == "http_exception":
                def fail(*args, **kwargs): raise server.HTTPException(400, detail="PRIVATE_TOKEN secret@synthetic.invalid")
            monkeypatch.setattr(state.service, "send_manual_campaign", fail)
        else: monkeypatch.setattr(state.db.digest_log, "insert_one", fail)
        with pytest.raises(server.HTTPException) as error: endpoint()
        assert error.value.status_code == 500 and error.value.detail == "Manual campaign email unavailable"
        assert not state.logs
        if failure != "digest": assert not state.calls
    assert "PRIVATE_TOKEN" not in caplog.text and "secret@" not in caplog.text


def test_preview_unexpected_failure_is_private(monkeypatch, caplog):
    state = setup(monkeypatch)
    def fail(*args, **kwargs): raise RuntimeError("PRIVATE_TOKEN secret@synthetic.invalid")
    monkeypatch.setattr(state.service, "_send_email", fail)
    with pytest.raises(server.HTTPException) as error: endpoint(mode="test", test_email="preview@synthetic.invalid")
    assert error.value.status_code == 500 and error.value.detail == "Manual campaign email unavailable"
    assert not state.logs and not state.db.subscribers.queries
    assert "PRIVATE_TOKEN" not in caplog.text and "secret@" not in caplog.text


def test_slice6_campaign_interface_guards_remain():
    old = ast.parse(subprocess.check_output(["git", "show", "3fe466e:backend/server.py"], text=True))
    current = ast.parse(Path("backend/server.py").read_text())
    old_endpoint = next(node for node in ast.walk(old) if isinstance(node, ast.AsyncFunctionDef) and node.name == "admin_send_campaign_email")
    current_endpoint = next(node for node in ast.walk(current) if isinstance(node, ast.AsyncFunctionDef) and node.name == "admin_send_campaign_email")
    assert ast.dump(old_endpoint.args, include_attributes=False) == ast.dump(current_endpoint.args, include_attributes=False)
    assert [ast.dump(node, include_attributes=False) for node in old_endpoint.decorator_list] == [ast.dump(node, include_attributes=False) for node in current_endpoint.decorator_list]

    service = ast.parse(Path("backend/app/email_service.py").read_text())
    cls = next(node for node in service.body if isinstance(node, ast.ClassDef) and node.name == "EmailService")
    methods = [node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "send_manual_campaign"]
    assert len(methods) == 1
