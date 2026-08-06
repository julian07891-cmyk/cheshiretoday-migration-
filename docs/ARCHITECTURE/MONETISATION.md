# Cheshire Today — Monetisation Architecture

> **Reconstruction status:** Current-code capability at HEAD; activation, inventory and revenue performance are not inferred.

## Document purpose

Describe authority/affiliate and paid-placement systems, their Admin workflows, tracking and payment boundaries.

## Authority and evidence

Primary evidence: authority, affiliate, sponsored-placement, advertiser-lead, jobs and Stripe routes in `backend/server.py`; corresponding frontend components; current tests and committed configuration. See [Source Register](../HISTORY/SOURCE_REGISTER.md).

## How to use this document

Use this to identify commercial data flows before changing placement, checkout or reporting behaviour. Confirm environment activation separately.

## Authority pages and affiliate providers

`authority_pages` stores guide content exposed through public guide routes and crawler HTML. `affiliate_products` stores Admin-managed provider/product records; public endpoints return active products. Authority-page helpers apply mapped affiliate links to eligible tool entries. Article-to-guide recommendations and homepage guide surfaces connect editorial content to relevant authority pages.

## Sponsored placements

Public `GET /api/sponsored-placements` selects active records by placement slot. Forced preview parameters are constrained; ordinary serving uses priority plus weighted rotation over a bounded candidate set. Placement types include current article/homepage slots evidenced in stored route handling. Public impression and click endpoints update placement counters.

## Advertiser workflow

Public advertising routes capture `advertiser_leads`. Authenticated Admin routes list and update lead status and create/update sponsored placements. Publishing a placement can claim and send an advert-live notification once; provider failure is recorded separately. House adverts are represented by ordinary placement data/configuration where present, not a separate revenue claim.

## Stripe checkout

Advertising checkout creates or associates a lead, creates a Stripe session and records a `payment_transactions` entry. Checkout status and signed webhook processing update payment/lead state. Paid status remains pending editorial/Admin review rather than automatic publication. Jobs have a separate checkout path using the configured payments integration.

## Tracking and analytics

Sponsored impression/click counters, advertiser lead states and payment summaries feed Admin analytics. Affiliate/provider clicks are a separate signal. These counters do not prove realised revenue or conversion attribution.

## Feature and provider boundaries

Stripe, provider links, advert-live email, external social systems and specific inventory depend on environment configuration and data. Social Publishing prepares deterministic assets/links but does not belong to automatic advertising publication.

## Protected boundaries

Preserve Admin review before paid placement goes live, webhook validation, bounded rotation, click/impression separation, advertiser privacy, and no automatic editorial publication from payment.

## Known limitations

Repository code does not establish live campaigns, revenue, provider approval or conversion accuracy. Weighted rotation is application-level and database availability dependent. Deferred provider integrations must remain labelled as such.

## Related documents

[Architecture Master](../ARCHITECTURE_MASTER.md), [Analytics](ANALYTICS.md), [SEO and Crawlers](SEO_AND_CRAWLERS.md), [Deployment](../OPERATIONS/DEPLOYMENT.md), and [Decision Register](../DECISION_REGISTER.md).
