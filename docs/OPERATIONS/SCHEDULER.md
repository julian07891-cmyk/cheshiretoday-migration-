# Cheshire Today — Scheduler Operations

> **Reconstruction status:** Job definitions and guards reflect current HEAD; live enablement requires environment and logs.

## Document purpose

Document current APScheduler jobs, ownership, locks and safe observation.

## Authority and evidence

Primary evidence: startup and job functions in `backend/server.py`, `render.yaml`, `tests/test_scheduler_lock.py`, `tests/test_admin_generation_operations_auth.py`, and `tests/test_article_generation_memory_observability.py`. See [Source Register](../HISTORY/SOURCE_REGISTER.md).

## How to use this document

Use it to predict normal run windows and distinguish configured code from a confirmed live run. Do not manually trigger routine QA.

## Startup conditions

Jobs are configured during FastAPI startup. The scheduler starts only if `AUTO_GENERATION_ENABLED` parses true and `HOSTNAME` is non-empty and not `unknown`. No clock-time or thread-name inference enables Editorial Similarity. The Render warmup cron only calls health and does not own these jobs.

## Current job schedule

All listed times use `Europe/London`:

| Job ID | Callable | Schedule | Purpose |
|---|---|---|---|
| `morning_article_generation` | `daily_article_generation(12)` | 06:00 daily | Scheduled hybrid article run |
| `midday_article_generation` | `daily_article_generation(12)` | 12:00 daily | Scheduled hybrid article run |
| `evening_article_generation` | `daily_article_generation(12)` | 18:00 daily | Scheduled hybrid article run |
| `daily_brief` | `send_scheduled_news_digest` | Mon–Sat 07:30 | Daily Brief |
| `weekly_roundup_batch_1`…`4` | `send_weekly_roundup_email` | Sun 09:00, 10:00, 11:00, 12:00 | Safe roundup batches |

Commented legacy digest schedules and disabled Facebook queue processing are not active jobs.

## Locks and ownership

Article generation uses `scheduler_locks` with an hourly key, owner instance, timestamp and two-hour expiry/stale takeover. Digest flows use date/batch-specific locks and persisted logs/cursors to reduce duplicate sends. Current `scheduler.add_job` calls use stable IDs and `replace_existing=True`; no explicit `max_instances` is set in these calls, so do not claim a non-default value.

## Duplicate prevention

Scheduler locks prevent concurrent job ownership; article Version 1 checks and Mongo unique indexes prevent duplicate content at later boundaries. Newsletter digest locks/log records and rotating cursors prevent repeated slot delivery. These controls are complementary, not interchangeable.

## Stale-lock handling

Article generation may take over a lock older than two hours or past `expires_at`. Successful completion deletes its lock. Failure paths and process exits can leave state for stale takeover; inspect the exact lock/job logs before intervening.

## Safe observation workflow

1. Convert London schedule to Render UTC for the date.
2. Capture start, lock, memory/import/send logs and completion.
3. Verify health and no restart for an appropriate post-run window.
4. Confirm output read-only in Admin/public surfaces.
5. For similarity, observe normal runs only and collect bounded advisory fields.

## Protected boundaries

Do not trigger imports or sends for ordinary QA, delete locks, edit job times, enable local schedulers, or change hostname/enablement variables without explicit production approval. Preserve lock semantics and startup-generation disablement.

## Known limitations

APScheduler runs inside the web process and depends on eligible process topology. Article lock acquisition exceptions currently warn and continue, making database/lock observability important. Committed schedules do not prove a particular run executed.

## Related documents

[Article Pipeline](../ARCHITECTURE/ARTICLE_PIPELINE.md), [Newsletter](../ARCHITECTURE/NEWSLETTER.md), [Render](RENDER.md), [Monitoring](MONITORING.md), and [Newsletter Operations](NEWSLETTER_OPERATIONS.md).
