import React, { useEffect, useMemo, useState } from "react";
import HomepageLayout from "../components/homepage/HomepageLayout";
import HomepageHeader from "../components/homepage/HomepageHeader";
import HeroStoryCard from "../components/homepage/HeroStoryCard";
import TopStoriesGrid from "../components/homepage/TopStoriesGrid";
import LatestFeed from "../components/homepage/LatestFeed";
import NewsFooter from "../components/NewsFooter";

export default function HomePageV1() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        setLoading(true);
        setErr("");

        const res = await fetch("/api/articles?limit=20");
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

  const hero = articles?.[0] || null;

  const topStories = useMemo(() => {
    return (articles || []).slice(1, 5).map((a, idx) => ({
      id: a?.id || a?._id || `top-${idx}`,
      title: a?.title || "Untitled",
      image: a?.image || "",
      category: a?.category || "Local News",
      town: a?.location || "Cheshire",
      url: "/article/" + (a?.id || a?._id || `top-${idx}`),
      publishedDate: a?.publishedDate,
      readTime: 3,
    }));
  }, [articles]);

  const latest = useMemo(() => {
    return (articles || []).slice(5, 9).map((a, idx) => ({
      id: a?.id || a?._id || `latest-${idx}`,
      title: a?.title || "Untitled",
      summary: a?.summary || "",
      image: a?.image || "",
      category: a?.category || "Local News",
      town: a?.location || "Cheshire",
      url: "/article/" + (a?.id || a?._id || `latest-${idx}`),
      publishedDate: a?.publishedDate,
      readTime: 3,
    }));
  }, [articles]);

  return (
    <HomepageLayout>
      <HomepageHeader breakingStories={[]} />

      {loading && (
        <div className="py-6 text-gray-600 dark:text-gray-300">
          Loading homepage…
        </div>
      )}

      {!loading && err && (
        <div className="py-6 text-red-600">Failed to load articles: {err}</div>
      )}

      {!loading && !err && hero && (
        <>
          {/* HERO */}
          <HeroStoryCard
            image={hero.image}
            category={hero.category || "Local News"}
            town={hero.location || "Cheshire"}
            headline={hero.title || "Untitled"}
            publishedTime={hero.publishedDate || ""}
            readTime={3}
            url={"/article/" + (hero.id || hero._id || "preview")}
          />

          {/* TOP STORIES (4) */}
          <TopStoriesGrid stories={topStories} />

          {/* LATEST FEED (4) */}
          <LatestFeed stories={latest} />

          {/* FOOTER */}
          <NewsFooter />
        </>
      )}
    </HomepageLayout>
  );
}
