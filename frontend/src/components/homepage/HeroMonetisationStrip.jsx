import React, { useMemo } from "react";
import { FEATURES } from "../../config/features";
import { monetisationTools } from "../../config/monetisationTools";

export default function HeroMonetisationStrip() {
  if (!FEATURES.NON_AMAZON_MONETISATION_ENABLED) return null;

  // Choose 3 hero items that do NOT overlap with the Money Toolkit (mortgages/savings/council tax)
  const items = useMemo(() => {
    return [
      monetisationTools.credit[0],  // Credit cards
      monetisationTools.energy[1],  // Broadband
      monetisationTools.energy[0],  // Energy
    ].filter(Boolean);
  }, []);

  return (
    <div className="mt-4">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {items.map((it) => (
          <a
            key={it.href}
            href={it.href}
            className="rounded-xl border border-[#E6E1D8] dark:border-gray-800 bg-[#FBFAF7] dark:bg-transparent px-4 py-3 hover:bg-[#F2EEE6] dark:hover:bg-gray-900 transition group"
          >
            <div className="flex items-center justify-between">
              <div className="text-[11px] font-semibold text-slate-600 dark:text-gray-300">
                {it.badge || "Affiliate"}
              </div>
              <span className="text-[11px] px-2 py-1 rounded bg-gray-200 dark:bg-gray-800 text-slate-700 dark:text-gray-200">
                Deal
              </span>
            </div>

            <div className="mt-2 text-sm font-extrabold tracking-tight text-slate-900 dark:text-white">
              {it.title}
            </div>
            <div className="mt-1 text-sm text-sky-800 dark:text-slate-200 font-semibold group-hover:underline underline-offset-2">
              {it.desc}
            </div>
          </a>
        ))}
      </div>

      <div className="text-[11px] mt-2 text-gray-500">
        We may earn a commission if you use affiliate links.
      </div>
    </div>
  );
}
