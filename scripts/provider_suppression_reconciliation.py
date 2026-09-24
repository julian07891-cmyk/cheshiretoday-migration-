import csv
import json
import os
import sys
from datetime import datetime, timezone
from collections import Counter
from pathlib import Path

from pymongo import MongoClient, UpdateOne


EXPECTED_COLUMNS = {"id", "email_address", "reason", "reason_detail", "created_at"}
ALLOWED_REASONS = {"bounce", "complaint"}


def load_env(path="backend/.env"):
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip(chr(34)).strip(chr(39)))


def normalize_email(value):
    return (value or "").strip().lower()


def load_suppressions(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        if columns != EXPECTED_COLUMNS:
            raise SystemExit("REFUSING: unexpected suppression CSV columns")

        rows = list(reader)

    if not rows:
        raise SystemExit("REFUSING: suppression CSV is empty")

    normalized = []
    for row in rows:
        email = normalize_email(row.get("email_address"))
        reason = (row.get("reason") or "").strip().lower()
        if not email:
            raise SystemExit("REFUSING: suppression row has empty email address")
        if reason not in ALLOWED_REASONS:
            raise SystemExit("REFUSING: unexpected suppression reason")
        normalized.append((email, reason))

    emails = [email for email, _ in normalized]
    if len(emails) != len(set(emails)):
        raise SystemExit("REFUSING: duplicate normalized email addresses in suppression CSV")

    return rows, normalized


def main():
    backup_mode = len(sys.argv) == 3 and sys.argv[2] == "--backup"
    apply_mode = len(sys.argv) == 3 and sys.argv[2] == "--apply-confirm-815"
    if len(sys.argv) not in (2, 3) or (len(sys.argv) == 3 and not (backup_mode or apply_mode)):
        raise SystemExit("Usage: python3 scripts/provider_suppression_reconciliation.py /path/to/suppressions.csv [--backup|--apply-confirm-815]")

    rows, normalized = load_suppressions(sys.argv[1])
    provider_by_email = {email: reason.lower() for email, reason in normalized}
    provider_timestamp_by_email = {}
    reason_counts = Counter(reason for _, reason in normalized)
    valid_timestamps = 0
    invalid_timestamps = 0
    for row in rows:
        try:
            parsed = datetime.fromisoformat((row.get("created_at") or "").strip().replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                raise ValueError("suppression timestamp is not timezone-aware")
            parsed = parsed.astimezone(timezone.utc)
            parsed = parsed.replace(microsecond=(parsed.microsecond // 1000) * 1000)
            provider_timestamp_by_email[normalize_email(row.get("email_address"))] = parsed
            valid_timestamps += 1
        except (TypeError, ValueError):
            invalid_timestamps += 1

    print("PROVIDER SUPPRESSION RECONCILIATION — READ ONLY")
    print("provider_records=", len(rows))
    print("provider_unique_addresses=", len(provider_by_email))
    print("provider_bounce=", reason_counts["bounce"])
    print("provider_complaint=", reason_counts["complaint"])
    print("valid_created_at=", valid_timestamps)
    print("invalid_created_at=", invalid_timestamps)

    load_env()
    client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=10000)
    db = client[os.environ["DB_NAME"]]

    try:
        subscribers = list(
            db.subscribers.find(
                {"email": {"$in": list(provider_by_email)}},
                {
                    "email": 1,
                    "active": 1,
                    "provider_suppressed": 1,
                    "provider_suppression_reason": 1,
                    "provider_suppressed_at": 1,
                    "provider_suppression_source": 1,
                },
            )
        )

        matched = {}
        duplicate_db_matches = 0
        for subscriber in subscribers:
            email = normalize_email(subscriber.get("email"))
            if not email:
                continue
            if email in matched:
                duplicate_db_matches += 1
                continue
            matched[email] = subscriber

        matched_emails = set(matched)
        provider_emails = set(provider_by_email)
        unmatched = provider_emails - matched_emails

        active = 0
        inactive = 0
        state_reason_counts = Counter()
        matched_bounce = 0
        matched_complaint = 0
        already_exact = 0
        needs_change = 0
        existing_suppressed_nonexact = 0

        for email, subscriber in matched.items():
            reason = provider_by_email[email]
            if subscriber.get("active") is True:
                active += 1
                state_reason_counts[(reason, "active")] += 1
            else:
                inactive += 1
                state_reason_counts[(reason, "inactive_or_legacy")] += 1

            if reason == "bounce":
                matched_bounce += 1
            elif reason == "complaint":
                matched_complaint += 1

            stored_at = subscriber.get("provider_suppressed_at")
            if isinstance(stored_at, str):
                try:
                    stored_at = datetime.fromisoformat(stored_at.replace("Z", "+00:00"))
                except ValueError:
                    stored_at = None
            if stored_at is not None and getattr(stored_at, "tzinfo", None) is None:
                stored_at = stored_at.replace(tzinfo=timezone.utc)
            if stored_at is not None:
                stored_at = stored_at.astimezone(timezone.utc)

            exact = (
                subscriber.get("provider_suppressed") is True
                and subscriber.get("provider_suppression_reason") == reason
                and subscriber.get("provider_suppression_source") == "resend"
                and stored_at == provider_timestamp_by_email[email]
            )
            if exact:
                already_exact += 1
            else:
                needs_change += 1
                if subscriber.get("provider_suppressed") is True:
                    existing_suppressed_nonexact += 1

        print()
        print("DATABASE COMPARISON")
        print("matched_subscribers=", len(matched))
        print("unmatched_provider_addresses=", len(unmatched))
        print("duplicate_database_matches=", duplicate_db_matches)
        print("matched_active=", active)
        print("matched_inactive_or_legacy=", inactive)
        print("matched_bounce=", matched_bounce)
        print("matched_complaint=", matched_complaint)
        print("bounce_active=", state_reason_counts[("bounce", "active")])
        print("bounce_inactive_or_legacy=", state_reason_counts[("bounce", "inactive_or_legacy")])
        print("complaint_active=", state_reason_counts[("complaint", "active")])
        print("complaint_inactive_or_legacy=", state_reason_counts[("complaint", "inactive_or_legacy")])
        print("already_exactly_reconciled=", already_exact)
        print("would_require_local_change=", needs_change)
        print("already_suppressed_but_nonexact=", existing_suppressed_nonexact)

        print()
        print("SAFETY")
        print("database_writes_before_apply=0")
        print("provider_api_calls=0")
        print("provider_unsuppressions=0")
        print("recipient_addresses_printed=0")

        if apply_mode:
            if len(rows) != 815 or len(provider_by_email) != 815:
                raise SystemExit("REFUSING APPLY: expected exactly 815 provider suppressions")
            if reason_counts["bounce"] != 785 or reason_counts["complaint"] != 30:
                raise SystemExit("REFUSING APPLY: expected exactly 785 bounce and 30 complaint suppressions")
            if valid_timestamps != 815 or invalid_timestamps != 0 or len(provider_timestamp_by_email) != 815:
                raise SystemExit("REFUSING APPLY: suppression timestamps do not match validated baseline")
            if len(matched) != 815 or unmatched or duplicate_db_matches:
                raise SystemExit("REFUSING APPLY: reconciliation is not exactly 815 matched, 0 unmatched, 0 duplicates")
            if active != 583 or inactive != 232:
                raise SystemExit("REFUSING APPLY: subscriber active-state baseline changed")
            if matched_bounce != 785 or matched_complaint != 30:
                raise SystemExit("REFUSING APPLY: matched reason baseline changed")
            if state_reason_counts[("bounce", "active")] != 555 or state_reason_counts[("bounce", "inactive_or_legacy")] != 230:
                raise SystemExit("REFUSING APPLY: bounce state baseline changed")
            if state_reason_counts[("complaint", "active")] != 28 or state_reason_counts[("complaint", "inactive_or_legacy")] != 2:
                raise SystemExit("REFUSING APPLY: complaint state baseline changed")
            if already_exact != 0 or needs_change != 815 or existing_suppressed_nonexact != 0:
                raise SystemExit("REFUSING APPLY: provider suppression state baseline changed")

            backup_path = Path.home() / ".cheshiretoday-private-backups" / "provider-suppression-pre-reconcile-815.json"
            if not backup_path.is_file():
                raise SystemExit("REFUSING APPLY: validated private backup is missing")
            if (backup_path.stat().st_mode & 0o777) != 0o600:
                raise SystemExit("REFUSING APPLY: private backup permissions are not 0600")
            try:
                backup_docs = json.loads(backup_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                raise SystemExit("REFUSING APPLY: private backup is unreadable or invalid JSON")

            if not isinstance(backup_docs, list) or len(backup_docs) != 815:
                raise SystemExit("REFUSING APPLY: private backup does not contain exactly 815 documents")
            backup_ids = [str(document.get("_id", "")) for document in backup_docs if isinstance(document, dict)]
            if len(backup_ids) != 815 or any(not value for value in backup_ids) or len(set(backup_ids)) != 815:
                raise SystemExit("REFUSING APPLY: private backup IDs are incomplete or duplicated")
            current_ids = {str(subscriber["_id"]) for subscriber in matched.values()}
            if set(backup_ids) != current_ids:
                raise SystemExit("REFUSING APPLY: private backup IDs do not exactly match current reconciliation targets")

            operations = []
            for email in sorted(matched):
                subscriber = matched[email]
                operations.append(
                    UpdateOne(
                        {
                            "_id": subscriber["_id"],
                            "provider_suppressed": {"$ne": True},
                        },
                        {
                            "$set": {
                                "provider_suppressed": True,
                                "provider_suppression_reason": provider_by_email[email],
                                "provider_suppressed_at": provider_timestamp_by_email[email],
                                "provider_suppression_source": "resend",
                            }
                        },
                    )
                )

            if len(operations) != 815:
                raise SystemExit("REFUSING APPLY: did not construct exactly 815 update operations")

            print()
            print("APPLY PLAN")
            print("update_operations=", len(operations))
            print("fields_per_update=4")
            print("targeting=exact_subscriber_id")
            print("provider_api_calls=0")
            with client.start_session() as session:
                with session.start_transaction():
                    result = db.subscribers.bulk_write(operations, ordered=True, session=session)
                    if result.matched_count != 815 or result.modified_count != 815:
                        raise RuntimeError(
                            "APPLY ABORTED: bulk write did not match and modify exactly 815 subscribers"
                        )

                    verified = list(
                        db.subscribers.find(
                            {"_id": {"$in": [subscriber["_id"] for subscriber in matched.values()]}},
                            {
                                "email": 1,
                                "provider_suppressed": 1,
                                "provider_suppression_reason": 1,
                                "provider_suppressed_at": 1,
                                "provider_suppression_source": 1,
                            },
                            session=session,
                        )
                    )
                    if len(verified) != 815:
                        raise RuntimeError("APPLY ABORTED: post-write verification did not return exactly 815 subscribers")

                    verified_exact = 0
                    for subscriber in verified:
                        email = normalize_email(subscriber.get("email"))
                        stored_at = subscriber.get("provider_suppressed_at")
                        if stored_at is not None and getattr(stored_at, "tzinfo", None) is None:
                            stored_at = stored_at.replace(tzinfo=timezone.utc)
                        if stored_at is not None:
                            stored_at = stored_at.astimezone(timezone.utc)

                        if (
                            email in provider_by_email
                            and subscriber.get("provider_suppressed") is True
                            and subscriber.get("provider_suppression_reason") == provider_by_email[email]
                            and subscriber.get("provider_suppression_source") == "resend"
                            and stored_at == provider_timestamp_by_email[email]
                        ):
                            verified_exact += 1

                    if verified_exact != 815:
                        raise RuntimeError("APPLY ABORTED: post-write exact verification did not reach 815")

            print()
            print("APPLY RESULT")
            print("matched_count=", result.matched_count)
            print("modified_count=", result.modified_count)
            print("post_write_exact=", verified_exact)
            print("transaction_committed=1")
            print("provider_api_calls=0")
            print("provider_unsuppressions=0")
            print("recipient_addresses_printed=0")

        if backup_mode:
            if len(rows) != 815 or len(provider_by_email) != 815:
                raise SystemExit("REFUSING BACKUP: expected exactly 815 provider suppressions")
            if len(matched) != 815 or unmatched or duplicate_db_matches:
                raise SystemExit("REFUSING BACKUP: reconciliation is not exactly 815 matched, 0 unmatched, 0 duplicates")

            backup_dir = Path.home() / ".cheshiretoday-private-backups"
            if not backup_dir.is_dir():
                raise SystemExit("REFUSING BACKUP: private backup directory does not exist")
            if (backup_dir.stat().st_mode & 0o077) != 0:
                raise SystemExit("REFUSING BACKUP: private backup directory permissions are too broad")

            backup_path = backup_dir / "provider-suppression-pre-reconcile-815.json"
            if backup_path.exists():
                raise SystemExit("REFUSING BACKUP: backup file already exists")

            backup_docs = []
            for email in sorted(matched):
                document = dict(matched[email])
                document["_id"] = str(document["_id"])
                backup_docs.append(document)

            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            fd = os.open(backup_path, flags, 0o600)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump(backup_docs, handle, default=str, indent=2)
                    handle.write("\n")
            except Exception:
                backup_path.unlink(missing_ok=True)
                raise

            print()
            print("BACKUP")
            print("backup_created=1")
            print("backup_documents=", len(backup_docs))
            print("backup_path=", backup_path)
            print("backup_permissions=0600")
    finally:
        client.close()


if __name__ == "__main__":
    main()
