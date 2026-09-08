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

## Search Console canonical audit — 7 September 2026

The Search Console issue **Alternate page with proper canonical tag** remained in
`Validation Failed` state (validation started 16 July and failed 25 July), with
82 affected examples and a latest report update observed on 4 September 2026.
That validation state alone is not evidence of a current implementation defect.

Representative inspection classified the report as **MOSTLY HISTORICAL
ALTERNATE URLS — CURRENT IMPLEMENTATION HEALTHY**:

- current article identity is `/article/{Mongo _id}/{current-title-slug}`; the
  slug is deterministic and capped at 80 characters, and resolvable stale or
  wrong slugs redirect with HTTP 301 to the current canonical;
- recognised crawlers receive server-rendered canonical, robots, title,
  `NewsArticle` JSON-LD and crawlable article content without depending on
  hydration;
- the sampled `?category=AI%20%26%20Tech` homepage alternate returned HTTP 200
  with the homepage canonical and `index, follow, max-image-preview:large`.
  Search Console last crawled it on 18 August 2026 using Googlebot smartphone,
  fetched it successfully, and agreed with the declared homepage canonical.
  The dedicated hub remains `/category/ai-tech`;
- sampled article alternates `69dcd11...`, `69db7f6...` and `69de221...` were
  HTTP 200 archived records whose current Mongo-ID URLs were self-canonical and
  intentionally `noindex, follow, max-image-preview:large`. For `69dcd11...`
  and `69db7f6...`, Search Console's historical UUID canonicals
  (`8bd18ee6-da58-4b20-9ac8-817ef7a53712` and
  `dc405fcd-e719-4b67-84be-ab0a0f2f3663`) matched those same articles'
  `internal_id` values, rather than a homepage, category, unrelated or missing
  article. Their last crawls were 1 May 2026 at 09:36:21 and 30 April 2026 at
  22:24:59 respectively, both successful Googlebot-smartphone fetches with the
  declared and Google-selected historical UUID canonical aligned;
- `/sitemap.xml` and `/news-sitemap.xml` returned HTTP 200. The sampled archived
  Mongo URLs, historical UUID forms and query alternate were absent; current
  sitemap logic emits eligible active Mongo-ID/current-slug URLs. This was
  representative sampling, not inspection of all 82 examples;
- the crawler homepage exposed 40 Mongo-ID/current-slug article links and no
  `?category=` navigation links. Frontend category navigation uses
  `/category/...`, article helpers use current slugs and public Mongo IDs, and
  no inspected source emitted the sampled UUID or stale alternatives;
- the homepage, a current Wilmslow article and `/category/ai-tech` were HTTP 200,
  correctly canonical and indexable. The archived samples were intentionally
  noindex, and no unintended public `X-Robots-Tag` was observed.

Decision: **DO NOT PRESS VALIDATE FIX NOW.** The report contains intentional
alternates and sampled historical identities for the same articles, while the
current implementation, discovery files and internal links are healthy. Allow
natural Google recrawl. Retain 82 affected examples and the 4 September report
update as the monitoring baseline; recheck after a later report update or a
newly crawled current mismatch. For any new current sample, inspect declared and
Google-selected canonical, article identity, sitemap membership and internal
link source before considering a code change.

## Related documents

[Architecture Master](../ARCHITECTURE_MASTER.md), [Article Pipeline](ARTICLE_PIPELINE.md), [Monitoring](../OPERATIONS/MONITORING.md), and [Production Timeline](../PRODUCTION_TIMELINE.md).
