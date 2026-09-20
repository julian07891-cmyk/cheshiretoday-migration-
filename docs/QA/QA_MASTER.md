# Cheshire Today — QA Master

> **Reconstruction status:** Evidence-backed reconciliation at repository HEAD `03a6abbd5133de969275477488ea49bb34242ee0`. The immutable 29 July baseline is retained; later code, test, deployment and production evidence are classified separately.

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
| Open or not fully production verified | 3 |
| Remediated and verified by tests at repository level | 2 |
| Remediated, deployed and production verified | 6 |

Six additional post-baseline findings are registered: documentation authority
sprawl, Editorial Similarity calibration/product-decision evidence after completion
of the numerical observation-count gate, the now-closed scheduler lock-failure
continuation risk, the distinct cross-source duplicate-identity finding
(`CT-QA-2026-004`), the High RSS-preview/imported-body-quality defect with partial
natural acceptance, and the now-closed newsletter logging privacy defect. These
totals describe evidence status, not severity totals.

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

Rendered public metadata reconciliation was implemented in `6bfe896` and `1e5c2da`, deployed, and recorded as production-verified in `7ca1269`. This closes `QA-SEO-001`. Commit `24f381e` then added first-byte Admin `noindex, nofollow, noarchive` protection and explicit wildcard, Googlebot and Googlebot-News exclusions for `/admin` and `/api/admin/`. Deployment `dep-da7ala710e5c738ovtm0` on instance `824s7` was production-verified on 26 August 2026 with public SEO preserved, so `QA-SEO-002` is **CLOSED — PRODUCTION VERIFIED**. These are indexing controls only; Admin authentication and API authorization remain the security boundary.

A representative Search Console canonical audit on 7 September 2026 classified
the 82-example **Alternate page with proper canonical tag** report as **MOSTLY
HISTORICAL ALTERNATE URLS — CURRENT IMPLEMENTATION HEALTHY**. Sampled historical
UUIDs resolved to the same current Mongo articles, intentional query
consolidation was coherent, and current canonicals, noindex boundaries,
sitemaps and internal links were healthy. This does not claim all 82 examples
were inspected or that Google indexing is solved. **DO NOT PRESS VALIDATE FIX
NOW**; allow natural recrawl and reassess after a later report update or a newly
crawled current mismatch. GA4 validation remains external work.

## Performance and memory

`QA-PERF-001` is narrowed to **MATERIAL IMPROVEMENT — OPTIMISATION VERIFIED**.
After a five-request diagnostic baseline on `15695cb` identified Motor/database
materialisation as dominant, read-only sufficiency replay found deepest contributing
Local/UK positions 42/58 and selected 100/100 caps with exact ordered output and
operational headroom. Commit `70057e1` skips unused homepage `count_documents()`
and applies those caps only to the exact public 80-item homepage list shape. Its
five-request production comparison reduced median handler 1,081.639→708.314 ms
(-34.5%), TTFB 1,868.333→1,544.086 ms (-17.4%) and total
1,897.497→1,587.383 ms (-16.3%), while all responses remained HTTP 200 with 79
articles, stable bytes, unchanged 33 force candidates, 80/79 pre-dedupe/final and
fallback 0/5. Five samples do not prove broad statistical certainty. The remaining
839.327 ms median TTFB-minus-handler residual is unmeasured and becomes a separate
read-only investigation; no subsystem cause or further query change is inferred.

Article-generation observability now provides fifteen RSS/Python-heap lifecycle markers,
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

Secure request-link, challenge, replay, unsubscribe/reactivation, active-recipient exclusion, rotating batches, Resend diagnostics and accepted-recipient ledgers have extensive focused coverage. Weekly Roundup slot-aware idempotence is **NATURAL VERIFICATION COMPLETE**: on 6 September 2026, all four natural Sunday slots selected 1,000 recipients and recorded 1,000/1,000 successful application/provider-path acceptance, with distinct slot identities, cursor progression 996→1996→2996→3996, no observed `E11000` conflict and the slot-aware unique index confirmed at subsequent startup. This closes the idempotence reliability-validation loop, not delivery, bounce, engagement, inactive-subscriber, growth or commercial conclusions; provider acceptance is not inbox delivery.

Newsletter Funnel V1 is **PRODUCTION ACCEPTED**. Commit `66fde10` added
backend-authoritative, fail-open, anonymous daily signup outcome aggregates and
matching authenticated Admin reporting without changing subscriber semantics.
Focused backend (69), dedicated Admin analytics (15), frontend signup/service
contract (9), expanded frontend consent/provider/trackEvent (17), and broader
relevant regression (294) tests passed; the frontend production build,
`compileall` and `git diff --check` also passed. Deployment
`dep-dan3beojo6nc7395spm0` became live on instance `fkdbq` at 08:14:30 BST on
19 September. One controlled authorised signup produced HTTP 200/`created`, the
exact uncontended `newsletter_landing` aggregate `1/1/0/0/0`, and matching Admin
reporting with 100.0% created conversion. The aggregate stores no subscriber PII
and expires after exactly 13 calendar months; no inbox-delivery or distributed
exact-once claim is made. The separately confirmed pre-existing newsletter
logging defect did not invalidate Funnel V1 and is now `CT-QA-2026-006`
**CLOSED — IMPLEMENTED, TESTED, DEPLOYED AND PRODUCTION-VERIFIED**.

Commit `03a6abb` bounded subscriber creation, welcome/subscribe, shared SMTP,
scheduled invalid-address, Admin test-send and provider diagnostics so the
changed paths no longer log subscriber/recipient or SMTP-user identity,
recipient-derived data, raw provider bodies or arbitrary exception text. It
preserves subscriber, delivery, provider, digest, scheduler, Funnel, analytics
and frontend contracts. Focused suites passed 47/47; the relevant bounded
regression set passed 1,145 with 12 skipped and was not the complete repository
suite. Three initial Material test-evidence weaknesses were corrected before
complete unstaged and staged reviews were approved with no remaining finding.
Auto-Deploy `dep-daneoh6q1p3s73cdmf9g` ran exact SHA `03a6abb` on Standard
instance `zpcmz`; build/startup and bounded public/log checks passed. Every
failure branch was not naturally exercised, historical logs were not altered,
and no legal/privacy-compliance claim is made.

## Editorial workflow

Manual Review is a first-class hidden state with backend-authoritative restoration
guards. Publication-intent confirmation, responsive cards and mobile editor work
are recorded, with varying deployment evidence. Version 1 duplicate protection
remains authoritative. Editorial Similarity is advisory, scheduled-only and
shadow-only. Its numerical three-run observation-count gate is satisfied;
calibration, threshold, UI and enforcement decisions remain unapproved.

`CT-QA-2026-005` records a confirmed High imported-body-quality defect, not an
AI-authored-content defect. A continuation-ended Guardian RSS preview became
public, and tag deletion destroyed HTML block boundaries; five current records
were found in a bounded audit, not a lifetime census. Commit `bbc526c` preserves
block boundaries, classifies incompleteness before sanitisation and prevents
`manual_review_without_ai` from bypassing hidden Manual Review. Focused and
related suites passed (44; 130 with 12 skipped; 104), with compilation/diff and
review gates approved. Deployment `dep-damij1btqb8s73fvesp0` was healthy, and
the natural 18 September 18:00 run verified one incomplete Guardian candidate
routed to Manual Review plus bounded clean structure/marker evidence. Overall
status is **IMPORT ARTICLE QUALITY FIX NATURAL ACCEPTANCE PARTIAL**: the complete-
replacement path is not naturally exercised, five historical records remain
unrepaired, and `/api/import-real-news` remains a separate unchanged follow-up.

## Social publishing

Unified deterministic Facebook, Instagram and Threads preparation is covered by focused frontend/backend tests and later authenticated production evidence for the Facebook attribution path. Legacy direct Admin Facebook publishing controls were contained. No automated publishing claim is made.

## Analytics

Article-view and Most Read corrections were committed with focused regression
evidence. Admin first-party analytics and Facebook attribution were implemented.
Commit `be0182b` added the bounded third-party consent layer; 4 focused suites/17
tests, 10 regression suites/118 tests and the production build passed. Deployment
`dep-dam3mb3ncjis73cit8mg` is verified live on instance `w8frn`, and observable
consent behaviour passed without a confirmed defect. Event-level production
network acceptance remains **INCONCLUSIVE / TOOLING UNAVAILABLE**: exact consent
storage, provider event payloads/counts, SPA cardinality, transmitted URL
normalisation, event-level sensitive-route exclusion and immediate withdrawal
suppression still require a genuinely isolated request-inspection context. This
external evidence item does not reopen implementation engineering or block
unrelated analytics/growth work absent new defect evidence.

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
