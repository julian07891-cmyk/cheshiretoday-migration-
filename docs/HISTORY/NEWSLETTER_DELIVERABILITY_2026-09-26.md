# Newsletter deliverability — evidence reconciliation, 26 September 2026

## Scope and provenance

Baseline: `full-scrape-prod`, `8ed19846ccf9242b646ea38440d71e1f85f59141`.
This documentation-only reconciliation uses inspected code/Git, the prior
read-only production Mongo audits (September 26, approximately 18:17–18:25 UTC),
the authoritative local suppression export `suppressions-1790268487765.csv`,
and the owner's supplied deployment, mailbox-source, Postmaster and support
observations. No production operation or test send was repeated for documentation.
Raw mailbox identities, message sources, credentials, tracking IDs and event
network metadata are deliberately not preserved here.

Earlier snapshots are dated observations, not current live guarantees. Complete
historical reconstruction remains incomplete. See [Source Register](SOURCE_REGISTER.md).

## Provider suppression hygiene — completed, not deliverability recovery

- `34ecf74` separates provider delivery suppression from subscription consent;
  `active` is not repurposed. Delivery eligibility excludes provider-suppressed
  subscribers. Fields: `provider_suppressed`, `provider_suppression_reason`,
  `provider_suppressed_at`, `provider_suppression_source`.
- `5afd7b1` records reconciliation and adds
  `scripts/provider_suppression_reconciliation.py`.
- Authoritative population: 815 unique addresses, 785 bounce and 30 complaint.
  Of these, 583 were locally active before reconciliation.
- First transaction aborted and rolled back because source sub-millisecond
  timestamps did not equal BSON millisecond timestamps. Corrected reconciliation:
  matched 815, modified 815, exact post-write 815, committed 1; provider API calls
  0, unsuppressions 0. Independent verification found zero requiring change.
- At that observation: total 14,267; active 11,673; suppressed 815;
  active-and-suppressed 583; inactive-and-suppressed 232; bounce 785; complaint 30.
  Later September 26 audits found 14,268 total; do not overwrite the older snapshot.

Consent, ordinary preferences and provider-side suppression were not changed by
the reconciliation. This does not establish Inbox recovery.

## Controlled placement and authentication — owner-supplied evidence

- The owner's existing Gmail and tested Googlemail alias reach Spam; those are
  the same mailbox, not independent seeds. A separate fresh Gmail seed received
  the signup welcome in Spam. Current Resend Daily Brief tests also reached Spam.
- iCloud Variant A (production tracking/external hero) reached Junk. Variant B
  (direct article links, no open pixel, third-party hero removed) reached Inbox.
  Multiple variables changed, so this does not isolate one cause.
- Gmail Variant B still reached Spam; plain-text Variant C also reached Spam.
  Yahoo and a controlled custom-domain recipient reached Inbox in tested variants.
- SPF, Cheshire Today DKIM, SES DKIM where applicable, and DMARC pass.
- Reported Postmaster compliance: SPF/DKIM, From alignment, DMARC, encryption,
  user-reported spam rate, DNS, one-click unsubscribe and honour unsubscribe all
  Compliant. Feedback Loop previously displayed no data.
- Deliverability Analysis states: “Users signal that they don't want to get your
  email messages”, describing reporting Inbox mail as spam and/or not marking
  Spam-folder mail as not spam.

Negative recipient sentiment/reputation is the strongest current provider-side
diagnosis despite technical compliance. These controlled observations do not
establish that all Gmail recipients get Spam or identify a single causal event.

## Feedback-ID — deployed application support; desired FBL outcome not achieved

`8ed1984` emits recipient-neutral campaign values:
`daily:::cheshtoday`, `weekly:::cheshtoday`, `breaking:::cheshtoday`,
`siteupdate:::cheshtoday`, `manual:::cheshtoday`.
Transport-level headers remain separate from strict native-unsubscribe artifacts.
Welcome, management transactional/recovery/reactivation, unrelated SMTP and
preview paths remain excluded. No audience, scheduling, tracking or provider
configuration change was included.

Owner-supplied evidence: Render service `cheshiretoday-migration-` reported Live
at exact SHA `8ed19846ccf9242b646ea38440d71e1f85f59141`; public health HTTP 200.
The owner independently verified the remote HEAD. This task checks local Git,
not a fresh remote or production observation.

Both Resend `/emails/batch` and single `/emails` delivered Gmail sources with
SES-generated Feedback-ID ending `:AmazonSES`, replacing the submitted custom
value. The single-endpoint test returned HTTP 200. Cheshire Today DKIM did not
sign Feedback-ID; SES DKIM did. Authentication still passed. No adverse app-side
effect is reported, but Gmail FBL instrumentation is not operational as intended.
The exact internal Resend-versus-SES replacement boundary is unproven.
Resend support was asked about custom preservation or a supported Gmail FBL
mechanism; response pending. Do not infer a supported workaround or universal
provider impossibility from these tests alone.

## Historical reconstruction: January–June

| Period | Evidence |
|---|---|
| January | Owner has Gmail Inbox evidence; Git starts February 1, so January transport/population cannot be reconstructed reliably. |
| April 6–7 | Approximately 14,342 imported subscribers; Daily enabled by default. Early-April documentation identifies Office 365 SMTP. |
| April 11 | `f76248a` Resend Daily/Weekly migration; sending domain `updates.cheshiretoday.co.uk`; `11d56f2` recipient-level tracking. |
| April 15/22 | Default Daily cap 250→2,000 (`c54c3c1`); fetch limit 1,000→15,000 (`805bda4`). |
| May 2–3 | `540f73d` rotation and expanded Weekly eligibility deployed, according to contemporaneous notes; Weekly eligible population approximately 2→14,316, cap 2,000. |
| May 4–12 | Seven days contain 656 of 689 May bounce suppressions (95.21%); 634/689 occur in the scheduled 06:30 UTC minute (92.02%). |
| May 27–28 | Default cap reduced to 1,000; organic/engaged audience prioritisation introduced. |
| June | 22 bounce and eight complaint suppressions; lower recorded sending volume. |

May total: 689 bounces + 12 complaints. All 701 suppressed addresses match
current records dated April 6. Gmail contributes 140 bounces and zero complaints;
the burst is predominantly non-Gmail. This is a date-linked population, not
explicit import metadata or proof of consent history.

| Month | Daily targeted / reported success | Weekly targeted / reported success |
|---|---:|---:|
| April | 22,015 / 19,014 | 6 / 4 |
| May | 47,000 / 38,900 | 9,000 / 4,000 |
| June | 26,000 / 24,900 | 4,000 / 4,000 |

May combined application-reported success was 42,900 versus April 19,018
(approximately 2.26×). These are not deliveries, unique recipients or Inbox
counts. No recipient ledger exists before July 14. The temporal association
between import/rotation/capacity and suppression does not prove May caused later
Gmail reputation deterioration.

## Current eligible Gmail cohort — September 26 snapshot

Eligibility: explicit active, Daily enabled/not opted out, valid address,
provider suppression excluded; normalized domain exactly gmail.com/googlemail.com.
7,797 eligible: 7,794 April-6-dated with unknown explicit origin, three newer
September website-origin signups. No July/August additions in this Gmail cohort.

| Window | Recorded engaged | Recorded clickers | April-dated engaged |
|---|---:|---:|---:|
| 30 days | 954 | 0 | 951 |
| 60 days | 2,317 | 1 | 2,314 |
| 90 days | 4,586 | 1 | 4,583 |

Historical-only engagement: 377; no engagement ever: 2,834. Equivalent non-Gmail
clickers: 159/225/349. The three newer website signups all have recent opens but
no recent clicks; this sample cannot establish a general newer-subscriber effect.
No non-empty recent-click recovery cohort was established. Opens do not certify
human interest; GET scanner activity also limits interpretation of non-Gmail clicks.

## Historical event quality — all current-address-matched subscribers

This table includes inactive/suppressed subscribers and groups by event month,
unlike the eligible rolling-window cohort above. September ends on the 26th.

| Month | Gmail openers / events | Gmail clickers / events | Non-Gmail openers / events | Non-Gmail clickers / events |
|---|---:|---:|---:|---:|
| April | 439 / 700 | 0 / 0 | 3 / 54 | 3 / 25 |
| May | 1,884 / 2,693 | 6 / 7 | 1,296 / 3,566 | 374 / 6,580 |
| June | 2,461 / 3,538 | 11 / 14 | 1,367 / 6,438 | 364 / 6,258 |
| July | 3,767 / 5,209 | 9 / 11 | 1,316 / 5,381 | 356 / 3,861 |
| August | 1,840 / 2,999 | 1 / 1 | 1,098 / 5,565 | 88 / 1,269 |
| September | 746 / 885 | 0 / 0 | 1,094 / 4,293 | 158 / 1,086 |

Earliest retained events are March 7; recipient-attributable events start April 12.
169 unmatched analytics rows (626 opens/3,389 clicks) are excluded, not treated
as zero. Attributable counters equal retained event-array totals. Gmail has only
33 historical clicks: activity thins after July 13, then one on July 29 and one
on August 23, with none later. There is no strong historical Gmail click baseline.

Tracking history: May 22 `6738d47` adds non-counting HEAD handling; July 14
`bbea335` adds the accepted ledger; July 20 secure legacy cutover; July 22
HTML/design changes; July 30 `e49f4b4` validates redirect destinations. No
Gmail-specific filter or change to the eight-character SHA-256 suffix is identified.
Temporal proximity alone does not establish a tracking regression.

Open metadata includes timestamp, user agent and request-client IP, not a verified
MPP/proxy/bot classification. Of 16,024 Gmail opens, 36 explicitly advertise Google
image proxying; 15,416 have Chrome-family strings and 567 bare Mozilla/5.0 strings.
These strings do not prove human activity or allow a defensible MPP count.
HEAD clicks are excluded; valid GET clicks are not human/scanner filtered.

The ledger timestamp is written after a batch, not at individual handoff.
4,162 linked Gmail opens precede it; 3,305 occur within one minute afterward.
This concentration is consistent with rapid fetching but is not exact send
latency or proof of automation. Accepted-send rates before July cannot be derived.

## Cold-count reconciliation

The existing rule uses at least five qualifying accepted Daily/Weekly
opportunities within 90 days, no retained historical engagement, and existing
age/organic/priority protections. Reconstructing with current eligibility:
September 25 18:17 UTC gives 739; September 26 06:29:59 still gives 739;
September 26 18:17 gives 1,001. All 262 additions had four opportunities and
crossed to five in the September 26 send; no removals. No ledger entries aged
out because the ledger starts July 14. No methodology inconsistency is identified.
This fully reproduces the numerical change, not an immutable historical
eligibility snapshot. The 30-day send-window variant yields zero and must not be
confused with the documented 90-day investigation.

## Open boundaries

Gmail placement investigation remains active/monitoring; technical compliance
passes in supplied observations, not a guarantee of placement. Support response
on FBL is pending. No Gmail-specific deactivation, cohort selection, volume change
or speculative remediation is approved. CT-DEC-021 functional acceptance remains
complete, but **POTENTIAL QUERY LOG EXPOSURE** remains open.

Missing historical provider rejection detail, January transport proof, pre-July
recipient ledgers, immutable eligibility snapshots, per-recipient handoff times,
rejected tracking-request logs and reliable human/bot classification prevent
stronger causal conclusions. Commercial/affiliate work is a separate future task.
