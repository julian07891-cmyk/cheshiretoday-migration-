# Cheshire Today — Current Operational State

> - **Status:** Concise operational source of truth; Version 1 is complete and the current stage is production hardening, QA and evidence-led reliability monitoring
> - **Operational authority:** This file, governed by [Project Master](PROJECT_MASTER.md)
> - **Primary branch:** `full-scrape-prod`
> - **Repository baseline:** `03a6abbd5133de969275477488ea49bb34242ee0`
> - **Last repository reconciliation:** 20 September 2026
> - **Production-verification status:** Commit `03a6abb` is live and `CT-QA-2026-006` is closed after implementation, tests, automatic deployment and bounded production verification. Newsletter Funnel V1 remains production accepted and unchanged. The RSS-preview fix remains implemented/deployed with partial natural acceptance and its complete-replacement path remains unexercised. `QA-OPS-001` remains High Open
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
- **Current reconciled HEAD:** `03a6abbd5133de969275477488ea49bb34242ee0`
- **Latest baseline commit:** `Remove subscriber identity from newsletter logs`

This is the repository and production baseline reconciled on 20 September 2026, not
an assertion that a later session remains at the same HEAD or deployment.

### CT-DEC-021 production-readiness evidence — 23 September 2026

- **Live subscriber identity/index gate: SATISFIED by read-only inspection.**
- Full production-configured migration dry-run scanned **14,266** subscriber records: **14,266 already valid**, zero IDs requiring assignment, zero malformed IDs, zero duplicate management-ID groups, zero token versions requiring initialisation, and zero final identity/version defects.
- Separate read-only live index inspection confirmed `newsletter_management_id_unique` exists on `newsletter_management_id` ascending with `unique=true`, `sparse=false`, and matches the repository's exact expected definition.
- No subscriber record was modified, no migration apply mode was invoked, and no index was created or altered.
- This closes only the live identity/index readiness gate. **POTENTIAL QUERY LOG EXPOSURE**, upstream logging/privacy inspection, delivered native-header/DKIM/provider preservation, Apple Mail direct-footer acceptance, and controlled production mutation/persistence acceptance remain open. Nothing in the local CT-DEC-021 implementation chain has been pushed or deployed.

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

### Approved design — direct newsletter unsubscribe

**DESIGN APPROVED — FULL IMPLEMENTATION INCOMPLETE** under
[CT-DEC-021](DECISION_REGISTER.md#ct-dec-021--direct-newsletter-unsubscribe-with-secure-recovery-retained).
Normal newsletter links will use distinct version-bound signed credentials and
explicit confirmation; GET remains non-mutating. Signup/preferences stay unchanged
and generic recovery remains challenge-backed. The direct signed class uses the
existing five claims plus `credential_class="newsletter_direct_unsubscribe"`,
90-day expiry and strict class-specific validation. Tracked reactivation increments
version atomically; missing identities fail closed before content send. Welcome
is transactional onboarding, without native headers. Live identity coverage,
native query-log privacy and delivered DKIM/header/client checks are
production-readiness gates. See [Newsletter Architecture](ARCHITECTURE/NEWSLETTER.md).
Phase 1: **SECURITY FOUNDATION IMPLEMENTED LOCALLY — FULL CT-DEC-021 IMPLEMENTATION
INCOMPLETE**. The Phase 1 implementation committed locally as `516fa29` adds strict six-claim issuance and
validation, authenticated direct/recovery dispatch, and a shared atomic
identity/version/type-guarded direct unsubscribe processor for confirmation and
one-click POST. Focused fixture tests cover stale/reactivated versions, mutation-
boundary races, inactive replay and preserved recovery challenge enforcement.
No frontend, email-builder, outgoing-header or production change is included.
Query logging remains **POTENTIAL QUERY LOG EXPOSURE**; builder/transport wiring,
identity coverage and delivered-header/DKIM/client acceptance remain later gates.
CT-DEC-021 is not fully implemented or production-ready. CT-QA-2026-007 stays
closed and Apple Mail remains a separate unproven mechanism.

Phase 1 is **NOT PUSHED — NOT DEPLOYED**. Phase 2A delivery infrastructure is
**COMMITTED LOCALLY AT `4e6a8cf` — RE-REVIEWED, NOT PUSHED/DEPLOYED**: immutable validated
recipient contexts, candidate-only ambiguity rejection, single-issuance direct
artifacts, strict opt-in per-message Resend/SMTP headers and narrowly scoped
Uvicorn one-click query redaction. At the Phase 2A checkpoint, delivery-path
integration remained unimplemented; no scheduler bookkeeping or Phase 1 token
service change was made. Final Phase 2A local re-review verification passed 1,407 newsletter tests with
no failures; Python compilation and tracked `git diff --check` also passed. Existing
framework/datetime/gzip warning debt remains.
The access-log check uses pinned Uvicorn 0.25.0 with an in-memory HTTP transport;
no production server or email transport was contacted.
The two local review findings are corrected: origin/absolute-form one-click
queries are removed, identifiable sensitive unsupported records and sanitizer
failures are suppressed, and native-header containers have redacted diagnostics
with explicit fresh transport exports. Covered h11 shapes preserve the original
ASGI credential; httptools is supported by static inspection only. These defects
were never deployed; this is local test evidence, not production privacy acceptance.

Phase 2B **SLICE 1 DAILY BRIEF INTEGRATION IS COMMITTED LOCALLY AT `e91de2d` — FULL PHASE 2B
INCOMPLETE — SECOND INDEPENDENT REVIEW COMPLETED AND LOCAL FINDINGS CORRECTED**.
The first independent review found a material local artifact-binding defect:
prepared human/native credentials were not cryptographically rebound to their
recipient context at the final consumer boundary. The defect was never committed,
pushed, deployed or used to send email. It is corrected locally with one reusable
strict verifier that requires the exact canonical human and one-click structures,
one shared direct credential, a valid existing direct-token
signature/class/claims contract, and claims whose management ID and version equal
the artifact context. The complete batch is verified before rendering or provider
contact; failures are bounded and credential-free. The second independent
read-only review confirmed that material defect corrected and found no remaining
blocker or material issue. It identified one minor local accounting defect:
scheduled Daily Brief inferred `provider_contacted=true` from prepared-message
count even when SMTP was disabled or Resend configuration prevented any transport
attempt. That defect was also never committed, pushed, deployed or used to send
email. It is corrected locally with transport-boundary evidence: each Daily Brief
attempt resets the contact signal, Resend sets it immediately before the HTTP
provider request, and SMTP sets it only after configuration checks and immediately
before the connection attempt. All-invalid preparation remains a pre-provider
failure; valid preparation with unavailable transport is separately recorded with
`provider_contacted=false`; actual attempted zero-acceptance delivery remains a
provider failure.
Scheduled and manual real-audience Daily Brief validate full
candidate identity sets before deduplication, require explicit active=True, retain
selected slots without backfill, and prepare per-recipient direct HTML/text links
and native headers. Preferences, priority/cap/rotation, planned cursors and
positive-acceptance-only cursor advancement remain unchanged. Bounded selected,
prepared, skipped/reason and accepted counts distinguish preparation from provider
acceptance; accepted recipients are snapshotted before persistence awaits.
Single-address Daily tests use an explicit exactly-one non-direct preview boundary.
At the Slice 1 checkpoint, Welcome, Weekly and other content paths were unchanged. Focused Daily Slice 1
regression passes 41 tests. Offline newsletter plus Weekly idempotence regression
after the second-review correction: 1,461 passed, zero failures; existing
framework/datetime/gzip warning debt remains. Slice 1 is committed locally, not
pushed or deployed.

Phase 2B **SLICE 2 WEEKLY ROUNDUP INTEGRATION IS COMMITTED LOCALLY AT `fc8b34c`**.
Scheduled subscriber batches and the real-subscriber batch diagnostic reuse the
existing recipient context, single-issuance preparation and authenticated binding
validator. Full candidate ambiguity validation precedes deduplication; selected
identity/state/preparation-invalid slots are skipped without backfill. Direct
HTML/text and native unsubscribe headers share the recipient-bound credential;
the full prepared batch is validated before rendering or provider contact.
The single-address Weekly test is explicit preview only, without identity lookup,
direct credentials, native headers or subscriber accounting. Diagnostic sends
continue without durable digest/ledger/cursor writes. Four Sunday slots, claim
ownership, priority/engaged selection, caps, no-wraparound, article composition
and positive-acceptance cursor advancement remain intact. Actual transport
contact evidence is persisted; failed zero-acceptance outcomes with recorded
provider contact cannot be reclaimed. Genuine pre-contact failures remain
retryable; historical failed records without a contact marker retain the existing
legacy reclaim rule. Sent/partial/sending/ambiguous states remain non-retryable.
Offline Slice 2/Weekly idempotence verification: 51 passed, zero failures, with 5
existing warnings. Full newsletter plus Weekly idempotence regression: 1,499 passed,
zero failures, with 418 existing framework/datetime/gzip warnings. Slice 2 independent review completed locally; no production or deployment verification is
claimed. Full CT-DEC-021 remains incomplete and POTENTIAL QUERY LOG EXPOSURE remains.

Phase 2B **SLICE 3 BREAKING NEWS EMAIL INTEGRATION IS COMMITTED LOCALLY AT `14e2f01`**.
The authenticated manual email endpoint retains its breaking_news/active query
and 1,000-record limit. Full fetched candidate validation precedes preparation;
invalid selected positions are skipped without substitution. Explicit active=False
is excluded by the query; missing active reaches preparation and fails closed.
The builder requires existing recipient-bound direct artifacts and validates the
entire batch before rendering/contact. HTML now has a visible human unsubscribe
link, and plain text contains preferences and direct unsubscribe links. Native
headers share that same credential. Preferences and existing campaign-level
live-update CTA tracking are unchanged; direct unsubscribe is never click-tracked.
Resend and SMTP use existing per-message header infrastructure and reset acceptance
and actual contact evidence for each send. Digest records add bounded aggregate
delivery counts/reasons and contact evidence; endpoint failures use fixed private
errors. There is no email preview or provisioning. Daily, Weekly and separate
Breaking News push functions are unchanged. Slice 3 independent review completed locally; the
fetched-position accounting finding was corrected so missing, empty and non-string email positions
remain consumed and are reported as bounded skips without backfill. No deployment or production
verification is claimed. Full CT-DEC-021 remains
incomplete and POTENTIAL QUERY LOG EXPOSURE remains.

Slice 3 post-review focused verification: 38 tests passed, zero failures; full newsletter plus Weekly
idempotence regression passed 1,537 tests with zero failures and 419 existing
framework/datetime/gzip warnings. Python compilation and diff whitespace
checks passed. This is local test evidence only.

Phase 2B **SLICE 4 MIGRATION ANNOUNCEMENT INTEGRATION IS COMMITTED LOCALLY AT
`14d05a9` — NOT PUSHED/DEPLOYED**.
The authenticated endpoint preserves the active=True OR active-missing query and
10,000 fetched delivery positions. Missing/non-string/empty emails and invalid
identity/state positions are bounded skips without backfill; explicit active=True
is required for candidate preparation. Existing prepared-artifact validation checks
the entire batch before rendering or provider contact. HTML and plain text include
the recipient's direct unsubscribe URL, sharing its credential with native headers
on Resend and SMTP. Existing subject/main copy and preferences architecture remain
unchanged. Transport acceptance/contact state resets per attempt; digest records
contain aggregate delivery evidence and endpoint errors are private.
The post-send daily_brief=True update_many deliberately remains scoped to the full
active/missing-active population, including records beyond the fetched 10,000 and
skipped/unaccepted recipients. It is NOT acceptance-scoped. Normal partial, zero
or unavailable-transport returns still precede that mutation; a sender exception
prevents it, preserving the original ordering. Historical subscribers_migrated
response semantics remain the fetched-position count, not the update_many total.
Slice 4 independent review completed locally with no material implementation or test defect found. No production/deployment verification is
claimed; full CT-DEC-021 remains incomplete and POTENTIAL QUERY LOG EXPOSURE remains.
Offline verification: 45 focused Announcement tests passed (5 warnings); full
newsletter plus Weekly idempotence regression passed 1,582 tests (418 warnings),
zero failures. Existing framework/datetime/gzip warning debt remains. Compilation
and tracked/new-test whitespace checks passed. Scope tests confirm other production
functions are unchanged; migration fixtures exercise the full population beyond
the 10,000 delivery limit, zero/partial acceptance and sender exceptions.

Phase 2B **SLICE 5 SITE UPDATE PARTS 1/2 AND ONBOARDING INTEGRATION IS COMMITTED LOCALLY AT
`4503c28ef8b81d579626e29e33148796e6df2316` — NOT PUSHED/DEPLOYED**. Baseline verified at `14d05a9b98e991e864ef16ac0e7e63cbfb71723f`
on `full-scrape-prod`, 0 behind/6 ahead of the locally recorded origin ref, with
only the two protected local files initially untracked. Both Site Update senders
now require prepared direct deliveries and validate the complete set before
rendering or transport. Subjects, message meaning, tracking pixels and generic
preferences URLs remain unchanged; HTML/text/native headers share each recipient's
direct credential without click wrapping. SMTP and Resend preserve per-recipient
isolation and reset/contact/acceptance evidence. No identity provisioning or
generic-unsubscribe fallback was introduced.

Manual endpoints retain the active=True OR active-missing Mongo predicate,
10,000 fetched-position limit, digest identities/date semantics, targeted counts,
and send → digest → global-flag ordering, including normal zero/partial acceptance
and unavailable-transport returns. Invalid fetched positions are counted without
replacement; only explicit active=True can prepare. Diagnostics are aggregate and
public failures are fixed/private. The onboarding default-off gate is retained
and returns its intended fixed 404 outside the delivery error handler. Dry runs
remain send/preparation-free. Day 3/7 rules, independent parts, 20,000 fetch cap,
case-insensitive deterministic deduplication and the skip-only-explicit-False
eligibility rule are retained. Live preparation inspects the full fetched identity
set before deduplication. Selected invalid state/identity records fail closed.
Each part immediately snapshots accepted recipients/contact evidence before any
await; only accepted recipients receive that part's marker, using their stored
email spelling. Zero acceptance writes no markers. `created_at` is never written;
its fallback to `subscribed_at` remains age-calculation-only. Concurrency and
unrelated legacy dead code were not redesigned or cleaned up.

Offline Slice 5 verification: **175 focused tests passed (5 warnings)**;
the newsletter plus Weekly idempotence suite passed **1,712 tests (421 warnings)**,
with zero failures. Existing framework/datetime/gzip warning debt remains outside
scope. Python compilation and tracked/new-test whitespace checks passed. Tests
cover both transports, the 100-message Resend boundary, complete-batch security,
Mongo scalar/array active-query semantics, fetched slots/caps, private failures,
global flag ordering, onboarding eligibility, accepted-only marking and snapshots
across awaits. The historical Announcement scope assertion is pinned to its
committed slice; a new live Slice 5 AST guard verifies all other production
functions, including Announcement, Daily, Weekly and Breaking News, are unchanged.
No production/deployment verification is claimed, no subscriber data was inspected
and no real email was sent. Full CT-DEC-021 remains incomplete and
**POTENTIAL QUERY LOG EXPOSURE** remains. At the Slice 5 checkpoint, manual campaigns
and production-readiness gates remained outstanding. Slice 5 is committed locally at `4503c28ef8b81d579626e29e33148796e6df2316` but has not been pushed or deployed; the protected local files were untouched.

Phase 2B **SLICE 6 MANUAL CAMPAIGN DIRECT DELIVERY IS COMMITTED LOCALLY — NOT
PUSHED/DEPLOYED**. Capability commit: `68cefd3` (`Integrate direct unsubscribe into manual campaigns`). The verified baseline is
`3fe466efebd6f950a83528cfa692d99cb86c7adc` on `full-scrape-prod`, 0 behind/8 ahead
of the locally recorded origin ref, with only the two protected files initially
untracked. Production changes are confined to `admin_send_campaign_email` and the
new `EmailService.send_manual_campaign` method. Real `mode=all` delivery retains
the exact active=True OR active-missing query and 10,000 fetched-position cap.
The full fetched identity set is validated before preparation; invalid email,
identity, version or non-explicit-True active positions are counted as bounded
skips, without backfill, provisioning or generic fallback. The dedicated sender
rejects raw/missing prepared contracts, resets diagnostics and verifies the entire
prepared batch before rendering or provider contact. Empty prepared sets return
integer zero without transport.

Arbitrary subject/HTML/text, existing placeholder semantics, generic preferences,
campaign-wide ManualCampaign tracking identity and HTML-only tracking pixels are
preserved. `__UNSUB_URL__` resolves to the same recipient-bound credential used by
native headers; it is not click-wrapped. Templates without placeholders are not
rewritten to add content. SMTP and Resend retain per-recipient isolation and
truthful acceptance/contact evidence, including partial/zero/unavailable outcomes.
Real-mode digest records retain historical fields and add aggregate selected,
prepared, skipped/reason, accepted and provider-contact evidence. Validation
errors remain 400; unexpected delivery/storage failures now have fixed private
500 details and bounded logging.

`mode=test` remains the existing single-address SMTP preview (including Admin
address fallback), with generic unsubscribe and no subscriber query, preparation,
direct credential issuance, native headers or new subscriber-delivery accounting.
Its historical explicitly test-mode digest record remains unchanged. No other
newsletter production functions were modified. The committed Slice 5 scope test
is pinned to `4503c28`; the new Slice 6 live AST guard compares against `3fe466e`.

Independent offline verification: **231 focused Slice 6/Slice 5 scope tests passed (5 warnings)**; full
newsletter plus Weekly idempotence regression: **1,813 passed (420 warnings)**,
zero failures. Python compilation, `git diff --check` and new-test whitespace
checks passed. Existing framework/datetime/gzip warning debt remains outside scope.
Tests cover preview isolation, content forms, query/projection/cap semantics,
invalid fetched positions, ambiguity, complete-batch security, SMTP MIME headers,
Resend 100/101 boundaries, acceptance/contact accounting and private failures.
No production data was inspected, no real email was sent and no deployment or
production verification is claimed. Full **CT-DEC-021 remains incomplete**;
**POTENTIAL QUERY LOG EXPOSURE** and all outstanding production-readiness gates
remain. Slice 6 is committed locally at `68cefd3` but has not been pushed or deployed;
protected local files remain untouched.

The last recorded production commit is `c2a6fb0`; this offline correction did not
re-inspect production. Render service
`cheshiretoday-migration-` (`srv-d5virmm3jp1c73c9d6tg`) is connected to
`julian07891-cmyk/cheshiretoday-migration-`, branch `full-scrape-prod`, with
**AUTO-DEPLOY ENABLED — ON COMMIT: NO PUSH WITHOUT EXPLICIT DEPLOYMENT
AUTHORIZATION**. Phase 2A is locally committed, not pushed or deployed. Full CT-DEC-021
remains incomplete and not production-ready. Live identity/index coverage, real
Mongo/BSON/concurrency evidence, upstream Render/proxy/CDN/APM log privacy,
delivered headers/DKIM, Apple Mail acceptance and controlled production persistence
remain gates. Overall **POTENTIAL QUERY LOG EXPOSURE** remains; the local filter
only addresses the Uvicorn access-record boundary. CT-QA-2026-007 remains closed;
the historical Apple Mail observation is **OBSERVED COMPATIBILITY FAILURE — ROOT
CAUSE UNPROVEN**, and proposed CT-QA-2026-008 is **NOT REGISTERED**. QA accounting
is unchanged.

### Generic management entry closure — 20 September 2026

`CT-QA-2026-007` (Medium at discovery) is **IMPLEMENTED, DEPLOYED AND
PRODUCTION-VERIFIED**. Commit `e6408133c48a98b2e22e8cf22a958bce7a922716`
(`Fix generic newsletter management entry states`) separates legitimate generic
entries from invalid credentials. Auto-Deploy `dep-dao287ajnfac739ab80g`, instance
`cqsqq`, became Live at 19:23:47 BST. All three generic management pages and
390×844 layouts passed; health/homepage returned 200. Six frontend suites / 96
tests and the production build passed. Security/token/backend contracts were
unchanged. No form submission or subscriber mutation occurred; live network
capture was unavailable, so zero-auto-request evidence remains code/test based.
See [the durable finding](QA/OPEN_FINDINGS.md) for full evidence and limitations.
The separate Apple Mail/iPhone email-CTA issue remains unresolved; this commit
did not change management-email URL generation or prove the transformation cause.

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
no distributed transaction is used. Production acceptance separately confirmed a
pre-existing identity-bearing newsletter logging defect; it was not caused by or
stored in the anonymous Funnel V1 aggregate. `CT-QA-2026-006` is now **CLOSED —
IMPLEMENTED, TESTED, DEPLOYED AND PRODUCTION-VERIFIED**. Commit `03a6abb`
removed subscriber/recipient identity and uncontrolled exception text from the
bounded subscribe, welcome, shared SMTP, scheduled and Admin diagnostic paths
while preserving delivery and subscriber behaviour. Historical logs were not
altered, every failure branch was not naturally exercised in production, and no
legal/privacy-compliance claim is made.

Deployment `dep-daneoh6q1p3s73cdmf9g` automatically deployed exact SHA
`03a6abbd5133de969275477488ea49bb34242ee0` to Standard instance `zpcmz`
(1 CPU/2 GB, one instance). It started at 21:10:44 BST on 19 September 2026,
built at 21:12:25, completed application startup at 21:13:12 and became Live at
21:13:17. Uvicorn, Mongo/index and APScheduler startup succeeded, expected
article-generation, Daily Brief and Weekly Roundup registrations were present,
and no changed-variable or newsletter/email logging-format failure was observed.
Health, homepage, `/newsletter` and a representative article returned HTTP 200;
bounded post-Live observation found no attributable traceback, fatal error, OOM,
exit 137, restart or material 5xx. Verification involved no manual deployment,
restart, signup, test send, import, subscriber mutation or production-data
mutation.

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
4. Investigate the separate Apple Mail/iPhone management-email CTA compatibility
   issue read-only: the blue CTA failed while the complete fallback link worked.
   The generic-entry UX defect is closed as `CT-QA-2026-007`; the precise email-link
   transformation remains unproven and no email URL change is approved here.
5. Keep inactive-subscriber hygiene as future work after that audit. Do not delete
   subscribers merely because no open was recorded; first analyse engagement
   history, account age, open/click evidence and tracking limitations, preview the
   affected population and define a safe deactivate/delete policy.
6. Measure/design the remaining post-handler/client TTFB residual read-only before
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
