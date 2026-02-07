export const trackEvent = (event, props = {}) => {
  if (typeof window === "undefined") return;

  // Google Tag / GA4 compatible
  if (window.dataLayer && Array.isArray(window.dataLayer)) {
    window.dataLayer.push({
      event,
      ...props,
    });
  }

  // Safe fallback for debugging
  if (process.env.NODE_ENV !== "production") {
    console.log("[trackEvent]", event, props);
  }
};
