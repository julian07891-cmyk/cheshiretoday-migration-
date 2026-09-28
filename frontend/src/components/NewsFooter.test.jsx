import React, { act } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter } from "react-router-dom";
import NewsFooter from "./NewsFooter";

jest.mock("./NewsletterPreferences", () => () => null);
jest.mock("./AnalyticsConsentManager", () => ({
  useAnalyticsConsent: () => ({ openAnalyticsPreferences: jest.fn() }),
}));

test("footer labels category links Topics and preserves all navigation groups", () => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  try {
    act(() => root.render(<MemoryRouter><NewsFooter /></MemoryRouter>));
    const headings = [...container.querySelectorAll("footer h4")];
    expect(headings.map((heading) => heading.textContent)).toEqual([
      "Coverage", "Topics", "Company",
    ]);
    expect(headings.some((heading) => heading.textContent === "Guides")).toBe(false);
    expect(headings.map((heading) => [...heading.parentElement.querySelectorAll("a")]
      .map((link) => [link.textContent, link.getAttribute("href")]))).toEqual([
      [["Local", "/category/local-news"], ["Business", "/category/business"], ["UK", "/category/uk-news"]],
      [["AI & Tech", "/category/ai-tech"], ["Finance", "/category/finance"]],
      [["Contact", "/contact"], ["Advertise", "/advertise"]],
    ]);
  } finally {
    act(() => root.unmount());
    container.remove();
  }
});
