# Cheshire Today — Newsletter Operations Runbook

> **Reconstruction status:** Safe procedures derived from current HEAD. Live provider, recipient and delivery state must be verified without exposing personal data.

## Document purpose

Provide an operator-facing, privacy-preserving process for Daily Brief, Weekly Roundup and subscriber-delivery incidents.

## Authority and evidence

Primary evidence: `send_scheduled_news_digest`, `send_weekly_roundup_email` and ledger helpers in `backend/server.py`; `backend/app/email_service.py`; secure newsletter modules and tests. See [Source Register](../HISTORY/SOURCE_REGISTER.md).

## How to use this document

Begin read-only. Use normal scheduled evidence unless a send or state mutation has separate explicit approval.

## Daily Brief status check

1. Confirm deployed commit, health and scheduler ownership.
2. Use the Mon–Sat 07:30 Europe/London window.
3. Capture the Daily Brief lock, eligible count, rotating batch/cap, selected public content, provider result, accepted count, ledger result, digest-log entry and cursor update.
4. Confirm no duplicate slot execution and no protected/private content was selected.

## Weekly Roundup status check

Review Sunday batch slots at 09:00–12:00 separately. Confirm batch number, priority-recipient allocation, continuing engaged-reader slice without wraparound, provider/accepted counts, ledger and digest log. Do not add counts across retries without identifying the same tracking/batch identity.

## Provider diagnostics

Distinguish disabled, unconfigured, attempted, accepted, rejected and indeterminate states. Resend and SMTP are environment-controlled paths. Redact provider response details that may contain addresses, IDs or tokens. Do not switch provider settings as a diagnostic shortcut.

## Accepted-recipient ledger

`email_send_opportunities` should contain the digest/tracking identity, acceptance time, accepted count and privacy-preserving recipient hashes. Compare accepted count with provider diagnostics and digest log. Never report or reverse hashes and never substitute the ledger for proof of inbox delivery.

## Subscriber eligibility

Daily/weekly queries must require `active=True` and the appropriate preference/default compatibility rule. Verify `active=False` exclusion through code/tests or a bounded aggregate, not by revealing subscriber rows. Inactive-subscriber diagnosis requires dated provider and ledger evidence, not a single open/click absence.


## Provider suppression reconciliation — CT-DEC-022

Treat provider suppression as delivery eligibility, not subscription withdrawal. `active` and newsletter preferences remain Cheshire Today lifecycle state. An explicit local `provider_suppressed=true` blocks subscriber-content delivery; absence of that value does not assert that the provider will accept or deliver a message.

D-1 is deployed and establishes the application eligibility guard. Before any new reconciliation, obtain current provider suppression evidence and compare it with subscriber state using privacy-safe aggregate output only. Classify provider suppression reasons separately as `complaint` or `bounce`; retain the provider suppression timestamp and source where available. Do not expose recipient addresses in diagnostic output.

Reconciliation must begin as a dry run. Report aggregate provider records, unique matched subscribers, locally active/inactive matches, reason counts, unmatched records and proposed changes. Counts must reconcile before any write. Do not derive permanent local suppression from ordinary/transient bounce-event history: provider suppression-list state is distinct from message-level bounce events. Normalize provider timestamps to BSON millisecond precision before exact MongoDB write/read comparison; source timestamps may carry sub-millisecond precision that BSON Date cannot preserve.

Never remove complaint suppressions as part of reactivation or routine reconciliation. Normal newsletter reactivation must not clear provider suppression. Do not unsuppress recipients at Resend, mutate production subscriber records or alter lifecycle/preferences without separate explicit approval. Preserve evidence and take a bounded private backup before an approved bulk local mutation. Use transactional writes with exact target counts and verify the intended fields inside the transaction before allowing commit; on any mismatch, abort and independently verify production state before considering another attempt.

The 24 September 2026 reconciliation used the authoritative 815-record Resend suppression export: 785 bounce and 30 complaint. All 815 matched exactly one subscriber; 583 were active and 232 inactive/legacy. The protected backup contained the exact 815 target IDs. The first approved transaction aborted before commit because 60 source timestamps contained sub-millisecond precision and therefore failed exact comparison after BSON storage; immediate read-only verification confirmed no reconciliation changes had committed. After millisecond normalization and an independent BSON round-trip test, the corrected transaction committed **815 matched / 815 modified / 815 exact post-write**. Independent post-commit verification returned **815 exact / 0 requiring change / 0 non-exact**, and global aggregates independently confirmed 815 suppressed, 583 active, 232 inactive/legacy, 785 Resend bounce, 30 Resend complaint and zero unexpected source/reason.

After any approved local reconciliation, independently verify aggregate before/after counts, exact changed-record count and that suppressed records are excluded from delivery eligibility before caps/selection. Deployment of D-1, population of suppression metadata and provider-side changes remain separate actions and must be recorded separately. The completed local reconciliation did not unsuppress any address at Resend and does not establish inbox placement or remediation of the separate Apple/iCloud Junk issue.

## Protected addresses and dry-run review

Reserved/test/invalid addresses are filtered by current delivery safeguards. Before any approved send, review content, recipient count, preference filter, cap, batch slot and provider configuration without dispatching. Test endpoints are still production mutations and require explicit authority.

## Deactivation safeguards

### Cold-report correction — 23 September 2026

The admin-authenticated GET cold-report remains read-only/dry-run. Its local
replacement uses `email_send_opportunities`, not missing analytics rows, as the
accepted-send denominator. The producer writes only accepted recipient hashes,
deduplicates them and upserts by tracking identity. The report requires a positive
integer accepted count matching unique valid hashes, a recognised Daily/Weekly
digest and provider, and a valid nonfuture acceptance time. Each recipient counts
once per opportunity; repeated tracking identities cannot inflate the count.

Default minimum is five, clamped to 5–100 via `min_accepted_sends`. Existing
`days` defaults to 30 (7–180); use 90 explicitly for the investigation window.
Only opportunities in that window count. Any recorded open/click in retained
analytics history vetoes candidacy, even outside the window. No analytics row
alone and no ledger evidence can never establish candidacy.

Preserved active/legacy-active and Daily eligibility, valid-address, priority,
website/organic and own-domain protections apply first. Recent subscription
protection remains 21 days by default (1–90); Mongo datetimes and ISO strings are
normalised to UTC. Unknown age is now conservatively excluded. Duplicate eligible
email records cannot hide a protected or recent peer. The report streams reads
without silently truncating engagement evidence.

Response compatibility: `sample`, `tracked_hashes`, `engaged_hashes` and the two
old tracking/no-tracking cold breakdowns are removed. `sample_limit` remains an
ignored input for legacy callers. No repository UI caller depended on these fields.
New outputs are aggregate counts, accepted-send count distribution and valid ledger
coverage dates. Recipient metrics/distribution describe the population after
eligibility/protection/age exclusions; engaged and insufficient-evidence counts
can overlap. Ledger coverage spans all valid retained rows, while opportunity
counts use the configured window. Invalid ledger rows are counted and excluded.
No raw addresses, hashes, tracking identities or tokens are returned. Unexpected
failures return a fixed private 503, not exception text.

Acceptance is not delivery and short hash collisions/tracking limitations remain.
Candidates require review and separately authorised lifecycle action; no automatic
deactivation endpoint, hard deletion or reactivation is added.

### Deployment verification — 24 September 2026

Commit `3763aa6` was confirmed live in production and `/api/health` returned healthy.
A read-only 90-day report with `min_accepted_sends=5` returned 11,673 active
Daily-eligible subscribers, 11,669 recipients with accepted-send evidence, 5,202
with insufficient accepted-send evidence and zero current cold candidates. The
accepted-send ledger contained 102 valid opportunities, zero invalid rows, and
coverage from 14 July through 23 September 2026. The response exposed aggregate
data only: no subscriber addresses, recipient hashes, tracking identities or tokens.
The report remained `dry_run=true`; it performed no lifecycle mutation or deletion.

### Production evidence and separately controlled deactivation

Owner-supplied 23 September evidence: the old 90-day report had 14,095 active Daily
unique addresses, 0 invalid, 4 protected/organic, 0 recent, 6,131 engaged/tracked
hashes and 8,040 alleged cold candidates, all solely missing recent tracking.
Analytics had 35,881 rows (35,240 opened, 4,568 clicked), zero rows with both
counters zero. It is engagement/event evidence, not a sent-recipient roster.

Ledger coverage was 14 July 2026 06:30:12.077 to 23 September 2026
06:30:12.925: 102 rows, accepted-count sum 101,599, 14,129 unique accepted hashes.
Accepted-send/no-engagement distribution: 9 recipients with 3, 4,910 with 4 and
2,422 with 5; none above 5. The five-send cohort was active, had zero recorded
engagement, 65–67 days between first/last acceptance, 170-day subscription age,
no protected/organic members, no missing/unparseable ages and none within 30/60/90
days of signup. This historical selection also considered span and age; the new
generic report does not claim to reproduce that exact cohort with every parameter.

After an outside-repository backup of exactly 2,422 records, a separately approved
production operation deactivated them; the application report did not perform it.
Total remained 14,267; active 14,095 → 11,673; inactive 172 → 2,594; active Daily
eligible 14,095 → 11,673. Records received `active=False`,
`cold_deactivated_at` and
`cold_deactivation_reason="5_provider_accepted_sends_zero_recorded_engagement_65_67_day_span"`.
This implementation neither modifies those markers nor reactivates the cohort.
Evidence was supplied by the operator, not repeated during this local correction.

Do not bulk deactivate from bounce-like symptoms, scanner noise or missing engagement alone. Require reviewed accepted-recipient history, age/span and current protected-address rules; reconcile provider rejection evidence when relevant. Prefer soft lifecycle state over deletion, and obtain production approval.

## Secure-management incidents

For request-link, preference, unsubscribe or reactivation issues, capture generic response, status, purpose, rate-limit/challenge outcome and relevant non-sensitive log code. Never expose signed links or tokens. Do not bypass replay, expiry or enumeration protections.

## Incident response

- Duplicate send: preserve lock/digest/provider evidence, stop before manual resend, and escalate.
- Provider failure: classify status and scope; do not change credentials or provider flags without approval.
- Ledger mismatch: compare one bounded batch; preserve evidence before repair.
- Tracking anomaly: account for scanners and redirect behaviour; do not infer unique readers.
- Subscriber-security failure: escalate immediately and avoid replaying real links.

## Actions requiring explicit production approval

Any send/test-send, preference or subscriber mutation, deactivation/reactivation, cursor or lock repair, digest-log edit, provider/environment change, database migration, schedule change or service restart.

## Protected boundaries

Preserve active/preference filtering, rotating batches, priority-recipient rules, locks, accepted-recipient accounting, secure tokens/challenges, rate limiting and privacy.

## Known limitations

Provider acceptance is not delivery; opens/clicks include scanner noise; environment activation is external; and a read-only investigation cannot prove inbox placement.

## Related documents

[Newsletter Architecture](../ARCHITECTURE/NEWSLETTER.md), [Scheduler](SCHEDULER.md), [Monitoring](MONITORING.md), [Deployment](DEPLOYMENT.md), and [Analytics](../ARCHITECTURE/ANALYTICS.md).
