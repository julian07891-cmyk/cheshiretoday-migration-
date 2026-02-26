import { Helmet } from "react-helmet-async";
import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getApiUrl } from "../utils/api";
import HomepageLayout from "../components/homepage/HomepageLayout";
import HomepageHeader from "../components/homepage/HomepageHeader";
import NewsFooter from "../components/NewsFooter";


function BestPickCta({ tools = [], monetisation = "affiliate" }) {
  const list = Array.isArray(tools) ? tools : [];
  const bestWithLink = list.find((t) => String(t?.affiliate_link || "").trim().length > 0);
  const best = bestWithLink || (list.length ? list[0] : null);
  if (!best) return null;

  const name = best?.name || "Recommended option";
  const rating = Number(best?.rating || 0);
  const link = String(best?.affiliate_link || "").trim();
  const why = String(best?.content || best?.title || "").trim();

  return (
    <div className="mt-6 rounded-xl border border-emerald-200/60 dark:border-emerald-900/40 bg-emerald-50/60 dark:bg-emerald-900/10 p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-xs font-semibold text-emerald-900/80 dark:text-emerald-200 mb-1">
            Best pick
          </div>
          <div className="text-base md:text-lg font-extrabold text-slate-900 dark:text-white">
            {name}
          </div>
          <div className="text-sm text-slate-700 dark:text-gray-300 mt-1">
            Rating: {rating > 0 ? `${rating}/5` : "—"}
          </div>

          {why && (
            <div className="text-sm text-slate-700 dark:text-gray-300 mt-2 leading-relaxed max-w-3xl">
              {why.length > 180 ? why.slice(0, 180) + "…" : why}
            </div>
          )}
        </div>

        <div className="shrink-0">
          {link ? (
            <a
              href={link}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white px-4 py-2 text-sm font-semibold"
            >
              Compare now →
            </a>
          ) : (
            <span className="inline-flex items-center justify-center rounded-lg bg-gray-200 dark:bg-gray-800 px-4 py-2 text-sm font-semibold">
              Link pending
            </span>
          )}
          {monetisation === "affiliate" && (
            <div className="mt-2 text-[11px] text-slate-600 dark:text-gray-400">
              We may earn a commission.
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
    <div className="mt-6 rounded-xl border border-slate-200/60 dark:border-gray-800 bg-white/70 dark:bg-transparent p-5">
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-extrabold tracking-tight text-slate-900 dark:text-white">
          Quick comparison
        </div>
        <div className="text-[11px] text-slate-500 dark:text-gray-400">
          Top picks (summary)
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {top.map((t, idx) => {
          const name = t?.name || `Option ${idx + 1}`;
          const rating = Number(t?.rating || 0);
          const link = String(t?.affiliate_link || "").trim();

          return (
            <div
              key={name + idx}
              className="rounded-xl border border-slate-200/60 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4"
            >
              <div className="text-sm font-extrabold text-slate-900 dark:text-white">
                {name}
              </div>
              <div className="text-xs text-slate-600 dark:text-gray-300 mt-1">
                Rating: {rating > 0 ? `${rating}/5` : "—"}
              </div>

              <div className="mt-3">
                {link ? (
                  <a
                    href={link}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center justify-center rounded-lg bg-slate-900 hover:bg-slate-800 text-white px-3 py-2 text-xs font-semibold"
                  >
                    Visit →
                  </a>
                ) : (
                  <span className="inline-flex items-center justify-center rounded-lg bg-gray-200 dark:bg-gray-800 px-3 py-2 text-xs font-semibold">
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
  const tools = sections.filter((s) => s?.type === "tool");

  return (
    <div className="min-h-screen bg-neutral-50 text-slate-900 dark:bg-gray-900 dark:text-white">
      <HomepageLayout>
        <Helmet>
          <title>{title} | Cheshire Today</title>
          <meta name="description" content={intro ? intro.slice(0, 155) : "Cheshire Today guide"} />
          <link rel="canonical" href={`https://cheshiretoday.co.uk/guides/${slug}`} />
          <meta property="og:title" content={`${title} | Cheshire Today`} />
          <meta property="og:description" content={intro ? intro.slice(0, 155) : "Cheshire Today guide"} />
          <meta property="og:url" content={`https://cheshiretoday.co.uk/guides/${slug}`} />
          <meta property="og:type" content="article" />
        </Helmet>
        <HomepageHeader breakingStories={[]} />

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
            <BestPickCta tools={tools} monetisation={monetisation} />
            <QuickComparison tools={tools} />



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
