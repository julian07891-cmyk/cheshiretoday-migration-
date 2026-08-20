"""Process-isolated allocator/BSON diagnostics for QA-OPS-001.

This module is deliberately test-only.  It has no network or database client and
uses deterministic synthetic BSON to approximate the bounded production scans.
"""

from __future__ import annotations

import argparse
import ctypes
import gc
import json
import os
import platform
import random
import resource
import subprocess
import sys
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

from bson import BSON, decode_all


DEFAULT_RECORD_COUNT = 4_200
MIN_DIAGNOSTIC_RECORDS = 4_100
MAX_DIAGNOSTIC_RECORDS = 4_500
DEFAULT_BATCH_LABEL = "default-like"
FIXED_BATCH_SIZES = (250, 100, 50)
WORKLOADS = ("duplicate", "short_content", "visible_pool", "visible_pool_streamed")
CHECKPOINTS = (
    "baseline",
    "synthetic_documents_ready",
    "decode_materialisation_complete",
    "application_processing_complete",
    "application_references_released",
    "after_gc_control",
    "final",
)
BOILERPLATE_MARKERS = (
    "this story has been reported by",
    "more details are expected to emerge soon",
    "for the latest news from across the region, keep following",
)
VISIBLE_PROJECTION = (
    "_id",
    "content",
    "summary",
    "publishedDate",
    "created_at",
    "source",
    "featured",
    "force_live",
    "is_priority_cheshire",
    "archived",
    "archive_reason",
    "manual_review_hidden_from_public",
    "verification_status",
    "rewrite_status",
    "manual_edited",
    "manual_edit_protected",
)
DUPLICATE_PROJECTION = (
    "_id",
    "title",
    "source_url",
    "manual_edit_protected",
    "manual_edited",
    "force_live",
    "manual_edited_at",
    "updated_at",
    "created_at",
    "publishedDate",
    "content",
)
SHORT_CONTENT_PROJECTION = (
    "_id",
    "content",
    "summary",
    "manual_review_hidden_from_public",
    "verification_status",
    "rewrite_status",
    "manual_edited",
    "manual_edit_protected",
    "source",
)


@dataclass(frozen=True)
class ChildRequest:
    workload: str
    batch_size: str
    record_count: int
    cycles: int
    process_mode: str
    run_gc: bool = True
    run_malloc_trim: bool = True


def _bounded_text(words: tuple[str, ...], length: int, offset: int) -> str:
    chunks = []
    current = 0
    index = offset
    while current < length:
        word = words[index % len(words)]
        chunks.append(word)
        current += len(word) + 1
        index += 1
    return " ".join(chunks)[:length]


def synthetic_articles(record_count: int = DEFAULT_RECORD_COUNT, seed: int = 20260818):
    """Return bounded, deterministic article-like data with varied text lengths."""
    if not 1 <= record_count <= MAX_DIAGNOSTIC_RECORDS:
        raise ValueError(f"record_count must be between 1 and {MAX_DIAGNOSTIC_RECORDS}")
    rng = random.Random(seed)
    words = (
        "cheshire", "reporting", "business", "community", "planning",
        "technology", "analysis", "council", "market", "transport",
        "education", "development", "public", "regional", "update",
    )
    records = []
    for index in range(record_count):
        content_length = rng.randint(650, 6_400)
        summary_length = rng.randint(80, 480)
        title_length = rng.randint(38, 132)
        duplicate_bucket = index // 97 if index % 97 in (0, 1) else index
        record = {
            "_id": f"synthetic-{index:05d}",
            "title": _bounded_text(words, title_length, index),
            "source_url": (
                f"https://synthetic.invalid/news/{duplicate_bucket}/"
                f"{'detail-' * (index % 5)}story"
            ),
            "content": _bounded_text(words, content_length, index + 3),
            "summary": _bounded_text(words, summary_length, index + 7),
            "publishedDate": f"2026-08-{1 + index % 18:02d}T{index % 24:02d}:00:00+00:00",
            "created_at": f"2026-08-{1 + index % 18:02d}T{index % 24:02d}:05:00+00:00",
            "source": "Synthetic Local" if index % 3 else "Synthetic UK",
            "archived": index % 19 == 0,
            "archive_reason": "auto_cap" if index % 19 == 0 else None,
            "featured": index % 211 == 0,
            "force_live": index % 307 == 0,
            "is_priority_cheshire": index % 173 == 0,
            "manual_edited": index % 257 == 0,
            "manual_edit_protected": index % 263 == 0,
            "manual_review_hidden_from_public": index % 229 == 0,
            "verification_status": "needs_manual_review" if index % 229 == 0 else "verified",
            "rewrite_status": "manual_review_required" if index % 233 == 0 else "rss_imported",
            "updated_at": f"2026-08-{1 + index % 18:02d}T{index % 24:02d}:10:00+00:00",
            "manual_edited_at": None,
        }
        if index % 113 == 0:
            record["content"] = record["content"][:550]
        if index % 127 == 0:
            record["summary"] += " " + BOILERPLATE_MARKERS[index % len(BOILERPLATE_MARKERS)]
        records.append(record)
    return records


def _project_and_encode(records: Iterable[dict], projection: tuple[str, ...]):
    return [BSON.encode({key: record.get(key) for key in projection}) for record in records]


def _default_like_batches(encoded: list[bytes]) -> Iterator[list[bytes]]:
    """Approximate Mongo's first batch and later 16 MiB response boundary."""
    if not encoded:
        return
    yield encoded[:101]
    batch = []
    batch_bytes = 0
    for item in encoded[101:]:
        if batch and batch_bytes + len(item) > 16 * 1024 * 1024:
            yield batch
            batch = []
            batch_bytes = 0
        batch.append(item)
        batch_bytes += len(item)
    if batch:
        yield batch


def _encoded_batches(encoded: list[bytes], batch_size: str) -> Iterator[list[bytes]]:
    if batch_size == DEFAULT_BATCH_LABEL:
        yield from _default_like_batches(encoded)
        return
    size = int(batch_size)
    if size not in FIXED_BATCH_SIZES:
        raise ValueError(f"unsupported batch size: {batch_size}")
    for index in range(0, len(encoded), size):
        yield encoded[index:index + size]


def _decode_batch(batch: list[bytes]):
    return decode_all(b"".join(batch))


def _current_rss_mb():
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/self/status", encoding="utf-8") as status:
                for line in status:
                    if line.startswith("VmRSS:"):
                        return round(float(line.split()[1]) / 1024, 3), "proc_status"
        except (OSError, ValueError, IndexError):
            pass
    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["/bin/ps", "-o", "rss=", "-p", str(os.getpid())],
                check=True,
                capture_output=True,
                text=True,
                timeout=2,
            )
            return round(float(result.stdout.strip()) / 1024, 3), "ps_rss"
        except (OSError, ValueError, subprocess.SubprocessError):
            pass
    maximum = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    divisor = 1024 * 1024 if sys.platform == "darwin" else 1024
    return round(float(maximum) / divisor, 3), "ru_maxrss_fallback"


def _smaps_rollup():
    fields = {
        "smaps_rss_mb": None,
        "smaps_pss_mb": None,
        "smaps_private_clean_mb": None,
        "smaps_private_dirty_mb": None,
        "smaps_anonymous_mb": None,
        "smaps_swap_mb": None,
    }
    path = Path("/proc/self/smaps_rollup")
    if not sys.platform.startswith("linux") or not path.exists():
        return fields
    names = {
        "Rss": "smaps_rss_mb",
        "Pss": "smaps_pss_mb",
        "Private_Clean": "smaps_private_clean_mb",
        "Private_Dirty": "smaps_private_dirty_mb",
        "Anonymous": "smaps_anonymous_mb",
        "Swap": "smaps_swap_mb",
    }
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition(":")
            if separator and key in names:
                fields[names[key]] = round(float(value.split()[0]) / 1024, 3)
    except (OSError, ValueError, IndexError):
        return {key: None for key in fields}
    return fields


def _measurement(request: ChildRequest, cycle: int, phase: str, started_at: float, **extra):
    rss_mb, rss_source = _current_rss_mb()
    current, peak = tracemalloc.get_traced_memory()
    result = {
        "workload": request.workload,
        "cycle": cycle,
        "process_mode": request.process_mode,
        "batch_size": request.batch_size,
        "phase": phase,
        "rss_mb": rss_mb,
        "rss_source": rss_source,
        "tracemalloc_current_mb": round(current / (1024 * 1024), 3),
        "tracemalloc_peak_mb": round(peak / (1024 * 1024), 3),
        "allocated_blocks": int(sys.getallocatedblocks()) if hasattr(sys, "getallocatedblocks") else None,
        "runtime_ms": round((time.perf_counter() - started_at) * 1000, 3),
    }
    result.update(_smaps_rollup())
    result.update(extra)
    return result


def _owner_protected(article: dict) -> bool:
    return bool(
        article.get("manual_edit_protected")
        or article.get("manual_edited")
        or article.get("force_live")
        or article.get("source") == "Manual Entry"
    )


def _short_content_assessment(article: dict):
    if article.get("manual_review_hidden_from_public") is True or _owner_protected(article):
        return None
    content = (article.get("content") or "").strip()
    summary = (article.get("summary") or "").strip()
    blob_len = len(content) + len(summary) + (1 if content and summary else 0)
    if blob_len < 1000:
        return blob_len
    content_l = content.lower()
    summary_l = summary.lower()
    if any(marker in content_l or marker in summary_l for marker in BOILERPLATE_MARKERS):
        return blob_len
    if content and summary:
        boundary_size = max(map(len, BOILERPLATE_MARKERS)) - 1
        boundary = content_l[-boundary_size:] + " " + summary_l[:boundary_size]
        if any(marker in boundary for marker in BOILERPLATE_MARKERS):
            return blob_len
    return None


def _counts_towards_visible_cap(article: dict) -> bool:
    content = str(article.get("content") or "").strip()
    summary = str(article.get("summary") or "").strip()
    return bool(
        content
        and article.get("manual_review_hidden_from_public") is not True
        and str(article.get("verification_status") or "") != "needs_manual_review"
        and str(article.get("rewrite_status") or "")
        not in {"manual_review_required", "ai_rewrite_needs_review"}
        and (_owner_protected(article) or len(f"{content} {summary}".strip()) >= 1000)
    )


def _duplicate_workload(encoded: list[bytes], batch_size: str):
    groups = {}
    decoded_count = 0
    for encoded_batch in _encoded_batches(encoded, batch_size):
        decoded_batch = _decode_batch(encoded_batch)
        for article in decoded_batch:
            source_url = (article.get("source_url") or "").strip().lower()
            title = (article.get("title") or "").strip()
            key = f"url::{source_url}" if source_url else f"title::{title.lower()}"
            group = groups.setdefault(key, {"display_title": title, "members": []})
            group["members"].append(
                {
                    "id": article.get("_id"),
                    "keep_score": (
                        int(_owner_protected(article)),
                        int(bool(article.get("force_live"))),
                        str(article.get("updated_at") or article.get("created_at") or ""),
                        len(article.get("content") or ""),
                    ),
                    "scan_order": decoded_count,
                }
            )
            decoded_count += 1
        decoded_batch = None
    duplicate_members = sum(len(value["members"]) for value in groups.values() if len(value["members"]) > 1)
    # Model bounded Stage 2 point refetch/revalidation without any persistence.
    encoded_by_id = {}
    for encoded_batch in _encoded_batches(encoded, "100"):
        for document, raw in zip(_decode_batch(encoded_batch), encoded_batch):
            encoded_by_id[document.get("_id")] = raw
    stage2_refetch_count = 0
    for group_key, group in groups.items():
        if len(group["members"]) <= 1:
            continue
        current_members = []
        for member in group["members"]:
            raw = encoded_by_id.get(member["id"])
            if raw is None:
                continue
            article = BSON(raw).decode()
            source_url = (article.get("source_url") or "").strip().lower()
            title = (article.get("title") or "").strip()
            current_key = f"url::{source_url}" if source_url else f"title::{title.lower()}"
            if current_key == group_key:
                current_members.append(member)
                stage2_refetch_count += 1
        current_members.sort(key=lambda item: item["keep_score"], reverse=True)
    encoded_by_id = None
    current_members = None
    return groups, {
        "decoded_count": decoded_count,
        "retained_scalar_count": decoded_count,
        "candidate_count": duplicate_members,
        "stage2_refetch_count": stage2_refetch_count,
    }


def _short_content_workload(encoded: list[bytes], batch_size: str):
    candidate_ids = []
    decoded_count = 0
    for encoded_batch in _encoded_batches(encoded, batch_size):
        decoded_batch = _decode_batch(encoded_batch)
        for article in decoded_batch:
            decoded_count += 1
            if _short_content_assessment(article) is not None:
                candidate_ids.append(article.get("_id"))
        decoded_batch = None
    return candidate_ids, {"decoded_count": decoded_count, "retained_scalar_count": len(candidate_ids), "candidate_count": len(candidate_ids)}


def _visible_pool_workload(encoded: list[bytes], batch_size: str, streamed: bool, on_decode_complete=None):
    if not streamed:
        materialized = []
        for encoded_batch in _encoded_batches(encoded, batch_size):
            materialized.extend(_decode_batch(encoded_batch))
        if on_decode_complete is not None:
            on_decode_complete({"decoded_count": len(materialized)})
        eligible = [article for article in materialized if _counts_towards_visible_cap(article)]
        eligible.sort(key=lambda article: str(article.get("publishedDate") or article.get("created_at") or ""), reverse=True)
        protected_ids = {article.get("_id") for article in materialized if _owner_protected(article)}
        retained = {
            "materialized": materialized,
            "eligible": eligible,
            "keep_ids": list(protected_ids.union(article.get("_id") for article in eligible[:100])),
        }
        return retained, {
            "decoded_count": len(materialized),
            "retained_scalar_count": len(retained["keep_ids"]),
            "candidate_count": len(eligible),
        }

    scalars = []
    decoded_count = 0
    for encoded_batch in _encoded_batches(encoded, batch_size):
        decoded_batch = _decode_batch(encoded_batch)
        for article in decoded_batch:
            decoded_count += 1
            if _counts_towards_visible_cap(article):
                scalars.append(
                    (
                        article.get("_id"),
                        str(article.get("publishedDate") or article.get("created_at") or ""),
                        _owner_protected(article),
                    )
                )
        decoded_batch = None
    if on_decode_complete is not None:
        on_decode_complete({"decoded_count": decoded_count, "retained_scalar_count": len(scalars)})
    scalars.sort(key=lambda item: item[1], reverse=True)
    protected_ids = {item[0] for item in scalars if item[2]}
    keep_ids = list(protected_ids.union(item[0] for item in scalars[:100]))
    return {"scalars": scalars, "keep_ids": keep_ids}, {
        "decoded_count": decoded_count,
        "retained_scalar_count": len(scalars),
        "candidate_count": len(scalars),
    }


def _malloc_trim():
    if not sys.platform.startswith("linux"):
        return False, "unsupported_platform", None
    try:
        libc_name, _ = platform.libc_ver()
        if libc_name != "glibc":
            return False, "non_glibc", None
        function = ctypes.CDLL(None).malloc_trim
        function.argtypes = [ctypes.c_size_t]
        function.restype = ctypes.c_int
        return True, "called", int(function(0))
    except (AttributeError, OSError):
        return False, "unavailable", None


def _run_cycle(request: ChildRequest, cycle: int):
    started_at = time.perf_counter()
    measurements = [_measurement(request, cycle, "baseline", started_at)]
    records = synthetic_articles(request.record_count, seed=20260818 + cycle)
    projection = {
        "duplicate": DUPLICATE_PROJECTION,
        "short_content": SHORT_CONTENT_PROJECTION,
        "visible_pool": VISIBLE_PROJECTION,
        "visible_pool_streamed": VISIBLE_PROJECTION,
    }[request.workload]
    encoded = _project_and_encode(records, projection)
    records = None
    measurements.append(_measurement(request, cycle, "synthetic_documents_ready", started_at, encoded_count=len(encoded)))
    tracemalloc.reset_peak()

    decode_checkpoint_recorded = False

    def record_decode_checkpoint(counts):
        nonlocal decode_checkpoint_recorded
        measurements.append(
            _measurement(request, cycle, "decode_materialisation_complete", started_at, **counts)
        )
        decode_checkpoint_recorded = True

    if request.workload == "duplicate":
        application_state, counts = _duplicate_workload(encoded, request.batch_size)
    elif request.workload == "short_content":
        application_state, counts = _short_content_workload(encoded, request.batch_size)
    else:
        application_state, counts = _visible_pool_workload(
            encoded,
            request.batch_size,
            streamed=request.workload == "visible_pool_streamed",
            on_decode_complete=record_decode_checkpoint,
        )
    if not decode_checkpoint_recorded:
        measurements.append(_measurement(request, cycle, "decode_materialisation_complete", started_at, **counts))
    measurements.append(_measurement(request, cycle, "application_processing_complete", started_at, **counts))

    application_state = None
    measurements.append(_measurement(request, cycle, "application_references_released", started_at, **counts))
    if request.run_gc:
        collected = gc.collect()
        measurements.append(_measurement(request, cycle, "after_gc_control", started_at, gc_collected=collected, **counts))
    else:
        measurements.append(_measurement(request, cycle, "after_gc_control", started_at, gc_collected=None, **counts))

    trim_supported = False
    trim_status = "not_requested"
    trim_result = None
    if request.run_malloc_trim:
        measurements.append(_measurement(request, cycle, "before_malloc_trim", started_at, **counts))
        trim_supported, trim_status, trim_result = _malloc_trim()
        measurements.append(
            _measurement(
                request,
                cycle,
                "after_malloc_trim" if trim_supported else "malloc_trim_unavailable",
                started_at,
                malloc_trim_status=trim_status,
                malloc_trim_result=trim_result,
                **counts,
            )
        )

    encoded = None
    gc.collect()
    measurements.append(_measurement(request, cycle, "final", started_at, **counts))
    return measurements, {
        "malloc_trim_supported": trim_supported,
        "malloc_trim_status": trim_status,
        "malloc_trim_result": trim_result,
    }


def _summarize_cycle(measurements: list[dict]):
    by_phase = {item["phase"]: item for item in measurements}
    baseline = by_phase["baseline"]
    released = by_phase["application_references_released"]
    final = by_phase["final"]
    peak_rss = max(item["rss_mb"] for item in measurements)
    peak_heap = max(item["tracemalloc_peak_mb"] for item in measurements)
    block_values = [item["allocated_blocks"] for item in measurements if item["allocated_blocks"] is not None]
    return {
        "workload": baseline["workload"],
        "cycle": baseline["cycle"],
        "process_mode": baseline["process_mode"],
        "batch_size": baseline["batch_size"],
        "baseline_rss_mb": baseline["rss_mb"],
        "peak_rss_mb": peak_rss,
        "post_release_rss_mb": released["rss_mb"],
        "final_rss_mb": final["rss_mb"],
        "rss_retained_mb": round(released["rss_mb"] - baseline["rss_mb"], 3),
        "peak_tracemalloc_mb": peak_heap,
        "final_tracemalloc_mb": final["tracemalloc_current_mb"],
        "blocks_released": max(block_values) - final["allocated_blocks"] if block_values and final["allocated_blocks"] is not None else None,
        "runtime_ms": final["runtime_ms"],
    }


def execute_child(request: ChildRequest):
    if request.workload not in WORKLOADS:
        raise ValueError(f"unsupported workload: {request.workload}")
    if request.process_mode not in {"fresh_child", "long_lived_child"}:
        raise ValueError(f"unsupported process mode: {request.process_mode}")
    tracemalloc.start(1)
    all_measurements = []
    controls = []
    for cycle in range(1, request.cycles + 1):
        measurements, control = _run_cycle(request, cycle)
        all_measurements.extend(measurements)
        controls.append(control)
    summaries = [
        _summarize_cycle([item for item in all_measurements if item["cycle"] == cycle])
        for cycle in range(1, request.cycles + 1)
    ]
    baselines = [item["baseline_rss_mb"] for item in summaries]
    return {
        "schema_version": 1,
        "platform": sys.platform,
        "python_version": platform.python_version(),
        "record_count": request.record_count,
        "measurements": all_measurements,
        "summaries": summaries,
        "controls": controls,
        "stair_step_delta_mb": round(baselines[-1] - baselines[0], 3) if len(baselines) > 1 else 0.0,
        "production_environment_used": False,
        "network_or_database_used": False,
    }


def _sanitized_child_environment():
    allowed = ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "PYTHONPATH", "DYLD_LIBRARY_PATH", "LD_LIBRARY_PATH")
    return {key: os.environ[key] for key in allowed if key in os.environ}


def run_child(
    workload: str,
    batch_size: str = DEFAULT_BATCH_LABEL,
    record_count: int = DEFAULT_RECORD_COUNT,
    cycles: int = 1,
    process_mode: str = "fresh_child",
    timeout: int = 180,
):
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--child",
        "--workload", workload,
        "--batch-size", str(batch_size),
        "--record-count", str(record_count),
        "--cycles", str(cycles),
        "--process-mode", process_mode,
    ]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_sanitized_child_environment(),
    )
    return json.loads(completed.stdout)


def run_fresh_child(workload: str, batch_size: str = DEFAULT_BATCH_LABEL, record_count: int = DEFAULT_RECORD_COUNT):
    return run_child(workload, batch_size, record_count, cycles=1, process_mode="fresh_child")


def run_long_lived_child(workload: str, batch_size: str = DEFAULT_BATCH_LABEL, record_count: int = DEFAULT_RECORD_COUNT, cycles: int = 3):
    if cycles < 3:
        raise ValueError("long-lived diagnostics require at least three cycles")
    return run_child(workload, batch_size, record_count, cycles=cycles, process_mode="long_lived_child")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--workload", choices=WORKLOADS, required=True)
    parser.add_argument("--batch-size", default=DEFAULT_BATCH_LABEL)
    parser.add_argument("--record-count", type=int, default=DEFAULT_RECORD_COUNT)
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--process-mode", choices=("fresh_child", "long_lived_child"), default="fresh_child")
    args = parser.parse_args()
    request = ChildRequest(
        workload=args.workload,
        batch_size=args.batch_size,
        record_count=args.record_count,
        cycles=args.cycles,
        process_mode=args.process_mode,
    )
    print(json.dumps(execute_child(request), separators=(",", ":")))


if __name__ == "__main__":
    main()
