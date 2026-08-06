# Cheshire Today Reconstruction Source Register

## Purpose and authority model

This register identifies the evidence available for rebuilding the Cheshire Today
project knowledge base. It records provenance, authority, preservation status and
known limitations without converting historical statements into current facts.

The reconstruction uses the following authority levels, in descending order for
questions about current technical or production state:

1. **Current repository code and configuration** — the checked-out implementation
   and deployment configuration at a verified commit.
2. **Verified production evidence** — timestamped health responses, deployment
   records, logs, settled browser behaviour and other read-only live evidence.
3. **Git commits, branches and tags** — durable implementation history and
   checkpoints, subject to verification that a named ref was deployed or remained
   current.
4. **Current operational repository documentation** — principally the concise
   local `docs/PROJECT_STATE.md`; repository-wide transition awaits the approved
   documentation commit and push.
5. **Dated QA and engineering snapshots** — accurate records of the state audited
   at their stated date and commit, not automatic statements of present status.
6. **Historical strategy and research references** — useful context that cannot
   override current code, verified production evidence or later decisions.
7. **ChatGPT and Codex records awaiting reconciliation** — source material only;
   it becomes authoritative project knowledge after evidence-based reconciliation
   into repository records.
8. **Unverified or incomplete sources** — missing, empty, partial, superseded or
   otherwise unconfirmed material that must be labelled before use.

Repository code and verified production evidence control current technical truth.
Where they conflict, the conflict must be recorded and resolved with dated evidence
rather than silently editing history. `docs/PROJECT_STATE.md` is the concise local
operational authority after Phase 7; repository-wide transition awaits the approved
documentation commit and push. Historical files remain evidence and must not be
silently rewritten. ChatGPT and Codex material becomes authoritative only after
reconciliation into repository records. Old PDFs are historical references, not
current operational truth.

## Preservation checkpoint

The Phase 2 preservation copy was made on 6 August 2026 before any restructuring of
`docs/PROJECT_STATE.md`.

| Property | Source and preservation copy |
| --- | --- |
| Source | `docs/PROJECT_STATE.md` |
| Preservation copy | `docs/ARCHIVE/PROJECT_STATE_FULL_2026-08-06.md` |
| SHA-256 | `6ab1a3a70be61cbeaca38301a59ef1ddb846231a39be9642cea7310b5ac7faaf` |
| Bytes | 997,716 |
| Lines | 25,597 |
| Equality check | Byte-for-byte `cmp` passed |

The original source remained unchanged during Phase 2 and is preserved exactly at
the local archive path. Phase 7 later replaced the working `docs/PROJECT_STATE.md`
with a concise local operational source. Phase 7.2 retained the exact archive
locally but excluded it from the proposed Git commit, then created a privacy-safe
repository archive. All repository documentation changes remain unstaged and await
final review and an approved commit and push.

## Registered repository sources

### Current operational state

#### Original preserved operational source

- **Original path:** `docs/PROJECT_STATE.md`.
- **Source type:** accumulated operational state, engineering chronology and session
  handover record.
- **Date range:** March 2026 through 4 August 2026, with older strategic references.
- **Authority level:** 5 as dated historical evidence after the Phase 7 replacement.
- **Material covered:** production architecture, deployments, editorial workflow,
  Manual Review, newsletter, SEO, social publishing, monetisation, incidents, QA,
  tests, decisions and session continuation instructions.
- **Original SHA-256:** `6ab1a3a70be61cbeaca38301a59ef1ddb846231a39be9642cea7310b5ac7faaf`.
- **Original size:** 25,597 lines; 997,716 bytes.
- **Exact preserved location:** `docs/ARCHIVE/PROJECT_STATE_FULL_2026-08-06.md`.
- **Limitations:** combines current and superseded state, repeats source summaries,
  contains out-of-order history and retains obsolete "current" and "next step"
  statements.
- **Reconciliation status:** inventoried, decomposed and preserved exactly; retained
  locally and excluded from the proposed Git commit by the Phase 7.2 owner decision.

#### Current concise operational source

- **Path:** `docs/PROJECT_STATE.md`.
- **Source type:** concise current operational source of truth.
- **Repository status:** tracked file modified locally in Phase 7; unstaged and
  pending approved commit and push.
- **Authority level:** 4 for current local operations, governed by
  `docs/PROJECT_MASTER.md`.
- **Phase 7 replacement baseline SHA-256:** `a0230c90c2a6ec59e0e0ade66f42d1020e9b96bf2241575b969835b8138a38a9`.
- **Phase 7 replacement baseline size:** 478 lines; 19,781 bytes.
- **Current Phase 7.1 SHA-256:** `d430393dca8386fea9911d493326632ec98619c957aa6e5f1111fe36a87ba8f2`.
- **Current Phase 7.1 size:** 486 lines; 20,050 bytes.
- **Current Phase 7.2 SHA-256:** `f2d652d0c4a22d8dc30b65da78185b617446f7c41d388d68669f2a7fba47bf13`.
- **Current Phase 7.2 size:** 493 lines; 20,431 bytes.
- **Current Phase 7.4 SHA-256:** `df06b22a1185543db17693b1725dda980f42aa8332f6a6328c3d34469d5c7108`.
- **Current Phase 7.4 size:** 496 lines; 20,606 bytes.
- **Reconciliation status:** rebuilt locally in Phase 7; final consistency review,
  approved commit and push remain pending.

#### Exact local preservation archive

- **Path:** `docs/ARCHIVE/PROJECT_STATE_FULL_2026-08-06.md`.
- **Source type:** immutable preservation copy of the Phase 2 source state.
- **Repository status:** local preservation evidence; untracked and explicitly
  excluded from the proposed Git commit.
- **Snapshot date:** 6 August 2026.
- **Authority level:** 5 as preservation evidence; it does not supersede the active
  operational file.
- **Material covered:** byte-for-byte contents of `docs/PROJECT_STATE.md` at HEAD
  `1601ae48be281153e5dd4af0eee0889a26835162`.
- **SHA-256:** `6ab1a3a70be61cbeaca38301a59ef1ddb846231a39be9642cea7310b5ac7faaf`.
- **Size:** 25,597 lines; 997,716 bytes.
- **Privacy limitation:** contains inherited personal email and private local-path
  material and is not suitable for repository publication.
- **Exclusion decision:** must remain unchanged locally and must not be staged or
  committed.
- **Reconciliation status:** preserved and verified byte-for-byte; privacy-safe
  derivative registered below.

#### Privacy-safe repository archive

- **Path:** `docs/ARCHIVE/PROJECT_STATE_REDACTED_2026-08-06.md`.
- **Source type:** privacy-redacted repository historical archive derived from the
  exact local preservation copy.
- **Repository status:** newly created and intended for the documentation commit.
- **Snapshot date:** 6 August 2026; privacy-safe derivative created in Phase 7.2.
- **Authority level:** 5 as repository historical evidence; it does not supersede
  the current operational file.
- **SHA-256:** `5ffe2390f172ea488ad5b781fa049b4e424ddf981e7d42197c1663006945a6e7`.
- **Size:** 25,602 lines; 997,606 bytes.
- **Redactions:** 23 `[REDACTED_EMAIL]` markers, 10
  `[REDACTED_LOCAL_PATH]` markers and no `[REDACTED_SECRET]` marker because no
  actual secret assignment was detected.
- **Limitations:** not byte-identical to the exact archive; explicit redaction
  markers replace privacy-sensitive values while headings, chronology and
  historical meaning remain preserved.
- **Reconciliation status:** privacy-safe repository copy prepared locally;
  final review and approved commit/push remain pending.

#### Proposed archive commit membership

- **Include:** `docs/ARCHIVE/PROJECT_STATE_REDACTED_2026-08-06.md`.
- **Exclude:** `docs/ARCHIVE/PROJECT_STATE_FULL_2026-08-06.md`.
- **Staging safeguard:** stage the redacted file by its exact path; do not stage the
  archive directory recursively.

### Earlier operational-state snapshots

#### `docs/PROJECT_STATE.md.bak_20260716_2231`

- **Source type:** local state backup.
- **Repository status:** ignored by the `*.bak_*` rule and not tracked.
- **Date range:** material accumulated through 16 July 2026.
- **Authority level:** 5.
- **Material covered:** earlier consolidated operational and historical state.
- **SHA-256:** `2a3f2b3cc8f7a9b7c9d6497afaf0259ad4994ac0f10a7395aba36cf283c45adb`.
- **Size:** 20,487 lines; 768,501 bytes.
- **Limitations:** predates later July and August work; filename timestamp is local
  provenance rather than proof of production state.
- **Reconciliation status:** inventoried; comparison with the full Phase 2 snapshot
  remains part of historical reconstruction.

#### `docs/PROJECT_STATE.md.bak_pre_july_merge_20260716`

- **Source type:** pre-July-merge local state backup.
- **Repository status:** ignored by the `*.bak_*` rule and not tracked.
- **Date range:** earlier project history through the pre-merge checkpoint on
  16 July 2026.
- **Authority level:** 5.
- **Material covered:** an earlier branch/subset of project state.
- **SHA-256:** `dd27ceb6f653825775da1f8a4425b9ef9e44c65333687267038caaca7c9ceede`.
- **Size:** 3,279 lines; 158,731 bytes.
- **Limitations:** incomplete relative to both the later July backup and current
  state; ignored and therefore not durable Git history.
- **Reconciliation status:** inventoried; retain until section-level preservation is
  demonstrated.

### Engineering and QA records

#### `docs/HISTORY/ENGINEERING_LOG_JULY_2026.md`

- **Source type:** curated engineering history and handover.
- **Repository status:** tracked.
- **Date range:** principally July 2026, with appended milestones through 4 August
  2026.
- **Authority level:** 5.
- **Material covered:** Version 1 completion, newsletter, Admin and Manual Review,
  security, analytics, metadata, mobile work and Editorial Similarity Phases 2A/2B.
- **SHA-256:** `e1c505af4892fdd8fdd1052b60e6814d4f79123c8e8a8113087570878a429270`.
- **Size:** 1,140 lines; 58,519 bytes.
- **Limitations:** filename understates its August coverage; later production
  investigations may post-date it.
- **Reconciliation status:** inventoried; retain unchanged and reconcile into the
  future engineering-history master.

#### `docs/QA/QA_REPORT_2026-07-29.md`

- **Source type:** dated post-release QA report.
- **Repository status:** tracked.
- **Audit date and baseline:** 29 July 2026 at commit `2bcdf5c`.
- **Authority level:** 5.
- **Material covered:** public, Admin, security, tests, crawler/SEO, newsletter,
  social publishing, performance and memory findings.
- **SHA-256:** `c4d526c94edb85806450c4f998483ae1be34e2f6385844bfcd871a08e4860154`.
- **Size:** 580 lines; 27,443 bytes.
- **Limitations:** several findings were addressed by later commits; the report must
  remain an unchanged historical baseline while later outcomes are linked.
- **Reconciliation status:** inventoried and reconciled locally in the Phase 5 QA
  records; final consistency review and commit remain pending.

### Entry-point and workflow records

#### `docs/PROJECT_MASTER.md`

- **Source type:** permanent first-read project index and governance record.
- **Repository status:** intentional untracked file rebuilt locally; pending approved
  commit and push.
- **Date range:** prepared and rebuilt in August 2026.
- **Authority level:** 4 for local documentation governance after Phase 6.
- **Material covered:** governance, project identity, architecture, strategy, QA,
  roadmap, operating rules and documentation index.
- **Phase 6 replacement baseline SHA-256:** `6f71c4e7fbe14ae0e865ee2b275fa279bbdf51b0bb4fc22ce65413fba2da4eee`.
- **Phase 6 replacement baseline size:** 889 lines; 37,257 bytes.
- **Current Phase 7.1 SHA-256:** `41c6bfa87e956ce7d4df91aeda036b3ad3275a18f56a56ea44a12b7269c531b6`.
- **Current Phase 7.1 size:** 895 lines; 37,970 bytes.
- **Current Phase 7.2 SHA-256:** `05c5a220d8a88d9689f281a784127114b0e2c32dc52f4c71e2f266d1c6fb6943`.
- **Current Phase 7.2 size:** 900 lines; 38,303 bytes.
- **Current Phase 7.4 SHA-256:** `655897ea59bb3423be0e35a9a4a1a1d6e54f66bbb516a7184099dbfcc579327c`.
- **Current Phase 7.4 size:** 902 lines; 38,464 bytes.
- **Limitations:** repository-wide authority awaits final review and the approved
  documentation commit and push; mutable production facts still require verification.
- **Reconciliation status:** rebuilt locally in Phase 6 and synchronised after
  Phase 7; commit and push remain pending.

#### `AGENTS.md`

- **Source type:** repository operating instructions.
- **Repository status:** intentional untracked file.
- **Date range:** current local workflow guidance as of Phase 2.
- **Authority level:** 4 for repository work practices, subject to higher-level
  system and user instructions.
- **Material covered:** startup checks, safe production workflow, project layout,
  tests, style, Git and security rules.
- **SHA-256:** `3be32212dd0a429041c4d22599069790851afe994bfc4fd97de0821b0c537adc`.
- **Size:** 65 lines; 4,308 bytes.
- **Limitations:** intentionally local/untracked; not itself historical project
  evidence.
- **Reconciliation status:** registered and preserved unchanged.

#### Root `README.md`

- **Source type:** repository README.
- **Repository status:** tracked.
- **Authority level:** 8.
- **Material covered:** only the heading `Here are your Instructions`.
- **SHA-256:** `4d98a881426d611841978ecdc7192d83446a2191081b08776b94c39019ccda1f`.
- **Size:** 1 line; 29 bytes.
- **Limitations:** provides no usable Cheshire Today onboarding or architecture.
- **Reconciliation status:** inventoried as stale/incomplete; no Phase 2 change.

#### `frontend/README.md`

- **Source type:** generated Create React App README.
- **Repository status:** tracked.
- **Authority level:** 8 for project-specific operations; level 6 as framework
  background.
- **Material covered:** generic CRA development, test and build commands.
- **SHA-256:** `70eafbc7a5fd466aa3213b5a7e1b2a41383cbe5d4e6fc5f4582efc58bdb509d1`.
- **Size:** 70 lines; 3,359 bytes.
- **Limitations:** generic and includes `npm start`, which repository instructions
  prohibit unless explicitly requested.
- **Reconciliation status:** inventoried as framework boilerplate; unchanged.

### Chat and agent-history sources

#### `docs/HISTORY/CHAT_HISTORY_AUGUST_2026.md`

- **Source type:** reserved August ChatGPT-history file.
- **Repository status:** intentional untracked file.
- **Date range:** intended for August 2026.
- **Authority level:** 8.
- **Material covered:** none; the file is empty.
- **SHA-256:** `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- **Size:** 0 lines; 0 bytes.
- **Limitations:** must not be described as reconciled history.
- **Reconciliation status:** pending source material.

#### Pending ChatGPT export

- **Source type:** external conversation export requested by the project owner.
- **Repository status:** not received and not present in the repository.
- **Authority level:** 7 before reconciliation.
- **Material covered:** potentially relevant project discussions, decisions and
  evidence mixed with unrelated projects.
- **Limitations:** unknown completeness; Cheshire Today conversations must be
  separated from unrelated property, trading, travel, estate-management, Bose,
  Philippines and other material.
- **Reconciliation status:** pending receipt; no reconstruction-complete claim is
  permitted.

#### Pending Codex history integration

- **Source type:** Codex task records and investigation outputs.
- **Repository status:** not systematically preserved under `docs/HISTORY/CODEX/`.
- **Authority level:** 7 before reconciliation, with individual production evidence
  assessed under level 2 when independently verified.
- **Material covered:** code reviews, implementations, tests, production checks,
  incidents and decisions from recent engineering tasks.
- **Limitations:** distributed across tasks; latest production investigations may
  post-date repository HEAD.
- **Reconciliation status:** pending Phase 9 collection and evidence review.

### Brand and commercial records

#### `docs/brand-assets/`

- **Source type:** brand guidelines, README records and approved social asset
  masters.
- **Repository status:** tracked, apart from local `.DS_Store` files.
- **Date range:** principally July 2026.
- **Authority level:** 4 for approved brand-asset contracts; 5 for dated rollout
  history.
- **Material covered:** logo, colour, typography, accessibility, Instagram,
  Facebook, Threads, Stories, Feed, Reels and Highlight assets.
- **Limitations:** asset guidance does not establish deployment or current social
  platform behaviour without code/production verification.
- **Reconciliation status:** inventoried; retain in place and link from future brand,
  social and master records rather than duplicating it.

#### `docs/commercial-gap-map/`

- **Source type:** dated monetisation-cleanup records and commercial-guide payloads.
- **Repository status:** tracked.
- **Date range:** April 2026.
- **Authority level:** 5 for dated work; 6 for commercial strategy inputs.
- **Material covered:** authority-page affiliate labelling, finance/utility cleanup
  and payroll, insurance and tax guide payloads.
- **Limitations:** does not prove current publication, programme approval or live
  monetisation state.
- **Reconciliation status:** inventoried; retain originals and reference them from
  future monetisation architecture and history.

### Historical PDF references

#### `CheshireToday_Project_History.pdf`

- **Source type:** one-page historical project PDF.
- **Repository status:** tracked at repository root.
- **Authority level:** 6.
- **Material covered:** historical project summary.
- **SHA-256:** `e841f12f03cc8ff095cb7d6081f98ef95a35b8ce2848271ea290ef4be6ab5312`.
- **Size:** 1,369 bytes; PDF 1.3, one page. Line count is not a meaningful PDF
  content measure.
- **Limitations:** not identified by `PROJECT_STATE.md` as current operational
  authority and not yet reconciled against repository history.
- **Reconciliation status:** registered; content reconciliation pending.

#### PDFs named in `docs/PROJECT_STATE.md`

- **Identifiers:** `Cheshire_Economic_AI_Project_Master_Feb2026.pdf`, `report.pdf`,
  `report 2.pdf` and `report 3.pdf`.
- **Source type:** historical strategy, competitor analysis and website-assessment
  references.
- **Repository status:** referenced by `PROJECT_STATE.md` but not present in the
  current repository checkout.
- **Date range:** February 2026 or earlier audit period as described by the state
  record.
- **Authority level:** 6 when supplied and verified; otherwise 8.
- **Material covered:** high-level strategy and historical research, not current
  implementation.
- **Limitations:** unavailable for Phase 2 hashing or direct reconciliation. The
  state record says `report 2.pdf` and `report 3.pdf` were byte-identical, but that
  claim has not been independently rechecked here.
- **Reconciliation status:** pending source recovery; never use the February master
  as current operational truth.

## Git history source record

- **Repository:** `CT29january26-new-website-migration`.
- **Current branch:** `full-scrape-prod`.
- **Current HEAD:** `1601ae48be281153e5dd4af0eee0889a26835162` —
  `Record Editorial Similarity deployment state`, dated 4 August 2026.
- **First known commit:** `789e9c8a39ff947b21ef01d15d2aba07e95fee7f` —
  `Initial commit for Render deployment`, dated 1 February 2026.
- **Commit count reachable from current HEAD:** 943.
- **Commit count across all refs established in Phase 1:** 949. The six-commit
  difference is branch/ref history not reachable from the current HEAD and is
  retained as historical evidence.

### Monthly totals reachable from current HEAD

| Month | Commits |
| --- | ---: |
| February 2026 | 203 |
| March 2026 | 160 |
| April 2026 | 139 |
| May 2026 | 224 |
| June 2026 | 25 |
| July 2026 | 177 |
| August 2026 through HEAD | 15 |
| **Total** | **943** |

### Monthly totals across all refs established in Phase 1

| Month | Commits |
| --- | ---: |
| February 2026 | 209 |
| March 2026 | 160 |
| April 2026 | 139 |
| May 2026 | 224 |
| June 2026 | 25 |
| July 2026 | 177 |
| August 2026 through inventory | 15 |
| **Total** | **949** |

### Relevant branches

- `full-scrape-prod`
- `main`
- `backup-before-rollback`
- `safety-before-saturday-restore-20260525`
- `homepage-spec-v1`
- `monetisation`
- `monetisation-advertise-route`
- `niche-silos`

Corresponding remote refs exist for all listed branches except the local safety
branch. Branch names are historical evidence and do not establish current
deployment, approval or production behaviour.

### Relevant tags

- `LAYOUT_STABLE_2026_02_22`
- `UI_LAYOUT_SOURCE_STABLE_2026_02_22`
- `layout-lock`
- `newsletter-security-v1.0`
- `pre-editorial-filter`
- `stable-api-clean`
- `v1-stable-data`

Tag names record intended checkpoints; they are not automatic current-state or
deployment claims. Commit contents and production evidence must be inspected before
using a tag operationally.

### Git-history coverage and limitations

Git is the durable source for implementation sequence, reversals, tests and
documentation changes. Commit messages alone do not prove deployment, production
verification or continued activation. Reverted commits, branch-only work and later
corrections must be represented explicitly in historical records.

## Pending and unreconciled sources

The following gates remain open:

1. The ChatGPT export has been requested but not received.
2. `docs/HISTORY/CHAT_HISTORY_AUGUST_2026.md` is empty.
3. Codex investigations have not been systematically preserved or reconciled.
4. Historical PDFs referenced by `PROJECT_STATE.md` are not present in the current
   checkout and have not been directly reconciled.
5. The tracked `CheshireToday_Project_History.pdf` remains a historical source whose
   content has not yet been reconciled.
6. Latest production investigations may post-date repository HEAD and must be
   recorded only from preserved, timestamped evidence.
7. The ignored July state backups have not yet received section-level comparison
   against the full Phase 2 snapshot.
8. QA findings have been reconciled locally against repository evidence; final
   consistency review and the approved documentation commit remain pending.

The full historical reconstruction must not be marked complete until these sources
have been obtained where possible, reconciled, reviewed and reflected in the
repository-backed master records.

## Phase status

- **Phases 1–7.3:** completed locally, including preservation, source registration,
  history, architecture, operations, QA, roadmap, Project Master and concise Project
  State reconstruction, privacy-safe archiving and clean-checkout-safe archive-link
  correction.
- **Authority synchronisation:** active locally through this correction pass.
- **Archive privacy/preservation decision:** completed locally; exact archive is
  excluded and the privacy-safe derivative is the proposed repository archive.
- **Final review, commit and push:** pending.
- **Historical reconstruction:** incomplete while ChatGPT, structured Codex,
  historical PDF and post-HEAD production evidence remain unreconciled.
