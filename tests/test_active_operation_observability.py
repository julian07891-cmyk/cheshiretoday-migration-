"""Stage 2Z-AN: proposed process-local contract; production is intentionally RED.

Design, not a distributed registry:
* ActiveOperationRegistry.track(kind) is a synchronous context manager spanning
  the entire async execution, including persistence and cleanup. Same-task nested
  scopes count once under the outer type; a separately scheduled child task is an
  independent execution even when it inherits ContextVars.
* confirm_coverage(entry_points, version=...) records a validated instrumentation
  manifest, not a lease or lock. Revalidation must check actual wiring; merely
  advancing a timestamp is not sufficient. Snapshot freshness uses monotonic time.
* Missing/stale/invalid coverage or identity yields unknown and active_counts=None,
  never a fabricated idle result. A known snapshot covers ONLY this process and
  the versioned manifest below, never all application routes/serving instances.
* No task/request/article/recipient objects, arguments, payloads or exception text
  belong in the registry. Fixed counters and metadata only; no database writes.
* Future server wiring must preserve signatures/auth and resolve the registry at
  invocation time. __active_operation_type__ exposes inspectable wrapper coverage.

ENTRY_POINTS is the bounded coverage manifest, not a promise to observe arbitrary
third-party or future work. Disabled startup create_task calls remain disabled.
No distributed clearance, heartbeat store, scheduler change or lock change is
requested by these tests. Unknown topology cannot be cleared by this foundation.
"""

import asyncio
import importlib
import importlib.util
import json
import socket
from contextlib import contextmanager
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest


VERSION = "active_operations_v1"
KINDS = frozenset({
    "article_generation", "article_import", "article_maintenance",
    "daily_brief", "weekly_roundup", "manual_newsletter", "admin_ai",
    "provider_evidence",
})
ENTRY_POINTS = {
    "daily_article_generation": "article_generation",
    "trigger_daily_generation": "article_generation",
    "generate_articles": "article_generation",
    "_generate_articles_internal": "article_generation",
    "import_hybrid_news": "article_import",
    "_import_hybrid_news_internal": "article_import",
    "import_real_news": "article_import",
    "clear_and_refresh_news": "article_maintenance",
    "regenerate_recent_article_content": "article_maintenance",
    "regenerate_article_content": "article_maintenance",
    "_remove_duplicates_internal": "article_maintenance",
    "cap_visible_articles": "article_maintenance",
    "send_scheduled_news_digest": "daily_brief",
    "send_weekly_roundup_email": "weekly_roundup",
    "send_digest_now": "manual_newsletter",
    "send_digest_test": "manual_newsletter",
    "send_weekly_roundup_test": "manual_newsletter",
    "send_weekly_roundup_batch_test": "manual_newsletter",
    "send_breaking_news_alert": "manual_newsletter",
    "send_migration_announcement": "manual_newsletter",
    "send_site_update_part1": "manual_newsletter",
    "send_site_update_part2": "manual_newsletter",
    "admin_run_onboarding_emails": "manual_newsletter",
    "admin_send_campaign_email": "manual_newsletter",
    "admin_ai_review_article": "admin_ai",
    "admin_openai_rewrite_draft": "admin_ai",
    "admin_perplexity_rewrite_test": "admin_ai",
    "receive_resend_webhook": "provider_evidence",
}
FIELDS = {
    "scope", "status", "reason", "instance_id", "process_id", "snapshot_at",
    "coverage_version", "coverage_age_seconds", "active_counts",
    "all_instances_covered",
}


@pytest.fixture(autouse=True)
def no_external_connections(monkeypatch):
    """Even a future wiring error must not reach MongoDB or a provider."""
    def forbidden(*args, **kwargs):
        raise AssertionError("External connection forbidden in synthetic RED tests")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setenv("MONGO_URL", "mongodb://localhost:27017")
    monkeypatch.setenv("DB_NAME", "cheshire_test")
    monkeypatch.setenv("LOCAL_DEV_NO_DB", "1")
    monkeypatch.setenv("AUTO_GENERATION_ENABLED", "false")


class Clock:
    def __init__(self):
        self.seconds = 100.0

    def monotonic(self):
        return self.seconds

    def utc_now(self):
        return datetime(2026, 10, 28, 10, 0, tzinfo=timezone.utc)


def production_module():
    name = "backend.app.active_operation_observability"
    assert importlib.util.find_spec(name) is not None, (
        "Missing active-operation observability production capability (Stage 2Z-AN RED)"
    )
    return importlib.import_module(name)


def registry(*, covered=True, instance_id="synthetic-instance", process_id=123):
    module = production_module()
    clock = Clock()
    result = module.ActiveOperationRegistry(
        instance_id=instance_id, process_id=process_id,
        monotonic=clock.monotonic, utc_now=clock.utc_now,
    )
    if covered:
        result.confirm_coverage(dict(ENTRY_POINTS), version=VERSION)
    return result, clock


def snapshot(result):
    return result.snapshot(max_age_seconds=30)


def counts(result):
    data = snapshot(result)
    assert data["status"] == "known"
    return data["active_counts"]


def test_fixed_manifest_and_kind_allowlists():
    module = production_module()
    assert dict(module.REQUIRED_ENTRY_POINTS) == ENTRY_POINTS
    assert frozenset(module.OPERATION_TYPES) == KINDS
    assert module.COVERAGE_VERSION == VERSION


def test_entry_await_persistence_and_final_return_lifetime():
    result, _ = registry()

    async def exercise():
        with result.track("daily_brief"):
            assert counts(result)["daily_brief"] == 1
            await asyncio.sleep(0)
            assert counts(result)["daily_brief"] == 1
            # A stored terminal digest is not function return: ledger/cursor may
            # still await. Remain active until all such work is finished.
            for phase in ("digest_result", "send_ledger", "batch_cursor", "cleanup"):
                await asyncio.sleep(0)
                assert counts(result)["daily_brief"] == 1, phase
        assert all(value == 0 for value in counts(result).values())

    asyncio.run(exercise())


def test_exception_propagates_and_releases_counter_without_private_text():
    result, _ = registry()

    async def exercise():
        with result.track("admin_ai"):
            await asyncio.sleep(0)
            raise RuntimeError("PRIVATE body reader@synthetic.invalid")

    with pytest.raises(RuntimeError, match="PRIVATE"):
        asyncio.run(exercise())
    assert counts(result)["admin_ai"] == 0
    assert "PRIVATE" not in json.dumps(snapshot(result))
    assert "reader@" not in json.dumps(snapshot(result))


def test_cancellation_propagates_and_releases_counter():
    result, _ = registry()

    async def exercise():
        entered = asyncio.Event()
        async def work():
            with result.track("article_import"):
                entered.set()
                await asyncio.Event().wait()
        task = asyncio.create_task(work())
        await entered.wait()
        assert counts(result)["article_import"] == 1
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert counts(result)["article_import"] == 0

    asyncio.run(exercise())


def test_same_task_nested_calls_count_only_outer_operation():
    result, _ = registry()

    async def exercise():
        with result.track("article_generation"):
            with result.track("article_import"):
                with result.track("article_maintenance"):
                    await asyncio.sleep(0)
                    assert sum(counts(result).values()) == 1
                    assert counts(result)["article_generation"] == 1
            assert counts(result)["article_generation"] == 1
        assert sum(counts(result).values()) == 0

    asyncio.run(exercise())


def test_nested_failure_does_not_release_outer_operation_early():
    result, _ = registry()

    async def exercise():
        with result.track("article_generation"):
            with pytest.raises(ValueError):
                with result.track("article_import"):
                    raise ValueError("synthetic")
            assert counts(result)["article_generation"] == 1
        assert sum(counts(result).values()) == 0

    asyncio.run(exercise())


def test_independent_child_tasks_are_counted_despite_inherited_context():
    result, _ = registry()

    async def exercise():
        gate = asyncio.Event()
        entered = [asyncio.Event(), asyncio.Event()]
        async def child(index):
            with result.track("article_import"):
                entered[index].set()
                await gate.wait()
        with result.track("article_generation"):
            tasks = [asyncio.create_task(child(i)) for i in range(2)]
            try:
                await asyncio.gather(*(event.wait() for event in entered))
                assert counts(result)["article_generation"] == 1
                assert counts(result)["article_import"] == 2
            finally:
                gate.set()
                await asyncio.gather(*tasks)
            assert sum(counts(result).values()) == 1
        assert sum(counts(result).values()) == 0

    asyncio.run(exercise())


@pytest.mark.parametrize("mode", ["missing", "partial", "wrong_version", "stale"])
def test_unconfirmed_coverage_is_unknown_not_zero(mode):
    result, clock = registry(covered=False)
    if mode == "partial":
        result.confirm_coverage({"daily_article_generation": "article_generation"}, version=VERSION)
    elif mode == "wrong_version":
        result.confirm_coverage(dict(ENTRY_POINTS), version="unsupported")
    elif mode == "stale":
        result.confirm_coverage(dict(ENTRY_POINTS), version=VERSION)
        clock.seconds += 31
    data = snapshot(result)
    assert data["status"] == "unknown"
    assert data["active_counts"] is None
    assert data["reason"] in {"incomplete_coverage", "unsupported_coverage", "stale_coverage"}
    assert data["all_instances_covered"] is False


def test_stale_coverage_does_not_erase_real_activity():
    result, clock = registry()
    async def exercise():
        with result.track("daily_brief"):
            clock.seconds += 31
            assert snapshot(result)["active_counts"] is None
            result.confirm_coverage(dict(ENTRY_POINTS), version=VERSION)
            assert counts(result)["daily_brief"] == 1
        assert counts(result)["daily_brief"] == 0
    asyncio.run(exercise())


@pytest.mark.parametrize("identity", ["", "unknown"])
def test_missing_runtime_identity_cannot_report_idle(identity):
    result, _ = registry(instance_id=identity)
    assert snapshot(result)["status"] == "unknown"
    assert snapshot(result)["active_counts"] is None


def test_snapshot_is_bounded_private_detached_and_explicitly_process_local():
    result, _ = registry()
    data = snapshot(result)
    assert set(data) == FIELDS
    assert data["scope"] == "process_local"
    assert data["all_instances_covered"] is False
    assert data["instance_id"] == "synthetic-instance"
    assert data["process_id"] == 123
    assert data["snapshot_at"] == "2026-10-28T10:00:00+00:00"
    assert data["coverage_version"] == VERSION
    assert data["coverage_age_seconds"] == 0
    assert set(data["active_counts"]) == KINDS
    assert all(type(value) is int and value == 0 for value in data["active_counts"].values())
    data["active_counts"]["admin_ai"] = 999
    assert counts(result)["admin_ai"] == 0


def test_unknown_kind_cannot_expand_cardinality_or_echo_input():
    result, _ = registry()
    private = "reader@synthetic.invalid/private-body"
    with pytest.raises(ValueError) as caught:
        with result.track(private):
            pass
    assert private not in str(caught.value)
    assert private not in json.dumps(snapshot(result))
    assert set(counts(result)) == KINDS


def test_sampling_failure_is_unknown_not_exception_or_false_idle():
    module = production_module()
    def broken_clock():
        raise RuntimeError("PRIVATE sampling error")
    result = module.ActiveOperationRegistry(
        instance_id="synthetic-instance", process_id=123,
        monotonic=lambda: 100.0, utc_now=broken_clock,
    )
    result.confirm_coverage(dict(ENTRY_POINTS), version=VERSION)
    data = snapshot(result)
    assert data["status"] == "unknown"
    assert data["active_counts"] is None
    assert data["reason"] == "unavailable"
    assert "PRIVATE" not in json.dumps(data)


@pytest.mark.parametrize("name,kind", sorted(ENTRY_POINTS.items()))
def test_real_entry_point_is_instrumented(name, kind):
    from backend import server
    endpoint = getattr(server, name)
    assert getattr(endpoint, "__active_operation_type__", None) == kind, (
        f"{name} has no active-operation lifecycle coverage"
    )


def test_actual_manual_generate_tracks_helper_await_and_preserves_result(monkeypatch):
    from backend import server
    result, _ = registry()
    monkeypatch.setattr(server, "active_operation_registry", result, raising=False)
    expected = object()
    async def helper(request):
        assert counts(result)["article_generation"] == 1
        await asyncio.sleep(0)
        assert counts(result)["article_generation"] == 1
        return expected
    monkeypatch.setattr(server, "_generate_articles_internal", helper)
    async def exercise():
        assert await server.generate_articles(server.GenerateArticlesRequest(), authorized=True) is expected
    asyncio.run(exercise())
    assert sum(counts(result).values()) == 0


@pytest.mark.parametrize("failed_phase", ["entry", "exit"])
@pytest.mark.parametrize("business_raises", [False, True])
def test_observability_failure_never_retries_or_masks_business_work(
    monkeypatch, failed_phase, business_raises,
):
    from backend import server
    events = []
    original = ValueError("original synthetic business error")
    expected = object()
    class UnavailableRegistry:
        @contextmanager
        def track(self, kind):
            if failed_phase == "entry":
                raise RuntimeError("PRIVATE diagnostic entry")
            try:
                yield
            finally:
                raise RuntimeError("PRIVATE diagnostic exit")
        def mark_unavailable(self):
            events.append("unknown")
    monkeypatch.setattr(server, "active_operation_registry", UnavailableRegistry(), raising=False)
    async def helper(request):
        events.append("business")
        if business_raises:
            raise original
        return expected
    monkeypatch.setattr(server, "_generate_articles_internal", helper)
    async def exercise():
        if business_raises:
            with pytest.raises(ValueError) as caught:
                await server.generate_articles(server.GenerateArticlesRequest(), authorized=True)
            assert caught.value is original
        else:
            assert await server.generate_articles(server.GenerateArticlesRequest(), authorized=True) is expected
    asyncio.run(exercise())
    assert events.count("business") == 1
    assert "unknown" in events, "Diagnostic failure must invalidate coverage, not report idle"


def test_actual_scheduled_generation_stays_active_through_cleanup_and_lock_release(monkeypatch):
    from backend import server
    result, _ = registry()
    monkeypatch.setattr(server, "active_operation_registry", result, raising=False)
    events = []
    def record(phase):
        assert counts(result)["article_generation"] == 1
        events.append(phase)
    class Locks:
        async def update_one(self, *args, **kwargs):
            record("seed")
        async def find_one_and_update(self, *args, **kwargs):
            record("acquire")
            return {"locked": True}
        async def delete_one(self, *args, **kwargs):
            await asyncio.sleep(0)
            record("release")
    async def generate(*args, **kwargs):
        record("generate")
    async def cleanup(*args, **kwargs):
        await asyncio.sleep(0)
        record("cleanup")
        return {"total_removed": 0}
    monkeypatch.setattr(server, "db", SimpleNamespace(scheduler_locks=Locks()))
    monkeypatch.setattr(server, "_generate_articles_internal", generate)
    monkeypatch.setattr(server, "_remove_duplicates_internal", cleanup)
    asyncio.run(server.daily_article_generation())
    assert events == ["seed", "acquire", "generate", "cleanup", "release"]
    assert sum(counts(result).values()) == 0


def test_actual_daily_brief_stays_active_after_terminal_digest_through_ledger_and_cursor(monkeypatch):
    from backend import server
    from tests.test_newsletter_daily_delivery import Collection, ARTICLE, subscriber, TOKEN_SERVICE
    from app.email_service import EmailService
    result, _ = registry()
    monkeypatch.setattr(server, "active_operation_registry", result, raising=False)
    events = []
    class Writes(Collection):
        def __init__(self, phase):
            super().__init__()
            self.phase = phase
        async def update_one(self, *args, **kwargs):
            await asyncio.sleep(0)
            assert counts(result)["daily_brief"] == 1
            events.append(self.phase)
            return await super().update_one(*args, **kwargs)
    database = SimpleNamespace(
        subscribers=Collection([subscriber(1)]), articles=Collection([ARTICLE]),
        digest_log=Writes("digest"), email_send_opportunities=Writes("ledger"),
        email_batch_cursors=Writes("cursor"),
    )
    service = EmailService()
    service.resend_enabled = False
    def smtp(*args, **kwargs):
        assert counts(result)["daily_brief"] == 1
        events.append("provider")
        service.last_provider_contacted = True
        return True
    async def evidence(**kwargs):
        await asyncio.sleep(0)
        assert counts(result)["daily_brief"] == 1
        events.append("evidence")
        return True, 0
    monkeypatch.setattr(server, "db", database)
    monkeypatch.setattr(server, "email_service", service)
    monkeypatch.setattr(service, "_send_email", smtp)
    monkeypatch.setattr(server, "_save_last_resend_acceptances", evidence)
    monkeypatch.setattr(server, "newsletter_token_service_from_environment", lambda: TOKEN_SERVICE)
    monkeypatch.setenv("HOSTNAME", "synthetic-instance")
    asyncio.run(server.send_scheduled_news_digest())
    assert events.count("provider") == 1
    assert "evidence" in events and "ledger" in events and "cursor" in events
    assert events.index("provider") < events.index("ledger") < events.index("cursor")
    assert sum(counts(result).values()) == 0


def test_status_route_requires_authentication_without_business_work():
    from backend import server
    routes = [route for route in server.app.routes
              if getattr(route, "path", None) == "/api/admin/active-operations"
              and "GET" in getattr(route, "methods", ())]
    assert len(routes) == 1, "Missing authenticated process-local status endpoint"
    dependencies = list(routes[0].dependant.dependencies)
    calls = set()
    while dependencies:
        item = dependencies.pop()
        calls.add(item.call)
        dependencies.extend(item.dependencies)
    assert server.get_admin_auth in calls


def test_no_legacy_scheduler_status_widening_or_new_job_registration():
    # Existing schedule endpoint remains schedule-only; an auth-only diagnostic
    # endpoint must not change the eight business job registrations.
    import inspect
    from backend import server
    source = inspect.getsource(server.get_scheduler_status)
    assert '"scheduler_running"' in source
    assert '"next_run_time"' in source
    assert '"active_counts"' not in source
    startup = inspect.getsource(server.startup_event)
    assert "asyncio.create_task(check_and_generate())" in startup
    assert "# asyncio.create_task(auto_clean_duplicate_articles())" in startup
    assert "id='daily_brief'" in startup
    assert "id=f'weekly_roundup_batch_{roundup_batch_slot}'" in startup
