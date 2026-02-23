import React from "react";
import { monetisationTools } from "../../config/monetisationTools";

export default function ContextTools({ type }) {
  const tools = monetisationTools[type];

  if (!tools || tools.length === 0) return null;

  return (
    <div className="mt-6 mb-6 rounded-xl border border-[#E6E1D8] bg-[#FBFAF7] p-4 dark:border-gray-800 dark:bg-gray-900/30">
      <div className="text-sm font-bold mb-4 tracking-tight text-neutral-900 dark:text-white">
        Helpful tools
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {tools.slice(0, 3).map((tool, idx) => (
          <a
            key={idx}
            href={tool.href}
            className="rounded-lg border border-[#E6E1D8] bg-transparent px-3 py-2 hover:bg-[#F2EEE6] transition dark:border-gray-800 dark:hover:bg-gray-900/60"
          >
            <div className="text-xs font-semibold text-neutral-600 dark:text-slate-300">
              {tool.badge}
            </div>

            <div className="mt-2 text-sm font-bold text-neutral-900 dark:text-white">
              {tool.title}
            </div>

            <div className="mt-1 text-sm text-neutral-600 dark:text-slate-300">
              {tool.desc} →
            </div>
          </a>
        ))}
      </div>

      <div className="text-[11px] mt-4 text-neutral-500 dark:text-slate-400">
        We may earn a commission if you use affiliate links.
      </div>
    </div>
  );
}
