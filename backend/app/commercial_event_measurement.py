"""Bounded first-party commercial-event validation and reporting helpers."""

from __future__ import annotations

import hashlib
from datetime import date, datetime, time, timedelta, timezone
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


EVENT_TYPES = ("rendered", "viewable", "clicked")
DEVICE_CLASSES = ("mobile", "desktop")
DESTINATION_TYPES = ("advertiser", "affiliate", "guide", "product", "provider")
COMMERCIAL_EVENT_RETENTION_DAYS = 120
COMMERCIAL_REPORT_MAX_DAYS = 90
COMMERCIAL_REPORT_DEFAULT_DAYS = 30
COMMERCIAL_REPORT_LIST_LIMIT = 20
COMMERCIAL_DIMENSION_LIMIT = 50
# Operational triage filter only; this is not a statistical-significance claim.
ZERO_CLICK_MIN_RENDERED = 25
COMMERCIAL_EVENT_MAX_BODY_BYTES = 2048
LONDON = ZoneInfo("Europe/London")

COMMERCIAL_EVENT_INDEXES = (
    {
        "keys": [("dedupe_key", 1)],
        "options": {"unique": True, "name": "commercial_event_dedupe_unique"},
    },
    {
        "keys": [("expires_at", 1)],
        "options": {"expireAfterSeconds": 0, "name": "commercial_event_expiry_ttl"},
    },
    {
        "keys": [
            ("occurred_at", 1),
            ("event_type", 1),
            ("provider_id", 1),
            ("placement_id", 1),
        ],
        "options": {"name": "commercial_event_reporting"},
    },
)

Identifier = str


class CommercialEventPayload(BaseModel):
    """Strict, bounded client contract; no reader identity or destination URL."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    event_type: Literal["rendered", "viewable", "clicked"]
    card_id: Identifier = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_-]+$")
    provider_id: Identifier = Field(min_length=1, max_length=48, pattern=r"^[a-z0-9_-]+$")
    placement_id: Identifier = Field(min_length=1, max_length=48, pattern=r"^[a-z0-9_-]+$")
    article_id: Identifier | None = Field(default=None, min_length=1, max_length=64, pattern=r"^[a-z0-9_-]+$")
    article_category: Identifier | None = Field(default=None, min_length=1, max_length=32, pattern=r"^[a-z0-9_-]+$")
    use_case: Identifier = Field(min_length=1, max_length=48, pattern=r"^[a-z0-9_-]+$")
    destination_type: Literal["advertiser", "affiliate", "guide", "product", "provider"]
    destination_id: Identifier = Field(min_length=1, max_length=96, pattern=r"^[a-z0-9_-]+$")
    device_class: Literal["mobile", "desktop"]
    rule_reason_code: Identifier = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_-]+$")
    variant_version: Identifier = Field(min_length=1, max_length=32, pattern=r"^[a-z0-9_-]+$")
    disclosure_version: Identifier = Field(min_length=1, max_length=32, pattern=r"^[a-z0-9_-]+$")
    session_key: str = Field(min_length=16, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    page_view_id: Identifier = Field(min_length=16, max_length=64, pattern=r"^[a-z0-9_-]+$")

    @field_validator(
        "card_id",
        "provider_id",
        "placement_id",
        "article_id",
        "article_category",
        "use_case",
        "destination_id",
        "rule_reason_code",
        "variant_version",
        "disclosure_version",
        "page_view_id",
        mode="before",
    )
    @classmethod
    def normalise_identifier(cls, value):
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        return value.strip().lower()

    @model_validator(mode="after")
    def require_article_for_article_placement(self):
        if self.placement_id.startswith("article_") and not self.article_id:
            raise ValueError("article_id is required for article placements")
        return self


def session_hash(session_key: str) -> str:
    return hashlib.sha256(session_key.encode("utf-8")).hexdigest()


def commercial_event_dedupe_key(payload: CommercialEventPayload) -> str:
    identity = "\x1f".join(
        (
            session_hash(payload.session_key),
            payload.page_view_id,
            payload.event_type,
            payload.provider_id,
            payload.card_id,
            payload.placement_id,
            payload.destination_id,
        )
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def commercial_event_document(
    payload: CommercialEventPayload,
    *,
    now: datetime | None = None,
) -> dict:
    occurred_at = now or datetime.now(timezone.utc)
    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=timezone.utc)
    occurred_at = occurred_at.astimezone(timezone.utc)
    data = payload.model_dump(exclude={"session_key"})
    data.update(
        {
            "occurred_at": occurred_at,
            "expires_at": occurred_at + timedelta(days=COMMERCIAL_EVENT_RETENTION_DAYS),
            "session_hash": session_hash(payload.session_key),
            "dedupe_key": commercial_event_dedupe_key(payload),
        }
    )
    return data


async def ensure_commercial_event_indexes(collection) -> None:
    """Create only the dedupe, expiry and bounded-reporting indexes."""
    for index in COMMERCIAL_EVENT_INDEXES:
        await collection.create_index(index["keys"], **index["options"])


class CommercialReportingPeriod(BaseModel):
    model_config = ConfigDict(frozen=True)

    from_date: date
    to_date: date
    start_utc: datetime
    end_utc: datetime


def commercial_reporting_period(
    from_value: str | None,
    to_value: str | None,
    *,
    now: datetime | None = None,
) -> CommercialReportingPeriod:
    if bool(from_value) != bool(to_value):
        raise ValueError("from and to must be supplied together")

    if from_value and to_value:
        try:
            from_date = date.fromisoformat(from_value)
            to_date = date.fromisoformat(to_value)
        except ValueError as exc:
            raise ValueError("from and to must use YYYY-MM-DD") from exc
    else:
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        to_date = current.astimezone(LONDON).date() - timedelta(days=1)
        from_date = to_date - timedelta(days=COMMERCIAL_REPORT_DEFAULT_DAYS - 1)

    period_days = (to_date - from_date).days + 1
    if period_days < 1:
        raise ValueError("to must not be before from")
    if period_days > COMMERCIAL_REPORT_MAX_DAYS:
        raise ValueError("commercial analytics range cannot exceed 90 days")

    start_local = datetime.combine(from_date, time.min, tzinfo=LONDON)
    end_local = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=LONDON)
    return CommercialReportingPeriod(
        from_date=from_date,
        to_date=to_date,
        start_utc=start_local.astimezone(timezone.utc),
        end_utc=end_local.astimezone(timezone.utc),
    )


def _count_expression(event_type: str) -> dict:
    return {"$sum": {"$cond": [{"$eq": ["$event_type", event_type]}, 1, 0]}}


def _dimension_pipeline(
    field: str,
    output_name: str,
    *,
    limit: int = COMMERCIAL_DIMENSION_LIMIT,
) -> list[dict]:
    return [
        {
            "$group": {
                "_id": {"$ifNull": [f"${field}", "unknown"]},
                "rendered": _count_expression("rendered"),
                "viewable": _count_expression("viewable"),
                "clicked": _count_expression("clicked"),
            }
        },
        {"$sort": {"rendered": -1, "viewable": -1, "clicked": -1, "_id": 1}},
        {"$limit": limit},
        {
            "$project": {
                "_id": 0,
                output_name: "$_id",
                "rendered": 1,
                "viewable": 1,
                "clicked": 1,
            }
        },
    ]


def commercial_aggregate_pipeline(period: CommercialReportingPeriod) -> list[dict]:
    card_group = {
        "provider_id": "$provider_id",
        "card_id": "$card_id",
        "placement_id": "$placement_id",
    }
    card_projection = {
        "_id": 0,
        "provider_id": "$_id.provider_id",
        "card_id": "$_id.card_id",
        "placement_id": "$_id.placement_id",
        "rendered": 1,
        "viewable": 1,
        "clicked": 1,
    }
    card_group_stage = {
        "$group": {
            "_id": card_group,
            "rendered": _count_expression("rendered"),
            "viewable": _count_expression("viewable"),
            "clicked": _count_expression("clicked"),
        }
    }
    return [
        {
            "$match": {
                "occurred_at": {"$gte": period.start_utc, "$lt": period.end_utc}
            }
        },
        {
            "$facet": {
                "overall": [
                    {
                        "$group": {
                            "_id": None,
                            "rendered": _count_expression("rendered"),
                            "viewable": _count_expression("viewable"),
                            "clicked": _count_expression("clicked"),
                        }
                    },
                    {"$project": {"_id": 0, "rendered": 1, "viewable": 1, "clicked": 1}},
                ],
                "by_provider": _dimension_pipeline("provider_id", "provider_id"),
                "by_placement": _dimension_pipeline("placement_id", "placement_id"),
                "by_category": _dimension_pipeline("article_category", "article_category"),
                "by_device": _dimension_pipeline("device_class", "device_class"),
                "by_use_case": _dimension_pipeline("use_case", "use_case"),
                "top_cards": [
                    card_group_stage,
                    {"$sort": {"rendered": -1, "viewable": -1, "clicked": -1, "_id.provider_id": 1, "_id.card_id": 1, "_id.placement_id": 1}},
                    {"$limit": COMMERCIAL_REPORT_LIST_LIMIT},
                    {"$project": card_projection},
                ],
                "zero_click_high_impression": [
                    card_group_stage,
                    {"$match": {"clicked": 0, "rendered": {"$gte": ZERO_CLICK_MIN_RENDERED}}},
                    {"$sort": {"rendered": -1, "viewable": -1, "_id.provider_id": 1, "_id.card_id": 1, "_id.placement_id": 1}},
                    {"$limit": COMMERCIAL_REPORT_LIST_LIMIT},
                    {"$project": card_projection},
                ],
            }
        },
    ]


def _with_ctr(row: dict) -> dict:
    result = dict(row)
    rendered = int(result.get("rendered") or 0)
    viewable = int(result.get("viewable") or 0)
    clicked = int(result.get("clicked") or 0)
    result.update(
        {
            "rendered": rendered,
            "viewable": viewable,
            "clicked": clicked,
            "rendered_ctr": round(clicked / rendered * 100, 2) if rendered else None,
            "viewable_ctr": round(clicked / viewable * 100, 2) if viewable else None,
        }
    )
    return result


async def build_commercial_analytics(
    collection,
    period: CommercialReportingPeriod,
) -> dict:
    rows = await collection.aggregate(commercial_aggregate_pipeline(period)).to_list(length=1)
    result = rows[0] if rows else {}
    overall_rows = result.get("overall") or []
    overall = _with_ctr(overall_rows[0] if overall_rows else {})

    response = {
        "success": True,
        "period": {
            "from": period.from_date.isoformat(),
            "to": period.to_date.isoformat(),
            "timezone": "Europe/London",
        },
        "overall": overall,
    }
    for name in (
        "by_provider",
        "by_placement",
        "by_category",
        "by_device",
        "by_use_case",
        "top_cards",
        "zero_click_high_impression",
    ):
        limit = (
            COMMERCIAL_REPORT_LIST_LIMIT
            if name in {"top_cards", "zero_click_high_impression"}
            else COMMERCIAL_DIMENSION_LIMIT
        )
        response[name] = [_with_ctr(row) for row in (result.get(name) or [])[:limit]]
    return response
