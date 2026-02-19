import React from "react";
import { Link } from "react-router-dom";

const safeText = (v) => (typeof v === "string" ? v : "");

export default function TopStoriesGrid({ stories = [] }) {
  if (!Array.isArray(stories) || stories.length === 0) return null;

  return (
    <div className="grid grid-cols-1 gap-3">
      {stories.slice(0, 7).map((story, idx) => {
        const href = story.url || `/article/${story._id || story.id}`;
        const title = safeText(story.title) || "Untitled";
        const category = safeText(story.category) || "";
        const summary =
          safeText(story.summary).trim() ||
          safeText(story.content).trim() ||
          "";

        return (
          <Link
            key={story.id || story.url || story.title || idx}
            to={href}
            className="group flex gap-3 overflow-hidden rounded-lg border border-slate-200/50 dark:border-gray-800 bg-white/70 dark:bg-transparent p-3 hover:border-emerald-300 transition-colors"
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
              {category ? (
                <div className="mb-1 text-[11px] font-semibold text-amber-700 dark:text-amber-400">
                  {category}
                </div>
              ) : null}

              <h3 className="text-sm font-semibold text-slate-900 dark:text-white leading-snug line-clamp-3 group-hover:underline underline-offset-2">
                {title}
              </h3>

              {summary ? (
                <p className="mt-1 text-xs text-slate-600 dark:text-gray-400 line-clamp-2">
                  {summary}
                </p>
              ) : null}
            </div>
          </Link>
        );
      })}
    </div>
  );
}
