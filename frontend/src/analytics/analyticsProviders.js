import { ANALYTICS_CONSENT } from "./analyticsConsent";

export const GA_MEASUREMENT_ID = "G-Q1NZLJC50D";
export const POSTHOG_API_HOST = "https://us.i.posthog.com";
export const POSTHOG_PROJECT_TOKEN =
  "phc_yJW1VjHGGwmCbbrtczfqqNxgBDbhlhOWcdzcIJEOTFE";

export const ANALYTICS_SCRIPT_IDS = Object.freeze({
  ga4: "ct-analytics-ga4",
  plausible: "ct-analytics-plausible",
  posthog: "ct-analytics-posthog",
});

const POSTHOG_STUB_METHODS = [
  "capture",
  "opt_in_capturing",
  "opt_out_capturing",
  "reset",
  "stopSessionRecording",
];

let analyticsStatus = ANALYTICS_CONSENT.UNKNOWN;
let activationGeneration = 0;
let initializationPromise = null;
let pendingRoute = null;
let lastDispatchedRoute = null;
let providerReady = { ga4: false, plausible: false, posthog: false };

const safeCall = (callback) => {
  try {
    return callback();
  } catch (_error) {
    return undefined;
  }
};

const appendScriptOnce = ({ id, src, attributes = {} }) => {
  if (typeof document === "undefined") return Promise.resolve(false);

  const existing = document.getElementById(id);
  if (existing) {
    return Promise.resolve(existing.dataset.analyticsLoaded === "true");
  }

  return new Promise((resolve) => {
    const script = document.createElement("script");
    script.id = id;
    script.async = true;
    script.src = src;
    Object.entries(attributes).forEach(([name, value]) => {
      if (value) script.setAttribute(name, value);
    });
    script.addEventListener("load", () => {
      script.dataset.analyticsLoaded = "true";
      resolve(true);
    }, { once: true });
    script.addEventListener("error", () => resolve(false), { once: true });
    (document.head || document.body || document.documentElement).appendChild(script);
  });
};

const loadGa4 = async () => {
  if (typeof window === "undefined") return false;

  window.dataLayer = Array.isArray(window.dataLayer) ? window.dataLayer : [];
  window.gtag = window.gtag || function gtag() {
    window.dataLayer.push(arguments);
  };
  window.gtag("js", new Date());
  window.gtag("config", GA_MEASUREMENT_ID, { send_page_view: false });

  return appendScriptOnce({
    id: ANALYTICS_SCRIPT_IDS.ga4,
    src: `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(GA_MEASUREMENT_ID)}`,
  });
};

const installPlausibleStub = () => {
  if (typeof window === "undefined") return null;
  if (typeof window.plausible === "function") return window.plausible;

  const plausible = function plausible() {
    plausible.q.push(arguments);
  };
  plausible.q = [];
  plausible.init = (options = {}) => {
    plausible.o = options;
  };
  window.plausible = plausible;
  return plausible;
};

const loadPlausible = async () => {
  const domain = String(process.env.REACT_APP_PLAUSIBLE_DOMAIN || "").trim();
  if (!domain || typeof window === "undefined") return false;

  const plausible = installPlausibleStub();
  plausible?.init({ autoCapturePageviews: false });
  return appendScriptOnce({
    id: ANALYTICS_SCRIPT_IDS.plausible,
    src: "https://plausible.io/js/script.js",
    attributes: { "data-domain": domain },
  });
};

const installPostHogStub = () => {
  if (typeof window === "undefined") return null;
  if (window.posthog?.__SV) return window.posthog;

  const posthog = window.posthog || [];
  posthog._i = posthog._i || [];
  POSTHOG_STUB_METHODS.forEach((method) => {
    if (typeof posthog[method] !== "function") {
      posthog[method] = function posthogStub() {
        posthog.push([method, ...arguments]);
      };
    }
  });
  posthog.init = posthog.init || ((token, options, name = "posthog") => {
    posthog._i.push([token, options, name]);
  });
  posthog.__SV = 1;
  window.posthog = posthog;
  return posthog;
};

const loadPostHog = async () => {
  if (typeof window === "undefined") return false;
  const posthog = installPostHogStub();
  posthog?.init(POSTHOG_PROJECT_TOKEN, {
    api_host: POSTHOG_API_HOST,
    person_profiles: "identified_only",
    autocapture: false,
    capture_pageview: false,
    capture_pageleave: false,
    disable_session_recording: true,
    disable_surveys: true,
    opt_out_capturing_by_default: false,
  });
  return appendScriptOnce({
    id: ANALYTICS_SCRIPT_IDS.posthog,
    src: "https://us-assets.i.posthog.com/static/array.js",
    attributes: { crossorigin: "anonymous" },
  });
};

const dispatchRoute = (route) => {
  if (
    analyticsStatus !== ANALYTICS_CONSENT.ACCEPTED ||
    !route ||
    route === lastDispatchedRoute
  ) {
    return false;
  }

  const absoluteUrl = typeof window === "undefined"
    ? route
    : `${window.location.origin}${route}`;

  if (providerReady.ga4) {
    safeCall(() => window.gtag("event", "page_view", {
      page_location: absoluteUrl,
      page_path: route,
      page_title: document.title,
    }));
  }
  if (providerReady.plausible) {
    safeCall(() => window.plausible("pageview", { url: absoluteUrl }));
  }
  if (providerReady.posthog) {
    safeCall(() => window.posthog.capture("$pageview", {
      $current_url: absoluteUrl,
    }));
  }

  lastDispatchedRoute = route;
  return true;
};

export const enableAnalyticsProviders = () => {
  const alreadyAccepted = analyticsStatus === ANALYTICS_CONSENT.ACCEPTED;
  analyticsStatus = ANALYTICS_CONSENT.ACCEPTED;
  if (!alreadyAccepted) activationGeneration += 1;
  const generation = activationGeneration;

  if (!initializationPromise) {
    initializationPromise = Promise.allSettled([
      loadGa4(),
      loadPlausible(),
      loadPostHog(),
    ]).then((results) => {
      providerReady = {
        ga4: results[0].status === "fulfilled" && results[0].value === true,
        plausible: results[1].status === "fulfilled" && results[1].value === true,
        posthog: results[2].status === "fulfilled" && results[2].value === true,
      };
      return providerReady;
    });
  }

  return initializationPromise.then(() => {
    if (
      analyticsStatus !== ANALYTICS_CONSENT.ACCEPTED ||
      generation !== activationGeneration
    ) {
      return false;
    }
    safeCall(() => window.gtag?.("consent", "update", {
      analytics_storage: "granted",
    }));
    safeCall(() => window.posthog?.opt_in_capturing?.());
    const route = pendingRoute;
    pendingRoute = null;
    if (route) dispatchRoute(route);
    return true;
  }).catch(() => false);
};

export const disableAnalyticsProviders = () => {
  analyticsStatus = ANALYTICS_CONSENT.REJECTED;
  activationGeneration += 1;
  pendingRoute = null;
  lastDispatchedRoute = null;

  safeCall(() => window.gtag?.("consent", "update", {
    analytics_storage: "denied",
    ad_storage: "denied",
    ad_user_data: "denied",
    ad_personalization: "denied",
  }));
  safeCall(() => window.posthog?.stopSessionRecording?.());
  safeCall(() => window.posthog?.opt_out_capturing?.());
  safeCall(() => window.posthog?.reset?.());
};

export const requestAnalyticsPageView = (route) => {
  if (analyticsStatus !== ANALYTICS_CONSENT.ACCEPTED || !route) return false;
  if (!initializationPromise) {
    pendingRoute = route;
    enableAnalyticsProviders();
    return true;
  }
  pendingRoute = route;
  initializationPromise.then(() => {
    if (analyticsStatus !== ANALYTICS_CONSENT.ACCEPTED) return;
    const latestRoute = pendingRoute;
    pendingRoute = null;
    if (latestRoute) dispatchRoute(latestRoute);
  }).catch(() => {});
  return true;
};

export const dispatchAnalyticsEvent = (event, props = {}) => {
  if (
    analyticsStatus !== ANALYTICS_CONSENT.ACCEPTED ||
    typeof event !== "string" ||
    !event
  ) {
    return false;
  }

  if (providerReady.ga4) {
    safeCall(() => window.gtag("event", event, props));
  }
  if (providerReady.plausible) {
    safeCall(() => window.plausible(event, { props }));
  }
  if (providerReady.posthog) {
    safeCall(() => window.posthog.capture(event, props));
  }
  return Object.values(providerReady).some(Boolean);
};

export const __resetAnalyticsProvidersForTests = () => {
  analyticsStatus = ANALYTICS_CONSENT.UNKNOWN;
  activationGeneration = 0;
  initializationPromise = null;
  pendingRoute = null;
  lastDispatchedRoute = null;
  providerReady = { ga4: false, plausible: false, posthog: false };
};
