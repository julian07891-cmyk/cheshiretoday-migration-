import importlib.util
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from backend.scripts import provision_newsletter_email_unique_index as provisioning


class Cursor(list):
    def sort(self, *args):
        key = args[0][0][0] if len(args) == 1 else args[0]
        return Cursor(sorted(self, key=lambda item: str(item.get(key))))


class FakeCollection:
    def __init__(self, records, indexes=None, batches=None):
        self.records = deepcopy(records)
        self.indexes = deepcopy(indexes or [{"name": "_id_", "key": [("_id", 1)]}])
        self.batches = [deepcopy(batch) for batch in batches] if batches else None
        self.find_calls = 0
        self.create_calls = []
        self.document_writes = []

    def find(self, query, projection):
        assert query == {}
        assert projection == {"_id": 1, "email": 1}
        batch = self.batches[min(self.find_calls, len(self.batches) - 1)] if self.batches else self.records
        self.find_calls += 1
        return Cursor(deepcopy(batch))

    def list_indexes(self):
        return deepcopy(self.indexes)

    def create_index(self, keys, **options):
        self.create_calls.append((deepcopy(keys), deepcopy(options)))
        self.indexes.append({"name": options["name"], "key": deepcopy(keys), "unique": options["unique"], "sparse": options["sparse"]})

    def insert_one(self, *args, **kwargs): self.document_writes.append("insert")
    def update_one(self, *args, **kwargs): self.document_writes.append("update")
    def delete_one(self, *args, **kwargs): self.document_writes.append("delete")


RECORDS = [
    {"_id": 1, "email": "one@example.com"},
    {"_id": 2, "email": "two@example.com"},
]


def apply(collection, **kwargs):
    return provisioning.execute(
        collection,
        "cheshiretoday",
        apply=True,
        expected_count=2,
        stdin_isatty=lambda: True,
        input_func=lambda _prompt: provisioning.CONFIRMATION_TEXT,
        **kwargs,
    )


def exact_index(name=provisioning.INDEX_NAME):
    return {"name": name, "key": [("email", 1)], "unique": True, "sparse": False}


def test_import_isolation_and_default_cli_is_dry_run(monkeypatch):
    assert provisioning.build_parser().parse_args([]).apply is False
    source = Path(provisioning.__file__).read_text()
    assert "backend.server" not in source
    import pymongo
    monkeypatch.setattr(pymongo, "MongoClient", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("connected")))
    spec = importlib.util.spec_from_file_location("isolated_email_index_script", provisioning.__file__)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)


def test_dry_run_reports_safely_and_performs_no_write():
    collection = FakeCollection(RECORDS)
    report = provisioning.execute(collection, "cheshiretoday")
    assert report["mode"] == "dry-run"
    assert report["database"] == "cheshiretoday"
    assert report["collection"] == "subscribers"
    assert report["total_records"] == 2
    assert report["unique_raw_emails"] == 2
    assert report["unique_normalised_emails"] == 2
    assert report["duplicate_group_count"] == 0
    assert report["apply_safe"] is True
    assert collection.create_calls == []
    assert collection.document_writes == []


def test_apply_requires_expected_count_before_reading():
    collection = FakeCollection(RECORDS)
    with pytest.raises(provisioning.ConfirmationError):
        provisioning.execute(collection, "db", apply=True, stdin_isatty=lambda: True)
    assert collection.find_calls == 0


def test_apply_rejects_non_tty_before_reading():
    collection = FakeCollection(RECORDS)
    with pytest.raises(provisioning.ConfirmationError):
        provisioning.execute(collection, "db", apply=True, expected_count=2, stdin_isatty=lambda: False)
    assert collection.find_calls == 0


def test_wrong_confirmation_aborts_without_write():
    collection = FakeCollection(RECORDS)
    with pytest.raises(provisioning.ConfirmationError):
        provisioning.execute(collection, "db", apply=True, expected_count=2, stdin_isatty=lambda: True, input_func=lambda _: "wrong")
    assert collection.create_calls == []


@pytest.mark.parametrize("record", [
    {"_id": 1}, {"_id": 1, "email": ""}, {"_id": 1, "email": 12},
    {"_id": 1, "email": " padded@example.com "}, {"_id": 1, "email": "UPPER@example.com"},
])
def test_malformed_data_blocks_apply(record):
    collection = FakeCollection([record])
    with pytest.raises(provisioning.AuditError):
        provisioning.execute(collection, "db", apply=True, expected_count=1, stdin_isatty=lambda: True)
    assert collection.create_calls == []


def test_raw_normalised_mismatch_and_duplicate_group_are_privacy_safe():
    collection = FakeCollection([{"_id": 1, "email": "A@example.com"}, {"_id": 2, "email": "a@example.com"}])
    audit = provisioning.audit_collection(collection, "db")
    assert audit.unique_raw_emails == 2
    assert audit.unique_normalised_emails == 1
    assert audit.duplicate_groups[0]["group_size"] == 2
    assert "@" not in audit.duplicate_groups[0]["email_hash_prefix"]
    with pytest.raises(provisioning.AuditError):
        provisioning.execute(collection, "db", apply=True, expected_count=2, stdin_isatty=lambda: True)


def test_expected_count_mismatch_aborts():
    collection = FakeCollection(RECORDS)
    with pytest.raises(provisioning.DriftError):
        provisioning.execute(collection, "db", apply=True, expected_count=3, stdin_isatty=lambda: True, input_func=lambda _: provisioning.CONFIRMATION_TEXT)
    assert collection.create_calls == []


def test_collection_count_drift_aborts():
    collection = FakeCollection(RECORDS, batches=[RECORDS, RECORDS + [{"_id": 3, "email": "three@example.com"}]])
    with pytest.raises(provisioning.DriftError):
        apply(collection)
    assert collection.create_calls == []


def test_same_count_ordered_snapshot_drift_aborts():
    changed = [RECORDS[0], {"_id": 2, "email": "changed@example.com"}]
    collection = FakeCollection(RECORDS, batches=[RECORDS, changed])
    with pytest.raises(provisioning.DriftError):
        apply(collection)
    assert collection.create_calls == []


def test_compatible_target_is_already_provisioned_without_write():
    collection = FakeCollection(RECORDS, indexes=[exact_index()])
    report = apply(collection)
    assert report["target_index_status"] == "ALREADY_PROVISIONED"
    assert collection.create_calls == []


def test_incompatible_same_name_index_aborts():
    collection = FakeCollection(RECORDS, indexes=[{"name": provisioning.INDEX_NAME, "key": [("email", 1)], "unique": False}])
    with pytest.raises(provisioning.IndexConflictError):
        provisioning.execute(collection, "db")


def test_equivalent_different_name_exits_safely():
    collection = FakeCollection(RECORDS, indexes=[exact_index("legacy_email_unique")])
    report = apply(collection)
    assert report["target_index_status"] == "EQUIVALENT_INDEX_EXISTS"
    assert collection.create_calls == []


def test_conflicting_email_index_aborts():
    collection = FakeCollection(RECORDS, indexes=[{"name": "email_1", "key": [("email", 1)]}])
    with pytest.raises(provisioning.IndexConflictError):
        provisioning.execute(collection, "db")


def test_successful_apply_creates_once_with_exact_contract_and_verifies():
    collection = FakeCollection(RECORDS)
    report = apply(collection)
    assert collection.create_calls == [
        ([('email', 1)], {"name": "newsletter_email_unique", "unique": True, "sparse": False})
    ]
    assert report["status"] == "PROVISIONED"
    assert report["target_index_status"] == "ALREADY_PROVISIONED"
    assert collection.find_calls == 3
    assert collection.document_writes == []


def test_post_creation_index_verification_failure_is_detected():
    class BrokenIndexCollection(FakeCollection):
        def create_index(self, keys, **options):
            self.create_calls.append((keys, options))
    collection = BrokenIndexCollection(RECORDS)
    with pytest.raises(provisioning.VerificationError):
        apply(collection)


def test_post_creation_data_audit_failure_is_detected():
    malformed = [{"_id": 1, "email": "one@example.com"}, {"_id": 2, "email": " TWO@example.com"}]
    collection = FakeCollection(RECORDS, batches=[RECORDS, RECORDS, malformed])
    with pytest.raises(provisioning.AuditError):
        apply(collection)


def test_script_contains_no_subscriber_mutation_calls():
    source = Path(provisioning.__file__).read_text()
    for operation in ("insert_one(", "update_one(", "update_many(", "delete_one(", "delete_many("):
        assert operation not in source
