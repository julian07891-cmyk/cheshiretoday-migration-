import asyncio
import os
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server
from backend.app.admin_analytics import (
    APPROVED_ADVERTISER_STATUSES,
    TOP_ARTICLE_LIMIT,
    analytics_period_start,
    build_admin_analytics_summary,
)


NOW = datetime(2026, 8, 1, 14, 30, tzinfo=timezone.utc)


class AggregateCursor:
    def __init__(self, result):
        self.result = result
        self.length = None

    async def to_list(self, length):
        self.length = length
        return [self.result] if self.result is not None else []


class AggregateCollection:
    def __init__(self, results):
        self.results = list(results)
        self.pipelines = []
        self.cursors = []

    def aggregate(self, pipeline):
        self.pipelines.append(pipeline)
        cursor = AggregateCursor(self.results.pop(0) if self.results else {})
        self.cursors.append(cursor)
        return cursor

    def __getattr__(self, name):
        raise AssertionError(f"Analytics collection must remain read-only: {name}")


class FailingCollection:
    def aggregate(self, pipeline):
        raise RuntimeError("private database failure")


class AnalyticsDatabase:
    def __init__(self):
        self.article_views = AggregateCollection(
            [
                {
                    "totals": [{"total": 12, "unique_articles": 2}],
                    "top_articles": [
                        {
                            "id": "64b7f9d4aabbccddeeff0011",
                            "title": "Public article",
                            "category": "Local News",
                            "views": 8,
                        },
                        {
                            "id": "64b7f9d4aabbccddeeff0012",
                            "title": "Business article",
                            "category": "Business",
                            "views": 4,
                        },
                    ],
                    "categories": [
                        {"category": "Local News", "views": 8},
                        {"category": "Business", "views": 4},
                    ],
                }
            ]
        )
        self.email_send_opportunities = AggregateCollection(
            [{"accepted_opportunities": 300, "send_batches": 2}]
        )
        self.email_analytics = AggregateCollection([{"opens": 40, "clicks": 7}])
        self.sponsored_placements = AggregateCollection(
            [{"impressions": 100, "clicks": 5}]
        )
        self.advertiser_leads = AggregateCollection(
            [{"total": 3, "by_status": [{"status": "new", "count": 3}]}]
        )


@pytest.mark.parametrize(
    ("period", "expected"),
    [
        ("today", NOW.replace(hour=0, minute=0, second=0, microsecond=0)),
        ("week", NOW - timedelta(days=7)),
        ("month", NOW - timedelta(days=30)),
    ],
)
def test_analytics_periods_are_deterministic(period, expected):
    assert analytics_period_start(period, NOW) == expected


def test_invalid_period_is_rejected_without_database_access(monkeypatch):
    class UntouchedDatabase:
        def __getattr__(self, name):
            raise AssertionError("invalid period must not access the database")

    server.app.dependency_overrides[server.get_admin_auth] = lambda: True
    monkeypatch.setattr(server, "db", UntouchedDatabase())
    try:
        response = TestClient(server.app).get(
            "/api/admin/analytics/summary?period=year"
        )
    finally:
        server.app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid analytics period"}


def test_authentication_precedes_all_database_work(monkeypatch):
    class UntouchedDatabase:
        def __getattr__(self, name):
            raise AssertionError("database must not be accessed before authentication")

    monkeypatch.setattr(server, "db", UntouchedDatabase())
    response = TestClient(server.app).get("/api/admin/analytics/summary?period=week")

    assert response.status_code == 401


def test_authenticated_route_returns_the_summary_contract(monkeypatch):
    calls = []

    async def fake_summary(database, period):
        calls.append((database, period))
        return {"success": True, "period": period, "article_views": {"available": True}}

    database = object()
    server.app.dependency_overrides[server.get_admin_auth] = lambda: True
    monkeypatch.setattr(server, "db", database)
    monkeypatch.setattr(server, "build_admin_analytics_summary", fake_summary)
    try:
        response = TestClient(server.app).get(
            "/api/admin/analytics/summary?period=month"
        )
    finally:
        server.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "period": "month",
        "article_views": {"available": True},
    }
    assert calls == [(database, "month")]


def test_summary_uses_bounded_private_aggregates_and_returns_no_pii():
    database = AnalyticsDatabase()
    result = asyncio.run(
        build_admin_analytics_summary(database, "week", now=NOW)
    )

    assert result["article_views"] == {
        "available": True,
        "total": 12,
        "unique_articles": 2,
        "top_articles": [
            {
                "id": "64b7f9d4aabbccddeeff0011",
                "title": "Public article",
                "category": "Local News",
                "views": 8,
            },
            {
                "id": "64b7f9d4aabbccddeeff0012",
                "title": "Business article",
                "category": "Business",
                "views": 4,
            },
        ],
        "categories": [
            {"category": "Local News", "views": 8, "share_percent": 66.7},
            {"category": "Business", "views": 4, "share_percent": 33.3},
        ],
    }
    assert result["newsletter"] == {
        "available": True,
        "accepted_opportunities": 300,
        "send_batches": 2,
        "opens": 40,
        "clicks": 7,
    }
    assert result["sponsored"] == {
        "available": True,
        "scope": "lifetime",
        "impressions": 100,
        "clicks": 5,
        "ctr_percent": 5.0,
    }
    assert result["advertisers"] == {
        "available": True,
        "total": 3,
        "by_status": [{"status": "new", "count": 3}],
    }

    rendered = repr(result).lower()
    for forbidden in (
        "recipient_hash",
        "email",
        "user_agent",
        "ip_hash",
        "article content",
        "summary",
        "personal details",
    ):
        assert forbidden not in rendered

    collections = (
        database.article_views,
        database.email_send_opportunities,
        database.email_analytics,
        database.sponsored_placements,
        database.advertiser_leads,
    )
    assert all(cursor.length == 1 for collection in collections for cursor in collection.cursors)


def test_article_pipeline_filters_public_records_before_bounded_top_results():
    database = AnalyticsDatabase()
    asyncio.run(build_admin_analytics_summary(database, "today", now=NOW))

    pipeline = database.article_views.pipelines[0]
    lookup = next(stage["$lookup"] for stage in pipeline if "$lookup" in stage)
    assert lookup["let"]["view_object_id"] == {
        "$convert": {
            "input": "$_id",
            "to": "objectId",
            "onError": None,
            "onNull": None,
        }
    }
    identity_match = lookup["pipeline"][0]["$match"]["$expr"]["$or"]
    assert {"$eq": ["$_id", "$$view_object_id"]} in identity_match
    assert {"$eq": ["$id", "$$view_article_id"]} in identity_match
    visibility = next(
        stage["$match"]
        for stage in lookup["pipeline"]
        if stage.get("$match", {}).get("archived")
    )
    assert visibility == {
        "archived": {"$ne": True},
        "manual_review_hidden_from_public": {"$ne": True},
    }
    assert lookup["pipeline"][-1] == {"$limit": 1}

    facet = next(stage["$facet"] for stage in pipeline if "$facet" in stage)
    assert {"$limit": TOP_ARTICLE_LIMIT} in facet["top_articles"]
    assert pipeline.index({"$unwind": "$article"}) < next(
        index for index, stage in enumerate(pipeline) if "$facet" in stage
    )
    projection = next(
        stage["$project"] for stage in facet["top_articles"] if "$project" in stage
    )
    assert "content" not in projection
    assert "summary" not in projection
    assert "image" not in projection


def test_empty_period_returns_real_empty_results():
    database = AnalyticsDatabase()
    database.article_views = AggregateCollection([{}])

    result = asyncio.run(
        build_admin_analytics_summary(database, "month", now=NOW)
    )

    assert result["article_views"] == {
        "available": True,
        "total": 0,
        "unique_articles": 0,
        "top_articles": [],
        "categories": [],
    }


def test_one_failed_section_is_safely_unavailable_without_leaking_exception():
    database = AnalyticsDatabase()
    database.email_analytics = FailingCollection()

    result = asyncio.run(
        build_admin_analytics_summary(database, "week", now=NOW)
    )

    assert result["article_views"]["available"] is True
    assert result["newsletter"] == {"available": False}
    assert "private database failure" not in repr(result)


def test_zero_sponsored_impressions_has_no_false_ctr():
    database = AnalyticsDatabase()
    database.sponsored_placements = AggregateCollection(
        [{"impressions": 0, "clicks": 0}]
    )

    result = asyncio.run(
        build_admin_analytics_summary(database, "week", now=NOW)
    )

    assert result["sponsored"]["ctr_percent"] is None


def test_advertiser_statuses_are_normalised_before_bounded_grouping():
    database = AnalyticsDatabase()
    pipeline_result = [
        {"status": status, "count": 1}
        for status in APPROVED_ADVERTISER_STATUSES
    ] + [{"status": "other", "count": 5}]
    database.advertiser_leads = AggregateCollection(
        [
            {
                "total": len(APPROVED_ADVERTISER_STATUSES) + 5,
                "by_status": pipeline_result,
            }
        ]
    )

    result = asyncio.run(
        build_admin_analytics_summary(database, "week", now=NOW)
    )

    assert result["advertisers"]["total"] == len(APPROVED_ADVERTISER_STATUSES) + 5
    assert result["advertisers"]["by_status"] == pipeline_result
    assert {row["status"] for row in result["advertisers"]["by_status"]} == {
        *APPROVED_ADVERTISER_STATUSES,
        "other",
    }

    pipeline = database.advertiser_leads.pipelines[0]
    normalisation_index = next(
        index
        for index, stage in enumerate(pipeline)
        if stage.get("$project", {}).get("normalised_status")
    )
    grouping_index = next(
        index
        for index, stage in enumerate(pipeline)
        if stage.get("$group", {}).get("_id") == "$normalised_status"
    )
    assert normalisation_index < grouping_index
    assert pipeline[normalisation_index] == {
        "$project": {
            "_id": 0,
            "normalised_status": {
                "$cond": [
                    {"$in": ["$status", list(APPROVED_ADVERTISER_STATUSES)]},
                    "$status",
                    "other",
                ]
            },
        }
    }
    assert not any("$limit" in stage for stage in pipeline)

    raw_examples = ("legacy", None, "", {"unexpected": "value"}, 42)
    approved = set(APPROVED_ADVERTISER_STATUSES)
    assert [
        value if isinstance(value, str) and value in approved else "other"
        for value in raw_examples
    ] == ["other"] * len(raw_examples)

    rendered = repr(result["advertisers"])
    for forbidden in (
        "legacy",
        "unexpected",
        "contact@example.com",
        "phone",
        "message",
    ):
        assert forbidden not in rendered
    assert database.advertiser_leads.cursors[0].length == 1
