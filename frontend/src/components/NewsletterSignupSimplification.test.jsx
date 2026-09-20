import React, { act } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import { SecureNewsletterPreferencesPage } from "./SecureNewsletterManagementPages";
import NewsletterFull from "./homepage/NewsletterFull";
import {
  NEWSLETTER_SIGNUP_CONSENT,
  buildNewsletterSignupPayload,
} from "../constants/newsletterSignup";

const mockSubscribe = jest.fn();
const mockTrackEvent = jest.fn();
jest.mock("../services/api", () => ({
  newsletterService: { subscribe: (...args) => mockSubscribe(...args) },
}));
jest.mock("../utils/trackEvent", () => ({
  trackEvent: (...args) => mockTrackEvent(...args),
}));

jest.mock("@/lib/utils", () => ({
  cn: (...values) => values.filter(Boolean).join(" "),
}), { virtual: true });

let container;
let root;

beforeAll(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
});

beforeEach(() => {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
  mockSubscribe.mockReset();
  mockTrackEvent.mockReset();
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
  document.body.innerHTML = "";
  jest.restoreAllMocks();
});

const renderSignup = () => {
  act(() => {
    root.render(
      <MemoryRouter>
        <HelmetProvider>
          <Routes>
            <Route path="/" element={<NewsletterFull />} />
            <Route path="/newsletter/preferences" element={<SecureNewsletterPreferencesPage />} />
          </Routes>
        </HelmetProvider>
      </MemoryRouter>,
    );
  });
};

const submit = async (outcome) => {
  mockSubscribe.mockResolvedValue({ success: true, outcome, message: "safe" });
  renderSignup();
  const input = container.querySelector("input[type='email']");
  act(() => {
    const setter = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype,
      "value",
    ).set;
    setter.call(input, "reader@example.com");
    input.dispatchEvent(new Event("change", { bubbles: true }));
  });
  await act(async () => {
    container.querySelector("form").dispatchEvent(
      new Event("submit", { bubbles: true, cancelable: true }),
    );
    await Promise.resolve();
    await Promise.resolve();
  });
};

test("uses the exact consent text and server-owned placement-only payload", async () => {
  await submit("created");
  expect(container.textContent).toContain(NEWSLETTER_SIGNUP_CONSENT);
  expect(mockSubscribe).toHaveBeenCalledWith(
    "reader@example.com",
    "newsletter_landing",
  );
  expect(mockTrackEvent).not.toHaveBeenCalled();
  expect(buildNewsletterSignupPayload("a@b.test", "footer")).toEqual({
    email: "a@b.test",
    signup_placement: "footer",
  });
});

test("does not emit a frontend funnel event before or after the API result", async () => {
  await submit("created");
  expect(mockSubscribe).toHaveBeenCalledTimes(1);
  expect(mockTrackEvent).not.toHaveBeenCalled();
});

test("keeps loading and error UX without emitting a funnel event", async () => {
  let rejectRequest;
  mockSubscribe.mockReturnValue(
    new Promise((_resolve, reject) => {
      rejectRequest = reject;
    }),
  );
  renderSignup();
  const input = container.querySelector("input[type='email']");
  act(() => {
    const setter = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype,
      "value",
    ).set;
    setter.call(input, "reader@example.com");
    input.dispatchEvent(new Event("change", { bubbles: true }));
  });
  act(() => {
    container.querySelector("form").dispatchEvent(
      new Event("submit", { bubbles: true, cancelable: true }),
    );
  });
  expect(container.querySelector("button").disabled).toBe(true);
  expect(container.querySelector("button").textContent).toBe("…");
  await act(async () => {
    rejectRequest(new Error("offline"));
    await Promise.resolve();
  });
  expect(container.textContent).toContain("Something went wrong");
  expect(mockTrackEvent).not.toHaveBeenCalled();
});

test("created outcome confirms all three products without requiring management", async () => {
  await submit("created");
  expect(document.body.textContent).toContain("You’re subscribed");
  expect(document.body.textContent).toContain("The Daily Brief, Monday to Saturday");
  expect(document.body.textContent).toContain("The Weekly Roundup on Sunday");
  expect(document.body.textContent).toContain(
    "Rare Breaking News Alerts for major incidents",
  );
  expect(document.body.textContent).toContain("Close");
  expect(document.body.textContent).toContain("Manage preferences");
  expect(mockSubscribe).toHaveBeenCalledTimes(1);
});

test("existing outcome remains generic and does not assert active subscription", async () => {
  await submit("existing");
  expect(document.body.textContent).toContain(
    "Thanks. If this address is eligible, no further action is needed.",
  );
  expect(document.body.textContent).not.toContain("You’re subscribed");
});

test("signup success opens neutral credential-less preferences", async () => {
  window.history.replaceState({}, "", "/");
  const originalFetch = global.fetch;
  global.fetch = jest.fn();
  try {
    await submit("existing");
    const link = Array.from(document.querySelectorAll("a")).find((item) => item.textContent === "Manage preferences");
    expect(link.getAttribute("href")).toBe("/newsletter/preferences");
    await act(async () => link.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, button: 0 })));
    expect(container.textContent).toContain("secure link to manage your newsletter preferences");
    expect(container.textContent).not.toContain("This link is not valid");
    expect(global.fetch).not.toHaveBeenCalled();
  } finally {
    global.fetch = originalFetch;
  }
});
