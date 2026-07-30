import asyncio
import os
from pathlib import Path

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.app.newsletter_click_tracking import (
    UnsafeNewsletterClickDestination,
    validate_newsletter_click_destination,
)


os.environ["MONGO_URL"] = "mongodb://localhost:27017"
os.environ["DB_NAME"] = "cheshire_test"
os.environ["LOCAL_DEV_NO_DB"] = "1"
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")


VALID_DESTINATIONS = (
    "https://cheshiretoday.co.uk/article/example",
    "https://www.cheshiretoday.co.uk/article/example",
    "https://cheshiretoday.co.uk/article/example?utm_source=newsletter&utm_medium=email",
    "https://cheshiretoday.co.uk/article/example#story",
    "https://CHESHIRETODAY.CO.UK/article/example",
    "http://cheshiretoday.co.uk:80/article/example",
    "https://cheshiretoday.co.uk:443/article/example",
)

INVALID_DESTINATIONS = (
    None,
    "",
    "   ",
    "https://example.com/article/example",
    "http://example.com/article/example",
    "https://cheshiretoday.co.uk.example.com/article/example",
    "https://www.cheshiretoday.co.uk.example.com/article/example",
    "https://evilcheshiretoday.co.uk/article/example",
    "https://localhost/article/example",
    "https://127.0.0.1/article/example",
    "https://[::1]/article/example",
    "https://10.0.0.1/article/example",
    "https://[fc00::1]/article/example",
    "https://[fe80::1]/article/example",
    "https://8.8.8.8/article/example",
    "javascript:alert(1)",
    "data:text/html,hello",
    "file:///etc/passwd",
    "ftp://cheshiretoday.co.uk/article/example",
    "//cheshiretoday.co.uk/article/example",
    "cheshiretoday.co.uk/article/example",
    "https://cheshiretoday.co.uk:invalid/article/example",
    "https://cheshiretoday.co.uk:8080/article/example",
    "https://user:password@cheshiretoday.co.uk/article/example",
    "https://cheshiretoday.co.uk\\@example.com/article/example",
)


@pytest.mark.parametrize("destination", VALID_DESTINATIONS)
def test_approved_newsletter_destinations_are_preserved(destination):
    assert validate_newsletter_click_destination(destination) == destination


@pytest.mark.parametrize("destination", INVALID_DESTINATIONS)
def test_unsafe_newsletter_destinations_are_rejected(destination):
    with pytest.raises(UnsafeNewsletterClickDestination):
        validate_newsletter_click_destination(destination)


def test_generated_newsletter_urls_use_the_approved_public_host():
    from backend import server

    generated = server.email_service._get_tracked_url(
        "daily_brief_test",
        "https://cheshiretoday.co.uk/article/example?utm_source=newsletter",
    )

    assert generated.startswith("https://cheshiretoday.co.uk/api/email/track/click/")
    assert validate_newsletter_click_destination(
        "https://cheshiretoday.co.uk/article/example?utm_source=newsletter"
    )


class AnalyticsWriteSpy:
    def __init__(self):
        self.calls = []

    async def update_one(self, *args, **kwargs):
        self.calls.append((args, kwargs))


class DatabaseSpy:
    def __init__(self):
        self.email_analytics = AnalyticsWriteSpy()


def make_request():
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/email/track/click/test",
            "headers": [],
            "client": ("203.0.113.10", 1234),
        }
    )


def test_invalid_destination_is_rejected_before_analytics_write(monkeypatch):
    from backend import server

    database = DatabaseSpy()
    monkeypatch.setattr(server, "db", database)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            server.track_email_click(
                "daily_brief_test",
                "https://example.com/phishing",
                make_request(),
            )
        )

    assert exc_info.value.status_code == 400
    assert database.email_analytics.calls == []


def test_valid_destination_writes_existing_contract_and_redirects(monkeypatch):
    from backend import server

    database = DatabaseSpy()
    monkeypatch.setattr(server, "db", database)
    destination = "https://cheshiretoday.co.uk/article/example?utm_source=newsletter#story"

    response = asyncio.run(
        server.track_email_click(
            "daily_brief_test",
            destination,
            make_request(),
        )
    )

    assert response.status_code == 302
    assert response.headers["location"] == destination
    assert len(database.email_analytics.calls) == 1
    args, kwargs = database.email_analytics.calls[0]
    assert args[0] == {"tracking_id": "daily_brief_test"}
    assert args[1]["$inc"] == {"clicks": 1}
    assert args[1]["$push"]["click_events"]["url"] == destination
    assert kwargs == {"upsert": True}


def test_route_validates_before_analytics_update():
    source = Path("backend/server.py").read_text(encoding="utf-8")
    route_source = source.split("async def track_email_click(", 1)[1].split(
        '@api_router.get("/admin/email-analytics")', 1
    )[0]

    assert route_source.index("validate_newsletter_click_destination") < route_source.index(
        "db.email_analytics.update_one"
    )
