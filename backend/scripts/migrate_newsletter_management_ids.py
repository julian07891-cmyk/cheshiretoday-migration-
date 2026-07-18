#!/usr/bin/env python3
"""Safely initialise newsletter subscriber management fields."""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from dotenv import load_dotenv
from pymongo import ASCENDING, MongoClient, UpdateOne
from pymongo.errors import BulkWriteError, PyMongoError


MANAGEMENT_ID_FIELD = "newsletter_management_id"
TOKEN_VERSION_FIELD = "newsletter_token_version"
APPROVED_UPDATE_FIELDS = frozenset({MANAGEMENT_ID_FIELD, TOKEN_VERSION_FIELD})
CONFIRMATION_TEXT = "APPLY NEWSLETTER MANAGEMENT MIGRATION"
DEFAULT_BATCH_SIZE = 250
MAX_BATCH_SIZE = 2000
INDEX_NAME = "newsletter_management_id_unique"
INDEX_KEYS = [(MANAGEMENT_ID_FIELD, ASCENDING)]
NON_SEMANTIC_INDEX_METADATA = frozenset(
    {"v", "key", "name", "ns", "unique", "sparse", "background"}
)
MISSING = object()


class MigrationError(Exception):
    """Base class for privacy-safe migration failures."""


class ConfigurationError(MigrationError):
    """Configuration or CLI validation failed."""


class ConfirmationError(MigrationError):
    """The apply confirmation was unavailable or incorrect."""


class DatabaseOperationError(MigrationError):
    """A database operation failed without exposing its payload."""


class IndexConflictError(MigrationError):
    """An existing index conflicts with the required definition."""


@dataclass(frozen=True)
class PlannedRecord:
    record_id: Any
    observed_management_id: Any = MISSING
    observed_token_version: Any = MISSING
    assign_management_id: bool = False
    initialize_token_version: bool = False
    malformed_management_id: bool = False
    duplicate_management_id: bool = False


@dataclass(frozen=True)
class PreparedUpdate:
    filter_document: Mapping[str, Any]
    set_document: Mapping[str, Any]
    assigns_management_id: bool
    initializes_token_version: bool
    repairs_duplicate_management_id: bool


@dataclass(frozen=True)
class BulkApplyResult:
    modified_count: int
    conditional_conflicts: int
    failed_updates: int


@dataclass(frozen=True)
class VerificationResult:
    subscriber_count: int
    missing_or_invalid_ids: int
    duplicate_id_groups: int
    invalid_versions: int

    @property
    def is_clean(self) -> bool:
        return (
            self.missing_or_invalid_ids == 0
            and self.duplicate_id_groups == 0
            and self.invalid_versions == 0
        )


@dataclass
class MigrationStatistics:
    mode: str
    scanned: int = 0
    already_valid: int = 0
    ids_assigned: int = 0
    versions_initialized: int = 0
    malformed_ids_found: int = 0
    duplicate_id_groups_found: int = 0
    duplicate_id_records_repaired: int = 0
    conditional_update_conflicts: int = 0
    failed_updates: int = 0
    final_missing_or_invalid_ids: int = 0
    final_duplicate_id_groups: int = 0
    final_invalid_versions: int = 0
    index_status: str = "not_requested"

    def public_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MigrationPlan:
    records: tuple[PlannedRecord, ...]
    statistics: MigrationStatistics


def is_canonical_uuid4(value: Any) -> bool:
    if not isinstance(value, str) or value != value.lower():
        return False
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError):
        return False
    return parsed.version == 4 and str(parsed) == value


def is_valid_token_version(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _sort_records(records: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    try:
        return sorted(records, key=lambda record: record["_id"])
    except (KeyError, TypeError) as exc:
        raise MigrationError("Subscriber scan could not be ordered safely.") from exc


def plan_migration(
    records: Iterable[Mapping[str, Any]], mode: str = "dry-run"
) -> MigrationPlan:
    ordered_records = _sort_records(records)
    seen_management_ids: set[str] = set()
    duplicate_groups: set[str] = set()
    planned: list[PlannedRecord] = []
    stats = MigrationStatistics(mode=mode, scanned=len(ordered_records))

    for record in ordered_records:
        observed_id = record.get(MANAGEMENT_ID_FIELD, MISSING)
        observed_version = record.get(TOKEN_VERSION_FIELD, MISSING)
        valid_id = is_canonical_uuid4(observed_id)
        duplicate_id = valid_id and observed_id in seen_management_ids
        malformed_id = observed_id is not MISSING and not valid_id
        assign_id = not valid_id or duplicate_id
        initialize_version = not is_valid_token_version(observed_version)

        if valid_id and not duplicate_id:
            seen_management_ids.add(observed_id)
        if duplicate_id:
            duplicate_groups.add(observed_id)
            stats.duplicate_id_records_repaired += 1
        if malformed_id:
            stats.malformed_ids_found += 1
        if assign_id:
            stats.ids_assigned += 1
        if initialize_version:
            stats.versions_initialized += 1
        if not assign_id and not initialize_version:
            stats.already_valid += 1

        if assign_id or initialize_version:
            planned.append(
                PlannedRecord(
                    record_id=record["_id"],
                    observed_management_id=observed_id,
                    observed_token_version=observed_version,
                    assign_management_id=assign_id,
                    initialize_token_version=initialize_version,
                    malformed_management_id=malformed_id,
                    duplicate_management_id=duplicate_id,
                )
            )

    stats.duplicate_id_groups_found = len(duplicate_groups)
    return MigrationPlan(records=tuple(planned), statistics=stats)


def _observed_field_filter(field: str, value: Any) -> dict[str, Any]:
    if value is MISSING:
        return {field: {"$exists": False}}
    return {field: value}


def prepare_update(
    planned: PlannedRecord, replacement_management_id: str | None = None
) -> PreparedUpdate:
    update_filter: dict[str, Any] = {"_id": planned.record_id}
    set_document: dict[str, Any] = {}

    if planned.assign_management_id:
        if not is_canonical_uuid4(replacement_management_id):
            raise MigrationError("A generated management identifier was invalid.")
        update_filter.update(
            _observed_field_filter(MANAGEMENT_ID_FIELD, planned.observed_management_id)
        )
        set_document[MANAGEMENT_ID_FIELD] = replacement_management_id

    if planned.initialize_token_version:
        update_filter.update(
            _observed_field_filter(
                TOKEN_VERSION_FIELD, planned.observed_token_version
            )
        )
        set_document[TOKEN_VERSION_FIELD] = 1

    if not set_document or not set(set_document).issubset(APPROVED_UPDATE_FIELDS):
        raise MigrationError("An unsafe migration update was rejected.")

    return PreparedUpdate(
        filter_document=update_filter,
        set_document=set_document,
        assigns_management_id=planned.assign_management_id,
        initializes_token_version=planned.initialize_token_version,
        repairs_duplicate_management_id=planned.duplicate_management_id,
    )


class SubscriberRepository:
    """Narrow synchronous PyMongo adapter used by the migration executor."""

    def __init__(self, collection: Any):
        self.collection = collection

    def count(self) -> int:
        try:
            return int(self.collection.count_documents({}))
        except PyMongoError as exc:
            raise DatabaseOperationError("Subscriber count failed.") from exc

    def scan(self, limit: int | None = None) -> list[dict[str, Any]]:
        projection = {
            "_id": 1,
            MANAGEMENT_ID_FIELD: 1,
            TOKEN_VERSION_FIELD: 1,
        }
        try:
            cursor = self.collection.find({}, projection).sort("_id", ASCENDING)
            if limit is not None:
                cursor = cursor.limit(limit)
            return list(cursor)
        except PyMongoError as exc:
            raise DatabaseOperationError("Subscriber scan failed.") from exc

    def management_id_exists(self, management_id: str) -> bool:
        try:
            return (
                self.collection.count_documents(
                    {MANAGEMENT_ID_FIELD: management_id}, limit=1
                )
                > 0
            )
        except PyMongoError as exc:
            raise DatabaseOperationError(
                "Management identifier collision check failed."
            ) from exc

    def apply_batch(self, updates: Sequence[PreparedUpdate]) -> BulkApplyResult:
        operations = [
            UpdateOne(
                dict(update.filter_document),
                {"$set": dict(update.set_document)},
            )
            for update in updates
        ]
        try:
            result = self.collection.bulk_write(operations, ordered=False)
            modified = int(result.modified_count)
            return BulkApplyResult(
                modified_count=modified,
                conditional_conflicts=len(updates) - modified,
                failed_updates=0,
            )
        except BulkWriteError as exc:
            details = exc.details or {}
            if details.get("writeConcernErrors"):
                raise DatabaseOperationError(
                    "Subscriber update batch failed systemically."
                ) from exc
            failed = len(details.get("writeErrors", []))
            modified = int(details.get("nModified", 0))
            conflicts = max(0, len(updates) - modified - failed)
            return BulkApplyResult(
                modified_count=modified,
                conditional_conflicts=conflicts,
                failed_updates=failed,
            )
        except PyMongoError as exc:
            raise DatabaseOperationError("Subscriber update batch failed.") from exc

    def verify(self) -> VerificationResult:
        records = self.scan()
        seen: set[str] = set()
        duplicate_groups: set[str] = set()
        invalid_ids = 0
        invalid_versions = 0
        for record in records:
            management_id = record.get(MANAGEMENT_ID_FIELD, MISSING)
            if not is_canonical_uuid4(management_id):
                invalid_ids += 1
            elif management_id in seen:
                duplicate_groups.add(management_id)
            else:
                seen.add(management_id)
            if not is_valid_token_version(record.get(TOKEN_VERSION_FIELD, MISSING)):
                invalid_versions += 1
        return VerificationResult(
            subscriber_count=len(records),
            missing_or_invalid_ids=invalid_ids,
            duplicate_id_groups=len(duplicate_groups),
            invalid_versions=invalid_versions,
        )

    def _find_named_index(self) -> Mapping[str, Any] | None:
        try:
            for index in self.collection.list_indexes():
                if index.get("name") == INDEX_NAME:
                    return index
                if list(index.get("key", {}).items()) == INDEX_KEYS:
                    raise IndexConflictError(
                        "The newsletter management index definition conflicts."
                    )
            return None
        except IndexConflictError:
            raise
        except PyMongoError as exc:
            raise DatabaseOperationError(
                "Newsletter management index inspection failed."
            ) from exc

    @staticmethod
    def _is_exact_unique_index(index: Mapping[str, Any]) -> bool:
        return (
            index.get("name") == INDEX_NAME
            and list(index.get("key", {}).items()) == INDEX_KEYS
            and index.get("unique") is True
            and index.get("sparse", False) is False
            and set(index).issubset(NON_SEMANTIC_INDEX_METADATA)
        )

    def verify_unique_index(self) -> None:
        index = self._find_named_index()
        if index is None or not self._is_exact_unique_index(index):
            raise IndexConflictError(
                "The newsletter management index definition conflicts."
            )

    def ensure_unique_index(self) -> str:
        existing = self._find_named_index()
        if existing is not None:
            if not self._is_exact_unique_index(existing):
                raise IndexConflictError(
                    "The newsletter management index definition conflicts."
                )
            return "already_valid"
        try:
            self.collection.create_index(
                INDEX_KEYS,
                unique=True,
                sparse=False,
                name=INDEX_NAME,
            )
        except PyMongoError as exc:
            raise DatabaseOperationError(
                "Newsletter management index operation failed."
            ) from exc
        self.verify_unique_index()
        return "created"


def _new_unique_management_id(
    repository: Any,
    reserved: set[str],
    uuid_factory: Callable[[], Any],
) -> str:
    for _ in range(100):
        candidate = str(uuid_factory())
        if (
            is_canonical_uuid4(candidate)
            and candidate not in reserved
            and not repository.management_id_exists(candidate)
        ):
            reserved.add(candidate)
            return candidate
    raise MigrationError("A unique management identifier could not be generated.")


def execute_dry_run(repository: Any, limit: int | None = None) -> MigrationStatistics:
    plan = plan_migration(repository.scan(limit), mode="dry-run")
    plan.statistics.final_missing_or_invalid_ids = (
        plan.statistics.ids_assigned
        - plan.statistics.duplicate_id_records_repaired
    )
    plan.statistics.final_duplicate_id_groups = (
        plan.statistics.duplicate_id_groups_found
    )
    plan.statistics.final_invalid_versions = plan.statistics.versions_initialized
    return plan.statistics


def execute_apply(
    repository: Any,
    *,
    expected_count: int,
    batch_size: int = DEFAULT_BATCH_SIZE,
    limit: int | None = None,
    create_index: bool = False,
    uuid_factory: Callable[[], Any] = uuid.uuid4,
    input_func: Callable[[str], str] = input,
    stdin_isatty: Callable[[], bool] | None = None,
) -> MigrationStatistics:
    if create_index and limit is not None:
        raise ConfigurationError(
            "Index creation is prohibited for a limited migration."
        )
    initial_count = repository.count()
    if initial_count != expected_count:
        raise ConfigurationError(
            "Expected subscriber count did not match; no updates were attempted."
        )
    if stdin_isatty is None:
        stdin_isatty = sys.stdin.isatty
    if not stdin_isatty():
        raise ConfirmationError(
            "Interactive confirmation is required; no updates were attempted."
        )
    if input_func("Type the exact migration confirmation: ") != CONFIRMATION_TEXT:
        raise ConfirmationError(
            "Migration confirmation did not match; no updates were attempted."
        )

    records = repository.scan(limit)
    plan = plan_migration(records, mode="apply")
    stats = plan.statistics
    stats.ids_assigned = 0
    stats.versions_initialized = 0
    stats.duplicate_id_records_repaired = 0
    reserved = {
        record[MANAGEMENT_ID_FIELD]
        for record in records
        if is_canonical_uuid4(record.get(MANAGEMENT_ID_FIELD))
    }
    prepared_groups: dict[tuple[bool, bool, bool], list[PreparedUpdate]] = {}

    for planned in plan.records:
        replacement = None
        if planned.assign_management_id:
            replacement = _new_unique_management_id(
                repository, reserved, uuid_factory
            )
        update = prepare_update(planned, replacement)
        group_key = (
            update.assigns_management_id,
            update.initializes_token_version,
            update.repairs_duplicate_management_id,
        )
        prepared_groups.setdefault(group_key, []).append(update)

    for group_key, updates in prepared_groups.items():
        assigns_id, initializes_version, repairs_duplicate = group_key
        for start in range(0, len(updates), batch_size):
            batch = updates[start : start + batch_size]
            result = repository.apply_batch(batch)
            stats.conditional_update_conflicts += result.conditional_conflicts
            stats.failed_updates += result.failed_updates
            if assigns_id:
                stats.ids_assigned += result.modified_count
            if initializes_version:
                stats.versions_initialized += result.modified_count
            if repairs_duplicate:
                stats.duplicate_id_records_repaired += result.modified_count

    verification = repository.verify()
    final_count = repository.count()
    if final_count != initial_count:
        raise MigrationError("Subscriber count changed during migration.")
    stats.final_missing_or_invalid_ids = verification.missing_or_invalid_ids
    stats.final_duplicate_id_groups = verification.duplicate_id_groups
    stats.final_invalid_versions = verification.invalid_versions

    clean = (
        verification.is_clean
        and stats.conditional_update_conflicts == 0
        and stats.failed_updates == 0
    )
    if create_index:
        if not clean:
            stats.index_status = "blocked"
        else:
            stats.index_status = repository.ensure_unique_index()
            post_index_verification = repository.verify()
            post_index_count = repository.count()
            if post_index_count != initial_count:
                raise MigrationError(
                    "Subscriber count changed during post-index verification."
                )
            if not post_index_verification.is_clean:
                raise MigrationError(
                    "Subscriber fields failed post-index verification."
                )
            repository.verify_unique_index()
    return stats


def positive_integer(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("A positive integer is required.") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("A positive integer is required.")
    return parsed


def batch_size(value: str) -> int:
    parsed = positive_integer(value)
    if parsed > MAX_BATCH_SIZE:
        raise argparse.ArgumentTypeError(
            f"Batch size must not exceed {MAX_BATCH_SIZE}."
        )
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Initialise newsletter subscriber management fields safely."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--batch-size", type=batch_size, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--limit", type=positive_integer)
    parser.add_argument("--expected-count", type=positive_integer)
    parser.add_argument("--create-index", action="store_true")
    return parser


def validate_arguments(args: argparse.Namespace) -> None:
    if args.apply and args.expected_count is None:
        raise ConfigurationError("--expected-count is required with --apply.")
    if args.dry_run and args.expected_count is not None:
        raise ConfigurationError("--expected-count is only valid with --apply.")
    if args.create_index and not args.apply:
        raise ConfigurationError("--create-index requires --apply.")
    if args.create_index and args.limit is not None:
        raise ConfigurationError("--create-index is prohibited with --limit.")


def create_repository_from_environment() -> SubscriberRepository:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    mongo_url = os.environ.get("MONGO_URL")
    database_name = os.environ.get("DB_NAME")
    if not mongo_url or not database_name:
        raise ConfigurationError("Required database configuration is unavailable.")
    try:
        client = MongoClient(mongo_url, serverSelectionTimeoutMS=10000)
        client.admin.command("ping")
        return SubscriberRepository(client[database_name]["subscribers"])
    except PyMongoError as exc:
        raise DatabaseOperationError("Database connection failed.") from exc


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        validate_arguments(args)
        repository = create_repository_from_environment()
        if args.dry_run:
            stats = execute_dry_run(repository, limit=args.limit)
        else:
            stats = execute_apply(
                repository,
                expected_count=args.expected_count,
                batch_size=args.batch_size,
                limit=args.limit,
                create_index=args.create_index,
            )
        print(json.dumps(stats.public_dict(), sort_keys=True))
        if (
            args.apply
            and (
                stats.conditional_update_conflicts
                or stats.failed_updates
                or stats.final_missing_or_invalid_ids
                or stats.final_duplicate_id_groups
                or stats.final_invalid_versions
            )
        ):
            return 2
        return 0
    except MigrationError as exc:
        print(f"Migration failed safely: {exc}", file=sys.stderr)
        return 1
    except Exception:
        print("Migration failed safely due to an unexpected error.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
