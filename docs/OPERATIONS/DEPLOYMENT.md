# Cheshire Today — Deployment Runbook

> **Reconstruction status:** Commands and checks derive from committed HEAD. Current Render settings and live deployment identity require direct verification.

## Document purpose

Provide a safe build, deploy and verification procedure without embedding credentials or assuming Git push equals deployment.

## Authority and evidence

Primary evidence: `render.yaml`, `render_build.sh`, `frontend/package.json`, `backend/requirements.txt`, `backend/server.py`, and current build/regression conventions. See [Source Register](../HISTORY/SOURCE_REGISTER.md).

## How to use this document

Use as a checklist with explicit production approval. Capture repository and production baselines before any mutation.

## Current deployment shape

- Production branch: `full-scrape-prod` by repository convention.
- Render web build command: `./render_build.sh`.
- Start command: `cd backend; uvicorn server:app --host 0.0.0.0 --port $PORT`.
- Build script installs backend requirements, runs `npm ci` and the frontend production build, then copies `frontend/build` into `backend/frontend_build`.
- FastAPI serves APIs, crawler/discovery responses and the copied SPA bundle.

## Environment categories

Required categories include Mongo connection/database, public/backend URLs, Admin authentication, scheduler enablement/hostname, provider credentials (Perplexity/OpenAI, Resend/SMTP, Stripe, Facebook), feature flags, newsletter signing/security and allowed operational caps. Record names only in reviewed configuration; never document values.

## Pre-deploy checklist

1. Read [Project State](../PROJECT_STATE.md), confirm branch/HEAD/status and preserve unrelated changes.
2. Review the exact diff and deployment implications.
3. Run focused tests, related regressions, Python compilation and frontend production build as applicable.
4. Run `git diff --check`; confirm no secrets, production data or generated build artefacts are included.
5. Confirm database migrations/index effects, scheduler effects, sends and content mutations are absent or explicitly approved.
6. Obtain approval for commit, push and Render deployment as separate actions.

## Build and deployment checks

Use project commands from `AGENTS.md`: `python3 -m pytest ...`, `npm --prefix frontend test -- --watchAll=false`, and `REACT_APP_BACKEND_URL=https://cheshiretoday.co.uk npm --prefix frontend run build` when appropriate. Do not run `npm start` for deployment verification. Render deployment is manual; verify the deployed commit in Render rather than assuming it from GitHub.

## Post-deploy verification

Confirm deployment success and startup logs, then `/api/health` or the current health alias returns HTTP 200. Verify the changed surface with settled browser/server evidence. For scheduler-sensitive changes, observe normal scheduled runs rather than triggering one. Search logs for traceback, 5xx, restart, OOM/SIGKILL, bundle failures and subsystem-specific errors.

## Rollback principles

Preserve evidence first. Prefer reverting the smallest deployment commit and redeploying through the normal path. Do not reset production data, delete collections, change environment variables or restart repeatedly without an approved incident plan.

## Protected boundaries

No deployment, restart, environment mutation, database repair, indexing request, send, import or publication occurs without explicit scope and approval.

## Known limitations

Committed `render.yaml` declares a service shape and plan, but does not prove live settings or current plan tier. Build success does not verify external providers, scheduler ownership or browser behaviour.

## Related documents

[Architecture Master](../ARCHITECTURE_MASTER.md), [Render](RENDER.md), [Monitoring](MONITORING.md), [Scheduler](SCHEDULER.md), and [Production Timeline](../PRODUCTION_TIMELINE.md).
