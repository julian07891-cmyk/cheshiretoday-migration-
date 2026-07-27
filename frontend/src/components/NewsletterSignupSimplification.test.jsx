import React, { act } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter } from "react-router-dom";
import NewsletterFull from "./homepage/NewsletterFull";
import {
  NEWSLETTER_SIGNUP_CONSENT,
  buildNewsletterSignupPayload,
} from "../constants/newsletterSignup";

const mockSubscribe = jest.fn();
jest.mock("../services/api", () => ({
  newsletterService: { subscribe: (...args) => mockSubscribe(...args) },
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
        <NewsletterFull />
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
  expect(buildNewsletterSignupPayload("a@b.test", "footer")).toEqual({
    email: "a@b.test",
    signup_placement: "footer",
  });
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
