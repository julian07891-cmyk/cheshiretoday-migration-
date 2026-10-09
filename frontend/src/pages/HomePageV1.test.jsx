import React, { act } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter } from "react-router-dom";
import HomePageV1 from "./HomePageV1";

jest.mock("react-helmet-async", () => ({
  Helmet: ({ children }) => <>{children}</>,
}));
jest.mock("../components/homepage/HomepageLayout", () => ({ children }) => <>{children}</>);
jest.mock("../components/homepage/HomepageHeader", () => () => <header>Cheshire Today</header>);
jest.mock("../components/NewsFooter", () => () => <footer>Footer</footer>);
jest.mock("../components/SubscribeSection", () => () => null);
jest.mock("../components/JobsWidget", () => ({
  SubscribeInlineBanner: () => null,
}));
jest.mock("../components/SponsoredPlacement", () => ({ placement }) => <div data-sponsor-placement={placement} />);
jest.mock("../components/homepage/HeroMonetisationStrip", () => ({
  __esModule: true,
  ...jest.requireActual("../components/homepage/HeroMonetisationStrip"),
  default: props => <div data-guide-strip={JSON.stringify(props)} />,
}));
jest.mock("../components/AffiliateWidgets", () => ({
  AffiliateWidgetSidebar: () => <div data-amazon-sidebar />,
}));
jest.mock("../components/homepage/HeroStoryCard", () => (props) => (
  <article data-hero-title={props.headline}>{props.headline}</article>
));
jest.mock("../components/homepage/TopStoriesGrid", () => ({ stories }) => (
  <div data-top-stories>
    {stories.map((story) => (
      <article key={story.id} data-card-id={story.id}>{story.title}</article>
    ))}
  </div>
));
jest.mock("../components/homepage/LeadSection", () => ({ title, items }) => (
  <section data-lead-section={title}>
    {items.map((item) => (
      <article key={item.id} data-card-id={item.id} data-card-category={item.category}>{item.title}</article>
    ))}
  </section>
));
jest.mock("../components/homepage/SectionHeader", () => ({ title, meta }) => (
  <h2 data-section-title={title}>{title}{meta ? ` ${meta}` : ""}</h2>
));
jest.mock("../components/CompactArticleCard", () => ({ article, variant }) => (
  <article data-card-id={article.id} data-card-variant={variant || "default"}>{article.title}</article>
));
jest.mock("../components/homepage/TextHeadlineStrip", () => ({ articles }) => (
  <div data-headline-strip>
    {articles.map((article) => (
      <article key={article.id} data-card-id={article.id}>{article.title}</article>
    ))}
  </div>
));

const makeArticle = (index, overrides = {}) => ({
  id: `article-${index}`,
  title: `Cheshire council service update ${index}`,
  summary: "A useful Cheshire council and public services update.",
  content: "A".repeat(1300),
  category: "Local News",
  scope: "cheshire",
  image: `https://example.com/image-${index}.jpg`,
  publishedDate: new Date(Date.UTC(2026, 6, 23, 12, 0, 0) - index * 60000).toISOString(),
  ...overrides,
});

let container;
let root;

beforeAll(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
});

beforeEach(() => {
  Object.defineProperty(window, "innerWidth", {
    configurable: true,
    value: 1200,
  });
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root?.unmount());
  container?.remove();
  root = null;
  container = null;
  jest.restoreAllMocks();
});

const renderHomepage = async (articles, guides = []) => {
  global.fetch = jest
    .fn()
    .mockResolvedValueOnce({
      ok: true,
      json: async () => articles,
    })
    .mockResolvedValueOnce({
      ok: true,
      json: async () => guides,
    });

  await act(async () => {
    root.render(
      <MemoryRouter>
        <HomePageV1 />
      </MemoryRouter>
    );
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
};

const sectionByTitle = (title) =>
  Array.from(container.querySelectorAll("section")).find(
    (section) => section.querySelector(`[data-section-title="${title}"]`)
  );

const sectionCards = (title) =>
  Array.from(sectionByTitle(title)?.querySelectorAll("[data-card-id]") || []);

const clickButton = async (section, label) => {
  const button = Array.from(section.querySelectorAll("button")).find(
    (candidate) => candidate.textContent === label
  );
  expect(button).toBeTruthy();
  await act(async () => {
    button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
};

const sidebarCards = title => Array.from(container.querySelectorAll(
  `aside [data-lead-section="${title}"] [data-card-id]`
));

const SIDEBAR_NOW = Date.parse("2026-10-08T12:00:00.000Z");
const hoursBeforeSidebarNow = hours => new Date(SIDEBAR_NOW - hours * 60 * 60 * 1000).toISOString();

const makeNeutralRecentArticles = () => Array.from({ length: 4 }, (_, index) => makeArticle(index, {
  title: `Cheshire public services briefing ${index}`,
  publishedDate: hoursBeforeSidebarNow(index + 1),
  created_at: hoursBeforeSidebarNow(index + 1),
}));

const makeSidebarArticle = (index, module, hoursAgo, overrides = {}) => {
  const moduleDefaults = {
    Business: {
      category: "Business",
      scope: "uk",
      title: `Company manufacturing investment update ${index}`,
      summary: "Companies announced investment, jobs and manufacturing plans.",
    },
    AI: {
      category: "AI & Tech",
      scope: "uk",
      title: `Artificial intelligence software update ${index}`,
      summary: "An artificial intelligence company released a software update.",
    },
    Finance: {
      category: "Finance",
      scope: "uk",
      title: `Mortgage savings update ${index}`,
      summary: "Mortgage and savings interest rate information for customers.",
    },
  }[module];

  return makeArticle(index, {
    ...moduleDefaults,
    publishedDate: hoursBeforeSidebarNow(hoursAgo),
    created_at: hoursBeforeSidebarNow(hoursAgo),
    ...overrides,
  });
};

beforeEach(() => {
  jest.spyOn(Date, "now").mockReturnValue(SIDEBAR_NOW);
});

test.each([1440, 390])("Finance omits unrelated fallback stories at %ipx", async width => {
  Object.defineProperty(window, 'innerWidth', { configurable: true, value: width });
  await renderHomepage(Array.from({ length: 30 }, (_, index) => makeArticle(index)));
  expect(sidebarCards('Finance')).toHaveLength(0);
  expect(container.querySelector('aside [data-lead-section="Finance"]')).toBeNull();
  expect(container.querySelector('aside').classList.contains('hidden')).toBe(true);
  expect(container.querySelector('aside').classList.contains('lg:block')).toBe(true);
});

test("Finance retains a smaller eligible pool without filling unrelated slots", async () => {
  const articles = [
    ...makeNeutralRecentArticles(),
    ...Array.from({ length: 6 }, (_, index) => makeArticle(index + 4, {
      publishedDate: hoursBeforeSidebarNow(10 + index),
      created_at: hoursBeforeSidebarNow(10 + index),
    })),
  ];
  for (let index = 10; index < 13; index += 1) {
    articles[index] = makeArticle(index, {
      title: `Savings interest update ${index}`, category: 'Finance', section: 'money',
      publishedDate: hoursBeforeSidebarNow(30 + index),
      created_at: hoursBeforeSidebarNow(30 + index),
    });
  }
  await renderHomepage(articles);
  const cards = sidebarCards('Finance');
  expect(cards.map(card => card.textContent)).toEqual(
    articles.slice(10, 13).map(article => article.title)
  );
  expect(cards[0].dataset.cardCategory).toBe('Finance');
  expect(new Set(cards.map(card => card.dataset.cardId)).size).toBe(cards.length);
});

test("Finance preserves capped housing enrichment without unrelated fallback", async () => {
  const articles = [
    ...makeNeutralRecentArticles(),
    ...Array.from({ length: 26 }, (_, index) => makeArticle(index + 4, {
      publishedDate: hoursBeforeSidebarNow(10 + index),
      created_at: hoursBeforeSidebarNow(10 + index),
    })),
  ];
  for (let index = 15; index < 20; index += 1) {
    articles[index] = makeArticle(index, {
      title: `Housing development update ${index}`,
      section: 'housing',
      publishedDate: hoursBeforeSidebarNow(30 + index),
      created_at: hoursBeforeSidebarNow(30 + index),
    });
  }
  await renderHomepage(articles);
  expect(sidebarCards('Finance').map(card => card.textContent)).toEqual(
    articles.slice(15, 17).map(item => item.title)
  );
});

test("Business and AI sidebar pools retain their own stories while Finance stays empty", async () => {
  const articles = Array.from({ length: 12 }, (_, index) => makeArticle(index));
  for (let index = 12; index < 36; index += 1) {
    articles.push(makeArticle(index, index < 24 ? {
      category: 'Business', title: `Company manufacturing investment ${index}`, scope: 'uk',
      publishedDate: hoursBeforeSidebarNow(12 + index), created_at: hoursBeforeSidebarNow(12 + index),
    } : {
      category: 'AI & Tech', title: `Artificial intelligence software update ${index}`, scope: 'uk',
      publishedDate: hoursBeforeSidebarNow(12 + index), created_at: hoursBeforeSidebarNow(12 + index),
    }));
  }
  await renderHomepage(articles);
  expect(sidebarCards('Business')).toHaveLength(3);
  expect(sidebarCards('AI & Tech')).toHaveLength(6);
  expect(sidebarCards('Business').every(card => card.textContent.startsWith('Company manufacturing'))).toBe(true);
  expect(sidebarCards('AI & Tech').every(card => card.textContent.startsWith('Artificial intelligence'))).toBe(true);
  expect(sidebarCards('Finance')).toHaveLength(0);
});

test("Finance does not treat vaccination rates or save-our-school campaigns as money stories", async () => {
  const articles = [
    ...makeNeutralRecentArticles(),
    makeSidebarArticle(10, "Finance", 10),
    makeSidebarArticle(11, "Finance", 11),
    makeArticle(12, {
      title: "Childhood vaccination rates fall below public-health target",
      summary: "Health officials discussed vaccination rates across the region.",
      category: "UK News",
      scope: "uk",
      publishedDate: hoursBeforeSidebarNow(12),
      created_at: hoursBeforeSidebarNow(12),
    }),
    makeArticle(13, {
      title: "Parents launch save our school campaign",
      summary: "Families urged councillors to save their community school.",
      category: "UK News",
      scope: "uk",
      publishedDate: hoursBeforeSidebarNow(13),
      created_at: hoursBeforeSidebarNow(13),
    }),
  ];

  await renderHomepage(articles);

  const financeTitles = sidebarCards("Finance").map(card => card.textContent);
  expect(financeTitles).not.toContain(articles[6].title);
  expect(financeTitles).not.toContain(articles[7].title);
});

test.each([
  ["Mortgage rate falls for first-time buyers", "Mortgage rates changed for first-time buyers.", "Finance", undefined],
  ["Bank cuts interest rate on home loans", "The bank reduced its interest rate.", "Finance", undefined],
  ["New ISA and savings options announced", "New ISA and savings accounts were announced.", "Finance", undefined],
  ["Council tax changes take effect next month", "Council tax bills will change.", "Finance", "tax"],
  ["Planning application approved for new homes", "The housing development includes 80 homes.", "Local News", "planning"],
])("Finance retains genuine context: %s", async (title, summary, category, section) => {
  const candidate = makeArticle(24, {
    title,
    summary,
    category,
    section,
    scope: category === "Local News" ? "cheshire" : "uk",
    publishedDate: hoursBeforeSidebarNow(16),
    created_at: hoursBeforeSidebarNow(16),
  });
  const articles = [
    ...makeNeutralRecentArticles(),
    makeSidebarArticle(20, "Business", 8, { title: "Company profits rise after manufacturing investment" }),
    makeSidebarArticle(21, "Business", 9, { title: "Industry company reports revenue growth" }),
    makeArticle(22, {
      title: "Housing development approved for town centre",
      summary: "A planning application for homes was approved.",
      category: "Local News",
      scope: "cheshire",
      publishedDate: hoursBeforeSidebarNow(10),
      created_at: hoursBeforeSidebarNow(10),
    }),
    candidate,
  ];

  await renderHomepage(articles);

  expect(sidebarCards("Finance").map(card => card.textContent)).toContain(candidate.title);
});

test.each([
  ["Business", 3],
  ["AI & Tech", 6],
  ["Finance", 6],
])("%s prefers qualified published stories from the first 48 hours", async (section, capacity) => {
  const module = section === "AI & Tech" ? "AI" : section;
  const articles = [
    ...makeNeutralRecentArticles(),
    ...Array.from({ length: capacity + 3 }, (_, index) =>
      makeSidebarArticle(100 + index, module, 12 + index)
    ),
    ...Array.from({ length: capacity }, (_, index) =>
      makeSidebarArticle(200 + index, module, 72 + index)
    ),
  ];

  await renderHomepage(articles);

  const selectedTitles = sidebarCards(section).map(card => card.textContent);
  expect(selectedTitles).toHaveLength(capacity);
  expect(selectedTitles.every(title => articles.slice(4, 4 + capacity + 3).some(article => article.title === title))).toBe(true);
});

test.each([
  ["Business", "Business", 3, 2],
  ["AI & Tech", "AI", 6, 2],
  ["Finance", "Finance", 6, 2],
])("%s widens through seven days but does not use older stories to fill capacity", async (section, module, capacity, recentCount) => {
  const recent = Array.from({ length: recentCount + (module === "Business" ? 1 : module === "AI" ? 1 : 0) }, (_, index) =>
    makeSidebarArticle(300 + index, module, 24 + index)
  );
  const withinSevenDays = Array.from({ length: module === "Business" ? 1 : 2 }, (_, index) =>
    makeSidebarArticle(400 + index, module, 72 + index * 24)
  );
  const older = Array.from({ length: capacity + 2 }, (_, index) =>
    makeSidebarArticle(500 + index, module, 8 * 24 + index)
  );
  const articles = [...makeNeutralRecentArticles(), ...recent, ...withinSevenDays, ...older];

  await renderHomepage(articles);

  const selectedTitles = sidebarCards(section).map(card => card.textContent);
  expect(selectedTitles).toEqual(expect.arrayContaining(withinSevenDays.map(article => article.title)));
  for (const article of older) expect(selectedTitles).not.toContain(article.title);
  expect(selectedTitles.length).toBeLessThan(capacity);
});

test.each([
  ["Business", "Business"],
  ["AI & Tech", "AI"],
  ["Finance", "Finance"],
])("%s uses publishedDate rather than recent import metadata for its seven-day boundary", async (section, module) => {
  const staleButRecentlyImported = Array.from({ length: 4 }, (_, index) =>
    makeSidebarArticle(600 + index, module, 8 * 24 + index, {
      created_at: hoursBeforeSidebarNow(index + 1),
      id: `6ac7777${index}0000000000000000`,
    })
  );
  const articles = [
    ...makeNeutralRecentArticles(),
    ...Array.from({ length: module === "Business" ? 2 : module === "AI" ? 1 : 0 }, (_, index) =>
      makeSidebarArticle(610 + index, module, 24 + index)
    ),
    ...staleButRecentlyImported,
  ];

  await renderHomepage(articles);

  const selectedTitles = sidebarCards(section).map(card => card.textContent);
  for (const article of staleButRecentlyImported) expect(selectedTitles).not.toContain(article.title);
});

test("sidebar freshness contract preserves Hero, Top Stories, editorial filtering, dedupe and shared requests", async () => {
  const duplicateTitle = "Company manufacturing investment duplicate";
  const crimeStory = makeSidebarArticle(700, "Business", 10, {
    title: "Company director jailed after crown court trial",
    summary: "The court sentenced the company director after a trial.",
  });
  const articles = [
    ...makeNeutralRecentArticles(),
    makeSidebarArticle(701, "Business", 8, { title: duplicateTitle }),
    makeSidebarArticle(702, "Business", 9, { title: duplicateTitle }),
    crimeStory,
    ...Array.from({ length: 6 }, (_, index) => makeSidebarArticle(710 + index, "AI", 12 + index)),
  ];

  await renderHomepage(articles);

  expect(container.querySelector("[data-hero-title]")).toBeTruthy();
  expect(container.querySelectorAll("[data-top-stories] [data-card-id]").length).toBeGreaterThan(0);
  expect(container.textContent).not.toContain(crimeStory.title);
  const renderedSidebarIds = Array.from(container.querySelectorAll("aside [data-card-id]"))
    .map(card => card.dataset.cardId);
  expect(new Set(renderedSidebarIds).size).toBe(renderedSidebarIds.length);
  expect(global.fetch).toHaveBeenCalledTimes(2);
  expect(global.fetch.mock.calls[0][0]).toMatch(/\/api\/articles\?limit=80$/);
  expect(global.fetch.mock.calls.filter(([url]) => String(url).includes("/api/articles"))).toHaveLength(1);
});

test("dead Most Read allocation reserves nothing and Latest expands deterministically", async () => {
  const articles = Array.from({ length: 33 }, (_, index) => makeArticle(index));
  await renderHomepage(articles);

  expect(container.textContent).not.toContain("Most Read");

  const latest = sectionByTitle("Latest");
  const moreStories = sectionByTitle("More stories");

  expect(sectionCards("Latest")).toHaveLength(12);
  expect(sectionCards("Latest").map((card) => card.textContent)).toEqual(
    articles.slice(1, 13).map((article) => article.title)
  );
  expect(sectionCards("More stories")).toHaveLength(12);

  await clickButton(latest, "Show more");
  expect(sectionCards("Latest")).toHaveLength(32);
  expect(sectionCards("Latest").map((card) => card.textContent)).toEqual(
    articles.slice(1).map((article) => article.title)
  );
  expect(latest.textContent).not.toContain("Show more");

  await clickButton(moreStories, "Show more");
  expect(sectionCards("More stories")).toHaveLength(27);
  expect(moreStories.textContent).not.toContain("Show more");

  const exclusiveIds = new Set([
    container.querySelector("[data-hero-title]")?.getAttribute("data-hero-title"),
    ...Array.from(container.querySelectorAll("[data-top-stories] [data-card-id]")).map(
      (card) => card.textContent
    ),
  ]);
  for (const card of sectionCards("More stories")) {
    expect(exclusiveIds.has(card.textContent)).toBe(false);
  }
});

test("Latest uses the editorial card variant before and after the guide strip", async () => {
  const articles = Array.from({ length: 12 }, (_, index) => makeArticle(index));
  await renderHomepage(articles);

  const latest = sectionByTitle("Latest");
  const compactCards = Array.from(latest.querySelectorAll("[data-card-variant]"));

  expect(compactCards.length).toBeGreaterThan(0);
  expect(compactCards.every((card) => card.getAttribute("data-card-variant") === "editorial")).toBe(true);
});

test("guide strips retain selection props and distinct measurement placements", async () => {
  await renderHomepage(Array.from({ length: 12 }, (_, index) => makeArticle(index)));
  const strips = Array.from(container.querySelectorAll('[data-guide-strip]')).map(el => JSON.parse(el.dataset.guideStrip));
  expect(strips.slice(0, 2)).toEqual([
    { limit: 2, compact: true, focus: 'finance', placement: 'homepage_finance_guides' },
    { start: 0, limit: 2, compact: true, eyebrow: 'Popular guides', title: 'More practical next steps', excludeFocus: 'finance', placement: 'homepage_popular_guides' },
  ]);
  expect(strips[2]).toEqual(expect.objectContaining({
    limit: 1,
    compact: true,
    sidebar: true,
    placement: 'homepage_sidebar_guide',
    eyebrow: 'Useful guide',
  }));
  expect(strips[2].excludeHrefs).toHaveLength(4);
  expect(new Set(strips[2].excludeHrefs).size).toBe(4);
  expect(container.querySelector('[data-amazon-sidebar]')).toBeNull();
  expect(container.querySelector('[data-sponsor-placement="homepage_sidebar"]')).not.toBeNull();
});

test("mobile homepage does not mount guide strips", async () => {
  Object.defineProperty(window, "innerWidth", {
    configurable: true,
    value: 390,
  });

  await renderHomepage(Array.from({ length: 12 }, (_, index) => makeArticle(index)));

  expect(container.querySelectorAll("[data-guide-strip]")).toHaveLength(0);
  expect(container.querySelector('[data-amazon-sidebar]')).toBeNull();
});

test.each([390, 768, 1023])('hidden sidebar has no guide mounted at %ipx', async width => {
  Object.defineProperty(window, 'innerWidth', { configurable: true, value: width });
  await renderHomepage(Array.from({ length: 12 }, (_, index) => makeArticle(index)));
  expect(container.querySelector('aside [data-guide-strip]')).toBeNull();
  expect(container.querySelector('[data-amazon-sidebar]')).toBeNull();
});

test('sidebar receives only published guide destinations from the existing request', async () => {
  await renderHomepage(Array.from({ length: 12 }, (_, index) => makeArticle(index)), [
    { slug: 'best-accounting-software-uk', status: 'published' },
    { slug: 'draft-guide', status: 'draft' },
    { status: 'published' },
  ]);
  const props = JSON.parse(container.querySelector('aside [data-guide-strip]').dataset.guideStrip);
  expect(props.allowedHrefs).toEqual(['/guides/best-accounting-software-uk']);
  expect(props.limit).toBe(1);
  expect(global.fetch).toHaveBeenCalledTimes(2);
  expect(global.fetch.mock.calls[1][0]).toMatch(/\/api\/authority-pages\?limit=10&status=published$/);
});

test("Latest keeps approved unique stories only and hides an unnecessary toggle", async () => {
  const duplicateTitle = "Cheshire council budget update";
  const articles = [
    makeArticle(0),
    makeArticle(1, { title: duplicateTitle }),
    makeArticle(2, { title: duplicateTitle }),
    makeArticle(3),
    makeArticle(3, { title: "Duplicate identifier should not render" }),
    makeArticle(4, {
      title: "Police investigate a burglary",
      summary: "A suspect was arrested and charged at court.",
    }),
  ];

  await renderHomepage(articles);

  const latestCards = sectionCards("Latest");
  expect(latestCards.map((card) => card.textContent)).toEqual([
    duplicateTitle,
    articles[3].title,
  ]);
  expect(latestCards.map((card) => card.textContent)).not.toContain(
    container.querySelector("[data-hero-title]")?.getAttribute("data-hero-title")
  );
  expect(new Set(latestCards.map((card) => card.getAttribute("data-card-id"))).size)
    .toBe(latestCards.length);
  expect(sectionByTitle("Latest").textContent).not.toContain("Show more");
  expect(container.textContent).not.toContain("Police investigate a burglary");
  expect(container.textContent).not.toContain("Duplicate identifier should not render");
});
