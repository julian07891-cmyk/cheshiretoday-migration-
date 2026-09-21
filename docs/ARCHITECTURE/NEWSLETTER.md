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

## Failure boundaries

Digest locks prevent duplicate scheduled ownership. Provider diagnostics distinguish disabled, unconfigured, rejected and indeterminate outcomes. Failed management-email delivery does not reveal subscriber existence. Digest logging and ledger failures are reported separately from provider acceptance.

## Protected boundaries

Never expose subscriber addresses, tokens or hashes. Do not bypass active/preference filters, protected-address rules, request-link enumeration resistance, rate limits, replay controls, digest locks or accepted-recipient accounting. Production sends require explicit authority.

## Known limitations

Scanner traffic can inflate opens/clicks. Accepted counts are provider acceptance, not human readership. SMTP code remains available but operational selection cannot be inferred from source. Subscriber state repairs and deactivation require production evidence and separate approval.

## Related documents

[Architecture Master](../ARCHITECTURE_MASTER.md), [Scheduler](../OPERATIONS/SCHEDULER.md), [Newsletter Operations](../OPERATIONS/NEWSLETTER_OPERATIONS.md), [Analytics](ANALYTICS.md), and [Editorial Evolution](../EDITORIAL_EVOLUTION.md).
