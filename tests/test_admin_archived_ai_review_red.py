"""Offline saved-review persistence contract; no application startup or clients.

Reuse the AST-isolation pattern from test_rss_excerpt.py: execute the production
endpoint body and both real lookup helpers, removing only startup decorators.
HTTP authentication/decorator integration is outside this focused regression.
"""

import asyncio
import ast
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import socket
from types import SimpleNamespace

from bson import ObjectId
from fastapi import Depends, HTTPException
from pymongo.results import UpdateResult
import pytest


SERVER = Path(__file__).resolve().parents[1] / "backend/server.py"
ARTICLE_ID = "11111111-1111-4111-8111-111111111111"
MONGO_ID = ObjectId("000000000000000000000001")
REVIEW = {
    "risk_level": "high",
    "recommended_action": "manual_review",
    "safe_to_keep_live": False,
    "editor_notes": "Synthetic source verification required.",
    "factual_concerns": ["Synthetic concern"],
}
STAMP = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)
SAVED_FIELDS = {
    "ai_review_status": "reviewed",
    "ai_review_checked_at": STAMP.isoformat(),
    "ai_review_model": "synthetic-review-model",
    "ai_review_result": REVIEW,
    "ai_review_risk_level": REVIEW["risk_level"],
    "ai_review_recommended_action": REVIEW["recommended_action"],
    "ai_review_safe_to_keep_live": REVIEW["safe_to_keep_live"],
}


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    attempts = []

    def forbidden(*_args, **_kwargs):
        attempts.append(True)
        raise AssertionError("Network forbidden in synthetic review tests")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    yield
    assert attempts == []


class Collection:
    """Strict, in-memory find/update fixture with real PyMongo result semantics."""

    def __init__(self, rows=()):
        self.rows = deepcopy(list(rows))
        self.reads = []
        self.writes = []
        self.failure = None

    async def find_one(self, query):
        assert set(query) in ({"id"}, {"_id"})
        self.reads.append(deepcopy(query))
        return next((deepcopy(row) for row in self.rows
                     if all(row.get(key) == value for key, value in query.items())), None)

    async def update_one(self, query, operation, *, upsert=False):
        assert upsert is False, "Reviews must not fabricate another article"
        assert set(query) in ({"id"}, {"_id"})
        assert set(operation) == {"$set"}
        assert set(operation["$set"]) == set(SAVED_FIELDS)
        if self.failure:
            raise self.failure
        matched = modified = 0
        for row in self.rows:
            if all(row.get(key) == value for key, value in query.items()):
                matched = 1
                before = deepcopy(row)
                row.update(deepcopy(operation["$set"]))
                modified = int(before != row)
                break
        self.writes.append({"query": deepcopy(query), "fields": deepcopy(operation["$set"]),
                            "matched": matched, "modified": modified})
        return UpdateResult({"n": matched, "nModified": modified, "ok": 1.0}, True)


def story(**changes):
    return {"_id": MONGO_ID, "id": ARTICLE_ID, "title": "Synthetic archived article",
            "content": "Synthetic unchanged article body.", "category": "Local News",
            **changes}


def runtime(active=(), archived=()):
    tree = ast.parse(SERVER.read_text())
    names = {"admin_ai_review_article", "_find_article_by_any_id",
             "_find_article_with_archive_provenance"}
    nodes = [node for node in tree.body
             if isinstance(node, ast.AsyncFunctionDef) and node.name in names]
    assert {node.name for node in nodes} == names
    assert len(nodes) == len(names), "Do not silently select an overridden definition"
    for node in nodes:
        node.decorator_list = []
    database = SimpleNamespace(articles=Collection(active), archived_articles=Collection(archived))
    reviews = []
    errors = []

    async def review(article):
        reviews.append(deepcopy(article))
        return deepcopy(REVIEW)

    def unused_auth():
        raise AssertionError("This endpoint-body test passes synthetic authorisation explicitly")

    namespace = {
        "db": database, "ObjectId": ObjectId, "Depends": Depends,
        "get_admin_auth": unused_auth, "HTTPException": HTTPException,
        "datetime": SimpleNamespace(now=lambda tz: STAMP), "timezone": timezone,
        "os": SimpleNamespace(environ={"OPENAI_REVIEW_MODEL": "synthetic-review-model"}),
        "logger": SimpleNamespace(error=lambda message: errors.append(message)),
        "run_openai_article_review": review,
    }
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SERVER), "exec"), namespace)
    return SimpleNamespace(db=database, reviews=reviews, errors=errors,
                           endpoint=namespace["admin_ai_review_article"])


@pytest.mark.parametrize("identifier", [ARTICLE_ID, str(MONGO_ID)])
def test_archive_only_review_cannot_report_success_without_persistence(identifier):
    original = story(archive_reason="admin_delete", archived_at="2026-11-16T12:00:00Z")
    current = runtime(archived=[original])
    result = asyncio.run(current.endpoint(identifier, authorized=True))

    # These precede the RED assertion: real lookup resolved the intended archive
    # record and the provider was mocked, not skipped because of broken setup.
    assert current.reviews == [original]
    assert current.db.archived_articles.reads
    assert current.errors == []
    assert current.db.articles.rows == []
    stored = current.db.archived_articles.rows[0]
    assert {key: stored[key] for key in original} == original
    persisted = all(stored.get(key) == value for key, value in SAVED_FIELDS.items())
    assert result.get("success") is not True or persisted, (
        "False saved-review success: active update matched counts="
        f"{[write['matched'] for write in current.db.articles.writes]}, "
        f"archive writes={len(current.db.archived_articles.writes)}; "
        "no saved review exists in either synthetic collection"
    )


@pytest.mark.parametrize("legacy_archived", [False, True])
def test_active_and_legacy_archive_records_preserve_successful_metadata_only_review(legacy_archived):
    original = story(archived=legacy_archived, force_live=False)
    unrelated = {**story(), "_id": ObjectId("000000000000000000000002"), "id": "unrelated"}
    current = runtime(active=[original, unrelated])
    result = asyncio.run(current.endpoint(ARTICLE_ID, authorized=True))

    assert result == {"success": True, "article_id": str(MONGO_ID),
                      "title": original["title"], "review": REVIEW}
    assert current.reviews == [original]
    assert current.db.articles.rows == [{**original, **SAVED_FIELDS}, unrelated]
    assert [(write["matched"], write["modified"]) for write in current.db.articles.writes] == [(1, 1)]
    assert current.db.archived_articles.writes == []
    assert current.errors == []


def test_already_identical_review_is_success_when_matched_but_not_modified():
    original = {**story(), **deepcopy(SAVED_FIELDS)}
    current = runtime(active=[original])
    result = asyncio.run(current.endpoint(ARTICLE_ID, authorized=True))
    assert result["success"] is True
    assert current.db.articles.rows == [original]
    assert [(write["matched"], write["modified"]) for write in current.db.articles.writes] == [(1, 0)]


def test_missing_article_remains_404_without_review_or_write():
    current = runtime()
    with pytest.raises(HTTPException) as caught:
        asyncio.run(current.endpoint(ARTICLE_ID, authorized=True))
    assert caught.value.status_code == 404
    assert current.reviews == []
    assert current.db.articles.writes == current.db.archived_articles.writes == []


def test_database_failure_cannot_report_success_or_modify_a_fixture():
    original = story()
    current = runtime(active=[original])
    current.db.articles.failure = RuntimeError("Synthetic persistence failure")
    with pytest.raises(HTTPException) as caught:
        asyncio.run(current.endpoint(ARTICLE_ID, authorized=True))
    assert caught.value.status_code == 500
    assert current.reviews == [original]
    assert current.db.articles.rows == [original]
    assert current.db.archived_articles.rows == []


def test_saved_review_route_keeps_admin_auth_dependency():
    node = next(node for node in ast.parse(SERVER.read_text()).body
                if isinstance(node, ast.AsyncFunctionDef) and node.name == "admin_ai_review_article")
    dependency = node.args.defaults[-1]
    assert isinstance(dependency, ast.Call) and isinstance(dependency.func, ast.Name)
    assert dependency.func.id == "Depends" and dependency.args[0].id == "get_admin_auth"
    assert any(isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute)
               and decorator.func.attr == "post"
               and decorator.args[0].value == "/admin/articles/{article_id}/ai-review"
               for decorator in node.decorator_list)
