import React, { act } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter } from "react-router-dom";
import NewsletterPage from "./NewsletterPage";

jest.mock("react-helmet-async", () => ({
  Helmet: ({ children }) => <>{children}</>,
}));
jest.mock("../components/NewsFooter", () => () => <footer>Footer</footer>);
jest.mock("../components/NewsletterPreferences", () => () => null);

let container;
let root;

beforeAll(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
});

beforeEach(() => {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
});

test("renders the newsletter landing page, benefits and documented schedule", () => {
  act(() => {
    root.render(
      <MemoryRouter>
        <NewsletterPage />
      </MemoryRouter>,
    );
  });

  expect(container.querySelectorAll("h1")).toHaveLength(1);
  expect(container.textContent).toContain("Stay ahead with Cheshire’s daily briefing");
  expect(container.textContent).toContain("Cheshire Daily Brief");
  expect(container.textContent).toContain("Business and investment updates");
  expect(container.textContent).toContain("Monday to Saturday");
  expect(container.textContent).toContain("Sunday");
  expect(container.textContent).toContain("Privacy Policy");
  expect(container.querySelector("[data-testid='newsletter-full-signup']")).toBeTruthy();
});

test("hero CTA focuses the reused signup form email field", () => {
  act(() => {
    root.render(
      <MemoryRouter>
        <NewsletterPage />
      </MemoryRouter>,
    );
  });

  const cta = Array.from(container.querySelectorAll("button")).find(
    (button) => button.textContent === "Subscribe free",
  );
  act(() => cta.click());

  expect(document.activeElement).toBe(
    container.querySelector("#newsletter-signup-email"),
  );
});

test("uses a mobile-safe container without horizontal overflow styling", () => {
  act(() => {
    root.render(
      <MemoryRouter>
        <NewsletterPage />
      </MemoryRouter>,
    );
  });

  expect(container.firstChild.className).toContain("overflow-x-hidden");
  expect(container.querySelector("main").className).toContain("w-full");
});

test("uses the dedicated absolute newsletter image for browser social metadata", () => {
  act(() => {
    root.render(
      <MemoryRouter>
        <NewsletterPage />
      </MemoryRouter>,
    );
  });

  const expected = "https://cheshiretoday.co.uk/cheshire-today-newsletter-share.png";
  expect(container.querySelector('meta[property="og:image"]').getAttribute("content")).toBe(expected);
  expect(container.querySelector('meta[name="twitter:image"]').getAttribute("content")).toBe(expected);
  expect(container.innerHTML).not.toContain("/social-share.jpg");
});
