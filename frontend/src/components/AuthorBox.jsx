import React from "react";

const AuthorBox = ({ name = "Cheshire Today Editorial Team", bio, category = "AI & Finance" }) => {
  return (
    <div className="mt-10 border-t pt-6 border-gray-200 dark:border-gray-700">
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-5">
        <h3 className="text-sm uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
          About the author
        </h3>

        <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
          {name}
        </h4>

        <p className="mt-2 text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
          {bio ||
            `The Cheshire Today editorial team covers ${category}, local news and business stories across the region, with a focus on clarity, accuracy and reader-first reporting.`}
        </p>

        <div className="mt-3">
          <a
            href="/"
            className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:underline"
          >
            View more articles →
          </a>
        </div>
      </div>
    </div>
  );
};

export default AuthorBox;
