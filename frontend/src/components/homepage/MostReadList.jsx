import React from "react";
import { Link } from "react-router-dom";

export default function MostReadList({ stories = [] }) {
  return (
    <section>
      <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
        Most Read
      </h2>

      <ol className="space-y-3">
        {stories.slice(0, 5).map((story, index) => (
          <li key={story.id}>
            <Link
              to={story.url || "#"}
              className="flex items-start gap-3 group"
            >
              <span className="text-2xl font-extrabold text-gray-300 group-hover:text-emerald-500">
                {index + 1}
              </span>
              <span className="text-sm text-gray-800 dark:text-gray-200 group-hover:underline line-clamp-2">
                {story.title}
              </span>
            </Link>
          </li>
        ))}
      </ol>
    </section>
  );
}
