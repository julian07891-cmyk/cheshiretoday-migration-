# Cheshire Today — Current Operational State

> - **Status:** Concise operational source of truth; Version 1 is complete and the current stage is production hardening, QA and evidence-led reliability monitoring
> - **Operational authority:** This file, governed by [Project Master](PROJECT_MASTER.md)
> - **Primary branch:** `full-scrape-prod`
> - **Repository baseline:** `d8943e8c7284781b8fefb915e00b4e53f831c3bb`
> - **Last repository reconciliation:** 13 August 2026
> - **Production-verification status:** Commit `d8943e8` is live and CT-QA-2026-003 is closed after natural-run verification of the fail-closed article lock; cumulative process-memory risk remains under monitoring
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
- **Current reconciled HEAD:** `d8943e8c7284781b8fefb915e00b4e53f831c3bb`
- **Latest baseline commit:** `Fail closed on article scheduler lock errors`

This is the repository and production baseline reconciled on 13 August 2026, not
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
delete, publish, reroute or alter an article. No threshold or UI decision is
approved at this baseline.

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

Perplexity may provide bounded research/rewrite assistance in eligible import
paths. Provider output still passes deterministic and editorial controls.

OpenAI remains Admin-only and draft/review-only. It must never auto-publish.
Manual Review is a first-class hidden editorial state. No automatic AI
publication is permitted.

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

Inactive-subscriber deactivation requires reconciled provider, acceptance and
engagement evidence. Missing opens alone are insufficient. Do not expose raw
subscriber addresses, tokens or hashes.

Code capability does not prove the current live provider, audience, delivery or
inbox result. Verify production state and use normal scheduled evidence rather
than an unapproved test send.

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

## 9. Current monetisation model

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

Dynamic affiliate inventory and sponsor-impression bot filtering remain open or
deferred roadmap work, not completed operating capabilities.

See [Monetisation Architecture](ARCHITECTURE/MONETISATION.md) and
[Commercial Gap Map](commercial-gap-map/).

## 10. Current QA posture

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

- **Medium:** duplicate-cleanup memory is structurally and materially improved by
  `49e5fe4`, `c06c837` and `cd3f093`, with 13 phase markers now isolating cleanup
  intervals. The `1811430` string-allocation change was semantically safe but its
  first natural comparison was similar (+28.5 MB versus +26.0 MB). Broader
  cumulative Render memory/OOM stability remains under monitoring. The 13 August
  18:00 observation was worse than recent runs (130.7→305.5 MB current RSS,
  +174.8 MB net), but one noisier run does not establish a worsening trend or a
  new optimisation target.
- **Medium:** Editorial Similarity’s numerical three-run observation-count gate is
  satisfied. Calibration, threshold, UI and enforcement decisions remain
  unapproved; the scorer remains scheduled-only and shadow-only.
- **Medium:** `CT-QA-2026-004` records a cross-source same-event duplicate-identity
  limitation. A 10–14 August read-only ledger found zero confirmed or probable
  archived-to-reimport cases through the normal scheduled hybrid importer, whose
  exact active/archive identity protection is functioning. Four strong
  cross-source or cross-format same-event clusters remain evidence that changed
  URLs, titles and images can bypass deterministic identity checks. No
  implementation is approved; the next step is design review only, preserving
  legitimate updates and Editorial Similarity's advisory, non-blocking policy.
- **Medium:** public desktop search accessibility remains open.
- **Medium:** Admin first-byte server-level noindex/robots alignment is not fully
  proven.
- **Active:** documentation reconstruction and pending-source reconciliation.

Rendered public metadata duplication is recorded as remediated, deployed and
production-verified. Legacy Python compilation and the original external-test
mutation boundary are remediated at repository level. These closures do not
close adjacent production or maintenance risks.

See [Completed Phases](QA/COMPLETED_PHASES.md) and
[Test History](QA/TEST_HISTORY.md).

## 11. Current active milestone

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

- reconcile this 13 August authority update through final review and an approved
  documentation commit;
- receive and reconcile the ChatGPT export;
- preserve and reconcile structured Codex history;
- reconcile historical PDFs;
- continue reconciling later production evidence as it is verified.

### Track 2 — Production observation

- observe normal scheduler runs only;
- capture all thirteen article-generation memory markers;
- continue post-run stability monitoring after the duplicate-cleanup lifecycle,
  projected-scan and observability improvements; first duplicate Stage 1,
  visible-pool work, short-content scan variability and high-start process memory
  remain material evidence areas;
- retain bounded Editorial Similarity score, band, reason and provenance evidence;
- confirm Version 1 decisions, Manual Review and publication remain unchanged;
- make no calibration, threshold, UI or enforcement decision without a separate
  reviewed evidence gate and approval.

No manual import should be triggered solely to accelerate observation.

## 12. Immediate approved priorities

1. Observe at least one further natural article-generation run before selecting
   another memory implementation target.
2. Continue broader Render memory monitoring; do not infer that `1811430` reduced
   RSS from its first similar natural-run comparison.
3. Complete Weekly Roundup QA using normal scheduled evidence.
4. Continue inactive-subscriber evidence gathering without speculative
   deactivation.
5. Complete ChatGPT and Codex historical reconciliation.

Security and reliability take precedence over speculative features.

## 13. Near-term priorities

- repair and verify public search accessibility;
- provide and verify Admin first-byte noindex/robots alignment;
- measure current article-list performance before optimisation;
- preserve and improve hermetic test isolation;
- reduce compilation/build/test warning debt in bounded changes;
- validate GA4 configuration and reporting separately from first-party analytics;
- perform representative Search Console, Google News and Discover review;
- continue quality-first commercial SEO and affiliate guide development;
- design evidence-backed dynamic affiliate inventory;
- complete sponsor workflow readiness and reporting checks.

Each item requires its own reviewed scope, tests and deployment/production
verification plan.

## 14. Deferred work

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

## 15. Current operating rules

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

## 16. Session-start checklist

1. Read [Project Master](PROJECT_MASTER.md) and this file.
2. Read relevant architecture, operations, QA and roadmap records.
3. Verify branch, HEAD, latest commit and working-tree status.
4. Check current production state where facts may have changed.
5. Identify and protect affected production systems.
6. Confirm the exact task, mutation boundary and approval scope.
7. Make one safe action and verify it before continuing.

## 17. Session-end checklist

1. Run tests, compilation, build or checks appropriate to the task.
2. Review the exact diff and repository status.
3. Record commit, deployment and live verification as separate evidence.
4. Update the correct current, architecture, QA, history or roadmap document.
5. Record unresolved findings and closure criteria.
6. Preserve historical evidence and source limitations.
7. Confirm no production change remains undocumented.

## 18. Documentation links

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

## 19. Reconstruction and verification status

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
