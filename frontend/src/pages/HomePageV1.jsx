import React, { useEffect, useMemo, useState } from "react";
import { getApiUrl } from "../utils/api";
import { useNavigate } from "react-router-dom";
import HomepageLayout from "../components/homepage/HomepageLayout";
import HomepageHeader from "../components/homepage/HomepageHeader";
import CompactArticleCard from "../components/CompactArticleCard";
import HeroStoryCard from "../components/homepage/HeroStoryCard";
import TopRatedGuides from "../components/TopRatedGuides";
import TopStoriesGrid from "../components/homepage/TopStoriesGrid";
import LeadSection from "../components/homepage/LeadSection";
import SidebarBestPicks from "../components/SidebarBestPicks";
import NewsFooter from "../components/NewsFooter";
import { filterEditorialPool } from "../utils/editorialPolicy";

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
  return /\b(ai|artificial intelligence|chatgpt|openai|gemini|llm|gpt-?\d*|prompt|machine\s*learning|deep\s*learning|neural|chip|gpu|nvidia|amd|intel|semiconductor|cybersecurity|ransomware|malware|phishing|hack(?:ed|ing)?|data\s*breach|breach|cloud\s*comput(?:ing|e)|saas|robot|automation)\b/.test(t);
}

function isAiTechFeatured(a) {
  // optionally allow manual pinning via featured=true, but still prefer AI/Tech/Science first
  return isAiTechScience(a) || Boolean(a?.featured);
}


function isFeatured(a) {
  return Boolean(a?.featured);
}


/* ---------- editorial policy ---------- */
// Goal: de-emphasize pure crime/sensational local aggregation.
// Keep major public-interest incidents (weather, road/rail disruption, emergencies) when relevant.

function isPublicInterestException(a) {
  const t = (String(a?.title || "") + " " + String(a?.summary || "") + " " + String(a?.content || "")).toLowerCase();

  // Disruption / safety / essential service impact
  if (/\b(road|a\d{2,4}|m\d|motorway|rail|train|bus|bridge|closure|closed|shut|blocked|diversion|traffic|crash|collision|accident|delays?)\b/.test(t)) return true;
  if (/\b(storm|flood|flooding|severe\s+weather|met\s+office|warning|amber\s+warning|red\s+warning|power\s+cut|outage)\b/.test(t)) return true;
  if (/\b(missing\s+person|appeal\s+for\s+information|public\s+appeal)\b/.test(t)) return true;

  return false;
}

function isCrimeSensational(a) {
  const cat = String(a?.category || "").toLowerCase();
  const sec = String(a?.section || "").toLowerCase();
  const t = (String(a?.title || "") + " " + String(a?.summary || "") + " " + String(a?.content || "")).toLowerCase();

  // Category/section hints
  if (/(crime|police|court|incident)/.test(cat)) return true;
  if (/(crime|police|court)/.test(sec)) return true;

  // Content hints (sensational / violent crime / courts)
  if (/\b(stab(bed|bing)?|murder(ed)?|killed|fatal|death|rape(d)?|sex\s+offen[cs]e|assault|rob(bery|bed)|burglar(y|ies)|arson|drug\s+raid|charged|sentenced|jailed|court|magistrates|crown\s+court|trial)\b/.test(t)) return true;

  return false;
}

function isAllowedByPolicy(a) {
  if (!a) return false;
  // Block pure crime/sensational unless it’s a clear public-interest exception
  if (isCrimeSensational(a) && !isPublicInterestException(a)) return false;
  return true;
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

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error) {
    return { error };
  }
  componentDidCatch(error, info) {
    // keep a console trail too
    console.error("HomePageV1 crashed:", error, info);
  }
  render() {
    if (this.state.error) {
      return (
        <div className="p-6 rounded-xl border border-red-200 bg-red-50 text-red-900">
          <div className="font-extrabold mb-2">Homepage crashed (ErrorBoundary)</div>
          <pre className="text-xs whitespace-pre-wrap leading-relaxed">
            {String(this.state.error?.stack || this.state.error)}
          </pre>
        </div>
      );
    }
    return this.props.children;
  }
}


export default function HomePageV1() {
  const [articles, setArticles] = useState([]);
  const [guides, setGuides] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  
  const [showMoreStories, setShowMoreStories] = useState(false);
  const [showLatest, setShowLatest] = useState(false);
  const [showAiBiz, setShowAiBiz] = useState(false);
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

        // Load published guides (authority pages) for sidebar modules
        try {
          const gRes = await fetch(getApiUrl() + "/api/authority-pages?limit=10&status=published");
          if (gRes.ok) {
            const gData = await gRes.json();
            if (mounted) setGuides(Array.isArray(gData) ? gData : []);
          }
        } catch (e) {
          // Non-fatal: guides module can be empty if API unavailable
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

    // Editorial policy pool (filters out pure crime/sensational unless public-interest)
    const pool = (Array.isArray(newestFirst) ? newestFirst : []).filter(isAllowedByPolicy);
    const editorialPool = filterEditorialPool(Array.isArray(newestFirst) ? newestFirst : []);
    const poolAll = editorialPool.length ? editorialPool : (Array.isArray(newestFirst) ? newestFirst : []);

    const mark = (a) => {
      const k = articleKey(a);
      if (!k) return false;
      if (used.has(k)) return false;
      used.add(k);
      return true;
    };

    // 1) Hero
    const heroArticle = poolAll.find(isLocal) || poolAll.find(a => String(a?.category || "").toLowerCase().includes("business")) || poolAll.find(isAiTechScience) || poolAll.find(a => String(a?.category || "").toLowerCase().includes("uk")) || poolAll[0] || null;
    if (heroArticle) mark(heroArticle);

    // 2) Top Stories (7) — fixed mix: 2 Local, 2 Business, 1 AI, 1 Property, 1 Flexible
    // 2) Top Stories (7) — fixed mix: 2 Local, 2 Business, 1 Tech/Science, 1 Property, 1 Flexible (dedupe-safe)
    const topStoriesCards = [];

    // Top Stories (7) — fixed mix:
    // 2 Local + 2 Business + 1 AI/Tech + 1 Property + 1 UK (dedupe-safe)
    const isBusinessishTop = (a) => {
      const cat = String(a?.category || "").toLowerCase();
      if (cat.includes("business") || cat.includes("finance") || cat.includes("money") || cat.includes("tax")) return true;
      const t = (String(a?.title || "") + " " + String(a?.summary || "") + " " + String(a?.content || "")).toLowerCase();
      return /\b(business|economy|economic|markets?|inflation|gdp|trade|tariff|company|companies|earnings|profits?|shares?|stocks?|ftse|investment|investor|fund|bank|banking|hmrc|tax|vat|interest\s*rate|rate\s*cut|rate\s*hike|mortgage|mortgages|remortgage|savings|isa|credit\s*card)\b/.test(t);
    };

    const isPropertyishTop = (a) => {
      const cat = String(a?.category || "").toLowerCase();
      if (cat.includes("property") || cat.includes("housing") || cat.includes("planning")) return true;

      const t = (String(a?.title || "") + " " + String(a?.summary || "") + " " + String(a?.content || "")).toLowerCase();

      // STRICT property/planning focus only (prevents macro Business being mislabeled as Property)
      return /\b(planning\s*application|application\s*submitted|plans?\s*submitted|planning\s*permission|approved|refused|housing\s*development|residential\s*development|residential\s*scheme|new\s*homes?|green\s*belt|development\s*site)\b/.test(t);
    };

    const isUkishTop = (a) => {
      const cat = String(a?.category || "").toLowerCase();
      const scope = String(a?.scope || "").toLowerCase();
      return cat.includes("uk") || scope === "uk";
    };

    const counts = { local: 0, business: 0, tech: 0, property: 0, uk: 0 };

    const pushTop = (a, overrideCategory = null) => {
      if (topStoriesCards.length >= 7) return;
      if (!mark(a)) return;
      topStoriesCards.push(
        toCard(
          a,
          `top-${topStoriesCards.length}`,
          overrideCategory ? { category: overrideCategory } : {}
        )
      );
    };

    // Pass 1: Local (2) — exclude Tech/Business/Property so those slots remain available
    for (const a of poolAll) {
      if (counts.local >= 2) break;
      if (!isLocal(a)) continue;
      if (isAiTechScience(a)) continue;
      if (isBusinessishTop(a)) continue;
      if (isPropertyishTop(a)) continue;
      pushTop(a, "Local News");
      counts.local += 1;
    }

    // Pass 2: Business (2) — exclude Tech/Property
    for (const a of poolAll) {
      if (counts.business >= 2) break;
      if (isAiTechScience(a)) continue;
      if (isPropertyishTop(a)) continue;
      if (!isBusinessishTop(a)) continue;
      pushTop(a, "Business");
      counts.business += 1;
    }

    // Pass 3: AI/Tech (1)
    for (const a of poolAll) {
      if (counts.tech >= 1) break;
      if (!isAiTechScience(a)) continue;
      pushTop(a, "AI & Tech");
      counts.tech += 1;
    }

    // Pass 4: Property (1) — ensure it is actually property-ish
    for (const a of poolAll) {
      if (counts.property >= 1) break;
      if (isAiTechScience(a)) continue;
      if (!isPropertyishTop(a)) continue;
      pushTop(a, "Property");
      counts.property += 1;
    }

    // Pass 5: UK News (1) — explicitly UK, exclude Local/Business/Property/Tech
    for (const a of poolAll) {
      if (counts.uk >= 1) break;
      if (isAiTechScience(a)) continue;
      if (!isUkishTop(a)) continue;
      if (isLocal(a)) continue;
      if (isBusinessishTop(a)) continue;
      if (isPropertyishTop(a)) continue;
      pushTop(a, "UK News");
      counts.uk += 1;
    }

    // Safety fill: if we still have <7 (rare), fill with newest non-tech
    for (const a of poolAll) {
      if (topStoriesCards.length >= 7) break;
      if (isAiTechScience(a)) continue;
      pushTop(a);
    }

// 3) Most Read (5) — use view_count when present, exclude used
    const mostReadCards = [];

    const byViewsThenNewest = [...poolAll].sort((a, b) => {
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
    for (const a of poolAll) {
      if (aiArticles.length >= 4) break;
      if (!isAiTechScience(a)) continue;
      if (!mark(a)) continue;
      aiArticles.push(toCard(a, `ai-${aiArticles.length}`, { category: "AI & Tech" }));
    }


    // Fallback: if AI feed ends up empty, use newest 4 (still dedupe-safe)
    if (aiArticles.length === 0) {
      for (const a of poolAll) {
        if (aiArticles.length >= 4) break;
        if (!mark(a)) continue;
        aiArticles.push(a);
      }
    }

// 4) Finance feed — structured (4 business, 1 local, 1 business latest)
    const financeArticles = [];

        const isBusiness = (a) => {
      const cat = String(a?.category || "").toLowerCase();
      if (cat.includes("business") || cat.includes("finance") || cat.includes("money")) return true;
      const t = (String(a?.title || "") + " " + String(a?.summary || "") + " " + String(a?.content || "")).toLowerCase();
      return /\b(business|economy|economic|market|markets|inflation|gdp|trade|tariff|company|companies|earnings|profits?|shares?|stocks?|ftse|investment|investor|fund|bank|banking|hmrc|tax|vat|interest\s*rate|rate\s*cut|rate\s*hike|mortgage|mortgages|remortgage)\b/.test(t);
    };

const isMoney = (a) => {
      const sec = String(a?.section || "").toLowerCase();
      if (["money", "tax", "property", "mortgages"].includes(sec)) return true;

      const cat = String(a?.category || "").toLowerCase();
      if (cat.includes("money") || cat.includes("finance") || cat.includes("business") || cat.includes("property") || cat.includes("tax")) return true;

      const t = (String(a?.title || "") + " " + String(a?.summary || "") + " " + String(a?.content || "")).toLowerCase();
      return /\b(mortgage|mortgages|remortgage|fixed\s*rate|tracker|interest\s*rate|isa|savings|bank|credit\s*card|loan|debt|council\s*tax|stamp\s*duty|hmrc|tax|rebate|refund)\b/.test(t);
    };

    // Pass 1: Prefer Money-ish first (2), then Business (up to 4)
    for (const a of poolAll) {
      if (financeArticles.length >= 2) break;
      if (!isMoney(a)) continue;
      if (!mark(a)) continue;
      financeArticles.push(toCard(a, `fin-${financeArticles.length}`, { category: "Business & Money" }));
    }

    for (const a of poolAll) {
      if (financeArticles.length >= 4) break;
      if (!isBusiness(a)) continue;
      if (!mark(a)) continue;
      financeArticles.push(toCard(a, `fin-${financeArticles.length}`, { category: "Business & Money" }));
    }

// Pass 2: 1 local news// Pass 2: 1 local news (to keep the sidebar grounded in Cheshire)
    for (const a of poolAll) {
      if (financeArticles.length >= 5) break;

      const sec = String(a?.section || "").toLowerCase();
      // Avoid pulling AI items into Business & Money
      if (isAiTechScience(a)) continue;

      if (!isLocal(a)) continue;
      if (!mark(a)) continue;
      financeArticles.push(toCard(a, `fin-${financeArticles.length}`, { category: "Business & Money" }));
    }

    // Pass 3: 1 more latest business
    for (const a of poolAll) {
      if (financeArticles.length >= 6) break;
      if (!isBusiness(a)) continue;
      if (!mark(a)) continue;
      financeArticles.push(toCard(a, `fin-${financeArticles.length}`, { category: "Business & Money" }));
    }


    
    // Fallback: if Business & Money ends up empty, fill with newest 3 non-AI (still dedupe-safe)
    if (financeArticles.length === 0) {
      for (const a of poolAll) {
        if (financeArticles.length >= 3) break;
        if (isAiTechScience(a)) continue;
        if (!mark(a)) continue;
        financeArticles.push(toCard(a, `fin-${financeArticles.length}`, { category: "Business & Money" }));
      }
    }

// 4a) Business (3) — business-first, exclude AI and exclude used
    const businessFeed = [];
    for (const a of poolAll) {
      if (businessFeed.length >= 3) break;
      const sec = String(a?.section || "").toLowerCase();
      if (isAiTechScience(a)) continue;
      if (!isBusiness(a)) continue;
      if (!mark(a)) continue;
      businessFeed.push(a);
    }

    // 4b) Mortgages & Savings (3) — keyword + section based, exclude used
    const moneyFeed = [];

    const isMoneyish = (a) => {
      const sec = String(a?.section || "").toLowerCase();
      if (["money", "tax", "property", "mortgages"].includes(sec)) return true;
      const t = (String(a?.title || "") + " " + String(a?.summary || "")).toLowerCase();
      return /\b(mortgage|mortgages|rate|rates|isa|savings|save|interest|remortgage|fixed\s*rate|tracker|stamp\s*duty|council\s*tax)\b/.test(t);
    };

    for (const a of poolAll) {
      if (moneyFeed.length >= 3) break;
      const sec = String(a?.section || "").toLowerCase();
      if (isAiTechScience(a)) continue; // keep this block focused
      if (!isMoneyish(a)) continue;
      if (!mark(a)) continue;
      moneyFeed.push(a);
    }

    
    // Fallback: if Mortgages & Savings ends up empty, fill with newest 3 non-AI (still dedupe-safe)
    if (moneyFeed.length === 0) {
      for (const a of poolAll) {
        if (moneyFeed.length >= 3) break;
        if (isAiTechScience(a)) continue;
        if (!mark(a)) continue;
        moneyFeed.push(a);
      }
    }

// 4c) Property & Housing (3) — planning, homes, rent, property; exclude used
    const propertyFeed = [];

    const isPropertyish = (a) => {
      const sec = String(a?.section || "").toLowerCase();
      if (["property", "housing", "planning"].includes(sec)) return true;

      const t = (String(a?.title || "") + " " + String(a?.summary || "")).toLowerCase();
      return /\b(property|housing|planning|application|approved|refused|development|homes|apartments|estate|rent|rental|landlord|tenant|lease|build|green\s*belt)\b/.test(t);
    };

    for (const a of poolAll) {
      if (propertyFeed.length >= 3) break;
      const sec = String(a?.section || "").toLowerCase();
      if (isAiTechScience(a)) continue;
      // section is null in backend; no section-based exclude

      if (!isPropertyish(a)) continue;
      if (!mark(a)) continue;
      propertyFeed.push(a);
    }



    
    // (Removed) Property & Housing fallback fill: keep this block strictly property/housing.




// 5) Latest feed (12) — balanced mix for Cheshire Today strategy (dedupe-safe)
    // Target: 4 Local, 4 Business/Finance, 3 AI/Tech, 1 UK (newest-first within each bucket)
    const latestCards = [];

    const isUkishLatest = (a) => {
      const cat = String(a?.category || "").toLowerCase();
      const scope = String(a?.scope || "").toLowerCase();
      return cat.includes("uk") || scope === "uk";
    };

    const pushLatest = (a, overrideCategory = null) => {
      if (latestCards.length >= 12) return;
      if (!mark(a)) return;
      latestCards.push(toCard(a, `latest-${latestCards.length}`, overrideCategory ? { category: overrideCategory } : {}));
    };

    // Pass 1: Local (4) — keep it grounded in Cheshire
    for (const a of poolAll) {
      if (latestCards.length >= 4) break;
      if (!isLocal(a)) continue;
      if (isAiTechScience(a)) continue; // reserve AI/Tech quota for later
      pushLatest(a, "Local News");
    }

    // Pass 2: Business/Finance (4)
    for (const a of poolAll) {
      if (latestCards.length >= 8) break;
      if (isAiTechScience(a)) continue;
      if (!isBusiness(a) && !isMoney(a)) continue;
      pushLatest(a, "Business");
    }

    // Pass 3: AI/Tech (3)
    for (const a of poolAll) {
      if (latestCards.length >= 11) break;
      if (!isAiTechScience(a)) continue;
      pushLatest(a, "AI & Tech");
    }

    // Pass 4: UK (1) — only if we still have room
    for (const a of poolAll) {
      if (latestCards.length >= 12) break;
      if (!isUkishLatest(a)) continue;
      if (isLocal(a)) continue;
      pushLatest(a, "UK News");
    }

    // Safety fill: anything (rare) to reach 12
    for (const a of poolAll) {
      if (latestCards.length >= 12) break;
      pushLatest(a);
    }


// 5b) AI & Business feed (dedupe-safe, 36 max) — hybrid authority block, avoids duplicates via mark()
    const aiBizFeedCards = [];
    const isAiBiz = (a) => {
      // Prefer existing classifiers already defined in this builder scope
      if (isAiTechScience(a)) return true;
      if (isBusiness(a) || isMoney(a)) return true;

      // Property/housing/planning often overlaps with finance audience; include it here too
      // (isPropertyish is defined for propertyFeed in this builder scope)
      if (typeof isPropertyish === "function" && isPropertyish(a)) return true;

      // Lightweight keyword fallback (title + summary only)
      const t = (String(a?.title || "") + " " + String(a?.summary || "")).toLowerCase();
      return /\b(tax|hmrc|vat|budget|inflation|interest\s*rate|rates|mortgage|remortgage|savings|isa|credit\s*card|bank|housing|property|planning)\b/.test(t);
    };

    for (const a of poolAll) {
      if (aiBizFeedCards.length >= 36) break;
      if (!isAiBiz(a)) continue;
      if (!mark(a)) continue;
      aiBizFeedCards.push(toCard(a, `aibiz-${aiBizFeedCards.length}`, { category: a?.category || "AI & Business" }));
    }

// 6) More stories (dedupe-safe leftovers, 36 max)
      const moreStoriesCards = [];
      for (const a of poolAll) {
        if (moreStoriesCards.length >= 36) break;
        if (!mark(a)) continue;
        moreStoriesCards.push(toCard(a, `more-${moreStoriesCards.length}`));
      }



return {
      hero: heroArticle,
      topStories: topStoriesCards,
      mostReadFeed: mostReadCards,
      aiFeed: aiArticles,
      aiBizFeed: aiBizFeedCards,
      financeFeed: financeArticles,
      businessFeed: businessFeed,
      moneyFeed: moneyFeed,
      latestFeed: latestCards,
        moreStoriesFeed: moreStoriesCards,
            propertyFeed: propertyFeed,
};
  }, [newestFirst]);

  const hero = home?.hero || null;

  // Always default to arrays to prevent runtime crashes (blank page)
  const topStories = Array.isArray(home?.topStories) ? home.topStories : [];
  const aiFeed = Array.isArray(home?.aiFeed) ? home.aiFeed : [];
  const financeFeed = Array.isArray(home?.financeFeed) ? home.financeFeed : [];

  const businessFeed = Array.isArray(home?.businessFeed) ? home.businessFeed : [];
  const moneyFeed = Array.isArray(home?.moneyFeed) ? home.moneyFeed : [];
  const propertyFeed = Array.isArray(home?.propertyFeed) ? home.propertyFeed : [];

  const latestFeed = Array.isArray(home?.latestFeed) ? home.latestFeed : [];
  const moreStoriesFeed = Array.isArray(home?.moreStoriesFeed) ? home.moreStoriesFeed : [];

  const aiBizFeed = Array.isArray(home?.aiBizFeed) ? home.aiBizFeed : [];

  // AI & Business feed (filtered) — keep cards relevant and avoid dumping all articles here
  
return (
    <div data-build="HPV1_BUILD_20260222_A" className="min-h-screen bg-neutral-50 text-slate-900 dark:bg-gray-900 dark:text-white">
    <ErrorBoundary><HomepageLayout>
      <HomepageHeader breakingStories={[]} />

      {loading && <div className="py-6">Loading…</div>}
      {!loading && err && <div className="py-6 text-red-600">{err}</div>}

      {!loading && !err && (
        <section className="mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Left: Hero (dominant) */}
            <div className="lg:col-span-8">
              {hero && (
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

              <TopRatedGuides guides={guides} />

{/* Monetisation strip (hero) */}
              <div className="mt-4">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">

                  <a
                    href="/guides/best-mortgage-rates-uk"
                    className="group rounded-xl border border-slate-200/50 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4 hover:border-emerald-300 transition-colors"
                  >
                    <div className="text-[11px] font-semibold text-slate-500 dark:text-gray-400 mb-1">Affiliate</div>
                    <div className="text-sm font-extrabold text-slate-900 dark:text-white group-hover:underline underline-offset-2">Mortgage rates</div>
                    <div className="text-xs text-slate-600 dark:text-gray-400 mt-1"><span className="group-hover:underline underline-offset-2">Compare UK deals →</span></div>
                  </a>

                  <a
                    href="/guides/best-credit-cards-uk"
                    className="group rounded-xl border border-slate-200/50 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4 hover:border-emerald-300 transition-colors"
                  >
                    <div className="text-[11px] font-semibold text-slate-500 dark:text-gray-400 mb-1">Affiliate</div>
                    <div className="text-sm font-extrabold text-slate-900 dark:text-white group-hover:underline underline-offset-2">Compare credit cards</div>
                    <div className="text-xs text-slate-600 dark:text-gray-400 mt-1"><span className="group-hover:underline underline-offset-2">0% offers + rewards →</span></div>
                  </a>

                  <a
                    href="/guides/best-savings-accounts-uk"
                    className="group rounded-xl border border-slate-200/50 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4 hover:border-emerald-300 transition-colors"
                  >
                    <div className="text-[11px] font-semibold text-slate-500 dark:text-gray-400 mb-1">Affiliate</div>
                    <div className="text-sm font-extrabold text-slate-900 dark:text-white group-hover:underline underline-offset-2">Savings accounts</div>
                    <div className="text-xs text-slate-600 dark:text-gray-400 mt-1"><span className="group-hover:underline underline-offset-2">Best easy-access picks →</span></div>
                  </a>

                </div>

                <div className="mt-2 text-[11px] text-slate-500 dark:text-gray-400">
                  We may earn a commission from affiliate links.
                </div>
              </div>
            </div>

            {/* Right: Top Stories (compact) */}
            <aside className="lg:col-span-4 lg:-mt-10">
              {topStories.length > 0 && (
                <div className="rounded-xl border border-slate-200/50 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h2 className="text-base font-extrabold tracking-tight">Top stories</h2>
                    <span className="text-[11px] text-slate-500 dark:text-gray-400">Updated live</span>
                  </div>
                  <TopStoriesGrid stories={topStories} />
                </div>
              )}
            </aside>
          </div>
        </section>
      )}

      {/* --- Main content: 2-column news layout --- */}
      {!loading && !err && (
        <div className="-mt-4 grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left: Latest feed */}
          
          <main className="lg:col-span-8 lg:-mt-4">

            {/* Latest */}
            {Array.isArray(latestFeed) && latestFeed.length > 0 && (
              <section className="rounded-xl border border-slate-200/60 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-base font-extrabold tracking-tight">Latest</h2>
                  </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {(showLatest ? latestFeed.slice(0, 36) : latestFeed.slice(0, 18)).map((a, idx) => (
                    <div key={a?.id || a?._id || idx}>
                      <CompactArticleCard
                        onClick={() => navigate(a.url || ("/article/" + (a.id || a._id || "")))}
                        article={a}
                      />
                    </div>
                  ))}
                </div>
              

                <div className="mt-3 flex justify-end">
                  <button
                    type="button"
                    onClick={() => setShowLatest(v => !v)}
                    className="text-sm font-semibold hover:underline underline-offset-2"
                  >
                    {showLatest ? "Show less" : "Show more"}
                  </button>
                </div>
</section>
            )}

            {/* Property & Tax Intelligence */}
            <section className="mt-6 rounded-xl border border-slate-200/60 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-base font-extrabold tracking-tight">Property & Tax Intelligence</h2>
                <span className="text-[11px] px-2 py-1 rounded bg-slate-100 dark:bg-gray-800 text-slate-600 dark:text-gray-300">
                  Affiliate
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <a href="/guides/cost-of-buying-home-cheshire-2026" className="group rounded-xl border border-slate-200/50 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4 hover:border-emerald-300 transition-colors">
                  <div className="text-sm font-extrabold">Cost of buying in Cheshire</div>
                </a>

                <a href="/guides/best-savings-accounts-uk" className="group rounded-xl border border-slate-200/50 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4 hover:border-emerald-300 transition-colors">
                  <div className="text-sm font-extrabold">Best savings accounts</div>
                </a>
                <a href="/guides/best-mortgage-rates-uk" className="group rounded-xl border border-slate-200/50 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4 hover:border-emerald-300 transition-colors">
                  <div className="text-sm font-extrabold">Compare mortgage rates</div>
                </a>
                <a href="/guides/council-tax-bands-cheshire" className="group rounded-xl border border-slate-200/50 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4 hover:border-emerald-300 transition-colors">
                  <div className="text-sm font-extrabold">Council tax guide</div>
                </a>
              </div>
            </section>

            {/* AI & Business */}
            {Array.isArray(aiBizFeed) && aiBizFeed.length > 0 && (
              <section className="mt-6 rounded-xl border border-slate-200/60 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-base font-extrabold tracking-tight">AI & Business</h2>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {(showAiBiz ? aiBizFeed.slice(0, 36) : aiBizFeed.slice(0, 18)).map((a, i) => (
                    <div key={a?.id || a?._id || i}>
                      <CompactArticleCard
                        onClick={() => navigate(a.url || ("/article/" + (a.id || a._id || "")))}
                        article={a}

{/* AI & Business */}
            {Array.isArray(aiBizFeed) && aiBizFeed.length > 0 && (
              <section className="mt-6 rounded-xl border border-slate-200/60 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-base font-extrabold tracking-tight">AI & Business</h2>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {(showAiBiz ? aiBizFeed.slice(0, 36) : aiBizFeed.slice(0, 18)).map((a, i) => (
                    <div key={a?.id || a?._id || i}>
                      <CompactArticleCard
                        onClick={() => navigate(a.url || ("/article/" + (a.id || a._id || "")))}
                        article={a}
                      />
                    </div>
                  ))}
                </div>
                <div className="mt-3 flex justify-center">
                  <button
                    type="button"
                    onClick={() => setShowAiBiz(v => !v)}
                    className="text-sm font-semibold hover:underline underline-offset-2"
                  >
                    {showAiBiz ? "Show less" : "Show more"}
                  </button>
                </div>
              </section>
            )}

            {/* More stories */}
            {Array.isArray(moreStoriesFeed) && moreStoriesFeed.length > 0 && (
              <section className="mt-6 rounded-xl border border-slate-200/60 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-base font-extrabold tracking-tight">More stories</h2>
                  </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {(showMoreStories ? moreStoriesFeed.slice(0, 36) : moreStoriesFeed.slice(0, 18)).map((a, i) => (
                    <div key={a?.id || a?._id || i}>
                      <CompactArticleCard
                        onClick={() => navigate(a.url || ("/article/" + (a.id || a._id || "")))}
                        article={a}
                      />
                    </div>
                  ))}
                </div>
              

                <div className="mt-3 flex justify-end">
                  <button
                    type="button"
                    onClick={() => setShowMoreStories(v => !v)}
                    className="text-sm font-semibold hover:underline underline-offset-2"
                  >
                    {showMoreStories ? "Show less" : "Show more"}
                  </button>
                </div>
</section>
            )}

          </main>


          {/* Right: Sidebar widgets */}
          <aside className="lg:col-span-4 space-y-3">

            {/* Business & Money */}
            
            {Array.isArray(financeFeed) && financeFeed.length > 0 && (
              <LeadSection
                title="Business & Money"
                badgeText="Business"
                items={financeFeed.slice(0, 4)}
                onNavigate={(url) => navigate(url)}
              />
            )}
            {/* AI & Tech */}
            
            {(aiFeed.length > 0 || (Array.isArray(guides) && guides.length > 0)) && (
              <div className="space-y-3">
                {Array.isArray(guides) && guides.length > 0 && (
                  <div className="rounded-xl border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20 p-4">
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-extrabold text-slate-900 dark:text-white">Guides</div>
                      <a
                        href="/guides"
                        className="text-sm font-semibold text-slate-700 dark:text-slate-200 hover:underline underline-offset-2"
                      >
                        View guides →
                      </a>
                    </div>

                    <ul className="mt-3 space-y-2 text-sm">
                      {guides.slice(0, 3).map((g, idx) => (
                        <li key={g?.id || g?.slug || idx}>
                          <a
                            href={`/guides/${encodeURIComponent(g.slug)}`}
                            className="font-semibold text-blue-700 dark:text-blue-300 hover:underline underline-offset-2"
                          >
                            🔥 {g.title || g.slug}
                          </a>
                        </li>
                      ))}
                    </ul>

                    <div className="text-xs mt-3 text-slate-600 dark:text-gray-300">
                      UK-focused comparisons &amp; best picks →
                    </div>
                  </div>
                )}

                <LeadSection
                  title="AI & Tech"
                  badgeText="AI Pulse"
                  badgeClassName="text-[10px] uppercase tracking-wide font-semibold px-2 py-1 rounded-full border border-indigo-200 bg-indigo-50 text-indigo-700 dark:border-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-200"
                  items={aiFeed.slice(0, 4)}
                  onNavigate={(url) => navigate(url)}
                />
              </div>
            )}
            {/* Mortgages & Savings */}
            
            {Array.isArray(moneyFeed) && moneyFeed.length > 0 && (
              <LeadSection
                title="Mortgages & Savings"
                badgeText="Finance"
                items={moneyFeed.slice(0, 4)}
                onNavigate={(url) => navigate(url)}
              />
            )}

            {/* Property & Housing */}
            
            {Array.isArray(propertyFeed) && propertyFeed.length > 0 && (
              <LeadSection
                title="Property & Housing"
                badgeText="Property"
                badgeClassName="text-[10px] uppercase tracking-wide font-semibold px-2 py-1 rounded-full border border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-900/30 dark:text-amber-200"
                items={propertyFeed.slice(0, 4)}
                onNavigate={(url) => navigate(url)}
              />
            )}

            <SidebarBestPicks guides={guides} />

            {/* Sponsored placeholder */}
            <section className="rounded-xl border border-dashed border-slate-300 dark:border-gray-700 bg-white/50 dark:bg-transparent p-3 text-sm text-slate-600 dark:text-gray-300">
              <div className="flex items-center justify-between mb-2">
                <div className="font-semibold text-slate-900 dark:text-white">Sponsored</div>
                <span className="text-[10px] uppercase tracking-wide font-semibold px-2 py-1 rounded-full border border-slate-200 bg-slate-100 text-slate-700 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200">
                  Ad
                </span>
              </div>
              <div>Ad slot / affiliate widget placeholder (monetisation phase).</div>
              <a
                href="/advertise"
                className="inline-block mt-2 text-slate-800 dark:text-slate-100 hover:underline underline-offset-2 font-semibold"
              >
                Advertise with us →
              </a>
            </section>

          </aside>
        </div>
      )}

      <NewsFooter />
</HomepageLayout></ErrorBoundary>
    </div>

  );
}
