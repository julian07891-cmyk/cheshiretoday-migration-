import copy
import json
import uuid

import pytest
from pymongo.errors import OperationFailure

from backend.scripts import migrate_newsletter_management_ids as migration


UUID_1 = "123e4567-e89b-42d3-a456-426614174000"
UUID_2 = "123e4567-e89b-42d3-a456-426614174001"
UUID_3 = "123e4567-e89b-42d3-a456-426614174002"
UUID_4 = "123e4567-e89b-42d3-a456-426614174003"
EMAIL = "private-subscriber@example.invalid"


def record(record_id, management_id=migration.MISSING, version=migration.MISSING):
    result = {
        "_id": record_id,
        "id": f"legacy-{record_id}",
        "email": EMAIL,
        "active": True,
        "daily_brief": False,
        "weekly_roundup": True,
        "breaking_news": False,
        "categories": ["local"],
        "frequency": "daily",
        "preferences": {"category": "local"},
        "subscribed_at": "2026-01-01T00:00:00+00:00",
        "created_at": "2026-01-01T00:00:00+00:00",
        "unsubscribe_history": [{"at": "2026-02-01T00:00:00+00:00"}],
        "reactivation_history": [{"at": "2026-03-01T00:00:00+00:00"}],
        "signup_source": "website",
        "delivery_history": {"last": "2026-04-01T00:00:00+00:00"},
        "digest_history": [1, 2],
        "analytics": {"opens": 3},
    }
    if management_id is not migration.MISSING:
        result[migration.MANAGEMENT_ID_FIELD] = management_id
    if version is not migration.MISSING:
        result[migration.TOKEN_VERSION_FIELD] = version
    return result


class FakeRepository:
    def __init__(self, records):
        self.records = copy.deepcopy(records)
        self.write_calls = 0
        self.index_calls = 0
        self.conflict_ids = set()
        self.failed_ids = set()
        self.systemic_failure = False
        self.existing_index = None
        self.verify_calls = 0
        self.index_verify_calls = 0
        self.count_values = []
        self.verification_values = []

    def count(self):
        if self.count_values:
            return self.count_values.pop(0)
        return len(self.records)

    def scan(self, limit=None):
        result = sorted(copy.deepcopy(self.records), key=lambda item: item["_id"])
        return result if limit is None else result[:limit]

    def management_id_exists(self, management_id):
        return any(
            item.get(migration.MANAGEMENT_ID_FIELD) == management_id
            for item in self.records
        )

    @staticmethod
    def _matches(item, filters):
        for key, expected in filters.items():
            if isinstance(expected, dict) and "$exists" in expected:
                if (key in item) != expected["$exists"]:
                    return False
            elif item.get(key, migration.MISSING) != expected:
                return False
        return True

    def apply_batch(self, updates):
        self.write_calls += 1
        if self.systemic_failure:
            raise migration.DatabaseOperationError("Subscriber update batch failed.")
        modified = conflicts = failures = 0
        for update in updates:
            record_id = update.filter_document["_id"]
            if record_id in self.failed_ids:
                failures += 1
                continue
            target = next(item for item in self.records if item["_id"] == record_id)
            if record_id in self.conflict_ids or not self._matches(
                target, update.filter_document
            ):
                conflicts += 1
                continue
            assert set(update.set_document) <= migration.APPROVED_UPDATE_FIELDS
            target.update(update.set_document)
            modified += 1
        return migration.BulkApplyResult(modified, conflicts, failures)

    def verify(self):
        self.verify_calls += 1
        if self.verification_values:
            return self.verification_values.pop(0)
        records = self.scan()
        seen = set()
        duplicates = set()
        invalid_ids = invalid_versions = 0
        for item in records:
            management_id = item.get(
                migration.MANAGEMENT_ID_FIELD, migration.MISSING
            )
            if not migration.is_canonical_uuid4(management_id):
                invalid_ids += 1
            elif management_id in seen:
                duplicates.add(management_id)
            else:
                seen.add(management_id)
            if not migration.is_valid_token_version(
                item.get(migration.TOKEN_VERSION_FIELD, migration.MISSING)
            ):
                invalid_versions += 1
        return migration.VerificationResult(
            len(records), invalid_ids, len(duplicates), invalid_versions
        )

    def ensure_unique_index(self):
        self.index_calls += 1
        if self.existing_index == "conflicting":
            raise migration.IndexConflictError(
                "The newsletter management index definition conflicts."
            )
        return "already_valid" if self.existing_index == "exact" else "created"

    def verify_unique_index(self):
        self.index_verify_calls += 1
        if self.existing_index == "conflicting":
            raise migration.IndexConflictError(
                "The newsletter management index definition conflicts."
            )


class FakeIndexCollection:
    def __init__(
        self,
        indexes=None,
        *,
        creation_failure=False,
        created_index=None,
    ):
        self.indexes = copy.deepcopy(indexes or [])
        self.creation_failure = creation_failure
        self.created_index = created_index
        self.create_calls = []
        self.list_calls = 0

    def list_indexes(self):
        self.list_calls += 1
        return copy.deepcopy(self.indexes)

    def create_index(self, keys, **kwargs):
        self.create_calls.append((list(keys), dict(kwargs)))
        if self.creation_failure:
            raise OperationFailure("private database operation detail")
        if self.created_index is None:
            created = {
                "v": 2,
                "key": dict(keys),
                "name": kwargs["name"],
                "unique": kwargs["unique"],
            }
        else:
            created = copy.deepcopy(self.created_index)
        self.indexes.append(created)
        return kwargs["name"]


class IndexBackedFakeRepository(FakeRepository):
    def __init__(self, records, collection):
        super().__init__(records)
        self.index_adapter = migration.SubscriberRepository(collection)
        self.collection = collection

    def ensure_unique_index(self):
        self.index_calls += 1
        return self.index_adapter.ensure_unique_index()

    def verify_unique_index(self):
        self.index_verify_calls += 1
        self.index_adapter.verify_unique_index()


def uuid_factory(values):
    iterator = iter(values)
    return lambda: uuid.UUID(next(iterator))


def apply(repository, **kwargs):
    defaults = {
        "expected_count": repository.count(),
        "input_func": lambda _prompt: migration.CONFIRMATION_TEXT,
        "stdin_isatty": lambda: True,
        "uuid_factory": uuid_factory([UUID_2, UUID_3]),
    }
    defaults.update(kwargs)
    return migration.execute_apply(repository, **defaults)


@pytest.mark.parametrize("value", [UUID_1, UUID_2])
def test_canonical_uuid4_is_valid(value):
    assert migration.is_canonical_uuid4(value)


@pytest.mark.parametrize(
    "value",
    [
        UUID_1.upper(),
        UUID_1.replace("-", ""),
        "550e8400-e29b-11d4-a716-446655440000",
        "not-a-uuid",
        None,
    ],
)
def test_noncanonical_or_non_v4_management_id_is_invalid(value):
    assert not migration.is_canonical_uuid4(value)


@pytest.mark.parametrize("value", [1, 2, 99])
def test_positive_integer_token_version_is_valid(value):
    assert migration.is_valid_token_version(value)


@pytest.mark.parametrize("value", [0, -1, "1", True, False, None])
def test_invalid_token_version_is_rejected(value):
    assert not migration.is_valid_token_version(value)


def test_valid_record_is_unchanged_and_valid_version_is_preserved():
    plan = migration.plan_migration([record(1, UUID_1, 7)])
    assert not plan.records
    assert plan.statistics.already_valid == 1


@pytest.mark.parametrize(
    "management_id,malformed",
    [(migration.MISSING, False), (None, True), ("bad", True)],
)
def test_missing_null_or_malformed_id_is_planned(management_id, malformed):
    plan = migration.plan_migration([record(1, management_id, 1)])
    assert plan.records[0].assign_management_id
    assert plan.records[0].malformed_management_id is malformed


def test_lowercase_noncanonical_uuid_is_planned_for_replacement():
    noncanonical = UUID_1.replace("-", "")
    plan = migration.plan_migration([record(1, noncanonical, 1)])
    assert plan.records[0].assign_management_id
    assert plan.records[0].malformed_management_id


def test_duplicate_group_keeps_first_sorted_owner_and_repairs_later_records():
    plan = migration.plan_migration(
        [record(3, UUID_1, 1), record(1, UUID_1, 1), record(2, UUID_1, 1)]
    )
    assert [item.record_id for item in plan.records] == [2, 3]
    assert plan.statistics.duplicate_id_groups_found == 1
    assert plan.statistics.duplicate_id_records_repaired == 2


@pytest.mark.parametrize("version", [migration.MISSING, None, 0, "1", True])
def test_missing_or_invalid_version_is_planned_for_initialization(version):
    plan = migration.plan_migration([record(1, UUID_1, version)])
    assert plan.records[0].initialize_token_version


def test_prepared_update_contains_only_required_fields_and_observed_conditions():
    planned = migration.plan_migration([record(1, None, None)]).records[0]
    update = migration.prepare_update(planned, UUID_2)
    assert update.set_document == {
        migration.MANAGEMENT_ID_FIELD: UUID_2,
        migration.TOKEN_VERSION_FIELD: 1,
    }
    assert update.filter_document == {
        "_id": 1,
        migration.MANAGEMENT_ID_FIELD: None,
        migration.TOKEN_VERSION_FIELD: None,
    }


def test_missing_fields_use_exists_false_conditions():
    planned = migration.plan_migration([record(1)]).records[0]
    update = migration.prepare_update(planned, UUID_2)
    assert update.filter_document[migration.MANAGEMENT_ID_FIELD] == {
        "$exists": False
    }
    assert update.filter_document[migration.TOKEN_VERSION_FIELD] == {
        "$exists": False
    }


def test_dry_run_performs_zero_writes_uuids_and_indexes_and_is_stable():
    repository = FakeRepository([record(1), record(2, "bad", 0)])
    calls = {"uuid": 0}

    def unused_uuid():
        calls["uuid"] += 1
        return uuid.uuid4()

    first = migration.execute_dry_run(repository)
    second = migration.execute_dry_run(repository)
    assert first.public_dict() == second.public_dict()
    assert first.ids_assigned == 2
    assert first.versions_initialized == 2
    assert first.malformed_ids_found == 1
    assert first.final_missing_or_invalid_ids == 2
    assert first.final_invalid_versions == 2
    assert repository.write_calls == repository.index_calls == calls["uuid"] == 0


def test_dry_run_counts_duplicate_values_without_generating_replacements():
    repository = FakeRepository(
        [record(1, UUID_1, 1), record(2, UUID_1, 1)]
    )
    stats = migration.execute_dry_run(repository)
    assert stats.duplicate_id_groups_found == 1
    assert stats.duplicate_id_records_repaired == 1
    assert stats.final_duplicate_id_groups == 1
    assert stats.final_missing_or_invalid_ids == 0


def test_apply_assigns_repairs_initializes_and_preserves_valid_version():
    repository = FakeRepository(
        [record(1), record(2, "bad", 8), record(3, UUID_1, 0)]
    )
    stats = apply(
        repository,
        uuid_factory=uuid_factory([UUID_2, UUID_3]),
    )
    assert stats.ids_assigned == 2
    assert stats.versions_initialized == 2
    assert repository.records[1][migration.TOKEN_VERSION_FIELD] == 8
    assert repository.verify().is_clean


def test_apply_repairs_duplicate_and_is_idempotent_on_rerun():
    repository = FakeRepository(
        [record(1, UUID_1, 1), record(2, UUID_1, 1)]
    )
    first = apply(repository)
    second = apply(repository)
    assert first.duplicate_id_records_repaired == 1
    assert second.ids_assigned == second.versions_initialized == 0
    assert second.already_valid == 2


def test_generated_uuid_collision_is_retried():
    repository = FakeRepository([record(1, UUID_1, 1), record(2)])
    apply(
        repository,
        uuid_factory=uuid_factory([UUID_1, UUID_2]),
    )
    assert repository.records[1][migration.MANAGEMENT_ID_FIELD] == UUID_2


def test_conditional_update_conflict_is_counted_without_overwrite():
    repository = FakeRepository([record(1)])
    repository.conflict_ids.add(1)
    stats = apply(repository)
    assert stats.conditional_update_conflicts == 1
    assert stats.ids_assigned == 0
    assert stats.final_missing_or_invalid_ids == 1


def test_isolated_failed_update_is_counted_and_later_update_continues():
    repository = FakeRepository([record(1), record(2)])
    repository.failed_ids.add(1)
    stats = apply(repository)
    assert stats.failed_updates == 1
    assert migration.is_canonical_uuid4(
        repository.records[1][migration.MANAGEMENT_ID_FIELD]
    )


def test_systemic_failure_aborts_with_safe_error():
    repository = FakeRepository([record(1)])
    repository.systemic_failure = True
    with pytest.raises(
        migration.DatabaseOperationError, match="Subscriber update batch failed"
    ):
        apply(repository)


def test_partial_completion_can_be_rerun_safely():
    repository = FakeRepository([record(1), record(2)])
    repository.failed_ids.add(1)
    apply(repository)
    repository.failed_ids.clear()
    result = apply(repository, uuid_factory=uuid_factory([UUID_4]))
    assert result.ids_assigned == 1
    assert repository.verify().is_clean


def test_exact_index_is_created_only_after_clean_verification():
    collection = FakeIndexCollection()
    repository = IndexBackedFakeRepository([record(1)], collection)
    stats = apply(repository, create_index=True)
    assert repository.index_calls == 1
    assert repository.verify_calls == 2
    assert repository.index_verify_calls == 1
    assert stats.index_status == "created"
    assert collection.create_calls == [
        (
            [(migration.MANAGEMENT_ID_FIELD, migration.ASCENDING)],
            {
                "unique": True,
                "sparse": False,
                "name": migration.INDEX_NAME,
            },
        )
    ]


def test_index_is_not_created_when_conflicts_or_failures_remain():
    repository = FakeRepository([record(1)])
    repository.conflict_ids.add(1)
    stats = apply(repository, create_index=True)
    assert repository.index_calls == 0
    assert stats.index_status == "blocked"


def test_index_is_not_created_when_an_update_fails():
    repository = FakeRepository([record(1)])
    repository.failed_ids.add(1)
    stats = apply(repository, create_index=True)
    assert repository.index_calls == 0
    assert stats.failed_updates == 1
    assert stats.index_status == "blocked"


def test_existing_exact_index_is_accepted():
    collection = FakeIndexCollection(
        [
            {
                "v": 2,
                "key": {migration.MANAGEMENT_ID_FIELD: migration.ASCENDING},
                "name": migration.INDEX_NAME,
                "unique": True,
            }
        ]
    )
    repository = IndexBackedFakeRepository(
        [record(1, UUID_1, 1)], collection
    )
    assert apply(repository, create_index=True).index_status == "already_valid"
    assert not collection.create_calls
    assert repository.verify_calls == 2
    assert repository.index_verify_calls == 1


def test_conflicting_index_definition_aborts_without_replacement():
    collection = FakeIndexCollection(
        [
            {
                "v": 2,
                "key": {"different_field": migration.ASCENDING},
                "name": migration.INDEX_NAME,
                "unique": True,
            }
        ]
    )
    repository = IndexBackedFakeRepository(
        [record(1, UUID_1, 1)], collection
    )
    with pytest.raises(migration.IndexConflictError):
        apply(repository, create_index=True)
    assert not collection.create_calls


@pytest.mark.parametrize(
    "index_override",
    [
        {"partialFilterExpression": {"active": True}},
        {"sparse": True},
        {"hidden": True},
        {"key": {"different_field": migration.ASCENDING}},
        {"unique": False},
        {"collation": {"locale": "en"}},
        {"expireAfterSeconds": 3600},
    ],
)
def test_non_equivalent_named_indexes_are_rejected(index_override):
    index = {
        "v": 2,
        "key": {migration.MANAGEMENT_ID_FIELD: migration.ASCENDING},
        "name": migration.INDEX_NAME,
        "unique": True,
    }
    index.update(index_override)
    repository = migration.SubscriberRepository(FakeIndexCollection([index]))
    with pytest.raises(migration.IndexConflictError):
        repository.ensure_unique_index()


def test_exact_named_index_is_accepted_by_real_index_validator():
    collection = FakeIndexCollection(
        [
            {
                "v": 2,
                "key": {migration.MANAGEMENT_ID_FIELD: migration.ASCENDING},
                "name": migration.INDEX_NAME,
                "unique": True,
                "sparse": False,
            }
        ]
    )
    repository = migration.SubscriberRepository(collection)
    assert repository.ensure_unique_index() == "already_valid"
    repository.verify_unique_index()
    assert not collection.create_calls


def test_expected_keys_under_a_different_name_are_rejected():
    collection = FakeIndexCollection(
        [
            {
                "v": 2,
                "key": {migration.MANAGEMENT_ID_FIELD: migration.ASCENDING},
                "name": "different_name",
                "unique": True,
            }
        ]
    )
    with pytest.raises(migration.IndexConflictError):
        migration.SubscriberRepository(collection).ensure_unique_index()
    assert not collection.create_calls


def test_index_creation_failure_aborts_safely():
    collection = FakeIndexCollection(creation_failure=True)
    repository = IndexBackedFakeRepository(
        [record(1, UUID_1, 1)], collection
    )
    with pytest.raises(
        migration.DatabaseOperationError,
        match="Newsletter management index operation failed",
    ) as captured:
        apply(repository, create_index=True)
    assert "private database operation detail" not in str(captured.value)


def test_incorrect_index_definition_after_creation_aborts():
    collection = FakeIndexCollection(
        created_index={
            "v": 2,
            "key": {migration.MANAGEMENT_ID_FIELD: migration.ASCENDING},
            "name": migration.INDEX_NAME,
            "unique": True,
            "partialFilterExpression": {"active": True},
        }
    )
    repository = IndexBackedFakeRepository(
        [record(1, UUID_1, 1)], collection
    )
    with pytest.raises(migration.IndexConflictError):
        apply(repository, create_index=True)


def test_post_index_verification_failure_aborts():
    collection = FakeIndexCollection()
    repository = IndexBackedFakeRepository(
        [record(1, UUID_1, 1)], collection
    )
    repository.verification_values = [
        migration.VerificationResult(1, 0, 0, 0),
        migration.VerificationResult(1, 1, 0, 0),
    ]
    with pytest.raises(
        migration.MigrationError,
        match="Subscriber fields failed post-index verification",
    ):
        apply(repository, create_index=True)
    assert repository.verify_calls == 2


def test_subscriber_count_change_after_apply_aborts_without_success_result():
    repository = FakeRepository([record(1, UUID_1, 1)])
    repository.count_values = [1, 2]
    with pytest.raises(migration.MigrationError, match="Subscriber count changed"):
        migration.execute_apply(
            repository,
            expected_count=1,
            input_func=lambda _prompt: migration.CONFIRMATION_TEXT,
            stdin_isatty=lambda: True,
        )


def test_subscriber_count_change_after_index_creation_aborts():
    collection = FakeIndexCollection()
    repository = IndexBackedFakeRepository(
        [record(1, UUID_1, 1)], collection
    )
    repository.count_values = [1, 1, 2]
    with pytest.raises(
        migration.MigrationError,
        match="Subscriber count changed during post-index verification",
    ):
        migration.execute_apply(
            repository,
            expected_count=1,
            create_index=True,
            input_func=lambda _prompt: migration.CONFIRMATION_TEXT,
            stdin_isatty=lambda: True,
        )
    assert repository.verify_calls == 2


def test_parser_requires_exactly_one_mode():
    parser = migration.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])
    with pytest.raises(SystemExit):
        parser.parse_args(["--dry-run", "--apply"])


@pytest.mark.parametrize(
    "arguments",
    [
        ["--dry-run", "--batch-size", "0"],
        ["--dry-run", "--batch-size", "2001"],
        ["--dry-run", "--limit", "0"],
    ],
)
def test_parser_rejects_invalid_numeric_controls(arguments):
    with pytest.raises(SystemExit):
        migration.build_parser().parse_args(arguments)


def test_expected_count_is_required_for_apply():
    args = migration.build_parser().parse_args(["--apply"])
    with pytest.raises(migration.ConfigurationError):
        migration.validate_arguments(args)


@pytest.mark.parametrize(
    "arguments",
    [
        ["--dry-run", "--create-index"],
        ["--apply", "--expected-count", "1", "--limit", "1", "--create-index"],
    ],
)
def test_create_index_restrictions_are_enforced(arguments):
    args = migration.build_parser().parse_args(arguments)
    with pytest.raises(migration.ConfigurationError):
        migration.validate_arguments(args)


def test_expected_count_mismatch_aborts_before_confirmation_or_writes():
    repository = FakeRepository([record(1)])
    prompted = {"value": False}

    def input_func(_prompt):
        prompted["value"] = True
        return migration.CONFIRMATION_TEXT

    with pytest.raises(migration.ConfigurationError):
        migration.execute_apply(
            repository,
            expected_count=2,
            input_func=input_func,
            stdin_isatty=lambda: True,
        )
    assert not prompted["value"]
    assert repository.write_calls == 0


def test_confirmation_mismatch_and_noninteractive_apply_abort():
    repository = FakeRepository([record(1)])
    with pytest.raises(migration.ConfirmationError):
        migration.execute_apply(
            repository,
            expected_count=1,
            input_func=lambda _prompt: "wrong",
            stdin_isatty=lambda: True,
        )
    with pytest.raises(migration.ConfirmationError):
        migration.execute_apply(
            repository,
            expected_count=1,
            input_func=lambda _prompt: migration.CONFIRMATION_TEXT,
            stdin_isatty=lambda: False,
        )
    assert repository.write_calls == 0


def test_limited_apply_never_creates_index():
    repository = FakeRepository([record(1)])
    with pytest.raises(migration.ConfigurationError):
        migration.execute_apply(
            repository,
            expected_count=1,
            limit=1,
            create_index=True,
            input_func=lambda _prompt: migration.CONFIRMATION_TEXT,
            stdin_isatty=lambda: True,
        )
    assert repository.index_calls == 0
    assert repository.write_calls == 0


def test_protected_fields_remain_byte_for_byte_unchanged():
    repository = FakeRepository([record(1)])
    before = copy.deepcopy(repository.records[0])
    apply(repository)
    after = repository.records[0]
    for key, value in before.items():
        assert after[key] == value
    assert len(repository.records) == 1


def test_public_output_contains_only_aggregate_fields_and_no_sensitive_values():
    repository = FakeRepository([record(1)])
    output = json.dumps(migration.execute_dry_run(repository).public_dict())
    assert set(json.loads(output)) == {
        "mode",
        "scanned",
        "already_valid",
        "ids_assigned",
        "versions_initialized",
        "malformed_ids_found",
        "duplicate_id_groups_found",
        "duplicate_id_records_repaired",
        "conditional_update_conflicts",
        "failed_updates",
        "final_missing_or_invalid_ids",
        "final_duplicate_id_groups",
        "final_invalid_versions",
        "index_status",
    }
    assert EMAIL not in output
    assert UUID_1 not in output
    assert "legacy-1" not in output
    assert "category" not in output


def test_safe_errors_do_not_expose_raw_database_details():
    secret_detail = "mongodb://private-host/private-db?token=secret"
    try:
        raise RuntimeError(secret_detail)
    except RuntimeError as cause:
        error = migration.DatabaseOperationError("Subscriber scan failed.")
        error.__cause__ = cause
    assert secret_detail not in str(error)


def test_repository_index_definition_is_exact():
    collection = FakeIndexCollection()
    status = migration.SubscriberRepository(collection).ensure_unique_index()
    assert status == "created"
    assert collection.create_calls == [
        (
            [(migration.MANAGEMENT_ID_FIELD, migration.ASCENDING)],
            {
                "unique": True,
                "sparse": False,
                "name": migration.INDEX_NAME,
            },
        )
    ]
