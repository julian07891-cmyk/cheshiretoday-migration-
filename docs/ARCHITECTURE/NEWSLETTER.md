# Cheshire Today — Newsletter Architecture

> **Reconstruction status:** Current code capability at HEAD; provider enablement, recipient counts and recent deliveries require production evidence.

## Document purpose

Describe subscriber lifecycle, scheduled digests, delivery accounting, tracking and secure self-service.

## Authority and evidence

Primary evidence: `backend/server.py`, `backend/app/email_service.py`, newsletter token/challenge/runtime modules in `backend/app/`, `frontend/src/pages/NewsletterPage.jsx`, secure management components, and `tests/test_newsletter_*.py`. See [Source Register](../HISTORY/SOURCE_REGISTER.md).

## How to use this document

Use this for design and code ownership. Operators should use [Newsletter Operations](../OPERATIONS/NEWSLETTER_OPERATIONS.md) before investigating or authorising a send.

## Subscriber lifecycle

`POST /api/newsletter/subscribe` creates or recognises subscribers without silently overwriting established preferences. Eligibility queries require active subscribers and the relevant preference. Inactive subscribers are excluded. Public signup, Admin management and secure self-service are distinct boundaries.

Newsletter Funnel V1 measures public signup outcomes without changing that
lifecycle. The backend records anonymous daily attempts and `created`, `existing`
or `failed` outcomes by canonical placement; retries remain attempts and existing
addresses retain their existing state. Measurement failure is fail-open. The
aggregate has no subscriber identity or request-level reader data, uses exact
13-calendar-month TTL retention, and has no historical backfill. Production
acceptance passed on 19 September 2026 for one controlled authorised created
subscriber and matching Admin aggregate reporting. The separate pre-existing
newsletter logging defect is now `CT-QA-2026-006` **CLOSED — IMPLEMENTED,
TESTED, DEPLOYED AND PRODUCTION-VERIFIED** through commit `03a6abb`. This logging
hardening did not change Funnel V1 or subscriber behaviour.


## Provider suppression and delivery eligibility — CT-DEC-022

Cheshire Today subscription lifecycle and provider delivery eligibility are separate states. `active` remains the subscription/consent lifecycle field; a provider block must not be represented as an unsubscribe. A subscriber with explicit `provider_suppressed=true` is ineligible for subscriber-content delivery even when locally active and opted into the relevant newsletter. Absence of that explicit value remains backward-compatible and means no known local provider block.

The provider-suppression metadata contract is `provider_suppressed=true`, `provider_suppression_reason` (`complaint` or `bounce`), `provider_suppressed_at` as a UTC datetime and `provider_suppression_source="resend"`. Query-capable subscriber-content paths exclude explicit suppression before selection/caps and project the field for defence-in-depth preparation. The shared candidate-context guard also rejects an explicitly suppressed record if one reaches preparation. Onboarding intentionally retains its broad identity fetch and excludes suppressed records from its due population.

Provider suppression does not change preferences or `active`, and normal reactivation must not silently clear provider suppression. Migration-announcement preference migration remains independent from its delivery audience. Complaint suppressions are not application reactivation candidates. Provider-side unsuppression remains a separate controlled operation requiring evidence and approval. Transient message-level bounce events alone must not be converted into permanent local provider suppression.

D-1 coverage includes scheduled/manual Daily Brief, scheduled/diagnostic Weekly Roundup, Breaking News, migration announcement, Site Update parts 1/2, onboarding and subscriber-targeted manual campaigns. Combined affected regression passed 403 tests with zero failures. D-1 was committed as `34ecf74`, deployed Live on that exact commit and production health-verified HTTP 200. The authoritative 24 September 2026 Resend suppression population was subsequently reconciled into the metadata contract: **815 exactly reconciled**, comprising **785 bounce and 30 complaint**, with **583 locally active and 232 inactive/legacy**. Independent post-write verification found zero records requiring further reconciliation and zero unexpected suppression source/reason values. This local provider-state reconciliation made no Resend unsuppression, subscription lifecycle, preference, transport or DNS change and does not establish inbox placement or remediation of the separate Apple/iCloud Junk issue.

## Daily Brief

`send_scheduled_news_digest` acquires a date-keyed lock, selects active Daily Brief recipients, applies configured caps and a fair Mongo-backed rotating cursor, selects eligible public articles, then calls `EmailService.send_daily_brief`. The current schedule is Monday–Saturday at 07:30 Europe/London.

## Weekly Roundup

`send_weekly_roundup_email` uses four Sunday batch slots at 09:00, 10:00, 11:00 and 12:00. Batch one prioritises organic website subscribers before engaged readers; later batches continue without wraparound. Its content composition differs from the Daily Brief and can include a Big Read and other roundup sections.

Commit `5559499` made the idempotence identity slot-aware on
`(digest_time, date_key, weekly_roundup_batch_slot)` and protects the `claimed`,
`sending`, `sent`, `partial`, `failed` and `ambiguous` lifecycle states. Natural
production verification completed on 6 September 2026: all four scheduled slots
recorded 1,000/1,000 application/provider-path acceptance, distinct tracking
identities and sequential cursor advancement to 996, 1996, 2996 and 3996, with
no observed `E11000` conflict. The slot-aware unique index was also confirmed at
subsequent production startup. This verifies slot identity and natural execution,
not final inbox delivery, readership, bounce-free delivery or perfect
deliverability.

## Delivery providers and diagnostics

`EmailService` supports Resend batch delivery and an explicitly configured SMTP path. Resend/SMTP selection is environment-dependent. Provider diagnostics and `last_accepted_recipients` are reset per send attempt. Successful acceptance is not equivalent to inbox delivery.

Commit `03a6abb` removed subscriber/recipient identity from operational
newsletter logging. Subscriber creation no longer logs subscriber identity;
welcome outcomes are bounded to accepted/not-accepted; welcome/subscribe and
shared SMTP failures use bounded categories or exception classes rather than
arbitrary exception text; SMTP diagnostics expose configuration presence only;
scheduled Daily Brief invalid-address diagnostics retain counts without
addresses; Admin Daily Brief and Weekly Roundup test-send logs omit destinations;
and Resend/provider diagnostics omit raw response bodies and recipient-derived
identity. `resend_last_error` remains a bounded operational diagnostic and may
populate `digest_log.provider_error`. Legitimate delivery/database use of email
addresses is unchanged. Historical logs were not erased, and this engineering
closure is not a legal/privacy-compliance claim.

## Tracking and accepted-recipient ledger

Email content uses per-recipient derived tracking IDs. Open pixels and click redirect endpoints record first-party email analytics. After accepted sends, `_record_email_send_opportunity` stores privacy-preserving recipient hashes, counts and tracking identity in `email_send_opportunities`; raw recipient addresses are not the ledger contract.

## Secure preference management

Preference, unsubscribe and reactivation request-link flows use generic public responses, purpose-specific collaborators, IP/email rate-limit reservations, stored challenges and short-lived signed tokens. Secure verification/update endpoints enforce purpose and challenge eligibility. One-click unsubscribe has its own contract. Replay and stale-token protections are covered by focused tests.

### Generic management entry presentation — CT-QA-2026-007

Commit `e6408133` separates generic, token, invalid and retired frontend entry
states. Clean no-token preferences/unsubscribe/reactivation routes show neutral
request-link UI; supplied malformed/empty/overlong credentials remain invalid.
Unsupported query credentials, retired links, valid token flows and fragment
capture/scrubbing are preserved. Requesting an unsubscribe link does not itself
unsubscribe the reader. No automatic request or backend/security-contract change
was introduced. The generic-entry fix is **IMPLEMENTED, DEPLOYED AND
PRODUCTION-VERIFIED**; [QA evidence](../QA/OPEN_FINDINGS.md) records the bounded
mobile/production checks and unavailable live-network-capture limitation.
The separate iPhone Apple Mail management-email CTA issue remains unresolved;
email URL generation was unchanged and the precise link transformation is unproven.

## Approved direct unsubscribe contract — 21 September 2026

**FUNCTIONAL PRODUCTION ACCEPTANCE COMPLETE — UPSTREAM QUERY-LOG PRIVACY GATE OPEN** under
[CT-DEC-021](../DECISION_REGISTER.md#ct-dec-021--direct-newsletter-unsubscribe-with-secure-recovery-retained).
The chain was deployed and functionally accepted at `2f40374` on 23 September 2026:
live identity/index, controlled Resend delivery, Apple Mail/native headers and DKIM,
native unsubscribe/replay, human confirmation, reactivation/version rotation,
stale-token rejection, active preferences/consumed challenge and new-signup
transactional welcome all passed. See the bounded
[production evidence](../PRODUCTION_TIMELINE.md#23-september-2026--ct-dec-021-functional-production-acceptance).
This is not upstream logging/privacy acceptance. Later pushed `40304fc` only
changes welcome coverage copy; the earlier received email does not verify it.
Normal subscriber-newsletter flow: signed footer link → confirmation page →
explicit Confirm unsubscribe → inactive subscription. No email re-entry or second
email. Signup remains email → Subscribe → success. Preferences remain separate
and challenge-backed. Generic `/unsubscribe` retains neutral email-entry recovery,
the request endpoint, management email and challenge creation/delivery/consumption.

### Credentials and mutation

Direct credentials must have a distinct authenticated class, purpose, management
UUID, current `newsletter_token_version` and bounded expiry, with no subscriber
email. The direct schema is exactly `sub`, `purpose`, `ver`, `iat`, `exp` and
`credential_class`; `purpose="unsubscribe"` and
`credential_class="newsletter_direct_unsubscribe"`. `sub` is a canonical UUID4,
`ver` a positive integer excluding booleans, and timestamps integer UTC seconds.
Use the existing HS256 signing architecture and strict header validation.
Issue for exactly **90 days** (`exp - iat = 7,776,000` seconds), validating that
duration as well as expiry/future issuance with the existing 60-second skew.
Thirty days gives a short recovery horizon for older weekly messages; 180 days
unnecessarily doubles bearer exposure versus 90. Ninety days covers roughly
thirteen weekly editions while version revocation handles reactivation. This is
a bounded product choice, not an observed readership-age statistic.
Never infer exemption from missing challenges or token lifetime.
Endpoints expecting other credential classes must reject this class. Recovery
tokens still require delivered challenges; only direct newsletter credentials
are intentionally challenge-free.

Existing recovery/preferences/reactivation tokens keep the exact original five
claims and validators unchanged. Add a separate strict six-claim direct validator;
legacy validators reject the extra claim and the direct validator rejects missing,
unknown or wrong-class claims. Only unsubscribe confirmation/one-click dispatch
may accept either class, after cryptographic validation; no caller-controlled
skip-challenge flag or permissive fallback on validation failure. Both entrypoints
share one direct atomic mutation helper; recovery retains its existing processor.

Website URL: `https://cheshiretoday.co.uk/unsubscribe#token=<REDACTED_TOKEN>`.
Reuse capture/scrubbing. GET never mutates. Display “Confirm unsubscribe” and
“Are you sure you want to unsubscribe from Cheshire Today newsletters?” with an
explicit confirmation button, then a clear unsubscribed state and home link.
No email field or second email on the valid direct path.
Mutation validates signature, class, purpose, expiry, identity and current version,
using an atomic version guard. Concurrent reactivation must defeat a stale update.
Already-inactive success is permitted only after current-version validation.

### Native protocol and production gates

Eligible messages receive per-recipient headers on both Resend and SMTP:

```text
List-Unsubscribe: <https://cheshiretoday.co.uk/api/newsletter/unsubscribe/one-click?token=<REDACTED_TOKEN>>
List-Unsubscribe-Post: List-Unsubscribe=One-Click
```

The endpoint mutates only on protocol POST with the expected form body;
ordinary GET/prefetch never unsubscribes. Direct-class credentials require no
recovery challenge; existing recovery credentials remain challenge-dependent.
This does not protect against software deliberately issuing a valid protocol POST.
Preserve batches, schedules, eligibility, accepted-recipient accounting and privacy-
safe logging; never share one recipient's credential across a batch.

Delivered header values, passing DKIM covering both unsubscribe headers and Apple
Mail native/human acceptance are now verified. Independent manual comparison of
the human/native token strings was not recorded; shared-token binding is an
implementation guarantee, not an additional raw-source observation.
The startup-installed Uvicorn filter protects its supported access records and
the committed start command is not TRACE. Upstream Render/proxy retention remains
unverified because Request Logs are unavailable at the current plan/access level.
Client-side httpx INFO output exposed an already-stale credential URL during the
stale-token acceptance request. The application filter does not cover that logger.
**POTENTIAL QUERY LOG EXPOSURE** remains; no token or URL from that event is retained.

### Historical design prerequisites and bounded scope — 21 September 2026

The inventory and unverified-gate wording below record the pre-rollout design
checkpoint, not current production state. Identity/index and functional gates are
now satisfied as recorded above; upstream query privacy remains unresolved.

- Tracked subscriber-write inventory at `52c9b64`: public signup creates new
  UUID/version-1 records only; existing signup does not reactivate. Secure
  reactivation is the only identified inactive-to-active writer and atomically
  increments version. Secure/Admin unsubscribe deactivate; secure preferences
  requires active state and updates preferences only; announcement updates a
  preference only; site-update jobs write sent timestamps only. Management-ID
  migration is an explicit CLI updating identity/version fields only, and email
  unique-index provisioning does not activate records. Scheduler/diagnostic
  readers and HTTP support tests add no alternate activation writer. No unsafe
  activation path was found in tracked runtime/operational code; untracked or
  external operational writes are not certified. Retain atomic version-race tests.
- Live identity coverage was not inspected. Legacy records are conceptually
  possible; recipient queries accept missing active fields and builders currently
  receive email lists. Require bounded aggregate-only UUID/version coverage before
  rollout. **LIVE IDENTITY COVERAGE UNVERIFIED**; no counts are inferred.
  Implementation may fail closed for legacy records: skip the affected content
  recipient before send if UUID/version is absent, malformed or ambiguous; issue
  no credential, do not silently substitute generic links, and record bounded
  aggregate skip counts without identity. Preserve acceptance accounting (skips
  are not sends). No send-time provisioning. Classification: **IMPLEMENTATION CAN
  FAIL CLOSED FOR LEGACY RECORDS, BACKFILL SEPARATE**. Quantify impact before rollout.
  The migration defines a non-sparse unique management-ID index; its live presence
  is not proven here. No database schema validator guarantees all historical fields.
- Daily Brief/Weekly Roundup use Resend batch or SMTP. Breaking News,
  announcements/site updates use SMTP builders. The manual campaign route is an
  additional subscriber-content path requiring explicit inclusion when sent to the
  subscriber audience. All need per-recipient context and HTML/text/footer/header
  review. Local Phase 2B integration now supplies the approved per-recipient direct
  footer and native unsubscribe headers for these subscriber-content paths.
- Welcome is classified **transactional onboarding**, excluded from native headers:
  it follows signup and explains the subscription, rather than serving as a content
  digest. Existing visible management links/copy stay unchanged. Security/management,
  job verification and unrelated transactional mail must not inherit headers.
- Likely runtime scope: token service, server recipient-context/mutation wiring,
  email builders/transports, and necessary confirmation copy only. Keep signup,
  preferences, reactivation semantics, recovery infrastructure and scheduling intact.
  Tests must cover class separation, atomic races, stale versions, inactive replay,
  all transports/builders, GET safety, generated-link round trips and recovery.

Local implementation requirements are specified; production gates remain. Query
logging classification is **POTENTIAL QUERY LOG EXPOSURE**, not proven safe.
Add a narrowly scoped Uvicorn access-log query redaction control for the one-click
path, test exception/request diagnostics and inspect upstream logs independently.
Moving the secret into a path still exposes it to access logs; a fragment cannot
reach the native server and the protocol body is fixed, so retain the approved
query transport rather than inventing a nonstandard header/body credential.
Provider receipt of the bearer is inherent; never claim zero provider visibility.
Resend now supports opt-in per-message `headers` forwarding in `_send_resend_batch`
locally; SMTP supports explicit `newsletter_headers` in `_send_email`. Allocate recipient-specific
objects; security mail must not inherit defaults. Delivered DKIM, client behaviour,
upstream log privacy and active-identity coverage remain acceptance gates, not
blockers to isolated local implementation. No live database/log inspection occurred.

At this historical checkpoint, local implementation was complete through Slice 6
but production acceptance was not yet claimed. Current acceptance is recorded
above. CT-QA-2026-006 and CT-QA-2026-007 remain closed; no new QA ID, accounting
change or legal/compliance claim follows from this reconciliation.

### Historical Phase 2A local delivery infrastructure checkpoint

Phase 1 is committed locally as `516fa29`, not pushed or deployed. Phase 2A is
privacy-corrected locally, unstaged and re-reviewed; Phase 2B is not implemented.
`newsletter_delivery.py` owns frozen, repr-safe three-field recipient contexts,
bounded validation outcomes, supplied-candidate ambiguity detection and immutable
direct artifacts. The email policy mirrors the existing server validator under a
parity test, without changing selectors. Positive Python/BSON integers are accepted;
bool/string/float coercion is forbidden. Candidate preparation preserves order and
rejects all detected conflicting-address or repeated canonical-management-ID peers,
including identical repeated IDs; it is not a database-wide uniqueness audit.

Artifact preparation calls the Phase 1 issuer once and reuses the credential for
the canonical human fragment and native query URL. Sensitive fields are excluded
from repr, and the immutable internal header Mapping redacts repr/str, including
nested and exception/log interpolation. Its explicit `as_transport_dict()` export
returns a fresh sensitive dictionary only for transport use. Explicit value lookup
and exported dictionaries are not safe to log or serialize generically. Validation
uses temporary copies; no mutable dictionary is retained in the header container.
Errors contain fixed categories. These are internal objects, not log/API payloads.
Header validation permits exactly the two native names, canonical HTTPS endpoint,
one token parameter and the fixed POST value; it rejects injection, alternate
destinations and malformed compact-JWT syntax. It does not replace endpoint
signature/claim validation. Resend prevalidates all supplied headers before contact,
then preserves 100-message chunks and existing acceptance/failure behavior. SMTP
uses keyword-only opt-in headers; existing callers receive none. No new send-result
type or scheduler-accounting migration is necessary for this phase.

`newsletter_access_logging.py` installs an idempotent filter during server import.
It removes the entire query from the pinned Uvicorn five-argument access record
for the one-click path, including origin/absolute-form and trailing-slash targets,
without modifying ASGI scope or unrelated records. Identifiable sensitive
preformatted/unsupported records and sanitizer failures are suppressed, not emitted
raw. Real h11 protocol/formatter tests use an in-memory transport and confirm
original queries still reach the synthetic ASGI endpoint, including signed-token
verification; protocol-rejected requests never reach ASGI. Route lookalikes remain
unchanged. Uvicorn 0.25.0 httptools is supported by static inspection only.
Both material local-review findings are corrected and were never deployed.
This establishes local protection for covered shapes only, not infrastructure
privacy: overall **POTENTIAL QUERY LOG EXPOSURE** remains.

All current content builders, generic unsubscribe destinations, subscriber
selection, transactional copy and accounting remain unchanged. Phase 2B must also
address missing visible Breaking News/announcement footers, accepted-only onboarding
markers, mandatory subscriber-campaign footers and bounded outer exception
diagnostics. Broader historical `str(e)` cleanup is not part of Phase 2A.
Final local re-review verification: 1,407 newsletter tests passed with no failures; Python
compilation and tracked `git diff --check` also passed. Existing framework/datetime/gzip
warnings remain. Real Mongo and all production gates above
remain outstanding. Render auto-deploy is enabled on commit for `full-scrape-prod`;
no push is permitted without explicit production-deployment authorization.

## Failure boundaries

Digest locks prevent duplicate scheduled ownership. Provider diagnostics distinguish disabled, unconfigured, rejected and indeterminate outcomes. Failed management-email delivery does not reveal subscriber existence. Digest logging and ledger failures are reported separately from provider acceptance.

## Protected boundaries

Never expose subscriber addresses, tokens or hashes. Do not bypass active/preference filters, protected-address rules, request-link enumeration resistance, rate limits, replay controls, digest locks or accepted-recipient accounting. Production sends require explicit authority.

## Known limitations

Scanner traffic can inflate opens/clicks. Accepted counts are provider acceptance, not human readership. SMTP code remains available but operational selection cannot be inferred from source. Subscriber state repairs and deactivation require production evidence and separate approval.

## Related documents

[Architecture Master](../ARCHITECTURE_MASTER.md), [Scheduler](../OPERATIONS/SCHEDULER.md), [Newsletter Operations](../OPERATIONS/NEWSLETTER_OPERATIONS.md), [Analytics](ANALYTICS.md), and [Editorial Evolution](../EDITORIAL_EVOLUTION.md).
