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

## Daily Brief

`send_scheduled_news_digest` acquires a date-keyed lock, selects active Daily Brief recipients, applies configured caps and a fair Mongo-backed rotating cursor, selects eligible public articles, then calls `EmailService.send_daily_brief`. The current schedule is Monday–Saturday at 07:30 Europe/London.

## Weekly Roundup

`send_weekly_roundup_email` uses four Sunday batch slots at 09:00, 10:00, 11:00 and 12:00. Batch one prioritises organic website subscribers before engaged readers; later batches continue without wraparound. Its content composition differs from the Daily Brief and can include a Big Read and other roundup sections.

## Delivery providers and diagnostics

`EmailService` supports Resend batch delivery and an explicitly configured SMTP path. Resend/SMTP selection is environment-dependent. Provider diagnostics and `last_accepted_recipients` are reset per send attempt. Successful acceptance is not equivalent to inbox delivery.

## Tracking and accepted-recipient ledger

Email content uses per-recipient derived tracking IDs. Open pixels and click redirect endpoints record first-party email analytics. After accepted sends, `_record_email_send_opportunity` stores privacy-preserving recipient hashes, counts and tracking identity in `email_send_opportunities`; raw recipient addresses are not the ledger contract.

## Secure preference management

Preference, unsubscribe and reactivation request-link flows use generic public responses, purpose-specific collaborators, IP/email rate-limit reservations, stored challenges and short-lived signed tokens. Secure verification/update endpoints enforce purpose and challenge eligibility. One-click unsubscribe has its own contract. Replay and stale-token protections are covered by focused tests.

## Failure boundaries

Digest locks prevent duplicate scheduled ownership. Provider diagnostics distinguish disabled, unconfigured, rejected and indeterminate outcomes. Failed management-email delivery does not reveal subscriber existence. Digest logging and ledger failures are reported separately from provider acceptance.

## Protected boundaries

Never expose subscriber addresses, tokens or hashes. Do not bypass active/preference filters, protected-address rules, request-link enumeration resistance, rate limits, replay controls, digest locks or accepted-recipient accounting. Production sends require explicit authority.

## Known limitations

Scanner traffic can inflate opens/clicks. Accepted counts are provider acceptance, not human readership. SMTP code remains available but operational selection cannot be inferred from source. Subscriber state repairs and deactivation require production evidence and separate approval.

## Related documents

[Architecture Master](../ARCHITECTURE_MASTER.md), [Scheduler](../OPERATIONS/SCHEDULER.md), [Newsletter Operations](../OPERATIONS/NEWSLETTER_OPERATIONS.md), [Analytics](ANALYTICS.md), and [Editorial Evolution](../EDITORIAL_EVOLUTION.md).
