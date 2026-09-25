"""Offline Feedback-ID coverage through real message builders/transports."""
import pytest

from tests.test_newsletter_delivery_transports import (
    module, service, smtp, response, headers, message,
    RecipientDeliveryContext, prepare_direct_delivery, NewsletterTokenService,
    NewsletterManagementEmailHelper, NewsletterManagementEmailPurpose,
    NewsletterManagementEmailRequest, datetime, timezone, timedelta, SimpleNamespace,
)

ARTICLE = {"id": "synthetic", "title": "Local news", "summary": "Local news summary",
           "content": "Local news content", "category": "Business", "image": ""}
FAMILIES = [
    ("send_daily_brief", "daily", {"articles": [ARTICLE]}),
    ("send_weekly_roundup", "weekly", {"big_read": ARTICLE, "icymi_articles": []}),
    ("send_breaking_news", "breaking", {"headline": "News", "bullet_points": ["Update"]}),
    ("send_site_update_part1", "siteupdate", {}),
    ("send_site_update_part2", "siteupdate", {}),
    ("send_manual_campaign", "manual", {"subject": "News", "html": "__UNSUB_URL__",
                                         "text": "__PREFS_URL__", "tracking_id": "synthetic"}),
]


@pytest.mark.parametrize("method,family,kwargs", FAMILIES)
@pytest.mark.parametrize("transport", ["resend", "smtp465", "smtp587"])
def test_campaign_feedback_at_wire_boundary(service, smtp, monkeypatch, method, family, kwargs, transport):
    tokens = NewsletterTokenService("D" * 43)
    deliveries = [prepare_direct_delivery(RecipientDeliveryContext(
        f"reader{i}@synthetic.invalid", f"00000000-0000-4000-8000-{i:012d}", 1), tokens)
        for i in (1, 2)]
    originals = [dict(d.native_headers) for d in deliveries]
    captured = []
    def post(url, *, headers, json, timeout):
        assert "Feedback-ID" not in headers  # Not an HTTP header.
        captured.extend(json)
        return response()
    monkeypatch.setattr(module.httpx, "post", post)
    service.resend_enabled = transport == "resend"
    service.smtp_port = 465 if transport == "smtp465" else 587
    getattr(service, method)(prepared_deliveries=deliveries, token_service=tokens, **kwargs)
    assert len(captured if service.resend_enabled else smtp) == 2
    for i, native in enumerate(originals):
        if service.resend_enabled:
            actual = captured[i]["headers"]
            assert actual == {**native, "Feedback-ID": f"{family}:::cheshtoday"}
        else:
            assert smtp[i].get_all("Feedback-ID") == [f"{family}:::cheshtoday"]
            assert all(smtp[i][k] == v for k, v in native.items())
    assert [dict(d.native_headers) for d in deliveries] == originals


def test_welcome_unrelated_and_management_excluded(service, smtp, monkeypatch):
    assert service.send_welcome_email("reader@synthetic.invalid")
    assert service._send_email("reader@synthetic.invalid", "Operational", "Body")
    assert all(m.get_all("Feedback-ID") is None for m in smtp)
    captured = []
    monkeypatch.setattr(module.httpx, "post", lambda *a, **k: (captured.append(k["json"]) or response()))
    helper = NewsletterManagementEmailHelper(
        transport=SimpleNamespace(send_transactional=service.send_newsletter_management_transactional),
        site_origin="https://cheshiretoday.co.uk")
    now = datetime.now(timezone.utc)
    for purpose in NewsletterManagementEmailPurpose:
        msg = helper.build_message(NewsletterManagementEmailRequest(
            recipient_email="reader@synthetic.invalid", purpose=purpose,
            token="synthetic", expires_at=now + timedelta(minutes=30)), now=now)
        assert service.send_newsletter_management_transactional(msg)
    assert all("headers" not in m for m in captured)


@pytest.mark.parametrize("transport", ["resend", "smtp"])
def test_feedback_cannot_enter_unsubscribe_mapping(service, smtp, transport):
    from app.newsletter_delivery import NewsletterDeliveryError
    native = {**headers(), "Feedback-ID": "daily:::cheshtoday"}
    with pytest.raises(NewsletterDeliveryError, match="^invalid_newsletter_headers$"):
        if transport == "resend":
            service._send_resend_batch([{**message(), "headers": native}])
        else:
            service._send_email("reader@synthetic.invalid", "News", "Body", newsletter_headers=native)
    assert not smtp


@pytest.mark.parametrize("method,kwargs", [
    ("send_daily_brief", {"articles": [ARTICLE]}),
    ("send_weekly_roundup", {"big_read": ARTICLE, "icymi_articles": []}),
])
@pytest.mark.parametrize("resend", [True, False])
def test_digest_preview_excluded(service, smtp, monkeypatch, method, kwargs, resend):
    captured = []
    monkeypatch.setattr(module.httpx, "post", lambda *a, **k: (captured.extend(k["json"]) or response()))
    service.resend_enabled = resend
    getattr(service, method)(to_emails=["preview@synthetic.invalid"], preview=True, **kwargs)
    if resend:
        assert len(captured) == 1
        assert "headers" not in captured[0]
    else:
        assert len(smtp) == 1
        assert smtp[0].get_all("Feedback-ID") is None


@pytest.mark.parametrize("invalid", ["", "unknown:::cheshtoday", "daily:::cheshtoday\r\nBcc: bad", 1, {}])
@pytest.mark.parametrize("transport", ["resend", "smtp"])
def test_invalid_feedback_rejected_before_contact(service, smtp, invalid, transport):
    from app.newsletter_delivery import NewsletterDeliveryError
    service.last_provider_contacted = False
    with pytest.raises(NewsletterDeliveryError, match="^invalid_feedback_id$"):
        if transport == "resend":
            messages = [{**message(), "feedback_id": "daily:::cheshtoday"} for _ in range(100)]
            messages.append({**message(), "feedback_id": invalid})
            service._send_resend_batch(messages)
        else:
            service._send_email("reader@synthetic.invalid", "News", "Body",
                                newsletter_headers=headers(), feedback_id=invalid)
    assert not service.last_provider_contacted
    assert not smtp


def test_feedback_change_scope():
    import ast
    import subprocess
    from pathlib import Path
    baseline = lambda path: subprocess.check_output(["git", "show", "5afd7b1:" + path], text=True)
    assert Path("backend/server.py").read_text() == baseline("backend/server.py")
    assert Path("backend/app/newsletter_delivery.py").read_text() == baseline("backend/app/newsletter_delivery.py")
    allowed = {"_feedback_headers", "_send_email", "_send_resend_batch"} | {item[0] for item in FAMILIES}
    def functions(source):
        return {n.name: ast.dump(n, include_attributes=False) for n in ast.walk(ast.parse(source))
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name not in allowed
                and n.name != "build_recipient_message"}
    path = "backend/app/email_service.py"
    assert functions(Path(path).read_text()) == functions(baseline(path))
