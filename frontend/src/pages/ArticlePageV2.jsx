import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Helmet, HelmetProvider } from "react-helmet-async";

import NewsHeader from "../components/NewsHeader";
import NewsFooter from "../components/NewsFooter";
import FestiveTheme from "../components/FestiveTheme";
import RelatedArticles from "../components/RelatedArticles";

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
    <div className="mt-8 p-5 rounded-xl border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20">
      <div className="text-sm font-semibold text-blue-700 dark:text-blue-300 mb-2">🔎 AI Guides</div>
      <div className="space-y-2">
        {ordered.map((g) => (
          <div
            key={g.slug}
            className="rounded-lg border border-blue-100 dark:border-blue-900 bg-white/60 dark:bg-transparent p-3"
          >
            <a
              href={`/guides/${g.slug}`}
              className="block font-bold text-blue-800 dark:text-blue-200 hover:underline"
            >
              {safeText(g.title) || g.slug}
            </a>
            <div className="text-xs mt-1 text-gray-700 dark:text-gray-400">
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
    <div className="mt-8 p-5 rounded-xl border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20">
      <div className="text-sm font-semibold text-blue-700 dark:text-blue-300 mb-1">In-depth Guide</div>
      <a href={href} className="block font-bold text-blue-900 dark:text-blue-200 hover:underline">
        {title}
      </a>
      <div className="text-sm mt-1 text-gray-700 dark:text-gray-400">
        Updated UK guide with recommendations and affiliate disclosures →
      </div>
    </div>
  );
};

export default function ArticlePageV2({ categories }) {
  const { articleId } = useParams();
  const navigate = useNavigate();

  const [article, setArticle] = useState(null);
  const [guides, setGuides] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  const publicUrl =
    process.env.REACT_APP_PUBLIC_URL || (typeof window !== "undefined" ? window.location.origin : "");

  const description = useMemo(() => buildDescription(article), [article]);
  const safeTitle = useMemo(() => safeText(article?.title), [article]);

  const rawBody = useMemo(() => {
    const c = article?.content;
    const s = article?.summary;
    if (typeof c === "string" && c.trim()) return c;
    if (typeof s === "string" && s.trim()) return s;
    // last-resort stringify avoidance: return empty instead of rendering objects
    return "";
  }, [article]);

  const { main: mainContent, attribution } = useMemo(() => splitAttribution(rawBody), [rawBody]);

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

        // Load AI Guides (authority pages). Non-blocking: page still works if this fails.
        try {
          const gRes = await fetch(getApiUrl().replace(/\/$/, "") + "/api/authority-pages");
          if (gRes.ok) {
            const gData = await gRes.json();
            const pages = Array.isArray(gData?.pages) ? gData.pages : [];
            if (mounted) setGuides(pages);
          }
        } catch (_) {
          // ignore
        }
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
        <div className="min-h-screen bg-neutral-50 text-slate-900 dark:bg-gray-900 dark:text-white">
          <FestiveTheme />
          <NewsHeader
            categories={categories}
            activeCategory="all"
            onCategoryChange={() => navigate("/")}
            onSearch={() => {}}
          />
          <div className="container mx-auto px-4 py-20">
            <div className="flex flex-col items-center justify-center">
              <Loader2 className="h-16 w-16 animate-spin text-emerald-600 mb-4" />
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
        <div className="min-h-screen bg-neutral-50 text-slate-900 dark:bg-gray-900 dark:text-white">
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
              className="inline-flex items-center justify-center rounded-md bg-emerald-600 px-4 py-2 text-white font-medium hover:bg-emerald-700"
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

  return (
    <HelmetProvider>
      <div className="min-h-screen bg-neutral-50 text-slate-900 dark:bg-gray-900 dark:text-white">
        <FestiveTheme />

        <Helmet>
          <title>{safeTitle || "Article"} | Cheshire Today</title>
          <meta name="description" content={description} />

          <meta property="og:type" content="article" />
          <meta property="og:url" content={`${publicUrl}/article/${articleId}`} />
          <meta property="og:title" content={safeTitle} />
          <meta property="og:description" content={description} />
          {article.image && <meta property="og:image" content={article.image} />}

          <meta name="twitter:card" content="summary_large_image" />
          <meta name="twitter:url" content={`${publicUrl}/article/${articleId}`} />
          <meta name="twitter:title" content={safeTitle} />
          <meta name="twitter:description" content={description} />
          {article.image && <meta name="twitter:image" content={article.image} />}
        </Helmet>

        <NewsHeader
          categories={categories}
          activeCategory="all"
          onCategoryChange={() => navigate("/")}
          onSearch={() => {}}
        />

        <main className="mx-auto w-full max-w-5xl px-4 sm:px-6 lg:px-8 py-8 md:py-12">
          <div className="mb-6">
            <button onClick={() => navigate(-1)} className="text-sm text-emerald-700 hover:underline">
              ← Back
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <article className="lg:col-span-8">
              <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-foreground">{safeTitle}</h1>

              <div className="mt-3 text-sm text-muted-foreground flex items-center gap-3">
                <span>{published}</span>
                <button onClick={handleShare} className="ml-auto text-emerald-700 hover:underline text-sm">
                  Share
                </button>
              </div>

              {article.image && (
                <img
                  src={article.image}
                  alt={safeTitle || "Article image"}
                  className="w-full rounded-xl mt-6 mb-6 object-cover"
                />
              )}

              <div className="rounded-2xl bg-white/70 dark:bg-transparent border border-slate-200/60 dark:border-border p-5 md:p-8">
                <div className="prose prose-lg prose-slate max-w-3xl whitespace-pre-wrap leading-8 text-slate-800 dark:text-slate-100 dark:prose-invert prose-p:my-5 prose-li:my-2 prose-a:text-emerald-700 prose-a:underline-offset-2 dark:prose-a:text-emerald-400">
                {safeText(mainContent)}
              </div>

              <GuidesInlinePromo guides={guides} />

              {(article.source || article.source_url) && (
                <div className="mt-8 pt-6 border-t border-border">
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Source:{" "}
                    {(article.sourceUrl || article.source_url) ? (
                      <a
                        href={article.sourceUrl || article.source_url}
                        target="_blank"
                        rel="nofollow noopener noreferrer"
                        className="font-medium text-foreground hover:underline"
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

              <GuidePromoBlock guides={guides} category={article?.category} />
              </div>
            </article>

            <aside className="lg:col-span-4">
              <div className="sticky top-6 space-y-6">
                <RelatedArticles
                  articleId={articleId}
                  variant="sidebar"
                  limit={4}
                  onArticleClick={(a) => navigate(`/article/${a.id}`)}
                />

                {Array.isArray(guides) && guides.length > 0 && (
                  <div className="rounded-xl border border-emerald-200 dark:border-emerald-800 bg-emerald-50/40 dark:bg-emerald-900/10 p-4">
                    <div className="text-xs font-semibold text-emerald-700 dark:text-emerald-300 mb-2">
                      AI Guides
                    </div>
                    <ul className="space-y-2 text-sm">
                      {guides.map((g) => (
                        <li key={g.slug}>
                          <a
                            href={`/guides/${g.slug}`}
                            className="font-semibold text-foreground hover:underline underline-offset-2"
                          >
                            🔥 {safeText(g.title) || g.slug}
                          </a>
                        </li>
                      ))}
                    </ul>
                    <div className="text-xs mt-3 text-muted-foreground">UK-focused comparisons &amp; best picks →</div>
                  </div>
                )}

                <div className="rounded-xl border border-dashed border-border bg-card p-4 text-sm text-muted-foreground">
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-semibold text-foreground">Sponsored</div>
                    <span className="text-xs px-2 py-1 rounded bg-muted text-muted-foreground">Ad</span>
                  </div>
                  <div>Ad slot / affiliate widget placeholder (monetisation phase).</div>
                  <a
                    href="/advertise"
                    className="inline-block mt-2 text-emerald-700 hover:underline font-semibold dark:text-emerald-400"
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
                      className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700"
                    >
                      Sign up
                    </button>
                  </form>
                  <p className="mt-2 text-xs text-muted-foreground">You can unsubscribe anytime.</p>
                </div>

                <div className="rounded-xl border border-border bg-card p-4">
                  <h3 className="text-sm font-semibold text-foreground mb-3">Local news by area</h3>
                  <div className="flex flex-wrap gap-2">
                    {[
                      "chester",
                      "crewe",
                      "warrington",
                      "macclesfield",
                      "wilmslow",
                      "northwich",
                      "congleton",
                      "nantwich",
                      "knutsford",
                      "ellesmere-port",
                    ].map((slug) => (
                      <button
                        key={slug}
                        onClick={() => navigate(`/`)}
                        className="rounded-full border border-input bg-background px-3 py-1 text-xs text-foreground hover:border-emerald-300 hover:text-emerald-700 dark:hover:text-emerald-400"
                      >
                        {slug.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                      </button>
                    ))}
                  </div>
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
