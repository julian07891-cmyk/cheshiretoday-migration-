import asyncio
import inspect
import os
from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server
from backend.scripts import repair_live_article_pool as repair

FULL_CONTENT = "Complete verified reporting. " * 80


class Cursor:
    def __init__(self, records, fail_after=None):
        self.records = records
        self.fail_after = fail_after
        self.limit_value = None
        self.yielded_count = 0

    def limit(self, value):
        self.limit_value = value
        return self

    def __aiter__(self):
        async def iterate():
            for index, record in enumerate(self.records):
                if self.limit_value is not None and index >= self.limit_value:
                    break
                if self.fail_after is not None and index >= self.fail_after:
                    raise RuntimeError("injected visible-pool scan failure")
                self.yielded_count += 1
                yield deepcopy(record)

        return iterate()


class Articles:
    def __init__(self, records, fail_after=None):
        self.records = deepcopy(records)
        self.fail_after = fail_after
        self.find_calls = []
        self.updates = []
        self.cursor = None

    def find(self, query, projection=None):
        self.find_calls.append((deepcopy(query), deepcopy(projection)))
        matching = [
            record
            for record in self.records
            if record.get("archived") in (None, False)
            or (
                record.get("archived") is True
                and record.get("archive_reason") in {"auto_cap", "ratio_rebalance"}
            )
        ]
        self.cursor = Cursor(matching, fail_after=self.fail_after)
        return self.cursor

    async def update_many(self, query, update):
        self.updates.append((deepcopy(query), deepcopy(update)))
        return SimpleNamespace(modified_count=0)


def article(record_id, **values):
    record = {
        "_id": record_id,
        "title": f"Article {record_id}",
        "content": FULL_CONTENT,
        "publishedDate": f"2026-07-{record_id:02d}T12:00:00+00:00",
        "archived": False,
    }
    record.update(values)
    return record


def reference_visible_pool_plan(records, keep):
    """Reproduce the pre-streaming algorithm for ordered cursor results."""
    candidates = deepcopy(records[:10000])

    def parsed_date(value):
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if not value:
            return datetime.fromtimestamp(0, tz=timezone.utc)
        try:
            result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return result if result.tzinfo else result.replace(tzinfo=timezone.utc)
        except Exception:
            return datetime.fromtimestamp(0, tz=timezone.utc)

    candidates.sort(
        key=lambda item: (
            int(
                item.get("force_live") is True
                or item.get("featured") is True
                or item.get("is_priority_cheshire") is True
            ),
            max(parsed_date(item.get("publishedDate")), parsed_date(item.get("created_at"))),
        ),
        reverse=True,
    )
    protected_ids = {
        item["_id"]
        for item in candidates
        if item.get("_id") is not None and server._is_owner_protected_article(item)
    }
    eligible = [item for item in candidates if server._counts_towards_visible_cap(item)]
    newest_ids = [item["_id"] for item in eligible[:keep] if item.get("_id") is not None]
    keep_ids = list(protected_ids.union(newest_ids))
    eligible_ids = [
        item["_id"]
        for item in eligible
        if item.get("_id") is not None and item["_id"] not in protected_ids
    ]
    restore_ids = [
        item["_id"]
        for item in eligible
        if item.get("_id") in keep_ids
        and item.get("archived") is True
        and item.get("archive_reason") in {"auto_cap", "ratio_rebalance"}
    ]
    return {
        "scanned_count": len(candidates),
        "protected_ids": protected_ids,
        "newest_ids": newest_ids,
        "keep_ids": keep_ids,
        "eligible_ids": eligible_ids,
        "restore_ids": restore_ids,
    }


def scalar_visible_pool_plan(records, keep):
    """Build the exact scalar input consumed by the production planner."""
    epoch = datetime.fromtimestamp(0, tz=timezone.utc)

    def parsed_date(value):
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if not value:
            return epoch
        try:
            result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return result if result.tzinfo else result.replace(tzinfo=timezone.utc)
        except Exception:
            return epoch

    protected_ids = set()
    eligible = []
    for ordinal, item in enumerate(records[:10000]):
        owner_protected = server._is_owner_protected_article(item)
        if item.get("_id") is not None and owner_protected:
            protected_ids.add(item["_id"])
        if server._counts_towards_visible_cap(item):
            eligible.append(
                (
                    item.get("_id"),
                    int(
                        item.get("force_live") is True
                        or item.get("featured") is True
                        or item.get("is_priority_cheshire") is True
                    ),
                    max(parsed_date(item.get("publishedDate")), parsed_date(item.get("created_at"))),
                    ordinal,
                    owner_protected,
                    item.get("archived") is True,
                    item.get("archive_reason"),
                )
            )
    plan = server._plan_visible_pool_scalars(eligible, protected_ids, keep)
    return {
        "scanned_count": min(len(records), 10000),
        "protected_ids": protected_ids,
        **plan,
    }


def test_metadata_only_records_do_not_count_towards_cap():
    assert server._counts_towards_visible_cap(article(1)) is True
    assert server._counts_towards_visible_cap(article(2, content="")) is False


def test_manual_and_failed_review_records_do_not_count_towards_cap():
    assert server._counts_towards_visible_cap(
        article(1, manual_review_hidden_from_public=True)
    ) is False
    assert server._counts_towards_visible_cap(
        article(2, rewrite_status="ai_rewrite_needs_review")
    ) is False


def test_visible_cap_effective_length_boundary_is_unchanged():
    assert server._counts_towards_visible_cap(
        article(1, content="x" * 999, summary="")
    ) is False
    assert server._counts_towards_visible_cap(
        article(2, content="x" * 900, summary="y" * 99)
    ) is True
    assert server._counts_towards_visible_cap(
        article(3, content="x" * 1000, summary="")
    ) is True


def test_existing_owner_markers_are_protected():
    fixtures = [
        article(1, manual_edited=True),
        article(2, manual_edit_protected=True),
        article(3, verification_status="manual_corrected_verified_limited"),
        article(4, rewrite_status="manual_corrected"),
        article(5, verification_status="manual_force_live"),
        article(6, rewrite_status="manual_force_live"),
        article(7, source="Manual Entry"),
    ]
    assert all(server._is_owner_protected_article(item) for item in fixtures)


def test_cap_protects_owner_records_and_ignores_metadata(monkeypatch):
    records = [
        article(1, manual_edited=True),
        article(2),
        article(3, content=""),
    ]
    collection = Articles(records)
    monkeypatch.setattr(server, "db", SimpleNamespace(articles=collection))

    result = asyncio.run(server.cap_visible_articles(keep=1))

    assert result["protected"] == 1
    archive_query = collection.updates[0][0]
    assert archive_query["_id"]["$in"] == [2]
    assert 1 in archive_query["_id"]["$nin"]
    assert 3 not in archive_query["_id"]["$in"]


def test_cap_can_restore_selected_automatic_archives(monkeypatch):
    records = [
        article(
            1,
            archived=True,
            archive_reason="auto_cap",
            publishedDate="2026-07-24T12:00:00+00:00",
        ),
        article(
            2,
            archived=True,
            archive_reason="ratio_rebalance",
            publishedDate="2026-07-23T12:00:00+00:00",
        ),
        article(
            3,
            archived=True,
            archive_reason="manual_admin",
            publishedDate="2026-07-22T12:00:00+00:00",
        ),
    ]
    collection = Articles(records)
    monkeypatch.setattr(server, "db", SimpleNamespace(articles=collection))

    asyncio.run(server.cap_visible_articles(keep=1))

    find_query = collection.find_calls[0][0]
    assert "auto_cap" in str(find_query)
    assert "ratio_rebalance" in str(find_query)

    restore_updates = [
        (query, update)
        for query, update in collection.updates
        if update.get("$set", {}).get("archived") is False
    ]
    assert len(restore_updates) == 1

    restore_query, restore_update = restore_updates[0]
    assert restore_query["_id"]["$in"] == [1]
    assert restore_query["archived"] is True
    assert restore_query["archive_reason"] == {
        "$in": ["auto_cap", "ratio_rebalance"]
    }
    assert restore_update["$unset"] == {
        "archived_at": "",
        "archive_reason": "",
    }


def test_streamed_scalar_plan_is_equivalent_to_old_materialised_algorithm(monkeypatch):
    records = [
        article(
            record_id,
            publishedDate=f"2026-07-{1 + record_id % 28:02d}T{record_id % 24:02d}:00:00+00:00",
            created_at=f"2026-07-{1 + record_id % 28:02d}T{record_id % 24:02d}:05:00+00:00",
        )
        for record_id in range(1, 131)
    ]
    records[0].update(publishedDate="2026-07-20T12:00:00+00:00", created_at=None)
    records[1].update(publishedDate="2026-07-20T12:00:00+00:00", created_at=None)
    records[2]["force_live"] = True
    records[3]["featured"] = True
    records[4]["is_priority_cheshire"] = True
    records[5]["publishedDate"] = "malformed"
    records[5]["created_at"] = None
    records[6]["created_at"] = "2026-08-01T12:00:00+00:00"
    records[7]["manual_edited"] = True
    records[8]["manual_edit_protected"] = True
    records[9]["source"] = "Manual Entry"
    records[10]["verification_status"] = "manual_corrected_verified_limited"
    records[11]["verification_status"] = "manual_force_live"
    records[12]["rewrite_status"] = "manual_corrected"
    records[13]["rewrite_status"] = "manual_force_live"
    records[14].update(manual_edited=True, manual_review_hidden_from_public=True)
    records[15]["content"] = ""
    records[16]["content"] = "short"
    records[17].update(content="x" * 900, summary="y" * 99)
    records[18].update(content="x" * 1000, summary="")
    records[19].update(
        archived=True,
        archive_reason="auto_cap",
        force_live=True,
    )
    records[20].update(
        archived=True,
        archive_reason="ratio_rebalance",
        featured=True,
    )
    records[21].update(archived=True, archive_reason="manual_admin")
    records[22].update(publishedDate=None, created_at=None)
    records[-1].update(manual_edited=True, publishedDate="2020-01-01T00:00:00+00:00")

    matching = [
        item
        for item in records
        if item.get("archived") in (None, False)
        or (
            item.get("archived") is True
            and item.get("archive_reason") in {"auto_cap", "ratio_rebalance"}
        )
    ]
    reference = reference_visible_pool_plan(matching, keep=100)
    streamed = scalar_visible_pool_plan(matching, keep=100)

    assert streamed["scanned_count"] == reference["scanned_count"]
    assert streamed["protected_ids"] == reference["protected_ids"]
    assert streamed["newest_ids"] == reference["newest_ids"]
    assert set(streamed["keep_ids"]) == set(reference["keep_ids"])
    assert streamed["eligible_ids"] == reference["eligible_ids"]
    assert streamed["restore_ids"] == reference["restore_ids"]
    assert streamed["newest_ids"].index(records[0]["_id"]) < streamed["newest_ids"].index(records[1]["_id"])
    assert records[2]["_id"] in streamed["newest_ids"]
    assert records[2]["_id"] not in streamed["protected_ids"]
    assert records[-1]["_id"] in streamed["protected_ids"]
    assert records[14]["_id"] not in streamed["protected_ids"]
    assert records[21]["_id"] not in streamed["eligible_ids"]

    collection = Articles(records)
    monkeypatch.setattr(server, "db", SimpleNamespace(articles=collection))
    result = asyncio.run(server.cap_visible_articles(keep=100))

    assert result == {
        "success": True,
        "keep": 100,
        "keep_ids": len(reference["keep_ids"]),
        "protected": len(reference["protected_ids"]),
    }
    restore_query, restore_update = collection.updates[0]
    archive_query, archive_update = collection.updates[1]
    assert restore_query == {
        "_id": {"$in": reference["restore_ids"]},
        "archived": True,
        "archive_reason": {"$in": ["auto_cap", "ratio_rebalance"]},
    }
    assert restore_update == {
        "$set": {"archived": False},
        "$unset": {"archived_at": "", "archive_reason": ""},
    }
    assert archive_query == {
        "_id": {
            "$in": reference["eligible_ids"],
            "$nin": reference["keep_ids"],
        }
    }
    assert archive_update["$set"]["archived"] is True
    assert archive_update["$set"]["archive_reason"] == "auto_cap"
    assert isinstance(archive_update["$set"]["archived_at"], str)


def test_visible_pool_stream_enforces_exact_ceiling_and_projection(monkeypatch):
    records = [
        article(
            record_id,
            content="x" * 1000,
            publishedDate="2026-07-20T12:00:00+00:00",
        )
        for record_id in range(1, 10006)
    ]
    collection = Articles(records)
    monkeypatch.setattr(server, "db", SimpleNamespace(articles=collection))

    asyncio.run(server.cap_visible_articles(keep=1))

    assert collection.cursor.limit_value == 10000
    assert collection.cursor.yielded_count == 10000
    find_query, projection = collection.find_calls[0]
    assert find_query == {
        "$or": [
            {"archived": {"$exists": False}},
            {"archived": False},
            {
                "archived": True,
                "archive_reason": {"$in": ["auto_cap", "ratio_rebalance"]},
            },
        ]
    }
    assert projection == {
        "_id": 1,
        "content": 1,
        "summary": 1,
        "publishedDate": 1,
        "created_at": 1,
        "source": 1,
        "featured": 1,
        "force_live": 1,
        "is_priority_cheshire": 1,
        "archived": 1,
        "archive_reason": 1,
        "manual_review_hidden_from_public": 1,
        "verification_status": 1,
        "rewrite_status": 1,
        "manual_edited": 1,
        "manual_edit_protected": 1,
    }
    archived_ids = collection.updates[-1][0]["_id"]["$in"]
    assert 10001 not in archived_ids
    assert 10005 not in archived_ids


def test_visible_pool_scan_failure_performs_zero_writes(monkeypatch):
    collection = Articles([article(1), article(2), article(3)], fail_after=2)
    monkeypatch.setattr(server, "db", SimpleNamespace(articles=collection))

    result = asyncio.run(server.cap_visible_articles(keep=1))

    assert result["success"] is False
    assert "injected visible-pool scan failure" in result["error"]
    assert collection.updates == []


def test_visible_pool_runtime_retains_only_scalar_planning_state():
    runtime_source = inspect.getsource(server.cap_visible_articles)
    planner_source = inspect.getsource(server._plan_visible_pool_scalars)

    assert ".to_list(" not in runtime_source
    assert ".limit(10000)" in runtime_source
    assert ".batch_size(" not in runtime_source
    assert "article = None" in runtime_source
    assert "content" not in planner_source
    assert "summary" not in planner_source


def test_ratio_rebalance_source_protects_owner_ids():
    source = open(server.__file__, encoding="utf-8").read()
    ratio = source[source.index("# === RATIO_REBALANCE_45 ===") :]
    assert "_is_owner_protected_article(article)" in ratio
    assert "owner_protected_ids.union" in ratio


def test_repair_restores_only_automatic_owner_approved_records():
    records = [
        article(1, archived=True, archive_reason="auto_cap", manual_edited=True),
        article(
            2,
            archived=True,
            archive_reason="ratio_rebalance",
            source="Manual Entry",
        ),
        article(3, archived=True, archive_reason="manual_admin", manual_edited=True),
        article(4, archived=True, archive_reason="auto_cap", content=""),
        article(
            5,
            archived=True,
            archive_reason="auto_cap",
            manual_edited=True,
            editorial_status="rejected",
        ),
        article(
            6,
            archived=True,
            archive_reason="auto_cap",
            manual_edited=True,
            manual_review_hidden_from_public=True,
        ),
    ]
    plan = repair.build_plan(records)
    assert plan.record_ids == (1, 2)


class RepairRepository:
    def __init__(
        self,
        records,
        *,
        scan_results=None,
        matched_count=None,
        modified_count=None,
        leave_eligible=False,
    ):
        self.records = deepcopy(records)
        self.scan_results = [
            deepcopy(result) for result in (scan_results or [])
        ]
        self.matched_count = matched_count
        self.modified_count = modified_count
        self.leave_eligible = leave_eligible
        self.write_calls = []

    def scan(self):
        if self.scan_results:
            return self.scan_results.pop(0)
        return deepcopy(self.records)

    def restore_many(self, record_ids):
        self.write_calls.append(tuple(record_ids))
        matched = (
            len(record_ids)
            if self.matched_count is None
            else self.matched_count
        )
        modified = (
            len(record_ids)
            if self.modified_count is None
            else self.modified_count
        )
        if not self.leave_eligible:
            for record in self.records:
                if record["_id"] in record_ids:
                    record["archived"] = False
                    record.pop("archive_reason", None)
        return matched, modified


def test_repair_dry_run_is_zero_write_and_apply_is_expected_count_guarded():
    repository = RepairRepository(
        [article(1, archived=True, archive_reason="auto_cap", manual_edited=True)]
    )
    dry_run = repair.execute(repository, "dry-run", None)
    assert dry_run["expected_live_increase"] == 1
    assert repository.write_calls == []

    try:
        repair.execute(repository, "apply", 2)
    except repair.RepairError:
        pass
    else:
        raise AssertionError("Expected-count mismatch was not rejected")
    assert repository.write_calls == []

    applied = repair.execute(repository, "apply", 1)
    assert applied["updated"] == 1
    assert repository.write_calls == [(1,)]


def test_repair_count_drift_aborts_before_write():
    first = [article(1, archived=True, archive_reason="auto_cap", manual_edited=True)]
    second = first + [
        article(2, archived=True, archive_reason="auto_cap", manual_edited=True)
    ]
    repository = RepairRepository(first, scan_results=[first, second])

    try:
        repair.execute(repository, "apply", 1)
    except repair.RepairError:
        pass
    else:
        raise AssertionError("Count drift was not rejected")
    assert repository.write_calls == []


def test_repair_id_set_drift_aborts_before_write():
    first = [article(1, archived=True, archive_reason="auto_cap", manual_edited=True)]
    second = [article(2, archived=True, archive_reason="auto_cap", manual_edited=True)]
    repository = RepairRepository(first, scan_results=[first, second])

    try:
        repair.execute(repository, "apply", 1)
    except repair.RepairError:
        pass
    else:
        raise AssertionError("ID-set drift was not rejected")
    assert repository.write_calls == []


def test_repair_partial_match_is_reported_as_failure():
    records = [
        article(1, archived=True, archive_reason="auto_cap", manual_edited=True),
        article(2, archived=True, archive_reason="auto_cap", manual_edited=True),
    ]
    repository = RepairRepository(records, matched_count=1, modified_count=1)

    try:
        repair.execute(repository, "apply", 2)
    except repair.RepairError:
        pass
    else:
        raise AssertionError("Partial matching was not rejected")
    assert repository.write_calls == [(1, 2)]


def test_repair_success_updates_all_records_in_one_operation():
    records = [
        article(1, archived=True, archive_reason="auto_cap", manual_edited=True),
        article(2, archived=True, archive_reason="ratio_rebalance", source="Manual Entry"),
    ]
    repository = RepairRepository(records)

    result = repair.execute(repository, "apply", 2)

    assert result["updated"] == 2
    assert repository.write_calls == [(1, 2)]


def test_repair_post_write_verification_failure_is_detected():
    records = [
        article(1, archived=True, archive_reason="auto_cap", manual_edited=True)
    ]
    repository = RepairRepository(records, leave_eligible=True)

    try:
        repair.execute(repository, "apply", 1)
    except repair.RepairError:
        pass
    else:
        raise AssertionError("Verification failure was not detected")
    assert repository.write_calls == [(1,)]
