# Cheshire Today — Article Pipeline

> **Reconciliation baseline:** `b83d2c3e4932a9870555b156a4c7e774eed8d226`, 5 October 2026. Deployment/health verified at the 4 October observation; new-source natural-run acceptance pending. Source/provider availability remains environment-dependent.

## Document purpose

Trace current article processing from scheduled discovery to reader-facing consumption and identify authoritative versus advisory controls.

## Authority and evidence

Primary evidence: `backend/server.py` symbols `daily_article_generation`, `_generate_articles_internal`, `_import_hybrid_news_internal`, `_remove_duplicates_internal`, `cap_visible_articles`, `apply_ai_manual_review_guard`; `backend/app/editorial_similarity_shadow.py`; importer, scheduler, Manual Review, duplicate and memory tests. See [Source Register](../HISTORY/SOURCE_REGISTER.md).

## How to use this document

Use the sequence below before changing imports, visibility or cleanup. Validate the nearest tests first and preserve the protected controls.

## Current processing sequence

1. APScheduler invokes `daily_article_generation(count=12)` at configured London-time slots.
2. The job records memory, acquires a Mongo `scheduler_locks` lease keyed by date/hour, then calls `_generate_articles_internal` with `public_import_limit=6` and Editorial Similarity shadow explicitly enabled.
3. `_generate_articles_internal` calls `_import_hybrid_news_internal`. Existing active/archived title, source-URL and related Version 1 identity sets are built before insertion work.
4. Feed discovery and parsing process category RSS and Local RSS inputs; concurrency is bounded in current importer code. Perplexity may research or expand eligible items when configured and within budget.
5. Category, locality, age, content-length, source, crime/filler, AI-refusal and other editorial guards determine rejection, public eligibility or Manual Review routing.
   For scheduled hybrid/category RSS imports, raw continuation-ended preview
   evidence is classified before sanitisation. HTML cleaning preserves block
   boundaries and normalises line endings; only supported terminal continuation
   markers are removed. A known incomplete fallback is routed to hidden Manual
   Review and cannot be made public merely by `manual_review_without_ai`.
6. Four scheduled insertion contexts use the shared insert wrapper: `category_rss`, `local_rss_manual_review`, `local_rss`, and `cheshire_fallback`.
7. Version 1 checks and article construction complete before the Phase 2B shadow comparison. Similarity never changes the insert decision.
8. Successful inserts update the bounded same-run shadow corpus; a bounded advisory log is attempted after insertion.
9. `cap_visible_articles(keep=100)` applies the current visible-pool policy. Scheduled generation then runs `_remove_duplicates_internal` for duplicate/short-content cleanup. Automatic age-based hard deletion is disabled.
10. Public queries exclude archived and `manual_review_hidden_from_public` records. Homepage/article APIs, newsletter selection and social tools consume eligible stored articles.

## Manual Review and editorial authority

### Local discovery is not publication eligibility

Dedicated `fetch_local_feeds_only()` discovery combines Cheshire Live first,
other configured Local feeds (including enabled Cheshire East releases) next,
then bounded Nub coverage. Existing title deduplication and newest-first ordering
within groups remain; the result is not a global date-only merge.

- Nub News: Macclesfield, Sandbach, Congleton, Nantwich, Crewe, Alsager, Chester
  and Wilmslow. The coverage selector retains at most three newest candidates
  per hub before downstream eligibility; it does not allocate publication slots.
- Cheshire East Media Hub: index-derived release candidates are sorted newest
  first; the production call uses the default maximum of five release-page
  fetches. The helper has an explicit `max_articles` parameter, not a universal
  hard ceiling of five for every possible caller. Index/article failures fail
  safely; incomplete parsed records are skipped. No town `location` or
  `priority_location` is invented.
- Both constructor flags default to false on ordinary `NewsFeedService()`
  instances. The global production service explicitly sets `enable_nub_news=True`
  and `enable_cheshire_east_media_hub=True`. This prevents ordinary test instances
  from acquiring new network dependencies; tests exercising the enabled global
  path still require mocked discovery.

All discoveries remain subject to image, duplicate, freshness, safety, usefulness
and downstream locality/editorial checks. Source branding is not a locality
guarantee and adding sources does not relax those checks.

The bounded `has_conflicting_local_location_detail` helper catches the confirmed
Heswall/Wirral Council/Chester Road ambiguity only when independent locality
evidence is absent. Metadata is a hint, not sufficient to rescue the road-only
match. Suitable source-stage candidates enter the existing hidden-review queue
before generation/topic accounting, with `locality_ambiguous_out_of_area`.
The final locality guard uses the same helper when conflict emerges in body text.
This is neither a general road-name ban nor a UK-town blacklist. Early review
does not consume Local target/topic/public counts; final hidden review retains
the existing Local/topic counting semantics but does not consume a public slot.
Existing stronger rejection/archive controls remain authoritative.

Category RSS also routes the narrowly matched dated Guardian politics-liveblog
URL format to hidden review before generation (`113c150`). That category path
retains its established retained-record target accounting, distinct from the
early Local queue. Neither rule is a new scheduler or fallback architecture.

### Reporting depth and display excerpts are separate

`41444da` provides conditional source-led guidance: usually 400–650 words with
adequate verified evidence, potentially 700–900 for substantial reports, shorter
when evidence is thin. The ranges are not quotas. Corroboration cannot override
or conflate the primary story without evidence; invention, repetition and generic
filler are prohibited. First/retry provider parameters and empty/refusal retry
conditions remain unchanged. Non-empty short output returns to the importer;
the existing 1,000-character and editorial gates own public routing.

`b98a49e` adds deterministic `select_rss_excerpt`: clean full source text, select
complete source-supported sentences to a soft size target, otherwise use available
detailed body sentences or return empty. It makes no AI request or hard sentence/
word cut. Display summaries are selected after existing editorial decisions;
raw source remains available to incomplete-preview classification. Relevant card
and article-intro surfaces use stored summaries without another hard substring
preview. Historical stored excerpts are not automatically repaired.

Manual Review is a hidden editorial state represented by fields such as `manual_review_hidden_from_public`, `verification_status`, `rewrite_status` and `archive_reason`. Backend update safeguards decide whether a reviewed update can return live. OpenAI review is Admin-only and draft/review-only; it is not an automatic publisher.

## Duplicate and visibility controls

Version 1 normalised-title/source-URL checks, batch sets, active and archived snapshots, Mongo unique indexes and `DuplicateKeyError` handling remain authoritative. Image checks apply in contexts where current code uses them. Editorial Similarity is advisory only. The public import cap is six in the scheduled request; further eligible candidates can be routed to Manual Review rather than silently published.

## Memory-heavy phases

`9bf8877` implemented streamed visible-pool planning state; it is not pending
implementation. This does not establish a measured memory gain or close the wider
OOM/resource gate. Scheduled locks, six-public-slot limit and cleanup semantics
remain separate protected controls.

`log_article_generation_memory` marks job start, lock, existing-record indexing, feed completion, source-group processing, visible-pool cap, two cleanup reads and completion. Feed materialisation, 10,000-record identity projections, provider responses and cleanup reads are the main evidenced retention points. See [Monitoring](../OPERATIONS/MONITORING.md).

## Failure-safe behaviour

Generation and cleanup errors are caught separately so the scheduler process can continue. Similarity pool/scorer/log failures fail open and do not retry insertion. Mongo uniqueness remains the last deterministic duplicate barrier. Article scheduler-lock acquisition errors fail closed and skip generation; database lock health remains operationally important.

## Tests

New-source/locality coverage includes `test_locality_ambiguity.py`,
`test_nub_news_adapter.py`, `test_cheshire_east_media_hub_adapter.py`,
`test_perplexity_article_content.py` and `test_rss_excerpt.py`. Supplied combined
pre-deployment regression evidence is 226 passed/six known warnings, not a new
test run or proof of natural production acceptance. See
[Engineering History](../HISTORY/ENGINEERING_HISTORY_MASTER.md).

Relevant coverage includes `tests/test_scheduler_lock.py`, `tests/test_sync_rss_editorial_guard.py`, `tests/test_local_rss_manual_review_routing.py`, `tests/test_article_generation_memory_observability.py`, `tests/test_editorial_similarity_shadow_runtime.py`, RSS preview/body-quality regressions, and Version 1 duplicate/import regressions. The `bbc526c` gate recorded 44 focused tests, 130 importer/Manual Review/scheduler tests with 12 skipped, and 104 memory/similarity-isolation/cleanup tests.

## Protected boundaries

Do not alter Version 1 order, public caps, Manual Review rules, one-insert semantics, cleanup policy, scheduler locks or provider role as part of similarity calibration.

## Known limitations

The importer remains a large multi-context function. Cleanup can remove records after insertion under existing duplicate/short-content rules. Provider and feed quality vary. The scheduled hybrid/category RSS path now protects known continuation-ended previews, but `/api/import-real-news` was not broadened or production-tested by `bbc526c`. Five pre-deployment Guardian records remain a separate editorial-repair issue. A natural continuation-ended source receiving a genuinely distinct complete public replacement has not yet been observed. Shadow evidence needs multiple normal scheduled runs before thresholds or UI work.

## Related documents

[Architecture Master](../ARCHITECTURE_MASTER.md), [Editorial Similarity](EDITORIAL_SIMILARITY.md), [Scheduler](../OPERATIONS/SCHEDULER.md), [Monitoring](../OPERATIONS/MONITORING.md), and [Editorial Evolution](../EDITORIAL_EVOLUTION.md).
