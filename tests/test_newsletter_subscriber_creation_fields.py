import asyncio
import inspect
import json
import os
import uuid
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


GENERIC_ID = uuid.UUID("123e4567-e89b-42d3-a456-426614174000")
MANAGEMENT_ID = uuid.UUID("123e4567-e89b-42d3-a456-426614174001")
TEST_EMAIL = "reader@trusted-news.co.uk"


def _post_routes(path):
    return [
        route
        for route in server.app.routes
        if getattr(route, "path", None) == path
        and "POST" in getattr(route, "methods", set())
    ]


class StubSubscribers:
    def __init__(self, existing=None):
        self.existing = deepcopy(existing)
        self.inserted = []
        self.updates = []

    async def find_one(self, query, projection):
        assert query == {"email": TEST_EMAIL}
        assert projection == {"_id": 0}
        return deepcopy(self.existing)

    async def insert_one(self, document):
        self.inserted.append(deepcopy(document))
        return SimpleNamespace(inserted_id="offline-only")

    async def update_one(self, query, update):
        self.updates.append((deepcopy(query), deepcopy(update)))
        return SimpleNamespace(modified_count=1)


class StubEmailService:
    def __init__(self):
        self.welcome_addresses = []

    def send_welcome_email(self, email):
        self.welcome_addresses.append(email)


def _run_subscribe(monkeypatch, existing=None, preferences=None):
    subscribers = StubSubscribers(existing)
    email_service = StubEmailService()
    database = SimpleNamespace(subscribers=subscribers)
    monkeypatch.setattr(server, "db", database)
    monkeypatch.setattr(server, "email_service", email_service)

    response = asyncio.run(
        server.subscribe_newsletter(
            server.SubscribeRequest(
                email="Reader@trusted-news.co.uk",
                preferences=preferences,
            )
        )
    )
    return response, subscribers, email_service


def _assert_private_subscribe_response(response):
    payload = response.model_dump()
    rendered = json.dumps(payload)
    assert set(payload) == {"success", "message"}
    assert "newsletter_management_id" not in rendered
    assert "newsletter_token_version" not in rendered
    assert str(GENERIC_ID) not in rendered
    assert str(MANAGEMENT_ID) not in rendered
    assert "_id" not in rendered


def test_public_subscribe_aliases_share_one_endpoint():
    direct_routes = _post_routes("/api/subscribe")
    newsletter_routes = _post_routes("/api/newsletter/subscribe")

    assert len(direct_routes) == 1
    assert len(newsletter_routes) == 1
    assert direct_routes[0].endpoint is server.subscribe_newsletter
    assert newsletter_routes[0].endpoint is server.subscribe_newsletter


def test_brand_new_subscriber_initializes_distinct_management_fields(monkeypatch):
    uuid_factory = Mock(side_effect=[GENERIC_ID, MANAGEMENT_ID])
    monkeypatch.setattr(server.uuid, "uuid4", uuid_factory)

    response, subscribers, email_service = _run_subscribe(monkeypatch)

    assert len(subscribers.inserted) == 1
    inserted = subscribers.inserted[0]
    assert uuid_factory.call_count == 2
    assert inserted["id"] == str(GENERIC_ID)
    assert inserted["newsletter_management_id"] == str(MANAGEMENT_ID)
    assert inserted["id"] != inserted["newsletter_management_id"]
    assert isinstance(inserted["newsletter_management_id"], str)
    parsed = uuid.UUID(inserted["newsletter_management_id"])
    assert parsed.version == 4
    assert str(parsed) == inserted["newsletter_management_id"]
    assert inserted["newsletter_management_id"].islower()
    assert inserted["newsletter_token_version"] == 1
    assert type(inserted["newsletter_token_version"]) is int
    assert inserted["email"] == TEST_EMAIL
    assert inserted["active"] is True
    assert inserted["daily_brief"] is True
    assert inserted["weekly_roundup"] is False
    assert inserted["breaking_news"] is False
    assert inserted["signup_source"] == "website"
    assert inserted["subscriber_origin"] == "organic_website"
    assert inserted["preferences"] == {
        "categories": ["Local News", "Business", "Finance", "AI & Tech"],
        "frequency": "daily",
    }
    assert set(inserted) == {
        "id",
        "newsletter_management_id",
        "newsletter_token_version",
        "email",
        "subscribed_at",
        "created_at",
        "site_update_part1_sent_at",
        "site_update_part2_sent_at",
        "active",
        "preferences",
        "signup_source",
        "subscriber_origin",
        "daily_brief",
        "weekly_roundup",
        "breaking_news",
    }
    assert email_service.welcome_addresses == [TEST_EMAIL]
    assert response.success is True
    _assert_private_subscribe_response(response)


def test_new_subscriber_preferences_and_existing_fields_are_preserved(monkeypatch):
    preferences = {"categories": ["Business"], "frequency": "weekly"}
    monkeypatch.setattr(
        server.uuid,
        "uuid4",
        Mock(side_effect=[GENERIC_ID, MANAGEMENT_ID]),
    )

    _response, subscribers, _email_service = _run_subscribe(
        monkeypatch, preferences=preferences
    )

    inserted = subscribers.inserted[0]
    assert inserted["preferences"] == preferences
    assert inserted["site_update_part1_sent_at"] is None
    assert inserted["site_update_part2_sent_at"] is None
    assert "subscribed_at" in inserted
    assert "created_at" in inserted


@pytest.mark.parametrize(
    "existing",
    [
        {"email": TEST_EMAIL, "active": True},
        {
            "email": TEST_EMAIL,
            "active": True,
            "newsletter_management_id": str(MANAGEMENT_ID),
            "newsletter_token_version": 7,
        },
        {"email": TEST_EMAIL, "active": False},
        {
            "email": TEST_EMAIL,
            "active": False,
            "newsletter_management_id": str(MANAGEMENT_ID),
            "newsletter_token_version": 7,
        },
    ],
)
def test_existing_subscriber_branches_never_assign_management_fields(
    monkeypatch, existing
):
    uuid_factory = Mock()
    monkeypatch.setattr(server.uuid, "uuid4", uuid_factory)

    response, subscribers, email_service = _run_subscribe(monkeypatch, existing)

    assert subscribers.inserted == []
    assert uuid_factory.call_count == 0
    assert email_service.welcome_addresses == []
    for _query, update in subscribers.updates:
        rendered = json.dumps(update)
        assert "newsletter_management_id" not in rendered
        assert "newsletter_token_version" not in rendered
    _assert_private_subscribe_response(response)


def test_existing_active_preference_update_does_not_touch_management_fields(
    monkeypatch,
):
    existing = {
        "email": TEST_EMAIL,
        "active": True,
        "newsletter_management_id": str(MANAGEMENT_ID),
        "newsletter_token_version": 4,
    }
    preferences = {"categories": ["Local News"], "frequency": "daily"}

    _response, subscribers, _email_service = _run_subscribe(
        monkeypatch, existing, preferences
    )

    assert subscribers.updates == [
        (
            {"email": TEST_EMAIL},
            {"$set": {"preferences": preferences}},
        )
    ]


def test_subscribe_responses_expose_no_subscriber_identifiers(monkeypatch):
    monkeypatch.setattr(
        server.uuid,
        "uuid4",
        Mock(side_effect=[GENERIC_ID, MANAGEMENT_ID]),
    )
    response, _subscribers, _email_service = _run_subscribe(monkeypatch)

    _assert_private_subscribe_response(response)


def test_subscribe_handler_does_not_activate_token_system():
    source = inspect.getsource(server.subscribe_newsletter)

    assert "newsletter_token_service" not in source
    assert "NEWSLETTER_LINK_SECRET" not in source
    assert "issue_newsletter_token" not in source
    assert "verify_newsletter_token" not in source
    assert "jwt" not in source.lower()
    assert "management_url" not in source
