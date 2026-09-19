# Cheshire Today — Current Operational State

> - **Status:** Concise operational source of truth; Version 1 is complete and the current stage is production hardening, QA and evidence-led reliability monitoring
> - **Operational authority:** This file, governed by [Project Master](PROJECT_MASTER.md)
> - **Primary branch:** `full-scrape-prod`
> - **Repository baseline:** `66fde1004a322d540bf9ac3197dab6b80152428b`
> - **Last repository reconciliation:** 19 September 2026
> - **Production-verification status:** Commit `66fde10` is live and Newsletter Funnel V1 production acceptance passed. The RSS-preview fix remains implemented/deployed with partial natural acceptance and its complete-replacement path remains unexercised. `QA-OPS-001` remains High Open
> - **Historical archive:** [Privacy-safe Project State archive](ARCHIVE/PROJECT_STATE_REDACTED_2026-08-06.md)
> - **Project master:** [Project Master](PROJECT_MASTER.md)
> - **QA register:** [QA Master](QA/QA_MASTER.md) and [Open Findings](QA/OPEN_FINDINGS.md)
> - **Roadmap:** [Roadmap Master](ROADMAP_MASTER.md)

## 1. How to use this file

This is Cheshire Today's current operational source of truth.

Read [Project Master](PROJECT_MASTER.md) first and this file second at the start
of every engineering, editorial, operational, SEO, newsletter, social or
commercial session.

This file contains only current operating state, protected boundaries, active
milestones and priorities. Detailed architecture, QA, decisions, history,
production incidents and roadmap evidence belong in their linked records.

The pre-rebuild state, including historical session logs and resume prompts, is
preserved for the repository in the [privacy-safe archive](ARCHIVE/PROJECT_STATE_REDACTED_2026-08-06.md).
The byte-exact source archive remains unchanged locally and excluded from Git; its
hash is registered in [Source Register](HISTORY/SOURCE_REGISTER.md). Chronological
history is maintained in [Engineering History Master](HISTORY/ENGINEERING_HISTORY_MASTER.md).

Do not append chat transcripts, historical checkpoints or temporary resume
instructions to this file.

## 2. Current repository state

- **Repository:** `CT29january26-new-website-migration`
- **Reconstruction branch:** `full-scrape-prod`
- **Current reconciled HEAD:** `66fde1004a322d540bf9ac3197dab6b80152428b`
- **Latest baseline commit:** `Add newsletter signup funnel analytics`

This is the repository and production baseline reconciled on 19 September 2026, not
an assertion that a later session remains at the same HEAD or deployment.

The intentional untracked/local-only set is limited to:

- `AGENTS.md`;
- `docs/ARCHIVE/PROJECT_STATE_FULL_2026-08-06.md` as excluded local preservation
  evidence.

The reconstructed documentation set is tracked. Verify the actual working tree at
every session start rather than inferring current modifications from this list.

Verify branch, HEAD, latest commit and working tree at every session start.
Preserve intentional untracked records and unrelated user changes.

## 3. Current production architecture

Cheshire Today currently consists of:

- a React 18/CRACO single-page frontend;
- a FastAPI backend in `backend/server.py`;
- MongoDB accessed through Motor/PyMongo;
- Uvicorn on the committed Render web-service path;
- a Cloudflare-facing public hostname;
- FastAPI serving `/api`, selected crawler/discovery routes and the built SPA;
- distinct public and authenticated Admin surfaces;
- environment-dependent source, AI, email, payment, social and analytics
  providers.

The build path installs backend requirements, builds the frontend and copies it
to `backend/frontend_build` for SPA hosting.

Committed configuration does not prove the current Render plan, deployed commit,
provider enablement, environment values or database contents. Verify those facts
directly when they affect a task.

See [Architecture Master](ARCHITECTURE_MASTER.md) and
[System Overview](ARCHITECTURE/SYSTEM_OVERVIEW.md).

## 4. Protected production systems

The following systems are protected:

- article discovery/import and provider calls;
- scheduler configuration, ownership and locks;
- article insertion and publication;
- Manual Review routing and restoration;
- Archive state and cleanup;
- Daily Brief and Weekly Roundup;
- subscriber records and preferences;
- newsletter tracking, accepted-recipient ledger and batch cursors;
- first-party and Admin analytics;
- canonical routes, crawler HTML, sitemaps and robots;
- Social Publishing and external platform accounts;
- sponsored placements and advertiser/payment state;
- authority guides and affiliate products;
- production MongoDB and environment configuration;
- Render services, deploys and restarts.

No production mutation, manual job, send, deployment, indexing request, data
repair or configuration change may occur without explicit approval and
evidence-led safeguards.

Do not expose credentials, tokens, subscriber information, IP hashes, hidden
articles or provider secrets.

## 5. Current scheduler and publication model

Current code configures these `Europe/London` schedules:

| Job | Schedule |
|---|---|
| Article generation | Daily at 06:00, 12:00 and 18:00 |
| Daily Brief | Monday–Saturday at 07:30 |
| Weekly Roundup batch 1 | Sunday at 09:00 |
| Weekly Roundup batch 2 | Sunday at 10:00 |
| Weekly Roundup batch 3 | Sunday at 11:00 |
| Weekly Roundup batch 4 | Sunday at 12:00 |

APScheduler is configured inside the eligible web process and starts only when
the explicit automation flag is enabled and the runtime hostname is valid.
Article and digest workflows use Mongo-backed locks and stale-lock handling.
Deployment-triggered article generation remains disabled.

Scheduled article generation requests up to twelve candidates with a current
public import limit of six. Quality, locality, freshness, source and AI-output
guards can reject or route records to hidden Manual Review. Backend safeguards
remain authoritative when a Manual Review edit may return live.

Version 1 deterministic title, source-URL, image, active/archive snapshot, batch,
unique-index and duplicate-key controls remain authoritative.

Editorial Similarity Phase 2B is explicitly enabled only on normal scheduled
hybrid imports. It is shadow-only and log-only. It cannot block, merge, archive,
delete, publish, reroute or alter an article. Commit `5e8f0ef` added bounded,
deterministic `phase2a_event_anchors_v1` evidence for entities/event phrases,
typed quantities, ordered/outcome-aware stages, format/angle and exact-boundary
locality. Scorer weights and bands remain unchanged; the corpus remains 50 active
plus 50 archived and the shortlist remains 20. No database scan or publication
behaviour was added. The first natural run verified execution and compact logging,
not routing precision. No threshold, UI or publication-state decision is approved.

See [Scheduler Operations](OPERATIONS/SCHEDULER.md),
[Article Pipeline](ARCHITECTURE/ARTICLE_PIPELINE.md) and
[Editorial Similarity](ARCHITECTURE/EDITORIAL_SIMILARITY.md).

## 6. Current editorial operating model

The target editorial mix is:

- **40% Local Cheshire**;
- **40% Business / Economy / Finance / Property**;
- **20% AI / Technology**.

Quality and relevance override mechanical quota filling.

Current standards require:

- clear Cheshire relevance for Local News;
- factual, neutral and readable reporting;
- professional British English;
- useful source attribution;
- suppression of weak crime, court, emergency and national filler;
- no clickbait, promotional language or invented facts;
- no generic, repetitive or AI-shaped endings and openings;
- minimum-content, image and source safeguards.

Commit `bbc526c` (`Fix incomplete RSS preview handling`) addresses a confirmed
High import-quality defect in which continuation-ended Guardian RSS preview
content could remain public and HTML block boundaries could be destroyed. A
bounded audit found five current Guardian-derived records containing
case-insensitive `Continue reading`; this is not a lifetime count and those five
historical records remain unrepaired. The implementation preserves block
boundaries with BeautifulSoup, normalises line endings, recognises/removes only
terminal continuation markers, classifies incomplete raw previews before
sanitisation, and routes known incomplete fallback content to hidden Manual
Review even when `manual_review_without_ai` applies. The existing 1,000-character
completeness floor remains, genuinely distinct complete replacements remain
eligible under existing controls, and no full Guardian-article fetching was
introduced.

Deployment `dep-damij1btqb8s73fvesp0` became live on Standard instance `klzb8`
(1 CPU/2 GB) at 13:10:17 BST on 18 September. The natural 18:00 run completed
once at 18:01:58 in 118.50 seconds, with normal imports, zero cleanup removals,
final RSS about 302.0 MB and no attributable OOM, restart or material 5xx. It
naturally routed Guardian record `6aad6e3245d0658a103d921e` to hidden Manual
Review with the expected incomplete-preview reason and preserved source data.
Bounded inspection of that record and public Guardian record
`6aad6e7245d0658a103d9228` found no supported terminal marker or obvious joined
HTML boundary. Classification: **HTML-BOUNDARY FIX NATURALLY VERIFIED** and
**INCOMPLETE-PREVIEW ROUTING NATURALLY VERIFIED**, but **COMPLETE-REPLACEMENT
PATH NOT NATURALLY EXERCISED**. Overall: **IMPORT ARTICLE QUALITY FIX NATURAL
ACCEPTANCE PARTIAL**. `/api/import-real-news` remains a separate unchanged
follow-up risk. Newsletter Funnel V1 subsequently resumed and completed through
the separately verified implementation, deployment and production-acceptance
evidence recorded below.

Perplexity may provide bounded research/rewrite assistance in eligible import
paths. Provider output still passes deterministic and editorial controls.

OpenAI remains Admin-only and draft/review-only. It must never auto-publish.
Manual Review is a first-class hidden editorial state. No automatic AI
publication is permitted.

Commit `fcb801b` (`Show dates on Manual Review cards`) was deployed and
production-verified on 17 August 2026. Manual Review cards now show the
published date and the date/time added to review, with review timestamps
displayed in `Europe/London`. Desktop and mobile verification passed. This was
a frontend-only Admin UX improvement; the existing API, sorting, Manual Review
actions and editorial behaviour are unchanged.

Commits `075214b` (`Stabilise Manual Review ordering`) and `fa9ffe9` (`Add
Manual Review load more`) were deployed through Render deployment
`dep-da6ag1dg1s2s739anklg` on Standard instance `9rtcd` (2 GB RAM / 1 CPU).
Production verification observed a live total of 354: the initial state showed
100 of 354, authenticated GET-only pages at `skip=100`, `skip=200` and
`skip=300` appended successfully, and the final state showed 354 of 354. All
354 cards had unique IDs, with no duplicate across page boundaries; API order
was preserved without a frontend re-sort. Published and Added to review dates,
Editorial assessment, Source, Edit, Create OpenAI Draft and Archive remained
present, and `Select loaded` wording was verified. Desktop 1440×900 and mobile
390×844 checks passed. No mutation was invoked; bulk-action and Force
Live/restoration paths were not dynamically exercised, and transactional
snapshot consistency during concurrent mutations is not claimed. Health
returned HTTP 200, with no OOM, restart or material 5xx observed. **MANUAL
REVIEW LOAD MORE PRODUCTION VERIFIED.**

See [Editorial Evolution](EDITORIAL_EVOLUTION.md) and
[Article Pipeline](ARCHITECTURE/ARTICLE_PIPELINE.md).

## 7. Current newsletter operating model

The newsletter system currently supports:

- Daily Brief Monday–Saturday;
- four Sunday Weekly Roundup batches;
- active/preference-based eligibility;
- fair rotating batch cursors and priority-recipient handling;
- Resend batch delivery when enabled;
- an explicitly configured SMTP fallback capability;
- per-recipient tracking identities;
- open and click analytics;
- privacy-preserving accepted-recipient ledgers;
- secure request links for preferences, unsubscribe and reactivation;
- purpose-specific signed tokens, stored challenges, rate limits, expiry and
  replay protection;
- protected, invalid and test-address safeguards.

Newsletter Funnel V1 is **PRODUCTION ACCEPTED**. Commit
`66fde1004a322d540bf9ac3197dab6b80152428b` (`Add newsletter signup funnel
analytics`) added backend-authoritative, fail-open measurement of syntactically
valid public signup attempts and `created`, `existing` or `failed` outcomes in
anonymous daily `newsletter_signup_funnel_daily` aggregates. Canonical placements
are `newsletter_landing`, `homepage`, `article`, `footer`, `popup` and `unknown`;
legacy, missing, malformed or unrecognised placement values map to `unknown` for
measurement only. Invalid-email 422 requests do not enter the handler and do not
count. Created conversion is `created / (created + existing + failed)`, with no
historical backfill. The misleading pre-result NewsletterFull
`newsletter_submit` event was removed while its API placement remains
`newsletter_landing`; subscriber and welcome-email semantics are unchanged.

Deployment `dep-dan3beojo6nc7395spm0` ran the exact commit on Standard instance
`fkdbq` (1 CPU/2 GB, one instance, `WEB_CONCURRENCY=1`) and became live at
08:14:30 BST on 19 September 2026 after successful build, Uvicorn/Mongo startup,
normal scheduler registration and index provisioning. Before controlled
acceptance, bounded inspection found zero matching subscriber records for the
authorised test identity and no `newsletter_landing` aggregate for
`date_key=2026-09-19`, so the effective pre-test counters were all zero. Exactly
one production signup request was made. It returned HTTP 200/`created` and
created exactly one record with `active=true`,
`signup_placement=newsletter_landing`, creation/subscription timestamps and
`daily_brief=true`, `weekly_roundup=true`, `breaking_news=true`.

The post-request aggregate was attempts 1, created 1, existing 0, failed 0 and
server_error 0. The complete observed delta was attempts +1, created +1,
existing +0, failed +0 and server_error +0; no natural-traffic confounding was
observed between the bounded pre/post reads. Its identity/timestamps were
`date_key=2026-09-19`, `day_start_utc=2026-09-18T23:00:00Z` and
`expires_at=2027-10-18T23:00:00Z`. Application logs recorded one successful
welcome-email send attempt; no resend occurred. Inbox delivery, human receipt,
deliverability and engagement were not assessed and are not claimed.

The first Admin analytics acceptance request returned HTTP 401 because the
existing Admin authentication session was expired or invalid. It caused no
second newsletter signup. Normal authorised Admin re-authentication then
completed without a credential or authentication-configuration change, and the
authenticated analytics request succeeded. `signup_funnel` reported
`available=true`, totals of attempts 1, created 1, existing 0, failed 0 and
server_error 0, a `newsletter_landing` breakdown of `1/1/0/0/0`, and 100.0%
created conversion, exactly matching the independently verified aggregate.
Existing analytics also loaded, with point-in-time observations of 10,000
provider-accepted opportunities, 10 accepted send batches, 1,450 opens and 264
clicks, together with article, Facebook and commercial analytics. These values
were observed only to verify continuity; they are not permanent/current KPIs and
must not be interpreted beyond their established measurement semantics.
Provider acceptance does not prove inbox delivery, and opens/clicks do not prove
unique human engagement. **NEWSLETTER FUNNEL V1 PRODUCTION ACCEPTANCE PASSED.**

The version-1 aggregate stores only schema/placement/day identity, counters and
timestamps. It stores no subscriber email or hash, IP or hash, user agent,
session, page URL, article ID, UTM values or request payload. Retention is exactly
13 calendar months through an `expires_at` TTL. A process termination between
subscriber creation and the best-effort aggregate write can undercount because
no distributed transaction is used. Production acceptance separately confirmed
that pre-existing subscribe/welcome logging writes full subscriber email values;
this is the Medium Open `CT-QA-2026-006` privacy/data-minimisation follow-up and
is not caused by, or stored in, the anonymous Funnel V1 aggregate.

Inactive-subscriber deactivation requires reconciled provider, acceptance and
engagement evidence. Missing opens alone are insufficient. Do not expose raw
subscriber addresses, tokens or hashes.

Code capability does not prove the current live provider, audience, delivery or
inbox result. Verify production state and use normal scheduled evidence rather
than an unapproved test send.

Weekly Roundup slot-aware idempotence is **NATURAL VERIFICATION COMPLETE**.
Commit `5559499` (`Fix Weekly Roundup batch idempotence`) established identity on
`(digest_time, date_key, weekly_roundup_batch_slot)` with `claimed`, `sending`,
`sent`, `partial`, `failed` and `ambiguous` lifecycle protection. On Sunday
6 September 2026, the four scheduled slots ran naturally at 09:00, 10:00, 11:00
and 12:00 BST. Each selected 1,000 recipients and recorded 1,000/1,000 successful
application/provider-path acceptance, with distinct slot tracking identities and
cursor progression to 996, 1996, 2996 and 3996. No `E11000` duplicate-key conflict
was found, and subsequent production startup confirmed the slot-aware unique
index. No manual newsletter send was used for verification. These results close
the idempotence reliability-validation loop; they do not prove 4,000 inbox
deliveries, readership, absence of delayed provider failures or perfect
deliverability.

See [Newsletter Architecture](ARCHITECTURE/NEWSLETTER.md) and
[Newsletter Operations](OPERATIONS/NEWSLETTER_OPERATIONS.md).

## 8. Current social and growth workflow

Social publishing remains manual and editorially approved.

The working sequence is:

1. recommend an eligible public article;
2. wait for explicit editorial approval;
3. prepare the Facebook post and pinned comment;
4. prepare relevant Instagram and Threads copy;
5. add restrained hashtags and an engagement prompt;
6. preview the final platform result;
7. publish only with approval.

The unified Admin Social Publishing workflow prepares deterministic links, copy
and approved brand assets. It does not automatically publish or schedule.

Growth priorities are qualified Facebook traffic, newsletter ownership, SEO and
Discover visibility, strong local/topic authority and sponsor readiness.

Do not select or publish Manual Review, archived, source-only or unapproved
content. Do not confuse first-party Facebook UTM attribution with Meta platform
reactions, comments or shares.

See [Brand Assets](brand-assets/), [Analytics Architecture](ARCHITECTURE/ANALYTICS.md)
and [Engineering History](HISTORY/ENGINEERING_HISTORY_MASTER.md).

## 9. Current analytics-consent state

Commit `be0182b` (`Add consent-gated analytics tracking`) implemented a bounded
frontend consent layer for third-party analytics. It provides versioned Unknown,
Accepted and Rejected states; defaults fresh visitors to no third-party analytics;
dynamically loads GA4, Plausible and PostHog only after acceptance; owns SPA
page-view dispatch while disabling provider automatic page views (`send_page_view:
false` for GA4); disables PostHog autocapture and session recording; excludes
sensitive routes; normalises analytics URLs; gates custom events; supports
withdrawal and re-acceptance; and keeps a persistent Cookie/privacy settings
control with equally prominent Accept and Reject actions. Existing first-party
measurement systems were intentionally unchanged.

Pre-deployment verification passed 4 focused suites/17 tests, 10 regression
suites/118 tests, the production frontend build and `git diff --check`. No
unconditional provider loader, direct provider bypass outside
`analyticsProviders.js`, or enabled PostHog recording remained.

Render Auto-Deploy `dep-dam3mb3ncjis73cit8mg` deployed the commit on 17 September
2026 to service `cheshiretoday-migration-` (`srv-d5virmm3jp1c73c9d6tg`), Standard
instance `w8frn` (1 CPU/2 GB). It started at 20:10:36 BST, built successfully at
20:12:24, completed application startup at 20:13:09 and became live at 20:13:16.
The deployment duration was 2m40s.
Health returned HTTP 200 with `{"status":"healthy","service":"cheshire-news"}`;
no deployment-attributable traceback, OOM, exit 137, restart loop, Bad Gateway or
material 5xx was observed. The existing nonfatal Twitter-credentials warning was
not caused by this change.

Production browser acceptance observed the consent UI for a fresh visitor, no
GA4/Plausible/PostHog scripts before consent, persisted rejection with providers
unloaded across navigation/reload, settings reopening with the rejected state,
provider loaders/assets appearing only after acceptance, accepted reload without
duplicate script insertion, no provider scripts on a direct accepted-state
`/admin` load, accepted-to-rejected withdrawal, no provider initialisation on the
subsequent rejected reload, no PostHog recorder/session-replay asset at any stage,
working public pages, and a 390×844 mobile panel without horizontal overflow.

Classification: implementation **COMPLETE**; automated verification **PASS**;
production deployment **VERIFIED**; observed production consent behaviour **PASS
for the behaviours actually observed**; confirmed production defect **NONE**.
Overall event-level acceptance remains **ANALYTICS CONSENT PRODUCTION EVIDENCE
INCONCLUSIVE**. Available tooling could not provide both genuinely isolated
storage inspection and request-level interception/payload inspection, and a
second attempt correctly stopped as **EVENT-LEVEL PRODUCTION VERIFICATION TOOLING
UNAVAILABLE**. Exact production consent JSON, provider page-view payloads/counts,
one-event-per-route cardinality, event-level duplicate suppression, transmitted
URL normalisation, event-level `/admin` exclusion, immediate post-withdrawal event
suppression and provider-dashboard receipt therefore remain unproven. No
implementation work should reopen without defect evidence; complete the bounded
external verification when isolated DevTools/Playwright/CDP request inspection is
available. This evidence makes no legal-compliance, historical-data,
provider-dashboard or first-party measurement-policy conclusion.

## 10. Current monetisation model

The commercial strategy is affiliate-first and reader-focused.

Current code supports:

- authority and comparison guides;
- active affiliate products and guide recommendations;
- sponsored placement slots with bounded weighted rotation;
- placement impression and click counters;
- advertiser leads and Admin review;
- Stripe-supported advertising checkout and payment state;
- manual advert approval and live notification;
- house adverts through the placement architecture where configured.

Payment does not automatically publish an advert. Commercial presentation must
remain clearly labelled, relevant and non-intrusive. No revenue or conversion
performance is claimed here.

Commits `89916c4` (`Reduce article monetisation clutter`) and `5256bd7`
(`Suppress article house-guide sponsor fallback`) were deployed and
production-verified on desktop and mobile through Render deployment
`dep-da5bvarl550s7385krgg`, instance `f594w`. Normal article pages no longer
show generic Useful Guides, Amazon Top Picks or article house-guide/
house-affiliate fallback placements; genuine paid/local sponsor capability and
one article-specific newsletter invitation remain available. The contextual
recommendation system and homepage monetisation are unchanged. Verification
found no empty-gap or layout regression, health returned HTTP 200, and no OOM,
restart or material 5xx was observed. **ARTICLE MONETISATION RESTRAINT
PRODUCTION VERIFIED.** This is visual/placement evidence only: it does not show
improved monetisation performance, CTR or revenue, does not fully validate
contextual recommendations, and did not dynamically exercise paid sponsor
delivery.

Dynamic affiliate inventory and sponsor-impression bot filtering remain open or
deferred roadmap work, not completed operating capabilities.

See [Monetisation Architecture](ARCHITECTURE/MONETISATION.md) and
[Commercial Gap Map](commercial-gap-map/).

## 11. Current QA posture

The current evidence-backed QA posture is summarised in [QA Master](QA/QA_MASTER.md).
Detailed closure criteria are in [Open Findings](QA/OPEN_FINDINGS.md).

`QA-SEC-001` retained its original Critical severity but closed on 11 August
2026 after production Admin-password rotation, invalidation of nine pre-rotation
Admin sessions, successful replacement-credential and bearer-token verification,
and HTTP 401 rejection of the historical password. The current tracked tree
remains contained; reachable Git history still retains the revoked historical
credential and was not rewritten. Production remained healthy.

`QA-SEC-002` retained its original High severity and closed on 12 August 2026
after commit `b497635` replaced wildcard browser origins with the canonical
production origin and two explicit local-development origins. Deployment
`dep-d9u594oae00c73bs1lvg` became live on instance `qmqjs` at 12:12:56 BST.
Canonical-origin and hostile-origin preflights, Admin authentication compatibility,
health and public frontend smoke checks passed without a production regression.

`CT-QA-2026-003` retained its Medium severity and closed on 13 August 2026.
Commit `d8943e8` changed article lock-acquisition errors from warn-and-continue to
error-and-skip. Seven focused tests prove seed and atomic-acquisition exceptions
cannot proceed to generation, cleanup or lock deletion while held, successful and
stale-lock paths remain intact. The natural 18:00 run on instance `qc88z` acquired
`article_gen_2026081317` once, completed one generation and cleanup sequence in
105.98 seconds, and remained healthy with HTTP 200. No production lock failure was
deliberately induced; the natural run verifies normal-path compatibility.

Highest-priority unresolved or monitoring items are:

- **High — partial natural acceptance:** the confirmed RSS-preview import-quality
  defect is implemented, tested and deployed in `bbc526c`. Core incomplete-preview
  routing and bounded HTML-boundary behaviour are naturally verified without a
  confirmed deployment defect. Natural evidence for a continuation-ended source
  receiving a genuinely distinct complete public replacement remains outstanding;
  the five historical affected Guardian records remain a separate editorial repair.

- **High:** `QA-OPS-001` remains **HIGH OPEN — RECURRENT PRODUCTION OOM
  CONFIRMED**. Cleanup lifecycle and projection changes remain structurally safe,
  and commit `b3550c0` added `batch_size(250)` only to the projected short-content
  cursor. Natural runs on instance `zthtp` reduced that isolated RSS interval to
  +3.9 MB over 4,249 records in 2.68 seconds on 20 August 18:00 and +1.0 MB over
  4,264 records in 2.65 seconds on 21 August 06:00, versus a supplied pre-batch
  range of about +26 to +51 MB and mean of about +39.5 MB. Both runs removed zero
  records, completed normally and showed no material runtime regression, so
  `batch_size(250)` is a **provisional keep**. This does not resolve allocator/native
  retention, elevated cumulative RSS or the wider OOM risk. Standard 2 GB remains
  temporary production-safety headroom. The 21 August Business/Tech-to-visible-
  pool interval added +57.7 MB and is evidence for a separate review, not approval
  for a visible-pool change.
- **Medium:** Editorial Similarity’s numerical three-run observation-count gate is
  satisfied. Two bounded calibration rounds covered 27 labelled pairs and found
  overlapping positive/negative score ranges plus four false positives from the
  tested composite. The current scorer needs deterministic event-identity feature
  design before routing; thresholds, UI and enforcement remain unapproved and the
  scorer remains scheduled-only and shadow-only.
- **Medium:** `CT-QA-2026-004` records a cross-source same-event duplicate-identity
  limitation. A 10–14 August read-only ledger found zero confirmed or probable
  archived-to-reimport cases through the normal scheduled hybrid importer, whose
  exact active/archive identity protection is functioning. Four strong
  cross-source or cross-format same-event clusters remain evidence that changed
  URLs, titles and images can bypass deterministic identity checks. Score-only,
  band-only and the tested cross-source composite are not safe for Manual Review
  routing. Commit `5e8f0ef` implements the approved bounded deterministic evidence
  layer without enforcement. Its healthy 15 August 12:00 natural run logged 20
  `phase2a_event_anchors_v1` evaluations (19 scored and one `no_match`) in
  `scheduled_log_only` mode. Seventeen emitted compact codes, limited in this run
  to `format_guard`, `cross_source`, `same_run` and noisy `locality_overlap`.
  No high-specificity positive or `same_run_event_compatible` case occurred, so
  calibration remains open and Manual Review routing remains unapproved.
- **Closed — production verified:** `QA-A11Y-001`. Commit `dcd5cfa`
  (`Improve public search accessibility`) added durable `Search news` naming,
  native article-result links, ordinary Tab/Enter semantics, Escape dismissal
  with input-focus retention, and polite loading/result/no-result feedback.
  Deployment `dep-da82j9uk1f9s73dgc1mg` ran on Standard instance `9sflp`
  (2 GB RAM / 1 CPU). Desktop and 390×844 mobile production checks preserved
  the two-character threshold, five-result limit, real article destinations,
  modifier/new-tab/copy-link semantics, visible focus, usable touch targets,
  layout and public homepage/article/category/authority surfaces. Health was
  HTTP 200 with no browser-console, startup, Mongo, scheduler, OOM, restart or
  material 5xx anomaly. Failure messaging and stale-response cancellation are
  deployed and test-covered; no production failure was manufactured. This
  closes the identified search defect, not site-wide accessibility or WCAG
  conformance, and no arrow-key combobox behaviour was introduced.
- **Closed — production verified:** `QA-SEO-002`. Commit `24f381e` added
  first-byte `X-Robots-Tag: noindex, nofollow, noarchive` protection for `/admin`
  and `/admin/`, retained first-byte noindex on unsupported nested Admin paths,
  and made wildcard, Googlebot and Googlebot-News exclusions for `/admin` and
  `/api/admin/` explicit. Deployment `dep-da7ala710e5c738ovtm0` on instance
  `824s7` (Standard, 2 GB RAM / 1 CPU) was production-verified on 26 August 2026.
  Public homepage, category and article SEO, canonical/social metadata, JSON-LD
  and both sitemaps were preserved. Robots and noindex are indexing controls only;
  Admin authentication and API authorization remain the security boundary.
- **Production-verified material improvement:** `QA-PERF-001` is narrowed to
  record that its original homepage database/materialisation defect has received
  an evidence-supported optimisation. Commit `70057e1` skips the unused
  `count_documents()` call and caps Local and UK candidate materialisation at 100
  each only for the exact public `GET /api/articles?limit=80` list shape. Force-
  live and fallback caps and semantics, visibility, Mongo predicates, projections,
  sorting, filtering, 2:2 interleaving, incident/crime handling, boosting, dedupe,
  slicing and response contracts remain unchanged. Read-only sufficiency analysis
  found deepest contributing Local/UK positions 42/58: 60/60 and 80/80 matched
  but lacked the selected operational headroom, while 100/100 retained an exact
  ordered match; force-live reduction was rejected and fallback was unchanged.
  A bounded five-request comparison measured median handler time
  1,081.639→708.314 ms (-373.325 ms, 34.5%), TTFB
  1,868.333→1,544.086 ms (-324.247 ms, 17.4%), and total time
  1,897.497→1,587.383 ms (-310.114 ms, 16.3%). Count time fell
  123.102→0 ms, Local materialisation 366.840→255.975 ms (-30.2%),
  and UK materialisation 248.688→132.848 ms (-46.6%). All five responses
  returned HTTP 200 and 79 articles with stable bytes, force candidates 33,
  pre-dedupe/final 80/79 and fallback 0/5; exactly five markers were emitted,
  with no traceback, material 5xx, OOM, exit 137 or unexpected restart. This is
  bounded evidence, not statistical or site-wide performance closure. The median
  post-change TTFB-minus-handler residual is 839.327 ms; its framework, encoding,
  compression, proxy/runtime, network or other composition is unmeasured and must
  not be attributed without a separate read-only investigation. Classification:
  **MATERIAL IMPROVEMENT — QA-PERF-001 OPTIMISATION VERIFIED.**
- **Search Console canonical audit — monitoring only:** representative inspection
  on 7 September 2026 classified **Alternate page with proper canonical tag** as
  **MOSTLY HISTORICAL ALTERNATE URLS — CURRENT IMPLEMENTATION HEALTHY**. The
  report remained `Validation Failed` with 82 examples (validation 16–25 July;
  latest report update observed 4 September), but sampled query consolidation,
  historical UUID identities, current Mongo-ID canonicals, archived noindex,
  sitemaps and internal links were coherent. No current canonical defect or code
  change was justified. **DO NOT PRESS VALIDATE FIX NOW.** Allow natural Google
  recrawl and recheck after a later report update or a newly crawled current
  mismatch; the detailed evidence is in
  [SEO and Crawler Architecture](ARCHITECTURE/SEO_AND_CRAWLERS.md).
- **Active:** documentation reconstruction and pending-source reconciliation.

Rendered public metadata duplication is recorded as remediated, deployed and
production-verified. Legacy Python compilation and the original external-test
mutation boundary are remediated at repository level. These closures do not
close adjacent production or maintenance risks.

See [Completed Phases](QA/COMPLETED_PHASES.md) and
[Test History](QA/TEST_HISTORY.md).

## 12. Current active milestone

The active milestone is **production hardening, QA reconciliation and controlled
production observation**.

### Track 1 — Documentation authority

Completed and committed:

- Phase 7 concise current-state replacement and preservation verification;
- Project Master, architecture, operations, QA and roadmap reconstruction.
- archive privacy decision and privacy-safe repository archive creation.
- Phase 7.3 archive-link correction, removing repository Markdown dependencies on
  the excluded exact archive and making clean-checkout links use the privacy-safe
  archive.

Still pending:

- reconcile this 15 August authority update through final review and an approved
  documentation commit;
- receive and reconcile the ChatGPT export;
- preserve and reconcile structured Codex history;
- reconcile historical PDFs;
- continue reconciling later production evidence as it is verified.

### Track 2 — Production observation

- observe normal scheduler runs only;
- capture all fifteen article-generation memory markers, including both helper-
  return boundaries and bounded Python-heap diagnostics;
- continue post-run stability monitoring after the duplicate-cleanup lifecycle,
  projected-scan and observability improvements; first duplicate Stage 1,
  visible-pool work, short-content scan variability and high-start process memory
  remain material evidence areas;
- retain bounded Editorial Similarity score, band, reason and provenance evidence;
- continue labelled calibration of bounded event-anchor evidence using natural,
  high-specificity same-run cross-source cases;
- confirm Version 1 decisions, Manual Review and publication remain unchanged;
- make no calibration, threshold, UI or enforcement decision without a separate
  reviewed evidence gate and approval.

No manual import should be triggered solely to accelerate observation.

## 13. Immediate approved priorities

1. Keep the isolated short-content `batch_size(250)` change provisionally and
   continue cumulative memory monitoring; its two-run phase improvement does not
   close `QA-OPS-001`.
2. Review the visible-pool lifecycle separately using current heap/RSS evidence;
   do not combine another memory change with the batching decision.
3. Continue Weekly Roundup delivery, bounce and engagement monitoring without
   treating provider acceptance as final inbox delivery.
4. Continue inactive-subscriber evidence gathering without speculative
   deactivation.
5. Measure/design the remaining post-handler/client TTFB residual read-only before
   any further performance optimisation.

Security and reliability take precedence over speculative features.

## 14. Near-term priorities

- investigate the remaining homepage post-handler/client TTFB residual without
  assuming a subsystem cause or proposing another Mongo/index/query change;
- preserve and improve hermetic test isolation;
- reduce compilation/build/test warning debt in bounded changes;
- validate GA4 configuration and reporting separately from first-party analytics;
- complete event-level third-party consent verification when suitable isolated
  request-interception tooling is available; this does not block unrelated
  analytics or growth work;
- monitor the 82-example Search Console canonical baseline after natural recrawl;
  inspect any newly crawled current mismatch before changing code or requesting
  validation, and continue separate Google News and Discover review;
- continue quality-first commercial SEO and affiliate guide development;
- design evidence-backed dynamic affiliate inventory;
- complete sponsor workflow readiness and reporting checks.

Each item requires its own reviewed scope, tests and deployment/production
verification plan.

## 15. Deferred work

The following remain deferred or unapproved:

- Version 2 brand refresh until audience and business value justify a coordinated
  rollout;
- Similar Stories or similarity Admin UI;
- automatic similarity blocking, merging, routing, archive or deletion;
- broad Admin navigation/dashboard redesign;
- speculative database indexes, caching or optimisation without measurements;
- intrusive advertising;
- automatic social publishing unless separately designed, reviewed and approved;
- new Save Draft or Publish contracts outside existing editorial safeguards.

Version 1 duplicate prevention remains authoritative while similarity is
observational.

## 16. Current operating rules

- Read [Project Master](PROJECT_MASTER.md) first.
- Read this Current Operational State second.
- Verify repository and mutable production state before acting.
- Confirm whether requested work already exists.
- Make one safe action at a time.
- Prefer safe scripted edits.
- Use `/usr/bin/grep`, not `rg`.
- Do not use `npm start` unless explicitly requested.
- Run the smallest relevant test after each change, then related validation.
- Inspect the complete diff and run `git diff --check`.
- Do not push, deploy or mutate production without approval.
- Preserve intentional untracked files and unrelated user work.
- Do not trigger manual production jobs for ordinary QA.
- Keep OpenAI Admin-only and draft-only.
- Preserve Manual Review, Version 1 duplicate rules and newsletter security.
- Record implementation, deployment and production verification separately.
- Update the documentation layer that owns the evidence.

## 17. Session-start checklist

1. Read [Project Master](PROJECT_MASTER.md) and this file.
2. Read relevant architecture, operations, QA and roadmap records.
3. Verify branch, HEAD, latest commit and working-tree status.
4. Check current production state where facts may have changed.
5. Identify and protect affected production systems.
6. Confirm the exact task, mutation boundary and approval scope.
7. Make one safe action and verify it before continuing.

## 18. Session-end checklist

1. Run tests, compilation, build or checks appropriate to the task.
2. Review the exact diff and repository status.
3. Record commit, deployment and live verification as separate evidence.
4. Update the correct current, architecture, QA, history or roadmap document.
5. Record unresolved findings and closure criteria.
6. Preserve historical evidence and source limitations.
7. Confirm no production change remains undocumented.

## 19. Documentation links

### Governance and current state

- [Project Master](PROJECT_MASTER.md)
- [Privacy-safe archived Project State](ARCHIVE/PROJECT_STATE_REDACTED_2026-08-06.md)
- [Source Register](HISTORY/SOURCE_REGISTER.md)

### History and decisions

- [Engineering History Master](HISTORY/ENGINEERING_HISTORY_MASTER.md)
- [Decision Register](DECISION_REGISTER.md)
- [Production Timeline](PRODUCTION_TIMELINE.md)
- [Editorial Evolution](EDITORIAL_EVOLUTION.md)

### Architecture and operations

- [Architecture Master](ARCHITECTURE_MASTER.md)
- [System Overview](ARCHITECTURE/SYSTEM_OVERVIEW.md)
- [Article Pipeline](ARCHITECTURE/ARTICLE_PIPELINE.md)
- [Newsletter Architecture](ARCHITECTURE/NEWSLETTER.md)
- [Editorial Similarity](ARCHITECTURE/EDITORIAL_SIMILARITY.md)
- [Analytics Architecture](ARCHITECTURE/ANALYTICS.md)
- [SEO and Crawlers](ARCHITECTURE/SEO_AND_CRAWLERS.md)
- [Monetisation Architecture](ARCHITECTURE/MONETISATION.md)
- [Deployment](OPERATIONS/DEPLOYMENT.md)
- [Render Operations](OPERATIONS/RENDER.md)
- [Monitoring](OPERATIONS/MONITORING.md)
- [Scheduler Operations](OPERATIONS/SCHEDULER.md)
- [Newsletter Operations](OPERATIONS/NEWSLETTER_OPERATIONS.md)

### QA and roadmap

- [QA Master](QA/QA_MASTER.md)
- [Open Findings](QA/OPEN_FINDINGS.md)
- [Completed Phases](QA/COMPLETED_PHASES.md)
- [Test History](QA/TEST_HISTORY.md)
- [Roadmap Master](ROADMAP_MASTER.md)

### Supporting records

- [Brand Assets](brand-assets/)
- [Commercial Gap Map](commercial-gap-map/)

Pending ChatGPT, Codex and historical PDF evidence is registered in the Source
Register. No nonexistent future history file is linked here.

## 20. Reconstruction and verification status

### Completed locally

- exact byte-for-byte historical Project State archive;
- source register and authority model;
- engineering history reconstruction;
- decision register;
- production timeline;
- editorial evolution;
- current architecture set;
- current operations runbooks;
- QA master, live findings, completed phases and test history;
- evidence-backed roadmap;
- permanent Project Master;
- this concise Current Operational State replacement.
- privacy-safe repository archive, with the byte-exact source retained locally and
  excluded from Git.

### Pending

- ChatGPT export receipt and reconciliation;
- structured Codex-history preservation and reconciliation;
- historical PDF reconciliation;
- post-HEAD production-evidence reconciliation;
- final review and approved commit of this current authority reconciliation.

Complete historical reconstruction has **not** yet been achieved.

This file is the concise repository operational authority. This 11 August update
becomes current repository evidence only after final review and the approved
commit. Production facts that can change must still be freshly verified.
