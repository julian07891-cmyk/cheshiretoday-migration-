# Cheshire Today Engineering Log — July 2026

## Executive summary

July 2026 completed Cheshire Today Version 1. During this phase, the project
developed from a working news platform into a production-ready publishing
system with a hardened editorial pipeline, secure newsletter management,
reliable public routing and metadata, a controlled Manual Review workflow, and
an Admin Facebook Publishing Studio.

The work was deliberately incremental. Production-sensitive changes were
audited before implementation, introduced through narrow commits, covered by
focused and regression tests, compiled and built in production mode, and then
verified operationally. `docs/PROJECT_STATE.md` remained the operational source
of truth; this document records the engineering history rather than replacing
current operating instructions.

## Repository baseline

```text
Repository: CT29january26-new-website-migration
Branch: full-scrape-prod
Final HEAD: 9cc745c2cf4bc1830d11c2a66a1df3510eec0d90
Final commit: 9cc745c Record July 2026 platform completion
Operational state file: docs/PROJECT_STATE.md
```

## Major milestones

### Platform completion

#### Homepage

The homepage editorial layout was redesigned and then stabilised around the
current publishing strategy. Hero and top-story presentation, editorial
sections and article allocation were refined without introducing a separate
publication system. Homepage allocation regressions were corrected so the same
article would not be reused incorrectly across competing positions, while the
existing category and editorial selection rules remained authoritative.

#### Admin

The Admin dashboard became a safer operational workspace. Article archive
actions were corrected to call the intended authenticated archive endpoints,
bulk archive age thresholds were sent using the backend's actual JSON contract,
and visible wording was aligned with archive rather than deletion behaviour.
Import results now distinguish public and Manual Review outcomes. Dashboard
labels and mobile layout were updated to describe the real operation performed.

The ordinary subscriber hard-delete action was replaced with an authenticated,
reversible Admin unsubscribe workflow. Subscriber history and preferences are
retained, inactive status remains visible, and reactivation continues through a
verified email link. The historical hard-delete route was not repurposed as the
ordinary lifecycle action.

#### Editorial workflow

The article-generation and rewrite pipeline was audited from source discovery
through research, rewrite, editorial guards, Manual Review and publication.
Legacy import and regeneration routes were then hardened narrowly rather than
being broadly redesigned. Recent-content regeneration gained sanitation,
minimum-quality and Manual Review protection. The legacy real-news importer was
prevented from inserting weak content directly into the public pool.

Local RSS handling was improved without weakening automatic-publication
standards. Suitable lower-confidence local stories are retained in hidden
Manual Review instead of being silently discarded. High-value civic and
economic classification was refined, while crime, court, promotional, unsafe,
duplicate, missing-source and weak-image records continue to be rejected.

#### SEO

Canonical article identity was consolidated, public category hubs were aligned
with the stored taxonomy, unsupported routes began returning real HTTP 404
responses, and sitemap `lastmod` values were made truthful. Article pages,
category hubs, crawler metadata and sitemap behaviour received regression
coverage. Social-preview image handling was also corrected for supported
Newsquest and Contentful sources.

#### Newsletter

The existing digest foundations and presentation were repaired and refreshed.
Daily Brief and Weekly Roundup rendering, excerpts, headlines and article
selection were tested alongside the later secure-management and public-signup
work described below.

#### Manual review

Manual Review was separated from the public article pool and established as a
first-class editorial state. Records remain hidden until an editor acts. Admin
article identifiers and archive-to-review transitions were corrected, and
structured editorial metadata was added to explain deterministic routing,
locality, topic, rewrite, image, freshness and duplicate status. The metadata
assists editorial judgement but does not change publication routing.

#### Publishing

The publication surface was completed across articles, homepage allocation,
category hubs, sitemap and social graphics. Manual Review, archive status and
public visibility remain explicit boundaries. Admin OpenAI work remains
draft-only and does not auto-publish.

#### Security

Admin authentication was applied to content operations, imports, generation,
maintenance and subscriber controls. Legacy operational and image routes were
removed or protected. Newsletter preferences, unsubscribe and reactivation
were migrated to secure purpose-bound request-link and challenge flows with
rate limiting and replay protection.

#### Production hardening

Article live-pool eligibility was corrected so metadata-only records do not
consume visible capacity. Owner-protected records are not automatically
archived by cap and ratio maintenance. A guarded, separately invoked repair
workflow was used instead of embedding historical restoration in normal
runtime behaviour.

Local RSS source coverage expanded through measured shadow evaluation and
staged activation of Knutsford Guardian, Runcorn & Widnes World and Nantwich
News. Shared deterministic policy prevents evaluator drift. Nantwich
county-wide records can enter hidden Manual Review only when useful and after
hard-rejection checks. Northwich Guardian remained inactive pending evidence.

## Facebook Publishing Studio

The Facebook publishing work began with a permanent SVG template and logo
contract. A pure backend composition engine then populated the approved Local
News master using only validated stored article data. It performs bounded image
retrieval, SSRF protection, MIME and dimension checks, XML escaping, headline
fitting, immutable-asset checksum verification and self-contained SVG output.

An authenticated, read-only Admin endpoint exposed the Local News composer.
The frontend then added an article-row action and dedicated dialog. Editors can
preview the returned SVG, rasterise it in the browser to an exact 1200 × 630 PNG
and download it without server-side file writes or database mutation.

The workflow developed through the following stages:

- article link actions: View Article and Copy Link
- deterministic Copy Caption, Copy Hashtags and Copy Facebook Post actions
- Link Preview mode for ordinary linked Facebook publishing
- Branded Graphic mode for explicit graphic generation and download
- a declarative Graphic Type selector
- a separate deterministic Newsletter graphic and publishing-copy contract
- expansion to Local News, Newsletter, Business, Property, AI & Tech, Breaking
  News, Event, Quote and Poll

Article-based types accept the selected Mongo article ID and use stored title,
category and image data. Category eligibility is explicit rather than inferred
from headlines. Breaking News requires editor confirmation. Quote accepts a
verified quotation and attribution; Poll accepts one question and two options.
Both are validated, escaped and kept transient. No post is published or
scheduled automatically.

Release-candidate hardening completed the system:

- the graphic-definition and approved-master registries are genuinely immutable
- frontend options, transport mappings, backend route allow-lists and backend
  composers have inventory-parity protection
- Quote attribution and Poll options use deterministic wrapping and font fitting
  within tested template geometry
- impossible text is rejected rather than clipped or silently truncated
- URL schemes, HTML and practical malformed tag-like fragments are rejected
- approved template and logo checksums remain enforced
- object URLs are revoked on regeneration, type changes, close and unmount
- stale asynchronous results cannot overwrite the active preview or status
- authenticated, archived-record, Manual Review, error-mapping and no-write
  route contracts have focused regressions

The completed Facebook Publishing Studio is an Admin preparation tool: it
generates graphics and copy but does not post, schedule or mutate articles.

## Newsletter redesign

### Public landing page

A dedicated public `/newsletter` landing page replaced the previously invalid
campaign destination. It uses the production design system, the existing public
signup contract and a self-canonical public URL. Browser and crawler responses
carry newsletter-specific title, description, Open Graph and Twitter metadata.

A dedicated 1200 × 630 newsletter Open Graph image was created using the
approved Cheshire Today identity. It replaced the generic share image for the
newsletter page and provides a campaign-specific social preview.

### One-click signup

The public signup journey was simplified. A genuinely new normalised email is
created immediately with The Daily Brief, The Weekly Roundup and Breaking News
Alerts enabled. The client cannot select or override lifecycle or preference
fields. Existing active, inactive or partially subscribed addresses are not
changed, duplicated or publicly reactivated and receive the same
privacy-preserving existing-address response.

### Consent recording

New subscriptions atomically record the approved consent text, consent version,
consent timestamp, enabled preference set and allow-listed signup placement.
Frontend and backend wording is protected by an automated parity test. The
implementation did not add IP-address or user-agent storage.

### Welcome email redesign

The welcome email confirms immediate subscription without requiring a
confirmation click. It describes the Daily Brief, Weekly Roundup and rare
Breaking News Alerts without an unreliable guaranteed-delivery promise. A
welcome-email failure remains non-fatal to successful subscriber creation.

### Accessibility

Public signup surfaces use explicit polite status announcements and alert
semantics for errors. Created and existing outcomes remain distinct without
revealing subscriber state. Close is the primary completion action, while secure
preference management remains an optional secondary path.

### Secure preference management

Secure preferences, unsubscribe and reactivation remain purpose-bound email-link
flows with challenge enforcement, replay protection and rate limiting. The
one-click signup change did not reopen legacy insecure preference paths.

## Production data work

A read-only production audit applied the exact application normalisation
contract: convert the email value to a string, trim surrounding whitespace and
lowercase it. It did not apply provider-specific rewriting such as Gmail-dot or
plus-address removal.

The verified production result was:

```text
Total subscribers: 14,265
Duplicate normalised-email groups: 0
Malformed emails: 0
```

Because no duplicate repair was required, a guarded provisioning workflow added
the production unique email index. The workflow included a read-only planning
stage, expected-count and data-drift checks, interactive exact confirmation and
post-operation verification. It did not silently repair subscriber records.

The resulting production index is active:

```text
Index name: newsletter_email_unique
Status: ACTIVE
```

This makes the public signup route's duplicate-key race handling enforceable at
the database layer while preserving its privacy-safe response.

## Security improvements

July's security work established several consistent boundaries:

- Admin authentication executes before protected database, generation or
  external-image work.
- Secure newsletter tokens are purpose-bound and paired with challenge,
  replay-protection and rate-limit contracts.
- Social-asset image retrieval rejects non-HTTP protocols, loopback, private,
  link-local and unsafe redirect destinations.
- Supported image MIME types, response sizes and dimensions are bounded.
- Approved SVG templates and logo artwork are checksum validated.
- Social SVG output is XML escaped, self-contained and validated at exactly
  1200 × 630.
- Clients cannot submit arbitrary template paths, logo paths, article image
  URLs or SVG content.
- Graphic routes compose in memory and perform no filesystem, article,
  subscriber, posting or scheduling writes.
- Subscriber mutations are restricted to their intended lifecycle operations;
  ordinary Admin unsubscribe does not hard-delete the record.

## QA methodology

The engineering workflow throughout July was consistent:

1. Read the operational state and inspect repository and production state.
2. Audit the existing contract before changing behaviour.
3. Add a focused failing regression for the confirmed defect where applicable.
4. Make the smallest reversible change.
5. Run the narrowest relevant tests immediately.
6. Run related backend and frontend regression suites.
7. Compile changed Python and create a production frontend build when affected.
8. Run `git diff --check` and inspect the complete diff and working tree.
9. Perform safe manual or production verification only after deployment.
10. Record verified results in `docs/PROJECT_STATE.md`.
11. Commit only the reviewed scope.

Production endpoints that imported, regenerated, archived, emailed, published
or deleted data were not used during read-only audits. Database operations were
separated into explicit guarded procedures rather than deployment or startup
side effects.

## Key engineering decisions

### Operational state and history are separate

`docs/PROJECT_STATE.md` remains the concise operational authority. This history
file preserves the completion narrative without making maintainers search a
historical document for current instructions.

### Newsletter signup was simplified without weakening management security

New readers receive an immediate, explicit subscription to the three approved
options. Existing or inactive addresses remain unchanged, while later preference
changes, unsubscribe and reactivation continue through secure email flows.

### A dedicated newsletter page was used

A real `/newsletter` page provides a stable canonical campaign URL and valid
social metadata. It avoids redirecting campaigns to a generic homepage and does
not expose subscriber-management routes or tokens.

### Graphic definitions use an immutable registry

A declarative registry keeps identifiers, eligibility, templates, logo variants,
copy and filenames aligned. Immutable structures and parity tests prevent
runtime mutation and frontend/backend inventory drift.

### Production verification precedes completion records

Subscriber totals, duplicate status and index state were verified before being
recorded as operational facts. Feed activations and Manual Review behaviour were
likewise observed before later rollout decisions.

## Major production milestones

- The secure newsletter management cutover was completed.
- The public newsletter landing page became the canonical campaign destination.
- One-click all-three newsletter signup became operational.
- The production subscriber collection was verified with zero duplicate groups
  and zero malformed emails.
- The unique `newsletter_email_unique` production index was provisioned and
  verified active.
- Knutsford Guardian, Runcorn & Widnes World and Nantwich News were activated
  through the guarded Local RSS workflow.
- Facebook Publishing Studio was completed with nine approved graphic types.
- Version 1 platform completion was recorded at commit `9cc745c`.

## Repository milestones

Significant July commits, in chronological order within each phase, include:

### Editorial, security and public platform foundations

- `3c6e858` — Tighten OpenAI editorial standards
- `611b57d` — Cross-check OpenAI rewrites with independent fact research
- `1f18f9b` — Separate live articles from manual review
- `5a943fa` — Protect Admin content operations with authentication
- `41346c7` — Remove unsafe legacy operational routes
- `85bc971` — Complete secure newsletter legacy cutover
- `bb925f1` — Redesign homepage hero and top stories
- `608ed7b` — Align public hub taxonomy and routing
- `0cf67e9` — Return real 404s for unsupported routes
- `13be6af` — Use truthful sitemap lastmod dates
- `ffd4a52` — Fix homepage story allocation

### Admin, live-pool and Local RSS hardening

- `1034bb9` — Guard recent article regeneration
- `50bf9c6` — Guard legacy real-news import
- `4622edf` — Fix Admin bulk archive thresholds
- `f8858ec` — Correct Admin archive actions and import results
- `a2421d6` — Add safe Admin subscriber unsubscribe
- `be5c4ed` — Harden article live pool and align newsletter tests
- `dc18e65` — Restore eligible articles through live pool cap
- `468e0b7` — Route suitable Local RSS candidates to Manual Review
- `6da87da` — Add editorial metadata to Manual Review
- `4e00f0f` — Add shared Local RSS policy and Newsquest shadow evaluator
- `6d87817` — Activate Knutsford Guardian Local feed
- `99dec3e` — Activate Runcorn and Widnes World feed
- `9cfb187` — Activate Nantwich News feed and county-wide manual review routing
- `c80ca7e` — Refine local RSS manual review quality

### Brand and Facebook publishing

- `86794f6` — Add Cheshire Today Brand Asset Library v1.0
- `07bb72e` — Add Instagram Story and Feed Template Systems v1.0
- `0e8d767` — Add Reels Cover Template System v1.0
- `2f4e1a0` — Add Brand Guidelines v1.0
- `f094c63` — Add Facebook Template System v1.0
- `dd7a22f` — Refine Facebook template logo treatment
- `34fa9f0` — Phase 1A Facebook social asset composition engine
- `1aa455a` — Add authenticated Facebook social asset route
- `4ea06dd` — Add Admin Facebook graphic generator
- `b57df05` — Add article link actions to Facebook graphic dialog
- `d86dc24` — Add Facebook publishing copy pack
- `4424504` — Refine Facebook publishing workflow
- `42812c7` — Add Facebook publishing modes
- `43c1489` — Add Facebook newsletter graphic support
- `886d9f3` — Complete Facebook graphic publishing system

### Newsletter completion and production provisioning

- `d845ddd` — Add public newsletter landing page
- `82bd4ab` — Simplify newsletter signup journey
- `0bb3ce8` — Add guarded newsletter email index provisioning
- `9cc745c` — Record July 2026 platform completion

## Lessons learned

- A QA-first workflow turns production observations into narrow regressions
  instead of speculative refactors.
- One safe change at a time makes failures attributable and rollbacks practical.
- Security boundaries must be designed before convenience features, especially
  for subscriber management, remote images and Admin publishing tools.
- Repository tests cannot prove production data state; read-only production
  verification is required before migrations or operational claims.
- Documentation should record verified outcomes, not intended outcomes.
- Small reversible commits provide clearer review, safer deployment and more
  useful engineering history than broad completion batches.
- Shared pure policy and parity tests reduce drift between audit tools,
  production classifiers, frontend inventories and backend routes.

## Version 1 completion status

### Completed

- Public homepage, article, category-hub, canonical, sitemap and 404 contracts
- Authenticated Admin editorial and maintenance workflows
- Hidden Manual Review with deterministic editorial metadata
- Hardened import, rewrite, regeneration and live-pool boundaries
- Secure newsletter preferences, unsubscribe and reactivation
- Public newsletter landing page and dedicated social preview
- One-click all-three newsletter signup with consent evidence
- Production newsletter uniqueness audit and guarded unique index
- Local RSS policy sharing, shadow evaluation and staged feed expansion
- Brand Asset Library and approved Facebook master templates
- Admin Facebook Publishing Studio with nine graphic types
- Focused, regression, compilation and production-build coverage for the above

### Operational

- Production public site and Admin workflows
- Morning, midday and evening content scheduler
- Manual Review and archive workflows
- Daily Brief and Weekly Roundup scheduling
- Secure newsletter management
- Public newsletter signup
- `newsletter_email_unique` production index
- Active guarded Local RSS source set
- Facebook graphic and deterministic publishing-copy preparation

### Future opportunities

- Continued editorial and content growth
- Ongoing production monitoring
- Evidence-led source expansion
- Additional future feature work through the established QA-first process

These are opportunities, not Version 1 completion claims.

## Appendix

### High-level timeline

```text
7–12 July: editorial guards, fact research and rewrite quality
14–20 July: Manual Review separation, Admin security and secure newsletter management
21–24 July: design, public routing, SEO, Admin and live-pool hardening
25–26 July: Local RSS Manual Review, source evaluation, feed rollout and brand assets
26–27 July: Facebook templates, composition engine and Admin publishing workflow
27 July: newsletter landing page, one-click signup, production uniqueness index and Version 1 completion
```

### Production statistics

```text
Newsletter subscriber records: 14,265
Normalised-email duplicate groups: 0
Malformed email records: 0
Unique email index: newsletter_email_unique
Unique email index status: ACTIVE
```

### Newsletter verification

- The public `/newsletter` destination is the canonical signup page.
- New subscribers receive The Daily Brief, The Weekly Roundup and Breaking News
  Alerts immediately.
- Existing and inactive subscriber records are not modified by public signup.
- Consent wording and stored consent evidence are aligned.
- Secure preference, unsubscribe and reactivation workflows remain operational.
- Production email uniqueness is enforced by `newsletter_email_unique`.

### Testing summary

The final Facebook release-candidate verification recorded:

```text
Backend social-asset tests: 105 passed
Focused frontend publishing tests: 80 passed
Complete frontend suite: 211 passed
Python compilation: passed
Production frontend build: passed
git diff --check: passed
```

The newsletter signup completion verification recorded focused signup,
welcome-email, consent-parity, related security, complete frontend, compilation
and production-build passes before release. Exact phase-specific counts remain
in `docs/PROJECT_STATE.md`.

### Final repository state

```text
Repository: CT29january26-new-website-migration
Branch: full-scrape-prod
HEAD: 9cc745c2cf4bc1830d11c2a66a1df3510eec0d90
Operational source of truth: docs/PROJECT_STATE.md
Historical engineering log: docs/HISTORY/ENGINEERING_LOG_JULY_2026.md
```

## Version 1 completion

### Representative Instagram operational verification

The approved Instagram systems moved beyond structural validation into
representative real-use verification. A current Cheshire Today Local News
article was composed through the approved Story workflow and exported as an
exact `1080 × 1920` sRGB PNG. Representative Feed and Reels working copies were
also exported at `1080 × 1080` and `1080 × 1920` respectively. Image crops,
headline wrapping, logo and CTA placement, hidden guides, placeholders and safe
areas were reviewed without altering the permanent masters.

These representative checks signed off the production export workflow. A final
private preview in the Instagram app remains an ordinary per-post editorial
check for platform chrome and device presentation, not an outstanding Version
1 engineering task.

### Threads workflow completion

The Threads Version 1 workflow was completed as a native, conversational and
text-led publishing process. It documents article selection, the two-step
editorial approval sequence, post structure, link and image use, engagement,
frequency, the 40/40/20 editorial balance and a copy-ready acceptance checklist.
Repository evidence did not establish a need for a dedicated Threads graphic
system, so no unnecessary template or software was introduced.

### Documentation and social-media completion

The operational state, July engineering history, Brand Asset Library, Brand
Guidelines and platform READMEs now record the approved production contracts.
Stale references that described completed Facebook and Instagram systems as
future work, the approved Brand Guidelines as unapproved, or Threads as a
graphics system were corrected during the final handover audit.

Facebook Publishing Studio, Instagram Highlights, Stories, Feed graphics and
Reels covers, and the native Threads workflow together complete the Version 1
social-media suite.

### Engineering handover

Cheshire Today Version 1 engineering is complete. The Version 1 implementation
baseline before the final documentation commit is:

```text
Repository: CT29january26-new-website-migration
Branch: full-scrape-prod
HEAD: b1e6b186a01865870a9a1deed2e187303a565552
Operational source of truth: docs/PROJECT_STATE.md
Historical engineering log: docs/HISTORY/ENGINEERING_LOG_JULY_2026.md
```

The project now moves into Operations & Growth. Further engineering should be
evidence-led and follow the established QA-first, narrowly scoped and
reversible workflow.

## Unified Social Publishing Admin completion

The Facebook-specific Admin workflow was extended into one shared Social
Publishing dialog without reopening Facebook behaviour. The implementation was
completed as a sequence of independently reviewed changes:

- `3bc2a1f` added Instagram Story Top Story generation to Admin;
- `7e64bf8` refined the verified Story headline and CTA geometry;
- `50a3c6f` added Instagram Local News Feed and Reels Cover generation;
- `bd19af7` added deterministic Instagram format-specific copy helpers;
- `5ceb997` added native Threads post preparation and copying.

Instagram uses authenticated, stored-article-only SVG generation, immutable
checksum-protected masters, safe image retrieval, self-contained previews and
exact browser-side PNG exports. Threads remains a transient text-only workflow
with explicit editorial approval and constrained verified copy. Neither platform
adds automatic posting, scheduling, persistence or AI generation. Facebook's
existing nine graphic types and copy contracts remain unchanged.

Focused final source verification passed `124` frontend tests spanning the shared
dialog, Facebook regressions, Instagram generation/rasterisation/copy services
and Threads validation/copy behaviour.

The production verification on 28 July 2026 confirmed HTTP 200 for `/health` and
`/admin`, but the deployed Admin bundle `main.b82e6a85.js` did not yet contain the
shared Social Publishing, Instagram or Threads implementation. Consequently,
authenticated live generation, download and clipboard verification remained a
post-deployment operational handover check; it was not recorded as completed.

## First-party article-view tracking repair

A read-only analytics audit identified that first-party article readership was
not being recorded by the public article page and that the existing tracking
route did not resolve public eligibility before analytics writes. The working
tree also showed that `backend/server.py` contained two independent changes:
article-view tracking and Most Read period correctness.

The work was separated at hunk level. The article-view route, public frontend
integration and focused tests were isolated from all Most Read changes through
interactive partial staging. The staged diff was then reviewed independently to
confirm that it contained only article-view resolution, visibility rejection,
canonical Mongo identifier use, one-hour deduplication, non-blocking frontend
tracking and stale-navigation protection.

The isolated repair was committed as:

```text
6a95ba9 Repair first-party article view tracking
```

The commit was pushed successfully to `origin/full-scrape-prod`. The separate
Most Read handler and tests were intentionally left unstaged for their own QA,
review and commit. Import, scheduler, publishing, newsletter and production-data
behaviour remained outside the change.

## Most Read period-correctness repair

After the article-view repair was isolated and released, the remaining Most Read
work was reviewed as a separate QA change. The audit confirmed that the endpoint
limited aggregated view groups before resolving public eligibility. Missing,
archived or Manual Review-hidden records could therefore consume result slots and
exclude lower-ranked eligible articles.

The endpoint was corrected to retain descending period-view ordering while
applying the requested limit only after eligible public records had been resolved.
The lifetime `articles.view_count` fallback was removed, while the established
`today`, `week`, `month` and invalid-period contracts were preserved.

Deterministic regression coverage proved that hidden records do not consume
limited slots and that lower-ranked eligible records fill the result in the
correct order. Focused and directly related tests passed `61` checks; Python
compilation and `git diff --check` also passed.

The change was committed as:

```text
a93d4bf Fix Most Read public result limiting
```

The commit was pushed successfully to `origin/full-scrape-prod`. After the push,
the working tree contained only the intentionally untracked `AGENTS.md` file.

## First-party analytics QA — complete engineering handover

### Audit conclusions

The closing analytics review traced public article loading, the view-recording
endpoint, `article_views`, the lifetime `articles.view_count` field and the Most
Read endpoint. It established that the public article page was not recording a
first-party read, while an empty period in Most Read was being replaced by a
lifetime ranking. Period events and lifetime counters were therefore retained as
separate concepts: `article_views` is authoritative for period rankings, while
`view_count` remains a lifetime field and is not a period fallback.

The work intentionally did not introduce indexes, TTL retention, bot filtering,
homepage or Admin changes, or a wider analytics redesign. Existing one-hour
IP/article deduplication remained the production contract. Residual risks noted
for future evidence-led work were concurrent application-level deduplication,
shared/proxy IP ambiguity and non-transactional event/counter writes.

### Isolation and delivery sequence

The first implementation diff mixed article-view tracking and Most Read changes
inside `backend/server.py`. They were classified as independent work streams and
were not released together. Interactive partial staging selected only the
article-view handler from the shared backend file, together with the public-page
integration, isolated helper and focused tests. The staged diff was reviewed to
prove that the Most Read hunk remained outside the commit.

Article-view tracking was then released through:

```text
6a95ba9 Repair first-party article view tracking
c4d9faf Update project state after article-view tracking repair
```

Both commits were pushed to `origin/full-scrape-prod`. Verification included `55`
focused backend/visibility tests, `7` focused frontend tests, `268` complete
frontend tests, Python compilation, a successful production frontend build and a
clean `git diff --check`.

The remaining Most Read diff was audited independently. QA found that a database
limit applied before visibility resolution could allow missing, archived or
Manual Review-hidden records to consume slots. The final implementation retained
descending period-view ordering but applied the result limit only after eligible
public articles were resolved. It removed the lifetime fallback while preserving
`today`, `week`, `month`, invalid-period, Mongo-ID and legacy-ID behavior.

Most Read was released through:

```text
a93d4bf Fix Most Read public result limiting
d6eb46b Record completed Most Read fix
```

Both commits were pushed to `origin/full-scrape-prod`. Focused and related tests
passed `61` checks; Python compilation and `git diff --check` passed. The branch
then reached `d6eb46b1c400c98e5f25595c01fd34ce2373c0b0` with only the intentionally
untracked `AGENTS.md` remaining.

### Operational and documentation decisions

Throughout the sequence, imports, scheduler, publishing, newsletters, subscribers,
provider delivery and production data were protected explicitly. No production
import, scheduler, newsletter-send or database operation was run. Runtime and
documentation work used separate commit boundaries so that operational state
records did not obscure implementation review.

The agreed handover practice for future substantial engineering chats is to add
a durable summary before closure: architecture conclusions, independent task
boundaries, exact QA evidence, commits and pushes, repository transitions,
protected-system impact and remaining risks belong in `docs/PROJECT_STATE.md` and
the relevant historical engineering log. Prompt iterations and conversational
back-and-forth are excluded from that record.

## Scheduled article-generation memory observability

A read-only Render investigation identified web-service OOM terminations at
approximately 12:01 BST on 29 July and 18:00 BST on 30 July. Each exceeded the
Starter instance's 512 MB limit and aligned with a scheduled article-generation
slot. Static code-path analysis found several plausible peaks, including fully
buffered multi-feed acquisition and unbounded duplicate-cleanup reads, but the
retained platform events contained no Python stack trace or phase-level memory
evidence.

The first engineering response was deliberately limited to observability.
Standard-library process maximum-RSS and monotonic-duration logging was added at
existing workflow boundaries, with allow-listed numeric counts and a consistent
`article_generation_memory` prefix. The helper fails safely and excludes content,
URLs, images, records, credentials and provider payloads.

No import, scheduler, database, editorial, Manual Review, AI, newsletter or
deployment behaviour was optimised or restructured. Deployment and observation
of normal scheduled runs remain pending before any memory mitigation is selected.
