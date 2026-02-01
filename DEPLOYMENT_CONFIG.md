# Deployment Configuration Guide

## ⚠️ CRITICAL: Configuration for Production Deployments

This document ensures the app works correctly after every deployment.

---

## Frontend Configuration

**File:** `/app/frontend/.env`

**MUST ALWAYS BE:**
```env
REACT_APP_BACKEND_URL=https://cheshiretoday.co.uk
REACT_APP_PUBLIC_URL=https://cheshiretoday.co.uk
WDS_SOCKET_PORT=443
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
```

**⚠️ NEVER USE:**
```env
REACT_APP_BACKEND_URL=https://cheshire-fix.preview.emergentagent.com ❌
```

**Why:** The preview domain is not accessible in production. Using it causes "Failed to load articles" error.

---

## Backend Configuration

**File:** `/app/backend/.env`

**MUST ALWAYS BE:**
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="cheshire_news"
CORS_ORIGINS="*"
PERPLEXITY_API_KEY="[REDACTED_PERPLEXITY_KEY]"
EMERGENT_LLM_KEY="sk-emergent-aE34cD4A5864fB4F13"
SITEMAP_BASE_URL="https://cheshiretoday.co.uk"
BACKEND_BASE_URL="https://cheshire-fix.preview.emergentagent.com"
SMTP_HOST="smtp.gmail.com"
SMTP_PORT="587"
SMTP_USER=""
SMTP_PASSWORD=""
SMTP_FROM_EMAIL="news@cheshiretoday.co.uk"
SMTP_FROM_NAME="Cheshire Today"
```

---

## Database Requirements

**Critical Fields for Articles:**

Every article MUST have:
- `featured` field (boolean: true or false)
- `image` field (URL to image)
- `title`, `content`, `category`
- `publishedDate`

**Distribution:**
- Maximum 5-8 articles with `featured: true` (for hero rotation)
- All other articles with `featured: false` (for grid display)

**Fix Script (if articles fail to load):**
```bash
cd /app/backend && python3 << 'EOF'
from dotenv import load_dotenv
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

load_dotenv('/app/backend/.env')

async def fix_featured():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    # Set all to false first
    await db.articles.update_many({}, {"$set": {"featured": False}})
    
    # Get 5 newest articles
    newest = await db.articles.find({}).sort('publishedDate', -1).limit(5).to_list(5)
    newest_ids = [art['_id'] for art in newest]
    
    # Set only newest 5 to featured
    await db.articles.update_many(
        {"_id": {"$in": newest_ids}},
        {"$set": {"featured": True}}
    )
    
    print("✅ Fixed featured articles")
    client.close()

asyncio.run(fix_featured())
EOF
```

---

## Article Content Configuration

**Priority Focus:** Golden Triangle (85% of articles)
- Knutsford
- Wilmslow  
- Alderley Edge
- Prestbury
- Handforth, Mobberley, Mere, Styal, Hale

**Secondary:** Macclesfield, Congleton, Chester

**UK News:** Minimal (15% only)

**Location in code:** `/app/backend/server.py` lines 342-377 (cheshire_topics array)

---

## Scheduled Article Generation

**Runs:** 3 times daily at 6 AM, 12 PM, 6 PM
**Configuration:** Lines 860-865 in `/app/backend/server.py`

**What it does:**
- Fetches from 30+ RSS feeds (local Cheshire sources)
- Generates AI articles with Perplexity
- Ensures unique images per article
- Maintains 85% local / 15% UK ratio

---

## Pre-Deployment Checklist

Before deploying, verify:

1. ✅ `/app/frontend/.env` uses `cheshiretoday.co.uk` (NOT preview domain)
2. ✅ Database has articles with proper `featured` distribution
3. ✅ Backend and frontend services running
4. ✅ Test API: `curl https://cheshiretoday.co.uk/api/articles`
5. ✅ All environment variables in place

---

## Post-Deployment Verification

After deploying, test:

1. Visit https://cheshiretoday.co.uk
2. Verify hero article loads
3. Verify article grid loads (should see 90+ articles)
4. Test sharing an article (should show article image)
5. Check categories work (Local News, Business, etc.)

---

## Common Issues & Fixes

### Issue 1: "Failed to load articles"
**Cause:** Frontend using preview domain
**Fix:** Update `/app/frontend/.env` to use `cheshiretoday.co.uk`

### Issue 2: No articles in grid (but hero works)
**Cause:** All articles have `featured: true`
**Fix:** Run featured distribution fix script above

### Issue 3: All articles same image
**Cause:** Image uniqueness broken
**Fix:** Run `/api/reassign-all-images` endpoint

### Issue 4: NHS articles show food images
**Cause:** Wrong category images
**Fix:** Already fixed - health category now has medical images only

---

## Files That Must NOT Be Modified

**Critical Files (changes persist in database/code):**
- `/app/frontend/.env` ✅
- `/app/backend/.env` ✅
- Database schema (MongoDB)

**Auto-Generated (can be recreated):**
- `/app/frontend/build/` (rebuilt on deployment)
- `/app/frontend/node_modules/`
- `/app/backend/__pycache__/`

---

## Support & Troubleshooting

If issues persist after deployment:

1. Check supervisor logs: `sudo supervisorctl status`
2. Check backend logs: `tail -f /var/log/supervisor/backend.err.log`
3. Check frontend logs: `tail -f /var/log/supervisor/frontend.err.log`
4. Test API directly: `curl https://cheshiretoday.co.uk/api/articles`
5. Check database: Use scripts in this document

---

**Last Updated:** December 15, 2024
**Next Review:** After any major deployment issue
