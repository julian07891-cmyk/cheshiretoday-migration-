import { autoLinkContent } from "./ArticlePageV2";

jest.mock("react-helmet-async", () => ({ Helmet: ({ children }) => <>{children}</> }));
jest.mock("../services/articleViewTracking", () => ({ loadPublicArticle: jest.fn() }));
jest.mock("../config/contextualRecommendations", () => ({
  normaliseContextualCategory: jest.fn(),
  selectContextualRecommendation: jest.fn(),
}));
jest.mock("../components/NewsHeader", () => () => null);
jest.mock("../components/NewsFooter", () => () => null);
jest.mock("../components/FestiveTheme", () => () => null);
jest.mock("../components/RelatedArticles", () => () => null);
jest.mock("../components/SubscribeSection", () => () => null);
jest.mock("../components/JobsWidget", () => ({ SubscribeInlineBanner: () => null }));
jest.mock("../components/CompactArticleCard", () => () => null);
jest.mock("../components/homepage/TextHeadlineStrip", () => () => null);
jest.mock("../components/homepage/SectionHeader", () => () => null);
jest.mock("../components/monetisation/ContextualRecommendationCard", () => () => null);
jest.mock("../components/SponsoredPlacement", () => () => null);
jest.mock("../components/ui/toaster", () => ({ Toaster: () => null }));
jest.mock("../hooks/use-toast.js", () => ({ toast: jest.fn() }));

describe("article content named external links", () => {
  test.each(["https", "http"])("renders a valid named %s link", (protocol) => {
    const html = autoLinkContent(
      `[Council survey](${protocol}://www.wilmslowtowncouncil.gov.uk/residentssurvey)`,
      "Local News"
    );

    expect(html).toContain(
      `<a href="${protocol}://www.wilmslowtowncouncil.gov.uk/residentssurvey" target="_blank" rel="nofollow noopener noreferrer"`
    );
    expect(html).toContain(">Council survey</a>");
  });

  test.each(["javascript:alert(1)", "data:text/html,hello"])(
    "does not link an unsafe %s target",
    (target) => {
      const html = autoLinkContent(`[Unsafe link](${target})`, "Local News");

      expect(html).not.toContain("<a ");
      expect(html).toContain("[Unsafe link]");
    }
  );

  test("keeps raw HTML escaped and escapes named-link labels", () => {
    const html = autoLinkContent(
      `<script>alert(1)</script> [<img src=x onerror=alert(1)>](https://example.com)`,
      "Local News"
    );

    expect(html).not.toContain("<script>");
    expect(html).not.toContain("<img");
    expect(html).toContain("&lt;script");
    expect(html).toContain("&lt;img src=x onerror=alert(1)&lt;</a>");
  });

  test("leaves malformed named-link syntax as safe plain text", () => {
    const html = autoLinkContent("Read [the survey](not a URL", "Local News");

    expect(html).not.toContain("<a ");
    expect(html).toContain("Read [the survey](not a URL");
  });

  test("does not mistake ordinary online-will prose for will-writing intent", () => {
    const html = autoLinkContent(
      "Completing the residents' survey online will take only a few minutes.",
      "Local News"
    );

    expect(html).not.toContain("best-online-will-writing-services-uk");
    expect(html).toContain("survey online will take only a few minutes");
  });

  test("preserves specific will-writing guide links", () => {
    const html = autoLinkContent("The service offers regulated will writing.", "Business");

    expect(html).toContain("best-online-will-writing-services-uk");
  });

  test("preserves ordinary imported article paragraphs", () => {
    expect(autoLinkContent("First paragraph.\n\nSecond paragraph.", "Local News")).toBe(
      "<p>First paragraph.</p><p>Second paragraph.</p>"
    );
  });

  test("renders the Wilmslow Residents' Survey link exactly", () => {
    const html = autoLinkContent(
      "[Complete the Wilmslow Residents’ Survey](https://www.wilmslowtowncouncil.gov.uk/residentssurvey)",
      "Local News"
    );

    expect(html).toContain(
      '<a href="https://www.wilmslowtowncouncil.gov.uk/residentssurvey" target="_blank" rel="nofollow noopener noreferrer"'
    );
    expect(html).toContain(">Complete the Wilmslow Residents’ Survey</a>");
  });
});
