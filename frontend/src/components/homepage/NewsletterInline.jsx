import React from "react";

export default function NewsletterInline() {
  return (
    <section className="my-8 p-4 border border-gray-200 rounded-lg bg-white dark:bg-gray-800">
      <h3 className="font-semibold text-lg mb-2">
        Get local Cheshire news straight to your inbox
      </h3>
      <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
        Sign up for daily headlines and breaking updates.
      </p>
      <form className="flex gap-2">
        <input
          type="email"
          placeholder="Your email"
          className="flex-1 px-3 py-2 border rounded"
        />
        <button
          type="submit"
          className="px-4 py-2 bg-emerald-600 text-white rounded"
        >
          Subscribe
        </button>
      </form>
    </section>
  );
}
