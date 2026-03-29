# Cheshire Today – Master Project State
Date: 7 March 2026

--------------------------------------------------
PROJECT OVERVIEW
--------------------------------------------------

Cheshire Today is a hybrid local economic intelligence platform combining:
- Local Cheshire news
- Business & finance coverage
- AI & technology authority
- UK economic and policy news

Stack:

Frontend: React (CRA)
Backend: FastAPI (Python)
Database: MongoDB
Hosting: Render
Domain: cheshiretoday.co.uk
SSL: Active for root and www

--------------------------------------------------
CURRENT LIVE SYSTEM STATUS
--------------------------------------------------

Database:

Total stored articles: 1202
Active articles: 44
Archived articles: 1158

Archive system preserves URLs so shared links remain valid.

Active category mix:

Local News: 18
Business: 12
UK News: 8
Tech: 6

Editorial balance:

Local ≈ 41%
Authority (Business + Tech) ≈ 41%
UK ≈ 18%

Target strategy:

40% Local
40% Authority
20% UK

System currently aligned with strategy.

--------------------------------------------------
CONTENT QUALITY
--------------------------------------------------

Minimum article length rule:

All active articles ≥ 1000 characters.

Previously:

21 short articles detected
21 regenerated via API
1 archived

Current status:

ACTIVE_UNDER_1000 = 0

--------------------------------------------------
HOMEPAGE SYSTEM
--------------------------------------------------

Homepage sections:

Hero
Top Stories
Latest
AI & Business
More Stories
Finance
Property

Features implemented:

Global dedupe
Topic caps
Editorial pool filtering
40/40/20 pillar balancing
Mobile responsive section limits

Mobile behaviour:

Sections collapse to 4 items
Show More toggle enabled

Desktop behaviour:

Larger feed display

Sidebar hidden on mobile to prevent repetition.

--------------------------------------------------
IMPORT SYSTEM
--------------------------------------------------

Hybrid RSS importer operational.

Sources include:

Cheshire Live
BBC
Liverpool Echo
Regional feeds
Google News regional queries

Import pipeline includes:

Duplicate title detection
Duplicate image prevention
Auto archive cleanup
Image reuse control
Hybrid AI rewrite option

Scheduled imports:

06:00
12:00
18:00

Target active pool:

55–70 articles.

--------------------------------------------------
ARCHIVE SYSTEM
--------------------------------------------------

Articles automatically archived when pool grows too large.

Archive protects:

existing URLs
SEO links
shared content.

--------------------------------------------------
DEPLOYMENT STATUS
--------------------------------------------------

Production hosting: Render

Frontend service deployed
Backend service deployed

Domain connected:

cheshiretoday.co.uk
www.cheshiretoday.co.uk

SSL active.

--------------------------------------------------
PROJECT WORKFLOW RULES
--------------------------------------------------

Development workflow:

Check current state before any modification.
Apply changes via terminal commands only.
No manual editing inside files.
One command per step.
Verify system state after each change.

Local verification method:

npm run build
npx serve -s build

Do NOT use npm start.

--------------------------------------------------
NEXT PHASE TASKS
--------------------------------------------------

1. Newsletter system

SMTP activation
Newsletter testing
Subject-line optimisation strategy

2. Monetisation

Affiliate blocks
Affiliate networks integration
Commerce guides system

3. AI content

Perplexity article generation tests
Evergreen article production

4. SEO improvements

Structured data
Schema markup
Internal linking optimisation

--------------------------------------------------
SYSTEM OPERATING MODE
--------------------------------------------------

Current recommendation:

Stop major structural changes.
Allow scheduled imports to run.
Maintain active pool between 55–70.
Focus on monetisation and growth.

--------------------------------------------------
END OF FILE
--------------------------------------------------


## Update — 13 March 2026 (post-deploy scheduler + layout verification)

### What was verified
- Production deploy completed successfully.
- Morning scheduler **did run** on 13 March 2026 at **06:00:00 UTC**.
- Logs confirm:
  - `Generate morning news articles` started at 06:00 UTC
  - distributed lock acquired
  - intentional `rewrite_delay_seconds=900` applied
  - hybrid import completed around **06:16–06:17 UTC**
  - 7 articles imported total
- Therefore the scheduler is working correctly; visible publication happens about **15–17 minutes after trigger time** because of the intentional rewrite delay.

### Backend quality gates now enforced
- Hybrid RSS importer now skips:
  - articles with **no image**
  - articles with **content under 600 chars**
- Local verification confirmed newly inserted records are now:
  - image present
  - full-length content (~5k–6k+ chars)
- Legacy bad short/no-image records were cleaned from MongoDB.

### Frontend/article presentation improvements now live
- Homepage supports **image-first card layout** plus **text-only headline strip** for no-image stories.
- Article page `More stories` now follows the same pattern as homepage.
- Sidebar no-image items no longer render broken/empty thumbnails.
- Added orphan-row safeguard so card grids do not end with a single stranded card.
- Added display-only short-title enhancement on article pages:
  - visible H1 can expand short titles for readability
  - SEO/OpenGraph/Twitter titles remain unchanged.

### Important live behavior note
- Homepage freshness ordering still uses **publishedDate**, not `created_at`.
- This means scheduler-imported stories can exist in production without always surfacing immediately on homepage top slots if their source `publishedDate` is older.
- This is currently a deliberate **no-change decision** to avoid destabilising working production.
- Revisit later only if homepage freshness becomes a clear editorial problem.

### Operational conclusion
- Scheduler: working
- Import pipeline: working
- Quality gates: working
- Layout/rendering for no-image stories: working
- Production left stable without changing homepage sort logic

### Next recommended step
- Observe the **12:00 UTC scheduler run** and confirm the same 15–17 minute publish pattern.
- After that, freeze content engine changes unless a production issue appears.


## SEO note — 13 March 2026 (article schema verification)

### What was checked
- Live article page source was tested with `curl`.
- Publisher/organization schema is present in raw HTML (`NewsMediaOrganization`, `ImageObject`, `Place`).
- `ArticlePageV2.jsx` does define a `NewsArticle` JSON-LD object in frontend code.
- However, raw initial HTML response does **not reliably expose `@type: NewsArticle`** in the first server response.

### Current interpretation
- Article structured data appears to be client-rendered after article fetch/render.
- This is weaker for Google News / indexing than having `NewsArticle` JSON-LD present in the initial HTML response.
- Backend already contains article HTML/JSON-LD machinery in `backend/server.py`, so the architectural path for a stronger fix already exists.

### Recommended future fix
- Move article `NewsArticle` JSON-LD into the **initial server HTML response** for article pages.
- Goal: ensure `curl` / crawlers can see full article schema without relying on client-side React render.
- This is a **high-value SEO hardening task**, but not a production emergency.

### Production decision
- Leave current live setup unchanged for now to avoid destabilising production.
- Revisit when doing next SEO hardening pass.

--------------------------------------------------
GOOGLE SEARCH CONSOLE MONITORING (POST-LAUNCH)
--------------------------------------------------

Purpose:
Monitor SEO health and indexing behaviour during the first 4–6 weeks after stable production launch.

The site infrastructure is now technically correct:
- robots.txt verified
- sitemap.xml active
- news-sitemap.xml active
- Google Analytics installed
- Google Search Console connected
- automated publishing running (06:00 / 12:00 / 18:00)

Because of this, the project now enters the observation phase rather than development changes.

--------------------------------------------------
1. Indexed Pages
--------------------------------------------------

Location:
Search Console → Pages

Current baseline (March 2026):
Indexed: ~16
Not indexed: ~68

Expected progression:

Week 1:
30–50 indexed pages

Week 2:
60–90 indexed pages

Week 4:
120–200 indexed pages

If indexing remains below ~40 pages after 3–4 weeks,
investigate crawl/indexing issues.

--------------------------------------------------
2. Search Impressions
--------------------------------------------------

Location:
Search Console → Performance

Expected growth pattern:

Week 1:
20–80 impressions per day

Week 2:
100–300 impressions per day

Week 4:
500–1500 impressions per day

Clicks normally appear after impressions grow.

--------------------------------------------------
3. Crawl Frequency
--------------------------------------------------

Location:
Search Console → Settings → Crawl stats

Expected progression:

Week 1:
~30 pages crawled per day

Week 2:
~80 pages crawled per day

Week 4:
200+ pages crawled per day

Growth indicates Google increasing trust in the site.

--------------------------------------------------
4. Search Queries
--------------------------------------------------

After several weeks, Search Console should begin showing
queries related to:

- Cheshire news
- Chester news
- Warrington news
- Cheshire business news
- planning applications Cheshire
- local economic news

These signals help guide editorial focus.

--------------------------------------------------
Important Operational Rule
--------------------------------------------------

During this monitoring phase:

DO NOT make major SEO or homepage algorithm changes
unless a clear technical issue appears.

Focus on:
- consistent publishing
- maintaining article quality
- keeping scheduler stable
- monitoring GSC metrics weekly


## Update — 13 March 2026 (midday scheduler verification + timezone note)

### 12:00 scheduler verification
- Midday scheduler run was verified successfully.
- New articles were inserted with `created_at` timestamps around **12:15–12:16 UTC**.
- This matches the expected behaviour:
  - scheduler trigger at 12:00
  - intentional 900-second rewrite delay
  - visible/import completion around 12:15–12:17
- Example newly inserted articles from the 12:00 cycle included:
  - Burglar jailed after gang raided Cheshire business stealing £50,000 worth of power tools
  - Live M6 Cheshire updates as crash causes delays
  - AI toys for children misread emotions and respond inappropriately, researchers warn
  - UK economy flatlines in January as people cut back on eating out
  - What on earth is going on with the oil price?
  - Council cannot appeal asylum seeker hotel ruling

### Important interpretation
- The content engine and scheduler are working correctly at midday as well as morning.
- If newly imported articles do not immediately appear at the top of homepage/API output, this is due to homepage/API surfacing logic using source/article `publishedDate` behaviour rather than import-time freshness.

### UK time / scheduler clock note
- Verified operationally that current scheduler timestamps are aligned with UK time for this period.
- On **13 March 2026**, UK local time is effectively **UTC/GMT**.
- Therefore current scheduler events logged at:
  - 06:00 UTC
  - 07:30 UTC
  - 12:00 UTC
  are also:
  - 06:00 UK
  - 07:30 UK
  - 12:00 UK
- Note for later: this alignment will change once British Summer Time begins.


## Planned next phase — Category architecture upgrade (March 2026)

### Goal
Improve editorial category purity while keeping the current scheduler and article volume stable.

### Current scheduler / volume to preserve
- Scheduler runs:
  - 06:00
  - 12:00
  - 18:00
- Current import pattern per cycle is approximately:
  - 2 Local
  - 1 UK
  - 2 Business
  - 2 Tech / AI
- Do not change volume yet.
- Do not change scheduler timing yet.

### Target category structure

#### Local
Must contain only Cheshire-specific news.

Desired Local topics:
- local government
- planning
- infrastructure
- transport
- community
- local economy
- local business openings
- education
- development projects

Desired Local source focus:
- Cheshire Live
- Warrington Guardian
- Chester Chronicle
- Macclesfield Express
- Crewe Chronicle
- Northwich Guardian
- Knutsford Guardian
- Nantwich News
- Winsford Guardian
- Runcorn & Widnes World

Operational note:
- crime / court / police stories should be limited or de-weighted where possible

#### UK
Should become a national economy / money / policy section.

Desired UK topics:
- finance
- money
- tax
- property market
- energy prices
- banking
- fintech
- AI regulation
- technology policy
- economic policy
- startups / investment

Desired UK source focus:
- Financial Times
- BBC Business
- BBC Technology
- Guardian Money
- MoneySavingExpert
- Sky Business
- ONS releases
- HM Treasury
- Bank of England
- City AM
- Reuters UK Business
- strong Google News economic feeds

#### Business
Must contain pure business news only.

Desired Business topics:
- company news
- industry developments
- markets
- earnings
- M&A
- retail sector
- manufacturing
- supply chains
- startup funding

Desired Business source focus:
- Financial Times Business
- Reuters Business
- Bloomberg Business
- BBC Business
- Guardian Business
- Sky Business

Should avoid:
- crime
- entertainment
- generic politics
- general UK filler

### RSS feed expansion plan
Expand source pool for:
- Cheshire local coverage
- UK economy / finance coverage
- AI / Tech coverage

Possible additional Cheshire feeds:
- Chester Chronicle
- Macclesfield Express
- Crewe Chronicle
- Northwich Guardian
- Knutsford Guardian
- Nantwich News
- Winsford Guardian
- Runcorn & Widnes World

Possible additional UK economy feeds:
- ONS
- HM Treasury
- Bank of England
- City AM
- Reuters UK Business
- property market feeds
- fintech feeds

Possible additional AI / Tech feeds:
- MIT Technology Review
- VentureBeat
- Wired
- DeepMind blog
- OpenAI blog
- AI regulation feeds

### Classification note
Do not rely only on title keywords for location/category logic.
Many RSS titles do not include clear locations.
Future improvements should consider:
- source-based weighting
- summary/content analysis
- location confidence scoring
- better Cheshire locality detection

### Implementation rules for next chat
Before any code changes:
1. Inspect current category logic
2. Inspect rss source configuration
3. Inspect backend category mapping
4. Inspect homepage/category feed logic

Files likely involved:
- backend/app/rss_sources.py
- backend/app/news_feed_service.py
- backend/server.py

Workflow rules remain:
- one terminal command at a time
- check state before modifying
- no manual file editing where avoidable

### Strategic objective
Move Cheshire Today closer to:
Local Economic Intelligence Platform for Cheshire

with cleaner separation across:
- Local
- UK economy / money / policy
- Business
- AI / Tech


## March 16, 2026 - Emergency stability update and pool-safety findings

### Reason for investigation
Production had shown disappearance of fresh articles, especially recent March 13-15 items, despite the intended 14-day active window. Investigation was completed before making any further pool/archive changes.

### Confirmed current live behaviour
Public API inspection confirmed:
- live active pool recovered beyond the damaged baseline of 101
- observed active count during investigation increased to 131 and then 146
- fresh March 16 articles are now persisting in the live API instead of disappearing
- current live date mix observed during investigation:
  - 2026-03-16: 37
  - 2026-03-15: 4
  - 2026-03-14: 1
  - 2026-03-12: 12
  - 2026-03-09: 7
  - 2026-03-08: 70

### Current live category mix observed
Public API sample showed:
- Local News: 32
- Business: 39
- Tech: 10
- UK News: 58
- Science: 6
- Health: 1

This means:
- ingestion is working
- fresh content is staying live
- visible pool is larger because articles are no longer being wrongly removed
- March 8 backlog still remains visible because the archive rule is age-based, not count-based

### Root cause of disappearing fresh articles
Investigation of git history and server logic confirmed two dangerous article-removal paths had existed:

1. Startup duplicate cleanup
- startup previously called auto_clean_duplicate_articles()
- this was identified as unsafe because it could remove legitimate recent articles using only the first 5 words of title
- this startup call is now disabled

2. Hard-delete safety cap at 100 visible articles
- cleanup_old_articles() previously deleted anything older than the 100th newest article by publishedDate
- this did NOT protect articles by import time
- therefore newly imported but slightly older-dated recent articles (for example March 13-15) could still be permanently deleted immediately
- this hard-delete cap is now disabled

### Important conclusion
The disappearance of March 13-15 articles was NOT consistent with the intended 14-day active policy.
Those articles were lost because unsafe hard-delete logic overrode the 14-day archive rule.

### Confirmed current safe/unsafe paths
Safe / currently acceptable:
- scheduled archive job still active at 01:30 using days_old = 14
- this matches the requirement that articles stay active for at least two weeks before automatic archiving
- post-import duplicate cleanup uses _remove_duplicates_internal()
- scheduled-generation cleanup also uses _remove_duplicates_internal()
- _remove_duplicates_internal() groups by exact full title, keeps the longest-content version, attempts archive first, and only removes basically empty broken items with no outbound link

Unsafe / do not restore:
- startup duplicate hard-delete cleanup
- hard-delete visible cap at 100
- any keep_visible / keep newest N automatic archive behaviour as a replacement for the 14-day rule
- automatic ratio rebalance for visible pool
- any logic that removes recent articles by pool size instead of article age

### Git-history findings relevant to future chats
Confirmed in git history:
- "Auto maintain 65 active articles" was previously introduced and then reverted
- archive window was previously extended from 7 days to 14 days
- automatic ratio rebalance was disabled by default
- March 16 emergency patch explicitly disabled:
  - startup duplicate cleanup
  - 100-article hard-delete safety cap

Therefore:
- do NOT reintroduce count-based pool maintenance
- do NOT replace the 14-day archive policy with keep_visible behaviour
- do NOT assume smaller visible pool = safer system

### Current interpretation of system health
As of this investigation:
- article generation/import pipeline is working
- fresh articles persist
- content lengths are healthy (multi-thousand-character articles observed)
- pool is safer than before, but larger than ideal because old articles are now surviving correctly until the 14-day window expires

This larger pool should NOT be treated as a bug by itself unless it causes a separate homepage or editorial issue.

### Working rule from this point
Before any future pool/archive modification:
1. Check git history first for prior reverted pool logic
2. Confirm whether proposed logic conflicts with the 14-day active requirement
3. Never reintroduce hard-delete behaviour for recent editorial content
4. Prefer archive-preserving behaviour only
5. Inspect current live API state before changing cleanup logic


--------------------------------------------------
UPDATE: 29 MARCH 2026 – HOMEPAGE LOGIC, LIVE DATA, AND PRODUCTION DIAGNOSIS
--------------------------------------------------

### Summary of work completed in this chat
This chat completed a major homepage logic stabilisation and production diagnosis cycle.

Completed:
- fixed admin "Force show on homepage" action so it actually sends authenticated requests and refreshes admin data correctly
- restored homepage freshness ordering after an earlier force_live boost caused older stories to outrank newer ones
- made `force_live` work without breaking hero / Top Stories freshness
- rebuilt and tested homepage locally multiple times using:
  - `npm run build`
  - `npx serve -s build`
- fixed repeated runtime crashes / blank-page issues caused by:
  - variables being used before declaration
  - duplicate `const k = articleKey(a)` declarations
  - corrupted code structure inside `isPropertyish`
  - misplaced dedupe and sorting logic
- implemented homepage dedupe across:
  - Latest
  - AI & Tech sidebar
  - Business sidebar
  - Finance sidebar
  - Property & Tax sidebar
  - AI & Business feed
  - More Stories
- fixed cross-sidebar duplication, especially Finance vs Property / Tax
- made More Stories:
  - fully populated
  - freshness-first
  - filtered against entertainment / celebrity / filler
  - stronger on local / business / finance / public-impact utility
- tightened Business & Finance / AI & Business quality rules to reduce soft culture / entertainment leakage
- tuned Top Stories away from entertainment and toward local/economic/public-impact stories
- verified local production-style output visually at multiple points during the chat

### Key commits / deployment state
A later homepage stabilisation commit was created and pushed:
- `6d40c63` — Fix homepage dedupe: sidebar isolation + property block repair + stability fixes

Additional homepage code in this chat also included:
- freshness-first ordering
- feed dedupe
- More Stories quality gating
- section ordering clean-up
- sidebar isolation

### Important homepage architecture conclusions from this chat
Homepage logic is now intentionally structured as:
1. fetch public article pool
2. apply editorial filters
3. build shared ranked pools
4. construct section-specific feeds
5. dedupe across sections where required
6. sort final feeds for stable rendering
7. render freshness-first homepage

Important final behavior:
- Latest = newest-first
- More Stories = newest-first with quality filter
- Top Stories = editorially filtered / weighted
- Business / Finance / Property sidebars = deduped and stabilised
- no blank-page crashes in the final validated local state

### Live production diagnosis completed
A production issue was investigated where the homepage appeared stuck at 27 March articles.

Findings:
- this was NOT caused by homepage code alone
- live public API initially had no 28–29 March articles
- manual live article generation was triggered successfully:
  - `/api/generate-articles`
  - returned success with fresh article generation
- after manual generation, live public API showed 28–29 March content, including:
  - 2026-03-29 local stories
  - 2026-03-28 business stories

Conclusion:
- homepage freshness logic was working
- the real production issue at that stage was missing fresh public data, likely due to scheduler/import inactivity or zero-result scheduled runs before manual generation

### Important live deployment / serving conclusion
Production domain behaviour was investigated in detail.

Confirmed:
- `cheshiretoday.co.uk` is served by the BACKEND web service, not the separate frontend migration static service
- backend serves SPA assets from:
  - `backend/frontend_build`
- relevant live backend code:
  - `_FRONTEND_DIR = Path(__file__).resolve().parent / "frontend_build"`
  - root `/` and SPA routes serve files from that folder

Important implication for future chats:
- production deploy for the visible site must be treated primarily as a BACKEND deploy if the backend-embedded React build is the live artifact
- do not assume the separate `cheshiretoday-frontend-migration` service controls the production domain
- verify what bundle/domain is actually serving before diagnosing frontend deployment mismatches

### Verified production status by end of chat
By the end of this chat:
- live API showed fresh March 28–29 articles
- live homepage screenshots matched the corrected homepage behaviour
- latest articles were surfacing again
- homepage no longer appeared stuck at March 27
- local final state was visually validated as stable and clean

### Remaining issues / next-phase tasks
Do next:
1. inspect Render logs when the automatic scheduler runs
2. confirm whether scheduled imports/article generation are running correctly after March 29
3. identify any obsolete Facebook auto-scheduler tasks/processes still logging or executing
4. disable/delete unused Facebook scheduler functionality if it is not part of active production operations
5. keep Render focused only on actively used automation and production tasks

### Explicit note about Facebook scheduler cleanup
User reported Render logs showing Facebook auto-scheduler activity even though Facebook automation is not being actively used.
This should be investigated in the next chat and removed/disabled if inactive, to reduce noise and avoid unnecessary work on Render.

### Working restart instruction for next chat
In the next chat:
- read `PROJECT_CURRENT_STATE_MASTER_MARCH_2026.md`
- read `PROJECT_HANDOVER_MASTER_MARCH_2026.md`
- assume homepage logic / dedupe / freshness work from this chat is complete
- start with Render scheduler/log inspection
- specifically investigate unused Facebook auto-scheduler jobs and remove/disable them if confirmed unnecessary

