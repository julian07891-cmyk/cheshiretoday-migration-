"""Anonymous daily newsletter-signup funnel aggregates."""

from __future__ import annotations

import calendar
import logging
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo


COLLECTION_NAME = "newsletter_signup_funnel_daily"
SCHEMA_VERSION = 1
LONDON = ZoneInfo("Europe/London")
CANONICAL_PLACEMENTS = frozenset(
    {"newsletter_landing", "homepage", "article", "footer", "popup", "unknown"}
)
OUTCOMES = frozenset({"created", "existing", "failed"})
NEWSLETTER_SIGNUP_FUNNEL_INDEXES = (
    {
        "keys": [("date_key", 1), ("placement", 1)],
        "options": {
            "unique": True,
            "name": "newsletter_signup_funnel_day_placement_unique",
        },
    },
    {
        "keys": [("expires_at", 1)],
        "options": {
            "expireAfterSeconds": 0,
            "name": "newsletter_signup_funnel_expiry_ttl",
        },
    },
    {
        "keys": [("day_start_utc", 1), ("placement", 1)],
        "options": {"name": "newsletter_signup_funnel_reporting"},
    },
)


def normalise_newsletter_signup_placement(value: object) -> str:
    """Map only approved measurement placements; legacy values remain unknown."""
    if not isinstance(value, str):
        return "unknown"
    if value == "website" or value not in CANONICAL_PLACEMENTS:
        return "unknown"
    return value


def _add_calendar_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def newsletter_signup_funnel_period(now: datetime | None = None) -> dict:
    """Return London-day identity and exact 13-calendar-month expiry."""
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    current_utc = current.astimezone(timezone.utc)
    london_day = current_utc.astimezone(LONDON).date()
    day_start = datetime.combine(london_day, time.min, tzinfo=LONDON)
    expiry_day = _add_calendar_months(london_day, 13)
    expiry = datetime.combine(expiry_day, time.min, tzinfo=LONDON)
    return {
        "date_key": london_day.isoformat(),
        "day_start_utc": day_start.astimezone(timezone.utc),
        "created_at": current_utc,
        "updated_at": current_utc,
        "expires_at": expiry.astimezone(timezone.utc),
    }


async def record_newsletter_signup_outcome(
    collection,
    placement: object,
    outcome: str,
    *,
    now: datetime | None = None,
) -> None:
    """Atomically record one completed attempt and exactly one outcome."""
    if outcome not in OUTCOMES:
        raise ValueError("Unsupported newsletter signup outcome")

    canonical_placement = normalise_newsletter_signup_placement(placement)
    period = newsletter_signup_funnel_period(now)
    increments = {
        "attempts": 1,
        "created": 1 if outcome == "created" else 0,
        "existing": 1 if outcome == "existing" else 0,
        "failed": 1 if outcome == "failed" else 0,
        "server_error": 1 if outcome == "failed" else 0,
    }

    await collection.update_one(
        {
            "date_key": period["date_key"],
            "placement": canonical_placement,
        },
        {
            "$inc": increments,
            "$set": {
                "updated_at": period["updated_at"],
                "expires_at": period["expires_at"],
            },
            "$setOnInsert": {
                "schema_version": SCHEMA_VERSION,
                "date_key": period["date_key"],
                "day_start_utc": period["day_start_utc"],
                "placement": canonical_placement,
                "created_at": period["created_at"],
            },
        },
        upsert=True,
    )


async def record_newsletter_signup_outcome_safely(
    database,
    placement: object,
    outcome: str,
    *,
    logger: logging.Logger,
    now: datetime | None = None,
) -> bool:
    """Fail open so measurement can never alter the subscription result.

    A process termination between subscriber mutation and this best-effort write
    can undercount; no distributed transaction is introduced for diagnostics.
    """
    try:
        collection = getattr(database, COLLECTION_NAME)
        await record_newsletter_signup_outcome(
            collection, placement, outcome, now=now
        )
        return True
    except Exception:
        logger.warning(
            "Newsletter signup funnel recording unavailable: outcome=%s",
            outcome,
        )
        return False


async def ensure_newsletter_signup_funnel_indexes(collection) -> None:
    """Idempotently provision aggregate identity, expiry and reporting indexes."""
    for index in NEWSLETTER_SIGNUP_FUNNEL_INDEXES:
        await collection.create_index(index["keys"], **index["options"])
