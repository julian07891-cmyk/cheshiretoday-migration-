import React, { act } from "react";
import { createRoot } from "react-dom/client";
import { HelmetProvider } from "react-helmet-async";
import { MemoryRouter } from "react-router-dom";
import {
  SecureNewsletterPreferencesPage,
  SecureNewsletterReactivationPage,
  SecureNewsletterUnsubscribePage,
} from "./SecureNewsletterManagementPages";
import {
  captureNewsletterFragmentToken,
  NEWSLETTER_TOKEN_MAX_LENGTH,
} from "../services/secureNewsletterManagement";

const TOKEN = "opaque.token/value+safe";

globalThis.IS_REACT_ACT_ENVIRONMENT = true;

const jsonResponse = (status, data) =>
  Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
  });

const pendingJsonResponse = () => {
  let resolve;
  const promise = new Promise((next) => {
    resolve = next;
  });
  return { promise, resolve };
};

const flush = async () => {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
};

const renderPage = async (Component, url) => {
  window.history.replaceState({}, "", url);
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () => {
    root.render(
      <HelmetProvider>
        <MemoryRouter>
          <Component />
        </MemoryRouter>
      </HelmetProvider>,
    );
  });
  return {
    container,
    root,
    cleanup: async () => {
      await act(async () => root.unmount());
      container.remove();
    },
  };
};

const click = async (element) => {
  await act(async () => {
    element.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
};

const checkboxByLabel = (container, labelText) =>
  Array.from(container.querySelectorAll("label")).find((label) =>
    label.textContent.includes(labelText),
  )?.querySelector('input[type="checkbox"]');

beforeEach(() => {
  global.fetch = jest.fn();
});

afterEach(() => {
  jest.restoreAllMocks();
  document.body.innerHTML = "";
  window.history.replaceState({}, "", "/");
});

describe("fragment-token capture", () => {
  test("captures a canonical fragment and removes it immediately", () => {
    window.history.replaceState(
      { safe: true },
      "",
      `/newsletter/preferences#token=${encodeURIComponent(TOKEN)}`,
    );
    const replaceState = jest.spyOn(window.history, "replaceState");

    expect(captureNewsletterFragmentToken()).toBe(TOKEN);
    expect(window.location.hash).toBe("");
    expect(replaceState).toHaveBeenCalledWith(
      { safe: true },
      "",
      "/newsletter/preferences",
    );
  });

  test("never accepts a token from query parameters", () => {
    window.history.replaceState(
      {},
      "",
      "/newsletter/preferences?token=query-secret",
    );
    expect(captureNewsletterFragmentToken()).toBeNull();
  });

  test.each([
    ["raw plus", "#token=alpha+beta", "alpha+beta"],
    ["encoded plus", "#token=alpha%2Bbeta", "alpha+beta"],
    ["encoded ampersand", "#token=alpha%26beta", "alpha&beta"],
    ["encoded hash", "#token=alpha%23beta", "alpha#beta"],
    ["single-decoded ampersand", "#token=alpha%2526beta", "alpha%26beta"],
    ["single-decoded hash", "#token=alpha%2523beta", "alpha%23beta"],
    ["single-decoded plus", "#token=alpha%252Bbeta", "alpha%2Bbeta"],
  ])("preserves %s with exactly one decode", (_label, fragment, expected) => {
    window.history.replaceState({}, "", `/unsubscribe${fragment}`);
    expect(captureNewsletterFragmentToken()).toBe(expected);
    expect(window.location.hash).toBe("");
  });

  test.each([
    ["empty", "#token="],
    ["whitespace", "#token=%20%20"],
    [
      "overlong",
      `#token=${"a".repeat(NEWSLETTER_TOKEN_MAX_LENGTH + 1)}`,
    ],
    ["raw extra ampersand", "#token=safe&other=value"],
    ["raw extra hash", "#token=safe#other"],
    ["malformed percent encoding", "#token=%E0%A4%A"],
    ["wrong fragment key", "#other=safe"],
  ])("rejects %s fragment tokens", (_label, fragment) => {
    window.history.replaceState({}, "", `/unsubscribe${fragment}`);
    expect(captureNewsletterFragmentToken()).toBeNull();
    expect(window.location.hash).toBe("");
  });

  test("invalid fragments trigger no API request", async () => {
    const page = await renderPage(
      SecureNewsletterPreferencesPage,
      "/newsletter/preferences#token=broken&other=value",
    );
    await flush();
    expect(fetch).not.toHaveBeenCalled();
    expect(page.container.textContent).toContain("This link is not valid");
    await page.cleanup();
  });
});

describe("secure preferences page", () => {
  test("verifies automatically but updates only after explicit submit", async () => {
    fetch
      .mockReturnValueOnce(
        jsonResponse(200, {
          success: true,
          preferences: {
            daily_brief: true,
            weekly_roundup: false,
            breaking_news: false,
          },
        }),
      )
      .mockReturnValueOnce(
        jsonResponse(200, {
          success: true,
          message: "ignored",
        }),
      );
    const page = await renderPage(
      SecureNewsletterPreferencesPage,
      `/newsletter/preferences#token=${encodeURIComponent(TOKEN)}`,
    );
    await flush();

    expect(fetch).toHaveBeenCalledTimes(1);
    expect(fetch.mock.calls[0][0]).toMatch(
      /\/api\/newsletter\/preferences\/verify$/,
    );
    expect(window.location.hash).toBe("");
    expect(page.container.textContent).not.toContain(TOKEN);

    await click(
      checkboxByLabel(page.container, "Weekly Roundup"),
    );
    expect(fetch).toHaveBeenCalledTimes(1);
    await click(
      Array.from(page.container.querySelectorAll("button")).find(
        (button) => button.textContent === "Save preferences",
      ),
    );
    await flush();

    expect(fetch).toHaveBeenCalledTimes(2);
    expect(fetch.mock.calls[1][0]).toMatch(
      /\/api\/newsletter\/preferences\/secure$/,
    );
    expect(JSON.parse(fetch.mock.calls[1][1].body)).toEqual({
      token: TOKEN,
      daily_brief: true,
      weekly_roundup: true,
      breaking_news: false,
    });
    await page.cleanup();
  });

  test("preserves a raw plus and scrubs history before the first API call", async () => {
    const replaceState = jest.spyOn(window.history, "replaceState");
    fetch.mockReturnValue(
      jsonResponse(200, {
        success: true,
        preferences: {
          daily_brief: false,
          weekly_roundup: false,
          breaking_news: false,
        },
      }),
    );
    const page = await renderPage(
      SecureNewsletterPreferencesPage,
      "/newsletter/preferences#token=alpha+beta",
    );
    await flush();

    expect(window.location.hash).toBe("");
    expect(replaceState.mock.invocationCallOrder[1]).toBeLessThan(
      fetch.mock.invocationCallOrder[0],
    );
    expect(JSON.parse(fetch.mock.calls[0][1].body).token).toBe(
      "alpha+beta",
    );
    expect(fetch.mock.calls[0][0]).not.toContain("alpha+beta");
    await page.cleanup();
  });

  test.each([
    [401, "This link is not valid"],
    [403, "This link is not valid"],
    [409, "Reactivation is required"],
    [422, "This link is not valid"],
    [503, "Newsletter management is unavailable"],
  ])("maps verify HTTP %s to a safe state", async (status, copy) => {
    fetch.mockReturnValue(jsonResponse(status, { detail: TOKEN }));
    const page = await renderPage(
      SecureNewsletterPreferencesPage,
      `/newsletter/preferences#token=${encodeURIComponent(TOKEN)}`,
    );
    await flush();
    expect(page.container.textContent).toContain(copy);
    expect(page.container.textContent).not.toContain(TOKEN);
    await page.cleanup();
  });

  test("handles a network failure without exposing details", async () => {
    fetch.mockRejectedValue(new Error(TOKEN));
    const page = await renderPage(
      SecureNewsletterPreferencesPage,
      `/newsletter/preferences#token=${encodeURIComponent(TOKEN)}`,
    );
    await flush();
    expect(page.container.textContent).toContain(
      "Newsletter management is unavailable",
    );
    expect(page.container.textContent).not.toContain(TOKEN);
    await page.cleanup();
  });

  test("handles malformed JSON without exposing response details", async () => {
    const consoleMethods = ["log", "info", "warn", "error"].map((method) =>
      jest.spyOn(console, method).mockImplementation(() => {}),
    );
    fetch.mockReturnValue(
      Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.reject(new Error(TOKEN)),
      }),
    );
    const page = await renderPage(
      SecureNewsletterPreferencesPage,
      `/newsletter/preferences#token=${encodeURIComponent(TOKEN)}`,
    );
    await flush();
    expect(page.container.textContent).toContain(
      "Newsletter management is unavailable",
    );
    expect(page.container.textContent).not.toContain(TOKEN);
    consoleMethods.forEach((method) => expect(method).not.toHaveBeenCalled());
    await page.cleanup();
  });

  test("handles an unexpected success shape without exposing it", async () => {
    fetch.mockReturnValue(
      jsonResponse(200, {
        success: true,
        preferences: { internal: TOKEN },
      }),
    );
    const page = await renderPage(
      SecureNewsletterPreferencesPage,
      `/newsletter/preferences#token=${encodeURIComponent(TOKEN)}`,
    );
    await flush();
    expect(page.container.textContent).toContain("This link is not valid");
    expect(page.container.textContent).not.toContain(TOKEN);
    await page.cleanup();
  });

  test("prevents duplicate preference updates while pending", async () => {
    const pending = pendingJsonResponse();
    fetch
      .mockReturnValueOnce(
        jsonResponse(200, {
          success: true,
          preferences: {
            daily_brief: false,
            weekly_roundup: false,
            breaking_news: false,
          },
        }),
      )
      .mockReturnValueOnce(pending.promise);
    const page = await renderPage(
      SecureNewsletterPreferencesPage,
      `/newsletter/preferences#token=${encodeURIComponent(TOKEN)}`,
    );
    await flush();
    const button = page.container.querySelector("button");
    await click(button);
    await click(button);
    expect(fetch).toHaveBeenCalledTimes(2);

    pending.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ success: true }),
    });
    await flush();
    await page.cleanup();
  });
});

describe("explicit mutation flows", () => {
  test("unsubscribe calls only the human-confirm endpoint after confirmation", async () => {
    fetch.mockReturnValue(jsonResponse(200, { success: true }));
    const page = await renderPage(
      SecureNewsletterUnsubscribePage,
      `/unsubscribe#token=${encodeURIComponent(TOKEN)}`,
    );

    expect(fetch).not.toHaveBeenCalled();
    const button = Array.from(
      page.container.querySelectorAll("button"),
    ).find((candidate) => candidate.textContent === "Confirm unsubscribe");
    await click(button);
    await flush();

    expect(fetch).toHaveBeenCalledTimes(1);
    expect(fetch.mock.calls[0][0]).toMatch(
      /\/api\/newsletter\/unsubscribe\/confirm$/,
    );
    expect(fetch.mock.calls[0][0]).not.toContain("one-click");
    await page.cleanup();
  });

  test("reactivation requires explicit preference confirmation", async () => {
    fetch.mockReturnValue(jsonResponse(200, { success: true }));
    const page = await renderPage(
      SecureNewsletterReactivationPage,
      `/newsletter/reactivate#token=${encodeURIComponent(TOKEN)}`,
    );
    const submit = Array.from(
      page.container.querySelectorAll("button"),
    ).find((button) => button.textContent === "Confirm reactivation");

    expect(submit.disabled).toBe(true);
    await click(checkboxByLabel(page.container, "Daily Brief"));
    expect(fetch).not.toHaveBeenCalled();
    await click(
      checkboxByLabel(
        page.container,
        "I confirm these newsletter preferences",
      ),
    );
    expect(submit.disabled).toBe(false);
    await click(submit);
    await flush();

    expect(fetch).toHaveBeenCalledTimes(1);
    expect(fetch.mock.calls[0][0]).toMatch(
      /\/api\/newsletter\/reactivate\/confirm$/,
    );
    expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({
      token: TOKEN,
      daily_brief: true,
      weekly_roundup: false,
      breaking_news: false,
    });
    await page.cleanup();
  });

  test("prevents duplicate unsubscribe submissions while pending", async () => {
    const pending = pendingJsonResponse();
    fetch.mockReturnValue(pending.promise);
    const page = await renderPage(
      SecureNewsletterUnsubscribePage,
      `/unsubscribe#token=${encodeURIComponent(TOKEN)}`,
    );
    const button = page.container.querySelector("button");
    await click(button);
    await click(button);
    expect(fetch).toHaveBeenCalledTimes(1);

    pending.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ success: true }),
    });
    await flush();
    await page.cleanup();
  });

  test("prevents duplicate reactivation submissions while pending", async () => {
    const pending = pendingJsonResponse();
    fetch.mockReturnValue(pending.promise);
    const page = await renderPage(
      SecureNewsletterReactivationPage,
      `/newsletter/reactivate#token=${encodeURIComponent(TOKEN)}`,
    );
    await click(
      checkboxByLabel(
        page.container,
        "I confirm these newsletter preferences",
      ),
    );
    const button = page.container.querySelector("button");
    await click(button);
    await click(button);
    expect(fetch).toHaveBeenCalledTimes(1);

    pending.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ success: true }),
    });
    await flush();
    await page.cleanup();
  });

  test("503 displays unavailable without rendering the token", async () => {
    fetch.mockReturnValue(jsonResponse(503, { detail: TOKEN }));
    const page = await renderPage(
      SecureNewsletterUnsubscribePage,
      `/unsubscribe#token=${encodeURIComponent(TOKEN)}`,
    );
    await click(page.container.querySelector("button"));
    await flush();
    expect(page.container.textContent).toContain(
      "Newsletter management is unavailable",
    );
    expect(page.container.textContent).not.toContain(TOKEN);
    await page.cleanup();
  });
});

describe("privacy and route source contracts", () => {
  test("does not persist or log a captured token", async () => {
    const localSet = jest.spyOn(
      Storage.prototype,
      "setItem",
    );
    const consoleMethods = ["log", "info", "warn", "error"].map((method) =>
      jest.spyOn(console, method).mockImplementation(() => {}),
    );
    const page = await renderPage(
      SecureNewsletterUnsubscribePage,
      `/unsubscribe#token=${encodeURIComponent(TOKEN)}`,
    );

    expect(localSet).not.toHaveBeenCalled();
    consoleMethods.forEach((method) => expect(method).not.toHaveBeenCalled());
    expect(document.cookie).not.toContain(TOKEN);
    expect(page.container.innerHTML).not.toContain(TOKEN);
    expect(document.title).not.toContain(TOKEN);
    await page.cleanup();
  });

  test("registers all secure pages without changing unrelated routes", () => {
    const appSource = require("fs").readFileSync(
      require("path").join(__dirname, "../App.js"),
      "utf8",
    );
    [
      'path="/newsletter/preferences"',
      'path="/unsubscribe"',
      'path="/newsletter/reactivate"',
    ].forEach((route) => {
      expect(appSource.split(route)).toHaveLength(2);
    });
    [
      'path="/"',
      'path="/admin"',
      'path="/jobs"',
      'path="/privacy"',
      'path="/contact"',
    ].forEach((route) => expect(appSource).toContain(route));
    expect(appSource).not.toContain(
      "/api/newsletter/unsubscribe/one-click",
    );
  });
});
