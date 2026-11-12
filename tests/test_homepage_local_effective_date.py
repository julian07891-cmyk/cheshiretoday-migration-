"""Offline contracts for the exact homepage's bounded Local candidate query.

The strict fake checks the Mongo pipeline and models its result independently.
It is not a Mongo query-plan, latency or production-memory benchmark.
"""

import asyncio
import ast
import copy
import socket
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import ExecutionTimeout, OperationFailure

from tests.test_public_hub_route_alignment import (
    LocalChronologyCollection,
    LocalChronologyCursor,
    _be_date,
    _local_bson_key,
    _local_matches,
    _local_story,
    server,
)


BASELINE = "73cdf41652421dab946004302586bb09c779b11a"
ROOT = Path(__file__).resolve().parents[1]
KEY = "_homepage_local_effective_date"
PROJECTION = {
    "_id": 1, "title": 1, "summary": 1, "category": 1,
    "author": 1, "publishedDate": 1, "created_at": 1, "image": 1,
    "tags": 1, "featured": 1, "source": 1, "source_url": 1,
    "scope": 1, "is_local_source": 1, "location": 1, "priority_location": 1,
}


def expected_date(field):
    return {"$switch": {"branches": [
        {"case": {"$eq": [{"$type": field}, "date"]}, "then": field},
        {"case": {"$eq": [{"$type": field}, "string"]},
         "then": {"$convert": {"input": field, "to": "date",
                                "onError": None, "onNull": None}}},
    ], "default": None}}


class CandidateCursor(LocalChronologyCursor):
    def batch_size(self, size):
        assert size == 100
        self.read["batch_size"] = size
        return self


class LegacyCursor(LocalChronologyCursor):
    def sort(self, fields):
        def key(value):
            if isinstance(value, bool):
                return (8, value)
            if isinstance(value, dict):
                assert value == {}  # Only the explicitly modelled malformed fixture.
                return (4, ())
            return _local_bson_key(value)

        self.read["sort"] = copy.deepcopy(fields)
        for name, direction in reversed(fields):
            self.documents.sort(key=lambda item: key(item.get(name)), reverse=direction == -1)
        return self


class CandidateCollection(LocalChronologyCollection):
    def __init__(self, documents):
        super().__init__(documents)
        self.candidate_reads = []
        self.failure = None

    def find(self, query, projection=None):
        cursor = super().find(query, projection)
        return LegacyCursor(cursor.documents, projection, cursor.read)

    def aggregate(self, pipeline, **kwargs):
        # No permissive catch-all evaluator: reject any extra stage or work.
        assert len(pipeline) == 6
        query = pipeline[0]["$match"]
        assert query == {"$and": [
            {"is_local_source": True},
            {"$or": [{"archived": {"$exists": False}}, {"archived": False}]},
            {"manual_review_hidden_from_public": {"$ne": True}},
        ]}
        assert pipeline[1:] == [
            {"$project": PROJECTION},
            {"$set": {KEY: {"$ifNull": [expected_date("$created_at"),
                                          expected_date("$publishedDate")]}}},
            {"$sort": {KEY: -1, "_id": 1}},
            {"$limit": 100},
            {"$project": PROJECTION},
        ]
        assert kwargs == {"maxTimeMS": 2000, "allowDiskUse": False}
        read = {"pipeline": copy.deepcopy(pipeline), **kwargs}
        self.candidate_reads.append(read)
        if self.failure:
            raise self.failure
        documents = [item for item in self.documents if _local_matches(item, query)]
        documents.sort(key=lambda item: item["_id"])
        documents.sort(
            key=lambda item: (_be_date(item.get("created_at"))
                              or _be_date(item.get("publishedDate"))
                              or datetime.min.replace(tzinfo=timezone.utc)),
            reverse=True,
        )
        selected = documents[:100]
        read["selected_ids"] = [item["_id"] for item in selected]
        cursor = CandidateCursor(selected, PROJECTION, read)
        cursor.cap = 100
        return cursor


@pytest.fixture
def install(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Network forbidden in homepage effective-date tests")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setenv("UK_FILTER_NOISE", "1")

    def configure(documents):
        collection = CandidateCollection(documents)
        monkeypatch.setattr(server.db, "articles", collection)
        return collection

    return configure


def homepage():
    return asyncio.run(server.get_articles(limit=80))


def selected(collection):
    assert len(collection.candidate_reads) == 1, "Homepage must use effective-date aggregation"
    read = collection.candidate_reads[0]
    assert read["batch_size"] == read["to_list"] == 100
    assert read["returned"] <= 100
    assert read["body_documents"] == 0
    return read["selected_ids"]


@pytest.mark.parametrize("created,published,effective", [
    ("2026-11-12T10:00:00Z", "2026-11-01T12:00:00Z", "2026-11-12T10:00:00Z"),
    ("2026-11-12T12:00:00+0200", "2026-11-01T12:00:00Z", "2026-11-12T10:00:00Z"),
    (datetime(2026, 11, 12, 10), "2026-11-01T12:00:00Z", "2026-11-12T10:00:00Z"),
    (datetime(2026, 11, 12, 12, tzinfo=timezone(timedelta(hours=2))), None,
     "2026-11-12T10:00:00Z"),
    (None, "2026-11-12T10:00:00+0000", "2026-11-12T10:00:00Z"),
    ("not-a-date", "2026-11-12T10:00:00Z", "2026-11-12T10:00:00Z"),
    ("", datetime(2026, 11, 12, 10), "2026-11-12T10:00:00Z"),
    (17, "2026-11-12T10:00:00Z", "2026-11-12T10:00:00Z"),
    (True, "2026-11-12T10:00:00Z", "2026-11-12T10:00:00Z"),
    ({}, "2026-11-12T10:00:00Z", "2026-11-12T10:00:00Z"),
    ("2026-10-01T10:00:00Z", "2026-11-12T10:00:00Z", "2026-10-01T10:00:00Z"),
    (None, "invalid", None),
    ("invalid", 42, None),
    (None, None, None),
])
def test_date_normalisation_before_cap(install, created, published, effective):
    target = _local_story(1000, published, created_at=created)
    boundary = _be_date(effective) or datetime(2026, 1, 1, tzinfo=timezone.utc)
    old = [_local_story(i + 1, boundary - timedelta(seconds=i + 1),
                        created_at=boundary - timedelta(seconds=i + 1)) for i in range(100)]
    collection = install([*old, target])
    before = copy.deepcopy(collection.documents)
    response = homepage()
    assert (target["_id"] in selected(collection)) is (effective is not None)
    assert collection.documents == before
    assert all(KEY not in item and "content" not in item for item in response)


def test_missing_creation_falls_back_and_ties_use_ascending_id(install):
    moment = "2026-11-12T10:00:00Z"
    documents = [_local_story(i, moment) for i in range(105, 0, -1)]
    collection = install(documents)
    homepage()
    assert selected(collection) == [ObjectId(f"{i:024x}") for i in range(1, 101)]


def test_equal_instants_across_bson_and_iso_dates_use_id_ties(install):
    documents = [
        _local_story(3, None, created_at="2026-11-12T12:00:00+0200"),
        _local_story(2, None, created_at=datetime(2026, 11, 12, 10)),
        _local_story(1, "2026-11-12T10:00:00+0000"),
    ]
    collection = install(documents)
    homepage()
    assert selected(collection) == [ObjectId(f"{i:024x}") for i in (1, 2, 3)]


def test_missing_publication_and_creation_sort_last_without_rewriting(install):
    undated = _local_story(1, None)
    del undated["publishedDate"]
    dated = _local_story(2, "2026-11-12T10:00:00Z")
    collection = install([undated, dated])
    before = copy.deepcopy(collection.documents)
    homepage()
    assert selected(collection) == [dated["_id"], undated["_id"]]
    assert collection.documents == before


# Public article metadata captured in the preceding authorised read-only diagnosis.
# These rows reproduce date defects, not full production content or a fresh live ranking.
MISSING = [
    ("6af4adb70812ba809f33afcc", "2026-11-11T14:19:00+0000", 249),
    ("6af35c365fb0a2a6c96d4d43", "2026-11-10T16:00:00+0000", 251),
    ("6af35c3d5fb0a2a6c96d4d45", "2026-11-10T13:27:00+0000", 252),
    ("6af2b34b514d46f9776d1c9a", "2026-11-10T06:00:00+0000", 253),
    ("6af161e0514d46f9776d0b37", "2026-11-09T06:00:00+0000", 254),
    ("6aee161e514d46f9776ce2b3", "2026-11-06T16:51:00+0000", 256),
    ("6aee1623514d46f9776ce2b4", "2026-11-06T15:30:00+0000", 257),
    ("6aee1629514d46f9776ce2b6", "2026-11-06T14:35:00+0000", 258),
    ("6aec1c0ba1c3522d784a1a30", "2026-11-04T16:40:00+0000", 259),
    ("6aec1c13a1c3522d784a1a32", "2026-11-04T14:38:00+0000", 260),
]


@pytest.mark.parametrize("identifier,published,raw_position", MISSING)
def test_diagnosed_ids_available_when_effective_date_in_top_100(
    install, identifier, published, raw_position,
):
    target = _local_story(1000, published, _id=ObjectId(identifier))
    earlier = _be_date(published) - timedelta(days=1)
    documents = [*[_local_story(i + 1, earlier, created_at=earlier)
                   for i in range(raw_position - 1)], target]
    collection = install(documents)
    legacy = asyncio.run(collection.find(
        {"is_local_source": True}, PROJECTION,
    ).sort([("created_at", -1), ("publishedDate", -1)]).limit(100).to_list(100))
    assert target["_id"] not in [item["_id"] for item in legacy]
    homepage()
    assert selected(collection)[0] == target["_id"]


def test_fallback_does_not_guarantee_selection_beyond_boundary(install):
    moment = datetime(2026, 11, 12, tzinfo=timezone.utc)
    target = _local_story(1000, moment - timedelta(days=1))
    collection = install([target, *[_local_story(i + 1, moment, created_at=moment)
                                   for i in range(100)]])
    homepage()
    assert target["_id"] not in selected(collection)


def test_visibility_editorial_force_live_and_response_contracts(install):
    moment = "2026-11-12T10:00:00Z"
    good = _local_story(1, moment)
    archived = _local_story(2, moment, archived=True)
    hidden = _local_story(3, moment, manual_review_hidden_from_public=True)
    podcast = _local_story(4, moment, title="Podcast: Cheshire civic information")
    forced = _local_story(5, moment, force_live=True)
    collection = install([good, archived, hidden, podcast, forced])
    response = homepage()
    identifiers = {item["id"] for item in response}
    assert str(good["_id"]) in identifiers
    assert str(forced["_id"]) in identifiers
    assert not {str(item["_id"]) for item in (archived, hidden, podcast)} & identifiers
    assert set(selected(collection)) == {good["_id"], podcast["_id"], forced["_id"]}
    assert all(KEY not in item and "content" not in item for item in response)
    # Existing force-live and UK find branches retain their projections/caps/sort.
    assert collection.reads[0]["limit"] == collection.reads[0]["to_list"] == 400
    assert collection.reads[1]["limit"] == collection.reads[1]["to_list"] == 100
    assert collection.reads[1]["sort"] == [("created_at", -1), ("publishedDate", -1)]


@pytest.mark.parametrize("failure", [ExecutionTimeout("synthetic"), OperationFailure("synthetic")])
def test_sort_failure_does_not_retry_or_return_partial_feed(install, failure):
    collection = install([])
    collection.failure = failure
    with pytest.raises(HTTPException) as caught:
        homepage()
    assert caught.value.status_code == 500
    assert len(collection.candidate_reads) == 1
    assert len(collection.reads) == 1  # Only the unchanged force-live read preceded it.


def test_unrelated_code_and_frontend_unchanged_from_production():
    path = "backend/server.py"
    before = ast.parse(subprocess.check_output(
        ["git", "show", f"{BASELINE}:{path}"], cwd=ROOT, text=True,
    ))
    after = ast.parse((ROOT / path).read_text())

    def normalise(tree):
        handler = next(node for node in tree.body
                       if isinstance(node, ast.AsyncFunctionDef) and node.name == "get_articles")
        # Remove precisely the permitted Local retrieval statements. All query
        # construction, eligibility, allocation, fallback and shaping stay compared.
        for node in ast.walk(handler):
            if not isinstance(node, ast.If) or not ast.unparse(node.test).startswith("(not category or category == 'all')"):
                continue
            first = next(i for i, item in enumerate(node.body)
                         if isinstance(item, ast.Assign) and ast.unparse(item.targets[0]) == "local_candidate_limit")
            end = next(i for i in range(first + 1, len(node.body))
                       if isinstance(node.body[i], ast.If) and ast.unparse(node.body[i].test) == "homepage_timing_enabled")
            node.body[first + 1:end] = []
        return ast.dump(tree, include_attributes=False)

    assert normalise(after) == normalise(before)
    for path in ("frontend/src/pages/HomePageV1.jsx", "frontend/src/pages/HomePageV1.test.jsx",
                 "backend/app/public_article_eligibility.py"):
        assert (ROOT / path).read_bytes() == subprocess.check_output(
            ["git", "show", f"{BASELINE}:{path}"], cwd=ROOT,
        )
