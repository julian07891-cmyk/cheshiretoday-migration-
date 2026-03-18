import React from "react";
import { Link } from "react-router-dom";
import { Clock, BookOpen } from "lucide-react";
import { buildArticleUrl } from "../../utils/articleUrl";

const formatDate = (dateString) => {
  if (!dateString) return "";
  const normalized =
    typeof dateString === "string" && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/.test(dateString)
      ? `${dateString}Z`
      : dateString;
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return "";
  const now = new Date();
  const diffMs = now - date;
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  if (diffHours < 1) return "Just now";
  if (diffHours < 24) return `${diffHours}h ago`;
  return date.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
};

const calculateReadTime = (content) => {
  if (!content) return 1;
  const words = String(content).split(/\s+/).length;
  const minutes = Math.ceil(words / 200);
  return minutes < 1 ? 1 : minutes;
};

export default function TextHeadlineStrip({ title = "More headlines", articles = [] }) {
  if (!Array.isArray(articles) || articles.length === 0) return null;

  return (
    <div className="mt-4 rounded-xl border border-slate-200/60 dark:border-gray-800 bg-slate-50/80 dark:bg-gray-900/40 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-extrabold tracking-tight text-slate-900 dark:text-white">
          {title}
        </h3>
        <span className="text-[11px] text-slate-500 dark:text-gray-400">
          ({articles.length})
        </span>
      </div>

      <div className="grid grid-cols-1 gap-3">
        {articles.map((a, i) => {
          const href = a?.url || buildArticleUrl(a);
          const readTime = calculateReadTime(a?.content || a?.summary || "");
          const published = formatDate(a?.publishedDate);

          return (
            <Link
              key={a?.id || a?._id || i}
              to={href}
              className="group block rounded-lg border border-slate-200/70 dark:border-gray-800 bg-white dark:bg-gray-900 px-4 py-3 hover:border-emerald-300 dark:hover:border-emerald-500 transition-colors"
            >
              <div className="text-[11px] font-semibold uppercase tracking-wide text-sky-700 dark:text-sky-400 mb-1">
                {a?.category || "Story"}
              </div>
              <h4 className="text-sm font-semibold leading-snug text-slate-900 dark:text-white group-hover:underline underline-offset-2">
                {a?.title || "Untitled"}
              </h4>
              <div className="mt-2 flex items-center gap-3 text-[11px] text-slate-500 dark:text-gray-400">
                {published ? (
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {published}
                  </span>
                ) : null}
                <span className="flex items-center gap-1">
                  <BookOpen className="h-3 w-3" />
                  {readTime} min read
                </span>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
