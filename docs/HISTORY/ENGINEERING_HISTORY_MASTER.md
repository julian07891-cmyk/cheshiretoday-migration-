# Cheshire Today — Engineering History Master

> **Reconstruction status:** repository-evidence history through commit
> `49e5fe49cc35e0ca020e8520db6365d356760060` on 7 August 2026. ChatGPT export,
> systematic Codex history and post-HEAD production evidence remain unreconciled.

## Document purpose

This document is the durable chronological engineering history of Cheshire Today.
It records the problem, implementation, verification and operational outcome of
major work without treating an old “current state” statement as present truth.

## How to use this document

- Start with the relevant month and follow its source and Git references.
- Use the [Decision Register](../DECISION_REGISTER.md) for rationale, the
  [Production Timeline](../PRODUCTION_TIMELINE.md) for live events and the
  [Editorial Evolution](../EDITORIAL_EVOLUTION.md) for policy changes.
- Consult the [Source Register](SOURCE_REGISTER.md) before relying on evidence.
- Verify current behaviour against code and production; this is history, not the
  operational-state file.

## Evidence and authority

The preserved source is
[PROJECT_STATE_REDACTED_2026-08-06.md](../ARCHIVE/PROJECT_STATE_REDACTED_2026-08-06.md).
Supporting evidence is the unchanged
[July engineering log](ENGINEERING_LOG_JULY_2026.md), the
[29 July QA report](../QA/QA_REPORT_2026-07-29.md), Git history and repository
documentation. “Implemented”, “committed”, “deployed” and “production-verified”
are separate states. A commit message is not deployment proof.

## Reconstruction status

The repository chronology is reconstructed through current HEAD. Uncertain deploy
claims are labelled. No claim of complete history is made until the pending sources
listed below are reconciled.

## Chronological history

### February 2026

#### Initial Render platform and API stabilisation — 1–9 February

- **Problem/objective:** establish a live React/FastAPI/MongoDB publication and
  stabilise health, API addressing, Admin authentication and newsletter input.
- **Implementation:** initial Render deployment (`789e9c8`); `/api/health`
  (`ef7cfbc`); API caching (`c7fe038`); production URL/canonical handling
  (`9004895`); Admin/API URL consolidation (`223cc34`); newsletter validation
  (`4ba7afa`).
- **Verification/result:** later repository records describe the site as live on
  Render with SSL and operational API, database and Admin paths. These later records
  corroborate launch but do not preserve every initial deploy event.
- **Follow-up:** scheduler, editorial allocation and production-safe import controls
  remained immature.
- **Sources:** [preserved state](../ARCHIVE/PROJECT_STATE_REDACTED_2026-08-06.md),
  sections “Current State Master” and February history; Git `789e9c8`, `ef7cfbc`,
  `223cc34`, `4ba7afa`.

#### Homepage, article and authority foundations — 7–24 February

- **Problem/objective:** replace unstable early layouts with a coherent editorial
  homepage, readable article pages and monetisable authority guides.
- **Implementation:** Homepage V1 scaffold and allocation (`8aae8e1`, `217a6f5`),
  article rendering crash repairs (`1c44b37` through `e0b6048`), authority-page
  system (`28b7f9c`, `649fce3`, `2dc9c26`) and stable layout checkpoints
  `LAYOUT_STABLE_2026_02_22` and `UI_LAYOUT_SOURCE_STABLE_2026_02_22`.
- **Result:** a stable homepage/article/guide baseline emerged. Several early guide
  and promo surfaces were deliberately feature-gated after article regressions.
- **Sources:** preserved state, February layout and monetisation sections; Git
  `8aae8e1`, `217a6f5`, `28b7f9c`, `4d8958b`, `2dc9c26`; listed tags.

#### Editorial allocation and import controls — 14–28 February

- **Problem/objective:** prevent repeated, archived, crime-heavy and weak commercial
  items from dominating the public site.
- **Implementation:** source/title RSS dedupe (`a2d1639`), archived filtering
  (`30a6282`), deal-source blocking (`41fa296`), lead crime guard (`262d4fb`),
  stricter Local RSS sources (`ad4c2a7`) and 40/40/20 homepage refinement
  (`6b928d4`).
- **Result:** deterministic editorial controls began to replace UI-only filtering.
  Local supply and category balance still required repeated adjustment.
- **Sources:** preserved state, February editorial sections; Git `a2d1639`,
  `30a6282`, `262d4fb`, `6b928d4`.

### March 2026

#### Canonical routes, crawler HTML and sitemap identity — 3–18 March

- **Problem/objective:** repair unstable article URLs, crawler SPA responses and
  social preview identity.
- **Implementation:** slugged canonical routes (`0f6f4e0`), redirects and HEAD
  support (`82e193f`, `c9aa4a5`), slugged sitemap URLs (`025a290`, `d2e013d`),
  crawler HTML (`f4324ac`, `bc170be`) and larger social images (`f751627`,
  `a01c76e`).
- **Result:** Mongo/public ID compatibility was retained while canonical slug paths
  became the public contract. Later July work consolidated identity further.
- **Sources:** preserved state, March SEO and routing updates; Git `0f6f4e0`,
  `82e193f`, `f4324ac`, `bc170be`, `c9aa4a5`.

#### Hybrid RSS and Perplexity article pipeline — 5–17 March

- **Problem/objective:** move beyond thin RSS summaries without allowing stalled or
  invented rewrites into production.
- **Implementation:** long-form Perplexity pipeline (`000fb94`), timeout and immediate
  rewrite corrections (`bd762fc`, `1408300`, `41ff27e`), research-oriented prompts
  (`5a892be`), paragraph preservation (`53d5911`) and full-content publication floor
  (`c7f8e20`, `0091276`).
- **Result:** hybrid RSS plus Perplexity became the principal automated model. Short
  or failed work increasingly moved away from public visibility.
- **Sources:** preserved state, March import-pipeline sections; Git `000fb94`,
  `bd762fc`, `5a892be`, `53d5911`, `0091276`.

#### Scheduler and archive safety — 6–17 March

- **Problem/objective:** scheduled freshness mechanisms and naive duplicate cleanup
  could remove or surface the wrong records.
- **Implementation:** scheduler enablement (`6fc5d05`), Daily Brief repair
  (`4c36137`), archive window and indexes (`34ac536`, `72a5dcb`), unsafe startup
  duplicate cleanup disabled (`3ca0834`) and force-live support (`add9a21`).
- **Result:** a destructive first-five-word startup cleaner was rejected. Archive and
  owner controls became explicit safety boundaries.
- **Sources:** preserved state, March stability and pool-safety sections; Git
  `3ca0834`, `add9a21`, `4c36137`.

#### Homepage stability and guide recovery — 9–29 March

- **Problem/objective:** prevent repeated articles, stale ordering, fragile guide
  rendering and uncontrolled monetisation surfaces.
- **Implementation:** stable homepage/article layout (`c15069e`), freshness fixes
  (`3418ff8`, `fdf8541`), duplicate protection (`b4612e1`), guide route recovery
  (`073a13e`, `6287cdd`) and force-live correction (`316a8f0`).
- **Result:** the homepage recovered, while feature flags and conservative rollouts
  were retained after failed article-funnel experiments.
- **Sources:** preserved state, sections “Detailed update — March 19”, “Guides /
  Monetisation” and March 29 handover; Git `b4612e1`, `073a13e`, `6287cdd`.

### April 2026

#### Scheduler timezone and hard-delete policy — 2 April

- **Problem/objective:** keep jobs DST-correct and stop newly imported stories with
  old source dates being deleted.
- **Implementation:** Europe/London scheduler pinning and archive-cron removal
  (`2e3b17d`, `be47a48`); automatic hard-delete cleanup disabled (`ad2e3b2`).
- **Result:** scheduled times became explicit; age-based deletion remained manual.
- **Sources:** preserved state, April scheduler history; Git `2e3b17d`, `be47a48`,
  `ad2e3b2`.

#### Homepage performance, content and archive protection — 3–12 April

- **Problem/objective:** reduce slow article-list responses, restore strategic mix
  and prevent automatic caps from undoing editorial archives.
- **Implementation:** backend article-list optimisation (`0e1d639`), image/cache work
  (`75b6c5c`), reverted feed-image normalisation (`27c5a57`), strategic filtering
  (`509e263`, `1aef3cb`), source-URL duplicate guards (`a676059`, `a31fcab`) and
  durable archive protection (`707da88`).
- **Result:** performance and archive semantics improved; the risky global image
  normalisation experiment was removed rather than retained.
- **Sources:** preserved state, 3–12 April appendices; Git `0e1d639`, `27c5a57`,
  `a31fcab`, `707da88`.

#### Authority guides and affiliate-first monetisation — 7–30 April

- **Problem/objective:** establish useful commercial pages without turning editorial
  coverage into undifferentiated advertising.
- **Implementation:** authority rendering/metadata (`aae3a97`), contextual guide
  surfaces (`c9f5131`, `59a9cc3`), provider assets and routing, tracked clicks, guide
  sitemap inclusion (`fa5a8bc`) and documented label cleanup (`cbb3dfe`).
- **Result:** affiliate guides became the primary low-risk monetisation layer;
  controlled rollouts replaced blanket guide promotion.
- **Sources:** preserved state, April authority/affiliate sections;
  [commercial records](../commercial-gap-map/); Git `aae3a97`, `c9f5131`,
  `59a9cc3`, `fa5a8bc`.

#### Resend cutover and recipient tracking — 11–15 April

- **Problem/objective:** replace fragile Office 365 per-message SMTP delivery and
  obtain recipient-level delivery evidence.
- **Implementation:** Resend batch delivery (`f76248a`), per-recipient IDs
  (`11d56f2`), source-of-truth update (`fe5fe97`) and bounded cleanup/cap controls
  (`c54c3c1`).
- **Result:** newsletter delivery moved to batches with an accepted-recipient ledger.
  Send caps remained operational safeguards rather than inferred delivery proof.
- **Sources:** preserved state, “Resend newsletter cutover” section; July log,
  “Newsletter redesign”; Git `f76248a`, `11d56f2`, `fe5fe97`.

#### Sponsored placement and advertising workflow — 25–30 April

- **Problem/objective:** support paid placements without automatic publication or
  unreviewed payment activation.
- **Implementation:** manual sponsored-placement records (`282a503`), Admin manager
  (`2d65bdb`), tracking (`4f4d22e`), review-first payment (`bc734d0`), advertiser
  notifications and reporting/export work.
- **Result:** placements became paid but manually reviewed operational records.
- **Sources:** preserved state, April advertising phases; Git `282a503`, `2d65bdb`,
  `4f4d22e`, `bc734d0`.

### May 2026

#### Manual Review becomes an editorial state — 12–31 May

- **Problem/objective:** unsafe or incomplete AI/RSS records needed a hidden state
  rather than publication, silent discard or ordinary archive.
- **Implementation:** hidden risky rewrites (`8bcc6bf`), Manual Review Admin views
  (`7dda210`, `518a062`), public/sitemap exclusion (`a1980d2`, `ff3c20a`,
  `22914d1`), edit/restore (`d426558`), OpenAI review (`ecd4a30`, `a7aa5ea`) and
  strengthened move/force-live protection (`067288e`, `4a276f1`).
- **Result:** Manual Review evolved into a first-class hidden editorial queue with
  explicit human release safeguards.
- **Sources:** preserved state, May Manual Review sections; Git `8bcc6bf`,
  `7dda210`, `d426558`, `067288e`.

#### Editorial verification experiments and rollback — 24–26 May

- **Problem/objective:** improve factual safety and manage failed/short Perplexity
  output.
- **Implementation:** a sequence of verification, fallback and Manual Review commits
  on 24 May, followed by explicit reversions on 25 May, including paused Gemini
  verification. A narrower working Perplexity flow was restored on 26 May
  (`d0b7243`) with diagnostics and Admin-only OpenAI review.
- **Result:** broad experimental verification did not become production authority.
  Deterministic gates and human review remained preferred.
- **Sources:** preserved state, “Major QA / Import Rollback” and 25–26 May updates;
  Git `1e2733f`, `7efe329`, reverts `d0e8399`, `7fef821`, `a796691`, and `d0b7243`.

#### Newsletter scale and memory safeguards — 2–28 May

- **Problem/objective:** scale Daily Brief/Weekly Roundup while avoiding duplicate,
  inactive or memory-heavy sends.
- **Implementation:** batch rotation (`540f73d`), diagnostics (`ffc4acc`), reserved
  test-address exclusion (`90d284f`), Daily Brief memory reduction (`9580cbd`),
  1,000 default cap (`55f36ac`) and engaged-recipient prioritisation (`7267e67`).
- **Production incident:** repository history records a confirmed 512 MB OOM during
  a 2,000-recipient Daily Brief on 22 May; subsequent caps and batching were safety
  responses.
- **Sources:** preserved state, May newsletter/OOM sections; QA `QA-OPS-001`; Git
  `9580cbd`, `55f36ac`, `7267e67`.

#### Sitemap and crawler quality tightening — 13–31 May

- **Problem/objective:** remove filler, hidden review records and stale/low-quality
  items from Google-facing surfaces.
- **Implementation:** Google News fixes (`b6e336c`), repeated sitemap filters
  (`c73b68e`, `634043f`, `10e0741`, `56d0098`, `0a62c29`) and archived social-link
  recovery (`d492b8a`).
- **Result:** sitemap inclusion became an editorial-quality contract rather than a
  dump of stored records.
- **Sources:** preserved state, May indexing sections; Git references above.

### June 2026

#### Town feeds, Manual Review and homepage dedupe — 2–22 June

- **Problem/objective:** retain useful local soft failures while preventing repeated
  or weakly local homepage stories.
- **Implementation:** town RSS soft failures to review (`41639cf`), related-title
  homepage dedupe (`d9e0b2d`, `5a3cb1f`) and local filter adjustment (`49a1296`).
- **Result:** locality became stored and reviewable rather than a simple publish/drop
  decision.
- **Sources:** preserved state, June QA and homepage sections; Git `41639cf`,
  `d9e0b2d`, `5a3cb1f`.

#### Admin OpenAI draft flow and crawler SEO — 22–27 June

- **Problem/objective:** allow human editors to improve articles without giving
  OpenAI publication authority, and make article/guide HTML crawlable.
- **Implementation:** Admin-only no-save draft (`ad131c7`), crawler article HTML
  (`6b80bff`, `2b8194c`), authority crawler HTML/noindex controls (`ad8df82`,
  `644b2b2`).
- **Result:** OpenAI was established as an editor tool; crawler HTML remained a
  backend contract separate from browser rendering.
- **Sources:** preserved state, 22 and 26 June updates; Git references above.

### July 2026

#### Scheduler, OpenAI and operational security — 2–18 July

- **Problem/objective:** harden scheduled ownership and ensure factual-rewrite and
  operational endpoints were safe.
- **Implementation:** Resend validation (`276f7ff`), scheduler ownership guard
  (`432b180`), source/fact-pack OpenAI pipeline (`5ef4041`, `2723fc7`), deterministic
  editorial guard (`3fcc4a3`, `83d8d69`) and broad Admin-authentication protections
  (`5a943fa`, `63241ad`, `c888a8e`, `63885d7`, `68c5a9d`).
- **Result:** OpenAI remained draft-only and operational routes became explicitly
  authenticated. Deployment status varies by individual entry; later July records
  document the integrated baseline.
- **Sources:** July log, “Security improvements” and OpenAI sections; preserved
  state, 7–18 July updates; Git references above.

#### Manual Review, Archive and live-pool separation — 14–24 July

- **Problem/objective:** repair ID mismatches, separate live/review/archive states and
  stop caps/cleanup leaving or restoring the wrong records.
- **Implementation:** Manual Review ID repair (`a075a49`), live/review separation
  (`1f18f9b`), searchable Archive (`b3ca258`), truthful archive/import actions
  (`f8858ec`), canonical consolidation (`98d582f`), live-pool hardening
  (`be5c4ed`) and self-healing cap repair (`dc18e65`).
- **Result:** state boundaries became test-backed. Normal Admin archive remained an
  archive move, while specific legacy cleanup utilities retained separate semantics.
- **Sources:** July log, “Production data work” and repository milestones; preserved
  state, 14–24 July updates; Git references above.

#### Secure newsletter ownership — 18–27 July

- **Problem/objective:** replace identity-bearing management URLs and ambiguous
  subscriber ownership with secure request/challenge flows.
- **Implementation:** token service and migration (`be98b43`, `45165e6`), dormant
  routes, preferences/unsubscribe/reactivation challenges, guarded index
  (`6e36b71`), frontend cutover (`298a880`, `85bc971`), activation
  (`18d03c2`, `60b57a4`) and one-click public signup/unique index (`82bd4ab`,
  `0bb3ce8`).
- **Verification/result:** July records describe zero duplicate normalised-email
  groups and successful guarded index provisioning. Request-link controls were
  temporarily disabled and re-enabled during correction.
- **Sources:** July log, “Newsletter redesign” and security stages; preserved state,
  18–27 July entries; Git references above.

#### Local RSS staged activation — 21–26 July

- **Problem/objective:** improve Cheshire supply without admitting crime, duplicates,
  invalid sources or low-value filler.
- **Implementation:** Newsquest image resolution (`3f4ab10`), Local RSS review route
  (`468e0b7`), civic/investment refinement (`4d58e31`), editorial metadata
  (`6da87da`), shadow evaluator (`4e00f0f`) and staged Nantwich activation
  (`9cfb187`, `c80ca7e`).
- **Production result:** documented scheduled imports confirmed active feeds and a
  larger hidden review pool while public safeguards remained authoritative.
- **Sources:** July log, “Production hardening”; preserved state, 21–26 July Local
  RSS updates; Git references above.

#### Brand system, newsletter presentation and Social Publishing — 21–28 July

- **Problem/objective:** create consistent public/editorial presentation and a safe
  no-post Admin composition workflow.
- **Implementation:** homepage/article redesign (`bb925f1`, `a529791`), digest HTML
  (`7b1aeef`), brand library and guidelines (`86794f6`, `2f4e1a0`), Facebook and
  Instagram generators, unified Admin (`9902e3c`) and Threads workflow
  (`2bcdf5c`).
- **Result:** copy/download workflows were separated from publishing. Version 1
  social assets became repository-defined and deterministic.
- **Sources:** July log, Facebook Publishing Studio and Version 1 sections;
  [brand assets](../brand-assets/); Git references above.

#### Version 1 completion and QA — 27–29 July

- **Milestone:** Version 1 engineering completion was recorded at `ffa7f9d`, with
  the platform, Manual Review, newsletter, security, social and operational baseline
  documented.
- **QA:** the 29 July report found a committed credential, unsafe external tests,
  syntax failures, broad CORS, metadata and accessibility issues and unresolved
  memory evidence. Credential/test containment followed (`b804cdd`, `603e11b`),
  while the QA report remained an immutable baseline.
- **Sources:** July log, “Version 1 completion”; [QA report](../QA/QA_REPORT_2026-07-29.md),
  `QA-SEC-001` through `QA-OPS-001`; Git `ffa7f9d`, `b804cdd`, `603e11b`.

#### Analytics, Most Read and memory observability — 30–31 July

- **Problem/objective:** make first-party article views and period rankings truthful,
  and obtain evidence for Render generation memory risk.
- **Implementation:** view tracking repair (`6a95ba9`), period limit correction
  (`a93d4bf`, `d6eb46b`) and twelve article-generation memory markers (`42736f9`).
- **Result:** Most Read used period events instead of lifetime fallback. Memory work
  was observational and did not optimise or alter scheduler behaviour.
- **Sources:** July log, analytics and memory sections; preserved state, 30–31 July;
  Git references above.

### August 2026 through current HEAD

#### Admin Analytics and Facebook attribution — 1 August

- **Implementation:** Admin analytics dashboard (`cac9b24`) and first-party bounded
  Facebook UTM attribution (`9b024cc`).
- **Result:** deterministic Social Publishing URLs could be attributed without Meta
  API data, raw URLs or IP exposure. The repository records implementation and later
  functional production verification, but post-HEAD task evidence remains subject
  to Codex reconciliation.
- **Sources:** preserved state, “Admin Analytics Phase 1/2A”; July log appended
  August sections; Git `cac9b24`, `9b024cc`.

#### Rendered metadata reconciliation — 1 August

- **Problem/objective:** eliminate static-shell and route-specific canonical, Open
  Graph and Twitter duplicates without changing crawler HTML.
- **Implementation:** `6bfe896`, `1e5c2da`; production documentation `7ca1269`.
- **Production result:** repository history records successful live rendered-DOM,
  crawler, sitemap and robots verification. No indexing recovery was claimed.
- **Sources:** preserved state, metadata sections; Git `6bfe896`, `1e5c2da`,
  `7ca1269`; QA antecedent `QA-SEO-001`.

#### Admin mobile and editorial safety — 1–2 August

- **Implementation:** Admin-scoped mobile typography/login (`2d7ed9f`), editor
  containment (`6328cf3`), sticky close (`a6bfb78`), production record (`cf0ae79`),
  Manual Review publication-intent confirmation (`50ede47`) and responsive cards
  (`761a7c2`, `f43c4ef`).
- **Production result:** real-iPhone verification recorded usable login/editor at
  Safari Page Zoom 100%; Safari zoom itself was not disabled. Normal Articles mobile
  containment was deployed according to repository records, but later device/task
  evidence must be reconciled separately if it post-dates HEAD.
- **Sources:** preserved state, August Admin sections; July log appended sections;
  Git references above.

#### Editorial Similarity Phases 2A and 2B — 4 August

- **Objective:** evaluate cross-publisher same-event similarity without replacing
  Version 1 duplicate prevention or changing publication outcomes.
- **Phase 2A:** pure deterministic, identity-free scorer with bounded inputs and
  synthetic Hough fixture (`8043fdd`).
- **Phase 2B:** scheduled-only, log-only, fail-open integration with 50+50 initial
  pool, 100-record corpus, 20-record shortlist and maximum 20 scorer calls
  (`5e1a875`).
- **Deployment:** `1601ae4` records Render deployment of `5e1a875` and an observation
  gate of at least three normal scheduled runs. It does not prove calibration.
- **Sources:** preserved state, final three sections; July log appended Phase 2A/2B;
  Git `8043fdd`, `5e1a875`, `1601ae4`.

#### Duplicate-cleanup memory lifecycle mitigation — 7–8 August

- **Incident:** the normal 7 August 06:00 BST scheduled import began at a 385.3 MB
  process high-water, reached 431.7 MB after the visible-pool cap, 466.6 MB after
  the first duplicate-cleanup read and 530.0 MB after the second read. The job
  completed, then Render reported OOM at approximately 06:42 and recovered at
  approximately 06:43; the verified service ceiling was 512 MB.
- **Investigation:** `_remove_duplicates_internal()` retained the first full
  `articles` materialisation, `duplicate_groups` references and the final `group`
  and `article` loop values while starting a second unrestricted
  `find({}).to_list(None)`. Two complete decoded collections were therefore
  reachable simultaneously. The pre-fix classification was **PRIMARY CAUSE
  STRONGLY INDICATED**.
- **Implementation:** commit `49e5fe4` set `group`, `article`, `duplicate_groups`
  and `articles` to `None` immediately after duplicate processing and before the
  second read. Queries, thresholds, archive ordering, Manual Review safeguards,
  scheduler behaviour and Editorial Similarity were unchanged.
- **Tests:** five focused lifecycle regressions and 28 related cleanup, auth,
  memory-observability and live-pool regressions passed; compilation and diff
  checks also passed.
- **Deployment and production result:** Render automatically deployed `49e5fe4`
  before the 7 August 12:00 run. Three normal runs completed without OOM: second
  read increases were 29.4 MB at 12:00, 8.6 MB at 18:00 and 40.7 MB at 8 August
  06:00, compared with 63.4 MB pre-fix. The high-start 8 August run ended at
  473.6 MB, 38.4 MB below the ceiling. Cleanup semantics remained active and all
  three runs removed zero records.
- **Conclusion/follow-up:** the immediate duplicate-cleanup simultaneous-list OOM
  risk is operationally mitigated. This is not proof that all memory risk is gone;
  full unrestricted reads, visible-pool growth, allocator high-water behaviour,
  provider decode buffers and newsletter workloads remain monitoring concerns.
- **Sources:** [Production Timeline](../PRODUCTION_TIMELINE.md), [Open Findings](../QA/OPEN_FINDINGS.md), Git `49e5fe4`; authenticated Render evidence reconciled 8 August.

## Failed, reverted and deferred work

### Rolled-back homepage and feed experiments

- March source-pool expansion and archived-pool fills were reverted (`2f7b218`,
  `80f4d81`, `e0a0a37`) after destabilising allocation semantics.
- April global feed-image normalisation was reverted (`27c5a57`), while cache/header
  improvements were retained.
- Guide and monetisation surfaces were repeatedly feature-gated when article or
  homepage stability was at risk (`93d386a`, `89fa840`).
- **Sources:** preserved state, failed-attempt appendices; cited Git commits.

### May verification rollback and Gemini pause

The 24–25 May verification branch introduced multiple fallback, Manual Review and
Gemini checks, then explicitly reverted them when the combined behaviour was unsafe
or unstable. Later work restored a narrower Perplexity and Admin OpenAI path. Gemini
did not become an authoritative production gate.

- **Sources:** preserved state, 24–26 May rollback sections; Git reverts including
  `d0e8399`, `7fef821`, `a796691`, `30027b3`.

### Deferred Version 2 brand refresh

On 31 July, `dcde9ba` recorded that a broad Version 2 visual refresh was deferred in
favour of operational evidence, analytics and editorial work. Existing Version 1
brand assets remained authoritative at HEAD.

- **Sources:** July log, “Version 2 branding decision”; Git `dcde9ba`.

### Deferred operational work

Navigation redesign, broader Admin row/dialog consistency, threshold-driven
Editorial Similarity UI, Similar Stories, speculative indexes and unmeasured memory
optimisation were not approved at HEAD.

- **Sources:** preserved state, final July/August sections; Git `42736f9`, `1601ae4`.

## Unreconciled history

- The requested ChatGPT export has not been received.
- Codex tasks and production investigations have not been systematically preserved.
- Production evidence after commit `49e5fe4` is outside this reconstruction unless
  already present in repository sources. The 7–8 August duplicate-cleanup evidence
  is reconciled in the production and QA records.
- Historical PDFs named in the preserved state are missing from the checkout; the
  tracked `CheshireToday_Project_History.pdf` remains unreconciled.
- Some historical paragraphs say “deployed” without a matching retained Render
  event. They remain historical claims, not current deployment assertions.
- The July engineering log includes August entries; it is retained unchanged and
  treated according to the date of each entry.
