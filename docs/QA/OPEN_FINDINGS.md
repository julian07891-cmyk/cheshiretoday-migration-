# Cheshire Today — Open Findings Register

> **Reconstruction status:** Live finding register at HEAD `1601ae4`. It includes all original identifiers exactly once, even when closed at repository level.

## Document purpose

Record unresolved, partially verified, completed and superseded QA findings with durable closure criteria.

## Authority and evidence

Current code, Git commits and tests control current technical status. The [original QA report](QA_REPORT_2026-07-29.md) controls original wording/severity. Production claims require repository-preserved live evidence. See [Source Register](../HISTORY/SOURCE_REGISTER.md).

## How to use this document

Work highest current severity first. Update an entry only when evidence changes; never delete its historical identity.

## Original QA findings

### QA-SEC-001

- **Original severity:** Critical
- **Current severity:** Critical
- **Area:** Security / credentials
- **Original finding:** A production Admin credential was committed in legacy tests and historical tracked artefacts.
- **Current status:** Open — contained in current tree and test-verified; rotation/revocation and history exposure are not production-verified.
- **Current-code evidence:** `tests/external_admin_test_safety.py` reads credentials only after loopback target approval; current hygiene tests scan tracked content.
- **Fixing commits:** `b804cdd`, `603e11b`.
- **Test evidence:** 29 July remediation records 31 focused safety/hygiene passes, 48 affected-group passes with 55 safe skips, a production-URL refusal subprocess, and 45 related authentication/mutation passes.
- **Deployment evidence:** Not sufficient; test containment is repository behaviour.
- **Production evidence:** No repository evidence that the exposed credential and associated tokens were rotated/revoked and retested.
- **Remaining gap:** Operational rotation/revocation proof and a safe confirmation that old access no longer works; Git history still retains the secret.
- **Closure criteria:** Record dated rotation/revocation, invalidate affected sessions/tokens as required, verify old access fails without exposing values, rescan current tree/history policy, and retain loopback tests.
- **Owner/documentation responsibility:** Production security owner; record evidence in Project State/production timeline without secret material.
- **Sources:** [29 July report](QA_REPORT_2026-07-29.md), Git `b804cdd`, `603e11b`; `tests/test_committed_admin_credential_hygiene.py`.

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
- **Current severity:** High
- **Area:** Security / CORS
- **Original finding:** Credentialed CORS accepted arbitrary origins.
- **Current status:** Open.
- **Current-code evidence:** `backend/server.py` still declares `allow_origins=["*"]`, `allow_credentials=True`, all methods and headers.
- **Fixing commits:** None.
- **Test evidence:** Original live hostile-origin preflight; no current positive/negative allow-list regression.
- **Deployment evidence:** Current code remains broad.
- **Production evidence:** 29 July production preflight confirmed the defect; no later live retest proves remediation.
- **Remaining gap:** Validated production/local origin allow-list and regression coverage.
- **Closure criteria:** Implement reviewed origin configuration, pass allowed/disallowed credentialed preflight tests, deploy exact commit, and repeat bounded live preflight verification.
- **Owner/documentation responsibility:** Backend/security owner; deployment and QA records.
- **Sources:** [29 July report](QA_REPORT_2026-07-29.md), `backend/server.py` CORS middleware.

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
- **Current status:** Monitoring — instrumentation deployed; stability not proven.
- **Current-code evidence:** Twelve bounded markers in `backend/app/article_generation_observability.py`; RSS concurrency eight; scheduler locks; large identity/cleanup reads and newsletter materialisation remain.
- **Fixing commits:** Observability `42736f9`; no optimisation commit claimed.
- **Test evidence:** `tests/test_article_generation_memory_observability.py` and related scheduler/import regressions.
- **Deployment evidence:** Later Project State records deployment context, but current HEAD does not contain a completed multi-run stability conclusion.
- **Production evidence:** Historical 512 MB OOM and 29/30 July generation correlations; post-HEAD investigations are unreconciled.
- **Remaining gap:** Multiple complete normal-run timelines, peaks/final RSS, post-run restart window and workload correlation.
- **Closure criteria:** Evidence-backed stability window or separately reviewed optimisation followed by normal-run production verification.
- **Owner/documentation responsibility:** Production operations owner; [Monitoring](../OPERATIONS/MONITORING.md).
- **Sources:** [29 July report](QA_REPORT_2026-07-29.md), Git `42736f9`, [Production Timeline](../PRODUCTION_TIMELINE.md).

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
- **Current status:** Phases 1–7.3, including the archive privacy decision and clean-checkout-safe archive-link correction, are complete locally, but the reconstruction has not yet passed the final documentation commit gate.
- **Current-code evidence:** Not a runtime defect; repository documentation inventory and [Source Register](../HISTORY/SOURCE_REGISTER.md) establish the sprawl.
- **Fixing commits:** None for the untracked reconstruction set.
- **Test evidence:** Hash, link, heading and content validations by phase.
- **Deployment evidence:** Not applicable.
- **Production evidence:** Not applicable.
- **Remaining gap:** Pass final review, obtain approval for commit/push, and reconcile pending ChatGPT, structured Codex, historical PDF and post-HEAD production evidence.
- **Closure criteria:** Approved tracked master set containing the privacy-safe archive; exact local archive excluded and preserved unchanged; and a durable plan for the remaining external and post-HEAD sources.
- **Owner/documentation responsibility:** Documentation reconstruction owner.
- **Roadmap mapping:** [Roadmap Master](../ROADMAP_MASTER.md), Documentation reconstruction roadmap.
- **Sources:** [Source Register](../HISTORY/SOURCE_REGISTER.md), [Architecture Master](../ARCHITECTURE_MASTER.md).

### CT-QA-2026-002

- **Original severity:** Not applicable
- **Current severity:** Medium
- **Area:** Editorial Similarity operations
- **Original finding:** Phase 2B is deployed shadow-only, but the required multi-run production observation/calibration gate is incomplete at repository HEAD.
- **Current status:** Monitoring.
- **Current-code evidence:** Explicit scheduled-only activation, 50+50 pool, 100 corpus, 20 shortlist/scorer cap, safe logs and no operational decisions.
- **Fixing commits:** `8043fdd`, `5e1a875`; deployment record `1601ae4`.
- **Test evidence:** 54 focused Phase 2A/2B tests; related group 178 passed and 12 skipped; compile/Black/diff checks recorded.
- **Deployment evidence:** Project State records `5e1a875` live on 4 August.
- **Production evidence:** No three-normal-run review is preserved at current HEAD.
- **Remaining gap:** At least three normal scheduled runs with health, duration, memory, pool/shortlist/comparison, provenance and unchanged outcome evidence.
- **Closure criteria:** Complete and reconcile the observation gate; approve or reject later calibration separately. Version 1 remains authoritative.
- **Owner/documentation responsibility:** Editorial/import and production operations owners.
- **Sources:** [Editorial Similarity architecture](../ARCHITECTURE/EDITORIAL_SIMILARITY.md), [Project State](../PROJECT_STATE.md).

### CT-QA-2026-003

- **Original severity:** Not applicable
- **Current severity:** Medium
- **Area:** Scheduler failure isolation
- **Original finding:** `daily_article_generation` logs a scheduler-lock exception and continues, so database/lock failure can remove the ownership guarantee.
- **Current status:** Open for evidence-led design review; no observed duplicate run is asserted.
- **Current-code evidence:** Lock acquisition is inside a `try/except`; the exception branch warns and continues to generation.
- **Fixing commits:** None.
- **Test evidence:** Existing scheduler-lock tests cover normal ownership/stale takeover, not an approved fail-closed policy change.
- **Deployment evidence:** Current deployed-code status must be checked separately.
- **Production evidence:** No duplicate generation caused by this branch is preserved at HEAD.
- **Remaining gap:** Determine intended availability-versus-duplication policy and quantify real lock failures before change.
- **Closure criteria:** Evidence review, explicit decision, focused failure-path tests, safe implementation if approved, and normal scheduled production verification.
- **Owner/documentation responsibility:** Scheduler/backend owner; [Scheduler](../OPERATIONS/SCHEDULER.md).
- **Roadmap mapping:** [Roadmap Master](../ROADMAP_MASTER.md), `CT-QA-2026-003` fail-closed lock-acquisition review.
- **Sources:** `backend/server.py` `daily_article_generation`; [Article Pipeline](../ARCHITECTURE/ARTICLE_PIPELINE.md).

## Related documents

[QA Master](QA_MASTER.md), [Completed Phases](COMPLETED_PHASES.md), [Test History](TEST_HISTORY.md), [Roadmap Master](../ROADMAP_MASTER.md), and [29 July QA report](QA_REPORT_2026-07-29.md).

## Known limitations

Post-HEAD production investigations, pending ChatGPT/Codex history and external dashboards are unreconciled. “Closed” here means the stated original defect’s evidence threshold, not that adjacent maintenance is finished.
