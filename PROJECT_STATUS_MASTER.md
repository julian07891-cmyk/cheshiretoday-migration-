# Cheshire Today Migration — Project Status (Master)
Date: 2026-02-23
Branch: full-scrape-prod

## 1) Current Goal
Build Cheshire Today as a hybrid authority publication:
**Local (Cheshire) + Business + AI/Tech + Finance/Tax**
Positioning: “Local economic intelligence for Cheshire” (reader-first, monetisable via guides + affiliates + sponsored placements).

## 2) Current Working State (Verified)
### Homepage
File: frontend/src/pages/HomePageV1.jsx
- Layout restored and stable: hero + sidebar present
- Left column sections:
  - Latest (grid, 3 columns on large screens) with Show more toggle at bottom
  - Money Toolkit affiliate block
  - AI & Business (now uses filtered aiBizFeed) with Show more toggle at bottom
  - More stories with Show more toggle at bottom
- Right sidebar sections:
  - Business & Money
  - AI Guides + AI & Tech
  - Mortgages & Savings
  - Property & Housing
  - Sponsored placeholder

### Article Page
File: frontend/src/pages/ArticlePageV2.jsx
- Layout matched to homepage width + right sidebar column spacing
- Article source attribution is shown at end of article content (not on cards)
- More stories under article uses CompactArticleCard design and collapses to 1 row with Show more toggle
- Sidebar extended to avoid empty appearance and styled to match homepage behavior

### Cards
File: frontend/src/components/CompactArticleCard.jsx
- Removed source display from cards (source now belongs at end of article page)
- Added underline-on-hover behavior to match homepage sidebar styling

## 3) Monetisation (Current)
- Homepage includes “Money Toolkit” and hero monetisation strip (guides links)
- Article page uses contextual monetisation widget:
  - Component: frontend/src/components/monetisation/ContextTools.jsx
  - Config: frontend/src/config/monetisationTools.js
- Context mapping in ArticlePageV2 picks a tool type based on article title/category/section keywords.
Note: Some articles show the affiliate/tools strip because they match the keyword mapping; others don’t.

## 4) Known Issues / Next Fixes
### Affiliate/tools strip dark mode color mismatch
- The ContextTools container currently uses light palette:
  border-[#E6E1D8], bg-[#FBFAF7], hover bg-[#F2EEE6]
- Needs dark-mode equivalents to match site dark theme.

### Content positioning: “pure crime” items
- Some purely local crime articles appear; user wants to avoid this for the project direction.
- Next action: implement a homepage-level filter to exclude “crime-only” from Hero/Top Stories/Latest (and optionally keep only for a lower-priority feed).

## 5) Recommended Next Steps (Order A → B → C)
A) Define editorial content policy (homepage-safe):
- Keep local + business + ai/tech + finance/tax.
- De-prioritise pure crime; allow only high-impact incidents or consumer-impact crimes.
B) Implement ranking/filters:
- Add isCrimeOnly() heuristic in HomePageV1.jsx
- Prevent crime-only from entering Hero/Top Stories/Latest
C) Improve sources/taxonomy:
- Bias RSS sources toward councils, planning, transport, business, economy.
- Tighten category inference rules.

## 6) Git Status
As of 2026-02-23:
- Clean working tree after latest commit/push.
