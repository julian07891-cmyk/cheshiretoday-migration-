# Cheshire Today — Current State Master (Updated 12 March 2026)

## 1. Executive summary
Cheshire Today is live on Render at `https://cheshiretoday.co.uk` with SSL issued for both root and `www` domains. Frontend, backend API, MongoDB article storage, admin login, scheduler, archive system, sitemap, robots, and analytics are all operational.

This session moved the project forward in four major areas:
1. restored live article imports after the site went stale,
2. re-established the intended hybrid RSS + Perplexity publishing model,
3. fixed article-body paragraph formatting for future Perplexity rewrites,
4. diagnosed the difference between infrastructure problems and editorial / ordering problems.

The project is still live and functioning, but it is **not yet in a fully closed / maintenance-only state**. The core system is up; remaining work is mainly around:
- reliable Perplexity-first publishing,
- rewriting all thin recent articles,
- removing poor-fit crime / low-value stories,
- and deploying the homepage freshness ordering fix currently changed locally but not yet committed.

---

## 2. What was done in this session (detailed)

### A. Article page text design and typography
Work completed:
- Confirmed article page body rendering was not using the intended paragraph-friendly design.
- Located `ArticlePageV2.jsx` rendering logic and confirmed body content was still effectively flattening content in some cases.
- Updated article body rendering so article text is output as **real paragraphs** instead of a dense block.
- Confirmed article container uses the updated typography shell with the intended visual style.
- Regenerated / updated live article formatting for many articles.

Important implementation details:
- `autoLinkContent()` was changed so plain text is converted into paragraph blocks rather than simple newline-to-`<br/>` output.
- Existing live articles were updated in bulk during this session.

Result:
- Many live articles now render in the newer, cleaner article-body style.
- However, articles rewritten **before** the final Perplexity paragraph-formatting fix may still contain compressed text until regenerated again.

### B. Article-page metadata clean-up
Work completed:
- Removed the location badge above article hero titles on article pages.
- This specifically removed the unreliable `· LOCATION` output (for example `UK NEWS · MACCLESFIELD`) because location extraction is not yet trustworthy enough for prominent display.

Result:
- Article hero header is cleaner and avoids inaccurate location signalling.

### C. Related / sidebar category badge clean-up
Work completed:
- Removed category badges from `RelatedArticles.jsx` so article page side blocks do not display misleading tags such as `UK News` or `Business` in contexts where they read as wrong or noisy.

Result:
- Sidebar/related article presentation is cleaner.
- Reduced risk of confusing category labels in article-side modules.

### D. Homepage sticky sidebar experiment
Work attempted:
- Multiple sticky-sidebar experiments were tested on `HomePageV1.jsx`.
- Variants included making the full sidebar sticky, moving sticky to an inner wrapper, splitting Business blocks, and changing where sticky started.

What happened:
- Sticky behavior proved unreliable and visually harmful in the current homepage layout.
- Several iterations caused misalignment between the Latest column and the Business sidebar.
- A full rollback was done to restore the stable, aligned non-sticky homepage layout.

Result:
- Homepage is back to the known-good non-sticky aligned layout.
- Sticky sidebar is **not** currently implemented.
- This was the correct choice for now.

### E. Git / deploy / technical checks completed
Completed in this session:
- Saved and pushed frontend article/page cleanup work to git.
- Verified production deployment.
- Verified:
  - `robots.txt` returns `200`
  - `sitemap.xml` returns `200`
  - Google Analytics / tracking snippets exist in live HTML
  - canonical / OG / Twitter metadata are present
- Observed that homepage JSON-LD block appears effectively empty and still needs future structured-data refinement.

### F. Diagnosis of disappearing / stale articles
Problem observed:
- User reported that new imports were not appearing and articles looked missing.

Diagnostics performed:
- Checked live `/api/articles` dates.
- Confirmed no new imports on 10–11 March during the failure window.
- Confirmed scheduler itself was still running.
- Confirmed `use_perplexity=false` imports worked immediately.
- Confirmed `use_perplexity=true` calls appeared to hang.

Root causes identified during session:
1. **Perplexity-enabled import path was stalling**.
2. **Archive cleanup kept running daily**, so visible live pool shrank while fresh imports were not replenishing it.
3. Emergency RSS-only refill repopulated the site, but published thin RSS snippets live.

### G. Import pipeline fixes implemented in backend
#### 1. Removed sports import from hybrid import path
- Sports import was disabled to align with editorial strategy and reduce noise.

#### 2. Added timeout/fallback protection around Perplexity rewrite calls
- Wrapped Perplexity content-generation calls in timeout protection.
- If Perplexity rewrite fails or times out, import falls back to RSS/original content instead of stalling the whole import.

#### 3. Added timeout/fallback around Cheshire Perplexity search fallback
- Wrapped `search_cheshire_news()` fallback in timeout protection.
- Prevents total import blockage when Perplexity search stalls.

#### 4. Removed default 15-minute rewrite delay
- Found that `rewrite_delay_seconds` defaulted to `900` seconds.
- This did **not** help Perplexity research; it simply made the server sleep before rewriting.
- Default delay was changed to `0`, while keeping Perplexity rewriting enabled.

Result:
- Infrastructure path is now safer and less likely to block on Perplexity.
- However, Perplexity-enabled import requests can still feel slow because the import route remains synchronous and rewrite work can take a long time before responding.

### H. Perplexity prompt inspection and upgrade
Original question addressed:
- Confirm whether the original implementation truly used Perplexity to research from multiple online sources rather than just expand the RSS summary.

Findings:
- The original prompt was too close to “expand the summary into a full article.”
- It used source URL and citations, but did **not** strongly force multi-source research + verification.

Changes implemented:
- Updated the Perplexity system prompt to say:
  - research the news story using the provided source URL and other reliable sources online,
  - write a fully original article,
  - verify key facts using the source URL and other reputable sources when available.

Result:
- The intended publishing logic is now much closer to the real project model:
  - RSS finds story,
  - Perplexity researches and rewrites,
  - article goes live.

### I. Paragraph formatting fix inside Perplexity service
Problem observed:
- Newly generated Perplexity articles were still not rendering with the intended paragraph design because paragraph breaks were being flattened during cleanup.

Cause found:
- In `backend/app/perplexity_service.py`, the cleanup step used:
  - `re.sub(r'\s+', ' ', content).strip()`
  - and same for `retry_content`
- This collapsed newlines into single spaces, destroying paragraph structure.

Fix implemented:
- Replaced those calls with whitespace cleanup that preserves newlines:
  - `re.sub(r'[ \t]+', ' ', content).strip()`
  - same for `retry_content`

Result:
- Future Perplexity-regenerated articles should retain paragraph breaks and render in the updated article-body design.
- Articles generated before this fix need regeneration to pick up the improved formatting.

### J. Live regeneration of recent content
Actions performed:
- Used admin login and live admin token.
- Triggered `POST /api/admin/regenerate-recent-content`.
- Confirmed regeneration worked for at least part of the recent live set.
- Verified one very thin article (`Predator who sexually abused young girl...`) had been upgraded from a 46-character stub to a full multi-paragraph article.

Observed output during session:
- One regenerate pass returned:
  - `success: true`
  - `recent_articles_found: 25`
  - `regenerated: 15`
  - `estimated_cost_usd: 0.125`

Result:
- Regeneration route is operational.
- It can rewrite thin live articles into substantial content.
- But it did **not** yet upgrade all recent thin items in one pass.

### K. Homepage freshness / ordering diagnosis and local fix
Problem observed:
- Fresh articles existed in MongoDB, but homepage / API order looked random and older high-score stories still appeared above fresh ones.

Cause found in `HomePageV1.jsx`:
- `rankScore()` weighting was extremely strong:
  - `is_priority_cheshire +1000`
  - `featured +300`
  - `is_secondary_cheshire +120`
  - freshness contributed only a small amount in comparison.
- So older priority stories could outrank truly fresh content.

Local fix implemented:
- Changed homepage pool ordering from:
  - rank first, freshness second
- to:
  - freshness first, rank second

Result:
- On local build, newest articles appear at the top as expected.
- **Important:** this homepage freshness ordering fix is currently a **local uncommitted frontend change** (`frontend/src/pages/HomePageV1.jsx`) and was **not yet committed/pushed** at the point this file was updated.
- Therefore production may still show mixed/random ordering until that frontend file is committed and deployed.

---

## 3. Current verified production state (as of end of this session)

### Infrastructure
- Production domain: `cheshiretoday.co.uk`
- Hosting: Render
- SSL: working for root and `www`
- Backend is live and starts successfully after deploy
- Scheduler starts successfully on deploy
- Health endpoint `/health` returns `200`
- `robots.txt` returns `200`
- `sitemap.xml` returns `200`
- Analytics scripts are present in live HTML

### Scheduler / automation
Confirmed in logs during this session:
- Morning article generation job active
- Midday article generation job active
- Evening article generation job active
- Daily Brief job active
- Weekly Roundup job active
- Archive cleanup job active at 01:30

### Live content state
Confirmed from live API during this session:
- Fresh articles from **11 March 2026** and **12 March 2026** are now present
- Therefore imports / regeneration are functioning again
- However, ordering is still mixed in production until homepage freshness fix is deployed

### Current content quality state
- Many live articles are now long-form and healthy (`5000+` chars common)
- But several recent live articles were still thin during the last audit (for example 31, 42, 57, 66, 76 chars etc.)
- Regeneration route improved some, but not all, recent articles in a single pass

### Current article rendering state
- Old/full articles render properly
- Some newly regenerated/future regenerated Perplexity articles should now render with improved paragraphs because backend formatting fix was committed and pushed
- Articles rewritten before the paragraph-preservation fix still need regeneration to adopt the improved text design

---

## 4. What works right now

### Confirmed working
- Frontend and backend deploy on Render
- SSL / domain / live site
- Admin login (`/api/admin/login`)
- Scheduler boot and job registration
- Archive cleanup scheduling
- Robots and sitemap
- RSS/hybrid import route with `use_perplexity=false`
- Live regeneration route (`/api/admin/regenerate-recent-content`)
- Perplexity service integration
- Perplexity rewrite prompt now oriented toward research + verification
- Paragraph-preserving formatting for future Perplexity content
- Regeneration of recent thin articles works at least partially
- Homepage freshness fix works locally

### Confirmed working examples from this session
- Thin live article upgraded into substantial content after regeneration
- Fresh March 11–12 content present again in live API
- Long-form article bodies visible in multiple live API records

---

## 5. What does NOT fully work yet / still needs action

### A. Production homepage ordering still not fully corrected
- Local fix exists and works.
- Production still likely shows mixed chronology because `HomePageV1.jsx` freshness-first ordering was not yet committed/pushed.

### B. Not all recent thin articles have been rewritten yet
- Regeneration is partial; one pass rewrote 15 of 25 recent articles.
- Some live articles remain too short and should not be considered acceptable final live state.

### C. Perplexity-enabled import request still feels slow / blocking in direct curl tests
- `use_perplexity=true` requests still appear to hang from the client side because route is synchronous and can take a long time.
- This does **not** mean Perplexity architecture is absent; it means execution/response timing is still awkward for live use.

### D. Editorial filtering still needs attention
- Crime-heavy / poor-fit stories still entered live pool during this session.
- This remains inconsistent with the project’s intended positioning.

### E. Structured data still incomplete
- Homepage JSON-LD appears effectively empty and should be improved in a later session.

---

## 6. Important conclusions from this session

1. **The original hybrid architecture was not wrong.**
   The intended model remains correct:
   RSS source discovery → Perplexity research + rewrite → publish.

2. **The core failure was execution reliability, not project concept.**
   The combination of stalling Perplexity paths + archive cleanup made the site appear empty/stale.

3. **Emergency RSS-only refill was useful but compromised content quality.**
   It repopulated live content fast, but published thin snippets that required later regeneration.

4. **Perplexity research/rewrite is now better specified than before.**
   The prompt now explicitly asks for research + verification rather than summary expansion.

5. **Homepage freshness remains the main frontend issue.**
   The local fix exists but still needs to be committed and deployed.

---

## 7. Current priority actions for the next session

### Highest priority
1. **Commit and deploy `frontend/src/pages/HomePageV1.jsx` freshness-first ordering fix**
   - this should make new articles rise correctly to the top on production

2. **Run regenerate-recent-content again until no recent live articles remain under acceptable length**
   - operational target: no recent live articles under ~1000 chars

3. **Audit recent live pool and remove bad-fit crime-heavy stories if necessary**
   - especially those inconsistent with Local / Business / AI / Finance strategy

### Secondary priority
4. Re-test whether scheduled Perplexity-first generation now behaves acceptably in practice
5. Tighten any remaining short-article acceptance thresholds if needed
6. Refine structured data / JSON-LD later

---

## 8. Persistent project memory / operating rules (carry forward)

### Workflow preferences
- No manual file edits; apply changes via terminal commands/scripts
- One command at a time
- Always check current state before modifying anything
- Verify after each change before moving to the next
- For coding tasks, user prefers strict step-by-step guidance
- Prefer running from project root
- Prefer `grep` over `rg` because `rg` is not installed in user environment
- Avoid heredoc patterns that pipe raw JSON into `python3 - <<'PY'`; prefer `python3 -c`, `python3 -m json.tool`, or save to file first

### Project positioning / strategy
- Cheshire Today is not a generic local news site; it is intended as a **local economic intelligence platform for Cheshire**
- Core positioning: Local + Business + Finance + AI/Tech authority
- Keep minimal top nav aligned with strategy (Local / Business / UK)
- AI/Tech should be surfaced via homepage sections/guides rather than top nav
- Preferred category/pillar order: Local, Business, AI & Tech, Finance, Tax
- Long-term editorial mix target: **40 / 40 / 20**
  - Local
  - Business + Finance
  - AI / Tech
- De-emphasise crime / sensational / sports / celebrity / entertainment content

### Content / operational standards
- Live content quality floor should remain strong; historically active articles were cleaned to **1000+ chars**
- Use regenerate route when short articles appear
- Archive weak outliers if regeneration does not improve them enough
- Scheduler cadence remains:
  - 06:00
  - 12:00
  - 18:00
- Archive cleanup runs daily at **01:30 UTC**
- Daily Brief runs at **07:30 UTC**
- Weekly Roundup runs Sunday at **09:00 UTC**

### Deployment / environment notes
- Domain already live on Render (`cheshiretoday.co.uk`)
- Render auto-deploy disabled historically for some services; manual awareness still important
- Local frontend verification preference remains:
  - `npm run build`
  - `npx serve -s build`
- Avoid `npm start`/CRACO dev server for final verification because of historical local listener issues

### Monetisation / project business memory
- Affiliate-first monetisation strategy remains in force
- Amazon Associates is currently available
- Non-Amazon monetisation/features should remain controlled / feature-flagged until approved and UX-ready
- Newsletter subject line strategy remains: emphasise financial impact + local relevance + authority; improve opens without harming strong click-to-open performance

---

## 9. Current git / code state snapshot at end of this session

### Backend changes committed/pushed in this session
Confirmed commits include:
- `5a892be` — upgraded Perplexity rewrite prompt to research and verify sources
- `41ff27e` — prevent Perplexity search/rewrite stalls in hybrid import; remove sports import
- `53d5911` — fix Perplexity article formatting so paragraphs render correctly in article design

### Frontend state at end of session
- `frontend/src/pages/HomePageV1.jsx` has a local homepage freshness-first ordering fix
- At the time of writing this file, that frontend change was **still modified locally and not yet committed/pushed**
- This is likely why production ordering still appears mixed/random

### Local repo note
- There is also an untracked local item named `full-scrape-prod` visible in git status; this appears unrelated to production behavior but should be reviewed/cleaned later if needed

---

## 10. Short final assessment
The system is no longer in emergency failure state.

It is now in a **partially restored but not yet fully refined** state:
- live site works,
- fresh content exists again,
- Perplexity regeneration works,
- formatting fix for future rewrites is deployed,
- but homepage production ordering still needs deployment and some recent thin articles still need regeneration/removal.

The next session should therefore begin with:
1. deploy the homepage freshness fix,
2. continue regenerating recent thin articles until the live pool is clean,
3. re-apply editorial discipline to remove crime-heavy low-value stories,
4. then reassess whether the system is finally back to the intended hybrid publishing standard.

---

## 11. Recommended new-chat resume prompt
Use this in the next fresh chat:

`Continue the Cheshire Today project from the current March 2026 master state. Respect the workflow: check state first, no manual file edits, one command at a time, verify after each step. Priority order: (1) commit/deploy the local HomePageV1 freshness-first ordering fix, (2) regenerate/re-audit recent thin live articles until the recent pool is clean, (3) remove crime-heavy / poor-fit stories from active live pool if needed, (4) then reassess whether scheduled hybrid RSS + Perplexity publishing is back to the intended standard.`


---

## 12. Detailed update — March 19, 2026 session (duplicate protection, latest ordering, QA, deploy)

### Session goals
This session focused on stabilising the live content pipeline and validating production-critical behaviour before moving toward monetisation readiness. The main objectives were:
- restore code to the last good deployed baseline when intermediate experiments drifted,
- diagnose and fix duplicate live article creation,
- ensure the **Latest** feed behaves as a true newest-first feed,
- preserve slug URL support without breaking older compatibility paths,
- run a practical QA pass against production,
- deploy only the minimum safe set of fixes.

### What happened in detail

#### A) Business/category experiments were intentionally rolled back
At the start of the session, several frontend and backend experiments had been made while trying to improve Business category quality and homepage composition. These included temporary tightening of business filters and fallback rules. After inspection, it became clear those changes were not the right long-term fix because they were overfitting weak input rather than improving the source pool.

Action taken:
- local edits were restored back to the last deployed baseline using git restore,
- codebase was confirmed clean against `origin/full-scrape-prod`,
- conclusion documented: upstream feed/input quality is more important than over-tuning frontend filters.

This was an important strategic reset. It prevented accidental drift away from the stable production architecture.

#### B) Temporary feed expansion was tested, then intentionally reverted
To test whether business/finance scarcity was mainly a feed-supply issue, the following business sources were temporarily added into `backend/app/news_feed_service.py`:
- Guardian Business
- Reuters Business
- City AM

The feed registry was verified and a controlled import was run. This showed that feed expansion did improve source variety somewhat, but it also made clear the main bottleneck was still the import allocation logic and not just feed count.

Because the immediate priority then became restoring exact parity with the last stable deployed code before making structural feed decisions, `backend/app/news_feed_service.py` was restored back to `origin/full-scrape-prod`.

Important note:
- these temporary feed additions were **not** left in the final deployed code from this session.

#### C) Production duplicates were discovered, diagnosed, and cleaned
A critical issue surfaced during testing: duplicate live articles were appearing in production.

Confirmed symptoms:
- the same source URL could appear more than once in live `/api/articles` results,
- in one confirmed case, identical City AM article URL/title/published date appeared twice with different Mongo IDs,
- duplicate scan across the latest 200 live items returned multiple repeated `source_url` values.

Key diagnosis:
- article insertion paths in `backend/server.py` were using an in-memory `existing_titles` snapshot plus plain `insert_one(article)` calls,
- there was a unique index on `articles.title`, but no enforced uniqueness on `source_url`,
- unlike digest sending logic, article imports did not use an atomic duplicate-safe pattern.

Immediate remediation performed:
- confirmed duplicate live records via production API,
- archived/deleted the extra live duplicates one by one through the live delete endpoint,
- re-ran production duplicate scan until latest-200 returned `[]`.

Confirmed cleanup outcome:
- live active pool duplicate scan is clean again.

#### D) Root-cause duplicate prevention fix was implemented in backend
After cleanup, the real fix was added to `backend/server.py`.

Final backend protections added:
1. `DuplicateKeyError` import from `pymongo.errors`
2. unique index creation for `articles.source_url`
3. `try/except DuplicateKeyError` around article inserts in the RSS/UK import path

This moved duplicate prevention from a soft in-memory snapshot model toward proper DB-level enforcement on the article source URL.

Why this matters:
- repeated manual imports are now much safer,
- scheduler/manual overlap is much less likely to create duplicate live articles,
- DB-level uniqueness now protects the real canonical source identity instead of only relying on title matching.

#### E) Duplicate protection was tested live after the fix
After deploying the backend duplicate-protection change, a controlled small production import was run:
- `count=10`
- `include_uk_news=true`
- `rewrite_delay_seconds=0`

The import completed successfully and a fresh duplicate scan over the latest 200 live articles returned `[]`.

This is the most important operational validation from this session:
- duplicate cleanup worked,
- duplicate prevention fix held under a post-fix live import.

#### F) Latest ordering problem was isolated correctly
A separate production issue remained: the **Latest** section did not behave as a true newest-first feed.

Important finding:
- backend `/api/articles` mostly sorted correctly at query level,
- frontend sort experiments alone did not fully solve the visible problem,
- the actual root cause in homepage composition was that Latest used the shared `mark(a)` dedupe gate.

Because earlier sections could consume newer stories first, Latest was becoming:
- “latest remaining after other sections”
not:
- “true latest feed”.

Final homepage fix applied:
- in `frontend/src/pages/HomePageV1.jsx`, the `mark(a)` gate was removed from the Latest feed builder.

Result:
- Latest now behaves as a true newest-first list rather than a residual pool.
- This was manually validated after rebuild and user confirmed it as **fixed**.

This is one of the most important editorial correctness fixes in the whole project.

#### G) Date display was simplified for clearer visual ordering
There was also confusion caused by mixed relative/absolute timestamps such as:
- `Just now`
- `14h ago`
- `18 Mar`

That made correctly sorted lists look visually inconsistent. In `frontend/src/components/CompactArticleCard.jsx`, the date display was changed away from mixed relative labels and toward a clearer explicit date/time display.

This is a display-layer improvement rather than a sorting fix, but it helps users understand chronology much more clearly.

#### H) Slug support was preserved strategically rather than forced globally
Slug URL behaviour was reviewed because some article paths were showing slug URLs while others were still ID-only.

Important conclusion from code inspection:
- mixed slug/non-slug behaviour was not accidental,
- it exists because the project is in a staged migration state with both routes supported:
  - `/article/:articleId`
  - `/article/:articleId/:slug`
- old fallbacks were kept intentionally for backward compatibility.

Safe compromise chosen:
- do **not** rip out all legacy ID-only fallbacks in one go,
- keep compatibility paths intact for now,
- ensure main card-building flow is slug-forward for new content.

Active change kept:
- `HomePageV1.jsx` `toCard()` now uses `buildArticleUrl(a)` so core homepage cards generate slug URLs.

Important note:
- many older/legacy fallback paths still exist elsewhere in the frontend and may still produce ID-only links,
- this is currently accepted as a compatibility layer, not treated as a blocker for pushing the stable fix set.

#### I) QA pass results from this session
Production/site QA carried out during this session produced the following results:

##### Passed
- duplicate scan over latest 200 live articles: `[]`
- latest feed ordering issue: fixed after removing shared dedupe from Latest
- image coverage check over latest 50: `0` missing images
- content quality floor over latest 50: minimum content length was comfortably above 1000 chars
- controlled post-fix import completed successfully without reintroducing duplicates

##### Known remaining limitations / not fully solved in this session
- category balance remains weak in the observed live sample (Local-heavy, low Business/Money/Tech counts)
- article routing is still mixed between slug-forward and legacy ID-only paths depending on component
- not every user-facing path has yet been migrated to slug-only navigation
- business/finance source/feed strategy still needs a later dedicated pass, but only now that the pipeline is stable

#### J) Final code changes that remained staged, committed, pushed, and deployed
Final deploy set from this session was intentionally minimal and production-relevant:

1. `backend/server.py`
- add `DuplicateKeyError` handling
- add unique `source_url` index creation
- wrap article insert path with duplicate-safe try/except

2. `frontend/src/components/CompactArticleCard.jsx`
- simplify / clarify article date display

3. `frontend/src/pages/HomePageV1.jsx`
- remove shared `mark(a)` dedupe gate from Latest feed so Latest is truly newest-first
- keep homepage card path slug-forward through `buildArticleUrl(a)` in `toCard()`

These changes were committed and user reported they were deployed.

### Net result at end of session
At the end of this session, the project is in a much safer and more production-trustworthy state than it was at the start.

#### What is now materially better
- live duplicate articles were cleaned up,
- duplicate prevention is now far stronger,
- Latest feed now behaves like a real news feed should,
- homepage card path is slug-forward for new content in the main flow,
- no broad destabilising structural changes were left in place,
- code drift from baseline was kept limited to the minimum set of fixes that solved real production problems.

#### What should happen next (priority order)
1. Run a dedicated business/finance/tech supply audit and improve category balance carefully.
2. Continue gradual slug migration only on high-traffic user-facing paths, while preserving backward compatibility.
3. Freeze structural code after validation and move into monetisation-readiness work.
4. Perform affiliate-readiness audit before applying to networks.

### Updated practical recommendation for next chat
Use this next-chat resume prompt:

`Continue the Cheshire Today project from the March 2026 master state. Respect the workflow: check state first, no manual file edits, one command at a time, verify after each step. Assume latest duplicate-protection fix is deployed, Latest feed true newest-first fix is deployed, and main homepage card path is slug-forward. Priority order now: (1) audit category balance/business-money-tech supply, (2) review remaining legacy non-slug user-facing paths without breaking compatibility, (3) lock stable production code, (4) run affiliate/monetisation readiness audit before applications.`


## SESSION UPDATE — 21 MARCH 2026 — GUIDES / MONETISATION / ARTICLE FUNNEL DEBUG SESSION

This session focused on recovering, testing, and validating the non-Amazon guide / authority-page monetisation system, restoring guide routing, upgrading the first finance guide into a real money-page template, and debugging article-page guide injection. This session also included several failed attempts and regressions; they are preserved below because they matter for future continuity and for avoiding repeated mistakes.

### 1) Objective of this session
The user wanted to:
- verify the current codebase and test whether the stored monetisation system could be safely reinstated,
- test guide / authority-page rendering locally,
- restore any broken code needed to support future affiliate approvals,
- confirm what works versus what only exists in backups,
- update the master March 2026 state file with a detailed record before moving into a fresh chat.

The session therefore moved through four major phases:
1. recover and validate hidden/disabled monetisation code,
2. restore and test the guide route and guide rendering,
3. upgrade finance guide data into a real local money-page template,
4. debug article-page guide injection and separate true blockers from feature-flag behaviour.

### 2) Monetisation system recovery — what was found
Initial inspection showed that the non-Amazon monetisation system was not actually removed from the project; it was partially disabled / hidden.

Confirmed components / config found in source:
- `frontend/src/config/features.js`
- `frontend/src/config/monetisationTools.js`
- `frontend/src/components/homepage/HeroMonetisationStrip.jsx`
- guide / authority-page backend endpoints in `backend/server.py`
- guide page component `frontend/src/pages/AuthorityPage.jsx`
- guide route was present only in backup `App.js` variants, not in the active router.

Important strategic finding:
- Amazon monetisation remained the only intended live monetisation path.
- Non-Amazon monetisation was intentionally feature-flag controlled.
- The system had already been architected but was only partially wired into active frontend code.

### 3) HeroMonetisationStrip recovery and code repair
#### A) Broken import bug found in active component
`frontend/src/components/homepage/HeroMonetisationStrip.jsx` contained a corrupted import line that had previously been introduced during earlier work. The file started with an invalid fragment similar to:
- stray import text,
- broken `FEATURES` reference,
- invalid syntax before the real React import.

This corruption was one of the causes of earlier build freezes / failures.

#### B) Fix applied
The broken top lines were removed, leaving a clean header:
- `import React, { useMemo } from "react";`
- `import { FEATURES } from "../../config/features";`
- `import { monetisationTools } from "../../config/monetisationTools";`

Result:
- `HeroMonetisationStrip.jsx` became syntactically valid again,
- local build succeeded,
- component could be tested under the feature flag.

#### C) `monetisationTools.js` restored from disabled backup
The active `frontend/src/config/monetisationTools.js` only contained an empty export / disabled placeholder.

Restoration performed:
- copied back the prior guide / tool definitions from the saved backup file,
- verified categories such as mortgages, savings, tax, credit, energy, property, AI were restored.

This was important because `HeroMonetisationStrip.jsx` expects named collections such as:
- `monetisationTools.credit`
- `monetisationTools.energy`

Result:
- tool data structure was restored successfully,
- local build passed.

#### D) Feature flag used only for local testing
For visual validation only, `frontend/src/config/features.js` was temporarily changed:
- `NON_AMAZON_MONETISATION_ENABLED: false` -> `true`

This was later reverted deliberately before production-safe commits.

### 4) Local homepage monetisation strip test
After restoring:
- the monetisation tools config,
- the feature flag,
- the strip component,

local homepage testing showed the strip could render correctly once mounted.

Initially it remained invisible because:
- the component existed,
- the flag was on,
- but it was not mounted anywhere in active homepage code.

### 5) HomePageV1 changes — mounting the monetisation strip
#### A) Import added
`frontend/src/pages/HomePageV1.jsx` was updated to import:
- `HeroMonetisationStrip` from `../components/homepage/HeroMonetisationStrip`

#### B) Component inserted into active layout
The strip was inserted above the main two-column content area and below the hero/top section.

After local build + browser verification:
- strip became visible,
- it displayed cards such as credit cards / broadband / energy,
- styling was aligned with the site,
- layout did not break.

#### C) Important observation
Two of the three strip cards initially 404’d because their guide slugs did not yet exist in authority pages. This was a data issue, not a component issue.

### 6) Guide route / authority page recovery
#### A) Guide page existed but active router did not expose it
Findings:
- `frontend/src/pages/AuthorityPage.jsx` existed and was functional,
- backend endpoints for `/api/authority-pages` existed,
- but active `frontend/src/App.js` did not include:
  - `import AuthorityPage ...`
  - `<Route path="/guides/:slug" element={<AuthorityPage />} />`

#### B) Fix applied
`App.js` was updated to:
- import `AuthorityPage`,
- add active route `/guides/:slug`.

Result:
- previously blank guide page paths started rendering locally.

### 7) Authority pages backend inspection and seeding
The backend already had an admin seed route:
- `POST /api/admin/seed-authority-pages`

Seed definitions found in `backend/server.py` included draft stubs for:
- `best-mortgage-rates-uk`
- `best-credit-cards-uk`
- `best-savings-accounts-uk`
- `council-tax-bands-cheshire`

The user logged in through the admin endpoint and seeded these pages.

Important detail:
- a temporary token worked,
- attempted use of a presumed “permanent token” failed with `Invalid or expired token`,
- therefore the session proceeded with fresh admin tokens from `/api/admin/login`.

### 8) Additional missing guide pages created to prevent 404s
The homepage strip required guide slugs that did not yet exist.

Created via admin upsert API:
- `best-broadband-deals-uk`
- `cheap-energy-tariffs-uk`

Both were created as draft authority pages with intro-only content so the links could resolve during local testing.

Result:
- all three homepage strip links resolved locally,
- no more strip-level 404s.

### 9) AuthorityPage.jsx inspection and rendering fixes
#### A) Initial rendering limitation discovered
`AuthorityPage.jsx` only rendered:
- `intro` sections,
- `tool` sections.

It did **not** render generic `content` sections.

This caused upgraded guides to look thin even when backend data contained multiple content blocks.

#### B) Fix applied
`AuthorityPage.jsx` was extended to:
- derive `contentSections = sections.filter((s) => s?.type === "content")`
- render them as structured sections between intro and affiliate/tool areas.

Result:
- headings and long-form content became visible,
- guide pages started looking like real content assets instead of stubs.

### 10) Best-credit-cards guide upgrade — first real money-page template
The guide `best-credit-cards-uk` was repeatedly upgraded via admin upsert calls.

#### Evolution of this guide during session
##### Stage 1 — seed stub
Original state:
- intro draft only,
- empty tool block,
- no real SEO / trust / decision-support structure.

##### Stage 2 — content sections added
Structured content added:
- intro,
- “Best credit cards in the UK right now”,
- “How to choose the right credit card”,
- “Eligibility and risks”,
- “Frequently asked questions”,
- retained tool section.

##### Stage 3 — tool placeholders removed from top until data quality improved
It became clear that empty placeholder tools (“Link pending”) weakened the page. The frontend was adjusted so tool blocks only rendered if `affiliate_link` was non-empty.

##### Stage 4 — monetisation tools reintroduced as placeholders
Later, multiple supported `tool` sections were added to the same guide using the existing schema:
- Barclaycard Platinum (0 percent purchase)
- NatWest Balance Transfer Card
- American Express Cashback Card
- HSBC Purchase Plus Credit Card

This created a real UI structure for:
- Best Pick,
- Quick Comparison,
- Recommended Tools,
while still using placeholder `#` links locally.

### 11) AuthorityPage UX / template improvements
Several iterative template improvements were made locally:

#### A) Best Pick and Quick Comparison hierarchy
Goal achieved:
- Best Pick uses only the first tool,
- Quick Comparison uses the remaining tools.

This removed duplication and created the desired 3-layer structure:
1. Best Pick (dominant CTA)
2. Quick Comparison (alternatives)
3. Content + FAQ + disclosure

#### B) Empty grid issue solved
At one point only 2 comparison cards remained after promoting the first tool to Best Pick, creating an unprofessional empty space.

Resolution:
- added a fourth tool entry (HSBC Purchase Plus Credit Card)
- Quick Comparison then had 3 cards after the first tool was reserved for Best Pick.

#### C) CTA wording refined
The Best Pick CTA text was adjusted away from generic wording toward more finance-appropriate language:
- from `Compare now`
- to `Check eligibility`

This was considered more appropriate for UK financial comparison intent.

### 12) AuthoritySection model limitation discovered
An attempt was made to introduce a richer `top_picks` section with nested `items` data.

Result:
- backend saved only supported flat fields,
- nested `items` array was discarded.

Inspection of backend model confirmed:
`AuthoritySection` only supports:
- `type`
- `title`
- `content`
- `name`
- `rating`
- `affiliate_link`

Important conclusion:
- do not expand backend schema casually at this stage,
- use multiple `tool` entries to represent top picks / comparisons instead.

This is an important memory for future chats.

### 13) HomePage monetisation strip final test outcome
With route + pages + data in place, local homepage tests showed:
- strip visible,
- all cards resolving,
- feature-flag-driven behaviour working.

However, the strategic decision for production remained:
- keep `NON_AMAZON_MONETISATION_ENABLED` set to `false` in active production-safe code,
- do not expose non-Amazon guide monetisation in production until affiliate approvals / content maturity justify it.

### 14) Commits made during this session (important persisted code changes)
Two clean commits were made and pushed/deployed during this session:

#### Commit 1
`70b0804`
Message:
`Fix monetisation system: repair HeroMonetisationStrip, restore monetisation tools config, keep feature flag OFF for production safety`

Scope:
- repaired HeroMonetisationStrip syntax,
- restored `monetisationTools.js`,
- kept live feature flag OFF.

#### Commit 2
`6f1e693`
Message:
`Improve category override accuracy by requiring 2 keyword matches`

Scope:
- backend `news_feed_service.py`
- changed category override behaviour from 1 keyword match to requiring 2 matches.

#### Commit 3
`073a13e`
Message:
`Enable guides system: add AuthorityPage route and mount monetisation strip (feature-flag controlled)`

Scope:
- added guide route to active `App.js`
- mounted homepage monetisation strip in `HomePageV1.jsx`
- preserved feature-flag control.

### 15) Category classification improvement in backend
This session also corrected a high-value backend issue unrelated to guides UI but important for site quality.

#### Problem
Long rewritten articles were being miscategorised because category override logic in `backend/app/news_feed_service.py` would override based on any single keyword match.

Real bad example observed:
- Guardian politics podcast article was categorised as `Tax`.

#### Fix applied
`get_category_override(...)` was changed from:
- 1 keyword hit => override

to:
- require 2 keyword hits before overriding.

Result:
- reduced random bleed from long-form rewritten content into Tax/Money/Property,
- improved future import classification quality.

### 16) ArticlePageV2 guide-funnel debugging — what worked and what failed
This was the most complex debugging area in the session.

#### Initial state
`ArticlePageV2.jsx` already contained guide funnel components:
- `GuidesInlinePromo`
- `GuidePromoBlock`
- `pickGuidesForPillar()`

But they were non-functional or hidden because of several blockers.

#### Problems found
1. links were dead:
- `href={"#"}`
- `const href = null`

2. feature flag hard-blocks still existed in active code:
- `if (!FEATURES.NON_AMAZON_MONETISATION_ENABLED) return [];`
- `if (!FEATURES.NON_AMAZON_MONETISATION_ENABLED) return null;`

3. guide priority logic was incomplete or corrupt after multiple edits.

4. strict category matching and missing published guides made the funnel look empty or irrelevant.

#### Fixes that worked
- corrected guide link targets to `/guides/${slug}`
- repaired duplicated / broken code blocks in `ArticlePageV2.jsx`
- updated business / finance branches in `pickGuidesForPillar()`
- removed fallback corruption and duplicate returns
- added published finance guides to backend so article pages had actual data to select from

#### Fixes / attempts that failed or caused regressions
This section is important memory and should not be forgotten.

##### A) Bad insertion of strict ordering sort
A sort block was inserted before `const out = []`, causing runtime breakage / blank page.
This was removed.

##### B) Corrupted duplicate branch logic
Multiple command attempts caused duplicate conditions such as:
- duplicate `else if (pillar.includes("business"))`
- duplicate `return out.slice(0,3)`
These had to be manually cleaned from the active file.

##### C) Broken article text rendering
A sed replacement accidentally changed newline rendering to:
- `html.replace(/n/g, "<br/>")`

This replaced every letter `n` in article text and visually destroyed content.

This regression was fixed by restoring:
- `html.replace(/\n/g, "<br/>")`

##### D) Broken title display logic
The article H1 was found to concatenate summary text to the title, making titles too long and visually broken.
This was simplified back to:
- plain cleaned title only.

##### E) Attempt to bypass article-body feature gate
A command temporarily removed the early return in `autoLinkContent()` and damaged rendering. This was reversed. Conclusion:
- do not tamper with article-body rendering when trying to expose guide promos.
- treat guide-funnel exposure separately from body auto-linking.

### 17) Final article-page guide funnel state at end of this session
By the end of the session:
- guides API fetching on article page works,
- guide components render,
- guide links can route to `/guides/...`,
- published finance guides exist,
- but the article-page funnel still needs final controlled refinement before it should be considered production-complete.

Observed end state:
- some screenshots showed guide containers rendering with missing or mixed relevance,
- relevance improved substantially after published finance guides were added,
- but the user did not yet confirm a fully polished final article-page guide result worth shipping.

Therefore the correct conclusion is:
- **guide / authority-page system itself is working**,
- **homepage guide/strip infrastructure is working locally**,
- **article-page injection logic has been heavily improved but should be treated as still in refinement state**,
- **non-Amazon monetisation should remain OFF in production until this final polish is completed and affiliate approvals are in place.**

### 18) Published authority pages state at end of session
Published authority pages now include at least:
- `best-credit-cards-uk`
- `best-savings-accounts-uk`
- `best-mortgage-rates-uk`
- `cost-of-buying-home-cheshire-2026`
- `best-business-credit-cards-uk`
- `best-accounting-software-uk`
- `best-business-bank-accounts-uk`
- `best-ai-tools-uk`
- `best-ai-writing-tools-uk`
- `best-ai-productivity-tools-uk`

Draft but existing:
- `best-broadband-deals-uk`
- `cheap-energy-tariffs-uk`
- `council-tax-bands-cheshire` may still require final live/published decision depending on current admin state,
- other seeded finance pages can be promoted later.

### 19) Current production-safe recommendation after this session
#### Keep production in conservative state
Recommended safe state after this session:
- keep `NON_AMAZON_MONETISATION_ENABLED: false`
- keep Amazon-only live monetisation as current production path
- treat guide infrastructure as built but not yet fully activated site-wide.

#### Why
Because:
- guide pages are now real and usable,
- homepage monetisation strip is implemented and testable,
- article-page guide funnel still needs final strict relevance polish,
- affiliate approval sequence still matters strategically.

### 20) What worked well in this session
- restoring hidden systems from backups instead of rebuilding from scratch,
- using admin authority-page upsert endpoint rather than manual data edits,
- using feature flags to keep production safe while testing locally,
- finding the actual bottlenecks instead of assuming missing components,
- converting a stub guide into a legitimate local money-page template.

### 21) What failed / should be avoided next time
- direct complex multi-line `python3 -c` replacements with tricky escaping,
- sed/perl replacements without immediately re-checking exact affected lines,
- editing article-body auto-link rendering when the real issue is guide-block visibility or selection logic,
- introducing nested JSON structures into `AuthoritySection` before confirming schema support,
- assuming feature-flag behaviour was removed just because one guard was deleted; the file needed repeated grep verification.

### 22) Memory / project truths to carry forward from this chat
These points should be treated as active project memory for future continuation:

1. The non-Amazon monetisation system already exists architecturally; the work is now mostly activation / relevance / content quality, not greenfield build.
2. `AuthoritySection` is a flat schema. Repeated `tool` sections are the safe way to build monetisation blocks.
3. `AuthorityPage.jsx` needed explicit rendering of `content` sections; this has now been implemented.
4. `HeroMonetisationStrip.jsx` had a real corrupted import bug that has now been fixed and committed.
5. Guide route `/guides/:slug` was missing from active `App.js` and has now been restored and committed.
6. Published finance guides now exist and can be used as real authority assets.
7. The article-page guide funnel is the remaining fine-tuning area, not the overall guide system.
8. The master production stance remains: Amazon live, non-Amazon hidden until approvals / final polish.

### 23) Remaining work after this session
#### Highest-value remaining tasks
1. Finalise article-page guide relevance so Business/Finance articles surface the best matching money guides consistently and elegantly.
2. Decide whether homepage should get a published-guides block in addition to the feature-flagged monetisation strip.
3. Improve guide content depth / quality for:
   - `best-savings-accounts-uk`
   - `best-mortgage-rates-uk`
   - `best-broadband-deals-uk`
   - `cheap-energy-tariffs-uk`
4. Replace placeholder `#` tool links with real affiliate destinations once networks are approved / available.
5. Run affiliate-readiness review on guide pages, disclosures, and navigation once the article funnel is finished.

#### Lower-level technical cleanup still worth doing later
- audit `ArticlePageV2.jsx` for any leftover temporary guide-debug edits and normalise the file,
- verify canonical / OG metadata on `AuthorityPage.jsx` if needed,
- optionally improve homepage guide surfacing using published authority pages only.

### 24) Recommended resume prompt for next chat
Use this prompt in the next chat:

`Continue the Cheshire Today project from the March 2026 master state. Read PROJECT_CURRENT_STATE_MASTER_MARCH_2026.md first. Respect workflow: one command at a time, no manual edits, always check current state before changing anything. Assume the guides system is restored, AuthorityPage route is live, HeroMonetisationStrip is repaired and mounted behind the feature flag, published finance guides now exist (credit cards, savings, mortgage), backend category override now requires 2 keyword matches, and the remaining priority is to finish article-page guide relevance / article monetisation funnel polish while keeping NON_AMAZON_MONETISATION_ENABLED false in production-safe state.`

---

## 25) Update — 3 April 2026 session (homepage speed, freshness, and header search)

### A. Header search result click-through bug fixed
Problem observed:
- Header search results were not navigating correctly to article pages in all cases.
- `searchArticles()` in the frontend was also assuming the articles API returned a raw array, which broke search results when the endpoint returned an object with an `articles` array.

Work completed:
- Updated `frontend/src/components/NewsHeader.jsx` to import `buildArticleUrl` and use it when a search result is clicked and no external `onArticleClick` handler is provided.
- Updated `frontend/src/services/api.js` search handling so it safely reads either:
  - a raw array response, or
  - an object response shaped like `{ articles: [...] }`.

Commit saved during session:
- `57b66cd` — `Fix header search results and article navigation`

Result:
- Header search results now navigate correctly to canonical article URLs.
- Search result parsing is more robust against current backend response format.

### B. Business & Finance homepage freshness issue investigated and improved
Problem observed:
- Homepage `Latest` feed was current, but `Business & Finance` was surfacing older items (for example 30 March / 1 April content) even though newer relevant stories had been imported.

Root cause identified:
- Homepage section selection was not giving enough weight to `created_at` freshness in the business/finance-related side and mixed feeds.
- Too many newest stories were effectively being "reserved" out of sidebar-style sections because `latestPreviewKeys` was holding 12 newest items back.
- `AI & Business / Business & Finance` feed construction was also iterating over `poolRanked` rather than the freshness-prioritised `sectionFreshPool`, which reduced recency in that section.

Frontend changes kept:
- Added `created_at` into homepage card objects in `HomePageV1.jsx`.
- Reduced `latestPreviewKeys` reservation from `12` to `4` so fresher stories can appear in business/finance side sections.
- Changed `sectionFreshPool` sorting to prefer `created_at` first, then `publishedDate`, then rank.
- Changed `financeArticles` sorting to prefer `created_at` first.
- Changed `businessFeed` sorting to prefer `created_at` first.
- Changed `aiBizFeedCards` source loop from `poolRanked` to `sectionFreshPool`.

Result:
- Business / Finance-related homepage sections now draw from a fresher ordered pool.
- The homepage logic remains dedupe-aware, but with much better recency behavior.

### C. Critical homepage performance issue diagnosed and fixed
Problem observed:
- Homepage load felt extremely slow locally and live, including cases of approximately 30–35 seconds perceived delay.
- Initial suspicion was frontend rendering cost, because `HomePageV1.jsx` contains heavy pool/allocation logic.

Investigation performed:
- Measured live `authority-pages` endpoint and confirmed it was not the major bottleneck.
- Measured live homepage articles endpoint directly:
  - `https://cheshiretoday.co.uk/api/articles?limit=80`
  - observed live response time: **51.307628 seconds**
  - payload size: **338718 bytes**
- Measured local backend endpoint before backend fix:
  - `http://127.0.0.1:8000/api/articles?limit=80`
  - observed local response time: **48.049868 seconds**

Conclusion:
- This proved the real bottleneck was backend-side, not Render warm-up and not primarily frontend rendering.
- The issue reproduced locally, so it was not a cold-start / cron warm-up issue.

True root cause:
- The homepage `/api/articles?limit=80` "all" / interleaved branch in `backend/server.py` was fetching oversized candidate pools **with full `content` bodies included**.
- It was then running Python-side classification / filtering / sensitivity / editorial checks across those large records before returning the homepage feed.
- For a homepage request of `limit=80`, the code was effectively pulling very large candidate pools (previously up to local `limit*20`, UK `limit*8`, fallback `limit*20`) and scanning them server-side.

Backend fixes implemented in `backend/server.py`:
1. Removed `content` from the homepage interleaved branch projections for:
   - `force_articles`
   - `local_articles`
   - `uk_articles`
   - `fallback_items`
2. Reduced candidate pool sizes in the same branch:
   - local pool from `limit*20` to `limit*6`
   - UK pool from `limit*8` to `limit*4`
   - fallback pool from `limit*20` to `limit*6`

Why this is safe:
- This change applies to the homepage list endpoint path only.
- It does **not** remove full article content from stored articles.
- It does **not** break article pages, because single-article endpoints still return full content.

Verification completed:
- After backend fix, local homepage endpoint timing dropped to:
  - **3.620845 seconds**, then **3.484837 seconds** on repeat test.
- After deploy, live homepage endpoint timing dropped to:
  - **1.313563 seconds** for `https://cheshiretoday.co.uk/api/articles?limit=80`
- Article detail endpoint was checked locally and still returned full content:
  - tested article content length: **6032 characters**

Operational conclusion:
- Homepage performance issue was successfully fixed.
- Root cause was backend homepage feed over-fetching and scanning full article bodies.
- Render warm-up / cron timing was not the primary cause.

### D. Temporary frontend performance mitigation tested and then reverted
What happened:
- A temporary frontend mitigation was tested where homepage state only kept a short content excerpt.
- This helped prove the direction of investigation but was not the true fix.

Final decision:
- Reverted that frontend slicing change.
- Kept the proper backend fix instead.

Reason:
- The backend fix solved the actual bottleneck.
- No need to keep extra frontend-only workaround behavior once the root cause was fixed.

### E. Commits and deployment state
Commits created / referenced in this session:
- `57b66cd` — `Fix header search results and article navigation`
- `0e1d639` — `Speed up homepage articles endpoint and refresh business feed ordering`

Deployment status:
- Changes were committed, pushed, and manually deployed to Render.
- Backend manual deploy was triggered first, then frontend manual deploy.
- Live verification confirmed the performance improvement.

### F. Important project truths added from this session
1. If homepage becomes extremely slow again, test `/api/articles?limit=80` directly before blaming frontend rendering.
2. The homepage interleaved `/api/articles` branch must stay light-weight; do not reintroduce full `content` into large homepage candidate pool projections unless there is a very strong reason.
3. Large candidate pool multipliers on homepage feed construction can destroy performance quickly, especially when combined with Python-side text classification.
4. Business / Finance homepage freshness depends heavily on `created_at`, not only `publishedDate`.
5. Reserving too many newest stories away from sidebar/business sections makes those sections look stale even when new imports exist.
6. Live Render warm-up concerns should not be treated as the default explanation when the same delay reproduces locally.

### G. Current production-safe state after 3 April 2026 session
Current confirmed state:
- Homepage live articles endpoint is fast again.
- Homepage load is much improved.
- Article pages still return full article content.
- Header search results navigate correctly.
- Business / Finance related homepage sections have fresher ordering behavior.
- Latest feed remains correct.

### H. Recommended resume prompt for next chat (updated)
Use this prompt in the next chat:

`Continue the Cheshire Today project from the March 2026 master state and the 3 April 2026 update. Read PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260403.md first. Respect workflow: one command at a time, no manual edits, always check current state before changing anything. Assume header search navigation is fixed (57b66cd), homepage /api/articles performance issue was fixed in backend by removing full content from homepage candidate pools and reducing pool sizes (0e1d639), live /api/articles?limit=80 improved from 51.3s to 1.31s, article detail endpoints still return full content, and homepage Business/Finance freshness now uses created_at-aware ordering. Prioritise stability, homepage freshness, and production-safe verification before any new structural changes.`

---

## 6. Appendix: fuller session log for 3 April 2026 chat

This appendix was added because the earlier update captured the main outcomes, but not all of the intermediate diagnostics, failed attempts, and reasoning steps from the session. This section is intended to preserve the practical troubleshooting trail more completely.

### A. What was actually investigated in sequence

Order of work during this chat:
1. Fixed homepage/header article search result navigation.
2. Investigated Business & Finance homepage section showing stale items despite new imports.
3. Considered homepage redesign / larger effective pool behavior so more fresh imports could surface across Latest and sidebar-style sections.
4. Applied several homepage freshness logic changes in `HomePageV1.jsx`.
5. Observed no meaningful visible improvement at first.
6. Discovered a severe homepage loading delay both locally and on live.
7. Tested whether the issue was frontend-side or backend-side.
8. Proved backend `/api/articles?limit=80` was the true bottleneck.
9. Tested and then rejected a temporary frontend-only mitigation as the final solution.
10. Implemented the proper backend fix in `backend/server.py`.
11. Re-verified article detail endpoints still return full content.
12. Committed, pushed, and manually deployed backend then frontend.
13. Verified live timing improvement.

### B. Header search fix details preserved
Exact fix path:
- `frontend/src/services/api.js`
- `frontend/src/components/NewsHeader.jsx`

Technical issue:
- Header search logic expected `response.data` to be a plain array.
- Current backend response shape was object-style (`{articles: [...], total: ..., ...}`).
- Search dropdown could therefore fail or behave inconsistently.
- Search result clicks also needed to route through canonical slug article URLs.

Implemented details:
- In `api.js`, changed search parsing from direct `response.data` usage to:
  - array if response is already an array
  - otherwise `data.articles || []`
- In `NewsHeader.jsx`, added `buildArticleUrl` import and used it so search result clicks navigate correctly when `onArticleClick` is not provided.

Commit created:
- `57b66cd` — `Fix header search results and article navigation`

### C. Business & Finance freshness troubleshooting trail
Observed issue:
- User repeatedly confirmed that homepage `Latest` looked current, but `Business & Finance` still showed stale dates such as 30 March / 1 April despite newer imported stories existing.

Initial homepage logic findings:
- `latestPreviewKeys` reserved too many newest items away from sidebar/business-type sections.
- `sectionFreshPool` originally preferred `publishedDate` before `created_at`.
- `financeArticles` and `businessFeed` sorting also leaned on `publishedDate`.
- `aiBizFeedCards` iterated over `poolRanked` rather than the freshness-prioritised `sectionFreshPool`.

Changes applied and kept:
- Added `created_at` to `toCard(...)`.
- Reduced `latestPreviewKeys` reservation from 12 to 4.
- Changed `sectionFreshPool` sort order to use `created_at || publishedDate`.
- Changed `financeArticles` sort order to use `created_at` first.
- Changed `businessFeed` sort order to use `created_at` first.
- Changed `aiBizFeedCards` source loop from `poolRanked` to `sectionFreshPool`.

Important practical note:
- Several of these changes were applied before the homepage performance root cause was fully diagnosed.
- Early tests made it look as though freshness changes were not working, but part of that confusion was because the homepage endpoint itself was so slow and heavy.

### D. Temporary paths and failed attempts during freshness work
These happened during the chat and should be remembered:

1. A quick attempt was made to change `sectionFreshPool` ordering with a `perl` substitution.
   - It failed because the exact pattern did not match.
   - A safer `python3 -c` file-edit replacement was then used successfully.

2. Early tests of freshness changes sometimes showed “no visible change”.
   - This created suspicion that we had tried similar changes before and reverted.
   - Final conclusion: the logic changes were directionally correct, but the backend homepage endpoint was such a large bottleneck that it obscured diagnosis.

3. The user reasonably questioned whether allowing fresher Business & Finance items might increase duplication with Latest.
   - Decision: keep dedupe-aware structure, but reduce the “reservation” effect and use a fresher source pool rather than simply forcing duplicates.

### E. Homepage performance diagnostic trail in more complete detail
Symptoms:
- Homepage felt extremely slow locally and on live.
- User perceived approximately 30–35 second loading delay.
- Delay persisted even after some homepage ordering changes.

What was tested:
- Checked frontend `useEffect` fetch path in `HomePageV1.jsx`.
- Measured `authority-pages` endpoint time:
  - approximately `0.620024s`
  - too small to explain homepage delay.
- Measured live articles endpoint:
  - `https://cheshiretoday.co.uk/api/articles?limit=80`
  - `time=51.307628`
  - `size=338718`
- Measured local backend endpoint:
  - `http://127.0.0.1:8000/api/articles?limit=80`
  - approximately `48.049868s`

Why that mattered:
- Because the delay reproduced locally, it was not primarily a Render cold start, cron warm-up, or live-only platform issue.
- This ruled out the user’s sensible suspicion about earlier Render warm-up / cron behavior being the primary root cause.
- It also meant frontend `HomePageV1.jsx` was not the principal bottleneck.

### F. Temporary frontend mitigation that was tested
Temporary mitigation tested:
- Homepage `setArticles(...)` was changed to keep only the first 400 characters of `content` in homepage state.

Why it was tested:
- To see if frontend-side large content scanning was the dominant bottleneck.

Result:
- It did not produce the decisive fix.
- It was useful as a diagnostic step, but not the final solution.

Final decision:
- Reverted this change.
- Kept the backend fix instead.

### G. Root cause in backend `/api/articles` all-feed branch
Confirmed root cause:
- The homepage interleaved `/api/articles?limit=80` path in `backend/server.py` fetched oversized candidate pools and included full `content` bodies in those candidate records.
- It then ran Python-side:
  - noise filtering
  - editorial noise filtering
  - sensitive/crime/incident classification
  - interleaving
  - fallback top-up filtering
  - soft authority boost scoring
- This meant huge unnecessary text handling before the endpoint returned the 80 homepage records.

Specific candidate pool sizes before fix:
- local pool: `limit*20`
- UK pool: `limit*8`
- fallback pool: `limit*20`

At homepage `limit=80`, this was extremely expensive.

### H. Backend fix details preserved
Final backend fix in `backend/server.py`:
1. Removed `content` from the projections used by the homepage all/interleaved branch for:
   - `force_articles`
   - `local_articles`
   - `uk_articles`
   - `fallback_items`
2. Reduced candidate pool multipliers:
   - local: `limit*20` → `limit*6`
   - UK: `limit*8` → `limit*4`
   - fallback: `limit*20` → `limit*6`

Observed shell trouble while patching:
- One attempted `python3 -c` replacement command failed with shell quoting / escape issues and raised `SyntaxError`.
- Simpler `perl` replacements plus a targeted `python3 -c` line replacement were then used to complete the patch safely.

### I. Local uvicorn warnings observed during testing
Observed during local backend testing:
- repeated warnings like:
  - `Exception ignored in: <gzip ...>`
  - `ValueError: I/O operation on closed file.`

Interpretation used in this session:
- These warnings were noted but were **not** treated as the main cause of the 48–51 second homepage endpoint problem.
- The timing improvement after removing homepage-branch `content` confirmed the gzip warning was not the primary bottleneck.

### J. Verification after backend fix
Local verification after backend fix:
- `/api/articles?limit=80`
  - dropped to approximately `3.620845s`
  - then approximately `3.484837s`

Frontend/local behavior:
- Local homepage felt much faster after backend fix.

Article detail verification:
- Checked a direct article endpoint locally:
  - `curl http://127.0.0.1:8000/api/articles/69cbbb3f833852083fefdd21`
  - verified `content` length = `6032`
- This proved article detail endpoints still return full content.

Live verification after deploy:
- `https://cheshiretoday.co.uk/api/articles?limit=80`
  - dropped to approximately `1.313563s`

### K. Deploy sequence preserved
Deploy sequence used:
1. Commit changes.
2. Push branch `full-scrape-prod`.
3. Trigger backend manual deploy first in Render.
4. Trigger frontend manual deploy second in Render.
5. Re-test live endpoint timing and homepage behavior.

Commit created for the combined performance/freshness work:
- `0e1d639` — `Speed up homepage articles endpoint and refresh business feed ordering`

### L. Final kept vs reverted changes from this session
Kept in frontend:
- `created_at` added to card objects
- `latestPreviewKeys` reduced from 12 to 4
- `sectionFreshPool` uses `created_at` first
- `financeArticles` sorts by `created_at` first
- `businessFeed` sorts by `created_at` first
- `aiBizFeedCards` iterates over `sectionFreshPool`

Reverted in frontend:
- homepage-only `content.slice(0, 400)` state mitigation

Kept in backend:
- removed `content` from homepage interleaved branch projections
- reduced local/UK/fallback candidate pool sizes

### M. Important lessons now explicitly preserved
1. If homepage is slow, measure `/api/articles?limit=80` directly before changing frontend rendering.
2. If the same slowness reproduces locally, do not default to blaming Render warm-up, cron, or platform issues.
3. Homepage list/feed endpoints should not pull full article bodies unless absolutely necessary.
4. `created_at` is operationally more useful than `publishedDate` for freshness of imported homepage business/finance content.
5. Reservation logic like `latestPreviewKeys` can accidentally make business/finance sections look stale even while imports are current.
6. Temporary frontend mitigations can help diagnosis, but backend feed over-fetching was the actual failure mode here.

### N. Scope note
This appendix is intended to preserve the project-relevant technical work from the chat. It does not aim to document unrelated non-project side requests from the same conversation thread.


---

## Appendix — 2026-04-03 homepage performance follow-up (image delivery, cache headers, attempted feed image normalization, and revert)

This appendix preserves the exact verified sequence from the 2026-04-03 follow-up session that happened **after** the main homepage backend speed fix documented above.

Important context:
- This work happened only after the previously verified backend performance fix was already live.
- Existing project constraints were kept in force:
  - no redesign
  - do not retry sticky sidebar experiments
  - work from current state first
  - one command at a time
  - no manual file edits
  - project-root commands only
- The goal in this follow-up was to investigate the **next safe performance improvements** after the backend `/api/articles` speed fix.

### O. Starting verified state for this follow-up
At the start of this session, the already-verified live state was:
- homepage `/api/articles?limit=80` had already been fixed from roughly `51.3s` live to roughly `1.31s` live
- root cause had already been identified as the homepage all/interleaved backend path fetching oversized candidate pools plus full content bodies
- the fix was already documented in the state file and associated with:
  - `0e1d639` — `Speed up homepage articles endpoint and refresh business feed ordering`
- article detail pages were still expected to return full content normally
- the user explicitly asked for the next safe focus to be:
  1. homepage image delivery optimisation
  2. cache lifetimes for static assets
  3. LCP image discovery / priority
  4. lazy-loading / decoding for non-critical homepage media

### P. Source-of-truth and guardrails used during this follow-up
Before changing anything, the following were treated as current references:
- `PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260403_v2.md`
- `PROJECT_HANDOVER_MASTER_MARCH_2026.md`
- `Cheshire_Economic_AI_Project_Master_Feb2026.pdf`

Practical guardrail repeated and respected:
- image/cache/LCP work appeared not to have been fully attempted before
- sticky-sidebar/layout experiments were explicitly treated as failed/closed and not retried

### Q. First inspection of homepage image/render path
The homepage image/render path was checked before any code change.

Findings:
- homepage uses:
  - `HeroStoryCard`
  - `TopStoriesGrid`
  - multiple `CompactArticleCard` blocks
- `HomePageV1.jsx` was **not** passing `priority` to homepage `CompactArticleCard` usage
- therefore the likely primary desktop LCP target was the homepage hero image in `HeroStoryCard`

Component findings:
1. `HeroStoryCard.jsx`
   - used a real `<img>`
   - already had `loading="eager"`
   - did **not** have:
     - `fetchPriority="high"`
     - explicit width/height attributes
     - decoding hint
2. `TopStoriesGrid.jsx`
   - already used `loading="lazy"`
   - looked conservative enough to leave alone initially
3. `CompactArticleCard.jsx`
   - already had richer image handling than `HeroStoryCard`
   - included:
     - `loading`
     - `fetchpriority`
     - explicit `width` / `height`
     - `decoding="async"`
     - lightweight source-specific URL optimization for Unsplash only

Conclusion at this point:
- the cleanest first local-only performance change was to tighten the homepage hero image path rather than broadly changing all homepage card behavior.

### R. Hero LCP improvement applied and kept
A targeted local change was made to:
- `frontend/src/components/homepage/HeroStoryCard.jsx`

Change made:
- kept `loading="eager"`
- added:
  - `fetchPriority="high"`
  - `decoding="sync"`
  - `width="1200"`
  - `height="675"`

Why it was done:
- the homepage hero was the most plausible desktop LCP candidate
- it was less optimized than existing compact cards
- this was a narrow change that did not alter layout

Verification sequence:
- backup created first
- diff checked to confirm only the hero image block changed
- `npm --prefix frontend run build` completed successfully
- local static serve via `npx serve -s frontend/build -l 3000` confirmed the frontend still served normally

Final status of this hero change:
- **kept**
- eventually deployed live

### S. Homepage feed image delivery attempt that was tested and then reverted
After the hero check, real homepage API image URLs were inspected.

Live `/api/articles` inspection showed many homepage images were still returning small source variants, for example:
- Guardian images with `width=140`
- BBC images with `/240/`
- Reach images with `/ALTERNATES/s615/`

Important discovery:
- source-specific image upscaling logic already existed in `backend/server.py`, but only inside the **social/OG** path (`normalize_social_image`), not in the general homepage `/api/articles` response path.

A local attempt was then made to reuse similar image normalization logic inside the live `/api/articles` serialization loop.

Local change temporarily added to `backend/server.py`:
- introduced a helper `normalize_feed_image(...)` inside `get_articles(...)`
- rewrote images on API output for:
  - Reach `s615` / `s615b` / `s810` → `s1200`
  - Guardian `width=140` / `width=240` → `width=1200`
  - BBC `/240/` / `/320/` / `/480/` → `/1024/`
- applied it to `article['image']` before appending to `unique_articles`

Local verification result:
- worked technically
- local `/api/articles` output showed larger image variants as expected

But visual outcome on homepage after deploy attempt:
- user reported that many articles now appeared with what looked like generic/newspaper-style imagery instead of the preferred visual appearance seen before
- screenshots made it clear that even though the URLs were valid and varied, the visual result was worse on the homepage

Important conclusion:
- this was **not** a cache-header problem
- this was **not** caused by the hero LCP change
- it was the homepage feed image normalization itself creating a worse visual result by surfacing larger source-selected images that were often generic or newspaper-style

Decision:
- revert only the homepage feed image normalization
- keep the hero LCP work
- keep the static asset cache-header work

Final status of this attempted image normalization:
- **reverted**
- explicitly not part of the final live state

### T. Static asset cache-header investigation and fix
After the image-path work, static asset cache behavior was investigated.

Initial live checks:
- hashed JS/CSS asset responses appeared to have no visible long-lived `Cache-Control` in initial `curl -I` checks
- `cf-cache-status` showed `DYNAMIC`
- however this first result turned out to be partially misleading because the custom `HEAD` route was not mirroring the actual file response

Important serving-path discovery:
- frontend assets were not being served by an explicit `StaticFiles` mount
- instead the backend used a generic SPA `FileResponse` path in `backend/server.py`
- this path:
  - served real files under `backend/frontend_build`
  - served `index.html` for `/`
  - served `index.html` as SPA fallback for unknown paths
- there was no dedicated cache policy on these `FileResponse` returns

Additional critical observation:
- the `HEAD /{full_path:path}` handler returned a bare `Response(status_code=200)` for non-API paths
- that meant `curl -I` against `/static/...` was not showing the true asset headers

Real GET-header check showed:
- JS asset response did include `ETag` and `Last-Modified`
- but still lacked the desired explicit long-lived `Cache-Control`

Fix applied locally in `backend/server.py`:
1. introduced `_spa_file_response(path: Path)`
2. added per-path cache policy logic:
   - `index.html`:
     - `Cache-Control: public, max-age=0, must-revalidate`
   - hashed `/static/*` assets:
     - `Cache-Control: public, max-age=31536000, immutable`
   - unhashed static files:
     - `Cache-Control: public, max-age=3600`
3. updated SPA GET file-serving path to use `_spa_file_response(candidate)`
4. updated root/index serving path to use `_spa_file_response(_INDEX_HTML)`
5. changed `HEAD` handlers so they now follow the same real file/index response path instead of returning a blank `200`

Local verification after backend restart:
- local JS asset returned:
  - `cache-control: public, max-age=31536000, immutable`
- local CSS asset returned:
  - `cache-control: public, max-age=31536000, immutable`
- local `/` returned:
  - `cache-control: public, max-age=0, must-revalidate`

Final status of this cache-header work:
- **kept**
- eventually deployed live

### U. Backup files created during this follow-up
The following backup files were created during this session and should be preserved for rollback/reference history:

1. `frontend/src/components/homepage/HeroStoryCard.jsx.bak_lcp_20260403_1`
   - backup created before the hero LCP change

2. `backend/server.py.bak_homepage_image_normalize_20260403_1`
   - backup created before the attempted homepage feed image normalization

3. `backend/server.py.bak_static_cache_headers_20260403_1`
   - backup created before the SPA/static cache-header patch

4. `backend/server.py.bak_revert_feed_image_normalize_20260403_1`
   - backup created before removing the homepage feed image normalization after the visual regression was reported

Important note:
- these backups reflect the exact command-by-command workflow used in this session
- they are not the final production state
- they should be kept as local rollback anchors for this specific April 3 follow-up

### V. Commit and deploy sequence for this follow-up
This sequence should be preserved exactly because one intermediate commit was intentionally corrected by a later commit.

1. Local changes verified:
   - hero LCP improvement
   - feed image normalization attempt
   - static asset cache-header improvement

2. Commit created:
- `75b6c5c` — `Improve homepage image delivery and static asset cache headers`

Important note on this commit:
- it included **three** things:
  - hero LCP improvement
  - static asset cache-header improvement
  - homepage feed image normalization attempt
- the third part later proved visually undesirable and was intentionally reverted

3. After user review of homepage visuals, only the feed image normalization was removed.

4. Follow-up corrective commit created:
- `27c5a57` — `Revert homepage feed image normalization and keep cache header improvements`

Meaning of final branch state after `27c5a57`:
- **kept:** hero LCP improvement
- **kept:** static asset cache-header improvement
- **reverted:** homepage feed image normalization

### W. Deploy behavior nuance that must be remembered
A deployment nuance happened during this session:
- user initially canceled a deploy by mistake
- later manually redeployed the latest corrected state in Render
- screenshot confirmation showed commit `27c5a57` eventually reached live status

Operational lesson:
- when one commit introduces a mixed set of changes and one part is visually wrong, do not rewrite history midstream if deploy/autodeploy is already in motion
- safer pattern used here was:
  1. create corrective commit
  2. make sure latest branch tip is the corrected state
  3. redeploy latest corrected commit

### X. Final live verification after corrective deploy
Production was then re-checked.

#### 1. Live `/api/articles` verification
Live homepage API output confirmed the feed image normalization was no longer active.

Observed again on live after corrective deploy:
- Guardian images back to `width=140`
- BBC images back to `/240/`
- Reach images back to `/s615/`

This proved:
- the bad homepage feed-image normalization was no longer live
- the corrective commit had actually reached production

#### 2. Live static asset cache-header verification
Care had to be taken to check the **current** hashed asset names after deploy.

A mistaken test initially used an old or placeholder JS path and therefore got SPA fallback HTML.
That was corrected by first extracting the current live asset names from homepage HTML.

Verified live asset names at the time of check:
- `/static/js/main.73e70fb0.js`
- `/static/css/main.83a32087.css`
- `/static/array.js`

Verified live responses for real hashed assets then showed:
- JS:
  - `cache-control: public, max-age=31536000, immutable`
  - `content-type: text/javascript; charset=utf-8`
- CSS:
  - `cache-control: public, max-age=31536000, immutable`
  - `content-type: text/css; charset=utf-8`

This proved:
- the static asset cache-header improvement was live
- the SPA file-serving patch was functioning as intended for hashed assets

#### 3. Live state summary after corrective deploy
Final verified live outcome from this follow-up session:
- **kept live:** hero LCP improvement in `HeroStoryCard.jsx`
- **kept live:** static asset cache-header improvement in SPA/static `FileResponse` path
- **not live:** homepage feed image normalization attempt

### Y. Important lessons preserved from this follow-up
1. A technically valid image upscaling rule is not automatically a visual win for homepage presentation.
2. Source-specific image rewrites that are acceptable for social/OG may still degrade homepage editorial appearance.
3. For the homepage, visual quality and editorial fit matter more than simply serving a larger source image variant.
4. The SPA `HEAD` shortcut can make cache debugging misleading if it does not mirror the real file-serving path.
5. When checking live cache headers after deploy, always first fetch the **current** hashed asset names from live HTML.
6. The correct final approach from this session was selective:
   - keep LCP help for the hero image
   - keep long-lived cache headers for hashed assets
   - do **not** rewrite homepage feed image URLs globally

### Z. Final state to continue from in the next chat
Use the following as the verified state after this April 3 follow-up:

1. The major homepage backend speed fix from `0e1d639` remains live and valid.
2. The hero image LCP improvement remains live.
3. The static asset cache-header improvement remains live.
4. The homepage feed image normalization attempt was tested and explicitly reverted.
5. Any further homepage performance work should now focus on **safe next steps only**, such as:
   - further LCP discovery/priority refinement if clearly measurable
   - render-blocking reduction if identifiable
   - careful monitoring of asset caching behavior
6. Do **not** reintroduce the reverted homepage feed image normalization without a much more selective, visually tested strategy.



### AA. April 5, 2026 follow-up: affiliate readiness, CJ onboarding, live cleanup, and obituary-import fix

This follow-up moved from generic readiness discussion into concrete verification and production cleanup work.

#### 1. Google Analytics / live analytics verification
Google Analytics was verified as live on production.

Observed from the live site and GA property checks:
- live site was loading GA4 directly via `gtag/js`
- live measurement ID in use: `G-Q1NZLJC50D`
- live site was also loading Plausible and PostHog
- GA4 web stream for `https://cheshiretoday.co.uk` showed traffic in the last 48 hours
- Realtime view showed active users and live page activity

Conclusion preserved:
- analytics is not the blocker for affiliate-readiness
- GA4 is functioning well enough for commercial / network-readiness purposes
- DebugView being empty without debug mode was not treated as a setup failure

#### 2. Affiliate-readiness re-evaluation
A fresh readiness pass showed that the original assumption "missing commercial pages" was no longer correct.

Verified during this session:
- legal/compliance URLs were live and returning `200`:
  - `/privacy`
  - `/terms`
  - `/cookies`
  - `/affiliate-disclosure`
  - `/contact`
  - `/advertise`
- guide / commercial URLs were also live and returning `200`, including:
  - `/guides/best-accounting-software-uk`
  - `/guides/best-business-bank-accounts-uk`
  - `/guides/best-mortgage-rates-uk`
  - `/guides/best-credit-cards-uk`
  - `/guides/best-savings-accounts-uk`

This corrected an earlier mistaken direction.

The real remaining affiliate-readiness blockers were identified as:
- production polish
- active placeholder links in footer/social areas
- feature-flag / exposure polish for non-Amazon monetisation
- guide quality / credibility review rather than guide existence

#### 3. Footer placeholder-link polish completed
The active footer file was inspected and still contained placeholder social links and a fallback `href="#"` branch.

Changes made locally in `frontend/src/components/NewsFooter.jsx`:
- removed placeholder social icon block using `href="#"`
- replaced unmapped footer fallback links with plain text instead of dead `#` links
- removed now-unused social icon imports

Verification performed:
- local frontend build completed successfully
- active footer file no longer contained `href="#"`
- changes were committed and pushed
- live homepage shell no longer returned `href="#"`
- key live legal/commercial pages still returned `200`

Conclusion preserved:
- affiliate-readiness polish improved
- no new social links were added anywhere on homepage during this patch
- this was a cleanup / credibility fix only

#### 4. CJ publisher account setup attempted from scratch
CJ setup was worked through interactively during this session.

Completed inside CJ:
- email verification
- user details (including correcting initially broken `undefined undefined` user name)
- network profile
- primary promotional property for `https://cheshiretoday.co.uk`
- promotional model aligned to content/editorial publisher use
- W-8BEN submission for individual payee flow
- payment / bank information saved
- company / account information reviewed and entered

Important outcome:
- the CJ account became usable enough to browse Partners screens
- however advertiser application remained blocked because CJ onboarding stayed stuck at `7 of 9 completed`
- the stuck state appeared inconsistent with completed tax/payment/company details
- screenshots also showed onboarding URLs with repeated `/undefined/` segments, suggesting CJ-side onboarding state issues rather than a missing local field

Decision preserved:
- stop trying to brute-force CJ onboarding locally
- treat this as a CJ-side activation/support issue
- a message was sent to `sales@cj.com` as a fallback because the support route was not working
- next CJ step is to wait for response rather than continue changing the account state blindly

#### 5. Live editorial audit resumed after affiliate/CJ work
After recent live changes, a fresh production audit showed that some off-strategy items were still appearing publicly.

Immediate live examples identified during this session:
- death notices / obituary-style content
- low-value crime leakage
- a few borderline public-interest local police/safety items

The audit deliberately avoided over-removal.
Business/public-interest items were separated from obvious low-fit content.

#### 6. Live manual cleanup completed during this session
A focused live archive pass was carried out via admin endpoints.

Archived during the broader off-strategy cleanup (science / celebrity / weak lifestyle / filler):
- `69cf4d4049075d441b2006b2` — “I’d introduce aliens to shito sauce...”
- `69cf4d5149075d441b2006b3` — Artemis far-side story
- `69ceb28deca970997176aecf` — Artemis toilet story
- `69d0f32c24de2d6384902b90` — “scientists aren’t funny” opinion-style science filler
- `69d09eb824de2d6384902b80` — Artemis halfway-to-moon story
- `69d1479224de2d6384902b9b` — Artemis Earth-image story
- `69d1f04424de2d6384902ba6` — Jeremy Hansen / Project Hail Mary story
- `69d1fc2424de2d6384902bb2` — space dust citizen-scientist story
- `69cfa1bcc4f6a4db0963008b` — Artemis “first words from space” story
- `69ceb29eeca970997176aed0` — Artemis leave-Earth-orbit story
- `69ce5ba3eca970997176aeba` — “Everything you need to know” Artemis explainer
- `69ce5e2ceca970997176aec4` — Apollo missions feature
- `69ce5e3aeca970997176aec5` — Jeremy Hansen profile feature
- `69d1473324de2d6384902b95` — hot chocolate tasting/rating piece
- `69d0f2cd24de2d6384902b8a` — house swaps / holiday lifestyle piece
- `69d1474624de2d6384902b96` — emergency foods stockpile lifestyle piece
- `69d1475624de2d6384902b97` — traditional farmhouses picture gallery
- `69cd60f3833852083fefdd3b` — Artemis live/follow piece
- `69cd6104833852083fefdd3c` — students / Nasa launch watch party
- `69ca6985ce11a2e917daae08` — Florida space-coast feature
- `69cfa1a3c4f6a4db0963008a` — beavers piece
- `69ce5b96eca970997176aeb9` — Danish warship discovery
- `69ceb2abeca970997176aed1` — Real Housewives item
- `69cd6126833852083fefdd3e` — Real Housewives comeback item
- `69ce5dedeca970997176aec0` — Colin the Caterpillar taste test piece
- `69ce5dfeeca970997176aec1` — quarter-zip “finance bro” lifestyle piece

Archived during the obituary / crime leak cleanup:
- `69d299143e111f15c2ab941b` — “11 death notices made in Cheshire this week”
- `69ce5bc6eca970997176aebc` — Mounjaro jabs “goes on the run” crime item
- `69cd6116833852083fefdd3d` — “multiple fractures” Chester city-centre attack item

Explicitly kept during review because they still fit public-interest / business logic better than filler:
- `JLR sees sales recover after cyber attack`
- `Iran war driving up funeral costs in the UK`
- `CCTV appeal after Macclesfield FC stadium targeted in arson attack` (kept as borderline local public-interest / police appeal rather than generic crime filler)

Decision preserved:
- stop the manual archive pass once obvious low-fit items were removed
- do not over-prune legitimate public-interest local items

#### 7. Root-cause investigation for obituary leakage
Production/API checks then narrowed the actual obituary leak path.

Key discovery:
- `/sync-rss-now` already had explicit obituary / hard-crime / crime title blocking
- therefore the death-notice leak was unlikely to have come through that path
- attention shifted to `import_hybrid_news(...)`

Inside `import_hybrid_news(...)`, the active UK RSS path had:
- image gate
- Manchester-source exclusion
- duplicate checks
- crime-like low cap
- no obituary/death-notice hard block

That difference explained why obituary-style titles could still leak through hybrid imports even though `/sync-rss-now` looked stricter.

#### 8. Hybrid importer obituary fix implemented
A narrow backend patch was added to `backend/server.py` inside `import_hybrid_news(...)`.

What was added:
- new helper: `is_obituary_like(article: dict)`
- regex block covering obituary / memorial notice-style titles, including:
  - death notices
  - funeral notices
  - funeral arrangements
  - in memoriam
  - death announcements
  - passed away peacefully
  - loving memory
  - beloved husband / wife / mum / mom / dad
  - family announcement
- hard block inserted immediately after Manchester-source exclusion and before crime-cap logic:
  - `if is_obituary_like(article): continue`

Validation completed:
- backup created before patching
- exact insertion points inspected line-by-line
- `python3 -m py_compile backend/server.py` passed
- diff reviewed cleanly
- committed as:
  - `d3bd127` — `Block obituary-style titles in hybrid RSS importer`
- pushed to `full-scrape-prod`
- live `/api/health` returned healthy after deploy
- fresh obituary-title scan on live API returned clean

Conclusion preserved:
- obituary/death-notice leakage is now fixed both reactively and proactively:
  1. existing live obituary item removed
  2. hybrid importer now blocks obituary-style titles before import

#### 9. Current remaining content-policy state after the fix
After the importer fix and live cleanup:
- obituary/death-notice leakage is clean on live scan
- obvious low-value crime leakage has been reduced materially
- the only remaining borderline crime item from the targeted scan was:
  - `CCTV appeal after Macclesfield FC stadium targeted in arson attack`
- that was intentionally kept as a public-interest local safety/police appeal exception

#### 10. Verified state to continue from next chat
Use the following as the verified continuation state after this April 5 follow-up:

1. GA4 is live and functioning; analytics is not the blocker.
2. Core legal/compliance URLs are live and returning `200`.
3. Guide/commercial pages already exist; guide existence is not the blocker.
4. Footer placeholder-link cleanup was completed and pushed; live homepage shell no longer shows dead `#` placeholders.
5. CJ publisher setup was largely completed but is blocked by a CJ-side onboarding/activation issue; wait for support response rather than changing the account further.
6. Live off-strategy science/celebrity/lifestyle clutter was manually reduced via admin archive actions.
7. Live obituary/death-notice leakage was manually removed.
8. `import_hybrid_news(...)` now hard-blocks obituary-style titles via `is_obituary_like(...)`.
9. Live obituary scan is currently clean.
10. Remaining borderline crime/public-interest handling is now a policy choice, not an active obituary bug.
11. Next worthwhile backend content-policy work, if needed later, is stricter low-value crime handling in `import_hybrid_news(...)` without breaking legitimate public-interest local alerts.


---

## April 6 2026 follow-up — homepage strategy restoration and live pool cleanup

### 11. Problem re-opened: homepage still showed wrong live articles after earlier cleanup
User reviewed the live homepage and correctly reported that many visible stories were still off-strategy for the Cheshire Today model. Examples seen during this session included:
- death notices / obituary leakage had already been addressed, but weaker off-strategy items still surfaced
- pub / restaurant / leisure stories
- lifestyle / shopping-review filler
- property / “best places to live” fluff
- zoo / soft human-interest filler
- weak generic explainers and low-value consumer pieces

Important diagnostic conclusion:
- the main remaining problem was not the old site-wide crime filter in `editorialPolicy.js`
- the drift had happened in the homepage section-building logic inside `frontend/src/pages/HomePageV1.jsx`
- specifically, `Latest`, `AI & Business`, and `More stories` had become too broad during later homepage freshness / ordering iterations

### 12. Source-of-truth comparison performed before changing code
Before any new patching, the session compared:
- current active `HomePageV1.jsx`
- current active `editorialPolicy.js`
- older known-good homepage commit `6e77dd4`
- source/state documents already uploaded in the project files

What this established:
- the original project positioning remains: Local + Business + Finance + AI/Tech / local economic intelligence
- `editorialPolicy.js` had not meaningfully changed from the older strategic baseline; it was still mainly a crime/public-interest filter
- therefore the homepage regression was caused by broader homepage pool logic rather than the old editorial-policy file itself

### 13. Homepage strategy restoration work completed in frontend
A staged homepage restoration pass was carried out in `frontend/src/pages/HomePageV1.jsx`.

#### A. Latest feed restored to balanced strategic mix
The `Latest` builder was restored away from the broader strict-newest behavior and back to the intended balanced mix:
- 4 Local
- 4 Business/Finance
- 3 AI/Tech
- 1 UK

Important preserved rule:
- Latest should not consume the shared homepage dedupe pool
- it should still fill independently while staying aligned with project positioning

#### B. Strategic homepage filter added before homepage pool construction
A new helper was added in `HomePageV1.jsx`:
- `isStrategicHomepageStory(a)`

This acts before homepage sections are built and narrows the usable homepage pool beyond the basic crime filter.

It now hard-blocks obvious weak-fit homepage classes such as:
- entertainment / celebrity / showbiz / music-festival filler
- shopping-review / listicle / product-review filler
- leisure / pub / café / bar / tourism / food-tour / arts-festival filler
- soft property fluff such as “best places to live”, charming cottages, farmhouses-for-sale, etc.
- abstract astronomy / Nasa / space-science filler unless it has clear AI/tech/business relevance
- emotional human-interest filler without clear public-impact utility
- generic health/wellness explainer filler unless there is clear public-service relevance
- pool-cleaning / power-washing / mowing simulator-style filler

This is a homepage-selection change only; it does not alter layout.

#### C. AI & Business and More stories reverted toward stricter leftovers logic
The active broadened builders for:
- `AI & Business`
- `More stories`

were replaced with the older stricter dedupe-safe leftovers model.

Resulting behavior now:
- `AI & Business` draws only from the already filtered homepage pool and only when stories are genuinely AI / business / money / property-relevant
- `More stories` now behaves as filtered leftovers instead of reintroducing broad weak-fit content through separate permissive allow logic

### 14. Local verification completed before deploy
The following verification steps were completed locally:
- frontend backups created before edits
- repeated local build checks with `npm --prefix frontend run build`
- intermediate local homepage screenshot checks on `http://127.0.0.1:3000`
- local passes confirmed the homepage was materially cleaner after the second tightening pass

### 15. Frontend commits and deploy state from this session
Frontend strategic homepage restoration was committed and deployed in stages.

Important commits from this session:
- `1aef3cb` — `Tighten homepage strategic filter to remove lifestyle and promo filler`

The live frontend bundle was then verified to update from the earlier deployed bundle to:
- `/static/js/main.cc4d37d5.js`

Additional live bundle verification:
- the new strategic filter strings (for example `bean-to-cup`) were confirmed present in the live compiled JS bundle, proving the new homepage filter logic had deployed

### 16. Live manual archive cleanup completed after homepage tightening
After deploying the stricter homepage logic, live API scans were run to identify the still-active weak-fit items in the current active article pool.

#### A. First live weak-fit cleanup batch archived
The following were archived as clear off-strategy / weak-fit live items:
- `69d298cb3e111f15c2ab9415` — Pepsi withdraws as UK festival sponsor after Kanye West backlash
- `69d1f06424de2d6384902ba8` — charming cottage in Chester suburb
- `69d1f08924de2d6384902baa` — market town named among UK’s best places to live
- `69d1fc4224de2d6384902bb4` — walking food tours / Chester
- `69d2447024de2d6384902bba` — bean-to-cup coffee machines tried and tested
- `69d147d124de2d6384902b9f` — major arts festival returns
- `69d1fc5124de2d6384902bb5` — country pub and restaurant on market
- `69d09ef524de2d6384902b84` — rural Chester barn conversion
- `69ceb2baeca970997176aed2` — zoo anteater pup
- `69d298db3e111f15c2ab9416` — “Choc horror” flavour-bars piece
- `69d1477824de2d6384902b99` — top chef / supermarkets piece
- `69ce5b63eca970997176aeb6` — child-free pubs opinion / readers piece
- `69cb5ce56704896e9f581bfc` — historic Warrington pub festival
- `69ca154bce11a2e917daae02` — Morrisons / Home Bargains shoplifter item

#### B. Second live weak-fit cleanup batch archived
After a second scan, another remaining weak-fit batch was archived:
- `69d0f35824de2d6384902b93` — food and drink festival at Chester Racecourse
- `69d09f0624de2d6384902b85` — pub being turned into restaurant and bar
- `69ceb2dbeca970997176aed4` — refurbished Warrington pub
- `69ccb826833852083fefdd2c` — zoo giant anteater pup
- `69c90a12c7c2b8d0c741eee9` — Delamere Forest community pub story

#### C. Explicitly kept during this cleanup
These were deliberately kept because they still fit the intended strategy sufficiently:
- `Elon Musk's SpaceX set to be worth $1 trillion with planned public listing`
- `Popular restaurant to close after rising costs`
- earlier retained item: `JLR sees sales recover after cyber attack`
- earlier retained item: `CCTV appeal after Macclesfield FC stadium targeted in arson attack` (kept as borderline public-interest exception)
- earlier retained item: `Iran war driving up funeral costs in the UK`
- earlier retained item: `What is the triple lock and how much is the state pension worth?`

### 17. Current verified live outcome after the April 6 homepage cleanup
At the end of this session:
- obituary / death-notice leakage remains fixed
- weak-fit pub / property / festival / zoo / shopping-review / “best places to live” filler has been materially reduced from the live active pool
- homepage visible mix is now much closer to the intended project positioning
- `Latest` / `Business & Finance` / `More stories` are materially cleaner than at the beginning of this session
- one remaining relevant business story about a restaurant closing due to rising costs was intentionally kept

### 18. Operational note about tokens / admin actions
During this session the previous live admin token expired during a bulk archive pass.
A fresh live admin token was obtained successfully via the live `/api/admin/login` endpoint using credentials sourced from `backend/.env`, and the archive pass was then completed.

### 19. Verified continuation state after this April 6 homepage restoration
Use the following as the new source-of-truth continuation state:

1. The hybrid importer obituary leak is fixed and live.
2. The homepage now has an additional strategic filter in `HomePageV1.jsx` beyond the base crime policy.
3. `Latest` has been restored to a balanced strategic mix rather than a broad strict-newest mix.
4. `AI & Business` and `More stories` have been pulled back toward the stricter leftovers model.
5. Large live weak-fit batches (festival / pub / zoo / property-fluff / shopping-review / lifestyle filler) were manually archived.
6. The live homepage is now visibly much closer to the intended Local + Business + Finance + AI/Tech positioning.
7. Remaining future work should focus on preventing similar weak-fit items from entering the active pool in the first place, rather than repeated manual cleanup.
8. CJ publisher onboarding is still waiting on CJ-side support; no further CJ setup changes should be made until support responds.
9. The best next technical task, if needed later, is to strengthen backend import categorisation / exclusion so fewer weak-fit local leisure/property items ever enter the active pool.
10. The project should now continue from this cleaner post-restoration state, not from the earlier broad homepage state.


### 20. Newsletter subscriber import and first-live-send safety work (April 6–7, 2026)
This session materially changed the newsletter state.

#### A. Bulk subscriber imports completed
Two CSV-based subscriber imports were completed into the live `subscribers` collection.

1. First import source:
- `/Users/iuliandumitrascu/Downloads/Text/5080TargettedEmailList 2.csv`
- Valid unique emails found: `5022`
- Already in subscribers: `0`
- New imported: `5022`

2. Second import source:
- `/Users/iuliandumitrascu/Library/Mobile Documents/com~apple~CloudDocs/Downloads/16kemailslist2023dec.csv`
- Valid unique emails found: `14279`
- Already in subscribers: `4959`
- New imported: `9320`

Post-import verified live newsletter state:
- `total_subscribers: 14346`
- `active_subscribers: 14346`
- `daily_brief_enabled: 14346`

Important implementation detail:
- imported subscribers were created with the existing live default newsletter structure,
- active = `True`,
- `daily_brief = True`,
- `weekly_roundup = False`,
- `breaking_news = False`,
- default preferences preserved the project newsletter category/frequency defaults.

#### B. Test send verified against production
A live production test send was completed successfully using:
- `POST /api/send-digest-test?test_email=news@cheshiretoday.co.uk&use_preview_links=false`

Verified result:
- `success: true`
- one Daily Brief was sent to `news@cheshiretoday.co.uk`
- production links were used
- response returned a valid `tracking_id`
- article IDs included in the response confirmed the template was building links from real production article IDs

This confirmed:
- SMTP is operational,
- the production test endpoint works,
- production Daily Brief generation is capable of sending successfully.

#### C. Manual Daily Brief article selection aligned with production pillar mix
The manual Daily Brief selection path was updated so it no longer used the older broad local/other/sports ordering model.

Commit:
- `7ff8bde` — `Align manual daily brief selection with production pillar mix`

Result:
- manual sends now follow the production-oriented pillar structure,
- Local → Business/Finance → AI/Tech → National context,
- sports / entertainment / generic low-fit material excluded from that path.

#### D. First-live-send recipient caps added for safety
Because the live newsletter list expanded to `14,346` active subscribers and the site is still using Office 365 SMTP rather than a dedicated bulk-email platform, temporary first-batch caps were added before deployment.

Manual Daily Brief cap:
- commit `21dace1` — `Cap manual daily brief first live batch to 250 recipients`

Scheduled Daily Brief + Weekly Roundup cap:
- commit `25cb127` — `Cap scheduled newsletter batches to 250 recipients`

Current protected behavior:
- manual Daily Brief = capped to first `250`
- automatic Daily Brief = capped to first `250`
- automatic Weekly Roundup = capped to first `250`

#### E. Important operational warning about current cap logic
The current `250` cap is only a temporary safety brake.
It is **not** yet a proper batching system.

Current limitations confirmed during this session:
- the cap is **not random**,
- the cap is **not rotating**,
- there is **no subscriber fairness / round-robin logic yet**,
- some email paths still use `.to_list(1000)` upstream, so parts of the code may still only consider the first `1000` matching subscribers before applying the `250` recipient cap.

Practical consequence:
- without further batching work, the same early slice of the subscriber list is likely to receive the scheduled sends repeatedly.

#### F. Engagement-based batching was investigated but is not yet implemented
Email tracking infrastructure exists:
- tracking pixels for opens,
- tracked click redirects,
- `digest_log`,
- `email_analytics`,
- send-level `tracking_id` values.

However, this session confirmed the system currently tracks **campaign/send-level analytics**, not true **per-subscriber engagement ranking** for send selection.

Therefore:
- true engagement-based subscriber selection is **not yet available**,
- the live `250` cap should be treated as a one-week temporary risk-control measure only.

#### G. Review reminder created
A reminder was scheduled for:
- `13 April 2026 at 09:00 Europe/London`

Purpose of that reminder:
- review Daily Brief / Weekly Roundup results under the temporary `250` cap,
- decide whether to move next to:
  - round-robin batching, or
  - a proper bulk email provider.

### 21. Affiliate network onboarding state after Awin / Impact work (April 7, 2026)
This session also moved affiliate onboarding forward materially.

#### A. Impact.com outcome
- Impact.com Marketplace application was declined.
- No further Marketplace onboarding work was pursued after that result.
- The session pivoted to Awin as the higher-value active network path.

#### B. Awin onboarding completed to active usable state
Awin account state at the end of this session:
- account active,
- payment details completed,
- tax details completed as a UK sole-trader-style setup,
- profile materially usable for advertiser applications.

#### C. Awin application volume reached a sufficient first-pass level
At stopping point, the account had:
- `33 pending` advertiser applications,
- `4 joined` advertiser programmes.

This was judged sufficient for the first pass and applications were intentionally paused to avoid low-quality over-application.

#### D. Current joined Awin programmes
The four joined programmes at the end of this session were:
- `WebHosting UK Com Ltd.`
- `ISOQAR Academy`
- `Create`
- `Interparcel`

These are a credible first commercial base because they map directly to:
- websites / hosting,
- startup / site creation,
- business shipping / parcel delivery,
- compliance / training.

#### E. Recommended first commercial pages based on current joined programmes
The immediate commercial content priority identified from the joined Awin base is:

1. `Best website hosting for small businesses in the UK`
   - use: WebHosting UK + Create

2. `Best website builders for small business websites in the UK`
   - use: Create + WebHosting UK

3. `Best parcel delivery and courier services for UK small businesses`
   - use: Interparcel

4. `How to choose a shipping solution for an online business in the UK`
   - use: Interparcel

5. `Best ISO training and certification courses for UK businesses`
   - use: ISOQAR Academy

6. `What ISO certification means for a small business`
   - use: ISOQAR Academy

Operational recommendation from this session:
- stop applying for now,
- wait for pending Awin approvals,
- build the first commercial seed pages around the four already joined programmes,
- then expand only after the next wave of approvals arrives.

### 22. New source-of-truth continuation state after this session
Continue from the following assumptions in the next chat:

1. Live newsletter subscribers now total `14,346` active records.
2. Daily Brief live send infrastructure works and was successfully tested to `news@cheshiretoday.co.uk`.
3. Manual Daily Brief content selection was aligned with production pillar logic.
4. Temporary first-batch recipient caps are live in code for:
   - manual Daily Brief,
   - scheduled Daily Brief,
   - scheduled Weekly Roundup.
5. Those caps are currently only a temporary protection layer and are not yet fair batching.
6. Engagement-based subscriber selection is not yet implemented despite existing tracking infrastructure.
7. Reminder already scheduled for `13 April 2026 09:00 Europe/London` to review newsletter batching.
8. Impact.com Marketplace path is effectively parked after decline.
9. Awin is now the active affiliate-network priority.
10. Awin current state at session end = `33 pending`, `4 joined`.
11. The first commercial content build should now focus on joined-programme pages (hosting / website builder / shipping / ISO training) rather than additional affiliate applications.


### 23. April 7, 2026 follow-up — first joined-programme commercial seed set completed
This follow-up session converted the joined-programme plan from section 21 into live published authority pages and also fixed one important authority-page frontend issue.

#### A. Existing live authority-page system was re-verified before changes
Before creating anything new, the following were re-confirmed from live code / live API state:
- `frontend/src/App.js` still mounts `/guides/:slug` to `AuthorityPage`
- `frontend/src/pages/AuthorityPage.jsx` still fetches `/api/authority-pages/{slug}`
- `backend/server.py` still exposes:
  - `GET /api/authority-pages`
  - `GET /api/authority-pages/{slug}`
  - `POST /api/admin/authority-pages/upsert`
  - `POST /api/admin/seed-authority-pages`
- live published authority-page inventory did **not** yet include the six new joined-programme pages planned in section 21.

This confirmed the correct operational path:
- do **not** invent a parallel content system,
- use the live authority-page collection already in production,
- seed the new pages there first,
- then visually verify before publishing.

#### B. Admin auth path re-used successfully
A fresh admin token was obtained again through:
- `POST /api/admin/login`

Token verification succeeded through:
- `GET /api/admin/verify`

Operational note preserved:
- this session used the existing login-token path,
- `ADMIN_PERMANENT_TOKEN` was not present in `backend/.env` at the time of this follow-up,
- credentials in `backend/.env` were sufficient for operational login.

#### C. Six new joined-programme authority pages were seeded into live DB as drafts first
The six planned pages from section 21 were created through the live upsert endpoint as **drafts** first.

New pages created:
1. `best-web-hosting-small-business-uk`
   - `Best web hosting for small businesses in the UK (2026): uptime, support and value`
2. `best-website-builders-small-business-uk`
   - `Best website builders for small business websites in the UK (2026): easiest ways to launch`
3. `best-parcel-courier-services-small-business-uk`
   - `Best parcel and courier services for small businesses in the UK (2026): delivery, cost and reliability`
4. `how-to-choose-shipping-solution-online-business-uk`
   - `How to choose a shipping solution for an online business in the UK (2026)`
5. `best-iso-training-certification-courses-uk-businesses`
   - `Best ISO training and certification courses for UK businesses (2026)`
6. `what-iso-certification-means-small-business-uk`
   - `What ISO certification means for a small business in the UK (2026)`

Each page was created with:
- `category: Business`
- `monetisation: affiliate`
- one intro section,
- one or two joined-programme tool rows,
- multiple long-form `content` sections,
- direct affiliate URLs matching the currently joined Awin programmes:
  - WebHosting UK
  - Create
  - Interparcel
  - ISOQAR Academy

#### D. Public route verification completed for all six new pages
After draft creation, the public guide URLs were checked directly and all returned `200`.

This confirmed:
- route mounting works,
- live fetch works,
- the new authority-page documents were accessible through the public guide route,
- the blocker was not page existence but only publication / controlled exposure.

#### E. Important frontend authority-page issue found and fixed
During verification, one real frontend limitation was identified in `frontend/src/pages/AuthorityPage.jsx`:
- it only rendered sections with `type == "content"`
- some older live authority pages still used `type == "section"`
- canonical / `og:url` / `mainEntityOfPage.@id` were hardcoded to the homepage instead of the actual guide URL

This was corrected locally, then built, committed, and pushed.

Patch summary:
- added `guideUrl = https://cheshiretoday.co.uk/guides/${slug}`
- changed section rendering filter to accept both:
  - `content`
  - `section`
- changed:
  - canonical URL
  - `og:url`
  - JSON-LD `mainEntityOfPage.@id`
  so they now point to the current guide URL rather than `/`

Build verification:
- `npm --prefix frontend run build` passed successfully

Commit saved:
- `aae3a97` — `Fix AuthorityPage guide metadata and section rendering`

Deployment note updated:
- user clarified that deployment behavior is now effectively auto-deploy on push,
- therefore `git push origin full-scrape-prod` should now be treated as the deployment trigger rather than a separately triggered manual Render deploy.

#### F. Visual QA completed directly on live guide URLs
Each new page was opened directly on production and visually checked.

Observed result:
- title rendered correctly,
- intro rendered correctly,
- Best Pick box rendered,
- Quick Comparison rendered,
- content blocks rendered,
- affiliate disclosure rendered,
- recommended tools rendered,
- newsletter block rendered,
- page structure looked stable.

Initial visible issue on all six pages:
- they still showed the `DRAFT` badge,
- intro / closing copy still contained obvious seed-language such as:
  - `This draft guide ...`
  - `should later link ...`

#### G. All six new pages were then cleaned and promoted from draft to published
After visual verification, each of the six pages was updated through the live upsert endpoint to:
- remove visible seed-language,
- change `status` from `draft` to `published`.

Final verified published state:
- `best-web-hosting-small-business-uk` — `published`
- `best-website-builders-small-business-uk` — `published`
- `best-parcel-courier-services-small-business-uk` — `published`
- `how-to-choose-shipping-solution-online-business-uk` — `published`
- `best-iso-training-certification-courses-uk-businesses` — `published`
- `what-iso-certification-means-small-business-uk` — `published`

This means the first joined-programme commercial seed set is no longer just planned — it now exists live as published commercial / authority pages.

#### H. Commercial strategy consequence after this follow-up
The joined Awin base from section 21 has now been converted into real live commercial assets.

This materially improves monetisation readiness because:
- the four joined Awin programmes now map to actual published guide pages,
- the site has moved closer to the master strategy requirement for a real commercial page base,
- the next monetisation bottleneck is no longer "create first seed pages".

The next bottlenecks are now:
1. final article-page guide relevance / funnel polish,
2. decision on whether homepage should surface published guides directly,
3. newsletter batching fairness / rotation,
4. deeper content-quality expansion on older / thinner guide pages.

#### I. Production-safe recommendation after this follow-up
Safe recommendation **after** publishing these six pages:
- keep `NON_AMAZON_MONETISATION_ENABLED` conservative / controlled site-wide,
- allow direct published guide URLs to exist as real assets,
- do **not** treat broad site-wide guide exposure as complete yet,
- continue next with article-page funnel polish and homepage guide-surfacing decision.

Reason:
- guide infrastructure is now stronger,
- new joined-programme guide inventory is live,
- but broad non-Amazon monetisation exposure still depends on final relevance / UX polish.

### 24. Updated continuation state after this April 7 follow-up
Continue from the following verified assumptions in the next chat:

1. Source of truth remains this file: `PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260407_v5.md`
2. Newsletter state remains:
   - `14,346` active subscribers
   - Daily Brief test send verified
   - manual + scheduled Daily Brief / Weekly Roundup temporarily capped to `250`
   - current batching is **not yet fair / rotating**
3. Affiliate state remains:
   - Impact.com parked after decline
   - Awin active
   - `33 pending`
   - `4 joined`
4. The first joined-programme commercial seed set is now **completed and published**:
   - hosting
   - website builders
   - parcel / courier
   - shipping solution
   - ISO training
   - ISO certification explainer
5. `AuthorityPage.jsx` guide rendering / metadata fix is committed and pushed as:
   - `aae3a97` — `Fix AuthorityPage guide metadata and section rendering`
6. Deployment behavior should now be assumed to be push-triggered auto-deploy rather than separately triggered manual deployment.
7. The next highest-value commercial / product tasks are now:
   - finalise article-page guide relevance so Business / Finance articles surface the best matching published guides consistently,
   - decide whether homepage should surface published guides directly,
   - implement fair / rotating newsletter batching rather than fixed first-250 behavior,
   - deepen quality of older guide pages such as savings / mortgage / broadband / energy.
8. Production-safe stance still remains:
   - Amazon live
   - non-Amazon broader activation still controlled until approvals / final polish
   - guide pages themselves can exist live and published by direct URL.


### 26. April 10, 2026 follow-up — first commercial guide set published, article-guide relevance improved, and duplicate article issue fixed

A new verified state change occurred after the CJ activation update.

#### A. First six seed commercial guide pages are now published live
During this session, the first joined-programme commercial guide cluster was moved from seeded draft status to published live status.

Published guides now verified live:
- `best-web-hosting-small-business-uk`
- `best-website-builders-small-business-uk`
- `best-parcel-courier-services-small-business-uk`
- `how-to-choose-shipping-solution-online-business-uk`
- `best-iso-training-certification-courses-uk-businesses`
- `what-iso-certification-means-small-business-uk`

Guide copy was also cleaned during publishing so public pages no longer exposed visible draft-language such as `This draft guide...` or `should later link...`.

This means the first commercial seed set around:
- hosting
- website builders
- parcel / courier
- shipping solutions
- ISO training / certification

is no longer just seeded in the authority-pages store; it is now publicly published and usable.

#### B. `AuthorityPage.jsx` rendering + metadata fix shipped
A frontend fix was made and pushed so guide pages behave more like proper public assets.

Verified changes shipped:
- `AuthorityPage.jsx` now renders both `content` and legacy `section` blocks,
- guide canonical URL now points to the real guide URL instead of the homepage,
- `og:url` now points to the real guide URL,
- `mainEntityOfPage` JSON-LD now points to the real guide URL.

Commit shipped for this:
- `aae3a97` — `Fix AuthorityPage guide metadata and section rendering`

Operational consequence:
- guide pages now render correctly even where older stored guide data still uses `section` blocks,
- guide metadata is safer for indexing / sharing,
- public commercial pages are cleaner and more SEO-consistent.

#### C. Article-page guide relevance improved for the newly published business pages
After publishing the first six new commercial guides, article-page monetisation relevance was updated so Business-relevant content can surface the new commercial guide set more intelligently.

Verified patch shipped:
- `ArticlePageV2.jsx` guide selection logic now uses `contextToolType` correctly,
- new business context mappings were added for:
  - `accounting`
  - `business-banking`
  - `web-presence`
  - `shipping`
  - `iso`
- generic Business pillar fallback now prefers:
  - `best-business-bank-accounts-uk`
  - `best-accounting-software-uk`
  - `best-web-hosting-small-business-uk`
- context keyword detection was extended for:
  - business banking / payment terms,
  - accounting software,
  - hosting / domain / website builder terms,
  - courier / parcel / shipping terms,
  - ISO certification / training / compliance terms.

Commit shipped for this:
- `63ebc40` — `Improve article guide relevance for published business pages`

Operational consequence:
- the article-page commercial funnel is now materially closer to the intended model,
- published business guides should surface more appropriately from relevant content,
- this reduces the mismatch where business content previously leaned too heavily toward older finance defaults.

#### D. Duplicate article issue investigated and narrowed down
User reported visible duplicate articles in the live feed.

Live verification during this session confirmed the symptom was real:
- duplicate title groups were visible in the latest public feed,
- duplicate source URLs were also visible,
- examples included repeated Guardian and Cheshire Live URLs imported under different DB IDs at different times.

Key diagnosis findings:
1. live Mongo `articles` collection did not currently have:
   - `title_1` unique index
   - `source_url_1` unique index
2. several live import paths were still deduping mainly by title and/or image rather than source URL,
3. `/api/sync-rss-now` had lost earlier `source_url` canonicalisation + cross-feed dedupe logic that existed in older code history,
4. duplicate cleanup logic was still weaker than needed because it only scanned a limited subset and grouped only by title.

Historical code review confirmed that older `sync-rss-now` URL dedupe logic had existed previously and later dropped out.

#### E. Import-path duplicate guard fix shipped
The main import paths in `backend/server.py` were patched so duplicate prevention now includes `source_url` checks and safer insert handling.

Verified backend changes shipped:
- `import_real_news(...)`
  - now loads existing `source_url`s,
  - skips items whose normalized `source_url` is already known,
  - adds `DuplicateKeyError` protection around inserts.
- `import_hybrid_news(...)`
  - now loads existing `source_url`s,
  - skips duplicate RSS `source_url`s,
  - local RSS insert path now has `DuplicateKeyError` protection,
  - Cheshire Perplexity insert path now has `DuplicateKeyError` protection,
  - duplicate tracking now updates `existing_source_urls` after successful inserts.

Commit shipped for this:
- `a676059` — `Guard article imports against duplicate source URLs`

#### F. `sync-rss-now` URL-dedupe logic restored
Because duplicates were still reproducible through manual RSS sync after the first backend patch, the dedicated `/api/sync-rss-now` path was separately inspected.

Verified finding:
- this function had previously contained `canonicalize_url(...)`, `existing_urls`, and `seen_urls` logic,
- current code no longer had those pieces,
- therefore the sync path was still able to re-import same-source articles under certain conditions.

The old dedupe logic was restored.

Restored behavior now includes:
- `canonicalize_url(...)` inside `sync_rss_now()`,
- existing-source-url preload from current articles,
- in-batch `seen_urls` dedupe,
- post-insert update of `existing_urls`.

Commit shipped for this:
- `d3ed935` — `Restore sync-rss-now source URL dedupe`

#### G. Duplicate cleanup helper fixed and run live
Duplicate cleanup logic was then strengthened and executed live.

Verified cleanup helper improvements:
- `_remove_duplicates_internal()` now scans the full collection,
- duplicate grouping is now by normalized `source_url` first, with exact title fallback,
- short-content cleanup pass also scans the full collection.

Commit shipped for this:
- `a31fcab` — `Fix duplicate cleanup to group by source URL`

After deployment, live admin duplicate cleanup was run.

Verified cleanup result:
- `duplicates_removed`: `33`
- `short_articles_removed`: `0`
- `total_removed`: `33`
- `remaining_articles`: `1083`

#### H. Live post-fix duplicate verification passed
After the cleanup and sync-path fixes, the latest public article feed was re-checked.

Verified result in the latest public sample:
- `duplicate_title_groups = 0`
- `duplicate_url_groups = 0`

This means the visible duplicate symptom reported by the user was resolved in the latest checked live feed after:
- import-path duplicate guarding,
- `sync-rss-now` dedupe restoration,
- duplicate cleanup execution.

#### I. Updated live continuation state after this session
Continue from the following verified assumptions after this April 10 update:

1. Source of truth remains this file: `PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260407_v5.md`
2. First six commercial seed guides are now live and published, not draft-only.
3. `AuthorityPage.jsx` render / canonical / OG fix is live via commit `aae3a97`.
4. Article-page guide relevance for published business guides is improved via commit `63ebc40`.
5. CJ state remains:
   - activated
   - promotional property active
   - `0 joined`
   - `7 pending`
6. Awin state remains:
   - `33 pending`
   - `4 joined`
7. Duplicate-import protections were strengthened via commit `a676059`.
8. `sync-rss-now` source URL dedupe was restored via commit `d3ed935`.
9. Duplicate cleanup logic was improved via commit `a31fcab` and then run live.
10. Latest public duplicate verification now shows:
    - `0` duplicate title groups
    - `0` duplicate URL groups

#### J. Next highest-value tasks after this update
With the first guide cluster now published and visible duplicate feed issues cleared, the next highest-value tasks are now:
- improve the commercial quality depth of the six newly published guide pages,
- wire newly approved CJ / Awin links into the relevant published guides as approvals arrive,
- decide whether homepage should directly surface selected published guides,
- implement fair / rotating newsletter batching instead of fixed first-250 behavior,
- monitor future RSS syncs to ensure duplicate behavior does not regress.


### 27. April 10, 2026 continuation decision — controlled monetisation polish path after guide publication and duplicate-fix stabilisation

This continuation note reconciles the April 7 master state with the later April 10 verified updates.

#### A. Canonical continuation conclusion
The project has now moved past the previous two bottlenecks:
1. the first business-oriented seed commercial guide cluster now exists live as published public assets,
2. the visible duplicate-article regression has been fixed and the latest checked public sample passed with zero duplicate title groups and zero duplicate URL groups.

Because of that, the next best work is no longer foundational monetisation setup and no longer duplicate triage.
The next best work is **controlled monetisation funnel quality**.

#### B. Recommended next highest-value priority
The recommended next priority is:
- tighten and verify article-page guide selection so the live article funnel consistently shows the most relevant already-published commercial guides,
- while keeping broad non-Amazon exposure conservative.

Why this is the best next move:
- article pages are the highest-intent entry point already receiving live traffic,
- the newly published hosting / website-builder / parcel / shipping / ISO guides now give the funnel more relevant business inventory to surface,
- improving relevance here increases monetisation usefulness without needing a broad homepage monetisation rollout,
- this stays aligned with the production-safe stance of keeping non-Amazon activation controlled until approvals and polish are stronger.

#### C. What this means operationally
For the next coding session, the first technical target should be a state-check and audit of the current live selection logic in `ArticlePageV2.jsx`, specifically:
- confirm the current `pickGuidesForPillar()` / related guide-selection path,
- confirm there are no leftover generic finance fallbacks overriding stronger business-context matches,
- confirm the six newly published business guides can actually be surfaced for the intended keyword clusters,
- confirm the fallback order remains sane when no strong context match exists,
- confirm any temporary debug / duplicate branch logic from earlier guide-funnel experimentation is fully cleaned.

#### D. Recommended priority order after that audit
After the article-page guide-selection audit, the best order is:
1. improve the **commercial quality depth** of the six newly published business guides,
2. prepare a simple mapping layer so newly approved CJ / Awin links can be inserted into the matching guides quickly,
3. only then decide whether homepage should surface a very small curated published-guides block,
4. keep newsletter batching fairness as an important but secondary monetisation-system task,
5. continue duplicate-regression monitoring after future sync/import runs.

#### E. What should explicitly NOT be treated as the immediate next task
Do **not** treat these as the first next move:
- broad non-Amazon feature-flag activation site-wide,
- aggressive homepage monetisation rollout,
- major layout redesign,
- complex schema expansion for authority sections.

Reason:
- the master strategy still requires controlled rollout,
- the design/layout constraint remains unchanged,
- previous sessions already established that `AuthoritySection` should remain flat-schema and safe.

#### F. Practical next-chat execution recommendation
Resume with this operational intent:
- check current code state first,
- inspect `ArticlePageV2.jsx`, `AuthorityPage.jsx`, and any guide-selection helper usage,
- verify the live-safe production stance is still preserved,
- then make the smallest possible relevance-cleanup patch before touching homepage guide surfacing.

#### G. Updated practical recommendation to carry forward
Use this as the continuation instruction after April 10:

`Continue Cheshire Today from PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260407_v5.md and the April 10 continuation notes. Respect workflow: check current state first, no manual file edits, one command at a time, verify after each step. Assume first six business seed guides are published, AuthorityPage metadata/rendering fix is live, article-page business-guide relevance has been improved, duplicate protections are strengthened, sync-rss-now URL dedupe is restored, and latest duplicate verification passed. Next highest-value task: audit and tighten ArticlePageV2 guide-selection logic so live business articles consistently surface the most relevant already-published guides while keeping NON_AMAZON_MONETISATION_ENABLED conservative.`

---

### 28. April 10, 2026 continuation — importer-side strategic filtering tightened to stop off-strategy article leakage

This continuation followed the April 10 guide-publication / duplicate-fix state and pivoted back to a higher-priority editorial issue: weak-fit articles were still entering the live pool despite earlier homepage clean-up.

#### A. Reconstructed cause from current code + prior state
A fresh code/history check confirmed:
- earlier homepage regression had already been addressed in `HomePageV1.jsx`
- active homepage code still contains `isStrategicHomepageStory(...)` and hard-blocks for:
  - entertainment / celebrity / lifestyle filler
  - shopping / review / listicle filler
  - pub / café / leisure / festival fluff
  - soft property fluff
- therefore the remaining leakage was no longer mainly a homepage-selection issue

The actual remaining leak path was identified in active backend importer code:
- `import_hybrid_news(...)` in `backend/server.py`
- this path still:
  - hard-excluded Manchester sources
  - hard-blocked obituary / memorial titles
  - capped crime-like stories
  - required image + minimum content quality
- but it still mechanically imported `Property` items based on category and did not hard-block broader low-utility lifestyle / promo / entertainment / soft-property filler at ingestion

#### B. Live importer state confirmed before patch
Inspection of active `backend/server.py` confirmed:
- `property_articles = [a for a in uk_with_images if a.get('category') == 'Property']`
- `property_target = min(2, max(0, request.uk_articles - finance_target))`
- import gate did not yet include a broader low-utility hard block

Conclusion:
- off-strategy items could still enter the active pool upstream even after homepage logic had already been tightened
- the correct next fix was importer-side exclusion, not more homepage-only cleanup

#### C. Importer tightening patch applied in `backend/server.py`
A targeted backend patch was added to the live importer path.

New helper added:
- `is_low_utility_article(article)`
  - hard-blocks obvious low-utility lifestyle / promo / entertainment / soft-property filler at ingestion
  - patterns include:
    - celebrity / showbiz / reality-TV / Love Island / Netflix / movie / film
    - shopping-deal / promo style filler
    - restaurant-review / afternoon-tea / festival fluff
    - dream-home / charming-cottage / house-for-sale / farmhouse-for-sale type soft property content

New helper added:
- `is_useful_property_article(article)`
  - allows Property stories only when they match utility/public-impact housing themes such as:
    - planning
    - development
    - housing
    - rent / rental
    - landlord / tenant
    - mortgage / remortgage
    - stamp duty
    - council tax
    - affordable homes
    - green belt
    - house prices
  - automatically rejects property items that also trip the low-utility filter

#### D. Importer bucket and gate changes completed
The following active importer changes were then made:

1. Property bucket tightened
- `property_articles` now includes only Property-category items that pass `is_useful_property_article(article)`

2. Per-article import gate tightened inside `import_category_articles(...)`
- hard-block low-utility articles before import
- re-check Property utility alignment before Property import

This means the importer now blocks more weak-fit content before it ever enters the active article pool.

#### E. Verification completed
Verification steps completed during this continuation:
- created backup:
  - `backend/server.py.bak_filter_gate_20260410_1`
- grep confirmed the patch landed in the intended three places:
  - `def is_low_utility_article(...)`
  - `def is_useful_property_article(...)`
  - tightened `property_articles = ... and is_useful_property_article(a)`
  - low-utility hard block inside importer gate
- `python3 -m py_compile backend/server.py` passed successfully

#### F. Operational impact
Expected impact of this patch:
- reduces future ingestion of pub / leisure / festival / shopping / property-fluff stories that do not fit Cheshire Today strategy
- preserves useful Property coverage, but narrows it toward:
  - planning
  - housing
  - affordability
  - rent
  - landlord / tenant
  - public-impact property topics

This is the correct long-term direction because it prevents weak-fit stories from entering the active pool upstream rather than relying only on repeated homepage filtering or manual archive cleanup later.

#### G. Recommended next step after this patch
Next recommended operational step:
1. run the next scheduled or manual import
2. inspect the newest imported items for category quality
3. archive any remaining historical off-strategy active items that were imported before this tighter gate existed
4. then continue controlled monetisation work and merchant-to-guide mapping as new CJ / Awin approvals arrive

#### H. Source-of-truth note
From this point, `PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260410_v2.md` should be treated as the active continuation file rather than the older root-only March master filename when documenting new progress.

### 29. April 10, 2026 live cleanup + datetime visibility fix follow-up

This follow-up session addressed two separate but related production issues:

#### A. Render log diagnosis clarified the real failure mode
Render logs initially looked as though imported articles were not going live. Detailed inspection showed the import pipeline itself was succeeding:
- feeds fetched successfully
- Perplexity rewrites completed successfully
- article inserts completed successfully

However, the post-import visibility step then failed with:
- `cap_visible_articles error: can't compare offset-naive and offset-aware datetimes`

This established that the main issue was not feed fetch failure, but a post-import visibility/capping error.

#### B. Root cause identified in mixed datetime handling
Inspection of `backend/server.py` confirmed:
- older datetime-normalisation work had already been done previously (`c2ba38a`, `922f0a3`)
- but current HEAD still had a remaining gap:
  - `sync_rss_now()` could still write a naive `publishedDate` when parsing feed date strings without timezone information
  - `cap_visible_articles()` still parsed string datetimes without forcing UTC awareness

This matched the live Render error exactly.

#### C. Backend fix applied and pushed
A targeted follow-on fix was committed and pushed:

- `0f37d20` — `Fix sync RSS publishedDate timezone normalization and cap visibility datetime handling`

What this changed:
1. `sync_rss_now()` now normalises parsed `publishedDate` values so naive datetimes are converted to UTC-aware datetimes
2. `cap_visible_articles()` now normalises parsed string datetimes so naive values are converted to UTC-aware before comparison

This completed the earlier March datetime-fix work rather than duplicating it.

#### D. Live production verification after push
Post-fix public API checks showed that production was not generally stuck:
- latest public sample contained fresh `2026-04-09` and `2026-04-10` content
- several titles from the Render import batch were confirmed live in the public feed, including:
  - `How many ships are crossing the Strait of Hormuz?`
  - `Have you lost a UK mortgage deal or seen your mortage rate increase? We would like to speak to you`
  - `Artemis 2 splashdown...` (before later cleanup)
  - M56 live updates under a rewritten title

Conclusion:
- the system was publishing fresh content again
- the remaining issue was specific story fit / visibility quality, not total publication failure

#### E. Live manual cleanup completed in multiple focused batches
A large off-strategy cleanup pass was then completed through live admin archive actions.

Archived in the first batch:
- `69c22c27f753a991b9c31854` — `What are zettajoules – and what do they tell us about Earth’s energy imbalance?`
- `69d930eae0c12795850127de` — `Artemis 2 splashdown UK time and how to watch live as astronauts return home`
- `69d887f6e8022cd618fcb3ae` — `Schoolboy becomes Cheshire golf club's youngest ever player to get hole-in-one`
- `69d93033e0c12795850127d4` — `‘Fresher than anything in a shop’: the best recipe boxes and meal kits for time-poor foodies, tested`
- `69d8dc35e0c12795850127cc` — `Feed the birds... just not in summer`
- `69d93055e0c12795850127d6` — `Canalside homes for sale in England and Scotland – in pictures`
- `69d887d2e8022cd618fcb3ac` — `UK band linked to Artemis II's toilet trouble`
- `69d4e7bb6236dbfa130c35b1` — `Inside Coleen Rooney's 40th birthday party at Cheshire mansion`
- `69d4935a6236dbfa130c35a5` — `The Warrington man who spent 6 months creating Hobbit costume for Comic Con`
- `69d78aa8401689c5fa90332b` — `Space: the ultimate wardrobe challenge – in pictures`
- `69d7363e401689c5fa903318` — `Artemis II is 'inspiring' a whole generation`
- `69d39626bdd9cd71c811836c` — `Pink Floyd Space Dome show returning to Jodrell Bank after sell-out 2025`
- `69d3420dac21f51975c4fa92` — `Chicken and chips and a top class beer in Paysan is a perfect afternoon...`
- `69d68d93401689c5fa903304` — `What does the dark side of the moon sound like? Nasa’s sonifications are helping us imagine`

Archived in the second batch:
- `69d63945401689c5fa9032fb` — `US and Iran agree two-week ceasefire as Donald Trump declares 'total victory'`
- `69d82efce8022cd618fcb3a4` — `Hot in the city: Energy crisis tests Singapore's air-con addiction`
- `69d4e7c86236dbfa130c35b2` — `Chester's Piccolino restaurant temporarily closes for major revamp`
- `69d4e7d86236dbfa130c35b3` — `Tributes paid after death of councillor pivotal in creation of Chester Storyhouse`
- `69d78a96401689c5fa90332a` — `Surrey scientists lead new space weather mission`
- `69d4934c6236dbfa130c35a4` — `Cheshire schoolgirl needed urgent heart surgery after falling ill on family holiday`
- `69d3eaa90ae39e16562a65f7` — `13 things which you could do in Warrington in the 90s which you can't do now`
- `69d3eac70ae39e16562a65f9` — `Vets in Glazebrook warn dog hay fever signs may go unnoticed`
- `69d68d2d401689c5fa9032fe` — `Starmer warns ‘lot of work to do’ to make ceasefire permanent at start of talks in Gulf - UK politics live`
- `69d39643bdd9cd71c811836e` — `Great Sankey business hosts veterans breakfast in north west`
- `69d39650bdd9cd71c811836f` — `Millions of Brits set to receive 'game changing' support to help them with finances`
- `69d341dfac21f51975c4fa8f` — `Devastated mum's important message after traumatic loss of son, 5`

Archived in the third batch:
- `69ca1519ce11a2e917daadff` — `Why Chinese tech companies are racing to set up in Hong Kong`
- `69d82ef0e8022cd618fcb3a3` — `Woman has leg amputated after Cheshire Tesco car park incident`
- `69d88796e8022cd618fcb3a9` — `Buy bread in the evening, hit the sales on a Tuesday: retail workers’ top tips to cut your shopping bill`
- `69d82f19e8022cd618fcb3a6` — `Zack Polanski calls for UK to withdraw trade agreement with Israel after strikes on Lebanon`
- `69d3eab70ae39e16562a65f8` — `Daresbury-based Redrow earns five-star customer rating again`
- `69d2991e3e111f15c2ab941c` — `Warrington housebuilder named five-star for tenth year running`

#### F. Duplicate-ID / live-copy discovery during cleanup
During a later cleanup pass it became clear that some public API IDs did not match the currently live UUID article records shown by the admin endpoint.

This explained why some archive actions initially appeared not to “stick”.
The actual live UUID records were then identified and archived successfully:

- `b635cf02-dab7-4034-934e-bcaaa93ad71c` — `Recap: M6 van flips as two left in hospital`
- `249f7399-81ea-4c8b-bb90-ec585a2043a2` — `Unit available in Stockton Heath after shock closure of business`
- `aa8e50f9-e93d-492c-914c-61069c59591b` — `Recap: Fire crews at 'large' fallen tree on shut Cheshire road`
- `97c381a9-c872-4910-824e-f1a3e1f3489e` — `When you will be able to see the new Spitfire at Hooton Park`

Operational lesson:
- in some cases the public feed may expose records under IDs that are not the current live UUID admin records for the same title
- for production cleanup, admin endpoint verification is safer than relying only on the public ID values

#### G. Live state after cleanup
After the datetime fix and the archive passes, the public pool became materially closer to the Cheshire Today strategy.

The feed is now much stronger on:
- Local public-impact stories
- Business / cost-of-living
- Finance / inflation / rates / fuel
- AI / Tech where relevant
- planning / housing / transport / council / service stories

Remaining borderline but not urgent titles at end of session included things like:
- `This coat cost $248 in illegal tariffs. Will he ever get the money back?`
- `Emergency services scrambled to Cheshire narrowboat fire`
- `Warrington North MP warns of cost pressures amid Middle East conflict`
- `'Significant impact' as burglars take life-saving kit from Cheshire fire station`

#### H. Updated continuation conclusion
At the end of this follow-up:
1. the datetime/capping bug causing post-import visibility failure was fixed and pushed
2. fresh April 9–10 content was confirmed live in the public feed
3. several large off-strategy batches were manually removed from the live public pool
4. the live feed is now materially cleaner and closer to the intended Local + Business + Finance + AI/Tech strategy

Recommended next priority after this:
- strengthen importer-side and classification-side filtering further so less off-strategy content reaches the active public pool in the first place,
- then continue controlled monetisation work and merchant-to-guide mapping as new Awin / CJ approvals arrive.


---

### 30. April 11, 2026 — Resend newsletter cutover + per-recipient tracking foundation

This session completed the core newsletter infrastructure repair and the first engagement-batching foundation.

#### A. Root cause of uptime failures identified
The repeated uptime drops around scheduled newsletter sends were traced to the previous Office 365 SMTP implementation.

Confirmed behavior before fix:
- scheduled Daily Brief and Weekly Roundup were capped to `250` recipients each
- newsletter sends ran synchronously on the live app process
- each recipient was sent individually
- each recipient send opened a fresh SMTP connection, logged in, sent one email, then closed

This meant a scheduled batch of 250 triggered 250 blocking SMTP login/send cycles on the live backend process.

Conclusion:
- the uptime failures were not caused by article generation or frontend behavior
- they were caused by the old per-recipient Office 365 SMTP send model

#### B. Resend account and sending domain set up
A Resend account was created and configured for production newsletter sending.

Domain chosen:
- `updates.cheshiretoday.co.uk`

DNS setup completed in GoDaddy:
- DKIM TXT record added
- sending MX record added
- SPF TXT record added

Result:
- all 3 required Resend DNS records verified successfully
- receiving was intentionally left disabled
- production sender configured as:
  - `news@updates.cheshiretoday.co.uk`

#### C. Resend production API integration added
Environment wiring added locally and in Render backend environment:
- `RESEND_ENABLED=true`
- `RESEND_API_KEY=...`
- `RESEND_FROM_EMAIL=news@updates.cheshiretoday.co.uk`
- `RESEND_FROM_NAME=Editor at Cheshire Today`

Local backup created before env changes:
- `backend/.env.bak_resend_20260411_1`

Important deployment note:
- first Resend API key used in Render was invalid
- Render logs showed:
  - `401 Unauthorized`
  - `API key is invalid`
- a brand new Resend API key was then created and replaced in Render
- after replacing the key, live test sending succeeded

#### D. Newsletter send path moved from Office 365 SMTP loop to Resend batch API
`backend/app/email_service.py` was changed so Daily Brief and Weekly Roundup now use Resend batch sending when `RESEND_ENABLED=true`.

Implementation details:
- `httpx` used for Resend API calls
- Resend env/config added to `EmailService`
- helper added:
  - `_resend_from_header()`
  - `_send_resend_batch(batch_messages)`
- messages are chunked in batches of `100`
- Daily Brief and Weekly Roundup now build personalized message payloads and send via Resend batch API
- old SMTP path remains as fallback if Resend is disabled

Backups created:
- `backend/app/email_service.py.bak_resend_batch_cutover_20260411_1`

Commit:
- `f76248a` — `Move Daily Brief and Weekly Roundup to Resend batch sending`

Outcome:
- live test Daily Brief send succeeded through Resend
- test response showed:
  - `"success": true`
  - `"emails_sent": 1`

This materially reduces the previous uptime risk because the scheduled newsletter path is no longer doing per-recipient Office 365 login/send cycles.

#### E. Current newsletter send caps remain in place
Code inspection confirmed current caps are still:

- manual send path: `250`
- scheduled Daily Brief: `250`
- scheduled Weekly Roundup: `250`

So although total subscribers are ~14,000+, current scheduled sends are still intentionally limited to the first `250`.

This is acceptable for the current phased cleanup / engagement workflow.

#### F. Per-recipient tracking implemented
Previous newsletter analytics only tracked a single `tracking_id` per send, which allowed campaign-level analytics only.

That was not sufficient for the planned “batch 001 → review → deactivate cold subscribers → next 250” workflow.

Fix added in `backend/app/email_service.py`:
- new helper:
  - `_recipient_tracking_id(base_tracking_id, recipient_email)`
- Daily Brief and Weekly Roundup now:
  - derive a unique recipient tracking ID using a recipient email hash suffix
  - replace the base tracking ID inside each recipient’s HTML
  - generate per-recipient tracked preference/unsubscribe links
  - generate per-recipient tracked open/click IDs

Result:
- opens/clicks are now attributable to each recipient instead of only to the whole campaign

Backup created:
- `backend/app/email_service.py.bak_per_recipient_tracking_20260411_1`

Commit:
- `11d56f2` — `Add per-recipient tracking IDs for newsletter analytics`

#### G. Per-recipient tracking verified live
A live Daily Brief test send was sent successfully after the per-recipient tracking patch.

The resulting Mongo query confirmed a real per-recipient analytics record was created:

Example matched record shape:
- tracking ID prefix:
  - `daily_brief_2026-04-11T12:57:23.263069_ff93aeb7`
- stored tracking ID example:
  - `daily_brief_2026-04-11T12:57:23.263069_ff93aeb7_512929bd`

Observed verified behavior:
- open events stored
- click events stored
- clicked article URLs stored
- recipient hash suffix present

This confirmed that per-recipient tracking is now working in production.

#### H. Admin email analytics patched to aggregate per-recipient rows
Once per-recipient tracking was introduced, the admin analytics endpoint under-counted `recent_sends` because it still assumed one analytics row per send.

`backend/server.py` was patched so the admin analytics read path now aggregates all `email_analytics` rows whose `tracking_id` begins with the send’s base tracking ID.

Backup created:
- `backend/server.py.bak_email_analytics_prefix_fix_20260411_1`

Commit:
- `77af404` — `Aggregate per-recipient tracking in admin email analytics`

After deployment, live admin analytics returned valid recent send data again.

#### I. Live analytics state after fixes
Live `/api/admin/email-analytics?days=7` confirmed:

- `DailyBrief.sent = 1253`
- `DailyBrief.success = 1252`
- `WeeklyRoundup.sent = 1`
- `WeeklyRoundup.success = 1`

Recent sends showed Daily Brief runs of `250` subscribers with real opens/clicks now visible in `recent_sends`.

#### J. Batch 001 subscriber cohort snapshotted
The first Daily Brief cohort of `250` subscribers was snapshotted and saved so later review/deactivation decisions are based on a fixed cohort rather than a drifting live query.

Files created:
- `daily_brief_batch_001.json`
- `daily_brief_batch_001_engagement.json`

Validation:
- saved first 10 emails matched the current live first 10 emails
- this confirmed batch 001 is stable

#### K. Protected emails established
A protected email list was created so internal/test addresses are not accidentally deactivated later.

Protected list stored in:
- `/tmp/newsletter_protected_emails.txt`

Included:
- `julian07891@yahoo.co.uk`
- `julian07891@icloud.com`
- `iulian.dumitrascu@henburyhouse.com`
- `news@cheshiretoday.co.uk`

#### L. Important deactivation safeguard
An initial deactivate-candidate list was generated and then explicitly invalidated.

Reason:
- Daily Brief sends from `9 April`, `10 April`, and `11 April 07:30` happened before per-recipient tracking was deployed
- those earlier sends cannot be used to judge individual subscriber engagement reliably
- therefore any generated “0 opens / 0 clicks” list based on pre-patch data is invalid for pruning

Invalid file quarantined as:
- `/tmp/daily_brief_batch_001_deactivate_candidates_INVALID_PREPATCH.txt`

Operational rule:
- do **not** deactivate or delete any batch 001 subscribers based on pre-patch analytics

#### M. Correct next pruning window
The first valid post-patch tracked Daily Brief sends for batch 001 are expected to be:

- Monday `13 April 2026`
- Tuesday `14 April 2026`
- Wednesday `15 April 2026`

Only after those 3 properly tracked sends should batch 001 be reviewed for cold subscribers.

Pruning rule agreed:
- do **not** hard-delete first
- first action should be **deactivate**
- only consider subscribers with:
  - `0 opens`
  - `0 clicks`
  - across the valid review window
- protected emails must always be excluded

#### N. Reminder created
A reminder was created for:
- `15 April 2026 at 09:00 Europe/London`

Purpose:
- review batch 001 engagement after 3 valid tracked Daily Brief sends
- exclude protected emails
- deactivate only subscribers with 0 opens and 0 clicks

#### O. Net outcome of this session
At the end of this session:

1. the unstable Office 365 newsletter batch path was replaced for Daily Brief / Weekly Roundup with Resend batch sending
2. production Resend sending was verified live
3. per-recipient newsletter tracking was implemented and verified
4. admin analytics was updated to aggregate per-recipient tracking correctly
5. batch 001 was snapshotted for controlled subscriber-quality review
6. protected internal/test emails were defined
7. pre-patch deactivate candidates were explicitly invalidated
8. the system is now ready for the first valid batch-001 engagement review after the next 3 tracked Daily Brief sends

Recommended next newsletter priority after this:
- allow the next 3 properly tracked Daily Brief sends to hit batch 001
- then build the first valid deactivate list for batch 001 only
- deactivate cold subscribers (excluding protected emails)
- then move to the next 250 cohort in a controlled wave

