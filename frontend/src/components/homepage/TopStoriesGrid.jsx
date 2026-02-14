import React from "react";
import { Link } from "react-router-dom";

export default function TopStoriesGrid({ stories = [] }) {
  if (!stories.length) return null;

  return (
    <section className="mt-8">
      <h2 className="mb-4 text-lg font-bold text-gray-900 dark:text-white">
        Top Stories
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {stories.slice(0,4).map((story, idx) => (
          <Link
            key={story.id || story.url || story.title || idx}
            to={story.url || `/article/${story._id || story.id}` }
            className="group block overflow-hidden rounded-lg border border-gray-200 dark:border-gray-800"
          >
            {story.image && (
              <img
                src={story.image}
                alt={story.title}
                className="h-48 w-full object-cover"
              />
            )}

            <div className="p-4">
              <div className="mb-1 text-xs font-semibold text-amber-700 dark:text-amber-400">
                {story.category}
              </div>

              <h3 className="text-base font-semibold text-gray-900 dark:text-white group-hover:underline">
                {story.title}
              </h3>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
