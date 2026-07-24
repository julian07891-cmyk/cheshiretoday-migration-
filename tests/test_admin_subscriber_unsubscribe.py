import os
import uuid
from copy import deepcopy
from types import SimpleNamespace

from fastapi.testclient import TestClient


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


MANAGEMENT_ID = str(uuid.uuid4())
OTHER_MANAGEMENT_ID = str(uuid.uuid4())


def _subscriber(*, active=True):
    return {
        "email": "reader@example.test",
        "newsletter_management_id": MANAGEMENT_ID,
        "newsletter_token_version": 7,
        "active": active,
        "daily_brief": True,
        "weekly_roundup": True,
        "breaking_news": True,
        "preferences": {"topics": ["business"]},
        "signup_source": "homepage",
        "subscriber_origin": "organic",
        "subscribed_at": "2026-01-01T00:00:00+00:00",
        "reactivated_at": "2026-02-01T00:00:00+00:00",
        "priority_daily_brief": True,
    }


class StubCursor:
    def __init__(self, records):
        self.records = records

    async def to_list(self, _limit):
        return [dict(record) for record in self.records]


class StubSubscribers:
    def __init__(self, records):
        self.records = [deepcopy(record) for record in records]
        self.find_one_calls = []
        self.update_calls = []
        self.delete_calls = []
        self.find_calls = []

    async def find_one(self, query, projection=None):
        self.find_one_calls.append((deepcopy(query), deepcopy(projection)))
        for record in self.records:
            if all(record.get(key) == value for key, value in query.items()):
                if projection:
                    return {
                        key: deepcopy(record[key])
                        for key, enabled in projection.items()
                        if enabled and key in record
                    }
                return deepcopy(record)
        return None

    async def update_one(self, query, update):
        self.update_calls.append((deepcopy(query), deepcopy(update)))
        for record in self.records:
            if all(record.get(key) == value for key, value in query.items()):
                record.update(deepcopy(update["$set"]))
                return SimpleNamespace(matched_count=1, modified_count=1)
        return SimpleNamespace(matched_count=0, modified_count=0)

    async def delete_one(self, query):
        self.delete_calls.append(deepcopy(query))
        raise AssertionError("soft unsubscribe must never delete")

    def find(self, query, projection):
        self.find_calls.append((deepcopy(query), deepcopy(projection)))
        eligible = [
            record
            for record in self.records
            if record.get("active", "missing") is True
            or "active" not in record
        ]
        return StubCursor(eligible)


class StubDigestLog:
    def __init__(self):
        self.inserts = []

    async def insert_one(self, document):
        self.inserts.append(deepcopy(document))
        return SimpleNamespace(inserted_id="digest")


class StubDatabase:
    def __init__(self, records):
        self.subscribers = StubSubscribers(records)
        self.digest_log = StubDigestLog()
        self.unexpected_collection_access = []

    def __getattr__(self, name):
        self.unexpected_collection_access.append(name)
        raise AssertionError(f"unexpected collection access: {name}")


def _route(method, path):
    matches = [
        route
        for route in server.app.routes
        if getattr(route, "path", None) == path
        and method in getattr(route, "methods", set())
    ]
    assert len(matches) == 1
    return matches[0]


def _dependency_calls(dependant):
    calls = set()
    pending = list(dependant.dependencies)
    while pending:
        dependency = pending.pop()
        calls.add(dependency.call)
        pending.extend(dependency.dependencies)
    return calls


def _request(database, management_id=MANAGEMENT_ID):
    server.app.dependency_overrides[server.get_admin_auth] = lambda: True
    original_db = server.db
    server.db = database
    try:
        return TestClient(server.app).post(
            f"/api/admin/subscribers/{management_id}/unsubscribe"
        )
    finally:
        server.db = original_db
        server.app.dependency_overrides.pop(server.get_admin_auth, None)


def test_admin_unsubscribe_route_is_registered_once_and_authenticated():
    route = _route(
        "POST",
        "/api/admin/subscribers/{newsletter_management_id}/unsubscribe",
    )

    assert route.endpoint is server.admin_unsubscribe_subscriber
    assert server.get_admin_auth in _dependency_calls(route.dependant)


def test_unauthenticated_request_performs_no_database_work(monkeypatch):
    class UntouchedDatabase:
        touched = False

        def __getattr__(self, name):
            self.touched = True
            raise AssertionError(name)

    database = UntouchedDatabase()
    monkeypatch.setattr(server, "db", database)

    response = TestClient(server.app).post(
        f"/api/admin/subscribers/{MANAGEMENT_ID}/unsubscribe"
    )

    assert response.status_code == 401
    assert database.touched is False


def test_malformed_management_id_fails_before_database_access():
    database = StubDatabase([_subscriber()])

    response = _request(database, "not-a-canonical-uuid")

    assert response.status_code == 400
    assert database.subscribers.find_one_calls == []
    assert database.subscribers.update_calls == []


def test_unknown_management_id_fails_without_mutation():
    database = StubDatabase([_subscriber()])

    response = _request(database, OTHER_MANAGEMENT_ID)

    assert response.status_code == 404
    assert len(database.subscribers.find_one_calls) == 1
    assert database.subscribers.update_calls == []
    assert database.subscribers.delete_calls == []


def test_active_subscriber_changes_only_the_six_lifecycle_fields():
    original = _subscriber()
    database = StubDatabase(
        [
            original,
            {
                **_subscriber(),
                "email": "other@example.test",
                "newsletter_management_id": OTHER_MANAGEMENT_ID,
            },
        ]
    )

    response = _request(database)

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "newsletter_management_id": MANAGEMENT_ID,
        "active": False,
        "message": "Subscriber unsubscribed.",
    }
    assert len(database.subscribers.update_calls) == 1
    query, update = database.subscribers.update_calls[0]
    assert query == {"newsletter_management_id": MANAGEMENT_ID}
    assert set(update) == {"$set"}
    assert set(update["$set"]) == {
        "active",
        "daily_brief",
        "weekly_roundup",
        "breaking_news",
        "unsubscribed_at",
        "unsubscribe_method",
    }
    assert update["$set"]["active"] is False
    assert update["$set"]["daily_brief"] is False
    assert update["$set"]["weekly_roundup"] is False
    assert update["$set"]["breaking_news"] is False
    assert update["$set"]["unsubscribe_method"] == "admin"
    assert update["$set"]["unsubscribed_at"].endswith("+00:00")

    changed = database.subscribers.records[0]
    for key, value in original.items():
        if key not in update["$set"]:
            assert changed[key] == value
    assert changed["newsletter_token_version"] == 7
    assert database.subscribers.records[1]["active"] is True
    assert database.subscribers.delete_calls == []
    assert database.unexpected_collection_access == []


def test_already_inactive_subscriber_is_idempotent_and_preserves_timestamp():
    inactive = _subscriber(active=False)
    inactive.update(
        {
            "daily_brief": False,
            "weekly_roundup": False,
            "breaking_news": False,
            "unsubscribed_at": "2026-03-01T00:00:00+00:00",
            "unsubscribe_method": "secure_token",
        }
    )
    database = StubDatabase([inactive])

    response = _request(database)

    assert response.status_code == 200
    assert response.json()["active"] is False
    assert database.subscribers.update_calls == []
    assert database.subscribers.records[0] == inactive


def test_management_id_not_email_controls_subscriber_identity():
    first = _subscriber()
    second = {
        **_subscriber(),
        "email": "READER@example.test",
        "newsletter_management_id": OTHER_MANAGEMENT_ID,
    }
    database = StubDatabase([first, second])

    response = _request(database, OTHER_MANAGEMENT_ID)

    assert response.status_code == 200
    assert database.subscribers.records[0]["active"] is True
    assert database.subscribers.records[1]["active"] is False


def test_manual_campaign_all_uses_active_or_legacy_selection(monkeypatch):
    records = [
        {"email": "active@example.test", "active": True},
        {"email": "inactive@example.test", "active": False},
        {"email": "legacy@example.test"},
        {"active": True},
    ]
    database = StubDatabase(records)
    sent_to = []

    monkeypatch.setattr(server, "db", database)
    monkeypatch.setattr(
        server.email_service,
        "_generate_tracking_id",
        lambda _name: "tracking-id",
    )
    monkeypatch.setattr(
        server.email_service,
        "_get_tracking_pixel",
        lambda _tracking_id: "<pixel>",
    )
    monkeypatch.setattr(
        server.email_service,
        "_send_email",
        lambda email, *_args: sent_to.append(email) or True,
    )
    server.app.dependency_overrides[server.get_admin_auth] = lambda: True
    try:
        response = TestClient(server.app).post(
            "/api/admin/send-campaign-email",
            json={
                "subject": "Test",
                "text": "Campaign",
                "mode": "all",
            },
        )
    finally:
        server.app.dependency_overrides.pop(server.get_admin_auth, None)

    assert response.status_code == 200
    assert sent_to == ["active@example.test", "legacy@example.test"]
    assert database.subscribers.find_calls == [
        (
            {
                "$or": [
                    {"active": True},
                    {"active": {"$exists": False}},
                ]
            },
            {"_id": 0, "email": 1},
        )
    ]


def test_manual_campaign_test_mode_does_not_query_subscribers(monkeypatch):
    database = StubDatabase([{"email": "inactive@example.test", "active": False}])
    sent_to = []

    monkeypatch.setattr(server, "db", database)
    monkeypatch.setattr(
        server.email_service,
        "_generate_tracking_id",
        lambda _name: "tracking-id",
    )
    monkeypatch.setattr(
        server.email_service,
        "_get_tracking_pixel",
        lambda _tracking_id: "<pixel>",
    )
    monkeypatch.setattr(
        server.email_service,
        "_send_email",
        lambda email, *_args: sent_to.append(email) or True,
    )
    server.app.dependency_overrides[server.get_admin_auth] = lambda: True
    try:
        response = TestClient(server.app).post(
            "/api/admin/send-campaign-email",
            json={
                "subject": "Test",
                "text": "Campaign",
                "mode": "test",
                "test_email": "preview@example.test",
            },
        )
    finally:
        server.app.dependency_overrides.pop(server.get_admin_auth, None)

    assert response.status_code == 200
    assert sent_to == ["preview@example.test"]
    assert database.subscribers.find_calls == []

