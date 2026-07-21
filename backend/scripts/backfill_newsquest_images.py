#!/usr/bin/env python3
"""Safely backfill legacy Newsquest article images.

Uses source Open Graph data where appropriate.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

import requests
from dotenv import load_dotenv
from pymongo import ASCENDING, MongoClient
from pymongo.errors import PyMongoError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.article_image_resolver import (  # noqa: E402
    NEWSQUEST_HOSTS,
    resolve_imported_article_image,
)


CONFIRMATION_TEXT = "APPLY NEWSQUEST IMAGE BACKFILL"
LEGACY_IMAGE_FRAGMENT = "/resources/images/"
REQUEST_TIMEOUT_SECONDS = 10
SAFE_USER_AGENT = "CheshireToday-NewsquestImageBackfill/1.0"


class BackfillError(Exception):
    """Base class for privacy-safe backfill failures."""


class ConfigurationError(BackfillError):
    """Configuration or CLI validation failed."""


class ConfirmationError(BackfillError):
    """Interactive apply confirmation was unavailable or incorrect."""


class DatabaseOperationError(BackfillError):
    """A database operation failed without exposing its payload."""


class VerificationError(BackfillError):
    """Post-update verification failed."""


@dataclass(frozen=True)
class PlannedImageUpdate:
    record_id: Any
    source_url: str
    original_image: str
    resolved_image: str


@dataclass(frozen=True)
class UpdateResult:
    modified_count: int
    conditional_conflicts: int


@dataclass
class BackfillStatistics:
    mode: str
    scanned: int = 0
    candidates: int = 0
    resolved: int = 0
    unchanged: int = 0
    lookup_failures: int = 0
    updates_planned: int = 0
    records_updated: int = 0
    conditional_conflicts: int = 0
    verification_failures: int = 0
    status: str = "inspected"

    def public_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BackfillPlan:
    updates: tuple[PlannedImageUpdate, ...]
    statistics: BackfillStatistics


class LookupTracker:
    """Track source-page failures without retaining sensitive details."""

    def __init__(self, fetch_page: Callable[[str], str]) -> None:
        self._fetch_page = fetch_page
        self.failed = False

    def __call__(self, source_url: str) -> str:
        try:
            return self._fetch_page(source_url)
        except Exception:
            self.failed = True
            raise


class ArticleRepository:
    """Narrow synchronous adapter for the article image backfill."""

    def __init__(self, collection: Any) -> None:
        self.collection = collection

    def scan_candidates(self) -> list[dict[str, Any]]:
        query = {
            "image": {"$regex": LEGACY_IMAGE_FRAGMENT, "$options": "i"},
            "source_url": {"$type": "string"},
        }
        projection = {"_id": 1, "image": 1, "source_url": 1}
        try:
            return list(
                self.collection.find(query, projection).sort("_id", ASCENDING)
            )
        except PyMongoError as exc:
            raise DatabaseOperationError(
                "Article candidate scan failed."
            ) from exc
        except Exception as exc:
            raise DatabaseOperationError(
                "Article candidate scan failed."
            ) from exc

    def apply_update(self, update: PlannedImageUpdate) -> UpdateResult:
        filter_document = {
            "_id": update.record_id,
            "image": update.original_image,
            "source_url": update.source_url,
        }
        try:
            result = self.collection.update_one(
                filter_document,
                {"$set": {"image": update.resolved_image}},
            )
        except PyMongoError as exc:
            raise DatabaseOperationError(
                "Article image update failed."
            ) from exc
        except Exception as exc:
            raise DatabaseOperationError(
                "Article image update failed."
            ) from exc

        matched_count = getattr(result, "matched_count", None)
        modified_count = getattr(result, "modified_count", None)
        if type(matched_count) is not int or type(modified_count) is not int:
            raise DatabaseOperationError(
                "Article image update result was invalid."
            )
        if matched_count == 0 and modified_count == 0:
            return UpdateResult(modified_count=0, conditional_conflicts=1)
        if matched_count != 1 or modified_count != 1:
            raise DatabaseOperationError(
                "Article image update result was invalid."
            )
        return UpdateResult(modified_count=1, conditional_conflicts=0)

    def verify_image(self, update: PlannedImageUpdate) -> bool:
        try:
            record = self.collection.find_one(
                {"_id": update.record_id}, {"_id": 0, "image": 1}
            )
        except PyMongoError as exc:
            raise DatabaseOperationError(
                "Article image verification failed."
            ) from exc
        except Exception as exc:
            raise DatabaseOperationError(
                "Article image verification failed."
            ) from exc
        return bool(record and record.get("image") == update.resolved_image)


def _supported_source(source_url: Any) -> bool:
    from urllib.parse import urlparse

    if not isinstance(source_url, str):
        return False
    try:
        return urlparse(source_url.strip()).netloc.lower() in NEWSQUEST_HOSTS
    except Exception:
        return False


def _valid_changed_image(original: str, resolved: Any) -> bool:
    from urllib.parse import urlparse

    if not isinstance(resolved, str):
        return False
    candidate = resolved.strip()
    if not candidate or candidate == original:
        return False
    try:
        parsed = urlparse(candidate)
    except Exception:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def build_plan(
    repository: Any,
    *,
    fetch_page: Callable[[str], str],
    mode: str,
) -> BackfillPlan:
    records = repository.scan_candidates()
    statistics = BackfillStatistics(mode=mode, scanned=len(records))
    updates: list[PlannedImageUpdate] = []

    for record in records:
        original = record.get("image")
        source_url = record.get("source_url")
        if (
            not isinstance(original, str)
            or LEGACY_IMAGE_FRAGMENT not in original.lower()
            or not _supported_source(source_url)
        ):
            continue

        statistics.candidates += 1
        normalised_original = original.strip()
        tracker = LookupTracker(fetch_page)
        resolved = resolve_imported_article_image(
            normalised_original,
            source_url,
            fetch_page=tracker,
        )
        if tracker.failed:
            statistics.lookup_failures += 1
            statistics.unchanged += 1
            continue
        if not _valid_changed_image(normalised_original, resolved):
            statistics.unchanged += 1
            continue

        statistics.resolved += 1
        updates.append(
            PlannedImageUpdate(
                record_id=record["_id"],
                source_url=source_url,
                original_image=original,
                resolved_image=resolved,
            )
        )

    statistics.updates_planned = len(updates)
    return BackfillPlan(updates=tuple(updates), statistics=statistics)


def execute_dry_run(
    repository: Any,
    *,
    fetch_page: Callable[[str], str],
) -> BackfillStatistics:
    return build_plan(
        repository, fetch_page=fetch_page, mode="dry-run"
    ).statistics


def require_apply_confirmation(
    *,
    input_func: Callable[[str], str] = input,
    stdin_isatty: Callable[[], bool] | None = None,
) -> None:
    isatty = stdin_isatty or sys.stdin.isatty
    if isatty() is not True:
        raise ConfirmationError(
            "Interactive confirmation is required; no updates were attempted."
        )
    if (
        input_func("Type the exact backfill confirmation: ")
        != CONFIRMATION_TEXT
    ):
        raise ConfirmationError(
            "Backfill confirmation did not match; no updates were attempted."
        )


def execute_apply(
    repository: Any,
    *,
    fetch_page: Callable[[str], str],
    expected_count: int,
    input_func: Callable[[str], str] = input,
    stdin_isatty: Callable[[], bool] | None = None,
) -> BackfillStatistics:
    plan = build_plan(repository, fetch_page=fetch_page, mode="apply")
    statistics = plan.statistics
    if statistics.lookup_failures:
        raise BackfillError(
            "Source image lookup failed; no updates were attempted."
        )
    if statistics.updates_planned != expected_count:
        raise ConfigurationError(
            "Expected update count did not match; no updates were attempted."
        )

    require_apply_confirmation(
        input_func=input_func,
        stdin_isatty=stdin_isatty,
    )

    for update in plan.updates:
        result = repository.apply_update(update)
        statistics.records_updated += result.modified_count
        statistics.conditional_conflicts += result.conditional_conflicts
        if result.modified_count and not repository.verify_image(update):
            statistics.verification_failures += 1
            raise VerificationError("Post-update image verification failed.")

    if statistics.conditional_conflicts or statistics.verification_failures:
        statistics.status = "failed"
    else:
        statistics.status = "verified"
    return statistics


def positive_integer(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "A positive integer is required."
        ) from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("A positive integer is required.")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Backfill legacy Newsquest article images safely."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-count", type=positive_integer)
    return parser


def validate_arguments(args: argparse.Namespace) -> None:
    if args.apply and args.expected_count is None:
        raise ConfigurationError("--expected-count is required with --apply.")
    if args.dry_run and args.expected_count is not None:
        raise ConfigurationError(
            "--expected-count is only valid with --apply."
        )


def fetch_source_page(source_url: str) -> str:
    response = requests.get(
        source_url,
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers={"User-Agent": SAFE_USER_AGENT},
    )
    response.raise_for_status()
    return response.text


def create_repository_from_environment(
    *, client_factory: Callable[..., Any] = MongoClient
) -> ArticleRepository:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    mongo_url = os.environ.get("MONGO_URL")
    database_name = os.environ.get("DB_NAME")
    if not mongo_url or not database_name:
        raise ConfigurationError(
            "Required database configuration is unavailable."
        )
    try:
        client = client_factory(mongo_url, serverSelectionTimeoutMS=10000)
        client.admin.command("ping")
        return ArticleRepository(client[database_name]["articles"])
    except PyMongoError as exc:
        raise DatabaseOperationError(
            "Database connection failed safely."
        ) from exc
    except Exception as exc:
        raise DatabaseOperationError(
            "Database connection failed safely."
        ) from exc


def main(
    argv: Sequence[str] | None = None,
    *,
    repository_factory: Callable[[], Any] = create_repository_from_environment,
    fetch_page: Callable[[str], str] = fetch_source_page,
    input_func: Callable[[str], str] = input,
    stdin_isatty: Callable[[], bool] | None = None,
) -> int:
    try:
        args = build_parser().parse_args(argv)
        validate_arguments(args)
        repository = repository_factory()
        if args.dry_run:
            statistics = execute_dry_run(repository, fetch_page=fetch_page)
        else:
            statistics = execute_apply(
                repository,
                fetch_page=fetch_page,
                expected_count=args.expected_count,
                input_func=input_func,
                stdin_isatty=stdin_isatty,
            )
        print(json.dumps(statistics.public_dict(), sort_keys=True))
        if (
            statistics.conditional_conflicts
            or statistics.verification_failures
        ):
            return 2
        return 0
    except BackfillError as exc:
        print(
            f"Newsquest image backfill failed safely: {exc}", file=sys.stderr
        )
        return 1
    except SystemExit:
        raise
    except Exception:
        print(
            "Newsquest image backfill failed safely due to an "
            "unexpected error.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
