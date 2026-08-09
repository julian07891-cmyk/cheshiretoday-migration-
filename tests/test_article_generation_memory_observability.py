import asyncio
import builtins
import io
import os
from types import SimpleNamespace

import pytest

os.environ["MONGO_URL"] = "mongodb://localhost:27017"
os.environ["DB_NAME"] = "test_database"
os.environ["LOCAL_DEV_NO_DB"] = "1"

from backend import server
from backend.app import article_generation_observability as observability


class RecordingLogger:
    def __init__(self, fail=False):
        self.messages = []
        self.fail = fail

    def info(self, message):
        if self.fail:
            raise RuntimeError("logger unavailable")
        self.messages.append(message)


def test_normal_phase_log_contains_only_approved_numeric_fields(monkeypatch):
    logger = RecordingLogger()
    monkeypatch.setattr(observability.time, "monotonic", lambda: 15.5)
    monkeypatch.setattr(observability, "_sample_process_rss_mb", lambda: 438.7)
    monkeypatch.setattr(observability, "_sample_current_rss_mb", lambda: None)

    observability.log_article_generation_memory(
        logger,
        "all_feed_fetch_completed",
        2.5,
        {
            "candidate_count": 742,
            "title": "private title",
            "source_url": "https://private.invalid/story",
            "image_url": "https://private.invalid/image.jpg",
            "content": "private article body",
            "credential": "private credential-like value",
            "database_record": {"email": "private@example.invalid"},
            "document_count": "not-an-integer",
            "active_record_count": True,
        },
    )

    assert logger.messages == [
        "article_generation_memory phase=all_feed_fetch_completed "
        "elapsed_seconds=13.00 rss_mb=438.7 candidate_count=742"
    ]


def test_memory_sampling_failure_is_non_fatal(monkeypatch):
    logger = RecordingLogger()
    monkeypatch.setattr(observability.time, "monotonic", lambda: 3.0)

    def fail_sample():
        raise RuntimeError("sample failed")

    monkeypatch.setattr(observability, "_sample_process_rss_mb", fail_sample)
    monkeypatch.setattr(observability, "_sample_current_rss_mb", lambda: None)
    observability.log_article_generation_memory(logger, "job_started", 1.0)

    assert logger.messages == [
        "article_generation_memory phase=job_started elapsed_seconds=2.00"
    ]


def test_logging_failure_is_non_fatal(monkeypatch):
    monkeypatch.setattr(observability, "_sample_process_rss_mb", lambda: 1.0)
    observability.log_article_generation_memory(
        RecordingLogger(fail=True),
        "job_started",
        0.0,
    )


def test_unapproved_phase_and_text_metadata_are_not_emitted(monkeypatch):
    logger = RecordingLogger()
    monkeypatch.setattr(observability, "_sample_process_rss_mb", lambda: 1.0)

    observability.log_article_generation_memory(
        logger,
        "article_title",
        0.0,
        {"candidate_count": 1},
    )

    assert logger.messages == []


def test_ru_maxrss_platform_units_are_deterministic():
    assert observability._ru_maxrss_to_mb(512 * 1024, "linux") == 512
    assert observability._ru_maxrss_to_mb(512 * 1024 * 1024, "darwin") == 512


def test_current_rss_linux_vmrss_is_converted_from_kb(monkeypatch):
    monkeypatch.setattr(
        builtins,
        "open",
        lambda *_args, **_kwargs: io.StringIO(
            "Name:\tpython\nVmRSS:\t204800 kB\nThreads:\t1\n"
        ),
    )

    assert observability._sample_current_rss_mb() == 200.0


@pytest.mark.parametrize(
    "vmrss_line",
    [
        "VmRSS: 204800 kB\n",
        "VmRSS:\t  204800    kB  \n",
        "  VmRSS : 204800 kB\n",
    ],
)
def test_current_rss_accepts_proc_whitespace_variation(monkeypatch, vmrss_line):
    monkeypatch.setattr(
        builtins,
        "open",
        lambda *_args, **_kwargs: io.StringIO(vmrss_line),
    )

    assert observability._sample_current_rss_mb() == 200.0


@pytest.mark.parametrize(
    "status_text",
    [
        "Name:\tpython\nThreads:\t1\n",
        "VmRSS: not-a-number kB\n",
        "VmRSS: 204800 MB\n",
        "VmRSS: -1 kB\n",
    ],
)
def test_current_rss_malformed_or_missing_value_is_safe(monkeypatch, status_text):
    monkeypatch.setattr(
        builtins,
        "open",
        lambda *_args, **_kwargs: io.StringIO(status_text),
    )

    assert observability._sample_current_rss_mb() is None


@pytest.mark.parametrize("error", [OSError("unavailable"), RuntimeError("unexpected")])
def test_current_rss_open_failure_is_safe(monkeypatch, error):
    def fail_open(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(builtins, "open", fail_open)

    assert observability._sample_current_rss_mb() is None


def test_phase_log_contains_peak_and_current_rss(monkeypatch):
    logger = RecordingLogger()
    monkeypatch.setattr(observability.time, "monotonic", lambda: 5.0)
    monkeypatch.setattr(observability, "_sample_process_rss_mb", lambda: 455.4)
    monkeypatch.setattr(observability, "_sample_current_rss_mb", lambda: 360.2)

    observability.log_article_generation_memory(logger, "job_started", 2.0)

    assert logger.messages == [
        "article_generation_memory phase=job_started elapsed_seconds=3.00 "
        "rss_mb=455.4 current_rss_mb=360.2"
    ]


def test_current_rss_failure_keeps_peak_rss_log(monkeypatch):
    logger = RecordingLogger()
    monkeypatch.setattr(observability.time, "monotonic", lambda: 5.0)
    monkeypatch.setattr(observability, "_sample_process_rss_mb", lambda: 455.4)

    def fail_current_sample():
        raise RuntimeError("current RSS unavailable")

    monkeypatch.setattr(observability, "_sample_current_rss_mb", fail_current_sample)

    observability.log_article_generation_memory(logger, "job_started", 2.0)

    assert logger.messages == [
        "article_generation_memory phase=job_started elapsed_seconds=3.00 "
        "rss_mb=455.4"
    ]


def test_unsupported_platform_omits_rss_and_keeps_phase_log(monkeypatch):
    logger = RecordingLogger()
    fake_resource = SimpleNamespace(
        RUSAGE_SELF=0,
        getrusage=lambda _who: SimpleNamespace(ru_maxrss=512 * 1024),
    )
    monkeypatch.setattr(observability, "resource", fake_resource)
    monkeypatch.setattr(observability.sys, "platform", "unsupported")
    monkeypatch.setattr(observability.time, "monotonic", lambda: 4.0)
    monkeypatch.setattr(observability, "_sample_current_rss_mb", lambda: None)

    observability.log_article_generation_memory(logger, "job_started", 1.0)

    assert observability._sample_process_rss_mb() is None
    assert logger.messages == [
        "article_generation_memory phase=job_started elapsed_seconds=3.00"
    ]


def test_missing_resource_module_omits_rss_and_keeps_phase_log(monkeypatch):
    logger = RecordingLogger()
    monkeypatch.setattr(observability, "resource", None)
    monkeypatch.setattr(observability.sys, "platform", "linux")
    monkeypatch.setattr(observability.time, "monotonic", lambda: 6.0)
    monkeypatch.setattr(observability, "_sample_current_rss_mb", lambda: None)

    observability.log_article_generation_memory(logger, "job_started", 2.0)

    assert observability._sample_process_rss_mb() is None
    assert logger.messages == [
        "article_generation_memory phase=job_started elapsed_seconds=4.00"
    ]


def test_synthetic_all_feed_phase_can_report_higher_sample_without_io(monkeypatch):
    logger = RecordingLogger()
    samples = iter([120.0, 440.0])
    monkeypatch.setattr(observability, "_sample_process_rss_mb", lambda: next(samples))
    monkeypatch.setattr(observability.time, "monotonic", lambda: 5.0)

    observability.log_article_generation_memory(logger, "job_started", 0.0)
    observability.log_article_generation_memory(
        logger,
        "all_feed_fetch_completed",
        0.0,
        {"candidate_count": 5000},
    )

    assert "rss_mb=120.0" in logger.messages[0]
    assert "rss_mb=440.0" in logger.messages[1]
    assert "candidate_count=5000" in logger.messages[1]


def test_hybrid_import_reaches_instrumented_phase_markers_in_order(monkeypatch):
    phases = []

    class Cursor:
        async def to_list(self, _length):
            return []

    class Collection:
        def find(self, *_args, **_kwargs):
            return Cursor()

    class NewsFeed:
        async def fetch_all_feeds(self):
            return []

        async def fetch_local_feeds_only(self):
            return []

        async def fetch_local_news(self):
            return []

    async def fake_cap_visible_articles(keep):
        assert keep == 100

    monkeypatch.setattr(
        server,
        "db",
        SimpleNamespace(articles=Collection(), archived_articles=Collection()),
    )
    monkeypatch.setattr(server, "news_feed_service", NewsFeed())
    monkeypatch.setattr(server, "cap_visible_articles", fake_cap_visible_articles)
    monkeypatch.setattr(
        server,
        "log_article_generation_memory",
        lambda _logger, phase, _started_at, counts=None: phases.append(phase),
    )

    asyncio.run(
        server._import_hybrid_news_internal(
            server.HybridNewsRequest(
                cheshire_articles=0,
                uk_articles=1,
                business_articles=0,
                tech_articles=0,
                use_perplexity=False,
            ),
            memory_started_at=1.0,
        )
    )

    assert phases == [
        "existing_record_index_completed",
        "all_feed_fetch_completed",
        "uk_finance_processing_completed",
        "local_feed_fetch_completed",
        "local_processing_completed",
        "business_tech_processing_completed",
        "visible_pool_cap_completed",
    ]


def test_duplicate_cleanup_reaches_both_read_markers_in_order(monkeypatch):
    phases = []

    class Cursor:
        async def to_list(self, _length):
            return []

        def __aiter__(self):
            return self

        async def __anext__(self):
            raise StopAsyncIteration

    class Articles:
        def find(self, *_args, **_kwargs):
            return Cursor()

        async def count_documents(self, _query):
            return 0

    monkeypatch.setattr(server, "db", SimpleNamespace(articles=Articles()))
    monkeypatch.setattr(
        server,
        "log_article_generation_memory",
        lambda _logger, phase, _started_at, counts=None: phases.append(phase),
    )

    asyncio.run(server._remove_duplicates_internal(memory_started_at=1.0))

    assert phases == [
        "duplicate_cleanup_first_read_completed",
        "duplicate_cleanup_second_read_completed",
    ]


def test_scheduled_workflow_reaches_all_phase_markers_in_order(monkeypatch):
    phases = []

    class Locks:
        async def update_one(self, *_args, **_kwargs):
            return None

        async def find_one_and_update(self, *_args, **_kwargs):
            return {"locked": True}

        async def delete_one(self, *_args, **_kwargs):
            return None

    def record(_logger, phase, _started_at, counts=None):
        phases.append(phase)

    async def fake_generate(
        _request,
        memory_started_at=None,
        enable_editorial_similarity_shadow=False,
    ):
        assert memory_started_at is not None
        assert enable_editorial_similarity_shadow is True
        for phase in (
            "existing_record_index_completed",
            "all_feed_fetch_completed",
            "uk_finance_processing_completed",
            "local_feed_fetch_completed",
            "local_processing_completed",
            "business_tech_processing_completed",
            "visible_pool_cap_completed",
        ):
            record(None, phase, memory_started_at)

    async def fake_cleanup(memory_started_at=None):
        assert memory_started_at is not None
        record(None, "duplicate_cleanup_first_read_completed", memory_started_at)
        record(None, "duplicate_cleanup_second_read_completed", memory_started_at)
        return {"total_removed": 0}

    monkeypatch.setattr(server, "db", SimpleNamespace(scheduler_locks=Locks()))
    monkeypatch.setattr(server, "log_article_generation_memory", record)
    monkeypatch.setattr(server, "_generate_articles_internal", fake_generate)
    monkeypatch.setattr(server, "_remove_duplicates_internal", fake_cleanup)

    asyncio.run(server.daily_article_generation(count=12))

    assert phases == [
        "job_started",
        "lock_acquired",
        "existing_record_index_completed",
        "all_feed_fetch_completed",
        "uk_finance_processing_completed",
        "local_feed_fetch_completed",
        "local_processing_completed",
        "business_tech_processing_completed",
        "visible_pool_cap_completed",
        "duplicate_cleanup_first_read_completed",
        "duplicate_cleanup_second_read_completed",
        "job_completed",
    ]


def test_required_phase_inventory_is_exact():
    assert observability.APPROVED_PHASES == {
        "job_started",
        "lock_acquired",
        "existing_record_index_completed",
        "all_feed_fetch_completed",
        "uk_finance_processing_completed",
        "local_feed_fetch_completed",
        "local_processing_completed",
        "business_tech_processing_completed",
        "visible_pool_cap_completed",
        "duplicate_cleanup_first_read_completed",
        "duplicate_cleanup_second_read_completed",
        "job_completed",
    }
