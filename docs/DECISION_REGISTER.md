# Cheshire Today — Decision Register

> **Reconstruction status:** evidence-backed decisions reconciled through
> `8ed19846ccf9242b646ea38440d71e1f85f59141`, 26 September 2026. Pending ChatGPT, Codex, PDF and
> post-HEAD evidence may add context but must not silently rewrite these entries.

## Document purpose

This register preserves major decisions, their alternatives and outcomes. Status
describes the decision at current repository HEAD, not an unverified live claim.

## How to use this document

- Locate a decision by ID and follow its sources before changing the contract.
- See the [Engineering History](HISTORY/ENGINEERING_HISTORY_MASTER.md) for sequence,
  the [Production Timeline](PRODUCTION_TIMELINE.md) for operations and the
  [Editorial Evolution](EDITORIAL_EVOLUTION.md) for policy context.
- Apply the evidence hierarchy in the [Source Register](HISTORY/SOURCE_REGISTER.md).

## Decision entries

### CT-DEC-001 — Repository operational documentation is the source of truth

- **ID:** CT-DEC-001
- **Date or date range:** 12–16 July 2026; preservation system approved August 2026.
- **Status:** Active.
- **Area:** Documentation governance.
- **Problem:** state was distributed across uploaded files, prompts and duplicated
  handovers, making stale advice easy to mistake for current truth.
- **Evidence:** consolidated state reconciliation found one fuller chronology and
  several subsets/duplicates.
- **Alternatives considered:** continue using chat handovers; use the February PDF;
  maintain multiple parallel state files.
- **Decision:** repository records govern long-term project knowledge;
  `PROJECT_STATE.md` remains operational authority until its safe Phase 7 replacement.
- **Rationale:** repository evidence is reviewable, diffable and tied to commits.
- **Implementation:** state moved under `docs/`, consolidated, then preserved
  byte-for-byte before restructuring.
- **Result:** one explicit operational source exists, although it still needs safe
  separation from history.
- **Follow-up:** complete master records and only then reduce `PROJECT_STATE.md`.
- **Sources:** [preserved state](ARCHIVE/PROJECT_STATE_REDACTED_2026-08-06.md), sections
  “Source reconciliation” and “Repository-backed state migration”;
  [Source Register](HISTORY/SOURCE_REGISTER.md); Git `751915b`, `b54e66d`.

### CT-DEC-002 — QA-first, smallest-safe-change workflow

- **ID:** CT-DEC-002
- **Date or date range:** established during 2026; codified July 2026.
- **Status:** Active.
- **Area:** Engineering governance.
- **Problem:** broad changes and production-coupled tests caused regressions and
  unsafe verification pressure.
- **Evidence:** repeated rollbacks, the 29 July test-safety findings and successful
  narrow fixes with focused regressions.
- **Alternatives considered:** broad rewrites; unqualified production smoke tests;
  large multi-system releases.
- **Decision:** verify state first, make one bounded change, run focused then related
  tests, inspect the diff and require explicit production authority.
- **Rationale:** minimises editorial, subscriber, scheduler and production risk.
- **Implementation:** repository workflow instructions and task-specific regression
  suites.
- **Result:** later security, metadata, mobile and Editorial Similarity work shipped
  as isolated phases.
- **Follow-up:** preserve this model in the future project master and QA records.
- **Sources:** [QA report](QA/QA_REPORT_2026-07-29.md), “QA methodology”;
  [July log](HISTORY/ENGINEERING_LOG_JULY_2026.md), “QA methodology”; `AGENTS.md`.

### CT-DEC-003 — Hybrid RSS plus Perplexity publishing model

- **ID:** CT-DEC-003
- **Date or date range:** February–March 2026, refined through July.
- **Status:** Active.
- **Area:** Article pipeline.
- **Problem:** raw RSS was too thin, while unconstrained AI generation could stall or
  invent facts.
- **Evidence:** thin content, import stalls and later successful bounded rewrites.
- **Alternatives considered:** RSS-only summaries; Perplexity-first generation
  without source leads; unrestricted provider fallback.
- **Decision:** use RSS/source records as the lead, Perplexity for bounded research
  and rewriting, and deterministic gates before publication.
- **Rationale:** combines source identity and freshness with fuller copy while
  retaining deterministic safety.
- **Implementation:** long-form pipeline, timeouts, content floor, source URL and
  duplicate checks.
- **Result:** the scheduled hybrid importer became the production article path.
- **Follow-up:** continue observing quality; never infer provider output is verified
  merely because prose is fluent.
- **Sources:** preserved state, March import-pipeline sections; Git `295041e`,
  `000fb94`, `bd762fc`, `5a892be`, `53d5911`.

### CT-DEC-004 — OpenAI is Admin-only and never auto-publishes

- **ID:** CT-DEC-004
- **Date or date range:** June–July 2026.
- **Status:** Active.
- **Area:** Editorial AI.
- **Problem:** editors needed stronger rewriting while automated publication of
  OpenAI output would bypass human factual judgement.
- **Evidence:** factual-draft experiments introduced unsupported names, comparisons
  and rhetorical claims despite prompt instructions.
- **Alternatives considered:** use OpenAI in scheduled imports; auto-save corrected
  drafts; rely on prompts alone.
- **Decision:** OpenAI may research/copy-edit through authenticated Admin draft flows
  only; it must not save or publish automatically.
- **Rationale:** human review remains the final factual and publication boundary.
- **Implementation:** no-write draft endpoint, source/fact-pack evidence and a
  deterministic correction guard.
- **Result:** editors receive drafts and diagnostics without article mutation.
- **Follow-up:** retain manual verification of every factual claim.
- **Sources:** preserved state, “Admin OpenAI factual rewrite and editorial guard”;
  Git `ad131c7`, `5ef4041`, `2723fc7`, `3fcc4a3`, `83d8d69`.

### CT-DEC-005 — Manual Review is a first-class hidden editorial state

- **ID:** CT-DEC-005
- **Date or date range:** May–July 2026.
- **Status:** Active.
- **Area:** Editorial workflow.
- **Problem:** unsafe, short, uncertain or capped candidates were being published,
  archived ambiguously or discarded without editor visibility.
- **Evidence:** AI rewrite failures, locality failures and public API leakage.
- **Alternatives considered:** publish with warning; hard delete; ordinary archive;
  silent skip.
- **Decision:** retain qualifying candidates in a hidden Manual Review state excluded
  from public feeds, sitemaps and newsletters.
- **Rationale:** preserves editorial opportunity without weakening publication gates.
- **Implementation:** status/visibility fields, Admin queue, edit/restore protections
  and deterministic editorial metadata.
- **Result:** live, Manual Review and Archive became separate workflows.
- **Follow-up:** backend gates remain authoritative; update confirmation must explain
  possible restoration.
- **Sources:** preserved state, May and July Manual Review sections; Git `8bcc6bf`,
  `7dda210`, `a1980d2`, `1f18f9b`, `6da87da`, `50ede47`.

### CT-DEC-006 — Maintain the 40/40/20 editorial positioning

- **ID:** CT-DEC-006
- **Date or date range:** February 2026 onward.
- **Status:** Active.
- **Area:** Editorial strategy/homepage.
- **Problem:** undifferentiated feeds overrepresented crime, sport, lifestyle and
  generic national content.
- **Evidence:** repeated homepage audits and source/category rebalancing.
- **Alternatives considered:** purely chronological homepage; source quotas without
  editorial pillars; local-only publication.
- **Decision:** target an editorial mix of approximately 40% Cheshire/local, 40% UK
  public-interest and 20% business/finance/AI-tech, subject to available quality.
- **Rationale:** supports a useful Cheshire identity with broader economic relevance.
- **Implementation:** homepage allocation, importer classification, caps and
  newsletter selection.
- **Result:** the ratio became a strategic target, not a promise to publish weak
  material to fill a bucket.
- **Follow-up:** verify actual supply; quality and safety override ratio completion.
- **Sources:** preserved state, editorial strategy and homepage allocation sections;
  Git `6e77dd4`, `6b928d4`; July log, Version 1 completion.

### CT-DEC-007 — Suppress crime-heavy and weak filler material

- **ID:** CT-DEC-007
- **Date or date range:** February–July 2026.
- **Status:** Active.
- **Area:** Editorial policy.
- **Problem:** crime, court, death notices, galleries, deals and generic filler could
  dominate local feeds and lead positions.
- **Evidence:** live pool audits and repeated cleanup/filter corrections.
- **Alternatives considered:** allow all source output; UI-only suppression; category
  relabelling after publication.
- **Decision:** reject or hide weak/off-strategy material before public allocation;
  route only suitable uncertain records to Manual Review.
- **Rationale:** protects trust and the economic/civic publication mission.
- **Implementation:** deterministic import, homepage, sitemap and newsletter gates.
- **Result:** filler suppression became cross-surface rather than homepage-only.
- **Follow-up:** continue evidence-based feed audits without broadening filters
  speculatively.
- **Sources:** preserved state, February/March filtering and July Local RSS sections;
  Git `262d4fb`, `c39a00e`, `3c6d96e`, `4e00f0f`.

### CT-DEC-008 — Archive instead of ordinary hard delete

- **ID:** CT-DEC-008
- **Date or date range:** March–July 2026.
- **Status:** Active, with explicit legacy/admin-maintenance exceptions.
- **Area:** Article lifecycle.
- **Problem:** hard deletion broke links and naive cleanup removed recent or
  editorially protected records.
- **Evidence:** unsafe startup cleaner and archive-cap regressions.
- **Alternatives considered:** permanent delete; status-only hide; automatic age
  purge.
- **Decision:** normal Admin removal and duplicate/quality cleanup should archive
  before deleting the active copy; automatic hard-delete cleanup is disabled.
- **Rationale:** preserves recoverability and link history.
- **Implementation:** archive collection/reasons, owner protection, disabled startup
  and scheduled hard-delete paths.
- **Result:** archive became the ordinary removal contract. Some legacy cleanup
  endpoints still have separate hard-delete semantics and must not be conflated.
- **Follow-up:** retain explicit reasons and ID traceability in later lifecycle work.
- **Sources:** preserved state, March pool safety and April archive protection;
  Git `3ca0834`, `ad2e3b2`, `707da88`, `f8858ec`.

### CT-DEC-009 — Secure request-link newsletter management

- **ID:** CT-DEC-009
- **Date or date range:** 18–27 July 2026.
- **Status:** Active.
- **Area:** Newsletter security.
- **Problem:** legacy preference/unsubscribe/reactivation identity and ownership
  contracts were unsuitable for durable public management links.
- **Evidence:** staged security review and challenge-consumption tests.
- **Alternatives considered:** direct identity-bearing links; authenticated account
  system; immediate unguarded cutover.
- **Decision:** use expiring request links and transactional challenges for secure
  preferences, unsubscribe and reactivation.
- **Rationale:** gives subscribers control without exposing identity or requiring a
  full account system.
- **Implementation:** token service, migration fields, request limits, challenge
  routes, frontend fragment consumers and guarded indexes.
- **Result:** legacy management cut over after staged dormant implementation and
  activation corrections.
- **Follow-up:** preserve generic responses and transactional one-use behaviour.
- **Sources:** [July log](HISTORY/ENGINEERING_LOG_JULY_2026.md), secure newsletter
  phases; Git `be98b43` through `db8fae1`; tag `newsletter-security-v1.0`.

### CT-DEC-010 — Use Resend batch delivery

- **ID:** CT-DEC-010
- **Date or date range:** 11 April 2026 onward.
- **Status:** Active.
- **Area:** Newsletter delivery.
- **Problem:** Office 365 SMTP loops were fragile and difficult to observe at scale.
- **Evidence:** delivery failures, uptime issues and later batch diagnostics.
- **Alternatives considered:** retain SMTP loop; switch providers without recipient
  tracking; unlimited batches.
- **Decision:** use Resend batch APIs with bounded send caps and diagnostics.
- **Rationale:** provider batching reduces connection overhead and supports scalable
  accepted-recipient evidence.
- **Implementation:** `f76248a`, later batch rotation and memory/cap safeguards.
- **Result:** Daily Brief and Weekly Roundup moved to Resend; provider acceptance is
  distinguished from opens/clicks.
- **Follow-up:** monitor memory, errors and inactive-subscriber policy.
- **Sources:** preserved state, “Resend newsletter cutover”; Git `f76248a`,
  `540f73d`, `9580cbd`, `55f36ac`.

### CT-DEC-011 — Accepted-recipient delivery ledger

- **ID:** CT-DEC-011
- **Date or date range:** 11 April 2026 onward.
- **Status:** Active.
- **Area:** Newsletter analytics.
- **Problem:** a send attempt or batch count did not prove which recipients the
  provider accepted.
- **Evidence:** per-recipient tracking and Admin aggregation requirements.
- **Alternatives considered:** aggregate send counts only; infer delivery from opens;
  provider-wide batch state.
- **Decision:** persist per-recipient accepted delivery records and aggregate them
  for operational reporting.
- **Rationale:** creates a bounded auditable denominator for later engagement.
- **Implementation:** tracking IDs and per-recipient analytics (`11d56f2`,
  `77af404`).
- **Result:** delivery, open and click concepts became separable.
- **Follow-up:** never treat acceptance as confirmed inbox delivery.
- **Sources:** preserved state, April newsletter tracking; Git `11d56f2`, `77af404`.

### CT-DEC-012 — Affiliate-first monetisation

- **ID:** CT-DEC-012
- **Date or date range:** February–May 2026.
- **Status:** Active.
- **Area:** Monetisation.
- **Problem:** the publication needed revenue without premature broad advertising or
  low-trust commerce content.
- **Evidence:** authority-page system, joined programme work and guide conversion
  audits.
- **Alternatives considered:** display-ad-first approach; unsupported placeholder
  guides; product/deal feed publishing.
- **Decision:** prioritise useful authority/comparison guides with disclosed
  affiliate relationships and relevance-based placement.
- **Rationale:** aligns commercial value with reader intent and editorial usefulness.
- **Implementation:** authority pages, central routing, provider assets, click
  tracking and label cleanup.
- **Result:** affiliate guides became the primary commercial foundation.
- **Follow-up:** keep provider claims current and retain disclosure/quality controls.
- **Sources:** preserved state, March–May monetisation sections;
  [commercial records](commercial-gap-map/); Git `28b7f9c`, `c9f5131`, `cbb3dfe`.

### CT-DEC-013 — Paid sponsored placements require manual review

- **ID:** CT-DEC-013
- **Date or date range:** 25–30 April 2026.
- **Status:** Active.
- **Area:** Advertising.
- **Problem:** payment must not automatically publish unreviewed creative or create
  ambiguous unpaid placements.
- **Evidence:** advertising funnel and webhook verification work.
- **Alternatives considered:** automatic publication after checkout; enquiry-only
  workflow; unpaid placeholder activation.
- **Decision:** use paid placements with manual Admin review and explicit lifecycle
  status.
- **Rationale:** protects editorial presentation, payment integrity and advertiser
  expectations.
- **Implementation:** placement manager, review-first payment, webhook/notification,
  reporting and unpaid-lead flags.
- **Result:** a production-capable advertising workflow existed by late April.
- **Follow-up:** verify payment/configuration live before claiming individual
  placements active.
- **Sources:** preserved state, April advertising sections; Git `282a503`, `2d65bdb`,
  `bc734d0`, `c708b7d`.

### CT-DEC-014 — Stage Local RSS activation

- **ID:** CT-DEC-014
- **Date or date range:** 25–26 July 2026.
- **Status:** Active.
- **Area:** Sources/imports.
- **Problem:** adding multiple local feeds at once risked crime/filler leakage,
  duplicate overlap and unusable images.
- **Evidence:** read-only Newsquest shadow evaluation and scheduled import reviews.
- **Alternatives considered:** activate all discovered feeds; manual imports; reject
  every soft candidate.
- **Decision:** evaluate deterministically, activate feeds one at a time and observe
  normal scheduled outcomes before expansion.
- **Rationale:** isolates source quality and preserves existing publication gates.
- **Implementation:** shared Local RSS policy, shadow evaluator, image resolution and
  staged Knutsford/Nantwich rollout.
- **Result:** Local supply expanded while soft candidates remained hidden for review.
- **Follow-up:** require normal-run evidence before further feed activation.
- **Sources:** July log, Local RSS sections; Git `4e00f0f`, `6d87817`, `9cfb187`,
  `c80ca7e`.

### CT-DEC-015 — Version 1 duplicate prevention remains authoritative

- **ID:** CT-DEC-015
- **Date or date range:** March–August 2026.
- **Status:** Active.
- **Area:** Duplicate handling.
- **Problem:** new same-event similarity work could accidentally replace proven exact
  title, source URL, image, batch and uniqueness protections.
- **Evidence:** historical duplicate incidents and later Phase 2A/2B isolation tests.
- **Alternatives considered:** replace Version 1 with fuzzy similarity; make a score
  block insertion; merge records automatically.
- **Decision:** retain deterministic Version 1 checks as operational authority.
- **Rationale:** exact identity rules are explainable and already embedded throughout
  the insertion and cleanup paths.
- **Implementation:** scorer exact matches are ineligible; shadow integration runs
  after Version 1 decisions and cannot affect writes.
- **Result:** similarity evidence is advisory only at HEAD.
- **Follow-up:** any operational change requires separate review and production data.
- **Sources:** preserved state, duplicate and Phase 2A/2B sections; Git `b4612e1`,
  `a676059`, `a31fcab`, `8043fdd`, `5e1a875`.

### CT-DEC-016 — Editorial Similarity begins deterministic and shadow-only

- **ID:** CT-DEC-016
- **Date or date range:** 3–4 August 2026.
- **Status:** Active.
- **Area:** Editorial Similarity.
- **Problem:** cross-publisher same-event stories were not exact duplicates, but an
  uncalibrated AI or fuzzy blocker could suppress legitimate reporting.
- **Evidence:** Hough/former-kennels case and bounded scorer regressions.
- **Alternatives considered:** external AI classification; image comparison;
  immediate blocking or Manual Review routing; Admin UI first.
- **Decision:** start with a pure deterministic scorer, then scheduled-only,
  log-only, fail-open shadow integration.
- **Rationale:** produces reviewable evidence with no publication consequence.
- **Implementation:** `8043fdd`, `5e1a875`.
- **Result:** bounded logs were activated for normal scheduled generation according
  to deployment record `1601ae4`.
- **Follow-up:** inspect multiple normal runs before calibration.
- **Sources:** preserved state, final Editorial Similarity sections; Git `8043fdd`,
  `5e1a875`, `1601ae4`.

### CT-DEC-017 — No threshold or UI before multiple normal-run evidence

- **ID:** CT-DEC-017
- **Date or date range:** 4 August 2026.
- **Status:** Active.
- **Area:** Editorial Similarity operations.
- **Problem:** synthetic tests and one run cannot establish safe score thresholds or
  user-facing conclusions.
- **Evidence:** Phase 2B remains advisory and deployment itself is not calibration.
- **Alternatives considered:** build Similar Stories immediately; use likely band as
  a blocker; trigger imports solely to collect data.
- **Decision:** observe at least three normal scheduled runs, without manual imports,
  before threshold or UI work.
- **Rationale:** normal production distributions and failure behaviour are required.
- **Implementation:** documented observation gate at `1601ae4`.
- **Result:** threshold/UI work remained unapproved at HEAD.
- **Follow-up:** reconcile post-HEAD run evidence through repository records.
- **Sources:** preserved state, “Editorial Similarity deployment and
  production-observation gate”; Git `1601ae4`.

### CT-DEC-018 — Observe production memory before optimising

- **ID:** CT-DEC-018
- **Date or date range:** 29–31 July 2026.
- **Status:** Active.
- **Area:** Production performance.
- **Problem:** historical Render OOMs existed, but repository inspection could not
  attribute every restart or justify a speculative optimisation.
- **Evidence:** QA `QA-OPS-001` and generation-time memory investigation.
- **Alternatives considered:** add an index without plans; reduce editorial/import
  behaviour; optimise from local estimates alone.
- **Decision:** add twelve read-only memory phase markers and compare normal runs
  before changing production behaviour.
- **Rationale:** `ru_maxrss` is a process high-water mark and must be interpreted with
  timing/context.
- **Implementation:** `42736f9`.
- **Result:** observability was added without scheduler or publication changes.
- **Follow-up:** correlate peaks with feed, visible-pool and duplicate-read phases.
- **Sources:** [QA report](QA/QA_REPORT_2026-07-29.md), `QA-OPS-001`; July log,
  “Scheduled article-generation memory observability”; Git `42736f9`.

### CT-DEC-019 — Defer the broad Version 2 brand refresh

- **ID:** CT-DEC-019
- **Date or date range:** 31 July 2026.
- **Status:** Deferred.
- **Area:** Brand/product design.
- **Problem:** a broad visual refresh would compete with unresolved operational,
  analytics, mobile and editorial evidence work.
- **Evidence:** Version 1 brand library was complete and current risks were elsewhere.
- **Alternatives considered:** immediate comprehensive redesign; incremental polish;
  retain Version 1 baseline.
- **Decision:** defer the Version 2 brand refresh and keep the approved Version 1
  system.
- **Rationale:** avoids destabilising production while higher-value work continues.
- **Implementation:** documentation commit `dcde9ba`; no redesign runtime change.
- **Result:** existing brand assets remained the repository baseline at HEAD.
- **Follow-up:** revisit only with a separately approved brief and evidence.
- **Sources:** July log, “Version 2 branding decision”;
  [brand assets](brand-assets/); Git `dcde9ba`.

### CT-DEC-020 — Separate historical records from current operational state

- **ID:** CT-DEC-020
- **Date or date range:** July–August 2026 documentation rebuild.
- **Status:** Active.
- **Area:** Documentation architecture.
- **Problem:** the 25,597-line state file mixed current facts, chronology, prompts,
  failed attempts and superseded next steps.
- **Evidence:** Phase 1 inventory and exact Phase 2 preservation copy.
- **Alternatives considered:** delete old sections; keep appending indefinitely;
  rewrite without backup.
- **Decision:** preserve the full state, build permanent history/decision/timeline
  records and reduce current state only after section-level preservation is proven.
- **Rationale:** current operations become readable without losing reasoning.
- **Implementation:** archive snapshot, source register and this Phase 3 record set.
- **Result:** historical separation is in progress; `PROJECT_STATE.md` remains
  unchanged and authoritative until Phase 7.
- **Follow-up:** build current architecture/operations records, QA and roadmap before
  reducing state.
- **Sources:** [Source Register](HISTORY/SOURCE_REGISTER.md); preserved state;
  [Engineering History](HISTORY/ENGINEERING_HISTORY_MASTER.md).

### CT-DEC-021 — Direct newsletter unsubscribe with secure recovery retained

- **Date:** 21 September 2026.
- **Status (23 September 2026):** **FUNCTIONAL PRODUCTION ACCEPTANCE COMPLETE — UPSTREAM QUERY-LOG PRIVACY GATE OPEN**.
- **Problem:** Generic newsletter footers unnecessarily require email re-entry
  and a second email for normal unsubscribe.
- **Decision:** Use a distinct signed subscriber-specific direct credential to
  reach website confirmation, followed by explicit mutation. GET never mutates.
  Keep generic challenge-backed recovery, signup and preferences unchanged.
- **Security:** Bind purpose, management UUID, token version and bounded expiry;
  exclude subscriber email. Require an explicit signed class discriminator, not
  inferred lifetime or absent challenge. Only direct credentials are challenge-free;
  recovery credentials retain their challenge requirements. Enforce current version
  atomically at mutation, including concurrent reactivation and inactive replay.
- **Transport:** Website fragment capture/scrubbing; native one-click HTTPS POST
  with query credential and the exact protocol body. Per-recipient native headers
  require query-log privacy and delivered DKIM/header acceptance gates.
- **Alternatives:** Retain second-email normal flow, website query credentials or
  new opaque bearer storage. Fragment reuse reduces HTTP-log exposure but does not
  prove Apple Mail compatibility.
- **Prerequisite resolution:** Exact direct claims are the existing `sub`, `purpose`,
  `ver`, `iat`, `exp` plus signed
  `credential_class="newsletter_direct_unsubscribe"`, with unsubscribe purpose
  and a 90-day lifetime. Strict legacy five-claim validation stays unchanged.
  The tracked inactive-to-active writer increments version atomically. Missing or
  malformed recipient identity fails closed before content send, with aggregate
  skip diagnostics; backfill remains separate. Welcome is transactional onboarding,
  excluded from native headers. Live identity coverage, query-log privacy and
  delivered authentication/client evidence remain production gates, not local
  implementation blockers. See the architecture record for audit bounds.
- **Local progress:** Local implementation is complete through Phase 2B Slice 6.
  Phase 1 is committed at `516fa29`; Phase 2A at `4e6a8cf`; Phase 2B subscriber-content
  integrations are committed at `e91de2d`, `fc8b34c`, `14e2f01`, `14d05a9`,
  `4503c28` and `68cefd3`, with state reconciled through `283a5f7`. Daily Brief,
  Weekly Roundup, Breaking News, migration announcement, Site Updates/onboarding
  and subscriber-targeted manual campaigns now use the approved prepared direct-delivery
  path. Independent final Slice 6 regression evidence is 1,813 newsletter
  plus Weekly idempotence tests passed with zero failures (420 warnings). The chain
  was pushed and deployed at `2f40374`; functional production acceptance passed
  for identity/index readiness, controlled Resend receipt, native headers/DKIM,
  native mutation/inactive replay, human confirmation, challenge-backed reactivation
  with exact version increment, stale-token rejection, active preferences and
  consumed-challenge rejection, and transactional header-free welcome delivery.
  Later `40304fc` only changes welcome coverage copy and was pushed after this run.
  Upstream privacy is unverified and **POTENTIAL QUERY LOG EXPOSURE** remains. Render auto-deploy
  is enabled on commit for `full-scrape-prod`: no push without explicit deployment
  authorization.
- **Boundaries:** Functional acceptance is complete, not unconditional privacy closure.
  Render Request Logs remain unavailable at the current plan/access level. Client
  httpx INFO logging exposed the already-stale credential URL during acceptance;
  no sensitive value is retained here. No independent manual human/native token
  equality comparison or post-signup database verification is claimed. CT-QA-2026-006
  and CT-QA-2026-007 stay closed; no new QA finding is registered, no totals change
  and no legal/compliance claim is made.
- **Sources:** Owner approval at baseline `52c9b64e3940655177002cda6f0fe3613bc0b8ad`;
  owner-supplied 23 September production evidence reconciled in the
  [Production Timeline](PRODUCTION_TIMELINE.md#23-september-2026--ct-dec-021-functional-production-acceptance);
  [Newsletter Architecture](ARCHITECTURE/NEWSLETTER.md) owns the detailed contract.


### CT-DEC-022 — Separate provider suppression from subscription lifecycle

- **ID:** CT-DEC-022
- **Date:** 24 September 2026.
- **Status:** Implemented, deployed and production suppression reconciliation verified.
- **Area:** Newsletter delivery eligibility and provider hygiene.
- **Problem:** Resend suppression state and Cheshire Today subscriber lifecycle state are distinct. Provider evidence identified suppressed recipients whose local records could remain active, while transient bounce events must not be treated as permanent subscription withdrawal. Reusing unsubscribe/reactivation fields would misstate the cause and could allow later reactivation to obscure an unchanged provider block.
- **Decision:** Keep `active` as the Cheshire Today subscription/consent lifecycle. Represent a known provider block separately with `provider_suppressed=true`, `provider_suppression_reason` (`complaint` or `bounce`), `provider_suppressed_at` and `provider_suppression_source="resend"`. Absence of `provider_suppressed=true` remains backward-compatible and means no known local provider block. Subscriber-content delivery must exclude explicit provider suppression before caps/selection where the path supports query-time filtering, with a shared preparation guard as defence in depth.
- **Lifecycle boundary:** Provider suppression does not unsubscribe a reader and normal reactivation must not silently clear it. Complaint suppressions must not be removed as part of application reactivation. Provider reconciliation, provider-side unsuppression and any production subscriber mutation require separate evidence and explicit approval.
- **Implementation:** D-1 changes cover scheduled/manual Daily Brief, scheduled/diagnostic Weekly Roundup, Breaking News, migration announcement, Site Update parts 1/2, onboarding eligibility and subscriber-targeted manual campaigns. Onboarding retains its intentionally broad identity fetch and excludes suppressed records from its due population. Migration-announcement preference migration remains separate from delivery eligibility. D-1 was committed as `34ecf74`, pushed to `full-scrape-prod`, deployed Live on that exact commit and health-verified HTTP 200. Production reconciliation then populated only the four CT-DEC-022 provider-suppression fields for the authoritative matched suppression population; no Resend configuration, DNS, transport, unsubscribe/reactivation semantics or newsletter preferences were changed.
- **Verification:** Combined affected newsletter regression: 403 passed, 18 pre-existing deprecation warnings, zero failures. `backend/server.py` compilation and `git diff --check` passed. Production deployment was verified at exact commit `34ecf74` with HTTP 200 health. The authoritative Resend export contained 815 unique suppressions (785 bounce, 30 complaint), all 815 matched exactly one subscriber record, with 583 active and 232 inactive/legacy. A validated `0600` private backup covered the same 815 IDs. The first approved transaction aborted before commit when post-write verification exposed BSON millisecond precision handling for 60 sub-millisecond source timestamps; immediate read-only verification confirmed 0 reconciled / 815 pending / 0 non-exact. After BSON-compatible timestamp normalization and an independent aborted round-trip test, the corrected transaction committed with 815 matched, 815 modified and 815 exact post-write. Independent verification then returned 815 exactly reconciled / 0 pending / 0 non-exact; global aggregates showed 815 provider-suppressed, 785 bounce, 30 complaint, zero unexpected source/reason.
- **Follow-up:** Keep provider suppression separate from transient message-level bounce events and do not clear it through ordinary reactivation. Provider-side unsuppression remains a separate explicitly approved action. With the known suppression population reconciled locally, trace the owner-reported missing-newsletter case and Apple/iCloud Junk placement separately; CT-DEC-022 does not claim inbox-delivery remediation.
- **Sources:** D-1 implementation, deployment and production reconciliation evidence on `full-scrape-prod`; [Newsletter Architecture](ARCHITECTURE/NEWSLETTER.md); [Newsletter Operations](OPERATIONS/NEWSLETTER_OPERATIONS.md); [Test History](QA/TEST_HISTORY.md).

## 26 September 2026 — CT-DEC-010/011/022 operational boundary

CT-DEC-022 suppression eligibility and the 815-record reconciliation are complete
(`34ecf74`, `5afd7b1`); consent state remains separate. Resend remains the
configured newsletter transport contract; no provider migration is approved.
Application Feedback-ID support (`8ed1984`) is deployed, but tested Resend batch
and single deliveries contain SES-generated identifiers, not the custom values.
Support response on preservation/equivalent Gmail FBL is pending. Do not claim
end-to-end FBL operational or implement an unsupported workaround.

The existing CT-DEC-011 accepted-opportunity cold methodology is unchanged.
The 739→1,001 change is reproduced by 262 four→five threshold crossings on
September 26. Gmail placement and Postmaster negative sentiment remain an
evidence-led investigation. No Gmail-specific deactivation, recovery audience,
send-volume change or speculative remediation is authorised by these findings.
See [dated evidence](HISTORY/NEWSLETTER_DELIVERABILITY_2026-09-26.md).
CT-DEC-021 functional acceptance and its open query-log privacy gate are unchanged.
This clarifies existing boundaries, not a new implementation decision.

## Unreconciled decision evidence

- ChatGPT export and systematic Codex records may reveal additional alternatives or
  earlier rationale.
- Historical PDF strategy has not been reconciled.
- Post-HEAD production investigations cannot change a decision status until recorded
  in repository evidence.
- No decision above should be interpreted as permission to mutate production.
