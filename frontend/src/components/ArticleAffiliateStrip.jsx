import React from "react";
import { FEATURES } from "../config/features";

const items = [
  {
    badge: "Affiliate",
    title: "Mobile SIM deals",
    desc: "Cheap UK monthly plans →",
    href: "/guides/best-sim-only-deals-uk",
  },
  {
    badge: "Affiliate",
    title: "Car insurance",
    desc: "Compare UK quotes →",
    href: "/guides/cheap-car-insurance-uk",
  },
  {
    badge: "Affiliate",
    title: "Travel insurance",
    desc: "Cover + best value →",
    href: "/guides/best-travel-insurance-uk",
  },
];

export default function ArticleAffiliateStrip() {
  if (!FEATURES.NON_AMAZON_MONETISATION_ENABLED) return null;

  return (
    <section className="mt-6">
      <div className="rounded-xl border border-gray-200/70 dark:border-gray-800 bg-white/80 dark:bg-transparent p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="text-sm font-bold">Recommended</div>
          <span className="text-[11px] px-2 py-1 rounded bg-gray-200 dark:bg-gray-800 text-slate-700 dark:text-gray-200">
            Affiliate
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {items.map((it) => (
            <a
              key={it.href}
              href={it.href}
              className="rounded-lg border border-gray-200/70 dark:border-gray-800 bg-white/60 dark:bg-transparent px-3 py-3 hover:bg-gray-50 dark:hover:bg-gray-900 transition"
            >
              <div className="text-[11px] font-semibold text-slate-600 dark:text-gray-300">
                {it.badge}
              </div>
              <div className="mt-1 text-sm font-extrabold tracking-tight text-slate-900 dark:text-white">
                {it.title}
              </div>
              <div className="mt-1 text-sm text-blue-700 dark:text-blue-300 font-semibold">
                {it.desc}
              </div>
            </a>
          ))}
        </div>

        <div className="text-[11px] mt-3 text-gray-500">
          We may earn a commission if you use affiliate links.
        </div>
      </div>
    </section>
  );
}
