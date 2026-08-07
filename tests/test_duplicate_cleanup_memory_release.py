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


class TrackedArticle(dict):
    pass


class CleanupCursor:
    def __init__(self, collection, read_number):
        self.collection = collection
        self.read_number = read_number

    async def to_list(self, length):
        assert length is None
        if self.read_number == 2 and self.collection.first_read_refs:
            assert all(ref() is None for ref in self.collection.first_read_refs)

        records = [TrackedArticle(deepcopy(item)) for item in self.collection.records]
        if self.read_number == 1:
            self.collection.first_read_refs = [weakref.ref(item) for item in records]
        return records


class CleanupArticles:
    def __init__(self, records, events):
        self.records = deepcopy(records)
        self.events = events
        self.find_calls = 0
        self.deleted_ids = []
        self._first_read_refs = []

    @property
    def first_read_refs(self):
        return self._first_read_refs

    @first_read_refs.setter
    def first_read_refs(self, value):
        self._first_read_refs = value

    def find(self, query):
        assert query == {}
        self.find_calls += 1
        return CleanupCursor(self, self.find_calls)

    async def delete_one(self, query):
        article_id = query["_id"]
        self.events.append(("delete", article_id))
        self.deleted_ids.append(article_id)
        self.records = [item for item in self.records if item["_id"] != article_id]
        return SimpleNamespace(deleted_count=1)

    async def count_documents(self, query):
        assert query == {}
        return len(self.records)


class CleanupArchive:
    def __init__(self, events):
        self.events = events
        self.inserted = []

    async def insert_one(self, article):
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


def run_cleanup(monkeypatch, records):
    events = []
    articles = CleanupArticles(records, events)
    archive = CleanupArchive(events)
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
