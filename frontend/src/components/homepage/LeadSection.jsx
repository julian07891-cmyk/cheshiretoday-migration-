import React from "react";
import CompactArticleCard from "../CompactArticleCard";

/**
 * LeadSection
 * - One-column layout (one card per row)
 * - Mobile-friendly collapsed state: 4 items initially
 * - Optional badge styling via badgeClassName
 */
export default function LeadSection({
  title,
  badgeText,
  badgeClassName = "",
  items = [],
  onNavigate,
}) {
  const [expanded, setExpanded] = React.useState(false);

  if (!Array.isArray(items) || items.length === 0) return null;

  const badgeCls =
    badgeClassName ||
    "text-[10px] uppercase tracking-wide font-semibold px-2 py-1 rounded-full border border-slate-200 bg-slate-100 text-slate-700 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200";

  const norm = (a) => ({
    title: a?.title,
    content: a?.summary || a?.content || "",
    summary: a?.summary || "",
    image: a?.image,
    category: a?.category,
    location: a?.town || a?.location || "Cheshire",
    publishedDate: a?.publishedDate,
    readTime: a?.readTime || 3,
    url: a?.url || (a?.id || a?._id ? `/article/${a.id || a._id}` : "/"),
  });

  const visibleItems = expanded ? items : items.slice(0, 4);

  return (
    <section className="rounded-xl border border-slate-200/60 dark:border-gray-800 bg-white/70 dark:bg-transparent p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-base font-extrabold tracking-tight">{title}</h2>
        {badgeText ? <span className={badgeCls}>{badgeText}</span> : null}
      </div>

      <div className="space-y-3">
        {visibleItems.map((raw, i) => {
          const a = norm(raw);
          return (
            <CompactArticleCard
              key={raw?.id || raw?._id || i}
              onClick={() => onNavigate && onNavigate(a.url)}
              article={a}
            />
          );
        })}
      </div>

      {items.length > 4 && (
        <div className="mt-3 flex justify-end">
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="text-sm font-semibold hover:underline underline-offset-2"
          >
            {expanded ? "Show less" : "Show more"}
          </button>
        </div>
      )}
    </section>
  );
}
