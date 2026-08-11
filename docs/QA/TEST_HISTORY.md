# Cheshire Today — Test and Verification History

> **Reconstruction status:** Evidence register through HEAD. Missing exact counts and warning totals are explicitly left unknown.

## Document purpose

Preserve major test/build/production verification baselines and the limitations of each.

## Authority and evidence

Sources are current tests/configuration, Git history, [29 July QA report](QA_REPORT_2026-07-29.md), [Project State](../PROJECT_STATE.md), [Completed Phases](COMPLETED_PHASES.md), and production records. See [Source Register](../HISTORY/SOURCE_REGISTER.md).

## How to use this document

Select the smallest relevant safe suite, then related regressions, compilation/build and bounded production verification. Never point legacy mutation-capable tests at production.

## Test strategy

The safe sequence is focused behavioural tests, related regressions, complete applicable suite, compilation/build, diff hygiene, then non-mutating production checks after deployment. Source-contract assertions supplement but do not replace behavioural coverage where practical.

## Backend tests

Pytest tests live under `tests/`. Current coverage spans APIs, authentication, imports, scheduler, newsletter, analytics, SEO and Editorial Similarity. External HTTP helpers must approve loopback targets before reading credentials or opening transport.

## Frontend tests

CRACO/Jest tests live beside components and services. They cover public routes, metadata, Admin workflows, responsive contracts, analytics, newsletter and social publishing. JSDOM cannot prove real Safari layout; physical-device checks remain final acceptance where required.

## Compilation checks

The 29 July repository-wide compilation failed on three tracked legacy modules. Git `7c2ac62` repaired them. `python3 -m compileall -q backend tests` passes at Phase 5 reconstruction.

## Production builds

The 29 July production React build passed. Later analytics, metadata and mobile milestones record successful `npm --prefix frontend run build` validations. Exact warning counts are not consistently preserved. `render_build.sh` remains the deployment build path.

## Security tests

`tests/test_committed_admin_credential_hygiene.py` scans tracked content; `tests/test_external_http_test_safety.py` verifies loopback-only targets, malformed/public target refusal, credential-read ordering and no redirects. Newsletter security suites cover token purpose, challenge, replay, enumeration resistance and rate limits.

## Newsletter tests

Coverage includes public landing/signup, consent parity, welcome email, secure preferences, request links, reactivation, unsubscribe, one-click contracts, challenge enforcement, unique-index provisioning, click redirects, HTML and runtime collaborators. Provider/live inbox delivery remains outside unit tests.

## Scheduler and import tests

`tests/test_scheduler_lock.py`, `tests/test_admin_generation_operations_auth.py`, `tests/test_article_generation_memory_observability.py`, `tests/test_sync_rss_editorial_guard.py` and Local RSS tests cover locks, authentication-first operations, memory phases, editorial guards and routing. Normal production runs remain the scheduler acceptance gate.

## SEO and crawler tests

Canonical route, sitemap lastmod, crawler/social metadata and frontend metadata uniqueness tests cover query-free identity, redirects, managed tags, NewsArticle and public hubs. Search Console and actual indexing are external.

## Analytics tests

Article-view tracking tests cover eligibility, identifiers, deduplication and non-blocking frontend behaviour. Most Read period tests cover eligibility before result limiting and no lifetime fallback. Admin analytics tests cover bounded/privacy-safe subsections and Facebook attribution.

## Editorial Similarity tests

Phase 2A tests cover pure immutable results, independent bounds, malformed fallback, signals, Hough and negative fixtures, determinism and I/O isolation. Phase 2B tests cover activation, pool/corpus/shortlist caps, selection/provenance, log privacy, fail-open insertion and Version 1 preservation.

## Production verification checks

Preserved checks include health, public routes, crawler HTML, sitemaps/robots, settled metadata/SPA navigation, Admin mobile Safari on a real iPhone, normal Articles/Manual Review mobile layouts, and a controlled Facebook-attributed view. Production checks were bounded and avoided publishing or administrative mutation except ordinary reader analytics explicitly acknowledged.

## Known non-hermetic or unsafe tests

At the 29 July baseline, four HTTP suites were unsafe by default. Commits `b804cdd` and `603e11b` contained that defect with strict loopback-only transport and safe skips. Any future external smoke suite must be distinctly named, read-only by default and impossible to target production accidentally. No such opt-in mutation mode is approved.

## Warning and maintenance backlog

Known warnings include deprecated FastAPI `on_event`, multipart pending deprecation, gzip unraisable-resource noise, stale Browserslist data and legacy backup artefacts. Warning counts vary by suite and are not normalised. See `QA-MAINT-001` in [Open Findings](OPEN_FINDINGS.md#qa-maint-001).

## Test baselines by date

| Date | Branch/HEAD | Command or suite | Result | Warnings | Scope | Limitations | Source |
|---|---|---|---|---|---|---|---|
| 29 Jul 2026 | `full-scrape-prod` / `2bcdf5c` | Focused backend social | 146 passed | 5 recorded | Social assets/routes | No authenticated live preview | [QA report](QA_REPORT_2026-07-29.md) |
| 29 Jul 2026 | same | Related Admin/newsletter/editorial/RSS | 1,193 passed | 363 recorded | Focused backend regressions | Not full suite | [QA report](QA_REPORT_2026-07-29.md) |
| 29 Jul 2026 | same | Focused frontend social | 96 passed | Not recorded | Social UI/services | JSDOM/browser limits | [QA report](QA_REPORT_2026-07-29.md) |
| 29 Jul 2026 | same | Complete frontend | 261 passed, 20 suites | Not recorded | Frontend | No physical-device proof | [QA report](QA_REPORT_2026-07-29.md) |
| 29 Jul 2026 | same | Broad backend excluding dangerous module | 1,635 passed, 21 failed, 12 errors | Not consolidated | Legacy broad suite | Non-hermetic baseline | [QA report](QA_REPORT_2026-07-29.md) |
| 29 Jul 2026 | remediation commits | Safety/hygiene focused | 31 passed | Not recorded | Credentials/targets | Local boundary only | [QA report](QA_REPORT_2026-07-29.md) |
| 30 Jul 2026 | `6a95ba9` lineage | Article-view backend/frontend | 55 backend-related; 7 frontend | Not recorded | View recording | Production event behaviour separately verified later | [Project State](../PROJECT_STATE.md) |
| 31 Jul 2026 | `a93d4bf` | Most Read related | 61 passed | Not recorded | Period correctness | Functional, not latency | [Project State](../PROJECT_STATE.md) |
| 31 Jul 2026 | `d6eb46b` handover | Complete frontend | 268 passed | Not recorded | Frontend baseline | Exact suite count absent | [Project State](../PROJECT_STATE.md) |
| 1 Aug 2026 | `6bfe896`/`1e5c2da` | Metadata uniqueness and regressions | Passed; exact total not preserved here | Not recorded | Seven fields/routes/SPA | Production checked separately | [Project State](../PROJECT_STATE.md) |
| 1–2 Aug 2026 | mobile commits | Admin mobile/editor responsive suites | Passed; exact total varies/not consolidated | Not recorded | Mobile structural/behavioural contracts | Real iPhone needed | [Project State](../PROJECT_STATE.md) |
| 4 Aug 2026 | `8043fdd`/`5e1a875` | Phase 2A/2B focused | 54 passed | Not recorded | Similarity contracts | No calibration proof | [Project State](../PROJECT_STATE.md) |
| 4 Aug 2026 | same | Related Version 1 group | 178 passed, 12 skipped | Not recorded | Import/duplicate/scheduler/Manual Review/memory | Bounded regression group | [Project State](../PROJECT_STATE.md) |
| 6 Aug 2026 | `1601ae4` | `python3 -m compileall -q backend tests` | Pass | None emitted | Repository compilation | Not runtime test | Phase 5 validation |
| 11 Aug 2026 | `1811430` | `python3 -m pytest -q tests` | 1,889 passed, 55 skipped | 385 | Full local backend test tree | Skips include deliberately unavailable/external paths; no production mutation | Current QA reconciliation |
| 11 Aug 2026 | `1811430` | Complete frontend Jest suite | 312 passed, 28 suites | Not consolidated | Current frontend regression baseline | JSDOM cannot prove physical-browser/platform state | Current QA reconciliation |
| 11 Aug 2026 | `1811430` | `python3 -m compileall -q backend tests` | Pass | None emitted | Current repository compilation | Static validation only | Current QA reconciliation |

## Reconstruction limitations

CI history is not comprehensively preserved in repository documents. Some later milestones record “passed” without totals or warnings. No number has been inferred. Pending chat/Codex records may add evidence but cannot silently change this register.

## Related documents

[QA Master](QA_MASTER.md), [Open Findings](OPEN_FINDINGS.md), [Completed Phases](COMPLETED_PHASES.md), [Roadmap Master](../ROADMAP_MASTER.md), and [Deployment](../OPERATIONS/DEPLOYMENT.md).

## Known limitations

Passing tests do not prove deployed identity, provider health, indexing, inbox delivery, performance or Mobile Safari behaviour. External verification must remain bounded and privacy-safe.
