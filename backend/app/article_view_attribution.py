"""Privacy-bounded attribution for public article-view events."""

import json
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, StrictStr, ValidationError


APPROVED_ATTRIBUTION_SOURCES = (
    "facebook",
    "instagram",
    "threads",
    "newsletter",
    "google",
    "bing",
    "other_search",
    "other_social",
    "referral",
    "direct_or_unknown",
    "unknown",
)
APPROVED_ATTRIBUTION_MEDIA = (
    "social",
    "email",
    "organic_search",
    "referral",
    "direct_or_unknown",
    "unknown",
)
APPROVED_ATTRIBUTION_CAMPAIGNS = (
    "social_publishing",
    "daily_brief",
    "weekly_roundup",
    "breaking_news",
    "unknown",
)
MAX_ARTICLE_VIEW_TRACKING_BODY_BYTES = 1024


class InvalidArticleViewAttribution(ValueError):
    """Raised without submitted input when the narrow request is invalid."""


class ArticleViewAttributionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    utm_source: Optional[StrictStr] = Field(default=None, max_length=32)
    utm_medium: Optional[StrictStr] = Field(default=None, max_length=32)
    utm_campaign: Optional[StrictStr] = Field(default=None, max_length=40)
    referrer_hostname: Optional[StrictStr] = Field(default=None, max_length=253)


class ArticleViewTrackingInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attribution: Optional[ArticleViewAttributionInput] = None


def parse_article_view_tracking_input(
    raw_body: bytes,
) -> ArticleViewTrackingInput | None:
    """Parse the narrow request without exposing rejected values in errors."""
    if not raw_body or not raw_body.strip():
        return None
    if len(raw_body) > MAX_ARTICLE_VIEW_TRACKING_BODY_BYTES:
        raise InvalidArticleViewAttribution() from None
    try:
        payload = json.loads(raw_body)
        return ArticleViewTrackingInput.model_validate(payload)
    except (UnicodeDecodeError, json.JSONDecodeError, ValidationError, TypeError, ValueError):
        raise InvalidArticleViewAttribution() from None


def normalise_article_view_attribution(
    attribution: ArticleViewAttributionInput | None,
) -> dict[str, str]:
    """Return server-owned enums; never return browser-supplied text verbatim."""
    unknown = {"source": "unknown", "medium": "unknown", "campaign": "unknown"}
    if attribution is None:
        return unknown

    if (
        attribution.utm_source == "facebook"
        and attribution.utm_medium == "social"
        and attribution.utm_campaign == "social_publishing"
    ):
        return {
            "source": "facebook",
            "medium": "social",
            "campaign": "social_publishing",
        }

    return unknown
