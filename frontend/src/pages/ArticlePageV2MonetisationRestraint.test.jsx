import React, { act } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter, Route, Routes, useNavigate } from "react-router-dom";

import ArticlePageV2 from "./ArticlePageV2";

const mockLoadPublicArticle = jest.fn();
const mockSelectContextualRecommendation = jest.fn();
let mockSponsorKind = "none";
let mockRelatedResults = [];
let mockUseRealRelated = false;

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
jest.mock("../components/RelatedArticles", () => function MockRelated({ articleId, onResultsChange, ...props }) {
  const ReactModule = require("react");
  ReactModule.useEffect(() => {
    if (!mockUseRealRelated) onResultsChange?.(mockRelatedResults, { articleId, loading: false });
  }, [articleId, onResultsChange]);
  if (mockUseRealRelated) {
    const RealRelated = jest.requireActual('../components/RelatedArticles').default;
    return <RealRelated {...props} articleId={articleId} onResultsChange={onResultsChange} />;
  }
  return <div data-testid="related-articles">Related articles</div>;
});
jest.mock("../components/SubscribeSection", () => () => <div data-testid="sidebar-newsletter">Sidebar newsletter</div>);
jest.mock("../components/JobsWidget", () => ({
  SubscribeInlineBanner: () => <div data-testid="inline-newsletter">Inline newsletter</div>,
}));
jest.mock("../components/CompactArticleCard", () => ({ article }) => <div data-testid="story-card">{article.title}</div>);
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
  mockRelatedResults = [];
  mockUseRealRelated = false;
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

test("UK article uses a neutral sidebar heading for mixed-category related results", async () => {
  mockUseRealRelated = true;
  mockLoadPublicArticle.mockResolvedValue({ ...article, category: "UK News" });
  const related = [
    { ...article, id: "related-uk", category: "UK News", title: "National transport update" },
    { ...article, id: "related-business", category: "Business", title: "Business investment update" },
  ];
  global.fetch.mockImplementation(async url => ({
    ok: true,
    json: async () => String(url).includes('/api/related-articles/')
      ? related : String(url).includes('/api/articles?') ? stories : [],
  }));
  await renderArticle(1440);

  const sidebar = container.querySelector('aside');
  expect(sidebar.querySelector('h3').textContent).toBe('Related stories');
  expect(sidebar.textContent).not.toContain('More in Finance');
  related.forEach(item => expect(sidebar.textContent).toContain(item.title));
  const requests = global.fetch.mock.calls
    .map(([url]) => String(url)).filter(url => url.includes('/api/related-articles/'));
  expect(requests).toHaveLength(1);
  expect(requests[0]).toMatch(/\/api\/related-articles\/article-1\?limit=6$/);
});

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

const further = () => Array.from(container.querySelectorAll('aside h3'))
  .find(h => h.textContent === 'Further reading')?.parentElement.parentElement;
const furtherTitles = () => Array.from(further()?.querySelectorAll('h4') || []).map(h => h.textContent);
const setStories = (list) => global.fetch.mockImplementation(async url => ({
  ok: true, json: async () => String(url).includes('/api/articles?') ? list : [],
}));
const extraStories = () => Array.from({ length: 24 }, (_, i) => ({
  ...stories[0], id: `extra-${i}`, title: `Cheshire business report ${i}`,
  publishedDate: new Date(Date.UTC(2026, 8, 1, 0, 0, 30 - i)).toISOString(),
}));

test('Further reading reserves twelve main stories, excludes related, and caps at four without fetching', async () => {
  const list = extraStories();
  mockRelatedResults = [list[12]];
  setStories(list);
  await renderArticle(1440);
  expect(furtherTitles()).toEqual(list.slice(13, 17).map(a => a.title));
  expect(further().querySelector('img')).toBeNull();
  expect(further().textContent).not.toContain('min read');
  expect(global.fetch.mock.calls.filter(([url]) => String(url).includes('/api/articles?'))).toHaveLength(1);
  expect(global.fetch.mock.calls.map(([url]) => String(url))).toHaveLength(2); // stories + existing guide request
  const titles = () => Array.from(container.querySelectorAll('article [data-testid="story-card"]')).map(e => e.textContent);
  expect(titles()).toEqual(list.slice(0, 6).map(a => a.title));
  await press('Show more');
  expect(titles()).toEqual(list.slice(0, 12).map(a => a.title));
  expect(furtherTitles()).toEqual(list.slice(13, 17).map(a => a.title));
});

test('Further reading excludes all ID aliases and normalised titles without mutating main inventory', async () => {
  const list = extraStories();
  list[12] = { ...list[12], _id: article.id };
  list[13] = { ...list[13], title: `  ${list[0].title.toUpperCase().replaceAll(' ', '   ')}  ` };
  list[14] = { ...list[14], _id: 'related-alias' };
  list[16] = { ...list[16], title: list[15].title.toUpperCase() };
  list[17] = { ...list[17], title: article.title };
  mockRelatedResults = [{ id: 'related-alias', title: 'Another related story' }];
  const before = JSON.stringify(list);
  setStories(list);
  await renderArticle(1440);
  expect(furtherTitles()).toEqual([15, 18, 19, 20].map(i => list[i].title));
  expect(JSON.stringify(list)).toBe(before);
});

test.each([12, 14])('Further reading with %s candidates omits empty block or shows only available items', async count => {
  setStories(extraStories().slice(0, count));
  await renderArticle(1440);
  if (count === 12) expect(further()).toBeUndefined();
  else expect(furtherTitles()).toHaveLength(2);
});

test('navigation resets related exclusions for the next article', async () => {
  const list = extraStories();
  mockRelatedResults = [list[12]];
  setStories(list);
  await renderArticle(1440);
  expect(furtherTitles()).not.toContain(list[12].title);
  mockRelatedResults = [];
  mockLoadPublicArticle.mockResolvedValue({ ...article, id: 'article-2' });
  await act(async () => { navigateArticle('/article/article-2/next'); await new Promise(r => setTimeout(r, 0)); });
  expect(furtherTitles()[0]).toBe(list[12].title);
});

test.each([390, 768, 1023, 1024, 1440])('Further reading stays inside existing lg-only sidebar at %spx', async width => {
  setStories(extraStories());
  await renderArticle(width);
  expect(further()).toBeTruthy();
  expect(further().closest('aside').className).toContain('hidden lg:block');
  expect(container.querySelector('article').textContent).not.toContain('Further reading');
  expect(global.fetch.mock.calls.filter(([url]) => String(url).includes('/api/articles?'))).toHaveLength(1);
});

test.each(['genuine', 'none', 'house', 'error'])('Further reading follows unchanged %s sponsor/newsletter opportunity', async kind => {
  mockSponsorKind = kind;
  setStories(extraStories());
  await renderArticle(1440);
  const opportunity = container.querySelector(kind === 'genuine' ? '[data-testid="sponsor-article_sidebar"]' : '[data-testid="sidebar-newsletter"]');
  expect(further()).toBeTruthy();
  expect(opportunity.compareDocumentPosition(further()) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  expect(container.querySelectorAll('[data-testid="inline-newsletter"], [data-testid="sidebar-newsletter"]')).toHaveLength(1);
});

test.each(['success', 'empty', 'error'])('real RelatedArticles %s uses only existing requests and waits for exclusions', async outcome => {
  mockUseRealRelated = true;
  const list = extraStories();
  let resolveRelated;
  global.fetch.mockImplementation(url => {
    if (String(url).includes('/api/related-articles/')) return new Promise(r => { resolveRelated = r; });
    return Promise.resolve({ ok: true, json: async () => String(url).includes('/api/articles?') ? list : [] });
  });
  const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
  try {
    await renderArticle(1440);
    expect(further()).toBeUndefined();
    await act(async () => resolveRelated({ ok: outcome !== 'error', json: async () => outcome === 'success' ? [list[12]] : [] }));
    expect(furtherTitles()[0]).toBe(list[outcome === 'success' ? 13 : 12].title);
    expect(global.fetch).toHaveBeenCalledTimes(3); // existing stories, related and guides only
    expect(global.fetch.mock.calls.every(([, options]) => !options?.method || options.method === 'GET')).toBe(true);
  } finally { errorSpy.mockRestore(); }
});
