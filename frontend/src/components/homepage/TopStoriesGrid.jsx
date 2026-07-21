import React from "react";
import { Link } from "react-router-dom";
import { Clock, BookOpen } from "lucide-react";
import { buildArticleUrl } from "../../utils/articleUrl";

const safeText = (value) => (typeof value === "string" ? value : "");

const formatDate = (dateString) => {
  if (!dateString) return "";

  const normalized =
    typeof dateString === "string" &&
    /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/.test(dateString)
      ? `${dateString}Z`
      : dateString;

  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return "";

  const now = new Date();
  const diffHours = Math.floor((now - date) / (1000 * 60 * 60));

  if (diffHours < 1) return "Just now";
  if (diffHours < 24) return `${diffHours}h ago`;

  return date.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
  });
};

const calculateReadTime = (content) => {
  if (!content) return 1;
  return Math.max(1, Math.ceil(String(content).split(/\s+/).length / 200));
};

export default function TopStoriesGrid({ stories = [] }) {
  if (!Array.isArray(stories) || stories.length === 0) return null;

  return (
    <div className="divide-y divide-slate-200 dark:divide-gray-800">
      {stories.slice(0, 4).map((story, index) => {
        const href = story.url || buildArticleUrl(story);
        const title = safeText(story.title) || "Untitled";
        const category =
          safeText(story.displayCategory).trim() ||
          safeText(story.category).trim() ||
          "Top story";
        const location = safeText(story.location).trim();
        const published = formatDate(story.publishedDate);
        const readTime = calculateReadTime(story.content || story.summary || "");

        return (
          <Link
            key={story.id || story._id || story.url || story.title || index}
            to={href}
            className="group grid grid-cols-[7rem_minmax(0,1fr)] gap-4 py-5 first:pt-1 last:pb-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1E3A8A] focus-visible:ring-offset-2 dark:focus-visible:ring-offset-gray-900"
          >
            <div className="aspect-[4/3] w-28 overflow-hidden rounded-lg bg-slate-100 dark:bg-gray-800">
              {story.image ? (
                <img
                  src={story.image}
                  alt={title}
                  className="h-full w-full object-cover transition-transform duration-300 ease-out group-hover:scale-[1.03]"
                  loading="lazy"
                  decoding="async"
                  width="224"
                  height="168"
                />
              ) : null}
            </div>

            <div className="min-w-0 self-center">
              <div className="mb-2 flex flex-wrap items-center gap-x-2 text-[10px] font-semibold uppercase tracking-[0.11em]">
                <span className="text-emerald-700 dark:text-emerald-400">
                  {category}
                </span>
                {location ? (
                  <>
                    <span
                      className="text-slate-300 dark:text-gray-600"
                      aria-hidden="true"
                    >
                      •
                    </span>
                    <span className="text-slate-500 dark:text-gray-400">
                      {location}
                    </span>
                  </>
                ) : null}
              </div>

              <h3 className="font-headline text-[1.05rem] font-semibold leading-[1.2] tracking-[-0.015em] text-slate-950 transition-colors group-hover:text-[#1E3A8A] dark:text-white dark:group-hover:text-blue-300">
                {title}
              </h3>

              <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-slate-500 dark:text-gray-400">
                {published ? (
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" aria-hidden="true" />
                    {published}
                  </span>
                ) : null}
                <span className="flex items-center gap-1">
                  <BookOpen className="h-3 w-3" aria-hidden="true" />
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
