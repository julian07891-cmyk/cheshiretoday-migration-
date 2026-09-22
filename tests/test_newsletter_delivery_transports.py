"""All providers are replaced: no network, production secrets or real email."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from email import message_from_string
from pathlib import Path
from types import SimpleNamespace
import sys
from uuid import UUID

import httpx
import pytest

BACKEND_ROOT = str(Path(__file__).parents[1] / "backend")
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)
from app import email_service as module
from app.newsletter_delivery import (
    NewsletterDeliveryError, RecipientDeliveryContext, prepare_direct_delivery,
)
from app.newsletter_token_service import NewsletterTokenService
from app.newsletter_management_email import (
    NewsletterManagementEmailHelper, NewsletterManagementEmailPurpose,
    NewsletterManagementEmailRequest,
)


@pytest.fixture
def service(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Real transport forbidden in offline tests")
    monkeypatch.setattr(module.httpx, "post", forbidden)
    monkeypatch.setattr(module.smtplib, "SMTP", forbidden)
    monkeypatch.setattr(module.smtplib, "SMTP_SSL", forbidden)
    service = module.EmailService()
    service.smtp_enabled = service.resend_enabled = True
    service.smtp_host, service.smtp_port = "smtp.synthetic.invalid", 587
    service.smtp_user, service.smtp_password = "synthetic-user", "synthetic-password"
    service.from_email = service.resend_from_email = "news@synthetic.invalid"
    service.resend_api_key = "synthetic-key"
    service.last_accepted_recipients = []
    service.resend_last_successful_chunks = service.resend_last_failed_chunks = 0
    service.resend_last_error = None
    return service


def headers(index=1):
    context = RecipientDeliveryContext(
        f"reader{index}@synthetic.invalid", str(UUID(int=index, version=4)), 1,
    )
    return dict(prepare_direct_delivery(context, NewsletterTokenService("D" * 43)).native_headers)


def safe_headers(index=1):
    return prepare_direct_delivery(
        RecipientDeliveryContext(f"reader{index}@synthetic.invalid", str(UUID(int=index, version=4)), 1),
        NewsletterTokenService("D" * 43),
    ).native_headers


def test_safe_container_resend_export_and_provider_mutation(service, monkeypatch):
    messages = [message(i, native=False) for i in range(1, 102)]
    containers = [safe_headers(i) for i in range(1, 102)]
    expected = [h.as_transport_dict() for h in containers]
    for item, container in zip(messages, containers):
        item["headers"] = container
    captured = []
    def post(url, *, headers, json, timeout):
        for item in json:
            assert type(item["headers"]) is dict
            captured.append(item["headers"].copy())
            item["headers"].clear()
        return response()
    monkeypatch.setattr(module.httpx, "post", post)
    assert service._send_resend_batch(messages) == 101
    assert captured == expected
    assert [h.as_transport_dict() for h in containers] == expected


@pytest.mark.parametrize("port", [465, 587])
def test_safe_container_smtp_export(service, smtp, port):
    service.smtp_port = port
    first, second = safe_headers(1), safe_headers(2)
    for native in (first, second, None):
        assert service._send_email("reader@synthetic.invalid", "Subject", "Body",
                                   newsletter_headers=native)
    assert smtp[0]["List-Unsubscribe"] == first["List-Unsubscribe"]
    assert smtp[1]["List-Unsubscribe"] == second["List-Unsubscribe"]
    assert smtp[2]["List-Unsubscribe"] is None


def message(index=1, *, native=True):
    item = {"to": f"reader{index}@synthetic.invalid", "subject": "Synthetic subject",
            "html": "<p>Body</p>", "text": "Body"}
    if native:
        item["headers"] = headers(index)
    return item


def response(status=200):
    return httpx.Response(status, request=httpx.Request("POST", "https://synthetic.invalid"))


def test_resend_opt_in_isolation_and_chunk_boundary(service, monkeypatch):
    messages = [message(i) for i in range(1, 102)] + [message(102, native=False)]
    expected = deepcopy(messages)
    calls = []
    live_payloads = []

    def post(url, *, headers, json, timeout):
        assert set(headers) == {"Authorization", "Content-Type"}
        assert timeout == 60.0
        calls.append(deepcopy(json))
        live_payloads.extend(json)
        # Later recipient input mutation cannot affect the already validated copy.
        messages[100]["headers"].clear()
        json[0]["headers"]["List-Unsubscribe"] = "provider-side mutation"
        return response()

    monkeypatch.setattr(module.httpx, "post", post)
    assert service._send_resend_batch(messages) == 102
    assert [len(call) for call in calls] == [100, 2]
    flattened = calls[0] + calls[1]
    assert all(flattened[i]["headers"] == expected[i]["headers"] for i in range(101))
    assert len({item["headers"]["List-Unsubscribe"] for item in flattened[:101]}) == 101
    assert "headers" not in flattened[-1]
    assert len({id(item["headers"]) for item in live_payloads[:101]}) == 101
    assert flattened[0]["text"] == "Body"
    assert flattened[0]["to"] == [expected[0]["to"]]
    assert service.last_accepted_recipients == [item["to"] for item in messages]
    assert service.resend_last_successful_chunks == 2


@pytest.mark.parametrize("failure", ["status", "exception"])
def test_resend_failure_preserves_chunk_accounting_without_sensitive_logs(service, monkeypatch, caplog, failure):
    messages = [message(i) for i in range(1, 102)]
    secret = messages[0]["headers"]["List-Unsubscribe"]
    calls = []
    def post(*args, **kwargs):
        calls.append(kwargs["json"])
        if len(calls) == 1:
            if failure == "exception":
                raise RuntimeError(secret + repr(kwargs["json"]))
            return response(400)
        return response()
    monkeypatch.setattr(module.httpx, "post", post)
    assert service._send_resend_batch(messages) == 1
    assert len(calls) == 2  # No retry; the next chunk still runs.
    assert service.last_accepted_recipients == [messages[-1]["to"]]
    assert service.resend_last_failed_chunks == service.resend_last_successful_chunks == 1
    diagnostic = caplog.text + service.resend_last_error
    assert secret not in diagnostic and "List-Unsubscribe" not in diagnostic
    assert "reader1@synthetic.invalid" not in diagnostic


def test_resend_invalid_late_header_rejected_before_any_provider_contact(service, monkeypatch):
    calls = []
    monkeypatch.setattr(module.httpx, "post", lambda *a, **k: calls.append(k))
    messages = [message(i) for i in range(1, 102)]
    messages[-1]["headers"]["Bcc"] = "injected"
    with pytest.raises(NewsletterDeliveryError, match="^invalid_newsletter_headers$"):
        service._send_resend_batch(messages)
    assert not calls and not service.last_accepted_recipients


@pytest.fixture
def smtp(monkeypatch):
    captured = []
    class FakeSMTP:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def ehlo(self):
            pass
        def starttls(self, **kwargs):
            pass
        def login(self, *args):
            pass
        def sendmail(self, sender, recipient, wire):
            captured.append(message_from_string(wire))
    monkeypatch.setattr(module.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(module.smtplib, "SMTP_SSL", FakeSMTP)
    return captured


@pytest.mark.parametrize("port", [465, 587])
def test_smtp_headers_opt_in_isolated_and_multipart_preserved(service, smtp, port):
    service.smtp_port = port
    first, second = headers(1), headers(2)
    expected = deepcopy(first)
    for native in (first, second, None):
        assert service._send_email("reader@synthetic.invalid", "Subject", "<b>HTML</b>", "Text",
                                   newsletter_headers=native)
    first.clear()
    assert smtp[0]["List-Unsubscribe"] == expected["List-Unsubscribe"]
    assert smtp[1]["List-Unsubscribe"] == second["List-Unsubscribe"]
    assert smtp[2]["List-Unsubscribe"] is None
    assert smtp[2]["List-Unsubscribe-Post"] is None
    for mime in smtp:
        assert mime["Subject"] == "Subject"
        assert mime["To"] == "reader@synthetic.invalid"
        assert mime["From"] == f"{service.from_name} <{service.from_email}>"
        assert mime.get_content_type() == "multipart/alternative"
        assert [part.get_content_type() for part in mime.get_payload()] == ["text/plain", "text/html"]


@pytest.mark.parametrize("bad", [{"Bcc": "other"}, {"List-Unsubscribe": 1},
                                 {"List-Unsubscribe": "\r\nBcc: other"}])
def test_smtp_rejects_invalid_headers_before_contact(service, smtp, bad):
    with pytest.raises(NewsletterDeliveryError, match="^invalid_newsletter_headers$"):
        service._send_email("reader@synthetic.invalid", "Subject", "Body", newsletter_headers=bad)
    assert not smtp


def test_smtp_exception_does_not_log_native_values(service, monkeypatch, caplog):
    native = headers()
    class FailingSMTP:
        def __init__(self, *args, **kwargs):
            raise RuntimeError(repr(native))
    monkeypatch.setattr(module.smtplib, "SMTP", FailingSMTP)
    assert not service._send_email("reader@synthetic.invalid", "Subject", "Body", newsletter_headers=native)
    assert native["List-Unsubscribe"] not in caplog.text
    assert "List-Unsubscribe" not in caplog.text


def test_welcome_verification_and_operational_messages_stay_header_free(service, smtp):
    assert service.send_welcome_email("reader@synthetic.invalid")
    assert service.send_verification_code("reader@synthetic.invalid", "Reader", "123456")
    assert service.send_job_approved_email("reader@synthetic.invalid", "Reader", "Role", "Company")
    assert service.send_job_rejected_email("reader@synthetic.invalid", "Reader", "Role", "Company")
    assert len(smtp) == 4
    assert all(mime["List-Unsubscribe"] is None and mime["List-Unsubscribe-Post"] is None for mime in smtp)


@pytest.mark.parametrize("purpose", list(NewsletterManagementEmailPurpose))
def test_management_recovery_preferences_reactivation_remain_header_free(service, monkeypatch, purpose):
    now = datetime.now(timezone.utc)
    helper = NewsletterManagementEmailHelper(
        transport=SimpleNamespace(send_transactional=service.send_newsletter_management_transactional),
        site_origin="https://cheshiretoday.co.uk",
    )
    management_message = helper.build_message(NewsletterManagementEmailRequest(
        recipient_email="reader@synthetic.invalid", purpose=purpose,
        token="synthetic-management-token", expires_at=now + timedelta(minutes=30),
    ), now=now)
    calls = []
    def post(*args, **kwargs):
        calls.append(kwargs)
        return response()
    monkeypatch.setattr(module.httpx, "post", post)
    assert service.send_newsletter_management_transactional(management_message)
    assert len(calls) == 1
    assert "headers" not in calls[0]["json"]
    assert set(calls[0]["headers"]) == {"Authorization", "Content-Type"}
