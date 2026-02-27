# CHESHIRE TODAY — MASTER PROJECT STATUS
Date: 27 Feb 2026
Branch: full-scrape-prod
Environment: Local (React 3000 / FastAPI 8000)
Deployment: Render (manual deploy only, auto-deploy OFF)

============================================================
SECTION 1 — ORIGINAL PROJECT VISION
============================================================

Cheshire Today is being rebuilt as a:

> Hybrid Local + Business + Finance + AI/Tech Authority Platform

Long-term positioning:
- Local economic intelligence platform for Cheshire
- 40% Local
- 40% Business / Finance
- 20% AI / Tech
- Affiliate-first monetisation
- De-emphasise crime-heavy / sensational content
- Authority tone, financially relevant framing

Strategic sequence (locked in earlier):
A → Editorial policy
B → Homepage algorithm enforcement
C → RSS + categorisation logic cleanup

============================================================
SECTION 2 — TECHNICAL ARCHITECTURE
============================================================

Frontend:
- React (CRA)
- HomePageV1 is active homepage
- ArticlePageV2 is active article template

Backend:
- FastAPI
- MongoDB
- /api/articles endpoint
- RSS ingestion service
- Gemini / AI processing layer

Hosting:
- Render
- Manual deployment only
- Production domain swap only when staging fully stable

Development rule:
- No manual file edits
- One terminal command at a time
- Always check current state before modifying

============================================================
SECTION 3 — RSS + AI HYBRID STRATEGY
============================================================

Sources:
- Cheshire Live
- Liverpool Echo
- BBC England
- BBC UK
- Google News (Macclesfield, Wilmslow, Knutsford, Cheshire East, Cheshire West & Chester)

Logic:
- RSS feeds are hybrid
- Articles filtered through editorial rules
- Deduplication enforced
- Crime-like content filtered
- AI-assisted categorisation (Gemini)
- Article cards constructed with fallback safeguards
- Avoid section=None issues by using category + keyword logic

Homepage logic:
- Pass-based content distribution:
  - Local
  - Business
  - AI/Tech
  - Property
  - UK (fallback)
- AI feed capped
- Latest feed capped
- Deduped across sections

============================================================
SECTION 4 — MONETISATION STRATEGY EVOLUTION
============================================================

Phase 1 (Initial build):
- Multiple monetisation blocks:
  - TopRatedGuides
  - SidebarBestPicks
  - ContextTools
  - ToolsGrid
  - ArticleAffiliateStrip
  - HeroMonetisationStrip
  - GuidePromoBlock (AI Guides)
  - GuidesInlinePromo (In-depth Guide)
  - Hardcoded financial comparison strips
  - Auto-link injection inside article body

Issue:
- Over-monetised UI
- Cluttered homepage
- Too many non-Amazon guides
- Risk of low trust perception
- Structural instability when toggling modules

Decision:
> Move to Amazon-only monetisation temporarily.

============================================================
SECTION 5 — FEATURE FLAG ARCHITECTURE INTRODUCED
============================================================

File added:
frontend/src/config/features.js

Flag:
FEATURES.NON_AMAZON_MONETISATION_ENABLED = false

Meaning:
- Hide all non-Amazon monetisation modules
- Keep Amazon AffiliateWidgetSidebar active

Components gated:
- HeroMonetisationStrip.jsx
- ContextTools.jsx
- ToolsGrid.jsx
- ArticleAffiliateStrip.jsx
- TopRatedGuides.jsx
- SidebarBestPicks.jsx

Pattern:
if (!FEATURES.NON_AMAZON_MONETISATION_ENABLED) return null;

============================================================
SECTION 6 — HOMEPAGE CLEANUP
============================================================

Removed:
- TopRatedGuides hero block
- Mortgage / savings / credit card strips
- “We may earn a commission” hero disclaimer
- Sidebar “Guides” box
- Sponsored placeholder block
- Property & Tax Intelligence block
- Best picks sidebar module

Replaced with:
- AffiliateWidgetSidebar (Amazon)

Errors encountered:
- JSX mismatched closing tags
- Duplicate imports
- Dangling feature wrapper blocks
- Adjacent JSX fragment errors

Fixes:
- Restored proper JSX structure
- Removed empty NON_AMAZON wrapper
- Verified sidebar section layout
- Recompiled cleanly

============================================================
SECTION 7 — ARTICLE PAGE CLEANUP
============================================================

Initial issues:
- AI Guides still rendering
- In-depth Guide block visible
- Auto-injected /guides links in article body
- Runtime crash due to null return from helper

Fixes applied:
- Disabled guide auto-link injection when flag false
- Modified guide selector to return [] instead of null
- Gated GuidePromoBlock and GuidesInlinePromo at render level
- Ensured AffiliateWidgetSidebar remains active
- Fixed blank-page crash

Remaining verification required:
- Confirm no /guides auto-links appear in article body
- Confirm AI Guides & In-depth Guide fully hidden

============================================================
SECTION 8 — GIT STATE & STRUCTURE
============================================================

Branch:
full-scrape-prod

Modified:
- App.js
- ArticleAffiliateStrip.jsx
- NewsFooter.jsx
- SidebarBestPicks.jsx
- TopRatedGuides.jsx
- HeroMonetisationStrip.jsx
- ContextTools.jsx
- ToolsGrid.jsx
- HomePageV1.jsx
- ArticlePageV2.jsx

Added:
- ContactPage.jsx
- CookiePolicy.jsx
- config/features.js

Temp file removed:
- .!8438!App.js (zsh history expansion issue fixed)

============================================================
SECTION 9 — CURRENT SYSTEM STATE
============================================================

✔ Homepage loads
✔ Amazon widget visible
✔ Non-Amazon hero strips removed
✔ Sidebar guides removed
✔ Sponsored placeholder removed
✔ Feature flag architecture in place
✔ Build compiles without syntax errors
⚠ AI Guides visibility must be re-verified
⚠ Production deploy not yet triggered

============================================================
SECTION 10 — REQUIRED STEPS TO PRODUCTION
============================================================

STEP 1 — Stability Audit
- Confirm homepage loads without console errors
- Confirm article page loads without blank state
- Confirm no guide auto-links when flag false

STEP 2 — Legal Pages
Ensure live:
- Privacy Policy
- Cookie Policy
- Affiliate Disclosure
- Terms & Conditions
- Contact page

STEP 3 — Analytics
- Confirm GA4 present
- Confirm Search Console still valid after deploy

STEP 4 — Monetisation Integrity
- Confirm Amazon associateId correct
- Confirm category mapping correct
- Confirm no hidden guide blocks remain

STEP 5 — Render Deployment
- Push branch
- Manual deploy frontend + backend
- Smoke test staging
- Only then swap production domain

============================================================
SECTION 11 — DEVELOPMENT PROTOCOL (MANDATORY)
============================================================

For future GPT sessions:
- No manual file edits
- One terminal command at a time
- Always run git status first
- Always check current state before modifying
- Use grep (not rg)
- Do not introduce new monetisation modules without gating

============================================================
SECTION 12 — LONG-TERM ROADMAP
============================================================

Phase 2:
- Reintroduce non-Amazon monetisation strategically
- AWIN / Impact / CJ onboarding
- Structured guide templates
- Pillar-based monetisation logic

Phase 3:
- Newsletter optimisation
- Authority positioning refinement
- Finance-focused subject lines
- Affiliate network scaling

============================================================
END OF MASTER STATUS
============================================================

To continue in a new chat, paste:

"Continue Cheshire Today using PROJECT_MASTER_STATUS_FEB_2026.md.
We are on full-scrape-prod.
Amazon-only monetisation active.
Follow strict one-command workflow."

