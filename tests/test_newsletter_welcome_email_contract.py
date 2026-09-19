import logging
import smtplib

import pytest

from backend.app.email_service import EmailService


def test_welcome_email_confirms_immediate_all_three_subscription(monkeypatch):
    service = EmailService()
    captured = {}

    def capture(to_email, subject, html_content, text_content=None):
        captured.update(
            to_email=to_email,
            subject=subject,
            html=html_content,
            text=text_content,
        )
        return True

    monkeypatch.setattr(service, "_send_email", capture)

    assert service.send_welcome_email("reader@example.com") is True
    combined = f"{captured['html']}\n{captured['text']}"
    assert "The Daily Brief" in combined
    assert "Monday to Saturday" in combined
    assert "The Weekly Roundup" in combined
    assert "on Sunday" in combined
    assert "Breaking News Alerts" in combined
    assert "Rare alerts for major incidents" in combined
    assert "active now" in combined
    assert "No confirmation click is required" in combined
    assert "tomorrow" not in combined.lower()
    assert "/newsletter/preferences" in captured["html"]
    assert "/unsubscribe" in captured["html"]


@pytest.mark.parametrize(
    ("error", "stage", "category"),
    [
        (
            smtplib.SMTPAuthenticationError(
                535, b"authentication failed for reader@example.com"
            ),
            "login",
            "smtp_authentication_failed",
        ),
        (
            smtplib.SMTPConnectError(
                421, b"connection failed for reader@example.com"
            ),
            "login",
            "smtp_connection_failed",
        ),
        (
            smtplib.SMTPRecipientsRefused(
                {"reader@example.com": (550, b"recipient refused")}
            ),
            "sendmail",
            "recipient_refused",
        ),
        (
            smtplib.SMTPException("SMTP failure for reader@example.com"),
            "sendmail",
            "smtp_error",
        ),
        (
            RuntimeError("unexpected failure for reader@example.com"),
            "sendmail",
            "unexpected_send_error",
        ),
    ],
)
def test_smtp_failures_log_category_without_recipient_or_exception_text(
    monkeypatch, caplog, error, stage, category
):
    recipient = "reader@example.com"
    smtp_user = "smtp-owner@example.com"
    service = EmailService()
    service.smtp_enabled = True
    service.smtp_host = "smtp.example.com"
    service.smtp_port = 587
    service.smtp_user = smtp_user
    service.smtp_password = "synthetic-password"
    service.from_email = "news@example.com"

    class FailingSMTP:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def ehlo(self):
            return None

        def starttls(self, context=None):
            return None

        def login(self, *_args):
            if stage == "login":
                raise error

        def sendmail(self, *_args):
            if stage == "sendmail":
                raise error

    monkeypatch.setattr(smtplib, "SMTP", FailingSMTP)
    caplog.set_level(logging.ERROR)

    result = service._send_email(
        recipient,
        "Synthetic subject",
        "<p>Synthetic body</p>",
    )

    assert result is False
    assert category in caplog.text
    assert type(error).__name__ in caplog.text
    assert recipient not in caplog.text
    assert smtp_user not in caplog.text
    assert str(error) not in caplog.text
