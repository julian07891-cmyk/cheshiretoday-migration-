import React from "react";
import { Link } from "react-router-dom";
import { Clock, BookOpen } from "lucide-react";
import { buildArticleUrl } from "../../utils/articleUrl";

const safeText = (v) => (typeof v === "string" ? v : "");


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

export default function TopStoriesGrid({ stories = [] }) {
  if (!Array.isArray(stories) || stories.length === 0) return null;

  return (
    <div className="grid grid-cols-1 gap-3">
      {stories.slice(0, 8).map((story, idx) => {
        const href = story.url || buildArticleUrl(story);
        const title = safeText(story.title) || "Untitled";
        const summary =
          safeText(story.summary).trim() ||
          safeText(story.content).trim() ||
          "";
        const published = formatDate(story.publishedDate);
        const readTime = calculateReadTime(story.content || story.summary || "");

        return (
          <Link
            key={story.id || story.url || story.title || idx}
            to={href}
            className="group flex w-full gap-3 overflow-hidden rounded-xl border border-slate-200/50 dark:border-gray-800 bg-white/70 dark:bg-transparent p-5 min-h-[148px] hover:border-emerald-300 transition-colors"
          >
            {story.image ? (
              <div className="h-20 w-28 flex-none overflow-hidden rounded-md bg-slate-100 dark:bg-gray-800">
                <img
                  src={story.image}
                  alt={title}
                  className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                  loading="lazy"
                />
              </div>
            ) : (
              <div className="h-20 w-28 flex-none rounded-md bg-slate-100 dark:bg-gray-800" />
            )}

            <div className="min-w-0 flex-1">

              <h3 className="text-sm font-semibold text-slate-900 dark:text-white leading-snug line-clamp-3 group-hover:underline underline-offset-2">
                {title}
              </h3>

              {summary ? (
                <p className="mt-1 text-xs text-slate-600 dark:text-gray-400 line-clamp-1">
                  {summary}
                </p>
              ) : null}

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
            </div>
          </Link>
        );
      })}
    </div>
  );
}
