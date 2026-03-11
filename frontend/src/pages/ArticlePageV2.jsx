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
import SubscribeSection from "../components/SubscribeSection";
import { SubscribeInlineBanner } from "../components/JobsWidget";
import CompactArticleCard from "../components/CompactArticleCard";
import { AffiliateWidgetSidebar } from "../components/AffiliateWidgets";
import { filterEditorialPool, getPrimaryPillar } from "../utils/editorialPolicy";

import { FEATURES } from "../config/features";

function getSourceLabel(article) {
  const raw = String(article?.source || "").trim();
  const link = String(article?.sourceUrl || article?.source_url || "").trim();

  // If 'source' is missing, use hostname from source_url
  const fallbackFromLink = () => {
    try {
      if (!link) return "";
      return new URL(link).hostname.replace(/^www\./, "");
    } catch {
      return "";
    }
  };

  // If 'source' itself is a URL, show hostname instead of the full URL
  const looksLikeUrl = /^https?:\/\//i.test(raw);
  if (!raw) return fallbackFromLink() || "Source";
  if (looksLikeUrl) {
    try {
      return new URL(raw).hostname.replace(/^www\./, "");
    } catch {
      return fallbackFromLink() || "Source";
    }
  }
  return raw;
}

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

/* ===== Contextual auto-linking (monetisation) =====
   - Escapes HTML first
   - Adds limited internal links to relevant guides
   - Avoids linking inside existing URLs
*/
function escapeHtml(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&lt;".replace("&lt;","&lt;")) /* noop to keep build deterministic */
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function autoLinkContent(rawText, pillarLabel) {
  const text = String(rawText || "");
  if (!text.trim()) return "";

  // 1) Escape first (safety)
  let html = escapeHtml(text);

  // Non-Amazon monetisation OFF => do NOT auto-inject /guides/ links into article body.
  // Keep newline formatting consistent with existing rendering.
  if (!FEATURES.NON_AMAZON_MONETISATION_ENABLED) {
    html = html.replace(/\n/g, "<br/>");
    return html;
  }

  // 2) Protect plain URLs from being modified
  const urlRe = /(https?:\/\/[^\s<]+)/gi;
  const protectedUrls = [];
  html = html.replace(urlRe, (m) => {
    const token = `__URLTOKEN_${protectedUrls.length}__`;
    protectedUrls.push(m);
    return token;
  });

  const pillar = String(pillarLabel || "").toLowerCase();

  // 3) Define link targets (ordered by monetisation priority)
  const links = [];

  const add = (pattern, href) => links.push({ pattern, href });

  // Local tax
// Finance staples

  // Business (draft pages exist; link anyway — they render)
// Investing / ISA (draft exists)
// AI (published)
// 4) Apply with limits (avoid spam)
  const maxLinks = pillar.includes("ai") ? 3 : 4;
  let used = 0;
  const usedHref = new Set();

  const replaceOnce = (re, href) => {
    if (used >= maxLinks) return;
    if (usedHref.has(href)) return;

    const m = html.match(re);
    if (!m) return;

    const matchText = m[0];
    // Replace only the first match, wrap it
    html = html.replace(re, `<a href="${href}" class="underline underline-offset-2 font-semibold">${matchText}</a>`);
    used += 1;
    usedHref.add(href);
  };

  // Prioritise by pillar
  if (pillar.includes("ai")) {
} else if (pillar.includes("business")) {
} else if (pillar.includes("finance")) {
  } else if (pillar.includes("local")) {
}

  // Fill remaining in general priority order
  for (const { pattern, href } of links) {
    if (used >= maxLinks) break;
    replaceOnce(pattern, href);
  }

  // 5) Restore URLs
  for (let idx = 0; idx < protectedUrls.length; idx++) {
    const token = `__URLTOKEN_${idx}__`;
    const url = protectedUrls[idx];
    html = html.replaceAll(token, url);
  }

  // 6) Convert plain text into real paragraphs for improved article typography.
  // Split on blank lines first; within each paragraph, preserve single line breaks.
  const sentences = html.split(/(?<=[.!?])\s+/);
  const paragraphs = [];
  let buf = [];

  for (const s of sentences) {
    buf.push(s);
    if (buf.length >= 3) {
      paragraphs.push(`<p>${buf.join(" ")}</p>`);
      buf = [];
    }
  }

  if (buf.length) {
    paragraphs.push(`<p>${buf.join(" ")}</p>`);
  }

  return paragraphs.join("");
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


function slugifyArticleTitle(title) {
  const raw = safeText(title).toLowerCase();
  const slug = raw.replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  return (slug || "article").slice(0, 80);
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


/* ===== Guide selection (pillar-aware) ===== */
function pickGuidesForPillar(guides, pillarLabel) {
  // Non-Amazon monetisation OFF => hide AI Guides / In-depth Guide module
  if (!FEATURES.NON_AMAZON_MONETISATION_ENABLED) return [];

  const list = Array.isArray(guides) ? guides : [];
  const pillar = String(pillarLabel || "").toLowerCase();

  const bySlug = new Map(list.map((g) => [String(g?.slug || ""), g]));
  const want = [];

  const push = (slug) => {
    if (!slug) return;
    if (!bySlug.has(slug)) return;
    if (want.includes(slug)) return;
    want.push(slug);
  };

  if (pillar.includes("ai")) {
    push("best-ai-tools-uk");
    push("best-ai-writing-tools-uk");
    push("best-ai-productivity-tools-uk");
  } else if (pillar.includes("business")) {
    push("best-business-bank-accounts-uk");
    push("best-accounting-software-uk");
    push("best-business-credit-cards-uk");
  } else if (pillar.includes("finance")) {
    push("best-isa-platforms-uk");
  } else if (pillar.includes("local")) {
    push("council-tax-bands-cheshire");
  } else {
    push("best-ai-tools-uk");
  }

  const out = [];
  for (const slug of want) {
    const g = bySlug.get(slug);
    if (g) out.push(g);
    if (out.length >= 3) break;
  }

  if (out.length < 3) {
    for (const g of list) {
      const slug = String(g?.slug || "");
      if (!slug) continue;
      if (out.some((x) => String(x?.slug || "") === slug)) continue;
      out.push(g);
      if (out.length >= 3) break;
    }
  }

  return out.slice(0, 3);
}

/* ===== AI Guide Promo Block (Monetisation Funnel) ===== */
const GuidePromoBlock = ({ guides = [], category, pillarLabel }) => {
  if (!FEATURES.NON_AMAZON_MONETISATION_ENABLED) return null;
  if (!Array.isArray(guides) || guides.length === 0) return null;

  const cat = String(category || "").toLowerCase();
  const ordered = pickGuidesForPillar(guides, pillarLabel || category);

  return (
    <div className="mt-6 p-4 rounded-xl border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20">
      <div className="text-xs font-semibold text-sky-800 dark:text-slate-200 mb-2">🔎 AI Guides</div>
      <div className="space-y-2">
        {ordered.map((g) => (
          <div
            key={g.slug}
            className="rounded-lg border border-slate-200 dark:border-slate-800 bg-[#FBFAF7] dark:bg-transparent p-2.5"
          >
            <a
              href={"#"}
              className="block font-semibold text-sky-900 dark:text-slate-200 hover:underline underline-offset-2"
            >
              {safeText(g.title) || g.slug}
            </a>
            <div className="text-[11px] mt-1 text-slate-700 dark:text-gray-400">
              Updated: {String(g.updated_at || g.created_at || "").slice(0, 10)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const GuidesInlinePromo = ({ guides, pillarLabel }) => {
  if (!FEATURES.NON_AMAZON_MONETISATION_ENABLED) return null;
  const list = Array.isArray(guides) ? guides : [];
  const picked = pickGuidesForPillar(list, pillarLabel);
  const g = picked[0];
  if (!g) return null;

  const title = safeText(g?.title) || "In-depth Guide";
  const slug = String(g?.slug || "").trim();
  const href = null;

  return (
    <div className="mt-6 p-4 rounded-xl border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20">
      <div className="text-xs font-semibold text-sky-800 dark:text-slate-200 mb-1">In-depth Guide</div>
      <a href={href} className="block font-semibold text-sky-900 dark:text-slate-200 hover:underline underline-offset-2">
        {title}
      </a>
      <div className="text-[11px] mt-1 text-slate-700 dark:text-gray-400">
        Updated UK guide with recommendations and affiliate disclosures →
      </div>
    </div>
  );
};

export default function ArticlePageV2({ categories }) {
  const { articleId } = useParams();
  const navigate = useNavigate();
  // --- More stories (below article) ---
  const [moreStories, setMoreStories] = useState([]);
  const [moreStoriesOpen, setMoreStoriesOpen] = useState(false);

  const fmtShort = (dateString) => {
    const d = new Date(dateString);
    if (Number.isNaN(d.getTime())) return "";
    return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
  };

  useEffect(() => {
    let mounted = true;

    async function fetchMoreStories() {
      try {
        const API = getApiUrl().replace(/\/$/, "");
        const res = await fetch(`${API}/api/articles?limit=24`);
        if (!res.ok) return;

        const data = await res.json();
        const list = Array.isArray(data)
          ? data
          : Array.isArray(data?.articles)
          ? data.articles
          : [];

        const cleaned = list
          .filter((a) => a && (a.id || a._id) && String(a.id || a._id) !== String(articleId))
          .filter((a) => String(a.title || "").trim().length > 0);

        if (mounted) setMoreStories(filterEditorialPool(cleaned));
      } catch (_) {
        // ignore
      }
    }

    fetchMoreStories();
    return () => {
      mounted = false;
    };
  }, [articleId]);

  const [article, setArticle] = useState(null);
  const [guides, setGuides] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  const publicUrl =
    process.env.REACT_APP_PUBLIC_URL || (typeof window !== "undefined" ? window.location.origin : "");

  const description = useMemo(() => buildDescription(article), [article]);
  const safeTitle = useMemo(() => safeText(article?.title), [article]);

  const readingTime = useMemo(() => {
    const text = String(article?.content || "");
    const words = text.trim().split(/\s+/).length;
    return Math.max(1, Math.round(words / 200));
  }, [article]);


  // Pillar label for sidebar (keeps the publication feeling intentional)
  const pillarLabel = useMemo(() => {
    const pillar = getPrimaryPillar(article);
    return pillar === "UK" ? "Local" : pillar;
  }, [article]);


  const rawBody = useMemo(() => {
    const c = article?.content;
    const s = article?.summary;
    if (typeof c === "string" && c.trim()) return c;
    if (typeof s === "string" && s.trim()) return s;
    // last-resort stringify avoidance: return empty instead of rendering objects
    return "";
  }, [article]);

  const { main: mainContent, attribution } = useMemo(() => splitAttribution(rawBody), [rawBody]);


  // Contextual monetisation mapping: convert article metadata -> tool category
  // Hybrid approach: section-first (if present), then category, then keywords.
  const contextToolType = useMemo(() => {
    const sec = String(article?.section || "").toLowerCase();
    const cat = String(article?.category || "").toLowerCase();
    const title = String(article?.title || "").toLowerCase();
    const summary = String(article?.summary || "").toLowerCase();
    const text = `${sec} ${cat} ${title} ${summary}`.replace(/\s+/g, " ").trim();

    // 1) SECTION-FIRST (most reliable when available)
    if (sec.startsWith("ai-")) return "ai";
    if (sec === "mortgages" || sec === "mortgage") return "mortgages";
    if (sec === "savings" || sec === "isas") return "savings";
    if (sec === "tax") return "tax";
    if (sec === "property" || sec === "housing" || sec === "planning") return "property";
    if (sec === "credit") return "credit";
    if (sec === "energy" || sec === "utilities") return "energy";

    // 2) CATEGORY NEXT
    if (cat.includes("ai") || cat.includes("tech")) return "ai";
    if (cat.includes("mortgage")) return "mortgages";
    if (cat.includes("savings") || cat.includes("isa")) return "savings";
    if (cat.includes("tax")) return "tax";
    if (cat.includes("property") || cat.includes("housing") || cat.includes("planning")) return "property";
    if (cat.includes("credit")) return "credit";
    if (cat.includes("energy") || cat.includes("utilities") || cat.includes("broadband")) return "energy";

    // 3) KEYWORD FALLBACK (ordered by intent)
    if (/\b(chatgpt|openai|gemini|llm|ai|artificial intelligence|machine learning)\b/.test(text)) return "ai";

    // Tax first (so “council tax” and “stamp duty” don't fall into generic property)
    if (/\b(hmrc|tax|vat|self assessment|national insurance|ni contributions|council tax|stamp duty)\b/.test(text)) return "tax";

    if (/\b(remortgage|mortgage|fixed rate|tracker)\b/.test(text)) return "mortgages";
    if (/\b(isa|savings|easy-access|interest rate)\b/.test(text)) return "savings";
    if (/\b(property|house price|rent|rental|landlord|tenant|letting|planning permission|green belt)\b/.test(text)) return "property";

    if (/\b(credit card|balance transfer|apr|loan|debt)\b/.test(text)) return "credit";
    if (/\b(energy|tariff|broadband|utilities)\b/.test(text)) return "energy";

    return "";
  }, [article]);


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

        // Load published authority pages (guides) for monetisation funnel
        try {
          const gRes = await fetch(`${API_BASE}/api/authority-pages?limit=50&status=published`);
          if (gRes.ok) {
            const gData = await gRes.json();
            if (mounted) setGuides(Array.isArray(gData) ? gData : []);
          }
        } catch (_) {
          // non-fatal
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
    const shareUrl = canonicalUrl;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(shareUrl);
      toast({ title: "Link Copied!", description: "Article link copied to clipboard!" });
    }
  };

  if (loading) {
    return (
      <HelmetProvider>
        <div className="min-h-screen bg-[#F7F4EE] text-neutral-900 dark:bg-gray-900 dark:text-white">
          <FestiveTheme />
          <NewsHeader
            categories={categories}
            activeCategory="all"
            onCategoryChange={() => navigate("/")}
            onSearch={() => {}}
          />
          <div className="container mx-auto px-4 py-20">
            <div className="flex flex-col items-center justify-center">
              <Loader2 className="h-16 w-16 animate-spin text-slate-600 mb-4" />
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
        <div className="min-h-screen bg-[#F7F4EE] text-neutral-900 dark:bg-gray-900 dark:text-white">
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

          <main className="container mx-auto px-4 py-16 max-w-7xl">
            <h1 className="text-4xl font-extrabold text-foreground mb-3">Article Not Found</h1>
            <p className="text-muted-foreground mb-6">{errorMsg || "Sorry, this link may be incorrect."}</p>
            <button
              onClick={() => navigate("/")}
              className="inline-flex items-center justify-center rounded-md bg-sky-700 px-4 py-2 text-white font-medium hover:bg-sky-800"
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

  const articleSlug = slugifyArticleTitle(safeTitle || article?.title || "article");
  const canonicalUrl = `${publicUrl}/article/${articleId}/${articleSlug}`;

  const absoluteImageUrl = (() => {
    const img = String(article?.image || "").trim();
    if (!img) return "";
    if (/^https?:\/\//i.test(img)) return img;
    // Support relative paths (e.g. /images/x.jpg)
    return `${publicUrl}${img.startsWith("/") ? "" : "/"}${img}`;
  })();

  const jsonLdNewsArticle = {
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    mainEntityOfPage: { "@type": "WebPage", "@id": canonicalUrl },
    headline: safeTitle || "Article",
    description,
    image: absoluteImageUrl ? [absoluteImageUrl] : undefined,
    datePublished: article?.publishedDate || article?.published_at || article?.created_at || undefined,
    dateModified: article?.updated_at || article?.publishedDate || article?.published_at || article?.created_at || undefined,
    author: { "@type": "Organization", name: "Cheshire Today" },
    publisher: {
      "@type": "Organization",
      name: "Cheshire Today",
      logo: {
        "@type": "ImageObject",
        url: `${publicUrl}/logo.png`,
      },
    },
  };

  return (
    <HelmetProvider>
      <div className="min-h-screen bg-[#F7F4EE] text-neutral-900 dark:bg-gray-900 dark:text-white">
        <FestiveTheme />

        <Helmet>
          <title>{safeTitle || "Article"} | Cheshire Today</title>
          <meta name="description" content={description} />

          <link rel="canonical" href={canonicalUrl} />

          {/* Structured data for Google */}
          <script type="application/ld+json">
            {JSON.stringify(jsonLdNewsArticle)}
          </script>

          <meta property="og:type" content="article" />
          <meta property="og:url" content={canonicalUrl} />
          <meta property="og:title" content={safeTitle} />
          <meta property="og:description" content={description} />
          {absoluteImageUrl && <meta property="og:image" content={absoluteImageUrl} />}

          <meta name="twitter:card" content="summary_large_image" />
          <meta name="twitter:url" content={canonicalUrl} />
          <meta name="twitter:title" content={safeTitle} />
          <meta name="twitter:description" content={description} />
          {absoluteImageUrl && <meta name="twitter:image" content={absoluteImageUrl} />}
        </Helmet>

        <NewsHeader
          categories={categories}
          activeCategory="all"
          onCategoryChange={() => navigate("/")}
          onSearch={() => {}}
        />

        <main className="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-8 md:py-12">
          <div className="mb-6">
            <button onClick={() => navigate(-1)} className="text-sm text-slate-700 hover:underline underline-offset-2 dark:text-slate-200">
              ← Back
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <article className="lg:col-span-8">
              <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">
                {String(article?.category || "Article")}
              </div>
              <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-foreground">{safeTitle}</h1>

              <div className="mt-3 text-sm text-muted-foreground flex items-center gap-3">
                <span>{published}</span>
                <span>• {readingTime} min read</span>
                <button onClick={handleShare} className="ml-auto text-slate-700 hover:underline underline-offset-2 text-sm dark:text-slate-200 dark:hover:text-white">
                  Share
                </button>
              </div>

              {article.image && (
                <img
                  src={absoluteImageUrl || article.image}
                  alt={safeTitle || "Article image"}
                  loading="lazy"
                  decoding="async"
                  width="1200"
                  height="630"
                  className="w-full rounded-xl mt-6 mb-6 object-cover"
                />
              )}
<div className="rounded-2xl bg-[#FBFAF7] dark:bg-transparent border border-[#E6E1D8] dark:border-border p-5 md:p-8">
                <div className="prose prose-lg md:prose-xl prose-slate max-w-none text-slate-800 dark:text-slate-100 dark:prose-invert prose-p:my-7 prose-p:leading-9 prose-li:my-3 prose-a:text-slate-700 prose-a:underline-offset-2 dark:prose-a:text-slate-200 [&>div>p]:my-7 [&>div>p]:leading-9 [&>div>p]:text-[1.08rem] md:[&>div>p]:text-[1.12rem] [&>div>p]:tracking-[0.01em] [&>div>p]:text-slate-800 dark:[&>div>p]:text-slate-100">
                {/* auto-linked content (safe) */}
                <div dangerouslySetInnerHTML={{ __html: autoLinkContent(mainContent, pillarLabel) }} />
              </div>


              
              

              {(article.source || article.source_url) && (
                <div className="mt-8 pt-6 border-t border-border">
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Source:{" "}
                    {(article.sourceUrl || article.source_url) ? (
                      <a
                        href={article.sourceUrl || article.source_url}
                        target="_blank"
                        rel="nofollow noopener noreferrer"
                        className="font-medium text-foreground hover:underline underline-offset-2"
                      >
                        {getSourceLabel(article)}
                      </a>
                    ) : (
                      <span className="font-medium text-foreground">{getSourceLabel(article)}</span>
                    )}
                  </p>

                  {attribution ? (
                    <p className="mt-2 text-[11px] text-muted-foreground whitespace-pre-wrap leading-relaxed">
                      {safeText(attribution)}
                    </p>
                  ) : null}
                </div>
              )}


              </div>

              <div className="mt-6">
                <SubscribeInlineBanner />
              </div>

              <div className="mt-6">
                <GuidesInlinePromo guides={guides} pillarLabel={pillarLabel} />
                
              <GuidePromoBlock guides={guides} category={article?.category} pillarLabel={pillarLabel} />
              </div>
              {/* More stories — match homepage layout */}
              
              {/* More stories (publisher-style) — collapsed shows only one row */}
              
              {/* More stories (homepage card style) — collapsed shows only one row */}
              {Array.isArray(moreStories) && moreStories.length > 0 && (
                <section className="mt-10">
                  <div className="flex items-center justify-between mb-3">
                    <h2 className="text-sm font-extrabold tracking-tight text-neutral-900 dark:text-white">
                      More stories
                    </h2>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {(moreStoriesOpen ? moreStories.slice(0, 12) : moreStories.slice(0, 4)).map((a, idx) => (
                      <div key={a?.id || a?._id || idx}>
                        <CompactArticleCard
                          onClick={() => navigate(a?.url || ("/article/" + (a?.id || a?._id || "")))}
                          article={{
                            title: a?.title,
                            content: a?.summary || a?.content || "",
                            summary: a?.summary || "",
                            image: a?.image,
                            category: a?.category,
                            location: a?.town || a?.location || "Cheshire",
                            publishedDate: a?.publishedDate || a?.published_at || a?.created_at,
                            readTime: a?.readTime || 3,
                            url: a?.url || ("/article/" + (a?.id || a?._id || "")),
                          }}
                        />
                      </div>
                    ))}
                  </div>

                  {moreStories.length > 4 && (
                    <div className="mt-3 flex justify-center">
                      <button
                        type="button"
                        onClick={() => setMoreStoriesOpen((v) => !v)}
                        className="text-xs font-semibold text-slate-700 hover:underline underline-offset-2 dark:text-slate-200"
                      >
                        {moreStoriesOpen ? "Show less" : "Show more"}
                      </button>
                    </div>
                  )}
                </section>
              )}

                        


            </article>

            <aside className="hidden lg:block lg:col-span-4 space-y-3 [overflow-anchor:none]">
              <div className="space-y-6 md:space-y-8 lg:sticky lg:top-24 self-start">
                <div className="rounded-xl border border-slate-200/60 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4">
                  <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-bold">More in {pillarLabel}</h3>
                  <span className="text-[11px] px-2 py-1 rounded bg-muted text-muted-foreground">
                    {pillarLabel}
                  </span>
                </div>
                  <RelatedArticles
                    articleId={articleId}
                    variant="sidebar"
                    limit={6}
                    onArticleClick={(a) => navigate("/article/" + a.id)}
                  />
                </div>

                {/* Filler blocks (match homepage rhythm / avoids empty sidebar) */}                {/* Latest (fills sidebar height, compact) */}
                {Array.isArray(moreStories) && moreStories.length > 0 && (
                  <div className="rounded-xl border border-slate-200/60 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-sm font-bold text-foreground">Latest</h3>
                      <span className="text-[11px] px-2 py-1 rounded bg-muted text-muted-foreground">
                        Updated
                      </span>
                    </div>

                    <div className="space-y-2">
                      {moreStories.slice(0, 6).map((a, idx) => (
                        <CompactArticleCard
                          key={a?.id || a?._id || idx}
                          horizontal
                          onClick={() => navigate(a?.url || ("/article/" + (a?.id || a?._id || "")))}
                          article={{
                            id: a?.id || a?._id || String(idx),
                            title: a?.title,
                            content: a?.summary || a?.content || "",
                            summary: a?.summary || "",
                            image: a?.image,
                            category: a?.category,
                            location: a?.town || a?.location || "Cheshire",
                            publishedDate: a?.publishedDate || a?.published_at || a?.created_at,
                            readTime: a?.readTime || 3,
                            url: a?.url || ("/article/" + (a?.id || a?._id || "")),
                          }}
                        />
                      ))}
                    </div>
                  </div>
                )}

                {Array.isArray(moreStories) && moreStories.length > 6 && (
                  <div className="rounded-xl border border-slate-200/60 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-sm font-bold text-foreground">More from Cheshire Today</h3>
                      <span className="text-[11px] px-2 py-1 rounded bg-muted text-muted-foreground">
                        Editorial
                      </span>
                    </div>

                    <div className="space-y-2">
                      {moreStories.slice(6, 12).map((a, idx) => (
                        <CompactArticleCard
                          key={a?.id || a?._id || `more-sidebar-${idx}`}
                          horizontal
                          onClick={() => navigate(a?.url || ("/article/" + (a?.id || a?._id || "")))}
                          article={{
                            id: a?.id || a?._id || String(idx),
                            title: a?.title,
                            content: a?.summary || a?.content || "",
                            summary: a?.summary || "",
                            image: a?.image,
                            category: a?.category,
                            location: a?.town || a?.location || "Cheshire",
                            publishedDate: a?.publishedDate || a?.published_at || a?.created_at,
                            readTime: a?.readTime || 3,
                            url: a?.url || ("/article/" + (a?.id || a?._id || "")),
                          }}
                        />
                      ))}
                    </div>
                  </div>
                )}


                {/* Sponsored (Amazon affiliate) */}
                <AffiliateWidgetSidebar 
                  category={
                    pillarLabel?.toLowerCase().includes("ai") ? "tech" :
                    pillarLabel?.toLowerCase().includes("business") ? "business" :
                    pillarLabel?.toLowerCase().includes("finance") ? "business" :
                    "default"
                  }
                />

<div className="rounded-xl border border-slate-200/60 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4">
                  <SubscribeSection compact />
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
