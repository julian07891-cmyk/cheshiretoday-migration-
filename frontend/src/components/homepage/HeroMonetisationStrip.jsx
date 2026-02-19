import React from "react";

export default function HeroMonetisationStrip() {
  return (
    <div className="mt-4">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <a
          href="/guides/best-mortgage-rates-uk"
          className="rounded-xl border border-slate-200/50 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4 hover:border-emerald-300 transition-colors"
        >
          <div className="text-[11px] font-semibold text-slate-500 dark:text-gray-400 mb-1">Affiliate</div>
          <div className="text-sm font-extrabold text-slate-900 dark:text-white">Mortgage rates</div>
          <div className="text-xs text-slate-600 dark:text-gray-400 mt-1">Compare UK deals →</div>
        </a>

        <a
          href="/guides/best-credit-cards-uk"
          className="rounded-xl border border-slate-200/50 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4 hover:border-emerald-300 transition-colors"
        >
          <div className="text-[11px] font-semibold text-slate-500 dark:text-gray-400 mb-1">Affiliate</div>
          <div className="text-sm font-extrabold text-slate-900 dark:text-white">Credit cards</div>
          <div className="text-xs text-slate-600 dark:text-gray-400 mt-1">0% offers + rewards →</div>
        </a>

        <a
          href="/guides/best-savings-accounts-uk"
          className="rounded-xl border border-slate-200/50 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4 hover:border-emerald-300 transition-colors"
        >
          <div className="text-[11px] font-semibold text-slate-500 dark:text-gray-400 mb-1">Affiliate</div>
          <div className="text-sm font-extrabold text-slate-900 dark:text-white">Savings</div>
          <div className="text-xs text-slate-600 dark:text-gray-400 mt-1">Best easy-access picks →</div>
        </a>
      </div>

      <div className="mt-2 text-[11px] text-slate-500 dark:text-gray-400">
        We may earn a commission from affiliate links.
      </div>
    </div>
  );
}
