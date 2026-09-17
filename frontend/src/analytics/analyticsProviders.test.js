import { ANALYTICS_CONSENT } from "./analyticsConsent";
import {
  ANALYTICS_SCRIPT_IDS,
  __resetAnalyticsProvidersForTests,
  disableAnalyticsProviders,
  dispatchAnalyticsEvent,
  enableAnalyticsProviders,
  requestAnalyticsPageView,
} from "./analyticsProviders";
import { trackEvent } from "../utils/trackEvent";

describe("consent-aware analytics providers", () => {
  const originalDomain = process.env.REACT_APP_PLAUSIBLE_DOMAIN;

  beforeEach(() => {
    process.env.REACT_APP_PLAUSIBLE_DOMAIN = "cheshiretoday.co.uk";
    __resetAnalyticsProvidersForTests();
    Object.values(ANALYTICS_SCRIPT_IDS).forEach((id) => document.getElementById(id)?.remove());
    delete window.dataLayer;
    delete window.gtag;
    delete window.plausible;
    delete window.posthog;
  });

  afterAll(() => { process.env.REACT_APP_PLAUSIBLE_DOMAIN = originalDomain; });

  test("drops events before consent and inserts each provider script once after acceptance", async () => {
    expect(dispatchAnalyticsEvent("before_consent")).toBe(false);
    expect(Object.values(ANALYTICS_SCRIPT_IDS).every((id) => !document.getElementById(id))).toBe(true);

    const first = enableAnalyticsProviders();
    const second = enableAnalyticsProviders();
    Object.values(ANALYTICS_SCRIPT_IDS).forEach((id) => {
      document.getElementById(id).dispatchEvent(new Event("load"));
    });
    await Promise.all([first, second]);
    Object.values(ANALYTICS_SCRIPT_IDS).forEach((id) => {
      expect(document.querySelectorAll(`#${id}`)).toHaveLength(1);
    });
    expect(window.posthog._i[0][1]).toEqual(expect.objectContaining({
      autocapture: false,
      capture_pageview: false,
      disable_session_recording: true,
    }));
  });

  test("isolates a provider failure and dispatches one explicit route", async () => {
    const enabled = enableAnalyticsProviders();
    document.getElementById(ANALYTICS_SCRIPT_IDS.ga4).dispatchEvent(new Event("load"));
    document.getElementById(ANALYTICS_SCRIPT_IDS.plausible).dispatchEvent(new Event("error"));
    document.getElementById(ANALYTICS_SCRIPT_IDS.posthog).dispatchEvent(new Event("load"));
    requestAnalyticsPageView("/article/one");
    await enabled;
    const pageviews = window.dataLayer.filter((entry) => entry?.[0] === "event" && entry?.[1] === "page_view");
    expect(pageviews).toHaveLength(1);
  });

  test("uses the exact Plausible manual URL contract and dispatches an accepted custom event once", async () => {
    const enabled = enableAnalyticsProviders();
    Object.values(ANALYTICS_SCRIPT_IDS).forEach((id) => {
      document.getElementById(id).dispatchEvent(new Event("load"));
    });
    requestAnalyticsPageView("/article/one?utm_source=facebook");
    await enabled;

    const pageviewCall = window.plausible.q.find(([event]) => event === "pageview");
    expect(pageviewCall[0]).toBe("pageview");
    expect(pageviewCall[1]).toEqual({
      url: "http://localhost/article/one?utm_source=facebook",
    });
    expect(pageviewCall[1]).not.toHaveProperty("u");

    trackEvent("social_click", { network: "facebook" });
    const customCalls = window.plausible.q.filter(([event]) => event === "social_click");
    expect(customCalls).toHaveLength(1);
    expect(customCalls[0][0]).toBe("social_click");
    expect(customCalls[0][1]).toEqual({ props: { network: "facebook" } });
  });

  test("withdrawal wins during loading and re-acceptance does not duplicate scripts", async () => {
    const enabled = enableAnalyticsProviders();
    disableAnalyticsProviders();
    Object.values(ANALYTICS_SCRIPT_IDS).forEach((id) => document.getElementById(id).dispatchEvent(new Event("load")));
    await enabled;
    expect(requestAnalyticsPageView("/after-withdrawal")).toBe(false);
    expect(dispatchAnalyticsEvent("after_withdrawal")).toBe(false);
    await enableAnalyticsProviders();
    expect(Object.values(ANALYTICS_SCRIPT_IDS).every((id) => document.querySelectorAll(`#${id}`).length === 1)).toBe(true);
    expect(window.dataLayer.some((entry) => entry?.[0] === "consent" && entry?.[2]?.analytics_storage === "granted")).toBe(true);
  });
});
