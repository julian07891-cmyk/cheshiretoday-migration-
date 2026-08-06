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

## Protected addresses and dry-run review

Reserved/test/invalid addresses are filtered by current delivery safeguards. Before any approved send, review content, recipient count, preference filter, cap, batch slot and provider configuration without dispatching. Test endpoints are still production mutations and require explicit authority.

## Deactivation safeguards

Do not bulk deactivate from bounce-like symptoms, scanner noise or missing engagement. Require reconciled provider rejection evidence, accepted-recipient history and the current protected-address rules. Prefer soft lifecycle state over deletion, and obtain production approval.

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
