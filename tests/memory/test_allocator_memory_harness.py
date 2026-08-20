import json
from pathlib import Path

import pytest

from tests.memory import allocator_memory_harness as harness


REQUIRED_MEASUREMENT_FIELDS = {
    "workload",
    "cycle",
    "process_mode",
    "batch_size",
    "phase",
    "rss_mb",
    "tracemalloc_current_mb",
    "tracemalloc_peak_mb",
    "allocated_blocks",
    "runtime_ms",
    "smaps_rss_mb",
    "smaps_pss_mb",
    "smaps_private_clean_mb",
    "smaps_private_dirty_mb",
    "smaps_anonymous_mb",
    "smaps_swap_mb",
}


def test_synthetic_dataset_is_deterministic_varied_and_bounded():
    first = harness.synthetic_articles(120)
    second = harness.synthetic_articles(120)

    assert first == second
    assert len(first) == 120
    assert len({len(article["content"]) for article in first}) > 50
    assert len({len(article["summary"]) for article in first}) > 40
    assert all(article["source_url"].startswith("https://synthetic.invalid/") for article in first)
    with pytest.raises(ValueError):
        harness.synthetic_articles(harness.MAX_DIAGNOSTIC_RECORDS + 1)


def test_fresh_child_returns_json_safe_structured_checkpoints():
    result = harness.run_fresh_child("short_content", record_count=240)

    assert result["schema_version"] == 1
    assert result["production_environment_used"] is False
    assert result["network_or_database_used"] is False
    assert result["record_count"] == 240
    phases = {measurement["phase"] for measurement in result["measurements"]}
    assert set(harness.CHECKPOINTS).issubset(phases)
    assert all(REQUIRED_MEASUREMENT_FIELDS <= measurement.keys() for measurement in result["measurements"])
    json.dumps(result)


def test_long_lived_child_records_three_separate_cycles_with_stable_schema():
    result = harness.run_long_lived_child("duplicate", record_count=180, cycles=3)

    assert [summary["cycle"] for summary in result["summaries"]] == [1, 2, 3]
    assert {measurement["cycle"] for measurement in result["measurements"]} == {1, 2, 3}
    assert isinstance(result["stair_step_delta_mb"], float)
    schemas = [set(measurement) for measurement in result["measurements"]]
    assert all(REQUIRED_MEASUREMENT_FIELDS <= schema for schema in schemas)


@pytest.mark.parametrize("batch_size", [harness.DEFAULT_BATCH_LABEL, "250", "100", "50"])
def test_all_requested_batch_variants_run(batch_size):
    result = harness.run_fresh_child("short_content", batch_size=batch_size, record_count=160)

    assert result["summaries"][0]["batch_size"] == batch_size
    assert result["summaries"][0]["runtime_ms"] > 0


@pytest.mark.parametrize("workload", harness.WORKLOADS)
def test_each_workload_runs_without_live_services(workload):
    result = harness.run_fresh_child(workload, record_count=160)

    assert result["network_or_database_used"] is False
    assert result["summaries"][0]["workload"] == workload


def test_traced_heap_falls_after_materialised_references_and_corpus_release():
    result = harness.run_fresh_child("visible_pool", record_count=700)
    summary = result["summaries"][0]

    assert summary["peak_tracemalloc_mb"] > 1.0
    assert summary["final_tracemalloc_mb"] < summary["peak_tracemalloc_mb"] * 0.5


def test_platform_specific_controls_are_safe_and_explicit():
    result = harness.run_fresh_child("short_content", record_count=120)
    control = result["controls"][0]
    phases = {measurement["phase"] for measurement in result["measurements"]}

    assert control["malloc_trim_status"] in {
        "called", "unsupported_platform", "non_glibc", "unavailable"
    }
    assert {"after_malloc_trim", "malloc_trim_unavailable"} & phases
    if not result["platform"].startswith("linux"):
        assert all(item["smaps_rss_mb"] is None for item in result["measurements"])


def test_harness_has_no_production_client_or_application_imports():
    source = Path(harness.__file__).read_text(encoding="utf-8")

    forbidden = (
        "MongoClient(",
        "AsyncIOMotorClient(",
        "backend.server",
        "requests.",
        "httpx.",
        "MONGO_URL",
        "RENDER_",
    )
    assert all(value not in source for value in forbidden)
    assert "gc.collect()" in source
    assert "malloc_trim" in source


def test_production_source_is_not_part_of_diagnostic_boundary():
    root = Path(__file__).resolve().parents[2]
    assert (root / "backend" / "server.py").exists()
    assert str(root / "backend" / "server.py") != harness.__file__
