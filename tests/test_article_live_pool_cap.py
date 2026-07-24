import asyncio
import os
from copy import deepcopy
from types import SimpleNamespace

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "cheshire_test")
os.environ.setdefault("LOCAL_DEV_NO_DB", "1")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_dummy")

from backend import server
from backend.scripts import repair_live_article_pool as repair

FULL_CONTENT = "Complete verified reporting. " * 80


class Cursor:
    def __init__(self, records):
        self.records = records

    async def to_list(self, _limit):
        return deepcopy(self.records)


class Articles:
    def __init__(self, records):
        self.records = deepcopy(records)
        self.updates = []

    def find(self, _query, _projection=None):
        return Cursor(self.records)

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
