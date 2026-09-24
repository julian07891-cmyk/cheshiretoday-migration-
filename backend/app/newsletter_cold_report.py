"""Read-only aggregate cold evidence. Acceptance is not proof of inbox delivery."""

from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import re


HASH = re.compile(r"[0-9a-f]{8}")
ELIGIBLE = {"$and": [
    {"$or": [{"active": True}, {"active": {"$exists": False}}]},
    {"$or": [{"daily_brief": {"$ne": False}}, {"daily_brief": {"$exists": False}}]},
]}


def utc_date(value):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if not isinstance(value, datetime):
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


async def rows(collection, query, projection):
    """No silent read caps: omitted engagement could produce false candidates."""
    cursor = collection.find(query, projection)
    try:
        async for row in cursor:
            yield row
    finally:
        await cursor.close()


async def build_cold_report(db, deliverable, *, days, recent_days, min_accepted_sends, now):
    cutoff = now - timedelta(days=days)
    recent_cutoff = now - timedelta(days=recent_days)
    summary = dict(active_daily_unique=0, invalid_excluded=0,
                   protected_or_organic_excluded=0, recent_subscribers_excluded=0,
                   unknown_subscription_date_excluded=0,
                   accepted_send_evidence_recipient_count=0, engaged_recipient_count=0,
                   insufficient_accepted_send_evidence=0, cold_candidates_total=0)
    subscribers = {}
    projection = {key: 1 for key in (
        "email", "active", "daily_brief", "subscribed_at", "created_at",
        "signup_source", "subscriber_origin", "priority_daily_brief")}
    projection["_id"] = 0
    async for sub in rows(db.subscribers, ELIGIBLE, projection):
        raw = sub.get("email")
        if not isinstance(raw, str) or not raw.strip():
            summary["invalid_excluded"] += 1
            continue
        email = raw.strip().lower()
        subscribers.setdefault(email, []).append(sub)

    eligible_hashes = []
    for email, peers in subscribers.items():
        summary["active_daily_unique"] += 1
        if not deliverable(email):
            summary["invalid_excluded"] += 1
            continue
        if email.rsplit("@", 1)[-1] == "cheshiretoday.co.uk" or any(
            p.get("priority_daily_brief") is True or p.get("signup_source") == "website"
            or p.get("subscriber_origin") == "organic_website" for p in peers
        ):
            summary["protected_or_organic_excluded"] += 1
            continue
        # A duplicate record must not hide a recent signup. Preserve the
        # subscribed_at-first, created_at-fallback convention.
        dates = [utc_date(p.get("subscribed_at")) or utc_date(p.get("created_at")) for p in peers]
        if any(d is not None and d >= recent_cutoff for d in dates):
            summary["recent_subscribers_excluded"] += 1
            continue
        if any(d is None for d in dates):
            summary["unknown_subscription_date_excluded"] += 1
            continue
        eligible_hashes.append(hashlib.sha256(email.encode()).hexdigest()[:8])

    # Any recorded engagement vetoes a candidate, even outside the send window.
    # Producers upsert counters and timestamps, not a delivered-recipient roster.
    engaged = set()
    async for row in rows(db.email_analytics, {}, {
        "_id": 0, "tracking_id": 1, "opens": 1, "clicks": 1,
        "last_opened": 1, "last_clicked": 1,
    }):
        tracking = row.get("tracking_id")
        suffix = tracking.rsplit("_", 1)[-1] if isinstance(tracking, str) else ""
        if not HASH.fullmatch(suffix):
            continue
        positive = any(isinstance(row.get(k), (int, float)) and row[k] > 0
                       for k in ("opens", "clicks"))
        if positive or utc_date(row.get("last_opened")) or utc_date(row.get("last_clicked")):
            engaged.add(suffix)

    opportunities = {}
    dates = []
    invalid_ledger_rows = 0
    async for row in rows(db.email_send_opportunities, {}, {
        "_id": 0, "accepted_at": 1, "accepted_count": 1, "recipient_hashes": 1,
        "tracking_id": 1, "digest_key": 1, "provider": 1,
    }):
        accepted_at = utc_date(row.get("accepted_at"))
        hashes = row.get("recipient_hashes")
        count = row.get("accepted_count")
        tracking = row.get("tracking_id")
        valid = (
            accepted_at is not None and accepted_at <= now
            and isinstance(tracking, str) and bool(tracking.strip())
            and row.get("digest_key") in ("DailyBrief", "WeeklyRoundup")
            and row.get("provider") in ("resend", "smtp")
            and isinstance(count, int) and not isinstance(count, bool) and count > 0
            and isinstance(hashes, list) and bool(hashes)
            and all(isinstance(h, str) and HASH.fullmatch(h) for h in hashes)
        )
        if not valid or count != len(set(hashes)):
            invalid_ledger_rows += 1
            continue
        dates.append(accepted_at)
        if accepted_at >= cutoff:
            # Producer upserts by tracking_id. Duplicate documents cannot inflate
            # an opportunity; duplicate hashes in a document count only once.
            opportunities.setdefault(tracking, set()).update(hashes)
    accepted = Counter(h for hashes in opportunities.values() for h in hashes)
    distribution = Counter()
    for recipient in eligible_hashes:
        n = accepted[recipient]
        distribution[str(n)] += 1
        summary["accepted_send_evidence_recipient_count"] += int(n > 0)
        summary["engaged_recipient_count"] += int(recipient in engaged)
        summary["insufficient_accepted_send_evidence"] += int(n < min_accepted_sends)
        if n >= min_accepted_sends and recipient not in engaged:
            summary["cold_candidates_total"] += 1
    return {
        "success": True, "dry_run": True, "period_days": days,
        "recent_subscriber_exclusion_days": recent_days,
        "min_accepted_sends": min_accepted_sends,
        "engagement_scope": "all_recorded_history",
        "summary": summary,
        "accepted_send_count_distribution": dict(sorted(distribution.items(), key=lambda x: int(x[0]))),
        "ledger_coverage": {
            "earliest_accepted_at": min(dates).isoformat() if dates else None,
            "latest_accepted_at": max(dates).isoformat() if dates else None,
            "valid_opportunities_in_window": len(opportunities),
            "invalid_rows_excluded": invalid_ledger_rows,
        },
        "next_step": (
            "Review accepted-send evidence and absence of recorded engagement before any "
            "separately approved lifecycle action. This report is dry-run only; "
            "provider acceptance does not prove delivery. Do not hard-delete subscribers."
        ),
    }
