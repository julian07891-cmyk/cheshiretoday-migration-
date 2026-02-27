import React from "react";
import { FEATURES } from "../../config/features";

/**
 * Editorial-style tools grid (affiliate-friendly without looking like ads).
 * Use this wherever you want "Money Toolkit" / "Financial Tools" blocks.
 */
export default function ToolsGrid({
  if (!FEATURES.NON_AMAZON_MONETISATION_ENABLED) return null;

  title = "Financial Tools & Comparisons",
  badge = "Tools",
  disclaimer = "We may earn a commission if you use links on this page.",
  items = [],
}) {
  if (!Array.isArray(items) || items.length === 0) return null;

  return (
    <div className="mb-5 rounded-lg border border-[#E6E1D8] dark:border-gray-800 bg-[#FBFAF7] dark:bg-transparent p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-extrabold tracking-tight">{title}</div>
        <span className="text-[11px] px-2 py-1 rounded bg-[#F2EEE6] dark:bg-gray-800 text-neutral-700 dark:text-gray-200">
          {badge}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
        {items.map((it) => (
          <a
            key={it.href}
            href={it.href}
            className="rounded-md border border-[#E6E1D8] dark:border-gray-800 px-3 py-2 hover:bg-[#F2EEE6] dark:hover:bg-gray-900 transition"
          >
            <div className="font-semibold text-sky-900 dark:text-slate-200 hover:underline underline-offset-2">
              {it.label}
            </div>
            {it.sub ? (
              <div className="text-xs text-neutral-600 dark:text-gray-400 mt-1">
                {it.sub}
              </div>
            ) : null}
          </a>
        ))}
      </div>

      <div className="text-[11px] mt-3 text-neutral-600 dark:text-gray-400">
        {disclaimer}
      </div>
    </div>
  );
}
