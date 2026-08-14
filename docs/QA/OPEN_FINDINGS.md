# Cheshire Today — Open Findings Register

> **Reconstruction status:** Live finding register at HEAD `b497635`. It includes all original identifiers exactly once, even when closed at repository level.

## Document purpose

Record unresolved, partially verified, completed and superseded QA findings with durable closure criteria.

## Authority and evidence

Current code, Git commits and tests control current technical status. The [original QA report](QA_REPORT_2026-07-29.md) controls original wording/severity. Production claims require repository-preserved live evidence. See [Source Register](../HISTORY/SOURCE_REGISTER.md).

## How to use this document

Work highest current severity first. Update an entry only when evidence changes; never delete its historical identity.

## Original QA findings

### QA-SEC-001

- **Original severity:** Critical
- **Current severity:** Closed
- **Area:** Security / credentials
- **Original finding:** A production Admin credential was committed in legacy tests and historical tracked artefacts.
- **Current status:** **CLOSED — ROTATION/REVOCATION PROVEN** on 11 August 2026. The current tree was already contained; production rotation, session revocation and old-access rejection are now verified.
- **Current-code evidence:** `tests/external_admin_test_safety.py` reads credentials only after loopback target approval; current hygiene tests scan tracked content.
- **Fixing commits:** `b804cdd`, `603e11b`.
- **Test evidence:** 29 July remediation records 31 focused safety/hygiene passes, 48 affected-group passes with 55 safe skips, a production-URL refusal subprocess, and 45 related authentication/mutation passes.
- **Deployment evidence:** On Render service `cheshiretoday-migration-` (`srv-d5virmm3jp1c73c9d6tg`), only `ADMIN_PASSWORD` was rotated. Final deployment `dep-d9tiku142hec738apl80` ran revision `3b3f4c9` on instance `6xgfs`; build succeeded at 14:59:53 BST, application startup completed at 15:00:49 and the service was live at 15:00:55. `ADMIN_PERMANENT_TOKEN` was unchanged.
- **Production evidence:** Replacement-credential login and new bearer-token verification passed; the historical password was rejected with HTTP 401; unauthenticated `/api/admin/verify` returned 401 and `/api/health` returned 200. Nine pre-rotation Admin tokens were invalidated at the 14:42:29 BST cutoff, and the Render restart eliminated old-instance in-memory tokens. One verified post-rotation session was active. No startup, Mongo, scheduler, OOM, restart-loop or material 5xx failure was observed.
- **Residual risk:** Reachable Git history still contains the revoked historical credential and was not rewritten. Production no longer accepts that password.
- **Closure criteria:** Met: current-tree containment retained, dated production rotation recorded, affected sessions invalidated, replacement login/token verified, historical access rejected and service health confirmed without recording secret material.
- **Owner/documentation responsibility:** Production security owner; record evidence in Project State/production timeline without secret material.
- **Sources:** [29 July report](QA_REPORT_2026-07-29.md), Git `b804cdd`, `603e11b`; `tests/test_committed_admin_credential_hygiene.py`; authenticated Render/Admin/Mongo verification reconciled 11 August 2026.

### QA-TEST-001

- **Original severity:** High
- **Current severity:** Low
- **Area:** Test safety and hermeticity
- **Original finding:** Legacy backend HTTP suites were production-coupled and mutation-capable.
- **Current status:** Remediated and test-verified at repository level; broader test-organisation maintenance remains separate.
- **Current-code evidence:** Four configurable suites use `tests/external_admin_test_safety.py`; only explicit loopback HTTP(S) is permitted, redirects and public/production targets are refused.
- **Fixing commits:** `b804cdd`, `603e11b`.
- **Test evidence:** Focused boundary, subprocess and related authentication results are preserved in the original report.
- **Deployment evidence:** Not applicable to local test harness safety.
- **Production evidence:** No production request was required or permitted.
- **Remaining gap:** Keep the safe-default command documented and continue separating external smoke tests from hermetic suites.
- **Closure criteria:** Already met for the original mutation-boundary defect; reopen if a default test can contact an external target or mutate production.
- **Owner/documentation responsibility:** Test maintainers; [Test History](TEST_HISTORY.md).
- **Sources:** [29 July report](QA_REPORT_2026-07-29.md), Git `603e11b`, `tests/test_external_http_test_safety.py`.

### QA-CODE-001

- **Original severity:** High
- **Current severity:** Low
- **Area:** Compilation
- **Original finding:** Three tracked legacy Python modules failed compilation.
- **Current status:** Remediated and compilation-verified at repository level.
- **Current-code evidence:** `backend/config.py`, `backend/services/article_service.py`, and `backend/services/auth_service.py` parse at current HEAD.
- **Fixing commits:** `7c2ac62`.
- **Test evidence:** `python3 -m compileall -q backend tests` passes at Phase 5 reconstruction.
- **Deployment evidence:** Not required for dead/legacy compilation health; no runtime activation was introduced.
- **Production evidence:** None required; no behaviour change claimed.
- **Remaining gap:** Decide long-term ownership or removal when refactoring legacy services.
- **Closure criteria:** Already met for syntax failure; reopen on repository-wide compilation failure.
- **Owner/documentation responsibility:** Backend maintainers; [Test History](TEST_HISTORY.md).
- **Sources:** [29 July report](QA_REPORT_2026-07-29.md), Git `7c2ac62`.

### QA-SEC-002

- **Original severity:** High
- **Current severity:** Closed
- **Area:** Security / CORS
- **Original finding:** Credentialed CORS accepted arbitrary origins.
- **Current status:** **CLOSED — PRODUCTION CORS RESTRICTION VERIFIED** on 12 August 2026.
- **Current-code evidence:** Commit `b497635` replaces the wildcard origin with explicit `https://cheshiretoday.co.uk`, `http://localhost:3000` and `http://127.0.0.1:3000` origins. Credentials, methods and headers remain intentionally unchanged.
- **Fixing commit:** `b4976357776f7414a3edcb49fc69ee046c525c23`.
- **Test evidence:** Eight focused CORS contract tests passed, including approved origins, hostile-origin rejection, credentialed preflight, no-Origin compatibility, public API and authenticated Admin verification.
- **Deployment evidence:** Render deployment `dep-d9u594oae00c73bs1lvg` ran revision `b497635` on instance `qmqjs` and became live at 12:12:56 BST on 12 August 2026.
- **Production evidence:** Canonical-origin preflight returned HTTP 200 with the exact origin and credentials enabled, with no wildcard ACAO. A hostile `https://evil.example` preflight returned HTTP 400 `Disallowed CORS origin`, without ACAO, reflection or wildcard. Health and homepage/article/newsletter smoke checks returned 200; unauthenticated Admin verification returned 401; an authorised operator confirmed fresh Admin login and authenticated access after deployment. No startup, Mongo, scheduler, OOM, restart-loop or material 5xx regression was observed.
- **Residual risk:** None for the wildcard-origin defect itself. The unchanged broad methods/headers and credential support are separate future-hardening questions, not blockers for this closure.
- **Closure criteria:** Met: reviewed explicit origins, focused tests, exact deployment identity, bounded positive and negative production preflights, Admin compatibility and healthy production are recorded.
- **Owner/documentation responsibility:** Backend/security owner; deployment and QA records.
- **Sources:** [29 July report](QA_REPORT_2026-07-29.md), Git `b497635`,
  `backend/server.py` CORS middleware; focused tests and authenticated
  Render/Admin/preflight verification reconciled 12 August 2026.

### QA-A11Y-001

- **Original severity:** Medium
- **Current severity:** Medium
- **Area:** Accessibility / public search
- **Original finding:** Desktop search results lacked semantic keyboard operation, labelled input and no-results feedback.
- **Current status:** Open; unrelated Admin mobile accessibility work does not close it.
- **Current-code evidence:** No evidenced fixing commit for the `NewsHeader` desktop search contract.
- **Fixing commits:** None identified.
- **Test evidence:** Original live/source audit only.
- **Deployment evidence:** None.
- **Production evidence:** Original keyboard/no-results behaviour; no later retest.
- **Remaining gap:** Semantic links/buttons, programmatic label, keyboard selection and polite status.
- **Closure criteria:** Behavioural accessibility tests, complete frontend regression/build, deployment and desktop keyboard/screen-reader-oriented production check.
- **Owner/documentation responsibility:** Frontend accessibility owner.
- **Sources:** [29 July report](QA_REPORT_2026-07-29.md), `frontend/src/components/NewsHeader.jsx`.

### QA-SEO-001

- **Original severity:** Medium
- **Current severity:** Closed
- **Area:** SEO / rendered metadata
- **Original finding:** Static homepage and route-specific metadata accumulated in settled browser DOM.
- **Current status:** Remediated, test-verified, deployed and production-verified.
- **Current-code evidence:** Managed static shell and always-mounted reconciliation owner; route-specific Helmet owners.
- **Fixing commits:** `6bfe896`, `1e5c2da`; verification record `7ca1269`.
- **Test evidence:** `frontend/src/PublicMetadataUniqueness.test.jsx` covers production owners, seven-field uniqueness and SPA navigation.
- **Deployment evidence:** Repository records identify the deployed reconciliation commits.
- **Production evidence:** Settled DOM, SPA transitions, crawler HTML, sitemaps and robots were verified; no indexing recovery was claimed.
- **Remaining gap:** Search Console sampling is separate, not required to close duplicate DOM ownership.
- **Closure criteria:** Met; reopen if settled routes contain duplicate/stale managed metadata.
- **Owner/documentation responsibility:** Frontend SEO owner; [SEO architecture](../ARCHITECTURE/SEO_AND_CRAWLERS.md).
- **Sources:** [Project State](../PROJECT_STATE.md), Git `6bfe896`, `1e5c2da`, `7ca1269`.

### QA-SEO-002

- **Original severity:** Medium
- **Current severity:** Medium
- **Area:** SEO/privacy / Admin
- **Original finding:** Unauthenticated Admin login lacked first-byte `noindex`; Googlebot rules did not repeat the wildcard disallow.
- **Current status:** Partially remediated — homepage metadata leakage is gone after React settles; server-level first-byte and robots-group criteria remain unproven.
- **Current-code evidence:** Runtime metadata cleanup removes homepage fields on `/admin`; authenticated `AdminDashboard` has robots metadata, but ordinary SPA delivery is not an evidenced server-level Admin noindex response.
- **Fixing commits:** Metadata portion `6bfe896`, `1e5c2da`.
- **Test evidence:** Admin isolation in `PublicMetadataUniqueness.test.jsx`.
- **Deployment evidence:** Metadata reconciliation deployed.
- **Production evidence:** Live `/admin` showed no homepage canonical/description/social metadata after settling; first-byte noindex was not established.
- **Remaining gap:** Server-delivered Admin robots directive and aligned Googlebot rules.
- **Closure criteria:** Add focused root-response/robots tests, deploy, verify initial HTML and direct Googlebot response without authenticating.
- **Owner/documentation responsibility:** Backend SEO/security owner.
- **Sources:** [29 July report](QA_REPORT_2026-07-29.md), [SEO architecture](../ARCHITECTURE/SEO_AND_CRAWLERS.md).

### QA-PERF-001

- **Original severity:** Medium
- **Current severity:** Medium
- **Area:** Performance
- **Original finding:** Public article-list TTFB was consistently around 1.4–1.5 seconds warm, with slower larger request and visible homepage skeleton delay.
- **Current status:** Open; no measured query/index/cache remediation.
- **Current-code evidence:** Public article selection still performs database queries plus in-process eligibility/interleaving work.
- **Fixing commits:** None identified.
- **Test evidence:** Functional endpoint tests do not close latency.
- **Deployment evidence:** None.
- **Production evidence:** 29 July timings only; current timings unknown.
- **Remaining gap:** Current bounded latency sample and Mongo execution-plan/index evidence.
- **Closure criteria:** Profile without altering editorial selection, implement only evidence-supported optimisation, pass functional regressions, deploy and compare like-for-like latency.
- **Owner/documentation responsibility:** Backend/performance owner; monitoring record.
- **Sources:** [29 July report](QA_REPORT_2026-07-29.md), [Monitoring](../OPERATIONS/MONITORING.md).

### QA-OPS-001

- **Original severity:** Medium
- **Current severity:** Medium
- **Area:** Render memory and operations
- **Original finding:** OOM risk was only partially evidenced after newsletter and import memory incidents.
- **Current status:** Monitoring — immediate duplicate-cleanup lifecycle OOM risk operationally mitigated; broader process-memory stability not proven.
- **Current-code evidence:** Thirteen bounded markers include current RSS and isolate first-pass Stage 2. `49e5fe4` removed simultaneous full-list retention; `c06c837` streams/projects the short-content scan; `cd3f093` streams/projects the first duplicate scan; `1811430` avoids joined full-article strings in short-content qualification. Scheduler locks and RSS concurrency eight remain.
- **Fixing commits:** Observability `42736f9`, `fd7cc82`, `0cdc089`; cleanup lifecycle/scan changes `49e5fe4`, `c06c837`, `cd3f093`, `1811430`.
- **Test evidence:** Five focused lifecycle regressions, 28 related cleanup/auth/memory/live-pool regressions, compilation and diff checks passed before commit `49e5fe4`.
- **Deployment evidence:** Render automatically deployed `49e5fe4` on 7 August 2026; startup completed and the service became live before the 12:00 scheduled run.
- **Production evidence:** The pre-fix 7 August 06:00 run reached 530.0 MB against the verified 512 MB ceiling and was followed by an OOM. Later normal observations established structural improvement. On 13 August at 18:00, `d8943e8` completed normally at 305.5 MB current RSS (130.7 MB start; +174.8 MB net), leaving 206.5 MB marker-level headroom. Visible-pool, first duplicate Stage 1, first Stage 2 and short-content scan intervals were +32.7, +41.0, 0.0 and +42.0 MB; cleanup from visible-pool completion to job completion was +83.0 MB. No OOM or restart occurred. This run was worse than recent reconciled observations, but one noisier run does not prove a worsening trend or identify a new implementation target.
- **Remaining gap:** Cumulative process RSS still rises materially and may remain elevated. First duplicate Stage 1, visible-pool work, short-content cursor/decoded-string behaviour, feed work, allocator retention and high-start workloads remain under observation; obtain another normal 13-marker run before selecting a target.
- **Closure criteria:** A sustained evidence-backed stability window covering scheduled imports and newsletter workloads, or separately reviewed further optimisation followed by normal-run production verification.
- **Owner/documentation responsibility:** Production operations owner; [Monitoring](../OPERATIONS/MONITORING.md).
- **Sources:** [29 July report](QA_REPORT_2026-07-29.md), Git `42736f9`, `49e5fe4`, `c06c837`, `cd3f093`, `0cdc089`, `1811430`, [Production Timeline](../PRODUCTION_TIMELINE.md).

### QA-DOC-001

- **Original severity:** Low
- **Current severity:** Low
- **Area:** Documentation / Threads
- **Original finding:** Threads operational documentation and implementation/deployment descriptions diverged.
- **Current status:** Open pending reconciliation; later Social Publishing code and production evidence supersede parts of the original state, while the brand README still describes verified opening/context workflow.
- **Current-code evidence:** Current Social Publishing component contracts and `docs/brand-assets/social/threads/README.md` are not fully reconciled.
- **Fixing commits:** No dedicated final documentation reconciliation identified.
- **Test evidence:** Unified Social Publishing focused suites validate current component behaviour.
- **Deployment evidence:** Later Admin bundle and production workflows were observed, but documentation remains mixed.
- **Production evidence:** Repository records later authenticated checks without publishing.
- **Remaining gap:** Preserve history while updating the current operator instructions to match current deterministic workflow.
- **Closure criteria:** Reviewed docs/code comparison, update in a dedicated documentation change, validate links and confirm no historical record was rewritten.
- **Owner/documentation responsibility:** Social Publishing/documentation owner.
- **Roadmap mapping:** [Roadmap Master](../ROADMAP_MASTER.md), `QA-DOC-001` Threads/operator-documentation consistency.
- **Sources:** [29 July report](QA_REPORT_2026-07-29.md), `docs/brand-assets/social/threads/README.md`.

### QA-MAINT-001

- **Original severity:** Low
- **Current severity:** Low
- **Area:** Maintenance
- **Original finding:** FastAPI lifecycle, multipart/gzip, Browserslist and backup artefact warnings reduced validation signal.
- **Current status:** Open maintenance backlog.
- **Current-code evidence:** `backend/server.py` still uses `@app.on_event`; tracked backup files and warning-producing dependencies remain evidenced.
- **Fixing commits:** None comprehensive.
- **Test evidence:** Later suites pass with varying warnings; warning-free baseline is not established.
- **Deployment evidence:** Not applicable until changes exist.
- **Production evidence:** No current failure attributed solely to these warnings.
- **Remaining gap:** Separate dependency/lifecycle/artefact cleanup with warning baseline.
- **Closure criteria:** Scoped cleanup, safe full regressions/build, documented before/after warnings and deployment where runtime code changes.
- **Owner/documentation responsibility:** Maintenance owner; [Test History](TEST_HISTORY.md).
- **Sources:** [29 July report](QA_REPORT_2026-07-29.md), current code/configuration.

## Post-29 July findings

### CT-QA-2026-001

- **Original severity:** Not applicable
- **Current severity:** Medium
- **Area:** Documentation authority
- **Original finding:** Operational truth, history, QA and chat-derived evidence were spread across a near-million-byte Project State and multiple records.
- **Current status:** Repository reconstruction and its authority transition were committed in `a6e0f98`; external-source reconciliation remains incomplete.
- **Current-code evidence:** Not a runtime defect; repository documentation inventory and [Source Register](../HISTORY/SOURCE_REGISTER.md) establish the sprawl.
- **Fixing commits:** Documentation reconstruction `a6e0f98`; later authority updates `f5e4094` and this 11 August reconciliation.
- **Test evidence:** Hash, link, heading and content validations by phase.
- **Deployment evidence:** Not applicable.
- **Production evidence:** Not applicable.
- **Remaining gap:** Reconcile pending ChatGPT export, structured Codex history, historical PDFs and production evidence after the stated baseline.
- **Closure criteria:** The tracked master set and privacy-safe archive are complete; closure additionally requires a durable reconciliation of the remaining external evidence sources.
- **Owner/documentation responsibility:** Documentation reconstruction owner.
- **Roadmap mapping:** [Roadmap Master](../ROADMAP_MASTER.md), Documentation reconstruction roadmap.
- **Sources:** [Source Register](../HISTORY/SOURCE_REGISTER.md), [Architecture Master](../ARCHITECTURE_MASTER.md).

### CT-QA-2026-002

- **Original severity:** Not applicable
- **Current severity:** Medium
- **Area:** Editorial Similarity operations
- **Original finding:** Phase 2B was deployed shadow-only, but the required multi-run production observation/calibration gate was incomplete at the earlier repository baseline.
- **Current status:** Monitoring — numerical three-run observation-count gate satisfied; calibration and any product decision remain unapproved.
- **Current-code evidence:** Explicit scheduled-only activation, 50+50 pool, 100 corpus, 20 shortlist/scorer cap, safe logs and no operational decisions.
- **Fixing commits:** `8043fdd`, `5e1a875`; deployment record `1601ae4`.
- **Test evidence:** 54 focused Phase 2A/2B tests; related group 178 passed and 12 skipped; compile/Black/diff checks recorded.
- **Deployment evidence:** Project State records `5e1a875` live on 4 August.
- **Production evidence:** At least three complete normal scheduled production shadow observations are preserved at current HEAD, with health, duration, bounded similarity evidence and unchanged publication authority.
- **Remaining gap:** Calibration review and any threshold, UI or enforcement decision require separate evidence and explicit approval; no such change is currently justified.
- **Closure criteria:** Complete a separately scoped calibration decision, or explicitly retain shadow-only monitoring based on reviewed evidence. Version 1 remains authoritative throughout.
- **Owner/documentation responsibility:** Editorial/import and production operations owners.
- **Sources:** [Editorial Similarity architecture](../ARCHITECTURE/EDITORIAL_SIMILARITY.md), [Project State](../PROJECT_STATE.md).

### CT-QA-2026-003

- **Original severity:** Medium
- **Current severity:** Medium
- **Area:** Scheduler failure isolation
- **Original finding:** `daily_article_generation` logged a scheduler-lock exception and continued, so database/lock failure could remove the ownership guarantee.
- **Current status:** **CLOSED — FAIL-CLOSED ARTICLE LOCK VERIFIED** on 13 August 2026.
- **Current-code evidence:** Commit `d8943e8c7284781b8fefb915e00b4e53f831c3bb` logs a lock-acquisition error and returns, preventing unlocked generation. Lock key, stale timeout, acquisition/release queries, schedules and downstream work are unchanged.
- **Fixing commits:** `d8943e8`.
- **Test evidence:** Seven focused tests prove seed-operation and atomic-acquisition exceptions skip generation, cleanup and lock deletion; held locks skip; successful and stale acquisitions execute; scheduler registrations remain unchanged.
- **Deployment evidence:** `d8943e8` was deployed on Render instance `qc88z` before the natural 13 August 18:00 run.
- **Production evidence:** The natural run started at 18:00:00.001 BST, acquired `article_gen_2026081317` at 18:00:00.245, and completed at 18:01:45.983 in 105.98 seconds. Logs showed exactly one start, acquisition, generation, cleanup and completion, with no competing instance, unlocked execution or lock-acquisition failure. APScheduler succeeded and `/api/health` returned HTTP 200.
- **Residual boundary:** No production lock failure was deliberately induced. Hermetic tests verify the exception branch; production verifies normal-path compatibility. Broader lock release/finally ownership questions were outside this fix and are not silently closed.
- **Closure criteria:** Satisfied by the explicit fail-closed decision, focused failure-path tests, deployed implementation and single-execution natural production verification.
- **Owner/documentation responsibility:** Scheduler/backend owner; [Scheduler](../OPERATIONS/SCHEDULER.md).
- **Roadmap mapping:** [Roadmap Master](../ROADMAP_MASTER.md), completed `CT-QA-2026-003` fail-closed article lock.
- **Sources:** `backend/server.py` `daily_article_generation`; [Article Pipeline](../ARCHITECTURE/ARTICLE_PIPELINE.md).

## Related documents

[QA Master](QA_MASTER.md), [Completed Phases](COMPLETED_PHASES.md), [Test History](TEST_HISTORY.md), [Roadmap Master](../ROADMAP_MASTER.md), and [29 July QA report](QA_REPORT_2026-07-29.md).

## Known limitations

Post-HEAD production investigations, pending ChatGPT/Codex history and external dashboards are unreconciled. “Closed” here means the stated original defect’s evidence threshold, not that adjacent maintenance is finished.
