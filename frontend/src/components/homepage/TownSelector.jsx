import React from "react";
import { Link } from "react-router-dom";

export default function TownSelector({ towns = [] }) {
  if (!towns.length) return null;

  return (
    <section>
      <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-3">
        Browse by Town
      </h2>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {towns.map((town) => (
          <Link
            key={town.slug}
            to={`/${town.slug}`}
            className="px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 text-sm text-gray-800 dark:text-gray-200 hover:bg-emerald-600 hover:text-white transition text-center"
          >
            {town.name}
          </Link>
        ))}
      </div>
    </section>
  );
}
