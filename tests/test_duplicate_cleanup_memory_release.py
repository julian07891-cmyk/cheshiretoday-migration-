import asyncio
import os
import weakref
from copy import deepcopy
from types import SimpleNamespace

import pytest


os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server


LONG_CONTENT = "Complete verified Cheshire reporting. " * 40
DUPLICATE_PROJECTION = {
    "_id": 1,
    "title": 1,
    "source_url": 1,
    "manual_edit_protected": 1,
    "manual_edited": 1,
    "force_live": 1,
    "manual_edited_at": 1,
    "updated_at": 1,
    "created_at": 1,
    "publishedDate": 1,
    "content": 1,
}
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
BOILERPLATE_MARKERS = [
    "this story has been reported by",
    "more details are expected to emerge soon",
    "for the latest news from across the region, keep following",
]


class TrackedArticle(dict):
    pass


class TrackedContent(str):
    pass


class NoFullBlobJoinText(str):
    def __deepcopy__(self, _memo):
        return self

    def strip(self):
        return self

    def __add__(self, _other):
        raise AssertionError("short-content assessment must not build a full joined blob")


class CleanupCursor:
    def __init__(self, collection, read_number, projection=None):
        self.collection = collection
        self.read_number = read_number
        self.projection = projection
        self.index = 0

    async def to_list(self, _length):
        raise AssertionError("cleanup collection scans must stream asynchronously")

    def __aiter__(self):
        if self.read_number == 1:
            self.collection.duplicate_scan_iterated = True
        else:
            self.collection.short_scan_iterated = True
        return self

    async def __anext__(self):
        if self.index >= len(self.collection.records):
            if self.read_number == 1 and self.collection.after_duplicate_scan:
                self.collection.after_duplicate_scan(self.collection)
                self.collection.after_duplicate_scan = None
            elif self.read_number == 2 and self.collection.after_short_scan:
                self.collection.after_short_scan(self.collection)
                self.collection.after_short_scan = None
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
        refs = (
            self.collection.duplicate_scan_refs
            if self.read_number == 1
            else self.collection.short_scan_refs
        )
        refs.append(weakref.ref(projected))
        projected_content = projected.get("content")
        if isinstance(projected_content, TrackedContent):
            self.collection.projected_content_refs.append(
                weakref.ref(projected_content)
            )
        return projected


class CleanupArticles:
    def __init__(
        self,
        records,
        events,
        *,
        after_duplicate_scan=None,
        after_short_scan=None,
        delete_count=1,
        delete_raises=False,
    ):
        self.records = deepcopy(records)
        self.events = events
        self.find_calls = 0
        self.find_one_calls = []
        self.deleted_ids = []
        self.duplicate_scan_refs = []
        self.short_scan_refs = []
        self.projected_content_refs = []
        self.duplicate_projection = None
        self.short_projection = None
        self.duplicate_scan_iterated = False
        self.short_scan_iterated = False
        self.after_duplicate_scan = after_duplicate_scan
        self.after_short_scan = after_short_scan
        self.delete_count = delete_count
        self.delete_raises = delete_raises

    def find(self, query, projection=None):
        assert query == {}
        self.find_calls += 1
        if self.find_calls == 1:
            self.duplicate_projection = projection
            assert projection is not None
        elif self.find_calls == 2:
            assert all(ref() is None for ref in self.duplicate_scan_refs)
            assert all(ref() is None for ref in self.projected_content_refs)
            self.short_projection = projection
            assert projection is not None
        else:
            raise AssertionError("cleanup must perform exactly two collection scans")
        return CleanupCursor(self, self.find_calls, projection)

    async def find_one(self, query):
        assert set(query) == {"_id"}
        assert all(ref() is None for ref in self.duplicate_scan_refs)
        assert all(ref() is None for ref in self.short_scan_refs)
        assert all(ref() is None for ref in self.projected_content_refs)
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
        if self.delete_raises:
            raise RuntimeError("delete unavailable")
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
    after_duplicate_scan=None,
    after_short_scan=None,
    archive_fails=False,
    delete_count=1,
    delete_raises=False,
):
    events = []
    articles = CleanupArticles(
        records,
        events,
        after_duplicate_scan=after_duplicate_scan,
        after_short_scan=after_short_scan,
        delete_count=delete_count,
        delete_raises=delete_raises,
    )
    archive = CleanupArchive(events, fail=archive_fails)
    monkeypatch.setattr(
        server,
        "db",
        SimpleNamespace(articles=articles, archived_articles=archive),
    )
    result = asyncio.run(server._remove_duplicates_internal())
    return result, articles, archive


def old_short_content_assessment(article_record):
    content = (article_record.get("content") or "").strip()
    summary = (article_record.get("summary") or "").strip()
    text_blob = (content + " " + summary).strip()
    blob_len = len(text_blob)
    text_l = text_blob.lower()
    return (
        blob_len
        if blob_len < 1000 or any(marker in text_l for marker in BOILERPLATE_MARKERS)
        else None
    )


def assert_short_content_matches_old_assessment(monkeypatch, content, summary):
    record = article("candidate", "Qualification candidate", content=content, summary=summary)
    expected = old_short_content_assessment(record)

    result, active, archive = run_cleanup(monkeypatch, [record])

    assert result["success"] is True
    assert result["short_articles_removed"] == (1 if expected is not None else 0)
    assert active.deleted_ids == (["candidate"] if expected is not None else [])
    assert len(archive.inserted) == (1 if expected is not None else 0)


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


def test_same_title_with_distinct_non_empty_urls_is_not_duplicate(monkeypatch):
    result, active, archive = run_cleanup(
        monkeypatch,
        [
            article("one", "Same story", source_url="https://one.test/story"),
            article("two", "Same story", source_url="https://two.test/story"),
        ],
    )

    assert result["duplicates_removed"] == 0
    assert active.find_one_calls == []
    assert active.deleted_ids == []
    assert archive.inserted == []


def test_blank_source_url_falls_back_to_case_insensitive_title(monkeypatch):
    result, active, archive = run_cleanup(
        monkeypatch,
        [
            article("older", " Fallback Story ", source_url="   ", publishedDate="1"),
            article("newer", "fallback story", source_url="", publishedDate="2"),
        ],
    )

    assert result["duplicates_removed"] == 1
    assert [item["_id"] for item in active.records] == ["newer"]
    assert archive.inserted[0]["title"] == " Fallback Story "


def test_blank_source_url_and_blank_title_retain_title_empty_group(monkeypatch):
    result, active, archive = run_cleanup(
        monkeypatch,
        [
            article("first", "", source_url="", publishedDate="1"),
            article("second", "   ", source_url="   ", publishedDate="2"),
        ],
    )

    assert result["duplicates_removed"] == 1
    assert [item["_id"] for item in active.records] == ["second"]
    assert len(archive.inserted) == 1


def test_equal_score_keeps_first_scanned_member(monkeypatch):
    result, active, archive = run_cleanup(
        monkeypatch,
        [
            article("first", "Tied", source_url="https://same.test/tied"),
            article("second", "Tied", source_url="https://same.test/tied"),
        ],
    )

    assert result["duplicates_removed"] == 1
    assert [item["_id"] for item in active.records] == ["first"]
    assert active.deleted_ids == ["second"]


def test_three_member_group_recomputes_one_winner_and_two_losers(monkeypatch):
    result, active, archive = run_cleanup(
        monkeypatch,
        [
            article(
                "old", "Old", source_url="https://same.test/three", publishedDate="1"
            ),
            article(
                "best", "Best", source_url="https://same.test/three", publishedDate="3"
            ),
            article(
                "middle",
                "Middle",
                source_url="https://same.test/three",
                publishedDate="2",
            ),
        ],
    )

    assert result["duplicates_removed"] == 2
    assert [item["_id"] for item in active.records] == ["best"]
    assert active.find_one_calls[:3] == ["old", "best", "middle"]
    assert active.deleted_ids == ["middle", "old"]
    assert [item["archive_reason"] for item in archive.inserted] == [
        "duplicate",
        "duplicate",
    ]


def test_manual_edited_has_same_precedence_as_manual_edit_protected(monkeypatch):
    result, active, _archive = run_cleanup(
        monkeypatch,
        [
            article(
                "manual",
                "Manual",
                source_url="https://same.test/manual",
                manual_edited=True,
                publishedDate="1",
            ),
            article(
                "forced",
                "Forced",
                source_url="https://same.test/manual",
                force_live=True,
                publishedDate="9",
                content=LONG_CONTENT * 2,
            ),
        ],
    )

    assert result["duplicates_removed"] == 1
    assert [item["_id"] for item in active.records] == ["manual"]


def test_force_live_precedes_timestamp_and_content(monkeypatch):
    result, active, _archive = run_cleanup(
        monkeypatch,
        [
            article(
                "forced",
                "Forced",
                source_url="https://same.test/forced",
                force_live=True,
                publishedDate="1",
            ),
            article(
                "newer",
                "Newer",
                source_url="https://same.test/forced",
                publishedDate="9",
                content=LONG_CONTENT * 2,
            ),
        ],
    )

    assert result["duplicates_removed"] == 1
    assert [item["_id"] for item in active.records] == ["forced"]


@pytest.mark.parametrize(
    "timestamp_field",
    ["manual_edited_at", "updated_at", "created_at", "publishedDate"],
)
def test_each_timestamp_fallback_field_can_select_winner(monkeypatch, timestamp_field):
    earlier = article(
        "earlier",
        "Earlier",
        source_url="https://same.test/time",
        publishedDate="1",
    )
    later = article(
        "later",
        "Later",
        source_url="https://same.test/time",
        publishedDate="1",
    )
    later[timestamp_field] = "2"

    result, active, _archive = run_cleanup(monkeypatch, [earlier, later])

    assert result["duplicates_removed"] == 1
    assert [item["_id"] for item in active.records] == ["later"]


def test_timestamp_strings_retain_lexicographical_order(monkeypatch):
    result, active, _archive = run_cleanup(
        monkeypatch,
        [
            article(
                "lexical",
                "Lexical",
                source_url="https://same.test/lex",
                publishedDate="9",
            ),
            article(
                "numeric",
                "Numeric",
                source_url="https://same.test/lex",
                publishedDate="10",
            ),
        ],
    )

    assert result["duplicates_removed"] == 1
    assert [item["_id"] for item in active.records] == ["lexical"]


def test_content_length_breaks_only_later_tie(monkeypatch):
    result, active, _archive = run_cleanup(
        monkeypatch,
        [
            article("shorter", "Shorter", source_url="https://same.test/length"),
            article(
                "longer",
                "Longer",
                source_url="https://same.test/length",
                content=LONG_CONTENT * 2,
            ),
        ],
    )

    assert result["duplicates_removed"] == 1
    assert [item["_id"] for item in active.records] == ["longer"]


def test_first_pass_streams_exact_projection_and_releases_projected_content(
    monkeypatch,
):
    result, active, archive = run_cleanup(
        monkeypatch,
        [article("singleton", "Unique", content=TrackedContent(LONG_CONTENT))],
    )

    assert result["success"] is True
    assert active.duplicate_projection == DUPLICATE_PROJECTION
    assert active.duplicate_scan_iterated is True
    assert active.find_one_calls == []
    assert all(ref() is None for ref in active.duplicate_scan_refs)
    assert all(ref() is None for ref in active.projected_content_refs)
    assert archive.inserted == []


def test_all_duplicate_group_members_are_fetched_but_singletons_are_not(monkeypatch):
    result, active, _archive = run_cleanup(
        monkeypatch,
        [
            article(
                "one", "One", source_url="https://same.test/group", publishedDate="1"
            ),
            article(
                "two", "Two", source_url="https://same.test/group", publishedDate="2"
            ),
            article("singleton", "Singleton", source_url="https://other.test/story"),
        ],
    )

    assert result["duplicates_removed"] == 1
    assert active.find_one_calls == ["one", "two"]


def test_provisional_winner_disappears_and_group_falls_to_one(monkeypatch):
    def remove_winner(collection):
        collection.records = [
            item for item in collection.records if item["_id"] != "winner"
        ]

    result, active, archive = run_cleanup(
        monkeypatch,
        [
            article(
                "loser", "Loser", source_url="https://same.test/race", publishedDate="1"
            ),
            article(
                "winner",
                "Winner",
                source_url="https://same.test/race",
                publishedDate="2",
            ),
        ],
        after_duplicate_scan=remove_winner,
    )

    assert result["duplicates_removed"] == 0
    assert active.deleted_ids == []
    assert archive.inserted == []


def test_provisional_loser_disappears_and_group_falls_to_one(monkeypatch):
    def remove_loser(collection):
        collection.records = [
            item for item in collection.records if item["_id"] != "loser"
        ]

    result, active, archive = run_cleanup(
        monkeypatch,
        [
            article(
                "loser", "Loser", source_url="https://same.test/race", publishedDate="1"
            ),
            article(
                "winner",
                "Winner",
                source_url="https://same.test/race",
                publishedDate="2",
            ),
        ],
        after_duplicate_scan=remove_loser,
    )

    assert result["duplicates_removed"] == 0
    assert active.deleted_ids == []
    assert archive.inserted == []


@pytest.mark.parametrize("changed_id", ["winner", "loser"])
def test_identity_change_removes_member_from_provisional_group(monkeypatch, changed_id):
    def change_identity(collection):
        for item in collection.records:
            if item["_id"] == changed_id:
                item["source_url"] = "https://different.test/story"

    result, active, archive = run_cleanup(
        monkeypatch,
        [
            article(
                "loser",
                "Loser",
                source_url="https://same.test/identity",
                publishedDate="1",
            ),
            article(
                "winner",
                "Winner",
                source_url="https://same.test/identity",
                publishedDate="2",
            ),
        ],
        after_duplicate_scan=change_identity,
    )

    assert result["duplicates_removed"] == 0
    assert active.deleted_ids == []
    assert archive.inserted == []


@pytest.mark.parametrize(
    ("field", "value"),
    [("manual_edited", True), ("manual_edit_protected", True), ("force_live", True)],
)
def test_revalidation_recomputes_protection_and_force_live(monkeypatch, field, value):
    def promote_loser(collection):
        collection.records[0][field] = value

    result, active, archive = run_cleanup(
        monkeypatch,
        [
            article(
                "loser",
                "Loser",
                source_url="https://same.test/promote",
                publishedDate="1",
            ),
            article(
                "winner",
                "Winner",
                source_url="https://same.test/promote",
                publishedDate="2",
            ),
        ],
        after_duplicate_scan=promote_loser,
    )

    assert result["duplicates_removed"] == 1
    assert [item["_id"] for item in active.records] == ["loser"]
    assert archive.inserted[0]["title"] == "Winner"


def test_revalidation_recomputes_content_length_winner(monkeypatch):
    def improve_loser(collection):
        collection.records[0]["content"] = LONG_CONTENT * 3

    result, active, archive = run_cleanup(
        monkeypatch,
        [
            article("loser", "Loser", source_url="https://same.test/content"),
            article(
                "winner",
                "Winner",
                source_url="https://same.test/content",
                content=LONG_CONTENT * 2,
            ),
        ],
        after_duplicate_scan=improve_loser,
    )

    assert result["duplicates_removed"] == 1
    assert [item["_id"] for item in active.records] == ["loser"]
    assert archive.inserted[0]["title"] == "Winner"


def test_revalidation_recomputes_timestamp_winner(monkeypatch):
    def update_loser(collection):
        collection.records[0]["updated_at"] = "3"

    result, active, archive = run_cleanup(
        monkeypatch,
        [
            article(
                "loser",
                "Loser",
                source_url="https://same.test/update",
                publishedDate="1",
            ),
            article(
                "winner",
                "Winner",
                source_url="https://same.test/update",
                publishedDate="2",
            ),
        ],
        after_duplicate_scan=update_loser,
    )

    assert result["duplicates_removed"] == 1
    assert [item["_id"] for item in active.records] == ["loser"]
    assert archive.inserted[0]["title"] == "Winner"


def test_three_member_group_recomputes_latest_winner(monkeypatch):
    def promote_oldest(collection):
        collection.records[0]["manual_edited"] = True

    result, active, archive = run_cleanup(
        monkeypatch,
        [
            article(
                "oldest",
                "Oldest",
                source_url="https://same.test/latest",
                publishedDate="1",
            ),
            article(
                "middle",
                "Middle",
                source_url="https://same.test/latest",
                publishedDate="2",
            ),
            article(
                "newest",
                "Newest",
                source_url="https://same.test/latest",
                publishedDate="3",
            ),
        ],
        after_duplicate_scan=promote_oldest,
    )

    assert result["duplicates_removed"] == 2
    assert [item["_id"] for item in active.records] == ["oldest"]
    assert {item["title"] for item in archive.inserted} == {"Middle", "Newest"}


def test_duplicate_archive_preserves_complete_latest_loser(monkeypatch):
    original_loser = article(
        "loser",
        "Loser",
        source_url="https://same.test/archive",
        publishedDate="1",
        image="https://images.test/story.jpg",
        image_metadata={"credit": "Publisher"},
        source="Provider",
        source_metadata={"feed": "local"},
        analytics={"views": 8},
        social_state={"facebook": {"prepared": True}},
        legacy_field="preserve-me",
        arbitrary_nested={"one": {"two": [1, 2, 3]}},
    )

    def update_loser(collection):
        collection.records[0]["latest_nested"] = {"revision": 2}

    result, active, archive = run_cleanup(
        monkeypatch,
        [
            original_loser,
            article(
                "winner",
                "Winner",
                source_url="https://same.test/archive",
                publishedDate="2",
            ),
        ],
        after_duplicate_scan=update_loser,
    )

    assert result["duplicates_removed"] == 1
    archived = archive.inserted[0]
    expected = deepcopy(original_loser)
    expected["latest_nested"] = {"revision": 2}
    expected.pop("_id")
    expected["archived_at"] = archived["archived_at"]
    expected["archive_reason"] = "duplicate"
    assert archived == expected
    assert [item["_id"] for item in active.records] == ["winner"]


def test_duplicate_archive_failure_preserves_active_and_does_not_count(monkeypatch):
    result, active, archive = run_cleanup(
        monkeypatch,
        [
            article(
                "loser",
                "Loser",
                source_url="https://same.test/failure",
                publishedDate="1",
            ),
            article(
                "winner",
                "Winner",
                source_url="https://same.test/failure",
                publishedDate="2",
            ),
        ],
        archive_fails=True,
    )

    assert result["success"] is True
    assert result["duplicates_removed"] == 0
    assert active.deleted_ids == []
    assert {item["_id"] for item in active.records} == {"loser", "winner"}
    assert archive.inserted == []


def test_duplicate_delete_exception_does_not_count(monkeypatch):
    result, active, archive = run_cleanup(
        monkeypatch,
        [
            article(
                "loser",
                "Loser",
                source_url="https://same.test/delete",
                publishedDate="1",
            ),
            article(
                "winner",
                "Winner",
                source_url="https://same.test/delete",
                publishedDate="2",
            ),
        ],
        delete_raises=True,
    )

    assert result["success"] is True
    assert result["duplicates_removed"] == 0
    assert len(archive.inserted) == 1
    assert {item["_id"] for item in active.records} == {"loser", "winner"}


def test_duplicate_delete_noop_does_not_count(monkeypatch):
    result, active, archive = run_cleanup(
        monkeypatch,
        [
            article(
                "loser", "Loser", source_url="https://same.test/noop", publishedDate="1"
            ),
            article(
                "winner",
                "Winner",
                source_url="https://same.test/noop",
                publishedDate="2",
            ),
        ],
        delete_count=0,
    )

    assert result["success"] is True
    assert result["duplicates_removed"] == 0
    assert active.events == [("archive", "Loser"), ("delete", "loser")]
    assert len(archive.inserted) == 1


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


@pytest.mark.parametrize(
    ("content", "summary"),
    [
        ("", ""),
        ("short content", ""),
        ("", "short summary"),
        ("a" * 499, "b" * 499),
        ("a" * 499, "b" * 500),
        ("a" * 500, "b" * 500),
        ("  " + ("a" * 499) + "  ", "\t" + ("b" * 499) + "\n"),
        ("\u2003" + ("a" * 499) + "\u2003", "\u00a0" + ("b" * 500) + "\u00a0"),
    ],
    ids=[
        "both-empty",
        "content-only",
        "summary-only",
        "effective-999",
        "effective-1000",
        "effective-1001",
        "ordinary-whitespace",
        "unicode-whitespace",
    ],
)
def test_short_content_length_matches_old_joined_blob_semantics(
    monkeypatch, content, summary
):
    assert_short_content_matches_old_assessment(monkeypatch, content, summary)


def _mixed_case(value):
    return "".join(
        character.upper() if index % 2 == 0 else character.lower()
        for index, character in enumerate(value)
    )


@pytest.mark.parametrize("marker", BOILERPLATE_MARKERS)
@pytest.mark.parametrize("placement", ["content", "summary", "boundary"])
def test_each_boilerplate_marker_matches_old_case_and_boundary_semantics(
    monkeypatch, marker, placement
):
    if placement == "content":
        content = ("x" * 1000) + marker.upper()
        summary = ""
    elif placement == "summary":
        content = "x" * 1000
        summary = _mixed_case(marker)
    else:
        variant = _mixed_case(marker)
        split_at = variant.find(" ", len(variant) // 3)
        assert split_at > 0
        content = ("x" * 1000) + variant[:split_at]
        summary = variant[split_at + 1 :]

    assert_short_content_matches_old_assessment(monkeypatch, content, summary)


def test_lower_semantics_do_not_become_casefold_semantics(monkeypatch):
    marker_lookalike = BOILERPLATE_MARKERS[2].replace("across", "acroß")
    assert marker_lookalike.lower() == marker_lookalike
    assert marker_lookalike.casefold() != marker_lookalike

    assert_short_content_matches_old_assessment(
        monkeypatch,
        ("x" * 1000) + marker_lookalike,
        "",
    )


def test_short_content_assessment_does_not_join_full_article_text(monkeypatch):
    result, active, archive = run_cleanup(
        monkeypatch,
        [
            article(
                "complete",
                "Complete article",
                content=NoFullBlobJoinText("x" * 1000),
                summary=NoFullBlobJoinText("complete summary"),
            )
        ],
    )

    assert result["success"] is True
    assert result["short_articles_removed"] == 0
    assert active.deleted_ids == []
    assert archive.inserted == []


@pytest.mark.parametrize(
    ("content", "summary"),
    [
        (123, ""),
        ("complete", ["not", "a", "string"]),
    ],
)
def test_truthy_non_string_text_preserves_strip_failure(monkeypatch, content, summary):
    record = article("malformed", "Malformed text", content=content, summary=summary)
    with pytest.raises(AttributeError):
        old_short_content_assessment(record)

    result, active, archive = run_cleanup(monkeypatch, [record])

    assert result["success"] is False
    assert result["total_removed"] == 0
    assert active.deleted_ids == []
    assert archive.inserted == []


def test_first_pass_articles_are_unreachable_before_second_materialisation(monkeypatch):
    result, active, archive = run_cleanup(
        monkeypatch,
        [article("kept", "Unique complete story")],
    )

    assert result["success"] is True
    assert active.find_calls == 2
    assert active.duplicate_projection == DUPLICATE_PROJECTION
    assert active.duplicate_scan_iterated is True
    assert all(ref() is None for ref in active.duplicate_scan_refs)
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
    assert active.short_projection == SHORT_CONTENT_PROJECTION
    assert active.short_scan_iterated is True
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
        after_short_scan=hide_for_review,
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
        after_short_scan=protect_article,
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
        after_short_scan=complete_article,
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
        after_short_scan=update_article,
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
        after_short_scan=remove_candidate,
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
