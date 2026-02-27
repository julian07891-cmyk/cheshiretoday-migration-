/**
 * Feature flags (production safety)
 * Keep Amazon affiliates ON, hide all other monetisation blocks until ready.
 */
export const FEATURES = {
  // Keep Amazon affiliate widgets visible (AffiliateWidgets.jsx)
  AMAZON_AFFILIATES_ENABLED: true,

  // Hide non-Amazon monetisation UI (guides strips, “helpful tools”, “best picks”, etc.)
  NON_AMAZON_MONETISATION_ENABLED: false,
};
