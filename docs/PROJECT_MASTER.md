# Cheshire Today — Project Master

> - **Status:** Permanent first-read project index; Phases 1–7.3 complete locally and awaiting final read-only review, commit and push
> - **Primary branch:** `full-scrape-prod`
> - **Operational authority:** [Project State](PROJECT_STATE.md), rebuilt locally as the concise operational source; repository-wide transition awaits the approved documentation commit and push
> - **Architecture authority:** [Architecture Master](ARCHITECTURE_MASTER.md) and its detailed records
> - **QA authority:** [QA Master](QA/QA_MASTER.md) and [Open Findings](QA/OPEN_FINDINGS.md)
> - **Roadmap authority:** [Roadmap Master](ROADMAP_MASTER.md)
> - **Historical reconstruction status:** Substantial repository reconstruction completed; ChatGPT, Codex, PDF and post-HEAD reconciliation remain incomplete
> - **Last repository reconciliation date:** 6 August 2026
> **Current repository baseline:** `full-scrape-prod` at `1601ae48be281153e5dd4af0eee0889a26835162`

This metadata describes the repository baseline used for reconstruction. It does
not assert that the same commit is currently deployed or that every production
dependency is healthy. Verify mutable production facts at session start whenever
they matter.

## 1. Document purpose

This is the primary entry point for every future Cheshire Today ChatGPT and Codex
session.

It is a concise project operating manual and navigation layer. It explains:

- what Cheshire Today is;
- which records control current state, architecture, QA, history and roadmap;
- the load-bearing engineering and editorial boundaries;
- how to begin and end work safely;
- where detailed evidence belongs.

It is not:

- a chronological engineering log;
- a replacement for current operational state;
- a complete architecture specification;
- a production dashboard;
- a substitute for the live finding register;
- proof of deployment or production verification.

Detailed evidence remains in the linked records. Do not copy long histories or
temporary checkpoints back into this file.

## 2. Document governance

### First-read rule

Read this document first in every new engineering, editorial, operational, SEO,
newsletter, social or commercial session.

Then read [Project State](PROJECT_STATE.md), the concise local operational source
of truth. The authority transition is locally complete and becomes repository-wide
after the approved documentation commit and push. Read only the architecture, QA,
operations, history and roadmap records relevant to the task.

### Document roles

| Record | Role | Update responsibility |
|---|---|---|
| `PROJECT_MASTER.md` | Permanent first-read index, governance, mission and system-wide boundaries | Update only for project-wide governance, architecture index, strategy or major milestone changes |
| [Project State](PROJECT_STATE.md) | Concise local operational authority; repository-wide transition awaits the approved documentation commit and push | Update after meaningful current operational change; do not turn it into a second history master |
| [Roadmap Master](ROADMAP_MASTER.md) | Priorities, statuses, dependencies and gates | Update when evidence changes priority or an item changes approved status |
| [Architecture Master](ARCHITECTURE_MASTER.md) | Current architecture index | Update when current component or data-flow ownership changes |
| [Detailed architecture](ARCHITECTURE/SYSTEM_OVERVIEW.md) | Subsystem contracts and protected boundaries | Update the affected subsystem after reviewed architecture change |
| [QA Master](QA/QA_MASTER.md) | Current evidence-backed QA summary | Update when QA posture or classification totals change |
| [Open Findings](QA/OPEN_FINDINGS.md) | Durable live finding register and closure criteria | Update only when code, test, deployment or production evidence changes |
| [Completed Phases](QA/COMPLETED_PHASES.md) | Completed QA and hardening programmes | Add a phase when its defined implementation boundary is complete; keep residual risks explicit |
| [Test History](QA/TEST_HISTORY.md) | Test, build and production-verification baselines | Record meaningful dated baselines without inventing counts |
| [Engineering History Master](HISTORY/ENGINEERING_HISTORY_MASTER.md) | Chronological engineering reconstruction | Append/reconcile historical evidence; never rewrite past claims as present truth |
| [Decision Register](DECISION_REGISTER.md) | Durable load-bearing decisions and rationale | Add or supersede decisions with evidence; preserve previous status |
| [Production Timeline](PRODUCTION_TIMELINE.md) | Deployments, incidents, operations and verification gates | Record production evidence separately from local implementation |
| [Editorial Evolution](EDITORIAL_EVOLUTION.md) | Editorial-policy and workflow history | Record policy shifts and repository-HEAD principles |
| [Source Register](HISTORY/SOURCE_REGISTER.md) | Evidence inventory and authority levels | Register new sources, hashes, limitations and reconciliation status |

### ChatGPT and Codex records

The pending ChatGPT export is a source awaiting reconciliation, not an authority
by itself. The existing [August ChatGPT history location](HISTORY/CHAT_HISTORY_AUGUST_2026.md)
is currently an incomplete placeholder.

Codex investigations have not yet been systematically preserved into a dedicated
history record. Their status is registered in the [Source Register](HISTORY/SOURCE_REGISTER.md).
Future ChatGPT or Codex material becomes authoritative only after it is reconciled
against repository code, Git and verified production evidence, then recorded in
the appropriate permanent repository document.

### Update rules

- Current operational state belongs in Project State.
- Implementation chronology belongs in Engineering History.
- Production deployments and incidents belong in Production Timeline.
- QA findings and closure evidence belong in the QA registers.
- Architecture belongs in Architecture Master and the relevant detail document.
- Decisions belong in Decision Register.
- Priorities and gates belong in Roadmap Master.
- Editorial-policy evolution belongs in Editorial Evolution.
- Evidence provenance belongs in Source Register.

Update this master only when a future session would otherwise misunderstand the
project-wide operating model, system boundaries, strategic positioning or
documentation map.

Historical evidence must never be silently rewritten, deleted or converted into
a present-tense claim. Preserve disagreements and mark uncertainty.

## 3. Project identity and mission

Cheshire Today is a professional digital publication serving Cheshire readers
with useful local reporting and selected high-value wider coverage.

Its mission is to become a trusted Cheshire local authority by combining:

- timely local news;
- business, economy, finance and property coverage;
- practical technology and AI reporting;
- clear source attribution;
- strong editorial safeguards;
- a fast, clean and readable product;
- sustainable audience and commercial growth.

The publication should feel credible, calm and useful rather than sensational or
content-farm-like. Readers should be able to understand what happened, where it
happened and why it matters without intrusive presentation or promotional prose.

Long-term sustainability depends on:

- direct reader trust;
- repeat readership;
- newsletter ownership;
- search and Discover visibility;
- responsible social distribution;
- affiliate authority;
- sponsor readiness;
- disciplined operating costs.

Commercial systems must support the editorial product rather than distort it.

## 4. Strategic positioning

### Editorial mix

The repository-supported target mix is:

- **40% Local Cheshire** — councils, planning, communities, transport, schools,
  local institutions and developments with clear Cheshire relevance;
- **40% Business / Economy / Finance / Property** — useful economic and consumer
  authority, including strong regional or national stories relevant to readers;
- **20% AI / Technology** — practical, credible developments without repetitive
  hype or generic product filler.

This is an editorial positioning model, not permission to force weak items into a
quota. Quality and relevance remain gates.

### Primary growth goals

- Grow qualified Facebook traffic through deterministic manual publishing.
- Grow owned newsletter reach and engagement.
- Improve technical SEO, Google News and Google Discover eligibility.
- Build commercially useful authority and comparison guides.
- Prepare credible sponsor inventory and advertiser operations.
- Strengthen Cheshire Today as a trusted local authority.

### Explicit exclusions

Avoid:

- crime-heavy or court-heavy filler;
- weak national stories with no useful Cheshire or strategic relevance;
- clickbait headlines;
- repetitive AI-sounding copy;
- invented facts, quotes, locations or consequences;
- generic introductions and endings;
- intrusive advertising that damages reading;
- automatic publication from unreviewed OpenAI output;
- similarity scores that silently block, merge, archive or publish;
- production jobs triggered solely to create QA evidence.

## 5. Repository and production environment

### Repository baseline

- Repository: `CT29january26-new-website-migration`
- Primary production branch: `full-scrape-prod`
- Reconciliation HEAD: `1601ae48be281153e5dd4af0eee0889a26835162`

Always verify the actual branch, HEAD and working tree. Preserve intentional
untracked documentation and unrelated user changes.

### Hosting architecture

The committed architecture is:

```text
Public browser or crawler
  -> Cloudflare-facing public hostname
  -> Render web service
  -> Uvicorn
  -> FastAPI
       -> /api routes and MongoDB
       -> crawler HTML, sitemaps and robots
       -> built React SPA
```

Cloudflare and live Render settings are external to the repository. Committed
configuration does not prove current plan tier, deployed commit, environment
values or service health.

### Build and start

Committed Render configuration uses:

```text
Build: ./render_build.sh
Start: cd backend; uvicorn server:app --host 0.0.0.0 --port $PORT
```

The build installs backend requirements, runs a clean frontend dependency install
and production build, then copies the React output into `backend/frontend_build`
for FastAPI SPA hosting.

### Database and scheduler

MongoDB stores content, archive, subscriber, analytics, security, scheduler,
commercial and social-operational records evidenced in current code.

APScheduler is configured inside the eligible web process. Startup requires the
explicit automation flag and a valid runtime hostname. Mongo locks protect
article and digest ownership. The separate committed Render warmup cron calls a
health endpoint and does not own article or newsletter schedules.

### Protected production systems

Treat these as protected:

- MongoDB collections and indexes;
- articles, Manual Review and Archive state;
- subscriber records, preferences, tokens and delivery ledgers;
- scheduler jobs, locks and cursors;
- provider credentials and environment configuration;
- newsletter sends;
- social publishing and external platform accounts;
- Stripe and advertiser state;
- sitemaps, robots and Search Console;
- Render services and deployment configuration.

See [Deployment](OPERATIONS/DEPLOYMENT.md), [Render Operations](OPERATIONS/RENDER.md)
and [Scheduler Operations](OPERATIONS/SCHEDULER.md).

## 6. Current architecture summary

### Frontend

React 18 and CRACO produce one SPA with public and authenticated Admin surfaces.
React Router owns browser routes. Production Helmet owners reconcile managed
metadata after hydration. Admin-specific mobile styling is scoped away from
public forms.

### Backend

FastAPI in `backend/server.py` exposes the `/api` router, selected root crawler
and discovery routes, authentication boundaries and the built SPA. Domain helpers
under `backend/app/` handle email, analytics, observability, security, social
assets and Editorial Similarity.

### Database

MongoDB is the durable application store. Current collections are enumerated in
[System Overview](ARCHITECTURE/SYSTEM_OVERVIEW.md). Do not infer live collection
contents from code.

### Article pipeline

```text
RSS / source discovery
  -> Version 1 duplicate and quality controls
  -> bounded Perplexity research/rewrite where eligible
  -> public insertion or hidden Manual Review
  -> visible-pool and cleanup controls
  -> homepage / category / location / article routes
  -> newsletter / social preparation
  -> readers
  -> first-party analytics
```

Scheduled imports run through explicit locks and public import caps. Existing
title, source-URL, image and database-uniqueness controls remain authoritative.

### Manual Review

Manual Review is a first-class hidden editorial state. Backend safeguards decide
whether an edited record can return live. The frontend explains publication
intent but does not decide eligibility. Archive and Manual Review are not public
article states.

### Editorial Similarity

Phase 2A is a pure, deterministic, bounded scorer. Phase 2B invokes it only from
normal scheduled hybrid imports in shadow mode. It logs bounded advisory evidence
and has no effect on insertion, publication, Manual Review, archive, merge,
deletion or cleanup. Version 1 remains authoritative.

### Newsletter

Daily Brief and Weekly Roundup use eligible active subscribers, rotating batches,
provider diagnostics, per-recipient tracking and accepted-recipient ledgers.
Secure request-link flows protect preference, unsubscribe and reactivation state.

### Analytics

First-party article-view events drive Most Read and privacy-safe Admin reporting.
Facebook attribution uses deterministic UTM input normalised by the backend.
Email and commercial analytics remain separate. GA4 is third-party and
environment-dependent.

### SEO and crawlers

Mongo-ID-plus-slug URLs define article identity. Recognised crawlers can receive
server-rendered metadata and `NewsArticle` structured data. Browser metadata,
sitemaps, news sitemap, robots, hubs and authority guides have distinct contracts.

### Social publishing

Admin Social Publishing prepares deterministic Facebook, Instagram and Threads
materials. It is not authority to publish automatically. Legacy direct publishing
controls were removed from the visible Admin workflow.

### Affiliates and advertising

Authority pages and active affiliate products support guide surfaces. Sponsored
placements use bounded weighted rotation, impression/click counters and manual
Admin review. Advertiser leads and Stripe-supported checkout do not auto-publish
an advert.

### Security boundaries

Admin APIs require `get_admin_auth`. Newsletter ownership uses purpose-bound
tokens, stored challenges, rate limits and replay controls. External mutation
tests refuse non-loopback targets. Wildcard credentialed CORS remains a high
priority open finding.

Detailed architecture begins at [Architecture Master](ARCHITECTURE_MASTER.md).

## 7. Engineering principles

### Working method

- Read this file and Project State before changing anything.
- Inspect the real code, configuration, tests and current state first.
- Make the smallest safe change that solves the evidenced problem.
- Make one safe action at a time.
- Run the smallest relevant verification after each change.
- Inspect the complete diff before proposing a commit.
- Prefer safe scripted edits over ad hoc manual editing.
- Use `/usr/bin/grep`, not `rg`, in this repository.
- Do not run `npm start` unless explicitly requested.

### Production safety

- Evidence precedes optimisation.
- A fixing commit is not deployment evidence.
- Deployment is not production verification.
- Do not deploy, push or mutate production without approval.
- Do not trigger an import, newsletter, cleanup or scheduler job solely for QA.
- Do not publish an article or social post merely to test a workflow.
- Never expose credentials, tokens, subscriber data, IP hashes or hidden content.
- Preserve Manual Review, Version 1 duplicate rules and newsletter security.
- Capture incident evidence before restart, redeploy or configuration change.

### Verification

Use the risk-proportionate sequence:

1. focused behavioural tests;
2. related regressions;
3. complete applicable suite;
4. compilation and/or production build;
5. `git diff --check` and status;
6. deployment identity;
7. bounded production verification.

### Documentation responsibility

After meaningful work, update the record that owns the evidence. Do not duplicate
the same narrative in every master. Production evidence, QA closure, roadmap
status and architecture change are separate updates.

## 8. Editorial standards

### Writing quality

Articles should be:

- factual and neutral;
- locally grounded where presented as local;
- readable and well structured;
- SEO-friendly without keyword stuffing;
- written in professional British English;
- explicit about sources and uncertainty;
- free of promotional language unless clearly labelled commercial content.

Quality references are the clarity and restraint associated with the BBC and
Financial Times, combined with the practical local specificity of publications
such as the Chester Standard and Knutsford Guardian. These are quality references,
not instructions to imitate wording.

### Content safeguards

- Do not invent facts, quotations, organisations, locations or dates.
- Do not use generic “in conclusion” endings.
- Avoid repeated names, openings, transitions and AI-shaped filler.
- Require real local relevance for Local News.
- Suppress weak crime, court, emergency and national filler.
- Preserve minimum-content, image, source and locality gates.

### Provider roles

Perplexity can perform bounded research and rewriting in the import pipeline when
configured and eligible. Provider output still passes deterministic editorial and
quality safeguards.

OpenAI remains Admin-only and draft/review-only. It must never auto-publish.

### Manual Review and duplicates

Manual Review protects uncertain, sensitive, thin, stale or safeguard-failing
records from public visibility. Editors can revise records; backend checks remain
authoritative on restoration.

Version 1 exact duplicate prevention owns title, source-URL, image, batch and
database-uniqueness decisions. Editorial Similarity observes possible same-story
coverage only and awaits the approved production evidence gate.

See [Editorial Evolution](EDITORIAL_EVOLUTION.md) and
[Article Pipeline](ARCHITECTURE/ARTICLE_PIPELINE.md).

## 9. Newsletter system

### Daily Brief

The Daily Brief is scheduled Monday to Saturday at 07:30 Europe/London when the
scheduler is active. It selects eligible public stories and active subscribers
with the correct preference, subject to configured caps and rotating cursor.

### Weekly Roundup

The Weekly Roundup uses four Sunday batches at 09:00, 10:00, 11:00 and 12:00.
Batch one prioritises organic website subscribers before engaged readers; later
batches continue without wrapping through the same audience.

### Delivery and evidence

Current code supports Resend batch delivery and an explicitly configured SMTP
path. The active production provider must be verified. Provider acceptance is not
proof of inbox delivery.

Each recipient receives a derived tracking identity. Open and click events feed
first-party email analytics. The accepted-recipient ledger stores privacy-
preserving hashes and aggregate acceptance evidence, not a public recipient list.

### Secure ownership

Preference, unsubscribe and reactivation request links use generic public
responses, purpose-specific signed tokens, stored challenges, rate limiting,
expiry and replay protection. `active=False` subscribers are excluded from sends.

### Operational safeguards

- Do not expose subscriber addresses, tokens or hashes.
- Do not infer inactivity from missing opens alone.
- Require reconciled provider and ledger evidence before deactivation.
- Preserve protected-address and invalid/test-address filtering.
- Do not run test sends without explicit production approval.

See [Newsletter Architecture](ARCHITECTURE/NEWSLETTER.md) and
[Newsletter Operations](OPERATIONS/NEWSLETTER_OPERATIONS.md).

## 10. Social-media workflow

### Publishing model

Facebook, Instagram and Threads publishing remains editorial and manual. The
Admin prepares assets and copy; it does not grant authority to post automatically.

The operating rhythm documented by the project is a morning, evening and Sunday
social workflow. Treat times and platform availability as editorial operations
that require current confirmation rather than hard-coded scheduler jobs.

### Approval sequence

1. Recommend a suitable approved public article first.
2. Wait for editorial approval.
3. Prepare the Facebook post.
4. Prepare the pinned comment.
5. Prepare the Instagram caption where relevant.
6. Prepare the Threads post.
7. Add restrained hashtags and an engagement prompt appropriate to the platform.
8. Preview the final link/asset in the real platform.
9. Publish only after explicit approval.

Do not present a URL, image, source record or Manual Review article as approved
social content.

### Unified Admin and brand assets

The unified Social Publishing Admin contains deterministic Facebook link/copy and
graphic preparation plus approved Instagram and Threads workflows. Brand assets
and platform guidance live in [Brand Assets](brand-assets/).

### Analytics boundaries

Facebook article attribution is first-party and UTM-based. It is distinct from
Meta reactions, comments, shares and provider dashboards. No Meta API response is
required for the first-party Facebook article-view metric.

Historical development is in [Engineering History](HISTORY/ENGINEERING_HISTORY_MASTER.md);
current analytics are in [Analytics Architecture](ARCHITECTURE/ANALYTICS.md).

## 11. SEO and audience growth

### Technical foundations

- Canonical articles use stable Mongo ID and current slug.
- Slugless or stale-slug routes redirect where resolution succeeds.
- Attribution queries and fragments do not enter canonical or Open Graph URL.
- Recognised crawlers receive server-specific article and guide HTML.
- Article crawler HTML includes `NewsArticle` structured data.
- Browser routes reconcile one active managed metadata set after hydration.
- Hidden Manual Review and archived non-force-live content are not indexable public
  articles.

### Discovery surfaces

The main sitemap, news sitemap and robots file are generated by current backend
routes. Category and town/location hubs provide thematic entry points. Published,
substantive authority pages can enter the sitemap; thin guides remain excluded or
noindex according to current code.

### Growth work

Audience growth depends on:

- strong local and topic hubs;
- useful internal links;
- authority guides;
- clean canonical identity;
- appropriate Google News freshness;
- original, useful reporting suited to Discover;
- newsletter ownership;
- responsible social referral.

Search Console and GA4 are external platforms. Their current state must be
verified directly. HTTP correctness alone does not prove indexing, Discover
distribution or analytics collection.

Known gaps include Admin first-byte noindex, public search accessibility,
representative Search Console sampling, GA4 validation and potential server-side
homepage crawl improvements.

See [SEO and Crawlers](ARCHITECTURE/SEO_AND_CRAWLERS.md) and
[Open Findings](QA/OPEN_FINDINGS.md).

## 12. Monetisation strategy

### Affiliate-first model

The primary sustainable commercial direction is affiliate-first authority rather
than intrusive display advertising. Useful guides and comparisons should answer
real reader questions and maintain editorial credibility.

Authority pages, active affiliate products and article-to-guide recommendations
support this model. Commercial SEO should improve reader utility first; provider
links must be relevant and clearly handled.

### Sponsored placements

Current code supports active placement slots, bounded weighted rotation,
impression/click tracking, advertiser leads and Admin management. House adverts
can use the same placement architecture where configured.

Stripe-supported advertising checkout creates payment and lead state but does
not automatically publish an advert. Paid placements remain subject to manual
review and an advert-live workflow.

### Reader experience

- Keep adverts clearly labelled.
- Do not obscure editorial content.
- Do not use payment as an editorial-publication signal.
- Do not claim revenue, conversion or campaign performance without evidence.
- Preserve advertiser and payment privacy.

Dynamic affiliate inventory and sponsor impression bot filtering remain roadmap
items. See [Monetisation Architecture](ARCHITECTURE/MONETISATION.md) and
[Commercial Gap Map](commercial-gap-map/).

## 13. QA posture

The [QA Master](QA/QA_MASTER.md) reconciles the immutable 29 July baseline with
later code, tests, deployment and production evidence.

At the current repository baseline:

- tracked credential literals and unsafe external test targeting were contained;
- legacy Python compilation was repaired;
- rendered metadata duplication was deployed and production-verified;
- first-party article views and Most Read were corrected;
- bounded memory and Editorial Similarity observability exist;
- substantial newsletter, Manual Review, analytics, crawler and mobile regression
  coverage is preserved.

Highest-priority unresolved evidence includes:

- production credential rotation/revocation;
- wildcard credentialed CORS;
- Render memory/OOM stability and duplicate-cleanup peaks;
- Editorial Similarity’s three-normal-run observation gate;
- public desktop search accessibility;
- Admin first-byte noindex/robots alignment;
- documentation reconstruction and pending-source reconciliation.

Do not duplicate the register here. Use:

- [QA Master](QA/QA_MASTER.md) for posture;
- [Open Findings](QA/OPEN_FINDINGS.md) for closure criteria;
- [Completed Phases](QA/COMPLETED_PHASES.md) for programmes;
- [Test History](QA/TEST_HISTORY.md) for baselines.

## 14. Major decisions

The full evidence and alternatives are in the [Decision Register](DECISION_REGISTER.md).
The most load-bearing decisions are:

1. Repository operational documentation controls current work.
2. Work is QA-first and bounded to the smallest safe change.
3. The publishing model combines hybrid RSS discovery with bounded Perplexity
   research/rewrite.
4. OpenAI is Admin-only and never an automatic publisher.
5. Manual Review is a first-class hidden editorial state.
6. Archive is preferred to ordinary hard deletion.
7. Subscriber ownership uses secure request-link management.
8. Resend batch delivery and accepted-recipient evidence support newsletter scale.
9. Monetisation is affiliate-first, with paid placements manually reviewed.
10. Local RSS activation is staged and quality-gated.
11. Version 1 deterministic duplicate prevention remains authoritative.
12. Editorial Similarity begins deterministic, scheduled-only and shadow-only.
13. No similarity threshold or UI proceeds before multiple normal-run evidence.
14. Memory observation precedes scheduler/import optimisation.
15. Historical evidence is separated from current operational truth.

Future decisions should supersede, not erase, previous entries.

## 15. Production incidents and lessons

The detailed chronology is in [Production Timeline](PRODUCTION_TIMELINE.md).

- **Render memory and OOM:** newsletter and scheduled article work have reached
  memory limits. Twelve article-generation markers improve diagnosis but do not
  prove stability; capture complete normal runs before optimisation.
- **Newsletter delivery and memory:** provider transitions, caps, rotating cursors,
  zero-success diagnostics and accepted-recipient accounting followed incidents.
  Provider acceptance and subscriber engagement remain separate evidence.
- **Scheduler and import:** locks, hostname guards, stale takeover, RSS concurrency
  and public caps followed duplicate-owner/resource risks. Do not manually trigger
  routine runs to prove a fix.
- **Archive and live pool:** over-broad or date-driven cleanup can remove legitimate
  content. Archive-first controls, protected manual states and disabled automatic
  age deletion reduce that risk.
- **Indexing and metadata:** incidents led to canonical ID routes, crawler HTML,
  stronger discovery files and rendered metadata reconciliation. DOM verification
  does not prove indexing recovery.
- **AI verification rollback:** uncertain or over-automated experiments were
  paused, reverted or routed through Manual Review. Providers assist; deterministic
  and human safeguards own publication.

- Preserve evidence before intervention.
- Prefer reversible changes.
- Separate implementation, deployment and production verification.
- Never use production mutation as the easiest test.
- Do not optimise or repair databases without measured cause.
- Record incidents without exposing private content or secrets.

## 16. Major milestones

- **Production foundation:** Render/Uvicorn/FastAPI and the React SPA were
  stabilised through iterative deployment, health, routing and build work.
- **Editorial pipeline:** hybrid RSS, Perplexity assistance, quality controls,
  public caps, archive safety and scheduler locking form Version 1.
- **Manual Review:** a hidden editorial state gained metadata, Admin workflow,
  backend-authoritative restoration and publication-intent/mobile safeguards.
- **Newsletter and secure ownership:** Daily Brief, batched Weekly Roundup,
  Resend, tracking, ledgers and secure lifecycle management were staged; current
  provider state remains environment-dependent.
- **SEO and crawlers:** canonical routes, crawler HTML, structured data, hubs,
  discovery files and metadata ownership were implemented. Metadata reconciliation
  is production-verified; indexing remains external.
- **Affiliates and advertising:** authority pages, affiliate providers, sponsored
  placements, advertiser leads and Stripe-supported workflows exist without a
  revenue-performance claim.
- **Local RSS:** staged locality, freshness, source and Manual Review safeguards
  are implemented; quality monitoring continues.
- **Brand and social suite:** approved assets and unified Social Publishing support
  deterministic manual Facebook, Instagram and Threads preparation.
- **Version 1:** core public, editorial, duplicate, Manual Review, newsletter, SEO,
  analytics and commercial foundations are represented; open QA still applies.
- **Analytics:** first-party views, Most Read, Admin summaries and Facebook
  attribution use bounded privacy-safe reporting; GA4 remains external.
- **Editorial Similarity:** Phase 2A (`8043fdd`) and Phase 2B (`5e1a875`) are
  implemented; repository records state deployment, while observation/calibration
  remains incomplete.

See [Engineering History](HISTORY/ENGINEERING_HISTORY_MASTER.md) for chronology
and [Completed Phases](QA/COMPLETED_PHASES.md) for QA boundaries.

## 17. Current operational status

[Project State](PROJECT_STATE.md) is the concise local operational authority. The
authority transition becomes repository-wide after final consistency review and
the approved documentation commit and push. Do not copy an older July “current
checkpoint” into this master.

The current repository reconstruction baseline is:

```text
Branch: full-scrape-prod
HEAD: 1601ae48be281153e5dd4af0eee0889a26835162
```

At session start, verify:

- actual local branch and HEAD;
- working-tree state;
- current deployed Render commit when relevant;
- health and startup state;
- mutable provider, scheduler or production facts needed by the task.

Editorial Similarity is documented at HEAD as deployed into passive scheduled
observation. Later production investigations fall outside this repository
baseline until they are reconciled into approved records. Do not claim calibration,
threshold approval, Similar Stories UI or production detection quality.

## 18. Roadmap summary

The authoritative prioritisation is [Roadmap Master](ROADMAP_MASTER.md).

### Immediate

- obtain credential rotation/revocation evidence;
- restrict and verify wildcard credentialed CORS;
- observe production memory and duplicate-cleanup pressure;
- complete Editorial Similarity normal-run observation;
- complete documentation reconstruction.

### Near term

- public search accessibility;
- Admin first-byte noindex;
- Weekly Roundup QA;
- inactive-subscriber and engagement evidence;
- safe test organisation and warning cleanup;
- current public API performance measurement.

### Medium and long term

- GA4 and Search Console validation;
- commercial SEO and affiliate guide development;
- sponsor readiness;
- server-side homepage crawl improvements;
- dynamic affiliate inventory;
- sponsor impression bot filtering;
- Version 2 brand refresh only when justified.

Security and production stability remain ahead of discretionary features.

## 19. Documentation index

### Current state and preservation

- [Project State](PROJECT_STATE.md) — concise local operational authority; repository-wide transition pending approved commit and push.
- [Privacy-safe preserved state](ARCHIVE/PROJECT_STATE_REDACTED_2026-08-06.md) —
  repository historical copy derived from the exact local archive with explicit
  privacy redactions.
- [Source Register](HISTORY/SOURCE_REGISTER.md) — source inventory and authority.

### History and decisions

- [Engineering History Master](HISTORY/ENGINEERING_HISTORY_MASTER.md)
- [Decision Register](DECISION_REGISTER.md)
- [Production Timeline](PRODUCTION_TIMELINE.md)
- [Editorial Evolution](EDITORIAL_EVOLUTION.md)
- [July Engineering Log](HISTORY/ENGINEERING_LOG_JULY_2026.md)

### Architecture

- [Architecture Master](ARCHITECTURE_MASTER.md)
- [System Overview](ARCHITECTURE/SYSTEM_OVERVIEW.md)
- [Article Pipeline](ARCHITECTURE/ARTICLE_PIPELINE.md)
- [Newsletter Architecture](ARCHITECTURE/NEWSLETTER.md)
- [Editorial Similarity](ARCHITECTURE/EDITORIAL_SIMILARITY.md)
- [Analytics Architecture](ARCHITECTURE/ANALYTICS.md)
- [SEO and Crawlers](ARCHITECTURE/SEO_AND_CRAWLERS.md)
- [Monetisation Architecture](ARCHITECTURE/MONETISATION.md)

### Operations

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
- [Original 29 July QA Report](QA/QA_REPORT_2026-07-29.md)
- [Roadmap Master](ROADMAP_MASTER.md)

### Editorial, brand and commercial supporting records

- [Brand Assets](brand-assets/)
- [Commercial Gap Map](commercial-gap-map/)

### Pending sources

- [August ChatGPT history location](HISTORY/CHAT_HISTORY_AUGUST_2026.md) — empty or
  incomplete pending export/reconciliation.
- [Source Register](HISTORY/SOURCE_REGISTER.md) — records pending structured Codex
  history, historical PDFs and post-HEAD evidence.

No nonexistent future history file is linked here.

## 20. Session-start checklist

1. Read this Project Master.
2. Read [Project State](PROJECT_STATE.md).
3. Read the relevant architecture, QA, operations and roadmap records.
4. Verify branch, HEAD, latest commit and working tree.
5. Check current production state where facts may have changed.
6. Protect production systems and intentional untracked/user files.
7. Make one safe action at a time and verify it.
8. Do not deploy, push or mutate production without explicit approval.

Also confirm whether the requested work already exists before repeating it.

## 21. Session-end checklist

1. Run the focused tests, related regressions, builds and diff checks appropriate
   to the change.
2. Record implementation, deployment and production evidence separately.
3. Update the detailed record that owns the change or evidence.
4. Update Project State only for a current operational change.
5. Update Project Master only for project-wide architecture, governance, strategy
   or index changes.
6. Preserve historical evidence and source limitations.
7. Record unresolved work in Open Findings or Roadmap Master.
8. Do not leave production changes undocumented.

Confirm repository status and explicitly state what was not staged, committed,
pushed, deployed or changed in production.

## 22. Reconstruction status

### Completed locally

- repository documentation inventory;
- source register and authority model;
- full Project State preservation copy;
- engineering history master;
- decision register;
- production timeline;
- editorial evolution;
- current architecture and operations set;
- QA reconciliation and test history;
- evidence-backed roadmap;
- this Project Master replacement.
- Phase 7 concise Project State replacement and preservation verification.
- Phase 7.2 archive privacy decision and privacy-safe repository archive.
- Phase 7.3 archive-link correction: all repository Markdown links now use the
  privacy-safe archive and no link depends on the excluded exact local archive.

### Pending

- receipt and reconciliation of the ChatGPT export;
- structured preservation and reconciliation of Codex history;
- historical PDF reconciliation;
- post-HEAD production-evidence reconciliation;
- final documentation consistency review and corrections;
- approved documentation commit and push.

Complete historical reconstruction has **not** yet been achieved. The current set
is an evidence-backed repository reconstruction through the stated HEAD, with
explicit unresolved sources and production gaps.

Phases 1–7.3 are complete locally. Project State is the concise local operational
authority, while this document is the permanent navigation/governance entry point
rather than the source of mutable live state. Repository-wide authority transition
still awaits final review and the approved documentation commit and push.

The byte-exact archive remains local, unchanged and hash-verified but is excluded
from the proposed Git commit because it contains inherited personal/local-path
material. The linked privacy-safe archive is the repository historical copy.
