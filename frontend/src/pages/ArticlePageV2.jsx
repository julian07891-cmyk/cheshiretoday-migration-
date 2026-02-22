import React, { useEffect, useMemo, useState } from "react";
import ContextTools from "../components/monetisation/ContextTools";
import { useNavigate, useParams } from "react-router-dom";
import { Helmet, HelmetProvider } from "react-helmet-async";
import ArticleAffiliateStrip from "../components/ArticleAffiliateStrip";
import AuthorBox from "../components/AuthorBox";

import NewsHeader from "../components/NewsHeader";
import NewsFooter from "../components/NewsFooter";
import FestiveTheme from "../components/FestiveTheme";
import RelatedArticles from "../components/RelatedArticles";
import SidebarMoreStories from "../components/SidebarMoreStories";

import { Toaster } from "../components/ui/toaster";
import { toast } from "../hooks/use-toast.js";

import { Loader2 } from "lucide-react";
import { getApiUrl } from "../utils/api";

/**
 * Convert unknown values to a safe string for React rendering.
 * Prevents React error: "Objects are not valid as a React child" (React #31).
 */
function safeText(v) {
  if (v == null) return "";
  const t = typeof v;
  if (t === "string") return v;
  if (t === "number" || t === "boolean") return String(v);
  if (Array.isArray(v)) return v.map(safeText).filter(Boolean).join("\n");
  if (t === "object") {
    // Common backend shapes
    if (typeof v.text === "string") return v.text;
    if (typeof v.content === "string") return v.content;
    if (typeof v.summary === "string") return v.summary;
    if (typeof v.title === "string") return v.title;
    if (typeof v.name === "string") return v.name;
    return "";
  }
  try {
    return String(v);
  } catch (_) {
    return "";
  }
}

function formatDateTime(dateString) {
  if (!dateString) return "";
  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function buildDescription(article) {
  const summary = safeText(article?.summary).trim();
  if (summary.length >= 40) return summary.slice(0, 200);
  return safeText(article?.content).trim().slice(0, 200);
}

// Split out any appended attribution block so it doesn't dominate the article body.
function splitAttribution(rawContent) {
  const content = safeText(rawContent);
  const marker = "This article was originally published by";
  const idx = content.indexOf(marker);
  if (idx === -1) return { main: content, attribution: "" };
  return {
    main: content.slice(0, idx).trim(),
    attribution: content.slice(idx).trim(),
  };
}

/* ===== AI Guide Promo Block (Monetisation Funnel) ===== */
const GuidePromoBlock = ({ guides = [], category }) => {
  if (!Array.isArray(guides) || guides.length === 0) return null;

  const cat = String(category || "").toLowerCase();

  const preferSlug = () => {
    if (cat.includes("ai") || cat.includes("tech")) return "best-ai-tools-uk";
    if (cat.includes("business") || cat.includes("finance") || cat.includes("money"))
      return "best-ai-productivity-tools-uk";
    if (cat.includes("writing")) return "best-ai-writing-tools-uk";
    return "best-ai-tools-uk";
  };

  const preferred = preferSlug();
  const preferredGuide = guides.find((g) => String(g?.slug || "") === preferred);
  const others = guides.filter((g) => String(g?.slug || "") !== preferred);
  const ordered = [preferredGuide, ...others].filter(Boolean).slice(0, 3);

  return (
    <div className="mt-6 p-4 rounded-xl border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20">
      <div className="text-xs font-semibold text-sky-800 dark:text-slate-200 mb-2">🔎 AI Guides</div>
      <div className="space-y-2">
        {ordered.map((g) => (
          <div
            key={g.slug}
            className="rounded-lg border border-slate-200 dark:border-slate-800 bg-[#FBFAF7] dark:bg-transparent p-2.5"
          >
            <a
              href={`/guides/${g.slug}`}
              className="block font-semibold text-sky-900 dark:text-slate-200 hover:underline underline-offset-2"
            >
              {safeText(g.title) || g.slug}
            </a>
            <div className="text-[11px] mt-1 text-slate-700 dark:text-gray-400">
              Updated: {String(g.updated_at || g.created_at || "").slice(0, 10)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const GuidesInlinePromo = ({ guides }) => {
  const list = Array.isArray(guides) ? guides : [];
  const g = list[0];
  if (!g) return null;

  const title = safeText(g?.title) || "In-depth Guide";
  const slug = String(g?.slug || "").trim();
  const href = slug ? `/guides/${slug}` : "/guides/best-ai-tools-uk";

  return (
    <div className="mt-6 p-4 rounded-xl border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20">
      <div className="text-xs font-semibold text-sky-800 dark:text-slate-200 mb-1">In-depth Guide</div>
      <a href={href} className="block font-semibold text-sky-900 dark:text-slate-200 hover:underline underline-offset-2">
        {title}
      </a>
      <div className="text-[11px] mt-1 text-slate-700 dark:text-gray-400">
        Updated UK guide with recommendations and affiliate disclosures →
      </div>
    </div>
  );
};

export default function ArticlePageV2({ categories }) {
  const { articleId } = useParams();
  const navigate = useNavigate();
  // --- More stories (below article) ---
  const [moreStories, setMoreStories] = useState([]);
  const [moreStoriesOpen, setMoreStoriesOpen] = useState(false);

  const fmtShort = (dateString) => {
    const d = new Date(dateString);
    if (Number.isNaN(d.getTime())) return "";
    return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
  };

  useEffect(() => {
    let mounted = true;

    async function fetchMoreStories() {
      try {
        const API = getApiUrl().replace(/\/$/, "");
        const res = await fetch(`${API}/api/articles?limit=24`);
        if (!res.ok) return;

        const data = await res.json();
        const list = Array.isArray(data)
          ? data
          : Array.isArray(data?.articles)
          ? data.articles
          : [];

        const cleaned = list
          .filter((a) => a && (a.id || a._id) && String(a.id || a._id) !== String(articleId))
          .filter((a) => String(a.title || "").trim().length > 0);

        if (mounted) setMoreStories(cleaned);
      } catch (_) {
        // ignore
      }
    }

    fetchMoreStories();
    return () => {
      mounted = false;
    };
  }, [articleId]);

  const [article, setArticle] = useState(null);
  const [guides, setGuides] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  const publicUrl =
    process.env.REACT_APP_PUBLIC_URL || (typeof window !== "undefined" ? window.location.origin : "");

  const description = useMemo(() => buildDescription(article), [article]);
  const safeTitle = useMemo(() => safeText(article?.title), [article]);

  // Pillar label for sidebar (keeps the publication feeling intentional)
  const pillarLabel = useMemo(() => {
    const sec = String(article?.section || "").toLowerCase();
    const cat = String(article?.category || "").toLowerCase();
    const title = String(article?.title || "").toLowerCase();
    const blob = `${sec} ${cat} ${title}`;

    if (sec.startsWith("ai-") || blob.includes("artificial intelligence") || blob.includes(" tech ") || blob.includes("technology") || blob.includes(" ai ")) {
      return "AI & Tech";
    }
    if (blob.includes("finance") || blob.includes("money") || blob.includes("mortgage") || blob.includes("savings") || blob.includes("rates") || blob.includes("tax")) {
      return "Finance";
    }
    if (blob.includes("business") || blob.includes("economy") || blob.includes("jobs") || blob.includes("companies")) {
      return "Business";
    }
    return "Local";
  }, [article?.section, article?.category, article?.title]);


  const rawBody = useMemo(() => {
    const c = article?.content;
    const s = article?.summary;
    if (typeof c === "string" && c.trim()) return c;
    if (typeof s === "string" && s.trim()) return s;
    // last-resort stringify avoidance: return empty instead of rendering objects
    return "";
  }, [article]);

  const { main: mainContent, attribution } = useMemo(() => splitAttribution(rawBody), [rawBody]);


  // Contextual monetisation mapping: convert article metadata -> tool category
  const contextToolType = useMemo(() => {
    const sec = String(article?.section || "").toLowerCase();
    const title = String(article?.title || "").toLowerCase();
    const cat = String(article?.category || "").toLowerCase();
    const text = `${sec} ${title} ${cat}`;

    // AI / Tech
    if (sec.startsWith("ai-") || text.includes(" ai ") || text.includes("chatgpt") || text.includes("gemini")) return "ai";

    // Mortgages / Savings / Property / Tax
    if (text.includes("mortgage") || text.includes("remortgage") || text.includes("fixed rate") || text.includes("tracker")) return "mortgages";
    if (text.includes("savings") || text.includes("isa") || text.includes("interest rate") || text.includes("easy-access")) return "savings";
    if (text.includes("property") || text.includes("house price") || text.includes("rent") || text.includes("landlord")) return "property";
    if (text.includes("council tax") || text.includes("stamp duty") || text.includes("hmrc") || text.includes("tax")) return "property";

    // Credit / Utilities
    if (text.includes("credit card") || text.includes("0%") || text.includes("balance transfer") || text.includes("apr")) return "credit";
    if (text.includes("energy") || text.includes("tariff") || text.includes("broadband") || text.includes("utilities")) return "energy";

    return "";
  }, [article]);

  useEffect(() => {
    let mounted = true;

    async function fetchArticle() {
      try {
        setLoading(true);
        setErrorMsg("");

        const API_BASE = getApiUrl().replace(/\/$/, "");
        const res = await fetch(`${API_BASE}/api/articles/${encodeURIComponent(articleId)}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();
        if (!mounted) return;

        setArticle(data);
      } catch (e) {
        if (!mounted) return;
        console.error("Error fetching article:", e);
        setArticle(null);
        setErrorMsg("Article not found");
      } finally {
        if (!mounted) return;
        setLoading(false);
      }
    }

    fetchArticle();
    return () => {
      mounted = false;
    };
  }, [articleId]);

  const handleShare = () => {
    const shareUrl = `${publicUrl}/article/${articleId}`;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(shareUrl);
      toast({ title: "Link Copied!", description: "Article link copied to clipboard!" });
    }
  };

  if (loading) {
    return (
      <HelmetProvider>
        <div className="min-h-screen bg-[#F7F4EE] text-neutral-900 dark:bg-gray-900 dark:text-white">
          <FestiveTheme />
          <NewsHeader
            categories={categories}
            activeCategory="all"
            onCategoryChange={() => navigate("/")}
            onSearch={() => {}}
          />
          <div className="container mx-auto px-4 py-20">
            <div className="flex flex-col items-center justify-center">
              <Loader2 className="h-16 w-16 animate-spin text-slate-600 mb-4" />
              <p className="text-lg text-muted-foreground">Loading article...</p>
            </div>
          </div>
          <Toaster />
        </div>
      </HelmetProvider>
    );
  }

  if (!article) {
    return (
      <HelmetProvider>
        <div className="min-h-screen bg-[#F7F4EE] text-neutral-900 dark:bg-gray-900 dark:text-white">
          <FestiveTheme />
          <Helmet>
            <title>Article Not Found | Cheshire Today</title>
            <meta name="robots" content="noindex, nofollow" />
          </Helmet>

          <NewsHeader
            categories={categories}
            activeCategory="all"
            onCategoryChange={() => navigate("/")}
            onSearch={() => {}}
          />

          <main className="container mx-auto px-4 py-16 max-w-6xl">
            <h1 className="text-4xl font-extrabold text-foreground mb-3">Article Not Found</h1>
            <p className="text-muted-foreground mb-6">{errorMsg || "Sorry, this link may be incorrect."}</p>
            <button
              onClick={() => navigate("/")}
              className="inline-flex items-center justify-center rounded-md bg-sky-700 px-4 py-2 text-white font-medium hover:bg-sky-800"
              data-testid="go-home-btn"
            >
              Go to Homepage
            </button>
          </main>

          <NewsFooter />
          <Toaster />
        </div>
      </HelmetProvider>
    );
  }

  const published = formatDateTime(article.publishedDate || article.published_at || article.created_at);

  const canonicalUrl = `${publicUrl}/article/${articleId}`;

  const absoluteImageUrl = (() => {
    const img = String(article?.image || "").trim();
    if (!img) return "";
    if (/^https?:\/\//i.test(img)) return img;
    // Support relative paths (e.g. /images/x.jpg)
    return `${publicUrl}${img.startsWith("/") ? "" : "/"}${img}`;
  })();

  const jsonLdNewsArticle = {
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    mainEntityOfPage: { "@type": "WebPage", "@id": canonicalUrl },
    headline: safeTitle || "Article",
    description,
    image: absoluteImageUrl ? [absoluteImageUrl] : undefined,
    datePublished: article?.publishedDate || article?.published_at || article?.created_at || undefined,
    dateModified: article?.updated_at || article?.publishedDate || article?.published_at || article?.created_at || undefined,
    author: { "@type": "Organization", name: "Cheshire Today" },
    publisher: {
      "@type": "Organization",
      name: "Cheshire Today",
      logo: {
        "@type": "ImageObject",
        url: `${publicUrl}/logo.png`,
      },
    },
  };

  return (
    <HelmetProvider>
      <div className="min-h-screen bg-[#F7F4EE] text-neutral-900 dark:bg-gray-900 dark:text-white">
        <FestiveTheme />

        <Helmet>
          <title>{safeTitle || "Article"} | Cheshire Today</title>
          <meta name="description" content={description} />

          <link rel="canonical" href={canonicalUrl} />

          {/* Structured data for Google */}
          <script type="application/ld+json">
            {JSON.stringify(jsonLdNewsArticle)}
          </script>

          <meta property="og:type" content="article" />
          <meta property="og:url" content={`${publicUrl}/article/${articleId}`} />
          <meta property="og:title" content={safeTitle} />
          <meta property="og:description" content={description} />
          {absoluteImageUrl && <meta property="og:image" content={absoluteImageUrl} />}

          <meta name="twitter:card" content="summary_large_image" />
          <meta name="twitter:url" content={`${publicUrl}/article/${articleId}`} />
          <meta name="twitter:title" content={safeTitle} />
          <meta name="twitter:description" content={description} />
          {absoluteImageUrl && <meta name="twitter:image" content={absoluteImageUrl} />}
        </Helmet>

        <NewsHeader
          categories={categories}
          activeCategory="all"
          onCategoryChange={() => navigate("/")}
          onSearch={() => {}}
        />

        <main className="mx-auto w-full max-w-5xl px-4 sm:px-6 lg:px-8 py-8 md:py-12">
          <div className="mb-6">
            <button onClick={() => navigate(-1)} className="text-sm text-slate-700 hover:underline underline-offset-2 dark:text-slate-200">
              ← Back
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <article className="lg:col-span-8">
              <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-foreground">{safeTitle}</h1>

              <div className="mt-3 text-sm text-muted-foreground flex items-center gap-3">
                <span>{published}</span>
                <button onClick={handleShare} className="ml-auto text-slate-700 hover:underline underline-offset-2 text-sm dark:text-slate-200 dark:hover:text-white">
                  Share
                </button>
              </div>

              {article.image && (
                <img
                  src={absoluteImageUrl || article.image}
                  alt={safeTitle || "Article image"}
                  loading="lazy"
                  decoding="async"
                  width="1200"
                  height="630"
                  className="w-full rounded-xl mt-6 mb-6 object-cover"
                />
              )}
<div className="rounded-2xl bg-[#FBFAF7] dark:bg-transparent border border-[#E6E1D8] dark:border-border p-4 md:p-6">
                <div className="prose prose-lg prose-slate max-w-3xl whitespace-pre-wrap leading-8 text-slate-800 dark:text-slate-100 dark:prose-invert prose-p:my-5 prose-li:my-2 prose-a:text-slate-700 prose-a:underline-offset-2 dark:prose-a:text-slate-200">
                {safeText(mainContent)}
              </div>


              {(article.source || article.source_url) && (
                <div className="mt-8 pt-6 border-t border-border">
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Source:{" "}
                    {(article.sourceUrl || article.source_url) ? (
                      <a
                        href={article.sourceUrl || article.source_url}
                        target="_blank"
                        rel="nofollow noopener noreferrer"
                        className="font-medium text-foreground hover:underline underline-offset-2"
                      >
                        {safeText(article.source) || "View original"}
                      </a>
                    ) : (
                      <span className="font-medium text-foreground">{safeText(article.source)}</span>
                    )}
                  </p>

                  {attribution ? (
                    <p className="mt-2 text-[11px] text-muted-foreground whitespace-pre-wrap leading-relaxed">
                      {safeText(attribution)}
                    </p>
                  ) : null}
                </div>
              )}

              {contextToolType ? <ContextTools type={contextToolType} /> : null}

              </div>

              <div className="mt-6">
                <GuidesInlinePromo guides={guides} />
                
              <GuidePromoBlock guides={guides} category={article?.category} />
              </div>

              <AuthorBox
                name="Cheshire Today Editorial Team"
                category="AI, technology, finance and tax"
              />

              {/* More stories (publisher-style, subtle) */}
              {Array.isArray(moreStories) && moreStories.length > 0 && (
                <section className="mt-10">
                  <div className="flex items-center justify-between mb-3">
                    <h2 className="text-sm font-extrabold tracking-tight text-neutral-900 dark:text-white">
                      More stories
                    </h2>

                    {moreStories.length > 4 && (
                      <button
                        type="button"
                        onClick={() => setMoreStoriesOpen((v) => !v)}
                        className="text-xs font-semibold text-slate-700 hover:underline underline-offset-2 dark:text-slate-200"
                      >
                        {moreStoriesOpen ? "Show less" : "Show more"}
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {(moreStoriesOpen ? moreStories.slice(0, 12) : moreStories.slice(0, 4)).map((a, idx) => (
                      <div
                        key={a.id || a._id || idx}
                        onClick={() => navigate("/article/" + (a.id || a._id))}
                        className="cursor-pointer group flex gap-3 rounded-xl border border-[#E6E1D8] dark:border-gray-800 bg-[#FBFAF7] dark:bg-gray-900/30 p-3 hover:bg-[#F2EEE6] dark:hover:bg-gray-900 transition"
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") navigate("/article/" + (a.id || a._id));
                        }}
                      >
                        <div className="relative overflow-hidden rounded-lg flex-shrink-0">
                          {a.image ? (
                            <img
                              src={a.image}
                              alt={a.title || "Story image"}
                              className="h-14 w-20 object-cover group-hover:scale-105 transition-transform duration-300"
                            />
                          ) : (
                            <div className="h-14 w-20 bg-[#F2EEE6] rounded-lg" />
                          )}
                        </div>

                        <div className="min-w-0">
                          <div className="mb-1 flex items-center gap-2">
                            <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-[#F2EEE6] dark:bg-gray-800 text-neutral-700 dark:text-gray-200">
                              {a.category || "News"}
                            </span>
                            <span className="text-[10px] text-neutral-500 dark:text-gray-400">
                              {fmtShort(a.publishedDate || a.published_at || a.created_at)}
                            </span>
                          </div>

                          <div className="text-sm font-semibold text-neutral-900 dark:text-white line-clamp-2 group-hover:underline underline-offset-2">
                            {a.title}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              )}
            </article>

            <aside className="lg:col-span-4">
              <div className="sticky top-6 space-y-6">
                <div className="rounded-xl border border-[#E6E1D8] bg-[#FBFAF7] p-4 dark:border-gray-800 dark:bg-gray-900/30">
                  <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-bold">More in {pillarLabel}</h3>
                  <span className="text-[11px] px-2 py-1 rounded bg-muted text-muted-foreground">
                    {pillarLabel}
                  </span>
                </div>
                  <RelatedArticles
                    articleId={articleId}
                    variant="sidebar"
                    limit={6}
                    onArticleClick={(a) => navigate("/article/" + a.id)}
                  />
                </div>

                
                <div className="rounded-xl border border-dashed border-border bg-card p-4 text-sm text-muted-foreground">
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-semibold text-foreground">Sponsored</div>
                    <span className="text-xs px-2 py-1 rounded bg-muted text-muted-foreground">Ad</span>
                  </div>
                  <div>Ad slot / affiliate widget placeholder (monetisation phase).</div>
                  <a
                    href="/advertise"
                    className="inline-block mt-2 text-slate-700 hover:underline underline-offset-2 font-semibold dark:text-slate-200"
                  >
                    Advertise with us →
                  </a>
                </div>

                <div className="rounded-xl border border-border bg-card p-4">
                  <h3 className="text-sm font-semibold text-foreground mb-2">Get the Cheshire Today briefing</h3>
                  <p className="text-sm text-muted-foreground mb-3">A short email with the top local stories — no spam.</p>
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      toast({ title: "Coming soon", description: "Newsletter signup will be enabled shortly." });
                    }}
                    className="flex gap-2"
                  >
                    <input
                      type="email"
                      required
                      placeholder="you@example.com"
                      className="flex-1 rounded-md border border-input bg-background text-foreground px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-200 placeholder:text-muted-foreground"
                    />
                    <button
                      type="submit"
                      className="rounded-md bg-sky-700 px-3 py-2 text-sm font-medium text-white hover:bg-sky-800"
                    >
                      Sign up
                    </button>
                  </form>
                  <p className="mt-2 text-xs text-muted-foreground">You can unsubscribe anytime.</p>
                </div>
                </div>
            </aside>
          </div>
        </main>

        <NewsFooter />
        <Toaster />
      </div>
    </HelmetProvider>

  );
}
