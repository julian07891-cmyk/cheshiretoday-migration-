# Cheshire Today — Article Pipeline

> **Reconstruction status:** Current pipeline reconstructed from code and tests at HEAD; source/provider availability remains environment-dependent.

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
6. Four scheduled insertion contexts use the shared insert wrapper: `category_rss`, `local_rss_manual_review`, `local_rss`, and `cheshire_fallback`.
7. Version 1 checks and article construction complete before the Phase 2B shadow comparison. Similarity never changes the insert decision.
8. Successful inserts update the bounded same-run shadow corpus; a bounded advisory log is attempted after insertion.
9. `cap_visible_articles(keep=100)` applies the current visible-pool policy. Scheduled generation then runs `_remove_duplicates_internal` for duplicate/short-content cleanup. Automatic age-based hard deletion is disabled.
10. Public queries exclude archived and `manual_review_hidden_from_public` records. Homepage/article APIs, newsletter selection and social tools consume eligible stored articles.

## Manual Review and editorial authority

Manual Review is a hidden editorial state represented by fields such as `manual_review_hidden_from_public`, `verification_status`, `rewrite_status` and `archive_reason`. Backend update safeguards decide whether a reviewed update can return live. OpenAI review is Admin-only and draft/review-only; it is not an automatic publisher.

## Duplicate and visibility controls

Version 1 normalised-title/source-URL checks, batch sets, active and archived snapshots, Mongo unique indexes and `DuplicateKeyError` handling remain authoritative. Image checks apply in contexts where current code uses them. Editorial Similarity is advisory only. The public import cap is six in the scheduled request; further eligible candidates can be routed to Manual Review rather than silently published.

## Memory-heavy phases

`log_article_generation_memory` marks job start, lock, existing-record indexing, feed completion, source-group processing, visible-pool cap, two cleanup reads and completion. Feed materialisation, 10,000-record identity projections, provider responses and cleanup reads are the main evidenced retention points. See [Monitoring](../OPERATIONS/MONITORING.md).

## Failure-safe behaviour

Generation and cleanup errors are caught separately so the scheduler process can continue. Similarity pool/scorer/log failures fail open and do not retry insertion. Mongo uniqueness remains the last deterministic duplicate barrier. A lock warning currently logs and continues, so database lock health is operationally important.

## Tests

Relevant coverage includes `tests/test_scheduler_lock.py`, `tests/test_sync_rss_editorial_guard.py`, `tests/test_local_rss_manual_review_routing.py`, `tests/test_article_generation_memory_observability.py`, `tests/test_editorial_similarity_shadow_runtime.py`, and Version 1 duplicate/import regressions.

## Protected boundaries

Do not alter Version 1 order, public caps, Manual Review rules, one-insert semantics, cleanup policy, scheduler locks or provider role as part of similarity calibration.

## Known limitations

The importer remains a large multi-context function. Cleanup can remove records after insertion under existing duplicate/short-content rules. Provider and feed quality vary. Shadow evidence needs multiple normal scheduled runs before thresholds or UI work.

## Related documents

[Architecture Master](../ARCHITECTURE_MASTER.md), [Editorial Similarity](EDITORIAL_SIMILARITY.md), [Scheduler](../OPERATIONS/SCHEDULER.md), [Monitoring](../OPERATIONS/MONITORING.md), and [Editorial Evolution](../EDITORIAL_EVOLUTION.md).
