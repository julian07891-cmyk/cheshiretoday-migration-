"""Non-sensitive observability helpers for scheduled article generation."""

from __future__ import annotations

import gc
import math
import sys
import time
import tracemalloc
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
        "article_import_returned",
        "duplicate_cleanup_first_read_completed",
        "duplicate_cleanup_first_stage2_completed",
        "duplicate_cleanup_second_read_completed",
        "duplicate_cleanup_returned",
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

_PYTHON_HEAP_FIELD_ORDER = (
    "python_heap_current_mb",
    "python_heap_peak_mb",
    "python_allocated_blocks",
    "gc_gen0_count",
    "gc_gen1_count",
    "gc_gen2_count",
)
_python_heap_diagnostics_enabled = False


def prepare_article_generation_memory_observability() -> None:
    """Enable bounded heap counters once without disturbing existing tracing."""
    global _python_heap_diagnostics_enabled

    try:
        if not tracemalloc.is_tracing():
            # One frame is sufficient for current/peak counters and minimises
            # tracing overhead. Tracing remains active across scheduled runs so
            # the next job start is comparable with the previous completion.
            tracemalloc.start(1)
        _python_heap_diagnostics_enabled = True
    except Exception:
        # Diagnostics must never prevent scheduled article generation.
        _python_heap_diagnostics_enabled = False


def _sample_python_heap_diagnostics() -> dict[str, float | int]:
    """Return fixed-size counters; never inspect objects or take snapshots."""
    if not _python_heap_diagnostics_enabled:
        return {}

    fields: dict[str, float | int] = {}
    try:
        current_bytes, peak_bytes = tracemalloc.get_traced_memory()
        current_mb = current_bytes / (1024 * 1024)
        peak_mb = peak_bytes / (1024 * 1024)
        if current_mb >= 0 and math.isfinite(current_mb):
            fields["python_heap_current_mb"] = current_mb
        if peak_mb >= 0 and math.isfinite(peak_mb):
            fields["python_heap_peak_mb"] = peak_mb
    except Exception:
        pass

    try:
        allocated_blocks = sys.getallocatedblocks()
        if isinstance(allocated_blocks, int) and allocated_blocks >= 0:
            fields["python_allocated_blocks"] = allocated_blocks
    except Exception:
        pass

    try:
        gc_counts = gc.get_count()
        if len(gc_counts) == 3:
            for generation, value in enumerate(gc_counts):
                if isinstance(value, int) and value >= 0:
                    fields[f"gc_gen{generation}_count"] = value
    except Exception:
        pass

    return fields


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


def _sample_current_rss_mb() -> float | None:
    """Read the current resident set size from Linux procfs."""
    try:
        with open("/proc/self/status", encoding="utf-8") as status_file:
            for line in status_file:
                label, separator, value = line.partition(":")
                if separator != ":" or label.strip() != "VmRSS":
                    continue
                parts = value.split()
                if len(parts) != 2 or parts[1] != "kB":
                    return None
                value_kb = int(parts[0])
                if value_kb < 0:
                    return None
                return value_kb / 1024
    except Exception:
        return None
    return None


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

        try:
            current_rss_mb = _sample_current_rss_mb()
        except Exception:
            current_rss_mb = None

        if current_rss_mb is not None:
            fields.append(f"current_rss_mb={current_rss_mb:.1f}")

        try:
            python_diagnostics = _sample_python_heap_diagnostics()
        except Exception:
            python_diagnostics = {}

        for key in _PYTHON_HEAP_FIELD_ORDER:
            value = python_diagnostics.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            if isinstance(value, float):
                if value < 0 or not math.isfinite(value):
                    continue
                fields.append(f"{key}={value:.1f}")
            elif value >= 0:
                fields.append(f"{key}={value}")

        for key, value in (counts or {}).items():
            if key not in APPROVED_COUNT_FIELDS:
                continue
            if isinstance(value, bool) or not isinstance(value, int):
                continue
            fields.append(f"{key}={value}")

        logger.info(" ".join(fields))
    except Exception:
        return
