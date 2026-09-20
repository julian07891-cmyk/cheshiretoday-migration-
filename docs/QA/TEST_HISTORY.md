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

CRACO/Jest tests live beside components and services. They cover public routes, metadata, Admin workflows, responsive contracts, analytics, newsletter and social publishing. Commit `dcd5cfa` added seven focused public-search accessibility tests; 42 related and 367 total frontend tests passed before deployment. JSDOM cannot prove real browser or assistive-technology behaviour, so bounded production checks remain separate and no screen-reader certification is inferred.

## Compilation checks

The 29 July repository-wide compilation failed on three tracked legacy modules. Git `7c2ac62` repaired them. `python3 -m compileall -q backend tests` passes at Phase 5 reconstruction.

## Production builds

The 29 July production React build passed. Later analytics, metadata and mobile milestones record successful `npm --prefix frontend run build` validations. Exact warning counts are not consistently preserved. `render_build.sh` remains the deployment build path.

## Security tests

`tests/test_committed_admin_credential_hygiene.py` scans tracked content; `tests/test_external_http_test_safety.py` verifies loopback-only targets, malformed/public target refusal, credential-read ordering and no redirects. Newsletter security suites cover token purpose, challenge, replay, enumeration resistance and rate limits.

## Newsletter tests

Coverage includes public landing/signup, consent parity, welcome email, secure preferences, request links, reactivation, unsubscribe, one-click contracts, challenge enforcement, unique-index provisioning, click redirects, HTML and runtime collaborators. Provider/live inbox delivery remains outside unit tests.

Newsletter Funnel V1 commit `66fde10` contains exactly eight implementation and
test files: `backend/app/admin_analytics.py`,
`backend/app/newsletter_signup_funnel.py`, `backend/server.py`,
`frontend/src/components/NewsletterSignupSimplification.test.jsx`,
`frontend/src/components/homepage/NewsletterFull.jsx`,
`tests/test_admin_analytics_summary.py`,
`tests/test_newsletter_signup_funnel.py`, and
`tests/test_newsletter_subscriber_creation_fields.py`. Its recorded counts are
scoped to this capability and the stated related regressions, not unrelated
systems.

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
| 26 Aug 2026 | `24f381e` | Admin indexing focused suite | 11 passed | Not recorded | First-byte Admin header, paths and robots contract | Functional implementation verification; production checked separately | QA-SEO-002 closure |
| 26 Aug 2026 | `24f381e` | Related regression suites | 74 passed | Not recorded | Admin/static delivery, auth and public SEO compatibility | Bounded related regression set | QA-SEO-002 closure |
| 26 Aug 2026 | `24f381e` | Sitemap regression suite | 9 passed | Not recorded | Public and news sitemap preservation | Functional, not external indexing proof | QA-SEO-002 closure |
| 26 Aug 2026 | `24f381e` | `python3 -m compileall -q backend tests`; `git diff --check` | Pass | None emitted | Compilation and diff hygiene | Static validation only | QA-SEO-002 closure |
| 27 Aug 2026 | `dcd5cfa` | Public search accessibility focused | 7 passed | None | Input names, native links, Escape/focus, polite status, stale-response safety | No screen-reader certification or manufactured production failure | Current QA reconciliation |
| 27 Aug 2026 | `dcd5cfa` | Public search related regressions | 42 passed | Existing diagnostic output only | Public metadata, hub/category/authority, homepage and article surfaces | Bounded related set | Current QA reconciliation |
| 27 Aug 2026 | `dcd5cfa` | Complete frontend Jest suite | 367 passed, 37 suites | Existing unrelated diagnostic output only | Full safe frontend baseline | Browser production verification recorded separately | Current QA reconciliation |
| 27 Aug 2026 | `dcd5cfa` | Production frontend build and `git diff --check` | Pass | Stale Browserslist-data notice | Production bundle and whitespace validation | Build does not prove deployment | Current QA reconciliation |
| 2 Sep 2026 | `70057e1` | Homepage article-list timing/materialisation focused regressions and static validation | Passed; exact total not preserved here | Not recorded | Exact homepage predicate, count bypass, 100/100 caps, unchanged request shapes/force/fallback/timing contracts | Functional evidence; production latency checked separately | Git `70057e1` and implementation review |
| 4 Sep 2026 | `70057e1` | Five sequential production requests with temporary timing gate | 5/5 HTTP 200; exactly five correlated markers | None observed | Like-for-like homepage materialisation verification | Bounded five-request sample; does not identify the remaining client residual | Production deployments `dep-dad5jv2jnfac73ehqh20`, `dep-dad5pcgn74is73dd4mj0` |
| 17 Sep 2026 | `be0182b` | Third-party analytics consent focused suites | 17 passed, 4 suites | None material recorded | Consent state, provider loading, route tracking and gated custom events | Automated evidence; not production request interception | Implementation verification |
| 17 Sep 2026 | `be0182b` | Related frontend regressions | 118 passed, 10 suites | None material recorded | Public routing, analytics and first-party compatibility | Bounded regression set | Implementation verification |
| 17 Sep 2026 | `be0182b` | Production frontend build and `git diff --check` | Pass | No material failure | Production bundle and diff hygiene | Build does not prove provider collection | Implementation verification |
| 17 Sep 2026 | `be0182b` | Production browser consent acceptance | Observable behaviour passed; event-level verdict inconclusive | No confirmed defect | Unknown/rejected/accepted/withdrawal/reload, `/admin`, mobile, recorder absence | Tooling could not combine isolated storage inspection with request interception/payload inspection | Deployment `dep-dam3mb3ncjis73cit8mg`; instance `w8frn` |
| 18 Sep 2026 | `bbc526c` | RSS-preview/body-quality focused suites | 44 passed | None material recorded | Block boundaries, terminal markers, pre-sanitisation classification, replacement distinction and Manual Review routing | Implementation evidence only | Commit-gate verification |
| 18 Sep 2026 | `bbc526c` | Importer / Manual Review / scheduler regressions | 130 passed, 12 skipped | None material recorded | Import and protected workflow compatibility | Bounded regression set; not production evidence | Commit-gate verification |
| 18 Sep 2026 | `bbc526c` | Memory observability / Editorial Similarity isolation / cleanup regressions | 104 passed | None material recorded | Protected reliability and isolation boundaries | Bounded regression set | Commit-gate verification |
| 18 Sep 2026 | `bbc526c` | `python3 -m compileall -q backend tests`; `git diff --check`; complete unstaged/staged reviews | Pass / approved | No Blocker, Material or Minor finding remained | Compilation, diff hygiene and review gate | Does not prove production behaviour | Commit-gate verification |
| 18 Sep 2026 | `bbc526c` | Natural 18:00 article-generation acceptance | Partial: incomplete-preview routing and bounded HTML-boundary behaviour verified | Nonfatal Warrington/Knutsford Guardian HTTP 403 feed warnings | One scheduled run; Guardian candidate routing; bounded Admin/public inspection | Complete-replacement path not naturally exercised; historical records not repaired | Deployment `dep-damij1btqb8s73fvesp0`; instance `klzb8` |
| 19 Sep 2026 | `66fde10` | Newsletter Funnel V1 focused backend | 69 passed | None material recorded | Signup attempt/outcome aggregation, placement normalisation, subscriber semantics and failure isolation | Focused capability scope only | Implementation verification |
| 19 Sep 2026 | `66fde10` | Dedicated Admin analytics | 15 passed | None material recorded | Funnel totals, placement breakdown, conversion and subsection isolation | Does not cover unrelated Admin systems | Implementation verification |
| 19 Sep 2026 | `66fde10` | Frontend signup/service contract | 9 passed | None material recorded | NewsletterFull placement and removal of misleading pre-result event | JSDOM/service contract evidence | Implementation verification |
| 19 Sep 2026 | `66fde10` | Expanded frontend consent/provider/trackEvent | 17 passed | None material recorded | Adjacent analytics-consent compatibility | Does not repeat event-level production verification | Implementation verification |
| 19 Sep 2026 | `66fde10` | Broader relevant regressions | 294 passed | None material recorded | Newsletter, Admin analytics and protected adjacent behaviour | Bounded relevant set, not repository-wide proof | Implementation verification |
| 19 Sep 2026 | `66fde10` | Production frontend build; `python3 -m compileall -q backend tests`; `git diff --check` | Pass | No material failure | Build, compilation and diff hygiene | Static/build evidence only | Implementation verification |
| 19 Sep 2026 | `66fde10` | Controlled Newsletter Funnel V1 production acceptance | Pass: one HTTP 200/`created` signup, exact aggregate delta and matching Admin report | Pre-existing full-email logging confirmed separately | Subscriber creation, anonymous aggregate, retention/index contract and Admin continuity | No inbox-delivery or distributed exact-once claim; acceptance subscriber retained | Deployment `dep-dan3beojo6nc7395spm0`; instance `fkdbq` |
| 19 Sep 2026 | `03a6abb` | Focused newsletter logging privacy/subscribe/welcome suites | 47 passed, 0 failed, 0 skipped | Three initial Material evidence weaknesses corrected before final approval | Created/existing/duplicate/welcome/failure privacy, Funnel preservation and bounded diagnostics | Automated branch evidence; no deliberate production identity-bearing failure | Capability verification |
| 19 Sep 2026 | `03a6abb` | Relevant newsletter/Funnel/Admin/provider/scheduler regressions | 1,145 passed, 12 skipped | None remained after correction | Protected subscriber, delivery, provider, digest, scheduler, Funnel, analytics and Admin contracts | Bounded relevant set, not complete repository suite | Capability verification |
| 19 Sep 2026 | `03a6abb` | `python3 -m compileall -q backend tests`; `git diff --check`; complete unstaged re-review and staged review | Pass / approved | Final Blocker: none; Material: none; Minor: none | Compilation, diff hygiene and complete review gates | Static/review evidence only | Commit-gate verification |
| 19–20 Sep 2026 | `03a6abb` | Automatic deployment and bounded production observation | Pass: exact SHA Live; build/Uvicorn/Mongo/index/APScheduler healthy; health and three public surfaces HTTP 200 | No attributable logging-format/changed-variable failure, traceback, fatal error, OOM, exit 137, restart or material 5xx observed | Deployment and immediate runtime compatibility | Every failure branch was not naturally exercised; historical logs unchanged; no compliance claim | Deployment `dep-daneoh6q1p3s73cdmf9g`; instance `zpcmz` |

## Reconstruction limitations

CI history is not comprehensively preserved in repository documents. Some later milestones record “passed” without totals or warnings. No number has been inferred. Pending chat/Codex records may add evidence but cannot silently change this register.

## Related documents

[QA Master](QA_MASTER.md), [Open Findings](OPEN_FINDINGS.md), [Completed Phases](COMPLETED_PHASES.md), [Roadmap Master](../ROADMAP_MASTER.md), and [Deployment](../OPERATIONS/DEPLOYMENT.md).

## Known limitations

Passing tests do not prove deployed identity, provider health, indexing, inbox delivery, performance or Mobile Safari behaviour. External verification must remain bounded and privacy-safe.
