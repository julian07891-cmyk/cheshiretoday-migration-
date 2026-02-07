import React from "react";
import { Link } from "react-router-dom";

const SponsoredSidebarBlock = () => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-amber-200 dark:border-amber-700">
      <div className="text-xs uppercase tracking-wide text-amber-600 font-semibold mb-2">
        Sponsored
      </div>

      <Link
        to="/advertise"
        className="block hover:opacity-90 transition"
      >
        <h3 className="font-bold text-gray-900 dark:text-white mb-1">
          Promote Your Business Here
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-300">
          Reach local Cheshire readers daily. Affordable sponsorships available.
        </p>
        <p className="mt-2 text-sm font-semibold text-amber-600">
          Enquire today →
        </p>
      </Link>
    </div>
  );
};

export default SponsoredSidebarBlock;
