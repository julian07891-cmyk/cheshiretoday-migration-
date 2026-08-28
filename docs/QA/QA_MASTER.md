# Cheshire Today — QA Master

> **Reconstruction status:** Evidence-backed reconciliation at repository HEAD `dcd5cfa1bfc4e396ccd23d52878306e23e307501`. The immutable 29 July baseline is retained; later code, test, deployment and production evidence are classified separately.

## Document purpose

This is the central QA index and concise statement of current quality posture. Detailed live findings are in [Open Findings](OPEN_FINDINGS.md); this document does not replace the dated source report.

## Authority and evidence

Authority order is current code/configuration, Git history, current tests/build configuration, the [29 July QA report](QA_REPORT_2026-07-29.md), [historical records](../HISTORY/ENGINEERING_HISTORY_MASTER.md), [current architecture](../ARCHITECTURE_MASTER.md), and repository-preserved production evidence. See [Source Register](../HISTORY/SOURCE_REGISTER.md).

## How to use this document

Use the summary to choose a QA area, then consult the live register and test history. Never infer deployment or live verification from a commit or passing local suite.

## Current QA posture

The current HEAD is materially safer than the 29 July baseline: tracked credential literals were contained, external mutation tests were made loopback-only, legacy Python compilation was restored, first-party analytics and Most Read were corrected, rendered metadata was reconciled and production-verified, and bounded memory/similarity observability was added.

Evidence-backed status totals for the eleven original findings are:

| Classification | Count |
|---|---:|
| Open or not fully production verified | 5 |
| Remediated and verified by tests at repository level | 2 |
| Remediated, deployed and production verified | 4 |

Three additional post-baseline findings are registered: documentation authority
sprawl, Editorial Similarity calibration/product-decision evidence after completion
of the numerical observation-count gate, and the now-closed scheduler
lock-failure continuation risk. These totals describe evidence status, not severity totals.

## Original 29 July QA baseline

The audit at `2bcdf5c` found one critical credential exposure; high-risk non-hermetic tests, compilation failures and broad credentialed CORS; medium accessibility, metadata, latency and memory findings; and low documentation/maintenance debt. It also recorded healthy public routes, crawler responses, focused suites and frontend build. Its release recommendation applied to that baseline and is not silently rewritten.

## Finding reconciliation summary

The authoritative row-by-row reconciliation is [Open Findings](OPEN_FINDINGS.md). Original identifiers appear exactly once there, including repository-level closures. A finding closes only when its stated closure criteria are satisfied; remediation, tests, deployment and production verification remain separate fields.

## Security

Current tracked-tree credential scans and loopback-only external test boundaries are covered by `tests/test_committed_admin_credential_hygiene.py` and `tests/test_external_http_test_safety.py`.

`QA-SEC-001` is **CLOSED — ROTATION/REVOCATION PROVEN** as of 11 August 2026. Its original severity remains **Critical**. Only `ADMIN_PASSWORD` required production rotation; nine pre-rotation Admin sessions were invalidated, replacement login and bearer-token verification passed, and the historical password was rejected with HTTP 401. The current residual risk is that reachable Git history still retains the revoked historical credential; production no longer accepts it and history was not rewritten.

`QA-SEC-002` is **CLOSED — PRODUCTION CORS RESTRICTION VERIFIED** as of
12 August 2026. Its original severity remains **High**. Commit `b497635`
replaced wildcard browser origins with the canonical production origin and two
explicit local-development origins. Deployment `dep-d9u594oae00c73bs1lvg`
became live on instance `qmqjs` at 12:12:56 BST. Focused tests, canonical and
hostile production preflights, fresh Admin login compatibility, public health and
frontend smoke checks passed. There is no residual risk for the wildcard-origin
defect itself; unchanged credential, method and header policy is separate future
hardening rather than a closure blocker.

## Test safety and hermeticity

Commits `b804cdd` and `603e11b` removed literals and made four legacy HTTP suites refuse external targets and redirects. That closes the defined repository mutation-boundary defect, while broader suite organisation and warning cleanup remain maintenance work. Safe commands must never point mutation-capable tests at production.

## Compilation and build health

Commit `7c2ac62` repaired the three tracked Python syntax defects. Repository-wide `python3 -m compileall -q backend tests` passes at current HEAD. Multiple later frontend production builds are recorded as passing, but build success alone does not verify runtime providers or production behaviour.

## Accessibility

Admin mobile Safari received substantial responsive and touch hardening with real-iPhone verification under Safari Page Zoom 100%. `QA-A11Y-001` is **CLOSED — PRODUCTION VERIFIED** as of 27 August 2026. Commit `dcd5cfa` added durable public-search naming, native article-result links, ordinary Tab/Enter semantics, Escape dismissal with input-focus retention and polite loading/result/no-result feedback. Seven focused, 42 related and 367 total frontend tests plus the production build passed. Deployment `dep-da82j9uk1f9s73dgc1mg` on Standard instance `9sflp` passed bounded desktop and 390×844 mobile verification with public surfaces and HTTP 200 health preserved. No production request failure was manufactured; failure and stale-response handling rest on deployed code and tests. This closes the identified search defect, not site-wide accessibility or WCAG conformance.

## SEO and metadata

Rendered public metadata reconciliation was implemented in `6bfe896` and `1e5c2da`, deployed, and recorded as production-verified in `7ca1269`. This closes `QA-SEO-001`. Commit `24f381e` then added first-byte Admin `noindex, nofollow, noarchive` protection and explicit wildcard, Googlebot and Googlebot-News exclusions for `/admin` and `/api/admin/`. Deployment `dep-da7ala710e5c738ovtm0` on instance `824s7` was production-verified on 26 August 2026 with public SEO preserved, so `QA-SEO-002` is **CLOSED — PRODUCTION VERIFIED**. These are indexing controls only; Admin authentication and API authorization remain the security boundary. Search Console and GA4 validation remain external work.

## Performance and memory

The public article-list latency finding lacks a measured remediation. Article-
generation observability now provides fifteen RSS/Python-heap lifecycle markers,
and hermetic allocator diagnostics in `0052b68` supported one isolated production
experiment. Commit `b3550c0` applies `batch_size(250)` only to the projected short-
content cursor. Natural runs on 20 August 18:00 and 21 August 06:00 reduced that
phase to +3.9 MB over 4,249 records in 2.68 seconds and +1.0 MB over 4,264 records
in 2.65 seconds. The +2.45 MB two-run mean compares with a supplied pre-batch mean
of about +39.5 MB; both full jobs completed normally in 101.62 and 92.06 seconds
with zero removals and no material runtime or semantic regression. The change is a
**provisional keep**. `QA-OPS-001` remains **High Open** because recurrent OOM,
allocator/native retention and an elevated cumulative baseline are unresolved.
Standard 2 GB remains temporary headroom. The +57.7 MB visible-pool interval on
21 August is evidence for separate review, not approval for another change.

## Operations and monitoring

The Phase 4 runbooks define health, scheduler, memory, similarity and newsletter
evidence capture. `CT-QA-2026-003` is **CLOSED — FAIL-CLOSED ARTICLE LOCK
VERIFIED**: `d8943e8` returns on lock seed or atomic-acquisition error. Seven
focused tests cover the failure and normal/stale paths, while the natural 13
August 18:00 run on `qc88z` verified one acquisition and one complete execution
without scheduler or Mongo regression. No production failure was induced, and
broader release/finally ownership questions were outside this closure.

## Newsletter

Secure request-link, challenge, replay, unsubscribe/reactivation, active-recipient exclusion, rotating batches, Resend diagnostics and accepted-recipient ledgers have extensive focused coverage. Weekly Roundup live reliability and inactive-subscriber conclusions still require dated operational evidence; provider acceptance is not inbox delivery.

## Editorial workflow

Manual Review is a first-class hidden state with backend-authoritative restoration
guards. Publication-intent confirmation, responsive cards and mobile editor work
are recorded, with varying deployment evidence. Version 1 duplicate protection
remains authoritative. Editorial Similarity is advisory, scheduled-only and
shadow-only. Its numerical three-run observation-count gate is satisfied;
calibration, threshold, UI and enforcement decisions remain unapproved.

## Social publishing

Unified deterministic Facebook, Instagram and Threads preparation is covered by focused frontend/backend tests and later authenticated production evidence for the Facebook attribution path. Legacy direct Admin Facebook publishing controls were contained. No automated publishing claim is made.

## Analytics

Article-view and Most Read corrections were committed with focused regression evidence. Admin first-party analytics and Facebook attribution were implemented; repository records state functional production verification for Facebook Analytics, while GA4 remains separately environment-dependent.

## Release-readiness model

- **Code remediated:** reviewed implementation exists.
- **Test verified:** focused or complete safe suites passed.
- **Deployed:** the exact commit is evidenced live.
- **Production verified:** bounded live behaviour was observed without prohibited mutation.
- **Ready:** all closure criteria, risk-specific evidence and protected boundaries pass.

Critical security or unsafe-test findings block release regardless of unrelated green suites. Monitoring findings can permit normal operation only with explicit observation and escalation thresholds.

## Evidence required to close a finding

Every finding requires: an identified current-code state; a fixing or superseding commit where relevant; focused regression evidence; safe broad validation; explicit deployment identity for runtime changes; bounded production verification where the defect was live; and recorded residual risk. Security rotation requires external operational proof without revealing secrets.

## Related records

[Open Findings](OPEN_FINDINGS.md), [Completed Phases](COMPLETED_PHASES.md), [Test History](TEST_HISTORY.md), [Roadmap Master](../ROADMAP_MASTER.md), [Architecture Master](../ARCHITECTURE_MASTER.md), and [Production Timeline](../PRODUCTION_TIMELINE.md).

## Reconstruction status

Repository evidence through HEAD, including the 13 August scheduler-lock closure
and memory observation, is reconciled. Pending ChatGPT export,
systematic Codex-history integration, historical PDF reconciliation and other
post-HEAD production investigations can change evidence classifications later;
they are not treated as current truth here.

## Known limitations

Exact full-suite counts are unavailable for some later milestones; none are invented. Search Console, GA4 and provider state cannot be proven from Git alone. Credential rotation is supported by dated production evidence rather than Git state alone.
