"""Bounded, read-only first-party aggregates for the Admin Analytics dashboard."""

from datetime import datetime, timedelta, timezone
import logging


ALLOWED_ANALYTICS_PERIODS = ("today", "week", "month")
TOP_ARTICLE_LIMIT = 10
CATEGORY_LIMIT = 50
APPROVED_ADVERTISER_STATUSES = (
    "advert_live",
    "archived",
    "contacted",
    "converted",
    "declined",
    "expired",
    "new",
    "paid_pending_review",
    "payment_expired",
    "payment_pending",
    "renewal_due",
)

logger = logging.getLogger(__name__)


def analytics_period_start(period: str, now: datetime | None = None) -> datetime:
    """Return the UTC start for an approved analytics period."""
    if period not in ALLOWED_ANALYTICS_PERIODS:
        raise ValueError("Unsupported analytics period")

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)

    if period == "today":
        return current.astimezone(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    if period == "week":
        return current - timedelta(days=7)
    return current - timedelta(days=30)


async def _one_aggregate(collection, pipeline: list) -> dict:
    rows = await collection.aggregate(pipeline).to_list(length=1)
    return rows[0] if rows else {}


async def _article_view_summary(database, cutoff: datetime) -> dict:
    """Aggregate public article readership without materialising raw events."""
    pipeline = [
        {"$match": {"viewed_at": {"$gte": cutoff}}},
        {"$group": {"_id": "$article_id", "views": {"$sum": 1}}},
        {
            "$lookup": {
                "from": "articles",
                "let": {
                    "view_article_id": {"$toString": "$_id"},
                    "view_object_id": {
                        "$convert": {
                            "input": "$_id",
                            "to": "objectId",
                            "onError": None,
                            "onNull": None,
                        }
                    },
                },
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$or": [
                                    {"$eq": ["$_id", "$$view_object_id"]},
                                    {"$eq": ["$id", "$$view_article_id"]},
                                ]
                            }
                        }
                    },
                    {
                        "$match": {
                            "archived": {"$ne": True},
                            "manual_review_hidden_from_public": {"$ne": True},
                        }
                    },
                    {
                        "$project": {
                            "_id": 1,
                            "title": 1,
                            "category": 1,
                        }
                    },
                    {"$limit": 1},
                ],
                "as": "article",
            }
        },
        {"$unwind": "$article"},
        {
            "$facet": {
                "totals": [
                    {
                        "$group": {
                            "_id": None,
                            "total": {"$sum": "$views"},
                            "unique_articles": {"$sum": 1},
                        }
                    },
                    {"$project": {"_id": 0, "total": 1, "unique_articles": 1}},
                ],
                "top_articles": [
                    {"$sort": {"views": -1, "article._id": 1}},
                    {"$limit": TOP_ARTICLE_LIMIT},
                    {
                        "$project": {
                            "_id": 0,
                            "id": {"$toString": "$article._id"},
                            "title": {"$ifNull": ["$article.title", ""]},
                            "category": {"$ifNull": ["$article.category", "Uncategorised"]},
                            "views": 1,
                        }
                    },
                ],
                "categories": [
                    {
                        "$group": {
                            "_id": {"$ifNull": ["$article.category", "Uncategorised"]},
                            "views": {"$sum": "$views"},
                        }
                    },
                    {"$sort": {"views": -1, "_id": 1}},
                    {"$limit": CATEGORY_LIMIT},
                    {"$project": {"_id": 0, "category": "$_id", "views": 1}},
                ],
            }
        },
    ]

    result = await _one_aggregate(database.article_views, pipeline)
    totals = (result.get("totals") or [{}])[0]
    total_views = int(totals.get("total") or 0)
    categories = []
    for row in result.get("categories") or []:
        views = int(row.get("views") or 0)
        categories.append(
            {
                "category": str(row.get("category") or "Uncategorised"),
                "views": views,
                "share_percent": round((views / total_views * 100), 1)
                if total_views
                else 0.0,
            }
        )

    return {
        "available": True,
        "total": total_views,
        "unique_articles": int(totals.get("unique_articles") or 0),
        "top_articles": result.get("top_articles") or [],
        "categories": categories,
    }


async def _newsletter_summary(database, cutoff: datetime) -> dict:
    """Return period event counts without exposing tracking or recipient data."""
    accepted = await _one_aggregate(
        database.email_send_opportunities,
        [
            {"$match": {"accepted_at": {"$gte": cutoff}}},
            {
                "$group": {
                    "_id": None,
                    "accepted_opportunities": {"$sum": "$accepted_count"},
                    "send_batches": {"$sum": 1},
                }
            },
            {"$project": {"_id": 0, "accepted_opportunities": 1, "send_batches": 1}},
        ],
    )
    engagement = await _one_aggregate(
        database.email_analytics,
        [
            {
                "$match": {
                    "$or": [
                        {"open_events.timestamp": {"$gte": cutoff}},
                        {"click_events.timestamp": {"$gte": cutoff}},
                    ]
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "opens": {
                        "$size": {
                            "$filter": {
                                "input": {"$ifNull": ["$open_events", []]},
                                "as": "event",
                                "cond": {"$gte": ["$$event.timestamp", cutoff]},
                            }
                        }
                    },
                    "clicks": {
                        "$size": {
                            "$filter": {
                                "input": {"$ifNull": ["$click_events", []]},
                                "as": "event",
                                "cond": {"$gte": ["$$event.timestamp", cutoff]},
                            }
                        }
                    },
                }
            },
            {"$group": {"_id": None, "opens": {"$sum": "$opens"}, "clicks": {"$sum": "$clicks"}}},
            {"$project": {"_id": 0, "opens": 1, "clicks": 1}},
        ],
    )
    return {
        "available": True,
        "accepted_opportunities": int(accepted.get("accepted_opportunities") or 0),
        "send_batches": int(accepted.get("send_batches") or 0),
        "opens": int(engagement.get("opens") or 0),
        "clicks": int(engagement.get("clicks") or 0),
    }


async def _sponsored_summary(database) -> dict:
    """Sponsored counters are lifetime totals in the current storage contract."""
    totals = await _one_aggregate(
        database.sponsored_placements,
        [
            {
                "$group": {
                    "_id": None,
                    "impressions": {"$sum": {"$ifNull": ["$impression_count", 0]}},
                    "clicks": {"$sum": {"$ifNull": ["$click_count", 0]}},
                }
            },
            {"$project": {"_id": 0, "impressions": 1, "clicks": 1}},
        ],
    )
    impressions = int(totals.get("impressions") or 0)
    clicks = int(totals.get("clicks") or 0)
    return {
        "available": True,
        "scope": "lifetime",
        "impressions": impressions,
        "clicks": clicks,
        "ctr_percent": round((clicks / impressions * 100), 1) if impressions else None,
    }


async def _advertiser_summary(database, cutoff: datetime) -> dict:
    """Return period lead counts by status, never lead documents or contact data."""
    result = await _one_aggregate(
        database.advertiser_leads,
        [
            {"$match": {"created_at": {"$gte": cutoff}}},
            {
                "$project": {
                    "_id": 0,
                    "normalised_status": {
                        "$cond": [
                            {"$in": ["$status", list(APPROVED_ADVERTISER_STATUSES)]},
                            "$status",
                            "other",
                        ]
                    },
                }
            },
            {"$group": {"_id": "$normalised_status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1, "_id": 1}},
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$count"},
                    "by_status": {"$push": {"status": "$_id", "count": "$count"}},
                }
            },
            {"$project": {"_id": 0, "total": 1, "by_status": 1}},
        ],
    )
    return {
        "available": True,
        "total": int(result.get("total") or 0),
        "by_status": result.get("by_status") or [],
    }


async def build_admin_analytics_summary(
    database,
    period: str,
    *,
    now: datetime | None = None,
) -> dict:
    """Build independent sections so one unavailable source does not hide the rest."""
    cutoff = analytics_period_start(period, now)
    sections = {}
    builders = (
        ("article_views", lambda: _article_view_summary(database, cutoff)),
        ("newsletter", lambda: _newsletter_summary(database, cutoff)),
        ("sponsored", lambda: _sponsored_summary(database)),
        ("advertisers", lambda: _advertiser_summary(database, cutoff)),
    )
    for name, builder in builders:
        try:
            sections[name] = await builder()
        except Exception:
            logger.warning("Admin analytics section unavailable: %s", name)
            sections[name] = {"available": False}

    return {
        "success": True,
        "period": period,
        "period_start": cutoff.isoformat(),
        **sections,
    }
