# Cheshire Today — Production Timeline

## 5 October 2026 — mixed-date hotfix production acceptance

**APPROVED WITH OBSERVATIONS — production accepted on the first post-hotfix
natural article run.** Evidence is the preceding authenticated Render read-only
inspection, reiterated in the approved documentation brief; no production action
or new test run was performed to record it. Times below are BST.

### Original incident and correction

The 06:00 scheduled run on `b83d2c3` acquired `article_gen_2026100505`, then failed
at 06:01:27.908 with the comparison error
`'<' not supported between instances of 'datetime.datetime' and 'str'` during
local-feed aggregation. Cleanup and the scheduler wrapper returned at 06:01:32.844;
their completion messages did not establish a successful import. Four UK records
had been retained, including one explicitly hidden for Manual Review.

The exact failure was reproduced locally with a RED regression test. Commit
`c4a977bbf6e7b118375bca5b5ab9ac4be48c6d40` (`Handle mixed local feed publication
dates`) replaces raw mixed-date sort keys with comparable timezone-aware date
keys in all three local-feed groups; source values and group priority remain
unchanged. Supplied GREEN QA: **8 passed** focused Cheshire East adapter tests;
**227 passed, 6 known warnings** broader regression; compilation and
`git diff --check` passed. See [Engineering History](HISTORY/ENGINEERING_HISTORY_MASTER.md).

### Corrective deployment and natural run

| Evidence | Observed value |
|---|---|
| SHA | `c4a977bbf6e7b118375bca5b5ab9ac4be48c6d40` |
| Service | `cheshiretoday-migration-` / `srv-d5virmm3jp1c73c9d6tg` |
| Deployment | `dep-db1jg8lg1s2s739nhsr0`, Deploy succeeded — Live |
| Started / startup complete / Live | 5 October 06:39:47 / 06:42:07 / 06:42:11 BST |
| Instance | `srv-d5virmm3jp1c73c9d6tg-8445df675c-jnkrn` |
| First post-hotfix natural article run | 5 October 12:00:00.001 BST; midday cron, scheduled at 12:00 BST |
| Lock | `article_gen_2026100511`, acquired at 12:00:00.252 BST |
| Execution | One observed execution; no duplicate/overlap observed |
| Completion | Wrapper/scheduler returned at 12:02:04.160 BST; 124.16 seconds |

Unlike the failed morning run, this run explicitly logged local-fetch and
local-processing completion, `Hybrid import complete`, and import return.
The previous datetime/string comparison exception did not recur. No `TypeError`,
`Error in hybrid news import`, `Error in generate_articles`, traceback or
error-level log appeared in the inspected 11:45–13:00 BST interval. No OOM,
crash loop, unexpected restart or fatal traceback was observed. Separate lock
release/ownership-token evidence was not retrieved; acquisition and the single
execution are the observed evidence.

### Source and editorial results

- All-feed candidates **1,917**; local candidates **218**, **213** with images.
  Completed local aggregation: **34 Cheshire Live + 163 other + 21 Nub News**.
- Retained/imported counts: **Local 7, UK 3, Finance 1, Business 5, Tech 4**.
  These may include Manual Review records and are **not all-public publication
  counts**. The human-readable final summary omitted Finance; the dedicated
  metric recorded one. Manual Review, public-cap and existing rejection/image/
  duplicate safeguards remained active.
- All eight Nub hubs returned HTTP 200: Macclesfield, Sandbach, Congleton,
  Nantwich, Crewe, Alsager, Chester and Wilmslow. Aggregation recorded 21 Nub
  candidates. Per-hub selected counts were not logged: runtime does not
  independently prove the three-per-hub bound; code/tests provide that evidence.
- Cheshire East Media Hub index and five release pages returned HTTP 200; no
  source-specific HTTP/parser failure was observed. Its exact contribution
  inside the 163 “other” candidates was not separately logged and is not inferred.

### Resources and retained observations

Current RSS: **169.9 MB** initially, **260.3 MB** after local fetching,
**271.0 MB** after local processing, **406.5 MB** finally; final `rss_mb` field
**404.8 MB**. Python heap peak **96.8 MB**, final current heap **0.5 MB**.
Cleanup read **4,441 documents per pass**, removing **0** records. These bounded
results do not close the separate cumulative-memory/OOM finding.

The two source-count limitations above remain. A crime-like filter rejection of
a headline beginning “Cheshire clean energy plan could create …” is a separate
non-blocking editorial observation; the truncated log cannot establish whether
classification was correct. It is not a hotfix failure or authority to change
filters. The rollout acceptance gate is closed **APPROVED WITH OBSERVATIONS**;
unrelated QA and historical-recovery limitations remain open.

## 4 October 2026 — combined locality and source-expansion deployment

Reconciled 5 October from the authenticated Render observation supplied/preserved
in the task, not a new production inspection. Exact deployed SHA:
`b83d2c3e4932a9870555b156a4c7e774eed8d226`. The combined chain includes `b27a7f1`,
`2cd1b6e`, `d0b14f5`, `b515af0` and `b83d2c3`; separate deployments are not
asserted for those individual commits.

| Evidence | Observed value |
|---|---|
| Service | `cheshiretoday-migration-` / `srv-d5virmm3jp1c73c9d6tg` |
| Deployment | `dep-db19qndckfvc73dh6ang`, Deploy succeeded / Live |
| Instance | `srv-d5virmm3jp1c73c9d6tg-7d974dd84d-w7p9z` |
| Deployment started | 4 October 2026, 19:39:25 BST |
| Application startup complete | 19:42:33 BST |
| Service Live | 19:42:44 BST |
| Public health | HTTP 200; `{"status":"healthy","service":"cheshire-news"}` |
| Post-start observation | Same instance serving through approximately 21:04 BST |

The inspected evidence showed no visible crash loop, OOM, fatal traceback or
post-deployment restart. The Twitter-credentials warning was non-blocking.
These are bounded observations, not an exhaustive absence-of-errors guarantee.
Startup registered the morning/midday/evening jobs and started the scheduler;
registration is not execution evidence.

**At the 4 October checkpoint: deployment and health verified; natural scheduled-run acceptance pending.**
This deployment followed the 4 October 18:00 slot. The first required slot was
5 October 06:00 BST. No verified result for that run is supplied by this
reconciliation, even though the nominal time has passed. Hub fetch/selection
counts, Cheshire East parser outcomes, Local review/import counts, lock ownership,
single execution, duration, memory and cleanup remain unverified for the new run.
Subsequent evidence: the 06:00 run failed; the corrective `c4a977b` deployment
and accepted 12:00 run are recorded above. This preserves the original checkpoint,
not a current pending gate.
Implementation/QA provenance: [Engineering History](HISTORY/ENGINEERING_HISTORY_MASTER.md)
and [Source Register](HISTORY/SOURCE_REGISTER.md).

## 24–26 September 2026 — suppression, deployment and deliverability evidence

`34ecf74` provider-suppression eligibility was deployed/verified; `5afd7b1`
records the corrected 815-record reconciliation. First attempt aborted/rolled
back for BSON precision mismatch; corrected attempt matched/modified/exact 815,
committed once, zero provider API calls or unsuppressions. At that observation:
14,267 subscribers, 11,673 active, 815 suppressed (583 active/232 inactive).

Owner-supplied evidence confirms service `cheshiretoday-migration-` Live at
`8ed19846ccf9242b646ea38440d71e1f85f59141`, public health HTTP 200.
This is preserved deployment evidence, not a fresh check by this reconciliation.
It supersedes the earlier lack of deployment evidence for ancestor `40304fc`;
it does not re-verify that welcome copy through a new receipt.

Controlled Gmail sources show SES-generated Feedback-ID on both Resend batch and
single delivery; the latter returned HTTP 200. Cheshire Today DKIM does not sign
Feedback-ID, SES DKIM does. Gmail controlled placement remains Spam despite
authentication/compliance; Resend support response is pending.

Read-only September 26 cohort and historical audits are preserved with their
snapshot boundaries in [the detailed evidence record](HISTORY/NEWSLETTER_DELIVERABILITY_2026-09-26.md).
The May suppression burst is associated in time with import/rotation/capacity
changes, not proven to cause later reputation deterioration. No production
operations were repeated to reconcile these records.


> **Reconstruction status:** selected production evidence reconciled through the 5 October `c4a977b` natural-run acceptance, APPROVED WITH OBSERVATIONS, with supplied evidence labelled. A historical “deployed” statement
> is retained as a dated claim unless matching live verification is recorded.

## Document purpose

This document separates deployments, incidents, data operations and production
verification gates from general engineering history.

## How to use this document

- Read the event type and verification column before treating a commit as live.
- Use the [Engineering History](HISTORY/ENGINEERING_HISTORY_MASTER.md) for build
  sequence, the [Decision Register](DECISION_REGISTER.md) for rationale and the
  [Source Register](HISTORY/SOURCE_REGISTER.md) for authority.
- Production state after current HEAD belongs in the unreconciled section until it
  is preserved in the repository.

## Deployments and activations

### 20 September 2026 — CT-QA-2026-007 generic-entry UX

Service `cheshiretoday-migration-` (`srv-d5virmm3jp1c73c9d6tg`) automatically
deployed exact SHA `e6408133c48a98b2e22e8cf22a958bce7a922716` through
`dep-dao287ajnfac739ab80g`, instance `cqsqq` (Live / Deploy succeeded).
BST timestamps: start 19:21:17; build success 19:22:55; startup complete 19:23:45;
Live 19:23:47. Build, backend, Mongo/index and scheduler startup were normal;
bounded logs showed no attributable traceback, OOM/exit 137, crash or restart loop.
Health/homepage and all three generic management routes returned HTTP 200.
Neutral request-link UI and 390×844 layouts passed. **IMPLEMENTED, DEPLOYED AND
PRODUCTION-VERIFIED** applies to the generic-entry defect only. No form was
submitted; network capture was unavailable. The Apple Mail CTA issue remains
separate and unresolved. See [QA evidence](QA/OPEN_FINDINGS.md).

| Date/time | Environment | Event type | System | Change or incident | Commit/deployment | Verification | Impact | Resolution/follow-up | Sources |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 February 2026 | Render production | Initial deployment | Full stack | Initial repository deployment to Render | `789e9c8` | Later operational records describe live Render service; original event detail is limited | Established production baseline | Subsequent health, API and frontend stabilisation | [Preserved state](ARCHIVE/PROJECT_STATE_REDACTED_2026-08-06.md), early history; Git `789e9c8` |
| 4–9 February | Render production | Activation/stabilisation | API/Admin | Health endpoint, article caching, URL and Admin auth corrections | `ef7cfbc`, `c7fe038`, `223cc34` | Later health and Admin operation records | Improved availability and routing | Continued scheduler/editorial work | Preserved state, February sections; cited Git |
| 3–18 March | Render production | Deployment sequence | SEO/article routes | Slug canonical routes, redirects, crawler HTML and social previews | `0f6f4e0`, `82e193f`, `f4324ac`, `bc170be`, `c9aa4a5` | Repository records include live crawler/social verification | Stabilised article identity and shared links | July canonical consolidation followed | Preserved state, March SEO updates; cited Git |
| 7–17 March | Render production | Pipeline activation | Scheduled imports | Long-form hybrid RSS/Perplexity generation with timeouts and content floors | `000fb94`, `bd762fc`, `53d5911`, `0091276` | Live regeneration/import records in state history | Fuller articles; unsafe short output archived | Repeated editorial and memory hardening | Preserved state, March import sections; cited Git |
| 2 April | Render production | Scheduler deployment | Scheduler | Europe/London timezone, DST-correct jobs and archive-cron removal | `2e3b17d`, `be47a48`, `ad2e3b2` | Subsequent scheduled-run records use BST/UTC distinction | Prevented timing drift and age-based deletion | Retain manual cleanup only | Preserved state, April scheduler sections; cited Git |
| 11 April | Production newsletter | Provider cutover | Newsletter | Daily Brief and Weekly Roundup moved to Resend batches | `f76248a`, documented by `fe5fe97` | Per-recipient tracking and test-send records | Replaced SMTP loop; enabled batch evidence | Caps, rotation and memory controls added | Preserved state, “Resend newsletter cutover”; cited Git |
| 25–30 April | Production | Feature activation | Advertising | Manual sponsored placements, Admin management, payment and reporting workflow | `282a503`, `2d65bdb`, `bc734d0`, `4f4d22e` | Repository records describe live readiness and webhook verification; individual placement activation varies | Established controlled paid-placement system | Continue manual review and payment verification | Preserved state, April advertising sections; cited Git |
| 12–31 May | Production | Workflow activation | Manual Review | Hidden review records excluded from public surfaces and editable/restorable through Admin | `8bcc6bf`, `7dda210`, `a1980d2`, `d426558`, `067288e` | Live cleanup and Admin workflow observations recorded | Separated unsafe candidates from public publication | July state/ID separation hardened it | Preserved state, May Manual Review sections; cited Git |
| 22 June–12 July | Production/Admin | Controlled activation | OpenAI editorial draft | Admin-only OpenAI draft, source/fact-pack research and editorial guard | `ad131c7`, `5ef4041`, `2723fc7`, `3fcc4a3`, `83d8d69` | Controlled draft diagnostics; drafts were not auto-saved or published | Added human-review writing assistance | Continue claim-by-claim verification | Preserved state, June/July OpenAI sections; cited Git |
| 18–27 July | Production | Security activation | Newsletter management | Secure preference, unsubscribe and reactivation request/challenge flows | `be98b43` through `db8fae1`; tag `newsletter-security-v1.0` | Focused tests and production provisioning records; zero duplicate normalised emails recorded | Removed legacy management-link risk | Maintain request limits and one-use challenges | [July log](HISTORY/ENGINEERING_LOG_JULY_2026.md), newsletter security sections; cited Git |
| 21–26 July | Production | Staged source activation | Local RSS | Newsquest/Knutsford and Nantwich staged Local RSS rollout | `3f4ab10`, `6d87817`, `9cfb187`, `c80ca7e` | Scheduled imports and Manual Review counts recorded | Increased local supply without bypassing gates | Continue source-by-source observation | July log, Local RSS sections; preserved state; cited Git |
| 26–28 July | Repository and production Admin | Feature activation | Brand/Social Publishing | Brand Library v1, Facebook/Instagram/Threads assets and unified Social Publishing Admin | `86794f6`, `2f4e1a0`, `9902e3c`, `2bcdf5c` | Automated asset tests and later Admin bundle verification; no automatic posting | Standardised creation/copy/download workflow | Publishing remains manual | July log, social sections; [brand assets](brand-assets/); cited Git |
| 27 July | Production baseline | Milestone | Version 1 | Version 1 completion documented | `ffa7f9d` | Documentation and production baseline recorded; not a claim that all future work stopped | Closed Version 1 engineering scope | Version 2 work remained separately gated | July log, “Version 1 completion”; Git `ffa7f9d` |
| 30–31 July | Production | Analytics deployment | Article views/Most Read | First-party article-view repair and period-correct Most Read | `6a95ba9`, `a93d4bf`, `d6eb46b` | Focused/live checks documented; Most Read no longer used lifetime fallback | Restored trustworthy period ranking | Later Admin analytics built on these events | July log, analytics sections; cited Git |
| 1 August | Production | Analytics activation | Admin/Facebook attribution | Admin dashboard and deterministic Facebook UTM attribution | `cac9b24`, `9b024cc` | Repository records say Phase 2A was functionally production-verified; detailed task evidence awaits Codex reconciliation | Added privacy-bounded first-party attribution | No Meta API or raw attribution storage | Preserved state, Admin Analytics sections; cited Git |
| 1 August | Production | Deployment/verification | Metadata | Static-shell/Helmet reconciliation | `6bfe896`, `1e5c2da`, documented by `7ca1269` | Health 200, settled DOM, crawler, sitemap and robots checks recorded | Removed duplicate route metadata and Admin leakage | Search Console recovery not claimed | Preserved state, metadata verification sections; cited Git |
| 1–2 August | Production/Admin | Mobile deployment | Admin editor/cards | Mobile Safari input, editor containment/sticky close and responsive Admin cards | `2d7ed9f`, `6328cf3`, `a6bfb78`, `cf0ae79`, `761a7c2`, `f43c4ef` | Real-iPhone evidence recorded for editor; Page Zoom 100% requirement identified | Restored usable mobile Admin editing and card containment | Broader navigation/dialog work deferred | Preserved state, August mobile sections; cited Git |
| 4 August, approximately 14:15 BST | Render production | Shadow activation | Editorial Similarity | Scheduled-only log-only Phase 2B deployed | Scorer `8043fdd`; integration `5e1a875`; deployment record `1601ae4` | Render marked `5e1a875` live according to repository record | Added advisory evidence only; no publication decision changed | Observe at least three normal runs | Preserved state, “Editorial Similarity deployment and production-observation gate”; cited Git |
| 7 August, 11:16–11:19 BST | Render production | Automatic deployment | Duplicate cleanup | Lifecycle-only release of first-pass duplicate-cleanup references before the second full read | `49e5fe49cc35e0ca020e8520db6365d356760060` | Build succeeded; Uvicorn startup completed; service became live before the 12:00 run; health returned 200 | Removed simultaneous reachability of both decoded collection lists without changing cleanup semantics | Verify only through normal scheduled runs | Git `49e5fe4`; authenticated Render deployment and health evidence reconciled 8 August |
| 26 August 2026 | Render production | SEO closure deployment | Admin indexing protection | Add first-byte Admin response directives and explicit crawler-specific robots exclusions | Revision `24f381e`; deployment `dep-da7ala710e5c738ovtm0`; instance `824s7`; Standard 2 GB / 1 CPU | GET/HEAD `/admin` and `/admin/` returned 200 without redirect with exact `X-Robots-Tag`; `/admin/settings` remained 404 with first-byte noindex; public routes, metadata, JSON-LD, both sitemaps, Admin API protection and health passed | Closed `QA-SEO-002` without changing Admin access control or public indexing behaviour | **CLOSED — PRODUCTION VERIFIED**; indexing controls are not authentication or authorization | Git `24f381e`; authenticated production verification reconciled 26 August 2026 |
| 2 September 2026 | Render production | Performance deployment | Homepage article list | Skip an unused count and cap Local/UK candidate materialisation at 100 only for the exact 80-item public homepage list shape | Revision `70057e1`; deployment `dep-dabrjseq1p3s73fsvf7g`; initial instance `xmx4p`; Standard 2 GB / 1 CPU | Deployment live and healthy; no startup failure, traceback, restart/OOM, Bad Gateway or material 5xx observed | Preserved force/fallback, editorial selection, query/projection/sort and response contracts while reducing bounded database materialisation | Run one controlled five-request like-for-like observation with the timing gate, then remove it | Git `70057e1`; authenticated Render verification |
| 4 September 2026 | Render production | Performance verification | Homepage article list | Compare `70057e1` against the `15695cb` five-request baseline | Observation deployment `dep-dad5jv2jnfac73ehqh20`, instance `cs5n2`; final gate-removal deployment `dep-dad5pcgn74is73dd4mj0`, instance `gldsq` | Median handler 1,081.639→708.314 ms (-34.5%), TTFB 1,868.333→1,544.086 ms (-17.4%), total 1,897.497→1,587.383 ms (-16.3%); count 0 ms, Local/UK 255.975/132.848 ms; 5/5 HTTP 200, 79 articles, stable bytes, fallback 0/5 and exactly five markers | **MATERIAL IMPROVEMENT — QA-PERF-001 OPTIMISATION VERIFIED.** No statistical/site-wide closure is claimed | Gate removed; SHA remained `70057e1`, health 200. Measure the 839.327 ms median post-handler/client residual separately before further optimisation | Authenticated Render logs, bounded client measurements and health verification reconciled 4 September 2026 |
| 19 September 2026, 08:11:55–08:14:30 BST | Render production | Automatic deployment and controlled acceptance | Newsletter signup funnel | Add backend-authoritative anonymous daily signup-attempt/outcome measurement and Admin aggregation | Service `cheshiretoday-migration-` (`srv-d5virmm3jp1c73c9d6tg`); `66fde1004a322d540bf9ac3197dab6b80152428b`; `dep-dan3beojo6nc7395spm0`; instance `fkdbq`; Standard 1 CPU/2 GB, one instance, `WEB_CONCURRENCY=1` | Deployment started 08:11:55, build completed 08:13:38, application startup completed 08:14:28 and Live 08:14:30; Uvicorn, Mongo, scheduler and funnel indexes started normally; health, homepage, `/newsletter`, representative article and `/admin` returned 200. During the bounded deployment/startup/post-start review, no attributable traceback, material 5xx, Mongo/index failure, OOM, exit 137 or restart was observed. One controlled authorised signup returned HTTP 200/`created`; subscriber defaults and exact anonymous `newsletter_landing` delta `1/1/0/0/0` were verified; Admin reporting matched with 100.0% created conversion | **NEWSLETTER FUNNEL V1 PRODUCTION ACCEPTANCE PASSED.** No inbox-delivery or exact-once claim; acceptance subscriber remained active and intact | Record pre-existing full-email subscribe/welcome logging separately as `CT-QA-2026-006`; do not attribute it to the anonymous aggregate | Git `66fde10`; authenticated Render/Admin, bounded Mongo and application-log evidence reconciled 19 September 2026 |
| 19 September 2026, 21:10:44–21:13:17 BST | Render production | Automatic deployment and bounded verification | Newsletter logging privacy | Remove subscriber/recipient identity and uncontrolled exception text from bounded subscribe, welcome, SMTP, scheduled and Admin diagnostics | Service `cheshiretoday-migration-` (`srv-d5virmm3jp1c73c9d6tg`); `03a6abbd5133de969275477488ea49bb34242ee0`; `dep-daneoh6q1p3s73cdmf9g`; instance `zpcmz`; Standard 1 CPU/2 GB, one instance | Build completed 21:12:25, application startup completed 21:13:12 and Live 21:13:17. Uvicorn, Mongo/index and APScheduler startup succeeded; article-generation, Daily Brief and Weekly Roundup registrations were present. Health, homepage, `/newsletter` and a representative article returned 200. Bounded post-Live observation found no attributable logging-format/changed-variable failure, traceback, fatal error, OOM, exit 137, restart or material 5xx | **CT-QA-2026-006 CLOSED — IMPLEMENTED, TESTED, DEPLOYED AND PRODUCTION-VERIFIED.** Logging hardening only; subscriber/delivery/Funnel semantics preserved | Every failure branch was not naturally exercised; focused/regression tests cover those branches. No deliberate production failure, signup or test send occurred. Historical logs were not altered and no compliance claim is made | Git `03a6abb`; 47 focused passes; 1,145 relevant regression passes with 12 skipped; authenticated Render and bounded public verification reconciled 20 September 2026 |

## Production incidents

| Date/time | Environment | Event type | System | Change or incident | Commit/deployment | Verification | Impact | Resolution/follow-up | Sources |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| March 2026 | Production/startup | Data-loss risk | Duplicate cleanup | First-five-word startup duplicate cleaner removed legitimate recent articles | Pre-fix runtime; disabled by `3ca0834` | Code/history and pool-safety investigation | Recent records could disappear | Startup call disabled; later exact/source URL rules retained | Preserved state, “Emergency stability update”; Git `3ca0834` |
| March–April | Production | Freshness incident | Homepage/pool | Stale ordering, repeated stories and pool starvation followed competing cap/fallback experiments | Multiple March commits/reverts | Live homepage observations in state history | Poor freshness and duplicates | Stable allocation, deeper bounded pool and backend ordering fixes | Preserved state, March/3 April updates; Git `b4612e1`, `0e1d639` |
| 12 April | Production | State regression | Archive/live pool | Auto-cap could unarchive manually archived records | Resolved by `707da88` | Live pool audit and post-fix cleanup | Editorial removals could reappear | Durable archive-reason guard | Preserved state, 12 April archive section; Git `707da88` |
| 22 May | Render production | OOM | Daily Brief | Confirmed 512 MB OOM during a 2,000-recipient send | Runtime incident; later mitigation commits | Recorded in project state and QA `QA-OPS-001` | Service memory limit exceeded | Recipient caps, batch/memory changes; later observability | [QA report](QA/QA_REPORT_2026-07-29.md), `QA-OPS-001`; Git `9580cbd`, `55f36ac` |
| 24–25 May | Production engineering | Rollback | Import/AI verification | Broad verification/Manual Review/Gemini changes were introduced then reverted | Multiple commits and explicit reverts | Git history and 25 May project update | Unstable combined import behaviour | Restore narrower Perplexity flow; pause Gemini | Preserved state, “Major QA / Import Rollback”; Git reverts `d0e8399`, `7fef821`, `a796691` |
| July 2026 | Render production | Intermittent OOM concern | Article generation | Historical intermittent generation-time memory failures lacked phase attribution | Before `42736f9` | QA found risk but no sufficient Render metrics | Unclear feed/cleanup peak source | Add twelve phase markers; observe before optimising | QA `QA-OPS-001`; July log memory section; Git `42736f9` |
| 29 July | Repository/security | Critical QA finding | Admin tests | Admin credential was present in tracked legacy tests/history and external tests could mutate production | Baseline `2bcdf5c`; containment `b804cdd`, `603e11b` | QA `QA-SEC-001`, `QA-TEST-001` | Credential and unsafe-test risk | Remove current-tree exposure and enforce loopback-only tests; production rotation was not proven at that checkpoint | QA report and cited Git |
| 29 July | Production/API | Security finding | CORS | Credentialed CORS accepted arbitrary origins | Baseline `2bcdf5c` | QA `QA-SEC-002`, including live preflight | Weakened browser origin boundary | Later status requires QA reconciliation; do not infer resolved here | QA report `QA-SEC-002` |
| 1 August | Production | Metadata regression | Browser/Admin | First dedupe deployment fixed public core tags but left Admin homepage leakage and social tag duplication | `6bfe896`; follow-up `1e5c2da` | Live settled-DOM verification | Ambiguous head metadata | Managed all conflicting shell tags and reverified | Preserved state, metadata sections; cited Git |
| 1 August | Production/iPhone | Usability incident | Admin editor | Safari retained focus enlargement; translated editor clipped and close control became inaccessible | `2d7ed9f` followed by `6328cf3`, `a6bfb78` | Real-iPhone tests | Difficult mobile editing/closing | Top-aligned editor, sticky close; Safari zoom not disabled | Preserved state, mobile sections; cited Git |
| 7 August, 06:00–06:43 BST | Render production | OOM | Scheduled article cleanup | The scheduled job completed after rising from 385.3 MB to 530.0 MB high-water; Render reported OOM at approximately 06:42 and recovered approximately 06:43 | Before `49e5fe4` | Twelve markers showed 431.7 MB at visible-pool cap, 466.6 MB after first cleanup read and 530.0 MB after second read; verified ceiling 512 MB | Service exceeded its memory ceiling after job completion | Static investigation found first-pass articles, duplicate groups and residual loop references still reachable during the second full materialisation | Authenticated Render logs and code investigation reconciled 8 August; Git `49e5fe4` |

## Data and content operations

| Date/time | Environment | Event type | System | Change or incident | Commit/deployment | Verification | Impact | Resolution/follow-up | Sources |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| March–April 2026 | Production database | Live cleanup | Articles | Duplicate, stale and weak-fit records were manually archived during homepage/import stabilisation | Operational actions; supporting code around `b4612e1`, `707da88` | Before/after live pool audits recorded | Improved public quality; carries mutation history | Preserve archive reasons and avoid recreating via caps | Preserved state, March/April cleanup sections |
| 6–7 April | Production database | Subscriber import/test send | Newsletter | Bulk subscriber imports and first-live-send safety batches | Operational work; `25cb127` cap | Test send and recipient totals recorded historically | Established initial newsletter audience | Later Resend cutover and engagement rotation | Preserved state, April subscriber/newsletter sections |
| 7 April | Production database | Content seeding | Authority guides | Six commercial guides seeded as drafts, visually checked and promoted | Runtime data operation; frontend follow-up `aae3a97` | Public route and visual checks recorded | Created initial commercial guide set | Continue disclosure and provider review | Preserved state, 7 April guide section; Git `aae3a97` |
| 11 April | Production database | Index/tracking change | Newsletter | Per-recipient delivery IDs and Admin aggregation introduced | `11d56f2`, `77af404` | Live tracking verification recorded | Recipient-attributable engagement; not the later accepted-send ledger | September 26 correction: accepted ledger introduced July 14 (`bbea335`); acceptance is not delivery | Preserved state, Resend tracking section; cited Git |
| 21 July | Production database | Image backfill | Articles | Newsquest image pipeline and guarded historical backfill | `c1356ea`, `93a38e4` | Backfill completion recorded | Improved article/social imagery | Keep source attribution and image validation | July log, image milestone; cited Git |
| 24 July | Production database | Controlled repair | Live pool | Repair utility restored eligible auto-capped records after cleanup/cap starvation | `be5c4ed`, `dc18e65` | Counted repair and production checks recorded | Refilled eligible visible pool | Retain guarded/dry-run repair semantics | Preserved state, 24 July live-pool sections; cited Git |
| 27 July | Production database | Unique-index provisioning | Subscribers | Normalised-email audit found zero duplicate groups; guarded unique index provisioned | `0bb3ce8` | Counts/index status recorded | Enforced one subscriber per normalised email | Retain safe duplicate-key handling | July log, production data work; Git `0bb3ce8` |

## Production verification gates

| Date/time | Environment | Event type | System | Change or incident | Commit/deployment | Verification | Impact | Resolution/follow-up | Sources |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 27 July | Production/repository | Completion gate | Version 1 | Version 1 declared complete | `ffa7f9d` | Platform, newsletter, Manual Review, security and social evidence summarised | Established stable baseline | Future opportunities kept separate | July log, Version 1 completion |
| 29 July | Production/repository | QA gate | Whole platform | Post-release audit at `2bcdf5c` | QA baseline | Public/crawler/frontend passed with critical/high findings | New release not unconditionally approved | Security/test/code/CORS work required | [QA report](QA/QA_REPORT_2026-07-29.md) |
| 31 July | Production/repository | Observation gate | Memory | Generation phase markers introduced | `42736f9` | Local regression validation; production latency/memory observation required | Evidence collection without optimisation | Compare normal runs and high-water marks | July log, memory section |
| 1 August | Production | Verification gate | Metadata | Seven-field uniqueness and crawler preservation checked | `1e5c2da`, documented `7ca1269` | Health, DOM, SPA, crawler, sitemap and robots checks passed | Follow-up verified in production | Search Console recovery remained unclaimed | Preserved state, metadata production verification |
| 1–2 August | Production/iPhone | Verification gate | Admin mobile | Physical-device editor and layout checks | Through `a6bfb78`, `f43c4ef` | Login/editor checks recorded; broader all-browser coverage not claimed | Operational mobile usability improved | Navigation/other row work separate | Preserved state, mobile production sections |
| 4 August | Render production | Observation gate | Editorial Similarity | Phase 2B marked live | `5e1a875`, record `1601ae4` | Deployment recorded, calibration explicitly not proven | Shadow evidence collection began | Require at least three normal scheduled runs | Preserved state, final section; cited Git |
| 7 August, 12:00 BST | Render production | Post-fix verification | Duplicate cleanup memory | First normal run after `49e5fe4` | `49e5fe4` | 123.6 MB start, 228.9 MB visible cap, 236.4 MB first read, 265.8 MB second/final; second-read increase 29.4 MB; runtime 103.07 seconds; no OOM or restart | Lifecycle release behaved safely; cleanup removed zero records | Continue normal-run monitoring | Authenticated Render logs reconciled 8 August |
| 7 August, 18:00 BST | Render production | Post-fix verification | Duplicate cleanup memory | Second normal run after `49e5fe4` | `49e5fe4` | 314.8 MB start, 341.8 MB visible cap, 343.0 MB first read, 351.6 MB second/final; second-read increase 8.6 MB; runtime 49.45 seconds; no OOM or restart | Strengthened evidence that simultaneous-list amplification was removed | Require high-start comparison | Authenticated Render logs reconciled 8 August |
| 8 August, 06:00 BST | Render production | Post-fix verification | Duplicate cleanup memory | High-start comparison with the pre-fix OOM run | `49e5fe4` | 377.2 MB start, 406.4 MB visible cap, 432.9 MB first read, 473.6 MB second/final; second-read increase 40.7 MB; runtime 77.32 seconds; 38.4 MB below ceiling; zero removals and no OOM/restart during the observed window | Immediate duplicate-cleanup lifecycle OOM risk classified as operationally mitigated | Continue broader memory monitoring; do not infer all memory risk is gone | Authenticated Render logs reconciled 8 August |
| 10 August | Render production | Cleanup hardening | Duplicate cleanup memory | Stream/project the second short-content scan, then the first duplicate scan | `c06c837`, `cd3f093` | Natural runs showed structural improvement; first-pass Stage 2 remained mixed with the short scan until a later marker | Removed both unrestricted cleanup materialisations while preserving full archive payloads through re-fetch/revalidation | Separate remaining intervals before selecting more work | Git and authenticated Render evidence reconciled 11 August |
| 10 August, 19:13 BST | Render production | Observability deployment | Duplicate cleanup memory | Add `duplicate_cleanup_first_stage2_completed` and retain current-RSS logging | `0cdc089` | Healthy deployment on instance `tdc7g`; phase inventory increased from 12 to 13 | Isolated first-pass Stage 2 from the projected short-content scan | Observe natural runs only | Git and authenticated Render evidence reconciled 11 August |
| 11 August, 06:00 BST | Render production | Separated observation | Duplicate cleanup memory | First natural 13-marker run | `0cdc089` | Current RSS: visible pool 210.0 MB, first scan 232.4 MB, first Stage 2 231.5 MB, short scan/completion 257.5 MB; 4,066 documents scanned | First Stage 2 negligible (-0.9 MB); short-content projected scan dominated cleanup at +26.0 MB | Audit string allocation without changing cursor semantics | Authenticated Render logs reconciled 11 August |
| 11 August, 07:06 BST | Render production | Automatic deployment | Short-content memory | Avoid full joined and joined-lower article strings while preserving qualification semantics | `1811430070cfa73084c8b5ded830fa88076d3cc7` | Build/startup/health succeeded; instance `jpk6g` became live | Safe bounded allocation change | Validate on the natural 12:00 run | Git and authenticated Render deployment evidence reconciled 11 August |
| 11 August, 12:00–12:01 BST | Render production | Natural validation | Article generation memory | Validate `1811430` using all 13 markers | `1811430` | Lock `article_gen_2026081111`; runtime 94.63 s; current RSS 202.3→338.6 MB; first scan +44.2 MB, first Stage 2 0.0 MB, short scan +28.5 MB over 4,087 records; no OOM/restart/failure; health 200 | String change remained semantically safe but showed no material RSS improvement versus +26.0 MB; cumulative memory stays Monitoring/Medium | Obtain another natural run before selecting a new target | Authenticated Render scheduler, memory and health evidence reconciled 11 August |
| 11 August, 14:42–15:03 BST | Render production | Security closure | Admin authentication | Rotate the Git-history-exposed Admin password and invalidate pre-rotation sessions | Deployment `dep-d9tiku142hec738apl80`; revision `3b3f4c9`; instance `6xgfs` | Only `ADMIN_PASSWORD` changed; nine pre-rotation tokens invalidated at 14:42:29; build succeeded 14:59:53, startup completed 15:00:49 and service became live 15:00:55; replacement login/token verification passed, historical login returned 401 and health returned 200 | Revoked the historical password without rewriting Git history or changing `ADMIN_PERMANENT_TOKEN`; `QA-SEC-001` closed | Retain current-tree hygiene and treat credentialed wildcard CORS as the highest-priority unresolved security finding | Authenticated Render/Admin/Mongo verification reconciled 11 August 2026 |
| 12 August, 12:10–12:13 BST | Render production | Security closure | Credentialed CORS | Replace wildcard browser origins with the canonical production origin and explicit local-development origins | Deployment `dep-d9u594oae00c73bs1lvg`; revision `b497635`; instance `qmqjs` | Build and startup succeeded; service live at 12:12:56; health 200; canonical-origin preflight 200 with exact ACAO and credentials; hostile-origin preflight 400 without ACAO; fresh Admin login and authenticated access passed; homepage, article and newsletter returned 200 | Restored an explicit browser-origin boundary without changing credentials, methods or headers; `QA-SEC-002` closed | Scheduler lock fail-open review becomes the highest-priority unresolved security/reliability item; no production regression observed | Git `b497635`; focused tests and authenticated Render/Admin/preflight verification reconciled 12 August 2026 |
| 13 August, 18:00–18:01 BST | Render production | Reliability closure and observation | Article scheduler and memory | Verify fail-closed article-lock compatibility on the natural scheduled run and capture all thirteen memory markers | Revision `d8943e8`; instance `qc88z` | Start 18:00:00.001; lock `article_gen_2026081317` acquired 18:00:00.245; one start/acquisition/generation/cleanup/completion; finish 18:01:45.983; runtime 105.98 s; APScheduler success and health 200 | `CT-QA-2026-003` closed without inducing a production lock failure. Current RSS rose 130.7→305.5 MB (+174.8 MB), leaving 206.5 MB marker-level headroom; no OOM/restart | `QA-OPS-001` remains open: +32.7 MB visible-pool, +41.0 MB first duplicate Stage 1, 0.0 MB first Stage 2 and +42.0 MB short-content scan; obtain another normal run before choosing work | Git `d8943e8`; seven focused lock tests; authenticated Render scheduler, marker and health evidence reconciled 13 August 2026 |
| 15 August, 09:01 BST | Render production | Shadow feature deployment | Editorial Similarity | Deploy bounded deterministic event-anchor evidence without routing or publication changes | Deployment `dep-da01o93ncjis738c7m8g`; revision `5e8f0ef`; instance `65q7v` | Service live 09:01:05; build/startup, Mongo and scheduler healthy; public health HTTP 200 | `phase2a_event_anchors_v1` available in scheduled shadow mode; scorer weights/bands, 50+50 corpus, shortlist 20 and publication behaviour unchanged | Observe the next natural run; no manual import or routing decision | Git `5e8f0ef`; authenticated Render deployment/startup evidence reconciled 15 August 2026 |
| 15 August, 12:00–12:01 BST | Render production | Natural shadow verification | Editorial Similarity and article-generation memory | Verify the first natural run of bounded event-anchor evidence | Revision `5e8f0ef`; instance `65q7v` | Start 12:00:00.001; lock `article_gen_2026081511` at 12:00:00.251; one execution; finish 12:01:38.700; runtime 98.70 s; APScheduler success and health 200. Indexes 4,305 active/3,651 archived; 1,790 feed candidates; imports UK 4, Finance 0, Local 0, Business 0, Tech 1; both cleanup scans 4,325; removals 0 | All 20 shadow evaluations used `phase2a_event_anchors_v1` and `scheduled_log_only` (19 scored, one `no_match`); 17 emitted bounded codes. Observed codes were `format_guard`, `cross_source`, `same_run` and `locality_overlap`; no high-specificity or `same_run_event_compatible` case occurred. Publication state remained unchanged. Current RSS 129.8→291.9 MB (+162.1 MB), peak 291.9 MB, about 220.1 MB headroom; no observable material event-anchor regression | **SHADOW EVENT-ANCHOR FEATURE VERIFIED — CONTINUE CALIBRATION.** CT-QA-2026-004 and QA-OPS-001 remain open; future routing remains separately gated and unapproved | Authenticated Render scheduler, shadow-log, marker, database-metadata and health evidence reconciled 15 August 2026 |
| 20 August, 15:53–15:56 BST | Render production | Isolated memory experiment deployment | Short-content cleanup scan | Apply `batch_size(250)` only to the projected short-content cursor | Revision `b3550c0`; deployment `dep-da3h9s1srm7s739aqadg`; instance `zthtp`; Standard 2 GB / 1 CPU | Auto-deployment became live with startup, scheduler and health checks passing; first duplicate cursor, visible pool, projections, Stage 2 and archive/delete contracts remained unchanged | Enabled a bounded production test of cursor-batch RSS expansion without combining another optimisation | Observe two natural runs; keep `QA-OPS-001` High Open | Git `b3550c0`; authenticated Render deployment verification reconciled 20 August 2026 |
| 20 August, 18:00–18:01 BST | Render production | Natural experiment observation 1 | Short-content cleanup scan | First natural run with `batch_size(250)` | Revision `b3550c0`; instance `zthtp`; lock `article_gen_2026082017` | One scheduled execution; short scan 247.5→251.4 MB (+3.9 MB), 4,249 records, 2.68 s; full runtime 101.62 s; removals 0; normal health | Strong improvement versus supplied pre-batch +26 to +51 MB range, without material runtime or observed semantic regression | Second natural run still required before keep/revert decision | Authenticated Render scheduler, marker, cleanup and health evidence reconciled 20 August 2026 |
| 21 August, 06:00–06:01 BST | Render production | Natural experiment observation 2 and decision | Short-content cleanup scan | Second required natural run with `batch_size(250)` | Revision `b3550c0`; instance `zthtp`; lock `article_gen_2026082105` | One scheduled execution; short scan 381.3→382.3 MB (+1.0 MB), 4,264 records, 2.65 s; full runtime 92.06 s; removals 0; normal health | Two-run mean +2.45 MB versus supplied pre-batch mean about +39.5 MB; strong replicated improvement, unchanged marker order and normal Stage 2 completion; no material runtime regression | **PROVISIONAL KEEP.** QA-OPS-001 remains High Open; Standard remains temporary mitigation. Heap/RSS retention persists, archive-before-delete was not dynamically exercised, and the +57.7 MB visible-pool interval is evidence for separate review only | Authenticated Render scheduler, marker, cleanup and health evidence reconciled 21 August 2026 |
| 27 August, 13:12–13:15 BST | Render production | Accessibility closure | Public search | Deploy and verify semantic search naming, links, keyboard/focus and polite status feedback | Revision `dcd5cfa`; deployment `dep-da82j9uk1f9s73dgc1mg`; instance `9sflp`; Standard 2 GB / 1 CPU | Build succeeded; startup completed 13:14:42 and service became live 13:14:52. Desktop and 390×844 mobile checks verified `Search news` naming, native result links and destinations, focus/Escape, `Searching…`, result-count and `No articles found` states, usable mobile targets and no overflow. Homepage, article, Local category and authority guide loaded; health returned 200 | Closed `QA-A11Y-001` without a header redesign, custom combobox, backend search change or public-surface regression | **CLOSED — PRODUCTION VERIFIED.** Failure messaging and stale-response cancellation rest on deployed code/tests; no production failure was manufactured and no full WCAG/screen-reader certification is claimed | Git `dcd5cfa`; authenticated Render and public-browser verification reconciled 27 August 2026 |
| 6 September 2026, 09:00–12:00 BST | Render production | Natural reliability verification | Weekly Roundup slot-aware idempotence | Observe all four scheduled Sunday slots after `5559499` without a manual send | Revision containing `5559499`; instance `gldsq` | Slots 1–4 each selected 1,000 recipients and recorded 1,000/1,000 application/provider-path acceptance with four distinct tracking identities; cursor advanced 996→1996→2996→3996. No `E11000` conflict was found, and later production startup confirmed the unique index on `(digest_time, date_key, weekly_roundup_batch_slot)` | **NATURAL VERIFICATION COMPLETE.** The original idempotence reliability-validation loop is complete | Continue delivery/bounce, engagement, unsubscribe, growth and commercial monitoring. Acceptance does not prove final inbox delivery or readership | Authenticated Render scheduled-send, cursor and startup logs reconciled 9–10 September 2026 |
| 7 September 2026 | Search Console and live production | Read-only canonical audit | Alternate page with proper canonical tag | Reconcile representative report examples with current routes, crawler output, sitemaps and internal links | Current application revision `de87f232`; Search Console report 82 examples, `Validation Failed`, latest report update observed 4 September 2026 | Sampled query consolidation was intentional; sampled historical UUID canonicals identified the same current Mongo articles; current public canonicals, archived noindex, both sitemaps and internal links were coherent. All 82 examples were not inspected | **MOSTLY HISTORICAL ALTERNATE URLS — CURRENT IMPLEMENTATION HEALTHY.** No current canonical defect or code change confirmed | **DO NOT PRESS VALIDATE FIX NOW.** Allow natural Google recrawl; recheck after a later report update or newly crawled current mismatch | Authenticated Search Console representative inspection plus read-only live and repository evidence reconciled 7 September 2026 |
| 17 September 2026, 20:10–20:13 BST | Render production | Analytics consent deployment and bounded acceptance | Third-party analytics | Deploy versioned consent-gated GA4, Plausible and PostHog loading, application-owned SPA page views, sensitive-route exclusion, URL normalisation and withdrawal support | Revision `be0182b`; deployment `dep-dam3mb3ncjis73cit8mg`; service `srv-d5virmm3jp1c73c9d6tg`; instance `w8frn`; Standard 1 CPU/2 GB | Auto-Deploy started 20:10:36, build succeeded 20:12:24, application startup completed 20:13:09 and service became live at 20:13:16; duration 2m40s. Health returned HTTP 200. Observable Unknown/Rejected/Accepted/withdrawal/reload behaviour, direct `/admin` script exclusion, mobile 390×844 layout and recorder absence passed; no deployment-attributable traceback, OOM, exit 137, restart loop, Bad Gateway or material 5xx was observed | Implementation complete, automated verification passed, deployment verified and observable production consent behaviour passed; no defect confirmed | **ANALYTICS CONSENT PRODUCTION EVIDENCE INCONCLUSIVE** at event level. A second attempt stopped as **EVENT-LEVEL PRODUCTION VERIFICATION TOOLING UNAVAILABLE** because isolated storage plus request interception/payload inspection was unavailable. Complete that bounded external evidence when suitable tooling exists; do not infer provider-dashboard receipt or legal compliance | Git `be0182b`; focused/regression/build evidence; authenticated Render and production browser evidence reconciled 17 September 2026 |
| 18 September 2026, 13:07–13:10 BST | Render production | Import-quality deployment | RSS preview/body integrity | Deploy block-boundary preservation and pre-sanitisation incomplete-preview routing | Revision `bbc526c`; deployment `dep-damij1btqb8s73fvesp0`; service `srv-d5virmm3jp1c73c9d6tg`; instance `klzb8`; Standard 1 CPU/2 GB | Start 13:07:33, build 13:09:25, startup 13:10:10, live 13:10:17; duration 2m44s; health HTTP 200; no attributable fatal error, OOM, exit 137, restart loop, Bad Gateway or material 5xx | Implementation/deployment verified without repairing five historical affected Guardian records or adding full-article scraping | Observe natural scheduled imports; complete-replacement evidence remains separately gated | Git `bbc526c`; authenticated Render evidence reconciled 18 September 2026 |
| 18 September 2026, 18:00–18:01 BST | Render production and authenticated Admin | Natural import-quality acceptance | RSS preview/body integrity | Observe the first eligible natural run without manual import or data mutation | Revision `bbc526c`; instance `klzb8` | One execution completed 18:01:58 in 118.50 s. Guardian Money/Housing/Science/UK candidates 26/18/26/44; output Cheshire 3, UK 3, Business 2, Tech 4, Sports 0; 15 hybrid results; zero cleanup removals; final RSS about 302.0 MB. Guardian record `6aad6e3245d0658a103d921e` was hidden in Manual Review with the expected incomplete-preview reason; bounded inspection of it and public record `6aad6e7245d0658a103d9228` found no supported terminal marker or analogous joined boundary | **HTML-BOUNDARY FIX NATURALLY VERIFIED; INCOMPLETE-PREVIEW ROUTING NATURALLY VERIFIED.** Normal import behaviour continued and no attributable production defect was found | **IMPORT ARTICLE QUALITY FIX NATURAL ACCEPTANCE PARTIAL. COMPLETE-REPLACEMENT PATH NOT NATURALLY EXERCISED.** Five historical records remain unresolved; `/api/import-real-news` remains a separate unchanged follow-up risk. Nonfatal Warrington/Knutsford Guardian HTTP 403 warnings were unrelated | Authenticated scheduler, Admin, public-page and health evidence reconciled 18 September 2026 |

### 13 August 18:00 article-generation memory markers

| Phase | `rss_mb` | `current_rss_mb` |
|---|---:|---:|
| `job_started` | 129.8 | 130.7 |
| `lock_acquired` | 129.8 | 130.7 |
| `existing_record_index_completed` | 139.0 | 139.9 |
| `all_feed_fetch_completed` | 167.4 | 168.1 |
| `uk_finance_processing_completed` | 167.7 | 168.4 |
| `local_feed_fetch_completed` | 178.8 | 179.5 |
| `local_processing_completed` | 188.9 | 189.8 |
| `business_tech_processing_completed` | 188.9 | 189.8 |
| `visible_pool_cap_completed` | 236.0 | 222.5 |
| `duplicate_cleanup_first_read_completed` | 262.6 | 263.5 |
| `duplicate_cleanup_first_stage2_completed` | 262.6 | 263.5 |
| `duplicate_cleanup_second_read_completed` | 304.4 | 305.5 |
| `job_completed` | 304.4 | 305.5 |

Logged counts were active/archived indexes 4,224/3,649; all-feed candidates
1,782; UK candidates/imported 237/4; finance 61/0; local 180/2; business/technology
imports 3/1; both cleanup scans 4,253; and zero cleanup removals. Current RSS rose
174.8 MB overall. The 83.0 MB visible-pool-to-completion interval comprised
+41.0 MB first duplicate Stage 1, 0.0 MB first Stage 2 and +42.0 MB short-content
scan after the +32.7 MB visible-pool interval. This was a worse observation, not a
proven trend or approval for another optimisation.

## 23 September 2026 — CT-DEC-021 functional production acceptance

**FUNCTIONAL PRODUCTION ACCEPTANCE COMPLETE — UPSTREAM QUERY-LOG PRIVACY GATE OPEN.**
Source: owner-supplied controlled production observations and bounded diagnostic
results reconciled on 23 September; no production action was repeated for this
documentation change. Acceptance ran at
`2f40374a136b4a03b5e2fbf97a5ea19fd1aaf92f`, after the implementation chain was
pushed/deployed. Render reported Live, the runtime SHA matched, and health was
HTTP 200/healthy. Production Resend was enabled with key/from and newsletter
secret present; read-only Resend authentication returned HTTP 200. Local Mac
transport credentials were not used for production acceptance.

| Gate | Recorded evidence |
|---|---|
| Identity/index | Read-only dry-run: 14,266 scanned, all valid; zero assignments, malformed IDs, duplicate groups or invalid versions. Exact `newsletter_management_id_unique` existed, unique and non-sparse. No migration apply/index change. |
| Controlled delivery | One prepared recipient, zero skips, one provider contact, one accepted recipient; Resend successful chunks 1, failed 0. Message received in Apple Mail. |
| Native headers/DKIM | Apple Mail recognised mailing-list metadata. Raw headers contained both native headers and exact `List-Unsubscribe=One-Click`; recipient DKIM passed and its signature covered both header names. |
| Native mutation | Apple Mail native unsubscribe made the controlled record inactive; identity remained present and version structurally valid. |
| Inactive replay | Original delivered credential returned HTTP 200; active remained false, UUID/version/preferences/unsubscribe and other management metadata unchanged; complete compared state unchanged. Independent provider non-contact is not inferred from this replay evidence. |
| Human confirmation | Delivered footer opened explicit confirmation; no email re-entry or second email. One confirmation displayed the completed unsubscribe result. |
| Reactivation | Normal management request delivered a challenge-backed reactivation email. All three choices and explicit confirmation were submitted once. Read-only verification showed active/all three true, UUID unchanged, version exactly +1, reactivation timestamp, `verified_email` method and preferences timestamp present. |
| Stale credential | Original pre-reactivation direct credential POST returned HTTP 401; active stayed true and identity/version/preferences/compared state were unchanged. No email provider contact was reported. |
| Active preferences | Challenge-backed email/form/save succeeded: Daily Brief and Weekly Roundup true, Breaking News false, active true, UUID/version unchanged, preferences timestamp present. Reopening the consumed link showed invalid-link/new-link-request UI. |
| New-signup welcome | Separate owner-controlled address had zero existing matches; one normal production signup produced a received welcome. Immediate activation copy, three newsletters, coverage, latest-news CTA and management links were observed. Both native unsubscribe headers were absent, as required for transactional welcome. |

### Evidence boundaries and outstanding privacy

- No independent manual human/native token-string equality comparison was recorded.
  Shared-token binding is implemented and both paths worked; do not promote that
  to an unperformed raw-source comparison.
- No separate post-signup database verification of active/all-three/version 1 was
  performed. The exact delivered welcome subject was not manually verified;
  configured subject/code semantics are not additional observed acceptance.
- **POTENTIAL QUERY LOG EXPOSURE remains open.** App/Uvicorn filtering and a
  non-TRACE committed start do not establish upstream retention. No active
  Sentry/OTel/Datadog/New Relic/request-dump integration was found, but Render
  Request Logs were unavailable at the current plan/access level.
- During stale-token acceptance, client httpx INFO output printed the full
  credential-bearing request URL in Render Shell. The credential was already
  stale after rotation; this still demonstrates client-side query logging exposure.
  No credential, address or secure URL is retained in this record.
- Functional acceptance is complete, not unconditional CT-DEC-021/privacy closure.
  Original QA counts remain 3 unresolved / 2 repo-remediated / 6 production-verified;
  post-baseline counts remain 4 unresolved/partial / 3 production-verified;
  combined 18 remain 7 / 2 / 9. CT-QA-2026-006 and CT-QA-2026-007 stay closed.
  No new QA ID is created.

### Later welcome-copy-only commit

`40304fc24879e37f5ef004f501c82b9b85842d2e` changed only HTML/plain-text welcome
coverage to Cheshire, Macclesfield, Wilmslow, Knutsford, Alderley Edge, Prestbury,
Congleton, Nantwich & more (bullets in HTML, commas in plain text).
Reported focused verification: 11 passed, 2,848 deselected; `git diff --check` passed.
It was pushed after the acceptance run. The earlier welcome receipt does not prove
this later wording; this record does not independently establish its deployment.

## 27 September 2026 — Commercial Trust production acceptance and affiliate correction

### Deployment and preconditions

Local and freshly queried remote `full-scrape-prod` both matched
`3a9b81e7b9dc9e1cf57fd7347b02e9d8bea5122e`, `Improve commercial trust and outbound
measurement`. Tracked tree was clean; only the two protected local files were
untracked. Render deployment `dep-dasccr0ae00c73avpep0` showed **Deploy succeeded |
Live**, the exact source SHA and runtime `74qjv`; startup completed at 08:34:21
BST and Live was logged at 08:34:22. Fresh public `/api/health` returned HTTP
200/healthy. Phase 1 deployment acceptance was complete before the data write:
linked/unlinked and zero-link comparisons, no automatic top-pick panel, neutral
Amazon fallback without price/rating claims, one UK associate tag and intended
commercial rel handling passed bounded desktop/mobile inspection.

Fresh production reads found exactly one record for each of the AI productivity,
mattress and education slugs. Published state, monetisation, advertiser IDs,
target labels, exact old mattress copy and all six AI alternatives passed. API
identity/sections/monetisation matched Mongo. No configured enrichment mapping
could restore either cleared link. An aborted snapshot read transaction confirmed
transaction capability without changing data.

### Private backup and atomic correction

At approximately 08:30 UTC, a unique timestamp/random-suffix private directory
under `~/cheshiretoday-private-backups/commercial-trust/` was created outside Git.
It contains only `authority-pages-before.bson` for the two target records.
Directory mode 0700, file mode 0600, exclusive creation, flush/fsync, BSON decode,
exact encoded equality, record count and slug checks all passed. No backup content
or tracking URL is retained in repository documentation.

The authorised snapshot transaction reread complete originals, resolved provider
indices by trimmed name with title fallback, and conditionally matched original
identity, slug, timestamp, sections, status, monetisation and complete record state.
No upsert or whole-document replacement was used.

| Record | Approved business changes | Matched / modified |
|---|---|---|
| `best-ai-productivity-tools-uk` | EMPLA AI Employees `affiliate_link` → empty string; 127533 closed 25 September | 1 / 1 |
| `best-mattress-deals-uk` | Emma Sleep `affiliate_link` → empty string; `monetisation` affiliate → none; provider `content` → approved neutral text; 79506 identifies Emma App, not Emma Sleep | 1 / 1 |

The exact replacement copy is: “An option covered in this guide for readers
comparing online mattresses, delivery and trial-period terms.” Both records also
received the correction's UTC ISO `updatedAt`. Exactly four business fields changed.
Before commit, both complete expected post-images and the unchanged education
control passed. **Commit acknowledged; no ambiguous result or write retry.**
Immediate majority readback again matched both complete post-images and the
complete unchanged education document. AI monetisation stayed `none`; all seven
providers and the six alternative sections were preserved byte/value-equivalently.

### Post-write acceptance and boundaries

- Public API and Googlebot/static HTML passed for all three slugs. EMPLA and Emma
  remained present with no restored outbound link; AI alternatives remained and
  mattress copy matched exactly. Education API and crawler response were identical
  to the pre-write baseline.
- Six browser samples (three guides at 1440px and 390px) passed. AI showed all
  seven providers without outbound CTAs/disclosure; Emma showed neutral exact copy,
  no outbound CTA/disclosure and intact layout; education retained CloudLearn and
  Alison Free Online Courses with both CTAs. No automatic top pick, horizontal
  document overflow or runtime error was observed.
- Isolated Playwright interception was installed before navigation; service workers,
  commercial/sponsor/article measurement, analytics and off-site navigation were
  blocked. Two passes blocked **22 commercial requests** (11 each); **zero allowed
  through**, zero forbidden responses and zero synthetic clicks. The initial
  browser selector incorrectly expected h3 labels; correcting it to the deployed
  div markup produced the six passing checks. Expected blocked-resource console
  messages were not application errors. Consent remained untouched.
- Before backup/write, a temporary precondition incorrectly treated shorthand
  “Alison” as an exact label; a read-only label check confirmed the expected full
  name, and the corrected preflight passed. No production mismatch or mutation
  occurred on that initial stopped preflight.
- Alison UK monetisation remains unresolved and the education record remains
  unchanged. Existing ratings/unrelated editorial copy were preserved. No
  replacement programme or Amazon replacement was invented; no Awin/CJ account,
  sponsor inventory, subscriber, application code, configuration or deployment
  change accompanied this correction. **Rollback requires separate approval.**

Only the four governance documents were reconciled afterward for a documentation-
only commit; no push is authorised. Unrelated newsletter query-log, deliverability,
security and QA gates remain unchanged.

## 27 September 2026 — Virtual-office editorial baseline correction

### Preconditions and backup

Branch `full-scrape-prod`, local HEAD and live remote ref all matched
`8c8788f86bc88a4ee5f9ea8039014ad46d5d37f0`. Tracked tree and whitespace checks
passed; only the two protected untracked files remained. Render's current Live
deployment was `dep-dasdclgae00c73b0g7ag` at that exact documentation revision,
above unchanged application baseline `3a9b81e`. Public health returned HTTP
200/healthy. This task did not push or trigger deployment.

The exact slug `best-virtual-office-services-small-business-uk` resolved to one
published Business/affiliate document with 11 sections and two uniquely identified
tool entries. All approved old target values, timestamp, provider order and
advertisers 36030/83191 passed; public API matched the complete serialised record.
No backend enrichment mapping applies. A first combined preflight/write-mode
script was not executed by the safety gate; a separate structurally read-only
script then passed before the authorised write-mode execution.

At 16:08 UTC a new private timestamp/random-suffix directory under
`~/cheshiretoday-private-backups/commercial-trust/` received exactly one original
document in `authority-pages-before.bson`. Exclusive creation, directory 0700,
file 0600, flush/fsync, decode, slug/cardinality and exact BSON equality passed.
No contents or full tracking URLs are recorded here. Rollback requires separate
approval.

### Transaction and exact changed paths

Snapshot reread matched the backup exactly. Section identities/order and the
approved snapshot were revalidated before deriving the update. Conditional
`update_one`, `upsert=False`, guarded identity, timestamp, sections and full
original document; it matched and modified exactly one record. Complete expected
post-image equality passed before commit. **Commit acknowledged**, no retry;
majority readback matched exactly and confirmed this complete difference set:

```text
title
sections.0.content
sections.1.content
sections.2.content
sections.2.rating
sections.3.title
sections.3.content
sections.4.content
sections.5.content
sections.6.content
sections.7.title
sections.7.content
sections.8.content
updatedAt
```

These are 13 editorial fields plus execution-time UTC ISO `updatedAt`. The new
title is “Virtual office options for UK small businesses: address services and
mail handling”. Both provider ratings are null. Both affiliate URLs are exactly
preserved, including advertiser IDs 36030 and 83191; stored provider names/order,
section types, slug, category, published status, `monetisation=affiliate`, all
unlisted sections and other metadata are unchanged. No provider was added/removed.

### Public acceptance and evidence boundary

- Public API matched the complete expected serialised post-image. Googlebot HTML
  showed the new title and all copy, both provider names and unchanged links, and
  no 4.4 rating; no enrichment restored old wording.
- Desktop 1440px and mobile 390px passed exact guide title/copy, provider order,
  two provider-list CTAs, unchanged destinations and the existing exact
  `sponsored noreferrer noopener` rel. Frontend affiliate disclosure remained;
  neither provider showed a numeric rating, and edited provider/location wording
  contained no old “Best for” / “best virtual office” claims. No automatic top
  pick, horizontal overflow or runtime error was observed.
- Crawler HTML's existing renderer has no affiliate-disclosure block. Disclosure
  preservation is verified on the React frontend; crawler disclosure is not
  claimed or changed by this data-only operation.
- Isolated interception preceded navigation, blocked service workers, commercial,
  sponsor/article measurement, analytics and off-site navigation, and allowed only
  GET/HEAD. Two passes each blocked six desktop and five mobile commercial
  requests: **22 blocked, zero allowed through**, zero forbidden responses,
  zero synthetic clicks. Expected blocked-resource console errors were harmless.
  The first pass incorrectly selected the site-brand h1 and expected `nofollow`;
  temporary assertions were aligned with existing markup and the second passed.
  No application code or production data was changed to satisfy the checks.

The correction is the clean baseline for the first virtual-office affiliate
engagement experiment. It does not establish conversion/revenue improvement or
launch a variant. Route, related-guide inputs, placements, disclosure/CTA logic,
measurement identifiers, Awin, configuration and all application code remain
unchanged. Four governance documents record the result in a documentation-only
commit; no push is authorised. Unrelated privacy, deliverability and QA gates
remain open as previously recorded.

## Unreconciled later production evidence

- The 7–21 August duplicate-cleanup, scheduler-lock, event-anchor and isolated
  batching deployments and natural-run evidence through 21 August 06:00 are
  reconciled above. Later Render logs, Admin observations and production
  investigations may exist in Codex tasks but are not yet systematically preserved.
- The requested ChatGPT export is unavailable.
- The Editorial Similarity numerical three-run observation-count gate is satisfied;
  calibration, thresholds, UI and enforcement remain unapproved.
- Production credential rotation following `QA-SEC-001` is preserved above as
  dated operational evidence; Git history alone does not prove that external
  action and still retains the revoked historical credential.
- Historical PDFs remain unreconciled and cannot establish live state.
- No event in this section should be upgraded to “verified” without a timestamped,
  repository-backed evidence record.

## 28 September 2026 — desktop lead-story hierarchy deployment

Commit `8ed336fe426a140d2cabb006b2c405611e22d594`
(`Improve desktop lead-story hierarchy`) was pushed to `full-scrape-prod` and
confirmed Live on Render. Public `/health` returned HTTP 200 with
`{"status":"healthy","service":"cheshire-news"}`.

The bounded frontend change visually orders the existing category/headline/meta
block before the hero image at `lg` widths (1024px and above) while preserving
image-first presentation below 1024px. It retains one article link, one `h1`,
existing image crop/aspect ratios, hero selection/allocation, sidebar,
monetisation and backend/data behaviour. The matching loading skeleton uses the
same desktop ordering.

Pre-deployment verification passed 53 focused/related tests, 465 full frontend
tests and the production build. Isolated local browser checks confirmed text-first
desktop ordering and image-first mobile/tablet behaviour. A final 1440×900 check
measured the lead headline at 310–405px and the hero image starting at 461px.
The local fixture intentionally substituted `/fixture.svg` for real article
images, so placeholder imagery was not a production-image defect.


## 28 September 2026 — Latest card consistency deployment

After the hero deployment, visual production review identified that the Latest
cards following the Popular Guides insertion used the default CompactArticleCard
presentation while the cards before the insertion used `variant="editorial"`.
The cause was a single missing prop on `latestSplit.remainingCards`.

Commit `f07c792ed7646b63f01e61bd054dc56db855d477`
(`Unify Latest card styling after guides`) adds only the existing
`variant="editorial"` presentation to that post-guide render path. Article
allocation, newest-first order, counts, headline strip, guide placement/rotation,
navigation, monetisation and backend/data are unchanged.

Verification passed 3 focused homepage tests, 54 related tests across five suites,
466 full frontend tests across 45 suites, the production build and whitespace
checks. Isolated browser acceptance passed at 1440×900 and 390×844: Latest
expanded 12→36 desktop and 4→36 mobile in fixture order, Popular Guides remained
in the same insertion position, both card groups used the editorial style, Show
more worked, and no overflow or console errors were observed. No production
analytics or affiliate clicks were generated during those local checks.

`f07c792` was pushed to `full-scrape-prod`, confirmed Live on Render, and public
health returned HTTP 200 with
`{"status":"healthy","service":"cheshire-news"}`.

## 28 September 2026 — footer topic naming deployment

Commit `f5af386a9557ab079231628aa9d7af4aad25c857`
(`Clarify footer topic navigation`) was pushed to `full-scrape-prod` and
confirmed Live on Render. Public `/health` returned HTTP 200 with
`{"status":"healthy","service":"cheshire-news"}`.

The change is copy-only: the NewsFooter category group label changed from
“Guides” to “Topics”. AI & Tech still links to `/category/ai-tech` and Finance
to `/category/finance`. Routes, navigation structure, homepage guide strips,
monetisation, SEO, backend and data are unchanged.

Verification passed one focused footer test, 22 related tests across five suites,
467 full frontend tests across 46 suites, the production build and whitespace
checks. Isolated local browser checks at 1440×900 and 390×844 confirmed the
Topics heading, unchanged destinations, intact layout, no horizontal overflow
and no console errors. No production navigation, analytics or affiliate clicks
were generated during those local checks.

## 29–30 September 2026 — mobile homepage refinement and guide measurement deployment

Commits `609d9d5` (`Simplify mobile homepage news flow`) and `6afb0b3` (`Move mobile newsletter below Latest controls`) were pushed to `full-scrape-prod` and production-accepted. The mobile homepage now prioritises news, does not show Finance or Popular Guides, and places the compact newsletter below the Latest Show more/Show less control. Exact local/remote SHA equality was verified after deployment and public `/health` returned HTTP 200/healthy. Owner mobile acceptance passed.

A UK News homepage-visibility investigation during the same period confirmed several raw-feed articles were omitted by the existing homepage UK editorial/noise filter path rather than by archive or Manual Review state. A temporary candidate-depth experiment was reverted after historical comparison showed the Friday baseline already used 100/100 Local/UK caps. The 100/100 caps were restored and no UK filter-policy change was approved.

Commit `d4165800662131cded5cedf064a03cbdef21f531` (`Add homepage guide measurement`) was then pushed after explicit approval. It adds first-party desktop homepage guide-card measurement with stable guide IDs, distinct Finance/Popular Guide placement IDs, and `rendered`, `viewable` and `clicked` events. Viewability requires 50% continuous visibility for 1,000 ms while the document is visible. Measurement is best-effort, deduplicated and privacy-bounded, and failures do not block native navigation or the legacy guide-click analytics path.

The homepage now does not mount guide strips on mobile, preventing hidden mobile rendered impressions, while desktop retains both guide placements. Verification passed three focused suites with 23/23 tests and a successful production frontend build. After deployment, local and remote SHAs matched exactly, public `/health` returned HTTP 200/healthy, and owner production acceptance confirmed desktop guide strips visible and mobile guide strips absent.

This deployment establishes a measurement baseline only; it does not establish CTR, conversion improvement, revenue or guide popularity.

## 6 October 2026 — sidebar package and regional eligibility acceptance

The sidebar package comprised `8a1b593` (neutral `Related stories` article
heading), `fdad609` (remove unrelated Finance fallback) and `6683413` (replace
the homepage Amazon sidebar with one measured useful guide), with acceptance
recorded by `7004994`. The live bundle contained `Related stories` and
`homepage_sidebar_guide`, omitted the old `More in ` wording and retained the
expected guide destination. Health and homepage returned HTTP 200.

The subsequent article investigation found five unarchived/non-Manual-Review
records. Chester University was correctly local/public; The Papers was filtered;
RAF Fairford remained excluded by existing utility policy; Scotland £5.8bn was
initially public; and the AI-teacher story exposed singular `school` failing to
match plural `schools`. `871874d` made only the plural-aware `schools?` change.
Historical comparison showed no prior general Scotland/Glasgow block, so the
regional distinction was approved as new bounded policy rather than a revert.

`a527e74` centralised binary public eligibility and applied it to public pools and
Admin Articles before pagination/counting. Stored records, Archive, Manual
Review, force-live, ranking/interleave and sensitive caps were preserved. After
40 focused and 158 broader passing tests, production excluded the two Scotland
fixtures and retained Chester, but Glasgow remained: “one of the UK’s biggest
ever” matched the bare `UK` rescue.

`b413282` restricted rescue to explicit nationwide phrases and existing national
institutions. The exact Glasgow fixture and incidental UK/British cases joined
the preserved national/local/noise counterexamples; 43 combined helper/Admin
tests, compilation and whitespace checks passed. Read-only production acceptance
returned HTTP 200/healthy and 97 public articles. All four required exclusions
were absent, Chester University was present, no exact or >=0.85 title duplicates
were found, and no obvious sports/video/podcast/gallery or paper-roundup leakage
was observed. Acceptance is **APPROVED WITH OBSERVATIONS**: Drumcree/Portadown
remains unclassified because its metadata contains no approved regional marker,
and RAF Fairford/defence-security remains a separate policy question. No
production write, import, job, newsletter or analytics event was triggered.

## 7 October 2026 — retail-offence gate and sticky Further reading

`36aeafe` deployed the bounded local-RSS `retail offence(s)` pre-rewrite gate and corrected the existing stab expression so it does not match “established”. The broader post-rewrite crime classifier explored during diagnosis was reverted and was never deployed. Local verification passed 149 affected tests with six existing warnings, compilation and whitespace checks.

The natural 06:00 BST production observation found 19 active records created in the checked window, zero active retail-offence matches and no reappearance of the previously archived Chester Standard record. The second healthy natural observation at 12:00 BST / 11:00 UTC found 26 active records and again zero exact active retail-offence matches. A new Cheshire Live crime story, “Man labelled 'persistent problem in Chester' hit with four-year city centre ban”, was routed to hidden review with `verification_status=needs_manual_review` and `rewrite_status=manual_review_required`; ordinary local planning/school stories were allowed through, including auto-screened examples.

The archived record could also be suppressed by duplicate/archive state, so its absence is not represented as direct runtime proof of the new phrase matcher; the fresh-candidate regression remains the direct classifier evidence. A BBC sexual-assault article appeared in the active collection as `ai_rewrite_auto_screened`, but active-collection presence does not prove public visibility because shared public eligibility is separate. It is therefore not classified as a confirmed production defect. Acceptance remains **APPROVED** with those evidence boundaries.

`0e4c408` then deployed the desktop-only sticky Further reading completion. Only the existing conditionally rendered Further reading block is sticky (`lg:sticky lg:top-24`); Related stories and sponsor/newsletter remain normal-flow, and mobile/tablet behaviour is unchanged. Focused verification passed 36 tests, related ArticlePage/component checks and the production build passed, and the owner visually accepted the live long-article behaviour. Local/origin matched `0e4c408`; health and homepage returned HTTP 200. No production data, scheduler, newsletter or backend change accompanied this frontend deployment.

## 7 October 2026 — automatic article-depth screening acceptance

Commit `efc79b1d7a46320c54b29fef46c0f991ab92faa6`
(`Tighten automatic article depth screening`) was production-observed during the
natural 18:00 BST / 17:00 UTC import. The checked window contained 18 created
records. No `ai_rewrite_auto_screened` record was below 200 words, and no checked
source-audit/meta-language construction was found.

Four sub-200-word rewrites were retained in hidden Manual Review: the 161-word
Admiral Taverns Chester story, 192-word Admiral Taverns national expansion
story, 191-word Specsavers Runcorn charity story and 127-word Paul Ferris story.
All had `needs_manual_review`, `manual_review_required` and
`manual_review_hidden_from_public=True`. Four clean rewrites at 209, 223, 260
and 271 words remained `ai_rewrite_auto_screened` / `ai_rewritten`. The
281-word manually corrected Wilmslow banking article retained
`manual_corrected_verified_limited` / `manual_corrected`.

**Acceptance: APPROVED.** The observation verifies the intended boundary in this
natural run: short rewrites were retained rather than discarded, clean 200+ word
rewrites could still auto-screen, and manual-corrected content was unaffected.
The zero source-audit match is bounded run evidence, not proof that prompt
leakage can never recur or that every future candidate is covered beyond the
implemented rules and tests.

## 9 October 2026 — homepage sidebar freshness deployment and acceptance

Commit `10d5a8a4452868a69b91484cc64b2f62d2f0f895` (`Keep homepage
sidebar articles fresh`) was pushed from `ccc6e26` to `full-scrape-prod` and
deployed. Local HEAD and `origin/full-scrape-prod` matched the full SHA. Public
`/api/health` returned HTTP 200 with
`{"status":"healthy","service":"cheshire-news"}`, and the production homepage
returned HTTP 200.

The correction is confined to the visible Business, AI & Tech and Finance
homepage sidebar modules. They now accept only valid `publishedDate` values no
older than seven days, retain existing deterministic fresh-first ordering and
may render fewer cards rather than filling from older inventory. Recent
`created_at`, ObjectId or import timestamps cannot rescue an old publication
date. The unrendered legacy Finance allocation no longer reserves candidates,
and bare `rate`, `rates` and `save` no longer classify unrelated stories as
Finance. Genuine mortgage, interest/fixed-rate, ISA, savings, tax and existing
bounded property/planning matching remain. Hero, Top Stories, backend/API,
public eligibility and request behaviour are unchanged.

QA recorded focused RED **13 failed / 17 passed**, followed by GREEN **30/30**;
related component suites passed **45/45**; the frontend suite excluding the
documented `QA-MAINT-002` harness defect passed **553/553**; and the production
frontend build and `git diff --check` passed. `QA-MAINT-002` remains an unrelated
pre-existing `PublicMetadataUniqueness` mock omission and was not fixed here.

The owner performed a live homepage visual/content check after deployment and
explicitly accepted the corrected Business, AI & Tech and Finance behaviour.
Top Stories remained satisfactory and intentionally unchanged. **Production
acceptance: APPROVED.** This evidence covers the observed deployed homepage; it
does not establish that future inventory can never expose another bounded
classification or selection edge case.
