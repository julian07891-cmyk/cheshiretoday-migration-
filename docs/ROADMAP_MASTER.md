# Cheshire Today — Roadmap Master

> **Reconstruction status:** Evidence-backed roadmap at repository HEAD `49e5fe49cc35e0ca020e8520db6365d356760060`. It includes the reconciled 7–8 August duplicate-cleanup memory evidence but not other unreconciled post-HEAD claims.

## Document purpose

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

**Next — Final documentation review.** Phases 1–7.3, authority synchronisation and
the archive privacy/preservation decision are complete locally. The documentation
commit/push remains blocked pending a successful final review and explicit approval.
Operationally, Editorial Similarity remains in passive observation and Version 1
remains authoritative.

## Immediate priorities

| Status | Priority | Work | Evidence/gate |
|---|---|---|---|
| Next | P0 | Close `QA-SEC-001` operational credential exposure | Dated rotation/revocation and old-access failure evidence without revealing secrets |
| Next | P0 | Restrict credentialed wildcard CORS (`QA-SEC-002`) | Reviewed allow-list, positive/negative tests, deploy and live preflight |
| Monitoring | P0 | Broader Render memory stability after duplicate-cleanup mitigation | Immediate simultaneous-list risk verified as mitigated across three normal runs; continue import/newsletter high-water and restart observation |
| Completed | P1 | Synchronise documentation authority | Master, state, source, QA and roadmap records aligned after local completion of Phases 1–7.3 |
| Completed | P1 | Archive privacy/preservation decision | Exact archive retained locally and excluded; privacy-safe repository derivative prepared |
| Next | P1 | Final documentation review | Repeat the complete read-only gate after synchronisation and archive decision |
| Blocked | P1 | Documentation commit and push | Requires successful final review and explicit approval |

Security and production stability precede feature expansion.

## Near-term priorities

| Status | Work | Scope and gate |
|---|---|---|
| Next | Public search accessibility | Semantics, label, keyboard/no-results tests and live desktop verification |
| Next | Admin first-byte noindex/robots alignment | Server/crawler contract, tests and non-authenticated live verification |
| Monitoring | Weekly Roundup QA | Normal Sunday batch evidence, provider diagnostics, ledger/cursor reconciliation; no test send by default |
| Monitoring | Inactive-subscriber evidence gathering | Provider rejection plus accepted-recipient history; no bulk deactivation from engagement absence |
| Next | Legacy/non-hermetic suite organisation | Preserve loopback refusal; document safe default; separate read-only smoke tests if justified |
| Next | Compilation/warning maintenance | Lifecycle, multipart/gzip, Browserslist and backup artefacts as separate low-risk changes |
| Monitoring | Public article-list performance | Current TTFB and Mongo plan/index evidence before optimisation |
| Next | `QA-DOC-001` Threads/operator-documentation consistency | Reconcile current implementation and operator wording without rewriting the dated QA baseline |
| Next | `CT-QA-2026-003` scheduler lock-acquisition review | Decide fail-closed ownership policy, add focused tests and preserve normal scheduler availability safeguards |

## Medium-term priorities

| Status | Work | Scope and gate |
|---|---|---|
| Monitoring | GA4 validation | Confirm configured collection/consent/reporting separately from first-party analytics |
| Monitoring | Search Console/Google News/Discover | Representative sampling; do not request indexing merely for QA |
| Next | Commercial SEO and affiliate guides | Quality-first authority pages, current inventory and crawler/index evidence |
| Next | Sponsor readiness | Placement QA, advertiser workflow, checkout/webhook and reporting checks before campaigns |
| Next | Server-side homepage crawl improvements | Preserve current crawler/browser metadata and public editorial allocation |
| Next | Dynamic affiliate inventory | Evidence-backed provider data model and Admin workflow; no unsupported revenue claims |
| Next | Sponsor impression bot filtering | Define trustworthy event policy and regression baseline before changing counters |

## Long-term priorities

| Status | Work | Scope and gate |
|---|---|---|
| Deferred | Version 2 branding | Coordinated professional rollout only when audience/business value justifies it |
| Deferred | Editorial Similarity UI or Similar Stories | Numerical observation-count gate is satisfied; calibration, product review and separately approved thresholds are still required |
| Deferred | Broader Admin navigation redesign | Separate from resolved mobile editor/card containment |
| Deferred | Database/index optimisation programme | Requires measured production evidence per query/workload |

## Monitoring-only work

- Editorial Similarity pool, shortlist, comparison, band, reason and provenance
  evidence after satisfaction of the numerical three-run gate; continued monitoring
  does not authorise calibration, UI or enforcement.
- All twelve article-generation memory phases, scheduler duration and post-run stability.
- Residual full-read, visible-pool and high-start memory behaviour after `49e5fe4`;
  the lifecycle fix does not close broader Render memory risk.
- Weekly Roundup batches, accepted-recipient ledger, provider outcome and cursor progress.
- First-party analytics subsection latency and scanner/bot noise.
- Sitemap, crawler metadata and representative Search Console state.
- Sponsored/affiliate event quality before revenue interpretation.

Monitoring does not authorise imports, sends, restarts, indexing requests or database repairs.

## Deferred work

- Version 2 brand refresh.
- Sticky editor action toolbar, word count/reading time and general unsaved-change warnings.
- New Save Draft or Publish endpoint.
- Similarity thresholds, automatic routing, merge/archive/delete actions or Admin panel.
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
- First-party article-view and Most Read correctness repairs.
- Admin read-only analytics and Facebook attribution foundation.
- Rendered metadata reconciliation with production verification.
- Core Admin mobile Safari/editor containment and accessible close control.
- Editorial Similarity Phase 2A pure scorer and Phase 2B scheduled shadow integration.
- Phases 1–7.3 documentation inventory, preservation, history, architecture,
  operations, QA, roadmap, Project Master and concise Project State reconstruction
  completed locally, including privacy-safe archive creation and clean-checkout-safe
  archive-link correction.

Completion refers to the defined item; residual findings remain in [Open Findings](QA/OPEN_FINDINGS.md).

## Dependencies and gates

1. Security findings precede discretionary deployment.
2. Memory evidence precedes scheduler/import optimisation.
3. The numerical three-run similarity gate is satisfied; calibration, UI and
   enforcement still require separate reviewed evidence and approval.
4. Provider/ledger evidence precedes newsletter recipient-state changes.
5. Query measurements precede indexes or caching.
6. Tests precede deployment; deployed commit evidence precedes production verification.
7. Search Console/GA4 access is required for their platform-specific conclusions.
8. Repository-wide documentation authority transition waits for final review, an
   explicit archive privacy/preservation decision and the approved commit/push.

## Current risks

- Broad credentialed CORS.
- Unverified credential rotation/history exposure.
- Render memory peaks from remaining full reads, visible-pool work, allocator
  high-water behaviour or newsletter materialisation despite the operationally
  verified duplicate-cleanup lifecycle mitigation.
- Scheduler ownership degradation if lock acquisition errors continue fail-open.
- Public API latency.
- Newsletter provider/recipient conclusions without reconciled evidence.
- Documentation/history gaps affecting operational decisions.
- Premature interpretation of similarity shadow scores.

## Documentation reconstruction roadmap

- **Completed locally:** Phases 1–7.3, including inventory, archive/source register,
  history, decisions, production/editorial records, architecture, operations, QA,
  roadmap, Project Master and concise Project State.
- **Completed locally:** Authority synchronisation across the rebuilt set.
- **Completed locally:** Archive privacy/preservation decision; exact archive
  excluded and privacy-safe repository copy prepared.
- **Next:** Final read-only documentation review after synchronisation and archive decision.
- **Blocked:** Documentation commit and push until successful final review and approval.
- **Blocked:** ChatGPT export reconciliation until export is received.
- **Next:** Systematic Codex-history integration when records are collected and source-ranked.
- **Deferred:** Historical PDF reconciliation pending source availability and prioritisation.
- **Monitoring:** Post-HEAD production evidence pending preservation and reconciliation.

## Related records

[QA Master](QA/QA_MASTER.md), [Open Findings](QA/OPEN_FINDINGS.md), [Completed Phases](QA/COMPLETED_PHASES.md), [Test History](QA/TEST_HISTORY.md), [Architecture Master](ARCHITECTURE_MASTER.md), [Production Timeline](PRODUCTION_TIMELINE.md), and [Decision Register](DECISION_REGISTER.md).

## Reconstruction status

Current repository evidence is represented. Pending ChatGPT export, Codex history, historical PDFs and latest post-HEAD production investigations remain unreconciled and cannot silently reprioritise this roadmap.

## Known limitations

Roadmap priority is evidence-based but still requires product/owner approval. It does not assign people, dates or budgets not present in repository evidence, and it does not claim external platform access.
