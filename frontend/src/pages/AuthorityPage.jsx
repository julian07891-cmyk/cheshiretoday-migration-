import { Helmet } from "react-helmet-async";
import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getApiUrl } from "../utils/api";
import HomepageLayout from "../components/homepage/HomepageLayout";
import NewsFooter from "../components/NewsFooter";

function safeText(v) {
  if (v == null) return "";
  const t = typeof v;
  if (t === "string") return v;
  if (t === "number" || t === "boolean") return String(v);
  if (Array.isArray(v)) return v.map(safeText).filter(Boolean).join(" ");
  if (t === "object") {
    if (typeof v.text === "string") return v.text;
    if (typeof v.content === "string") return v.content;
    if (typeof v.title === "string") return v.title;
    if (typeof v.name === "string") return v.name;
    return "";
  }
  try {
    return String(v);
  } catch {
    return "";
  }
}


function getToolLogoSrc(name = "") {
  const cleaned = String(name || "").toLowerCase();

  if (cleaned.includes("123 reg")) return "/affiliate-logos/123-reg.png";
  if (cleaned.includes("quickbooks")) return "/affiliate-logos/quickbooks.png";
  if (cleaned.includes("mailchimp")) return "/affiliate-logos/mailchimp.ico";
  if (cleaned.includes("interparcel")) return "/affiliate-logos/interparcel.ico";
  if (cleaned.includes("safestore")) return "/affiliate-logos/safestore.ico";
  if (cleaned.includes("webhosting")) return "/affiliate-logos/webhosting-uk.ico";
  if (cleaned.includes("create")) return "/affiliate-logos/create.ico";
  if (cleaned.includes("virtual office")) return "/affiliate-logos/virtual-office.png";
  if (cleaned.includes("make a will")) return "/affiliate-logos/make-a-will-online.png";
  if (cleaned.includes("isoq")) return "/affiliate-logos/isoqar.png";

  return "";
}

function getToolInitials(name = "") {
  const cleaned = String(name || "").trim();

  if (/^123\s*reg/i.test(cleaned)) return "123";
  if (/quickbooks/i.test(cleaned)) return "QB";
  if (/mailchimp/i.test(cleaned)) return "MC";
  if (/interparcel/i.test(cleaned)) return "IP";
  if (/safestore/i.test(cleaned)) return "SS";
  if (/webhosting/i.test(cleaned)) return "WH";
  if (/create/i.test(cleaned)) return "CR";

  const words = cleaned
    .replace(/^best\s+/i, "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2);

  return words.map((word) => word[0]).join("").toUpperCase() || "CT";
}

function BestPickCta({ tools = [], monetisation = "affiliate" }) {
  const list = Array.isArray(tools) ? tools : [];
  const bestWithLink = list.find((t) => String(t?.affiliate_link || "").trim().length > 0);
  const best = bestWithLink || (list.length ? list[0] : null);
  if (!best) return null;

  const name = best?.name || "Recommended option";
  const rating = Number(best?.rating || 0);
  const link = String(best?.affiliate_link || "").trim();
  const why = String(best?.content || best?.title || "").trim();
  const initials = getToolInitials(name);
  const logoSrc = getToolLogoSrc(name);

  return (
    <div className="mt-7 rounded-3xl border border-emerald-200 dark:border-emerald-900/50 bg-emerald-50/80 dark:bg-emerald-950/20 p-4 md:p-5 shadow-md">
      <div className="rounded-2xl border border-emerald-200 dark:border-emerald-900/50 bg-white dark:bg-gray-950 overflow-hidden">
        <div className="grid grid-cols-1 md:grid-cols-[1fr_260px] gap-0">
          <div className="p-5 md:p-6">
            <div className="flex items-start gap-4">
              <div className="h-20 w-20 rounded-2xl border border-emerald-100 dark:border-gray-800 bg-white dark:bg-gray-900 flex items-center justify-center shrink-0 shadow-sm overflow-hidden">
                {logoSrc ? (
                  <>
                    <img
                      src={logoSrc}
                      alt=""
                      className="h-full w-full object-contain p-3"
                      loading="lazy"
                      onError={(e) => {
                        e.currentTarget.style.display = "none";
                        e.currentTarget.nextElementSibling?.classList.remove("hidden");
                      }}
                    />
                    <span className="hidden text-xl font-black tracking-tight text-sky-950 dark:text-sky-100">
                      {initials}
                    </span>
                  </>
                ) : (
                  <span className="text-xl font-black tracking-tight text-sky-950 dark:text-sky-100">
                    {initials}
                  </span>
                )}
              </div>

              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <span className="text-[11px] uppercase tracking-wide px-2.5 py-1 rounded-md bg-emerald-100 text-emerald-900 dark:bg-emerald-900/40 dark:text-emerald-100 font-black">
                    Our top pick
                  </span>
                  {rating > 0 && (
                    <span className="text-[12px] font-black text-slate-800 dark:text-gray-200">
                      {rating}/5 rating
                    </span>
                  )}
                </div>

                <div className="text-2xl md:text-3xl font-black tracking-tight text-slate-950 dark:text-white">
                  {name}
                </div>

                {why && (
                  <div className="mt-2 text-base text-slate-700 dark:text-gray-300 leading-relaxed max-w-2xl">
                    {why.length > 170 ? why.slice(0, 170) + "…" : why}
                  </div>
                )}

                <div className="mt-4 flex flex-wrap gap-2 text-[12px] font-bold text-slate-700 dark:text-gray-300">
                  <span className="rounded-full bg-slate-50 dark:bg-gray-900 border border-slate-200 dark:border-gray-800 px-3 py-1.5">✓ Easy to compare</span>
                  <span className="rounded-full bg-slate-50 dark:bg-gray-900 border border-slate-200 dark:border-gray-800 px-3 py-1.5">✓ UK-focused</span>
                  <span className="rounded-full bg-slate-50 dark:bg-gray-900 border border-slate-200 dark:border-gray-800 px-3 py-1.5">✓ Practical checks</span>
                </div>
              </div>
            </div>
          </div>

          <div className="border-t md:border-t-0 md:border-l border-emerald-100 dark:border-gray-800 bg-emerald-50/80 dark:bg-gray-900/60 p-5 md:p-6 flex flex-col justify-center">
            {link ? (
              <a
                href={link}
                target="_blank"
                rel="noreferrer"
                className="inline-flex w-full items-center justify-center rounded-xl bg-emerald-700 hover:bg-emerald-800 dark:bg-emerald-600 dark:hover:bg-emerald-500 text-white px-5 py-4 text-base font-black transition shadow-md"
              >
                Visit provider →
              </a>
            ) : (
              <span className="inline-flex w-full items-center justify-center rounded-xl bg-gray-200 dark:bg-gray-800 px-4 py-3.5 text-base font-black">
                Link pending
              </span>
            )}

            {monetisation === "affiliate" && (
              <div className="mt-3 text-[11px] text-slate-600 dark:text-gray-400 leading-relaxed text-center">
                Affiliate link. We may earn a commission.
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="mt-3 rounded-2xl border border-emerald-200 dark:border-emerald-900/50 bg-white dark:bg-gray-950/70 p-4 shadow-sm">
        <div className="flex items-start gap-3">
          <div className="h-8 w-8 rounded-full bg-emerald-100 dark:bg-emerald-900/50 flex items-center justify-center shrink-0">
            <span className="text-emerald-800 dark:text-emerald-100 font-black">✓</span>
          </div>
          <div>
            <div className="text-sm font-black text-slate-950 dark:text-white">
              Why we picked {name}
            </div>
            <div className="mt-1 text-sm text-slate-700 dark:text-gray-300 leading-relaxed">
              Strong fit for readers comparing practical UK options before choosing a provider.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


const RELATED_GUIDE_LIBRARY = [
  {
    slug: "best-web-hosting-small-business-uk",
    title: "Best web hosting",
    desc: "Hosting options for small-business websites",
    tag: "Web presence"
  },
  {
    slug: "best-website-builders-small-business-uk",
    title: "Best website builders",
    desc: "Create a professional site without coding",
    tag: "Website"
  },
  {
    slug: "best-domain-registrars-small-business-uk",
    title: "Best domain registrars",
    desc: "Register and manage your business domain",
    tag: "Domain"
  },
  {
    slug: "best-email-marketing-tools-small-business-uk",
    title: "Best email marketing tools",
    desc: "Grow subscribers and automate campaigns",
    tag: "Marketing"
  },
  {
    slug: "best-accounting-software-uk",
    title: "Best accounting software",
    desc: "VAT, invoices and reporting tools",
    tag: "Accounting"
  },
  {
    slug: "best-virtual-office-services-small-business-uk",
    title: "Best virtual office services",
    desc: "Business address and remote setup",
    tag: "Remote business"
  },
  {
    slug: "best-self-storage-services-uk-home-business",
    title: "Best self-storage services",
    desc: "Storage options for home and business",
    tag: "Storage"
  },
  {
    slug: "best-online-will-writing-services-uk",
    title: "Best online will writing services",
    desc: "Simple UK wills and estate planning checks",
    tag: "Finance"
  }
];

function getRelatedGuides(currentSlug = "", category = "") {
  const current = String(currentSlug || "").trim();
  const cat = String(category || "").toLowerCase();

  let preferred = [];

  if (current.includes("domain")) {
    preferred = [
      "best-web-hosting-small-business-uk",
      "best-website-builders-small-business-uk",
      "best-email-marketing-tools-small-business-uk",
      "best-virtual-office-services-small-business-uk",
    ];
  } else if (current.includes("website-builder") || current.includes("web-hosting")) {
    preferred = [
      "best-domain-registrars-small-business-uk",
      "best-email-marketing-tools-small-business-uk",
      "best-virtual-office-services-small-business-uk",
      "best-accounting-software-uk",
    ];
  } else if (current.includes("accounting")) {
    preferred = [
      "best-email-marketing-tools-small-business-uk",
      "best-domain-registrars-small-business-uk",
      "best-virtual-office-services-small-business-uk",
      "best-online-will-writing-services-uk",
    ];
  } else if (current.includes("storage")) {
    preferred = [
      "best-parcel-courier-services-small-business-uk",
      "how-to-choose-shipping-solution-online-business-uk",
      "best-website-builders-small-business-uk",
      "best-accounting-software-uk",
    ];
  } else if (current.includes("will")) {
    preferred = [
      "best-accounting-software-uk",
      "best-self-storage-services-uk-home-business",
      "best-domain-registrars-small-business-uk",
      "best-email-marketing-tools-small-business-uk",
    ];
  } else if (cat.includes("business") || cat.includes("finance")) {
    preferred = [
      "best-accounting-software-uk",
      "best-domain-registrars-small-business-uk",
      "best-website-builders-small-business-uk",
      "best-email-marketing-tools-small-business-uk",
    ];
  }

  const bySlug = new Map(RELATED_GUIDE_LIBRARY.map((g) => [g.slug, g]));
  const picked = preferred.map((s) => bySlug.get(s)).filter(Boolean);
  const fallback = RELATED_GUIDE_LIBRARY.filter((g) => g.slug !== current && !picked.some((p) => p.slug === g.slug));

  return [...picked, ...fallback].filter((g) => g.slug !== current).slice(0, 4);
}

function RelatedGuidesBlock({ currentSlug, category }) {
  const related = getRelatedGuides(currentSlug, category);
  if (!related.length) return null;

  return (
    <section className="mt-6 rounded-3xl border border-[#E6E1D8] dark:border-gray-800 bg-white dark:bg-gray-950 p-5 md:p-6 shadow-sm">
      <div className="flex items-end justify-between gap-4 mb-5">
        <div>
          <div className="text-[11px] uppercase tracking-wide font-black text-slate-500 dark:text-gray-400">
            Recommended next
          </div>
          <h2 className="mt-1 text-xl md:text-2xl font-black tracking-tight text-slate-950 dark:text-white">
            Related business guides
          </h2>
        </div>
        <div className="hidden sm:block text-xs text-slate-500 dark:text-gray-400">
          Continue comparing
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {related.map((g) => (
          <Link
            key={g.slug}
            to={`/guides/${g.slug}`}
            className="group rounded-2xl border border-[#E6E1D8] dark:border-gray-800 bg-[#FBFAF7] dark:bg-gray-900/50 p-4 hover:border-emerald-300 dark:hover:border-emerald-800 hover:shadow-sm transition"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-[11px] uppercase tracking-wide font-black text-emerald-700 dark:text-emerald-300">
                  {g.tag}
                </div>
                <div className="mt-1 text-base font-black text-slate-950 dark:text-white group-hover:underline underline-offset-2">
                  {g.title}
                </div>
                <div className="mt-1 text-sm text-slate-700 dark:text-gray-300 leading-relaxed">
                  {g.desc}
                </div>
              </div>
              <span className="shrink-0 rounded-xl bg-slate-950 dark:bg-emerald-700 text-white px-3 py-2 text-xs font-black">
                View →
              </span>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}


function QuickComparison({ tools = [] }) {
  const list = Array.isArray(tools) ? tools : [];
  const top = list.slice(0, 3);
  if (top.length < 2) return null;

  return (
    <div className="mt-6 rounded-3xl border border-slate-200/70 dark:border-gray-800 bg-white/80 dark:bg-gray-950/30 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="text-sm font-black tracking-tight text-slate-950 dark:text-white">
            Quick comparison
          </div>
          <div className="text-xs text-slate-500 dark:text-gray-400">
            Other options mentioned in this guide
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {top.map((t, idx) => {
          const name = t?.name || `Option ${idx + 1}`;
          const rating = Number(t?.rating || 0);
          const link = String(t?.affiliate_link || "").trim();
          const initials = getToolInitials(name);

          return (
            <div
              key={name + idx}
              className="rounded-2xl border border-slate-200/70 dark:border-gray-800 bg-[#FBFAF7] dark:bg-gray-950/40 p-4 hover:border-sky-300 dark:hover:border-sky-700 hover:shadow-sm transition"
            >
              <div className="flex items-start gap-3">
                <div className="h-10 w-10 rounded-xl bg-white dark:bg-gray-900 border border-[#E6E1D8] dark:border-gray-800 flex items-center justify-center shrink-0">
                  <span className="text-xs font-black text-sky-950 dark:text-sky-100">{initials}</span>
                </div>
                <div>
                  <div className="text-sm font-black text-slate-950 dark:text-white">
                    {name}
                  </div>
                  <div className="text-xs text-slate-600 dark:text-gray-300 mt-1">
                    {rating > 0 ? `${rating}/5 rating` : "Listed option"}
                  </div>
                </div>
              </div>

              <div className="mt-4">
                {link ? (
                  <a
                    href={link}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex w-full items-center justify-center rounded-lg bg-slate-900 hover:bg-sky-900 dark:bg-sky-700 dark:hover:bg-sky-600 text-white px-3 py-2 text-xs font-black transition"
                  >
                    Visit →
                  </a>
                ) : (
                  <span className="inline-flex w-full items-center justify-center rounded-lg bg-gray-200 dark:bg-gray-800 px-3 py-2 text-xs font-black">
                    Link pending
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}


export default function AuthorityPage() {
  const { slug } = useParams();
  const guideUrl = slug ? `https://cheshiretoday.co.uk/guides/${slug}` : "https://cheshiretoday.co.uk/guides";

  const [page, setPage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        setLoading(true);
        setErr("");

        const res = await fetch(`${getApiUrl()}/api/authority-pages/${encodeURIComponent(slug)}`);
        if (!res.ok) {
          const msg = `API ${res.status}`;
          throw new Error(msg);
        }

        const data = await res.json();
        if (mounted) setPage(data);
      } catch (e) {
        if (mounted) setErr(e?.message || "Failed to load guide");
      } finally {
        if (mounted) setLoading(false);
      }
    }

    if (slug) load();
    return () => {
      mounted = false;
    };
  }, [slug]);

  const title = page?.title || "Guide";
  const category = page?.category || "AI";
  const monetisation = page?.monetisation || "affiliate";
  const sections = Array.isArray(page?.sections) ? page.sections : [];

  const intro = sections.find((s) => s?.type === "intro")?.content || "";
  const tools = sections.filter((s) => s?.type === "tool" && String(s?.affiliate_link || "").trim());
  const contentSections = sections.filter((s) => s?.type === "content" || s?.type === "section");


  return (
    <div className="min-h-screen bg-neutral-50 text-slate-900 dark:bg-gray-900 dark:text-white">
      <HomepageLayout>
        <Helmet>
          <title>{title} | Cheshire Today</title>
          <meta name="description" content={intro ? intro.slice(0, 155) : "Cheshire Today guide"} />
          <link rel="canonical" href={guideUrl} />
          <meta property="og:title" content={`${title} | Cheshire Today`} />
          <meta property="og:description" content={intro ? intro.slice(0, 155) : "Cheshire Today guide"} />
          <meta property="og:url" content={guideUrl} />
          <meta property="og:type" content="article" />
          <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{
              __html: JSON.stringify({
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": title,
                "description": intro ? intro.slice(0, 155) : "Cheshire Today guide",
                "dateModified": page?.updatedAt || undefined,
                "author": { "@type": "Organization", "name": "Cheshire Today" },
                "publisher": {
                  "@type": "Organization",
                  "name": "Cheshire Today",
                  "logo": {
                    "@type": "ImageObject",
                    "url": "https://cheshiretoday.co.uk/logo.png"
                  }
                },
                "image": "https://cheshiretoday.co.uk/social-share.jpg",
                "mainEntityOfPage": {
                  "@type": "WebPage",
                  "@id": guideUrl
                }
              })
            }}
          />
        </Helmet>

        <div className="mx-auto w-full max-w-5xl px-4 sm:px-6 lg:px-8 py-8 md:py-12">
        <div className="mb-4">
          <Link to="/" className="text-sm text-emerald-700 dark:text-emerald-400 hover:underline">
            ← Back to Home
          </Link>
        </div>

        {loading && <div className="py-6">Loading…</div>}
        {!loading && err && <div className="py-6 text-red-600">{err}</div>}

        {!loading && !err && (
          <>
            <section className="rounded-3xl border border-[#E6E1D8] dark:border-gray-800 bg-white dark:bg-gray-950 shadow-sm overflow-hidden">
              <div className="p-5 md:p-8">
                <div className="flex flex-wrap items-center gap-2 mb-4">
                  <span className="text-[11px] uppercase tracking-wide px-3 py-1 rounded-full bg-slate-950 text-white dark:bg-sky-700 font-black">
                    Cheshire Today guide
                  </span>
                  <span className="text-xs px-2.5 py-1 rounded-full bg-[#FBFAF7] text-slate-700 dark:bg-gray-900 dark:text-gray-200 border border-[#E6E1D8] dark:border-gray-700 font-semibold">
                    {category}
                  </span>
                  <span className="text-xs px-2.5 py-1 rounded-full bg-[#FBFAF7] text-slate-700 dark:bg-gray-900 dark:text-gray-200 border border-[#E6E1D8] dark:border-gray-700 font-semibold">
                    {monetisation === "affiliate" ? "Affiliate supported" : monetisation}
                  </span>
                  {page?.status && (
                    <span className="text-xs px-2.5 py-1 rounded-full bg-[#FBFAF7] text-slate-700 dark:bg-gray-900 dark:text-gray-200 border border-[#E6E1D8] dark:border-gray-700 font-semibold">
                      {String(page.status).toUpperCase()}
                    </span>
                  )}
                </div>

                <h1 className="text-3xl md:text-5xl font-black tracking-tight text-slate-950 dark:text-white max-w-4xl">
                  {title}
                </h1>

                {intro && (
                  <div className="mt-5 rounded-2xl bg-[#FBFAF7] dark:bg-gray-900/70 border border-[#E6E1D8] dark:border-gray-800 p-4 md:p-5">
                    <p className="text-base md:text-lg text-slate-700 dark:text-gray-300 leading-relaxed max-w-4xl">
                      {intro}
                    </p>
                    <div className="mt-3 flex flex-wrap gap-2 text-[12px] text-slate-600 dark:text-gray-400">
                      <span className="font-semibold">Updated comparison guide</span>
                      <span>•</span>
                      <span>Links may earn commission at no extra cost to you</span>
                    </div>
                  </div>
                )}
              </div>
            </section>
            <BestPickCta tools={tools.slice(0,1)} monetisation={monetisation} />
            <QuickComparison tools={tools.slice(1)} />

            {contentSections.length > 0 && (
              <div className="mt-8 space-y-8">
                {contentSections.map((s, idx) => (
                  <section key={(s?.title || "section") + idx} className="rounded-xl border border-slate-200/60 dark:border-gray-800 bg-white/70 dark:bg-transparent p-6">
                    {s?.title && (
                      <h2 className="text-xl md:text-2xl font-extrabold tracking-tight text-slate-900 dark:text-white mb-3">
                        {s.title}
                      </h2>
                    )}
                    {s?.content && (
                      <p className="text-base text-slate-700 dark:text-gray-300 leading-relaxed">
                        {s.content}
                      </p>
                    )}
                  </section>
                ))}
              </div>
            )}




            {monetisation === "affiliate" && (
              <div className="mt-6 rounded-xl border border-amber-200/60 dark:border-amber-900/40 bg-amber-50/70 dark:bg-amber-900/10 p-5">
                <div className="text-sm font-semibold mb-1">Affiliate disclosure</div>
                <div className="text-sm text-slate-700 dark:text-gray-300 leading-relaxed">
                  Some links on this page may be affiliate links. If you use them, we may earn a commission at no extra cost to you.
                </div>
                <Link to="/affiliate-disclosure" className="inline-block mt-2 text-sm font-semibold text-blue-600 hover:underline">
                  Read full disclosure →
                </Link>
              </div>
            )}

            {tools.length > 0 && (
              <section className="mt-10 rounded-3xl border border-[#E6E1D8] dark:border-gray-800 bg-white dark:bg-gray-950 p-5 md:p-6 shadow-sm">
                <div className="flex items-end justify-between gap-4 mb-5">
                  <div>
                    <div className="text-[11px] uppercase tracking-wide font-black text-slate-500 dark:text-gray-400">
                      Provider list
                    </div>
                    <h2 className="mt-1 text-xl md:text-2xl font-black tracking-tight text-slate-950 dark:text-white">
                      Recommended tools
                    </h2>
                  </div>
                  <div className="hidden sm:block text-xs text-slate-500 dark:text-gray-400">
                    Compare before choosing
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {tools.map((t, idx) => {
                    const name = t?.name || `Tool ${idx + 1}`;
                    const rating = Number(t?.rating || 0);
                    const link = (t?.affiliate_link || "").trim();
                    const logoSrc = getToolLogoSrc(name);
                    const initials = getToolInitials(name);
                    const summary = String(t?.content || t?.title || "").trim();

                    return (
                      <div
                        key={name + idx}
                        className="rounded-2xl border border-[#E6E1D8] dark:border-gray-800 bg-[#FBFAF7] dark:bg-gray-900/50 p-4 hover:border-emerald-300 dark:hover:border-emerald-800 hover:shadow-sm transition"
                      >
                        <div className="flex items-start gap-3">
                          <div className="h-12 w-12 rounded-2xl border border-[#E6E1D8] dark:border-gray-800 bg-white dark:bg-gray-950 flex items-center justify-center shrink-0 overflow-hidden">
                            {logoSrc ? (
                              <>
                                <img
                                  src={logoSrc}
                                  alt=""
                                  className="h-full w-full object-contain p-2"
                                  loading="lazy"
                                  onError={(e) => {
                                    e.currentTarget.style.display = "none";
                                    e.currentTarget.nextElementSibling?.classList.remove("hidden");
                                  }}
                                />
                                <span className="hidden text-sm font-black tracking-tight text-sky-950 dark:text-sky-100">
                                  {initials}
                                </span>
                              </>
                            ) : (
                              <span className="text-sm font-black tracking-tight text-sky-950 dark:text-sky-100">
                                {initials}
                              </span>
                            )}
                          </div>

                          <div className="min-w-0 flex-1">
                            <div className="flex items-start justify-between gap-3">
                              <div>
                                <div className="text-base font-black text-slate-950 dark:text-white">
                                  {name}
                                </div>
                                <div className="text-xs font-bold text-emerald-700 dark:text-emerald-300 mt-1">
                                  {rating > 0 ? `${rating}/5 rating` : "Listed option"}
                                </div>
                              </div>
                            </div>

                            {summary && (
                              <div className="mt-2 text-sm text-slate-700 dark:text-gray-300 leading-relaxed">
                                {summary.length > 130 ? summary.slice(0, 130) + "…" : summary}
                              </div>
                            )}

                            <div className="mt-4">
                              {link ? (
                                <a
                                  href={link}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="inline-flex w-full sm:w-auto items-center justify-center rounded-xl bg-slate-950 hover:bg-emerald-800 dark:bg-emerald-700 dark:hover:bg-emerald-600 text-white px-4 py-2.5 text-sm font-black transition"
                                >
                                  Visit provider →
                                </a>
                              ) : (
                                <span className="inline-flex items-center justify-center rounded-xl bg-gray-200 dark:bg-gray-800 px-4 py-2.5 text-sm font-black">
                                  Link pending
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}

                  {tools.length < 2 && getRelatedGuides(slug, category).slice(0, 3).map((g) => (
                    <Link
                      key={`related-tool-${g.slug}`}
                      to={`/guides/${g.slug}`}
                      className="rounded-2xl border border-[#E6E1D8] dark:border-gray-800 bg-[#FBFAF7] dark:bg-gray-900/50 p-4 hover:border-emerald-300 dark:hover:border-emerald-800 hover:shadow-sm transition"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="text-[11px] uppercase tracking-wide font-black text-emerald-700 dark:text-emerald-300">
                            Related guide
                          </div>
                          <div className="mt-1 text-base font-black text-slate-950 dark:text-white">
                            {g.title}
                          </div>
                          <div className="mt-1 text-sm text-slate-700 dark:text-gray-300 leading-relaxed">
                            {g.desc}
                          </div>
                        </div>
                        <span className="shrink-0 rounded-xl bg-slate-950 dark:bg-emerald-700 text-white px-3 py-2 text-xs font-black">
                          View →
                        </span>
                      </div>
                    </Link>
                  ))}
                </div>
              </section>
            )}

            {tools.length > 1 && <RelatedGuidesBlock currentSlug={slug} category={category} />}

            {tools.length === 0 && (
              <div className="mt-6 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
                <div className="text-sm text-slate-700 dark:text-gray-300 leading-relaxed">
                  This guide is live, but tools are still being filled in.
                </div>
              </div>
            )}
          </>
        )}
        </div>

        <NewsFooter />
      </HomepageLayout>
    </div>
  );
}
