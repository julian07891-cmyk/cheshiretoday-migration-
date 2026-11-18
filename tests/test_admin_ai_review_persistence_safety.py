"""Focused persistence safety using the established offline production-body fixture."""

import asyncio
from copy import deepcopy

from bson import ObjectId
from fastapi import HTTPException
from pymongo.results import UpdateResult
import pytest

from tests.test_admin_archived_ai_review_red import (
    ARTICLE_ID, REVIEW, SAVED_FIELDS, offline, runtime, story,
)


def configure(origin):
    original = story(archived_at="2026-11-16T12:00:00Z", archive_reason="admin_delete")
    current = runtime(**({"active": [original]} if origin == "articles" else {"archived": [original]}))
    selected = getattr(current.db, origin)
    other = current.db.archived_articles if origin == "articles" else current.db.articles
    return current, selected, other, original


@pytest.mark.parametrize("origin", ["articles", "archived_articles"])
def test_unacknowledged_write_cannot_report_confirmed_persistence(monkeypatch, origin):
    current, selected, other, original = configure(origin)
    update = selected.update_one

    async def unacknowledged(*args, **kwargs):
        await update(*args, **kwargs)
        return UpdateResult({"n": 1, "nModified": 1}, False)

    monkeypatch.setattr(selected, "update_one", unacknowledged)
    with pytest.raises(HTTPException) as caught:
        asyncio.run(current.endpoint(ARTICLE_ID, authorized=True))
    assert caught.value.status_code == 500
    assert caught.value.detail == "Could not confirm AI review persistence"
    assert current.reviews == [original]
    assert current.errors == []  # Do not read an unacknowledged result's matched count.
    assert len(selected.writes) == 1
    assert other.writes == []
    # This fixture applied the write before losing acknowledgement: failure is
    # not a claim that Mongo rolled back or that retry would be harmless.
    assert selected.rows == [{**original, **SAVED_FIELDS}]


@pytest.mark.parametrize("origin", ["articles", "archived_articles"])
@pytest.mark.parametrize("loss", ["deleted", "moved"])
def test_target_loss_during_review_fails_without_upsert_or_cross_collection_fallback(monkeypatch, origin, loss):
    current, selected, other, original = configure(origin)
    review = current.endpoint.__globals__["run_openai_article_review"]

    async def target_lost(article):
        result = await review(article)
        if loss == "moved":
            other.rows.extend(deepcopy(selected.rows))
        selected.rows.clear()
        return result

    monkeypatch.setitem(current.endpoint.__globals__, "run_openai_article_review", target_lost)
    with pytest.raises(HTTPException) as caught:
        asyncio.run(current.endpoint(ARTICLE_ID, authorized=True))
    assert caught.value.status_code == 404
    assert caught.value.detail == "Article not found"
    assert current.reviews == [original]
    assert selected.rows == []
    assert [(write["matched"], write["modified"]) for write in selected.writes] == [(0, 0)]
    assert other.rows == ([original] if loss == "moved" else [])
    assert other.writes == []
    assert current.errors == []


@pytest.mark.parametrize("archive_id_requested", [False, True])
def test_existing_identity_precedence_selects_only_the_resolved_record(archive_id_requested):
    active = story(title="Synthetic active identity")
    archived = story(_id=ObjectId("000000000000000000000002"), title="Synthetic archived identity")
    current = runtime(active=[active], archived=[archived])
    identifier = str(archived["_id"]) if archive_id_requested else ARTICLE_ID
    result = asyncio.run(current.endpoint(identifier, authorized=True))
    expected = archived if archive_id_requested else active
    assert result == {"success": True, "article_id": str(expected["_id"]),
                      "title": expected["title"], "review": REVIEW}
    assert current.reviews == [expected]
    assert current.db.articles.rows == ([active] if archive_id_requested else [{**active, **SAVED_FIELDS}])
    assert current.db.archived_articles.rows == ([{**archived, **SAVED_FIELDS}] if archive_id_requested else [archived])
    assert len(current.db.articles.writes) == int(not archive_id_requested)
    assert len(current.db.archived_articles.writes) == int(archive_id_requested)


def test_uuid_only_archive_record_retains_its_existing_identity_and_lifecycle():
    original = story(archived=True, force_live=False)
    original.pop("_id")
    current = runtime(archived=[original])
    result = asyncio.run(current.endpoint(ARTICLE_ID, authorized=True))
    assert result["success"] is True
    assert result["article_id"] == ARTICLE_ID
    assert current.db.archived_articles.rows == [{**original, **SAVED_FIELDS}]
    assert current.db.archived_articles.writes[0]["query"] == {"id": ARTICLE_ID}
    assert current.db.articles.rows == current.db.articles.writes == []


def test_identical_archive_review_remains_successful_without_a_modification():
    original = {**story(archived=True), **deepcopy(SAVED_FIELDS)}
    current = runtime(archived=[original])
    result = asyncio.run(current.endpoint(ARTICLE_ID, authorized=True))
    assert result["success"] is True
    assert current.db.archived_articles.rows == [original]
    assert [(write["matched"], write["modified"]) for write in current.db.archived_articles.writes] == [(1, 0)]
    assert current.db.articles.writes == []


def test_archive_database_failure_retains_existing_error_behaviour():
    current, selected, other, original = configure("archived_articles")
    selected.failure = RuntimeError("Synthetic persistence failure")
    with pytest.raises(HTTPException) as caught:
        asyncio.run(current.endpoint(ARTICLE_ID, authorized=True))
    assert caught.value.status_code == 500
    assert caught.value.detail == "Synthetic persistence failure"
    assert current.reviews == [original]
    assert selected.rows == [original]
    assert selected.writes == other.writes == []
    assert len(current.errors) == 1


def test_cancellation_during_archive_update_remains_observable(monkeypatch):
    current, selected, other, original = configure("archived_articles")

    async def cancelled(*args, **kwargs):
        raise asyncio.CancelledError()

    monkeypatch.setattr(selected, "update_one", cancelled)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(current.endpoint(ARTICLE_ID, authorized=True))
    assert current.reviews == [original]
    assert selected.rows == [original]
    assert selected.writes == other.writes == []
    assert current.errors == []
