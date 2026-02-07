import React, { useState } from "react";

export default function NewsletterInline() {
  const [email, setEmail] = useState("");

  return (
    <section className="mt-8 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-5">
      <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
        Get the latest headlines
      </h3>
      <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
        One email. No spam. Unsubscribe anytime.
      </p>

      <form
        className="mt-4 flex flex-col sm:flex-row gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          alert("Subscribed (placeholder)");
          setEmail("");
        }}
      >
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-950 px-3 py-2 text-sm text-gray-900 dark:text-gray-100"
        />
        <button
          type="submit"
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
        >
          Subscribe
        </button>
      </form>
    </section>
  );
}
