import React, { useEffect, useMemo, useState } from "react";
import { getApiUrl } from "../utils/api";
import { useNavigate } from "react-router-dom";
import HomepageLayout from "../components/homepage/HomepageLayout";
import HomepageHeader from "../components/homepage/HomepageHeader";
import CompactArticleCard from "../components/CompactArticleCard";
import HeroStoryCard from "../components/homepage/HeroStoryCard";
import TopStoriesGrid from "../components/homepage/TopStoriesGrid";
import NewsFooter from "../components/NewsFooter";

/* ---------- helpers ---------- */
function safeDateMs(d) {
  const t = Date.parse(d);
  return Number.isFinite(t) ? t : 0;
}

function articleKey(a, fallback = "x") {
  return a?.id || a?._id || fallback;
}

function isLocal(a) {
  const cat = (a?.category || "").toLowerCase();
  const scope = (a?.scope || "").toLowerCase();
  return cat.includes("local") || scope.includes("cheshire");
}

function isFeatured(a) {
  return Boolean(a?.featured);
}

/* ---------- page ---------- */
export default function HomePageV1() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const navigate = useNavigate();

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        setLoading(true);
        setErr("");

        const res = await fetch(getApiUrl() + "/api/articles?limit=50");
        if (!res.ok) throw new Error(`API ${res.status}`);

        const data = await res.json();
        const list = Array.isArray(data) ? data : data?.articles || [];
        if (mounted) setArticles(list);
      } catch (e) {
        if (mounted) setErr(e?.message || "Failed to load");
      } finally {
        if (mounted) setLoading(false);
      }
    }

    load();
    return () => {
      mounted = false;
    };
  }, []);

  /* ---------- ordering ---------- */
  const newestFirst = useMemo(() => {
    return [...(articles || [])].sort(
      (a, b) => safeDateMs(b?.publishedDate) - safeDateMs(a?.publishedDate),
    );
  }, [articles]);

  /* ---------- hero ---------- */
  const hero = useMemo(() => {
    return newestFirst.find(isLocal) || newestFirst[0] || null;
  }, [newestFirst]);

  /* ---------- top stories (4) ---------- */
  const topStories = useMemo(() => {
    const heroId = hero ? articleKey(hero) : null;

    return newestFirst
      .filter((a) => articleKey(a) !== heroId)
      .filter(isFeatured)
      .slice(0, 4)
      .map((a, i) => ({
        id: articleKey(a, `top-${i}`),
        title: a?.title || "Untitled",
        image: a?.image || "",
        category: a?.category || "Local News",
        town: a?.location || "Cheshire",
        publishedDate: a?.publishedDate || "",
        url: `/article/${articleKey(a)}`,
        readTime: 3,
      }));
  }, [newestFirst, hero]);

  /* ---------- buckets ---------- */
  const aiFeed = useMemo(() => newestFirst.filter(a => (a.section || "").startsWith("ai")).slice(0,4), [newestFirst]);
  const financeFeed = useMemo(() => newestFirst.filter(a => a.category === "Business" || (a.section || "").includes("money") || (a.section || "").includes("tax")).slice(0,4), [newestFirst]);

/* ---------- latest feed (4) ---------- */
  const latestFeed = useMemo(() => {
    const exclude = new Set([
      hero ? articleKey(hero) : null,
      ...topStories.map((s) => s.id),
    ]);

    return newestFirst
      .filter((a) => !exclude.has(articleKey(a)))
      .slice(0, 4)
      .map((a, i) => ({
        id: articleKey(a, `latest-${i}`),
        title: a?.title || "Untitled",
        image: a?.image || "",
        category: a?.category || "Local News",
        town: a?.location || "Cheshire",
        publishedDate: a?.publishedDate || "",
        url: `/article/${articleKey(a)}`,
        readTime: 3,
      }));
  }, [newestFirst, hero, topStories]);

  return (
    <HomepageLayout>
      <HomepageHeader breakingStories={[]} />

      {loading && <div className="py-6">Loading…</div>}
      {!loading && err && <div className="py-6 text-red-600">{err}</div>}

      {!loading && !err && hero && (
        <HeroStoryCard
          image={hero.image}
          category={hero.category || "Local News"}
          town={hero.location || "Cheshire"}
          headline={hero.title || "Untitled"}
          publishedTime={hero.publishedDate || ""}
          readTime={3}
          url={`/article/${articleKey(hero)}`}
        />
      )}

      {!loading && !err && topStories.length > 0 && (
        <TopStoriesGrid stories={topStories} />
      )}

      
      {!loading && !err && aiFeed.length > 0 && (
        <section className="mt-8">
          <h2 className="text-lg font-bold mb-3">AI & Tech</h2>
          <div className="space-y-3">
            {aiFeed.map((a, i) => (
              <CompactArticleCard
                key={a.id || a._id || i}
                onClick={() => navigate("/article/" + (a.id || a._id))}
                article={{
                  title: a.title,
                  content: a.summary || a.content || "",
                  summary: a.summary || "",
                  image: a.image,
                  category: a.category,
                  location: a.location || "Cheshire",
                  publishedDate: a.publishedDate,
                  readTime: 3,
                  url: "/article/" + (a.id || a._id),
                }}
              />
            ))}
          </div>
        </section>
      )}

      {!loading && !err && financeFeed.length > 0 && (
        <section className="mt-8">
          <h2 className="text-lg font-bold mb-3">Money & Finance</h2>
          <div className="space-y-3">
            {financeFeed.map((a, i) => (
              <CompactArticleCard
                key={a.id || a._id || i}
                onClick={() => navigate("/article/" + (a.id || a._id))}
                article={{
                  title: a.title,
                  content: a.summary || a.content || "",
                  summary: a.summary || "",
                  image: a.image,
                  category: a.category,
                  location: a.location || "Cheshire",
                  publishedDate: a.publishedDate,
                  readTime: 3,
                  url: "/article/" + (a.id || a._id),
                }}
              />
            ))}
          </div>
        </section>
      )}
{!loading && !err && latestFeed.length > 0 && (
        <section className="mt-6">
          <h2 className="text-lg font-bold mb-3">Latest</h2>
          <div className="space-y-3">
            {latestFeed.map((a, idx) => (
              <CompactArticleCard
                key={a?.id || a?._id || idx}
                onClick={() =>
                  navigate(a.url || ("/article/" + (a.id || a._id || "")))
                }
                article={{
                  title: a.title,
                  content: a.summary || a.content || "",
                  summary: a.summary || "",
                  image: a.image,
                  category: a.category,
                  location: a.town || a.location || "Cheshire",
                  publishedDate: a.publishedDate,
                  readTime: a.readTime || 3,
                  url: a.url || ("/article/" + (a.id || a._id || "")),
                }}
              />
            ))}
        
          </div>
        </section>
      )}

      <NewsFooter />
    </HomepageLayout>
  );
}
