import React, { act } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import { createRoot } from "react-dom/client";
import CategoryPage from "./CategoryPage";
import LocationPage from "./LocationPage";
import { CATEGORY_HUBS } from "../config/publicHubs";
import {
  getDisplayCategoryForPillar,
  getPrimaryPillar,
} from "../utils/editorialPolicy";

jest.mock("./NewsHeader", () => () => <header>Cheshire Today</header>);
jest.mock("./NewsFooter", () => () => <footer>Footer</footer>);
jest.mock("./ui/button", () => ({
  Button: ({ children, ...props }) => <button {...props}>{children}</button>,
}));
jest.mock("./ui/badge", () => ({
  Badge: ({ children }) => <span>{children}</span>,
}));
jest.mock("./ui/toaster", () => ({
  Toaster: () => null,
}));
jest.mock("react-helmet-async", () => ({
  HelmetProvider: ({ children }) => <>{children}</>,
  Helmet: ({ children }) => <>{children}</>,
}));

const publicArticle = {
  id: "6a619fe3d25f3963602b219a",
  articleId: "6a619fe3d25f3963602b219a",
  slug: "cheshire-investment",
  title: "Cheshire investment creates new jobs",
  summary: "A useful public summary.",
  content: "A useful public article.",
  category: "Business",
  source: "Cheshire Today",
  image: "https://example.com/image.jpg",
  publishedDate: "2026-07-23T09:00:00Z",
};

let container;
let root;

beforeAll(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
});

const renderRoute = async (path, pattern, element) => {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
  await act(async () => {
    root.render(
      <HelmetProvider>
        <MemoryRouter initialEntries={[path]}>
          <Routes>
            <Route path={pattern} element={element} />
          </Routes>
        </MemoryRouter>
      </HelmetProvider>
    );
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
};

afterEach(() => {
  act(() => root?.unmount());
  container?.remove();
  root = null;
  container = null;
  jest.restoreAllMocks();
});

test("supported category renders articles and self-canonical metadata", async () => {
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ articles: [publicArticle], total: 1 }),
  });

  await renderRoute(
    "/category/business",
    "/category/business",
    <CategoryPage categorySlug="business" />
  );

  expect(container.textContent).toContain(publicArticle.title);
  expect(container.querySelector("h1")?.textContent).toBe("Business");
  expect(container.querySelector('link[rel="canonical"]')?.href).toBe(
    "https://cheshiretoday.co.uk/category/business"
  );
});

test("supported location renders articles and self-canonical metadata", async () => {
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ articles: [publicArticle], total: 1 }),
  });

  await renderRoute("/chester", "/:location", <LocationPage />);

  expect(container.textContent).toContain(publicArticle.title);
  expect(container.querySelector("h1")?.textContent.trim()).toBe("Chester News");
  expect(container.querySelector('link[rel="canonical"]')?.href).toBe(
    "https://cheshiretoday.co.uk/chester"
  );
});

test("empty supported category renders an explicit empty state", async () => {
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ articles: [], total: 0 }),
  });

  await renderRoute(
    "/category/finance",
    "/category/finance",
    <CategoryPage categorySlug="finance" />
  );

  expect(container.textContent).toContain(
    "No public articles are currently available for Finance"
  );
  expect(container.textContent).not.toContain("Latest News");
});

test("displayed count and cards reflect editorial filtering", async () => {
  const filteredArticle = {
    ...publicArticle,
    id: "6a619fe3d25f3963602b219b",
    articleId: "6a619fe3d25f3963602b219b",
    title: "Police investigate a burglary",
  };
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({
      articles: [publicArticle, filteredArticle],
      total: 2,
    }),
  });

  await renderRoute(
    "/category/business",
    "/category/business",
    <CategoryPage categorySlug="business" />
  );

  expect(container.textContent).toContain("1 public articles");
  expect(container.querySelectorAll("article")).toHaveLength(1);
  expect(container.textContent).not.toContain(filteredArticle.title);
});

test("all filtered articles produce a zero count and explicit empty state", async () => {
  const filteredArticle = {
    ...publicArticle,
    title: "Police investigate a burglary",
  };
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ articles: [filteredArticle], total: 1 }),
  });

  await renderRoute(
    "/category/business",
    "/category/business",
    <CategoryPage categorySlug="business" />
  );

  expect(container.textContent).toContain("0 public articles");
  expect(container.querySelectorAll("article")).toHaveLength(0);
  expect(container.textContent).toContain(
    "No public articles are currently available for Business"
  );
});

test("article image uses the article title as accessible alt text", async () => {
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ articles: [publicArticle], total: 1 }),
  });

  await renderRoute(
    "/category/business",
    "/category/business",
    <CategoryPage categorySlug="business" />
  );

  expect(container.querySelector("article img")?.getAttribute("alt")).toBe(
    publicArticle.title
  );
});

test("public category labels and stable URLs match the approved taxonomy", () => {
  expect(
    CATEGORY_HUBS.map(
      ({ slug, label, canonicalCategory, aliases }) => ({
        slug,
        label,
        canonicalCategory,
        aliases,
      })
    )
  ).toEqual([
    {
      slug: "local-news",
      label: "Local",
      canonicalCategory: "Local News",
      aliases: ["Local"],
    },
    {
      slug: "uk-news",
      label: "UK",
      canonicalCategory: "UK News",
      aliases: ["UK"],
    },
    {
      slug: "business",
      label: "Business",
      canonicalCategory: "Business",
      aliases: ["Economy", "Economic"],
    },
    {
      slug: "finance",
      label: "Finance",
      canonicalCategory: "Finance",
      aliases: ["Tax", "Property", "Property & Tax", "Money"],
    },
    {
      slug: "ai-tech",
      label: "AI & Tech",
      canonicalCategory: "AI & Tech",
      aliases: ["AI", "Tech", "Technology"],
    },
  ]);
});

test.each([
  ["Finance", "Finance"],
  ["Tax", "Finance"],
  ["Property", "Finance"],
  ["Property & Tax", "Finance"],
  ["Money", "Finance"],
  ["Business", "Business"],
  ["Economy", "Business"],
  ["Economic", "Business"],
  ["AI & Tech", "AI & Tech"],
  ["AI", "AI & Tech"],
  ["Tech", "AI & Tech"],
  ["Technology", "AI & Tech"],
])("%s remains in its specialist homepage pillar despite UK scope", (category, expected) => {
  const article = { category, scope: "uk", title: "A national update" };
  expect(getPrimaryPillar(article)).toBe(expected);
  expect(getDisplayCategoryForPillar(article)).toBe(expected);
});

test("Local and UK use their reader-facing labels", () => {
  expect(getDisplayCategoryForPillar({ category: "Local News" })).toBe("Local");
  expect(getDisplayCategoryForPillar({ category: "UK News" })).toBe("UK");
});

test("generic Science is not classified as AI & Tech automatically", () => {
  expect(
    getPrimaryPillar({
      category: "Science",
      scope: "uk",
      title: "National research update",
    })
  ).toBe("UK");
});
