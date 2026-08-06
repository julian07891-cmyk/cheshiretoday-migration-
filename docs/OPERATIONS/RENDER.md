# Cheshire Today — Render Operations

> **Reconstruction status:** Current committed Render topology at HEAD; live service settings require Render evidence.

## Document purpose

Explain service ownership, startup, health, scheduler and safe incident investigation on Render.

## Authority and evidence

Primary evidence: `render.yaml`, `render_build.sh`, startup/shutdown code in `backend/server.py`, and scheduler/memory tests. See [Source Register](../HISTORY/SOURCE_REGISTER.md).

## How to use this document

Use it to interpret deployments and logs before taking action. Pair with [Deployment](DEPLOYMENT.md) and [Monitoring](MONITORING.md).

## Committed service topology

`render.yaml` declares a Python web service named `cheshiretoday` and a separate cron service named `cheshiretoday-backend-warmup`. The cron runs every ten minutes and performs a read-only request to the public `/api/health` endpoint. It is a warmup/health caller, not the owner of article or newsletter scheduling.

The web service builds through `render_build.sh` and starts one Uvicorn command from `backend/`. FastAPI owns APIs, SPA hosting and, when guarded conditions pass, the APScheduler instance. Cloudflare may sit in front of the public hostname, but edge configuration is external to this repository.

## Startup sequence

FastAPI startup provisions required indexes with guarded error handling, leaves deploy-triggered content generation disabled, configures scheduled jobs, then starts the scheduler only when `AUTO_GENERATION_ENABLED` is true and `HOSTNAME` is present and not `unknown`. Shutdown attempts scheduler shutdown and closes the Mongo client.

## Health endpoint

`GET /api/health` reports service/database status according to current backend code. A 200 response proves endpoint availability at that moment, not provider, scheduler or every database workflow.

## Scheduler ownership

The scheduler belongs to the eligible web process, not the warmup cron. Article and digest jobs also use Mongo locks. Multiple eligible web processes would increase scheduler risk, so hostname/enablement logs and lock outcomes must be inspected.

## Memory and restart interpretation

Article generation logs twelve `article_generation_memory` phases. Treat rising RSS, missing completion, process restart, SIGKILL/exit 137, OOM or post-job Bad Gateway as incident evidence. Compare like-for-like normal runs; do not optimise from a single transient reading.

## Safe log investigation

1. Fix the exact UTC/local-time window and deployed commit.
2. Capture job start, lock, pool load, import phases, memory markers, cleanup and completion.
3. Search at least the relevant post-job window for 5xx, traceback, restart and OOM evidence.
4. Redact tokens, addresses, raw payloads and subscriber/article-view details.
5. Correlate with health and read-only Admin state before concluding.

## Actions to avoid before evidence

Do not restart, redeploy, change plan/configuration, trigger imports, run cleanup, modify schedules or repair MongoDB merely because a log line looks unusual. Do not treat the committed plan declaration as verified current billing tier.

## Protected boundaries

Preserve the normal build/start commands, scheduler guard, distributed locks, disabled startup generation and read-only warmup role.

## Known limitations

Render dashboards and environment values are external. In-process scheduling remains sensitive to process topology. Health probes can succeed while a provider or subsection is degraded.

## Related documents

[Architecture Master](../ARCHITECTURE_MASTER.md), [Deployment](DEPLOYMENT.md), [Monitoring](MONITORING.md), [Scheduler](SCHEDULER.md), and [Production Timeline](../PRODUCTION_TIMELINE.md).
