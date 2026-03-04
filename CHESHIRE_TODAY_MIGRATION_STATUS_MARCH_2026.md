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
