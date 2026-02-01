from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import re
import logging
import secrets
import hashlib
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from openai import OpenAI
import random
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
from app import rss_routes

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')
LOCAL_DEV_NO_DB = os.getenv("LOCAL_DEV_NO_DB") == "1"
# Import services AFTER loading environment variables
from app.email_service import email_service
from app.unsplash_service import unsplash_service
from app.pexels_service import pexels_service
from app.pixabay_service import pixabay_service
from app.news_feed_service import news_feed_service
from app.perplexity_service import perplexity_service

# Stripe integration for paid job listings
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY', 'sk_test_emergent')

# Job posting pricing packages (amounts in GBP)
JOB_POSTING_PACKAGES = {
    "free": {"price": 0, "name": "Free Listing", "duration_days": 14, "featured": False},
    "standard": {"price": 15.00, "name": "Standard Listing", "duration_days": 30, "featured": False},
    "featured": {"price": 29.00, "name": "Featured Listing", "duration_days": 30, "featured": True},
    "premium": {"price": 49.00, "name": "Premium Listing", "duration_days": 60, "featured": True}
}

# MongoDB connection

if LOCAL_DEV_NO_DB:
    db = None
else:
    mongo_url = os.environ["MONGO_URL"]
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ["DB_NAME"]]
# -------------------------------
# LOCAL DEV: in-memory articles
# -------------------------------
LOCAL_DEV_ARTICLES = []

def seed_local_articles_if_needed():
    """Seed mock articles for local dev when no DB is available."""
    if LOCAL_DEV_ARTICLES:
        return
    from uuid import uuid4
    from datetime import datetime, timezone
    categories = ["Local News", "UK News", "Business", "Tech", "Health", "Science", "Entertainment", "Sports"]
    locations = [
        "chester",
        "warrington",
        "crewe",
        "nantwich",
        "macclesfield",
        "congleton",
        "northwich",
        "winsford",
        "wilmslow",
        "knutsford",
        "ellesmere-port"
    ]
    for i in range(20):
        LOCAL_DEV_ARTICLES.append({
            "id": str(uuid4()),
            "title": f"Mock article {i+1}",
            "content": "Mock content for local development.",
            "summary": "Mock summary.",
            "category": categories[i % len(categories)],
            "author": "Cheshire Today (Mock)",
            "publishedDate": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "image": "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=1200&q=60&fit=crop&auto=format",
            "tags": ["mock", "cheshire"],
            "featured": i < 3,
            "source": "Mock Feed",
            "source_url": "",
            "scope": "cheshire",
            "location": locations[i % len(locations)],
            "is_local_source": True,
        })
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
        # Use async DB check for distributed token verification
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

class GenerateArticlesResponse(BaseModel):
    success: bool
    generated: int
    cheshire_articles: int
    uk_articles: int

class SubscribeRequest(BaseModel):
    email: EmailStr
    preferences: Optional[dict] = None  # Newsletter preferences

class SubscribeResponse(BaseModel):
    success: bool
    message: str

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

class NewsletterPreferences(BaseModel):
    categories: List[str] = []  # Categories user wants: Local News, Sports, etc.
    frequency: str = "daily"  # daily, weekly, breaking_only
    
class UpdatePreferencesRequest(BaseModel):
    email: EmailStr
    preferences: NewsletterPreferences

class PreferencesUpdateRequest(BaseModel):
    """Request model for updating email tier preferences (daily brief, weekly, breaking news)"""
    email: str
    daily_brief: bool = True
    weekly_roundup: bool = False
    breaking_news: bool = False

class UnsubscribeRequest(BaseModel):
    """Request model for unsubscribe endpoint"""
    email: str

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
    content: str
    category: str
    image: Optional[str] = None
    author: Optional[str] = "Cheshire Today"
    tags: Optional[List[str]] = []
    featured: Optional[bool] = False
    scope: Optional[str] = "cheshire"

# Store for email verification codes (in production, use Redis with TTL)
email_verification_codes = {}

# =====================================================================================
# UK-ONLY IMAGE LIBRARY - CHESHIRE & UK SCENES ONLY
# NO NEWSPAPER IMAGES, NO GENERIC STOCK PHOTOS
# All images must be authentic UK locations matching article content
# =====================================================================================

# CHESHIRE LOCATION-SPECIFIC IMAGES 
LOCATION_IMAGES = {
    'knutsford': [
        'https://images.unsplash.com/photo-1591027590129-4de51a2fb3f6?w=800&h=500&fit=crop',  # English market town cobbles
        'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&h=500&fit=crop',  # English high street shops
    ],
    'wilmslow': [
        'https://images.unsplash.com/photo-1587474260584-136574528ed5?w=800&h=500&fit=crop',  # English town center
        'https://images.unsplash.com/photo-1565008576549-57569a49371d?w=800&h=500&fit=crop',  # UK town street
    ],
    'alderley': [
        'https://images.unsplash.com/photo-1588152850700-c82ecb8ba9b1?w=800&h=500&fit=crop',  # English countryside woodland
        'https://images.unsplash.com/photo-1566159196936-b4f3dc52dbfc?w=800&h=500&fit=crop',  # British countryside path
    ],
    'prestbury': [
        'https://images.unsplash.com/photo-1670620800086-3b9a345967fc?w=800&h=500&fit=crop',  # Cotswolds stone buildings
        'https://images.unsplash.com/photo-1670620800060-b90889e9f7d9?w=800&h=500&fit=crop',  # English village street
    ],
    'chester': [
        'https://images.unsplash.com/photo-1590058175032-5e68d70e3e2b?w=800&h=500&fit=crop',  # UK stone bridge historic
        'https://images.unsplash.com/photo-1567610018053-7f1b5c2d7f01?w=800&h=500&fit=crop',  # English town square
    ],
    'macclesfield': [
        'https://images.unsplash.com/photo-1763238638505-76f22e816560?w=800&h=500&fit=crop',  # English market town
        'https://images.unsplash.com/photo-1696113073939-213d3d9610b1?w=800&h=500&fit=crop',  # UK village scene
    ],
    'golden triangle': [
        'https://images.unsplash.com/photo-1508325739122-c57a76313bf4?w=800&h=500&fit=crop',  # Castle Combe wealthy village
        'https://images.unsplash.com/photo-1524919131051-b29c762a8356?w=800&h=500&fit=crop',  # Historic British manor
    ],
}

# UK-ONLY CATEGORY IMAGES - NO NEWSPAPER IMAGES, ALL AUTHENTIC UK SCENES
CATEGORY_IMAGES = {
    'Local News': [
        # CHESHIRE & ENGLISH VILLAGES ONLY - countryside, villages, market towns
        'https://images.unsplash.com/photo-1591027590129-4de51a2fb3f6?w=800&h=500&fit=crop',  # English cobbled market town
        'https://images.unsplash.com/photo-1650117790243-d659112e532c?w=800&h=500&fit=crop',  # Cheshire pastoral green fields
        'https://images.unsplash.com/photo-1588152850700-c82ecb8ba9b1?w=800&h=500&fit=crop',  # English sheep countryside
        'https://images.unsplash.com/photo-1568190538421-53523065d4b8?w=800&h=500&fit=crop',  # Yorkshire Dales road
        'https://images.unsplash.com/photo-1670620800086-3b9a345967fc?w=800&h=500&fit=crop',  # Cotswolds stone cottages
        'https://images.unsplash.com/photo-1670620800060-b90889e9f7d9?w=800&h=500&fit=crop',  # English village lane
        'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&h=500&fit=crop',  # Historic English shopfront
        'https://images.unsplash.com/photo-1567610018053-7f1b5c2d7f01?w=800&h=500&fit=crop',  # English village green grass
        'https://images.unsplash.com/photo-1590058175032-5e68d70e3e2b?w=800&h=500&fit=crop',  # UK stone bridge river
        'https://images.unsplash.com/photo-1587474260584-136574528ed5?w=800&h=500&fit=crop',  # English town square
        'https://images.unsplash.com/photo-1566159196936-b4f3dc52dbfc?w=800&h=500&fit=crop',  # British countryside footpath
        'https://images.unsplash.com/photo-1599974331560-c4d5c209a005?w=800&h=500&fit=crop',  # English village houses
        'https://images.unsplash.com/photo-1590182844668-a09d1fa27c1f?w=800&h=500&fit=crop',  # UK village church spire
        'https://images.unsplash.com/photo-1584530782379-886b08e3c9b5?w=800&h=500&fit=crop',  # English rolling hills
        'https://images.unsplash.com/photo-1542566604-6d30ead97cfe?w=800&h=500&fit=crop',  # UK farmland scene
        'https://images.unsplash.com/photo-1565008576549-57569a49371d?w=800&h=500&fit=crop',  # English high street
        'https://images.unsplash.com/photo-1527489377706-5bf97e608852?w=800&h=500&fit=crop',  # UK market town center
        'https://images.unsplash.com/photo-1508325739122-c57a76313bf4?w=800&h=500&fit=crop',  # Castle Combe village
        'https://images.unsplash.com/photo-1549544131-35406370c265?w=800&h=500&fit=crop',  # UK green pastoral valley
        'https://images.unsplash.com/photo-1524919131051-b29c762a8356?w=800&h=500&fit=crop',  # Historic British manor
        'https://images.unsplash.com/photo-1763238638505-76f22e816560?w=800&h=500&fit=crop',  # English market town street
        'https://images.unsplash.com/photo-1696113073939-213d3d9610b1?w=800&h=500&fit=crop',  # UK village cottages
    ],
    'Business': [
        # UK BUSINESS - London offices, Canary Wharf (NO newspaper images)
        'https://images.unsplash.com/photo-1486325212027-8081e485255e?w=800&h=500&fit=crop',  # London Shard business
        'https://images.unsplash.com/photo-1529655683826-aba9b3e77383?w=800&h=500&fit=crop',  # Tower Bridge London
        'https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800&h=500&fit=crop',  # London city skyline
        'https://images.unsplash.com/photo-1520986606214-8b456906c813?w=800&h=500&fit=crop',  # UK modern office building
        'https://images.unsplash.com/photo-1454117096348-e4abbeba002c?w=800&h=500&fit=crop',  # London office towers
        'https://images.unsplash.com/photo-1526129318478-62ed807ebdf9?w=800&h=500&fit=crop',  # British street scene
        'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=800&h=500&fit=crop',  # UK corporate glass building
        'https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&h=500&fit=crop',  # British office interior
        'https://images.unsplash.com/photo-1497215728101-856f4ea42174?w=800&h=500&fit=crop',  # UK workspace
        'https://images.unsplash.com/photo-1560179707-f14e90ef3623?w=800&h=500&fit=crop',  # British business exterior
        'https://images.unsplash.com/photo-1521737711867-e3b97375f902?w=800&h=500&fit=crop',  # UK business meeting
        'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=800&h=500&fit=crop',  # London financial district
    ],
    'Tech': [
        # UK TECH - servers, coding, innovation
        'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&h=500&fit=crop',  # UK data globe
        'https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&h=500&fit=crop',  # Circuit board tech
        'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800&h=500&fit=crop',  # Cybersecurity lock
        'https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=800&h=500&fit=crop',  # UK tech workspace laptops
        'https://images.unsplash.com/photo-1504639725590-34d0984388bd?w=800&h=500&fit=crop',  # Coding screen
        'https://images.unsplash.com/photo-1535378620166-273708d44e4c?w=800&h=500&fit=crop',  # UK tech office
        'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&h=500&fit=crop',  # Digital matrix code
        'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&h=500&fit=crop',  # Server room
        'https://images.unsplash.com/photo-1547658719-da2b51169166?w=800&h=500&fit=crop',  # Web development screen
        'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=800&h=500&fit=crop',  # UK scientist lab
        'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800&h=500&fit=crop',  # UK robotics tech
        'https://images.unsplash.com/photo-1555255707-c07966088b7b?w=800&h=500&fit=crop',  # Innovation tech
    ],
    'Finance': [
        # UK FINANCE - City of London, currency
        'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&h=500&fit=crop',  # UK stock trading screens
        'https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=800&h=500&fit=crop',  # British pound notes
        'https://images.unsplash.com/photo-1559526324-4b87b5e36e44?w=800&h=500&fit=crop',  # UK finance chart
        'https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=800&h=500&fit=crop',  # Financial planning
        'https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=800&h=500&fit=crop',  # UK coins stack
        'https://images.unsplash.com/photo-1460472178825-e5240623afd5?w=800&h=500&fit=crop',  # London financial skyline
        'https://images.unsplash.com/photo-1567427017947-545c5f8d16ad?w=800&h=500&fit=crop',  # UK banking ATM
        'https://images.unsplash.com/photo-1565372195458-9de0b320ef04?w=800&h=500&fit=crop',  # British currency coins
        'https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=800&h=500&fit=crop',  # UK financial services
        'https://images.unsplash.com/photo-1621761191319-c6fb62004040?w=800&h=500&fit=crop',  # Banking app UK
    ],
    'Health': [
        # UK HEALTH - NHS, British healthcare
        'https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=800&h=500&fit=crop',  # NHS doctor consultation
        'https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=800&h=500&fit=crop',  # UK hospital corridor
        'https://images.unsplash.com/photo-1571772996211-2f02c9727629?w=800&h=500&fit=crop',  # UK hospital building
        'https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=800&h=500&fit=crop',  # UK doctor stethoscope
        'https://images.unsplash.com/photo-1551076805-e1869033e561?w=800&h=500&fit=crop',  # UK medical equipment
        'https://images.unsplash.com/photo-1631217868264-e5b90bb7e133?w=800&h=500&fit=crop',  # UK patient care
        'https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=800&h=500&fit=crop',  # UK nurse healthcare
        'https://images.unsplash.com/photo-1584432810601-6c7f27d2362b?w=800&h=500&fit=crop',  # NHS vaccination injection
        'https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=800&h=500&fit=crop',  # UK medical research
        'https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?w=800&h=500&fit=crop',  # UK dentist healthcare
        'https://images.unsplash.com/photo-1581594693702-fbdc51b2763b?w=800&h=500&fit=crop',  # UK medical lab
    ],
    'Weather': [
        # UK WEATHER - British weather over UK landscapes
        'https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?w=800&h=500&fit=crop',  # UK rain storm clouds
        'https://images.unsplash.com/photo-1478719059408-592965723cbc?w=800&h=500&fit=crop',  # UK grey cloudy sky
        'https://images.unsplash.com/photo-1500740516770-92bd004b996e?w=800&h=500&fit=crop',  # UK sunset countryside
        'https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=800&h=500&fit=crop',  # UK sunrise field
        'https://images.unsplash.com/photo-1428592953211-077101b2021b?w=800&h=500&fit=crop',  # UK storm clouds dark
        'https://images.unsplash.com/photo-1527482797697-8795b05a13fe?w=800&h=500&fit=crop',  # UK fog mist morning
        'https://images.unsplash.com/photo-1530908295418-a12e326966ba?w=800&h=500&fit=crop',  # UK dramatic sky
        'https://images.unsplash.com/photo-1534088568595-a066f410bcda?w=800&h=500&fit=crop',  # UK autumn leaves weather
        'https://images.unsplash.com/photo-1561553590-267fc716698a?w=800&h=500&fit=crop',  # UK spring weather
        'https://images.unsplash.com/photo-1605451523461-b48c9d0ec3c9?w=800&h=500&fit=crop',  # UK winter snow scene
    ],
    'Food': [
        # BRITISH FOOD - UK restaurants, British cuisine
        'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800&h=500&fit=crop',  # British restaurant table
        'https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=800&h=500&fit=crop',  # British pub meal
        'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800&h=500&fit=crop',  # UK plated dinner
        'https://images.unsplash.com/photo-1476224203421-9ac39bcb3327?w=800&h=500&fit=crop',  # British full breakfast
        'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&h=500&fit=crop',  # UK pizza meal
        'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=800&h=500&fit=crop',  # British cafe pancakes
        'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800&h=500&fit=crop',  # UK roast dinner
        'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800&h=500&fit=crop',  # British healthy salad
        'https://images.unsplash.com/photo-1473093295043-cdd812d0e601?w=800&h=500&fit=crop',  # UK fine dining
        'https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=800&h=500&fit=crop',  # British vegetable dish
    ],
    'Festive': [
        # BRITISH FESTIVE - UK Christmas, celebrations
        'https://images.unsplash.com/photo-1512389142860-9c449e58a543?w=800&h=500&fit=crop',  # UK Christmas decorations
        'https://images.unsplash.com/photo-1482517967863-00e15c9b44be?w=800&h=500&fit=crop',  # British Christmas scene
        'https://images.unsplash.com/photo-1543589077-47d81606c1bf?w=800&h=500&fit=crop',  # UK Christmas tree lights
        'https://images.unsplash.com/photo-1576919228236-a097c32a5cd4?w=800&h=500&fit=crop',  # British Christmas lights
        'https://images.unsplash.com/photo-1544986581-efac024faf62?w=800&h=500&fit=crop',  # UK Christmas market stall
        'https://images.unsplash.com/photo-1512909006721-3d6018887383?w=800&h=500&fit=crop',  # British festive lights
        'https://images.unsplash.com/photo-1481653125770-b78c206c59d4?w=800&h=500&fit=crop',  # UK Christmas street
        'https://images.unsplash.com/photo-1511407192727-02e0a49e8a0f?w=800&h=500&fit=crop',  # British New Year
        'https://images.unsplash.com/photo-1607447009832-c18dafe4b61b?w=800&h=500&fit=crop',  # UK winter festive
        'https://images.unsplash.com/photo-1513297887119-d46091b24bfa?w=800&h=500&fit=crop',  # British Christmas morning
    ],
    'Events': [
        # UK EVENTS - British festivals, local fairs
        'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=800&h=500&fit=crop',  # UK festival lights
        'https://images.unsplash.com/photo-1530103862676-de8c9debad1d?w=800&h=500&fit=crop',  # British celebration balloons
        'https://images.unsplash.com/photo-1501281668745-f7f57925c3b4?w=800&h=500&fit=crop',  # UK concert crowd
        'https://images.unsplash.com/photo-1519671482749-fd09be7ccebf?w=800&h=500&fit=crop',  # British party sparklers
        'https://images.unsplash.com/photo-1506157786151-b8491531f063?w=800&h=500&fit=crop',  # UK music event stage
        'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&h=500&fit=crop',  # British conference hall
        'https://images.unsplash.com/photo-1464047736614-af63643285bf?w=800&h=500&fit=crop',  # UK country fair
        'https://images.unsplash.com/photo-1472653431158-6364773b2a56?w=800&h=500&fit=crop',  # British local event
        'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800&h=500&fit=crop',  # UK nightlife
        'https://images.unsplash.com/photo-1492538368677-f6e0afe31dcc?w=800&h=500&fit=crop',  # British outdoor gathering
    ],
    'Sports': [
        # UK SPORTS - Football, rugby, cricket
        'https://images.unsplash.com/photo-1459865264687-595d652de67e?w=800&h=500&fit=crop',  # UK football stadium
        'https://images.unsplash.com/photo-1579952363873-27f3bade9f55?w=800&h=500&fit=crop',  # British football ball
        'https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=800&h=500&fit=crop',  # UK football match
        'https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=800&h=500&fit=crop',  # British rugby scrum
        'https://images.unsplash.com/photo-1529900748604-07564a03e7a6?w=800&h=500&fit=crop',  # UK cricket match
        'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=800&h=500&fit=crop',  # British athletics track
        'https://images.unsplash.com/photo-1530549387789-4c1017266635?w=800&h=500&fit=crop',  # UK swimming pool
        'https://images.unsplash.com/photo-1535131749006-b7f58c99034b?w=800&h=500&fit=crop',  # British golf course
        'https://images.unsplash.com/photo-1546519638-68e109498ffc?w=800&h=500&fit=crop',  # UK basketball court
        'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=800&h=500&fit=crop',  # British gym fitness
    ],
    'Community': [
        # UK COMMUNITY - British village life, gatherings
        'https://images.unsplash.com/photo-1464226184884-fa280b87c399?w=800&h=500&fit=crop',  # UK countryside field
        'https://images.unsplash.com/photo-1559027615-cd4628902d4a?w=800&h=500&fit=crop',  # British community garden
        'https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=800&h=500&fit=crop',  # UK friends group
        'https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=800&h=500&fit=crop',  # British family park
        'https://images.unsplash.com/photo-1511285560929-80b456fea0bc?w=800&h=500&fit=crop',  # UK wedding celebration
        'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=800&h=500&fit=crop',  # British team meeting
        'https://images.unsplash.com/photo-1517457373958-b7bdd4587205?w=800&h=500&fit=crop',  # UK volunteer group
        'https://images.unsplash.com/photo-1491438590914-bc09fcaaf77a?w=800&h=500&fit=crop',  # British friends laughing
        'https://images.unsplash.com/photo-1528605248644-14dd04022da1?w=800&h=500&fit=crop',  # UK community meal
        'https://images.unsplash.com/photo-1517048676732-d65bc937f952?w=800&h=500&fit=crop',  # British team office
    ],
    'UK News': [
        # UK NATIONAL NEWS - London landmarks, Parliament
        'https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800&h=500&fit=crop',  # London skyline sunset
        'https://images.unsplash.com/photo-1529655683826-aba9b3e77383?w=800&h=500&fit=crop',  # Tower Bridge night
        'https://images.unsplash.com/photo-1486325212027-8081e485255e?w=800&h=500&fit=crop',  # London Shard building
        'https://images.unsplash.com/photo-1520986606214-8b456906c813?w=800&h=500&fit=crop',  # UK Parliament area
        'https://images.unsplash.com/photo-1454117096348-e4abbeba002c?w=800&h=500&fit=crop',  # British cityscape evening
        'https://images.unsplash.com/photo-1526129318478-62ed807ebdf9?w=800&h=500&fit=crop',  # London street lamps
        'https://images.unsplash.com/photo-1485201543483-f06c8d2a8fb4?w=800&h=500&fit=crop',  # British landmark
        'https://images.unsplash.com/photo-1505092670810-fb7d4ff03ee5?w=800&h=500&fit=crop',  # UK city life
        'https://images.unsplash.com/photo-1508966319062-b5bc8fb46d38?w=800&h=500&fit=crop',  # British urban scene
        'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=800&h=500&fit=crop',  # London financial district
    ]
}
# TOPIC-SPECIFIC IMAGE MAPPINGS (Keywords -> Images)
TOPIC_IMAGE_MAPPINGS = {
    'police': [
        'https://images.unsplash.com/photo-1455735459330-969b65c65b1c?w=800&h=500&fit=crop', # UK Police car
        'https://images.unsplash.com/photo-1595329088732-d853e3ceba74?w=800&h=500&fit=crop', # Police officer
        'https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=800&h=500&fit=crop', # Law/Justice
        'https://images.unsplash.com/photo-1453873531674-2151bcd01707?w=800&h=500&fit=crop', # Police lights
        'https://images.unsplash.com/photo-1532375810709-75b1da00537c?w=800&h=500&fit=crop', # Emergency lights
        'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&h=500&fit=crop', # UK street at night
        'https://images.unsplash.com/photo-1594312915251-48db9280c8f1?w=800&h=500&fit=crop', # Urban night scene
        'https://images.unsplash.com/photo-1569863959165-56dae551d4fc?w=800&h=500&fit=crop', # City night
    ],
    'crime': [
        'https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=800&h=500&fit=crop', # Law/Justice
        'https://images.unsplash.com/photo-1505664194779-8beaceb93744?w=800&h=500&fit=crop', # Pillars of justice
        'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&h=500&fit=crop', # UK street at night
        'https://images.unsplash.com/photo-1453873531674-2151bcd01707?w=800&h=500&fit=crop', # Emergency lights
    ],
    'arrest': [
        'https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=800&h=500&fit=crop', # Handcuffs/Law
        'https://images.unsplash.com/photo-1453873531674-2151bcd01707?w=800&h=500&fit=crop', # Police lights
    ],
    'court': [
        'https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=800&h=500&fit=crop', # Gavel/Law
        'https://images.unsplash.com/photo-1505664194779-8beaceb93744?w=800&h=500&fit=crop', # Pillars of justice
    ],
    'fire': [
        'https://images.unsplash.com/photo-1486551937199-baf066858de7?w=800&h=500&fit=crop', # Fire truck
        'https://images.unsplash.com/photo-1517213849290-bbbfffdc6da3?w=800&h=500&fit=crop', # Fire scene
        'https://images.unsplash.com/photo-1560635070-c7d8e83e1a71?w=800&h=500&fit=crop', # Emergency response
    ],
    'crash': [
        'https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=800&h=500&fit=crop', # Car/Road
        'https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=800&h=500&fit=crop', # Motorway
        'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=800&h=500&fit=crop', # Road at night
    ],
    'motorway': [
        'https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=800&h=500&fit=crop', # Motorway
        'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=800&h=500&fit=crop', # Road at night
        'https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=800&h=500&fit=crop', # Car/Road
    ],
    'nhs': [
        'https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=800&h=500&fit=crop', # Hospital building
        'https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=800&h=500&fit=crop', # Medical staff
    ],
    'hospital': [
        'https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=800&h=500&fit=crop', # Hospital building
        'https://images.unsplash.com/photo-1516549655169-df83a0774514?w=800&h=500&fit=crop', # Ambulance
    ],
    'school': [
        'https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=800&h=500&fit=crop', # Classroom
        'https://images.unsplash.com/photo-1546410531-bb4caa6b424d?w=800&h=500&fit=crop', # School building
    ],
    'transport': [
        'https://images.unsplash.com/photo-1517355163-39cc70762df7?w=800&h=500&fit=crop', # Train station
        'https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=800&h=500&fit=crop', # Car/Traffic
    ],
    'train': [
        'https://images.unsplash.com/photo-1517355163-39cc70762df7?w=800&h=500&fit=crop', # Train station
        'https://images.unsplash.com/photo-1474487548417-781cb71495f3?w=800&h=500&fit=crop', # Train tracks
    ],
    'weather': [
        'https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?w=800&h=500&fit=crop', # Rain
        'https://images.unsplash.com/photo-1561553590-267fc716698a?w=800&h=500&fit=crop', # Sunny sky
    ],
    'council': [
        'https://images.unsplash.com/photo-1555848962-6e79363ec58f?w=800&h=500&fit=crop', # Meeting room
        'https://images.unsplash.com/photo-1577495508048-b635879837f1?w=800&h=500&fit=crop', # Official building
    ]
}

# CHESHIRE & UK GENERIC POOL (Safe for any Cheshire story fallback)
CHESHIRE_FALLBACK_IMAGES = [
    # Villages / Market Towns
    'https://images.unsplash.com/photo-1549544131-35406370c265?w=800&h=500&fit=crop',  # Green valley
    'https://images.unsplash.com/photo-1568190538421-53523065d4b8?w=800&h=500&fit=crop',  # Country road
    'https://images.unsplash.com/photo-1508325739122-c57a76313bf4?w=800&h=500&fit=crop',  # Village stone
    'https://images.unsplash.com/photo-1599974331560-c4d5c209a005?w=800&h=500&fit=crop',  # Brick houses
    'https://images.unsplash.com/photo-1590182844668-a09d1fa27c1f?w=800&h=500&fit=crop',  # Church spire
    'https://images.unsplash.com/photo-1524919131051-b29c762a8356?w=800&h=500&fit=crop',  # Manor house
    'https://images.unsplash.com/photo-1696113073939-213d3d9610b1?w=800&h=500&fit=crop',  # Cottage
    'https://images.unsplash.com/photo-1566159196936-b4f3dc52dbfc?w=800&h=500&fit=crop',  # Path
    'https://images.unsplash.com/photo-1588152850700-c82ecb8ba9b1?w=800&h=500&fit=crop',  # Sheep
    'https://images.unsplash.com/photo-1542566604-6d30ead97cfe?w=800&h=500&fit=crop',  # Farmland
    'https://images.unsplash.com/photo-1565008576549-57569a49371d?w=800&h=500&fit=crop',  # High street
    'https://images.unsplash.com/photo-1527489377706-5bf97e608852?w=800&h=500&fit=crop',  # Town center
    'https://images.unsplash.com/photo-1591027590129-4de51a2fb3f6?w=800&h=500&fit=crop',  # Cobbles
    'https://images.unsplash.com/photo-1570193628474-5ba0c21b8f3f?w=800&h=500&fit=crop',  # Village green
    'https://images.unsplash.com/photo-1500343673619-3aa6d5c281c1?w=800&h=500&fit=crop',  # Fields
    'https://images.unsplash.com/photo-1582555172866-f73bb12a2ab3?w=800&h=500&fit=crop',  # Rural
    'https://images.unsplash.com/photo-1516815231560-8f41ec531527?w=800&h=500&fit=crop',  # Rural buildings
    'https://images.unsplash.com/photo-1609137144813-7d9921338f24?w=800&h=500&fit=crop',  # Street scene
    'https://images.unsplash.com/photo-1548013146-72479768bada?w=800&h=500&fit=crop',  # Lane
    'https://images.unsplash.com/photo-1502139214982-d0ad755818d8?w=800&h=500&fit=crop',  # Village
    'https://images.unsplash.com/photo-1518378188025-22bd89516ee2?w=800&h=500&fit=crop',  # Historic house
    'https://images.unsplash.com/photo-1568084680786-a84f91d1153c?w=800&h=500&fit=crop',  # Road
    'https://images.unsplash.com/photo-1598513431456-ebedfd60c98f?w=800&h=500&fit=crop',  # Landscape
]

# EXPLICITLY BANNED IMAGES (Newspapers, generic business text, etc)
BANNED_IMAGES = [
    'https://images.unsplash.com/photo-1504711434969-e33886168f5c',  # World Business newspapers
    'https://images.unsplash.com/photo-1586339949916-3e9457bef6d3',  # Generic newspapers
    'https://images.unsplash.com/photo-1566378246598-5b11a0d486cc',  # Newspapers stack
    'https://images.unsplash.com/photo-1595152772835-219674b2a8a6',  # Newspaper rack
    'https://images.unsplash.com/photo-1523995462485-3d171b5c8fa9',  # Newspaper close up
    'https://images.unsplash.com/photo-1584820927498-cfe5211fd8bf',  # Blue gloves PPE (Medical)
    'https://images.unsplash.com/photo-1553484771-047a44eee27b',  # Old newspaper/business image
    'https://images.unsplash.com/photo-1560179707-f14e90ef3623',  # London financial district (often generic)
]

# Build a GLOBAL pool of ALL unique images for fallback
def get_all_unique_images():
    """Get all unique images from all categories"""
    all_images = set()
    for images in CATEGORY_IMAGES.values():
        all_images.update(images)
    return list(all_images)

ALL_UNIQUE_IMAGES = get_all_unique_images()
print(f"[INFO] Initialized {len(ALL_UNIQUE_IMAGES)} unique images across all categories")

def extract_photo_id(url: str) -> str:
    """
    Extract the unique photo ID from an image URL.
    CRITICAL: This function extracts the actual photo identifier, ignoring
    URL parameters like timestamps/session IDs that make same photos look different.
    
    Examples:
    - Unsplash: photo-1632207857925-a4d52c54d683?ixid=ABC -> unsplash:photo-1632207857925-a4d52c54d683
    - Pexels: /photos/12345/pexels-photo-12345.jpeg -> pexels:12345
    - Pixabay: /photo/city-123456_1280.jpg -> pixabay:123456
    - Static: https://example.com/image.jpg?w=800 -> https://example.com/image.jpg
    """
    if not url:
        return ""
    
    # Unsplash: extract photo-XXXX identifier
    if 'unsplash.com' in url or 'photo-' in url:
        match = re.search(r'photo-([a-zA-Z0-9_-]+)', url)
        if match:
            return f'unsplash:{match.group(0)}'
    
    # Pexels: extract numeric photo ID
    if 'pexels.com' in url:
        match = re.search(r'/photos/(\d+)', url)
        if match:
            return f'pexels:{match.group(1)}'
        # Try alternate format
        match = re.search(r'pexels-photo-(\d+)', url)
        if match:
            return f'pexels:{match.group(1)}'
    
    # Pixabay: extract numeric ID from URL
    if 'pixabay.com' in url:
        match = re.search(r'[_-](\d{5,})', url)  # Look for 5+ digit IDs
        if match:
            return f'pixabay:{match.group(1)}'
    
    # Static/fallback URL - remove query params and use base URL as ID
    base_url = url.split('?')[0]
    return base_url

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
    """
    Select a UK image that matches the article's location if possible.
    Checks article title and content for location mentions.
    """
    text = (title + ' ' + content).lower()
    
    # Check for Cheshire location mentions
    location_matches = []
    for location, images in LOCATION_IMAGES.items():
        if location in text:
            available = [
                img for img in images 
                if not is_image_used(img, used_photo_ids)
                and not any(b in img for b in BANNED_IMAGES)
            ]
            if available:
                location_matches.extend(available)
    
    if location_matches:
        image = random.choice(location_matches)
        logger.info(f"Selected location-specific UK image: {image[-50:]}")
        return image
    
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
    STRICT unique UK-only image selection - NEVER returns a duplicate image.
    Returns None if no unique image is available (signals to skip article generation).
    
    Priority:
    1. Location-specific image (if article mentions a UK location)
    2. Category-specific UK image
    3. Any available UK image from pool
    """
    # FIRST: Try topic-specific image (keyword matching)
    if title or content:
        topic_image = select_topic_image(title, content, used_photo_ids)
        if topic_image:
            return topic_image

    # SECOND: Try location-specific image based on article content
    if title or content:
        location_image = select_location_image(title, content, used_photo_ids)
        if location_image:
            return location_image
    
    # SECOND: Try category-specific UK images
    category_images = CATEGORY_IMAGES.get(category, [])
    available = [
        img for img in category_images 
        if not is_image_used(img, used_photo_ids)
        and not any(b in img for b in BANNED_IMAGES)
    ]
    
    if available:
        image = random.choice(available)
        logger.info(f"Selected unique UK {category} image: {image[-50:]}")
        return image
    
    # THIRD: If category images exhausted, try ALL UK images pool
    # CRITICAL: If scope is 'cheshire', ONLY fall back to Cheshire/Village images
    # Do NOT fallback to London/City images for local news
    
    fallback_pool = ALL_UNIQUE_IMAGES
    if title and ('cheshire' in title.lower() or 'golden triangle' in title.lower() or 'knutsford' in title.lower() or 'wilmslow' in title.lower()):
        # Force Cheshire fallback for local stories
        fallback_pool = CHESHIRE_FALLBACK_IMAGES + CATEGORY_IMAGES.get('Local News', [])
        
    all_available = [
        img for img in fallback_pool
        if not is_image_used(img, used_photo_ids)
        and not any(b in img for b in BANNED_IMAGES)
    ]
    
    if all_available:
        image = random.choice(all_available)
        logger.info(f"Selected unique fallback image from pool: {image[-50:]}")
        return image
    
    # NO unique UK images available - return None to signal skip
    logger.warning(f"No unique UK images available! {len(used_photo_ids)} images already in use, {len(ALL_UNIQUE_IMAGES)} total in pool")
    return None

async def get_dynamic_image(title: str, category: str, content: str, scope: str, used_photo_ids: set) -> str:
    """
    Get an image for an article using multiple free image APIs.
    Priority: 1) Unsplash  2) Pexels  3) Pixabay  4) Static fallback pool
    All sources configured to return UK/Cheshire specific images.
    CRITICAL: Ensures no duplicate images across all sources.
    """
    if used_photo_ids is None:
        used_photo_ids = set()
    
    # Try Unsplash API first (great UK content)
    if unsplash_service.enabled:
        try:
            unsplash_image = await unsplash_service.get_article_image(
                title=title,
                category=category,
                content=content,
                scope=scope,
                used_images=used_photo_ids  # Pass used_photo_ids to check duplicates
            )
            if unsplash_image and not is_image_used(unsplash_image, used_photo_ids):
                logger.info(f"✅ Unsplash UK image matched for: {title[:40]}...")
                return unsplash_image
            elif unsplash_image:
                logger.warning("Unsplash image already used, trying Pexels...")
        except Exception as e:
            logger.warning(f"Unsplash API error: {str(e)}")
    
    # Try Pexels API second (excellent UK content)
    if pexels_service.enabled:
        try:
            pexels_image = await pexels_service.get_article_image(
                title=title,
                category=category,
                scope=scope,
                used_images=used_photo_ids
            )
            if pexels_image and not is_image_used(pexels_image, used_photo_ids):
                logger.info(f"✅ Pexels UK image matched for: {title[:40]}...")
                return pexels_image
            elif pexels_image:
                logger.warning("Pexels image already used, trying Pixabay...")
        except Exception as e:
            logger.warning(f"Pexels API error: {str(e)}")
    
    # Try Pixabay API third (good UK/British content)
    if pixabay_service.enabled:
        try:
            pixabay_image = await pixabay_service.get_article_image(
                title=title,
                category=category,
                scope=scope,
                used_images=used_photo_ids
            )
            if pixabay_image and not is_image_used(pixabay_image, used_photo_ids):
                logger.info(f"✅ Pixabay UK image matched for: {title[:40]}...")
                return pixabay_image
            elif pixabay_image:
                logger.warning("Pixabay image already used, using static fallback...")
        except Exception as e:
            logger.warning(f"Pixabay API error: {str(e)}")
    
    # Fallback to static Unsplash pool
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
            
            is_local = (
            article.get("scope") == "cheshire"
            or article.get("is_cheshire_related") is True
            or bool(article.get("location"))
            )           
            scope = "cheshire" if is_local else "uk"

            # Prevent "Local News" unless truly local
            category = article.get("category") or "UK News"
            if category == "Local News" and scope != "cheshire":
                category = "UK News"

            headlines.append({
                "headline": title,
                "category": category,
                "scope": scope,
                "source": article.get("source", "BBC News"),
                "source_url": article.get("source_url", "")
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
        valid_categories = ["Local News", "UK News", "Business", "Health", "Sports", "Tech", "Weather", "Food"]
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

class GenerateFromHeadlineRequest(BaseModel):
    headline: str
    category: str = "Local News"
    scope: str = "uk"

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

# =====================================================================================

@api_router.post("/generate-from-headline")
async def generate_from_headline(request: GenerateFromHeadlineRequest):
    """
    Generate a single article based on a specific breaking news headline.
    This provides on-demand article generation when a user clicks a headline.
    """
    try:
        logger.info(f"Generating article from headline: {request.headline[:50]}...")
        
        # Get used photo IDs to ensure uniqueness
        used_photo_ids = await get_used_images_from_db()
        
        # Generate the article using the headline as the topic
        article_data = await generate_article_with_gemini(
            topic=request.headline,
            scope=request.scope,
            category=request.category,
            used_photo_ids=used_photo_ids
        )
        
        if not article_data:
            return {"success": False, "message": "Could not generate article", "article": None}
        
        # Get a matching image
        image = await get_dynamic_image(
            title=article_data['title'],
            category=request.category,
            content=article_data['content'],
            scope=request.scope,
            used_photo_ids=used_photo_ids
        )
        
        if not image:
            # Use a default image if none found
            image = "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=800&h=500&fit=crop"
        
        # Create the article
        article = {
            "id": str(uuid4()),
            "title": article_data['title'],
            "content": article_data['content'],
            "image": image,
            "category": request.category,
            "tags": article_data.get('tags', [request.scope, request.category.lower().replace(' ', '-')]),
            "publishedDate": datetime.now(timezone.utc).isoformat(),
            "author": "Cheshire Today Editorial"
        }
        
        # Save to database
        await db.articles.insert_one({**article, "_id": None})
        
        logger.info(f"✅ Generated article from headline: {article['title'][:40]}...")
        
        return {"success": True, "article": article}
        
    except Exception as e:
        logger.error(f"Error generating article from headline: {str(e)}")
        return {"success": False, "message": str(e), "article": None}

@api_router.post("/generate-articles", response_model=GenerateArticlesResponse)
async def generate_articles(request: GenerateArticlesRequest):
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
            use_perplexity=True
        )
        
        result = await import_hybrid_news(hybrid_request)
        
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
async def import_real_news(limit: int = 20, category: Optional[str] = None):
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
        
        # Get existing article titles to avoid duplicates
        existing_titles = set()
        existing_articles = await db.articles.find({}, {'title': 1}).to_list(1000)
        for a in existing_articles:
            existing_titles.add(a.get('title', '').lower().strip())
        
        # Import new articles
        imported = 0
        skipped = 0
        
        for article in articles:
            title = article.get('title', '').strip()
            if not title or title.lower() in existing_titles:
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
            
            # Insert into database
            await db.articles.insert_one(article)
            existing_titles.add(title.lower())
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
    cheshire_articles: int = 8   # 8 Cheshire/local articles
    uk_articles: int = 12        # 12 UK articles
    max_sports: int = 3          # Limit sports articles
    business_articles: int = 2   # 2 Business articles (FREE from RSS)
    health_articles: int = 2     # 2 Health articles (FREE from RSS)
    tech_articles: int = 2       # 2 Tech articles (FREE from RSS)
    science_articles: int = 2    # 2 Science articles (FREE from RSS)
    entertainment_articles: int = 2  # 2 Entertainment articles (FREE from RSS)
    use_perplexity: bool = True  # ENABLED - Hybrid model with AI content generation


@api_router.post("/import-hybrid-news")
async def import_hybrid_news(request: HybridNewsRequest = HybridNewsRequest()):
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
        
        # Get existing article titles to avoid duplicates
        existing_titles = set()
        existing_articles = await db.articles.find({}, {'title': 1, 'image': 1}).to_list(1000)
        for a in existing_articles:
            existing_titles.add(a.get('title', '').lower().strip())
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
        health_imported = 0
        tech_imported = 0
        science_imported = 0
        entertainment_imported = 0
        max_sports = getattr(request, 'max_sports', 3)  # Default 3 sports articles
        
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
            health_articles = [a for a in uk_with_images if a.get('category') == 'Health']
            tech_articles = [a for a in uk_with_images if a.get('category') == 'Tech']
            science_articles = [a for a in uk_with_images if a.get('category') == 'Science']
            entertainment_articles = [a for a in uk_with_images if a.get('category') == 'Entertainment']
            uk_news_articles = [a for a in uk_with_images if a.get('category') in ['UK News', 'Local News'] or a.get('category') not in ['Sports', 'Business', 'Health', 'Tech', 'Science', 'Entertainment']]
            
            logger.info(f"Found: {len(uk_news_articles)} UK News, {len(business_articles)} Business, {len(health_articles)} Health, {len(tech_articles)} Tech, {len(science_articles)} Science, {len(entertainment_articles)} Entertainment, {len(sports_articles)} Sports")
            
            # Helper function to import articles from a category with Perplexity content generation
            async def import_category_articles(articles_list, category_name, max_count, counter_name):
                nonlocal perplexity_cost_estimate
                imported_count = 0
                for article in articles_list:
                    if imported_count >= max_count:
                        break
                        
                    title = article.get('title', '').strip()
                    rss_image = article.get('image', '').strip()
                    
                    # Skip if duplicate title or image
                    if not title or title.lower() in existing_titles:
                        continue
                    if rss_image in used_image_urls:
                        logger.info(f"Skipping duplicate RSS image: {title[:40]}...")
                        continue
                    
                    # Get content - either generate via Perplexity or use RSS content
                    original_content = article.get('content', '')
                    
                    if request.use_perplexity:
                        # Generate detailed content using Perplexity
                        logger.info(f"Generating content for {category_name} article: {title[:40]}...")
                        detailed_content = await perplexity_service.generate_article_content(
                            title=title,
                            summary=original_content,
                            source=article.get('source', 'BBC News'),
                            source_url=article.get('source_url', '')
                        )
                        perplexity_cost_estimate += 0.005
                    else:
                        # Use RSS content directly (faster, no AI)
                        detailed_content = original_content if len(original_content) > 100 else f"{original_content}\n\nRead the full story at the source."
                    
                    # Use RSS image (guaranteed perfect match)
                    article['image'] = rss_image
                    article['image_source'] = 'rss_feed'
                    article['content'] = detailed_content
                    article['summary'] = original_content[:200] + '...' if len(original_content) > 200 else original_content
                    article['scope'] = 'uk'
                    article['author'] = article.get('source', 'BBC News')
                    article['id'] = str(uuid4())
                    
                    await db.articles.insert_one(article)
                    existing_titles.add(title.lower())
                    used_image_urls.add(rss_image)
                    imported_articles.append(article)
                    imported_count += 1
                    logger.info(f"✅ Imported {category_name} article: {title[:50]}...")
                
                return imported_count
            
            # Import UK News articles
            uk_imported = await import_category_articles(uk_news_articles, "UK News", request.uk_articles, "uk_imported")
            
            # Import Business articles (FREE from RSS)
            business_imported = await import_category_articles(business_articles, "Business", request.business_articles, "business_imported")
            
            # Import Health articles (FREE from RSS)
            health_imported = await import_category_articles(health_articles, "Health", request.health_articles, "health_imported")
            
            # Import Tech articles (FREE from RSS)
            tech_imported = await import_category_articles(tech_articles, "Tech", request.tech_articles, "tech_imported")
            
            # Import Science articles (FREE from RSS)
            science_imported = await import_category_articles(science_articles, "Science", request.science_articles, "science_imported")
            
            # Import Entertainment articles (FREE from RSS)
            entertainment_imported = await import_category_articles(entertainment_articles, "Entertainment", request.entertainment_articles, "entertainment_imported")
            
            # Import Sports articles (limited to max_sports)
            sports_imported = await import_category_articles(sports_articles, "Sports", max_sports, "sports_imported")
        
        # ==========================================
        # STEP 2: Check LOCAL Cheshire newspaper feeds (FREE + Full Content via Perplexity)
        # Now includes: Cheshire Live, Warrington Guardian, Manchester Evening News
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
        
        for article in cheshire_with_images:
            if cheshire_from_rss >= request.cheshire_articles:
                break
                
            title = article.get('title', '').strip()
            rss_image = article.get('image', '').strip()
            
            if not title or title.lower() in existing_titles:
                continue
            if rss_image in used_image_urls:
                continue
            
            # Get content - either generate via Perplexity or use RSS content
            original_content = article.get('content', '')
            
            if request.use_perplexity:
                # Generate detailed content using Perplexity (expands RSS summary to full article)
                logger.info(f"Generating full content for local article: {title[:40]}...")
                detailed_content = await perplexity_service.generate_article_content(
                    title=title,
                    summary=original_content,
                    source=article.get('source', 'Cheshire Live'),
                    source_url=article.get('source_url', '')
                )
                perplexity_cost_estimate += 0.005
            else:
                # Use RSS content directly (faster, no AI)
                detailed_content = original_content if len(original_content) > 100 else f"{original_content}\n\nRead the full story at the source."
            
            article['image'] = rss_image
            article['image_source'] = 'rss_feed'
            article['content'] = detailed_content
            article['summary'] = original_content[:200] + '...' if len(original_content) > 200 else original_content
            article['scope'] = 'cheshire'
            article['category'] = 'Local News'
            article['id'] = str(uuid4())
            article['is_local_source'] = True  # Mark as local source
            article['is_local_newspaper'] = article.get('is_local_feed', False)
            
            await db.articles.insert_one(article)
            existing_titles.add(title.lower())
            used_image_urls.add(rss_image)
            imported_articles.append(article)
            cheshire_from_rss += 1
            logger.info(f"✅ Imported local Cheshire article: {title[:50]}...")
        
        # ==========================================
        # STEP 3: Import Cheshire news via Perplexity (ONLY if local feeds don't have enough)
        # This is now a FALLBACK, not the primary source
        # ==========================================
        cheshire_from_perplexity = 0
        remaining_cheshire = request.cheshire_articles - cheshire_from_rss
        
        if request.use_perplexity and remaining_cheshire > 0 and cheshire_from_rss < 3:
            logger.info(f"Fetching {remaining_cheshire} more Cheshire articles via Perplexity...")
            
            cheshire_articles = await perplexity_service.search_cheshire_news(
                category="Local News", 
                limit=remaining_cheshire + 2  # Get extra in case some fail
            )
            perplexity_cost_estimate += 0.005
            
            for article in cheshire_articles:
                if cheshire_from_perplexity >= remaining_cheshire:
                    break
                    
                title = article.get('title', '').strip()
                content = article.get('content', '')
                category = article.get('category', 'Local News')
                
                if not title or title.lower() in existing_titles:
                    continue
                
                # Generate SMART image search query using Perplexity
                logger.info(f"Generating smart image query for: {title[:40]}...")
                smart_query = await perplexity_service.generate_image_search_query(
                    title=title,
                    content=content,
                    category=category
                )
                perplexity_cost_estimate += 0.005
                
                if not smart_query:
                    # Fallback to extracting key terms from title
                    smart_query = ' '.join(title.split()[:4])
                
                # Search for image using the smart query
                image = None
                
                # Try Unsplash first with smart query
                try:
                    image = await unsplash_service.search_image(smart_query + " UK")
                    if image and image not in used_image_urls:
                        logger.info(f"✅ Found Unsplash image for query: '{smart_query}'")
                    else:
                        image = None
                except Exception as e:
                    logger.warning(f"Unsplash search failed: {e}")
                
                # Try Pexels if Unsplash failed
                if not image:
                    try:
                        image = await pexels_service.search_image(smart_query)
                        if image and image not in used_image_urls:
                            logger.info(f"✅ Found Pexels image for query: '{smart_query}'")
                        else:
                            image = None
                    except Exception as e:
                        logger.warning(f"Pexels search failed: {e}")
                
                # Skip if no unique image found (quality over quantity)
                if not image:
                    logger.warning(f"Skipping article - no unique image found: {title[:40]}...")
                    continue
                
                article['image'] = image
                article['image_source'] = 'smart_search'
                article['image_query'] = smart_query
                article['scope'] = 'cheshire'
                article['id'] = str(uuid4())
                article['author'] = 'Cheshire Today'
                article['publishedDate'] = datetime.now(timezone.utc).isoformat()
                
                await db.articles.insert_one(article)
                existing_titles.add(title.lower())
                used_image_urls.add(image)
                imported_articles.append(article)
                cheshire_from_perplexity += 1
                logger.info(f"✅ Imported Cheshire article with smart image: {title[:50]}...")
        
        total_cheshire = cheshire_from_rss + cheshire_from_perplexity
        rss_images_used = len([a for a in imported_articles if a.get('image_source') == 'rss_feed'])
        smart_images_used = len([a for a in imported_articles if a.get('image_source') == 'smart_search'])
        
        logger.info(f"Hybrid import complete: {total_cheshire} Cheshire + {uk_imported} UK + {business_imported} Business + {health_imported} Health + {tech_imported} Tech + {science_imported} Science + {entertainment_imported} Entertainment + {sports_imported} Sports")
        logger.info(f"Image sources: {rss_images_used} RSS, {smart_images_used} smart search")
        
        return {
            "success": True,
            "total_imported": len(imported_articles),
            "cheshire_articles": total_cheshire,
            "cheshire_from_perplexity": cheshire_from_perplexity,
            "cheshire_from_rss": cheshire_from_rss,
            "uk_articles": uk_imported,
            "business_articles": business_imported,
            "health_articles": health_imported,
            "tech_articles": tech_imported,
            "science_articles": science_imported,
            "entertainment_articles": entertainment_imported,
            "sports_articles": sports_imported,
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
        # NOTE: use_perplexity=False for quick refresh (avoids timeout)
        # Use the Import button for full AI-enhanced articles
        request = HybridNewsRequest(
            cheshire_articles=8,   # 8 Cheshire/local articles
            uk_articles=12,        # 12 UK articles
            max_sports=3,          # Limit sports to 3
            business_articles=2,   # 2 Business articles (FREE)
            health_articles=2,     # 2 Health articles (FREE)
            tech_articles=2,       # 2 Tech articles (FREE)
            science_articles=2,    # 2 Science articles (FREE)
            entertainment_articles=2,  # 2 Entertainment articles (FREE)
            use_perplexity=False   # Quick refresh - no AI content generation
        )
        
        import_result = await import_hybrid_news(request)
        
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


@api_router.post("/admin/regenerate-content")
async def regenerate_article_content(authorized: bool = Depends(get_admin_auth)):
    """
    Regenerate content for all existing articles using Perplexity.
    Only processes articles with short content (< 500 chars).
    Cost: ~$0.005 per article
    Requires admin authentication.
    """
    try:
        # Find articles with short content
        articles = await db.articles.find({}).to_list(1000)
        
        short_content_articles = [
            a for a in articles 
            if len(a.get('content', '')) < 500
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


@api_router.post("/admin/remove-duplicates")
async def _remove_duplicates_internal():
    """
    Internal helper function to remove duplicate articles.
    Called automatically after imports and by the admin endpoint.
    Archives removed articles to archived_articles collection for link preservation.
    """
    try:
        articles = await db.articles.find({}).to_list(1000)
        
        # Group by title
        title_groups = {}
        for article in articles:
            title = article.get('title', '').strip()
            if title not in title_groups:
                title_groups[title] = []
            title_groups[title].append(article)
        
        duplicates_removed = 0
        short_removed = 0
        
        for title, group in title_groups.items():
            if len(group) > 1:
                # Sort by content length (longest first)
                group.sort(key=lambda x: len(x.get('content', '')), reverse=True)
                
                # Keep the first one (longest content), archive and remove the rest
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
                    logger.info(f"Archived duplicate: {title[:40]}...")
        
        # Remove articles with very short content (< 50 chars) - likely broken/incomplete
        # Note: RSS summaries can be short but valid - only remove truly empty articles
        remaining = await db.articles.find({}).to_list(1000)
        for article in remaining:
            content_len = len(article.get('content', ''))
            if content_len < 50:
                # Archive before deletion
                article['archived_at'] = datetime.now(timezone.utc).isoformat()
                article['archive_reason'] = 'short_content'
                original_id = article.pop('_id', None)
                try:
                    await db.archived_articles.insert_one(article)
                except:
                    pass  # Continue even if archival fails
                
                await db.articles.delete_one({'_id': original_id})
                short_removed += 1
                logger.info(f"Archived short article ({content_len} chars): {article.get('title', '')[:40]}...")
        
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
                'author': 1, 'publishedDate': 1, 'image': 1, 'tags': 1,
                'featured': 1, 'source': 1, 'source_url': 1, 'scope': 1, 'is_local_source': 1,
                'location': 1
            }
        ).sort('publishedDate', -1).skip(skip).limit(limit).to_list(limit)
        
        total_count = await db.articles.count_documents(query)
        
        # Convert ObjectId to string
        for article in articles:
            article['id'] = str(article['_id'])
            del article['_id']
        
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
        # -------------------------------
        # LOCAL DEV – use mock articles
        # -------------------------------
        if LOCAL_DEV_NO_DB:
            seed_local_articles_if_needed()
            location_lower = location.lower()

            if location_lower not in LOCATION_KEYWORDS:
                raise HTTPException(status_code=404, detail=f"Location '{location}' not found")

            # strict: only exact location matches
            filtered = [a for a in LOCAL_DEV_ARTICLES if a.get("location") == location_lower]

            # newest first (string ISO dates sort fine)
            filtered.sort(key=lambda a: a.get("publishedDate", ""), reverse=True)

            page = filtered[skip: skip + limit]

            return {
                "articles": page,
                "location": location.capitalize(),
                "total": len(filtered)
            }

        # existing DB logic continues below...
        location_lower = location.lower()
        
        if location_lower not in LOCATION_KEYWORDS:
            raise HTTPException(status_code=404, detail=f"Location '{location}' not found")
        
        # STRICT: Only match articles with location field set to this location
        # This prevents articles that merely mention a town from appearing on that town's page
        query = {'location': location_lower}
        
        articles = await db.articles.find(
            query,
            {
                '_id': 1, 'title': 1, 'content': 1, 'summary': 1, 'category': 1,
                'author': 1, 'publishedDate': 1, 'image': 1, 'tags': 1,
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
    search: Optional[str] = None  # Search query for title and content
):
    """Get all articles with optional filtering by category, source type, and search"""
    try:
        # -------------------------------
        # LOCAL DEV – return mock articles
        # -------------------------------
        if LOCAL_DEV_NO_DB:
            seed_local_articles_if_needed()
            return LOCAL_DEV_ARTICLES
        # Check cache for default homepage request (most common)
        cache_key = f"articles:{category}:{skip}:{limit}:{source_type}:{include_archived}"
        if not search and skip == 0 and limit == 20 and not category:
            cached = api_cache.get(cache_key, ttl_seconds=30)  # 30 second cache
            if cached:
                return cached
        
        query = {}
        
        # Exclude archived articles by default
        if not include_archived:
            query["$or"] = [{"archived": {"$exists": False}}, {"archived": False}]
        
        # Search functionality - search in title and content
        if search and len(search) >= 2:
            import re
            search_regex = {'$regex': re.escape(search), '$options': 'i'}
            # Override the $or query to include search
            if "$or" in query:
                # Combine archived filter with search
                query = {
                    "$and": [
                        {"$or": [{"archived": {"$exists": False}}, {"archived": False}]},
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
                    'author': 1, 'publishedDate': 1, 'image': 1, 'tags': 1,
                    'featured': 1, 'source': 1, 'source_url': 1, 'scope': 1, 'is_local_source': 1
                }
            ).sort('publishedDate', -1).skip(skip).limit(limit).to_list(limit)
            
            # Process IDs
            for article in articles:
                if 'id' not in article or not article['id']:
                    article['id'] = str(article['_id'])
                if '_id' in article:
                    del article['_id']
            
            return {"articles": articles, "total": len(articles), "search": search}
        
        # Category filtering
        if category and category != 'all':
            # Special handling for Local News - only show local sources
            if category == 'Local News':
                query['is_local_source'] = True
            # Special handling for UK News - only show national sources
            elif category == 'UK News':
                query['is_local_source'] = False
                query['category'] = {'$in': ['UK News', 'Business', 'Tech', 'Health', 'Science', 'Entertainment', 'Education']}
            else:
                query['category'] = category
        
        # Additional source type filtering
        if source_type == 'local':
            query['is_local_source'] = True
        elif source_type == 'national':
            query['is_local_source'] = False
        
        # For "all" category (Latest News), use interleaved ordering: Local, Local, UK, UK
        if (not category or category == 'all') and not source_type:
            # Fetch local and UK articles separately
            local_articles = await db.articles.find(
                {'is_local_source': True},
                {
                    '_id': 1, 'title': 1, 'content': 1, 'summary': 1, 'category': 1,
                    'author': 1, 'publishedDate': 1, 'image': 1, 'tags': 1,
                    'featured': 1, 'source': 1, 'source_url': 1, 'scope': 1, 'is_local_source': 1
                }
            ).sort('publishedDate', -1).limit(limit).to_list(limit)
            
            uk_articles = await db.articles.find(
                {'is_local_source': {'$ne': True}},
                {
                    '_id': 1, 'title': 1, 'content': 1, 'summary': 1, 'category': 1,
                    'author': 1, 'publishedDate': 1, 'image': 1, 'tags': 1,
                    'featured': 1, 'source': 1, 'source_url': 1, 'scope': 1, 'is_local_source': 1
                }
            ).sort('publishedDate', -1).limit(limit).to_list(limit)
            
            # Interleave: 2 local, 2 UK, repeat
            articles = []
            local_idx = 0
            uk_idx = 0
            
            while len(articles) < limit and (local_idx < len(local_articles) or uk_idx < len(uk_articles)):
                # Add 2 local articles
                for _ in range(2):
                    if local_idx < len(local_articles) and len(articles) < limit:
                        articles.append(local_articles[local_idx])
                        local_idx += 1
                
                # Add 2 UK articles
                for _ in range(2):
                    if uk_idx < len(uk_articles) and len(articles) < limit:
                        articles.append(uk_articles[uk_idx])
                        uk_idx += 1
            
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
        unique_articles = []
        for article in articles:
            article['id'] = str(article['_id'])
            del article['_id']
            
            # Skip duplicate articles by ID
            if article['id'] in seen_ids:
                continue
            seen_ids.add(article['id'])
            
            if 'created_at' in article:
                del article['created_at']
            # Clean word count from content
            if 'content' in article:
                article['content'] = clean_word_count(article['content'])
            
            # Add Cheshire priority flags and location
            title = article.get('title', '')
            content = article.get('content', '')
            article['is_priority_cheshire'] = is_priority_cheshire_article(title, content)
            article['is_secondary_cheshire'] = is_secondary_cheshire_article(title, content)
            article['priority_location'] = get_article_priority_location(title, content)
            
            unique_articles.append(article)
        
        # Cache the result for homepage requests
        if not search and skip == 0 and limit == 20 and not category:
            api_cache.set(cache_key, unique_articles)
        
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
            {"$sort": {"views": -1}},
            {"$limit": limit}
        ]
        
        view_counts = await db.article_views.aggregate(pipeline).to_list(limit)
        
        if not view_counts:
            # Fallback to articles with highest view_count field
            articles = await db.articles.find(
                {},
                {"_id": 0, "id": 1, "title": 1, "image": 1, "category": 1, "view_count": 1}
            ).sort("view_count", -1).limit(limit).to_list(limit)
            
            return {
                "success": True,
                "period": period,
                "articles": articles
            }
        
        # Get article details for top viewed
        articles = []
        
        for vc in view_counts:
            article_id = vc["_id"]
            # Try to find by ObjectId first, then by id field
            article = None
            try:
                article = await db.articles.find_one({"_id": ObjectId(article_id)})
            except:
                pass
            
            if not article:
                article = await db.articles.find_one({"id": article_id})
            
            if article:
                articles.append({
                    "id": str(article.get("_id", article.get("id", ""))),
                    "title": article.get("title", ""),
                    "image": article.get("image", ""),
                    "category": article.get("category", ""),
                    "views": vc["views"]
                })
        
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
\
        # -------------------------------
        # LOCAL DEV – single article from mock store
        # -------------------------------
        if LOCAL_DEV_NO_DB:
            seed_local_articles_if_needed()
            article = next((a for a in LOCAL_DEV_ARTICLES if a.get("id") == article_id), None)
            if not article:
                raise HTTPException(status_code=404, detail="Article not found")
            return article

        article = None
        
        # First try to find by custom 'id' field (UUID format) in main collection
        article = await db.articles.find_one({'id': article_id})
        
        # If not found, try MongoDB ObjectId in main collection
        if not article:
            try:
                article = await db.articles.find_one({'_id': ObjectId(article_id)})
            except:
                pass  # Invalid ObjectId format, that's fine
        
        # If still not found, search in archived_articles collection
        # This ensures old shared links (e.g., Facebook posts) continue to work
        if not article:
            article = await db.archived_articles.find_one({'id': article_id})
            
        if not article:
            try:
                article = await db.archived_articles.find_one({'_id': ObjectId(article_id)})
            except:
                pass  # Invalid ObjectId format, that's fine
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        article['id'] = str(article.get('id', article['_id']))
        del article['_id']
        if 'created_at' in article:
            del article['created_at']
        
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
    
    try:
        # Search in main articles collection first
        article = await db.articles.find_one({'_id': ObjectId(article_id)})
        
        # If not found, search in archived_articles collection
        if not article:
            article = await db.archived_articles.find_one({'_id': ObjectId(article_id)})
        
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
        
        title = article.get('title', 'Cheshire Today')
        description = article.get('content', '')[:200].replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        image = article.get('image', '')
        article_url = f"https://cheshiretoday.co.uk/article/{article_id}"
        share_url = f"https://cheshiretoday.co.uk/api/share/{article_id}"
        
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
            <meta property="fb:app_id" content="2091422248085004">
            
            <!-- Twitter Card -->
            <meta name="twitter:card" content="summary_large_image">
            <meta name="twitter:image" content="{image}">
            <meta name="twitter:url" content="{share_url}">
            <meta name="twitter:title" content="{title}">
            <meta name="twitter:description" content="{description}">
            <meta name="twitter:site" content="@CheshireToday">
            
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
    Server-side rendered HTML page optimized for search engine crawlers.
    Returns full article content with proper meta tags for indexing.
    This helps Google index article pages properly since React is client-rendered.
    """
    from fastapi.responses import HTMLResponse
    
    try:
        # Search in main articles collection first
        article = None
        try:
            article = await db.articles.find_one({'_id': ObjectId(article_id)})
        except:
            pass
        
        if not article:
            article = await db.articles.find_one({'id': article_id})
        
        # If not found, search in archived_articles collection
        if not article:
            try:
                article = await db.archived_articles.find_one({'_id': ObjectId(article_id)})
            except:
                pass
        
        if not article:
            article = await db.archived_articles.find_one({'id': article_id})
        
        if not article:
            return HTMLResponse(status_code=404, content="""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="robots" content="noindex">
                <title>Article Not Found | Cheshire Today</title>
            </head>
            <body><h1>Article Not Found</h1></body>
            </html>
            """)
        
        # Get article data
        article_id_str = str(article.get('id', article.get('_id', '')))
        title = article.get('title', 'Cheshire Today Article')
        content = article.get('content', '')
        description = content[:160].replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;') if content else title
        image = article.get('image', 'https://cheshiretoday.co.uk/social-share.jpg')
        category = article.get('category', 'News')
        author = article.get('author', 'Cheshire Today')
        published_date = article.get('publishedDate', article.get('created_at', ''))
        canonical_url = f"https://cheshiretoday.co.uk/article/{article_id_str}"
        
        # Format content for HTML (basic paragraph handling)
        formatted_content = content.replace('\n\n', '</p><p>').replace('\n', '<br>')
        if formatted_content and not formatted_content.startswith('<p>'):
            formatted_content = f'<p>{formatted_content}</p>'
        
        # Escape HTML in title
        safe_title = title.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Build JSON-LD structured data for Google
        json_ld = {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": title,
            "description": description,
            "image": [image] if image else [],
            "datePublished": published_date,
            "dateModified": published_date,
            "author": {
                "@type": "Organization",
                "name": author
            },
            "publisher": {
                "@type": "NewsMediaOrganization",
                "name": "Cheshire Today",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://cheshiretoday.co.uk/logo.png"
                }
            },
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": canonical_url
            },
            "articleSection": category
        }
        
        import json
        json_ld_str = json.dumps(json_ld)
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title} | Cheshire Today</title>
    <meta name="description" content="{description}">
    <meta name="author" content="{author}">
    <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
    
    <!-- Canonical URL - Critical for SEO -->
    <link rel="canonical" href="{canonical_url}">
    
    <!-- Open Graph / Facebook -->
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
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:url" content="{canonical_url}">
    <meta name="twitter:title" content="{safe_title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{image}">
    <meta name="twitter:site" content="@CheshireToday">
    
    <!-- Structured Data for Google -->
    <script type="application/ld+json">{json_ld_str}</script>
    
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
            <time datetime="{published_date}">{published_date[:10] if published_date else ''}</time>
        </div>
        {f'<img src="{image}" alt="{safe_title}">' if image else ''}
        <div class="content">
            {formatted_content}
        </div>
        <a href="{canonical_url}" class="cta">Read Full Article on Cheshire Today</a>
    </article>
</body>
</html>"""
        
        return HTMLResponse(content=html_content, headers={
            "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
            "X-Robots-Tag": "index, follow"
        })
        
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


@api_router.post("/clean-all-articles")
async def clean_all_articles():
    """Clean markdown formatting from all existing articles in the database"""
    try:
        articles = await db.articles.find({}).to_list(1000)
        cleaned_count = 0
        
        for article in articles:
            original_title = article.get('title', '')
            original_content = article.get('content', '')
            
            cleaned_title = clean_article_content(original_title)
            cleaned_content = clean_article_content(original_content)
            
            # Only update if changes were made
            if cleaned_title != original_title or cleaned_content != original_content:
                await db.articles.update_one(
                    {"_id": article["_id"]},
                    {"$set": {"title": cleaned_title, "content": cleaned_content}}
                )
                cleaned_count += 1
        
        logger.info(f"Cleaned {cleaned_count} articles")
        return {"success": True, "articles_cleaned": cleaned_count, "total_articles": len(articles)}
    
    except Exception as e:
        logger.error(f"Error cleaning articles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/article-meta/{article_id}")
async def get_article_meta(article_id: str):
    """Get article metadata for social sharing. Also searches archived articles."""
    try:
        # Use environment variable for base URL (works across all deployment environments)
        base_url = os.environ.get('PUBLIC_URL', 'https://cheshiretoday.co.uk')
        
        # Search in main articles collection first
        article = await db.articles.find_one({"_id": ObjectId(article_id)})
        
        # If not found, search in archived_articles collection
        if not article:
            article = await db.archived_articles.find_one({"_id": ObjectId(article_id)})
        
        if not article:
            return {
                "title": "Cheshire Today - Local News",
                "description": "Stay informed with the latest news from Cheshire",
                "image": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1200&h=630&fit=crop",
                "url": base_url
            }
        
        return {
            "title": article.get('title', 'Cheshire Today Article'),
            "description": article.get('content', '')[:200],
            "image": article.get('image', 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1200&h=630&fit=crop'),
            "url": f"{base_url}/article/{article_id}",
            "author": article.get('author', 'Cheshire Today'),
            "publishedDate": article.get('publishedDate', article.get('created_at'))
        }
    except Exception as e:
        logging.error(f"Error fetching article meta: {str(e)}")
        # Use environment variable for base URL (works across all deployment environments)
        base_url = os.environ.get('PUBLIC_URL', 'https://cheshiretoday.co.uk')
        return {
            "title": "Cheshire Today - Local News",
            "description": "Stay informed with the latest news from Cheshire",
            "image": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1200&h=630&fit=crop",
            "url": base_url
        }

@api_router.delete("/articles/{article_id}")
async def delete_article(article_id: str):
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
async def subscribe_newsletter(request: SubscribeRequest):
    """Subscribe to newsletter with optional preferences"""
    try:
        email = request.email.lower().strip()
        
        # Check if email already exists
        existing = await db.subscribers.find_one({"email": email}, {"_id": 0})
        
        if existing:
            # Update preferences if provided
            if request.preferences:
                await db.subscribers.update_one(
                    {"email": email},
                    {"$set": {"preferences": request.preferences}}
                )
            return SubscribeResponse(
                success=True,
                message="You're already subscribed to our newsletter!"
            )
        
        # Default preferences
        default_preferences = {
            "categories": ["Local News", "UK News", "Business", "Health", "Sports", "Tech", "Entertainment"],
            "frequency": "daily"
        }
        
        # Create new subscriber with preferences (January 2026 update)
        subscriber = {
            "id": str(uuid.uuid4()),
            "email": email,
            "subscribed_at": datetime.now(timezone.utc).isoformat(),
            "active": True,
            "preferences": request.preferences if request.preferences else default_preferences,
            # New tiered email preferences - daily_brief enabled by default
            "daily_brief": True,
            "weekly_roundup": False,
            "breaking_news": False
        }
        
        await db.subscribers.insert_one(subscriber)
        
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
            message="Thank you for subscribing! You'll receive The Daily Brief every morning at 7:30 AM."
        )
        
    except Exception as e:
        logger.error(f"Error subscribing email: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to subscribe. Please try again.")

# =====================================================================================
# NEWSLETTER PREFERENCES ENDPOINTS
# =====================================================================================

@api_router.get("/newsletter/preferences/{email}")
async def get_newsletter_preferences(email: str):
    """Get newsletter preferences for an email - includes new tiered preferences (Jan 2026)"""
    try:
        email = email.lower().strip()
        subscriber = await db.subscribers.find_one({"email": email}, {"_id": 0})
        
        if not subscriber:
            return {
                "found": False,
                "email": email,
                "message": "Email not found in subscriber list",
                "preferences": None
            }
        
        return {
            "found": True,
            "success": True,
            "email": email,
            "preferences": {
                # New tiered email preferences (Jan 2026)
                "daily_brief": subscriber.get("daily_brief", True),
                "weekly_roundup": subscriber.get("weekly_roundup", False),
                "breaking_news": subscriber.get("breaking_news", False),
                # Legacy preferences (kept for backwards compatibility)
                "categories": subscriber.get("preferences", {}).get("categories", ["Local News", "UK News"]),
                "frequency": subscriber.get("preferences", {}).get("frequency", "daily")
            },
            "subscribed_at": str(subscriber.get("subscribed_at")) if subscriber.get("subscribed_at") else None
        }
    except Exception as e:
        logger.error(f"Error getting preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get preferences")

@api_router.put("/newsletter/preferences")
async def update_newsletter_preferences(request: UpdatePreferencesRequest):
    """Update newsletter preferences for a subscriber"""
    try:
        email = request.email.lower().strip()
        
        # Check if subscriber exists
        existing = await db.subscribers.find_one({"email": email})
        if not existing:
            raise HTTPException(status_code=404, detail="Subscriber not found. Please subscribe first.")
        
        # Update preferences
        await db.subscribers.update_one(
            {"email": email},
            {"$set": {
                "preferences": {
                    "categories": request.preferences.categories,
                    "frequency": request.preferences.frequency
                },
                "preferences_updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        logger.info(f"Updated newsletter preferences for: {email}")
        
        return {
            "success": True,
            "message": "Your newsletter preferences have been updated!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update preferences")


@api_router.post("/newsletter/email-preferences")
async def update_email_preferences(request: PreferencesUpdateRequest):
    """
    Update email tier preferences (Daily Brief, Weekly Roundup, Breaking News).
    If all preferences are disabled, user still stays subscribed but won't receive any emails.
    """
    try:
        email = request.email.lower().strip()
        
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        # Check if subscriber exists
        subscriber = await db.subscribers.find_one({"email": email})
        
        if not subscriber:
            raise HTTPException(status_code=404, detail="Email not found. Please subscribe first.")
        
        # Update tiered preferences
        await db.subscribers.update_one(
            {"email": email},
            {"$set": {
                "daily_brief": request.daily_brief,
                "weekly_roundup": request.weekly_roundup,
                "breaking_news": request.breaking_news,
                "preferences_updated_at": datetime.now(timezone.utc)
            }}
        )
        
        # If ALL preferences are False, log it
        if not request.daily_brief and not request.weekly_roundup and not request.breaking_news:
            logger.info(f"Subscriber {email[:3]}*** disabled all email preferences")
        
        return {
            "success": True,
            "message": "Your email preferences have been updated.",
            "preferences": {
                "daily_brief": request.daily_brief,
                "weekly_roundup": request.weekly_roundup,
                "breaking_news": request.breaking_news
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating email preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update preferences")

@api_router.get("/newsletter/categories")
async def get_available_categories():
    """Get available newsletter subscription options (January 2026 update)"""
    return {
        "subscription_types": [
            {
                "id": "daily_brief",
                "name": "The Daily Brief",
                "description": "Top Cheshire stories every morning at 7:30 AM",
                "frequency": "Daily",
                "default": True
            },
            {
                "id": "weekly_roundup",
                "name": "The Weekly Roundup",
                "description": "Curated digest of the week's best content",
                "frequency": "Every Sunday at 9:00 AM",
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
            {"id": "UK News", "name": "UK News", "description": "National news from across the UK"},
            {"id": "Business", "name": "Business", "description": "Business & economy updates"},
            {"id": "Health", "name": "Health", "description": "Health & NHS news"},
            {"id": "Sports", "name": "Sports", "description": "Sports coverage"},
            {"id": "Tech", "name": "Tech", "description": "Technology news"},
            {"id": "Science", "name": "Science", "description": "Science & research"},
            {"id": "Entertainment", "name": "Entertainment", "description": "Entertainment & celebrity news"}
        ]
    }


class UpdateEmailPreferencesRequest(BaseModel):
    email: str
    daily_brief: Optional[bool] = None
    weekly_roundup: Optional[bool] = None
    breaking_news: Optional[bool] = None


@api_router.put("/newsletter/email-preferences")
async def update_email_preferences(request: UpdateEmailPreferencesRequest):
    """Update subscriber's email preferences (Daily Brief, Weekly Roundup, Breaking News)"""
    try:
        email = request.email.lower().strip()
        
        # Check if subscriber exists
        existing = await db.subscribers.find_one({"email": email})
        if not existing:
            raise HTTPException(status_code=404, detail="Subscriber not found")
        
        # Build update object
        update_data = {}
        if request.daily_brief is not None:
            update_data["daily_brief"] = request.daily_brief
        if request.weekly_roundup is not None:
            update_data["weekly_roundup"] = request.weekly_roundup
        if request.breaking_news is not None:
            update_data["breaking_news"] = request.breaking_news
        
        if update_data:
            await db.subscribers.update_one(
                {"email": email},
                {"$set": update_data}
            )
        
        logger.info(f"Updated email preferences for: {email}")
        
        return {
            "success": True,
            "email": email,
            "preferences": update_data,
            "message": "Your email preferences have been updated!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating email preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/newsletter/email-preferences/{email}")
async def get_email_preferences(email: str):
    """Get subscriber's current email preferences"""
    try:
        email = email.lower().strip()
        subscriber = await db.subscribers.find_one({"email": email}, {"_id": 0})
        
        if not subscriber:
            raise HTTPException(status_code=404, detail="Subscriber not found")
        
        return {
            "email": email,
            "daily_brief": subscriber.get("daily_brief", True),  # Default to True
            "weekly_roundup": subscriber.get("weekly_roundup", False),
            "breaking_news": subscriber.get("breaking_news", False),
            "subscribed_at": subscriber.get("subscribed_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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


# =====================================================================================
# PUBLIC NEWSLETTER ENDPOINTS (No auth required)
# =====================================================================================

@api_router.post("/newsletter/unsubscribe")
async def unsubscribe_newsletter(request: UnsubscribeRequest):
    """
    Public endpoint to unsubscribe from newsletter.
    Completely removes the subscriber from the database.
    """
    try:
        email = request.email.lower().strip()
        
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        # Find and delete the subscriber
        result = await db.subscribers.delete_one({"email": email})
        
        if result.deleted_count == 0:
            # Still return success - don't reveal if email exists
            logger.info(f"Unsubscribe attempt for non-existent email: {email[:3]}***")
            return {
                "success": True,
                "message": "If you were subscribed, you have been unsubscribed successfully."
            }
        
        logger.info(f"Subscriber unsubscribed: {email[:3]}***")
        return {
            "success": True,
            "message": "You have been successfully unsubscribed from all Cheshire Today emails."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsubscribing: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process unsubscribe request")


@api_router.get("/newsletter/preferences/{email}")
async def get_newsletter_preferences(email: str):
    """
    Get current newsletter preferences for an email.
    Returns preferences if found, or defaults if not.
    """
    try:
        email = email.lower().strip()
        subscriber = await db.subscribers.find_one({"email": email})
        
        if not subscriber:
            return {
                "found": False,
                "email": email,
                "message": "Email not found in subscriber list",
                "preferences": None
            }
        
        return {
            "found": True,
            "email": email,
            "preferences": {
                "daily_brief": subscriber.get("daily_brief", True),
                "weekly_roundup": subscriber.get("weekly_roundup", False),
                "breaking_news": subscriber.get("breaking_news", False)
            },
            "subscribed_at": str(subscriber.get("subscribed_at")) if subscriber.get("subscribed_at") else None
        }
        
    except Exception as e:
        logger.error(f"Error getting preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get preferences")


@api_router.post("/newsletter/preferences")
async def update_newsletter_preferences(request: PreferencesUpdateRequest):
    """
    Update newsletter preferences for a subscriber.
    If all preferences are disabled, effectively unsubscribes them from all emails.
    """
    try:
        email = request.email.lower().strip()
        
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        # Check if subscriber exists
        subscriber = await db.subscribers.find_one({"email": email})
        
        if not subscriber:
            raise HTTPException(status_code=404, detail="Email not found. Please subscribe first.")
        
        # Update preferences
        await db.subscribers.update_one(
            {"email": email},
            {"$set": {
                "daily_brief": request.daily_brief,
                "weekly_roundup": request.weekly_roundup,
                "breaking_news": request.breaking_news,
                "preferences_updated_at": datetime.now(timezone.utc)
            }}
        )
        
        # If ALL preferences are False, log it (user might as well unsubscribe)
        if not request.daily_brief and not request.weekly_roundup and not request.breaking_news:
            logger.info(f"Subscriber {email[:3]}*** disabled all email preferences")
        
        return {
            "success": True,
            "message": "Your email preferences have been updated.",
            "preferences": {
                "daily_brief": request.daily_brief,
                "weekly_roundup": request.weekly_roundup,
                "breaking_news": request.breaking_news
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update preferences")


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

@api_router.get("/admin/articles")
async def get_admin_articles(skip: int = 0, limit: int = 50, authorized: bool = Depends(get_admin_auth)):
    """Get all articles for admin dashboard with full details. Requires admin authentication."""
    try:
        articles = await db.articles.find(
            {}, {"_id": 0}
        ).sort("publishedDate", -1).skip(skip).limit(limit).to_list(limit)
        
        total = await db.articles.count_documents({})
        return {"articles": articles, "total": total, "skip": skip, "limit": limit}
    except Exception as e:
        logger.error(f"Error getting admin articles: {str(e)}")
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
        default_image = "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=800&h=500&fit=crop"
        
        # Auto-detect location from title and content
        detected_location = get_article_priority_location(article.title, article.content)
        
        # Build tags list
        tags = article.tags or []
        if detected_location:
            location_tag = detected_location.capitalize()
            if location_tag not in tags:
                tags.append(location_tag)
        
        # Create article document
        article_doc = {
            "id": article_id,
            "title": article.title,
            "content": article.content,
            "category": article.category,
            "author": article.author or "Cheshire Today",
            "publishedDate": datetime.now(timezone.utc).isoformat(),
            "image": article.image or default_image,
            "tags": tags,
            "featured": article.featured or False,
            "source": "Manual Entry",
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
        
        # Check if article exists
        existing = await db.articles.find_one({"id": article_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Auto-detect location from updated title and content
        detected_location = get_article_priority_location(article.title, article.content)
        
        # Build update document
        update_doc = {
            "title": article.title,
            "content": article.content,
            "category": article.category,
            "author": article.author or existing.get("author", "Cheshire Today"),
            "image": article.image or existing.get("image"),
            "tags": article.tags or existing.get("tags", []),
            "featured": article.featured if article.featured is not None else existing.get("featured", False),
            "scope": article.scope or existing.get("scope", "cheshire"),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Update location if detected (or clear if no longer matches any location)
        if detected_location:
            update_doc["location"] = detected_location
            # Add location to tags if not already present
            location_tag = detected_location.capitalize()
            if location_tag not in update_doc["tags"]:
                update_doc["tags"].append(location_tag)
            logger.info(f"Auto-detected location '{detected_location}' for article: {article.title}")
        else:
            # Clear location if article no longer matches any specific location
            update_doc["location"] = None
        
        # Update in database
        await db.articles.update_one(
            {"id": article_id},
            {"$set": update_doc}
        )
        
        logger.info(f"Article updated: {article.title}")
        
        return {
            "success": True,
            "message": "Article updated successfully",
            "location_detected": detected_location
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating article: {str(e)}")
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
            {"$set": {"archived": True, "archived_at": datetime.now(timezone.utc).isoformat()}}
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

@api_router.get("/admin/articles/archived")
async def get_archived_articles(
    skip: int = 0,
    limit: int = 50,
    auth: bool = Depends(get_admin_auth)
):
    """Get all archived articles from both legacy (archived flag) and new (archived_articles collection) systems"""
    try:
        all_archived = []
        
        # Get articles from main collection with archived flag (legacy system)
        legacy_archived = await db.articles.find(
            {"archived": True},
            {"_id": 1, "id": 1, "title": 1, "category": 1, "publishedDate": 1, "archived_at": 1, "image": 1, "archive_reason": 1}
        ).to_list(None)
        
        for article in legacy_archived:
            article['id'] = str(article.get('id', article['_id']))
            article['archive_source'] = 'legacy'
            if '_id' in article:
                del article['_id']
            all_archived.append(article)
        
        # Get articles from archived_articles collection (new system)
        new_archived = await db.archived_articles.find(
            {},
            {"_id": 1, "id": 1, "title": 1, "category": 1, "publishedDate": 1, "archived_at": 1, "image": 1, "archive_reason": 1}
        ).to_list(None)
        
        for article in new_archived:
            article['id'] = str(article.get('id', article['_id']))
            article['archive_source'] = 'collection'
            if '_id' in article:
                del article['_id']
            all_archived.append(article)
        
        # Sort by archived_at descending
        all_archived.sort(key=lambda x: x.get('archived_at', ''), reverse=True)
        
        # Apply pagination
        total = len(all_archived)
        paginated = all_archived[skip:skip + limit]
        
        return {"articles": paginated, "total": total}
    except Exception as e:
        logger.error(f"Error getting archived articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/admin/articles/bulk-archive")
async def bulk_archive_articles(
    days_old: int = 30,
    auth: bool = Depends(get_admin_auth)
):
    """Archive all articles older than specified days"""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
        
        result = await db.articles.update_many(
            {
                "publishedDate": {"$lt": cutoff_date.isoformat()},
                "$or": [{"archived": {"$exists": False}}, {"archived": False}]
            },
            {"$set": {"archived": True, "archived_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {
            "success": True,
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
            "Local News", "Sports", "Tech", "Health", "Entertainment",
            "UK News", "Business", "Science", "Education", "default"
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
    """Handle Stripe webhooks"""
    try:
        body = await request.body()
        signature = request.headers.get("Stripe-Signature")
        
        host_url = str(request.base_url).rstrip('/')
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
        
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        logger.info(f"Stripe webhook: {webhook_response.event_type} for session {webhook_response.session_id}")
        
        if webhook_response.payment_status == "paid":
            # Find and update the transaction
            transaction = await db.payment_transactions.find_one({"session_id": webhook_response.session_id})
            if transaction and transaction.get("payment_status") != "completed":
                await db.payment_transactions.update_one(
                    {"session_id": webhook_response.session_id},
                    {"$set": {"payment_status": "completed", "completed_at": datetime.utcnow()}}
                )
                
                job_id = webhook_response.metadata.get("job_id") or transaction.get("job_id")
                if job_id:
                    package_id = webhook_response.metadata.get("package_id") or transaction.get("package_id")
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
                "avg_engagement_per_post": round(total_engagement / len(posts), 1) if posts else 0
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
    Analyzes which categories and topics perform best.
    """
    try:
        # Get our posting history with article details
        recent_logs = await db.facebook_post_log.find({}).sort("posted_at", -1).limit(100).to_list(100)
        
        if not recent_logs:
            return {
                "success": True,
                "message": "Not enough data yet. Post more articles to get insights.",
                "insights": []
            }
        
        # Get article details for posted items
        article_ids = [log.get("article_id") for log in recent_logs if log.get("article_id")]
        
        # Fetch engagement from Facebook
        engagement_data = await facebook_service.fetch_recent_posts_engagement(limit=30)
        posts = engagement_data.get("posts", [])
        
        # Analyze by category (from our logs)
        category_stats = {}
        for log in recent_logs:
            article_id = log.get("article_id")
            if article_id:
                # Try to get article to find category
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
        
        # Top engagement insight
        if posts:
            top_post = posts[0]
            insights.append({
                "type": "top_performer",
                "icon": "🏆",
                "title": "Top Performing Post",
                "description": f'"{top_post.get("title", "Unknown")}" got {top_post.get("likes", 0)} likes, {top_post.get("comments", 0)} comments, {top_post.get("shares", 0)} shares',
                "engagement_score": top_post.get("engagement_score", 0)
            })
        
        # Category insights
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
        
        # Posting frequency insight
        if recent_logs:
            from datetime import timedelta
            week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            
            def make_aware(dt):
                """Ensure datetime is timezone-aware"""
                if dt is None:
                    return None
                if isinstance(dt, datetime):
                    if dt.tzinfo is None:
                        return dt.replace(tzinfo=timezone.utc)
                    return dt
                return None
            
            posts_this_week = len([l for l in recent_logs if l.get("posted_at") and make_aware(l["posted_at"]) and make_aware(l["posted_at"]) > week_ago])
            insights.append({
                "type": "frequency",
                "icon": "📅",
                "title": "Posting Frequency",
                "description": f"{posts_this_week} posts in the last 7 days",
                "recommendation": "Aim for 3-4 posts per day at peak times (8 AM, 1 PM, 7 PM) for best engagement."
            })
        
        # Time-based insight
        if posts:
            avg_engagement = sum(p.get("engagement_score", 0) for p in posts) / len(posts)
            insights.append({
                "type": "engagement_summary",
                "icon": "💡",
                "title": "Average Engagement",
                "description": f"Average engagement score: {round(avg_engagement, 1)}",
                "recommendation": "Posts with local location mentions tend to perform better. Try including Chester, Knutsford, or Warrington in headlines."
            })
        
        return {
            "success": True,
            "total_posts_analyzed": len(recent_logs),
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
        # Get client IP for deduplication
        client_ip = request.client.host if request.client else "unknown"
        
        # Check if this IP viewed this article in last hour
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        existing_view = await db.article_views.find_one({
            "article_id": article_id,
            "ip_hash": hashlib.md5(client_ip.encode()).hexdigest(),
            "viewed_at": {"$gte": one_hour_ago}
        })
        
        if existing_view:
            return {"success": True, "counted": False, "message": "View already counted"}
        
        # Record the view
        await db.article_views.insert_one({
            "article_id": article_id,
            "ip_hash": hashlib.md5(client_ip.encode()).hexdigest(),
            "viewed_at": datetime.now(timezone.utc)
        })
        
        # Increment view counter on article
        await db.articles.update_one(
            {"$or": [{"_id": ObjectId(article_id)}, {"id": article_id}]},
            {"$inc": {"view_count": 1}}
        )
        
        return {"success": True, "counted": True}
        
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


async def send_subscriber_milestone_email(subscriber_count: int):
    """Send email alert when subscriber milestones are reached"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.office365.com')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_username = os.environ.get('SMTP_USERNAME')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        admin_email = os.environ.get('ADMIN_EMAIL', 'news@cheshiretoday.co.uk')
        
        if not smtp_username or not smtp_password:
            logger.warning("SMTP not configured - skipping milestone email")
            return
        
        # Create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🎉 Cheshire Today: {subscriber_count} Push Notification Subscribers!"
        msg['From'] = smtp_username
        msg['To'] = admin_email
        
        # Milestone messages
        milestone_messages = {
            10: "Your first 10 subscribers! You're building an engaged audience.",
            25: "25 subscribers! Your breaking news alerts are gaining traction.",
            50: "50 subscribers! Half way to your first hundred!",
            100: "🎯 100 subscribers! A fantastic milestone - triple digits!",
            250: "250 subscribers! Your audience is growing rapidly.",
            500: "🚀 500 subscribers! You've built a significant reach.",
            1000: "🏆 1,000 subscribers! You now have a powerful notification channel!",
            2500: "⭐ 2,500 subscribers! Incredible growth!",
            5000: "🔥 5,000 subscribers! You're reaching a massive local audience!",
            10000: "👑 10,000 subscribers! Cheshire Today is a local news powerhouse!"
        }
        
        message = milestone_messages.get(subscriber_count, f"You've reached {subscriber_count} subscribers!")
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #10b981, #059669); border-radius: 10px;">
                <h1 style="color: white; margin: 0;">🔔 Subscriber Milestone!</h1>
            </div>
            
            <div style="padding: 30px 20px; text-align: center;">
                <h2 style="font-size: 48px; color: #10b981; margin: 0;">{subscriber_count:,}</h2>
                <p style="font-size: 18px; color: #666;">Push Notification Subscribers</p>
            </div>
            
            <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p style="font-size: 16px; color: #333; margin: 0;">{message}</p>
            </div>
            
            <div style="text-align: center; padding: 20px;">
                <p style="color: #666; font-size: 14px;">
                    These subscribers will receive instant alerts when you send breaking news notifications.
                </p>
                <a href="https://cheshiretoday.co.uk/admin" 
                   style="display: inline-block; padding: 12px 24px; background: #10b981; color: white; text-decoration: none; border-radius: 6px; margin-top: 10px;">
                    Go to Admin Dashboard
                </a>
            </div>
            
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
            <p style="text-align: center; color: #9ca3af; font-size: 12px;">
                Cheshire Today - Your Local News Source
            </p>
        </body>
        </html>
        """
        
        text_content = f"""
        🔔 Subscriber Milestone!
        
        {subscriber_count:,} Push Notification Subscribers
        
        {message}
        
        These subscribers will receive instant alerts when you send breaking news notifications.
        
        Visit https://cheshiretoday.co.uk/admin to manage your notifications.
        """
        
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        logger.info(f"🎉 Milestone email sent: {subscriber_count} subscribers!")
        
        # Also log to database for tracking
        await db.milestone_alerts.insert_one({
            "type": "push_subscribers",
            "count": subscriber_count,
            "sent_at": datetime.now(timezone.utc),
            "email_sent_to": admin_email
        })
        
    except Exception as e:
        logger.error(f"Error sending milestone email: {str(e)}")


@api_router.post("/push/unsubscribe")
async def unsubscribe_from_push(request: Request):
    """Unsubscribe from push notifications"""
    try:
        data = await request.json()
        endpoint = data.get("endpoint")
        
        if not endpoint:
            return {"success": False, "error": "Missing endpoint"}
        
        await db.push_subscriptions.update_one(
            {"endpoint": endpoint},
            {"$set": {"active": False}}
        )
        
        return {"success": True, "message": "Unsubscribed from push notifications"}
        
    except Exception as e:
        logger.error(f"Error unsubscribing from push: {str(e)}")
        return {"success": False, "error": str(e)}


@api_router.get("/push/milestones")
async def get_push_milestones(auth: bool = Depends(get_admin_auth)):
    """Get history of subscriber milestones reached"""
    try:
        milestones = await db.milestone_alerts.find(
            {"type": "push_subscribers"}
        ).sort("sent_at", -1).limit(20).to_list(20)
        
        # Get current count
        current_count = await db.push_subscriptions.count_documents({"active": True})
        
        # Calculate next milestone
        all_milestones = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]
        next_milestone = next((m for m in all_milestones if m > current_count), None)
        subscribers_needed = (next_milestone - current_count) if next_milestone else 0
        
        return {
            "success": True,
            "current_subscribers": current_count,
            "next_milestone": next_milestone,
            "subscribers_to_next": subscribers_needed,
            "milestones_reached": [
                {
                    "count": m.get("count"),
                    "reached_at": m.get("sent_at").isoformat() if m.get("sent_at") else None
                }
                for m in milestones
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting milestones: {str(e)}")
        return {"success": False, "error": str(e)}


@api_router.post("/push/send-breaking-news")
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


@api_router.post("/test-email")
async def test_email_send():
    """Test email sending to verify SMTP configuration"""
    try:
        import os
        test_email = "news@cheshiretoday.co.uk"  # Send test to admin
        
        smtp_host = os.environ.get('SMTP_HOST')
        smtp_port = os.environ.get('SMTP_PORT')
        smtp_user = os.environ.get('SMTP_USER')
        smtp_pass = os.environ.get('SMTP_PASSWORD', '')
        
        logger.info(f"TEST EMAIL - SMTP Config: Host={smtp_host}, Port={smtp_port}, User={smtp_user}, Pass={'***' if smtp_pass else 'MISSING'}")
        
        # Try to send a simple test email with detailed error capture
        try:
            result = email_service._send_email(
                to_email=test_email,
                subject="Cheshire Today - Email Test",
                html_content="<h1>Test Email</h1><p>If you receive this, email sending is working!</p>"
            )
            error_msg = None
        except Exception as send_error:
            result = False
            error_msg = str(send_error)
            logger.error(f"Email send exception: {error_msg}")
        
        return {
            "success": result,
            "test_email": test_email,
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "smtp_user": smtp_user,
            "smtp_password_set": bool(smtp_pass),
            "error": error_msg
        }
    except Exception as e:
        logger.error(f"Test email error: {str(e)}")
        return {"success": False, "error": str(e)}


@api_router.get("/check-subscribers")
async def check_subscribers():
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
            "duplicates": duplicates
        }
    except Exception as e:
        return {"error": str(e)}


@api_router.post("/cleanup-subscribers")
async def cleanup_duplicate_subscribers():
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
async def cleanup_invalid_emails():
    """Remove invalid email addresses from subscribers"""
    import re
    try:
        subscribers = await db.subscribers.find({}, {"_id": 1, "email": 1}).to_list(1000)
        
        email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        invalid_ids = []
        invalid_emails = []
        
        for s in subscribers:
            email = s.get('email', '').strip()
            # Remove if: empty, example.com, invalid format, or test addresses
            if not email or \
               email.endswith('@example.com') or \
               not email_regex.match(email) or \
               'test' in email.lower() and '@cheshiretoday' in email.lower():
                invalid_ids.append(s.get('_id'))
                invalid_emails.append(email)
        
        # Delete invalid subscribers
        deleted_count = 0
        for doc_id in invalid_ids:
            result = await db.subscribers.delete_one({"_id": doc_id})
            deleted_count += result.deleted_count
        
        return {
            "success": True,
            "invalid_removed": deleted_count,
            "invalid_emails": invalid_emails,
            "remaining_subscribers": len(subscribers) - deleted_count
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.post("/send-digest")
async def send_digest_now():
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
                    return {
                        "success": False,
                        "message": f"Daily Brief was already sent {int(time_since)} minutes ago. Wait at least 1 hour before sending again.",
                        "last_sent": sent_at.isoformat(),
                        "subscribers_reached": recent_send.get('success_count', recent_send.get('subscribers_count', 0))
                    }
        
        # Log SMTP config at start for debugging
        logger.info(
            f"SMTP Config Check - Host: {os.environ.get('SMTP_HOST')}, "
            f"Port: {os.environ.get('SMTP_PORT')}, "
            f"User: {os.environ.get('SMTP_USER')}"
        )

        # Get subscribers with daily_brief preference (or all if no preference set - backwards compatibility)
        subscribers = await db.subscribers.find(
            {"$or": [
                {"daily_brief": True},
                {"daily_brief": {"$exists": False}}
            ]},
            {"_id": 0, "email": 1}
        ).to_list(1000)

        if not subscribers:
            logger.info("No subscribers found with daily_brief preference - skipping")
            return

        # Deduplicate emails (case-insensitive) + basic validation
        import re
        email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

        seen_emails = set()
        unique_emails = []

        for s in subscribers:
            email_raw = (s.get("email") or "").strip()
            email_norm = email_raw.lower()

            if not email_raw:
                continue
            if email_norm in seen_emails:
                continue
            if not email_regex.match(email_norm) or email_norm.endswith("@example.com"):
                continue

            seen_emails.add(email_norm)
            unique_emails.append(email_raw)  # keep original case

        subscriber_emails = unique_emails
        logger.info(
            f"Found {len(subscriber_emails)} valid unique subscribers for Daily Brief "
            f"(from {len(subscribers)} candidate records)"
        )

        # ============================================================
        # TEST MODE: During migration, send digest ONLY to one email
        # Set DIGEST_TEST_EMAIL in Render env to enable
        # ============================================================
        test_digest_email = os.environ.get("DIGEST_TEST_EMAIL", "").strip()
        if test_digest_email:
            subscriber_emails = [test_digest_email]
            logger.warning(f"🧪 TEST MODE ENABLED: Digest will be sent ONLY to {test_digest_email}")
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
        
        # Prioritize Local News (including Cheshire locations) first, Sports LAST
        local_keywords = ['local news', 'cheshire', 'crewe', 'macclesfield', 'wilmslow', 'chester', 'warrington', 'nantwich', 'congleton', 'northwich', 'knutsford', 'sandbach', 'middlewich', 'alsager', 'winsford', 'ellesmere port']
        
        def is_local(article):
            category = article.get('category', '').lower()
            title = article.get('title', '').lower()
            content = article.get('content', '').lower()[:500]
            
            for keyword in local_keywords:
                if keyword in category or keyword in title or keyword in content:
                    return True
            return False
        
        def is_sports(article):
            return article.get('category', '').lower() == 'sports'
        
        # Sort: Local News first, then other categories, Sports LAST
        local_news = [a for a in unique_articles if is_local(a)]
        sports_news = [a for a in unique_articles if is_sports(a) and not is_local(a)]
        other_news = [a for a in unique_articles if not is_local(a) and not is_sports(a)]
        
        # Combine: local first, then others, then max 2 sports at the end
        sorted_articles = local_news + other_news + sports_news[:2]
        sorted_articles = sorted_articles[:10]
        
        logger.info(f"Digest: {len(local_news)} local, {len(other_news)} other, {len(sports_news)} sports (max 2 used), sending {len(sorted_articles)} total")
        
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
        
        # Get latest articles
        pipeline = [
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
            {"breaking_news": True},
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


@api_router.get("/email/track/click/{tracking_id}")
async def track_email_click(tracking_id: str, url: str, request: Request):
    """
    Track email link clicks and redirect to target URL.
    """
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
                        "url": url[:500],
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
    return RedirectResponse(url=url, status_code=302)


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
            analytics = None
            if tracking_id:
                analytics = await db.email_analytics.find_one({"tracking_id": tracking_id})
            
            recent_sends.append({
                "sent_at": log.get("sent_at").isoformat() if log.get("sent_at") else None,
                "type": log.get("type", log.get("digest_time", "Unknown")),
                "subscribers": log.get("subscribers_count", 0),
                "delivered": log.get("success_count", 0),
                "opens": analytics.get("opens", 0) if analytics else 0,
                "clicks": analytics.get("clicks", 0) if analytics else 0,
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
        # Get ALL subscribers
        subscribers = await db.subscribers.find({}, {"_id": 0, "email": 1}).to_list(10000)
        
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
            {},
            {"$set": {"daily_brief": True}}
        )
        
        # Log the send
        await db.digest_log.insert_one({
            "sent_at": datetime.now(timezone.utc),
            "digest_time": "Announcement",
            "type": "MigrationAnnouncement",
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


@api_router.get("/")
async def root():
    return {"message": "Cheshire News API"}

# Health check endpoint for Kubernetes (at root level, not under /api)
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes liveness probes - returns immediately"""
    return {"status": "healthy", "service": "cheshire-news"}

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

@app.get("/sitemap.xml")
async def generate_sitemap():
    """Generate dynamic sitemap.xml for Google Search Console"""
    from fastapi.responses import Response
    from datetime import datetime
    import xml.sax.saxutils as saxutils
    
    try:
        # ALWAYS use production domain for sitemap - this is for Google Search Console
        # which indexes cheshiretoday.co.uk, not preview/staging environments
        base_url = 'https://cheshiretoday.co.uk'
        
        # Get recent articles from database (limit to 500 for performance)
        articles = await db.articles.find({}, {'_id': 1, 'publishedDate': 1, 'category': 1, 'image': 1, 'title': 1}).sort('publishedDate', -1).limit(500).to_list(500)
        
        # Start building XML with image namespace
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
        
        # Add homepage
        xml_content += '  <url>\n'
        xml_content += f'    <loc>{base_url}/</loc>\n'
        xml_content += f'    <lastmod>{datetime.utcnow().strftime("%Y-%m-%d")}</lastmod>\n'
        xml_content += '    <changefreq>daily</changefreq>\n'
        xml_content += '    <priority>1.0</priority>\n'
        xml_content += '  </url>\n'
        
        # Add location pages for Local SEO
        locations = ['chester', 'warrington', 'crewe', 'wirral', 'macclesfield', 'stockport', 'runcorn', 'northwich']
        for loc in locations:
            xml_content += '  <url>\n'
            xml_content += f'    <loc>{base_url}/{loc}</loc>\n'
            xml_content += f'    <lastmod>{datetime.utcnow().strftime("%Y-%m-%d")}</lastmod>\n'
            xml_content += '    <changefreq>daily</changefreq>\n'
            xml_content += '    <priority>0.9</priority>\n'
            xml_content += '  </url>\n'
        
        # Add category pages
        categories_list = ['Local News', 'UK News', 'Community', 'Tech', 'Business', 'Finance', 'Health', 'Weather', 'Food', 'Festive', 'Sports', 'Events']
        for category in categories_list:
            xml_content += '  <url>\n'
            xml_content += f'    <loc>{base_url}/category/{category.lower().replace(" ", "-")}</loc>\n'
            xml_content += f'    <lastmod>{datetime.utcnow().strftime("%Y-%m-%d")}</lastmod>\n'
            xml_content += '    <changefreq>daily</changefreq>\n'
            xml_content += '    <priority>0.8</priority>\n'
            xml_content += '  </url>\n'
        
        # Add all articles with images
        for article in articles:
            article_id = str(article['_id'])
            published_date = article.get('publishedDate', datetime.utcnow())
            if isinstance(published_date, str):
                try:
                    published_date = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                except:
                    published_date = datetime.utcnow()
            
            # Get article image and title
            article_image = article.get('image', '')
            article_title = article.get('title', 'Cheshire Today Article')
            
            xml_content += '  <url>\n'
            xml_content += f'    <loc>{saxutils.escape(base_url)}/article/{article_id}</loc>\n'
            xml_content += f'    <lastmod>{published_date.strftime("%Y-%m-%d")}</lastmod>\n'
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
    from datetime import datetime, timedelta
    import xml.sax.saxutils as saxutils
    
    try:
        base_url = 'https://cheshiretoday.co.uk'
        
        # Get articles from last 48 hours (Google News requirement)
        cutoff_date = datetime.utcnow() - timedelta(hours=48)
        
        articles = await db.articles.find(
            {"publishedDate": {"$gte": cutoff_date.isoformat()}},
            {'_id': 1, 'id': 1, 'title': 1, 'publishedDate': 1, 'category': 1}
        ).sort('publishedDate', -1).limit(1000).to_list(1000)
        
        # Build Google News sitemap XML
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        xml_content += '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n'
        
        for article in articles:
            article_id = str(article.get('id', article.get('_id', '')))
            title = saxutils.escape(str(article.get('title', 'News Article'))[:100])
            
            # Parse published date
            pub_date = article.get('publishedDate', '')
            if isinstance(pub_date, str):
                try:
                    pub_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                except:
                    pub_date = datetime.utcnow()
            
            xml_content += '  <url>\n'
            xml_content += f'    <loc>{base_url}/article/{article_id}</loc>\n'
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
@app.get("/rss.xml")
async def generate_rss_feed():
    """Generate RSS feed for news readers and Google News"""
    from fastapi.responses import Response
    import xml.sax.saxutils as saxutils
    
    try:
        # ALWAYS use production domain for RSS feed - this is for Google News and feed readers
        base_url = 'https://cheshiretoday.co.uk'
        
        # Get latest 50 articles
        articles = await db.articles.find(
            {}, 
            {'_id': 0, 'id': 1, 'title': 1, 'content': 1, 'publishedDate': 1, 'category': 1, 'author': 1, 'image': 1}
        ).sort('publishedDate', -1).limit(50).to_list(50)
        
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
            title = saxutils.escape(article.get('title', 'Untitled'))
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
            rss += f'    <link>{base_url}/article/{article_id}</link>\n'
            rss += f'    <guid isPermaLink="true">{base_url}/article/{article_id}</guid>\n'
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
    try:
        # Prefer FREE RSS headlines
        headlines = await fetch_trending_headlines_from_rss(count=5)

        # Optional fallback to Gemini if RSS fails/empty
        if not headlines:
            cheshire = await fetch_trending_headlines("cheshire", count=3)
            uk = await fetch_trending_headlines("uk", count=2)

            headlines = []
            for title, category, source, url in cheshire:
                headlines.append({
                    "headline": title,
                    "category": category,
                    "scope": "cheshire",
                    "source": source,
                    "source_url": url
                })
            for title, category, source, url in uk:
                headlines.append({
                    "headline": title,
                    "category": category,
                    "scope": "uk",
                    "source": source,
                    "source_url": url
                })

        return {"headlines": headlines}

    except Exception as e:
        logger.error(f"Error fetching trending headlines: {str(e)}")
        return {"headlines": []}
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
        # -------------------------------
        # LOCAL DEV – compute from mock articles
        # -------------------------------
        if LOCAL_DEV_NO_DB:
            seed_local_articles_if_needed()
            all_articles = LOCAL_DEV_ARTICLES

            source = next((a for a in all_articles if a.get("id") == article_id), None)
            if not source:
                return []

            category = source.get("category", "")
            source_tags = set(source.get("tags") or [])

            def score(a):
                s = 0
                if a.get("category") == category:
                    s += 10
                a_tags = set(a.get("tags") or [])
                s += len(source_tags.intersection(a_tags)) * 3
                return s

            candidates = [a for a in all_articles if a.get("id") != article_id]
            candidates.sort(key=lambda a: (score(a), a.get("publishedDate", "")), reverse=True)
            return candidates[:limit]
        # -------------------------------

        # -------------------------------
        # DB mode
        # -------------------------------
        article = None
        try:
            article = await db.articles.find_one({"_id": ObjectId(article_id)}, {"_id": 0})
        except Exception:
            pass

        if not article:
            article = await db.articles.find_one({"id": article_id}, {"_id": 0})

        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        category = article.get("category", "")

        query = {"category": category, "id": {"$ne": article_id}}

        related = await db.articles.find(
            query,
            {"_id": 0, "id": 1, "title": 1, "image": 1, "category": 1, "publishedDate": 1},
        ).sort("publishedDate", -1).limit(limit).to_list(limit)

        if len(related) < limit:
            more = await db.articles.find(
                {"id": {"$ne": article_id}, "category": {"$ne": category}},
                {"_id": 0, "id": 1, "title": 1, "image": 1, "category": 1, "publishedDate": 1},
            ).sort("publishedDate", -1).limit(limit - len(related)).to_list(limit - len(related))
            related.extend(more)

        return related

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting related articles: {str(e)}")
        return []
async def serve_article_html(article_id: str):
    """
    Server-side rendered HTML for social media crawlers (Facebook, Twitter, LinkedIn).
    This endpoint serves static HTML with pre-rendered meta tags since crawlers don't execute JavaScript.
    """
    from fastapi.responses import HTMLResponse
    
    try:
        # Fetch article from database - try both ObjectId and string id field
        article = None
        
        # First try to find by _id (ObjectId)
        try:
            article = await db.articles.find_one({"_id": ObjectId(article_id)}, {"_id": 0})
        except:
            pass
        
        # If not found, try to find by 'id' field (string)
        if not article:
            article = await db.articles.find_one({"id": article_id}, {"_id": 0})
        
        # Use environment variable for base URL (works across all deployment environments)
        base_url = os.environ.get('PUBLIC_URL', 'https://cheshiretoday.co.uk')
        
        if not article:
            # Return default meta tags if article not found
            title = "Cheshire Today - Local News & Updates"
            description = "Stay informed with the latest news from Cheshire and across the UK."
            image = "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1200&h=630&fit=crop&auto=format"
            share_url = base_url
            app_url = base_url
        else:
            title = article.get('title', 'Cheshire Today Article')
            description = article.get('content', '')[:200]
            image = article.get('image', 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1200&h=630&fit=crop&auto=format')
            # Use clean production domain URL for og:url (what users see when shared)
            # CRITICAL: Point og:url to the API ENDPOINT (server-side rendered HTML), not the frontend.
            # This ensures Facebook scraper sees this exact HTML again, instead of React's blank index.html
            share_url = f"{base_url}/api/article/{article_id}"
            
            # Use regular URL for user redirect (React app will handle routing)
            # This MUST point to the article page, NOT the homepage
            app_url = f"{base_url}/article/{article_id}"
        
        # Generate static HTML with meta tags for social media crawlers
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | Cheshire Today</title>
    
    <!-- Primary Meta Tags -->
    <meta name="title" content="{title}">
    <meta name="description" content="{description}">
    
    <!-- Facebook / Open Graph -->
    <meta property="fb:app_id" content="2091422248085004" />
    <meta property="og:type" content="article">
    <meta property="og:url" content="{share_url}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:image" content="{image}">
    <meta property="og:image:secure_url" content="{image}">
    <meta property="og:image:type" content="image/jpeg">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:image:alt" content="{title}">
    <meta property="og:site_name" content="Cheshire Today">
    <meta property="og:locale" content="en_GB">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:url" content="{share_url}">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{image}">
    <meta name="twitter:image:alt" content="{title}">
    <meta name="twitter:site" content="@CheshireToday">
    
    <!-- Redirect to React app for actual users -->
    <script>
        // Check if this is a bot/crawler
        var userAgent = navigator.userAgent.toLowerCase();
        var isCrawler = /bot|crawler|spider|crawling|facebookexternalhit|twitterbot|linkedinbot|whatsapp/i.test(userAgent);
        
        // If not a crawler, redirect to main site (React Router will handle article display)
        if (!isCrawler) {{
            window.location.href = "{app_url}";
        }}
    </script>
</head>
<body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; line-height: 1.6;">
    <h1>{title}</h1>
    <p>{description}</p>
    <p style="color: #666; font-size: 14px;">
        <a href="{app_url}" style="color: #059669; text-decoration: none;">← Back to Cheshire Today</a>
    </p>
</body>
</html>"""
        
        return HTMLResponse(content=html_content, headers={"Cache-Control": "public, max-age=3600"})
        
    except Exception as e:
        logger.error(f"Error serving article for social crawlers: {str(e)}")
        # Return a basic HTML page on error
        # Use environment variable for base URL (works across all deployment environments)
        base_url = os.environ.get('PUBLIC_URL', 'https://cheshiretoday.co.uk')
        fallback_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta property="og:title" content="Cheshire Today - Local News">
    <meta property="og:image" content="https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1200&h=630&fit=crop">
    <meta property="fb:app_id" content="2091422248085004">
    <script>window.location.href = "{base_url}";</script>
</head>
<body>
    <h1>Cheshire Today</h1>
    <p><a href="{base_url}">Visit Cheshire Today</a></p>
</body>
</html>"""
        return HTMLResponse(content=fallback_html)

# Register article endpoints for social media crawlers
@app.get("/article/{article_id}")
async def serve_article_for_production(article_id: str):
    """
    Endpoint for social media crawlers at /article/{id}
    Returns server-rendered HTML with meta tags for proper sharing
    """
    return await serve_article_html(article_id)

@api_router.get("/article/{article_id}")
async def serve_article_for_api(article_id: str):
    """API endpoint for programmatic access"""
    return await serve_article_html(article_id)


# Helper function for robots.txt content
def get_robots_content():
    base_url = os.environ.get('PUBLIC_URL', 'https://cheshiretoday.co.uk')
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
# Block bad bots and scrapers
# =============================================
User-agent: AhrefsBot
Disallow: /

User-agent: SemrushBot
Disallow: /

User-agent: DotBot
Disallow: /

User-agent: MJ12bot
Disallow: /

# =============================================
# Sitemaps
# =============================================
Sitemap: {base_url}/api/sitemap.xml
Sitemap: {base_url}/api/news-sitemap.xml

# Preferred domain
Host: {base_url}
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
async def trigger_daily_generation():
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
            'https://images.unsplash.com/photo-1564760055775-d63b17a55c44?w=800&h=500&fit=crop',  # UK countryside village
            'https://images.unsplash.com/photo-1599809275671-b5942cabc7a2?w=800&h=500&fit=crop',  # British countryside
            'https://images.unsplash.com/photo-1570193628474-5ba0c21b8f3f?w=800&h=500&fit=crop',  # English village
            'https://images.unsplash.com/photo-1583083527882-4bee9aba2eea?w=800&h=500&fit=crop',  # UK countryside
            'https://images.unsplash.com/photo-1500343673619-3aa6d5c281c1?w=800&h=500&fit=crop',  # British rural
            'https://images.unsplash.com/photo-1542718610-a1d656d1884c?w=800&h=500&fit=crop',  # English countryside
            'https://images.unsplash.com/photo-1582555172866-f73bb12a2ab3?w=800&h=500&fit=crop',  # UK rural scene
            'https://images.unsplash.com/photo-1598513431456-ebedfd60c98f?w=800&h=500&fit=crop',  # British landscape
            'https://images.unsplash.com/photo-1519904981063-b0cf448d479e?w=800&h=500&fit=crop',  # Rural UK
            'https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=800&h=500&fit=crop',  # English countryside
            'https://images.unsplash.com/photo-1516815231560-8f41ec531527?w=800&h=500&fit=crop',  # Rural buildings
            'https://images.unsplash.com/photo-1508766206392-8bd5cf550d1c?w=800&h=500&fit=crop',  # British town
            'https://images.unsplash.com/photo-1609137144813-7d9921338f24?w=800&h=500&fit=crop',  # UK village street
            'https://images.unsplash.com/photo-1548013146-72479768bada?w=800&h=500&fit=crop',  # Country lane
            'https://images.unsplash.com/photo-1502139214982-d0ad755818d8?w=800&h=500&fit=crop',  # British village
            'https://images.unsplash.com/photo-1605616857458-e9e191ba3158?w=800&h=500&fit=crop',  # Rural scene
            'https://images.unsplash.com/photo-1617952739847-6593487e7d95?w=800&h=500&fit=crop',  # UK countryside
            'https://images.unsplash.com/photo-1518378188025-22bd89516ee2?w=800&h=500&fit=crop',  # Country house
            'https://images.unsplash.com/photo-1486299267070-83823f5448dd?w=800&h=500&fit=crop',  # British architecture
            'https://images.unsplash.com/photo-1568084680786-a84f91d1153c?w=800&h=500&fit=crop',  # Countryside road
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

@api_router.post("/update-local-news-images")
async def update_local_news_images():
    """Update ONLY Local News articles with Cheshire-specific images - Production Safe"""
    try:
        # Get all Local News articles from the current database
        local_news_articles = await db.articles.find({"category": "Local News"}).to_list(1000)
        
        if not local_news_articles:
            return {
                "success": True,
                "message": "No Local News articles found",
                "articles_updated": 0
            }
        
        # Cheshire-specific images for Local News
        cheshire_images = CATEGORY_IMAGES.get('Local News', [])
        
        if not cheshire_images:
            raise HTTPException(status_code=500, detail="Cheshire images not configured")
        
        # Shuffle for randomness
        available_cheshire = list(cheshire_images)
        random.shuffle(available_cheshire)
        
        updated_count = 0
        articles_info = []
        
        for article in local_news_articles:
            # Get next Cheshire image (cycle through list if needed)
            if not available_cheshire:
                available_cheshire = list(cheshire_images)
                random.shuffle(available_cheshire)
            
            new_image = available_cheshire.pop(0)
            
            # Update article
            result = await db.articles.update_one(
                {'_id': article['_id']},
                {'$set': {'image': new_image}}
            )
            
            if result.modified_count > 0:
                updated_count += 1
                articles_info.append({
                    "title": article.get('title', 'Untitled')[:60],
                    "old_image": article.get('image', '')[-40:],
                    "new_image": new_image[-40:]
                })
        
        logger.info(f"Updated {updated_count} Local News articles with Cheshire images")
        
        return {
            "success": True,
            "message": f"Successfully updated {updated_count} Local News articles with Cheshire-specific images",
            "articles_updated": updated_count,
            "total_local_news": len(local_news_articles),
            "cheshire_images_available": len(cheshire_images),
            "sample_updates": articles_info[:5]  # Show first 5 updates
        }
        
    except Exception as e:
        logger.error(f"Error updating Local News images: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/reassign-all-images-uk")
async def reassign_all_images_uk():
    """
    PERMANENT FIX: Reassign ALL article images with STRICT category matching.
    Each article gets a unique image that matches its category.
    This ensures images are both unique AND category-appropriate.
    """
    try:
        # Get all articles sorted by category for efficient assignment
        all_articles = await db.articles.find({}).to_list(1000)
        
        # Group articles by category
        articles_by_category = {}
        for article in all_articles:
            cat = article.get('category', 'Local News')
            if cat not in articles_by_category:
                articles_by_category[cat] = []
            articles_by_category[cat].append(article)
        
        # Track globally used images to ensure uniqueness
        used_images = set()
        updated_count = 0
        category_match_count = 0
        fallback_count = 0
        category_stats = {}
        
        # Process each category
        for category, articles in articles_by_category.items():
            category_images = CATEGORY_IMAGES.get(category, []).copy()
            random.shuffle(category_images)  # Randomize order
            
            category_assigned = 0
            category_fallback = 0
            
            for article in articles:
                # Try category-specific image first
                available_category = [img for img in category_images if img not in used_images]
                
                if available_category:
                    new_image = available_category[0]
                    category_assigned += 1
                    category_match_count += 1
                else:
                    # Fallback: Use any unused image from the global pool
                    all_unused = [img for img in ALL_UNIQUE_IMAGES if img not in used_images]
                    if all_unused:
                        new_image = random.choice(all_unused)
                        category_fallback += 1
                        fallback_count += 1
                    else:
                        logger.error(f"No unique images available for article in {category}")
                        continue
                
                # Update article with new image
                await db.articles.update_one(
                    {'_id': article['_id']},
                    {'$set': {'image': new_image}}
                )
                used_images.add(new_image)
                updated_count += 1
            
            category_stats[category] = {
                'total': len(articles),
                'category_matched': category_assigned,
                'fallback': category_fallback
            }
        
        return {
            "success": True,
            "articles_updated": updated_count,
            "total_articles": len(all_articles),
            "category_matched_images": category_match_count,
            "fallback_images": fallback_count,
            "match_rate": f"{(category_match_count / updated_count * 100):.1f}%" if updated_count > 0 else "0%",
            "category_breakdown": category_stats,
            "total_unique_images_available": len(ALL_UNIQUE_IMAGES),
            "images_used": len(used_images)
        }
        
    except Exception as e:
        logger.error(f"Error reassigning images: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/fix-all-images-uk")
async def fix_all_images_uk():
    """Alias for reassign-all-images-uk"""
    return await reassign_all_images_uk()

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
    Find and fix articles with Perplexity refusal messages in content.
    Replaces bad content with proper fallback text.
    Requires admin authentication.
    """
    try:
        # Refusal indicators to detect
        refusal_indicators = [
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
            "Alternatively, if you have"
        ]
        
        # Get all articles
        articles = await db.articles.find({}, {"_id": 0}).to_list(1000)
        
        fixed_count = 0
        fixed_articles = []
        
        for article in articles:
            content = article.get('content', '')
            content_lower = content.lower()
            
            # Check if content contains refusal messages
            is_bad = any(indicator.lower() in content_lower for indicator in refusal_indicators)
            
            if is_bad:
                title = article.get('title', '')
                source = article.get('source', 'News Source')
                summary = article.get('original_summary', title)
                category = article.get('category', '')
                
                # Determine appropriate template based on title/category
                text_lower = f"{title} {summary} {category}".lower()
                
                # Sports/Entertainment templates
                if any(word in text_lower for word in ['football', 'united', 'everton', 'liverpool', 'city', 'match', 'goal', 'player', 'manager', 'transfer', 'league', 'cup', 'sport']):
                    new_content = f"""{summary}

This sports story has been reported by {source}. Fans and supporters have been following developments closely as the situation unfolds.

Further details are expected to emerge in the coming hours. Stay tuned to {source} for the latest updates on this developing story.

For more sports news and updates from the region, continue following {source}."""

                elif any(word in text_lower for word in ['show', 'tv', 'star', 'celebrity', 'film', 'movie', 'music', 'concert', 'theatre', 'entertainment', 'actor', 'actress', 'singer']):
                    new_content = f"""{summary}

This entertainment story has been covered by {source}. Fans have been eagerly following the latest developments.

More details are expected to be announced soon. {source} will continue to bring you the latest updates as they become available.

For more entertainment news from across the region, keep following {source}."""

                elif any(word in text_lower for word in ['business', 'company', 'investment', 'jobs', 'economy', 'market', 'retail', 'shop', 'store', 'property', 'development']):
                    new_content = f"""{summary}

This business story has been reported by {source}. Industry observers and local stakeholders are monitoring the situation closely.

Further details are expected as the story develops. {source} will continue to provide updates as more information becomes available.

For more business and economic news from the region, follow {source}."""

                elif any(word in text_lower for word in ['health', 'hospital', 'nhs', 'doctor', 'medical', 'patient', 'clinic', 'wellbeing', 'fitness']):
                    new_content = f"""{summary}

This health story has been reported by {source}. Health officials and medical professionals are involved in addressing the matter.

Residents are encouraged to follow official guidance from health authorities. {source} will continue to provide updates as more information becomes available."""

                elif any(word in text_lower for word in ['police', 'crime', 'arrest', 'court', 'trial', 'accident', 'crash', 'incident', 'emergency', 'fire']):
                    new_content = f"""{summary}

This developing story has been reported by {source}. Local authorities and emergency services are understood to be involved in the response.

Residents in the affected area are advised to stay informed through official channels as more details emerge. The situation continues to develop and further updates are expected.

Anyone with information related to this story is encouraged to contact the relevant authorities. {source} will continue to provide updates as more information becomes available."""

                else:
                    # Generic local news template
                    new_content = f"""{summary}

This story has been reported by {source}. Local residents and community members have been following developments with interest.

More details are expected to emerge soon. {source} will continue to bring you updates on this and other local news stories.

For the latest news from across the region, keep following {source}."""
                
                # Update the article
                await db.articles.update_one(
                    {'id': article.get('id')},
                    {'$set': {'content': new_content}}
                )
                
                fixed_count += 1
                fixed_articles.append(title[:50] + "...")
                logger.info(f"Fixed bad content for: {title[:40]}...")
        
        return {
            "success": True,
            "articles_checked": len(articles),
            "articles_fixed": fixed_count,
            "fixed_titles": fixed_articles,
            "cost": "$0 (FREE - no API calls)"
        }
        
    except Exception as e:
        logger.error(f"Error fixing bad content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/fix-mismatched-content")
async def fix_mismatched_content():
    """
    Fix articles where the template content doesn't match the article category/topic.
    This re-applies the correct category-aware template.
    """
    try:
        # Get all articles with the generic emergency template
        articles = await db.articles.find({
            'content': {'$regex': 'emergency services.*affected area', '$options': 'i'}
        }).to_list(500)
        
        fixed_count = 0
        fixed_articles = []
        
        for article in articles:
            title = article.get('title', '')
            source = article.get('source', 'News Source')
            summary = article.get('original_summary', '') or title
            category = article.get('category', '')
            text_lower = f"{title} {summary} {category}".lower()
            
            # Check if the current template is appropriate
            is_incident_related = any(word in text_lower for word in [
                'police', 'crime', 'arrest', 'court', 'trial', 'accident', 'crash', 
                'incident', 'emergency', 'fire', 'death', 'dies', 'killed', 'tragedy',
                'investigation', 'appeal', 'missing'
            ])
            
            # If it's NOT incident-related but has the incident template, fix it
            if not is_incident_related:
                # Sports template
                if any(word in text_lower for word in ['football', 'united', 'everton', 'liverpool', 'city', 'match', 'goal', 'player', 'manager', 'transfer', 'league', 'cup', 'sport']):
                    new_content = f"""{summary}

This sports story has been reported by {source}. Fans and supporters have been following developments closely as the situation unfolds.

Further details are expected to emerge in the coming hours. Stay tuned to {source} for the latest updates on this developing story.

For more sports news and updates from the region, continue following {source}."""

                # Entertainment template
                elif any(word in text_lower for word in ['show', 'tv', 'star', 'celebrity', 'film', 'movie', 'music', 'concert', 'theatre', 'entertainment', 'actor', 'actress', 'singer']):
                    new_content = f"""{summary}

This entertainment story has been covered by {source}. Fans have been eagerly following the latest developments.

More details are expected to be announced soon. {source} will continue to bring you the latest updates as they become available.

For more entertainment news from across the region, keep following {source}."""

                # Business template
                elif any(word in text_lower for word in ['business', 'company', 'investment', 'jobs', 'economy', 'market', 'retail', 'shop', 'store', 'property', 'development']):
                    new_content = f"""{summary}

This business story has been reported by {source}. Industry observers and local stakeholders are monitoring the situation closely.

Further details are expected as the story develops. {source} will continue to provide updates as more information becomes available.

For more business and economic news from the region, follow {source}."""

                # Health template
                elif any(word in text_lower for word in ['health', 'hospital', 'nhs', 'doctor', 'medical', 'patient', 'clinic', 'wellbeing', 'fitness']):
                    new_content = f"""{summary}

This health story has been reported by {source}. Health officials and medical professionals are involved in addressing the matter.

Residents are encouraged to follow official guidance from health authorities. {source} will continue to provide updates as more information becomes available."""

                else:
                    # Generic local news template
                    new_content = f"""{summary}

This story has been reported by {source}. Local residents and community members have been following developments with interest.

More details are expected to emerge soon. {source} will continue to bring you updates on this and other local news stories.

For the latest news from across the region, keep following {source}."""
                
                # Update the article
                await db.articles.update_one(
                    {'_id': article['_id']},
                    {'$set': {'content': new_content}}
                )
                
                fixed_count += 1
                fixed_articles.append(f"{title[:50]}... -> {category or 'Generic'}")
                logger.info(f"Fixed mismatched content for: {title[:40]}...")
        
        return {
            "success": True,
            "articles_checked": len(articles),
            "articles_fixed": fixed_count,
            "fixed_titles": fixed_articles,
            "message": f"Fixed {fixed_count} articles with mismatched templates"
        }
        
    except Exception as e:
        logger.error(f"Error fixing mismatched content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/remove-product-articles")
async def remove_product_articles():
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
async def sync_rss_now():
    """
    Force immediate sync of RSS feeds - imports latest articles from all feeds.
    This is useful after deployment to quickly get the latest articles.
    """
    try:
        from app.news_feed_service import news_feed_service
        from app.perplexity_service import perplexity_service
        from uuid import uuid4
        
        logger.info("Starting manual RSS sync...")
        
        # Get existing article titles to avoid duplicates
        existing_articles = await db.articles.find({}, {'title': 1}).to_list(2000)
        existing_titles = {a['title'].lower().strip() for a in existing_articles if a.get('title')}
        
        # Fetch all RSS feeds
        rss_articles = await news_feed_service.fetch_all_feeds()
        logger.info(f"Fetched {len(rss_articles)} articles from RSS feeds")
        
        # Filter for new articles with images
        new_articles = []
        for article in rss_articles:
            title = article.get('title', '').strip()
            if not title:
                continue
            if title.lower() in existing_titles:
                continue
            if not article.get('image'):
                continue
            new_articles.append(article)
        
        logger.info(f"Found {len(new_articles)} new articles to import")
        
        # Import up to 10 new articles
        imported_count = 0
        imported_titles = []
        max_import = 10
        
        for article in new_articles[:max_import]:
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
                    'published_date': article.get('published_date'),
                    'created_at': datetime.utcnow()
                }
                
                await db.articles.insert_one(article_doc)
                imported_count += 1
                imported_titles.append(title[:60] + "...")
                existing_titles.add(title.lower())
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
    """Get scheduler status and next run time"""
    try:
        jobs = scheduler.get_jobs()
        job_info = []
        for job in jobs:
            job_info.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
            })
        return {
            "scheduler_running": scheduler.running,
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
app.include_router(api_router)
app.include_router(rss_routes.router)

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

# Initialize scheduler
scheduler = AsyncIOScheduler()

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
        
        # Also ensure we don't have too many articles (safety cap at 100)
        total_count = await db.articles.count_documents({})
        if total_count > 100:
            # Get the 100th newest article's date
            articles = await db.articles.find({}, {'publishedDate': 1}).sort('publishedDate', -1).skip(100).limit(1).to_list(1)
            if articles:
                cutoff = articles[0]['publishedDate']
                result = await db.articles.delete_many({'publishedDate': {'$lt': cutoff}})
                logger.info(f"🗑️ Safety cap: removed {result.deleted_count} articles beyond 100 limit")
                
    except Exception as e:
        logger.error(f"Error cleaning up old articles: {str(e)}")

async def daily_article_generation(count: int = 12):
    """Generate new articles daily with fault tolerance and distributed locking"""
    try:
        # ============================================
        # DISTRIBUTED LOCK - Prevents duplicate article generation
        # Only ONE instance across ALL replicas should generate articles
        # ============================================
        now = datetime.now(timezone.utc)
        lock_key = f"article_gen_{now.strftime('%Y%m%d%H')}"
        
        # Try to acquire the lock - first server wins
        try:
            await db.scheduler_locks.insert_one({
                "job": lock_key,
                "locked": True,
                "locked_at": now,
                "instance_id": os.environ.get('HOSTNAME', 'unknown'),
                "expires_at": now + timedelta(hours=2)
            })
            logger.info(f"✅ Acquired article generation lock: {lock_key}")
        except Exception as lock_error:
            error_str = str(lock_error).lower()
            if "duplicate key" in error_str or "e11000" in error_str:
                logger.info(f"⏭️ Another server is handling article generation, skipping...")
                return
            else:
                logger.warning(f"Lock warning (continuing): {lock_error}")
        
        logger.info(f"Starting daily article generation (target: {count})...")
        
        # Generate new articles (5+ Cheshire, 3+ UK) with error handling
        try:
            # Request higher count to ensure net 5+ articles after image filtering
            await generate_articles(GenerateArticlesRequest(count=count, include_uk_news=True))
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
        try:
            await cleanup_old_articles()
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {str(cleanup_error)}")
            # Continue even if cleanup fails
            pass
        
        logger.info("Daily article generation process completed")
        
        # Release the lock
        try:
            await db.scheduler_locks.delete_one({"job": lock_key})
        except Exception:
            pass
            
    except Exception as e:
        logger.error(f"Critical error in daily article generation: {str(e)}")

async def send_scheduled_news_digest(digest_time: str = "DailyBrief"):
    """
    Send The Daily Brief to all subscribers with daily_brief preference.
    Called by scheduler at 07:30 AM daily.
    
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
            logger.info(f"⏭️ {digest_time} for {date_key} already exists (status: {existing.get('status')}), skipping...")
            return
        
        # ============================================
        # Step 2: Try atomic insert - MongoDB unique index ensures only ONE wins
        # ============================================
        instance_id = f"{os.environ.get('HOSTNAME', 'unknown')}_{uuid4().hex[:8]}"
        
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
        
        # Get subscribers with daily_brief preference (or all if no preference set - for backwards compatibility)
        subscribers = await db.subscribers.find(
            {"$or": [
                {"daily_brief": True},
                {"daily_brief": {"$exists": False}}  # Backwards compatibility
            ]},
            {"_id": 0, "email": 1}
        ).to_list(1000)
        if not subscribers:
            logger.info("No subscribers found with daily_brief preference - skipping")
            return
        
        # Deduplicate emails (case-insensitive) and validate
        import re
        email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        seen_emails = set()
        unique_emails = []
        invalid_emails = []
        
        for s in subscribers:
            email = s.get('email', '').lower().strip()
            if email and email not in seen_emails:
                # Validate email format
                if email_regex.match(email) and not email.endswith('@example.com'):
                    seen_emails.add(email)
                    unique_emails.append(s.get('email'))  # Keep original case
                else:
                    invalid_emails.append(email)
        
        if invalid_emails:
            logger.warning(f"Skipping {len(invalid_emails)} invalid emails: {invalid_emails[:5]}...")
        
        subscriber_emails = unique_emails
        logger.info(f"Found {len(subscriber_emails)} valid unique subscribers for Daily Brief")
        # ============================================================
        # TEST MODE (migration): send digest ONLY to one email address
        # Set DIGEST_TEST_EMAIL in Render env to enable this
        # ============================================================
        test_digest_email = os.environ.get("DIGEST_TEST_EMAIL", "").strip()
        if test_digest_email:
            subscriber_emails = [test_digest_email]
            logger.warning(f"🧪 TEST MODE ENABLED: Digest will be sent ONLY to {test_digest_email}")
        # Get latest articles (published in last 24 hours for variety)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Use aggregation to get unique articles by title
        pipeline = [
            {"$match": {"publishedDate": {"$gte": cutoff_time.isoformat()}}},
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
            {"$limit": 10}
        ]
        
        recent_articles = await db.articles.aggregate(pipeline).to_list(10)
        
        # Convert IDs to string format for email links
        # IMPORTANT: Use mongo_id (ObjectId hex) as the primary ID since that's what the API expects
        for article in recent_articles:
            if article.get('mongo_id'):
                article['id'] = str(article['mongo_id'])
            elif article.get('custom_id'):
                article['id'] = str(article['custom_id'])
            article.pop('mongo_id', None)
            article.pop('custom_id', None)
        
        # If no recent articles, get latest 10 regardless of time (still unique by title)
        if not recent_articles:
            logger.info("No recent articles, using latest 10 unique articles")
            pipeline = [
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
            
            # Convert IDs for fallback articles too
            for article in recent_articles:
                if article.get('mongo_id'):
                    article['id'] = str(article['mongo_id'])
                elif article.get('custom_id'):
                    article['id'] = str(article['custom_id'])
                article.pop('mongo_id', None)
                article.pop('custom_id', None)
        
        if not recent_articles:
            logger.warning("No articles available for digest")
            return
        
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
        
        # Prioritize Local News (including Cheshire locations) first, Sports LAST
        local_keywords = ['local news', 'cheshire', 'crewe', 'macclesfield', 'wilmslow', 'chester', 'warrington', 'nantwich', 'congleton', 'northwich', 'knutsford', 'sandbach', 'middlewich', 'alsager', 'winsford', 'ellesmere port']
        
        def is_local(article):
            category = article.get('category', '').lower()
            title = article.get('title', '').lower()
            content = article.get('content', '').lower()[:500]
            
            for keyword in local_keywords:
                if keyword in category or keyword in title or keyword in content:
                    return True
            return False
        
        def is_sports(article):
            return article.get('category', '').lower() == 'sports'
        
        # Sort: Local News first, then other categories, Sports LAST
        local_news = [a for a in unique_articles if is_local(a)]
        sports_news = [a for a in unique_articles if is_sports(a) and not is_local(a)]
        other_news = [a for a in unique_articles if not is_local(a) and not is_sports(a)]
        
        # Combine: local first, then others, then max 2 sports at the end
        unique_articles = (local_news + other_news + sports_news[:2])[:10]
        
        logger.info(f"Sending Daily Brief with {len(unique_articles)} unique articles ({len(local_news)} Local, {len(other_news)} Other, max 2 Sports) to {len(subscriber_emails)} subscribers")
        
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
        
        # Update our digest log record to "sent" status
        await db.digest_log.update_one(
            {"digest_time": digest_time, "date_key": date_key, "instance_id": instance_id},
            {"$set": {
                "success_count": success_count,
                "tracking_id": tracking_id,
                "status": "sent",
                "completed_at": datetime.now(timezone.utc)
            }}
        )
        
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


async def send_weekly_roundup_email():
    """
    Send The Weekly Roundup to all subscribers with weekly_roundup preference.
    Called by scheduler every Sunday at 09:00 AM.
    """
    from datetime import timedelta
    
    try:
        now = datetime.now(timezone.utc)
        
        # DISTRIBUTED LOCK - Same pattern as daily brief
        lock_key = f"weekly_roundup_{now.strftime('%Y%m%d')}"
        lock_id = str(uuid4())
        
        # Check if already sent
        recent_digest = await db.digest_log.find_one({
            "sent_at": {"$gte": now - timedelta(hours=12)},
            "digest_time": "WeeklyRoundup"
        })
        
        if recent_digest:
            logger.info(f"⏭️ Weekly Roundup already sent at {recent_digest.get('sent_at')}, skipping...")
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
        
        # Get subscribers with weekly_roundup preference
        subscribers = await db.subscribers.find(
            {"weekly_roundup": True},
            {"_id": 0, "email": 1}
        ).to_list(1000)
        
        if not subscribers:
            logger.info("No subscribers found with weekly_roundup preference - skipping")
            await db.scheduler_locks.delete_one({"job": lock_key})
            return
        
        subscriber_emails = [s.get('email') for s in subscribers if s.get('email')]
        logger.info(f"Found {len(subscriber_emails)} subscribers for Weekly Roundup")
        
        # Get top performing articles from the past week (by view_count)
        one_week_ago = now - timedelta(days=7)
        
        # Get big read (most viewed article)
        big_read = await db.articles.find_one(
            {"publishedDate": {"$gte": one_week_ago.isoformat()}},
            sort=[("view_count", -1)]
        )
        
        if not big_read:
            # Fallback to most recent
            big_read = await db.articles.find_one({}, sort=[("publishedDate", -1)])
        
        if not big_read:
            logger.warning("No articles found for Weekly Roundup")
            await db.scheduler_locks.delete_one({"job": lock_key})
            return
        
        # Convert _id to id
        if big_read.get('_id'):
            big_read['id'] = str(big_read['_id'])
        
        # Get top 5 trending articles (excluding big read)
        icymi_cursor = db.articles.find(
            {"publishedDate": {"$gte": one_week_ago.isoformat()}},
            sort=[("view_count", -1)]
        ).limit(6)
        
        icymi_articles = []
        async for article in icymi_cursor:
            if str(article.get('_id')) != str(big_read.get('_id')):
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
                "date_key": now.strftime('%Y%m%d'),
                "type": "WeeklyRoundup",
                "articles_count": 1 + len(icymi_articles),
                "subscribers_count": len(subscriber_emails),
                "success_count": success_count,
                "tracking_id": tracking_id  # For email analytics
            })
        except Exception as log_error:
            logger.warning(f"Could not log weekly roundup send: {log_error}")
        
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
            if current_image and (is_banned or current_image not in ALL_UNIQUE_IMAGES):
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
                    elif img in ALL_UNIQUE_IMAGES and not any(b in img for b in BANNED_IMAGES):
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
        if LOCAL_DEV_NO_DB or db is None:
            logger.warning("LOCAL_DEV_NO_DB=1 -> Skipping MongoDB startup DB tasks.")
            return
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
        except Exception as idx_error:
            if "already exists" in str(idx_error).lower() or "index" in str(idx_error).lower():
                logger.info("✅ Unique index on articles.title already exists")
            else:
                logger.warning(f"Could not create articles.title index: {idx_error}")
        
        # Start scheduler FIRST so server can accept requests immediately
        # All heavy operations run in background tasks
        
        # 1. Queue duplicate cleanup as background task (non-blocking)
        asyncio.create_task(auto_clean_duplicate_articles())
        
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
        
        asyncio.create_task(check_and_generate())
        
        # 3. Start Scheduler
        scheduler.add_job(
            daily_article_generation,
            CronTrigger(hour=6, minute=0),  # Morning: 6:00 AM
            id='morning_article_generation',
            name='Generate morning news articles',
            replace_existing=True,
            args=[12]
        )
        
        scheduler.add_job(
            daily_article_generation,
            CronTrigger(hour=12, minute=0),  # Midday: 12:00 PM
            id='midday_article_generation',
            name='Generate midday news articles',
            replace_existing=True
        )
        
        scheduler.add_job(
            daily_article_generation,
            CronTrigger(hour=18, minute=0),  # Evening: 6:00 PM
            id='evening_article_generation',
            name='Generate evening news articles',
            replace_existing=True
        )
        scheduler.add_job(
            daily_article_generation,
            CronTrigger(hour=15, minute=0),  # Afternoon: 3:00 PM
            id='afternoon_article_generation',
            name='Generate afternoon news articles',
            replace_existing=True
        )
        
        # ============================================
        # EMAIL DIGEST SCHEDULE (Updated January 2026)
        # New tiered email strategy: Daily Brief (07:30), Weekly Roundup (Sunday 09:00)
        # Breaking News Alerts are manual only
        # ============================================
        
        # The Daily Brief - Every day at 07:30 AM
        scheduler.add_job(
            send_scheduled_news_digest,
            CronTrigger(hour=7, minute=30),
            id='daily_brief',
            name='Send The Daily Brief (07:30 AM)',
            replace_existing=True,
            kwargs={'digest_time': 'DailyBrief'}
        )
        
        # The Weekly Roundup - Every Sunday at 09:00 AM
        scheduler.add_job(
            send_weekly_roundup_email,
            CronTrigger(day_of_week='sun', hour=9, minute=0),
            id='weekly_roundup',
            name='Send The Weekly Roundup (Sunday 09:00 AM)',
            replace_existing=True
        )
        
        # OLD SCHEDULE DISABLED - Keeping commented for reference
        # scheduler.add_job(send_scheduled_news_digest, CronTrigger(hour=6, minute=15), id='morning_news_digest', ...)
        # scheduler.add_job(send_scheduled_news_digest, CronTrigger(hour=12, minute=15), id='midday_news_digest', ...)
        # scheduler.add_job(send_scheduled_news_digest, CronTrigger(hour=18, minute=15), id='evening_news_digest', ...)
        
        logger.info("📬 Email schedule: Daily Brief at 07:30, Weekly Roundup Sunday 09:00")
        
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
        
        # Check every 5 minutes for due scheduled posts
        scheduler.add_job(
            process_user_scheduled_posts,
            'interval',
            minutes=5,
            id='process_scheduled_facebook_posts',
            name='Process user-scheduled Facebook posts',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("Scheduler started. Articles: 6AM, 12PM, 3PM, 6PM. Digests: Daily Brief 7:30AM, Weekly Roundup Sunday 9AM. Facebook: MANUAL ONLY. Twitter: MANUAL ONLY.")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")

@app.on_event("shutdown")
async def shutdown_db_client():
    scheduler.shutdown()
    client.close()
