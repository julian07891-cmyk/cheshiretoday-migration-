import React, { useMemo } from "react";
import { FEATURES } from "../../config/features";
import { monetisationTools } from "../../config/monetisationTools";
import { trackEvent } from "../../utils/trackEvent";

function getInitials(title = "") {
  const words = String(title || "")
    .replace(/^best\s+/i, "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2);

  return words.map((word) => word[0]).join("").toUpperCase() || "CT";
}

function getDailyRotationOffset(key = "", total = 0) {
  if (!total) return 0;
  const now = new Date();
  const dayKey = `${now.getUTCFullYear()}-${now.getUTCMonth() + 1}-${now.getUTCDate()}`;
  const source = `${dayKey}:${key}`;
  let hash = 0;
  for (const ch of source) {
    hash = (hash * 31 + ch.charCodeAt(0)) % 2147483647;
  }
  return hash % total;
}

function getRotatedSlice(items = [], start = 0, limit = 0, key = "") {
  const clean = (items || []).filter(Boolean);
  if (!clean.length || limit <= 0) return [];

  const offset = getDailyRotationOffset(key, clean.length);
  const rotated = clean.map((_, idx) => clean[(offset + idx) % clean.length]);
  const count = Math.min(limit, rotated.length);

  return Array.from({ length: count }, (_, idx) => rotated[(start + idx) % rotated.length]).filter(
    (item, idx, arr) => arr.findIndex((x) => x?.href === item?.href) === idx
  );
}

export default function HeroMonetisationStrip({ start = 0, limit = 3, compact = false, className = "", eyebrow = "Useful next steps", title = "Guides and tools for readers", focus = "", excludeFocus = "" }) {
  if (!FEATURES.NON_AMAZON_MONETISATION_ENABLED) return null;

  const items = useMemo(() => {
    const isFinanceGuide = (item) =>
      /mortgage|savings|energy|tariff|bills|credit/i.test(`${item?.title || ""} ${item?.href || ""}`);

    let sourceItems = monetisationTools.homepage_primary || [];

    if (focus === "finance") {
      sourceItems = sourceItems.filter(isFinanceGuide);
    }

    if (excludeFocus === "finance") {
      sourceItems = sourceItems.filter((item) => !isFinanceGuide(item));
    }

    return getRotatedSlice(sourceItems, start, limit, `homepage_primary_${focus || "all"}_${excludeFocus || "none"}`);
  }, [start, limit, focus, excludeFocus]);

  if (!items.length) return null;

  const gridClass = compact
    ? "grid grid-cols-1 sm:grid-cols-2 gap-3"
    : "grid grid-cols-1 sm:grid-cols-3 gap-3";

  return (
    <section className={`${compact ? "mt-4" : "mt-5"} ${className}`} aria-label="Recommended guides and tools">
      <div className="mb-2">
        <div className="text-[11px] font-extrabold uppercase tracking-[0.18em] text-sky-800 dark:text-sky-300">
          {eyebrow}
        </div>
        <div className="text-sm font-black tracking-tight text-slate-950 dark:text-white">
          {title}
        </div>
      </div>
      <div className={gridClass}>
        {items.map((it) => {
          const title = it.title || "Recommended guide";
          const logoLabel = it.logoLabel || getInitials(title);
          const cta = it.cta || "View guide";

          return (
            <a
              key={it.href}
              href={it.href}
              onClick={() => trackEvent("guide_click", {
                placement: "homepage_monetisation_strip",
                title,
                href: it.href,
                start,
                compact: Boolean(compact),
              })}
              className="group relative rounded-2xl border border-[#E6E1D8] dark:border-gray-800 bg-[#FBFAF7] dark:bg-gray-950/40 p-3.5 shadow-sm hover:shadow-md hover:-translate-y-0.5 hover:border-sky-300 dark:hover:border-sky-700 transition-all duration-200"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="h-11 w-11 rounded-2xl bg-white dark:bg-gray-900 border border-[#E6E1D8] dark:border-gray-800 flex items-center justify-center overflow-hidden shrink-0">
                  {it.logoSrc ? (
                    <>
                      <img
                        src={it.logoSrc}
                        alt=""
                        className="h-full w-full object-contain p-1.5"
                        loading="lazy"
                        onError={(e) => {
                          e.currentTarget.style.display = "none";
                          e.currentTarget.nextElementSibling?.classList.remove("hidden");
                        }}
                      />
                      <span className="hidden text-sm font-black tracking-tight text-sky-900 dark:text-sky-100">
                        {logoLabel}
                      </span>
                    </>
                  ) : (
                    <span className="text-sm font-black tracking-tight text-sky-900 dark:text-sky-100">
                      {logoLabel}
                    </span>
                  )}
                </div>

                <span className="text-[10px] uppercase tracking-wide px-2 py-1 rounded-full bg-slate-100 dark:bg-gray-800 text-slate-600 dark:text-gray-300 font-bold">
                  {it.badge || "Affiliate"}
                </span>
              </div>

              <div className="mt-3">
                <div className="text-[15px] leading-tight font-black tracking-tight text-slate-950 dark:text-white group-hover:text-sky-900 dark:group-hover:text-sky-200">
                  {title}
                </div>

                <div className="mt-1.5 text-[13px] leading-snug text-slate-700 dark:text-gray-300">
                  {it.desc}
                </div>

                {it.benefit && (
                  <div className="mt-3 rounded-lg bg-white/80 dark:bg-gray-900/70 border border-[#EEE8DC] dark:border-gray-800 px-2.5 py-2 text-[12px] font-semibold text-slate-800 dark:text-gray-200">
                    ✓ {it.benefit}
                  </div>
                )}

                <div className="mt-3 flex items-center justify-between gap-2">
                  <span className="inline-flex items-center justify-center rounded-lg bg-slate-900 dark:bg-sky-700 px-3 py-1.5 text-[12px] font-extrabold text-white group-hover:bg-sky-800 dark:group-hover:bg-sky-600 transition">
                    {cta} →
                  </span>
                  <span className="text-[10px] text-gray-500 dark:text-gray-400">
                    Guide
                  </span>
                </div>
              </div>
            </a>
          );
        })}
      </div>

      <div className="text-[11px] mt-2 text-gray-500">
        We may earn a commission if you use affiliate links.
      </div>
    </section>
  );
}
