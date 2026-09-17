import { dispatchAnalyticsEvent } from "../analytics/analyticsProviders";
import { trackEvent } from "./trackEvent";

jest.mock("../analytics/analyticsProviders", () => ({ dispatchAnalyticsEvent: jest.fn() }));

test("trackEvent delegates exclusively to the consent-aware adapter", () => {
  trackEvent("social_click", { network: "facebook" });
  expect(dispatchAnalyticsEvent).toHaveBeenCalledWith("social_click", { network: "facebook" });
});
