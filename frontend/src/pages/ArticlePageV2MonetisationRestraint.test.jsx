import React, { act } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter, Route, Routes, useNavigate } from "react-router-dom";

import ArticlePageV2 from "./ArticlePageV2";

const mockLoadPublicArticle = jest.fn();
const mockSelectContextualRecommendation = jest.fn();
let mockSponsorKind = "none";

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
jest.mock("../components/CompactArticleCard", () => ({ article }) => <div data-testid="story-card">{article.title}</div>);
jest.mock("../components/homepage/TextHeadlineStrip", () => () => null);
jest.mock("../components/homepage/SectionHeader", () => ({ title }) => <h2>{title}</h2>);
jest.mock("../components/monetisation/ContextualRecommendationCard", () => ({ recommendation }) => (
  recommendation ? <div data-testid="contextual-card">Contextual recommendation</div> : null
));
jest.mock("../components/SponsoredPlacement", () => function MockSponsoredPlacement(props) {
  const ReactModule = require("react");
  const available = mockSponsorKind === "genuine" || (
    mockSponsorKind === "house" && !props.suppressFallback
  );
  ReactModule.useEffect(() => {
    if (props.placement === "article_sidebar") {
      props.onAvailabilityChange?.(available);
    }
  }, [available, props.onAvailabilityChange, props.placement]);

  if (!available && props.suppressFallback) return null;
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
let navigateArticle;
function NavigationProbe() {
  navigateArticle = useNavigate();
  return null;
}
const stories = Array.from({ length: 14 }, (_, i) => ({
  ...article, id: `story-${i}`, title: `Cheshire business update ${i}`,
  publishedDate: new Date(Date.UTC(2026, 7, 22, 10, 0, 14 - i)).toISOString(),
}));

beforeAll(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
});

beforeEach(() => {
  mockSponsorKind = "none";
  mockSelectContextualRecommendation.mockReturnValue(null);
  mockLoadPublicArticle.mockResolvedValue(article);
  global.fetch = jest.fn().mockImplementation(async (url) => ({
    ok: true, json: async () => String(url).includes('/api/articles?') ? stories : [],
  }));
  HTMLElement.prototype.scrollIntoView = jest.fn();
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
        <NavigationProbe />
        <Routes>
          <Route path="/article/:articleId/:slug" element={<ArticlePageV2 categories={[]} />} />
        </Routes>
      </MemoryRouter>
    );
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
};

test("desktop keeps a genuine sponsor after related editorial content and one inline newsletter", async () => {
  mockSponsorKind = "genuine";
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

const moreHeading = () => Array.from(container.querySelectorAll('article h2')).find(h => h.textContent === 'More stories');
const press = async (text) => {
  const button = Array.from(container.querySelectorAll('article button')).find(b => b.textContent.includes(text));
  expect(button).toBeTruthy();
  await act(async () => button.dispatchEvent(new MouseEvent('click', { bubbles: true })));
};
test('long mobile article withholds More stories until expansion', async () => {
  await renderArticle(390);
  expect(moreHeading()).toBeUndefined();
  expect(container.querySelector('article .prose').textContent).not.toContain('Fourth paragraph.');
  await press('Read more');
  expect(moreHeading()).toBeTruthy();
  expect(container.querySelector('article').textContent).toContain('Fourth paragraph.');
  expect(container.querySelectorAll('article [data-testid="story-card"]')).toHaveLength(4);
});
test('three-paragraph mobile article needs no expansion', async () => {
  mockLoadPublicArticle.mockResolvedValue({ ...article, content: 'One.\n\nTwo.\n\nThree.' });
  await renderArticle(390);
  expect(moreHeading()).toBeTruthy();
  expect(container.textContent).not.toContain('Read more…');
});
test('navigation resets mobile completion state', async () => {
  await renderArticle(390); await press('Read more');
  expect(moreHeading()).toBeTruthy();
  mockLoadPublicArticle.mockResolvedValue({ ...article, id: 'article-2' });
  await act(async () => { navigateArticle('/article/article-2/next'); await new Promise(resolve => setTimeout(resolve, 0)); });
  expect(moreHeading()).toBeUndefined();
  expect(container.textContent).toContain('Read more…');
});
test('639/640 transitions preserve completion visibility', async () => {
  await renderArticle(639); expect(moreHeading()).toBeUndefined();
  const resize = async width => act(async () => {
    Object.defineProperty(window, 'innerWidth', { configurable: true, value: width });
    window.dispatchEvent(new Event('resize'));
  });
  await resize(640); expect(moreHeading()).toBeTruthy();
  await resize(639); expect(moreHeading()).toBeUndefined();
  await press('Read more'); await resize(640); await resize(639);
  expect(moreHeading()).toBeTruthy();
});
test.each(['genuine', 'none', 'house', 'error'])('desktop sidebar restraint preserves %s sponsor state and main stories', async kind => {
  mockSponsorKind = kind; await renderArticle(1440);
  const aside = container.querySelector('aside');
  expect(aside.textContent).not.toContain('Latest');
  expect(aside.textContent).not.toContain('More from Cheshire Today');
  expect(aside.querySelector('[data-testid="related-articles"]')).toBeTruthy();
  expect(Boolean(aside.querySelector('[data-testid="sponsor-article_sidebar"]'))).toBe(kind === 'genuine');
  expect(Boolean(aside.querySelector('[data-testid="sidebar-newsletter"]'))).toBe(kind !== 'genuine');
  expect(moreHeading()).toBeTruthy();
  const titles = () => Array.from(container.querySelectorAll('article [data-testid="story-card"]')).map(e => e.textContent);
  expect(titles()).toEqual(stories.slice(0, 6).map(s => s.title));
  await press('Show more'); expect(titles()).toEqual(stories.slice(0, 12).map(s => s.title));
  await press('Show less'); expect(titles()).toEqual(stories.slice(0, 6).map(s => s.title));
});

test("desktop without sponsor uses one sidebar newsletter and no house fallback", async () => {
  await renderArticle(1440);

  expect(container.querySelector('[data-testid="sponsor-article_sidebar"]')).toBeNull();
  expect(container.querySelector('[data-testid="sidebar-newsletter"]')).toBeTruthy();
  expect(container.querySelector('[data-testid="inline-newsletter"]')).toBeNull();
});

test("mobile contextual recommendation suppresses sponsor and keeps one newsletter after full content", async () => {
  mockSponsorKind = "genuine";
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
  mockSponsorKind = "genuine";
  await renderArticle(390);

  const readMore = Array.from(container.querySelectorAll("button")).find((button) => button.textContent.includes("Read more"));
  await act(async () => {
    readMore.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });

  expect(container.querySelectorAll('[data-testid="sponsor-article_mobile"]')).toHaveLength(1);
  expect(container.querySelector('[data-testid="contextual-card"]')).toBeNull();
  expect(container.querySelectorAll('[data-testid="inline-newsletter"]')).toHaveLength(1);
});

test("mobile house-guide inventory renders no commercial card and keeps one newsletter", async () => {
  mockSponsorKind = "house";
  await renderArticle(390);

  const readMore = Array.from(container.querySelectorAll("button")).find((button) => button.textContent.includes("Read more"));
  await act(async () => {
    readMore.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });

  expect(container.querySelector('[data-testid="sponsor-article_mobile"]')).toBeNull();
  expect(container.querySelector('[data-testid="contextual-card"]')).toBeNull();
  expect(container.querySelectorAll('[data-testid="inline-newsletter"]')).toHaveLength(1);
});
