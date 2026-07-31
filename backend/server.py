from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header, Request, Body, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import JSONResponse, RedirectResponse, Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
import os
import re
import json
import logging
import httpx
import secrets
import hashlib
from pathlib import Path
from pydantic import BaseModel, EmailStr, Field, StrictBool, field_validator
from typing import List, Optional
import uuid
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from openai import OpenAI
import random
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo
import asyncio
from pathlib import Path
import sys
_THIS_DIR = Path(__file__).resolve().parent
_PARENT_DIR = _THIS_DIR.parent
# Ensure imports work both locally and on Render
if str(_THIS_DIR) not in sys.path: sys.path.insert(0, str(_THIS_DIR))
if str(_PARENT_DIR) not in sys.path: sys.path.insert(0, str(_PARENT_DIR))
try:
    from app import rss_routes
except ModuleNotFoundError:
    from backend.app import rss_routes

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')
LOCAL_DEV_NO_DB = os.getenv("LOCAL_DEV_NO_DB") == "1"
# Import services AFTER loading environment variables
from app.email_service import email_service
from app.news_feed_service import news_feed_service
from app.article_image_resolver import resolve_imported_article_image
from app.facebook_social_asset import (
    ArticleValidationError as SocialAssetArticleValidationError,
    ImageContentError as SocialAssetImageContentError,
    ImageFetchError as SocialAssetImageFetchError,
    ImageURLValidationError as SocialAssetImageURLValidationError,
    TemplateValidationError as SocialAssetTemplateValidationError,
    compose_facebook_local_news_svg,
)
from app.facebook_newsletter_asset import compose_facebook_newsletter_svg
from app.facebook_graphic_types import (
    ARTICLE_GRAPHIC_TYPES as FACEBOOK_ARTICLE_GRAPHIC_TYPES,
    compose_facebook_graphic_svg,
)
from app.instagram_social_asset import (
    ArticleValidationError as InstagramAssetArticleValidationError,
    ImageContentError as InstagramAssetImageContentError,
    ImageFetchError as InstagramAssetImageFetchError,
    ImageURLValidationError as InstagramAssetImageURLValidationError,
    TemplateValidationError as InstagramAssetTemplateValidationError,
    compose_instagram_feed_svg,
    compose_instagram_reels_cover_svg,
    compose_instagram_top_story_svg,
)
from app.local_rss_editorial_policy import (
    is_crime_like as classify_local_crime,
    is_high_value_local_civic_economic_article as classify_high_value_local,
    is_low_utility_article as classify_low_utility_local,
    is_obituary_like as classify_local_obituary,
    is_useful_local_article as classify_useful_local,
    local_editorial_text as build_local_editorial_text,
    local_manual_review_editorial_reason as classify_local_manual_review_reason,
    should_reject_before_local_manual_review as classify_reject_before_local_review,
)
from app.newsletter_token_service import (
    ExpiredNewsletterTokenError,
    InvalidNewsletterTokenError,
    NewsletterTokenConfigurationError,
    NewsletterTokenVersionMismatchError,
    PREFERENCES_PURPOSE,
    REACTIVATE_PURPOSE,
    UNSUBSCRIBE_PURPOSE,
    WrongNewsletterTokenPurposeError,
    newsletter_token_service_from_environment,
)
from app.newsletter_click_tracking import (
    UnsafeNewsletterClickDestination,
    validate_newsletter_click_destination,
)
from app.newsletter_link_security import (
    CHALLENGE_COLLECTION_NAME,
    RATE_LIMIT_COLLECTION_NAME,
    ChallengeResultReason,
    NewsletterChallengeRepository,
    NewsletterRateLimitRepository,
    hash_token as hash_newsletter_challenge_token,
)
from app.newsletter_management_email import (
    CANONICAL_SITE_ORIGIN,
    NewsletterManagementEmailHelper,
    NewsletterManagementEmailPurpose,
    NewsletterManagementEmailRequest,
)
from app.perplexity_service import perplexity_service, ai_budget_available

# Stripe integration for paid job listings
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
import stripe
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY', 'sk_test_emergent')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '').strip()

# Job posting pricing packages (amounts in GBP)
JOB_POSTING_PACKAGES = {
    "free": {"price": 0, "name": "Free Listing", "duration_days": 14, "featured": False},
    "standard": {"price": 15.00, "name": "Standard Listing", "duration_days": 30, "featured": False},
    "featured": {"price": 29.00, "name": "Featured Listing", "duration_days": 30, "featured": True},
    "premium": {"price": 49.00, "name": "Premium Listing", "duration_days": 60, "featured": True}
}

# Advertising pricing packages (amounts in GBP)
ADVERTISING_PACKAGES = {
    "local_starter": {"price": 49.00, "name": "Local Starter", "duration_days": 30, "rotation_weight": 1, "priority": 10},
    "local_featured": {"price": 99.00, "name": "Local Featured", "duration_days": 30, "rotation_weight": 2, "priority": 20},
    "local_partner": {"price": 199.00, "name": "Local Partner", "duration_days": 30, "rotation_weight": 4, "priority": 30},
}

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# =====================================================================================
# IN-MEMORY CACHE FOR PERFORMANCE (reduces TTFB)
# =====================================================================================
from functools import lru_cache
import time

class SimpleCache:
    """Simple in-memory cache with TTL for API responses"""
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
    
    def get(self, key: str, ttl_seconds: int = 60):
        """Get cached value if not expired"""
        if key in self._cache:
            if time.time() - self._timestamps.get(key, 0) < ttl_seconds:
                return self._cache[key]
            else:
                # Expired, remove it
                del self._cache[key]
                del self._timestamps[key]
        return None
    
    def set(self, key: str, value):
        """Set cached value with current timestamp"""
        self._cache[key] = value
        self._timestamps[key] = time.time()
    
    def clear(self):
        """Clear all cached values"""
        self._cache.clear()
        self._timestamps.clear()

# Global cache instance
api_cache = SimpleCache()

# =====================================================================================
# ADMIN AUTHENTICATION
# =====================================================================================
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'changeme')

# Simple token store (in production, use Redis or database)
admin_tokens = {}  # Legacy - kept for backwards compatibility during transition

def generate_admin_token() -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)

async def store_admin_token(token: str, expiry: datetime):
    """Store admin token in MongoDB for distributed access"""
    try:
        await db.admin_tokens.update_one(
            {"token": token},
            {"$set": {"token": token, "expiry": expiry.isoformat()}},
            upsert=True
        )
        # Also keep in memory for single-instance fallback
        admin_tokens[token] = expiry
    except Exception as e:
        logger.warning(f"Failed to store token in DB, using memory only: {e}")
        admin_tokens[token] = expiry

async def verify_admin_token_db(token: str) -> bool:
    """Verify if a token is valid and not expired - checks MongoDB first"""
    try:
        # Check MongoDB first (distributed)
        db_token = await db.admin_tokens.find_one({"token": token})
        if db_token:
            expiry_str = db_token.get("expiry")
            if expiry_str:
                expiry = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))
                if datetime.now(timezone.utc) < expiry:
                    return True
                else:
                    # Token expired, remove it
                    await db.admin_tokens.delete_one({"token": token})
                    return False
    except Exception as e:
        logger.warning(f"DB token check failed, falling back to memory: {e}")
    
    # Fallback to memory (for single-instance or DB failure)
    if token in admin_tokens:
        expiry = admin_tokens[token]
        if datetime.now(timezone.utc) < expiry:
            return True
        else:
            del admin_tokens[token]
    return False

async def delete_admin_token(token: str):
    """Delete admin token from both DB and memory"""
    try:
        await db.admin_tokens.delete_one({"token": token})
    except Exception:
        pass
    if token in admin_tokens:
        del admin_tokens[token]

NEWSLETTER_EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def is_deliverable_newsletter_email(email: str) -> bool:
    """Block invalid, reserved, and test-only addresses before newsletter delivery."""
    e = (email or "").strip().lower()
    if not e or not NEWSLETTER_EMAIL_REGEX.match(e):
        return False

    local, _, domain = e.rpartition("@")
    if not local or not domain:
        return False

    if local.startswith("unsubscribe-test-"):
        return False

    if domain.startswith("example."):
        return False

    if "test" in local and "cheshiretoday" in domain:
        return False

    return True

def verify_admin_token(token: str) -> bool:
    """Sync wrapper - DEPRECATED, use verify_admin_token_db"""
    # Legacy sync check for backwards compatibility
    if token in admin_tokens:
        expiry = admin_tokens[token]
        if datetime.now(timezone.utc) < expiry:
            return True
        else:
            del admin_tokens[token]
    return False

async def get_admin_auth(authorization: Optional[str] = Header(None)) -> bool:
    """Dependency to verify admin authentication - uses MongoDB for distributed tokens"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Extract token from "Bearer <token>" format
    if authorization.startswith("Bearer "):
        token = authorization[7:]

        # Permanent admin token from environment (for operational access)
        permanent_token = os.environ.get("ADMIN_PERMANENT_TOKEN")
        if permanent_token and token == permanent_token:
            return True

        # Existing DB-based token verification
        if await verify_admin_token_db(token):
            return True
    
    raise HTTPException(status_code=401, detail="Invalid or expired token")

# =====================================================================================

# Gemini LLM client using Emergent integration
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Initialize Gemini chat for article generation
def get_gemini_chat(session_id: str, system_message: str) -> LlmChat:
    """Create a Gemini chat instance for article generation"""
    return LlmChat(
        api_key=os.environ.get('EMERGENT_LLM_KEY'),
        session_id=session_id,
        system_message=system_message
    ).with_model("gemini", "gemini-2.5-flash")

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class Article(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    category: str
    author: str = "AI Journalist"
    publishedDate: str
    image: str
    tags: List[str] = []
    featured: bool = False
    source: str = "Perplexity AI"
    scope: str  # "cheshire" or "uk"

class GenerateArticlesRequest(BaseModel):
    count: int = 10
    include_uk_news: bool = True
    rewrite_delay_seconds: int = 0
    public_import_limit: Optional[int] = None

class GenerateArticlesResponse(BaseModel):
    success: bool
    generated: int
    cheshire_articles: int
    uk_articles: int

class SubscribeRequest(BaseModel):
    email: EmailStr
    signup_placement: Optional[str] = None

class SubscribeResponse(BaseModel):
    success: bool
    outcome: str
    message: str


NEWSLETTER_SIGNUP_CONSENT_VERSION = "all_three_newsletters_v1"
NEWSLETTER_SIGNUP_CONSENT_TEXT = (
    "By subscribing, you agree to receive The Daily Brief from Monday to "
    "Saturday, The Weekly Roundup on Sunday, and rare Breaking News Alerts "
    "for major incidents. You can unsubscribe or change your preferences at "
    "any time."
)
NEWSLETTER_SIGNUP_PLACEMENTS = frozenset(
    {"newsletter_landing", "homepage", "article", "footer", "popup"}
)
NEWSLETTER_SIGNUP_DEFAULT_PLACEMENT = "website"
NEWSLETTER_SIGNUP_PREFERENCES = {
    "daily_brief": True,
    "weekly_roundup": True,
    "breaking_news": True,
}

# =====================================================================================
# COMMENTS SYSTEM - Email-based authentication
# =====================================================================================

class CommentUserRegister(BaseModel):
    email: EmailStr
    name: str

class CommentUserLogin(BaseModel):
    email: EmailStr
    code: str  # 6-digit verification code

class CommentCreate(BaseModel):
    article_id: str
    content: str
    parent_id: Optional[str] = None  # For reply threads

class CommentResponse(BaseModel):
    success: bool
    message: str
    comment_id: Optional[str] = None

# =====================================================================================
# NEWSLETTER SEGMENTATION
# =====================================================================================

class NewsletterTokenRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=4096)

    @field_validator("token", mode="before")
    @classmethod
    def normalize_token(cls, value):
        return value.strip() if isinstance(value, str) else value


class SecureNewsletterPreferencesUpdateRequest(NewsletterTokenRequest):
    daily_brief: StrictBool
    weekly_roundup: StrictBool
    breaking_news: StrictBool


class NewsletterSecureLinkRequest(BaseModel):
    email: EmailStr


class NewsletterReactivationConfirmRequest(NewsletterTokenRequest):
    daily_brief: StrictBool
    weekly_roundup: StrictBool
    breaking_news: StrictBool


class NewsletterGenericResponse(BaseModel):
    success: bool
    message: str


class NewsletterSecurePreferences(BaseModel):
    daily_brief: bool
    weekly_roundup: bool
    breaking_news: bool


class NewsletterSecurePreferencesResponse(BaseModel):
    success: bool
    preferences: NewsletterSecurePreferences


class AdvertiseLeadCreate(BaseModel):
    name: str
    email: EmailStr
    business: Optional[str] = None
    budget: Optional[str] = None  # Legacy field kept for backward compatibility
    package_id: Optional[str] = None
    package_price: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    target_area: Optional[str] = None
    message: Optional[str] = None
    tier: Optional[str] = None
    source: Optional[str] = "advertise_page"
    origin_url: Optional[str] = None

class SponsoredPlacementDoc(BaseModel):
    slug: str
    placement: str = "article_sidebar"
    sponsor_name: str
    title: str
    description: Optional[str] = None
    target_url: str
    image_url: Optional[str] = None
    cta_text: str = "Learn more"
    package_tier: Optional[str] = None
    campaign_id: Optional[str] = None
    source_lead_id: Optional[str] = None
    notify_client_on_publish: Optional[bool] = False
    rotation_weight: Optional[int] = None
    active: bool = True
    priority: int = 0
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None

# =====================================================================================
# JOB BOARD SYSTEM
# =====================================================================================

class JobCreate(BaseModel):
    title: str
    company: str
    location: str  # Cheshire town
    job_type: str  # full-time, part-time, contract, remote
    salary: Optional[str] = None
    description: str
    requirements: Optional[str] = None
    apply_url: Optional[str] = None
    apply_email: Optional[str] = None
    category: str = "General"  # Healthcare, Tech, Retail, Hospitality, etc.

# Public job submission (requires contact info for approval workflow)
class JobSubmission(BaseModel):
    title: str
    company: str
    location: str
    job_type: str
    salary: Optional[str] = None
    description: str
    requirements: Optional[str] = None
    apply_url: Optional[str] = None
    apply_email: Optional[str] = None
    category: str = "Other"
    contact_name: str  # Person submitting the job
    contact_email: str  # Email for approval notifications
    contact_phone: Optional[str] = None
    
class JobResponse(BaseModel):
    success: bool
    message: str
    job_id: Optional[str] = None

# Manual Article Creation
class ManualArticleCreate(BaseModel):
    title: str
    summary: Optional[str] = None
    content: str
    category: str
    image: Optional[str] = None
    author: Optional[str] = "Cheshire Today"
    source: Optional[str] = None
    source_url: Optional[str] = None
    tags: Optional[List[str]] = []
    featured: Optional[bool] = False
    scope: Optional[str] = "cheshire"
    force_live: Optional[bool] = False
    location: Optional[str] = None

SUPPORTED_ARTICLE_LOCATIONS = {
    "chester",
    "warrington",
    "crewe",
    "wirral",
    "macclesfield",
    "wilmslow",
    "knutsford",
    "stockport",
    "northwich",
    "cheshire-general",
}

def normalise_manual_article_location(location: Optional[str]) -> Optional[str]:
    """Return a safe location slug for manual article town assignment."""
    if location is None:
        return None

    location_slug = str(location).strip().lower().replace("_", "-")
    if not location_slug:
        return None

    if location_slug not in SUPPORTED_ARTICLE_LOCATIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported article location: {location}")

    return location_slug

# Store for email verification codes (in production, use Redis with TTL)
email_verification_codes = {}

# =====================================================================================

# =====================================================================================
# RSS-ONLY IMAGE MODE
# External providers removed. No static image pools are used for generation.
# These stubs remain only to avoid breaking legacy admin/debug code paths.
# =====================================================================================

LOCATION_IMAGES = {}
CATEGORY_IMAGES = {}
TOPIC_IMAGE_MAPPINGS = {}
CHESHIRE_FALLBACK_IMAGES = []
BANNED_IMAGES = []

WEAK_GENERIC_IMAGE_PATTERNS = [
    "warringtonguardian.co.uk/resources/images/",
    "warringtonguardian.co.uk/resources/images/20771109",
]

def is_weak_generic_image(url: str) -> bool:
    """Block known weak/repeated stock-style images that harm article quality."""
    img = str(url or "").strip().lower()
    if not img:
        return True
    return any(pattern in img for pattern in WEAK_GENERIC_IMAGE_PATTERNS)

def build_manual_review_editorial_metadata(article: dict) -> dict:
    """Describe an existing Manual Review decision without influencing it."""
    content = str(article.get("content") or "").strip()
    reason = str(article.get("manual_review_reason") or "").strip()
    reason_lower = reason.lower()
    source = str(article.get("source") or "").strip().lower()

    if source == "manual entry":
        source_type = "manual_entry"
    elif article.get("is_local_feed") is True:
        source_type = "local_rss"
    elif article.get("ai_rewritten") is True or article.get("is_rewritten") is True:
        source_type = "ai_rewrite"
    elif article.get("source_url"):
        source_type = "rss_or_publisher"
    else:
        source_type = "unknown"

    detected_locality = str(
        article.get("location")
        or article.get("priority_location")
        or article.get("scope")
        or "Not specified"
    ).strip()

    topic_labels = (
        "Community feature",
        "Human-interest",
        "Lifestyle",
        "Local attraction",
        "Retail feature",
        "Hospitality",
        "Tourism",
        "Entertainment",
        "Soft local news",
    )
    editorial_topic = next(
        (label for label in topic_labels if label.lower() in reason_lower),
        str(article.get("category") or "Uncategorised").strip(),
    )

    published_at = article.get("publishedDate") or article.get("published_date")
    review_at = article.get("manual_review_created_at")
    freshness_bucket = "unknown"
    try:
        published_dt = (
            published_at
            if isinstance(published_at, datetime)
            else datetime.fromisoformat(str(published_at).replace("Z", "+00:00"))
        )
        review_dt = (
            review_at
            if isinstance(review_at, datetime)
            else datetime.fromisoformat(str(review_at).replace("Z", "+00:00"))
        )
        if published_dt.tzinfo is None:
            published_dt = published_dt.replace(tzinfo=timezone.utc)
        if review_dt.tzinfo is None:
            review_dt = review_dt.replace(tzinfo=timezone.utc)
        age_days = max(0, (review_dt - published_dt).days)
        freshness_bucket = "fresh" if age_days == 0 else "recent" if age_days <= 7 else "older"
    except (TypeError, ValueError):
        pass

    if "duplicate" in reason_lower:
        duplicate_status = "flagged"
    else:
        duplicate_status = "not_flagged"

    if "moved back to manual review" in reason_lower:
        failed_public_gate = "editorial_review"
    elif any(value in reason_lower for value in ("length", "short", "empty", "needs rewrite")):
        failed_public_gate = "content_length"
    elif any(value in reason_lower for value in ("invented", "unsupported", "repeated", "editorial")):
        failed_public_gate = "editorial_safety"
    elif "location" in reason_lower or "locality" in reason_lower:
        failed_public_gate = "locality"
    elif "fresh" in reason_lower or "older than" in reason_lower:
        failed_public_gate = "freshness"
    elif "topic cap" in reason_lower:
        failed_public_gate = "topic_cap"
    elif "public import cap" in reason_lower:
        failed_public_gate = "public_import_cap"
    elif any(label.lower() in reason_lower for label in topic_labels):
        failed_public_gate = "editorial_relevance"
    else:
        failed_public_gate = "other"

    image_status = (
        "missing"
        if not str(article.get("image") or "").strip()
        else "weak"
        if is_weak_generic_image(str(article.get("image") or ""))
        else "available"
    )

    auto_publish_candidate = bool(
        failed_public_gate in {"public_import_cap", "topic_cap", "freshness"}
        and len(content) >= 1000
        and image_status == "available"
        and duplicate_status == "not_flagged"
    )

    if failed_public_gate in {"editorial_safety", "locality", "editorial_review"}:
        recommendation = "Needs editorial review"
    elif len(content) < 1000 or failed_public_gate == "content_length":
        recommendation = "Needs rewrite"
    elif auto_publish_candidate:
        recommendation = "Strong candidate"
    else:
        recommendation = "Borderline"

    return {
        "routing_reason": reason or "Manual Review reason not recorded",
        "source_type": source_type,
        "detected_locality": detected_locality or "Not specified",
        "editorial_topic": editorial_topic or "Uncategorised",
        "rewrite_status": str(article.get("rewrite_status") or "unknown"),
        "rewrite_length": len(content),
        "image_status": image_status,
        "freshness_bucket": freshness_bucket,
        "duplicate_status": duplicate_status,
        "auto_publish_candidate": auto_publish_candidate,
        "failed_public_gate": failed_public_gate,
        "publication_recommendation": recommendation,
    }

def attach_manual_review_editorial_metadata(article: dict) -> dict:
    if article.get("manual_review_hidden_from_public") is True:
        article["editorial_metadata"] = build_manual_review_editorial_metadata(article)
    return article

def extract_photo_id(url: str) -> str:
    """Return a stable ID for an image URL (strip query params only)."""
    if not url:
        return ""
    return url.split("?")[0]

def is_image_used(url: str, used_photo_ids: set) -> bool:
    """
    Check if an image is already used by comparing photo IDs.
    This properly handles URLs with different query parameters.
    """
    photo_id = extract_photo_id(url)
    return photo_id in used_photo_ids

def add_image_to_used(url: str, used_photo_ids: set) -> None:
    """Add an image's photo ID to the used set."""
    photo_id = extract_photo_id(url)
    if photo_id:
        used_photo_ids.add(photo_id)

async def get_used_images_from_db() -> set:
    """Fetch all currently used photo IDs from the database"""
    try:
        articles = await db.articles.find({}, {"image": 1, "_id": 0}).to_list(1000)
        used_photo_ids = set()
        for art in articles:
            if 'image' in art and art['image']:
                photo_id = extract_photo_id(art['image'])
                if photo_id:
                    used_photo_ids.add(photo_id)
        return used_photo_ids
    except Exception as e:
        logger.error(f"Error fetching used images: {str(e)}")
        return set()

def select_location_image(title: str, content: str, used_photo_ids: set) -> str:
    """RSS-only mode: no location-based fallback images."""
    return None


def select_topic_image(title: str, content: str, used_photo_ids: set) -> str:
    """
    Select a specific topic-based image (e.g. Police, NHS) if keywords match.
    Prioritizes this over generic location matches.
    """
    text = (title + ' ' + content).lower()
    
    for topic, images in TOPIC_IMAGE_MAPPINGS.items():
        if topic in text:
            # Found a matching topic
            available = [
                img for img in images 
                if not is_image_used(img, used_photo_ids)
                and not any(b in img for b in BANNED_IMAGES)
            ]
            if available:
                image = random.choice(available)
                logger.info(f"Selected TOPIC-specific image for '{topic}': {image[-50:]}")
                return image
    return None



def select_unique_image(category: str, used_photo_ids: set, title: str = "", content: str = "") -> str:
    """
    RSS-only image selection.
    - Never returns empty strings.
    - No external providers (Unsplash/Pexels/Pixabay).
    - No static fallback pools.

    If no configured non-empty URL matches, return None.
    """
    # Topic-specific (only if configured and non-empty)
    if title or content:
        try:
            topic_image = select_topic_image(title, content, used_photo_ids)
            topic_image = _clean_img(topic_image)
            if topic_image and not is_image_used(topic_image, used_photo_ids) and not any(b and (b in topic_image) for b in BANNED_IMAGES):
                return topic_image
        except Exception:
            pass

    # Location-specific (currently disabled in RSS-only mode, but keep safe)
    if title or content:
        try:
            location_image = select_location_image(title, content, used_photo_ids)
            location_image = _clean_img(location_image)
            if location_image and not is_image_used(location_image, used_photo_ids) and not any(b and (b in location_image) for b in BANNED_IMAGES):
                return location_image
        except Exception:
            pass

    # Category-specific list (only if you later populate with real URLs)
    category_images = [ _clean_img(i) for i in CATEGORY_IMAGES.get(category, []) ]
    category_images = [i for i in category_images if i]

    available = [
        img for img in category_images
        if not is_image_used(img, used_photo_ids)
        and not any(b and (b in img) for b in BANNED_IMAGES)
    ]

    if available:
        import random
        image = random.choice(available)
        return image

    # RSS-only: no static fallback pool
    return None

async def get_dynamic_image(title: str, category: str, content: str, scope: str, used_photo_ids: set) -> str:
    """
    Get an image for an article.
    Current policy: RSS-only images + static fallback pool (no external image APIs).
    Ensures no duplicate images across the pool.
    """
    if used_photo_ids is None:
        used_photo_ids = set()

    static_image = select_unique_image(category, used_photo_ids, title, content)
    if static_image:
        logger.info(f"Using static pool image for: {title[:40]}...")
    return static_image

def clean_article_content(text: str) -> str:
    """
    Clean article content by removing markdown formatting, AI thinking, and improving readability.
    """
    import re
    
    # CRITICAL: Remove AI thinking/reasoning that shouldn't be in articles
    # These patterns indicate the model output its internal reasoning
    bad_patterns = [
        r'^THOUGHT:.*$',
        r'^I need to write.*$',
        r'^I will write.*$',
        r'^Let me write.*$',
        r'^Here is the article.*$',
        r'^Here\'s the article.*$',
        r'NO markdown formatting.*',
        r'Write naturally as a.*',
        r'words in plain text.*',
        r'Crucially,.*formatting.*',
        r'This means no bold.*',
    ]
    
    for pattern in bad_patterns:
        text = re.sub(pattern, '', text, flags=re.MULTILINE | re.IGNORECASE)
    
    # Remove markdown bold/italic markers
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold** -> bold
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic* -> italic
    text = re.sub(r'__([^_]+)__', r'\1', text)      # __bold__ -> bold
    text = re.sub(r'_([^_]+)_', r'\1', text)        # _italic_ -> italic
    
    # Remove markdown headers
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)  # ## Header -> Header
    
    # Remove markdown links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # [text](url) -> text
    
    # Remove bullet points at start of lines
    text = re.sub(r'^\s*[-*•]\s+', '', text, flags=re.MULTILINE)
    
    # Remove numbered lists formatting
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Clean up extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)  # Multiple newlines -> double newline
    text = re.sub(r'  +', ' ', text)  # Multiple spaces -> single space
    
    return text.strip()

async def generate_article_with_gemini(topic: str, scope: str, category: str, used_photo_ids: set = None, retry_count: int = 0) -> dict:
    """
    Generate an article using Gemini 2.5 Flash with STRICT unique UK image enforcement.
    Images are selected AFTER content generation to match article location/content.
    Returns None if no unique UK image is available (quality over quantity).
    """
    max_retries = 3
    retry_delay = 2  # seconds
    
    try:
        # Track used photo IDs - this MUST include all DB photo IDs
        if used_photo_ids is None:
            used_photo_ids = set()
        
        # GENERATE CONTENT FIRST, then select location-aware image
        if scope == "cheshire":
            prompt = f"""Write a professional news article about: {topic}

Location: Cheshire, UK (mention Knutsford, Wilmslow, Alderley Edge, Chester, or Macclesfield where relevant)

Requirements:
- 300-400 words
- Plain text only, no formatting symbols
- Professional journalistic style
- Include realistic quotes and details

Output format:
HEADLINE
[Your headline here]

ARTICLE
[Your article text here - 3-4 paragraphs]

Start writing the article now:"""
        else:
            prompt = f"""Write a professional news article about: {topic}

Location: United Kingdom

Requirements:
- 300-400 words
- Plain text only, no formatting symbols
- Professional journalistic style
- Include realistic quotes and details

Output format:
HEADLINE
[Your headline here]

ARTICLE
[Your article text here - 3-4 paragraphs]

Start writing the article now:"""
        
        # Create Gemini chat instance with strict system message
        chat = get_gemini_chat(
            session_id=f"article-gen-{uuid4()}",
            system_message="You are a professional British news journalist. Output ONLY the article content. Never output your thinking process, instructions, or meta-commentary. Write the headline and article directly without any preamble."
        )
        
        # Send message to Gemini
        user_message = UserMessage(text=prompt)
        full_text = await chat.send_message(user_message)
        # Guard: some clients return a coroutine from send_message
        import asyncio
        if asyncio.iscoroutine(full_text):
            full_text = await full_text
        full_text = full_text.strip()
        
        # CRITICAL: Check for AI thinking/reasoning in output - this indicates a bad response
        bad_indicators = ['THOUGHT:', 'I need to write', 'I will write', 'Let me write', 
                         'Here is the article', 'Here\'s the article', 'NO markdown',
                         'words in plain text', 'Crucially,', 'This means no bold',
                         'Let\'s brainstorm', 'brainstorm some', 'Let me think', 'I should write',
                         'current/recent', 'Here are some', 'topics to write about']
        
        has_bad_content = any(indicator.lower() in full_text.lower() for indicator in bad_indicators)
        if has_bad_content:
            logger.warning("Detected AI reasoning in output, cleaning and retrying if needed...")
            # Try to extract just the article part if possible
            if 'ARTICLE' in full_text:
                parts = full_text.split('ARTICLE', 1)
                if len(parts) > 1:
                    full_text = parts[1].strip()
            elif '\n\n' in full_text:
                # Try to get content after the first paragraph (which might be reasoning)
                paragraphs = full_text.split('\n\n')
                # Find first paragraph that looks like actual content
                for i, para in enumerate(paragraphs):
                    if not any(ind.lower() in para.lower() for ind in bad_indicators):
                        full_text = '\n\n'.join(paragraphs[i:])
                        break
        
        # Parse HEADLINE and ARTICLE sections if present
        if 'HEADLINE' in full_text and 'ARTICLE' in full_text:
            headline_match = re.search(r'HEADLINE\s*\n(.+?)(?=\n\s*ARTICLE|\n\n)', full_text, re.DOTALL)
            article_match = re.search(r'ARTICLE\s*\n(.+)', full_text, re.DOTALL)
            
            if headline_match and article_match:
                title = headline_match.group(1).strip()
                content = article_match.group(1).strip()
            else:
                # Fallback to first line as title
                lines = full_text.split('\n', 1)
                title = lines[0].strip()
                content = lines[1].strip() if len(lines) > 1 else full_text
        else:
            # Extract title (first line) and content (rest)
            lines = full_text.split('\n', 1)
            title = lines[0].strip().replace('#', '').replace('**', '').strip()
            content = lines[1].strip() if len(lines) > 1 else full_text
        
        # Remove any "HEADLINE" or "ARTICLE" labels from the text
        title = re.sub(r'^HEADLINE[:\s]*', '', title, flags=re.IGNORECASE).strip()
        content = re.sub(r'^ARTICLE[:\s]*', '', content, flags=re.IGNORECASE).strip()
        
        # Remove citation numbers in square brackets [1], [2], etc.
        title = re.sub(r'\[\d+\]', '', title).strip()
        content = re.sub(r'\[\d+\]', '', content).strip()
        
        # Clean up any double spaces created by removing citations
        title = re.sub(r'\s+', ' ', title).strip()
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Clean markdown formatting from content
        content = clean_article_content(content)
        title = clean_article_content(title)
        
        # FINAL VALIDATION: Reject if title/content still contains AI reasoning
        final_bad_check = ['THOUGHT:', 'I need to', 'I will ', 'Let me ', 'Here is', 'Here\'s', 
                          'words in plain', 'NO markdown', 'formatting symbols',
                          'Let\'s brainstorm', 'brainstorm', 'current/recent', 'topics to write']
        
        title_has_bad = any(ind.lower() in title.lower() for ind in final_bad_check)
        content_has_bad = any(ind.lower() in content[:200].lower() for ind in final_bad_check)
        
        if title_has_bad or content_has_bad:
            logger.error(f"Article still contains AI reasoning after cleaning. Title: {title[:50]}")
            if retry_count < max_retries:
                logger.info("Retrying article generation...")
                await asyncio.sleep(1)
                return await generate_article_with_gemini(topic, scope, category, used_photo_ids, retry_count + 1)
            return None
        
        # Validate article has reasonable length
        if len(content) < 100:
            logger.warning(f"Article content too short ({len(content)} chars), retrying...")
            if retry_count < max_retries:
                await asyncio.sleep(1)
                return await generate_article_with_gemini(topic, scope, category, used_photo_ids, retry_count + 1)
            return None
        
        # Generate tags
        tags = []
        if scope == "cheshire":
            tags.append("cheshire")
        else:
            tags.append("uk")
        tags.append(category.lower().replace(' ', '-'))
        
        # Return article without image - image will be fetched separately via Unsplash API
        logger.info(f"Generated clean article: '{title[:40]}...' ({len(content)} chars)")
        
        return {
            'title': title,
            'content': content,
            'category': category,
            'tags': tags,
            'image': None  # Image will be fetched via get_dynamic_image()
        }
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error generating article (attempt {retry_count + 1}/{max_retries}): {error_msg}")
        
        # Retry on connection errors or rate limits
        if retry_count < max_retries and ("Connection" in error_msg or "500" in error_msg or "429" in error_msg):
            wait_time = retry_delay * (retry_count + 1)  # Exponential backoff
            logging.info(f"Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            return await generate_article_with_gemini(topic, scope, category, used_photo_ids, retry_count + 1)
        
        # If all retries failed, raise the error
        raise

async def fetch_trending_headlines_from_rss(count: int = 5) -> List[dict]:
    """
    Fetch trending headlines from actual RSS feeds (FREE).
    Returns the latest headlines from BBC, Sky, Guardian etc.
    This replaces the Gemini-based headline generation.
    """
    try:
        logger.info("Fetching trending headlines from RSS feeds (FREE)...")
        
        # Fetch from all RSS feeds
        all_articles = await news_feed_service.fetch_all_feeds()
        
        # Get the most recent unique headlines
        headlines = []
        seen_titles = set()
        
        for article in all_articles[:count * 3]:  # Get extra to filter duplicates
            title = article.get('title', '').strip()
            if not title or title.lower() in seen_titles:
                continue
            
            # Determine scope based on content
            is_local = article.get('is_cheshire_related', False)
            scope = 'cheshire' if is_local else 'uk'
            
            headlines.append({
                'headline': title,
                'category': article.get('category', 'UK News'),
                'scope': scope,
                'source': article.get('source', 'BBC News'),
                'source_url': article.get('source_url', '')
            })
            seen_titles.add(title.lower())
            
            if len(headlines) >= count:
                break
        
        logger.info(f"Retrieved {len(headlines)} trending headlines from RSS")
        return headlines
        
    except Exception as e:
        logger.error(f"Error fetching RSS headlines: {str(e)}")
        return []


async def fetch_trending_headlines(scope: str, count: int = 5) -> List[tuple]:
    """
    Fetch trending news headlines using Gemini to ensure content is current and important.
    Returns a list of (topic, category) tuples.
    """
    try:
        logger.info(f"Fetching trending headlines for {scope}...")
        
        # Define valid categories - simplified to 8 main categories
        valid_categories = ["Local News", "UK News", "Business", "Finance", "Tax", "AI & Tech"]
        valid_categories_str = ", ".join(valid_categories)
        
        if scope == "cheshire":
            prompt = f"""Identify the top {count} most important news stories in Cheshire, UK.
            Focus on Knutsford, Wilmslow, Alderley Edge, Macclesfield, and Chester.
            Assign each story a category from: [{valid_categories_str}].
            
            Return in this format (one per line):
            Headline | Category"""
        else:
            prompt = f"""Identify the top {count} most important news stories in the United Kingdom.
            Focus on major national developments.
            Assign each story a category from: [{valid_categories_str}].
            
            Return in this format (one per line):
            Headline | Category"""

        # Create Gemini chat instance
        chat = get_gemini_chat(
            session_id=f"headlines-{scope}-{uuid4()}",
            system_message="You are a news editor. Return headlines in the exact format requested."
        )
        
        # Send message to Gemini
        user_message = UserMessage(text=prompt)
        content = await chat.send_message(user_message)
        content = content.strip()
        
        lines = content.split('\n')
        
        topics = []
        for line in lines:
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    topic = parts[0].strip()
                    category = parts[1].strip()
                    # Validate category - must be in our 8 main categories
                    if category not in valid_categories:
                        category = "Local News" if scope == "cheshire" else "UK News"
                    topics.append((topic, category))
        
        logger.info(f"Found {len(topics)} trending topics for {scope}")
        return topics
        
    except Exception as e:
        logger.error(f"Error fetching trending headlines: {str(e)}")
        return []

# =====================================================================================
# ADMIN LOGIN ENDPOINT
# =====================================================================================
class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminLoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    message: str
    expires_in: int = 86400  # 24 hours in seconds


# =====================================================================================
# AUTHORITY PAGES (GUIDES / MONEY PAGES)
# Purpose: 15–25 commercial + authority pages that power affiliate revenue.
# Frontend route: /guides/:slug (AuthorityPage.jsx)
# API:
#   - GET /api/authority-pages           (list)
#   - GET /api/authority-pages/{slug}    (detail)
# Storage: MongoDB collection "authority_pages"
# =====================================================================================

class AuthoritySection(BaseModel):
    type: str = Field(..., description="e.g. intro, section, tool, faq")
    title: Optional[str] = None
    content: Optional[str] = None
    name: Optional[str] = None
    rating: Optional[float] = None
    affiliate_link: Optional[str] = None

class AuthorityPageDoc(BaseModel):
    slug: str = Field(..., description="URL slug, e.g. best-mortgage-rates-uk")
    title: str
    category: str = "Finance"
    monetisation: str = "affiliate"  # affiliate | none | other
    status: str = "draft"  # draft | live
    sections: List[AuthoritySection] = []
    updatedAt: Optional[str] = None

AUTHORITY_AFFILIATE_LINKS = {
    "best-business-bank-accounts-uk": {
        "Starling Business": "",
        "Tide": "",
        "Monzo Business": "",
        "Wise Business": "",
    },
    "best-accounting-software-uk": {
        "Xero": "",
        "QuickBooks Online": "https://quickbooks.intuit.com/uk/?cid=aff_uk_CJ_always_on___123099-123099",
        "FreeAgent": "",
        "Sage Accounting": "",
    },
    "best-isa-platforms-uk": {},
    "cheap-energy-tariffs-uk": {},
    "best-broadband-deals-uk": {},
    "council-tax-bands-cheshire": {},
}

def _ap_apply_affiliate_links(out: dict) -> dict:
    slug = str(out.get("slug") or "").strip()
    link_map = AUTHORITY_AFFILIATE_LINKS.get(slug) or {}
    sections = out.get("sections")

    if not isinstance(sections, list) or not link_map:
        return out

    enriched_sections = []
    for section in sections:
        if not isinstance(section, dict):
            enriched_sections.append(section)
            continue

        item = dict(section)
        if item.get("type") == "tool" and not str(item.get("affiliate_link") or "").strip():
            tool_name = str(item.get("name") or "").strip()
            mapped = str(link_map.get(tool_name) or "").strip()
            if mapped:
                item["affiliate_link"] = mapped

        enriched_sections.append(item)

    out["sections"] = enriched_sections
    return out

def _ap_serialize(doc: dict) -> dict:
    if not isinstance(doc, dict):
        return {}
    out = dict(doc)
    if "_id" in out:
        out["id"] = str(out["_id"])
        del out["_id"]
    return _ap_apply_affiliate_links(out)

@api_router.get("/authority-pages")
async def list_authority_pages(limit: int = 50, skip: int = 0, status: Optional[str] = None):
    """
    List authority pages for homepage modules / navigation.
    """
    q = {}
    if status:
        q["status"] = status
    docs = await db.authority_pages.find(
        q,
        {"_id": 1, "slug": 1, "title": 1, "category": 1, "monetisation": 1, "status": 1, "updatedAt": 1}
    ).sort("updatedAt", -1).skip(skip).limit(limit).to_list(limit)
    return [_ap_serialize(d) for d in docs]

@api_router.get("/authority-pages/{slug}")
async def get_authority_page(slug: str):
    """
    Get a single authority page by slug.
    """
    doc = await db.authority_pages.find_one({"slug": slug})
    if not doc:
        raise HTTPException(status_code=404, detail="Not Found")
    return _ap_serialize(doc)


@api_router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest):
    """
    Admin login endpoint - returns a token for authenticated admin access.
    Token is valid for 24 hours and stored in MongoDB for distributed access.
    """
    if request.username == ADMIN_USERNAME and request.password == ADMIN_PASSWORD:
        # Generate token
        token = generate_admin_token()
        expiry = datetime.now(timezone.utc) + timedelta(hours=24)
        
        # Store in MongoDB for distributed access across replicas
        await store_admin_token(token, expiry)
        
        logger.info(f"Admin login successful for: {request.username}")
        return AdminLoginResponse(
            success=True,
            token=token,
            message="Login successful",
            expires_in=86400
        )
    else:
        logger.warning(f"Failed admin login attempt for: {request.username}")
        raise HTTPException(status_code=401, detail="Invalid username or password")

@api_router.post("/admin/logout")
async def admin_logout(authorization: Optional[str] = Header(None)):
    """Logout and invalidate the admin token"""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        await delete_admin_token(token)
    return {"success": True, "message": "Logged out successfully"}

@api_router.get("/admin/verify")
async def verify_admin_token_endpoint(authorized: bool = Depends(get_admin_auth)):
    """Verify if the current token is valid"""
    return {"valid": True, "message": "Token is valid"}



@api_router.get("/admin/articles/counts")
async def admin_article_counts():
    """Quick DB counts for operational verification (visible vs archived)."""
    try:
        total = await db.articles.count_documents({})
        visible = await db.articles.count_documents({"$or": [{"archived": {"$exists": False}}, {"archived": False}]})
        archived = await db.articles.count_documents({"archived": True})
        featured = await db.articles.count_documents({"featured": True, "$or": [{"archived": {"$exists": False}}, {"archived": False}]})
        priority = await db.articles.count_documents({"is_priority_cheshire": True, "$or": [{"archived": {"$exists": False}}, {"archived": False}]})
        return {
            "total": total,
            "visible": visible,
            "archived": archived,
            "visible_featured": featured,
            "visible_priority": priority
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _serialize_sponsored_placement(doc):
    if not doc:
        return None
    out = dict(doc)
    out["id"] = str(out.get("_id", ""))
    out.pop("_id", None)
    return out


def _sponsored_rotation_weight(doc):
    """Return weighted rotation score for sponsored advert serving."""
    try:
        explicit = int(doc.get("rotation_weight") or 0)
        if explicit > 0:
            return min(explicit, 20)
    except Exception:
        pass

    tier = str(doc.get("package_tier") or "").lower()
    if "partner" in tier or "premium" in tier:
        return 4
    if "featured" in tier:
        return 2
    return 1


@api_router.get("/sponsored-placements")
async def get_sponsored_placements(placement: str = "article_sidebar", limit: int = 1, slug: str = "", campaign_id: str = ""):
    """Public endpoint - Return active sponsored placements for a page slot using weighted rotation or forced preview."""
    try:
        import random

        now_iso = datetime.now(timezone.utc).isoformat()
        safe_limit = max(1, min(int(limit or 1), 5))
        query = {
            "placement": str(placement or "article_sidebar").strip(),
            "active": True,
            "$and": [
                {"$or": [{"starts_at": {"$exists": False}}, {"starts_at": None}, {"starts_at": ""}, {"starts_at": {"$lte": now_iso}}]},
                {"$or": [{"ends_at": {"$exists": False}}, {"ends_at": None}, {"ends_at": ""}, {"ends_at": {"$gte": now_iso}}]},
            ],
        }

        clean_slug = str(slug or "").strip()
        clean_campaign_id = str(campaign_id or "").strip()
        if clean_slug:
            query["slug"] = clean_slug
        elif clean_campaign_id:
            query["campaign_id"] = clean_campaign_id

        cursor = db.sponsored_placements.find(query).sort([("priority", -1), ("updated_at", -1)]).limit(50)
        candidates = [doc async for doc in cursor]

        if not candidates:
            return {"success": True, "placements": []}

        if clean_slug or clean_campaign_id:
            return {"success": True, "placements": [_serialize_sponsored_placement(candidates[0])]}

        if safe_limit == 1:
            weights = [_sponsored_rotation_weight(doc) for doc in candidates]
            chosen = random.choices(candidates, weights=weights, k=1)[0]
            return {"success": True, "placements": [_serialize_sponsored_placement(chosen)]}

        placements = [_serialize_sponsored_placement(doc) for doc in candidates[:safe_limit]]
        return {"success": True, "placements": placements}
    except Exception as e:
        logger.error(f"Error getting sponsored placements: {str(e)}")
        return {"success": False, "placements": []}


@api_router.post("/sponsored-placements/{slug}/impression")
async def track_sponsored_placement_impression(slug: str):
    """Public endpoint - Track a sponsored placement impression."""
    try:
        clean_slug = str(slug or "").strip()
        if not clean_slug:
            return {"success": False}

        await db.sponsored_placements.update_one(
            {"slug": clean_slug},
            {
                "$inc": {"impression_count": 1},
                "$set": {"last_impression_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        return {"success": True}
    except Exception as e:
        logger.error(f"Error tracking sponsored placement impression: {str(e)}")
        return {"success": False}


@api_router.post("/sponsored-placements/{slug}/click")
async def track_sponsored_placement_click(slug: str):
    """Public endpoint - Track a sponsored placement click."""
    try:
        clean_slug = str(slug or "").strip()
        if not clean_slug:
            return {"success": False}

        await db.sponsored_placements.update_one(
            {"slug": clean_slug},
            {
                "$inc": {"click_count": 1},
                "$set": {"last_click_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        return {"success": True}
    except Exception as e:
        logger.error(f"Error tracking sponsored placement click: {str(e)}")
        return {"success": False}


@api_router.get("/admin/sponsored-placements")
async def get_admin_sponsored_placements(limit: int = 100, auth: bool = Depends(get_admin_auth)):
    """Admin endpoint - List sponsored placements including inactive adverts."""
    try:
        safe_limit = max(1, min(int(limit or 100), 300))
        cursor = db.sponsored_placements.find({}).sort([("active", -1), ("priority", -1), ("updated_at", -1)]).limit(safe_limit)
        placements = [_serialize_sponsored_placement(doc) async for doc in cursor]
        return {"success": True, "placements": placements, "total": len(placements)}
    except Exception as e:
        logger.error(f"Error getting admin sponsored placements: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not load sponsored placements")


async def _latest_public_article_url_for_ad_preview():
    """Return a recent public article URL suitable for sponsored advert preview links."""
    try:
        query = {"$or": [{"archived": {"$exists": False}}, {"archived": False}]}
        article = await db.articles.find_one(
            query,
            {"_id": 1, "id": 1, "title": 1, "publishedDate": 1, "created_at": 1},
            sort=[("publishedDate", -1), ("created_at", -1)]
        )
        if not article:
            return "https://cheshiretoday.co.uk"

        article_id = str(article.get("_id") or article.get("id"))
        slug = _article_slug_from_title(article.get("title") or "article")
        return f"https://cheshiretoday.co.uk/article/{article_id}/{slug}"
    except Exception as e:
        logger.error(f"Could not build sponsored advert preview article URL: {str(e)}")
        return "https://cheshiretoday.co.uk"


async def send_sponsored_advert_live_email(source_lead_id: str, campaign_id: str = "", placement_doc: dict = None):
    """Email the advertiser when their sponsored advert has been published."""
    try:
        clean_lead_id = str(source_lead_id or "").strip()
        if not ObjectId.is_valid(clean_lead_id):
            return False

        oid = ObjectId(clean_lead_id)
        clean_campaign_id = str(campaign_id or "").strip()

        claim_query = {
            "_id": oid,
            "advert_live_notification_sent": {"$ne": True},
            "advert_live_notification_sending": {"$ne": True},
        }
        claim = await db.advertiser_leads.update_one(
            claim_query,
            {"$set": {
                "advert_live_notification_sending": True,
                "advert_live_notification_started_at": datetime.utcnow(),
                "advert_live_notification_campaign_id": clean_campaign_id,
            }}
        )

        if claim.modified_count == 0:
            return False

        lead = await db.advertiser_leads.find_one({"_id": oid})
        if not lead:
            return False

        email = str(lead.get("email") or "").strip()
        if not email:
            await db.advertiser_leads.update_one(
                {"_id": oid},
                {"$set": {
                    "advert_live_notification_sent": False,
                    "advert_live_notification_error": "Missing client email",
                    "advert_live_notification_checked_at": datetime.utcnow(),
                }, "$unset": {"advert_live_notification_sending": ""}}
            )
            return False

        placement_query = {}
        if clean_campaign_id:
            placement_query["campaign_id"] = clean_campaign_id
        elif placement_doc and placement_doc.get("slug"):
            placement_query["slug"] = placement_doc.get("slug")

        placements = []
        if placement_query:
            cursor = db.sponsored_placements.find(placement_query).sort([("placement", 1), ("updated_at", -1)])
            placements = [doc async for doc in cursor]

        if not placements and placement_doc:
            placements = [placement_doc]

        preview_article_base_url = await _latest_public_article_url_for_ad_preview()
        preview_homepage_base_url = "https://cheshiretoday.co.uk"

        import html as _html
        import urllib.parse as _urlparse

        def build_preview_link(slot):
            if not slot:
                return preview_article_base_url

            slot_name = str(slot.get("placement") or "article_sidebar").strip()
            slot_campaign = str(slot.get("campaign_id") or clean_campaign_id or "").strip()
            slot_slug = str(slot.get("slug") or "").strip()
            anchor_key = slot_campaign or slot_slug or "advert"
            params = {"sponsored_ad_placement": slot_name}
            if slot_campaign:
                params["sponsored_ad_campaign"] = slot_campaign
            elif slot_slug:
                params["sponsored_ad_slug"] = slot_slug

            base_url = preview_homepage_base_url if slot_name.startswith("homepage_") else preview_article_base_url
            return f"{base_url}?{_urlparse.urlencode(params)}#sponsored-advert-{slot_name}-{anchor_key}"

        preview_links = []
        seen_slots = set()
        for slot in placements:
            slot_name = str(slot.get("placement") or "article_sidebar").strip()
            if slot_name in seen_slots:
                continue
            seen_slots.add(slot_name)
            label = (
                "Desktop homepage advert" if slot_name == "homepage_sidebar"
                else "Mobile homepage advert" if slot_name == "homepage_mobile"
                else "Desktop sidebar advert" if slot_name == "article_sidebar"
                else "Mobile in-article advert" if slot_name == "article_mobile"
                else "Advert preview"
            )
            preview_links.append((label, build_preview_link(slot)))

        if not preview_links:
            preview_links.append(("View your advert", preview_article_base_url))

        tier = str(lead.get("tier") or lead.get("package_tier") or (placements[0].get("package_tier") if placements else "") or "Advertising package").strip()
        business = str(lead.get("business") or lead.get("name") or (placements[0].get("sponsor_name") if placements else "") or "your business").strip()
        starts_at = placements[0].get("starts_at") if placements else ""
        ends_at = placements[0].get("ends_at") if placements else ""

        links_html = "".join(
            f'<p><a href="{_html.escape(url)}" style="background:#059669;color:#ffffff;padding:12px 18px;border-radius:8px;text-decoration:none;font-weight:bold;display:inline-block;">{_html.escape(label)}</a></p>'
            f'<p style="font-size:13px;color:#555;word-break:break-word;">{_html.escape(url)}</p>'
            for label, url in preview_links
        )

        html_content = f"""
        <h2>Your Cheshire Today advert is now live</h2>
        <p>Good news — your sponsored advert has been reviewed and published on Cheshire Today.</p>
        <p><strong>Package:</strong> {_html.escape(tier)}</p>
        <p><strong>Business:</strong> {_html.escape(business)}</p>
        {f'<p><strong>Campaign start:</strong> {_html.escape(str(starts_at))}</p>' if starts_at else ''}
        {f'<p><strong>Campaign end:</strong> {_html.escape(str(ends_at))}</p>' if ends_at else ''}
        <hr>
        <h3>View your advert</h3>
        <p>Use the links below to open the homepage or an article page and jump directly to your advert card.</p>
        {links_html}
        <p><strong>Please note:</strong> normal visitors see adverts in rotation, so your advert may not appear on every page load. The preview link above forces your advert to display so you can check it directly.</p>
        <p>If you need a wording, image, logo or link change, reply to this email.</p>
        <p>Thank you for advertising with Cheshire Today.</p>
        """

        sent = bool(email_service._send_email(
            to_email=email,
            subject="Your Cheshire Today advert is now live",
            html_content=html_content,
        ))

        await db.advertiser_leads.update_one(
            {"_id": oid},
            {"$set": {
                "advert_live_notification_sent": sent,
                "advert_live_notification_checked_at": datetime.utcnow(),
                "advert_live_notification_error": "" if sent else "Email service returned false",
            }, "$unset": {"advert_live_notification_sending": ""}}
        )

        return sent
    except Exception as email_error:
        logger.error(f"Failed to send sponsored advert live email: {str(email_error)}")
        try:
            if ObjectId.is_valid(str(source_lead_id or "")):
                await db.advertiser_leads.update_one(
                    {"_id": ObjectId(str(source_lead_id))},
                    {"$set": {
                        "advert_live_notification_sent": False,
                        "advert_live_notification_error": str(email_error),
                        "advert_live_notification_checked_at": datetime.utcnow(),
                    }, "$unset": {"advert_live_notification_sending": ""}}
                )
        except Exception:
            pass
        return False


@api_router.post("/admin/sponsored-placements/upsert")
async def upsert_sponsored_placement(payload: SponsoredPlacementDoc, auth: bool = Depends(get_admin_auth)):
    """Admin endpoint - Upsert a manual sponsored placement by slug."""
    doc = payload.model_dump()
    doc["slug"] = str(doc.get("slug") or "").strip()
    doc["placement"] = str(doc.get("placement") or "article_sidebar").strip()
    doc["sponsor_name"] = str(doc.get("sponsor_name") or "").strip()
    doc["title"] = str(doc.get("title") or "").strip()
    doc["target_url"] = str(doc.get("target_url") or "").strip()
    doc["package_tier"] = str(doc.get("package_tier") or "").strip()
    doc["campaign_id"] = str(doc.get("campaign_id") or "").strip()
    doc["source_lead_id"] = str(doc.get("source_lead_id") or "").strip()
    doc["notify_client_on_publish"] = bool(doc.get("notify_client_on_publish"))
    try:
        doc["rotation_weight"] = int(doc.get("rotation_weight") or 0) or None
    except Exception:
        doc["rotation_weight"] = None

    if not doc["slug"] or not doc["sponsor_name"] or not doc["title"] or not doc["target_url"]:
        raise HTTPException(status_code=400, detail="slug, sponsor_name, title and target_url are required")

    allowed_target_schemes = ("https://", "http://", "mailto:")
    if not doc["target_url"].lower().startswith(allowed_target_schemes):
        raise HTTPException(status_code=400, detail="target_url must start with http://, https:// or mailto:")

    doc["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.sponsored_placements.update_one({"slug": doc["slug"]}, {"$set": doc, "$setOnInsert": {"created_at": doc["updated_at"]}}, upsert=True)
    saved = await db.sponsored_placements.find_one({"slug": doc["slug"]})

    live_notification_sent = False
    if doc.get("active") and doc.get("source_lead_id") and doc.get("notify_client_on_publish"):
        live_notification_sent = await send_sponsored_advert_live_email(
            source_lead_id=doc.get("source_lead_id"),
            campaign_id=doc.get("campaign_id"),
            placement_doc=saved,
        )

    return {
        "success": True,
        "placement": _serialize_sponsored_placement(saved),
        "live_notification_sent": live_notification_sent,
    }


@api_router.delete("/admin/sponsored-placements/{slug}")
async def delete_admin_sponsored_placement(slug: str, auth: bool = Depends(get_admin_auth)):
    """Admin endpoint - Delete a sponsored placement by slug."""
    try:
        result = await db.sponsored_placements.delete_one({"slug": str(slug or "").strip()})
        return {"success": True, "deleted_count": result.deleted_count}
    except Exception as e:
        logger.error(f"Error deleting sponsored placement: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not delete sponsored placement")


def _serialize_advertiser_lead(doc):
    if not doc:
        return None
    out = dict(doc)
    out["id"] = str(out.get("_id", ""))
    out.pop("_id", None)
    for key, value in list(out.items()):
        if hasattr(value, "isoformat"):
            out[key] = value.isoformat()
    return out


@api_router.get("/admin/advertiser-leads")
async def get_admin_advertiser_leads(status: str = "", limit: int = 50, auth: bool = Depends(get_admin_auth)):
    """Admin endpoint - List advertiser enquiries."""
    try:
        safe_limit = max(1, min(int(limit or 50), 200))
        query = {}
        clean_status = str(status or "").strip()
        if clean_status:
            query["status"] = clean_status

        cursor = db.advertiser_leads.find(query).sort("created_at", -1).limit(safe_limit)
        leads = [_serialize_advertiser_lead(doc) async for doc in cursor]

        total = await db.advertiser_leads.count_documents(query)
        new_count = await db.advertiser_leads.count_documents({"status": "new"})

        return {
            "success": True,
            "leads": leads,
            "total": total,
            "new_count": new_count,
        }
    except Exception as e:
        logger.error(f"Error getting advertiser leads: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not load advertiser leads")


@api_router.post("/admin/advertiser-leads/{lead_id}/status")
async def update_admin_advertiser_lead_status(lead_id: str, request: Request, auth: bool = Depends(get_admin_auth)):
    """Admin endpoint - Update advertiser enquiry status."""
    try:
        body = await request.json()
        status = str(body.get("status") or "").strip().lower()
        notes = str(body.get("notes") or "").strip()

        allowed = {"new", "contacted", "converted", "declined", "archived", "advert_live", "renewal_due", "expired"}
        if status not in allowed:
            raise HTTPException(status_code=400, detail="Invalid status")

        result = await db.advertiser_leads.update_one(
            {"_id": ObjectId(lead_id)},
            {"$set": {"status": status, "admin_notes": notes, "status_updated_at": datetime.utcnow()}}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Advertiser lead not found")

        saved = await db.advertiser_leads.find_one({"_id": ObjectId(lead_id)})
        return {"success": True, "lead": _serialize_advertiser_lead(saved)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating advertiser lead status: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not update advertiser lead")


@api_router.delete("/admin/advertiser-leads/{lead_id}")
async def delete_admin_advertiser_lead(lead_id: str, auth: bool = Depends(get_admin_auth)):
    """Admin endpoint - Delete an advertiser enquiry."""
    try:
        if not ObjectId.is_valid(lead_id):
            raise HTTPException(status_code=400, detail="Invalid advertiser lead id")

        result = await db.advertiser_leads.delete_one({"_id": ObjectId(lead_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Advertiser lead not found")

        return {"success": True, "deleted_count": result.deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting advertiser lead: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not delete advertiser lead")


@api_router.post("/admin/authority-pages/upsert")
async def upsert_authority_page(payload: AuthorityPageDoc, auth: bool = Depends(get_admin_auth)):
    """
    Upsert an authority page by slug (local/staging admin utility).
    """
    doc = payload.model_dump()
    if not doc.get("updatedAt"):
        doc["updatedAt"] = datetime.now(timezone.utc).isoformat()
    await db.authority_pages.update_one({"slug": doc["slug"]}, {"$set": doc}, upsert=True)
    saved = await db.authority_pages.find_one({"slug": doc["slug"]})
    return _ap_serialize(saved)

@api_router.post("/admin/seed-authority-pages")
async def seed_authority_pages(auth: bool = Depends(get_admin_auth)):
    """
    Seed a minimal set of authority pages (draft) so /guides/* links resolve.
    Safe to call multiple times (upsert by slug).
    """
    now = datetime.now(timezone.utc).isoformat()
    seeds = [
        {
            "slug": "best-mortgage-rates-uk",
            "title": "Best mortgage rates in the UK (compare deals & lenders)",
            "category": "Finance",
            "monetisation": "affiliate",
            "status": "draft",
            "updatedAt": now,
            "sections": [
                {"type": "intro", "content": "This guide will compare mortgage options and explain how to find the right deal. (Draft seed)"},
                {"type": "tool", "name": "Mortgage comparison tool", "rating": 0, "affiliate_link": ""}
            ]
        },
        {
            "slug": "best-credit-cards-uk",
            "title": "Best credit cards in the UK (0% offers, rewards, and business cards)",
            "category": "Finance",
            "monetisation": "affiliate",
            "status": "draft",
            "updatedAt": now,
            "sections": [
                {"type": "intro", "content": "This guide will compare card types and show how to choose based on eligibility and APR. (Draft seed)"},
                {"type": "tool", "name": "Credit card comparison tool", "rating": 0, "affiliate_link": ""}
            ]
        },
        {
            "slug": "best-savings-accounts-uk",
            "title": "Best savings accounts in the UK (easy access, fixed, and ISA options)",
            "category": "Finance",
            "monetisation": "affiliate",
            "status": "draft",
            "updatedAt": now,
            "sections": [
                {"type": "intro", "content": "This guide will compare savings types and explain how to maximise interest safely. (Draft seed)"},
                {"type": "tool", "name": "Savings comparison tool", "rating": 0, "affiliate_link": ""}
            ]
        },
        {
            "slug": "council-tax-bands-cheshire",
            "title": "Council tax bands in Cheshire: how to check, challenge, and estimate costs",
            "category": "Tax",
            "monetisation": "affiliate",
            "status": "draft",
            "updatedAt": now,
            "sections": [
                {"type": "intro", "content": "Plain-English guide to council tax bands across Cheshire and what affects your bill. (Draft seed)"},
            ]
        },
    ]
    col = db.authority_pages
    upserts = 0
    for doc in seeds:
        res = await col.update_one({"slug": doc["slug"]}, {"$set": doc}, upsert=True)
        if res.upserted_id is not None or res.modified_count:
            upserts += 1
    total = await col.count_documents({})
    return {"success": True, "upserts": upserts, "total": total}

# =====================================================================================

async def _generate_articles_internal(
    request: GenerateArticlesRequest,
) -> GenerateArticlesResponse:
    """
    Generate articles using HYBRID approach (cost-optimized):
    - RSS feeds for UK news (FREE) with original images
    - Perplexity AI only for Cheshire-specific searches
    
    NOTE: This endpoint now uses real news instead of AI-generated content.
    """
    try:
        # Use the hybrid news import approach
        hybrid_request = HybridNewsRequest(
            cheshire_articles=int(request.count * 0.6),  # 60% Cheshire
            uk_articles=int(request.count * 0.4) if request.include_uk_news else 0,
            use_perplexity=True,
            rewrite_delay_seconds=max(0, int(0 if getattr(request, "rewrite_delay_seconds", None) is None else getattr(request, "rewrite_delay_seconds"))),
            public_import_limit=getattr(request, "public_import_limit", None)
        )
        
        result = await _import_hybrid_news_internal(hybrid_request)
        
        cheshire_count = result.get('cheshire_articles', 0)
        uk_count = result.get('uk_articles', 0)
        total = result.get('total_imported', 0)
        
        logger.info(f"Hybrid article generation: {total} total ({cheshire_count} Cheshire, {uk_count} UK)")
        
        return GenerateArticlesResponse(
            success=total > 0,
            generated=total,
            cheshire_articles=cheshire_count,
            uk_articles=uk_count
        )
    except Exception as e:
        logging.error(f"Error in generate_articles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/generate-articles", response_model=GenerateArticlesResponse)
async def generate_articles(
    request: GenerateArticlesRequest,
    authorized: bool = Depends(get_admin_auth),
):
    return await _generate_articles_internal(request)


# ============================================================================
# REAL NEWS FEED ENDPOINTS
# ============================================================================

@api_router.get("/real-news")
async def get_real_news(category: Optional[str] = None, limit: int = 20):
    """
    Fetch real news from BBC, Sky News, Guardian, and other UK sources.
    This returns actual news articles from RSS feeds, not AI-generated content.
    """
    try:
        if category:
            articles = await news_feed_service.fetch_category_feeds(category)
        else:
            articles = await news_feed_service.fetch_all_feeds()
        
        # Limit results
        articles = articles[:limit]
        
        return {
            "success": True,
            "count": len(articles),
            "articles": articles,
            "source": "Real news from BBC, Sky News, Guardian RSS feeds"
        }
    except Exception as e:
        logger.error(f"Error fetching real news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/real-news/local")
async def get_local_real_news(limit: int = 20):
    """
    Fetch real news related to Cheshire and North West England.
    Filters UK news for Cheshire-related content.
    """
    try:
        articles = await news_feed_service.fetch_local_news()
        articles = articles[:limit]
        
        return {
            "success": True,
            "count": len(articles),
            "articles": articles,
            "source": "Real local news from BBC, Sky News, Guardian (Cheshire/NW focus)"
        }
    except Exception as e:
        logger.error(f"Error fetching local real news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/import-real-news")
async def import_real_news(
    limit: int = 20,
    category: Optional[str] = None,
    authorized: bool = Depends(get_admin_auth),
):
    """
    Import real news articles from RSS feeds into the database.
    These articles will appear alongside AI-generated content.
    """
    try:
        # Fetch real news
        if category:
            articles = await news_feed_service.fetch_category_feeds(category)
        else:
            articles = await news_feed_service.fetch_all_feeds()
        
        articles = articles[:limit]
        
        # Get existing article titles/source URLs to avoid duplicates
        existing_titles = set()
        existing_source_urls = set()
        existing_articles = await db.articles.find({}, {'title': 1, 'source_url': 1}).to_list(1000)
        for a in existing_articles:
            existing_titles.add(a.get('title', '').lower().strip())
            source_url = (a.get('source_url') or '').strip().lower()
            if source_url:
                existing_source_urls.add(source_url)
        
        # Import new articles
        imported = 0
        skipped = 0
        
        for article in articles:
            title = article.get('title', '').strip()
            source_url = (article.get('source_url') or '').strip().lower()
            if not title or title.lower() in existing_titles or (source_url and source_url in existing_source_urls):
                skipped += 1
                continue
            
            # If no image, try to get one based on category
            if not article.get('image'):
                used_photo_ids = await get_used_images_from_db()
                article['image'] = await get_dynamic_image(
                    title=title,
                    category=article.get('category', 'UK News'),
                    content=article.get('content', ''),
                    scope='uk',
                    used_photo_ids=used_photo_ids
                )
            
            # Prepare the complete candidate before the single database insert.
            # Strip RSS trailing URLs from body/summary so the frontend never
            # prints raw source links.
            sanitized_content = sanitize_rss_text(
                article.get('content', ''),
                article.get('source_url', ''),
                is_summary=False,
            )
            sanitized_summary = sanitize_rss_text(
                article.get('summary', ''),
                article.get('source_url', ''),
                is_summary=True,
            )
            if not sanitized_content.strip():
                skipped += 1
                logger.info(f"Skipped empty real-news article: {title[:60]}...")
                continue

            from datetime import datetime

            article_doc = {
                **article,
                "content": sanitized_content,
                "summary": sanitized_summary,
                "publishedDate": (
                    article.get("publishedDate")
                    if isinstance(article.get("publishedDate"), datetime)
                    else datetime.fromisoformat(str(article.get("publishedDate")).replace("Z","+00:00"))
                    if article.get("publishedDate")
                    else datetime.now(timezone.utc)
                ),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "archived": False
            }

            article_doc = apply_ai_manual_review_guard(
                article_doc,
                sanitized_content,
                ai_rewrite_used=False,
                title=title,
            )

            risk_hits = find_ai_manual_review_hits(sanitized_content)
            editorial_quality_reasons = find_ai_editorial_quality_reasons(
                sanitized_content,
                title,
            )
            route_review_reasons = []
            shared_review_reason = str(
                article_doc.get("manual_review_reason") or ""
            ).strip()
            shared_quality_floor_applied = (
                "below the public quality floor" in shared_review_reason.lower()
            )
            if (
                len(sanitized_content) < 1000
                and not shared_quality_floor_applied
            ):
                route_review_reasons.append(
                    "Imported RSS article is below the 1000-character public "
                    "quality threshold and needs manual review."
                )
            if risk_hits:
                route_review_reasons.append(
                    "Imported RSS content contained risky unsupported-detail "
                    "wording that requires source verification."
                )
            route_review_reasons.extend(editorial_quality_reasons)

            if route_review_reasons:
                now_iso = datetime.now(timezone.utc).isoformat()
                article_doc["manual_review_hidden_from_public"] = True
                article_doc["manual_review_reason"] = " ".join(
                    value
                    for value in [
                        shared_review_reason,
                        *route_review_reasons,
                    ]
                    if value
                )
                article_doc["manual_review_created_at"] = now_iso
                article_doc["verification_status"] = "needs_manual_review"
                article_doc["rewrite_status"] = "manual_review_required"
                article_doc["archive_reason"] = "needs_manual_review"

                if risk_hits or editorial_quality_reasons:
                    article_doc["archived"] = True
                    article_doc["archived_at"] = now_iso
                    article_doc["manual_review_hits"] = risk_hits

            article_doc = attach_manual_review_editorial_metadata(article_doc)
            try:
                await db.articles.insert_one(article_doc)
            except DuplicateKeyError:
                skipped += 1
                continue
            existing_titles.add(title.lower())
            if source_url:
                existing_source_urls.add(source_url)
            imported += 1
        
        logger.info(f"Imported {imported} real news articles, skipped {skipped} duplicates")
        
        return {
            "success": True,
            "imported": imported,
            "skipped": skipped,
            "total_fetched": len(articles),
            "source": "BBC, Sky News, Guardian RSS feeds"
        }
    except Exception as e:
        logger.error(f"Error importing real news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class HybridNewsRequest(BaseModel):
    cheshire_articles: int = 5   # 5 Cheshire/local articles
    uk_articles: int = 7         # 7 UK articles
    max_sports: int = 3          # Limit sports articles
    business_articles: int = 5   # 5 Business articles (FREE from RSS)
    tech_articles: int = 5       # 5 Tech/AI articles (FREE from RSS)
    use_perplexity: bool = True  # ENABLED - Hybrid model with AI content generation
    rewrite_delay_seconds: int = 0  # No artificial delay before AI rewrite/import
    public_import_limit: Optional[int] = None  # Optional cap for public articles per import run


async def _import_hybrid_news_internal(
    request: HybridNewsRequest,
) -> dict:
    """
    Import news using HYBRID approach (cost-optimized):
    1. RSS feeds for UK news - ONLY articles WITH RSS images (FREE & perfect match)
    2. RSS feeds for Business, Health, Tech (FREE)
    3. Perplexity for content expansion + Cheshire news
    4. STRICT: Skip articles without proper images (quality over quantity)
    """
    try:
        imported_articles = []
        perplexity_cost_estimate = 0
        used_image_urls = set()  # Track ALL image URLs to prevent duplicates
        public_import_limit = getattr(request, "public_import_limit", None)
        public_import_limit = int(public_import_limit) if public_import_limit is not None else None
        public_imported = 0
        manual_review_imported = 0

        def apply_public_import_cap(article: dict, title: str = "") -> dict:
            nonlocal public_imported
            if public_import_limit is None:
                return article

            already_manual_review = article.get("manual_review_hidden_from_public") is True
            if already_manual_review:
                return article

            if public_imported >= public_import_limit:
                now_iso = datetime.now(timezone.utc).isoformat()
                article["manual_review_hidden_from_public"] = True
                article["manual_review_reason"] = (
                    "Public import cap reached for scheduled run; queued for manual review"
                )
                article["manual_review_created_at"] = now_iso
                article["verification_status"] = "needs_manual_review"
                article["rewrite_status"] = "manual_review_required"
                article["archive_reason"] = "needs_manual_review"
                logger.info(f"Queued extra imported article for manual review after public cap: {title[:80]}")
            return article

        def count_inserted_article_visibility(article: dict) -> None:
            nonlocal public_imported, manual_review_imported
            if article.get("manual_review_hidden_from_public") is True:
                manual_review_imported += 1
            else:
                public_imported += 1

        def is_source_fresh_enough(article: dict, max_age_days: int) -> bool:
            raw_date = article.get("publishedDate") or article.get("published_date")
            if not raw_date:
                return True
            try:
                if isinstance(raw_date, datetime):
                    published_dt = raw_date
                else:
                    published_dt = datetime.fromisoformat(str(raw_date).replace("Z", "+00:00"))
                if published_dt.tzinfo is None:
                    published_dt = published_dt.replace(tzinfo=timezone.utc)
                return published_dt >= datetime.now(timezone.utc) - timedelta(days=max_age_days)
            except Exception:
                return True

        rewrite_delay_seconds = max(0, int(getattr(request, "rewrite_delay_seconds", 0) or 0))
        if request.use_perplexity and rewrite_delay_seconds > 0:
            logger.info(f"Delaying AI rewrite stage for {rewrite_delay_seconds}s to allow source coverage/indexing...")
            await asyncio.sleep(rewrite_delay_seconds)
        
        # Get existing article titles/source URLs to avoid duplicates
        existing_titles = set()
        existing_source_urls = set()
        existing_articles = await db.articles.find({}, {'title': 1, 'image': 1, 'source_url': 1}).to_list(10000)
        archived_existing_articles = await db.archived_articles.find({}, {'title': 1, 'image': 1, 'source_url': 1}).to_list(10000)
        for a in existing_articles + archived_existing_articles:
            existing_titles.add(a.get('title', '').lower().strip())
            source_url = (a.get('source_url') or '').strip().lower()
            if source_url:
                existing_source_urls.add(source_url)
            if a.get('image'):
                used_image_urls.add(a.get('image'))
        
        logger.info(f"Starting hybrid import. {len(existing_titles)} existing titles, {len(used_image_urls)} existing images")
        
        # ==========================================
        # STEP 1: Import UK news via RSS (FREE)
        # ONLY articles that have RSS images (perfect content match)
        # ==========================================
        uk_imported = 0
        sports_imported = 0
        business_imported = 0
        tech_imported = 0
        max_sports = getattr(request, 'max_sports', 3)  # Default 3 sports articles

        # ==========================================
        # CONTENT POLICY: De-emphasise crime + exclude Manchester sources
        # - Keep crime-like stories to a very low cap per import run (default 1)
        # - Hard exclude Manchester sources (per project requirement)
        # ==========================================
        crime_cap = int(os.getenv("CRIME_MAX_PER_IMPORT", "1") or "1")
        crime_count = 0

        def is_manchester_source(article: dict) -> bool:
            s = (article.get("source") or article.get("source_name") or "").lower()
            t = (article.get("title") or "").lower()
            u = (article.get("source_url") or "").lower()
            return ("manchester" in s) or ("manchester" in t) or ("manchestereveningnews" in u) or ("men." in u)

        def is_crime_like(article: dict) -> bool:
            return classify_local_crime(article)

        def is_obituary_like(article: dict) -> bool:
            return classify_local_obituary(article)

        def is_low_utility_article(article: dict) -> bool:
            return classify_low_utility_local(article)

        def is_useful_property_article(article: dict) -> bool:
            title = (article.get("title") or "").lower()
            summary = (article.get("summary") or "").lower()
            content = (article.get("content") or "").lower()
            text = " ".join([title, summary, content])

            if is_low_utility_article(article):
                return False

            useful_property_kw = re.compile(
                r"\b(planning|application|approved|refused|development|homes?|housing|rent|rental|landlord|tenant|leasehold|freehold|mortgage|remortgage|stamp\s+duty|council\s+tax|affordable\s+homes?|brownfield|green\s+belt|house\s+prices?|build\s+to\s+rent|eviction|property\s+tax)\b",
                re.I,
            )
            return bool(useful_property_kw.search(text))

        def local_editorial_text(article: dict) -> str:
            return build_local_editorial_text(article)

        def is_high_value_local_civic_economic_article(article: dict) -> bool:
            return classify_high_value_local(article)

        def local_manual_review_editorial_reason(article: dict) -> str:
            return classify_local_manual_review_reason(article)

        def is_useful_local_article(article: dict) -> bool:
            return classify_useful_local(article)

        def is_useful_category_article(article: dict, target_category: str) -> bool:
            """Positive category gate for UK RSS imports before publish."""
            title = (article.get("title") or "").lower()
            summary = (article.get("summary") or "").lower()
            content = (article.get("content") or "").lower()
            source = (article.get("source") or "").lower()
            text = " ".join([title, summary, content, source])
            category = (target_category or article.get("category") or "").lower()

            # Hard block off-strategy review/shopping/science/lifestyle leakage.
            blocked_kw = re.compile(
                r"\b("
                r"product\s+review|gadget\s+review|display\s+review|tried\s+and\s+tested|best\s+fans?|keep\s+you\s+cool|hot\s+tubs?|air\s+conditioning\s+units?|"
                r"studio\s+display|apple'?s\s+pro\s+display|"
                r"water\s+safety|outdoor\s+swimming|spoil\s+heaps?|lead\s+mining|banks\s+of\s+pansies|pennycress|"
                r"nature\s+itself|climate\s+change|hantavirus|"
                r"tipping\s+culture|forever\s+chemicals|firefighting\s+foam"
                r")\b",
                re.I,
            )
            if blocked_kw.search(text):
                return False

            if category == "finance":
                useful_finance_kw = re.compile(
                    r"\b("
                    r"mortgage|remortgage|interest\s+rates?|savings?|isa|pension|retirement|student\s+loans?|"
                    r"tax|hmrc|vat|stamp\s+duty|council\s+tax|energy\s+bills?|price\s+cap|"
                    r"inflation|cost\s+of\s+living|household\s+bills?|rent|insurance|wages?|pay"
                    r")\b",
                    re.I,
                )
                return bool(useful_finance_kw.search(text))

            if category == "tech":
                useful_tech_kw = re.compile(
                    r"\b("
                    r"ai|artificial\s+intelligence|chatgpt|openai|anthropic|gemini|deepmind|automation|"
                    r"cyber|security|malware|data\s+breach|privacy|software|cloud|servers?|database|"
                    r"aws|microsoft|google|nvidia|semiconductor|chips?|startup|enterprise|developers?|coding|"
                    r"costs?|jobs?|workers?|business|productivity"
                    r")\b",
                    re.I,
                )
                return bool(useful_tech_kw.search(text))

            if category == "business":
                useful_business_kw = re.compile(
                    r"\b("
                    r"uk|britain|cheshire|business|company|companies|jobs?|workers?|training|apprentice|"
                    r"investment|factory|manufacturing|retail|supply\s+chain|exports?|imports?|"
                    r"market|growth|inflation|costs?|prices?|energy|wages?|redundanc|startup|funding|"
                    r"carmakers?|automotive|china"
                    r")\b",
                    re.I,
                )
                return bool(useful_business_kw.search(text))

            return True

        if request.uk_articles > 0:
            logger.info(f"Fetching UK news via RSS feeds (ONLY with images, max {max_sports} sports)...")
            
            rss_articles = await news_feed_service.fetch_all_feeds()
            
            # STRICT: Only articles WITH RSS images
            uk_with_images = [
                a for a in rss_articles 
                if a.get('image') and a.get('title') and not a.get('is_cheshire_related', False)
            ]
            
            # Separate articles by category
            sports_articles = [a for a in uk_with_images if a.get('category') == 'Sports']
            business_articles = [a for a in uk_with_images if a.get('category') == 'Business']
            tech_articles = [a for a in uk_with_images if a.get('category') in ['Tech', 'AI', 'Science']]
            finance_articles = [a for a in uk_with_images if a.get('category') in ['Finance', 'Tax']]
            property_enrichment_articles = [a for a in uk_with_images if a.get('category') == 'Property' and is_useful_property_article(a)]
            uk_news_articles = [
                a for a in uk_with_images
                if a.get('category') == 'UK News'
            ]
            
            logger.info(f"Found: {len(uk_news_articles)} UK, {len(finance_articles)} Finance/Tax, {len(property_enrichment_articles)} Property->Finance, {len(business_articles)} Business, {len(tech_articles)} Tech/AI, {len(sports_articles)} Sports")
            
            # Helper function to import articles from a category with Perplexity content generation
            async def import_category_articles(articles_list, category_name, max_count, counter_name):
                nonlocal perplexity_cost_estimate
                imported_count = 0
                for article in articles_list:
                    if imported_count >= max_count:
                        break
                        
                    title = article.get('title', '').strip()
                    rss_image = article.get('image', '').strip()

                    # Strict quality gate: skip RSS items without a real image
                    if not rss_image:
                        logger.info(f"Skipping no-image RSS article: {title[:40]}...")
                        continue
                    if is_weak_generic_image(rss_image):
                        logger.info(f"Skipping weak generic RSS image: {title[:40]}...")
                        continue

                    # Exclude Manchester sources entirely
                    if is_manchester_source(article):
                        continue

                    # Hard block obituary / memorial notice-style content
                    if is_obituary_like(article):
                        continue

                    # Hard block obvious low-utility lifestyle / promo / entertainment filler
                    if is_low_utility_article(article):
                        continue

                    # Keep original Property articles tightly aligned to housing/planning/public-impact utility,
                    # even when they are being folded into Finance.
                    if article.get('category') == "Property" and not is_useful_property_article(article):
                        continue

                    # Positive category gate for UK RSS buckets.
                    # Prevents weak category leakage such as product reviews in Finance,
                    # science/nature filler in Tech, and broad overseas soft-business stories.
                    if not is_useful_category_article(article, category_name):
                        logger.info(f"Skipping weak {category_name} RSS article by category gate: {title[:60]}...")
                        continue

                    # Hard block crime / police / court / mugshot-style content from going live.
                    # This keeps the site aligned with the local economic intelligence strategy.
                    if is_crime_like(article):
                        logger.info(f"Skipping crime-like RSS article: {title[:40]}...")
                        continue
                    
                    # Skip if duplicate title, source URL, or image
                    source_url = (article.get('source_url') or '').strip().lower()
                    if not title or title.lower() in existing_titles:
                        continue
                    if source_url and source_url in existing_source_urls:
                        logger.info(f"Skipping duplicate RSS source URL: {title[:40]}...")
                        continue
                    if rss_image in used_image_urls:
                        logger.info(f"Skipping duplicate RSS image: {title[:40]}...")
                        continue
                    
                    # Freshness gate: do not spend AI budget or publish stale national/business/tech items.
                    if not is_source_fresh_enough(article, 3):
                        logger.info(f"Skipping stale RSS article before Perplexity/public import: {title[:60]}...")
                        continue

                    # Get content - either generate via Perplexity or use RSS content
                    original_content = article.get('content', '')
                    ai_rewrite_used = False
                    manual_review_without_ai = (public_import_limit is not None and public_imported >= public_import_limit) or not ai_budget_available(0.05)
                    
                    if manual_review_without_ai:
                        logger.info(f"Public import cap reached before AI rewrite; queueing RSS candidate for manual review: {title[:60]}...")
                        detailed_content = original_content
                    elif request.use_perplexity:
                        # Generate detailed content using Perplexity, but never let one rewrite stall the whole import.
                        logger.info(f"Generating content for {category_name} article: {title[:40]}...")
                        try:
                            detailed_content = await asyncio.wait_for(
                                perplexity_service.generate_article_content(
                                    title=title,
                                    summary=original_content,
                                    source=article.get('source', 'BBC News'),
                                    source_url=article.get('source_url', '')
                                ),
                                timeout=45
                            )
                            ai_rewrite_used = bool((detailed_content or "").strip() and detailed_content != original_content)
                            perplexity_cost_estimate += 0.005
                        except Exception as px_err:
                            logger.warning(f"Perplexity rewrite failed/timed out for {category_name}: {title[:60]}... | {px_err}")
                            detailed_content = original_content
                    else:
                        # Use RSS content directly (faster, no AI)
                        detailed_content = original_content
                    
                    # Strict public quality gate.
                    # Any non-empty rewrite below 1000 characters is retained for
                    # editable Manual Review rather than silently discarded.
                    short_nonlocal_review_reason = ""
                    if not manual_review_without_ai and len((detailed_content or "").strip()) < 1000:
                        if (detailed_content or "").strip():
                            short_nonlocal_review_reason = (
                                "UK RSS article needs manual review: "
                                "AI content remained below the 1000-character public threshold."
                            )
                        else:
                            logger.info(f"Skipping empty-content article after rewrite attempt: {title[:60]}...")
                            continue

                    # Use RSS image (guaranteed perfect match)
                    article['image'] = rss_image
                    article['image_source'] = 'rss_feed'
                    article['content'] = detailed_content
                    article['summary'] = original_content[:200] + '...' if len(original_content) > 200 else original_content
                    article['scope'] = 'uk'
                    article['author'] = article.get('source', 'BBC News')
                    article['id'] = str(uuid4())
                    
                    # Strip RSS trailing URLs from body/summary so the frontend never prints raw source links
                    
                    article['content'] = sanitize_rss_text(article.get('content',''), article.get('source_url',''), is_summary=False)
                    article = apply_ai_manual_review_guard(
                        article,
                        article.get('content', ''),
                        ai_rewrite_used,
                        title
                    )

                    if short_nonlocal_review_reason:
                        now_iso = datetime.now(timezone.utc).isoformat()

                        # Preserve any stronger archive decision already made by
                        # the editorial/invention-risk guard.
                        if article.get("archived") is not True:
                            article["archived"] = False
                            article["manual_review_hidden_from_public"] = True
                            existing_reason = str(article.get("manual_review_reason") or "").strip()
                            article["manual_review_reason"] = " ".join(
                                value for value in [
                                    existing_reason,
                                    short_nonlocal_review_reason
                                ]
                                if value
                            )
                            article["manual_review_created_at"] = now_iso
                            article["verification_status"] = "needs_manual_review"
                            article["rewrite_status"] = "manual_review_required"
                            article["archive_reason"] = "needs_manual_review"

                    article = apply_public_import_cap(article, title)
                    article['summary'] = sanitize_rss_text(article.get('summary',''), article.get('source_url',''), is_summary=True)
                    article = attach_manual_review_editorial_metadata(article)
                    try:
                        await db.articles.insert_one(article)
                    except DuplicateKeyError:
                        logger.info(f"⏭️ Duplicate skipped (DB unique index): {title[:60]}...")
                        continue
                    existing_titles.add(title.lower())
                    if source_url:
                        existing_source_urls.add(source_url)
                    used_image_urls.add(rss_image)
                    imported_articles.append(article)
                    count_inserted_article_visibility(article)
                    imported_count += 1
                    logger.info(f"✅ Imported {category_name} article: {title[:50]}...")
            
                return imported_count
            
            finance_target = min(5, request.uk_articles)
            property_enrichment_target = min(1, max(0, request.uk_articles - finance_target))
            uk_target = max(0, request.uk_articles - finance_target - property_enrichment_target)

            finance_imported = await import_category_articles(finance_articles, "Finance", finance_target, "finance_imported")
            property_enrichment_imported = await import_category_articles(property_enrichment_articles, "Finance", property_enrichment_target, "finance_imported")
            uk_imported = await import_category_articles(uk_news_articles, "UK News", uk_target, "uk_imported")

            if finance_imported < finance_target:
                uk_imported += await import_category_articles(
                    uk_news_articles,
                    "UK News",
                    finance_target - finance_imported,
                    "uk_imported"
                )

            if property_enrichment_imported < property_enrichment_target:
                uk_imported += await import_category_articles(
                    uk_news_articles,
                    "UK News",
                    property_enrichment_target - property_enrichment_imported,
                    "uk_imported"
                )
            
        
        # ==========================================
        # STEP 2: Check LOCAL Cheshire newspaper feeds (FREE + Full Content via Perplexity)
        # Now includes: Cheshire Live and other Cheshire/UK sources (Manchester excluded by policy)
        # ==========================================
        cheshire_from_rss = 0
        
        logger.info("Fetching from LOCAL Cheshire newspaper feeds...")
        
        # First try dedicated local feeds (Cheshire Live, Warrington Guardian, etc.)
        local_articles = await news_feed_service.fetch_local_feeds_only()
        logger.info(f"Found {len(local_articles)} articles from local Cheshire newspapers")
        
        # If not enough from local feeds, also check national feeds for Cheshire mentions
        if len(local_articles) < request.cheshire_articles:
            additional = await news_feed_service.fetch_local_news()
            # Add only articles not already in local_articles
            existing_local_titles = {a.get('title', '').lower() for a in local_articles}
            for article in additional:
                if article.get('title', '').lower() not in existing_local_titles:
                    local_articles.append(article)
        
        # Only Cheshire articles WITH images
        cheshire_with_images = [
            a for a in local_articles 
            if a.get('image') and a.get('title')
        ]
        
        logger.info(f"Found {len(cheshire_with_images)} local articles with images")
        
        # Per-run local diversity caps so Local News does not become dominated
        # by one topic type such as planning/housing applications.
        local_topic_counts = {}

        def is_hard_reject_local_review_candidate(article: dict) -> bool:
            """Keep unsafe, promotional and unusable records out of Manual Review."""
            from urllib.parse import urlparse

            source_url_value = str(article.get("source_url") or "").strip()
            try:
                parsed_source = urlparse(source_url_value)
                valid_source = (
                    parsed_source.scheme in {"http", "https"}
                    and bool(parsed_source.netloc)
                )
            except Exception:
                valid_source = False

            text = " ".join(
                str(article.get(field) or "")
                for field in ("title", "summary", "content", "category")
            )
            promotional_or_spam = re.search(
                r"\b(sponsored|advertorial|affiliate|casino|gambling|betting|"
                r"shopping deal|gift guide|black friday|cyber monday|"
                r"must-have buys?|product review|celebrity|showbiz|love island)\b",
                text,
                re.IGNORECASE,
            )
            return bool(
                not valid_source
                or not str(article.get("image") or "").strip()
                or is_weak_generic_image(str(article.get("image") or ""))
                or is_manchester_source(article)
                or is_obituary_like(article)
                or is_crime_like(article)
                or promotional_or_spam
                or find_ai_manual_review_hits(
                    str(article.get("content") or "")
                )
            )

        async def queue_local_rss_manual_review(article: dict, title: str, reason: str, detailed_content: str = "") -> bool:
            """Queue suitable non-public local RSS candidates for human review."""
            safety_candidate = dict(article)
            if detailed_content:
                safety_candidate["content"] = detailed_content
            if is_hard_reject_local_review_candidate(safety_candidate):
                return False

            source_url_local = (article.get("source_url") or "").strip().lower()
            if not title or title.lower() in existing_titles or (source_url_local and source_url_local in existing_source_urls):
                return False

            review_doc = dict(article)
            review_doc["id"] = str(uuid4())
            review_doc["image"] = review_doc.get("image") or article.get("image") or ""
            review_doc["image_source"] = "rss_feed"
            available_source_text = (
                detailed_content
                or review_doc.get("content", "")
                or review_doc.get("summary", "")
            )
            review_doc["content"] = sanitize_rss_text(available_source_text, review_doc.get("source_url", ""), is_summary=False)
            review_doc["summary"] = sanitize_rss_text(review_doc.get("summary", ""), review_doc.get("source_url", ""), is_summary=True)
            review_doc["scope"] = "cheshire"
            review_doc["category"] = "Local News"
            review_doc["is_local_source"] = True
            review_doc["is_local_newspaper"] = review_doc.get("is_local_feed", False)
            review_doc["manual_review_hidden_from_public"] = True
            review_doc["manual_review_reason"] = reason
            review_doc["manual_review_created_at"] = datetime.now(timezone.utc).isoformat()
            review_doc["verification_status"] = "needs_manual_review"
            review_doc["rewrite_status"] = "manual_review_required"
            review_doc["archive_reason"] = "needs_manual_review"
            review_doc = attach_manual_review_editorial_metadata(review_doc)

            try:
                await db.articles.insert_one(review_doc)
            except DuplicateKeyError:
                logger.info(f"⏭️ Duplicate skipped (local RSS manual review): {title[:60]}...")
                return False

            existing_titles.add(title.lower())
            if source_url_local:
                existing_source_urls.add(source_url_local)
            imported_articles.append(review_doc)
            count_inserted_article_visibility(review_doc)
            logger.info(f"📝 Queued local RSS article for manual review: {title[:60]}... | {reason}")
            return True
        
        for article in cheshire_with_images:
            if cheshire_from_rss >= request.cheshire_articles:
                break
                
            title = article.get('title', '').strip()
            rss_image = article.get('image', '').strip()
            source_url = (article.get('source_url') or '').strip().lower()
            
            if not title or title.lower() in existing_titles:
                continue
            if source_url and source_url in existing_source_urls:
                continue
            if not rss_image:
                continue
            if is_weak_generic_image(rss_image):
                logger.info(f"Skipping weak generic RSS image: {title[:40]}...")
                continue

            def fetch_source_page(page_url: str) -> str:
                import urllib.request

                request_obj = urllib.request.Request(
                    page_url,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                return (
                    urllib.request.urlopen(request_obj, timeout=8)
                    .read()
                    .decode("utf-8", errors="ignore")
                )

            resolved_rss_image = await asyncio.to_thread(
                resolve_imported_article_image,
                rss_image,
                article.get("source_url", ""),
                fetch_page=fetch_source_page,
            )
            if resolved_rss_image != rss_image:
                logger.info(
                    "Upgraded Newsquest RSS image from source Open Graph metadata: "
                    f"{title[:60]}..."
                )
                rss_image = resolved_rss_image
                article["image"] = resolved_rss_image

            
            # Exclude Manchester sources entirely
            if is_manchester_source(article):
                continue

            # Hard block obituary / memorial notice-style content
            if is_obituary_like(article):
                continue

            # A feed-configured Cheshire-wide signal is useful for editorial
            # review but must never substitute a false town location or enter
            # the strict automatic-publication path.
            if article.get("county_wide_manual_review_candidate") is True:
                if is_hard_reject_local_review_candidate(article):
                    logger.info(
                        "Skipping unsafe county-wide Local RSS candidate: "
                        f"{title[:60]}..."
                    )
                    continue
                if not is_useful_local_article(article):
                    logger.info(
                        "Skipping low-value county-wide Local RSS candidate: "
                        f"{title[:60]}..."
                    )
                    continue
                if await queue_local_rss_manual_review(
                    article,
                    title,
                    "Local RSS article needs manual review: County-wide "
                    "Cheshire story without a qualifying town match",
                ):
                    continue
                logger.info(
                    "Skipping unsafe county-wide Local RSS candidate: "
                    f"{title[:60]}..."
                )
                continue

            if classify_reject_before_local_review(article):
                logger.info(
                    "Skipping low-value Local RSS item before Manual Review: "
                    f"{title[:60]}..."
                )
                continue

            # Keep promotional/spam material rejected, but let suitable soft
            # lifestyle or borderline editorial candidates reach Manual Review.
            if is_low_utility_article(article) and not is_high_value_local_civic_economic_article(article):
                if await queue_local_rss_manual_review(
                    article,
                    title,
                    local_manual_review_editorial_reason(article),
                ):
                    continue
                continue

            # Hard block crime / police / court / mugshot-style content from going live.
            # This keeps the site aligned with the local economic intelligence strategy.
            if is_crime_like(article):
                logger.info(f"Skipping crime-like local RSS article: {title[:40]}...")
                continue

            # Positive usefulness gate before spending Perplexity budget.
            # This keeps budget focused on planning, housing, council, business, schools,
            # health, energy, infrastructure and other public/economic impact stories.
            if not is_useful_local_article(article):
                if await queue_local_rss_manual_review(
                    article,
                    title,
                    local_manual_review_editorial_reason(article),
                ):
                    continue
                logger.info(f"Skipping low-impact local RSS article before Perplexity: {title[:60]}...")
                continue

            local_text = " ".join([
                str(article.get("title") or ""),
                str(article.get("summary") or ""),
                str(article.get("content") or ""),
            ]).lower()

            local_topic = "other"
            if re.search(r"\b(planning|application|approved|refused|development|housing|green\s+belt|brownfield|(?:new|affordable)\s+homes?|\d+\s+homes?)\b", local_text, re.I):
                local_topic = "planning_housing"
            elif re.search(r"\b(school|academy|college|ofsted|education|pupils?|students?)\b", local_text, re.I):
                local_topic = "education"
            elif re.search(r"\b(nhs|hospital|gp|health|care\s+home|social\s+care)\b", local_text, re.I):
                local_topic = "health_care"
            elif re.search(r"\b(business|jobs?|employer|investment|funding|grant|factory|warehouse|retail|startup|expansion|relocat(?:e|es|ed|ion))\b", local_text, re.I):
                local_topic = "local_business_economy"
            elif re.search(r"\b(council|councillors?|committee|consultation|public\s+meeting|local\s+plan|regeneration|town\s+centre|high\s+street)\b", local_text, re.I):
                local_topic = "council_public_services"

            local_topic_caps = {
                "planning_housing": 1,
                "education": 1,
                "health_care": 1,
            }

            local_topic_cap = local_topic_caps.get(local_topic)
            if local_topic_cap is not None and local_topic_counts.get(local_topic, 0) >= local_topic_cap:
                if await queue_local_rss_manual_review(article, title, f"Local RSS article needs manual review: per-run topic cap reached ({local_topic})"):
                    continue
                logger.info(f"Skipping local RSS article due to per-run topic cap ({local_topic}): {title[:60]}...")
                continue

            if rss_image in used_image_urls:
                continue
            
            # Freshness gate: allow slower-moving local planning/council stories, but block stale local filler.
            if not is_source_fresh_enough(article, 7):
                if await queue_local_rss_manual_review(article, title, "Local RSS article needs manual review: older than automatic local RSS freshness gate"):
                    continue
                logger.info(f"Skipping stale local RSS article before Perplexity/public import: {title[:60]}...")
                continue

            # Get content - either generate via Perplexity or use RSS content
            original_content = article.get('content', '')
            ai_rewrite_used = False
            manual_review_without_ai = (public_import_limit is not None and public_imported >= public_import_limit) or not ai_budget_available(0.05)
            
            if manual_review_without_ai:
                logger.info(f"Public import cap reached before AI rewrite; queueing local RSS candidate for manual review: {title[:60]}...")
                detailed_content = original_content
            elif request.use_perplexity:
                # Generate detailed content using Perplexity, but never let one rewrite stall the whole import.
                logger.info(f"Generating full content for local article: {title[:40]}...")
                try:
                    detailed_content = await asyncio.wait_for(
                        perplexity_service.generate_article_content(
                            title=title,
                            summary=original_content,
                            source=article.get('source', 'Cheshire Live'),
                            source_url=article.get('source_url', '')
                        ),
                        timeout=45
                    )
                    ai_rewrite_used = bool((detailed_content or "").strip() and detailed_content != original_content)
                    perplexity_cost_estimate += 0.005
                except Exception as px_err:
                    logger.warning(f"Perplexity rewrite failed/timed out for local article: {title[:60]}... | {px_err}")
                    detailed_content = original_content
            else:
                # Use RSS content directly (faster, no AI)
                detailed_content = original_content

            # Strict quality gate: publish only full-length rewritten content.
            if not manual_review_without_ai and len((detailed_content or "").strip()) < 1000:
                if await queue_local_rss_manual_review(article, title, "Local RSS article needs manual review: AI/RSS content remained below public length threshold", detailed_content):
                    continue
                logger.info(f"Skipping short-content local article after rewrite attempt: {title[:60]}...")
                continue
            
            article['image'] = rss_image
            article['image_source'] = 'rss_feed'
            article['content'] = detailed_content
            article['summary'] = original_content[:200] + '...' if len(original_content) > 200 else original_content
            article['scope'] = 'cheshire'
            article['category'] = 'Local News'
            article['id'] = str(uuid4())
            article['is_local_source'] = True  # Mark as local source
            article['is_local_newspaper'] = article.get('is_local_feed', False)
            
            # Strip RSS trailing URLs from body/summary so the frontend never prints raw source links
            
            article['content'] = sanitize_rss_text(article.get('content',''), article.get('source_url',''), is_summary=False)
            article = apply_ai_manual_review_guard(
                article,
                article.get('content', ''),
                ai_rewrite_used,
                title
            )
            article = apply_public_import_cap(article, title)
            article['summary'] = sanitize_rss_text(article.get('summary',''), article.get('source_url',''), is_summary=True)
            article = attach_manual_review_editorial_metadata(article)
            try:
                await db.articles.insert_one(article)
            except DuplicateKeyError:
                logger.info(f"⏭️ Duplicate skipped (local RSS insert): {title[:60]}...")
                continue
            existing_titles.add(title.lower())
            if source_url:
                existing_source_urls.add(source_url)
            used_image_urls.add(rss_image)
            local_topic_counts[local_topic] = local_topic_counts.get(local_topic, 0) + 1
            imported_articles.append(article)
            count_inserted_article_visibility(article)
            cheshire_from_rss += 1
            logger.info(f"✅ Imported local Cheshire article: {title[:50]}...")
        
        # ==========================================
        # STEP 2B: Import Business and Tech articles after Local RSS
        # This preserves Perplexity budget priority for useful Cheshire local stories.
        # ==========================================
        if request.uk_articles > 0:
            # Import Business articles (FREE from RSS)
            business_imported = await import_category_articles(business_articles, "Business", request.business_articles, "business_imported")
            
            # Import Tech articles (FREE from RSS)
            tech_imported = await import_category_articles(tech_articles, "Tech", request.tech_articles, "tech_imported")
            
            # Sports import removed per editorial policy
            sports_imported = 0
        
        # ==========================================
        # STEP 3: Import Cheshire news via Perplexity (ONLY if local feeds don't have enough)
        # This is now a FALLBACK, not the primary source
        # ==========================================
        cheshire_from_perplexity = 0
        remaining_cheshire = request.cheshire_articles - cheshire_from_rss
        
        if request.use_perplexity and remaining_cheshire > 0 and cheshire_from_rss < 3:
            logger.info(f"Fetching {remaining_cheshire} more Cheshire articles via Perplexity...")
            
            try:
                cheshire_articles = await asyncio.wait_for(
                    perplexity_service.search_cheshire_news(
                        category="Local News",
                        limit=remaining_cheshire + 2  # Get extra in case some fail
                    ),
                    timeout=45
                )
                perplexity_cost_estimate += 0.005
            except Exception as e:
                logger.warning(f"Perplexity search failed or timed out: {e}")
                cheshire_articles = []
            
            for article in cheshire_articles:
                if cheshire_from_perplexity >= remaining_cheshire:
                    break
                    
                title = article.get('title', '').strip()
                content = article.get('content', '')
                category = article.get('category', 'Local News')
                source_url = (article.get('source_url') or '').strip().lower()
                
                if not title or title.lower() in existing_titles:
                    continue
                if source_url and source_url in existing_source_urls:
                    continue
                
                # 1️⃣ Try to use image provided by Perplexity result first
                image = article.get('image')

                if image and image not in used_image_urls:
                    article['image'] = image
                    article['image_source'] = 'perplexity'
                else:
                    # 2️⃣ Fallback to smart image search
                    logger.info(f"Generating smart image query for: {title[:40]}...")
                    smart_query = await perplexity_service.generate_image_search_query(
                        title=title,
                        content=content,
                        category=category
                    )
                    perplexity_cost_estimate += 0.005

                    if not smart_query:
                        smart_query = ' '.join(title.split()[:4])

                    image = None

                    try:
                        image = None
                        if image in used_image_urls:
                            image = None
                    except:
                        image = None

                    if not image:
                        try:
                            image = None  # Pexels disabled (RSS-only images)
                            if image in used_image_urls:
                                image = None
                        except:
                            image = None

                    if not image:
                        # Try RSS fallback image instead of skipping
                        fallback_image = None
                        for a in cheshire_with_images:
                            u = (a.get('image') or '').strip()
                            if u and u not in used_image_urls:
                                fallback_image = u
                                break

                        if fallback_image:
                            image = fallback_image
                            article['image_source'] = 'rss_fallback'
                        else:
                            logger.warning(f"Skipping article - no usable image found: {title[:40]}...")
                            continue

                    article['image'] = image
                    article['image_source'] = 'smart_search'

                article['scope'] = 'cheshire'
                article['id'] = str(uuid4())
                article['author'] = 'Cheshire Today'
                article['publishedDate'] = datetime.now(timezone.utc).isoformat()

                # Strip RSS trailing URLs from body/summary so the frontend never prints raw source links

                article['content'] = sanitize_rss_text(article.get('content',''), article.get('source_url',''), is_summary=False)

                article['summary'] = sanitize_rss_text(article.get('summary',''), article.get('source_url',''), is_summary=True)
                article = apply_ai_manual_review_guard(
                    article,
                    article.get('content', ''),
                    ai_rewrite_used=True,
                    title=title,
                )

                if len((article.get('content') or '').strip()) < 1000:
                    now_iso = datetime.now(timezone.utc).isoformat()
                    short_fallback_reason = (
                        "Perplexity Cheshire fallback article needs manual review: "
                        "content remained below the 1000-character public threshold."
                    )
                    article["manual_review_hidden_from_public"] = True
                    existing_reason = str(article.get("manual_review_reason") or "").strip()
                    article["manual_review_reason"] = " ".join(
                        value for value in [existing_reason, short_fallback_reason] if value
                    )
                    article["manual_review_created_at"] = now_iso
                    article["verification_status"] = "needs_manual_review"
                    if article.get("rewrite_status") == "ai_rewritten":
                        article["rewrite_status"] = "manual_review_required"
                    article["archive_reason"] = "needs_manual_review"
                    if article.get("archived") is not True:
                        article["archived"] = False

                article = apply_public_import_cap(article, title)
                article = attach_manual_review_editorial_metadata(article)
                try:
                    await db.articles.insert_one(article)
                except DuplicateKeyError:
                    logger.info(f"⏭️ Duplicate skipped (Perplexity Cheshire insert): {title[:60]}...")
                    continue
                existing_titles.add(title.lower())
                if source_url:
                    existing_source_urls.add(source_url)
                used_image_urls.add(article['image'])
                imported_articles.append(article)
                count_inserted_article_visibility(article)
                cheshire_from_perplexity += 1
                logger.info(f"✅ Imported Cheshire article (hybrid image logic): {title[:50]}...")
        
        total_cheshire = cheshire_from_rss + cheshire_from_perplexity
        rss_images_used = len([a for a in imported_articles if a.get('image_source') == 'rss_feed'])
        smart_images_used = len([a for a in imported_articles if a.get('image_source') == 'smart_search'])
        
        logger.info(f"Hybrid import complete: {total_cheshire} Cheshire + {uk_imported} UK + {business_imported} Business + {tech_imported} Tech + {sports_imported} Sports")
        logger.info(f"Image sources: {rss_images_used} RSS, {smart_images_used} smart search")
        
        await cap_visible_articles(keep=100)

        # === RATIO_REBALANCE_45 ===
        if os.getenv("ENABLE_RATIO_REBALANCE", "0").strip().lower() in ("1", "true", "yes", "on"):
            MAX_VISIBLE = 45
            active_filter = {"$or": [{"archived": {"$exists": False}}, {"archived": False}]}
            active = await db.articles.find(
                active_filter,
                {
                    "_id": 1,
                    "publishedDate": 1,
                    "scope": 1,
                    "category": 1,
                    "source": 1,
                    "manual_edited": 1,
                    "manual_edit_protected": 1,
                    "manual_review_hidden_from_public": 1,
                    "verification_status": 1,
                    "rewrite_status": 1,
                    "editorial_status": 1,
                    "moderation_status": 1,
                }
            ).sort("publishedDate", -1).to_list(10000)

            local, business, ai, uk_other = [], [], [], []

            for a in active:
                cat = (a.get("category") or "")
                scope = (a.get("scope") or "")

                # Treat Local News as local even if scope is wrong
                if scope == "cheshire" or cat == "Local News":
                    local.append(a)
                elif cat in ["Business", "Finance", "Tax", "Property"]:
                    business.append(a)
                elif cat in ["Tech", "AI & Tech", "AI", "Technology"]:
                    ai.append(a)
                else:
                    uk_other.append(a)

            # Quotas sum exactly to 45
            Q_LOCAL = 18
            Q_BUSINESS = 12
            Q_AI = 6
            Q_UK = 9

            owner_protected = [
                article
                for article in active
                if _is_owner_protected_article(article)
            ]
            keep = []
            keep += local[:Q_LOCAL]
            keep += business[:Q_BUSINESS]
            keep += ai[:Q_AI]
            keep += uk_other[:Q_UK]

            # Fill any shortfall with newest remaining (dedupe by _id)
            keep_ids = set([x.get("_id") for x in keep if x.get("_id")])
            if len(keep) < MAX_VISIBLE:
                for a in active:
                    _id = a.get("_id")
                    if not _id or _id in keep_ids:
                        continue
                    keep.append(a)
                    keep_ids.add(_id)
                    if len(keep) >= MAX_VISIBLE:
                        break

            keep = keep[:MAX_VISIBLE]
            owner_protected_ids = {
                article.get("_id")
                for article in owner_protected
                if article.get("_id")
            }
            keep_ids = list(
                owner_protected_ids.union(
                    a["_id"] for a in keep if a.get("_id")
                )
            )

            archive_query = dict(active_filter)
            archive_query["_id"] = {"$nin": keep_ids}

            result = await db.articles.update_many(
                archive_query,
                {"$set": {
                    "archived": True,
                    "archived_at": datetime.now(timezone.utc).isoformat(),
                    "archive_reason": "ratio_rebalance"
                }}
            )

            logger.info(
                f"[RATIO_REBALANCE] keep={{local:{min(len(local),Q_LOCAL)}, business:{min(len(business),Q_BUSINESS)}, ai:{min(len(ai),Q_AI)}, uk_other:{min(len(uk_other),Q_UK)}}} archived={result.modified_count}"
            )


        else:
            logger.info("[RATIO_REBALANCE] disabled by ENABLE_RATIO_REBALANCE")


        return {
            "success": True,
            "total_imported": len(imported_articles),
            "public_imported": public_imported,
            "manual_review_imported": manual_review_imported,
            "cheshire_articles": total_cheshire,
            "cheshire_from_perplexity": cheshire_from_perplexity,
            "cheshire_from_rss": cheshire_from_rss,
            "uk_articles": uk_imported,
            "business_articles": business_imported,
"tech_articles": tech_imported,
# "sports_articles": sports_imported,
            "rss_images_used": rss_images_used,
            "smart_images_used": smart_images_used,
            "estimated_cost_usd": round(perplexity_cost_estimate, 4),
            "sources": {
                "perplexity": cheshire_from_perplexity > 0,
                "rss": uk_imported > 0 or cheshire_from_rss > 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error in hybrid news import: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/import-hybrid-news")
async def import_hybrid_news(
    request: HybridNewsRequest = HybridNewsRequest(),
    authorized: bool = Depends(get_admin_auth),
):
    return await _import_hybrid_news_internal(request)


@api_router.post("/admin/clear-and-refresh")
async def clear_and_refresh_news(authorized: bool = Depends(get_admin_auth)):
    """
    Archive all articles and import fresh news using hybrid approach.
    This is the main way to populate the site with real news.
    Articles are moved to archive, not permanently deleted.
    Requires admin authentication.
    """
    try:
        # Archive existing articles instead of deleting
        articles_to_archive = await db.articles.find({}).to_list(None)
        archived_count = 0
        
        for article in articles_to_archive:
            # Add archived timestamp and move to archived_articles collection
            article['archived_at'] = datetime.now(timezone.utc).isoformat()
            article['archive_reason'] = 'clear_and_refresh'
            
            # Remove _id to avoid duplicate key error when inserting
            article_id = article.pop('_id', None)
            
            # Insert into archived_articles collection
            try:
                await db.archived_articles.insert_one(article)
                archived_count += 1
            except Exception as e:
                logger.warning(f"Failed to archive article {article.get('id')}: {e}")
        
        # Now clear the articles collection
        result = await db.articles.delete_many({})
        logger.info(f"Archived {archived_count} articles, cleared {result.deleted_count} from main collection")
        
        # Import fresh news using hybrid approach
        # Cheshire Today policy: ALL imported articles must be AI-enriched before going live
        local_target = int(os.getenv("LOCAL_IMPORT_LIMIT", "5") or "5")
        uk_target = int(os.getenv("UK_IMPORT_LIMIT", "7") or "7")

        request = HybridNewsRequest(
            cheshire_articles=local_target,   # Cheshire/local (env: LOCAL_IMPORT_LIMIT)
            uk_articles=uk_target,            # UK (env: UK_IMPORT_LIMIT; default keeps ~20 total)
            max_sports=3,                     # Limit sports to 3
            business_articles=5,              # 5 Business articles (FREE)
            tech_articles=5,                  # 5 Tech/AI articles (FREE)
            use_perplexity=True,              # Force AI rewrite for all refreshed imports
            rewrite_delay_seconds=0            # Manual/admin refresh should not wait 15 minutes
        )
        
        import_result = await _import_hybrid_news_internal(request)
        
        # AUTO-CLEANUP: Remove any duplicates or short articles after import
        cleanup_result = await _remove_duplicates_internal()
        logger.info(f"Auto-cleanup: removed {cleanup_result['total_removed']} duplicates/short articles")
        
        # Clear the API cache after refreshing articles
        api_cache.clear()
        logger.info("API cache cleared after refresh")
        
        return {
            "success": True,
            "archived": archived_count,
            "articles_imported": import_result.get("total_imported", 0),
            "cheshire_articles": import_result.get("cheshire_articles", 0),
            "uk_articles": import_result.get("uk_articles", 0),
            "estimated_cost_usd": import_result.get("estimated_cost_usd", 0),
            "auto_cleanup": cleanup_result
        }
        
    except Exception as e:
        logger.error(f"Error in clear and refresh: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@api_router.post("/admin/perplexity-rewrite-test")
async def admin_perplexity_rewrite_test(
    title: str = Body(...),
    summary: str = Body(""),
    source: str = Body("BBC News"),
    source_url: str = Body(""),
    auth: bool = Depends(get_admin_auth)
):
    """
    No-write Perplexity rewrite diagnostic.
    Runs the current Perplexity rewrite prompt and returns length/preview only.
    Does not insert, update, publish, archive, or modify any article.
    """
    try:
        safe_title = str(title or "").strip()
        if not safe_title:
            raise HTTPException(status_code=400, detail="title is required")

        detailed_content = await asyncio.wait_for(
            perplexity_service.generate_article_content(
                title=safe_title,
                summary=str(summary or ""),
                source=str(source or "BBC News"),
                source_url=str(source_url or "")
            ),
            timeout=120
        )

        content = str(detailed_content or "")

        return {
            "success": True,
            "title": safe_title,
            "source": source,
            "source_url": source_url,
            "content_len": len(content),
            "passes_quality_floor": len(content.strip()) >= 1000,
            "preview": content[:1200]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running Perplexity rewrite test: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/admin/regenerate-recent-content")
async def regenerate_recent_article_content(authorized: bool = Depends(get_admin_auth)):
    """
    Regenerate recent articles using Perplexity, regardless of current content length.
    Focuses only on the last 48 hours and caps the batch size for cost control.
    """
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()

        articles = await db.articles.find(
            {"publishedDate": {"$gte": cutoff}}
        ).sort("publishedDate", -1).limit(25).to_list(25)

        regenerated = 0
        safe_regenerated = 0
        manual_review_routed = 0
        skipped_empty = 0
        skipped_too_short = 0
        processing_failures = 0
        cost_estimate = 0.0

        for article in articles:
            title = article.get('title', '')
            original_content = article.get('content', '') or article.get('summary', '') or ''
            source = article.get('source', 'BBC News')
            source_url = article.get('source_url', '')

            logger.info(f"Regenerating recent content for: {title[:60]}...")

            try:
                detailed_content = await perplexity_service.generate_article_content(
                    title=title,
                    summary=original_content,
                    source=source,
                    source_url=source_url
                )
                cost_estimate += 0.005

                if not (detailed_content or "").strip():
                    skipped_empty += 1
                    logger.warning(f"Skipped recent article - empty rewrite: {title[:60]}...")
                    continue

                sanitized_content = sanitize_rss_text(
                    detailed_content,
                    source_url,
                    is_summary=False,
                )
                if len(sanitized_content) < max(len(original_content), 1200):
                    skipped_too_short += 1
                    logger.warning(f"Skipped recent article - no safe length improvement: {title[:60]}...")
                    continue

                proposed_article = {
                    **article,
                    "content": sanitized_content,
                }
                guarded_article = apply_ai_manual_review_guard(
                    proposed_article,
                    sanitized_content,
                    ai_rewrite_used=True,
                    title=title,
                )

                update_fields = {
                    'content': sanitized_content,
                    'original_summary': article.get('summary', '') or original_content,
                    'content_generated': True,
                    'content_regenerated_at': datetime.now(timezone.utc).isoformat(),
                }
                guard_fields = (
                    "ai_rewritten",
                    "is_rewritten",
                    "verification_status",
                    "rewrite_status",
                    "manual_review_hidden_from_public",
                    "manual_review_reason",
                    "manual_review_created_at",
                    "editorial_metadata",
                    "manual_review_hits",
                    "archived",
                    "archived_at",
                    "archive_reason",
                )
                for field in guard_fields:
                    if (
                        field in guarded_article
                        and guarded_article.get(field) != article.get(field)
                    ):
                        update_fields[field] = guarded_article[field]

                await db.articles.update_one(
                    {'_id': article['_id']},
                    {'$set': update_fields}
                )
                regenerated += 1
                if guarded_article.get("manual_review_hidden_from_public") is True:
                    manual_review_routed += 1
                    logger.info(
                        f"Regenerated recent article into Manual Review "
                        f"({len(sanitized_content)} chars): {title[:60]}..."
                    )
                else:
                    safe_regenerated += 1
                    logger.info(
                        f"✅ Regenerated recent article "
                        f"({len(sanitized_content)} chars): {title[:60]}..."
                    )
            except Exception as regeneration_error:
                processing_failures += 1
                logger.error(
                    f"Recent article regeneration failed safely for "
                    f"{title[:60]}: {str(regeneration_error)}"
                )

        return {
            "success": True,
            "recent_articles_found": len(articles),
            "regenerated": regenerated,
            "safe_regenerated": safe_regenerated,
            "manual_review_routed": manual_review_routed,
            "skipped_empty": skipped_empty,
            "skipped_too_short": skipped_too_short,
            "processing_failures": processing_failures,
            "estimated_cost_usd": round(cost_estimate, 4)
        }

    except Exception as e:
        logger.error(f"Error regenerating recent content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/admin/regenerate-content")
async def regenerate_article_content(authorized: bool = Depends(get_admin_auth)):
    """
    Regenerate content for all existing articles using Perplexity.
    Only processes articles with short content (< 1000 chars).
    Cost: ~$0.005 per article
    Requires admin authentication.
    """
    try:
        # Find articles with short content
        articles = await db.articles.find({}).to_list(1000)
        
        short_content_articles = [
            a for a in articles 
            if len(a.get('content', '')) < 1000
        ]
        
        logger.info(f"Found {len(short_content_articles)} articles with short content to regenerate")
        
        regenerated = 0
        cost_estimate = 0
        
        for article in short_content_articles:
            title = article.get('title', '')
            original_content = article.get('content', '')
            source = article.get('source', 'BBC News')
            source_url = article.get('source_url', '')
            
            logger.info(f"Regenerating content for: {title[:40]}...")
            
            detailed_content = await perplexity_service.generate_article_content(
                title=title,
                summary=original_content,
                source=source,
                source_url=source_url
            )
            cost_estimate += 0.005
            
            if detailed_content and len(detailed_content) > len(original_content):
                await db.articles.update_one(
                    {'_id': article['_id']},
                    {'$set': {
                        'content': detailed_content,
                        'original_summary': original_content,
                        'content_generated': True
                    }}
                )
                regenerated += 1
                logger.info(f"✅ Regenerated content ({len(detailed_content)} chars): {title[:40]}...")
            else:
                logger.warning(f"Skipped - no improvement: {title[:40]}...")
        
        return {
            "success": True,
            "total_articles": len(articles),
            "short_content_found": len(short_content_articles),
            "regenerated": regenerated,
            "estimated_cost_usd": round(cost_estimate, 4)
        }
        
    except Exception as e:
        logger.error(f"Error regenerating content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/admin/clean-content")
async def clean_article_content(authorized: bool = Depends(get_admin_auth)):
    """
    Clean all article content - remove asterisks, brackets, and markdown formatting.
    This is a FREE operation (no API calls).
    Requires admin authentication.
    """
    try:
        import re
        articles = await db.articles.find({}).to_list(1000)
        
        cleaned = 0
        
        for article in articles:
            content = article.get('content', '')
            original_content = content
            
            # Clean up content
            content = re.sub(r'\[\d+\]', '', content)  # Remove citation brackets
            content = re.sub(r'\*+', '', content)  # Remove asterisks
            content = re.sub(r'#+\s*', '', content)  # Remove markdown headers
            content = re.sub(r'_+', ' ', content)  # Remove underscores
            content = re.sub(r'\s+', ' ', content).strip()  # Clean up extra spaces
            
            if content != original_content:
                await db.articles.update_one(
                    {'_id': article['_id']},
                    {'$set': {'content': content}}
                )
                cleaned += 1
                logger.info(f"✅ Cleaned content for: {article.get('title', '')[:40]}...")
        
        return {
            "success": True,
            "total_articles": len(articles),
            "cleaned": cleaned,
            "cost": "$0 (FREE)"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _remove_duplicates_internal():
    """
    Internal helper function to remove duplicate articles.
    Called automatically after imports and by the admin endpoint.
    Archives removed articles to archived_articles collection for link preservation.
    """
    try:
        articles = await db.articles.find({}).to_list(None)
        
        # Group by normalized source URL first, fall back to exact title
        duplicate_groups = {}
        for article in articles:
            title = article.get('title', '').strip()
            source_url = (article.get('source_url') or '').strip().lower()
            group_key = f"url::{source_url}" if source_url else f"title::{title.lower()}"
            if group_key not in duplicate_groups:
                duplicate_groups[group_key] = []
            duplicate_groups[group_key].append(article)
        
        duplicates_removed = 0
        short_removed = 0
        
        for group_key, group in duplicate_groups.items():
            if len(group) > 1:
                display_title = (group[0].get('title') or '').strip()
                def duplicate_keep_score(x):
                    """Prefer manually edited/protected articles over longer reimports."""
                    protected = bool(x.get("manual_edit_protected") or x.get("manual_edited"))
                    force_live = bool(x.get("force_live"))
                    updated = x.get("manual_edited_at") or x.get("updated_at") or x.get("created_at") or x.get("publishedDate") or ""
                    updated_key = updated.isoformat() if hasattr(updated, "isoformat") else str(updated or "")
                    return (
                        1 if protected else 0,
                        1 if force_live else 0,
                        updated_key,
                        len(x.get("content", "") or ""),
                    )

                # Keep the best canonical record. Manual/admin-edited records must win
                # over longer imported duplicates so editor changes are not replaced.
                group.sort(key=duplicate_keep_score, reverse=True)
                
                # Keep the first one, archive and remove the rest
                for article in group[1:]:
                    # Archive before deletion
                    article['archived_at'] = datetime.now(timezone.utc).isoformat()
                    article['archive_reason'] = 'duplicate'
                    original_id = article.pop('_id', None)
                    try:
                        await db.archived_articles.insert_one(article)
                    except:
                        pass  # Continue even if archival fails
                    
                    await db.articles.delete_one({'_id': original_id})
                    duplicates_removed += 1
                    logger.info(f"Archived duplicate: {display_title[:40]}...")
        
        # Archive low-quality short fallback articles so only full rewritten content stays live.
        remaining = await db.articles.find({}).to_list(None)
        boilerplate_markers = [
            "this story has been reported by",
            "more details are expected to emerge soon",
            "for the latest news from across the region, keep following",
        ]

        for article in remaining:
            if article.get("manual_review_hidden_from_public") is True:
                continue
            if _is_owner_protected_article(article):
                continue
            content = (article.get('content') or '').strip()
            summary = (article.get('summary') or '').strip()
            text_blob = ((content + " " + summary).strip())
            blob_len = len(text_blob)
            text_l = text_blob.lower()

            is_low_quality_short = blob_len < 1000
            is_boilerplate_fallback = any(m in text_l for m in boilerplate_markers)

            if is_low_quality_short or is_boilerplate_fallback:
                article['archived_at'] = datetime.now(timezone.utc).isoformat()
                article['archive_reason'] = 'short_content'
                original_id = article.pop('_id', None)
                try:
                    await db.archived_articles.insert_one(article)
                except:
                    pass

                await db.articles.delete_one({'_id': original_id})
                short_removed += 1
                logger.info(f"Archived low-quality article ({blob_len} chars): {article.get('title', '')[:60]}...")
        
        final_count = await db.articles.count_documents({})
        
        return {
            "success": True,
            "duplicates_removed": duplicates_removed,
            "short_articles_removed": short_removed,
            "total_removed": duplicates_removed + short_removed,
            "remaining_articles": final_count
        }
        
    except Exception as e:
        logger.error(f"Error in duplicate removal: {str(e)}")
        return {
            "success": False,
            "duplicates_removed": 0,
            "short_articles_removed": 0,
            "total_removed": 0,
            "error": str(e)
        }


@api_router.post("/admin/remove-duplicates")
async def remove_duplicate_articles(authorized: bool = Depends(get_admin_auth)):
    """
    Remove duplicate articles, keeping only the one with the longest content.
    Also removes articles with very short content (<200 chars).
    Requires admin authentication.
    """
    result = await _remove_duplicates_internal()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        await cap_visible_articles(keep=200)

    return result


@api_router.get("/news-sources")
async def get_news_sources():
    """
    Get list of available real news sources.
    """
    sources = {}
    for feed_key, config in news_feed_service.feeds.items():
        source = config['source']
        if source not in sources:
            sources[source] = {
                'name': source,
                'categories': [],
                'feeds': []
            }
        sources[source]['categories'].append(config['category'])
        sources[source]['feeds'].append({
            'key': feed_key,
            'category': config['category'],
            'url': config['url']
        })
    
    return {
        "sources": list(sources.values()),
        "total_feeds": len(news_feed_service.feeds)
    }


@api_router.post("/admin/refresh-article-images")
async def refresh_article_images(limit: int = 10, authorized: bool = Depends(get_admin_auth)):
    """
    Refresh images for existing articles to better match their content.
    Uses improved Unsplash search query building and photo ID comparison.
    Requires admin authentication.
    """
    try:
        # Get articles that might need image refresh - include _id for update
        articles_cursor = db.articles.find({}).sort("publishedDate", -1).limit(limit)
        articles = await articles_cursor.to_list(limit)
        
        updated_count = 0
        used_photo_ids = await get_used_images_from_db()
        
        for article in articles:
            try:
                # Get a new image based on improved query
                new_image = await get_dynamic_image(
                    title=article.get('title', ''),
                    category=article.get('category', 'Local News'),
                    content=article.get('content', ''),
                    scope=article.get('scope', 'cheshire'),
                    used_photo_ids=used_photo_ids
                )
                
                if new_image and new_image != article.get('image'):
                    # Update the article with the new image using _id
                    await db.articles.update_one(
                        {"_id": article['_id']},
                        {"$set": {"image": new_image}}
                    )
                    add_image_to_used(new_image, used_photo_ids)
                    updated_count += 1
                    logger.info(f"Updated image for: {article['title'][:40]}...")
                    
            except Exception as e:
                logger.error(f"Error refreshing image for article: {str(e)}")
                continue
        
        return {
            "success": True,
            "updated": updated_count,
            "total_checked": len(articles)
        }
        
    except Exception as e:
        logger.error(f"Error in refresh_article_images: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/admin/cleanup-bad-articles")
async def cleanup_bad_articles(authorized: bool = Depends(get_admin_auth)):
    """
    Remove articles that contain AI reasoning/thinking instead of actual news content.
    Requires admin authentication.
    """
    try:
        bad_indicators = ['THOUGHT:', 'I need to write', 'I will write', 'Let me write',
                        'words in plain text', 'NO markdown', 'Crucially,', 'This means no bold',
                        'formatting symbols', 'Here is the article', 'Here\'s the article']
        
        all_articles = await db.articles.find({}).to_list(1000)
        removed_count = 0
        removed_titles = []
        
        for article in all_articles:
            title = article.get('title', '')
            content = article.get('content', '')[:500]
            
            # Check if article has bad content
            has_bad = any(ind.lower() in title.lower() or ind.lower() in content.lower() 
                         for ind in bad_indicators)
            
            if has_bad:
                await db.articles.delete_one({"_id": article['_id']})
                removed_count += 1
                removed_titles.append(title[:50])
                logger.info(f"Removed bad article: {title[:50]}...")
        
        return {
            "success": True,
            "removed": removed_count,
            "removed_titles": removed_titles[:10]  # Show first 10
        }
        
    except Exception as e:
        logger.error(f"Error in refresh_article_images: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/admin/cleanup-all")
async def cleanup_all(authorized: bool = Depends(get_admin_auth)):
    """
    Comprehensive cleanup: Remove duplicate articles, duplicate images, and refresh all images.
    Requires admin authentication.
    """
    try:
        results = {
            "duplicates_removed": 0,
            "images_refreshed": 0,
            "total_articles_before": 0,
            "total_articles_after": 0
        }
        
        # Count before
        results["total_articles_before"] = await db.articles.count_documents({})
        
        # Step 1: Remove duplicate articles (same title)
        all_articles = await db.articles.find({}).to_list(1000)
        seen_titles = {}
        duplicates_to_remove = []
        
        for article in all_articles:
            title = article.get('title', '').lower().strip()
            if title in seen_titles:
                duplicates_to_remove.append(article['_id'])
            else:
                seen_titles[title] = article['_id']
        
        if duplicates_to_remove:
            await db.articles.delete_many({"_id": {"$in": duplicates_to_remove}})
            results["duplicates_removed"] = len(duplicates_to_remove)
            logger.info(f"Removed {len(duplicates_to_remove)} duplicate articles")
        
        # Step 2: Find and fix duplicate images using PHOTO ID comparison
        remaining_articles = await db.articles.find({}).to_list(1000)
        
        # Group articles by photo ID (not full URL)
        photo_id_map = {}  # photo_id -> [(article_id, full_url), ...]
        for article in remaining_articles:
            img = article.get('image', '')
            if img:
                photo_id = extract_photo_id(img)
                if photo_id:
                    if photo_id not in photo_id_map:
                        photo_id_map[photo_id] = []
                    photo_id_map[photo_id].append((article['_id'], img))
        
        # Refresh images for articles with duplicate photo IDs
        used_photo_ids = set()
        for photo_id, article_data in photo_id_map.items():
            if len(article_data) > 1:
                # Multiple articles using same photo - refresh all but first
                used_photo_ids.add(photo_id)
                for article_id, old_url in article_data[1:]:
                    article = await db.articles.find_one({"_id": article_id})
                    if article:
                        new_image = await get_dynamic_image(
                            title=article.get('title', ''),
                            category=article.get('category', 'Local News'),
                            content=article.get('content', ''),
                            scope=article.get('scope', 'cheshire'),
                            used_photo_ids=used_photo_ids
                        )
                        if new_image:
                            await db.articles.update_one(
                                {"_id": article_id},
                                {"$set": {"image": new_image}}
                            )
                            add_image_to_used(new_image, used_photo_ids)
                            results["images_refreshed"] += 1
                            logger.info(f"Refreshed duplicate image for: {article['title'][:40]}...")
        
        # Count after
        results["total_articles_after"] = await db.articles.count_documents({})
        
        return {"success": True, "results": results}
        
    except Exception as e:
        logger.error(f"Error in cleanup_all: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/admin/refresh-all-images-uk")
async def refresh_all_images_uk(authorized: bool = Depends(get_admin_auth)):
    """
    Refresh ALL article images with UK/British-themed images from Unsplash.
    This ensures all images are relevant to UK/Cheshire news context.
    Uses photo ID comparison to ensure uniqueness.
    Requires admin authentication.
    """
    try:
        articles = await db.articles.find({}).to_list(1000)
        updated_count = 0
        used_photo_ids = set()
        
        for article in articles:
            try:
                # Get a UK-specific image based on the improved query builder
                new_image = await get_dynamic_image(
                    title=article.get('title', ''),
                    category=article.get('category', 'Local News'),
                    content=article.get('content', ''),
                    scope=article.get('scope', 'cheshire'),
                    used_photo_ids=used_photo_ids
                )
                
                if new_image:
                    await db.articles.update_one(
                        {"_id": article['_id']},
                        {"$set": {"image": new_image}}
                    )
                    add_image_to_used(new_image, used_photo_ids)
                    updated_count += 1
                    logger.info(f"Refreshed UK image for: {article['title'][:40]}...")
                    
            except Exception as e:
                logger.error(f"Error refreshing image: {str(e)}")
                continue
        
        return {
            "success": True,
            "updated": updated_count,
            "total": len(articles)
        }
        
    except Exception as e:
        logger.error(f"Error in refresh_all_images_uk: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Location keywords for filtering articles by area
LOCATION_KEYWORDS = {
    'chester': ['chester', 'ellesmere port', 'neston', 'flint'],
    'warrington': ['warrington', 'lymm', 'culcheth', 'birchwood', 'runcorn', 'widnes'],
    'crewe': ['crewe', 'nantwich', 'sandbach', 'alsager'],
    'wirral': ['wirral', 'birkenhead', 'wallasey', 'heswall', 'bebington', 'west kirby'],
    'macclesfield': ['macclesfield', 'alderley edge', 'poynton', 'congleton', 'bollington'],
    'wilmslow': ['wilmslow', 'handforth', 'styal'],
    'knutsford': ['knutsford', 'tatton', 'mobberley'],
    'stockport': ['stockport', 'cheadle', 'bramhall', 'hazel grove', 'marple'],
    'northwich': ['northwich', 'winsford', 'middlewich', 'hartford'],
    'cheshire-general': ['cheshire']  # For general Cheshire articles
}

PUBLIC_CATEGORY_HUBS = {
    "local-news": {
        "label": "Local",
        "canonical_category": "Local News",
        "aliases": ("Local",),
        "title": "Local news and updates",
        "description": "Latest local reporting from across Cheshire and its communities.",
    },
    "uk-news": {
        "label": "UK",
        "canonical_category": "UK News",
        "aliases": ("UK",),
        "title": "UK news and updates",
        "description": "Important UK news and developments affecting Cheshire readers.",
    },
    "business": {
        "label": "Business",
        "canonical_category": "Business",
        "aliases": ("Economy", "Economic"),
        "title": "Business news and updates",
        "description": "Cheshire business, investment, jobs and economic news.",
    },
    "finance": {
        "label": "Finance",
        "canonical_category": "Finance",
        "aliases": ("Tax", "Property", "Property & Tax", "Money"),
        "title": "Finance news and updates",
        "description": "Personal finance, tax, markets and money news for Cheshire readers.",
    },
    "ai-tech": {
        "label": "AI & Tech",
        "canonical_category": "AI & Tech",
        "aliases": ("AI", "Tech", "Technology"),
        "title": "AI & Tech news and updates",
        "description": "Practical artificial intelligence and technology coverage.",
    },
}

PUBLIC_LOCATION_HUBS = {
    "cheshire-general",
    "chester",
    "warrington",
    "crewe",
    "macclesfield",
    "wilmslow",
    "knutsford",
    "northwich",
}


def _public_category_hub_for_value(value: str):
    candidate = str(value or "").strip().casefold()
    for config in PUBLIC_CATEGORY_HUBS.values():
        accepted = (
            config["canonical_category"],
            config["label"],
            *config["aliases"],
        )
        if candidate in {str(item).casefold() for item in accepted}:
            return config
    return None


def _apply_public_category_hub_filter(query: dict, config: dict) -> None:
    canonical = config["canonical_category"]
    if canonical == "Local News":
        query.setdefault("$and", []).extend(
            [
                {"category": {"$in": [canonical, *config["aliases"]]}},
                {
                    "$or": [
                        {"is_local_source": True},
                        {"scope": {"$in": ["cheshire", "local"]}},
                        {"location": {"$in": sorted(PUBLIC_LOCATION_HUBS - {"cheshire-general"})}},
                    ]
                },
            ]
        )
        return

    query["category"] = {
        "$in": [canonical, *config["aliases"]],
    }


def _article_matches_public_category_hub(article: dict, config: dict) -> bool:
    category = str(article.get("category") or "").strip().casefold()
    accepted = {
        str(value).casefold()
        for value in (config["canonical_category"], *config["aliases"])
    }
    if category not in accepted:
        return False

    if config["canonical_category"] != "Local News":
        return True

    scope = str(article.get("scope") or "").strip().casefold()
    location = str(article.get("location") or "").strip().casefold()
    return (
        article.get("is_local_source") is True
        or scope in {"cheshire", "local"}
        or location in (PUBLIC_LOCATION_HUBS - {"cheshire-general"})
    )


def _article_matches_public_location_hub(article: dict, location: str) -> bool:
    if location == "cheshire-general":
        has_general_location = (
            "location" not in article
            or article.get("location") is None
        )
        return has_general_location and (
            article.get("is_cheshire_related") is True
            or article.get("is_local_source") is True
        )

    return (
        str(article.get("location") or "").strip().casefold()
        == str(location).casefold()
    )


@api_router.get("/articles/location/cheshire-general")
async def get_cheshire_general_articles(
    skip: int = 0,
    limit: int = 20
):
    """Get articles that mention Cheshire but don't have a specific town location.
    
    These are general Cheshire-wide articles that aren't specific to any particular town.
    """
    try:
        # Get articles where:
        # 1. location field is null/missing (not tagged to specific location)
        # 2. Article is Cheshire-related (is_cheshire_related or from local source)
        query = {
            '$and': [
                {'$or': [
                    {'archived': {'$exists': False}},
                    {'archived': False}
                ]},
                {'manual_review_hidden_from_public': {'$ne': True}},
                {'$or': [
                    {'location': None},
                    {'location': {'$exists': False}}
                ]},
                {'$or': [
                    {'is_cheshire_related': True},
                    {'is_local_source': True},
                    {'source': {'$in': ['Cheshire Live', 'Warrington Guardian', 'Manchester Evening News']}}
                ]}
            ]
        }
        
        articles = await db.articles.find(
            query,
            {
                '_id': 1, 'title': 1, 'content': 1, 'summary': 1, 'category': 1,
                'author': 1, 'publishedDate': 1, 'created_at': 1, 'image': 1, 'tags': 1,
                'featured': 1, 'source': 1, 'source_url': 1,
                    'priority_location': 1,
                    'location': 1, 'scope': 1, 'is_local_source': 1,
                'location': 1
            }
        ).sort('publishedDate', -1).skip(skip).limit(limit).to_list(limit)
        
        total_count = await db.articles.count_documents(query)
        
        # Convert ObjectId to string
        for article in articles:
            article['id'] = str(article['_id'])
            del article['_id']

            # Normalize scope for frontend consistency
            # Local sources should always be treated as Cheshire scope
            if article.get('is_local_source') is True:
                article['scope'] = 'cheshire'
            elif not article.get('scope'):
                article['scope'] = 'uk'
        
        return {
            'articles': articles,
            'location': 'Cheshire',
            'total': total_count,
            'description': 'General Cheshire news not specific to any particular town'
        }
        
    except Exception as e:
        logger.error(f"Error getting Cheshire general articles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/articles/location/{location}")
async def get_articles_by_location(
    location: str,
    skip: int = 0,
    limit: int = 20
):
    """Get articles filtered by location (Chester, Warrington, etc.)
    
    STRICT MODE: Only returns articles where the 'location' field exactly matches.
    This ensures each location page shows only articles primarily about that area.
    """
    try:
        location_lower = location.lower()
        
        if location_lower not in LOCATION_KEYWORDS:
            raise HTTPException(status_code=404, detail=f"Location '{location}' not found")
        
        # STRICT: Only match articles with location field set to this location,
        # while applying the same public visibility guard used by the main articles feed.
        # This prevents town pages listing articles that later 404 on the article detail page.
        query = {
            "$and": [
                {"location": location_lower},
                {"$or": [{"archived": {"$exists": False}}, {"archived": False}]},
                {"manual_review_hidden_from_public": {"$ne": True}},
            ]
        }
        
        articles = await db.articles.find(
            query,
            {
                '_id': 1, 'title': 1, 'content': 1, 'summary': 1, 'category': 1,
                'author': 1, 'publishedDate': 1, 'created_at': 1, 'image': 1, 'tags': 1,
                'featured': 1, 'source': 1, 'source_url': 1, 'scope': 1, 'is_local_source': 1,
                'location': 1
            }
        ).sort('publishedDate', -1).skip(skip).limit(limit).to_list(limit)
        
        # Get total count for this location
        total_count = await db.articles.count_documents(query)
        
        # Convert ObjectId to string
        for article in articles:
            article['id'] = str(article['_id'])
            del article['_id']
        
        return {
            'articles': articles,
            'location': location.capitalize(),
            'total': total_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting articles by location: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/articles")
async def get_articles(
    category: Optional[str] = None, 
    skip: int = 0, 
    limit: int = 20,
    source_type: Optional[str] = None,  # "local", "national", or None for all
    include_archived: bool = False,  # By default, exclude archived articles
    search: Optional[str] = None,  # Search query for title and content
    with_total: bool = False  # Return {articles,total} envelope when true
):
    """Get all articles with optional filtering by category, source type, and search"""
    try:
        # Check cache for default homepage request (most common)
        cache_key = f"articles:{category}:{skip}:{limit}:{source_type}:{include_archived}:{with_total}:{search or ''}"
        if not search and skip == 0 and limit == 20 and not category:
            cached = api_cache.get(cache_key, ttl_seconds=30)  # 30 second cache
            if cached:
                # Normalise cached shape (older cache entries may be a list)
                if isinstance(cached, dict) and "articles" in cached:
                    return cached
                if isinstance(cached, list):
                    return {
                        "articles": cached,
                        "total": len(cached),
                        "skip": skip,
                        "limit": limit,
                        "category": category,
                        "include_archived": include_archived,
                    }
                return cached
        
        query = {}
        
        # Exclude archived and manual-review-hidden articles by default
        if not include_archived:
            query["$and"] = [
                {"$or": [{"archived": {"$exists": False}}, {"archived": False}]},
                {"manual_review_hidden_from_public": {"$ne": True}},
            ]
        
        # Search functionality - search in title and content
        if search and len(search) >= 2:
            import re
            search_regex = {'$regex': re.escape(search), '$options': 'i'}
            # Override the query to include search while preserving public visibility filters
            if not include_archived:
                query = {
                    "$and": [
                        {"$or": [{"archived": {"$exists": False}}, {"archived": False}]},
                        {"manual_review_hidden_from_public": {"$ne": True}},
                        {"$or": [{"title": search_regex}, {"content": search_regex}]}
                    ]
                }
            else:
                query["$or"] = [{"title": search_regex}, {"content": search_regex}]
            
            # Direct search query - return results sorted by relevance
            articles = await db.articles.find(
                query,
                {
                    '_id': 1, 'id': 1, 'title': 1, 'content': 1, 'summary': 1, 'category': 1,
                    'author': 1, 'publishedDate': 1, 'created_at': 1, 'image': 1, 'tags': 1,
                    'featured': 1, 'source': 1, 'source_url': 1, 'scope': 1, 'is_local_source': 1,
                    'location': 1, 'priority_location': 1
                }
            ).sort('publishedDate', -1).skip(skip).limit(limit).to_list(limit)
            
            # Process IDs and expose ready-to-use canonical article URLs.
            for article in articles:
                if 'id' not in article or not article['id']:
                    article['id'] = str(article['_id'])
                if '_id' in article:
                    del article['_id']

                article_id = str(article.get("id") or "").strip()
                article_slug = _article_slug_from_title(article.get("title"))
                article["articleId"] = article_id
                article["slug"] = article_slug
                article["canonicalUrl"] = (
                    f"https://cheshiretoday.co.uk/article/{article_id}/{article_slug}"
                )
            
            return {"articles": articles, "total": len(articles), "search": search}
        
        # Category filtering
        if category and category != 'all':
            public_hub = _public_category_hub_for_value(category)
            if public_hub:
                _apply_public_category_hub_filter(query, public_hub)
            else:
                query['category'] = category
        
        # Additional source type filtering
        if source_type == 'local':
            query['is_local_source'] = True
        elif source_type == 'national':
            query['is_local_source'] = False

        # Total count for pagination/UI (respects include_archived + filters)
        try:
            total_count = await db.articles.count_documents(query)
        except Exception:
            total_count = 0
        
        # For "all" category (Latest News), use interleaved ordering: Local, Local, UK, UK
        if (not category or category == 'all') and not source_type and not search:
            # Fetch local and UK articles separately
            # include_archived support (build-phase cap archives older items)
            public_visibility_clauses = []
            if not include_archived:
                public_visibility_clauses = [
                    {'$or': [{'archived': {'$exists': False}}, {'archived': False}]},
                    {'manual_review_hidden_from_public': {'$ne': True}},
                ]

            local_q = {'is_local_source': True}
            uk_q = {'is_local_source': {'$ne': True}}
            force_q = {'force_live': True}
            if public_visibility_clauses:
                local_q = {'$and': [local_q] + public_visibility_clauses}
                uk_q = {'$and': [uk_q] + public_visibility_clauses}
                force_q = {'$and': [force_q] + public_visibility_clauses}

            force_articles = await db.articles.find(force_q,
                {
                    '_id': 1, 'title': 1, 'summary': 1, 'category': 1,
                    'author': 1, 'publishedDate': 1, 'created_at': 1, 'image': 1, 'tags': 1,
                    'featured': 1, 'source': 1, 'source_url': 1, 'scope': 1, 'is_local_source': 1,
                    'location': 1, 'priority_location': 1, 'force_live': 1
                }
            ).sort([('created_at', -1), ('publishedDate', -1)]).limit(limit*5).to_list(limit*5)

            local_articles = await db.articles.find(local_q,
                {
                    '_id': 1, 'title': 1, 'summary': 1, 'category': 1,
                    'author': 1, 'publishedDate': 1, 'created_at': 1, 'image': 1, 'tags': 1,
                    'featured': 1, 'source': 1, 'source_url': 1, 'scope': 1, 'is_local_source': 1,
                    'location': 1, 'priority_location': 1
                }
            ).sort([('created_at', -1), ('publishedDate', -1)]).limit(limit*6).to_list(limit*6)
            
            uk_articles = await db.articles.find(uk_q,
                {
                    '_id': 1, 'title': 1, 'summary': 1, 'category': 1,
                    'author': 1, 'publishedDate': 1, 'created_at': 1, 'image': 1, 'tags': 1,
                    'featured': 1, 'source': 1, 'source_url': 1, 'scope': 1, 'is_local_source': 1,
                    'location': 1, 'priority_location': 1
                }
            ).sort([('created_at', -1), ('publishedDate', -1)]).limit(limit*4).to_list(limit*4)

            # UK homepage noise filter (removes sport/video/tabloid-politics filler from 'all' feed)
            # Toggle: UK_FILTER_NOISE=0 to disable.
            UK_FILTER_NOISE = os.getenv("UK_FILTER_NOISE", "1") not in ("0", "false", "False")
            if UK_FILTER_NOISE and (uk_articles or local_articles):
                import re
                econ_hint = re.compile(
                    r"\b(tax|budget|inflation|interest\s*rate|rates|mortgage|rent|wages|jobs|growth|economy|economic|"
                    r"business|finance|markets?|prices?|bills?|energy|housing|trade|tariff|investment)\b",
                    re.I,
                )
                noise_kw = re.compile(
                    r"\b(the\s+papers|on\s+ropes|nightmare\s+for|grop(?:e|ing)|pitch\s+invader)\b",
                    re.I,
                )

                def is_noise_uk(a: dict) -> bool:
                    cat = (a.get("category") or "").lower()
                    src = (a.get("source") or "").lower()
                    url = (a.get("source_url") or "").lower()
                    title = (a.get("title") or "").lower()
                    summary = (a.get("summary") or "").lower()
                    text_meta = f"{title} {summary}"

                    # Sports + highlight/video clips
                    if "sport" in cat or "sport" in src or "/sport/" in url or "skysports" in url:
                        return True
                    if "/watch/" in url or "/video" in url or "watch video" in title:
                        return True

                    # Tabloid/paper-roundups + low-signal drama
                    if noise_kw.search(text_meta):
                        return True

                    # Politics drama in UK News unless it has clear economic impact
                    if ("uk news" in cat) and re.search(r"\b(mp|labour|conservative|tory|starmer|reeves|parliament|byelection|election)\b", title, re.I):
                        if not econ_hint.search(text_meta):
                            return True
                    # De-emphasize generic human-interest in UK News unless it has clear impact.
                    # Keeps the UK pillar aligned to economy/business/policy utility.
                    if cat == "uk news":
                        impact_kw = re.compile(
                            r"\b(nhs|hospital|gp|doctor|school|education|council|planning|housing|rent|mortgage|"
                            r"tax|budget|inflation|interest\s*rate|rates|jobs|wages|economy|economic|business|"
                            r"finance|markets?|prices?|bills?|energy|transport|rail|road|roadworks|investment|"
                            r"trade|tariff|regulation|regulator|ofgem|ofwat|boe|bank of england)\b",
                            re.I,
                        )
                        if not econ_hint.search(text_meta) and not impact_kw.search(text_meta):
                            return True


                    return False

                uk_articles = [a for a in uk_articles if not is_noise_uk(a)]

                def is_editorial_noise(a: dict) -> bool:
                    cat = (a.get("category") or "").lower()
                    src = (a.get("source") or "").lower()
                    url = (a.get("source_url") or "").lower()
                    title = (a.get("title") or "").lower()
                    summary = (a.get("summary") or "").lower()
                    text_meta = f"{title} {summary}"

                    # Audio / podcasts / videos / galleries
                    if "/audio/" in url or "podcast" in title or "podcast" in summary:
                        return True
                    if "/video" in url or "/watch/" in url or "watch video" in title:
                        return True
                    if "/gallery/" in url:
                        return True

                    # Letters / cartoons / opinion-style filler
                    if re.search(r"\b(letter|letters|cartoon|opinion|editorial)\b", title, re.I):
                        return True

                    # Entertainment / celebrity / culture leakage that does not fit live news mix
                    if re.search(
                        r"\b(celebrity|showbiz|reality\s*tv|love island|netflix|concert|album|music\s*video|bts|kris jenner|kardashian)\b",
                        text_meta,
                        re.I,
                    ):
                        return True

                    # Cheshire Today public-feed quality guard:
                    # remove weak crime, tragedy, tourism/lifestyle filler, and random global tech/business items
                    # from the homepage/API feed without affecting article URLs, imports, admin, newsletters, or archives.
                    if re.search(
                        r"\b(cocaine|drugs?|gangs?|devastating diagnosis|started to ache|lost everything|"
                        r"hit-and-run|knocked off|smash between|train station crash|emergency services respond|"
                        r"in pictures|pictures from|anniversary celebrations|"
                        r"horror m56 crash|two in hospital after horror|chester zoo celebrates|aardvark|"
                        r"lake study|cancel climate impact|ill health in old age|roblox|"
                        r"keep your home.*cool|video doorbells|football club could become home|"
                        r"fastest growing sport|five engines called|discarded cigarette|firefighters deal|city centre incident|"
                        r"pokemon|alton towers|period drama|free to watch|animal park|tiger cubs?|hedgehogs?|"
                        r"x limits|freeloaders|airbus gets hpc|hpc-as-a-service|zte showcases|brazil|"
                        r"typhoon jets|swinney|first minister vote|swatch|starbucks korea|tank day|"
                        r"elon musk has lost|new high street crime unit|st brelade|iran hints it could interfere|"
                        r"vmware quietly debuts|mace wants to make power bills)\b",
                        text_meta,
                        re.I,
                    ):
                        return True

                    # Off-brand science / tech / business filler
                    if cat in {"science", "tech", "business", "uk news"}:
                        if re.search(r"\b(letter|letters|cartoon|podcast)\b", text_meta, re.I):
                            return True

                    return False

                def is_local_editorial_noise(a: dict) -> bool:
                    """Light local-only homepage filter.

                    Keep normal Cheshire soft/local news visible while still removing
                    obvious media-format filler that should not lead the homepage.
                    """
                    url = (a.get("source_url") or "").lower()
                    title = (a.get("title") or "").lower()
                    summary = (a.get("summary") or "").lower()
                    text_meta = f"{title} {summary}"

                    if "/audio/" in url or "podcast" in text_meta:
                        return True
                    if "/video" in url or "/watch/" in url or "watch video" in title:
                        return True
                    if "/gallery/" in url or "in pictures" in title or "pictures from" in title:
                        return True
                    if re.search(r"\b(letter|letters|cartoon|opinion|editorial)\b", title, re.I):
                        return True

                    return False

                local_articles = [a for a in local_articles if not is_local_editorial_noise(a)]
                uk_articles = [a for a in uk_articles if not is_editorial_noise(a)]

            # Interleave: 2 local, 2 UK, repeat (with presentation-time crime cap)
            # Keeps crime-like stories to a very low cap in the TOP feed (default 1).
            crime_cap_top = int(os.getenv("CRIME_MAX_TOP", "1") or "1")
            incident_cap_top = int(os.getenv("INCIDENT_MAX_TOP", "2") or "2")
            incident_count_top = 0
            # Apply lead-guard to both crime + incident-like content
            lead_non_sensitive = int(os.getenv("LEAD_NON_SENSITIVE", os.getenv("LEAD_NON_CRIME", "3")) or "3")

            lead_non_crime = int(os.getenv("LEAD_NON_CRIME", "3") or "3")
            crime_count_top = 0

            def classify_sensitive(a: dict) -> str | None:

                import re

                cat = (a.get('category') or '').lower()

                title = (a.get('title') or '').lower()

                summary = (a.get('summary') or '').lower()

                content = (a.get('content') or '').lower()

                text = ' '.join([title, summary, content])


                url = (a.get('source_url') or '').lower()

                if '/audio/' in url or 'podcast' in title:

                    return None


                # Category signals

                if 'court' in cat or 'crime' in cat:

                    return 'crime'


                # HARD CRIME (excluded from homepage feed entirely)

                hard_crime_kw = re.compile(
        
                    r"(murder(?:s)?|kill(?:ed|s)?|homicide|manslaughter|"

                    r"found dead|body found|woman found dead|man found dead|found hanged|hanged|strangl(?:ed|ing)?|"

                    r"stab(?:bing|bed|s)?|shoot(?:ing|s)?|rape(?:d)?|"

                    r"jailed|sentenc(?:ed|ing)|charged|trial|convict(?:ed|ion))",

                    re.I,

                )

                if hard_crime_kw.search(text):

                    return 'hard_crime'


                crime_kw = re.compile(

                    r"(murder(?:s)?|kill(?:ed|s)?|manslaughter|homicide|"

                    r"stab(?:bing|bed|s)?|shoot(?:ing|s)?|firearm(?:s)?|gunman|"

                    r"rape(?:d)?|sexual assault|robber(?:y|ies)|burglar(?:y|ies)|arson|"

                    r"charged|prosecut(?:ed|ion)|trial|sentenc(?:ed|ing)|jailed|jail|prison|convict(?:ed|ion)|inquest(?:s)?)",

                    re.I,

                )

                if crime_kw.search(text):

                    return 'crime'


                # Incident/traffic (separate from crime; optionally capped in top feed)

                incident_kw = re.compile(

                    r"\b(crash|collision|road closed|lane closed|car fire|vehicle fire|queues? building|"

                    r"traffic is slow|delays?|death notices?|death|dead|died|dies|body found|found dead|found hanged|hanged|police presence|"

                    r"police cordon|cordon|scene|investigation|emergency services|ambulance|paramedics|"

                    r"fire service|air ambulance|assault(?:ed|s)?|cctv appeal|reported to police|"

                    r"police probe|police investigating|grop(?:e|ing|ed))\b",

                    re.I,

                )

                if incident_kw.search(text):

                    return 'incident'


                return None


            articles = []
            deferred_lead_incident = []  # incident-like items deferred ONLY to protect lead positions
            deferred_lead_crime = []     # crime-like items deferred ONLY to protect lead positions
            deferred_overcap_incident = []  # incident-like items skipped due to cap (never re-added)
            deferred_overcap_crime = []     # crime-like items skipped due to hard cap (never re-added)
            local_idx = 0
            uk_idx = 0

            while len(articles) < limit and (local_idx < len(local_articles) or uk_idx < len(uk_articles)):
                # Add 2 local articles
                for _ in range(2):
                    if local_idx < len(local_articles) and len(articles) < limit:
                        a = local_articles[local_idx]
                        local_idx += 1
                        kind = classify_sensitive(a)
                        if kind == "hard_crime":
                            continue
                        if kind == "incident":
                            # Keep incidents out of lead positions when possible
                            if len(articles) < lead_non_sensitive:
                                deferred_lead_incident.append(a)
                                continue
                            if incident_count_top >= incident_cap_top:
                                deferred_overcap_incident.append(a)
                                continue
                            incident_count_top += 1
                        elif kind == "crime":
                            # Keep crime out of lead positions when possible
                            if len(articles) < lead_non_sensitive:
                                deferred_lead_crime.append(a)
                                continue
                            if crime_count_top >= crime_cap_top:
                                deferred_overcap_crime.append(a)
                                continue
                            crime_count_top += 1
                        articles.append(a)

                # Add 2 UK articles
                for _ in range(2):
                    if uk_idx < len(uk_articles) and len(articles) < limit:
                        a = uk_articles[uk_idx]
                        uk_idx += 1
                        kind = classify_sensitive(a)
                        if kind == "hard_crime":
                            continue
                        if kind == "incident":
                            # Keep incidents out of lead positions when possible
                            if len(articles) < lead_non_sensitive:
                                deferred_lead_incident.append(a)
                                continue
                            if incident_count_top >= incident_cap_top:
                                deferred_overcap_incident.append(a)
                                continue
                            incident_count_top += 1
                        elif kind == "crime":
                            # Keep crime out of lead positions when possible
                            if len(articles) < lead_non_sensitive:
                                deferred_lead_crime.append(a)
                                continue
                            if crime_count_top >= crime_cap_top:
                                deferred_overcap_crime.append(a)
                                continue
                            crime_count_top += 1
                        articles.append(a)

            # If we still have space, keep filling from whichever pool still has items.
            # This prevents feed starvation when one side runs low after filtering.
            while len(articles) < limit and (local_idx < len(local_articles) or uk_idx < len(uk_articles)):
                if local_idx < len(local_articles):
                    a = local_articles[local_idx]
                    local_idx += 1
                else:
                    a = uk_articles[uk_idx]
                    uk_idx += 1

                kind = classify_sensitive(a)
                if kind == "hard_crime":
                    continue
                if kind == "incident":
                    if len(articles) < lead_non_sensitive:
                        deferred_lead_incident.append(a)
                        continue
                    if incident_count_top >= incident_cap_top:
                        deferred_overcap_incident.append(a)
                        continue
                    incident_count_top += 1
                elif kind == "crime":
                    if len(articles) < lead_non_sensitive:
                        deferred_lead_crime.append(a)
                        continue
                    if crime_count_top >= crime_cap_top:
                        deferred_overcap_crime.append(a)
                        continue
                    crime_count_top += 1

                articles.append(a)

            # If we still have space, append ONLY lead-deferred sensitive items.
            # Re-add incidents first (utility), then crime; both strictly capped.
            if len(articles) < limit and deferred_lead_incident:
                for a in deferred_lead_incident:
                    if len(articles) >= limit:
                        break
                    if incident_count_top >= incident_cap_top:
                        break
                    incident_count_top += 1
                    articles.append(a)

            if len(articles) < limit and deferred_lead_crime:
                for a in deferred_lead_crime:
                    if len(articles) >= limit:
                        break
                    if crime_count_top >= crime_cap_top:
                        break
                    crime_count_top += 1
                    articles.append(a)

            # Final fallback: if curation/filtering leaves the homepage short,
            # top up from the normal visible pool so /api/articles can still
            # return the requested number of items.
            if len(articles) < limit:
                seen_ids = {str(a.get('_id')) for a in articles if a.get('_id')}
                fallback_q = {
                    "$or": [{"archived": {"$exists": False}}, {"archived": False}],
                    "manual_review_hidden_from_public": {"$ne": True}
                }
                fallback_items = await db.articles.find(
                    fallback_q,
                    {
                        '_id': 1, 'title': 1, 'summary': 1, 'category': 1,
                        'author': 1, 'publishedDate': 1, 'created_at': 1, 'image': 1, 'tags': 1,
                        'featured': 1, 'source': 1, 'source_url': 1, 'scope': 1,
                        'is_local_source': 1, 'location': 1, 'priority_location': 1
                    }
                ).sort([('created_at', -1), ('publishedDate', -1)]).limit(limit * 6).to_list(limit * 6)

                for a in fallback_items:
                    aid = str(a.get('_id'))
                    if not aid or aid in seen_ids:
                        continue

                    # Re-apply homepage noise and sensitive-story filters to fallback items
                    if a.get("is_local_source") is not True and UK_FILTER_NOISE and is_noise_uk(a):
                        continue
                    if UK_FILTER_NOISE and is_editorial_noise(a):
                        continue

                    kind = classify_sensitive(a)
                    title_l = (a.get("title") or "").lower()
                    if "death notice" in title_l or "death notices" in title_l:
                        continue
                    if kind == "hard_crime":
                        continue
                    if kind == "incident":
                        continue
                    if kind == "crime":
                        continue

                    articles.append(a)
                    seen_ids.add(aid)
                    if len(articles) >= limit:
                        break

            
            # Prepend recent force_live articles so admin-picked stories can lead briefly,
            # but older manual/promoted articles do not permanently make the homepage look stale.
            if force_articles:
                existing_ids = {str(a.get('_id')) for a in articles if a.get('_id')}
                forced_front = []
                force_pin_hours = int(os.getenv("FORCE_LIVE_PIN_HOURS", "72") or "72")
                force_pin_cutoff = datetime.now(timezone.utc) - timedelta(hours=force_pin_hours)

                def is_recent_force_live(a: dict) -> bool:
                    raw_dt = a.get("publishedDate") or a.get("created_at")
                    if isinstance(raw_dt, datetime):
                        article_dt = raw_dt
                    elif isinstance(raw_dt, str):
                        try:
                            article_dt = datetime.fromisoformat(raw_dt.replace("Z", "+00:00"))
                        except Exception:
                            return False
                    else:
                        return False

                    if article_dt.tzinfo is None:
                        article_dt = article_dt.replace(tzinfo=timezone.utc)
                    return article_dt >= force_pin_cutoff

                for a in force_articles:
                    aid = str(a.get('_id'))
                    if not aid or aid in existing_ids:
                        continue
                    if not is_recent_force_live(a):
                        continue
                    forced_front.append(a)
                    existing_ids.add(aid)
                if forced_front:
                    articles = forced_front + articles

            # Soft authority boost: gently reorder only the top of the feed
            # to surface Business/Tech/economic relevance without breaking the
            # Local/UK interleave structure or overall recency.
            boost_top_n = int(os.getenv("BOOST_TOP_N", "8") or "8")
            if boost_top_n > 0 and len(articles) > 1:
                top_n = min(boost_top_n, len(articles))
                head = articles[:top_n]
                tail = articles[top_n:]

                econ_terms = (
                    "tax","inflation","budget","investment","jobs","housing","mortgage",
                    "rates","economy","economic","business","finance","growth"
                )
                boosted_cats = {"business","tech","finance","ai & tech"}

                def boost_score(a: dict) -> int:
                    score = 0
                    cat = (a.get("category") or "").lower().strip()
                    if cat in boosted_cats:
                        score += 2
                    text = " ".join([
                        (a.get("title") or ""),
                        (a.get("summary") or ""),
                        (a.get("content") or ""),
                    ]).lower()
                    if any(t in text for t in econ_terms):
                        score += 1
                    if a.get("is_priority_cheshire") is True:
                        score += 1
                    return score

                # Keep the first N items fixed to preserve Cheshire-first lead ordering.
                # Only re-rank the remainder of the head slice.
                keep_prefix = int(os.getenv("BOOST_KEEP_PREFIX", "0") or "0")
                keep_prefix = max(0, min(keep_prefix, len(head)))

                fixed = head[:keep_prefix]
                rest = head[keep_prefix:]

                # Stable sort by score descending, preserving original order on ties
                scored = [(i, boost_score(a), a) for i, a in enumerate(rest)]
                scored.sort(key=lambda x: (-x[1], x[0]))
                rest2 = [a for _, _, a in scored]

                articles = fixed + rest2 + tail

            # Apply skip if needed
            if skip > 0:
                articles = articles[skip:]
        else:
            # Query with projection to fetch only required fields for better performance
            articles = await db.articles.find(
                query,
                {
                    '_id': 1,
                    'title': 1,
                    'content': 1,
                    'summary': 1,
                    'category': 1,
                    'author': 1,
                    'publishedDate': 1,
                    'image': 1,
                    'tags': 1,
                    'featured': 1,
                    'source': 1,
                    'source_url': 1,
                    'scope': 1,
                    'is_local_source': 1
                }
            ).sort('publishedDate', -1).skip(skip).limit(limit).to_list(limit)
        
        # Helper function to clean word count from content
        def clean_word_count(content):
            if not content:
                return content
            import re
            content = re.sub(r'\s*\(Word count:?\s*\d+\)', '', content, flags=re.IGNORECASE)
            content = re.sub(r'\s*\(Character count:?\s*\d+\)', '', content, flags=re.IGNORECASE)
            content = re.sub(r'\s*Word count:?\s*\d+\.?\s*$', '', content, flags=re.IGNORECASE)
            return content.strip()

        # Import Cheshire priority functions
        from app.news_feed_service import is_priority_cheshire_article, is_secondary_cheshire_article, get_article_priority_location
        
        # Convert ObjectId to string and clean content
        seen_ids = set()
        seen_title_keys = set()
        seen_title_keywords = []
        unique_articles = []

        def get_public_feed_title_keywords(title):
            """Extract title keywords for lightweight public-feed near-duplicate detection."""
            import re
            stop_words = {
                'the', 'a', 'an', 'is', 'are', 'was', 'were', 'for', 'to', 'of', 'in',
                'on', 'at', 'with', 'as', 'by', 'and', 'from', 'this', 'that', 'will',
                'after', 'before', 'over', 'into', 'about', 'expected', 'announce'
            }
            words = str(title or "").lower().split()
            return set(
                w.strip(".,:;!?()[]'\"")
                for w in words
                if len(w.strip(".,:;!?()[]'\"")) > 3 and w.strip(".,:;!?()[]'\"") not in stop_words
            )

        for article in articles:
            article['id'] = str(article['_id'])
            del article['_id']

            # Expose the exact public URL so API consumers do not need to
            # reproduce Cheshire Today's slug-generation rules.
            article_id = str(article.get("id") or "").strip()
            article_slug = _article_slug_from_title(article.get("title"))
            article["articleId"] = article_id
            article["slug"] = article_slug
            article["canonicalUrl"] = (
                f"https://cheshiretoday.co.uk/article/{article_id}/{article_slug}"
            )

            # Normalize scope for frontend consistency
            if article.get('is_local_source') is True:
                article['scope'] = 'cheshire'
            elif not article.get('scope'):
                article['scope'] = 'uk'

            # Normalize misleading category labels:
            # Some national feeds use 'Local News' even when not local to Cheshire.
            if article.get('is_local_source') is not True and article.get('category') == 'Local News' and article.get('scope') != 'cheshire':
                article['category'] = 'UK News'
            
            # Skip duplicate articles by ID
            if article['id'] in seen_ids:
                continue
            seen_ids.add(article['id'])

            # Skip near-duplicate titles in the public feed.
            # This catches same-topic articles from multiple feeds without changing imports/admin.
            title_key = (article.get('title') or '').lower().strip()[:55]
            title_keywords = get_public_feed_title_keywords(article.get('title') or '')
            if title_key and title_key in seen_title_keys:
                continue

            is_similar_title = False
            for prev_keywords in seen_title_keywords:
                if title_keywords and prev_keywords:
                    overlap = len(title_keywords & prev_keywords)
                    similarity = overlap / min(len(title_keywords), len(prev_keywords))
                    if similarity >= 0.50:
                        is_similar_title = True
                        break

            if is_similar_title:
                continue

            if title_key:
                seen_title_keys.add(title_key)
            if title_keywords:
                seen_title_keywords.append(title_keywords)
            
            # Clean word count from content
            if 'content' in article:
                article['content'] = clean_word_count(article['content'])

            
            # Add Cheshire priority flags and normalize live category/location metadata
            title = article.get('title', '')
            content = article.get('content', '')
            summary = article.get('summary', '')

            article['is_priority_cheshire'] = is_priority_cheshire_article(title, content)
            article['is_secondary_cheshire'] = is_secondary_cheshire_article(title, content)

            # Preserve any existing feed-derived location first.
            # Only fall back to title + summary detection when no location exists.
            existing_location = article.get('location') or article.get('priority_location')
            detected_location = get_article_priority_location(title, summary)
            final_location = existing_location or detected_location

            article['priority_location'] = final_location
            if final_location:
                article['location'] = final_location
            else:
                article.pop('location', None)

            # Keep obvious podcast items out of generic UK News
            text_meta = f"{title} {summary}".lower()
            if article.get('category') == 'UK News' and 'podcast' in text_meta:
                if any(k in text_meta for k in ['energy','bill','economy','economic','market','finance','money','tax','mortgage','housing','oil','gas']):
                    article['category'] = 'Business'
                elif any(k in text_meta for k in ['ai','tech','technology','digital']):
                    article['category'] = 'Tech'

            unique_articles.append(article)

        # Enforce requested API limit after force-live prepending, boosting, skip, and dedupe.
        # This keeps /api/articles?limit=N predictable for homepage, admin QA, feeds, and consumers.
        unique_articles = unique_articles[:limit]
        
        # Cache the result for homepage requests
        if not search and skip == 0 and limit == 20 and not category:
            api_cache.set(
                cache_key,
                {"articles": unique_articles, "total": total_count, "skip": skip, "limit": limit, "category": category, "include_archived": include_archived},
            )

        # Backward compatible: default is LIST; only return envelope when requested
        if with_total:
            return {"articles": unique_articles, "total": total_count, "skip": skip, "limit": limit, "category": category, "include_archived": include_archived}
        return unique_articles
    except Exception as e:
        logging.error(f"Error getting articles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# NOTE: This route MUST be defined BEFORE /articles/{article_id} to prevent route matching issues
@api_router.get("/articles/most-read")
async def get_most_read_articles(period: str = "today", limit: int = 5):
    """
    Get the most read articles for a time period.
    
    Args:
        period: "today", "week", or "month"
        limit: Number of articles to return (default 5)
    """
    try:
        # Calculate time window
        now = datetime.now(timezone.utc)
        if period == "today":
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_time = now - timedelta(days=7)
        elif period == "month":
            start_time = now - timedelta(days=30)
        else:
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Aggregate view counts by article
        pipeline = [
            {"$match": {"viewed_at": {"$gte": start_time}}},
            {"$group": {"_id": "$article_id", "views": {"$sum": 1}}},
            {"$sort": {"views": -1}}
        ]
        
        # Resolve ranked view groups until the requested number of public
        # articles has been collected. Hidden or missing records must not
        # consume result slots.
        articles = []
        
        async for vc in db.article_views.aggregate(pipeline):
            article_id = vc["_id"]
            # Try to find by ObjectId first, then by id field
            article = None
            try:
                article = await db.articles.find_one({"_id": ObjectId(article_id)})
            except:
                pass
            
            if not article:
                article = await db.articles.find_one({"id": article_id})
            
            if (
                article
                and article.get("archived") is not True
                and article.get("manual_review_hidden_from_public") is not True
            ):
                articles.append({
                    "id": str(article.get("_id", article.get("id", ""))),
                    "title": article.get("title", ""),
                    "image": article.get("image", ""),
                    "category": article.get("category", ""),
                    "views": vc["views"]
                })
                if len(articles) >= limit:
                    break
        
        return {
            "success": True,
            "period": period,
            "articles": articles
        }
        
    except Exception as e:
        logger.error(f"Error getting most read articles: {str(e)}")
        return {"success": False, "error": str(e), "articles": []}


@api_router.get("/articles/{article_id}")
async def get_article(article_id: str):
    """Get a single article by ID (supports both MongoDB _id and custom id field)
    
    Also searches in archived_articles collection to ensure old shared links still work.
    """
    try:
        # Use the shared lookup helper so the JSON endpoint matches article/share routes.
        article = await _find_article_by_any_id(article_id)
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        # Manual-review articles are hidden from public article detail/API access
        # until they are verified, rewritten, and explicitly restored.
        if article.get("manual_review_hidden_from_public") is True:
            raise HTTPException(status_code=404, detail="Article not found")
        
        original_internal_id = str(article.get('id') or '').strip()
        public_article_id = str(article.get('_id') or original_internal_id or article_id)
        if original_internal_id and original_internal_id != public_article_id:
            article['internal_id'] = original_internal_id
        article['id'] = public_article_id
        if '_id' in article:
            del article['_id']
        if 'created_at' in article:
            del article['created_at']

        # Keep public JSON clean. Admin-only review/rewrite metadata should not
        # be exposed through the public article endpoint.
        for internal_field in [
            "manual_review_hidden_from_public",
            "manual_review_reason",
            "manual_review_created_at",
            "manual_review_resolved_at",
            "manual_review_hits",
            "verification_status",
            "rewrite_status",
        ]:
            article.pop(internal_field, None)
        
        return article
    except HTTPException:
        # Re-raise HTTP exceptions as-is (don't wrap 404 in 500)
        raise
    except Exception as e:
        logging.error(f"Error getting article: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/share/{article_id}")
async def get_article_share_page(article_id: str, request: Request):
    """
    Server-side rendered HTML page for social media sharing.
    This page contains proper Open Graph meta tags for the specific article.
    Social media crawlers will see the article image, title, and description.
    Also searches archived_articles to ensure old shared links work.
    """
    from fastapi.responses import HTMLResponse
    import json
    
    try:
        article = None
        mongo_id = None

        # Search in main articles collection first by Mongo _id, then by internal UUID.
        try:
            mongo_id = ObjectId(article_id)
            article = await db.articles.find_one({'_id': mongo_id})
        except Exception:
            pass

        if not article:
            article = await db.articles.find_one({'id': article_id})

        # If not found, search archived_articles by Mongo _id, then by internal UUID.
        if not article and mongo_id:
            article = await db.archived_articles.find_one({'_id': mongo_id})

        if not article:
            article = await db.archived_articles.find_one({'id': article_id})
        
        if not article:
            # Return default share page if article not found
            return HTMLResponse(content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta http-equiv="refresh" content="0;url=https://cheshiretoday.co.uk/">
                <meta property="og:title" content="Cheshire Today - Local News">
                <meta property="og:image" content="https://cheshiretoday.co.uk/social-share.jpg">
            </head>
            <body>Redirecting...</body>
            </html>
            """)
        
        public_article_id = str(article.get('_id') or article.get('id') or article_id).strip()
        article_slug = _article_slug_from_title(article.get('title') or 'article')
        title = article.get('title', 'Cheshire Today')
        raw_description = article.get('content', '')[:200]
        description = raw_description.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        image = article.get('image', '')
        article_url = f"https://cheshiretoday.co.uk/article/{public_article_id}/{article_slug}"
        share_url = f"https://cheshiretoday.co.uk/api/share/{public_article_id}"
        app_url = article_url

        raw_published = article.get('publishedDate') or article.get('published_at') or article.get('created_at') or ''
        published_iso = raw_published.isoformat() if hasattr(raw_published, 'isoformat') else str(raw_published or '')

        json_ld_script = '<script type="application/ld+json">' + json.dumps({
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": title,
            "description": raw_description or title,
            "url": app_url,
            "mainEntityOfPage": app_url,
            "datePublished": published_iso or None,
            "dateModified": published_iso or None,
            "author": {
                "@type": "Organization",
                "name": article.get('author') or "Cheshire Today"
            },
            "publisher": {
                "@type": "Organization",
                "name": "Cheshire Today",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://cheshiretoday.co.uk/logo.png"
                }
            },
            "image": image or "https://cheshiretoday.co.uk/social-share.jpg"
        }, ensure_ascii=False) + '</script>'
        
        # Use default social share image if no article image
        if not image or len(image) < 10:
            image = 'https://cheshiretoday.co.uk/social-share.jpg'
        
        # Check if request is from a social media crawler (don't redirect them)
        user_agent = request.headers.get('user-agent', '').lower()
        is_crawler = any(bot in user_agent for bot in ['facebookexternalhit', 'twitterbot', 'linkedinbot', 'whatsapp', 'telegrambot', 'slackbot'])
        
        # For crawlers: NO redirect, just meta tags
        # For real users: Show page with link to article
        redirect_meta = '' if is_crawler else f'<meta http-equiv="refresh" content="1;url={article_url}">'
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title} | Cheshire Today</title>
            <meta name="description" content="{description}">
            
            <!-- Open Graph / Facebook -->
            <meta property="og:image" content="{image}">
            <meta property="og:image:url" content="{image}">
            <meta property="og:image:secure_url" content="{image}">
            <meta property="og:image:width" content="1200">
            <meta property="og:image:height" content="630">
            <meta property="og:image:alt" content="{title}">
            <meta property="og:type" content="article">
            <meta property="og:url" content="{share_url}">
            <meta property="og:title" content="{title}">
            <meta property="og:description" content="{description}">
            <meta property="og:site_name" content="Cheshire Today">
            <meta property="fb:app_id" content="1265742728765482">
            
            <!-- Twitter Card -->
            <meta name="twitter:card" content="summary_large_image">
            <meta name="twitter:image" content="{image}">
            <meta name="twitter:url" content="{share_url}">
            <meta name="twitter:title" content="{title}">
            <meta name="twitter:description" content="{description}">
            <meta name="twitter:site" content="@CheshireToday">

    {json_ld_script}
    <link rel="canonical" href="{app_url}">
    <meta property="article:published_time" content="{published_iso}">
    <meta property="article:author" content="{article.get('author','Cheshire Today') if article else ''}">
            
            <!-- Canonical points to share URL so Facebook doesn't follow to homepage -->
            <link rel="canonical" href="{share_url}">
            
            <!-- Redirect real users (not crawlers) -->
            {redirect_meta}
        </head>
        <body style="font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f0f0f0;">
            <div style="text-align: center; padding: 40px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h1 style="color: #047857; margin-bottom: 20px;">Cheshire Today</h1>
                <p style="color: #666; margin-bottom: 20px;">Redirecting to article...</p>
                <a href="{article_url}" style="display: inline-block; background: #047857; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">Read Article</a>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logging.error(f"Error generating share page: {str(e)}")
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta http-equiv="refresh" content="0;url=https://cheshiretoday.co.uk/">
        </head>
        <body>Redirecting...</body>
        </html>
        """)


# =====================================================================================
# SEO PRE-RENDERING FOR SEARCH ENGINES
# =====================================================================================

@api_router.get("/seo/article/{article_id}")
async def get_seo_article_page(article_id: str, request: Request):
    """
    Server-side rendered HTML page optimised for search engine crawlers.
    Returns full article content with proper meta tags + JSON-LD for indexing.
    """
    from fastapi.responses import HTMLResponse
    import json

    try:
        # Search in main articles collection first
        article = None
        try:
            article = await db.articles.find_one({"_id": ObjectId(article_id)}, {"_id": 0})
        except Exception:
            pass

        if not article:
            article = await db.articles.find_one({"id": article_id}, {"_id": 0})

        # If not found, search in archived_articles collection
        if not article:
            try:
                article = await db.archived_articles.find_one({"_id": ObjectId(article_id)}, {"_id": 0})
            except Exception:
                pass

        if not article:
            article = await db.archived_articles.find_one({"id": article_id}, {"_id": 0})

        if not article:
            return HTMLResponse(
                status_code=404,
                content="""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="robots" content="noindex">
<title>Article Not Found | Cheshire Today</title></head>
<body><h1>Article Not Found</h1></body></html>"""
            )

        # Base URL: prefer env for deploys; in local dev you may set PUBLIC_URL=http://localhost:3000
        base_url = (os.environ.get("PUBLIC_URL") or "https://cheshiretoday.co.uk").rstrip("/")

        article_id_str = str(article.get("id") or article.get("_id") or "").strip()
        title = str(article.get("title") or "Cheshire Today Article")
        content = str(article.get("content") or "")
        summary = str(article.get("summary") or "")
        description_src = summary if len(summary.strip()) >= 40 else content
        description = (description_src[:160]).replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;") if description_src else title

        def normalize_social_image_url(raw_image: str) -> str:
            image_url = str(raw_image or "").strip().replace("&amp;", "&")
            if not image_url:
                return f"{base_url}/social-share.jpg"

            lowered = image_url.lower()

            if "i.guim.co.uk" in lowered:
                if re.search(r"([?&])width=\d+", image_url):
                    image_url = re.sub(r"([?&])width=\d+", r"\1width=1200", image_url)
                else:
                    image_url += ("&" if "?" in image_url else "?") + "width=1200"
                image_url = re.sub(r"([?&])quality=\d+", r"\1quality=85", image_url)

            if "ichef.bbci.co.uk" in lowered:
                image_url = re.sub(r"/standard/(240|320|480|624|800)/", "/standard/1024/", image_url)
                image_url = re.sub(r"/news/(240|320|480|624|800)/", "/news/1024/", image_url)

            if "i2-prod.cheshire-live.co.uk" in lowered or "i-prod.cheshire-live.co.uk" in lowered or "/alternates/s" in lowered:
                image_url = re.sub(r"/ALTERNATES/s(615b?|810|1200)/", "/ALTERNATES/s1200/", image_url, flags=re.IGNORECASE)

            return image_url

        image = normalize_social_image_url(article.get("image") or f"{base_url}/social-share.jpg")
        category = str(article.get("category") or "News")
        author = str(article.get("author") or "Cheshire Today")
        published_date = str(article.get("publishedDate") or article.get("created_at") or "")

        canonical_url = f"{base_url}/article/{article_id_str}"

        # Basic content formatting
        formatted_content = content.replace("\n\n", "</p><p>").replace("\n", "<br>")
        if formatted_content and not formatted_content.startswith("<p>"):
            formatted_content = f"<p>{formatted_content}</p>"

        safe_title = title.replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")

        json_ld = {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": title,
            "description": description,
            "image": [image] if image else [],
            "datePublished": published_date,
            "dateModified": published_date,
            "author": {"@type": "Organization", "name": author},
            "publisher": {
                "@type": "Organization",
                "name": "Cheshire Today",
                "logo": {"@type": "ImageObject", "url": f"{base_url}/logo.png"},
            },
            "mainEntityOfPage": {"@type": "WebPage", "@id": canonical_url},
            "articleSection": category,
        }

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{safe_title} | Cheshire Today</title>
  <meta name="description" content="{description}">
  <meta name="author" content="{author}">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">

  <link rel="canonical" href="{canonical_url}">

  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical_url}">
  <meta property="og:title" content="{safe_title}">
  <meta property="og:description" content="{description}">
  <meta property="og:image" content="{image}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:site_name" content="Cheshire Today">
  <meta property="article:published_time" content="{published_date}">
  <meta property="article:section" content="{category}">

  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:url" content="{canonical_url}">
  <meta name="twitter:title" content="{safe_title}">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{image}">
  <meta name="twitter:site" content="@CheshireToday">

  <script type="application/ld+json">{json.dumps(json_ld)}</script>

  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
    h1 {{ color: #1a1a1a; margin-bottom: 10px; }}
    .meta {{ color: #666; font-size: 14px; margin-bottom: 20px; }}
    .content {{ color: #333; }}
    img {{ max-width: 100%; height: auto; border-radius: 8px; margin: 20px 0; }}
    .cta {{ background: #047857; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 20px; }}
  </style>
</head>
<body>
  <article>
    <h1>{safe_title}</h1>
    <div class="meta">
      <span>By {author}</span> |
      <span>{category}</span> |
      <time datetime="{published_date}">{published_date[:10] if published_date else ""}</time>
    </div>
    {f'<img src="{image}" alt="{safe_title}">' if image else ''}
    <div class="content">{formatted_content}</div>
    <a href="{canonical_url}" class="cta">Read Full Article on Cheshire Today</a>
  </article>
</body>
</html>"""

        return HTMLResponse(
            content=html_content,
            headers={"Cache-Control": "public, max-age=3600", "X-Robots-Tag": "index, follow"},
        )

    except Exception as e:
        logging.error(f"Error generating SEO article page: {str(e)}")
        return HTMLResponse(status_code=500, content="""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="robots" content="noindex">
            <title>Error | Cheshire Today</title>
        </head>
        <body><h1>Error loading article</h1></body>
        </html>
        """)


@api_router.get("/article-meta/{article_id}")
async def get_article_meta(article_id: str):
    """Get article metadata for social sharing. Also searches archived articles."""
    try:
        # Use environment variable for base URL (works across all deployment environments)
        # Domain config:
        # PUBLIC_URL = frontend domain (React app)
        # API_PUBLIC_URL = backend domain (serves /api/article/{id} HTML for crawlers)
        public_url = os.environ.get('PUBLIC_URL', 'https://cheshiretoday.co.uk').rstrip('/')
        api_public_url = os.environ.get('API_PUBLIC_URL', public_url).rstrip('/')
        
        # Search in main articles collection first
        article = await db.articles.find_one({"_id": ObjectId(article_id)})
        
        # If not found, search in archived_articles collection
        if not article:
            article = await db.archived_articles.find_one({"_id": ObjectId(article_id)})
        
        if not article:
            return {
                "title": "Cheshire Today - Local News",
                "description": "Stay informed with the latest news from Cheshire",
                "image": "",
                "url": public_url
            }
        
        return {
            "title": article.get('title', 'Cheshire Today Article'),
            "description": article.get('content', '')[:200],
            "image": article.get('image', ''),
            "url": f"{public_url}/article/{article_id}",
            "author": article.get('author', 'Cheshire Today'),
            "publishedDate": article.get('publishedDate', article.get('created_at'))
        }
    except Exception as e:
        logging.error(f"Error fetching article meta: {str(e)}")
        # Use environment variable for base URL (works across all deployment environments)
        public_url = os.environ.get('PUBLIC_URL', 'https://cheshiretoday.co.uk').rstrip('/')
        api_public_url = os.environ.get('API_PUBLIC_URL', public_url).rstrip('/')
        return {
            "title": "Cheshire Today - Local News",
            "description": "Stay informed with the latest news from Cheshire",
            "image": "",
            "url": public_url
        }

@api_router.delete("/articles/{article_id}")
async def delete_article(article_id: str, auth: bool = Depends(get_admin_auth)):
    """Archive an article (moves to archived_articles collection instead of permanent deletion).
    
    This ensures that shared links (e.g., Facebook posts) continue to work even after
    articles are removed from the main collection.
    """
    try:
        article = None
        mongo_id = None
        
        # First try to find by ObjectId (_id)
        try:
            mongo_id = ObjectId(article_id)
            article = await db.articles.find_one({'_id': mongo_id})
        except Exception:
            pass  # Not a valid ObjectId, try custom id field
        
        # Fallback: try to find by custom 'id' field (UUID format)
        if not article:
            article = await db.articles.find_one({'id': article_id})
            if article:
                mongo_id = article['_id']
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Archive the article instead of deleting it permanently
        article['archived_at'] = datetime.now(timezone.utc).isoformat()
        article['archive_reason'] = 'admin_delete'
        
        # Store the original _id as a string for reference, then remove it for insertion
        original_id = article.pop('_id', None)
        
        # Insert into archived_articles collection
        try:
            await db.archived_articles.insert_one(article)
        except Exception as e:
            logger.warning(f"Failed to archive article {article_id}: {e}")
            # Continue with deletion even if archival fails
        
        # Now delete from main collection
        result = await db.articles.delete_one({'_id': mongo_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Article not found")
        
        return {"success": True, "message": "Article archived successfully (links will still work)"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error archiving article: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/subscribe", response_model=SubscribeResponse)
@api_router.post("/newsletter/subscribe", response_model=SubscribeResponse)
async def subscribe_newsletter(request: SubscribeRequest):
    """Create an all-three subscription without mutating existing records."""
    try:
        email = request.email.lower().strip()
        
        # Check if email already exists
        existing = await db.subscribers.find_one({"email": email}, {"_id": 0})
        
        if existing:
            # Existing addresses must use mailbox-verified management flows.
            # Keep the response identical for active and inactive records and do
            # not change subscriber state or preferences from public signup.
            return SubscribeResponse(
                success=True,
                outcome="existing",
                message="Thanks. If this address is eligible, no further action is needed."
            )
        
        # Default preferences
        default_preferences = {
            "categories": ["Local News", "Business", "Finance", "AI & Tech"],
            "frequency": "daily"
        }
        
        now = datetime.now(timezone.utc).isoformat()
        signup_placement = (
            request.signup_placement
            if request.signup_placement in NEWSLETTER_SIGNUP_PLACEMENTS
            else NEWSLETTER_SIGNUP_DEFAULT_PLACEMENT
        )

        # Create a new active all-three subscription with server-owned consent.
        subscriber = {
            "id": str(uuid.uuid4()),
            "newsletter_management_id": str(uuid.uuid4()),
            "newsletter_token_version": 1,
            "email": email,
            "subscribed_at": now,
            "created_at": now,
            "site_update_part1_sent_at": None,
            "site_update_part2_sent_at": None,
            "active": True,
            "preferences": default_preferences,
            "signup_source": "website",
            "subscriber_origin": "organic_website",
            **NEWSLETTER_SIGNUP_PREFERENCES,
            "consent_at": now,
            "consent_version": NEWSLETTER_SIGNUP_CONSENT_VERSION,
            "consent_text": NEWSLETTER_SIGNUP_CONSENT_TEXT,
            "consent_preferences": dict(NEWSLETTER_SIGNUP_PREFERENCES),
            "signup_placement": signup_placement,
        }

        try:
            await db.subscribers.insert_one(subscriber)
        except DuplicateKeyError:
            return SubscribeResponse(
                success=True,
                outcome="existing",
                message="Thanks. If this address is eligible, no further action is needed.",
            )
        
        logger.info(f"New newsletter subscriber: {email}")
        
        # Send welcome email (non-blocking)
        try:
            email_service.send_welcome_email(email)
            logger.info(f"Welcome email sent to: {email}")
        except Exception as email_error:
            logger.error(f"Failed to send welcome email to {email}: {str(email_error)}")
            # Don't fail subscription if email fails
        
        return SubscribeResponse(
            success=True,
            outcome="created",
            message="You're subscribed to Cheshire Today newsletters."
        )
        
    except Exception as e:
        logger.error(f"Error subscribing email: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to subscribe. Please try again.")

# =====================================================================================
# NEWSLETTER PREFERENCES ENDPOINTS
# =====================================================================================

SECURE_NEWSLETTER_MANAGEMENT_UNAVAILABLE = (
    "Secure newsletter management is not yet available."
)
SECURE_NEWSLETTER_TOKEN_INVALID = (
    "This newsletter management link is invalid or has expired."
)
SECURE_NEWSLETTER_TOKEN_WRONG_PURPOSE = (
    "This newsletter management link cannot be used for this action."
)
SECURE_NEWSLETTER_REACTIVATION_REQUIRED = (
    "Please reactivate your subscription before managing email preferences."
)
SECURE_NEWSLETTER_UPDATE_CONFLICT = (
    "Your email preferences could not be updated. Please try again."
)
SECURE_NEWSLETTER_UNSUBSCRIBE_CONFLICT = (
    "Your unsubscribe request could not be processed. Please try again."
)
SECURE_NEWSLETTER_UNSUBSCRIBE_INVALID = (
    "The one-click unsubscribe request is invalid."
)
SECURE_NEWSLETTER_UNSUBSCRIBE_SUCCESS = (
    "Your unsubscribe request has been processed."
)
SECURE_NEWSLETTER_REACTIVATION_CONFLICT = (
    "Your subscription could not be confirmed. Please request a new link."
)
SECURE_NEWSLETTER_REACTIVATION_SUCCESS = (
    "Your subscription preferences have been confirmed."
)
SECURE_NEWSLETTER_MANAGEMENT_503 = {
    503: {
        "description": SECURE_NEWSLETTER_MANAGEMENT_UNAVAILABLE,
    }
}

# Stage 4E3 readiness gate. This is enabled only after the subscriber migration,
# unique index, signing secret, provider adapter and frontend management flow
# have each been reviewed and activated separately.
NEWSLETTER_REQUEST_LINKS_ENABLED = True
# Stage 4E6A challenge-enforcement gate. This remains independently controlled
# from request-link issuance after challenge storage, indexes and the complete
# confirmation flow were reviewed and activated separately.
NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED = True


class _NewsletterOneClickInactiveReplay(Exception):
    """Abort an ineligible inactive one-click transaction without disclosure."""


SECURE_NEWSLETTER_REQUEST_LINK_ACCEPTED = (
    "If the address is eligible, an email with the next step will be sent "
    "shortly."
)
_NEWSLETTER_REQUEST_LINK_PROJECTION = {
    "_id": 0,
    "newsletter_management_id": 1,
    "newsletter_token_version": 1,
    "active": 1,
}
_NEWSLETTER_REQUEST_LINK_EMAIL_DIMENSION = "email"
_NEWSLETTER_REQUEST_LINK_IP_DIMENSION = "ip"
_NEWSLETTER_REQUEST_LINK_PREFERENCES_PURPOSE = "preferences"
_NEWSLETTER_REQUEST_LINK_REACTIVATE_PURPOSE = "reactivate"
_NEWSLETTER_REQUEST_LINK_UNSUBSCRIBE_PURPOSE = "unsubscribe"
_NEWSLETTER_REQUEST_LINK_PREFERENCES_PROFILE = "website_preferences"
_NEWSLETTER_REQUEST_LINK_REACTIVATE_PROFILE = "reactivation"
_NEWSLETTER_REQUEST_LINK_UNSUBSCRIBE_PROFILE = "website_unsubscribe"


class NewsletterPreferencesRequestLinkCollaborators:
    """Injected future orchestration dependencies for the dormant route."""

    def __init__(
        self,
        *,
        rate_limit_repository,
        challenge_repository,
        lookup_subscriber,
        issue_token,
        send_management_email,
        source_ip,
        now,
    ):
        self.rate_limit_repository = rate_limit_repository
        self.challenge_repository = challenge_repository
        self.lookup_subscriber = lookup_subscriber
        self.issue_token = issue_token
        self.send_management_email = send_management_email
        self.source_ip = source_ip
        self.now = now


class NewsletterUnsubscribeRequestLinkCollaborators:
    """Injected future orchestration dependencies for the dormant route."""

    def __init__(
        self,
        *,
        rate_limit_repository,
        challenge_repository,
        lookup_subscriber,
        issue_token,
        send_management_email,
        source_ip,
        now,
    ):
        self.rate_limit_repository = rate_limit_repository
        self.challenge_repository = challenge_repository
        self.lookup_subscriber = lookup_subscriber
        self.issue_token = issue_token
        self.send_management_email = send_management_email
        self.source_ip = source_ip
        self.now = now


class NewsletterReactivationRequestLinkCollaborators:
    """Injected future orchestration dependencies for the dormant route."""

    def __init__(
        self,
        *,
        rate_limit_repository,
        challenge_repository,
        lookup_subscriber,
        issue_token,
        send_management_email,
        source_ip,
        now,
    ):
        self.rate_limit_repository = rate_limit_repository
        self.challenge_repository = challenge_repository
        self.lookup_subscriber = lookup_subscriber
        self.issue_token = issue_token
        self.send_management_email = send_management_email
        self.source_ip = source_ip
        self.now = now


def _create_newsletter_preferences_request_link_collaborators(
    request: Request,
):
    return _create_newsletter_request_link_collaborators(
        request,
        NewsletterPreferencesRequestLinkCollaborators,
    )


def _create_newsletter_unsubscribe_request_link_collaborators(
    request: Request,
):
    return _create_newsletter_request_link_collaborators(
        request,
        NewsletterUnsubscribeRequestLinkCollaborators,
    )


def _create_newsletter_reactivation_request_link_collaborators(
    request: Request,
):
    return _create_newsletter_request_link_collaborators(
        request,
        NewsletterReactivationRequestLinkCollaborators,
    )


class _NewsletterManagementEmailTransport:
    """Narrow adapter over the existing application email-service owner."""

    def __init__(self, service):
        self._service = service

    def send_transactional(self, message):
        return self._service.send_newsletter_management_transactional(message)


def _create_newsletter_rate_limit_repository():
    """Build a lazy repository over the existing application database."""

    return NewsletterRateLimitRepository(db[RATE_LIMIT_COLLECTION_NAME])


def _create_newsletter_preference_challenge_repository():
    """Build a lazy repository over the existing application database."""

    return NewsletterChallengeRepository(db[CHALLENGE_COLLECTION_NAME])


def _create_newsletter_management_email_helper():
    """Build the untracked helper without performing a delivery."""

    return NewsletterManagementEmailHelper(
        transport=_NewsletterManagementEmailTransport(email_service),
        site_origin=CANONICAL_SITE_ORIGIN,
    )


def _newsletter_runtime_collaborator_readiness():
    """Return privacy-safe booleans without environment or network access."""

    return {
        "database_bound": db is not None,
        "transaction_client_bound": client is not None,
        "email_transport_configured": bool(
            email_service.newsletter_management_transport_ready()
        ),
        "request_links_enabled": (
            NEWSLETTER_REQUEST_LINKS_ENABLED is True
        ),
        "challenge_enforcement_enabled": (
            NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED is True
        ),
    }


def _create_newsletter_request_link_collaborators(
    request: Request,
    collaborator_type,
):
    """Create one purpose-neutral set of lazy production collaborators."""

    source_ip = getattr(getattr(request, "client", None), "host", None)
    if not isinstance(source_ip, str) or not source_ip:
        raise RuntimeError("Newsletter request source is unavailable.")

    rate_limit_repository = _create_newsletter_rate_limit_repository()
    challenge_repository = (
        _create_newsletter_preference_challenge_repository()
    )
    token_service = _create_secure_newsletter_token_service()
    email_helper = _create_newsletter_management_email_helper()

    async def lookup_subscriber(normalized_email, projection):
        return await db.subscribers.find_one(
            {"email": normalized_email},
            projection,
        )

    def send_management_email(
        *,
        recipient_email,
        purpose,
        token,
        expires_at,
        now,
    ):
        return email_helper.send(
            NewsletterManagementEmailRequest(
                recipient_email=recipient_email,
                purpose=NewsletterManagementEmailPurpose(purpose),
                token=token,
                expires_at=expires_at,
            ),
            now=now,
        )

    return collaborator_type(
        rate_limit_repository=rate_limit_repository,
        challenge_repository=challenge_repository,
        lookup_subscriber=lookup_subscriber,
        issue_token=token_service.issue_newsletter_token,
        send_management_email=send_management_email,
        source_ip=source_ip,
        now=datetime.now(timezone.utc),
    )


def _valid_newsletter_management_id(value) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        return False
    return parsed.version == 4 and str(parsed) == value


def _normalize_and_hash_newsletter_request(email: str, source_ip: str):
    normalized_email = email.strip().lower()
    return (
        normalized_email,
        hashlib.sha256(normalized_email.encode()).hexdigest(),
        hashlib.sha256(source_ip.encode()).hexdigest(),
    )


async def _run_newsletter_preferences_request_link(
    *,
    email: str,
    http_request: Request,
):
    """Run the future non-enumerating flow through injected collaborators."""

    try:
        collaborators = (
            _create_newsletter_preferences_request_link_collaborators(
                http_request
            )
        )
        current = collaborators.now
        if (
            not isinstance(current, datetime)
            or current.tzinfo is None
            or current.utcoffset() != timedelta(0)
        ):
            return

        normalized_email, email_hash, ip_hash = (
            _normalize_and_hash_newsletter_request(
                email,
                collaborators.source_ip,
            )
        )

        ip_decision = await collaborators.rate_limit_repository.reserve_request(
            dimension=_NEWSLETTER_REQUEST_LINK_IP_DIMENSION,
            subject_hash=ip_hash,
            operation=_NEWSLETTER_REQUEST_LINK_PREFERENCES_PURPOSE,
            now=current,
        )
        if not getattr(ip_decision, "allowed", False):
            return

        email_decision = (
            await collaborators.rate_limit_repository.reserve_request(
                dimension=_NEWSLETTER_REQUEST_LINK_EMAIL_DIMENSION,
                subject_hash=email_hash,
                operation=_NEWSLETTER_REQUEST_LINK_PREFERENCES_PURPOSE,
                now=current,
            )
        )
        if not getattr(email_decision, "allowed", False):
            return

        subscriber = await collaborators.lookup_subscriber(
            normalized_email,
            dict(_NEWSLETTER_REQUEST_LINK_PROJECTION),
        )
        if not isinstance(subscriber, dict):
            return

        management_id = subscriber.get("newsletter_management_id")
        token_version = subscriber.get("newsletter_token_version")
        if not (
            _valid_newsletter_management_id(management_id)
            and _is_valid_newsletter_token_version(token_version)
        ):
            return

        active = subscriber.get("active")
        if active is True:
            purpose = _NEWSLETTER_REQUEST_LINK_PREFERENCES_PURPOSE
            expiry_profile = _NEWSLETTER_REQUEST_LINK_PREFERENCES_PROFILE
        elif active is False:
            purpose = _NEWSLETTER_REQUEST_LINK_REACTIVATE_PURPOSE
            expiry_profile = _NEWSLETTER_REQUEST_LINK_REACTIVATE_PROFILE
        else:
            return

        expires_at = current + timedelta(minutes=30)
        token = collaborators.issue_token(
            subscriber_management_id=management_id,
            purpose=purpose,
            token_version=token_version,
            expiry_profile=expiry_profile,
            now=current,
        )
        if not isinstance(token, str) or not token:
            return

        token_hash = hashlib.sha256(token.encode()).hexdigest()
        challenge_result = await collaborators.challenge_repository.create_pending(
            token_hash=token_hash,
            subscriber_management_id=management_id,
            purpose=purpose,
            issued_at=current,
            expires_at=expires_at,
        )
        if not getattr(challenge_result, "succeeded", False):
            return

        try:
            email_result = collaborators.send_management_email(
                recipient_email=normalized_email,
                purpose=purpose,
                token=token,
                expires_at=expires_at,
                now=current,
            )
        except Exception:
            email_result = None

        if getattr(email_result, "accepted", False):
            await collaborators.challenge_repository.mark_delivered(token_hash)
        else:
            await collaborators.challenge_repository.mark_failed(token_hash)
    except Exception:
        # Public callers receive the same accepted response for every internal
        # outcome, including collaborator and storage failures.
        return


async def _run_newsletter_unsubscribe_request_link(
    *,
    email: str,
    http_request: Request,
):
    """Run the future non-enumerating flow through injected collaborators."""

    try:
        collaborators = (
            _create_newsletter_unsubscribe_request_link_collaborators(
                http_request
            )
        )
        current = collaborators.now
        if (
            not isinstance(current, datetime)
            or current.tzinfo is None
            or current.utcoffset() != timedelta(0)
        ):
            return

        normalized_email, email_hash, ip_hash = (
            _normalize_and_hash_newsletter_request(
                email,
                collaborators.source_ip,
            )
        )

        ip_decision = await collaborators.rate_limit_repository.reserve_request(
            dimension=_NEWSLETTER_REQUEST_LINK_IP_DIMENSION,
            subject_hash=ip_hash,
            operation=_NEWSLETTER_REQUEST_LINK_UNSUBSCRIBE_PURPOSE,
            now=current,
        )
        if not getattr(ip_decision, "allowed", False):
            return

        email_decision = (
            await collaborators.rate_limit_repository.reserve_request(
                dimension=_NEWSLETTER_REQUEST_LINK_EMAIL_DIMENSION,
                subject_hash=email_hash,
                operation=_NEWSLETTER_REQUEST_LINK_UNSUBSCRIBE_PURPOSE,
                now=current,
            )
        )
        if not getattr(email_decision, "allowed", False):
            return

        subscriber = await collaborators.lookup_subscriber(
            normalized_email,
            dict(_NEWSLETTER_REQUEST_LINK_PROJECTION),
        )
        if not isinstance(subscriber, dict):
            return

        management_id = subscriber.get("newsletter_management_id")
        token_version = subscriber.get("newsletter_token_version")
        active = subscriber.get("active")
        if not (
            _valid_newsletter_management_id(management_id)
            and _is_valid_newsletter_token_version(token_version)
            and (active is True or active is False)
        ):
            return

        expires_at = current + timedelta(minutes=30)
        token = collaborators.issue_token(
            subscriber_management_id=management_id,
            purpose=_NEWSLETTER_REQUEST_LINK_UNSUBSCRIBE_PURPOSE,
            token_version=token_version,
            expiry_profile=_NEWSLETTER_REQUEST_LINK_UNSUBSCRIBE_PROFILE,
            now=current,
        )
        if not isinstance(token, str) or not token:
            return

        token_hash = hashlib.sha256(token.encode()).hexdigest()
        challenge_result = await collaborators.challenge_repository.create_pending(
            token_hash=token_hash,
            subscriber_management_id=management_id,
            purpose=_NEWSLETTER_REQUEST_LINK_UNSUBSCRIBE_PURPOSE,
            issued_at=current,
            expires_at=expires_at,
        )
        if not getattr(challenge_result, "succeeded", False):
            return

        try:
            email_result = collaborators.send_management_email(
                recipient_email=normalized_email,
                purpose=_NEWSLETTER_REQUEST_LINK_UNSUBSCRIBE_PURPOSE,
                token=token,
                expires_at=expires_at,
                now=current,
            )
        except Exception:
            email_result = None

        if getattr(email_result, "accepted", False):
            await collaborators.challenge_repository.mark_delivered(token_hash)
        else:
            await collaborators.challenge_repository.mark_failed(token_hash)
    except Exception:
        # Public callers receive the same accepted response for every internal
        # outcome, including collaborator and storage failures.
        return


async def _run_newsletter_reactivation_request_link(
    *,
    email: str,
    http_request: Request,
):
    """Run the future non-enumerating flow through injected collaborators."""

    try:
        collaborators = (
            _create_newsletter_reactivation_request_link_collaborators(
                http_request
            )
        )
        current = collaborators.now
        if (
            not isinstance(current, datetime)
            or current.tzinfo is None
            or current.utcoffset() != timedelta(0)
        ):
            return

        normalized_email, email_hash, ip_hash = (
            _normalize_and_hash_newsletter_request(
                email,
                collaborators.source_ip,
            )
        )

        ip_decision = await collaborators.rate_limit_repository.reserve_request(
            dimension=_NEWSLETTER_REQUEST_LINK_IP_DIMENSION,
            subject_hash=ip_hash,
            operation=_NEWSLETTER_REQUEST_LINK_REACTIVATE_PURPOSE,
            now=current,
        )
        if not getattr(ip_decision, "allowed", False):
            return

        email_decision = (
            await collaborators.rate_limit_repository.reserve_request(
                dimension=_NEWSLETTER_REQUEST_LINK_EMAIL_DIMENSION,
                subject_hash=email_hash,
                operation=_NEWSLETTER_REQUEST_LINK_REACTIVATE_PURPOSE,
                now=current,
            )
        )
        if not getattr(email_decision, "allowed", False):
            return

        subscriber = await collaborators.lookup_subscriber(
            normalized_email,
            dict(_NEWSLETTER_REQUEST_LINK_PROJECTION),
        )
        if not isinstance(subscriber, dict):
            return

        management_id = subscriber.get("newsletter_management_id")
        token_version = subscriber.get("newsletter_token_version")
        if not (
            _valid_newsletter_management_id(management_id)
            and _is_valid_newsletter_token_version(token_version)
            and subscriber.get("active") is False
        ):
            return

        expires_at = current + timedelta(minutes=30)
        token = collaborators.issue_token(
            subscriber_management_id=management_id,
            purpose=_NEWSLETTER_REQUEST_LINK_REACTIVATE_PURPOSE,
            token_version=token_version,
            expiry_profile=_NEWSLETTER_REQUEST_LINK_REACTIVATE_PROFILE,
            now=current,
        )
        if not isinstance(token, str) or not token:
            return

        token_hash = hashlib.sha256(token.encode()).hexdigest()
        challenge_result = await collaborators.challenge_repository.create_pending(
            token_hash=token_hash,
            subscriber_management_id=management_id,
            purpose=_NEWSLETTER_REQUEST_LINK_REACTIVATE_PURPOSE,
            issued_at=current,
            expires_at=expires_at,
        )
        if not getattr(challenge_result, "succeeded", False):
            return

        try:
            email_result = collaborators.send_management_email(
                recipient_email=normalized_email,
                purpose=_NEWSLETTER_REQUEST_LINK_REACTIVATE_PURPOSE,
                token=token,
                expires_at=expires_at,
                now=current,
            )
        except Exception:
            email_result = None

        if getattr(email_result, "accepted", False):
            await collaborators.challenge_repository.mark_delivered(token_hash)
        else:
            await collaborators.challenge_repository.mark_failed(token_hash)
    except Exception:
        # Public callers receive the same accepted response for every internal
        # outcome, including collaborator and storage failures.
        return


def _create_secure_newsletter_token_service():
    try:
        return newsletter_token_service_from_environment()
    except NewsletterTokenConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail=SECURE_NEWSLETTER_MANAGEMENT_UNAVAILABLE,
        ) from exc


def _create_newsletter_preference_transaction_client():
    """Return the existing Motor client only when the gated route is called."""

    return client


def _raise_secure_newsletter_token_error(exc: Exception):
    if isinstance(exc, WrongNewsletterTokenPurposeError):
        raise HTTPException(
            status_code=403,
            detail=SECURE_NEWSLETTER_TOKEN_WRONG_PURPOSE,
        ) from exc
    if isinstance(
        exc,
        (
            ExpiredNewsletterTokenError,
            NewsletterTokenVersionMismatchError,
            InvalidNewsletterTokenError,
        ),
    ):
        raise HTTPException(
            status_code=401,
            detail=SECURE_NEWSLETTER_TOKEN_INVALID,
        ) from exc
    raise exc


def _is_valid_newsletter_token_version(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


async def _get_secure_newsletter_preference_subscriber(token: str):
    token_service = _create_secure_newsletter_token_service()
    try:
        claims = token_service.verify_newsletter_token(
            token,
            expected_purpose=PREFERENCES_PURPOSE,
        )
    except (
        ExpiredNewsletterTokenError,
        WrongNewsletterTokenPurposeError,
        NewsletterTokenVersionMismatchError,
        InvalidNewsletterTokenError,
    ) as exc:
        _raise_secure_newsletter_token_error(exc)

    try:
        subscriber = await db.subscribers.find_one(
            {
                "newsletter_management_id": (
                    claims.subscriber_management_id
                )
            },
            {
                "_id": 0,
                "newsletter_management_id": 1,
                "newsletter_token_version": 1,
                "active": 1,
                "daily_brief": 1,
                "weekly_roundup": 1,
                "breaking_news": 1,
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=SECURE_NEWSLETTER_MANAGEMENT_UNAVAILABLE,
        ) from exc

    if not subscriber:
        raise HTTPException(
            status_code=401,
            detail=SECURE_NEWSLETTER_TOKEN_INVALID,
        )

    stored_version = subscriber.get("newsletter_token_version")
    if (
        not _is_valid_newsletter_token_version(stored_version)
        or stored_version != claims.token_version
    ):
        raise HTTPException(
            status_code=401,
            detail=SECURE_NEWSLETTER_TOKEN_INVALID,
        )

    if subscriber.get("active") is not True:
        raise HTTPException(
            status_code=409,
            detail=SECURE_NEWSLETTER_REACTIVATION_REQUIRED,
        )

    return claims, subscriber


async def _process_secure_newsletter_unsubscribe(
    token: str,
    token_service=None,
    *,
    allow_inactive_replay: bool = False,
):
    if NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED is not True:
        raise HTTPException(
            status_code=503,
            detail=SECURE_NEWSLETTER_MANAGEMENT_UNAVAILABLE,
        )

    if token_service is None:
        token_service = _create_secure_newsletter_token_service()
    try:
        claims = token_service.verify_newsletter_token(
            token,
            expected_purpose=UNSUBSCRIBE_PURPOSE,
        )
    except (
        ExpiredNewsletterTokenError,
        WrongNewsletterTokenPurposeError,
        NewsletterTokenVersionMismatchError,
        InvalidNewsletterTokenError,
    ) as exc:
        _raise_secure_newsletter_token_error(exc)

    subscriber_query = {
        "newsletter_management_id": claims.subscriber_management_id,
    }
    subscriber_projection = {
        "_id": 0,
        "newsletter_management_id": 1,
        "newsletter_token_version": 1,
        "active": 1,
    }
    try:
        subscriber = await db.subscribers.find_one(
            subscriber_query,
            subscriber_projection,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=SECURE_NEWSLETTER_MANAGEMENT_UNAVAILABLE,
        ) from exc

    if not subscriber:
        raise HTTPException(
            status_code=401,
            detail=SECURE_NEWSLETTER_TOKEN_INVALID,
        )

    stored_version = subscriber.get("newsletter_token_version")
    if (
        subscriber.get("newsletter_management_id")
        != claims.subscriber_management_id
        or not _is_valid_newsletter_token_version(stored_version)
        or stored_version != claims.token_version
    ):
        raise HTTPException(
            status_code=401,
            detail=SECURE_NEWSLETTER_TOKEN_INVALID,
        )

    subscriber_active = subscriber.get("active")
    if subscriber_active is not True and subscriber_active is not False:
        raise HTTPException(
            status_code=409,
            detail=SECURE_NEWSLETTER_UNSUBSCRIBE_CONFLICT,
        )

    try:
        token_hash = hash_newsletter_challenge_token(token)
        challenge_repository = (
            _create_newsletter_preference_challenge_repository()
        )
        transaction_client = (
            _create_newsletter_preference_transaction_client()
        )
        session_context = await transaction_client.start_session()
        async with session_context as session:
            async with session.start_transaction():
                current_subscriber = await db.subscribers.find_one(
                    subscriber_query,
                    subscriber_projection,
                    session=session,
                )
                if not current_subscriber:
                    raise HTTPException(
                        status_code=401,
                        detail=SECURE_NEWSLETTER_TOKEN_INVALID,
                    )

                current_version = current_subscriber.get(
                    "newsletter_token_version"
                )
                if (
                    current_subscriber.get("newsletter_management_id")
                    != claims.subscriber_management_id
                    or not _is_valid_newsletter_token_version(current_version)
                    or current_version != claims.token_version
                ):
                    raise HTTPException(
                        status_code=401,
                        detail=SECURE_NEWSLETTER_TOKEN_INVALID,
                    )

                current_active = current_subscriber.get("active")
                if current_active is not True and current_active is not False:
                    raise HTTPException(
                        status_code=409,
                        detail=SECURE_NEWSLETTER_UNSUBSCRIBE_CONFLICT,
                    )

                now = datetime.now(timezone.utc)
                challenge_result = await challenge_repository.consume(
                    token_hash=token_hash,
                    subscriber_management_id=(
                        claims.subscriber_management_id
                    ),
                    expected_purpose=UNSUBSCRIBE_PURPOSE,
                    now=now,
                    session=session,
                )
                if (
                    getattr(challenge_result, "reason", None)
                    is ChallengeResultReason.STORAGE_ERROR
                ):
                    raise RuntimeError(
                        "Newsletter challenge storage is unavailable."
                    )
                if (
                    getattr(challenge_result, "succeeded", None) is not True
                    or getattr(challenge_result, "reason", None)
                    is not ChallengeResultReason.CONSUMED
                ):
                    if allow_inactive_replay and current_active is False:
                        raise _NewsletterOneClickInactiveReplay
                    raise HTTPException(
                        status_code=401,
                        detail=SECURE_NEWSLETTER_TOKEN_INVALID,
                    )

                if current_active is True:
                    result = await db.subscribers.update_one(
                        {
                            "newsletter_management_id": (
                                claims.subscriber_management_id
                            ),
                            "newsletter_token_version": claims.token_version,
                            "active": True,
                        },
                        {
                            "$set": {
                                "active": False,
                                "daily_brief": False,
                                "weekly_roundup": False,
                                "breaking_news": False,
                                "unsubscribed_at": now,
                                "unsubscribe_method": "secure_token",
                            }
                        },
                        session=session,
                    )
                    matched_count = result.matched_count
                    if type(matched_count) is not int or matched_count < 0:
                        raise RuntimeError(
                            "Newsletter subscriber update result is invalid."
                        )
                    if matched_count == 0:
                        raise HTTPException(
                            status_code=409,
                            detail=SECURE_NEWSLETTER_UNSUBSCRIBE_CONFLICT,
                        )
                    if matched_count != 1:
                        raise RuntimeError(
                            "Newsletter subscriber update result is invalid."
                        )
    except _NewsletterOneClickInactiveReplay:
        return NewsletterGenericResponse(
            success=True,
            message=SECURE_NEWSLETTER_UNSUBSCRIBE_SUCCESS,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=SECURE_NEWSLETTER_MANAGEMENT_UNAVAILABLE,
        ) from exc

    return NewsletterGenericResponse(
        success=True,
        message=SECURE_NEWSLETTER_UNSUBSCRIBE_SUCCESS,
    )


async def _process_secure_newsletter_reactivation(
    request: NewsletterReactivationConfirmRequest,
):
    if NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED is not True:
        raise HTTPException(
            status_code=503,
            detail=SECURE_NEWSLETTER_MANAGEMENT_UNAVAILABLE,
        )

    token_service = _create_secure_newsletter_token_service()
    try:
        claims = token_service.verify_newsletter_token(
            request.token,
            expected_purpose=REACTIVATE_PURPOSE,
        )
    except (
        ExpiredNewsletterTokenError,
        WrongNewsletterTokenPurposeError,
        NewsletterTokenVersionMismatchError,
        InvalidNewsletterTokenError,
    ) as exc:
        _raise_secure_newsletter_token_error(exc)

    subscriber_query = {
        "newsletter_management_id": claims.subscriber_management_id,
    }
    subscriber_projection = {
        "_id": 0,
        "newsletter_management_id": 1,
        "newsletter_token_version": 1,
        "active": 1,
    }
    try:
        subscriber = await db.subscribers.find_one(
            subscriber_query,
            subscriber_projection,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=SECURE_NEWSLETTER_MANAGEMENT_UNAVAILABLE,
        ) from exc

    if not subscriber:
        raise HTTPException(
            status_code=401,
            detail=SECURE_NEWSLETTER_TOKEN_INVALID,
        )

    stored_version = subscriber.get("newsletter_token_version")
    if (
        subscriber.get("newsletter_management_id")
        != claims.subscriber_management_id
        or not _is_valid_newsletter_token_version(stored_version)
        or stored_version != claims.token_version
    ):
        raise HTTPException(
            status_code=401,
            detail=SECURE_NEWSLETTER_TOKEN_INVALID,
        )

    if subscriber.get("active") is not False:
        raise HTTPException(
            status_code=409,
            detail=SECURE_NEWSLETTER_REACTIVATION_CONFLICT,
        )

    try:
        token_hash = hash_newsletter_challenge_token(request.token)
        challenge_repository = (
            _create_newsletter_preference_challenge_repository()
        )
        transaction_client = (
            _create_newsletter_preference_transaction_client()
        )
        session_context = await transaction_client.start_session()
        async with session_context as session:
            async with session.start_transaction():
                current_subscriber = await db.subscribers.find_one(
                    subscriber_query,
                    subscriber_projection,
                    session=session,
                )
                if not current_subscriber:
                    raise HTTPException(
                        status_code=401,
                        detail=SECURE_NEWSLETTER_TOKEN_INVALID,
                    )

                current_version = current_subscriber.get(
                    "newsletter_token_version"
                )
                if (
                    current_subscriber.get("newsletter_management_id")
                    != claims.subscriber_management_id
                    or not _is_valid_newsletter_token_version(current_version)
                    or current_version != claims.token_version
                ):
                    raise HTTPException(
                        status_code=401,
                        detail=SECURE_NEWSLETTER_TOKEN_INVALID,
                    )

                if current_subscriber.get("active") is not False:
                    raise HTTPException(
                        status_code=409,
                        detail=SECURE_NEWSLETTER_REACTIVATION_CONFLICT,
                    )

                now = datetime.now(timezone.utc)
                challenge_result = await challenge_repository.consume(
                    token_hash=token_hash,
                    subscriber_management_id=(
                        claims.subscriber_management_id
                    ),
                    expected_purpose=REACTIVATE_PURPOSE,
                    now=now,
                    session=session,
                )
                if (
                    getattr(challenge_result, "reason", None)
                    is ChallengeResultReason.STORAGE_ERROR
                ):
                    raise RuntimeError(
                        "Newsletter challenge storage is unavailable."
                    )
                if (
                    getattr(challenge_result, "succeeded", None) is not True
                    or getattr(challenge_result, "reason", None)
                    is not ChallengeResultReason.CONSUMED
                ):
                    raise HTTPException(
                        status_code=401,
                        detail=SECURE_NEWSLETTER_TOKEN_INVALID,
                    )

                result = await db.subscribers.update_one(
                    {
                        "newsletter_management_id": (
                            claims.subscriber_management_id
                        ),
                        "newsletter_token_version": claims.token_version,
                        "active": False,
                    },
                    {
                        "$set": {
                            "active": True,
                            "daily_brief": request.daily_brief,
                            "weekly_roundup": request.weekly_roundup,
                            "breaking_news": request.breaking_news,
                            "reactivated_at": now,
                            "reactivation_method": "verified_email",
                            "preferences_updated_at": now,
                            "newsletter_token_version": (
                                claims.token_version + 1
                            ),
                        }
                    },
                    session=session,
                )
                matched_count = result.matched_count
                if type(matched_count) is not int or matched_count < 0:
                    raise RuntimeError(
                        "Newsletter subscriber update result is invalid."
                    )
                if matched_count == 0:
                    raise HTTPException(
                        status_code=409,
                        detail=SECURE_NEWSLETTER_REACTIVATION_CONFLICT,
                    )
                if matched_count != 1:
                    raise RuntimeError(
                        "Newsletter subscriber update result is invalid."
                    )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=SECURE_NEWSLETTER_MANAGEMENT_UNAVAILABLE,
        ) from exc

    return NewsletterGenericResponse(
        success=True,
        message=SECURE_NEWSLETTER_REACTIVATION_SUCCESS,
    )


@api_router.post(
    "/newsletter/preferences/verify",
    response_model=NewsletterSecurePreferencesResponse,
    responses=SECURE_NEWSLETTER_MANAGEMENT_503,
)
async def verify_secure_newsletter_preferences(
    request: NewsletterTokenRequest,
):
    if NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED is not True:
        raise HTTPException(
            status_code=503,
            detail=SECURE_NEWSLETTER_MANAGEMENT_UNAVAILABLE,
        )

    claims, subscriber = await _get_secure_newsletter_preference_subscriber(
        request.token
    )
    try:
        token_hash = hash_newsletter_challenge_token(request.token)
        challenge_repository = (
            _create_newsletter_preference_challenge_repository()
        )
        challenge_result = (
            await challenge_repository.read_eligible_preference(
                token_hash=token_hash,
                subscriber_management_id=(
                    claims.subscriber_management_id
                ),
                now=datetime.now(timezone.utc),
            )
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=SECURE_NEWSLETTER_MANAGEMENT_UNAVAILABLE,
        ) from exc

    if (
        getattr(challenge_result, "reason", None)
        is ChallengeResultReason.STORAGE_ERROR
    ):
        raise HTTPException(
            status_code=503,
            detail=SECURE_NEWSLETTER_MANAGEMENT_UNAVAILABLE,
        )
    if (
        getattr(challenge_result, "succeeded", None) is not True
        or getattr(challenge_result, "reason", None)
        is not ChallengeResultReason.ELIGIBLE
    ):
        raise HTTPException(
            status_code=401,
            detail=SECURE_NEWSLETTER_TOKEN_INVALID,
        )

    return NewsletterSecurePreferencesResponse(
        success=True,
        preferences=NewsletterSecurePreferences(
            daily_brief=subscriber.get("daily_brief", True),
            weekly_roundup=subscriber.get("weekly_roundup", False),
            breaking_news=subscriber.get("breaking_news", False),
        ),
    )


@api_router.put(
    "/newsletter/preferences/secure",
    response_model=NewsletterGenericResponse,
    responses=SECURE_NEWSLETTER_MANAGEMENT_503,
)
async def update_secure_newsletter_preferences(
    request: SecureNewsletterPreferencesUpdateRequest,
):
    if NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED is not True:
        raise HTTPException(
            status_code=503,
            detail=SECURE_NEWSLETTER_MANAGEMENT_UNAVAILABLE,
        )

    claims, _ = await _get_secure_newsletter_preference_subscriber(
        request.token
    )
    try:
        token_hash = hash_newsletter_challenge_token(request.token)
        challenge_repository = (
            _create_newsletter_preference_challenge_repository()
        )
        transaction_client = (
            _create_newsletter_preference_transaction_client()
        )
        session_context = await transaction_client.start_session()
        async with session_context as session:
            async with session.start_transaction():
                subscriber = await db.subscribers.find_one(
                    {
                        "newsletter_management_id": (
                            claims.subscriber_management_id
                        )
                    },
                    {
                        "_id": 0,
                        "newsletter_management_id": 1,
                        "newsletter_token_version": 1,
                        "active": 1,
                    },
                    session=session,
                )
                if not subscriber:
                    raise HTTPException(
                        status_code=401,
                        detail=SECURE_NEWSLETTER_TOKEN_INVALID,
                    )

                stored_version = subscriber.get(
                    "newsletter_token_version"
                )
                if (
                    subscriber.get("newsletter_management_id")
                    != claims.subscriber_management_id
                    or not _is_valid_newsletter_token_version(stored_version)
                    or stored_version != claims.token_version
                ):
                    raise HTTPException(
                        status_code=401,
                        detail=SECURE_NEWSLETTER_TOKEN_INVALID,
                    )
                if subscriber.get("active") is not True:
                    raise HTTPException(
                        status_code=409,
                        detail=SECURE_NEWSLETTER_REACTIVATION_REQUIRED,
                    )

                now = datetime.now(timezone.utc)
                challenge_result = await challenge_repository.consume(
                    token_hash=token_hash,
                    subscriber_management_id=(
                        claims.subscriber_management_id
                    ),
                    expected_purpose=PREFERENCES_PURPOSE,
                    now=now,
                    session=session,
                )
                if (
                    getattr(challenge_result, "reason", None)
                    is ChallengeResultReason.STORAGE_ERROR
                ):
                    raise RuntimeError(
                        "Newsletter challenge storage is unavailable."
                    )
                if (
                    getattr(challenge_result, "succeeded", None) is not True
                    or getattr(challenge_result, "reason", None)
                    is not ChallengeResultReason.CONSUMED
                ):
                    raise HTTPException(
                        status_code=401,
                        detail=SECURE_NEWSLETTER_TOKEN_INVALID,
                    )

                result = await db.subscribers.update_one(
                    {
                        "newsletter_management_id": (
                            claims.subscriber_management_id
                        ),
                        "newsletter_token_version": claims.token_version,
                        "active": True,
                    },
                    {
                        "$set": {
                            "daily_brief": request.daily_brief,
                            "weekly_roundup": request.weekly_roundup,
                            "breaking_news": request.breaking_news,
                            "preferences_updated_at": now,
                        }
                    },
                    session=session,
                )
                matched_count = result.matched_count
                if type(matched_count) is not int or matched_count < 0:
                    raise RuntimeError(
                        "Newsletter subscriber update result is invalid."
                    )
                if matched_count == 0:
                    raise HTTPException(
                        status_code=409,
                        detail=SECURE_NEWSLETTER_UPDATE_CONFLICT,
                    )
                if matched_count != 1:
                    raise RuntimeError(
                        "Newsletter subscriber update result is invalid."
                    )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=SECURE_NEWSLETTER_MANAGEMENT_UNAVAILABLE,
        ) from exc

    return NewsletterGenericResponse(
        success=True,
        message="Your email preferences have been updated.",
    )


@api_router.post(
    "/newsletter/preferences/request-link",
    response_model=NewsletterGenericResponse,
    responses=SECURE_NEWSLETTER_MANAGEMENT_503,
)
async def request_secure_newsletter_preferences_link(
    request: NewsletterSecureLinkRequest,
    http_request: Request,
):
    if NEWSLETTER_REQUEST_LINKS_ENABLED is not True:
        raise HTTPException(
            status_code=503,
            detail=SECURE_NEWSLETTER_MANAGEMENT_UNAVAILABLE,
        )

    await _run_newsletter_preferences_request_link(
        email=str(request.email),
        http_request=http_request,
    )
    return JSONResponse(
        status_code=202,
        content={
            "success": True,
            "message": SECURE_NEWSLETTER_REQUEST_LINK_ACCEPTED,
        },
    )


@api_router.post(
    "/newsletter/unsubscribe/confirm",
    response_model=NewsletterGenericResponse,
    responses=SECURE_NEWSLETTER_MANAGEMENT_503,
)
async def confirm_secure_newsletter_unsubscribe(
    request: NewsletterTokenRequest,
):
    if NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED is not True:
        raise HTTPException(
            status_code=503,
            detail=SECURE_NEWSLETTER_MANAGEMENT_UNAVAILABLE,
        )
    return await _process_secure_newsletter_unsubscribe(request.token)


@api_router.post(
    "/newsletter/unsubscribe/one-click",
    response_model=NewsletterGenericResponse,
    responses=SECURE_NEWSLETTER_MANAGEMENT_503,
)
async def one_click_secure_newsletter_unsubscribe(
    request: Request,
    token: Optional[str] = Query(default=None),
):
    if NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED is not True:
        raise HTTPException(
            status_code=503,
            detail=SECURE_NEWSLETTER_MANAGEMENT_UNAVAILABLE,
        )

    token_service = _create_secure_newsletter_token_service()

    if not token or not token.strip() or len(token.strip()) > 4096:
        raise HTTPException(
            status_code=400,
            detail=SECURE_NEWSLETTER_UNSUBSCRIBE_INVALID,
        )

    content_type = request.headers.get("content-type", "").lower()
    if not (
        content_type.startswith("application/x-www-form-urlencoded")
        or content_type.startswith("multipart/form-data")
    ):
        raise HTTPException(
            status_code=400,
            detail=SECURE_NEWSLETTER_UNSUBSCRIBE_INVALID,
        )

    try:
        form = await request.form()
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=SECURE_NEWSLETTER_UNSUBSCRIBE_INVALID,
        ) from exc

    if (
        list(form.multi_items())
        != [("List-Unsubscribe", "One-Click")]
    ):
        raise HTTPException(
            status_code=400,
            detail=SECURE_NEWSLETTER_UNSUBSCRIBE_INVALID,
        )

    return await _process_secure_newsletter_unsubscribe(
        token.strip(),
        token_service=token_service,
        allow_inactive_replay=True,
    )


@api_router.post(
    "/newsletter/unsubscribe/request-link",
    response_model=NewsletterGenericResponse,
    responses=SECURE_NEWSLETTER_MANAGEMENT_503,
)
async def request_secure_newsletter_unsubscribe_link(
    request: NewsletterSecureLinkRequest,
    http_request: Request,
):
    if NEWSLETTER_REQUEST_LINKS_ENABLED is not True:
        raise HTTPException(
            status_code=503,
            detail=SECURE_NEWSLETTER_MANAGEMENT_UNAVAILABLE,
        )

    await _run_newsletter_unsubscribe_request_link(
        email=str(request.email),
        http_request=http_request,
    )
    return JSONResponse(
        status_code=202,
        content={
            "success": True,
            "message": SECURE_NEWSLETTER_REQUEST_LINK_ACCEPTED,
        },
    )


@api_router.post(
    "/newsletter/reactivate/request-link",
    response_model=NewsletterGenericResponse,
    responses=SECURE_NEWSLETTER_MANAGEMENT_503,
)
async def request_secure_newsletter_reactivation_link(
    request: NewsletterSecureLinkRequest,
    http_request: Request,
):
    if NEWSLETTER_REQUEST_LINKS_ENABLED is not True:
        raise HTTPException(
            status_code=503,
            detail=SECURE_NEWSLETTER_MANAGEMENT_UNAVAILABLE,
        )

    await _run_newsletter_reactivation_request_link(
        email=str(request.email),
        http_request=http_request,
    )
    return JSONResponse(
        status_code=202,
        content={
            "success": True,
            "message": SECURE_NEWSLETTER_REQUEST_LINK_ACCEPTED,
        },
    )


@api_router.post(
    "/newsletter/reactivate/confirm",
    response_model=NewsletterGenericResponse,
    responses=SECURE_NEWSLETTER_MANAGEMENT_503,
)
async def confirm_secure_newsletter_reactivation(
    request: NewsletterReactivationConfirmRequest,
):
    if NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED is not True:
        raise HTTPException(
            status_code=503,
            detail=SECURE_NEWSLETTER_MANAGEMENT_UNAVAILABLE,
        )
    return await _process_secure_newsletter_reactivation(request)


@api_router.get("/newsletter/categories")
async def get_available_categories():
    """Get available newsletter subscription options (January 2026 update)"""
    return {
        "subscription_types": [
            {
                "id": "daily_brief",
                "name": "The Daily Brief",
                "description": "Top Cheshire stories on newsletter mornings",
                "frequency": "Daily",
                "default": True
            },
            {
                "id": "weekly_roundup",
                "name": "The Weekly Roundup",
                "description": "Curated digest of the week's best content",
                "frequency": "Every Sunday morning",
                "default": False
            },
            {
                "id": "breaking_news",
                "name": "Breaking News Alerts",
                "description": "High-priority notifications for major incidents only",
                "frequency": "As needed (rare)",
                "default": False
            }
        ],
        # Legacy categories for backwards compatibility
        "categories": [
            {"id": "Local News", "name": "Local News", "description": "Cheshire & surrounding areas"},
            {"id": "UK News", "name": "UK News", "description": "National public-interest and policy coverage"},
            {"id": "Business", "name": "Business", "description": "Business & economic intelligence"},
            {"id": "Finance", "name": "Finance", "description": "Personal finance, housing and money"},
            {"id": "Tax", "name": "Tax", "description": "Tax, HMRC and council-tax coverage"},
            {"id": "AI & Tech", "name": "AI & Tech", "description": "Artificial intelligence & technology"}
        ]
    }


# =====================================================================================
# COMMENTS SYSTEM ENDPOINTS
# =====================================================================================

@api_router.post("/comments/register")
async def register_commenter(request: CommentUserRegister):
    """Register a new commenter - sends verification code to email"""
    try:
        email = request.email.lower().strip()
        name = request.name.strip()
        
        if len(name) < 2:
            raise HTTPException(status_code=400, detail="Name must be at least 2 characters")
        
        # Generate 6-digit verification code
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Store code with expiry (10 minutes)
        email_verification_codes[email] = {
            "code": code,
            "name": name,
            "expires": datetime.now(timezone.utc) + timedelta(minutes=10)
        }
        
        # Send verification email
        try:
            email_service.send_verification_code(email, name, code)
            logger.info(f"Verification code sent to: {email}")
        except Exception as email_error:
            logger.error(f"Failed to send verification code to {email}: {str(email_error)}")
            # For development, log the code
            logger.info(f"DEV: Verification code for {email}: {code}")
        
        return {
            "success": True,
            "message": f"Verification code sent to {email}. Please check your inbox."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering commenter: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send verification code")

@api_router.post("/comments/verify")
async def verify_commenter(request: CommentUserLogin):
    """Verify email and create/login commenter"""
    try:
        email = request.email.lower().strip()
        code = request.code.strip()
        
        # Check verification code
        stored = email_verification_codes.get(email)
        if not stored:
            raise HTTPException(status_code=400, detail="No verification code found. Please request a new one.")
        
        if datetime.now(timezone.utc) > stored["expires"]:
            del email_verification_codes[email]
            raise HTTPException(status_code=400, detail="Verification code expired. Please request a new one.")
        
        if stored["code"] != code:
            raise HTTPException(status_code=400, detail="Invalid verification code")
        
        # Code verified - create or update user
        name = stored["name"]
        del email_verification_codes[email]  # Remove used code
        
        # Check if user exists
        existing_user = await db.comment_users.find_one({"email": email})
        
        if existing_user:
            # Update last login
            await db.comment_users.update_one(
                {"email": email},
                {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
            )
            user_id = existing_user["id"]
        else:
            # Create new user
            user_id = str(uuid.uuid4())
            user = {
                "id": user_id,
                "email": email,
                "name": name,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_login": datetime.now(timezone.utc).isoformat()
            }
            await db.comment_users.insert_one(user)
            logger.info(f"New commenter registered: {email}")
        
        # Generate session token
        token = secrets.token_urlsafe(32)
        token_expiry = datetime.now(timezone.utc) + timedelta(days=30)
        
        # Store token
        await db.comment_sessions.insert_one({
            "token": token,
            "user_id": user_id,
            "email": email,
            "name": name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": token_expiry.isoformat()
        })
        
        return {
            "success": True,
            "token": token,
            "user": {
                "id": user_id,
                "name": name,
                "email": email
            },
            "message": "Email verified successfully!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying commenter: {str(e)}")
        raise HTTPException(status_code=500, detail="Verification failed")

async def get_comment_user(authorization: Optional[str] = Header(None)):
    """Get current comment user from token"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization[7:]
    session = await db.comment_sessions.find_one({"token": token})
    
    if not session:
        return None
    
    # Check expiry
    expires = datetime.fromisoformat(session["expires_at"].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expires:
        await db.comment_sessions.delete_one({"token": token})
        return None
    
    return {
        "user_id": session["user_id"],
        "email": session["email"],
        "name": session["name"]
    }

@api_router.get("/comments/me")
async def get_current_commenter(authorization: Optional[str] = Header(None)):
    """Get current logged-in commenter info"""
    user = await get_comment_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not logged in")
    return {"success": True, "user": user}

@api_router.post("/comments")
async def create_comment(request: CommentCreate, authorization: Optional[str] = Header(None)):
    """Create a new comment on an article"""
    try:
        user = await get_comment_user(authorization)
        if not user:
            raise HTTPException(status_code=401, detail="Please login to comment")
        
        content = request.content.strip()
        if len(content) < 3:
            raise HTTPException(status_code=400, detail="Comment is too short")
        if len(content) > 2000:
            raise HTTPException(status_code=400, detail="Comment is too long (max 2000 characters)")
        
        # Verify article exists
        article = await db.articles.find_one({"id": request.article_id})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Create comment
        comment_id = str(uuid.uuid4())
        comment = {
            "id": comment_id,
            "article_id": request.article_id,
            "user_id": user["user_id"],
            "user_name": user["name"],
            "content": content,
            "parent_id": request.parent_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "likes": 0,
            "status": "approved"  # Auto-approve for now
        }
        
        await db.comments.insert_one(comment)
        logger.info(f"New comment on article {request.article_id} by {user['email']}")
        
        return {
            "success": True,
            "message": "Comment posted!",
            "comment_id": comment_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating comment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to post comment")

@api_router.get("/comments/article/{article_id}")
async def get_article_comments(article_id: str, skip: int = 0, limit: int = 50):
    """Get comments for an article"""
    try:
        # Get top-level comments first
        comments = await db.comments.find(
            {"article_id": article_id, "parent_id": None, "status": "approved"},
            {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        # Get replies for each comment
        for comment in comments:
            replies = await db.comments.find(
                {"parent_id": comment["id"], "status": "approved"},
                {"_id": 0}
            ).sort("created_at", 1).to_list(100)
            comment["replies"] = replies
        
        total = await db.comments.count_documents(
            {"article_id": article_id, "parent_id": None, "status": "approved"}
        )
        
        return {
            "success": True,
            "comments": comments,
            "total": total
        }
        
    except Exception as e:
        logger.error(f"Error getting comments: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load comments")

@api_router.post("/comments/{comment_id}/like")
async def like_comment(comment_id: str, authorization: Optional[str] = Header(None)):
    """Like a comment"""
    try:
        user = await get_comment_user(authorization)
        if not user:
            raise HTTPException(status_code=401, detail="Please login to like comments")
        
        # Check if already liked
        existing_like = await db.comment_likes.find_one({
            "comment_id": comment_id,
            "user_id": user["user_id"]
        })
        
        if existing_like:
            # Unlike
            await db.comment_likes.delete_one({
                "comment_id": comment_id,
                "user_id": user["user_id"]
            })
            await db.comments.update_one(
                {"id": comment_id},
                {"$inc": {"likes": -1}}
            )
            return {"success": True, "action": "unliked"}
        else:
            # Like
            await db.comment_likes.insert_one({
                "comment_id": comment_id,
                "user_id": user["user_id"],
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            await db.comments.update_one(
                {"id": comment_id},
                {"$inc": {"likes": 1}}
            )
            return {"success": True, "action": "liked"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error liking comment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to like comment")

@api_router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: str, authorization: Optional[str] = Header(None)):
    """Delete own comment"""
    try:
        user = await get_comment_user(authorization)
        if not user:
            raise HTTPException(status_code=401, detail="Please login")
        
        comment = await db.comments.find_one({"id": comment_id})
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        if comment["user_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Cannot delete others' comments")
        
        await db.comments.delete_one({"id": comment_id})
        # Also delete replies
        await db.comments.delete_many({"parent_id": comment_id})
        
        return {"success": True, "message": "Comment deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting comment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete comment")

@api_router.post("/comments/logout")
async def logout_commenter(authorization: Optional[str] = Header(None)):
    """Logout commenter - invalidate token"""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        await db.comment_sessions.delete_one({"token": token})
    return {"success": True, "message": "Logged out"}

# ==================== ADMIN ENDPOINTS ====================

@api_router.get("/admin/stats")
async def get_admin_stats(authorized: bool = Depends(get_admin_auth)):
    """Get dashboard statistics. Requires admin authentication."""
    try:
        article_count = await db.articles.count_documents({})
        subscriber_count = await db.subscribers.count_documents({})
        
        # Get articles by category
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        categories = await db.articles.aggregate(pipeline).to_list(1000)
        
        # Get latest article date
        latest_article = await db.articles.find_one(
            {}, {"publishedDate": 1}, sort=[("publishedDate", -1)]
        )
        
        return {
            "articles": {
                "total": article_count,
                "by_category": {cat["_id"]: cat["count"] for cat in categories if cat["_id"]}
            },
            "subscribers": {
                "total": subscriber_count
            },
            "latest_article_date": latest_article.get("publishedDate") if latest_article else None
        }
    except Exception as e:
        logger.error(f"Error getting admin stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/admin/normalize-published-dates")
async def normalize_published_dates(authorized: bool = Depends(get_admin_auth)):
    """
    One-time admin endpoint to normalize publishedDate to datetime objects
    across both articles and archived_articles collections.
    """
    try:
        results = {
            "articles_updated": 0,
            "articles_skipped": 0,
            "archived_updated": 0,
            "archived_skipped": 0,
        }

        def normalize_value(v):
            if isinstance(v, datetime):
                return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
            if not v:
                return None
            try:
                dt = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except Exception:
                return None

        articles = await db.articles.find({}, {"_id": 1, "publishedDate": 1, "published_date": 1}).to_list(10000)
        for article in articles:
            normalized = normalize_value(article.get("publishedDate")) or normalize_value(article.get("published_date"))
            if normalized is None:
                results["articles_skipped"] += 1
                continue
            await db.articles.update_one({"_id": article["_id"]}, {"$set": {"publishedDate": normalized}})
            results["articles_updated"] += 1

        archived_articles = await db.archived_articles.find({}, {"_id": 1, "publishedDate": 1, "published_date": 1}).to_list(10000)
        for article in archived_articles:
            normalized = normalize_value(article.get("publishedDate")) or normalize_value(article.get("published_date"))
            if normalized is None:
                results["archived_skipped"] += 1
                continue
            await db.archived_articles.update_one({"_id": article["_id"]}, {"$set": {"publishedDate": normalized}})
            results["archived_updated"] += 1

        logger.info(f"Published date normalization completed: {results}")
        return {"success": True, **results}
    except Exception as e:
        logger.error(f"Error normalizing published dates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/admin/backfill-locations")
async def backfill_article_locations(authorized: bool = Depends(get_admin_auth)):
    """
    Backfill location field for all existing articles.
    This one-time admin endpoint updates all articles in both 'articles' and 'archived_articles' 
    collections with the correct location tag based on their title/content AND source.
    """
    try:
        from app.news_feed_service import get_article_priority_location
        
        # Source-based location mapping - articles from these sources get tagged
        SOURCE_LOCATIONS = {
            'Warrington Guardian': 'warrington',
            # Cheshire Live articles are tagged by content, not source (since it covers all of Cheshire)
        }
        
        results = {
            "articles_updated": 0,
            "articles_skipped": 0,
            "archived_updated": 0,
            "archived_skipped": 0,
            "location_counts": {}
        }
        
        async def process_article(article, collection):
            """Process a single article and return the location if found"""
            title = article.get('title', '')
            content = article.get('content', '')
            source = article.get('source', '')
            
            # First try content-based detection
            location = get_article_priority_location(title, content)
            
            # If no location found from content, check source
            if not location:
                location = SOURCE_LOCATIONS.get(source)
            
            return location
        
        # Process main articles collection
        articles = await db.articles.find({}).to_list(10000)
        for article in articles:
            location = await process_article(article, 'articles')
            
            if location:
                # Update the article with the location field
                await db.articles.update_one(
                    {"_id": article['_id']},
                    {"$set": {"location": location}}
                )
                results["articles_updated"] += 1
                results["location_counts"][location] = results["location_counts"].get(location, 0) + 1
            else:
                results["articles_skipped"] += 1
        
        # Process archived articles collection
        archived_articles = await db.archived_articles.find({}).to_list(10000)
        for article in archived_articles:
            location = await process_article(article, 'archived_articles')
            
            if location:
                await db.archived_articles.update_one(
                    {"_id": article['_id']},
                    {"$set": {"location": location}}
                )
                results["archived_updated"] += 1
                results["location_counts"][location] = results["location_counts"].get(location, 0) + 1
            else:
                results["archived_skipped"] += 1
        
        logger.info(f"Location backfill completed: {results}")
        
        return {
            "success": True,
            "message": "Location backfill completed successfully",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in backfill_article_locations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/admin/subscribers")
async def get_subscribers(authorized: bool = Depends(get_admin_auth)):
    """Get all subscribers for admin dashboard. Requires admin authentication."""
    try:
        subscribers = await db.subscribers.find({}, {"_id": 0}).to_list(1000)
        return {"subscribers": subscribers, "total": len(subscribers)}
    except Exception as e:
        logger.error(f"Error getting subscribers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post(
    "/admin/subscribers/{newsletter_management_id}/unsubscribe"
)
async def admin_unsubscribe_subscriber(
    newsletter_management_id: str,
    authorized: bool = Depends(get_admin_auth),
):
    """Soft-unsubscribe one subscriber while preserving lifecycle history."""
    if not _valid_newsletter_management_id(newsletter_management_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid subscriber management ID.",
        )

    try:
        subscriber = await db.subscribers.find_one(
            {"newsletter_management_id": newsletter_management_id},
            {
                "_id": 0,
                "newsletter_management_id": 1,
                "active": 1,
            },
        )
        if not subscriber:
            raise HTTPException(
                status_code=404,
                detail="Subscriber not found.",
            )

        if subscriber.get("active") is not False:
            result = await db.subscribers.update_one(
                {"newsletter_management_id": newsletter_management_id},
                {
                    "$set": {
                        "active": False,
                        "daily_brief": False,
                        "weekly_roundup": False,
                        "breaking_news": False,
                        "unsubscribed_at": datetime.now(
                            timezone.utc
                        ).isoformat(),
                        "unsubscribe_method": "admin",
                    }
                },
            )
            if (
                type(getattr(result, "matched_count", None)) is not int
                or result.matched_count != 1
            ):
                raise RuntimeError(
                    "Subscriber lifecycle update did not match one record."
                )

        return {
            "success": True,
            "newsletter_management_id": newsletter_management_id,
            "active": False,
            "message": "Subscriber unsubscribed.",
        }
    except HTTPException:
        raise
    except Exception:
        logger.error("Admin subscriber unsubscribe failed.")
        raise HTTPException(
            status_code=503,
            detail="Could not unsubscribe subscriber.",
        )


@api_router.get("/admin/subscribers/cold-report")
async def get_cold_subscriber_report(
    days: int = 30,
    recent_days: int = 21,
    sample_limit: int = 50,
    authorized: bool = Depends(get_admin_auth)
):
    """
    Dry-run cold subscriber report.

    Read-only. Does not deactivate or delete anyone.

    A cold candidate is:
    - active or active missing
    - Daily Brief enabled or missing
    - deliverable email format
    - not organic/website priority
    - not recently subscribed
    - has no recorded opens/clicks in the tracking window
    """
    try:
        safe_days = max(7, min(int(days), 180))
        safe_recent_days = max(1, min(int(recent_days), 90))
        safe_sample_limit = max(0, min(int(sample_limit), 250))

        now = datetime.now(timezone.utc)
        engagement_cutoff = now - timedelta(days=safe_days)
        recent_cutoff = now - timedelta(days=safe_recent_days)

        subscribers = await db.subscribers.find(
            {
                "$and": [
                    {"$or": [{"active": True}, {"active": {"$exists": False}}]},
                    {"$or": [{"daily_brief": {"$ne": False}}, {"daily_brief": {"$exists": False}}]},
                ]
            },
            {
                "_id": 0,
                "email": 1,
                "active": 1,
                "daily_brief": 1,
                "weekly_roundup": 1,
                "subscribed_at": 1,
                "created_at": 1,
                "signup_source": 1,
                "subscriber_origin": 1,
                "priority_daily_brief": 1,
            }
        ).to_list(50000)

        analytics_rows = await db.email_analytics.find(
            {"$or": [
                {"last_opened": {"$gte": engagement_cutoff}},
                {"last_clicked": {"$gte": engagement_cutoff}},
                {"created_at": {"$gte": engagement_cutoff}},
            ]},
            {"_id": 0, "tracking_id": 1, "opens": 1, "clicks": 1, "last_opened": 1, "last_clicked": 1}
        ).to_list(100000)

        engaged_hashes = set()
        tracked_hashes = set()

        for row in analytics_rows:
            tracking_value = str(row.get("tracking_id") or "")
            suffix = tracking_value.rsplit("_", 1)[-1]
            if len(suffix) == 8:
                tracked_hashes.add(suffix)
                if ((row.get("opens") or 0) > 0) or ((row.get("clicks") or 0) > 0):
                    engaged_hashes.add(suffix)

        seen_emails = set()
        total_active_daily = 0
        invalid_excluded = 0
        protected_excluded = 0
        recent_excluded = 0
        tracked_no_engagement = 0
        no_tracking_seen = 0
        cold_candidates = []

        protected_domains = {
            "cheshiretoday.co.uk",
        }

        def parse_dt(value):
            if not value:
                return None
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    return value.replace(tzinfo=timezone.utc)
                return value
            try:
                return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except Exception:
                return None

        for sub in subscribers:
            raw_email = sub.get("email") or ""
            email_norm = raw_email.strip().lower()
            if not email_norm or email_norm in seen_emails:
                continue
            seen_emails.add(email_norm)
            total_active_daily += 1

            if not is_deliverable_newsletter_email(email_norm):
                invalid_excluded += 1
                continue

            domain = email_norm.rsplit("@", 1)[-1] if "@" in email_norm else ""
            is_protected = (
                sub.get("priority_daily_brief") is True
                or sub.get("signup_source") == "website"
                or sub.get("subscriber_origin") == "organic_website"
                or domain in protected_domains
            )
            if is_protected:
                protected_excluded += 1
                continue

            sub_dt = parse_dt(sub.get("subscribed_at") or sub.get("created_at"))
            if sub_dt and sub_dt >= recent_cutoff:
                recent_excluded += 1
                continue

            email_hash = hashlib.sha256(email_norm.encode()).hexdigest()[:8]

            if email_hash in engaged_hashes:
                continue

            if email_hash in tracked_hashes:
                tracked_no_engagement += 1
                reason = f"No opens or clicks recorded in last {safe_days} days"
            else:
                no_tracking_seen += 1
                reason = f"No tracking record seen in last {safe_days} days"

            if len(cold_candidates) < safe_sample_limit:
                cold_candidates.append({
                    "email": raw_email,
                    "reason": reason,
                    "subscribed_at": sub.get("subscribed_at"),
                    "signup_source": sub.get("signup_source"),
                    "subscriber_origin": sub.get("subscriber_origin"),
                    "weekly_roundup": sub.get("weekly_roundup"),
                })

        return {
            "success": True,
            "dry_run": True,
            "period_days": safe_days,
            "recent_subscriber_exclusion_days": safe_recent_days,
            "summary": {
                "active_daily_unique": total_active_daily,
                "invalid_excluded": invalid_excluded,
                "protected_or_organic_excluded": protected_excluded,
                "recent_subscribers_excluded": recent_excluded,
                "engaged_hashes": len(engaged_hashes),
                "tracked_hashes": len(tracked_hashes),
                "cold_candidates_total": tracked_no_engagement + no_tracking_seen,
                "cold_candidates_with_tracking_but_no_engagement": tracked_no_engagement,
                "cold_candidates_with_no_recent_tracking_seen": no_tracking_seen,
            },
            "sample": cold_candidates,
            "next_step": "Review this dry-run report before adding any deactivate endpoint. Do not hard-delete subscribers."
        }

    except Exception as e:
        logger.error(f"Error building cold subscriber report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/admin/subscribers/{email}")
async def delete_subscriber(email: str, authorized: bool = Depends(get_admin_auth)):
    """Delete a subscriber by email. Requires admin authentication."""
    try:
        result = await db.subscribers.delete_one({"email": email})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Subscriber not found")
        return {"success": True, "message": f"Subscriber {email} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting subscriber: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/admin/social-assets/facebook/local-news/{mongo_id}")
async def get_admin_facebook_local_news_social_asset(
    mongo_id: str,
    authorized: bool = Depends(get_admin_auth),
):
    """Compose one active Local News Facebook SVG without persisting output."""
    if not ObjectId.is_valid(mongo_id):
        raise HTTPException(status_code=400, detail="Article ID is invalid")

    try:
        article = await db.articles.find_one(
            {
                "_id": ObjectId(mongo_id),
                "archived": {"$ne": True},
                "manual_review_hidden_from_public": {"$ne": True},
            },
            {"_id": 1, "title": 1, "category": 1, "image": 1},
        )
        if (
            not article
            or article.get("archived") is True
            or article.get("manual_review_hidden_from_public") is True
        ):
            raise HTTPException(status_code=404, detail="Article not found")
        if article.get("category") != "Local News":
            raise HTTPException(
                status_code=400,
                detail="Only Local News articles are supported",
            )

        svg = compose_facebook_local_news_svg(
            {
                "mongo_id": str(article["_id"]),
                "title": article.get("title"),
                "category": article.get("category"),
                "image": article.get("image"),
            }
        )
        filename = f"cheshire-today-{mongo_id.lower()}-facebook-local-news.svg"
        return Response(
            content=svg,
            media_type="image/svg+xml",
            headers={
                "Cache-Control": "no-store",
                "Content-Disposition": f'inline; filename="{filename}"',
            },
        )
    except HTTPException:
        raise
    except (
        SocialAssetImageURLValidationError,
        SocialAssetImageFetchError,
        SocialAssetImageContentError,
        SocialAssetArticleValidationError,
    ) as exc:
        logger.warning(
            "Admin Facebook social asset rejected article_id=%s error=%s",
            mongo_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=422,
            detail="Article image is unavailable or unusable",
        ) from None
    except SocialAssetTemplateValidationError as exc:
        logger.error(
            "Admin Facebook social asset failed article_id=%s error=%s",
            mongo_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail="Social asset could not be generated",
        ) from None
    except Exception as exc:
        logger.error(
            "Admin Facebook social asset failed article_id=%s error=%s",
            mongo_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail="Social asset could not be generated",
        ) from None


@api_router.get("/admin/social-assets/facebook/newsletter")
async def get_admin_facebook_newsletter_social_asset(
    authorized: bool = Depends(get_admin_auth),
):
    """Compose the deterministic Newsletter Facebook SVG without persistence."""
    try:
        svg = compose_facebook_newsletter_svg()
        return Response(
            content=svg,
            media_type="image/svg+xml",
            headers={
                "Cache-Control": "no-store",
                "Content-Disposition": 'inline; filename="cheshire-today-newsletter-facebook.svg"',
            },
        )
    except SocialAssetTemplateValidationError as exc:
        logger.error(
            "Admin Facebook Newsletter social asset failed error=%s",
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail="Social asset could not be generated",
        ) from None
    except Exception as exc:
        logger.error(
            "Admin Facebook Newsletter social asset failed error=%s",
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail="Social asset could not be generated",
        ) from None


class FacebookQuoteGraphicRequest(BaseModel):
    model_config = {"extra": "forbid"}
    quote: str = Field(min_length=1, max_length=240)
    attribution: str = Field(min_length=1, max_length=80)


class FacebookPollGraphicRequest(BaseModel):
    model_config = {"extra": "forbid"}
    question: str = Field(min_length=1, max_length=140)
    option_a: str = Field(min_length=1, max_length=48)
    option_b: str = Field(min_length=1, max_length=48)


async def _get_facebook_graphic_article(mongo_id: str):
    if not ObjectId.is_valid(mongo_id):
        raise HTTPException(status_code=400, detail="Article ID is invalid")
    article = await db.articles.find_one(
        {
            "_id": ObjectId(mongo_id),
            "archived": {"$ne": True},
            "manual_review_hidden_from_public": {"$ne": True},
        },
        {"_id": 1, "title": 1, "category": 1, "image": 1},
    )
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return {
        "mongo_id": str(article["_id"]),
        "title": article.get("title"),
        "category": article.get("category"),
        "image": article.get("image"),
    }


def _facebook_graphic_response(svg: bytes, graphic_type: str, mongo_id: str):
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": (
                f'inline; filename="cheshire-today-{mongo_id.lower()}-facebook-{graphic_type}.svg"'
            ),
        },
    )


def _raise_facebook_graphic_error(exc: Exception, mongo_id: str):
    error_name = type(exc).__name__
    if isinstance(
        exc,
        (
            SocialAssetImageURLValidationError,
            SocialAssetImageFetchError,
            SocialAssetImageContentError,
        ),
    ):
        logger.warning(
            "Admin Facebook graphic rejected article_id=%s error=%s",
            mongo_id,
            error_name,
        )
        raise HTTPException(status_code=422, detail="Article image is unavailable or unusable") from None
    if isinstance(exc, SocialAssetArticleValidationError):
        logger.warning(
            "Admin Facebook graphic rejected article_id=%s error=%s",
            mongo_id,
            error_name,
        )
        raise HTTPException(status_code=400, detail="Graphic input is unsupported") from None
    logger.error(
        "Admin Facebook graphic failed article_id=%s error=%s",
        mongo_id,
        error_name,
    )
    raise HTTPException(status_code=500, detail="Social asset could not be generated") from None


@api_router.get("/admin/social-assets/facebook/article/{graphic_type}/{mongo_id}")
async def get_admin_facebook_article_graphic(
    graphic_type: str,
    mongo_id: str,
    authorized: bool = Depends(get_admin_auth),
):
    if graphic_type not in FACEBOOK_ARTICLE_GRAPHIC_TYPES:
        raise HTTPException(status_code=404, detail="Graphic type not found")
    try:
        article = await _get_facebook_graphic_article(mongo_id)
        svg = compose_facebook_graphic_svg(article, graphic_type)
        return _facebook_graphic_response(svg, graphic_type, mongo_id)
    except HTTPException:
        raise
    except Exception as exc:
        _raise_facebook_graphic_error(exc, mongo_id)


@api_router.post("/admin/social-assets/facebook/quote/{mongo_id}")
async def get_admin_facebook_quote_graphic(
    mongo_id: str,
    request: FacebookQuoteGraphicRequest,
    authorized: bool = Depends(get_admin_auth),
):
    try:
        article = await _get_facebook_graphic_article(mongo_id)
        svg = compose_facebook_graphic_svg(
            article,
            "quote",
            quote=request.quote,
            attribution=request.attribution,
        )
        return _facebook_graphic_response(svg, "quote", mongo_id)
    except HTTPException:
        raise
    except Exception as exc:
        _raise_facebook_graphic_error(exc, mongo_id)


@api_router.post("/admin/social-assets/facebook/poll/{mongo_id}")
async def get_admin_facebook_poll_graphic(
    mongo_id: str,
    request: FacebookPollGraphicRequest,
    authorized: bool = Depends(get_admin_auth),
):
    try:
        article = await _get_facebook_graphic_article(mongo_id)
        svg = compose_facebook_graphic_svg(
            article,
            "poll",
            question=request.question,
            option_a=request.option_a,
            option_b=request.option_b,
        )
        return _facebook_graphic_response(svg, "poll", mongo_id)
    except HTTPException:
        raise
    except Exception as exc:
        _raise_facebook_graphic_error(exc, mongo_id)


async def _compose_admin_instagram_article_asset(
    article_id: str,
    *,
    composer,
    format_name: str,
    filename_suffix: str,
):
    if not ObjectId.is_valid(article_id):
        raise HTTPException(status_code=400, detail="Article ID is invalid")
    try:
        article = await db.articles.find_one(
            {
                "_id": ObjectId(article_id),
                "archived": {"$ne": True},
                "manual_review_hidden_from_public": {"$ne": True},
            },
            {"_id": 1, "title": 1, "category": 1, "image": 1},
        )
        if (
            not article
            or article.get("archived") is True
            or article.get("manual_review_hidden_from_public") is True
        ):
            raise HTTPException(status_code=404, detail="Article not found")
        if article.get("category") != "Local News":
            raise HTTPException(
                status_code=400,
                detail="Only Local News articles are supported",
            )
        svg = composer({
            "mongo_id": str(article["_id"]),
            "title": article.get("title"),
            "category": article.get("category"),
            "image": article.get("image"),
        })
        return Response(
            content=svg,
            media_type="image/svg+xml",
            headers={
                "Cache-Control": "no-store",
                "Content-Disposition": (
                    f'inline; filename="cheshire-today-{article_id.lower()}-{filename_suffix}.svg"'
                ),
            },
        )
    except HTTPException:
        raise
    except (
        InstagramAssetImageURLValidationError,
        InstagramAssetImageFetchError,
        InstagramAssetImageContentError,
        InstagramAssetArticleValidationError,
    ) as exc:
        logger.warning(
            "Admin Instagram %s rejected article_id=%s error=%s",
            format_name,
            article_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=422,
            detail="Article image is unavailable or unusable",
        ) from None
    except InstagramAssetTemplateValidationError as exc:
        logger.error(
            "Admin Instagram %s failed article_id=%s error=%s",
            format_name,
            article_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail="Social asset could not be generated",
        ) from None
    except Exception as exc:
        logger.error(
            "Admin Instagram %s failed article_id=%s error=%s",
            format_name,
            article_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail="Social asset could not be generated",
        ) from None


@api_router.get("/admin/social-assets/instagram/story/{article_id}")
async def get_admin_instagram_top_story_social_asset(
    article_id: str,
    authorized: bool = Depends(get_admin_auth),
):
    """Compose one active Local News Instagram Top Story without persistence."""
    return await _compose_admin_instagram_article_asset(
        article_id,
        composer=compose_instagram_top_story_svg,
        format_name="Story",
        filename_suffix="instagram-story-top-story",
    )


@api_router.get("/admin/social-assets/instagram/feed/{article_id}")
async def get_admin_instagram_feed_social_asset(
    article_id: str,
    authorized: bool = Depends(get_admin_auth),
):
    """Compose one active Local News Instagram Feed graphic without persistence."""
    return await _compose_admin_instagram_article_asset(
        article_id,
        composer=compose_instagram_feed_svg,
        format_name="Feed",
        filename_suffix="instagram-feed-local-news",
    )


@api_router.get("/admin/social-assets/instagram/reels-cover/{article_id}")
async def get_admin_instagram_reels_cover_social_asset(
    article_id: str,
    authorized: bool = Depends(get_admin_auth),
):
    """Compose one active Local News Instagram Reels cover without persistence."""
    return await _compose_admin_instagram_article_asset(
        article_id,
        composer=compose_instagram_reels_cover_svg,
        format_name="Reels Cover",
        filename_suffix="instagram-reels-cover-local-news",
    )


@api_router.get("/admin/articles")
async def get_admin_articles(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    authorized: bool = Depends(get_admin_auth)
):
    """Get admin articles with optional full-database search. Requires admin authentication."""
    try:
        admin_visible_clauses = [
            {"$or": [{"archived": {"$exists": False}}, {"archived": False}]},
            {"manual_review_hidden_from_public": {"$ne": True}},
        ]

        query = {"$and": admin_visible_clauses}
        if search and search.strip():
            raw_search = search.strip()
            id_match = re.search(r"([a-f0-9]{24})", raw_search, re.I)
            search_regex = {"$regex": raw_search, "$options": "i"}

            or_clauses = [
                {"title": search_regex},
                {"content": search_regex},
                {"source": search_regex},
                {"source_url": search_regex},
                {"category": search_regex},
                {"id": search_regex},
            ]

            if id_match:
                try:
                    from bson import ObjectId
                    or_clauses.append({"_id": ObjectId(id_match.group(1))})
                except Exception:
                    pass

            query = {
                "$and": [
                    *admin_visible_clauses,
                    {"$or": or_clauses},
                ]
            }

        articles = await db.articles.find(
            query
        ).sort("publishedDate", -1).skip(skip).limit(limit).to_list(limit)

        # Preserve the stored article `id` for existing admin actions, while
        # exposing Mongo `_id` separately for routes that require the public Mongo ID.
        for article in articles:
            article["mongo_id"] = str(article.get("_id") or "")
            article.pop("_id", None)

        total = await db.articles.count_documents(query)
        return {"articles": articles, "total": total, "skip": skip, "limit": limit, "search": search or ""}
    except Exception as e:
        logger.error(f"Error getting admin articles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def resolve_manual_article_image(image_url: str, source_url: str) -> str:
    """Prefer source og:image for manual articles when image is blank; allow direct Postimg image files for manual uploads."""
    chosen = (image_url or "").strip()
    source = (source_url or "").strip()

    def is_blocked(url: str) -> bool:
        lowered = (url or "").lower()
        postimg_host = any(host in lowered for host in ["postimg.cc", "i.postimg.cc", "postimage.org", "postimages.org"])
        if postimg_host:
            return not re.search(r"\.(jpg|jpeg|png|webp|gif)(\?.*)?$", lowered)
        return False

    if source and (not chosen or is_blocked(chosen)):
        try:
            import urllib.request
            req = urllib.request.Request(source, headers={"User-Agent": "Mozilla/5.0"})
            html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", errors="ignore")
            m = re.search(r'<meta[^>]+(?:property|name)=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
            if m:
                og_image = (m.group(1) or "").strip()
                if og_image and not is_blocked(og_image):
                    return og_image
        except Exception:
            pass

    return "" if is_blocked(chosen) else chosen


async def run_openai_article_review(article: dict) -> dict:
    """Run a low-cost editorial safety review for one article. Does not edit or publish/unpublish."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not configured")

    model = os.environ.get("OPENAI_REVIEW_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"

    title = str(article.get("title") or "").strip()
    summary = str(article.get("summary") or "").strip()
    content = str(article.get("content") or "").strip()
    category = str(article.get("category") or "").strip()
    source = str(article.get("source") or "").strip()
    source_url = str(article.get("source_url") or "").strip()
    scope = str(article.get("scope") or "").strip()
    location = str(article.get("location") or article.get("priority_location") or "").strip()

    review_payload = {
        "title": title,
        "summary": summary[:1200],
        "content": content[:9000],
        "category": category,
        "source": source,
        "source_url": source_url,
        "scope": scope,
        "location": location,
    }

    system_prompt = """You are an editorial safety and quality reviewer for Cheshire Today.

Cheshire Today strategy:
- Hybrid local + business/finance + AI/technology authority publication
- Local News should focus on Cheshire public-interest stories with a clear local place or organisation
- Business, Finance, Tech and AI stories may be UK-wide or international if they have practical relevance for Cheshire readers, small businesses, workers, households, investors, technology users or the wider economy
- Clean reader experience
- Avoid crime-heavy filler, live traffic filler, weak lifestyle filler, generic national filler, exaggerated headlines and unsupported claims

You are NOT rewriting the article.
You are NOT deciding final publication automatically.
You are only reviewing and flagging issues for a human editor.

Return valid JSON only with this exact shape:
{
  "safe_to_keep_live": true or false,
  "risk_level": "low" or "medium" or "high",
  "recommended_action": "keep_live" or "manual_review" or "archive",
  "category_fit": "good" or "questionable" or "poor",
  "local_place_confirmed": true or false,
  "strategy_fit": "strong" or "acceptable" or "weak",
  "crime_or_safeguarding_risk": true or false,
  "traffic_or_incident_filler": true or false,
  "weak_lifestyle_or_clickbait": true or false,
  "unsupported_claims": ["short issue", "..."],
  "factual_concerns": ["short issue", "..."],
  "editor_notes": "short practical note for the admin editor"
}

Be strict, but apply category rules correctly.

LOCAL NEWS RULE:
For Local News, require a clear Cheshire town, village, road, venue, school, council area, named site or local organisation. If Local News has no clear local place or organisation, use manual_review or archive.

BUSINESS / FINANCE / TECH / AI RULE:
Do NOT reject, downgrade to poor, or recommend archive for a Business, Finance, Tech or AI article merely because it is not Cheshire-local or because local_place_confirmed is false.
For Business, Finance, Tech and AI, local_place_confirmed=false is acceptable when the article has practical UK-wide or wider economic relevance for Cheshire readers, households, workers, small businesses, savers, borrowers, landlords, tenants, taxpayers, investors, drivers, employers, technology users, AI users or the wider local economy.
A strong Business/Finance/Tech/AI article can be safe_to_keep_live=true even with no Cheshire place if it is useful, factual, practical and aligned with money, jobs, tax, mortgages, rent, bills, energy, business costs, investment, productivity, AI, cybersecurity, software, cloud, automation, or the UK economy.

Use manual_review for high-stakes or sensitive national/international claims that may need checking.
Use archive only for weak, sensational, irrelevant, celebrity/entertainment, crime-heavy, live traffic, thin filler, shopping/gift-guide, or strategy-poor stories.
If recommending archive for Business, Finance, Tech or AI, editor_notes must explain the real weakness beyond lack of Cheshire locality.
"""

    user_prompt = "Review this article for Cheshire Today admin:\n" + json.dumps(review_payload, ensure_ascii=False)

    def _call_openai():
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content

    raw = await asyncio.to_thread(_call_openai)

    try:
        review = json.loads(raw or "{}")
    except Exception:
        review = {
            "safe_to_keep_live": False,
            "risk_level": "medium",
            "recommended_action": "manual_review",
            "category_fit": "questionable",
            "local_place_confirmed": bool(location),
            "strategy_fit": "weak",
            "crime_or_safeguarding_risk": False,
            "traffic_or_incident_filler": False,
            "weak_lifestyle_or_clickbait": False,
            "unsupported_claims": [],
            "factual_concerns": ["AI review returned non-JSON output."],
            "editor_notes": str(raw or "")[:500],
        }

    return review


def find_openai_rewrite_editorial_violations(article_content: str):
    """Return deterministic editorial violations in an OpenAI rewrite draft."""
    body = str(article_content or "").strip()
    if not body:
        return []

    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", body)
        if paragraph.strip()
    ]
    first_paragraph = paragraphs[0] if paragraphs else body
    last_paragraph = paragraphs[-1] if paragraphs else body
    violations = []

    lead_patterns = (
        r"\braising (?:questions|concerns)\b",
        r"\bprompting (?:scrutiny|discussion|discussions|debate)\b",
        r"\bunderscoring concerns\b",
        r"\bhighlighting the importance\b",
        r"\bsparking debate\b",
    )
    if any(re.search(pattern, first_paragraph, re.IGNORECASE) for pattern in lead_patterns):
        violations.append("interpretive wording in the opening paragraph")

    vague_attribution_patterns = (
        r"\brecent data (?:shows|indicates|suggests|reveals)\b",
        r"\bexperts (?:say|suggest|believe|warn|argue|claim|are examining|are exploring)\b",
        r"\bexperts (?:have |has )?(?:raise|raised|expressed|voiced) concerns?\b",
        r"\bcritics (?:say|suggest|believe|argue|claim|warn)\b",
        r"\bresearchers (?:say|suggest|believe|argue|claim|warn)\b",
        r"\bofficials (?:say|suggest|believe|argue|claim|warn)\b",
        r"\bobservers (?:say|suggest|believe|argue|claim|warn)\b",
        r"\bit is (?:thought|believed|understood|reported)\b",
    )
    if any(re.search(pattern, body, re.IGNORECASE) for pattern in vague_attribution_patterns):
        violations.append("vague or unnamed attribution")

    absolute_certainty_patterns = (
        r"\bensure(?:s|d)? full protection\b",
        r"\bguarantee(?:s|d)? (?:full )?protection\b",
        r"\bcompletely prevent(?:s|ed)?\b",
        r"\beliminate(?:s|d)? the risk\b",
        r"\bfully effective\b",
        r"\bzero risk\b",
        r"\balways safe\b",
        r"\bnever causes?\b",
    )
    if any(re.search(pattern, body, re.IGNORECASE) for pattern in absolute_certainty_patterns):
        violations.append("absolute or unsupported certainty")

    ending_patterns = (
        r"^\s*(?:the|a)\s+debate\b.*\bcontinues\b",
        r"^\s*as\b.*\b(?:grapples|evolves|continues|faces)\b",
        r"^\s*the future\b.*\bremains (?:uncertain|unclear)\b",
        r"^\s*the situation\b.*\b(?:highlights|underscores)\b.*\burgent need\b",
        r"\bthe question remains\b",
        r"\bthe focus remains\b",
        r"\burgent need for\b",
        r"^\s*(?:overall|ultimately|looking ahead)\b",
    )
    ending_paragraphs = paragraphs[-2:] if len(paragraphs) > 1 else [last_paragraph]
    if (
        last_paragraph.rstrip().endswith("?")
        or any(
            re.search(pattern, paragraph, re.IGNORECASE)
            for paragraph in ending_paragraphs
            for pattern in ending_patterns
        )
    ):
        violations.append("generic, rhetorical or essay-style ending")

    british_english_patterns = (
        r"\baging\b",
        r"\bmarginalized\b",
    )
    if any(re.search(pattern, body, re.IGNORECASE) for pattern in british_english_patterns):
        violations.append("non-British spelling")

    return violations


async def run_openai_article_rewrite_draft(article: dict) -> dict:
    """Create an OpenAI rewrite draft for admin review. Does not save, publish, unhide or update the DB."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not configured")

    model = os.environ.get("OPENAI_REWRITE_MODEL", os.environ.get("OPENAI_REVIEW_MODEL", "gpt-4o-mini")).strip() or "gpt-4o-mini"

    title = str(article.get("title") or "").strip()
    summary = str(article.get("summary") or "").strip()
    content = str(article.get("content") or "").strip()
    category = str(article.get("category") or "Local News").strip()
    source = str(article.get("source") or "").strip()
    source_url = str(article.get("source_url") or "").strip()
    location = str(article.get("location") or article.get("priority_location") or "").strip()

    # Admin-only source retrieval for the Open AI rewrite button.
    # This does not affect automatic imports and fails open to the existing
    # title/summary/content when the publisher blocks extraction.
    source_page_content = ""
    source_fetch_status = "not_attempted"

    if source_url.startswith(("http://", "https://")):
        try:
            from app.simple_scraper import scrape_article

            scrape_result = await asyncio.to_thread(
                scrape_article,
                source_url,
                20
            )

            source_fetch_status = (
                "ok" if scrape_result.get("ok")
                else str(scrape_result.get("error") or "failed")
            )

            extracted_content = str(scrape_result.get("content") or "").strip()
            if extracted_content:
                source_page_content = extracted_content[:18000]

        except Exception as scrape_error:
            source_fetch_status = f"failed: {str(scrape_error)[:160]}"
            logger.warning(
                f"OpenAI rewrite source extraction failed for {title[:60]}: "
                f"{source_fetch_status}"
            )

    # Admin-only structured verification for every rewrite with a source URL.
    # Perplexity returns a factual pack to corroborate the publisher page,
    # identify contradictions and prevent inaccurate source claims being
    # expanded into the draft. Nothing is saved or published automatically.
    research_fact_pack = {}

    if source_url.startswith(("http://", "https://")):
        try:
            research_fact_pack = await asyncio.wait_for(
                perplexity_service.research_article_facts(
                    title=title,
                    summary=summary or content,
                    source=source,
                    source_url=source_url,
                    publisher_content=source_page_content,
                ),
                timeout=120,
            )

            if research_fact_pack:
                source_fetch_status = (
                    f"{source_fetch_status}; fact_research_ok"
                    if source_fetch_status not in ("", "not_attempted")
                    else "fact_research_ok"
                )
            else:
                source_fetch_status = (
                    f"{source_fetch_status}; fact_research_empty"
                    if source_fetch_status not in ("", "not_attempted")
                    else "fact_research_empty"
                )

        except Exception as research_error:
            source_fetch_status = (
                f"{source_fetch_status}; fact_research_failed: "
                f"{str(research_error)[:120]}"
            )
            logger.warning(
                f"OpenAI rewrite fact research failed for {title[:60]}: "
                f"{str(research_error)[:160]}"
            )

    rewrite_payload = {
        "title": title,
        "summary": summary[:1800],
        "content": content[:12000],
        "category": category,
        "source": source,
        "source_url": source_url,
        "location": location,
        "source_page_content": source_page_content,
        "research_fact_pack": research_fact_pack,
        "source_fetch_status": source_fetch_status,
    }

    system_prompt = """You are a careful local news editor writing for Cheshire Today.

Task:
Rewrite the supplied article into a clean Cheshire Today draft for a human admin editor to review.

Important rules:

SOURCE CONTROL
- Return valid JSON only.
- Do not publish, save or modify the article.
- Do not mention being an AI or describe the rewriting process in the article.
- When both source_page_content and research_fact_pack are available, compare them before writing.
- Treat source_page_content as the publisher's account, not automatic proof that every claim is accurate.
- Use research_fact_pack to corroborate names, roles, dates, locations, figures, quotations and award or legal status.
- Give greater weight to official bodies, original records and authoritative primary sources when they conflict with the publisher page.
- Never combine contradictory versions of the same fact.
- If a meaningful contradiction remains, use only the best-supported version and record the conflict clearly in editor_notes.
- If research_fact_pack is unavailable, use only claims directly supported by source_page_content and flag important verification limits in editor_notes.
- Treat the stored title, summary and content only as research leads. Do not repeat their claims unless supported by source_page_content or research_fact_pack.
- Do not use training knowledge, memory, assumptions or invented context.
- Never present uncertain_or_unverified items or contradictions as established facts.
- If a detail cannot be verified, omit it.
- Preserve supported names, dates, locations, figures, organisations and quotations accurately.
- Use direct quotations only when the exact quotation and speaker are supported.
- Rewrite fully in fresh wording rather than copying the source.
- Treat every sentence as if an editor may ask for its supporting source. Remove any sentence that cannot be supported.

CLAIM STRENGTH AND OFFICIAL STATUS
- Preserve the exact strength, scope, population, conditions and uncertainty of every source claim.
- Never strengthen may to will, possible to likely, protection to full protection, unlikely to be cost-effective to unnecessary, recommendation to decision or approval, under consideration to will happen, concern to failure, or eligible to entitled.
- Distinguish recommendation, consultation, proposal, consideration, approval, decision and implementation.
- Preserve exact cost-effectiveness qualifications and the population or conditions to which they apply.
- Treat contradictions and uncertain_or_unverified as hard limits; do not make categorical claims that conflict with either field.
- Treat official_status_verified=false as a warning not to strengthen or extend an official or policy status.
- Never infer government or organisational motives, financial consequences, savings, funding decisions, implementation dates, implementation consequences or policy outcomes.
- Cost-effectiveness analysis is evidence used in policy-making, not itself a government policy decision.

NEWS JUDGEMENT AND ATTRIBUTION
- Select the strongest verified facts. Do not try to include every available detail.
- Separate reported facts from opinion, criticism, analysis and forecasts.
- Attribute opinions and interpretations directly to the named person or organisation making them.
- Attribute important statistics, reports and claims to their named source.
- Never use vague attribution such as "experts say", "critics believe", "recent data shows" or "it is thought".
- Attribute every factual finding, opinion, interpretation or criticism to the specific person, organisation, study or official body supporting it.
- Never combine findings from one source with opinions from another source under a collective label such as "experts", "critics", "researchers" or "officials".
- When two sources support different parts of a paragraph, identify each source separately.
- When comparing figures, give the exact periods being compared whenever they are available.
- Do not imply that correlation proves causation.
- Do not add a Cheshire connection unless the verified material supports one.

LEAD
- Begin with the single strongest verified news development.
- Include the main source, figure, place or date in the opening where it materially helps the reader.
- The opening must report what has happened rather than comment on what it means.
- Do not use interpretive lead phrases such as "raising questions", "prompting scrutiny", "underscoring concerns", "highlighting the importance" or "sparking debate" unless that reaction is itself verified and attributed.

STRUCTURE AND STYLE
- Organise the article logically: the development, key evidence, necessary context, attributed responses or viewpoints, and confirmed next steps where available.
- Preserve chronological order where it improves clarity.
- Merge closely related facts into coherent paragraphs.
- Every paragraph must add a new fact, attributed viewpoint or necessary context.
- Avoid repeating names, statistics, organisations or conclusions.
- Produce a complete article when enough verified material exists, but let the available facts determine its length.
- Never pad a thin story with generic background, speculation or commentary.
- Write in natural British English suitable for a professional UK regional newspaper.
- Use British spellings throughout, including "ageing", "marginalised", "organisation", "programme" and "centre" where applicable.
- Avoid clickbait, promotional wording, council-press-release language, exaggerated claims and generic AI phrasing.
- For Local News, preserve supported Cheshire towns, villages, roads, venues, councils, schools, hospitals, businesses and organisations.
- For Business, Finance, AI & Tech and UK stories, explain practical relevance only when the verified facts support it.

ENDING
- End on a concrete verified fact, attributed official response, confirmed action, date, deadline or practical information.
- If no suitable closing fact exists, end on the last substantive factual paragraph.
- Never add a concluding paragraph merely to summarise the article or discuss the wider debate.
- Never end with an opinion, rhetorical question, prediction, recommendation or call for reform.
- Forbidden generic endings include "The debate continues", "As discussions evolve", "Looking ahead", "Ultimately", "Overall", "the focus remains" and "the urgent need for reform".

FINAL CHECK
- Before returning the JSON, silently remove unsupported claims, vague attribution, interpretive wording in the lead, repetition and any generic concluding paragraph.
- If the source material is unavailable or thin, explain that only in editor_notes, not in the article body.
- Do not include source labels, citation lists, markdown headings, bullet points or meta commentary in the content body.

Return this exact JSON shape:
{
  "title": "rewritten headline",
  "summary": "one or two sentence summary",
  "content": "full rewritten article body in plain text paragraphs",
  "category": "same or corrected category",
  "editor_notes": "short note for the admin editor, including any limitations or checks needed"
}
"""

    user_prompt = "Rewrite this article into an admin-review draft for Cheshire Today:\n" + json.dumps(rewrite_payload, ensure_ascii=False)

    def _call_openai():
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            temperature=0.25,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content

    raw = await asyncio.to_thread(_call_openai)

    try:
        draft = json.loads(raw or "{}")
    except Exception:
        draft = {
            "title": title,
            "summary": summary,
            "content": content,
            "category": category,
            "editor_notes": "OpenAI returned non-JSON output. Original article has been left unchanged."
        }

    draft_title = str(draft.get("title") or title).strip()
    draft_summary = str(draft.get("summary") or summary).strip()
    draft_content = str(draft.get("content") or content).strip()
    draft_category = str(draft.get("category") or category or "Local News").strip()
    draft_notes = str(draft.get("editor_notes") or "").strip()

    editorial_guard_violations = find_openai_rewrite_editorial_violations(draft_content)

    if editorial_guard_violations:
        correction_system_prompt = """You are a strict UK newspaper copy editor.

Return valid JSON only, using exactly these fields:
title, summary, content, category, editor_notes.

Revise the supplied draft only enough to correct the listed editorial violations.

Rules:
- Use only facts already present in the draft or supported by source_page_content or research_fact_pack.
- Do not add new names, figures, claims, quotations, context or conclusions.
- Remove unsupported or vaguely attributed claims when no named source supports them.
- Split blended evidence into separately attributed sentences.
- Do not imply that a person, study or organisation made a claim supplied by another source.
- If the exact responsible source cannot be identified, remove the claim.
- Repeat the person or organisation name when necessary instead of using vague plural attribution.
- Review the complete draft for unsupported strengthening, not only the detected phrase.
- Restore the exact source strength, scope, population, conditions, uncertainty and official decision stage.
- Remove absolute efficacy or outcome wording unless the same absolute claim is explicitly supported.
- Do not convert recommendation, consideration or cost-effectiveness analysis into approval, implementation or government policy.
- Remove inferred motives, financial consequences, savings, funding decisions, implementation details or policy outcomes that are not explicit in verified evidence.
- Treat contradictions and uncertain_or_unverified as hard limits, and do not strengthen official status when official_status_verified is false.
- Make the opening factual and remove interpretation such as "raising concerns" or "prompting scrutiny".
- Attribute opinions and interpretations directly to the named person or organisation responsible.
- Remove a generic or rhetorical final paragraph entirely when necessary.
- End on the final substantive verified fact, attributed response, action, date or practical information.
- Never replace one generic conclusion with another.
- Use natural British English and British spellings.
- Preserve the article's strongest verified facts and overall meaning.
- Preserve relevant limitations in editor_notes.
"""

        correction_payload = {
            "editorial_violations": editorial_guard_violations,
            "draft": {
                "title": draft_title,
                "summary": draft_summary,
                "content": draft_content,
                "category": draft_category,
                "editor_notes": draft_notes,
            },
            "source_page_content": source_page_content,
            "research_fact_pack": research_fact_pack,
        }

        def _call_openai_correction():
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": correction_system_prompt},
                    {
                        "role": "user",
                        "content": json.dumps(correction_payload, ensure_ascii=False),
                    },
                ],
            )
            return response.choices[0].message.content

        try:
            corrected_raw = await asyncio.to_thread(_call_openai_correction)
            corrected = json.loads(corrected_raw or "{}")

            draft_title = str(corrected.get("title") or draft_title).strip()
            draft_summary = str(corrected.get("summary") or draft_summary).strip()
            draft_content = str(corrected.get("content") or draft_content).strip()
            draft_category = str(corrected.get("category") or draft_category).strip()
            draft_notes = str(corrected.get("editor_notes") or draft_notes).strip()
        except Exception:
            guard_failure_note = (
                "The automatic editorial correction pass could not be applied. "
                "Review the detected issues before publishing."
            )
            draft_notes = " ".join(
                part for part in (draft_notes, guard_failure_note) if part
            )

    editorial_guard_remaining_violations = find_openai_rewrite_editorial_violations(draft_content)

    if editorial_guard_remaining_violations:
        remaining_note = (
            "Editorial guard still detected: "
            + ", ".join(editorial_guard_remaining_violations)
            + ". Review before publishing."
        )
        draft_notes = " ".join(
            part for part in (draft_notes, remaining_note) if part
        )

    return {
        "title": draft_title,
        "summary": draft_summary,
        "content": draft_content,
        "category": draft_category,
        "editor_notes": draft_notes,
        "model": model,
        "source_fetch_status": source_fetch_status,
        "source_page_content_length": len(source_page_content),
        "research_fact_pack_available": bool(research_fact_pack),
        "research_source_count": len(research_fact_pack.get("source_urls", [])) if isinstance(research_fact_pack, dict) else 0,
        "research_fact_pack": research_fact_pack,
        "editorial_guard_triggered": bool(editorial_guard_violations),
        "editorial_guard_violations": editorial_guard_violations,
        "editorial_guard_corrected": bool(
            editorial_guard_violations
            and not editorial_guard_remaining_violations
        ),
        "editorial_guard_remaining_violations": editorial_guard_remaining_violations,
    }


@api_router.post("/admin/articles/{article_id}/ai-review")
async def admin_ai_review_article(article_id: str, authorized: bool = Depends(get_admin_auth)):
    """Admin-only ChatGPT/OpenAI article review. Flags risk; does not auto-edit/archive/hide."""
    try:
        article = await _find_article_by_any_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        review = await run_openai_article_review(article)

        now_iso = datetime.now(timezone.utc).isoformat()
        review_doc = {
            "ai_review_status": "reviewed",
            "ai_review_checked_at": now_iso,
            "ai_review_model": os.environ.get("OPENAI_REVIEW_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini",
            "ai_review_result": review,
            "ai_review_risk_level": review.get("risk_level"),
            "ai_review_recommended_action": review.get("recommended_action"),
            "ai_review_safe_to_keep_live": review.get("safe_to_keep_live"),
        }

        if article.get("_id"):
            await db.articles.update_one({"_id": article["_id"]}, {"$set": review_doc})
        elif article.get("id"):
            await db.articles.update_one({"id": article["id"]}, {"$set": review_doc})

        return {
            "success": True,
            "article_id": str(article.get("_id") or article.get("id") or article_id),
            "title": article.get("title"),
            "review": review,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running AI article review: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/admin/articles/{article_id}/openai-rewrite-draft")
async def admin_openai_rewrite_draft(article_id: str, authorized: bool = Depends(get_admin_auth)):
    """Admin-only OpenAI rewrite draft. Returns draft text only; does not save, publish, unhide or update."""
    try:
        article = await _find_article_by_any_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        draft = await run_openai_article_rewrite_draft(article)

        return {
            "success": True,
            "article_id": str(article.get("_id") or article.get("id") or article_id),
            "original_title": article.get("title"),
            "draft": draft,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating OpenAI rewrite draft: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/admin/articles")
async def create_manual_article(article: ManualArticleCreate, authorized: bool = Depends(get_admin_auth)):
    """Create a new article manually. Requires admin authentication.
    
    Automatically detects and sets location based on article content.
    """
    try:
        from app.news_feed_service import get_article_priority_location
        
        # Generate article ID
        article_id = str(uuid.uuid4())
        
        # Use default image if not provided
        default_image = ""
        
        # Use explicit admin-selected location when provided; otherwise auto-detect from title/content.
        manual_location = normalise_manual_article_location(article.location)
        detected_location = manual_location or get_article_priority_location(article.title, article.content)
        
        # Build tags list
        tags = article.tags or []
        if detected_location:
            location_tag = detected_location.capitalize()
            if location_tag not in tags:
                tags.append(location_tag)
        
        resolved_source_url = article.source_url or ""
        resolved_image = resolve_manual_article_image(article.image or default_image, resolved_source_url)

        # Create article document
        article_doc = {
            "id": article_id,
            "title": article.title,
            "summary": (article.summary or "").strip(),
            "content": article.content,
            "category": article.category,
            "author": article.author or "Cheshire Today",
            "publishedDate": datetime.now(timezone.utc).isoformat(),
            "image": resolved_image,
            "tags": tags,
            "featured": article.featured or False,
            "force_live": article.force_live or False,
            "source": article.source or "Manual Entry",
            "source_url": resolved_source_url,
            "scope": article.scope or "cheshire",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Add location if detected
        if detected_location:
            article_doc["location"] = detected_location
            logger.info(f"Auto-detected location '{detected_location}' for new article: {article.title}")
        
        # Insert into database
        await db.articles.insert_one(article_doc)
        
        # Remove _id for response
        article_doc.pop('_id', None)
        
        logger.info(f"Manual article created: {article.title}")
        
        return {
            "success": True,
            "message": "Article created successfully",
            "article": article_doc,
            "location_detected": detected_location
        }
        
    except Exception as e:
        logger.error(f"Error creating manual article: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/admin/articles/{article_id}")
async def update_article(article_id: str, article: ManualArticleCreate, authorized: bool = Depends(get_admin_auth)):
    """Update an existing article. Requires admin authentication.
    
    Automatically detects and updates location based on article content.
    """
    try:
        from app.news_feed_service import get_article_priority_location
        
        # Check if article exists by custom id first, then MongoDB _id.
        # Admin Manual Review uses MongoDB _id as article.id, so both must work.
        match_query = {"id": article_id}
        existing = await db.articles.find_one(match_query)

        if not existing:
            try:
                mongo_id = ObjectId(article_id)
                match_query = {"_id": mongo_id}
                existing = await db.articles.find_one(match_query)
            except Exception:
                pass

        if not existing:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Use explicit admin-selected location when provided; otherwise auto-detect from updated title/content.
        manual_location = normalise_manual_article_location(article.location)
        detected_location = manual_location or get_article_priority_location(article.title, article.content)
        
        resolved_source_url = article.source_url if article.source_url is not None else existing.get("source_url", "")
        candidate_image = article.image if article.image is not None else existing.get("image")
        resolved_image = resolve_manual_article_image(candidate_image, resolved_source_url)

        # Build update document
        update_doc = {
            "title": article.title,
            "summary": (article.summary or "").strip(),
            "content": article.content,
            "category": article.category,
            "author": article.author or existing.get("author", "Cheshire Today"),
            "image": resolved_image,
            "source": article.source or existing.get("source", "Manual Entry"),
            "source_url": resolved_source_url,
            "tags": article.tags or existing.get("tags", []),
            "featured": article.featured if article.featured is not None else existing.get("featured", False),
            "force_live": article.force_live if article.force_live is not None else existing.get("force_live", False),
            "scope": article.scope or existing.get("scope", "cheshire"),
            "manual_edited": True,
            "manual_edited_at": datetime.now(timezone.utc).isoformat(),
            "manual_edit_protected": True,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Update location if detected (or clear if no longer matches any location)
        if detected_location:
            update_doc["location"] = detected_location
            update_doc["priority_location"] = detected_location
            # Add location to tags if not already present
            location_tag = detected_location.capitalize()
            if location_tag not in update_doc["tags"]:
                update_doc["tags"].append(location_tag)
            logger.info(f"Auto-detected location '{detected_location}' for article: {article.title}")
        else:
            # Clear location if article no longer matches any specific location
            update_doc["location"] = None
            update_doc["priority_location"] = None
        
        unset_doc = {}
        restored_from_manual_review = False

        was_manual_review = (
            existing.get("manual_review_hidden_from_public") is True
            or existing.get("archive_reason") == "needs_manual_review"
        )

        if was_manual_review:
            review_check_article = {**existing, **update_doc}
            remaining_review_reason = find_local_location_review_reason(
                review_check_article,
                update_doc.get("content", ""),
                update_doc.get("title", ""),
            )
            remaining_ai_hits = find_ai_manual_review_hits(update_doc.get("content", ""))

            remaining_reasons = []
            if remaining_review_reason:
                remaining_reasons.append(remaining_review_reason)
            if remaining_ai_hits:
                remaining_reasons.append("Edited article still contains risky invented-detail phrases; verify against source before restoring.")

            force_live_override = bool(update_doc.get("force_live"))

            if remaining_reasons and not force_live_override:
                update_doc.update({
                    "manual_review_hidden_from_public": True,
                    "manual_review_reason": " ".join(remaining_reasons),
                    "manual_review_hits": remaining_ai_hits,
                    "manual_review_created_at": existing.get("manual_review_created_at") or datetime.now(timezone.utc).isoformat(),
                    "verification_status": "needs_manual_review",
                    "rewrite_status": "manual_review_required",
                })
                update_doc["editorial_metadata"] = build_manual_review_editorial_metadata(
                    {**existing, **update_doc}
                )
                restored_from_manual_review = False
            else:
                restored_from_manual_review = True
                update_doc.update({
                    "archived": False,
                    "verification_status": "manual_corrected_verified_limited",
                    "rewrite_status": "manual_corrected",
                    "ai_rewritten": False,
                    "manual_review_restored_at": datetime.now(timezone.utc).isoformat(),
                })
                unset_doc.update({
                    "archived_at": "",
                    "archive_reason": "",
                    "manual_review_hidden_from_public": "",
                    "manual_review_hits": "",
                    "manual_review_reason": "",
                    "manual_review_created_at": "",
                    "editorial_metadata": "",
                })

        update_operation = {"$set": update_doc}
        if unset_doc:
            update_operation["$unset"] = unset_doc

        # Update in database
        await db.articles.update_one(
            match_query,
            update_operation
        )
        
        logger.info(f"Article updated: {article.title}")
        
        return {
            "success": True,
            "message": "Article updated and restored successfully" if restored_from_manual_review else "Article updated successfully",
            "location_detected": detected_location,
            "restored_from_manual_review": restored_from_manual_review
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating article: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/admin/articles/{article_id}/move-to-manual-review")
async def move_article_to_manual_review(article_id: str, authorized: bool = Depends(get_admin_auth)):
    # Admin-only: hide a live article from public feeds and place it back into Manual Review for editing.
    try:
        from bson import ObjectId

        existing = await db.articles.find_one({"id": article_id})
        match_query = {"id": article_id}

        if not existing and len(article_id) == 24:
            try:
                mongo_id = ObjectId(article_id)
                existing = await db.articles.find_one({"_id": mongo_id})
                if existing:
                    match_query = {"_id": mongo_id}
            except Exception:
                pass

        if not existing:
            raise HTTPException(status_code=404, detail="Article not found")

        now_iso = datetime.now(timezone.utc).isoformat()
        update_doc = {
            "archived": False,
            "manual_review_hidden_from_public": True,
            "manual_review_reason": "Moved back to Manual Review for editor rewrite before publication",
            "manual_review_created_at": now_iso,
            "verification_status": "needs_manual_review",
            "rewrite_status": "manual_review_required",
            "force_live": False,
            "updated_at": now_iso,
        }
        update_doc["editorial_metadata"] = build_manual_review_editorial_metadata(
            {**existing, **update_doc}
        )

        await db.articles.update_one(
            match_query,
            {
                "$set": update_doc,
                "$unset": {
                    "archived_at": "",
                    "archive_reason": "",
                    "archive_source": "",
                },
            },
        )

        return {
            "success": True,
            "article_id": str(existing.get("id") or article_id),
            "title": existing.get("title"),
            "message": "Article moved to Manual Review"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error moving article to Manual Review: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/admin/articles/{article_id}/force-live")
async def toggle_force_live_article(article_id: str, authorized: bool = Depends(get_admin_auth)):
    """Toggle force_live for an article so it can bypass homepage/public feed filters."""
    try:
        from bson import ObjectId

        existing = await db.articles.find_one({"id": article_id})
        match_query = {"id": article_id}

        if not existing and len(article_id) == 24:
            try:
                mongo_id = ObjectId(article_id)
                existing = await db.articles.find_one({"_id": mongo_id})
                if existing:
                    match_query = {"_id": mongo_id}
            except Exception:
                pass

        if not existing:
            raise HTTPException(status_code=404, detail="Article not found")

        new_value = not bool(existing.get("force_live", False))

        if new_value and existing.get("manual_review_hidden_from_public") is True:
            ai_safe = existing.get("ai_review_safe_to_keep_live") is True
            ai_action = str(existing.get("ai_review_recommended_action") or "").lower()
            content_len = len(str(existing.get("content") or "").strip())
            if not ai_safe and ai_action not in ("keep_live", "publish"):
                raise HTTPException(status_code=400, detail="Force Live blocked: run AI Review first and only force live articles marked safe to keep live, or edit the article manually before publishing.")
            if content_len < 1000:
                raise HTTPException(status_code=400, detail="Force Live blocked: article content is too short. Edit/rewrite before publishing.")

        update_doc = {"force_live": new_value, "updated_at": datetime.now(timezone.utc).isoformat()}
        unset_doc = {}
        if new_value:
            update_doc.update({
                "archived": False,
                "verification_status": "manual_force_live",
                "rewrite_status": "manual_force_live",
                "manual_review_restored_at": datetime.now(timezone.utc).isoformat(),
            })
            unset_doc.update({
                "archived_at": "",
                "archive_reason": "",
                "manual_review_hidden_from_public": "",
                "manual_review_hits": "",
                "manual_review_reason": "",
                "manual_review_created_at": "",
                "editorial_metadata": "",
            })

        update_operation = {"$set": update_doc}
        if unset_doc:
            update_operation["$unset"] = unset_doc

        await db.articles.update_one(match_query, update_operation)

        return {
            "success": True,
            "article_id": str(existing.get("id") or article_id),
            "force_live": new_value,
            "message": "Article forced live" if new_value else "Force live removed"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling force_live: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/check-smtp-config")
async def check_smtp_config():
    """Check SMTP configuration (admin diagnostic endpoint)"""
    import os
    smtp_host = os.environ.get('SMTP_HOST', 'NOT SET')
    smtp_port = os.environ.get('SMTP_PORT', 'NOT SET')
    smtp_user = os.environ.get('SMTP_USER', 'NOT SET')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')
    smtp_from = os.environ.get('SMTP_FROM_EMAIL', 'NOT SET')
    
    # Mask password for security
    password_status = "SET (hidden)" if smtp_password else "NOT SET"
    
    return {
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
        "smtp_user": smtp_user,
        "smtp_password": password_status,
        "smtp_from_email": smtp_from,
        "config_valid": all([
            smtp_host != 'NOT SET',
            smtp_port != 'NOT SET', 
            smtp_user != 'NOT SET',
            smtp_password,
            smtp_from != 'NOT SET'
        ]),
        "godaddy_recommended_settings": {
            "smtp_host": "smtpout.secureserver.net",
            "smtp_port": "465 (SSL) or 587 (TLS)",
            "smtp_user": "your-email@yourdomain.com",
            "smtp_from_email": "your-email@yourdomain.com"
        }
    }

# ============================================
# ARTICLE ARCHIVE & MANAGEMENT ENDPOINTS
# ============================================

@api_router.post("/admin/articles/{article_id}/archive")
async def archive_article(article_id: str, auth: bool = Depends(get_admin_auth)):
    """Archive an article (move to archived status)"""
    try:
        from bson import ObjectId
        
        # Try to find article by various ID formats
        article = None
        if len(article_id) == 24:
            try:
                article = await db.articles.find_one({"_id": ObjectId(article_id)})
            except:
                pass
        if not article:
            article = await db.articles.find_one({"id": article_id})
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Update article to archived status
        await db.articles.update_one(
            {"_id": article["_id"]},
            {"$set": {
                "archived": True,
                "archived_at": datetime.now(timezone.utc).isoformat(),
                "archive_reason": "manual_admin"
            }}
        )
        
        return {"success": True, "message": "Article archived successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving article: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/admin/articles/{article_id}/unarchive")
async def unarchive_article(article_id: str, auth: bool = Depends(get_admin_auth)):
    """Restore an archived article - handles both legacy (archived flag) and new (archived_articles collection) systems"""
    try:
        from bson import ObjectId
        
        # First, try to find in main articles collection (legacy archived)
        article = None
        mongo_id = None
        
        if len(article_id) == 24:
            try:
                mongo_id = ObjectId(article_id)
                article = await db.articles.find_one({"_id": mongo_id, "archived": True})
            except:
                pass
        
        if not article:
            article = await db.articles.find_one({"id": article_id, "archived": True})
            if article:
                mongo_id = article["_id"]
        
        # If found in main collection, just unset the archived flag
        if article:
            await db.articles.update_one(
                {"_id": mongo_id},
                {"$set": {"archived": False}, "$unset": {"archived_at": "", "archive_reason": ""}}
            )
            return {"success": True, "message": "Article restored successfully"}
        
        # If not in main collection, look in archived_articles collection
        archived_article = None
        
        if len(article_id) == 24:
            try:
                archived_article = await db.archived_articles.find_one({"_id": ObjectId(article_id)})
            except:
                pass
        
        if not archived_article:
            archived_article = await db.archived_articles.find_one({"id": article_id})
        
        if not archived_article:
            raise HTTPException(status_code=404, detail="Article not found in archive")
        
        # Move from archived_articles back to main articles collection
        original_id = archived_article.pop('_id', None)
        archived_article.pop('archived_at', None)
        archived_article.pop('archive_reason', None)
        archived_article.pop('archive_source', None)
        archived_article['archived'] = False
        
        # Insert into main collection
        await db.articles.insert_one(archived_article)
        
        # Remove from archived collection
        await db.archived_articles.delete_one({"_id": original_id})
        
        return {"success": True, "message": "Article restored from archive successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unarchiving article: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/admin/articles/manual-review")
async def get_manual_review_articles(
    skip: int = 0,
    limit: int = 100,
    auth: bool = Depends(get_admin_auth)
):
    """Get live articles hidden from public feeds pending manual review."""
    try:
        safe_skip = max(0, int(skip or 0))
        safe_limit = min(max(1, int(limit or 100)), 250)

        query = {
            "manual_review_hidden_from_public": True,
            "$or": [{"archived": {"$exists": False}}, {"archived": False}]
        }
        projection = {
            "_id": 1,
            "id": 1,
            "title": 1,
            "content": 1,
            "summary": 1,
            "category": 1,
            "publishedDate": 1,
            "created_at": 1,
            "image": 1,
            "source": 1,
            "source_url": 1,
            "author": 1,
            "tags": 1,
            "scope": 1,
            "location": 1,
            "priority_location": 1,
            "manual_review_reason": 1,
            "manual_review_created_at": 1,
            "editorial_metadata": 1,
            "verification_status": 1,
            "rewrite_status": 1,
            "ai_review_status": 1,
            "ai_review_checked_at": 1,
            "ai_review_model": 1,
            "ai_review_risk_level": 1,
            "ai_review_recommended_action": 1,
            "ai_review_safe_to_keep_live": 1,
            "ai_review_result": 1,
        }

        total = await db.articles.count_documents(query)
        articles = await db.articles.find(query, projection).sort("publishedDate", -1).skip(safe_skip).limit(safe_limit).to_list(safe_limit)

        for article in articles:
            # Older Manual Review records predate persisted editorial metadata.
            # Derive the same read-only contract so every Admin row is complete.
            article["editorial_metadata"] = build_manual_review_editorial_metadata(article)
            article["id"] = str(article.get("_id") or article.get("id") or "")
            if "_id" in article:
                del article["_id"]

        return {
            "success": True,
            "articles": articles,
            "total": total,
            "skip": safe_skip,
            "limit": safe_limit,
        }
    except Exception as e:
        logger.error(f"Error getting manual review articles: {e}")
        raise HTTPException(status_code=500, detail="Could not load manual review articles")


@api_router.get("/admin/articles/archived")
async def get_archived_articles(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    auth: bool = Depends(get_admin_auth)
):
    """Get all archived articles from both legacy (archived flag) and new (archived_articles collection) systems"""
    try:
        safe_skip = max(0, int(skip or 0))
        safe_limit = min(max(1, int(limit or 20)), 100)
        fetch_cap = min(safe_skip + safe_limit, 500)
        all_archived = []

        raw_search = str(search or "").strip()
        search_clauses = []

        if raw_search:
            escaped_search = re.escape(raw_search)
            search_regex = {"$regex": escaped_search, "$options": "i"}

            search_clauses = [
                {"title": search_regex},
                {"source": search_regex},
                {"source_url": search_regex},
                {"id": search_regex},
            ]

            id_match = re.fullmatch(r"[a-f0-9]{24}", raw_search, re.I)
            if id_match:
                try:
                    from bson import ObjectId
                    search_clauses.append({"_id": ObjectId(raw_search)})
                except Exception:
                    pass

        legacy_query = {"archived": True}
        collection_query = {}

        if search_clauses:
            legacy_query = {
                "$and": [
                    {"archived": True},
                    {"$or": search_clauses},
                ]
            }
            collection_query = {"$or": search_clauses}
        
        # Get articles from main collection with archived flag (legacy system)
        legacy_archived = await db.articles.find(
            legacy_query,
            {"_id": 1, "id": 1, "title": 1, "content": 1, "summary": 1, "category": 1, "publishedDate": 1, "archived_at": 1, "image": 1, "archive_reason": 1, "verification_status": 1, "rewrite_status": 1, "manual_review_hits": 1, "manual_review_reason": 1, "manual_review_hidden_from_public": 1, "manual_review_created_at": 1, "source": 1, "source_url": 1, "author": 1, "tags": 1, "featured": 1, "force_live": 1, "scope": 1, "location": 1}
        ).sort([("archived_at", -1), ("publishedDate", -1)]).limit(fetch_cap).to_list(fetch_cap)
        
        for article in legacy_archived:
            article['id'] = str(article.get('id', article['_id']))
            article['archive_source'] = 'legacy'
            if '_id' in article:
                del article['_id']
            all_archived.append(article)
        
        # Get articles from archived_articles collection (new system)
        new_archived = await db.archived_articles.find(
            collection_query,
            {"_id": 1, "id": 1, "title": 1, "content": 1, "summary": 1, "category": 1, "publishedDate": 1, "archived_at": 1, "image": 1, "archive_reason": 1, "verification_status": 1, "rewrite_status": 1, "manual_review_hits": 1, "manual_review_reason": 1, "manual_review_hidden_from_public": 1, "manual_review_created_at": 1, "source": 1, "source_url": 1, "author": 1, "tags": 1, "featured": 1, "force_live": 1, "scope": 1, "location": 1}
        ).sort([("archived_at", -1), ("publishedDate", -1)]).limit(fetch_cap).to_list(fetch_cap)
        
        for article in new_archived:
            article['id'] = str(article.get('id', article['_id']))
            article['archive_source'] = 'collection'
            if '_id' in article:
                del article['_id']
            all_archived.append(article)
        
        # Sort by archived_at descending
        all_archived.sort(key=lambda x: x.get('archived_at', ''), reverse=True)
        
        # Count totals without loading the full archive into memory
        legacy_total = await db.articles.count_documents(legacy_query)
        collection_total = await db.archived_articles.count_documents(collection_query)
        total = legacy_total + collection_total
        paginated = all_archived[safe_skip:safe_skip + safe_limit]
        
        return {
            "articles": paginated,
            "total": total,
            "skip": safe_skip,
            "limit": safe_limit,
            "search": raw_search,
        }
    except Exception as e:
        logger.error(f"Error getting archived articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/admin/articles/bulk-archive")
async def bulk_archive_articles(
    payload: dict = Body(default={}),
    auth: bool = Depends(get_admin_auth)
):
    """
    Bulk archive helper.

    Supports:
      - {"keep_visible": N}  -> keep newest N active (archive the rest)
      - {"days_old": D}      -> archive active articles older than D days (legacy behavior)
    """
    try:
        now = datetime.now(timezone.utc)
        keep_visible = 0
        days_old = None

        if isinstance(payload, dict):
            if payload.get("keep_visible") is not None:
                try:
                    keep_visible = int(payload.get("keep_visible") or 0)
                except Exception:
                    keep_visible = 0
            if payload.get("days_old") is not None:
                try:
                    days_old = int(payload.get("days_old"))
                except Exception:
                    days_old = None

        active_filter = {"$or": [{"archived": {"$exists": False}}, {"archived": False}]}

        # Mode A: keep newest N
        if keep_visible and keep_visible > 0:
            active = await db.articles.find(
                active_filter,
                {"_id": 1, "publishedDate": 1}
            ).sort("publishedDate", -1).to_list(10000)

            keep = active[:keep_visible]
            keep_ids = [a["_id"] for a in keep if a.get("_id") is not None]

            archive_query = dict(active_filter)
            archive_query["_id"] = {"$nin": keep_ids}

            result = await db.articles.update_many(
                archive_query,
                {"$set": {
                    "archived": True,
                    "archived_at": now.isoformat(),
                    "archive_reason": f"bulk_keep_newest_{keep_visible}"
                }}
            )

            return {
                "success": True,
                "mode": "keep_newest",
                "kept_visible": keep_visible,
                "archived_count": result.modified_count,
                "message": f"Archived {result.modified_count} older articles; kept newest {keep_visible} visible"
            }

        # Mode B: legacy days_old
        if days_old is None:
            days_old = 30

        cutoff_date = now - timedelta(days=days_old)

        result = await db.articles.update_many(
            {
                "publishedDate": {"$lt": cutoff_date.isoformat()},
                **active_filter
            },
            {"$set": {"archived": True, "archived_at": now.isoformat(), "archive_reason": f"bulk_days_old_{days_old}"}}
        )

        return {
            "success": True,
            "mode": "days_old",
            "days_old": days_old,
            "archived_count": result.modified_count,
            "message": f"Archived {result.modified_count} articles older than {days_old} days"
        }

    except Exception as e:
        logger.error(f"Error bulk archiving articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@api_router.get("/admin/articles/by-date")
async def get_articles_by_date_range(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    include_archived: bool = False,
    skip: int = 0,
    limit: int = 50,
    auth: bool = Depends(get_admin_auth)
):
    """Get articles filtered by date range and category"""
    try:
        query = {}
        
        # Date filtering
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date + "T23:59:59"
            query["publishedDate"] = date_query
        
        # Category filtering
        if category and category != 'all':
            query["category"] = category
        
        # Archive filtering
        if not include_archived:
            query["$or"] = [{"archived": {"$exists": False}}, {"archived": False}]
        
        articles = await db.articles.find(
            query,
            {"_id": 1, "id": 1, "title": 1, "category": 1, "publishedDate": 1, "image": 1, "archived": 1}
        ).sort("publishedDate", -1).skip(skip).limit(limit).to_list(limit)
        
        total = await db.articles.count_documents(query)
        
        for article in articles:
            article['id'] = str(article.get('id', article['_id']))
            if '_id' in article:
                del article['_id']
        
        return {"articles": articles, "total": total, "skip": skip, "limit": limit}
    except Exception as e:
        logger.error(f"Error getting articles by date: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/admin/articles/stats")
async def get_article_stats(auth: bool = Depends(get_admin_auth)):
    """Get comprehensive article statistics including both archive systems"""
    try:
        total_main = await db.articles.count_documents({})
        legacy_archived = await db.articles.count_documents({"archived": True})
        
        # Count articles in the archived_articles collection (new system)
        collection_archived = await db.archived_articles.count_documents({})
        
        # Total archived = legacy + collection
        total_archived = legacy_archived + collection_archived
        
        # Active = articles in main collection that are NOT archived
        active = await db.articles.count_documents({"$or": [{"archived": {"$exists": False}}, {"archived": False}]})
        
        # Total stored = active + all archived
        total_stored = active + total_archived
        
        # Get date range from main articles
        oldest = await db.articles.find_one(sort=[("publishedDate", 1)])
        newest = await db.articles.find_one(sort=[("publishedDate", -1)])
        
        # Get category breakdown (active articles only)
        pipeline = [
            {"$match": {"$or": [{"archived": {"$exists": False}}, {"archived": False}]}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        categories = await db.articles.aggregate(pipeline).to_list(20)
        
        # Get articles per day (last 7 days)
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        daily_pipeline = [
            {"$match": {"publishedDate": {"$gte": seven_days_ago}}},
            {"$group": {
                "_id": {"$substr": ["$publishedDate", 0, 10]},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": -1}}
        ]
        daily_counts = await db.articles.aggregate(daily_pipeline).to_list(7)
        
        return {
            "total": total_stored,
            "active": active,
            "archived": total_archived,
            "legacy_archived": legacy_archived,
            "collection_archived": collection_archived,
            "oldest_date": oldest.get("publishedDate") if oldest else None,
            "newest_date": newest.get("publishedDate") if newest else None,
            "by_category": {cat["_id"]: cat["count"] for cat in categories},
            "daily_counts": {day["_id"]: day["count"] for day in daily_counts},
            "storage_note": "Archived articles are preserved so shared links continue to work"
        }
    except Exception as e:
        logger.error(f"Error getting article stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# AMAZON AFFILIATE PRODUCT MANAGEMENT
# ============================================

class AffiliateProductCreate(BaseModel):
    name: str
    price: str
    url: str
    image: str
    category: str = "default"
    rating: float = 4.5
    active: bool = True

class AffiliateProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[str] = None
    url: Optional[str] = None
    image: Optional[str] = None
    category: Optional[str] = None
    rating: Optional[float] = None
    active: Optional[bool] = None

@api_router.get("/admin/affiliates")
async def get_affiliate_products(
    category: Optional[str] = None,
    active_only: bool = True,
    auth: bool = Depends(get_admin_auth)
):
    """Get all affiliate products, optionally filtered by category"""
    try:
        query = {}
        if category:
            query["category"] = category
        if active_only:
            query["active"] = {"$ne": False}
        
        products = await db.affiliate_products.find(query).sort("category", 1).to_list(100)
        
        for product in products:
            product['id'] = str(product['_id'])
            del product['_id']
        
        # Get unique categories
        categories = await db.affiliate_products.distinct("category")
        
        return {
            "success": True,
            "products": products,
            "categories": categories,
            "total": len(products)
        }
    except Exception as e:
        logger.error(f"Error getting affiliate products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/admin/cleanup-duplicate-articles")
async def cleanup_duplicate_articles(auth: bool = Depends(get_admin_auth)):
    """
    Find and remove duplicate articles based on title similarity.
    Keeps the most recent version of each article.
    """
    try:
        # Get all articles
        articles = await db.articles.find({}, {"_id": 1, "title": 1, "publishedDate": 1}).to_list(1000)
        
        logger.info(f"Checking {len(articles)} articles for duplicates...")
        
        # Group by exact title (case-insensitive)
        title_groups = {}
        for article in articles:
            title_key = article.get('title', '').lower().strip()
            if title_key not in title_groups:
                title_groups[title_key] = []
            title_groups[title_key].append(article)
        
        # Find duplicates and keep only the most recent
        duplicates_to_remove = []
        for title, group in title_groups.items():
            if len(group) > 1:
                # Sort by publishedDate descending, keep the newest
                group.sort(key=lambda x: x.get('publishedDate', ''), reverse=True)
                # Mark all but the first (newest) for deletion
                for article in group[1:]:
                    duplicates_to_remove.append(article['_id'])
        
        # Remove duplicates
        removed_count = 0
        if duplicates_to_remove:
            result = await db.articles.delete_many({"_id": {"$in": duplicates_to_remove}})
            removed_count = result.deleted_count
        
        logger.info(f"Removed {removed_count} duplicate articles")
        
        return {
            "success": True,
            "duplicates_found": len(duplicates_to_remove),
            "removed": removed_count,
            "remaining_articles": len(articles) - removed_count
        }
    except Exception as e:
        logger.error(f"Error cleaning up duplicates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/admin/check-duplicates")
async def check_duplicate_articles(auth: bool = Depends(get_admin_auth)):
    """
    Check for duplicate articles without removing them.
    Returns a list of potential duplicates.
    """
    try:
        articles = await db.articles.find({}, {"_id": 1, "title": 1, "publishedDate": 1, "source": 1}).to_list(1000)
        
        # Group by exact title
        title_groups = {}
        for article in articles:
            title_key = article.get('title', '').lower().strip()
            if title_key not in title_groups:
                title_groups[title_key] = []
            title_groups[title_key].append({
                "id": str(article['_id']),
                "title": article.get('title', ''),
                "publishedDate": article.get('publishedDate', ''),
                "source": article.get('source', '')
            })
        
        # Find groups with duplicates
        duplicates = []
        for title, group in title_groups.items():
            if len(group) > 1:
                duplicates.append({
                    "title": title[:80],
                    "count": len(group),
                    "articles": group
                })
        
        duplicates.sort(key=lambda x: -x['count'])
        
        return {
            "success": True,
            "total_articles": len(articles),
            "duplicate_groups": len(duplicates),
            "total_duplicates": sum(d['count'] - 1 for d in duplicates),
            "duplicates": duplicates[:20]  # Return top 20 duplicate groups
        }
    except Exception as e:
        logger.error(f"Error checking duplicates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/affiliates/public")
async def get_public_affiliate_products(category: Optional[str] = None):
    """Public endpoint - Get active affiliate products for display on the site"""
    try:
        query = {"active": {"$ne": False}}
        if category:
            query["category"] = category
        
        products = await db.affiliate_products.find(query).to_list(100)
        
        # Format for frontend - exclude _id
        formatted = []
        for product in products:
            formatted.append({
                "name": product.get("name"),
                "price": product.get("price"),
                "url": product.get("url"),
                "image": product.get("image"),
                "category": product.get("category", "default"),
                "rating": product.get("rating", 4.5)
            })
        
        # Group by category
        by_category = {}
        for product in formatted:
            cat = product["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(product)
        
        return {
            "success": True,
            "products": formatted,
            "by_category": by_category
        }
    except Exception as e:
        logger.error(f"Error getting public affiliate products: {e}")
        return {"success": False, "products": [], "by_category": {}}

@api_router.post("/admin/affiliates")
async def create_affiliate_product(
    product: AffiliateProductCreate,
    auth: bool = Depends(get_admin_auth)
):
    """Create a new affiliate product"""
    try:
        product_data = {
            "name": product.name,
            "price": product.price,
            "url": product.url,
            "image": product.image,
            "category": product.category,
            "rating": product.rating,
            "active": product.active,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = await db.affiliate_products.insert_one(product_data)
        
        return {
            "success": True,
            "id": str(result.inserted_id),
            "message": "Affiliate product created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating affiliate product: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/admin/affiliates/{product_id}")
async def update_affiliate_product(
    product_id: str,
    product: AffiliateProductUpdate,
    auth: bool = Depends(get_admin_auth)
):
    """Update an existing affiliate product"""
    try:
        update_data = {k: v for k, v in product.dict().items() if v is not None}
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await db.affiliate_products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {
            "success": True,
            "message": "Affiliate product updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating affiliate product: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/admin/affiliates/{product_id}")
async def delete_affiliate_product(
    product_id: str,
    auth: bool = Depends(get_admin_auth)
):
    """Delete an affiliate product"""
    try:
        result = await db.affiliate_products.delete_one({"_id": ObjectId(product_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {
            "success": True,
            "message": "Affiliate product deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting affiliate product: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/admin/affiliates/categories")
async def get_affiliate_categories(auth: bool = Depends(get_admin_auth)):
    """Get all affiliate product categories with counts"""
    try:
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        categories = await db.affiliate_products.aggregate(pipeline).to_list(50)
        
        # Default categories if none exist
        default_categories = [
            "Local News", "UK News", "Business", "Finance", "Tax", "AI & Tech", "default"
        ]
        
        category_map = {cat["_id"]: cat["count"] for cat in categories}
        
        return {
            "success": True,
            "categories": category_map,
            "available_categories": default_categories
        }
    except Exception as e:
        logger.error(f"Error getting affiliate categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# JOB BOARD ENDPOINTS
# ============================================

CHESHIRE_LOCATIONS = [
    "Macclesfield", "Wilmslow", "Knutsford", "Chester", "Warrington", 
    "Crewe", "Northwich", "Congleton", "Nantwich", "Sandbach",
    "Middlewich", "Alsager", "Poynton", "Bollington", "Handforth",
    "Remote", "Cheshire-wide"
]

JOB_CATEGORIES = [
    "Healthcare", "Technology", "Retail", "Hospitality", "Education",
    "Manufacturing", "Finance", "Construction", "Transport", "Admin",
    "Sales", "Marketing", "Engineering", "Care", "Other"
]

JOB_TYPES = ["Full-time", "Part-time", "Contract", "Temporary", "Remote", "Apprenticeship"]

@api_router.get("/jobs")
async def get_jobs(
    location: Optional[str] = None,
    category: Optional[str] = None,
    job_type: Optional[str] = None,
    limit: int = 50
):
    """Public endpoint - Get job listings"""
    try:
        query = {"active": {"$ne": False}}
        
        if location:
            query["location"] = {"$regex": location, "$options": "i"}
        if category:
            query["category"] = category
        if job_type:
            query["job_type"] = job_type
        
        jobs = await db.jobs.find(query).sort("created_at", -1).to_list(limit)
        
        # Format for frontend
        formatted = []
        for job in jobs:
            formatted.append({
                "id": str(job["_id"]),
                "title": job.get("title"),
                "company": job.get("company"),
                "location": job.get("location"),
                "job_type": job.get("job_type"),
                "salary": job.get("salary"),
                "description": job.get("description"),
                "requirements": job.get("requirements"),
                "category": job.get("category", "Other"),
                "apply_url": job.get("apply_url"),
                "apply_email": job.get("apply_email"),
                "created_at": job.get("created_at").isoformat() if job.get("created_at") else None,
                "featured": job.get("featured", False)
            })
        
        return {
            "success": True,
            "jobs": formatted,
            "total": len(formatted)
        }
    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        return {"success": False, "jobs": [], "total": 0}

@api_router.get("/jobs/meta/options")
async def get_job_options():
    """Get job categories, locations, and types for filters"""
    return {
        "locations": CHESHIRE_LOCATIONS,
        "categories": JOB_CATEGORIES,
        "job_types": JOB_TYPES
    }

@api_router.get("/jobs/packages")
async def get_job_packages():
    """Get available job listing packages and prices"""
    return {
        "packages": [
            {
                "id": "free",
                "name": "Free Listing",
                "price": 0,
                "currency": "GBP",
                "description": "14-day basic listing - perfect for trying us out",
                "features": ["Visible for 14 days", "Basic listing", "No payment required"]
            },
            {
                "id": "standard",
                "name": "Standard",
                "price": 15.00,
                "currency": "GBP",
                "description": "30-day listing on the job board",
                "features": ["Visible for 30 days", "Basic listing", "Email support"]
            },
            {
                "id": "featured",
                "name": "Featured",
                "price": 29.00,
                "currency": "GBP",
                "description": "30-day featured listing with priority placement",
                "features": ["Visible for 30 days", "Featured badge", "Top of listings", "Highlighted design"]
            },
            {
                "id": "premium",
                "name": "Premium",
                "price": 49.00,
                "currency": "GBP",
                "description": "60-day featured listing with maximum visibility",
                "features": ["Visible for 60 days", "Featured badge", "Top of listings", "Social media promotion"]
            }
        ]
    }

@api_router.post("/leads/advertise")
async def submit_advertise_lead(lead: AdvertiseLeadCreate, request: Request):
    """Public endpoint - Capture advertising enquiries from /advertise."""
    try:
        name = str(lead.name or "").strip()
        email = str(lead.email or "").strip().lower()
        tier = str(lead.tier or "").strip()
        tier_to_package_id = {
            "Local Starter": "local_starter",
            "Local Featured": "local_featured",
            "Local Partner": "local_partner",
        }
        package_id = str(lead.package_id or "").strip() or tier_to_package_id.get(tier, "")

        if len(name) < 2:
            raise HTTPException(status_code=400, detail="Please enter your name")

        allowed_tiers = {"Local Starter", "Local Featured", "Local Partner", "Starter", "Featured", "Premium"}
        if tier and tier not in allowed_tiers:
            raise HTTPException(status_code=400, detail="Invalid advertising package")

        if package_id and package_id not in ADVERTISING_PACKAGES:
            raise HTTPException(status_code=400, detail="Invalid advertising package")

        payment_token = secrets.token_urlsafe(32)
        origin_url = str(lead.origin_url or "").strip().rstrip("/") or str(request.base_url).rstrip("/")
        payment_url = f"{origin_url}/advertise/pay?token={payment_token}"

        lead_doc = {
            "name": name,
            "email": email,
            "business": str(lead.business or "").strip(),
            "budget": str(lead.budget or "").strip(),
            "package_id": package_id,
            "package_price": str(lead.package_price or "").strip(),
            "phone": str(lead.phone or "").strip(),
            "website": str(lead.website or "").strip(),
            "target_area": str(lead.target_area or "").strip(),
            "message": str(lead.message or "").strip(),
            "tier": tier,
            "source": str(lead.source or "advertise_page").strip(),
            "status": "new",
            "created_at": datetime.utcnow(),
            "submitted_at": datetime.utcnow(),
            "notify_email": "news@cheshiretoday.co.uk",
            "payment_token": payment_token,
            "payment_token_created_at": datetime.utcnow(),
        }

        result = await db.advertiser_leads.insert_one(lead_doc)
        logger.info(f"Advertising enquiry submitted: {tier or 'unspecified'} by {email}")

        notification_sent = False
        try:
            import html as _html

            html_content = f"""
            <h2>New Cheshire Today advertising enquiry</h2>
            <p><strong>Package:</strong> {_html.escape(tier or "Not selected")}</p>
            <p><strong>Name:</strong> {_html.escape(name)}</p>
            <p><strong>Email:</strong> {_html.escape(email)}</p>
            <p><strong>Business:</strong> {_html.escape(lead_doc.get("business") or "Not provided")}</p>
            <p><strong>Package price:</strong> {_html.escape(lead_doc.get("package_price") or "Not provided")}</p>
            <p><strong>Phone:</strong> {_html.escape(lead_doc.get("phone") or "Not provided")}</p>
            <p><strong>Website/Facebook:</strong> {_html.escape(lead_doc.get("website") or "Not provided")}</p>
            <p><strong>Target area:</strong> {_html.escape(lead_doc.get("target_area") or "Not provided")}</p>
            <p><strong>Source:</strong> {_html.escape(lead_doc.get("source") or "advertise_page")}</p>
            <p><strong>Message:</strong><br>{_html.escape(lead_doc.get("message") or "No message").replace(chr(10), "<br>")}</p>
            <hr>
            <p>Reply to the advertiser from news@cheshiretoday.co.uk.</p>
            """

            notification_sent = bool(email_service._send_email(
                to_email="news@cheshiretoday.co.uk",
                subject=f"New advertising enquiry — {tier or 'Cheshire Today'}",
                html_content=html_content,
            ))

            client_html_content = f"""
            <h2>Your Cheshire Today advertising request</h2>
            <p>Thanks for sending your advertising details. Please review the summary below before continuing to secure payment on Cheshire Today.</p>
            <p><strong>Package:</strong> {_html.escape(tier or "Not selected")}</p>
            <p><strong>Package price:</strong> {_html.escape(lead_doc.get("package_price") or "Not provided")}</p>
            <p><strong>Business:</strong> {_html.escape(lead_doc.get("business") or "Not provided")}</p>
            <p><strong>Website/Facebook:</strong> {_html.escape(lead_doc.get("website") or "Not provided")}</p>
            <p><strong>Target area:</strong> {_html.escape(lead_doc.get("target_area") or "Not provided")}</p>
            <p><strong>Advert message:</strong><br>{_html.escape(lead_doc.get("message") or "No message").replace(chr(10), "<br>")}</p>
            <hr>
            <h3>Where your advert can appear</h3>
            <p>Your advert can appear in Cheshire Today article advertising slots, including the desktop article sidebar and mobile in-article advert card. Local Partner campaigns may also receive selected homepage/category visibility where suitable.</p>
            <p><strong>Important:</strong> payment does not make your advert live automatically. Cheshire Today reviews adverts before publication. Your 30-day campaign starts once your advert is approved and published.</p>
            <p>If anything needs changing, reply to this email before completing payment.</p>
            <p style="margin-top:18px;">
              <a href="{_html.escape(payment_url)}" style="background:#059669;color:#ffffff;padding:12px 18px;border-radius:8px;text-decoration:none;font-weight:bold;display:inline-block;">
                Continue to secure payment
              </a>
            </p>
            <p style="font-size:13px;color:#555;">Payment link: {_html.escape(payment_url)}</p>
            """

            client_notification_sent = bool(email_service._send_email(
                to_email=email,
                subject=f"Your Cheshire Today advertising request — {tier or 'Advertising'}",
                html_content=client_html_content,
            ))

            await db.advertiser_leads.update_one(
                {"_id": result.inserted_id},
                {"$set": {
                    "notification_sent": notification_sent,
                    "client_notification_sent": client_notification_sent,
                    "notification_checked_at": datetime.utcnow()
                }}
            )
        except Exception as email_error:
            logger.error(f"Failed to send advertising enquiry notification: {str(email_error)}")
            await db.advertiser_leads.update_one(
                {"_id": result.inserted_id},
                {"$set": {"notification_sent": False, "notification_error": str(email_error), "notification_checked_at": datetime.utcnow()}}
            )

        return {
            "success": True,
            "message": "Thanks — your advertising enquiry has been received. We'll reply from news@cheshiretoday.co.uk.",
            "lead_id": str(result.inserted_id),
            "notification_sent": notification_sent,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting advertising enquiry: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not submit advertising enquiry")


@api_router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Get a single job listing"""
    try:
        job = await db.jobs.find_one({"_id": ObjectId(job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "success": True,
            "job": {
                "id": str(job["_id"]),
                "title": job.get("title"),
                "company": job.get("company"),
                "location": job.get("location"),
                "job_type": job.get("job_type"),
                "salary": job.get("salary"),
                "description": job.get("description"),
                "requirements": job.get("requirements"),
                "category": job.get("category"),
                "apply_url": job.get("apply_url"),
                "apply_email": job.get("apply_email"),
                "created_at": job.get("created_at").isoformat() if job.get("created_at") else None,
                "featured": job.get("featured", False)
            }
        }
    except Exception as e:
        logger.error(f"Error getting job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/jobs/submit")
async def submit_job(job: JobSubmission):
    """Public endpoint - Submit a job listing for approval"""
    try:
        # Validate email format
        import re
        if not re.match(r"[^@]+@[^@]+\.[^@]+", job.contact_email):
            raise HTTPException(status_code=400, detail="Invalid contact email format")
        
        job_doc = {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "job_type": job.job_type,
            "salary": job.salary,
            "description": job.description,
            "requirements": job.requirements,
            "category": job.category,
            "apply_url": job.apply_url,
            "apply_email": job.apply_email,
            "contact_name": job.contact_name,
            "contact_email": job.contact_email,
            "contact_phone": job.contact_phone,
            "status": "pending",  # pending, approved, rejected
            "active": False,  # Not visible until approved
            "featured": False,
            "created_at": datetime.utcnow(),
            "submitted_at": datetime.utcnow()
        }
        
        result = await db.jobs.insert_one(job_doc)
        logger.info(f"Job submitted for approval: {job.title} at {job.company} by {job.contact_email}")
        
        return {
            "success": True,
            "message": "Your job listing has been submitted for review. We'll notify you by email once it's approved.",
            "job_id": str(result.inserted_id)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# STRIPE PAYMENT FOR JOB LISTINGS
# ============================================

class JobPaymentRequest(BaseModel):
    package_id: str  # standard, featured, premium
    origin_url: str  # Frontend origin for success/cancel URLs
    # Job details to store temporarily
    title: str
    company: str
    location: str
    job_type: str
    salary: Optional[str] = None
    description: str
    requirements: Optional[str] = None
    category: str = "Other"
    apply_url: Optional[str] = None
    apply_email: Optional[str] = None
    contact_name: str
    contact_email: str
    contact_phone: Optional[str] = None

class AdvertisingPaymentRequest(BaseModel):
    package_id: str
    origin_url: str
    existing_lead_id: Optional[str] = None
    name: str
    business: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    website: Optional[str] = None
    target_area: Optional[str] = None
    message: Optional[str] = None

@api_router.post("/advertising/checkout")
async def create_advertising_checkout(request: Request, payment: AdvertisingPaymentRequest):
    """Create a Stripe checkout session for advertising packages."""
    try:
        package_id = str(payment.package_id or "").strip()
        if package_id not in ADVERTISING_PACKAGES:
            raise HTTPException(status_code=400, detail="Invalid advertising package selected")

        package = ADVERTISING_PACKAGES[package_id]
        amount = package["price"]

        name = str(payment.name or "").strip()
        business = str(payment.business or "").strip()
        email = str(payment.email or "").strip().lower()
        website = str(payment.website or "").strip()

        if len(name) < 2:
            raise HTTPException(status_code=400, detail="Please enter your name")

        if website and not website.startswith(("https://", "http://")):
            website = "https://" + website

        lead_doc = {
            "name": name,
            "email": email,
            "business": business,
            "package_id": package_id,
            "tier": package["name"],
            "package_price": f"£{amount:.0f} / 30 days",
            "phone": str(payment.phone or "").strip(),
            "website": website,
            "target_area": str(payment.target_area or "").strip(),
            "message": str(payment.message or "").strip(),
            "source": "advertise_checkout",
            "status": "payment_pending",
            "payment_status": "pending",
            "active": False,
            "submitted_at": datetime.utcnow(),
        }

        existing_lead_id = str(payment.existing_lead_id or "").strip()
        if existing_lead_id:
            existing = await db.advertiser_leads.find_one({"_id": ObjectId(existing_lead_id)})
            if not existing:
                raise HTTPException(status_code=404, detail="Advertising enquiry not found")
            await db.advertiser_leads.update_one(
                {"_id": ObjectId(existing_lead_id)},
                {"$set": {**lead_doc, "payment_started_at": datetime.utcnow()}}
            )
            lead_id = existing_lead_id
        else:
            lead_doc["created_at"] = datetime.utcnow()
            result = await db.advertiser_leads.insert_one(lead_doc)
            lead_id = str(result.inserted_id)

        stripe.api_key = STRIPE_API_KEY

        success_url = f"{payment.origin_url}/advertise/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{payment.origin_url}/advertise"

        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "gbp",
                    "unit_amount": int(round(amount * 100)),
                    "product_data": {
                        "name": f"Cheshire Today advertising — {package['name']}",
                        "description": "One 30-day sponsored advertising campaign, pending Cheshire Today review before publication",
                    },
                },
                "quantity": 1,
            }],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "type": "advertising",
                "advertiser_lead_id": lead_id,
                "package_id": package_id,
                "contact_email": email,
            }
        )

        await db.payment_transactions.insert_one({
            "session_id": session.id,
            "type": "advertising",
            "advertiser_lead_id": lead_id,
            "amount": amount,
            "currency": "gbp",
            "package_id": package_id,
            "contact_email": email,
            "payment_status": "initiated",
            "created_at": datetime.utcnow(),
        })

        await db.advertiser_leads.update_one(
            {"_id": ObjectId(lead_id)},
            {"$set": {"stripe_session_id": session.id}}
        )

        return {
            "success": True,
            "checkout_url": session.url,
            "session_id": session.id,
            "lead_id": lead_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating advertising checkout: {e}")
        raise HTTPException(status_code=500, detail="Could not create advertising checkout")


class AdvertisingLeadCheckoutRequest(BaseModel):
    origin_url: str


@api_router.post("/advertising/checkout/from-lead/{payment_token}")
async def create_advertising_checkout_from_lead(payment_token: str, request: Request, payload: AdvertisingLeadCheckoutRequest):
    """Create a Stripe checkout session from a saved advertising enquiry."""
    try:
        clean_token = str(payment_token or "").strip()
        if not clean_token:
            raise HTTPException(status_code=400, detail="Missing payment token")

        lead = await db.advertiser_leads.find_one({"payment_token": clean_token})
        if not lead:
            raise HTTPException(status_code=404, detail="Advertising payment link not found")

        if lead.get("payment_status") == "paid":
            raise HTTPException(status_code=400, detail="This advertising enquiry has already been paid")

        tier_to_package_id = {
            "Local Starter": "local_starter",
            "Local Featured": "local_featured",
            "Local Partner": "local_partner",
        }
        package_id = str(lead.get("package_id") or "").strip() or tier_to_package_id.get(str(lead.get("tier") or "").strip(), "")
        if package_id not in ADVERTISING_PACKAGES:
            raise HTTPException(status_code=400, detail="Advertising package is missing from this enquiry")

        payment = AdvertisingPaymentRequest(
            package_id=package_id,
            origin_url=payload.origin_url,
            existing_lead_id=str(lead["_id"]),
            name=lead.get("name") or "Advertiser",
            business=lead.get("business") or "",
            email=lead.get("email") or "news@cheshiretoday.co.uk",
            phone=lead.get("phone") or "",
            website=lead.get("website") or "",
            target_area=lead.get("target_area") or "",
            message=lead.get("message") or "",
        )

        await db.advertiser_leads.update_one(
            {"_id": lead["_id"]},
            {"$set": {"payment_link_clicked_at": datetime.utcnow()}}
        )

        return await create_advertising_checkout(request, payment)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating advertising checkout from lead: {e}")
        raise HTTPException(status_code=500, detail="Could not start advertising payment")


async def send_advertising_payment_confirmation_email(lead_id: str):
    """Send one client email after an advertising payment is confirmed."""
    try:
        if not ObjectId.is_valid(str(lead_id or "")):
            return False

        oid = ObjectId(lead_id)
        claim = await db.advertiser_leads.update_one(
            {
                "_id": oid,
                "payment_confirmation_sent": {"$ne": True},
                "payment_confirmation_sending": {"$ne": True},
            },
            {"$set": {"payment_confirmation_sending": True, "payment_confirmation_started_at": datetime.utcnow()}}
        )

        if claim.modified_count == 0:
            return False

        lead = await db.advertiser_leads.find_one({"_id": oid})
        if not lead:
            return False

        email = str(lead.get("email") or "").strip()
        if not email:
            await db.advertiser_leads.update_one(
                {"_id": oid},
                {"$set": {
                    "payment_confirmation_sent": False,
                    "payment_confirmation_error": "Missing client email",
                    "payment_confirmation_checked_at": datetime.utcnow(),
                }, "$unset": {"payment_confirmation_sending": ""}}
            )
            return False

        import html as _html

        tier = str(lead.get("tier") or lead.get("package_tier") or "Advertising package").strip()
        business = str(lead.get("business") or lead.get("name") or "your business").strip()
        package_price = str(lead.get("package_price") or "").strip()
        target_area = str(lead.get("target_area") or "").strip()
        website = str(lead.get("website") or "").strip()

        html_content = f"""
        <h2>Payment received — Cheshire Today advertising</h2>
        <p>Thank you. We have received your payment for your Cheshire Today advertising package.</p>
        <p><strong>Package:</strong> {_html.escape(tier)}</p>
        <p><strong>Package price:</strong> {_html.escape(package_price or "Paid")}</p>
        <p><strong>Business:</strong> {_html.escape(business)}</p>
        <p><strong>Website/Facebook:</strong> {_html.escape(website or "Not provided")}</p>
        <p><strong>Target area:</strong> {_html.escape(target_area or "Cheshire")}</p>
        <hr>
        <h3>What happens next</h3>
        <p>Your advert is now marked as paid and pending review. Cheshire Today will check the advert details before it goes live.</p>
        <p>Your 30-day campaign starts once the advert is approved and published, not from the moment of payment.</p>
        <p>If we need anything else, we will contact you by email. If you want to send a logo, image, updated wording, or any change to your website link, reply to this email.</p>
        <p>Thank you for advertising with Cheshire Today.</p>
        """

        sent = bool(email_service._send_email(
            to_email=email,
            subject="Payment received — Cheshire Today advertising",
            html_content=html_content,
        ))

        await db.advertiser_leads.update_one(
            {"_id": oid},
            {"$set": {
                "payment_confirmation_sent": sent,
                "payment_confirmation_checked_at": datetime.utcnow(),
                "payment_confirmation_error": "" if sent else "Email service returned false",
            }, "$unset": {"payment_confirmation_sending": ""}}
        )

        return sent
    except Exception as email_error:
        logger.error(f"Failed to send advertising payment confirmation email: {str(email_error)}")
        try:
            if ObjectId.is_valid(str(lead_id or "")):
                await db.advertiser_leads.update_one(
                    {"_id": ObjectId(lead_id)},
                    {"$set": {
                        "payment_confirmation_sent": False,
                        "payment_confirmation_error": str(email_error),
                        "payment_confirmation_checked_at": datetime.utcnow(),
                    }, "$unset": {"payment_confirmation_sending": ""}}
                )
        except Exception:
            pass
        return False


@api_router.get("/advertising/payment-status/{session_id}")
async def get_advertising_payment_status(session_id: str, request: Request):
    """Check the status of an advertising payment."""
    try:
        stripe.api_key = STRIPE_API_KEY

        session = stripe.checkout.Session.retrieve(session_id)
        session_status = getattr(session, "status", None)
        payment_status = getattr(session, "payment_status", None)

        transaction = await db.payment_transactions.find_one({"session_id": session_id, "type": "advertising"})
        if not transaction:
            raise HTTPException(status_code=404, detail="Payment not found")

        if transaction.get("payment_status") == "completed":
            existing_lead_id = transaction.get("advertiser_lead_id")
            if existing_lead_id:
                await send_advertising_payment_confirmation_email(str(existing_lead_id))

            return {
                "success": True,
                "status": "completed",
                "payment_status": "paid",
                "advertiser_lead_id": existing_lead_id,
                "message": "Payment already processed. Your advert is pending review."
            }

        if payment_status == "paid":
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {"payment_status": "completed", "completed_at": datetime.utcnow()}}
            )

            lead_id = transaction.get("advertiser_lead_id")
            await db.advertiser_leads.update_one(
                {"_id": ObjectId(lead_id)},
                {"$set": {
                    "status": "paid_pending_review",
                    "payment_status": "paid",
                    "paid_at": datetime.utcnow()
                }}
            )
            await send_advertising_payment_confirmation_email(str(lead_id))

            return {
                "success": True,
                "status": "completed",
                "payment_status": "paid",
                "advertiser_lead_id": lead_id,
                "message": "Payment successful. Your advert has been received and is pending Cheshire Today review."
            }

        if session_status == "expired":
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {"payment_status": "expired"}}
            )
            await db.advertiser_leads.update_one(
                {"stripe_session_id": session_id},
                {"$set": {"status": "payment_expired", "payment_status": "expired"}}
            )
            return {
                "success": False,
                "status": "expired",
                "payment_status": "expired",
                "message": "Payment session expired. Please try again."
            }

        return {
            "success": False,
            "status": session_status,
            "payment_status": payment_status,
            "message": "Payment is being processed..."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking advertising payment status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/jobs/checkout")
async def create_job_checkout(request: Request, payment: JobPaymentRequest):
    """Create a Stripe checkout session for job posting (or submit free listing directly)"""
    try:
        # Validate package
        if payment.package_id not in JOB_POSTING_PACKAGES:
            raise HTTPException(status_code=400, detail="Invalid package selected")
        
        package = JOB_POSTING_PACKAGES[payment.package_id]
        amount = package["price"]
        
        # Handle FREE listings - no payment needed
        if amount == 0 or payment.package_id == "free":
            job_doc = {
                "title": payment.title,
                "company": payment.company,
                "location": payment.location,
                "job_type": payment.job_type,
                "salary": payment.salary,
                "description": payment.description,
                "requirements": payment.requirements,
                "category": payment.category,
                "apply_url": payment.apply_url,
                "apply_email": payment.apply_email,
                "contact_name": payment.contact_name,
                "contact_email": payment.contact_email,
                "contact_phone": payment.contact_phone,
                "package_id": "free",
                "status": "pending",  # Goes straight to pending approval
                "payment_status": "free",
                "active": False,
                "featured": False,
                "duration_days": 14,
                "created_at": datetime.utcnow(),
                "submitted_at": datetime.utcnow()
            }
            
            result = await db.jobs.insert_one(job_doc)
            logger.info(f"Free job submitted: {payment.title} at {payment.company} by {payment.contact_email}")
            
            return {
                "success": True,
                "free_listing": True,
                "job_id": str(result.inserted_id),
                "message": "Your free job listing has been submitted for review!"
            }
        
        # PAID listings - use Stripe
        # Initialize Stripe
        host_url = str(request.base_url).rstrip('/')
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
        
        # Build success and cancel URLs from provided origin
        success_url = f"{payment.origin_url}/jobs/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{payment.origin_url}/jobs/post"
        
        # Create a pending job record and get its ID for metadata
        job_doc = {
            "title": payment.title,
            "company": payment.company,
            "location": payment.location,
            "job_type": payment.job_type,
            "salary": payment.salary,
            "description": payment.description,
            "requirements": payment.requirements,
            "category": payment.category,
            "apply_url": payment.apply_url,
            "apply_email": payment.apply_email,
            "contact_name": payment.contact_name,
            "contact_email": payment.contact_email,
            "contact_phone": payment.contact_phone,
            "package_id": payment.package_id,
            "status": "payment_pending",
            "payment_status": "pending",
            "active": False,
            "featured": package.get("featured", False),
            "created_at": datetime.utcnow()
        }
        
        job_result = await db.jobs.insert_one(job_doc)
        job_id = str(job_result.inserted_id)
        
        # Create checkout session
        checkout_request = CheckoutSessionRequest(
            amount=amount,
            currency="gbp",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "job_id": job_id,
                "package_id": payment.package_id,
                "contact_email": payment.contact_email
            }
        )
        
        session = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Create payment transaction record
        await db.payment_transactions.insert_one({
            "session_id": session.session_id,
            "job_id": job_id,
            "amount": amount,
            "currency": "gbp",
            "package_id": payment.package_id,
            "contact_email": payment.contact_email,
            "payment_status": "initiated",
            "created_at": datetime.utcnow()
        })
        
        # Update job with session ID
        await db.jobs.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"stripe_session_id": session.session_id}}
        )
        
        logger.info(f"Created checkout session {session.session_id} for job {job_id}")
        
        return {
            "success": True,
            "checkout_url": session.url,
            "session_id": session.session_id,
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating job checkout: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/jobs/payment-status/{session_id}")
async def get_job_payment_status(session_id: str, request: Request):
    """Check the status of a job payment"""
    try:
        # Initialize Stripe
        host_url = str(request.base_url).rstrip('/')
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
        
        # Get checkout status from Stripe
        status = await stripe_checkout.get_checkout_status(session_id)
        
        # Find the payment transaction
        transaction = await db.payment_transactions.find_one({"session_id": session_id})
        if not transaction:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Check if already processed
        if transaction.get("payment_status") == "completed":
            return {
                "success": True,
                "status": "completed",
                "payment_status": "paid",
                "job_id": transaction.get("job_id"),
                "message": "Payment already processed"
            }
        
        # Update based on Stripe status
        if status.payment_status == "paid":
            # Mark payment as completed
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {"payment_status": "completed", "completed_at": datetime.utcnow()}}
            )
            
            # Update job to pending approval (paid but needs admin review)
            job_id = transaction.get("job_id")
            package_id = transaction.get("package_id")
            package = JOB_POSTING_PACKAGES.get(package_id, {})
            
            await db.jobs.update_one(
                {"_id": ObjectId(job_id)},
                {"$set": {
                    "status": "pending",  # Now pending admin approval
                    "payment_status": "paid",
                    "featured": package.get("featured", False),
                    "paid_at": datetime.utcnow()
                }}
            )
            
            logger.info(f"Payment completed for job {job_id}")
            
            return {
                "success": True,
                "status": "completed",
                "payment_status": "paid",
                "job_id": job_id,
                "message": "Payment successful! Your job is now pending approval."
            }
        elif status.status == "expired":
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {"payment_status": "expired"}}
            )
            await db.jobs.update_one(
                {"stripe_session_id": session_id},
                {"$set": {"status": "payment_expired", "payment_status": "expired"}}
            )
            return {
                "success": False,
                "status": "expired",
                "payment_status": "expired",
                "message": "Payment session expired. Please try again."
            }
        else:
            return {
                "success": False,
                "status": status.status,
                "payment_status": status.payment_status,
                "message": "Payment is being processed..."
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking payment status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks using Stripe's official signature verification."""
    try:
        body = await request.body()
        signature = request.headers.get("Stripe-Signature")

        if not STRIPE_WEBHOOK_SECRET:
            logger.error("Stripe webhook secret is not configured")
            raise HTTPException(status_code=500, detail="Stripe webhook secret is not configured")

        try:
            event = stripe.Webhook.construct_event(
                payload=body,
                sig_header=signature,
                secret=STRIPE_WEBHOOK_SECRET,
            )
        except ValueError as e:
            logger.warning(f"Stripe webhook invalid payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid Stripe webhook payload")
        except stripe.error.SignatureVerificationError as e:
            logger.warning(f"Stripe webhook signature verification failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid Stripe webhook signature")

        event_type = str(event.get("type") or "")
        session = event.get("data", {}).get("object", {}) or {}
        session_id = str(session.get("id") or "")
        payment_status = str(session.get("payment_status") or "")
        metadata = dict(session.get("metadata") or {})

        logger.info(f"Stripe webhook: {event_type} for session {session_id}")

        if event_type == "checkout.session.completed" and payment_status == "paid" and session_id:
            transaction = await db.payment_transactions.find_one({"session_id": session_id})
            if transaction and transaction.get("payment_status") != "completed":
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {"payment_status": "completed", "completed_at": datetime.utcnow()}}
                )

                payment_type = metadata.get("type") or transaction.get("type")

                if payment_type == "advertising":
                    lead_id = metadata.get("advertiser_lead_id") or transaction.get("advertiser_lead_id")
                    if lead_id:
                        await db.advertiser_leads.update_one(
                            {"_id": ObjectId(lead_id)},
                            {"$set": {
                                "status": "paid_pending_review",
                                "payment_status": "paid",
                                "paid_at": datetime.utcnow()
                            }}
                        )
                        await send_advertising_payment_confirmation_email(str(lead_id))
                        logger.info(f"Webhook: Updated advertiser lead {lead_id} to paid pending review")
                else:
                    job_id = metadata.get("job_id") or transaction.get("job_id")
                    if job_id:
                        package_id = metadata.get("package_id") or transaction.get("package_id")
                        package = JOB_POSTING_PACKAGES.get(package_id, {})

                        await db.jobs.update_one(
                            {"_id": ObjectId(job_id)},
                            {"$set": {
                                "status": "pending",
                                "payment_status": "paid",
                                "featured": package.get("featured", False),
                                "paid_at": datetime.utcnow()
                            }}
                        )
                        logger.info(f"Webhook: Updated job {job_id} to pending after payment")

        return {"received": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        return {"received": True, "error": str(e)}

@api_router.get("/admin/jobs")
async def get_admin_jobs(auth: bool = Depends(get_admin_auth)):
    """Admin endpoint - Get all job listings"""
    try:
        jobs = await db.jobs.find({}).sort("created_at", -1).to_list(500)
        
        formatted = []
        for job in jobs:
            formatted.append({
                "id": str(job["_id"]),
                "title": job.get("title"),
                "company": job.get("company"),
                "location": job.get("location"),
                "job_type": job.get("job_type"),
                "salary": job.get("salary"),
                "description": job.get("description")[:200] + "..." if job.get("description") and len(job.get("description", "")) > 200 else job.get("description"),
                "category": job.get("category"),
                "active": job.get("active", True),
                "featured": job.get("featured", False),
                "status": job.get("status", "approved"),  # pending, approved, rejected
                "contact_name": job.get("contact_name"),
                "contact_email": job.get("contact_email"),
                "contact_phone": job.get("contact_phone"),
                "apply_url": job.get("apply_url"),
                "apply_email": job.get("apply_email"),
                "created_at": job.get("created_at").isoformat() if job.get("created_at") else None
            })
        
        # Count pending submissions
        pending_count = len([j for j in formatted if j.get("status") == "pending"])
        
        return {
            "success": True,
            "jobs": formatted,
            "total": len(formatted),
            "pending_count": pending_count
        }
    except Exception as e:
        logger.error(f"Error getting admin jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/admin/jobs")
async def create_job(job: JobCreate, auth: bool = Depends(get_admin_auth)):
    """Admin endpoint - Create a new job listing"""
    try:
        job_doc = {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "job_type": job.job_type,
            "salary": job.salary,
            "description": job.description,
            "requirements": job.requirements,
            "category": job.category,
            "apply_url": job.apply_url,
            "apply_email": job.apply_email,
            "active": True,
            "featured": False,
            "created_at": datetime.utcnow()
        }
        
        result = await db.jobs.insert_one(job_doc)
        logger.info(f"Created job: {job.title} at {job.company}")
        
        return {
            "success": True,
            "message": "Job created successfully",
            "job_id": str(result.inserted_id)
        }
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/admin/jobs/{job_id}")
async def update_job(job_id: str, job: JobCreate, auth: bool = Depends(get_admin_auth)):
    """Admin endpoint - Update a job listing"""
    try:
        result = await db.jobs.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "job_type": job.job_type,
                "salary": job.salary,
                "description": job.description,
                "requirements": job.requirements,
                "category": job.category,
                "apply_url": job.apply_url,
                "apply_email": job.apply_email,
                "updated_at": datetime.utcnow()
            }}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {"success": True, "message": "Job updated successfully"}
    except Exception as e:
        logger.error(f"Error updating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/admin/jobs/{job_id}")
async def delete_job(job_id: str, auth: bool = Depends(get_admin_auth)):
    """Admin endpoint - Delete a job listing"""
    try:
        result = await db.jobs.delete_one({"_id": ObjectId(job_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {"success": True, "message": "Job deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/admin/jobs/{job_id}/toggle")
async def toggle_job_active(job_id: str, auth: bool = Depends(get_admin_auth)):
    """Admin endpoint - Toggle job active status"""
    try:
        job = await db.jobs.find_one({"_id": ObjectId(job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        new_status = not job.get("active", True)
        await db.jobs.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"active": new_status}}
        )
        
        return {"success": True, "active": new_status}
    except Exception as e:
        logger.error(f"Error toggling job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/admin/jobs/{job_id}/feature")
async def toggle_job_featured(job_id: str, auth: bool = Depends(get_admin_auth)):
    """Admin endpoint - Toggle job featured status"""
    try:
        job = await db.jobs.find_one({"_id": ObjectId(job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        new_status = not job.get("featured", False)
        await db.jobs.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"featured": new_status}}
        )
        
        return {"success": True, "featured": new_status}
    except Exception as e:
        logger.error(f"Error featuring job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/admin/jobs/{job_id}/approve")
async def approve_job(job_id: str, auth: bool = Depends(get_admin_auth)):
    """Admin endpoint - Approve a pending job submission"""
    try:
        job = await db.jobs.find_one({"_id": ObjectId(job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        await db.jobs.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"status": "approved", "active": True, "approved_at": datetime.utcnow()}}
        )
        
        logger.info(f"Job approved: {job.get('title')} - Contact: {job.get('contact_email')}")
        
        # Send approval email notification
        email_sent = False
        contact_email = job.get("contact_email")
        if contact_email:
            try:
                email_sent = email_service.send_job_approved_email(
                    to_email=contact_email,
                    contact_name=job.get("contact_name", "Employer"),
                    job_title=job.get("title"),
                    company=job.get("company")
                )
                if email_sent:
                    logger.info(f"Approval email sent to {contact_email}")
            except Exception as email_error:
                logger.error(f"Failed to send approval email: {email_error}")
        
        return {
            "success": True, 
            "message": f"Job '{job.get('title')}' has been approved and is now live",
            "contact_email": contact_email,
            "email_sent": email_sent
        }
    except Exception as e:
        logger.error(f"Error approving job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class RejectJobRequest(BaseModel):
    reason: Optional[str] = None

@api_router.post("/admin/jobs/{job_id}/reject")
async def reject_job(job_id: str, request_body: RejectJobRequest = None, auth: bool = Depends(get_admin_auth)):
    """Admin endpoint - Reject a pending job submission"""
    try:
        job = await db.jobs.find_one({"_id": ObjectId(job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        reason = request_body.reason if request_body else None
        
        await db.jobs.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"status": "rejected", "active": False, "rejected_at": datetime.utcnow(), "rejection_reason": reason}}
        )
        
        logger.info(f"Job rejected: {job.get('title')} - Reason: {reason}")
        
        # Send rejection email notification
        email_sent = False
        contact_email = job.get("contact_email")
        if contact_email:
            try:
                email_sent = email_service.send_job_rejected_email(
                    to_email=contact_email,
                    contact_name=job.get("contact_name", "Employer"),
                    job_title=job.get("title"),
                    company=job.get("company"),
                    reason=reason
                )
                if email_sent:
                    logger.info(f"Rejection email sent to {contact_email}")
            except Exception as email_error:
                logger.error(f"Failed to send rejection email: {email_error}")
        
        return {
            "success": True, 
            "message": f"Job '{job.get('title')}' has been rejected",
            "contact_email": contact_email,
            "email_sent": email_sent
        }
    except Exception as e:
        logger.error(f"Error rejecting job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# FACEBOOK AUTO-POSTING ENDPOINTS
# ============================================

from app.facebook_service import facebook_service
from app.twitter_service import twitter_service

# ============================================
# TWITTER/X ENDPOINTS
# ============================================

@api_router.get("/twitter/status")
async def check_twitter_status():
    """Check Twitter integration status"""
    return {
        "configured": twitter_service.is_configured,
        "message": "Twitter is configured and ready" if twitter_service.is_configured else "Twitter credentials not set"
    }

@api_router.post("/twitter/post-single")
async def post_single_to_twitter(article_id: str, auth: bool = Depends(get_admin_auth)):
    """Post a specific article to Twitter"""
    try:
        if not twitter_service.is_configured:
            return {"success": False, "error": "Twitter not configured"}
        
        # Check if already posted in last 24 hours
        window_start = datetime.now(timezone.utc) - timedelta(hours=24)
        already_posted = await db.twitter_post_log.find_one({
            "article_id": article_id,
            "posted_at": {"$gte": window_start}
        })
        
        if already_posted:
            return {"success": False, "error": "Article already posted to Twitter in last 24 hours"}
        
        # Get article
        from bson import ObjectId
        article = await db.articles.find_one({"_id": ObjectId(article_id)})
        if not article:
            return {"success": False, "error": "Article not found"}
        
        article['id'] = str(article['_id'])
        del article['_id']
        
        result = await twitter_service.post_article(article)
        
        if result.get("success"):
            await db.twitter_post_log.insert_one({
                "article_id": article_id,
                "tweet_id": result.get("tweet_id"),
                "title": article.get("title", "")[:100],
                "posted_at": datetime.now(timezone.utc)
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Twitter post error: {str(e)}")
        return {"success": False, "error": str(e)}

@api_router.post("/twitter/trigger-scheduled")
async def trigger_twitter_scheduled_post(auth: bool = Depends(get_admin_auth)):
    """Manually trigger Twitter scheduled post (posts 3 articles)"""
    try:
        if not twitter_service.is_configured:
            return {"success": False, "error": "Twitter not configured"}
        
        # Use lock to prevent concurrent posts
        now = datetime.now(timezone.utc)
        five_minutes_ago = now - timedelta(minutes=5)
        lock_id = str(uuid4())
        
        await db.scheduler_locks.update_one(
            {"job": "twitter_post"},
            {"$setOnInsert": {"job": "twitter_post", "locked_at": None, "lock_id": None}},
            upsert=True
        )
        
        lock_result = await db.scheduler_locks.find_one_and_update(
            {
                "job": "twitter_post",
                "$or": [
                    {"locked_at": None},
                    {"locked_at": {"$lt": five_minutes_ago}}
                ]
            },
            {"$set": {"locked_at": now, "lock_id": lock_id}},
            return_document=True
        )
        
        if lock_result is None or lock_result.get("lock_id") != lock_id:
            return {"success": False, "posted": 0, "message": "Twitter post already in progress"}
        
        try:
            # Get articles not posted in last 24 hours
            window_start = datetime.now(timezone.utc) - timedelta(hours=24)
            recently_posted = await db.twitter_post_log.find({
                "posted_at": {"$gte": window_start}
            }).to_list(100)
            
            posted_article_ids = set(p.get('article_id') for p in recently_posted)
            
            # Get recent articles
            all_articles = await db.articles.find(
                {},
                {"_id": 1, "title": 1, "content": 1, "category": 1, "image": 1}
            ).sort("publishedDate", -1).limit(30).to_list(30)
            
            articles = []
            for article in all_articles:
                article_id = str(article['_id'])
                if article_id not in posted_article_ids:
                    article['id'] = article_id
                    del article['_id']
                    articles.append(article)
                    if len(articles) >= 1:  # Only 1 article (Free tier limit)
                        break
            
            if not articles:
                await db.scheduler_locks.delete_one({"job": "twitter_post"})
                return {"success": True, "posted": 0, "message": "No new articles to post"}
            
            result = await twitter_service.post_multiple_articles(articles, limit=1)  # 1 article
            
            # Log posted articles
            for i, article in enumerate(articles[:result.get('posted', 0)]):
                if result.get('results') and i < len(result['results']):
                    tweet_result = result['results'][i]
                    if tweet_result.get('success'):
                        await db.twitter_post_log.insert_one({
                            "article_id": article.get('id'),
                            "tweet_id": tweet_result.get('tweet_id'),
                            "title": article.get('title', '')[:100],
                            "posted_at": datetime.now(timezone.utc)
                        })
            
            await db.scheduler_locks.delete_one({"job": "twitter_post"})
            
            return {
                "success": result.get("success", False),
                "posted": result.get("posted", 0),
                "message": f"Posted {result.get('posted', 0)} articles to Twitter",
                "results": result.get("results", [])
            }
            
        except Exception as e:
            await db.scheduler_locks.delete_one({"job": "twitter_post"})
            raise e
        
    except Exception as e:
        logger.error(f"Twitter trigger error: {str(e)}")
        return {"success": False, "error": str(e)}

# ============================================
# FACEBOOK ENDPOINTS  
# ============================================

@api_router.get("/facebook/status")
async def check_facebook_status():
    """Check Facebook integration status and token validity"""
    import os
    
    # Check if configured
    token_set = bool(os.environ.get('FACEBOOK_PAGE_ACCESS_TOKEN'))
    page_id_set = bool(os.environ.get('FACEBOOK_PAGE_ID'))
    
    if not token_set or not page_id_set:
        return {
            "configured": False,
            "token_set": token_set,
            "page_id_set": page_id_set,
            "message": "Set FACEBOOK_PAGE_ACCESS_TOKEN and FACEBOOK_PAGE_ID in environment"
        }
    
    # Verify token is valid
    verification = await facebook_service.verify_token()
    
    return {
        "configured": True,
        "token_valid": verification.get("valid", False),
        "page_name": verification.get("page_name"),
        "page_id": verification.get("page_id"),
        "followers": verification.get("followers"),
        "page_url": verification.get("page_url"),
        "error": verification.get("error")
    }


# ============================================================================
# FACEBOOK OAUTH (Long-Lived Tokens)
# ============================================================================

from app.facebook_oauth import facebook_oauth

@api_router.get("/facebook/oauth/status")
async def facebook_oauth_status(auth: bool = Depends(get_admin_auth)):
    """Check if Facebook OAuth is configured"""
    return {
        "configured": facebook_oauth.is_configured,
        "app_id_set": bool(os.environ.get('FACEBOOK_APP_ID')),
        "app_secret_set": bool(os.environ.get('FACEBOOK_APP_SECRET')),
        "redirect_uri": facebook_oauth.redirect_uri if facebook_oauth.is_configured else None,
        "message": "Set FACEBOOK_APP_ID and FACEBOOK_APP_SECRET to enable OAuth" if not facebook_oauth.is_configured else "OAuth is configured"
    }


@api_router.get("/facebook/oauth/authorize")
async def facebook_oauth_authorize(auth: bool = Depends(get_admin_auth)):
    """
    Get the Facebook OAuth authorization URL.
    Redirect user to this URL to start the OAuth flow.
    """
    if not facebook_oauth.is_configured:
        return {
            "success": False,
            "error": "Facebook OAuth not configured. Set FACEBOOK_APP_ID and FACEBOOK_APP_SECRET in environment."
        }
    
    import secrets
    state = secrets.token_hex(16)
    
    # Store state in session/db for verification (simplified - store in memory for now)
    # In production, use secure session storage
    
    return {
        "success": True,
        "authorization_url": facebook_oauth.get_authorization_url(state),
        "state": state,
        "instructions": "Redirect to authorization_url. After approval, Facebook will redirect to /api/facebook/oauth/callback with a code parameter."
    }


@api_router.get("/facebook/oauth/callback")
async def facebook_oauth_callback(code: str = None, state: str = None, error: str = None):
    """
    OAuth callback endpoint - Facebook redirects here after user authorizes.
    Exchanges the code for a long-lived page access token.
    """
    from fastapi.responses import HTMLResponse
    
    if error:
        return HTMLResponse(f"""
            <html><body>
            <h1>Facebook Authorization Failed</h1>
            <p>Error: {error}</p>
            <p><a href="/admin">Return to Admin</a></p>
            </body></html>
        """)
    
    if not code:
        return HTMLResponse("""
            <html><body>
            <h1>Facebook Authorization Failed</h1>
            <p>No authorization code received.</p>
            <p><a href="/admin">Return to Admin</a></p>
            </body></html>
        """)
    
    # Exchange code for token
    result = await facebook_oauth.exchange_code_for_token(code)
    
    if result.get("success"):
        # Success! Show the token for manual configuration
        # In production, you would automatically save this to secure storage
        token = result.get("access_token")
        page_name = result.get("page_name", "Unknown")
        
        return HTMLResponse(f"""
            <html><body style="font-family: Arial; padding: 20px; max-width: 800px; margin: 0 auto;">
            <h1 style="color: green;">✅ Facebook Authorization Successful!</h1>
            <p><strong>Page:</strong> {page_name}</p>
            <p><strong>Token Type:</strong> Long-lived Page Access Token (Never Expires)</p>
            <hr>
            <h3>Next Steps:</h3>
            <ol>
                <li>Copy the token below</li>
                <li>Add it to your production environment variables:
                    <br><code>FACEBOOK_PAGE_ACCESS_TOKEN={token[:50]}...</code>
                </li>
                <li>Restart your application</li>
            </ol>
            <h4>Your Page Access Token:</h4>
            <textarea readonly style="width: 100%; height: 100px; font-family: monospace; font-size: 12px;">{token}</textarea>
            <br><br>
            <a href="/admin" style="padding: 10px 20px; background: #1877f2; color: white; text-decoration: none; border-radius: 5px;">Return to Admin</a>
            </body></html>
        """)
    else:
        return HTMLResponse(f"""
            <html><body>
            <h1 style="color: red;">❌ Token Exchange Failed</h1>
            <p>Error: {result.get('error', 'Unknown error')}</p>
            <p><a href="/admin">Return to Admin</a></p>
            </body></html>
        """)


@api_router.post("/facebook/oauth/validate-token")
async def validate_facebook_token(auth: bool = Depends(get_admin_auth)):
    """Validate the current page access token"""
    token = os.environ.get('FACEBOOK_PAGE_ACCESS_TOKEN')
    
    if not token:
        return {"success": False, "error": "No token configured"}
    
    if not facebook_oauth.is_configured:
        return {"success": False, "error": "OAuth not configured - cannot validate token"}
    
    result = await facebook_oauth.validate_token(token)
    return result


@api_router.post("/facebook/test-post")
async def test_facebook_post(auth: bool = Depends(get_admin_auth)):
    """
    Test Facebook posting with the newest article (Admin only)
    Posts ONE article to verify everything works
    """
    try:
        # Get the newest article - include _id for reliable article linking
        article = await db.articles.find_one(
            {},
            {"_id": 1, "id": 1, "title": 1, "content": 1, "image": 1, "source": 1, "source_url": 1}
        )
        
        if not article:
            return {"success": False, "error": "No articles found to post"}
        
        # Use _id as the article identifier (works in both preview and production)
        article['id'] = str(article['_id'])
        del article['_id']
        
        # Post to Facebook
        result = await facebook_service.post_article(article)
        
        return {
            "success": result.get("success", False),
            "article_title": article.get("title"),
            "post_id": result.get("post_id"),
            "error": result.get("error")
        }
        
    except Exception as e:
        logger.error(f"Facebook test post error: {str(e)}")
        return {"success": False, "error": str(e)}


@api_router.post("/facebook/test-simplified")
async def test_simplified_facebook_post(auth: bool = Depends(get_admin_auth)):
    """
    Test SIMPLIFIED Facebook post format (link-only, no image attachment)
    This lets Facebook auto-generate the preview card from Open Graph tags.
    """
    try:
        # Get a recent article
        article = await db.articles.find_one(
            {},
            {"_id": 1, "title": 1, "category": 1, "image": 1}
        )
        
        if not article:
            return {"success": False, "error": "No articles found"}
        
        article_id = str(article['_id'])
        title = article.get('title', 'News')
        category = article.get('category', '')
        
        # Generate minimal hashtags (max 3)
        hashtags = ["#CheshireToday"]
        if "chester" in title.lower():
            hashtags.append("#Chester")
        elif "warrington" in title.lower():
            hashtags.append("#Warrington")
        if category == "Local News":
            hashtags.append("#LocalNews")
        elif category == "UK News":
            hashtags.append("#UKNews")
        
        hashtag_str = " ".join(hashtags[:3])
        
        # SIMPLIFIED FORMAT - just headline + link + minimal hashtags
        # The link will auto-generate a preview card with image
        article_url = f"https://cheshiretoday.co.uk/search?q={article_id[:20]}"
        
        message = f"{title}\n\n🔗 {article_url}\n\n{hashtag_str}"
        
        # Post as LINK post (not photo) - Facebook will auto-preview
        page_token = await facebook_service.get_page_token()
        
        if not page_token:
            return {"success": False, "error": "Could not get page token"}
        
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://graph.facebook.com/v18.0/{facebook_service.page_id}/feed",
                data={
                    "message": message,
                    "link": article_url,  # This triggers the auto-preview!
                    "access_token": page_token
                },
                timeout=30.0
            )
            
            result = response.json()
            
            if "error" in result:
                return {
                    "success": False,
                    "error": result["error"].get("message", "Unknown error"),
                    "format": "simplified"
                }
            
            return {
                "success": True,
                "post_id": result.get("id"),
                "format": "simplified",
                "message_preview": message[:200],
                "note": "Check your Facebook page to see the auto-generated preview card!"
            }
            
    except Exception as e:
        logger.error(f"Simplified Facebook test error: {str(e)}")
        return {"success": False, "error": str(e)}

@api_router.post("/facebook/post-latest")
async def post_latest_to_facebook(count: int = 3, auth: bool = Depends(get_admin_auth)):
    """
    Post the latest N articles to Facebook (Admin only)
    Uses distributed lock to prevent duplicate posting from concurrent requests.
    Default: 3 newest articles
    """
    try:
        if not facebook_service.is_configured:
            return {"success": False, "error": "Facebook not configured"}
        
        # DISTRIBUTED LOCK: Prevent concurrent posting
        now = datetime.now(timezone.utc)
        five_minutes_ago = now - timedelta(minutes=5)
        lock_id = str(uuid4())
        
        await db.scheduler_locks.update_one(
            {"job": "facebook_post"},
            {"$setOnInsert": {"job": "facebook_post", "locked_at": None, "lock_id": None}},
            upsert=True
        )
        
        lock_result = await db.scheduler_locks.find_one_and_update(
            {
                "job": "facebook_post",
                "$or": [
                    {"locked_at": None},
                    {"locked_at": {"$lt": five_minutes_ago}}
                ]
            },
            {"$set": {"locked_at": now, "lock_id": lock_id}},
            return_document=True
        )
        
        if lock_result is None or lock_result.get("lock_id") != lock_id:
            return {"success": False, "posted": 0, "message": "Facebook post already in progress (locked)"}
        
        logger.info(f"📘 Post-latest: Lock acquired (ID: {lock_id[:8]}...)")
        
        try:
            # Check recently posted to avoid duplicates
            window_start = datetime.now(timezone.utc) - timedelta(hours=24)
            recently_posted = await db.facebook_post_log.find({
                "posted_at": {"$gte": window_start}
            }).to_list(100)
            
            posted_article_ids = set(p.get('article_id') for p in recently_posted if p.get('article_id'))
            posted_title_patterns = set()
            for p in recently_posted:
                title = p.get('title', '')
                if title:
                    words = [w.lower() for w in title.split() if len(w) > 3][:5]
                    posted_title_patterns.add(' '.join(sorted(words)))
            
            # Get articles, excluding already posted
            all_articles = await db.articles.find(
                {},
                {"_id": 1, "id": 1, "title": 1, "content": 1, "image": 1, "source": 1, "source_url": 1, "category": 1}
            ).sort("publishedDate", -1).limit(30).to_list(30)
            
            articles = []
            for article in all_articles:
                article_id = str(article['_id'])
                title = article.get('title', '')
                
                if article_id in posted_article_ids:
                    continue
                
                words = [w.lower() for w in title.split() if len(w) > 3][:5]
                title_pattern = ' '.join(sorted(words))
                if title_pattern in posted_title_patterns:
                    continue
                
                article['id'] = article_id
                del article['_id']
                articles.append(article)
                posted_title_patterns.add(title_pattern)
                
                if len(articles) >= count:
                    break
            
            if not articles:
                await db.scheduler_locks.delete_one({"job": "facebook_post"})
                return {"success": True, "posted": 0, "message": "No new articles to post"}
            
            result = await facebook_service.post_multiple_articles(articles, limit=count)
            
            # Log posted articles
            for article in articles[:result.get('posted', 0)]:
                await db.facebook_post_log.insert_one({
                    "article_id": article.get('id'),
                    "title": article.get('title', '')[:100],
                    "posted_at": datetime.now(timezone.utc)
                })
            
            await db.scheduler_locks.delete_one({"job": "facebook_post"})
            return result
            
        except Exception as e:
            await db.scheduler_locks.delete_one({"job": "facebook_post"})
            raise e
        
    except Exception as e:
        logger.error(f"Facebook posting error: {str(e)}")
        return {"success": False, "error": str(e)}

@api_router.post("/facebook/trigger-scheduled")
async def trigger_facebook_scheduled_post(auth: bool = Depends(get_admin_auth)):
    """
    Manually trigger a scheduled Facebook post (same as auto-scheduler does)
    Uses the same lock mechanism to prevent duplicate posts from concurrent calls.
    """
    try:
        if not facebook_service.is_configured:
            return {"success": False, "error": "Facebook not configured"}
        
        # COOLDOWN CHECK: Skip if we posted in the last 10 minutes (shorter for manual trigger)
        now = datetime.now(timezone.utc)
        ten_minutes_ago = now - timedelta(minutes=10)
        recent_post = await db.facebook_post_log.find_one({
            "posted_at": {"$gte": ten_minutes_ago}
        })
        
        if recent_post:
            return {"success": False, "posted": 0, "message": "Cooldown active - please wait 10 minutes between posts to prevent duplicates"}
        
        # DISTRIBUTED LOCK: Same logic as scheduled_facebook_post
        five_minutes_ago = now - timedelta(minutes=5)
        lock_id = str(uuid4())
        
        # Ensure lock document exists (idempotent)
        await db.scheduler_locks.update_one(
            {"job": "facebook_post"},
            {"$setOnInsert": {"job": "facebook_post", "locked_at": None, "lock_id": None}},
            upsert=True
        )
        
        # Atomically try to claim the lock
        lock_result = await db.scheduler_locks.find_one_and_update(
            {
                "job": "facebook_post",
                "$or": [
                    {"locked_at": None},
                    {"locked_at": {"$lt": five_minutes_ago}}
                ]
            },
            {"$set": {"locked_at": now, "lock_id": lock_id}},
            return_document=True
        )
        
        # If lock_result is None or lock_id doesn't match, another process has the lock
        if lock_result is None:
            return {"success": False, "posted": 0, "message": "Facebook post already in progress (locked by another process)"}
        
        if lock_result.get("lock_id") != lock_id:
            return {"success": False, "posted": 0, "message": "Facebook post lock mismatch - try again"}
        
        logger.info(f"📘 Manual trigger: Lock acquired (ID: {lock_id[:8]}...)")
        
        try:
            # Use 24-hour sliding window to check recently posted articles
            window_start = datetime.now(timezone.utc) - timedelta(hours=24)
            recently_posted = await db.facebook_post_log.find({
                "posted_at": {"$gte": window_start}
            }).to_list(100)
            
            posted_article_ids = set(p.get('article_id') for p in recently_posted if p.get('article_id'))
            posted_title_patterns = set()
            for p in recently_posted:
                title = p.get('title', '')
                if title:
                    words = [w.lower() for w in title.split() if len(w) > 3][:5]
                    posted_title_patterns.add(' '.join(sorted(words)))
            
            # Get articles, excluding already posted
            all_articles = await db.articles.find(
                {},
                {"_id": 1, "id": 1, "title": 1, "content": 1, "image": 1, "source": 1, "source_url": 1, "category": 1}
            ).sort("publishedDate", -1).limit(30).to_list(30)
            
            articles = []
            for article in all_articles:
                article_id = str(article['_id'])
                title = article.get('title', '')
                
                if article_id in posted_article_ids:
                    continue
                
                words = [w.lower() for w in title.split() if len(w) > 3][:5]
                title_pattern = ' '.join(sorted(words))
                if title_pattern in posted_title_patterns:
                    continue
                
                article['id'] = article_id
                del article['_id']
                articles.append(article)
                posted_title_patterns.add(title_pattern)
                
                if len(articles) >= 3:
                    break
            
            if not articles:
                # Release lock and return
                await db.scheduler_locks.delete_one({"job": "facebook_post"})
                return {"success": True, "posted": 0, "message": "No new articles to post (all recent articles already posted)"}
            
            result = await facebook_service.post_multiple_articles(articles, limit=3)
            
            # Log posted articles
            for article in articles[:result.get('posted', 0)]:
                await db.facebook_post_log.insert_one({
                    "article_id": article.get('id'),
                    "title": article.get('title', '')[:100],
                    "posted_at": datetime.now(timezone.utc)
                })
            
            # Release lock
            await db.scheduler_locks.delete_one({"job": "facebook_post"})
            
            return {
                "success": result.get("success", False),
                "posted": result.get("posted", 0),
                "message": f"Posted {result.get('posted', 0)} articles to Facebook",
                "results": result.get("results", [])
            }
        except Exception as e:
            # Release lock on error
            await db.scheduler_locks.delete_one({"job": "facebook_post"})
            raise e
        
    except Exception as e:
        logger.error(f"Facebook trigger error: {str(e)}")
        return {"success": False, "error": str(e)}


# ============================================================================
# FACEBOOK SCHEDULING ENDPOINTS - Manual article selection & scheduling
# ============================================================================

class SchedulePostRequest(BaseModel):
    article_id: str
    scheduled_time: str  # ISO format datetime string

@api_router.get("/facebook/schedulable-articles")
async def get_schedulable_articles(limit: int = 20, auth: bool = Depends(get_admin_auth)):
    """
    Get articles available for Facebook posting.
    Returns recent articles that can be selected for manual posting or scheduling.
    """
    try:
        articles = await db.articles.find(
            {},
            {"_id": 1, "id": 1, "title": 1, "image": 1, "category": 1, "publishedDate": 1, "source": 1}
        ).sort("publishedDate", -1).limit(limit).to_list(limit)
        
        # Convert ObjectId to string
        for article in articles:
            article['_id'] = str(article['_id'])
            if 'id' not in article:
                article['id'] = article['_id']
        
        return {
            "success": True,
            "articles": articles,
            "count": len(articles)
        }
    except Exception as e:
        logger.error(f"Error fetching schedulable articles: {str(e)}")
        return {"success": False, "error": str(e), "articles": []}


@api_router.post("/facebook/post-single")
async def post_single_article_to_facebook(article_id: str, auth: bool = Depends(get_admin_auth)):
    """
    Post a specific article to Facebook immediately.
    Allows manual selection of which article to post.
    Checks if article was recently posted to prevent duplicates.
    """
    try:
        if not facebook_service.is_configured:
            return {"success": False, "error": "Facebook not configured. Set FACEBOOK_PAGE_ACCESS_TOKEN and FACEBOOK_PAGE_ID"}
        
        # Check if this article was already posted in the last 24 hours
        window_start = datetime.now(timezone.utc) - timedelta(hours=24)
        already_posted = await db.facebook_post_log.find_one({
            "article_id": article_id,
            "posted_at": {"$gte": window_start}
        })
        
        if already_posted:
            return {
                "success": False,
                "error": "This article was already posted to Facebook in the last 24 hours",
                "posted_at": already_posted.get("posted_at").isoformat() if already_posted.get("posted_at") else None
            }
        
        result = await facebook_service.post_single_article_by_id(db, article_id)
        
        # Log successful posts
        if result.get("success"):
            await db.facebook_post_log.insert_one({
                "article_id": article_id,
                "title": result.get("article_title", "")[:100],
                "posted_at": datetime.now(timezone.utc)
            })
        
        return {
            "success": result.get("success", False),
            "message": "Article posted to Facebook" if result.get("success") else result.get("error", "Failed to post"),
            "post_id": result.get("post_id"),
            "article_title": result.get("article_title")
        }
        
    except Exception as e:
        logger.error(f"Error posting single article: {str(e)}")
        return {"success": False, "error": str(e)}


@api_router.post("/facebook/schedule-post")
async def schedule_facebook_post(request: SchedulePostRequest, auth: bool = Depends(get_admin_auth)):
    """
    Schedule a specific article to be posted to Facebook at a future time.
    """
    try:
        # Parse the scheduled time
        try:
            scheduled_dt = datetime.fromisoformat(request.scheduled_time.replace('Z', '+00:00'))
        except ValueError:
            return {"success": False, "error": "Invalid datetime format. Use ISO format."}
        
        # Verify the article exists
        article = None
        try:
            article = await db.articles.find_one({"_id": ObjectId(request.article_id)})
        except:
            pass
        
        if not article:
            article = await db.articles.find_one({"id": request.article_id})
        
        if not article:
            return {"success": False, "error": "Article not found"}
        
        # Create scheduled post record
        scheduled_post = {
            "article_id": request.article_id,
            "article_title": article.get("title", "Untitled"),
            "article_image": article.get("image", ""),
            "scheduled_time": scheduled_dt,
            "created_at": datetime.now(timezone.utc),
            "status": "pending",  # pending, posted, cancelled, failed
            "post_id": None,
            "error": None
        }
        
        result = await db.scheduled_facebook_posts.insert_one(scheduled_post)
        
        logger.info(f"Scheduled Facebook post for article '{article.get('title', '')[:40]}...' at {scheduled_dt}")
        
        return {
            "success": True,
            "message": f"Post scheduled for {scheduled_dt.strftime('%Y-%m-%d %H:%M')} UTC",
            "scheduled_post_id": str(result.inserted_id),
            "article_title": article.get("title", "")
        }
        
    except Exception as e:
        logger.error(f"Error scheduling post: {str(e)}")
        return {"success": False, "error": str(e)}


@api_router.get("/facebook/scheduled-posts")
async def get_scheduled_posts(auth: bool = Depends(get_admin_auth)):
    """
    Get all scheduled Facebook posts (pending and recent history).
    """
    try:
        # Get pending posts
        pending_posts = await db.scheduled_facebook_posts.find(
            {"status": "pending"}
        ).sort("scheduled_time", 1).to_list(50)
        
        # Get recent history (posted/failed in last 7 days)
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        history_posts = await db.scheduled_facebook_posts.find(
            {"status": {"$in": ["posted", "failed", "cancelled"]}, "scheduled_time": {"$gte": week_ago}}
        ).sort("scheduled_time", -1).limit(20).to_list(20)
        
        # Convert ObjectIds to strings
        for post in pending_posts + history_posts:
            post['_id'] = str(post['_id'])
            if 'scheduled_time' in post:
                post['scheduled_time'] = post['scheduled_time'].isoformat()
            if 'created_at' in post:
                post['created_at'] = post['created_at'].isoformat()
        
        return {
            "success": True,
            "pending": pending_posts,
            "history": history_posts,
            "pending_count": len(pending_posts)
        }
        
    except Exception as e:
        logger.error(f"Error fetching scheduled posts: {str(e)}")
        return {"success": False, "error": str(e), "pending": [], "history": []}


@api_router.delete("/facebook/scheduled-posts/{post_id}")
async def cancel_scheduled_post(post_id: str, auth: bool = Depends(get_admin_auth)):
    """
    Cancel a pending scheduled post.
    """
    try:
        result = await db.scheduled_facebook_posts.update_one(
            {"_id": ObjectId(post_id), "status": "pending"},
            {"$set": {"status": "cancelled"}}
        )
        
        if result.modified_count > 0:
            logger.info(f"Cancelled scheduled post: {post_id}")
            return {"success": True, "message": "Scheduled post cancelled"}
        else:
            return {"success": False, "error": "Post not found or already processed"}
            
    except Exception as e:
        logger.error(f"Error cancelling scheduled post: {str(e)}")
        return {"success": False, "error": str(e)}


# ============================================================================
# FACEBOOK ANALYTICS ENDPOINTS
# ============================================================================

@api_router.get("/facebook/analytics/debug-edges")
async def debug_facebook_analytics_edges(auth: bool = Depends(get_admin_auth)):
    """
    Admin-only diagnostic for Facebook Graph content edges.
    Shows which Page edges expose the newest posts/Reels without exposing tokens.
    """
    try:
        page_token = await facebook_service.get_page_token()
        if not page_token:
            return {"success": False, "error": "Could not get page token", "edges": []}

        edges = [
            {
                "name": "promotable_posts",
                "fields": "id,message,created_time,permalink_url"
            },
            {
                "name": "feed",
                "fields": "id,message,created_time,permalink_url"
            },
            {
                "name": "published_posts",
                "fields": "id,message,created_time,permalink_url"
            },
            {
                "name": "posts",
                "fields": "id,message,created_time,permalink_url"
            },
            {
                "name": "photos",
                "fields": "id,name,created_time,permalink_url"
            },
            {
                "name": "videos",
                "fields": "id,description,created_time,permalink_url"
            },
            {
                "name": "video_reels",
                "fields": "id,description,created_time,permalink_url"
            }
        ]

        diagnostics = []
        async with httpx.AsyncClient() as client:
            for edge in edges:
                response = await client.get(
                    f"{facebook_service.base_url}/{facebook_service.page_id}/{edge['name']}",
                    params={
                        "fields": edge["fields"],
                        "limit": 10,
                        "access_token": page_token
                    },
                    timeout=30.0
                )
                result = response.json()

                if "error" in result:
                    diagnostics.append({
                        "edge": edge["name"],
                        "success": False,
                        "error": result["error"].get("message", "Unknown error"),
                        "count": 0,
                        "items": []
                    })
                    continue

                items = []
                for item in result.get("data", [])[:5]:
                    message = item.get("message") or item.get("description") or item.get("name") or ""
                    items.append({
                        "id": item.get("id"),
                        "created_time": item.get("created_time"),
                        "title": message[:120] if message else "Unknown",
                        "permalink_url": item.get("permalink_url")
                    })

                diagnostics.append({
                    "edge": edge["name"],
                    "success": True,
                    "count": len(result.get("data", [])),
                    "items": items
                })

        return {
            "success": True,
            "page_id": facebook_service.page_id,
            "edges": diagnostics
        }

    except Exception as e:
        logger.error(f"Error debugging Facebook analytics edges: {str(e)}")
        return {"success": False, "error": str(e), "edges": []}


@api_router.get("/facebook/analytics/insights-debug")
async def debug_facebook_insights_metrics(auth: bool = Depends(get_admin_auth)):
    """Admin-only diagnostic for available Meta post/video insights metrics."""
    try:
        return await facebook_service.debug_latest_post_insights()
    except Exception as e:
        logger.error(f"Error debugging Facebook insights metrics: {str(e)}")
        return {"success": False, "error": str(e)}


@api_router.get("/facebook/analytics")
async def get_facebook_analytics(auth: bool = Depends(get_admin_auth)):
    """
    Get Facebook post analytics - engagement metrics for recent posts.
    Shows which articles performed best on Facebook.
    """
    try:
        # Fetch engagement data from Facebook
        engagement_data = await facebook_service.fetch_recent_posts_engagement(limit=20)
        
        if not engagement_data.get("success"):
            return engagement_data
        
        posts = engagement_data.get("posts", [])
        
        # Calculate summary statistics
        total_likes = sum(p.get("likes", 0) for p in posts)
        total_comments = sum(p.get("comments", 0) for p in posts)
        total_shares = sum(p.get("shares", 0) for p in posts)
        total_engagement = sum(p.get("engagement_score", 0) for p in posts)
        
        # Get top performing post
        top_post = posts[0] if posts else None
        
        # Get posts from our log to match with article data
        recent_logs = await db.facebook_post_log.find({}).sort("posted_at", -1).limit(50).to_list(50)
        
        # Enhance posts with our article data if available
        log_by_title = {log.get("title", "")[:50]: log for log in recent_logs}
        
        for post in posts:
            title_key = post.get("title", "")[:50]
            if title_key in log_by_title:
                log_entry = log_by_title[title_key]
                post["article_id"] = log_entry.get("article_id")
                post["posted_at_local"] = log_entry.get("posted_at").isoformat() if log_entry.get("posted_at") else None
        
        return {
            "success": True,
            "summary": {
                "total_posts_analyzed": len(posts),
                "total_likes": total_likes,
                "total_comments": total_comments,
                "total_shares": total_shares,
                "total_engagement_score": total_engagement,
                "avg_engagement_per_post": round(total_engagement / len(posts), 2) if posts else 0
            },
            "top_post": top_post,
            "posts": posts
        }
        
    except Exception as e:
        logger.error(f"Error fetching Facebook analytics: {str(e)}")
        return {"success": False, "error": str(e)}


@api_router.get("/facebook/analytics/insights")
async def get_facebook_insights(auth: bool = Depends(get_admin_auth)):
    """
    Get actionable insights from Facebook post performance.
    Uses internal post logs when available, otherwise falls back to live Facebook Graph data.
    """
    try:
        # Fetch engagement/content data from Facebook first so insights still work without DB logs.
        engagement_data = await facebook_service.fetch_recent_posts_engagement(limit=30)
        posts = engagement_data.get("posts", []) if engagement_data.get("success") else []
        
        # Get our posting history with article details if present.
        recent_logs = await db.facebook_post_log.find({}).sort("posted_at", -1).limit(100).to_list(100)
        
        if not recent_logs and not posts:
            return {
                "success": True,
                "message": "Not enough Facebook data yet. Post more articles or Reels to get insights.",
                "insights": []
            }
        
        # Analyze by category when internal logs can be matched to articles.
        category_stats = {}
        for log in recent_logs:
            article_id = log.get("article_id")
            if article_id:
                article = await db.articles.find_one({"_id": ObjectId(article_id)}) if ObjectId.is_valid(article_id) else None
                if not article:
                    article = await db.articles.find_one({"id": article_id})
                
                if article:
                    category = article.get("category", "Unknown")
                    if category not in category_stats:
                        category_stats[category] = {"count": 0, "titles": []}
                    category_stats[category]["count"] += 1
                    category_stats[category]["titles"].append(article.get("title", "")[:50])
        
        # Generate insights
        insights = []
        
        if posts:
            top_post = max(
                posts,
                key=lambda p: (p.get("engagement_score", 0), p.get("created_time") or "")
            )
            source_stats = {}
            for post in posts:
                source_type = post.get("source_type", "unknown")
                source_stats[source_type] = source_stats.get(source_type, 0) + 1
            
            insights.append({
                "type": "top_performer",
                "icon": "🏆",
                "title": "Top Performing Content",
                "description": f'"{top_post.get("title", "Unknown")}" got {top_post.get("likes", 0)} reactions, {top_post.get("comments", 0)} comments, {top_post.get("shares", 0)} shares',
                "engagement_score": top_post.get("engagement_score", 0)
            })
            
            top_source = max(source_stats.items(), key=lambda x: x[1])
            insights.append({
                "type": "content_mix",
                "icon": "🎬" if top_source[0] in ["videos", "video_reels"] else "📰",
                "title": "Most Common Facebook Format",
                "description": f'{top_source[0].replace("_", " ").title()} - {top_source[1]} items in the latest Facebook analytics sample',
                "recommendation": "Recent activity includes Reels/videos, so the analytics now checks feed posts and video content together."
            })
        
        if category_stats:
            sorted_categories = sorted(category_stats.items(), key=lambda x: x[1]["count"], reverse=True)
            top_category = sorted_categories[0]
            insights.append({
                "type": "category_trend",
                "icon": "📊",
                "title": "Most Posted Category",
                "description": f'{top_category[0]} - {top_category[1]["count"]} posts',
                "recommendation": f"You're posting a lot of {top_category[0]} content. Consider diversifying if engagement is low."
            })
        
        # Posting frequency insight from internal logs if available, otherwise from Facebook created_time.
        from datetime import timedelta
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        
        def make_aware(dt):
            if dt is None:
                return None
            if isinstance(dt, datetime):
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt
            return None
        
        def parse_facebook_time(value):
            if not value:
                return None
            try:
                return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
            except Exception:
                return None
        
        if recent_logs:
            posts_this_week = len([
                l for l in recent_logs
                if l.get("posted_at") and make_aware(l["posted_at"]) and make_aware(l["posted_at"]) > week_ago
            ])
        else:
            posts_this_week = len([
                p for p in posts
                if parse_facebook_time(p.get("created_time")) and parse_facebook_time(p.get("created_time")) > week_ago
            ])
        
        insights.append({
            "type": "frequency",
            "icon": "📅",
            "title": "Posting Frequency",
            "description": f"{posts_this_week} Facebook items found in the last 7 days",
            "recommendation": "Aim for consistent morning and after-work posts, with Reels used for simple visual stories and links reinforced in captions/comments."
        })
        
        if posts:
            avg_engagement = sum(p.get("engagement_score", 0) for p in posts) / len(posts)
            insights.append({
                "type": "engagement_summary",
                "icon": "💡",
                "title": "Average Engagement",
                "description": f"Average engagement score: {round(avg_engagement, 2)}",
                "recommendation": "If Meta still reports zero reactions in this dashboard, check Facebook Page permissions/insights access because content is now being found successfully."
            })
        
        return {
            "success": True,
            "total_posts_analyzed": len(posts) if posts else len(recent_logs),
            "category_breakdown": category_stats,
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"Error generating Facebook insights: {str(e)}")
        return {"success": False, "error": str(e)}


# ============================================================================
# ARTICLE VIEW TRACKING & MOST READ
# ============================================================================

@api_router.post("/articles/{article_id}/view")
async def track_article_view(article_id: str, request: Request):
    """
    Track an article view for "Most Read" feature.
    Uses IP-based deduplication to prevent spam.
    """
    try:
        article = None
        try:
            article = await db.articles.find_one({"_id": ObjectId(article_id)})
        except Exception:
            article = None

        if not article:
            article = await db.articles.find_one({"id": article_id})

        if (
            not article
            or article.get("archived") is True
            or article.get("manual_review_hidden_from_public") is True
        ):
            raise HTTPException(status_code=404, detail="Article not found")

        resolved_article_id = str(article["_id"])

        # Get client IP for deduplication
        client_ip = request.client.host if request.client else "unknown"
        
        # Check if this IP viewed this article in last hour
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        existing_view = await db.article_views.find_one({
            "article_id": resolved_article_id,
            "ip_hash": hashlib.md5(client_ip.encode()).hexdigest(),
            "viewed_at": {"$gte": one_hour_ago}
        })
        
        if existing_view:
            return {"success": True, "counted": False, "message": "View already counted"}
        
        # Record the view
        await db.article_views.insert_one({
            "article_id": resolved_article_id,
            "ip_hash": hashlib.md5(client_ip.encode()).hexdigest(),
            "viewed_at": datetime.now(timezone.utc)
        })
        
        # Increment view counter on article
        await db.articles.update_one(
            {"_id": article["_id"]},
            {"$inc": {"view_count": 1}}
        )
        
        return {"success": True, "counted": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking article view: {str(e)}")
        return {"success": False, "error": str(e)}


# ============================================================================
# PUSH NOTIFICATIONS
# ============================================================================

from app.push_service import push_service

@api_router.get("/push/vapid-public-key")
async def get_vapid_public_key():
    """Get the VAPID public key for push subscription"""
    return {
        "publicKey": push_service.get_vapid_public_key(),
        "configured": push_service.is_configured
    }


@api_router.post("/push/subscribe")
async def subscribe_to_push(request: Request):
    """
    Subscribe to push notifications.
    Stores the subscription in the database.
    Sends milestone email alerts at 10, 50, 100, 250, 500, 1000 subscribers.
    """
    try:
        data = await request.json()
        subscription = data.get("subscription")
        
        if not subscription or not subscription.get("endpoint"):
            return {"success": False, "error": "Invalid subscription"}
        
        # Check if this is a new subscription
        existing = await db.push_subscriptions.find_one({"endpoint": subscription["endpoint"]})
        is_new = existing is None
        
        # Store subscription
        await db.push_subscriptions.update_one(
            {"endpoint": subscription["endpoint"]},
            {
                "$set": {
                    "subscription": subscription,
                    "subscribed_at": datetime.now(timezone.utc),
                    "active": True
                }
            },
            upsert=True
        )
        
        logger.info(f"📱 New push subscription: {subscription['endpoint'][:50]}...")
        
        # Check for milestone if new subscription
        if is_new:
            total_subscribers = await db.push_subscriptions.count_documents({"active": True})
            milestones = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]
            
            if total_subscribers in milestones:
                # Send milestone email
                await send_subscriber_milestone_email(total_subscribers)
        
        return {"success": True, "message": "Subscribed to push notifications"}
        
    except Exception as e:
        logger.error(f"Error subscribing to push: {str(e)}")
        return {"success": False, "error": str(e)}


async def send_breaking_news_notification(request: Request, auth: bool = Depends(get_admin_auth)):
    """
    Send a breaking news push notification to all subscribers.
    Admin only.
    """
    try:
        data = await request.json()
        article_id = data.get("article_id")
        title = data.get("title")
        
        if not title:
            return {"success": False, "error": "Title required"}
        
        # Get all active subscriptions
        subscriptions = await db.push_subscriptions.find(
            {"active": True}
        ).to_list(10000)
        
        if not subscriptions:
            return {"success": False, "error": "No subscribers", "sent": 0}
        
        # Extract subscription objects
        sub_objects = [s.get("subscription") for s in subscriptions if s.get("subscription")]
        
        # Send notifications
        result = await push_service.send_breaking_news(
            subscriptions=sub_objects,
            article_title=title,
            article_id=article_id or "",
            category="Breaking News"
        )
        
        # Remove expired subscriptions
        if result.get("expired_endpoints"):
            for endpoint in result["expired_endpoints"]:
                await db.push_subscriptions.delete_one({"endpoint": endpoint})
        
        return result
        
    except Exception as e:
        logger.error(f"Error sending breaking news notification: {str(e)}")
        return {"success": False, "error": str(e)}


@api_router.get("/push/stats")
async def get_push_stats(auth: bool = Depends(get_admin_auth)):
    """Get push notification statistics"""
    try:
        total = await db.push_subscriptions.count_documents({})
        active = await db.push_subscriptions.count_documents({"active": True})
        
        return {
            "success": True,
            "total_subscriptions": total,
            "active_subscriptions": active,
            "configured": push_service.is_configured
        }
        
    except Exception as e:
        logger.error(f"Error getting push stats: {str(e)}")
        return {"success": False, "error": str(e)}


# ============================================================================
# SMART CONTENT PRIORITIZATION
# ============================================================================

@api_router.get("/facebook/smart-articles")
async def get_smart_prioritized_articles(auth: bool = Depends(get_admin_auth), limit: int = 10):
    """
    Get articles prioritized by engagement potential.
    Uses historical engagement data to recommend articles for Facebook posting.
    
    Prioritization factors:
    1. Category performance (from past engagement)
    2. Location mentions (local content performs better)
    3. Topic keywords (breaking news, police, etc.)
    4. Recency (newer articles preferred)
    5. Not recently posted to Facebook
    """
    try:
        # Get engagement data by category from past posts
        category_engagement = {}
        recent_posts = await db.facebook_post_log.find({}).sort("posted_at", -1).limit(100).to_list(100)
        
        for post in recent_posts:
            article_id = post.get("article_id")
            if article_id:
                article = await db.articles.find_one({"$or": [{"_id": ObjectId(article_id) if ObjectId.is_valid(article_id) else None}, {"id": article_id}]})
                if article:
                    category = article.get("category", "Unknown")
                    if category not in category_engagement:
                        category_engagement[category] = {"count": 0, "score": 0}
                    category_engagement[category]["count"] += 1
        
        # Get articles not posted in last 24 hours
        yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_post_ids = set()
        recent_posts_24h = await db.facebook_post_log.find({"posted_at": {"$gte": yesterday}}).to_list(100)
        for p in recent_posts_24h:
            recent_post_ids.add(p.get("article_id"))
        
        # Get all recent articles
        all_articles = await db.articles.find(
            {},
            {"_id": 1, "id": 1, "title": 1, "category": 1, "image": 1, "source": 1, "publishedDate": 1}
        ).sort("publishedDate", -1).limit(50).to_list(50)
        
        # Score each article
        scored_articles = []
        for article in all_articles:
            article_id = str(article.get("_id", article.get("id", "")))
            
            # Skip if recently posted
            if article_id in recent_post_ids:
                continue
            
            title = article.get("title", "").lower()
            category = article.get("category", "Unknown")
            score = 50  # Base score
            reasons = []
            
            # Category bonus
            if category in category_engagement and category_engagement[category]["count"] > 5:
                score += 10
                reasons.append(f"Popular category: {category}")
            
            # Location bonus (local content performs well)
            local_keywords = ["chester", "knutsford", "wilmslow", "macclesfield", "warrington", "crewe", "cheshire"]
            if any(loc in title for loc in local_keywords):
                score += 20
                reasons.append("Local content")
            
            # Breaking/urgent topic bonus
            urgent_keywords = ["breaking", "urgent", "police", "crash", "fire", "emergency", "alert"]
            if any(word in title for word in urgent_keywords):
                score += 25
                reasons.append("Urgent/breaking topic")
            
            # Human interest bonus
            interest_keywords = ["community", "charity", "award", "celebrates", "hero", "rescue"]
            if any(word in title for word in interest_keywords):
                score += 15
                reasons.append("Human interest story")
            
            # Recency bonus (articles from last 6 hours get boost)
            pub_date = article.get("publishedDate")
            if pub_date:
                try:
                    if isinstance(pub_date, str):
                        pub_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                    if (datetime.now(timezone.utc) - pub_date).total_seconds() < 6 * 3600:
                        score += 15
                        reasons.append("Fresh content")
                except:
                    pass
            
            scored_articles.append({
                "id": article_id,
                "title": article.get("title", ""),
                "category": category,
                "image": article.get("image", ""),
                "source": article.get("source", ""),
                "score": score,
                "reasons": reasons
            })
        
        # Sort by score
        scored_articles.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "success": True,
            "articles": scored_articles[:limit],
            "total_candidates": len(scored_articles),
            "category_stats": category_engagement
        }
        
    except Exception as e:
        logger.error(f"Error getting smart articles: {str(e)}")
        return {"success": False, "error": str(e), "articles": []}


@api_router.get("/check-subscribers")
async def check_subscribers(authorized: bool = Depends(get_admin_auth)):
    """Check for duplicate subscribers and return stats"""
    try:
        subscribers = await db.subscribers.find({}, {"_id": 1, "email": 1}).to_list(1000)
        
        # Find duplicates
        email_counts = {}
        for s in subscribers:
            email = s.get('email', '').lower().strip()
            if email:
                if email not in email_counts:
                    email_counts[email] = []
                email_counts[email].append(str(s.get('_id')))
        
        duplicates = {email: ids for email, ids in email_counts.items() if len(ids) > 1}
        
        return {
            "total_records": len(subscribers),
            "unique_emails": len(email_counts),
            "duplicate_emails": len(duplicates),
            "duplicate_records": sum(len(ids) - 1 for ids in duplicates.values())
        }
    except Exception as e:
        return {"error": str(e)}


@api_router.post("/cleanup-subscribers")
async def cleanup_duplicate_subscribers(authorized: bool = Depends(get_admin_auth)):
    """Remove duplicate subscriber entries, keeping only the first one"""
    try:
        subscribers = await db.subscribers.find({}, {"_id": 1, "email": 1}).to_list(1000)
        
        # Find duplicates
        email_first_id = {}
        ids_to_delete = []
        
        for s in subscribers:
            email = s.get('email', '').lower().strip()
            if email:
                if email not in email_first_id:
                    email_first_id[email] = s.get('_id')
                else:
                    # This is a duplicate - mark for deletion
                    ids_to_delete.append(s.get('_id'))
        
        # Delete duplicates
        deleted_count = 0
        for doc_id in ids_to_delete:
            result = await db.subscribers.delete_one({"_id": doc_id})
            deleted_count += result.deleted_count
        
        return {
            "success": True,
            "duplicates_removed": deleted_count,
            "remaining_subscribers": len(email_first_id)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.post("/cleanup-invalid-emails")
async def cleanup_invalid_emails(authorized: bool = Depends(get_admin_auth)):
    """Remove invalid email addresses from subscribers"""
    import re
    try:
        subscribers = await db.subscribers.find({}, {"_id": 1, "email": 1}).to_list(1000)
        
        email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        invalid_ids = []
        for s in subscribers:
            email = s.get('email', '').strip()
            # Remove if: empty, reserved/example domain, invalid format, or test addresses
            if not is_deliverable_newsletter_email(email):
                invalid_ids.append(s.get('_id'))
        
        # Delete invalid subscribers
        deleted_count = 0
        for doc_id in invalid_ids:
            result = await db.subscribers.delete_one({"_id": doc_id})
            deleted_count += result.deleted_count
        
        return {
            "success": True,
            "invalid_removed": deleted_count,
            "remaining_subscribers": len(subscribers) - deleted_count
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.post("/send-digest")
async def send_digest_now(authorized: bool = Depends(get_admin_auth)):
    """Manually trigger sending news digest to all subscribers (for testing)"""
    try:
        # ============================================
        # DUPLICATE PREVENTION - Check if already sent recently
        # ============================================
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        date_key = now.strftime('%Y%m%d')
        
        # Check if digest was already sent in the last hour (to prevent accidental double-clicks)
        one_hour_ago = now - timedelta(hours=1)
        recent_send = await db.digest_log.find_one({
            "sent_at": {"$gte": one_hour_ago},
            "digest_time": "DailyBrief"
        })
        
        if recent_send:
            sent_at = recent_send.get('sent_at')
            if sent_at:
                # Handle both timezone-aware and naive datetimes
                if isinstance(sent_at, datetime):
                    if sent_at.tzinfo is None:
                        sent_at = sent_at.replace(tzinfo=timezone.utc)
                    time_since = (now - sent_at).total_seconds() / 60
                    logger.warning(f"Daily Brief recently sent ({int(time_since)} minutes ago) — continuing anyway (manual override).")
        
        # Log SMTP config at start for debugging
        import os
        logger.info(f"SMTP Config Check - Host: {os.environ.get('SMTP_HOST')}, Port: {os.environ.get('SMTP_PORT')}, User: {os.environ.get('SMTP_USER')}")
        
        # Resend Pro cleanup mode: send to active subscribers in larger controlled batches.
        subscribers = await db.subscribers.find(
            {
                "$and": [
                    {"$or": [{"active": True}, {"active": {"$exists": False}}]},
                    {"$or": [{"daily_brief": {"$ne": False}}, {"daily_brief": {"$exists": False}}]}
                ]
            },
            {"_id": 0, "email": 1}
        ).to_list(15000)
        if not subscribers:
            return {"success": False, "message": "No subscribers found"}
        
        # Deduplicate emails (case-insensitive)
        seen_emails = set()
        unique_emails = []
        for s in subscribers:
            email = s.get('email', '').lower().strip()
            if email and email not in seen_emails:
                seen_emails.add(email)
                unique_emails.append(s.get('email'))  # Keep original case
        
        daily_send_cap = int(os.environ.get("DAILY_BRIEF_SEND_CAP", "1000"))
        subscriber_emails = unique_emails[:daily_send_cap]
        logger.info(f"DIGEST: Using Resend Pro Daily Brief cap of {len(subscriber_emails)} subscriber emails from {len(unique_emails)} active subscribers")
        
        # Get latest articles with deduplication by title
        pipeline = [
            {"$sort": {"publishedDate": -1}},
            {"$group": {
                "_id": "$title",  # Group by title to remove duplicates
                "mongo_id": {"$first": "$_id"},  # Keep MongoDB _id
                "custom_id": {"$first": "$id"},  # Keep custom id if exists
                "title": {"$first": "$title"},
                "content": {"$first": "$content"},
                "category": {"$first": "$category"},
                "author": {"$first": "$author"},
                "image": {"$first": "$image"},
                "publishedDate": {"$first": "$publishedDate"},
                "source": {"$first": "$source"}
            }},
            {"$sort": {"publishedDate": -1}},
            {"$limit": 30}  # Get more to have enough after filtering
        ]
        
        recent_articles = await db.articles.aggregate(pipeline).to_list(30)
        
        # Convert IDs to string format for email links
        # IMPORTANT: Use mongo_id (ObjectId hex) as the primary ID since that's what the API expects
        for article in recent_articles:
            # Prefer mongo_id as the primary identifier (matches what /api/articles/{id} expects)
            if article.get('mongo_id'):
                article['id'] = str(article['mongo_id'])
            elif article.get('custom_id'):
                article['id'] = str(article['custom_id'])
            # Clean up temporary fields
            article.pop('mongo_id', None)
            article.pop('custom_id', None)
        
        if not recent_articles:
            return {"success": False, "message": "No articles available"}
        
        # Enhanced deduplication - check for similar topics, not just exact titles
        def get_title_keywords(title):
            """Extract key words from title for similarity checking"""
            stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'for', 'to', 'of', 'in', 'on', 'at', 'with', 'as', 'by'}
            words = title.lower().split()
            return set(w for w in words if len(w) > 3 and w not in stop_words)
        
        seen_titles = set()
        seen_keywords = []
        unique_articles = []
        
        for article in recent_articles:
            title = article.get('title', '')
            title_normalized = title.lower().strip()[:50]
            title_keywords = get_title_keywords(title)
            
            # Check for exact duplicate
            if title_normalized in seen_titles:
                continue
            
            # Check for similar topic (more than 50% keyword overlap)
            is_similar = False
            for prev_keywords in seen_keywords:
                if len(title_keywords) > 0 and len(prev_keywords) > 0:
                    overlap = len(title_keywords & prev_keywords)
                    similarity = overlap / min(len(title_keywords), len(prev_keywords))
                    if similarity > 0.5:
                        is_similar = True
                        break
            
            if not is_similar:
                seen_titles.add(title_normalized)
                seen_keywords.append(title_keywords)
                unique_articles.append(article)
        
        towns = [
            'cheshire','chester','crewe','warrington','wilmslow','knutsford','macclesfield',
            'northwich','winsford','nantwich','ellesmere port','sandbach','middlewich','congleton'
        ]

        def _is_local(article):
            category = (article.get('category','') or '').lower()
            title = (article.get('title','') or '').lower()
            content = (article.get('content','') or '').lower()[:500]
            return any(k in category for k in ['local','cheshire']) or any(t in title or t in content for t in towns)

        def _is_business(article):
            category = (article.get('category','') or '').lower()
            title = (article.get('title','') or '').lower()
            return (
                any(k in category for k in ['business','finance','economy','property'])
                or any(k in title for k in ['finance','mortgage','rates','tax','budget','inflation','jobs','housing','market'])
            )

        def _is_tech(article):
            category = (article.get('category','') or '').lower()
            title = (article.get('title','') or '').lower()

            banned_keywords = [
                'game','gaming','xbox','playstation','nintendo',
                'resident evil','horror','celebrity','showbiz'
            ]
            if any(b in title for b in banned_keywords):
                return False

            keywords = [
                'ai','artificial intelligence','chatgpt','openai','gemini','deepmind',
                'machine learning','ml','automation','robot','cyber','security',
                'data','digital','software','startup','nvidia','microsoft',
                'google','apple','tesla','chip','semiconductor','cloud',
                'enterprise','infrastructure','data centre'
            ]

            return (
                any(k in category for k in ['tech','technology','ai'])
                or any(k in title for k in keywords)
            )

        def _is_banned(article):
            category = (article.get('category','') or '').lower()
            title = (article.get('title','') or '').lower()
            content = (article.get('content','') or '').lower()[:500]
            text = f"{category} {title} {content}"

            blocked_keywords = [
                'death notices', 'death notice', 'funeral notices', 'funeral notice',
                'in memoriam', 'death announcements', 'family announcement'
            ]

            return (
                category in ['sports','sport','entertainment','celebrity','showbiz']
                or any(k in text for k in blocked_keywords)
            )

        local_bucket = []
        business_bucket = []
        tech_bucket = []
        national_bucket = []

        for a in unique_articles:
            if _is_banned(a):
                continue
            if _is_local(a):
                local_bucket.append(a)
            elif _is_business(a):
                business_bucket.append(a)
            elif _is_tech(a):
                tech_bucket.append(a)
            else:
                national_bucket.append(a)

        local_bucket = local_bucket[:3]
        business_bucket = business_bucket[:2]
        tech_bucket = tech_bucket[:1]
        national_bucket = national_bucket[:2]

        sorted_articles = (local_bucket + business_bucket + tech_bucket + national_bucket)[:10]

        logger.info(f"Manual digest: {len(sorted_articles)} articles (local={len(local_bucket)}, business={len(business_bucket)}, tech={len(tech_bucket)}, national={len(national_bucket)})")
        
        # Send Daily Brief (new format) instead of old digest
        result = email_service.send_daily_brief(
            to_emails=subscriber_emails,
            articles=sorted_articles,
            weather=None,
            travel=None,
            photo_of_day=None
        )
        
        # Handle tuple return (success_count, tracking_id)
        if isinstance(result, tuple):
            success_count, tracking_id = result
        else:
            success_count, tracking_id = result, None
        
        # Log the send
        try:
            await db.digest_log.insert_one({
                "sent_at": datetime.now(timezone.utc),
                "digest_time": "DailyBrief",
                "type": "DailyBrief",
                "date_key": datetime.now(timezone.utc).strftime('%Y%m%d'),
                "articles_count": len(sorted_articles),
                "subscribers_count": len(subscriber_emails),
                "success_count": success_count,
                "tracking_id": tracking_id,
                "manual": True  # Mark as manually triggered
            })
        except Exception as log_error:
            logger.warning(f"Failed to log digest send: {log_error}")
        
        return {
            "success": True,
            "subscribers": len(subscriber_emails),
            "articles": len(sorted_articles),
            "local_news_count": len([a for a in sorted_articles if is_local(a)]),
            "sports_count": len([a for a in sorted_articles if is_sports(a)]),
            "emails_sent": success_count,
            "email_type": "DailyBrief"
        }
        
    except Exception as e:
        logger.error(f"Error sending manual digest: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/send-digest-test")
async def send_digest_test(test_email: str = "news@cheshiretoday.co.uk", use_preview_links: bool = False, auth: bool = Depends(get_admin_auth)):
    """
    TEST ENDPOINT: Send digest to a SINGLE email address for testing.
    
    Args:
        test_email: Email to send test to
        use_preview_links: If True, links will point to preview URL (for testing link functionality)
                          If False (default), links point to production (for verifying production works)
    
    IMPORTANT: Preview and Production have DIFFERENT databases with different article IDs.
    - use_preview_links=True: Test email format, clicking links works (on preview)
    - use_preview_links=False: Links will only work after deploying to production
    
    Usage: POST /api/send-digest-test?test_email=your@email.com&use_preview_links=true
    """
    try:
        logger.info(f"TEST DIGEST: Sending test to {test_email}, preview_links={use_preview_links}")
        
        # Get latest public articles only — never include archived or Manual Review-hidden articles
        pipeline = [
            {"$match": {
                "archived": {"$ne": True},
                "manual_review_hidden_from_public": {"$ne": True}
            }},
            {"$sort": {"publishedDate": -1}},
            {"$group": {
                "_id": "$title",
                "mongo_id": {"$first": "$_id"},
                "custom_id": {"$first": "$id"},
                "title": {"$first": "$title"},
                "content": {"$first": "$content"},
                "category": {"$first": "$category"},
                "author": {"$first": "$author"},
                "image": {"$first": "$image"},
                "publishedDate": {"$first": "$publishedDate"},
                "source": {"$first": "$source"}
            }},
            {"$sort": {"publishedDate": -1}},
            {"$limit": 10}
        ]
        
        recent_articles = await db.articles.aggregate(pipeline).to_list(10)
        
        for article in recent_articles:
            if article.get('mongo_id'):
                article['id'] = str(article['mongo_id'])
            elif article.get('custom_id'):
                article['id'] = str(article['custom_id'])
            article.pop('mongo_id', None)
            article.pop('custom_id', None)
        
        if not recent_articles:
            return {"success": False, "message": "No articles available"}
        
        # Temporarily override base_url if testing with preview links
        original_base_url = email_service.base_url
        original_api_url = email_service.api_url
        if use_preview_links:
            # Get preview URL from environment
            preview_url = os.environ.get('REACT_APP_BACKEND_URL', '').replace('/api', '')
            if preview_url:
                email_service.base_url = preview_url
                email_service.api_url = f"{preview_url}/api"
                logger.info(f"TEST DIGEST: Using preview base URL: {preview_url}")
        
        try:
            # Send Daily Brief (new format) to single test email
            result = email_service.send_daily_brief(
                to_emails=[test_email],
                articles=recent_articles[:5],
                weather=None,
                travel=None,
                photo_of_day=None
            )
            
            # Handle tuple return
            if isinstance(result, tuple):
                success_count, tracking_id = result
            else:
                success_count, tracking_id = result, None
        finally:
            # Always restore original URLs
            email_service.base_url = original_base_url
            email_service.api_url = original_api_url
        
        # Return article IDs for verification
        article_info = [{"id": a.get('id'), "title": a.get('title', '')[:50]} for a in recent_articles[:5]]
        
        link_type = "PREVIEW (for testing)" if use_preview_links else "PRODUCTION"
        
        return {
            "success": success_count > 0,
            "message": f"Test Daily Brief sent to {test_email}",
            "email_type": "DailyBrief",
            "emails_sent": success_count,
            "tracking_id": tracking_id,
            "link_type": link_type,
            "articles_included": article_info,
            "note": f"Links point to {link_type}. {'Click to verify format works!' if use_preview_links else 'Will only work on production after deployment.'}"
        }
        
    except Exception as e:
        logger.error(f"Error sending test digest: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/send-weekly-roundup-test")
async def send_weekly_roundup_test(test_email: str = "news@cheshiretoday.co.uk", auth: bool = Depends(get_admin_auth)):
    """
    TEST ENDPOINT: Send Weekly Roundup to a SINGLE email address for testing.
    Does not update scheduler locks, digest_log, or email_batch_cursors.
    """
    try:
        logger.info(f"TEST WEEKLY ROUNDUP: Sending test to {test_email}")

        now = datetime.now(timezone.utc)
        one_week_ago = now - timedelta(days=7)

        big_read = await db.articles.find_one(
            {
                "archived": {"$ne": True},
                "manual_review_hidden_from_public": {"$ne": True},
                "$or": [
                    {"publishedDate": {"$gte": one_week_ago}},
                    {"publishedDate": {"$gte": one_week_ago.isoformat()}}
                ]
            },
            sort=[("view_count", -1)]
        )

        if not big_read:
            big_read = await db.articles.find_one(
                {
                    "archived": {"$ne": True},
                    "manual_review_hidden_from_public": {"$ne": True}
                },
                sort=[("publishedDate", -1)]
            )

        if not big_read:
            return {"success": False, "message": "No articles available for Weekly Roundup test"}

        if big_read.get("_id"):
            big_read["id"] = str(big_read["_id"])

        icymi_cursor = db.articles.find(
            {
                "archived": {"$ne": True},
                "manual_review_hidden_from_public": {"$ne": True},
                "$or": [
                    {"publishedDate": {"$gte": one_week_ago}},
                    {"publishedDate": {"$gte": one_week_ago.isoformat()}}
                ]
            },
            sort=[("view_count", -1)]
        ).limit(6)

        icymi_articles = []
        async for article in icymi_cursor:
            if str(article.get("_id")) != str(big_read.get("_id")):
                if is_digest_excluded(article):
                    continue
                if article.get("_id"):
                    article["id"] = str(article["_id"])
                icymi_articles.append(article)
                if len(icymi_articles) >= 5:
                    break

        result = email_service.send_weekly_roundup(
            to_emails=[test_email],
            big_read=big_read,
            icymi_articles=icymi_articles,
            property_of_week=None,
            food_review=None
        )

        if isinstance(result, tuple):
            success_count, tracking_id = result
        else:
            success_count, tracking_id = result, None

        return {
            "success": success_count > 0,
            "message": f"Test Weekly Roundup sent to {test_email}",
            "email_type": "WeeklyRoundup",
            "emails_sent": success_count,
            "tracking_id": tracking_id,
            "big_read": {
                "id": big_read.get("id"),
                "title": (big_read.get("title") or "")[:80]
            },
            "icymi_count": len(icymi_articles),
            "icymi_titles": [(a.get("title") or "")[:80] for a in icymi_articles]
        }

    except Exception as e:
        logger.error(f"Error sending Weekly Roundup test: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/send-weekly-roundup-batch-test")
async def send_weekly_roundup_batch_test(cap: int = 25, auth: bool = Depends(get_admin_auth)):
    """
    DIAGNOSTIC ENDPOINT: Send Weekly Roundup to a small rotating batch.
    Does not update scheduler locks, digest_log, or email_batch_cursors.
    Use to reproduce Resend batch behaviour safely before Sunday scheduler runs.
    """
    try:
        safe_cap = max(1, min(int(cap), 100))
        logger.info(f"TEST WEEKLY ROUNDUP BATCH: Sending diagnostic batch with cap={safe_cap}")

        subscribers = await db.subscribers.find(
            {
                "$and": [
                    {"$or": [{"active": True}, {"active": {"$exists": False}}]},
                    {"$or": [
                        {"weekly_roundup": True},
                        {"$and": [
                            {"daily_brief": True},
                            {"preferences_updated_at": {"$exists": False}}
                        ]}
                    ]}
                ]
            },
            {"_id": 0, "email": 1}
        ).to_list(15000)

        import re
        email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        seen_emails = set()
        unique_emails = []

        for s in subscribers:
            email = (s.get("email") or "").lower().strip()
            if email and email not in seen_emails and is_deliverable_newsletter_email(email):
                seen_emails.add(email)
                unique_emails.append(s.get("email"))

        subscriber_emails, batch_start, batch_next, total_eligible = await _select_rotating_email_batch(
            "WeeklyRoundup",
            unique_emails,
            safe_cap
        )

        if not subscriber_emails:
            return {"success": False, "message": "No eligible Weekly Roundup subscribers found"}

        now = datetime.now(timezone.utc)
        one_week_ago = now - timedelta(days=7)

        big_read = await db.articles.find_one(
            {"$or": [
                {"publishedDate": {"$gte": one_week_ago}},
                {"publishedDate": {"$gte": one_week_ago.isoformat()}}
            ]},
            sort=[("view_count", -1)]
        )

        if not big_read:
            big_read = await db.articles.find_one({}, sort=[("publishedDate", -1)])

        if not big_read:
            return {"success": False, "message": "No articles available for Weekly Roundup batch test"}

        if big_read.get("_id"):
            big_read["id"] = str(big_read["_id"])

        icymi_cursor = db.articles.find(
            {"$or": [
                {"publishedDate": {"$gte": one_week_ago}},
                {"publishedDate": {"$gte": one_week_ago.isoformat()}}
            ]},
            sort=[("view_count", -1)]
        ).limit(6)

        icymi_articles = []
        async for article in icymi_cursor:
            if str(article.get("_id")) != str(big_read.get("_id")):
                if is_digest_excluded(article):
                    continue
                if article.get("_id"):
                    article["id"] = str(article["_id"])
                icymi_articles.append(article)
                if len(icymi_articles) >= 5:
                    break

        result = email_service.send_weekly_roundup(
            to_emails=subscriber_emails,
            big_read=big_read,
            icymi_articles=icymi_articles,
            property_of_week=None,
            food_review=None
        )

        if isinstance(result, tuple):
            success_count, tracking_id = result
        else:
            success_count, tracking_id = result, None

        return {
            "success": success_count > 0,
            "message": f"Weekly Roundup batch diagnostic sent to {len(subscriber_emails)} subscribers",
            "email_type": "WeeklyRoundup",
            "requested_cap": cap,
            "safe_cap": safe_cap,
            "emails_selected": len(subscriber_emails),
            "emails_sent": success_count,
            "batch_start": batch_start,
            "batch_next_if_saved": batch_next,
            "total_eligible": total_eligible,
            "tracking_id": tracking_id,
            "first_domain": subscriber_emails[0].split("@", 1)[1] if subscriber_emails and "@" in subscriber_emails[0] else "unknown",
            "big_read": {
                "id": big_read.get("id"),
                "title": (big_read.get("title") or "")[:80]
            },
            "icymi_count": len(icymi_articles)
        }

    except Exception as e:
        logger.error(f"Error sending Weekly Roundup batch diagnostic: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# NEW EMAIL ENDPOINTS (January 2026)
# ============================================

class BreakingNewsRequest(BaseModel):
    headline: str
    bullet_points: List[str]  # "What we know" points
    article_url: Optional[str] = None  # Link to live updates

@api_router.post("/send-breaking-news")
async def send_breaking_news_alert(request: BreakingNewsRequest, auth: bool = Depends(get_admin_auth)):
    """
    Send Breaking News Alert to all subscribers with breaking_news preference.
    This is a manual trigger for high-priority incidents only.
    Requires admin authentication.
    """
    try:
        # Get subscribers with breaking_news preference
        subscribers = await db.subscribers.find(
            {
                "$and": [
                    {"breaking_news": True},
                    {"$or": [{"active": True}, {"active": {"$exists": False}}]}
                ]
            },
            {"_id": 0, "email": 1}
        ).to_list(1000)
        
        if not subscribers:
            return {
                "success": False,
                "message": "No subscribers found with Breaking News preference enabled"
            }
        
        subscriber_emails = [s.get('email') for s in subscribers if s.get('email')]
        
        # Send the breaking news alert
        result = email_service.send_breaking_news(
            to_emails=subscriber_emails,
            headline=request.headline,
            bullet_points=request.bullet_points,
            article_url=request.article_url
        )
        
        # Handle tuple return (success_count, tracking_id)
        if isinstance(result, tuple):
            success_count, tracking_id = result
        else:
            success_count, tracking_id = result, None
        
        # Log the send
        await db.digest_log.insert_one({
            "sent_at": datetime.now(timezone.utc),
            "digest_time": "BreakingNews",
            "type": "BreakingNews",
            "headline": request.headline,
            "subscribers_count": len(subscriber_emails),
            "success_count": success_count,
            "tracking_id": tracking_id  # For email analytics
        })
        
        return {
            "success": True,
            "message": f"Breaking News alert sent to {success_count}/{len(subscriber_emails)} subscribers",
            "headline": request.headline
        }
        
    except Exception as e:
        logger.error(f"Error sending breaking news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/digest-log")
async def get_digest_log(limit: int = 50, auth: bool = Depends(get_admin_auth)):
    """Get email digest send history"""
    try:
        logs = await db.digest_log.find(
            {},
            {"_id": 0}
        ).sort("sent_at", -1).limit(limit).to_list(limit)
        
        return {
            "success": True,
            "logs": logs,
            "total": len(logs)
        }
    except Exception as e:
        logger.error(f"Error fetching digest log: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/admin/email-config/status")
async def get_email_config_status(auth: bool = Depends(get_admin_auth)):
    """Safe email configuration diagnostics. Does not expose secrets."""
    try:
        return {
            "success": True,
            "smtp": {
                "enabled": bool(getattr(email_service, "smtp_enabled", False)),
                "host_set": bool(getattr(email_service, "smtp_host", None)),
                "user_set": bool(getattr(email_service, "smtp_user", None)),
                "password_set": bool(getattr(email_service, "smtp_password", None)),
                "from_email_set": bool(getattr(email_service, "from_email", None)),
                "from_name": getattr(email_service, "from_name", None),
            },
            "resend": {
                "enabled": bool(getattr(email_service, "resend_enabled", False)),
                "api_key_set": bool(getattr(email_service, "resend_api_key", None)),
                "from_email_set": bool(getattr(email_service, "resend_from_email", None)),
                "from_name": getattr(email_service, "resend_from_name", None),
                "reply_to_set": bool(getattr(email_service, "reply_to", None)),
            },
            "links": {
                "base_url": getattr(email_service, "base_url", None),
                "api_url": getattr(email_service, "api_url", None),
            }
        }
    except Exception as e:
        logger.error(f"Error checking email config status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/admin/email-config/validate-resend")
async def validate_resend_config(auth: bool = Depends(get_admin_auth)):
    """Validate current Resend API key with Resend without sending email. Does not expose secrets."""
    try:
        import hashlib
        import urllib.error
        import urllib.request

        key = getattr(email_service, "resend_api_key", None) or ""
        key = str(key)

        result = {
            "success": True,
            "resend_enabled": bool(getattr(email_service, "resend_enabled", False)),
            "key_exists": bool(key),
            "key_length": len(key),
            "key_starts_with": key[:3] if key else "",
            "key_ends_with": key[-4:] if key else "",
            "key_fingerprint": hashlib.sha256(key.encode("utf-8")).hexdigest()[:12] if key else "",
            "valid": False,
            "resend_status": None,
            "resend_response": None,
        }

        if not key:
            result["resend_response"] = "RESEND_API_KEY is missing"
            return result

        req = urllib.request.Request(
            "https://api.resend.com/domains",
            headers={"Authorization": f"Bearer {key}"},
        )

        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                body = response.read().decode("utf-8", errors="replace")
                result["resend_status"] = response.status
                result["resend_response"] = body[:800]
                result["valid"] = 200 <= int(response.status) < 300
                return result

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            result["resend_status"] = e.code
            result["resend_response"] = body[:800]
            result["valid"] = False
            return result

    except Exception as e:
        logger.error(f"Error validating Resend config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================================
# EMAIL ANALYTICS TRACKING
# =====================================================================================


@api_router.get("/email/track/open/{tracking_id}")
async def track_email_open(tracking_id: str, request: Request):
    """
    Track email opens via invisible tracking pixel.
    Returns a 1x1 transparent GIF.
    """
    from fastapi.responses import Response
    import base64
    
    try:
        # Log the open event
        await db.email_analytics.update_one(
            {"tracking_id": tracking_id},
            {
                "$inc": {"opens": 1},
                "$set": {"last_opened": datetime.now(timezone.utc)},
                "$push": {
                    "open_events": {
                        "timestamp": datetime.now(timezone.utc),
                        "ip": request.client.host if request.client else None,
                        "user_agent": request.headers.get("user-agent", "")[:200]
                    }
                }
            },
            upsert=True
        )
    except Exception as e:
        logger.warning(f"Failed to log email open: {e}")
    
    # Return 1x1 transparent GIF
    gif_data = base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")
    return Response(content=gif_data, media_type="image/gif")


@api_router.head("/email/track/click/{tracking_id}")
async def track_email_click_head(tracking_id: str, url: str, request: Request):
    """
    Accept HEAD checks from email security scanners without counting them as real clicks.
    Prevents noisy 404s in Render logs and avoids inflating click analytics.
    """
    try:
        validate_newsletter_click_destination(url)
    except UnsafeNewsletterClickDestination:
        raise HTTPException(status_code=400, detail="Invalid newsletter destination.")

    from fastapi.responses import Response
    return Response(status_code=204)


@api_router.get("/email/track/click/{tracking_id}")
async def track_email_click(tracking_id: str, url: str, request: Request):
    """
    Track email link clicks and redirect to target URL.
    """
    try:
        approved_url = validate_newsletter_click_destination(url)
    except UnsafeNewsletterClickDestination:
        raise HTTPException(status_code=400, detail="Invalid newsletter destination.")

    try:
        # Log the click event
        await db.email_analytics.update_one(
            {"tracking_id": tracking_id},
            {
                "$inc": {"clicks": 1},
                "$set": {"last_clicked": datetime.now(timezone.utc)},
                "$push": {
                    "click_events": {
                        "timestamp": datetime.now(timezone.utc),
                        "url": approved_url[:500],
                        "ip": request.client.host if request.client else None,
                        "user_agent": request.headers.get("user-agent", "")[:200]
                    }
                }
            },
            upsert=True
        )
    except Exception as e:
        logger.warning(f"Failed to log email click: {e}")
    
    # Redirect to the actual URL
    return RedirectResponse(url=approved_url, status_code=302)


@api_router.get("/admin/email-analytics")
async def get_email_analytics(days: int = 30, auth: bool = Depends(get_admin_auth)):
    """
    Get email analytics for the admin dashboard.
    Returns open rates, click rates, and engagement metrics.
    """
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get digest logs for the period
        digest_logs = await db.digest_log.find(
            {"sent_at": {"$gte": cutoff_date}}
        ).sort("sent_at", -1).to_list(1000)
        
        # Get analytics data
        analytics_data = await db.email_analytics.find(
            {"$or": [
                {"last_opened": {"$gte": cutoff_date}},
                {"last_clicked": {"$gte": cutoff_date}}
            ]}
        ).to_list(10000)
        
        # Calculate totals
        total_sent = sum(log.get("subscribers_count", 0) for log in digest_logs)
        total_opens = sum(a.get("opens", 0) for a in analytics_data)
        total_clicks = sum(a.get("clicks", 0) for a in analytics_data)
        unique_openers = len([a for a in analytics_data if a.get("opens", 0) > 0])
        unique_clickers = len([a for a in analytics_data if a.get("clicks", 0) > 0])
        
        # Calculate rates
        open_rate = (unique_openers / total_sent * 100) if total_sent > 0 else 0
        click_rate = (unique_clickers / total_sent * 100) if total_sent > 0 else 0
        click_to_open_rate = (unique_clickers / unique_openers * 100) if unique_openers > 0 else 0
        
        # Get breakdown by email type
        type_breakdown = {}
        for log in digest_logs:
            email_type = log.get("type", log.get("digest_time", "Unknown"))
            if email_type not in type_breakdown:
                type_breakdown[email_type] = {"sent": 0, "success": 0}
            type_breakdown[email_type]["sent"] += log.get("subscribers_count", 0)
            type_breakdown[email_type]["success"] += log.get("success_count", 0)
        
        # Get recent sends with analytics
        recent_sends = []
        for log in digest_logs[:10]:
            tracking_id = log.get("tracking_id")
            opens = 0
            clicks = 0
            if tracking_id:
                matching_analytics = await db.email_analytics.find(
                    {"tracking_id": {"$regex": f"^{re.escape(tracking_id)}"}}
                ).to_list(10000)
                opens = sum(a.get("opens", 0) for a in matching_analytics)
                clicks = sum(a.get("clicks", 0) for a in matching_analytics)
            
            recent_sends.append({
                "sent_at": log.get("sent_at").isoformat() if log.get("sent_at") else None,
                "type": log.get("type", log.get("digest_time", "Unknown")),
                "subscribers": log.get("subscribers_count", 0),
                "delivered": log.get("success_count", 0),
                "opens": opens,
                "clicks": clicks,
                "headline": log.get("headline", "")[:60] if log.get("headline") else None
            })
        
        return {
            "success": True,
            "period_days": days,
            "summary": {
                "total_emails_sent": total_sent,
                "total_opens": total_opens,
                "total_clicks": total_clicks,
                "unique_openers": unique_openers,
                "unique_clickers": unique_clickers,
                "open_rate": round(open_rate, 1),
                "click_rate": round(click_rate, 1),
                "click_to_open_rate": round(click_to_open_rate, 1)
            },
            "by_type": type_breakdown,
            "recent_sends": recent_sends
        }
        
    except Exception as e:
        logger.error(f"Error fetching email analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/admin/email-analytics/trends")
async def get_email_analytics_trends(auth: bool = Depends(get_admin_auth)):
    """
    Get email analytics trends over the past 30 days for charts.
    """
    try:
        # Get daily aggregates for the past 30 days
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        # Aggregate digest logs by day
        pipeline = [
            {"$match": {"sent_at": {"$gte": cutoff_date}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$sent_at"}},
                "emails_sent": {"$sum": "$subscribers_count"},
                "delivered": {"$sum": "$success_count"},
                "sends_count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        daily_sends = await db.digest_log.aggregate(pipeline).to_list(31)
        
        # Build trend data
        trends = []
        for day in daily_sends:
            trends.append({
                "date": day["_id"],
                "sent": day["emails_sent"],
                "delivered": day["delivered"],
                "sends": day["sends_count"]
            })
        
        return {
            "success": True,
            "trends": trends
        }
        
    except Exception as e:
        logger.error(f"Error fetching email trends: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/send-announcement-email")
async def send_migration_announcement(auth: bool = Depends(get_admin_auth)):
    """
    Send one-time announcement email to ALL subscribers about the new email strategy.
    This migrates everyone to Daily Brief and informs them about preference options.
    Requires admin authentication.
    """
    try:
        # Get active subscribers only
        subscribers = await db.subscribers.find(
            {"$or": [{"active": True}, {"active": {"$exists": False}}]},
            {"_id": 0, "email": 1}
        ).to_list(10000)
        
        if not subscribers:
            return {
                "success": False,
                "message": "No subscribers found"
            }
        
        subscriber_emails = [s.get('email') for s in subscribers if s.get('email')]
        
        # Send the announcement email
        success_count = email_service.send_announcement_email(to_emails=subscriber_emails)
        
        # Update all subscribers to have daily_brief enabled by default
        await db.subscribers.update_many(
            {"$or": [{"active": True}, {"active": {"$exists": False}}]},
            {"$set": {"daily_brief": True}}
        )
        
        # Log the send
        await db.digest_log.insert_one({
            "sent_at": datetime.now(timezone.utc),
            "digest_time": "Announcement",
            "type": "MigrationAnnouncement",
            "date_key": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "subscribers_count": len(subscriber_emails),
            "success_count": success_count
        })
        
        return {
            "success": True,
            "message": f"Announcement email sent to {success_count}/{len(subscriber_emails)} subscribers",
            "subscribers_migrated": len(subscriber_emails)
        }
        
    except Exception as e:
        logger.error(f"Error sending announcement email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/send-site-update-part1")
async def send_site_update_part1(auth: bool = Depends(get_admin_auth)):
    """Send Site Update (Part 1) to ALL subscribers. Requires admin authentication."""
    try:
        subscribers = await db.subscribers.find(
            {"$or": [{"active": True}, {"active": {"$exists": False}}]},
            {"_id": 0, "email": 1}
        ).to_list(10000)
        if not subscribers:
            return {"success": False, "message": "No subscribers found"}

        subscriber_emails = [s.get("email") for s in subscribers if s.get("email")]
        success_count = email_service.send_site_update_part1(to_emails=subscriber_emails)

        await db.digest_log.insert_one({
            "sent_at": datetime.now(timezone.utc),
            "digest_time": "SiteUpdatePart1",
            "type": "SiteUpdatePart1",
            "date_key": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "subscribers_count": len(subscriber_emails),
            "success_count": success_count
        })


        # Lock this endpoint after successful send (global one-time)
        await db.system_flags.update_one(
            {"key": "site_update_part1_sent_global"},
            {"$set": {"key": "site_update_part1_sent_global", "value": True, "sent_at": datetime.now(timezone.utc)}},
            upsert=True
        )
        return {
            "success": True,
            "message": f"Site Update (Part 1) sent to {success_count}/{len(subscriber_emails)} subscribers",
            "subscribers_targeted": len(subscriber_emails)
        }
    except Exception as e:
        logger.error(f"Error sending site update part 1: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@api_router.post("/send-site-update-part2")
async def send_site_update_part2(auth: bool = Depends(get_admin_auth)):
    """Send Site Update (Part 2) to ALL subscribers. Requires admin authentication."""
    try:
        subscribers = await db.subscribers.find(
            {"$or": [{"active": True}, {"active": {"$exists": False}}]},
            {"_id": 0, "email": 1}
        ).to_list(10000)
        if not subscribers:
            return {"success": False, "message": "No subscribers found"}

        subscriber_emails = [s.get("email") for s in subscribers if s.get("email")]
        success_count = email_service.send_site_update_part2(to_emails=subscriber_emails)

        await db.digest_log.insert_one({
            "sent_at": datetime.now(timezone.utc),
            "digest_time": "SiteUpdatePart2",
            "type": "SiteUpdatePart2",
            "date_key": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "subscribers_count": len(subscriber_emails),
            "success_count": success_count
        })


        # Lock this endpoint after successful send (global one-time)
        await db.system_flags.update_one(
            {"key": "site_update_part2_sent_global"},
            {"$set": {"key": "site_update_part2_sent_global", "value": True, "sent_at": datetime.now(timezone.utc)}},
            upsert=True
        )
        return {
            "success": True,
            "message": f"Site Update (Part 2) sent to {success_count}/{len(subscriber_emails)} subscribers",
            "subscribers_targeted": len(subscriber_emails)
        }
    except Exception as e:
        logger.error(f"Error sending site update part 2: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/admin/run-onboarding-emails")
async def admin_run_onboarding_emails(dry_run: int = 1, auth: bool = Depends(get_admin_auth)):
    """
    Run onboarding emails based on subscriber age:
      - Day 3: Site Update Part 1
      - Day 7: Site Update Part 2
    Idempotent per-subscriber via site_update_part1_sent_at / site_update_part2_sent_at.

    dry_run=1: returns counts + sample recipients, sends nothing
    dry_run=0: sends + writes sent_at markers + logs to digest_log
    """
    try:

        # Disabled by default (we are using manual one-time buttons post-domain-swap)
        if os.getenv("ENABLE_ONBOARDING_AUTOMATION", "0") != "1":
            raise HTTPException(status_code=404, detail="Not Found")
        now = datetime.now(timezone.utc)

        # Pull subscribers (keep it light: only fields we need)
        subs = await db.subscribers.find(
            {},
            {"_id": 0, "email": 1, "created_at": 1, "subscribed_at": 1,
             "active": 1, "site_update_part1_sent_at": 1, "site_update_part2_sent_at": 1}
        ).to_list(20000)

        def parse_iso(dt_str: str):
            if not dt_str:
                return None
            try:
                # Handles 'Z' sometimes
                dt_str2 = dt_str.replace("Z", "+00:00")
                return datetime.fromisoformat(dt_str2)
            except Exception:
                return None

        due_part1 = []
        due_part2 = []

        for sub in subs:
            email = (sub.get("email") or "").strip().lower()
            if not email:
                continue

            # Treat missing active as active=True (back-compat)
            if sub.get("active") is False:
                continue

            created = parse_iso(sub.get("created_at")) or parse_iso(sub.get("subscribed_at"))
            if not created:
                continue

            age_days = (now - created).total_seconds() / 86400.0

            if (sub.get("site_update_part1_sent_at") in (None, "", False)) and age_days >= 3:
                due_part1.append(email)

            if (sub.get("site_update_part2_sent_at") in (None, "", False)) and age_days >= 7:
                due_part2.append(email)

        # De-dupe and make deterministic
        due_part1 = sorted(set(due_part1))
        due_part2 = sorted(set(due_part2))

        # If someone qualifies for Day 7 but not Day 3 (old subscriber missing flags),
        # we still allow Part 2, but we can also optionally send Part 1 first.
        # We'll keep it simple + explicit: send what is due independently.

        preview = {
            "success": True,
            "dry_run": int(dry_run),
            "due_part1_count": len(due_part1),
            "due_part2_count": len(due_part2),
            "sample_part1": due_part1[:10],
            "sample_part2": due_part2[:10],
        }

        if int(dry_run) == 1:
            return preview

        # Actually send
        sent1 = 0
        sent2 = 0

        if due_part1:
            sent1 = email_service.send_site_update_part1(to_emails=due_part1)
            await db.subscribers.update_many(
                {"email": {"$in": due_part1}},
                {"$set": {"site_update_part1_sent_at": now.isoformat(), "created_at": {"$ifNull": ["$created_at", "$subscribed_at"]}}}
            )
            await db.digest_log.insert_one({
                "sent_at": now,
                "digest_time": "AutoOnboarding",
                "type": "SiteUpdatePart1Auto",
                "subscribers_count": len(due_part1),
                "success_count": sent1
            })

        if due_part2:
            sent2 = email_service.send_site_update_part2(to_emails=due_part2)
            await db.subscribers.update_many(
                {"email": {"$in": due_part2}},
                {"$set": {"site_update_part2_sent_at": now.isoformat(), "created_at": {"$ifNull": ["$created_at", "$subscribed_at"]}}}
            )
            await db.digest_log.insert_one({
                "sent_at": now,
                "digest_time": "AutoOnboarding",
                "type": "SiteUpdatePart2Auto",
                "subscribers_count": len(due_part2),
                "success_count": sent2
            })

        return {
            **preview,
            "sent_part1": sent1,
            "sent_part2": sent2,
            "message": f"Onboarding run complete. Part1: {sent1}/{len(due_part1)}, Part2: {sent2}/{len(due_part2)}"
        }

    except Exception as e:
        logger.error(f"Error running onboarding emails: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

        subscriber_emails = [s.get("email") for s in subscribers if s.get("email")]
        success_count = email_service.send_site_update_part2(to_emails=subscriber_emails)

        await db.digest_log.insert_one({
            "sent_at": datetime.now(timezone.utc),
            "digest_time": "SiteUpdatePart2",
            "type": "SiteUpdatePart2",
            "date_key": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "subscribers_count": len(subscriber_emails),
            "success_count": success_count
        })

        return {
            "success": True,
            "message": f"Site Update (Part 2) sent to {success_count}/{len(subscriber_emails)} subscribers",
            "subscribers_targeted": len(subscriber_emails)
        }
    except Exception as e:
        logger.error(f"Error sending site update part 2: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class CampaignEmailRequest(BaseModel):
    subject: str
    html: Optional[str] = None
    text: Optional[str] = None
    mode: str = "test"  # "test" or "all"
    test_email: Optional[str] = None


@api_router.post("/admin/send-campaign-email")
async def admin_send_campaign_email(request: CampaignEmailRequest, auth: bool = Depends(get_admin_auth)):
    """Send a manual campaign email. mode=test sends only to test_email; mode=all sends to all subscribers."""
    try:
        subject = (request.subject or "").strip()
        if not subject:
            raise HTTPException(status_code=400, detail="Subject is required")

        html = (request.html or "").strip()
        text = (request.text or "").strip()

        if not html and not text:
            raise HTTPException(status_code=400, detail="Provide at least html or text content")

        mode = (request.mode or "test").strip().lower()
        if mode not in ("test", "all"):
            raise HTTPException(status_code=400, detail="mode must be 'test' or 'all'")

        # Determine recipients
        if mode == "test":
            test_email = (request.test_email or ADMIN_USERNAME or "").strip().lower()
            if not test_email:
                raise HTTPException(status_code=400, detail="test_email is required for test mode")
            to_emails = [test_email]
        else:
            subs = await db.subscribers.find(
                {
                    "$or": [
                        {"active": True},
                        {"active": {"$exists": False}},
                    ]
                },
                {"_id": 0, "email": 1},
            ).to_list(10000)
            to_emails = [x.get("email") for x in subs if x.get("email")]
            if not to_emails:
                return {"success": False, "message": "No subscribers found"}

        tracking_id = email_service._generate_tracking_id("ManualCampaign")

        # If HTML, inject tracking pixel and tracked links placeholders
        if html:
            # ensure pixel
            if "</body>" in html:
                html_base = html.replace("</body>", f"{email_service._get_tracking_pixel(tracking_id)}</body>")
            else:
                html_base = html + email_service._get_tracking_pixel(tracking_id)

        success_count = 0
        for email in to_emails:
            prefs_url = f"{email_service.base_url}/newsletter/preferences"
            unsub_url = f"{email_service.base_url}/unsubscribe"

            html_personal = None
            if html:
                html_personal = html_base.replace("__PREFS_URL__", prefs_url).replace("__UNSUB_URL__", unsub_url)

            # text: if placeholders exist, replace them with raw URLs
            text_personal = None
            if text:
                text_personal = text.replace("__PREFS_URL__", prefs_url).replace("__UNSUB_URL__", unsub_url)

            if email_service._send_email(email, subject, html_personal or ("<p>" + (text_personal or "") + "</p>"), text_personal):
                success_count += 1

        await db.digest_log.insert_one({
            "sent_at": datetime.now(timezone.utc),
            "digest_time": "ManualCampaign",
            "type": "ManualCampaign",
            "subscribers_count": len(to_emails),
            "success_count": success_count,
            "mode": mode,
            "subject": subject,
            "tracking_id": tracking_id
        })

        return {
            "success": True,
            "message": f"Campaign sent to {success_count}/{len(to_emails)} recipients",
            "mode": mode,
            "tracking_id": tracking_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending manual campaign: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/")
async def root():
    return {"message": "Cheshire News API"}

# Health check endpoint for Kubernetes (at root level, not under /api)
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes liveness probes - returns immediately"""
    return {"status": "healthy", "service": "cheshire-news"}



@api_router.get("/health")
async def api_health_check():
    """Alias for health check under /api"""
    return {"status": "healthy", "service": "cheshire-news"}
@api_router.get("/health")
async def api_health_check():
    """Alias for Render/cron/probes that hit /api/health"""
    return await health_check()

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint for Kubernetes - verifies DB connection"""
    try:
        # Quick DB ping to verify connection
        await db.command("ping")
        return {"status": "ready", "service": "cheshire-news", "database": "connected"}
    except Exception as e:
        from fastapi import Response
        return Response(
            content=f'{{"status": "not_ready", "error": "{str(e)}"}}',
            status_code=503,
            media_type="application/json"
        )

# Also expose sitemap via /api/ prefix for ingress routing
@api_router.get("/sitemap.xml")
async def api_sitemap():
    """Sitemap accessible via /api/sitemap.xml"""
    return await generate_sitemap()


def _parse_sitemap_datetime(value, *, now: Optional[datetime] = None):
    if not value:
        return None

    parsed = None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None
        try:
            parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
    else:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    else:
        current = current.astimezone(timezone.utc)

    if parsed > current:
        return None
    return parsed


def _article_sitemap_datetime(article: dict, *, now: Optional[datetime] = None):
    for field in (
        "updated_at",
        "modified_at",
        "manual_edited_at",
        "updatedAt",
        "publishedDate",
        "created_at",
    ):
        parsed = _parse_sitemap_datetime(article.get(field), now=now)
        if parsed is not None:
            return parsed
    return None


def _sitemap_lastmod_value(value, *, now: Optional[datetime] = None):
    parsed = _parse_sitemap_datetime(value, now=now)
    return parsed.strftime("%Y-%m-%d") if parsed is not None else None


def _newest_article_sitemap_lastmod(
    articles: List[dict],
    *,
    now: Optional[datetime] = None,
):
    dates = [
        parsed
        for article in articles
        if (parsed := _article_sitemap_datetime(article, now=now)) is not None
    ]
    return max(dates).strftime("%Y-%m-%d") if dates else None


def _append_sitemap_lastmod(xml_content: str, lastmod: Optional[str]) -> str:
    if lastmod:
        xml_content += f"    <lastmod>{lastmod}</lastmod>\n"
    return xml_content


@app.get("/sitemap.xml")
async def generate_sitemap():
    """Generate dynamic sitemap.xml for Google Search Console"""
    from fastapi.responses import Response
    # datetime imported at top-level
    import xml.sax.saxutils as saxutils
    
    try:
        # ALWAYS use production domain for sitemap - this is for Google Search Console
        # which indexes cheshiretoday.co.uk, not preview/staging environments
        base_url = 'https://cheshiretoday.co.uk'
        
        # Get recent active articles from database (limit to 500 for performance).
        # Sitemap should submit only index-worthy strategic pages, not every transient RSS item.
        articles = await db.articles.find(
            {
                "manual_review_hidden_from_public": {"$ne": True},
                "$or": [
                    {"archived": {"$ne": True}},
                    {"force_live": True},
                ],
            },
            {
                '_id': 1, 'id': 1, 'publishedDate': 1, 'created_at': 1,
                'updated_at': 1, 'modified_at': 1, 'manual_edited_at': 1,
                'updatedAt': 1, 'category': 1, 'image': 1, 'title': 1,
                'scope': 1, 'source': 1, 'source_url': 1, 'force_live': 1,
                'archived': 1, 'location': 1, 'priority_location': 1,
                'is_local_source': 1, 'is_cheshire_related': 1,
            }
        ).sort('publishedDate', -1).limit(500).to_list(500)

        strategic_article_categories = {
            "Local News",
            "UK News",
            "Business",
            "Finance",
            "Tax",
            "Property",
            "Tech",
            "AI",
            "AI & Tech",
        }

        # Main sitemap should submit strategic, index-worthy article URLs only.
        # This does not affect article visibility, imports, homepage, RSS, Facebook links, or archives.
        sitemap_excluded_title_patterns = [
            r"\bcrime\b",
            r"\bcrash\b",
            r"\bsmash\b",
            r"\bhit-and-run\b",
            r"\bemergency services\b",
            r"\bknocked off\b",
            r"\bpolice\b",
            r"\bcourt\b",
            r"\bjailed\b",
            r"\bcharged\b",
            r"\bmurder\b",
            r"\bassault\b",
            r"\bcocaine\b",
            r"\bdrugs?\b",
            r"\bgangs?\b",
            r"\bdevastating diagnosis\b",
            r"\bstarted to ache\b",
            r"\bcancer\b",
            r"\btributes?\b",
            r"\bfuneral\b",
            r"\bdied\b",
            r"\bdeath\b",
            r"\blost everything\b",
            r"\bsports quiz\b",
            r"\bjohn fury\b",
            r"\bnigel farage\b",
            r"\belon musk has lost\b",
            r"\bcameo\b",
            r"\bporn\b",
            r"\bstarwatch\b",
            r"\bmoon\b",
            r"\bperiod drama\b",
            r"\bfree to watch\b",
            r"\bhair dryer\b",
            r"\bcruise ship\b",
            r"\bdoom soundtrack\b",
            r"\bpokemon\b",
            r"\balton towers\b",
            r"\banimal park\b",
            r"\bhedgehogs?\b",
            r"\btiger cubs?\b",
            r"\bx limits\b",
            r"\bfreeloaders\b",
            r"\bairbus gets hpc\b",
            r"\bhpc-as-a-service\b",
            r"\bzte showcases\b",
            r"\bbrazil\b",
            r"\btyphoon jets\b",
            r"\bf-35\b",
            r"\bmaga\b",
            r"\bstarbucks korea\b",
            r"\bswatch\b",
            r"\btank day\b",
            r"\bsubmarine cables\b",
            r"\bstrait of hormuz\b",
            r"\bnothing phone\b",
            r"\bgps jamming\b",
            r"\bcloud-managed earbuds\b",
            r"\bpandemic preparedness\b",
            r"\binfection risk\b",
            r"\bbest fans?\b",
            r"\bkeep you cool\b",
            r"\bbeat the heat\b",
            r"\btraffic queues\b",
            r"\bhottest day\b",
            r"\bhot day\b",
            r"\bworld'?s first trillionaire\b",
            r"\btrillionaire\b",
            r"\bmars colony\b",
            r"\bgrok warnings?\b",
            r"\bspacex\b",
            r"\bdems?\b",
            r"\btrump\b",
            r"\bcapri pants\b",
            r"\bpadel rackets\b",
            r"\bglow worms?\b",
            r"\bslime moulds?\b",
            r"\bscotland'?s declining rainforest\b",
            r"\bwater campaigner\b",
            r"\bbathing site\b",
            r"\bflipper one\b",
            r"\blondoners\b",
            r"\bworking-class voices\b",
            r"\bdriving test\b",
            r"\bswinney\b",
            r"\bin pictures\b",
            r"\bpictures from\b",
            r"\banniversary celebrations\b",
            r"\bfirst minister vote\b",
            r"\|\s*letter\b",
            r"\bletters\b",
            r"\bpeople fixing the world\b",
            r"\bsearch history\b",
            r"\bwhat we ask google\b",
            r"\bspoil heaps\b",
            r"\blead mining\b",
            r"\bbanks of pansies\b",
            r"\bnature itself\b",
            r"\bhantavirus\b",
            r"\bgroup project\b",
            r"\bpodcaster\b",
            r"\bdaughter a millionaire\b",
        ]

        cheshire_terms = [
            "cheshire", "chester", "crewe", "wilmslow", "warrington", "macclesfield",
            "northwich", "nantwich", "knutsford", "congleton", "sandbach", "ellesmere port",
            "middlewich", "winsford", "alderley edge", "hale", "runcorn", "widnes",
            "leighton", "creamfields"
        ]

        def include_article_in_sitemap(article):
            title = str(article.get("title") or "").strip()
            category = str(article.get("category") or "").strip()
            image = str(article.get("image") or "").strip()
            scope = str(article.get("scope") or "").strip().lower()
            source = str(article.get("source") or "").strip().lower()

            if not title or not image:
                return False
            if category not in strategic_article_categories:
                return False

            title_lower = title.lower()
            combined = f"{title_lower} {source}"

            if any(re.search(pattern, title_lower) for pattern in sitemap_excluded_title_patterns):
                return False

            if category == "Local News":
                return scope == "cheshire" or any(term in combined for term in cheshire_terms)

            if category in {
                "UK News",
                "Business",
                "Finance",
                "Tax",
                "Property",
                "Tech",
                "AI",
                "AI & Tech",
            }:
                return True

            return False

        now_utc = datetime.now(timezone.utc)
        sitemap_articles = [
            article for article in articles if include_article_in_sitemap(article)
        ]
        newest_article_lastmod = _newest_article_sitemap_lastmod(
            sitemap_articles,
            now=now_utc,
        )

        category_lastmods = {}
        for category_slug, category_config in PUBLIC_CATEGORY_HUBS.items():
            matching = [
                article
                for article in sitemap_articles
                if _article_matches_public_category_hub(article, category_config)
            ]
            category_lastmods[category_slug] = _newest_article_sitemap_lastmod(
                matching,
                now=now_utc,
            )

        location_lastmods = {}
        for location in PUBLIC_LOCATION_HUBS:
            matching = [
                article
                for article in sitemap_articles
                if _article_matches_public_location_hub(article, location)
            ]
            location_lastmods[location] = _newest_article_sitemap_lastmod(
                matching,
                now=now_utc,
            )

        # Start building XML with image namespace
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
        
        # Add homepage
        xml_content += '  <url>\n'
        xml_content += f'    <loc>{base_url}/</loc>\n'
        xml_content = _append_sitemap_lastmod(xml_content, newest_article_lastmod)
        xml_content += '    <changefreq>daily</changefreq>\n'
        xml_content += '    <priority>1.0</priority>\n'
        xml_content += '  </url>\n'
        
        # Add plain HTML article-index crawl path for search engines
        xml_content += '  <url>\n'
        xml_content += f'    <loc>{base_url}/article-index</loc>\n'
        xml_content = _append_sitemap_lastmod(xml_content, newest_article_lastmod)
        xml_content += '    <changefreq>daily</changefreq>\n'
        xml_content += '    <priority>0.9</priority>\n'
        xml_content += '  </url>\n'

        # Add location pages for Local SEO
        for loc in sorted(PUBLIC_LOCATION_HUBS):
            xml_content += '  <url>\n'
            xml_content += f'    <loc>{base_url}/{loc}</loc>\n'
            xml_content = _append_sitemap_lastmod(
                xml_content,
                location_lastmods[loc],
            )
            xml_content += '    <changefreq>daily</changefreq>\n'
            xml_content += '    <priority>0.9</priority>\n'
            xml_content += '  </url>\n'
        
        # Add category pages
        for category_slug in PUBLIC_CATEGORY_HUBS:
            xml_content += '  <url>\n'
            xml_content += f'    <loc>{base_url}/category/{category_slug}</loc>\n'
            xml_content = _append_sitemap_lastmod(
                xml_content,
                category_lastmods[category_slug],
            )
            xml_content += '    <changefreq>daily</changefreq>\n'
            xml_content += '    <priority>0.8</priority>\n'
            xml_content += '  </url>\n'
        
        # Add published authority guide pages
        authority_pages = await db.authority_pages.find(
            {"status": {"$in": ["published", "live"]}},
            {"_id": 0, "slug": 1, "updatedAt": 1, "sections": 1}
        ).sort("updatedAt", -1).limit(250).to_list(250)

        for page in authority_pages:
            guide_slug = str(page.get("slug") or "").strip()
            if not guide_slug:
                continue

            # Keep thin/stub authority pages out of the sitemap until they have
            # enough useful guide content. Pages remain live, but are not
            # submitted for indexing while under the quality threshold.
            guide_sections = page.get("sections") if isinstance(page.get("sections"), list) else []
            guide_content_len = sum(
                len(str(section.get("content") or "").strip())
                for section in guide_sections
                if isinstance(section, dict)
            )
            if guide_content_len < 700:
                continue

            guide_lastmod = _sitemap_lastmod_value(
                page.get("updatedAt"),
                now=now_utc,
            )

            xml_content += '  <url>\n'
            xml_content += f'    <loc>{saxutils.escape(base_url)}/guides/{saxutils.escape(guide_slug)}</loc>\n'
            xml_content = _append_sitemap_lastmod(xml_content, guide_lastmod)
            xml_content += '    <changefreq>weekly</changefreq>\n'
            xml_content += '    <priority>0.7</priority>\n'
            xml_content += '  </url>\n'

        # Add only strategic, index-worthy articles with images
        for article in sitemap_articles:
            article_id = str(article.get("_id") or article.get("id") or "")
            raw_title = str(article.get("title") or "Cheshire Today Article")
            slug = re.sub(r"[^a-z0-9]+","-", raw_title.lower()).strip("-")
            slug = (slug[:80] if slug else "article")
            article_lastmod = _article_sitemap_datetime(article, now=now_utc)
            
            # Get article image and title
            article_image = article.get('image', '')
            article_title = article.get('title', 'Cheshire Today Article')
            
            xml_content += '  <url>\n'
            xml_content += f'    <loc>{saxutils.escape(base_url)}/article/{article_id}/{slug}</loc>\n'
            xml_content = _append_sitemap_lastmod(
                xml_content,
                article_lastmod.strftime("%Y-%m-%d")
                if article_lastmod is not None
                else None,
            )
            xml_content += '    <changefreq>weekly</changefreq>\n'
            xml_content += '    <priority>0.6</priority>\n'
            
            # Add image information if available
            if article_image:
                xml_content += '    <image:image>\n'
                xml_content += f'      <image:loc>{saxutils.escape(article_image)}</image:loc>\n'
                xml_content += f'      <image:title>{saxutils.escape(article_title)}</image:title>\n'
                xml_content += '    </image:image>\n'
            
            xml_content += '  </url>\n'
        
        xml_content += '</urlset>'
        
        return Response(content=xml_content, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error generating sitemap: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/news-sitemap.xml")
@app.get("/news-sitemap.xml")
async def generate_news_sitemap():
    """Generate Google News sitemap for recent articles (last 48 hours)"""
    from fastapi.responses import Response
    # datetime, timedelta imported at top-level
    import xml.sax.saxutils as saxutils
    
    try:
        base_url = 'https://cheshiretoday.co.uk'
        
        # Get articles from last 48 hours (Google News requirement)
        cutoff_date = datetime.utcnow() - timedelta(hours=48)
        
        cutoff_iso = cutoff_date.isoformat()

        articles = await db.articles.find(
            {
                "archived": {"$ne": True},
                "manual_review_hidden_from_public": {"$ne": True},
                "$or": [
                    {"publishedDate": {"$gte": cutoff_date}},
                    {"publishedDate": {"$gte": cutoff_iso}},
                ],
            },
            {"_id": 1, "id": 1, "title": 1, "publishedDate": 1, "created_at": 1, "category": 1, "scope": 1, "source": 1, "source_url": 1}
        ).sort("created_at", -1).limit(1000).to_list(1000)

        strategic_news_categories = {"Local News", "Business", "Finance", "Tax", "Property", "Tech", "AI", "AI & Tech"}

        # Keep the Google News sitemap tightly aligned with Cheshire Today's positioning:
        # Cheshire local + business/finance + practical AI/tech. This does not affect
        # imports, homepage visibility, article pages, RSS, or archives.
        news_sitemap_excluded_title_patterns = [
            # Crime, courts, accidents, emergency filler
            r"\bcrime\b",
            r"\bcrash\b",
            r"\bsmash\b",
            r"\bhit-and-run\b",
            r"\bemergency services\b",
            r"\bknocked off\b",
            r"\bpolice\b",
            r"\bcourt\b",
            r"\bjailed\b",
            r"\bcharged\b",
            r"\bmurder\b",
            r"\bassault\b",
            r"\bcocaine\b",
            r"\bdrugs?\b",
            r"\bgangs?\b",

            # Personal tragedy / human-interest filler unsuitable for strategic sitemap
            r"\bdevastating diagnosis\b",
            r"\bstarted to ache\b",
            r"\bcancer\b",
            r"\btributes?\b",
            r"\bfuneral\b",
            r"\bdied\b",
            r"\bdeath\b",
            r"\blost everything\b",

            # Celebrity/politics/lifestyle/entertainment filler
            r"\bsports quiz\b",
            r"\bjohn fury\b",
            r"\bnigel farage\b",
            r"\belon musk has lost\b",
            r"\bcameo\b",
            r"\bporn\b",
            r"\bstarwatch\b",
            r"\bmoon\b",
            r"\bperiod drama\b",
            r"\bfree to watch\b",
            r"\bhair dryer\b",
            r"\bcruise ship\b",
            r"\bdoom soundtrack\b",
            r"\bpokemon\b",
            r"\balton towers\b",
            r"\banimal park\b",
            r"\bhedgehogs?\b",
            r"\btiger cubs?\b",

            # Weak/global tech or international filler not useful for Cheshire readers
            r"\bx limits\b",
            r"\bfreeloaders\b",
            r"\bairbus gets hpc\b",
            r"\bhpc-as-a-service\b",
            r"\bzte showcases\b",
            r"\bbrazil\b",
            r"\btyphoon jets\b",
            r"\bf-35\b",
            r"\bmaga\b",
            r"\bstarbucks korea\b",
            r"\bswatch\b",
            r"\btank day\b",
            r"\bsubmarine cables\b",
            r"\bstrait of hormuz\b",
            r"\bnothing phone\b",
            r"\bgps jamming\b",
            r"\bcloud-managed earbuds\b",
            r"\bpandemic preparedness\b",
            r"\binfection risk\b",
            r"\bbest fans?\b",
            r"\bkeep you cool\b",
            r"\bbeat the heat\b",
            r"\btraffic queues\b",
            r"\bhottest day\b",
            r"\bhot day\b",
            r"\bworld'?s first trillionaire\b",
            r"\btrillionaire\b",
            r"\bmars colony\b",
            r"\bgrok warnings?\b",
            r"\bspacex\b",
            r"\bdems?\b",
            r"\btrump\b",
            r"\bcapri pants\b",
            r"\bpadel rackets\b",
            r"\bglow worms?\b",
            r"\bslime moulds?\b",
            r"\bscotland'?s declining rainforest\b",
            r"\bwater campaigner\b",
            r"\bbathing site\b",
            r"\bflipper one\b",

            # Weak national/local filler that does not support authority positioning
            r"\blondoners\b",
            r"\bworking-class voices\b",
            r"\bdriving test\b",
            r"\bswinney\b",
            r"\bin pictures\b",
            r"\bpictures from\b",
            r"\banniversary celebrations\b",
            r"\bfirst minister vote\b",
            r"\|\s*letter\b",
            r"\bletters\b",
            r"\breview\b",
            r"\bsearch history\b",
            r"\bwhat we ask google\b",
            r"\bspoil heaps\b",
            r"\blead mining\b",
            r"\bbanks of pansies\b",
            r"\bnature itself\b",
            r"\bhantavirus\b",
            r"\bgroup project\b",
            r"\bpodcaster\b",
            r"\bdaughter a millionaire\b",
        ]

        cheshire_terms = [
            "cheshire", "chester", "crewe", "wilmslow", "warrington", "macclesfield",
            "northwich", "nantwich", "knutsford", "congleton", "sandbach", "ellesmere port",
            "middlewich", "winsford", "alderley edge", "hale", "runcorn", "widnes",
            "leighton", "creamfields"
        ]

        business_impact_terms = [
            "uk", "britain", "britons", "government", "supermarkets", "inflation",
            "unemployment", "jobs", "roles", "workers", "wages", "costs", "prices",
            "energy", "bills", "petrol", "pensions", "bank", "mortgage", "rent",
            "tax", "hs2", "imf", "traders", "high street", "ombudsman", "savings",
            "childcare", "insurance", "food prices", "growth forecast", "job",
            "recruitment", "sales", "air conditioning", "geothermal", "start-ups",
            "startups", "startup"
        ]

        practical_tech_terms = [
            "ai", "artificial intelligence", "cyber", "security", "malware", "infected",
            "npm", "software", "cloud", "aws", "google cloud", "coding", "code",
            "developers", "devs", "database", "postgresql", "vpn", "privacy",
            "age-check", "agent", "linux", "bug hunters", "automation", "layoffs",
            "costs", "bills", "jobs", "workers", "bank", "business", "sap",
            "ransomware"
        ]

        def include_article_in_news_sitemap(article):
            title = str(article.get("title") or "").strip()
            category = str(article.get("category") or "").strip()
            scope = str(article.get("scope") or "").strip().lower()
            source = str(article.get("source") or "").strip().lower()

            if not title:
                return False
            if category not in strategic_news_categories:
                return False

            title_lower = title.lower()
            combined = f"{title_lower} {source}"

            if any(re.search(pattern, title_lower) for pattern in news_sitemap_excluded_title_patterns):
                return False

            if category == "Local News":
                return scope == "cheshire" or any(term in combined for term in cheshire_terms)

            if category in {"Finance", "Tax", "Property"}:
                return True

            if category == "Business":
                if scope == "cheshire" or any(term in combined for term in cheshire_terms):
                    return True
                return any(term in combined for term in business_impact_terms)

            if category in {"Tech", "AI", "AI & Tech"}:
                return any(term in combined for term in practical_tech_terms)

            return False

        # Build Google News sitemap XML
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        xml_content += '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n'
        
        for article in articles:
            if not include_article_in_news_sitemap(article):
                continue
            article_id = str(article.get('_id') or article.get('id') or '')
            raw_title = str(article.get("title","News Article"))
            title = saxutils.escape(raw_title[:100])
            slug = re.sub(r"[^a-z0-9]+","-", raw_title.lower()).strip("-")
            slug = (slug[:80] if slug else "article")
            
            # Parse published date
            pub_date = article.get('publishedDate') or article.get('created_at') or ''
            if isinstance(pub_date, str):
                try:
                    pub_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                except:
                    pub_date = datetime.utcnow()
            
            xml_content += '  <url>\n'
            xml_content += f'    <loc>{base_url}/article/{article_id}/{slug}</loc>\n'
            xml_content += '    <news:news>\n'
            xml_content += '      <news:publication>\n'
            xml_content += '        <news:name>Cheshire Today</news:name>\n'
            xml_content += '        <news:language>en</news:language>\n'
            xml_content += '      </news:publication>\n'
            xml_content += f'      <news:publication_date>{pub_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")}</news:publication_date>\n'
            xml_content += f'      <news:title>{title}</news:title>\n'
            xml_content += '    </news:news>\n'
            xml_content += '  </url>\n'
        
        xml_content += '</urlset>'
        
        return Response(
            content=xml_content, 
            media_type="application/xml",
            headers={"Cache-Control": "public, max-age=3600"}  # Cache for 1 hour
        )
        
    except Exception as e:
        logger.error(f"Error generating news sitemap: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/rss.xml")
@app.get("/api/rss.xml")
async def api_rss_xml_alias():
    return RedirectResponse(url="/rss.xml", status_code=301)


@app.get("/article-index")
@app.get("/latest-articles")
async def latest_articles_html():
    """Plain HTML latest-articles index for search engines and non-JS crawlers."""
    from fastapi.responses import HTMLResponse
    import html as _html

    base_url = "https://cheshiretoday.co.uk"
    allowed_categories = ["Local News", "Business", "Finance", "Tech", "AI", "AI & Tech", "Tax", "Property"]

    articles = await db.articles.find(
        {
            "archived": {"$ne": True},
            "manual_review_hidden_from_public": {"$ne": True},
            "category": {"$in": allowed_categories},
            "image": {"$exists": True, "$ne": ""},
            "title": {"$exists": True, "$ne": ""},
        },
        {
            "_id": 1,
            "id": 1,
            "title": 1,
            "category": 1,
            "summary": 1,
            "content": 1,
            "publishedDate": 1,
        }
    ).sort("publishedDate", -1).limit(120).to_list(120)

    grouped = {}
    for article in articles:
        category = str(article.get("category") or "News").strip()
        grouped.setdefault(category, []).append(article)

    def article_url(article):
        article_id = str(article.get("_id") or article.get("id") or "").strip()
        title = str(article.get("title") or "article")
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        slug = slug[:80] if slug else "article"
        return f"{base_url}/article/{article_id}/{slug}"

    sections = []
    for category in allowed_categories:
        items = grouped.get(category, [])
        if not items:
            continue

        links = []
        for article in items:
            title = _html.escape(str(article.get("title") or "Untitled article"))
            url = _html.escape(article_url(article))
            desc_source = str(article.get("summary") or article.get("content") or "")
            desc = _html.escape(re.sub(r"\s+", " ", desc_source).strip()[:160])
            links.append(f'<li><a href="{url}">{title}</a><p>{desc}</p></li>')

        sections.append(f"<section><h2>{_html.escape(category)}</h2><ul>{''.join(links)}</ul></section>")

    html_content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Latest articles | Cheshire Today</title>
  <meta name="description" content="Latest public articles from Cheshire Today across local news, business, finance and technology.">
  <meta name="robots" content="index,follow">
  <link rel="canonical" href="{base_url}/article-index">
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
  <header>
    <h1>Latest articles</h1>
    <p>Latest public articles from Cheshire Today.</p>
    <p><a href="{base_url}/">Back to Cheshire Today</a></p>
  </header>
  <main>
    {''.join(sections)}
  </main>
</body>
</html>"""

    return HTMLResponse(content=html_content, headers={"Cache-Control": "public, max-age=1800"})

@app.get("/rss.xml")
async def generate_rss_feed():
    """Generate RSS feed for news readers and Google News"""
    from fastapi.responses import Response
    import xml.sax.saxutils as saxutils
    
    try:
        # ALWAYS use production domain for RSS feed - this is for Google News and feed readers
        base_url = 'https://cheshiretoday.co.uk'
        
        # Get latest strategic public articles only.
        # RSS must match Cheshire Today public positioning and avoid exposing weak/off-strategy DB items.
        rss_query = {
            "$or": [{"archived": {"$exists": False}}, {"archived": False}],
            "manual_review_hidden_from_public": {"$ne": True},
            "category": {"$in": ["Local News", "Business", "Finance", "Tech", "AI", "AI & Tech", "Tax", "Property"]}
        }
        articles = await db.articles.find(
            rss_query,
            {"_id": 0, "id": 1, "title": 1, "content": 1, "publishedDate": 1, "category": 1, "author": 1, "image": 1}
        ).sort("publishedDate", -1).limit(50).to_list(50)
        
        # Build RSS XML
        rss = '<?xml version="1.0" encoding="UTF-8"?>\n'
        rss += '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">\n'
        rss += '<channel>\n'
        rss += '  <title>Cheshire Today - Local News</title>\n'
        rss += f'  <link>{base_url}</link>\n'
        rss += '  <description>Latest news from Cheshire and the UK</description>\n'
        rss += '  <language>en-gb</language>\n'
        rss += f'  <lastBuildDate>{datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")}</lastBuildDate>\n'
        rss += f'  <atom:link href="{base_url}/api/rss.xml" rel="self" type="application/rss+xml"/>\n'
        rss += '  <image>\n'
        rss += f'    <url>{base_url}/logo.png</url>\n'
        rss += '    <title>Cheshire Today</title>\n'
        rss += f'    <link>{base_url}</link>\n'
        rss += '  </image>\n'
        
        for article in articles:
            article_id = str(article.get('id', article.get('_id', '')))
            raw_title = article.get('title', 'Untitled')
            slug = re.sub(r"[^a-z0-9]+", "-", str(raw_title or "").lower()).strip("-")
            slug = slug[:80] if slug else "article"
            article_url = f"{base_url}/article/{article_id}/{slug}"
            title = saxutils.escape(raw_title)
            description = saxutils.escape(article.get('content', '')[:300] + '...')
            pub_date = article.get('publishedDate', datetime.utcnow().isoformat())
            category = saxutils.escape(article.get('category', 'News'))
            author = saxutils.escape(article.get('author', 'Cheshire Today'))
            image = article.get('image', '')
            
            # Parse date
            try:
                if isinstance(pub_date, str):
                    dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                else:
                    dt = pub_date
                formatted_date = dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
            except:
                formatted_date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
            
            rss += '  <item>\n'
            rss += f'    <title>{title}</title>\n'
            rss += f'    <link>{saxutils.escape(article_url)}</link>\n'
            rss += f'    <guid isPermaLink="true">{saxutils.escape(article_url)}</guid>\n'
            rss += f'    <description>{description}</description>\n'
            rss += f'    <pubDate>{formatted_date}</pubDate>\n'
            rss += f'    <category>{category}</category>\n'
            rss += f'    <author>{author}</author>\n'
            if image and not image.startswith('data:'):
                rss += f'    <media:content url="{saxutils.escape(image)}" medium="image"/>\n'
            rss += '  </item>\n'
        
        rss += '</channel>\n'
        rss += '</rss>'
        
        return Response(content=rss, media_type="application/rss+xml")
        
    except Exception as e:
        logger.error(f"Error generating RSS feed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/trending-headlines")
async def get_trending_headlines():
    """Get breaking news headlines from recent articles in the database.
    
    IMPORTANT: We use ACTUAL articles from the database (not AI-generated headlines)
    so that clicking a headline always opens the correct matching article.
    """
    try:
        # Get the most recent articles from the database - these ARE the breaking news
        # Mix of Cheshire and UK articles for variety
        recent_articles = await db.articles.find(
            {},
            {"_id": 1, "title": 1, "category": 1, "scope": 1, "publishedDate": 1}
        ).sort("publishedDate", -1).limit(10).to_list(10)
        
        headlines = []
        for article in recent_articles:
            headlines.append({
                "headline": article.get("title", ""),
                "category": article.get("category", "News"),
                "scope": article.get("scope", "cheshire"),
                "articleId": str(article.get("_id", ""))  # Include article ID for direct linking
            })
        
        logger.info(f"Returning {len(headlines)} headlines from database articles")
        return {"headlines": headlines, "updated_at": datetime.utcnow().isoformat()}
        
    except Exception as e:
        logger.error(f"Error fetching trending headlines: {str(e)}")
        return {"headlines": [], "error": str(e)}

@api_router.get("/trending-topics")
async def get_trending_topics(limit: int = 10):
    """
    Get trending topics based on keyword frequency in recent articles.
    Analyzes the most common meaningful words in recent article titles.
    """
    try:
        # Get recent articles (last 100)
        recent_articles = await db.articles.find(
            {},
            {"_id": 0, "title": 1, "category": 1}
        ).sort("publishedDate", -1).limit(100).to_list(100)
        
        if not recent_articles:
            return {"topics": [], "message": "No articles found"}
        
        # Common stop words to exclude
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'this',
            'that', 'these', 'those', 'it', 'its', 'as', 'after', 'before',
            'into', 'through', 'during', 'under', 'again', 'further', 'then',
            'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
            'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'not',
            'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'over',
            'up', 'down', 'out', 'about', 'what', 'which', 'who', 'whom',
            'says', 'said', 'new', 'news', 'cheshire', 'uk', 'today', 'now',
            'latest', 'breaking', 'live', 'update', 'updates', 'read', 'full',
            'story', 'bbc', 'sky', 'guardian', 'amid', 'following', 'after',
            'reveals', 'revealed', 'announces', 'announced', 'set', 'gets'
        }
        
        # Count word frequency
        word_counts = {}
        category_associations = {}
        
        for article in recent_articles:
            title = article.get('title', '').lower()
            category = article.get('category', 'News')
            
            # Extract words (2+ characters, alphanumeric)
            words = re.findall(r'\b[a-z]{3,}\b', title)
            
            for word in words:
                if word not in stop_words:
                    word_counts[word] = word_counts.get(word, 0) + 1
                    if word not in category_associations:
                        category_associations[word] = {}
                    category_associations[word][category] = category_associations[word].get(category, 0) + 1
        
        # Sort by frequency and get top topics
        sorted_topics = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        # Build response with category associations
        topics = []
        for word, count in sorted_topics:
            # Get most associated category
            categories = category_associations.get(word, {})
            top_category = max(categories.items(), key=lambda x: x[1])[0] if categories else 'News'
            
            topics.append({
                "topic": word.capitalize(),
                "count": count,
                "category": top_category,
                "trending": count >= 3  # Mark as "hot" if mentioned 3+ times
            })
        
        return {
            "topics": topics,
            "total_articles_analyzed": len(recent_articles),
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching trending topics: {str(e)}")
        return {"topics": [], "error": str(e)}

@api_router.get("/related-articles/{article_id}")
async def get_related_articles(article_id: str, limit: int = 4):
    """Get related articles based on category and tags"""
    try:
        # Find the source article
        article = None
        try:
            article = await db.articles.find_one({"_id": ObjectId(article_id)}, {"_id": 0})
        except:
            pass
        if not article:
            article = await db.articles.find_one({"id": article_id}, {"_id": 0})
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        category = article.get('category', '')
        tags = article.get('tags', [])
        
        visibility_filter = {
            "$or": [{"archived": {"$exists": False}}, {"archived": False}],
            "manual_review_hidden_from_public": {"$ne": True},
        }

        def normalise_related(items):
            normalised = []
            seen = set()
            for item in items:
                public_id = str(item.get("_id") or item.get("id") or "").strip()
                if not public_id or public_id == str(article_id):
                    continue
                if public_id in seen:
                    continue
                seen.add(public_id)
                item["id"] = public_id
                item.pop("_id", None)
                normalised.append(item)
            return normalised

        # Find related articles by category, excluding current article
        query = {
            **visibility_filter,
            "category": category,
            "$and": [{"id": {"$ne": article_id}}],
        }
        
        related = await db.articles.find(
            query,
            {"_id": 1, "id": 1, "title": 1, "image": 1, "category": 1, "publishedDate": 1}
        ).sort("publishedDate", -1).limit(limit * 2).to_list(limit * 2)
        related = normalise_related(related)[:limit]
        
        # If not enough related articles, get more from other categories
        if len(related) < limit:
            more = await db.articles.find(
                {
                    **visibility_filter,
                    "id": {"$ne": article_id},
                    "category": {"$ne": category},
                },
                {"_id": 1, "id": 1, "title": 1, "image": 1, "category": 1, "publishedDate": 1}
            ).sort("publishedDate", -1).limit((limit - len(related)) * 2).to_list((limit - len(related)) * 2)
            related.extend(normalise_related(more)[:limit - len(related)])
        
        return related
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting related articles: {str(e)}")
        return []

async def serve_article_html(article_id: str, request=None):
    """
    HTML endpoint used by social crawlers.
    Must accept BOTH:
      - Mongo _id (24-hex) e.g. 69a6cd63d803ba80e6108213
      - Our public UUID field in article["id"]
    """
    from fastapi.responses import HTMLResponse
    import urllib.parse
    import html as _html

    # Use the shared lookup helper so crawler/social HTML can serve both
    # active articles and archived/duplicate-preserved articles.
    article = await _find_article_by_any_id(article_id)

    # If still missing, return 404 (never 500)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    title = str(article.get("title") or "Cheshire Today")
    summary = str(article.get("summary") or "").strip()
    content = str(article.get("content") or "").strip()
    desc_src = summary if len(summary) >= 40 else content
    desc = re.sub(r"\s+", " ", desc_src).strip()[:180]

    def normalize_social_image(raw_img, source_url=None) -> str:
        img = str(raw_img).strip() if raw_img else ""
        if not img:
            return "https://cheshiretoday.co.uk/social-share.jpg"

        # Contentful: request a genuine Facebook-sized social image.
        # The source asset may be smaller, while the Contentful Images API
        # can safely produce a valid 1200x630 JPEG using fill mode.
        if "images.ctfassets.net" in img:
            img = img.split("?", 1)[0]
            img += "?fm=jpg&w=1200&h=630&fit=fill&q=85"

        # Reach / Cheshire Live
        if "/ALTERNATES/s615/" in img:
            img = img.replace("/ALTERNATES/s615/", "/ALTERNATES/s1200/")
        if "/ALTERNATES/s615b/" in img:
            img = img.replace("/ALTERNATES/s615b/", "/ALTERNATES/s1200/")
        if "/ALTERNATES/s810/" in img:
            img = img.replace("/ALTERNATES/s810/", "/ALTERNATES/s1200/")

        # Newsquest sites such as Chester Standard expose a dedicated
        # 1200x630 social image on the source page. Prefer that declared
        # og:image over the smaller generic resources/images URL.
        newsquest_hosts = (
            "chesterstandard.co.uk",
            "warringtonguardian.co.uk",
            "knutsfordguardian.co.uk",
            "northwichguardian.co.uk",
            "wilmslowguardian.co.uk",
            "crewechronicle.co.uk",
        )
        if (
            "/resources/images/" in img
            and source_url
            and any(host in str(source_url).lower() for host in newsquest_hosts)
        ):
            try:
                import urllib.request

                req = urllib.request.Request(
                    str(source_url),
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                source_html = (
                    urllib.request.urlopen(req, timeout=8)
                    .read()
                    .decode("utf-8", errors="ignore")
                )
                match = re.search(
                    r"<meta[^>]+property=[\"\x27]og:image[\"\x27]"
                    r"[^>]+content=[\"\x27]([^\"\x27]+)[\"\x27]",
                    source_html,
                    re.I,
                )
                if match:
                    candidate = (
                        match.group(1)
                        .replace("&amp;", "&")
                        .strip()
                    )
                    if candidate.startswith(("https://", "http://")):
                        return candidate
            except Exception:
                pass

        # Guardian image URLs are signed. For small stored thumbnails, inspect
        # the source page for a larger clean signed image from normal image
        # markup, while rejecting the branded page-level Open Graph image.
        if "i.guim.co.uk" in img and "s=" in img:
            is_small_guardian_image = (
                "width=140" in img or "width=240" in img
            )
            is_guardian_source = (
                source_url
                and "theguardian.com" in str(source_url).lower()
            )

            if is_small_guardian_image and is_guardian_source:
                try:
                    import html as _source_html
                    import urllib.request

                    req = urllib.request.Request(
                        str(source_url),
                        headers={"User-Agent": "Mozilla/5.0"},
                    )
                    source_html = (
                        urllib.request.urlopen(req, timeout=8)
                        .read()
                        .decode("utf-8", errors="ignore")
                    )
                    source_html = _source_html.unescape(source_html)

                    candidates = re.findall(
                        r"https://i\.guim\.co\.uk/img/media/"
                        r"[^\"'<>\s]+",
                        source_html,
                        re.I,
                    )

                    clean_candidates = []
                    for candidate in candidates:
                        candidate = candidate.strip()
                        if "overlay-base64" in candidate:
                            continue

                        width_match = re.search(
                            r"(?:[?&])width=(\d+)",
                            candidate,
                            re.I,
                        )
                        if not width_match:
                            continue

                        width = int(width_match.group(1))
                        if width < 620:
                            continue

                        clean_candidates.append((width, candidate))

                    preferred = next(
                        (
                            candidate
                            for width, candidate in clean_candidates
                            if width == 1200
                        ),
                        None,
                    )
                    if preferred:
                        return preferred

                    if clean_candidates:
                        clean_candidates.sort(
                            key=lambda item: (
                                abs(item[0] - 1200),
                                item[0],
                            )
                        )
                        return clean_candidates[0][1]
                except Exception:
                    pass

            return img

        if "i.guim.co.uk" in img and "width=140" in img:
            img = img.replace("width=140", "width=1200")
        if "i.guim.co.uk" in img and "width=240" in img:
            img = img.replace("width=240", "width=1200")

        # BBC
        if "ichef.bbci.co.uk" in img and "/240/" in img:
            img = img.replace("/240/", "/1024/")
        if "ichef.bbci.co.uk" in img and "/320/" in img:
            img = img.replace("/320/", "/1024/")
        if "ichef.bbci.co.uk" in img and "/480/" in img:
            img = img.replace("/480/", "/1024/")

        return img

    img = normalize_social_image(article.get("image"), article.get("source_url"))

    # Canonical/OG should point at the one public Mongo-ID article identity.
    canonical = _canonical_article_url(article)

    # Escape to avoid breaking HTML
    import json as _json

    esc_title = _html.escape(title)
    esc_desc = _html.escape(desc)
    esc_img = _html.escape(img)
    esc_canon = _html.escape(canonical)

    author = str(article.get("author") or "Cheshire Today").strip() or "Cheshire Today"
    section = str(article.get("category") or "News").strip() or "News"

    def _seo_datetime(value) -> str:
        raw = str(value or "").strip()
        if not raw:
            return ""
        # Convert common DB/date string formats to ISO-style datetime for structured data.
        if "T" not in raw and re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?", raw):
            raw = raw.replace(" ", "T", 1)
        if raw.endswith("Z"):
            return raw
        if re.search(r"[+-]\d{2}:?\d{2}$", raw):
            return raw
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?", raw):
            return raw + "+00:00"
        return raw

    published = _seo_datetime(article.get("publishedDate") or article.get("published_at") or article.get("created_at"))
    modified = _seo_datetime(article.get("updated_at") or article.get("modified_at") or article.get("publishedDate") or article.get("created_at"))

    # Build a crawlable text version of the article body.
    # Keep it plain and safe: remove scripts/styles/tags, normalise whitespace, then paragraphise.
    body_src = content or summary or ""
    body_src = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", body_src)
    body_src = re.sub(r"(?is)<br\s*/?>", "\n", body_src)
    body_src = re.sub(r"(?is)</p\s*>", "\n\n", body_src)
    body_text = re.sub(r"(?is)<[^>]+>", " ", body_src)
    body_text = _html.unescape(body_text)
    body_text = re.sub(r"\r", "\n", body_text)
    body_text = re.sub(r"[ \t]+", " ", body_text)
    body_text = re.sub(r"\n{3,}", "\n\n", body_text).strip()

    if not body_text:
        body_text = desc

    paragraphs = [x.strip() for x in re.split(r"\n\s*\n", body_text) if x.strip()]
    if len(paragraphs) == 1 and len(paragraphs[0]) > 700:
        sentences = re.split(r"(?<=[.!?])\s+", paragraphs[0])
        chunks = []
        buf = []
        for sentence in sentences:
            buf.append(sentence)
            if len(" ".join(buf)) >= 450:
                chunks.append(" ".join(buf).strip())
                buf = []
        if buf:
            chunks.append(" ".join(buf).strip())
        paragraphs = chunks or paragraphs

    article_body_html = "\n".join(f"  <p>{_html.escape(x)}</p>" for x in paragraphs[:80])
    esc_author = _html.escape(author)
    esc_section = _html.escape(section)
    esc_published = _html.escape(published)
    esc_modified = _html.escape(modified or published)

    robots_directive = "index, follow, max-image-preview:large"
    # Archived/manual-review-hidden articles are kept reachable for old links.
    # Manually force-live articles are intentional public picks and can remain indexable.
    is_manual_review_hidden = article.get("manual_review_hidden_from_public") is True
    is_archived_without_force_live = article.get("archived") is True and article.get("force_live") is not True
    if is_manual_review_hidden or is_archived_without_force_live:
        robots_directive = "noindex, follow, max-image-preview:large"

    schema = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": canonical,
        },
        "headline": title,
        "description": desc,
        "image": [img],
        "datePublished": published or None,
        "dateModified": modified or published or None,
        "author": {
            "@type": "Organization" if author == "Cheshire Today" else "Person",
            "name": author,
        },
        "publisher": {
            "@type": "NewsMediaOrganization",
            "name": "Cheshire Today",
            "logo": {
                "@type": "ImageObject",
                "url": "https://cheshiretoday.co.uk/logo.png",
            },
        },
        "articleSection": section,
        "articleBody": body_text[:20000],
    }
    schema = {k: v for k, v in schema.items() if v is not None}
    schema_json = _json.dumps(schema, ensure_ascii=False)
    schema_json = schema_json.replace("</", "<\\/")

    html_content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc_title}</title>
  <link rel="canonical" href="{esc_canon}">
  <meta name="description" content="{esc_desc}">
  <meta name="robots" content="{robots_directive}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Cheshire Today">
  <meta property="og:locale" content="en_GB">
  <meta property="fb:app_id" content="1265742728765482">
  <meta property="og:url" content="{esc_canon}">
  <meta property="og:title" content="{esc_title}">
  <meta property="og:description" content="{esc_desc}">
  <meta property="og:image" content="{esc_img}">
  <meta property="og:image:secure_url" content="{esc_img}">
  <meta property="article:published_time" content="{esc_published}">
  <meta property="article:modified_time" content="{esc_modified}">
  <meta property="article:section" content="{esc_section}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc_title}">
  <meta name="twitter:description" content="{esc_desc}">
  <meta name="twitter:image" content="{esc_img}">
  <script type="application/ld+json">{schema_json}</script>
</head>
<body>
  <article>
    <header>
      <h1>{esc_title}</h1>
      <p>{esc_desc}</p>
      <p><strong>By {esc_author}</strong></p>
      <time datetime="{esc_published}">{esc_published}</time>
    </header>
{article_body_html}
    <p><a href="{esc_canon}">Open article on Cheshire Today</a></p>
  </article>
</body>
</html>"""

    # Cache modestly to reduce scraper flapping
    return HTMLResponse(content=html_content, headers={"Cache-Control": "public, max-age=3600"})

async def _find_article_by_any_id(article_id: str):
    """Return an article from active/archive collections by public id or Mongo _id."""
    if not article_id:
        return None

    article = None
    try:
        article = await db.articles.find_one({"id": article_id})
    except Exception:
        article = None

    if not article:
        try:
            article = await db.articles.find_one({"_id": ObjectId(article_id)})
        except Exception:
            article = None

    if not article:
        try:
            article = await db.archived_articles.find_one({"id": article_id})
        except Exception:
            article = None

    if not article:
        try:
            article = await db.archived_articles.find_one({"_id": ObjectId(article_id)})
        except Exception:
            article = None

    return article


def _article_slug_from_title(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(title or "").lower()).strip("-")
    return slug[:80] if slug else "article"


def _is_uuid_article_id(article_id: str) -> bool:
    value = str(article_id or "").strip()
    try:
        return str(uuid.UUID(value)) == value.lower()
    except (ValueError, AttributeError, TypeError):
        return False


def _canonical_article_url(article: dict) -> str:
    """Build the canonical Mongo-ID article URL for a resolved article."""
    import urllib.parse

    mongo_id = str(article.get("_id") or "").strip()
    if not re.fullmatch(r"[0-9a-fA-F]{24}", mongo_id):
        raise HTTPException(status_code=404, detail="Article not found")
    slug = _article_slug_from_title(article.get("title") or "article")
    return (
        "https://cheshiretoday.co.uk/article/"
        f"{urllib.parse.quote(mongo_id)}/{urllib.parse.quote(slug)}"
    )


LEGACY_ARTICLE_REDIRECTS = {
    "69e85a2b5c3fd0f57cf3a438": ("69e9031c87e34f348b321972", "the-cheshire-village-fighting-to-have-its-own-council"),
    "69df1fb5311960544b7adc0a": ("69e071242549c00aa1d4a4f6", "cheshire-asylum-hotel-shuts-with-immediate-effect"),
    "6a0166ee3ab76ea50644bc29": ("8abea102-5d81-4f55-b746-99f25fa46bb5", "cheshire-town-confirms-food-and-drink-festival-return-and-it-s-free"),
    "6a0aa09c406651729119b2bf": ("6a0af519406651729119b2de", "why-does-amazon-have-no-western-rivals"),
    "6a09f7ce9dfc21e2577620c0": ("6a0aa0bf406651729119b2c2", "vicious-circle-of-rising-costs-is-fuelling-crisis-for-traders"),
}


def _manual_legacy_article_redirect(article_id: str):
    target = LEGACY_ARTICLE_REDIRECTS.get(str(article_id or "").strip())
    if not target:
        return None
    target_id, target_slug = target
    return RedirectResponse(url=f"https://cheshiretoday.co.uk/article/{target_id}/{target_slug}", status_code=301)


async def _redirect_facebook_logged_article_if_needed(article_id: str):
    """Recover short Facebook links whose old Mongo _id no longer exists.

    Facebook posts historically used /article/{mongo_id}. If the same story is later
    reimported under a new Mongo _id, use facebook_post_log.title to find the
    current article and redirect to its canonical URL.
    """
    clean_id = str(article_id or "").strip()
    if not clean_id:
        return None

    existing = await _find_article_by_any_id(clean_id)
    if existing:
        return None

    log = None
    try:
        log = await db.facebook_post_log.find_one({"article_id": clean_id})
    except Exception:
        log = None

    title = str((log or {}).get("title") or "").strip()
    if not title or len(title) < 12:
        return None

    words = [w for w in re.split(r"[^a-z0-9]+", title.lower()) if len(w) > 2]
    if len(words) < 4:
        return None

    title_regex = r"^\s*" + r"[^a-z0-9]+".join(re.escape(w) for w in words[:12]) + r".*$"

    article = None
    try:
        article = await db.articles.find_one({"title": {"$regex": title_regex, "$options": "i"}})
    except Exception:
        article = None

    if not article:
        try:
            article = await db.archived_articles.find_one({"title": {"$regex": title_regex, "$options": "i"}})
        except Exception:
            article = None

    if not article:
        return None

    target_id = str(article.get("_id") or article.get("id") or "").strip()
    if not target_id:
        return None

    target_slug = _article_slug_from_title(article.get("title") or title)
    return RedirectResponse(url=f"https://cheshiretoday.co.uk/article/{target_id}/{target_slug}", status_code=301)


async def _redirect_stale_article_slug_if_needed(article_id: str, slug: str):
    """Recover old Facebook/article links where the old ID is gone but the slug still matches a live article."""
    existing = await _find_article_by_any_id(article_id)
    if existing:
        return None

    clean_slug = str(slug or "").strip().lower()
    if not clean_slug or clean_slug == "article" or len(clean_slug) < 12:
        return None

    words = [w for w in re.split(r"[^a-z0-9]+", clean_slug) if w]
    if len(words) < 4:
        return None

    title_regex = r"^\s*" + r"[^a-z0-9]+".join(re.escape(w) for w in words) + r"(?:[^a-z0-9]+)?\s*$"
    article = None

    try:
        article = await db.articles.find_one({"title": {"$regex": title_regex, "$options": "i"}})
    except Exception:
        article = None

    if not article:
        try:
            article = await db.archived_articles.find_one({"title": {"$regex": title_regex, "$options": "i"}})
        except Exception:
            article = None

    if not article:
        return None

    target_id = str(article.get("_id") or article.get("id") or "").strip()
    if not target_id:
        return None

    target_slug = _article_slug_from_title(article.get("title") or clean_slug)
    return RedirectResponse(url=f"https://cheshiretoday.co.uk/article/{target_id}/{target_slug}", status_code=301)



async def serve_guide_html(slug: str, request=None):
    """Crawler/static HTML for authority guide pages in /guides/{slug}."""
    from fastapi.responses import HTMLResponse
    import html as _html
    import json as _json
    import urllib.parse

    clean_slug = str(slug or "").strip()
    if not clean_slug:
        raise HTTPException(status_code=404, detail="Guide not found")

    doc = await db.authority_pages.find_one({
        "slug": clean_slug,
        "status": {"$in": ["published", "live"]},
    })

    if not doc:
        raise HTTPException(status_code=404, detail="Guide not found")

    guide = _ap_serialize(doc)

    title = str(guide.get("title") or clean_slug.replace("-", " ").title()).strip()
    category = str(guide.get("category") or "Guides").strip()
    updated = str(guide.get("updatedAt") or guide.get("updated_at") or "").strip()
    sections = guide.get("sections") if isinstance(guide.get("sections"), list) else []

    canonical = f"https://cheshiretoday.co.uk/guides/{urllib.parse.quote(clean_slug)}"

    # Build readable guide sections from existing authority_pages data.
    body_parts = []
    plain_parts = []
    useful_content_len = 0

    for section in sections:
        if not isinstance(section, dict):
            continue

        section_type = str(section.get("type") or "").strip().lower()
        heading = str(section.get("title") or section.get("name") or "").strip()
        content = str(section.get("content") or "").strip()
        rating = section.get("rating")
        affiliate_link = str(section.get("affiliate_link") or "").strip()

        if heading:
            body_parts.append(f"<h2>{_html.escape(heading)}</h2>")
            plain_parts.append(heading)

        if rating not in (None, ""):
            body_parts.append(f"<p><strong>Rating:</strong> {_html.escape(str(rating))}</p>")
            plain_parts.append(f"Rating: {rating}")

        if content:
            useful_content_len += len(content)
            safe_content = _html.escape(content)
            # Keep paragraphs readable without trusting stored HTML.
            paragraphs = [x.strip() for x in re.split(r"\n\s*\n", safe_content) if x.strip()]
            if not paragraphs:
                paragraphs = [safe_content]
            for para in paragraphs[:12]:
                body_parts.append(f"<p>{para}</p>")
            plain_parts.append(content)

        if affiliate_link:
            safe_link = _html.escape(affiliate_link)
            link_label = _html.escape(heading or "Visit provider")
            body_parts.append(
                f'<p><a href="{safe_link}" rel="nofollow sponsored noopener" target="_blank">{link_label}</a></p>'
            )

        # Avoid very thin empty tool rows looking completely blank.
        if section_type == "tool" and heading and not content:
            body_parts.append("<p>Listed as one of the options covered in this guide.</p>")
            plain_parts.append("Listed as one of the options covered in this guide.")

    body_text = re.sub(r"\s+", " ", " ".join(plain_parts)).strip()
    desc_source = body_text or title
    desc = desc_source[:180]

    if not body_parts:
        body_parts.append(f"<p>{_html.escape(desc)}</p>")

    esc_title = _html.escape(title)
    esc_desc = _html.escape(desc)
    esc_category = _html.escape(category)
    esc_canonical = _html.escape(canonical)
    esc_updated = _html.escape(updated)

    robots_directive = "index, follow, max-image-preview:large"
    if useful_content_len < 700:
        robots_directive = "noindex, follow, max-image-preview:large"

    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": desc,
        "url": canonical,
        "dateModified": updated or None,
        "publisher": {
            "@type": "Organization",
            "name": "Cheshire Today",
            "logo": {
                "@type": "ImageObject",
                "url": "https://cheshiretoday.co.uk/logo.png",
            },
        },
        "about": category,
    }
    schema = {k: v for k, v in schema.items() if v is not None}
    schema_json = _json.dumps(schema, ensure_ascii=False).replace("</", "<\\/")

    html_content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc_title}</title>
  <link rel="canonical" href="{esc_canonical}">
  <meta name="description" content="{esc_desc}">
  <meta name="robots" content="{robots_directive}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Cheshire Today">
  <meta property="og:locale" content="en_GB">
  <meta property="og:url" content="{esc_canonical}">
  <meta property="og:title" content="{esc_title}">
  <meta property="og:description" content="{esc_desc}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{esc_title}">
  <meta name="twitter:description" content="{esc_desc}">
  <script type="application/ld+json">{schema_json}</script>
</head>
<body>
  <article>
    <header>
      <p><a href="https://cheshiretoday.co.uk/">Cheshire Today</a> / {esc_category}</p>
      <h1>{esc_title}</h1>
      <p>{esc_desc}</p>
      <p><strong>Category:</strong> {esc_category}</p>
      <time datetime="{esc_updated}">{esc_updated}</time>
    </header>
    {''.join(body_parts)}
    <p><a href="{esc_canonical}">Open this guide on Cheshire Today</a></p>
  </article>
</body>
</html>"""

    return HTMLResponse(content=html_content, headers={"Cache-Control": "public, max-age=3600"})


@app.get("/guides/{slug}")
async def serve_guide_for_production(slug: str, request: Request):
    """Public guide URL serves crawler HTML for bots/social previews and SPA for browsers."""
    user_agent = request.headers.get("user-agent", "").lower()
    is_crawler = any(bot in user_agent for bot in [
        "facebookexternalhit",
        "twitterbot",
        "linkedinbot",
        "whatsapp",
        "telegrambot",
        "slackbot",
        "discordbot",
        "googlebot",
        "bingbot",
        "crawler",
        "bot",
    ])

    if is_crawler:
        return await serve_guide_html(slug, request)

    return _spa_index_or_500()


@api_router.get("/guides/{slug}")
async def serve_guide_for_api_route(slug: str):
    """Guide HTML variant for API/crawler access."""
    return await serve_guide_html(slug)


@app.get("/article/{article_id}/{slug}")
async def serve_article_for_production_slug(article_id: str, slug: str, request: Request):
    """Public slug URL serves crawler HTML for bots/social previews and SPA for browsers."""
    user_agent = request.headers.get("user-agent", "").lower()
    is_crawler = any(bot in user_agent for bot in [
        "facebookexternalhit",
        "twitterbot",
        "linkedinbot",
        "whatsapp",
        "telegrambot",
        "slackbot",
        "discordbot",
        "googlebot",
        "bingbot",
        "crawler",
        "bot",
    ])

    manual_redirect = _manual_legacy_article_redirect(article_id)
    if manual_redirect:
        return manual_redirect

    article = await _find_article_by_any_id(article_id)
    if article:
        canonical_url = _canonical_article_url(article)
        canonical_id = canonical_url.split("/article/", 1)[1].split("/", 1)[0]
        canonical_slug = _article_slug_from_title(article.get("title") or "article")
        if article_id != canonical_id or slug != canonical_slug:
            return RedirectResponse(url=canonical_url, status_code=301)

    # A syntactically valid but unknown internal UUID is not an old slug.
    # Keep the not-found contract instead of title-matching it to another story.
    if _is_uuid_article_id(article_id):
        raise HTTPException(status_code=404, detail="Article not found")

    stale_redirect = await _redirect_stale_article_slug_if_needed(article_id, slug)
    if stale_redirect:
        return stale_redirect

    if is_crawler:
        return await serve_article_html(article_id, request)

    return _spa_index_or_500()

@api_router.get("/article/{article_id}/{slug}")
async def serve_article_for_api_slug(article_id: str, slug: str):
    """Slug URL variant (API router)"""
    return await serve_article_html(article_id)


@app.head("/article/{article_id}")
async def serve_article_for_production_head(article_id: str):
    """HEAD: 301 /article/{id} -> canonical slug URL."""
    return await serve_article_for_production(article_id)

@app.get("/article/{article_id}")
async def serve_article_for_production(article_id: str):
    """301 /article/{id} -> the canonical Mongo-ID slug URL."""
    manual_redirect = _manual_legacy_article_redirect(article_id)
    if manual_redirect:
        return manual_redirect

    from fastapi.responses import RedirectResponse

    article = await _find_article_by_any_id(article_id)

    if not article:
        # Backward compatibility for historical Facebook links that used
        # /article/{slug} without an article ID. Reuse the existing safe
        # title/slug recovery helper and redirect to the canonical ID URL.
        slug_only_redirect = await _redirect_stale_article_slug_if_needed(article_id, article_id)
        if slug_only_redirect:
            return slug_only_redirect

        facebook_redirect = await _redirect_facebook_logged_article_if_needed(article_id)
        if facebook_redirect:
            return facebook_redirect

        # If missing, keep crawler HTML behaviour (no redirect)
        return await serve_article_html(article_id)

    target = _canonical_article_url(article)
    return RedirectResponse(url=target, status_code=301)
@api_router.get("/article/{article_id}")
async def serve_article_for_api(article_id: str):
    """API endpoint for programmatic access"""
    return await serve_article_html(article_id)


# Helper function for robots.txt content
def get_robots_content():
    base_url = os.environ.get('PUBLIC_URL', 'https://cheshiretoday.co.uk').rstrip('/')
    host_only = re.sub(r'^https?://', '', base_url).rstrip('/')
    return f"""# =============================================
# Cheshire Today - robots.txt
# https://cheshiretoday.co.uk
# Last updated: 2026-01-27
# =============================================

# Default rules for all bots
User-agent: *
Allow: /
Allow: /article/
Allow: /search
Allow: /chester
Allow: /warrington
Allow: /wirral
Allow: /crewe
Allow: /macclesfield
Allow: /category/

# Crawl rate (be polite to server)
Crawl-delay: 1

# Disallow admin and internal API paths
Disallow: /admin
Disallow: /api/admin/
Disallow: /api/send-digest
Disallow: /api/test-email
Disallow: /api/cleanup-subscribers
Disallow: /api/check-subscribers
Disallow: /unsubscribe
Disallow: /newsletter/preferences

# Disallow query parameters that create duplicate content
Disallow: /*?*utm_
Disallow: /*?*fbclid
Disallow: /*?*gclid

# =============================================
# Googlebot specific rules
# =============================================
User-agent: Googlebot
Allow: /
Allow: /article/
Allow: /api/seo/article/
Crawl-delay: 0

User-agent: Googlebot-Image
Allow: /
Allow: /*.jpg$
Allow: /*.jpeg$
Allow: /*.png$
Allow: /*.gif$
Allow: /*.webp$

User-agent: Googlebot-News
Allow: /
Allow: /article/

# =============================================
# Bing specific rules
# =============================================
User-agent: Bingbot
Allow: /
Crawl-delay: 1

# =============================================
# Social media crawlers (for link previews)
# =============================================
User-agent: facebookexternalhit
Allow: /

User-agent: Twitterbot
Allow: /

User-agent: LinkedInBot
Allow: /

User-agent: WhatsApp
Allow: /

# =============================================
# Sitemaps
# =============================================
Sitemap: {base_url}/sitemap.xml
Sitemap: {base_url}/news-sitemap.xml

# Preferred domain
Host: {host_only}
"""

# Helper function for ads.txt content
def get_ads_content():
    # Legacy function - kept for backwards compatibility
    # Now using Ezoic ads.txt manager redirect
    return """google.com, pub-3403912630939928, DIRECT, f08c47fec0942fa0
"""

# Ezoic ads.txt manager URL
EZOIC_ADS_TXT_URL = "https://srv.adstxtmanager.com/82520/cheshiretoday.co.uk"


# Root-level routes (for local development)

@app.head("/robots.txt")
async def robots_txt_head():
    """HEAD support for robots.txt"""
    from fastapi.responses import Response
    return Response(
        content=get_robots_content(),
        media_type="text/plain",
        headers={"Cache-Control": "public, max-age=86400"}
    )

@app.get("/robots.txt")
async def robots_txt():
    """Generate robots.txt for search engines"""
    from fastapi.responses import Response
    return Response(content=get_robots_content(), media_type="text/plain", headers={"Cache-Control": "public, max-age=86400"})


@app.get("/ads.txt")
async def ads_txt():
    """Redirect to Ezoic ads.txt manager for dynamic ad partner management"""
    return RedirectResponse(url=EZOIC_ADS_TXT_URL, status_code=301)


# API router routes (for production - accessible via /api/robots.txt which gets served at root by nginx)

@api_router.head("/robots.txt")
async def api_robots_txt_head():
    """HEAD support for robots.txt (API route)"""
    from fastapi.responses import Response
    return Response(
        content=get_robots_content(),
        media_type="text/plain",
        headers={"Cache-Control": "public, max-age=86400"}
    )

@api_router.get("/robots.txt")
async def api_robots_txt():
    """Generate robots.txt for search engines (API route for production)"""
    from fastapi.responses import Response
    return Response(content=get_robots_content(), media_type="text/plain", headers={"Cache-Control": "public, max-age=86400"})


@api_router.get("/ads.txt")
async def api_ads_txt():
    """Redirect to Ezoic ads.txt manager for dynamic ad partner management (API route for production)"""
    return RedirectResponse(url=EZOIC_ADS_TXT_URL, status_code=301)


@api_router.post("/trigger-daily-generation")
async def trigger_daily_generation(authorized: bool = Depends(get_admin_auth)):
    """Manually trigger daily article generation (admin endpoint)"""
    try:
        await daily_article_generation(count=12)
        return {
            "success": True,
            "message": "Daily article generation triggered successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/fix-cheshire-images")
async def fix_cheshire_images():
    """Update LOCAL NEWS articles with Cheshire-specific images"""
    try:
        # CHESHIRE-SPECIFIC images - countryside, villages, towns
        CHESHIRE_IMAGES = [
            '',  # UK countryside village
            '',  # British countryside
            '',  # English village
            '',  # UK countryside
            '',  # British rural
            '',  # English countryside
            '',  # UK rural scene
            '',  # British landscape
            '',  # Rural UK
            '',  # English countryside
            '',  # Rural buildings
            '',  # British town
            '',  # UK village street
            '',  # Country lane
            '',  # British village
            '',  # Rural scene
            '',  # UK countryside
            '',  # Country house
            '',  # British architecture
            '',  # Countryside road
        ]
        
        # Get all LOCAL NEWS articles
        local_articles = await db.articles.find({"category": "Local News"}).to_list(1000)
        
        updated = 0
        for i, article in enumerate(local_articles):
            # Use modulo to cycle through Cheshire images
            cheshire_image = CHESHIRE_IMAGES[i % len(CHESHIRE_IMAGES)]
            
            await db.articles.update_one(
                {'_id': article['_id']},
                {'$set': {'image': cheshire_image}}
            )
            updated += 1
        
        return {
            "success": True,
            "articles_updated": updated,
            "message": f"Updated {updated} Local News articles with Cheshire-specific images"
        }
        
    except Exception as e:
        logger.error(f"Error updating Cheshire images: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/admin/clean-duplicate-articles")
async def clean_duplicate_articles(authorized: bool = Depends(get_admin_auth)):
    """Remove duplicate articles keeping the newest one (admin utility). Requires admin authentication."""
    try:
        # Get all articles sorted by date (newest first)
        articles = await db.articles.find({}).sort('publishedDate', -1).to_list(1000)
        
        # Track seen title patterns (first 5 words)
        seen_patterns = set()
        to_remove = []
        kept = []
        
        for article in articles:
            title = article.get('title', '')
            words = title.split()[:5]
            pattern = ' '.join(words).lower()
            
            if pattern in seen_patterns:
                to_remove.append({
                    'id': str(article['_id']),
                    'title': title[:60]
                })
            else:
                seen_patterns.add(pattern)
                kept.append(title[:60])
        
        # Remove duplicates
        removed_count = 0
        for item in to_remove:
            from bson import ObjectId
            await db.articles.delete_one({'_id': ObjectId(item['id'])})
            removed_count += 1
            logger.info(f"Removed duplicate: {item['title']}...")
        
        remaining = await db.articles.count_documents({})
        
        return {
            "success": True,
            "removed": removed_count,
            "removed_articles": [item['title'] for item in to_remove[:10]],
            "remaining": remaining
        }
    except Exception as e:
        logger.error(f"Error cleaning duplicates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/admin/cleanup-old-articles")
async def admin_cleanup_old_articles(authorized: bool = Depends(get_admin_auth)):
    """
    Manually cleanup articles older than 14 days (2 weeks).
    This is a FREE operation - no API costs.
    Requires admin authentication.
    """
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=14)
        
        # Count before cleanup
        total_before = await db.articles.count_documents({})
        old_count = await db.articles.count_documents({
            'publishedDate': {'$lt': cutoff_date.isoformat()}
        })
        
        # Delete old articles
        result = await db.articles.delete_many({
            'publishedDate': {'$lt': cutoff_date.isoformat()}
        })
        
        total_after = await db.articles.count_documents({})
        
        return {
            "success": True,
            "message": "Cleaned up articles older than 14 days",
            "articles_before": total_before,
            "articles_deleted": result.deleted_count,
            "articles_remaining": total_after,
            "cutoff_date": cutoff_date.isoformat(),
            "cost": "$0 (FREE operation)"
        }
    except Exception as e:
        logger.error(f"Error in manual cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/admin/fix-bad-content")
async def fix_bad_content(authorized: bool = Depends(get_admin_auth)):
    """
    Archive articles with AI refusal text or old fallback/template filler.
    No fallback articles should be rewritten or kept live.
    Requires admin authentication.
    """
    try:
        bad_content_indicators = [
            "I cannot write",
            "I can't write",
            "cannot fabricate",
            "can't fabricate",
            "no source to support",
            "no evidence of",
            "As Perplexity",
            "my core responsibility",
            "I'd be happy to",
            "If you'd like me to",
            "I could create a news article covering",
            "maintain strict accuracy",
            "ground every claim",
            "These are real, documented events",
            "Alternatively, if you have",
            "This developing story has been reported by",
            "Local authorities and emergency services are understood to be involved",
            "Residents in the affected area are advised to stay informed through official channels",
            "Anyone with information related to this story is encouraged to contact the relevant authorities",
            "This story has been reported by",
            "Local residents and community members have been following developments with interest",
            "This business story has been reported by",
            "Industry observers and local stakeholders are monitoring the situation closely",
            "This health story has been reported by",
            "This entertainment story has been covered by",
            "This sports story has been reported by"
        ]

        active_filter = {"$or": [{"archived": {"$exists": False}}, {"archived": False}]}
        articles = await db.articles.find(active_filter, {"_id": 0}).to_list(2000)

        archived_count = 0
        archived_articles = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for article in articles:
            content = str(article.get("content", "") or "")
            content_lower = content.lower()
            is_bad = any(indicator.lower() in content_lower for indicator in bad_content_indicators)

            if not is_bad:
                continue

            title = article.get("title", "")
            await db.articles.update_one(
                {"id": article.get("id")},
                {"$set": {
                    "archived": True,
                    "archived_at": now_iso,
                    "archive_reason": "bad_ai_or_fallback_content",
                    "manual_review_hidden_from_public": True,
                    "manual_review_reason": "AI refusal/fallback/template filler detected; archived instead of rewritten"
                }}
            )

            archived_count += 1
            archived_articles.append(title[:80] + "...")
            logger.info(f"Archived bad/fallback content article: {title[:60]}...")

        return {
            "success": True,
            "articles_checked": len(articles),
            "articles_archived": archived_count,
            "archived_titles": archived_articles,
            "cost": "$0 (FREE - no API calls)"
        }

    except Exception as e:
        logger.error(f"Error archiving bad content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/fix-mismatched-content")
async def fix_mismatched_content(authorized: bool = Depends(get_admin_auth)):
    """
    Legacy cleanup endpoint.
    Archive articles containing old emergency/fallback template filler.
    No fallback/template articles should be rewritten or kept live.
    """
    try:
        active_filter = {
            "$and": [
                {"$or": [{"archived": {"$exists": False}}, {"archived": False}]},
                {"content": {"$regex": "emergency services.*affected area", "$options": "i"}}
            ]
        }
        articles = await db.articles.find(active_filter).to_list(500)

        archived_count = 0
        archived_articles = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for article in articles:
            title = article.get("title", "")
            await db.articles.update_one(
                {"_id": article["_id"]},
                {"$set": {
                    "archived": True,
                    "archived_at": now_iso,
                    "archive_reason": "old_mismatched_fallback_template",
                    "manual_review_hidden_from_public": True,
                    "manual_review_reason": "Old emergency/fallback template detected; archived instead of rewritten"
                }}
            )
            archived_count += 1
            archived_articles.append(title[:80] + "...")
            logger.info(f"Archived mismatched fallback/template article: {title[:60]}...")

        return {
            "success": True,
            "articles_checked": len(articles),
            "articles_archived": archived_count,
            "archived_titles": archived_articles,
            "message": f"Archived {archived_count} articles with old mismatched fallback templates"
        }

    except Exception as e:
        logger.error(f"Error archiving mismatched fallback content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/remove-product-articles")
async def remove_product_articles(authorized: bool = Depends(get_admin_auth)):
    """
    Remove articles that are product advertisements, gadgets, deals, or shopping content.
    These should not appear on a news site.
    """
    try:
        # Keywords that indicate product/shopping articles
        product_keywords = [
            'gadget', 'blender', 'air fryer', 'nutribullet', 'ninja', 'dyson', 'shark',
            'reduced to £', 'now just £', 'now only £', 'deal stack', 'price slash',
            'shoppers snapping', 'shoppers rushing', 'flying off shelves', 'selling fast',
            'argos deal', 'amazon shoppers', 'tesco shoppers', 'aldi shoppers',
            'cheaper than the osteopath', 'cheaper than physio', 'pain relief gadget',
            'massage gun', 'posture corrector', 'vacuum cleaner', 'coffee machine',
            'kitchen gadget', 'home gadget', 'cleaning gadget',
            'much cheaper than', 'fraction of the price', 'save over £',
            'five-star reviews', '5-star reviews', 'rave reviews', 'shoppers are loving',
            'i swear by', 'game-changer', 'life-changing gadget'
        ]
        
        # Get all articles
        all_articles = await db.articles.find({}).to_list(1000)
        
        removed_count = 0
        removed_titles = []
        
        for article in all_articles:
            title = article.get('title', '').lower()
            content = article.get('content', '').lower()
            text = f"{title} {content}"
            
            # Check if article matches any product keyword
            is_product = any(keyword.lower() in text for keyword in product_keywords)
            
            # Also check for price patterns like "£14" in title with product context
            import re
            has_price_pattern = re.search(r'(reduced to|now just|now only|was £\d+.*now|save (over )?£)\d+', text)
            
            if is_product or has_price_pattern:
                # Delete the article
                await db.articles.delete_one({'_id': article['_id']})
                removed_count += 1
                removed_titles.append(article.get('title', 'Unknown')[:60] + "...")
                logger.info(f"Removed product article: {article.get('title', '')[:50]}...")
        
        return {
            "success": True,
            "articles_checked": len(all_articles),
            "articles_removed": removed_count,
            "removed_titles": removed_titles[:20],  # Only return first 20 titles
            "message": f"Removed {removed_count} product/gadget articles"
        }
        
    except Exception as e:
        logger.error(f"Error removing product articles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/sync-rss-now")
async def sync_rss_now(authorized: bool = Depends(get_admin_auth)):
    """
    Force immediate sync of RSS feeds - imports latest articles from all feeds.
    This is useful after deployment to quickly get the latest articles.
    """
    try:
        from app.news_feed_service import news_feed_service
        import re
        from app.perplexity_service import perplexity_service
        from uuid import uuid4
        
        def canonicalize_url(url: str) -> str:
            try:
                from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
                u = url.strip()
                if not u:
                    return ""
                parts = urlparse(u)
                keep = [(k, v) for (k, v) in parse_qsl(parts.query, keep_blank_values=True)
                        if not (k.lower().startswith("utm_") or k.lower() in ("at_medium", "at_campaign", "fbclid", "gclid", "mc_cid", "mc_eid"))]
                new_query = urlencode(keep, doseq=True)
                return urlunparse((parts.scheme, parts.netloc, parts.path, parts.params, new_query, parts.fragment))
            except Exception:
                return (url or "").strip()

        logger.info("Starting manual RSS sync...")
        
        # Get existing article titles/source URLs to avoid duplicates
        existing_articles = await db.articles.find({}, {'title': 1, 'source_url': 1}).to_list(2000)
        existing_titles = {a['title'].lower().strip() for a in existing_articles if a.get('title')}
        existing_urls = set()
        for a in existing_articles:
            u = (a.get('source_url') or '').strip()
            if u:
                existing_urls.add(canonicalize_url(u))
        
        # Fetch all RSS feeds
        rss_articles = await news_feed_service.fetch_all_feeds()
        logger.info(f"Fetched {len(rss_articles)} articles from RSS feeds")
        
        # Filter for new articles with images
        new_articles = []
        # Import-time editorial filters (project rules)
        # - block sports and hard-crime at ingestion (not just homepage display)
        # - de-dupe within this sync batch
        sport_kw = re.compile(
            r"(\bsport\b|football|premier league|championship|efl|super league|"
            r"rugby|cricket|tennis|golf|boxing|f1|formula 1|grand prix|race|"
            r"var\b|match\b|cup\b|league\b|hull kr|leeds|west ham|"
            r"arsenal|chelsea|liverpool|manchester|derby|leicester|hull)",
            re.I
        )
        hard_crime_kw = re.compile(r"(murder|kill(?:ed|s)?|killed|homicide|manslaughter|found dead|body found|death|died|dies|stab|shoot|rape|jailed|sentenc|charged|trial|convict)", re.I)
        crime_kw = re.compile(r"(police|arrest|court|jailed|sentenc|charged|trial|inquest|knife crime|stabb|shoot|assault|drink[- ]driver|drink[- ]driving|drunk[- ]driver|dui|dwi)", re.I)
        obituary_kw = re.compile(r"(death notices?|funeral notices?|funeral arrangements|in memoriam|death announcements?|passed away peacefully|loving memory|beloved husband|beloved wife|beloved mum|beloved mom|beloved dad|family announcement)", re.I)
        sync_low_utility_kw = re.compile(
            r"\b(celebrity|showbiz|reality\s*tv|love island|netflix|movie|film|album|concert|music\s*video|book\s*launch|novel|brit awards|baftas|royal fashion|gift guide|black friday|cyber monday|shopping deal|must-have buys?|restaurant review|afternoon tea|food\s+festival|arts\s+festival|music\s+festival|best\s+places\s+to\s+live|market\s+town\s+named|charming\s+cottage|dream\s+home|period\s+home|house\s+for\s+sale|farmhouse\s+for\s+sale|stunning\s+home|property\s+of\s+the\s+week|inside\s+this\s+home|listed\s+for\s+sale|tasted?\s+and\s+rated|best supermarket|holiday mistake|travel experts?|woodland you need to visit|visit this spring|play area|safari park celebrates|zoo hails birth|in pictures)\b",
            re.I,
        )
        local_utility_kw = re.compile(
            r"\b(council|planning|approved|refused|development|homes?|housing|bridge|road|motorway|m6|m56|station|rail|train|bus|waste|bins?|school|college|hospital|nhs|business|jobs?|firm|factory|company|funding|flood|warning|closure|traffic|crash|re-open|reopen|town centre|charity|police|court|tax|price|cost|energy|water|sewage)\b",
            re.I,
        )
        science_keep_kw = re.compile(
            r"\b(ai|artificial intelligence|tech|technology|chip|chips|semiconductor|cyber|software|robot|cloud|openai|chatgpt|gemini|nasa|space|artemis)\b",
            re.I,
        )
        sync_crime_kw = re.compile(
            r"\b(crime spree|behind bars|groomed|grooming|roblox|sex offender|paedophile|pedophile|child abuse|sexual abuse|stab(?:bed|bing)?|shoot(?:ing)?|murder|manslaughter|rape|jailed|sentenc(?:ed|ing)|charged|trial|court appearance|arrested)\b",
            re.I,
        )
        sync_local_advice_kw = re.compile(
            r"\b(martin lewis|money saving expert|check this simple thing|before it'?s too late|warning about this common|common holiday mistake|travel experts? issu(?:e|es) warning|consumer warning)\b",
            re.I,
        )
        sync_opinion_kw = re.compile(
            r"\b(the hill i will die on|if you spend it right|comment is free)\b",
            re.I,
        )
        sync_local_lifestyle_kw = re.compile(
            r"\b(coffee machine|air fryer|vacuum cleaner|mornings?, myself|transformed my mornings|saved me a load of cash|must-have buy|my favourite product|beauty buy|skincare|make-up|fashion find)\b",
            re.I,
        )
        seen_new_titles = set()
        seen_urls = set()

        for article in rss_articles:
            title = article.get('title', '').strip()
            if not title:
                continue

            norm = title.lower().strip()
            url = (article.get('source_url') or '').strip()
            if norm in existing_titles:
                continue
            if url:
                c_url = canonicalize_url(url)
                if c_url in existing_urls:
                    continue
                if c_url in seen_urls:
                    continue
            else:
                if norm in seen_new_titles:
                    continue

            # Block sports + hard crime at ingestion
            src = (article.get('source') or '').lower()
            url = (article.get('source_url') or '').lower()

            # Hard block known sports publishers
            if 'sky sports' in src or 'bbc sport' in src:
                continue

            # Block sport URLs
            if '/sport/' in url or 'skysports' in url:
                continue

            low = title.lower()

            # Block obituary / memorial notice-style content, but not general news reporting
            if obituary_kw.search(title):
                continue

            # Structural sports patterns
            if ((' vs ' in low) or (' v ' in low)) and ('team news' in low or ' live' in low or 'kick-off' in low or 'kickoff' in low or 'line-up' in low or 'lineup' in low):
                continue

            low = title.lower()
            # Structural sports patterns (captures many football/rugby headlines that omit explicit sport words)
            if ((" vs " in low) or (" v " in low)) and ("team news" in low or " live" in low or "kick-off" in low or "kickoff" in low or "line-up" in low or "lineup" in low):
                continue

            if sport_kw.search(title):
                continue
            if hard_crime_kw.search(title):
                continue
            if crime_kw.search(title):
                continue

            if not article.get('image'):
                continue

            text_all = " ".join([
                article.get('title', ''),
                article.get('summary', ''),
                article.get('content', ''),
                article.get('category', ''),
            ]).lower()
            cat_lower = (article.get('category') or '').lower()

            if sync_low_utility_kw.search(text_all):
                continue

            # Block low-value incident / animal / tabloid filler
            sync_noise_kw = re.compile(
                r"(driver|crash|injured|pulled from vehicle|emergency services|"
                r"zoo|wildlife park|lion|antelopes?|dogs? brains?|rescued animals?|"
                r"I had to|family says|heartbroken|after my|rescued by firefighters)",
                re.I,
            )
            sync_econ_kw = re.compile(
                r"\b(mortgage|rent|rents|tax|budget|inflation|interest\s*rate|rates|jobs|wages|economy|economic|business|finance|markets?|prices?|bills?|energy|council|planning|housing|investment|trade|tariff|regulation|ofgem|ofwat|boe|bank of england|warehouse|development|stores?|retail|jobs?)\b",
                re.I,
            )
            if sync_noise_kw.search(text_all) and not sync_econ_kw.search(text_all):
                continue


            if cat_lower == 'science' and not science_keep_kw.search(text_all):
                continue

            if sync_crime_kw.search(text_all):
                continue

            if sync_opinion_kw.search(text_all):
                continue

            if article.get('is_local_source') is True and sync_local_advice_kw.search(text_all):
                continue

            if article.get('is_local_source') is True and sync_local_lifestyle_kw.search(text_all):
                continue

            if article.get('is_local_source') is True and not (article.get('location') or article.get('priority_location')):
                if not local_utility_kw.search(text_all):
                    continue

            if url:
                seen_urls.add(c_url)
            else:
                seen_new_titles.add(norm)
            new_articles.append(article)
        
        logger.info(f"Found {len(new_articles)} new articles to import")

        # Rank candidates to match project positioning (Local + economic utility first)
        econ_kw = re.compile(r"\b(mortgage|rent|rents|tax|budget|inflation|interest\s*rate|rates|jobs|wages|economy|economic|business|finance|markets?|prices?|bills?|energy|council|planning|housing|investment|trade|tariff|regulation|ofgem|ofwat|boe|bank of england)\b", re.I)
        low_utility_kw = re.compile(r"\b(brit awards|baftas|celebrity|film|tv|ceremony|showbiz|royal fashion)\b", re.I)

        def candidate_score(a: dict) -> int:
            score = 0
            title = (a.get("title") or "")
            cat = (a.get("category") or "").lower()
            if a.get("is_local_source") is True:
                score += 3
            if cat in ("business","tech","finance","tax","ai"):
                score += 2
            if econ_kw.search(title):
                score += 2
            if low_utility_kw.search(title):
                score -= 2
            return score

        # Stable sort: higher score first, preserve original order on ties
        scored = [(i, candidate_score(a), a) for i, a in enumerate(new_articles)]
        scored.sort(key=lambda x: (-x[1], x[0]))
        new_articles = [a for _, _, a in scored]

        # Import up to 10 new articles
        imported_count = 0
        imported_titles = []
        max_import = 10
        
        # Prefer local items when available; then fill with best non-local.
        local_target = int(os.getenv("LOCAL_SYNC_TARGET", "4") or "4")
        local_items = [a for a in new_articles if a.get("is_local_source") is True]
        non_local_items = [a for a in new_articles if a.get("is_local_source") is not True]

        picked = []
        seen_titles = set()
        source_counts = {}

        def pick_from(pool, cap):
            for a in pool:
                if len(picked) >= max_import:
                    break
                if cap is not None and cap <= 0:
                    break
                t = (a.get("title") or "").strip().lower()
                src = (a.get("source") or "").strip().lower()
                if not t:
                    continue
                if t in seen_titles:
                    continue
                # Soft source de-dupe to reduce repetition (allow if needed later)
                if src:
                    c = source_counts.get(src, 0)
                    if c >= 1:
                        continue
                picked.append(a)
                seen_titles.add(t)
                if src:
                    source_counts[src] = source_counts.get(src, 0) + 1
                if cap is not None:
                    cap -= 1

        pick_from(local_items, local_target)
        pick_from(non_local_items, None)

        for article in picked:
            try:
                title = article.get('title', '').strip()
                original_content = article.get('content', '')
                source = article.get('source', 'News Source')
                source_url = article.get('source_url', '')
                
                # Generate detailed content using Perplexity
                logger.info(f"Generating content for: {title[:50]}...")
                detailed_content = await perplexity_service.generate_article_content(
                    title=title,
                    summary=original_content,
                    source=source,
                    source_url=source_url
                )
                
                # Strict quality gate: publish only full-length rewritten content
                if len((detailed_content or "").strip()) < 1000:
                    logger.info(f"Skipping short-content picked article after rewrite attempt: {title[:60]}...")
                    continue

                # Create article document
                article_doc = {
                    'id': str(uuid4()),
                    'title': title,
                    'content': detailed_content,
                    'summary': original_content[:200] + '...' if len(original_content) > 200 else original_content,
                    'original_summary': original_content,
                    'image': article.get('image'),
                    'image_source': 'rss_feed',
                    'category': article.get('category', 'Local News'),
                    'source': source,
                    'source_url': source_url,
                    'author': source,
                    'scope': 'cheshire' if article.get('is_cheshire_related') else 'uk',
                    'is_local_source': article.get('is_local_source', False),
                    'location': article.get('location'),
                    'priority_location': article.get('priority_location') or article.get('location'),
                    'publishedDate': ((article.get('publishedDate') if article.get('publishedDate') is not None else article.get('published_date')) if isinstance((article.get('publishedDate') if article.get('publishedDate') is not None else article.get('published_date')), datetime) and (article.get('publishedDate') if article.get('publishedDate') is not None else article.get('published_date')).tzinfo else (((article.get('publishedDate') if article.get('publishedDate') is not None else article.get('published_date')).replace(tzinfo=timezone.utc)) if isinstance((article.get('publishedDate') if article.get('publishedDate') is not None else article.get('published_date')), datetime) else ((lambda dt: dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc))(datetime.fromisoformat(str((article.get('publishedDate') if article.get('publishedDate') is not None else article.get('published_date'))).replace('Z', '+00:00'))) if (article.get('publishedDate') if article.get('publishedDate') is not None else article.get('published_date')) else datetime.now(timezone.utc)))),
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'archived': False
                }

                article_doc['content'] = sanitize_rss_text(
                    article_doc.get('content', ''),
                    article_doc.get('source_url', ''),
                    is_summary=False,
                )
                article_doc['summary'] = sanitize_rss_text(
                    article_doc.get('summary', ''),
                    article_doc.get('source_url', ''),
                    is_summary=True,
                )
                article_doc = apply_ai_manual_review_guard(
                    article_doc,
                    article_doc.get('content', ''),
                    ai_rewrite_used=True,
                    title=title,
                )
                article_doc = attach_manual_review_editorial_metadata(article_doc)
                
                await db.articles.insert_one(article_doc)
                imported_count += 1
                imported_titles.append(title[:60] + "...")
                existing_titles.add(title.lower())
                if source_url:
                    existing_urls.add(canonicalize_url(source_url))
                logger.info(f"✅ Imported: {title[:50]}...")
                
            except Exception as e:
                logger.error(f"Error importing article: {str(e)}")
                continue
        
        return {
            "success": True,
            "rss_articles_found": len(rss_articles),
            "new_articles_found": len(new_articles),
            "articles_imported": imported_count,
            "imported_titles": imported_titles,
            "message": f"Synced RSS feeds - imported {imported_count} new articles"
        }
        
    except Exception as e:
        logger.error(f"Error syncing RSS: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/fix-duplicate-images")
async def fix_duplicate_images():
    """Fix articles with duplicate or missing images (admin utility)"""
    try:
        # Get all articles
        all_articles = await db.articles.find({}).to_list(1000)
        
        # Track image usage
        image_usage = {}
        articles_to_update = []
        
        for article in all_articles:
            article_id = article['_id']
            image_url = article.get('image')
            
            if not image_url:
                # Article has no image
                articles_to_update.append({
                    'id': article_id,
                    'reason': 'missing',
                    'category': article.get('category', 'Local News')
                })
            else:
                # Track image usage
                if image_url not in image_usage:
                    image_usage[image_url] = []
                image_usage[image_url].append(article_id)
        
        # Find duplicates
        for image_url, article_ids in image_usage.items():
            if len(article_ids) > 1:
                # Keep the first article with this image, update the rest
                for article_id in article_ids[1:]:
                    article = next(a for a in all_articles if a['_id'] == article_id)
                    articles_to_update.append({
                        'id': article_id,
                        'reason': 'duplicate',
                        'category': article.get('category', 'Local News'),
                        'old_image': image_url
                    })
        
        # Collect all currently used images (keeping the first occurrence)
        used_images = set(image_usage.keys())
        
        # Collect all available images
        all_available_images = []
        for cat_images in CATEGORY_IMAGES.values():
            all_available_images.extend(cat_images)
        all_available_images = list(set(all_available_images))
        
        # Update articles with unique images
        updated_count = 0
        for item in articles_to_update:
            article_id = item['id']
            category = item['category']
            
            # Get available images for this category
            category_images = CATEGORY_IMAGES.get(category, CATEGORY_IMAGES['Local News'])
            available = [img for img in category_images if img not in used_images]
            
            # If no category images available, use any available image
            if not available:
                available = [img for img in all_available_images if img not in used_images]
            
            # If still no images, skip (shouldn't happen with expanded pool)
            if not available:
                logger.warning(f"No available images for article {article_id}")
                continue
            
            # Select and assign new image
            new_image = random.choice(available)
            used_images.add(new_image)
            
            # Update in database
            await db.articles.update_one(
                {'_id': article_id},
                {'$set': {'image': new_image}}
            )
            
            updated_count += 1
            logger.info(f"Updated article {article_id}: {item['reason']} - assigned {new_image[:60]}...")
        
        return {
            "success": True,
            "articles_updated": updated_count,
            "total_checked": len(all_articles),
            "duplicates_fixed": len([a for a in articles_to_update if a['reason'] == 'duplicate']),
            "missing_fixed": len([a for a in articles_to_update if a['reason'] == 'missing'])
        }
        
    except Exception as e:
        logger.error(f"Error fixing duplicate images: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/scheduler-status")
async def get_scheduler_status():
    """Get scheduler status and next run time (version-safe)"""
    try:
        jobs = scheduler.get_jobs()
        job_info = []

        for job in jobs:
            # APScheduler versions differ: some expose next_run_time, some don't
            nrt = getattr(job, "next_run_time", None)

            # Convert to ISO if possible
            if hasattr(nrt, "isoformat"):
                nrt_iso = nrt.isoformat()
            else:
                nrt_iso = None

            job_info.append({
                "id": getattr(job, "id", None),
                "name": getattr(job, "name", None),
                "next_run_time": nrt_iso
            })

        return {
            "scheduler_running": bool(getattr(scheduler, "running", False)),
            "jobs": job_info,
            "total_jobs": len(job_info)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@api_router.post("/emergency-fix-all-images")
@api_router.post("/force-clean-newspaper-images")
async def force_clean_newspaper_images():
    """Manually trigger removal of all newspaper/banned images"""
    return await auto_fix_duplicate_images()

async def emergency_fix_all_images():
    """EMERGENCY: Force reassign ALL images with category-appropriate verified images"""
    try:
        logger.info("EMERGENCY IMAGE FIX: Starting complete image reassignment")
        
        # Get all articles
        all_articles = await db.articles.find({}).to_list(1000)
        logger.info(f"Found {len(all_articles)} total articles")
        
        # Collect all available images
        all_available_images = []
        for cat_images in CATEGORY_IMAGES.values():
            all_available_images.extend(cat_images)
        all_available_images = list(set(all_available_images))
        
        logger.info(f"Total unique images available: {len(all_available_images)}")
        
        updated_count = 0
        category_counts = {}
        
        for article in all_articles:
            category = article.get('category', 'Local News')
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # Get appropriate images for this category
            category_images = CATEGORY_IMAGES.get(category, CATEGORY_IMAGES.get('Local News', []))
            
            if not category_images:
                logger.warning(f"No images for category: {category}")
                continue
            
            # Randomly select an image from the category
            import random
            new_image = random.choice(category_images)
            
            # Update article
            await db.articles.update_one(
                {'_id': article['_id']},
                {'$set': {'image': new_image}}
            )
            updated_count += 1
        
        logger.info(f"EMERGENCY FIX COMPLETE: Updated {updated_count} articles")
        logger.info(f"Category distribution: {category_counts}")
        
        return {
            "success": True,
            "message": "Emergency image fix completed",
            "articles_updated": updated_count,
            "total_articles": len(all_articles),
            "categories": category_counts,
            "total_images_available": len(all_available_images),
            "cheshire_local_news_images": len(CATEGORY_IMAGES.get('Local News', []))
        }
        
    except Exception as e:
        logger.error(f"Emergency image fix error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Include the routers in the main app

# =====================================================================================
# EXPLICIT HEAD ROUTES FOR SEO (bots/CDNs sometimes probe with HEAD)
# =====================================================================================

@app.head("/sitemap.xml")
async def head_sitemap():
    return await generate_sitemap()

@app.head("/news-sitemap.xml")
async def head_news_sitemap():
    return await generate_news_sitemap()

@api_router.head("/seo/article/{article_id}")
async def head_seo_article_page(article_id: str, request: Request):
    return await get_seo_article_page(article_id=article_id, request=request)

@api_router.head("/article/{article_id}")
async def head_api_article(article_id: str):
    return await serve_article_html(article_id)

@app.head("/article/{article_id}")
async def head_article(article_id: str):
    return await serve_article_for_production(article_id)

app.include_router(api_router)
app.include_router(rss_routes.router)
app.include_router(
    rss_routes.create_admin_import_router(get_admin_auth)
)

# =====================================================================================
# SERVE REACT FRONTEND (Render copies build into backend/frontend_build)
# - Serve index.html at /
# - Serve real files when they exist (/static/* etc)
# - Otherwise return index.html so client-side routes work (/privacy, /terms, etc)
# - Never hijack /api/*
# =====================================================================================
from pathlib import Path
from fastapi.responses import FileResponse

_FRONTEND_DIR = Path(__file__).resolve().parent / "frontend_build"
_INDEX_HTML = _FRONTEND_DIR / "index.html"


def _is_crawler_request(request: Request) -> bool:
    user_agent = request.headers.get("user-agent", "").lower()
    return any(bot in user_agent for bot in [
        "facebookexternalhit",
        "twitterbot",
        "linkedinbot",
        "whatsapp",
        "telegrambot",
        "slackbot",
        "discordbot",
        "googlebot",
        "bingbot",
        "crawler",
        "bot",
    ])


async def serve_public_hub_html(full_path: str = ""):
    """Crawler/static HTML for public homepage, category and location hub pages."""
    from fastapi.responses import HTMLResponse
    import html as _html
    import json as _json
    import urllib.parse

    base_url = "https://cheshiretoday.co.uk"
    clean_path = str(full_path or "").strip().strip("/")
    path_parts = [p for p in clean_path.split("/") if p]

    category_slug_map = PUBLIC_CATEGORY_HUBS
    locations = PUBLIC_LOCATION_HUBS

    page_kind = "home"
    page_title = "Cheshire Today | Local News, Business, AI & Tech, Finance"
    page_desc = "Latest Cheshire news, business updates, finance guides and practical AI and technology coverage from Cheshire Today."
    canonical_path = "/"

    article_query = {
        "$or": [{"archived": {"$exists": False}}, {"archived": False}],
        "manual_review_hidden_from_public": {"$ne": True},
        "title": {"$exists": True, "$ne": ""},
        "image": {"$exists": True, "$ne": ""},
    }

    if len(path_parts) >= 2 and path_parts[0] == "category":
        category_slug = path_parts[1]
        category_config = category_slug_map.get(category_slug)
        if not category_config:
            raise HTTPException(status_code=404, detail="Not Found")

        page_kind = "category"
        canonical_path = f"/category/{category_slug}"
        page_title = f"{category_config['title']} | Cheshire Today"
        page_desc = category_config["description"]
        _apply_public_category_hub_filter(article_query, category_config)

    elif len(path_parts) == 1 and path_parts[0] in locations:
        location = path_parts[0]
        location_label = location.replace("-", " ").title()
        page_kind = "location"
        canonical_path = f"/{location}"
        page_title = f"{location_label} news | Cheshire Today"
        page_desc = f"Latest news and updates for {location_label} and the wider Cheshire area."
        if location == "cheshire-general":
            article_query["$and"] = article_query.get("$and", []) + [
                {"$or": [
                    {"location": None},
                    {"location": {"$exists": False}},
                ]},
                {"$or": [
                    {"is_cheshire_related": True},
                    {"is_local_source": True},
                ]},
            ]
        else:
            article_query["location"] = location

    elif clean_path in ("", "latest-articles", "article-index"):
        page_kind = "home"
        canonical_path = "/" if clean_path == "" else f"/{clean_path}"
        if clean_path in ("latest-articles", "article-index"):
            page_title = "Latest articles | Cheshire Today"
            page_desc = "Latest public articles from Cheshire Today across local news, business, finance and technology."
    else:
        raise HTTPException(status_code=404, detail="Not Found")

    articles = await db.articles.find(
        article_query,
        {
            "_id": 1,
            "id": 1,
            "title": 1,
            "summary": 1,
            "category": 1,
            "publishedDate": 1,
            "created_at": 1,
        }
    ).sort([("created_at", -1), ("publishedDate", -1)]).limit(40).to_list(40)

    # Strong/indexable guides only: keep thin/stub guides out of crawler hub links.
    guide_docs = await db.authority_pages.find(
        {"status": {"$in": ["published", "live"]}},
        {"_id": 0, "slug": 1, "title": 1, "category": 1, "sections": 1, "updatedAt": 1}
    ).sort("updatedAt", -1).limit(80).to_list(80)

    guides = []
    for guide in guide_docs:
        sections = guide.get("sections") if isinstance(guide.get("sections"), list) else []
        content_len = sum(
            len(str(section.get("content") or "").strip())
            for section in sections
            if isinstance(section, dict)
        )
        if content_len < 700:
            continue
        guides.append(guide)

    if page_kind == "category":
        wanted = page_title.split(" news and updates", 1)[0]
        category_guides = [
            g for g in guides
            if str(g.get("category") or "").lower() == wanted.lower()
        ]
        if not category_guides:
            category_guides = guides[:12]
    else:
        category_guides = guides[:16]

    def article_url(article):
        public_id = str(article.get("_id") or article.get("id") or "").strip()
        raw_title = str(article.get("title") or "article")
        slug = re.sub(r"[^a-z0-9]+", "-", raw_title.lower()).strip("-")
        slug = slug[:80] if slug else "article"
        return f"{base_url}/article/{urllib.parse.quote(public_id)}/{urllib.parse.quote(slug)}"

    article_items = []
    for article in articles:
        title = _html.escape(str(article.get("title") or "Untitled article"))
        url = _html.escape(article_url(article))
        category = _html.escape(str(article.get("category") or "News"))
        desc = _html.escape(re.sub(r"\s+", " ", str(article.get("summary") or "")).strip()[:180])
        article_items.append(f'<li><a href="{url}">{title}</a><p>{category}</p><p>{desc}</p></li>')
    if not article_items:
        article_items.append(
            "<li>No public articles are currently available for this section.</li>"
        )

    guide_items = []
    for guide in category_guides:
        slug = str(guide.get("slug") or "").strip()
        if not slug:
            continue
        title = _html.escape(str(guide.get("title") or slug.replace("-", " ").title()))
        category = _html.escape(str(guide.get("category") or "Guides"))
        url = _html.escape(f"{base_url}/guides/{slug}")
        guide_items.append(f'<li><a href="{url}">{title}</a><p>{category}</p></li>')

    category_links = []
    for slug, config in category_slug_map.items():
        category_links.append(
            f'<li><a href="{base_url}/category/{slug}">'
            f'{_html.escape(config["label"])}</a></li>'
        )

    location_links = []
    for loc in sorted(locations):
        label = loc.replace("-", " ").title()
        location_links.append(f'<li><a href="{base_url}/{loc}">{_html.escape(label)}</a></li>')

    canonical = f"{base_url}{canonical_path}"
    esc_title = _html.escape(page_title)
    esc_desc = _html.escape(page_desc)
    esc_canon = _html.escape(canonical)

    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": page_title,
        "description": page_desc,
        "url": canonical,
        "publisher": {
            "@type": "Organization",
            "name": "Cheshire Today",
            "logo": {
                "@type": "ImageObject",
                "url": "https://cheshiretoday.co.uk/logo.png",
            },
        },
    }
    schema_json = _json.dumps(schema, ensure_ascii=False).replace("</", "<\\/")

    html_content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc_title}</title>
  <link rel="canonical" href="{esc_canon}">
  <meta name="description" content="{esc_desc}">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Cheshire Today">
  <meta property="og:locale" content="en_GB">
  <meta property="og:url" content="{esc_canon}">
  <meta property="og:title" content="{esc_title}">
  <meta property="og:description" content="{esc_desc}">
  <script type="application/ld+json">{schema_json}</script>
</head>
<body>
  <header>
    <h1>{esc_title}</h1>
    <p>{esc_desc}</p>
    <nav>
      <a href="{base_url}/">Home</a> |
      <a href="{base_url}/article-index">Article index</a> |
      <a href="{base_url}/category/local-news">Local News</a> |
      <a href="{base_url}/category/business">Business</a> |
      <a href="{base_url}/category/finance">Finance</a>
    </nav>
  </header>
  <main>
    <section>
      <h2>Latest articles</h2>
      <ul>{''.join(article_items)}</ul>
    </section>
    <section>
      <h2>Useful guides</h2>
      <ul>{''.join(guide_items)}</ul>
    </section>
    <section>
      <h2>Categories</h2>
      <ul>{''.join(category_links)}</ul>
    </section>
    <section>
      <h2>Locations</h2>
      <ul>{''.join(location_links)}</ul>
    </section>
  </main>
</body>
</html>"""

    return HTMLResponse(content=html_content, headers={"Cache-Control": "public, max-age=1800"})


def _spa_file_response(path: Path):
    rel = path.relative_to(_FRONTEND_DIR).as_posix()
    headers = {}

    if rel == "index.html":
        headers["Cache-Control"] = "public, max-age=0, must-revalidate"
    elif rel.startswith("static/"):
        name = path.name
        parts = name.split(".")
        hash_part = parts[-2].lower() if len(parts) >= 3 else ""
        is_hashed = len(hash_part) >= 8 and all(ch in "0123456789abcdef" for ch in hash_part)
        headers["Cache-Control"] = "public, max-age=31536000, immutable" if is_hashed else "public, max-age=3600"
    else:
        headers["Cache-Control"] = "public, max-age=3600"

    return FileResponse(str(path), headers=headers)

def _spa_index_or_500():
    if _INDEX_HTML.is_file():
        return _spa_file_response(_INDEX_HTML)
    raise HTTPException(status_code=500, detail="frontend_build missing (React build not present)")


def _newsletter_landing_crawler_response():
    from fastapi.responses import HTMLResponse

    title = "Cheshire Today Newsletter | Local News and Business Briefing"
    description = (
        "Subscribe free to the Cheshire Today newsletter for local news, business, "
        "property, finance and AI & Tech updates from across Cheshire."
    )
    og_title = "Stay ahead with Cheshire’s daily briefing"
    og_description = (
        "Local news, business, property, finance and AI & Tech stories delivered free "
        "to your inbox."
    )
    url = "https://cheshiretoday.co.uk/newsletter"
    image = "https://cheshiretoday.co.uk/cheshire-today-newsletter-share.png"
    content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{description.replace('&', '&amp;')}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{url}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Cheshire Today">
  <meta property="og:url" content="{url}">
  <meta property="og:title" content="{og_title}">
  <meta property="og:description" content="{og_description.replace('&', '&amp;')}">
  <meta property="og:image" content="{image}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{og_title}">
  <meta name="twitter:description" content="{og_description.replace('&', '&amp;')}">
  <meta name="twitter:image" content="{image}">
</head>
<body>
  <main>
    <h1>{og_title}</h1>
    <p>{og_description.replace('&', '&amp;')}</p>
    <p><a href="{url}">Subscribe free</a></p>
  </main>
</body>
</html>"""
    return HTMLResponse(
        content=content,
        status_code=200,
        headers={"Cache-Control": "public, max-age=1800"},
    )


PUBLIC_SPA_EXACT_PATHS = {
    "admin",
    "jobs",
    "jobs/post",
    "jobs/payment-success",
    "advertise",
    "advertise/pay",
    "advertise/payment-success",
    "privacy",
    "terms",
    "cookies",
    "affiliate-disclosure",
    "contact",
    "unsubscribe",
    "newsletter",
    "newsletter/preferences",
    "newsletter/reactivate",
}


def _is_supported_public_spa_path(full_path: str) -> bool:
    clean_path = str(full_path or "").strip("/")
    if clean_path in PUBLIC_SPA_EXACT_PATHS:
        return True
    if clean_path in PUBLIC_LOCATION_HUBS:
        return True
    if clean_path.startswith("category/"):
        parts = clean_path.split("/")
        return len(parts) == 2 and parts[1] in PUBLIC_CATEGORY_HUBS
    return False


def _public_not_found_response(full_path: str):
    from fastapi.responses import HTMLResponse
    import html as _html

    safe_path = _html.escape(f"/{str(full_path or '').strip('/')}")
    content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Page not found | Cheshire Today</title>
  <meta name="robots" content="noindex, follow">
  <meta name="description" content="The requested Cheshire Today page could not be found.">
</head>
<body>
  <main>
    <p>Cheshire Today</p>
    <h1>Page not found</h1>
    <p>The requested page <code>{safe_path}</code> could not be found.</p>
    <p><a href="/">Return to the Cheshire Today homepage</a></p>
  </main>
</body>
</html>"""
    return HTMLResponse(
        content=content,
        status_code=404,
        headers={"Cache-Control": "no-store"},
    )


@app.get("/")
async def serve_spa_root(request: Request):
    if _is_crawler_request(request):
        return await serve_public_hub_html("")
    return _spa_index_or_500()

@app.head("/")
async def head_spa_root():
    return _spa_index_or_500()

@app.get("/{full_path:path}")
async def serve_react_spa(full_path: str, request: Request):
    if full_path.startswith("api/") or full_path == "api":
        raise HTTPException(status_code=404, detail="Not Found")
    candidate = (_FRONTEND_DIR / full_path)
    if candidate.is_file():
        return _spa_file_response(candidate)
    if _is_crawler_request(request):
        if full_path == "newsletter":
            return _newsletter_landing_crawler_response()
        if (
            full_path in PUBLIC_LOCATION_HUBS
            or (
                full_path.startswith("category/")
                and full_path.split("/", 1)[1] in PUBLIC_CATEGORY_HUBS
            )
        ):
            return await serve_public_hub_html(full_path)
    if _is_supported_public_spa_path(full_path):
        return _spa_index_or_500()
    return _public_not_found_response(full_path)

@app.head("/{full_path:path}")
async def head_react_spa(full_path: str):
    if full_path.startswith("api/") or full_path == "api":
        raise HTTPException(status_code=404, detail="Not Found")
    candidate = (_FRONTEND_DIR / full_path)
    if candidate.is_file():
        return _spa_file_response(candidate)
    if _is_supported_public_spa_path(full_path):
        return _spa_index_or_500()
    return _public_not_found_response(full_path)


# Add GZip compression middleware for faster response delivery
app.add_middleware(GZipMiddleware, minimum_size=500)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Digest helper functions
def is_local(article):
    return (article.get("category") or "").lower() == "local news"

def is_sports(article):
    title = (article.get("title") or "").lower()
    sports = ["football", "rugby", "fa cup", "premier league", "six nations", "match", "goal", "championship"]
    return any(k in title for k in sports)



# --- Digest helper functions ---
def is_local(article):
    return (article.get("category") or "").lower() == "local news"

def is_sports(article):
    title = (article.get("title") or "").lower()
    sports = ["football","rugby","fa cup","premier league","six nations","match","goal","championship"]
    return any(k in title for k in sports)

def is_digest_excluded(article):
    if article.get("archived") is True:
        return True
    if article.get("manual_review_hidden_from_public") is True:
        return True

    title = (article.get("title") or "").lower()
    category = (article.get("category") or "").lower()
    text = f"{title} {(article.get('summary') or '').lower()} {(article.get('content') or '').lower()[:400]}"

    if any(k in category for k in ["sports", "sport", "entertainment", "celebrity", "showbiz"]):
        return True

    crime_terms = [
        "found dead", "found hanged", "hanged", "murder", "killed", "fatal",
        "stabbed", "stabbing", "shot", "shooting", "rape", "sexual abuse",
        "sex attacker", "predator", "jailed", "sentenced", "charged",
        "arrested", "police hunt", "police appeal", "inquest", "court"
    ]
    return any(k in text for k in crime_terms)


# =====================================================================================
# RSS CONTENT HYGIENE
# - Strip naked URLs (esp. the original source_url) from RSS content/summary
# - Strip "Read more / Continue reading" tails
# =====================================================================================
def sanitize_rss_text(text: str, source_url: str = "", *, is_summary: bool = False) -> str:
    if text is None:
        return ""
    t = str(text)

    su = (source_url or "").strip()
    if su:
        t = t.replace(su, "")

    # Remove common "read more" tails that include a URL (line-based)
    t = re.sub(r'(?im)^\s*(read\s+more|continue\s+reading|full\s+story|source)\s*[:\-]?\s*https?://\S+\s*$', '', t)

    # Remove lines that are ONLY a URL
    t = re.sub(r'(?im)^\s*https?://\S+\s*$', '', t)

    # Remove leftover "Read more:" without URL (sometimes after replacement)
    t = re.sub(r'(?im)^\s*(read\s+more|continue\s+reading|full\s+story)\s*[:\-]?\s*$', '', t)

    t = t.replace('\r\n', '\n').replace('\r', '\n')
    t = re.sub(r'\n{3,}', '\n\n', t).strip()

    if is_summary:
        return re.sub(r'\s+', ' ', t).strip()

    paragraphs = [part.strip() for part in re.split(r'\n\s*\n+', t) if part.strip()]
    if len(paragraphs) >= 2:
        return '\n\n'.join(paragraphs)

    # Raw RSS descriptions are commonly flattened into one block upstream.
    # Protect common non-terminal periods before applying the established
    # deterministic two-sentence fallback formatting.
    protected = t
    period_marker = "\ue000"
    while period_marker in protected:
        period_marker += "\ue000"

    protected = re.sub(
        r'\b(?:Mr|Mrs|Ms|Dr|Prof|Ltd|No)\.',
        lambda match: match.group(0).replace('.', period_marker),
        protected,
        flags=re.IGNORECASE,
    )
    protected = re.sub(
        r'\b(?:[A-Z]\.){1,}(?=\s*[A-Z])',
        lambda match: match.group(0).replace('.', period_marker),
        protected,
    )
    protected = re.sub(r'(?<=\d)\.(?=\d)', period_marker, protected)

    sentences = re.split(
        r'(?<=[.!?])\s+|(?<=[.!?]["\'’”])\s+',
        protected,
    )
    sentences = [sentence.replace(period_marker, '.').strip() for sentence in sentences if sentence.strip()]

    attribution_pattern = re.compile(
        r'^(?:(?:Mr|Mrs|Ms|Dr|Prof)\.\s+)?'
        r'(?:[A-Z][A-Za-z\'’\-]+(?:\s+[A-Z][A-Za-z\'’\-]+){0,3}|[Hh]e|[Ss]he|[Tt]hey)\s+'
        r'(?:said|added|told|stated|explained|confirmed|continued|replied)\b'
    )
    merged_sentences = []
    for sentence in sentences:
        if (
            merged_sentences
            and merged_sentences[-1].endswith(('"', '\'', '’', '”'))
            and attribution_pattern.match(sentence)
        ):
            merged_sentences[-1] = f"{merged_sentences[-1]} {sentence}"
        else:
            merged_sentences.append(sentence)
    sentences = merged_sentences

    if len(sentences) >= 4:
        chunks = [' '.join(sentences[i:i + 2]) for i in range(0, len(sentences), 2)]
        return '\n\n'.join(chunks)

    return t


# =====================================================================================
# AI REWRITE MANUAL REVIEW GUARD
# Flags likely hallucinated / unsupported detail patterns before publication.
# =====================================================================================
AI_MANUAL_REVIEW_RISK_TERMS = [
    "police spokesperson",
    "wished to remain anonymous",
    "repair bills",
    "windows shattered",
    "smashed bottles",
    "councillor commented",
    "hashtags",
    "trending locally",
    "British Retail Consortium",
    "Night Time Industries Association",
    "according to local residents",
    "residents have rallied",
    "one regular",
    "closure wave",
    "tourists seeking",
    "source ingredients",
    "police have been notified",
    "officers attending",
    "a spokesperson confirmed",
    "millions of views",
    "insiders suggest",
    "analysts in recent reports",
    "source material",
    "not mentioned in the source",
    "not mentioned in source",
    "no police involvement",
    "resident complaints",
    "specific venue damage",
    "business closures",
]


RSS_WEAK_PUBLIC_REVIEW_MARKERS = [
    "this story has been reported by",
    "more details are expected to emerge soon",
    "for the latest news from across the region, keep following",
]


def find_weak_rss_public_review_reason(article: dict, content: str, ai_rewrite_used: bool = False) -> str:
    """Keep weak RSS/fallback items out of public view unless a real AI rewrite succeeded."""
    if ai_rewrite_used:
        return ""

    image_source = str(article.get("image_source") or "").lower()
    source_flags = " ".join([
        str(article.get("source") or ""),
        str(article.get("source_url") or ""),
        str(article.get("source_type") or ""),
    ]).lower()

    is_rss_or_fallback = (
        "rss" in image_source
        or "fallback" in image_source
        or article.get("is_local_feed") is True
        or article.get("is_local_source") is True
        or "rss" in source_flags
    )

    if not is_rss_or_fallback:
        return ""

    text_blob = " ".join([
        str(content or "").strip(),
        str(article.get("summary") or "").strip(),
    ]).strip()
    text_l = text_blob.lower()

    if len(text_blob) < 1000:
        return "RSS/fallback article is below the public quality floor and needs manual review before publication."

    if any(marker in text_l for marker in RSS_WEAK_PUBLIC_REVIEW_MARKERS):
        return "RSS/fallback article contains boilerplate or placeholder wording and needs manual review before publication."

    return ""


def find_ai_manual_review_hits(content: str):
    text = (content or "").lower()
    hits = []
    for term in AI_MANUAL_REVIEW_RISK_TERMS:
        if term.lower() in text and term not in hits:
            hits.append(term)
    return hits


AI_EDITORIAL_PADDING_PHRASES = [
    "serves as a reminder",
    "serves as an inspiration",
    "is a testament to",
    "underscores the importance",
    "highlights the importance",
    "demonstrates that",
    "this reinforces",
    "this reflects",
    "this illustrates",
    "this showcases",
    "the anticipation is likely",
    "is likely driving",
    "the wider community",
    "charity fundraising often",
    "participants often",
    "friends who have previously",
    "local media coverage",
]


def find_ai_editorial_quality_reasons(content: str, title: str = "") -> list:
    """Detect obvious repetitive, padded or citation-heavy AI rewrites."""
    text = str(content or "").strip()
    if not text:
        return ["AI rewrite returned empty article content."]

    text_lower = text.lower()
    reasons = []

    source_labels = re.findall(r"\[\s*source\s*:[^\]]+\]", text, flags=re.I)
    if len(source_labels) >= 2:
        reasons.append("AI rewrite repeats inline source labels throughout the article.")

    padding_hits = sorted({
        phrase for phrase in AI_EDITORIAL_PADDING_PHRASES
        if phrase in text_lower
    })
    if len(padding_hits) >= 2:
        reasons.append("AI rewrite contains repeated generic AI-style padding or commentary.")

    paragraphs = [
        re.sub(r"\s+", " ", part).strip()
        for part in re.split(r"\n\s*\n+", text)
        if part.strip()
    ]

    normalised_paragraphs = [
        re.sub(r"[^a-z0-9 ]+", "", paragraph.lower()).strip()
        for paragraph in paragraphs
    ]
    if len(normalised_paragraphs) != len(set(normalised_paragraphs)):
        reasons.append("AI rewrite contains duplicated paragraphs.")

    if len(paragraphs) >= 6:
        openings = []
        for paragraph in normalised_paragraphs:
            words = paragraph.split()
            openings.append(" ".join(words[:7]))

        repeated_openings = {
            opening for opening in openings
            if opening and openings.count(opening) >= 2
        }
        if repeated_openings:
            reasons.append("AI rewrite repeats the same paragraph openings or sentence structure.")

    if title and paragraphs:
        normalised_title = re.sub(r"[^a-z0-9 ]+", "", str(title).lower()).strip()
        normalised_lead = normalised_paragraphs[0]
        title_words = {word for word in normalised_title.split() if len(word) > 3}
        lead_words = {word for word in normalised_lead.split() if len(word) > 3}
        if len(title_words) >= 4 and len(title_words & lead_words) / len(title_words) >= 0.9:
            if len(paragraphs) > 1:
                second_words = {
                    word for word in normalised_paragraphs[1].split()
                    if len(word) > 3
                }
                if len(title_words & second_words) / len(title_words) >= 0.75:
                    reasons.append("AI rewrite repeats the headline and lead information.")

    return reasons


LOCAL_SPECIFIC_LOCATION_PATTERN = re.compile(
    r"\b("
    r"Chester|Crewe|Macclesfield|Warrington|Widnes|Runcorn|Knutsford|Wilmslow|Congleton|"
    r"Nantwich|Sandbach|Middlewich|Poynton|Alsager|Northwich|Winsford|Ellesmere Port|"
    r"Frodsham|Holmes Chapel|Alderley Edge|Tarporley|Audlem|Malpas|Prestbury|Handforth|"
    r"Halton|Cheshire East|Cheshire West|Leighton Hospital|Chester Zoo|River Dee|M53|M56|M6|"
    r"Booths Park|Crow Wood Park|Deva Stadium|Bumper'?s Lane|West Street|"
    r"Storyhouse|Tatton Park|Delamere|Jodrell Bank|Oulton Park|Cholmondeley|"
    r"Cheshire Oaks|Blue Planet Aquarium|Speke Hall|Neston|Lymm|Culcheth|"
    r"Great Sankey|Birchwood|Appleton|Mobberley|Disley|Bollington|Haslington|"
    r"Wistaston|Shavington|Willaston|Tarvin|Kelsall|Mickle Trafford|Hooton|"
    r"Handbridge|Hoole|Boughton|Upton|Saltney|Blacon"
    r")\b",
    re.I,
)


VAGUE_CHESHIRE_LOCATION_PATTERN = re.compile(
    r"\b(Cheshire woman|Cheshire man|Cheshire dad|Cheshire mum|Cheshire park|"
    r"Cheshire football club|Cheshire village|Cheshire town|part of Cheshire|in Cheshire)\b",
    re.I,
)


def is_local_article_for_location_review(article: dict) -> bool:
    return (
        (article.get("category") or "").lower() == "local news"
        or (article.get("scope") or "").lower() == "cheshire"
        or article.get("is_local_source") is True
        or article.get("is_local_feed") is True
    )


def has_specific_local_location_detail(article: dict, content: str, title: str = "") -> bool:
    """Require specific local detail in the article text itself.

    Location fields are useful for filtering/navigation, but public local articles
    must also say the actual town, village, site, venue, street, council area or
    named local place in the title, summary or article body.
    """
    text = " ".join([
        str(title or ""),
        str(article.get("summary") or ""),
        str(content or "")[:3500],
    ])

    known_place_found = bool(LOCAL_SPECIFIC_LOCATION_PATTERN.search(text))

    stored_locations = [
        str(article.get("location") or "").strip(),
        str(article.get("priority_location") or "").strip(),
    ]
    stored_location_in_text = any(
        loc and re.search(r"\b" + re.escape(loc) + r"\b", text, re.I)
        for loc in stored_locations
    )

    return known_place_found or stored_location_in_text


def find_local_location_review_reason(article: dict, content: str, title: str = "") -> str:
    if not is_local_article_for_location_review(article):
        return ""

    if has_specific_local_location_detail(article, content, title):
        return ""

    vague_hit = VAGUE_CHESHIRE_LOCATION_PATTERN.search(
        " ".join([str(title or ""), str(article.get("summary") or ""), str(content or "")[:1500]])
    )

    if vague_hit:
        return "Local article uses vague Cheshire wording without a specific town, village, street, venue, council area or named site."

    return "Local article is missing a specific town, village, street, venue, council area or named site."

def apply_ai_manual_review_guard(article: dict, content: str, ai_rewrite_used: bool = False, title: str = ""):
    if ai_rewrite_used:
        article["ai_rewritten"] = True
        article["is_rewritten"] = True

    hits = find_ai_manual_review_hits(content) if ai_rewrite_used else []
    editorial_quality_reasons = find_ai_editorial_quality_reasons(content, title) if ai_rewrite_used else []
    weak_rss_reason = find_weak_rss_public_review_reason(article, content, ai_rewrite_used)
    local_location_reason = find_local_location_review_reason(article, content, title)

    review_reasons = []
    if hits:
        review_reasons.append("AI rewrite contained risky invented-detail phrases; verify against source before promotion or social sharing.")
    review_reasons.extend(editorial_quality_reasons)
    if weak_rss_reason:
        review_reasons.append(weak_rss_reason)
    if local_location_reason:
        review_reasons.append(local_location_reason)

    if review_reasons:
        now_iso = datetime.now(timezone.utc).isoformat()
        article["verification_status"] = "needs_manual_review"
        article["rewrite_status"] = "ai_rewrite_needs_review" if hits else "manual_review_required"
        article["manual_review_hidden_from_public"] = True
        article["manual_review_reason"] = " ".join(review_reasons)
        article["manual_review_created_at"] = now_iso

        if hits or editorial_quality_reasons:
            article["archived"] = True
            article["archived_at"] = now_iso
            article["archive_reason"] = "needs_manual_review"
            article["manual_review_hits"] = hits

        logger.warning(
            f"Article hidden for manual review: {title[:80]} | "
            f"ai_hits={hits} | local_location_missing={bool(local_location_reason)}"
        )
        article = attach_manual_review_editorial_metadata(article)
    elif ai_rewrite_used:
        article.setdefault("verification_status", "ai_rewrite_auto_screened")
        article.setdefault("rewrite_status", "ai_rewritten")

    return article


# Initialize scheduler
scheduler = AsyncIOScheduler(timezone=ZoneInfo("Europe/London"))

async def cleanup_old_articles():
    """
    Remove articles older than 14 days (2 weeks).
    This is a FREE operation - no API costs.
    Runs automatically after each article generation.
    """
    try:
        # Calculate cutoff date (14 days ago - 2 weeks)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=14)
        
        # Count articles that will be deleted
        old_count = await db.articles.count_documents({
            'publishedDate': {'$lt': cutoff_date.isoformat()}
        })
        
        if old_count > 0:
            # Delete articles older than 14 days
            result = await db.articles.delete_many({
                'publishedDate': {'$lt': cutoff_date.isoformat()}
            })
            logger.info(f"🗑️ Cleaned up {result.deleted_count} articles older than 14 days")
        else:
            logger.info("✅ No old articles to clean up (all within 14 days)")
        
        # Safety cap hard-delete disabled.
        # Recent articles were disappearing because anything older than the 100th newest
        # was being permanently deleted, even if still fresh.
        total_count = await db.articles.count_documents({})
        logger.info(f"ℹ️ Safety cap hard-delete disabled; total active articles = {total_count}")
                
    except Exception as e:
        logger.error(f"Error cleaning up old articles: {str(e)}")


def _is_owner_protected_article(article: dict) -> bool:
    """Recognise existing owner approval markers that automated caps must preserve."""
    if article.get("manual_review_hidden_from_public") is True:
        return False
    if str(article.get("verification_status") or "").strip() == "needs_manual_review":
        return False
    if str(article.get("rewrite_status") or "").strip() in {
        "manual_review_required",
        "ai_rewrite_needs_review",
    }:
        return False
    verification_status = str(article.get("verification_status") or "").strip()
    rewrite_status = str(article.get("rewrite_status") or "").strip()
    return bool(
        article.get("manual_edited") is True
        or article.get("manual_edit_protected") is True
        or str(article.get("source") or "").strip() == "Manual Entry"
        or verification_status
        in {"manual_corrected_verified_limited", "manual_force_live"}
        or rewrite_status in {"manual_corrected", "manual_force_live"}
    )


def _counts_towards_visible_cap(article: dict) -> bool:
    """Exclude metadata and unpublished review records from the existing cap."""
    content = str(article.get("content") or "").strip()
    summary = str(article.get("summary") or "").strip()
    return bool(
        content
        and article.get("manual_review_hidden_from_public") is not True
        and str(article.get("verification_status") or "") != "needs_manual_review"
        and str(article.get("rewrite_status") or "")
        not in {"manual_review_required", "ai_rewrite_needs_review"}
        and (
            _is_owner_protected_article(article)
            or len(f"{content} {summary}".strip()) >= 1000
        )
    )


async def cap_visible_articles(keep: int = 200):
    """
    Keep the newest eligible records visible while protecting owner-approved work.
    """
    try:
        candidates = await db.articles.find(
            {
                "$or": [
                    {"archived": {"$exists": False}},
                    {"archived": False},
                    {
                        "archived": True,
                        "archive_reason": {
                            "$in": ["auto_cap", "ratio_rebalance"]
                        },
                    },
                ]
            },
            {
                "_id": 1,
                "content": 1,
                "summary": 1,
                "publishedDate": 1,
                "created_at": 1,
                "source": 1,
                "featured": 1,
                "force_live": 1,
                "is_priority_cheshire": 1,
                "archived": 1,
                "archive_reason": 1,
                "manual_review_hidden_from_public": 1,
                "verification_status": 1,
                "rewrite_status": 1,
                "manual_edited": 1,
                "manual_edit_protected": 1,
            },
        ).to_list(10000)

        def _dt(v):
            if isinstance(v, datetime):
                return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
            if not v:
                return datetime.fromtimestamp(0, tz=timezone.utc)
            try:
                dt = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except Exception:
                return datetime.fromtimestamp(0, tz=timezone.utc)

        candidates.sort(
            key=lambda article: (
                1
                if article.get("force_live") is True
                or article.get("featured") is True
                or article.get("is_priority_cheshire") is True
                else 0,
                max(
                    _dt(article.get("publishedDate")),
                    _dt(article.get("created_at")),
                ),
            ),
            reverse=True,
        )
        protected_ids = {
            article["_id"]
            for article in candidates
            if article.get("_id") is not None
            and _is_owner_protected_article(article)
        }
        eligible = [
            article
            for article in candidates
            if _counts_towards_visible_cap(article)
        ]
        newest_ids = [
            article["_id"]
            for article in eligible[:keep]
            if article.get("_id") is not None
        ]
        keep_ids = list(protected_ids.union(newest_ids))

        # Metadata and unpublished review records do not consume cap slots.
        # They retain their existing visibility/review state; only eligible
        # non-protected records outside the cap are automatically archived.
        eligible_ids = [
            article["_id"]
            for article in eligible
            if article.get("_id") is not None
            and article["_id"] not in protected_ids
        ]
        restore_ids = [
            article["_id"]
            for article in eligible
            if article.get("_id") in keep_ids
            and article.get("archived") is True
            and article.get("archive_reason")
            in {"auto_cap", "ratio_rebalance"}
        ]
        if restore_ids:
            await db.articles.update_many(
                {
                    "_id": {"$in": restore_ids},
                    "archived": True,
                    "archive_reason": {
                        "$in": ["auto_cap", "ratio_rebalance"]
                    },
                },
                {
                    "$set": {"archived": False},
                    "$unset": {
                        "archived_at": "",
                        "archive_reason": "",
                    },
                },
            )

        await db.articles.update_many(
            {
                "_id": {
                    "$in": eligible_ids,
                    "$nin": keep_ids,
                },
            },
            {
                "$set": {
                    "archived": True,
                    "archived_at": datetime.now(timezone.utc).isoformat(),
                    "archive_reason": "auto_cap",
                }
            },
        )

        logger.info(
            "✅ cap_visible_articles: "
            f"keep={keep}, keep_ids={len(keep_ids)}, protected={len(protected_ids)}"
        )
        return {
            "success": True,
            "keep": keep,
            "keep_ids": len(keep_ids),
            "protected": len(protected_ids),
        }
    except Exception as e:
        logger.error(f"cap_visible_articles error: {str(e)}")
        return {"success": False, "error": str(e)}

async def daily_article_generation(count: int = 12):
    """Generate new articles daily with fault tolerance and distributed locking"""
    try:
        # ============================================
        # DISTRIBUTED LOCK - Prevents duplicate article generation
        # Only ONE instance across ALL replicas should generate articles
        # ============================================
        now = datetime.now(timezone.utc)
        lock_key = f"article_gen_{now.strftime('%Y%m%d%H')}"
        
        # Try to acquire the lock; allow takeover if an old lock is stale
        try:
            await db.scheduler_locks.update_one(
                {"job": lock_key},
                {"$setOnInsert": {
                    "job": lock_key,
                    "locked": False,
                    "locked_at": None,
                    "instance_id": None,
                    "expires_at": None
                }},
                upsert=True
            )

            stale_before = now - timedelta(hours=2)

            lock_result = await db.scheduler_locks.find_one_and_update(
                {
                    "job": lock_key,
                    "$or": [
                        {"locked_at": None},
                        {"locked_at": {"$lt": stale_before}},
                        {"expires_at": {"$lt": now}}
                    ]
                },
                {"$set": {
                    "locked": True,
                    "locked_at": now,
                    "instance_id": os.environ.get('HOSTNAME', 'unknown'),
                    "expires_at": now + timedelta(hours=2)
                }},
                return_document=True
            )

            if lock_result is None:
                logger.info(f"⏭️ Another server is handling article generation, skipping...")
                return

            logger.info(f"✅ Acquired article generation lock: {lock_key}")
        except Exception as lock_error:
            logger.warning(f"Lock warning (continuing): {lock_error}")
        
        logger.info(f"Starting daily article generation (target: {count})...")
        
        # Generate new articles (5+ Cheshire, 3+ UK) with error handling
        try:
            # Request up to 12 candidates, but keep only 6 public; extras go to manual review.
            # Keeps quality/cost controlled while reducing homepage starvation from an overly thin public pool.
            await _generate_articles_internal(GenerateArticlesRequest(count=count, include_uk_news=True, public_import_limit=6))
        except Exception as gen_error:
            logger.error(f"Error during article generation (will retry): {str(gen_error)}")
            # Don't fail the entire job, just log and continue
            pass
        
        # AUTO-CLEANUP: Remove duplicates and short articles
        try:
            cleanup_result = await _remove_duplicates_internal()
            logger.info(f"Auto-cleanup after generation: removed {cleanup_result.get('total_removed', 0)} duplicates/short articles")
        except Exception as dup_error:
            logger.error(f"Error during duplicate removal: {str(dup_error)}")
            pass

        # Clean up old articles (independent of generation)
        # Automatic hard-delete cleanup disabled.
        # Old source publication dates can cause newly imported stories to be deleted.
        # Keep manual/admin cleanup only until a safer archive-based policy replaces this.
        
        logger.info("Daily article generation process completed")
        
        # Release the lock
        try:
            await db.scheduler_locks.delete_one({"job": lock_key})
        except Exception:
            pass
            
    except Exception as e:
        logger.error(f"Critical error in daily article generation: {str(e)}")

async def _select_rotating_email_batch(digest_key: str, unique_emails: list, send_cap: int):
    """
    Select a fair rotating email batch for capped newsletter sends.
    Reads a per-digest cursor from MongoDB; the cursor is saved after the send attempt.
    """
    if not unique_emails or send_cap <= 0:
        return [], 0, 0, 0

    stable_emails = sorted(
        [email for email in unique_emails if email],
        key=lambda value: str(value).lower()
    )

    total = len(stable_emails)
    capped = min(send_cap, total)

    cursor_doc = await db.email_batch_cursors.find_one({"digest_key": digest_key}) or {}
    start_index = int(cursor_doc.get("next_index") or 0)
    if start_index < 0 or start_index >= total:
        start_index = 0

    end_index = start_index + capped
    if end_index <= total:
        batch = stable_emails[start_index:end_index]
    else:
        batch = stable_emails[start_index:] + stable_emails[:end_index % total]

    next_index = (start_index + capped) % total

    return batch, start_index, next_index, total


async def _save_email_batch_cursor(digest_key: str, next_index: int, start_index: int, batch_size: int, total_eligible: int):
    """Persist the next newsletter batch cursor after a send attempt."""
    await db.email_batch_cursors.update_one(
        {"digest_key": digest_key},
        {"$set": {
            "digest_key": digest_key,
            "next_index": next_index,
            "last_start_index": start_index,
            "last_batch_size": batch_size,
            "total_eligible": total_eligible,
            "updated_at": datetime.now(timezone.utc)
        }},
        upsert=True
    )


async def _save_email_send_opportunities(
    digest_key: str,
    tracking_id: str,
    accepted_recipients: list,
    provider: str,
):
    """Store privacy-preserving recipient hashes for a successfully accepted newsletter send."""
    import hashlib

    recipient_hashes = []
    seen_hashes = set()

    for raw_email in accepted_recipients or []:
        email_norm = str(raw_email or "").strip().lower()
        if not email_norm or "@" not in email_norm:
            continue

        email_hash = hashlib.sha256(email_norm.encode()).hexdigest()[:8]
        if email_hash in seen_hashes:
            continue

        seen_hashes.add(email_hash)
        recipient_hashes.append(email_hash)

    if not tracking_id or not recipient_hashes:
        logger.warning(
            f"Email send ledger not written: digest={digest_key} "
            f"tracking_id_present={bool(tracking_id)} accepted_hashes={len(recipient_hashes)}"
        )
        return 0

    ledger_doc = {
        "digest_key": digest_key,
        "tracking_id": tracking_id,
        "provider": provider,
        "accepted_at": datetime.now(timezone.utc),
        "accepted_count": len(recipient_hashes),
        "recipient_hashes": recipient_hashes,
    }

    await db.email_send_opportunities.update_one(
        {"tracking_id": tracking_id},
        {"$set": ledger_doc},
        upsert=True,
    )

    logger.info(
        f"Email send ledger stored: digest={digest_key} "
        f"tracking={tracking_id} accepted={len(recipient_hashes)}"
    )
    return len(recipient_hashes)


async def send_scheduled_news_digest(digest_time: str = "DailyBrief"):
    """
    Send The Daily Brief to all subscribers with daily_brief preference.
    Called by scheduler for the Daily Brief newsletter.
    
    CRITICAL: Uses MongoDB unique index for atomic duplicate prevention.
    Only ONE server instance will successfully send the digest.
    """
    from datetime import timedelta
    
    try:
        now = datetime.now(timezone.utc)
        date_key = now.strftime('%Y%m%d')
        
        # ============================================
        # BULLETPROOF DUPLICATE PREVENTION
        # Step 1: Check if digest already exists for today
        # ============================================
        existing = await db.digest_log.find_one({
            "digest_time": digest_time,
            "date_key": date_key
        })
        
        if existing:
            existing_status = existing.get("status")
            existing_sent_at = existing.get("sent_at")
            existing_success_count = int(existing.get("success_count") or 0)

            if isinstance(existing_sent_at, datetime):
                if existing_sent_at.tzinfo is None:
                    existing_sent_at = existing_sent_at.replace(tzinfo=timezone.utc)
                existing_age_minutes = (now - existing_sent_at).total_seconds() / 60
            else:
                existing_age_minutes = 0

            stale_in_progress = (
                existing_status in ("claimed", "sending")
                and existing_success_count == 0
                and existing_age_minutes >= 90
            )

            if stale_in_progress:
                logger.warning(
                    f"♻️ Reclaiming stale {digest_time} digest lock for {date_key} "
                    f"(status={existing_status}, age={int(existing_age_minutes)}m, success_count=0)"
                )
                await db.digest_log.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {
                        "status": "failed",
                        "error": "Marked failed automatically because digest was stuck in claimed/sending state",
                        "failed_at": now,
                        "reclaimed_at": now
                    }}
                )
                await db.digest_log.delete_one({"_id": existing["_id"]})
            else:
                logger.info(f"⏭️ {digest_time} for {date_key} already exists (status: {existing_status}), skipping...")
                return
        
        # ============================================
        # Step 2: Try atomic insert - MongoDB unique index ensures only ONE wins
        # ============================================
        hostname = os.environ.get("HOSTNAME", "").strip()
        if not hostname or hostname.lower() == "unknown":
            logger.error(f"Refusing to claim {digest_time} digest lock for {date_key}: HOSTNAME is missing/unknown")
            return

        instance_id = f"{hostname}_{uuid4().hex[:8]}"
        
        try:
            result = await db.digest_log.insert_one({
                "digest_time": digest_time,
                "date_key": date_key,
                "sent_at": now,
                "status": "claimed",
                "instance_id": instance_id,
                "subscribers_count": 0,
                "success_count": 0
            })
            logger.info(f"✅ WON digest lock for {digest_time} ({date_key}) - instance: {instance_id}")
        except Exception as e:
            error_str = str(e).lower()
            if "duplicate key" in error_str or "e11000" in error_str:
                logger.info(f"⏭️ {digest_time} for {date_key} already claimed by another instance, skipping...")
                return
            else:
                logger.error(f"Unexpected error claiming digest: {e}")
                return
        
        # ============================================
        # Step 3: Double-verify we own the record before sending
        # ============================================
        our_record = await db.digest_log.find_one({
            "digest_time": digest_time,
            "date_key": date_key,
            "instance_id": instance_id
        })
        
        if not our_record:
            logger.warning(f"⏭️ Lost ownership of {digest_time} ({date_key}), aborting...")
            return
        
        # ============================================
        # Step 4: Update status to 'sending' before we send
        # ============================================
        await db.digest_log.update_one(
            {"digest_time": digest_time, "date_key": date_key, "instance_id": instance_id},
            {"$set": {"status": "sending"}}
        )
        
        logger.info(f"📧 Proceeding with {digest_time} news digest email send...")
        
        # Get active subscribers for Daily Brief.
        # Permanent fix: align scheduled recipient base with manual send,
        # while still excluding explicit Daily Brief opt-outs.
        subscribers = await db.subscribers.find(
            {
                "$and": [
                    {"$or": [{"active": True}, {"active": {"$exists": False}}]},
                    {"$or": [{"daily_brief": {"$ne": False}}, {"daily_brief": {"$exists": False}}]}
                ]
            },
            {
                "_id": 0,
                "email": 1,
                "priority_daily_brief": 1,
                "signup_source": 1,
                "subscriber_origin": 1
            }
        ).to_list(15000)
        if not subscribers:
            logger.info("No subscribers found with daily_brief preference - skipping")
            return
        
        # Deduplicate emails (case-insensitive), validate, and prioritise genuine website subscribers.
        import re
        email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        seen_emails = set()
        priority_emails = []
        rotating_emails = []
        invalid_emails = []
        
        for s in subscribers:
            email = s.get('email', '').lower().strip()
            if email and email not in seen_emails:
                # Validate email format
                if is_deliverable_newsletter_email(email):
                    seen_emails.add(email)
                    original_email = s.get('email')  # Keep original case
                    is_priority = (
                        s.get("priority_daily_brief") is True
                        or s.get("signup_source") == "website"
                        or s.get("subscriber_origin") == "organic_website"
                    )
                    if is_priority:
                        priority_emails.append(original_email)
                    else:
                        rotating_emails.append(original_email)
                else:
                    invalid_emails.append(email)
        
        if invalid_emails:
            logger.warning(f"Skipping {len(invalid_emails)} invalid emails: {invalid_emails[:5]}...")
        
        daily_send_cap = int(os.environ.get("DAILY_BRIEF_SEND_CAP", "1000"))
        priority_emails = sorted(priority_emails, key=lambda value: str(value).lower())
        remaining_cap = max(0, daily_send_cap - len(priority_emails))

        rotating_batch, batch_start, batch_next, rotating_total = await _select_rotating_email_batch(
            "DailyBrief",
            rotating_emails,
            remaining_cap
        )

        subscriber_emails = (priority_emails + rotating_batch)[:daily_send_cap]
        total_eligible = len(priority_emails) + rotating_total

        logger.info(
            f"Found {len(subscriber_emails)} Daily Brief subscribers "
            f"({len(priority_emails)} priority organic + {len(rotating_batch)} rotating imported) "
            f"from {total_eligible} eligible unique subscribers "
            f"(rotating_start={batch_start}, rotating_next={batch_next})"
        )

        # Persist planned cursor details before sending so an interrupted Render restart
        # can be repaired without guessing which subscriber batch was being processed.
        await db.digest_log.update_one(
            {"digest_time": digest_time, "date_key": date_key, "instance_id": instance_id},
            {"$set": {
                "planned_batch_start": batch_start,
                "planned_batch_next": batch_next,
                "planned_batch_size": len(subscriber_emails),
                "planned_total_eligible": total_eligible,
                "planned_cursor_recorded_at": datetime.now(timezone.utc)
            }}
        )
        
        # Get latest articles from the last 24 hours, then choose quality-first.
        # This prevents weak newest stories from crowding out better money/business/local-impact articles.
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        cutoff_time_iso = cutoff_time.isoformat()

        pipeline = [
            {"$match": {
                "archived": {"$ne": True},
                "manual_review_hidden_from_public": {"$ne": True},
                "$or": [
                    {"publishedDate": {"$gte": cutoff_time}},
                    {"publishedDate": {"$gte": cutoff_time_iso}}
                ]
            }},
            {"$sort": {"publishedDate": -1}},
            {"$group": {
                "_id": "$title",
                "mongo_id": {"$first": "$_id"},
                "custom_id": {"$first": "$id"},
                "title": {"$first": "$title"},
                "content": {"$first": "$content"},
                "category": {"$first": "$category"},
                "author": {"$first": "$author"},
                "image": {"$first": "$image"},
                "publishedDate": {"$first": "$publishedDate"},
                "source": {"$first": "$source"}
            }},
            {"$sort": {"publishedDate": -1}},
            {"$limit": 80}
        ]

        recent_articles = await db.articles.aggregate(pipeline).to_list(80)

        # If the 24h query returns nothing, fall back to latest unique articles so the digest does not fail.
        # This is a safety fallback only, not the default newsletter pool.
        if not recent_articles:
            logger.warning("No 24h articles found for Daily Brief; falling back to latest unique articles")
            fallback_pipeline = [
                {"$match": {
                    "archived": {"$ne": True},
                    "manual_review_hidden_from_public": {"$ne": True}
                }},
                {"$sort": {"publishedDate": -1}},
                {"$group": {
                    "_id": "$title",
                    "mongo_id": {"$first": "$_id"},
                    "custom_id": {"$first": "$id"},
                    "title": {"$first": "$title"},
                    "content": {"$first": "$content"},
                    "category": {"$first": "$category"},
                    "author": {"$first": "$author"},
                    "image": {"$first": "$image"},
                    "publishedDate": {"$first": "$publishedDate"},
                    "source": {"$first": "$source"}
                }},
                {"$sort": {"publishedDate": -1}},
                {"$limit": 20}
            ]
            recent_articles = await db.articles.aggregate(fallback_pipeline).to_list(20)

        for article in recent_articles:
            if article.get("mongo_id"):
                article["id"] = str(article["mongo_id"])
            elif article.get("custom_id"):
                article["id"] = str(article["custom_id"])
            article.pop("mongo_id", None)
            article.pop("custom_id", None)

        if not recent_articles:
            logger.warning("No articles available for digest")
            return

        def _term_match(blob: str, term: str) -> bool:
            term = str(term or "").lower().strip()
            if not term:
                return False
            if " " in term:
                return term in blob
            return re.search(rf"\b{re.escape(term)}\b", blob) is not None

        def _has_any(blob: str, terms: list) -> bool:
            return any(_term_match(blob, term) for term in terms)

        def get_title_keywords(title):
            """Extract key words from title for similarity checking."""
            stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'for', 'to', 'of', 'in', 'on', 'at', 'with', 'as', 'by', 'and', 'from', 'this', 'that', 'will'}
            words = str(title or "").lower().split()
            return set(w.strip(".,:;!?()[]'\"") for w in words if len(w.strip(".,:;!?()[]'\"")) > 3 and w not in stop_words)

        towns = [
            'cheshire', 'crewe', 'macclesfield', 'wilmslow', 'chester', 'warrington',
            'nantwich', 'congleton', 'northwich', 'knutsford', 'sandbach', 'middlewich',
            'alsager', 'winsford', 'ellesmere port'
        ]

        money_terms = [
            'mortgage', 'rent', 'council tax', 'tax', 'vat', 'savings', 'rates', 'bills',
            'energy', 'inflation', 'budget', 'cost', 'prices', 'wages', 'pay', 'pension',
            'retirement'
        ]

        business_terms = [
            'business', 'jobs', 'job', 'workforce', 'redundancy', 'investment', 'company',
            'startup', 'factory', 'employer', 'retail', 'hospitality', 'growth', 'market'
        ]

        property_terms = [
            'property', 'housing', 'house', 'home', 'planning', 'landlord', 'development'
        ]

        ai_terms = [
            'ai', 'artificial intelligence', 'chatgpt', 'openai', 'gemini', 'automation',
            'software', 'cyber', 'data centre', 'digital', 'cloud', 'startup', 'chip',
            'semiconductor', 'microsoft', 'google'
        ]

        weak_terms = [
            'celebrity', 'showbiz', 'gaming', 'xbox', 'playstation', 'nintendo',
            'sports', 'sport', 'football', 'tv', 'horror', 'dinosaur', 'squirrel',
            'osprey', 'museum', 'twins', 'different dads', 'underwater forests'
        ]

        crime_terms = [
            'police', 'court', 'jailed', 'assault', 'murder', 'stabbed', 'arrest',
            'crime', 'crash', 'live updates'
        ]

        def _article_blob(article):
            return " ".join([
                str(article.get("title") or ""),
                str(article.get("category") or ""),
                str(article.get("content") or "")[:700],
            ]).lower()

        def _is_banned(article):
            category = (article.get('category', '') or '').lower()
            blob = _article_blob(article)
            if category in ['sports', 'sport', 'entertainment', 'celebrity', 'showbiz']:
                return True
            return _has_any(blob, weak_terms)

        def _is_local(article):
            return _has_any(_article_blob(article), towns)

        def _is_business(article):
            return _has_any(_article_blob(article), money_terms + business_terms + property_terms)

        def _is_tech(article):
            blob = _article_blob(article)
            title = str(article.get("title") or "").lower()
            category = str(article.get("category") or "").lower()
            if _has_any(blob, weak_terms):
                return False
            return _has_any(category, ['ai', 'technology']) or _has_any(title, ai_terms)

        def _score_article(article):
            blob = _article_blob(article)
            title = str(article.get("title") or "")
            score = 0
            reasons = []

            if _is_local(article):
                score += 30
                reasons.append("local")
            if _has_any(blob, money_terms):
                score += 25
                reasons.append("money")
            if _has_any(blob, business_terms):
                score += 22
                reasons.append("business/jobs")
            if _has_any(blob, property_terms):
                score += 18
                reasons.append("property")
            if _is_tech(article):
                score += 18
                reasons.append("AI/tech")
            if _has_any(blob, ['save', 'savings', 'advice', 'retirement', 'job losses', 'cost of living', 'mortgage', 'council tax']):
                score += 18
                reasons.append("reader-impact")
            if any(ch.isdigit() for ch in title):
                score += 8
                reasons.append("number")
            if len(title) <= 95:
                score += 5
                reasons.append("clear-title")
            if _has_any(blob, crime_terms):
                score -= 35
                reasons.append("crime/live-update penalty")
            if _has_any(blob, weak_terms):
                score -= 40
                reasons.append("weak-topic penalty")

            return score, reasons

        # Enhanced deduplication - check for similar topics, not just exact titles.
        seen_titles = set()
        seen_keywords = []
        unique_candidates = []

        for article in recent_articles:
            title = article.get('title', '')
            title_normalized = title.lower().strip()[:50]
            title_keywords = get_title_keywords(title)

            if not title_normalized or title_normalized in seen_titles:
                continue

            is_similar = False
            for prev_keywords in seen_keywords:
                if title_keywords and prev_keywords:
                    overlap = len(title_keywords & prev_keywords)
                    similarity = overlap / min(len(title_keywords), len(prev_keywords))
                    if similarity > 0.5:
                        is_similar = True
                        break

            if not is_similar:
                seen_titles.add(title_normalized)
                seen_keywords.append(title_keywords)
                unique_candidates.append(article)

        scored_candidates = []
        rejected_count = 0

        for article in unique_candidates:
            score, reasons = _score_article(article)
            if _is_banned(article) or score < 30:
                rejected_count += 1
                continue
            scored_candidates.append((score, reasons, article))

        scored_candidates.sort(key=lambda item: item[0], reverse=True)

        # Quality-first Daily Brief:
        # one lead story + one supporting story + up to three related stories, only if genuinely useful.
        selected_articles = []
        seen_selected_titles = set()

        for score, reasons, article in scored_candidates:
            title_key = str(article.get("title") or "").strip().lower()
            if not title_key or title_key in seen_selected_titles:
                continue
            selected_articles.append(article)
            seen_selected_titles.add(title_key)
            if len(selected_articles) >= 5:
                break

        # If the quality threshold is too strict on a slow day, allow the strongest available candidates,
        # but never banned/weak topics.
        if len(selected_articles) < 2:
            for article in unique_candidates:
                if _is_banned(article):
                    continue
                title_key = str(article.get("title") or "").strip().lower()
                if not title_key or title_key in seen_selected_titles:
                    continue
                selected_articles.append(article)
                seen_selected_titles.add(title_key)
                if len(selected_articles) >= 2:
                    break

        unique_articles = selected_articles

        local_count = len([a for a in unique_articles if _is_local(a)])
        business_count = len([a for a in unique_articles if _is_business(a)])
        tech_count = len([a for a in unique_articles if _is_tech(a)])

        logger.info(f"Sending quality-first Daily Brief with {len(unique_articles)} articles (local={local_count}, business_or_money={business_count}, tech={tech_count}, rejected={rejected_count}) to {len(subscriber_emails)} subscribers")
        
        # Update status to "sending" with article count
        await db.digest_log.update_one(
            {"digest_time": digest_time, "date_key": date_key, "instance_id": instance_id},
            {"$set": {
                "status": "sending",
                "articles_count": len(unique_articles),
                "subscribers_count": len(subscriber_emails)
            }}
        )
        
        # Send the Daily Brief using new template
        success_count = email_service.send_daily_brief(
            to_emails=subscriber_emails,
            articles=unique_articles,
            weather=None,  # TODO: Integrate weather API
            travel=None,   # TODO: Integrate travel RSS
            photo_of_day=None  # TODO: Add community photo feature
        )
        
        # Handle tuple return (success_count, tracking_id)
        if isinstance(success_count, tuple):
            success_count, tracking_id = success_count
        else:
            tracking_id = None
        
        logger.info(f"✅ Daily Brief sent to {success_count}/{len(subscriber_emails)} subscribers")

        provider_name = "resend" if getattr(email_service, "resend_enabled", False) else "smtp"
        provider_error = None
        final_status = "sent"

        if int(success_count or 0) <= 0:
            final_status = "failed"
            provider_error = (
                getattr(email_service, "resend_last_error", None)
                or "Daily Brief email service returned zero successful sends"
            )
            logger.error(
                f"❌ Daily Brief provider failure: selected={len(subscriber_emails)} "
                f"success_count=0 provider={provider_name} error={provider_error}"
            )
        
        # Update our digest log record with final provider result
        await db.digest_log.update_one(
            {"digest_time": digest_time, "date_key": date_key, "instance_id": instance_id},
            {"$set": {
                "success_count": success_count,
                "tracking_id": tracking_id,
                "status": final_status,
                "provider": provider_name,
                "provider_error": provider_error,
                "resend_successful_chunks": getattr(email_service, "resend_last_successful_chunks", None),
                "resend_failed_chunks": getattr(email_service, "resend_last_failed_chunks", None),
                "completed_at": datetime.now(timezone.utc)
            }}
        )
        
        if success_count > 0:
            accepted_recipients = list(
                getattr(email_service, "last_accepted_recipients", []) or []
            )
            ledger_count = await _save_email_send_opportunities(
                "DailyBrief",
                tracking_id,
                accepted_recipients,
                provider_name,
            )
            if ledger_count != int(success_count or 0):
                logger.warning(
                    f"Daily Brief accepted-recipient mismatch: "
                    f"success_count={success_count} ledger_count={ledger_count}"
                )

            await _save_email_batch_cursor(
                "DailyBrief",
                batch_next,
                batch_start,
                len(subscriber_emails),
                total_eligible
            )
            logger.info(f"✅ Daily Brief batch cursor advanced to {batch_next}")
        else:
            logger.warning("Daily Brief batch cursor not advanced because success_count was 0")

        logger.info(f"✅ Digest log updated for {digest_time} ({date_key})")
        
    except Exception as e:
        logger.error(f"Error sending Daily Brief: {str(e)}")
        # Try to mark as failed so another instance doesn't retry
        try:
            await db.digest_log.update_one(
                {"digest_time": digest_time, "date_key": date_key},
                {"$set": {"status": "failed", "error": str(e)}}
            )
        except:
            pass


async def send_weekly_roundup_email(batch_slot: int = 1):
    """
    Send The Weekly Roundup to all subscribers with weekly_roundup preference.
    Called by scheduler in safe Sunday morning batches.
    """
    from datetime import timedelta
    
    try:
        now = datetime.now(timezone.utc)
        date_key = now.strftime('%Y%m%d')
        roundup_batch_slot = max(1, int(batch_slot or 1))
        
        # DISTRIBUTED LOCK - Same pattern as daily brief, but per Sunday batch slot.
        lock_key = f"weekly_roundup_{date_key}_batch_{roundup_batch_slot}"
        lock_id = str(uuid4())
        
        # Check if this specific Sunday batch slot was already sent.
        recent_digest = await db.digest_log.find_one({
            "date_key": date_key,
            "digest_time": "WeeklyRoundup",
            "weekly_roundup_batch_slot": roundup_batch_slot
        })
        
        if recent_digest:
            logger.info(f"⏭️ Weekly Roundup batch {roundup_batch_slot} already sent at {recent_digest.get('sent_at')}, skipping...")
            return
        
        # Acquire lock
        await db.scheduler_locks.update_one(
            {"job": lock_key},
            {"$setOnInsert": {"job": lock_key, "locked_at": None, "lock_id": None}},
            upsert=True
        )
        
        lock_result = await db.scheduler_locks.find_one_and_update(
            {
                "job": lock_key,
                "$or": [
                    {"locked_at": None},
                    {"locked_at": {"$lt": now - timedelta(minutes=30)}}
                ]
            },
            {"$set": {"locked_at": now, "lock_id": lock_id}},
            return_document=True
        )
        
        if lock_result is None or lock_result.get("lock_id") != lock_id:
            logger.info("⏭️ Another server acquired lock for Weekly Roundup, skipping...")
            return
        
        logger.info("📰 Proceeding with Weekly Roundup email send...")
        
        # Get active subscribers for Weekly Roundup.
        # Existing large list had weekly_roundup=False as a system default, not a manual opt-out.
        # Include default Daily Brief subscribers unless they later explicitly update preferences.
        subscribers = await db.subscribers.find(
            {
                "$and": [
                    {"$or": [{"active": True}, {"active": {"$exists": False}}]},
                    {"$or": [
                        {"weekly_roundup": True},
                        {"$and": [
                            {"daily_brief": True},
                            {"preferences_updated_at": {"$exists": False}}
                        ]}
                    ]}
                ]
            },
            {
                "_id": 0,
                "email": 1,
                "priority_daily_brief": 1,
                "signup_source": 1,
                "subscriber_origin": 1
            }
        ).to_list(15000)
        
        if not subscribers:
            logger.info("No subscribers found for Weekly Roundup - skipping")
            await db.scheduler_locks.delete_one({"job": lock_key})
            return
        
        import re
        email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        seen_emails = set()
        priority_emails = []
        rotating_emails = []

        for s in subscribers:
            email = (s.get('email') or '').lower().strip()
            if email and email not in seen_emails and is_deliverable_newsletter_email(email):
                seen_emails.add(email)
                original_email = s.get('email')
                is_priority = (
                    s.get("priority_daily_brief") is True
                    or s.get("signup_source") == "website"
                    or s.get("subscriber_origin") == "organic_website"
                )
                if is_priority:
                    priority_emails.append(original_email)
                else:
                    rotating_emails.append(original_email)

        weekly_send_cap = int(os.environ.get("WEEKLY_ROUNDUP_SEND_CAP", os.environ.get("DAILY_BRIEF_SEND_CAP", "1000")))
        priority_emails = sorted(priority_emails, key=lambda value: str(value).lower())
        remaining_cap = max(0, weekly_send_cap - len(priority_emails))

        # Weekly Roundup should go to organic subscribers plus recently engaged readers only.
        # Engagement is based on per-recipient tracking hash from Daily Brief / Weekly Roundup opens or clicks.
        import hashlib
        engagement_cutoff = datetime.now(timezone.utc) - timedelta(days=60)
        analytics_rows = await db.email_analytics.find(
            {"$or": [
                {"last_opened": {"$gte": engagement_cutoff}},
                {"last_clicked": {"$gte": engagement_cutoff}}
            ]},
            {"_id": 0, "tracking_id": 1, "opens": 1, "clicks": 1}
        ).to_list(50000)

        engaged_hashes = set()
        for row in analytics_rows:
            tracking_value = str(row.get("tracking_id") or "")
            suffix = tracking_value.rsplit("_", 1)[-1]
            if len(suffix) == 8 and ((row.get("opens") or 0) > 0 or (row.get("clicks") or 0) > 0):
                engaged_hashes.add(suffix)

        engaged_rotating_emails = []
        for email_value in rotating_emails:
            email_norm = str(email_value or "").lower().strip()
            email_hash = hashlib.sha256(email_norm.encode()).hexdigest()[:8]
            if email_hash in engaged_hashes:
                engaged_rotating_emails.append(email_value)

        # Multi-batch Sunday delivery: send engaged readers once per Sunday without wraparound.
        # Batch 1 includes organic subscribers; later batches continue the engaged list only.
        engaged_rotating_emails = sorted(engaged_rotating_emails, key=lambda value: str(value).lower())

        priority_for_this_batch = priority_emails if roundup_batch_slot == 1 else []
        priority_slots_used = len(priority_emails) if roundup_batch_slot > 1 else 0

        engaged_start = max(0, ((roundup_batch_slot - 1) * weekly_send_cap) - priority_slots_used)
        engaged_cap = max(0, weekly_send_cap - len(priority_for_this_batch))
        engaged_end = min(len(engaged_rotating_emails), engaged_start + engaged_cap)

        rotating_batch = engaged_rotating_emails[engaged_start:engaged_end]
        batch_start = engaged_start
        batch_next = engaged_end
        rotating_total = len(engaged_rotating_emails)

        subscriber_emails = (priority_for_this_batch + rotating_batch)[:weekly_send_cap]
        total_eligible = len(priority_emails) + rotating_total

        if not subscriber_emails:
            logger.info(
                f"⏭️ Weekly Roundup batch {roundup_batch_slot} has no remaining priority/engaged recipients "
                f"(engaged_pool={rotating_total}, engaged_start={engaged_start})"
            )
            await db.scheduler_locks.delete_one({"job": lock_key})
            return

        logger.info(
            f"Found {len(subscriber_emails)} Weekly Roundup subscribers for batch {roundup_batch_slot} "
            f"({len(priority_for_this_batch)} priority organic + {len(rotating_batch)} engaged) "
            f"from {total_eligible} priority/engaged eligible subscribers "
            f"(engaged_pool={len(engaged_rotating_emails)}, engaged_start={batch_start}, engaged_next={batch_next})"
        )
        
        # Get top performing articles from the past week (by view_count)
        one_week_ago = now - timedelta(days=7)
        
        # Get big read (most viewed article)
        big_read = await db.articles.find_one(
            {
                "archived": {"$ne": True},
                "manual_review_hidden_from_public": {"$ne": True},
                "$or": [
                    {"publishedDate": {"$gte": one_week_ago}},
                    {"publishedDate": {"$gte": one_week_ago.isoformat()}}
                ]
            },
            sort=[("view_count", -1)]
        )
        
        if not big_read:
            # Fallback to most recent public article
            big_read = await db.articles.find_one(
                {
                    "archived": {"$ne": True},
                    "manual_review_hidden_from_public": {"$ne": True}
                },
                sort=[("publishedDate", -1)]
            )
        
        if not big_read:
            logger.warning("No articles found for Weekly Roundup")
            await db.scheduler_locks.delete_one({"job": lock_key})
            return
        
        # Convert _id to id
        if big_read.get('_id'):
            big_read['id'] = str(big_read['_id'])
        
        # Get top 5 trending public articles (excluding big read)
        icymi_cursor = db.articles.find(
            {
                "archived": {"$ne": True},
                "manual_review_hidden_from_public": {"$ne": True},
                "$or": [
                    {"publishedDate": {"$gte": one_week_ago}},
                    {"publishedDate": {"$gte": one_week_ago.isoformat()}}
                ]
            },
            sort=[("view_count", -1)]
        ).limit(6)
        
        icymi_articles = []
        async for article in icymi_cursor:
            if str(article.get('_id')) != str(big_read.get('_id')):
                if is_digest_excluded(article):
                    continue
                if article.get('_id'):
                    article['id'] = str(article['_id'])
                icymi_articles.append(article)
                if len(icymi_articles) >= 5:
                    break
        
        # Send the Weekly Roundup
        success_count = email_service.send_weekly_roundup(
            to_emails=subscriber_emails,
            big_read=big_read,
            icymi_articles=icymi_articles,
            property_of_week=None,  # TODO: Add property integration
            food_review=None  # TODO: Add food review integration
        )
        
        # Handle tuple return (success_count, tracking_id)
        if isinstance(success_count, tuple):
            success_count, tracking_id = success_count
        else:
            tracking_id = None
        
        logger.info(f"✅ Weekly Roundup sent to {success_count}/{len(subscriber_emails)} subscribers")
        
        # Log the send
        try:
            await db.digest_log.insert_one({
                "sent_at": datetime.now(timezone.utc),
                "digest_time": "WeeklyRoundup",
                "date_key": date_key,
                "type": "WeeklyRoundup",
                "weekly_roundup_batch_slot": roundup_batch_slot,
                "weekly_roundup_batch_label": f"batch_{roundup_batch_slot}",
                "articles_count": 1 + len(icymi_articles),
                "subscribers_count": len(subscriber_emails),
                "success_count": success_count,
                "tracking_id": tracking_id  # For email analytics
            })
        except Exception as log_error:
            logger.warning(f"Could not log weekly roundup send: {log_error}")
        
        if success_count > 0:
            accepted_recipients = list(
                getattr(email_service, "last_accepted_recipients", []) or []
            )
            weekly_provider = (
                "resend"
                if getattr(email_service, "resend_enabled", False)
                else "smtp"
            )
            ledger_count = await _save_email_send_opportunities(
                "WeeklyRoundup",
                tracking_id,
                accepted_recipients,
                weekly_provider,
            )
            if ledger_count != int(success_count or 0):
                logger.warning(
                    f"Weekly Roundup accepted-recipient mismatch: "
                    f"success_count={success_count} ledger_count={ledger_count}"
                )

            await _save_email_batch_cursor(
                "WeeklyRoundup",
                batch_next,
                batch_start,
                len(subscriber_emails),
                total_eligible
            )
            logger.info(f"✅ Weekly Roundup batch cursor advanced to {batch_next}")
        else:
            logger.warning("Weekly Roundup batch cursor not advanced because success_count was 0")

        # Release lock
        await db.scheduler_locks.delete_one({"job": lock_key})
        
    except Exception as e:
        logger.error(f"Error sending Weekly Roundup: {str(e)}")


async def auto_fix_duplicate_images():
    """
    AUTOMATIC image cleanup that runs on startup.
    Ensures 100% unique images across all articles AND removes unverified images.
    - PRESERVES RSS images (from BBC, Guardian, Sky) - these are always correct
    - Replaces only stock images that are duplicates or banned
    """
    try:
        logger.info("Running automatic image cleanup and verification...")
        
        # Get all articles
        all_articles = await db.articles.find({}).to_list(1000)
        if not all_articles:
            logger.info("No articles found - skipping image cleanup")
            return
        
        # RSS image domains - ALWAYS preserve these (they're from original publishers)
        RSS_IMAGE_DOMAINS = ['ichef.bbci.co.uk', 'i.guim.co.uk', 'e3.365dm.com', 'media.guim.co.uk']
        
        def is_rss_image(url):
            """Check if image is from RSS feed (should never be replaced)"""
            if not url:
                return False
            return any(domain in url for domain in RSS_IMAGE_DOMAINS)
        
        # 1. First pass: Identify invalid images (not RSS AND (banned OR not in verified list))
        invalid_image_count = 0
        articles_with_invalid_images = []
        
        for article in all_articles:
            current_image = article.get('image')
            
            # SKIP RSS IMAGES - they're always correct
            if is_rss_image(current_image):
                continue
            
            # Check if stock image is banned
            is_banned = False
            if current_image:
                for banned in BANNED_IMAGES:
                    if banned in current_image:
                        is_banned = True
                        break
            
            # Only flag non-RSS images that are banned or not in verified list
            if current_image and (is_banned):
                articles_with_invalid_images.append(article)
        
        if articles_with_invalid_images:
            logger.info(f"Found {len(articles_with_invalid_images)} articles with banned/unverified stock images. Replacing...")
            
            # Get currently used VALID images (include RSS images as "used")
            used_images = set()
            for a in all_articles:
                img = a.get('image')
                if img:
                    if is_rss_image(img):
                        used_images.add(img)  # Count RSS images as used
                    elif img and not any(b in img for b in BANNED_IMAGES):
                        used_images.add(img)
            
            for article in articles_with_invalid_images:
                # Select a new VALID, UNIQUE image
                new_image = select_unique_image(article.get('category', 'Local News'), used_images, article.get('title', ''), article.get('content', ''))
                
                if new_image:
                    await db.articles.update_one(
                        {'_id': article['_id']},
                        {'$set': {'image': new_image}}
                    )
                    used_images.add(new_image)
                    # Update local article object for next pass
                    article['image'] = new_image 
                    invalid_image_count += 1
                else:
                    logger.warning(f"Could not find replacement image for article {article['_id']}")

            logger.info(f"✅ Replaced {invalid_image_count} unverified/newspaper images (RSS images preserved)")
            
            # Refresh all_articles after updates for duplicate check
            all_articles = await db.articles.find({}).to_list(1000)

        # 2. Second pass: Fix duplicates among valid images
        image_usage = {}
        for article in all_articles:
            image = article.get('image')
            if image:
                if image not in image_usage:
                    image_usage[image] = []
                image_usage[image].append(article['_id'])
        
        # Get articles that need new images (all duplicates except the first one)
        articles_needing_images = []
        for image, article_ids in image_usage.items():
            if len(article_ids) > 1:
                # Keep first article with this image, replace others
                for article_id in article_ids[1:]:
                    article = next(a for a in all_articles if a['_id'] == article_id)
                    articles_needing_images.append({
                        'id': article_id,
                        'category': article.get('category', 'Local News'),
                        'current_image': image,
                        'title': article.get('title', ''),
                        'content': article.get('content', '')
                    })
        
        if not articles_needing_images and invalid_image_count == 0:
            logger.info(f"✅ All {len(all_articles)} articles have unique, verified images - no cleanup needed")
            return
        
        if articles_needing_images:
            logger.warning(f"Found {len(articles_needing_images)} articles with duplicate images - fixing now...")
            
            # Get all currently used images
            used_images = {article.get('image') for article in all_articles if article.get('image')}
            
            # Fix each duplicate
            fixed_count = 0
            for article_info in articles_needing_images:
                # Select a new unique image
                new_image = select_unique_image(article_info['category'], used_images, article_info['title'], article_info['content'])
                
                if new_image:
                    await db.articles.update_one(
                        {'_id': article_info['id']},
                        {'$set': {'image': new_image}}
                    )
                    used_images.add(new_image)
                    fixed_count += 1
                    logger.info(f"Fixed duplicate: replaced {article_info['current_image'][-40:]} with {new_image[-40:]}")
                else:
                    logger.warning(f"Could not find unique image for article {article_info['id']}")
            
            logger.info(f"✅ Auto-fixed {fixed_count} duplicate images on startup")
        
    except Exception as e:
        logger.error(f"Error during auto duplicate image cleanup: {str(e)}")

async def auto_clean_duplicate_articles():
    """Automatically remove duplicate articles on startup"""
    try:
        articles = await db.articles.find({}).sort('publishedDate', -1).to_list(1000)
        
        seen_patterns = set()
        removed_count = 0
        
        for article in articles:
            title = article.get('title', '')
            words = title.split()[:5]
            pattern = ' '.join(words).lower()
            
            if pattern in seen_patterns:
                await db.articles.delete_one({'_id': article['_id']})
                removed_count += 1
            else:
                seen_patterns.add(pattern)
        
        if removed_count > 0:
            logger.info(f"✅ Auto-removed {removed_count} duplicate articles on startup")
        else:
            logger.info("✅ No duplicate articles to remove")
            
    except Exception as e:
        logger.error(f"Error during auto duplicate article cleanup: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Start scheduler and queue background tasks - fast startup for Kubernetes"""
    try:
        # ============================================
        # ENSURE UNIQUE INDEX ON SCHEDULER_LOCKS
        # This prevents race conditions for digest sends
        # ============================================
        try:
            await db.scheduler_locks.create_index("job", unique=True)
            logger.info("✅ Created unique index on scheduler_locks.job")
        except Exception as idx_error:
            if "already exists" in str(idx_error).lower():
                logger.info("✅ Unique index on scheduler_locks.job already exists")
            else:
                logger.warning(f"Could not create index: {idx_error}")
        
        # ============================================
        # CLEANUP DUPLICATE SCHEDULER LOCKS (fixes index creation)
        # ============================================
        try:
            # Find and remove duplicate scheduler locks
            pipeline = [
                {"$group": {"_id": "$job", "count": {"$sum": 1}, "docs": {"$push": "$_id"}}},
                {"$match": {"count": {"$gt": 1}}}
            ]
            duplicates = await db.scheduler_locks.aggregate(pipeline).to_list(100)
            for dup in duplicates:
                # Keep first, delete rest
                for doc_id in dup['docs'][1:]:
                    await db.scheduler_locks.delete_one({"_id": doc_id})
                logger.info(f"Cleaned up {len(dup['docs'])-1} duplicate scheduler_locks for job: {dup['_id']}")
        except Exception as cleanup_err:
            logger.warning(f"Could not cleanup scheduler_locks duplicates: {cleanup_err}")
        
        # ============================================
        # CLEANUP DUPLICATE DIGEST_LOG ENTRIES (fixes index creation & duplicate emails)
        # ============================================
        try:
            # Find duplicate digest_log entries (same digest_time + date_key)
            pipeline = [
                {"$match": {"digest_time": {"$ne": None}, "date_key": {"$ne": None}}},
                {"$group": {
                    "_id": {"digest_time": "$digest_time", "date_key": "$date_key"},
                    "count": {"$sum": 1},
                    "docs": {"$push": {"_id": "$_id", "sent_at": "$sent_at", "status": "$status"}}
                }},
                {"$match": {"count": {"$gt": 1}}}
            ]
            duplicates = await db.digest_log.aggregate(pipeline).to_list(100)
            
            for dup in duplicates:
                # Sort by sent_at to keep the earliest, or by status to keep 'sent'
                sorted_docs = sorted(dup['docs'], key=lambda x: (
                    0 if x.get('status') == 'sent' else 1,  # Prefer 'sent' status
                    x.get('sent_at') or datetime.min.replace(tzinfo=timezone.utc)  # Then earliest
                ))
                # Delete all except the first (best) one
                for doc in sorted_docs[1:]:
                    await db.digest_log.delete_one({"_id": doc['_id']})
                logger.info(f"Cleaned up {len(sorted_docs)-1} duplicate digest_log entries for {dup['_id']}")
        except Exception as cleanup_err:
            logger.warning(f"Could not cleanup digest_log duplicates: {cleanup_err}")
        
        # Also clean up entries with null digest_time or date_key (these block non-sparse index)
        try:
            null_count = await db.digest_log.count_documents({
                "$or": [
                    {"digest_time": None},
                    {"date_key": None},
                    {"digest_time": {"$exists": False}},
                    {"date_key": {"$exists": False}}
                ]
            })
            if null_count > 0:
                # Update old entries to have unique date_keys based on their _id
                async for doc in db.digest_log.find({
                    "$or": [
                        {"digest_time": None},
                        {"date_key": None},
                        {"digest_time": {"$exists": False}},
                        {"date_key": {"$exists": False}}
                    ]
                }):
                    new_digest_time = doc.get('digest_time') or doc.get('type') or 'Legacy'
                    new_date_key = f"legacy_{str(doc['_id'])}"
                    await db.digest_log.update_one(
                        {"_id": doc['_id']},
                        {"$set": {"digest_time": new_digest_time, "date_key": new_date_key}}
                    )
                logger.info(f"Fixed {null_count} digest_log entries with null fields")
        except Exception as null_fix_err:
            logger.warning(f"Could not fix null digest_log entries: {null_fix_err}")
        
        # ============================================
        # DROP OLD SPARSE INDEX AND CREATE NON-SPARSE INDEX
        # ============================================
        try:
            # First try to drop the old sparse index
            await db.digest_log.drop_index("digest_time_1_date_key_1")
            logger.info("Dropped old sparse digest_log index")
        except Exception as drop_err:
            # Index might not exist, that's fine
            if "not found" not in str(drop_err).lower():
                logger.info(f"Could not drop old index (may not exist): {drop_err}")
        
        # ============================================
        # ENSURE UNIQUE INDEX ON DIGEST_LOG
        # Prevents duplicate digests even if lock fails
        # ============================================
        try:
            # Create compound index: one digest per type per day (NOT sparse for better enforcement)
            await db.digest_log.create_index(
                [("digest_time", 1), ("date_key", 1)], 
                unique=True,
                sparse=False,  # Non-sparse for stronger enforcement
                background=True,
                name="digest_time_date_key_unique_v3"  # New name to avoid conflicts
            )
            logger.info("✅ Created unique index on digest_log (digest_time + date_key)")
        except Exception as idx_error:
            if "already exists" in str(idx_error).lower():
                logger.info("✅ Unique index on digest_log already exists")
            elif "duplicate key" in str(idx_error).lower():
                # If still failing due to duplicates, try with sparse=True as fallback
                logger.warning("Duplicates still exist, trying sparse index as fallback...")
                try:
                    await db.digest_log.create_index(
                        [("digest_time", 1), ("date_key", 1)], 
                        unique=True,
                        sparse=True,
                        background=True,
                        name="digest_time_date_key_unique_sparse"
                    )
                    logger.info("✅ Created sparse unique index on digest_log (fallback)")
                except Exception as sparse_err:
                    logger.warning(f"Could not create digest_log index (even sparse): {sparse_err}")
            else:
                logger.warning(f"Could not create digest_log index: {idx_error}")
        
        # ============================================
        # CREATE INDEX ON ADMIN_TOKENS FOR DISTRIBUTED AUTH
        # This allows multiple replicas to share tokens
        # ============================================
        try:
            await db.admin_tokens.create_index("token", unique=True)
            logger.info("✅ Created unique index on admin_tokens.token")
        except Exception as idx_error:
            if "already exists" in str(idx_error).lower():
                logger.info("✅ Unique index on admin_tokens.token already exists")
            else:
                logger.warning(f"Could not create admin_tokens index: {idx_error}")
        
        # ============================================
        # CREATE UNIQUE INDEX ON ARTICLE TITLES
        # Prevents duplicate articles at database level
        # ============================================
        try:
            # Create a text index with unique partial filter (ignores empty titles)
            await db.articles.create_index(
                [("title", 1)],
                unique=True,
                partialFilterExpression={"title": {"$exists": True, "$ne": ""}}
            )
            logger.info("✅ Created unique index on articles.title")

            # Create unique index on source_url for proper deduplication
            try:
                await db.articles.create_index("source_url", unique=True)
                logger.info("✅ Created unique index on articles.source_url")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info("✅ Unique index on articles.source_url already exists")
                else:
                    logger.warning(f"Could not create source_url index: {e}")
        except Exception as idx_error:
            if "already exists" in str(idx_error).lower() or "index" in str(idx_error).lower():
                logger.info("✅ Unique index on articles.title already exists")
            else:
                logger.warning(f"Could not create articles.title index: {idx_error}")
        
        # Start scheduler FIRST so server can accept requests immediately
        # All heavy operations run in background tasks
        
        # 1. Startup duplicate hard-delete cleanup DISABLED.
        # It was removing legitimate recent articles using only the first 5 words of title.
        # asyncio.create_task(auto_clean_duplicate_articles())
        
        # 2. Queue content freshness check as background task (non-blocking)
        async def check_and_generate():
            """Background task to check content freshness and generate if needed"""
            try:
                count = await db.articles.count_documents({})
                
                if count == 0:
                    logger.info("Database is empty. Generating initial articles...")
                    await daily_article_generation(count=12)
                else:
                    # Check age of latest article
                    latest = await db.articles.find_one(sort=[("publishedDate", -1)])
                    if latest:
                        pub_date_str = latest.get('publishedDate')
                        if pub_date_str:
                            try:
                                if isinstance(pub_date_str, datetime):
                                    pub_date = pub_date_str
                                    if pub_date.tzinfo is None:
                                        pub_date = pub_date.replace(tzinfo=timezone.utc)
                                else:
                                    pub_date_str = str(pub_date_str).replace('Z', '+00:00')
                                    if '+' not in pub_date_str and 'T' in pub_date_str:
                                        pub_date_str = pub_date_str + '+00:00'
                                    pub_date = datetime.fromisoformat(pub_date_str)
                                    if pub_date.tzinfo is None:
                                        pub_date = pub_date.replace(tzinfo=timezone.utc)
                                
                                if (datetime.now(timezone.utc) - pub_date).total_seconds() > (4 * 3600):
                                    logger.info(f"Latest article is from {pub_date}, generating fresh content...")
                                    await daily_article_generation(count=12)
                                else:
                                    logger.info(f"Content is fresh (latest: {pub_date}). Skipping startup generation.")
                            except Exception as e:
                                logger.warning(f"Could not parse date {pub_date_str}: {e}")
            except Exception as e:
                logger.error(f"Background content check failed: {e}")
        
        # Startup generation disabled to prevent deploy-triggered content mutation\n        # asyncio.create_task(check_and_generate())
        
        # 3. Start Scheduler
        scheduler.add_job(
            daily_article_generation,
            CronTrigger(hour=6, minute=0, timezone=ZoneInfo("Europe/London")),  # Morning: 6:00 AM
            id='morning_article_generation',
            name='Generate morning news articles',
            replace_existing=True,
            args=[12]
        )
        
        scheduler.add_job(
            daily_article_generation,
            CronTrigger(hour=12, minute=0, timezone=ZoneInfo("Europe/London")),  # Midday: 12:00 PM
            id='midday_article_generation',
            name='Generate midday news articles',
            replace_existing=True,
            args=[12]
        )
        
        scheduler.add_job(
            daily_article_generation,
            CronTrigger(hour=18, minute=0, timezone=ZoneInfo("Europe/London")),  # Evening: 6:00 PM
            id='evening_article_generation',
            name='Generate evening news articles',
            replace_existing=True,
            args=[12]
        )
        
        # ============================================
        # EMAIL DIGEST SCHEDULE (Updated January 2026)
        # New tiered email strategy: Daily Brief plus Sunday morning Weekly Roundup batches
        # Breaking News Alerts are manual only
        # ============================================
        
        # The Daily Brief - Monday to Saturday at 07:30 AM
        scheduler.add_job(
            send_scheduled_news_digest,
            CronTrigger(day_of_week='mon-sat', hour=7, minute=30, timezone=ZoneInfo("Europe/London")),
            id='daily_brief',
            name='Send The Daily Brief (Mon-Sat 07:30 AM)',
            replace_existing=True,
            kwargs={'digest_time': 'DailyBrief'}
        )
        
        # The Weekly Roundup - Every Sunday in safe engaged-recipient batches.
        # Batch 1 includes organic website subscribers, then engaged readers.
        # Later batches continue the engaged reader list without wraparound.
        for roundup_hour, roundup_batch_slot in [(9, 1), (10, 2), (11, 3), (12, 4)]:
            scheduler.add_job(
                send_weekly_roundup_email,
                CronTrigger(day_of_week='sun', hour=roundup_hour, minute=0, timezone=ZoneInfo("Europe/London")),
                id=f'weekly_roundup_batch_{roundup_batch_slot}',
                name=f'Send The Weekly Roundup batch {roundup_batch_slot} (Sunday {roundup_hour:02d}:00)',
                replace_existing=True,
                kwargs={'batch_slot': roundup_batch_slot}
            )
        
        # OLD SCHEDULE DISABLED - Keeping commented for reference
        # scheduler.add_job(send_scheduled_news_digest, CronTrigger(hour=6, minute=15), id='morning_news_digest', ...)
        # scheduler.add_job(send_scheduled_news_digest, CronTrigger(hour=12, minute=15), id='midday_news_digest', ...)
        # scheduler.add_job(send_scheduled_news_digest, CronTrigger(hour=18, minute=15), id='evening_news_digest', ...)
        
        logger.info("📬 Email schedule: Daily Brief at 07:30, Weekly Roundup Sunday batches at 09:00, 10:00, 11:00, 12:00")
        
        # ============================================
        # FACEBOOK AUTO-POSTING JOBS (UK Peak Times)
        # ============================================
        
        async def scheduled_facebook_post():
            """Post 3 latest articles to Facebook (avoiding duplicates with 24-hour window)"""
            try:
                if not facebook_service.is_configured:
                    logger.info("Facebook not configured - skipping scheduled post")
                    return
                
                # COOLDOWN CHECK: Skip if we posted in the last 30 minutes
                # This prevents duplicate posts even if lock fails
                now = datetime.now(timezone.utc)
                thirty_minutes_ago = now - timedelta(minutes=30)
                recent_post = await db.facebook_post_log.find_one({
                    "posted_at": {"$gte": thirty_minutes_ago}
                })
                
                if recent_post:
                    logger.info(f"📘 Facebook cooldown active - last post was within 30 minutes. Skipping...")
                    return
                
                # ROBUST DISTRIBUTED LOCK for MongoDB
                # Uses findOneAndUpdate with strict filter to ensure only ONE winner
                five_minutes_ago = now - timedelta(minutes=5)
                lock_id = str(uuid4())  # Unique ID for this lock attempt
                
                # CRITICAL: Use findOneAndUpdate with return_document=AFTER
                # The filter ONLY matches if:
                # 1. Document has our specific job name AND
                # 2. Lock is either missing, null, or stale (>5 min old)
                # 
                # With upsert=False, this ONLY updates existing documents
                # We first ensure the document exists, then try to claim it
                
                # Ensure lock document exists (idempotent)
                await db.scheduler_locks.update_one(
                    {"job": "facebook_post"},
                    {"$setOnInsert": {"job": "facebook_post", "locked_at": None, "lock_id": None}},
                    upsert=True
                )
                
                # Now atomically try to claim the lock
                # This query will only match if lock is available (None or stale)
                lock_result = await db.scheduler_locks.find_one_and_update(
                    {
                        "job": "facebook_post",
                        "$or": [
                            {"locked_at": None},
                            {"locked_at": {"$lt": five_minutes_ago}}
                        ]
                    },
                    {"$set": {"locked_at": now, "lock_id": lock_id}},
                    return_document=True  # Return the updated document
                )
                
                # If lock_result is None, the lock was already held by another process
                if lock_result is None:
                    logger.info("📘 Facebook post already in progress (lock held by another process), skipping...")
                    return
                
                # Double-check that OUR lock_id is set (paranoid check)
                if lock_result.get("lock_id") != lock_id:
                    logger.info("📘 Facebook post lock mismatch - race condition detected, skipping...")
                    return
                
                logger.info(f"📘 Lock acquired (ID: {lock_id[:8]}...) - proceeding with Facebook post")
                
                # Use 24-hour sliding window (not just "today") to prevent duplicates at day boundaries
                window_start = datetime.now(timezone.utc) - timedelta(hours=24)
                recently_posted = await db.facebook_post_log.find({
                    "posted_at": {"$gte": window_start}
                }).to_list(100)
                
                # Track both article_id AND title patterns to catch duplicates
                posted_article_ids = set(p.get('article_id') for p in recently_posted if p.get('article_id'))
                posted_title_patterns = set()
                for p in recently_posted:
                    title = p.get('title', '')
                    if title:
                        # Create a pattern from first 5 significant words
                        words = [w.lower() for w in title.split() if len(w) > 3][:5]
                        posted_title_patterns.add(' '.join(sorted(words)))
                
                logger.info(f"📘 Articles posted in last 24h: {len(posted_article_ids)} IDs, {len(posted_title_patterns)} title patterns")
                
                # Get latest articles, excluding those already posted
                all_articles = await db.articles.find(
                    {},
                    {"_id": 1, "id": 1, "title": 1, "content": 1, "image": 1, "source": 1, "source_url": 1, "category": 1}
                ).sort("publishedDate", -1).limit(30).to_list(30)
                
                # Filter out already posted articles (by ID and by similar title)
                articles = []
                for article in all_articles:
                    article_id = str(article['_id'])
                    title = article.get('title', '')
                    
                    # Skip if article ID was already posted
                    if article_id in posted_article_ids:
                        logger.debug(f"Skipping already posted article (by ID): {title[:40]}...")
                        continue
                    
                    # Skip if similar title was already posted (duplicate detection)
                    words = [w.lower() for w in title.split() if len(w) > 3][:5]
                    title_pattern = ' '.join(sorted(words))
                    if title_pattern in posted_title_patterns:
                        logger.info(f"Skipping duplicate article (by title): {title[:40]}...")
                        continue
                    
                    # Add to post queue
                    article['id'] = article_id
                    del article['_id']
                    articles.append(article)
                    
                    # Also add to posted patterns to prevent duplicates within this batch
                    posted_title_patterns.add(title_pattern)
                    
                    if len(articles) >= 3:
                        break
                
                if not articles:
                    logger.warning("No new articles to post to Facebook (all recent articles already posted)")
                    # Release lock
                    await db.scheduler_locks.delete_one({"job": "facebook_post"})
                    return
                
                logger.info(f"📘 Posting {len(articles)} new articles to Facebook")
                
                result = await facebook_service.post_multiple_articles(articles, limit=3)
                
                # Log posted articles to prevent future duplicates
                for article in articles[:result.get('posted', 0)]:
                    await db.facebook_post_log.insert_one({
                        "article_id": article.get('id'),
                        "title": article.get('title', '')[:100],
                        "posted_at": datetime.now(timezone.utc)
                    })
                
                logger.info(f"📘 Scheduled Facebook post: {result.get('posted', 0)}/{len(articles)} articles posted successfully")
                
                # Release lock
                await db.scheduler_locks.delete_one({"job": "facebook_post"})
                
            except Exception as e:
                logger.error(f"Error in scheduled Facebook post: {str(e)}")
                # Release lock on error
                try:
                    await db.scheduler_locks.delete_one({"job": "facebook_post"})
                except:
                    pass
        
        # ============================================
        # FACEBOOK AUTO-POSTING - DISABLED
        # User requested manual posting only
        # Manual posting still available via Admin Dashboard buttons
        # ============================================
        
        # # Morning post: 8:00 AM UK
        # scheduler.add_job(
        #     scheduled_facebook_post,
        #     CronTrigger(hour=8, minute=0),
        #     id='facebook_morning_post',
        #     name='Facebook morning post (8 AM)',
        #     replace_existing=True
        # )
        # 
        # # Lunch post: 1:00 PM UK
        # scheduler.add_job(
        #     scheduled_facebook_post,
        #     CronTrigger(hour=13, minute=0),
        #     id='facebook_lunch_post',
        #     name='Facebook lunch post (1 PM)',
        #     replace_existing=True
        # )
        # 
        # # Evening post: 7:00 PM UK
        # scheduler.add_job(
        #     scheduled_facebook_post,
        #     CronTrigger(hour=19, minute=0),
        #     id='facebook_evening_post',
        #     name='Facebook evening post (7 PM)',
        #     replace_existing=True
        # )
        
        logger.info("📘 Facebook auto-posting DISABLED - use manual buttons in Admin Dashboard")
        
        # ============================================
        # TWITTER/X SCHEDULED POSTS - DISABLED
        # User requested manual posting only
        # ============================================
        
        async def scheduled_twitter_post():
            """Post 3 latest articles to Twitter (avoiding duplicates with 24-hour window)"""
            try:
                if not twitter_service.is_configured:
                    logger.info("Twitter not configured - skipping scheduled post")
                    return
                
                # Use lock to prevent concurrent posts
                now = datetime.now(timezone.utc)
                five_minutes_ago = now - timedelta(minutes=5)
                lock_id = str(uuid4())
                
                await db.scheduler_locks.update_one(
                    {"job": "twitter_post"},
                    {"$setOnInsert": {"job": "twitter_post", "locked_at": None, "lock_id": None}},
                    upsert=True
                )
                
                lock_result = await db.scheduler_locks.find_one_and_update(
                    {
                        "job": "twitter_post",
                        "$or": [
                            {"locked_at": None},
                            {"locked_at": {"$lt": five_minutes_ago}}
                        ]
                    },
                    {"$set": {"locked_at": now, "lock_id": lock_id}},
                    return_document=True
                )
                
                if lock_result is None or lock_result.get("lock_id") != lock_id:
                    logger.info("🐦 Twitter post already in progress (locked), skipping...")
                    return
                
                logger.info(f"🐦 Twitter lock acquired - proceeding with post")
                
                try:
                    # Get articles not posted in last 24 hours
                    window_start = datetime.now(timezone.utc) - timedelta(hours=24)
                    recently_posted = await db.twitter_post_log.find({
                        "posted_at": {"$gte": window_start}
                    }).to_list(100)
                    
                    posted_article_ids = set(p.get('article_id') for p in recently_posted)
                    
                    # Get recent articles
                    all_articles = await db.articles.find(
                        {},
                        {"_id": 1, "title": 1, "content": 1, "category": 1, "image": 1}
                    ).sort("publishedDate", -1).limit(30).to_list(30)
                    
                    articles = []
                    for article in all_articles:
                        article_id = str(article['_id'])
                        if article_id not in posted_article_ids:
                            article['id'] = article_id
                            del article['_id']
                            articles.append(article)
                            if len(articles) >= 1:  # Only 1 article per scheduled post (Free tier: 500/month limit)
                                break
                    
                    if not articles:
                        logger.info("🐦 No new articles to post to Twitter")
                        await db.scheduler_locks.delete_one({"job": "twitter_post"})
                        return
                    
                    result = await twitter_service.post_multiple_articles(articles, limit=1)  # 1 article per post
                    
                    # Log posted articles
                    for i, article in enumerate(articles[:result.get('posted', 0)]):
                        if result.get('results') and i < len(result['results']):
                            tweet_result = result['results'][i]
                            if tweet_result.get('success'):
                                await db.twitter_post_log.insert_one({
                                    "article_id": article.get('id'),
                                    "tweet_id": tweet_result.get('tweet_id'),
                                    "title": article.get('title', '')[:100],
                                    "posted_at": datetime.now(timezone.utc)
                                })
                    
                    logger.info(f"🐦 Twitter scheduled post complete: {result.get('posted', 0)} articles posted")
                    await db.scheduler_locks.delete_one({"job": "twitter_post"})
                    
                except Exception as e:
                    await db.scheduler_locks.delete_one({"job": "twitter_post"})
                    raise e
                    
            except Exception as e:
                logger.error(f"❌ Twitter scheduled post error: {str(e)}")
        
        # ============================================
        # TWITTER AUTO-POSTING - DISABLED
        # User requested manual posting only
        # Manual posting still available via Admin Dashboard buttons
        # ============================================
        
        # # Twitter morning post: 8:15 AM UK (15 min after Facebook)
        # scheduler.add_job(
        #     scheduled_twitter_post,
        #     CronTrigger(hour=8, minute=15),
        #     id='twitter_morning_post',
        #     name='Twitter morning post (8:15 AM)',
        #     replace_existing=True
        # )
        # 
        # # Twitter afternoon post: 1:15 PM UK
        # scheduler.add_job(
        #     scheduled_twitter_post,
        #     CronTrigger(hour=13, minute=15),
        #     id='twitter_afternoon_post',
        #     name='Twitter afternoon post (1:15 PM)',
        #     replace_existing=True
        # )
        # 
        # # Twitter evening post: 7:15 PM UK
        # scheduler.add_job(
        #     scheduled_twitter_post,
        #     CronTrigger(hour=19, minute=15),
        #     id='twitter_evening_post',
        #     name='Twitter evening post (7:15 PM)',
        #     replace_existing=True
        # )
        
        logger.info("🐦 Twitter auto-posting DISABLED - use manual buttons in Admin Dashboard")
        
        # ============================================
        # USER-SCHEDULED FACEBOOK POST CHECKER
        # Checks every 5 minutes for posts that are due
        # ============================================
        
        async def process_user_scheduled_posts():
            """Check for and process user-scheduled Facebook posts that are due"""
            try:
                if not facebook_service.is_configured:
                    return
                
                now = datetime.now(timezone.utc)
                
                # Find pending posts that are due (scheduled_time <= now)
                due_posts = await db.scheduled_facebook_posts.find({
                    "status": "pending",
                    "scheduled_time": {"$lte": now}
                }).to_list(10)
                
                if not due_posts:
                    return
                
                logger.info(f"📅 Processing {len(due_posts)} user-scheduled Facebook posts...")
                
                for post in due_posts:
                    try:
                        article_id = post.get("article_id")
                        result = await facebook_service.post_single_article_by_id(db, article_id)
                        
                        if result.get("success"):
                            await db.scheduled_facebook_posts.update_one(
                                {"_id": post["_id"]},
                                {"$set": {
                                    "status": "posted",
                                    "post_id": result.get("post_id"),
                                    "posted_at": datetime.now(timezone.utc)
                                }}
                            )
                            logger.info(f"✅ Posted scheduled article: {post.get('article_title', '')[:40]}...")
                        else:
                            await db.scheduled_facebook_posts.update_one(
                                {"_id": post["_id"]},
                                {"$set": {
                                    "status": "failed",
                                    "error": result.get("error", "Unknown error")
                                }}
                            )
                            logger.error(f"❌ Failed to post scheduled article: {result.get('error')}")
                            
                    except Exception as e:
                        await db.scheduled_facebook_posts.update_one(
                            {"_id": post["_id"]},
                            {"$set": {"status": "failed", "error": str(e)}}
                        )
                        logger.error(f"Error processing scheduled post: {str(e)}")
                        
            except Exception as e:
                logger.error(f"Error in process_user_scheduled_posts: {str(e)}")
        
        # Scheduled Facebook queue processor disabled to remove unused background polling.
        
        auto_enabled = os.getenv("AUTO_GENERATION_ENABLED", "false").strip().lower() in ("1","true","yes","on")
        scheduler_hostname = os.environ.get("HOSTNAME", "").strip()

        # Safety guard: only a real Render/runtime hostname may run scheduled jobs.
        # This prevents local/unknown duplicate processes from winning digest locks
        # and attempting Resend sends with stale or invalid environment variables.
        scheduler_host_valid = bool(scheduler_hostname) and scheduler_hostname.lower() != "unknown"

        if auto_enabled and scheduler_host_valid:
            scheduler.start()
            logger.info(f"AUTO_GENERATION_ENABLED=true and HOSTNAME={scheduler_hostname} → Scheduler started")
        elif auto_enabled:
            logger.warning("AUTO_GENERATION_ENABLED=true but HOSTNAME is missing/unknown → Scheduler NOT started")
        else:
            logger.info("AUTO_GENERATION_ENABLED is false → Scheduler NOT started")
        logger.info("Scheduler configured. Articles: 6AM, 12PM, 6PM. Digests: Daily Brief 7:30AM, Weekly Roundup Sunday batches 9AM-12PM. Facebook: MANUAL ONLY. Twitter: MANUAL ONLY.")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")

@app.on_event("shutdown")
async def shutdown_db_client():
    try:
        scheduler.shutdown()
    except Exception:
        pass
    client.close()

# ============================================
# ADMIN FEATURE FLAGS (UI SAFETY GATES)
# ============================================

@api_router.get("/admin/feature-flags")
async def get_admin_feature_flags(auth: bool = Depends(get_admin_auth)):
    """
    Returns backend feature flags so Admin UI can safely enable/disable
    dangerous operations (Archive & Refresh, etc.)
    """
    return {
        "enable_clear_refresh": os.environ.get("ENABLE_CLEAR_REFRESH") == "1",
        "smtp_enabled": os.environ.get("SMTP_ENABLED") in ["1", "true", "True"],
        "auto_generation_enabled": os.environ.get("AUTO_GENERATION_ENABLED") in ["1", "true", "True"],
        "environment": os.environ.get("ENVIRONMENT", "local")
    }
