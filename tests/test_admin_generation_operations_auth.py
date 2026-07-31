import asyncio
import inspect
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


ROUTES = (
    ("/api/generate-articles", server.generate_articles, "_generate_articles_internal"),
    ("/api/import-hybrid-news", server.import_hybrid_news, "_import_hybrid_news_internal"),
)


def _post_routes(path):
    return [
        route
        for route in server.app.routes
        if getattr(route, "path", None) == path
        and "POST" in getattr(route, "methods", set())
    ]


def _dependency_calls(dependant):
    calls = set()
    pending = list(dependant.dependencies)
    while pending:
        dependency = pending.pop()
        calls.add(dependency.call)
        pending.extend(dependency.dependencies)
    return calls


@pytest.mark.parametrize(("path", "endpoint", "_helper_name"), ROUTES)
def test_generation_operation_has_one_authenticated_route(path, endpoint, _helper_name):
    routes = _post_routes(path)

    assert len(routes) == 1
    assert routes[0].endpoint is endpoint
    assert server.get_admin_auth in _dependency_calls(routes[0].dependant)


@pytest.mark.parametrize(("path", "_endpoint", "helper_name"), ROUTES)
def test_unauthenticated_generation_operation_starts_no_business_work(
    monkeypatch,
    path,
    _endpoint,
    helper_name,
):
    called = False

    async def fail_if_helper_starts(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("business helper must not run before authentication")

    class UntouchedDatabase:
        touched = False

        def __getattr__(self, name):
            self.touched = True
            raise AssertionError("database must not be used before authentication")

    database = UntouchedDatabase()
    monkeypatch.setattr(server, helper_name, fail_if_helper_starts)
    monkeypatch.setattr(server, "db", database)

    response = TestClient(server.app).post(path)

    assert response.status_code == 401
    assert called is False
    assert database.touched is False


def test_authenticated_generate_wrapper_returns_helper_shape(monkeypatch):
    calls = []
    expected = server.GenerateArticlesResponse(
        success=True,
        generated=4,
        cheshire_articles=2,
        uk_articles=2,
    )

    async def fake_helper(request):
        calls.append(request)
        return expected

    server.app.dependency_overrides[server.get_admin_auth] = lambda: True
    monkeypatch.setattr(server, "_generate_articles_internal", fake_helper)
    try:
        response = TestClient(server.app).post(
            "/api/generate-articles",
            json={"count": 5, "include_uk_news": True},
        )
    finally:
        server.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(calls) == 1
    assert response.json() == {
        "success": True,
        "generated": 4,
        "cheshire_articles": 2,
        "uk_articles": 2,
    }


def test_authenticated_import_wrapper_returns_complete_helper_shape(monkeypatch):
    calls = []
    expected = {
        "success": True,
        "total_imported": 3,
        "public_imported": 2,
        "manual_review_imported": 1,
        "cheshire_articles": 1,
        "cheshire_from_perplexity": 1,
        "cheshire_from_rss": 0,
        "uk_articles": 2,
        "business_articles": 1,
        "tech_articles": 1,
        "rss_images_used": 2,
        "smart_images_used": 1,
        "estimated_cost_usd": 0.01,
        "sources": {"perplexity": True, "rss": True},
    }

    async def fake_helper(request):
        calls.append(request)
        return expected

    server.app.dependency_overrides[server.get_admin_auth] = lambda: True
    monkeypatch.setattr(server, "_import_hybrid_news_internal", fake_helper)
    try:
        response = TestClient(server.app).post(
            "/api/import-hybrid-news",
            json={"cheshire_articles": 1, "uk_articles": 2},
        )
    finally:
        server.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(calls) == 1
    assert response.json() == expected


def test_internal_generation_preserves_request_mapping_and_result(monkeypatch):
    requests = []

    async def fake_import(request):
        requests.append(request)
        return {
            "total_imported": 7,
            "cheshire_articles": 4,
            "uk_articles": 3,
        }

    async def fail_if_http_wrapper_called(*args, **kwargs):
        raise AssertionError("internal generation must not call HTTP wrapper")

    monkeypatch.setattr(server, "_import_hybrid_news_internal", fake_import)
    monkeypatch.setattr(server, "import_hybrid_news", fail_if_http_wrapper_called)

    result = asyncio.run(
        server._generate_articles_internal(
            server.GenerateArticlesRequest(
                count=7,
                include_uk_news=True,
                rewrite_delay_seconds=9,
                public_import_limit=5,
            )
        )
    )

    assert len(requests) == 1
    hybrid_request = requests[0]
    assert hybrid_request.cheshire_articles == 4
    assert hybrid_request.uk_articles == 2
    assert hybrid_request.use_perplexity is True
    assert hybrid_request.rewrite_delay_seconds == 9
    assert hybrid_request.public_import_limit == 5
    assert result.model_dump() == {
        "success": True,
        "generated": 7,
        "cheshire_articles": 4,
        "uk_articles": 3,
    }


def test_scheduled_generation_uses_internal_helper_and_preserves_lock_order(
    monkeypatch,
):
    events = []

    class FakeLocks:
        async def update_one(self, *args, **kwargs):
            events.append("lock_seed")

        async def find_one_and_update(self, query, update, return_document):
            events.append("lock_acquire")
            assert query["$or"][1]["locked_at"]["$lt"] is not None
            return {"locked": True}

        async def delete_one(self, query):
            events.append("lock_release")

    async def fake_generate(request, memory_started_at=None):
        events.append("generate")
        assert memory_started_at is not None
        assert request.count == 12
        assert request.include_uk_news is True
        assert request.public_import_limit == 6

    async def fake_cleanup(memory_started_at=None):
        events.append("cleanup")
        assert memory_started_at is not None
        return {"total_removed": 0}

    async def fail_if_http_wrapper_called(*args, **kwargs):
        raise AssertionError("scheduler must not call authenticated HTTP wrapper")

    monkeypatch.setattr(server, "db", SimpleNamespace(scheduler_locks=FakeLocks()))
    monkeypatch.setattr(server, "_generate_articles_internal", fake_generate)
    monkeypatch.setattr(server, "_remove_duplicates_internal", fake_cleanup)
    monkeypatch.setattr(server, "generate_articles", fail_if_http_wrapper_called)

    asyncio.run(server.daily_article_generation(count=12))

    assert events == [
        "lock_seed",
        "lock_acquire",
        "generate",
        "cleanup",
        "lock_release",
    ]


def test_internal_callers_use_helpers_not_http_wrappers():
    generation_source = inspect.getsource(server.daily_article_generation)
    refresh_source = inspect.getsource(server.clear_and_refresh_news)

    assert "_generate_articles_internal(" in generation_source
    assert "await generate_articles(" not in generation_source
    assert "public_import_limit=6" in generation_source
    assert "_import_hybrid_news_internal(" in refresh_source
    assert "await import_hybrid_news(" not in refresh_source


def test_admin_dashboard_generation_callers_send_bearer_authentication():
    dashboard = (
        Path(__file__).resolve().parents[1]
        / "frontend"
        / "src"
        / "components"
        / "AdminDashboard.jsx"
    ).read_text()

    generate_block = dashboard[
        dashboard.index("const handleGenerateArticles"):
        dashboard.index("// News Import Handlers")
    ]
    import_start = dashboard.index("const handleImportNews")
    import_block = dashboard[
        import_start:
        dashboard.index("const handleClearAndRefresh", import_start)
    ]

    assert "/api/generate-articles" in generate_block
    assert "...getAuthHeaders()" in generate_block
    assert "/api/import-hybrid-news" in import_block
    assert "'Authorization': `Bearer ${localStorage.getItem(TOKEN_KEY)}`" in import_block
