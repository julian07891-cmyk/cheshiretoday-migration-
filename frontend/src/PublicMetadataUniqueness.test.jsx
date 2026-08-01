import React, { act } from "react";
import { createRoot } from "react-dom/client";
import { Helmet, HelmetProvider } from "react-helmet-async";
import {
  MemoryRouter,
  Route,
  Routes,
  useNavigate,
  useParams,
} from "react-router-dom";
import PublicMetadataDefaults from "./components/PublicMetadataDefaults";
import HomePageV1 from "./pages/HomePageV1";
import ArticlePageV2 from "./pages/ArticlePageV2";
import CategoryPage from "./components/CategoryPage";
import LocationPage from "./components/LocationPage";
import NewsletterPage from "./pages/NewsletterPage";
import AuthorityPage from "./pages/AuthorityPage";
import ContactPage from "./components/ContactPage";
import { SecureNewsletterPreferencesPage } from "./components/SecureNewsletterManagementPages";

const mockLoadPublicArticle = jest.fn();

jest.mock("./services/articleViewTracking", () => ({
  loadPublicArticle: (...args) => mockLoadPublicArticle(...args),
}));
jest.mock("./components/NewsHeader", () => () => <header>Cheshire Today</header>);
jest.mock("./components/NewsFooter", () => () => <footer>Footer</footer>);
jest.mock("./components/FestiveTheme", () => () => null);
jest.mock("./components/RelatedArticles", () => () => null);
jest.mock("./components/SubscribeSection", () => () => null);
jest.mock("./components/JobsWidget", () => ({ SubscribeInlineBanner: () => null }));
jest.mock("./components/CompactArticleCard", () => () => null);
jest.mock("./components/homepage/TextHeadlineStrip", () => () => null);
jest.mock("./components/homepage/SectionHeader", () => () => null);
jest.mock("./components/AffiliateWidgets", () => ({ AffiliateWidgetSidebar: () => null }));
jest.mock("./components/SponsoredPlacement", () => () => null);
jest.mock("./components/NewsletterPreferences", () => () => null);
jest.mock("./components/homepage/HomepageLayout", () => ({ children }) => <>{children}</>);
jest.mock("./components/homepage/HomepageHeader", () => () => <header>Cheshire Today</header>);
jest.mock("./components/homepage/HeroMonetisationStrip", () => () => null);
jest.mock("./components/homepage/HeroStoryCard", () => () => null);
jest.mock("./components/homepage/TopStoriesGrid", () => () => null);
jest.mock("./components/homepage/LeadSection", () => () => null);
jest.mock("./components/ui/button", () => ({
  Button: ({ children, ...props }) => <button {...props}>{children}</button>,
}));
jest.mock("./components/ui/badge", () => ({
  Badge: ({ children }) => <span>{children}</span>,
}));
jest.mock("./components/ui/toaster", () => ({ Toaster: () => null }));
jest.mock("./hooks/use-toast.js", () => ({ toast: jest.fn() }));

const HOME_DESCRIPTION =
  "Latest local, business, finance, AI and UK news from Cheshire Today.";
const STATIC_HOME_DESCRIPTION =
  "Cheshire Today delivers local Cheshire news and business updates alongside AI & tech coverage, finance insights and practical tax guides.";
const STATIC_HOME_TITLE =
  "Cheshire Today | Local News, Business, AI & Tech, Finance";
const STATIC_HOME_SOCIAL_DESCRIPTION =
  "Local Cheshire news and business updates alongside AI & tech coverage, finance insights and practical tax guides.";
const HOME_SOCIAL_IMAGE = "https://cheshiretoday.co.uk/social-share.jpg";

const articles = {
  "6a65e9284730b1c10b2b37c0": {
    slug: "first-cheshire-story",
    description: "The first article description.",
  },
  "6a65e9284730b1c10b2b37c1": {
    slug: "second-cheshire-story",
    description: "The second article description.",
  },
};

function RouteMetadata({ kind }) {
  const params = useParams();
  let canonical = "https://cheshiretoday.co.uk/";
  let description = HOME_DESCRIPTION;
  let title = "Latest News | Cheshire Today";
  let type = "website";
  let image = HOME_SOCIAL_IMAGE;

  if (kind === "article") {
    const article = articles[params.articleId];
    canonical = `https://cheshiretoday.co.uk/article/${params.articleId}/${article.slug}`;
    description = article.description;
    title = `${article.slug} | Cheshire Today`;
    type = "article";
    image = `https://cheshiretoday.co.uk/${article.slug}.jpg`;
  } else if (kind === "category") {
    canonical = `https://cheshiretoday.co.uk/category/${params.slug}`;
    description = "Business reporting and analysis from Cheshire Today.";
    title = "Business | Cheshire Today";
  } else if (kind === "location") {
    canonical = `https://cheshiretoday.co.uk/${params.location}`;
    description = "The latest news and updates from Chester.";
    title = "Chester News | Cheshire Today";
  } else if (kind === "newsletter") {
    canonical = "https://cheshiretoday.co.uk/newsletter";
    description = "Subscribe to the Cheshire Today newsletter.";
    title = "Newsletter | Cheshire Today";
  }

  return (
    <Helmet defer={false}>
      <title>{title}</title>
      <meta name="description" content={description} />
      <link rel="canonical" href={canonical} />
      <meta property="og:url" content={canonical} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:type" content={type} />
      <meta property="og:image" content={image} />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:url" content={canonical} />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={image} />
    </Helmet>
  );
}

function Navigation() {
  const navigate = useNavigate();
  return (
    <nav>
      <button onClick={() => navigate("/")}>Home</button>
      <button
        onClick={() =>
          navigate(
            "/article/6a65e9284730b1c10b2b37c0/ignored-stale-slug?utm_source=facebook&utm_medium=social&utm_campaign=social_publishing&fbclid=abc&gclid=def#comments",
          )
        }
      >
        First article
      </button>
      <button
        onClick={() =>
          navigate("/article/6a65e9284730b1c10b2b37c1/another-stale-slug")
        }
      >
        Second article
      </button>
    </nav>
  );
}

const MetadataApp = ({ initialEntry = "/" }) => (
  <HelmetProvider>
    <MemoryRouter initialEntries={[initialEntry]}>
      <PublicMetadataDefaults />
      <Navigation />
      <Routes>
        <Route path="/" element={<RouteMetadata kind="home" />} />
        <Route
          path="/article/:articleId/:slug"
          element={<RouteMetadata kind="article" />}
        />
        <Route
          path="/category/:slug"
          element={<RouteMetadata kind="category" />}
        />
        <Route path="/:location" element={<RouteMetadata kind="location" />} />
        <Route
          path="/newsletter"
          element={<RouteMetadata kind="newsletter" />}
        />
      </Routes>
    </MemoryRouter>
  </HelmetProvider>
);

const headTags = () => ({
  canonical: Array.from(
    document.head.querySelectorAll('link[rel="canonical"]'),
  ),
  description: Array.from(
    document.head.querySelectorAll('meta[name="description"]'),
  ),
  ogUrl: Array.from(document.head.querySelectorAll('meta[property="og:url"]')),
  ogTitle: Array.from(document.head.querySelectorAll('meta[property="og:title"]')),
  ogDescription: Array.from(
    document.head.querySelectorAll('meta[property="og:description"]'),
  ),
  twitterUrl: Array.from(
    document.head.querySelectorAll('meta[name="twitter:url"]'),
  ),
  twitterTitle: Array.from(
    document.head.querySelectorAll('meta[name="twitter:title"]'),
  ),
  twitterDescription: Array.from(
    document.head.querySelectorAll('meta[name="twitter:description"]'),
  ),
  ogType: Array.from(document.head.querySelectorAll('meta[property="og:type"]')),
  ogImage: Array.from(document.head.querySelectorAll('meta[property="og:image"]')),
  twitterCard: Array.from(
    document.head.querySelectorAll('meta[name="twitter:card"]'),
  ),
  twitterImage: Array.from(
    document.head.querySelectorAll('meta[name="twitter:image"]'),
  ),
});

const expectUniqueMetadata = ({ canonical, description }) => {
  const tags = headTags();
  expect(tags.canonical).toHaveLength(1);
  expect(tags.description).toHaveLength(1);
  expect(tags.ogUrl).toHaveLength(1);
  expect(tags.ogTitle).toHaveLength(1);
  expect(tags.ogDescription).toHaveLength(1);
  expect(tags.twitterUrl).toHaveLength(1);
  expect(tags.twitterTitle).toHaveLength(1);
  expect(tags.twitterDescription).toHaveLength(1);
  expect(tags.canonical[0].getAttribute("href")).toBe(canonical);
  expect(tags.description[0].getAttribute("content")).toBe(description);
  expect(tags.ogUrl[0].getAttribute("content")).toBe(canonical);
  expect(tags.ogDescription[0].getAttribute("content")).toBe(description);
  expect(tags.twitterUrl[0].getAttribute("content")).toBe(canonical);
  expect(tags.twitterDescription[0].getAttribute("content")).toBe(description);
};

const expectUniqueCoreMetadata = ({ canonical, description }) => {
  const tags = headTags();
  expect(tags.canonical).toHaveLength(1);
  expect(tags.description).toHaveLength(1);
  expect(tags.ogUrl).toHaveLength(1);
  expect(tags.canonical[0].getAttribute("href")).toBe(canonical);
  expect(tags.description[0].getAttribute("content")).toBe(description);
  expect(tags.ogUrl[0].getAttribute("content")).toBe(canonical);
};

const expectUniquePrimaryMetadata = ({
  canonical,
  description,
  type,
  image,
}) => {
  expectUniqueCoreMetadata({ canonical, description });
  const tags = headTags();
  expect(tags.ogType).toHaveLength(1);
  expect(tags.ogImage).toHaveLength(1);
  expect(tags.twitterCard).toHaveLength(1);
  expect(tags.twitterImage).toHaveLength(1);
  expect(tags.ogType[0].getAttribute("content")).toBe(type);
  expect(tags.ogImage[0].getAttribute("content")).toBe(image);
  expect(tags.twitterCard[0].getAttribute("content")).toBe(
    "summary_large_image",
  );
  expect(tags.twitterImage[0].getAttribute("content")).toBe(image);
};

let container;
let root;
let originalHead;
let originalFetch;
let originalPublicUrl;

beforeAll(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
});

beforeEach(() => {
  originalHead = document.head.innerHTML;
  originalFetch = global.fetch;
  originalPublicUrl = process.env.REACT_APP_PUBLIC_URL;
  process.env.REACT_APP_PUBLIC_URL = "https://cheshiretoday.co.uk";
  mockLoadPublicArticle.mockReset();
  document.head.insertAdjacentHTML(
    "beforeend",
    `<meta name="description" content="${STATIC_HOME_DESCRIPTION}" data-rh="true">` +
      '<link rel="canonical" href="https://cheshiretoday.co.uk/" data-rh="true">' +
      '<meta property="og:url" content="https://cheshiretoday.co.uk/" data-rh="true">' +
      '<meta property="og:type" content="website" data-rh="true">' +
      `<meta property="og:image" content="${HOME_SOCIAL_IMAGE}" data-rh="true">` +
      `<meta property="og:image:secure_url" content="${HOME_SOCIAL_IMAGE}" data-rh="true">` +
      '<meta property="og:image:type" content="image/jpeg" data-rh="true">' +
      '<meta property="og:image:width" content="1200" data-rh="true">' +
      '<meta property="og:image:height" content="630" data-rh="true">' +
      '<meta property="og:image:alt" content="Cheshire Today News" data-rh="true">' +
      `<meta property="og:title" content="${STATIC_HOME_TITLE}" data-rh="true">` +
      `<meta property="og:description" content="${STATIC_HOME_SOCIAL_DESCRIPTION}" data-rh="true">` +
      '<meta name="twitter:card" content="summary_large_image" data-rh="true">' +
      '<meta name="twitter:url" content="https://cheshiretoday.co.uk/" data-rh="true">' +
      `<meta name="twitter:title" content="${STATIC_HOME_TITLE}" data-rh="true">` +
      `<meta name="twitter:description" content="${STATIC_HOME_SOCIAL_DESCRIPTION}" data-rh="true">` +
      `<meta name="twitter:image" content="${HOME_SOCIAL_IMAGE}" data-rh="true">` +
      '<meta name="twitter:image:alt" content="Cheshire Today News" data-rh="true">',
  );
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root?.unmount());
  container?.remove();
  document.head.innerHTML = originalHead;
  global.fetch = originalFetch;
  if (originalPublicUrl === undefined) delete process.env.REACT_APP_PUBLIC_URL;
  else process.env.REACT_APP_PUBLIC_URL = originalPublicUrl;
  jest.restoreAllMocks();
  root = null;
  container = null;
});

const renderMetadataApp = async (initialEntry = "/") => {
  await act(async () => {
    root.render(<MetadataApp initialEntry={initialEntry} />);
    await new Promise((resolve) => setTimeout(resolve, 50));
  });
};

const navigateByLabel = async (label) => {
  const button = Array.from(container.querySelectorAll("button")).find(
    (candidate) => candidate.textContent === label,
  );
  await act(async () => {
    button.click();
    await new Promise((resolve) => setTimeout(resolve, 50));
  });
};

const renderProductionRoute = async ({ path, pattern, element }) => {
  await act(async () => {
    root.render(
      <HelmetProvider>
        <MemoryRouter initialEntries={[path]}>
          <PublicMetadataDefaults />
          <Routes>
            <Route path={pattern} element={element} />
          </Routes>
        </MemoryRouter>
      </HelmetProvider>,
    );
    await new Promise((resolve) => setTimeout(resolve, 75));
  });
};

const expectNoHomepageDefaults = () => {
  expect(document.head.innerHTML).not.toContain(HOME_DESCRIPTION);
  expect(document.head.innerHTML).not.toContain(STATIC_HOME_DESCRIPTION);
  expect(document.head.innerHTML).not.toContain(STATIC_HOME_TITLE);
  expect(document.head.innerHTML).not.toContain(STATIC_HOME_SOCIAL_DESCRIPTION);
  expect(document.head.innerHTML).not.toContain(HOME_SOCIAL_IMAGE);
  expect(
    document.head.querySelector('link[rel="canonical"][href="https://cheshiretoday.co.uk/"]'),
  ).toBeNull();
  expect(
    document.head.querySelector('meta[property="og:url"][content="https://cheshiretoday.co.uk/"]'),
  ).toBeNull();
  expect(
    document.head.querySelector(`meta[property="og:image"][content="${HOME_SOCIAL_IMAGE}"]`),
  ).toBeNull();
  expect(
    document.head.querySelector(`meta[name="twitter:image"][content="${HOME_SOCIAL_IMAGE}"]`),
  ).toBeNull();
};

const expectNoPrimarySocialMetadata = () => {
  expect(document.head.querySelectorAll('meta[property="og:url"]')).toHaveLength(0);
  expect(document.head.querySelectorAll('meta[property="og:type"]')).toHaveLength(0);
  expect(document.head.querySelectorAll('meta[property="og:image"]')).toHaveLength(0);
  expect(document.head.querySelectorAll('meta[name="twitter:card"]')).toHaveLength(0);
  expect(document.head.querySelectorAll('meta[name="twitter:image"]')).toHaveLength(0);
};

const expectRouteTypeWithoutImageDefaults = (type) => {
  const tags = headTags();
  expect(tags.ogType).toHaveLength(1);
  expect(tags.ogType[0].getAttribute("content")).toBe(type);
  expect(tags.ogImage).toHaveLength(0);
  expect(tags.twitterCard).toHaveLength(0);
  expect(tags.twitterImage).toHaveLength(0);
};

test("homepage replaces the real static shell with one complete metadata set", async () => {
  await renderMetadataApp();
  expectUniquePrimaryMetadata({
    canonical: "https://cheshiretoday.co.uk/",
    description: HOME_DESCRIPTION,
    type: "website",
    image: HOME_SOCIAL_IMAGE,
  });
});

test("the production homepage owns one complete primary metadata set", async () => {
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => [],
  });
  await renderProductionRoute({ path: "/", pattern: "/", element: <HomePageV1 /> });
  expectUniquePrimaryMetadata({
    canonical: "https://cheshiretoday.co.uk/",
    description: HOME_DESCRIPTION,
    type: "website",
    image: HOME_SOCIAL_IMAGE,
  });
});

test("the production Contact page keeps its description without homepage metadata", async () => {
  await renderProductionRoute({ path: "/contact", pattern: "/contact", element: <ContactPage /> });
  const descriptions = document.head.querySelectorAll('meta[name="description"]');
  expect(descriptions).toHaveLength(1);
  expect(descriptions[0].getAttribute("content")).toBe(
    "Contact Cheshire Today for editorial enquiries, partnerships, corrections or advertising.",
  );
  expect(document.head.querySelectorAll('link[rel="canonical"]')).toHaveLength(0);
  expect(document.head.querySelectorAll('meta[property="og:url"]')).toHaveLength(0);
  expectNoPrimarySocialMetadata();
  expectNoHomepageDefaults();
});

test("the production secure preferences page remains noindex without homepage metadata", async () => {
  await renderProductionRoute({
    path: "/newsletter/preferences",
    pattern: "/newsletter/preferences",
    element: <SecureNewsletterPreferencesPage />,
  });
  const robots = document.head.querySelectorAll('meta[name="robots"]');
  expect(robots).toHaveLength(1);
  expect(robots[0].getAttribute("content")).toBe("noindex, nofollow, noarchive");
  expect(document.head.querySelectorAll('meta[name="description"]')).toHaveLength(0);
  expect(document.head.querySelectorAll('link[rel="canonical"]')).toHaveLength(0);
  expect(document.head.querySelectorAll('meta[property="og:url"]')).toHaveLength(0);
  expectNoPrimarySocialMetadata();
  expectNoHomepageDefaults();
});

test.each(["/admin", "/unsupported-public-route"])(
  "the homepage fallback injects nothing on %s",
  async (path) => {
    await renderProductionRoute({ path, pattern: path, element: <div>Route</div> });
    expect(document.head.querySelectorAll('meta[name="description"]')).toHaveLength(0);
    expect(document.head.querySelectorAll('link[rel="canonical"]')).toHaveLength(0);
    expect(document.head.querySelectorAll('meta[property="og:url"]')).toHaveLength(0);
    expect(document.head.querySelectorAll('meta[property="og:type"]')).toHaveLength(0);
    expect(document.head.querySelectorAll('meta[property="og:image"]')).toHaveLength(0);
    expect(document.head.querySelectorAll('meta[name="twitter:card"]')).toHaveLength(0);
    expect(document.head.querySelectorAll('meta[name="twitter:image"]')).toHaveLength(0);
    expectNoHomepageDefaults();
  },
);

test("the production authority page owns route-specific metadata", async () => {
  const description = "A bounded guide introduction for Cheshire readers.";
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({
      title: "Cheshire business guide",
      sections: [{ type: "intro", content: description }],
    }),
  });
  await renderProductionRoute({
    path: "/guides/cheshire-business-guide",
    pattern: "/guides/:slug",
    element: <AuthorityPage />,
  });
  expectUniqueCoreMetadata({
    canonical: "https://cheshiretoday.co.uk/guides/cheshire-business-guide",
    description,
  });
  expectRouteTypeWithoutImageDefaults("article");
  expectNoHomepageDefaults();
});

test("the production article owner emits a clean canonical from Mongo ID and title", async () => {
  const articleId = "6a65e9284730b1c10b2b37c0";
  const description = "The production article description for Cheshire Today readers.";
  mockLoadPublicArticle.mockResolvedValue({
    id: articleId,
    title: "First Cheshire Story",
    summary: description,
    content: "A complete public article body for metadata rendering.",
    category: "Local News",
    image: "https://example.com/article.jpg",
    publishedDate: "2026-08-01T06:00:00Z",
  });
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => [] });
  await renderProductionRoute({
    path: `/article/${articleId}/stale?utm_source=facebook&fbclid=abc&gclid=def#comments`,
    pattern: "/article/:articleId/:slug",
    element: <ArticlePageV2 categories={[]} />,
  });
  expectUniquePrimaryMetadata({
    canonical: `https://cheshiretoday.co.uk/article/${articleId}/first-cheshire-story`,
    description,
    type: "article",
    image: "https://example.com/article.jpg",
  });
  expectNoHomepageDefaults();
});

test("production category, location and newsletter owners keep route-specific core metadata", async () => {
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ articles: [], total: 0 }),
  });
  await renderProductionRoute({
    path: "/category/business",
    pattern: "/category/business",
    element: <CategoryPage categorySlug="business" />,
  });
  expectUniqueCoreMetadata({
    canonical: "https://cheshiretoday.co.uk/category/business",
    description: "Cheshire business, investment, jobs and economic news.",
  });
  expectRouteTypeWithoutImageDefaults("website");
  expectNoHomepageDefaults();

  act(() => root.unmount());
  root = createRoot(container);
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ articles: [], total: 0 }),
  });
  await renderProductionRoute({
    path: "/chester",
    pattern: "/:location",
    element: <LocationPage />,
  });
  expectUniqueCoreMetadata({
    canonical: "https://cheshiretoday.co.uk/chester",
    description: "Latest news from Chester, Ellesmere Port and surrounding areas.",
  });
  expectRouteTypeWithoutImageDefaults("website");
  expectNoHomepageDefaults();

  act(() => root.unmount());
  root = createRoot(container);
  await renderProductionRoute({
    path: "/newsletter",
    pattern: "/newsletter",
    element: <NewsletterPage />,
  });
  expectUniquePrimaryMetadata({
    canonical: "https://cheshiretoday.co.uk/newsletter",
    description:
      "Subscribe free to the Cheshire Today newsletter for local news, business, property, finance and AI & Tech updates from across Cheshire.",
    type: "website",
    image: "https://cheshiretoday.co.uk/cheshire-today-newsletter-share.png",
  });
  expectNoHomepageDefaults();
});

test.each([
  [
    "/category/business",
    "https://cheshiretoday.co.uk/category/business",
    "Business reporting and analysis from Cheshire Today.",
  ],
  [
    "/chester",
    "https://cheshiretoday.co.uk/chester",
    "The latest news and updates from Chester.",
  ],
  [
    "/newsletter",
    "https://cheshiretoday.co.uk/newsletter",
    "Subscribe to the Cheshire Today newsletter.",
  ],
])("%s owns one self-canonical metadata set", async (path, canonical, description) => {
  await renderMetadataApp(path);
  expectUniqueMetadata({ canonical, description });
});

test("Facebook attribution and browser tracking values never enter article canonicals", async () => {
  await renderMetadataApp(
    "/article/6a65e9284730b1c10b2b37c0/stale?utm_source=facebook&utm_medium=social&utm_campaign=social_publishing&fbclid=abc&gclid=def#comments",
  );
  expectUniqueMetadata({
    canonical:
      "https://cheshiretoday.co.uk/article/6a65e9284730b1c10b2b37c0/first-cheshire-story",
    description: "The first article description.",
  });
  expectUniquePrimaryMetadata({
    canonical:
      "https://cheshiretoday.co.uk/article/6a65e9284730b1c10b2b37c0/first-cheshire-story",
    description: "The first article description.",
    type: "article",
    image: "https://cheshiretoday.co.uk/first-cheshire-story.jpg",
  });
  expect(document.head.innerHTML).not.toContain("utm_");
  expect(document.head.innerHTML).not.toContain("fbclid");
  expect(document.head.innerHTML).not.toContain("gclid");
  expect(document.head.innerHTML).not.toContain("#comments");
});

test("SPA navigation replaces article metadata and restores homepage metadata", async () => {
  await renderMetadataApp();
  await navigateByLabel("First article");
  expectUniqueMetadata({
    canonical:
      "https://cheshiretoday.co.uk/article/6a65e9284730b1c10b2b37c0/first-cheshire-story",
    description: "The first article description.",
  });
  expectUniquePrimaryMetadata({
    canonical:
      "https://cheshiretoday.co.uk/article/6a65e9284730b1c10b2b37c0/first-cheshire-story",
    description: "The first article description.",
    type: "article",
    image: "https://cheshiretoday.co.uk/first-cheshire-story.jpg",
  });

  await navigateByLabel("Second article");
  expectUniqueMetadata({
    canonical:
      "https://cheshiretoday.co.uk/article/6a65e9284730b1c10b2b37c1/second-cheshire-story",
    description: "The second article description.",
  });
  expectUniquePrimaryMetadata({
    canonical:
      "https://cheshiretoday.co.uk/article/6a65e9284730b1c10b2b37c1/second-cheshire-story",
    description: "The second article description.",
    type: "article",
    image: "https://cheshiretoday.co.uk/second-cheshire-story.jpg",
  });
  expect(document.head.innerHTML).not.toContain("first-cheshire-story");
  expect(document.head.innerHTML).not.toContain("The first article description.");

  await navigateByLabel("Home");
  expectUniqueMetadata({
    canonical: "https://cheshiretoday.co.uk/",
    description: HOME_DESCRIPTION,
  });
  expectUniquePrimaryMetadata({
    canonical: "https://cheshiretoday.co.uk/",
    description: HOME_DESCRIPTION,
    type: "website",
    image: HOME_SOCIAL_IMAGE,
  });
  expect(document.head.innerHTML).not.toContain("second-cheshire-story");
  expect(document.head.innerHTML).not.toContain("The second article description.");
});
