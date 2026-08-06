# Cheshire Today — QA Master

> **Reconstruction status:** Evidence-backed reconciliation at repository HEAD `1601ae48be281153e5dd4af0eee0889a26835162`. The immutable 29 July baseline is retained; later code, test, deployment and production evidence are classified separately.

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
| Open or not fully production verified | 8 |
| Remediated and verified by tests at repository level | 2 |
| Remediated, deployed and production verified | 1 |

Three additional post-baseline findings are registered: documentation authority sprawl, incomplete Editorial Similarity production observation, and scheduler lock-failure continuation risk. These totals describe evidence status, not severity totals.

## Original 29 July QA baseline

The audit at `2bcdf5c` found one critical credential exposure; high-risk non-hermetic tests, compilation failures and broad credentialed CORS; medium accessibility, metadata, latency and memory findings; and low documentation/maintenance debt. It also recorded healthy public routes, crawler responses, focused suites and frontend build. Its release recommendation applied to that baseline and is not silently rewritten.

## Finding reconciliation summary

The authoritative row-by-row reconciliation is [Open Findings](OPEN_FINDINGS.md). Original identifiers appear exactly once there, including repository-level closures. A finding closes only when its stated closure criteria are satisfied; remediation, tests, deployment and production verification remain separate fields.

## Security

Current tracked-tree credential scans and loopback-only external test boundaries are covered by `tests/test_committed_admin_credential_hygiene.py` and `tests/test_external_http_test_safety.py`. Production credential rotation/revocation is not established by repository evidence, so `QA-SEC-001` remains open. `backend/server.py` still uses `allow_origins=["*"]` with credentials, keeping `QA-SEC-002` open.

## Test safety and hermeticity

Commits `b804cdd` and `603e11b` removed literals and made four legacy HTTP suites refuse external targets and redirects. That closes the defined repository mutation-boundary defect, while broader suite organisation and warning cleanup remain maintenance work. Safe commands must never point mutation-capable tests at production.

## Compilation and build health

Commit `7c2ac62` repaired the three tracked Python syntax defects. Repository-wide `python3 -m compileall -q backend tests` passes at current HEAD. Multiple later frontend production builds are recorded as passing, but build success alone does not verify runtime providers or production behaviour.

## Accessibility

Admin mobile Safari received substantial responsive and touch hardening with real-iPhone verification under Safari Page Zoom 100%. The original public desktop header-search semantics, label and no-results concerns have no evidenced fixing commit and remain open.

## SEO and metadata

Rendered public metadata reconciliation was implemented in `6bfe896` and `1e5c2da`, deployed, and recorded as production-verified in `7ca1269`. This closes `QA-SEO-001`. Admin homepage-metadata leakage was corrected, but the original first-byte server-level Admin `noindex` and Googlebot robots alignment requirement is not evidenced as complete; `QA-SEO-002` remains open. Search Console and GA4 validation remain external work.

## Performance and memory

The public article-list latency finding lacks a measured remediation. Memory markers added by `42736f9` improve diagnosis but do not prove Render OOM stability or reduce peak memory. Duplicate-cleanup reads and newsletter materialisation remain evidence-led monitoring priorities.

## Operations and monitoring

The Phase 4 runbooks define health, scheduler, memory, similarity and newsletter evidence capture. Current scheduler code is explicitly guarded and locked, but lock-acquisition exceptions warn and continue. Production investigation must precede changes.

## Newsletter

Secure request-link, challenge, replay, unsubscribe/reactivation, active-recipient exclusion, rotating batches, Resend diagnostics and accepted-recipient ledgers have extensive focused coverage. Weekly Roundup live reliability and inactive-subscriber conclusions still require dated operational evidence; provider acceptance is not inbox delivery.

## Editorial workflow

Manual Review is a first-class hidden state with backend-authoritative restoration guards. Publication-intent confirmation, responsive cards and mobile editor work are recorded, with varying deployment evidence. Version 1 duplicate protection remains authoritative. Editorial Similarity is advisory, scheduled-only and awaiting multi-run observation.

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

Repository evidence through HEAD is reconciled. Pending ChatGPT export, systematic Codex-history integration, historical PDF reconciliation and post-HEAD production investigations can change evidence classifications later; they are not treated as current truth here.

## Known limitations

Exact full-suite counts are unavailable for some later milestones; none are invented. Render, Search Console, GA4, provider and credential-rotation state cannot be proven from Git alone.
