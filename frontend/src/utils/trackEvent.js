export const trackEvent = (event, props = {}) => {
  if (typeof window === "undefined") return;

  // Plausible custom events
  // Requires: <script defer data-domain="..." src="https://plausible.io/js/script.js"></script>
  if (typeof window.plausible === "function") {
    window.plausible(event, { props });
  }

  // Google Tag / GA4 compatible (via GTM)
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
