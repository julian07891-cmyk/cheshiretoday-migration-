import asyncio
import os
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server
from backend.app.commercial_event_measurement import (
    COMMERCIAL_EVENT_INDEXES,
    COMMERCIAL_EVENT_RETENTION_DAYS,
    COMMERCIAL_REPORT_LIST_LIMIT,
    ZERO_CLICK_MIN_RENDERED,
    CommercialEventPayload,
    build_commercial_analytics,
    commercial_aggregate_pipeline,
    commercial_event_dedupe_key,
    commercial_event_document,
    commercial_reporting_period,
    ensure_commercial_event_indexes,
)


NOW = datetime(2026, 8, 21, 12, 30, tzinfo=timezone.utc)
BASE_PAYLOAD = {
    "event_type": "rendered",
    "card_id": "energy-bills-v1",
    "provider_id": "awin",
    "placement_id": "article_inline",
    "article_id": "article-123",
    "article_category": "business",
    "use_case": "energy_bills",
    "destination_type": "provider",
    "destination_id": "merchant-456",
    "device_class": "mobile",
    "rule_reason_code": "category_match",
    "variant_version": "v1",
    "disclosure_version": "affiliate_v1",
    "session_key": "SessionKey_1234567890",
    "page_view_id": "page_view_1234567890",
}
CLIENT_HEADERS = {"Accept-Encoding": "identity"}


def payload(**changes):
    return {**BASE_PAYLOAD, **changes}


@pytest.mark.parametrize("event_type", ["rendered", "viewable", "clicked"])
def test_exact_event_types_are_accepted(event_type):
    assert CommercialEventPayload(**payload(event_type=event_type)).event_type == event_type


def test_unknown_event_type_and_unknown_fields_are_rejected():
    with pytest.raises(ValidationError):
        CommercialEventPayload(**payload(event_type="hovered"))
    with pytest.raises(ValidationError):
        CommercialEventPayload(**payload(email="reader@example.com"))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("card_id", "unsafe/card"),
        ("provider_id", "p" * 49),
        ("placement_id", "p" * 49),
        ("destination_id", "d" * 97),
        ("page_view_id", "short"),
        ("session_key", "contains spaces and punctuation!"),
    ],
)
def test_identifier_patterns_and_bounds_are_enforced(field, value):
    with pytest.raises(ValidationError):
        CommercialEventPayload(**payload(**{field: value}))


def test_identifiers_are_normalised_and_article_context_is_required():
    event = CommercialEventPayload(
        **payload(card_id=" ENERGY-BILLS-V1 ", article_category=" Local_News ")
    )
    assert event.card_id == "energy-bills-v1"
    assert event.article_category == "local_news"

    with pytest.raises(ValidationError):
        CommercialEventPayload(**payload(article_id=None))
    non_article = CommercialEventPayload(
        **payload(placement_id="homepage_strip", article_id=None)
    )
    assert non_article.article_id is None


def test_server_fields_are_utc_bounded_and_raw_session_is_not_stored():
    event = CommercialEventPayload(**BASE_PAYLOAD)
    document = commercial_event_document(event, now=NOW)

    assert document["occurred_at"] == NOW
    assert document["expires_at"] == NOW + timedelta(days=COMMERCIAL_EVENT_RETENTION_DAYS)
    assert len(document["session_hash"]) == 64
    assert len(document["dedupe_key"]) == 64
    assert "session_key" not in document
    prohibited = {
        "email",
        "ip",
        "user_agent",
        "article_title",
        "article_body",
        "destination_url",
        "cookie_id",
    }
    assert prohibited.isdisjoint(document)


def test_dedupe_is_deterministic_and_changes_with_event_identity():
    first = CommercialEventPayload(**BASE_PAYLOAD)
    same = CommercialEventPayload(**BASE_PAYLOAD)
    clicked = CommercialEventPayload(**payload(event_type="clicked"))
    assert commercial_event_dedupe_key(first) == commercial_event_dedupe_key(same)
    assert commercial_event_dedupe_key(first) != commercial_event_dedupe_key(clicked)


def test_reporting_period_defaults_to_30_complete_london_days():
    period = commercial_reporting_period(None, None, now=NOW)
    assert period.from_date == date(2026, 7, 22)
    assert period.to_date == date(2026, 8, 20)
    assert period.start_utc == datetime(2026, 7, 21, 23, tzinfo=timezone.utc)
    assert period.end_utc == datetime(2026, 8, 20, 23, tzinfo=timezone.utc)


def test_reporting_period_accepts_90_days_and_rejects_invalid_ranges():
    assert commercial_reporting_period("2026-06-01", "2026-08-29").from_date == date(2026, 6, 1)
    for from_value, to_value in (
        ("2026-06-01", "2026-08-30"),
        ("2026-08-21", "2026-08-20"),
        ("2026-08-01", None),
        ("not-a-date", "2026-08-20"),
    ):
        with pytest.raises(ValueError):
            commercial_reporting_period(from_value, to_value)


class AggregateCursor:
    def __init__(self, result):
        self.result = result
        self.length = None

    async def to_list(self, length):
        self.length = length
        return [self.result]


class AggregateCollection:
    def __init__(self, result):
        self.pipeline = None
        self.cursor = AggregateCursor(result)

    def aggregate(self, pipeline):
        self.pipeline = pipeline
        return self.cursor

    def __getattr__(self, name):
        raise AssertionError(f"commercial report must remain aggregate-only: {name}")


def aggregate_result():
    dimensions = {
        "by_provider": [{"provider_id": "awin", "rendered": 100, "viewable": 80, "clicked": 4}],
        "by_placement": [{"placement_id": "article_inline", "rendered": 100, "viewable": 80, "clicked": 4}],
        "by_category": [{"article_category": "business", "rendered": 100, "viewable": 80, "clicked": 4}],
        "by_device": [{"device_class": "mobile", "rendered": 100, "viewable": 80, "clicked": 4}],
        "by_use_case": [{"use_case": "energy_bills", "rendered": 100, "viewable": 80, "clicked": 4}],
    }
    cards = [
        {
            "provider_id": "awin",
            "card_id": f"card-{index:02d}",
            "placement_id": "article_inline",
            "rendered": 100 - index,
            "viewable": 80 - index,
            "clicked": 0,
        }
        for index in range(25)
    ]
    return {
        "overall": [{"rendered": 100, "viewable": 80, "clicked": 4}],
        **dimensions,
        "top_cards": cards,
        "zero_click_high_impression": cards,
    }


def test_admin_aggregate_is_bounded_and_calculates_all_dimensions_and_ctrs():
    period = commercial_reporting_period("2026-08-01", "2026-08-20")
    collection = AggregateCollection(aggregate_result())
    result = asyncio.run(build_commercial_analytics(collection, period))

    assert result["period"] == {
        "from": "2026-08-01",
        "to": "2026-08-20",
        "timezone": "Europe/London",
    }
    assert result["overall"] == {
        "rendered": 100,
        "viewable": 80,
        "clicked": 4,
        "rendered_ctr": 4.0,
        "viewable_ctr": 5.0,
    }
    for name in ("by_provider", "by_placement", "by_category", "by_device", "by_use_case"):
        assert len(result[name]) == 1
        assert result[name][0]["rendered_ctr"] == 4.0
        assert result[name][0]["viewable_ctr"] == 5.0
    assert len(result["top_cards"]) == COMMERCIAL_REPORT_LIST_LIMIT
    assert len(result["zero_click_high_impression"]) == COMMERCIAL_REPORT_LIST_LIMIT
    assert collection.cursor.length == 1
    assert collection.pipeline == commercial_aggregate_pipeline(period)


def test_null_ctr_denominators_are_returned_as_null():
    empty = AggregateCollection({"overall": [{"rendered": 0, "viewable": 0, "clicked": 0}]})
    result = asyncio.run(
        build_commercial_analytics(
            empty,
            commercial_reporting_period("2026-08-01", "2026-08-20"),
        )
    )
    assert result["overall"]["rendered_ctr"] is None
    assert result["overall"]["viewable_ctr"] is None


def test_pipeline_has_deterministic_bounded_facets_and_operational_zero_click_filter():
    pipeline = commercial_aggregate_pipeline(
        commercial_reporting_period("2026-08-01", "2026-08-20")
    )
    facets = pipeline[1]["$facet"]
    assert facets["top_cards"][-2] == {"$limit": COMMERCIAL_REPORT_LIST_LIMIT}
    assert facets["zero_click_high_impression"][1] == {
        "$match": {"clicked": 0, "rendered": {"$gte": ZERO_CLICK_MIN_RENDERED}}
    }
    assert facets["zero_click_high_impression"][-2] == {
        "$limit": COMMERCIAL_REPORT_LIST_LIMIT
    }


class InsertCollection:
    def __init__(self, error=None):
        self.error = error
        self.documents = []

    async def insert_one(self, document):
        if self.error:
            raise self.error
        self.documents.append(document)
        return object()


class RouteDatabase:
    def __init__(self, collection):
        self.commercial_events = collection


@pytest.mark.parametrize("event_type", ["rendered", "viewable", "clicked"])
def test_public_route_accepts_each_event_and_persists_only_bounded_document(monkeypatch, event_type):
    collection = InsertCollection()
    monkeypatch.setattr(server, "db", RouteDatabase(collection))
    with TestClient(server.app, headers=CLIENT_HEADERS) as client:
        response = client.post("/api/commercial-events", json=payload(event_type=event_type))
    assert response.status_code == 202
    assert response.json() == {"accepted": True}
    assert len(collection.documents) == 1
    assert "session_key" not in collection.documents[0]


def test_public_route_duplicate_is_idempotent_success(monkeypatch):
    monkeypatch.setattr(
        server,
        "db",
        RouteDatabase(InsertCollection(DuplicateKeyError("duplicate"))),
    )
    with TestClient(server.app, headers=CLIENT_HEADERS) as client:
        response = client.post("/api/commercial-events", json=BASE_PAYLOAD)
    assert response.status_code == 202
    assert response.json() == {"accepted": True}


def test_public_route_rejects_malformed_oversized_and_database_failure(monkeypatch):
    collection = InsertCollection()
    monkeypatch.setattr(server, "db", RouteDatabase(collection))
    with TestClient(server.app, headers=CLIENT_HEADERS) as client:
        malformed = client.post("/api/commercial-events", json=payload(event_type="hovered"))
        oversized = client.post(
            "/api/commercial-events",
            content=b"{}",
            headers={"Content-Type": "application/json", "Content-Length": "2049"},
        )
    assert malformed.status_code == 422
    assert oversized.status_code == 413
    assert collection.documents == []

    monkeypatch.setattr(server, "db", RouteDatabase(InsertCollection(RuntimeError("private"))))
    with TestClient(server.app, headers=CLIENT_HEADERS) as client:
        failed = client.post("/api/commercial-events", json=BASE_PAYLOAD)
    assert failed.status_code == 503
    assert failed.json() == {"detail": "Commercial event recording unavailable"}


def test_admin_route_requires_existing_auth_before_database_access(monkeypatch):
    class UntouchedDatabase:
        def __getattr__(self, name):
            raise AssertionError("database must not be accessed before auth")

    monkeypatch.setattr(server, "db", UntouchedDatabase())
    with TestClient(server.app, headers=CLIENT_HEADERS) as client:
        response = client.get("/api/admin/analytics/commercial")
    assert response.status_code == 401


def test_admin_route_uses_bounded_aggregate_and_rejects_over_90_days(monkeypatch):
    collection = AggregateCollection(aggregate_result())
    server.app.dependency_overrides[server.get_admin_auth] = lambda: True
    monkeypatch.setattr(server, "db", RouteDatabase(collection))
    try:
        with TestClient(server.app, headers=CLIENT_HEADERS) as client:
            response = client.get(
                "/api/admin/analytics/commercial?from=2026-08-01&to=2026-08-20"
            )
            too_long = client.get(
                "/api/admin/analytics/commercial?from=2026-05-01&to=2026-08-20"
            )
    finally:
        server.app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["overall"]["rendered"] == 100
    assert too_long.status_code == 400


def test_exact_minimum_indexes_are_declared():
    assert COMMERCIAL_EVENT_INDEXES == (
        {
            "keys": [("dedupe_key", 1)],
            "options": {"unique": True, "name": "commercial_event_dedupe_unique"},
        },
        {
            "keys": [("expires_at", 1)],
            "options": {"expireAfterSeconds": 0, "name": "commercial_event_expiry_ttl"},
        },
        {
            "keys": [
                ("occurred_at", 1),
                ("event_type", 1),
                ("provider_id", 1),
                ("placement_id", 1),
            ],
            "options": {"name": "commercial_event_reporting"},
        },
    )


def test_exact_minimum_indexes_are_created_without_other_database_work():
    class IndexCollection:
        def __init__(self):
            self.calls = []

        async def create_index(self, keys, **options):
            self.calls.append((keys, options))

        def __getattr__(self, name):
            raise AssertionError(f"index provisioning must only create indexes: {name}")

    collection = IndexCollection()
    asyncio.run(ensure_commercial_event_indexes(collection))
    assert collection.calls == [
        (index["keys"], index["options"]) for index in COMMERCIAL_EVENT_INDEXES
    ]
