import React, { act } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import ArticlePageV2 from "./ArticlePageV2";

const mockLoadPublicArticle = jest.fn();
const mockSelectContextualRecommendation = jest.fn();
let mockSponsorAvailable = false;

jest.mock("react-helmet-async", () => ({ Helmet: ({ children }) => <>{children}</> }));
jest.mock("../services/articleViewTracking", () => ({
  loadPublicArticle: (...args) => mockLoadPublicArticle(...args),
}));
jest.mock("../config/contextualRecommendations", () => ({
  normaliseContextualCategory: (value) => String(value || "").toLowerCase(),
  selectContextualRecommendation: (...args) => mockSelectContextualRecommendation(...args),
}));
jest.mock("../components/NewsHeader", () => () => <header>Cheshire Today</header>);
jest.mock("../components/NewsFooter", () => () => <footer>Footer newsletter</footer>);
jest.mock("../components/FestiveTheme", () => () => null);
jest.mock("../components/RelatedArticles", () => () => <div data-testid="related-articles">Related articles</div>);
jest.mock("../components/SubscribeSection", () => () => <div data-testid="sidebar-newsletter">Sidebar newsletter</div>);
jest.mock("../components/JobsWidget", () => ({
  SubscribeInlineBanner: () => <div data-testid="inline-newsletter">Inline newsletter</div>,
}));
jest.mock("../components/CompactArticleCard", () => () => null);
jest.mock("../components/homepage/TextHeadlineStrip", () => () => null);
jest.mock("../components/homepage/SectionHeader", () => ({ title }) => <h2>{title}</h2>);
jest.mock("../components/monetisation/ContextualRecommendationCard", () => ({ recommendation }) => (
  recommendation ? <div data-testid="contextual-card">Contextual recommendation</div> : null
));
jest.mock("../components/SponsoredPlacement", () => function MockSponsoredPlacement(props) {
  const ReactModule = require("react");
  ReactModule.useEffect(() => {
    if (props.placement === "article_sidebar") {
      props.onAvailabilityChange?.(mockSponsorAvailable);
    }
  }, [props.onAvailabilityChange, props.placement]);

  if (!mockSponsorAvailable && props.suppressFallback) return null;
  return <div data-testid={`sponsor-${props.placement}`}>Genuine sponsor</div>;
});
jest.mock("../components/ui/toaster", () => ({ Toaster: () => null }));
jest.mock("../hooks/use-toast.js", () => ({ toast: jest.fn() }));

const article = {
  id: "article-1",
  title: "Cheshire business software update",
  summary: "A detailed local business update.",
  content: ["First paragraph.", "Second paragraph.", "Third paragraph.", "Fourth paragraph."].join("\n\n"),
  category: "Business",
  location: "Cheshire",
  image: "https://example.test/article.jpg",
  source: "Example source",
  source_url: "https://source.example/story",
  publishedDate: "2026-08-22T10:00:00Z",
};

let container;
let root;

beforeAll(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
});

beforeEach(() => {
  mockSponsorAvailable = false;
  mockSelectContextualRecommendation.mockReturnValue(null);
  mockLoadPublicArticle.mockResolvedValue(article);
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => [] });
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
  jest.clearAllMocks();
});

const renderArticle = async (width) => {
  Object.defineProperty(window, "innerWidth", { configurable: true, value: width });
  await act(async () => {
    root.render(
      <MemoryRouter initialEntries={["/article/article-1/test"]}>
        <Routes>
          <Route path="/article/:articleId/:slug" element={<ArticlePageV2 categories={[]} />} />
        </Routes>
      </MemoryRouter>
    );
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
};

test("desktop keeps a genuine sponsor after related editorial content and one inline newsletter", async () => {
  mockSponsorAvailable = true;
  await renderArticle(1440);

  const related = container.querySelector('[data-testid="related-articles"]');
  const sponsor = container.querySelector('[data-testid="sponsor-article_sidebar"]');
  expect(related).toBeTruthy();
  expect(sponsor).toBeTruthy();
  expect(related.compareDocumentPosition(sponsor) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  expect(container.querySelectorAll('[data-testid="inline-newsletter"]')).toHaveLength(1);
  expect(container.querySelector('[data-testid="sidebar-newsletter"]')).toBeNull();
  expect(container.textContent).not.toContain("Top Picks");
  expect(container.textContent).not.toContain("Useful guides");
});

test("desktop without sponsor uses one sidebar newsletter and no house fallback", async () => {
  await renderArticle(1440);

  expect(container.querySelector('[data-testid="sponsor-article_sidebar"]')).toBeNull();
  expect(container.querySelector('[data-testid="sidebar-newsletter"]')).toBeTruthy();
  expect(container.querySelector('[data-testid="inline-newsletter"]')).toBeNull();
});

test("mobile contextual recommendation suppresses sponsor and keeps one newsletter after full content", async () => {
  mockSponsorAvailable = true;
  mockSelectContextualRecommendation.mockReturnValue({ card_id: "accounting-card" });
  await renderArticle(390);

  expect(container.querySelector('[data-testid="contextual-card"]')).toBeNull();
  expect(container.querySelector('[data-testid="sponsor-article_mobile"]')).toBeNull();
  expect(container.querySelector('[data-testid="inline-newsletter"]')).toBeNull();

  const readMore = Array.from(container.querySelectorAll("button")).find((button) => button.textContent.includes("Read more"));
  await act(async () => {
    readMore.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });

  expect(container.querySelectorAll('[data-testid="contextual-card"]')).toHaveLength(1);
  expect(container.querySelector('[data-testid="sponsor-article_mobile"]')).toBeNull();
  expect(container.querySelectorAll('[data-testid="inline-newsletter"]')).toHaveLength(1);
  expect(container.querySelector('[data-testid="related-articles"]')).toBeTruthy();
});

test("mobile renders a genuine sponsor only when contextual targeting has no match", async () => {
  mockSponsorAvailable = true;
  await renderArticle(390);

  const readMore = Array.from(container.querySelectorAll("button")).find((button) => button.textContent.includes("Read more"));
  await act(async () => {
    readMore.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });

  expect(container.querySelectorAll('[data-testid="sponsor-article_mobile"]')).toHaveLength(1);
  expect(container.querySelector('[data-testid="contextual-card"]')).toBeNull();
  expect(container.querySelectorAll('[data-testid="inline-newsletter"]')).toHaveLength(1);
});
