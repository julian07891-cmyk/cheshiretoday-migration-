#!/usr/bin/env python3
"""Provision the reviewed newsletter link indexes with explicit safeguards."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError


CONFIRMATION_TEXT = "APPLY NEWSLETTER LINK INDEXES"
CHALLENGE_COLLECTION = "newsletter_link_challenges"
RATE_LIMIT_COLLECTION = "newsletter_link_request_limits"


class ProvisioningError(Exception):
    """Base class for privacy-safe provisioning failures."""


class ConfigurationError(ProvisioningError):
    """Required configuration or CLI state is unavailable."""


class ConfirmationError(ProvisioningError):
    """Interactive apply confirmation was unavailable or incorrect."""


class DatabaseOperationError(ProvisioningError):
    """A database operation failed without exposing its payload."""


class IndexConflictError(ProvisioningError):
    """An existing index conflicts with the reviewed definition."""


class VerificationError(ProvisioningError):
    """Post-creation verification did not prove all indexes exact."""


@dataclass(frozen=True)
class IndexDefinition:
    collection_name: str
    name: str
    keys: tuple[tuple[str, int], ...]
    unique: bool = False
    expire_after_seconds: int | None = None


INDEX_DEFINITIONS = (
    IndexDefinition(
        collection_name=CHALLENGE_COLLECTION,
        name="newsletter_link_challenge_token_hash_unique",
        keys=(("token_hash", 1),),
        unique=True,
    ),
    IndexDefinition(
        collection_name=CHALLENGE_COLLECTION,
        name="newsletter_link_challenge_ttl",
        keys=(("expires_at", 1),),
        expire_after_seconds=0,
    ),
    IndexDefinition(
        collection_name=RATE_LIMIT_COLLECTION,
        name="newsletter_link_request_limit_unique",
        keys=(("dimension", 1), ("hash", 1), ("operation", 1)),
        unique=True,
    ),
    IndexDefinition(
        collection_name=RATE_LIMIT_COLLECTION,
        name="newsletter_link_request_limit_ttl",
        keys=(("expires_at", 1),),
        expire_after_seconds=0,
    ),
)

SAFE_METADATA_FIELDS = frozenset(
    {
        "v",
        "key",
        "name",
        "ns",
        "background",
        "unique",
        "sparse",
        "partialFilterExpression",
        "hidden",
        "collation",
        "expireAfterSeconds",
    }
)


@dataclass(frozen=True)
class IndexAssessment:
    exact_existing: int
    missing: int
    conflicting: int
    missing_definitions: tuple[IndexDefinition, ...]

    @property
    def is_exact(self) -> bool:
        return (
            self.exact_existing == len(INDEX_DEFINITIONS)
            and self.missing == 0
            and self.conflicting == 0
        )


@dataclass(frozen=True)
class ProvisioningStatistics:
    mode: str
    target_indexes: int
    exact_existing: int
    missing: int
    conflicting: int
    created: int
    verified_exact: int
    status: str

    def public_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalise_keys(metadata: Mapping[str, Any]) -> tuple[tuple[str, int], ...]:
    raw_keys = metadata.get("key")
    if isinstance(raw_keys, Mapping):
        items = tuple(raw_keys.items())
    elif isinstance(raw_keys, Sequence) and not isinstance(
        raw_keys, (str, bytes)
    ):
        items = tuple(raw_keys)
    else:
        raise IndexConflictError("Index definition conflicts.")

    normalised: list[tuple[str, int]] = []
    for item in items:
        if (
            not isinstance(item, Sequence)
            or isinstance(item, (str, bytes))
            or len(item) != 2
        ):
            raise IndexConflictError("Index definition conflicts.")
        key, direction = item
        if (
            not isinstance(key, str)
            or type(direction) is not int
            or direction not in {-1, 1}
        ):
            raise IndexConflictError("Index definition conflicts.")
        normalised.append((key, direction))
    return tuple(normalised)


def validate_exact_index(
    metadata: Mapping[str, Any],
    expected: IndexDefinition,
) -> None:
    """Reject any semantic or type difference from the reviewed definition."""

    try:
        if metadata.get("name") != expected.name:
            raise IndexConflictError("Index definition conflicts.")
        if _normalise_keys(metadata) != expected.keys:
            raise IndexConflictError("Index definition conflicts.")

        if expected.unique:
            if metadata.get("unique") is not True:
                raise IndexConflictError("Index definition conflicts.")
        elif "unique" in metadata and metadata["unique"] is not False:
            raise IndexConflictError("Index definition conflicts.")

        if expected.expire_after_seconds is None:
            if "expireAfterSeconds" in metadata:
                raise IndexConflictError("Index definition conflicts.")
        elif (
            type(metadata.get("expireAfterSeconds")) is not int
            or metadata["expireAfterSeconds"]
            != expected.expire_after_seconds
        ):
            raise IndexConflictError("Index definition conflicts.")

        for option in ("sparse", "hidden"):
            if option in metadata and metadata[option] is not False:
                raise IndexConflictError("Index definition conflicts.")
        if "partialFilterExpression" in metadata:
            raise IndexConflictError("Index definition conflicts.")
        if "collation" in metadata:
            raise IndexConflictError("Index definition conflicts.")
        if any(key not in SAFE_METADATA_FIELDS for key in metadata):
            raise IndexConflictError("Index definition conflicts.")
    except IndexConflictError:
        raise
    except Exception as exc:
        raise IndexConflictError("Index definition conflicts.") from exc


class NewsletterLinkIndexRepository:
    """Synchronous adapter over the two approved collections."""

    def __init__(self, database: Any) -> None:
        self._collections = {
            CHALLENGE_COLLECTION: database[CHALLENGE_COLLECTION],
            RATE_LIMIT_COLLECTION: database[RATE_LIMIT_COLLECTION],
        }

    def discover(self, collection_name: str) -> tuple[Mapping[str, Any], ...]:
        try:
            return tuple(self._collections[collection_name].list_indexes())
        except Exception as exc:
            raise DatabaseOperationError(
                "Index discovery failed safely."
            ) from exc

    def create(self, definition: IndexDefinition) -> None:
        options: dict[str, Any] = {
            "name": definition.name,
            "unique": definition.unique,
            "sparse": False,
        }
        if definition.expire_after_seconds is not None:
            options["expireAfterSeconds"] = definition.expire_after_seconds
        try:
            self._collections[definition.collection_name].create_index(
                list(definition.keys),
                **options,
            )
        except Exception as exc:
            raise DatabaseOperationError(
                "Index creation failed safely."
            ) from exc


def _metadata_keys_or_none(
    metadata: Mapping[str, Any],
) -> tuple[tuple[str, int], ...] | None:
    try:
        return _normalise_keys(metadata)
    except IndexConflictError:
        return None


def assess_indexes(repository: Any) -> IndexAssessment:
    discovered = {
        collection_name: repository.discover(collection_name)
        for collection_name in (CHALLENGE_COLLECTION, RATE_LIMIT_COLLECTION)
    }
    exact = 0
    missing: list[IndexDefinition] = []
    conflicting = 0

    for expected in INDEX_DEFINITIONS:
        indexes = discovered[expected.collection_name]
        named = [
            metadata
            for metadata in indexes
            if metadata.get("name") == expected.name
        ]
        same_keys = [
            metadata
            for metadata in indexes
            if _metadata_keys_or_none(metadata) == expected.keys
            and metadata.get("name") != "_id_"
        ]

        if len(named) != 1:
            if named or same_keys:
                conflicting += 1
            else:
                missing.append(expected)
            continue

        try:
            validate_exact_index(named[0], expected)
            if any(item is not named[0] for item in same_keys):
                raise IndexConflictError("Index definition conflicts.")
        except IndexConflictError:
            conflicting += 1
        else:
            exact += 1

    return IndexAssessment(
        exact_existing=exact,
        missing=len(missing),
        conflicting=conflicting,
        missing_definitions=tuple(missing),
    )


def execute_dry_run(repository: Any) -> ProvisioningStatistics:
    assessment = assess_indexes(repository)
    status = "conflicts_found" if assessment.conflicting else "inspected"
    return ProvisioningStatistics(
        mode="dry-run",
        target_indexes=len(INDEX_DEFINITIONS),
        exact_existing=assessment.exact_existing,
        missing=assessment.missing,
        conflicting=assessment.conflicting,
        created=0,
        verified_exact=assessment.exact_existing,
        status=status,
    )


def require_apply_confirmation(
    *,
    input_func: Callable[[str], str] = input,
    stdin_isatty: Callable[[], bool] | None = None,
) -> None:
    isatty = stdin_isatty or sys.stdin.isatty
    if isatty() is not True:
        raise ConfirmationError("Interactive confirmation is required.")
    if input_func("Type the exact index confirmation: ") != CONFIRMATION_TEXT:
        raise ConfirmationError("Index confirmation did not match.")


def execute_apply(
    repository: Any,
    *,
    input_func: Callable[[str], str] = input,
    stdin_isatty: Callable[[], bool] | None = None,
) -> ProvisioningStatistics:
    require_apply_confirmation(
        input_func=input_func,
        stdin_isatty=stdin_isatty,
    )
    return _execute_confirmed_apply(repository)


def _execute_confirmed_apply(repository: Any) -> ProvisioningStatistics:
    initial = assess_indexes(repository)
    if initial.conflicting:
        raise IndexConflictError(
            "Conflicting index definitions block provisioning."
        )

    created = 0
    for definition in initial.missing_definitions:
        repository.create(definition)
        created += 1
        rediscovered = assess_indexes(repository)
        if rediscovered.conflicting:
            raise VerificationError("Created index verification failed.")
        if definition in rediscovered.missing_definitions:
            raise VerificationError("Created index verification failed.")

    final = assess_indexes(repository)
    if not final.is_exact:
        raise VerificationError("Final index verification failed.")
    return ProvisioningStatistics(
        mode="apply",
        target_indexes=len(INDEX_DEFINITIONS),
        exact_existing=initial.exact_existing,
        missing=initial.missing,
        conflicting=0,
        created=created,
        verified_exact=final.exact_existing,
        status="verified",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Provision newsletter link indexes safely."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    return parser


def create_repository_from_environment(
    *,
    client_factory: Callable[..., Any] = MongoClient,
) -> NewsletterLinkIndexRepository:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    mongo_url = os.environ.get("MONGO_URL")
    database_name = os.environ.get("DB_NAME")
    if not mongo_url or not database_name:
        raise ConfigurationError("Required database configuration is unavailable.")
    try:
        client = client_factory(mongo_url, serverSelectionTimeoutMS=10000)
        client.admin.command("ping")
        return NewsletterLinkIndexRepository(client[database_name])
    except PyMongoError as exc:
        raise DatabaseOperationError("Database connection failed safely.") from exc
    except Exception as exc:
        raise DatabaseOperationError("Database connection failed safely.") from exc


def main(
    argv: Sequence[str] | None = None,
    *,
    repository_factory: Callable[[], Any] = create_repository_from_environment,
    input_func: Callable[[str], str] = input,
    stdin_isatty: Callable[[], bool] | None = None,
) -> int:
    try:
        args = build_parser().parse_args(argv)
        if args.apply:
            require_apply_confirmation(
                input_func=input_func,
                stdin_isatty=stdin_isatty,
            )
        repository = repository_factory()
        if args.dry_run:
            statistics = execute_dry_run(repository)
        else:
            statistics = _execute_confirmed_apply(repository)
        print(json.dumps(statistics.public_dict(), sort_keys=True))
        return 0
    except ProvisioningError as exc:
        print(f"Index provisioning failed safely: {exc}", file=sys.stderr)
        return 1
    except SystemExit:
        raise
    except Exception:
        print(
            "Index provisioning failed safely due to an unexpected error.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
