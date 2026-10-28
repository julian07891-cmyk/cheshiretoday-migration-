"""Additional local acceptance for live wrapper validation and private status."""
import asyncio
import ast
import inspect
import subprocess
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from tests.test_active_operation_observability import (
    ENTRY_POINTS, FIELDS, VERSION, no_external_connections, registry,
)
from backend import server


@pytest.fixture
def status_client(monkeypatch):
    current, clock = registry(covered=False)
    monkeypatch.setattr(server, "active_operation_registry", current)
    previous = dict(server.app.dependency_overrides)
    server.app.dependency_overrides[server.get_admin_auth] = lambda: True
    try:
        yield TestClient(server.app), current, clock
    finally:
        server.app.dependency_overrides.clear()
        server.app.dependency_overrides.update(previous)


def test_unauthenticated_status_rejected_before_registry_use(monkeypatch):
    class Untouched:
        def __getattr__(self, name):
            raise AssertionError("authentication must precede diagnostics")
    monkeypatch.setattr(server, "active_operation_registry", Untouched())
    response = TestClient(server.app).get("/api/admin/active-operations")
    assert response.status_code == 401


def test_status_revalidates_complete_manifest_and_cannot_clear_other_instances(status_client):
    client, current, clock = status_client
    response = client.get("/api/admin/active-operations")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "private, no-store"
    data = response.json()
    assert set(data) == FIELDS
    assert data["status"] == "known"
    assert data["scope"] == "process_local"
    assert data["all_instances_covered"] is False
    assert data["coverage_version"] == VERSION
    clock.seconds += 31
    assert current.snapshot()["reason"] == "stale_coverage"
    # Endpoint verifies actual current callables again before refreshing age.
    assert client.get("/api/admin/active-operations").json()["status"] == "known"


def test_missing_wrapper_invalidates_coverage_without_resetting_counts(status_client, monkeypatch):
    client, current, _ = status_client
    original = server.admin_ai_review_article
    monkeypatch.setattr(server, "admin_ai_review_article", original.__wrapped__)
    assert client.get("/api/admin/active-operations").json()["active_counts"] is None
    monkeypatch.setattr(server, "admin_ai_review_article", original)
    # Recovered wiring cannot prove no activity was missed in the invalid period.
    assert client.get("/api/admin/active-operations").json()["status"] == "unknown"


def test_removed_http_route_does_not_pass_coverage_validation(status_client, monkeypatch):
    client, _, _ = status_client
    monkeypatch.setattr(server.app.router, "routes", [
        route for route in server.app.routes
        if getattr(route, "name", None) != "admin_ai_review_article"
    ])
    data = client.get("/api/admin/active-operations").json()
    assert data["status"] == "unknown"
    assert data["active_counts"] is None


@pytest.mark.parametrize("binding", ["normal", "unwrapped"])
def test_active_http_operation_uses_executable_binding_for_coverage(
    status_client, monkeypatch, binding,
):
    _, _, _ = status_client  # Applies the established synthetic auth override.
    route = next(route for route in server.app.routes
                 if getattr(route, "name", None) == "admin_ai_review_article")
    observed = server.admin_ai_review_article
    assert route.endpoint is observed
    assert route.dependant.call is observed
    if binding == "unwrapped":
        monkeypatch.setattr(route.dependant, "call", observed.__wrapped__)
    events = []

    async def exercise():
        entered = asyncio.Event()
        finish = asyncio.Event()
        async def find_article(_article_id):
            return {"_id": "synthetic", "title": "Synthetic"}
        async def review(_article):
            events.append("business")
            entered.set()
            await finish.wait()
            return {"risk_level": "low"}
        async def persist(*args, **kwargs):
            events.append("persist")
            return SimpleNamespace(matched_count=1)
        monkeypatch.setattr(server, "_find_article_by_any_id", find_article)
        monkeypatch.setattr(server, "run_openai_article_review", review)
        monkeypatch.setattr(server, "db", SimpleNamespace(
            articles=SimpleNamespace(update_one=persist),
        ))
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=server.app), base_url="http://testserver",
        ) as client:
            task = asyncio.create_task(client.post("/api/admin/articles/synthetic/ai-review"))
            try:
                await asyncio.wait_for(entered.wait(), timeout=2)
                assert not task.done()
                assert server.admin_ai_review_article is observed
                assert route.endpoint is observed
                response = await client.get("/api/admin/active-operations")
                assert response.status_code == 200
                assert response.headers["cache-control"] == "private, no-store"
                data = response.json()
                assert set(data) == FIELDS
                assert data["scope"] == "process_local"
                assert data["all_instances_covered"] is False
                if binding == "normal":
                    assert data["status"] == "known"
                    assert data["active_counts"]["admin_ai"] == 1
                else:
                    assert data["status"] == "unknown"
                    assert data["active_counts"] is None
                assert "Synthetic" not in response.text
                assert "synthetic" not in str(data.get("active_counts"))
            finally:
                finish.set()
                completed = await task
                assert completed.status_code == 200
                assert completed.json()["success"] is True
    asyncio.run(exercise())
    assert events == ["business", "persist"]


@pytest.mark.parametrize("binding", ["missing_call", "none", "unwrapped", "foreign", "missing_dependant"])
def test_invalid_executable_binding_is_unknown_and_stays_invalid_after_restore(
    status_client, monkeypatch, binding,
):
    client, _, _ = status_client
    route = next(route for route in server.app.routes
                 if getattr(route, "name", None) == "admin_ai_review_article")
    observed = route.endpoint
    async def foreign(*args, **kwargs):
        raise AssertionError("Diagnostics must not invoke or repair a route binding")
    assert client.get("/api/admin/active-operations").json()["status"] == "known"
    with monkeypatch.context() as changes:
        if binding == "missing_dependant":
            changes.setattr(route, "dependant", None)
        elif binding == "missing_call":
            changes.delattr(route.dependant, "call")
        else:
            changes.setattr(route.dependant, "call", {
                "none": None, "unwrapped": observed.__wrapped__, "foreign": foreign,
            }[binding])
        data = client.get("/api/admin/active-operations").json()
        assert data["status"] == "unknown"
        assert data["active_counts"] is None
        assert route.endpoint is observed
    assert route.dependant.call is observed
    data = client.get("/api/admin/active-operations").json()
    assert data["status"] == "unknown"
    assert data["active_counts"] is None


def test_status_sampling_failure_is_private_unknown(status_client, monkeypatch):
    client, current, _ = status_client
    def broken():
        raise RuntimeError("PRIVATE provider text reader@synthetic.invalid")
    monkeypatch.setattr(current, "_utc_now", broken)
    response = client.get("/api/admin/active-operations")
    assert response.status_code == 200
    assert response.json()["status"] == "unknown"
    assert response.json()["active_counts"] is None
    assert "PRIVATE" not in response.text
    assert "reader@" not in response.text


@pytest.mark.parametrize("name", sorted(ENTRY_POINTS))
def test_wrapper_preserves_signature_and_identity(name):
    observed = getattr(server, name)
    original = observed.__wrapped__
    assert inspect.signature(observed) == inspect.signature(original)
    assert observed.__name__ == original.__name__
    assert inspect.iscoroutinefunction(observed)


def test_real_wrapper_cancellation_releases_activity(monkeypatch):
    current, _ = registry()
    monkeypatch.setattr(server, "active_operation_registry", current)
    async def exercise():
        entered = asyncio.Event()
        async def helper(*args, **kwargs):
            entered.set()
            await asyncio.Event().wait()
        monkeypatch.setattr(server, "_generate_articles_internal", helper)
        task = asyncio.create_task(server.generate_articles(server.GenerateArticlesRequest(), authorized=True))
        await entered.wait()
        assert current.snapshot()["active_counts"]["article_generation"] == 1
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert current.snapshot()["active_counts"]["article_generation"] == 0
    asyncio.run(exercise())


def test_weekly_activity_extends_through_terminal_state_ledger_cursor_and_lock_release(monkeypatch):
    from tests.test_newsletter_weekly_delivery import runtime
    from tests.test_newsletter_daily_delivery import subscriber, TOKEN_SERVICE
    current, _ = registry()
    monkeypatch.setattr(server, "active_operation_registry", current)
    monkeypatch.setattr(server, "weekly_roundup_digest_index_ready", True)
    monkeypatch.setattr(server, "newsletter_token_service_from_environment", lambda: TOKEN_SERVICE)
    database, service = runtime(monkeypatch, [subscriber(1, priority_daily_brief=True)])
    events = []
    def record(phase):
        assert current.snapshot()["active_counts"]["weekly_roundup"] == 1
        events.append(phase)
    def smtp(*args, **kwargs):
        record("provider")
        service.last_provider_contacted = True
        return True
    monkeypatch.setattr(service, "_send_email", smtp)
    # Intercept synthetic storage only, preserving every original fake operation.
    for collection, method, phase in (
        (database.digest_log, "update_one", "digest"),
        (database.email_send_opportunities, "update_one", "ledger"),
        (database.email_batch_cursors, "update_one", "cursor"),
        (database.scheduler_locks, "delete_one", "release"),
    ):
        original = getattr(collection, method)
        async def observed(*args, _original=original, _phase=phase, **kwargs):
            await asyncio.sleep(0)
            record(_phase)
            return await _original(*args, **kwargs)
        monkeypatch.setattr(collection, method, observed)
    asyncio.run(server.send_weekly_roundup_email(1))
    assert events.count("provider") == 1
    assert events.index("provider") < events.index("ledger") < events.index("cursor") < events.index("release")
    assert database.digest_log.documents[0]["status"] == "sent"
    assert current.snapshot()["active_counts"]["weekly_roundup"] == 0


def test_existing_server_functions_and_route_declarations_are_unchanged_except_tracking():
    root = Path(__file__).resolve().parents[1]
    parent = ast.parse(subprocess.check_output(
        ["git", "show", "HEAD:backend/server.py"], cwd=root, text=True,
    ))
    current = ast.parse((root / "backend/server.py").read_text())
    types = (ast.FunctionDef, ast.AsyncFunctionDef)
    # Legacy server.py contains repeated function names. Compare each occurrence
    # in source order rather than silently replacing an earlier definition.
    functions = {}
    for node in current.body:
        if isinstance(node, types):
            functions.setdefault(node.name, []).append(node)
    for original in parent.body:
        if not isinstance(original, types):
            continue
        actual = functions[original.name].pop(0)
        actual.decorator_list = [decorator for decorator in actual.decorator_list
                                 if not (isinstance(decorator, ast.Call)
                                         and isinstance(decorator.func, ast.Name)
                                         and decorator.func.id == "_observe_active_operation")]
        assert ast.dump(actual) == ast.dump(original), original.name
