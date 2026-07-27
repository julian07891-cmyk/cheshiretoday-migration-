#!/usr/bin/env python3
"""Audit and safely provision the canonical newsletter email unique index."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from dotenv import load_dotenv
from pymongo import ASCENDING, MongoClient
from pymongo.errors import PyMongoError


COLLECTION_NAME = "subscribers"
INDEX_NAME = "newsletter_email_unique"
INDEX_KEYS = (("email", ASCENDING),)
CONFIRMATION_TEXT = "CREATE UNIQUE NEWSLETTER EMAIL INDEX"


class ProvisioningError(Exception):
    """Base class for privacy-safe provisioning failures."""


class ConfigurationError(ProvisioningError):
    pass


class ConfirmationError(ProvisioningError):
    pass


class AuditError(ProvisioningError):
    pass


class DriftError(ProvisioningError):
    pass


class IndexConflictError(ProvisioningError):
    pass


class VerificationError(ProvisioningError):
    pass


@dataclass(frozen=True)
class Audit:
    database: str
    collection: str
    total_records: int
    missing_email: int
    empty_email: int
    non_string_email: int
    whitespace_padded_email: int
    uppercase_email: int
    malformed_record_count: int
    unique_raw_emails: int
    unique_normalised_emails: int
    duplicate_groups: tuple[dict[str, Any], ...]
    snapshot: tuple[tuple[Any, str], ...]

    @property
    def malformed_records(self) -> int:
        return self.malformed_record_count


def normalise_email(value: Any) -> str:
    """Match the canonical production write contract exactly."""

    return str(value).strip().lower()


def _ordered_documents(collection: Any) -> tuple[Mapping[str, Any], ...]:
    cursor = collection.find({}, {"_id": 1, "email": 1})
    try:
        cursor = cursor.sort([("_id", ASCENDING)])
    except TypeError:
        cursor = cursor.sort("_id", ASCENDING)
    return tuple(cursor)


def audit_collection(collection: Any, database_name: str) -> Audit:
    documents = _ordered_documents(collection)
    missing = empty = non_string = padded = uppercase = 0
    raw_values: set[str] = set()
    normalised_groups: dict[str, list[Any]] = {}
    snapshot: list[tuple[Any, str]] = []
    malformed_positions: set[int] = set()

    for position, document in enumerate(documents):
        if "email" not in document:
            missing += 1
            malformed_positions.add(position)
            continue
        value = document["email"]
        if not isinstance(value, str):
            non_string += 1
            malformed_positions.add(position)
            continue
        if value == "":
            empty += 1
            malformed_positions.add(position)
            continue
        if value != value.strip():
            padded += 1
            malformed_positions.add(position)
        if any(character.isupper() for character in value):
            uppercase += 1
            malformed_positions.add(position)
        canonical = normalise_email(value)
        raw_values.add(value)
        normalised_groups.setdefault(canonical, []).append(document.get("_id"))
        snapshot.append((document.get("_id"), canonical))

    duplicate_groups = tuple(
        {
            "email_hash_prefix": hashlib.sha256(email.encode("utf-8")).hexdigest()[:12],
            "group_size": len(ids),
        }
        for email, ids in sorted(normalised_groups.items())
        if len(ids) > 1
    )
    return Audit(
        database=database_name,
        collection=COLLECTION_NAME,
        total_records=len(documents),
        missing_email=missing,
        empty_email=empty,
        non_string_email=non_string,
        whitespace_padded_email=padded,
        uppercase_email=uppercase,
        malformed_record_count=len(malformed_positions),
        unique_raw_emails=len(raw_values),
        unique_normalised_emails=len(normalised_groups),
        duplicate_groups=duplicate_groups,
        snapshot=tuple(snapshot),
    )


def _normalise_keys(metadata: Mapping[str, Any]) -> tuple[tuple[str, int], ...]:
    keys = metadata.get("key", ())
    return tuple(keys.items()) if isinstance(keys, Mapping) else tuple(tuple(item) for item in keys)


def _is_exact_unique_email_index(metadata: Mapping[str, Any]) -> bool:
    return (
        _normalise_keys(metadata) == INDEX_KEYS
        and metadata.get("unique") is True
        and metadata.get("sparse", False) is False
        and "partialFilterExpression" not in metadata
        and "collation" not in metadata
    )


def assess_indexes(indexes: Sequence[Mapping[str, Any]]) -> tuple[str, tuple[dict[str, Any], ...]]:
    inventory = tuple(
        {
            "name": item.get("name"),
            "key": list(_normalise_keys(item)),
            "unique": item.get("unique", False),
            "sparse": item.get("sparse", False),
            "partial": "partialFilterExpression" in item,
        }
        for item in indexes
    )
    named = [item for item in indexes if item.get("name") == INDEX_NAME]
    if named:
        if len(named) == 1 and _is_exact_unique_email_index(named[0]):
            return "ALREADY_PROVISIONED", inventory
        raise IndexConflictError("The target index exists with incompatible options.")

    email_indexes = [
        item for item in indexes if _normalise_keys(item) == INDEX_KEYS
    ]
    equivalent = [item for item in email_indexes if _is_exact_unique_email_index(item)]
    if equivalent:
        return "EQUIVALENT_INDEX_EXISTS", inventory
    if email_indexes:
        raise IndexConflictError("A conflicting email index blocks provisioning.")
    return "MISSING", inventory


def _assert_audit_safe(audit: Audit) -> None:
    if audit.malformed_records:
        raise AuditError("Malformed subscriber email records block provisioning.")
    if audit.unique_raw_emails != audit.unique_normalised_emails:
        raise AuditError("Raw and normalised email counts differ.")
    if audit.duplicate_groups:
        raise AuditError("Duplicate normalised email groups block provisioning.")


def _public_report(audit: Audit, indexes: tuple[dict[str, Any], ...], status: str) -> dict[str, Any]:
    report = asdict(audit)
    report.pop("snapshot")
    report["malformed_records"] = audit.malformed_records
    report["duplicate_group_count"] = len(audit.duplicate_groups)
    report["existing_indexes"] = indexes
    report["target_index_status"] = status
    report["apply_safe"] = (
        audit.malformed_records == 0
        and audit.unique_raw_emails == audit.unique_normalised_emails
        and not audit.duplicate_groups
        and status in {"MISSING", "ALREADY_PROVISIONED", "EQUIVALENT_INDEX_EXISTS"}
    )
    return report


def execute(
    collection: Any,
    database_name: str,
    *,
    apply: bool = False,
    expected_count: int | None = None,
    stdin_isatty: Callable[[], bool] = sys.stdin.isatty,
    input_func: Callable[[str], str] = input,
) -> dict[str, Any]:
    if apply and expected_count is None:
        raise ConfirmationError("--expected-count is required for apply.")
    if apply and stdin_isatty() is not True:
        raise ConfirmationError("Interactive TTY confirmation is required.")

    preflight = audit_collection(collection, database_name)
    status, inventory = assess_indexes(tuple(collection.list_indexes()))
    report = _public_report(preflight, inventory, status)
    if status in {"ALREADY_PROVISIONED", "EQUIVALENT_INDEX_EXISTS"}:
        report["mode"] = "apply" if apply else "dry-run"
        return report
    _assert_audit_safe(preflight)

    if not apply:
        report["mode"] = "dry-run"
        return report
    if expected_count != preflight.total_records:
        raise DriftError("Expected subscriber count does not match preflight.")
    if input_func("Type the exact index confirmation: ") != CONFIRMATION_TEXT:
        raise ConfirmationError("Index confirmation did not match.")

    final_scan = audit_collection(collection, database_name)
    _assert_audit_safe(final_scan)
    if final_scan.total_records != expected_count:
        raise DriftError("Subscriber collection count changed before apply.")
    if final_scan.snapshot != preflight.snapshot:
        raise DriftError("Ordered subscriber ID/email snapshot changed before apply.")
    final_status, _ = assess_indexes(tuple(collection.list_indexes()))
    if final_status != "MISSING":
        raise DriftError("Index inventory changed before apply.")

    collection.create_index(
        list(INDEX_KEYS),
        name=INDEX_NAME,
        unique=True,
        sparse=False,
    )
    verified_status, verified_inventory = assess_indexes(tuple(collection.list_indexes()))
    if verified_status != "ALREADY_PROVISIONED":
        raise VerificationError("Created index verification failed.")
    post_audit = audit_collection(collection, database_name)
    _assert_audit_safe(post_audit)
    if post_audit.snapshot != final_scan.snapshot:
        raise VerificationError("Subscriber data changed during index creation.")

    result = _public_report(post_audit, verified_inventory, "ALREADY_PROVISIONED")
    result.update({"mode": "apply", "status": "PROVISIONED"})
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit and provision the newsletter subscriber email unique index."
    )
    parser.add_argument("--apply", action="store_true", help="Create the reviewed index after all safeguards pass.")
    parser.add_argument("--expected-count", type=int, help="Exact subscriber count approved from the dry-run.")
    return parser


def _collection_from_environment(client_factory: Callable[..., Any] = MongoClient) -> tuple[Any, str]:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    mongo_url = os.environ.get("MONGO_URL")
    database_name = os.environ.get("DB_NAME")
    if not mongo_url or not database_name:
        raise ConfigurationError("Required database configuration is unavailable.")
    try:
        client = client_factory(mongo_url, serverSelectionTimeoutMS=10000)
        client.admin.command("ping")
        return client[database_name][COLLECTION_NAME], database_name
    except PyMongoError as exc:
        raise ConfigurationError("Database connection failed safely.") from exc


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        if args.apply and args.expected_count is None:
            raise ConfirmationError("--expected-count is required for apply.")
        if args.apply and not sys.stdin.isatty():
            raise ConfirmationError("Interactive TTY confirmation is required.")
        collection, database_name = _collection_from_environment()
        result = execute(
            collection,
            database_name,
            apply=args.apply,
            expected_count=args.expected_count,
        )
        print(json.dumps(result, sort_keys=True, default=str))
        return 0
    except ProvisioningError as exc:
        print(f"Index provisioning failed safely: {exc}", file=sys.stderr)
        return 1
    except Exception:
        print("Index provisioning failed safely due to an unexpected error.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
