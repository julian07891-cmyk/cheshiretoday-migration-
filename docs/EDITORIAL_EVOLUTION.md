# Cheshire Today — Editorial Evolution

> **Reconstruction status:** editorial policy reconstructed from repository evidence
> through HEAD `1601ae48be281153e5dd4af0eee0889a26835162`. Later chat-only conclusions and
> post-HEAD production findings remain unreconciled.

## Document purpose

This document explains how Cheshire Today’s editorial mission, automated pipeline,
human review and presentation rules evolved. It records previous behaviour as
history rather than silently turning it into current policy.

## How to use this document

- Use “Current editorial principles at repository HEAD” for the evidence-backed HEAD
  contract, then verify it in code before operational changes.
- Follow the linked [Engineering History](HISTORY/ENGINEERING_HISTORY_MASTER.md),
  [Decision Register](DECISION_REGISTER.md), [Production Timeline](PRODUCTION_TIMELINE.md)
  and [Source Register](HISTORY/SOURCE_REGISTER.md) for context.
- Treat ratio and category targets as editorial aims, never permission to publish
  weak or unsafe material.

## Editorial mission

### Problem and previous behaviour

Early feed-led operation risked becoming a generic aggregation site: crime,
incidents, lifestyle, shopping and undifferentiated national material could crowd
out useful Cheshire economic and civic reporting.

### Change and rationale

The project defined Cheshire Today as a clear, trustworthy publication combining
local public-interest news with relevant UK, business, finance and technology
coverage. Commercial material should help readers rather than dictate news choice.

### Implementation and result

Editorial intent moved into source selection, deterministic import filters,
homepage allocation, Manual Review, sitemap/newsletter selection and guide routing.
By Version 1 completion, this was a cross-system policy rather than presentation
copy alone.

- **Sources:** [preserved state](ARCHIVE/PROJECT_STATE_REDACTED_2026-08-06.md), February
  strategy, April homepage restoration and Version 1 sections;
  [July log](HISTORY/ENGINEERING_LOG_JULY_2026.md), executive summary.

## Content strategy evolution

### From feed volume to quality-controlled supply

- **Previous behaviour:** homepage and imports were repeatedly adjusted by count,
  source depth and chronology; weak stories could fill gaps.
- **Change:** quality gates now precede public caps, and caps may send qualifying
  excess records to Manual Review rather than forcing publication.
- **Rationale:** freshness and ratios are secondary to factual completeness,
  relevance and image/source quality.
- **Implementation:** strategic filters, full-content floors, public import caps,
  Manual Review routing and live-pool repair.
- **Result:** lower candidate yield is accepted when available source material is
  poor.
- **Sources:** preserved state, March–May import and 24–26 July Local RSS sections;
  Git `c7f8e20`, `be5c4ed`, `468e0b7`, `4e00f0f`.

### From broad experiments to controlled rollouts

- **Previous behaviour:** source pools, feed-image normalisation, guide surfaces and
  verification services were sometimes changed together.
- **Change:** risky experiments were reverted, feature-gated or staged one source at
  a time.
- **Result:** Local RSS, newsletter security, metadata and Editorial Similarity used
  explicit phases and observation gates.
- **Sources:** preserved state, failed/reverted sections;
  [Engineering History](HISTORY/ENGINEERING_HISTORY_MASTER.md), “Failed, reverted
  and deferred work”.

## Category and 40/40/20 model

### Problem

Pure chronology and broad source feeds produced inconsistent category balance and
allowed sport, video, astronomy, lifestyle or generic national stories to consume
prominent slots.

### Policy shift

The homepage target became approximately:

- 40% Cheshire/local;
- 40% UK public-interest;
- 20% business, finance and AI/technology.

### Implementation

Backend classification, homepage section allocation, source interleaving and
newsletter selection were aligned over several iterations. Business and Finance
framing was refined; property/tax and AI-tech retained strategic treatment.

### Result and limits

The model is a directional allocation contract. It does not override minimum
content, safety, duplicate, locality or image requirements, and actual proportions
depend on eligible supply.

- **Sources:** preserved state, February 40/40/20 and April category-alignment
  sections; Git `6e77dd4`, `6b928d4`, `509e263`, `3cfe089`; July log, Version 1.

## Local relevance

### Problem and previous behaviour

Town/location metadata was sometimes lost between feed configuration, parsing,
insertion and public normalisation. A fixed town allow-list could also discard useful
county-wide civic or economic stories.

### Change

Location persistence was repaired across construction paths. Deterministic locality
checks distinguish qualifying town matches, county-wide Cheshire relevance and
non-local material. Useful soft failures can enter hidden Manual Review.

### Rationale

Local relevance must be evidenced by the story, not created by an AI rewrite or a
false Cheshire angle.

### Result

Town and county-wide civic/economic material became reviewable, while Manchester,
weak or invented locality continued to fail public gates.

- **Sources:** preserved state, 11–12 April location work, May locality guards and
  25–26 July Local RSS updates; Git `1255475`, `1ed49b8`, `41639cf`, `9cfb187`.

## Crime, court and filler controls

### Problem and previous behaviour

High-volume local sources supplied crime, court, death notices, galleries,
promotional products and soft human-interest filler that could overwhelm lead slots.

### Change

Deterministic source/import filters and homepage/public-surface checks suppress:

- hard crime and court material;
- death notices and obituary leakage;
- gallery/photo filler;
- deals, gadgets and promotional shopping copy;
- celebrity, entertainment and generic lifestyle items without sufficient value;
- spam, invalid sources and known weak-image candidates.

Suitable non-crime soft local candidates may be retained in Manual Review, but hard
rejects do not gain review status merely to increase volume.

### Result

The policy moved from UI-only hiding to import, public API, homepage, sitemap and
newsletter enforcement.

- **Sources:** preserved state, February/March filtering, April obituary cleanup,
  May sitemap quality and July Local RSS policy; Git `262d4fb`, `c39a00e`,
  `3c6d96e`, `22914d1`, `4e00f0f`.

## Article quality and minimum-content safeguards

### Problem and previous behaviour

RSS summaries and failed rewrites could appear as short, boilerplate or compressed
articles. Early cleanup rules could also delete useful short source records.

### Change

- Plain RSS text is sanitised and paragraph structure preserved.
- Perplexity output must meet full-content expectations before ordinary publication.
- Short or failed candidates are skipped, archived for quality, or routed to Manual
  Review according to context.
- Owner-protected/manual edits are excluded from automated low-quality cleanup.

### Rationale and result

The public site prioritises usable reader-facing articles while retaining human
recovery paths. A numeric threshold is not itself proof of factual quality.

- **Sources:** preserved state, March long-form/paragraph work and July article
  safety; Git `9deb0e4`, `000fb94`, `53d5911`, `c7f8e20`, `be5c4ed`.

## Perplexity research and rewrite role

### Evolution

1. Perplexity was initially disabled by default behind an AI budget guard
   (`295041e`).
2. March introduced scheduled long-form rewriting, then timeouts and immediate
   bounded execution (`000fb94`, `bd762fc`, `1408300`).
3. Prompts were strengthened to research and verify source claims (`5a892be`).
4. May experiments exposed fallback and budget edge cases; broad changes were
   reverted and a narrower working flow restored (`d0b7243`).
5. July established Perplexity as the structured fact-pack fallback for Admin
   OpenAI drafts when direct source retrieval was blocked (`a01de4b`, `2723fc7`).

### Current rationale at HEAD

Perplexity supports source-led research and automated rewriting, but provider output
does not override deterministic gates or human verification. Stored article fields
are leads; uncertain claims must not be converted into facts.

- **Sources:** preserved state, March/May/July AI sections; Git references above.

## OpenAI admin-review role

### Problem and previous behaviour

Manual ChatGPT rewriting could improve copy but was not integrated, reproducible or
bounded. Early generated drafts sounded professional while introducing unsupported
names, comparisons and conclusions.

### Change

An authenticated Admin action now:

1. reads stored article fields as leads;
2. attempts direct source retrieval;
3. obtains a structured Perplexity fact pack when necessary;
4. asks OpenAI for a bounded JSON draft;
5. runs deterministic editorial checks and at most one focused correction pass;
6. returns the draft and diagnostics to the editor without saving.

### Rationale and result

OpenAI is a human-review tool, not the scheduled publishing engine. Prompt rules are
supplemented by deterministic checks because fluent text is not factual evidence.

- **Sources:** preserved state, “Admin OpenAI factual rewrite and editorial guard”;
  Git `ad131c7`, `5ef4041`, `2723fc7`, `3fcc4a3`, `83d8d69`;
  [Decision CT-DEC-004](DECISION_REGISTER.md#ct-dec-004--openai-is-admin-only-and-never-auto-publishes).

## Manual Review evolution

### From archive display to first-class workflow

- **Previous behaviour:** uncertain AI articles were hidden/archived inconsistently,
  IDs differed between Admin paths, and edits could fail to restore or could carry
  stale review flags.
- **Change:** dedicated hidden queue, public/sitemap/newsletter exclusion, consistent
  IDs, edit/restore, Force Live guards and deterministic review metadata.
- **Implementation:** May foundation; July live/review/archive separation; August
  publication-intent notice and confirmation.
- **Result:** backend publication gates remain authoritative. A Manual Review update
  may restore an article only if those existing safeguards pass.

### Descriptive editorial metadata

Recommendation, locality, topic, image, freshness, duplicate and failed-gate fields
describe why a record is in review. They do not score or publish it.

- **Sources:** preserved state, May–August Manual Review sections; Git `7dda210`,
  `d426558`, `1f18f9b`, `6da87da`, `50ede47`.

## Duplicate and same-story handling

### Version 1 exact identity

Duplicate prevention evolved from title checks and unsafe first-five-word cleanup to
multiple deterministic layers:

- normalised title and source URL checks;
- batch title/source sets;
- image safeguards where applicable;
- active and archived snapshots;
- Mongo uniqueness and `DuplicateKeyError` handling;
- duplicate cleanup that prefers protected/manual records.

The startup first-five-word cleaner was disabled after removing legitimate recent
stories. Automatic similarity does not replace these rules.

### Cross-publisher same-event stories

The Hough/former-kennels investigation showed that independently published records
can cover the same underlying event without sharing exact title/source identity.
Phase 2A added a deterministic advisory scorer; Phase 2B logs scheduled comparisons
only. It cannot block, archive, merge, delete or route Manual Review.

- **Sources:** preserved state, March duplicate history and final Editorial
  Similarity sections; Git `3ca0834`, `b4612e1`, `a676059`, `a31fcab`, `8043fdd`,
  `5e1a875`; [Decision CT-DEC-015](DECISION_REGISTER.md#ct-dec-015--version-1-duplicate-prevention-remains-authoritative).

## Image and source-quality safeguards

### Problem

Missing, tiny, duplicate, signed or publisher-branded images caused skipped imports,
broken previews and inconsistent article/social presentation.

### Evolution

- Source URLs became exact identity and attribution evidence.
- Reach and Guardian social variants were normalised carefully rather than globally.
- Newsquest image resolution and guarded backfill were added before staged Local RSS
  activation.
- Social publishing uses the stored approved article image; image selection does not
  establish story identity by itself.
- Global feed-image normalisation was reverted when it risked changing unrelated
  image behaviour.

### Result

Public, crawler and social images share explicit source-specific contracts, while
invalid/missing images remain publication guards.

- **Sources:** preserved state, March social image, April image revert, May Guardian
  and July Newsquest sections; Git `a01c76e`, `27c5a57`, `aa725ae`, `3f4ab10`,
  `c1356ea`.

## Homepage allocation and editorial presentation

### Evolution

- Early Homepage V1 established hero, Top Stories and Latest sections.
- Global dedupe and archived filtering removed repeated records.
- Crime-sensitive lead guards and 40/40/20 allocation shaped editorial hierarchy.
- Freshness fixes distinguished source publication dates from insertion/update
  freshness.
- July’s design work unified the hero, sections and article reading flow without
  weakening backend visibility.

### Result

At HEAD, the homepage is an editorial selection surface over eligible articles, not
the authority for publication status. Public APIs and backend gates remain primary.

- **Sources:** preserved state, February/March homepage, April restoration and July
  redesign; Git `217a6f5`, `3bfad8d`, `6e77dd4`, `0e1d639`, `bb925f1`, `ffd4a52`.

## Newsletter editorial selection

### Problem and previous behaviour

Chronological or overly narrow selections could omit strategic categories, include
Manual Review records or repeatedly address the same recipients.

### Change

Daily Brief and Weekly Roundup use quality-first article selection aligned with the
publication pillars. Manual Review records are excluded. Recipient selection is
separate from article selection and uses caps/rotation/engagement evidence.

### Result

Newsletter editorial choice follows public-quality rules but is not identical to
homepage allocation. Provider acceptance, opens and clicks remain distinct metrics.

- **Sources:** preserved state, April/May newsletter sections; July log, newsletter
  redesign; Git `3cfe089`, `60753ac`, `540f73d`, `7267e67`.

## Social-publishing workflow

### Problem and previous behaviour

Legacy Facebook posting/analytics controls mixed external platform operations with
article management, while Instagram/Threads lacked consistent assets and copy.

### Change

Version 1 established deterministic repository-backed Facebook, Instagram Story,
Feed, Reels and Threads composition. The unified Admin prepares previews, graphics,
canonical links and copy but does not auto-publish. Legacy posting controls were
later contained.

### Result

Social workflow is an editor-operated handoff. First-party Facebook UTMs measure
article traffic without restoring legacy Meta engagement panels.

- **Sources:** [July log](HISTORY/ENGINEERING_LOG_JULY_2026.md), Facebook Publishing
  Studio and Version 1 sections; [brand assets](brand-assets/); Git `9902e3c`,
  `2bcdf5c`, `7b08673`, `9b024cc`.

## Manual article editing standards

### Policy

- Title, summary, content, category, image, author, source, source URL, tags, featured
  and scope remain explicit editor-controlled fields.
- Manual edits and protected records must win over automated duplicate replacement.
- Updating a Manual Review article may restore it only when backend safeguards pass.
- Add Article and Update are not a draft/publish split; no new Save Draft endpoint
  exists at HEAD.
- Source and factual claims require verification; fluent AI output is insufficient.

### Mobile ergonomics

The shared editor is bounded, top-aligned on touch/mobile, uses 16-pixel controls and
a sticky close header. These changes preserve editing semantics and accessibility
pinch zoom.

- **Sources:** preserved state, Manual editing, August publication-intent and mobile
  sections; Git `edcf85f`, `6328cf3`, `a6bfb78`, `50ede47`.

## Current editorial principles at repository HEAD

The following principles are supported by repository evidence at
`1601ae48be281153e5dd4af0eee0889a26835162`:

1. Publish useful, attributable Cheshire and UK public-interest journalism, not feed
   volume for its own sake.
2. Treat 40/40/20 as an allocation aim subordinate to quality and safety.
3. Preserve source URL, canonical identity, date, location and image provenance.
4. Reject exact duplicates through Version 1 deterministic checks.
5. Treat Editorial Similarity as scheduled shadow evidence only.
6. Suppress crime-heavy, promotional, obituary, gallery and weak filler material.
7. Require usable, sufficiently complete reader-facing copy for public publication.
8. Use Perplexity for bounded source-led research/rewrite, with deterministic gates.
9. Keep OpenAI authenticated, Admin-only, draft-only and human-reviewed.
10. Keep Manual Review hidden and distinct from Live and Archive.
11. Prefer archive/recoverability over ordinary hard deletion.
12. Do not let automated caps or cleanup override protected manual editorial work.
13. Keep newsletter and social selection aligned with public editorial safeguards.
14. Do not infer production truth, calibration or indexing recovery from tests alone.

- **Sources:** preserved state, final Version 1 and Editorial Similarity sections;
  [Decision Register](DECISION_REGISTER.md); current Git history through HEAD.

## Unreconciled editorial history

- The pending ChatGPT export may contain earlier editorial rationale or rejected
  alternatives.
- Codex investigations, including post-HEAD duplicate and production article audits,
  are not yet systematically preserved.
- Historical strategy PDFs are missing or unreconciled and cannot override the HEAD
  principles above.
- Post-HEAD production behaviour must not be incorporated until repository-backed.
- Thresholds and UI for Editorial Similarity remain unapproved at HEAD.
