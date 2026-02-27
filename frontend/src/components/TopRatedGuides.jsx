import React from "react";

export default function TopRatedGuides({ guides = [] }) {
  const list = Array.isArray(guides) ? guides : [];
  const top = list.slice(0, 3);
  if (!top.length) return null;

  return (
    <section className="mt-3">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-base font-extrabold tracking-tight text-slate-900 dark:text-white">
          Top Rated This Month
        </h2>
        <a
          href="/guides"
          className="text-sm font-semibold text-slate-700 dark:text-slate-200 hover:underline underline-offset-2"
        >
          View all →
        </a>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {top.map((g, idx) => (
          <a
            key={g?.slug || idx}
            href={`/guides/${encodeURIComponent(g.slug)}`}
            className="group rounded-xl border border-slate-200/50 dark:border-gray-800 bg-white/70 dark:bg-transparent p-3 hover:border-emerald-300 transition-colors"
          >
            <div className="text-[11px] font-semibold text-slate-500 dark:text-gray-400 mb-1">
              Guide
            </div>
            <div className="text-sm font-extrabold text-slate-900 dark:text-white group-hover:underline underline-offset-2">
              {g.title || g.slug}
            </div>
            <div className="text-xs text-slate-600 dark:text-gray-400 mt-1">
              Compare the best options →
            </div>
          </a>
        ))}
      </div>

      <div className="mt-1 text-[11px] text-slate-500 dark:text-gray-400">
        We may earn a commission from affiliate links.
      </div>
    </section>
  );
}
