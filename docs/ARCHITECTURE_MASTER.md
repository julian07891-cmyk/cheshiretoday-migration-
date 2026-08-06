# Cheshire Today — Architecture Master

> **Reconstruction status:** Current-HEAD architecture reconstructed from repository code and configuration at `1601ae48be281153e5dd4af0eee0889a26835162`. Environment-dependent behaviour is labelled and requires production evidence.

## Document purpose

This is the concise index to Cheshire Today's current technical architecture and operating guides. It is not a history or a deployment-status assertion.

## Authority and evidence

Current code and committed configuration control this document: `backend/server.py`, `backend/app/`, `frontend/src/`, `render.yaml`, `render_build.sh`, and focused tests. See [Source Register](HISTORY/SOURCE_REGISTER.md). Historical context lives in [Engineering History Master](HISTORY/ENGINEERING_HISTORY_MASTER.md).

## How to use this document

Start here to locate a subsystem, then use its detailed architecture and operating guide before changing production behaviour.

## System map

```text
Browsers and crawlers
  -> Cloudflare/public hostname (environment-dependent edge)
  -> Render web service / Uvicorn / FastAPI
       -> /api routes -> MongoDB and external providers
       -> crawler HTML, sitemaps and robots
       -> built React SPA -> public pages and authenticated Admin

APScheduler (web-process owned when explicitly enabled)
  -> article discovery/rewrite/gates -> articles or Manual Review
  -> Editorial Similarity shadow logs (advisory only)
  -> Daily Brief / Weekly Roundup -> Resend or configured SMTP path

Readers -> first-party view/click/impression events -> MongoDB -> Admin analytics
Advertisers -> enquiry/checkout -> manual Admin review -> sponsored placements
```

## Architecture index

- [System overview](ARCHITECTURE/SYSTEM_OVERVIEW.md): component, API, data and trust boundaries.
- [Article pipeline](ARCHITECTURE/ARTICLE_PIPELINE.md): scheduled imports through reader surfaces.
- [Newsletter](ARCHITECTURE/NEWSLETTER.md): subscription, delivery, tracking and secure management.
- [Editorial Similarity](ARCHITECTURE/EDITORIAL_SIMILARITY.md): deterministic Phase 2A scorer and Phase 2B shadow integration.
- [Analytics](ARCHITECTURE/ANALYTICS.md): first-party, email, commercial and third-party analytics.
- [SEO and crawlers](ARCHITECTURE/SEO_AND_CRAWLERS.md): canonical identity, crawler HTML and discovery files.
- [Monetisation](ARCHITECTURE/MONETISATION.md): authority, affiliate, advertising and payment systems.
- [Deployment](OPERATIONS/DEPLOYMENT.md), [Render](OPERATIONS/RENDER.md), [Monitoring](OPERATIONS/MONITORING.md), [Scheduler](OPERATIONS/SCHEDULER.md), and [Newsletter operations](OPERATIONS/NEWSLETTER_OPERATIONS.md).

## Current boundaries

- Public React routes and Admin share a frontend bundle, but Admin APIs use `get_admin_auth`.
- MongoDB is the durable application store; code references the collections enumerated in the system overview.
- Perplexity participates in import research/rewrite paths; OpenAI review remains Admin-only and must never auto-publish.
- Manual Review is hidden from public queries and remains governed by backend safeguards.
- Version 1 deterministic duplicate controls remain authoritative; Editorial Similarity is scheduled-only and log-only.
- Newsletter provider, Stripe, Facebook, GA4 and scheduler activation depend on configuration; code capability is not proof that each is live.

## Protected boundaries

Do not weaken authentication, Manual Review, exact duplicate rules, subscriber security, crawler canonical rules, scheduler locking, or accessibility zoom. Do not trigger imports, sends or publishing merely to test a read-only claim.

## Known limitations

`backend/server.py` is a large shared entry point. The scheduler is process-owned, so its hostname and enablement guards matter. Mongo-backed operations and external providers can fail independently. The committed CORS middleware currently permits all origins and should be treated as a documented security limitation, not silently described as restricted.

## Related documents

[Project State](PROJECT_STATE.md) remains operational authority until its planned replacement. See also [Decision Register](DECISION_REGISTER.md), [Production Timeline](PRODUCTION_TIMELINE.md), and [Editorial Evolution](EDITORIAL_EVOLUTION.md).
