import React from "react";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";

export default function ContactPage() {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 text-slate-900 dark:text-white">
      <Helmet>
        <title>Contact Cheshire Today</title>
        <meta name="description" content="Contact Cheshire Today for editorial enquiries, partnerships, corrections or advertising." />
      </Helmet>

      <div className="max-w-3xl mx-auto px-4 py-12">
        <div className="mb-6">
          <Link
            to="/"
            className="inline-flex items-center rounded-full border border-[#E6E1D8] dark:border-slate-700 px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
          >
            ← Back to Home
          </Link>
        </div>
        <h1 className="text-2xl font-extrabold mb-6">Contact Cheshire Today</h1>

        <div className="space-y-6 text-sm leading-relaxed">
          <section>
            <h2 className="font-semibold mb-2">Editorial Enquiries</h2>
            <p>Email: <a href="mailto:news@cheshiretoday.co.uk" className="text-emerald-600 dark:text-emerald-400 hover:underline">news@cheshiretoday.co.uk</a></p>
          </section>

          <section>
            <h2 className="font-semibold mb-2">Advertising & Partnerships</h2>
            <p>Email: <a href="mailto:news@cheshiretoday.co.uk" className="text-emerald-600 dark:text-emerald-400 hover:underline">news@cheshiretoday.co.uk</a></p>
          </section>

          <section>
            <h2 className="font-semibold mb-2">Corrections</h2>
            <p>If you believe an article contains inaccurate information, please contact us with full details and supporting evidence.</p>
          </section>

          <section>
            <h2 className="font-semibold mb-2">Business Information</h2>
            <p>Cheshire Today is a UK-based independent digital publication.</p>
          </section>
        </div>
      </div>
    </div>
  );
}
