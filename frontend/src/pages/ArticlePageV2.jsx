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
import TextHeadlineStrip from "../components/homepage/TextHeadlineStrip";
import { AffiliateWidgetSidebar } from "../components/AffiliateWidgets";
import { filterEditorialPool, getPrimaryPillar } from "../utils/editorialPolicy";

import { FEATURES } from "../config/features";
import { monetisationTools } from "../config/monetisationTools";

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
  if (!FEATURES.ARTICLE_INLINE_GUIDES_ENABLED) {
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

  // Local / utility
  add(/\b(council\s+tax)\b/i, "/guides/council-tax-bands-cheshire");

  // Business guides with real destinations / stronger controlled-rollout value
  add(/\b(accounting\s+software|bookkeeping|xero|quickbooks)\b/i, "/guides/best-accounting-software-uk");
  add(/\b(mailchimp|email\s+marketing|newsletter\s+tools?|email\s+automation|marketing\s+automation|audience\s+segmentation|campaign\s+automation)\b/i, "/guides/best-email-marketing-tools-small-business-uk");
  add(/\b(domain\s+name|domain\s+registration|domain\s+registrar|registrar)\b/i, "/guides/best-domain-registrars-small-business-uk");
  add(/\b(web\s+hosting|hosting\s+provider|hosting)\b/i, "/guides/best-web-hosting-small-business-uk");
  add(/\b(website\s+builder|website\s+builders)\b/i, "/guides/best-website-builders-small-business-uk");
  add(/\b(virtual\s+office|business\s+address|registered\s+office|mail\s+handling|mail\s+forwarding)\b/i, "/guides/best-virtual-office-services-small-business-uk");
  add(/\b(self-storage|self\s+storage|storage\s+unit|storage\s+units|storage\s+facility|storage\s+facilities|safestore)\b/i, "/guides/best-self-storage-services-uk-home-business");
  add(/\b(will\s+writing|online\s+will|make\s+a\s+will|probate|inheritance|estate\s+planning|power\s+of\s+attorney)\b/i, "/guides/best-online-will-writing-services-uk");
  add(/\b(courier|parcel|shipping|delivery|fulfilment|fulfillment|multi-carrier)\b/i, "/guides/best-parcel-courier-services-small-business-uk");
  add(/\b(iso\s+9001|iso\s+14001|iso\s+27001|iso\s+certification|iso\s+training|audit\s+readiness)\b/i, "/guides/best-iso-training-certification-courses-uk-businesses");

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
    html = html.replace(re, `<a href="${href}" class="underline underline-offset-2 font-semibold">${matchText}</a>`);
    used += 1;
    usedHref.add(href);
  };

  // Prioritise by pillar
  if (pillar.includes("business")) {
    replaceOnce(/\b(accounting\s+software|bookkeeping|xero|quickbooks)\b/i, "/guides/best-accounting-software-uk");
    replaceOnce(/\b(mailchimp|email\s+marketing|newsletter\s+tools?|email\s+automation|marketing\s+automation|audience\s+segmentation|campaign\s+automation)\b/i, "/guides/best-email-marketing-tools-small-business-uk");
    replaceOnce(/\b(domain\s+name|domain\s+registration|domain\s+registrar|registrar)\b/i, "/guides/best-domain-registrars-small-business-uk");
    replaceOnce(/\b(web\s+hosting|hosting\s+provider|hosting)\b/i, "/guides/best-web-hosting-small-business-uk");
    replaceOnce(/\b(website\s+builder|website\s+builders)\b/i, "/guides/best-website-builders-small-business-uk");
    replaceOnce(/\b(virtual\s+office|business\s+address|registered\s+office|mail\s+handling|mail\s+forwarding)\b/i, "/guides/best-virtual-office-services-small-business-uk");
    replaceOnce(/\b(self-storage|self\s+storage|storage\s+unit|storage\s+units|storage\s+facility|storage\s+facilities|safestore)\b/i, "/guides/best-self-storage-services-uk-home-business");
    replaceOnce(/\b(will\s+writing|online\s+will|make\s+a\s+will|probate|inheritance|estate\s+planning|power\s+of\s+attorney)\b/i, "/guides/best-online-will-writing-services-uk");
    replaceOnce(/\b(courier|parcel|shipping|delivery|fulfilment|fulfillment|multi-carrier)\b/i, "/guides/best-parcel-courier-services-small-business-uk");
    replaceOnce(/\b(iso\s+9001|iso\s+14001|iso\s+27001|iso\s+certification|iso\s+training|audit\s+readiness)\b/i, "/guides/best-iso-training-certification-courses-uk-businesses");
  } else if (pillar.includes("local")) {
    replaceOnce(/\b(council\s+tax)\b/i, "/guides/council-tax-bands-cheshire");
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
function pickGuidesForPillar(guides, pillarLabel, contextToolType = "") {
  if (!FEATURES.ARTICLE_INLINE_GUIDES_ENABLED) return [];

  const list = Array.isArray(guides) ? guides : [];
  const pillar = String(pillarLabel || "").toLowerCase();
  const context = String(contextToolType || "").toLowerCase();

  const bySlug = new Map(list.map((g) => [String(g?.slug || ""), g]));
  const want = [];

  const ALLOWED_PROMO_GUIDE_SLUGS = new Set([
    "council-tax-bands-cheshire",
    "best-online-will-writing-services-uk",
    "best-accounting-software-uk",
    "best-email-marketing-tools-small-business-uk",
    "best-domain-registrars-small-business-uk",
    "best-web-hosting-small-business-uk",
    "best-website-builders-small-business-uk",
    "best-virtual-office-services-small-business-uk",
    "best-company-formation-services-uk",
    "best-self-storage-services-uk-home-business",
    "best-removal-van-services-uk",
    "best-mattress-deals-uk",
    "best-parcel-courier-services-small-business-uk",
    "how-to-choose-shipping-solution-online-business-uk",
    "best-iso-training-certification-courses-uk-businesses",
    "what-iso-certification-means-small-business-uk",
    "best-explainer-video-software-uk",
  ]);

  const push = (slug) => {
    const key = String(slug || "").trim();
    if (!key) return;
    if (!ALLOWED_PROMO_GUIDE_SLUGS.has(key)) return;
    if (!bySlug.has(key)) return;
    if (want.includes(key)) return;
    want.push(key);
  };

  if (context === "tax" || context === "property") {
    push("council-tax-bands-cheshire");
  } else if (context === "accounting") {
    push("best-accounting-software-uk");
    push("best-email-marketing-tools-small-business-uk");
    push("best-domain-registrars-small-business-uk");
  } else if (context === "business-banking") {
    push("best-accounting-software-uk");
    push("best-email-marketing-tools-small-business-uk");
    push("best-domain-registrars-small-business-uk");
  } else if (context === "virtual-office") {
    push("best-virtual-office-services-small-business-uk");
    push("best-company-formation-services-uk");
    push("best-domain-registrars-small-business-uk");
    push("best-website-builders-small-business-uk");
  } else if (context === "web-presence") {
    push("best-domain-registrars-small-business-uk");
    push("best-web-hosting-small-business-uk");
    push("best-website-builders-small-business-uk");
    push("best-virtual-office-services-small-business-uk");
  } else if (context === "company-formation") {
    push("best-company-formation-services-uk");
    push("best-virtual-office-services-small-business-uk");
    push("best-domain-registrars-small-business-uk");
    push("best-website-builders-small-business-uk");
  } else if (context === "marketing-video") {
    push("best-explainer-video-software-uk");
    push("best-email-marketing-tools-small-business-uk");
    push("best-website-builders-small-business-uk");
  } else if (context === "moving") {
    push("best-removal-van-services-uk");
    push("best-self-storage-services-uk-home-business");
    push("best-mattress-deals-uk");
  } else if (context === "storage") {
    push("best-self-storage-services-uk-home-business");
    push("best-removal-van-services-uk");
    push("best-parcel-courier-services-small-business-uk");
    push("how-to-choose-shipping-solution-online-business-uk");
  } else if (context === "wills") {
    push("best-online-will-writing-services-uk");
    push("best-self-storage-services-uk-home-business");
  } else if (context === "shipping") {
    push("best-parcel-courier-services-small-business-uk");
    push("how-to-choose-shipping-solution-online-business-uk");
    push("best-website-builders-small-business-uk");
  } else if (context === "iso") {
    push("best-iso-training-certification-courses-uk-businesses");
    push("what-iso-certification-means-small-business-uk");
    push("best-accounting-software-uk");
  } else if (context === "ai") {
    push("best-explainer-video-software-uk");
    push("best-email-marketing-tools-small-business-uk");
    push("best-domain-registrars-small-business-uk");
  } else if (context === "email-marketing") {
    push("best-email-marketing-tools-small-business-uk");
    push("best-website-builders-small-business-uk");
    push("best-domain-registrars-small-business-uk");
  } else if (pillar.includes("business")) {
    push("best-company-formation-services-uk");
    push("best-accounting-software-uk");
    push("best-email-marketing-tools-small-business-uk");
    push("best-domain-registrars-small-business-uk");
  } else if (pillar.includes("local")) {
    push("council-tax-bands-cheshire");
  }

  const out = [];
  for (const slug of want) {
    const g = bySlug.get(slug);
    if (g) out.push(g);
    if (out.length >= 3) break;
  }

  if (out.length < 3) {
    for (const g of list) {
      const slug = String(g?.slug || "").trim();
      if (!ALLOWED_PROMO_GUIDE_SLUGS.has(slug)) continue;
      if (!g?.category) continue;

      const cat = String(g.category).toLowerCase();
      const matchesPillar = pillar.includes("business")
        ? cat.includes("business")
        : pillar.includes("local")
          ? slug === "council-tax-bands-cheshire"
          : cat.includes(pillar);

      if (!matchesPillar) continue;
      if (out.some((x) => String(x?.slug) === slug)) continue;

      out.push(g);
      if (out.length >= 3) break;
    }
  }

  return out.slice(0, 3);
}

function getGuidePromoMeta(guide) {
  const slug = String(guide?.slug || "").trim();
  const href = slug ? `/guides/${encodeURIComponent(slug)}` : "";

  const pools = Object.values(monetisationTools || {}).filter(Array.isArray);
  for (const pool of pools) {
    const match = pool.find((item) => String(item?.href || "").trim() === href);
    if (match) {
      return {
        badge: match.badge || "Recommended deal",
        logoSrc: match.logoSrc || "",
        logoLabel: match.logoLabel || "",
        desc: match.desc || "",
        benefit: match.benefit || "",
        cta: match.cta || "View guide",
      };
    }
  }

  return {
    badge: String(guide?.monetisation || "").trim().toLowerCase() === "affiliate" ? "Recommended deal" : "Top guide",
    logoSrc: "",
    logoLabel: "CT",
    desc: "Practical comparisons and key checks for readers.",
    benefit: "Useful next step for readers",
    cta: "View guide",
  };
}

/* ===== AI Guide Promo Block (Monetisation Funnel) ===== */
const GuidePromoBlock = ({ guides = [], category, pillarLabel, contextToolType }) => {
  if (!FEATURES.ARTICLE_INLINE_GUIDES_ENABLED) return null;
  if (!Array.isArray(guides) || guides.length === 0) return null;

  const cat = String(category || "").toLowerCase();
  const ordered = pickGuidesForPillar(guides, pillarLabel || category, contextToolType);

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
              href={`/guides/${encodeURIComponent(g.slug)}`}
              className="block font-semibold text-sky-900 dark:text-slate-200 hover:underline underline-offset-2"
            >
              {safeText(g.title) || g.slug}
            </a>
            <div className="text-[11px] mt-1 text-slate-700 dark:text-gray-400">
              Updated: {String(g.updatedAt || g.createdAt || "").slice(0, 10)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const GuidesInlinePromo = ({ guides, pillarLabel, contextToolType, articleId, slot = 0, compact = false }) => {
  if (!FEATURES.ARTICLE_INLINE_GUIDES_ENABLED) return null;
  const list = Array.isArray(guides) ? guides : [];
  const picked = pickGuidesForPillar(list, pillarLabel, contextToolType);

  const fallbackOrder = [
    "best-self-storage-services-uk-home-business",
    "best-virtual-office-services-small-business-uk",
    "best-company-formation-services-uk",
    "best-explainer-video-software-uk",
    "best-accounting-software-uk",
    "best-email-marketing-tools-small-business-uk",
    "best-domain-registrars-small-business-uk",
  ];

  const monetisedPool = picked.filter(
    (item) => String(item?.slug || "").trim() !== "council-tax-bands-cheshire"
  );

  const fallbackPool = fallbackOrder
    .map((slug) => list.find((item) => String(item?.slug || "").trim() === slug))
    .filter(Boolean);

  const pool = monetisedPool.length > 0 ? monetisedPool : fallbackPool;

  const seed = `${String(articleId || "").trim()}-${slot}`;
  const hash = Array.from(seed).reduce((acc, ch) => ((acc * 31) + ch.charCodeAt(0)) >>> 0, 0);
  const g = pool.length > 0 ? pool[hash % pool.length] : null;

  if (!g) return null;

  const title = safeText(g?.title) || "In-depth Guide";
  const slug = String(g?.slug || "").trim();
  const href = slug ? `/guides/${encodeURIComponent(slug)}` : null;
  const promo = getGuidePromoMeta(g);
  const secondaryGuides = pool.filter((item) => String(item?.slug || "").trim() !== slug).slice(0, 2);
  const useLogoImage = Boolean(promo.logoSrc) && !/\.ico(?:\?|$)/i.test(String(promo.logoSrc));
  const logoLabel = promo.logoLabel || String(title).replace(/^best\s+/i, "").split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase() || "CT";

  return (
    <div className={compact
      ? "not-prose my-7 rounded-2xl border border-[#E6E1D8] dark:border-gray-800 bg-[#FBFAF7] dark:bg-gray-950/50 p-4 shadow-sm hover:shadow-md transition"
      : "mt-6 rounded-2xl border border-[#E6E1D8] dark:border-gray-800 bg-[#FBFAF7] dark:bg-gray-950/40 p-4 shadow-sm hover:shadow-md transition"
    }>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          <div className="h-11 w-11 rounded-2xl bg-white dark:bg-gray-900 border border-[#E6E1D8] dark:border-gray-800 flex items-center justify-center overflow-hidden shrink-0">
            {useLogoImage ? (
              <>
                <img
                  src={promo.logoSrc}
                  alt=""
                  className="h-full w-full object-contain p-1.5"
                  loading="lazy"
                  onError={(e) => {
                    e.currentTarget.style.display = "none";
                    e.currentTarget.nextElementSibling?.classList.remove("hidden");
                  }}
                />
                <span className="hidden text-sm font-black tracking-tight text-sky-900 dark:text-sky-100">
                  {logoLabel}
                </span>
              </>
            ) : (
              <span className="text-sm font-black tracking-tight text-sky-900 dark:text-sky-100">
                {logoLabel}
              </span>
            )}
          </div>

          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-1.5">
              <div className="text-[10px] uppercase tracking-wide px-2 py-1 rounded-full bg-slate-100 dark:bg-gray-800 text-slate-600 dark:text-gray-300 font-bold">
                {String(promo.badge || "").trim().toLowerCase() === "affiliate" ? "Recommended deal" : (promo.badge || (compact ? "Recommended guide" : "In-depth Guide"))}
              </div>
              <div className="text-[11px] font-semibold text-amber-600 dark:text-amber-400">
                ★ {Number(g?.sections?.find?.((x) => x?.type === "tool")?.rating || g?.rating || 4.5).toFixed(1)}
              </div>
            </div>

            <a href={href} className="block text-base font-black leading-tight text-sky-950 dark:text-slate-100 hover:underline underline-offset-2">
              {title}
            </a>

            <div className="text-[13px] mt-1.5 leading-snug text-slate-700 dark:text-gray-300">
              {promo.desc || "Practical comparisons and key checks for readers."}
            </div>

          </div>
        </div>

        <a
          href={href}
          className="shrink-0 hidden sm:inline-flex items-center justify-center rounded-lg bg-slate-900 dark:bg-sky-700 px-3 py-2 text-xs font-extrabold text-white hover:bg-sky-800 dark:hover:bg-sky-600 transition"
        >
          {promo.cta || "View guide"} →
        </a>
      </div>

            {compact && secondaryGuides.length > 0 && (
              <div className="mt-3">
                <div className="mb-1.5 text-[11px] font-extrabold uppercase tracking-wide text-slate-500 dark:text-gray-400">
                  Compare other options
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                {secondaryGuides.map((item) => {
                  const itemTitle = safeText(item?.title) || "Guide";
                  const itemSlug = String(item?.slug || "").trim();
                  const itemHref = itemSlug ? `/guides/${encodeURIComponent(itemSlug)}` : "#";
                  const itemPromo = getGuidePromoMeta(item);

                  return (
                    <a
                      key={itemSlug}
                      href={itemHref}
                      className="rounded-lg border border-[#E6E1D8] dark:border-gray-800 bg-white/80 dark:bg-gray-900/60 px-3 py-2 hover:border-sky-300 dark:hover:border-sky-700 transition"
                    >
                      <div className="text-[9px] uppercase tracking-wide font-bold text-slate-500 dark:text-gray-400">
                        Alternative
                      </div>
                      <div className="mt-0.5 text-[11px] font-black leading-snug text-slate-900 dark:text-white">
                        {itemTitle}
                      </div>
                      <div className="mt-0.5 text-[10px] leading-snug text-slate-600 dark:text-gray-300 truncate">
                        {itemPromo.desc || "Compare another option"}
                      </div>
                      <div className="mt-1 text-[10px] font-bold text-sky-800 dark:text-sky-300">
                        Compare →
                      </div>
                    </a>
                  );
                })}
                </div>
              </div>
            )}


      <div className="mt-3 rounded-lg bg-white/80 dark:bg-gray-900/70 border border-[#EEE8DC] dark:border-gray-800 px-2.5 py-2 text-[12px] font-semibold text-slate-800 dark:text-gray-200">
        ✓ {promo.benefit || "Useful next step for readers"}
      </div>

      <div className="mt-3 flex items-center justify-between gap-3">
        <div className="text-[11px] text-gray-500 dark:text-gray-400">
          We may earn a commission if you use affiliate links.
        </div>
        <a
          href={href}
          className="sm:hidden inline-flex items-center justify-center rounded-lg bg-slate-900 dark:bg-sky-700 px-3 py-2 text-xs font-extrabold text-white hover:bg-sky-800 dark:hover:bg-sky-600 transition"
        >
          {promo.cta || "View guide"} →
        </a>
      </div>
    </div>
  );
};

export default function ArticlePageV2({ categories }) {
  const { articleId } = useParams();
  const navigate = useNavigate();
  const [isMobileView, setIsMobileView] = useState(
    typeof window !== "undefined" ? window.innerWidth < 640 : false
  );
  // --- More stories (below article) ---
  const [moreStories, setMoreStories] = useState([]);
  const [moreStoriesOpen, setMoreStoriesOpen] = useState(false);

  const fmtShort = (dateString) => {
    const d = new Date(dateString);
    if (Number.isNaN(d.getTime())) return "";
    return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
  };

  useEffect(() => {
    const onResize = () => setIsMobileView(window.innerWidth < 640);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

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

        if (mounted) setMoreStories(filterEditorialPool(cleaned).sort((a, b) => Date.parse(b?.publishedDate || b?.created_at || 0) - Date.parse(a?.publishedDate || a?.created_at || 0)));
      } catch (_) {
        // ignore
      }
    }

    fetchMoreStories();
    return () => {
      mounted = false;
    };
  }, [articleId]);

  const cardsPerRow = isMobileView ? 2 : 3;
  const collapsedCount = isMobileView ? 4 : 6;
  const allMoreStoriesWithImages = moreStories.filter((a) => String(a?.image || "").trim());
  const allMoreStoriesWithoutImages = moreStories.filter((a) => !String(a?.image || "").trim());
  const visibleMoreStories = moreStoriesOpen
    ? moreStories.slice(0, 12)
    : moreStories.slice(0, collapsedCount);

  const moreStoriesWithImages = visibleMoreStories.filter((a) => String(a?.image || "").trim());
  const moreStoriesWithoutImages = visibleMoreStories.filter((a) => !String(a?.image || "").trim());
  const firstCardLimit = cardsPerRow * 2;
  const moreStoriesFirstCards = moreStoriesWithImages.slice(0, firstCardLimit);
  let moreStoriesRemainingCards = moreStoriesWithImages.slice(firstCardLimit);

  // Prevent orphan card rows (single card row)
  if (moreStoriesRemainingCards.length % cardsPerRow == 1) {
    const orphan = moreStoriesRemainingCards.pop();
    if (orphan) moreStoriesWithoutImages.unshift(orphan);
  }

  const [article, setArticle] = useState(null);
  const [guides, setGuides] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  const publicUrl =
    process.env.REACT_APP_PUBLIC_URL || (typeof window !== "undefined" ? window.location.origin : "");

  const description = useMemo(() => buildDescription(article), [article]);
  const safeTitle = useMemo(() => safeText(article?.title), [article]);
  const displayTitle = useMemo(() => {
    return safeText(article?.title).trim();
  }, [article]);


  const readingTime = useMemo(() => {
    const text = String(article?.content || "");
    const words = text.trim().split(/\s+/).length;
    return Math.max(1, Math.round(words / 200));
  }, [article]);


  // Pillar label for sidebar (keeps the publication feeling intentional)
  const pillarLabel = useMemo(() => {
    const pillar = getPrimaryPillar(article);
    return pillar === "UK" ? "Finance" : pillar;
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

  const { beforeGuideContent, afterGuideContent } = useMemo(() => {
    const text = String(mainContent || "").trim();
    if (!text) return { beforeGuideContent: "", afterGuideContent: "" };

    const paragraphs = text
      .split(/\n\s*\n+/)
      .map((p) => p.trim())
      .filter(Boolean);

    if (paragraphs.length < 4) {
      return { beforeGuideContent: text, afterGuideContent: "" };
    }

    const splitIndex = Math.max(2, Math.floor(paragraphs.length / 2));
    return {
      beforeGuideContent: paragraphs.slice(0, splitIndex).join("\n\n"),
      afterGuideContent: paragraphs.slice(splitIndex).join("\n\n"),
    };
  }, [mainContent]);


  // Contextual monetisation mapping: convert article metadata -> tool category
  // Hybrid approach: section-first (if present), then category, then keywords.
  const contextToolType = useMemo(() => {
    const sec = String(article?.section || "").toLowerCase();
    const cat = String(article?.category || "").toLowerCase();
    const title = String(article?.title || "").toLowerCase();
    const summary = String(article?.summary || "").toLowerCase();
    const text = `${sec} ${cat} ${title} ${summary}`.replace(/\s+/g, " ").trim();
    const hasMovingIntent = /\b(removal van|removals|moving house|house move|man and van|anyvan|relocation|furniture delivery|bed-in-a-box|mattress deals?)\b/.test(text);
    const hasCompanyFormationIntent = /\b(company formation|limited company|companies house|register a company|incorporate|incorporation|start a business|startup|start-up|sole trader)\b/.test(text);
    const hasMarketingVideoIntent = /\b(explainer video|whiteboard animation|marketing video|product demo|demo video|video marketing|animation software)\b/.test(text);

    if (hasMovingIntent) return "moving";
    if (hasCompanyFormationIntent) return "company-formation";
    if (hasMarketingVideoIntent) return "marketing-video";

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

    if (/\b(business bank|business account|merchant account|payment gateway|worldpay)\b/.test(text)) return "business-banking";
    if (/\b(accounting software|bookkeeping|xero|quickbooks|freeagent)\b/.test(text)) return "accounting";
    if (/\b(virtual office|business address|registered office|mail handling|mail forwarding)\b/.test(text)) return "virtual-office";
    if (/\b(web hosting|hosting provider|domain name|domain registration|website builder|website builders)\b/.test(text)) return "web-presence";
    if (/\b(self-storage|self storage|storage unit|storage units|storage facility|storage facilities|safestore)\b/.test(text)) return "storage";
    if (/\b(will writing|online will|make a will|probate|inheritance|estate planning|power of attorney)\b/.test(text)) return "wills";
    if (/\b(courier|parcel|shipping|delivery|fulfilment|fulfillment|multi-carrier)\b/.test(text)) return "shipping";
    if (/\b(iso 9001|iso 14001|iso 27001|iso certification|iso training|audit readiness)\b/.test(text) || (/\biso\b/.test(text) && /\b(certification|training|audit|compliance)\b/.test(text))) return "iso";
    if (/\b(mailchimp|email marketing|newsletter tool|newsletter tools|email automation|marketing automation|audience segmentation|campaign automation|email campaigns?)\b/.test(text)) return "email-marketing";

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
    let img = String(article?.image || "").trim();
    if (!img) return "";

    // Prefer larger social-share variant for Reach/Cheshire Live images
    if (img.includes("/ALTERNATES/s615/")) {
      img = img.replace("/ALTERNATES/s615/", "/ALTERNATES/s1200/");
    }

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
          {absoluteImageUrl && <link rel="preload" as="image" href={absoluteImageUrl} />}

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
              <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-foreground">{displayTitle || safeTitle}</h1>

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
                <div dangerouslySetInnerHTML={{ __html: autoLinkContent(beforeGuideContent || mainContent, pillarLabel) }} />

                {afterGuideContent && (
                  <>
                    <GuidesInlinePromo
                      guides={guides}
                      pillarLabel={pillarLabel}
                      contextToolType={contextToolType}
                      articleId={articleId}
                      slot={1}
                      compact
                    />

                    <div dangerouslySetInnerHTML={{ __html: autoLinkContent(afterGuideContent, pillarLabel) }} />
                  </>
                )}
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
                <GuidesInlinePromo guides={guides} pillarLabel={pillarLabel} contextToolType={contextToolType} articleId={articleId} />
                
              {/* GuidePromoBlock intentionally disabled for controlled non-Amazon rollout */}
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
                    {moreStoriesFirstCards.map((a, idx) => (
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

                  {moreStoriesWithoutImages.length > 0 && (
                    <TextHeadlineStrip
                      title="More headlines"
                      articles={moreStoriesWithoutImages.map((a) => ({
                        ...a,
                        publishedDate: a?.publishedDate || a?.published_at || a?.created_at,
                        url: a?.url || ("/article/" + (a?.id || a?._id || "")),
                      }))}
                    />
                  )}

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mt-3">
                    {moreStoriesRemainingCards.map((a, idx) => (
                      <div key={a?.id || a?._id || `remaining-${idx}`}>
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

                <div className="rounded-xl border border-amber-200/80 dark:border-amber-900/50 bg-amber-50/80 dark:bg-amber-950/20 p-4">
                  <div className="text-[11px] font-bold uppercase tracking-wide text-amber-700 dark:text-amber-300">
                    Local advertising
                  </div>
                  <h3 className="mt-2 text-base font-extrabold text-slate-900 dark:text-white">
                    Reach Cheshire readers from £49/month
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-slate-700 dark:text-slate-300">
                    Promote your local business with launch-price sponsored placements across Cheshire Today.
                  </p>
                  <button
                    type="button"
                    onClick={() => navigate("/advertise")}
                    className="mt-3 inline-flex w-full items-center justify-center rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-sm font-semibold px-4 py-2 transition"
                  >
                    View advertising options
                  </button>
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
