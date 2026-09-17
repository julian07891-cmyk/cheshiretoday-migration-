import {
  ANALYTICS_CONSENT,
  ANALYTICS_CONSENT_STORAGE_KEY,
  parseAnalyticsConsent,
  persistAnalyticsConsent,
  readAnalyticsConsent,
} from "./analyticsConsent";

describe("analytics consent storage", () => {
  test("defaults malformed, unknown and old values to UNKNOWN", () => {
    expect(parseAnalyticsConsent(null)).toBe(ANALYTICS_CONSENT.UNKNOWN);
    expect(parseAnalyticsConsent("broken")).toBe(ANALYTICS_CONSENT.UNKNOWN);
    expect(parseAnalyticsConsent('{"version":1,"status":"maybe"}')).toBe(ANALYTICS_CONSENT.UNKNOWN);
    expect(parseAnalyticsConsent('{"version":0,"status":"accepted"}')).toBe(ANALYTICS_CONSENT.UNKNOWN);
  });

  test("persists only a versioned accepted or rejected choice", () => {
    const storage = { getItem: jest.fn(), setItem: jest.fn() };
    expect(persistAnalyticsConsent(ANALYTICS_CONSENT.UNKNOWN, storage)).toBe(false);
    expect(persistAnalyticsConsent(ANALYTICS_CONSENT.ACCEPTED, storage)).toBe(true);
    expect(storage.setItem).toHaveBeenCalledWith(
      ANALYTICS_CONSENT_STORAGE_KEY,
      '{"version":1,"status":"accepted"}',
    );
  });

  test("storage failures fail denied and never break the app", () => {
    const storage = {
      getItem: () => { throw new Error("blocked"); },
      setItem: () => { throw new Error("blocked"); },
    };
    expect(readAnalyticsConsent(storage)).toBe(ANALYTICS_CONSENT.UNKNOWN);
    expect(persistAnalyticsConsent(ANALYTICS_CONSENT.ACCEPTED, storage)).toBe(false);
  });
});
