import React from "react";
import { Link } from "react-router-dom";

export default function LatestFeed({ stories = [] }) {
  if (!stories.length) return null;

  return (
    <section className="mt-6">
      <div className="flex items-baseline justify-between mb-3">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Latest
        </h2>
      </div>

      <div className="space-y-3">
        {stories.map((s) => (
          <Link
            key={s.id}
            to={s.url}
            className="block rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4 hover:shadow-sm transition"
          >
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
              {s.category} {s.town ? `• ${s.town}` : ""}
            </div>
            <div className="font-semibold text-gray-900 dark:text-gray-100 line-clamp-2">
              {s.title}
            </div>
            {s.summary ? (
              <div className="mt-1 text-sm text-gray-600 dark:text-gray-300 line-clamp-2">
                {s.summary}
              </div>
            ) : null}
          </Link>
        ))}
      </div>
    </section>
  );
}
