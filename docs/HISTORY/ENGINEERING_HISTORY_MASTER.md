# Cheshire Today — Engineering History Master

## 5 October 2026 reconciliation boundary

This continuation records committed engineering through
`c4a977bbf6e7b118375bca5b5ab9ac4be48c6d40`, following documentation commit
`109134b`. Production evidence now includes the 5 October 12:00 post-hotfix
natural-run acceptance, **APPROVED WITH OBSERVATIONS**. Earlier
dated records retain their original evidence boundaries. Full chat/PDF recovery
remains incomplete; see [Source Register](SOURCE_REGISTER.md).

### 5 October — mixed local publication-date correction

The 06:00 natural import on `b83d2c3` failed during local aggregation with
`'<' not supported between instances of 'datetime.datetime' and 'str'`.
Cleanup/wrapper completion did not make that import successful. The exact failure
was reproduced locally by a RED regression before `c4a977b` (`Handle mixed local
feed publication dates`). Its `_published_date_sort_key` accepts datetimes and
ISO strings, treats naive values as UTC, and puts missing/invalid values at an
aware `datetime.min`. All three local groups use comparable keys newest-first;
stored source dates and Cheshire Live/other/Nub group priority are unchanged.
The committed regression is in `tests/test_cheshire_east_media_hub_adapter.py`.

Supplied GREEN verification: focused adapter suite **8 passed**; broader gate
**227 passed, 6 known warnings**; compile and `git diff --check` passed. These
are preserved engineering results, not tests rerun by this documentation task.
The corrective deployment became Live at 06:42:11 BST; the first post-hotfix
natural article run, at 12:00, completed in 124.16 seconds with no recurrence and
with local processing completed. Gate closed **APPROVED WITH OBSERVATIONS**.
See [Production Timeline](../PRODUCTION_TIMELINE.md#5-october-2026--mixed-date-hotfix-production-acceptance)
for runtime counts, resource evidence and the retained source-count/editorial
limitations; unrelated memory/QA and historical-recovery gates are not closed.

### Selective August–September implementation backfill

These are commit-backed implementation notes, not newly recovered deployment or
test-run evidence:

- `275e131` (9 August): corrected legacy SEO article canonical identity, with
  route regression coverage in `test_article_canonical_routes.py`.
- `9bf8877` (27 August): streamed visible-pool planning state in
  `cap_visible_articles`, with expanded `test_article_live_pool_cap.py` coverage.
  Implementation is complete; memory improvement and OOM closure must not be
  inferred from the commit alone.
- `f0f1a00`, `54702d6`, `5ec0bdf` (21 August): introduced backend commercial
  events, the frontend measurement hook/transport, and the contextual article
  recommendation component/configuration. Later Commercial Trust and homepage
  guide measurement build on these foundations; their existing acceptance
  records are not repeated here.
- `de87f23` (7 September): added safe named article links in ArticlePageV2 and
  focused content-link tests. No separate deployment date/count is asserted.

## 1–4 October 2026 — editorial precision, presentation and source diversity

### Evidence-led depth and safe excerpts

`41444da` changed only Perplexity generation prompts and direct mocked service
tests. Ordinary evidence-rich reports are guided toward 400–650 words; substantial
stories may reach 700–900. These are not quotas: shorter accurate output is
permitted, with no invented/repeated filler. Primary-source-led research and
verified names, dates, figures, chronology, attributed responses and confirmed
next steps are encouraged. Retry refusal pressure was replaced with evidence-led
wording, including empty output when no usable verified report exists. Provider
parameters, retry conditions and downstream public-length/editorial routing were
not redesigned. No new QA count is reconstructed from the number of test functions.

`b98a49e` separated safe display excerpts from raw preview/body classification.
`select_rss_excerpt` cleans full source text and selects complete sentences with
a soft size target; it can fall back to available detailed text or return empty,
without another provider call or arbitrary ellipsis. Stored-summary card/intro
rendering no longer hard-slices another preview. Raw continuation classification,
body generation and routing remain distinct. The existing Project State checkpoint
records 143 backend passes/12 skips and 485 frontend passes, plus build evidence;
these are historical records, not rerun results. Git proves the work is committed,
not still local/uncommitted. Existing production articles were not regenerated.

### Presentation and navigation corrections

`74b2a0d`, `dd17d6d` and `40005e8` form a bounded homepage/category/article phase:
UK fuel-supply impact wording gained a narrow homepage-filter exception; dedicated
category headers now use canonical Home/Local/UK/Business destinations; desktop
articles gained up to four distinct further-reading headlines after existing
related/sponsor content. The sidebar reuses existing fetched records and excludes
main/related/current items rather than adding another feed request. Project State
retains their detailed RED/GREEN, frontend/build and scope evidence. These changes
do not establish a broader editorial-filter or mobile-layout redesign.

### Eligibility before generation

`113c150` routed dated Guardian politics liveblog URLs to hidden Manual Review
before generation, using the bounded source-format reason and existing category
accounting. It removed accidental dependence on short output as a format filter,
without changing the 1,000-character floor, provider prompts or general liveblog
policy. Existing Project State records 27 focused, 148 requested regression and
89 additional passes; those are preserved checkpoint results.

`b27a7f1` addressed the longstanding Heswall false positive: Chester Road plus
feed `location=chester` could satisfy specificity despite the Wirral subject.
The shared deterministic helper requires the bounded Heswall/Wirral Council/
Chester Road conflict and absence of independent locality evidence. It routes
eligible source-stage candidates through existing hidden review before generation
and protects final locality validation when evidence emerges later. Road names
are not globally banned; feed-location storage is unchanged. Early review leaves
Local target/topic/public capacity available; final review preserves existing
Local/topic accounting while consuming no public slot. Tests cover the confirmed
case and legitimate/background counterexamples; no historical record was repaired.

### Bounded source expansion and test isolation

`2cd1b6e` added bounded Nub News discovery. `d0b14f5` added Chester and Wilmslow;
`b515af0` set selection to at most three newest candidates per configured hub.
Final hubs: Macclesfield, Sandbach, Congleton, Nantwich, Crewe, Alsager, Chester
and Wilmslow. Existing Local feed priority and downstream eligibility remain
authoritative; candidates are not guaranteed publication.

`b83d2c3` added Cheshire East Council Media Hub index/release discovery. The
production call fetches at most five newest release pages, handles index/article
errors safely, skips incomplete parsed records and does not invent `location` or
`priority_location`. Ordinary service instances disable both new adapters by
default; the production global instance explicitly enables them.

**Supplied engineering incident evidence:** the initial unconditional Cheshire
East integration caused unrelated tests to perform live requests and contaminated
expected result lists. Constructor feature-gating fixed isolation: disabled by
default, explicitly enabled in production, without weakening test expectations.
The committed implementation/tests establish the final gate; the transient failed
run is supplied evidence, not independently recoverable from the final Git diff.

**Supplied pre-deployment QA:** focused source tests passed; broader regression
226 passed with six known warnings; Python compilation, `git diff --check` and
pre-push remote drift checks passed. Protected files remained untouched. No new
tests/providers were run to reconcile this account.

Source-investigation decisions and their supplied provenance are recorded in
[Editorial Evolution](../EDITORIAL_EVOLUTION.md#october-2026--separate-discovery-depth-excerpts-and-eligibility).
The five locality/source commits were deployed together at `b83d2c3`; see
[Production Timeline](../PRODUCTION_TIMELINE.md#4-october-2026--combined-locality-and-source-expansion-deployment).
Deployment/health were verified at that checkpoint. The subsequent 06:00 failure,
`c4a977b` correction and accepted 12:00 natural run are recorded above; per-hub
selection and exact Cheshire East contribution remain runtime evidence limits.

## 24–26 September 2026 — newsletter evidence and documentation reconciliation

Implementation sequence verified in Git:
`3763aa6` accepted-send cold-report correction; `0acbe8a` production evidence;
`34ecf74` suppression eligibility; `5afd7b1` reconciliation tooling/evidence;
`8ed1984` campaign Feedback-ID support. Earlier local/uncommitted slice labels
describe historical checkpoints, not the state of these capabilities today.

Application Feedback-ID changes preserve recipient selection, scheduling,
tracking and unsubscribe validation. Historical verification: 120 focused tests;
1,903 newsletter/Weekly regression tests, 422 existing warnings. These are
recorded results, not tests rerun during this documentation task.

Suppression reconciliation succeeded for 815 records after a rolled-back BSON
precision mismatch. Owner-supplied evidence confirms current SHA Live/health 200,
but custom Feedback-ID was replaced in delivered Gmail source on both tested
Resend endpoints. Support response pending; end-to-end FBL not achieved.

The September 26 audits establish historical Gmail click sparsity, uncertain
human-open attribution and the exact 262-recipient accepted-opportunity threshold
crossing behind 739→1,001 cold counts. No new deactivation or recovery rule follows.
See [dated aggregate evidence](NEWSLETTER_DELIVERABILITY_2026-09-26.md) for full
provenance, historical May reconstruction and remaining gaps. Commercial work is
a separate future stream; this reconciliation changes documentation only.


> **Reconstruction status:** repository-evidence history reconciled through
> `8ed19846ccf9242b646ea38440d71e1f85f59141` on 26 September 2026. ChatGPT export,
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

#### Duplicate-cleanup streaming and separated memory validation — 9–11 August

- **Problem:** Current-RSS markers showed that both cleanup collection scans still
  materially increased live process memory after the initial lifecycle fix.
- **Implementation:** `fd7cc82` added current RSS; `c06c837` streamed/projected the
  short-content scan with full candidate re-fetch; `cd3f093` streamed/projected the
  first duplicate scan with group-wide re-fetch/revalidation; `0cdc089` added the
  thirteenth marker separating first-pass Stage 2; `1811430` removed full joined
  and joined-lower strings from short-content qualification without semantic change.
- **Production evidence:** The 11 August 06:00 run isolated first-pass Stage 2 at
  -0.9 MB and the short scan at +26.0 MB. The 12:00 natural run on `1811430`
  completed in 94.63 seconds with current RSS 202.3→338.6 MB. First scan, first
  Stage 2, visible pool and short scan were +44.2, 0.0, +33.6 and +28.5 MB.
- **Conclusion:** Both unrestricted cleanup reads were removed and first-pass Stage
  2 is not the current hotspot. The string change is semantically safe but its
  first production comparison is similar, not materially improved. Cumulative
  memory remains Monitoring/Medium and another natural run is required before a
  further code target is selected.
- **Sources:** [Production Timeline](../PRODUCTION_TIMELINE.md), [Open Findings](../QA/OPEN_FINDINGS.md), Git `fd7cc82`, `c06c837`, `cd3f093`, `0cdc089`, `1811430`; authenticated Render evidence reconciled 11 August.

#### Admin credential rotation and QA-SEC-001 closure — 11 August

- **Reason:** current-tree containment did not neutralise the production Admin
  password retained in reachable Git history; history was not rewritten.
- **Action:** only `ADMIN_PASSWORD` was rotated on Render service
  `cheshiretoday-migration-` (`srv-d5virmm3jp1c73c9d6tg`).
  `ADMIN_PERMANENT_TOKEN` remained separate and unchanged. Nine pre-rotation
  Admin tokens were invalidated, and the service restart removed old-instance
  in-memory sessions.
- **Deployment and verification:** final deployment `dep-d9tiku142hec738apl80`
  ran revision `3b3f4c9` on instance `6xgfs`. Replacement login and bearer-token
  verification passed; the historical password was rejected with HTTP 401;
  public health returned 200. Build, startup, Mongo and scheduler checks were
  healthy with no OOM, restart loop or material 5xx evidence.
- **Result:** `QA-SEC-001` closed as **ROTATION/REVOCATION PROVEN**. Reachable Git
  history still contains the revoked credential, but production no longer accepts
  it. No secret value, hash or derivation is preserved here.
- **Sources:** [Open Findings](../QA/OPEN_FINDINGS.md), [Production Timeline](../PRODUCTION_TIMELINE.md); authenticated Render/Admin/Mongo verification reconciled 11 August 2026.

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

### QA-SEC-002 credentialed CORS closure — 12 August 2026

The High-severity credentialed wildcard-origin finding was confirmed, corrected
and production-verified. Commit `b497635` introduced the reviewed explicit origin
list while retaining the existing credentials, methods and headers policy. Eight
focused CORS tests passed. Render deployment `dep-d9u594oae00c73bs1lvg` became
live on instance `qmqjs` at 12:12:56 BST. Production returned the canonical origin
for an approved preflight and rejected `https://evil.example` without ACAO or
wildcard reflection. Fresh Admin login compatibility, health and public frontend
smoke checks passed, with no startup, Mongo, scheduler, OOM, restart-loop or
material 5xx regression. `QA-SEC-002` therefore closed.

- **Sources:** Git `b497635`; focused CORS regression evidence; authenticated
  Render/Admin and bounded production preflight verification on 12 August 2026.

### Article scheduler lock fail-closed closure — 13 August 2026

- **Finding and implementation:** `CT-QA-2026-003` identified that article lock
  seed/acquisition exceptions warned and continued without ownership. Commit
  `d8943e8` changed only that exception path to log an error and return.
- **Tests and deployment:** Seven focused tests covered seed and atomic-acquisition
  exceptions, held locks, successful/stale acquisition and unchanged scheduler
  registration. The commit deployed on Render instance `qc88z`.
- **Natural verification:** The 18:00 run acquired `article_gen_2026081317` once,
  executed one generation and cleanup sequence, and completed in 105.98 seconds
  with APScheduler success and health 200. No production lock failure was induced;
  hermetic tests verify the fail-closed branch and the natural run verifies normal
  compatibility. `CT-QA-2026-003` closed.
- **Memory observation:** All thirteen markers were present. Current RSS rose
  130.7→305.5 MB (+174.8 MB), with +32.7 MB visible-pool, +41.0 MB first duplicate
  Stage 1, 0.0 MB first Stage 2 and +42.0 MB short-content scan intervals. No OOM
  or restart occurred, but the worse observation does not prove a trend;
  `QA-OPS-001` remains open pending another normal run.
- **Sources:** Git `d8943e8`; [Open Findings](../QA/OPEN_FINDINGS.md);
  [Production Timeline](../PRODUCTION_TIMELINE.md); authenticated Render logs and
  health evidence reconciled 13 August 2026.

### Bounded event-anchor shadow verification — 14–15 August 2026

- **Reason and calibration:** `CT-QA-2026-004` records that different publishers,
  titles, images and URLs can describe one event without sharing deterministic
  identity. A 27-pair labelled matrix showed the existing scores/bands and tested
  composite were unsafe for routing.
- **Implementation:** Commit `5e8f0ef` added bounded deterministic entity/event-
  phrase, typed quantitative, ordered/outcome-aware stage, format/angle and exact-
  boundary locality evidence under `phase2a_event_anchors_v1`. Scorer weights,
  bands, the 50+50 corpus, 20-item shortlist and publication behaviour did not
  change; the feature remained scheduled-only, advisory and non-mutating.
- **Deployment and natural verification:** Deployment `dep-da01o93ncjis738c7m8g`
  became live on instance `65q7v` at 09:01:05 BST on 15 August. The natural 12:00
  run acquired one lock, completed once in 98.70 seconds and remained healthy.
  Twenty shadow evaluations (19 scored, one `no_match`) all used the new version
  and `scheduled_log_only`; 17 emitted compact evidence codes.
- **Conclusion/follow-up:** The observed codes were limited to format, source,
  same-run and locality evidence; no high-specificity positive or future-compatible
  event identity appeared. Locality remained noisy, including an ambiguous garden-
  waste-fire pair. Publication state was unchanged. Current RSS rose 129.8→291.9
  MB, with no observable material event-anchor regression, while `QA-OPS-001`
  remains open. CT-QA-2026-004 remains open for labelled natural calibration and
  routing remains separately gated and unapproved.
- **Sources:** Git `5e8f0ef`; [Open Findings](../QA/OPEN_FINDINGS.md);
  [Production Timeline](../PRODUCTION_TIMELINE.md); authenticated Render, scheduler,
  shadow-log and health evidence reconciled 15 August 2026.

### Allocator diagnostics and short-content cursor batching — 17–21 August 2026

- **Problem and diagnosis:** Recurrent Starter OOM evidence and heap/RSS markers
  showed that released Python heap did not imply returned process RSS. Commit
  `0052b68` added a hermetic, process-isolated allocator/PyMongo diagnostic harness;
  its synthetic short-content workload supported testing smaller cursor batches
  without treating local results as proof of Motor production behaviour.
- **Isolated implementation:** Commit `b3550c0` applied `batch_size(250)` only to
  the projected short-content cursor in `_remove_duplicates_internal()`. The first
  duplicate cursor, visible-pool materialisation, queries, projections, protection
  and qualification rules, Stage 2 revalidation, archive-before-delete, scheduler
  and marker contracts were unchanged.
- **Natural production evidence:** On instance `zthtp`, the 20 August 18:00 run
  scanned 4,249 records in 2.68 seconds with short-scan RSS 247.5→251.4 MB
  (+3.9 MB) and completed in 101.62 seconds. The 21 August 06:00 run scanned 4,264
  records in 2.65 seconds with 381.3→382.3 MB (+1.0 MB) and completed in 92.06
  seconds. Both acquired one natural-run lock, removed zero records, completed
  normally and remained healthy. The +2.45 MB mean compares with the supplied
  pre-batch mean of about +39.5 MB and range of about +26 to +51 MB.
- **Decision and limits:** The strong replicated isolated improvement supports a
  **provisional keep** of `batch_size(250)` with no material runtime regression.
  Heap release plus RSS retention remains, cumulative baseline risk is unresolved,
  and archive-before-delete was not dynamically exercised because both runs had
  zero removals; unchanged code and regression tests support its preservation.
  `QA-OPS-001` remains **HIGH OPEN — RECURRENT PRODUCTION OOM CONFIRMED**. Standard
  2 GB remains temporary mitigation. The 21 August visible-pool interval added
  +57.7 MB and requires a separate evidence-led review before any change.
- **Sources:** Git `0052b68`, `b3550c0`; [Open Findings](../QA/OPEN_FINDINGS.md);
  [Production Timeline](../PRODUCTION_TIMELINE.md); authenticated Render scheduler,
  memory-marker and health evidence reconciled 21 August 2026.

### Admin first-byte indexing protection — 26 August 2026

- **Finding:** `QA-SEO-002` retained a Medium gap after rendered metadata cleanup:
  the Admin entry route lacked proven first-byte noindex protection and crawler-
  specific robots exclusions were not explicit.
- **Implementation:** Commit `24f381e` added the exact response directive
  `X-Robots-Tag: noindex, nofollow, noarchive` for `/admin` and `/admin/`, retained
  first-byte protection on unsupported nested Admin paths, and explicitly
  disallowed `/admin` and `/api/admin/` for wildcard, Googlebot and Googlebot-News.
- **Verification:** 11 focused, 74 related and 9 sitemap tests passed with
  compilation and diff hygiene. Deployment `dep-da7ala710e5c738ovtm0` on instance
  `824s7` (Standard, 2 GB RAM / 1 CPU) was production-verified: GET/HEAD Admin
  routes and the nested-path 404 behaved as designed, public SEO and both
  sitemaps were preserved, unauthenticated Admin verify remained 401, health was
  200 and no material runtime anomaly was observed.
- **Outcome:** `QA-SEO-002` is **CLOSED — PRODUCTION VERIFIED**. Robots and
  `X-Robots-Tag` are indexing controls only; Admin authentication and API
  authorization remain the security boundary.
- **Sources:** Git `24f381e`; [Open Findings](../QA/OPEN_FINDINGS.md#qa-seo-002);
  [Production Timeline](../PRODUCTION_TIMELINE.md); production verification on
  26 August 2026.

### Public search accessibility closure — 27 August 2026

- **Finding:** `QA-A11Y-001` originally recorded placeholder-only search naming, pointer-only desktop results and absent no-results feedback.
- **Implementation:** Commit `dcd5cfa` (`Improve public search accessibility`) added durable `Search news` labels, native article links on desktop/mobile, native Tab/Enter and browser modifier semantics, Escape dismissal with focus retention, polite status feedback and stale-request cancellation. It deliberately did not add a custom combobox or arrow-key selection model.
- **Verification:** Seven focused, 42 related and 367 total frontend tests passed with a successful production build and diff check. Render deployment `dep-da82j9uk1f9s73dgc1mg` ran on Standard instance `9sflp` (2 GB RAM / 1 CPU). Desktop and 390×844 mobile checks verified naming, links, focus, status/no-results feedback, layout and public-route preservation; health returned HTTP 200 without observed browser-console, Mongo/scheduler, OOM, restart or material 5xx failure.
- **Decision:** `QA-A11Y-001` closed as production verified. Failure messaging and stale-response protection were verified from deployed immutable code/tests rather than a manufactured production failure. No screen-reader certification, full WCAG conformance or site-wide accessibility closure is claimed.
- **Sources:** Git `dcd5cfa`; [Open Findings](../QA/OPEN_FINDINGS.md#qa-a11y-001); [Production Timeline](../PRODUCTION_TIMELINE.md); authenticated Render and public-browser verification 27 August 2026.

### Homepage materialisation optimisation — 30 August–4 September 2026

- **Diagnosis and design:** Five production timing requests on diagnostic commit
  `15695cb` measured median handler 1,081.639 ms, including count 123.102 ms,
  Local materialisation 366.840 ms and UK materialisation 248.688 ms. A read-only
  candidate replay found deepest contributing Local/UK positions 42/58. Although
  60/60 and 80/80 matched, 100/100 was selected for safer operational headroom;
  force-live reduction was rejected and fallback remained unchanged.
- **Implementation:** Commit `70057e1` skips unused `count_documents()` and caps
  Local and UK materialisation at 100 only for the exact public 80-item homepage
  list request. Visibility, predicates, projections, sorting, filtering, 2:2
  interleaving, incident/crime rules, force/fallback, boosting, dedupe, slicing
  and response contracts remain unchanged.
- **Production verification:** Deployment `dep-dabrjseq1p3s73fsvf7g` was initially
  verified on instance `xmx4p`. Five gated sequential requests on deployment
  `dep-dad5jv2jnfac73ehqh20`, instance `cs5n2`, reduced median handler to
  708.314 ms (-34.5%), TTFB to 1,544.086 ms (-17.4%) and total to 1,587.383 ms
  (-16.3%). All returned HTTP 200 and 79 articles with stable bytes, 33 force
  candidates, 80/79 pre-dedupe/final and fallback 0/5; exactly five markers were
  recorded without traceback, material 5xx, OOM/137 or unexpected restart.
- **Decision and limit:** **MATERIAL IMPROVEMENT — QA-PERF-001 OPTIMISATION
  VERIFIED.** This is bounded five-request evidence, not statistical or site-wide
  closure. The gate was removed by `dep-dad5pcgn74is73dd4mj0`; SHA `70057e1`
  remained live on instance `gldsq` with health 200. The 839.327 ms median
  TTFB-minus-handler residual remains compositionally unmeasured and requires a
  separate read-only investigation before any further optimisation.
- **Sources:** Git `15695cb`, `70057e1`; [Open Findings](../QA/OPEN_FINDINGS.md#qa-perf-001);
  [Production Timeline](../PRODUCTION_TIMELINE.md); authenticated Render logs and
  bounded production comparison reconciled 4 September 2026.

## 23 September 2026 — Direct newsletter unsubscribe production acceptance

The CT-DEC-021 implementation chain was pushed/deployed at `2f40374` and completed
functional production acceptance: identity/index, one-recipient delivery/native
headers/DKIM, Apple Mail native and human unsubscribe, idempotent inactive replay,
challenge-backed reactivation/version rotation, stale-token rejection, active
preferences/consumed-challenge rejection and transactional header-free welcome.
The [Production Timeline](../PRODUCTION_TIMELINE.md#23-september-2026--ct-dec-021-functional-production-acceptance)
owns the detailed owner-supplied evidence and its limits. No production operations
were repeated during documentation reconciliation.

**FUNCTIONAL PRODUCTION ACCEPTANCE COMPLETE — UPSTREAM QUERY-LOG PRIVACY GATE OPEN.**
**POTENTIAL QUERY LOG EXPOSURE** remains: unavailable upstream Request Logs and
observed client logging of an already-stale credential URL are not resolved by
functional success. No sensitive values are retained and QA accounting is unchanged.

Later pushed `40304fc` changed welcome coverage copy only; reported verification
was 11 passed, 2,848 deselected and diff whitespace passed. Earlier receipt does
not verify the later wording or establish this commit's deployment.

## 26 September 2026 — Commercial Trust Phase 1 local implementation

Baseline: `full-scrape-prod`, `40b3da277b3b9b12f6a99673d185618c30cdd539`.
Initial tracked tree clean; protected untracked `AGENTS.md` and the full August
Project State archive preserved. This implementation is local/uncommitted and
undeployed; no advertiser or production data changes were performed.

Confirmed defects: AuthorityPage filtered editorial options by affiliate-link
availability and automatically featured the first linked provider; Amazon search
fallback cards displayed hard-coded prices/ratings and selection/deal claims;
Amazon tag handling used substring recognition and appended duplicate tags;
quick-comparison/Amazon links lacked the first-party measurement now used here.
The current AuthoritySection schema has no explicit editorial-pick field.

Changes: all named tool entries remain in configured order, unlinked options have
no CTA, the automatic featured recommendation is removed, and the provider-list
heading is neutral. Amazon search/fallback claims are hidden without changing
product data, rotation or inventory. URL parsing recognises only amazon.co.uk and
www.amazon.co.uk over HTTP(S), replaces the tag, preserves other parameters, and
leaves malformed/non-Amazon inputs untouched. No Awin/CJ URL or ID changes.

CommercialOutboundLink reuses useCommercialCardMeasurement and the existing
/api/commercial-events schema. It emits rendered/viewable/clicked with existing
per-navigation deduplication and keepalive click submission. Guide placements are
guide_quick_comparison and guide_provider_list; the live Amazon placement is
homepage_sidebar. Existing dormant widget variants use amazon_inline, amazon_end
and amazon_mobile without being added to any page. Payload fields are card_id,
provider_id, placement_id, use_case, destination_type, destination_id,
rule_reason_code, variant_version, disclosure_version, existing random session/
page-view IDs and device_class; article fields are null for these placements.
No affiliate URL, query, subscriber identity or conversion is recorded. Existing
guide-provider third-party calls are replaced by this bounded first-party path;
homepage guide_click and contextual-card tracking are unchanged. Click failures
do not cancel navigation.

Affiliate rel/disclosure is based on recognisable current network/link patterns,
not merely the page monetisation flag; plain merchant destinations retain normal
external-link attributes. This does not establish programme validity. The broader
disclosure page's future-partner wording is intentionally left for content review.

Verification: initial test harness needed a local Badge mock for the existing
Jest alias limitation; behavioural red run then showed 9 failures / 3 passes.
Final expanded focused suite: 28 passed. Five related commercial suites: 58
passed. Complete frontend: 43 suites / 440 tests passed. Production frontend
build compiled successfully. Warnings: ReactDOMTestUtils.act deprecation and
eight-month-old Browserslist data; synthetic fallback logging appeared as expected.
No real affiliate navigation or event transmission was used in tests. Diff
whitespace check passed. No production acceptance or revenue improvement claimed.

Independent review then identified a name-only filter incompatible with valid
title-only AuthoritySection entries. The minimal local correction resolves trimmed
name, otherwise trimmed title, once on copied tool entries; blank labels are
omitted and configured order is unchanged. Six added regression cases cover
linked title-only entries (absent/empty/blank name), unlinked title-only entries,
name precedence, source preservation, measurement labels and actual mixed DOM
order including invalid entries. Red: 5 failed / 29 passed. Green: 34 focused,
64 related and 446 full frontend tests across 43 suites; production build passed.
Project State committed-HEAD metadata now distinguishes `40b3da2` from the
unchanged documented production revision. Phase 1 remains unstaged/uncommitted,
unpushed and undeployed. No affiliate relationship or destination changed.

## 27 September 2026 — Commercial Trust production acceptance and affiliate correction

The preceding local-only checkpoint is historical. Phase 1 was committed as
`3a9b81e7b9dc9e1cf57fd7347b02e9d8bea5122e` (`Improve commercial trust and outbound
measurement`), deployed Live in `dep-dasccr0ae00c73avpep0`, and production-accepted.
Fresh local/remote SHA, clean tracked tree, protected untracked set and HTTP
200/healthy checks passed before the separately authorised data operation.

An exclusive private backup preserved exactly the two original target documents
as BSON outside Git, with 0700/0600 permissions, fsync and exact round-trip checks.
A snapshot transaction reread the originals, resolved tool indices by trimmed
name/title, guarded complete original state and applied minimal `$set` updates.
EMPLA 127533's link was cleared after its verified 25 September closure. Emma
Sleep's incorrect 79506 (Emma App) link was cleared, monetisation set to `none`,
and only its approved neutral provider copy substituted. Both updates matched
and modified one record, exact expected post-images passed and commit was
acknowledged: two records, four business fields, two `updatedAt` timestamps.

The complete education control document and API/crawler outputs stayed identical;
CloudLearn and Alison links were not changed. API/crawler checks passed 3/3 and
isolated 1440px/390px guide checks passed 6/6. Two protected browser passes blocked
22 commercial requests, allowed zero, used no synthetic clicks and observed no
runtime errors or horizontal overflow. Temporary harness corrections resolved the
control's full label (`Alison Free Online Courses`) and provider-label div selector;
neither required an application change or transaction retry. No replacement
affiliate programme, Awin/CJ change, code change or sponsor change accompanied the
operation. Alison UK monetisation remains unresolved. Rollback needs separate
approval. The follow-up commit is documentation-only and is not pushed.

See [Production Timeline](../PRODUCTION_TIMELINE.md#27-september-2026--commercial-trust-production-acceptance-and-affiliate-correction)
for the production evidence boundary. Historical Phase 1 test counts were not rerun
for this data/documentation-only operation.

## 27 September 2026 — Virtual-office editorial baseline correction

Initial local/remote `full-scrape-prod` matched `8c8788f86bc88a4ee5f9ea8039014ad46d5d37f0`;
tracked tree was clean with only the two protected untracked files. Render now
showed that documentation revision Live in `dep-dasdclgae00c73b0g7ag`; public
health was HTTP 200/healthy. No deployment was triggered by this task.

Exact production preconditions and public API equality passed for the single
`best-virtual-office-services-small-business-uk` record. A private one-document
BSON backup outside Git passed exclusive creation, permissions, fsync and exact
round-trip validation. A snapshot transaction used complete original-state guards,
no upsert and only a minimal `$set`: 13 approved editorial fields plus `updatedAt`.
Matched/modified 1/1, complete expected post-image verified, commit acknowledged,
and majority readback verified the same exact post-image without retry.

The unsupported 4.4 rating and targeted ranking/suitability claims were removed.
Both providers, stored labels/order, affiliate URLs/IDs 36030/83191, affiliate
monetisation, route, placements, measurement and all unrelated fields remained
unchanged. API/crawler checks and 1440px/390px browser acceptance passed. Two
intercepted passes blocked 22 commercial requests, allowed zero through, generated
no clicks and found no runtime errors or overflow. Temporary browser assertions
were corrected for the separate site-brand h1 and the existing exact
`sponsored noreferrer noopener` rel; no production change was needed. Frontend
disclosure was preserved; crawler HTML has no existing disclosure block.

This Mongo-only correction establishes the clean virtual-office experiment
baseline, not improved commercial performance. Only governance docs changed in
the repository; no application code, account, configuration or deployment changes.
The documentation-only follow-up is not authorised for push. Detailed evidence:
[Production Timeline](../PRODUCTION_TIMELINE.md#27-september-2026--virtual-office-editorial-baseline-correction).

## Unreconciled history

### 27 September 2026 — UX/commercial refinement batch 1 local verification

Baseline `f4fb2bd28060655c3d3e6465bfc8737d36b40e28`, branch `full-scrape-prod`,
clean tracked tree and only the protected untracked files. The bounded change
adds the existing article-completion condition to mobile More stories, removes
only desktop sidebar Latest / More from Cheshire Today, and removes only the
savings entry from `homepage_primary`. Main More stories data and presentation
counts, article thresholds/reset, related stories, sponsor/newsletter behaviour,
rotation/partitions and other registries are preserved. No redesign, Mongo,
guide-content, affiliate URL/ID, Amazon or measurement architecture change.

Red: 9 failed / 9 passed. Green focused: 25 tests / 3 suites; related: 101 / 10;
full frontend: 460 / 44, zero failures. Tests cover mobile collapse/expansion,
three-paragraph content, navigation reset, 639/640 transitions, preserved main
list order/count/expansion, sponsor genuine/absent/house/error behaviour, a real
sponsor fetch rejection, fixed-date rotation, unique destinations, partitions,
two-card density, retained non-homepage savings references and feature gating.
One initial assertion included CSS-hidden summary text; correcting its scope to
the body resolved the harness issue without production changes. Production build
passed; existing React act deprecation and eight-month-old Browserslist warning
remain. Full diff and whitespace checks passed.

Eight local built-page browser scenarios passed (390px and 1440px). All APIs used
local fixtures, with request interception installed before navigation: 12
first-party measurement attempts and 30 external requests were handled locally,
zero external requests forwarded, zero affiliate clicks/form submissions, no
horizontal overflow or runtime errors. The implementation was subsequently committed as `386887c` (`Improve article flow and reduce repeated promotion`), pushed and deployed Live on the exact SHA. Production health returned HTTP 200 / healthy. Isolated production-browser acceptance remained inconclusive because the temporary QA harness did not complete the intended article checks; no production defect was demonstrated and no rollback was indicated. Footer naming, homepage guide-strip first-party measurement and broader dedupe remain deferred.

- The requested ChatGPT export has not been received.
- Codex tasks and production investigations have not been systematically preserved.
- Production evidence through the 21 August 06:00 run on `b3550c0` is reconciled
  in the production and QA records. Later evidence remains outside this
  reconstruction unless already present in repository sources.
- Historical PDFs named in the preserved state are missing from the checkout; the
  tracked `CheshireToday_Project_History.pdf` remains unreconciled.
- Some historical paragraphs say “deployed” without a matching retained Render
  event. They remain historical claims, not current deployment assertions.
- The July engineering log includes August entries; it is retained unchanged and
  treated according to the date of each entry.


### Desktop lead-story hierarchy — 28 September 2026

- **Baseline:** deployed `386887c8119467ca0e6dc7eb3ec72718633afe81` on `full-scrape-prod`, tracked tree clean before implementation and only the two protected untracked files present.
- **Problem:** the desktop homepage hero placed its 4:3 image before the lead headline, pushing the primary editorial heading too far down the first viewport at common desktop sizes.
- **Implementation:** `HeroStoryCard.jsx` keeps one link and one `h1` and preserves DOM image-before-text order, but activates `lg:flex lg:flex-col` and `lg:order-first` so category/headline/meta render visually before the image from 1024px upward. Below 1024px remains image-first. `HomePageV1.jsx` applies the same desktop ordering to the loading skeleton. Image aspect ratios, crop, article selection/allocation, sidebar, commercial placements, guide rotation, backend and data are unchanged.
- **Tests:** new `HeroStoryCard.test.jsx` covers link/heading uniqueness, href/metadata, image identity/crop/eager/high-priority attributes, responsive ordering, missing image and image-error behaviour. Focused/related verification passed 53 tests; full frontend passed 465 tests; production build and whitespace checks passed.
- **Browser evidence:** isolated local built-page checks confirmed text-first at 1024px+ and image-first below; the current public lead headline fitted fully within 1440×900, with short/long headline and missing/failed-image scenarios also passing.
- **Deployment:** committed as `8ed336fe426a140d2cabb006b2c405611e22d594`
  (`Improve desktop lead-story hierarchy`), pushed to `full-scrape-prod` and
  confirmed Live on Render. Public health returned HTTP 200 / healthy. A final
  local 1440×900 geometry check measured the lead headline at 310–405px and the
  hero image beginning at 461px.

### Latest card consistency — 28 September 2026

The subsequent baseline was `8ed336fe426a140d2cabb006b2c405611e22d594`, with
deployment owner-reported. The owner visually identified mismatched Latest cards
after Popular Guides: the post-guide CompactArticleCard call omitted the
`editorial` variant. The existing uncommitted one-line fix was reviewed and kept;
its test mock exposes the variant and verifies the Latest cards all opt in.
No allocation, order/count, headline-strip, guide placement/rotation, navigation,
monetisation, backend or data change. Only the two expected source/test changes
and the two protected untracked files existed at task start.

HomePageV1: 3 passed; related: 54 passed / 5 suites; full frontend: 466 passed /
45 suites. Production build and whitespace checks passed. Existing React act,
fetchPriority and Browserslist warnings remain. No tests were weakened or added
beyond the supplied regression. Local production-build browser checks passed at
1440x900 and 390x844: Latest expanded 12→36 and 4→36 respectively, preserving
fixture order and guide insertion after six/four cards. Both sides used the same
editorial variant; no overflow or console errors. Fixture fetch responses and
restrictive CSP prevented production analytics; no affiliate clicks or production
navigation occurred. The correction was committed as
`f07c792ed7646b63f01e61bd054dc56db855d477`
(`Unify Latest card styling after guides`), pushed to `full-scrape-prod`, and
confirmed Live on Render. Public health returned HTTP 200 / healthy.

### Footer topic naming — 28 September 2026

Baseline `f3fff461bb406bbcaa00962e4933787c18e6c79f`, clean tracked tree and only
the two protected untracked files. Read-only inspection confirmed NewsFooter's
Guides group contained AI & Tech (`/category/ai-tech`) and Finance
(`/category/finance`), rather than guides. Renamed only that label to Topics;
destinations, structure, homepage guide headings, monetisation, SEO and data
remain unchanged. One new footer test verifies heading and navigation groups:
red before the change, green afterward. Related: 22 passed / 5 suites; full:
467 passed / 46 suites; production build and diff whitespace passed. Existing
React act/fetchPriority and stale Browserslist warnings remain. Isolated local
built-page desktop 1440x900 and mobile 390x844 DOM/visual checks confirmed the
heading, destinations and intact layout with no overflow or console errors.
No production navigation, analytics or affiliate clicks occurred during local
acceptance. The correction was committed as
`f5af386a9557ab079231628aa9d7af4aad25c857`
(`Clarify footer topic navigation`), pushed to `full-scrape-prod`, confirmed Live
on Render, and public health returned HTTP 200 / healthy.

## 29–30 September 2026 — homepage investigation, mobile refinement and guide measurement

### UK News homepage visibility investigation

A production-facing investigation examined several UK News articles that were present in the raw national feed but absent from the homepage feed. Read-only comparison confirmed that the affected records were not actually archived, not hidden in Manual Review and not force-live. The omission was attributable to the existing homepage UK editorial/noise filtering path rather than the late-September presentation changes.

A temporary candidate-depth experiment widened the exact homepage Local/UK candidate caps, but historical comparison established that the Friday baseline already used 100/100. The experiment was reverted and the 100/100 caps were restored. No UK filter-policy change was approved. The issue remains monitoring/investigation-only unless reopened with new feed evidence.

### Mobile homepage news-flow refinement

The mobile homepage was simplified to prioritise news rather than commercial guide interruptions. Commit `609d9d5` (`Simplify mobile homepage news flow`) removed Finance and Popular Guides from the mobile presentation and introduced the compact homepage newsletter while preserving desktop guide presentation. Commit `6afb0b3` (`Move mobile newsletter below Latest controls`) moved the compact newsletter below the Latest Show more/Show less control so the accepted mobile sequence is Latest stories → Show more/Show less → compact newsletter → Business & Finance.

Both revisions were pushed to `full-scrape-prod`, exact local/remote SHA equality was verified after deployment, public `/health` returned HTTP 200/healthy, and owner mobile production acceptance passed. Desktop behaviour remained unchanged by this refinement.

### First-party homepage guide measurement

Commit `d416580` (`Add homepage guide measurement`) added first-party measurement to the desktop homepage guide cards. Homepage guide inventory now has explicit stable `guideId` values. Finance and Popular Guides use distinct placements `homepage_finance_guides` and `homepage_popular_guides`; provider identity is `cheshire_today_guides` and destination type is `guide`.

The shared commercial measurement path records `rendered`, `viewable` and `clicked`. Viewability requires at least 50% intersection continuously for 1,000 ms while the document remains visible. Measurement is best-effort and deduplicated per navigation/card/event identity; failures do not block native same-tab navigation or the separate legacy `guide_click` analytics path. Payloads use bounded identifiers/classification metadata rather than raw guide URLs, titles, query strings or email-like values. Missing/invalid IDs or missing placement fail measurement closed without hiding cards.

Because CSS-only hiding would still mount guide components and could create false mobile rendered impressions, the homepage was tightened so Finance and Popular Guides are not mounted when `isMobileView` is true. Desktop still mounts both guide strips. Regression coverage explicitly verifies desktop selection/placement props and zero mobile guide-strip mounts.

Verification passed three focused suites with 23/23 tests, including dedicated rendered/viewable/clicked, dedupe, consent-separation, failure-safety, transport and device-classification coverage. The production frontend build compiled successfully; the only build notice was the existing stale Browserslist-data warning. `d4165800662131cded5cedf064a03cbdef21f531` was pushed after explicit approval, local and remote SHAs matched, public `/health` returned HTTP 200/healthy, and owner production acceptance confirmed desktop guide strips remained visible while mobile guide strips remained absent.

This establishes a first-party measurement baseline only. It does not establish CTR, conversion uplift, revenue performance or guide popularity.

## 6 October 2026 — sidebar and public-eligibility sequence

- `8a1b593`, `fdad609` and `6683413` delivered neutral article-related wording,
  truthful Finance allocation and a measured useful-guide sidebar; `7004994`
  recorded production acceptance. Live bundle evidence retained `Related
  stories` and `homepage_sidebar_guide` and removed old `More in ` wording.
- Investigation of the Scotland AI teacher, RAF Fairford, The Papers, Chester
  University and Scotland £5.8bn established that all five records were stored
  and visible to neither Archive nor Manual Review rules. The singular `school`
  mismatch caused the education false negative; `871874d` changed it to
  `schools?`. RAF Fairford remained an unchanged policy question.
- Historical comparison found no September Scotland/Glasgow exclusion. The
  approved regional rule was therefore new bounded policy. `a527e74` extracted
  shared binary public eligibility and aligned Admin Articles before
  pagination/counting without deleting records or changing force-live,
  rank/interleave or sensitive caps. QA passed 40 focused and 158 broader tests.
- Glasgow initially survived because incidental “one of the UK’s biggest ever”
  matched bare `UK`. `b413282` retained only explicit nationwide phrases and
  national institutions as rescue signals. Exact and incidental fixtures passed
  in the 43-test shared/Admin gate with compilation and whitespace checks.
- Read-only acceptance found health/homepage HTTP 200, 97 public articles, the
  four required exclusions absent, Chester present and no exact or >=0.85 title
  duplicates. One Drumcree/Portadown item lacked any configured regional marker;
  this and defence/security remain separate editorial decisions. The historical
  AST assertion `test_every_other_server_decision_matches_baseline` is not
  present at `b413282`; it is not current outstanding test debt.

## 7 October 2026 — bounded local-RSS and long-article sidebar completion

The archived Chester Standard retail-offence story exposed a narrow raw-RSS crime-classification miss. A broad post-rewrite rejection experiment was abandoned and reverted after demonstrating substring false positives; it never shipped. `36aeafe` instead added only bounded `retail offence(s)` coverage and word-bounded the existing stab expression to avoid “established”. Its fresh-candidate regression proves rejection before rewrite/publication. The wider affected gate passed 149 tests with six existing warnings, plus compilation and whitespace validation.

The 06:00 BST natural-run review found 19 active records in the checked window, zero active retail-offence matches and no return of the archived record. The second healthy natural review at 12:00 BST / 11:00 UTC found 26 active records and again zero exact active retail-offence matches. A new Cheshire Live city-centre-ban crime story was retained hidden with `needs_manual_review` / `manual_review_required`, while ordinary local planning/school stories passed, including auto-screened examples. Because duplicate/archive state could independently prevent the original archived record from returning, its absence is supporting rather than classifier-execution proof; the committed fresh-candidate regression supplies the direct evidence. One active BBC sexual-assault record does not establish public visibility because shared public eligibility remains a separate layer, so it is not classified as a confirmed defect.

`0e4c408` completed the long-desktop article-sidebar objective without reopening the earlier restraint decisions. Related stories and sponsor/newsletter remain normal-flow; only the unchanged maximum-four Further reading inventory is conditionally wrapped in `lg:sticky lg:top-24` as a direct child of the existing desktop-only aside. No request, allocation, duplicate exclusion, commercial inventory or mobile/tablet behaviour changed. The focused suite passed 36/36, related ArticlePage/component checks and the production build passed, and owner live visual acceptance confirmed the long-page result. The separately observed `PublicMetadataUniqueness` named-export mock defect predates this change and remains QA maintenance, not a production regression.

## 7 October 2026 — automatic rewrite depth and source-audit safeguards

Production examples established that non-empty rewrites around 165–183 words
could exceed the existing 1,000-character threshold and auto-screen, and that
source-verification narration could leak into public-style prose. QA-first work
at `efc79b1` retained the existing provider/retry and source-selection architecture
while making source research silent in both prompts, narrowly detecting confirmed
source-audit constructions, and requiring 200 words before an otherwise clean AI
rewrite can be automatically screened. Short rewrites remain stored in hidden
Manual Review; the rule is not a universal publication minimum and does not
trigger a second provider request.

The first production acceptance opportunity was the natural 18:00 BST run. Its
18-record checked window contained no auto-screened rewrite below 200 words and
no checked source-audit-language match. Four 127–192-word rewrites were retained
with `needs_manual_review` / `manual_review_required`; four 209–271-word clean
rewrites auto-screened; and a 281-word manual correction retained its existing
manual status. Acceptance is complete for the observed boundary, without
claiming that zero leakage in one run proves impossibility of future recurrence.

### Homepage sidebar publication freshness — 9 October

The Business, AI & Tech and Finance sidebar investigation established a
frontend selection defect rather than a public-eligibility or Top Stories
failure. The modules had no maximum age, their ordering could use import/ObjectId
freshness, and an unrendered legacy Finance pool reserved newer candidates. Bare
`rate`/`rates` and `save` also admitted non-financial stories. Backend supply
included old inventory but already contained newer suitable candidates.

`10d5a8a` (`Keep homepage sidebar articles fresh`) retained the existing
deterministic ordering but limited all three visible sidebar modules to valid
`publishedDate` values within seven days. It removed the dead Finance allocation
and its reservation side effect, narrowed only the confirmed Finance false-positive
terms, and preserved genuine financial and bounded property/planning matching.
Hero, Top Stories, public eligibility, backend/API behavior and the single shared
article request were unchanged.

The QA-first sequence recorded 13 intended RED failures and 17 passes, then
30/30 focused GREEN, 45/45 related component passes, 553/553 broader frontend
passes excluding documented `QA-MAINT-002`, a successful production build and
clean whitespace validation. After deployment, local/origin matched the full
`10d5a8a` SHA, health and homepage returned HTTP 200, and the owner accepted the
live Business, AI & Tech and Finance result. Acceptance is bounded to the
observed deployment and does not eliminate future inventory edge cases.
