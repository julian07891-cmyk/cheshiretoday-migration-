export const ANALYTICS_CONSENT_STORAGE_KEY = "ct_analytics_consent";
export const ANALYTICS_CONSENT_VERSION = 1;

export const ANALYTICS_CONSENT = Object.freeze({
  UNKNOWN: "unknown",
  ACCEPTED: "accepted",
  REJECTED: "rejected",
});

const persistedStatuses = new Set([
  ANALYTICS_CONSENT.ACCEPTED,
  ANALYTICS_CONSENT.REJECTED,
]);

export const parseAnalyticsConsent = (rawValue) => {
  if (typeof rawValue !== "string" || !rawValue) {
    return ANALYTICS_CONSENT.UNKNOWN;
  }

  try {
    const parsed = JSON.parse(rawValue);
    if (
      parsed &&
      typeof parsed === "object" &&
      parsed.version === ANALYTICS_CONSENT_VERSION &&
      persistedStatuses.has(parsed.status)
    ) {
      return parsed.status;
    }
  } catch (_error) {}

  return ANALYTICS_CONSENT.UNKNOWN;
};

export const readAnalyticsConsent = (storage) => {
  try {
    const availableStorage = storage === undefined ? globalThis.localStorage : storage;
    return parseAnalyticsConsent(availableStorage?.getItem(ANALYTICS_CONSENT_STORAGE_KEY));
  } catch (_error) {
    return ANALYTICS_CONSENT.UNKNOWN;
  }
};

export const persistAnalyticsConsent = (
  status,
  storage,
) => {
  if (!persistedStatuses.has(status)) return false;

  try {
    const availableStorage = storage === undefined ? globalThis.localStorage : storage;
    availableStorage?.setItem(
      ANALYTICS_CONSENT_STORAGE_KEY,
      JSON.stringify({ version: ANALYTICS_CONSENT_VERSION, status }),
    );
    return Boolean(availableStorage);
  } catch (_error) {
    return false;
  }
};
