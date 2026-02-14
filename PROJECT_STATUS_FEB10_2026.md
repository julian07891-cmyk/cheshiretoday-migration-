# Cheshire Today Migration – Status (10 Feb 2026)

## ✅ What is Working

### Backend (FastAPI + Uvicorn)
- Running locally on port 8000
- /health endpoint works
- /api/articles endpoint works
- Section inference logic (AI / Money / etc.) active
- MongoDB connection working
- Newsletter + Jobs + Stripe logic present
- Frontend build serving fixed in server.py

### Frontend (React + Yarn)
- Running locally on port 3000
- HomePageV1 active at "/"
- API unified via src/utils/api.js
- All duplicate getApiUrl() definitions removed
- Admin dashboard connected
- Jobs / Payment / Location pages using shared API util
- Duplicate imports fixed
- Build compiling successfully

### Render (Production Preview)
- API working on:
  https://cheshiretoday-migration.onrender.com/api/articles
- Frontend serving now returning HTML correctly
- Cron warmup active

---

## ⚠️ Current Issue

Homepage layout refinement in progress:

- Articles repeating across:
  - Hero
  - Top Stories
  - AI section
  - Finance section
  - Latest section

Need proper dedupe logic using shared usedIds set.

---

## 🎯 Next Tasks

### 1️⃣ Fix Homepage Layout
- Implement central usedIds dedupe system
- Convert layout to:
  - Hero (large)
  - 4-grid under hero
  - Left rail vertical feed
  - Right sidebar (Most Read / Trending / Ads)

### 2️⃣ Improve Section Strategy
- Strengthen section inference rules
- Ensure AI & Finance pull correct articles
- Possibly create explicit homepage buckets

### 3️⃣ Production Preparation
- Final local validation
- Clean render.yaml
- Deploy from main branch only
- Point custom domain later

### 4️⃣ Monetisation Phase
- Finance AI content strategy
- Sponsored blocks positioning
- Affiliate placement refinement
- Job board paid upgrade optimisation

---

## 📌 Important Architecture Decisions

- Local development first (3000/8000)
- Render only after stable
- Single source of truth for API URL:
  src/utils/api.js
- HomePageV1 is new primary homepage
- HomePage (old) preserved at /home-old

---

## 🚀 Current Stable State

Local:
http://localhost:3000  
http://127.0.0.1:8000  

Both working correctly.


---

## ✅ COMPLETED PHASES

### 1️⃣ Infrastructure & Migration
- Backend (FastAPI) deployed on Render
- Frontend (React + CRACO) deployed
- GitHub branch workflow established (`homepage-spec-v1`)
- Production build stable
- ESLint build blockers resolved
- ArticlePageV2 implemented
- Sidebar (Related + Newsletter + Areas) implemented
- Subtle source attribution added (Option A)

---

### 2️⃣ RSS System Stabilisation
- Removed blocked feeds (403 / 404 / Cloudflare)
- Removed partial-content feeds
- Added reliable feeds:
  - Cheshire Live
  - Liverpool Echo
  - BBC England
  - BBC UK
  - Google News town-targeted feeds:
    - Macclesfield
    - Wilmslow
    - Knutsford
    - Cheshire East
    - Cheshire West & Chester
- Backend RSS loading verified
- Feed count confirmed

---

# 🚧 REMAINING WORK / NEXT PHASES

---

## 🔵 PHASE 3 – Full Article Content Extraction (CRITICAL)

**Problem:**  
Most RSS feeds only provide summaries (7–150 chars).  
Current articles lack:
- Street names
- Locations
- Times
- Quotes
- Full narrative detail

### Tasks:
- Implement full article scraping fallback:
  - If RSS content length < X threshold → scrape article page
- Extract:
  - Full article body
  - Author
  - Publish time
  - Main image
- Clean:
  - Remove ads
  - Remove tracking scripts
  - Remove navigation text
- Store structured article object:
  - title
  - content (full HTML)
  - excerpt
  - source
  - sourceUrl
  - publishedAt
  - town (if detectable)

**Goal:** 100% detailed articles, not previews.

---

## 🔵 PHASE 4 – Town-Level Structuring

### Objective:
Make Cheshire Today feel hyperlocal.

### Tasks:
- Auto-detect town from:
  - Title
  - Content body
- Add new article field:
  - `town`
- Update frontend:
  - /macclesfield
  - /wilmslow
  - /knutsford
  - /chester
  - /crewe
- Sidebar: show “More from this town”

---

## 🔵 PHASE 5 – Editorial Quality Upgrade

### Tasks:
- AI rewrite mode:
  - Rewrite syndicated content
  - Improve clarity
  - Add local framing
- Add internal linking:
  - Link town pages automatically
- Add related stories by keyword similarity
- Improve headlines (SEO-focused)

---

## 🔵 PHASE 6 – Monetisation Framework

### 6.1 Affiliate System
- Expand RandomPromoWidget
- Add product placement logic:
  - Only relevant categories
- Add tracking clicks
- Track CTR per widget

### 6.2 Newsletter System
- Connect signup form to backend
- Store email addresses securely
- Weekly digest automation

### 6.3 Ad Infrastructure
- Placeholder ad blocks:
  - Article inline
  - Sidebar
  - Between homepage sections
- Future Google AdSense integration

---

## 🔵 PHASE 7 – SEO Optimisation

### Tasks:
- Structured Data:
  - Article schema (JSON-LD)
- Town schema
- Canonical tags validation
- Sitemap auto-generation
- RSS sitemap
- Improve meta descriptions dynamically

---

## 🔵 PHASE 8 – Performance & Scaling

### Backend:
- Cache RSS results
- Prevent duplicate article imports
- Deduplicate by URL hash
- Add logging for failed feeds

### Frontend:
- Lazy-load heavy components
- Image optimisation
- Improve Core Web Vitals

---

## 🔵 PHASE 9 – Admin Dashboard (Future)

- View RSS feed status
- See blocked feeds
- See article counts per town
- Manual publish toggle
- Sponsored article flag

---

# 🎯 CURRENT PRIORITY ORDER

1. FULL ARTICLE SCRAPING SYSTEM
2. Town auto-detection
3. AI rewrite integration
4. Newsletter backend activation
5. Structured data SEO

---

# ⚠️ KNOWN ISSUES

- Some Google News feeds aggregate duplicates
- Insider Media RSS blocks bots
- Some council feeds return HTML instead of XML
- RSS items missing full content field

---

# 📌 TARGET POSITIONING

Cheshire Today should become:

- Hyperlocal (Macclesfield, Wilmslow, Knutsford focus)
- Fully detailed articles
- Clean, modern UI
- Strong SEO structure
- Monetised via:
  - Affiliate
  - Newsletter
  - Display ads

---

# NEXT IMMEDIATE ACTION

Implement:
Full article scraping + content extraction pipeline.

---

