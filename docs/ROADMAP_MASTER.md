# Cheshire Today — Roadmap Master

> **Reconstruction status:** Evidence-backed roadmap at repository HEAD `03a6abbd5133de969275477488ea49bb34242ee0`, including production-accepted Newsletter Funnel V1, production-verified newsletter logging hardening and the RSS-preview protection's partial natural-acceptance boundary.

## Document purpose

Direct newsletter unsubscribe is **DESIGN APPROVED — IMPLEMENTATION PENDING**
under [CT-DEC-021](DECISION_REGISTER.md#ct-dec-021--direct-newsletter-unsubscribe-with-secure-recovery-retained).
Local prerequisites now specify a strict signed direct class, 90-day lifetime,
version-guarded mutation and fail-closed missing identities; preserve signup,
preferences and recovery. Live identity coverage, native logging and delivered-header
acceptance remain gates. The separate Apple Mail observation is not closed by
this design; current QA totals are unchanged.

Translate verified gaps and protected operating gates into prioritised work without promoting speculative features above security or production stability.

## Authority and evidence

Current code/configuration, [Open Findings](QA/OPEN_FINDINGS.md), [QA Master](QA/QA_MASTER.md), [Architecture Master](ARCHITECTURE_MASTER.md), [Decision Register](DECISION_REGISTER.md), Git history and repository-preserved production evidence control this roadmap. See [Source Register](HISTORY/SOURCE_REGISTER.md).

## How to use this document

Choose the highest eligible item whose dependencies are met. Each implementation remains a separate reviewed task with focused validation and deployment approval.

## Status model

- **Active:** currently being executed with an approved boundary.
- **Next:** highest justified work after active gates.
- **Monitoring:** evidence collection without speculative change.
- **Blocked:** cannot proceed safely until named evidence/dependency exists.
- **Deferred:** deliberately postponed.
- **Completed:** implementation and its defined evidence gate are complete.
- **Rejected:** considered and deliberately not pursued.
- **Superseded:** replaced by a later decision or architecture.

## Current milestone

**Active — Production hardening and evidence reconciliation.** Version 1 and the
documentation reconstruction are committed. Editorial Similarity remains passive,
Version 1 remains authoritative, and cumulative process memory remains a monitored
reliability risk.

## Immediate priorities

| Status | Priority | Work | Evidence/gate |
|---|---|---|---|
| Completed | P0 | Restrict credentialed wildcard CORS (`QA-SEC-002`) | Commit `b497635`, eight focused tests, deployment `dep-d9u594oae00c73bs1lvg`, positive/negative live preflights and Admin compatibility verified 12 August 2026 |
| Monitoring | P0 | Broader Render memory stability after duplicate-cleanup mitigation | The 13 August run was +174.8 MB net; the 15 August 12:00 run was +162.1 MB with no observable material event-anchor regression. Retained growth remains material and variable; require a broader comparable window before selecting a target |
| Completed | P1 | Synchronise documentation authority | Master, state, source, QA and roadmap records aligned after local completion of Phases 1–7.3 |
| Completed | P1 | Archive privacy/preservation decision | Exact archive retained locally and excluded; privacy-safe repository derivative prepared |
| Next | P1 | Current authority reconciliation review | Review and approve the 13 August scheduler/memory evidence update before its documentation-only commit |

Security and production stability precede feature expansion.

## Near-term priorities

| Status | Work | Scope and gate |
|---|---|---|
| Completed | Public search accessibility (`QA-A11Y-001`) | Commit `dcd5cfa`, 7 focused/42 related/367 total frontend tests, production build, deployment `dep-da82j9uk1f9s73dgc1mg`, and bounded desktop/mobile production verification completed 27 August 2026 |
| Monitoring | Bounded labelled event-anchor calibration (`CT-QA-2026-004`) | Implementation, deployment and first natural run are verified. Continue natural high-specificity same-run cross-source calibration; keep Manual Review routing, historical routing and all enforcement behind a separate evidence review and approval gate |
| Completed | Weekly Roundup slot-aware idempotence verification | Commit `5559499`; four natural slots on 6 September each recorded 1,000/1,000 application/provider acceptance, distinct slot identities and cursor progression 996→1996→2996→3996 without observed `E11000`. Continue deliverability and engagement monitoring separately; acceptance is not inbox delivery |
| Completed | Generic newsletter-management entry UX (`CT-QA-2026-007`) | **IMPLEMENTED, DEPLOYED AND PRODUCTION-VERIFIED.** `e6408133`; Auto-Deploy `dep-dao287ajnfac739ab80g`, instance `cqsqq`; three generic routes and mobile checks passed. Six suites / 96 tests and build passed; live-network-capture limitation retained in QA evidence |
| Next | Apple Mail/iPhone management-email CTA compatibility | **SEPARATE — UNRESOLVED.** Blue CTA reached invalid-link state while complete fallback link worked. Precise transformation is unproven; investigate read-only before implementation. `e6408133` did not change email URL generation or close this issue |
| Deferred | Inactive-subscriber hygiene | Future work after the unsubscribe audit. Do not delete subscribers merely because no open was recorded. First analyse engagement history, account age, open/click evidence and tracking limitations, preview the affected population and define a safe deactivate/delete policy before any destructive action |
| Next | Legacy/non-hermetic suite organisation | Preserve loopback refusal; document safe default; separate read-only smoke tests if justified |
| Next | Compilation/warning maintenance | Lifecycle, multipart/gzip, Browserslist and backup artefacts as separate low-risk changes |
| Completed | Homepage database/materialisation remediation (`QA-PERF-001`) | Commit `70057e1` skips the unused exact-homepage count and applies evidence-supported 100/100 Local/UK caps; five-request production comparison reduced median handler 34.5%, TTFB 17.4% and total 16.3% with observed response semantics preserved |
| Next | Post-handler/client TTFB residual measurement | Median post-change TTFB-minus-handler is 839.327 ms; measure its composition read-only before attributing framework, encoding, compression, proxy/runtime, network or other work or proposing further optimisation |
| Next | `QA-DOC-001` Threads/operator-documentation consistency | Reconcile current implementation and operator wording without rewriting the dated QA baseline |
| Monitoring | RSS-preview complete-replacement evidence (`CT-QA-2026-005`) | Core incomplete-preview routing and bounded HTML-boundary behaviour are naturally verified after `bbc526c`; observe a natural continuation-ended candidate receiving a genuinely distinct complete public replacement. Do not manufacture a candidate or block unrelated work |
| Next | Historical Guardian article repair | Separately review and repair the five bounded pre-deployment affected records; do not treat deployment of future-import protection as historical cleanup |
| Next | `/api/import-real-news` completeness review | **SEPARATE FOLLOW-UP RISK — UNCHANGED.** Audit/design independently; do not trigger the endpoint merely to manufacture evidence |
| Completed | Newsletter Funnel V1 | Commit `66fde10`, focused/related tests and build checks, deployment `dep-dan3beojo6nc7395spm0`, one controlled authorised created signup, exact anonymous aggregate and matching Admin reporting completed the defined acceptance gate on 19 September 2026 |
| Completed | Subscriber-log privacy remediation (`CT-QA-2026-006`) | Commit `03a6abb`; 47 focused passes; 1,145 relevant regression passes with 12 skipped; complete reviews approved; Auto-Deploy `dep-daneoh6q1p3s73cdmf9g` on `zpcmz`; healthy bounded production verification. Historical logs unchanged, every failure branch was not naturally exercised and no compliance claim is made |

## Medium-term priorities

| Status | Work | Scope and gate |
|---|---|---|
| Monitoring | Third-party analytics event-level verification | Consent implementation, deployment and observable behaviour are verified without a confirmed defect. When suitable isolated DevTools/Playwright/CDP request inspection is available, verify exact consent storage, provider page-view payload/cardinality, URL normalisation, sensitive-route exclusion and withdrawal suppression. This external-evidence item does not block unrelated analytics/growth work |
| Monitoring | Provider reporting validation | Reconcile GA4, Plausible and PostHog receipt/reporting separately from browser transmission and first-party analytics |
| Next | Broader measurement maturity | Treat newsletter conversion, campaign-attribution quality and commercial conversion measurement as separate evidence-led workstreams |
| Monitoring | Search Console/Google News/Discover | Canonical audit classified the 82-example alternate-page report as mostly historical with current implementation healthy; do not press Validate Fix now, allow natural recrawl, and recheck after a later report update or newly crawled current mismatch. Continue separate Google News/Discover sampling |
| Next | Commercial SEO and affiliate guides | Quality-first authority pages, current inventory and crawler/index evidence |
| Next | Sponsor readiness | Placement QA, advertiser workflow, checkout/webhook and reporting checks before campaigns |
| Next | Server-side homepage crawl improvements | Preserve current crawler/browser metadata and public editorial allocation |
| Next | Dynamic affiliate inventory | Evidence-backed provider data model and Admin workflow; no unsupported revenue claims |
| Next | Sponsor impression bot filtering | Define trustworthy event policy and regression baseline before changing counters |

## Long-term priorities

| Status | Work | Scope and gate |
|---|---|---|
| Deferred | Version 2 branding | Coordinated professional rollout only when audience/business value justifies it |
| Deferred | Editorial Similarity UI or Similar Stories | Numerical observation-count gate and bounded shadow event-anchor implementation are complete, but routing precision is not proven; labelled natural calibration and separate product approval remain required |
| Deferred | Broader Admin navigation redesign | Separate from resolved mobile editor/card containment |
| Deferred | Database/index optimisation programme | Requires measured production evidence per query/workload |

## Monitoring-only work

- Editorial Similarity pool, shortlist, comparison, band, reason and provenance
  evidence after satisfaction of the numerical three-run gate. The completed
  27-pair calibration and verified `phase2a_event_anchors_v1` natural execution do
  not authorise routing, UI or enforcement.
- All thirteen article-generation memory phases, scheduler duration and post-run stability.
- First duplicate Stage 1, visible-pool, short-content scan and high-start memory
  behaviour after the staged cleanup optimisations. `1811430` was safe but its
  first natural comparison (+28.5 MB versus +26.0 MB) did not show material RSS improvement.
- Weekly Roundup delivery/bounce, accepted-recipient ledger and engagement
  monitoring after completed slot-aware idempotence verification; provider
  acceptance remains distinct from inbox delivery.
- First-party analytics subsection latency and scanner/bot noise.
- Sitemap, crawler metadata and representative Search Console state.
- Sponsored/affiliate event quality before revenue interpretation.

Monitoring does not authorise imports, sends, restarts, indexing requests or database repairs.

## Deferred work

- Version 2 brand refresh.
- Sticky editor action toolbar, word count/reading time and general unsaved-change warnings.
- New Save Draft or Publish endpoint.
- Similarity thresholds, automatic routing, merge/archive/delete actions or Admin panel;
  no score, band or tested composite is currently approved.
- Broad Admin navigation and Archive-row redesign.

## Rejected or superseded work

- **Rejected:** automatic OpenAI publishing; OpenAI remains Admin-only and draft/review-only.
- **Rejected:** Editorial Similarity replacing Version 1 deterministic duplicate prevention.
- **Rejected:** disabling pinch zoom or JavaScript Safari zoom resets.
- **Rejected:** manual imports solely to manufacture similarity evidence.
- **Superseded:** ordinary article hard delete as lifecycle policy by archive-first handling.
- **Superseded:** legacy direct Facebook Admin posting controls by Social Publishing preparation.
- **Superseded:** old multiple daily newsletter digest schedule by Daily Brief and Sunday batched Weekly Roundup.

## Completed roadmap items

- Version 1 duplicate and archive safeguards.
- Manual Review hidden editorial state and backend-authoritative restoration.
- Secure newsletter management phases and accepted-recipient accounting.
- Newsletter Funnel V1 backend-authoritative anonymous daily aggregates and
  authenticated Admin reporting, production accepted through one controlled
  authorised signup on 19 September 2026.
- `CT-QA-2026-006` newsletter logging privacy hardening: commit `03a6abb`,
  corrected focused/regression evidence, approved complete reviews, automatic
  deployment `dep-daneoh6q1p3s73cdmf9g` and bounded production verification.
- First-party article-view and Most Read correctness repairs.
- Admin read-only analytics and Facebook attribution foundation.
- Rendered metadata reconciliation with production verification.
- `QA-SEC-001` production Admin-password rotation, pre-rotation session
  invalidation and historical-password rejection, closing the original Critical
  finding while retaining the revoked credential as reachable Git history.
- Core Admin mobile Safari/editor containment and accessible close control.
- Editorial Similarity Phase 2A pure scorer and Phase 2B scheduled shadow integration.
- Bounded deterministic event-anchor shadow evidence: `5e8f0ef`, healthy deployment
  `dep-da01o93ncjis738c7m8g` and first natural 15 August run verified execution,
  compact logging and unchanged publication behaviour; calibration remains open.
- `CT-QA-2026-003` fail-closed article lock: `d8943e8`, seven focused tests and
  the single-execution 13 August 18:00 natural run closed the Medium finding.
- Phases 1–7.3 documentation inventory, preservation, history, architecture,
  operations, QA, roadmap, Project Master and concise Project State reconstruction
  completed locally, including privacy-safe archive creation and clean-checkout-safe
  archive-link correction.

Completion refers to the defined item; residual findings remain in [Open Findings](QA/OPEN_FINDINGS.md).

## Dependencies and gates

1. Security findings precede discretionary deployment.
2. Memory evidence precedes scheduler/import optimisation.
3. The numerical three-run gate and bounded event-anchor shadow implementation are
   complete; labelled calibration, routing, UI and enforcement still require
   separate reviewed evidence and approval.
4. Provider/ledger evidence precedes newsletter recipient-state changes.
5. Query measurements precede indexes or caching.
6. Tests precede deployment; deployed commit evidence precedes production verification.
7. Search Console/GA4 access is required for their platform-specific conclusions.
8. Repository-wide documentation authority transition waits for final review, an
   explicit archive privacy/preservation decision and the approved commit/push.

## Current risks

- Render memory peaks from first duplicate Stage 1, visible-pool and feed work,
  short-content cursor/decoded-string behaviour, allocator retention or newsletter
  materialisation despite the structurally successful cleanup mitigations.
- Public API latency.
- Newsletter provider/recipient conclusions without reconciled evidence.
- Five historical Guardian records remain affected by the pre-`bbc526c` preview/body defect; complete-replacement natural evidence and `/api/import-real-news` coverage remain separate follow-ups.
- Documentation/history gaps affecting operational decisions.
- Premature interpretation of similarity shadow scores.
- Cross-source and localised same-event reports whose differing URLs, titles,
  images or formats evade deterministic identity checks; archived-record reimport
  was not reproduced in the 10–14 August audit.

## Documentation reconstruction roadmap

- **Completed locally:** Phases 1–7.3, including inventory, archive/source register,
  history, decisions, production/editorial records, architecture, operations, QA,
  roadmap, Project Master and concise Project State.
- **Completed locally:** Authority synchronisation across the rebuilt set.
- **Completed locally:** Archive privacy/preservation decision; exact archive
  excluded and privacy-safe repository copy prepared.
- **Next:** Final read-only review and approved commit of the 13 August authority reconciliation.
- **Blocked:** ChatGPT export reconciliation until export is received.
- **Next:** Systematic Codex-history integration when records are collected and source-ranked.
- **Deferred:** Historical PDF reconciliation pending source availability and prioritisation.
- **Monitoring:** Production evidence after the 13 August 18:00 run pending preservation and reconciliation.

## Related records

[QA Master](QA/QA_MASTER.md), [Open Findings](QA/OPEN_FINDINGS.md), [Completed Phases](QA/COMPLETED_PHASES.md), [Test History](QA/TEST_HISTORY.md), [Architecture Master](ARCHITECTURE_MASTER.md), [Production Timeline](PRODUCTION_TIMELINE.md), and [Decision Register](DECISION_REGISTER.md).

## Reconstruction status

Current repository evidence is represented. Pending ChatGPT export, Codex history, historical PDFs and latest post-HEAD production investigations remain unreconciled and cannot silently reprioritise this roadmap.

## Known limitations

Roadmap priority is evidence-based but still requires product/owner approval. It does not assign people, dates or budgets not present in repository evidence, and it does not claim external platform access.
