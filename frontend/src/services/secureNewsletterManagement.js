import { getApiUrl } from "../utils/api";

export const NEWSLETTER_TOKEN_MAX_LENGTH = 4096;

const JSON_HEADERS = {
  "Content-Type": "application/json",
};

export const captureNewsletterFragmentToken = (
  browserWindow = window,
) => {
  const fragment = browserWindow.location.hash;
  let token = null;

  if (fragment) {
    const prefix = "#token=";
    if (fragment.startsWith(prefix)) {
      const encodedToken = fragment.slice(prefix.length);
      if (
        encodedToken.length > 0 &&
        !encodedToken.includes("&") &&
        !encodedToken.includes("#")
      ) {
        try {
          token = decodeURIComponent(encodedToken);
        } catch {
          token = null;
        }
      }
    }

    browserWindow.history.replaceState(
      browserWindow.history.state,
      "",
      `${browserWindow.location.pathname}${browserWindow.location.search}`,
    );
  }

  if (
    typeof token !== "string" ||
    token.trim().length === 0 ||
    token.length > NEWSLETTER_TOKEN_MAX_LENGTH
  ) {
    return null;
  }

  return token;
};

const secureRequest = async (path, method, body) => {
  let response;
  try {
    response = await fetch(`${getApiUrl()}${path}`, {
      method,
      headers: JSON_HEADERS,
      body: JSON.stringify(body),
    });
  } catch {
    return { ok: false, status: 0 };
  }

  if (!response.ok) {
    return { ok: false, status: response.status };
  }

  try {
    return {
      ok: true,
      status: response.status,
      data: await response.json(),
    };
  } catch {
    return { ok: false, status: 0 };
  }
};

export const verifySecureNewsletterPreferences = (token) =>
  secureRequest(
    "/api/newsletter/preferences/verify",
    "POST",
    { token },
  );

export const updateSecureNewsletterPreferences = (
  token,
  preferences,
) =>
  secureRequest(
    "/api/newsletter/preferences/secure",
    "PUT",
    { token, ...preferences },
  );

export const confirmSecureNewsletterUnsubscribe = (token) =>
  secureRequest(
    "/api/newsletter/unsubscribe/confirm",
    "POST",
    { token },
  );

export const confirmSecureNewsletterReactivation = (
  token,
  preferences,
) =>
  secureRequest(
    "/api/newsletter/reactivate/confirm",
    "POST",
    { token, ...preferences },
  );

export const secureNewsletterStateForFailure = (
  status,
  { allowReactivation = false } = {},
) => {
  if (status === 503 || status === 0) {
    return "unavailable";
  }
  if (allowReactivation && status === 409) {
    return "reactivation-required";
  }
  return "invalid";
};
