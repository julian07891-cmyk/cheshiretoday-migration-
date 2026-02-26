import React, { useMemo } from "react";

function norm(s) {
  return String(s || "").toLowerCase();
}

// pick 3 strongest commercial guides first, then fall back
function pickBest(guides) {
  const list = Array.isArray(guides) ? guides : [];
  const bySlug = (slug) => list.find((g) => String(g?.slug || "") === slug);

  const priority = [
    "best-business-bank-accounts-uk",
    "best-accounting-software-uk",
    "best-business-credit-cards-uk",
    "best-mortgage-rates-uk",
    "best-savings-accounts-uk",
    "best-credit-cards-uk",
    "best-isa-platforms-uk",
    "best-ai-tools-uk",
  ];

  const picked = [];
  for (const s of priority) {
    const g = bySlug(s);
    if (g && !picked.find((x) => x.slug === g.slug)) picked.push(g);
    if (picked.length >= 3) break;
  }

  if (picked.length < 3) {
    for (const g of list) {
      if (!g?.slug) continue;
      if (!picked.find((x) => x.slug === g.slug)) picked.push(g);
      if (picked.length >= 3) break;
    }
  }

  return picked.slice(0, 3);
}

export default function SidebarBestPicks({ guides = [] }) {
  const picks = useMemo(() => pickBest(guides), [guides]);
  if (!picks.length) return null;

  return (
    <section className="rounded-xl border border-emerald-200/60 dark:border-emerald-900/40 bg-emerald-50/60 dark:bg-emerald-900/10 p-4">
      <div className="flex items-center justify-between">
        <div className="text-sm font-extrabold text-slate-900 dark:text-white">Best picks</div>
        <a
          href="/guides"
          className="text-sm font-semibold text-slate-700 dark:text-slate-200 hover:underline underline-offset-2"
        >
          View →
        </a>
      </div>

      <div className="mt-3 space-y-2">
        {picks.map((g) => (
          <a
            key={g.slug}
            href={`/guides/${encodeURIComponent(g.slug)}`}
            className="block rounded-lg border border-slate-200/60 dark:border-gray-800 bg-white/70 dark:bg-transparent p-3 hover:border-emerald-300 transition-colors"
          >
            <div className="text-[11px] font-semibold text-slate-500 dark:text-gray-400">
              {norm(g.category) || "guide"}
            </div>
            <div className="mt-0.5 font-semibold text-slate-900 dark:text-white hover:underline underline-offset-2">
              {g.title || g.slug}
            </div>
            <div className="text-[11px] mt-1 text-slate-600 dark:text-gray-400">
              Compare options → 
            </div>
          </a>
        ))}
      </div>

      <div className="mt-3 text-[11px] text-slate-600 dark:text-gray-300">
        We may earn a commission from affiliate links.
      </div>
    </section>
  );
}
