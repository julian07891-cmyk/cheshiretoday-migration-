# Cheshire Today — Monitoring Runbook

> **Reconstruction status:** Monitoring signals derive from current logging/routes at HEAD; retention and alerting configuration are environment-dependent.

## Document purpose

Define practical health, scheduler, import, newsletter, analytics and crawler evidence collection.

## Authority and evidence

Primary evidence: `backend/server.py`, `backend/app/editorial_similarity_shadow.py`, `backend/app/admin_analytics.py`, `backend/app/email_service.py`, and observability tests. See [Source Register](../HISTORY/SOURCE_REGISTER.md).

## How to use this document

Choose a bounded window, collect evidence before mutation, redact sensitive values, and compare with a known normal run.

## Health and deployment checks

- Verify deployed commit and deployment completion in Render.
- Check `/api/health` for HTTP 200.
- Search startup logs for index warnings, traceback, bundle/static failures and scheduler ownership messages.
- Continue observation after high-memory jobs to detect delayed restart or gateway failure.

## Article scheduler and import logs

Useful fixed strings include:

```text
Acquired article generation lock
Starting daily article generation
article_generation_memory
editorial_similarity_shadow_pool
editorial_similarity_shadow
Auto-cleanup after generation
Daily article generation process completed
```

With a downloaded/redacted log file, safe local searches include `/usr/bin/grep -n "article_generation_memory" app.log` and `/usr/bin/grep -nE "OOM|SIGKILL|exit 137|Bad Gateway|traceback|HTTP 5" app.log`. Do not paste secrets or personal data into commands or reports.

## Memory markers

Expect these ordered phases: `job_started`, `lock_acquired`, `existing_record_index_completed`, `all_feed_fetch_completed`, `uk_finance_processing_completed`, `local_feed_fetch_completed`, `local_processing_completed`, `business_tech_processing_completed`, `visible_pool_cap_completed`, `duplicate_cleanup_first_read_completed`, `duplicate_cleanup_second_read_completed`, `job_completed`.

Capture elapsed time and RSS at each phase, peak/final memory, and whether completion is followed by restart. Missing markers require code-path interpretation, not an invented value.

## Editorial Similarity observation

For enabled normal scheduled runs, record pool counts, comparison count (0–100), shortlist count (0–20), score/band, allow-listed reasons and provenance (`active`, `archived`, `same_run`). Confirm a bounded log attempt follows successful inserts and publication outcomes are unchanged. Observe at least three normal runs before threshold/UI work.

## Newsletter monitoring

Capture lock acquisition, eligible/batch counts, provider status, accepted counts, accepted-recipient ledger outcome, digest-log result and cursor progress. Never expose addresses, tokens or recipient hashes. Provider acceptance is not delivery or readership.

## Analytics verification

Use authenticated read-only summary requests sparingly for today/week/month. Record HTTP status, latency, response size and subsection availability. For controlled attribution, one ordinary event plus at most one deduplication reload is the normal ceiling and requires explicit scope.

## Sitemap and crawler checks

Smoke-check `/sitemap.xml`, `/news-sitemap.xml` and `/robots.txt` for 200 and valid content. Inspect direct crawler HTML for canonical, robots, Open Graph and structured data without requesting indexing or submitting sitemaps.

## Incident evidence capture

Record branch/HEAD, deployed commit, UTC and local times, request status, exact bounded log window, memory timeline, production-visible impact and what was not changed. Preserve pre-restart evidence. A minimum 30-minute post-job window is appropriate for memory/restart investigations; longer windows may be justified by the symptom.

## Escalation criteria

Escalate on repeated 5xx, failed health, missing completion with restart, OOM/SIGKILL, lock duplication, unexpected content mutation, subscriber-security failure, duplicate sends, privacy leakage or canonical/robots regression. A single provider timeout or shadow-scoring failure is monitored according to its fail-open contract.

## Protected boundaries

Monitoring is read-only by default. Do not trigger jobs, sends, imports, indexing, cleanup, restarts or database repairs to obtain evidence.

## Known limitations

Application logs are not a complete distributed trace. Render retention and edge logs are external. Browser/client events can fail silently or be affected by scanners and caching.

## Related documents

[Render](RENDER.md), [Scheduler](SCHEDULER.md), [Newsletter Operations](NEWSLETTER_OPERATIONS.md), [Editorial Similarity](../ARCHITECTURE/EDITORIAL_SIMILARITY.md), and [SEO and Crawlers](../ARCHITECTURE/SEO_AND_CRAWLERS.md).
