import asyncio
import copy
import logging
import os
import re

import pytest

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


TIMING_FIELDS = (
    "total_handler_ms",
    "count_ms",
    "force_materialise_ms",
    "local_materialise_ms",
    "uk_materialise_ms",
    "editorial_filter_ms",
    "selection_ms",
    "fallback_ms",
    "post_selection_ms",
    "final_shape_ms",
)

COUNT_FIELDS = (
    "force_candidates",
    "local_candidates_before_filter",
    "local_candidates_after_filter",
    "uk_candidates_before_filter",
    "uk_candidates_after_filter",
    "curated_before_fallback",
    "deferred_lead_incidents",
    "deferred_lead_crime",
    "deferred_overcap_incidents",
    "deferred_overcap_crime",
    "fallback_ran",
    "fallback_candidates",
    "pre_dedupe_count",
    "dedupe_removed_count",
    "final_count",
)


def _article(index, *, local):
    return {
        "_id": f"article-{index}",
        "title": f"Distinctive{index:04d} Regional{index:04d} bulletin",
        "summary": f"UniqueSummary{index:04d} UniqueDetail{index:04d} bulletin.",
        "category": "Local News" if local else "UK News",
        "author": "Cheshire Today",
        "publishedDate": f"2026-08-{(index % 28) + 1:02d}T12:00:00+00:00",
        "created_at": f"2026-08-{(index % 28) + 1:02d}T12:00:00+00:00",
        "image": f"https://images.example.test/news-{index}.jpg",
        "tags": [],
        "featured": False,
        "source": "Synthetic News",
        "source_url": f"https://source.example.test/story/{index}",
        "scope": "cheshire" if local else "uk",
        "is_local_source": local,
        "location": "chester" if local else None,
        "priority_location": "chester" if local else None,
    }


class FakeCursor:
    def __init__(self, documents, operations):
        self.documents = copy.deepcopy(documents)
        self.operations = operations

    def sort(self, *args):
        self.operations.append(("sort", args))
        return self

    def skip(self, value):
        self.operations.append(("skip", value))
        return self

    def limit(self, value):
        self.operations.append(("limit", value))
        self.documents = self.documents[:value]
        return self

    async def to_list(self, value):
        self.operations.append(("to_list", value))
        return copy.deepcopy(self.documents[:value])


class FakeArticlesCollection:
    def __init__(self, *, local, uk, force=None, fallback=None):
        self.local = local
        self.uk = uk
        self.force = force or []
        self.fallback = fallback or []
        self.calls = []

    async def count_documents(self, query):
        self.calls.append(("count_documents", copy.deepcopy(query)))
        return len(self.local) + len(self.uk)

    def find(self, query, projection):
        query_copy = copy.deepcopy(query)
        projection_copy = copy.deepcopy(projection)
        operations = []
        self.calls.append(("find", query_copy, projection_copy, operations))

        first_clause = query.get("$and", [{}])[0] if query.get("$and") else {}
        if first_clause.get("force_live") is True:
            documents = self.force
        elif first_clause.get("is_local_source") is True:
            documents = self.local
        elif isinstance(first_clause.get("is_local_source"), dict):
            documents = self.uk
        elif "$or" in query:
            documents = self.fallback
        else:
            documents = []
        return FakeCursor(documents, operations)


def _parse_marker(messages):
    markers = [message for message in messages if message.startswith("homepage_article_list_timing ")]
    assert len(markers) == 1
    return markers[0], dict(field.split("=", 1) for field in markers[0].split()[1:])


async def _run_homepage(monkeypatch, collection, *, enabled, logger=None, **kwargs):
    monkeypatch.setattr(server.db, "articles", collection)
    monkeypatch.setenv("HOMEPAGE_ARTICLE_LIST_TIMING", "true" if enabled else "false")
    monkeypatch.setenv("UK_FILTER_NOISE", "0")
    messages = []
    monkeypatch.setattr(server.logger, "info", logger or messages.append)
    response = await server.get_articles(limit=80, **kwargs)
    return response, messages


def test_gate_disabled_emits_no_marker(monkeypatch):
    collection = FakeArticlesCollection(
        local=[_article(i, local=True) for i in range(40)],
        uk=[_article(i + 100, local=False) for i in range(40)],
    )

    response, messages = asyncio.run(
        _run_homepage(monkeypatch, collection, enabled=False)
    )

    assert len(response) == 80
    assert not any("homepage_article_list_timing" in message for message in messages)


def test_exact_homepage_emits_one_bounded_complete_marker(monkeypatch):
    secret_title = "PRIVATE-MARKER-SENTINEL"
    local = [_article(i, local=True) for i in range(40)]
    local[0]["title"] = secret_title
    collection = FakeArticlesCollection(
        local=local,
        uk=[_article(i + 100, local=False) for i in range(40)],
    )

    response, messages = asyncio.run(
        _run_homepage(monkeypatch, collection, enabled=True)
    )
    marker, fields = _parse_marker(messages)

    assert len(response) == 80
    assert set(TIMING_FIELDS + COUNT_FIELDS) <= set(fields)
    assert all(float(fields[name]) >= 0 for name in TIMING_FIELDS)
    assert all(int(fields[name]) >= 0 for name in COUNT_FIELDS)
    assert fields["fallback_ran"] == "0"
    assert fields["fallback_candidates"] == "0"
    assert float(fields["fallback_ms"]) == 0
    assert secret_title not in marker
    assert "source.example.test" not in marker
    assert not re.search(r"article-\d+", marker)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"limit": 30},
        {"category": "Business"},
        {"search": "economy"},
        {"source_type": "local"},
        {"skip": 1},
        {"include_archived": True},
        {"with_total": True},
    ],
)
def test_non_homepage_shapes_emit_no_marker(monkeypatch, kwargs):
    collection = FakeArticlesCollection(
        local=[_article(i, local=True) for i in range(40)],
        uk=[_article(i + 100, local=False) for i in range(40)],
    )
    monkeypatch.setattr(server.db, "articles", collection)
    monkeypatch.setenv("HOMEPAGE_ARTICLE_LIST_TIMING", "on")
    messages = []
    monkeypatch.setattr(server.logger, "info", messages.append)

    asyncio.run(server.get_articles(**kwargs))

    assert not any("homepage_article_list_timing" in message for message in messages)


def test_fallback_marker_records_candidates_and_elapsed_time(monkeypatch):
    collection = FakeArticlesCollection(
        local=[_article(1, local=True)],
        uk=[_article(101, local=False)],
        fallback=[_article(i + 200, local=i % 2 == 0) for i in range(6)],
    )

    response, messages = asyncio.run(
        _run_homepage(monkeypatch, collection, enabled=True)
    )
    _, fields = _parse_marker(messages)

    assert len(response) == 8
    assert fields["fallback_ran"] == "1"
    assert fields["fallback_candidates"] == "6"
    assert float(fields["fallback_ms"]) >= 0


def test_logging_failure_does_not_change_successful_response(monkeypatch):
    local = [_article(i, local=True) for i in range(40)]
    uk = [_article(i + 100, local=False) for i in range(40)]
    baseline, _ = asyncio.run(
        _run_homepage(
            monkeypatch,
            FakeArticlesCollection(local=local, uk=uk),
            enabled=False,
        )
    )

    def fail_logging(_message):
        raise RuntimeError("diagnostic logger unavailable")

    instrumented, _ = asyncio.run(
        _run_homepage(
            monkeypatch,
            FakeArticlesCollection(local=local, uk=uk),
            enabled=True,
            logger=fail_logging,
        )
    )

    assert instrumented == baseline


def test_instrumentation_preserves_output_and_mongo_contract(monkeypatch):
    local = [_article(i, local=True) for i in range(40)]
    uk = [_article(i + 100, local=False) for i in range(40)]
    disabled_collection = FakeArticlesCollection(local=local, uk=uk)
    disabled_response, _ = asyncio.run(
        _run_homepage(monkeypatch, disabled_collection, enabled=False)
    )
    enabled_collection = FakeArticlesCollection(local=local, uk=uk)
    enabled_response, messages = asyncio.run(
        _run_homepage(monkeypatch, enabled_collection, enabled=True)
    )

    _parse_marker(messages)
    assert enabled_response == disabled_response
    assert enabled_collection.calls == disabled_collection.calls
