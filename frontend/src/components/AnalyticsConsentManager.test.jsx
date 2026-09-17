import React, { act } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter, useNavigate } from "react-router-dom";
import AnalyticsConsentManager, { normalizeAnalyticsRoute, useAnalyticsConsent } from "./AnalyticsConsentManager";
import { ANALYTICS_CONSENT_STORAGE_KEY } from "../analytics/analyticsConsent";
import * as providers from "../analytics/analyticsProviders";
import NewsFooter from "./NewsFooter";

jest.mock("./NewsletterPreferences", () => () => null);

jest.mock("../analytics/analyticsProviders", () => ({
  disableAnalyticsProviders: jest.fn(),
  enableAnalyticsProviders: jest.fn(() => Promise.resolve(true)),
  requestAnalyticsPageView: jest.fn(),
}));

const Controls = () => {
  const navigate = useNavigate();
  const { openAnalyticsPreferences } = useAnalyticsConsent();
  return <><button onClick={() => navigate("/article/two")}>Navigate</button><button onClick={() => navigate(-1)}>Back</button><button onClick={openAnalyticsPreferences}>Cookie / privacy settings</button></>;
};

let container;
let root;
beforeAll(() => { global.IS_REACT_ACT_ENVIRONMENT = true; });
beforeEach(() => {
  localStorage.clear();
  jest.clearAllMocks();
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});
afterEach(() => {
  act(() => root.unmount());
  container.remove();
});

const renderManager = async (entry = "/article/one", children = <Controls />) => {
  await act(async () => root.render(<MemoryRouter initialEntries={[entry]}><AnalyticsConsentManager>{children}</AnalyticsConsentManager></MemoryRouter>));
};
const button = (text) => [...container.querySelectorAll("button")].find((node) => node.textContent === text);
const click = async (node) => { await act(async () => node.click()); };

test("fresh visitor sees equal accessible choices and no providers load", async () => {
  await renderManager();
  expect(container.querySelector("h2").textContent).toBe("Analytics preferences");
  expect(button("Accept analytics")).not.toBeUndefined();
  expect(button("Reject analytics")).not.toBeUndefined();
  expect(button("Accept analytics").className).toBe(button("Reject analytics").className);
  expect(container.querySelector('a[href="/cookies"]').textContent).toBe("Cookie Policy");
  expect(providers.enableAnalyticsProviders).not.toHaveBeenCalled();
  expect(container.querySelector('[role="dialog"]').className).toContain("inset-x-3");
});

test("accept persists and counts current route and later navigation once", async () => {
  await renderManager();
  await click(button("Accept analytics"));
  expect(JSON.parse(localStorage.getItem(ANALYTICS_CONSENT_STORAGE_KEY))).toEqual({ version: 1, status: "accepted" });
  expect(providers.requestAnalyticsPageView).toHaveBeenCalledWith("/article/one");
  await click(button("Navigate"));
  expect(providers.requestAnalyticsPageView).toHaveBeenLastCalledWith("/article/two");
  expect(providers.requestAnalyticsPageView).toHaveBeenCalledTimes(2);
});

test("reject leaves navigation usable and settings permit re-acceptance", async () => {
  await renderManager();
  await click(button("Reject analytics"));
  await click(button("Navigate"));
  expect(providers.requestAnalyticsPageView).not.toHaveBeenCalled();
  await click(button("Cookie / privacy settings"));
  await click(button("Accept analytics"));
  expect(providers.enableAnalyticsProviders).toHaveBeenCalledTimes(1);
});

test("withdrawal stops dispatch and persisted rejection survives reload", async () => {
  localStorage.setItem(ANALYTICS_CONSENT_STORAGE_KEY, '{"version":1,"status":"accepted"}');
  await renderManager();
  await click(button("Cookie / privacy settings"));
  await click(button("Reject analytics"));
  expect(providers.disableAnalyticsProviders).toHaveBeenCalled();
  act(() => root.unmount());
  root = createRoot(container);
  jest.clearAllMocks();
  await renderManager();
  expect(container.querySelector('[role="dialog"]')).toBeNull();
  expect(providers.enableAnalyticsProviders).not.toHaveBeenCalled();
});

test("persisted acceptance loads once and rerender does not duplicate the initial route", async () => {
  localStorage.setItem(ANALYTICS_CONSENT_STORAGE_KEY, '{"version":1,"status":"accepted"}');
  await renderManager();
  expect(providers.enableAnalyticsProviders).toHaveBeenCalledTimes(1);
  expect(providers.requestAnalyticsPageView).toHaveBeenCalledTimes(1);
  await act(async () => root.render(<MemoryRouter initialEntries={["/article/one"]}><AnalyticsConsentManager><Controls /></AnalyticsConsentManager></MemoryRouter>));
  expect(providers.requestAnalyticsPageView).toHaveBeenCalledTimes(1);
});

test("route deduplication is consecutive-only across leave and history return", async () => {
  localStorage.setItem(ANALYTICS_CONSENT_STORAGE_KEY, '{"version":1,"status":"accepted"}');
  await renderManager();
  await click(button("Navigate"));
  await click(button("Back"));
  expect(providers.requestAnalyticsPageView.mock.calls.map(([route]) => route)).toEqual([
    "/article/one",
    "/article/two",
    "/article/one",
  ]);
});

test("persisted rejection loads no providers and sensitive routes dispatch no views", async () => {
  localStorage.setItem(ANALYTICS_CONSENT_STORAGE_KEY, '{"version":1,"status":"rejected"}');
  await renderManager("/admin");
  expect(providers.enableAnalyticsProviders).not.toHaveBeenCalled();
  expect(providers.requestAnalyticsPageView).not.toHaveBeenCalled();
});

test("footer privacy settings control reopens the single global manager", async () => {
  localStorage.setItem(ANALYTICS_CONSENT_STORAGE_KEY, '{"version":1,"status":"rejected"}');
  await renderManager("/", <NewsFooter />);
  expect(container.querySelector('[role="dialog"]')).toBeNull();
  await click(button("Cookie / privacy settings"));
  expect(container.querySelectorAll('[role="dialog"]')).toHaveLength(1);
});

test("normalizes safe attribution and excludes fragments, unsafe queries and sensitive routes", () => {
  expect(normalizeAnalyticsRoute({ pathname: "/", search: "?utm_source=facebook&email=private%40example.com&category=Local", hash: "#top" })).toBe("/?category=Local&utm_source=facebook");
  expect(normalizeAnalyticsRoute({ pathname: "/article/one", search: "?utm_campaign=a%20b&token=secret" })).toBe("/article/one");
  expect(normalizeAnalyticsRoute({ pathname: "/admin", search: "" })).toBeNull();
  expect(normalizeAnalyticsRoute({ pathname: "/newsletter/preferences", search: "?token=secret" })).toBeNull();
});
