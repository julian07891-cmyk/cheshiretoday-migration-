CONTINUE THE CHESHIRE TODAY PROJECT

Before doing anything:

1. Read these files in the project root:

PROJECT_CURRENT_STATE_MASTER_MARCH_2026.md
PROJECT_HANDOVER_MASTER_MARCH_2026.md

2. Understand the system architecture:

Frontend: React (CRA)
Backend: FastAPI
Database: MongoDB
Hosting: Render
Domain: cheshiretoday.co.uk

3. Workflow rules:

• Always check current system state before making changes  
• Apply changes via terminal commands only  
• Never require manual file edits  
• Execute one command per step  
• Verify results after each change  

4. Local verification method:

npm run build
npx serve -s build

Do NOT use:

npm start

5. Editorial strategy:

40% Local
40% Authority (Business + Tech)
20% UK

6. Content rules:

All active articles must contain at least 1000 characters.

7. Import schedule:

06:00
12:00
18:00

Target active pool:

55–70 articles.

8. Current production status:

Production running on Render  
SSL active  
Homepage algorithm stable  
Mobile responsive limits implemented  
Duplicate article prevention active  

9. Next tasks:

Newsletter system testing  
Affiliate monetisation integration  
Perplexity AI article generation tests  
SEO structured data improvements

Continue the project from this state.

---

## UPDATE — 9 March 2026 (current chat continuation)

### Scope of this update
This update records all work completed in the current chat session and consolidates relevant saved project memory / prior-chat operating constraints that still govern Cheshire Today.

### Persistent workflow / operating rules confirmed
The following remain active and should be assumed in all future work:

- No manual file editing. All changes must be applied by terminal command or script.
- One command at a time.
- Always check current code / state before modifying anything.
- Prefer running commands from project root.
- Prefer `grep` over `rg` because `rg` is not installed in the user environment.
- Local frontend verification method remains:
  - `npm run build`
  - `npx serve -s build`
- Do not use `npm start` / CRACO dev server as primary verification route.
- Staging / controlled rollout mindset remains in force even when production is live.
- Strategic positioning remains:
  - Hybrid local + business/finance + AI/tech authority publication
  - Affiliate-first monetisation
  - Content strategy ratio target approximately 40 / 40 / 20:
    - Local
    - Business + Finance
    - AI / Tech
- Header / nav should stay minimal and strategy-aligned.
- Project pillar preference/order remains:
  - Local
  - Business
  - AI & Tech
  - Finance
  - Tax (later / optional expansion context)
- Light mode and dark mode should both remain readable and visually coherent.
- Continue preserving the current homepage structure:
  - Smaller hero
  - Sidebar / right rail
  - Minimal nav
  - Homepage sections, not major layout redesign

### Relevant remembered project state from previous chats
The following prior-chat project memory remains relevant and should be treated as active project context:

- Production domain `cheshiretoday.co.uk` is live on Render.
- Render auto-deploy is disabled / manual deployment mindset has been used.
- The website is intended to evolve into a Cheshire economic intelligence / hybrid local authority publication.
- Current homepage / article system uses `category` and keyword logic because `/api/articles` does not reliably provide a `section` field.
- Newsletter optimisation strategy is still focused first on subject-line psychology and financial/local relevance, not on major email structural redesign yet.
- User wants major milestones captured into handover/status files so a new chat can resume immediately.
- Production priorities after core stability include:
  - newsletter growth / SMTP testing
  - affiliate monetisation blocks
  - Perplexity content testing
  - SEO / structured-data refinement
  - operational documentation / handover

### Completed in this chat — backend / content pipeline / freshness fixes

#### 1. Article page ID retrieval issue investigated and resolved
We traced article page loading inconsistency to identifier usage and verified backend article retrieval behavior:

- Confirmed `/api/articles/{article_id}` supports both custom `id` and Mongo `_id`.
- Verified article records where URL path used Mongo ObjectId while API payload returned custom UUID-style `id`.
- Confirmed backend route logic:
  - search main `articles` by `id`
  - fallback to `articles._id`
  - fallback to `archived_articles.id`
  - fallback to `archived_articles._id`
- Verified this behavior with live test fetches and DB record inspection.

#### 2. Local category contamination investigated
We diagnosed why non-local / business / AI content was appearing in Local views.

Findings:
- Category route and homepage/article logic had mismatches between raw categories and displayed pill labels.
- Confirmed local feeds / local location routing behavior and current route validation constraints.
- Verified location route wrapper only allows whitelisted locations.
- Confirmed location page API endpoint uses strict exact `location` matching.

#### 3. Scheduler not running — diagnosed and fixed
We identified why the expected 6am import did not appear:

- Checked scheduler endpoints and scheduler code paths.
- Verified scheduler jobs existed but `scheduler_running` was `false`.
- Confirmed `AUTO_GENERATION_ENABLED` gate was preventing scheduler start.
- Restarted backend with `AUTO_GENERATION_ENABLED=true`.
- Re-checked `/api/scheduler-status`.
- Confirmed scheduler now running with next run times populated for:
  - morning article generation
  - midday article generation
  - evening article generation
  - daily brief
  - weekly roundup
  - archive job
  - scheduled Facebook processing

#### 4. RSS freshness / stale homepage issue diagnosed to mixed-type `publishedDate`
This was a major root-cause fix.

Problem found:
- `publishedDate` values in Mongo were mixed between:
  - strings
  - true datetime objects
  - missing / malformed values
- Mongo sorting therefore produced stale or incorrect homepage order.
- Newest article could appear far below older ones even after successful import.

Actions completed:
- inspected raw `publishedDate` types in DB
- converted parseable string dates into real Mongo datetimes
- applied fallback dates to remaining invalid / missing entries
- verified API output now returns newest articles first
- identified ongoing ingestion risk in backend import code
- patched backend import logic so future imports normalize `publishedDate` to real datetimes instead of string ISO values
- verified `backend/server.py` imports cleanly after patch

Effect:
- homepage freshness restored
- newest imported article can surface correctly
- stale-ordering regression should not recur from future imports

#### 5. Content regeneration / readability checks
We reviewed the regeneration system and current article-content state:

- inspected `/admin/regenerate-content`
- confirmed it originally only targeted short-content articles (<1000 chars)
- reviewed regeneration behavior for recent articles
- triggered regeneration endpoint and confirmed recent articles were rewritten
- verified multiple regenerated articles now contain long-form content with materially increased character counts
- confirmed AI-generated content count still remains below full pool and many articles remain non-AI-generated
- clarified that content/readability issues were distinct from freshness / ordering issues

#### 6. RSS sync / article pool checks
We executed and reviewed sync behavior:

- confirmed RSS sync could import new items successfully
- verified active / archived counts
- confirmed system imported new items but stale ordering had masked freshness before `publishedDate` normalization
- active pool remained healthy after sync

### Completed in this chat — homepage / article UI / subscribe / Top Stories work

#### 7. Homepage subscribe banner restored
Objective:
Restore the homepage subscription banner that had previously disappeared from under the hero.

Work completed:
- searched current codebase for newsletter / subscribe components
- confirmed homepage no longer rendered a subscribe block
- identified reusable components:
  - `SubscribeSection`
  - `SubscribeInlineBanner`
- initially tested `SubscribeSection compact`, then rejected it because:
  - too large
  - wrong green promo styling
  - wrong visual fit for site theme
- switched homepage hero-area banner to use `SubscribeInlineBanner`
- moved banner into the left hero column so it no longer stretched under the Top Stories right rail
- adjusted wrapper width so it aligns visually with the hero content area rather than spanning the entire left column
- further refined width based on screenshot review

Current homepage result:
- small inline subscribe banner appears under hero
- layout no longer compresses or breaks Top Stories
- banner styling matches site palette better
- email input present
- subscribe CTA present

#### 8. Homepage subscribe banner text / strategy refinement
We noted and incorporated newsletter copy constraints:

- original copy was too generic / incorrect
- requirement raised to acknowledge weekend briefings
- homepage inline subscribe copy now references Cheshire stories at 7:30 AM
- article-page subscribe copy explicitly updated to:
  - mention weekend briefings
  - fit current site tone and palette

#### 9. Article page subscribe features corrected
There were two different subscribe placements to handle on article pages:

##### 9a. Sidebar subscribe box
- existing sidebar box was only a stub / placeholder toast
- replaced placeholder behavior with real `SubscribeSection compact`
- later restyled compact variant because its original green/yellow promo palette clashed with the site
- compact variant now uses:
  - slate / dark neutral surface
  - blue accent icon/button matching current theme
  - improved typography
  - weekend-briefing language
  - proper input + subscribe CTA
  - preferences link

Result:
- sidebar subscribe box now matches site color system and fits beneath affiliate block visually

##### 9b. Inline article subscribe banner
- confirmed article page did not contain `SubscribeInlineBanner`
- imported `SubscribeInlineBanner` into `ArticlePageV2.jsx`
- inserted it into the article flow before guides / promos / more stories
- verified placement visually in screenshots

Result:
- article pages now have both:
  - an inline subscribe banner in article flow
  - a sidebar subscribe form box

### 10. Top Stories right column improved
We specifically addressed the Top Stories sidebar / right rail.

Initial issue:
- right column was too sparse
- badges inconsistent
- meta missing
- later needed extra context and height balancing

Actions completed:
- inspected `TopStoriesGrid.jsx`
- confirmed it did not use `CompactArticleCard`
- normalized displayed category labels inside Top Stories:
  - `Local News` -> `Local`
  - `UK News` -> `UK`
  - `Tech` -> `AI & Tech`
- added time metadata
- added reading time metadata
- later re-added one-line summary/context because title + meta alone made cards too short
- increased card padding / minimum height to help right column extend naturally
- verified improved visual balance via screenshots

Current Top Stories result:
- right rail now shows:
  - normalized badge/category label
  - title
  - short summary/context
  - time
  - reading time
- right rail length/weight is improved and closer to desired visual balance against left hero + subscribe stack

### 11. Homepage layout balancing fixes
This chat included multiple iterative layout refinements based on screenshot review:

- moved subscribe banner out of full-width placement
- prevented Top Stories from being squashed by homepage banner
- rebalanced left hero column vs right Top Stories column
- tuned subscribe wrapper width
- tuned Top Stories vertical density so the right rail reads as intentional rather than underfilled

### 12. Color-system correction
A major visual correction completed in this chat:
- removed mismatched green/yellow marketing styling from article sidebar subscribe UI
- aligned subscribe surfaces/buttons with the current site theme
- preserved dark mode compatibility
- improved consistency with homepage / header / cards / affiliate blocks

### Git / deployment state reached during this chat
Within this chat we also:

- committed and pushed backend freshness fixes previously
- redeployed production after freshness / sorting correction
- verified homepage freshness on production/live site screenshots
- confirmed newest articles now surface correctly after `publishedDate` fixes

### Files changed in this chat
The following files were modified during this chat session:

- `backend/server.py`
  - scheduler enable flow validation
  - `publishedDate` normalization / import safety
- `frontend/src/pages/HomePageV1.jsx`
  - homepage subscribe banner restoration
  - hero-column placement
  - width/layout adjustments
- `frontend/src/pages/ArticlePageV2.jsx`
  - added inline article subscribe banner
  - sidebar subscribe integration retained
- `frontend/src/components/JobsWidget.jsx`
  - upgraded `SubscribeInlineBanner` into usable inline form/banner
- `frontend/src/components/homepage/TopStoriesGrid.jsx`
  - normalized badge labels
  - added meta
  - added summary/context
  - increased card height
- `frontend/src/components/SubscribeSection.jsx`
  - restyled compact variant to current slate/blue theme

### Current verified state after this chat
As of the end of this chat:

- homepage freshness is fixed
- scheduler is running
- RSS sync imports can surface correctly
- future imports should preserve proper datetime sorting
- homepage subscribe banner is restored and visually integrated under hero
- article pages have:
  - inline subscribe banner in content flow
  - styled sidebar subscribe form
- Top Stories right rail now includes:
  - normalized category label
  - title
  - summary/context
  - time
  - read time
- site palette is more consistent across newsletter UI surfaces

### Recommended next steps after this chat
Highest-value next actions now:

1. Normalize category / badge / pillar logic across homepage and cards so raw feed labels consistently map to project pillars.
2. Tighten homepage ranking logic so pillar ordering follows strategy more explicitly:
   - Local
   - Business
   - AI & Tech
   - Finance
   - UK
3. Continue SEO / schema refinement.
4. Continue newsletter / SMTP / growth work.
5. Continue affiliate monetisation refinement and safe placement.
6. Keep updating this handover file after each major milestone.

### Important note for future chat continuation
If continuing in a new chat, resume from:
- post-freshness-fix stable state
- homepage subscribe/banner system restored
- article subscribe placements restored
- Top Stories metadata/context restored
- next task = category / badge / pillar normalization across homepage logic


