# Cheshire Today — SEO and Crawler Architecture

> **Reconstruction status:** Current route and metadata behaviour reconstructed at HEAD; indexing outcomes and Search Console state remain external evidence.

## Document purpose

Describe canonical identity, rendered metadata, crawler-specific responses, discovery files and noindex boundaries.

## Authority and evidence

Primary evidence: crawler and sitemap routes in `backend/server.py`; `frontend/public/index.html`; Helmet owners in `frontend/src/components/` and `frontend/src/pages/`; canonical, sitemap and metadata tests. See [Source Register](../HISTORY/SOURCE_REGISTER.md).

## How to use this document

Consult it before changing article routes, metadata owners, sitemap filters, robots or crawler HTML. Browser DOM and direct crawler HTML are separate contracts.

## Canonical identity and routes

`_canonical_article_url` builds the canonical Mongo-ID plus slug article URL. Slugless and stale-slug routes redirect to current canonical identity where resolution succeeds. Query attribution and fragments are not part of canonical or `og:url` identity.

## Browser-rendered metadata

The static shell provides managed first-paint homepage metadata. `PublicMetadataDefaults` and production Helmet owners reconcile canonical, description, `og:url`, `og:type`, image and Twitter fields after hydration. Homepage owns the complete default set; article, category, location, newsletter and authority routes own their defined values. Admin, secure management and unsupported routes must not inherit homepage public metadata.

## Crawler-specific HTML

`_is_crawler_request` separates recognised search/social agents from ordinary browsers. Article crawler HTML contains canonical metadata, Open Graph/Twitter fields and `NewsArticle` JSON-LD. Hidden Manual Review or archived non-force-live articles receive noindex treatment. Category/location/home hubs, newsletter landing and authority guides have dedicated crawler responses where current routes support them.

## Public hubs and authority pages

React `CategoryPage` and `LocationPage` own browser metadata. Server hub HTML builds canonical links and index directives. Strong published authority pages can appear in the main sitemap; thin/stub guides are excluded and may be noindex.

## Sitemaps and robots

`generate_sitemap` serves `/sitemap.xml` and its API alias, with strategic filters, canonical article URLs and bounded last-modified dates. `generate_news_sitemap` serves recent eligible stories from the last 48 hours with additional editorial exclusions. `get_robots_content` serves root/API robots responses, disallows Admin and secure/private routes, and declares both sitemaps.

## Archived and unsupported content

Public queries exclude Manual Review and archived records except explicitly force-live legacy cases governed by current code. Unsupported browser routes use the existing SPA/404 noindex contract; they receive no homepage fallback metadata.

## Structured and social data

Articles use `NewsArticle`; authority pages use guide-appropriate structured data. Social metadata image selection remains separate from Editorial Similarity and duplicate rules. Social crawler routes do not justify exposing hidden content.

## Protected boundaries

Preserve Mongo-ID canonical identity, clean query-free canonical/OG URLs, hidden-content noindex, crawler/browser separation, robots declarations, sitemap filters and NewsArticle output. Do not request indexing as code validation.

## Known limitations

Crawler detection is user-agent based. Search engines decide indexing independently. Static first paint and settled browser DOM can differ transiently. Search Console representative sampling remains an operational investigation, not repository truth.

## Related documents

[Architecture Master](../ARCHITECTURE_MASTER.md), [Article Pipeline](ARTICLE_PIPELINE.md), [Monitoring](../OPERATIONS/MONITORING.md), and [Production Timeline](../PRODUCTION_TIMELINE.md).
