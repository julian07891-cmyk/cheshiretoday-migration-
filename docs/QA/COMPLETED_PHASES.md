# Cheshire Today — Completed QA and Hardening Phases

> **Reconstruction status:** Programme-level record through current HEAD. “Completed” describes implementation scope; deployment and production verification are explicit fields and may remain pending.

## Document purpose

Record completed QA programmes without mixing their residual risks into the live finding register.

## Authority and evidence

Evidence comes from current code/tests, Git history, [Project State](../PROJECT_STATE.md), [Engineering History](../HISTORY/ENGINEERING_HISTORY_MASTER.md), [Production Timeline](../PRODUCTION_TIMELINE.md), and the immutable [29 July report](QA_REPORT_2026-07-29.md).

## How to use this document

Use this to avoid repeating completed work. Follow residual-risk links before extending a subsystem.

## Foundational platform QA

- **Date range:** February–July 2026
- **Objective:** Stabilise Render/FastAPI/React production and establish repeatable QA.
- **Scope:** Health, routes, build, crawler/public/API checks, authentication boundaries and post-release audit.
- **Changes:** Iterative platform fixes; 29 July credential/test/compilation containment followed.
- **Tests:** Dated QA records include focused backend, complete frontend, compilation and production build baselines.
- **Deployment status:** Multiple historical deployments; no blanket statement that every later local fix deployed.
- **Production verification:** Public health/routes and sampled crawler/API behaviour were verified on 29 July.
- **Residual risks:** CORS, credential rotation evidence, public latency and maintenance warnings remain in [Open Findings](OPEN_FINDINGS.md).
- **Sources:** [29 July report](QA_REPORT_2026-07-29.md); [Engineering History](../HISTORY/ENGINEERING_HISTORY_MASTER.md).

## Scheduler and import safety

- **Date range:** March–August 2026
- **Objective:** Bound scheduled mutation and prevent duplicate owners/imports.
- **Scope:** Scheduler enablement, hostname guard, Mongo locks, stale takeover, import caps, RSS concurrency and authenticated manual operations.
- **Changes:** Explicit startup guards, distributed locks, disabled deployment-triggered generation and authentication-first Admin generation routes.
- **Tests:** `tests/test_scheduler_lock.py`, `tests/test_admin_generation_operations_auth.py`, importer regressions.
- **Deployment status:** Core scheduler controls are historical/current code; later observation instrumentation deployment is separately recorded.
- **Production verification:** Normal scheduled runs have historical evidence; comprehensive post-HEAD observation is unreconciled.
- **Residual risks:** Lock-acquisition exception continuation and memory peaks.
- **Sources:** [Scheduler](../OPERATIONS/SCHEDULER.md); Git history.

## Duplicate and archive safety

- **Date range:** March–August 2026
- **Objective:** Prevent exact duplicates without deleting legitimate content.
- **Scope:** Normalised title/source URL/image checks, active/archived snapshots, batch sets, unique indexes, archive-first policy and cleanup.
- **Changes:** Version 1 deterministic barriers remained authoritative; unsafe startup hard-delete and automatic age deletion are disabled.
- **Tests:** Importer, duplicate, archive, visibility and Manual Review regressions.
- **Deployment status:** Current code reflects controls.
- **Production verification:** Read-only duplicate investigations provide case evidence; no claim of zero future duplicates.
- **Residual risks:** Cleanup memory and same-story cross-feed cases motivate advisory similarity observation.
- **Sources:** [Article Pipeline](../ARCHITECTURE/ARTICLE_PIPELINE.md); [Editorial Evolution](../EDITORIAL_EVOLUTION.md).

## Manual Review hardening

- **Date range:** June–August 2026
- **Objective:** Make hidden editorial review a safe first-class state.
- **Scope:** Visibility, editorial reasons, editing/restoration safeguards, publication-intent confirmation and mobile presentation.
- **Changes:** Backend-authoritative gates, hidden public queries, honest `Review and Update` flow, shared editor and responsive cards.
- **Tests:** Manual Review metadata/routing/editor-intent/mobile suites and related archive tests.
- **Deployment status:** Core state and mobile/editor changes have mixed deployment records; publication-intent/card commits exist through `f43c4ef` lineage.
- **Production verification:** Mobile layout/editor verified in bounded read-only sessions; no real article was submitted merely for QA.
- **Residual risks:** Normal Articles/Archive responsiveness and broader navigation remain separate.
- **Sources:** [Project State](../PROJECT_STATE.md); Git `50ede47`, `761a7c2`, `f43c4ef`.

## Newsletter security phases

- **Date range:** April–July 2026
- **Objective:** Secure subscription lifecycle and management links while preserving reliable delivery.
- **Scope:** Generic public responses, token purpose, challenge storage, expiry/replay, rate limits, secure preferences, unsubscribe/reactivation, active exclusion and tracking redirects.
- **Changes:** Purpose-specific collaborators and transaction boundaries; safe click redirect; accepted-recipient ledger.
- **Tests:** `tests/test_newsletter_*.py`, including challenge, request-link, reactivation, unsubscribe, click, index and runtime suites.
- **Deployment status:** Historical records include staged deployments; live provider configuration is external.
- **Production verification:** Selected secure flows and newsletter sends were historically observed; no blanket inbox-delivery claim.
- **Residual risks:** Weekly Roundup reliability and inactive-subscriber evidence.
- **Sources:** [Newsletter architecture](../ARCHITECTURE/NEWSLETTER.md); [Newsletter Operations](../OPERATIONS/NEWSLETTER_OPERATIONS.md).

## Article live-pool hardening

- **Date range:** May–July 2026
- **Objective:** Keep only eligible strategic articles public and bound the visible pool.
- **Scope:** Manual Review/public filters, caps, source/content gates, cleanup and public APIs.
- **Changes:** `cap_visible_articles`, hidden-state exclusions, archive protections and quality gates.
- **Tests:** Visibility, importer, Manual Review, sitemap/RSS and article API regressions.
- **Deployment status:** Current code contains controls.
- **Production verification:** 29 July public sample found no archived/Manual Review leakage; later investigations require separate evidence.
- **Residual risks:** Cleanup can remove post-insert records under existing rules; memory pressure remains.
- **Sources:** [Article Pipeline](../ARCHITECTURE/ARTICLE_PIPELINE.md); [29 July report](QA_REPORT_2026-07-29.md).

## Local RSS staged verification

- **Date range:** July 2026
- **Objective:** Activate local feeds without weakening editorial quality.
- **Scope:** Locality, freshness, source classification, topic caps, Manual Review routing and public limits.
- **Changes:** Staged feed handling and `local_rss_manual_review` context.
- **Tests:** `tests/test_local_rss_manual_review_routing.py`, `tests/test_sync_rss_editorial_guard.py` and related import tests.
- **Deployment status:** Repository history records staged activation.
- **Production verification:** Normal run evidence exists historically; exhaustive feed-quality proof is not claimed.
- **Residual risks:** Weak source content and cross-feed same-story coverage.
- **Sources:** [Engineering History](../HISTORY/ENGINEERING_HISTORY_MASTER.md); [Editorial Evolution](../EDITORIAL_EVOLUTION.md).

## Social-publishing QA

- **Date range:** July–August 2026
- **Objective:** Provide deterministic, Admin-controlled preparation without auto-publishing.
- **Scope:** Facebook graphics/link copy, Instagram formats, Threads copy, SSRF/XML safety, archive/Manual Review exclusion and legacy UI containment.
- **Changes:** Unified Social Publishing dialog; deterministic Facebook UTM; obsolete direct posting controls removed from Admin.
- **Tests:** 29 July records 146 focused backend and 96 focused frontend social passes; later component regressions retained.
- **Deployment status:** Unified workflow later appeared in deployed Admin; attribution commit `9b024cc` is in current history.
- **Production verification:** Authenticated Facebook attribution path functionally verified without publishing; real iPhone composer remains a limited external check.
- **Residual risks:** Threads documentation reconciliation and external platform behaviour.
- **Sources:** [Project State](../PROJECT_STATE.md); [29 July report](QA_REPORT_2026-07-29.md).

## Analytics and Most Read QA

- **Date range:** 30 July–August 2026
- **Objective:** Correct first-party view recording, public ranking and privacy-safe Admin reporting.
- **Scope:** Valid public view events, one-hour deduplication, period ranking, Facebook attribution and read-only summaries.
- **Changes:** Git `6a95ba9`, `a93d4bf`, `cac9b24`, `9b024cc`.
- **Tests:** 55 article-view/visibility, seven focused frontend tracking, 61 Most Read related checks, complete frontend 268 at the documented handover, plus Admin analytics tests.
- **Deployment status:** Implementation commits in history; Project State records functional Facebook Analytics production verification.
- **Production verification:** One controlled attributed event and deduplication were verified without Admin mutation or Facebook publication.
- **Residual risks:** GA4 validation, scanner/bot noise and measured query latency.
- **Sources:** [Analytics architecture](../ARCHITECTURE/ANALYTICS.md); [Project State](../PROJECT_STATE.md).

## Metadata reconciliation

- **Date range:** 1 August 2026
- **Objective:** Guarantee one active rendered metadata set and remove homepage leakage.
- **Scope:** Seven managed canonical/description/Open Graph/Twitter fields, production owners and SPA transitions.
- **Changes:** `6bfe896`, `1e5c2da`; documentation `7ca1269`.
- **Tests:** Real static shell plus Home, Article, hubs, newsletter, Contact, secure management, Admin, guide and unsupported routes.
- **Deployment status:** Deployed.
- **Production verification:** Settled DOM, SPA, crawler HTML, structured data, sitemaps and robots passed; no indexing recovery claimed.
- **Residual risks:** Search Console sampling.
- **Sources:** [SEO architecture](../ARCHITECTURE/SEO_AND_CRAWLERS.md); [Open Findings](OPEN_FINDINGS.md#qa-seo-002).

## Admin mobile Safari QA

- **Date range:** 1–2 August 2026
- **Objective:** Resolve login/editor containment and keep close controls usable under Safari focus enlargement.
- **Scope:** Admin-only 16 px controls, dynamic viewport login, top-aligned editor, sticky close header, responsive cards.
- **Changes:** `2d7ed9f`, `6328cf3`, `a6bfb78`, plus later card/layout commits.
- **Tests:** `AdminDashboardMobileSafari.test.jsx` and responsive/editor suites.
- **Deployment status:** Core mobile fixes deployed through `a6bfb78`; later layout commits have their own records.
- **Production verification:** Real iPhone verified login/editor/close at Safari Page Zoom 100%; zoom remained enabled.
- **Residual risks:** Navigation, action-row consistency and broader touch targets.
- **Sources:** [Project State](../PROJECT_STATE.md); Git history.

## Admin indexing protection

- **Date:** 26 August 2026
- **Objective:** Close `QA-SEO-002` with first-byte Admin indexing protection while preserving public SEO and the existing access-control boundary.
- **Scope:** GET/HEAD `/admin` and `/admin/`, unsupported nested Admin paths, wildcard/Googlebot/Googlebot-News robots groups, public metadata and sitemap regressions.
- **Changes:** `24f381e` — `Protect Admin from indexing`.
- **Tests:** 11 focused tests, 74 related regression tests and 9 sitemap regression tests passed; `python3 -m compileall -q backend tests` and `git diff --check` passed.
- **Deployment status:** Deployment `dep-da7ala710e5c738ovtm0`; instance `824s7`; Standard 2 GB RAM / 1 CPU.
- **Production verification:** GET/HEAD `/admin` and `/admin/` returned 200 without redirect and with `X-Robots-Tag: noindex, nofollow, noarchive`; `/admin/settings` remained 404 with first-byte noindex. All three crawler groups explicitly disallow `/admin` and `/api/admin/`. Homepage, category, article, canonical, Open Graph, Twitter, JSON-LD and sitemap behaviour remained intact; unauthenticated Admin verify remained 401 and health returned 200.
- **Status:** **CLOSED — PRODUCTION VERIFIED.** Robots and response directives control indexing only; Admin authentication and API authorization remain the security boundary.
- **Sources:** [Open Findings](OPEN_FINDINGS.md#qa-seo-002); [Project State](../PROJECT_STATE.md); Git `24f381e`; production verification 26 August 2026.

## Editorial Similarity Phase 2A

- **Date range:** 3–4 August 2026
- **Objective:** Build pure deterministic same-event scoring without runtime coupling.
- **Scope:** Bounded inputs, immutable identity-free result, signals, safety gates and fixtures.
- **Changes:** `8043fdd`.
- **Tests:** Focused scorer suite, Hough fixture and conservative negatives.
- **Deployment status:** Code deployed as part of later baseline, but no caller in Phase 2A itself.
- **Production verification:** Not applicable to pure disconnected scoring.
- **Residual risks:** Calibration requires integration evidence.
- **Sources:** [Editorial Similarity](../ARCHITECTURE/EDITORIAL_SIMILARITY.md).

## Editorial Similarity Phase 2B implementation

- **Date range:** 4 August 2026
- **Objective:** Collect bounded scheduled shadow evidence without publication effect.
- **Scope:** Explicit scheduled activation, 50+50 pool, corpus 100, shortlist/scorer cap 20, provenance, deterministic selection and safe logs.
- **Changes:** `5e1a875`; deployment record `1601ae4`.
- **Tests:** 54 focused Phase 2A/2B; related Version 1 group 178 passed, 12 skipped; compile/Black/diff checks.
- **Deployment status:** Repository records `5e1a875` live on 4 August.
- **Production verification:** Deployment only; detection quality not established.
- **Residual risks:** Multi-run observation and false-positive/negative calibration.
- **Sources:** [Editorial Similarity](../ARCHITECTURE/EDITORIAL_SIMILARITY.md); [Project State](../PROJECT_STATE.md).

## Editorial Similarity production-observation gate

- **Date range:** Began 4 August 2026
- **Objective:** Observe at least three normal runs before threshold or UI work.
- **Scope:** Health, duration, thirteen memory phases (including isolated first-pass Stage 2), pool/shortlist/comparison counts, bands/reasons/provenance and unchanged outcomes.
- **Changes:** None; observation-only.
- **Tests:** Automated contract tests support log bounds but cannot replace production observation.
- **Deployment status:** Shadow integration deployed.
- **Production verification:** Numerical three-normal-run observation-count gate satisfied; Version 1 outcomes remained unchanged.
- **Residual risks:** Calibration, production recall/precision, thresholds, UI and enforcement remain unapproved and incomplete.
- **Sources:** [Open Findings](OPEN_FINDINGS.md#ct-qa-2026-002); [Monitoring](../OPERATIONS/MONITORING.md).

## Related documents

[QA Master](QA_MASTER.md), [Open Findings](OPEN_FINDINGS.md), [Test History](TEST_HISTORY.md), [Roadmap Master](../ROADMAP_MASTER.md), and [Production Timeline](../PRODUCTION_TIMELINE.md).

## Known limitations

Some historical phase boundaries aggregate many small commits. Exact counts are included only where preserved. Post-HEAD production investigations and pending chat exports remain unreconciled.
