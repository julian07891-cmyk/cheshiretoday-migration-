import json
import os
import re
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


ROUTES = (
    ("GET", "/api/check-subscribers", server.check_subscribers),
    ("POST", "/api/cleanup-subscribers", server.cleanup_duplicate_subscribers),
    ("POST", "/api/cleanup-invalid-emails", server.cleanup_invalid_emails),
)

TEST_RECORDS = (
    {"_id": "507f1f77bcf86cd799439011", "email": "reader@trusted-news.co.uk"},
    {"_id": "507f1f77bcf86cd799439012", "email": "READER@trusted-news.co.uk"},
    {"_id": "507f1f77bcf86cd799439013", "email": "invalid-address"},
)


def _routes(method, path):
    return [
        route
        for route in server.app.routes
        if getattr(route, "path", None) == path
        and method in getattr(route, "methods", set())
    ]


def _dependency_calls(dependant):
    calls = set()
    pending = list(dependant.dependencies)
    while pending:
        dependency = pending.pop()
        calls.add(dependency.call)
        pending.extend(dependency.dependencies)
    return calls


class StubCursor:
    def __init__(self, records):
        self.records = records

    async def to_list(self, _limit):
        return [dict(record) for record in self.records]


class StubSubscribers:
    def __init__(self, records):
        self.records = records
        self.deleted_ids = []

    def find(self, *_args, **_kwargs):
        return StubCursor(self.records)

    async def delete_one(self, query):
        self.deleted_ids.append(query["_id"])
        return SimpleNamespace(deleted_count=1)


class StubDatabase:
    def __init__(self, records):
        self.subscribers = StubSubscribers(records)


def _assert_response_is_aggregate_only(payload):
    rendered = json.dumps(payload)

    assert re.search(r"[^@\s]+@[^@\s]+", rendered) is None
    assert "_id" not in rendered
    assert "507f1f77bcf86cd799439011" not in rendered
    assert "507f1f77bcf86cd799439012" not in rendered
    assert "507f1f77bcf86cd799439013" not in rendered


@pytest.mark.parametrize(("method", "path", "endpoint"), ROUTES)
def test_subscriber_operation_has_one_authenticated_route(method, path, endpoint):
    routes = _routes(method, path)

    assert len(routes) == 1
    assert routes[0].endpoint is endpoint
    assert server.get_admin_auth in _dependency_calls(routes[0].dependant)


@pytest.mark.parametrize(("method", "path", "_endpoint"), ROUTES)
def test_unauthenticated_subscriber_operation_starts_no_database_work(
    monkeypatch,
    method,
    path,
    _endpoint,
):
    class UntouchedDatabase:
        def __init__(self):
            self.touched = False

        def __getattr__(self, name):
            self.touched = True
            raise AssertionError(
                f"database collaborator {name} must not be used before authentication"
            )

    database = UntouchedDatabase()
    monkeypatch.setattr(server, "db", database)

    response = TestClient(server.app).request(method, path)

    assert response.status_code == 401
    assert database.touched is False


@pytest.mark.parametrize(("method", "path", "_endpoint"), ROUTES)
def test_authenticated_subscriber_response_is_aggregate_only(
    monkeypatch,
    method,
    path,
    _endpoint,
):
    database = StubDatabase(TEST_RECORDS)
    monkeypatch.setattr(server, "db", database)
    server.app.dependency_overrides[server.get_admin_auth] = lambda: True

    try:
        response = TestClient(server.app).request(method, path)
    finally:
        server.app.dependency_overrides.pop(server.get_admin_auth, None)

    assert response.status_code == 200
    _assert_response_is_aggregate_only(response.json())


def test_check_subscribers_returns_duplicate_aggregates_only(monkeypatch):
    database = StubDatabase(TEST_RECORDS)
    monkeypatch.setattr(server, "db", database)
    server.app.dependency_overrides[server.get_admin_auth] = lambda: True

    try:
        response = TestClient(server.app).get("/api/check-subscribers")
    finally:
        server.app.dependency_overrides.pop(server.get_admin_auth, None)

    assert response.status_code == 200
    assert response.json() == {
        "total_records": 3,
        "unique_emails": 2,
        "duplicate_emails": 1,
        "duplicate_records": 1,
    }


def test_cleanup_duplicate_subscribers_returns_counts_only(monkeypatch):
    database = StubDatabase(TEST_RECORDS)
    monkeypatch.setattr(server, "db", database)
    server.app.dependency_overrides[server.get_admin_auth] = lambda: True

    try:
        response = TestClient(server.app).post("/api/cleanup-subscribers")
    finally:
        server.app.dependency_overrides.pop(server.get_admin_auth, None)

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "duplicates_removed": 1,
        "remaining_subscribers": 2,
    }
    _assert_response_is_aggregate_only(response.json())


def test_cleanup_invalid_emails_returns_counts_only(monkeypatch):
    database = StubDatabase(TEST_RECORDS)
    monkeypatch.setattr(server, "db", database)
    server.app.dependency_overrides[server.get_admin_auth] = lambda: True

    try:
        response = TestClient(server.app).post("/api/cleanup-invalid-emails")
    finally:
        server.app.dependency_overrides.pop(server.get_admin_auth, None)

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "invalid_removed": 1,
        "remaining_subscribers": 2,
    }
