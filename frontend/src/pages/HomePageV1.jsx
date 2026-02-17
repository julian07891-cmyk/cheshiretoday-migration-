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

function articleKey(a) {
  const id = a?.id || a?._id;
  if (id) return String(id);

  const url = a?.source_url || a?.sourceUrl || a?.url;
  if (url) return String(url);

  const title = a?.title || "";
  const date = a?.publishedDate || "";
  const combo = (title + "__" + date).trim();
  return combo !== "__" ? combo : null;
}

function isLocal(a) {
  const cat = (a?.category || "").toLowerCase();
  const scope = (a?.scope || "").toLowerCase();
  return cat.includes("local") || scope.includes("cheshire");
}

function isAiTechScience(a) {
  const cat = String(a?.category || "").toLowerCase();
  const sec = String(a?.section || "").toLowerCase();
  // backend: category may be AI/Tech/Science, and ai feed uses section ai-*
  if (sec.startsWith("ai-")) return true;
  if (cat.includes("ai") || cat.includes("tech") || cat.includes("science")) return true;
  // fallback keyword match
  const t = (String(a?.title || "") + " " + String(a?.summary || "") + " " + String(a?.content || "")).toLowerCase();
  return /\b(ai|artificial intelligence|chatgpt|openai|gemini|llm|model|chip|gpu|nvidia|amd|intel|cyber|security|hack|breach|data|cloud|saas|robot)\b/.test(t);
}

function isAiTechFeatured(a) {
  // optionally allow manual pinning via featured=true, but still prefer AI/Tech/Science first
  return isAiTechScience(a) || Boolean(a?.featured);
}


function isFeatured(a) {
  return Boolean(a?.featured);
}

function toCard(a, fallbackId, overrides = {}) {
  const id = articleKey(a) || fallbackId;
  return {
    id,
    title: a?.title || "Untitled",
    image: a?.image || "",
    category: a?.category || "Local News",
    town: a?.location || "Cheshire",
    publishedDate: a?.publishedDate || "",
    url: `/article/${articleKey(a)}`,
    readTime: 3,
    ...overrides,
  };
}

function escapeRegExp(s) {
  return String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/* ---------- page ---------- */
export default function HomePageV1() {
  const [articles, setArticles] = useState([]);
  const [guides, setGuides] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const navigate = useNavigate();

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        setLoading(true);
        setErr("");

        const res = await fetch(getApiUrl() + "/api/articles?limit=300");
        if (!res.ok) throw new Error(`API ${res.status}`);

        const data = await res.json();
        const list = Array.isArray(data) ? data : data?.articles || [];
        if (mounted) setArticles(list);

        // Load AI Guides (authority pages) — separate fetch so homepage still works if it fails
        try {
          const gRes = await fetch(getApiUrl() + "/api/authority-pages");
          if (gRes.ok) {
            const gData = await gRes.json();
            const pages = Array.isArray(gData?.pages) ? gData.pages : [];
            if (mounted) setGuides(pages);
          }
        } catch (_) {
          // ignore
        }

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

  /* ---------- ALL homepage slots with shared dedupe ---------- */
  const home = useMemo(() => {
    const used = new Set();

    const mark = (a) => {
      const k = articleKey(a);
      if (!k) return false;
      if (used.has(k)) return false;
      used.add(k);
      return true;
    };

    // 1) Hero
    const heroArticle = newestFirst.find(a => String(a?.category || "").toLowerCase().includes("uk")) || newestFirst.find(isLocal) || newestFirst[0] || null;
    if (heroArticle) mark(heroArticle);

    // 2) Top Stories (4) — local-first featured, excluding hero and any dupes
    const topStoriesCards = [];

    const pushTop = (a) => {
      if (topStoriesCards.length >= 4) return;
      if (!mark(a)) return;
      topStoriesCards.push(toCard(a, `top-${topStoriesCards.length}`));
    };

    // Pass 1: AI/Tech/Science first
    for (const a of newestFirst) {
      if (topStoriesCards.length >= 4) break;
      if (!isAiTechFeatured(a)) continue;
      pushTop(a);
    }

    // Pass 2: Local next
    for (const a of newestFirst) {
      if (topStoriesCards.length >= 4) break;
      const sec = String(a?.section || "").toLowerCase();
      if (!sec.startsWith("ai-")) continue;
      pushTop(a);
    }

    // Pass 3: Fill remaining slots with anything
    for (const a of newestFirst) {
      if (topStoriesCards.length >= 4) break;
      pushTop(a);
    }


    // 3) Most Read (5) — use view_count when present, exclude used
    const mostReadCards = [];

    const byViewsThenNewest = [...newestFirst].sort((a, b) => {
      const av = Number(a?.view_count || a?.views || 0);
      const bv = Number(b?.view_count || b?.views || 0);
      if (bv !== av) return bv - av;
      return safeDateMs(b?.publishedDate) - safeDateMs(a?.publishedDate);
    });

    for (const a of byViewsThenNewest) {
      if (mostReadCards.length >= 5) break;
      if (!mark(a)) continue;
      mostReadCards.push(toCard(a, `most-${mostReadCards.length}`));
    }

// 3) AI feed (4) — exclude used (backend section is source of truth)
    const aiArticles = [];
    for (const a of newestFirst) {
      if (aiArticles.length >= 4) break;
      const sec = String(a?.section || "").toLowerCase();
      if (!sec.startsWith("ai-")) continue;
      if (!mark(a)) continue;
      aiArticles.push(a);
    }

// 4) Finance feed — structured (4 business, 1 local, 1 business latest)
    const financeArticles = [];

    const isBusiness = (a) =>
      String(a?.section || "").toLowerCase() === "business-news";

    const isMoney = (a) =>
      ["money", "tax", "property", "mortgages"].includes(
        String(a?.section || "").toLowerCase()
      );

    // Pass 1: 4 business-news
    for (const a of newestFirst) {
      if (financeArticles.length >= 4) break;
      if (!isBusiness(a)) continue;
      if (!mark(a)) continue;
      financeArticles.push(a);
    }

    // Pass 2: 1 local news (to keep the sidebar grounded in Cheshire)
    for (const a of newestFirst) {
      if (financeArticles.length >= 5) break;

      const sec = String(a?.section || "").toLowerCase();
      // Avoid pulling AI items into Business & Money
      if (sec.startsWith("ai-")) continue;

      if (!isLocal(a)) continue;
      if (!mark(a)) continue;
      financeArticles.push(a);
    }

    // Pass 3: 1 more latest business
    for (const a of newestFirst) {
      if (financeArticles.length >= 6) break;
      if (!isBusiness(a)) continue;
      if (!mark(a)) continue;
      financeArticles.push(a);
    }

// 5) Latest feed (12) — local-first, exclude used
    const latestCards = [];

    const pushLatest = (a) => {
      if (latestCards.length >= 12) return;
      if (!mark(a)) return;
      latestCards.push(toCard(a, `latest-${latestCards.length}`));
    };

    // Pass 1: Prefer AI/Tech/Science for the first 8 slots
    for (const a of newestFirst) {
      if (latestCards.length >= 8) break;
      if (!isAiTechScience(a)) continue;
      pushLatest(a);
    }

    // Pass 2: Add Local (non-ai) for the next 4 slots
    for (const a of newestFirst) {
      if (latestCards.length >= 12) break;
      const sec = String(a?.section || "").toLowerCase();
      if (sec.startsWith("ai-")) continue;
      if (!isLocal(a)) continue;
      pushLatest(a);
    }

    // Pass 3: Fill remaining with anything else
    for (const a of newestFirst) {
      if (latestCards.length >= 12) break;
      pushLatest(a);
    }

return {
      hero: heroArticle,
      topStories: topStoriesCards,
      mostReadFeed: mostReadCards,
      aiFeed: aiArticles,
      financeFeed: financeArticles,
      latestFeed: latestCards,
    };
  }, [newestFirst]);

  const hero = home.hero;
  const topStories = home.topStories;
  const aiFeed = home.aiFeed;
  const financeFeed = home.financeFeed;
  const latestFeed = home.latestFeed;

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
          url={`/article/${articleKey(hero) || "hero"}`}
        />
      )}
      {!loading && !err && topStories.length > 0 && (
        <TopStoriesGrid stories={topStories} />
      )}

      {/* --- Main content: 2-column news layout --- */}
      {!loading && !err && (
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left: Latest feed */}
          <main className="lg:col-span-8">
            {latestFeed.length > 0 && (
              <section>
                <h2 className="text-lg font-bold mb-3">Latest</h2>
                <div className="space-y-3">
                  {latestFeed.map((a, idx) => (
                    <div key={a?.id || a?._id || idx}>
<CompactArticleCard
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


                      {idx === 2 && (
                        <div className="rounded-lg border border-gray-200 dark:border-gray-800 p-4 bg-gray-50 dark:bg-gray-900">
                          <div className="flex items-center justify-between mb-2">
                            <div className="text-sm font-semibold">Sponsored</div>
                            <span className="text-xs px-2 py-1 rounded bg-gray-200 dark:bg-gray-800">Ad</span>
                          </div>
                          <div className="text-sm mb-2">Grow your business with Cheshire Today readers.</div>
                          <a
                            href="/advertise"
                            className="text-sm font-semibold text-blue-600 hover:underline"
                          >
                            View advertising options →
                          </a>
                        </div>
                      )}

</div>
))}
</div>
              </section>
            )}
          </main>

          {/* Right: Sidebar widgets */}
          <aside className="lg:col-span-4 space-y-8">
            {/* Business & Money */}
            {financeFeed.length > 0 && (
              <>
                <section className="rounded-lg border border-gray-200 dark:border-gray-800 p-4">
                  <h2 className="text-lg font-bold mb-3">Business & Money</h2>
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

                <section className="rounded-lg border border-gray-200 dark:border-gray-800 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h2 className="text-lg font-bold">Money Toolkit</h2>
                    <span className="text-xs px-2 py-1 rounded bg-gray-200 dark:bg-gray-800">
                      Affiliate
                    </span>
                  </div>
                  <ul className="space-y-2 text-sm">
                    <li>
                      <a href="/money/best-savings-accounts" className="text-blue-600 hover:underline">
                        • Best savings accounts →
                      </a>
                    </li>
                    <li>
                      <a href="/money/best-mortgage-rates" className="text-blue-600 hover:underline">
                        • Compare mortgage rates →
                      </a>
                    </li>
                    <li>
                      <a href="/money/council-tax-bands-cheshire" className="text-blue-600 hover:underline">
                        • Cheshire council tax guide →
                      </a>
                    </li>
                  </ul>
                  <div className="text-xs mt-3 text-gray-500">
                    We may earn a commission if you use affiliate links.
                  </div>
                </section>
              </>
            )}

            {/* AI & Tech (only when backend classifies ai-*) */}
            {aiFeed.length > 0 && (
              <section className="rounded-lg border border-gray-200 dark:border-gray-800 p-4">
                <h2 className="text-lg font-bold mb-3">AI & Tech</h2>
                  {guides?.length > 0 && (
                    <div className="mb-4 p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
                      <div className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
                        AI Guides
                      </div>

                      <ul className="space-y-2 text-sm">
                        {guides.slice(0, 3).map((g, idx) => (
                          <li key={g?.id || g?.slug || idx}>
                            <a
                              href={`/guides/${encodeURIComponent(g.slug)}`}
                              className="font-semibold text-blue-700 dark:text-blue-300 hover:underline"
                            >
                              🔥 {g.title || g.slug}
                            </a>
                          </li>
                        ))}
                      </ul>

                      <div className="text-xs mt-2 text-gray-600 dark:text-gray-400">
                        UK-focused comparisons & best picks →
                      </div>
                    </div>
                  )}
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

            {/* Sponsored placeholder */}
            <section className="rounded-lg border border-dashed border-gray-300 dark:border-gray-700 p-4 text-sm text-gray-600 dark:text-gray-300">
              <div className="font-semibold mb-1">Sponsored</div>
              <div>Ad slot / affiliate widget placeholder (monetisation phase).</div>
              <a href="/advertise" className="inline-block mt-2 text-blue-600 hover:underline font-semibold">
                Advertise with us →
              </a>
            </section>
          </aside>
        </div>
      )}

      <NewsFooter />
</HomepageLayout>
  );
}
