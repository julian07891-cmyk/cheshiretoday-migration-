import asyncio
import os
import weakref
from copy import deepcopy
from types import SimpleNamespace


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


LONG_CONTENT = "Complete verified Cheshire reporting. " * 40
SHORT_CONTENT_PROJECTION = {
    "_id": 1,
    "content": 1,
    "summary": 1,
    "manual_review_hidden_from_public": 1,
    "verification_status": 1,
    "rewrite_status": 1,
    "manual_edited": 1,
    "manual_edit_protected": 1,
    "source": 1,
}


class TrackedArticle(dict):
    pass


class CleanupCursor:
    def __init__(self, collection, read_number, projection=None):
        self.collection = collection
        self.read_number = read_number
        self.projection = projection
        self.index = 0

    async def to_list(self, length):
        assert self.read_number == 1
        assert length is None
        records = [TrackedArticle(deepcopy(item)) for item in self.collection.records]
        self.collection.first_read_refs = [weakref.ref(item) for item in records]
        return records

    def __aiter__(self):
        assert self.read_number == 2
        self.collection.stage_one_iterated = True
        return self

    async def __anext__(self):
        if self.index >= len(self.collection.records):
            if self.collection.after_stage_one is not None:
                self.collection.after_stage_one(self.collection)
                self.collection.after_stage_one = None
            raise StopAsyncIteration

        source = self.collection.records[self.index]
        self.index += 1
        projected = TrackedArticle(
            {
                field: deepcopy(source[field])
                for field, included in self.projection.items()
                if included and field in source
            }
        )
        self.collection.stage_one_refs.append(weakref.ref(projected))
        return projected


class CleanupArticles:
    def __init__(
        self,
        records,
        events,
        *,
        after_stage_one=None,
        delete_count=1,
    ):
        self.records = deepcopy(records)
        self.events = events
        self.find_calls = 0
        self.find_one_calls = []
        self.deleted_ids = []
        self._first_read_refs = []
        self.stage_one_refs = []
        self.stage_one_projection = None
        self.stage_one_iterated = False
        self.after_stage_one = after_stage_one
        self.delete_count = delete_count

    @property
    def first_read_refs(self):
        return self._first_read_refs

    @first_read_refs.setter
    def first_read_refs(self, value):
        self._first_read_refs = value

    def find(self, query, projection=None):
        assert query == {}
        self.find_calls += 1
        if self.find_calls == 1:
            assert projection is None
        elif self.find_calls == 2:
            self.stage_one_projection = projection
            assert projection is not None
        else:
            raise AssertionError("cleanup must perform exactly two collection scans")
        return CleanupCursor(self, self.find_calls, projection)

    async def find_one(self, query):
        assert set(query) == {"_id"}
        assert all(ref() is None for ref in self.first_read_refs)
        assert all(ref() is None for ref in self.stage_one_refs)
        self.find_one_calls.append(query["_id"])
        return next(
            (
                deepcopy(item)
                for item in self.records
                if item.get("_id") == query["_id"]
            ),
            None,
        )

    async def delete_one(self, query):
        article_id = query["_id"]
        self.events.append(("delete", article_id))
        self.deleted_ids.append(article_id)
        if self.delete_count == 1:
            self.records = [item for item in self.records if item["_id"] != article_id]
        return SimpleNamespace(deleted_count=self.delete_count)

    async def count_documents(self, query):
        assert query == {}
        return len(self.records)


class CleanupArchive:
    def __init__(self, events, *, fail=False):
        self.events = events
        self.inserted = []
        self.fail = fail

    async def insert_one(self, article):
        if self.fail:
            raise RuntimeError("archive unavailable")
        self.events.append(("archive", article.get("title")))
        self.inserted.append(deepcopy(article))
        return SimpleNamespace(inserted_id=f"archive-{len(self.inserted)}")


def article(article_id, title, **values):
    record = {
        "_id": article_id,
        "title": title,
        "source_url": "",
        "content": LONG_CONTENT,
        "summary": "Complete summary",
        "publishedDate": "2026-08-07T06:00:00+00:00",
    }
    record.update(values)
    return record


def run_cleanup(
    monkeypatch,
    records,
    *,
    after_stage_one=None,
    archive_fails=False,
    delete_count=1,
):
    events = []
    articles = CleanupArticles(
        records,
        events,
        after_stage_one=after_stage_one,
        delete_count=delete_count,
    )
    archive = CleanupArchive(events, fail=archive_fails)
    monkeypatch.setattr(
        server,
        "db",
        SimpleNamespace(articles=articles, archived_articles=archive),
    )
    result = asyncio.run(server._remove_duplicates_internal())
    return result, articles, archive


def test_duplicate_source_url_keeps_best_and_archives_before_delete(monkeypatch):
    records = [
        article(
            "older",
            "Older wording",
            source_url=" HTTPS://publisher.test/story ",
            publishedDate="2026-08-06T06:00:00+00:00",
        ),
        article(
            "newer",
            "Newer wording",
            source_url="https://publisher.test/story",
            publishedDate="2026-08-07T06:00:00+00:00",
        ),
    ]

    result, active, archive = run_cleanup(monkeypatch, records)

    assert [item["_id"] for item in active.records] == ["newer"]
    assert active.deleted_ids == ["older"]
    assert active.events == [("archive", "Older wording"), ("delete", "older")]
    assert archive.inserted[0]["title"] == "Older wording"
    assert archive.inserted[0]["archive_reason"] == "duplicate"
    assert result["duplicates_removed"] == 1
    assert result["short_articles_removed"] == 0


def test_duplicate_title_fallback_remains_case_insensitive(monkeypatch):
    records = [
        article(
            "shorter",
            "Same Cheshire Story",
            content="Verified reporting. " * 70,
        ),
        article(
            "longer",
            "same cheshire story",
            content="Verified detailed reporting. " * 80,
        ),
    ]

    result, active, archive = run_cleanup(monkeypatch, records)

    assert [item["_id"] for item in active.records] == ["longer"]
    assert archive.inserted[0]["archive_reason"] == "duplicate"
    assert result["duplicates_removed"] == 1


def test_protected_record_wins_duplicate_keep_score(monkeypatch):
    records = [
        article(
            "protected",
            "Protected story",
            source_url="https://publisher.test/protected",
            manual_edit_protected=True,
            publishedDate="2026-08-01T06:00:00+00:00",
        ),
        article(
            "forced",
            "Forced story",
            source_url="https://publisher.test/protected",
            force_live=True,
            content="Newer and longer reporting. " * 100,
        ),
    ]

    result, active, archive = run_cleanup(monkeypatch, records)

    assert [item["_id"] for item in active.records] == ["protected"]
    assert archive.inserted[0]["title"] == "Forced story"
    assert result["duplicates_removed"] == 1


def test_second_pass_removes_short_content_but_preserves_manual_review(monkeypatch):
    records = [
        article("short", "Short public story", content="Too short", summary="Brief"),
        article(
            "review",
            "Short Manual Review story",
            content="Too short",
            summary="Brief",
            manual_review_hidden_from_public=True,
            verification_status="needs_manual_review",
            rewrite_status="manual_review_required",
        ),
    ]

    result, active, archive = run_cleanup(monkeypatch, records)

    assert [item["_id"] for item in active.records] == ["review"]
    assert active.deleted_ids == ["short"]
    assert archive.inserted[0]["title"] == "Short public story"
    assert archive.inserted[0]["archive_reason"] == "short_content"
    assert result == {
        "success": True,
        "duplicates_removed": 0,
        "short_articles_removed": 1,
        "total_removed": 1,
        "remaining_articles": 1,
    }


def test_first_pass_articles_are_unreachable_before_second_materialisation(monkeypatch):
    result, active, archive = run_cleanup(
        monkeypatch,
        [article("kept", "Unique complete story")],
    )

    assert result["success"] is True
    assert active.find_calls == 2
    assert archive.inserted == []
    assert result["total_removed"] == 0


def test_second_pass_streams_exact_projection_without_full_fetch_for_non_candidate(
    monkeypatch,
):
    result, active, archive = run_cleanup(
        monkeypatch,
        [article("kept", "Complete public story")],
    )

    assert result["success"] is True
    assert active.stage_one_projection == SHORT_CONTENT_PROJECTION
    assert active.stage_one_iterated is True
    assert active.find_calls == 2
    assert active.find_one_calls == []
    assert archive.inserted == []


def test_qualifying_candidate_fetches_once_and_archives_complete_latest_document(
    monkeypatch,
):
    record = article(
        "short",
        "Short public story",
        content="Too short",
        summary="Brief",
        image="https://images.test/story.jpg",
        image_metadata={"credit": "Publisher", "dimensions": [1200, 800]},
        source="Local Publisher",
        source_metadata={"feed": "cheshire", "rank": 3},
        social_state={"facebook": {"prepared": True}},
        analytics={"views": 17, "channels": ["direct"]},
        legacy_field="preserve-me",
        arbitrary_nested={"level": {"value": [1, 2, 3]}},
    )

    result, active, archive = run_cleanup(monkeypatch, [record])

    assert result["short_articles_removed"] == 1
    assert active.find_one_calls == ["short"]
    assert active.events == [("archive", "Short public story"), ("delete", "short")]
    archived = archive.inserted[0]
    expected = deepcopy(record)
    expected.pop("_id")
    expected["archive_reason"] = "short_content"
    expected["archived_at"] = archived["archived_at"]
    assert archived == expected


def test_revalidation_skips_article_that_becomes_manual_review_hidden(monkeypatch):
    def hide_for_review(collection):
        collection.records[0]["manual_review_hidden_from_public"] = True

    result, active, archive = run_cleanup(
        monkeypatch,
        [article("short", "Short story", content="Short", summary="Brief")],
        after_stage_one=hide_for_review,
    )

    assert active.find_one_calls == ["short"]
    assert active.deleted_ids == []
    assert archive.inserted == []
    assert result["short_articles_removed"] == 0


def test_revalidation_skips_article_that_becomes_owner_protected(monkeypatch):
    def protect_article(collection):
        collection.records[0]["manual_edit_protected"] = True

    result, active, archive = run_cleanup(
        monkeypatch,
        [article("short", "Short story", content="Short", summary="Brief")],
        after_stage_one=protect_article,
    )

    assert active.find_one_calls == ["short"]
    assert active.deleted_ids == []
    assert archive.inserted == []
    assert result["short_articles_removed"] == 0


def test_revalidation_skips_article_whose_content_becomes_complete(monkeypatch):
    def complete_article(collection):
        collection.records[0]["content"] = LONG_CONTENT

    result, active, archive = run_cleanup(
        monkeypatch,
        [article("short", "Short story", content="Short", summary="Brief")],
        after_stage_one=complete_article,
    )

    assert active.find_one_calls == ["short"]
    assert active.deleted_ids == []
    assert archive.inserted == []
    assert result["short_articles_removed"] == 0


def test_revalidation_archives_latest_still_short_document(monkeypatch):
    def update_article(collection):
        collection.records[0]["title"] = "Updated short title"
        collection.records[0]["legacy_state"] = {"revision": 2}

    result, active, archive = run_cleanup(
        monkeypatch,
        [article("short", "Original title", content="Short", summary="Brief")],
        after_stage_one=update_article,
    )

    assert result["short_articles_removed"] == 1
    assert active.events == [("archive", "Updated short title"), ("delete", "short")]
    assert archive.inserted[0]["title"] == "Updated short title"
    assert archive.inserted[0]["legacy_state"] == {"revision": 2}


def test_missing_candidate_between_stages_is_skipped_safely(monkeypatch):
    def remove_candidate(collection):
        collection.records = []

    result, active, archive = run_cleanup(
        monkeypatch,
        [article("short", "Short story", content="Short", summary="Brief")],
        after_stage_one=remove_candidate,
    )

    assert active.find_one_calls == ["short"]
    assert active.deleted_ids == []
    assert archive.inserted == []
    assert result["short_articles_removed"] == 0


def test_archive_failure_preserves_active_article_and_does_not_count(monkeypatch):
    result, active, archive = run_cleanup(
        monkeypatch,
        [article("short", "Short story", content="Short", summary="Brief")],
        archive_fails=True,
    )

    assert [item["_id"] for item in active.records] == ["short"]
    assert active.deleted_ids == []
    assert archive.inserted == []
    assert result["short_articles_removed"] == 0


def test_delete_noop_does_not_increment_short_removed(monkeypatch):
    result, active, archive = run_cleanup(
        monkeypatch,
        [article("short", "Short story", content="Short", summary="Brief")],
        delete_count=0,
    )

    assert active.events == [("archive", "Short story"), ("delete", "short")]
    assert [item["_id"] for item in active.records] == ["short"]
    assert len(archive.inserted) == 1
    assert result["short_articles_removed"] == 0
