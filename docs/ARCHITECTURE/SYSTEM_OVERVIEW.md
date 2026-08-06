# Cheshire Today — System Overview

> **Reconstruction status:** Current-code reconstruction at HEAD `1601ae4`; live configuration and provider availability are not inferred.

## Document purpose

Describe the present component, data and security boundaries without restating project history.

## Authority and evidence

Primary evidence: `backend/server.py`, `backend/requirements.txt`, `frontend/package.json`, `frontend/src/App.js`, `render.yaml`, `render_build.sh`, and current tests. Source authority is defined in [Source Register](../HISTORY/SOURCE_REGISTER.md).

## How to use this document

Use this to identify ownership before changing a route, collection, provider or deployment boundary. Follow subsystem links for detail.

## Major components

- **Frontend:** React 18 SPA built by CRACO. `frontend/src/App.js` defines public and Admin routing; `react-helmet-async` owners manage browser metadata.
- **Backend:** FastAPI application in `backend/server.py`, served by Uvicorn. `api_router` is mounted under `/api`; selected root routes serve crawler HTML and discovery files.
- **SPA host:** `render_build.sh` copies the production frontend into `backend/frontend_build`; FastAPI serves that bundle and applies the browser fallback.
- **Database:** Motor/PyMongo connects through the required `MONGO_URL`. MongoDB is used for articles, subscriber and operational state.
- **Background work:** APScheduler is configured inside the web process and starts only when its explicit environment and hostname guards pass.

## Frontend/backend boundary

Public pages call public `/api` endpoints. Admin UI is reached at `/admin`, while mutating and sensitive Admin endpoints depend on `get_admin_auth`. Secure newsletter management uses purpose-bound tokens/challenges rather than Admin authentication. Crawler requests may receive server-rendered HTML while ordinary browsers receive the SPA.

## MongoDB collections evidenced at HEAD

Direct `db.<collection>` references in `backend/server.py` include:

- content: `articles`, `archived_articles`, `authority_pages`, `affiliate_products`, `sponsored_placements`, `jobs`;
- newsletter: `subscribers`, `digest_log`, `email_analytics`, `email_batch_cursors`, `email_send_opportunities`;
- security/operations: `admin_tokens`, `scheduler_locks`, `system_flags`;
- commercial: `advertiser_leads`, `payment_transactions`;
- engagement/social: `article_views`, `comments`, `comment_likes`, `comment_sessions`, `comment_users`, `push_subscriptions`, `facebook_post_log`, `twitter_post_log`, `scheduled_facebook_posts`.

This is a code-reference inventory, not a claim that every collection contains live data.

## External services

Code supports MongoDB, Perplexity, OpenAI/LiteLLM, Resend, SMTP, Stripe, Facebook, web push, Cloudflare-facing public hosting, and third-party source feeds. Availability and credentials are environment-dependent; values must never enter documentation or logs.

## Authentication and trust boundaries

- Admin endpoints use token-based `get_admin_auth` and Mongo-backed `admin_tokens`.
- Public tracking and subscription endpoints validate and constrain caller input but are intentionally unauthenticated.
- Newsletter preference, unsubscribe and reactivation endpoints use signed/purpose-bound tokens, stored challenges, rate limits and replay controls.
- Stripe webhooks validate provider signatures where configured.
- The current CORS declaration is permissive (`allow_origins=["*"]`); that is a known current-code limitation.

## Public and Admin surfaces

Public surfaces include home, article, category, location, newsletter, guide, advertising and jobs routes. Admin covers articles, Manual Review, Archive, newsletter, advertising, analytics, affiliates and social-publishing helpers. Presence in code does not establish current operational enablement.

## Failure-isolation boundaries

Import sub-phases, similarity shadow evaluation, newsletter diagnostics, analytics subsections and provider sends have local error handling. This reduces cascading failure, but it does not make provider or database operations transactional as a whole. Article insertion remains separate from shadow logging.

## Protected boundaries

Preserve Admin authentication, Manual Review visibility filters, subscriber token rules, provider signature verification, scheduler locks, duplicate indexes and one-write import semantics.

## Known limitations

The large backend entry point couples many concerns. Environment state cannot be reconstructed from code alone. The in-process scheduler assumes a single eligible owner despite distributed locks, and permissive CORS deserves separate reviewed remediation.

## Related documents

[Architecture Master](../ARCHITECTURE_MASTER.md), [Article Pipeline](ARTICLE_PIPELINE.md), [Deployment](../OPERATIONS/DEPLOYMENT.md), [Render](../OPERATIONS/RENDER.md), and [Decision Register](../DECISION_REGISTER.md).
