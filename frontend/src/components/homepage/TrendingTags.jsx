import React from "react";
import { Link } from "react-router-dom";

export default function TrendingTags({ tags = [] }) {
  if (!tags.length) return null;

  return (
    <section>
      <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-3">
        Trending
      </h2>

      <div className="flex flex-wrap gap-2">
        {tags.map((tag) => (
          <Link
            key={tag}
            to={`/topic/${encodeURIComponent(tag)}`}
            className="px-4 py-2 rounded-full bg-gray-100 dark:bg-gray-800 text-sm text-gray-800 dark:text-gray-200 hover:bg-emerald-600 hover:text-white transition"
          >
            #{tag}
          </Link>
        ))}
      </div>
    </section>
  );
}
