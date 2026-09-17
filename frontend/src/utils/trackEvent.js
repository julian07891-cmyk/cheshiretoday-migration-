import { dispatchAnalyticsEvent } from "../analytics/analyticsProviders";

export const trackEvent = (event, props = {}) => {
  dispatchAnalyticsEvent(event, props);

  // Safe fallback for debugging
  if (process.env.NODE_ENV !== "production") {
    console.log("[trackEvent]", event, props);
  }
};
