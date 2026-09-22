import asyncio
import logging
from copy import deepcopy
from types import SimpleNamespace

import pytest

from backend import server
from backend.app import email_service as email_service_module
from backend.app.email_service import EmailService


class AsyncListCursor:
    def __init__(self, values):
        self.values = deepcopy(values)

    async def to_list(self, _limit):
        return deepcopy(self.values)


class AsyncCursor:
    def __init__(self, values):
        self.values = deepcopy(values)
        self.index = 0

    def limit(self, _limit):
        return self

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.values):
            raise StopAsyncIteration
        value = deepcopy(self.values[self.index])
        self.index += 1
        return value


class DigestLog:
    def __init__(self):
        self.inserted = []
        self.updated = []

    async def find_one(self, query):
        if len(query) == 2:
            return None
        return {"_id": "claim", **deepcopy(query)}

    async def insert_one(self, document):
        self.inserted.append(deepcopy(document))
        return SimpleNamespace(inserted_id="claim")

    async def update_one(self, query, update):
        self.updated.append((deepcopy(query), deepcopy(update)))
        return SimpleNamespace(modified_count=1)


class Subscribers:
    def __init__(self, values):
        self.values = values

    def find(self, *_args, **_kwargs):
        return AsyncListCursor(self.values)


class Articles:
    def __init__(self, values):
        self.values = values

    def aggregate(self, _pipeline):
        return AsyncListCursor(self.values)

    async def find_one(self, *_args, **_kwargs):
        return deepcopy(self.values[0]) if self.values else None

    def find(self, *_args, **_kwargs):
        return AsyncCursor(self.values[1:])


class RecordingEmailService:
    def __init__(self, error=None):
        self.error = error
        self.daily_calls = []
        self.roundup_calls = []
        self.base_url = "https://cheshiretoday.co.uk"
        self.api_url = "https://cheshiretoday.co.uk/api"
        self.resend_enabled = False
        self.resend_last_error = None
        self.resend_last_successful_chunks = 0
        self.resend_last_failed_chunks = 0
        self.last_accepted_recipients = []

    def send_daily_brief(self, **kwargs):
        self.daily_calls.append(deepcopy(kwargs))
        if self.error:
            raise self.error
        recipients = ([item.context.email for item in kwargs["prepared_deliveries"]]
                      if "prepared_deliveries" in kwargs else kwargs["to_emails"])
        self.last_accepted_recipients = list(recipients)
        return len(recipients), "daily-tracking"

    def send_weekly_roundup(self, **kwargs):
        self.roundup_calls.append(deepcopy(kwargs))
        if self.error:
            raise self.error
        return len(kwargs["to_emails"]), "weekly-tracking"


ARTICLE = {
    "_id": "article-id",
    "title": "Cheshire business investment creates local jobs",
    "content": "Cheshire businesses are investing in jobs and economic growth.",
    "category": "Business",
    "publishedDate": "2026-09-19T07:00:00+00:00",
}


def test_scheduled_invalid_addresses_are_counted_without_identity_logging(
    monkeypatch, caplog
):
    invalid_addresses = ["invalid-one@example.com", "invalid-two@example.com"]
    valid_address = "valid-reader@trusted-news.co.uk"
    email_service = RecordingEmailService()
    monkeypatch.setattr(
        server,
        "db",
        SimpleNamespace(
            digest_log=DigestLog(),
            subscribers=Subscribers(
                [{"email": address} for address in invalid_addresses] + [{
                    "email": valid_address, "active": True,
                    "newsletter_management_id": "123e4567-e89b-42d3-a456-426614174000",
                    "newsletter_token_version": 1,
                }]
            ),
            articles=Articles([ARTICLE]),
        ),
    )
    monkeypatch.setattr(server, "email_service", email_service)
    from app.newsletter_token_service import NewsletterTokenService
    monkeypatch.setattr(server, "newsletter_token_service_from_environment",
                        lambda: NewsletterTokenService("D" * 43))
    monkeypatch.setenv("HOSTNAME", "privacy-test")

    async def select_batch(*_args, **_kwargs):
        return [valid_address], 0, 0, 1

    async def save_opportunities(*_args, **_kwargs):
        return 1

    async def save_cursor(*_args, **_kwargs):
        return None

    monkeypatch.setattr(server, "_select_rotating_email_batch", select_batch)
    monkeypatch.setattr(server, "_save_email_send_opportunities", save_opportunities)
    monkeypatch.setattr(server, "_save_email_batch_cursor", save_cursor)
    caplog.set_level(logging.INFO, logger=server.logger.name)

    asyncio.run(server.send_scheduled_news_digest())

    assert len(email_service.daily_calls) == 1
    recipients = [d.context.email for d in email_service.daily_calls[0]["prepared_deliveries"]]
    assert recipients == [valid_address]
    assert "Skipping 2 invalid newsletter subscriber addresses" in caplog.text
    assert all(address not in caplog.text for address in invalid_addresses)
    assert all(
        address not in recipients
        for address in invalid_addresses
    )


@pytest.mark.parametrize("use_preview_links", [False, True])
def test_daily_brief_admin_test_preserves_destination_and_preview_without_logging_it(
    monkeypatch, caplog, use_preview_links
):
    destination = "daily-admin@example.com"
    email_service = RecordingEmailService()
    monkeypatch.setattr(server, "db", SimpleNamespace(articles=Articles([ARTICLE])))
    monkeypatch.setattr(server, "email_service", email_service)
    monkeypatch.setenv("REACT_APP_BACKEND_URL", "https://preview.example.com/api")
    caplog.set_level(logging.INFO, logger=server.logger.name)

    response = asyncio.run(
        server.send_digest_test(destination, use_preview_links, auth=True)
    )

    assert email_service.daily_calls[0]["to_emails"] == [destination]
    assert response["success"] is True
    assert response["emails_sent"] == 1
    assert response["link_type"] == (
        "PREVIEW (for testing)" if use_preview_links else "PRODUCTION"
    )
    assert email_service.base_url == "https://cheshiretoday.co.uk"
    assert email_service.api_url == "https://cheshiretoday.co.uk/api"
    assert destination not in caplog.text


def test_weekly_roundup_admin_test_preserves_destination_without_logging_it(
    monkeypatch, caplog
):
    destination = "weekly-admin@example.com"
    email_service = RecordingEmailService()
    monkeypatch.setattr(server, "db", SimpleNamespace(articles=Articles([ARTICLE])))
    monkeypatch.setattr(server, "email_service", email_service)
    caplog.set_level(logging.INFO, logger=server.logger.name)

    response = asyncio.run(server.send_weekly_roundup_test(destination, auth=True))

    assert email_service.roundup_calls[0]["to_emails"] == [destination]
    assert response["success"] is True
    assert response["emails_sent"] == 1
    assert response["tracking_id"] == "weekly-tracking"
    assert destination not in caplog.text


@pytest.mark.parametrize(
    ("function_name", "expected_log"),
    [
        ("send_digest_test", "Test digest send failed: RuntimeError"),
        (
            "send_weekly_roundup_test",
            "Weekly Roundup test send failed: RuntimeError",
        ),
    ],
)
def test_admin_test_send_failure_omits_destination_and_exception_message(
    monkeypatch, caplog, function_name, expected_log
):
    destination = "failed-admin@example.com"
    private_message = f"provider failure for {destination}"
    email_service = RecordingEmailService(RuntimeError(private_message))
    monkeypatch.setattr(server, "db", SimpleNamespace(articles=Articles([ARTICLE])))
    monkeypatch.setattr(server, "email_service", email_service)
    caplog.set_level(logging.INFO, logger=server.logger.name)

    with pytest.raises(server.HTTPException) as raised:
        asyncio.run(getattr(server, function_name)(destination, auth=True))

    assert raised.value.status_code == 500
    assert raised.value.detail == private_message
    assert expected_log in caplog.text
    assert destination not in caplog.text
    assert private_message not in caplog.text


def test_resend_failure_log_and_diagnostic_omit_provider_body_and_recipient(
    monkeypatch, caplog
):
    recipient = "reader@example.com"
    provider_body = f'provider rejected recipient "{recipient}"'
    service = EmailService()
    service.resend_enabled = True
    service.resend_api_key = "synthetic-key"
    service.resend_from_email = "news@example.com"
    service.last_accepted_recipients = []
    service.resend_last_successful_chunks = 0
    service.resend_last_failed_chunks = 0
    service.resend_last_error = None

    class RejectedResponse:
        status_code = 400
        text = provider_body

        def raise_for_status(self):
            raise RuntimeError(f"request failed for {recipient}")

    monkeypatch.setattr(
        email_service_module.httpx,
        "post",
        lambda *_args, **_kwargs: RejectedResponse(),
    )
    caplog.set_level(logging.ERROR)

    result = service._send_resend_batch(
        [
            {
                "to": recipient,
                "subject": "Synthetic newsletter",
                "html": "<p>Synthetic body</p>",
            }
        ]
    )

    assert result == 0
    assert "chunk=1" in caplog.text
    assert "size=1" in caplog.text
    assert "status=400" in caplog.text
    assert "error_type=RuntimeError" in caplog.text
    assert recipient not in caplog.text
    assert provider_body not in caplog.text
    assert recipient not in service.resend_last_error
    assert provider_body not in service.resend_last_error
