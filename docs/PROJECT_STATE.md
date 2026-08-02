# Cheshire Today — Consolidated Operational State Master

> **Authoritative operational source of truth — updated 12 July 2026**
>
> This is the single Cheshire Today operational state file to read first and update going forward.
> It reconciles the historical project record, the 26 June and 7 July updates, both 10 July
> operational phases, and the 12 July Admin OpenAI factual-rewrite/editorial-guard work.
>
> Do not use `Cheshire_Economic_AI_Project_Master_Feb2026.pdf` as current operational truth.
> Use it only for high-level historical strategy when explicitly relevant.

## Current operational checkpoint — 12 July 2026

```text
Branch: full-scrape-prod
Latest pushed commit: 83d8d69 Expand OpenAI editorial guard patterns
Immediate next step: after deployment, press Open AI again on the same healthy-life-expectancy article.
Inspect: editorial_guard_triggered, editorial_guard_corrected,
editorial_guard_remaining_violations, and the full research_fact_pack.
Do not publish the test article merely because it reads well.
Verify every name, study, quotation, figure, and healthcare comparison.
```

Core workflow remains:

```text
- Read this file before code/database/content-pool/category/newsletter/affiliate/advertising/article-generation changes.
- Check current repo and live state before changing anything.
- One safe command/action at a time.
- Scripted edits only unless unavoidable.
- Use /usr/bin/grep, not rg.
- Run syntax and diff checks before commit.
- Do not use npm start unless explicitly requested.
- OpenAI remains admin-only and must never auto-publish.
```

## Source reconciliation

State files reviewed and reconciled:

```text
cheshire_today_project_state_CONSOLIDATED_UPDATED_20260710(1).md
cheshire_today_project_state_latest_UPDATED_20260526.md
cheshire_today_project_state_latest_UPDATED_20260526_UPDATED_20260530.md
cheshire_today_project_state_latest_UPDATED_20260526_UPDATED_20260707.md
cheshire_today_project_state_latest_UPDATED_20260526_UPDATED_20260707(1)(1).md
cheshire_today_project_state_latest_UPDATED_20260710.md
```

Reconciliation findings:

```text
- The 10 July consolidated file is the fullest historical/operational base.
- The 12 July file contains the newer Admin OpenAI factual-rewrite and editorial-guard section.
- The 7 July section in the consolidated and 12 July files is identical and is retained once only.
- UPDATED_20260526.md and UPDATED_20260710.md are byte-identical despite different filenames.
- Older state files are subsets or earlier branches of the chronology now preserved here.
```

Other uploaded project references reviewed:

```text
Cheshire_Economic_AI_Project_Master_Feb2026.pdf
report.pdf
report 2.pdf
report 3.pdf
```

Treatment of those references:

```text
- The February master is historical strategy only, not operational truth.
- report.pdf is an older competitor-analysis reference.
- report 2.pdf and report 3.pdf are byte-identical website-assessment copies.
- These PDFs were not inserted into the operational chronology because they are research/audit references,
  not later verified code, database, deployment, newsletter, monetisation, or editorial state updates.
```

---

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

Reminder was then upgraded so it:
- includes the exact script sequence
- runs daily at `09:00`
- continues batch-by-batch until all newsletter subscribers have been reviewed
- keeps protected emails excluded
- only deactivates subscribers with `0 opens` and `0 clicks` after 3 valid post-patch sends

#### O. Private batch-cleanup tooling prepared
A full private batch-001 review/deactivation toolkit was prepared outside the repo in:
- `~/ct_private_newsletter_state`

Files/scripts prepared there:
- `daily_brief_batch_001.json`
- `daily_brief_batch_001_engagement.json`
- `newsletter_protected_emails.txt`
- `review_batch_001.py`
- `check_batch_001_ready.py`
- `run_batch_001_review_safe.py`
- `deactivate_batch_001_candidates.py`

Safety behavior verified:
- readiness check reports `READY_FOR_BATCH_001_REVIEW = NO` until 3 valid post-patch sends exist
- safe review runner exits early if fewer than 3 valid sends exist
- deactivation script exits harmlessly if no valid candidate file exists

This means the batch 001 cleanup workflow is now guarded against premature pruning.

#### P. Net outcome of this session
At the end of this session:

1. the unstable Office 365 newsletter batch path was replaced for Daily Brief and Weekly Roundup with Resend batch sending
2. production Resend sending was verified live
3. per-recipient newsletter tracking was implemented and verified
4. admin analytics was updated to aggregate per-recipient tracking correctly
5. batch 001 was snapshotted for controlled subscriber-quality review
6. protected internal/test emails were defined
7. pre-patch deactivate candidates were explicitly invalidated
8. private safe review/deactivation scripts were prepared for batch 001
9. the system is now ready for the first valid batch-001 engagement review after the next 3 tracked Daily Brief sends

Recommended next newsletter priority after this:
- allow the next 3 properly tracked Daily Brief sends to hit batch 001
- then build the first valid deactivate list for batch 001 only
- deactivate cold subscribers (excluding protected emails)
- then move to the next 250 cohort in a controlled wave

---

### 31. April 11, 2026 — Active category alignment cleanup completed safely

This session focused on removing off-strategy active category paths without risking a broad production taxonomy rename.

#### A. Core decision taken
A temporary attempt was made to rename core display labels toward `Local` / `UK`.

After inspecting active frontend and backend query paths, this was judged unnecessarily risky for the current production state because:
- `Local News` and `UK News` are still deeply wired into backend filters, stored article data, admin views, and various defaults
- the real strategic problem was not those two labels
- the real problem was the continued survival of off-strategy categories such as Sports, standalone Property, Entertainment, Health, and Science

Final decision for this session:
- keep canonical labels:
  - `Local News`
  - `UK News`
- remove or fold the off-strategy category paths instead of renaming the whole system

#### B. Source-of-truth strategy confirmed from project file
The source file was checked before patching.

Confirmed strategy from the project notes:
- Cheshire Today positioning remains:
  - Local + Business + Finance + AI/Tech
- de-emphasise / remove:
  - sports
  - celebrity / entertainment
  - weak science filler
  - generic health filler
  - soft property fluff
- previous notes already supported keeping only useful housing / planning / cost / public-impact property coverage rather than a broad Property pillar

This session therefore aligned active code to that existing strategy rather than inventing a new one.

#### C. `backend/app/news_feed_service.py` aligned to project categories
A backup was created first:
- `backend/app/news_feed_service.py.bak_category_alignment_20260411_1`

Changes made:
- removed BBC Sport and Sky Sports feed entries entirely
- remapped feed categories:
  - `Property` → `Finance`
  - `Health` → `UK News`
  - `Science` → `Tech`
  - `Entertainment` → `UK News`
- removed standalone Sports / Entertainment override outputs by converting them into disabled internal guard keys:
  - `_REMOVED_SPORTS`
  - `_REMOVED_ENTERTAINMENT`
- removed standalone Weather category as a live target while preserving weather-detection logic via:
  - `_GUARD_WEATHER`
- tightened allowed RSS categories to:
  - `UK News`
  - `Local News`
  - `Business`
  - `AI`
  - `Tech`
  - `Finance`
  - `Tax`
- folded former Property keyword override logic into Finance
- folded former Science keyword override logic into Tech
- folded former Education and Health keyword override logic into UK News
- stopped the final classification guard from converting UK stories into `Sports`

Net effect:
- off-strategy categories are no longer being created as live feed/category outcomes in the active feed service
- weather is still detected for public-interest protection, but not as a standalone category target

#### D. `frontend/src/pages/HomePageV1.jsx` cleaned up
A backup was created first:
- `frontend/src/pages/HomePageV1.jsx.bak_category_alignment_20260411_1`

Homepage changes:
- active homepage display path continues to use canonical labels:
  - `Local News`
  - `Business`
  - `AI & Tech`
  - `Finance`
  - `UK News`
- legacy standalone Property homepage section was removed
- useful housing / planning / property-type stories are now folded into the existing Finance sidebar feed
- important safeguard added:
  - property/housing enrichment into Finance is capped at **max 2 items**
  - this prevents Finance from being overtaken by property content
- Top Stories property slot was folded into Finance rather than kept as a separate Property slot
- AI/business/general homepage card display now uses the shared display helper more consistently
- no broad homepage architecture rewrite was done; this was a focused taxonomy cleanup only

Net effect:
- no standalone Property section remains on the homepage
- Finance remains the active money/housing/tax section, with property/housing only as controlled enrichment

#### E. `frontend/src/utils/editorialPolicy.js` updated carefully
Changes made:
- display helper still preserves canonical output:
  - `Local News`
  - `Business`
  - `AI & Tech`
  - `Finance`
  - `UK News`
- explicit `Tax` handling added so tax-tagged material can surface with the correct label rather than being swallowed generically by Finance

Important note:
- the brief experiment to output `Local` / `UK` was rolled back in the same session
- final committed state keeps `Local News` / `UK News` for safety and compatibility

#### F. `backend/server.py` aligned without risky stored-data renaming
A backup was created first:
- `backend/server.py.bak_import_category_alignment_20260411_1`

Changes made:
- UK import path no longer imports Property as a separate quota/category
- useful Property articles are now treated as:
  - `property_enrichment_articles`
  - imported into `Finance`
  - still capped separately before UK fallback fill
- critical safeguard preserved:
  - original Property articles must still pass `is_useful_property_article(article)` even when folded into Finance
- trending headline valid category list updated to remove off-strategy categories and align with current editorial direction
- newsletter/default category registries were updated to keep:
  - `Local News`
  - `UK News`
  - `Business`
  - `Finance`
  - `Tax`
  - `AI & Tech`
- category filtering endpoint updated to support both:
  - legacy stored labels
  - temporary `Local` / `UK` query compatibility
  even though final canonical labels remain `Local News` / `UK News`

Net effect:
- backend active category defaults are materially cleaner
- Property is no longer treated as a standalone active import category
- no dangerous stored-data migration was attempted

#### G. Safety checks performed during this session
Important checks completed before commit:
- active code paths were inspected first rather than doing blind global renames
- duplicate-key issue in keyword override dict was detected and corrected before commit
- a temporary `Local` / `UK` renaming attempt was explicitly rolled back
- backend syntax verified:
  - `python3 -m py_compile backend/server.py backend/app/news_feed_service.py`
- frontend production build verified successfully:
  - `npm --prefix frontend run build`

This confirms the category cleanup is technically stable in the current committed state.

#### H. Commit created
Commit created and pushed:
- `610d532` — `Align active categories with project strategy and remove standalone sports/property paths`

#### I. Final result of this session
At the end of this session:

1. canonical labels remain safely:
   - `Local News`
   - `UK News`
2. Sports active feed/category path has been removed
3. standalone Property homepage section has been removed
4. useful property/housing coverage now flows into Finance with a hard cap
5. Science is no longer a standalone active category path and is folded into Tech
6. Health and Entertainment are no longer standalone active category paths and are folded into UK News
7. weather remains only as a classification/public-interest guard, not a target category
8. backend syntax passed
9. frontend production build passed

#### J. Recommended next priority after this
Best next follow-up after this category-alignment cleanup:
- clean remaining lower-risk UI/admin legacy category labels where appropriate
- especially:
  - `AdminDashboard.jsx`
  - `MobileSearch.jsx`
  - `BreakingNewsTicker.jsx`
  - `AffiliateWidgets.jsx`
- but only in controlled passes, because some remaining references are display-only while others still reflect legacy stored backend categories


---

### 33. April 11–12, 2026 — live import verification, category strategy hardening, location persistence fixes, and active-pool cleanup

This continuation moved beyond code-only category cleanup and into full production verification on the live Cheshire Today system.

The session goal was to answer four practical questions:
1. whether the new category-alignment code was actually live and safe,
2. whether live imports now matched the project strategy,
3. whether local town/location metadata could be trusted enough for future balancing,
4. and whether the active pool could be cleaned safely without destabilising the site.

#### A. Starting verified state before live checks
At the start of this continuation, the following had already been completed and pushed:
- active category cleanup to remove standalone Sports paths and fold standalone Property into Finance,
- canonical display labels kept as:
  - `Local News`
  - `UK News`
  - `Business`
  - `Finance`
  - `AI & Tech`
- frontend build had already passed,
- backend syntax checks had already passed,
- source-of-truth update file had already been refreshed earlier in the day.

The next task was therefore not theoretical code review.  
It was live production verification.

#### B. First live import verification confirmed deployment and importer health
A live production sync was triggered through:
- `POST /api/sync-rss-now`

The initial result confirmed:
- backend deploy was live,
- import endpoint was functioning,
- RSS fetch volume remained healthy,
- new content was still entering the system,
- but active quality/mix still did not fully match the intended project positioning.

Early live-output findings included:
- `Local News` remained too dominant,
- `Science` was still visible in live output,
- some weak-fit or broad local-source consumer/advice pieces were still landing as `Local News`,
- some opinion/lifestyle pieces were still entering `Finance`.

This proved the system was technically healthy but strategically noisy.

#### C. Live category mix was measured before rebalancing
A live category sample of recent articles showed roughly:
- `Local News: 41`
- `Business: 15`
- `Finance: 12`
- `Science: 7`
- `Tech: 4`
- `UK News: 2`

Interpretation:
- Local was over-weighted,
- Business / Finance / Tech authority share was too thin,
- Science should not survive as an independent strategic pillar,
- importer defaults still leaned too heavily toward local/general supply relative to authority supply.

#### D. Hybrid import defaults were rebalanced toward Business / Finance / AI-Tech
A targeted backend rebalance was implemented in `backend/server.py`.

Changes made:
- `cheshire_articles: 8` → `5`
- `uk_articles: 12` → `7`
- `business_articles: 2` → `5`
- `tech_articles: 2` → `5`
- UK-side internal finance share changed:
  - `finance_target: 3` → `5`
- useful property enrichment within Finance was tightened:
  - `property_enrichment_target: 2` → `1`

Manual/admin refresh defaults were aligned to the same lower-local / higher-authority mix.

Commit shipped:
- `6891265` — `Rebalance hybrid import toward business finance and AI`

Operational conclusion:
- future imports now structurally favour Business / Finance / AI-Tech more than before,
- Local/UK default intake was reduced,
- Science was not increased as its own category and should instead trend toward Tech/AI where relevant.

#### E. Location/town imbalance was investigated and root causes were identified
The user correctly questioned why live local output looked dominated by Warrington/Cheshire Live-style coverage rather than a balanced mix across Cheshire towns.

Measured live local-source distribution showed roughly:
- `Cheshire Live: 22`
- `Warrington Guardian: 14`
- `Chester Standard: 5`

But the more important finding was:
- most live Local News records had no usable town metadata:
  - `location = None` for the large majority of sampled local articles

This showed the problem was not just source dominance.  
It was also that town metadata was missing or being lost, which prevented meaningful town balancing.

#### F. Feed-config town metadata existed, but was being lost in several active code paths
Inspection confirmed that many local feed definitions already carried explicit feed-level locations, for example:
- Warrington Guardian → `warrington`
- Chester Standard → `chester`
- Cheshire Live town feeds mapped to:
  - `chester`
  - `crewe`
  - `macclesfield`
  - `northwich`
  - `wilmslow`
  - `knutsford`
  - `warrington`
  - etc.

However, production checks showed many live articles still ended up with:
- `location: None`
- `priority_location: None`

Root causes identified:
1. `backend/app/news_feed_service.py` had multiple article-construction paths, and not all of them persisted both:
   - `location`
   - `priority_location`
2. `backend/server.py` live API normalization could remove existing location metadata if title/summary detection failed.
3. `/api/sync-rss-now` rebuilt fresh article documents and dropped:
   - `location`
   - `priority_location`

This meant valid feed-derived town metadata could disappear before or during storage.

#### G. Location persistence fixes were implemented across all load-bearing paths
Several coordinated fixes were applied.

##### 1. Live article normalization fix
`backend/server.py` was changed so that live article normalization:
- preserves any existing feed-derived location first,
- only falls back to title/summary detection when location is missing,
- stops removing valid existing location metadata.

Commit:
- `1255475` — `Preserve feed-derived locations in live article normalization`

##### 2. News feed parser fallback-path fix
A weaker parser path in `backend/app/news_feed_service.py` was patched so that:
- feed-derived location is preserved first,
- detected location is only fallback,
- `location` and `priority_location` are carried forward.

Commit:
- `e329452` — `Preserve feed-derived locations in news feed parser`

##### 3. Remaining parser construction paths fixed
Additional parser construction paths were patched so all active feed construction routes now preserve:
- `location`
- `priority_location`

Commit:
- `b56f04f` — `Persist local feed locations across all parser paths`

##### 4. Live sync insert path fixed
`/api/sync-rss-now` was patched so stored article documents now explicitly retain:
- `location`
- `priority_location`

Commit:
- `2a5860e` — `Persist location metadata in live RSS sync imports`

#### H. Result of location work
After redeployment and further syncs:
- fresh local imports began carrying town metadata more reliably in some cases, for example:
  - Warrington Guardian item with `location: warrington`
  - Chester Standard item with `location: chester`
  - Chester Standard item with `location: macclesfield`

However:
- many older articles imported before the full fix still remained blank,
- some broad general local-source items still lacked a detectable town,
- and the project still lacked a safe, fully verified town-balancing layer.

Decision taken:
- do **not** keep spending session time on perfecting location today,
- accept that location is improved for future imports,
- move back to the higher-value problem: off-strategy live imports and active-pool quality.

#### I. Source-of-truth strategy check confirmed importer-side exclusion remains the right direction
Before tightening imports further, source-of-truth references were re-checked.

Confirmed strategic direction remained:
- Cheshire Today should be a hybrid:
  - Local
  - Business
  - Finance
  - AI & Tech
- off-strategy content should be reduced upstream in the importer rather than merely hidden on the homepage,
- weak-fit Sports / Entertainment / low-value lifestyle / weak Science / soft property fluff should be blocked or reduced before entering the active pool.

This matched earlier source-file conclusions that importer-side exclusion is the correct long-term direction.

#### J. `sync-rss-now` was found to be strategically weaker than `import_hybrid_news(...)`
Detailed inspection showed that:
- `import_hybrid_news(...)` already used stronger logic such as:
  - `is_low_utility_article(...)`
  - `is_useful_property_article(...)`
- but `sync_rss_now()` still used:
  - a much weaker low-utility regex,
  - candidate scoring rather than stronger exclusion,
  - and inadequate blocking of local-source advice / crime / lifestyle leaks.

This was identified as the main reason off-strategy items could still enter live output even after earlier category cleanup.

#### K. Live sync filters were hardened in stages to align with project strategy
Multiple targeted hardening passes were made to `sync_rss_now()`.

##### 1. Broad sync-path hardening
Added stronger live sync logic to:
- broaden low-utility hard blocking,
- block many weak-fit lifestyle / festival / celebrity / travel / property-fluff items,
- block blank-location local-source items unless they looked genuinely public-interest / local-utility,
- reduce local sync target:
  - `LOCAL_SYNC_TARGET: 6` → `4`,
- score Business / Finance / Tax / AI/Tech more strongly than generic items.

Commit:
- `8be9f26` — `Harden live RSS sync filters toward business finance and AI strategy`

##### 2. Leak-specific refinement after live verification
After another live sync, three remaining leak types were identified:
- crime / sensational local-source pieces,
- local-source national advice pieces,
- weak opinion/commentary-style finance pieces.

Targeted regex blocks were added for:
- crime / grooming / jailed / charged / trial / behind bars,
- local-source national advice / Martin Lewis / travel warning / “check this simple thing”,
- opinion-style finance such as “The hill I will die on...”.

Commit:
- `394f223` — `Refine live sync filters for crime advice and weak opinion leaks`

##### 3. Narrow local lifestyle/testimonial leak block
A final narrow patch was added after a live sync still allowed:
- coffee-machine / saved-me-cash / local lifestyle testimonial style content.

Targeted local-source product/testimonial lifestyle phrases were blocked.

Commit:
- `e45c8b1` — `Block local lifestyle testimonial leaks in live RSS sync`

#### L. Live sync candidate pools dropped as filters tightened
Successive live syncs showed candidate pools trending down as filters improved, for example:
- around `384`
- then `378`
- then `365`
- then `353`
- then `334`
- then `322`
- then `316`

Interpretation:
- the live sync path was gradually becoming more selective,
- but repeated same-day imports also meant the remaining candidate pool got noisier as stronger stories were already consumed.

#### M. Decision taken to stop importing for the day
After repeated live syncs, the final imported batches started surfacing obviously weaker remnants such as:
- spa / “most beautiful” local leisure content,
- solar-lights product/lifestyle content,
- novelty AI/photo filler,
- and other thin consumer/travel-style items.

Conclusion:
- repeated same-day imports were no longer improving the pool,
- continuing to import would likely worsen active quality rather than improve it.

Decision taken:
- **stop importing for the day**
- keep the current hardened importer code as the new baseline
- do not continue repeated syncs in this session

#### N. Active-pool contamination was then addressed directly
Once importer behaviour improved, the remaining problem was identified as:
- older weak-fit articles already sitting in the active live pool

A targeted cleanup list of clearly off-strategy active articles was assembled from the live top output.

These included examples such as:
- local woodland “need to visit” leisure piece,
- countryside spa beauty-style piece,
- PIP national advice story published by a local source,
- travel-warning / holiday-mistake local-source advice piece,
- Martin Lewis couples advice piece,
- coffee machine testimonial,
- solar lights product piece,
- weak finance opinion (`money can buy you happiness`),
- halloumi taste-test piece,
- safari park / weak science filler,
- Guardian opinion-style Artemis science piece.

The admin login route was used to obtain a bearer token from the live environment using `ADMIN_USERNAME` / `ADMIN_PASSWORD` from `backend/.env`.

Then the live archive endpoint was used safely (archive, not delete):
- `POST /api/admin/articles/{article_id}/archive`

All 11 candidate archives returned success.

Result:
- those items were removed from the active pool without permanent deletion,
- archival safety and link preservation were maintained.

#### O. Final live top-25 verification after cleanup
After the archive pass, the top 25 live mix improved to approximately:
- `Local News: 13`
- `Tech: 5`
- `Finance: 4`
- `Business: 2`
- `Science: 1`

This was materially better than before cleanup, but still not ideal.

Remaining issues at session end:
- Local News still heavier than desired,
- Business still thinner than desired,
- a few surviving Local items were still weaker than ideal,
- one Science item still remained in the active top output,
- repeated imports were no longer desirable that day.

#### P. Final operational conclusion at end of session
At the end of this continuation, the correct state was:

- **stop importing for today**
- keep the hardened importer code as the new baseline
- keep the location persistence improvements that were already shipped
- leave perfect town balancing for a later dedicated pass
- use the current state as the new stable checkpoint

#### Q. Net outcome of this continuation
At the end of this continuation:

1. live production deploys were verified multiple times,
2. hybrid import defaults were rebalanced toward Business / Finance / AI-Tech,
3. feed/parser/sync/API location persistence was improved materially for future local imports,
4. the live sync importer was hardened substantially toward project strategy,
5. the worst active off-strategy articles were safely archived,
6. repeated same-day imports were intentionally stopped once the candidate pool became noisy,
7. the system ended the session materially closer to the intended Cheshire Today positioning than it was at the start.

#### R. Best next priority after this continuation
Recommended next priority in the next session:

1. **do not start by importing again**
2. first inspect the active live output
3. perform one more small targeted archive pass for any remaining weak-fit active items
4. then audit why Business is still relatively thin versus Local / Tech / Finance
5. only patch importer rules again if the active pool still shows recurring, specific leak patterns



---

### 33. April 12, 2026 — Newsletter opt-in exposure fixed and homepage Business sidebar tightened

This session focused on two practical live-product issues:

1. Weekly Roundup existed technically but was effectively hidden from normal subscriber signup flows.
2. The homepage Business sidebar remained too weak / soft even after importer-side hardening and active-pool cleanup.

#### A. Weekly Roundup send-count discrepancy investigated and explained
Admin analytics were checked after the dashboard showed Weekly Roundup had sent to `1` recipient.

Verified findings:
- Weekly Roundup logs in `digest_log` were real, not UI noise.
- Recent Weekly Roundup sends showed:
  - Sunday 12 April 2026 at 09:00 UK time sent to `1`
  - Sunday 5 April 2026 at 09:00 UK time sent to `1`
- The open count above subscriber count on one prior send was explained by repeat opens from the same recipient.
- The recipient was confirmed to be the user’s own email.

Conclusion:
- the Resend migration was not broken,
- Weekly Roundup sending was functioning,
- the real issue was that very few subscribers were actually opted into `weekly_roundup = true`.

#### B. Root cause of low Weekly Roundup audience identified
The frontend and backend preference flow were traced end-to-end.

Confirmed behavior:
- imported / migrated newsletter subscribers defaulted to:
  - `daily_brief = true`
  - `weekly_roundup = false`
  - `breaking_news = false`
- Weekly Roundup is only sent to subscribers with `weekly_roundup = true`
- the temporary scheduler/send cap of `250` is only a batch ceiling, not a guaranteed audience size
- therefore a Weekly Roundup send to `1` was consistent with the current preference state, not with a sending failure

#### C. Public preference UI existed, but was hidden from normal signup flow
Frontend inspection confirmed that preference support already existed:
- `PreferencesPage.jsx`
- `NewsletterPreferences.jsx`
- `/newsletter/preferences` route
- backend preference endpoints under `/api/newsletter/email-preferences`

However, the main signup flows were not exposing it effectively.

Verified issue:
- normal subscribe forms were subscribing users directly to Daily Brief
- most flows did **not** automatically surface the preferences modal/page after successful subscribe
- therefore most users never saw the Weekly Roundup toggle at the moment they joined

Conclusion:
- Weekly Roundup was technically implemented,
- but functionally under-exposed in the live UX.

#### D. Newsletter preference exposure fixed across all live signup entry points
A consistent product decision was implemented:
- after successful subscribe, the preferences modal should open automatically
- when the email is already known, the modal should jump straight to the toggle step instead of asking for email again

Implemented changes:

##### 1. `NewsletterPreferences.jsx`
- added auto-open behavior when `open === true` and `initialEmail` is already known
- modal now:
  - preloads the email
  - jumps directly to the preference-switch step
  - loads current existing preferences if present

##### 2. `NewsletterFull.jsx`
- homepage full-width newsletter block now opens `NewsletterPreferences` automatically after successful subscribe
- subscribed email is preserved and passed into the modal

Commit:
- `5ef574e` — `Open newsletter preferences after subscribe to expose roundup opt-in`

##### 3. `SubscribeSection.jsx`
- subscribe section now also opens preferences immediately after successful subscribe
- subscribed email is preserved and passed into the modal

This aligned the component behavior with the full-width subscribe path.

##### 4. `NewsFooter.jsx`
- footer newsletter signup was found to be a separate live subscribe path
- it previously subscribed successfully but never opened preferences
- it was patched to:
  - preserve subscribed email
  - open `NewsletterPreferences`
  - expose Weekly Roundup immediately after subscribe

##### 5. `JobsWidget.jsx` / `SubscribeInlineBanner`
- under-hero / inline subscribe path on homepage and article placements was found to use `SubscribeInlineBanner`, not `SubscribeSection`
- this path was patched to match footer behavior:
  - preserve subscribed email
  - open `NewsletterPreferences`
  - expose Weekly Roundup immediately after subscribe

Commit:
- `c07e012` — `Open newsletter preferences after inline subscribe to match footer flow`

#### E. Preference toggle interaction bug found and fixed
During local testing, the Weekly Roundup and Breaking News toggles were visible but could not be switched on.

Root cause:
- each toggle card had a parent `onClick`
- the nested `Switch` also handled its own change event
- clicking the switch caused a double-toggle, returning the value to its original state

Fix:
- wrapped the `Switch` with click-stopping behavior so clicks on the switch do not bubble to the parent container

Commit:
- `214ec61` — `Fix newsletter preference toggles and expose roundup opt-in in footer flow`

#### F. Newsletter UX verified locally and live
Local and live verification confirmed:
- subscribe succeeds
- preferences modal opens automatically
- modal skips the email-entry step when the email is already known
- Weekly Roundup is visible immediately at signup
- Weekly Roundup and Breaking News toggles now work correctly
- saving preferences works correctly

Final conclusion for newsletter system at end of this session:
- Resend sending path is working
- admin Weekly Roundup counts are real
- the former problem was UX exposure, not send infrastructure
- Weekly Roundup opt-in is now exposed properly at signup on the live product

#### G. Business-supply audit continued after newsletter fix
After newsletter UX was repaired, focus returned to the previously identified project priority:
- the homepage still needed stronger Business output relative to the project strategy

Feed/source audit findings:
- Business feed supply already existed in backend configuration, including:
  - BBC Business
  - Sky Business
  - Companies House
  - ONS
  - DBT
  - CMA
  - Insolvency Service
  - IPO
  - Google News UK startup/VC feeds
- therefore the Business weakness was **not mainly missing feed inventory**

This shifted the diagnosis toward selection/rendering logic rather than source configuration.

#### H. Hidden homepage feed was cannibalising Business items
Inspection of `HomePageV1.jsx` found a structural issue:
- `financeArticles` / `financeFeed` was still being built in homepage logic
- but `financeFeed` was not rendered in the live homepage sidebar
- despite being effectively hidden, `financeArticles` was still consuming Business candidates and adding them into shared used-key sets
- the visible `businessFeed` was then built **afterwards** from leftovers only

Practical effect:
- Business items were being thinned before reaching the actual rendered Business sidebar

Fix:
- removed the `isBusiness(...)` consumption passes from the hidden `financeArticles` selection logic
- kept Money/Finance behavior intact
- allowed visible `businessFeed` to receive a fairer share of Business candidates

Commit:
- `247ef1d` — `Stop hidden finance feed from consuming business homepage items`

#### I. Business sidebar quality was then tightened
After the cannibalisation fix, the live Business block improved, but still surfaced weak-fit items such as:
- celebrity/luxury-brand management stories
- soft feature-style international environment pieces

A dedicated Business-slot quality filter was added in `HomePageV1.jsx`.

New logic:
- Business sidebar must still satisfy business classification,
- but now also rejects softer / celebrity-adjacent / luxury-brand-management framing,
- and requires stronger business / market / regulatory / industry signals for the dedicated Business sidebar slot.

Examples of intended keep signals:
- company / companies
- earnings / profits / revenue / sales / trading
- market / investment / funding
- manufacturing / factory / supply / shortage
- trade / tariff / aviation / energy / utilities / water / mining
- banking / jobs / employer / regulation / CMA / insolvency / merger / takeover / shares / stocks

Commit:
- `91a8235` — `Tighten homepage business sidebar selection quality`

#### J. Final narrow Business refinement applied
After live verification, one remaining softer item still appeared in the Business sidebar:
- feature-style environmental framing (`Every drop of water counts`, `Fear for the future`)

A final narrow exclusion was added to keep this specific feature-style framing out of the Business sidebar without broadening the filter more than necessary.

Commit:
- `8e63e3f` — `Refine homepage business sidebar to exclude soft feature filler`

#### K. Live business sidebar state after fixes
Live checks showed the Business sidebar became materially better.

Observed progression:
- earlier weaker items included soft luxury/celebrity-adjacent brand pieces
- after homepage business fixes, the sidebar was reduced to much stronger items such as:
  - airline / fuel shortage / aviation business-impact coverage
  - airport systemic fuel risk coverage
- one softer environmental feature was then removed with the final narrow refinement

Conclusion:
- the Business sidebar is now meaningfully closer to the project’s intended Local + Business + Finance + AI focus,
- and no longer appears to be losing strong Business candidates to a hidden feed path.

#### L. Final verified state at end of this session
At the end of this session:

Newsletter system:
- all main live signup entry points now expose preferences immediately after subscribe
- Weekly Roundup is now visible and practically opt-in-able at signup
- toggles save correctly
- Resend remains the active live send infrastructure

Homepage editorial/business state:
- hidden feed cannibalisation of Business candidates has been removed
- Business sidebar quality has been tightened
- live Business block is cleaner and more strategically aligned than before

#### M. Recommended next priority after this session
Best next priority:
1. update the source-of-truth project file with this newsletter + Business-sidebar work
2. do one final quick live weak-fit article review if needed
3. then move into the next commercial phase:
   - article-page guide relevance refinement
   - business/finance merchant mapping
   - guide monetisation depth improvements

#### N. Operational continuation note
From this point, the current live product has improved in two important non-trivial ways without redesign:
- newsletter monetisation / audience segmentation is now surfaced properly in UX
- homepage Business quality is structurally stronger

This should now be treated as the new baseline before resuming article-page monetisation funnel work.


---

### 32. April 12, 2026 continuation — archive-state protection, live-pool cleanup, article-page guide relevance, and completion of remaining monetisation draft guides

This continuation followed the earlier April 12 newsletter UX repair and homepage Business-sidebar cleanup.

The work completed here addressed four remaining operational priorities:
1. stop manually archived weak-fit articles from being resurrected by backend capping logic,
2. clean the current live active pool now that archive behavior could be trusted,
3. tighten article-page guide relevance while keeping non-Amazon monetisation OFF,
4. convert the last four draft monetisation guide shells into real published authority pages and then clean stale future-facing guide slugs.

#### A. Live-pool audit showed remaining weak-fit items despite earlier homepage fixes
After the homepage Business fixes were deployed, a fresh live audit of `/api/articles?limit=30&with_total=1` still showed a noisy surfaced pool.

Observed issues included:
- Local News still containing leisure / review / “you need to visit” / soft consumer-advice filler,
- Tech still carrying nature / wildlife / NASA diary-style items that were not strong AI/tech authority coverage,
- Finance still carrying weak review/opinion/listicle items,
- some items previously archived in earlier cleanup work appearing to have resurfaced.

Important conclusion:
- import balancing and homepage Business improvements were real,
- but the live active pool still required one more controlled archive cleanup pass.

#### B. Root cause found: manual archives were being undone by `cap_visible_articles()`
A direct Mongo inspection of previously archived article IDs proved the resurfaced articles were **the same Mongo documents**, not fresh duplicate re-imports.

Verified live state on those documents:
- collection: `articles`
- `archived: False`
- `archived_at: None`
- same `_id` values as earlier manually archived rows

This eliminated the “re-imported as new rows” theory.

A code audit of `backend/server.py` found the real cause in:
- `cap_visible_articles(keep=200)`

Before fix, the function did two things:
1. archived everything not in `keep_ids`
2. then blindly set every `_id` in `keep_ids` back to:
   - `archived: False`
   - unset `archive_reason`
   - unset `archived_at`

Practical effect:
- if a manually archived weak-fit article was still recent enough to fall inside `keep_ids`,
- the auto-cap job resurrected it on the next run.

This explained exactly why earlier cleanup did not hold.

#### C. Backend archive-protection fix applied
A safe backend patch was made in `backend/server.py`.

##### 1. Manual admin archives now set an explicit durable reason
The admin archive route was updated so manual archives now write:
- `archived: True`
- `archived_at: <timestamp>`
- `archive_reason: "manual_admin"`

##### 2. Auto-cap unarchive branch is now guarded
The `cap_visible_articles()` unarchive step was tightened so it only resets archive state for rows that are:
- already visible / not archived, or
- archived specifically because of `auto_cap`

It no longer blindly unarchives all `keep_ids`.

This preserves the intent of auto-cap while protecting manual editorial cleanup.

Commit:
- `707da88` — `Prevent auto-cap from unarchiving manually archived articles`

Verification:
- `python3 -m py_compile backend/server.py` passed
- after redeploy, a manually archived article was checked directly in Mongo and showed:
  - `archived: True`
  - `archive_reason: manual_admin`
  - valid `archived_at`

Confirmed example:
- `The hidden Warrington woodland you need to visit this spring`
- remained archived with `archive_reason: manual_admin`

Final conclusion for this fix:
- manual cleanup is now durable,
- future weak-fit archive work should no longer be undone by the cap job.

#### D. Live active-pool cleanup was repeated successfully after backend fix
Once the backend protection was deployed, the previously identified weak-fit article IDs were re-archived via admin API.

Two cleanup passes were performed:

##### First pass removed obvious weak-fit surfaced items such as:
- barn conversion / spa lifestyle property piece
- village festival return piece
- pine martens / golden eagles / wildlife items misfit for Tech
- Apple iCloud scare-style consumer warning in Finance slot
- “diabolical paintings” human-interest piece
- woodland / spa / holiday mistake / coffee machine / solar lights filler
- supermarket halloumi review item
- weak consumer-advice / soft local filler

##### Second pass removed residual surfaced weak-fit items such as:
- safari park anniversary item
- money-can-buy-happiness opinion piece
- Delamere hill fort play-area leisure item
- giant otter triplets zoo item
- Artemis splashdown “how to watch” local misfit
- growing-pains emotional human-interest item
- NASA diary-style soft feature item

Result after cleanup + archive-protection fix:
- previously resurfacing manually archived items stayed gone,
- the live top 30 became materially cleaner,
- Business stabilized at a stronger visible presence,
- Tech/Finance noise reduced.

A representative post-cleanup surfaced mix showed:
- Local News: 16
- Finance: 5
- Business: 4
- Tech: 4
- Science: 1

Important interpretation:
- the surfaced top-30 mix still does **not** equal the importer’s category target mix,
- but the live pool is now clean enough to stop spending more time on reactive archive cleanup and return to monetisation-quality work.

#### E. Article-page guide relevance was refined without activating non-Amazon monetisation
A source-of-truth check confirmed that most monetisation infrastructure already existed.

Verified production-safe state before further work:
- `AMAZON_AFFILIATES_ENABLED: true`
- `NON_AMAZON_MONETISATION_ENABLED: false`

This meant the next correct move was **not** broad rollout.
Instead, the correct task was to improve the hidden/restricted article-page guide matching so it would be ready for future controlled activation.

##### What was already present
`ArticlePageV2.jsx` already contained:
- `pickGuidesForPillar(...)`
- `pillarLabel`
- `contextToolType`
- guide promo blocks
- body autolink logic gated behind the non-Amazon flag

##### Relevance issues found
The guide-selection logic was structurally good but had notable gaps:
- `property` lacked a dedicated explicit branch,
- `energy` lacked a proper guide-picking branch,
- `tax` still leaned too heavily on `council-tax-bands-cheshire` while that page was still draft,
- finance fallback ordering could be better aligned with the now-published guide set.

##### Patch applied
`frontend/src/pages/ArticlePageV2.jsx` was updated so:
- `tax` now prefers:
  - `council-tax-bands-cheshire`
  - `cost-of-buying-home-cheshire-2026`
  - `best-savings-accounts-uk`
- `property` now has an explicit branch:
  - `cost-of-buying-home-cheshire-2026`
  - `best-mortgage-rates-uk`
  - `best-savings-accounts-uk`
- `energy` now has an explicit branch:
  - `cheap-energy-tariffs-uk`
  - `best-broadband-deals-uk`
  - `best-savings-accounts-uk`
- finance pillar fallback ordering was slightly improved.

Important safety note:
- no feature flags were changed,
- no non-Amazon promo blocks were turned on,
- this was relevance polish only.

Commit:
- `adfbe7d` — `Refine article guide relevance for tax property and energy contexts`

#### F. Authority-page inventory audit showed only four remaining draft shells
A live `/api/authority-pages` audit showed the core guide inventory was already strong.

Published before this continuation included:
- ISO / certification guides
- shipping guides
- web hosting / website builder guides
- mortgage, savings, credit card guides
- cost-of-buying-home Cheshire guide
- business banking / accounting / business credit card guides
- AI tools / writing / productivity guides

Only four guides remained as draft shells:
- `council-tax-bands-cheshire`
- `best-isa-platforms-uk`
- `cheap-energy-tariffs-uk`
- `best-broadband-deals-uk`

A structural check showed these were not fully empty documents, but only thin seeds:
- one intro section in most cases,
- or one intro plus an empty tool section,
- far below the section depth of published guides.

#### G. The last four monetisation draft shells were converted into real guides and published
The admin upsert contract for authority pages was inspected directly in `backend/server.py`.
A published guide structure (`cost-of-buying-home-cheshire-2026`) was also inspected to match live schema and style.

Each draft was then upgraded in the safe sequence:
1. pull current document,
2. upsert expanded structured sections while keeping `status: draft`,
3. inspect returned live JSON,
4. publish only after confirming structure/readability.

##### 1. `council-tax-bands-cheshire`
Original state:
- draft seed only
- single intro section

Expanded to:
- 11 structured sections covering:
  - what bands mean
  - checking bands
  - why similar homes differ
  - what affects bills
  - when challenges may be justified
  - affordability / budgeting context
  - practical checklist
  - disclosure

Then published successfully.

Result:
- `status: published`
- `sections_count: 11`

##### 2. `best-isa-platforms-uk`
Original state:
- draft intro
- empty comparison tool shell

Expanded to:
- 13 structured sections covering:
  - ISA platform role
  - ISA-type choice
  - platform fees
  - dealing and total cost
  - ease of use vs depth
  - cash vs stocks & shares
  - lifetime ISA considerations
  - transfers
  - user-type prioritisation
  - checklist
  - disclosure

Then published successfully.

Result:
- `status: published`
- `sections_count: 13`

##### 3. `cheap-energy-tariffs-uk`
Original state:
- draft intro only

Expanded to:
- 13 structured sections covering:
  - what makes a tariff actually cheap
  - full-cost comparison
  - fixed vs variable
  - exit fees / flexibility
  - usage-profile fit
  - monthly affordability vs annual value
  - service quality
  - switching timing
  - household-budget context
  - checklist
  - disclosure

Then published successfully.

Result:
- `status: published`
- `sections_count: 13`

##### 4. `best-broadband-deals-uk`
Original state:
- draft intro only

Expanded to:
- 13 structured sections covering:
  - household needs
  - speed in context
  - full contract cost
  - contract length
  - reliability / service
  - package contents
  - switching timing
  - budget context
  - comparison criteria
  - checklist
  - disclosure

Then published successfully.

Result:
- `status: published`
- `sections_count: 13`

Final conclusion of this guide-publication block:
- the last four remaining monetisation draft shells are no longer thin placeholders,
- all four now exist as usable published authority pages,
- the guide layer is materially more complete and much closer to commercial readiness.

#### H. `monetisationTools.js` still contained dead future slugs and was cleaned up
After guide publication, the next audit checked `frontend/src/config/monetisationTools.js` because it is still imported by:
- `HeroMonetisationStrip.jsx`
- `ContextTools.jsx`

Even though non-Amazon monetisation remained OFF, this config still mattered for future-safe activation.

The audit found several stale guide slugs that no longer matched the real published inventory, including examples such as:
- `/guides/remortgage-deals-uk`
- `/guides/best-isas-uk`
- `/guides/stamp-duty-uk`
- `/guides/0-balance-transfer-cards-uk`
- `/guides/ai-for-small-business-uk`

These were replaced with live published guide destinations.

Key replacements:
- `remortgage-deals-uk` → `cost-of-buying-home-cheshire-2026`
- `best-isas-uk` → `best-isa-platforms-uk`
- `stamp-duty-uk` → `cost-of-buying-home-cheshire-2026`
- `0-balance-transfer-cards-uk` → `best-business-credit-cards-uk`
- `ai-for-small-business-uk` → `best-ai-productivity-tools-uk`

Commit:
- `7975b22` — `Align monetisation tool links with live published guide slugs`

Important safety note:
- this change is future-safe only,
- it does not surface new non-Amazon UI while the feature flag remains OFF,
- but it prevents future activation from routing users into dead guide slugs.

#### I. Final production-safe monetisation state after this continuation
At the end of this continuation:

Still OFF intentionally:
- `NON_AMAZON_MONETISATION_ENABLED: false`

Now strengthened underneath that flag:
- article-page guide relevance for tax/property/energy contexts,
- live published availability of the previously missing tax / ISA / energy / broadband guides,
- monetisation tool config now points at real published guide slugs.

This means the project has moved from:
- “infrastructure exists but missing guide content and stale links remain”

to:
- “guide layer is substantially complete; remaining decisions are rollout/activation timing and merchant-link quality rather than missing content scaffolding.”

#### J. Commits completed in this continuation
Backend:
- `707da88` — `Prevent auto-cap from unarchiving manually archived articles`

Frontend/article-page relevance:
- `adfbe7d` — `Refine article guide relevance for tax property and energy contexts`

Frontend/monetisation config hygiene:
- `7975b22` — `Align monetisation tool links with live published guide slugs`

Homepage/business and newsletter fixes already completed earlier the same day remained part of the active baseline:
- `247ef1d`
- `91a8235`
- `8e63e3f`
- `214ec61`
- `c07e012`

#### K. Updated practical project state after all April 12 work
By the end of all April 12 work, the verified live-safe state is:

Newsletter / audience segmentation:
- signup flows expose preferences correctly,
- Weekly Roundup opt-in is visible at subscribe time,
- toggle/save behavior works.

Homepage editorial state:
- Business sidebar quality is materially stronger,
- hidden feed cannibalisation is removed,
- weak-fit active surfaced stories have been cleaned again under durable archive protection.

Backend editorial operations:
- manual archive cleanup is now durable,
- auto-cap no longer resurrects manually archived articles.

Guide / monetisation layer:
- article-page guide relevance is improved,
- all previously thin draft monetisation shells have been expanded and published,
- future-facing monetisation config points to live published guide destinations.

#### L. Recommended next priority after this continuation
Best next priority order from this new baseline:
1. update the project state file with the completed April 12 archive/guide/monetisation work,
2. keep production in conservative state with non-Amazon monetisation still OFF,
3. only then decide the next controlled commercial move:
   - merchant-link enrichment inside the newly completed guides,
   - CJ/AWIN/Impact mapping where approvals exist,
   - or a very limited activation test of non-Amazon guide promos once merchant quality is ready.

#### M. What should explicitly NOT be treated as the next immediate task
Do **not** treat these as the first immediate next move:
- broad site-wide non-Amazon monetisation activation,
- aggressive homepage guide-strip rollout,
- large layout redesign,
- another prolonged reactive archive-cleanup session unless a new regression appears.

Reason:
- the missing-guide-content problem has now been substantially reduced,
- archive durability has been fixed,
- the highest-value remaining work is now commercial destination quality / merchant mapping rather than more scaffolding.

#### N. Updated continuation instruction to carry forward
Use this as the next-chat operational instruction after April 12:

`Continue Cheshire Today from PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260412_v7_FULL.md. Respect workflow: check current state first, no manual file edits, one command at a time, verify after each change. Assume newsletter preference exposure is fixed, homepage Business sidebar has been cleaned and strengthened, manual archive cleanup is now durable because auto-cap no longer resurrects manual archives, article-page guide relevance for tax/property/energy has been improved, council-tax / ISA / energy / broadband guide shells are now published, and monetisation tool slugs have been aligned to live published guides. Keep NON_AMAZON_MONETISATION_ENABLED conservative unless there is a specific controlled activation decision. Next highest-value task is merchant-link enrichment / commercial destination quality, not broad rollout.`

---

## April 13–14, 2026 — Affiliate Monetisation Activation, Visual Rollout, Guide UI Upgrade, and Logo Asset Pass

### A. Executive summary of this continuation
This continuation moved Cheshire Today from a conservative monetisation-preparation state into a controlled live affiliate monetisation state.

The major completed outcomes are:
- non-Amazon affiliate surfaces are now active on the homepage and article pages,
- homepage affiliate cards have been redesigned and split across the page instead of appearing as a 5-card block,
- article pages now include a mid-article guide recommendation card plus the existing end-of-article guide card,
- article guide recommendations rotate in a stable per-article way instead of showing the same guide everywhere,
- the “In-depth Guide” article promo no longer defaults to the non-monetised council tax guide,
- two new Awin-approved affiliate guide pages were created and wired into the site: Virtual Office and Safestore / self-storage,
- authority guide pages received a stronger featured-pick commercial design,
- local affiliate icon/logo support was added with safe fallback behavior,
- all available affiliate icons were added locally where possible,
- all changes were pushed to `full-scrape-prod`, manually deployed on Render, and reviewed successfully.

This is now a material monetisation milestone. The previous instruction to keep `NON_AMAZON_MONETISATION_ENABLED` OFF is superseded by the controlled activation completed in this continuation.

### B. Current monetisation flag state after this continuation
The frontend monetisation flags are now intentionally ON:

```js
NON_AMAZON_MONETISATION_ENABLED: true,
ARTICLE_INLINE_GUIDES_ENABLED: true,
```

This was a deliberate activation decision after the guide inventory, article guide selection logic, and homepage placement were reviewed.

Important clarification:
- this was not a broad uncontrolled affiliate injection,
- legal/trust pages were not monetised,
- the homepage uses curated guide cards,
- article pages use guide recommendation surfaces rather than aggressive ad units,
- article recommendation logic still avoids the previous stacked multi-guide block.

### C. Affiliate programs / merchants now active in the system
The following current affiliate stack is now being used or prepared in the live guide layer:

Existing active / usable affiliate-backed guide destinations:
- 123 Reg — domain registrar guide,
- Mailchimp — email marketing guide,
- QuickBooks / Intuit — accounting software guide,
- Create — website builder / web-presence guide,
- WebHosting UK — web hosting guide,
- Interparcel — parcel / courier / shipping guide,
- ISOQAR — ISO training / certification guide.

New Awin-approved affiliates added in this continuation:
- Virtual Office services,
- Safestore self-storage.

Make a Will Online:
- approved in Awin,
- not yet wired into the live site because the actual Awin tracking link was not provided in the dashboard content available in this continuation,
- do not add the plain `https://www.makeawillonline.co.uk` URL as an affiliate destination unless the tracking URL is confirmed or generated from Awin.

### D. New affiliate guide pages created through the admin/API layer
Two new published affiliate guides were created/upserted via the local admin API using `ADMIN_PERMANENT_TOKEN` from `backend/.env`:

1. `best-virtual-office-services-small-business-uk`
   - title: “Best virtual office services for small businesses in the UK (2026): business address, mail handling and remote setup”
   - category: Business
   - monetisation: affiliate
   - primary tool: Virtual Office
   - affiliate link used:
     `http://www.awin1.com/cread.php?awinmid=83191&awinaffid=2844510`

2. `best-self-storage-services-uk-home-business`
   - title: “Best self-storage services in the UK (2026): moving house, decluttering and business storage”
   - category: Finance
   - monetisation: affiliate
   - primary tool: Safestore
   - affiliate link used:
     `http://www.awin1.com/awclick.php?mid=5915&id=2844510`

Both were verified via `/api/authority-pages?limit=200&status=published` and reviewed after deployment.

Operational note:
- local `backend/.env` did not previously contain `ADMIN_PERMANENT_TOKEN`, so a new permanent token was generated and added locally.
- do not expose or commit the token value.
- backend needed restart to load the new token.
- user normally starts backend with:
  `AUTO_GENERATION_ENABLED=true uvicorn backend.server:app --reload --host 127.0.0.1 --port 8000`

### E. Homepage monetisation changes completed
The homepage affiliate system was changed from a cramped 5-card row into a spread-out editorial recommendation layout.

Completed changes:
- `HeroMonetisationStrip` restored and active,
- homepage top placement now shows the first 3 affiliate cards,
- remaining 2 affiliate cards are inserted lower inside the Latest section,
- this avoids mobile stacking of 5 affiliate cards after Hero / Top Stories,
- cards now use stronger editorial recommendation styling:
  - logo/initial area,
  - affiliate badge,
  - benefit line,
  - stronger CTA button,
  - safer hover state,
  - affiliate disclosure text.

Primary homepage affiliate cards now include:
- Best domain registrars,
- Best website builders,
- Best accounting software,
- Best virtual office services,
- Best self-storage services.

The top-strip component now accepts:
- `start`,
- `limit`,
- `compact`,
- `className`.

This allows the same component to be reused in multiple homepage positions.

### F. Article page monetisation changes completed
Article pages now have a stronger, higher-probability click path without becoming ad-heavy.

Completed changes:
- the existing end-of-article guide recommendation remains,
- a compact mid-article guide recommendation card was added,
- `mainContent` is split paragraph-by-paragraph so the compact card appears around the middle of longer articles,
- short articles with fewer than 4 paragraphs do not force a mid-article card,
- article guide selection now uses stable per-article rotation using article ID plus slot,
- different articles can show different guides,
- the same article stays stable across refreshes,
- separate slots allow the mid-article card and lower card to vary.

Important logic retained:
- the old stacked `GuidePromoBlock` remains intentionally disabled,
- the single guide card is cleaner and less intrusive,
- the article guide card skips `council-tax-bands-cheshire` as the default and falls back to monetised guides instead.

Current fallback priority for monetised article guide recommendations includes:
- self-storage,
- virtual office,
- accounting software,
- email marketing,
- domain registrars.

### G. Article guide relevance / routing updates
Article-page guide selection now knows the newer monetised guide slugs:

Added to allowed promo guide set and routing logic:
- `best-virtual-office-services-small-business-uk`,
- `best-self-storage-services-uk-home-business`.

New article contexts added:
- `virtual-office`,
- `storage`.

New keyword detection includes:
- virtual office,
- business address,
- registered office,
- mail handling,
- mail forwarding,
- self-storage,
- self storage,
- storage unit(s),
- storage facility/facilities,
- Safestore.

These map into more relevant guide destinations instead of only generic business/accounting/domain fallback behavior.

### H. Authority guide page design upgrade completed
The guide page design was improved, especially the featured-pick / CTA area.

Completed changes in `AuthorityPage.jsx`:
- `BestPickCta` rebuilt into a premium featured-pick card,
- larger logo/initial block added,
- stronger “Featured pick” badge,
- optional rating pill retained,
- “Why we picked it” strip added,
- right-side CTA panel improved,
- CTA remains clear but no longer uses an overly harsh full-black panel,
- quick comparison cards also upgraded to use logo/initial display and stronger CTA buttons.

The redesigned guide pages were reviewed and accepted after manual Render deployment.

### I. Affiliate logo / image support completed
Local affiliate icon support was added safely.

Implementation details:
- new folder created:
  `frontend/public/affiliate-logos/`
- homepage cards already supported `logoSrc`, now populated,
- guide page added `getToolLogoSrc()` helper,
- both homepage and guide pages include image-fallback logic,
- if a logo file is missing or fails to load, the UI safely hides the image and shows initials instead,
- no broken image icons should appear.

Logo/icon files added locally:
- `frontend/public/affiliate-logos/123-reg.png`
- `frontend/public/affiliate-logos/create.ico`
- `frontend/public/affiliate-logos/interparcel.ico`
- `frontend/public/affiliate-logos/isoqar.png`
- `frontend/public/affiliate-logos/mailchimp.ico`
- `frontend/public/affiliate-logos/quickbooks.png`
- `frontend/public/affiliate-logos/safestore.ico`
- `frontend/public/affiliate-logos/virtual-office.png`
- `frontend/public/affiliate-logos/webhosting-uk.ico`

Notes:
- first pass used official favicons and Google favicon service where direct downloads failed,
- this is acceptable as a functional first step,
- best future improvement is to replace favicons with approved Awin Toolbox creatives / merchant media-kit logos where available.

### J. Commits completed in this continuation
The following commits were completed, pushed to `full-scrape-prod`, manually deployed where relevant, and reviewed:

- `34ba34a` — `Refine article-only guide rollout controls`
- `c9f5131` — `Activate homepage and article affiliate guide surfaces`
- `0953ed6` — `Add virtual office and storage affiliate guides to live surfaces`
- `8da8f8e` — `Prefer monetised guides in article promo box`
- `59a9cc3` — `Improve affiliate card design and rotate article guide promos`
- `536d6fe` — `Split homepage affiliate cards across page`
- `9819caf` — `Add mid-article guide recommendation card`
- `39083d0` — `Improve authority guide featured pick design`
- `4eae989` — `Add affiliate logo support with safe fallbacks`
- `4326325` — `Add local affiliate icon assets`
- `ffb6021` — `Add remaining affiliate logo assets`

Current known branch endpoint after this continuation:
- `full-scrape-prod` at `ffb6021`.

### K. Deployment and review state
Manual Render frontend deploys were triggered after relevant pushes.

Reviewed and accepted by user:
- homepage affiliate cards after redesign,
- homepage split layout: 3 cards top, 2 inside Latest,
- mobile homepage behavior improved because 5 cards no longer stack together,
- article mid-guide card placement,
- article lower guide recommendation remains,
- article guide rotation working acceptably,
- authority guide featured-pick design,
- logo fallback behavior,
- final logo/icon asset pass.

### L. Current live commercial UX state
The live site now has a materially improved affiliate layer:

Homepage:
- top affiliate cards show 3 recommended business tools,
- 2 additional affiliate cards appear lower in Latest,
- cards have better CTA hierarchy and logo/icon support.

Article pages:
- mid-article compact guide card appears on longer articles,
- end-of-article guide card remains,
- recommendations rotate by article and slot,
- monetised guide fallback prevents council-tax dominance.

Guide pages:
- stronger featured-pick CTA design,
- logo/icon support with fallback,
- quick comparison design improved.

### M. Remaining monetisation tasks after this update
Do next, in priority order:

1. Find / generate the correct Awin tracking link for Make a Will Online, then create and wire a wills/probate guide only after tracking is confirmed.
2. Replace favicon-style icons with approved Awin Toolbox / media-kit logo creatives where possible.
3. Monitor article-guide relevance on live pages and tighten only specific weak contexts rather than disabling monetisation.
4. Add more true affiliate merchants to the higher-value categories still under-covered:
   - business banking,
   - business credit cards,
   - savings,
   - mortgages,
   - AI tools,
   - will/probate once tracking is available.
5. Consider a dedicated “Business tools” or “Recommended services” guide hub later, but do not do another major layout redesign immediately.

### N. What should explicitly NOT be done next
Do not roll back the monetisation flags unless there is a real production problem.

Do not add the plain Make a Will Online website URL as if it were a tracked affiliate link.

Do not reintroduce the old stacked multi-guide promo block on article pages.

Do not add affiliate cards to legal/trust pages.

Do not create another large visual redesign before checking live performance and click behavior.

### O. Updated next-chat continuation instruction
Use this as the next-chat operational instruction:

`Continue Cheshire Today from PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260412_v7_FULL.md. Respect workflow: check current state first, no manual file edits, one command at a time, verify after each change. The project has now moved from conservative monetisation prep to controlled live affiliate activation. NON_AMAZON_MONETISATION_ENABLED and ARTICLE_INLINE_GUIDES_ENABLED are intentionally ON. Homepage affiliate cards are redesigned and split across the page: 3 near the top and 2 inside Latest. Article pages now include a compact mid-article guide recommendation plus the lower guide recommendation, with stable per-article rotation and monetised-guide fallback. Authority guide pages have a stronger featured-pick design. Virtual Office and Safestore/self-storage Awin affiliates are live as published guide pages and wired into homepage/article logic. Local affiliate logo/icon support is implemented with safe fallbacks, and current icons exist in frontend/public/affiliate-logos. Make a Will Online is approved but NOT wired until the real Awin tracking link is available. Current branch endpoint after this continuation: full-scrape-prod at ffb6021. Next highest-value task is Make a Will tracking/link integration or replacing favicon-style icons with approved creative assets, not broad redesign.`



---

## 31. April 14–15, 2026 — affiliate guide expansion, guide UX hardening, image filtering repair, stricter content policy, and Resend Pro cleanup mode

### A. Scope and strategic context for this continuation
This continuation was carried out from the current source-of-truth state file and remained aligned with the February 2026 Cheshire Economic & AI master strategy:
- preserve the existing site design and layout,
- continue affiliate-first monetisation,
- improve commercial pages and internal guide routing,
- keep work tightly operational and documented,
- reduce off-strategy news leakage rather than broadening generic local-news coverage.

This session therefore combined four related workstreams:
1. improve guide-page UX and affiliate-guide recommendation quality,
2. add newly approved Awin merchants into the live guide ecosystem,
3. fix content-quality regressions (bad images, death notices, crime/mugshot leakage),
4. move newsletter sending from small free-tier-safe batching toward a Resend Pro list-cleanup mode.

### B. Affiliate guide page design was materially improved
The live guide layer was upgraded well beyond the earlier basic authority-page shell.

#### What changed in `AuthorityPage.jsx`
Guide pages were upgraded in multiple staged passes:
- stronger premium guide hero / header treatment,
- stronger featured-pick card hierarchy,
- larger logo area and clearer CTA hierarchy,
- improved “why we picked it” strip,
- improved lower recommendation cards,
- sparse-state handling so sections do not look empty when only one linked provider exists,
- related-guide cards now fill recommendation areas when provider count is low,
- recommendation rotation now intentionally injects operations/compliance/shipping variety rather than showing only the same web-presence stack repeatedly.

#### Result
Guide pages now feel substantially closer to the intended money-page design rather than plain CMS shells.

User-reviewed as working/acceptable:
- featured guide panel,
- recommendation section layout,
- sparse single-provider handling,
- operations/shipping rotation appearing inside the recommendation mix.

### C. Related-guide recommendation logic was strengthened
The recommendation library in `AuthorityPage.jsx` was expanded and then re-balanced.

#### New recommendation behavior
Added to the related guide library and/or rotation logic:
- shipping / parcel courier,
- shipping-solution explainer,
- ISO training,
- ISO explainer,
- Emma mattress guide,
- Spotlight oral-care guide,
- AnyVan removals guide.

Important logic refinement:
- recommendation output was changed so a contextual page no longer uses only the same adjacent category suggestions,
- the third/fourth recommendation slots can now rotate in higher-value “operations / compliance / household / moving” affiliate guides,
- sparse guide pages now avoid visually empty recommendation sections.

#### Commits for guide UX and recommendation work
Frontend commits completed and pushed during this continuation:
- `c3d5b2c` — `Upgrade authority guide featured pick design`
- `2b3af23` — `Improve authority guide recommendation sections`
- `a264bb8` — `Expand related affiliate guide recommendations`
- `8d446d8` — `Rotate operations guides into related recommendations`

### D. New Awin merchants were added into the guide ecosystem
During this continuation, newly approved Awin merchants were turned into actual live guide destinations instead of remaining only as merchant approvals.

#### New affiliate/tracking integrations completed
Tracking links were obtained and used to create new published guides for:
- Emma Sleep
- Spotlight Oral Care
- AnyVan

#### New published guide slugs created / live in authority pages
- `best-mattress-deals-uk`
- `best-electric-toothbrushes-oral-care-uk`
- `best-removal-van-services-uk`

These were created as practical commercial / household / moving guides with:
- intro section,
- one linked tool/provider,
- additional supporting content sections.

#### Existing linked-guide ecosystem also expanded / confirmed
During this broader continuation, the live linked-guide layer now includes all of the following meaningful linked destinations:
- Make a Will Online guide routing,
- virtual office,
- self-storage,
- email marketing,
- domain registrars,
- web hosting,
- website builders,
- parcel courier,
- shipping-solution explainer,
- ISO explainer,
- ISO training,
- accounting software (QuickBooks-linked),
- Emma mattress guide,
- Spotlight oral care guide,
- AnyVan removals guide.

#### Logo/icon support added for new merchants
Local logo assets were added and wired for:
- Emma,
- Spotlight Oral Care,
- AnyVan.

Frontend commits completed and pushed for this merchant/logo work:
- `91b2a57` — `Add Make a Will Online affiliate guide routing`
- `f6a4971` — `Add new Awin affiliate guide logos and recommendations`
- `481f02b` — `Rotate new Awin guides into recommendations`

### E. Accounting guide quality was substantially upgraded
The guide audit identified one clear weak linked guide:
- `best-accounting-software-uk`

Before fix:
- only ~406 content characters,
- only 1 content section,
- 4 tools but thin editorial depth.

Action taken:
- guide was re-upserted with a much stronger editorial structure,
- kept Xero / QuickBooks / FreeAgent / Sage as comparison tools,
- kept QuickBooks as the linked affiliate provider,
- expanded commercial/supporting content to approximately 1813 characters and 4 content sections.

Result:
- accounting guide is now consistent with the stronger guide UX direction and no longer one of the weakest linked guides.

### F. Weak image leakage was diagnosed and repaired
Two separate image-quality regressions were addressed.

#### 1. Weak generic repeated newspaper image blocker
A previously repeating weak newspaper image was identified and hard-blocked in `backend/server.py`.

Commit:
- `4e57420` — `Block weak generic newspaper RSS image`

#### 2. Warrington Guardian timeout image pattern fix
A more serious issue then appeared: several live articles had `warringtonguardian.co.uk/resources/images/...` URLs that timed out and failed to render reliably.

Actions taken:
- located affected live articles via API checks,
- confirmed these URLs timed out rather than resolving clean image content,
- bulk-cleared affected image URLs from MongoDB,
- expanded `WEAK_GENERIC_IMAGE_PATTERNS` to block the full `warringtonguardian.co.uk/resources/images/` pattern from future imports.

Operational result:
- active affected articles dropped to `0`,
- future imports should not reintroduce that broken image source class.

Commit:
- `e3b38a1` — `Block Warrington Guardian timeout image pattern`

### G. Death notices returned and were fixed again more durably
The user correctly reported that death-notice content had reappeared, including in the Daily Brief.

#### Root-cause diagnosis
Inspection confirmed:
- obituary/death-notice blocking existed in one hybrid import branch,
- but the local RSS import branch still lacked the obituary blocker,
- the Daily Brief selection logic also lacked a specific obituary/death-notice exclusion,
- several existing “death notices made in Cheshire this week” items remained active.

#### Reactive cleanup completed
Clear recurring death-notice articles were archived from the database.

#### Proactive backend fixes added
`backend/server.py` was updated so that:
- local RSS import now hard-blocks obituary / memorial notice-style titles,
- local RSS import also hard-blocks obvious low-utility filler in the same area,
- Daily Brief `_is_banned(article)` now excludes death-notice / funeral-notice style content.

#### Validation completed
- backend syntax checks passed,
- active death-notice scan returned `0` after deploy.

### H. Crime / police / court / mugshot leakage was tightened further
The user then reported that some crime-like stories were still showing, including in the homepage hero and active pool.

#### Frontend protection added
`HomePageV1.jsx` hero selection was tightened so crime/sensational stories can no longer become the homepage hero through fallback paths unless they qualify as genuine public-interest exceptions.

#### Backend import policy tightened
The old crime-cap logic was removed from hybrid/local RSS import branches and replaced with hard-block behavior:
- crime / police / court / mugshot-style content is now skipped instead of allowed up to a cap.

#### Reactive live cleanup completed
Existing active crime-like items were archived in two passes:
- first pass removed obvious live crime/police/court items,
- second pass widened the keyword net to catch “cops / pervert / indecent / cannabis raid / mugshot / sexual offence”-style items that had slipped through the earlier narrower filter.

#### Backend crime keyword expansion
`is_crime_like(article)` was expanded to catch terms including:
- cops / police / officer,
- mugshot,
- sexual offence / indecent / pervert / paedophile,
- raid / drug raid / cannabis plants,
- arrested / guilty,
- and other stronger policing/court signals.

#### Validation completed
Live scans after cleanup/deploy confirmed:
- death notices: `0`
- clear local crime/police/court-style active articles: `0`

Important nuance preserved:
- broader Tech/Business stories containing words like `guilty` or `groomed` may still exist where they are not part of the local mugshot/crime-churn problem.
- The fix here was to eliminate the off-strategy local crime churn, not to mass-delete every article on any subject that contains a court/crime word.

#### Commits for filtering/content-policy work
- `85f41f7` — `Strengthen crime and death notice filtering`
- `0793760` — `Expand backend crime filter keywords`

### I. Newsletter / Resend state moved into tracked cleanup mode
This continuation also picked up the previously planned newsletter tracking review after the Resend cutover.

#### What was verified
Using `digest_log` and `email_analytics`, the last tracked Daily Brief sends were confirmed, including 3 consecutive tracked 250-recipient runs:
- 2026-04-13
- 2026-04-14
- 2026-04-15

Tracking status confirmed:
- `digest_log` contains `tracking_id` values,
- engagement is stored in `email_analytics`,
- tracking/open collections named earlier in discussion were empty because the real analytics collection in use is `email_analytics`.

#### Cold-candidate analysis completed
A safe engagement review was run against the latest 3 tracked Daily Brief sends for the first-batch audience.

Results:
- batch size reviewed: `250`
- engaged or protected: `39`
- cold candidates: `211`

Action taken:
- `211` subscribers were flagged with `newsletter_cold_candidate=true`
- they were **not** deactivated or deleted.

#### Strategic change after Resend quota warnings
The user then reported receiving repeated Resend quota warning emails every morning.

Diagnosis:
- Daily Brief was still sending `250/day`,
- this is fine for successful sending but inappropriate for Resend free-tier daily warnings / list-cleanup goals,
- later in the session the user upgraded to **Resend Pro**.

#### Final backend state for newsletter sending after Pro upgrade
The Daily Brief send logic was changed again to support a larger cleanup run:
- manual Daily Brief send path now loads active subscribers rather than tiny free-tier-safe batches,
- scheduled Daily Brief path now uses `DAILY_BRIEF_SEND_CAP` default `2000`,
- Breaking News cap was explicitly restored to `1000` after an accidental broader change during patching,
- this change is intentionally for list-cleanup / engagement qualification mode after moving to Resend Pro.

Important note:
- cold-candidate flags still exist in the database,
- but the final Resend Pro cleanup-mode code was set to send to the larger active pool again rather than excluding all cold candidates immediately,
- this was the correct choice once the user decided to test much more of the list rather than keep the free-tier conservative send cap.

Commit:
- `c54c3c1` — `Set Resend Pro Daily Brief cleanup cap`

### J. Reminder / workflow support added
A reminder task was created for reviewing newsletter cold candidates after more tracked Resend sends.

The user also explicitly reaffirmed the operating preference to update the project state/source `.md` file at the end of the major working day.

### K. Full commit sequence completed in this continuation
Relevant commits completed/pushed during this continuation included:
- `4e57420` — `Block weak generic newspaper RSS image`
- `91b2a57` — `Add Make a Will Online affiliate guide routing`
- `c3d5b2c` — `Upgrade authority guide featured pick design`
- `2b3af23` — `Improve authority guide recommendation sections`
- `a264bb8` — `Expand related affiliate guide recommendations`
- `8d446d8` — `Rotate operations guides into related recommendations`
- `e3b38a1` — `Block Warrington Guardian timeout image pattern`
- `f6a4971` — `Add new Awin affiliate guide logos and recommendations`
- `481f02b` — `Rotate new Awin guides into recommendations`
- `85f41f7` — `Strengthen crime and death notice filtering`
- `0793760` — `Expand backend crime filter keywords`
- `c54c3c1` — `Set Resend Pro Daily Brief cleanup cap`

### L. Practical deployment state after this continuation
Manual Render deploys were performed and checked across this continuation.

Deploy/review coverage included:
- frontend guide UX / recommendation improvements,
- frontend hero crime-protection change,
- backend weak-image blocker,
- backend obituary/death-notice filters,
- backend crime hard-blocking and keyword expansion,
- backend Resend Pro Daily Brief cleanup cap.

Verified outcomes during this continuation included:
- authority guides render well locally/live after design changes,
- broken/timeout Warrington Guardian image URLs are no longer active on live articles,
- death notices are absent from active live pool,
- clear local crime/police/court churn is absent from active live pool,
- guide recommendation mix now includes broader operations/shipping/compliance/household destinations,
- Resend tracked Daily Brief sends are present and analysable.

### M. Current practical project state after all April 14–15 work
By the end of this continuation, the verified state is:

Affiliate / guide layer:
- guide UX is materially stronger and closer to intended money-page style,
- new Awin merchants Emma / Spotlight / AnyVan now exist as published guide destinations,
- recommendation logic is broader and less repetitive,
- accounting guide weakness was repaired,
- logo coverage is expanded for new affiliates.

Content-policy / homepage / ingestion:
- weak timeout image sources are blocked,
- death notices are proactively blocked in local RSS and Daily Brief,
- crime/police/court/mugshot-style local churn is now hard-blocked at import level,
- homepage hero can no longer fall back into off-strategy crime/sensational content,
- historical bad items were reactively archived.

Newsletter / Resend:
- tracking is functioning through `digest_log` + `email_analytics`,
- cold candidates were identified and flagged,
- the backend is now configured for a larger Resend Pro Daily Brief cleanup run,
- Breaking News cap remains conservative.

### N. Remaining next priorities after this continuation
Best next priority order from this new baseline:
1. update the source-of-truth project state file with the work from this continuation,
2. monitor the next Resend Pro Daily Brief runs and review engagement across the larger active list,
3. decide when to start suppressing/deactivating genuinely cold subscribers only after additional tracked sends,
4. continue merchant-link enrichment and guide expansion only where real approvals/tracking links exist,
5. monitor whether any new borderline local crime/public-interest edge cases need narrower exception handling rather than broader blocking,
6. later investigate the queued Render/frontend dependency vulnerability warning backlog item after the affiliate-guide / newsletter cleanup phase is calmer.

### O. What should explicitly NOT be done next
Do not mass-deactivate newsletter cold candidates immediately after only the first flagged review.

Do not re-open the homepage layout/design again; the guide UX and homepage hero filtering now need observation rather than more visual churn.

Do not restore permissive crime-cap logic in the importer.

Do not whitelist broad image-source classes without checking timeout/render behavior first.

Do not add merchants as “live” unless an actual approved affiliate tracking link exists.

### P. Updated next-chat continuation instruction
Use this as the operational continuation instruction after April 15 work:

`Continue Cheshire Today from PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260415_v8_FULL.md. Respect workflow: check current state first, no manual file edits, one command at a time, verify after each change. The project now has a materially stronger live guide/affiliate layer, additional Awin merchant guides (Emma, Spotlight, AnyVan), stronger authority-page design, proactive timeout-image blocking, proactive death-notice blocking, hard-blocked local crime/police/court churn, and a Resend Pro Daily Brief cleanup cap of 2000 for broader engagement qualification. Cold candidates are flagged but not yet suppressed. Next highest-value work is to monitor the next tracked Resend Pro Daily Brief sends, review engagement across the expanded batch, and then make a controlled suppression/deactivation decision only after more evidence.`


### Q. Admin search, Daily Brief image/rendering, and manual-source image hardening (later April 15 continuation)
After the earlier v8 state snapshot, a further continuation focused on admin workflow friction, Daily Brief rendering quality, and future manual-article image reliability.

#### 1. Admin article search was fixed across the full database
Problem reported:
- in Admin, newly manually published articles were often not discoverable unless the user pressed **Load more** repeatedly,
- this was especially visible when trying to find the Wilmslow cycle-parking article by article ID / recently published state.

Diagnosis:
- frontend Admin article search was only filtering the currently loaded local `articles` array,
- backend `/api/admin/articles` only supported paged browsing and not a real search parameter,
- therefore newly published articles outside the first 50 loaded rows were invisible to Admin search.

Fix completed:
- backend `/api/admin/articles` was upgraded to support `search=` queries across the full article collection,
- search now checks:
  - `title`
  - `content`
  - `source`
  - `source_url`
  - `category`
  - `id`
  - Mongo `_id` when a 24-character hex article ID is detected,
- frontend Admin search box was rewired to query the backend rather than only filter the currently loaded page,
- `Load more` was updated so it still works while a search term is active,
- the frontend no longer applies a second title-only search filter after the backend search result is returned.

Verification:
- local backend search returned the exact target article when searched by Mongo article ID,
- frontend built successfully after the patch,
- change was committed and pushed.

Commit:
- `d22407d` — `Fix admin article search across full database`

Deployment state:
- user confirmed deploy completed successfully after push.

#### 2. Daily Brief email image-host problem diagnosed and fixed
Problem reported:
- Daily Brief emails showed a blue Postimage / Postimg placeholder instead of the article image,
- this occurred on manually added articles that used Postimg-hosted image URLs,
- the same problem also appeared when opening the affected article from Facebook on mobile.

Diagnosis:
- the Daily Brief hero image was embedding the article image URL directly,
- the affected manual article used `https://i.postimg.cc/...`,
- Postimg / Postimage URLs are unreliable for email rendering and some mobile/article-view contexts.

Email-specific fix completed:
- `backend/app/email_service.py` gained `_safe_email_image_url(...)`,
- Daily Brief hero image rendering now strips blocked hosts for email use,
- blocked hosts include:
  - `postimg.cc`
  - `i.postimg.cc`
  - `postimage.org`
  - `postimages.org`
- effect: a manual article may still exist on site, but if its hero image is Postimg, the Daily Brief will no longer attempt to show that broken image block.

#### 3. Daily Brief thin-content fallback was also fixed
Problem reported:
- when one manual article was published on a given day, the next Daily Brief sometimes contained only that single article,
- when no manual article was added that day, the next newsletter often had a fuller story mix.

Diagnosis:
- the Daily Brief logic first pulled unique articles from the last 24 hours,
- fallback to “latest 10 regardless of time” only triggered if the recent set was completely empty,
- so if there was exactly 1 recent article, fallback never ran and the newsletter stayed too thin.

Fix completed:
- Daily Brief fallback logic now tops up when recent coverage is too thin rather than only when it is zero,
- threshold used:
  - if `len(recent_articles) < 5`,
  - then pull additional latest unique articles,
  - merge by unique title until the email reaches a healthier story count.

Commit:
- `e6854bc` — `Fix Daily Brief image host and thin-content fallback`

Deployment state:
- backend was pushed and deployed after this change.

#### 4. Specific Postimg-backed live manual articles were repaired at database level
After the user showed the Wilmslow cycle-parking article opening with the same Postimg placeholder on mobile/Facebook, the live stored article image values were audited directly in Mongo.

Target article repaired first:
- article: `🚲 Wilmslow Businesses Offered FREE Cycle Parking in New Council Scheme`
- old image: `https://i.postimg.cc/...`
- source page OG image successfully extracted from Wilmslow Town Council,
- live article record was updated directly in Mongo to the official source-hosted image.

Verification:
- user confirmed the article page was fixed immediately after the DB-level image swap.

A wider audit of Postimg-backed articles found six remaining Postimg article records at that time.

Two Wilmslow Town Council articles were then auto-fixed from official source pages:
- `New ‘Edible Hedgerow’ Project Launched on Browns Lane in Wilmslow`
- `Free Multisports Sessions Return to Wilmslow for Summer 2026`

A third Wilmslow Town Council manual article was fixed after the user supplied the correct official source URL:
- `Work Begins on Grove Street Improvements in Wilmslow as £80,000 Project Gets Underway`

Result after these DB-level repairs:
- three Wilmslow Town Council manual articles now use stable source-hosted images,
- only three older Postimg-backed manual-entry articles remained, and the user explicitly chose to leave those older ones as-is rather than force additional historical cleanup.

#### 5. Future manual articles now auto-prefer source-page OG images
Strategic decision reached:
- older manual articles without usable source metadata could be left alone for now,
- the more important fix was to stop future manual entries from repeating the Postimg problem.

Backend hardening completed:
- added `resolve_manual_article_image(image_url, source_url)` helper to `backend/server.py`,
- manual article **create** and **update** paths now:
  - prefer the source page’s `og:image` when `source_url` exists,
  - do this especially when the provided image is blank or uses Postimg,
  - strip blocked Postimg values if no safe source image can be resolved,
  - preserve non-Postimg manual images where appropriate.

Effect:
- future manually added PR/email stories (e.g. Wilmslow Town Council releases) should automatically adopt the official source page image when a valid `source_url` is supplied,
- this is the correct durable fix for the user’s manual-email workflow.

Commit:
- `b2bcff7` — `Auto-use source images for manual articles`

Deployment state:
- push initially failed due to GitHub auth prompt corruption / token entry issue,
- user then re-used an existing valid GitHub token,
- push succeeded,
- backend was then deployed successfully.

#### 6. Git/remote workflow clarification (Termius / Tailscale / same Mac)
A short operational clarification was handled:
- the user is connecting remotely through Termius via Tailscale to the same Mac,
- Git on this Mac is configured with `credential.helper=osxkeychain`,
- therefore no special second token should be required just because the session is remote,
- the earlier push failure was determined to be an auth-prompt / token-entry issue rather than a separate remote-machine credential model.

### R. Revenue comparison review and new strategic phase creation
The user then asked for a review of a competitor / revenue comparison report against the current Cheshire Today project state and requested a new phase.

#### 1. Comparison report was assessed against the real project strategy
Key conclusion:
- the report was useful, but over-weighted broad lifestyle-magazine and generic local-news models,
- the better revenue path for Cheshire Today remains the existing strategy:
  - affiliate-first,
  - 15–25 commercial comparison pages,
  - strong internal linking from local / business / cost-of-living articles into monetisable guide pages,
  - selective local advertiser surfaces rather than trying to copy massive classified/news ecosystems.

The strongest revenue lanes identified from the comparison were:
- business / finance / household-cost / SME tooling pages,
- advertiser inventory such as business listings / event placements / newsletter sponsorships,
- email monetisation,
- selective lifestyle/property/travel only where direct sponsor or affiliate fit exists.

#### 2. New strategic phase created
A new project phase was defined:

**Phase 9 — Revenue Convergence & Commercial Infrastructure**

Primary objective:
- move Cheshire Today closer to competitor-level revenue by increasing commercial intent per session, advertiser inventory, internal-routing efficiency into money pages, and newsletter monetisation readiness.

Recommended workstreams for this new phase:
1. **Commercial capture layer**
   - strengthen article-to-guide routing,
   - improve and standardise money-page coverage,
   - complete / deepen the 15–25 commercial page layer.
2. **Local advertiser inventory**
   - paid business directory / featured listings,
   - sponsored event placements,
   - paid business spotlight surfaces,
   - newsletter sponsor inventory.
3. **Email monetisation**
   - Daily Brief sponsor inventory,
   - stronger guide/CTA mapping inside newsletter,
   - later segmentation by money/business/local-weekend intent.
4. **Revenue-weighted editorial expansion**
   - business openings/closures/investment/jobs/property/cost-of-living/SME tooling,
   - selective premium local lifestyle only where sponsor/affiliate value exists.
5. **Operational publishing efficiency**
   - ensure manual PR stories always carry a `source_url`,
   - use source-page image preference logic rather than Postimg dependence,
   - later optionally warn in Admin when a Postimg URL is entered.

#### 3. Immediate recommended first task inside the new phase
The first task for the new phase was defined as:

**Build a Commercial Gap Map**

This should inventory:
- strongest current money pages,
- weakest current money pages,
- missing money-page clusters,
- best article categories that should feed each cluster,
- next 10 highest-value guide pages to build or strengthen.

### S. Additional commits/deployments completed after the earlier v8 snapshot
Additional commits completed and pushed after the earlier v8 state file point:
- `d22407d` — `Fix admin article search across full database`
- `e6854bc` — `Fix Daily Brief image host and thin-content fallback`
- `b2bcff7` — `Auto-use source images for manual articles`

All three were pushed to `full-scrape-prod`.

Deployment coverage after those commits:
- admin search fix deployed,
- Daily Brief image-host and fallback fix deployed,
- manual source-image preference logic deployed.

### T. Updated practical project state after this later continuation
By the end of this later continuation, the verified state is now:

Admin / workflow:
- Admin article search now works across the full article database,
- article ID / URL-token-based search is supported,
- Load more continues to work even during active search.

Manual article reliability:
- three Wilmslow Town Council manual articles have been repaired to source-hosted images,
- future manual articles with valid `source_url` will automatically prefer the source page OG image,
- Postimg risk for future manual PR/email stories is materially reduced.

Newsletter / Daily Brief:
- Daily Brief hero image no longer attempts to embed blocked Postimg hosts in email,
- Daily Brief no longer collapses to a one-story send just because one recent manual article exists,
- thin recent coverage is now topped up from latest unique articles.

Strategic planning:
- the project has formally entered a new proposed next-phase framing,
- Phase 9 is now the correct strategic lens for subsequent work,
- the highest-value next strategic deliverable is the Commercial Gap Map.

### U. Updated next priorities after this continuation
New priority order after this later continuation:
1. update the source-of-truth state `.md` file with this later April 15 work,
2. begin **Phase 9 — Revenue Convergence & Commercial Infrastructure**,
3. first deliverable inside Phase 9: build the **Commercial Gap Map**,
4. after that, turn the gap map into a ranked build list of money pages, routing upgrades and advertiser surfaces,
5. continue monitoring newsletter performance under the Resend Pro cleanup configuration,
6. later optionally add an Admin warning for pasted Postimg image URLs so the editor sees the risk before saving.

### V. Updated continuation instruction for the next chat
Use this as the continuation instruction after the later April 15 work:

`Continue Cheshire Today from PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260415_v9_FULL.md. Respect workflow: check current state first, no manual file edits, one command at a time, verify after each change. The project now has full-database Admin article search, improved Daily Brief fallback behavior, blocked Postimg hero rendering in email, three repaired Wilmslow Town Council manual articles at DB level, and a deployed backend rule that future manual articles with a valid source_url auto-prefer the source page OG image instead of Postimg. The next formal strategic phase is Phase 9 — Revenue Convergence & Commercial Infrastructure. The next highest-value task is to build the Commercial Gap Map: audit current money pages, identify missing/weak monetisation clusters, and rank the next guide / routing / advertiser-surface improvements.`
---

## April 26, 2026 update — Phase 9 advertising and sponsored-placement system completed

### W. Phase 9 advertising monetisation infrastructure completed
A major Phase 9 monetisation block was completed and deployed. The project now has a functioning local-advertising funnel, advertiser lead capture, email notification, sponsored placement serving, weighted advert rotation, and an Admin-managed sponsored-placement workflow.

#### 1. Article-level advertising surfaces added and tested
Article pages were updated to promote local advertising more effectively without damaging the reader experience.

Completed article-page advertising changes:
- desktop article sidebar now includes an advertising/sponsored placement surface,
- mobile article pages now include a visible advertising surface near the top of the article flow,
- article pages fall back to a Cheshire Today self-promotion CTA when no paid advert is active,
- when a paid sponsored placement is active, the real advertiser card is shown instead,
- mobile article layout now includes a stronger continue-reading flow so the advert is visible without fully hiding article context.

Final mobile article flow:
- title area,
- first Continue reading prompt,
- article image,
- sponsored / local advertising card,
- short article intro,
- second Continue reading full article prompt,
- full article expands after reader action.

This was locally tested on mobile and later deployed successfully.

Relevant commits from this working phase include:
- `de91974` — Add mobile article advertising CTA and continue reading flow,
- `e7a4a30` — Add bottom mobile continue reading prompt.

#### 2. Advertise page pricing and client-facing explanation corrected
The `/advertise` page was revised from higher mature-site pricing to realistic launch-stage pricing for local businesses.

Current public packages:
- **Local Starter — £49/month**,
- **Local Featured — £99/month**,
- **Local Partner — £199/month**.

The previous confusing **Estimated budget** field was removed because the products are now fixed monthly packages. The form now collects business-relevant details instead:
- selected package and package price,
- name,
- business name,
- email,
- phone number,
- website / booking page / Facebook page,
- target area,
- advert message / promotion goal.

The page now explains:
- packages run for 30 days,
- adverts can appear inside article pages,
- mobile in-article advert cards and desktop article sidebar advert slots are the main current slots,
- all adverts are reviewed manually before going live,
- automatic rotation is used when multiple advertisers are active,
- higher packages receive stronger rotation priority.

Relevant commit:
- `cb0d622` — Clarify advert packages and add weighted rotation.

#### 3. Advertiser enquiry capture and email notification completed
A public advertiser enquiry endpoint was added and tested:
- `POST /api/leads/advertise`

The endpoint now:
- validates the submitted package,
- stores advertiser leads in MongoDB under `advertiser_leads`,
- records contact and advert-intent fields,
- sends an internal email notification to `news@cheshiretoday.co.uk`,
- records whether the notification was successfully sent.

Live production test confirmed:
- lead capture worked,
- MongoDB save worked,
- notification email sent successfully to `news@cheshiretoday.co.uk`,
- test lead was deleted afterwards.

Relevant commits:
- `2721e84` — Add launch advertiser lead funnel,
- `cee4313` — Email notify advertiser enquiries.

#### 4. Manual sponsored-placement serving system added
A sponsored-placement backend system was added so real paid advertisers can appear in article slots.

Public endpoint added:
- `GET /api/sponsored-placements?placement=article_sidebar&limit=1`
- `GET /api/sponsored-placements?placement=article_mobile&limit=1`

Admin/backend placement model supports:
- slug,
- placement slot,
- sponsor name,
- advert title,
- advert description,
- target URL,
- optional image URL,
- CTA text,
- package tier,
- rotation weight,
- priority,
- active state,
- optional start/end dates.

Production behaviour:
- if no paid advert exists, article pages show the Cheshire Today fallback advert CTA,
- if one or more paid adverts exist, the sponsored placement endpoint serves eligible active adverts,
- test placements were created, displayed on live mobile and desktop article pages, and deleted after confirmation.

Relevant commit:
- `282a503` — Add manual sponsored placement system.

#### 5. Automatic weighted advert rotation added
Sponsored placement selection was upgraded from simple priority ordering to weighted rotation.

Rotation model:
- Local Starter / default: standard rotation weight,
- Local Featured: stronger rotation weight,
- Local Partner / Premium: priority rotation weight.

Backend logic now:
- collects eligible active placements for the requested slot,
- applies explicit `rotation_weight` if present,
- otherwise infers weight from package tier,
- randomly selects a placement using weighted choice when `limit=1`,
- caps explicit weights defensively.

This makes the public package wording accurate: when multiple advertisers are active, ads rotate through available slots, with stronger packages receiving higher visibility probability.

Relevant commit:
- `cb0d622` — Clarify advert packages and add weighted rotation.

#### 6. Sponsored placement helper script added
A helper script was added as a backup operational tool:
- `scripts/sponsored_placement_tool.py`

It supports:
- listing sponsored placements,
- creating/updating sponsored placements,
- deleting sponsored placements,
- setting placement slot,
- setting package tier,
- setting rotation weight,
- setting priority,
- setting active/inactive state.

The script was tested by creating and deleting temporary placements. The database was confirmed clean afterwards.

Relevant commit:
- `d516f26` — Add sponsored placement helper script.

### X. Admin Advertising tab completed
The Admin Dashboard now includes a dedicated **Advertising** tab.

#### 1. Advertising Leads panel added
Backend admin endpoints added:
- `GET /api/admin/advertiser-leads`
- `POST /api/admin/advertiser-leads/{lead_id}/status`

The Admin Advertising tab now displays:
- advertiser leads submitted through `/advertise`,
- selected package,
- package price,
- name,
- business name,
- email,
- phone,
- website/Facebook page,
- target area,
- message,
- created date,
- status.

Lead actions available in Admin:
- Email advertiser,
- Open website,
- Mark contacted,
- Mark converted,
- Decline,
- Archive.

A live end-to-end test was performed:
- temporary lead created through the live `/advertise` endpoint,
- email notification successfully sent,
- lead appeared in Admin → Advertising,
- email and website buttons were tested,
- status update was tested,
- temporary test lead was deleted afterwards.

Relevant commit:
- `f236124` — Add advertising admin lead view.

#### 2. Live Sponsored Placements manager added
The Admin Advertising tab was extended so ordinary advert setup no longer requires Terminal.

Backend admin endpoints added:
- `GET /api/admin/sponsored-placements`
- `DELETE /api/admin/sponsored-placements/{slug}`

The Admin Advertising tab now includes:
- **Create Sponsored Placement** form,
- **Live Sponsored Placements** list,
- visible red **Delete advert** button.

Create Sponsored Placement form supports:
- placement selection,
- package selection,
- sponsor/business name,
- target URL,
- advert title,
- CTA text,
- optional image URL,
- advert message.

Placement selection now supports:
- Desktop + mobile article slots,
- Desktop article sidebar only,
- Mobile in-article card only.

When **Desktop + mobile article slots** is selected, Admin creates two sponsored placement records automatically:
- one for `article_sidebar`,
- one for `article_mobile`.

The form automatically assigns rotation weight and priority by package tier:
- Local Starter: standard rotation,
- Local Featured: stronger rotation,
- Local Partner: priority rotation.

Live Admin testing confirmed:
- Create Sponsored Placement worked,
- Desktop + mobile created two placements,
- paid test advert appeared on live article page,
- delete workflow worked after deployment,
- all temporary sponsored test placements were deleted,
- final sponsored placement list returned empty.

Relevant commit:
- `1b48568` — Add advertising placement manager.

### Y. Current advertising workflow after this update
The working advertising workflow is now:

1. A business clicks an article advertising CTA or visits `/advertise`.
2. The business chooses Local Starter / Local Featured / Local Partner.
3. The business submits the enquiry form.
4. The lead is saved in MongoDB.
5. An internal notification email is sent to `news@cheshiretoday.co.uk`.
6. The lead appears in Admin → Advertising.
7. The admin contacts the business and updates lead status.
8. After manual payment and review, the admin creates a sponsored placement directly in Admin.
9. The advert appears in the selected article placement slots.
10. When the campaign ends, the admin deletes the advert from Admin.

Important limitation / next commercial step:
- online self-serve payment is not yet implemented,
- payment is still manual/off-platform,
- adverts are manually reviewed and manually activated in Admin.

This is intentional for the current launch stage because local-news adverts should not auto-publish without review.

### Z. Updated technical state after Phase 9 advertising work
Current live advertising-related capabilities:
- `/advertise` is clearer and more commercially usable,
- article pages can promote local advertising and show paid sponsored placements,
- backend sponsored placement endpoint is live,
- weighted rotation is implemented,
- Admin can list advertiser leads,
- Admin can update lead status,
- Admin can create sponsored placements,
- Admin can create both desktop and mobile advert records in one action,
- Admin can list and delete live sponsored placements,
- fallback advertising CTA appears when no paid advert is active.

Current confirmed cleanup state:
- no temporary advertiser test leads remain,
- no temporary sponsored test placements remain,
- final `git status --short` was clean after push.

### AA. Updated next priorities after this Phase 9 block
Recommended next order:
1. Keep the current advertising system live and monitor whether local businesses submit enquiries.
2. When the first real advertiser is secured, use Admin → Advertising to create the placement after payment and review.
3. Add impression and click tracking for sponsored placements so monthly reports can be sent to advertisers.
4. Add optional start/end date handling in Admin UI so 30-day campaign expiry is easier to manage.
5. Add a simple paid-advert performance summary inside Admin.
6. Later add Stripe/PayPal checkout only after the manual process proves advertiser demand.
7. Continue the Commercial Gap Map work for affiliate and guide-page expansion.
8. Continue monitoring Daily Brief performance and Resend Pro engagement before any cold-subscriber suppression.

### AB. Updated continuation instruction for the next chat
Use this as the continuation instruction after the April 26 Phase 9 advertising work:

`Continue Cheshire Today from PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260426_v10_FULL.md. Respect workflow: check current state first, no manual file edits, one command at a time, verify after each change. The project now has a live Phase 9 advertising system: clear /advertise launch packages, advertiser lead capture, email notifications to news@cheshiretoday.co.uk, Admin Advertising tab, lead status actions, manual sponsored-placement creation, desktop + mobile placement creation, weighted advert rotation, live sponsored placement list/delete controls, and fallback article advertising CTAs when no paid advert is active. Temporary test leads and adverts were deleted, and the working tree was clean after deployment. The next highest-value options are: add sponsored placement impression/click tracking and reporting, add Admin start/end-date handling for 30-day campaigns, or continue the Commercial Gap Map for affiliate / guide-page revenue expansion.`

---

## AC. April 26 2026 — Post-v10 advertising payment, tracking, and pay-later update

This section supersedes the earlier Phase 9 note that payments were still manual. The advertising system has now been extended into a live-tested Stripe **review-before-payment** workflow while preserving manual editorial/commercial approval before publication.

### 1. Sponsored advert performance tracking completed
Sponsored placement performance tracking was implemented and pushed.

Backend tracking endpoints added:
- `POST /api/sponsored-placements/{slug}/impression`
- `POST /api/sponsored-placements/{slug}/click`

Frontend `SponsoredPlacement.jsx` now records one impression when a paid sponsored placement loads and one click when a paid sponsored placement is clicked. Admin Advertising now displays impressions, clicks, placement priority/weight, and expiry date.

Local verification completed:
- temporary placement `test-metrics-advert` created,
- local backend function calls incremented `impression_count` and `click_count`,
- temporary test placement deleted afterwards.

Relevant commit:
- `4f4d22e` — Track sponsored placement performance.

### 2. Stripe review-before-payment advertising checkout completed
Advertising payments were added using the official `stripe` Python package. The older `emergentintegrations` Stripe wrapper in the project appeared unusable locally, so treat the jobs Stripe flow as a separate future audit item.

Advertising backend additions:
- `ADVERTISING_PACKAGES`:
  - `local_starter` — £49 / 30 days,
  - `local_featured` — £99 / 30 days,
  - `local_partner` — £199 / 30 days.
- `POST /api/advertising/checkout`
- `GET /api/advertising/payment-status/{session_id}`
- Stripe webhook update to handle `type = advertising` payment transactions.

Frontend additions:
- `frontend/src/components/AdvertisingPaymentSuccess.jsx`
- route `/advertise/payment-success`

The `/advertise` page was changed from immediate enquiry submission into a safer client journey:
1. client chooses package,
2. client fills advert details,
3. client clicks **Review advert details**,
4. details are shown locally before any backend submission,
5. client can choose either payment or enquiry path.

Customer-facing safeguards now shown before payment:
- selected package and price,
- 30-day campaign explanation,
- where the advert can appear,
- manual review before publication,
- the 30-day run starts only when the advert is approved and published,
- payment does not auto-publish the advert.

Relevant commit:
- `bc734d0` — Add review-first advertising payment flow.

### 3. Render Stripe key setup and live Stripe test confirmation
Render backend environment variable was updated with:
- `STRIPE_API_KEY = sk_test_...`

The live backend checkout endpoint was tested successfully:
- `POST https://cheshiretoday.co.uk/api/advertising/checkout`
- returned `success: true`,
- returned a `checkout_url`,
- returned a Stripe test session beginning `cs_test_...`.

A live end-to-end Stripe test-card payment was completed successfully:
- public `/advertise` flow opened Stripe Checkout,
- Stripe test card payment succeeded,
- user was redirected to `/advertise/payment-success`,
- success page displayed “pending Cheshire Today review”,
- backend recorded the paid lead as:
  - `status = paid_pending_review`,
  - `payment_status = paid`,
  - Stripe session ID saved.

The paid test lead and matching payment transaction were deleted afterwards.

Important operational note:
- Current Render Stripe mode is **test mode** while `STRIPE_API_KEY` is `sk_test_...`.
- To accept real customer payments later, replace it with `sk_live_...` in Render backend environment variables, then redeploy.
- Do not store or paste Stripe secret keys in chat.

### 4. Enquiry path and pay-later email link completed
The user identified that sending enquiry emails at the “Review advert details” step created noise if the client changed their mind. The flow was corrected.

Current two-path customer flow:

Path A — pay now:
1. client fills details,
2. review appears locally only,
3. no email and no lead are created at review stage,
4. client clicks **Continue to secure payment**,
5. backend creates a `payment_pending` advertiser lead and Stripe checkout session,
6. after successful payment, lead becomes `paid_pending_review`.

Path B — enquiry instead:
1. client fills details,
2. review appears locally only,
3. client clicks **Send enquiry instead**,
4. advertiser lead is created intentionally,
5. internal email goes to `news@cheshiretoday.co.uk`,
6. client receives a confirmation email,
7. that email now includes a secure **Continue to secure payment** link.

Backend pay-later additions:
- `AdvertiseLeadCreate` now accepts `package_id` and `origin_url`.
- enquiry leads now save `package_id`, `payment_token`, and `payment_token_created_at`.
- client confirmation email includes `/advertise/pay?token=...`.
- `POST /api/advertising/checkout/from-lead/{payment_token}` creates a fresh Stripe Checkout session from a saved enquiry.

Frontend pay-later additions:
- `frontend/src/components/AdvertisingPayLater.jsx`
- route `/advertise/pay`

Relevant commit:
- `57cfc7c` — Add advertising enquiry pay later link.

Live/local verification completed:
- review step appears instantly,
- no email/lead created until deliberate action,
- **Send enquiry instead** creates a lead and sends admin/client emails,
- enquiry-only test lead had `status = new`, `payment_status = None`, notification flags true,
- pay-now test created `payment_pending` lead and Stripe transaction,
- test leads and transactions were deleted afterwards,
- no sponsored placements active after tests.

### 5. Current paid-advert processing state
A paid customer should appear in Admin → Advertising as:
- `status = paid_pending_review`,
- `payment_status = paid`.

Do not publish adverts for leads showing:
- `payment_pending` — customer opened Stripe but did not complete payment.

Current manual processing workflow after payment:
1. open Admin → Advertising,
2. find lead with `paid_pending_review` / `paid`,
3. review business, website, area, message,
4. contact advertiser for logo/image/wording if needed,
5. create sponsored placement in Admin,
6. choose Desktop + mobile unless otherwise agreed,
7. set package tier to the paid package,
8. publish the advert,
9. mark lead converted / completed after advert is live.

### 6. In-progress local Admin improvement — create advert from paid lead
At the end of this working block, an Admin UI helper was started locally to make paid-lead processing easier.

Local change applied to `frontend/src/components/AdminDashboard.jsx`:
- added `prepareSponsoredPlacementFromLead(lead)` helper,
- adds a **Create advert from lead** button for leads where:
  - `lead.status === "paid_pending_review"`, or
  - `lead.payment_status === "paid"`,
- the button pre-fills the sponsored placement form with sponsor name, target URL, package tier, title placeholder, description, placement, CTA, and active status,
- adds `id="create-sponsored-placement"` to the sponsored placement form container,
- scrolls Admin to the form after prefill,
- improves lead badge wording:
  - `payment_pending` → `checkout started, not paid`,
  - `paid_pending_review` → `paid — needs review`.

Frontend build reportedly passed after this local Admin helper patch.

Critical continuation warning:
- This Admin helper was **not yet committed or pushed** when the user asked to update the MD file and move to a new chat.
- The next chat must first run `git status --short` and inspect `frontend/src/components/AdminDashboard.jsx` before making assumptions.
- If the AdminDashboard change is still present and build passes, the next likely action is to commit and push it.

Recommended next commit message if still pending:
- `Add create advert from paid lead action`

Recommended next verification for that helper:
1. create or locate a test paid lead (`paid_pending_review` / `paid`),
2. open Admin → Advertising,
3. confirm **Create advert from lead** button appears,
4. click it,
5. confirm sponsored placement form is pre-filled,
6. edit title/message if needed,
7. create Desktop + mobile placement,
8. confirm two placements are created,
9. delete test placements,
10. clean test lead/transaction.

### 7. Known status-label issue / next refinement
Current statuses in use now include:
- `new`,
- `payment_pending`,
- `paid_pending_review`,
- `contacted`,
- `converted`,
- `declined`,
- `archived`.

The Admin status update endpoint previously allowed only:
- `new`, `contacted`, `converted`, `declined`, `archived`.

Recommended refinement:
- add `advert_live` or `published` status after sponsored placement creation,
- optionally auto-update paid lead to `advert_live` when “Create advert from lead” successfully publishes sponsored placement,
- avoid using `converted` ambiguously for both sale and live-advert state.

### 8. Updated live commercial capability after this block
Cheshire Today now has a launch-ready small-business advertising funnel:
- public `/advertise` packages,
- clear advert placement explanation,
- review-before-payment UX,
- direct Stripe Checkout test flow,
- enquiry-only path,
- pay-later email link,
- paid lead state tracking,
- Admin Advertising lead list,
- Admin status buttons,
- Admin sponsored placement creation/deletion,
- automatic 30-day expiry on Admin-created placements,
- impression and click tracking,
- payment success page,
- fallback advert CTAs when no paid advert is active.

No test sponsored placements should be active. All explicitly mentioned temporary test leads and transactions were deleted during the session.

### 9. Updated next priorities after April 26 payment/pay-later work
Recommended next order:
1. Continue from `git status --short` because the Admin create-from-paid-lead helper may be uncommitted.
2. If present, inspect and commit/push the AdminDashboard helper after verification.
3. Add a lead status such as `advert_live` / `published` after advert creation.
4. Test a paid-lead → create-advert-from-lead → live advert → delete test advert workflow.
5. Keep Stripe in test mode until ready for real customer payments.
6. Only switch Render `STRIPE_API_KEY` from `sk_test_...` to `sk_live_...` when ready for real payments.
7. Update the source-of-truth `.md` again after the Admin helper is committed/pushed and tested.
8. Then continue to homepage/category sponsored slots or newsletter sponsorship slots.

### 10. Updated continuation instruction for the next chat
Use this as the continuation instruction after the April 26 advertising payment/pay-later work:

`Continue Cheshire Today from PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260426_v11_FULL.md. Respect workflow: check current state first, no manual file edits, one command at a time, verify after each change. The project now has a live-tested advertising monetisation funnel: /advertise review-before-payment UX, Stripe test checkout using official stripe package, payment success page, paid leads marked paid_pending_review, enquiry-only path, client confirmation email with pay-later link, /advertise/pay token route, Admin Advertising lead management, sponsored placement creation/delete, automatic 30-day placement expiry, and sponsored impression/click tracking. Stripe is still in test mode via Render STRIPE_API_KEY=sk_test_...; do not switch to sk_live_... until ready for real customers. First action in the new chat: run git status --short. There may be an uncommitted local AdminDashboard.jsx helper that adds Create advert from lead for paid leads; inspect it, build, then commit/push if correct. Next target is to finish/test paid-lead processing so a paid_pending_review lead can pre-fill and publish a sponsored placement, then optionally add advert_live/published status.`

---

## April 26, 2026 — Advertising Lead Processing, Live Stripe Readiness & Webhook Verification Update

### 1. Completed after v11 handover
This update records the work completed after the earlier v11 handover. The repository itself was not edited for this documentation update; this update is only in the chat-source master file.

Completed and pushed on `full-scrape-prod`:
- `8e3b566` — `Add advert creation helper for paid leads`
- `916a7e7` — `Add admin delete action for advertiser leads`
- `ea90a9d` — `Send advertising payment confirmation email`
- `eda27b2` — `Email advertisers when sponsored advert goes live`
- `e802a7d` — `Use Stripe webhook signing secret verification`

Final checked repo state after the work:
- `git status --short` returned empty.
- Backend `/api/health` returned healthy.
- Live webhook signature enforcement returned the expected HTTP `400` with `Invalid Stripe webhook signature` for an unsigned request.

### 2. Admin Advertising workflow completed
The previously pending AdminDashboard helper was inspected, built, committed and pushed.

Admin Advertising now supports:
- **Create advert from lead** for paid/reviewable leads.
- Paid lead prefill into the sponsored placement form.
- Lead website normalisation to `https://...` where needed.
- Improved status labels:
  - `payment_pending` → `checkout started, not paid`
  - `paid_pending_review` → `paid — needs review`
- Scroll target on the sponsored placement form via `id="create-sponsored-placement"`.
- **Delete lead** for advertiser leads, backed by a protected admin backend delete route and a confirmation prompt.

### 3. Payment-confirmation email added
After Stripe confirms an advertising payment, the advertiser now receives a **Payment received — Cheshire Today advertising** email.

The email explains:
- payment has been received,
- the advert is paid and pending review,
- Cheshire Today reviews adverts before publication,
- the 30-day campaign starts after approval/publication, not at payment time,
- the client can reply with logo, image, wording or link changes.

Implementation notes:
- Added `send_advertising_payment_confirmation_email(lead_id)`.
- The helper is idempotent using lead fields such as `payment_confirmation_sent` and `payment_confirmation_sending`.
- It is called from both `/advertising/payment-status/{session_id}` and `/webhook/stripe`.
- The already-completed payment-status branch also calls the helper idempotently, so a confirmation can still be sent if the webhook processed payment first.

### 4. Advert-live email with exact advert-card links added
When Admin creates/publishes a sponsored placement from a paid lead, the advertiser now receives a **Your Cheshire Today advert is now live** email.

The live email includes exact preview links that:
- open a real Cheshire Today article page,
- force the advertiser’s advert to display,
- jump directly to the relevant advert card anchor.

Example link shapes:
- `https://cheshiretoday.co.uk/article/{article_id}/{slug}?sponsored_ad_placement=article_sidebar&sponsored_ad_campaign={campaign_id}#sponsored-advert-article_sidebar-{campaign_id}`
- `https://cheshiretoday.co.uk/article/{article_id}/{slug}?sponsored_ad_placement=article_mobile&sponsored_ad_campaign={campaign_id}#sponsored-advert-article_mobile-{campaign_id}`

Implementation notes:
- Sponsored placement docs now support `campaign_id`, `source_lead_id`, and `notify_client_on_publish`.
- Admin create-from-lead sends a shared campaign ID across desktop/mobile placements.
- Only the final placement in a Desktop + mobile creation request triggers the live email, avoiding duplicate sends.
- Public sponsored placement API now supports forced preview serving by `slug` or `campaign_id`.
- `SponsoredPlacement.jsx` now reads preview query parameters and adds stable anchor IDs to advert cards.
- Normal visitor advert rotation remains unchanged.
- The live email helper is idempotent using lead fields such as `advert_live_notification_sent`, `advert_live_notification_sending`, and `advert_live_notification_campaign_id`.

### 5. Live Stripe key and checkout readiness
Stripe live-money readiness was advanced.

Completed checks:
- Live Stripe secret key was created/rotated in Stripe.
- Render backend `STRIPE_API_KEY` was updated to the live `sk_live_...` key.
- Backend was manually redeployed.
- Backend health check passed.
- A live advertising checkout session was successfully created.
- The returned session ID began with `cs_live_...`, confirming live Stripe mode.
- User confirmed Stripe payout/bank details are present.

Important note:
- A live checkout session was created for testing, but the user chose to complete the real payment test later.
- Do not assume a live real payment was completed unless later verified in Stripe and Admin leads.

### 6. Stripe live webhook destination and signature verification
A live Stripe webhook/event destination was created.

Webhook destination settings:
- Endpoint URL: `https://cheshiretoday.co.uk/api/webhook/stripe`
- Event selected: `checkout.session.completed`
- Scope: Account events.

Backend changes:
- Added `STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '').strip()`.
- Replaced the legacy `emergentintegrations` webhook handling for `/webhook/stripe` with official Stripe SDK verification via `stripe.Webhook.construct_event(...)`.
- Invalid payloads return 400.
- Invalid signatures return 400.
- Missing `STRIPE_WEBHOOK_SECRET` returns 500.
- Successful `checkout.session.completed` events continue to update advertising leads and job payments as before.

Live verification completed:
- Render backend environment now includes `STRIPE_WEBHOOK_SECRET` with the live `whsec_...` signing secret.
- Backend was redeployed.
- Health check passed.
- Unsigned POST to `/api/webhook/stripe` returned HTTP `400` with `Invalid Stripe webhook signature`, confirming the secret is active and unsigned requests are rejected.

### 7. Current advertising monetisation state
Current full advertising funnel:
1. Client submits advertising enquiry.
2. Client receives review/payment-link email.
3. Client can complete Stripe Checkout.
4. Webhook/payment-status marks lead as paid pending review.
5. Client receives payment-confirmation email.
6. Admin sees paid lead in Adverts section.
7. Admin can click **Create advert from lead**.
8. Admin reviews/edits advert fields.
9. Admin creates Desktop + mobile sponsored placements.
10. Client receives advert-live email with exact advert-card preview links.
11. Admin can delete unwanted leads or sponsored placements.
12. Public advert slots show fallback when no paid advert is active.
13. Active sponsored placements rotate normally for visitors while preview links can force a specific advertiser’s card.

### 8. Controlled real-payment test still pending
Recommended live test sequence:
1. Create or use a live advertising checkout session.
2. Complete real payment with a card.
3. Confirm Stripe shows successful payment.
4. Confirm Stripe webhook delivery succeeded.
5. Confirm Admin lead moves to `paid_pending_review`.
6. Confirm payment-confirmation email is received.
7. In Admin → Adverts, click **Create advert from lead**.
8. Publish Desktop + mobile placement.
9. Confirm advert-live email is received.
10. Click both preview links and verify the forced desktop/mobile advert cards.
11. Refund the test payment in Stripe if appropriate.
12. Delete/clean test sponsored placements and test lead if not needed.

### 9. Recommended next priorities
Recommended next order:
1. Perform the controlled live payment test when ready.
2. Confirm Stripe webhook delivery after the payment.
3. Confirm payment-confirmation and advert-live email delivery.
4. Add or refine a final lead status such as `advert_live` / `published` after successful sponsored placement creation.
5. Consider adding Admin visible indicators for payment-confirmation email sent, advert-live email sent, and live preview link copied.
6. Consider adding a dedicated public advert preview route later; current forced article-card links are sufficient for launch.
7. Continue broader revenue work only after the first real advert payment/live-placement flow is verified end-to-end.

### 10. Updated continuation instruction for next chat
Use this continuation instruction for the next Cheshire Today chat:

`Continue Cheshire Today from PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260426_v11_FULL.md. Respect workflow: check current state first, no manual file edits in the repo, one command at a time, verify after each change. Since v11, the advertising funnel has been completed and deployed: Create advert from paid lead, delete advertiser leads, payment-confirmation email after Stripe payment, advert-live email with exact forced advert-card preview links, Stripe live key in Render, live checkout session creation confirmed with cs_live_..., live Stripe webhook destination created for checkout.session.completed, STRIPE_WEBHOOK_SECRET added to Render, and webhook signature verification confirmed by an unsigned request returning 400 Invalid Stripe webhook signature. Repo was clean after final check. The next major step is a controlled real payment test: complete a live advert payment, verify Stripe webhook delivery, verify lead becomes paid_pending_review, verify payment-confirmation email, create sponsored placement from lead, verify advert-live email links jump directly to the forced desktop/mobile advert cards, then refund/clean test data if needed. After that, consider adding an advert_live/published status and Admin email-status indicators.`


---

## 11. April 27–28, 2026 detailed update — search, manual-image hardening, CloudLearn, homepage adverts, affiliate rotation, reporting, and duplicate cleanup

This working block moved Cheshire Today materially forward on both monetisation execution and day-to-day editorial hygiene.

The session can be grouped into eight major outcomes:
1. fixed Admin article search so manually published stories can be found without repeatedly loading more pages,
2. fixed Daily Brief image/coverage issues,
3. hardened future manual article image handling so source URLs are preferred over Postimg,
4. added a new Awin affiliate (CloudLearn) as a live commercial guide,
5. extended the paid sponsored-placement system from article pages onto the homepage,
6. made affiliate exposure fairer via stable daily rotation across homepage and sidebar surfaces,
7. improved advertiser/admin visibility with better homepage preview links and stronger sponsored-placement reporting,
8. cleaned live duplicate articles out of production.

### 11.1 Admin article search fix — full database search instead of repeated “Load more” hunting

Problem observed:
- manually published articles were difficult to find in Admin,
- the existing search experience effectively depended on the first loaded page of results,
- user had to click **Load more articles** repeatedly to reach older or manually published content.

Diagnosis completed:
- inspected `frontend/src/components/AdminDashboard.jsx`,
- confirmed the frontend search box filtered only the currently loaded `articles` array,
- confirmed `/api/admin/articles` originally only returned paginated results by `skip`/`limit` with no full-database `search` parameter,
- verified the target article example by ID and URL.

Backend fix applied:
- `/api/admin/articles` was extended to accept optional `search`,
- search now matches across:
  - `title`,
  - `content`,
  - `source`,
  - `source_url`,
  - `category`,
  - `id`,
  - and Mongo `_id` when a 24-character object ID appears in the query.

Frontend fix applied:
- added a dedicated `fetchAdminArticlesPage()` helper,
- wired the search field to backend full-database search,
- debounced search execution,
- preserved working pagination and `Load more` behavior for searched result sets,
- removed the old local-title-only frontend search filter.

Verification completed:
- local backend API check against article object ID returned the correct manually added article,
- frontend build passed,
- commit saved/pushed/deployed.

Relevant commit:
- `d22407d` — `Fix admin article search across full database`

Operational result:
- Admin article search can now find manually published stories by title text, article ID, source URL fragments, or direct object-ID values without repeated paging.

### 11.2 Daily Brief newsletter fixes — blocked image hosts and thin-content fallback

Problems observed:
1. Daily Brief hero images were not rendering correctly when the chosen hero used Postimg/Postimage-hosted assets.
2. If a manual article was the only recent story eligible at send time, the Daily Brief could become too thin and feel like a one-story newsletter instead of a fuller digest.

Diagnosis completed:
- inspected `backend/app/email_service.py`,
- confirmed hero image rendering relied on `hero.get('image')`,
- identified that manual articles using `i.postimg.cc` were especially problematic for email rendering,
- inspected the Daily Brief article-selection logic in `backend/server.py`.

Fixes applied:
- added `_safe_email_image_url()` to block problematic email image hosts:
  - `postimg.cc`,
  - `i.postimg.cc`,
  - `postimage.org`,
  - `postimages.org`.
- Daily Brief hero image rendering now suppresses blocked hosts instead of trying to display them.
- Daily Brief article selection now tops up from the latest unique articles if the recent article pool is too thin, instead of only falling back when zero articles are available.

Verification completed:
- code diff reviewed locally,
- commit saved/pushed/deployed.

Relevant commit:
- `e6854bc` — `Fix Daily Brief image host and thin-content fallback`

Operational result:
- Daily Brief no longer attempts to render blocked Postimg-style hero images,
- newsletter coverage is more resilient when recent article count is thin,
- manual article presence no longer causes the digest to collapse into a near-single-story email.

### 11.3 Manual article image hardening — prefer source page OG image over Postimg for future manual content

Problem observed:
- many manual PR / council / announcement articles were being published using Postimg image URLs,
- these links were bad for newsletter rendering and social/open behavior,
- future manual entry needed to prefer official source-page images when `source_url` was available.

Implementation applied in backend:
- added `resolve_manual_article_image(image_url, source_url)` in `backend/server.py`,
- logic now:
  - accepts the manually supplied image if it is already a safe non-Postimg asset,
  - if image is blank or blocked and `source_url` exists, fetches the source page,
  - extracts `og:image`,
  - uses that official image when valid,
  - otherwise returns empty string instead of persisting a blocked Postimg URL.
- applied to both:
  - `POST /admin/articles`,
  - `PUT /admin/articles/{article_id}`.

Verification completed:
- backend syntax check passed,
- diff reviewed,
- commit saved/pushed/deployed.

Relevant commit:
- `b2bcff7` — `Auto-use source images for manual articles`

Operational result:
- future manual articles with a reliable `source_url` will automatically prefer source-page imagery rather than Postimg,
- this reduces newsletter/social image failure risk for future manually added content.

### 11.4 Existing live manual-image clean-up completed during this block

Additional data-level clean-up completed for already-published manual stories:
- investigated existing live Postimg-backed manual articles,
- identified several Wilmslow Town Council / manual-entry records with better official source images available,
- manually updated existing article image fields in Mongo where reliable source assets were found.

Confirmed/fixed during session:
- **Wilmslow Businesses Offered FREE Cycle Parking in New Council Scheme** — source image resolved from Wilmslow Town Council page and DB updated,
- **New ‘Edible Hedgerow’ Project Launched on Browns Lane in Wilmslow** — source image resolved and DB updated,
- **Free Multisports Sessions Return to Wilmslow for Summer 2026** — source image resolved and DB updated,
- **Work Begins on Grove Street Improvements in Wilmslow as £80,000 Project Gets Underway** — source image resolved and DB updated.

Remaining legacy Postimg-backed manual articles were intentionally left unchanged when no strong replacement source was immediately available.

Operational result:
- several already-live manual stories now use proper source-hosted images,
- future manual stories are protected by the new source-image resolver.

### 11.5 New Awin affiliate added — CloudLearn

New affiliate joined and integrated during this block:
- advertiser: **CloudLearn**,
- Awin advertiser ID: `78364`.

Commercial work completed:
- reviewed Awin creative list,
- started from the default CloudLearn creative,
- then created a better Awin deeplink using Link Builder to the GCSE courses landing page,
- final deeplink stored in the guide:
  - `https://www.awin1.com/cread.php?awinmid=78364&awinaffid=2844510&clickref=cloudlearn_gcse_alevel_guide&ued=https%3A%2F%2Fcloudlearn.co.uk%2Fcourses%2Fonline-gcse-courses`

New authority/commercial guide created directly in Mongo:
- slug: `best-online-gcse-a-level-courses-uk`,
- title: `Best online GCSE and A-Level courses in the UK (2026): flexible study, adult learners and recognised qualifications`,
- status: `published`,
- category: `Business`,
- monetisation type: affiliate,
- primary tool: **CloudLearn**.

Frontend guide-layer work completed:
- downloaded/added CloudLearn favicon asset to `frontend/public/affiliate-logos/cloudlearn.ico`,
- added CloudLearn logo mapping in `AuthorityPage.jsx`,
- added the GCSE/A-Level guide into the related-guide library/rotation.

Verification completed:
- guide appeared in live authority-pages API,
- frontend build passed,
- changes were committed/pushed/deployed.

Relevant commit:
- `c2ce9a1` — `Add CloudLearn affiliate guide assets`

Operational result:
- CloudLearn is now a live monetised guide in Cheshire Today’s commercial layer,
- the guide uses a proper Awin deeplink rather than only a generic creative link.

### 11.6 Homepage sponsored-placement system added and tested

Strategic gap addressed:
- article-page sponsored placements already existed,
- homepage sponsored inventory had not yet been implemented,
- competitors’ monetisation breadth analysis reinforced the need to sell more than article-page advert cards alone. This aligns with the strategy emphasis on commercial pages and diversified monetisation, while staying within the no-redesign constraint. fileciteturn110file0 fileciteturn110file1

Frontend/Admin changes applied:
- extended Admin sponsored-placement selector from article-only options to include homepage options,
- new placement options now include:
  - `article_both`,
  - `homepage_both`,
  - `article_sidebar`,
  - `article_mobile`,
  - `homepage_sidebar`,
  - `homepage_mobile`.
- extended placement grouping logic so `homepage_both` creates both homepage desktop and homepage mobile placements.

Homepage rendering changes applied:
- imported and used `SponsoredPlacement` in `HomePageV1.jsx`,
- desktop homepage sponsored card placed **under Top stories** in the right column,
- mobile homepage sponsored card placed in the mobile view.

Local testing and UX/layout correction completed:
- created temporary preview campaign `homepage-preview-test` in Mongo for local testing,
- confirmed initial desktop placement created layout issues / white gap,
- iterated layout until correct result was achieved,
- final homepage layout changes included:
  - moving the affiliate strip into the left hero column,
  - reducing the upper affiliate strip from 3 to 2 cards,
  - removing the standalone full-width top strip,
  - making Top Stories full-height behavior desktop-only,
  - keeping sponsored card under Top Stories on desktop.
- temporary preview ads were then deleted from Mongo so no test sponsor remained on live.

Verification completed:
- local desktop and mobile homepage previews tested successfully,
- frontend build passed,
- commit saved/pushed/deployed,
- temporary preview campaign was explicitly removed afterwards (`deleted = 2`).

Relevant commit:
- `b54f4eb` — `Add homepage sponsored placement slots`

Operational result:
- Cheshire Today now has live homepage sponsored inventory on both desktop and mobile,
- Admin can create homepage advert campaigns directly,
- homepage can now carry paid sponsor cards in addition to article-page placements.

### 11.7 Affiliate fair-share rotation added across homepage and sidebar

Problem observed:
- homepage affiliate exposure was not fair,
- homepage strips were static,
- second homepage strip used `start={3}`, which skipped one slot in the pool,
- sidebar affiliate widgets used random-per-refresh behavior rather than stable fair-share exposure,
- CloudLearn was not yet part of the homepage affiliate pool.

Changes applied:

#### A. Homepage strip fairness
- added stable **daily rotation** logic to `HeroMonetisationStrip.jsx`,
- homepage strip cards now rotate by day instead of per-refresh randomization,
- fixed the skipped-slot issue by changing second strip from `start={3}` to `start={2}`.

#### B. Sidebar affiliate fairness
- replaced random-per-refresh selection in `AffiliateWidgets.jsx` with stable daily rotation for:
  - fallback/sample products,
  - DB-backed products.
- both homepage sidebar and article sidebar affiliate product widgets now use stable daily fair-share logic.

#### C. CloudLearn exposure
- added CloudLearn into `frontend/src/config/monetisationTools.js` homepage primary affiliate pool.

Verification completed:
- local preview confirmed rotation behavior is stable on refresh for the same day,
- CloudLearn confirmed visible in homepage rotation pool,
- build passed,
- commit saved/pushed/deployed.

Relevant commit:
- `01eadc7` — `Rotate affiliate exposure across homepage and sidebar`

Operational result:
- affiliate exposure is now materially fairer,
- homepage and sidebar affiliate placements rotate stably by day,
- CloudLearn is included in homepage affiliate exposure.

### 11.8 Homepage advert live-email preview links fixed

Problem observed:
- advertiser live-notification preview links were still article-page oriented,
- homepage placements would not generate the correct preview destination/labeling.

Backend fix applied in `send_sponsored_advert_live_email()`:
- split preview base handling into:
  - article preview base URL,
  - homepage preview base URL.
- homepage placements (`homepage_sidebar`, `homepage_mobile`) now generate homepage preview links,
- article placements still generate article-page preview links,
- updated slot labels to distinguish:
  - Desktop homepage advert,
  - Mobile homepage advert,
  - Desktop sidebar advert,
  - Mobile in-article advert.
- updated email copy so it no longer claims only article-page previews exist.

Verification completed:
- backend syntax check passed,
- diff reviewed,
- commit saved/pushed/deployed.

Relevant commit:
- `404381a` — `Support homepage advert preview links in live emails`

Operational result:
- advertiser live emails can now correctly preview homepage campaigns as well as article-page campaigns.

### 11.9 Sponsored-placement Admin reporting improved

Problem observed:
- sponsored placement cards in Admin were functional but too sparse for campaign management,
- package/slot performance was harder to read quickly.

Frontend Admin improvements applied:
- placement labels made human-readable:
  - Homepage desktop,
  - Homepage mobile,
  - Article desktop,
  - Article mobile.
- performance metrics now shown in cleaner cards:
  - impressions,
  - clicks,
  - CTR,
  - campaign ID.
- dates clarified:
  - starts,
  - expires.
- retained rotation diagnostics:
  - weight,
  - priority.

Verification completed:
- frontend build passed,
- diff reviewed,
- commit saved/pushed/deployed.

Relevant commit:
- `e6f9a07` — `Enhance sponsored placement admin reporting`

Operational result:
- Admin Advertising now gives materially better visibility into advert slot type, campaign identity, timing, and performance.

### 11.10 Competitor-monetisation interpretation completed and backlog extended

During this block, competitor monetisation models were reviewed again against Cheshire Today’s current system. The key conclusion was:
- Cheshire Today’s advert system is cleaner and more controlled than competitors’ cluttered models,
- but competitors are ahead in monetisation breadth through event listings, directories, jobs, newsletter sponsorship, sponsored content packages, and advertiser product layers. This interpretation is consistent with the competitor analysis report’s recommendation to use event/directory pages, business and finance coverage, and niche content to grow monetisation breadth. fileciteturn110file1

As a result, the post-current-phase backlog was expanded to include:
- event listings,
- business directory,
- job listings,
- newsletter sponsorship,
- sponsored spotlight / business spotlight packages,
- clearer media-kit/package sales layer,
- category-level sponsorship options,
- advertiser-facing campaign reporting.

### 11.11 Live duplicate article cleanup completed

Problem observed:
- user identified duplicate live articles on production.

Diagnostics completed:
- checked live API using `/api/articles?limit=200&with_total=1`,
- found:
  - `LIVE_ARTICLES = 198`,
  - `DUPLICATE_TITLE_GROUPS = 4`.

Affected duplicate title groups were:
- `Oil prices rise as US-Iran peace talks stall` (3 live copies),
- `'There's so much I want to give my daughter - poverty means I can't'` (2 live copies),
- `Doomjobbing: how the modern job hunt became a vicious loop` (2 live copies),
- `Which airlines are cancelling flights to the UK - and what can you do?` (2 live copies).

DB inspection confirmed:
- all were feed/import duplicates rather than intentional pinned/manual content,
- safe action was to keep the newest live copy in each group and archive the older copies.

Cleanup applied:
- archived 5 older duplicate documents in Mongo,
- used:
  - `archived = True`,
  - `archive_reason = manual_duplicate_cleanup`,
  - `archived_at` / `updated_at` timestamps.

Verification completed:
- after cleanup:
  - `LIVE_ARTICLES = 193`,
  - `DUPLICATE_TITLE_GROUPS = 0`.

Operational result:
- production live feed no longer contains duplicate titles from those groups,
- manual cleanup reason is now recorded for auditability.

### 11.12 Consolidated commit/deploy ledger for this working block

Commits completed in this chat/work block:
- `d22407d` — `Fix admin article search across full database`
- `e6854bc` — `Fix Daily Brief image host and thin-content fallback`
- `b2bcff7` — `Auto-use source images for manual articles`
- `c2ce9a1` — `Add CloudLearn affiliate guide assets`
- `b54f4eb` — `Add homepage sponsored placement slots`
- `01eadc7` — `Rotate affiliate exposure across homepage and sidebar`
- `404381a` — `Support homepage advert preview links in live emails`
- `e6f9a07` — `Enhance sponsored placement admin reporting`

Deploy status during this block:
- relevant frontend changes were pushed and deployed after verification,
- relevant backend changes were pushed and deployed after verification,
- user explicitly confirmed successful deploys during the session.

### 11.13 Current live monetisation capability after this block

Cheshire Today now has a materially stronger monetisation stack than at the start of this working day:

#### Affiliate/commercial layer
- CloudLearn live as a new Awin-backed commercial guide,
- homepage affiliate pool expanded,
- fairer daily affiliate rotation across homepage and sidebar,
- manual article source-image hardening improves newsletter/social reliability for monetised manual content.

#### Paid sponsor layer
- homepage desktop + mobile sponsored placements live,
- article desktop + mobile sponsored placements live,
- Admin can create either article or homepage slot combinations,
- advertiser live emails can preview homepage or article slots correctly,
- Admin sponsored-placement reporting is clearer and more commercially usable.

#### Editorial hygiene / workflow layer
- Admin article search is faster and more reliable for manual publishing operations,
- Daily Brief is more robust,
- manual image handling is safer,
- duplicate live stories were cleaned out of production.

### 11.14 Remaining next priorities after this block

Recommended next order:
1. Create the **first real homepage sponsor campaign** in Admin using `homepage_both` so the new homepage ad inventory starts generating revenue.
2. Run a full paid-sponsor workflow test for a homepage campaign, including advertiser preview link and impression/click tracking.
3. Add a lead state such as `advert_live` / `published` if still not implemented, so sales pipeline stages are clearer after an advert is actually live.
4. Continue building advertiser-facing campaign reporting beyond Admin-only visibility.
5. After current advertising/affiliate phase is truly stable, move to the post-phase backlog:
   - event listings,
   - business directory,
   - jobs monetisation,
   - newsletter sponsorship,
   - sponsored spotlight packages,
   - media-kit / category sponsorship layer.
6. Keep checking live article quality and duplicate hygiene after each import cycle.

### 11.15 Updated continuation instruction for the next chat

Use this as the continuation instruction after the April 27–28 monetisation and duplicate-cleanup work:

`Continue Cheshire Today from PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260428_v12_FULL.md. Respect workflow: check current state first, no manual file edits, one command at a time, verify after each change. The project now has: full-database Admin article search; Daily Brief image-host blocking and thin-content fallback; future manual article source-image preference over Postimg; several existing manual article image fixes; CloudLearn added as a live Awin-backed guide; homepage sponsored placements on desktop and mobile; stable daily affiliate rotation across homepage and sidebar; homepage advert preview links in advertiser live emails; improved sponsored-placement admin reporting; and manual duplicate cleanup that resolved 4 duplicate live title groups (5 older copies archived with archive_reason=manual_duplicate_cleanup). Current highest-value next step is to create the first real homepage sponsor campaign in Admin using homepage_both, then test preview links, impression/click tracking, and sponsor visibility end-to-end.`

---

## 12. April 28, 2026 — Chat-source reconciliation after checking duplicated v11 file

This append was added after explicitly comparing all uploaded/readable project-state markdown files in the chat source area:

- `PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260426_v11_FULL.md`
- `PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260426_v11_FULL 2.md`
- `PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260428_v12_FULL.md`

### 12.1 Reconciliation result

The original v11 file is fully contained inside this v12 file.

The duplicated v11 file (`PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260426_v11_FULL 2.md`) contained an extra append-only update block after the original v11 content. Most of its operational substance was already covered in this v12 file under the detailed April 27–28 update, especially:

- merchant-link / affiliate enrichment context,
- duplicate live-article cleanup,
- production verification showing `LIVE_ARTICLES = 193`,
- production verification showing `DUPLICATE_TITLE_GROUPS = 0`,
- archive-first duplicate cleanup principle,
- controlled advertising/payment verification still being a core next-phase concern unless later superseded,
- broader monetisation backlog items.

However, the duplicated v11 file preserved an important documentation-handling rule that needed to be carried forward explicitly in v12. This section records that rule so it is not lost.

### 12.2 Documentation preservation rule carried forward from duplicated v11

The project state file must be treated as append-only.

Rules now reaffirmed:

- Do not delete older project-state details.
- Do not compress older sections into shorter summaries.
- Do not rewrite history just because a later update supersedes an earlier one.
- If a previous section becomes outdated, add a new dated note explaining the supersession instead of removing the older record.
- Do not create a renamed `v13`, `v14`, or other new master version unless the current file is too large to append safely.
- If the file does become too large, start a new continuation file that clearly states it continues from `PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260428_v12_FULL.md` and preserves all earlier details by reference.
- For now, continue appending to this v12 file when documenting major end-of-day/project-day updates.

Reason for this rule:

- Previous source-file updates risked losing useful operational detail.
- The project depends heavily on the master state file for continuity across new chats.
- Losing older details creates risk for technical work, Stripe/payment work, advertising work, article cleanup, affiliate-guide work, import behaviour, newsletter logic, and deployment safety.

### 12.3 Duplicate-cleanup detail retained from duplicated v11

The duplicated v11 file recorded the following article-cleanup facts, which are preserved here for continuity:

- a cleanup operation archived 5 duplicate/extra live records,
- one valid live article was preserved for each affected duplicated title,
- the cleanup goal was not to remove all copies of valid stories, but to ensure exactly one live copy remained per duplicated title,
- final verification showed:
  - `LIVE_ARTICLES = 193`,
  - `DUPLICATE_TITLE_GROUPS = 0`.

Example affected titles recorded in the duplicated v11 file included:

- `Oil prices rise as US-Iran peace talks stall`,
- `'There's so much I want to give my daughter - poverty means I can't'`,
- `Doomjobbing: how the modern job hunt became a vicious loop`.

The fuller v12 section also records the fourth duplicate group:

- `Which airlines are cancelling flights to the UK - and what can you do?`.

### 12.4 Archive safety principle reaffirmed

For future article cleanup work:

- prefer archive-based fixes rather than destructive hard deletion,
- preserve one valid live article per duplicated title,
- set clear archive metadata such as `archive_reason` when manually cleaning records,
- do not resurrect manually archived records,
- do not allow cap/visibility jobs to overwrite manual archive decisions,
- after any cleanup, verify live count, duplicate-title count, and affected titles.

Recommended verification pattern after cleanup:

1. Check live article count.
2. Check duplicate live-title groups.
3. Spot-check affected titles to confirm exactly one live article remains.
4. Confirm homepage/category APIs still return healthy results.

### 12.5 Current continuation priority after reconciliation

After reconciling the duplicated v11 file with v12, the current practical priority remains unchanged from the latest v12 continuation instruction:

1. create the first real homepage sponsor campaign in Admin using `homepage_both`,
2. test homepage desktop and mobile preview links,
3. verify sponsor visibility on live homepage surfaces,
4. verify impression tracking,
5. verify click tracking,
6. verify Admin/reporting visibility end-to-end,
7. then decide whether advertiser lead status/reporting labels need another refinement such as `advert_live` / `published` or additional email-status indicators.

### 12.6 Updated continuation instruction after reconciliation

Use this continuation instruction for the next Cheshire Today chat:

`Continue Cheshire Today from PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260428_v12_FULL.md as the latest readable state. The v12 file has now been reconciled against both v11 markdown files, including the duplicated v11 copy. Treat the project state file as append-only: do not delete, compress, rewrite, or remove older details. Do not create another renamed master version unless the current file is too large to append safely. Respect workflow: check current state first, no manual repo edits, one command at a time, verify after each change, run commands from repo root, and use grep rather than rg. Current next priority: create the first real homepage sponsor campaign in Admin using homepage_both, then test preview links, sponsor visibility, impression/click tracking, and reporting end-to-end.`

---

## 13. April 28–29, 2026 — Homepage desktop layout, sponsor-slot visibility, house advert, and Admin advert editing

This append records the completed homepage layout and sponsored-placement work carried out after the v12 reconciliation section. The state file remains append-only; no previous sections were removed or rewritten.

### 13.1 High-level result

The homepage desktop layout phase is now complete and confirmed live. The homepage now has:

- a wider desktop content wrapper,
- a stronger two-column desktop homepage layout,
- the sponsor card moved into a more visible homepage sidebar position,
- refined Top Stories card sizing,
- tighter hero/newsletter/affiliate/latest spacing,
- a structural fix for the left-side gap under affiliate cards when the advert card is tall,
- sticky right-sidebar behaviour matching the article-page pattern,
- an active temporary Cheshire Today house advert on homepage desktop and mobile,
- Admin support for editing sponsored placements after creation.

This work stayed within the project rule of preserving the existing site design while making necessary structural and monetisation improvements.

### 13.2 Homepage layout changes completed

The desktop wrapper was widened from the previous narrower container to a wider desktop layout:

- `frontend/src/components/homepage/HomepageLayout.jsx`
- wrapper changed to `mx-auto w-full px-4 max-w-[1320px]` after the earlier `container mx-auto` wrapper did not fully force the desired live desktop width.

The homepage hero/top-stories layout was then refined in `frontend/src/pages/HomePageV1.jsx`:

- hero/content column and right column were rebalanced,
- Top Stories was kept in the right column,
- sponsor placement was moved above Top Stories to make the monetisation slot visible earlier on desktop,
- the mobile sponsored slot remained separate via `homepage_mobile`,
- hero spacing was tightened by reducing the newsletter and affiliate strip margins from `mt-4` to `mt-3`,
- the Latest area was pulled closer to the hero/affiliate block during the first spacing pass.

Relevant commits from this phase:

- `466ef3a` — `Improve desktop homepage layout and sponsor slot visibility`
- `69dd951` — `Force widened homepage wrapper on desktop`
- `2025c47` — `Refine desktop top stories card layout`
- `cd5a53c` — `Tighten homepage hero section spacing`

### 13.3 Top Stories card refinement

`frontend/src/components/homepage/TopStoriesGrid.jsx` was adjusted so Top Stories cards better fill the right column:

- card gap increased from `gap-3` to `gap-4`,
- card padding reduced from `p-5` to `p-4`,
- card min-height increased to `min-h-[156px]`,
- thumbnail size increased to `h-28 w-36`,
- headline size set to `text-[15px]`,
- the live Top Stories wrapper had `lg:h-full` removed so the border no longer stretched too tall beyond its content.

This made the Top Stories block look fuller without leaving a large empty border column.

### 13.4 Sponsor card positioning and fallback-card improvements

`frontend/src/components/SponsoredPlacement.jsx` was adjusted during the homepage sponsor-card work:

- fallback homepage sponsor card was made taller and more substantial on desktop,
- fallback-only homepage extras were added:
  - `Homepage visibility`,
  - `Local Cheshire audience`,
  - `Fast setup and approval`,
- this made the fallback card look more intentional before a paid/house advert is active.

After the real house advert became active, the paid sponsored version replaced the fallback in the homepage sponsor slot.

### 13.5 Structural homepage gap fix

A more important structural issue was discovered after the paid sponsor card loaded with a tall/square image. The previous homepage layout used two stacked grids:

- first grid: hero/newsletter/affiliate cards on the left and sponsor/Top Stories on the right,
- second grid: Latest and other feed sections on the left with sidebar widgets on the right.

That caused a large visual gap under the affiliate cards when the sponsor image made the right column taller. Attempts to constrain homepage sponsor images were tested but rejected as the long-term fix because real advertisers may provide square logos, tall artwork, or landscape banners.

The final structural fix changed the homepage into one desktop grid:

Left column:

- hero,
- Daily Brief / subscribe block,
- affiliate cards,
- Latest,
- Business & Finance,
- More stories.

Right column:

- homepage sponsor placement,
- Top Stories,
- Business widget,
- AI & Tech widget,
- Finance widget,
- affiliate/sidebar widgets.

Result:

- Latest now starts directly under the affiliate cards,
- the advert card can be tall/flexible without creating a left-side gap,
- the right column remains independent of the left content flow.

Relevant commit:

- `175d100` — `Fix homepage sponsor layout gap and sticky sidebar`

### 13.6 Sticky sidebar fix

The right column initially did not stick after the structural rewrite. The reason was the parent grid/sidebar classes were preventing the sticky wrapper from having enough parent height to work correctly.

Final fix in `frontend/src/pages/HomePageV1.jsx`:

- removed `items-start` from the main homepage grid wrapper,
- removed `self-start` from the outer live homepage sidebar aside,
- aligned the live homepage sticky wrapper with the article-page sticky pattern:
  - `space-y-6 md:space-y-8 lg:sticky lg:top-24 self-start`,
- kept `space-y-3 [overflow-anchor:none]` on the live homepage sidebar aside, mirroring `ArticlePageV2.jsx`.

This made the right column stick correctly once left-column content is long enough, and release naturally near the end of the page.

### 13.7 Homepage house advert created and tested

A temporary Cheshire Today house advert was created to occupy the homepage sponsor slots until real paid advertisers are available.

Active placements:

- `homepage_sidebar` — desktop homepage sponsor slot,
- `homepage_mobile` — mobile homepage sponsor slot.

Current final advert content:

- sponsor/business: `Cheshire Today`,
- title: `Promote your business on Cheshire Today`,
- description: `Get your business in front of local Cheshire readers across news, business and finance coverage. Homepage advertising packages start from £49/month.`,
- target URL: `https://cheshiretoday.co.uk/advertise`,
- image URL: `https://cheshiretoday.co.uk/logo.png`,
- CTA: `Advertise with us`,
- package tier: `Local Starter`,
- rotation weight: `1`,
- priority: `10`,
- active: `true`,
- campaign ID: `cheshire-today-1777403120734`,
- expiry: `2026-05-28T19:05:20.734Z`.

Public API verification confirmed the placements are active and visible on:

- homepage desktop,
- homepage mobile.

Article advert slots were deliberately left inactive for now:

- `article_sidebar` — not active,
- `article_mobile` — not active.

Article-page house adverts should be considered later, but were intentionally not activated in this phase.

### 13.8 Impression and click tracking verified

The homepage sponsor system was tested end-to-end.

Desktop homepage test confirmed:

- sponsor card visibility passed,
- image rendering passed,
- click target to `/advertise` passed,
- impression counter updated,
- click counter updated.

Mobile homepage test confirmed:

- mobile sponsor placement visibility passed,
- impression counter updated,
- click counter updated.

Example verified counters during testing:

- desktop placement reached at least `impression_count: 27`, `click_count: 1`,
- mobile placement reached at least `impression_count: 27`, `click_count: 1`.

The exact counts will continue increasing as the homepage is viewed.

### 13.9 Sponsor image experiments and final decision

Several sponsor image approaches were tested:

1. plain `logo.png`,
2. cropped/generated `sponsor-test-cheshire-today.jpg`,
3. versioned `sponsor-house-cheshire-today-v2.jpg` with text in the image,
4. return to `logo.png` with improved card text.

The generated banner with text inside the image was rejected because it duplicated the card title/description and made the advert feel crowded/cropped in the real sponsor card.

Final decision:

- keep the sponsor image simple and use `https://cheshiretoday.co.uk/logo.png`,
- keep sales copy in the card text rather than embedded in the image,
- allow real advertiser creatives later, but avoid forcing all images into a fixed short-height format.

The unused generated sponsor images were removed from the repo.

Relevant commits:

- `ffaabba` — `Constrain homepage sponsor image height` (later effectively superseded by the structural layout fix and image revert),
- `374783c` — `Improve Cheshire Today house advert image` (superseded),
- `66d4810` — `Add versioned Cheshire Today house advert image` (superseded),
- `ac7738e` — `Remove unused sponsor test images`.

### 13.10 Admin sponsored-placement edit support added

Admin could previously create/delete sponsored placements but could not edit them after creation. This became a practical issue when adjusting the house advert image/copy.

`frontend/src/components/AdminDashboard.jsx` now supports sponsored-placement editing:

- added `editingSponsoredPlacementSlug` state,
- added edit-mode save logic so existing `slug` is updated instead of creating a duplicate,
- added `editSponsoredPlacement(placement)` helper,
- added `cancelSponsoredPlacementEdit()` helper,
- Admin form heading now switches between:
  - `Create Sponsored Placement`,
  - `Edit Sponsored Placement`,
- form copy explains when an existing advert is being edited,
- submit button switches between:
  - `Create sponsored placement`,
  - `Save advert changes`,
- `Cancel edit` button is available in edit mode,
- Live Sponsored Placements list now includes an `Edit advert` button beside `Delete advert`.

Build verification passed after fixing one temporary literal `\n` insertion error.

Relevant commit:

- `27f2df3` — `Add admin edit support for sponsored placements`.

### 13.11 Current Git / deployment state after this phase

Relevant pushed commits in order:

- `466ef3a` — `Improve desktop homepage layout and sponsor slot visibility`,
- `69dd951` — `Force widened homepage wrapper on desktop`,
- `2025c47` — `Refine desktop top stories card layout`,
- `cd5a53c` — `Tighten homepage hero section spacing`,
- `ffaabba` — `Constrain homepage sponsor image height`,
- `175d100` — `Fix homepage sponsor layout gap and sticky sidebar`,
- `27f2df3` — `Add admin edit support for sponsored placements`,
- `374783c` — `Improve Cheshire Today house advert image`,
- `66d4810` — `Add versioned Cheshire Today house advert image`,
- `ac7738e` — `Remove unused sponsor test images`.

Final live-confirmed state after deploy:

- live homepage layout confirmed correct,
- cache-bypass URLs used during verification,
- Admin `Edit advert` confirmed visible,
- homepage desktop and mobile house adverts confirmed active,
- unused sponsor test images removed,
- current remote HEAD after this cleanup: `ac7738e Remove unused sponsor test images`.

### 13.12 Current immediate project state

Completed:

- homepage layout gap fixed,
- right sidebar sticky behaviour fixed,
- homepage house advert active on desktop + mobile,
- Admin advert edit support added,
- sponsor image experiments cleaned up,
- live deployment confirmed.

Still intentionally deferred:

- article-page house advert slots (`article_sidebar`, `article_mobile`),
- advertiser-facing campaign reporting/export improvements,
- advertiser lead status refinement such as `advert_live` / `published`,
- deeper Advertise page sales-copy/package refinement,
- event listings / business directory / jobs monetisation / newsletter sponsorship / sponsored spotlight packages.

### 13.13 Recommended next steps

Suggested next work order:

1. Leave the homepage house advert active while waiting for real advertisers.
2. Use Admin `Edit advert` for future copy/image changes instead of curl where practical.
3. Later create article-page house advert slots if desired, using `article_both` or individual `article_sidebar` / `article_mobile` placements.
4. Improve the Advertise page sales copy and package explanation so clicks from the house advert convert better.
5. Add a simple advertiser-facing reporting/export view for impressions, clicks, CTR, placement, campaign, start date and expiry.
6. Consider adding clearer advertiser lifecycle statuses such as `lead`, `paid`, `advert_live`, `expired`, and `renewal_due`.
7. Continue monitoring homepage layout after real advertiser images are added, especially with square logos and tall creatives.

### 13.14 Updated continuation instruction after homepage sponsor/layout phase

Use this continuation instruction for the next Cheshire Today chat:

`Continue Cheshire Today from PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260428_v12_FULL.md. Treat this file as append-only and do not delete, compress, rewrite, or remove older sections. Respect workflow: check current state first, no manual repo edits, one terminal command at a time, verify after each change, run commands from repo root, and use grep rather than rg. The homepage layout phase is complete: desktop wrapper widened, sponsor slot moved above Top Stories, Top Stories cards refined, hero spacing tightened, homepage converted into one desktop grid to remove the affiliate-card gap, and the right sidebar now sticks like the article-page sidebar. A temporary Cheshire Today house advert is active on homepage desktop and mobile only, using logo.png, improved advert copy, CTA “Advertise with us”, and target /advertise. Article advert slots are intentionally inactive for now. Admin now supports editing sponsored placements via an Edit advert button. Next highest-value work: improve the Advertise page conversion copy/packages, add advertiser-facing reporting/export, or later create article-page house advert slots if wanted.`

### 13.15 Final confirmation added after user review

User reminder: project state updates for this working phase should be written only into the chat-source state file, not a new repo source-of-truth file unless explicitly requested.

Final confirmed state from the latest review:

- live homepage looked correct after the layout/sticky/sidebar changes,
- the temporary Cheshire Today house advert was confirmed acceptable after reverting from the generated banner image back to `https://cheshiretoday.co.uk/logo.png`,
- the house advert remains active only on homepage desktop and homepage mobile,
- article advert slots remain intentionally inactive for later,
- Admin sponsored-placement edit support has been added and pushed,
- unused generated sponsor image files were removed and pushed,
- current active house advert copy remains:
  - title: `Promote your business on Cheshire Today`,
  - description: `Get your business in front of local Cheshire readers across news, business and finance coverage. Homepage advertising packages start from £49/month.`,
  - CTA: `Advertise with us`,
  - image URL: `https://cheshiretoday.co.uk/logo.png`,
  - target URL: `https://cheshiretoday.co.uk/advertise`.

This section was appended to make clear that the final live/user-reviewed state was captured after the image experiment, cleanup, and deploy confirmation.


---

## 14. April 30, 2026 — End-of-day update: advertising funnel hardening and Commercial Gap Map implementation

This append records the completed April 30 work after the April 28 v12 baseline and the later Advertise-page alignment notes. It is append-only and supersedes earlier “next step” notes only where explicitly stated below.

### 14.1 Operating mode used

The established workflow was maintained:
- checked current state before changes,
- used terminal/scripted edits rather than manual file editing,
- used one command at a time where practical,
- used `grep` rather than `rg`,
- verified after each change,
- built frontend with `REACT_APP_BACKEND_URL=https://cheshiretoday.co.uk npm --prefix frontend run build`,
- avoided `npm start`,
- when using Termius/mobile, killed old `npm` / `npx` / `serve` processes before starting a new local server.

A temporary GitHub authentication issue briefly blocked push, but the branch was later confirmed clean/ahead and queued commits were pushed.

### 14.2 Homepage sponsor/house advert cleanup

A Cheshire Today internal house advert image was generated and tested for the homepage sponsor placement. Versioned JPG variants were visually reviewed, but the final conclusion was that they looked worse than the existing logo treatment.

Actions completed:
- generated and locally served `frontend/public/sponsor-test-cheshire-today.jpg`,
- created a versioned copy `frontend/public/sponsor-house-cheshire-today-v2.jpg`,
- tested both desktop/mobile homepage placements against the new image URL,
- reverted live sponsored placements back to `https://cheshiretoday.co.uk/logo.png`,
- removed unused JPG test assets from the repo.

Relevant commits:
- `374783c` — `Improve Cheshire Today house advert image`
- `66d4810` — `Add versioned Cheshire Today house advert image`
- `ac7738e` — `Remove unused sponsor test images`

Current state:
- homepage house advert remains active on desktop and mobile,
- it uses the existing Cheshire Today logo asset,
- temporary test sponsor images are not retained.

### 14.3 Advertise page improvements completed

The `/advertise` page was aligned with the actual sponsor-placement strategy and improved for conversion.

Completed:
- updated page copy to describe available homepage and article sponsored slots,
- tightened mobile spacing/layout,
- added a Sponsored Business Spotlight section tied to the Local Partner package,
- added an advertiser package/media-kit summary explaining:
  - clear local visibility,
  - direct traffic,
  - performance reporting,
  - simple setup using headline/message/link/logo or image.

Relevant commits:
- `888d3ac` — `Align advertise page with homepage sponsor placements`
- `72f7867` — `Tighten advertise page mobile layout`
- `dbe25a9` — `Add business spotlight section to advertise page`
- `958479e` — `Add advertiser package summary to advertise page`

Live confirmation completed:
- `/advertise` deployed and visually confirmed,
- media-kit summary confirmed live after Render deployment.

### 14.4 Admin sponsored-placement reporting and advertiser workflow improvements

Admin Advertising was strengthened materially.

Completed sponsored-placement features:
- CSV export for sponsored placements,
- advertiser reporting summary card showing active campaigns, impressions, clicks and average CTR,
- confirmed Export CSV / Refresh / Edit advert / Delete advert controls live,
- cleaned outdated Admin guidance so it says active placements can appear in available homepage and article sponsored slots, including desktop and mobile placements.

Completed advertiser-lead workflow improvements:
- Local Partner leads now show a Business Spotlight indicator,
- Local Partner leads prefill sponsored-placement creation with `homepage_both`,
- added Business Spotlight workflow note in Admin Advertising,
- added prefilled advertiser follow-up email template to Email advertiser action,
- added warning UI for `payment_pending` leads explaining that checkout started but payment was not completed,
- added advertiser lifecycle statuses and Admin buttons for:
  - `advert_live`,
  - `renewal_due`,
  - `expired`.

Backend status endpoint now allows the new advertiser lifecycle statuses in addition to the previous `new`, `contacted`, `converted`, `declined`, and `archived` statuses.

Relevant commits:
- `dc79143` — `Add sponsored placement CSV export`
- `10ba4cc` — `Add sponsored placement report summary`
- `57f4c63` — `Improve business spotlight lead workflow`
- `6b3b674` — `Add advertiser follow-up email template`
- `d7825e3` — `Update admin advertising placement guidance`
- `c708b7d` — `Flag unpaid advertising checkout leads`
- `d2ed0b8` — `Add advertiser lead lifecycle statuses`

Live confirmation completed:
- Admin reporting card confirmed live,
- CSV export confirmed visible,
- Business Spotlight workflow note confirmed live,
- lifecycle buttons confirmed live after deployment.

### 14.5 Controlled advertising checkout test completed up to pre-payment

A controlled advertising checkout test was run using the public `/api/advertising/checkout` endpoint.

Verified successfully:
- public advertising checkout endpoint works,
- live Stripe Checkout session is created,
- Admin advertiser lead is created as `payment_pending`,
- `/api/advertising/payment-status/{session_id}` correctly reports unpaid/open for an unpaid session,
- the internal unpaid test lead was archived afterwards.

Important payment note:
- the returned Stripe session was a live Stripe checkout session (`cs_live_...`), not test mode,
- no real £49 payment was completed,
- full end-to-end live-payment verification is deliberately deferred.

Remaining full payment test still requires intentionally paying the live £49 test transaction, then checking webhook/payment success, client email, Admin paid-lead state, sponsored-placement creation, and refund/cleanup if it is only internal verification.

### 14.6 Commercial Gap Map audit findings

Commercial Gap Map audit was started and implemented in several concrete routing/page improvements.

Guide inventory checks completed:
- `frontend/src/config/monetisationTools.js` linked 15 guide URLs,
- all 15/15 linked monetisation guide URLs returned `200` through the live authority-page API,
- backend-only guide destinations were confirmed live even though not present as static fallback entries:
  - `best-company-formation-services-uk`,
  - `best-explainer-video-software-uk`,
  - `council-tax-bands-cheshire`.

Commercial depth findings:
- stronger guide pages include accounting software, web hosting, website builders, parcel/courier services and virtual office services,
- guide-only areas remain where no approved affiliate/tracking link exists,
- mortgage/savings/credit guide pages exist but currently have no affiliate links,
- energy/broadband/ISA pages exist but initially had no tools or affiliate links.

Rule reaffirmed:
- no approved tracking link = surface as `Guide`,
- approved tracking link = may be surfaced as `Affiliate`,
- do not label unapproved destinations as affiliate offers.

### 14.7 Commercial routing improvements completed

#### Moving and wills guides surfaced
Added `moving` and `wills` monetisation groups to `frontend/src/config/monetisationTools.js`.

Newly surfaced destinations:
- `best-removal-van-services-uk` — AnyVan-backed page,
- `best-mattress-deals-uk` — Emma Sleep-backed page,
- `best-online-will-writing-services-uk` — Make a Will Online-backed page.

Relevant commit:
- `1885ddb` — `Surface moving and wills commercial guides`

#### Finance and utility guides surfaced
Existing live but underused guide pages were surfaced as `Guide` destinations rather than Affiliate destinations because they currently do not have approved affiliate links.

Added/surfaced:
- `best-mortgage-rates-uk`,
- `best-savings-accounts-uk`,
- `best-isa-platforms-uk`,
- `best-credit-cards-uk`,
- `cheap-energy-tariffs-uk`,
- `best-broadband-deals-uk`.

Article guide allowlist and routing were updated for mortgages, savings, credit and energy/broadband.

Relevant commit:
- `704a1c6` — `Surface finance and utility guide routing`

#### Business bank account guide surfaced
`best-business-bank-accounts-uk` was confirmed already live through the authority-page API with tools for Starling Business, Tide, Monzo Business and Wise Business. Because affiliate links are empty, it was surfaced as a `Guide`, not Affiliate.

Relevant commit:
- `d908b2a` — `Surface business bank account guide routing`

### 14.8 New guide pages created and routed

Three missing guide pages were prepared, committed as JSON payloads, then upserted into the live authority-page database once an Admin token was available.

Prepared payload files committed to repo:
- `docs/commercial-gap-map/best-small-business-insurance-uk.json`
- `docs/commercial-gap-map/best-payroll-software-uk.json`
- `docs/commercial-gap-map/best-tax-software-uk.json`

Relevant commit:
- `2694f58` — `Prepare commercial gap guide payloads`

Live authority pages created/upserted:
- `best-small-business-insurance-uk`
- `best-payroll-software-uk`
- `best-tax-software-uk`

All three were created as:
- `status: published`,
- `monetisation: none`,
- guide/informational pages, not affiliate pages.

Live API verification returned `200` for all three:
- `best-small-business-insurance-uk 200`
- `best-payroll-software-uk 200`
- `best-tax-software-uk 200`

Public route verification also returned `HTTP/2 200` for:
- `/guides/best-small-business-insurance-uk`
- `/guides/best-payroll-software-uk`
- `/guides/best-tax-software-uk`

Frontend routing was then updated:
- new `monetisationTools.js` groups: `business_insurance`, `payroll`, `tax_software`,
- ArticlePage context routing added for `business-insurance`, `payroll`, and `tax-software`.

Relevant commit:
- `49b75d7` — `Route new business guide pages`

Build/deploy verification:
- frontend build passed,
- commit pushed to `origin/full-scrape-prod`,
- Render deployed,
- API and public routes verified live.

### 14.9 Current confirmed repo/deployment state after April 30 work

Latest confirmed git state:
- `HEAD -> full-scrape-prod`,
- `origin/full-scrape-prod` aligned at `49b75d7`,
- `git status --short` clean after push/deploy verification.

Latest confirmed commit:
- `49b75d7` — `Route new business guide pages`

Production verification completed:
- three new guide APIs return `200`,
- three new public guide routes return `HTTP/2 200`,
- Advertise page improvements deployed and visually confirmed,
- Admin advertising workflow/reporting improvements deployed and visually confirmed.

### 14.10 Current commercial/monetisation state after April 30

Advertising/local sponsor layer:
- homepage sponsor placements active,
- house advert active on desktop and mobile,
- `/advertise` has stronger package/media-kit explanation,
- Business Spotlight is positioned as a Local Partner benefit,
- Admin supports placement editing, CSV export, summary reporting, lifecycle statuses and follow-up email templates,
- pre-payment Stripe checkout path verified,
- full live payment test deferred.

Guide/affiliate/commercial layer:
- all previously linked monetisation guides verified live,
- moving/wills commercial guides surfaced,
- finance/utility guide routing expanded,
- business bank account guide surfaced as a Guide,
- small business insurance, payroll software and tax software guides created live and routed,
- guide-only pages remain intentionally non-affiliate until approved tracking links exist.

### 14.11 Still pending / deferred

Still pending:
1. Full live £49 advertising payment test.
2. Merchant-link enrichment for guide-only pages.
3. Additional tools/providers inside thin guide pages, especially energy, broadband, ISA, insurance, payroll and tax software.
4. Business directory / featured listing product.
5. Newsletter sponsorship inventory.
6. Continue Resend Pro Daily Brief monitoring before cold-subscriber suppression.
7. Render/frontend dependency vulnerability maintenance.
8. Optional Admin warning for pasted Postimg URLs.

### 14.12 Recommended next priority order

Recommended next order:
1. Leave the current advertising and guide routing changes stable after deployment.
2. Run browser spot-checks of:
   - `https://cheshiretoday.co.uk/guides/best-small-business-insurance-uk`
   - `https://cheshiretoday.co.uk/guides/best-payroll-software-uk`
   - `https://cheshiretoday.co.uk/guides/best-tax-software-uk`
3. When ready, perform the full live £49 advertising payment test and refund/cleanup if it is only internal verification.
4. Continue the Commercial Gap Map by improving guide quality/depth for the weakest current pages, not by blindly adding more links.
5. Prioritise merchant approval/tracking quality before converting Guide pages into Affiliate pages.
6. Then consider the next advertiser surface: business directory, newsletter sponsor slot, or category sponsorship.

### 14.13 Updated continuation instruction for the next chat

Use this as the next-chat continuation instruction:

`Continue Cheshire Today from PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260428_v12_FULL.md with the April 30 append applied. Treat this file as append-only. Respect workflow: check current state first, no manual file edits, one command at a time, verify after each change, use grep not rg, build frontend with REACT_APP_BACKEND_URL=https://cheshiretoday.co.uk npm --prefix frontend run build, and avoid npm start. Current latest confirmed commit is 49b75d7 (Route new business guide pages), with origin/full-scrape-prod aligned and production deployed. April 30 completed: homepage sponsor/house advert cleanup; Advertise page alignment/mobile polish/media-kit section; Business Spotlight sales and Admin workflow; sponsored placement CSV export/report summary; advertiser follow-up email template; unpaid checkout warning; advertiser lifecycle statuses advert_live/renewal_due/expired; controlled pre-payment Stripe checkout test with live payment deferred; Commercial Gap Map audit; moving/wills, finance/utility and business bank guide routing; three new published guide pages best-small-business-insurance-uk, best-payroll-software-uk and best-tax-software-uk created and routed. All three new guide APIs and public routes returned 200. Next priorities: visually spot-check the three new guide pages, later run the full live £49 Stripe payment test only when intentionally ready, then continue merchant-link enrichment and guide-depth improvement without marking unapproved destinations as Affiliate.`

---

## 15. May 2, 2026 — Commercial guide completion, sitemap discovery, advertiser-page conversion, Facebook growth scheduling, and newsletter follow-up checkpoint

### 15.1 Purpose of this continuation

This continuation completed several high-value commercial and growth tasks after the April 30 Commercial Gap Map work:

1. cleaned guide monetisation labels so only pages with real approved affiliate links are marked as affiliate,
2. surfaced every live authority guide in frontend routing,
3. added all live guide URLs to the live sitemap,
4. enriched affiliate guide pages with stronger comparison-depth content while preserving approved links,
5. improved the `/advertise` conversion page with a package-selection explainer,
6. fixed the GitHub personal-access-token push issue,
7. created scheduled Facebook growth tasks for article posts, Reels, and engagement follow-up,
8. re-confirmed newsletter follow-up work from the existing state file.

The work remained aligned with the project positioning: Cheshire Today as a local economic-intelligence platform built around Local, Business, Finance, AI/Tech and monetisable guide depth rather than generic crime-heavy news.

### 15.2 GitHub token / push authentication issue fixed

A GitHub email warned that the classic personal access token named `render-deploy` would expire.

Checks completed:
- `git remote -v` confirmed the repository remote did not embed a token,
- project file search found no committed `render-deploy`, `GITHUB_TOKEN`, `GH_TOKEN`, `github_pat` or `ghp_` references,
- macOS Keychain did contain a GitHub credential for `github.com`.

Actions completed:
- old Keychain credential was erased,
- a regenerated classic token with repo access was used at the next push prompt,
- push authentication succeeded.

Conclusion:
- token is most likely used for local HTTPS GitHub push/pull authentication rather than being embedded in the project code or Render config,
- future GitHub password prompts should use the regenerated token, not the account password.

### 15.3 Authority-page affiliate label cleanup completed

A live authority-page audit found pages marked as `monetisation=affiliate` despite having zero approved affiliate links.

First cleanup batch corrected six finance / utility guides from `affiliate` to `none`:
- `best-mortgage-rates-uk`
- `best-savings-accounts-uk`
- `best-credit-cards-uk`
- `cheap-energy-tariffs-uk`
- `best-broadband-deals-uk`
- `best-isa-platforms-uk`

Verification after update:
- all six remained `status=published`,
- all six were `monetisation=none`,
- all six had `affiliate_links=0`.

Documentation commit:
- `87912e7` — `Document finance guide monetisation cleanup`

Second cleanup batch corrected seven more zero-link affiliate-labelled pages:
- `best-ai-productivity-tools-uk`
- `best-ai-tools-uk`
- `best-ai-writing-tools-uk`
- `best-business-bank-accounts-uk`
- `best-business-credit-cards-uk`
- `cost-of-buying-home-cheshire-2026`
- `council-tax-bands-cheshire`

Verification after the second cleanup:
- `BAD_ZERO_LINK_AFFILIATE_PAGES=0`,
- all remaining `monetisation=affiliate` pages had at least one populated `affiliate_link`.

Documentation commit:
- `cbb3dfe` — `Document authority page affiliate label cleanup`

Operating rule confirmed and preserved:
- no approved tracking link = `Guide` / `monetisation: none`,
- approved tracking link exists = `Affiliate` / `monetisation: affiliate`.

### 15.4 All live guide pages surfaced in frontend routing

A live-vs-frontend guide audit originally found:
- `LIVE_GUIDES=34`,
- `FRONTEND_SURFACED_GUIDES=28`,
- `LIVE_NOT_SURFACED=6`,
- `FRONTEND_REFERENCES_NOT_LIVE=0`.

Hidden live guide pages identified:
- `best-ai-productivity-tools-uk`
- `best-ai-tools-uk`
- `best-ai-writing-tools-uk`
- `best-business-credit-cards-uk`
- `best-electric-toothbrushes-oral-care-uk`
- `cost-of-buying-home-cheshire-2026`

Frontend updates made:
- added `ai_tools`, `business_credit`, `home_buying`, and `oral_care` groups to `frontend/src/config/monetisationTools.js`,
- added the six slugs to `ArticlePageV2.jsx` allowlist/context routing,
- kept AI / business-credit / home-buying guide pages as `Guide`,
- kept oral-care guide as `Affiliate` because it has a real approved affiliate link.

Verification after update:
- `LIVE_NOT_SURFACED=0`,
- `FRONTEND_REFERENCES_NOT_LIVE=0`,
- frontend build passed.

Commit:
- `fc74d4e` — `Surface all live guide pages`

Deployment:
- pushed to `origin/full-scrape-prod`,
- Render deployment confirmed.

### 15.5 All live guide pages added to sitemap

Active `backend/server.py` sitemap generation was inspected. Before the patch, `/sitemap.xml` included:
- homepage,
- location pages,
- category pages,
- recent article URLs.

It did not include `/guides/...` authority pages.

Patch added:
- published/live authority pages from `db.authority_pages`,
- `/guides/{slug}` sitemap entries,
- guide `lastmod` based on `updatedAt` when available,
- weekly change frequency,
- priority `0.7`.

Verification:
- backend syntax check passed with `python3 -m py_compile backend/server.py`,
- commit pushed,
- live `/sitemap.xml` included guide URLs,
- full sitemap reconciliation returned:
  - `LIVE_GUIDES=34`,
  - `SITEMAP_GUIDES=34`,
  - `MISSING_FROM_SITEMAP=0`,
  - `EXTRA_IN_SITEMAP=0`.

Commit:
- `fa5a8bc` — `Add guide pages to sitemap`

Robots verification:
- live `robots.txt` advertises:
  - `https://cheshiretoday.co.uk/sitemap.xml`,
  - `https://cheshiretoday.co.uk/news-sitemap.xml`.

### 15.6 Affiliate guide-depth enrichment completed in live DB

A thin-affiliate guide audit was run to identify affiliate pages with shallow comparison depth. Enrichment was applied directly to the live authority-page database via admin upsert, preserving all existing approved affiliate links and not adding unapproved merchants.

#### Guides enriched individually

1. `best-domain-registrars-small-business-uk`
   - sections increased from `7` to `11`,
   - approved 123 Reg affiliate link preserved,
   - new sections added around renewal pricing, DNS/transfer control, web-presence stack and local business domain-name checks.

2. `best-email-marketing-tools-small-business-uk`
   - sections increased from `6` to `10`,
   - approved Mailchimp affiliate link preserved,
   - new sections added around list-size pricing, automation/segmentation, signup forms/website integration and reporting.

#### Batch enrichment 1

Guides enriched:
- `best-company-formation-services-uk`: `6 -> 10` sections,
- `best-explainer-video-software-uk`: `6 -> 10` sections,
- `best-self-storage-services-uk-home-business`: `6 -> 10` sections,
- `best-removal-van-services-uk`: `5 -> 9` sections.

All preserved:
- `status=published`,
- `monetisation=affiliate`,
- existing approved affiliate link count unchanged.

#### Batch enrichment 2

Guides enriched:
- `best-online-will-writing-services-uk`: `5 -> 9` sections,
- `best-mattress-deals-uk`: `5 -> 9` sections,
- `best-iso-training-certification-courses-uk-businesses`: `6 -> 10` sections,
- `best-online-gcse-a-level-courses-uk`: `5 -> 9` sections.

All preserved:
- `status=published`,
- `monetisation=affiliate`,
- existing approved affiliate link count unchanged.

#### Batch enrichment 3

Guides enriched:
- `how-to-choose-shipping-solution-online-business-uk`: `6 -> 10` sections,
- `what-iso-certification-means-small-business-uk`: `6 -> 10` sections,
- `best-parcel-courier-services-small-business-uk`: `7 -> 11` sections.

All preserved:
- `status=published`,
- `monetisation=affiliate`,
- existing approved affiliate links unchanged.

#### Batch enrichment 4

Guides enriched:
- `best-virtual-office-services-small-business-uk`: `7 -> 11` sections,
- `best-web-hosting-small-business-uk`: `7 -> 11` sections,
- `best-website-builders-small-business-uk`: `7 -> 11` sections,
- `best-accounting-software-uk`: `9 -> 13` sections.

All preserved:
- `status=published`,
- `monetisation=affiliate`,
- existing approved affiliate links unchanged.

Total guide-depth enrichment completed:
- `17` affiliate guides improved,
- no unapproved merchants added,
- all approved affiliate links preserved,
- commercial/SEO depth materially strengthened.

Lower-priority remaining thin affiliate page:
- `best-electric-toothbrushes-oral-care-uk`

Decision:
- leave oral-care enrichment for later because it is less aligned with the core Cheshire Today business/finance/AI authority strategy.

### 15.7 Guide-only monetisation candidates audited and intentionally skipped for now

Guide-only pages were audited to identify future affiliate or sponsor opportunities.

Highest future monetisation candidates:
- `best-business-bank-accounts-uk`,
- `best-business-credit-cards-uk`,
- `best-payroll-software-uk`,
- `best-small-business-insurance-uk`,
- `best-tax-software-uk`,
- AI tool guide cluster.

Decision taken:
- skip guide-only enrichment for now,
- keep these pages as Guide / `monetisation=none` until approved tracking links or clear commercial partners exist.

### 15.8 Advertise page package selector added and deployed

The public `/advertise` page was inspected. It already had:
- pricing tiers,
- placement explanation,
- Business Spotlight offer,
- review-before-payment step,
- secure checkout,
- enquiry fallback.

Conversion improvement added:
- a “Which package should I choose?” section above pricing cards,
- three explanatory package cards:
  - Local Starter — testing local visibility,
  - Local Featured — stronger desktop/mobile rotation,
  - Local Partner — regular local exposure and Business Spotlight.

Verification:
- local production build passed,
- local visual test at `/advertise` confirmed by user,
- commit pushed,
- Render deployment confirmed by user.

Commit:
- `3759af8` — `Add advertiser package selector`

Latest confirmed deployed code state after this patch:
- `HEAD -> full-scrape-prod`,
- `origin/full-scrape-prod` aligned,
- latest commit `3759af8`.

### 15.9 Facebook growth schedule created

The user asked for a practical Facebook growth workflow because they currently post articles manually about twice a day.

A scheduled Facebook workflow was created using reminders:

1. `7:30am` daily — morning Facebook post
   - searches `cheshiretoday.co.uk`,
   - chooses the strongest article/guide,
   - prioritises money, local impact, business, property, tax, jobs, AI usefulness and practical guides,
   - produces ready-to-paste Facebook copy,
   - avoids generic link-only posts and crime-heavy filler.

2. `9:30am` daily — one-image Facebook Reel
   - searches `cheshiretoday.co.uk`,
   - chooses the best article for one Reel,
   - uses the article’s main image as a full-screen vertical 9:16 background,
   - adds slow pan/zoom movement,
   - uses three short text overlays,
   - keeps total length to 7–12 seconds,
   - provides caption, article link and suggested pinned comment.

3. `12:30pm` daily — Facebook comment engagement check
   - reply to comments,
   - like useful comments,
   - ask one short follow-up question,
   - check whether the morning post/Reel is getting reach, comments, shares or link clicks,
   - optionally search for one extra breaking post only if genuinely strong local/business/finance/property/AI news exists.

4. `6:30pm` daily — evening Facebook post
   - searches `cheshiretoday.co.uk`,
   - chooses the strongest evening article or guide,
   - uses a discussion-led hook,
   - provides two or three useful points,
   - includes a direct comment question,
   - explains why the chosen post should attract views.

This schedule supports the project’s audience-growth strategy while keeping Facebook aligned to local economic usefulness, not generic link posting.

### 15.10 Newsletter / Daily Brief follow-up found in source file

The source file was searched for the previously agreed follow-up work after one week / several tracked newsletter sends.

Relevant newsletter follow-up plan found in the existing state file:
- after the first proper Resend tracking foundation, the system was considered ready for a valid batch-001 engagement review after the next `3` tracked Daily Brief sends,
- the recommended priority was to allow the next `3` properly tracked Daily Brief sends to hit batch 001,
- then build the first valid deactivate list for batch 001 only,
- exclude protected internal/test emails,
- then move to the next 250-recipient cohort in a controlled wave.

Later April continuation notes also warned:
- do not mass-deactivate cold candidates immediately,
- monitor the next tracked Resend Pro Daily Brief sends,
- review engagement across the expanded batch,
- make any suppression/deactivation decision only after more evidence.

Current newsletter action for next session:
1. check recent Daily Brief sends / email digest logs,
2. confirm how many properly tracked sends have occurred since Resend Pro expansion,
3. review open/click/engagement by batch/cohort,
4. only then decide whether a controlled cold-subscriber suppression wave is justified,
5. do not perform mass suppression without another evidence review.

### 15.11 Current confirmed project state after this update

Code / repo:
- latest confirmed deployed commit: `3759af8` — `Add advertiser package selector`,
- earlier relevant commits now deployed/pushed:
  - `fc74d4e` — `Surface all live guide pages`,
  - `fa5a8bc` — `Add guide pages to sitemap`,
  - `87912e7` — `Document finance guide monetisation cleanup`,
  - `cbb3dfe` — `Document authority page affiliate label cleanup`.

Guide system:
- `34` live guide pages,
- all `34` surfaced in frontend routing,
- all `34` present in live `/sitemap.xml`,
- `MISSING_FROM_SITEMAP=0`,
- `EXTRA_IN_SITEMAP=0`,
- `BAD_ZERO_LINK_AFFILIATE_PAGES=0`,
- `17` affiliate guides enriched for comparison depth.

Advertising / sponsor system:
- `/advertise` package selector added and deployed,
- Business Spotlight still positioned as Local Partner benefit,
- full live £49 payment test remains deferred.

Social growth:
- daily Facebook morning post task active,
- daily one-image Reel task active,
- midday engagement task active,
- daily evening post task active.

Newsletter:
- Resend Pro monitoring remains pending,
- email digest / Daily Brief follow-up should now be the next operational task if the user wants to inspect newsletter performance.

### 15.12 Recommended next priority order

Recommended next order from this checkpoint:
1. Check email digest / Daily Brief analytics and recent Resend tracking data.
2. Confirm whether the required properly tracked sends have occurred for the relevant cohort(s).
3. Review engagement before any suppression or deactivation decision.
4. If enough evidence exists, prepare a controlled cold-subscriber action plan, excluding protected internal/test emails.
5. If evidence is insufficient, continue monitoring rather than suppressing.
6. Later run the full live £49 advertising payment test when intentionally ready.
7. Later consider business directory / featured listing / newsletter sponsorship inventory.
8. Later update guide-only commercial pages only when approved affiliate partners/tracking links exist.
9. Later investigate Render/frontend dependency security warnings.

### 15.13 Updated continuation instruction

Use this continuation instruction in the next chat:

`Continue Cheshire Today from PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260428_v12_FULL.md with the May 2 append applied. Treat the file as append-only. Respect workflow: check current state first, no manual file edits, one command at a time, verify after each change, use grep not rg, and use full macOS command paths if terminal PATH cannot find git/curl/sed/python3. Latest confirmed deployed commit is 3759af8 (Add advertiser package selector). Guide system is now fully surfaced and sitemap-aligned: 34 live guides, 34 guide sitemap URLs, no hidden live guide pages, no broken frontend guide references, no affiliate-labelled pages without affiliate links. 17 affiliate guide pages were enriched directly in the live DB with comparison-depth sections while preserving approved links. Facebook growth reminders are active at 07:30, 09:30, 12:30 and 18:30. Next priority: check email digest / Daily Brief analytics, confirm whether enough tracked sends exist for newsletter cohort review, and do not mass-suppress cold subscribers without evidence.`

---

## 15. May 3, 2026 — Newsletter Rotation, Homepage Quality Tightening, Weekly Roundup Diagnostics, and Social Publishing Support

### 15.1 Working context and protocol followed

This update records the May 3 working session and should be treated as an append-only continuation of the current master project file.

Workflow followed during the session:
- checked current state before each change,
- applied changes through terminal commands/scripts only,
- avoided manual file editing,
- used one command at a time where practical,
- used `grep` rather than `rg`,
- built frontend with the production backend URL when testing locally,
- verified commits, pushes and deployments after each major step,
- preserved manually added / featured / force-live content when tightening homepage rules.

Strategic constraint maintained:
- Cheshire Today remains positioned as a local economic intelligence platform, not a generic broad local-news/lifestyle feed.
- Editorial direction remains Local + Business/Finance + AI/Tech, with property/tax allowed when economically useful, but with crime-heavy and weak filler de-emphasised.

### 15.2 Newsletter diagnostics and Daily Brief preview tooling

Three backend newsletter-support commits were already present locally and were pushed/deployed during this phase:

- `579451a` — `Add read-only email engagement diagnostic`
- `7406903` — `Add read-only Daily Brief preview tool`
- `3cfe089` — `Use quality-first Daily Brief article selection`

Purpose of the work:
- improve visibility into Daily Brief performance,
- allow read-only preview of likely Daily Brief article picks,
- stop weak newest-first content from dominating newsletter selection,
- prioritise stronger money/business/local-impact stories.

Daily Brief preview output during the session showed the quality-first selector choosing higher-value stories such as:
- financial advice / savings,
- data-centre / tech-business relevance,
- mortgages/jobs/energy-bills impact,
- Chester apartments / local property-economic relevance,
- business disruption stories.

Validation completed:
- `backend/venv/bin/python -m py_compile backend/server.py` passed,
- `git diff --check` passed after trailing whitespace cleanup,
- Daily Brief preview script executed successfully,
- local commit and push completed,
- backend deployed and health endpoint returned healthy.

### 15.3 Daily Brief and Weekly Roundup rotating batch system

A major newsletter audience fairness fix was added and deployed:

- `540f73d` — `Add newsletter batch rotation and weekly roundup scale`

Problem addressed:
- Daily Brief and Weekly Roundup were capped sends, but the user expected rotation through the wider subscriber list rather than repeatedly sending only to the first batch.
- Weekly Roundup was previously only finding 2 subscribers because the existing large subscriber list had `weekly_roundup=False` as a system default, not necessarily as a manually updated opt-out.

Code behaviour added:
- `_select_rotating_email_batch(digest_key, unique_emails, send_cap)` chooses a stable sorted capped batch using a per-digest cursor stored in MongoDB.
- `_save_email_batch_cursor(...)` persists cursor position only after send attempt success rules are met.
- Daily Brief now uses a `DailyBrief` cursor.
- Weekly Roundup now uses a separate `WeeklyRoundup` cursor.
- Cursor does not advance if `success_count == 0`, preventing failed sends from skipping subscribers.

Weekly Roundup audience query changed:
- includes explicitly `weekly_roundup=True` subscribers,
- also includes active `daily_brief=True` subscribers where `preferences_updated_at` does not exist, because the legacy `weekly_roundup=False` value was a system default rather than a confirmed manual opt-out.

Confirmed subscriber counts during checks:
- total active newsletter subscribers: about 14,316,
- legacy `weekly_roundup=True`: 2,
- `weekly_roundup=False` without `preferences_updated_at`: about 14,314,
- expected Weekly Roundup eligible audience after patch: about 14,316,
- Weekly Roundup cap: 2,000.

Deployment and verification:
- commit pushed to `origin/full-scrape-prod`,
- backend manually deployed on Render,
- `/api/health` returned healthy,
- digest logs showed previous Daily Brief sends were intact.

Important operational note:
- if no successful send has happened yet, `email_batch_cursors` can be empty; this is expected.
- after a successful capped send, the relevant digest cursor should appear with `next_index` advanced by the batch size.

### 15.4 Daily Brief live log state reviewed

Recent digest logs checked after deployment showed:
- Daily Brief continued to send at capped 2,000 recipient batches,
- recent successful Daily Brief logs showed `success_count=2000`,
- one earlier Daily Brief log on `20260430` showed `success_count=0`, which existed before the new cursor-safety change.

Current expected Daily Brief behaviour:
- runs Monday to Saturday at 07:30 UK time,
- sends to 2,000 per scheduled run,
- rotates through eligible subscribers once successful sends begin advancing the cursor,
- now uses quality-first article selection rather than raw latest-first filler.

### 15.5 Homepage article-pool audit and imported-story tightening

The live article API pool was audited because too many property/planning and weak imported stories were appearing around Latest / More stories.

Live API audit summary at the time:
- total articles reviewed: 81,
- Local News: 37,
- Tech: 20,
- Business: 12,
- Finance: 11,
- UK News: 1.

Theme flags found in live pool:
- business/money: 29,
- AI/tech-useful signals: 21,
- property/planning: 9,
- weak science/nature: 8,
- lifestyle/light local: 7,
- crime/live incident: 4,
- entertainment: 2.

Key diagnosis:
- the problem was not just property/planning,
- the wider issue was weak imported filler entering strategic homepage sections,
- examples included James Bond/song entertainment tech, dragonflies, frogs/birds/wetlands, underwater forests, dinosaur skull, red squirrels, ospreys, garden-centre/ice-cream/tearoom filler, butter-beans review content, and live incident/crime churn.

Decision:
- do not touch manually added / featured / force-live / priority articles,
- do not remove property entirely from the project,
- tighten imported article eligibility for homepage strategic sections.

Frontend change committed:

- `9ca5134` — `Tighten homepage imported story eligibility`

Code behaviour changed in `frontend/src/pages/HomePageV1.jsx`:
- `isStrategicHomepageStory()` now immediately preserves:
  - `featured`,
  - `force_live`,
  - `is_priority_cheshire`.
- Added stronger imported-story filtering for:
  - entertainment / James Bond song-style content,
  - shopping/review/listicle filler including butter beans,
  - soft lifestyle/local leisure filler such as garden centre, miniature railway, train rides, secret play area, ice cream, golf buggies, tearoom and Chester Races menu items,
  - weak nature/science/oddity tech such as dragonflies, frogs, birds, wetlands, sewage/underwater forests, dinosaurs, squirrels, ospreys, habitat powerhouses, Soviet science, Anne Boleyn and oddity stories unless they also have clear AI/business/money/public-impact relevance,
  - live incident/crime churn unless there is strong public-impact utility,
  - emotional/tragedy filler without clear public utility.

Build/deploy verification:
- frontend build passed locally,
- commit pushed to `origin/full-scrape-prod`,
- Render deployed,
- there was initial confusion because live bundle filename remained `main.5496f29f.js`, while local builds produced different bundle hashes,
- live bundle was then verified directly by grepping the deployed JS for new runtime filter terms.

Live verification completed:
- `dragonflies` found in live JS bundle,
- `james`, `underwater`, and `ospreys` found in live JS bundle,
- this confirmed the homepage tightening code was live even though the bundle filename did not change as expected.

Important distinction:
- `/api/articles` still returns the raw article pool and can still include weak/property/lifestyle articles,
- the frontend homepage now filters more of those out of strategic homepage sections,
- manually promoted stories remain preserved.

### 15.6 Weekly Roundup run investigation on May 3

The user reported that Weekly Roundup did not appear to run on Sunday morning.

Digest-log check showed it did run:

- `digest_time`: `WeeklyRoundup`,
- `date_key`: `20260503`,
- `sent_at`: `2026-05-03T08:00:20.664000` UTC / 09:00 UK,
- `articles_count`: 6,
- `subscribers_count`: 2000,
- `success_count`: 0,
- tracking ID: `weekly_roundup_2026-05-03T09:00:00.868735_3c63dbde`.

Conclusion:
- scheduler ran,
- the new Weekly Roundup audience scaling worked and selected 2,000 subscribers,
- six articles were selected,
- send path returned `success_count=0`, so no email was successfully sent,
- cursor safety worked because `email_batch_cursors` remained empty and no subscribers were skipped.

Render logs around the job showed one instance skipping because another acquired the Weekly Roundup lock:
- this was normal distributed-lock behaviour,
- the actual send attempt occurred on the instance that acquired the lock.

Email service inspection showed:
- Daily Brief and Weekly Roundup both build `batch_messages`,
- both call the shared `_send_resend_batch(batch_messages)` function,
- Daily Brief sends successfully through the shared path,
- therefore the likely issue is a Weekly-specific payload rejection by Resend, not a global Resend configuration failure.

### 15.7 Resend batch failure diagnostics added

Because Resend rejection details were only visible in Render logs and not stored in MongoDB, targeted logging was added to `_send_resend_batch()`.

Commit:

- `ffc4acc` — `Improve Resend batch failure diagnostics`

File changed:
- `backend/app/email_service.py`

Diagnostics added:
- chunk number,
- chunk size,
- HTTP status code,
- first recipient domain,
- email subject,
- first 1,000 characters of Resend response body,
- explicit zero-success summary log if all chunks fail.

Behaviour intentionally unchanged:
- no send logic was changed,
- no retry logic added yet,
- no subscriber state changed,
- no cursor behaviour changed.

Validation and deployment:
- `backend/venv/bin/python -m py_compile backend/app/email_service.py` passed,
- `git diff --check` passed,
- commit pushed to `origin/full-scrape-prod`,
- backend manually deployed on Render,
- `/api/health` returned healthy.

Next time Resend rejects a Weekly/Daily batch, Render logs should include:
- `Resend batch rejected before raise...`,
- `Resend batch send failed...`,
- `status=...`,
- `response=...`.

### 15.8 Social/Facebook publishing support during May 3

Social-support work was also carried out in chat, separate from code changes.

Tasks handled:
- morning Facebook article/post and Reel suggestions were created around household-money/energy-bill angles,
- user asked to avoid older article picks and to prefer same-day/newest article candidates,
- property/planning articles were initially suggested but the user clarified not to use planning/houses posts for that request,
- the final approach should prefer freshest same-day articles while respecting editorial exclusions,
- user also requested Facebook activity follow-up workflow:
  - reply to comments,
  - like useful comments,
  - ask one short discussion question,
  - check reach/comments/shares/link clicks,
  - only create an extra post if genuinely strong breaking local/business/finance/property/AI news exists,
  - only consider sharing/boosting if a post is already organically performing.

Editorial note for future social prompts:
- avoid old article picks unless explicitly requested,
- prefer articles from the current day when the user asks for latest/newest,
- avoid planning/housing/property suggestions if user says no houses/planning,
- avoid generic headline-plus-link posts,
- prioritise money impact, local business/job impact, practical guides and useful AI/tool stories.

### 15.9 Current confirmed git/deployment state after May 3 work

Latest confirmed pushed commits after this session:

- `579451a` — `Add read-only email engagement diagnostic`
- `7406903` — `Add read-only Daily Brief preview tool`
- `3cfe089` — `Use quality-first Daily Brief article selection`
- `540f73d` — `Add newsletter batch rotation and weekly roundup scale`
- `9ca5134` — `Tighten homepage imported story eligibility`
- `ffc4acc` — `Improve Resend batch failure diagnostics`

Latest confirmed branch state:
- branch: `full-scrape-prod`,
- latest pushed commit: `ffc4acc`,
- remote: `origin/full-scrape-prod`,
- backend health check after deployment returned healthy.

Confirmed live states:
- newsletter rotation code deployed,
- homepage tightening code deployed and verified inside live JS bundle,
- Weekly Roundup diagnostics deployed,
- no Weekly/Daily cursor advanced from the failed Weekly send because success count was zero.

### 15.10 Pending / next steps after May 3

Immediate pending tasks:
1. Search Render logs after the next Weekly/Daily failed batch for:
   - `Resend batch rejected before raise`,
   - `Resend batch send failed`,
   - `Resend batch send completed with zero successes`.
2. Use the new diagnostic response body to determine why Weekly Roundup Resend batch returned zero.
3. Do not manually advance the WeeklyRoundup cursor unless a send succeeds.
4. After the next successful Daily Brief, check `email_batch_cursors` to confirm `DailyBrief` cursor creation/advance.
5. After the next successful Weekly Roundup or controlled test, check `WeeklyRoundup` cursor creation/advance.
6. Continue monitoring homepage Latest / More stories visually after the new imported-story filter is live.
7. If property/planning still dominates visually, use a small cap rule rather than another broad block.
8. Continue avoiding manual/featured/force-live article interference.
9. Continue investigating the existing frontend dependency vulnerabilities as a separate maintenance task, not as part of the current newsletter/homepage flow.

### 15.11 Recommended next-chat continuation instruction

Use this as the next-chat continuation instruction:

`Continue Cheshire Today from PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260428_v12_FULL.md with the May 3 append applied. Treat the file as append-only. Respect workflow: check current state first, no manual file edits, one command at a time, verify after each change, use grep not rg, build frontend with REACT_APP_BACKEND_URL=https://cheshiretoday.co.uk npm --prefix frontend run build or render_build.sh as appropriate, avoid npm start, and remember Render auto-deploy is disabled so manual deploys are required. Latest confirmed pushed commit is ffc4acc (Improve Resend batch failure diagnostics). May 3 completed: newsletter diagnostic and Daily Brief preview tools; quality-first Daily Brief article selection; rotating 2,000-recipient batches for Daily Brief and Weekly Roundup with cursor safety; Weekly Roundup audience scaled from 2 to about 14,316 eligible default subscribers but capped at 2,000 per send; homepage imported-story eligibility tightened while preserving featured/force_live/manual articles; homepage tightening verified live in JS bundle; Weekly Roundup ran on 2026-05-03 at 09:00 UK, selected 2,000 subscribers and 6 articles, but Resend returned success_count=0; cursor did not advance, so subscribers were not skipped; Resend batch failure diagnostics were deployed to expose status/body/subject/chunk info in the next failure logs. Next priority: inspect Render logs for the new Resend diagnostic lines after the next failed/test send, determine the exact Weekly Roundup rejection reason, then patch the payload/template or send logic only after the rejection reason is known. Also monitor DailyBrief and WeeklyRoundup email_batch_cursors after successful sends.`


---

## 16. May 2026 append — homepage economic rebalancing, affiliate guide monetisation, article filtering, and provider-click tracking

### 16.1 Session objective

This working session moved Cheshire Today further from a generic local-news feed toward the intended hybrid local economic intelligence platform. The focus was not broad redesign. The work concentrated on:

- improving article filtering and homepage composition;
- reducing planning / soft local / incident-heavy content dominance;
- adding and optimising DHL eCommerce and Interparcel Awin affiliate tracking in the parcel/courier guide;
- creating provider-level tracking for authority guide affiliate buttons;
- preparing the next finance-affiliate monetisation layer through Awin applications.

This remains aligned with the strategic platform direction: local economic relevance, business, finance, AI/tech, property/tax utility, and affiliate-first monetisation.

### 16.2 Article filtering and live homepage content review

A live homepage/content-pool review was performed using `/api/articles?limit=120` and `/api/articles?limit=200` saved to temporary JSON files before parsing. The safe save-then-parse pattern was used to avoid the previous heredoc/JSON `SyntaxError` issue.

A first scan of the active homepage pool identified several articles that were not aligned with the current project positioning. The review separated true rejects from false positives. Some articles initially flagged by broad keyword matching were intentionally kept because they were business, finance, AI, local economic, or useful local infrastructure stories.

Examples of articles intentionally kept because they remain aligned:

- `Inside Chester's new-look Northgate Arena after multi-million pound revamp` — local infrastructure / investment relevance.
- `Companies pay out to charity after slurry incidents` — regulatory/business/environmental accountability relevance.
- `Lidl announces 23 Cheshire store target locations for 2026 - full list` — retail expansion / local economic impact.
- `Tatton Park dog rule change announced following death of lambs` was initially discussed as potentially keepable local utility, but later homepage curation removed it as part of reducing soft local content.
- `Nasa brought crashing down to earth as budget threat follows lunar success` — tech/budget/public spending relevance.
- `Billions of meals at risk due to Iran war, says fertiliser boss` — macro economy / food supply / business risk.
- Musk / Altman legal and AI/business stories — AI/business/technology relevance.
- Renters' rights, interest rates, tax, savings, car finance redress and similar household-money stories — core finance relevance.

Articles archived during the live editorial cleanup included clear crime, incident, sensitive, low-value animal/zoo, soft lifestyle, and weak entertainment/local items. Archived examples included:

- `Pornhub to become accessible again for some UK users` — sensitive/off-strategy adult-content article.
- `Driver 'pulled from vehicle' on Cheshire A34 after hitting tree` — incident churn.
- `Driver, 19, in hospital after crashing into tree on Cheshire A-road` — incident churn.
- `Thieving Carl BANNED from Crewe Tesco, Morrisons and Hobbycraft` — crime/court/local churn.
- `Wildlife park welcomes three male Asiatic lions` — animal/zoo filler.
- `'I had to pay £14k after my cat was run over'` — emotional/tabloid filler.
- `How to write a James Bond song - from the man who knows best` — entertainment filler.
- `German museum to return rare Irritator dinosaur skull to Brazil` — science/filler outside project angle.
- `Endangered antelopes flown to Kenya from Czech zoo in 'historic homecoming'` — zoo/animal filler.
- `£20m mystery gift buys London Zoo new hospital where you can watch vets work` — zoo filler.
- `Cheshire festival returns for second year after 'huge' debut success` — soft local lifestyle.
- `The Cheshire ice cream drive-in with golf buggies bringing treats to your car` — soft local lifestyle.
- `Ellesmere Port woman 'in state of panic' after beach visit ends in rescue from rising tide` — rescue/incident filler.
- `The Ivy launches limited edition menu for Chester Races` — restaurant/menu soft local.
- `Gap co-founder Doris Fisher dies aged 94` — obituary-style business filler.
- `A game-changer for good health? Scientists believe ‘we are when we eat’` — health/opinion filler.
- `The Cheshire garden centre with £3 train rides to secret play area` — soft lifestyle.
- `Tatton Park dog rule change announced following death of lambs` — soft local / animal-related story.
- `The Cheshire garden centre with miniature railway and tearoom` — soft lifestyle.

Result: the live homepage pool became cleaner and more aligned with business, finance, AI/tech and useful local economic relevance. Manual cleanup was treated as an immediate editorial correction, while code-level ranking and filtering were also improved to reduce repeat manual intervention.

### 16.3 RSS sync filter tightening

A backend filter weakness was identified in `backend/server.py` around the RSS sync path. The system already had strong filters for hard crime, sports, obituary-style content and obvious low-utility content, but the live pool showed leakage from:

- low-value incident / crash stories;
- animal / zoo / wildlife filler;
- emotional/tabloid stories.

A targeted sync filter was added in `sync_rss_now()` after the existing `sync_low_utility_kw` check. The new logic blocks low-value incident / animal / tabloid filler unless the article also has strong economic/business relevance.

New filter intent:

- Block: `driver`, `crash`, `injured`, `pulled from vehicle`, `emergency services` when not economic.
- Block: `zoo`, `wildlife park`, `lion`, `antelope`, `dogs brains`, `rescued animals` when not economic.
- Block: emotional/tabloid phrases such as `I had to`, `family says`, `heartbroken`, `after my`, `rescued by firefighters` when not economic.
- Preserve: articles with business/economic markers such as mortgage, rent, tax, inflation, jobs, business, finance, energy, council, planning, housing, investment, warehouse, development, stores, retail.

A syntax issue was avoided by defining `sync_econ_kw` locally inside the filter block rather than using `econ_kw` before its later definition. Backend syntax was verified with:

```bash
python3 -m py_compile backend/server.py
```

Commit and deployment:

- Commit: `c14a73e Tighten RSS sync filter for low-value incident and animal filler`
- Pushed and backend deployed.
- Health verified with `/api/health` returning healthy.

### 16.4 Homepage composition audit and ranking correction

The live homepage audit showed counts that looked acceptable on paper but still felt too planning/local-heavy visually:

- Tech: ~35–37
- Business: ~32–33
- Local News: ~31–34
- Finance: 19
- UK News: 1

The issue was not only category volume; it was ordering and visual impression. The top of Latest was still led by Local and planning/development items, making the site feel like a local planning feed rather than a finance/business/AI economic platform.

The existing `HomePageV1.jsx` logic was inspected before changing anything. Previous balancing logic already existed in the Latest section:

- Target mix: 4 Local, 4 Business/Finance, 3 AI/Tech, 1 UK.
- But the pass order started with Local first, then Business/Finance.

Two homepage frontend changes were made safely:

1. Latest pass order changed so Business/Finance leads before Local, while keeping the same 4/4/3/1 target mix.
2. Pure planning / housing approval articles were downranked inside `rankScore()` so they no longer dominate top homepage positions.

The planning penalty preserves business-impact developments. It penalises planning-only items but keeps jobs/warehouse/retail/business/investment/employment developments competitive.

Final planning penalty intent:

```js
const planningText = (String(a?.title || "") + " " + String(a?.summary || "")).toLowerCase();
const isPlanningOnly = /(planning|housing|estate|new homes|approved|approval|application|apartments|flats)/.test(planningText);
const hasBusinessImpact = /(jobs?|warehouse|retail|business|factory|investment|town centre|store|stores|employment)/.test(planningText);
if (isPlanningOnly && !hasBusinessImpact) {
  score -= 320;
}
```

The first build surfaced trailing whitespace and then a duplicate `t` variable issue. These were fixed by trimming trailing whitespace and using `planningText` rather than redeclaring `t`.

Build was verified with:

```bash
REACT_APP_BACKEND_URL=https://cheshiretoday.co.uk npm --prefix frontend run build
```

Result after local visual check:

- Top Latest row moved away from housing/planning dominance.
- Top row became more economic/business-led, e.g. pubs closing due to tax pressure, UK borrowing costs, and broader economic stories.
- Planning items remained available lower down, which is intentional. The objective was not to remove planning/property, but to stop pure planning approvals dominating first impression.

Commits and deployment:

- Commit: `73bd264 Downrank pure planning items in homepage ranking`
- Pushed and frontend deployed.

### 16.5 Homepage guide / monetisation strip work already live before this append

The current live homepage guide system includes earlier May work that is relevant to the current state:

- `6dd684a Expand homepage guide rotation with household finance options`
- `7f0ab76 Prioritise finance guides in primary homepage strip`

The first homepage guide strip now prioritises household/finance guide cards such as mortgage, savings and energy/bills. The second strip retains broader guide rotation. Daily rotation remains deterministic by UTC date.

### 16.6 Article-to-guide targeting improvements already live before this append

Article guide targeting was strengthened so finance, property/tax and business articles feed into more relevant commercial guides:

- `507ed77 Strengthen finance guide targeting for article conversion`
- `4ba9af6 Expand property/tax guide targeting for better household conversion`
- `9bdd6d4 Improve business fallback guide targeting with banking option`
- `a91b5a1 Remove unused article guide split logic`

Key improvements:

- Mortgage context now pushes mortgage, savings and ISA guides.
- Savings context pushes savings, ISA and mortgage guides.
- Credit context includes credit cards, business credit cards and savings.
- Energy context includes energy tariffs, broadband and savings.
- Property/tax context includes home-buying costs, council tax and mortgage rates.
- Business fallback now includes business formation, business bank accounts, accounting, email marketing and domains.
- Old unused split logic that previously supported intrusive mid-article guide placement was removed.

### 16.7 DHL eCommerce Awin affiliate integration

DHL eCommerce approval was received through Awin. The programme offers:

- 9% commission for new customers;
- 1.3% for existing customers;
- 30-day cookie window.

A DHL eCommerce Awin tracking link was generated using Awin Link Builder.

Destination URL used:

```text
https://www.dhl.com/gb-en/home/our-divisions/ecommerce/solutions.html
```

Click reference:

```text
ct-dhl-ecommerce-parcel-guide
```

Final DHL tracking URL:

```text
https://www.awin1.com/cread.php?awinmid=121764&awinaffid=2844510&clickref=ct-dhl-ecommerce-parcel-guide&ued=https%3A%2F%2Fwww.dhl.com%2Fgb-en%2Fhome%2Four-divisions%2Fecommerce%2Fsolutions.html
```

DHL eCommerce UK was added to the live parcel/courier guide using the admin authority-page upsert endpoint with a full payload. A failed attempt using `sections_append` revealed the endpoint requires required fields including `title`, so the full existing guide payload was fetched first, modified in Python, and then re-upserted.

Guide affected:

```text
/guides/best-parcel-courier-services-small-business-uk
```

DHL positioning:

```text
Best for small businesses needing a reliable direct courier with strong UK and international delivery coverage. DHL eCommerce is particularly suited for consistent shipping volumes and brand trust.
```

DHL was inserted into the tool list and later reordered as part of guide optimisation.

### 16.8 Interparcel Awin tracking link correction

Interparcel was confirmed as available on Awin. The existing guide link was previously untracked:

```text
https://www.interparcel.com/
```

A first Awin link was generated incorrectly with the destination URL placed into `clickref`. This was rejected and corrected.

Correct destination URL:

```text
https://www.interparcel.com/
```

Correct click reference:

```text
ct-interparcel-parcel-guide
```

Final Interparcel Awin tracking URL:

```text
https://www.awin1.com/cread.php?awinmid=32851&awinaffid=2844510&clickref=ct-interparcel-parcel-guide&ued=https%3A%2F%2Fwww.interparcel.com%2F
```

The live guide was updated so all three parcel/courier providers now use tracked Awin links.

Final verified provider tracking state:

1. Parcel ABC UK — tracked Awin link.
2. DHL eCommerce UK — tracked Awin link.
3. Interparcel — tracked Awin link.

### 16.9 Parcel/courier guide conversion optimisation

The parcel/courier guide became the first fully monetised and trackable guide asset.

Guide:

```text
best-parcel-courier-services-small-business-uk
```

Final provider ordering:

1. `Parcel ABC UK` — price comparison intent.
2. `DHL eCommerce UK` — reliability and scale.
3. `Interparcel` — overall multi-carrier option.

Tool descriptions were rewritten to be more decision-led and conversion-oriented:

- Parcel ABC UK: `Best for price comparison: compare parcel delivery quotes across couriers before booking. Useful for small businesses that want to check costs quickly before choosing a service.`
- DHL eCommerce UK: `Best for reliability and scale: a strong direct courier option for businesses that need trusted UK and international delivery, consistent tracking and brand recognition.`
- Interparcel: `Best overall multi-carrier option: useful for small businesses that want access to several courier services from one platform rather than managing separate carrier accounts.`

This improved the page from a simple provider list into a decision-first commercial guide.

### 16.10 Authority guide provider click tracking

Provider-level click tracking was added to `AuthorityPage.jsx` using the existing frontend `trackEvent` helper. No backend tracking endpoint exists yet, so this is currently client-side dataLayer / GA-style tracking.

Events added:

```text
guide_provider_click
```

Captured fields:

- guide slug;
- provider name;
- provider position;
- destination URL;
- placement where applicable.

Initial implementation added tracking to provider card CTAs:

- Commit: `9d462cc Track authority guide provider clicks`

Testing then showed that the top provider CTA had a separate “Visit provider” button that did not have tracking. Tracking was added there too.

- Commit: `c407465 Track authority guide top provider CTA clicks`

During live testing, two scope errors appeared:

1. `ReferenceError: Can't find variable: slug`
2. `ReferenceError: Can't find variable: page`

These occurred because the top CTA lives in a helper/component scope where neither `slug` nor `page` was available. The final fix used a pathname-derived guide slug:

```js
guide: window.location.pathname.replace("/guides/", "")
```

- Commit: `8928abb Fix top provider CTA tracking guide slug`
- Final subsequent commit after using the safer pathname scope: `Fix authority top CTA tracking scope` (commit created after `8928abb`; verify exact hash in git log if needed).

Final live test confirmed:

```js
window.dataLayer.filter(x => x && x.event === "guide_provider_click")
```

returned one event object after clicking the top provider CTA.

Important tracking note:

- The user’s browser blocks Google Tag Manager / GA as a known tracker.
- `window.dataLayer` still receives the event, confirming site-side event creation is working.
- GA may not receive events from browsers with tracker blocking.
- Future backend/internal click logging is recommended to avoid relying only on GA.

### 16.11 Current tracking limitation and recommended backend tracking upgrade

Current guide provider tracking is client-side only. This is useful but incomplete because:

- Safari/iOS privacy protections can block Google Tag Manager or GA;
- content blockers, Private Relay, DNS filters, Brave/Firefox tracking protection, AdGuard, NordVPN threat protection, Pi-hole, etc. may block analytics;
- affiliate clicks may still happen but not be visible in GA.

Recommended next technical upgrade:

Create a backend tracking endpoint, for example:

```text
POST /api/track/guide-click
```

Store:

- guide slug;
- provider;
- position;
- placement;
- destination;
- timestamp;
- optional user-agent / referrer where appropriate;
- no sensitive personal data unless explicitly required.

This would provide internal analytics even when GA is blocked.

### 16.12 Awin finance / insurance affiliate applications submitted

After parcel guide monetisation, the next monetisation expansion moved into Awin finance, insurance, property and household-cost partners.

The user selected website/content promotion under the user’s Cheshire Today website promotion method.

A short 255-character style description was used because Awin’s application description field allowed only 255 characters.

Submitted applications are currently pending:

1. AXA Business Insurance — pending.
2. AXA Landlord Insurance — pending.
3. QuoteSearcher — pending.
4. Heatable — pending.
5. Mymoneycomparison — pending.
6. Hiscox Underwriting Group Services Ltd — pending.

Strategic reasoning:

- AXA Business Insurance: strong fit for small-business insurance guide cluster.
- AXA Landlord Insurance: property / landlord / rental market monetisation layer.
- QuoteSearcher: comparison/aggregator layer for insurance/utilities/finance comparisons.
- Heatable: household energy/home-cost monetisation layer.
- Mymoneycomparison: finance comparison bridge for savings, loans and money guides.
- Hiscox: premium business-insurance backup/complement to AXA.

Instruction for next stage:

Stop applying to many more finance affiliates until at least one or two approvals arrive. Avoid creating a large batch of weak or random applications. When the first relevant approval arrives, immediately integrate it into the matching guide and track clicks.

### 16.13 Current deployed commit state from this session

Known pushed/deployed commits from this session include:

- `c14a73e Tighten RSS sync filter for low-value incident and animal filler`
- `73bd264 Downrank pure planning items in homepage ranking`
- `9d462cc Track authority guide provider clicks`
- `c407465 Track authority guide top provider CTA clicks`
- `8928abb Fix top provider CTA tracking guide slug`
- Later tracking-scope fix commit after `8928abb` was also pushed and deployed; verify exact hash with `git log -5 --oneline` in repo if needed.

Frontend and backend deployments were manually triggered on Render after pushes, consistent with the project rule that Render auto-deploy is disabled.

Health checks after backend deploys returned:

```json
{
  "status": "healthy",
  "service": "cheshire-news"
}
```

### 16.14 Current project state after this update

Current state summary:

- Homepage is cleaner and more aligned with the economic/business/finance strategy.
- Pure planning/housing approvals are downranked from top positions unless they have clear business/jobs/retail/investment impact.
- Incident, animal/zoo and emotional filler filtering was tightened in RSS sync.
- Manual cleanup removed sensitive, incident, crime, soft lifestyle and off-strategy content from live article pool.
- Parcel/courier guide is fully monetised with tracked Awin links for Parcel ABC, DHL eCommerce UK and Interparcel.
- Authority guide provider CTAs now emit `guide_provider_click` events into `window.dataLayer`.
- GA blocking in the user’s browser was diagnosed as local privacy/tracker blocking, not a broken site implementation.
- Finance/insurance affiliate expansion has begun in Awin with six relevant programmes pending.

### 16.15 Remaining high-priority tasks

1. Backend/internal click tracking
   - Build `POST /api/track/guide-click` or equivalent.
   - Record provider clicks in MongoDB for reliable internal analytics.
   - Keep GA/dataLayer as an additional layer, not the sole source of truth.

2. Continue affiliate approval monitoring
   - Watch Awin for AXA Business, AXA Landlord, Hiscox, QuoteSearcher, Heatable and Mymoneycomparison.
   - As soon as any approval is received, integrate into the most relevant guide.
   - Do not apply to a large number of additional finance programmes until current approvals/rejections are known.

3. Expand monetised guide coverage
   - Business insurance guide.
   - Landlord insurance / property cost guide.
   - Business bank accounts guide.
   - Mortgage / remortgage guide.
   - Savings / ISA guide.
   - Energy / home-cost guide.
   - Credit card guide only after site trust and approvals improve.

4. Increase guide visibility carefully
   - Homepage guide exposure should remain useful and non-intrusive.
   - Article-to-guide links should remain context-aware.
   - Avoid aggressive mid-article blocks that hurt reader experience.

5. Measure and optimise provider order
   - Use `guide_provider_click` data to identify which providers receive clicks.
   - Reorder guide providers based on actual click-through once enough data exists.
   - Promote top performers to top CTA; demote or remove weak providers.

6. Continue homepage quality monitoring
   - Watch for planning/property clusters returning.
   - Preserve useful local economic, retail, jobs, infrastructure and business-development stories.
   - Continue blocking crime/court/incident churn, soft lifestyle filler, adult/sensitive filler, animal/zoo filler and low-value entertainment stories.

7. Source-of-truth update protocol
   - Continue appending major-day updates to this file only.
   - Do not delete or compact older notes.
   - If file size becomes too large, start a continuation file rather than removing prior details.

### 16.16 Next-chat continuation instruction

Use this continuation instruction for the next chat:

`Continue Cheshire Today from PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260428_v12_FULL.md with the May 2026 append applied through section 16. Treat the file as append-only. Respect workflow: check current state first, no manual file edits, one command at a time, verify after each change, use grep not rg, avoid npm start, build frontend with REACT_APP_BACKEND_URL=https://cheshiretoday.co.uk npm --prefix frontend run build, and remember Render auto-deploy is disabled so manual deploys are required. Current major state: homepage has been rebalanced to lead with business/finance/economic value; pure planning/housing approvals are downranked unless they include business/jobs/retail/investment impact; RSS sync filtering now blocks low-value incident/animal/tabloid filler unless economic; live pool was manually cleaned of Pornhub/adult, crime/incident, animal/zoo and soft lifestyle stories; parcel/courier guide is fully monetised with tracked Awin links for Parcel ABC, DHL eCommerce UK and Interparcel; provider-level authority-guide click tracking is live through dataLayer using guide_provider_click; top CTA tracking was fixed after slug/page scope errors; GA may be blocked by browsers, so backend click logging is the next recommended technical upgrade. Awin applications pending: AXA Business Insurance, AXA Landlord Insurance, QuoteSearcher, Heatable, Mymoneycomparison and Hiscox. Next highest-value tasks: implement backend guide-click tracking, monitor Awin approvals, integrate first approved finance/insurance partner into a guide, and increase guide visibility without intrusive UX.`


---

# 17. MAY 2026 FULL CHAT ADDENDUM — FACEBOOK TASKS, FILTERING, HOMEPAGE, AFFILIATES, GUIDE TRACKING AND REMAINING TASKS

This section is a fuller append-only correction/addendum to capture the complete working sequence from the latest chat after the previous state-file update. It preserves the existing project history and adds the missing details, including operational tasks, affiliate applications, guide optimisation, article filtering, deployments, testing outcomes and outstanding work.

## 17.1 Facebook automation review and task-status check

The user asked to check whether the existing Facebook tasks still run daily and whether they could open in a new chat because the old reminder chat had become very slow.

Current active daily Facebook automations were reviewed and confirmed:

- `Prepare morning Facebook post`
  - Active daily at 07:30 Europe/London.
  - Prompt searches Cheshire Today for the best morning article and one Reel idea.
  - Prioritises council tax, household bills, mortgages, rent, savings, jobs, Cheshire business openings/closures, property/planning, useful AI tools and practical local guides.
  - Avoids crime-heavy filler and generic link-only posts.

- `Create daily Facebook Reel`
  - Active daily at 09:30 Europe/London.
  - Prompt searches Cheshire Today for the best article for a Facebook Reel.
  - Uses article image as 9:16 background, slow zoom/pan, 3 overlays, 7–12 seconds, caption with article link and question, plus pinned comment suggestion.

- `Engage Facebook comments`
  - Active daily at 12:30 Europe/London.
  - Prompt reminds user to reply to comments, like useful comments, ask a short follow-up question and consider one optional breaking extra post only if genuinely strong.

- `Prepare evening Facebook post`
  - Active daily at 18:30 Europe/London.
  - Prompt searches Cheshire Today for the strongest after-work/evening Facebook post.
  - Prioritises household money, local business, property, tax, jobs, AI tools, useful guides and Cheshire economic/local impact.

Issue identified:

- Opening the reminder notification links back to the original old chat where the task was created, causing slow loading.
- This is a limitation of reminder threading rather than a project bug.

Operational workaround agreed:

- Treat reminders as alerts only.
- Execute the task in a new chat using a stateless prompt.
- The new-chat prompt provided was:

```text
Continue Cheshire Today Facebook automation task setup. I want the daily Facebook reminders to act as alerts only, and each task should tell me to open a new chat with a clean, fast prompt. Please review and optimise the 4 Facebook tasks: morning post, daily Reel, comment engagement, evening post.
```

Remaining Facebook task work:

- In a new chat, rewrite the four Facebook automation prompts so each reminder explicitly says to open a new chat and paste/run a clean prompt.
- Keep task prompts stateless, shorter and faster.
- Continue using the user’s requested post package standard: article link in caption, link again in pinned/first comment where suitable, optional Story share text, optional first-comment engagement prompt and potential comment replies.

## 17.2 Article filtering review from chat-source files and strategy confirmation

The user asked to check all available chat-source files rather than relying only on the master file.

Strategy confirmed from uploaded files:

- Cheshire Today should stay aligned to Business, AI, Finance, Property and Tax.
- Affiliate-first monetisation remains the primary model.
- Commercial guides and comparison pages are the core income engine.
- Competitor reports show local crime/court/sports/lifestyle can drive traffic for competitors, but Cheshire Today’s differentiation is economic intelligence, business, finance, property utility, local economic impact and practical guides.
- Some local/property/lifestyle content can remain if it supports high-value audiences, advertisers or monetisation; random filler should not.

Filtering principle reaffirmed:

Hard block or archive:

- Crime/court/police churn.
- Incident/crash/emergency filler.
- Death notices/obituaries/funeral notices.
- Sports.
- Adult/sensitive filler.
- Generic entertainment/showbiz.
- Animal/zoo/nature filler when not economically relevant.
- Emotional tabloid items.
- Soft lifestyle pieces without economic, business, property, finance, jobs or utility value.

Allow or preserve:

- Cheshire local business impact.
- Jobs and employment impact.
- Retail openings/closures where economic.
- Property/planning only when useful and not over-dominant.
- Finance, tax, savings, mortgage, rent, energy and household-cost content.
- AI/technology/business-policy content.
- Local infrastructure, councils, regeneration and business-relevant developments.

## 17.3 Filtering code inspection and diagnosis

The active code was inspected with grep and specific server sections.

Filtering layers identified:

- RSS hybrid import around `backend/server.py` lines around 1875–2022.
- Local/Cheshire RSS import around lines around 2160–2190.
- Homepage/display filtering around lines around 3332–3681.
- Sync ingestion filtering around lines around 11620–11825.
- Digest filtering around lines around 12215 and later blocks.

Important findings:

- Main hybrid import path already hard-blocks crime, obituary and low-utility filler.
- Local RSS path also hard-blocks crime, obituary and low-utility filler.
- Sync ingestion path was the likely leak because it had strong title/category checks but still allowed some low-value incident, animal/zoo and tabloid items through.
- The homepage/live pool also contained older already-imported items that predated stricter rules.

A live article audit was run using `/api/articles?limit=120` and later `/api/articles?limit=200`.

Initial suspected issue:

- The scan falsely flagged one Vodafone article because a broad regex matched `tv` inside `Vodafone`.
- This confirmed the need to avoid overly broad filtering.

## 17.4 Live article pool cleanup and manual archives

The user shared homepage screenshots showing misaligned items.

Clear bad items identified and archived included:

- `Pornhub to become accessible again for some UK users`
  - ID: `69fa27563613d71e86b827cf`
  - Reason: adult/sensitive/off-strategy.

- `Driver 'pulled from vehicle' on Cheshire A34 after hitting tree`
  - ID: `69f880a8da2d800fcf255eec`
  - Reason: incident/crash churn.

- `Thieving Carl BANNED from Crewe Tesco, Morrisons and Hobbycraft`
  - ID: `69f880e3da2d800fcf255eef`
  - Reason: crime/court-style local churn.

- `Driver, 19, in hospital after crashing into tree on Cheshire A-road`
  - ID: `69fa27bb3613d71e86b827d4`
  - Reason: incident/crash churn.

- `Wildlife park welcomes three male Asiatic lions`
  - ID: `69f9d274da2d800fcf255f3b`
  - Reason: wildlife/zoo filler.

- `'I had to pay £14k after my cat was run over'`
  - ID: `69f8d4aada2d800fcf255eff`
  - Reason: emotional/tabloid animal story.

- `How to write a James Bond song - from the man who knows best`
  - ID: `69f6dae5f9397ed7f094dfd4`
  - Reason: entertainment filler.

- `German museum to return rare Irritator dinosaur skull to Brazil`
  - ID: `69f5dd6bf1fc31aa2606a33c`
  - Reason: dinosaur/filler.

- `Endangered antelopes flown to Kenya from Czech zoo in 'historic homecoming'`
  - ID: `69f1e8c89646626d371d6f57`
  - Reason: animal/zoo filler.

- `£20m mystery gift buys London Zoo new hospital where you can watch vets work`
  - ID: `69f1947136e8112381d99789`
  - Reason: zoo filler.

Additional weak local/lifestyle items archived after full homepage audit:

- `Cheshire festival returns for second year after 'huge' debut success`
  - ID: `69f880d6da2d800fcf255eee`
  - Reason: soft local lifestyle.

- `The Cheshire ice cream drive-in with golf buggies bringing treats to your car`
  - ID: `69f5dde0f1fc31aa2606a343`
  - Reason: soft lifestyle/filler.

- `Ellesmere Port woman 'in state of panic' after beach visit ends in rescue from rising tide`
  - ID: `69f4e089c49c818a0402d2ff`
  - Reason: rescue/incident soft news.

- `The Ivy launches limited edition menu for Chester Races`
  - ID: `69f48c2fc49c818a0402d2e6`
  - Reason: soft lifestyle/restaurant/event filler.

Further weak top-30 items archived:

- `Gap co-founder Doris Fisher dies aged 94`
  - ID: `69fa27213613d71e86b827cb`
  - Reason: obituary-style business filler.

- `A game-changer for good health? Scientists believe ‘we are when we eat’ | Devi Sridhar`
  - ID: `69f9d254da2d800fcf255f39`
  - Reason: health/opinion filler.

- `The Cheshire garden centre with £3 train rides to secret play area`
  - ID: `69f783c4f9c180770e944181`
  - Reason: soft lifestyle.

- `Tatton Park dog rule change announced following death of lambs`
  - ID: `69f6db58f9397ed7f094dfda`
  - Reason: animal/local soft story.

- `The Cheshire garden centre with miniature railway and tearoom`
  - ID: `69f5ddb8f1fc31aa2606a341`
  - Reason: soft lifestyle.

Items intentionally kept despite scanner hits:

- `Inside Chester's new-look Northgate Arena after multi-million pound revamp`
  - Local investment/infrastructure.

- `Companies pay out to charity after slurry incidents`
  - Environmental/business/regulatory relevance.

- `Lidl announces 23 Cheshire store target locations for 2026 - full list`
  - Retail/jobs/local economic relevance.

- `Tatton Park dog rule change...` was initially considered possibly useful but later archived during stricter top-30 cleanup.

- `Nasa brought crashing down to earth as budget threat follows lunar success`
  - Tech/budget/authority.

- `Billions of meals at risk due to Iran war, says fertiliser boss`
  - Business/economy/food supply risk.

- Musk/Altman court/business stories
  - AI/business/legal relevance.

- Renters’ Rights, interest rates, Rachel Reeves tax and finance pieces
  - Directly aligned with finance/household-money strategy.

## 17.5 RSS sync filter tightening

The sync ingestion filter was updated in `backend/server.py`.

Purpose:

- Block low-value incident, animal/zoo and tabloid filler at sync ingestion.
- Preserve economic/business/local-utility stories.

Patch added around the sync filter after `sync_low_utility_kw`:

```python
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
```

Important debugging note:

- First attempt referenced `econ_kw` before it was defined.
- Fixed by adding local `sync_econ_kw` in the same scope.
- `python3 -m py_compile backend/server.py` passed.

Commit pushed/deployed:

- `c14a73e Tighten RSS sync filter for low-value incident and animal filler`

Backend health check after deploy returned healthy.

## 17.6 Homepage audit and rebalancing

The user asked for a full homepage/category review because Latest felt too planning/housing-heavy and did not feel enough like the project goal.

Live audit result before deeper cleanup/rebalance:

- Total: 121 articles.
- Category counts included roughly:
  - Tech: 35–37
  - Business: 32–33
  - Local News: 31–34
  - Finance: 19
  - UK News: 1

Issue discovered:

- Counts were not necessarily bad, but ordering was wrong.
- `Latest` visually felt too local/planning-heavy because the existing frontend logic deliberately pushed Local first.

Existing `Latest` logic found in `frontend/src/pages/HomePageV1.jsx`:

- Target: 4 Local, 4 Business/Finance, 3 AI/Tech, 1 UK.
- Previous order:
  - Pass 1: Local (4)
  - Pass 2: Business/Finance (4)
  - Pass 3: AI/Tech (3)
  - Pass 4: UK (1)

This meant the top row/first impression looked like a local planning site even when total mix was balanced.

Safe change implemented:

- Reordered Latest passes so Business/Finance comes first, then Local.
- Kept the same intended 4/4/3/1 balance.
- This preserved prior structure instead of rewriting homepage logic.

Updated order:

- Pass 1: Business/Finance (4)
- Pass 2: Local (4)
- Pass 3: AI/Tech (3)
- Pass 4: UK (1)

Additional refinement:

- Sorting alone did not remove planning from top row because planning/housing items were classified as business/economic and scored too high.
- `rankScore()` was modified to penalise pure planning/housing approvals from top positions while preserving business-impact developments.

Final ranking penalty implemented in `frontend/src/pages/HomePageV1.jsx`:

```js
// Penalise pure planning / housing approvals from dominating top positions.
// Keep jobs/warehouse/retail/business-impact developments competitive.
const planningText = (String(a?.title || "") + " " + String(a?.summary || "")).toLowerCase();
const isPlanningOnly = /(planning|housing|estate|new homes|approved|approval|application|apartments|flats)/.test(planningText);
const hasBusinessImpact = /(jobs?|warehouse|retail|business|factory|investment|town centre|store|stores|employment)/.test(planningText);
if (isPlanningOnly && !hasBusinessImpact) {
  score -= 320;
}
```

Build/debug notes:

- Initial patch caused `git diff --check` trailing whitespace at `HomePageV1.jsx:426`; whitespace was stripped with a Python line-rstrip command.
- Initial patch caused duplicate variable error: `Identifier 't' has already been declared`.
- Fixed by using `planningText` instead of `t`.
- Frontend builds passed after fixes.

Visual result confirmed by screenshot:

- Top row shifted from planning/housing to:
  - `Two pubs closing every day after 'sheer weight' of tax rises`
  - `UK long-term borrowing costs reach 28-year high`
  - `What an empty car park tells us about the UK's debt problem`
- Pure planning no longer dominated the first row.
- Local planning still appeared lower down, which is acceptable.

Commits pushed/deployed:

- `73bd264 Downrank pure planning items in homepage ranking`

## 17.7 Homepage guide strip and article guide targeting work already completed in this chat sequence

Earlier in this chat sequence before the filtering and Awin work, the homepage guide/monetisation strip and article guide targeting were improved.

Completed commits included:

- `879c911 Refine homepage monetisation strip trust label`
  - Changed homepage monetisation strip label from `Deal` to `Guide`.

- `6b3650c Add homepage guide strip framing`
  - Added homepage guide strip framing and clearer guide wording.

- `471d4aa Make homepage guide titles intent-led`
  - Rewrote homepage guide titles from generic `Best...` wording into reader-intent titles.
  - Examples:
    - `Starting a business? Secure your domain`
    - `Need a website? Compare builders`
    - `Running a business? Compare accounting tools`

- `9f72e13 Differentiate homepage guide strip framing`
  - Added configurable eyebrow/title props for homepage guide strips.
  - Second strip changed to `Popular guides` / `More practical next steps`.

- `6dd684a Expand homepage guide rotation with household finance options`
  - Added household finance guide cards to `homepage_primary`:
    - `Mortgage due soon? Compare rates`
    - `Savings sitting idle? Compare accounts`
    - `Bills rising? Check energy deals`

- `507ed77 Strengthen finance guide targeting for article conversion`
  - Strengthened article guide targeting so mortgage, savings, credit and energy contexts push more relevant finance guides.

- `4ba9af6 Expand property/tax guide targeting for better household conversion`
  - Added mortgage-rate guide into property/tax context.

- `9bdd6d4 Improve business fallback guide targeting with banking option`
  - Added business bank accounts to business fallback guide stack.

- `a91b5a1 Remove unused article guide split logic`
  - Removed old `beforeGuideContent` / `afterGuideContent` split logic that had caused intrusive mid-article guide placements.

- `2da06bf Track homepage guide clicks`
  - Added `guide_click` tracking to homepage guide-strip cards.

- `b880dd1 Track article guide clicks`
  - Added `guide_click` tracking to article guide blocks.

- `7f0ab76 Prioritise finance guides in primary homepage strip`
  - Added `focus="finance"` support to `HeroMonetisationStrip`.
  - First homepage guide strip now rotates finance/household cards first.

These were pushed/deployed across the session and verified with builds and/or live checks.

## 17.8 DHL eCommerce Awin affiliate integration

The user received affiliate approval text for DHL eCommerce via Awin:

- 9% commission for new customers.
- 1.3% for existing customers.
- 30-day cookie window.
- Contact: Chris at `chris@makeitsoconsultants.com`.

Destination URL selected:

```text
https://www.dhl.com/gb-en/home/our-divisions/ecommerce/solutions.html
```

DHL Awin tracking link generated by user:

```text
https://www.awin1.com/cread.php?awinmid=121764&awinaffid=2844510&clickref=ct-dhl-ecommerce-parcel-guide&ued=https%3A%2F%2Fwww.dhl.com%2Fgb-en%2Fhome%2Four-divisions%2Fecommerce%2Fsolutions.html
```

Guide updated:

- `best-parcel-courier-services-small-business-uk`

Current provider stack after DHL insertion and reordering:

1. Parcel ABC UK
2. DHL eCommerce UK
3. Interparcel

DHL tool section added via admin authority-page upsert with:

- Type: `tool`
- Name: `DHL eCommerce UK`
- Rating: `4.5`
- Affiliate link: Awin tracked link above.
- Content initially positioned as direct courier/reliability/brand-trust option.

Important API note:

- First attempted `sections_append` failed because `/api/admin/authority-pages/upsert` requires full payload including `title`.
- Correct method was to fetch current guide JSON, modify `sections`, then POST full payload with slug/title/category/monetisation/status/sections.

## 17.9 Interparcel Awin tracking fix

Interparcel was confirmed to be on Awin.

Current problem:

- Interparcel initially used raw direct URL:

```text
https://www.interparcel.com/
```

This was revenue leakage because clicks were not tracked.

User first generated an incorrect Awin link where `clickref` contained the destination URL. This was rejected as analytically bad because `clickref` needs to be a clean internal reference.

Correct Interparcel Awin link generated:

```text
https://www.awin1.com/cread.php?awinmid=32851&awinaffid=2844510&clickref=ct-interparcel-parcel-guide&ued=https%3A%2F%2Fwww.interparcel.com%2F
```

The guide was updated via API to replace Interparcel direct link with the Awin link.

Verification confirmed all three parcel-guide provider links are now tracked through Awin:

1. Parcel ABC UK — tracked via Awin.
2. DHL eCommerce UK — tracked via Awin.
3. Interparcel — tracked via Awin.

## 17.10 Parcel/courier guide optimisation

The user asked to optimise the parcel guide.

Guide:

- `best-parcel-courier-services-small-business-uk`

Old tool descriptions were inspected and then rewritten into decision-first copy.

Final live provider copy:

- `Parcel ABC UK`
  - `Best for price comparison: compare parcel delivery quotes across couriers before booking. Useful for small businesses that want to check costs quickly before choosing a service.`

- `DHL eCommerce UK`
  - `Best for reliability and scale: a strong direct courier option for businesses that need trusted UK and international delivery, consistent tracking and brand recognition.`

- `Interparcel`
  - `Best overall multi-carrier option: useful for small businesses that want access to several courier services from one platform rather than managing separate carrier accounts.`

Current live order:

1. Parcel ABC UK — best for price comparison.
2. DHL eCommerce UK — best for reliability and scale.
3. Interparcel — best overall multi-carrier option.

Strategic note:

- The parcel/courier guide is now the first fully monetised and conversion-ready test page.
- It should be used as the benchmark for future guide monetisation and tracking work.

## 17.11 Authority guide provider click tracking

Goal:

- Track which guide provider buttons are clicked.
- Capture provider, guide slug, position and destination.
- Use data to reorder providers and optimise revenue.

Initial check found no backend guide-click endpoint.

Decision:

- Use the existing frontend `trackEvent` helper and dataLayer/GA first.
- Backend/internal click logging remains a later priority.

Frontend work:

- `AuthorityPage.jsx` imported `trackEvent`.
- Provider-card `Visit provider` buttons were updated to emit:

```js
trackEvent("guide_provider_click", {
  guide: slug,
  provider: name,
  position: idx + 1,
  destination: link,
})
```

Commit:

- `9d462cc Track authority guide provider clicks`

Issue discovered during live testing:

- There were two `Visit provider` button locations in `AuthorityPage.jsx`:
  - top/main provider CTA around lines 147–154.
  - card CTA around lines 740–752.
- Only card CTA was initially tracked.
- User likely clicked the top CTA, so `window.dataLayer.filter(x => x && x.event === "guide_provider_click")` returned `[]`.

Top CTA tracking was added.

First top CTA attempt used `slug`, causing:

```text
ReferenceError: Can't find variable: slug
```

Second attempt used `page?.slug`, causing:

```text
ReferenceError: Can't find variable: page
```

Final working fix:

- Top CTA now uses the current URL path:

```js
onClick={() => trackEvent("guide_provider_click", {
  guide: window.location.pathname.replace("/guides/", ""),
  provider: name,
  position: 1,
  destination: link,
  placement: "top_pick",
})}
```

Commits/deploys involved:

- `c407465 Track authority guide top provider CTA clicks`
- `8928abb Fix top provider CTA tracking guide slug`
- Final scope fix after `8928abb` used `window.location.pathname.replace("/guides/", "")`; verify exact hash in repo with `git log -5 --oneline` if needed because it was committed/pushed/deployed after the `page` scope error.

Live test result:

- After final deploy, running:

```js
window.dataLayer.filter(x => x && x.event === "guide_provider_click")
```

returned:

```text
[Object] (1)
```

This confirmed provider-click tracking is now firing.

## 17.12 GA/browser blocking diagnosis

During tracking tests, browser console showed:

```text
Blocked connection to known tracker https://www.googletagmanager.com/gtag/js?id=G-Q1NZLJC50D
```

Diagnosis:

- This is caused by browser/device privacy protection, not broken website code.
- Likely causes include Safari cross-site tracking prevention, iOS privacy protections, ad/content blockers, Private Relay/DNS filtering, Brave/Firefox protections, AdGuard/NextDNS/Pi-hole/NordVPN threat protection.

Important conclusion:

- `window.dataLayer` receiving `guide_provider_click` confirms frontend tracking code works.
- GA delivery can still be blocked by some browsers.
- Backend/internal click logging is needed for reliable first-party analytics.

## 17.13 Awin finance/insurance affiliate applications

The user wanted to return to Awin and apply for finance affiliates, especially categories without links such as mortgage, credit cards, savings, insurance and home-cost guides.

Awin listing supplied by user included many finance/insurance/home/travel/business options.

Application strategy:

- Do not mass-apply to dozens of programmes.
- Apply strategically to highly relevant programmes first.
- Build credibility through coherent verticals.
- Avoid credit cards/SIPP/big banks for now until site trust/approvals improve.

Promotion type advice:

- Use the website `cheshiretoday.co.uk` as primary promotion.
- Select Website / Content / Editorial / Blog if available.
- Avoid cashback, incentive, email-only and PPC unless actually used.

Short description format was needed because Awin allowed only 255 characters.

Applications submitted and pending:

1. `AXA Business Insurance`
   - Reason: strong fit for business insurance guide, small business audience and high brand trust.
   - Listed EPC observed by user: GBP 8.25.
   - 255-char description used:

```text
Cheshire Today is a UK local business and finance publication. We create editorial guides on insurance, money and business services, promoted via SEO, newsletter and Facebook to UK readers making practical financial decisions.
```

2. `AXA Landlord Insurance`
   - Reason: fits property, rental market and landlord finance content.
   - Status: pending.
   - Description:

```text
UK publication covering business, property and finance. We publish landlord, housing and money guides for UK readers, promoted via SEO, newsletter and Facebook to users making practical financial and property decisions.
```

3. `QuoteSearcher`
   - Reason: comparison/aggregator layer; easier approval than banks; useful for insurance/utilities/finance comparisons.
   - Status: pending.
   - Description:

```text
UK business and finance publication. We create comparison-style guides covering insurance, utilities and money products, promoted via SEO and Facebook to UK users actively comparing financial services and providers.
```

4. `Heatable`
   - Reason: home-cost/boiler/energy angle; very relevant to UK household cost and energy content.
   - Status: pending.
   - Description:

```text
UK business and finance publication covering household costs, energy and property. We publish practical guides on boilers, energy bills and home costs, promoted via SEO and Facebook to UK users making cost-saving decisions.
```

5. `Mymoneycomparison`
   - Reason: bridge into savings, loans and consumer finance comparisons.
   - Status: pending.
   - Description:

```text
UK business and finance publication. We create comparison-style guides covering savings, loans and financial products, promoted via SEO and Facebook to UK users actively comparing finance options and services.
```

6. `Hiscox Underwriting Group Services Ltd`
   - Reason: premium UK business insurer and useful backup/complement to AXA.
   - Status: pending.
   - Description:

```text
UK business and finance publication focused on small business and economic content. We publish practical guides on business services including insurance, promoted via SEO and Facebook to UK business owners and decision-makers.
```

Instruction agreed:

- Stop applying after these six pending applications.
- Wait for first approvals/rejections.
- Integrate approved programmes immediately into relevant guides.
- Avoid applying to too many programmes at once to reduce rejection risk.

## 17.14 Current pushed/deployed commits from this working sequence

Known commits pushed and deployed during this full chat sequence include:

```text
879c911 Refine homepage monetisation strip trust label
6b3650c Add homepage guide strip framing
471d4aa Make homepage guide titles intent-led
9f72e13 Differentiate homepage guide strip framing
6dd684a Expand homepage guide rotation with household finance options
507ed77 Strengthen finance guide targeting for article conversion
4ba9af6 Expand property/tax guide targeting for better household conversion
9bdd6d4 Improve business fallback guide targeting with banking option
a91b5a1 Remove unused article guide split logic
2da06bf Track homepage guide clicks
b880dd1 Track article guide clicks
7f0ab76 Prioritise finance guides in primary homepage strip
c14a73e Tighten RSS sync filter for low-value incident and animal filler
9d462cc Track authority guide provider clicks
73bd264 Downrank pure planning items in homepage ranking
c407465 Track authority guide top provider CTA clicks
8928abb Fix top provider CTA tracking guide slug
```

There was one later commit after `8928abb` to fix top CTA tracking scope by replacing `page?.slug` with `window.location.pathname.replace("/guides/", "")`. Verify exact hash with:

```bash
git log -5 --oneline
```

Deployment notes:

- Manual Render frontend/backend deploys were performed after pushes.
- Backend health checks returned:

```json
{
  "status": "healthy",
  "service": "cheshire-news"
}
```

- Render auto-deploy remains disabled; manual deploys are required.

## 17.15 Current live system state after this chat

Homepage:

- First impression is now more economic/business/finance-led.
- Pure planning/housing approvals are penalised unless they include business/jobs/warehouse/retail/investment/employment impact.
- Local utility remains, but should no longer dominate top Latest row.
- Business/Finance now leads the Latest mix.

Content filtering:

- RSS sync now blocks more incident/animal/tabloid filler unless economic relevance exists.
- Live pool was manually cleaned of several adult, crime, incident, animal/zoo, lifestyle and entertainment items.
- Continue monitoring new imports because edge cases can still slip through.

Guides/affiliate:

- Parcel/courier guide is fully monetised and conversion-ready.
- Parcel ABC, DHL eCommerce UK and Interparcel all have Awin links.
- Provider order/copy has been optimised.
- Authority guide provider clicks are tracked via `guide_provider_click` in `window.dataLayer`.

Tracking:

- Homepage guide clicks and article guide clicks use `guide_click`.
- Authority provider button clicks use `guide_provider_click`.
- Top provider CTA and provider card CTA are both tracked after fixes.
- GA may be blocked by some browsers; dataLayer event firing is confirmed.

Awin:

- Six applications pending:
  - AXA Business Insurance.
  - AXA Landlord Insurance.
  - QuoteSearcher.
  - Heatable.
  - Mymoneycomparison.
  - Hiscox.

Facebook tasks:

- Morning post, daily Reel, comment engagement and evening post automations are active.
- Need a new-chat/stateless prompt refresh to avoid old-chat slowdown.

## 17.16 Remaining tasks and backlog after this chat

### Immediate high-priority tasks

1. Verify exact latest git state

```bash
git status --short && git log -8 --oneline
```

Purpose:

- Capture exact hash of the final top CTA tracking scope fix after `8928abb`.
- Confirm local = origin.

2. Implement backend/internal provider-click tracking

Reason:

- GA/dataLayer is useful but not reliable because browsers can block Google Tag Manager/GA.

Recommended endpoint:

```text
POST /api/track/guide-click
```

Suggested payload:

```json
{
  "guide": "best-parcel-courier-services-small-business-uk",
  "provider": "DHL eCommerce UK",
  "position": 2,
  "placement": "tool_card",
  "destination": "https://www.awin1.com/..."
}
```

Suggested MongoDB collection:

```text
guide_click_events
```

Fields:

- guide
- provider
- position
- placement
- destination_domain
- timestamp
- user_agent (optional)
- referrer (optional)

3. Monitor Awin approvals daily

When any approval arrives:

- Create or update matching guide.
- Generate correct Awin tracking link using clean `clickref`.
- Insert provider into relevant guide using full authority-page upsert payload.
- Verify live guide API.
- Test outbound link.
- Check provider-click tracking.

4. Integrate first approved finance/insurance partners

Priority mapping:

- AXA Business or Hiscox → business insurance guide.
- AXA Landlord → landlord/property insurance guide.
- Heatable → energy/home-cost/boiler guide.
- QuoteSearcher → comparison guide and possibly insurance comparison layer.
- Mymoneycomparison → savings/loans/finance comparison layer.

5. Continue homepage quality monitoring

Check after next import cycle:

- Top Latest row should remain finance/business/economic.
- Planning/housing should not dominate.
- Soft local/lifestyle should not return.
- Crime/incident/adult/animal/zoo filler should stay out.

Useful audit command pattern:

```bash
curl -sS "https://cheshiretoday.co.uk/api/articles?limit=120" -o /tmp/ct_home_audit.json
```

Then review category/theme counts and first 30 items.

### Medium-priority tasks

6. Optimise parcel guide further after data

After 20–50 provider clicks:

- Compare provider CTR by position.
- Promote highest-click provider to top CTA.
- Consider badges:
  - Best for price comparison.
  - Best for reliability.
  - Best overall multi-carrier.
- Avoid layout-heavy redesign until data exists.

7. Increase guide visibility carefully

Potential actions:

- Add non-intrusive guide exposure on homepage.
- Improve context-aware article-to-guide routing.
- Keep article body clean; avoid intrusive mid-article blocks.
- Use sidebar/below-article placements rather than aggressive inline blocks.

8. Rework Facebook automation prompts in a new chat

Goal:

- Keep reminders as alerts only.
- Each reminder tells user to open a new chat.
- Each prompt should be shorter, stateless and faster.

Tasks to update:

- Morning Facebook post.
- Daily Facebook Reel.
- Comment engagement.
- Evening Facebook post.

9. Continue monetised guide expansion

Priority guide candidates:

- Best business insurance UK.
- Best landlord insurance UK.
- Best boiler replacement / home heating cost guide.
- Best business bank accounts UK.
- Best savings accounts UK.
- Best mortgage/remortgage brokers UK.
- Best credit cards UK later, once approvals/site trust improve.

10. Add provider-level analytics view in admin later

Useful metrics:

- Guide views.
- Provider clicks.
- CTR per provider.
- CTR by placement.
- Top providers last 7/30 days.
- Affiliate clickref mapping.

### Lower-priority / later tasks

11. Reassess homepage high-intent finance boost

Potential future `rankScore()` addition:

```js
if (/(interest rate|mortgage|savings|isa|tax|inflation|cost of living)/.test(t)) {
  score += 120;
}
```

Do not add immediately; first observe current homepage for 24–48 hours.

12. Review remaining active articles for soft Tech/science filler

Some Tech items remain science/health/nature-adjacent. Keep only if:

- AI/technology/business-policy relevance exists.
- Finance/economic impact exists.
- It supports authority.

13. Continue avoiding sports category

User has previously decided Sports is not needed. Future filtering/category work should continue to avoid Sports rather than preserving it.

## 17.17 Next-chat continuation instruction

Use this instruction in the next chat:

```text
Continue Cheshire Today from PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260428_v12_FULL.md with the May 2026 full addendum through section 17 applied. Treat the file as append-only. Respect workflow: check current state first, no manual file edits, one command at a time, verify after each change, use grep not rg, avoid npm start, build frontend with REACT_APP_BACKEND_URL=https://cheshiretoday.co.uk npm --prefix frontend run build, and remember Render auto-deploy is disabled so manual deploys are required. Current major state: homepage has been rebalanced to lead with business/finance/economic value; pure planning/housing approvals are downranked unless they include business/jobs/retail/investment/employment impact; RSS sync filtering blocks low-value incident/animal/tabloid filler unless economic; live pool was manually cleaned of adult/sensitive, crime/incident, animal/zoo, soft lifestyle and entertainment stories; parcel/courier guide is fully monetised with tracked Awin links for Parcel ABC, DHL eCommerce UK and Interparcel; provider-level authority-guide click tracking is live via dataLayer using guide_provider_click; top CTA tracking was fixed after slug/page scope errors using window.location.pathname; GA may be blocked by privacy tools, so backend/internal guide-click logging is the next technical priority. Awin applications pending: AXA Business Insurance, AXA Landlord Insurance, QuoteSearcher, Heatable, Mymoneycomparison and Hiscox. Facebook automations are active but should be rewritten as new-chat/stateless reminder prompts. Next highest-value tasks: verify latest git hash/status, implement backend guide-click tracking, monitor Awin approvals, integrate the first approved finance/insurance partner into a guide, and increase guide visibility without intrusive UX.
```

---

# 📅 SESSION LOG — MAY 2026 FULL OPERATIONAL UPDATE

## Scope of this appended update
This update records the complete working session since the previous source-of-truth update. It covers Facebook task handling, article filtering, homepage feed rebalancing, Awin affiliate applications, DHL/Interparcel affiliate setup, parcel guide optimisation, provider click tracking, debugging, commits, deployments, current state, and outstanding tasks.

---

## 1. Facebook task/reminder workflow review

### Issue identified
The daily Facebook automation reminders were still opening an older heavy chat, which was slow to load and inefficient for daily execution.

### Existing active Facebook-related automations confirmed
The scheduled tasks currently active include:

- **Prepare morning Facebook post** — daily at 07:30 Europe/London.
- **Create daily Facebook Reel** — daily at 09:30 Europe/London.
- **Engage Facebook comments** — daily at 12:30 Europe/London.
- **Prepare evening Facebook post** — daily at 18:30 Europe/London.

### Operational decision
The reminders should be treated as **alerts only**. The actual Facebook task should be executed in a new chat to improve speed and avoid loading the old long thread.

### Recommended new-chat instruction provided
The user was advised to start a new chat and paste a prompt requesting optimisation of the 4 daily Facebook tasks so they act as alerts and provide clean, fast prompts.

### Ongoing Facebook content preference reaffirmed
Future Facebook post packages should include:

- Article link in caption.
- Same link again in pinned/first comment where appropriate.
- Optional Facebook Story share text.
- Optional first-comment engagement prompt.
- Potential comment replies for common reader reactions.
- Clean Meta posting style; avoid overcrowding posts.

---

## 2. Homepage monetisation strip and guide targeting work completed earlier in this session

### Commits completed and deployed during this session
The following homepage/article monetisation changes were committed and deployed before the later filtering/affiliate work:

- `879c911` — Refine homepage monetisation strip trust label.
- `6b3650c` — Add homepage guide strip framing.
- `471d4aa` — Make homepage guide titles intent-led.
- `9f72e13` — Differentiate homepage guide strip framing.
- `6dd684a` — Expand homepage guide rotation with household finance options.
- `507ed77` — Strengthen finance guide targeting for article conversion.
- `4ba9af6` — Expand property/tax guide targeting for better household conversion.
- `9bdd6d4` — Improve business fallback guide targeting with banking option.
- `a91b5a1` — Remove unused article guide split logic.
- `2da06bf` — Track homepage guide clicks.
- `b880dd1` — Track article guide clicks.
- `7f0ab76` — Prioritise finance guides in primary homepage strip.

### Homepage guide strip changes
The homepage monetisation guide rotation was changed so the primary homepage strip can use a `focus="finance"` prop. This makes the first guide strip favour household finance cards such as:

- Mortgage rates.
- Savings accounts.
- Energy deals / bills.

The second guide strip remains broader, allowing business tools and household finance to rotate without making the homepage feel sales-heavy.

### Guide rotation behaviour confirmed
The guide strip uses deterministic daily UTC rotation. This means a card such as “Bills rising? Check energy deals” may not appear every day, but remains in the rotation.

### Article guide targeting improved
Article page guide targeting was strengthened so relevant articles push better guide choices:

- Mortgage context now pushes mortgage, savings, and ISA guides.
- Savings context now pushes savings, ISA, and mortgage guides.
- Credit context now pushes credit cards, business credit cards, and savings.
- Energy context now pushes energy tariffs, broadband deals, and savings.
- Tax/property context now pushes cost-of-buying-home, council tax, and mortgage rates.
- Business fallback now includes business bank accounts before accounting/domain/email tools.

### Dead article guide split logic removed
An old `beforeGuideContent` / `afterGuideContent` mid-article split block was removed because it was unused and previously contributed to intrusive article splitting. This preserves the cleaner article-body experience.

---

## 3. Article filtering and cleanup investigation

### Strategy reviewed from source files
The project source files confirm the platform should follow the Business, AI, Finance, Property, and Tax positioning, with affiliate-first monetisation and high-quality commercial comparison pages as the core income engine. The platform should not behave like a generic local crime/lifestyle feed.

Competitor reports show that crime/court/lifestyle content can drive traffic for other publishers, but Cheshire Today’s differentiation should be business, finance, property, useful local economic content, guides, directories, jobs and monetisation-aligned local utility.

### Live article pool audit performed
The live `/api/articles?limit=80`, `/api/articles?limit=120`, and `/api/articles?limit=200` outputs were reviewed using saved JSON files and Python scripts to avoid the known heredoc pipe JSON SyntaxError issue.

### Misaligned content identified
Examples of content identified as off-strategy or too weak included:

- Pornhub article from BBC Tech.
- Driver/crash/incident articles.
- “Thieving Carl BANNED from Crewe Tesco…” crime/court-style local churn.
- Wildlife/zoo/animal filler.
- Emotional/tabloid animal story: “I had to pay £14k after my cat was run over.”
- Soft local/lifestyle filler such as festival, ice cream drive-in, garden centre train rides, beach rescue, limited edition menu.

### Articles manually archived
The following types were archived through the admin archive endpoint:

- Adult/Pornhub article.
- Driver crash / pulled-from-vehicle incident articles.
- Theft/crime churn article.
- Zoo/wildlife/animal filler articles.
- Emotional tabloid cat story.
- Entertainment filler.
- Soft lifestyle local filler including festival, ice cream, beach rescue, limited edition menu, garden centre/miniature railway items.

Endpoint used:

```text
POST /api/admin/articles/{article_id}/archive
```

### Content retained intentionally
The following types were intentionally kept because they fit the platform direction:

- Northgate Arena revamp — local investment/infrastructure.
- Companies paying out after slurry incidents — business/environmental accountability.
- Lidl store target locations — local business/retail/jobs.
- Tatton Park dog rule change — local utility/rules, though later similar soft items may be stricter depending on homepage feel.
- NASA budget / technology/economic items.
- Food/fertiliser risk from Iran war — macro business/economy.
- Musk/Altman business/AI/legal stories.
- Renters’ Rights, interest rates, Rachel Reeves tax, finance and household-money stories.

### Filtering diagnosis
The existing filters were already hard-blocking many crime/obituary/low-utility stories in the RSS import path and local RSS path. The main remaining leakage was:

- Incident/emergency content.
- Animal/zoo/nature filler.
- Emotional/tabloid lifestyle stories.
- Existing active articles imported before stricter rules.

### Backend RSS sync filter tightened
File changed:

```text
backend/server.py
```

Commit:

```text
c14a73e Tighten RSS sync filter for low-value incident and animal filler
```

A new `sync_noise_kw` filter was added to the RSS sync path to catch low-value incident/animal/tabloid filler. It uses an economic exception filter so useful business/economic/local-impact stories are not blocked unnecessarily.

The new logic blocks phrases such as:

- driver / crash / injured / pulled from vehicle / emergency services.
- zoo / wildlife park / lion / antelope / dogs’ brains / rescued animals.
- “I had to”, “family says”, “heartbroken”, “after my”, “rescued by firefighters”.

But it preserves stories with economic/business signals such as:

- mortgage, rent, tax, inflation, rates, jobs, wages, economy, business, finance, markets, bills, energy, council, planning, housing, investment, trade, tariff, warehouse, development, stores, retail.

### Backend syntax verified
`python3 -m py_compile backend/server.py` passed before commit/deploy.

### Backend deployed and health checked
After deploy:

```json
{
  "status": "healthy",
  "service": "cheshire-news"
}
```

---

## 4. Homepage feed audit and rebalancing

### Problem identified
After cleanup, the article category counts looked acceptable, but the homepage still felt too planning/local-heavy, especially in Latest.

Audit snapshot:

- Total articles reviewed: 121.
- Category counts included Tech, Local News, Business, Finance and UK News.
- Theme counts showed high local_utility, ai_tech, business_jobs, finance_money, and planning_housing_development overlap.

### Core insight
The homepage was not simply overstocked with local articles. The issue was **ordering** and **ranking quality**:

- Latest was intentionally selecting 4 Local first.
- Pure planning/housing stories scored highly because they received local, Cheshire/town, planning/economic and freshness boosts.
- This made the homepage first impression feel like a local planning feed, not a finance/business/AI platform.

### Existing homepage logic inspected before changes
The existing `HomePageV1.jsx` already had structured sections and balanced logic. This was intentionally preserved. The fix was targeted, not a rewrite.

### Latest feed pass order changed
File:

```text
frontend/src/pages/HomePageV1.jsx
```

Latest feed logic changed from:

```text
Local → Business/Finance → AI/Tech → UK
```

to:

```text
Business/Finance → Local → AI/Tech → UK
```

This keeps the same broad mix but makes the first row feel more aligned with the project.

### Business/Finance candidate sorting added
The Business/Finance pass now builds `latestBusinessCandidates`, filters non-AI business/money articles, and sorts by `rankScore` before pushing cards.

### Planning penalty added to rankScore
A targeted penalty was added in `rankScore()`:

```js
const planningText = (String(a?.title || "") + " " + String(a?.summary || "")).toLowerCase();
const isPlanningOnly = /(planning|housing|estate|new homes|approved|approval|application|apartments|flats)/.test(planningText);
const hasBusinessImpact = /(jobs?|warehouse|retail|business|factory|investment|town centre|store|stores|employment)/.test(planningText);
if (isPlanningOnly && !hasBusinessImpact) {
  score -= 320;
}
```

This suppresses pure planning/housing approvals from top positions but keeps developments with jobs/warehouse/retail/business impact competitive.

### Build errors encountered and fixed
A first attempt caused:

```text
Identifier 't' has already been declared
```

This was fixed by renaming the injected variable to `planningText`.

Trailing whitespace was also fixed using a script that stripped line endings.

### Visual result confirmed
After the ranking change, the top row changed away from planning-heavy content toward:

- Two pubs closing due to tax rises.
- UK borrowing costs.
- UK debt/economy-style business story.

This confirmed that the homepage now feels more like a business/finance/economic publication and less like a generic local planning site.

### Commit and deploy
Commits:

```text
73bd264 Downrank pure planning items in homepage ranking
```

Frontend was deployed manually on Render after push.

---

## 5. Awin affiliate expansion work

### User provided Awin finance/insurance/business affiliate list
The list included finance, insurance, breakdown, travel, business, property and household-cost programmes.

### Application strategy chosen
Avoid mass-applying. Apply one-by-one to high-probability programmes that match the current site positioning and guide inventory.

### Promotion type guidance
In Awin “Promotion”, user should choose:

- Website / Content.
- Editorial / Blog where available.

Avoid:

- Cashback / Incentives.
- PPC unless actively running PPC.
- Email-only positioning as the main promotion method.

### Awin application copy compressed to 255 characters
Because Awin description field had a 255-character limit, shorter copy was used.

Example used:

```text
Cheshire Today is a UK local business and finance publication. We create editorial guides on insurance, money and business services, promoted via SEO, newsletter and Facebook to UK readers making practical financial decisions.
```

### Affiliate programmes applied to and current status
All of the following were submitted and are currently **pending**:

- AXA Business Insurance.
- AXA Landlord Insurance.
- QuoteSearcher.
- Heatable.
- Mymoneycomparison.
- Hiscox Underwriting Group Services Ltd.

### Application rationale
These were chosen to build a coherent monetisation stack:

- Business insurance layer: AXA Business, Hiscox.
- Landlord/property layer: AXA Landlord.
- Comparison layer: QuoteSearcher, Mymoneycomparison.
- Household/home-cost layer: Heatable.

The decision was made not to apply yet to harder-to-approve programmes such as major credit cards, SIPP/investment platforms and big banks until the site has more authority, more monetised guides, and at least some approvals.

---

## 6. DHL eCommerce and Interparcel affiliate setup

### DHL eCommerce approval confirmed
The user shared affiliate approval details:

- 9% commission for new customers.
- 1.3% for existing customers.
- 30-day cookie window.
- Contact: Chris at makeitsoconsultants.com.

### DHL destination URL guidance
For DHL eCommerce Awin deep link, the advised destination URL was:

```text
https://www.dhl.com/gb-en/home/our-divisions/ecommerce/solutions.html
```

Awin click reference used:

```text
ct-dhl-ecommerce-parcel-guide
```

Final DHL Awin tracking link used:

```text
https://www.awin1.com/cread.php?awinmid=121764&awinaffid=2844510&clickref=ct-dhl-ecommerce-parcel-guide&ued=https%3A%2F%2Fwww.dhl.com%2Fgb-en%2Fhome%2Four-divisions%2Fecommerce%2Fsolutions.html
```

### Interparcel Awin tracking link fixed
User first generated an Interparcel Awin link where `clickref` incorrectly contained the destination URL. This was rejected because it would break meaningful attribution.

Correct click reference:

```text
ct-interparcel-parcel-guide
```

Final Interparcel Awin tracking link:

```text
https://www.awin1.com/cread.php?awinmid=32851&awinaffid=2844510&clickref=ct-interparcel-parcel-guide&ued=https%3A%2F%2Fwww.interparcel.com%2F
```

### Parcel guide provider order updated
Guide:

```text
best-parcel-courier-services-small-business-uk
```

Final live order:

1. Parcel ABC UK — tracked via Awin.
2. DHL eCommerce UK — tracked via Awin.
3. Interparcel — tracked via Awin.

This replaced the previous state where Interparcel used a direct untracked link.

### Authority page API update method
The guide upsert endpoint required a full page payload including title, not `sections_append`. The guide was fetched to `/tmp/parcel_guide.json`, amended in Python, then posted back to:

```text
POST /api/admin/authority-pages/upsert
```

Admin token was retrieved from browser localStorage:

```js
localStorage.getItem("cheshire_admin_token")
```

The update succeeded with HTTP 200.

---

## 7. Parcel guide optimisation

### Existing tool descriptions inspected
Before optimisation, tool descriptions were:

- Parcel ABC UK: Best for comparing parcel delivery quotes across courier options.
- DHL eCommerce UK: Best for businesses needing reliable direct courier coverage.
- Interparcel: Best for businesses wanting multiple courier services from one platform.

### Updated decision-first copy
Provider copy was changed via the authority page API.

Final live copy:

- **Parcel ABC UK** — Best for price comparison: compare parcel delivery quotes across couriers before booking. Useful for small businesses that want to check costs quickly before choosing a service.
- **DHL eCommerce UK** — Best for reliability and scale: a strong direct courier option for businesses that need trusted UK and international delivery, consistent tracking and brand recognition.
- **Interparcel** — Best overall multi-carrier option: useful for small businesses that want access to several courier services from one platform rather than managing separate carrier accounts.

### Strategic result
The parcel guide is now the first fully monetised and conversion-positioned guide:

- all provider links tracked via Awin.
- provider ordering revenue-conscious.
- copy decision-led.
- suitable as first monetisation test page.

---

## 8. Guide/provider click tracking implementation

### Existing state
The site already had a frontend `trackEvent` helper:

```text
frontend/src/utils/trackEvent.js
```

It supports:

- Plausible custom events if `window.plausible` exists.
- GA/GTM-style dataLayer events if `window.dataLayer` exists.
- Console fallback in non-production.

No backend guide-click endpoint existed yet.

### First provider click tracking added
File:

```text
frontend/src/pages/AuthorityPage.jsx
```

`trackEvent` import added:

```js
import { trackEvent } from "../utils/trackEvent";
```

Provider card CTA tracking added:

```js
onClick={() => trackEvent("guide_provider_click", {
  guide: slug,
  provider: name,
  position: idx + 1,
  destination: link,
})}
```

Commit:

```text
9d462cc Track authority guide provider clicks
```

### Top provider CTA tracking issue
Testing showed clicking the top CTA did not fire the event. Inspection showed two `Visit provider` locations:

- top provider CTA around lines ~147–154.
- provider card CTA around lines ~740–752.

Only the provider card CTA was initially tracked.

### Top provider CTA tracking added
Tracking was added to the top CTA with:

```js
trackEvent("guide_provider_click", {
  guide: slug,
  provider: name,
  position: 1,
  destination: link,
  placement: "top_pick",
})
```

Commit:

```text
c407465 Track authority guide top provider CTA clicks
```

### Tracking bugs encountered and fixed
Live testing exposed two JavaScript reference errors:

1. `ReferenceError: Can't find variable: slug`
2. `ReferenceError: Can't find variable: page`

The top CTA was in a helper/component scope where neither `slug` nor `page` was available.

Final fix used the URL path:

```js
window.location.pathname.replace("/guides/", "")
```

Final top CTA tracking logic:

```js
onClick={() => trackEvent("guide_provider_click", {
  guide: window.location.pathname.replace("/guides/", ""),
  provider: name,
  position: 1,
  destination: link,
  placement: "top_pick",
})}
```

Commits:

```text
8928abb Fix top provider CTA tracking guide slug
```

and final scope fix committed after replacing `page` with `window.location`.

### Tracking validation
Testing on the live parcel guide showed:

```js
window.dataLayer.filter(x => x && x.event === "guide_provider_click")
```

returned an event object after clicking the provider CTA.

This confirmed:

- `guide_provider_click` fires.
- top provider CTA is tracked.
- provider card CTA is tracked.
- `dataLayer` receives the event.

### GA blocked locally
The user’s browser showed:

```text
Blocked connection to known tracker https://www.googletagmanager.com/gtag/js?id=G-Q1NZLJC50D
```

This was diagnosed as browser/device privacy blocking, likely Safari/iOS/content blocker/privacy protection. This does not mean the site code is broken. The `dataLayer` event works; GA may be blocked for some privacy-protected users.

### Remaining tracking limitation
Because GA can be blocked, the next important improvement is backend/internal click logging.

Recommended future endpoint:

```text
POST /api/track/guide-click
```

Store:

- guide slug.
- provider.
- position.
- placement.
- destination.
- timestamp.
- optionally referrer/user agent.

---

## 9. Final commits and deploys completed in this session

### Backend/filtering

```text
c14a73e Tighten RSS sync filter for low-value incident and animal filler
```

### Homepage and provider tracking

```text
9d462cc Track authority guide provider clicks
73bd264 Downrank pure planning items in homepage ranking
c407465 Track authority guide top provider CTA clicks
8928abb Fix top provider CTA tracking guide slug
```

Plus final scope fix for top CTA tracking using `window.location.pathname.replace("/guides/", "")`.

### Push/deploy status
All relevant commits were pushed to:

```text
origin/full-scrape-prod
```

Manual Render frontend/backend deploys were performed as needed.

Backend health checks passed after backend deploy:

```json
{
  "status": "healthy",
  "service": "cheshire-news"
}
```

---

## 10. Current project state after this session

### Homepage/content
- Homepage is now more economic-first.
- Pure planning/housing approvals are suppressed from top positions unless they have jobs/retail/business/investment impact.
- Latest now leads with Business/Finance before Local.
- Soft lifestyle and incident/noise content reduced.

### Article filtering
- Future RSS sync now blocks more incident/animal/tabloid filler.
- Existing active pool has been manually cleaned.
- Some local utility/property/business stories are intentionally retained.

### Monetisation
- Parcel/courier guide is fully monetised via Awin:
  - Parcel ABC.
  - DHL eCommerce.
  - Interparcel.
- Parcel guide copy is conversion-led.
- Provider click tracking is live.

### Awin
Pending applications:

- AXA Business Insurance.
- AXA Landlord Insurance.
- QuoteSearcher.
- Heatable.
- Mymoneycomparison.
- Hiscox Underwriting Group Services Ltd.

### Tracking
- Frontend provider tracking works through `dataLayer`.
- GA may be blocked by some browsers/privacy systems.
- Backend tracking is not yet implemented.

---

## 11. Remaining project tasks after this session

### Highest priority
1. **Implement backend/internal guide click tracking** so affiliate/provider clicks are recorded even when GA is blocked.
2. **Increase guide visibility** across homepage, article pages and sidebars without intrusive UX.
3. **Monitor Awin approvals** and immediately integrate approved providers into relevant guides.
4. **Build/upgrade 3–5 high-value monetised guides**, especially:
   - Business insurance.
   - Landlord insurance.
   - Mortgage rates / mortgage brokers.
   - Savings accounts / ISA platforms.
   - Credit cards.
   - Energy / boiler / home-cost guides.

### Medium priority
5. Use provider click data to reorder providers by CTR.
6. Add or improve “Top Pick” style presentation for guide providers.
7. Build guide-to-article and article-to-guide funnels.
8. Continue tightening RSS filters if new off-strategy content appears.

### Lower priority / backlog
9. Newsletter subject-line optimisation.
10. Wider affiliate expansion through CJ, Impact and other networks once Awin approvals land.
11. Future monetisation layers:
    - Jobs.
    - Directory.
    - Sponsorships.
    - Event listings.
    - Media kit and advertiser reporting.

---

## 12. Strategic status

Cheshire Today has moved from a content-heavy site toward a monetisable economic intelligence platform.

Key systems now active:

- Homepage ranking control.
- Cleaner article filtering.
- Awin affiliate integration.
- First fully monetised guide.
- Provider-level click tracking.
- Finance/business-first positioning.

The next major phase should be **Guide Visibility + Backend Tracking + Approved Affiliate Integration**.


---

# 📅 PROJECT UPDATE — 2026-05-06 — FACEBOOK ANALYTICS ADMIN INTEGRATION + MONETISATION/TRACKING CONTINUATION

## Session Objective
Wire the existing Facebook analytics/admin infrastructure to the live Facebook Page, improve Facebook analytics data quality, and document the current state after the homepage, guide, affiliate, and tracking work.

## 1. Existing Facebook Integration Confirmed
Inspected source files and confirmed Facebook functionality already existed in:
- `backend/app/facebook_service.py`
- `backend/app/facebook_oauth.py`
- backend Facebook routes in `backend/server.py`
- Facebook tab and Facebook Analytics tab in `frontend/src/components/AdminDashboard.jsx`

Existing backend/admin routes included:
- `GET /api/facebook/status`
- `GET /api/facebook/oauth/status`
- `GET /api/facebook/oauth/authorize`
- `GET /api/facebook/oauth/callback`
- `POST /api/facebook/oauth/validate-token`
- `POST /api/facebook/test-post`
- `POST /api/facebook/test-simplified`
- `POST /api/facebook/post-latest`
- `POST /api/facebook/trigger-scheduled`
- `GET /api/facebook/analytics`
- `GET /api/facebook/analytics/insights`

Conclusion: the UI/routes already existed; the missing piece was live Facebook configuration/token handling.

## 2. Render Facebook Environment Variables
Initial live analytics test returned:
```json
{
  "success": false,
  "error": "Facebook not configured",
  "posts": []
}
```

Required backend variables identified:
```env
FACEBOOK_PAGE_ID
FACEBOOK_PAGE_ACCESS_TOKEN
```

Optional OAuth variables identified:
```env
FACEBOOK_APP_ID
FACEBOOK_APP_SECRET
FACEBOOK_OAUTH_REDIRECT_URI
```

OAuth status test confirmed OAuth was not configured:
```json
{
  "configured": false,
  "app_id_set": false,
  "app_secret_set": false,
  "redirect_uri": null,
  "message": "Set FACEBOOK_APP_ID and FACEBOOK_APP_SECRET to enable OAuth"
}
```

## 3. Facebook Page ID and Page Token
Facebook Page ID confirmed:
```text
865430919994962
```

Page name:
```text
Cheshire Today
```

Important token discovery:
- Graph API Explorer token box could still show a user token.
- Correct Page token was obtained from the Page JSON response using:
```text
865430919994962?fields=id,name,access_token
```
- The returned JSON `access_token`, not the token box value, must be used in Render as `FACEBOOK_PAGE_ACCESS_TOKEN`.

Render backend variables were added/updated:
```env
FACEBOOK_PAGE_ID=865430919994962
FACEBOOK_PAGE_ACCESS_TOKEN=<Page access token from Graph API JSON response>
```

## 4. Facebook Status Endpoint Confirmed Working
After Render env update and backend redeploy, `/api/facebook/status` returned:
```json
{
  "configured": true,
  "token_valid": true,
  "page_name": "Cheshire Today ",
  "page_id": "865430919994962",
  "followers": 66,
  "page_url": "https://www.facebook.com/865430919994962",
  "error": null
}
```

Confirmed:
- Page ID correct
- Page token valid
- Page name detected
- follower count pulled
- backend/admin Facebook connection working

## 5. Facebook Token Handling Fixes
Problem: `facebook_service.py` assumed `FACEBOOK_PAGE_ACCESS_TOKEN` was a user token and tried to fetch another Page token.

Fix implemented in `backend/app/facebook_service.py`:
- `get_page_token()` now accepts a direct Page token.
- It validates the configured token directly against the Page first.
- If valid, it uses that token directly.
- If not valid, it falls back to user-token-to-page-token logic.

Commit:
```text
7ea5ac0 Accept direct Facebook page access token
```

Problem: stale `_page_token` could remain cached after Render token rotation.

Fix implemented:
- Avoid reusing stale cached Facebook Page tokens when env token changes/rotates.

Commit:
```text
a1962c5 Avoid stale cached Facebook page tokens
```

## 6. Facebook Analytics Endpoint Working
After using the correct JSON Page access token and redeploying backend, `/api/facebook/analytics` returned:
- `success: true`
- recent posts analysed
- real post IDs
- post titles
- message previews
- created timestamps

Example post titles returned:
- “Energy bills are changing — and this could affect what Cheshire households pay each month.”
- “Should Cheshire be worried about Bentley job cuts?”
- “Oil prices hit their highest level since 2022”
- “The Bank of England has held interest rates at 3.75% — but that does not mean the pressure is off.”
- “Plans resubmitted for 18 flats near Tatton Park”
- “Claire’s has closed all 154 of its standalone stores across the UK and Ireland...”

Result: Admin Facebook Analytics is now connected and should show real posts instead of “not configured.”

## 7. Facebook Analytics Title Extraction Improved
Problem: analytics rows showed `Unknown` because the parser only recognised auto-post captions starting with `📰`.

Fix in `backend/app/facebook_service.py`:
- Extract the first non-empty line of the Facebook caption.
- Remove `📰` when present.
- Use that line as the post title.

Commit:
```text
cf93d8b Improve Facebook analytics post title extraction
```

Result: Facebook Analytics now displays meaningful post titles.

## 8. Facebook Engagement Metric Upgrade
Problem: likes/comments/shares initially showed zero. The endpoint used legacy:
```text
likes.summary(true)
```

Change made:
```text
reactions.summary(true)
```

Engagement score now uses:
```python
reactions + (comments * 2) + (shares * 3)
```

Returned fields keep backwards compatibility:
```python
"likes": reactions
"reactions": reactions
```

Commit:
```text
a312e55 Use reactions for Facebook analytics engagement
```

Status: this commit was created locally and should be pushed/deployed if not already done.

## 9. Security Note
The Facebook access token appeared in debugging output/logs during setup.

Follow-up:
- Rotate/regenerate the Facebook Page token.
- Update Render with the new token.
- Redeploy backend.
- Avoid exposing the token in chat/logs.

## 10. Related Work From This Project Phase
This Facebook analytics work builds on the immediately prior monetisation/tracking phase:

### Homepage economic rebalance
- Latest feed reordered to lead with Business/Finance.
- Pure planning/housing items downranked unless they have business impact.
- Homepage now better reflects the economic intelligence positioning.

### Article cleanup
Archived off-strategy active articles including:
- incident/crash filler
- crime/court churn
- adult-topic article
- soft lifestyle filler
- weak local/tourism filler

### Parcel/courier guide monetisation
Guide:
```text
best-parcel-courier-services-small-business-uk
```

Providers:
1. Parcel ABC UK — tracked Awin link
2. DHL eCommerce UK — tracked Awin link
3. Interparcel — tracked Awin link

Provider positioning:
- Parcel ABC UK — best for price comparison
- DHL eCommerce UK — best for reliability and scale
- Interparcel — best overall multi-carrier option

### Guide click tracking
Implemented event:
```text
guide_provider_click
```

Captures:
- guide
- provider
- position
- destination
- placement

Tracking validated in `window.dataLayer`.

### Awin applications submitted
Pending applications:
- AXA Business Insurance
- AXA Landlord Insurance
- QuoteSearcher
- Heatable
- Mymoneycomparison
- Hiscox

## 11. Current Next Tasks
High priority:
1. Push/deploy `a312e55 Use reactions for Facebook analytics engagement` if not already done.
2. Retest `/api/facebook/analytics`.
3. Refresh Admin → Facebook Analytics and confirm titles + engagement metrics.
4. Rotate Facebook Page token for security.
5. Monitor Awin approvals and integrate approved partners into relevant guides.
6. Increase guide visibility across homepage/article/sidebar/newsletter.
7. Implement internal backend affiliate/provider click logging so analytics still works when GA is blocked.

Medium priority:
8. Add date-range selector to Facebook analytics.
9. Add link clicks/impressions if available via Graph API insights permissions.
10. Store Facebook analytics snapshots in MongoDB for historical trend tracking.

## Strategic Status
Cheshire Today now has:
- cleaner economic-first homepage ranking
- live monetised parcel/courier guide
- tracked guide provider clicks
- Facebook Page analytics connected in admin
- Awin finance/insurance applications pending
- the first real operational analytics loop across content, Facebook, and affiliate guides

The project is now in the monetisation infrastructure + analytics phase.

---

# 2026-05-07 CONTINUATION UPDATE — FACEBOOK ANALYTICS FINALISATION + UPTIMEROBOT CLEANUP

## 1. Source-of-truth note
This update was appended to the existing chat-source master file only:

```text
PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260428_v12_FULL_UPDATED_20260506_FACEBOOK_ANALYTICS.md
```

No older sections were deleted or compacted. This section supersedes the earlier “Current Next Tasks” items relating to Facebook analytics push/deploy/retest, because those items have now been completed and verified live.

## 2. Final git state after this work
Final verified branch state:

```text
Branch: full-scrape-prod
HEAD / origin: 8d06501 Replace migration warmup URLs with production domain
Working tree: clean when last checked
```

Recent relevant commit chain:

```text
8d06501 Replace migration warmup URLs with production domain
e757ed3 Fetch Facebook content before engagement metrics
04008b4 Import httpx for Facebook edge diagnostics
7235a04 Add Facebook analytics edge diagnostics
ae5da99 Add promotable posts to Facebook analytics
eecd0b8 Expand Facebook analytics content sources
af32ebb Improve Facebook analytics admin display
3cbd925 Generate Facebook insights from live analytics data
8cd8b48 Merge Facebook feed and video content in analytics
4b6124b Prefer exchanged Facebook page token for feed access
cef1dc9 Use Facebook feed for fresher analytics posts
7d48652 Fix single Facebook post reaction analytics
a312e55 Use reactions for Facebook analytics engagement
```

## 3. Facebook analytics — completed work
The Facebook analytics integration was taken from partially connected to operational and live-tested.

Confirmed production Page connection:

```text
Facebook Page ID: 865430919994962
Page name: Cheshire Today
Followers at verification point: 66
Token status after rotation: valid
```

Production status endpoint returned:

```json
{
  "configured": true,
  "token_valid": true,
  "page_name": "Cheshire Today ",
  "page_id": "865430919994962",
  "followers": 66,
  "error": null
}
```

### 3.1 Token/session issue found and resolved
During testing, the Facebook token expired and production returned:

```text
Session has expired on Wednesday, 06-May-26 15:00:00 PDT
```

Action taken:
- Facebook Page token was rotated/updated in Render.
- Backend token validation was retested successfully.
- Backend logic was improved so `get_page_token()` prefers exchanging the configured token for the actual Page token before falling back to direct token use.

Relevant commit:

```text
4b6124b Prefer exchanged Facebook page token for feed access
```

### 3.2 Single-post reaction bug fixed
A bug was found in `backend/app/facebook_service.py` where single-post engagement calculation had been changed to use `reactions`, but the Graph request still requested `likes`, leaving `reactions` undefined in that function.

Fix applied:
- Single-post engagement now requests `reactions.summary(true)`.
- Single-post engagement now extracts `reactions` consistently.
- Python syntax verified with `python3 -m py_compile`.

Relevant commit:

```text
7d48652 Fix single Facebook post reaction analytics
```

### 3.3 Analytics freshness issue diagnosed
Initial analytics endpoint was live but stale. It showed normal feed posts only up to 2026-05-03 and missed newer normal posts, while newer Reels/videos existed.

Initial attempted fixes:
- Switched analytics fetch from `/posts` to `/feed`.
- Added merged content fetching for `feed`, `videos`, and `video_reels`.
- Added additional sources including `posts`, `published_posts`, `photos`, and a diagnostic-only test for `promotable_posts`.

Finding:
- Facebook Graph returned newer feed posts when requested with basic fields only.
- Facebook Graph dropped or failed to surface the same newer feed posts when engagement fields were requested directly on the edge list query.

Root cause:

```text
The analytics list query was requesting engagement fields directly on the Facebook edge.
This caused newer feed posts to be omitted from the result set.
```

Final fix:
- Fetch Facebook content lists first using basic fields only: `id`, `message`/`description`/`name`, `created_time`, `permalink_url`.
- Enrich each returned item with engagement metrics in a second per-item request.
- Deduplicate by permalink where available.
- Classify Reels as `source_type = reel` when permalink contains `/reel/`.
- Keep engagement-score ranking, with created time as tie-breaker so zero-engagement lists remain current.

Relevant final analytics commit:

```text
e757ed3 Fetch Facebook content before engagement metrics
```

### 3.4 Verified production analytics result
After final deploy, `/api/facebook/analytics` returned up-to-date content including both Reels and normal posts.

Verified compact result:

```text
success = True
total = 29
source counts = {'reel': 12, 'feed': 16, 'photos': 1}
```

Newest verified items included:

```text
2026-05-07T11:16:49+0000 | reel | Up to 275 jobs are at risk at Bentley in Cheshire.
2026-05-07T06:04:39+0000 | feed | Plans have been lodged for 70 new homes in an affluent Cheshire village.
2026-05-06T17:59:26+0000 | feed | A massive new warehouse plan in Cheshire could create 275 jobs.
2026-05-06T11:00:37+0000 | reel | AI job scams are becoming harder to spot.
2026-05-06T06:00:02+0000 | feed | Pret A Manger has opened its first ever drive-thru restaurant in Cheshire.
2026-05-05T18:15:58+0000 | feed | Had car finance in the past? This could be worth checking.
2026-05-05T06:01:48+0000 | feed | Robots are moving into waste and recycling.
2026-05-04T17:53:58+0000 | feed | Work started on a 55-home development at Ledsham Garden Village.
```

This confirmed the dashboard freshness issue was fixed.

## 4. Facebook analytics insights endpoint fixed
Original problem:
- `/api/facebook/analytics/insights` returned:

```text
Not enough data yet. Post more articles to get insights.
```

Cause:
- The route relied on a MongoDB collection named `facebook_post_log`.
- Live database inspection showed no collection matching `facebook`, `post`, or `social`.
- Existing collections included `articles`, `authority_pages`, `digest_log`, `email_analytics`, `sponsored_placements`, etc., but no Facebook post log collection.

Fix applied:
- Insights route now fetches live Facebook analytics first.
- If internal `facebook_post_log` data exists later, it still uses it for category matching.
- If no internal logs exist, it falls back to live Graph data and still produces insights.

Verified production insights result after deploy:

```text
success: true
total_posts_analyzed: 31
insights returned:
- Top Performing Content
- Most Common Facebook Format
- Posting Frequency
- Average Engagement
```

Later frontend/backend changes improved the underlying analytics sample further.

Relevant commit:

```text
3cbd925 Generate Facebook insights from live analytics data
```

## 5. Facebook admin UI improved
Admin dashboard was updated so the Facebook analytics block matches the backend’s new mixed content model.

Changes:
- “Posts Analyzed” renamed to “Facebook Items”.
- “Total Likes” renamed to “Total Reactions”.
- “Top Performing Posts” renamed to “Facebook Content Performance”.
- Row display now supports feed posts, videos, Reels and photos.
- Shows `source_type` badge such as `feed`, `reel`, `photos`.
- Shows created date/time using existing `formatDate()` helper.
- Shows reaction/comment/share/score metrics.
- Shows clickable Facebook/Reel permalink via `ExternalLink` icon.

Build verification:

```text
REACT_APP_BACKEND_URL=https://cheshiretoday.co.uk npm --prefix frontend run build
Compiled successfully.
```

Relevant commit:

```text
af32ebb Improve Facebook analytics admin display
```

## 6. Facebook edge diagnostic endpoint added
An admin-only diagnostic route was added to identify which Facebook Graph edges expose what content.

Route:

```text
GET /api/facebook/analytics/debug-edges
```

Purpose:
- diagnose Facebook Graph edge differences without exposing tokens
- show each edge success/error
- show newest items per edge
- prove whether missing posts are hidden by Graph or filtered by our code

Diagnostic findings:
- `promotable_posts` returned invalid/nonexistent field for this Page.
- `feed`, `published_posts`, and `posts` all exposed newer normal feed posts when requested with basic fields only.
- `videos` and `video_reels` exposed Reels.
- This diagnostic directly led to the final two-step analytics fetch fix.

Relevant commits:

```text
7235a04 Add Facebook analytics edge diagnostics
04008b4 Import httpx for Facebook edge diagnostics
```

Note:
- The diagnostic endpoint is admin-protected.
- It can be kept temporarily for troubleshooting, but should eventually be removed or left undocumented from public/admin UI once Facebook analytics is stable.

## 7. UptimeRobot issue investigated and cleaned up
### 7.1 UptimeRobot false-alert cause
The monitor shown in UptimeRobot was originally labelled/pointing to old migration-era infrastructure:

```text
cheshiretoday-frontend-migration.onrender.com/api/articles
```

The monitor URL was corrected manually in UptimeRobot to:

```text
https://cheshiretoday.co.uk/api/health
```

Recommended UptimeRobot configuration:

```text
Monitor name: Cheshire Today API Health
Type: HTTP(s) or API monitor
Method: GET
URL: https://cheshiretoday.co.uk/api/health
Expected status: 200
Keyword / JSON assertion: healthy
Interval: 5 minutes
```

Production health endpoint tested successfully:

```text
HTTP/2 200
{"status":"healthy","service":"cheshire-news"}
```

Reasoning:
- The old Render frontend migration URL was used during the website migration when `cheshiretoday.co.uk` still pointed to the previous host.
- Now that the production domain is live on the new stack, UptimeRobot should monitor the production domain, not Render migration URLs.

### 7.2 Source/config check for old Render URLs
Active-file scan found old migration URL references in:

```text
render.yaml
frontend/warmup.sh
frontend/.env.production
```

Additional old references existed only in `.bak`, `.log`, or `.md` history files.

Live production JS check found only:

```text
cheshiretoday.co.uk
```

and did not show the old Render migration URLs in current active JS.

### 7.3 Source cleanup performed
Tracked source cleanup:

```text
render.yaml
- https://cheshiretoday-migration.onrender.com/health
+ https://cheshiretoday.co.uk/api/health

frontend/warmup.sh
- https://cheshiretoday-migration.onrender.com/api/articles
+ https://cheshiretoday.co.uk/api/articles?limit=1
```

Local `frontend/.env.production` was also confirmed as:

```text
REACT_APP_BACKEND_URL=https://cheshiretoday.co.uk
```

but it did not appear in Git diff, likely because it is ignored or already not tracked.

Active non-backup source scan after cleanup showed no matches for:

```text
cheshiretoday-frontend-migration.onrender.com
frontend-migration
cheshiretoday-migration.onrender.com
```

Relevant commit:

```text
8d06501 Replace migration warmup URLs with production domain
```

No backend deploy was required purely for this cleanup unless Render Blueprint/cron settings need to be re-applied from `render.yaml`.

## 8. Production verification commands/results used
Health check:

```bash
curl -sS https://cheshiretoday.co.uk/api/health | python3 -m json.tool
```

Returned:

```json
{
  "status": "healthy",
  "service": "cheshire-news"
}
```

Git final verification:

```text
8d06501 (HEAD -> full-scrape-prod, origin/full-scrape-prod) Replace migration warmup URLs with production domain
```

Facebook analytics final verification showed current feed posts and Reels correctly.

## 9. Updated completed tasks from earlier section
The following earlier tasks are now complete:

```text
1. Push/deploy a312e55 Use reactions for Facebook analytics engagement.
2. Retest /api/facebook/analytics.
3. Refresh Admin → Facebook Analytics and confirm titles + engagement metrics.
4. Rotate Facebook Page token for security.
8. Add better Facebook analytics freshness/format handling.
```

Additional completed work beyond the earlier list:

```text
- Fixed single-post reaction variable bug.
- Fixed Page-token exchange order.
- Added live Graph fallback insights.
- Added Reels/videos/feed/photos mixed analytics.
- Added and used admin-only Graph edge diagnostics.
- Fixed missing recent feed posts by separating content fetch from engagement metric fetch.
- Improved admin Facebook analytics display.
- Corrected UptimeRobot to production health endpoint.
- Removed active migration Render URL references from warmup config.
```

## 10. Remaining next tasks after this update
High priority:

1. Monitor UptimeRobot over the next several checks and confirm false alerts stop.
2. Consider removing the admin-only `/api/facebook/analytics/debug-edges` route once analytics stability is confirmed.
3. Continue using Facebook analytics to identify which topics/formats perform best.
4. Use Facebook performance data to guide daily post/Reel selection and Facebook-to-guide conversion.
5. Increase guide/affiliate visibility across homepage/article/sidebar/newsletter.
6. Implement internal backend affiliate/provider click logging so analytics remains available when GA is blocked.

Medium priority:

7. Add date-range selector to Facebook analytics.
8. Add link-click/impression analytics if Facebook Graph permissions allow.
9. Store Facebook analytics snapshots in MongoDB for historical trend tracking.
10. Add a real `facebook_post_log` collection when posting through admin, so dashboard insights can link Facebook items to exact article IDs/categories.
11. Clean duplicate `/api/health` route declarations in `backend/server.py` at a later maintenance point.
12. Consider cleaning old `.bak` files/logs only after confirming they are no longer needed for project history.

## 11. Strategic status after this update
Cheshire Today now has:

```text
- production Facebook analytics working across feed posts, Reels/videos and photos
- live Facebook insights even without MongoDB post logs
- admin dashboard display aligned with mixed Facebook content formats
- UptimeRobot pointing to production health endpoint
- active source config cleaned away from migration Render URLs
- verified production health and clean git state
```

The project remains in the monetisation infrastructure + analytics phase, with the next best business move being to turn Facebook performance data into better traffic-routing decisions toward guides, affiliate pages, newsletter signups and sponsored/revenue surfaces.


---

# Project update — 2026-05-12/13 — AI rewrite safety, Admin manual-review workflow, Facebook OG image fix, and newsletter test-email hardening

## 1. Purpose of this project session

This session focused on four connected production-quality issues for Cheshire Today:

1. Tightening AI rewrite accuracy so unsupported AI-generated article detail does not appear publicly.
2. Creating a proper Admin manual-review workflow for AI-risk articles.
3. Fixing a Facebook/Open Graph image-preview issue for a Guardian-sourced article.
4. Investigating and hardening newsletter delivery after a bounce from a dummy/test unsubscribe address.

All code work remained on:

```text
branch: full-scrape-prod
repo: CT29january26-new-website-migration
```

The established workflow was followed:

```text
- check current state before changing code
- one command at a time
- no manual file edits
- apply changes through terminal scripts
- run syntax/build verification before commits
- push to origin/full-scrape-prod
- manual Render deploys only
```

---

## 2. Daily Brief / digest-log cleanup and verification

Old Daily Brief rows were found stuck in a `sending` state.

Initial investigation showed:

```text
in_progress_daily_brief_rows = 18
success_count = 0 for all stuck rows
```

Examples included old rows dated around:

```text
20260203
20260206
20260207
20260209
20260210
20260211
20260212
20260213
20260216
20260217
20260218
20260219
20260220
20260221
20260418
```

Those rows were marked failed/cleaned:

```text
matched = 18
modified = 18
```

Follow-up check confirmed:

```text
remaining_in_progress_daily_brief_rows = 0
```

The Daily Brief cursor state was also checked:

```text
last_batch_size = 2000
last_start_index = 12000
next_index = 14000
total_eligible = 14265
updated_at = 2026-05-12 06:30:30.389000
```

Recent successful Daily Brief rows were verified for:

```text
2026-05-07
2026-05-08
2026-05-09
2026-05-12
```

A failed/stuck Daily Brief row from `2026-05-11` was confirmed as manually marked failed after no successful delivery/tracking.

---

## 3. First AI rewrite overreach issue identified and corrected

A Cheshire Live-sourced curry-house article was found with unsupported AI-generated details.

Article checked:

```text
Mongo _id: 6a030d559c85db6dad03778c
public id: 37d7c47d-84a2-4e99-a09f-87d5d40b58eb
title: Cheshire curry house plagued by yobs urges parents to control tearaway children
source: Cheshire Live
source_url: https://www.cheshire-live.co.uk/news/chester-cheshire-news/cheshire-curry-house-plagued-yobs-33924114
category: Local News
```

Problem found:

```text
verification_status = null
rewrite_status = null
ai_rewritten = null
location = null
```

The article content contained unsupported AI-generated expansion, including claims such as:

```text
- invented or unsupported anonymous customer quotes
- invented police spokesperson statements
- invented repair bills / damage details
- unsupported statements about Cheshire Police attendance
- unsupported hashtags / social-media trend claims
- broad economic claims about curry houses and the hospitality sector
- broad data claims such as British Retail Consortium / Night Time Industries Association references
```

The article was manually corrected in the database to source-limited safe copy.

Confirmed corrected state:

```text
ai_rewritten = false
is_rewritten = true
rewrite_status = manual_corrected
verification_status = manual_corrected_verified_limited
location = Cheshire
correction_reason = Removed unsupported AI-generated details and replaced with source-limited verified-safe copy.
```

---

## 4. Perplexity rewrite prompt tightened

File changed:

```text
backend/app/perplexity_service.py
```

Commit:

```text
3a6f049 Tighten AI rewrite accuracy and location verification
```

Main change:

The Perplexity rewrite role was changed from a general article writer to a careful UK local news rewrite editor.

Important new rules added to the prompt:

```text
- Source URL is the primary reference.
- Do not override source facts with guesses from the headline.
- Verify exact venue, business name, road, village, town, council area and county before naming them.
- If exact location is not confirmed, use broad wording such as "in Cheshire" or "in the local area".
- Never invent street names, town centres, quotes, anonymous residents, repair bills, smashed windows, police involvement, social media reaction, business history or previous incidents.
- Do not pad thin stories with generic background.
- Accuracy is more important than length.
- If source material is limited, write a shorter accurate article.
- Use British English and short paragraphs.
- Plain text only.
```

Temperature was lowered:

```text
old: 0.5
new: 0.2
```

This reduced creative expansion risk.

---

## 5. Existing AI-overreach articles audited and corrected

A recent content-risk scan was performed.

Initial local-audit result:

```text
recent_local_articles_checked = 35
suspects_found = 34
```

Many articles lacked rewrite/verification metadata, but only a smaller group contained obvious content-risk phrases.

A broader scan of recent articles identified and corrected several AI-risk articles.

Corrected articles included:

### The Register — fake PC / lunch article

```text
_id: 6a01bb32786635b5c03e8889
title: Who, Me? Lab worker built a fake PC to nuke his lunch
source: The Register
risk: unsupported Warrington tech park / CCTV / cost claims
```

Corrected manually.

### The Register — Schrödinger's trains article

```text
_id: 6a01bb13786635b5c03e8887
title: The latest innovation in UK public transport: Schrödinger's trains
source: The Register
risk: unsupported "a spokesperson confirmed" and Network Rail / repairs detail
```

Corrected manually.

### BBC — Gen Z birdwatchers article

```text
_id: 69ff6cae3ab76ea50644bbb2
title: Why Gen Z birdwatchers are flocking to reserves
source: BBC News
risk: unsupported hashtags, invented young visitor quote/details
```

Corrected manually.

### Cheshire Live — former village store article

```text
_id: 69fe1b4a119310b53fc76894
title: Former Cheshire village store could become children's party venue
source: Cheshire Live
risk: invented anonymous villager quote and unsupported planning/event details
```

Corrected manually.

### BBC — TikTok AI descriptions article

```text
_id: 69fdc6a3119310b53fc76879
title: TikTok scales back AI-generated video descriptions after absurd errors
source: BBC News
risk: invented absurd examples, hashtags and response detail
```

Corrected manually.

### BBC — World Cup broadcast uncertainty article

```text
_id: 69fd71b8119310b53fc7685c
title: World Cup fans in China and India face broadcast uncertainty
source: BBC News
risk: invented fan reaction, hashtags, commercial/revenue claims
```

Corrected manually.

Final scan result:

```text
articles_checked = 150
uncorrected_content_risk_articles = 0
[]
```

---

## 6. AI manual-review guard added

File changed:

```text
backend/server.py
```

Commit:

```text
8bcc6bf Hide risky AI rewrites for manual review
```

New helper added:

```text
AI_MANUAL_REVIEW_RISK_TERMS
find_ai_manual_review_hits(content)
apply_ai_manual_review_guard(article, content, ai_rewrite_used, title)
```

The import flow now tracks whether AI rewrite content was used:

```text
ai_rewrite_used = bool((detailed_content or "").strip() and detailed_content != original_content)
```

The manual-review guard is applied after RSS text sanitisation and before inserting articles.

When risky AI rewrite terms are detected, the article is now hidden and marked:

```text
ai_rewritten = true
is_rewritten = true
verification_status = needs_manual_review
rewrite_status = ai_rewrite_needs_review
archived = true
archived_at = now
archive_reason = needs_manual_review
manual_review_hidden_from_public = true
manual_review_hits = [...]
manual_review_reason = AI rewrite contained risky invented-detail phrases; verify against source before promotion or social sharing.
manual_review_created_at = now
```

Initial trigger list included:

```text
police spokesperson
wished to remain anonymous
repair bills
windows shattered
smashed bottles
councillor commented
hashtags
trending locally
British Retail Consortium
Night Time Industries Association
according to local residents
residents have rallied
one regular
closure wave
tourists seeking
source ingredients
police have been notified
officers attending
a spokesperson confirmed
millions of views
insiders suggest
analysts in recent reports
```

Backend syntax check passed before commit.

---

## 7. Admin archive manual-review display added

Files changed:

```text
backend/server.py
frontend/src/components/AdminDashboard.jsx
```

Commit:

```text
bf3e019 Show AI manual review articles in admin archive
```

Backend endpoint changed:

```text
GET /api/admin/articles/archived
```

The archived articles endpoint now includes manual-review metadata:

```text
verification_status
rewrite_status
manual_review_hits
manual_review_reason
manual_review_hidden_from_public
manual_review_created_at
source_url
```

Frontend Admin Archive list now shows:

```text
Needs manual review
Triggered by: ...
```

Verification confirmed the live frontend bundle contained:

```text
Needs manual review
Triggered by:
```

---

## 8. Admin manual-review count added

File changed:

```text
frontend/src/components/AdminDashboard.jsx
```

Commit:

```text
fb756ca Show AI manual review count in admin archive
```

Reason:

The user could not see the manual-review option because there were initially zero hidden review items. The UI only showed the badge inside the list when such an item existed.

Admin Archive header now always shows the count:

```text
X articles in archive · Y need AI manual review
```

Verified live frontend bundle contained:

```text
need AI manual review
```

---

## 9. Duplicate/new curry-house hero article hidden for manual review

A newer duplicate/reimported curry-house article appeared as the hero article and was still too AI-padded.

Article:

```text
_id: 6a03624398bf3447f623c6d9
title: Cheshire curry house plagued by yobs urges parents to control tearaway children
source_url: https://www.cheshire-live.co.uk/news/chester-cheshire-news/cheshire-curry-house-plagued-yobs-33924114
created_at: 2026-05-12T17:22:11.752503+00:00
ai_rewritten: true
verification_status: ai_rewrite_auto_screened
rewrite_status: ai_rewritten
archived: false
```

Problem:

The new guard had run but passed the article because it did not contain the exact hard trigger phrases. It still contained softer unsupported AI/editorial padding, including:

```text
desperate plea
threatening the viability
valued community dining destination
implemented various measures
post-pandemic period
similar challenges in recent years
costly security measures
local authorities and community leaders
wider concerns about antisocial behaviour
```

User did not want public correction/explanation text shown on the website.

Decision:

```text
- hide article from public website
- keep existing AI content exactly as-is in database
- send article to Admin manual-review queue
- allow editor to rewrite and restore later
```

The article was updated directly:

```text
archived = true
archived_at = now
archive_reason = needs_manual_review
verification_status = needs_manual_review
rewrite_status = ai_rewrite_needs_review
manual_review_hidden_from_public = true
manual_review_hits = [
  "soft AI overreach",
  "unsupported public-facing expansion",
  "needs editor review before restoring"
]
manual_review_reason = Hidden from public website. Keep content for editor review; rewrite cleanly before restoring.
manual_review_created_at = now
```

Verified state:

```text
archived = true
archive_reason = needs_manual_review
verification_status = needs_manual_review
rewrite_status = ai_rewrite_needs_review
content_length = 5740
```

The article was removed from public homepage/hero visibility while preserving original content for Admin editing.

---

## 10. Edit-from-manual-review and auto-restore workflow added

Files changed:

```text
backend/server.py
frontend/src/components/AdminDashboard.jsx
```

Commit:

```text
bdc4fc5 Restore manual review articles after admin edit
```

Backend change:

`PUT /api/admin/articles/{article_id}` now detects manual-review articles by:

```text
verification_status == needs_manual_review
or
archive_reason == needs_manual_review
```

When an editor saves such an article, backend automatically restores it live:

```text
archived = false
verification_status = manual_corrected_verified_limited
rewrite_status = manual_corrected
ai_rewritten = false
manual_review_restored_at = now
```

It also unsets:

```text
archived_at
archive_reason
manual_review_hidden_from_public
manual_review_hits
manual_review_reason
manual_review_created_at
```

Response now includes:

```text
restored_from_manual_review = true
```

Backend archived-articles endpoint now returns full edit fields:

```text
content
summary
source
source_url
author
tags
featured
force_live
scope
location
```

Frontend change:

Admin Archive manual-review items now show a blue edit button:

```text
Edit manual review article
```

Clicking it opens the existing article edit modal with the full content.

On save:

```text
- article is restored live automatically
- archive list refreshes
- article stats refresh
- toast confirms restore
```

Toast text added:

```text
Article Restored
Manual review article was edited and restored to the live site
```

Verified live frontend bundle contained:

```text
Edit manual review article
Manual review article was edited and restored to the live site
```

Final workflow now:

```text
1. AI-risk article is hidden automatically.
2. It appears in Admin → Archive.
3. Archive header shows manual-review count.
4. Manual-review item shows red badge and trigger phrase.
5. Editor clicks blue edit button.
6. Editor rewrites article.
7. Save automatically clears review flags and restores article live.
```

---

## 11. Facebook/OG image issue diagnosed on Guardian article

User reported a Facebook preview image issue for this article:

```text
https://cheshiretoday.co.uk/article/6a03603c98bf3447f623c6c9
```

Article metadata:

```text
_id: 6a03603c98bf3447f623c6c9
public id: 3d3e7a75-4298-4f94-8a88-699f37f13d8b
title: ‘There’s too much risk’: Britons on changing holiday plans amid Iran war
source: The Guardian
source_url: https://www.theguardian.com/business/2026/may/12/britons-changing-holiday-plans-iran-war-flight-cancellations-petrol-shortages
```

Facebook crawler test showed the article redirected correctly to canonical URL and contained:

```text
og:image
og:image:secure_url
twitter:image
```

But Facebook could not fetch the image because the image URL returned:

```text
HTTPError 401: Unauthorized - invalid signature
```

Root cause:

Database stored the original signed Guardian RSS image:

```text
https://i.guim.co.uk/...jpg?width=140&quality=85&auto=format&fit=max&s=...
```

Server social-preview normalisation was changing Guardian image query parameters:

```text
width=140 → width=1200
width=240 → width=1200
```

This broke Guardian’s signed `s=` URL.

Guardian validates the signature against the query string, so changing width invalidates the image URL.

---

## 12. Signed Guardian social image fix added

File changed:

```text
backend/server.py
```

Commit:

```text
aa725ae Preserve signed Guardian images for social previews
```

Change inside `normalize_social_image()`:

```text
if "i.guim.co.uk" in img and "s=" in img:
    return img
```

This prevents modifying signed Guardian URLs.

After deploy, Facebook crawler output preserved:

```text
width=140&quality=85&auto=format&fit=max&s=...
```

Image fetch then succeeded:

```text
STATUS = 200
CONTENT_TYPE = image/jpeg
```

But the image was small:

```text
dimensions = 140 × 112
bytes = 5337
```

So the invalid-signature issue was fixed, but a stronger Facebook preview required a valid larger Guardian image.

---

## 13. Large Guardian OG image extracted and stored

The original Guardian source article was fetched and its own valid `og:image` was extracted.

Guardian source page exposed:

```text
width=1200
height=630
valid s= signature
```

The large Guardian image was tested with Facebook user-agent:

```text
STATUS = 200
CONTENT_TYPE = image/jpeg
BYTES = 118392
DIMENSIONS = 1200 × 630
```

The Cheshire Today article image was then updated in MongoDB:

```text
_id: 6a03603c98bf3447f623c6c9
image = valid Guardian 1200x630 signed og:image URL
image_source = source_og_image
image_updated_at = now
image_update_reason = Replaced small Guardian RSS image with valid large signed Guardian og:image for Facebook preview.
```

Follow-up Facebook crawler output confirmed Cheshire Today now emits:

```text
og:image = Guardian 1200x630 signed URL
og:image:secure_url = same
twitter:image = same
```

Final image fetch result from live OG tag:

```text
STATUS = 200
CONTENT_TYPE = image/jpeg
BYTES = 118392
DIMENSIONS = 1200 × 630
```

The Facebook image-preview issue for this article is fixed. Facebook may still need Meta Sharing Debugger “Scrape Again” because Facebook can cache old previews.

---

## 14. Newsletter bounce from dummy unsubscribe-test address investigated

User received a delivery failure email for:

```text
unsubscribe-test-1778535592@example.co.uk
```

Bounce summary:

```text
recipient's email system refused to accept a connection
target computer actively refused it
```

Assessment:

```text
- this is a dummy/test address
- not a Cheshire Today website fault
- not evidence the unsubscribe system is broken
- likely delayed bounce from an older test send after repeated delivery attempts
```

Live database checks:

Main subscribers collection:

```text
found = false
```

Whole live database recent scan for exact address:

```text
matches = 0
[]
```

Conclusion:

The address is not currently in the live database. The bounce almost certainly came from a previous test send or queued retry.

---

## 15. Newsletter reserved/test email filtering hardened

Grep showed existing code filtered:

```text
@example.com
```

But it did not filter:

```text
@example.co.uk
unsubscribe-test-*
other example.* reserved domains
```

File changed:

```text
backend/server.py
```

Commit:

```text
90d284f Block reserved test emails from newsletter sends
```

Added shared helper:

```text
NEWSLETTER_EMAIL_REGEX
is_deliverable_newsletter_email(email: str)
```

The helper blocks:

```text
- empty email
- invalid email format
- local part beginning unsubscribe-test-
- any domain starting example.
- Cheshire Today internal test-style addresses where local part includes test and domain includes cheshiretoday
```

Examples now blocked:

```text
unsubscribe-test-1778535592@example.co.uk
anything@example.com
anything@example.co.uk
test@cheshiretoday...
```

Updated code paths to use the helper:

```text
cleanup_invalid_emails()
send_weekly_roundup_batch_test()
send_scheduled_news_digest()
send_weekly_roundup_email()
```

Backend syntax check passed.

Commit was pushed and backend deployed. Post-deploy health check:

```json
{
  "status": "healthy",
  "service": "cheshire-news"
}
```

---

## 16. Commits pushed during this session

The following commits were pushed to `origin/full-scrape-prod`:

```text
3a6f049 Tighten AI rewrite accuracy and location verification
8bcc6bf Hide risky AI rewrites for manual review
bf3e019 Show AI manual review articles in admin archive
fb756ca Show AI manual review count in admin archive
bdc4fc5 Restore manual review articles after admin edit
aa725ae Preserve signed Guardian images for social previews
90d284f Block reserved test emails from newsletter sends
```

---

## 17. Deployment and verification status

Backend:

```text
healthy after deploy
```

Frontend:

```text
manual-review Admin UI deployed and verified by live bundle text search
```

Verified live frontend strings:

```text
Needs manual review
Triggered by:
need AI manual review
Edit manual review article
Manual review article was edited and restored to the live site
```

Verified live Facebook crawler image fix:

```text
Article: 6a03603c98bf3447f623c6c9
OG image: Guardian 1200x630 signed URL
Fetch status: 200
Content type: image/jpeg
Dimensions: 1200 × 630
```

Newsletter:

```text
dummy unsubscribe-test address not in current live DB
reserved/test email helper now blocks similar addresses in future sends
```

---

## 18. Current operational state after this update

Cheshire Today now has:

```text
- tighter AI rewrite prompt
- lower Perplexity rewrite temperature
- source-first location verification rules
- database corrections for known AI-overreach articles
- automatic hiding of risky future AI rewrites
- Admin Archive manual-review queue visibility
- Admin Archive manual-review count
- blue edit button for manual-review articles
- save-after-edit auto-restore workflow
- Guardian signed image preservation for social previews
- fixed Guardian Facebook OG image for affected article
- newsletter reserved/test email filtering across major send paths
```

The site is safer editorially because AI-risk rewrites no longer need to appear publicly. They can be hidden, reviewed, edited and restored through Admin.

---

## 19. Recommended follow-up backlog

### A. Expand soft AI-overreach guard

The current guard catches hard invented-detail signals. It should also catch softer AI-padding terms that slipped through once, such as:

```text
threatening the viability
valued community
implemented various measures
post-pandemic period
similar challenges in recent years
costly security measures
local authorities and community leaders
wider concerns about antisocial behaviour
hospitality venues across Cheshire and beyond
```

### B. Add Guardian source-og-image enrichment

Guardian RSS images can be too small. Safer future approach:

```text
- do not alter signed Guardian URLs
- fetch Guardian source article og:image
- store valid large signed og:image when available
```

This avoids both:

```text
- broken 401 invalid-signature images
- tiny 140px Facebook previews
```

### C. Add dedicated Admin Manual Review tab/filter

Current workflow uses Admin → Archive. A better future UI would be:

```text
Admin → Manual Review
```

or an Archive filter:

```text
Show: All archived / Needs manual review / Manual admin / Ratio rebalance / Duplicate
```

### D. Add periodic audit for soft AI overreach

Run a scheduled/admin audit for:

```text
verification_status = ai_rewrite_auto_screened
```

combined with soft-risk phrases.

### E. Use Meta Sharing Debugger after OG image fixes

After fixing article previews, use Facebook Sharing Debugger:

```text
Scrape Again
```

because Facebook may cache the previous no-image or bad-image preview.


---

## 20. May 13, 2026 continuation — Google News sitemap indexing fix and live Facebook preview image audit

This continuation addressed two urgent live-discovery issues:

1. Google Search Console showed recent article indexing had stalled, with the last meaningful indexing around 1 May.
2. A newly shared article link on Facebook did not show an image preview.

Both issues were investigated against the live production site and fixed without changing the frontend layout.

### A. Google Search Console indexing issue diagnosed

User supplied Google Search Console screenshots showing:

```text
sitemap.xml       = Success, 547 discovered pages
news-sitemap.xml  = Error, 0 discovered pages
api/sitemap.xml   = old legacy sitemap path
```

The live news sitemap was checked directly:

```bash
curl -sS https://cheshiretoday.co.uk/news-sitemap.xml | sed -n '1,80p'
```

Live output showed the sitemap was valid XML but empty:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
</urlset>
```

This exactly explained the Search Console error:

```text
Missing XML tag
Parent tag: urlset
Missing tag: url
Discovered pages: 0
```

Conclusion:

```text
Google was not blocked, but the live news sitemap had no <url> entries, so recent news article discovery was broken.
```

### B. Root cause of empty `news-sitemap.xml`

The active route was found in:

```text
backend/server.py
```

Route:

```text
/news-sitemap.xml
```

The broken query was:

```python
articles = await db.articles.find(
    {"publishedDate": {"$gte": cutoff_date.isoformat()}},
    {'_id': 1, 'id': 1, 'title': 1, 'publishedDate': 1, 'category': 1}
).sort('publishedDate', -1).limit(1000).to_list(1000)
```

The problem was that recent live articles existed, but article date fields were mixed between:

```text
publishedDate
created_at
string ISO values
timezone-aware ISO strings
```

Example fresh live article data showed:

```text
publishedDate: 2026-05-13T05:01:19
created_at:    2026-05-13T05:15:05.393605+00:00
```

The news sitemap was filtering only by `publishedDate >= cutoff_iso`, which returned zero rows.

### C. Google News sitemap backend fix applied

File changed:

```text
backend/server.py
```

Commit:

```text
b6e336c Fix Google News sitemap recent article query
```

Fix summary:

```text
- added cutoff_iso
- excluded archived articles
- queried both publishedDate and created_at
- supported both datetime and ISO-string date formats
- included created_at in projection
- sorted by created_at first
- publication date fallback now uses publishedDate or created_at
```

The corrected query now checks:

```python
{
    "archived": {"$ne": True},
    "$or": [
        {"publishedDate": {"$gte": cutoff_date}},
        {"publishedDate": {"$gte": cutoff_iso}},
        {"created_at": {"$gte": cutoff_date}},
        {"created_at": {"$gte": cutoff_iso}},
    ],
}
```

Backend syntax check passed:

```bash
python3 -m py_compile backend/server.py
```

Commit was pushed to:

```text
origin/full-scrape-prod
```

### D. Live Google News sitemap verification after deploy

After deploy, the live sitemap was rechecked:

```bash
curl -sS https://cheshiretoday.co.uk/news-sitemap.xml | python3 -c "import sys,re; x=sys.stdin.read(); print('url_count=', x.count('<url>')); print('news_title_count=', x.count('<news:title>')); m=re.search(r'<loc>(.*?)</loc>', x); print('first_loc=', m.group(1) if m else 'NONE')"
```

Verified result:

```text
url_count= 71
news_title_count= 71
first_loc= https://cheshiretoday.co.uk/article/04d788bf-e0ad-46d0-9a5f-b57da35e6731/10-pictures-from-westminster-park-s-80th-anniversary-celebrations
```

Header verification:

```bash
curl -I https://cheshiretoday.co.uk/news-sitemap.xml
```

Verified result:

```text
HTTP/2 200
content-type: application/xml
cache-control: public, max-age=3600
x-render-origin-server: uvicorn
```

`robots.txt` was also verified and still advertises both sitemaps:

```text
Sitemap: https://cheshiretoday.co.uk/sitemap.xml
Sitemap: https://cheshiretoday.co.uk/news-sitemap.xml
```

And Googlebot-News is allowed:

```text
User-agent: Googlebot-News
Allow: /
Allow: /article/
```

Final conclusion:

```text
The live Google News sitemap error was fixed at source. Search Console should clear the missing-url error after Google re-reads the corrected sitemap.
```

Operational instruction:

```text
In Google Search Console, resubmit news-sitemap.xml and request indexing on one fresh article URL after live test passes.
```

---

### E. Facebook preview image issue reported for a Guardian article

User reported no Facebook preview image for:

```text
https://cheshiretoday.co.uk/article/6a04b1e56903ac2ecb7d896c
```

The article resolved to:

```text
/article/65783cd6-7c63-4a6d-93d6-6772a0e245fb/single-women-are-buying-more-houses-the-men-they-are-dating-are-not-responding-w
```

Facebook crawler test showed the article did have OG tags, but the image was a small Guardian RSS thumbnail:

```text
og:image = https://i.guim.co.uk/.../3000.jpg?width=140&quality=85&auto=format&fit=max&s=...
```

Therefore the problem was not missing OG tags. It was that Facebook received a valid but tiny Guardian `width=140` signed image.

### F. Initial wrong-route patch and correction

An initial patch was added to the SEO crawler route:

```text
get_seo_article_page(...)
```

Commit:

```text
9ce8f8d Normalize social preview images for article crawler HTML
```

This patch was syntactically valid, but live testing showed Facebook output still contained the old `width=140` Guardian image.

Conclusion:

```text
The first patch targeted a valid crawler/SEO route, but not the active route serving Facebook for canonical article URLs.
```

The active Facebook route was then identified as:

```text
serve_article_html(...)
```

around the later article HTML renderer in `backend/server.py`.

### G. Root cause in active Facebook article route

The active route already had `normalize_social_image(...)`, but included this early return:

```python
if "i.guim.co.uk" in img and "s=" in img:
    return img
```

This was previously added for a valid reason:

```text
Guardian image URLs are signed. Editing width=140 to width=1200 breaks the signature and causes 401 invalid signature / missing signature errors.
```

But the side effect was:

```text
small signed Guardian RSS image URLs were preserved as width=140, which is too small for reliable Facebook previews.
```

Testing proved the source Guardian page itself exposed a valid large signed OG image:

```text
width=1200
height=630
valid s= signature
```

### H. Correct Guardian social image fix applied

File changed:

```text
backend/server.py
```

Commit:

```text
8d8d2d3 Fetch large Guardian social image for Facebook previews
```

Correct behaviour now:

```text
If stored Guardian image is signed and small (width=140 or width=240), and the article has a Guardian source_url, fetch the Guardian source page and extract its valid large signed og:image.
```

The route no longer manually edits Guardian signed image dimensions. It uses the original Guardian page’s own valid `og:image` instead.

This avoids both failure modes:

```text
- invalid Guardian signature from changing query params manually
- tiny 140px Guardian preview images on Facebook
```

### I. Live Facebook crawler verification after fix

The original problem article was rechecked with:

```bash
curl -sSL -A "facebookexternalhit/1.1" "https://cheshiretoday.co.uk/article/6a04b1e56903ac2ecb7d896c" | grep -iE "og:image|twitter:image" | head -n 10
```

Verified output changed from:

```text
width=140
```

to:

```text
width=1200
height=630
```

Example verified output:

```text
og:image = https://i.guim.co.uk/.../3000.jpg?width=1200&height=630&quality=85&auto=format&fit=crop&...&s=22f3fa7a7a27cf99dc32ea361313b921
og:image:secure_url = same
Twitter image = same
```

The fix was then tested against another recent Guardian article:

```text
6a04b1c36903ac2ecb7d896b
```

Verified result:

```text
Guardian og:image now emits width=1200 height=630 valid signed URL
```

### J. Source-wide Facebook preview audit completed

A live source audit was run using the latest 80 live articles.

Representative sources found:

```text
Wilmslow Town Council
Cheshire Live
BBC News
The Register
The Guardian
Sky News
MoneySavingExpert
```

Each source was tested with Facebook user-agent against live article URLs.

Verified output:

```text
Wilmslow Town Council | image present
Cheshire Live         | /ALTERNATES/s1200/
BBC News              | /standard/1024/
The Register          | image present, width=800
The Guardian          | valid signed width=1200 image
Sky News              | strong 1920x1080 image
MoneySavingExpert     | image present, 800x600
```

Important verified source rules now active:

```text
Guardian      = fetch valid large signed source og:image when stored signed RSS image is too small
Cheshire Live = upgrade /ALTERNATES/s615/, /s615b/, /s810/ to /s1200/
BBC           = upgrade /240/, /320/, /480/ to /1024/
No image      = fallback to https://cheshiretoday.co.uk/social-share.jpg
```

Conclusion:

```text
Current major active article sources now emit Facebook-ready og:image URLs. Future Guardian, Cheshire Live/Reach and BBC articles are materially safer for Facebook previews.
```

### K. Remaining watch points

1. Facebook may cache old previews.

For any article pasted into Facebook before the fix:

```text
Use Meta Sharing Debugger -> Scrape Again
```

2. The Register currently emits:

```text
https://image.theregister.com/?imageId=...&width=800
```

This appears acceptable. Do not patch unless a real failure appears.

3. The first SEO-route patch from `9ce8f8d` is harmless but was not the route responsible for this Facebook issue. The correct active fix is `8d8d2d3`.

### L. Commits pushed during this continuation

```text
b6e336c Fix Google News sitemap recent article query
9ce8f8d Normalize social preview images for article crawler HTML
8d8d2d3 Fetch large Guardian social image for Facebook previews
```

### M. Updated operational state after this continuation

Cheshire Today now has:

```text
- fixed live Google News sitemap with valid recent article URLs
- news-sitemap.xml returning 71 valid news article entries at verification time
- robots.txt correctly advertising both sitemap.xml and news-sitemap.xml
- Googlebot-News allowed for /article/ URLs
- live Facebook article preview route fixed for small signed Guardian RSS thumbnails
- Guardian source-page OG image extraction for valid large signed previews
- verified Facebook image output for Guardian, Cheshire Live, BBC, Sky News, The Register, MoneySavingExpert and Wilmslow Town Council
```

Recommended next action:

```text
Resubmit news-sitemap.xml in Google Search Console and request indexing for one fresh article. Use Facebook Sharing Debugger -> Scrape Again for any article previously cached with a missing/small image preview.
```
---

## May 18, 2026 — sitemap quality cleanup, GA4/Search Console review, article-generation lock observation, Render-log interpretation, and mobile article reading-flow upgrade

### A. Scope of this continuation
This continuation focused on four practical production-quality areas:

1. cleaning the public XML sitemaps so Google is not being repeatedly fed low-value/off-strategy article URLs,
2. reviewing GA4/Search Console signals without overreacting to incomplete analytics data,
3. checking a missed 18:00 article-generation run and deciding not to disturb scheduler locks unnecessarily,
4. improving mobile article-page quality for Facebook-driven traffic while avoiding a cluttered or sales-heavy reader experience.

The guiding strategy remained unchanged:

```text
Cheshire Today = local + business/finance + AI/tech authority.
Avoid crime-heavy filler, lifestyle filler, weak national filler, and salesy guide placements on simple community articles.
```

No full scrape was run during this continuation because the main work was sitemap filtering and frontend article-page UX. Full scrape was explicitly deferred unless later needed for import/scrape/article-generation testing.

### B. Initial sitemap quality audit result
A sitemap/article-quality audit showed that the active sitemap pool still contained too many weak or off-strategy URLs.

Representative audit output at the beginning of the work:

```text
total = 184
kept_by_category = 181
category_counts = {
  'Local News': 31,
  'Business': 49,
  'Tech': 80,
  'Finance': 19,
  'Tax': 2,
  'UK News': 3
}
sample_bad_kept = [
  "Woman 'deliberately knocked off her bike' in Winsford hit-and-run",
  "M6 updates as smash between 'car and truck' brings Cheshire motorway to a stop",
  'Live updates as emergency services respond to Cheshire train station crash',
  "Utah tells porn sites to take the P out of VPNs, and it's their fault that they can't",
  'Starwatch: A young crescent moon journeys past Venus and Jupiter'
]
```

Conclusion:
- the sitemap was still too permissive,
- weak accident/crime/porn/astronomy/general-filler URLs were being submitted to search engines,
- this did not match the Cheshire Today positioning or the new Search Console cleanup direction.

### C. Main sitemap filtering tightened in `backend/server.py`
The main sitemap generator was updated inside `generate_sitemap()`.

Key changes:

1. Sitemap query changed from all articles to active, non-archived articles only:

```python
{"archived": {"$ne": True}}
```

2. Projection was kept light and included only fields needed for sitemap output:

```python
{'_id': 1, 'id': 1, 'publishedDate': 1, 'category': 1, 'image': 1, 'title': 1}
```

3. A strategic category allow-list was added:

```python
{"Local News", "Business", "Finance", "Tax", "Property", "Tech", "AI"}
```

4. A sitemap title exclusion list was added to block obvious low-value / off-strategy pages from the main sitemap, including patterns such as:

```text
sports quiz
crash
smash
hit-and-run
emergency services
knocked off
police
court
jailed
charged
murder
assault
john fury
nigel farage
cameo
porn
starwatch
moon
period drama
free to watch
hair dryer
cruise ship
infection risk
```

5. Sitemap inclusion now requires:

```text
- title present
- image present
- category in the strategic category allow-list
- title not matching any exclusion pattern
```

6. Article ID selection in sitemap output was corrected to prefer Mongo `_id` first:

```python
article_id = str(article.get("_id") or article.get("id") or "")
```

Backend syntax check passed:

```bash
python3 -m py_compile backend/server.py
```

Commit created:

```text
c73b68e — Tighten sitemap article quality filters
```

### D. Main sitemap verification after first filter pass
After deployment/verification, the main sitemap no longer showed the first bad sample terms.

Verification command used:

```bash
curl -sS "https://cheshiretoday.co.uk/sitemap.xml" | grep -n "weekly-sports-quiz\|discussion-over-the-future-of-sark\|nigel-farage\|john-fury\|train-station-crash\|hit-and-run\|starwatch\|hair-dryer\|porn-sites" | head -n 30
```

Result:

```text
empty output
```

Main sitemap URL count during this phase:

```text
236 <loc> entries
```

Later after additional filtering/deploy state, `/sitemap.xml` and `/api/sitemap.xml` were verified at:

```text
224 <loc> entries
```

### E. News sitemap quality issue found and fixed
After the main sitemap cleanup, the Google News sitemap still contained weak/off-strategy URLs.

Bad examples still present in `/news-sitemap.xml` before the news-sitemap patch included:

```text
Woman 'deliberately knocked off her bike' in Winsford hit-and-run
Utah tells porn sites to take the P out of VPNs...
Live updates as emergency services respond to Cheshire train station crash
Starwatch: A young crescent moon journeys past Venus and Jupiter
Dyson Supersonic Travel hair dryer review...
```

This confirmed that `generate_news_sitemap()` needed the same strategic-quality logic as the main sitemap.

### F. News sitemap filtering tightened in `backend/server.py`
`generate_news_sitemap()` was patched with:

1. strategic news category allow-list:

```python
{"Local News", "Business", "Finance", "Tax", "Property", "Tech", "AI"}
```

2. matching low-value/off-strategy title exclusions:

```text
sports quiz
crash
smash
hit-and-run
emergency services
knocked off
police
court
jailed
charged
murder
assault
john fury
nigel farage
cameo
porn
starwatch
moon
period drama
free to watch
hair dryer
cruise ship
infection risk
```

3. helper function:

```python
def include_article_in_news_sitemap(article):
    ...
```

4. per-article skip before XML output:

```python
if not include_article_in_news_sitemap(article):
    continue
```

5. article ID preference corrected to Mongo `_id` first:

```python
article_id = str(article.get('_id') or article.get('id') or '')
```

Commit created:

```text
634043f — Tighten news sitemap article quality filters
```

Pushed to `full-scrape-prod`.

Production health check after deploy:

```json
{
  "status": "healthy",
  "service": "cheshire-news"
}
```

Post-patch news sitemap verification for the original bad terms returned empty output.

News sitemap count after this pass:

```text
46 <loc> entries
```

### G. Second filler pass added to both sitemap filters
After the first sitemap/news-sitemap cleanup, a further review of recent sitemap/news-sitemap output identified more filler that still did not belong in search feeds.

Examples identified from live API/news sitemap review included:

```text
Doom soundtrack added to National Recording Registry
F-35 software delays leave UK buying time with US glide bombs
Nothing Phone 4a Pro review
Pokemon Mega Evolution Trails...
Cheshire mum lost everything after fire...
I visited Alton Towers...
US pandemic preparedness article
How can the PM improve the lives of Londoners?
We need working-class voices...
Driving test waiting-list item
GPS jamming in the Iran war
Cloud-managed earbuds...
```

A second exclusion pass was added to both sitemap and news-sitemap title pattern lists:

```text
doom soundtrack
f-35
nothing phone
pokemon
alton towers
fire ripped
lost everything
pandemic preparedness
londoners
working-class voices
driving test
gps jamming
cloud-managed earbuds
```

Commit created:

```text
29ddb09 — Further tighten sitemap filler exclusions
```

Pushed to `full-scrape-prod`.

Production health after deployment remained healthy.

Final sitemap verification at this stage:

```text
main sitemap: 224 <loc> entries
news sitemap: 34 <loc> entries
bad-sample grep checks: empty output
robots.txt lists both sitemap.xml and news-sitemap.xml
/api/sitemap.xml also returns 224 entries
```

Robots sitemap declaration confirmed:

```text
# Sitemaps
Sitemap: https://cheshiretoday.co.uk/sitemap.xml
Sitemap: https://cheshiretoday.co.uk/news-sitemap.xml
```

### H. Search Console / not-indexed guidance from this continuation
The correct decision was not to manually “remove” every not-indexed URL.

Current approach:

```text
- keep the cleaned sitemap as the canonical signal,
- stop submitting weak/off-strategy article URLs,
- let Google naturally drop older weak URLs over time,
- monitor Search Console after the sitemap cleanup settles.
```

Action to carry forward:

```text
Monitor Search Console 3–7 days after sitemap cleanup, especially examples under “Crawled – currently not indexed”.
```

If the same poor-quality URLs still dominate later, then review whether they are still internally linked, still active, or need archive/noindex handling. Do not mass-remove Search Console URLs blindly.

### I. Missed 18:00 article-generation check
The user asked whether the missed 18:00 article generation could be run manually.

First, the latest visible articles were checked:

```bash
curl -sS "https://cheshiretoday.co.uk/api/articles?limit=8" | python3 -c "import sys,json; rows=json.load(sys.stdin); [print(str(a.get('publishedDate'))+' | '+str(a.get('category'))+' | '+str(a.get('title'))) for a in rows[:8]]"
```

Then the manual trigger was called:

```bash
curl -sS -X POST "https://cheshiretoday.co.uk/api/trigger-daily-generation" | python3 -m json.tool
```

API response:

```json
{
  "success": true,
  "message": "Daily article generation triggered successfully"
}
```

However, Render logs showed the important real result:

```text
⏭️ Another server is handling article generation, skipping...
```

Relevant code inspection showed `daily_article_generation()` uses an hourly distributed lock:

```python
lock_key = f"article_gen_{now.strftime('%Y%m%d%H')}"
```

and skips when the hourly lock already exists or has not expired.

Important conclusion:
- the trigger endpoint returned a generic success response even though the job skipped due to lock protection,
- no new articles appeared immediately after the manual trigger,
- this was not treated as an emergency because the distributed lock is designed to prevent duplicate article generation,
- decision was to leave it alone and wait for the next scheduled run rather than manually deleting scheduler locks.

Carry-forward instruction:

```text
Leave skipped manual article generation alone for now.
Verify the next scheduled article generation run creates fresh articles before investigating scheduler locks.
```

### J. Render logs interpreted and follow-up cleanup noted
Render logs reviewed during this continuation contained several common request types.

#### 1. Normal website/API traffic
Examples:

```text
GET /api/articles?limit=80 200 OK
GET /api/authority-pages?limit=10&status=published 200 OK
GET /api/affiliates/public 200 OK
GET /static/js/main...js 200 OK
GET /static/css/main...css 200 OK
```

Interpretation:
- normal page/API/static asset activity.

#### 2. Sponsored placement impression logs
Examples:

```text
POST /api/sponsored-placements/retreat-social-club-homepage_sidebar-20260701/impression 200 OK
POST /api/sponsored-placements/retreat-social-club-article_mobile-20260701/impression 200 OK
```

Interpretation:
- sponsored placement impression endpoints are firing successfully.
- However, some of these requests were likely from Facebook/Meta crawlers or bots loading the page.

Carry-forward analytics cleanup:

```text
Consider filtering obvious bots/crawlers from sponsored advert impression tracking so Meta/Facebook crawler traffic does not inflate sponsor impression counts.
```

#### 3. Email open tracking logs
Examples:

```text
GET /api/email/track/open/daily_brief_... 200 OK
```

Interpretation:
- newsletter open tracking pixels are being hit.
- Some opens may be from privacy/security scanners; do not assume every open is a human read without deeper verification.

#### 4. Health HEAD 404 noise
Examples:

```text
HEAD /api/health 404 Not Found
GET /api/health 200 OK
```

Interpretation:
- `GET /api/health` works,
- `HEAD /api/health` currently returns 404 because there is no HEAD handler for that route,
- this is noisy but not urgent.

Backlog technical cleanup:

```text
Add support for HEAD /api/health later to prevent Render/bot health-probe 404 noise.
```

#### 5. 301 moved permanently logs for article URLs
Many logs showed:

```text
GET /article/{id} 301 Moved Permanently
GET /article/{id}/{slug} 200 OK
```

Interpretation:
- this is expected canonicalisation behavior,
- old ID-only article URLs redirect to canonical slug URLs,
- repeated requests from Facebook/Meta crawler IPs are normal when a link is shared or previewed.

No action required unless real user navigation breaks.

### K. GA4 / traffic quality review and newsletter caution
A GA4 review was performed using the user’s screenshots and navigation through GA4.

High-level conclusion:

```text
Traffic is growing.
Facebook is driving most visits.
Sitemaps are now cleaner.
Article/social link handling is healthier.
Newsletter unsubscribe/preference page traffic needs subscriber-database verification before strategy changes.
```

Important caution:
- `/unsubscribe` and `/newsletter/preferences` appearing in GA4 page views does not automatically prove mass human churn,
- some traffic may be from email security tools, privacy scanners, link scanners, or prefetchers,
- the real newsletter subscriber database must be checked before changing the newsletter strategy.

Carry-forward newsletter checks:

```text
- Review total newsletter subscribers.
- Review active subscribers.
- Review unsubscribed subscribers.
- Review unsubscribed in the last 7 days.
- Review unsubscribes after the latest Daily Brief.
- Investigate why /unsubscribe and /newsletter/preferences appear in top GA4 pages.
- Determine whether that traffic is real user churn or email security/privacy scanning.
- Do not change newsletter strategy until real subscriber/unsubscribe data is verified.
```

### L. Mobile article-page quality audit before changes
The mobile article page was audited because Facebook traffic is a major traffic driver and the article page needs to earn trust quickly.

Initial inspection of `frontend/src/pages/ArticlePageV2.jsx` showed:

```text
- duplicate mobile “Continue reading” buttons existed,
- a mobile sponsored advert appeared before the article body,
- source attribution could show while the article was still collapsed,
- the guide block could show irrelevant commercial recommendations on simple local articles,
- mobile reading flow felt repetitive when standfirst + “Why this matters” + intro all appeared together.
```

Initial target:

```text
Make the mobile article page feel cleaner, less repetitive, less salesy, and more trustworthy for Facebook-driven readers.
```

### M. First mobile header readability improvement shipped
First safe change:
- removed the duplicate mobile `Continue reading` button above the image,
- added a standfirst/description under headline metadata.

Build passed:

```bash
npm --prefix frontend run build
```

Commit:

```text
20819f2 — Improve mobile article header readability
```

Pushed to `full-scrape-prod`.

Frontend deploy verified with live bundle:

```text
main.c0907484.js
```

Live bundle verification confirmed old duplicate wording was gone:

```bash
curl -sS "https://cheshiretoday.co.uk/static/js/main.c0907484.js" | grep -o "Continue reading full article\|Continue reading" | sort | uniq -c
```

Result:

```text
1 Continue reading full article
```

Meaning:
- one old duplicate button had been removed,
- only the inner collapsed article continuation remained at that stage.

### N. “Why this matters” experiment tested and rejected
A mobile-only `Why this matters` box was then tested below the article image.

It generated contextual bullets for:
- finance,
- business,
- local,
- tech/AI,
- fallback general stories.

The box was visually tested locally and initially improved perceived professionalism.

However, user review correctly identified it as repetitive on real local/community articles because the page then read like:

```text
standfirst
Why this matters
article intro
```

Conclusion:
- `Why this matters` is useful in principle but too repetitive in this exact mobile article flow,
- it was removed from the final shipped implementation,
- final approach became simpler and more newspaper-like.

### O. Final mobile article reading flow implemented
Final accepted mobile flow:

```text
Headline
Date / read time / Share
Image
One short article starter paragraph
Read more… button
Sponsored advert below the starter/read-more area
Newsletter / more stories after that
```

After tapping `Read more…`:

```text
Full article body appears below the image
Source appears after the article body
Sponsored advert remains below the article/full-article area
```

Key implementation details in `ArticlePageV2.jsx`:

1. `buildDescription(article)` was fixed so it no longer cuts words mid-word.

Old behavior:

```python
summary.slice(0, 200)
```

New behavior:

```javascript
const source = summary.length >= 40 ? summary : safeText(article?.content).trim();
const compact = source.replace(/\s+/g, " ").trim();
if (compact.length <= 200) return compact;
const clipped = compact.slice(0, 197).replace(/\s+\S*$/, "").trim();
return `${clipped || compact.slice(0, 197).trim()}...`;
```

2. Mobile intro was shortened from two paragraphs to one paragraph:

```javascript
mobileIntroContent: paragraphs.slice(0, 1).join("\n\n"),
mobileRemainingContent: paragraphs.slice(1).join("\n\n"),
```

3. Desktop standfirst remains, but mobile hides it to avoid repetition:

```jsx
<p className="hidden sm:block ...">
```

4. When collapsed on mobile, the page now shows a short starter card with `Read more…` instead of rendering the full body or a second continuation button.

5. Full article body is conditionally rendered only when:

```javascript
!isMobileView || !mobileRemainingContent || articleExpanded
```

6. Source attribution is hidden until the full mobile article is expanded:

```javascript
(!isMobileView || !mobileRemainingContent || articleExpanded) && (article.source || article.source_url)
```

7. Mobile sponsored placement was moved lower:

```jsx
<div className="sm:hidden mt-6">
  <SponsoredPlacement placement="article_mobile" compact />
</div>
```

This avoids showing the advert before the reader sees any article text.

### P. Irrelevant article guide block fixed for simple local articles
During mobile testing, the Wilmslow Annual Town Meeting article showed an irrelevant `Best options based on this story` block with guide suggestions such as:

```text
Best accounting software
Self-storage
Virtual office services
```

This was not appropriate for a simple local community article and damaged trust.

Root cause:
- `GuidesInlinePromo` had a generic `fallbackOrder`, so even with no relevant commercial match it could fall back to generic monetised guides.

Fix implemented:

1. Removed the generic fallback order from `GuidesInlinePromo`.

2. Guide promo pool now uses only genuinely picked monetised guides:

```javascript
const monetisedPool = picked.filter(
  (item) => String(item?.slug || "").trim() !== "council-tax-bands-cheshire"
);

const pool = monetisedPool;
```

3. Added `shouldShowArticleGuidePromo`:

```javascript
const shouldShowArticleGuidePromo = useMemo(() => {
  const picked = pickGuidesForPillar(guides, pillarLabel, contextToolType);
  return picked.some((item) => String(item?.slug || "").trim() !== "council-tax-bands-cheshire");
}, [guides, pillarLabel, contextToolType]);
```

4. Wrapped the entire `Best options based on this story` block so it only appears when there is a real monetised guide match:

```jsx
{shouldShowArticleGuidePromo && (
  <section ...>
    ...
  </section>
)}
```

Result:
- irrelevant guide block no longer shows on the Wilmslow local/community article,
- article pages can still show commercial guide blocks where there is a genuine finance/business/property/AI/tech match,
- this keeps monetisation active but less salesy and more context-sensitive.

### Q. Final local visual QA before commit
Local static build/serve was used for visual QA.

Build command:

```bash
npm --prefix frontend run build
```

Local static serve ran on:

```text
http://localhost:3000
http://192.168.4.86:3000
```

Test article used:

```text
/article/6a0b3a948291326f210f02ee/wilmslow-residents-invited-to-annual-town-meeting
```

Final user-approved visual state:

```text
Article starter ✅
Read more… ✅
Sponsored advert below ✅
Irrelevant “Best options” block removed ✅
Newsletter appears after advert ✅
```

### R. Final mobile article flow commit, deploy, and live verification
Commit created:

```text
48611c9 — Improve mobile article reading flow
```

Changed file:

```text
frontend/src/pages/ArticlePageV2.jsx
```

Commit summary:

```text
48 insertions, 40 deletions
```

Pushed to `full-scrape-prod`:

```bash
git push origin full-scrape-prod
```

Frontend deploy verified live:

```text
main.4a064ee4.js
```

Live bundle check:

```bash
curl -sS "https://cheshiretoday.co.uk/static/js/main.4a064ee4.js" | grep -o "Read more" | sort | uniq -c
```

Result:

```text
1 Read more
```

Old wording check showed the old collapsed button was gone:

```text
Old “Continue reading full article” removed ✅
```

`Best options based on this story` still appears in the bundle because the component still exists for relevant commercial articles, but the Wilmslow article no longer shows it due to the new conditional rendering.

User confirmed final live result:

```text
Perfect
```

### S. Final code state after this continuation
Important commits from this continuation:

```text
c73b68e — Tighten sitemap article quality filters
634043f — Tighten news sitemap article quality filters
29ddb09 — Further tighten sitemap filler exclusions
20819f2 — Improve mobile article header readability
48611c9 — Improve mobile article reading flow
```

Final live frontend bundle after the article-flow deploy:

```text
main.4a064ee4.js
```

Final sitemap state verified during this continuation:

```text
/sitemap.xml      = 224 <loc> entries
/api/sitemap.xml  = 224 <loc> entries
/news-sitemap.xml = 34 <loc> entries
robots.txt lists both sitemap.xml and news-sitemap.xml
```

### T. Current to-do list / next-phase backlog added from this continuation
Add these to the project backlog:

```text
1. Review actual newsletter subscriber status, not just GA4 page views:
   - total subscribers
   - active subscribers
   - unsubscribed subscribers
   - unsubscribed in the last 7 days
   - unsubscribes after the latest Daily Brief

2. Investigate why /unsubscribe and /newsletter/preferences are appearing among top GA4 pages:
   - determine whether traffic is real user churn
   - or email security/privacy scanner traffic

3. Do not change newsletter strategy until real subscriber/unsubscribe data is verified.

4. Monitor GA4 after sitemap cleanup:
   - main sitemap now 224 URLs
   - news sitemap now 34 URLs
   - check Search Console again after 3–7 days for “Crawled – currently not indexed” samples

5. Later technical cleanup:
   - support HEAD /api/health to prevent Render/bot health-probe 404 noise

6. Later analytics cleanup:
   - consider filtering obvious bots/crawlers from sponsored advert impression tracking
   - especially Meta/Facebook crawler traffic inflating sponsor impression counts

7. Leave skipped manual article generation alone for now:
   - verify next scheduled article generation run creates fresh articles before investigating scheduler locks
```

### U. Operating rule added for project-state documentation
The user clarified and this must be carried forward:

```text
When asked to update the current state/source .md file, update the single chat-source project state file only.
Do not ask the user to run terminal find commands in the repo/project root unless they explicitly ask for a repo file update.
Do not split project-state updates into separate small update files.
Append detailed work summaries to the same single current-state file in chat sources so the project has one continuous source of truth.
```

This continuation is therefore appended into the same single project-state master file rather than kept as a separate update document.

### V. Recommended continuation prompt after this update
Use this continuation instruction for the next Cheshire Today coding/work session:

```text
Continue Cheshire Today from the current single chat-source project state file. Respect workflow: check current state first, one command at a time, no manual file edits unless absolutely necessary, use grep not rg, verify after each change, and do not run full scrape unless necessary for import/scrape testing. Assume the sitemap cleanup is live: main sitemap/api sitemap around 224 URLs, news sitemap around 34 URLs, robots advertises both. Assume mobile article reading flow is live via commit 48611c9: mobile shows image, one starter paragraph, Read more, ad lower down, source hidden until expanded, and irrelevant generic guide fallback removed from simple local articles. Next priorities: verify actual newsletter subscriber/unsubscribe data before changing email strategy, monitor Search Console after sitemap cleanup, verify the next scheduled article generation run before touching scheduler locks, and only then continue controlled monetisation/newsletter/SEO improvements.
```

---

## May 18, 2026 — final documentation consolidation note: single chat-source master file only

This note was appended after the user clarified again that all Cheshire Today work from this chat must remain in one single chat-source project-state master file rather than being split into separate update documents.

### A. Single-file documentation rule reaffirmed
The active operating rule is now:

```text
For Cheshire Today project-state updates, append the full detailed session record to this single chat-source master file.
Do not create separate update-only files unless the user explicitly asks for a separate export.
Do not ask the user to run terminal find commands in the repo to locate a root .md file when they ask to update the current state file.
Treat “update the current state md file” as “update the chat-source master file” by default.
```

### B. Confirmation of what was already consolidated into this file from the May 18 chat
The May 18 continuation above already records the detailed work from this chat, including:

```text
1. Sitemap quality audit and cleanup
   - main sitemap filtering in backend/server.py
   - news sitemap filtering in backend/server.py
   - second filler-exclusion pass
   - final sitemap counts: main/api sitemap 224 URLs, news sitemap 34 URLs
   - robots.txt sitemap declarations verified

2. Search Console / indexing guidance
   - do not manually remove not-indexed pages one by one
   - submit cleaner sitemap and monitor Search Console after 3–7 days
   - keep bad URLs out of future sitemap submissions rather than chasing each old URL manually

3. Missed 6pm article-generation review
   - manual trigger was tested
   - scheduler lock message observed: another server handling article generation
   - decision: leave scheduler locks alone for now and wait for the next automatic run before changing lock logic

4. Render log interpretation
   - normal article/API/asset requests explained
   - Meta/Facebook crawler traffic explained
   - 301 article URL redirects explained as expected legacy ID-only route to canonical slug route
   - HEAD /api/health 404 identified as non-critical cleanup task
   - sponsored-placement impression inflation by bots/crawlers noted as later analytics cleanup

5. GA4 / newsletter page-view interpretation
   - /unsubscribe and /newsletter/preferences views should not automatically be treated as real churn
   - actual subscriber records must be checked before newsletter strategy changes
   - backlog added to review active, unsubscribed, recent-unsubscribed and latest-Daily-Brief unsubscribe counts

6. Mobile article-page improvement workflow
   - current ArticlePageV2.jsx inspected first
   - duplicate mobile Continue reading button removed
   - desktop-only standfirst cleanup added with word-boundary clipping
   - multiple mobile UX iterations tested locally on port 3000
   - Why this matters box tested and rejected for this flow because it felt repetitive
   - final mobile flow selected: image, one starter paragraph, Read more, advert lower down, full article/source only after expansion
   - source hidden until full mobile article is expanded
   - irrelevant generic guide fallback removed
   - whole Best options block hidden unless there is a genuine monetised guide match

7. Build, commit, push, deploy and verification details
   - frontend production builds passed at each stage
   - local static server testing used instead of npm start
   - key commits recorded: c73b68e, 634043f, 29ddb09, 20819f2, 48611c9
   - final live frontend bundle verified: main.4a064ee4.js
   - live bundle confirmed Read more exists and old Continue reading full article wording was removed
```

### C. Current continuation instruction from this point
When continuing Cheshire Today work from a future chat, use this file as the one source of truth and continue appending to it. The current next practical priorities remain:

```text
1. Verify real newsletter subscriber/unsubscribe data before changing newsletter strategy.
2. Monitor Search Console after the sitemap cleanup settles.
3. Verify the next scheduled article-generation run before touching scheduler locks.
4. Later add HEAD /api/health support.
5. Later consider bot/crawler filtering for sponsored-placement impression analytics.
6. Continue mobile/article/monetisation refinements only after checking current live state first.
```



---

## May 20, 2026 — Full Cheshire Today QA, newsletter verification, Search Console review, sitemap cleanup, and public feed quality tightening

This section records the full May 20 QA continuation. The user explicitly asked to continue from the single chat-source project state file and to preserve the existing workflow: check current state first, one command at a time, no manual file edits unless absolutely necessary, use `grep` rather than `rg`, verify after each change, and do not run a full scrape unless necessary for import/scrape testing.

### A. Operating instruction reaffirmed for this session

The working rules remained:

```text
- Act as Boren, the practical Cheshire Today consultant.
- Use the single chat-source master file as the project source of truth.
- Check current state before recommending or changing anything.
- Use one command at a time.
- Avoid manual file edits; use safe terminal/script changes only.
- Use grep, not rg.
- Verify after every change.
- Do not use npm start unless explicitly requested.
- Do not run full scrape unless necessary for import/scrape testing.
- Preserve the strategy: Cheshire local + business/finance + AI/tech authority platform.
- Preserve the 40% Local / 40% Business+Finance / 20% AI-Tech target.
- Keep affiliate-first monetisation, Facebook traffic, newsletter growth, SEO/indexing, sponsor readiness, and clean reader experience central.
- Avoid crime-heavy filler, weak generic national filler, exaggerated headlines, and intrusive ads.
```

### B. QA request scope

The user requested a full QA review covering:

```text
1. Homepage layout and visual professionalism
2. Mobile reading experience
3. Article page experience
4. Content quality and category balance
5. Whether the site feels local, useful, and trustworthy
6. Facebook traffic suitability: headlines, article choice, click-through potential
7. Newsletter signup visibility and user journey
8. Affiliate guide visibility and monetisation opportunities
9. Sponsor/advertiser readiness
10. SEO basics, sitemap/indexing signals, internal linking, metadata
11. Site speed/performance from a user perspective
12. Trust/legal/UX issues
13. What could reduce bounce rate
14. What could increase page views per visitor
15. What could help revenue over the next 30–90 days
```

The work below focused first on the highest-risk measurable areas: newsletter data, sitemap/indexing signals, public feed quality, and Search Console status. Wider revenue/UX improvements were deferred until after the technical SEO/feed cleanup was safely closed.

### C. Newsletter code and database health verification

The backend newsletter-related code was inspected first with `grep` and `sed` before any strategy decisions were made.

Key code findings:

```text
- `/newsletter/subscribe` exists and supports reactivating previously soft-unsubscribed users.
- New subscribers are created with `active: True`, `daily_brief: True`, `weekly_roundup: False`, and `breaking_news: False`.
- `/newsletter/unsubscribe` performs a soft unsubscribe rather than deleting the record:
  - active set to False
  - daily_brief / weekly_roundup / breaking_news set to False
  - unsubscribed_at and unsubscribe_method recorded
  - unsubscribe_log audit record created
- `/admin/subscribers` returns subscriber records for the admin dashboard.
- Daily Brief sending uses active subscribers only and respects `daily_brief != False`.
- Daily Brief sending uses `DAILY_BRIEF_SEND_CAP`, default 2000.
- Batch rotation is implemented via `email_batch_cursors` using `_select_rotating_email_batch()` and `_save_email_batch_cursor()`.
- Scheduler duplicate protection uses `digest_log` with status/lock logic and stale lock reclaiming.
```

Actual subscriber/database snapshot provided during the session:

```json
{
  "subscribers_total_records": 14265,
  "subscribers_active_true": 14234,
  "subscribers_active_missing_legacy": 0,
  "subscribers_soft_unsubscribed": 31,
  "subscribers_unsubscribed_last_7_days": 29,
  "daily_brief_eligible_before_send_cap": 14234,
  "unsubscribe_log_total": 31,
  "unsubscribe_log_last_7_days": 29,
  "latest_digest_logs": [
    {
      "sent_at": "2026-05-19 06:30:00.001000",
      "type": "DailyBrief",
      "date_key": "20260519",
      "status": "sent",
      "subscribers_count": 2000,
      "success_count": 2000,
      "error": null
    },
    {
      "sent_at": "2026-05-18 06:30:00.001000",
      "type": "DailyBrief",
      "date_key": "20260518",
      "status": "sent",
      "subscribers_count": 2000,
      "success_count": 2000,
      "error": null
    },
    {
      "sent_at": "2026-05-17 08:00:37.614000",
      "type": "WeeklyRoundup",
      "date_key": "20260517",
      "status": null,
      "subscribers_count": 2000,
      "success_count": 2000,
      "error": null
    },
    {
      "sent_at": "2026-05-16 06:30:00.001000",
      "type": "DailyBrief",
      "date_key": "20260516",
      "status": "sent",
      "subscribers_count": 2000,
      "success_count": 2000,
      "error": null
    },
    {
      "sent_at": "2026-05-15 06:30:00.001000",
      "type": "DailyBrief",
      "date_key": "20260515",
      "status": "sent",
      "subscribers_count": 2000,
      "success_count": 2000,
      "error": null
    }
  ]
}
```

Batch cursor state verified:

```json
[
  {
    "digest_key": "DailyBrief",
    "last_batch_size": 2000,
    "last_start_index": 9737,
    "next_index": 11737,
    "total_eligible": 14241,
    "updated_at": "2026-05-19 06:30:26.674000"
  },
  {
    "digest_key": "WeeklyRoundup",
    "last_batch_size": 2000,
    "last_start_index": 2000,
    "next_index": 4000,
    "total_eligible": 14251,
    "updated_at": "2026-05-17 08:00:38.062000"
  }
]
```

Newsletter QA conclusion:

```text
- Newsletter system is not in panic state.
- Subscriber base is large and mostly active.
- Soft-unsubscribe audit trail exists.
- Daily Brief is sending successfully in capped batches.
- Batch rotation is working.
- Do not suppress cold subscribers or change newsletter strategy until more real engagement/unsubscribe evidence is gathered.
```

### D. Initial sitemap / robots verification before changes

Live robots and sitemap counts were checked before any SEO code changes.

Observed live state before later cleanup:

```text
robots.txt:
Disallow: /unsubscribe
Disallow: /newsletter/preferences
Sitemap: https://cheshiretoday.co.uk/sitemap.xml
Sitemap: https://cheshiretoday.co.uk/news-sitemap.xml

Initial live main sitemap URL count: 221
Initial live news sitemap URL count: 58
```

Search Console initially showed old counts:

```text
https://cheshiretoday.co.uk/sitemap.xml
Status: Success
Last read: 18 May 2026
Discovered URLs: 224

https://cheshiretoday.co.uk/news-sitemap.xml
Status: Success
Last read: 19 May 2026
Discovered URLs: 58
```

### E. News sitemap audit and tightening

The live news sitemap was inspected and was found to include too much off-strategy material, including:

```text
- personal tragedy / diagnosis stories
- drugs/crime stories
- random global tech and international filler
- weak politics/opinion items
- animal/lifestyle/filler items
- weak/non-useful business stories
```

Examples seen in the news sitemap before tightening included:

```text
Cheshire dad given devastating diagnosis after back started to ache
Creamfields festivalgoer hid 18 packets of cocaine inside 'insect zapper'
X limits hot takes from freeloaders to 50 a day
Airbus gets HPC-as-a-service supercomputer from Bull
ZTE Showcases AI Interactive Flat Panel at the Broadband User Congress in Brazil
UK Typhoon jets fitted with bargain-bin drone busters for Middle East sorties
Swinney defends food prices policy ahead of first minister vote
Animal park welcomes four Sumatran tiger cubs
MAGA's Mace wants to make power bills great again...
Starbucks Korea sacks CEO...
Swatch stores / Swatch boss stories
```

The news sitemap generator in `backend/server.py` was inspected around `generate_news_sitemap()` and then patched only in the news sitemap filter. It was tightened around the Cheshire Today positioning:

```text
- Cheshire local
- business/finance/economic impact
- practical AI/tech
- avoid crime/courts/accidents/emergency filler
- avoid personal tragedy / human-interest filler
- avoid celebrity/political/lifestyle/entertainment filler
- avoid weak/global tech filler not useful for Cheshire readers
```

A local simulation showed:

```text
RECENT_ARTICLES_FOUND = 73
FINAL_FILTER_INCLUDED = 35
```

Representative included items after the final news sitemap filter:

```text
- Apartments plan with café recommended for approval
- Leighton Hospital hit by 'water supply issue' as patients face disruption
- Shai-Hulud keeps burrowing: 314 npm packages infected...
- SAP customers warned AI agents could put costs on autopilot
- At least 15m Britons not saving enough to retire...
- Energy bills will rise by £209 a year...
- UK unemployment rate unexpectedly rises
- Standard Chartered to cut thousands of roles as AI use increases
- Google tells database devs to lean hard on AI for PostgreSQL work
- Surprise AI bills leave AWS and Google Cloud users aghast
```

Representative excluded items after the filter:

```text
- Cheshire dad given devastating diagnosis...
- Two in hospital after horror M56 crash...
- Broadcom finds a VMware customer willing to stick around...
- X limits hot takes from freeloaders...
- Airbus gets HPC-as-a-service...
- St Brelade concerns...
- Swatch boss...
- Creamfields cocaine story
- ZTE Brazil story
- UK Typhoon jets...
- New High Street crime unit...
- Elon Musk has lost yet another legal battle...
- Animal park / tiger cubs
- Starbucks Korea
- period drama / Pokemon / Alton Towers / fire / crash filler
```

Verification before commit:

```text
python3 -m py_compile backend/server.py → silent
/usr/bin/git diff --check → silent
```

Commit and push:

```text
10e0741 Tighten Google News sitemap quality filters
Pushed to origin/full-scrape-prod
```

After manual Render backend deployment, live news sitemap count was verified at approximately the expected range and later reported as 35 before additional freshness changed it to 39.

### F. Main sitemap audit and tightening

Main sitemap output was inspected and still contained weak/off-strategy article URLs. `generate_sitemap()` in `backend/server.py` was inspected. It already included:

```text
- homepage
- location pages
- category pages
- published/live authority guide pages
- filtered strategic articles with images
```

The main sitemap article filter was then tightened to align with the same strategic principles used in the news sitemap.

Simulation before commit showed:

```text
ARTICLE_CANDIDATES_CHECKED = 197
GUIDES_PUBLISHED_OR_LIVE = 35
STRATEGIC_ARTICLES_INCLUDED = 108
ESTIMATED_MAIN_SITEMAP_URLS = 156
```

This was considered a sensible reduction:

```text
Old live main sitemap: 221 URLs
Estimated cleaned main sitemap: about 156 URLs
```

The patch was committed and pushed:

```text
56d0098 Tighten main sitemap article quality filters
Pushed to origin/full-scrape-prod
```

After manual backend deployment, live verification showed:

```text
Main sitemap: 156 URLs
News sitemap: 35 URLs
```

A weak-term check across both live sitemaps returned silent output for known weak/off-strategy terms including cocaine, Swinney, X limits, Airbus HPC, ZTE, animal park, Starbucks Korea, Elon Musk legal battle, High Street crime unit, devastating diagnosis, and tiger cubs.

### G. Active article pool and public API/feed QA

A read-only database check showed the active pool was not balanced enough:

```text
ACTIVE_ARTICLES = 197

CATEGORY_COUNTS:
Tech: 78
Business: 53
Local News: 39
Finance: 23
Tax: 4

SCOPE_COUNTS:
uk: 158
cheshire: 39
```

Grouped against the 40/40/20 strategy:

```text
Local: 19.8%
Business + Finance + Tax: 40.6%
AI/Tech: 39.6%
```

QA verdict on the active pool:

```text
- Tech was roughly double target.
- Local was roughly half target.
- Active database pool still contained weak material.
- Do not archive manually yet; inspect public/homepage API first.
```

The public API was then checked:

```text
PUBLIC_API_ARTICLES = 83

CATEGORY_COUNTS:
Local News: 32
Tech: 21
Business: 19
Finance: 8
UK News: 3
```

Public API mix was better than the active pool but still had weak visible items, including:

```text
Airbus gets HPC-as-a-service supercomputer from Bull
Cheshire dad given devastating diagnosis...
Creamfields cocaine story
Woman deliberately knocked off her bike...
St Brelade concerns...
Swatch boss...
X limits hot takes...
M6 updates as smash...
Live updates as emergency services...
Pokemon Mega Evolution Trails...
UK Typhoon jets...
ZTE Brazil...
Animal park / tiger cubs
Swinney / first minister vote
```

The `/api/articles` endpoint was inspected around `get_articles()` in `backend/server.py`. Existing logic already included:

```text
- archive exclusion
- homepage cache
- local/UK interleaving
- UK noise filter
- editorial noise filter
- hard crime exclusion
- incident/crime caps
- fallback filtering
- force_live bypass
- soft authority boost
```

### H. Public feed quality filter tightening

A narrow public feed quality filter was added inside `is_editorial_noise()` so that only the public homepage/API feed selection was affected. This did not touch:

```text
- article pages
- old URLs
- admin
- imports
- scheduler
- newsletter
- archives
- sitemaps already fixed separately
```

Initial simulation showed the patch would filter 22 weak items but also caught a useful oil/energy story. The filter was refined to avoid blocking valid oil/energy impact stories such as:

```text
Oil prices rise after Trump warns Iran over stalled peace talks
```

After refinement, simulation showed:

```text
TOTAL_WOULD_FILTER = 21
```

Key items caught by the patch:

```text
Airbus HPC
Cheshire dad devastating diagnosis
Creamfields cocaine
St Brelade
Swatch
period drama/free to watch
X freeloaders
Pokemon
Alton Towers
ZTE Brazil
Animal park/tiger cubs
Swinney
Elon Musk has lost legal battle
High Street crime unit
Starbucks Korea
VMware quietly debuts
MAGA/Mace datacenter moratorium
```

Verification:

```text
python3 -m py_compile backend/server.py → silent
/usr/bin/git diff --check → silent
```

Commit and push:

```text
7eb1269 Tighten public article feed quality filter
Pushed to origin/full-scrape-prod
```

After backend deployment, public API was cleaner but still had traffic/incident filler.

### I. Additional public feed traffic/incident filler filter

A second narrow public feed patch was added for obvious traffic/incident filler terms:

```text
hit-and-run
knocked off
smash between
train station crash
emergency services respond
```

Simulation showed it would remove only 3 current public feed items:

```text
Woman 'deliberately knocked off her bike' in Winsford hit-and-run
M6 updates as smash between 'car and truck'
Live updates as emergency services respond to Cheshire train station crash
```

Verification:

```text
python3 -m py_compile backend/server.py → silent
/usr/bin/git diff --check → silent
```

Commit and push:

```text
72f6ef4 Filter public feed traffic incident filler
Pushed to origin/full-scrape-prod
```

After Render deployment, public API verification showed those 3 incident filler items were gone.

Public API after this stage:

```text
PUBLIC_API_ARTICLES = 83

CATEGORY_COUNTS:
Tech: 26
Local News: 24
Business: 18
Finance: 12
UK News: 3
```

Grouped roughly:

```text
Local / UK local: 27 = 32.5%
Business + Finance: 30 = 36.1%
Tech: 26 = 31.3%
```

QA verdict:

```text
- Feed became cleaner.
- Worst filler removed.
- Still slightly Tech-heavy.
- Do not keep tightening aggressively in the same phase, to avoid over-filtering useful local variety.
```

### J. Search Console resubmission and updated sitemap counts

After the sitemap cleanup, the user checked Google Search Console. It initially still showed older counts:

```text
Main sitemap: 224 discovered URLs
News sitemap: 58 discovered URLs
```

The user resubmitted/checked the sitemaps, and Search Console screenshots confirmed Google re-read the cleaned versions on 20/05/2026:

```text
Main sitemap discovered pages: 157
News sitemap discovered pages: 39
Status: Sitemap processed successfully
Last read: 20/05/2026
```

This was considered successful because live counts at that point were approximately:

```text
Main sitemap: 156
News sitemap: 35–39 depending on current 48-hour news window
```

### K. Page indexing report analysis

The user then checked Search Console Page Indexing.

Important note:

```text
Page indexing report last update: 15/05/2026
```

This was before the May 20 sitemap/feed cleanup, so the Page Indexing report was treated as historic/lagging data.

Approximate Page Indexing status shown:

```text
Not indexed: 3.6k
Indexed: 2
```

Reasons shown:

```text
Crawled - currently not indexed: 1,570
Not found (404): 450
Excluded by noindex tag: 40
Page with redirect: 34
Soft 404: 1
Duplicate, Google chose different canonical: 20
Alternative page with proper canonical tag: 919
Duplicate without user-selected canonical: 0
Discovered - currently not indexed: 562
```

Interpretation:

```text
- The sitemaps are healthy.
- The Page Indexing report has not caught up with the cleanup yet.
- Many old URLs are likely old weak RSS/import/history URLs.
- Do not manually remove old URLs one by one.
- Need to inspect samples before deciding whether any current important pages are affected.
```

### L. Crawled - currently not indexed sample analysis

The user opened examples under `Crawled - currently not indexed`.

Example URLs included:

```text
https://cheshiretoday.co.uk/article/13a10fea-3eac-4e5f-b87d-e63642bd941e/discussion-over-the-future-of-sark-launched
https://cheshiretoday.co.uk/article/69bb1ffb4ca75e6e8dd0f0df/council-confirms-school-crossing-patrols-scrapped-as-part-of-budget-cuts
https://cheshiretoday.co.uk/article/6a04b3a66903ac2ecb7d897b/10-pictures-from-westminster-park-s-80th-anniversary-celebrations
https://cheshiretoday.co.uk/article/fbb9e7a1-82ad-4871-9551-3ba2f1405bb4/nigel-farage-stops-accepting-cameo-requests-after-revelations-about-his-use-of-p
https://cheshiretoday.co.uk/article/140c83fe-8864-44c0-b609-fa681720d7bd/weekly-sports-quiz-who-is-youngest-top-flight-scorer
https://cheshiretoday.co.uk/article/69bb20c64ca75e6e8dd0f0ea/uk-says-it-remains-in-talks-over-escorting-ships-through-strait-of-hormuz
https://cheshiretoday.co.uk/article/ed35d07c-48e2-41e0-bea0-61b8aee36b21/redundancy-consultations-for-small-number-at-sykes-cottages-confirmed
https://cheshiretoday.co.uk/article/69bd8ee7cf5c97d942b248fb/eid-moon-spotters-pass-skills-to-next-generation
https://cheshiretoday.co.uk/article/da6c18f8-d1ca-4aaf-84bb-186b0fc8d949/john-fury-relationship-with-tyson-completely-destroyed
https://cheshiretoday.co.uk/article/ce416632-7f39-4e2d-9e66-32df8d331258/starmer-plans-to-ease-impact-of-immigration-policy-changes-after-backlash-from-l
```

Analysis:

```text
- Most examples were old weak/off-strategy URLs.
- They matched the type of content the sitemap/public feed cleanup was designed to stop promoting.
- One sample remained in the live sitemap: `10-pictures-from-westminster-park-s-80th-anniversary-celebrations`.
```

A live grep confirmed only that one sample from the list was still being promoted:

```text
<loc>https://cheshiretoday.co.uk/article/6a04b3a66903ac2ecb7d897b/10-pictures-from-westminster-park-s-80th-anniversary-celebrations</loc>
```

### M. Gallery/photo filler cleanup

A follow-up check looked for gallery/photo terms across the live sitemap, news sitemap, and public API.

The corrected quoted URL command found:

```text
https://cheshiretoday.co.uk/article/6a07fd7f207fa2edd0cf7bfd/art-deco-and-modernist-flats-in-england-and-scotland-for-sale-in-pictures
Art deco and modernist flats in England and Scotland for sale – in pictures

https://cheshiretoday.co.uk/article/6a04b3a66903ac2ecb7d897b/10-pictures-from-westminster-park-s-80th-anniversary-celebrations
10 pictures from Westminster Park's 80th anniversary celebrations
```

The public API also showed gallery-source URLs such as:

```text
/gallery/unique-cheshire-four-bed-cricket...
/gallery/more-images-proposed-new-ellesmere...
/gallery/inside-cheshires-newest-mcdonalds...
/gallery/10-pictures-westminster...
```

A controlled patch added gallery/photo-list exclusions in the relevant locations:

```text
Public feed:
- `/gallery/` URL guard
- `in pictures`
- `pictures from`
- `anniversary celebrations`

Main sitemap:
- `in pictures`
- `pictures from`
- `anniversary celebrations`

News sitemap:
- `in pictures`
- `pictures from`
- `anniversary celebrations`
```

A duplicate insertion in the main sitemap filter was detected during diff review and removed before commit.

Verification that all intended locations were covered:

```text
3456: if "/gallery/" in url:
3477: r"in pictures|pictures from|anniversary celebrations|"
10586: r"\bin pictures\b",
10587: r"\bpictures from\b",
10588: r"\banniversary celebrations\b",
10861: r"\bin pictures\b",
10862: r"\bpictures from\b",
10863: r"\banniversary celebrations\b",
```

Simulation showed the gallery/photo filter would exclude 5 items:

```text
PHOTO_GALLERY_MATCHES_THAT_FILTER_WOULD_EXCLUDE = 5

- [Local News] The 'unique' Cheshire four-bed with a cricket ground at the bottom of the garden
- [Local News] Plans Lodged for New Ellesmere Port Catholic High School
- [Finance] Art deco and modernist flats in England and Scotland for sale – in pictures
- [Local News] Inside Cheshire's newest McDonald's restaurant as it opens its doors
- [Local News] 10 pictures from Westminster Park's 80th anniversary celebrations
```

QA judgement:

```text
- Excluding these from public feed and sitemaps is acceptable.
- Articles remain accessible by direct URL.
- These are gallery/photo-list format rather than strong authority/news pages.
- Removing them from sitemap/public feed signals helps focus Google and reader-facing output.
```

Verification:

```text
python3 -m py_compile backend/server.py → silent
/usr/bin/git diff --check → silent
```

Commit and push:

```text
3c6d96e Filter gallery photo filler from public feeds and sitemaps
Pushed to origin/full-scrape-prod
```

After backend deployment, live verification command returned silent output for:

```text
in-pictures
in pictures
pictures from
anniversary-celebrations
anniversary celebrations
/gallery/
```

across:

```text
https://cheshiretoday.co.uk/sitemap.xml
https://cheshiretoday.co.uk/news-sitemap.xml
https://cheshiretoday.co.uk/api/articles?limit=80
```

Final live counts after gallery/photo cleanup:

```text
Main sitemap: 155 URLs
News sitemap: 39 URLs
Gallery/photo leak check: silent
Git status: clean
```

### N. Commits completed during this QA/cleanup phase

The key commits from this May 20 QA session were:

```text
10e0741 Tighten Google News sitemap quality filters
56d0098 Tighten main sitemap article quality filters
7eb1269 Tighten public article feed quality filter
72f6ef4 Filter public feed traffic incident filler
3c6d96e Filter gallery photo filler from public feeds and sitemaps
```

Each commit was pushed to:

```text
origin/full-scrape-prod
```

Manual Render backend deployments were performed after the pushed backend commits. Final deployed live state was verified.

### O. Final verified state at end of May 20 QA session

```text
Git status: clean
Backend deployed: yes
Main sitemap: 155 URLs
News sitemap: 39 URLs
Gallery/photo leak check: silent
Worst public feed filler removed
Newsletter subscriber health checked and stable
Daily Brief batching checked and rotating correctly
Search Console re-read cleaned sitemaps on 20/05/2026
```

Current readiness score after this QA phase:

```text
7.4 / 10
```

Reasons the score improved:

```text
- Sitemaps are now cleaner and more strategic.
- Google Search Console has processed the cleaned sitemap versions.
- Public feed no longer exposes the worst filler at the same level.
- Newsletter system has been verified with real subscriber/send data.
- No import, scheduler, newsletter-send, or full scrape disruption occurred.
- Repo ended clean after verification.
```

Reasons the score is not higher yet:

```text
- Public feed is still slightly Tech-heavy.
- Active database pool remains broader/noisier than ideal.
- Page Indexing report still shows many old non-indexed URLs.
- Search Console indexing data needs time to catch up with new sitemap signals.
- Revenue/guide visibility and sponsor readiness still need a controlled next phase.
```

### P. Recommended next steps after this session

Stop code changes for now and monitor Google/Search Console before applying more filters.

Next checks:

```text
1. Wait 2–5 days for Search Console to process the latest cleaned sitemap/feed signals.
2. Re-check Search Console → Page indexing → Crawled - currently not indexed → Examples.
3. If examples are mostly old weak/off-strategy URLs, do nothing.
4. If examples include important guide pages or strong local/business articles, inspect those specific pages.
5. Check latest public feed after the next scheduled imports to ensure weak filler does not return heavily.
6. Do not run full scrape unless needed for import/scrape testing.
7. Do not change newsletter suppression strategy yet; subscriber/unsubscribe data does not support panic action.
```

Revenue and growth phase to resume after monitoring:

```text
1. Improve guide visibility carefully without intrusive ads.
2. Strengthen article-to-guide internal linking.
3. Review newsletter signup placement and wording.
4. Prepare sponsor/media kit readiness and first campaign reporting flow.
5. Continue Facebook post selection around practical Cheshire/local money/business/AI impact stories.
```

### Q. Continuation prompt for the next Cheshire Today session

Use this when starting the next continuation:

```text
Continue Cheshire Today from the current single chat-source project state file.
Respect workflow: check current state first, one command at a time, no manual file edits unless absolutely necessary, use grep not rg, verify after each change, and do not run full scrape unless necessary for import/scrape testing.

Current verified state after May 20 QA:
- Git clean after live deploy.
- Backend deployed through commit 3c6d96e.
- Main sitemap live count: 155 URLs.
- News sitemap live count: 39 URLs.
- Search Console re-read cleaned sitemaps on 20/05/2026 and showed main sitemap around 157 discovered pages and news sitemap around 39 discovered pages.
- Gallery/photo leak check across sitemap/news sitemap/public API is silent.
- Public feed quality filters now remove worst filler, obvious traffic incidents, and gallery/photo-list pages from homepage/API selection.
- Articles remain accessible by direct URL; archives/imports/newsletter/scheduler were not disrupted.
- Newsletter verified: 14,265 total subscriber records, 14,234 active, 31 soft-unsubscribed, 29 unsubscribed last 7 days, Daily Brief eligible before cap around 14,234, Daily Brief sends capped at 2,000 and rotating via email_batch_cursors.
- Latest key commits: 10e0741, 56d0098, 7eb1269, 72f6ef4, 3c6d96e.

Next priorities:
1. Do not make more SEO/feed code changes immediately.
2. Monitor Search Console after 2–5 days, especially Page indexing → Crawled - currently not indexed → Examples.
3. If examples are old weak/off-strategy URLs, leave them.
4. If examples show important guides or strong local/business articles, inspect those pages individually.
5. Check latest public feed after scheduled imports; do not run full scrape unless required.
6. Then continue controlled monetisation work: guide visibility, article-to-guide links, newsletter signup wording, sponsor/media kit/reporting readiness.
```

---

## 2026-05-24 — Admin Manual Review, Newsletter Stability, Sitemap Hygiene, and Perplexity Verification Upgrade

### Summary
This working session focused on tightening the Cheshire Today operational workflow around four important areas:

1. Admin Manual Review article handling.
2. Daily Brief newsletter stability and tracking noise.
3. Sitemap/indexing hygiene.
4. Perplexity article rewriting, verification, budget control, and Manual Review routing.

The core strategy remains unchanged: Cheshire Today should remain a clean, useful Cheshire local + business/finance + AI/tech authority platform, avoiding crime-heavy filler, weak generic national filler, exaggerated claims, and intrusive reader experience.

---

### 1. Admin Manual Review and article edit/update fixes

#### Problem found
The Admin Dashboard Archive tab was showing archived articles correctly, but the “AI manual review” count was confusing and/or showing zero. The site also needed stronger handling for articles that were okay in principle but did not contain enough factual/local detail to publish safely.

Manual Review articles also needed to be editable and restorable only when genuinely fixed.

#### Work completed
- Confirmed Admin Dashboard Manual Review logic and archive count behaviour.
- Updated Archive description/count wording to avoid implying archived items were the same as live hidden Manual Review articles.
- Added support for Manual Review articles being found by MongoDB `_id` as well as custom article `id` when edited.
- Fixed Admin article update route so Manual Review articles can be edited from the dashboard.
- Updated the edit/update flow so saving a Manual Review article refreshes the Manual Review list.
- Added conditional restore logic:
  - If an edited Manual Review article now passes factual/local checks, it is restored to the public live site.
  - If it still lacks specific factual/local detail, it remains hidden in Manual Review.
  - If it still contains risky AI/invented-detail phrases, it remains hidden in Manual Review.
- Added `priority_location` update alongside `location` on article edits.
- Added Delete button to the Manual Review Articles panel.
- Protected article delete route with admin auth.

#### Commits
- `518a062` — Show manual review articles in admin archive tab
- `25896e0` — Clarify archive manual review count
- `1ed49b8` — Add local article location manual review guard
- `0be0a5f` — Add manual review delete control
- `d426558` — Fix manual review article update restore flow

#### Result
Manual Review articles are now visible, editable, deletable, and safer to restore. Edited articles only leave Manual Review when they pass the location/factual-detail and AI-risk checks.

---

### 2. Local article location/factual-detail guard

#### Problem found
Some Local News articles could have a location field but the article body itself might not clearly contain a specific town, village, road, venue, site, council area, hospital, park, school, or named local place.

This was a risk because articles could appear locally relevant while still being vague or unsupported.

#### Work completed
- Added local location review logic in `backend/server.py`.
- Added a specific local location regex for Cheshire towns/places/sites/routes including, but not limited to:
  - Chester, Crewe, Macclesfield, Warrington, Widnes, Runcorn, Knutsford, Wilmslow, Congleton, Nantwich, Sandbach, Middlewich, Northwich, Winsford, Ellesmere Port, Handforth, Leighton Hospital, Chester Zoo, River Dee, M53, M56, M6, Deva Stadium and other local terms.
- Added vague Cheshire wording detection for phrases like:
  - “Cheshire woman”
  - “Cheshire man”
  - “Cheshire dad”
  - “Cheshire park”
  - “Cheshire village”
  - “part of Cheshire”
- Strengthened the rule so the article text/title/summary itself must contain the specific local detail, not just a database field.
- Existing live articles were audited.
- Location fields were fixed where obvious and safe.
- Weak, vague, or non-strategy articles were moved to Manual Review.

#### Verification snapshots from the session
- Initial live public/manual review audit found candidate articles needing review.
- After fixes:
  - `PUBLIC_LOCAL_NEWS_WITHOUT_LOCATION = 0`
  - `LIVE_PUBLIC_ARTICLES = 176`
  - `LIVE_MANUAL_REVIEW_HIDDEN = 21`
  - Remaining public review candidates were narrowed to a small number of non-local/noise items.

#### Result
Public Local News now requires specific local factual detail in the article text itself. Vague “Cheshire” stories are hidden for Manual Review rather than published publicly.

---

### 3. Daily Brief interruption, memory issue, and recovery

#### Problem found
Render logs showed the Daily Brief started sending at 06:30 UTC / 07:30 UK time and made multiple successful Resend batch API calls. Shortly afterwards, the Render backend restarted.

A screenshot/log confirmed the instance failed due to memory usage over the 512MB limit.

Important log pattern:
- Daily Brief won the send lock.
- 2,000 rotating subscribers were selected.
- Resend accepted 19 batch POST requests.
- Backend restarted before final success/cursor updates were written.

Database state confirmed:
- `digest_log` for `DailyBrief` / `20260522` was stuck at `status = sending`.
- `success_count = 0`.
- Daily Brief cursor had not advanced.

#### Analysis
The main issue was memory pressure during the 2,000-recipient Daily Brief send on the 512MB Render instance. The deploy/restart timing made it visible, but the screenshot confirmed the underlying restart reason was memory.

The scheduler startup logs after restart were normal and not the cause.

#### Repair completed
The Daily Brief send was not manually retriggered to avoid duplicate emails.

Because Resend batch size is 100 and 19 successful batch POSTs were seen, at least 1,900 emails were confirmed accepted by Resend.

The database was repaired safely:
- Daily Brief 20260522 was marked as `sent_interrupted_after_resend_acceptance`.
- `success_count` repaired to `1900`.
- `confirmed_resend_batch_posts` set to `19`.
- Cursor advanced from the stuck previous position to the planned next index `1505` to avoid resending the same batch.

Verified repaired state:
- Digest status: `sent_interrupted_after_resend_acceptance`
- Cursor: `next_index = 1505`
- `last_start_index = 13737`
- `last_batch_size = 2000`
- `total_eligible = 14232`

#### Stability change completed
Render backend environment was updated:

```text
DAILY_BRIEF_SEND_CAP=1000
```

This reduces Daily Brief send workload from 2,000 to 1,000 per scheduled send to reduce memory pressure.

#### Code hardening completed
Added planned Daily Brief cursor details into `digest_log` before sending:

```text
planned_batch_start
planned_batch_next
planned_batch_size
planned_total_eligible
planned_cursor_recorded_at
```

This means if Render restarts mid-send again, recovery is safer and does not require guessing the planned cursor from logs.

#### Commit
- `be30cac` — Record planned Daily Brief cursor before send

#### Operational note
Avoid backend deploys around the Daily Brief send window, approximately:

```text
07:25–07:45 UK time
```

---

### 4. Email tracking HEAD request fix

#### Problem found
Render logs showed email security scanners issuing `HEAD` requests to click-tracking URLs:

```text
HEAD /api/email/track/click/... 404 Not Found
```

These were likely email security/privacy scanners checking newsletter links. They were causing noisy 404 logs and could later affect analytics interpretation.

#### Work completed
Added a `HEAD` route for:

```text
/api/email/track/click/{tracking_id}
```

The new route returns:

```text
204 No Content
```

and does not count as a real click.

#### Verification
Live curl test confirmed:

```text
HTTP/2 204
```

#### Commit
- `6738d47` — Support HEAD requests for email click tracking

#### Result
Email scanner HEAD checks no longer generate 404 noise and are not counted as real clicks.

---

### 5. Sitemap and indexing hygiene

#### Initial checks
Robots and sitemaps were checked:

```text
robots.txt: OK
/sitemap.xml: HTTP 200
/news-sitemap.xml: HTTP 200
```

Initial counts:

```text
MAIN SITEMAP URL COUNT = 156
NEWS SITEMAP URL COUNT = 41
```

A database/sitemap cross-check found:

```text
SITEMAP_ARTICLE_URLS = 108
DB_PUBLIC_LIVE_ARTICLES = 191
HIDDEN_MANUAL_REVIEW_IN_SITEMAP = 1
```

The hidden Manual Review article incorrectly present in the sitemap was:

```text
job-cuts-announced-at-cheshire-primary-school
```

#### Work completed
- Updated `/sitemap.xml` to exclude `manual_review_hidden_from_public = True`.
- Updated `/news-sitemap.xml` to exclude `manual_review_hidden_from_public = True`.
- Confirmed both sitemaps now exclude hidden Manual Review articles.

#### Commit
- `22914d1` — Exclude manual review articles from sitemaps

#### Verification after deploy
```text
MAIN_SITEMAP_TOTAL_URLS = 155
MAIN_SITEMAP_ARTICLE_URLS = 107
NEWS_SITEMAP_TOTAL_URLS = 40
NEWS_SITEMAP_ARTICLE_URLS = 40
HIDDEN_MANUAL_REVIEW_IN_MAIN_SITEMAP = 0
HIDDEN_MANUAL_REVIEW_IN_NEWS_SITEMAP = 0
```

#### Sitemap topic quality tightening
A news sitemap audit found weak/generic or non-strategy topics still appearing, such as:

- generic fans/heat/weather filler
- traffic queue/weather filler
- Musk/SpaceX/Grok personality filler
- Trump/Dems US politics filler
- Capri pants/bank holiday lifestyle filler
- glow-worms/slime moulds/Scotland nature filler
- generic bathing site filler
- Flipper One gadget filler

Additional weak-topic exclusions were added to both main and news sitemap filters.

#### Commit
- `63a9fb0` — Tighten sitemap topic quality filters

#### Verification after deploy
```text
MAIN_SITEMAP_TOTAL_URLS = 144
MAIN_SITEMAP_ARTICLE_URLS = 96
NEWS_SITEMAP_TOTAL_URLS = 30
NEWS_SITEMAP_ARTICLE_URLS = 30
```

Final combined hidden-review check:

```text
TOTAL_SITEMAP_URLS_CHECKED = 174
TOTAL_ARTICLE_URLS_CHECKED = 126
HIDDEN_MANUAL_REVIEW_URLS_IN_SITEMAPS = 0
```

#### Result
Sitemaps are now cleaner, tighter, and aligned with Cheshire Today strategy. Hidden Manual Review articles are excluded, and weak/generic topics are less likely to be submitted to Google.

#### Search Console recommendation
Resubmit:

```text
https://cheshiretoday.co.uk/sitemap.xml
https://cheshiretoday.co.uk/news-sitemap.xml
```

Then check Search Console again in 3–7 days, especially “Crawled – currently not indexed”.

---

### 6. Perplexity rewrite prompt and Manual Review workflow

#### User requirement
Perplexity should not simply rewrite articles loosely. It must be given detailed instructions to:

- verify true facts online;
- avoid invented details;
- check source/supporting sources;
- require exact local location for Cheshire stories;
- send unclear or unsupported stories into Admin Manual Review;
- handle property/planning/housing stories carefully so they are included when useful but not over-prioritised.

#### Existing issue found
The existing Perplexity prompt was careful but still returned short uncertain responses or fell back to expanded summaries. Logs showed repeated pattern:

```text
Content below target
Retrying with stronger long-form prompt
Retry still below acceptable quality
Using expanded summary fallback
Skipping short-content local article
```

This meant weak/unclear stories were often skipped completely instead of being saved for manual edit.

#### Prompt upgrade completed
`backend/app/perplexity_service.py` was updated with a strict verification and rewrite prompt for Cheshire Today.

New prompt rules include:

- Do not invent facts, quotes, names, dates, figures, locations, job numbers, planning status, business claims, causes or reactions.
- Use Source URL as primary reference.
- Check reliable online sources before rewriting.
- Prefer council planning portals, council statements, official company pages, press releases, Companies House, government pages, ONS, Bank of England, HMRC, established news sources, or original source.
- If key facts are unclear, unsupported, unavailable, too thin, too generic, or unsuitable, return:

```text
MANUAL_REVIEW_REQUIRED: short reason
```

- Local News must include a specific town, village, road, venue, school, hospital, park, development site, business name, council area, or named local place.
- Vague local wording such as “a Cheshire woman”, “a Cheshire park”, “a Cheshire village” must trigger Manual Review unless the exact place is verified.
- Property/planning/housing stories are allowed but must not dominate or be over-prioritised.
- Planning/housing stories require clear Cheshire relevance and public/economic impact.
- Routine, minor, vague or unsupported housing/planning applications should go to Manual Review.

#### Marker preservation completed
The Perplexity service now preserves:

```text
MANUAL_REVIEW_REQUIRED: reason
```

instead of treating it as a short failed rewrite.

#### Import flow wiring completed
`backend/server.py` was updated so the import flow recognises the marker and saves the article as hidden Manual Review:

```text
verification_status = needs_manual_review
rewrite_status = ai_rewrite_needs_review
manual_review_hidden_from_public = True
manual_review_reason = Perplexity verification requested manual review: ...
```

#### Commit
- `7fcb02d` — Strengthen Perplexity rewrite verification flow

---

### 7. Short Perplexity rewrites now go to Manual Review

#### Problem found in logs
After the stricter Perplexity prompt, the service was correctly producing short uncertain responses when it could not verify enough facts. However, the retry fallback still created an expanded summary and the backend skipped it for being too short.

This meant articles were not published, but they were also not saved for manual review.

#### Fix completed
Changed the short retry fallback in `backend/app/perplexity_service.py` from:

```text
Using expanded summary fallback
```

to:

```text
MANUAL_REVIEW_REQUIRED: Perplexity could not verify enough factual detail to produce a safe publish-ready article.
```

#### Commit
- `e45b9c3` — Send short Perplexity rewrites to manual review

#### Verification test
A small import test was triggered:

```json
{
  "cheshire_articles": 1,
  "uk_articles": 0,
  "business_articles": 0,
  "tech_articles": 0,
  "max_sports": 0,
  "use_perplexity": true,
  "rewrite_delay_seconds": 0
}
```

Logs showed:

```text
Retry still below acceptable quality... Sending to manual review.
Perplexity manual-review article hidden: Why council-owned land is being turned into a thriving Cheshire wildlife haven
```

Database verification showed the article was saved in Manual Review:

```text
Why council-owned land is being turned into a thriving Cheshire wildlife haven
Perplexity verification requested manual review: Perplexity could not verify enough factual detail to produce a safe publish-ready article.
```

#### Result
Unclear/unsupported Perplexity rewrites now go into Admin Manual Review instead of disappearing as skipped imports.

---

### 8. Perplexity budget hard cap

#### Problem found
Logs showed runaway Perplexity spending risk:

```text
Perplexity spend guard: projected £10.60 exceeds daily budget £0.70. Proceeding (soft cap).
```

The code had a soft warning cap and a hard cap option controlled by environment variable:

```text
PERPLEXITY_HARD_CAP
```

#### Decision
For now, keep the daily budget at:

```text
PERPLEXITY_DAILY_BUDGET_GBP=0.70
```

Enable hard cap:

```text
PERPLEXITY_HARD_CAP=1
```

This means roughly 14 estimated calls/day at the current internal estimate of £0.05/call. The number is only an estimate because real Perplexity API cost can vary depending on retrieval and token usage.

#### Result
The backend is now configured so once the daily estimated Perplexity spend reaches the budget, further Perplexity calls should stop rather than continue.

#### Monitoring target
Future logs should show:

```text
Perplexity budget guard: skipping generate_article_content() call
```

They should not show:

```text
Proceeding (soft cap)
```

---

### 9. Hybrid import response now splits public vs Manual Review counts

#### Problem found
When an import saved a hidden Manual Review article, the API response still counted it as a normal imported article:

```json
"total_imported": 1
```

This was technically true but operationally confusing.

#### Work completed
Updated `import_hybrid_news()` response to include:

```text
public_imported
manual_review_imported
```

#### Commit
- `a2bcb74` — Split hybrid import public and manual review counts

#### Verification test
After deployment, the same small import test returned:

```json
{
  "success": true,
  "total_imported": 1,
  "public_imported": 0,
  "manual_review_imported": 1,
  "cheshire_articles": 1,
  "cheshire_from_perplexity": 0,
  "cheshire_from_rss": 1,
  "uk_articles": 0,
  "business_articles": 0,
  "tech_articles": 0,
  "rss_images_used": 1,
  "smart_images_used": 0,
  "estimated_cost_usd": 0.005,
  "sources": {
    "perplexity": false,
    "rss": true
  }
}
```

#### Result
Import results now clearly distinguish between public articles and hidden Manual Review articles.

---

### 10. Current confirmed state after this session

#### Admin / Manual Review
```text
Manual Review articles visible: yes
Manual Review edit/update: fixed
Manual Review restore: conditional on passing checks
Manual Review delete button: added
Delete route: admin-auth protected
Hidden Manual Review excluded from public feeds/sitemaps/newsletter by existing filters and new sitemap fixes
```

#### Newsletter / Daily Brief
```text
Daily Brief 20260522 interrupted by Render memory restart: repaired
Confirmed Resend accepted batches: 19
Confirmed repaired accepted count: 1900
Cursor advanced to avoid duplicate send: yes
DAILY_BRIEF_SEND_CAP: 1000
Planned cursor details recorded before future sends: yes
Email click HEAD tracking: fixed with 204 response
```

#### Sitemap / SEO
```text
Main sitemap: live and 200
News sitemap: live and 200
Hidden Manual Review in sitemaps: 0
Weak/generic sitemap topics reduced
Final combined check: 174 sitemap URLs checked, 126 article URLs, 0 hidden Manual Review URLs
```

#### Perplexity / Import
```text
Strict verification prompt: deployed
Manual Review marker: MANUAL_REVIEW_REQUIRED
Marker preservation: deployed
Short/uncertain retry fallback now goes to Manual Review
Import response split: public_imported / manual_review_imported
Perplexity hard cap: enabled via Render env
Daily budget: £0.70 for now
```

---

### 11. Follow-up backlog from this session

1. Add `HEAD /api/health` support to remove probe 404 noise.
2. Monitor the next scheduled import run and confirm:
   - Perplexity hard cap stops calls after daily budget.
   - Manual Review articles appear in Admin panel.
   - Strong verified articles still publish.
3. Monitor tomorrow’s Daily Brief and confirm:
   - `Found 1000 rotating Daily Brief subscribers`
   - `Daily Brief batch cursor advanced`
   - no Render memory restart.
4. Consider improving import counters further so `cheshire_articles` separately reports public Cheshire vs Manual Review Cheshire.
5. Consider reducing how many weak local RSS candidates are sent to Perplexity before the API call, to save cost.
6. Consider adding per-100-email progress persistence for Daily Brief sends, not just planned cursor details.
7. Resubmit main/news sitemaps in Search Console and recheck indexing in 3–7 days.
8. Continue to avoid backend deploys around the Daily Brief window: 07:25–07:45 UK time.
9. Continue not using `npm start`; use build/static serve workflow when frontend testing is needed.
10. Continue updating this single chat-source state file only unless explicitly asked to update a repo/root file.

---

### 12. Important command/workflow reminders

```text
- Check current state first.
- One command at a time.
- No manual file edits unless absolutely necessary.
- Prefer safe terminal/script changes.
- Use grep, not rg.
- Do not use npm start unless explicitly requested.
- Verify after each change.
- Render auto-deploy remains disabled; deploy manually when needed.
- Backend-only changes require backend Render deploy only.
- Frontend/admin UI changes require frontend/static Render deploy too.
```

---

## 2026-05-25 Major QA / Import Rollback / Perplexity Fallback Fix Update

### 1. Reason for this update

During 2026-05-25 testing, article import behaviour became unstable after several Sunday/Monday experiments around short rewrites, RSS fallbacks, duplicate guards, and Gemini verification. The user clarified that the desired target state is:

```text
- Restore the successful live-import behaviour from before the Sunday/Monday import experiments.
- Keep the Manual Review/edit workflow so articles can be edited and restored manually.
- Do not allow RSS fallback summaries, source stubs, “Continue reading...” text, or weak fallback context to appear live.
- Pause Gemini for now.
- Re-evaluate Perplexity so failed, short, refused, timed-out or unverified rewrites go to Manual Review instead of public fallback.
```

### 2. Gemini work completed, tested, then paused

A Gemini verification scaffold and dry-run workflow was temporarily built and tested during the session. It included:

```text
- Disabled-by-default article verification service scaffold.
- Admin status endpoint.
- Dry-run test endpoint.
- Budget guard and budget status.
- Gemini implementation.
- Two-pass Gemini flow.
- Source-text extraction.
- Unsupported-claim and numeric-claim safety guards.
- Optional import flag and optional RSS import wiring.
```

Testing showed Gemini could produce useful verified rewrites, but it was not stable enough for the live import pipeline yet. Issues seen during testing:

```text
- Gemini quota/resource exhaustion: 429 RESOURCE_EXHAUSTED.
- Occasional provider/model availability issues.
- Over-cautious local-angle decisions.
- Need for further refinement before production use.
```

Decision made:

```text
Gemini is paused and removed from the live import path for now.
Do not continue Gemini import testing until the core RSS/Perplexity/manual-review behaviour is stable again.
```

A safety branch was created before rollback:

```text
safety-before-saturday-restore-20260525
```

### 3. Rollback to Saturday import baseline

The code was reverted back to the last known Saturday baseline before Sunday/Monday import experiments:

```text
7fcb02d | Sat May 23 08:08:17 2026 | Strengthen Perplexity rewrite verification flow
```

The revert removed the Gemini import path and the Sunday/Monday import experiments. This restored the older working import structure while retaining the pre-existing Manual Review/edit system from Thursday/Friday.

Important: the user specifically confirmed that RSS fallback summary behaviour must not be restored. Therefore, the revert commit below was intentionally kept because it removed the bad fallback path:

```text
a59d6d6 Revert "Restore RSS fallback for short Perplexity rewrites"
```

Meaning:

```text
Perplexity weak/short/refused rewrite should not become a public RSS fallback summary article.
```

### 4. Manual Review/edit system verified after rollback

After rollback, current code was checked and confirmed to still contain:

```text
GET /api/admin/articles/manual-review
PUT /api/admin/articles/{article_id}
Manual Review edit/update restore flow
manual_review_hidden_from_public filtering
Perplexity MANUAL_REVIEW_REQUIRED marker handling
```

This means the admin Manual Review/edit capability remains available, even though the later quick-send-to-manual-review endpoint added on Sunday was reverted as part of restoring Saturday behaviour.

### 5. Public article endpoint bug discovered and fixed

After rollback, the public article API returned:

```json
{
  "detail": "name 'archived_clause' is not defined"
}
```

Root cause:

```text
/api/articles fallback/top-up section referenced archived_clause, but that variable was undefined after the rollback.
```

Fix committed and pushed:

```text
0a34435 Fix public article fallback visibility query
```

Fix behaviour:

```text
Public fallback/top-up query now uses an explicit safe visibility filter:
- not archived
- manual_review_hidden_from_public != true
```

This prevents Manual Review-hidden articles leaking back into the public homepage/article feed fallback pool.

### 6. Perplexity fallback behaviour re-evaluated and fixed

The current Perplexity service still had risky fallback paths after rollback. These paths could return RSS summaries or expanded summaries when Perplexity failed, refused, timed out, hit budget guard, returned HTTP error, or produced too-short output.

Risky behaviour removed:

```text
Perplexity missing key -> return summary
Perplexity budget guard -> return expanded summary
Perplexity HTTP error -> return summary
Perplexity refusal -> return expanded summary
Perplexity retry still weak -> return expanded summary
Perplexity timeout/error -> return summary
```

New behaviour:

```text
All failed/short/refused/timed-out/API-error/budget-guard Perplexity rewrites now return:
MANUAL_REVIEW_REQUIRED: reason
```

Commit:

```text
0a9ebda Send failed Perplexity rewrites to manual review
```

Verification grep after patch showed no remaining live-generation paths returning RSS summary/expanded summary:

```text
MANUAL_REVIEW_REQUIRED: Perplexity API key is not configured.
MANUAL_REVIEW_REQUIRED: Perplexity budget guard skipped article rewrite.
MANUAL_REVIEW_REQUIRED: Perplexity content generation returned HTTP status.
MANUAL_REVIEW_REQUIRED: Perplexity refused to generate verified article content.
MANUAL_REVIEW_REQUIRED: Perplexity rewrite was below the quality floor after retry.
MANUAL_REVIEW_REQUIRED: Perplexity rewrite timed out.
MANUAL_REVIEW_REQUIRED: Perplexity rewrite failed with an error.
```

### 7. Small normal import test after Perplexity fallback fix

A controlled normal import test was run with Gemini off and Perplexity on:

```json
{
  "cheshire_articles": 0,
  "uk_articles": 1,
  "business_articles": 1,
  "tech_articles": 0,
  "use_perplexity": true,
  "rewrite_delay_seconds": 0
}
```

Result:

```json
{
  "success": true,
  "total_imported": 2,
  "estimated_cost_usd": 0.01,
  "sources": {
    "perplexity": false,
    "rss": false
  }
}
```

Because the response format was restored to the older Saturday style, it did not include `public_imported` / `manual_review_imported`. Manual Review was checked directly.

The two imported weak articles went to Manual Review, not public:

```text
Business | This beach hut costs the same as a three-bedroom house
Reason: Perplexity verification requested manual review: Perplexity rewrite was below the quality floor after retry.

Finance | Hundreds of homes in Kent and Sussex left without water after supply outages
Reason: Perplexity verification requested manual review: Perplexity rewrite was below the quality floor after retry.
```

This confirms the desired behaviour:

```text
Weak/failed Perplexity rewrite -> Manual Review -> not public fallback article
```

### 8. Public article cleanup performed

Public body scans were run against live article bodies, not just titles/summaries. The scan looked for:

```text
fallback version brief
automated rewrite could not produce enough verified detail
Readers should refer to the original source
Continue reading...
this story was reported by
manual review leakage
wedding/fascinator/dress/fashion filler
Scott McTominay / banknote / football novelty
Starwatch / blue moon / fossil / tar pits filler
Buzzballz / child-appeal alcohol story
Kent/Sussex outage / beach hut weak out-of-area story
```

One remaining weak public article was found and archived:

```text
Finance | From capri pants to padel rackets: 43 ways to celebrate bank holiday weekend
ID: 6a0fe683e44266b4b8b9f7e0
Action: archived from public
```

Final public body scan result:

```text
public_articles_scanned = 124
bad_public_body_hits = 0
```

### 9. Current confirmed live state after deployment and QA

```text
Backend health: healthy
Public article API: fixed
Manual Review-hidden article exclusion: active in public fallback query
Gemini: paused / removed from import path
Manual Review/edit: still available
Perplexity strict prompt: still present
Perplexity failed/short/refused rewrite: now Manual Review, not RSS fallback
RSS fallback-summary articles: no longer allowed live from Perplexity generation path
Final public body scan: 0 bad hits
```

### 10. Current target operating mode

Use this as the working target from here:

```text
Good verified Perplexity rewrites can still go public.
Weak, short, failed, refused, generic, unverified or unsuitable rewrites go to Admin Manual Review.
Manual Review/edit remains available so articles can be fixed and restored manually.
No Gemini in live imports for now.
No RSS fallback summary, source stub, “Continue reading...” or fallback disclaimer content should be public.
```

### 11. Recommended next checks before further imports

Before running regular imports again:

```text
1. Verify /api/articles returns 200 and no archived_clause error.
2. Run a public body scan for fallback/manual-review/weak-fit terms.
3. Run one small normal import test only.
4. Check whether good articles publish and weak articles go to Manual Review.
5. Only then resume scheduled/normal import usage.
```

### 12. Important caution

Do not reintroduce any behaviour that does this:

```text
Perplexity failure/short rewrite/refusal/timeout/API error/budget guard
-> RSS expanded summary
-> public article
```

That behaviour is bad for Cheshire Today’s quality, SEO, reader trust, sponsor readiness and local/business/finance positioning.

---

## Project State Update — 2026-05-25 / 2026-05-26: Import Stability, Manual Review Cleanup, Gemini Pause

### Purpose of this update

This update records the final state after the import-quality investigation, Gemini testing, rollback, Perplexity fallback correction, public-feed cleanup, and Manual Review queue cleanup.

The target operating state is:

- Good, verified Perplexity rewrites can still go live.
- Weak, short, refused, failed, generic, unsupported or unsuitable rewrites must not go public.
- RSS fallback-summary articles must not go live.
- Manual Review/edit must remain available so articles can be manually corrected and restored.
- Gemini is paused and removed from the live import path for now.
- Public site must remain clean and aligned with the Cheshire Today strategy.

### Strategic rule confirmed

Cheshire Today must continue to follow the hybrid local + business/finance + AI/tech authority strategy:

- Avoid weak generic national filler.
- Avoid crime-heavy filler.
- Avoid lifestyle/fashion/sports novelty filler.
- Avoid fallback summaries and “continue reading” source stubs.
- Prioritise useful Cheshire local, business, finance, tax, property, AI and technology content.
- Keep reader experience clean and professional.
- Preserve affiliate-first monetisation readiness and editorial authority.

### Rollback decision

The code was rolled back to the Saturday 23 May 2026 working import state after Sunday/Monday import experiments caused unwanted behaviour.

Restore target:

- Pre-problem import behaviour where good articles successfully went live.
- Manual Review/edit system preserved.
- Gemini removed from the live import path.
- RSS fallback-summary publishing blocked.

Safety branch created before rollback:

- `safety-before-saturday-restore-20260525`

Rollback point used:

- `7fcb02d` — `Strengthen Perplexity rewrite verification flow`

The rollback removed the Gemini experiment commits and later import/fallback experiments while preserving the existing Manual Review/edit workflow from the earlier stable system.

### Gemini status

Gemini testing was paused.

Gemini had been tested through dry-run and controlled import paths, but it was not reliable enough to continue:

- It worked in dry-run for some verified rewrites.
- It also hit quota/resource limits.
- It introduced complexity into the import path.
- It is not currently wanted in the live import system.

Current desired Gemini state:

- No Gemini import wiring.
- No Gemini automatic publishing.
- Future Gemini work should only resume after the current Perplexity + Manual Review workflow is stable.

### Perplexity fallback fix

A key issue was identified in `backend/app/perplexity_service.py`.

Risky behaviour found:

- Missing Perplexity API key returned RSS summary.
- Perplexity budget guard returned expanded RSS summary.
- Perplexity HTTP error returned RSS summary.
- Perplexity refusal returned expanded RSS summary.
- Retry below quality floor returned expanded RSS summary.
- Timeout/error returned RSS summary.

This was not acceptable because it could allow fallback/source-stub articles to go public.

Fix committed:

- `0a9ebda` — `Send failed Perplexity rewrites to manual review`

New desired behaviour:

- Perplexity API key missing → `MANUAL_REVIEW_REQUIRED`
- Perplexity budget guard skipped rewrite → `MANUAL_REVIEW_REQUIRED`
- Perplexity API HTTP error → `MANUAL_REVIEW_REQUIRED`
- Perplexity refusal → `MANUAL_REVIEW_REQUIRED`
- Perplexity retry below quality floor → `MANUAL_REVIEW_REQUIRED`
- Perplexity timeout/error → `MANUAL_REVIEW_REQUIRED`

Confirmed result:

- Failed or weak Perplexity rewrites now go to Admin Manual Review instead of going live as RSS fallback-summary content.

### Public article endpoint fix

After rollback, `/api/articles` exposed a bug:

- Error: `name 'archived_clause' is not defined`

This was found in the public article fallback/top-up query.

Fix committed:

- `0a34435` — `Fix public article fallback visibility query`

The fallback query was changed to use a safe public visibility filter:

- Exclude archived articles.
- Exclude `manual_review_hidden_from_public=True`.

Purpose:

- Prevent Manual Review-hidden articles leaking into the public fallback/top-up article pool.
- Fix public article API stability.

### Manual Review queue filter fix

Issue found:

- Archived articles were still showing in the Admin Manual Review queue.
- The Manual Review endpoint query only checked `manual_review_hidden_from_public=True`.

Fix committed:

- `d77c9be` — `Hide archived articles from manual review queue`

New Manual Review endpoint behaviour:

- Show only non-archived articles where `manual_review_hidden_from_public=True`.

Confirmed result:

- Archived weak queue items no longer appear after they are properly archived.
- Manual Review queue now reflects only active items needing manual editing.

### Public-feed QA

A full public body scan was run against live public articles.

Bad patterns checked included:

- `fallback version brief`
- `automated rewrite could not produce enough verified detail`
- `Readers should refer to the original source`
- `Continue reading...`
- Manual Review text leaking public
- Perplexity/Gemini review text leaking public
- Wedding/fascinator/fashion filler
- Scott McTominay/banknote/sports novelty
- Buzzballz/alcohol child-appeal story
- Blue moon/starwatch/fossil/tar pits/Los Angeles filler
- Kent/Sussex water outage
- Beach hut curiosity article

Final public body scan result:

- `public_articles_scanned = 124`
- `bad_public_body_hits = 0`

This confirms the public feed was clean at the time of this update.

### Normal import test after Perplexity fallback fix

A small normal import was run with:

- Gemini disabled.
- Perplexity enabled.
- Small UK/Business counts.

Result:

- Import created weak examples, but they were sent to Manual Review instead of going public.
- Examples:
  - `This beach hut costs the same as a three-bedroom house`
  - `Hundreds of homes in Kent and Sussex left without water after supply outages`

Manual Review reason:

- `Perplexity verification requested manual review: Perplexity rewrite was below the quality floor after retry.`

This confirms the key desired behaviour:

- Weak Perplexity result → Manual Review
- Not public fallback article

### Manual Review queue cleanup

Manual Review initially contained weak/test leftovers. These were reviewed and split into:

Keep for possible manual edit:

1. `HMRC made us wait a year for £150,000 tax rebate`
2. `All this talk about ‘difficult’ cuts, yet the largest part of Britain’s welfare bill is never mentioned. Why? | Zoe Williams`
3. `DWP pursued woman’s employer for nonexistent ‘benefit debt’`

Archived from Manual Review queue:

- Beach hut curiosity article.
- Kent/Sussex water outage article.
- Blue moon/starwatch article.
- Los Angeles fossil/tar-pits article.
- Buzzballz alcohol-child-appeal article.
- Wedding dresses article.
- Mars colony/Grok/SpaceX weak article.

Final Manual Review queue result:

- `manual_review_total = 3`

Remaining Manual Review items:

1. `HMRC made us wait a year for £150,000 tax rebate`
2. `All this talk about ‘difficult’ cuts, yet the largest part of Britain’s welfare bill is never mentioned. Why? | Zoe Williams`
3. `DWP pursued woman’s employer for nonexistent ‘benefit debt’`

### Current confirmed system state

Confirmed after deployment and QA:

- Backend healthy.
- Repo clean after commits.
- Public article API working.
- Public feed clean.
- Manual Review queue clean.
- Manual Review/edit workflow preserved.
- Failed Perplexity rewrites go to Manual Review.
- RSS fallback-summary content no longer goes public.
- Gemini paused and not part of live imports.
- Weak/test leftovers archived.
- Manual Review queue only contains useful possible edit candidates.

### Important operational instruction going forward

Do not reintroduce RSS fallback-summary publishing.

Do not resume Gemini import wiring until the current Perplexity + Manual Review workflow has remained stable across normal scheduled imports.

Before any new import-related development:

1. Check public article feed.
2. Check Manual Review queue.
3. Check backend health.
4. Check current git status.
5. Make one small change at a time.
6. Compile.
7. Commit.
8. Push/deploy only after verification.
9. Run public body scan after deploy.
10. Update this project state file after any major project day.

### Recommended next steps

1. Let the next scheduled import run normally.
2. After the run, verify:
   - good articles went public,
   - weak articles went to Manual Review,
   - no fallback/source-stub text appears public.
3. Review the 3 Manual Review articles manually and decide whether to rewrite/restore or archive.
4. Keep Gemini paused.
5. Later, refine Perplexity prompt further only if imports are too strict or too loose.

---

## 2026-05-26 late update — import rewrite recovery, article routing cleanup, and admin ChatGPT review layer

### Reason for this update

A production import/rewrite issue was investigated after scheduled/hybrid imports appeared to stop behaving correctly and test imports created unsuitable local stories. The work was handled cautiously because the current project rule is to check this state file before any future code/database/content-pool/category change, especially where previous import/filter fixes may have been tried and reverted.

### Key findings

1. The hybrid import endpoint itself was not dead. Controlled tests with `use_perplexity=true` returned successful imports and recorded Perplexity cost (`estimated_cost_usd: 0.005`).
2. The previous `use_perplexity=false` RSS-only test returning `total_imported: 0` was expected because raw RSS summaries usually fail the 1000+ character quality floor.
3. The 23 May rewrite-verification changes had made the Perplexity/import flow too difficult to verify. The later `MANUAL_REVIEW_REQUIRED` pathway caused inserted/hidden/manual-review records and made successful imports harder to understand.
4. Bad local Cheshire Live candidates slipped through during testing:
   - `Predator posed online as 15-year-old boy to groom teenage girl`
   - `CCTV appeal after £400 worth of Nicorette patches stolen from Morrisons`
   - `M62 updates as two breakdowns spark rush-hour gridlock`
5. The normal public `/api/articles?limit=250` no longer showed those test/problem records after filtering/checks, but some related/side-section behaviour exposed a separate endpoint issue.
6. The `/api/related-articles/{article_id}` endpoint was returning records without the same visibility and ID normalisation rules as the main article list, which could create broken article cards that clicked through to `Article not found`.
7. The admin OpenAI article review endpoint and UI were then built as a first safe review layer, with no automatic edit/archive/hide/publish behaviour.

### Commits completed and pushed in this phase

- `c5d603a` — `Preserve Cheshire scoped local article categories`
  - Fixed `/api/articles` category normalisation so manually added Cheshire-scoped Local News articles are not wrongly shown as `UK News` merely because `is_local_source` is missing.

- `0cb522d` — `Remove scheduled import rewrite delay regression`
  - Restored scheduled/import rewrite delay default from `900` seconds to `0` seconds.
  - Prevents scheduled import jobs from being blocked by a 15-minute artificial rewrite delay.

- `818dc1c` — `Tighten local crime safeguarding import filter`
  - Added safeguarding/crime terms such as `predator`, `groom`, `groomed`, `grooming`, `child sex`, and `online predator` to stop unsuitable local crime/safeguarding filler.

- `5d38070` — `Restore rewrite flow and align article lookup`
  - Removed the server-side `MANUAL_REVIEW_REQUIRED` import path from `server.py`.
  - Removed `extract_perplexity_manual_review_reason()` and `apply_perplexity_manual_review_marker()` from the import/publish path.
  - Restored the simpler working import rule: rewritten content must be at least 1000 characters or it is skipped.
  - Updated `/api/articles/{article_id}` to use `_find_article_by_any_id(article_id)` so JSON detail lookup better matches article/share routes.

- `be8d73a` — `Block theft appeal filler from local imports`
  - Added terms such as `cctv appeal`, `stolen`, `theft`, and `shoplift`/`shoplifting` to block low-value theft/CCTV appeal filler.

- `db7e69c` — `Restore traffic incident import filter`
  - Restored low-utility traffic/incident filters for terms including `traffic updates`, `live updates`, `rush-hour gridlock`, `gridlock`, `breakdown(s)`, `crash shuts`, `road closed`, `road closure`, and `recap:`.
  - This was explicitly aligned with the existing project-state rule to avoid traffic/incident churn unless there is clear wider public/economic impact.

- `d347fe1` — `Fix related article visibility and ids`
  - Updated `/api/related-articles/{article_id}` to exclude archived articles and `manual_review_hidden_from_public` records.
  - Returned reliable clickable IDs using `_id` or `id` and removed duplicate related IDs.
  - Fixed side/related article cards that could appear but click through to `Article not found`.

- `ecd4a30` — `Add admin OpenAI article review endpoint`
  - Added admin-only endpoint: `POST /api/admin/articles/{article_id}/ai-review`.
  - Uses server-side `OPENAI_API_KEY` and optional `OPENAI_REVIEW_MODEL`.
  - Default model in code: `gpt-4o-mini`.
  - Returns structured review JSON and saves review fields on the article:
    - `ai_review_status`
    - `ai_review_checked_at`
    - `ai_review_model`
    - `ai_review_result`
    - `ai_review_risk_level`
    - `ai_review_recommended_action`
    - `ai_review_safe_to_keep_live`
  - Does not edit article content.
  - Does not archive.
  - Does not hide.
  - Does not publish/unpublish.

- `a7aa5ea` — `Show OpenAI article review in admin`
  - Added Admin article-row UI support:
    - `Check with ChatGPT` button.
    - Loading spinner while review runs.
    - AI risk/action badge.
    - ChatGPT editor notes under the article row.
  - Frontend production build passed.

### OpenAI / ChatGPT review setup

Render backend environment variables added:

- `OPENAI_API_KEY`
- `OPENAI_REVIEW_MODEL=gpt-4o-mini`

Initial OpenAI endpoint test first returned `insufficient_quota`, which confirmed the endpoint and key were reaching OpenAI but billing/quota was not yet available. After quota/billing was resolved, the review endpoint worked.

Successful test article:

- Article: `Labour to expand youth work experience and training schemes`
- Article ID: `6a13717edd9994a983b23cd5`
- Endpoint: `POST /api/admin/articles/6a13717edd9994a983b23cd5/ai-review`

Returned review:

```json
{
  "safe_to_keep_live": true,
  "risk_level": "medium",
  "recommended_action": "manual_review",
  "category_fit": "good",
  "local_place_confirmed": false,
  "strategy_fit": "acceptable",
  "crime_or_safeguarding_risk": false,
  "traffic_or_incident_filler": false,
  "weak_lifestyle_or_clickbait": false,
  "unsupported_claims": [],
  "factual_concerns": [],
  "editor_notes": "The article discusses a national initiative with relevance to Cheshire, but lacks specific local place names or organizations. Consider adding local context or examples to strengthen the local relevance."
}
```

This was considered a good first result because it correctly flagged a national finance/employment article as safe but worth manual review for local context.

### Admin UI verification

After frontend deploy and refresh, Admin showed the review result correctly for the tested article:

- `AI: medium · manual_review`
- ChatGPT editor note visible below the article row.

The `Check with ChatGPT` button was also confirmed visible/working in Admin.

### Current confirmed behaviour after this phase

- Backend health checks passed after each deploy.
- Import endpoint runs successfully with Perplexity enabled.
- Perplexity rewrite delay is no longer 900 seconds.
- Import publish rule is now simple again: no 1000+ character rewritten content means the article is skipped.
- Bad crime/safeguarding/theft/traffic filler has been tightened at import filter level.
- Related article cards no longer use the unsafe old query that could expose hidden/archived/broken records.
- Admin-only ChatGPT review is live and visible in Admin.
- The ChatGPT review layer does not automatically mutate publication status.

### Important correction to older state-file guidance

Older notes in this state file mention failed Perplexity rewrites going to Manual Review. That was part of the post-23 May rewrite-verification/manual-review experiment and was removed in this recovery phase.

Current rule after this update:

- Failed/short Perplexity rewrite = skip import/publish.
- ChatGPT/OpenAI review = admin-only post-import review/flagging tool.
- ChatGPT/OpenAI review does not control publish/archive/hide automatically.

### Do not reintroduce without deliberate testing

Do not reintroduce the `MANUAL_REVIEW_REQUIRED` import path or hidden/manual-review insert behaviour unless explicitly planned and tested separately.

Do not loosen the restored traffic/crime/theft filters without checking this state file first.

Do not add automatic OpenAI review after every import yet. First observe manual admin usage and cost/quality.

### Recommended next steps

1. Use the Admin `Check with ChatGPT` button manually on a small number of fresh articles.
2. Watch whether the AI review correctly flags:
   - crime/theft/safeguarding filler,
   - traffic/incident filler,
   - weak shopping/lifestyle filler,
   - national finance/business stories lacking local context,
   - unsupported local claims.
3. Later, if manual testing is good, consider automatic review only for risky article types, not all articles.
4. Consider adding an Admin filter for `AI risk: high/medium/low` once enough reviews exist.
5. Continue verifying the next scheduled import before making any more import-pipeline changes.

---

# Cheshire Today — Project State Update — 30 May 2026

This update is intended to be appended to the single chat-source master state file `cheshire_today_project_state_latest_UPDATED_20260526.md`.

It records the full 30 May 2026 working session, including import generation checks, Perplexity budget control, Manual Review improvements, admin UI updates, Force Live publishing fixes, stale review-status prevention, stale RSS freshness filtering, GitHub token renewal check, deployments, verification, and follow-up actions.

---

## Operating rules reaffirmed

The session followed the established Cheshire Today workflow:

- Check current state before changing code, database, content pool, categories, scheduler or publication logic.
- Use one command at a time.
- Avoid manual file edits; use safe terminal/script changes.
- Use `grep`, not `rg`.
- Verify after every change.
- Do not use `npm start` unless explicitly asked.
- Preserve the strategy: Cheshire local + business/finance + AI/tech authority, affiliate-first monetisation, Facebook traffic, newsletter growth, SEO/indexing, sponsor readiness, clean reader experience, and a rough 40% Local / 40% Business+Finance / 20% AI-Tech mix.
- Avoid crime-heavy filler, weak generic national filler, stale articles surfaced as fresh, exaggerated headlines, and intrusive ads.

The current chat-source state file was checked during the session before continuing the freshness-rule work.

---

## 1. Perplexity budget and scheduled import cap review

### Problem

The site regularly hit the Perplexity daily budget cap:

```text
PERPLEXITY_DAILY_BUDGET_GBP = 0.70
```

The user asked how many articles should surface so the site does not hit the cap every import.

Inspection confirmed scheduled jobs requested 12 candidates:

```text
morning_article_generation args=[12]
midday_article_generation args=[12]
evening_article_generation args=[12]
```

The user correctly clarified the intended behaviour:

```text
Request 12 candidates, but only publish 4 public per run; the rest should go to Manual Review.
```

The scheduler already called:

```python
await generate_articles(GenerateArticlesRequest(count=count, include_uk_news=True, public_import_limit=4))
```

### Issue found

The public cap existed, but the import path could still try Perplexity rewrites after the public cap was reached or after the AI budget was exhausted. Logs showed repeated budget-guard warnings and short-content skips:

```text
Perplexity spend guard: projected £0.70 exceeds daily budget £0.70
Perplexity budget guard: skipping generate_article_content() call
Skipping short-content article after rewrite attempt
```

This meant candidates could be lost instead of saved to Manual Review and unnecessary AI attempts could continue.

---

## 2. Backend fix: stop AI rewrite attempts after public cap

### Files changed

```text
backend/server.py
```

### Behaviour added

When `public_import_limit` is reached, the import path now queues the candidate for Manual Review without attempting a Perplexity rewrite.

Added in both RSS national/category path and local RSS path:

```python
manual_review_without_ai = public_import_limit is not None and public_imported >= public_import_limit

if manual_review_without_ai:
    logger.info(f"Public import cap reached before AI rewrite; queueing RSS candidate for manual review: {title[:60]}...")
    detailed_content = original_content
elif request.use_perplexity:
    ...
```

The short-content quality gate was also adjusted:

```python
if not manual_review_without_ai and len((detailed_content or "").strip()) < 1000:
    continue
```

### Cleanup protection added

In `_remove_duplicates_internal()`, Manual Review hidden articles are now skipped by the short-content cleanup:

```python
if article.get("manual_review_hidden_from_public") is True:
    continue
```

This prevents short RSS/manual-review candidates from being archived immediately by quality cleanup.

### Commit

```text
02e12f9 Limit AI rewrites before manual review cap
```

---

## 3. Backend fix: queue review candidates when AI budget is exhausted

### Files changed

```text
backend/app/perplexity_service.py
backend/server.py
```

### New non-mutating budget helper

Added to `backend/app/perplexity_service.py`:

```python
def ai_budget_available(cost_estimate_gbp: float = 0.05) -> bool:
    today = date.today().isoformat()
    if _ai_usage["date"] != today:
        return True
    projected = (_ai_usage["calls"] + 1) * cost_estimate_gbp
    return projected <= DAILY_AI_SPEND_GBP
```

### Server import update

The server import changed to:

```python
from app.perplexity_service import perplexity_service, ai_budget_available
```

The manual-review-without-AI logic became:

```python
manual_review_without_ai = (public_import_limit is not None and public_imported >= public_import_limit) or not ai_budget_available(0.05)
```

### Result

If Perplexity budget is exhausted, suitable candidates should now go to Manual Review instead of repeatedly trying failed Perplexity calls and being skipped.

### Commit

```text
9788798 Queue review candidates when AI budget exhausted
```

---

## 4. Deploy and scheduler verification

Backend health after deploy:

```json
{"status":"healthy","service":"cheshire-news"}
```

Scheduler status confirmed active jobs:

```text
midday_article_generation
evening_article_generation
morning_article_generation
weekly_roundup_batch_1
weekly_roundup_batch_2
weekly_roundup_batch_3
weekly_roundup_batch_4
daily_brief
```

Scheduler was confirmed running with 8 jobs.

---

## 5. Manual Review baseline and cleanup

### Manual Review baseline

Manual Review queue showed 8 hidden candidates after the morning run. Examples included:

```text
Update on major search following reports a person entered River Dee from bridge
Cheshire farm building could be bulldozed to make way for new homes
The 1p ISA ‘loophole’ that could help savers sidestep new HMRC tax rules
Recap: Cheshire rail disruption after 'lightning strike' leaves lines 'blocked'
Behind the scenes at Ellesmere Port’s Vauxhall electric van plant
Union considers strike action as it brands planned school job cuts 'a disaster'
Cheshire villagers 'understandably worried' as plans for 200 new homes emerge
Man, 25, airlifted to hospital as fire-hit Cheshire flats evacuated
```

### Editorial decision

Recommended archive:

```text
River Dee emergency/search
Rail disruption recap
Fire-hit flats / airlifted man
```

Recommended keep/review:

```text
Farm building homes plan
1p ISA / HMRC tax rules
Vauxhall electric van plant
School job cuts
200 homes plan
```

### Archived weak items

Archived:

```text
6a1a6f3641966a3fd5b8f20c | River Dee emergency/search
6a1a6f1241966a3fd5b8f208 | Rail disruption recap
6a1a6f2c41966a3fd5b8f20b | Fire-hit flats / airlifted man
```

Post-cleanup Manual Review count:

```text
manual_review_count_returned = 5
```

---

## 6. Reminder set for 12:15 import check

A reminder was created for 30 May 2026 at 12:15 to check the 12:00 article import and Manual Review queue.

Reminder command included:

```bash
/usr/bin/curl -sS 'https://cheshiretoday.co.uk/api/admin/articles/manual-review?limit=50' -H "Authorization: Bearer $ADMIN_TOKEN" | /usr/bin/python3 -c "import sys,json; d=json.load(sys.stdin); arts=d.get('articles',[]); print('manual_review_count_returned=', len(arts)); [print('-', a.get('title','')[:90], '| reason:', a.get('manual_review_reason','')[:70]) for a in arts]"
```

---

## 7. Admin Dashboard: Open AI button added to Manual Review and Archive

### User request

The user asked to add the Open AI button from normal Admin Articles into the Manual Review / Archive article editing areas.

### Existing code found

Search located:

```text
frontend/src/components/AdminDashboard.jsx
handleAIReviewArticle()
```

The existing handler calls:

```javascript
/api/admin/articles/${articleId}/ai-review
```

### Manual Review UI update

Manual Review cards were updated to show:

```text
Source · Edit · Open AI · Archive · Delete
```

The Open AI button uses:

```javascript
handleAIReviewArticle(article._id || article.id)
```

### Archive UI update

Archived rows now show an Open AI icon button before Restore for archived/manual-review articles.

### Shell quoting issue fixed

A first patch used JSX template literals with backticks and `${...}` which `zsh` interpreted, causing:

```text
zsh: bad substitution
```

The resulting broken JSX was fixed by using string concatenation instead:

```javascript
disabled={actionLoading === "ai-review-" + (article._id || article.id)}
{actionLoading === "ai-review-" + (article._id || article.id) ? (...)}
```

### Build and commit

Frontend build passed.

Commit:

```text
6b3c304 Add AI review button to manual review and archive
```

---

## 8. Manual Review cards now display AI review details

### Problem

Manual Review cards had the Open AI button, but did not display the same information as the normal Articles list.

Normal Articles list showed:

```text
AI: medium · manual_review
ChatGPT: editor note
```

Manual Review cards showed only:

```text
manual_review_reason
Source
Edit
Open AI
Archive
```

### Frontend display update

Manual Review cards were updated to display:

```text
AI: {risk_level} · {recommended_action}
ChatGPT: {editor_notes}
manual_review_reason
```

Added in `frontend/src/components/AdminDashboard.jsx`:

```javascript
article.ai_review_risk_level
article.ai_review_recommended_action
article.ai_review_result?.editor_notes
```

Frontend build passed.

Commit:

```text
fdeccf4 Show AI review details in manual review cards
```

### Backend projection issue found

The Manual Review API was not sending the AI review fields.

Endpoint:

```python
@api_router.get("/admin/articles/manual-review")
```

Projection was patched to include:

```python
"ai_review_risk_level": 1,
"ai_review_recommended_action": 1,
"ai_review_result": 1,
```

Backend compile passed.

Commit:

```text
906c2b2 Include AI review fields in manual review API
```

### Deployment verification

Live asset manifest was checked. The new Admin UI strings were found in:

```text
/static/js/362.b8c62215.chunk.js
```

The user later confirmed the Manual Review card displayed the AI review information properly.

---

## 9. Manual-edited article not publishing: Force Live restore fix

### Problem

The user manually edited the Royal Mail article but it did not publish.

Article:

```text
Royal Mail misses annual delivery targets amid £500m investment plan
```

Manual Review showed stale/manual-review status:

```text
verification_status = needs_manual_review
rewrite_status = manual_review_required
```

### Root cause

The `update_article()` logic rechecked the article and kept it hidden if review reasons remained. There was no strong editor override via `force_live`.

### Manual edit + force_live override added

In `backend/server.py`, `update_article()` now supports:

```python
force_live_override = bool(update_doc.get("force_live"))

if remaining_reasons and not force_live_override:
    keep manual review
else:
    restore from manual review
```

When restored, it clears:

```text
archived_at
archive_reason
manual_review_hidden_from_public
manual_review_hits
manual_review_reason
manual_review_created_at
```

and sets:

```text
verification_status = manual_corrected_verified_limited
rewrite_status = manual_corrected
```

### Force-live endpoint also patched

Endpoint:

```python
POST /api/admin/articles/{article_id}/force-live
```

When turning Force Live on, it now clears Manual Review hidden fields and marks the article restored:

```python
verification_status = "manual_force_live"
rewrite_status = "manual_force_live"
manual_review_restored_at = now
```

### Commit

```text
1f3ba9c Allow force live to restore manual review articles
```

### Verification

Force Live call returned:

```json
{
  "success": true,
  "article_id": "1d91f759-edfc-4e74-968e-afb56f4e42c6",
  "force_live": true,
  "message": "Article forced live"
}
```

Manual Review no longer returned the Royal Mail article.

Public API confirmed it was live:

```text
Royal Mail misses annual delivery targets amid £500m investment plan
category: UK News
source: Chester Standard
publishedDate: 2026-05-30T07:21:42
```

---

## 10. Prevent stale review status re-hiding edited live articles

### Problem

The user noticed that three articles which were already live had somehow gone into Manual Review after editing.

The Manual Review endpoint itself was correct:

```python
query = {
    "manual_review_hidden_from_public": True,
    "$or": [{"archived": {"$exists": False}}, {"archived": False}]
}
```

Therefore something had actively set:

```text
manual_review_hidden_from_public = true
```

### Root cause

In `update_article()`, an article was treated as Manual Review if:

```python
existing.get("manual_review_hidden_from_public") is True
or existing.get("verification_status") == "needs_manual_review"
or existing.get("archive_reason") == "needs_manual_review"
```

This meant a live article with stale `verification_status = needs_manual_review` could be re-hidden after normal editing.

### Fix

Removed `verification_status` alone from `was_manual_review`.

New logic:

```python
was_manual_review = (
    existing.get("manual_review_hidden_from_public") is True
    or existing.get("archive_reason") == "needs_manual_review"
)
```

This prevents live/manual-edited articles from being pushed back into Manual Review because of stale status fields.

Backend compile passed.

Commit:

```text
575ce78 Prevent stale review status rehiding edited articles
```

---

## 11. Manual Review cleanup after stale-status fix

After deployment, Manual Review queue showed 15 items. The edited live articles did not appear to have re-entered Manual Review.

Weak incident/disruption items were archived:

```text
6a1b17c35170b22f862a3465 | Recap: Cheshire rail disruption after 'lightning strike' leaves lines 'blocked'
6a1b17c35170b22f862a3467 | Man, 25, airlifted to hospital as fire-hit Cheshire flats evacuated
```

Manual Review queue reduced to:

```text
manual_review_count = 13
```

Remaining queue mostly contained useful candidate material.

---

## 12. 18:00 import check and stale RSS issue

### 18:00 import results

Counts after the 18:00 check:

```json
{
  "total": 2355,
  "visible": 71,
  "archived": 2284,
  "visible_featured": 5,
  "visible_priority": 0
}
```

Manual Review stayed at:

```text
manual_review_count = 13
```

Public API showed three new articles created at 17:00 UTC / 18:00 UK:

```text
‘It feels unfair’: the Britons struggling to get a mortgage since Iran war began
Gluten-free basics ‘now a luxury’ as price of a small branded loaf nears £4
British Gas to pay £70 million in compensation and debt write-offs...
```

### Problem found

The British Gas article was stale:

```text
publishedDate: 2026-05-15
created_at: 2026-05-30T17:00:05
```

It was incorrectly surfaced as a fresh 18:00 article.

### Decision

Add source-date freshness gates before Perplexity spend and public import:

```text
Business / Finance / Tech / UK: max 3 days old
Local: max 7 days old
```

Local has a wider window because planning/council/local public-service items can remain useful longer.

---

## 13. Backend fix: skip stale RSS articles before AI import

### File changed

```text
backend/server.py
```

### Helper added inside `import_hybrid_news()`

```python
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
```

### National / Business / Finance / Tech path

Added before Perplexity rewrite:

```python
if not is_source_fresh_enough(article, 3):
    logger.info(f"Skipping stale RSS article before Perplexity/public import: {title[:60]}...")
    continue
```

### Local RSS path

Added before Perplexity rewrite:

```python
if not is_source_fresh_enough(article, 7):
    logger.info(f"Skipping stale local RSS article before Perplexity/public import: {title[:60]}...")
    continue
```

### Result

Old source-dated RSS items should no longer be treated as fresh public imports, and stale items are skipped before Perplexity spend.

Backend compile passed.

Commit:

```text
a00c836 Skip stale RSS articles before AI import
```

Deployment health:

```json
{"status":"healthy","service":"cheshire-news"}
```

---

## 14. Existing stale British Gas article archived

Because the stale filter only prevents future imports, the already-imported British Gas item had to be archived manually.

ID found:

```text
6a1b17c25170b22f862a3462
```

Archive result:

```json
{"success":true,"message":"Article archived successfully"}
```

Verification:

```bash
/usr/bin/curl -sS 'https://cheshiretoday.co.uk/api/articles?limit=120' | /usr/bin/grep -i "British Gas to pay"
```

Silent output confirmed it was no longer public.

---

## 15. GitHub token / deploy token renewal check

### User concern

The user asked about a token expiring that day. The pasted details showed it was a GitHub Personal Access Token classic, not a Render token.

### Current token status

GitHub showed:

```text
render-deploy — repo
Expires on Fri, Aug 28 2026
Last used within the last week

ct transfer code to new website
Expired on Tue, Mar 3 2026
Very broad scopes
```

### Actions

Checked for Render/deploy tokens in environment:

```bash
/usr/bin/printenv | /usr/bin/grep -E 'RENDER|DEPLOY|HOOK' | /usr/bin/sed 's/=.*$/=SET/'
```

Silent output: no Render token in current terminal environment.

Listed env files:

```text
./frontend/.env.production.local.disabled
./frontend/.env.production
./frontend/.env.production.local
./frontend/.env
./frontend/.env.development.local
./frontend/.env.development
./backend/.env.bak_resend_20260411_1
./backend/.env
./.env
```

Removed old GitHub credential from macOS Keychain:

```bash
/usr/bin/security delete-internet-password -s github.com 2>/dev/null || true
```

Verified GitHub authentication:

```bash
/usr/bin/git ls-remote origin HEAD
```

Output:

```text
f5eae9ecd812a36c2c7da95e1d366ecb976bc7c9 HEAD
```

### Recommendation

Keep:

```text
render-deploy — repo — expires Fri, Aug 28 2026
```

Revoke/delete:

```text
ct transfer code to new website — expired Tue, Mar 3 2026 — very broad scopes
```

No need to add old broad scopes to the active token.

---

## 16. Current confirmed state at end of 30 May 2026 session

### Backend / deploy

Latest backend health check:

```json
{"status":"healthy","service":"cheshire-news"}
```

Latest important commits pushed during this working period:

```text
02e12f9 Limit AI rewrites before manual review cap
9788798 Queue review candidates when AI budget exhausted
6b3c304 Add AI review button to manual review and archive
fdeccf4 Show AI review details in manual review cards
906c2b2 Include AI review fields in manual review API
1f3ba9c Allow force live to restore manual review articles
575ce78 Prevent stale review status rehiding edited articles
a00c836 Skip stale RSS articles before AI import
```

### Import behaviour now intended

```text
Scheduled generation requests up to 12 candidates.
Only 4 should surface publicly per scheduled run via public_import_limit=4.
Extra suitable candidates go to Manual Review.
If Perplexity budget is exhausted, candidates go to Manual Review without wasting AI calls.
Manual Review hidden articles are protected from short-content archive cleanup.
RSS source-date freshness gates prevent stale articles from being imported as fresh.
```

### Source-date freshness rules

```text
Business / Finance / Tech / UK: source publishedDate must be within 3 days.
Local: source publishedDate must be within 7 days.
```

### Manual Review behaviour now intended

```text
Manual Review card shows:
- AI risk/action when available
- ChatGPT editor note when available
- manual_review_reason
- Source / Edit / Open AI / Archive controls

Open AI button exists in:
- normal Articles list
- Manual Review cards
- Archive/needs-review rows
```

### Force Live behaviour now intended

```text
Force Live clears Manual Review hidden fields.
Force Live restores article publicly.
Manual edit + force_live=true can override remaining manual-review reasons.
Live articles with stale verification_status=needs_manual_review should not be re-hidden after normal edits.
```

### Manual Review queue

After cleanup, Manual Review count was around:

```text
manual_review_count = 13
```

Remaining items were mostly review candidates rather than obvious incident filler.

### Public feed

The stale 15 May British Gas article was archived and no longer public.

---

## 17. Follow-ups for next session

### A. Verify next scheduled import after stale filter

After the next scheduled run, use:

```bash
/usr/bin/curl -sS 'https://cheshiretoday.co.uk/api/articles?limit=30' | /usr/bin/python3 -m json.tool | /usr/bin/grep -E '"title"|"category"|"source"|"publishedDate"|"created_at"' | head -160
```

Confirm:

```text
No Business/Finance/Tech/UK article older than 3 days should have a fresh created_at.
No Local article older than 7 days should have a fresh created_at.
```

### B. Review remaining Manual Review queue

Use:

```bash
/usr/bin/curl -sS 'https://cheshiretoday.co.uk/api/admin/articles/manual-review?limit=100' -H "Authorization: Bearer $ADMIN_TOKEN" | /usr/bin/python3 -c "import sys,json; d=json.load(sys.stdin); arts=d.get('articles',[]); print('manual_review_count=', len(arts)); [print('-', a.get('id',''), '|', a.get('title','')[:100], '| reason:', a.get('manual_review_reason','')[:80]) for a in arts]"
```

Likely review/publish candidates:

```text
Chester town centre trader shutting after 50 years
1p ISA / HMRC tax rules
Vauxhall electric van plant
farm building / homes plan if exact location is added
200 homes plan if exact location is verified
school job cuts if location and facts are verified
QEMU AI contribution ban
23andMe data breach
Energy bills item if source-date freshness is acceptable
```

Likely archive or treat carefully:

```text
AWS/Grok if too personality/filler
Universal/Bill Ackman if too remote and weak for Cheshire readers
malicious npm packages if too niche unless framed as practical business cybersecurity
California AG/23andMe if duplicate or weaker than main 23andMe article
```

### C. Watch Perplexity logs after next run

Expected after fixes:

```text
No repeated AI attempts after public cap reached.
No repeated budget-guard skip loops.
Candidates should queue for Manual Review if budget unavailable.
```

### D. Optional future Admin UI improvement

Manual Review now has Open AI and AI details. A next refinement could add an explicit button label such as:

```text
Force Live / Publish
```

so publishing a reviewed article is clearer than using a generic force-live toggle.

### E. Optional stale already-imported article audit

The new stale filter prevents future old-source imports, but already-imported stale public articles may remain.

Future scan idea:

```text
Find articles where created_at is much newer than publishedDate and source publishedDate breaches the policy window.
```

### F. Update the chat-source master file at the end of each major working day

Continue appending detailed updates to the single chat-source master file, not old repo-root state files, unless the user explicitly asks for a repo/root update.

---

## 18. Recommended new-chat resume prompt

Use this in a fresh chat:

```text
Continue Cheshire Today from the 30 May 2026 project state update. First check the single chat-source master state file before any code/database/content/category change. Follow the workflow: one command at a time, no manual file edits, use grep not rg, verify after each step, do not use npm start unless asked. The latest deployed fixes include: Perplexity budget-aware Manual Review queueing, public import cap handling, Manual Review Open AI button and AI details display, Force Live restoring Manual Review articles, stale status no longer re-hiding edited live articles, and RSS source-date freshness gates (3 days for Business/Finance/Tech/UK, 7 days for Local). Next priority: verify the next scheduled import does not surface stale source-dated articles, then review the remaining Manual Review queue and only publish strong local/business/finance/AI-tech candidates.
```

---

## 19. Project update — 1 June 2026 full QA pass, RSS cleanup, feed-limit fix, SEO/newsletter/sponsor checks

### A. Working protocol followed

- Used the current chat-source master state file as the source of truth before touching sensitive areas.
- Continued the one-command-at-a-time workflow.
- Avoided manual file edits; changes were applied through terminal/Python scripts only.
- Used `grep`, not `rg`.
- Verified after every change.
- Avoided `npm start`.
- No production-domain or Render environment changes were made manually during this QA pass.

### B. Initial public/backend baseline

Baseline health and article checks showed:

```text
/api/health returned healthy.
Manual Review initially showed 0 in one check, later 6 after another import/review cycle.
/api/articles?limit=10 returned 12 articles before the feed-limit fix.
```

The over-returning article API was confirmed with:

```text
/api/articles?limit=10 -> returned: 12
```

Cause found in `backend/server.py`: `force_live` articles were prepended after the list had already been filled to the requested limit:

```python
articles = forced_front + articles
```

The response was then deduped and returned without a final cap.

### C. Fix deployed — enforce `/api/articles?limit=N` after curation

A final cap was added after feed curation, force-live prepending, boosting, skip, and dedupe:

```python
# Enforce requested API limit after force-live prepending, boosting, skip, and dedupe.
# This keeps /api/articles?limit=N predictable for homepage, admin QA, feeds, and consumers.
unique_articles = unique_articles[:limit]
```

Verification:

```text
python compile: passed
commit: 1bd3307 Enforce article API limit after feed curation
push: full-scrape-prod -> origin/full-scrape-prod
Render deploy: healthy
/api/articles?limit=10 -> returned: 10
```

After deploy, the endpoint correctly returned exactly 10 articles.

### D. SEO/article canonical/Facebook/Googlebot verification

A concern was raised that article slug URLs may be returning the React SPA shell with homepage canonical metadata.

Tests confirmed the behaviour is intentional and safe:

- Normal browser/plain curl receives the React SPA shell.
- `/article/{id}` returns `301` to `/article/{id}/{slug}`.
- Facebook/social crawlers receive article-specific SEO HTML.
- Googlebot desktop receives article-specific SEO HTML.
- Googlebot Smartphone receives article-specific SEO HTML.

Verified crawler metadata for article examples included:

```text
<title>University of Chester base helps teaching staff supplier grow links with schools</title>
<link rel="canonical" href="https://cheshiretoday.co.uk/article/.../university-of-chester-base-helps-teaching-staff-supplier-grow-links-with-schools">
<meta property="og:url" content="https://cheshiretoday.co.uk/article/...">
<meta property="og:title" content="University of Chester base helps teaching staff supplier grow links with schools">
<meta property="og:image" content="https://www.chesterstandard.co.uk/resources/images/20980209/">
```

For the NHS article:

```text
/article/6a1d11e4ed91e8804eb9c8d3 -> 301 to slug URL
Googlebot slug metadata:
title: NHS single patient record to be debated for first time
canonical: https://cheshiretoday.co.uk/article/6a1d11e4ed91e8804eb9c8d3/nhs-single-patient-record-to-be-debated-for-first-time
og_image: https://ichef.bbci.co.uk/ace/standard/1024/cpsprodpb/0ba5/live/051bf5e0-5d63-11f1-b62a-a36369f74e54.jpg
```

Conclusion:

```text
Do not change the article route at this stage.
Facebook previews are protected.
Googlebot desktop and smartphone receive article-specific metadata.
Search Console canonical warnings are likely historical or duplicate/discovery related, not caused by the current article route.
```

### E. Search Console and sitemap discovery check

A fresh article URL was inspected in Google Search Console:

```text
URL is not on Google.
Page is not indexed: URL is unknown to Google.
No referring sitemaps detected.
Last crawl: N/A.
Crawled as: N/A.
```

The same URL was confirmed live in the current sitemap:

```text
https://cheshiretoday.co.uk/article/6a1c14dcd7fe0d63f6548809/founder-of-chester-based-business-takes-on-charity-cycling-challenge
```

Conclusion:

```text
This was a discovery/recrawl lag issue, not a current code failure.
Action recommended in Search Console: resubmit sitemap.xml and news-sitemap.xml, then request indexing for selected strong fresh URLs.
```

### F. Sitemap checks

Main sitemap and news sitemap were checked after the earlier news-sitemap tightening:

```text
main_sitemap_urls: 88
article_urls: 40
guide_urls: 35
news_sitemap_urls: 4
```

The news sitemap is now very strict and only includes a small number of fresh/strategic articles.

Known future improvement:

```text
High-value UK News articles are currently excluded from both main sitemap article inclusion and news sitemap article inclusion if their category remains UK News.
Potential future rule: allow UK News only when it contains strong public-interest/economic/business/finance/technology terms such as NHS, hospital, GP, schools, housing, rent, mortgage, tax, energy, bills, transport, rail, jobs, wages, business, economy, AI, data, cyber, digital, privacy, government, regulator.
Do not add all UK News to sitemaps.
```

### G. Homepage/feed quality and category balance

After the API limit fix, `/api/articles?limit=24` returned exactly 24.

Homepage 24-feed mix during QA:

```text
Tech: 2
Local News: 10
UK News: 5
Business: 3
Finance: 4
```

Approximate strategic balance:

```text
Local News: 10 / 24 = 41.7%
Business + Finance: 7 / 24 = 29.2%
UK News: 5 / 24 = 20.8%
Tech: 2 / 24 = 8.3%
```

Interpretation:

```text
Local balance is on target.
Business/Finance is acceptable when UK economy/public-service stories are considered support content.
AI/Tech is slightly under the 20% target, but do not force weak tech filler.
Keep improving AI/Tech naturally through better practical AI/business-tech imports.
```

### H. Admin force-live cleanup

Royal Mail article was found leading the feed because it was still `force_live: True`:

```text
Royal Mail misses annual delivery targets amid £500m investment plan
category: UK News
force_live: True
published: 2026-05-30T07:21:42
created: 2026-05-30T11:00:42
```

Admin action taken:

```text
POST /api/admin/articles/6a1ac35b8ef0f7706d9f2101/force-live
result: Force live removed
```

After removal, `/api/articles?limit=10` returned a cleaner top feed:

```text
1 Tech - ChatGPT web-page flaw highlights new phishing risk for local businesses
2 Local News - Founder of Chester-based business takes on charity cycling challenge
3 UK News - Arm boss in line for billion-dollar payday if chipmaker hits targets
4 UK News - Wes Streeting calls for NI tax cuts for businesses to ‘incentivise’ hiring
5 Local News - New online-only Cheshire town estate agency sells homes in under 14 days
6 UK News - NHS single patient record to be debated for first time
7 Local News - Cheshire landlords warned over £40,000 fine risks after rental law changes
8 Local News - New clinic offers Chester residents chance to optimise health and slow down aging
9 Local News - From seed shop to popular garden centre: Family marks 200 years in business
10 Local News - University of Chester base helps teaching staff supplier grow links with schools
```

Remaining active force-live item:

```text
Behind the scenes at Ellesmere Port’s Vauxhall electric van plant
```

Decision:

```text
Leave this one for now because it is local, business/economy relevant, and not dominating the top 10.
```

### I. Article page readability and monetisation/guide checks

Article page API content was checked:

```text
Founder of Chester-based business takes on charity cycling challenge
content_len: 2441
```

The browser-facing article page was visually checked by user and confirmed OK.

Bundle inspection confirmed the article page has available monetisation surfaces:

```text
affiliate-sidebar
affiliate-inline
affiliate-end-article
affiliate-mobile
article_sidebar sponsored placement
article_mobile sponsored placement
guide/related modules
newsletter modules
```

User confirmed live visual layout is OK.

Keep future rule:

```text
Article body should stay clean.
Desktop monetisation should mainly be sidebar + below article.
Mobile should use at most one compact sponsor/affiliate block before the end of article, then related/guide after article.
Avoid large mid-article blocks that split stories aggressively.
```

### J. Newsletter QA

Public newsletter pages and subscribe validation were checked:

```text
/newsletter/preferences -> 200
/unsubscribe -> 200
POST /api/newsletter/subscribe with empty body -> controlled validation error: email field required
```

Admin auth note:

```text
Local backend/.env permanent token was not accepted by production.
Fresh 24-hour admin token generated successfully through /api/admin/login using configured admin credentials.
/admin/verify returned valid true.
No Render environment change was made.
```

Admin stats:

```text
articles total: 2399
subscribers total: 14265
latest_article_date: 2026-06-01T04:02:07
```

Subscriber endpoint QA:

```text
/api/admin/subscribers returned 1000 records and total_field 1000.
/admin/stats says subscribers total is 14265.
```

Finding:

```text
/admin/subscribers is capped at 1000 and reports total as len(subscribers), not the true subscriber count.
Future fix: add real total via count_documents(), plus skip/limit pagination.
Do not expose personal emails in QA output.
```

Email configuration status:

```text
SMTP enabled: true
SMTP host/user/password/from set: true
Resend enabled: true
Resend API key/from/reply-to set: true
base_url: https://cheshiretoday.co.uk
api_url: https://cheshiretoday.co.uk/api
```

30-day email analytics:

```text
total_emails_sent: 53000
total_opens: 7091
total_clicks: 7572
unique_openers: 5704
unique_clickers: 937
open_rate: 10.8%
click_rate: 1.8%
click_to_open_rate: 16.4%
DailyBrief sent: 44000, success: 35900
WeeklyRoundup sent: 9000, success: 4000
```

Latest Daily Brief:

```text
2026-06-01 DailyBrief: subscribers 1000, delivered 1000, opens 408, clicks 30
```

Intermittent failures found:

```text
WeeklyRoundup 2026-05-31: subscribers 1000, delivered 0
Older DailyBrief 2000-recipient batches sometimes delivered 0
Several failed logs have success_count 0 but no useful error field
One old 2026-05-11 failure was manually marked failed after stuck scheduled send
```

Decision:

```text
Do not suppress subscribers yet.
Daily Brief is currently working.
Investigate Weekly Roundup success_count=0 and older 2000-batch failures later.
Improve digest failure logging later.
```

### K. Sponsor/advertising QA

Public sponsor placement APIs checked:

```text
/api/sponsored-placements?placement=homepage_sidebar&limit=1 -> success true
/api/sponsored-placements?placement=homepage_mobile&limit=1 -> success true
```

Active campaign:

```text
The Retreat Social Club Opens This July
Campaign: retreat-social-club-open-day-20260701
Placement: homepage_sidebar and homepage_mobile
Package: Local Starter
Image present
Target URL present
Campaign active until 2026-07-02
```

Tracking:

```text
homepage_sidebar impression_count around 299, click_count 1
homepage_mobile impression_count around 296, click_count 2
```

Finding:

```text
Sponsor placements are live, locally relevant, and tracked.
Future improvement: filter obvious bot/crawler traffic from sponsored impression counts so sponsor reporting is cleaner.
```

### L. Affiliate/guide QA

Affiliate public API:

```text
/api/affiliates/public -> success true, products 0
```

Interpretation:

```text
Dynamic affiliate product feed is reachable but currently empty.
Monetisation currently depends on authority guides, fallback guide/affiliate cards, sponsor placements, and guide CTAs.
```

Authority pages checked:

```text
/api/authority-pages?limit=10&status=published -> 10 pages
```

Examples returned:

```text
best-mobile-sim-deals-uk
best-parcel-courier-services-small-business-uk
best-online-gcse-a-level-courses-uk
best-ai-writing-tools-uk
best-ai-tools-uk
best-ai-productivity-tools-uk
best-tax-software-uk
best-payroll-software-uk
best-small-business-insurance-uk
best-explainer-video-software-uk
```

Finding:

```text
Authority guide layer is live and supports affiliate-first monetisation.
Populate/activate dynamic affiliate product records later only after confirming affiliate approvals and avoiding article clutter.
```

### M. Admin/article/archive QA

Admin article counts:

```text
total stored articles: 2399
visible: 68
archived: 2331
visible_featured: 5
visible_priority: 0
```

Admin article stats:

```text
total: 4954
active: 68
archived: 4886
legacy_archived: 2331
collection_archived: 2555
oldest_date: 2026-03-31T06:49:29.633798+00:00
newest_date: 2026-06-01T04:02:07
```

Active category mix from admin article stats:

```text
Local News: 23
UK News: 16
Business: 15
Finance: 10
Tech: 4
```

Visible public mix from `/api/articles?limit=80`:

```text
returned: 49
Tech: 4
Local News: 19
UK News: 5
Business: 11
Finance: 10
```

Manual Review:

```text
Manual Review queue later showed total 6.
User decided to skip inspection and decide later when editing.
```

Archived endpoint:

```text
/api/admin/articles/archived?limit=5 returned total 4886 and only 5 articles.
Memory-safe pagination fix is holding.
```

Jobs endpoint:

```text
/api/admin/jobs returned success true, total 0, jobs_returned 0.
```

### N. Performance/static routing QA

Performance checks:

```text
homepage: 200 total=0.320266s size=8772
articles24: 200 total=1.350951s size=20122
article API: 200 total=0.655445s size=3850
```

Static asset caching:

```text
/static/js/main.547c18cf.js -> cache-control: public, max-age=31536000, immutable
/static/css/main.9d5eb182.css -> cache-control: public, max-age=31536000, immutable
```

Key public route checks all returned 200:

```text
/
/category/local-news
/category/business
/category/finance
/guides/best-ai-tools-uk
/guides/best-savings-accounts-uk
/privacy
/terms
/affiliate-disclosure
/advertise
/contact
```

Homepage HTML source check:

```text
Plain homepage HTML exposes only the SPA shell/title and does not expose article links server-side.
```

Finding:

```text
Not urgent because sitemaps and crawler-specific article HTML work.
Future SEO improvement: consider server-side/static article links in homepage initial HTML or a lightweight crawlable latest-links block, but avoid layout risk during QA.
```

### O. Health-route `HEAD /api/health` decision

Production check confirmed:

```text
GET /api/health -> 200
HEAD /api/health -> 404
```

A local patch was briefly attempted but stopped after checking the state file and seeing this had already been identified as non-critical log noise and a duplicate-route cleanup backlog item.

Action taken:

```text
git restore backend/server.py
repo returned clean
No health-route code change committed
```

Decision:

```text
Leave HEAD /api/health 404 as known low-risk log noise.
Clean duplicate /api/health route declarations later in a controlled maintenance phase only.
```

### P. RSS QA issue found and fixed

RSS feed initially exposed weak/off-strategy items because the RSS route used:

```python
db.articles.find({})
```

Examples seen in RSS before fix:

```text
Masturbation among birds is ‘natural’ and should not be punished, say experts
KSI quits Sidemen collective after 13 years
WHO calls for community cooperation to contain Ebola outbreak in DRC
Sturgeon items
River search under way for missing boy, 11
```

One bad RSS item was confirmed active, not archived:

```text
Masturbation among birds is ‘natural’ and should not be punished, say experts
archived: False
manual_review_hidden_from_public: None
source: The Guardian
category: UK News
```

RSS route was patched so `/rss.xml` only pulls strategic public articles:

```python
rss_query = {
    "$or": [{"archived": {"$exists": False}}, {"archived": False}],
    "manual_review_hidden_from_public": {"$ne": True},
    "category": {"$in": ["Local News", "Business", "Finance", "Tech", "AI", "AI & Tech", "Tax", "Property"]}
}
```

Verification:

```text
python compile: passed
commit: eb6f682 Restrict RSS feed to strategic public articles
push: full-scrape-prod -> origin/full-scrape-prod
Render deploy: healthy
/rss.xml after deploy: rss_items 46
Bad old RSS items not found
```

Post-fix RSS top items were much closer to strategy:

```text
Llandudno Junction to Chester rail line set for two-day closure for essential work
University of Chester base helps teaching staff supplier grow links with schools
From seed shop to popular garden centre: Family marks 200 years in business
Poor train Wi-Fi is still costing commuters time — and businesses should notice
New clinic offers Chester residents chance to optimise health and slow down aging
Gluten-free basics ‘now a luxury’ as price of a small branded loaf nears £4
Founder of Chester-based business takes on charity cycling challenge
New online-only Cheshire town estate agency sells homes in under 14 days
Northwich trader to close shop after five decades serving town
Cheshire landlords warned over £40,000 fine risks after rental law changes
```

RSS follow-up note:

```text
RSS is now clean enough, but later it may need the same high-value UK News allow-list as sitemap/news-sitemap so strong public-service/economy/technology UK News can appear while weak generic UK News remains excluded.
```

### Q. Deferred/backlog items from this QA pass

1. **Automatic OpenAI review before publish**
   - Current OpenAI review is manual-button only at `/admin/articles/{article_id}/ai-review`.
   - Later target pipeline:

```text
RSS -> duplicate/archive guard -> Perplexity rewrite -> internal checks -> OpenAI review -> publish only if safe -> otherwise Manual Review
```

2. **High-value UK News sitemap/RSS allow-list**
   - Do not add all UK News.
   - Later allow only strong public-service/economy/finance/technology UK News.

3. **Admin subscribers endpoint pagination**
   - Current endpoint returns first 1000 only and reports total as 1000.
   - Add `skip`, `limit`, and true `count_documents()` total later.

4. **Weekly Roundup / old 2000-batch email delivery investigation**
   - Current config healthy.
   - Daily Brief currently working.
   - Need better failure logging and Weekly Roundup-specific investigation.

5. **Sponsored impression bot filtering**
   - Current tracking works.
   - Later filter obvious bots/crawlers from impression counts.

6. **Dynamic affiliate product feed**
   - `/api/affiliates/public` returns zero products.
   - Authority guides are working.
   - Populate products later after checking approvals and avoiding clutter.

7. **HEAD `/api/health` cleanup**
   - Known log noise.
   - Do not patch casually due to previous duplicate-route history.

8. **Homepage crawlable links**
   - Homepage initial HTML does not expose article links server-side.
   - Consider future low-risk SEO enhancement.

9. **AI/Tech ratio**
   - Current visible pool has Tech around 8%.
   - Improve naturally with stronger practical AI/tech imports, not weak filler.

### R. Current safe project state after QA

```text
Repo clean after all changes.
Backend healthy.
Latest deployed commits:
- 1bd3307 Enforce article API limit after feed curation
- eb6f682 Restrict RSS feed to strategic public articles
Manual Review queue exists and user will decide later.
Article SEO/social sharing routes are working and should not be touched casually.
Homepage/feed is broadly aligned with strategy.
RSS no longer exposes the weak off-strategy items found during QA.
Newsletter Daily Brief is currently working; Weekly Roundup needs later investigation.
Sponsor placements are live and tracked.
Authority guides are live.
```

---

## 20. Recommended next-chat resume prompt after 1 June 2026 QA

```text
Continue Cheshire Today from the 1 June 2026 full QA update in the single chat-source master state file. First check that state file before any code/database/content-pool/category change. Workflow: one command at a time, no manual file edits unless necessary, safe terminal/script changes only, use grep not rg, verify after each step, do not use npm start unless explicitly asked. Latest deployed commits: 1bd3307 fixed /api/articles?limit=N after feed curation; eb6f682 restricted /rss.xml to strategic public articles. Royal Mail force_live was removed via admin. Article SEO/Facebook/Googlebot routes were verified and should not be changed casually. RSS is now clean. Known backlog: automatic OpenAI review before publish, high-value UK News allow-list for sitemap/RSS, admin subscriber pagination/true total, Weekly Roundup delivery/logging investigation, sponsored impression bot filtering, dynamic affiliate products, cautious HEAD /api/health cleanup, homepage crawlable links, and natural AI/Tech ratio improvement. Manual Review queue had 6 items but user chose to inspect/edit later.
```

---

## 21. 22 June 2026 — Google indexing crawl path + homepage QA/content-pool fixes

### A. Context / reason for work

User asked for a full QA after reviewing live screenshots of Cheshire Today. Visual screenshots showed the site was loading, but several quality/indexing issues were visible:

```text
- Homepage hero/top stories included older May/April items.
- Latest/homepage feed had two very similar Starmer stories.
- Homepage felt too national-heavy in places.
- Google indexing concern remained because raw React homepage/category HTML does not expose article links to non-JS crawlers.
```

Before making changes, the existing state-file history was checked. Previous warnings remained valid:

```text
- Do not reintroduce full content into homepage candidate projections.
- Do not massively increase homepage/API candidate-pool multipliers.
- Keep /api/articles lightweight because a previous /api/articles?limit=80 issue took roughly 48–51 seconds before the old performance fix.
- Keep the final API limit cap because earlier force_live prepending caused /api/articles?limit=10 to return more than requested.
```

### B. Google crawl/indexing diagnosis

Checks performed:

```text
robots.txt: OK — allows Googlebot and lists sitemap.xml/news-sitemap.xml.
sitemap.xml: live and reachable.
news-sitemap.xml: live and reachable.
Sample article Googlebot HTML: OK — title/canonical/no noindex looked correct.
Sitemap URLs tested: first batch returned HTTP 200.
Raw homepage/category HTML: React shell only; no visible /article/ links for non-JS crawlers.
```

Diagnosis:

```text
Not a robots/noindex/canonical failure.
Likely crawl discovery weakness caused by React-shell homepage/category HTML plus selective sitemap/feed constraints.
```

### C. Crawl hub added for Google/non-JS discovery

Commit:

```text
398be93 Add latest articles crawl path for indexing
```

Changes:

```text
- Added a plain HTML latest-articles route in backend/server.py.
- Route returns latest public article links grouped by category.
- Includes normal article hrefs like https://cheshiretoday.co.uk/article/<id>/<slug>.
- Uses simple HTML, meta robots index/follow, canonical, and cache-control.
- Added the crawl hub to sitemap.xml.
```

Verification:

```text
/sitemap.xml contained /latest-articles.
Cache-busted /latest-articles?v=398be93 returned correct plain HTML with article links.
Clean /latest-articles initially returned old React shell due cached path.
```

### D. Switched sitemap crawl hub to fresh /article-index path

Because the clean `/latest-articles` path had a cached SPA shell response, a fresh uncached route was added and submitted in sitemap instead.

Commit:

```text
2218069 Switch indexing crawl path to article index
```

Changes:

```text
- Added @app.get('/article-index') on the same plain HTML crawl route.
- Kept /latest-articles route for compatibility.
- Changed canonical to https://cheshiretoday.co.uk/article-index.
- Changed sitemap.xml to submit https://cheshiretoday.co.uk/article-index instead of /latest-articles.
```

Verification:

```text
curl https://cheshiretoday.co.uk/sitemap.xml | grep 'article-index\|latest-articles'
returned:
10:    <loc>https://cheshiretoday.co.uk/article-index</loc>
```

SEO follow-up:

```text
Submit/resubmit sitemap.xml in Search Console.
Inspect/request indexing for /article-index, homepage, and a few strong recent local/business articles.
Do not expect immediate indexing; monitor after 48–72 hours.
```

### E. Homepage/API QA baseline from screenshots and live checks

Initial public API check:

```text
/api/articles?limit=80 returned only 20 in first test.
No missing images found in that public result.
Two near-duplicate Starmer stories appeared.
Old May/April local items were visible.
```

Admin/all-article checks:

```text
/api/articles?limit=200&include_archived=true returned 200 sample items.
Admin counts:
  total: 3089
  visible: 105
  archived: 2984
  visible_featured: 5
  visible_priority: 0
```

With proper public `with_total=true` check before fixes:

```text
Time: about 1.62s
/api/articles?limit=80&with_total=true
COUNT: 24
TOTAL: 53
LIMIT: 80
CATEGORIES: Finance 5, UK News 10, Local News 7, Business 2
```

Interpretation:

```text
The endpoint was fast, but homepage curation was very restrictive.
Public pool existed but was thin after filters/manual-review.
Old May/April local stories appeared because only a few fresh public Local News articles existed.
```

### F. Local homepage editorial filter relaxed safely

Commit:

```text
49a1296 Relax local homepage editorial filter
```

Reason:

```text
The public feed applied the same heavy editorial noise filter to Local News and UK/national items.
This was suspected to starve Local News unnecessarily.
```

Change:

```text
- Added is_local_editorial_noise() as a lighter local-only homepage filter.
- Local filter now removes obvious media-format filler only: podcast/audio/video/watch/gallery/in-pictures/letters/cartoon/opinion/editorial.
- UK/national items still use the stronger existing editorial noise filter.
```

Safety:

```text
- No database query-size change.
- No content projection reintroduced.
- No candidate-pool multiplier increase.
- Final unique_articles[:limit] cap preserved.
```

Result after deploy:

```text
COUNT stayed 24; TOTAL stayed 53.
Conclusion: this filter was not the main bottleneck, but the change remains safe and appropriate.
```

### G. Manual-review/import-cap bottleneck identified

Admin article QA with fresh admin token showed:

```text
ADMIN TOTAL: 3089
Newest 80 admin articles:
  hidden/manual_review_hidden_from_public=True: 32
  public-visible hidden=None: 48
  categories: UK News 38, Tech 22, Business 8, Local News 7, Finance 5
```

Newest Local News in admin newest 80:

```text
1. public — Cheshire holiday park unveils plans for more lodges
2. hidden — Meet the brothers who turned derelict Cheshire boozer into high-end gastropub
3. public — Warrington department store Hancock & Wood to close after 112 years
4. public — Cheshire GP surgery with more than 8,400 patients could be on the move
5. hidden — Cheshire homes plan appeal dismissed by inspector
6. hidden — Take up vaccines plea from Cheshire West and Chester health boss
7. hidden — New cancer centre to improve care at Countess of Chester Hospital
```

Hidden Local News reasons/content lengths:

```text
- Gastropub: failed useful-local relevance gate before AI rewrite, content_len 30.
- Homes appeal: missing specific town/village/street/venue/council area/named site, content_len 64.
- Vaccines: public import cap reached, content_len 158.
- Cancer centre: public import cap reached, content_len 98.
```

Conclusion:

```text
Do NOT bulk-unhide these items. Several are short RSS snippets and would be bad for readers/Google if published as-is.
Root issue is that the scheduled import public cap was too thin, causing potentially useful local candidates to go into manual review before rewrite/publication.
```

### H. Scheduled public import cap raised from 4 to 6

Commit:

```text
c5475ee Raise scheduled public import cap
```

Previous scheduler setup:

```text
daily_article_generation(count=12)
Runs at 06:00, 12:00, 18:00 Europe/London.
Each run requested up to 12 candidates but used public_import_limit=4.
Max public articles/day before: 4 × 3 = 12.
```

Change:

```text
public_import_limit=4 -> public_import_limit=6
Max public articles/day after: 6 × 3 = 18.
```

Reason:

```text
Controlled increase to reduce homepage starvation while keeping manual review and cost/quality controls.
```

Safety:

```text
No automatic unhide.
No query-size change.
No full content projection change.
No removal of manual-review safeguards.
```

### I. One controlled manual import run after cap change

A single controlled import was run using:

```text
POST /api/generate-articles
payload: {"count":12,"include_uk_news":true,"public_import_limit":6}
```

Result:

```text
success: true
generated: 12
cheshire_articles: 7
uk_articles: 3
```

Admin check after manual import:

```text
Returned newest 30:
hidden=None: 21
hidden=True: 9
Local/full public examples included:
- Family lose much of their belongings in 'devastating' fire hours after moving in — len 2068
- Report on Nottingham NHS maternity scandal... — len 2686
- Brexit: how it has hit your wallet... — len 2928
- Gen Z earning more than millennials... — len 3606
```

One hidden full-length Local News item inspected:

```text
Title: How a Cheshire mum is giving back to hospital that saved her twin boys
hidden=True
reason: vague Cheshire wording without specific town/village/street/venue/council area/named site
content_len: 2319
```

Content inspection showed it repeatedly used vague terms:

```text
"a Cheshire mum", "the hospital", "the unit", "the hospital team", "specialist maternity and neonatal staff"
```

Decision:

```text
Leave hidden unless manually rewritten with a verified named local anchor. The location guard was correct here.
```

Public feed after manual import:

```text
Time: about 1.23s
COUNT: 25
TOTAL: 56
CATEGORIES: Finance 6, Local News 9, UK News 8, Business 2
Fresh local stories added near top:
- Anderton Boat Lift closure in focus as waterways charity hits 80-year milestone
- Family lose much of their belongings in 'devastating' fire hours after moving in
```

### J. Similar-title homepage dedupe added and tuned

Problem:

```text
Two Starmer near-duplicates appeared together:
- Keir Starmer expected to announce departure as prime minister on Monday
- Starmer expected to announce departure on Monday as growing numbers of MPs back Burnham for PM – UK politics live
```

Commit:

```text
d9e0b2d Deduplicate similar homepage titles
```

Change:

```text
- Added lightweight title-keyword near-duplicate detection in public /api/articles feed.
- Exact ID dedupe preserved.
- Similar-title dedupe only affects public feed output, not imports/admin/article detail pages.
- No DB query-size or content projection changes.
```

Initial threshold `> 0.55` did not catch the Starmer pair because similarity was about 0.50.

Follow-up commit:

```text
5a3cb1f Tighten homepage title dedupe threshold
```

Change:

```text
similarity > 0.55 -> similarity >= 0.50
```

Final verification:

```text
Time: about 1.22s
COUNT: 24
TOTAL: 56
CATEGORIES: Finance 6, Local News 9, UK News 7, Business 2
Starmer check: only one Starmer story remained.
```

### K. Final live QA status after 22 June work

```text
✅ Working tree clean.
✅ Latest branch: full-scrape-prod.
✅ Latest pushed/deployed commit checked: 5a3cb1f Tighten homepage title dedupe threshold.
✅ /article-index is in sitemap for Google crawl discovery.
✅ /article-index avoids the cached /latest-articles SPA-shell issue.
✅ API speed remained good (~1.1–1.6s during tests).
✅ Similar Starmer duplicate fixed in homepage/public feed.
✅ Scheduled public import cap raised from 4 to 6.
✅ Controlled manual import confirmed full-length public articles can be generated.
✅ Manual-review guard correctly kept vague/no-local-anchor article hidden.
⚠️ Homepage curated count remains low: 24 from 56 public-visible articles after filters/dedupe.
⚠️ Old May/April local stories still appear until enough fresh public local articles build up through scheduled runs/manual editorial publishing.
```

Latest commits at end of work:

```text
5a3cb1f Tighten homepage title dedupe threshold
d9e0b2d Deduplicate similar homepage titles
c5475ee Raise scheduled public import cap
49a1296 Relax local homepage editorial filter
2218069 Switch indexing crawl path to article index
398be93 Add latest articles crawl path for indexing
```

### L. Important follow-ups

1. **Monitor next scheduled imports**

```text
After the next 06:00 / 12:00 / 18:00 UK-time run, check:
/api/articles?limit=80&with_total=true
/api/admin/articles?limit=80
```

Goal:

```text
More public Local News.
Fewer useful local items stuck as short/manual-review due cap.
Homepage old May/April items pushed lower/out of first page.
API still around 1–3 seconds.
```

2. **Do not bulk-unhide manual review articles**

```text
Many hidden items are short snippets or have weak/vague local anchors.
Unhide only after manual rewrite/verification and specific place/site confirmation.
```

3. **Manual-review queue may need an editorial workflow**

Suggested later workflow:

```text
List newest hidden Local News -> choose 2–4 strong candidates -> verify source/place -> rewrite to full local-news style -> publish manually.
```

4. **Security follow-up**

```text
/api/generate-articles appears publicly callable without admin auth.
This was used once for controlled manual import.
Later fix should add admin auth or otherwise restrict this endpoint, after checking state/history to avoid breaking scheduler/internal calls.
```

5. **Search Console follow-up**

```text
Resubmit sitemap.xml.
Inspect/request indexing for /article-index.
Request indexing for homepage and 3 strong recent articles.
Monitor 48–72 hours.
```

6. **Homepage crawlability follow-up**

```text
/article-index is now the low-risk crawl hub.
Later consider limited server-side homepage article links, but do not do this casually because frontend/backend routing and caching need careful testing.
```

7. **Homepage count remains low by design/filtering**

```text
Current low count is not a speed failure.
It is caused by strict public/manual-review/homepage filters plus thin fresh Local News supply.
Let scheduled imports run with new cap before adding more code changes.
```

### M. Resume prompt for next chat after 22 June 2026 work

```text
Continue Cheshire Today from the 22 June 2026 QA/update section in the single chat-source master state file. First check that state file before any code/database/content-pool/category/indexing change. Workflow: one command at a time, safe terminal/script changes, use grep not rg, verify after each step, no dev server unless asked. Latest key commits: 398be93 added /latest-articles crawl hub; 2218069 switched sitemap/canonical to /article-index; 49a1296 relaxed local homepage editorial filter; c5475ee raised scheduled public import cap from 4 to 6; d9e0b2d added public-feed similar-title dedupe; 5a3cb1f tightened dedupe threshold and fixed duplicate Starmer homepage story. Current QA: API speed good (~1.2s), homepage count 24 from total 56 after filters, old May/April local stories still appear until more fresh public local articles build up. Do not bulk-unhide manual review articles; many are short snippets or vague local-anchor rewrites. Follow-ups: monitor next scheduled imports, inspect admin hidden Local News, secure /api/generate-articles with admin auth later, resubmit sitemap and inspect /article-index in Search Console.
```

---

## 26 June 2026 — admin rewrite, indexing, newsletter, article UX and cleanup update

### A. Source-of-truth reminder reinforced

Use this chat-source state file as the first checkpoint before future Cheshire Today code/database/content-pool/category/indexing changes.

Priority order remains:

```text
1. Latest chat-source state file
2. Current repo code
3. Live website/API checks
4. Recent commits/terminal verification
5. Cheshire Economic & AI Project Master only for high-level strategy
```

Do not rely only on the Cheshire Economic & AI Project Master document because it can be behind the live project state.

### B. OpenAI manual-review rewrite draft flow completed

User wanted the admin Manual Review **Open AI** button to use OpenAI, create a rewrite draft, open the editor, and let the user manually review/update/publish. It should not auto-publish or silently change database content.

Implemented backend helper and endpoint:

```text
run_openai_article_rewrite_draft(article: dict) -> dict
POST /api/admin/articles/{article_id}/openai-rewrite-draft
```

Behaviour:

```text
Uses OPENAI_API_KEY.
Uses OPENAI_REWRITE_MODEL if set, otherwise OPENAI_REVIEW_MODEL / gpt-4o-mini fallback.
Returns draft title, summary, content, category, editor_notes and model.
Does not save, publish, unhide, archive, force live, or update DB.
Keeps user in manual editorial control.
```

Frontend changes in `frontend/src/components/AdminDashboard.jsx`:

```text
Added handleOpenAIRewriteDraft(article).
Calls /api/admin/articles/{id}/openai-rewrite-draft.
Fills the existing article edit form with draft values.
Opens the existing editor dialog with setShowAddArticle(true).
Preserves image/source/tags/scope where appropriate.
Manual Update Article button remains required.
Manual Review Open AI button now calls this draft flow instead of the old AI review/risk endpoint.
```

Safety/testing completed:

```text
python3 -m py_compile backend/server.py
git diff --check
frontend npm build passed
```

Commit pushed:

```text
ad131c7 Add OpenAI admin rewrite draft flow
```

Live endpoint test completed on Manual Review article:

```text
Article ID: 6a38e3e13e01125014bd1dff
Original title: How a Cheshire mum is giving back to hospital that saved her twin boys
Endpoint returned success.
Generated draft title: Cheshire Mother Supports Hospital After Care for Her Twin Boys
Draft content length: 2189
```

User confirmed the admin button works.

Important editorial note:

```text
If source content is vague, the OpenAI prompt is told not to invent details, so some drafts may remain cautious/vague.
Manual review is still required.
```

### C. Google Search Console / article index checks

User shared Search Console screenshots showing a very small indexed count compared with many not-indexed URLs. The issue included many `Crawled - currently not indexed` URLs and `/article-index` previously showing no referring sitemap / older crawl history.

Live checks confirmed:

```text
/sitemap.xml includes https://cheshiretoday.co.uk/article-index with lastmod 2026-06-26.
/article-index returns plain crawlable HTML.
/article-index has index,follow meta.
/article-index has canonical /article-index.
/article-index includes visible article links by category.
```

Conclusion at the time:

```text
Current live implementation looked correct.
Search Console likely lagging behind current sitemap/page state.
```

User actions completed:

```text
Clicked TEST LIVE URL / request indexing for article index.
Resubmitted sitemap.
Requested indexing on stronger article URLs.
```

Follow-up:

```text
Check again after Google recrawls.
Do not assume the main GSC report updates immediately; it can lag behind live inspection results.
```

### D. Newsletter / email digest health check

User asked to check email digest after more than three weeks and asked to check state first.

State/context confirmed:

```text
Newsletter was previously moved from Office 365 SMTP to Resend.
Daily Brief and Weekly Roundup use Resend batch sending.
Per-recipient open/click tracking was added and verified.
Old cold-candidate lists must not be trusted.
After enough tracked sends, deactivate only proven cold subscribers; never hard-delete by default.
Protected/priority/organic emails must be excluded from cold cleanup.
```

Token expired during checks and was regenerated with:

```text
TOKEN_LENGTH=43
```

Live analytics endpoint checked:

```text
GET /api/admin/email-analytics?days=30
```

Returned around:

```text
total_emails_sent: 31,000
total_opens: 9,380
total_clicks: 9,121
unique_openers: 7,715
unique_clickers: 1,338
open_rate: 24.9%
click_rate: 4.3%
click_to_open_rate: 17.3%
DailyBrief sent: 27,000, success: 24,900
WeeklyRoundup sent: 4,000, success: 3,000
Recent Daily Brief sends: 1000/day
Recent Weekly Roundup sends: 1000
```

Code inspection found:

```text
Manual /api/send-digest still uses unique_emails[:daily_send_cap], i.e. first 1000 only. This manual endpoint is not ideal for proving rotation.
Scheduled send_scheduled_news_digest uses rotating logic via _select_rotating_email_batch.
```

Daily scheduled behaviour:

```text
Priority website/organic subscribers first.
Rotating imported emails after priority.
DAILY_BRIEF_SEND_CAP default 1000.
Cursor fields are logged in digest_log.
```

Digest log examples showed Daily Brief cursor moving and wrapping:

```text
2026-06-25 planned_start about 13228
planned_next about 70
planned_total about 14158
Recent daily success around 1000/1000.
```

Weekly Roundup behaviour:

```text
Sends to priority organic plus recently engaged imported readers.
Uses opens/clicks in last 60 days.
Uses per-recipient hashed tracking IDs.
Uses multi-batch Sunday delivery by roundup_batch_slot.
No wraparound in the same way as Daily Brief.
Digest logs did not include the same planned_start/planned_next/total fields.
```

Per-recipient tracking in `backend/app/email_service.py`:

```text
_recipient_tracking_id(base_tracking_id, email) appends first 8 chars of SHA256 of normalized email.
Daily and Weekly replace campaign tracking ID with per-recipient ID in HTML, tracking pixel and links.
```

### E. Cold subscriber report endpoint added as dry-run only

Added read-only dry-run endpoint:

```text
GET /api/admin/subscribers/cold-report?days=30&recent_days=21&sample_limit=20
```

Purpose:

```text
Report likely cold candidates without deactivating/deleting anyone.
Exclude protected/priority/organic/recent subscribers.
Avoid unsafe bulk cleanup.
```

Criteria:

```text
active/daily enabled
deliverable
not organic/website/priority/protected domain
not recently subscribed
no opens/clicks inside window
```

Commit pushed:

```text
b2b91e9 Add dry-run cold subscriber report
```

Live cold report result:

```text
active_daily_unique: 14157
invalid_excluded: 0
protected_or_organic_excluded: 4
recent_subscribers_excluded: 0
engaged_hashes: 3573
tracked_hashes: 3573
cold_candidates_total: 10660
cold_candidates_with_tracking_but_no_engagement: 0
cold_candidates_with_no_recent_tracking_seen: 10660
```

Critical conclusion:

```text
Do NOT deactivate anyone yet.
0 subscribers are proven cold by tracking.
10,660 candidates had no recent tracking record seen, which means they may not yet have had a tracked opportunity recorded.
Current system records opens/clicks, not a full send-recipient delivery ledger.
```

Future safe build:

```text
Add newsletter recipient delivery ledger first.
Record email_hash, digest type, tracking id, sent_at, success/failure.
Wait at least one full rotation.
Then run cold cleanup only on subscribers with proven delivery opportunities and no engagement.
```

### F. Article intro / image layout fix

User showed article page where the visible intro above the image was clipped mid-sentence. This affected manually edited articles or at least some article summaries.

Relevant code in `frontend/src/pages/ArticlePageV2.jsx`:

```text
buildDescription(article) was used for visible intro and clipped to about 200 chars, causing awkward mid-sentence display.
Full article body already had articleBodyRef below the image.
Mobile had a separate Read more flow, but desktop/tablet visible intro did not.
```

Implemented:

```text
Added buildVisibleIntro(article).
Visible intro now tries to use the first complete sentence when reasonable.
Falls back to cleaner clipped text with ellipsis.
Kept buildDescription for SEO/meta use.
Added visibleIntro useMemo.
Replaced desktop visible description block with visibleIntro.
Added a professional Continue reading ↓ text link above the image.
Continue reading scrolls toward the article body below the image with offset.
```

Testing:

```text
git diff --check passed.
frontend npm build passed.
Local article page tested on localhost.
```

Commits pushed:

```text
1d762b1 Improve article intro read more flow
87b9bb4 Refine article guide wording and continue reading link
```

Final behaviour:

```text
Top intro should no longer look awkwardly cut.
Continue reading ↓ appears as subtle editorial text link, not an advert-style button.
Clicking it should land at/near the start of article text below the image.
```

### G. Article guide wording softened

User identified guide promo wording as too advertorial:

```text
What this means for your household
Best options based on this story
Practical next steps, comparisons and tools...
```

Changed in `frontend/src/pages/ArticlePageV2.jsx` to softer publisher-style wording:

```text
Related business guides
Related money guides
Related reader guides
Related technology guides
Related guides
Useful guides
Further reading and practical resources linked to this topic.
```

This keeps internal guide/affiliate pathway cleaner and less intrusive.

### H. Article guide heading link fixed

User noted:

```text
RELATED READER GUIDES
Useful guides
Further reading and practical resources linked to this topic.
```

The title was not clickable, so it felt unfinished.

Initial attempted fix made `Useful guides` / `View all →` link to `/guides`, but testing showed `/guides` was not a real frontend route and fell back to homepage.

Repo checks showed many valid guide detail URLs such as:

```text
/guides/council-tax-bands-cheshire
/guides/best-domain-registrars-small-business-uk
/guides/best-website-builders-small-business-uk
/guides/best-accounting-software-uk
/guides/best-mortgage-rates-uk
```

but no working `/guides` index route.

Implemented safer fix:

```text
Added getPrimaryGuideHref(guides, pillarLabel, contextToolType).
Uses pickGuidesForPillar to select relevant guides already chosen for that article.
Links heading to the first selected real guide slug: /guides/<slug>.
If no guide exists, heading falls back to non-clickable text.
Changed secondary link text from View all → to Open guide →.
```

Important bug caught before/around testing:

```text
primaryGuideHref was initially created before pillarLabel/contextToolType existed.
This caused blank article pages on localhost.
The hook was moved after pillarLabel and contextToolType creation.
```

Testing:

```text
git diff --check passed.
frontend npm build passed.
Local article page was checked after the blank-page issue.
```

Commit pushed:

```text
e1fdbe6 Link article guide heading to relevant guide
```

Final expected behaviour:

```text
Article page should not go blank.
Useful guides / Open guide → should point to a real /guides/<slug> URL.
It should not send readers to homepage via broken /guides route.
```

### I. Sponsored/empty article removed from public view

User spotted live article:

```text
Title: Recovery has to keep up with AI
Date shown: Thursday, 25 June 2026 at 15:00
Visible intro: SPONSORED POST: Why an AI-era recovery architecture looks different, with Eon's Gonen Stein...
```

Live API check:

```text
/api/articles?limit=80
```

Confirmed article data:

```text
ID: 6a3d5ef0323e96d2ddee7115
TITLE: Recovery has to keep up with AI
SOURCE: The Register
CATEGORY: Tech
SUMMARY: SPONSORED POST: Why an AI-era recovery architecture looks different, with Eon's Gonen Stein
CONTENT_START: empty
```

Decision:

```text
Do not add code guard in this moment because user said we only need to remove that article.
Article should not stay public because it is source-sponsored, body is empty, and it weakens editorial trust.
```

Archive attempt initially failed due expired admin token:

```text
{"detail":"Invalid or expired token"}
```

After token issue was handled, public confirmation check returned:

```text
found_public: 0
```

Result:

```text
The sponsored/empty article is no longer in the public article feed.
```

Future optional follow-up, not completed in this update:

```text
Consider a controlled sponsored/advertorial skip guard later after checking state/history.
Potential phrases: SPONSORED POST, sponsored content, advertorial, paid partnership, promoted by, partner content.
Only do this later if user asks or if more examples appear.
```

### J. Commits from this update window

```text
ad131c7 Add OpenAI admin rewrite draft flow
b2b91e9 Add dry-run cold subscriber report
1d762b1 Improve article intro read more flow
87b9bb4 Refine article guide wording and continue reading link
e1fdbe6 Link article guide heading to relevant guide
```

### K. Current follow-ups after this update

1. **Check live deploy after latest frontend commits**

```text
/api/health returned healthy after earlier deploys.
After the latest commit, check again once Render deploy completes.
Open a live article and test:
- intro above image
- Continue reading ↓ scroll target
- Useful guides / Open guide → link target
```

2. **Do not use broken /guides route**

```text
There is no confirmed working /guides index route.
Do not link article blocks to /guides unless a real route/page is added and tested.
Use /guides/<slug> for known guide detail pages.
```

3. **Newsletter cleanup remains blocked until delivery ledger exists**

```text
Do not deactivate the 10,660 cold candidates from dry-run.
They are not proven cold because there is no send-recipient delivery ledger.
```

4. **Sponsored/empty article handling**

```text
The single known sponsored/empty article was removed from public view.
A future guard may be useful but was not added because user asked only to remove the article.
```

5. **OpenAI rewrite flow is draft-only**

```text
Keep this behaviour.
Do not make it auto-publish.
Manual editor review remains required.
```

### L. Resume prompt for next chat after 26 June 2026 update

```text
Continue Cheshire Today from the 26 June 2026 update section in the single chat-source master state file. First check that state file before any code/database/content-pool/category/indexing change. Workflow: one command at a time, safe terminal/script changes, use grep not rg, verify after each step, no dev server unless asked. Latest key changes: OpenAI Manual Review rewrite draft flow added and pushed (ad131c7); dry-run cold subscriber report added (b2b91e9) but no cleanup allowed yet; article intro now uses visibleIntro plus Continue reading ↓ (1d762b1/87b9bb4); article guide wording softened and guide heading links now point to a real relevant /guides/<slug> not broken /guides (e1fdbe6). One sponsored/empty article from The Register, ID 6a3d5ef0323e96d2ddee7115, was removed from public view and confirmed found_public: 0. Follow-ups: check live deploy/article UX, do not link to /guides unless a real index route is built, do not deactivate newsletter subscribers until recipient delivery ledger exists, and keep OpenAI rewrite as draft-only/manual-review.
```

---

## 2026-07-07 Current chat update — article UX, Daily Brief diagnostics, affiliate guides and house-guide ad rotation

### A. Operational reminder reinforced in this chat

Use this latest chat-source state file as the operational source of truth before any Cheshire Today code, database, content-pool, category, newsletter, indexing, advertising, affiliate or guide changes.

Do **not** treat `Cheshire_Economic_AI_Project_Master_Feb2026.pdf` as the updated project state. It can still be used for high-level strategy only if explicitly requested, but not as the current implementation/source-of-truth file.

### B. Article page intro, Continue reading and guide-link UX work completed

File changed during this chat:

```text
frontend/src/pages/ArticlePageV2.jsx
```

Implemented/refined:

1. Added visible article intro logic and a cleaner `Continue reading ↓` flow.
2. Added scroll handling to continue into the article body rather than leaving the reader at the top teaser.
3. Changed guide wording to cleaner local-reader language:

```text
Related reader/business/money/technology guides
Useful guides
```

4. Made the useful-guide heading/link point to a real guide URL instead of generic `/guides`.
5. Added `getPrimaryGuideHref(guides, pillarLabel, contextToolType)` and `primaryGuideHref`.
6. Fixed hook ordering after `primaryGuideHref` was initially placed before `pillarLabel` / `contextToolType`.
7. Added `articleBodyContent` so the intro flows into the full article body instead of being disconnected:

```js
const articleBodyContent = useMemo(() => {
  const intro = safeText(visibleIntro).trim();
  const body = String(mainContent || "").trim();
  if (!intro) return body;
  if (!body) return intro;
  // If body already contains the intro, avoid duplication.
  return `${intro}\n\n${body}`;
}, [visibleIntro, mainContent]);
```

Render changed from:

```text
autoLinkContent(mainContent, pillarLabel)
```

to:

```text
autoLinkContent(articleBodyContent, pillarLabel)
```

Relevant commits pushed:

```text
1d762b1 Improve article intro read more flow
87b9bb4 Refine article guide wording and continue reading link
c619083 Make article guide headings clickable
e1fdbe6 Link article guide heading to relevant guide
eba2db9 Continue article intro into body
```

### C. Bad/empty public article cleanup completed

Archived via admin API after confirming the issue was bad imported content/database data, not the Continue reading UI:

```text
6a3d5ef0323e96d2ddee7115
The Register sponsored/empty article: “Recovery has to keep up with AI”

6a3f58d856f9e351dd0138f8
Guardian tax article with empty/poor content

6a3e0767273dcfa98b520874
Guardian tax article with empty/poor content
```

### D. Cookie/banner review completed

Read-only grep found no obvious public analytics/ad pixel scripts currently active:

```text
No GA/GTM/Meta Pixel/AdSense/DoubleClick public scripts found.
Public localStorage currently includes dark mode / recent searches.
Admin token localStorage exists for admin use.
Existing routes: /privacy, /cookies, /terms and footer links.
```

Current recommendation:

```text
No cookie banner is needed immediately while no tracking/ad/affiliate pixels are active.
Add consent before adding analytics pixels, ad network scripts, remarketing pixels or similar tracking.
```

### E. Git author note

Observed wrong author email in earlier commits:

```text
julian07891@yahoo.com.uk
```

Likely correct email:

```text
julian07891@yahoo.co.uk
```

Suggested local config if not already done:

```bash
/usr/bin/git config user.name "Iulian Dumitrascu"
/usr/bin/git config user.email "julian07891@yahoo.co.uk"
```

Do not rewrite already pushed history unless there is a specific reason.

### F. Daily Brief / newsletter failure diagnostics and patch completed

Issue found:

```text
Daily Brief logs showed large selected counts, e.g. 1000, but success_count/delivered was 0.
Old logging could still mark these as "sent", causing misleading reporting.
```

Files changed:

```text
backend/app/email_service.py
backend/server.py
```

Added/changed:

1. Reset Resend send diagnostics at start of `send_daily_brief`:

```text
resend_last_error
resend_last_successful_chunks
resend_last_failed_chunks
```

2. Increment chunk success/fail counters in `_send_resend_batch`.
3. Store detailed `resend_last_error` including chunk, HTTP status, subject, first domain and response.
4. In `send_scheduled_news_digest`, if `success_count <= 0`, final digest log status becomes:

```text
failed
```

not `sent`.

5. Store provider diagnostics on digest logs:

```text
provider
provider_error
resend_successful_chunks
resend_failed_chunks
```

Commit pushed:

```text
5c31603 Mark zero-success Daily Brief sends as failed
```

Next-day log confirmed true cause:

```text
status: failed
success_count: 0
provider: resend
resend_failed_chunks: 10
provider_error: 401 Unauthorized ... {"message":"API key is invalid"}
```

Conclusion:

```text
Render environment had a RESEND_API_KEY value, but the key currently loaded by backend was invalid/revoked/wrong.
The issue was not caused by article/front-end changes. A deploy/restart likely caused backend to load the current invalid Render env value.
```

Added Resend validation endpoint:

```text
GET /api/admin/email-config/validate-resend
```

Purpose:

```text
Validate the configured Resend API key against Resend /domains without exposing the secret.
Returns key_exists, length, starts/ends, fingerprint, valid, resend_status and response.
```

Commit pushed:

```text
276f7ff Add Resend API key validation endpoint
```

Use for checking:

```bash
/usr/bin/curl -sS \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  'https://cheshiretoday.co.uk/api/admin/email-config/validate-resend'
```

Expected if fixed:

```text
valid: true
resend_status: 200
```

If still `401`, replace Render `RESEND_API_KEY`.

### G. Import/article quality investigation completed — do not assume code changed

User noticed several weak or unsuitable imports were public or had not gone to manual review. Examples discussed:

```text
London lost catastrophic 89% car club access / Zipcar-style story
Burnham/tax/cost-of-living national politics story
NHS walking scheme
The Register tech/startup/datacentre stories
Chester great-great-grandad story with suspicious non-UK location drift
Wilmslow Library / local grants items
```

Git log check since 30 June showed no relevant recent import/rewrite/manual-review logic changes. Recent commits at that point were only:

```text
276f7ff Add Resend API key validation endpoint
3a55b5e Noindex archived article pages
a2ef26f Serve crawlable HTML for public hub pages
```

Conclusion:

```text
The import rules did not recently change.
Today’s RSS/source mix exposed existing weaknesses in the current import/manual-review gates.
```

Important technical findings:

1. `/api/articles?limit=180` list endpoint does not return full article body in normal list mode, so initial `content_len: 0` from that endpoint was misleading.
2. Single-article/admin checks showed some public items had full content, while others were genuinely thin.
3. Existing bug/gap found in `backend/server.py`:

```python
manual_review_without_ai = (public_import_limit is not None and public_imported >= public_import_limit) or not ai_budget_available(0.05)

if not manual_review_without_ai and len((detailed_content or "").strip()) < 1000:
    ...
```

Because the short-content gate is conditional on `not manual_review_without_ai`, a fallback/manual-review-without-AI path can allow thin RSS content to go public before the public cap applies.

4. Scheduled import currently uses:

```python
await generate_articles(GenerateArticlesRequest(count=count, include_uk_news=True, public_import_limit=6))
```

5. `ai_budget_available` default is roughly:

```text
PERPLEXITY_DAILY_BUDGET_GBP=0.70
cost estimate about 0.05/call
roughly 14 calls/day
```

If the AI budget is considered used, later scheduled runs can still publish up to 6 thin RSS items because `public_import_limit` resets per run while the AI budget is daily.

6. `apply_ai_manual_review_guard` / `find_ai_manual_review_hits` mainly catches AI/internal residue and marks articles as:

```text
verification_status = ai_rewrite_auto_screened
rewrite_status = ai_rewritten
```

if residue is not found. It does **not** currently check:

```text
editorial fit
London-only/national-politics fit
factual drift
unsupported details
weak Cheshire/business relevance
```

Observed metadata examples:

```text
London Zipcar/car clubs article:
content_len about 581, no verification/rewrite/manual_review flags, public.

Burnham/tax article:
content_len about 11859, verification_status ai_rewrite_auto_screened, rewrite_status ai_rewritten, public despite weak fit.

Startup/Palo Alto/Koi article:
content_len about 2119, auto-screened/ai_rewritten, strategically AI but weak Cheshire/business-local fit unless manual reviewed.

Chester great-great-grandad article:
content_len about 4402, auto-screened/ai_rewritten, suspicious location/source drift.

NHS walking scheme:
content_len about 3287, auto-screened/ai_rewritten, generic UK public-service item.

Wilmslow Library:
content_len about 2428, local, no verification/rewrite status but acceptable local direction.
```

Important conclusion for future import fixes:

```text
Imports have not recently changed.
Existing rules are insufficient:
1. short RSS fallback can go public below 1000 chars,
2. some public articles have no rewrite_status/verification_status,
3. AI-rewritten articles can be auto-approved even when weak-fit or factually questionable,
4. a final post-rewrite editorial strategy/source-fit gate is missing.
```

Do not patch casually without first checking this state and prior import history.

### H. Affiliate guide work completed through live authority-page API

User had new affiliate approvals:

```text
BrickZoneHub via Awin, merchant ID 121692
EMPLA via Awin, merchant ID 127533
Alison Free Learning via Awin, merchant ID 120101
```

Awin tracking links used:

```text
BrickZoneHub:
https://www.awin1.com/cread.php?awinmid=121692&awinaffid=2844510&clickref=ct_guides&ued=https%3A%2F%2Fbrickzonehub.co.uk%2F

EMPLA:
https://www.awin1.com/cread.php?awinmid=127533&awinaffid=2844510&campaign=Shopify+App+Store+-+Ops+Mgr&clickref=ct_guides&ued=https%3A%2F%2Fempla.io%2Fai-employees%2Fexecutive-assistant

Alison:
https://www.awin1.com/cread.php?awinmid=120101&awinaffid=2844510&clickref=ct_guides&ued=https%3A%2F%2Falison.com%2F
```

Current authority pages were listed: 35 pages, including:

```text
best-ai-productivity-tools-uk
best-ai-tools-uk
best-online-gcse-a-level-courses-uk
best-web-hosting-small-business-uk
best-website-builders-small-business-uk
best-business-bank-accounts-uk
best-accounting-software-uk
best-iso-training-certification-courses-uk-businesses
...
```

Inspection showed:

```text
best-ai-productivity-tools-uk:
ChatGPT, Claude, Notion AI, Grammarly, Jasper, Midjourney
No EMPLA initially.

best-ai-tools-uk:
ChatGPT, Claude, Gemini, Midjourney
No EMPLA initially.

best-online-gcse-a-level-courses-uk:
CloudLearn linked via Awin.
No Alison initially.
```

Actions completed via `/api/admin/authority-pages/upsert`:

1. Added `EMPLA AI Employees` to:

```text
/guides/best-ai-productivity-tools-uk
status: published
```

Stored link:

```text
https://www.awin1.com/cread.php?awinmid=127533&awinaffid=2844510&campaign=Shopify+App+Store+-+Ops+Mgr&clickref=ct_guides&ued=https%3A%2F%2Fempla.io%2Fai-employees%2Fexecutive-assistant
```

2. Added `Alison Free Online Courses` to:

```text
/guides/best-online-gcse-a-level-courses-uk
status: published
```

Stored link:

```text
https://www.awin1.com/cread.php?awinmid=120101&awinaffid=2844510&clickref=ct_guides&ued=https%3A%2F%2Falison.com%2F
```

3. Created draft BrickZoneHub guide:

```text
slug: best-building-renovation-supplies-uk
title: Best building and renovation supplies in the UK (2026): materials, tools and project essentials
category: Finance
status: draft
tool: BrickZoneHub
```

Stored link:

```text
https://www.awin1.com/cread.php?awinmid=121692&awinaffid=2844510&clickref=ct_guides&ued=https%3A%2F%2Fbrickzonehub.co.uk%2F
```

Important note:

```text
These authority-guide changes were made through the live admin API/database, not code changes. There is nothing to commit for the authority-page DB updates.
```

### I. Authority page display behaviour confirmed

Frontend file inspected:

```text
frontend/src/pages/AuthorityPage.jsx
```

Key behaviour:

```jsx
<BestPickCta tools={tools.slice(0,1)} monetisation={monetisation} />
<QuickComparison tools={tools.slice(1)} />
```

Therefore:

```text
The first affiliate-linked tool becomes “Our top pick”.
Remaining linked tools appear lower down in comparison/provider list.
```

Current implications:

```text
CloudLearn remains the top pick on best-online-gcse-a-level-courses-uk.
Alison appears lower down as an additional provider.
This is appropriate because Alison is broader free/career learning, not a main GCSE/A-Level provider.

ChatGPT remains the top pick on best-ai-productivity-tools-uk.
EMPLA appears lower down unless a focused AI virtual assistant guide is created later.
```

Recommended future guides for stronger affiliate fit:

```text
best-free-online-courses-uk
Best free online courses in the UK (2026): skills, careers and flexible learning

best-ai-virtual-assistants-small-business-uk
Best AI virtual assistants for small businesses in the UK (2026)
```

BrickZoneHub should not be promoted until its draft guide is properly written, checked and published.

### J. Sponsored placement / house-guide affiliate ad rotation work completed

Goal discussed:

```text
Use empty advertising slots to rotate Cheshire Today’s own affiliate-supported guide cards until real paid adverts are available.
```

Strategic decision:

```text
Do not send ad-slot clicks directly to Awin links.
Send them to Cheshire Today guide pages first, then guide provider buttons handle affiliate clicks.
```

Reason:

```text
More trusted reader experience.
More page views/time on site.
Affiliate disclosure already exists on guide pages.
Less spammy than random direct affiliate banners.
Better SEO/internal-link value.
```

Existing sponsored placement system supports:

```text
placement
sponsor_name
title
description
target_url
image_url
cta_text
package_tier
campaign_id
rotation_weight
priority
starts_at
ends_at
active
impression tracking
click tracking
```

Frontend file changed:

```text
frontend/src/components/SponsoredPlacement.jsx
```

Problem found:

```text
All active placements were hardcoded to display label “Sponsored”.
That would be misleading for Cheshire Today-owned affiliate guide promos.
```

Fix implemented:

```js
const isHouseGuide = isPaidPlacement && (
  String(ad?.package_tier || "").toLowerCase().includes("house") ||
  String(ad?.campaign_id || "").toLowerCase().includes("ct_house")
);
const placementLabel = isPaidPlacement ? (isHouseGuide ? "Affiliate guide" : "Sponsored") : fallbackCopy.eyebrow;
```

Also changed link relation:

```text
House guide promo: rel="noopener noreferrer"
Paid sponsored advert: rel="noopener noreferrer sponsored"
```

Frontend build passed:

```text
REACT_APP_BACKEND_URL=https://cheshiretoday.co.uk npm run build
Compiled successfully.
```

Commit pushed:

```text
f3175f4 Label house guide placements clearly
```

Branch pushed:

```text
full-scrape-prod
```

Behaviour after deploy:

```text
Paid advertiser placements -> Sponsored
Cheshire Today house guide promos -> Affiliate guide
Fallback empty slot -> Local advertising
```

### K. Active house-guide sponsored placements created through live admin API

Created active rotating guide promos through:

```text
POST /api/admin/sponsored-placements/upsert
```

Important: these point to Cheshire Today guide pages, not direct Awin links.

Created placements:

```text
ct-house-ai-productivity-guide-sidebar
placement: article_sidebar
sponsor_name: Cheshire Today Guides
title: AI tools for small businesses
description: Compare practical AI productivity tools for admin, writing, planning and small business work.
target_url: https://cheshiretoday.co.uk/guides/best-ai-productivity-tools-uk
cta_text: View guide
package_tier: House guide
campaign_id: ct_house_guides_affiliate
rotation_weight: 1
priority: 5
active: true

ct-house-ai-productivity-guide-mobile
placement: article_mobile
same target/title/description as above
active: true

ct-house-online-learning-guide-sidebar
placement: article_sidebar
sponsor_name: Cheshire Today Guides
title: Flexible online learning options
description: Compare online GCSE, A-Level and skills course options for adult learners and career changers.
target_url: https://cheshiretoday.co.uk/guides/best-online-gcse-a-level-courses-uk
cta_text: View guide
package_tier: House guide
campaign_id: ct_house_guides_affiliate
rotation_weight: 1
priority: 5
active: true

ct-house-online-learning-guide-mobile
placement: article_mobile
same target/title/description as above
active: true
```

Verification passed:

```text
/api/sponsored-placements?placement=article_sidebar&limit=5
returned both:
- ct-house-online-learning-guide-sidebar
- ct-house-ai-productivity-guide-sidebar

/api/sponsored-placements?placement=article_mobile&limit=5
returned both:
- ct-house-online-learning-guide-mobile
- ct-house-ai-productivity-guide-mobile
```

Backend health after push:

```text
{"status":"healthy","service":"cheshire-news"}
```

Old Retreat Social Club placements were still `active: true` in admin listing, but had:

```text
ends_at: 2026-07-02T23:59:00.000Z
```

So they should no longer serve publicly after that end date.

### L. Recommended follow-ups after this chat

1. **Visual QA after frontend deploy**

Open a live article and refresh a few times. Confirm rotating cards show:

```text
Affiliate guide
Cheshire Today Guides
```

not:

```text
Sponsored
```

2. **Track house-guide click performance**

After 24–72 hours, check admin sponsored placements for:

```text
impression_count
click_count
last_click_at
```

Compare AI guide vs online-learning guide.

3. **Create better focused affiliate guides**

Suggested future guide pages:

```text
best-free-online-courses-uk
best-ai-virtual-assistants-small-business-uk
```

These would give Alison and EMPLA better top-pick positioning than the current broader guides.

4. **Do not activate BrickZoneHub rotation yet**

Current BrickZoneHub guide is draft:

```text
/guides/best-building-renovation-supplies-uk
```

Write/QA/publish it first, then add house-guide placements for property/finance/article slots.

5. **Consider homepage house-guide slots later**

Current active house-guide promos are only:

```text
article_sidebar
article_mobile
```

Do not add homepage slots until article-slot CTR is checked.

6. **Fix import/manual-review weaknesses later, carefully**

Known future fixes to consider:

```text
Always enforce 1000+ char floor before public status, including RSS/manual_review_without_ai fallback.
Add final post-rewrite editorial-fit gate.
Detect weak national/London-only items unless they strongly fit Cheshire Today strategy.
Require verification/rewrite status before public import where appropriate.
Improve fact/location drift detection.
```

Do not make these import fixes without first checking this state file and previous import changes.

7. **Daily Brief follow-up**

If newsletters still show no delivery/open/click activity:

```text
Check /api/admin/email-config/validate-resend
Replace invalid Render RESEND_API_KEY if needed
Confirm next scheduled digest has success_count > 0 and provider_error empty
```

### M. Resume prompt for next chat after 7 July 2026 work

```text
Continue Cheshire Today from the 7 July 2026 update in the single chat-source master state file. First check the state file before any code/database/content-pool/category/newsletter/affiliate/advertising change. Latest work completed: article intro/Continue reading/guide-heading UX commits through eba2db9; Daily Brief failure logging and Resend validation commits 5c31603 and 276f7ff; affiliate authority-page DB updates adding EMPLA to best-ai-productivity-tools-uk and Alison to best-online-gcse-a-level-courses-uk; BrickZoneHub guide created as draft best-building-renovation-supplies-uk; frontend sponsored placement label fix commit f3175f4; live active house-guide placements created for article_sidebar and article_mobile pointing to the AI productivity and online learning guides. Important: house-guide promos should display “Affiliate guide”, not “Sponsored”, after frontend deploy. Do not promote BrickZoneHub until its guide is written/QA’d/published. Known unresolved issues: import/manual-review gates can allow weak/thin RSS fallback items public; Resend key may still need replacing if validation returns 401; check house-guide impression/click counts after 24–72 hours. Workflow: one command at a time, safe terminal/script changes, use /usr/bin/grep not rg, verify after each step, no dev server unless asked.
```

---

## 2026-07-10 — Google indexing / crawler HTML / sitemap recovery phase

### Context

This update records the major Google Search Console, crawler HTML, sitemap, guide-indexing, archived-article and force-live fixes completed during the July 2026 SEO recovery work.

The operational goal was to diagnose why Google Search Console still showed very low indexing and a large number of `Crawled - currently not indexed` URLs, despite the site being live and sitemaps being available.

The Page Indexing report in Search Console was still showing stale report data with last update around 12 June. Because of that, live URL checks and Googlebot-style curl checks were treated as the source of truth for technical verification.

### Key Search Console findings

Search Console Page Indexing report showed:

- Indexed: about 3 pages.
- Not indexed: about 3.04k pages.
- Last update shown: 12 June.

Breakdown observed:

- `Crawled - currently not indexed`: 2,024 pages.
- `Alternative page with proper canonical tag`: 488 pages.
- `Not found (404)`: 451 pages.
- `Page with redirect`: 30 pages.
- `Excluded by noindex tag`: 26 pages.
- `Duplicate, Google chose different canonical`: 19 pages.
- `Soft 404`: 1 page.
- `Discovered - currently not indexed`: 0 pages.

Important interpretation:

- Discovery was not the main issue because `Discovered - currently not indexed` was 0.
- Google had already crawled many URLs but declined to index them.
- The biggest live technical problems were crawler HTML quality, weak internal links for bots, guide pages serving SPA shell, and archived old imports still returning `index, follow`.

### Article crawler HTML fixed

Initial live checks showed normal browser routes used the SPA shell, and Googlebot article HTML was too thin. Article pages for crawlers did not initially expose enough full body content / NewsArticle schema.

`serve_article_html(article_id, request=None)` was improved to output proper crawler HTML for article pages, including:

- Full article body paragraphs.
- Correct canonical URL.
- Correct `og:url`, Open Graph and Twitter metadata.
- `NewsArticle` JSON-LD.
- `articleBody` field.
- `<article>`, `<h1>`, byline, `<time>`, and visible content.
- `meta robots` handling.
- `max-image-preview:large`.

Commits:

- `6b80bff` — `Improve crawler article SEO HTML`
- `2b8194c` — `Format crawler article dates for SEO`

Date formatting was later verified live. Example output for article dates:

- `article:published_time = 2026-06-26T05:00:00+00:00`
- `datePublished = 2026-06-26T05:00:00+00:00`
- `<time datetime=...>` matched.

### Bad AI/internal wording removed and prevention tightened

A live crawler HTML check exposed a bad internal-style paragraph in one article, including wording similar to:

- `No police involvement...`
- `resident complaints...`
- `specific venue damage...`
- `source material...`

The affected article was cleaned via the existing admin update flow after `ADMIN_TOKEN` was loaded.

The manual review risk terms were extended to catch internal AI residue before publication, including terms such as:

- `source material`
- `not mentioned in the source`
- `not mentioned in source`
- `no police involvement`
- `resident complaints`
- `specific venue damage`
- `business closures`

Commit:

- `5c265de` — `Flag internal AI residue in article rewrites`

### Sitemap keyword filters expanded for strategic Business / Tech content

A sitemap audit found some strategically useful Business / Tech articles were missing from the main sitemap because the filters were too narrow.

Examples initially missing included:

- Record temperatures driving home air-conditioning sales.
- Former Huntress analyst / ransomware insider claim.
- Geothermal start-ups.
- Recruitment / getting a job.

The sitemap and news sitemap filters were expanded with terms including:

- `job`
- `recruitment`
- `sales`
- `air conditioning`
- `geothermal`
- `start-ups`
- `startups`
- `startup`
- `ransomware`

Commit:

- `7b1924d` — `Include more strategic business tech articles in sitemaps`

Live check after deploy confirmed:

- Main sitemap increased and included the strategic article IDs.
- News sitemap included the relevant recent items where date-eligible.
- Non-strategic / no-impact items such as the Baroness Mone example remained excluded.

### Article index route checked

`/article-index` was tested as Googlebot and confirmed crawlable.

Observed:

- No JS shell.
- Correct robots/canonical.
- Article links visible.

Comparison between sitemap and article-index showed no missing sitemap article URLs from article-index at the time of the check. No patch was made to `/article-index` at that point.

### Guide pages were serving SPA shell and then fixed

Sitemap breakdown showed many guide URLs were in the sitemap:

- Total sitemap locs around that phase: 72.
- Article URLs: 23.
- Guide URLs: 35.
- Category pages: 4.
- Location/other pages: 10.

Googlebot checks for guide URLs such as:

- `/guides/best-web-hosting-small-business-uk`
- `/guides/cost-of-buying-home-cheshire-2026`
- `/guides/best-ai-tools-uk`

initially showed they returned SPA/homepage-style shell signals:

- Homepage title/canonical.
- No real guide H1.
- No useful guide body for bots.

A crawlable guide route was added for bots:

- `serve_guide_html(slug, request=None)`
- `/guides/{slug}` crawler support.
- `/api/guides/{slug}` HTML variant support.

Guide crawler HTML includes:

- Correct guide title.
- Correct canonical.
- Visible H1/content/tool sections.
- Affiliate links with `rel="nofollow sponsored noopener"`.
- `WebPage` JSON-LD.
- Robots handling.

Commit:

- `ad8df82` — `Serve crawlable HTML for authority guide pages`

Live verification after deploy showed:

- `HAS_JS_SHELL=False`
- correct canonical.
- H1 visible.
- `WEBPAGE_SCHEMA=True`.

### Thin guide protection added

A guide-quality audit found 8 thin/stub guides under the useful-content threshold.

Thin guide examples included:

- `best-ai-tools-uk`
- `best-ai-productivity-tools-uk`
- `best-ai-writing-tools-uk`
- `best-savings-accounts-uk`
- `best-mortgage-rates-uk`
- `best-business-credit-cards-uk`
- `best-business-bank-accounts-uk`
- `best-credit-cards-uk`

These were not deleted because they may be useful later, but they were removed from sitemap submission and set to `noindex, follow` until improved.

Rule added:

- If guide useful content length from sections is under 700 characters, exclude from sitemap and return `noindex, follow, max-image-preview:large`.
- Strong guide pages remain `index, follow`.

Commit:

- `644b2b2` — `Noindex thin authority guides until improved`

Live verification after deploy:

- Thin guide examples returned `noindex, follow`.
- Strong guides such as `best-web-hosting-small-business-uk` and `cost-of-buying-home-cheshire-2026` returned `index, follow`.
- Sitemap guide count reduced from 35 to 27.

### Public hub crawler HTML added

A major internal-link issue was found: Googlebot saw SPA shell for the homepage/category/location pages, meaning crawler-visible links to articles and guides were weak or missing.

Before the fix:

- Homepage was JS shell to Googlebot.
- Category pages were JS shell to Googlebot.
- Some GSC examples showed `Referring page: None detected`.

A public hub crawler HTML renderer was added:

- `_is_crawler_request(request: Request)`
- `serve_public_hub_html(full_path: str = "")`

Crawler HTML support was added for:

- Homepage `/`
- `/category/{slug}`
- Location pages such as `/chester`, `/warrington`, `/crewe`, `/wirral`, `/macclesfield`, `/stockport`, `/runcorn`, `/northwich`
- The renderer builds visible article links, guide links, category links and location links.
- It filters out thin guides from hub links.
- It uses `CollectionPage` JSON-LD.

Commit:

- `a2ef26f` — `Serve crawlable HTML for public hub pages`

Live checks confirmed:

Homepage:

- `HAS_JS_SHELL=False`
- `ROBOTS=index, follow, max-image-preview:large`
- Correct canonical.
- 40 article links.
- 16 guide links.
- 10 category links.

Category examples:

- `/category/business` crawlable, indexable, correct canonical.
- `/category/finance` crawlable, indexable, correct canonical.
- `/category/local-news` crawlable, indexable, correct canonical.

Location examples:

- `/chester` crawlable, indexable, correct canonical.
- `/warrington` crawlable, indexable, correct canonical.

Minor wording issue noted but not urgent:

- `Local News news and updates | Cheshire Today`

This can be cleaned later.

### Archived old article pages now noindex

Search Console examples for `Crawled - currently not indexed` were mostly old archived imported articles. Live diagnostics showed those pages were:

- `archived=True`
- `archive_reason=auto_cap` or `duplicate`
- not in sitemap.
- still returning `index, follow`.

Examples included old Guardian/BBC/local imports such as asteroid, Spitfire, North Sea drilling, Topps Tiles, 1970s oil crisis, Ireland energy crisis and NASA Artemis items.

A robots rule was added so archived/manual-review-hidden article pages remain reachable for old links but are not submitted as indexable pages.

Initial rule:

- `article.get("archived") is True` → `noindex, follow`.
- `article.get("manual_review_hidden_from_public") is True` → `noindex, follow`.

Commit:

- `3a55b5e` — `Noindex archived article pages`

Live verification after deploy confirmed old archived examples returned:

- `HAS_JS_SHELL=False`
- `ROBOTS=noindex, follow, max-image-preview:large`
- correct canonical.

This is expected to shift many old Search Console examples from `Crawled - currently not indexed` to `Excluded by noindex tag` after Google recrawls them. That is correct for archived pages.

### Force-live articles allowed to stay indexable

After adding archived-article noindex, an important strategic article was found to be both archived and force-live:

- URL: `/article/6a3e5c043f6281aa4325b390/this-is-so-exciting-cheshire-and-warrington-s-big-moment-as-region-declares-itse`
- Title: `'This is so exciting': Cheshire and Warrington's big moment as region declares itself 'open for business'`
- Category: `Local News`
- Scope: `cheshire`
- Source: `Cheshire Live`
- Published: `2026-06-26T05:00:00`
- `ARCHIVED=True`
- `ARCHIVE_REASON=auto_cap`
- `FORCE_LIVE=True`

Problem found:

- It returned `noindex, follow`.
- It was excluded from sitemap because sitemap query used `"archived": {"$ne": True}`.

The rule was corrected so `force_live=True` intentionally overrides archived status for indexability and sitemap inclusion, while manual-review-hidden pages always remain noindex.

Final rule:

- Normal active strategic article: may be in sitemap and `index, follow`.
- Archived old article without force-live: excluded and `noindex, follow`.
- Archived but `force_live=True`: included and `index, follow`.
- Manual-review-hidden article: excluded and `noindex, follow`.

Sitemap query updated to include:

- `manual_review_hidden_from_public != True`
- and either `archived != True` or `force_live=True`.

Article robots rule updated to:

- `manual_review_hidden=True` → noindex.
- `archived=True and force_live is not True` → noindex.
- `archived=True and force_live=True` → index.

Commit:

- `2000dfd` — `Allow force live articles to stay indexable`

Live verification after deploy confirmed for the strategic article:

- `ARCHIVED=True`
- `FORCE_LIVE=True`
- `IN_SITEMAP_BY_ID=True`
- `ROBOTS=index, follow, max-image-preview:large`
- `HAS_JS_SHELL=False`
- correct canonical.

### Sitemap and live crawler status after latest verification

Latest live verification showed:

Sitemaps:

- `MAIN_TOTAL_LOC=68`
- `MAIN_ARTICLE_URLS=27`
- `MAIN_GUIDE_URLS=27`
- `NEWS_TOTAL_LOC=11`

Homepage:

- `HTTP_CODE=200`
- `HAS_JS_SHELL=False`
- `ROBOTS=index, follow, max-image-preview:large`
- correct canonical.
- 40 article links.
- 16 guide links.

Category pages:

- `/category/business` indexable, no JS shell, correct canonical, 7 article links, 15 guide links.
- `/category/finance` indexable, no JS shell, correct canonical, 6 article links, 10 guide links.
- `/category/local-news` indexable, no JS shell, correct canonical, 16 article links, 12 guide links.

Strong guides:

- `/guides/best-web-hosting-small-business-uk` indexable, no JS shell, correct canonical.
- `/guides/cost-of-buying-home-cheshire-2026` indexable, no JS shell, correct canonical.

Archived old article example:

- `/article/69ca6997ce11a2e917daae09/...`
- no JS shell.
- `ROBOTS=noindex, follow, max-image-preview:large`.
- correct canonical.

Force-live strategic article:

- `/article/6a3e5c043f6281aa4325b390/...`
- no JS shell.
- `ROBOTS=index, follow, max-image-preview:large`.
- in sitemap.
- correct canonical.

### Alternative canonical group checked

Search Console's `Alternative page with proper canonical tag` examples were checked.

Findings:

- Query URL `/?category=AI%20%26%20Tech` correctly canonicalised to homepage.
- `/category/festive` returned 404, which is acceptable for an old unsupported category.
- Old article variants returned `noindex, follow` after archived cleanup and were not in sitemap.

This group was judged low risk and mostly harmless.

### Operational interpretation

The current live site is no longer showing the earlier major crawler/indexing technical problems.

Current live state:

- Homepage crawler HTML fixed.
- Category crawler HTML fixed.
- Location crawler HTML fixed.
- Article crawler HTML fixed.
- Strong guide crawler HTML fixed.
- Thin guides protected with `noindex`.
- Archived old articles protected with `noindex`.
- Force-live strategic articles remain indexable and can be included in sitemap.
- Sitemaps are still `Success` in Search Console, but Page Indexing report is lagging.

Search Console Page Indexing may not update immediately. The large `Crawled - currently not indexed` count is expected to lag and may partly move into `Excluded by noindex tag` after old archived URLs are recrawled. That is acceptable for archived pages.

### Current recommended next steps

1. Do not make more indexing-related code changes unless a new live technical problem is found.
2. Monitor Search Console after the Page Indexing report updates beyond 12 June.
3. Use URL Inspection live test for priority URLs rather than relying only on the stale Page Indexing graph.
4. Keep requesting indexing only for a small number of important URLs, not old archived examples.
5. Improve thin guides before reindexing them.
6. Later tidy the category title wording: `Local News news and updates`.
7. Continue keeping archived/non-strategic imported articles out of sitemap and noindexed unless deliberately force-live.

### Important caution going forward

Do not undo the archived article `noindex` behaviour. It is needed to clean up thousands of old/weak imported URLs in Search Console.

Do not make `archived=True` automatically mean noindex without checking `force_live=True`. The final intended behaviour is:

- `manual_review_hidden_from_public=True` always noindex.
- `archived=True` and `force_live` not true = noindex.
- `archived=True` and `force_live=True` = indexable and sitemap-eligible.

Do not add thin/stub guide pages back into the sitemap until they have useful guide content above the current threshold.

---

## 2026-07-10 — town feeds, manual town assignment, Daily Brief scheduler protection, legacy Facebook links, and current unresolved social-preview issue

### A. Operational source-of-truth rule

This consolidated file is now the single operational Cheshire Today state file.

Going forward:

```text
1. Check this file first before code/database/content-pool/category/newsletter/affiliate/advertising/indexing/social-link changes.
2. Use current repo and live API checks to confirm the latest production state.
3. Do not use Cheshire_Economic_AI_Project_Master_Feb2026.pdf as operational truth.
4. The old master PDF is only for high-level historical strategy when explicitly relevant.
5. Do not create additional competing state files after each chat; update this consolidated file instead.
```

### B. Weak RSS fallback public guard completed

Commit:

```text
feb87da Guard weak RSS fallback imports from public view
```

Implemented a final manual-review guard for weak RSS/fallback articles:

```text
- RSS/fallback articles under 1000 characters are routed to manual review.
- Known boilerplate/filler markers are routed to manual review.
- AI-rewritten items are exempt from this specific weak-RSS check.
```

Syntax validation passed and the commit was pushed to `full-scrape-prod`.

### C. Unsupported town menu links removed

Commit:

```text
71af325 Remove unsupported town menu links
```

Removed visible menu links for unsupported town slugs that returned location-not-found responses:

```text
nantwich
ellesmere-port
winsford
```

Do not re-add these links unless backend location routes are explicitly supported/mapped and live-tested.

### D. Town feeds now use the same public visibility guard as main live feeds

Commit:

```text
bdb2eac Apply public visibility guard to town feeds
```

The `/api/articles/location/{location}` route now excludes:

```text
archived=True
manual_review_hidden_from_public=True
```

This fixed the mismatch where town feeds listed articles that then opened as `Article not found`.

Verified live after deployment:

```text
chester:      9 articles, 0 broken
warrington:   1 article,  0 broken
crewe:        1 article,  0 broken
macclesfield: 0 articles, 0 broken
wilmslow:     1 article,  0 broken
knutsford:    1 article,  0 broken
northwich:    0 articles, 0 broken
```

Restore/manual-edit behaviour was also confirmed:

```text
- During manual review: hidden from main feeds and town feeds.
- After a suitable manual edit/restoration: hidden flags are cleared, archived=False, and the article can reappear automatically in its town feed.
```

### E. Manual article town-location override added

Commit:

```text
f9d6624 Allow manual article town location override
```

`ManualArticleCreate` now accepts optional:

```text
location
```

Supported manual location slugs:

```text
chester
warrington
crewe
wirral
macclesfield
wilmslow
knutsford
stockport
northwich
cheshire-general
```

Behaviour:

```text
- If admin sends a valid location, backend uses that explicit town.
- If no location is sent, backend falls back to auto-detection.
- Unsupported location values return HTTP 400.
```

Confirmed live manual assignments:

```text
6a4cdc9c24f31577fce1f52f -> chester
6a4c9d1f24f31577fce1f527 -> wilmslow
6a4c9c9b24f31577fce1f525 -> wilmslow
6a4a39929a5ab609287d8b3a -> macclesfield
6a0b3a948291326f210f02ee -> wilmslow
69ea9efe4efa05af448d2278 -> wilmslow
```

Verified affected feeds after correction:

```text
chester:      11 articles, 0 broken
wilmslow:      5 articles, 0 broken
macclesfield:  1 article,  0 broken
warrington:    0 articles, 0 broken
```

Important caution:

```text
Do not bulk-assign town locations blindly.
Inspect article title/content/source first.
Manual edits can re-run location logic, so use the explicit location field when a deliberate town assignment is required.
```

### F. Editable article summary field added

Commit visible in current git history:

```text
4cc1b2a Add editable article summary field
```

This is part of the current live admin/article state.

Pending separate request:

```text
Admin manual edit still does not have a dedicated image-caption field.
The preferred future implementation is an optional `image_caption` field wired through backend model, create/update routes, API output, admin form, and public article rendering below the lead image.
Do not implement until current state is checked first.
```

### G. Daily Brief failure root cause identified

Live `digest_log` showed a repeated pattern:

```text
Successful Daily Brief sends:
instance_id = srv-d5virmm...
success_count = 1000

Failed Daily Brief sends:
instance_id = unknown_...
success_count = 0
provider = resend
Resend response = 401 API key is invalid
```

Examples:

```text
2026-07-08: failed, unknown_9d51db6f, 0 sent
2026-07-02: failed, unknown_4994f6a7, 0 sent
```

This explained why some Wednesday/Thursday dashboard entries had no opens/clicks: those batches were not delivered.

SMTP was not the cause. The failing path was:

```text
Daily Brief scheduler -> Resend batch API -> 401 invalid API key
```

### H. Unknown scheduler instances blocked

Commit:

```text
432b180 Prevent unknown scheduler instances claiming digests
```

Added two protections:

```text
1. Scheduler will not start when AUTO_GENERATION_ENABLED=true but HOSTNAME is missing/unknown.
2. send_scheduled_news_digest refuses to claim the digest lock if HOSTNAME is missing/unknown.
```

Verified after deploy:

```text
2026-07-09 DailyBrief
status: sent
instance_id: srv-d5virmm3jp1c73c9d6tg-6bcc5c8998-nxmtl_a7c59248
success_count: 1000
provider: resend
provider_error: null
resend_failed_chunks: 0
resend_successful_chunks: 10
```

Analytics were also working for successful sends:

```text
2026-07-09: delivered 1000, opens 123, clicks 108
2026-07-08: delivered 0, opens 0, clicks 0
2026-07-07: delivered 1000, opens 74, clicks 59
```

Conclusion:

```text
Open/click tracking works when delivery succeeds.
The zero-engagement rows were delivery failures, not primarily analytics failures.
```

### I. Legacy slug-only article links restored

Problem found in a Facebook post:

```text
Old/incorrect social URL:
https://cheshiretoday.co.uk/article/tap-and-go-coming-to-chester-railway-station-with-transport-for-wales

Result before fix:
HTTP 404
```

Current canonical format remains:

```text
/article/{article_id}/{slug}
```

Commit:

```text
e0113e0 Restore legacy slug-only article links
```

The production `/article/{article_id}` fallback now attempts safe slug/title recovery when the path value is not a real ID, then redirects to the canonical ID+slug URL.

Verified live:

```text
HTTP/2 301
location: https://cheshiretoday.co.uk/article/6a4fd4081c580910e0709046/tap-and-go-coming-to-chester-railway-station-with-transport-for-wales
```

Keep this backward-compatibility redirect. Do not replace the canonical ID+slug routing.

### J. Current Facebook/social-link issue still under investigation

A newer Facebook post used another slug-only link:

```text
https://cheshiretoday.co.uk/article/patients-reveal-easiest-gp-practices-to-contact-by-phone-in-and-around-chester
```

The exact canonical live URL is:

```text
https://cheshiretoday.co.uk/article/6a4fd3fa1c580910e0709045/patients-reveal-easiest-gp-practices-to-contact-by-phone-in-and-around-chester
```

Repo search showed current active source helpers generally use article IDs:

```text
frontend/src/components/SocialShare.jsx -> /article/${articleId}
frontend/src/components/SchemaMarkup.jsx -> /article/${article.id}
backend canonical routes -> /article/{id}/{slug}
```

No confirmed active website/admin code path was found in that search that intentionally generates `/article/{slug}` for a new post.

Current working conclusion:

```text
- The legacy redirect repairs already-published slug-only links.
- New social captions must never synthesize a URL from the headline alone.
- Always use the exact live ID-based canonical URL from the API/article page.
- The GP article was reported as “not showing” on Facebook even after the canonical URL was identified.
- The next check must inspect that exact article’s crawler HTML, og:image, image response, and Facebook Sharing Debugger result before any more code changes.
```

Do not assume this is only Facebook cache, only image metadata, or only the redirect. Reproduce against the exact GP canonical URL first.

### K. Current latest git state from this working sequence

Known commits in this period:

```text
feb87da Guard weak RSS fallback imports from public view
71af325 Remove unsupported town menu links
bdb2eac Apply public visibility guard to town feeds
f9d6624 Allow manual article town location override
4cc1b2a Add editable article summary field
432b180 Prevent unknown scheduler instances claiming digests
e0113e0 Restore legacy slug-only article links
```

Branch:

```text
full-scrape-prod
```

At the time of each verification, local and origin were aligned after pushes.

### L. Immediate next steps

1. **Resolve the GP Facebook preview/link display issue without blind changes**

Use the exact canonical URL:

```text
https://cheshiretoday.co.uk/article/6a4fd3fa1c580910e0709045/patients-reveal-easiest-gp-practices-to-contact-by-phone-in-and-around-chester
```

Check:

```text
HTTP status/redirect chain
canonical
robots
og:title
og:description
og:image
og:image response status/content-type/dimensions
Facebook Sharing Debugger fetched URL and preview
```

2. **Trace social-post URL creation**

Do not rely on broad searches that include backups/build logs. Search active source only:

```text
frontend/src
backend/server.py
backend/app
```

Exclude:

```text
*.bak*
node_modules
venv
build logs
```

Find any workflow that produces a Facebook caption with `/article/{slug}` instead of the exact live canonical URL.

3. **Add image caption support later**

After the Facebook issue is stable, add optional `image_caption` support across backend/admin/public article rendering.

4. **Continue monitoring Daily Brief**

Check future Wednesday/Thursday sends for:

```text
instance_id begins srv-
success_count > 0
provider_error is null
```

5. **Keep one state file only**

This consolidated file supersedes the separate state-file copies listed in its source reconciliation section.

---

## 12 July 2026 update — Admin OpenAI factual rewrite and editorial guard

### A. Operational source-of-truth reminder

This same chat-source state file remains the single operational source of truth for Cheshire Today.

Before any future code, database, content-pool, category, newsletter, affiliate, advertising or article-generation change:

1. Read this current state file first.
2. Check the current branch and live behaviour.
3. Do not rely on the February 2026 master PDF for current implementation state.
4. Use the master PDF only for high-level strategy when explicitly needed.

Workflow remains:

```text
One safe command at a time.
No manual code editing.
Use precise scripted terminal changes.
Use /usr/bin/grep rather than rg.
Run syntax checks and inspect the diff before committing.
Do not run npm start unless explicitly asked.
Do not publish or save generated OpenAI drafts automatically.
```

### B. Objective of this work

The Admin Archive/Manual Review **Open AI** button was improved so it can create a fuller, factual, human-review draft similar to the manual ChatGPT rewriting workflow.

The required safety boundary remains:

```text
Open AI button -> research/rewrite draft -> populate admin editor -> human reviews -> human presses Update Article
```

It must not:

```text
auto-save
auto-publish
auto-archive
auto-hide
control scheduled imports
replace the human editor
```

Automatic imports still use the existing RSS/source + Perplexity workflow and deterministic public/manual-review quality gates. OpenAI remains admin-only.

### C. Current Admin OpenAI rewrite architecture

The frontend Admin **Open AI** action calls:

```text
POST /api/admin/articles/{article_id}/openai-rewrite-draft
```

The backend function is:

```text
run_openai_article_rewrite_draft(article)
```

Current factual workflow:

```text
1. Read stored article fields as leads only.
2. Try to retrieve the original source page directly.
3. If direct source content is available, use it as the primary factual source.
4. If direct retrieval is blocked or unavailable, ask Perplexity for a structured verified fact pack.
5. Send source_page_content or research_fact_pack to OpenAI.
6. OpenAI returns JSON containing title, summary, content, category and editor_notes.
7. A deterministic editorial guard checks the draft.
8. If selected violations are found, one focused OpenAI copy-edit correction pass runs at temperature 0.
9. The corrected draft is checked again.
10. The result is returned to the admin editor but is not saved or published.
```

### D. Direct source scraping work

The simple source scraper had an earlier regex escaping defect that damaged text extraction by stripping characters. This was corrected in:

```text
d90cd78 Fix source article text extraction
```

Related import fix:

```text
4a0a39c Fix OpenAI source scraper import
```

Source fetch diagnostics were exposed in:

```text
c0ab82e Expose OpenAI source fetch diagnostics
```

A local test against:

```text
https://goostreyparishcouncil.gov.uk/dont-lose-your-vote/
```

successfully extracted roughly 1,418 characters and preserved the key facts, including:

```text
- Cheshire East residents urged to check electoral registration.
- Elections for all Cheshire East Council seats on 6 May 2027.
- Elections for town and parish councillors.
- Election of the first mayor of the Cheshire and Warrington Combined Authority.
- Annual canvass details.
- Helen Charlesworth-May attribution.
- Registration route at gov.uk/register-to-vote.
```

However, the live Render environment received HTTP 403 from that publisher. Jina was also blocked by a security verification page. This confirmed that a robust research fallback was needed rather than repeatedly trying alternate scraping proxies.

### E. Structured Perplexity fact research fallback

Initial prose fallback work:

```text
a01de4b Add Perplexity fallback for OpenAI drafts
```

Prompt strengthening:

```text
a082f6b Strengthen OpenAI rewrite journalism prompt
```

Structured fact research was then added:

```text
6bfae07 Add structured article fact research
2723fc7 Use verified fact packs for OpenAI drafts
```

The helper in:

```text
backend/app/perplexity_service.py
```

is:

```text
research_article_facts(title, summary="", source="", source_url="")
```

It is intended only for the admin OpenAI draft workflow and does not save or publish anything.

The fact pack uses this structure:

```json
{
  "verified_headline_facts": ["fact"],
  "verified_facts": ["fact"],
  "names_and_roles": [{"name": "...", "role": "...", "verified": true}],
  "dates": ["date/context"],
  "locations": ["..."],
  "figures": ["..."],
  "quotations": [{"quote": "...", "speaker": "..."}],
  "practical_information": ["..."],
  "uncertain_or_unverified": ["..."],
  "contradictions": ["..."],
  "source_urls": ["..."],
  "research_summary": "..."
}
```

Research rules include:

```text
- Try the original source URL first.
- Use reputable corroborating sources.
- Separate verified facts from uncertain claims and contradictions.
- Return structured facts rather than a ready-written article.
- Let OpenAI write only from verified fields.
```

### F. Fact-pack and source diagnostics now returned to admin

Commit:

```text
56d8888 Expose OpenAI research fact pack
```

The draft response now includes admin-only diagnostics:

```text
source_fetch_status
source_page_content_length
research_fact_pack_available
research_source_count
research_fact_pack
```

This was added to inspect exactly what Perplexity supplied before changing the research prompt further.

Do not expose these diagnostics on public article pages.

### G. Goostrey live test result after fact-pack connection

Test article:

```text
article_id: 6a4c884124f31577fce1f524
source: https://goostreyparishcouncil.gov.uk/dont-lose-your-vote/
```

Observed response:

```text
SUCCESS: True
SOURCE_FETCH_STATUS: HTTP 403; fact_research_ok
SOURCE_CONTENT_LENGTH: 0
FACT_PACK_AVAILABLE: True
RESEARCH_SOURCE_COUNT: 10
CONTENT_LENGTH: about 488 characters
```

The architecture worked, but the generated draft remained too thin and omitted several facts known from the locally retrievable source, including:

```text
6 May 2027
the combined-authority mayor election
annual canvass details
named official attribution
gov.uk registration information
```

This means the factual pipeline is functioning, but Perplexity research depth must still be assessed from the returned fact pack when a source blocks Render.

### H. Healthy-life-expectancy article used as editorial quality test

A UK healthy-life-expectancy article was repeatedly used to test whether the Open AI button could produce a publishable professional news feature.

Early drafts were longer and more coherent than the stored item, but introduced or repeated material requiring verification, including references to:

```text
National Voices
Gareth Lyon / Policy Exchange
Sebastian Rees / IPPR
Prof Martin McKee
Dr David Blane
an individual named Angie
comparisons with the Netherlands
claims about tax-funded and insurance-based health systems
regional healthy-life-expectancy gaps
```

These may be accurate only when supported by the source page or structured fact pack. The article must not be published merely because the prose reads convincingly.

Standing factual rule:

```text
Every name, role, quotation, date, figure, comparison, study and policy claim must be traceable to source_page_content or a verified field in research_fact_pack.
```

### I. OpenAI journalism prompt refinements

Prompt refinement commits:

```text
3c6e858 Tighten OpenAI editorial standards
79aa168 Improve OpenAI news judgement and structure
65bd7b0 Restructure OpenAI editorial prompt
```

The prompt was first strengthened to require:

```text
- named attribution for statistics and claims;
- exact comparison periods;
- no emotional or interpretive language unless quoted;
- natural British English;
- strongest verified news angle first;
- no rhetorical or essay-style conclusion;
- a concrete final fact, response, date, deadline or practical detail;
- sentence-by-sentence factual support;
- omission of secondary facts that interrupt the story;
- clear separation of fact from attributed opinion.
```

The rules were then reorganised into clearer sections to reduce duplicated and competing instructions:

```text
SOURCE CONTROL
NEWS JUDGEMENT AND ATTRIBUTION
LEAD
STRUCTURE AND STYLE
ENDING
FINAL CHECK
```

Important explicit rules now include:

```text
- Stored title/summary/content are leads only.
- Do not use OpenAI training knowledge, memory or assumptions.
- Never present uncertain_or_unverified or contradictions as fact.
- Do not imply correlation proves causation.
- Do not create a false Cheshire angle.
- Use British spellings such as ageing, marginalised, organisation, programme and centre.
- Never end with generic phrases such as The debate continues, As discussions evolve, Looking ahead, Ultimately, Overall, the focus remains or urgent need for reform.
```

### J. Why prompt-only enforcement was not enough

Even after the structured prompt was deployed, drafts still sometimes contained prohibited wording such as:

```text
raising concerns about the effectiveness of the NHS
prompting scrutiny
prompting discussions
Recent data indicates
Experts are examining
As the UK grapples with these challenges
The future of the NHS remains uncertain
The situation highlights the urgent need...
a final rhetorical question
```

This showed that prompt instructions alone were not reliable enough for predictable admin output.

Decision:

```text
Stop extending the main prompt indefinitely.
Add a deterministic editorial rule check and one focused correction pass.
```

### K. Deterministic editorial correction guard

Commit:

```text
3fcc4a3 Add OpenAI editorial correction guard
```

The guard is implemented inside the admin OpenAI draft workflow after the initial JSON draft is parsed.

It checks for selected categories of failure:

```text
- interpretive wording in the opening paragraph;
- vague or unnamed attribution;
- generic, rhetorical or essay-style endings;
- selected non-British spellings.
```

When violations are detected:

```text
1. Record the detected violation labels.
2. Run one focused OpenAI copy-edit pass.
3. Use temperature 0.
4. Allow only facts already in the draft or supported by source_page_content/research_fact_pack.
5. Forbid new names, figures, claims, quotations, context or conclusions.
6. Remove unsupported or vaguely attributed material when no named source supports it.
7. Remove generic final paragraphs rather than replacing them with another generic conclusion.
8. Recheck the corrected article.
9. Put unresolved warnings in editor_notes.
```

The guard does not save, publish, archive or hide anything.

An affected request may be slightly slower and consume a second OpenAI call.

### L. Guard regex repair during implementation

The first scripted insertion produced double-escaped regex strings such as:

```python
r"\\braising..."
r"\\n\\s*\\n"
```

These would have searched for literal backslashes rather than word boundaries and paragraph breaks.

They were corrected before commit to:

```python
r"\braising..."
r"\n\s*\n"
```

Validation passed:

```text
python3 -m py_compile backend/server.py
git diff --check
```

No broken regex version was committed.

### M. Editorial guard diagnostics

The admin response now also includes:

```text
editorial_guard_triggered
editorial_guard_violations
editorial_guard_corrected
editorial_guard_remaining_violations
```

Meaning:

```text
editorial_guard_triggered = initial draft matched one or more rules
editorial_guard_violations = initial detected rule labels
editorial_guard_corrected = violations existed and none remained after correction
editorial_guard_remaining_violations = issues still detected after the correction pass
```

If the correction request fails, editor_notes receives:

```text
The automatic editorial correction pass could not be applied. Review the detected issues before publishing.
```

If violations remain after correction, editor_notes receives a specific warning.

### N. Expanded editorial guard patterns

The first deployed guard did not catch all wording variants in the next health-article test. It was expanded in:

```text
83d8d69 Expand OpenAI editorial guard patterns
```

Added coverage includes:

```text
prompting discussion
prompting discussions
prompting debate
Experts are examining
Experts are exploring
As ... grapples/evolves/continues/faces
The future ... remains uncertain/unclear
The situation ... highlights/underscores ... urgent need
urgent need for...
```

The ending check now examines the final two paragraphs rather than only the last paragraph, so an attributed official response cannot conceal an essay-style paragraph immediately before or after it.

### O. Latest branch and commit state at end of chat

Repository:

```text
CT29january26-new-website-migration
```

Branch:

```text
full-scrape-prod
```

Latest pushed commit:

```text
83d8d69 Expand OpenAI editorial guard patterns
```

Relevant recent commit sequence:

```text
a01de4b Add Perplexity fallback for OpenAI drafts
a082f6b Strengthen OpenAI rewrite journalism prompt
6bfae07 Add structured article fact research
2723fc7 Use verified fact packs for OpenAI drafts
56d8888 Expose OpenAI research fact pack
3c6e858 Tighten OpenAI editorial standards
79aa168 Improve OpenAI news judgement and structure
65bd7b0 Restructure OpenAI editorial prompt
3fcc4a3 Add OpenAI editorial correction guard
83d8d69 Expand OpenAI editorial guard patterns
```

All listed commits were pushed to:

```text
origin/full-scrape-prod
```

### P. Current limitations and safety notes

1. **The guard is pattern-based, not a general truth checker.**

It catches known editorial failure phrases but may miss new wording variants.

2. **The second OpenAI pass does not prove factual accuracy.**

It is a copy-edit correction layer. Source and fact-pack verification remains essential.

3. **Perplexity fact research can still be shallow when the publisher blocks access.**

Inspect research_fact_pack before assuming omitted or included details are complete.

4. **Convincing prose can still contain unsupported claims.**

Do not publish merely because the draft reads naturally.

5. **OpenAI remains admin-only.**

Do not connect this workflow to automatic imports or automatic publishing without a separate, carefully reviewed design.

6. **Keep human review mandatory.**

The Admin editor must review title, summary, content, category, editor_notes, source diagnostics and guard diagnostics before pressing Update Article.

### Q. Immediate next test after deployment

After commit `83d8d69` is live, press **Open AI** again on the same healthy-life-expectancy article.

Check that the returned draft no longer contains:

```text
prompting discussions
Experts are examining
As the UK grapples...
The future ... remains uncertain
urgent need for...
rhetorical final questions
generic summary conclusions
```

Also inspect the admin diagnostics:

```text
editorial_guard_triggered
editorial_guard_violations
editorial_guard_corrected
editorial_guard_remaining_violations
source_fetch_status
source_page_content_length
research_fact_pack_available
research_source_count
research_fact_pack
```

Expected successful behaviour for a draft that initially breaks a known rule:

```text
editorial_guard_triggered: true
editorial_guard_corrected: true
editorial_guard_remaining_violations: []
```

If the draft still contains unsupported names, studies, healthcare-model comparisons or figures, inspect research_fact_pack before making another prompt or guard change.

Do not broaden the regex list blindly. First identify whether the problem is:

```text
research quality
fact-pack structure
initial OpenAI selection
copy-edit guard detection
copy-edit correction behaviour
```

### R. Recommended next technical decision process

Use this order:

```text
1. Test the deployed guard on the same article.
2. Read the guard diagnostics.
3. Inspect the full research_fact_pack.
4. Verify whether disputed claims are actually in verified fields.
5. Only then decide whether to change Perplexity research instructions, OpenAI selection rules or guard patterns.
```

Avoid repeatedly adding prose instructions without evidence from the diagnostics.

### S. Resume prompt for the next chat

```text
Continue Cheshire Today from the 12 July 2026 update in the single chat-source state file. Read the latest state file before any code/database/content-pool/category/newsletter/affiliate/advertising/article-generation change. We have completed the admin Open AI factual rewrite pipeline: direct source scrape first, structured Perplexity fact-pack fallback when blocked, OpenAI draft restricted to verified material, restructured professional UK-news prompt, and a deterministic editorial guard with one temperature-0 correction pass. Latest pushed commit on full-scrape-prod is 83d8d69 Expand OpenAI editorial guard patterns. The guard now detects known interpretive leads, vague attribution, generic/rhetorical endings in the final two paragraphs and selected US spellings; admin response exposes source, fact-pack and guard diagnostics. Immediate next step: after deploy, press Open AI again on the same healthy-life-expectancy article, paste the resulting draft and inspect editorial_guard_triggered, editorial_guard_corrected, editorial_guard_remaining_violations and the full research_fact_pack. Do not publish the test article merely because it reads well; verify every name, study, quote, figure and healthcare comparison. Workflow: one safe command at a time, scripted edits only, /usr/bin/grep not rg, syntax and diff checks before commit, no npm start unless asked, no automatic OpenAI publishing.
```

## 16 July 2026 — Deferred frontend maintenance

### Browserslist / caniuse-lite database refresh

Non-urgent maintenance item added after successful production frontend builds displayed:

```text
Browserslist: browsers data (caniuse-lite) is 6 months old.
npx update-browserslist-db@latest
```

Current decision:

```text
Do not update during active feature/debugging work.
The warning does not block builds or deployment.
Handle it later as a separate frontend maintenance commit.
```

Safe future workflow:

```bash
cd frontend
npx update-browserslist-db@latest
```

Then:

```text
1. Inspect package.json / package-lock.json changes.
2. Run npm run build.
3. Confirm no unexpected dependency changes or regressions.
4. Commit separately with a maintenance-only message.
```

Do not combine this dependency metadata refresh with article, archive, import, newsletter, or production bug fixes.



---

# Update – 2026-07-16 (Archive Search, Scheduler Investigation & Maintenance)

## Scheduler / Import Investigation
- Reviewed the complete scheduled pipeline:
  - `daily_article_generation()`
  - `generate_articles()`
  - `import_hybrid_news()`
  - RSS fetch pipeline
  - Daily Brief locking and newsletter batching.
- Confirmed scheduled imports request up to 12 candidates while limiting scheduled public imports to 6, with additional qualifying articles routed into Manual Review.
- Confirmed distributed locking, newsletter cursor rotation and intentional disabling of automatic hard-delete cleanup remain intact.

### Feed Architecture Audit
Verified the complete flow:

`RSS_FEEDS → _flatten_feed_groups() → fetch_feed() → fetch_all_feeds() → fetch_local_feeds_only() → fetch_local_news() → import_hybrid_news() → generate_articles() → daily_article_generation()`

Findings:
- 56 configured feeds.
- 56 flattened feeds.
- No hidden feed groups.
- No duplicate feed expansion.
- RSS configuration appears healthy and was intentionally left unchanged.

### Scheduler Behaviour
Operational observation:
- Imports are not reliably executing every scheduled run.
- This week they executed fewer than five times.
- Sometimes around 06:02.
- Sometimes around 12:00.
- Sometimes not at all.

Conclusion:
- Do **not** modify RSS feed definitions while investigating this issue.
- Future investigation should prioritise scheduler execution (Render/APScheduler/job triggering/logs) before altering feed logic.

## Archive Improvements
Reason:
- Archive contained approximately 6,311 articles.
- Existing paging made locating historical articles impractical.
- Work initiated to locate and amend the Wilmslow heritage boards article.

Backend:
- Added archive search parameter.
- Search by title.
- Search by article ID.
- Search by Mongo ObjectId.
- Search by source.
- Search by source URL.
- Reduced default archive page size from 50 to 20.
- Search-aware totals returned.

Frontend:
- Archive search box.
- Search button.
- Enter-key search.
- Clear button.
- Loading indicator.
- Matching result count.
- Improved empty-state messaging.
- Refresh workflow retained.

Verification:
- Static checks passed.
- Production frontend build passed.
- Git diff reviewed.
- Git status reviewed.
- Commit created and pushed successfully.

Deployment:
- Commit: `b3ca258`
- Message: `Add searchable archive article list`

## Deferred Maintenance
- Update Browserslist database:
  `npx update-browserslist-db@latest`
- Review dependency changes.
- Rebuild frontend.
- Commit separately from production fixes.

## Operational Reminder
Before modifying RSS feeds in future, first verify:
1. Scheduler execution.
2. Render/APScheduler timing.
3. Distributed locks.
4. Import logs.
5. Feed counts.

Do not assume RSS feeds are the root cause of intermittent imports until scheduler behaviour has been verified.

---

## Full operational update — 12–16 July 2026

### Current production and source-of-truth checkpoint

```text
Repository: CT29january26-new-website-migration
Branch: full-scrape-prod
Authoritative operational state: docs/PROJECT_STATE.md in the repository
Authoritative chat-source snapshot: this consolidated file
State migration commit: 751915b Move operational state into docs
Latest functional production commit before migration: b3ca258 Add searchable archive article list
Production health: healthy
```

Operational source rule:

```text
- Ignore Cheshire_Economic_AI_Project_Master_Feb2026.pdf for current operational decisions.
- That PDF is historical strategy only.
- Read the latest consolidated operational state first.
- The repository-backed source of truth is docs/PROJECT_STATE.md.
- Chat-source consolidated files are snapshots and must not replace the repository file once GitHub is current.
```

### 1. Admin OpenAI rewrite now cross-checks successful publisher scrapes

Test article:

```text
Mongo ID: 6a5373f217074c92eb2f31e8
Title: Chester primary shortlisted for independent school of the year
Source: Chester Standard
Source URL: https://www.chesterstandard.co.uk/news/26270079.national-award-shortlist-chester-primary-school/?ref=rss
```

Initial result:

```text
source_fetch_status: ok
source_page_content_length: 2283
research_fact_pack_available: false
editorial_guard_triggered: false
```

Root cause:

```python
if not source_page_content and source_url.startswith(("http://", "https://")):
```

Independent Perplexity research only ran when publisher scraping failed. A successful scrape prevented independent official-source verification.

Fix:

```text
- independent research now runs for every valid source URL
- publisher scrape and fact pack are compared
- official organiser/authority sources take priority
- unresolved conflicts must appear in editor notes
- publisher/social wording must not override official terminology
- workflow remains Admin-only and non-mutating until the editor presses Update Article
```

Commit:

```text
611b57d Cross-check OpenAI rewrites with independent fact research
```

### 2. Awards and official-status terminology guard

The first post-fix fact pack blended wording such as:

```text
commended/shortlisted
```

These stages must remain distinct:

```text
entered
nominated
commended
shortlisted
finalist
winner
```

Research and parser rules were tightened to:

```text
- use the official organiser's exact status term
- reject slash-separated alternatives in verified facts
- do not call an entrant shortlisted or finalist unless the organiser does
- treat official organiser/authority records as higher priority than publisher/social wording
- exclude evidence from different years, countries, organisations, institutions and events
- move unresolved status wording to uncertain_or_unverified / contradictions
```

Operational rule:

> Never publish an award-status claim until the exact official stage has been checked. “Commended” does not mean “shortlisted” or “finalist”.

### 3. Newsletter accepted-recipient send-opportunity ledger

Problem:

```text
Open/click analytics did not prove which recipients had actually been accepted by Resend during a partially successful batch.
```

Email service changes:

```text
- EmailService.last_accepted_recipients resets at the start of Daily Brief and Weekly Roundup sends
- successful Resend chunks append accepted recipients
- failed Resend chunks do not
- successful SMTP fallback sends append recipients
- provider diagnostics remain available
```

Regression test:

```text
Chunk 1: 100 accepted
Chunk 2: 100 failed with HTTP 500
Chunk 3: 5 accepted
SUCCESS_COUNT: 105
ACCEPTED_RECIPIENTS: 105
SUCCESSFUL_CHUNKS: 2
FAILED_CHUNKS: 1
```

MongoDB collection:

```text
email_send_opportunities
```

Stored fields:

```text
digest_key
tracking_id
provider
accepted_at
accepted_count
recipient_hashes
```

Privacy rule:

```text
- raw recipient email addresses are not stored
- addresses are normalised
- only the existing short SHA-256 recipient hash is stored
```

Commit:

```text
bbea335 Record newsletter send opportunities
```

Important limitation:

> Provider acceptance is a valid send opportunity, not proof of final delivery, inbox placement, bounce status, opening or readership.

Future option:

```text
Add Resend webhook ingestion for delivered, bounced, opened and clicked lifecycle events if delivery-level pruning evidence is needed.
```

### 4. Canonical public article URLs exposed through API

Problem:

```text
Social-posting workflows could find an article but could not reliably build the exact public URL before external indexing.
```

Public API fields added:

```text
articleId
slug
canonicalUrl
```

Example:

```text
ID: 6a54c53c9b216c52eb05aca8
Title: Councillors Seek Support for Jodrell Bank Amid Funding Concerns
Canonical URL: https://cheshiretoday.co.uk/article/6a54c53c9b216c52eb05aca8/councillors-seek-support-for-jodrell-bank-amid-funding-concerns
```

The backend uses the existing `_article_slug_from_title()` helper.

Commit:

```text
dbadc90 Expose canonical article URLs in API
```

Operational social rule:

```text
Use the live /api/articles feed first.
Use canonicalUrl directly when available.
Do not infer IDs from screenshots.
Do not rely on Google indexing for current article discovery.
```

### 5. Main Admin amber action now routes to Manual Review

Requirement:

```text
The amber action in the main Articles tab should send an article to Manual Review for editing, not permanent Archive.
```

Route used:

```text
POST /api/admin/articles/{article_id}/move-to-manual-review
```

Frontend changes:

```text
- added handleMoveToManualReview()
- changed confirmation title and text
- changed loading state and icon
- retained the true Archive action inside Manual Review
```

Commit:

```text
062a011 Send archived admin articles to manual review
```

### 6. Admin article ID mismatch repair

Production symptom:

```json
{"detail":"Article not found"}
```

Root cause:

```text
Some documents contain both Mongo _id and a separate UUID/custom id.
The Admin article endpoint projected Mongo _id out.
The frontend sometimes sent the stored UUID when the route needed Mongo identity.
```

Fix:

```text
- /api/admin/articles now exposes Mongo identity as mongo_id
- stored id remains unchanged for compatibility
- Manual Review action prefers article.mongo_id || article._id || article.id
```

Commit:

```text
a075a49 Fix admin manual review article IDs
```

### 7. Articles, Manual Review and Archive separated correctly

Test article:

```text
Title: Brand new primary school handed over to trust ahead of official opening
Mongo ID: 6a566b200ce41aa37200e4a3
Stored ID: 5d0b31dd-01ae-49f1-973e-87a0fc204c44
```

Problem state:

```text
manual_review_hidden_from_public: true
archived: true
archive_reason: manual_admin
```

Because Manual Review excludes archived records, the article was hidden from both queues.

Fix to move-to-manual-review:

```text
- set archived=false
- set manual_review_hidden_from_public=true
- set verification_status=needs_manual_review
- set rewrite_status=manual_review_required
- set force_live=false
- clear archived_at
- clear archive_reason
- clear archive_source
```

Fix to the main Admin Articles endpoint:

```text
exclude archived=true
exclude manual_review_hidden_from_public=true
```

Final workflow separation:

```text
Articles: live, non-review records
Manual Review: hidden, editable records awaiting review
Archive: genuinely archived records
```

Commit:

```text
1f18f9b Separate live articles from manual review
```

Live verification:

```text
- school article appeared in Manual Review
- school article disappeared from main Articles search
```

### 8. Jodrell Bank article restoration

The Jodrell Bank article temporarily disappeared because it was deliberately used for Manual Review endpoint testing.

Article:

```text
ID: 6a54c53c9b216c52eb05aca8
Title: Councillors Seek Support for Jodrell Bank Amid Funding Concerns
```

Result:

```text
- found intact in Manual Review
- restored through edit/save workflow
- returned to public API
- canonical URL verified
- article live again
```

This was a test side effect, not a random deletion.

### 9. Manual Review bulk selection and deletion

Added:

```text
- separate selectedManualReviewArticles state
- per-row tick boxes
- selected-row highlighting
- Select All / Deselect All
- Delete Selected count
- one confirmation for the whole operation
- loading state
- success and partial-failure reporting
- refresh of Manual Review, Archive and article statistics
```

The action uses the existing delete/archive-preservation route, preserving shared-link behaviour.

Commit:

```text
1dfcccc Add bulk delete for manual review articles
```

Verification:

```text
- static checks passed
- frontend production build passed
```

### 10. Searchable Archive tab

Archive size observed:

```text
approximately 6,311 records
```

Immediate target:

```text
Six new heritage boards to celebrate Wilmslow’s history unveiled this month
Article ID: 6a5106c40358c448f328f3c0
```

Backend archive search now supports:

```text
search
skip
limit
```

Search fields:

```text
title
stored article id
Mongo ObjectId
source
source_url
```

Collections searched:

```text
legacy archived records in articles
archived_articles collection
```

Other backend changes:

```text
- default page size reduced from 50 to 20
- search-aware totals
- search value returned in response
```

Frontend additions:

```text
- search input
- Search button
- Enter-key search
- Clear button
- Refresh button
- loading state
- error toast
- matching-result count
- search-specific empty state
```

Commit:

```text
b3ca258 Add searchable archive article list
```

Verification:

```text
- backend syntax passed
- git diff checks passed
- frontend production build passed
- production health returned healthy
```

### 11. Intermittent Render 512MB memory investigation

Render event:

```text
Instance: sxqq2
Failure: used over 512MB
Date: 16 July 2026
Time: 06:02 Europe/London
```

Schedules confirmed:

```text
06:00 article generation
12:00 article generation
18:00 article generation
07:30 Daily Brief Monday–Saturday
09:00–12:00 Sunday Weekly Roundup batches
```

Operational observation:

```text
- OOM does not happen every run
- sometimes near 06:00
- sometimes near 12:00
- some days have no OOM
- fewer than five incidents during the observed week
```

Pipeline reviewed:

```text
daily_article_generation()
generate_articles()
import_hybrid_news()
fetch_all_feeds()
fetch_local_feeds_only()
fetch_local_news()
fetch_feed()
```

Feed architecture verified:

```text
56 configured feeds
56 flattened feeds
no hidden feed-group expansion
```

Interpretation:

```text
56 feeds means 56 source endpoints checked for candidates.
It does not mean 56 articles are automatically imported or published.
```

Potential peak-memory contributors:

```text
- up to 10,000 active article projections loaded
- up to 10,000 archived article projections loaded
- all 56 feeds currently fetched concurrently through asyncio.gather
- one httpx.AsyncClient created per feed task
- complete response bodies/parser structures may remain until gather completes
- no explicit per-feed entry cap
- national candidate pools remain while local pools are fetched
- imported article dictionaries remain until the run finishes
- duplicate cleanup runs after generation
```

Patch decision:

```text
A proposed concurrency=4 and max 40 entries per feed patch was intentionally not applied.
```

Reason:

```text
- failures are intermittent
- per-feed caps could alter discovery
- no repeated failing stage has been proven
```

Current decision:

```text
Do not alter feed definitions, feed count or per-feed coverage yet.
Collect exact OOM timestamps and final pre-restart logs first.
If failures repeatedly occur in fetch_all_feeds, bounded concurrency alone is the preferred first mitigation.
```

Investigation order:

```text
1. Collect exact OOM timestamps.
2. Match each event to scheduled jobs.
3. Inspect final logs before restart.
4. Identify whether failure occurs during:
   - database duplicate preload
   - fetch_all_feeds
   - local-feed fetching
   - Perplexity rewriting
   - database insertion
   - duplicate cleanup
5. Apply a targeted fix only after identifying the repeated stage.
```

### 12. Deferred Browserslist maintenance

Build warning:

```text
Browserslist: browsers data (caniuse-lite) is 6 months old.
```

Decision:

```text
- non-urgent
- not a production build failure
- unrelated to current feature deployments
```

Deferred task:

```bash
cd frontend
npx update-browserslist-db@latest
```

Before committing:

```text
- inspect package.json and package-lock.json
- confirm no unexpected dependency changes
- run npm run build
- commit separately from functional production fixes
```

### 13. Repository-backed operational state migration

Historical repository files found:

```text
PROJECT_CURRENT_STATE_MASTER_MARCH_2026.md
PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260410_v3_FULL.md
```

New authoritative path:

```text
docs/PROJECT_STATE.md
```

Migration facts:

```text
- the historically maintained file was moved with git mv
- the latest 20,365-line consolidated operational file replaced its outdated contents
- the downloaded consolidated file and repository file were verified byte-for-byte
- matching SHA-256 before commit: 030471a0d5df857aa4b3f15ae3abad55721f8485e722bb3d5ad7352ca8cbf28a
- matching line count before commit: 20,365
- a small pointer remains at the former path
```

Commit:

```text
751915b Move operational state into docs
```

Push:

```text
b3ca258..751915b full-scrape-prod -> full-scrape-prod
```

Standing workflow:

```text
- docs/PROJECT_STATE.md is the only current repository operational source of truth
- read it before code/database/scheduler/newsletter/SEO/import/category/affiliate/advertising/infrastructure work
- update it after meaningful work
- commit and push it
- do not create dated replacement operational state files
- chat-source consolidated files are snapshots
- no manual state-file editing; use scripted updates with duplicate protection and diff/status checks
```

### 14. Relevant pushed commit sequence

```text
611b57d Cross-check OpenAI rewrites with independent fact research
bbea335 Record newsletter send opportunities
dbadc90 Expose canonical article URLs in API
062a011 Send archived admin articles to manual review
a075a49 Fix admin manual review article IDs
1f18f9b Separate live articles from manual review
1dfcccc Add bulk delete for manual review articles
b3ca258 Add searchable archive article list
751915b Move operational state into docs
```

All were pushed to:

```text
origin/full-scrape-prod
```

### 15. Current hard workflow and editorial memory

Technical workflow:

```text
- read the latest state first
- one safe command at a time when guiding terminal work
- scripted edits only; no manual editing
- use /usr/bin/grep, not rg
- run syntax and git diff checks before commit
- do not use npm start unless explicitly requested
- check production health after deployment
- do not broaden prompts/regex blindly; diagnose the actual stage first
```

OpenAI/editorial workflow:

```text
- OpenAI remains Admin-only
- no automatic saving or publishing
- convincing prose is not evidence of factual accuracy
- inspect source diagnostics, fact pack and guard diagnostics
- human review remains mandatory
- verify names, organisations, dates, figures, quotations and official status wording
```

Cheshire Today positioning:

```text
Local economic intelligence platform for Cheshire
```

Target editorial balance:

```text
40% Local
40% Business / Finance / Property / Economy
20% AI / Tech
```

Avoid:

```text
crime-heavy filler
weak generic national filler
low-value tragedy/traffic stories
exaggerated headlines
intrusive ad-style wording
duplicate themes too close together
```

Manual article style:

```text
professional local-news tone
avoid repeating names unnecessarily
use natural pronouns/references
tight structure
no generic filler
no unsupported interpretation
```

Social-posting workflow:

```text
- use live /api/articles feed first
- sort and assess by publishedDate
- verify canonicalUrl and public page
- prioritise today's articles
- never recommend an old article as a normal daily post
- keep platform themes consistent on the same day unless there is a strong reason not to
```

Newsletter pruning safety:

```text
- do not deactivate or delete subscribers merely because no open/click row exists
- require a valid accepted-recipient send opportunity
- provider acceptance still does not prove final delivery
- protected/internal addresses must remain excluded from pruning
```

### 16. Open follow-ups

```text
1. Verify deployed Archive search using article ID 6a5106c40358c448f328f3c0.
2. Amend the Wilmslow heritage-board article to include Wilmslow Civic Trust.
3. Continue collecting Render OOM timestamps and final pre-restart logs.
4. Do not change RSS coverage without evidence.
5. Complete exact official-status verification for award articles.
6. Add Resend webhook lifecycle handling later if delivery/bounce evidence is required.
7. Perform Browserslist maintenance separately.
8. Keep docs/PROJECT_STATE.md and the latest consolidated chat-source snapshot aligned after meaningful sessions.
```

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

# Historical Project State

This March 2026 snapshot is retained for historical reference only.
The authoritative operational source of truth is now:

- `docs/PROJECT_STATE.md`

### 12. Important command/workflow reminders

```text
- Check current state first.
- One command at a time.
- No manual file edits unless absolutely necessary.
- Prefer safe terminal/script changes.
- Use grep, not rg.
- Do not use npm start unless explicitly requested.
- Verify after each change.
- Render auto-deploy remains disabled; deploy manually when needed.
- Backend-only changes require backend Render deploy only.
- Frontend/admin UI changes require frontend/static Render deploy too.
```

### Important caution going forward

Do not undo the archived article `noindex` behaviour. It is needed to clean up thousands of old/weak imported URLs in Search Console.

Do not make `archived=True` automatically mean noindex without checking `force_live=True`. The final intended behaviour is:

- `manual_review_hidden_from_public=True` always noindex.
- `archived=True` and `force_live` not true = noindex.
- `archived=True` and `force_live=True` = indexable and sitemap-eligible.

Do not add thin/stub guide pages back into the sitemap until they have useful guide content above the current threshold.

## 18. Recommended new-chat resume prompt

Use this in a fresh chat:

```text
Continue Cheshire Today from the 30 May 2026 project state update. First check the single chat-source master state file before any code/database/content/category change. Follow the workflow: one command at a time, no manual file edits, use grep not rg, verify after each step, do not use npm start unless asked. The latest deployed fixes include: Perplexity budget-aware Manual Review queueing, public import cap handling, Manual Review Open AI button and AI details display, Force Live restoring Manual Review articles, stale status no longer re-hiding edited live articles, and RSS source-date freshness gates (3 days for Business/Finance/Tech/UK, 7 days for Local). Next priority: verify the next scheduled import does not surface stale source-dated articles, then review the remaining Manual Review queue and only publish strong local/business/finance/AI-tech candidates.
```

### L. Resume prompt for next chat after 26 June 2026 update

```text
Continue Cheshire Today from the 26 June 2026 update section in the single chat-source master state file. First check that state file before any code/database/content-pool/category/indexing change. Workflow: one command at a time, safe terminal/script changes, use grep not rg, verify after each step, no dev server unless asked. Latest key changes: OpenAI Manual Review rewrite draft flow added and pushed (ad131c7); dry-run cold subscriber report added (b2b91e9) but no cleanup allowed yet; article intro now uses visibleIntro plus Continue reading ↓ (1d762b1/87b9bb4); article guide wording softened and guide heading links now point to a real relevant /guides/<slug> not broken /guides (e1fdbe6). One sponsored/empty article from The Register, ID 6a3d5ef0323e96d2ddee7115, was removed from public view and confirmed found_public: 0. Follow-ups: check live deploy/article UX, do not link to /guides unless a real index route is built, do not deactivate newsletter subscribers until recipient delivery ledger exists, and keep OpenAI rewrite as draft-only/manual-review.
```

### M. Resume prompt for next chat after 22 June 2026 work

```text
Continue Cheshire Today from the 22 June 2026 QA/update section in the single chat-source master state file. First check that state file before any code/database/content-pool/category/indexing change. Workflow: one command at a time, safe terminal/script changes, use grep not rg, verify after each step, no dev server unless asked. Latest key commits: 398be93 added /latest-articles crawl hub; 2218069 switched sitemap/canonical to /article-index; 49a1296 relaxed local homepage editorial filter; c5475ee raised scheduled public import cap from 4 to 6; d9e0b2d added public-feed similar-title dedupe; 5a3cb1f tightened dedupe threshold and fixed duplicate Starmer homepage story. Current QA: API speed good (~1.2s), homepage count 24 from total 56 after filters, old May/April local stories still appear until more fresh public local articles build up. Do not bulk-unhide manual review articles; many are short snippets or vague local-anchor rewrites. Follow-ups: monitor next scheduled imports, inspect admin hidden Local News, secure /api/generate-articles with admin auth later, resubmit sitemap and inspect /article-index in Search Console.
```


---

### M. Resume prompt for next chat after 7 July 2026 work

```text
Continue Cheshire Today from the 7 July 2026 update in the single chat-source master state file. First check the state file before any code/database/content-pool/category/newsletter/affiliate/advertising change. Latest work completed: article intro/Continue reading/guide-heading UX commits through eba2db9; Daily Brief failure logging and Resend validation commits 5c31603 and 276f7ff; affiliate authority-page DB updates adding EMPLA to best-ai-productivity-tools-uk and Alison to best-online-gcse-a-level-courses-uk; BrickZoneHub guide created as draft best-building-renovation-supplies-uk; frontend sponsored placement label fix commit f3175f4; live active house-guide placements created for article_sidebar and article_mobile pointing to the AI productivity and online learning guides. Important: house-guide promos should display “Affiliate guide”, not “Sponsored”, after frontend deploy. Do not promote BrickZoneHub until its guide is written/QA’d/published. Known unresolved issues: import/manual-review gates can allow weak/thin RSS fallback items public; Resend key may still need replacing if validation returns 401; check house-guide impression/click counts after 24–72 hours. Workflow: one command at a time, safe terminal/script changes, use /usr/bin/grep not rg, verify after each step, no dev server unless asked.
```

# Cheshire Today — Consolidated Operational State Master

> **Authoritative operational source of truth — consolidated 10 July 2026**
>
> This file supersedes the separate Cheshire Today state-file copies that existed in the chat source.
> It combines the historical master state, the 26 June update, the 7 July update,
> the 10 July indexing update, and the latest 10 July operational work.
>
> Do not use `Cheshire_Economic_AI_Project_Master_Feb2026.pdf` as current operational truth.
> Use it only for high-level historical strategy when explicitly relevant.

## Source reconciliation

Merged from:

```text
cheshire_today_project_state_latest_UPDATED_20260526.md
cheshire_today_project_state_latest_UPDATED_20260526_UPDATED_20260530.md
cheshire_today_project_state_latest_UPDATED_20260526_UPDATED_20260707.md
cheshire_today_project_state_latest_UPDATED_20260710.md
```

Notes:

```text
- UPDATED_20260526.md and UPDATED_20260710.md were byte-identical copies despite different names.
- The 30 May/26 June file and the 7 July file shared the same historical base but had different later update sections.
- Both unique later sections have been preserved here in chronological order.
```

---

### L. Immediate next steps

1. **Resolve the GP Facebook preview/link display issue without blind changes**

Use the exact canonical URL:

```text
https://cheshiretoday.co.uk/article/6a4fd3fa1c580910e0709045/patients-reveal-easiest-gp-practices-to-contact-by-phone-in-and-around-chester
```

Check:

```text
HTTP status/redirect chain
canonical
robots
og:title
og:description
og:image
og:image response status/content-type/dimensions
Facebook Sharing Debugger fetched URL and preview
```

2. **Trace social-post URL creation**

Do not rely on broad searches that include backups/build logs. Search active source only:

```text
frontend/src
backend/server.py
backend/app
```

Exclude:

```text
*.bak*
node_modules
venv
build logs
```

Find any workflow that produces a Facebook caption with `/article/{slug}` instead of the exact live canonical URL.

3. **Add image caption support later**

After the Facebook issue is stable, add optional `image_caption` support across backend/admin/public article rendering.

4. **Continue monitoring Daily Brief**

Check future Wednesday/Thursday sends for:

```text
instance_id begins srv-
success_count > 0
provider_error is null
```

5. **Keep one state file only**

This consolidated file supersedes the separate state-file copies listed in its source reconciliation section.

## Operational update — 12–16 July 2026

### Current production checkpoint

- Repository: `CT29january26-new-website-migration`
- Branch: `full-scrape-prod`
- Baseline state migration commit: `751915b Move operational state into docs`
- Latest functional production commit before the state migration: `b3ca258 Add searchable archive article list`
- Production health: healthy
- Authoritative operational state file: `docs/PROJECT_STATE.md`

### Admin OpenAI factual cross-check
- Tested the Admin-only OpenAI rewrite flow on article `6a5373f217074c92eb2f31e8`, “Chester primary shortlisted for independent school of the year”.
- Confirmed a successful publisher scrape prevented independent Perplexity research because research only ran when `source_page_content` was empty.
- Changed the workflow so independent research runs for every valid source URL, compares publisher content with the fact pack, prioritises official sources and records contradictions.
- Commit: `611b57d Cross-check OpenAI rewrites with independent fact research`.
- Tightened award-stage terminology so entered, nominated, commended, shortlisted, finalist and winner are never blended. Slash-separated alternatives must not remain in verified fields. Official organiser terminology is authoritative.
- Operational rule: never publish award-status wording until the exact official stage is verified.

### Newsletter accepted-recipient ledger
- Added `last_accepted_recipients` tracking to Daily Brief and Weekly Roundup sends.
- Successful Resend chunks and SMTP sends add recipients; failed chunks do not.
- Added MongoDB collection `email_send_opportunities` with `digest_key`, `tracking_id`, `provider`, `accepted_at`, `accepted_count` and privacy-preserving recipient hashes.
- Regression test simulated 100 accepted, 100 failed and 5 accepted; success and ledger counts both equalled 105.
- Commit: `bbea335 Record newsletter send opportunities`.
- Limitation: provider acceptance does not prove final delivery, inbox placement, bounce status or readership. Resend webhook lifecycle ingestion remains future work.

### Canonical URLs in the public API
- Public article responses now expose `articleId`, `slug` and `canonicalUrl`.
- Verified on Jodrell Bank article `6a54c53c9b216c52eb05aca8`.
- Commit: `dbadc90 Expose canonical article URLs in API`.
- Social-posting rule: use the live API first and consume `canonicalUrl` directly rather than inferring IDs from screenshots or relying on external indexing.

### Main Admin amber action now routes to Manual Review
- Changed the main Articles-tab amber action from permanent Archive to `move-to-manual-review`.
- Updated wording, confirmation, icon and loading state.
- True Archive remains available inside Manual Review.
- Commit: `062a011 Send archived admin articles to manual review`.

### Admin article-ID mismatch repair
- Root cause: records can have Mongo `_id` plus a separate UUID/custom `id`; the Admin endpoint projected Mongo `_id` out.
- `/api/admin/articles` now exposes `mongo_id` while preserving existing `id`.
- Manual Review action prefers `article.mongo_id || article._id || article.id`.
- Commit: `a075a49 Fix admin manual review article IDs`.

### Articles, Manual Review and Archive separation
- Test article “Brand new primary school handed over to trust ahead of official opening” had both `manual_review_hidden_from_public=true` and `archived=true`, so it appeared in neither queue.
- Moving to Manual Review now sets `archived=false` and clears `archived_at`, `archive_reason` and `archive_source`.
- Main Admin Articles now excludes archived and Manual Review-hidden records.
- Result: Articles = live non-review; Manual Review = hidden editable; Archive = genuinely archived.
- Commit: `1f18f9b Separate live articles from manual review`.
- Live verification passed.

### Jodrell Bank restoration
- The Jodrell Bank article disappeared because it had deliberately been used for the Manual Review endpoint test.
- It was found intact in Manual Review and restored through edit/save.
- Public API and canonical URL were verified live again.

### Manual Review bulk selection and deletion
- Added separate Manual Review selection state, row tick boxes, selected-row highlighting, Select All/Deselect All, Delete Selected, single confirmation, loading and partial-failure reporting.
- Uses the existing delete/archive-preservation endpoint.
- Commit: `1dfcccc Add bulk delete for manual review articles`.
- Frontend production build passed.

### Searchable Archive tab
- Archive contained about 6,311 records and only exposed the newest page.
- Added server-side search across title, stored ID, Mongo ObjectId, source and source URL in both archive systems.
- Default page size reduced from 50 to 20; totals are search-aware.
- Frontend gained Search, Enter-key search, Clear, Refresh, loading state, matching count, error toast and improved empty state.
- Immediate target article: `6a5106c40358c448f328f3c0`, “Six new heritage boards to celebrate Wilmslow’s history unveiled this month”.
- Commit: `b3ca258 Add searchable archive article list`.
- Syntax, diff and production build checks passed; production health returned healthy.

### Intermittent Render 512MB OOM investigation
- Render event: instance `sxqq2`, over 512MB at 06:02 on 16 July 2026.
- Scheduled article generation runs at 06:00, 12:00 and 18:00 Europe/London.
- User confirmed failures are intermittent: sometimes 06:00, sometimes 12:00, sometimes none all day, fewer than five incidents in the observed week.
- Reviewed `daily_article_generation`, `generate_articles`, `import_hybrid_news`, `fetch_all_feeds`, `fetch_local_feeds_only`, `fetch_local_news` and `fetch_feed`.
- Confirmed 56 configured and 56 flattened feeds; no hidden feed-group expansion.
- Memory-pressure factors: up to 10,000 active and 10,000 archived projections loaded; all 56 feeds launched concurrently with `asyncio.gather`; each fetch creates its own `httpx.AsyncClient`; full response/parser structures can remain until gather completes; no per-feed entry cap; national and local pools overlap in memory.
- No RSS memory patch was applied.
- A proposed concurrency=4 plus 40-item cap patch was intentionally not run because failures are intermittent and the item cap could alter discovery.
- Decision: collect several exact OOM timestamps and final pre-restart logs. If failures consistently occur during `fetch_all_feeds`, bounded concurrency alone is the preferred first mitigation.

### Deferred Browserslist maintenance
- Build warning: `caniuse-lite` data is six months old.
- Deferred command: `cd frontend && npx update-browserslist-db@latest`.
- Inspect `package.json` and `package-lock.json`, rebuild and commit separately from production fixes.

### Repository-backed state migration
- Found historical repository state files:
  - `PROJECT_CURRENT_STATE_MASTER_MARCH_2026.md`
  - `PROJECT_CURRENT_STATE_MASTER_MARCH_2026_UPDATED_20260410_v3_FULL.md`
- Moved the actively maintained historical file to `docs/PROJECT_STATE.md` and preserved a pointer at the former path.
- Replaced its outdated contents with the 20,365-line consolidated July operational state.
- Verified the Downloads/chat-source copy and repository copy were byte-for-byte identical by SHA-256 before commit.
- Commit: `751915b Move operational state into docs`.
- Standing rule: `docs/PROJECT_STATE.md` is the only current operational source of truth. Read it first, update it in place, commit and push it. Chat attachments are historical snapshots only.

### Relevant pushed commits
- `611b57d Cross-check OpenAI rewrites with independent fact research`
- `bbea335 Record newsletter send opportunities`
- `dbadc90 Expose canonical article URLs in API`
- `062a011 Send archived admin articles to manual review`
- `a075a49 Fix admin manual review article IDs`
- `1f18f9b Separate live articles from manual review`
- `1dfcccc Add bulk delete for manual review articles`
- `b3ca258 Add searchable archive article list`
- `751915b Move operational state into docs`

### Open follow-ups
1. Verify live Archive search using `6a5106c40358c448f328f3c0`.
2. Amend the Wilmslow heritage-board article to include Wilmslow Civic Trust.
3. Continue OOM evidence collection before altering RSS coverage.
4. Complete exact official-status verification for award articles.
5. Add Resend webhook lifecycle handling later if delivery/bounce data is required.
6. Perform Browserslist maintenance separately.
7. Keep `docs/PROJECT_STATE.md` updated and pushed after every meaningful session.

---

## 17 July 2026 — Archive OpenAI rewrite-draft action

### Production validation blocker

The controlled healthy-life-expectancy rewrite validation could not be run from browser automation even after the production Admin page was authenticated.

Verified blocker:

```text
- the authenticated Admin session was available only inside the browser page;
- the browser-control evaluation environment did not expose localStorage or fetch;
- browser security policy blocked javascript: page-context execution and prohibited indirect workarounds;
- no authentication token was revealed, copied, exported or persisted;
- the rewrite-draft endpoint was not invoked;
- no article was saved, published, restored, unarchived or modified.
```

Target article:

```text
Title: We are living fewer years in good health: Is the NHS part of the problem?
Article ID: 71c315b6-292a-4b7f-8363-88e627fdde2f
Status: archived
Archive reason: auto_cap
Source: BBC News
```

### Archive UI mismatch

Manual Review already exposed the non-mutating **Open AI** action through:

```text
POST /api/admin/articles/{article_id}/openai-rewrite-draft
```

Archive rows exposed only the older `/ai-review` risk-review action, despite the documented requirement that Open AI be available in both Manual Review and Archive.

### Implemented frontend correction

`frontend/src/components/AdminDashboard.jsx` now adds a labelled **Open AI** action to every Archive row.

The Archive action:

```text
- reuses handleOpenAIRewriteDraft(article);
- calls POST /api/admin/articles/{article_id}/openai-rewrite-draft;
- uses the existing loading and error handling;
- opens the returned unsaved draft in the existing article editor;
- does not restore or unarchive the article;
- does not save or publish automatically;
- does not call the older /ai-review endpoint.
```

The older Archive risk-review action remains because it has a separate stateful purpose. Its tooltip is now **Run saved ChatGPT risk review** so it is distinguishable from the rewrite-draft action.

No backend change was required. The existing backend endpoint already locates archived articles by ID and returns a non-persisted draft.

Verification:

```text
- exact Manual Review and Archive handler references checked with /usr/bin/grep;
- git diff --check passed;
- production frontend build compiled successfully;
- no production rewrite request was made during implementation.
```

### Immediate next step

After deployment, run exactly one Open AI rewrite-draft validation on article `71c315b6-292a-4b7f-8363-88e627fdde2f` from its Archive row. Capture the complete API response and fact pack, verify every factual claim, and do not press Update Article or otherwise save or publish the draft.

---

## 17 July 2026 — Session-only OpenAI rewrite diagnostics

The deployed Archive **Open AI** action could open the returned draft, but browser automation could not capture the complete network response. Running the one permitted healthy-life-expectancy validation without preserving the fact pack and editorial-guard diagnostics would have wasted the test.

`frontend/src/components/AdminDashboard.jsx` now retains the complete successful rewrite response in temporary React state and exposes it inside the existing article draft editor through a collapsed **OpenAI Rewrite Diagnostics** section.

The read-only section displays:

```text
- editorial_guard_triggered
- editorial_guard_violations
- editorial_guard_corrected
- editorial_guard_remaining_violations
- source_fetch_status
- source_page_content_length
- research_fact_pack_available
- research_source_count
- the complete research_fact_pack
- editor_notes
- a collapsed raw view of the complete endpoint response JSON
```

An explicit **Copy diagnostics JSON** button copies only the response JSON and reports success or failure through the existing toast pattern. It does not include authentication tokens, request headers, credentials or browser storage.

Safety boundaries:

```text
- diagnostics exist only in frontend session state;
- diagnostics are not attached to articleForm or the article;
- Update Article sends only the existing articleForm payload;
- diagnostics clear when the editor closes, resets, opens Add Article or opens a normal Edit workflow;
- no backend, saving, publishing, Archive-status, risk-review or feature-flag behaviour changed;
- no production rewrite endpoint was invoked during implementation.
```

Verification:

```text
- git diff --check passed;
- production frontend build compiled successfully;
- existing Browserslist-age and Node deprecation warnings remain deferred.
```

Immediate next step: review and deploy this frontend-only diagnostics change, then run exactly one Archive-row Open AI validation for article `71c315b6-292a-4b7f-8363-88e627fdde2f`, copy the complete diagnostics JSON, and do not save or publish the draft.

---

## 17 July 2026 — OpenAI attribution guard and fact-pack identity validation

The controlled healthy-life-expectancy rewrite verification completed for archived article `71c315b6-292a-4b7f-8363-88e627fdde2f`. Factual reliability passed with one minor attribution ambiguity, but the editorial guard failed strict evaluation because it did not detect a vague plural attribution that blended National Voices evidence with Gareth Lyon's separate opinion. Nothing was saved or published.

The research fact pack also returned the malformed name `Aareth Lyon` and incomplete identities including `Rees`, `McKee` and `Sir Michael`.

Implemented backend safeguards:

```text
- extracted the deterministic rewrite editorial guard into a testable module-level helper;
- expanded vague-attribution detection, including "experts have raised concerns";
- required sentence-level named attribution and prohibited blending separate sources under collective labels;
- strengthened the existing temperature-zero correction prompt to split or remove blended attribution;
- added conservative person validation that downgrades incomplete or publisher-unsupported names without fuzzy correction;
- preserved independently researched complete identities when explicit provenance is supplied;
- added focused regression tests for detection, correction, remaining violations and person-name validation.
```

No endpoint response, database, persistence, publication or feature-flag behaviour changed.

Immediate next step: deploy the reviewed patch, then run one new controlled rewrite verification on a suitable test article before treating the guard fix as complete.

---

## 17 July 2026 — OpenAI claim-strength and certainty safeguards

A controlled rewrite verification for **Teenagers from 15 should be given free MenB vaccine, say UK experts** (`6a590e2611cd784274055b7c`) passed attribution and observed fact-pack identity validation but failed strict factual reliability. The draft strengthened qualified source claims into full protection, oversimplified population-specific cost-effectiveness analysis, changed “highly unlikely to be cost-effective” into “unnecessary”, and inferred financial implications for government.

Implemented a narrowly scoped draft-only safeguard:

```text
- the initial rewrite prompt now preserves claim strength, scope, population, uncertainty and official decision stage;
- contradictions and uncertain_or_unverified are hard limits, while unverified official status cannot be strengthened;
- unsupported motives, financial consequences and implementation or policy outcomes are prohibited;
- a deterministic guard flags a small family of high-risk absolute-certainty phrases as "absolute or unsupported certainty";
- the existing temperature-zero correction pass audits the complete draft and removes or qualifies unsupported strengthening;
- focused tests cover detection, permitted qualified wording, successful correction and reported remaining violations.
```

The admin-only endpoint, fact-pack generation, persistence, publication and article-state behaviour are unchanged. Syntax compilation and the focused rewrite-guard suite pass with 29 tests.

Immediate next step: review and deploy this patch, then run exactly one controlled rewrite-draft validation on a suitable unsaved article and inspect the complete diagnostics before making further changes.

---

## 17 July 2026 — duplicate cleanup route authentication correction

QA found that `POST /api/admin/remove-duplicates` was registered twice: the internal `_remove_duplicates_internal()` helper was unintentionally exposed without authentication before the intended authenticated `remove_duplicate_articles(...)` wrapper. The helper's route decorator was removed, while the helper and all scheduler/direct Python calls remain unchanged. Focused regression tests now verify that exactly one authenticated route remains, unauthenticated requests cannot invoke cleanup, and the helper remains directly callable. No production cleanup or data mutation was executed.

---

## 17 July 2026 — Admin authentication for content operations

QA confirmed that `POST /api/sync-rss-now`, `POST /api/fix-mismatched-content` and `POST /api/remove-product-articles` were unauthenticated even though all three active Admin Dashboard callers already supplied bearer authentication. Admin authentication was added to the existing route functions without changing their paths, business logic or response fields. Scheduler and Render cron behavior are unchanged. Focused regression tests verify one authenticated registration per route, unauthenticated `401` responses and that no RSS, Perplexity or database work starts before authentication. No production import, archive or deletion was executed.

---

## 17 July 2026 — Admin authentication for cost-bearing operations

QA confirmed that `POST /api/send-digest` and `POST /api/trigger-daily-generation` lacked Admin authentication. Scheduled Daily Brief, Weekly Roundup and article-generation jobs call internal Python functions rather than these HTTP wrappers and remain unchanged. Admin authentication was added only to the existing route signatures. Focused tests verify one authenticated registration per route, unauthenticated `401` responses and that email, subscriber database, digest-log, generation, scheduler-lock, RSS and Perplexity work cannot start before authentication. No email send or article generation was executed.

---

## 17 July 2026 — Admin authentication and response hardening for subscriber maintenance

QA confirmed that `POST /api/cleanup-subscribers`, `POST /api/cleanup-invalid-emails` and `GET /api/check-subscribers` lacked Admin authentication. The check route exposed subscriber addresses and MongoDB document IDs, while invalid-email cleanup returned the removed addresses. Admin authentication and aggregate-only responses were added without changing cleanup criteria. Newsletter signup, preferences, unsubscribe, scheduling, batching and delivery remain unchanged. Focused tests verify authentication, blocked unauthenticated database access and sanitized responses using isolated stubs. No production subscriber operation was executed.

---

## 17 July 2026 — Removal of disabled legacy image routes

`POST /api/update-local-news-images`, `POST /api/reassign-all-images-uk` and `POST /api/fix-all-images-uk` had already been permanently disabled under the RSS-only image policy. No frontend, scheduler, Render cron, tracked script, test or documented operator dependency was found. The dead wrappers and unreachable mutation bodies were removed without changing active RSS/source-image handling or image helpers. Focused tests verify that all three paths now return `404` while active article and RSS routes remain registered. No production image or article operation was executed.

---

## 18 July 2026 — Removal of unauthenticated legacy operational routes

`POST /api/test-email`, `POST /api/clean-all-articles` and `POST /api/generate-from-headline` were enabled without Admin authentication despite allowing public SMTP email sending and configuration disclosure, bulk article rewriting, and direct Gemini generation/publication. No active frontend, scheduler, Render cron, tracked script, test or documented operator dependency was found. All three routes and their route-specific bodies were removed. Authenticated email tests, Admin article editing and cleaning, hybrid imports, Manual Review, and scheduled generation remain unchanged. Focused tests confirm the POST operations are absent from OpenAPI without sending email, invoking AI, cleaning articles or changing production data. A duplicate `clean_article_content` Python function name remains in `backend/server.py`; the removed `/api/clean-all-articles` route no longer depends on the earlier helper, and the remaining naming collision was intentionally left unchanged because no current active behavior was altered. Any rename should follow a focused read-only caller audit in a later step.

---

## 18 July 2026 — Admin authentication for generation and hybrid import

`POST /api/generate-articles` and `POST /api/import-hybrid-news` previously mixed unauthenticated HTTP routing with reusable internal business logic. The unchanged generation and import logic now lives in `_generate_articles_internal(...)` and `_import_hybrid_news_internal(...)`, while thin HTTP wrappers require Admin authentication. APScheduler calls the generation helper directly, and clear-and-refresh calls the import helper directly. Import, duplicate, archive, image, Manual Review, cost, response and scheduler behaviour remain unchanged. Focused regression tests cover authentication, wrapper delegation, internal callers and frontend bearer compatibility. No production generation, import, RSS, AI or database operation was executed.

---

## 18 July 2026 — Admin authentication for legacy import routes

`POST /api/import-real-news` and `POST /api/rss/import-rss` remained unauthenticated. Importing `get_admin_auth` from `server.py` inside `rss_routes.py` would create a circular import, so the RSS POST is now registered through a factory-built protected router using the exact production dependency, while the public RSS GET routes remain unchanged. `/api/import-real-news` now directly requires Admin authentication. Importer logic, responses, scheduler and authentication internals are unchanged. Focused tests prove unauthenticated requests cannot reach RSS, Perplexity, image or database work. No production import was executed.

---

## 18 July 2026 — Newsletter ownership Stage 1 token service

The frozen newsletter ownership model uses purpose-specific signed links plus mailbox verification for public and legacy flows. Stage 1 added only an isolated token service supporting `preferences`, `unsubscribe` and `reactivate`, with fixed newsletter and 30-minute website/compatibility expiry profiles. It enforces HS256, exactly five claims, canonical UUIDv4 subscriber-management IDs, positive token versions and a 60-second clock skew. Missing or weak `NEWSLETTER_LINK_SECRET` configuration fails closed inside the service. Isolated tests cover signing, expiry, purpose separation, tampering, strict claims, identity/version validation and safe errors. No route, subscriber, migration, email builder, frontend flow or production configuration changed, and no production token, email or subscriber operation occurred. The next stage is migration tooling only, after diff approval and a deployment decision.

---

## 18 July 2026 — Newsletter ownership Stage 2 migration tooling

Stage 2 added only isolated tooling for `newsletter_management_id` and `newsletter_token_version`. The script provides read-only dry-run and guarded apply modes, with expected-count and exact interactive confirmation controls, conditional idempotent updates limited to those two fields, privacy-safe aggregate output, and explicit gated creation of the unique management-ID index. Offline tests cover validation, duplicates, conflicts, idempotency, index safety, CLI controls and protected-field invariants. No subscriber creation path, route, email builder, frontend, index or production record changed, and no production migration was executed. The next required stage is to initialise both fields in subscriber creation before any production migration run.

---

## 18 July 2026 — Newsletter ownership Stage 3 subscriber creation fields

Both public subscribe aliases use the same `subscribe_newsletter(...)` creation function. Brand-new subscriber documents now initialise `newsletter_management_id` as separate canonical UUIDv4 text and `newsletter_token_version` as integer `1`, while retaining the existing generic subscriber `id`. Existing active, inactive, reactivation and preference branches are unchanged; no existing subscriber was backfilled or modified. No token service, signing secret, tokenised route, email builder or frontend flow was activated. No migration ran, and no newsletter management index was created or activated. Isolated tests were added, and no production signup or subscriber operation occurred. The next required action is final diff review and deployment before any migration dry-run.

---

## 18 July 2026 — Newsletter ownership Stage 4A secure route contracts

Phase 1 Stage 4A added contracts for eight dormant secure newsletter-management routes. Every route returns the same generic HTTP `503`; no subscriber lookup or mutation, token verification, email send, challenge, migration or index operation occurs. Existing newsletter routes remain unchanged, and the isolated token service remains unused. Offline contract tests cover registration, validation, OpenAPI, privacy and preservation of existing routes. No production endpoint was invoked. The next stage is wiring the token service only into preference verification and secure preference updates.

---

## 18 July 2026 — Newsletter ownership Stage 4B secure preferences

Phase 1 Stage 4B implemented only secure preference-token verification and preference updates, with purpose, subscriber-management ID, positive version, version-match and active-state checks plus generic safe HTTP error mappings. Updates are conditionally restricted to the three tier fields and `preferences_updated_at`; normal updates do not change `newsletter_token_version`. The other six secure routes remain dormant. No email, challenge, legacy-route, frontend, migration or index behaviour changed. Offline tests were added, and no production endpoint or subscriber operation was invoked. Newsletter ownership security is not yet complete.

---

## 19 July 2026 — Newsletter ownership Stage 4C secure unsubscribe

Phase 1 Stage 4C implemented only secure human-confirmed and RFC one-click unsubscribe. Both routes use `unsubscribe`-purpose tokens, subscriber-management identity and positive token-version checks. Unsubscribe is soft, conditional and idempotent; it may update only `active`, `daily_brief`, `weekly_roundup`, `breaking_news`, `unsubscribed_at` and `unsubscribe_method`, and it does not increment the token version. The four remaining secure routes stay dormant; Stage 4B preference routes and all legacy routes are unchanged. No email, request-link, challenge, rate-limit, frontend, migration or index work occurred. Offline tests were added, and no production endpoint or subscriber operation was invoked. Newsletter ownership security is not yet complete.

---

## 19 July 2026 — Newsletter ownership Stage 4D secure reactivation

Phase 1 Stage 4D implemented only secure reactivation confirmation, with `reactivate`-purpose, subscriber-management identity, positive token-version and literal inactive-state checks plus explicit tier-preference selection. The conditional update preserves historical unsubscribe fields and increments `newsletter_token_version` exactly once, so replay is rejected. The three request-link routes remain dormant; Stage 4B preferences, Stage 4C unsubscribe and all legacy routes are unchanged. No email, challenge, rate-limit, frontend, migration or index work occurred. Offline tests were added, and no production endpoint or subscriber operation was invoked. Newsletter ownership security is not yet complete.

---

## 19 July 2026 — Newsletter ownership Stage 4E1 isolated link security

Phase 1 Stage 4E1 added only an isolated, unused newsletter link-security repository module. It provides privacy-safe full SHA-256 email/IP/token hashing, the frozen email and IP quotas, challenge creation and delivery state, preference eligibility and atomic single-use consumption, plus exact future index definitions with semantic conflict validation. Errors and optional fingerprints are redacted; no runtime module imports the new code, and no route, email, subscriber, migration, index, scheduler or frontend behaviour changed. Offline tests were added, no production system was accessed, and request-link flows remain dormant. The next stage is final read-only diff review before any commit.

---

## 19 July 2026 — Newsletter ownership Stage 4E2 isolated management email helper

Phase 1 Stage 4E2 added only an isolated, unused transactional newsletter-management email helper for preference, unsubscribe and reactivation purposes. It uses fixed non-personalised subjects, direct HTTPS fragment-token URLs, an injected transport and immutable privacy-safe results, with no tracking redirect, pixel, analytics, SMTP fallback, provider binding, database access, route wiring or runtime activation. Offline tests were added; no production email or endpoint was invoked, and the request-link routes remain dormant. The next stage is final read-only diff review before any commit.

---

## 19 July 2026 — Newsletter ownership Stage 4E3 preferences request-link

Phase 1 Stage 4E3 implemented only the preferences request-link route behind an explicit readiness gate that defaults off, so the route remains fail-closed. Future non-enumerating orchestration is isolated behind injected collaborators and selects only `website_preferences` for active subscribers or `reactivation` for inactive subscribers; the unsubscribe and reactivation request-link routes remain dormant. No runtime activation, production email, migration or index operation occurred, and no production endpoint was invoked. Newsletter ownership security is not yet complete.

---

## 19 July 2026 — Newsletter ownership Stage 4E4 unsubscribe request-link

Phase 1 Stage 4E4 implemented only unsubscribe request-link orchestration behind the same hard-disabled readiness gate. The future non-enumerating path uses IP-first then email rate limiting, requires valid management identity and token version for active or inactive subscribers, issues only `unsubscribe` tokens with the `website_unsubscribe` profile, creates a pending challenge, attempts one direct untracked management-email delivery and conditionally marks the challenge delivered or failed. All enabled-path outcomes return the same generic HTTP `202`, while production remains HTTP `503` with the literal gate set to `False`; the reactivation request-link remains dormant, and Stage 4B–4E3 and legacy routes are unchanged. No production endpoint, email, token, subscriber, challenge, migration, collection, index or configuration operation occurred. Newsletter ownership security is not yet complete.

---

## 19 July 2026 — Newsletter ownership Stage 4E5 reactivation request-link

Phase 1 Stage 4E5 implemented only reactivation request-link orchestration behind the same hard-disabled readiness gate. The future non-enumerating path uses IP-first then email rate limiting, permits only subscribers whose active state is literally `False`, issues only `reactivate` tokens with the `reactivation` profile, creates a pending challenge, attempts one direct untracked management-email delivery and conditionally marks the challenge delivered or failed. All enabled-path outcomes return the same generic HTTP `202`, while production remains HTTP `503` with the literal gate set to `False`; Stage 4B–4E4 and legacy routes are unchanged. No production endpoint, email, token, subscriber, challenge, migration, collection, index or configuration operation occurred. Newsletter ownership security is not yet complete.

---

## 19 July 2026 — Newsletter ownership Stage 4E6A preference challenge read

Phase 1 Stage 4E6A added subscriber-bound preference-challenge eligibility and optional session passthrough for future transactions, plus a separate literal-false confirmation-enforcement gate. When enabled only in isolated tests, preference verification requires a delivered, unexpired, unconsumed matching `preferences` challenge and remains read-only; production returns the existing generic HTTP `503` before collaborator access while the gate is false. Preference update, unsubscribe, reactivation, request-link and legacy routes remain unchanged. No collection or index was created, no migration, secret, email, frontend or production operation occurred, and isolated tests were added. Stage 4E6 is not complete.

---

## 19 July 2026 — Newsletter ownership Stage 4E6B preference challenge consumption

Phase 1 Stage 4E6B added subscriber-bound, single-use challenge consumption for secure preference updates behind the unchanged literal-false enforcement gate. When enabled only in isolated tests, the subscriber is re-read and revalidated inside one transaction that consumes the matching challenge and conditionally updates only the three tier preferences plus `preferences_updated_at`; the token version remains unchanged, replay is rejected, transaction failures roll back both operations where the transaction outcome is known, and indeterminate commit outcomes fail closed without claiming rollback certainty. Stage 4E6A preference verification and all other routes remain unchanged. Production continues to return the generic HTTP `503`; no migration, index, secret, email, frontend, collection creation or production operation occurred, and isolated tests were expanded. Stage 4E6 is not complete.

---

## 19 July 2026 — Newsletter ownership Stage 4E6C unsubscribe challenge consumption

Phase 1 Stage 4E6C added transactional, subscriber-bound challenge consumption for human-confirmed and RFC one-click unsubscribe behind the unchanged literal-false enforcement gate. Active subscribers consume the matching challenge and soft-unsubscribe in one transaction; literal inactive subscribers may consume an eligible challenge without another subscriber update, human replay fails, and RFC replay remains safely idempotent only for a confirmed inactive subscriber. Only the approved unsubscribe fields may change, the token version remains unchanged, known transaction failures roll back challenge and subscriber changes, and indeterminate commit outcomes fail closed without claiming rollback certainty. Production remains HTTP `503`; Stage 4E6A/B, request-link, reactivation and legacy routes are unchanged, and no migration, index, secret, email, frontend, collection creation or production operation occurred. Isolated tests were expanded. Stage 4E6 and Phase 1 are not complete.

---

## 19 July 2026 — Newsletter ownership Stage 4E6D reactivation challenge consumption

Phase 1 Stage 4E6D added transactional, subscriber-bound challenge consumption for secure reactivation behind the unchanged literal-false enforcement gate. Only literal inactive subscribers are eligible; challenge consumption, explicit preference selection, reactivation audit fields and a single token-version increment occur with the subscriber update in one transaction while historical unsubscribe fields remain intact, and replay is rejected. Known transaction failures roll back challenge and subscriber changes, while indeterminate commit outcomes fail closed without claiming rollback certainty. Production remains HTTP `503`; Stage 4E6A–C, request-link and legacy routes are unchanged, and no migration, index, secret, email, frontend, collection creation or production operation occurred. Isolated tests were expanded. Stage 4E6 and Phase 1 are not complete.

---

## 19 July 2026 — Newsletter ownership Stage 4F1 runtime collaborators

Phase 1 Stage 4F1 added lazy production collaborator wiring over the existing application database, Motor client and email-service owner: challenge and rate-limit repositories select only their reviewed collections, transactions reuse the existing client, and the management-email adapter performs one untracked Resend attempt with no retry or SMTP fallback. Privacy-safe readiness booleans perform no I/O, no collection or index is created automatically, and both readiness gates remain literal `False`, so startup and all public secure-route behavior remain fail-closed without the signing secret. No migration, index, secret, email, frontend, legacy-route or production operation occurred; isolated tests were added and obsolete isolation assertions were updated. Activation readiness is not complete.

---

## 20 July 2026 — Newsletter ownership Stage 4F2 guarded index tooling

Phase 1 Stage 4F2 added one isolated synchronous provisioning script for the four reviewed challenge and request-limit indexes, with read-only dry-run, interactive exact-confirmation apply, strict existing-definition conflict rejection, post-create rediscovery, full final verification and privacy-safe aggregate output. The script is not imported by runtime code and no database, production index, collection document, gate, secret, route, scheduler, migration or production behavior changed; offline tests were added. The indexes have not been created and activation readiness is not complete.

---

## 20 July 2026 — Newsletter ownership Stage 4F3 frontend fragment consumers

Phase 1 Stage 4F3 added the three frontend consumers for secure preferences, human unsubscribe and reactivation links. Each captures only the canonical fragment token into component memory, immediately removes the fragment from browser history, never renders or persists it, uses the reviewed secure endpoints, requires explicit user action before mutation and presents privacy-safe accessible failure states; the browser never invokes RFC one-click unsubscribe. Backend code, gates, secrets, email, migration and indexes remain unchanged, no production endpoint was invoked, and focused offline frontend tests were added. Production activation and Phase 1 remain incomplete.

---

## 20 July 2026 — Newsletter ownership Stage 4F4 legacy cutover

Phase 1 Stage 4F4 was committed as `85bc971efe9b36afa2edefbac6dbef65fc7f1048`, deployed and verified healthy in production. It retired public email-only preference and unsubscribe routes, prevents signup-based reactivation of existing subscribers, provides privacy-safe legacy-link retirement and explicit secure request-link forms, and uses clean untracked routine management URLs. First-time signup and authenticated Admin operations remain available, all secure routes remain behind the two literal-false gates, and outbound RFC one-click headers remain fail-closed because the synchronous routine-delivery paths cannot yet guarantee subscriber-bound challenge persistence and per-recipient headers. No migration, newsletter index provisioning, secret configuration, email delivery or production-data mutation occurred; activation remains incomplete.

---

## 20 July 2026 — Newsletter challenge enforcement activation

After the approved subscriber migration, newsletter index provisioning and signing-secret configuration, `NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED` was changed to literal `True`. `NEWSLETTER_REQUEST_LINKS_ENABLED` remains literal `False`, so request-link issuance stays unavailable while secure confirmation routes enforce subscriber-bound challenges. No migration, index, email or production-data operation was performed in this step.

---

## 20 July 2026 — Newsletter request-link activation

After challenge enforcement was deployed and verified healthy, `NEWSLETTER_REQUEST_LINKS_ENABLED` was changed to literal `True`. Both newsletter activation gates are now enabled in source. No migration, index, email or production-data operation was performed in this step.

---

## 20 July 2026 — Newsletter request-limit reservation correction

After the activated request-link path exposed MongoDB's prohibition on `$expr` in an upsert predicate, request-link issuance was disabled again while challenge enforcement remained enabled. The rate-limit repository now reserves an eligible existing record with a non-upsert conditional update and creates only a genuinely absent record with an insert protected by the existing compound unique index; duplicate insert races are classified from the stored rolling-window state. Quotas, rolling-window pruning, indexes, privacy-safe fail-closed behavior and request-link orchestration are unchanged. This correction was verified locally only; no deployment or production operation occurred.

---

## 20 July 2026 — Newsletter request-link reactivation

After the corrected request-limit reservation was deployed healthy, `NEWSLETTER_REQUEST_LINKS_ENABLED` was restored to literal `True` for controlled production verification. Challenge enforcement remains enabled; no migration, index or configuration change was performed in this step.

---

## 20 July 2026 — Newsletter Security Phase 1 completed

Newsletter Security Phase 1 is complete and operational in production. All 14,265 subscriber records were migrated successfully with valid management IDs and token versions; the unique management-ID index and all four reviewed challenge and request-limit indexes were created and verified without conflicts. `NEWSLETTER_LINK_SECRET` is configured, MongoDB transaction capability was confirmed, and both `NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED` and `NEWSLETTER_REQUEST_LINKS_ENABLED` are enabled.

Controlled production testing verified secure preferences retrieval and updates, secure unsubscribe, secure reactivation, single-use challenge consumption, replay rejection, privacy-safe non-enumerating responses, fragment-token handling and management-email delivery. The request-limit `$expr` upsert incompatibility was corrected and deployed, after which challenge creation and provider delivery succeeded. Legacy public email-only management routes remain retired, signup cannot reactivate existing inactive subscribers, and routine management links contain no recipient email or click-tracking wrapper.

Outbound RFC one-click unsubscribe headers remain deferred pending a safe per-recipient provider/header lifecycle. Minor unsubscribe/reactivation success-state presentation improvements are tracked as optional UX polish and do not block the completed secure production operation.

---

## 21 July 2026 — Cheshire Today Design System v2 progress

Phase 2 began from the completed `newsletter-security-v1.0` baseline using the existing React/Tailwind/component architecture rather than rebuilding the website. Work followed the approved small-change workflow with local production builds and real iPhone review before each checkpoint.

### Homepage editorial redesign

Commit `bb925f1` redesigned the homepage hero and Top Stories presentation and reordered the opening reader flow to:

1. Hero
2. Top Stories
3. Newsletter
4. Sponsored placement
5. Practical monetisation strip
6. Latest

The hero now uses stronger editorial typography, improved metadata hierarchy, responsive image proportions and accessible focus styling. Top Stories was reduced to four curated items and converted from boxed cards to a cleaner publisher-style list.

Commit `3c1ce55` added the reusable `SectionHeader` component and an isolated `editorial` variant for `CompactArticleCard`. Latest, Business & Finance and More Stories now share the same editorial section language and card presentation. Article-page sidebars, horizontal cards and existing `LeadSection` usage were left unchanged.

### Article page editorial redesign

Commit `a529791` redesigned the active `ArticlePageV2` header and reader flow. Changes include:

- Playfair editorial headline typography
- category and optional location hierarchy
- Cheshire Today organisational byline
- clearer date and reading-time metadata
- accessible Share control
- removal of the redundant Back link
- improved hero-image spacing
- shared editorial `SectionHeader` and card styling for main-column More Stories
- newsletter signup moved below the complete More Stories section

Existing SEO schema, source attribution, body content processing, guides, adverts, sidebar modules and article business logic were preserved.

The redesigned homepage and article page were verified through successful production frontend builds and real iPhone testing before commits and deployment.

### Facebook and Open Graph image correction

Commit `93d78b3` corrected Newsquest social-preview images for article crawler HTML. For recognised Newsquest source pages whose stored article image is a generic `/resources/images/` asset, the crawler path now retrieves and uses the source page's declared Open Graph image where available.

A focused isolated regression test was added in `tests/test_article_social_metadata.py`. It uses no real database or network access and confirms that the generated `og:image` and `og:image:secure_url` use the source Open Graph image rather than the smaller generic resource URL.

Verification completed:

- `backend/server.py` passed Python compilation.
- Focused regression test passed.
- Production remained healthy.
- Facebook crawler output was verified live for article `6a5e5434ff602e15f40d4225`.
- Live metadata now returns the article-specific canonical URL, title, description and the source-provided 1200 × 630 Newsquest Open Graph image.

### Article-body reader experience

Commit `6a350f0` refined the active `ArticlePageV2` reading experience after a read-only review of the existing helper history, prior article-flow fixes and current live article data.

The review confirmed that many current articles contain both an editorial summary and a complete body whose opening paragraph already covers the same facts in different wording. The previous exact-text comparison could not recognise that semantic overlap and therefore prepended the visible intro to the full body, producing duplicated openings.

The correction is deterministic:

- when full body content exists, it is rendered unchanged
- the visible intro is used only when no body content exists
- SEO description and visible standfirst generation remain unchanged
- stored article content is not modified
- mobile preview, attribution, guides, adverts, newsletter and related-story logic are preserved

The full body was also changed from an application-style rounded card to a restrained editorial reading column with subtle horizontal rules, small mobile-only horizontal padding and tighter mobile paragraph rhythm. The desktop reading measure was subsequently refined from `max-w-3xl` to `max-w-2xl` after production builds and localhost visual review.

Verification completed:

- historical commit `eba2db9` and the current chat-source state history were reviewed before changing body-flow logic
- live summary and body fields were compared across a sample of current articles
- the duplicate opening was removed on the farm-shop test article
- mobile body width, paragraph spacing, article ending, source attribution and More Stories flow were reviewed on a real iPhone
- the production frontend build compiled successfully
- `frontend/.env.production.local` was restored after local testing

### Current repository checkpoint

- Branch: `full-scrape-prod`
- Current local and remote commit: `7195e8c`
- `AGENTS.md` remains intentionally untracked
- Newsletter Security Phase 1 remains complete and operational

### Next approved Phase 2 focus

Continue only with confirmed reader-experience findings. The next priority is a read-only editorial typography and content-format audit covering:

- subheading presentation
- ordered and unordered lists
- inline-link presentation
- blockquotes where present
- image captions and credits where supported by article data
- remaining homepage and cross-site editorial consistency

Do not reintroduce semantic or fuzzy duplicate-intro detection. Preserve existing article content, SEO, attribution, advertising, guide, newsletter and monetisation logic unless a confirmed issue requires a narrowly scoped change.

---

## 21 July 2026 — Newsquest image pipeline and historical backfill completed

Commit `3f4ab10` added an isolated Newsquest image resolver and wired it only into future local Chester Standard and Warrington Guardian RSS imports. Recognised legacy `/resources/images/` assets are now resolved once from the source page's declared Open Graph image, stored as the canonical article image and reused by the website, article pages, cards, newsletters, RSS output and social publishing. Non-Newsquest images and all lookup failures preserve the original URL.

Commit `c1356ea` added a guarded historical backfill tool with deterministic dry-run, exact expected-count apply, interactive confirmation, conditional image-only updates, post-write verification and aggregate privacy-safe output.

Production execution completed successfully:

- initial candidate count: `320`
- dry-run scanned: `320`
- images resolved: `320`
- updates planned: `320`
- lookup failures: `0`
- conditional conflicts: `0`
- verification failures: `0`
- records updated: `320`
- apply status: `verified`

A post-migration dry-run returned `updates_planned: 0`, confirming the operation is idempotent. Live API checks verified previously affected Chester Standard articles now return source Open Graph image URLs, including the publisher's own crop parameters where supplied.

Only the `image` field changed. Article content, metadata, IDs, timestamps, SEO, attribution, newsletter, advertising and monetisation logic were preserved.

---

## 22 July 2026 — Desktop article layout and sidebar advertising refinement

Commit `cc092bc` removed ineffective sticky positioning from the complete desktop article sidebar. The sidebar stack includes related reporting, guides, advertising, Latest, affiliate content and newsletter modules and was substantially taller than the viewport, so normal page scrolling now provides more predictable behaviour.

Commit `7195e8c` refined the desktop article composition:

- article body reading measure reduced from `max-w-3xl` to `max-w-2xl`
- existing `article_sidebar` sponsored placement moved to the top of the sidebar
- optional `prominent` presentation added to the shared `SponsoredPlacement` component
- article advertising retains separate `article_sidebar` inventory, API lookup, campaign tracking and analytics
- prominent presentation reuses the homepage sidebar card scale without sharing homepage inventory
- temporary sidebar top padding was removed after final alignment review
- only one desktop article sponsored placement remains

Verification completed through successful production frontend builds, repeated localhost desktop review, aligned local and remote commit `7195e8c`, and a healthy production service.

Article content, SEO, attribution, guides, newsletter logic, advert inventory, campaign tracking and monetisation behaviour were preserved.

---

## 22 July 2026 — Facebook Contentful social preview correction

Commit `387d157` permanently corrected Facebook/Open Graph previews for articles using Contentful-hosted images.

Investigation followed the QA-first workflow and deliberately avoided introducing new image proxy endpoints or broad crawler changes. Live verification established that crawler HTML, canonical URLs and Open Graph metadata were already functioning correctly. The remaining Facebook warning was isolated to the Contentful image transformation used for social metadata.

Root cause:

- Facebook Sharing Debugger intermittently rejected the previous transformed Contentful image (`w=800&h=600`) with an "Image Too Small" warning despite the decoded image exceeding the documented minimum dimensions.
- Independent verification confirmed the Contentful Images API could generate a valid dedicated social image at `1200 × 630`.

Production correction:

- only Contentful-hosted social images are rewritten during crawler HTML generation
- Contentful images now request:
  `?fm=jpg&w=1200&h=630&fit=fill&q=85`
- BBC, Guardian, Reach, Newsquest and all other image normalisation logic remains unchanged
- no proxy endpoint, database migration or frontend change was introduced

Regression protection:

- added focused regression coverage in `tests/test_article_social_metadata.py`
- existing Newsquest regression retained
- new regression confirms Contentful social metadata emits the dedicated `1200 × 630` image URL

Verification completed:

- `backend/server.py` compiled successfully
- focused regression suite passed (`2 passed`)
- commit deployed successfully to production
- live crawler output verified using the Facebook crawler user-agent
- Facebook Sharing Debugger confirmed the previous "Image Too Small" warning was resolved
- remaining `fb:app_id` advisory intentionally left unchanged because Cheshire Today does not currently use a Meta App ID

Repository checkpoint:

- branch: `full-scrape-prod`
- production commit: `387d157`

---

## 22 July 2026 — Reader experience, guide completion and RSS paragraph preservation

### Stored editorial paragraph rendering

Commit `1c594f6` removed the frontend's artificial three-sentence regrouping and restored preservation of the paragraph structure already stored in each article.

The live article-detail audit confirmed that current articles contain meaningful blank-line paragraph boundaries. `ArticlePageV2` now renders those boundaries directly rather than making editorial decisions in the presentation layer.

Verification completed:

- production frontend build passed
- manual/rewrite article reviewed locally and in production
- imported Business article reviewed in production
- one-sentence transition paragraphs remained separate
- article ending and source attribution remained correctly positioned
- SEO, guides, newsletter, advertising and monetisation behaviour were preserved

### Public guide-page completion

Commit `cb8ecb6` corrected the public `AuthorityPage` presentation without redesigning the guide architecture.

Changes:

- added the existing Cheshire Today `NewsHeader`
- stopped displaying raw workflow status such as `PUBLISHED`
- stopped displaying null-like category values such as `none`
- stopped inventing default `AI` or `Affiliate supported` labels when metadata is absent
- removed the unfinished reader-facing placeholder stating that tools were still being filled in
- retained `Affiliate supported` only for genuine affiliate-mode guides

Production verification completed on:

- `/guides/best-savings-accounts-uk`
- `/guides/best-accounting-software-uk`

Verified preserved behaviour:

- guide titles, introductions and editorial sections
- valid Best Pick and provider modules
- affiliate destinations and disclosures
- related guides
- newsletter
- footer
- canonical, Open Graph and JSON-LD metadata
- responsive and dark-mode behaviour

### Phase 3A RSS paragraph preservation

Commit `0aa8eea` refined `sanitize_rss_text()` so successful Perplexity rewrites retain meaningful upstream paragraph boundaries.

Current contract:

- recognised source URLs and source-link tails are still removed
- summaries use explicit compact single-block mode
- bodies containing two or more meaningful paragraphs preserve those paragraphs
- only genuinely single-block RSS text receives deterministic fallback paragraph construction
- common abbreviations, initials, decimal figures and conventional quotation attribution are protected from obvious false sentence boundaries
- applying the sanitizer repeatedly produces the same result

All ten active callers now explicitly distinguish body and summary sanitation.

Regression coverage:

- new focused suite in `tests/test_rss_text_sanitization.py`
- sanitizer suite passed: `25 passed`
- existing OpenAI/editorial guard suite passed: `29 passed`
- combined directly related backend verification: `54 passed`
- Python compilation passed
- `git diff --check` passed

Production status:

- service health confirmed after deployment
- scheduler confirmed running normally
- no existing stored articles were migrated or rewritten
- no article created after the deployment has yet passed through the updated sanitizer
- final end-to-end verification remains pending on the first acceptable post-deployment RSS import, expected from a normal scheduled run

### Repository checkpoint

- branch: `full-scrape-prod`
- latest production commit: `0aa8eea`
- `AGENTS.md` remains intentionally untracked

---

## 23–24 July 2026 — Editorial safety, newsletter presentation, indexing recovery and Admin operational safety

This update consolidates all verified work completed after the `0aa8eea` checkpoint. Work continued on `full-scrape-prod` using the QA-first workflow: read the operational state, inspect the current branch and diff, make one narrow change at a time, run focused regressions before broader verification, inspect the final diff, then commit, push and allow the production deployment to complete. No production mutation was used to validate code-only changes unless explicitly recorded below.

### Operational workflow and repository state

The following workflow decisions remained in force:

- `docs/PROJECT_STATE.md` remains the operational source of truth.
- `AGENTS.md` remains intentionally untracked and was excluded from every commit.
- OpenAI remains Admin-only, draft-only and never auto-publishes.
- Article sanitation, factual safeguards, Manual Review, image handling, SEO, newsletter, advertising, guides and monetisation contracts were preserved unless a narrowly identified defect required a change.
- Production-sensitive changes were verified locally before commit and push.
- Frontend production builds were used instead of `npm start`.
- Read-only shadow tools remained isolated from production imports, MongoDB writes and live source configuration.
- Current local `HEAD` and `origin/full-scrape-prod` are aligned at `a2421d6ea735cc3b372ec3bb93d1a8b407fa59a7`.

### Project-state reconciliation

Commit `86a971d` recorded the already approved guide-completion and RSS paragraph-preservation work in this operational file. It did not change runtime behavior.

### Editorial publication safety

Commit `4860158` — `Guard Admin RSS sync before publication`

The authenticated `POST /api/sync-rss-now` insertion path was brought under the existing article sanitation and AI/manual-review guard immediately before insertion.

Verified behavior:

- body content uses `sanitize_rss_text(..., is_summary=False)`
- summaries use compact `is_summary=True` sanitation
- the existing 1,000-character floor remains in force
- `apply_ai_manual_review_guard(..., ai_rewrite_used=True)` runs before insertion
- safe articles retain the existing public insertion behavior
- flagged articles are retained in the established hidden Manual Review state rather than discarded or published
- title, source, source URL, image, category, scope, location and publication metadata remain unchanged
- duplicate handling, scheduler and hybrid-import behavior remain unchanged
- no OpenAI call was introduced

Focused offline coverage was added in `tests/test_sync_rss_editorial_guard.py`.

Commit `b1d0923` — `Guard short Cheshire fallback imports`

The Perplexity Cheshire-search fallback inside `_import_hybrid_news_internal()` had been able to publish a two-sentence article with an empty summary and no guard metadata. The affected production article was moved to Manual Review using the existing Admin workflow before the correction.

The fallback branch now:

- preserves body and summary sanitation
- applies the existing AI/manual-review guard
- sends short, repetitive, invention-risk or otherwise weak fallback output to Manual Review
- retains useful weak records rather than silently discarding them
- preserves image, source, source URL, category, scope, publication date and duplicate handling
- accounts for `public_imported` and `manual_review_imported` from the final guarded visibility state
- introduces no OpenAI call or prompt change

Focused offline coverage was added in `tests/test_hybrid_perplexity_fallback_guard.py`.

### Newsletter HTML foundation and visual system

Commit `7b1aeef` — `Repair newsletter digest HTML foundations`

A read-only Daily Brief and Weekly Roundup rendering audit identified malformed HTML, unsafe unescaped dynamic content and unreliable Weekly logo handling. The repair:

- balanced the existing newsletter HTML structure
- replaced the broken/unreliable Weekly logo reference with the verified Cheshire Today text masthead
- added explicit HTML escaping helpers for dynamic text and attributes
- retained article URLs, tracking URLs, preferences links, unsubscribe links and tracking pixels
- changed no scheduling, recipient selection, sending, batching or analytics logic

Offline HTML regression coverage was added in `tests/test_newsletter_digest_html.py`.

Commit `5099ddb` — `Refresh Daily Brief and Weekly Roundup design`

Newsletter Phase 4B refreshed presentation without changing newsletter operations.

Implemented:

- derived `frontend/public/cheshire-today-email-logo.png` from the official logo without replacing the source artwork
- optimised email logo size: 38,904 bytes
- shared Daily/Weekly masthead, shell, content width, blue palette, spacing, typography, CTA language and footer treatment
- compact editorial headers with edition name, date and `Local · Business · Finance`
- hidden inbox preheaders for Daily and Weekly
- refined Daily hero image/headline/excerpt and added the existing tracked `Read the full story →` CTA
- converted sparse Daily secondary rows into linked headline/excerpt rows
- aligned Weekly Big Read and ICYMI presentation without changing story selection or order
- added deterministic plain-text Daily and Weekly versions with clean canonical article URLs plus preferences/unsubscribe URLs
- added the smallest Admin control for the already existing authenticated Weekly test endpoint

The Admin control did not expose batch testing or create a new endpoint. Scheduling, send locks, ledgers, provider behavior, tracking, subscriber selection and article ranking remained unchanged.

Commit `1c78345` — `Polish newsletter masthead and weekly story summaries`

Newsletter Phase 4C applied final presentation-only refinements:

- displayed the existing email logo at approximately `150 × 51`
- increased Daily/Weekly edition-title prominence without materially increasing header height
- reduced Daily and Weekly hero headline size and line-height for cleaner mobile wrapping
- added compact escaped excerpts beneath the existing five Weekly ICYMI headlines
- preserved ICYMI ordering, tracked links, Big Read selection, CTA markup and plain-text output

Commit `06830ab` — `Refine newsletter headlines and excerpt truncation`

Newsletter readability was refined further:

- Daily hero and Weekly Big Read headlines now use `22px/28px`
- `_email_story_excerpt()` now truncates at a complete word
- truncated excerpts end with exactly one Unicode ellipsis
- trailing spaces, commas, semicolons, colons, full stops, hyphens/dashes and existing ellipsis characters are removed before the terminal ellipsis
- an unusually long first token returns that complete token plus one ellipsis rather than only `…`
- naturally completed excerpts remain unchanged
- HTML escaping, plain-text behavior and tracking links remain unchanged

Focused regressions cover existing ellipses, terminal punctuation, long first tokens, normal word-safe truncation and naturally completed text.

### Read-only Cheshire source and ranking evaluation

Commit `9d56c76` — `Add read-only Cheshire RSS ranking evaluators`

Two isolated offline/read-only tools were added:

1. `backend/scripts/evaluate_cheshire_rss_shadow.py`
2. `backend/scripts/evaluate_story_ranking_shadow.py`

The Cheshire RSS shadow evaluator:

- evaluates candidate Nantwich News and Newsquest feeds without changing production source configuration
- reports fetch/XML status, freshness, town relevance, image availability, acceptance and grouped rejection reasons
- validates content type/body before parsing and safely rejects HTML error pages
- canonicalises URLs and compares configured-feed baselines
- allows only accepted candidate items to influence later candidate deduplication
- records concise aggregate diagnostics without publisher bodies or private data
- supports module CLI execution
- guarantees zero database writes

The story-ranking shadow evaluator:

- groups related candidate stories without changing the importer
- scores transparent configurable factors such as locality, original reporting, business value, image quality, freshness and syndication
- compares current stable-order selection with the shadow preferred story
- records factor breakdown, assessment provenance, input position and ordering tie-break effects
- uses stable group IDs
- prevents transitive probable-headline chains from over-clustering unrelated A/B/C candidates
- distinguishes hard grouping evidence from heuristic grouping
- rejects article-body fields and unknown/overlong assessment provenance
- performs no network or database work

Comprehensive synthetic offline suites were added for both evaluators. No live feed run, production import, source-config change or database operation occurred as part of implementation.

### Article canonical identity and indexing recovery

Commit `98d582f` — `Consolidate article canonical identity`

Mongo ObjectId is now the single canonical public article identity:

`/article/{mongo_id}/{canonical_slug}`

Compatibility behavior:

- full internal-UUID article URLs redirect permanently to the Mongo-ID canonical URL
- UUID ID-only and UUID stale-slug URLs redirect to the same current Mongo canonical
- Mongo-ID ID-only and stale-slug URLs retain their canonical redirects
- unknown UUIDs retain not-found behavior and never redirect to the homepage
- sensitive or tracking query values are not forwarded
- crawler and ordinary-browser routes converge on the same canonical destination
- archived URLs preserve reachable `noindex,follow`
- force-live articles remain indexable
- Manual Review records remain protected
- the sitemap continues to emit Mongo-ID URLs only

Focused canonical-route coverage was added without migrating article data or stored identifiers.

Commit `608ed7b` — `Align public hub taxonomy and routing`

The public category/location inventory was aligned across React routes, navigation, crawler hubs and sitemap output.

Stable category URLs remain:

- `/category/local-news`
- `/category/uk-news`
- `/category/business`
- `/category/finance`
- `/category/ai-tech`

Reader-facing labels are:

- Local
- UK
- Business
- Finance
- AI & Tech

Canonical stored/read mapping:

- Local News accepts Local, with genuine Cheshire/local evidence still required
- UK News accepts UK and does not absorb specialist categories merely because `scope=uk`
- Business accepts Economy and Economic
- Finance accepts Tax, Property, Property & Tax and Money
- AI & Tech accepts AI, Tech and Technology, but not generic Science

Specialist category precedence now prevents Finance, Business and AI & Tech stories with UK scope from being misclassified into UK. Public hub retrieval deduplicates article IDs, displays counts from the filtered visible collection and uses article titles as image alt text. Empty supported hubs render an explicit empty state rather than homepage content. No Mongo category migration or public URL change was introduced; Admin write normalization and related-story normalization remain separate follow-up work.

Commit `0cf67e9` — `Return real 404s for unsupported routes`

Unsupported public routes now return genuine not-found behavior rather than masquerading as the homepage. Valid article, guide, category, location, Admin and secure-management routes were preserved. Focused reader/crawler regressions were added.

Commit `13be6af` — `Use truthful sitemap lastmod dates`

Sitemap `lastmod` values now come from truthful per-resource timestamps with strict parsing and safe omission when no reliable timestamp exists. The change removed misleading generated timestamps while preserving sitemap inventory, canonical URLs and visibility rules.

Commit `ffd4a52` — `Fix homepage story allocation`

Homepage allocation was corrected without redesign:

- specialist category classification takes precedence over generic UK scope
- section allocation better preserves the intended public taxonomy and 40/40/20 strategy
- duplicated or conflicting section assignment was reduced
- article ordering, cards and public route contracts remained stable

Focused homepage regression coverage was added.

### Legacy article-route hardening

A read-only pipeline and route-usage audit distinguished trusted manual editing from automated publication risk. It confirmed:

- the hybrid importer and Admin OpenAI draft workflow remain the preferred guarded paths
- `POST /api/admin/regenerate-recent-content` has documented operational use but lacked modern sanitation/guarding
- `POST /api/import-real-news` had no repository frontend, scheduler, script or internal caller but remained reachable through direct authenticated API use
- unrelated legacy routes were not removed without usage evidence

Commit `1034bb9` — `Guard recent article regeneration`

The authenticated recent-regeneration route now:

- rejects empty, too-short or shorter-than-existing output before mutation
- sanitises accepted proposed body content
- applies the existing AI/manual-review guard
- calculates the complete outcome before one deliberate update
- preserves article metadata and existing selection window/limit
- updates regeneration metadata only for accepted updates
- routes risky rewrites into the established Manual Review state
- introduces no OpenAI call, prompt, new schema or retry

Commit `50bf9c6` — `Guard legacy real-news import`

The authenticated legacy `POST /api/import-real-news` compatibility route now:

- sanitises body and compact summary before insertion
- applies the shared guard with `ai_rewrite_used=False`
- retains safe full-quality records publicly
- retains short useful or risky records in Manual Review
- skips empty/unusable content
- preserves duplicate-title/source-URL handling and source/category/image/date/location metadata
- performs one insertion maximum per retained candidate
- introduces no new AI call, prompt or retry

The route-specific short-content reason was removed after QA confirmed the shared guard already supplies the established public-quality-floor reason. Short records now contain exactly one floor reason, while separate invention/editorial checks remain present once where applicable.

### Admin archive request and action safety

Commit `4622edf` — `Fix Admin bulk archive thresholds`

The Admin displayed 7-, 14- and 30-day Bulk Archive controls but sent `days_old` in the query string while the backend expected JSON, causing all actions to use the 30-day default.

The frontend now:

- sends `{ "days_old": 7 }`, `{ "days_old": 14 }` or `{ "days_old": 30 }` in the authenticated POST body
- confirms the exact threshold before the request
- sends no request on cancellation
- reports the requested threshold and actual `articles_archived` count
- consistently says archive rather than delete
- exposes no private backend error detail

Backend selection logic and archive behavior were unchanged.

Commit `f8858ec` — `Correct Admin archive actions and import results`

This commit was pushed to `origin/full-scrape-prod`, deployed and verified as part of the normal production workflow.

Corrections:

- Articles-tab `Archive Selected` now calls the existing authenticated single-article archive endpoint once per selected ID
- cancellation preserves selection and sends no request
- full and partial outcomes report archived/failed aggregate counts
- successfully archived IDs are cleared; failed IDs remain selected
- article, archive and statistics data refresh after accepted results
- no DELETE endpoint or age-based bulk endpoint is used
- archive actions now say Archive where the backend archives
- genuine permanent-delete controls for unrelated resource types remain unchanged
- hybrid import completion always produces a visible result for public-only, Manual-Review-only, mixed and zero-retained outcomes
- retained count uses `public_imported + manual_review_imported` whenever valid detailed fields exist
- `total_imported` is only a compatibility fallback when both detailed fields are absent/invalid
- valid estimated cost is shown without inventing unsupported rejection counts
- Fix Content now reads `articles_archived` and reports `Archived X legacy template-mismatch articles`

Focused Admin action tests, the complete frontend suite, production build and diff checks passed before commit.

### Admin wording, information architecture and mobile polish

A read-only Admin dashboard audit mapped visible controls to their handlers/endpoints and identified stale labels, inaccurate import promises, clipped mobile text and ambiguous archive/delete language. It also confirmed that working controls should not be removed without usage evidence.

Commit `8cda9b4` — `Align Admin dashboard wording and mobile layout`

This commit was pushed to `origin/full-scrape-prod`, deployed and verified healthy.

Visible quick-action labels now accurately describe behavior:

- Generate → Run Hybrid Import
- Daily Brief → Send Daily Brief
- Facebook → Post to Facebook
- Twitter → Post to Twitter
- Cleanup → Remove Duplicates
- Archive Legacy Content retained with wrap-safe layout
- No Products → Remove Product Articles
- Sync RSS → Run RSS Sync

Mobile tabs now use Newsletter, Facebook, Email, Analytics and Affiliates while retaining order, icons, active state and horizontal scrolling.

Additional wording corrections:

- Import panel is now `Run News Import`
- stale fixed-volume and sports-cap promises were removed
- import copy describes RSS/research availability, duplicate/image/locality/quality checks and Manual Review outcomes
- Archive & Refresh is now `Archive All & Run Fresh Import` with explicit broad-maintenance warning
- Backfill Locations is now `Recalculate Article Locations`
- Manual Review copy says articles are withheld from public publication pending editorial review
- Open AI is now `Create OpenAI Draft`
- Archived Articles is now `Article Archive`
- stale Manchester, sports-quota and January 2026 source/strategy wording was removed

Quick actions retain readable touch targets and wrap-safe mobile labels. Handlers, endpoints and backend behavior remained unchanged. Focused polish tests, the complete frontend suite and production build passed.

### Subscriber lifecycle and manual-campaign safety

A read-only subscriber lifecycle audit confirmed:

- the ordinary Admin red trash control called authenticated `DELETE /api/admin/subscribers/{email}`
- the backend hard-deleted one subscriber document with no suppression/audit replacement
- preferences, consent-related lifecycle history and reactivation provenance could be lost
- the hard delete was irreversible except by backup and a deleted email could later be recreated as a fresh subscriber
- secure unsubscribe already provides the correct reversible lifecycle contract
- Daily Brief, Weekly Roundup, Breaking News, onboarding and migration/site-update sends exclude literal inactive subscribers
- manual campaign `Send to All` was the confirmed gap because it selected `find({})`
- Facebook and browser push use separate stores and are not driven by newsletter subscriber state

Design decision:

- ordinary Admin removal must be a reversible soft unsubscribe
- permanent privacy erasure is a separate future workflow and was not invented here
- subscriber identity for the new Admin action must be the canonical management UUID, never email
- repeat unsubscribe preserves the original inactive timestamp/method rather than rewriting lifecycle history
- the legacy hard-delete route remains authenticated and unchanged for now but is no longer exposed by the ordinary subscriber list

Commit `a2421d6` — `Add safe Admin subscriber unsubscribe`

This commit was pushed successfully to `origin/full-scrape-prod`; local and remote-tracking branches are aligned on the full hash `a2421d6ea735cc3b372ec3bb93d1a8b407fa59a7`. The deployed production checkpoint for this chat is this commit.

Backend:

- added authenticated `POST /api/admin/subscribers/{newsletter_management_id}/unsubscribe`
- validates canonical UUIDv4 before database access
- finds one subscriber only by management ID
- unknown/malformed IDs fail safely
- active or legacy-active records set exactly:
  - `active=False`
  - `daily_brief=False`
  - `weekly_roundup=False`
  - `breaking_news=False`
  - current UTC ISO `unsubscribed_at`
  - `unsubscribe_method="admin"`
- preserves email, preferences, provenance, management ID, token version, timestamps, reactivation history, onboarding/send history and priority flags
- does not delete a subscriber or mutate challenges, rate limits, analytics, digest logs or send ledgers
- does not increment `newsletter_token_version`
- already inactive subscribers return success without another update, preserving the original unsubscribe timestamp/method
- returns only success, management ID, inactive state and safe message

Manual campaigns:

- `mode=all` now includes literal `active=True` and legacy records where `active` is missing
- literal `active=False` is excluded
- test-send mode and provider/rendering behavior remain unchanged

Admin UI:

- replaced the ordinary trash control with `UserMinus`
- exact confirmation explains that all newsletter emails stop while preferences/history are retained
- success says `Subscriber unsubscribed.`
- failures use privacy-safe generic wording
- subscriber data/dashboard counts refresh after success
- the row remains visible with Active or Unsubscribed state
- inactive rows show `Reactivation requires a verified email link.` and no unsubscribe control
- active rows receive an action only when `newsletter_management_id` is a canonical UUIDv4
- active rows without a valid management ID show:
  `Management ID unavailable — subscriber migration or repair is required.`
- missing-ID rows have no clickable/network path and never fall back to email or hard delete

Verification completed:

- focused backend subscriber/campaign tests: `9 passed`
- focused frontend subscriber lifecycle tests after the final missing-ID correction: `9 passed`
- complete available frontend suite: `115 passed`
- frontend production build: passed
- Python compilation: passed
- current-state newsletter regression selection: `581 passed`, with only obsolete pre-activation assertions excluded
- `git diff --check`: passed
- no production subscriber or email mutation was used for verification

QA note:

Some older newsletter tests still assert that request-link routes return HTTP 503 and that activation gates are literal `False`. Those assertions conflict with the authoritative 20 July production record showing both gates enabled. They were not changed during the subscriber lifecycle implementation because secure public routes and activation behavior were outside scope. Updating those obsolete test expectations remains a separate narrow maintenance task.

### Deployment and health state

All commits listed above were pushed in order to `origin/full-scrape-prod`. Production deployments used the established push/deploy workflow. Deployment checks performed throughout this work confirmed:

- Render deployment returned to Live after deployment windows
- `/health` returned HTTP 200 healthy
- scheduler startup remained normal
- morning, midday and evening article-generation jobs remained registered
- Daily Brief remained registered
- Weekly Roundup batches 1–4 remained registered
- no database migration, index provisioning, secret change or unrelated production configuration change occurred during these code/UI stages
- no production email was sent as part of local implementation verification

### Deferred items and next follow-ups

The following work is intentionally deferred:

1. Correct obsolete newsletter test assertions that still describe the pre-activation literal-false/HTTP-503 state.
2. Decide whether the legacy Admin hard-delete subscriber route should later be removed or replaced by a separately approved privacy-erasure workflow.
3. Add Admin create/update canonical category validation and importer normalization as the planned taxonomy Stage 2B; no Mongo category migration is currently required.
4. Review related-story category alias matching separately.
5. Run read-only shadow evaluators against approved live/source snapshots only under a separately authorised evaluation step; they remain disconnected from production imports.
6. Continue operational observation of article quality guards, Manual Review counts and the public 40/40/20 allocation.
7. Keep RFC one-click outbound-header lifecycle work separate from the completed secure newsletter system.
8. Perform Browserslist database maintenance separately; current build warnings are non-blocking.

### Current repository checkpoint

- branch: `full-scrape-prod`
- local `HEAD`: `a2421d6ea735cc3b372ec3bb93d1a8b407fa59a7`
- `origin/full-scrape-prod`: `a2421d6ea735cc3b372ec3bb93d1a8b407fa59a7`
- latest completed work: safe Admin subscriber soft unsubscribe and inactive manual-campaign exclusion
- tracked working tree: clean before this documentation-only append
- `AGENTS.md`: intentionally untracked and excluded
- immediate recommended next step: review this documentation append, then commit it separately only after approval


## Operational update — 24 July 2026

### Phase 3A status

- Phase 3A implementation completed.
- Full automated QA completed successfully.
- Test suite result: **968 passed, 0 failed, 0 errors, 330 warnings**.
- Deployment completed successfully.
- Production health checks passed.
- Service running normally.

### Remaining production verification

The only remaining validation is the first production RSS-generated article created after deployment. Verify that it:

- was generated after deployment;
- preserves the Perplexity paragraph structure;
- retains quotes with correct attribution;
- includes a compact summary;
- removes source URL tails;
- renders correctly on desktop and mobile; and
- introduces no formatting regressions.

Phase 3A will be marked fully complete once this live production verification has been successfully performed.

## Operational update — 24 July 2026 — Newsletter test alignment and article live-pool hardening

### Repository baseline

- branch: `full-scrape-prod`
- work began from commit: `f4e5e6131dd66f153d85ebcdd142666521b042f1`
- `AGENTS.md` remains intentionally untracked and excluded
- no production mutation, deployment, push or database repair occurred during this work

### Newsletter activation test alignment

The production newsletter activation state was already:

- `NEWSLETTER_REQUEST_LINKS_ENABLED = True`
- `NEWSLETTER_CHALLENGE_ENFORCEMENT_ENABLED = True`

Several older tests still described the former dormant state. Those obsolete assertions were corrected without changing newsletter runtime behaviour.

Corrections:

- challenge-enforcement tests now assert the enabled production state
- request-link routes now expect the established privacy-safe HTTP 202 contract
- confirmation routes continue to fail closed with generic HTTP 503 when the signing secret is unavailable
- obsolete tests claiming that the three request-link routes remain dormant were removed
- route-contract test naming now reflects both privacy-safe 202 request-link responses and fail-closed confirmation behaviour

Verification:

- complete newsletter suite: `968 passed`
- Python compilation: passed
- `git diff --check`: passed

Known Python 3.13 gzip/resource warnings and existing FastAPI deprecation warnings remain non-blocking and did not produce test failures.

### Article live-pool root cause

The configured visibility cap remained 100, but the usable public pool contracted because:

- the cap previously selected recent records without requiring complete article content, an image or an eligible editorial state
- metadata-only RSS records could consume live slots
- later duplicate and quality cleanup archived invalid records without refilling vacated slots
- valid records archived by automatic cap or ratio balancing were not reliably restored
- the optional ratio rebalancer can restrict visibility further when enabled
- public API editorial filters reduce the final public set beyond the database-visible count

### Article live-pool correction

The cap now:

- requires a title, image and at least 1,000 characters of full article content
- excludes metadata-only, Manual Review, unsafe, crime-heavy, sport, celebrity, entertainment and lifestyle records
- restores only eligible records previously archived with `auto_cap` or `ratio_rebalance`
- preserves intentional Admin, duplicate, short-content, Manual Review and other editorial archives
- enforces a maximum of 100 eligible records
- targets the established 40% Local, 40% Business/Finance/Property/Economy and 20% AI & Tech allocation when sufficient inventory exists
- uses other suitable material only to fill genuine inventory shortages
- runs again after duplicate and quality cleanup so removed metadata records no longer leave vacant live slots

### Controlled repair utility

Added `backend/scripts/repair_live_article_pool.py`.

The utility is not an automatic or blind restoration tool. Safeguards include:

- read-only `--dry-run`
- mandatory `--expected-count` for apply
- interactive TTY requirement
- exact confirmation phrase
- fresh eligibility scan immediately before writing
- exact ordered ID-set comparison
- count-drift rejection before writes
- one guarded `update_many`
- conditional archive preconditions
- exact `matched_count` and `modified_count` validation
- post-write verification requiring zero remaining eligible repair candidates

The write is restricted to the exact eligible IDs that remain:

- `archived=True`
- `archive_reason` in `auto_cap` or `ratio_rebalance`

No repair was run against production.

### Article live-pool verification

- focused repair and live-pool tests: `12 passed`
- related article, canonical, hub and sitemap tests: `75 passed`
- broader focused article/importer/SEO regression selection previously passed: `144 passed`
- Python compilation: passed
- CLI help: passed
- `git diff --check`: passed

A broader repository run reported `1,382 passed`, `21 failed` and `12 errors`. The failures and errors were production-coupled tests requiring configured API, Admin-login or live database collaborators and failed before exercising the live-pool change. No production POST request was made.

### Expected production behaviour

After deployment and the next normal scheduled generation cycle:

- up to 100 eligible full-content articles may be visible
- metadata-only records remain excluded
- eligible records previously archived only by automatic cap or ratio balancing may refill the pool
- intentional safety and editorial archives remain untouched
- the visible count may remain below 100 when fewer than 100 safe full-content records exist

Immediate production recovery must not use a broad archive restore. Any controlled repair invocation requires a separate explicit approval after deployment and a fresh dry-run review.

### Files included in the pending commit

- `backend/server.py`
- `backend/scripts/repair_live_article_pool.py`
- `tests/test_article_live_pool_cap.py`
- `tests/test_newsletter_challenge_enforcement.py`
- `tests/test_newsletter_secure_preferences.py`
- `tests/test_newsletter_secure_reactivation.py`
- `tests/test_newsletter_secure_route_contracts.py`
- `tests/test_newsletter_secure_unsubscribe.py`
- `docs/PROJECT_STATE.md`

### Immediate next step

Review this state-file append, stage `docs/PROJECT_STATE.md`, rerun staged diff checks, then commit. Do not run the production repair before deployment and a separately approved dry-run.

## Operational correction — 24 July 2026 — Self-healing article pool restoration

Post-deployment production verification found:

- production service healthy
- `3,819` total article records
- `19` database-visible records
- `3,714` records archived with `archive_reason="auto_cap"`
- public API returned `16` articles after public filtering
- controlled repair dry-run found `197` eligible automatic-archive records
- no production repair or other database write was performed

A review of commit `be5c4ed` confirmed that `cap_visible_articles()` had been changed to inspect only currently unarchived records. It could archive excess eligible records but could not restore eligible records previously archived by `auto_cap` or `ratio_rebalance`.

The earlier state-file wording that the next scheduled generation cycle would automatically restore eligible archived records was therefore inaccurate.

The smallest corrective change now makes `cap_visible_articles()`:

- inspect currently visible records plus records archived only by `auto_cap` or `ratio_rebalance`
- continue excluding Admin and other intentional archive reasons
- select the newest eligible records up to the configured `keep` value
- restore only selected automatic archives
- unset `archived_at` and `archive_reason` on restored records
- continue archiving eligible, non-protected records outside the selected set
- preserve owner-protected, Manual Review, safety and editorial archive boundaries

Verification completed:

- new restoration regression test first failed against the deployed implementation, confirming the omission
- focused live-pool suite: `13 passed`
- related article, canonical, image, social metadata, public hub and sitemap regressions: `82 passed`
- Python compilation: passed
- `git diff --check`: passed

The standalone repair utility remains unused. Production restoration should occur only after this self-healing correction is committed, deployed and verified.

## Operational update — 24 July 2026 — RSS feed concurrency hardening

### Production log finding

Render logs at approximately `11:00:21 BST` showed a near-simultaneous timeout burst across many unrelated sources, including BBC, Sky, Guardian, Cheshire Live, GOV.UK, HMRC, ONS, Companies House, TechCrunch and arXiv feeds.

Read-only investigation confirmed:

- `56` RSS feeds are configured
- `fetch_all_feeds()` launched every configured feed simultaneously with `asyncio.gather()`
- `fetch_category_feeds()` used the same unbounded concurrency pattern
- every individual feed fetch created a separate `httpx.AsyncClient`
- each request used a `15.0` second timeout
- the near-identical timeout timestamps were consistent with shared outbound connection, DNS or resource pressure rather than independent failure of every source

### Correction

`NewsFeedService` now:

- limits outbound feed fetch concurrency to `8`
- uses one shared bounded batch helper
- applies the same bounded behaviour to all-feed and category-feed retrieval
- preserves existing per-feed parsing, source configuration, timeout, error handling and result ordering
- continues returning partial successful results when individual feeds fail

No timeout increase was introduced. The correction addresses resource pressure first rather than allowing 56 simultaneous clients to wait longer.

### Verification

A dedicated regression test first demonstrated the previous unbounded behaviour with a peak concurrency of `20` from `20` test feeds.

After the correction:

- focused concurrency test: `1 passed`
- concurrency plus related RSS shadow, text sanitation and editorial-guard tests: `64 passed`
- Python compilation: passed
- `git diff --check`: passed

Production log behaviour must be reviewed after deployment and the next scheduled RSS generation cycle.

## Operational update — 24 July 2026 — Guardian social-preview image consistency

### Production finding

Facebook sharing verification found that a Guardian-sourced Cheshire Today article displayed a Guardian-branded social image even though the public article page used a clean unbranded stored image.

Read-only inspection confirmed:

- the article record stored the clean Guardian image used on the website
- the crawler HTML path detected the small signed Guardian thumbnail
- Cheshire Today then fetched the Guardian source page
- the Guardian page-level `og:image` contained a branded Guardian overlay
- Facebook correctly rendered the branded image Cheshire Today supplied

This was not a Facebook cache issue.

### Correction

The Guardian-specific source-page substitution was removed from `serve_article_html()`.

The crawler path now:

- keeps the stored signed Guardian image
- does not fetch the Guardian source page for social-image replacement
- avoids Guardian-branded overlay parameters such as `overlay-base64`
- keeps existing Newsquest, Contentful, Reach and BBC social-image handling unchanged
- keeps article-page, Facebook and Twitter image selection consistent

### Verification

A dedicated regression test first reproduced the previous behaviour by returning a branded Guardian source-page `og:image`.

After the correction:

- focused Guardian regression: passed
- self-contained social/image metadata suite: `34 passed`
- Python compilation: passed
- `git diff --check`: passed

Production verification remains required after deployment by checking the live crawler HTML and refreshing the Facebook preview.

### Follow-up correction — Facebook minimum image size

Post-deployment Facebook Sharing Debugger verification showed that the clean stored Guardian image was only `140×112`, below Facebook's minimum `200×200` requirement.

Further read-only checks confirmed:

- changing `width=140` to `width=1200` invalidated the Guardian signature and returned HTTP 401
- removing the signed query also returned HTTP 401
- the Guardian source page exposes clean, large, correctly signed responsive image URLs
- these clean image candidates do not contain the branded `overlay-base64` parameter

The Guardian social-image handling was therefore refined again.

For small signed Guardian thumbnails only, Cheshire Today now:

- fetches the Guardian source page
- scans normal image markup for clean signed `i.guim.co.uk` candidates
- rejects every candidate containing `overlay-base64`
- ignores candidates below `620px`
- prefers an exact `1200px` clean image
- otherwise selects the clean candidate closest to `1200px`
- falls back to the stored image if source retrieval or extraction fails

This supersedes the earlier statement that Guardian source pages are never fetched. The source page is now fetched narrowly to obtain a large clean responsive image, never to reuse its branded page-level Open Graph image.

Verification:

- focused large-clean-Guardian regression: passed
- complete article social-metadata test file: `3 passed`
- Python compilation: passed
- `git diff --check`: passed

Production verification remains required after deployment using crawler HTML and Facebook Sharing Debugger. The expected outcome is a clean Guardian image with no branding overlay and no minimum-size warning.

### Final Guardian signed-URL correction

Production Facebook Sharing Debugger verification found that the selected clean `1200×630` Guardian image returned HTTP 401 with `text/html`, causing an `Invalid Image Content Type` warning.

The extracted URL had been truncated at the first comma within Guardian's signed `precrop` parameter because the candidate regex excluded commas. This removed trailing crop parameters and the final signature.

The extractor now preserves commas inside Guardian image URLs, retaining the complete signed query including crop offsets, upscale controls and the `s=` signature.

Verification:

- strengthened regression reproduced the truncated signed URL failure
- focused signed-URL regression: passed
- complete article social-metadata file: `3 passed`
- Python compilation: passed
- `git diff --check`: passed

Production verification remains required after deployment. The final image must return HTTP 200 with an image content type and pass Facebook Sharing Debugger without branding, minimum-size or invalid-content-type warnings.

### Facebook App ID crawler metadata correction

After the Guardian image corrections passed Facebook Sharing Debugger, the remaining warning was a missing `fb:app_id`.

Investigation confirmed:

- Cheshire Today's established Facebook App ID is `2091422248085004`
- the ID was already present in the homepage and another backend sharing template
- the dedicated article crawler HTML omitted the tag
- no new Meta application or identifier was created

The crawler article template now emits:

`<meta property="fb:app_id" content="2091422248085004">`

A regression assertion was added to the article social-metadata tests.

Verification:

- article social-metadata tests: `3 passed`
- Python compilation: passed
- `git diff --check`: passed

Production verification remains required after deployment by clicking `Scrape Again` in Facebook Sharing Debugger and confirming that no missing-property warning remains.

### Facebook App ID identity correction

Meta Developer settings confirmed that Cheshire Today's active application is:

- app name: `Cheshire Today Auto Poster`
- app ID: `1265742728765482`
- app domain: `cheshiretoday.co.uk`

The previously deployed value `2091422248085004` did not match any application available under the Cheshire Today Meta account.

Active runtime references were corrected in:

- the backend sharing template
- the dedicated article crawler metadata
- the frontend public HTML template
- the article social-metadata regression test

Historical documentation that records the previously deployed value was not rewritten.

Verification:

- article social-metadata tests: `3 passed`
- Python compilation: passed
- `git diff --check`: passed
- Meta App Domains now includes `cheshiretoday.co.uk`

Production verification remains required after deployment by checking the live crawler HTML and clicking `Scrape Again` in Facebook Sharing Debugger.

## Operational update — 25 July 2026

### Local RSS Manual Review fallback

The 05:00 production import fetched 27 Cheshire/local RSS candidates with images but imported none. Strict automatic-publication gates correctly rejected crime, weak and short material, but the existing Manual Review fallback was limited to a fixed town allowlist and ran after an overly broad low-utility rejection. Suitable non-crime community, human-interest, lifestyle and borderline local candidates could therefore be discarded without editorial review.

The local RSS path now retains strict public quality thresholds while routing suitable non-crime candidates that fail only the useful-local relevance gate, soft lifestyle/editorial-value classification, topic cap, freshness gate or post-rewrite public-length threshold into the existing hidden Manual Review workflow. The fallback:

- has no one-candidate limit within the existing import batch safeguards
- preserves title, source URL, image, location, Local News metadata and available source text
- records a clear Manual Review reason
- does not increment successful live Cheshire import counts
- continues rejecting duplicates, crime/court content, obituary material, promotional/spam/product filler, missing or invalid source URLs, missing or unusable images and unsafe invention-risk wording
- does not alter UK, Business, Finance, Tech, homepage, category, 40/40/20 or live-pool behaviour

Verification:

- focused Local RSS Manual Review regressions: `7 passed`
- combined importer, Manual Review, public-route, canonical, sitemap, live-pool, editorial-guard, sanitizer and RSS shadow verification: `177 passed`
- Python compilation: passed
- `git diff --check`: passed
- no production import or database mutation was used

Manual production verification remains required after deployment: run one authenticated Admin news import, confirm suitable non-crime Local candidates can appear in Manual Review with preserved metadata and clear reasons, confirm live Cheshire counts include only strict public imports, and confirm crime, duplicate, invalid-source and unusable-image candidates remain absent. Do not approve or publish any queued article without normal editorial review.

### Local RSS civic/economic relevance refinement

Production verification confirmed that the Manual Review fallback fixed the silent-discard defect, but the positive useful-local gate remained too conservative for clear civic and economic stories. Major retail or hospitality openings and investment, and material park, attraction or tourism improvements, could be diverted to Manual Review before reaching the existing strict rewrite and publication safeguards.

The Local RSS classifier now recognises only clear combinations of a relevant local sector and a material opening, investment, refurbishment, expansion, funding, employment or improvement signal. Those candidates proceed through the unchanged Perplexity rewrite, 1,000-character floor, locality check and AI/editorial guard; the general relevance threshold was not lowered. Sponsored, advertorial, review, shopping-deal and “best of” material cannot use this refinement.

Soft candidates continue to be retained in hidden Manual Review, but their reason now uses a concise editorial classification where evidence is available: Community feature, Human-interest, Lifestyle, Local attraction, Retail feature, Hospitality, Tourism, Entertainment or Soft local news. Existing hard rejection of crime/court, duplicates, Manchester material, invalid sources, missing or weak images, promotional/spam filler and unsafe content is unchanged.

Verification:

- focused Local RSS Manual Review and classifier regressions: `12 passed`
- combined importer, Manual Review, public-route, canonical, sitemap, live-pool, editorial-guard, sanitizer and RSS shadow verification: `182 passed`
- Python compilation: passed
- `git diff --check`: passed
- no production import, database mutation, staging, commit or deployment was performed

After deployment, the next scheduled import should allow obvious high-value Local investment and civic-improvement candidates to reach the existing strict automatic-publication path. Actual public counts remain dependent on current feed availability, successful full-length rewriting and every existing safety guard; soft stories should continue to appear only in Manual Review.

### Manual Review editorial metadata

Manual Review records now have a deterministic, non-scoring editorial metadata contract for Admin presentation. New guarded/imported records persist `editorial_metadata`; the authenticated Manual Review list derives the same contract in memory for historical records, so no database migration or read-time mutation is required.

The metadata describes the decision already made: routing reason, source type, detected locality, editorial topic, rewrite status and length, image status, freshness relative to review time, duplicate flag, failed public gate, automatic-publication candidacy and one of four deterministic recommendations: Strong candidate, Borderline, Needs rewrite or Needs editorial review. Automatic-publication candidacy is true only for complete records with usable images and no duplicate concern that were retained by a non-quality operational gate: public import cap, topic cap or freshness limit. A Strong candidate recommendation always carries that same true candidacy value. It is descriptive only. No importer, publication gate, safety guard, counter, homepage query, live-pool rule or public route consumes it.

The Admin Manual Review card now shows the recommendation and a compact responsive fact grid beneath the existing review reason. Existing Source, Edit, Create OpenAI Draft and Archive actions are unchanged.

Verification:

- focused backend metadata tests: `8 passed`
- focused frontend presentation tests: `2 passed`
- combined importer, Manual Review, public-route, canonical, sitemap, live-pool, editorial-guard, sanitizer, RSS shadow and Admin-auth regression verification: `200 passed`
- complete available frontend suite: `117 passed`
- production frontend build: passed
- Python compilation: passed
- `git diff --check`: passed
- no import, production mutation, staging, commit or deployment was performed

Deployment and authenticated Admin visual verification remain pending approval.

### Newsquest Local RSS shadow evaluation

A standalone read-only shadow evaluator now measures the proposed Northwich
Guardian, Knutsford Guardian and Runcorn & Widnes World feeds without adding
them to `RSS_FEEDS`, importing articles, publishing content or inserting Manual
Review records. It reuses the existing safe RSS/XML parsing, Newsquest image
extraction, canonical URL normalisation, spam screening, configured-local-feed
sampling and duplicate primitives. The deterministic Local crime, obituary,
low-utility, civic/economic, usefulness and Manual Review-reason policy now
lives in one database-free module used by both the production importer and the
evaluator, preventing independently copied shadow rules from drifting. The
Newsquest-specific layer reports town relevance, image
availability, existing/configured/cross-Newsquest duplicates and three
descriptive outcomes: existing strict automatic-publication path candidate,
Manual Review candidate or hard reject. Automatic-publication-path results
remain only pre-rewrite candidates and would still have to pass every existing
rewrite, length, locality, factual and editorial guard if the feeds are later
activated.

The evaluator has no MongoDB import, write method, activation flag, scheduler
hook or production-import hook. An optional existing-article JSON snapshot is
strictly limited to `title` and `source_url`. Rejected candidate items do not
suppress a later usable version, while cross-feed syndication remains visible
in the diagnostics.

The 25 July 2026 read-only live-feed evaluation found:

- all three feeds succeeded and supplied 50 items with images each
- Northwich Guardian: 50 raw, 11 town-relevant, 4 strict-path candidates,
  5 Manual Review candidates and 41 hard rejects
- Knutsford Guardian: 50 raw, 14 town-relevant, 5 strict-path candidates,
  6 Manual Review candidates and 39 hard rejects
- Runcorn & Widnes World: 50 raw, 30 town-relevant, 8 strict-path candidates,
  13 Manual Review candidates and 29 hard rejects
- combined: 150 raw, 150 with images, 55 town-relevant, 17 strict-path
  candidates, 24 Manual Review candidates, 109 hard rejects and 41 unique
  usable leads
- the comparison sampled all 17 configured Local feeds and a read-only
  192-record public/API snapshot
- exact cross-Newsquest title diagnostics affected 18 Northwich items,
  18 Knutsford items and 7 Runcorn/Widnes items; configured-feed duplication
  affected 15, 10 and 12 items respectively

The result supports a cautious activation order of Runcorn & Widnes World
first, then Knutsford Guardian, then Northwich Guardian. No feed has been
activated and production behaviour is unchanged.

Verification:

- focused Newsquest shadow tests: `16 passed`
- combined RSS shadow, Local importer, Manual Review, editorial guard, RSS
  sanitation, Newsquest image, feed concurrency, public-hub and duplicate-auth
  regressions: `174 passed`
- Python compilation: passed
- `git diff --check`: passed
- no database write, production import, publication, Manual Review insertion,
  staging, commit, push or deployment was performed

### Knutsford Guardian single-feed activation preparation

The smallest production-source change has been prepared for the Knutsford
Guardian RSS feed only. Northwich Guardian, Runcorn & Widnes World, Nantwich
News and every other proposed source remain inactive.

The feed is appended to the existing lower-priority dedicated Local publisher
group and retains the current RSS parsing, embedded-image handling,
title/source duplicate checks, shared Local editorial policy, strict rewrite
and publication guards, Manual Review routing, scheduler, batch safeguards and
public import caps. A feed-specific word-bounded locality allowlist admits only
articles whose title, summary or available feed content identifies Knutsford,
Wilmslow, Alderley Edge or Handforth. Matches map to the existing `knutsford`
or `wilmslow` public locations; county-wide syndicated items without one of
those place signals are discarded before entering the Local candidate list.

Verification:

- focused Knutsford feed activation tests: `4 passed`
- combined offline RSS, Newsquest shadow, Local importer, Manual Review,
  editorial guard, image, duplicate, concurrency and public-route regressions:
  `168 passed`
- Python compilation: passed
- `git diff --check`: passed
- the production-coupled scheduler test file was not run against a live URL;
  without its required API URL it produced only baseline missing-URL failures
- no feed fetch, production import, database mutation, staging, commit, push or
  deployment was performed

### Operational update — 25 July 2026

The Local RSS editorial rules were extracted into the database-free
`backend/app/local_rss_editorial_policy.py` module and are now shared by the
production Local importer and the read-only Newsquest shadow evaluator. This
keeps the crime, obituary, low-utility, civic/economic, useful-local and Manual
Review-reason classifications aligned without importing `backend.server` into
the evaluator or introducing any database or application-startup dependency.
Production publication thresholds, safety guards and Manual Review routing
were not weakened.

The Newsquest shadow evaluator was completed for Northwich Guardian, Knutsford
Guardian and Runcorn & Widnes World. The verified evaluation produced 150 raw
items, all with images, of which 55 were town-relevant; 17 were strict-path
candidates, 24 were Manual Review candidates, 109 were hard rejects and 41
were unique usable leads. The evidence-based rollout order was Runcorn &
Widnes World first, Knutsford Guardian second and Northwich Guardian third.
The operational decision was nevertheless to activate Knutsford Guardian
alone as the first controlled production source; the other evaluated feeds
remain inactive pending separate approval.

Knutsford Guardian was activated through commit
`6d87817d2020ca3a4519cb120f988cc179dfa1b0` and pushed and deployed on
`full-scrape-prod`. The activation retains the existing RSS parsing, image
validation, duplicate detection, shared Local editorial policy, strict
automatic-publication path, Manual Review routing, scheduler behaviour and
public import caps. Its locality gate accepts word-bounded evidence for
Knutsford, Wilmslow, Alderley Edge or Handforth and does not admit generic
county-wide Newsquest stories without one of those place signals. Northwich
Guardian, Runcorn & Widnes World, Nantwich News and all other proposed sources
remain inactive. The production `/health` endpoint was verified after
deployment and returned HTTP 200 with `{"status":"healthy","service":"cheshire-news"}`.

The next normal Knutsford import requires a read-only operational verification:

- confirm the feed fetch succeeds through the scheduled/import workflow
- confirm accepted candidates contain genuine Knutsford, Wilmslow, Alderley
  Edge or Handforth evidence and map to the existing supported locations
- confirm county-wide stories without an allowed place signal are excluded
- confirm duplicate, crime/court, promotional, invalid-source and
  missing/unusable-image records remain hard rejected
- confirm soft but suitable stories remain hidden in Manual Review and strict
  candidates publish only after all existing rewrite, length, locality,
  factual and editorial guards pass
- confirm import counts, public caps and scheduler behaviour remain unchanged
- confirm Northwich Guardian, Runcorn & Widnes World and Nantwich News remain
  inactive

Facebook, Instagram and Meta Insights were reviewed as part of the current
audience workflow. The agreed social strategy keeps editorial selection and
human approval ahead of social copy generation: first recommend the Cheshire
Today article, wait for approval, and only then prepare the Facebook and
Instagram posts for that approved article. Social publishing remains an
explicit editorial action; no automatic posting or change to article
publication behaviour was introduced.

Current priorities and remaining work are:

1. complete the post-import verification checklist for the first live
   Knutsford Guardian import without weakening any publication guard
2. monitor unique Local yield, duplicate overlap, Manual Review quality and
   town relevance before approving another Newsquest feed
3. consider Runcorn & Widnes World and Northwich Guardian only as separate,
   evidence-led activation changes; keep all unapproved sources inactive
4. follow the approve-article-first social workflow and use subsequent Meta
   Insights reviews to assess outcomes without automating editorial decisions

## Operational update — 26 July 2026

### RSS expansion

The Knutsford Guardian production activation was completed previously. Runcorn
& Widnes World has now also been activated as a production Local RSS source.
Its word-bounded locality mappings are:

- Runcorn → `warrington`
- Widnes → `warrington`
- Halton → `warrington`

The existing duplicate, locality, editorial, image, rewrite, scheduler and
Manual Review safeguards were preserved. Northwich Guardian remains inactive.
Nantwich News remained pending until the later activation recorded below.

### Nantwich News activation

Nantwich News has been activated through its verified RSS feed, with Nantwich
mapped to the existing `crewe` public location. County-wide Cheshire review
routing was added for configured Cheshire-wide signals that do not have a
qualifying Nantwich town match.

County-wide candidates never enter automatic public publication. They may
enter the existing hidden Manual Review workflow only after passing the
existing hard-rejection checks and the existing useful-local article gate.
Useful county-wide civic stories retain the Manual Review reason:

`Local RSS article needs manual review: County-wide Cheshire story without a qualifying town match`

Crime/court, duplicate, promotional/spam, missing-source, missing-image and
known weak-image safeguards remain in force before Manual Review insertion.
Low-value county-wide material is skipped without public or Manual Review
insertion.

### Current production status

```text
Branch: full-scrape-prod

99dec3e Activate Runcorn and Widnes World feed
9cfb187 Activate Nantwich News feed and county-wide manual review routing
```

The production `/health` endpoint was verified healthy with HTTP 200. The
scheduler is running, and the morning, midday and evening import jobs remain
scheduled.

### Social media / Meta

Completed:

- Business Portfolio reviewed
- Facebook Page ownership verified
- Instagram Business ownership verified
- Facebook and Instagram accounts linked for cross-platform management
- automatic cross-posting intentionally disabled to allow platform-specific publishing
- two-factor authentication required
- Instagram category changed to `News & Media Website`
- Instagram profile renamed to `Cheshire Today | Cheshire News`
- Instagram bio updated
- website link verified
- profile image refreshed
- first Instagram Highlight created: `News`
- Highlight branding project initiated

### Branding project

A new project, **Cheshire Today Brand Identity & Social Media System**, is
planned.

Planned deliverables:

- brand colour palette
- typography
- logo suite
- professional vector Highlight cover suite
- Instagram Highlight covers
- Story templates
- feed templates
- carousel templates
- Reel covers
- Facebook templates
- Threads templates
- Brand Guidelines PDF
- Media Kit

Status: planned.

### Next priorities

1. Observe the midday import after the RSS expansion.
2. Verify Runcorn & Widnes World articles entering the pipeline.
3. Verify Nantwich News town and county-wide Manual Review routing.
4. Continue the Brand Identity project.
5. Continue Meta optimisation.
6. Consider Northwich Guardian activation only after production observation.
7. Evaluate future HTML adapters for selected Nub News publishers.

## Operational update — 26 July 2026 (Post-deployment verification)

### Production deployment

The following commits are deployed in production:

```text
f82610e Update project state after RSS expansion and Meta setup
c80ca7e Refine local RSS manual review quality
```

Deployment completed successfully.

### Production verification

Confirmed:

- `/health` is healthy
- the scheduler is running normally
- no scheduler behaviour changed
- no RSS configuration regressions were found
- no locality-mapping regressions were found

### First production import verification

The first scheduled import after the Runcorn & Widnes World and Nantwich
News feed activations increased the hidden Manual Review pool from 69 to
114 articles, an increase of 45. This observation occurred before the
later `c80ca7e` Manual Review quality-refinement deployment.

Observed contribution from the newly evaluated Local feeds:

- Knutsford Guardian: `+4`
- Runcorn & Widnes World: `+10`
- Nantwich News: `+4`
- Northwich Guardian: `0`
- public articles from the newly activated feeds: `0`

This confirms that the newly activated feeds entered the existing hidden
Manual Review workflow rather than bypassing editorial review.

### Editorial refinement

Production observation led to a narrow pre-Manual-Review rejection rule for:

- routine kitchen, shed, bin and other small fires
- TripAdvisor “best” listicles
- picnic listicles
- generic café reviews
- ordinary property-for-sale features
- routine road closures without significant public impact

Existing handling was retained for:

- food-hygiene enforcement
- significant transport disruption
- planning and housing
- NHS
- council decisions
- education
- regeneration and investment
- business and infrastructure
- charity and community projects
- environmental stories

The planning/housing topic classifier was also corrected so that community
stories mentioning care homes are no longer incorrectly assigned to the
planning/housing topic cap. All other publication and Manual Review safeguards
remain unchanged.

### Current active production Local RSS sources

Active:

- Cheshire Live
- Warrington Guardian
- Chester Standard
- Knutsford Guardian
- Runcorn & Widnes World
- Nantwich News

Inactive by design:

- Northwich Guardian
- Nub News sources
- Wilmslow.co.uk
- AlderleyEdge.com

### Current project status

The RSS rollout phase is considered stable. Future RSS work must remain
evidence-led, and no further production feed activation should occur until
sufficient observation data has been gathered.

### Current primary project

The current primary project is **Cheshire Today Brand Identity & Social Media
System**.

Status: started.

Completed:

- Meta Business review
- Instagram optimisation
- Facebook linking review
- Threads account presence confirmed in Accounts Centre; it is not currently
  added as a Business Portfolio asset
- Business Portfolio review
- Highlight strategy
- initial Highlight cover concept
- brand system documented

Planned next work:

- professional vector Highlight covers
- logo suite
- colour palette
- typography
- Story templates
- Instagram templates
- Facebook templates
- Threads templates
- carousel templates
- Reel covers
- Brand Guidelines PDF
- Media Kit

### Immediate priorities

1. Continue the Brand Identity project.
2. Observe future RSS imports.
3. Review Manual Review quality after several scheduler cycles.
4. Reassess Northwich Guardian only after sufficient production evidence.
5. Begin the reusable social-media template library.

## Operational update — 26 July 2026 (Brand Asset Library v1.0)

### Authoritative design baseline

The live website design system is the authoritative Cheshire Today brand
baseline.

Approved typography:

- Playfair Display for editorial headlines
- Public Sans for interface and body text

Approved primary palette:

- royal blue `#1E3A8A`
- primary hover `#1B357D`
- editorial emerald `#047857` / `#059669`
- breaking red `#DC2626`
- warm paper `#F7F4EE`
- warm panel `#FBFAF7`
- warm border `#E6E1D8`
- main headline text `#020617`
- body text `#1E293B`
- secondary text `#475569`

Montserrat and a new teal-first palette were explicitly not adopted because
they would conflict with the current production design system.

### Brand Asset Library v1.0

The permanent library has been created at `docs/brand-assets/`. An SVG-first
workflow has been adopted, with production PNG exports generated from approved
SVG masters. Naming, export, versioning and approval rules are documented. No
existing Highlight asset was altered during the library setup.

### Instagram Highlight suite

The completed Version 1.0 production suite contains SVG masters and
`1080 × 1080` PNG exports for:

- News
- Money
- Property
- AI & Tech
- Food & Drink
- Places
- Transport
- Newsletter
- Reels

The shared production contract is:

- background `#1E3A8A`
- icon colour `#F7F4EE`
- `32 px` rounded monoline stroke
- no visible text
- no gradients
- no filters
- no shadows
- central safe-area compliance
- accessibility metadata in the SVG masters

### Library structure

Prepared repository locations now exist for:

- logos
- colours
- typography
- social/highlights
- social/stories
- social/feed
- social/reels
- social/facebook
- social/threads
- media-kit
- brand-guidelines

### Production impact

- no website code changed
- no frontend styling changed
- no Tailwind configuration changed
- no production behaviour changed
- no deployment was required

### Next priority

The next brand deliverable is the Instagram Story Template System, followed by:

1. Feed graphics
2. Reels covers
3. Facebook graphics
4. Threads graphics
5. Brand Guidelines PDF
6. Media Kit

## Brand asset update — Instagram Story and Feed Template Systems v1.0

### Instagram Story Template System v1.0

Eight permanent SVG master templates were created under
`docs/brand-assets/social/stories/templates/`:

- `breaking-news.svg`
- `top-story.svg`
- `business.svg`
- `property.svg`
- `ai-tech.svg`
- `newsletter.svg`
- `poll.svg`
- `read-more.svg`

Standards:

- 1080 × 1920 canvas
- 72 px side margins
- 250 px top safe margin
- 300 px bottom safe margin
- hidden editor-guide layer
- SVG-first workflow
- no raster images, gradients, filters, shadows or AI artwork
- Playfair Display headlines
- Public Sans interface text
- existing production website palette only

### Instagram Feed Template System v1.0

Eight permanent SVG master templates were created under
`docs/brand-assets/social/feed/templates/`:

- `breaking-news-square.svg`
- `local-news-square.svg`
- `business-square.svg`
- `property-square.svg`
- `ai-tech-square.svg`
- `quote-square.svg`
- `poll-square.svg`
- `newsletter-square.svg`

Standards:

- 1080 × 1080 canvas
- 72 px safe area
- four-column editor grid
- 24/48/72 px spacing rhythm
- shared logo, image, category, headline and CTA placeholder contract
- SVG-first workflow
- no raster images, gradients, filters, shadows or AI artwork
- Playfair Display headlines
- Public Sans interface text
- existing production website palette only

### Validation

- all sixteen SVG files are valid XML
- exact canvas and `viewBox` values were verified
- element IDs and accessibility references were validated
- all critical content remains inside the approved safe areas
- approved production colours and typography are used
- no PNG exports were committed at this stage
- Story and Feed README documentation was completed
- website, frontend, backend, Tailwind and production behaviour were unchanged

### Project status

The Brand Identity & Social Media System now includes:

- Brand Asset Library structure
- Instagram Highlight Suite v1.0
- Instagram Story Template System v1.0
- Instagram Feed Template System v1.0

Recommended next production asset:

- Reels Cover Template System v1.0

## Brand asset update — Reels Cover Template System v1.0

### Reels Cover Template System v1.0

Six permanent SVG masters were created under
`docs/brand-assets/social/reels/templates/`:

- `breaking-news-reel.svg`
- `local-news-reel.svg`
- `business-reel.svg`
- `property-reel.svg`
- `ai-tech-reel.svg`
- `newsletter-reel.svg`

Standards:

- 1080 × 1920 canvas
- same safe-area contract as the Story Template System
- hidden editor-guide layer
- shared `logo`, `image`, `category`, `headline`, `reel-badge` and CTA placeholders
- Playfair Display headlines
- Public Sans interface text
- approved production website palette only
- SVG-first workflow
- no raster images, gradients, filters, shadows, external references or PNG exports

### Validation

- all six SVG files are valid XML
- canvas and `viewBox` values were verified
- IDs and accessibility references were validated
- all critical content remains within the approved safe area
- no website, frontend, backend, Tailwind or production behaviour changed
- Reels README documentation was completed

### Project status

The Brand Identity & Social Media System now includes:

- Brand Asset Library v1.0
- Instagram Highlight Suite v1.0
- Instagram Story Template System v1.0
- Instagram Feed Template System v1.0
- Reels Cover Template System v1.0

Recommended next production asset:

- Facebook Template System v1.0

## Brand asset update — Brand Guidelines v1.0

### Brand Guidelines

A new version-controlled source document now exists at:

`docs/brand-assets/brand-guidelines/BRAND_GUIDELINES.md`

It is the operational source for:

- brand principles
- logo usage
- colour palette
- typography
- social asset standards
- editorial imagery
- accessibility
- social publishing
- version control
- future roadmap

Markdown is now the source of truth for the Brand Guidelines. PDF editions should be generated from the Markdown document when required. The production website design system remains the authoritative Cheshire Today brand baseline.

The guidelines reference the existing Highlight, Story, Feed and Reels template systems. No production code or website behaviour changed.

### Project status

The Brand Identity & Social Media System now contains:

- Brand Asset Library
- Highlight Suite
- Story Templates
- Feed Templates
- Reels Templates
- Brand Guidelines v1.0

Recommended next project:

- Facebook Template System v1.0

## Brand asset update — Facebook Template System v1.0

### Facebook Template System v1.0

Nine permanent SVG masters were created under
`docs/brand-assets/social/facebook/templates/`:

- `breaking-news-facebook.svg`
- `local-news-facebook.svg`
- `business-facebook.svg`
- `property-facebook.svg`
- `ai-tech-facebook.svg`
- `quote-facebook.svg`
- `poll-facebook.svg`
- `newsletter-facebook.svg`
- `event-facebook.svg`

Standards:

- 1200 × 630 landscape canvas
- 72 px safe margin on every side
- critical content area `x=72–1128`, `y=72–558`
- hidden editor-guide layer
- shared `logo`, `image`, `category`, `headline` and CTA placeholders
- additional `poll-options` placeholder in the poll master
- additional `event-date` and `event-location` placeholders in the event master
- Playfair Display editorial headlines and quotations
- Public Sans labels, supporting text and calls to action
- approved production website palette only
- SVG-first workflow with no raster images, gradients, filters, shadows, external references or PNG exports in the permanent masters

### Production-sample validation

The Local News, Business and Newsletter masters were tested with the real Cheshire Today article “Councillors to rule on plans for 75-home estate in Cheshire countryside” and its source image.

All three temporary production samples passed XML, exact output-dimension, safe-area, typography, palette, image-crop, logo, CTA, placeholder-removal and hidden-guide checks. Headline wrapping remained legible at Facebook feed size with no overflow. The Newsletter treatment used the approved inverse warm-paper logo on royal blue.

The Facebook Template System v1.0 is ready for production use. No website, frontend, backend, Tailwind or production behaviour changed.

## Brand asset update — Facebook logo treatment refinement

The Facebook Template System v1.0 now uses the approved Cheshire Today logo contract rather than a visible placeholder treatment.

Approved source artwork:

`frontend/public/cheshire-today-email-logo.png`

Approved variants:

- standard: royal blue `#1E3A8A` for warm or light backgrounds
- inverse: warm paper `#F7F4EE` for royal-blue or dark backgrounds

The permanent SVG masters do not embed raster logo files. Each master retains a documented logo placeholder with an exact `159.34 × 54 px` artwork box at `x=72`, `y=72` and an explicit standard or inverse variant requirement. Final public exports must remove all placeholder text and placeholder boxes.

Three temporary real-article Facebook samples were regenerated with the actual Cheshire Today logo and passed validation:

- Local News
- Business
- Newsletter

All nine Facebook masters remain valid XML and preserve:

- 1200 × 630 canvas
- 72 px safe frame
- accessibility references
- approved palette
- approved typography
- hidden editor guides

No website, frontend, backend or production behaviour changed.

## Operational update — 27 July 2026 (Newsletter landing page v1)

A dedicated public newsletter landing page has been implemented locally at
`/newsletter`. The page uses the production Cheshire Today design system and
reuses the existing `NewsletterFull` subscription component and
`/api/newsletter/subscribe` contract. It includes the approved newsletter
schedule, benefits, privacy guidance and FAQ without adding subscriber-count,
testimonial or advertising claims.

The frontend route is paired with a dedicated crawler response so Facebook and
other social crawlers receive HTTP 200, a self-canonical newsletter URL,
newsletter-specific title and description, `index, follow`, Open Graph and
Twitter metadata, and the dedicated approved 1200 × 630
`cheshire-today-newsletter-share.png` asset. The secure
`/newsletter/preferences` and `/newsletter/reactivate`
routes and the real unknown-route 404 contract remain unchanged.

Verification completed locally:

- focused newsletter landing and public-route backend tests: 37 passed
- related newsletter security/backend regression tests: 298 passed
- focused newsletter landing frontend tests: 4 passed
- complete frontend suite: 173 passed
- Python compilation: passed
- production frontend build: passed
- `git diff --check`: passed

No production deployment or newsletter operation was performed. After a later
approved deployment, verify `/newsletter` with an ordinary browser and a
Facebook crawler, then refresh the Facebook link preview cache before using the
URL in a live campaign.

## Operational update — 27 July 2026 (Newsletter signup simplification Phase 1)

The public newsletter signup flow has been simplified locally for genuinely
new subscribers. New records are immediately active for The Daily Brief, The
Weekly Roundup and rare Breaking News Alerts. The three preferences and a
versioned, server-owned consent contract are stored with the consent timestamp
and an allow-listed signup placement; no IP address or user agent is collected.

Existing normalised email addresses remain privacy-preserving no-ops. Active,
partially configured and inactive records are not changed, inactive readers are
not publicly reactivated, and the secure preference, unsubscribe and
reactivation flows remain unchanged. The public response now distinguishes only
`created` from `existing`; it does not expose active state, preferences or
management identifiers. A duplicate-key race is mapped to the same safe
`existing` outcome. No subscriber-email index was added because repository
evidence does not yet prove a production duplicate audit and migration plan.

All active public signup forms now show the exact all-three consent wording and
send only the email address plus an allow-listed placement. A created outcome
shows a clear “You’re subscribed” summary with Close as the primary action and
optional secure preference management. An existing outcome retains the generic
non-enumerating message. The welcome email confirms immediate activation,
describes the Monday-to-Saturday and Sunday schedules accurately, describes
Breaking News Alerts as rare major-incident alerts, and removes the unreliable
“tomorrow” promise and any confirmation-click requirement.

Local verification completed:

- focused subscriber, consent-parity and welcome-email tests: 25 passed
- related newsletter security, public-route and Admin subscriber tests: 469 passed
- focused newsletter frontend tests: 14 passed
- complete frontend suite: 183 passed
- Python compilation: passed
- production frontend build: passed
- `git diff --check`: passed

No production subscriber operation, email send, deployment, commit or push was
performed. A later deployment must verify one new signup, one existing active
address and one inactive address without changing the latter two records.

## Operational update — 27 July 2026 (Facebook publishing and newsletter completion)

### Facebook publishing system

The Admin Facebook publishing workflow is complete. The existing publishing
dialog now supports both Link Preview and Branded Graphic modes for one article
at a time. Editors can generate and preview approved graphics, download exact
PNG exports, copy the canonical Cheshire Today article link, copy deterministic
Facebook captions and hashtags, and copy a complete Facebook post. The workflow
does not publish or schedule posts automatically and does not modify articles.

Completed graphic types:

- Local News
- Newsletter
- Business
- Property
- AI & Tech
- Breaking News
- Event
- Quote
- Poll

The graphic system uses authenticated Admin-only SVG endpoints and immutable,
checksum-protected approved templates and logo assets. Article-based requests
use stored article data and Mongo IDs; the Newsletter graphic uses fixed
approved copy; Breaking News requires explicit editor confirmation; Quote and
Poll accept only narrowly validated editor text. No arbitrary template, logo or
image URL is accepted from the client.

Release-candidate hardening completed:

- deterministic Quote attribution and Poll option fitting within approved
  template geometry
- typed rejection when editor text cannot fit safely
- immutable backend graphic and master registries
- frontend option, transport, backend route and composer inventory-parity
  protection
- URL, scheme, HTML and malformed tag-like input rejection
- authenticated-route, archived-record, Manual Review, error-mapping and
  no-write security regressions
- complete frontend and backend coverage for generation, preview, PNG download,
  publishing copy, accessibility, object-URL cleanup and stale-request handling

Final release-candidate verification passed:

- backend social-asset tests: 105 passed
- focused frontend publishing tests: 80 passed
- complete frontend suite: 211 passed
- Python compilation: passed
- production frontend build: passed
- `git diff --check`: passed

### Newsletter improvements

The newsletter public and operational workflow now includes:

- the public `/newsletter` landing page
- a dedicated 1200 × 630 newsletter Open Graph image
- one-click signup for genuinely new normalised email addresses
- immediate activation of The Daily Brief, The Weekly Roundup and Breaking News
  Alerts
- versioned consent wording, consent timestamp, selected preferences and
  allow-listed signup-placement recording
- an updated welcome email that confirms subscription without requiring a
  confirmation click
- consistent accessible status and error announcements across public signup
  surfaces
- one shared consent wording contract with automated frontend/backend parity
  protection
- secure preference management, unsubscribe and reactivation retained for later
  subscriber changes

The read-only production subscriber duplicate audit and guarded unique-index
provisioning have been completed successfully.

Production subscriber verification:

```text
Total subscribers: 14,265
Duplicate groups: 0
Malformed emails: 0
Unique email index: ACTIVE
Index name: newsletter_email_unique
```

The unique production index now enforces the canonical newsletter email
uniqueness contract. No duplicate repair was required before provisioning.

### Current repository status

```text
Branch: full-scrape-prod
HEAD: 886d9f3
```

### Next priorities

1. Continue editorial and content growth.
2. Monitor production operation and health.
3. Continue future feature work through the established QA-first workflow.

## Operational update — 27 July 2026 (Version 1 completion)

### Version 1 completion

Cheshire Today Version 1 engineering is complete. The production platform now
has the public publishing, authenticated Admin, editorial workflow, hidden
Manual Review, scheduler, archive, newsletter, SEO, security and operational
documentation foundations required for the move into Operations & Growth.

The July engineering history is complete in
`docs/HISTORY/ENGINEERING_LOG_JULY_2026.md`. It remains the chronological
historical record, while this file remains the operational source of truth.

### Social-media suite completion

Facebook Publishing Studio is complete with Link Preview and Branded Graphic
modes, deterministic copy helpers, SVG preview, exact PNG download and all nine
approved graphic types: Local News, Newsletter, Business, Property, AI & Tech,
Breaking News, Event, Quote and Poll. Its authenticated, read-only generation
contracts and immutable asset registry remain protected by backend and frontend
regressions.

The Instagram Highlight, Story, Feed and Reels systems are complete.
Representative real-article operational exports verified the Story, Feed and
Reels workflows at their exact production dimensions without changing their
immutable masters. Final private previews in the Instagram app remain a normal
per-post publishing check rather than unfinished engineering.

The native Threads publishing workflow is complete. It uses the existing
two-step editorial approval process, preserves the 40/40/20 content strategy
and deliberately remains conversational and text-led. No dedicated Threads
template is required without evidence of a future operational need.

The Brand Asset Library, Brand Guidelines v1.0 and platform workflow
documentation together form the completed Version 1 social-media system.

### Version 1 production implementation baseline

- Public homepage, article, category, canonical, sitemap and 404 behaviour is
  operational.
- Admin editorial, Manual Review, archive and publishing workflows are
  operational.
- Morning, midday and evening scheduling remains operational.
- The public newsletter landing page, one-click signup, welcome email, secure
  preferences, unsubscribe and reactivation are operational.
- Production newsletter email uniqueness is enforced by
  `newsletter_email_unique`.
- Facebook preparation and the Instagram and Threads publishing workflows are
  ready for routine editorial use.

The following branch and SHA identify the Version 1 implementation baseline
before the final documentation commit:

```text
Branch: full-scrape-prod
HEAD: b1e6b186a01865870a9a1deed2e187303a565552
```

### Remaining priorities

1. Editorial growth.
2. Facebook growth.
3. Newsletter growth.
4. SEO.
5. Google News.
6. Discover.
7. Affiliate-first monetisation.
8. Sponsor readiness.
9. Production monitoring.
10. Evidence-led future engineering.

## Operational update — 28 July 2026 (Unified Social Publishing Admin completion)

### Unified Admin implementation

The authenticated Admin Articles workflow now has one shared Social Publishing
entry point. Facebook remains the default platform and its completed Link Preview,
Branded Graphic, deterministic copy and nine graphic-type contracts are unchanged.

Instagram preparation is integrated into the same dialog for the following
approved combinations:

- Story → Top Story, exported at exactly `1080 × 1920`
- Feed → Local News, exported at exactly `1080 × 1080`
- Reels Cover → Local News, exported at exactly `1080 × 1920`

Each Instagram format supports authenticated SVG preview, exact browser-side PNG
download and deterministic format-specific caption, restrained hashtag and post
copy. Story copy keeps the canonical article URL as editor-only link-sticker
guidance; Feed and Reel public copy does not claim caption links are clickable.
The Reels workflow describes an article graphic and does not imply that its image
is video footage.

Threads is integrated as a native text-only preparation mode. It requires the
editor to acknowledge prior article selection and approval, validates a required
verified opening line and optional verified context, shows the exact post preview
and copies a post ending with the canonical Cheshire Today URL. It adds no
hashtags by default and has no graphic, backend request, persistence, posting,
scheduling or AI generation.

All platforms preserve Admin authentication, stored-article-only generation,
immutable approved assets, bounded image retrieval, SSRF and XML safeguards,
archived and Manual Review exclusions, exact geometry, object-URL cleanup and
stale-request protection. The workflow writes no article, subscriber or generated
asset record and never publishes or schedules a social post.

### Verification status

Repository verification passed `124` focused frontend tests covering the shared
dialog, Facebook regressions, Instagram transport/rasterisation/copy and Threads
validation/copy contracts.

The production health endpoint and `/admin` returned HTTP 200 on 28 July 2026.
However, `/admin` referenced deployed bundle `main.b82e6a85.js`, which did not
contain the shared Social Publishing, Instagram or Threads implementation strings.
The implementation at `5ceb997` was therefore not yet deployed, and no
authenticated live Admin generation, clipboard or download result is claimed in
this update.

The Version 1 unified Social Publishing implementation baseline before this
documentation change is:

```text
Branch: full-scrape-prod
HEAD: 5ceb997f78abdd4c8cbb95b1296d3f2d2f9f0e86
```

### Remaining operational verification

After the implementation is deployed, perform one authenticated read-only Admin
check with a suitable active Local News article. Confirm Facebook defaults and
all nine types; generate and download one Story, Feed and Reels Cover PNG at the
dimensions above; verify their format-specific clipboard copy; and verify the
Threads approval, validation, preview and clipboard contract. Preview each final
Instagram asset in the Instagram app before publication. Do not publish during
the verification.

No unfinished unified Social Publishing source implementation is known. Deployment
and the authenticated live checks above remain operational handover steps.

## Operational update — 30 July 2026 (First-party article-view tracking repair)

### Analytics review and repair

The first-party analytics review and article-view tracking investigation were
completed. Article-view tracking was intentionally separated from the independent
Most Read period-correctness work before commit.

The backend route, public article-page integration and focused backend/frontend
regressions were repaired and verified. Public article reads now resolve the
stored article before recording analytics, reject missing, archived and Manual
Review-hidden records before any analytics write, use the resolved Mongo article
identifier consistently and preserve the existing one-hour deduplication. The
frontend records a non-blocking view only after a successful current article load;
analytics failures do not affect rendering and stale navigation cannot record the
previous article.

The completed repair was committed and pushed to `origin/full-scrape-prod`:

```text
6a95ba9 Repair first-party article view tracking
```

RSS and other imports, scheduler jobs and locks, Daily Brief, Weekly Roundup,
Breaking News, all newsletter generation/rendering/tracking/sending behaviour and
the production database were untouched.

### Current repository state

The article-view portion of `backend/server.py` is committed and clean. The file
still has a separate unstaged hunk limited to the pending Most Read period work;
it is therefore not globally clean in the current working tree. Remaining
uncommitted QA work is confined to:

- `backend/server.py` — Most Read only
- `tests/test_most_read_push_features.py` — Most Read only
- `tests/test_most_read_periods.py`
- `AGENTS.md`, intentionally untracked and untouched

The immediate next task is to review and complete Most Read as a completely
separate QA change.

## Operational update — 31 July 2026 (Most Read period correctness)

The separate Most Read QA task is complete. The previous implementation applied
the requested result limit to aggregated view groups before resolving article
visibility, allowing missing, archived or Manual Review-hidden records to consume
limited result slots.

Most Read now processes period view groups in descending view-count order, skips
ineligible records and applies the requested limit only after collecting eligible
public articles. Empty periods return an empty list and never fall back to the
lifetime `articles.view_count` field. Existing `today`, `week`, `month` and
invalid-period behaviour remains unchanged.

Verification completed successfully:

- focused Most Read and directly related regressions: `61 passed`
- Python compilation: PASS
- `git diff --check`: PASS

The completed repair was committed and pushed successfully to
`origin/full-scrape-prod`:

```text
a93d4bf Fix Most Read public result limiting
```

The working tree now contains only `AGENTS.md`, intentionally untracked and
untouched.

## Engineering handover — 31 July 2026 (First-party analytics QA completion)

### Architecture review and decisions

The first-party article analytics path was reviewed end to end. Cheshire Today
retains two deliberately distinct measures: individual period events in
`article_views`, and the lifetime `articles.view_count` counter. Public article
reads must create deduplicated period events; Most Read must use those events for
its `today`, `week` and `month` results and must not substitute lifetime counts
when a period is empty.

The existing one-view-per-IP-per-article-per-hour behavior was preserved. No bot
filtering, consent redesign, index, TTL retention policy, homepage activation,
Admin reporting change or broader analytics redesign was introduced. The known
residual limitations remain application-level concurrent-request deduplication,
shared/proxied IP ambiguity and separate Mongo operations for the event insert
and lifetime-counter increment.

### Work-stream separation

The initial working tree mixed two independent fixes in `backend/server.py`:

1. recording valid public article reads;
2. correcting period-based Most Read results.

They were treated as separate QA and commit boundaries. The article-view handler
was partially staged without the Most Read hunk, its frontend and tests were
reviewed independently, and the remaining Most Read changes stayed unstaged until
their own implementation and approval cycle. This separation prevented a shared
file from broadening either production change.

### Article-view tracking outcome

The public article page now records a non-blocking view only after a successful,
current article load and uses the canonical Mongo identifier returned by the
backend. Failed analytics never affect rendering, and cleanup/navigation guards
prevent a delayed response from recording the previous article.

The backend resolves Mongo `_id` or legacy `id` before any analytics write,
rejects missing, archived and Manual Review-hidden records with HTTP 404, stores
the resolved Mongo identifier consistently, increments the same resolved article
and preserves one-hour deduplication. Focused backend and visibility checks passed
`55` tests, focused frontend tracking passed `7`, the complete frontend suite
passed `268`, Python compilation passed, the production frontend build passed and
`git diff --check` passed.

The implementation and its documentation were committed and pushed as:

```text
6a95ba9 Repair first-party article view tracking
c4d9faf Update project state after article-view tracking repair
```

### Most Read outcome

QA identified a second correctness defect: applying Mongo's aggregation limit
before public eligibility resolution allowed missing, archived or Manual
Review-hidden records to consume result slots. The endpoint now streams period
groups in descending view-count order, skips ineligible records and stops only
after the requested number of eligible public articles has been collected.

Empty periods return an empty list, the lifetime fallback is removed, Mongo and
legacy identifiers remain compatible, and the established `today`, `week`,
`month` and invalid-period response behavior is preserved. Focused Most Read and
directly related regressions passed `61` checks; Python compilation and
`git diff --check` passed.

The implementation and its documentation were committed and pushed as:

```text
a93d4bf Fix Most Read public result limiting
d6eb46b Record completed Most Read fix
```

### Operational boundary and repository state

RSS and hybrid imports, Perplexity rewriting, Manual Review routing, public caps,
deduplication, freshness gates, automatic publishing, scheduler jobs and locks,
Daily Brief, Weekly Roundup, Breaking News, newsletter selection/templates/
tracking/sending, subscriber imports, provider delivery and production database
contents were unchanged. No production database, import, scheduler or newsletter
operation was invoked during the work.

The implementation and documentation commits were pushed to
`origin/full-scrape-prod`. At handover, branch `full-scrape-prod` is at
`d6eb46b1c400c98e5f25595c01fd34ce2373c0b0`; the working tree contains only the
intentionally untracked and untouched `AGENTS.md`.

### Documentation workflow

For future substantial engineering conversations, complete the same closing
sequence: isolate independent work streams, verify and commit runtime changes,
record the durable architecture decisions, QA evidence, commit/push state,
protected-system impact and remaining risks in `docs/PROJECT_STATE.md` and the
appropriate historical engineering log, then review and commit that documentation
as a separate boundary before closing the conversation.

## Operational update — 31 July 2026 (Scheduled article-generation memory observability)

Render recorded production web-service memory exhaustion at approximately
12:01 BST on 29 July and 18:00 BST on 30 July. Both events reached the Starter
instance's 512 MB limit and correlate with scheduled `daily_article_generation`
runs, but retained logs do not identify the memory-intensive phase.

Non-sensitive observability instrumentation has been added locally to the
existing scheduled workflow. Searchable `article_generation_memory` markers
record approved phase names, elapsed seconds, process maximum RSS in MiB and
allow-listed integer counts only. Memory sampling and logging failures are
non-fatal. Titles, article text, URLs, images, database records, credentials,
environment values and API payloads are excluded.

This change is instrumentation only. Scheduler times and IDs, import targets,
RSS concurrency, source ordering, editorial and Manual Review gates, AI
rewriting, MongoDB operations, visible-pool handling, duplicate cleanup,
newsletters and deployment configuration remain unchanged. No production
optimisation has been made. Deployment and evidence collection across future
06:00, 12:00 and 18:00 runs remain pending review and approval.

## Strategic note — Version 2 brand refresh deferred

The current Cheshire Today logo and branding remain in use. A Version 2 brand
refresh has been explored but deliberately postponed until audience and business
growth justify a coordinated professional rollout; it is not a current
engineering priority.

The preferred future direction is to replace the map-pin-led symbol with a
clearer regional-news icon: a simplified folded newspaper incorporating a
subtle, accurate Cheshire county silhouette. The Cheshire Today name and
established teal identity should remain, and the icon must stay clear at favicon,
social-avatar and app-icon sizes.

This should be a complete brand refresh rather than an isolated logo change.
Planned deliverables should eventually cover horizontal and stacked logos,
icon-only versions, light, teal and dark variants, vector SVG assets, social
avatars, favicon and app icon, typography, colour and usage guidance, and
applications across the website, newsletters and sponsor packs.

Current priorities remain audience and readership growth, newsletter growth,
SEO and Discover, social growth and monetisation readiness. Revisit Version 2
branding only when its timing and business value justify the coordinated work.

## Operational update — 31 July 2026 (Legacy Facebook Admin UI containment)

The obsolete direct Facebook publishing controls have been removed from the
Admin frontend. The Overview batch-post action, legacy single-article posting
buttons and misleading deterministic “AI-prioritized” recommendation surface
are no longer visible or callable from Admin.

The Facebook tab now provides a read-only handoff to the Articles tab, where the
completed Social Publishing Studio remains the only visible Facebook publishing
workflow. It explicitly states that the tab does not publish or schedule posts
automatically.

This was frontend containment only. Legacy backend Facebook routes, Meta/OAuth
code and database collections remain unchanged pending a separate review. No
Meta API, scheduler, database, analytics, push, newsletter or production
configuration change was made. Redesign of the separate Analytics tab remains
future work.

This containment change is implemented and validated locally; deployment remains pending.

## Operational update — 1 August 2026 (Admin Analytics Phase 1)

The Admin Analytics tab has been rebuilt as a compact, read-only first-party
dashboard. Its default weekly view can be changed to today or the last 30 days,
and reports public article-view totals, articles read, bounded most-read content,
category readership, newsletter engagement, commercial placement counters and
aggregate advertiser-lead activity. The old Meta-dependent Facebook panels and
the push-notification send controls are no longer part of Analytics.

One authenticated `GET /api/admin/analytics/summary` endpoint supplies the
dashboard. It uses `article_views` joined to narrow public `articles` fields,
privacy-preserving `email_send_opportunities` counts, event counts aggregated
inside `email_analytics`, lifetime counters from `sponsored_placements`, and
status-only period aggregates from `advertiser_leads`. Sponsored figures are
explicitly labelled lifetime because the current storage contract does not
retain dated impression/click events.

Queries use UTC period cutoffs, Mongo aggregation, narrow projections and
bounded response sets. Archived, missing and Manual Review-hidden articles are
excluded before top-content limits are applied. No email addresses, recipient
hashes, tracking IDs, IP addresses, user agents, lead contact details, article
content or summaries are returned. Each data section fails independently to a
safe unavailable state, and the tab contains no write, send, publish, schedule,
archive, import or delete action.

No Meta, GA4, Plausible or PostHog API was integrated. No tracking behavior,
database migration, index, retention policy, provider configuration or
production data was changed. The implementation and regression coverage are
validated locally; deployment and production verification remain pending.
Production query latency remains unverified and must be measured after deployment
before any index or query optimisation is considered.

## Operational update — 1 August 2026 (Admin Analytics Phase 2A implemented locally)

Analytics Phase 2A adds Facebook-first traffic attribution without Meta or
provider API access. Facebook links copied from Social Publishing now use the
deterministic query `utm_source=facebook&utm_medium=social&utm_campaign=social_publishing`,
while canonical article URLs, internal View Article links, Instagram links and
Threads links remain query-free and unchanged.

The existing public article-view endpoint remains body-less compatible and now
accepts one optional, narrowly validated attribution object. Counted events
continue to store canonical `article_id`, `ip_hash` and UTC `viewed_at`, and add
only server-normalised `source`, `medium` and `campaign`. Approved stored source
values are `facebook`, `instagram`, `threads`, `newsletter`, `google`, `bing`,
`other_search`, `other_social`, `referral`, `direct_or_unknown` and `unknown`;
approved media are `social`, `email`, `organic_search`, `referral`,
`direct_or_unknown` and `unknown`; approved campaigns are `social_publishing`,
`daily_brief`, `weekly_roundup`, `breaking_news` and `unknown`. Phase 2A emits
the exact Facebook combination only; missing, malformed and historical values
are treated as unknown rather than stored verbatim.

The one-hour article-plus-IP-hash deduplication and lifetime `view_count`
behaviour are unchanged. Attribution is not part of the deduplication key and a
duplicate cannot overwrite the first counted event. Raw referrers, hostnames,
URLs, query strings, tracking IDs and subscriber identifiers are not stored or
returned.

The authenticated read-only Admin summary now includes period Facebook article
views and at most five eligible public Facebook-driven articles. It uses bounded
Mongo aggregation over `article_views.source=facebook`, with no lifetime
fallback. No Meta API, cookie, session, fingerprint, provider API, migration,
index, retention or new dependency was introduced. Implementation and
validation are local; deployment and production verification remain pending.
Production query latency must be measured after deployment before any index or
query optimisation is considered.
Invalid attribution receives a generic response that does not echo submitted
values. Manual Facebook/iPhone paste and link-preview verification remains
pending after deployment to confirm that the deterministic UTM link is preserved
by the platform workflow.

## Operational update — 1 August 2026 (public metadata reconciliation follow-up implemented locally)

Live QA confirmed that direct crawler HTML was correct while the React-rendered
DOM could retain the static homepage canonical, description and `og:url`
alongside page-specific article or hub metadata. The same static ownership gap
could also leave stale homepage Open Graph and Twitter title/description values.

The first correction was deployed as `6bfe896`. Live verification confirmed
unique canonical, description and `og:url` values on settled public article,
category, location, newsletter and guide pages. It also found that `/admin`
still inherited those three static homepage values and that unmanaged static
`og:type`, `og:image`, `twitter:card` and `twitter:image` tags remained beside
route-specific values.

The local follow-up marks the remaining conflicting shell tags as managed and
keeps one Helmet reconciliation owner mounted on every route. Homepage defaults
are emitted only for the exact homepage route (`/`); non-home reconciliation
removes the managed static defaults even when the active route has no public
metadata owner. Behavioural coverage now enforces exact uniqueness for
canonical, description, `og:url`, `og:type`, `og:image`, `twitter:card` and
`twitter:image`, using production metadata owners for homepage, article,
category, location, newsletter, Contact, secure newsletter management and
authority/guide routes, plus Admin and unsupported-route isolation and SPA
navigation. Article canonicals remain free of UTM parameters, `fbclid`, `gclid`
and fragments.

Backend crawler HTML, article routing, Open Graph image handling, NewsArticle
structured data, sitemap and news-sitemap generation, robots rules, archived
`noindex` behavior and Manual Review protection were not changed. Focused and
complete frontend tests, related crawler/canonical/sitemap regressions, Python
compilation, the production frontend build and `git diff --check` pass locally.
The follow-up implementation and validation are local; deployment and a second
live rendered-DOM/Search Console verification remain pending.
This correction removes a confirmed ambiguity but is not claimed to resolve the
site's indexing exclusions by itself; representative Search Console URL sampling
remains a separate evidence-led follow-up.

## Operational update — 1 August 2026 (rendered metadata reconciliation verified in production)

Render deployed `1e5c2da` successfully and production health returned HTTP
`200`. Deployment, startup and surrounding application logs contained no HTTP
5xx, crawler, React-bundle or metadata errors.

Settled live-DOM checks passed for the homepage, a current article, the same
article with Facebook attribution parameters, category and location hubs, the
newsletter landing page, Contact, secure newsletter management, Admin, an
authority/guide page and a genuine unsupported-route `404`. Homepage and
article pages each contained exactly one canonical, description, `og:url`,
`og:type`, `og:image`, `twitter:card` and `twitter:image`. Non-home routes no
longer inherited homepage metadata; Admin contained no public homepage
canonical, description, Open Graph or Twitter metadata, and secure newsletter
management retained `noindex, nofollow, noarchive` without public homepage
metadata. Article canonical and `og:url` values remained free of UTM parameters,
`fbclid`, `gclid` and fragments.

Same-tab navigation passed for homepage to article, article A to article B,
article to homepage, attributed article to clean canonical identity and homepage
to Admin. Direct secure-route verification passed; a true article-to-secure-
management SPA transition was not demonstrated and remains a minor evidence
gap. Googlebot HTML remained correct for homepage, article and category, with
`NewsArticle` structured data still present. `sitemap.xml`, `news-sitemap.xml`
and `robots.txt` remained healthy and unchanged.

This verifies the production metadata reconciliation but makes no claim of
indexing recovery. Representative Search Console sampling is the next SEO
investigation. Loading public articles during verification naturally recorded
ordinary first-party article-view and sponsored-impression events; no Admin
action, form submission, publishing action or manual production job occurred.

## Operational update — 1 August 2026 (Admin mobile Safari usability)

A reported mobile Safari zoomed presentation was investigated against the live
unauthenticated Admin login and the current frontend implementation. The public
viewport contract was already correct (`width=device-width, initial-scale=1`),
portrait login widths from 320 to 430 pixels did not overflow, and portrait login
text fields were already 16 pixels. The remaining credible zoom risk was confined
to authenticated Admin text-entry controls that could resolve to 12 or 14 pixels,
particularly at wide-phone landscape breakpoints and inside portalled dialogs.

The local frontend correction introduces an Admin-only mobile scope with a 16-pixel
minimum for text-entry inputs, textareas, native selects and shared select triggers
on mobile or touch viewports. Checkbox, radio, range, file, hidden, colour and
button-like inputs retain their existing treatment, and public-site controls are
not affected. The login shell now uses `100vh` with a `100dvh` enhancement,
safe-area padding, vertical scrolling and top alignment on short-height viewports,
while preserving normal-height centring, browser pinch zoom, autocomplete and the
existing authentication flow.

This is a frontend usability change only. Admin navigation architecture and the
separate Articles/Archive row-overflow findings remain future tasks; backend,
authentication and production configuration behaviour are unchanged. Implementation
and automated validation are local. Deployment and real-iPhone Safari verification
remain pending, so the reported device issue is not yet recorded as fully resolved.

## Operational update — 1 August 2026 (Edit Article Safari focus follow-up)

Post-deployment testing on a real iPhone confirmed that the Admin login now fits
correctly, but focusing Edit Article text fields could still trigger Safari focus
enlargement. The retained focus state then clipped the right side of the fixed
editor dialog and could leave the dashboard looking enlarged after the editor was
closed or the session returned to login.

Inspection confirmed that Edit Article, Manual Review and Archive editing share
the same Radix portalled article dialog. The deployed portal scope and generic
16-pixel rule were both present, and authenticated Chromium inspection confirmed
that every editor control already computed to 16 pixels at representative portrait
and landscape sizes. The exact Safari enlargement trigger therefore remains
unproven. The revised local follow-up instead addresses the evidenced clipping risk:
on mobile/touch layouts the article dialog is top-aligned inside safe-area margins,
the inherited two-axis translation is removed, child horizontal overflow is
contained, and the category/author row collapses on narrow screens. The dialog
retains bounded vertical scrolling with `vh` and `dvh` height handling.
Desktop and ordinary non-touch dialog geometry remain unchanged; the top-aligned,
non-translated override applies only to the Add/Edit Article dialog on mobile or
coarse-pointer layouts.

Pinch zoom, authentication, article saving, Manual Review and Archive workflows
remain unchanged. No dashboard-scale workaround was added because the enlarged
dashboard remains consistent with retained Safari focus zoom rather than a proven
separate page-width defect. Chromium emulation is supporting layout evidence, not
proof of Mobile Safari behaviour. Implementation and automated validation are
local; a second real-iPhone focus, keyboard and orientation check remains required
after deployment before the issue is considered resolved.

## Operational update — 1 August 2026 (mobile editor close reachability follow-up)

Physical-iPhone verification of deployed commit `6328cf3` confirmed that the Admin
login fits correctly, the Add/Edit Article editor no longer clips on the right and
its fields remain usable with the software keyboard open. Safari can still enlarge
and pan the page while a text field is focused. The remaining usability issue is
therefore close-button reachability during that retained focus state, not editor
width or form usability.

The local follow-up keeps the article dialog as the existing vertical scroll
container and adds a mobile/touch-only sticky header containing the existing title,
subtitle and a Radix close action with a 44-pixel touch target. Safe scroll padding
keeps focused controls below the sticky header. Safari zoom remains enabled and no
zoom reset, blur workaround or viewport restriction was introduced. Desktop and
other Admin dialogs, authentication, article saving, Manual Review and Archive
behaviour remain unchanged. Deployment and final physical-iPhone focus, keyboard,
scroll and close verification remain pending; production resolution is not yet
claimed.

## Operational update — 1 August 2026 (Admin mobile Safari production verification)

The Admin mobile Safari fixes are deployed through commit `a6bfb78`. Final
real-iPhone verification established that the initial login-page enlargement came
from Safari's saved Website Page Zoom setting for `cheshiretoday.co.uk`, rather
than the Admin viewport or layout. Restoring Page Zoom to 100% returned the correct
initial presentation, and the login then fitted without pinching.

At 100% Page Zoom, the Add/Edit Article dialog no longer clipped on the right;
Title, Short preview and Content remained usable with the software keyboard open.
The mobile sticky header stayed visible during internal editor scrolling, and its
44-pixel close control remained reachable without pinching out. Closing the editor
returned to a correctly fitted dashboard, and the login page remained correctly
fitted afterward. No separate dashboard-width defect was confirmed.

Safari's browser-specific focus enlargement was not disabled, and accessibility
pinch zoom remains available. Authentication, article save/update behaviour,
Manual Review, Archive, Social Publishing and backend behaviour were unchanged.
The operational usability problem is resolved under Safari Page Zoom 100%; this
does not claim verification across every mobile browser. Mobile navigation,
Articles/Archive action-row overflow, undersized touch targets and broader dialog
consistency remain separate future work. Facebook Analytics end-to-end production
verification remains pending and is the next Admin task.

The verification changed no Admin record, article, publication, newsletter,
schedule, database record or production configuration.
