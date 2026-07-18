import asyncio
import inspect
import os

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server

rss_routes = server.rss_routes


ROUTES = (
    ("/api/import-real-news", server.import_real_news),
    ("/api/rss/import-rss", rss_routes.import_rss_articles),
)


def _routes(app, method, path):
    return [
        route
        for route in app.routes
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


@pytest.mark.parametrize(("path", "endpoint"), ROUTES)
def test_legacy_import_has_one_authenticated_post_route(path, endpoint):
    routes = _routes(server.app, "POST", path)

    assert len(routes) == 1
    assert routes[0].endpoint is endpoint
    assert server.get_admin_auth in _dependency_calls(routes[0].dependant)


def test_public_rss_routes_remain_public_and_unchanged():
    expected = (
        ("/api/rss/rss-sources", rss_routes.list_rss_sources),
        ("/api/rss/feed.xml", rss_routes.generate_rss_feed),
    )

    for path, endpoint in expected:
        routes = _routes(server.app, "GET", path)
        assert len(routes) == 1
        assert routes[0].endpoint is endpoint
        assert server.get_admin_auth not in _dependency_calls(routes[0].dependant)


@pytest.mark.parametrize(("path", "_endpoint"), ROUTES)
def test_unauthenticated_legacy_import_reaches_no_business_collaborator(
    monkeypatch,
    path,
    _endpoint,
):
    class UntouchedCollaborator:
        def __init__(self):
            self.touched = False

        def __getattr__(self, name):
            self.touched = True
            raise AssertionError(
                f"business collaborator {name} must not run before authentication"
            )

    database = UntouchedCollaborator()
    rss_feed = UntouchedCollaborator()
    image_lookup_called = False

    async def fail_image_lookup(*args, **kwargs):
        nonlocal image_lookup_called
        image_lookup_called = True
        raise AssertionError("image lookup must not run before authentication")

    def fail_dependency():
        raise AssertionError(
            "RSS database or Perplexity dependency must not run before authentication"
        )

    monkeypatch.setattr(server, "db", database)
    monkeypatch.setattr(server, "news_feed_service", rss_feed)
    monkeypatch.setattr(server, "get_dynamic_image", fail_image_lookup)
    server.app.dependency_overrides[rss_routes.get_database] = fail_dependency
    server.app.dependency_overrides[rss_routes.get_rss_service] = fail_dependency
    try:
        response = TestClient(server.app).post(path)
    finally:
        server.app.dependency_overrides.clear()

    assert response.status_code == 401
    assert database.touched is False
    assert rss_feed.touched is False
    assert image_lookup_called is False


def test_module_router_has_no_import_post_and_factory_is_independent():
    assert _routes(rss_routes.router, "POST", "/api/rss/import-rss") == []

    async def stub_auth():
        return True

    first = rss_routes.create_admin_import_router(stub_auth)
    second = rss_routes.create_admin_import_router(stub_auth)

    first_routes = _routes(first, "POST", "/api/rss/import-rss")
    second_routes = _routes(second, "POST", "/api/rss/import-rss")
    assert len(first_routes) == 1
    assert len(second_routes) == 1
    assert first is not second
    assert first_routes[0] is not second_routes[0]
    assert first_routes[0].endpoint is rss_routes.import_rss_articles
    assert stub_auth in _dependency_calls(first_routes[0].dependant)
    assert _routes(rss_routes.router, "POST", "/api/rss/import-rss") == []


def test_factory_router_accepts_stub_auth_in_isolated_app():
    calls = []

    async def rejecting_stub():
        calls.append("auth")
        raise HTTPException(status_code=401, detail="test authentication required")

    isolated_app = FastAPI()
    isolated_app.include_router(
        rss_routes.create_admin_import_router(rejecting_stub)
    )

    response = TestClient(isolated_app).post("/api/rss/import-rss")

    assert response.status_code == 401
    assert calls == ["auth"]


def test_rss_routes_does_not_import_server_or_define_authentication():
    source = inspect.getsource(rss_routes)

    assert "import backend.server" not in source
    assert "from backend.server" not in source
    assert "def get_admin_auth" not in source
    assert "admin_tokens" not in source
    assert "ADMIN_PERMANENT_TOKEN" not in source


def test_representative_admin_routes_keep_production_auth_dependency():
    paths = (
        ("GET", "/api/admin/verify"),
        ("POST", "/api/admin/remove-duplicates"),
        ("POST", "/api/generate-articles"),
        ("POST", "/api/import-hybrid-news"),
    )

    for method, path in paths:
        routes = _routes(server.app, method, path)
        assert len(routes) == 1
        assert server.get_admin_auth in _dependency_calls(routes[0].dependant)


def test_permanent_and_invalid_token_behaviour_is_unchanged(monkeypatch):
    permanent_token = "isolated-test-permanent-token"
    monkeypatch.setenv("ADMIN_PERMANENT_TOKEN", permanent_token)

    assert asyncio.run(
        server.get_admin_auth(f"Bearer {permanent_token}")
    ) is True

    async def invalid_database_token(_token):
        return False

    monkeypatch.delenv("ADMIN_PERMANENT_TOKEN")
    monkeypatch.setattr(server, "verify_admin_token_db", invalid_database_token)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(server.get_admin_auth("Bearer invalid-test-token"))

    assert exc_info.value.status_code == 401
