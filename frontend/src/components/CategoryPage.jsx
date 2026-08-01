import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { ArrowLeft, BookOpen, Loader2 } from "lucide-react";
import { getApiUrl } from "../utils/api";
import { buildArticleUrl } from "../utils/articleUrl";
import { filterEditorialPool } from "../utils/editorialPolicy";
import { CATEGORY_HUBS, findCategoryHub } from "../config/publicHubs";
import NewsHeader from "./NewsHeader";
import NewsFooter from "./NewsFooter";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { categories } from "../mockData";

const CategoryPage = ({ categorySlug }) => {
  const hub = findCategoryHub(categorySlug);
  const navigate = useNavigate();
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const publicUrl =
    process.env.REACT_APP_PUBLIC_URL || "https://cheshiretoday.co.uk";
  const canonical = `${publicUrl}/category/${hub.slug}`;

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          `${getApiUrl()}/api/articles?category=${encodeURIComponent(
            hub.canonicalCategory
          )}&limit=30&with_total=true`
        );
        if (!response.ok) throw new Error("Category unavailable");
        const data = await response.json();
        const list = Array.isArray(data) ? data : data.articles || [];
        if (mounted) {
          setArticles(filterEditorialPool(list));
        }
      } catch (_) {
        if (mounted) {
          setArticles([]);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    return () => {
      mounted = false;
    };
  }, [hub.canonicalCategory]);

  const structuredData = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: `${hub.label} | Cheshire Today`,
    description: hub.description,
    url: canonical,
    isPartOf: {
      "@type": "WebSite",
      name: "Cheshire Today",
      url: publicUrl,
    },
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <Loader2 className="h-12 w-12 animate-spin text-[#1E3A8A]" />
      </div>
    );
  }

  return (
    <>
      <Helmet defer={false}>
        <title>{`${hub.title} | Cheshire Today`}</title>
        <meta name="description" content={hub.description} />
        <meta name="robots" content="index, follow" />
        <link rel="canonical" href={canonical} />
        <meta property="og:title" content={`${hub.title} | Cheshire Today`} />
        <meta property="og:description" content={hub.description} />
        <meta property="og:url" content={canonical} />
        <meta property="og:type" content="website" />
      </Helmet>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <NewsHeader
          categories={categories}
          activeCategory={hub.label.toLowerCase()}
          onCategoryChange={() => navigate("/")}
        />
        <main className="container mx-auto px-4 py-8">
          <Button
            variant="ghost"
            onClick={() => navigate("/")}
            className="mb-4 text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to All News
          </Button>
          <header className="mb-8">
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white">
              {hub.label}
            </h1>
            <p className="text-gray-700 dark:text-gray-300 mt-3 max-w-2xl">
              {hub.description}
            </p>
            <p className="text-gray-500 dark:text-gray-400 mt-2">
              {articles.length} public articles
            </p>
          </header>
          {articles.length === 0 ? (
            <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg">
              <BookOpen className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">
                No public articles are currently available for {hub.label}
              </h2>
              <p className="text-gray-500 dark:text-gray-400">
                Check back soon for new reporting.
              </p>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {articles.map((article) => (
                <article
                  key={article.id}
                  onClick={() => navigate(buildArticleUrl(article))}
                  className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden cursor-pointer hover:shadow-lg transition-shadow"
                >
                  {article.image && (
                    <img
                      src={article.image}
                      alt={article.title || ""}
                      className="w-full h-48 object-cover"
                    />
                  )}
                  <div className="p-4">
                    <Badge className="mb-2 bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                      {article.category}
                    </Badge>
                    <h2 className="text-lg md:text-xl font-semibold text-gray-900 dark:text-white line-clamp-2 mb-2">
                      {article.title}
                    </h2>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {article.source}
                    </p>
                  </div>
                </article>
              ))}
            </div>
          )}
          <nav className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Explore Other Topics
            </h2>
            <div className="flex flex-wrap gap-3">
              {CATEGORY_HUBS.filter((item) => item.slug !== hub.slug).map(
                (item) => (
                  <Button
                    key={item.slug}
                    variant="outline"
                    onClick={() => navigate(`/category/${item.slug}`)}
                  >
                    {item.label}
                  </Button>
                )
              )}
            </div>
          </nav>
        </main>
        <NewsFooter />
      </div>
    </>
  );
};

export default CategoryPage;
