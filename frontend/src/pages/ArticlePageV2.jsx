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

function formatDateTime(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function safeText(s) {
  return (s || "").toString();
}

function buildDescription(article) {
  const summary = safeText(article?.summary);
  if (summary.trim().length >= 40) return summary.trim().slice(0, 200);
  return safeText(article?.content).trim().slice(0, 200);
}

// Shrink the “originally published by …” block so it doesn’t distract.
// Works whether backend appended it as plain text lines or a paragraph.
function splitAttribution(rawContent) {
  const content = safeText(rawContent);

  const marker = "This article was originally published by";
  const idx = content.indexOf(marker);

  if (idx === -1) {
    return { main: content, attribution: "" };
  }

  const main = content.slice(0, idx).trim();
  const attribution = content.slice(idx).trim();

  return { main, attribution };
}

export default function ArticlePageV2({ categories }) {
  const { articleId } = useParams();
  const navigate = useNavigate();

  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  const publicUrl =
    process.env.REACT_APP_PUBLIC_URL ||
    (typeof window !== "undefined" ? window.location.origin : "");

  const description = useMemo(() => buildDescription(article), [article]);

  const { main: mainContent, attribution } = useMemo(
    () => splitAttribution(article?.content),
    [article]
  );

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
      toast({
        title: "Link Copied!",
        description: "Article link copied to clipboard!",
      });
    }
  };

  if (loading) {
    return (
      <HelmetProvider>
        <div className="min-h-screen bg-background">
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
        <div className="min-h-screen bg-background">
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

  return (
    <HelmetProvider>
      <div className="min-h-screen bg-background">
        <FestiveTheme />

        <Helmet>
          <title>{article.title} | Cheshire Today</title>
          <meta name="description" content={description} />

          <meta property="og:type" content="article" />
          <meta property="og:url" content={`${publicUrl}/article/${articleId}`} />
          <meta property="og:title" content={article.title} />
          <meta property="og:description" content={description} />
          {article.image && <meta property="og:image" content={article.image} />}

          <meta name="twitter:card" content="summary_large_image" />
          <meta name="twitter:url" content={`${publicUrl}/article/${articleId}`} />
          <meta name="twitter:title" content={article.title} />
          <meta name="twitter:description" content={description} />
          {article.image && <meta name="twitter:image" content={article.image} />}
        </Helmet>

        <NewsHeader
          categories={categories}
          activeCategory="all"
          onCategoryChange={() => navigate("/")}
          onSearch={() => {}}
        />

        {/* Layout B: content + right sidebar */}
        <main className="container mx-auto px-4 py-10 max-w-6xl">
          <div className="mb-6">
            <button
              onClick={() => navigate(-1)}
              className="text-sm text-emerald-700 hover:underline"
            >
              ← Back
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Main article */}
            <article className="lg:col-span-8">
              <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-foreground">
                {article.title}
              </h1>

              <div className="mt-3 text-sm text-muted-foreground flex items-center gap-3">
                <span>
                  {formatDateTime(
                    article.publishedDate || article.published_at || article.created_at
                  )}
                </span>
                <button
                  onClick={handleShare}
                  className="ml-auto text-emerald-700 hover:underline text-sm"
                >
                  Share
                </button>
              </div>

              {article.image && (
                <img
                  src={article.image}
                  alt={article.title}
                  className="w-full rounded-xl mt-6 mb-6 object-cover"
                />
              )}

              <div className="prose prose-lg max-w-none whitespace-pre-wrap dark:prose-invert prose-a:text-emerald-700 prose-a:underline-offset-2 dark:prose-a:text-emerald-400">
                {mainContent}
              </div>

              {/* Make source attribution smaller + less prominent */}
              {attribution && (
                <div className="mt-6 pt-4 border-t border-border">
                  <p className="text-xs text-gray-400 leading-relaxed">
  {attribution && <span>{attribution.replace("This article was originally published by", "Originally published by")}</span>}
  {(article.sourceUrl || article.source_url || article.link || article.url) && (
    <>{" · "}
      <a
        href={article.sourceUrl || article.source_url || article.link || article.url}
        target="_blank"
        rel="nofollow noopener noreferrer"
        className="hover:text-muted-foreground underline decoration-dotted underline-offset-2"
      >
        View source
      </a>
    </>
  )}
</p>
                </div>
              )}
            </article>

            {/* Sidebar */}
            <aside className="lg:col-span-4">
              <div className="sticky top-6 space-y-6">
                {/* Related articles in sidebar format */}
                <RelatedArticles
                  articleId={articleId}
                  variant="sidebar"
                  limit={4}
                  onArticleClick={(a) => navigate(`/article/${a.id}`)}
                />


                {/* Monetisation placeholder (sponsored/affiliate/ad) */}
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

                  {/* Newsletter (non-intrusive, keeps readers coming back) */}
  <div className="rounded-xl border border-border bg-card p-4">
    <h3 className="text-sm font-semibold text-foreground mb-2">Get the Cheshire Today briefing</h3>
    <p className="text-sm text-muted-foreground mb-3">A short email with the top local stories — no spam.</p>
    <form onSubmit={(e) => { e.preventDefault(); toast({ title: "Coming soon", description: "Newsletter signup will be enabled shortly." }); }} className="flex gap-2">
      <input
        type="email"
        required
        placeholder="you.com"
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

  {/* Explore by area (internal routes) */}
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
