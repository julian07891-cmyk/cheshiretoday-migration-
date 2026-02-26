import React, { Suspense, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Helmet, HelmetProvider } from "react-helmet-async";

import NewsHeader from "../components/NewsHeader";
import NewsFooter from "../components/NewsFooter";
import NewsletterPopup from "../components/NewsletterPopup";
import FestiveTheme from "../components/FestiveTheme";

import { getApiUrl } from "../utils/api";

import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Separator } from "../components/ui/separator";
import { Toaster } from "../components/ui/toaster";
import { toast } from "../hooks/use-toast.js";

import { Loader2, Clock, ExternalLink, Share2, User } from "lucide-react";

import RelatedArticles from "../components/RelatedArticles";
import { filterEditorialPool } from "../utils/editorialPolicy";

// --- auto-stubs injected for missing modules (build-safe) ---
const AffiliateWidgetInline = () => null;
const AffiliateWidgetEndArticle = () => null;
const JobsInlineBanner = () => null;
const SubscribeInlineBanner = () => null;
const SAMPLE_PRODUCTS = { default: [] };
async function fetchDatabaseProducts(){ return { products: [], by_category: {} }; }
// --- end stubs ---


// Affiliate widgets (already used in App.js)
// These were referenced in App.js ArticlePage. Keep same behavior.
// API base (works in local + production)
const API_BASE = getApiUrl().replace(/\/$/, "");
// Small helpers
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
  // Prefer summary; fallback to first 200 chars of content
  const summary = safeText(article?.summary);
  if (summary.trim().length >= 40) return summary.trim().slice(0, 200);
  return safeText(article?.content).trim().slice(0, 200);
}

export default function ArticlePageV2({ categories }) {
  const { articleId } = useParams();
  const navigate = useNavigate();

  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [affiliateProducts, setAffiliateProducts] = useState({ inline: [], endArticle: [] });

  const publicUrl =
    process.env.REACT_APP_PUBLIC_URL ||
    (typeof window !== "undefined" ? window.location.origin : "");

  const description = useMemo(() => buildDescription(article), [article]);

  useEffect(() => {
    let mounted = true;

    async function fetchArticle() {
      try {
        setLoading(true);
        const res = await fetch(`${API_BASE}/api/articles/${articleId}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!mounted) return;
        setArticle(data);
        setError(null);
      } catch (e) {
        if (!mounted) return;
        console.error("Error fetching article:", e);
        setError("Article not found");
        setArticle(null);
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

  // Affiliate products distribution (same logic as your current page)
  useEffect(() => {
    if (!article) return;

    let mounted = true;

    const loadAffiliateProducts = async () => {
      const category = article.category || "default";

      const categoryProducts = SAMPLE_PRODUCTS[category] || [];
      const defaultProducts = SAMPLE_PRODUCTS["default"] || [];
      let allProducts = [...categoryProducts, ...defaultProducts];

      const dbData = await fetchDatabaseProducts();
      if (!mounted) return;

      if (dbData && dbData.products && dbData.products.length > 0) {
        const dbCategoryProducts = dbData.by_category?.[category] || [];
        const dbDefaultProducts = dbData.by_category?.["default"] || [];
        allProducts = [...dbCategoryProducts, ...dbDefaultProducts, ...allProducts];
      }

      const unique = allProducts.filter(
        (product, index, self) => index === self.findIndex((p) => p.name === product.name)
      );

      const shuffled = [...unique].sort(() => 0.5 - Math.random());

      setAffiliateProducts({
        inline: shuffled.slice(0, 2),
        endArticle: shuffled.slice(2, 6),
      });
    };

    loadAffiliateProducts();
    return () => {
      mounted = false;
    };
  }, [article]);

  // 404
  if (error) {
    return (
      <HelmetProvider>
        <div className="min-h-screen bg-gray-50 flex flex-col">
          <Helmet>
            <title>Article Not Found | Cheshire Today</title>
            <meta name="robots" content="noindex, nofollow" />
          </Helmet>

          <NewsHeader
            categories={categories}
            onCategoryChange={() => {}}
            activeCategory="all"
            onSearch={() => {}}
          />

          <main className="flex-1 flex items-center justify-center">
            <div className="text-center px-4">
              <h1 className="text-4xl font-bold text-gray-800 mb-4">Article Not Found</h1>
              <p className="text-gray-600 mb-6">
                Sorry, this article may have been removed or the link is incorrect.
              </p>
              <Button onClick={() => navigate("/")} data-testid="go-home-btn">
                Go to Homepage
              </Button>
            </div>
          </main>

          <NewsFooter />
        </div>
      </HelmetProvider>
    );
  }

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
        <div className="min-h-screen bg-gray-50">
          <FestiveTheme />
          <NewsHeader
            categories={categories}
            activeCategory="all"
            onCategoryChange={() => navigate("/")}
          />
          <div className="container mx-auto px-4 py-20">
            <div className="flex flex-col items-center justify-center">
              <Loader2 className="h-16 w-16 animate-spin text-emerald-600 mb-4" />
              <p className="text-lg text-gray-600">Loading article...</p>
            </div>
          </div>
          <Toaster />
        </div>
      </HelmetProvider>
    );
  }

  if (!article) return null;

  // NOTE: This is still your existing layout, moved into this component.
  // Next step we will redesign the markup here (without touching router logic).
  return (
    <HelmetProvider>
      <div className="min-h-screen bg-gray-50">
        <FestiveTheme />

        <Helmet>
          <title>{article.title} | Cheshire Today</title>
          <meta name="description" content={description} />

          <meta property="og:type" content="article" />
          <meta property="og:url" content={`${publicUrl}/article/${articleId}`} />
          <meta property="og:title" content={article.title} />
          <meta property="og:description" content={description} />
          <meta property="og:image" content={article.image} />
          <meta property="og:image:secure_url" content={article.image} />
          <meta property="og:image:width" content="1200" />
          <meta property="og:image:height" content="630" />

          <meta name="twitter:card" content="summary_large_image" />
          <meta name="twitter:url" content={`${publicUrl}/article/${articleId}`} />
          <meta name="twitter:title" content={article.title} />
          <meta name="twitter:description" content={description} />
          <meta name="twitter:image" content={article.image} />

          <script type="application/ld+json">
            {JSON.stringify({
              "@context": "https://schema.org",
              "@type": "NewsArticle",
              headline: article.title,
              image: [article.image],
              datePublished: article.publishedDate,
              dateModified: article.publishedDate,
              author: {
                "@type": "Person",
                name: article.author || "Cheshire Today",
              },
              publisher: {
                "@type": "Organization",
                name: "Cheshire Today",
                logo: {
                  "@type": "ImageObject",
                  url: `${publicUrl}/logo.png`,
                },
              },
              description,
              mainEntityOfPage: {
                "@type": "WebPage",
                "@id": `${publicUrl}/article/${articleId}`,
              },
            })}
          </script>
        </Helmet>

        <NewsHeader
          categories={categories}
          activeCategory="all"
          onCategoryChange={() => navigate("/")}
        />

        <main className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            <Button variant="outline" onClick={() => navigate("/")} className="mb-6">
              ← Back to Home
            </Button>

            <article className="bg-white rounded-lg shadow-lg overflow-hidden">
              <div className="relative h-96">
                <img
                  src={article.image}
                  alt={article.title}
                  className="w-full h-full object-cover"
                  loading="eager"
                  fetchpriority="high"
                  decoding="async"
                  width="800"
                  height="384"
                />
                <Badge className="absolute top-4 left-4 bg-emerald-600 text-white">
                  {article.category}
                </Badge>
              </div>

              <div className="p-8">
                <h1 className="text-4xl font-bold text-gray-900 mb-4 leading-tight">
                  {article.title}
                </h1>

                <div className="flex items-center flex-wrap gap-4 text-sm text-gray-600 mb-6 pb-6 border-b">
                  <div className="flex items-center">
                    <User className="h-4 w-4 mr-2" />
                    <span className="font-medium">{article.author}</span>
                  </div>
                  <div className="flex items-center">
                    <Clock className="h-4 w-4 mr-2" />
                    {formatDateTime(article.publishedDate)}
                  </div>

                  {article.source && (
                    <div className="flex items-center">
                      <span className="text-gray-400">via</span>
                      {article.source_url ? (
                        <a
                          href={article.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="ml-1 text-emerald-600 hover:text-emerald-700 hover:underline font-medium"
                          data-testid="article-source-link"
                        >
                          {article.source}
                        </a>
                      ) : (
                        <span className="ml-1 font-medium">{article.source}</span>
                      )}
                    </div>
                  )}
                </div>

                <div className="prose prose-lg max-w-none mb-8">
                  <p className="text-gray-800 text-lg md:text-xl leading-relaxed mb-4 whitespace-pre-wrap">
                    {article.content}
                  </p>
                </div>

                <Suspense fallback={null}>
                  <AffiliateWidgetInline
                    category={article.category}
                    title="You Might Like"
                    products={affiliateProducts.inline}
                  />
                </Suspense>

                <div className="space-y-2 my-6">
                  <Suspense fallback={null}>
                    <JobsInlineBanner />
                  </Suspense>
                  <SubscribeInlineBanner />
                </div>

                <Separator className="my-6" />

                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div className="flex flex-wrap gap-2">
                    {article.tags &&
                      article.tags.map((tag) => (
                        <Badge
                          key={tag}
                          variant="outline"
                          className="text-xs text-gray-700 dark:text-gray-200 border-gray-400 dark:border-gray-500 bg-gray-100 dark:bg-gray-700 font-medium"
                        >
                          #{tag}
                        </Badge>
                      ))}
                  </div>

                  <Button
                    variant="outline"
                    onClick={handleShare}
                    className="hover:bg-emerald-50 hover:text-emerald-700 hover:border-emerald-300"
                  >
                    <Share2 className="h-4 w-4 mr-2" />
                    Share Article
                  </Button>
                </div>

                <RelatedArticles
                  articleId={articleId}
                  onArticleClick={(a) => navigate(`/article/${a._id || a.id}`)}
                />

                {article.source_url && (
                  <div
                    className="mt-8 p-4 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                    data-testid="source-attribution-box"
                  >
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                      This article was originally published by <strong>{article.source}</strong>
                    </p>
                    <a
                      href={article.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center text-emerald-600 hover:text-emerald-700 font-medium text-sm hover:underline"
                      data-testid="read-original-link"
                    >
                      <ExternalLink className="h-4 w-4 mr-1" />
                      Read the original article at {article.source}
                    </a>
                  </div>
                )}

                <div className="mt-8">
                  <Suspense fallback={null}>
                    <AffiliateWidgetEndArticle
                      category={article.category}
                      products={affiliateProducts.endArticle}
                    />
                  </Suspense>
                </div>
              </div>
            </article>
          </div>
        </main>

        <NewsFooter />
        <Toaster />
        <NewsletterPopup />
      </div>
    </HelmetProvider>
  );
}
