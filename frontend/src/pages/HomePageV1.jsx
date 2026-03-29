const MONETISATION_ENABLED = false;
import React, { useEffect, useMemo, useState } from "react";
import { getApiUrl } from "../utils/api";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import HomepageLayout from "../components/homepage/HomepageLayout";
import HomepageHeader from "../components/homepage/HomepageHeader";
import CompactArticleCard from "../components/CompactArticleCard";
import { AffiliateWidgetSidebar } from "../components/AffiliateWidgets";
import HeroStoryCard from "../components/homepage/HeroStoryCard";
import TopStoriesGrid from "../components/homepage/TopStoriesGrid";
import TextHeadlineStrip from "../components/homepage/TextHeadlineStrip";
import HeroMonetisationStrip from "../components/homepage/HeroMonetisationStrip";
import LeadSection from "../components/homepage/LeadSection";
import NewsFooter from "../components/NewsFooter";
import SubscribeSection from "../components/SubscribeSection";
import { SubscribeInlineBanner } from "../components/JobsWidget";
import { filterEditorialPool, isLocalPillar, isAiTechPillar, isBusinessPillar, isFinancePillar, isUkPillar, getPrimaryPillar, getDisplayCategoryForPillar } from "../utils/editorialPolicy";
import { buildArticleUrl } from "../utils/articleUrl";

import { FEATURES } from "../config/features";
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
  return isLocalPillar(a);
}

function isAiTech(a) {
  return isAiTechPillar(a);
}

function isAiTechFeatured(a) {
  // Only allow manual pinning INSIDE AI/Tech (do not let featured override topic)
  return isAiTech(a) && Boolean(a?.featured);
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
    url: buildArticleUrl(a),
    readTime: 3,
    ...overrides,
  };
}

function escapeRegExp(s) {
  return String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function hasUsableImage(a) {
  return Boolean(String(a?.image || "").trim());
}

function splitFeedForCardsAndHeadlines(feed = [], cardsPerRow = 3, rows = 2) {
  const cardLimit = cardsPerRow * rows;
  const withImages = [];
  const withoutImages = [];

  for (const item of Array.isArray(feed) ? feed : []) {
    if (hasUsableImage(item)) withImages.push(item);
    else withoutImages.push(item);
  }

  return {
    firstCards: withImages.slice(0, cardLimit),
    headlineStrip: withoutImages,
    remainingCards: withImages.slice(cardLimit),
  };
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
  const [isMobileView, setIsMobileView] = useState(() =>
    typeof window !== "undefined" ? window.innerWidth < 768 : false
  );
const navigate = useNavigate();

  useEffect(() => {
    const onResize = () => setIsMobileView(window.innerWidth < 768);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);
  const [searchParams, setSearchParams] = useSearchParams();

  const selectedCategory = (searchParams.get("category") || "All").trim();

  const headerCategories = [
    { id: "all", name: "All" },
    { id: "local", name: "Local" },
    { id: "uk", name: "UK" },
    { id: "business", name: "Business" },
  ];

  const activeHeaderCategory =
    selectedCategory === "Local" ? "local" :
    selectedCategory === "UK" ? "uk" :
    selectedCategory === "Business" ? "business" :
    "all";

  const handleHeaderCategoryChange = (id) => {
    const value =
      id === "local" ? "Local" :
      id === "uk" ? "UK" :
      id === "business" ? "Business" :
      "";
    setSearchParams(value ? { category: value } : {});
    try { window.scrollTo({ top: 0, behavior: "smooth" }); } catch (e) {}
  };

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        setLoading(true);
        setErr("");

        const res = await fetch(getApiUrl() + "/api/articles?limit=200&with_total=1&include_archived=true");
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
  const filteredArticles = useMemo(() => {
    const list = Array.isArray(articles) ? articles : [];
    if (!selectedCategory || selectedCategory === "All") return list;

    return list.filter((a) => {
      const cat = String(a?.category || "").toLowerCase();
      const scope = String(a?.scope || "").toLowerCase();
      const text = (String(a?.title || "") + " " + String(a?.summary || "") + " " + String(a?.content || "")).toLowerCase();

      if (selectedCategory === "Local") {
        return isLocalPillar(a);
      }

      if (selectedCategory === "UK") {
        return isUkPillar(a);
      }

      if (selectedCategory === "Business") {
        return isBusinessPillar(a);
      }

      if (selectedCategory === "AI & Tech") {
        return isAiTech(a);
      }

      if (selectedCategory === "Finance") {
        return (
          cat.includes("finance") ||
          cat.includes("money") ||
          cat.includes("tax") ||
          /\b(mortgage|mortgages|rate|rates|isa|savings|interest|remortgage|stamp\s*duty|council\s*tax|budget|hmrc|vat)\b/.test(text)
        );
      }

      return true;
    });
  }, [articles, selectedCategory]);

    const newestFirst = useMemo(() => {
    return [...filteredArticles].sort(
      (a, b) => safeDateMs(b?.created_at || b?.publishedDate) - safeDateMs(a?.created_at || a?.publishedDate),
    );
  }, [filteredArticles]);

  /* ---------- ALL homepage slots with shared dedupe ---------- */
  const home = useMemo(() => {
    const used = new Set();

    // Editorial policy pool (filters out pure crime/sensational unless public-interest)
    const pool = (Array.isArray(newestFirst) ? newestFirst : []).filter(isAllowedByPolicy);
    const editorialPool = filterEditorialPool(Array.isArray(newestFirst) ? newestFirst : []);
    // ---- 40/40/20 RATIO ENFORCEMENT (Local / Authority / UK) ----
    // This ONLY reorders the pool used for homepage slot selection.
    // It does not change rendering/layout and preserves recency within each pillar.
    const basePool = editorialPool.length ? editorialPool : (Array.isArray(newestFirst) ? newestFirst : []);

    const lowerText = (a) =>
      (String(a?.title || "") + " " + String(a?.summary || "") + " " + String(a?.content || "")).toLowerCase();

    const isSportOrVideo = (a) => {
      const cat = String(a?.category || "").toLowerCase();
      const src = String(a?.source || "").toLowerCase();
      const url = String(a?.source_url || "").toLowerCase();
      // Treat sport/video as non-UK pillar for our 40/40/20 mix (keeps homepage “economic intelligence” tone)
      if (cat.includes("sport") || src.includes("sport")) return true;
      if (url.includes("skysports.com/watch") || url.includes("/watch/")) return true;
      if (src.includes("sky sports") || src.includes("bbc sport")) return true;
      return false;
    };

    const isUKPillar = (a) => {
      if (isSportOrVideo(a)) return false;
      const cat = String(a?.category || "").toLowerCase();
      const scope = String(a?.scope || "").toLowerCase();
      return scope === "uk" || cat.includes("uk");
    };

    const isAuthorityPillar = (a) => {
      // Tight “authority” definition: Business/Finance/Tax OR AI/Tech with strong signals
      const cat = String(a?.category || "").toLowerCase();
      if (cat.includes("business") || cat.includes("finance") || cat.includes("money") || cat.includes("tax")) return true;
      if (cat.includes("technology") || cat.includes("tech") || cat.includes("ai")) return true;

      const t = lowerText(a);

      // Business/finance signals
      const biz = /\b(business|economy|economic|markets?|inflation|gdp|trade|tariff|company|companies|earnings|profits?|shares?|stocks?|ftse|investment|investor|fund|bank|banking|hmrc|tax|vat|interest\s*rate|rate\s*cut|rate\s*hike|mortgage|mortgages|remortgage|savings|isa|credit\s*card)\b/;

      // AI/tech signals (kept strict)
      const tech = /\b(ai|artificial\s+intelligence|machine\s+learning|llm|openai|anthropic|google|deepmind|microsoft|chip|semiconductor|nvidia|data\s+centre|cyber|security|ransomware|software|cloud|saas|robot|automation)\b/;

      return biz.test(t) || tech.test(t);
    };

    const topicBucket = (a) => {
      const t = lowerText(a);
      if (/\b(planets?|planetary|parade|celestial|stargaz|astronom|how\s+you\s+can\s+see|photographer\s+captured)\b/.test(t)) return "astro";
      return "";
    };

    const rankScore = (a) => {
      let score = 0;
      if (a?.force_live) score += 5000;
      if (a?.is_priority_cheshire) score += 1000;
      if (a?.featured) score += 300;
      if (a?.is_secondary_cheshire) score += 120;

      const ageHours = Math.max(0, (Date.now() - safeDateMs(a?.publishedDate)) / 36e5);
      score += Math.max(0, 36 - ageHours); // stronger freshness decay over ~1.5 days

      const t = lowerText(a);

      if (isLocal(a)) score += 220;
      if (isBusinessPillar(a)) score += 180;
      if (isFinancePillar(a)) score += 180;
      if (isAiTech(a)) score += 90;
      if (isUKPillar(a)) score += 40;

      if (/\b(cheshire|chester|crewe|warrington|wilmslow|knutsford|nantwich|macclesfield|northwich|ellesmere\s+port|winsford)\b/.test(t)) score += 140;
      if (/\b(investment|economy|economic|business|finance|tax|hmrc|mortgage|savings|bank|banks|inflation|interest\s*rate|jobs?|wages?|salary|benefits?|housing|planning|rent|energy|transport|rail|trains?|buses?|factory|strike|strikes)\b/.test(t)) score += 90;
      if (/\b(ai|artificial\s+intelligence|tech|technology)\b/.test(t)) score += 35;

      return score;
    };

    const objectIdMs = (v) => {
      const id = String(v || "");
      if (!/^[0-9a-fA-F]{24}$/.test(id)) return 0;
      try {
        return parseInt(id.slice(0, 8), 16) * 1000;
      } catch {
        return 0;
      }
    };

    const freshnessMs = (a) => {
      return Math.max(
        safeDateMs(a?.publishedDate),
        objectIdMs(a?.id)
      );
    };

    const byRankThenNewest = (a, b) => {
      const freshDiff = freshnessMs(b) - freshnessMs(a);
      if (freshDiff !== 0) return freshDiff;
      return rankScore(b) - rankScore(a);
    };

    let poolAll = [];

    if (selectedCategory && selectedCategory !== "All") {
      let localFiltered = [...basePool];

      if (selectedCategory === "Local") {
        localFiltered = basePool.filter(a => {
          const cat = String(a?.category || "").toLowerCase();
          return cat === "local news" || cat === "local";
        });
      }

      const sortedBase = [...localFiltered].sort((a, b) => safeDateMs(b?.publishedDate || b?.created_at) - safeDateMs(a?.publishedDate || a?.created_at));

      if (selectedCategory === "Local") {
        const perTown = new Map();
        const balanced = [];

        for (const a of sortedBase) {
          if (balanced.length >= 28) break;

          const town = String(a?.priority_location || a?.location || "").toLowerCase().trim();
          if (!town) {
            balanced.push(a);
            continue;
          }

          const count = perTown.get(town) || 0;
          if (count >= 4) continue;

          perTown.set(town, count + 1);
          balanced.push(a);
        }

        poolAll = balanced;
      } else {
        poolAll = sortedBase.slice(0, 28);
      }
    } else {
      const localPool = basePool.filter((a) => isLocal(a)).sort(byRankThenNewest);
      const ukPool = basePool.filter((a) => !isLocal(a) && isUKPillar(a)).sort(byRankThenNewest);
      const authPool = basePool.filter((a) => !isLocal(a) && !isUKPillar(a) && isAuthorityPillar(a)).sort(byRankThenNewest);
      const otherPool = basePool.filter((a) => !isLocal(a) && !isUKPillar(a) && !isAuthorityPillar(a)).sort(byRankThenNewest);

      // Weighted pattern: 2 Local, 2 Authority, 1 UK (repeats)
      const pattern = ["local", "auth", "local", "auth", "uk"];

      let iL = 0, iA = 0, iU = 0, iO = 0;
      const totalTarget = Math.min(basePool.length, 120); // deeper homepage pool so recent active stories from the last few days can surface

      // Topic caps inside the top-28 mix (prevents single-theme takeover)
      const cap = { astro: 1 };
      const seen = { astro: 0 };

      const pickNext = (kind) => {
        if (kind === "local" && iL < localPool.length) return localPool[iL++];
        if (kind === "auth" && iA < authPool.length) return authPool[iA++];
        if (kind === "uk" && iU < ukPool.length) return ukPool[iU++];
        return null;
      };

      while (poolAll.length < totalTarget) {
        for (const kind of pattern) {
          if (poolAll.length >= totalTarget) break;

          let a = pickNext(kind);

          // Fallback order keeps strategy intent: Local → Authority → UK → Other
          if (!a && iL < localPool.length) a = localPool[iL++];
          if (!a && iA < authPool.length) a = authPool[iA++];
          if (!a && iU < ukPool.length) a = ukPool[iU++];
          if (!a && iO < otherPool.length) a = otherPool[iO++];

          if (!a) continue;

          const bucket = topicBucket(a);
          if (bucket && seen[bucket] >= (cap[bucket] || 1)) {
            continue;
          }

          if (bucket) seen[bucket] = (seen[bucket] || 0) + 1;
          poolAll.push(a);
        }

        if (iL >= localPool.length && iA >= authPool.length && iU >= ukPool.length && iO >= otherPool.length) break;
      }
    }


    const poolRanked = [...poolAll].sort(byRankThenNewest);

    const mark = (a) => {
      const k = articleKey(a);
      if (!k) return false;
      if (used.has(k)) return false;
      used.add(k);
      return true;
    };

    // 1) Hero
    const isHeroReady = (a) => String(a?.content || "").trim().length >= 1200;
    const heroArticle =
      poolAll.find(a => isLocal(a) && isHeroReady(a)) ||
      poolAll.find(a => String(a?.category || "").toLowerCase().includes("business") && isHeroReady(a)) ||
      poolAll.find(a => isAiTech(a) && isHeroReady(a)) ||
      poolAll.find(a => String(a?.category || "").toLowerCase().includes("uk") && isHeroReady(a)) ||
      poolAll.find(isLocal) ||
      poolAll.find(a => String(a?.category || "").toLowerCase().includes("business")) ||
      poolAll.find(isAiTech) ||
      poolAll.find(a => String(a?.category || "").toLowerCase().includes("uk")) ||
      poolAll[0] || null;
    if (heroArticle) mark(heroArticle);

    // 2) Top Stories (8) — fixed mix: 2 Local, 2 Business, 1 AI, 1 Property, 1 Flexible
    // 2) Top Stories (8) — fixed mix: 2 Local, 2 Business, 1 Tech, 1 Property, 1 Flexible (dedupe-safe)
    const topStoriesCards = [];

    // Top Stories (5) — fixed editorial mix (2 Local, 2 Business, 1 AI/Tech, 1 Property, 1 UK) — fixed mix:
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
    const isTopStoryAllowed = (a) => {
      const cat = String(a?.category || "").toLowerCase();
      const t = (String(a?.title || "") + " " + String(a?.summary || "")).toLowerCase();

      // HARD BLOCK entertainment
      if (/\b(celebrity|bts|netflix|movie|film|tv\b|showbiz|love island)\b/.test(t)) return false;
      if (cat.includes("entertainment")) return false;

      return true;
    };


    // Reserve scarce AI/Tech so Most Read doesn't consume it before the sidebar.
    // Reserve 5 = 1 for Top Stories AI slot + 4 for AI sidebar.
    const reservedAiKeys = new Set();
    for (const a of poolRanked) {
      if (reservedAiKeys.size >= 5) break;
      if (!isAiTech(a)) continue;
      const k = articleKey(a);
      if (k) reservedAiKeys.add(k);
    }

    const topStoryScore = (a) => {
      let score = 0;
      const cat = String(a?.category || "").toLowerCase();
      const t = (String(a?.title || "") + " " + String(a?.summary || "") + " " + String(a?.content || "")).toLowerCase();

      const ageHours = Math.max(0, (Date.now() - safeDateMs(a?.publishedDate || a?.created_at)) / 36e5);
      score += Math.max(0, 48 - ageHours);

      if (a?.force_live) score += 500;
      if (a?.is_priority_cheshire) score += 250;
      if (a?.featured) score += 120;

      if (/\b(investment|economy|economic|business|finance|tax|hmrc|mortgage|savings|interest\s*rate|inflation|jobs|housing|planning|trade|tariff)\b/.test(t)) score += 80;
      if (/\b(what\s+it\s+means|explained|analysis|guide|why|impact|cost|price|prices|bills?)\b/.test(t)) score += 40;

      // Stronger boost for stories with direct reader impact
      if (/\b(bills?|cost\s+of\s+living|prices?|inflation|mortgage|rent|housing|planning|jobs?|wages?|salary|tax|council\s+tax|benefits?|energy|petrol|diesel|transport|rail|trains?|buses?|road|closure|delays?)\b/.test(t)) score += 120;

      // Boost Cheshire / local public-impact utility stories
      if (/\b(cheshire|chester|crewe|warrington|wilmslow|knutsford|nantwich|macclesfield|northwich|ellesmere\s+port|winsford)\b/.test(t)) score += 60;

      // Slightly de-prioritise abstract science in Top Stories unless it also has direct impact framing
      if (/\b(science|research|study|scientists?|space|nasa|earth\'s|planet|consciousness|zettajoules?)\b/.test(t) && !/\b(impact|cost|price|bills?|what\s+it\s+means|economy|business|market|jobs?)\b/.test(t)) score -= 120;

      // HARD EXCLUDE entertainment from Top Stories
      if (/\b(celebrity|bts|netflix|movie|film|tv\b|showbiz|love island)\b/.test(t)) return -9999;
      if (cat.includes("entertainment")) return -9999;

      return score;
    };

    const pushTop = (a, overrideCategory = null) => {
      if (topStoriesCards.length >= 5) return;
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
    for (const a of poolRanked) {
      if (!isTopStoryAllowed(a)) continue;
      if (counts.local >= 2) break;
      if (!isLocal(a)) continue;
      if (isAiTech(a)) continue;
      if (isBusinessishTop(a)) continue;
      if (isPropertyishTop(a)) continue;
      pushTop(a, "Local News");
      counts.local += 1;
    }

    // Pass 2: Business (2) — exclude Tech/Property, pick best-scoring candidates
    for (const a of [...poolAll].sort((a, b) => topStoryScore(b) - topStoryScore(a))) {
      if (!isTopStoryAllowed(a)) continue;
      if (counts.business >= 2) break;
      if (isAiTech(a)) continue;
      if (isPropertyishTop(a)) continue;
      if (!isBusinessishTop(a)) continue;
      pushTop(a, "Business");
      counts.business += 1;
    }

    // Pass 3: AI/Tech (1)
    for (const a of poolRanked) {
      if (!isTopStoryAllowed(a)) continue;
      if (counts.tech >= 1) break;
      if (!isAiTech(a)) continue;
      pushTop(a, "AI & Tech");
      counts.tech += 1;
    }

    // Pass 4: Property (1) — ensure it is actually property-ish
    for (const a of poolRanked) {
      if (!isTopStoryAllowed(a)) continue;
      if (counts.property >= 1) break;
      if (isAiTech(a)) continue;
      if (!isPropertyishTop(a)) continue;
      pushTop(a, "Property");
      counts.property += 1;
    }

    // Pass 5: UK News (1) — explicitly UK, exclude Local/Business/Property/Tech
    for (const a of poolRanked) {
      if (!isTopStoryAllowed(a)) continue;
      if (counts.uk >= 1) break;
      if (isAiTech(a)) continue;
      if (!isUkishTop(a)) continue;
      if (isLocal(a)) continue;
      if (isBusinessishTop(a)) continue;
      if (isPropertyishTop(a)) continue;
      pushTop(a, "UK News");
      counts.uk += 1;
    }

    // Safety fill: if we still have <5 (rare), fill with newest non-tech
    for (const a of poolRanked) {
      if (topStoriesCards.length >= 5) break;
      if (isAiTech(a)) continue;
      pushTop(a);
    }

// 3) Most Read (5) — use view_count when present, exclude used
    const mostReadCards = [];

    const byViewsThenNewest = [...poolAll].sort((a, b) => {
      const av = Number(a?.view_count || a?.views || 0);
      const bv = Number(b?.view_count || b?.views || 0);
      if (bv !== av) return bv - av;
      return safeDateMs(b?.publishedDate || b?.created_at) - safeDateMs(a?.publishedDate || a?.created_at);
    });

    for (const a of byViewsThenNewest) {
      if (mostReadCards.length >= 5) break;
      const k = articleKey(a);
      if (k && reservedAiKeys.has(k)) continue; // protect AI/Tech reserve
      if (!mark(a)) continue;
      mostReadCards.push(toCard(a, `most-${mostReadCards.length}`));
    }

// 3) AI feed (6) — exclude used (exclusive; no duplicates)
    const latestPreviewKeys = (() => {
      const keys = new Set();
      for (const a of newestFirst) {
        if (keys.size >= 12) break;
        const k = articleKey(a);
        if (!k || keys.has(k)) continue;
        keys.add(k);
      }
      return keys;
    })();
    const sidebarUsed = new Set();
    const aiArticles = [];
    for (const a of poolRanked) {
      if (aiArticles.length >= 6) break;
      const k = articleKey(a);
      if (!k || latestPreviewKeys.has(k) || sidebarUsed.has(k)) continue;
      if (!isAiTech(a)) continue;
      if (!mark(a)) continue;
      aiArticles.push(toCard(a, `ai-${aiArticles.length}`, { category: "AI & Tech" }));
    }

// 4) Finance feed — structured (4 business, 1 local, 1 business latest)
    const financeArticles = [];
    const financeSeen = new Set();

        const isBusiness = (a) => {
      return isBusinessPillar(a);
    };

const isMoney = (a) => {
      return isFinancePillar(a);
    };

    const pushFinance = (a) => {
      const k = articleKey(a);
      if (!k || financeSeen.has(k) || latestPreviewKeys.has(k)) return false;
      financeSeen.add(k);
      sidebarUsed.add(k);
      financeArticles.push(toCard(a, `fin-${financeArticles.length}`));
      return true;
    };

    const sectionFreshPool = [...poolRanked].sort((a, b) => {
      const dateDiff = safeDateMs(b?.publishedDate || b?.created_at) - safeDateMs(a?.publishedDate || a?.created_at);
      if (dateDiff !== 0) return dateDiff;
      return rankScore(b) - rankScore(a);
    });

    // Pass 1: Prefer Money-ish first (2), then Business (up to 4)
    for (const a of sectionFreshPool) {
      if (financeArticles.length >= 2) break;
      if (!isMoney(a)) continue;
      pushFinance(a);
    }

    for (const a of sectionFreshPool) {
      if (financeArticles.length >= 4) break;
      if (!isBusiness(a)) continue;
      pushFinance(a);
    }

// Pass 2: 1 local news// Pass 2: 1 local news (to keep the sidebar grounded in Cheshire)
    for (const a of sectionFreshPool) {
      if (financeArticles.length >= 5) break;

      const sec = String(a?.section || "").toLowerCase();
      // Avoid pulling AI items into Business & Money
      if (isAiTech(a)) continue;

      if (!isLocal(a)) continue;
      pushFinance(a);
    }

    // Pass 3: 1 more latest business
    for (const a of sectionFreshPool) {
      if (financeArticles.length >= 6) break;
      if (!isBusiness(a)) continue;
      pushFinance(a);
    }


    
    // Fallback: if Business & Money ends up empty, fill with newest 3 non-AI
    if (financeArticles.length === 0) {
      for (const a of poolRanked) {
        if (financeArticles.length >= 3) break;
        if (isAiTech(a)) continue;
        pushFinance(a);
      }
    }


    financeArticles.sort((a,b)=> new Date(b.publishedDate||b.date||0)-new Date(a.publishedDate||a.date||0));

// 4a) Business (3) — business-first, exclude AI and exclude used
    const businessFeed = [];
    for (const a of sectionFreshPool) {
      if (businessFeed.length >= 3) break;
      const sec = String(a?.section || "").toLowerCase();
      const k = articleKey(a);
      if (!k || latestPreviewKeys.has(k) || sidebarUsed.has(k)) continue;
      if (isAiTech(a)) continue;
      if (!isBusiness(a)) continue;
      if (!mark(a)) continue;
      businessFeed.push(a);
    }

    // 4b) Mortgages & Savings (6) — keyword + section based, section-local dedupe
    const moneyFeed = [];
    const moneySeen = new Set();

    const isMoneyish = (a) => {
      const sec = String(a?.section || "").toLowerCase();
      if (["money", "tax", "property", "mortgages"].includes(sec)) return true;
      const t = (String(a?.title || "") + " " + String(a?.summary || "")).toLowerCase();
      return /\b(mortgage|mortgages|rate|rates|isa|savings|save|interest|remortgage|fixed\s*rate|tracker|stamp\s*duty|council\s*tax)\b/.test(t);
    };

    const pushMoney = (a) => {
      const k = articleKey(a);
      if (!k || moneySeen.has(k) || latestPreviewKeys.has(k) || sidebarUsed.has(k)) return false;
      moneySeen.add(k);
      moneyFeed.push(toCard(a, `money-${moneyFeed.length}`, { category: "Finance" }));
      return true;
    };

    for (const a of sectionFreshPool) {
      if (moneyFeed.length >= 6) break;
      const sec = String(a?.section || "").toLowerCase();
      if (isAiTech(a)) continue; // keep this block focused
      if (!isMoneyish(a)) continue;
      pushMoney(a);
    }

    
    // Fallback: if Mortgages & Savings ends up empty, fill with newest 6 non-AI
    if (moneyFeed.length === 0) {
      for (const a of poolRanked) {
        if (moneyFeed.length >= 6) break;
        if (isAiTech(a)) continue;
        pushMoney(a);
      }
    }

// 4c) Property & Housing (6) — planning, homes, rent, property; exclude used
    const propertyFeed = [];

    const isPropertyish = (a) => {
      const sec = String(a?.section || "").toLowerCase();
      if (["property", "housing", "planning"].includes(sec)) return true;

      const t = (String(a?.title || "") + " " + String(a?.summary || "")).toLowerCase();
      return /\b(property|housing|planning|application|approved|refused|development|homes|apartments|estate|rent|rental|landlord|tenant|lease|build|green\s*belt)\b/.test(t);
    };

    for (const a of sectionFreshPool) {
      if (propertyFeed.length >= 6) break;
      const sec = String(a?.section || "").toLowerCase();
      if (isAiTech(a)) continue;
      // section is null in backend; no section-based exclude

      if (!isPropertyish(a)) continue;
      const k = articleKey(a);
      if (!k || sidebarUsed.has(k)) continue;
      if (!mark(a)) continue;
      sidebarUsed.add(k);
      propertyFeed.push(toCard(a, `prop-${propertyFeed.length}`, { category: "Property" }));
    }


    businessFeed.sort((a,b)=> new Date(b.publishedDate||b.date||0)-new Date(a.publishedDate||a.date||0));
    moneyFeed.sort((a,b)=> new Date(b.publishedDate||b.date||0)-new Date(a.publishedDate||a.date||0));
    propertyFeed.sort((a,b)=> new Date(b.publishedDate||b.date||0)-new Date(a.publishedDate||a.date||0));


    
    // (Removed) Property & Housing fallback fill: keep this block strictly property/housing.




// 5) Latest feed (12) — strict newest-to-oldest
    const latestCards = [];
    const latestSeen = new Set();

    for (const a of newestFirst) {
      if (latestCards.length >= 12) break;

      const k = articleKey(a);
      if (!k || latestSeen.has(k)) continue;
      latestSeen.add(k);

      const resolvedCategory = getDisplayCategoryForPillar(a);

      latestCards.push(
        toCard(
          a,
          `latest-${latestCards.length}`,
          selectedCategory === "All" && resolvedCategory ? { category: resolvedCategory } : {}
        )
      );
    }

    const latestKeys = new Set(latestCards.map((a) => a?.id).filter(Boolean));
    const sidebarKeys = new Set([
      ...aiArticles.map((a) => a?.id).filter(Boolean),
      ...businessFeed.map((a) => a?.id).filter(Boolean),
      ...financeArticles.map((a) => a?.id).filter(Boolean),
      ...moneyFeed.map((a) => a?.id).filter(Boolean),
      ...propertyFeed.map((a) => a?.id).filter(Boolean),
    ]);


// 5b) AI & Business feed (avoid overlap with Latest, keep section-local dedupe)
    const aiBizFeedCards = [];
    const aiBizSeen = new Set();
    const isAiBiz = (a) => {
      const cat = String(a?.category || "").toLowerCase();
      const t = (String(a?.title || "") + " " + String(a?.summary || "") + " " + String(a?.content || "")).toLowerCase();

      // Hard blocks: entertainment / celebrity / books / showbiz filler
      if (/\b(celebrity|bts|netflix|movie|film|tv\b|showbiz|love island|novel|book launch|concert|album|music video|horror novel)\b/.test(t)) return false;
      if (cat.includes("entertainment")) return false;

      // Strong allows only
      if (isAiTech(a)) return true;
      if (isBusiness(a) || isMoney(a)) return true;
      if (typeof isPropertyish === "function" && isPropertyish(a)) return true;

      // Local public-impact or practical-economy fallback only
      if (/\b(cheshire|chester|crewe|warrington|wilmslow|knutsford|nantwich|macclesfield|northwich|ellesmere\s+port|winsford)\b/.test(t) &&
          /\b(business|jobs?|employer|company|investment|funding|wages?|salary|tax|council\s+tax|benefits?|energy|petrol|diesel|transport|rail|trains?|buses?|road|closure|delays?|bank|banks|payment|payments|housing|property|planning|rent|mortgage|nhs|school|schools|factory|strike|strikes)\b/.test(t)) return true;

      return /\b(tax|hmrc|vat|budget|inflation|interest\s*rate|rates|mortgage|remortgage|savings|isa|credit\s*card|bank|housing|property|planning|jobs?|wages?|salary|benefits?|energy|transport|ofcom|payment|payments)\b/.test(t);
    };

    for (const a of poolRanked) {
      if (aiBizFeedCards.length >= 36) break;
      if (!isAiBiz(a)) continue;
      const k = articleKey(a);
      if (!k || aiBizSeen.has(k) || latestKeys.has(k) || sidebarKeys.has(k)) continue;
      aiBizSeen.add(k);
      aiBizFeedCards.push(
        toCard(
          a,
          `aibiz-${aiBizFeedCards.length}`,
          selectedCategory === "All" ? { category: a?.category || "AI & Business" } : {}
        )
      );
    }

// 6) More stories (avoid overlap with Latest, AI & Business, and sidebars first)
      const moreStoriesCards = [];
      const moreStoriesSeen = new Set();

      const isMoreStoriesAllowed = (a) => {
        const cat = String(a?.category || "").toLowerCase();
        const t = (String(a?.title || "") + " " + String(a?.summary || "") + " " + String(a?.content || "")).toLowerCase();

        // Hard blocks: entertainment / celebrity / books / showbiz filler
        if (/\b(celebrity|bts|netflix|movie|film|tv\b|showbiz|love island|novel|book launch|concert|album|music video)\b/.test(t)) return false;
        if (cat.includes("entertainment")) return false;

        // Strong allows: local, business, finance, property, AI/tech, or useful UK public-impact stories
        if (isLocal(a) || isBusiness(a) || isMoney(a) || isAiTech(a)) return true;
        if (typeof isPropertyish === "function" && isPropertyish(a)) return true;

        if (/\b(cheshire|chester|crewe|warrington|wilmslow|knutsford|nantwich|macclesfield|northwich|ellesmere\s+port|winsford)\b/.test(t)) return true;
        if (/\b(bills?|cost\s+of\s+living|prices?|inflation|mortgage|rent|housing|planning|jobs?|wages?|salary|tax|council\s+tax|benefits?|energy|petrol|diesel|transport|rail|trains?|buses?|road|closure|delays?|ofcom|bank|banks|payment|payments|nhs|school|schools|factory|strike|strikes)\b/.test(t)) return true;

        // Block explainers / opinion / generic discussion
        if (/\b(explained|what is|what are|how does|discussion|future of|view on|opinion|editorial)\b/.test(t)) {
          return false;
        }

        // Block generic UK filler unless it has strong practical/economic relevance
        if (!isLocal(a) && !isBusiness(a) && !isMoney(a) && !isAiTech(a)) {
          if (!/\b(bills?|cost\s+of\s+living|inflation|mortgage|rent|tax|jobs?|wages?|salary|benefits?|energy|transport|rail|trains?|buses?|bank|banks|payments?|housing|planning|ofcom|nhs|school|schools|factory|strike|strikes)\b/.test(t)) {
            return false;
          }
        }

        return true;
      };
      const aiBizKeys = new Set(aiBizFeedCards.map((a) => a?.id).filter(Boolean));

      const moreStoriesScore = (a) => {
        let score = 0;
        const t = (String(a?.title || "") + " " + String(a?.summary || "") + " " + String(a?.content || "")).toLowerCase();

        if (isLocal(a)) score += 220;
        if (isBusiness(a)) score += 180;
        if (isMoney(a)) score += 180;
        if (typeof isPropertyish === "function" && isPropertyish(a)) score += 160;
        if (isAiTech(a)) score += 120;

        if (/\b(cheshire|chester|crewe|warrington|wilmslow|knutsford|nantwich|macclesfield|northwich|ellesmere\s+port|winsford)\b/.test(t)) score += 120;
        if (/\b(bills?|cost\s+of\s+living|prices?|inflation|mortgage|rent|housing|planning|jobs?|wages?|salary|tax|council\s+tax|benefits?|energy|petrol|diesel|transport|rail|trains?|buses?|road|closure|delays?|ofcom|bank|banks|payment|payments|nhs|school|schools|factory|strike|strikes)\b/.test(t)) score += 100;

        const ageHours = Math.max(0, (Date.now() - safeDateMs(a?.publishedDate || a?.created_at)) / 36e5);
        score += Math.max(0, 36 - ageHours);

        return score;
      };

      // Pass 1: strict dedupe
      for (const a of [...poolRanked].sort((a, b) => {
        const dateDiff = safeDateMs(b?.publishedDate || b?.created_at) - safeDateMs(a?.publishedDate || a?.created_at);
        if (dateDiff !== 0) return dateDiff;
        return moreStoriesScore(b) - moreStoriesScore(a);
      })) {
        if (moreStoriesCards.length >= 36) break;
        if (!isMoreStoriesAllowed(a)) continue;
        const k = articleKey(a);
        if (!k || moreStoriesSeen.has(k) || latestKeys.has(k) || aiBizKeys.has(k) || sidebarKeys.has(k)) continue;
        if (!isMoreStoriesAllowed(a)) continue;
        moreStoriesSeen.add(k);
        moreStoriesCards.push(toCard(a, `more-${moreStoriesCards.length}`));
      }

      // Pass 2: only if still short, allow sidebar overlap
      if (moreStoriesCards.length < 12) {
        for (const a of [...poolRanked].sort((a, b) => {
          const scoreDiff = moreStoriesScore(b) - moreStoriesScore(a);
          if (scoreDiff !== 0) return scoreDiff;
          return safeDateMs(b?.publishedDate || b?.created_at) - safeDateMs(a?.publishedDate || a?.created_at);
        })) {
          if (moreStoriesCards.length >= 36) break;
          if (!isMoreStoriesAllowed(a)) continue;
          const k = articleKey(a);

          // allow reuse, but avoid heavy duplication with sidebar dominance
          if (!k || moreStoriesSeen.has(k) || latestKeys.has(k)) continue;
          if (!isMoreStoriesAllowed(a)) continue;

          moreStoriesSeen.add(k);
          moreStoriesCards.push(toCard(a, `more-${moreStoriesCards.length}`));
        }
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

  const hero = selectedCategory === "All" ? (home?.hero || null) : (newestFirst?.[0] || null);

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

  const latestSplit = splitFeedForCardsAndHeadlines(showLatest ? latestFeed.slice(0, 36) : latestFeed.slice(0, isMobileView ? 4 : 12), isMobileView ? 2 : 3, 2);
  const aiBizSplit = splitFeedForCardsAndHeadlines(showAiBiz ? aiBizFeed.slice(0, 36) : aiBizFeed.slice(0, isMobileView ? 4 : 12), isMobileView ? 2 : 3, 2);
  const moreStoriesSplit = splitFeedForCardsAndHeadlines(showMoreStories ? moreStoriesFeed.slice(0, 36) : moreStoriesFeed.slice(0, isMobileView ? 4 : 12), isMobileView ? 2 : 3, 2);

  // AI & Business feed (filtered) — keep cards relevant and avoid dumping all articles here
return (
    <>
      <Helmet>
        <title>{selectedCategory === "All" ? "Latest News | Cheshire Today" : `${selectedCategory} News | Cheshire Today`}</title>
        <meta
          name="description"
          content={selectedCategory === "All"
            ? "Latest local, business, finance, AI and UK news from Cheshire Today."
            : `Latest ${selectedCategory} news and updates from Cheshire Today.`}
        />
      </Helmet>
    <div data-build="HPV1_BUILD_20260222_A" className="min-h-screen bg-neutral-50 text-slate-900 dark:bg-gray-900 dark:text-white">
    <ErrorBoundary><HomepageLayout>
      <HomepageHeader breakingStories={[]} categories={headerCategories} activeCategory={activeHeaderCategory} onCategoryChange={handleHeaderCategoryChange} />

      {loading && <div className="py-6">Loading…</div>}
      {!loading && err && <div className="py-6 text-red-600">{err}</div>}

      {!loading && !err && (
        <section className="mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
            {/* Left: Hero (dominant) */}
            <div className="lg:col-span-8 flex flex-col">
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

              <div className="mt-4 max-w-[720px]">
                <SubscribeInlineBanner />
              </div>
            </div>

            {/* Right: Top Stories (compact) */}
            <aside className="lg:col-span-4 h-full">
              {topStories.length > 0 && (
                <div className="rounded-xl border border-slate-200/50 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4 h-full">
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



      <HeroMonetisationStrip />

      {/* --- Main content: 2-column news layout --- */}
      {!loading && !err && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left: Latest feed */}
          
          <main className="lg:col-span-8 lg:-mt-4">

            {/* Latest */}
            {Array.isArray(latestFeed) && latestFeed.length > 0 && (
              <section className="rounded-xl border border-slate-200/60 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-base font-extrabold tracking-tight">{selectedCategory === "All" ? "Latest" : selectedCategory}</h2>
                  <span className="text-xs text-slate-500 dark:text-gray-400">({latestFeed.length})</span>
                  </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {latestSplit.firstCards.map((a, idx) => (
                    <div key={a?.id || a?._id || idx}>
                      <CompactArticleCard
                        onClick={() => navigate(a.url || ("/article/" + (a.id || a._id || "")))}
                        article={a}
                      />
                    </div>
                  ))}
                </div>

                {latestSplit.headlineStrip.length > 0 && (
                  <TextHeadlineStrip
                    articles={latestSplit.headlineStrip}
                    onClick={(a) => navigate(a.url || ("/article/" + (a.id || a._id || "")))}
                  />
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mt-3">
                  {latestSplit.remainingCards.map((a, idx) => (
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

            {/* AI & Business */}
            {Array.isArray(aiBizFeed) && aiBizFeed.length > 0 && (
              <section className="mt-6 rounded-xl border border-slate-200/60 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-base font-extrabold tracking-tight">Business & Finance</h2>
                  <span className="text-xs text-slate-500 dark:text-gray-400">({aiBizFeed.length})</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {aiBizSplit.firstCards.map((a, i) => (
                    <div key={a?.id || a?._id || i}>
                      <CompactArticleCard
                        onClick={() => navigate(a.url || ("/article/" + (a.id || a._id || "")))}
                        article={a}
                      />
                    </div>
                  ))}
                </div>

                {aiBizSplit.headlineStrip.length > 0 && (
                  <TextHeadlineStrip
                    articles={aiBizSplit.headlineStrip}
                  />
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mt-3">
                  {aiBizSplit.remainingCards.map((a, i) => (
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
                  {moreStoriesSplit.firstCards.map((a, i) => (
                    <div key={a?.id || a?._id || i}>
                      <CompactArticleCard
                        onClick={() => navigate(a.url || ("/article/" + (a.id || a._id || "")))}
                        article={a}
                      />
                    </div>
                  ))}
                </div>

                {moreStoriesSplit.headlineStrip.length > 0 && (
                  <TextHeadlineStrip
                    articles={moreStoriesSplit.headlineStrip}
                  />
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mt-3">
                  {moreStoriesSplit.remainingCards.map((a, i) => (
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
          <aside className="hidden lg:block lg:col-span-4 lg:-mt-4 self-start">
            <div className="space-y-6 md:space-y-8 lg:sticky lg:top-24 self-start h-fit">

            {/* Business & Money */}
            {Array.isArray(businessFeed) && businessFeed.length > 0 && (
              <LeadSection
                title="Business"
                badgeText="Business"
                items={businessFeed.slice(0, 6)}
                onNavigate={(url) => navigate(url)}
              />
            )}

            {/* AI & Tech */}
            {Array.isArray(aiFeed) && aiFeed.length > 0 && (
              <LeadSection
                title="AI & Tech"
                badgeText="AI Pulse"
                badgeClassName="text-[10px] uppercase tracking-wide font-semibold px-2 py-1 rounded-full border border-indigo-200 bg-indigo-50 text-indigo-700 dark:border-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-200"
                items={aiFeed.slice(0, 6)}
                onNavigate={(url) => navigate(url)}
              />
            )}
            {/* Mortgages & Savings */}

            {Array.isArray(moneyFeed) && moneyFeed.length > 0 && (
              <LeadSection
                title="Finance"
                badgeText="Finance"
                items={moneyFeed.slice(0, 6)}
                onNavigate={(url) => navigate(url)}
              />
            )}

            {/* Property & Housing */}
            
            {Array.isArray(propertyFeed) && propertyFeed.length > 0 && (
              <LeadSection
                title="Property & Tax"
                badgeText="Property"
                badgeClassName="text-[10px] uppercase tracking-wide font-semibold px-2 py-1 rounded-full border border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-900/30 dark:text-amber-200"
                items={propertyFeed.slice(0, 6)}
                onNavigate={(url) => navigate(url)}
              />
            )}
            <AffiliateWidgetSidebar category="default" />
            </div>
          </aside>
        </div>
      )}

      <NewsFooter />
</HomepageLayout></ErrorBoundary>
    </div>
    </>

  );
}