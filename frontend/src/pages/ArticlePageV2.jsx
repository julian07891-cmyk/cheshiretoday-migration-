import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Helmet, HelmetProvider } from "react-helmet-async";

import NewsHeader from "../components/NewsHeader";
import NewsFooter from "../components/NewsFooter";
import FestiveTheme from "../components/FestiveTheme";

import { Toaster } from "../components/ui/toaster";
import { toast } from "../hooks/use-toast.js";
import { Loader2 } from "lucide-react";

import { getApiUrl } from "../utils/api";

function safeText(s) {
  return (s || "").toString();
}

function buildDescription(article) {
  const summary = safeText(article?.summary);
  if (summary.trim().length >= 40) return summary.trim().slice(0, 200);
  return safeText(article?.content).trim().slice(0, 200);
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

export default function ArticlePageV2({ categories }) {
  const { articleId } = useParams();
  const navigate = useNavigate();

  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);

  const API_BASE = useMemo(() => getApiUrl().replace(/\/$/, ""), []);
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
      } catch (e) {
        if (!mounted) return;
        console.error("Error fetching article:", e);
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
  }, [API_BASE, articleId]);

  const handleShare = async () => {
    const shareUrl = `${publicUrl}/article/${articleId}`;
    try {
      await navigator.clipboard.writeText(shareUrl);
      toast({ title: "Link Copied!", description: "Article link copied to clipboard!" });
    } catch {
      // ignore
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

  if (!article) {
    return (
      <HelmetProvider>
        <div className="min-h-screen bg-gray-50 flex flex-col">
          <FestiveTheme />
          <Helmet>
            <title>Article Not Found | Cheshire Today</title>
            <meta name="robots" content="noindex, nofollow" />
          </Helmet>

          <NewsHeader
            categories={categories}
            activeCategory="all"
            onCategoryChange={() => {}}
            onSearch={() => {}}
          />

          <main className="flex-1 flex items-center justify-center">
            <div className="text-center px-4">
              <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-gray-800 mb-4">
                Article Not Found
              </h1>
              <p className="text-gray-600 mb-6">
                Sorry, this article may have been removed or the link is incorrect.
              </p>
              <button
                onClick={() => navigate("/")}
                className="inline-flex items-center justify-center rounded-md bg-emerald-600 px-4 py-2 text-white font-semibold hover:bg-emerald-700"
                data-testid="go-home-btn"
              >
                Go to Homepage
              </button>
            </div>
          </main>

          <NewsFooter />
          <Toaster />
        </div>
      </HelmetProvider>
    );
  }

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

        <main className="container mx-auto px-4 py-10 max-w-3xl">
          <div className="mb-6">
            <button
              onClick={() => navigate(-1)}
              className="text-sm text-emerald-700 hover:underline"
            >
              ← Back
            </button>
          </div>

          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-gray-900">
            {article.title}
          </h1>

          <div className="mt-3 text-sm text-gray-600 flex items-center gap-3">
            <span>{formatDateTime(article.publishedDate || article.published_at || article.created_at)}</span>
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

          <div className="prose prose-lg max-w-none whitespace-pre-wrap">
            {article.content}
          </div>
        </main>

        <NewsFooter />
        <Toaster />
      </div>
    </HelmetProvider>
  );
}
