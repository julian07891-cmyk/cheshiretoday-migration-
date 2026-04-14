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

  return (
    <div className="mt-7 overflow-hidden rounded-3xl border border-[#E6E1D8] dark:border-gray-800 bg-white dark:bg-gray-950 shadow-sm">
      <div className="grid grid-cols-1 md:grid-cols-[1fr_280px]">
        <div className="p-5 md:p-7">
          <div className="flex items-start gap-4">
            <div className="h-16 w-16 rounded-2xl border border-[#E6E1D8] dark:border-gray-800 bg-[#FBFAF7] dark:bg-gray-900 flex items-center justify-center shrink-0 shadow-sm">
              <span className="text-lg font-black tracking-tight text-sky-950 dark:text-sky-100">
                {initials}
              </span>
            </div>

            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <span className="text-[11px] uppercase tracking-wide px-2.5 py-1 rounded-full bg-sky-100 text-sky-900 dark:bg-sky-900/40 dark:text-sky-100 font-extrabold">
                  Featured pick
                </span>
                {rating > 0 && (
                  <span className="text-[11px] px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-200 font-bold">
                    {rating}/5 rating
                  </span>
                )}
              </div>

              <div className="text-xl md:text-2xl font-black tracking-tight text-slate-950 dark:text-white">
                {name}
              </div>

              {why && (
                <div className="mt-2 text-sm md:text-[15px] text-slate-700 dark:text-gray-300 leading-relaxed max-w-3xl">
                  {why.length > 230 ? why.slice(0, 230) + "…" : why}
                </div>
              )}

              <div className="mt-4 rounded-2xl bg-[#FBFAF7] dark:bg-gray-900 border border-[#E6E1D8] dark:border-gray-800 px-4 py-3">
                <div className="text-[12px] font-black uppercase tracking-wide text-slate-500 dark:text-gray-400">
                  Why we picked it
                </div>
                <div className="mt-1 text-sm font-semibold text-slate-800 dark:text-gray-200">
                  Strong fit for readers comparing practical UK options before choosing a provider.
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t md:border-t-0 md:border-l border-[#E6E1D8] dark:border-gray-800 bg-[#FBFAF7] dark:bg-gray-900/60 p-5 md:p-6 flex flex-col justify-center">
          {link ? (
            <a
              href={link}
              target="_blank"
              rel="noreferrer"
              className="inline-flex w-full items-center justify-center rounded-xl bg-slate-950 hover:bg-sky-900 dark:bg-sky-700 dark:hover:bg-sky-600 text-white px-4 py-3 text-sm font-black transition"
            >
              Visit provider →
            </a>
          ) : (
            <span className="inline-flex w-full items-center justify-center rounded-xl bg-gray-200 dark:bg-gray-800 px-4 py-3 text-sm font-black">
              Link pending
            </span>
          )}

          {monetisation === "affiliate" && (
            <div className="mt-3 text-[11px] text-slate-600 dark:text-gray-400 leading-relaxed text-center">
              We may earn a commission if you use this link, at no extra cost to you.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function QuickComparison({ tools = [] }) {
  const list = Array.isArray(tools) ? tools : [];
  const top = list.slice(0, 3);
  if (!top.length) return null;

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
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <span className="text-xs px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 dark:bg-gray-800 dark:text-gray-200 border border-slate-200/60 dark:border-gray-700">
                {category}
              </span>
              <span className="text-xs px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 dark:bg-gray-800 dark:text-gray-200 border border-slate-200/60 dark:border-gray-700">
                {monetisation === "affiliate" ? "Affiliate" : monetisation}
              </span>
              {page?.status && (
                <span className="text-xs px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 dark:bg-gray-800 dark:text-gray-200 border border-slate-200/60 dark:border-gray-700">
                  {String(page.status).toUpperCase()}
                </span>
              )}
            </div>

            <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white">
              {title}
            </h1>

            {intro && (
              <p className="mt-4 text-base md:text-lg text-slate-700 dark:text-gray-300 leading-relaxed max-w-4xl">
                {intro}
              </p>
            )}
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
              <div className="mt-10">
                <h2 className="text-lg font-extrabold tracking-tight text-slate-900 dark:text-white mb-4">
                  Recommended tools
                </h2>

                {tools.map((t, idx) => {
                  const name = t?.name || `Tool ${idx + 1}`;
                  const rating = Number(t?.rating || 0);
                  const link = (t?.affiliate_link || "").trim();

                  return (
                    <div
                      key={name + idx}
                      className="rounded-xl border border-slate-200/60 dark:border-gray-800 bg-white/70 dark:bg-transparent p-5 hover:bg-white transition"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="text-base md:text-lg font-semibold text-slate-900 dark:text-white">
                            {name}
                          </div>
                          <div className="text-sm text-slate-600 dark:text-gray-300 mt-1">
                            Rating: {rating > 0 ? `${rating}/5` : "—"}
                          </div>
                        </div>

                        {link ? (
                          <a
                            href={link}
                            target="_blank"
                            rel="noreferrer"
                            className="text-sm font-semibold text-emerald-700 dark:text-emerald-400 hover:underline whitespace-nowrap"
                          >
                            Visit →
                          </a>
                        ) : (
                          <span className="text-xs px-2 py-1 rounded bg-gray-200 dark:bg-gray-800 whitespace-nowrap">
                            Link pending
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

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
