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
jest.mock("../components/SponsoredPlacement", () => () => null);
jest.mock("../components/homepage/HeroMonetisationStrip", () => () => null);
jest.mock("../components/AffiliateWidgets", () => ({
  AffiliateWidgetSidebar: () => null,
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
      <article key={item.id} data-card-id={item.id}>{item.title}</article>
    ))}
  </section>
));
jest.mock("../components/homepage/SectionHeader", () => ({ title, meta }) => (
  <h2 data-section-title={title}>{title}{meta ? ` ${meta}` : ""}</h2>
));
jest.mock("../components/CompactArticleCard", () => ({ article }) => (
  <article data-card-id={article.id}>{article.title}</article>
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

const renderHomepage = async (articles) => {
  global.fetch = jest
    .fn()
    .mockResolvedValueOnce({
      ok: true,
      json: async () => articles,
    })
    .mockResolvedValueOnce({
      ok: true,
      json: async () => [],
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

test("dead Most Read allocation reserves nothing and Latest expands deterministically", async () => {
  const articles = Array.from({ length: 33 }, (_, index) => makeArticle(index));
  await renderHomepage(articles);

  expect(container.textContent).not.toContain("Most Read");

  const latest = sectionByTitle("Latest");
  const moreStories = sectionByTitle("More stories");

  expect(sectionCards("Latest")).toHaveLength(12);
  expect(sectionCards("Latest").map((card) => card.textContent)).toEqual(
    articles.slice(0, 12).map((article) => article.title)
  );
  expect(sectionCards("More stories")).toHaveLength(12);

  await clickButton(latest, "Show more");
  expect(sectionCards("Latest")).toHaveLength(33);
  expect(sectionCards("Latest").map((card) => card.textContent)).toEqual(
    articles.map((article) => article.title)
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
    articles[0].title,
    duplicateTitle,
    articles[3].title,
  ]);
  expect(new Set(latestCards.map((card) => card.getAttribute("data-card-id"))).size)
    .toBe(latestCards.length);
  expect(sectionByTitle("Latest").textContent).not.toContain("Show more");
  expect(container.textContent).not.toContain("Police investigate a burglary");
  expect(container.textContent).not.toContain("Duplicate identifier should not render");
});
