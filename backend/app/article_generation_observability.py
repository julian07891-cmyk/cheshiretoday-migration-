"""Non-sensitive observability helpers for scheduled article generation."""

from __future__ import annotations

import sys
import time
from typing import Mapping

try:
    import resource
except ImportError:  # pragma: no cover - exercised through the None fallback
    resource = None


LOG_PREFIX = "article_generation_memory"

APPROVED_PHASES = frozenset(
    {
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
)

APPROVED_COUNT_FIELDS = frozenset(
    {
        "active_record_count",
        "archived_record_count",
        "candidate_count",
        "uk_candidate_count",
        "finance_candidate_count",
        "uk_imported_count",
        "finance_imported_count",
        "local_candidate_count",
        "local_imported_count",
        "business_imported_count",
        "tech_imported_count",
        "document_count",
    }
)


def _ru_maxrss_to_mb(ru_maxrss: float, platform_name: str) -> float | None:
    """Convert ru_maxrss to MiB using the platform's documented units."""
    value = float(ru_maxrss)
    if platform_name == "linux":
        return value / 1024
    if platform_name == "darwin":
        return value / (1024 * 1024)
    return None


def _sample_process_rss_mb() -> float | None:
    if resource is None:
        return None
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return _ru_maxrss_to_mb(usage.ru_maxrss, sys.platform)


def log_article_generation_memory(
    logger,
    phase: str,
    started_at: float,
    counts: Mapping[str, object] | None = None,
) -> None:
    """Emit one safe phase marker without ever interrupting production work."""
    try:
        if phase not in APPROVED_PHASES:
            return

        elapsed_seconds = max(0.0, time.monotonic() - float(started_at))
        fields = [
            LOG_PREFIX,
            f"phase={phase}",
            f"elapsed_seconds={elapsed_seconds:.2f}",
        ]

        try:
            rss_mb = _sample_process_rss_mb()
        except Exception:
            rss_mb = None

        if rss_mb is not None:
            fields.append(f"rss_mb={rss_mb:.1f}")

        for key, value in (counts or {}).items():
            if key not in APPROVED_COUNT_FIELDS:
                continue
            if isinstance(value, bool) or not isinstance(value, int):
                continue
            fields.append(f"{key}={value}")

        logger.info(" ".join(fields))
    except Exception:
        return
