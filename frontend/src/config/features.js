/**
 * Feature flags (production safety)
 * Keep Amazon affiliates ON, hide all other monetisation blocks until ready.
 */
export const FEATURES = {
  // Keep Amazon affiliate widgets visible (AffiliateWidgets.jsx)
  AMAZON_AFFILIATES_ENABLED: true,

  // Hide non-Amazon monetisation UI (guides strips, “helpful tools”, “best picks”, etc.)
  NON_AMAZON_MONETISATION_ENABLED: true,

  // Narrow future test path for article-page guide promos only
  ARTICLE_INLINE_GUIDES_ENABLED: true,
};
