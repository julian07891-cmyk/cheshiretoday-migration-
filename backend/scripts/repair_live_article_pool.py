#!/usr/bin/env python3
"""Guarded one-time restoration of owner-approved main-collection articles."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from dotenv import load_dotenv
from pymongo import MongoClient


CONFIRMATION_TEXT = "APPLY LIVE ARTICLE POOL REPAIR"
AUTOMATIC_REASONS = {"auto_cap", "ratio_rebalance"}


class RepairError(Exception):
    pass


@dataclass(frozen=True)
class RepairPlan:
    record_ids: tuple[Any, ...]
    scanned: int

    def summary(self, mode: str, updated: int = 0) -> dict[str, Any]:
        return {
            "mode": mode,
            "scanned": self.scanned,
            "eligible_for_restore": len(self.record_ids),
            "expected_live_increase": len(self.record_ids),
            "updated": updated,
            "status": "ready" if mode == "dry-run" else "applied",
        }


def _owner_marker(record: dict[str, Any]) -> bool:
    return bool(
        record.get("manual_edited") is True
        or record.get("manual_edit_protected") is True
        or record.get("verification_status")
        in {"manual_corrected_verified_limited", "manual_force_live"}
        or record.get("rewrite_status") in {"manual_corrected", "manual_force_live"}
        or str(record.get("source") or "").strip() == "Manual Entry"
    )


def _blocked(record: dict[str, Any]) -> bool:
    return bool(
        record.get("manual_review_hidden_from_public") is True
        or record.get("verification_status") == "needs_manual_review"
        or record.get("rewrite_status")
        in {"manual_review_required", "ai_rewrite_needs_review"}
        or str(record.get("editorial_status") or "").casefold()
        in {"rejected", "removed", "legal_removal"}
        or str(record.get("moderation_status") or "").casefold()
        in {"rejected", "removed", "legal_removal"}
    )


def build_plan(records: Iterable[dict[str, Any]]) -> RepairPlan:
    ordered = sorted(records, key=lambda record: str(record.get("_id")))
    eligible = []
    for record in ordered:
        if record.get("archived") is not True:
            continue
        if record.get("archive_reason") not in AUTOMATIC_REASONS:
            continue
        if not str(record.get("title") or "").strip():
            continue
        if not str(record.get("content") or "").strip():
            continue
        if not _owner_marker(record) or _blocked(record):
            continue
        eligible.append(record["_id"])
    return RepairPlan(tuple(eligible), len(ordered))


class ArticleRepository:
    def __init__(self, collection: Any):
        self.collection = collection

    def scan(self) -> list[dict[str, Any]]:
        query = {
            "archived": True,
            "archive_reason": {"$in": sorted(AUTOMATIC_REASONS)},
        }
        projection = {
            "_id": 1,
            "title": 1,
            "content": 1,
            "archived": 1,
            "archive_reason": 1,
            "source": 1,
            "manual_edited": 1,
            "manual_edit_protected": 1,
            "manual_review_hidden_from_public": 1,
            "verification_status": 1,
            "rewrite_status": 1,
            "editorial_status": 1,
            "moderation_status": 1,
        }
        return list(self.collection.find(query, projection))

    def restore_many(self, record_ids: tuple[Any, ...]) -> tuple[int, int]:
        result = self.collection.update_many(
            {
                "_id": {"$in": list(record_ids)},
                "archived": True,
                "archive_reason": {"$in": sorted(AUTOMATIC_REASONS)},
            },
            {
                "$set": {"archived": False},
                "$unset": {"archived_at": "", "archive_reason": ""},
            },
        )
        matched = getattr(result, "matched_count", None)
        modified = getattr(result, "modified_count", None)
        if type(matched) is not int or type(modified) is not int:
            raise RepairError("The restoration result was invalid.")
        return matched, modified


def execute(repository: Any, mode: str, expected_count: int | None) -> dict[str, Any]:
    initial_plan = build_plan(repository.scan())
    if mode == "dry-run":
        return initial_plan.summary(mode)
    if expected_count != len(initial_plan.record_ids):
        raise RepairError("Expected count did not match the repair plan.")

    # Rebuild immediately before the single write so count and identity drift
    # abort without changing any record.
    apply_plan = build_plan(repository.scan())
    if apply_plan.record_ids != initial_plan.record_ids:
        raise RepairError("The eligible article set changed before apply.")
    if len(apply_plan.record_ids) != expected_count:
        raise RepairError("Expected count changed before apply.")

    matched, modified = repository.restore_many(apply_plan.record_ids)
    if matched != expected_count or modified != expected_count:
        raise RepairError("The guarded restoration was incomplete.")

    verification = build_plan(repository.scan())
    if verification.record_ids:
        raise RepairError("Post-repair verification failed.")
    return apply_plan.summary(mode, modified)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-count", type=int)
    args = parser.parse_args(argv)
    if args.apply and (args.expected_count is None or args.expected_count < 0):
        parser.error("--apply requires a non-negative --expected-count")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    mode = "apply" if args.apply else "dry-run"
    try:
        if mode == "apply":
            if not sys.stdin.isatty():
                raise RepairError("Apply requires an interactive terminal.")
            if input("Type confirmation: ").strip() != CONFIRMATION_TEXT:
                raise RepairError("Confirmation failed.")
        load_dotenv()
        uri = os.environ.get("MONGO_URL")
        database_name = os.environ.get("DB_NAME")
        if not uri or not database_name:
            raise RepairError("Database configuration is unavailable.")
        client = MongoClient(uri)
        repository = ArticleRepository(client[database_name]["articles"])
        print(json.dumps(execute(repository, mode, args.expected_count), sort_keys=True))
        return 0
    except Exception:
        print(json.dumps({"mode": mode, "status": "failed"}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
