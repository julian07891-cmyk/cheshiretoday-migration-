# Cheshire Today – Migration & Production Readiness
Project Status Document
Date: March 2026
Environment: Migration (Render) + Existing Production Domain

1. Project Overview
Cheshire Today is being rebuilt as a hybrid local + business + AI/finance authority publication.

Frontend
React

Backend
FastAPI (Python)

Database
MongoDB

Infrastructure
Render hosting
Cloudflare proxy currently used by production
GoDaddy DNS authoritative

Content Strategy
Local: 40%
Business / Finance: 40%
AI & Technology: 20%

2. Environments

Production
https://cheshiretoday.co.uk
Currently running on older platform.

Migration
https://cheshiretoday-migration.onrender.com
Full rebuild and testing environment.

3. Backend Infrastructure

API endpoints verified:

/api/health
/api/articles
/api/articles/{id}
api/related-articles
api/trending-topics

4. Article System

Mongo ID example
69a6cd63d803ba80e6108213

Public UUID example
a76ab5ec-a13a-4773-a970-3c78b98a0acb

Slug URL format

/article/{uuid}/{slug}

Example

/article/a76ab5ec-a13a-4773-a970-3c78b98a0acb/999-crews-called-to-car-on-side-as-drivers-told-avoid-rural-cheshire-lane

5. Social / Crawler HTML Endpoint

Endpoints implemented

/article/{id}
/article/{id}/{slug}

Purpose

Serve server-rendered HTML for:

Facebook
Twitter
LinkedIn
WhatsApp
Google News crawler

Metadata included

og:title
og:description
og:image
og:url
twitter:card

6. Canonical Strategy

Canonical always points to production domain

Example

https://cheshiretoday.co.uk/article/{uuid}/{slug}

7. SEO Infrastructure

Verified working

robots.txt
sitemap.xml
news-sitemap.xml
ads.txt

Endpoint checks

Homepage 200
API health 200
Articles 200
Sitemap 200
News sitemap 200
Robots 200
Ads.txt 200

8. Robots Rules

Allows

/article/
/search
/location pages
/category pages

Blocks

Admin endpoints
Email endpoints
Tracking parameters

Blocks scrapers

AhrefsBot
SemrushBot
MJ12bot
DotBot

Allows

Googlebot
Googlebot-News
Googlebot-Image
Bingbot

9. Google News Readiness

Crawler test verified.

Googlebot-News receives HTML response.

Canonical tags correct.

OpenGraph metadata present.

10. Domain Leak Check

Migration environment does not leak Render domain.

Result

leak_frontend_migration: False

11. Render Configuration

Custom domains configured

cheshiretoday.co.uk
www.cheshiretoday.co.uk

Status

Waiting for DNS verification.

12. DNS Infrastructure

Authoritative DNS

GoDaddy

Current root records

A @ → Cloudflare IP
A @ → Cloudflare IP

www

CNAME → cheshiretoday.co.uk

Email records include

MX
SPF
DMARC
Microsoft verification

These must remain unchanged.

13. Deployment Workflow

Commands executed via terminal.

Tools used

curl
grep
perl
python validation

Manual editing avoided.

14. Current System Status

Backend stable
API stable
Article crawler HTML working
Canonical URLs correct
OpenGraph metadata correct
Sitemap working
News sitemap working
Robots.txt working

Migration environment production ready.

15. Remaining Steps Before Launch

Structured data validation
Homepage crawler rendering test
Internal linking audit
Google News eligibility confirmation
DNS switch

16. DNS Switch Plan

Change A records in GoDaddy from Cloudflare IP to Render IP.

Propagation

5 to 20 minutes.

17. Expected Post Launch Architecture

User
↓
DNS
↓
Render
↓
FastAPI backend
↓
MongoDB

18. Post Launch Tasks

Submit sitemap to Google Search Console.
Submit news sitemap to Google Publisher Center.

Apply to affiliate networks

Skimlinks
AWIN
Impact
CJ

19. Platform Vision

Positioning

Local Economic Intelligence Platform for Cheshire.

Content pillars

Local
Business
Finance
AI Technology

Revenue model

Affiliate first
Sponsored placements
Newsletter monetisation

End of document

---

# Project Status Update — March 2026 (Current)

## Working baseline (verified recently)
- Backend: FastAPI running locally on `http://127.0.0.1:8000`
  - `/api/health` responds
  - `/api/articles` supports `with_total=1` and returns `{articles,total,skip,limit,...}`
  - Cache key bug fixed (f-string `search or ''`), removing server SyntaxError risk
- Frontend: React/CRACO project in `frontend/`
  - IMPORTANT: Dev server (`npm start`) is currently unreliable on this machine (CRACO prints “Compiled successfully” but no TCP listener is opened on 3000; `curl localhost:3000` = connection refused).
  - Approved workflow for local work is **static build + serve**:
    - `npm run build`
    - `npx serve -s build`

## Homepage system (production-intent logic now in place)
- HomePageV1 has an enforced editorial pool selection + ordering system aligned with Cheshire Today strategy:
  - Editorial filtering applied before slotting
  - Fixed-depth ratio enforcement (top 28 cap to prevent UK-heavy tail)
  - Weighted pattern mixing across pools: Local + Authority + UK
  - Topic cap example present: `astro: 1` to prevent single-theme takeover
- Top Stories:
  - Target is **8 items** (not 7) to prevent left-column gaps and align with right sidebar height.
  - TopStoriesGrid component currently slices to 8 (`stories.slice(0, 8)`), matching homepage slotting intent.
  - Action item: ensure TopStoriesGrid and selection logic both support 8 consistently.

## SEO and crawl surface (already present)
- `robots.txt` exists and includes sitemap pointers:
  - `Sitemap: https://cheshiretoday.co.uk/sitemap.xml`
  - `Sitemap: https://cheshiretoday.co.uk/news-sitemap.xml`
- Dynamic sitemap endpoints exist in backend:
  - `/sitemap.xml` and `/api/sitemap.xml`
  - `/news-sitemap.xml` and `/api/news-sitemap.xml`
  - `/rss.xml` and `/api/rss.xml`
- Article canonical routes include `/article/:articleId/:slug` routing support in App.

## Guides / authority pages (built but must remain hidden pre-approval)
- Authority pages exist in DB (confirmed ~12, mix of published/draft).
- `/api/authority-pages` endpoints exist.
- Monetisation plan rule (strict): guides must be **ready** but **NOT visible** until affiliate networks approved.
- Current implementation status:
  - Feature flag `NON_AMAZON_MONETISATION_ENABLED: false` (guides and non-Amazon tools should not render)
  - `/guides/:slug` route has been removed from `frontend/src/App.js` (good)
  - Action item: confirm no remaining visible `/guides` links in current homepage/sidebar components (only backups contain them).

## Git state (latest commit)
- Latest commit recorded:
  - `6e77dd4` — “Stabilise homepage system: 40/40/20 ratio, Top Stories 8 layout alignment, editorial policy filtering, API cache fix, affiliate sidebar correction”

---

# Outstanding work to go live (production checklist)

## A) Local run reliability (static build path)
1. Build frontend (`npm run build` in `frontend/`)
2. Serve build (`npx serve -s build`) and verify HTTP listener works
3. Confirm frontend can reach backend API and render homepage + article page

## B) Top Stories = 8 consistency
- Update TopStoriesGrid to slice 8 (or accept a prop for limit) to match homepage slotting intent.

## C) “Guides hidden” guarantee
- Verify current (non-backup) UI has zero public links to `/guides`:
  - Homepage modules
  - Sidebar components
  - Article page related/affiliate strips
- Keep feature flag OFF until affiliate network approvals complete.

## D) Production readiness gates (per handover constraints)
- Legal pages present (privacy/cookies/terms/affiliate disclosure/contact) — verify in production build
- Analytics: GA4 + Search Console already set on live domain; confirm migration build has no blockers
- No “pending monetisation” messaging or broken affiliate widgets in production

## E) Deployment protocol (Render)
- Auto-deploy remains disabled; deploy manually only after local verification.
- Confirm env vars and service names match current plan before switching domains.

---

# Workflow rules (do not break)
- One terminal command at a time (no manual file editing).
- Prefer `grep` (no `rg`).
- Prefer running from project root when possible.
- Avoid piping raw JSON into heredoc python (use `python3 -m json.tool` / `python3 -c` / save-to-file).

