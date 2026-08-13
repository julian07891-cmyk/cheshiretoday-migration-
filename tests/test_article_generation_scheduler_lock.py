import asyncio
import inspect
import os
from types import SimpleNamespace

os.environ["MONGO_URL"] = "mongodb://localhost:27017"
os.environ["DB_NAME"] = "cheshire_test"
os.environ["LOCAL_DEV_NO_DB"] = "1"

from backend import server


class FakeLocks:
    def __init__(self, *, acquisition_result=None, seed_error=None, acquisition_error=None):
        self.acquisition_result = acquisition_result
        self.seed_error = seed_error
        self.acquisition_error = acquisition_error
        self.events = []
        self.acquisition_query = None

    async def update_one(self, *_args, **_kwargs):
        self.events.append("lock_seed")
        if self.seed_error is not None:
            raise self.seed_error

    async def find_one_and_update(self, query, *_args, **_kwargs):
        self.events.append("lock_acquire")
        self.acquisition_query = query
        if self.acquisition_error is not None:
            raise self.acquisition_error
        return self.acquisition_result

    async def delete_one(self, *_args, **_kwargs):
        self.events.append("lock_release")


def _install_job_fakes(monkeypatch, locks):
    events = locks.events

    async def fake_generate(*_args, **_kwargs):
        events.append("generate")

    async def fake_cleanup(*_args, **_kwargs):
        events.append("cleanup")
        return {"total_removed": 0}

    monkeypatch.setattr(server, "db", SimpleNamespace(scheduler_locks=locks))
    monkeypatch.setattr(server, "_generate_articles_internal", fake_generate)
    monkeypatch.setattr(server, "_remove_duplicates_internal", fake_cleanup)


def test_acquired_lock_runs_generation_cleanup_and_release_once(monkeypatch):
    locks = FakeLocks(acquisition_result={"locked": True})
    _install_job_fakes(monkeypatch, locks)

    asyncio.run(server.daily_article_generation(count=12))

    assert locks.events == [
        "lock_seed",
        "lock_acquire",
        "generate",
        "cleanup",
        "lock_release",
    ]


def test_already_held_lock_skips_without_release(monkeypatch):
    locks = FakeLocks(acquisition_result=None)
    _install_job_fakes(monkeypatch, locks)

    asyncio.run(server.daily_article_generation(count=12))

    assert locks.events == ["lock_seed", "lock_acquire"]


def test_seed_exception_fails_closed_without_release(monkeypatch, caplog):
    locks = FakeLocks(seed_error=RuntimeError("seed unavailable"))
    _install_job_fakes(monkeypatch, locks)

    asyncio.run(server.daily_article_generation(count=12))

    assert locks.events == ["lock_seed"]
    assert "Article generation lock acquisition failed; skipping run" in caplog.text
    assert "seed unavailable" in caplog.text


def test_atomic_acquisition_exception_fails_closed_without_release(monkeypatch, caplog):
    locks = FakeLocks(acquisition_error=RuntimeError("claim unavailable"))
    _install_job_fakes(monkeypatch, locks)

    asyncio.run(server.daily_article_generation(count=12))

    assert locks.events == ["lock_seed", "lock_acquire"]
    assert "Article generation lock acquisition failed; skipping run" in caplog.text
    assert "claim unavailable" in caplog.text


def test_stale_or_expired_lock_takeover_still_runs_once(monkeypatch):
    locks = FakeLocks(acquisition_result={"locked": True})
    _install_job_fakes(monkeypatch, locks)

    asyncio.run(server.daily_article_generation(count=12))

    availability = locks.acquisition_query["$or"]
    assert availability[0] == {"locked_at": None}
    assert "$lt" in availability[1]["locked_at"]
    assert "$lt" in availability[2]["expires_at"]
    assert locks.events.count("generate") == 1
    assert locks.events.count("cleanup") == 1
    assert locks.events.count("lock_release") == 1


def test_manual_trigger_uses_same_fail_closed_generation_function():
    source = inspect.getsource(server.trigger_daily_generation)

    assert "Depends(get_admin_auth)" in source
    assert "await daily_article_generation(count=12)" in source


def test_article_scheduler_registrations_are_unchanged():
    source = inspect.getsource(server.startup_event)

    expected_registrations = (
        ("hour=6, minute=0", "id='morning_article_generation'"),
        ("hour=12, minute=0", "id='midday_article_generation'"),
        ("hour=18, minute=0", "id='evening_article_generation'"),
    )
    for trigger, job_id in expected_registrations:
        assert trigger in source
        assert job_id in source

    assert source.count("daily_article_generation,") == 3
    assert source.count("args=[12]") == 3
