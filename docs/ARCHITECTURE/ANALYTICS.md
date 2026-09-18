# Cheshire Today — Analytics Architecture

> **Reconstruction status:** Current-code capability at HEAD; third-party dashboard state and live volumes require production evidence.

## Document purpose

Describe first-party readership, email and commercial analytics separately from third-party platforms.

## Authority and evidence

Primary evidence: `backend/server.py` (`track_article_view`, `get_most_read_articles`, tracking endpoints), `backend/app/admin_analytics.py`, `frontend/src/services/articleViewTracking.js`, Admin analytics components, and focused analytics tests. See [Source Register](../HISTORY/SOURCE_REGISTER.md).

## How to use this document

Use this to interpret metrics and identify data ownership. Do not equate events, accepted sends or third-party signals with unique people.

## First-party article views and Most Read

The public article-view endpoint writes bounded events to `article_views` and maintains article view state subject to an IP/article/hour deduplication contract. Source attribution recognises deterministic Facebook UTM parameters. `/api/articles/most-read` aggregates eligible public article events for supported periods and excludes hidden/archived results.

## Admin analytics

`GET /api/admin/analytics/summary` is authenticated. `backend/app/admin_analytics.py` builds period summaries in separately isolated subsections, including article readership, Facebook-attributed views, newsletter, commercial and advertiser data. Subsection failure can be reported without invalidating every other subsection.

## Facebook attribution

Social Publishing constructs a deterministic public article URL with `utm_source=facebook`, `utm_medium=social`, and `utm_campaign=social_publishing`. The browser retains attribution parameters while canonical and Open Graph URL identity remain clean. First-party event attribution—not Meta reaction/comment/share data—drives the Admin Facebook article metrics.

## Email analytics

Per-recipient tracking identifiers support open pixels and click redirects stored in `email_analytics`. `email_send_opportunities` records hashed accepted-recipient opportunities and batch counts. Provider acceptance, opens and clicks are different measures; scanner activity can create non-human events.

## Commercial analytics

Sponsored placement impression and click endpoints increment counters in `sponsored_placements`. Affiliate/provider click tracking and advertiser/payment summaries are distinct from article views. Admin commercial summaries read MongoDB; they do not establish revenue attribution by themselves.

## Third-party analytics

Commit `be0182b` implements a bounded frontend consent layer for GA4, Plausible
and PostHog. The versioned state is Unknown, Accepted or Rejected; Unknown and
Rejected do not load providers. Accepted dynamically loads configured providers
and enables application-owned SPA page-view and consent-aware custom-event
dispatch. Provider automatic page views are disabled, including GA4
`send_page_view: false`; PostHog autocapture and session recording are disabled.
Sensitive routes are excluded and application-owned analytics URLs retain only
bounded approved attribution data. Users can withdraw or re-accept through the
persistent Cookie/privacy settings control. First-party measurement is outside
this gate and intentionally unchanged.

Four focused suites/17 tests and ten regression suites/118 tests passed before
deployment, together with the production build. Deployment and observable browser
behaviour are verified. Event-level production network acceptance remains
inconclusive because available tooling could not combine genuinely isolated
storage inspection with request interception/payload inspection. No production
defect is confirmed. Provider event payload/count, exact SPA cardinality,
transmitted URL normalisation, event-level sensitive-route and withdrawal
suppression, and dashboard receipt require later external evidence; code or
dashboard state alone must not be substituted for it.

Facebook provider APIs and first-party Facebook attribution must not be
conflated with this third-party consent layer.

## Privacy and data limitations

Do not expose raw IP hashes, subscriber data, tracking records or request payloads. Article views are events rather than unique users. Email scanners, browser caching, deduplication windows and provider latency affect interpretation. Historical unknown-source views are not Facebook views.

## Protected boundaries

Preserve event deduplication, authenticated Admin access, privacy-safe presentation, public canonical identity and separation of mutation endpoints from analytics reads.

## Known limitations

No single system gives end-to-end identity across public, email and third-party channels. Aggregate accuracy depends on client requests completing and database availability. Index changes require measured latency evidence.
This technical evidence does not establish legal compliance, historical-data
treatment, provider-dashboard reporting or correctness of first-party policy.

## Related documents

[Architecture Master](../ARCHITECTURE_MASTER.md), [Newsletter](NEWSLETTER.md), [Monetisation](MONETISATION.md), and [Monitoring](../OPERATIONS/MONITORING.md).
