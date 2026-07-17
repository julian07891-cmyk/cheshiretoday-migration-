import asyncio
import os

from fastapi.testclient import TestClient


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


def _remove_duplicates_routes():
    return [
        route
        for route in server.app.routes
        if getattr(route, "path", None) == "/api/admin/remove-duplicates"
        and "POST" in getattr(route, "methods", set())
    ]


def test_remove_duplicates_has_one_authenticated_route():
    routes = _remove_duplicates_routes()

    assert len(routes) == 1
    assert routes[0].endpoint is server.remove_duplicate_articles


def test_unauthenticated_remove_duplicates_does_not_run_cleanup(monkeypatch):
    cleanup_called = False

    async def fail_if_called():
        nonlocal cleanup_called
        cleanup_called = True
        raise AssertionError("cleanup must not run for an unauthenticated request")

    monkeypatch.setattr(server, "_remove_duplicates_internal", fail_if_called)

    response = TestClient(server.app).post("/api/admin/remove-duplicates")

    assert response.status_code == 401
    assert cleanup_called is False


def test_internal_remove_duplicates_remains_directly_callable(monkeypatch):
    class EmptyCursor:
        async def to_list(self, _length):
            return []

    class EmptyArticles:
        def find(self, _query):
            return EmptyCursor()

        async def count_documents(self, _query):
            return 0

    class EmptyDatabase:
        articles = EmptyArticles()

    monkeypatch.setattr(server, "db", EmptyDatabase())

    result = asyncio.run(server._remove_duplicates_internal())

    assert result == {
        "success": True,
        "duplicates_removed": 0,
        "short_articles_removed": 0,
        "total_removed": 0,
        "remaining_articles": 0,
    }
