import React from "react";
import { Link } from "react-router-dom";

export default function CookiePolicy() {
  return (
    <div className="min-h-screen bg-neutral-50 text-slate-900 dark:bg-gray-900 dark:text-white">
      <div className="container mx-auto px-4 py-10 max-w-4xl">
        <h1 className="text-3xl font-extrabold tracking-tight">Cookie Policy</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-gray-300">
          Last updated: {new Date().toLocaleDateString("en-GB")}
        </p>

        <div className="prose prose-slate dark:prose-invert max-w-none mt-6">
          <p>
            This Cookie Policy explains how Cheshire Today uses cookies and similar technologies when you visit our website.
          </p>

          <h2>What are cookies?</h2>
          <p>
            Cookies are small text files stored on your device. They help websites work efficiently, improve user experience,
            and provide information to website owners.
          </p>

          <h2>How we use cookies</h2>
          <ul>
            <li><strong>Essential cookies</strong>: Needed for the site to function (security, basic preferences).</li>
            <li><strong>Analytics cookies</strong>: Help us understand site usage (e.g., page views, traffic sources).</li>
            <li><strong>Affiliate/advertising cookies</strong>: Used to measure referral performance and conversions where applicable.</li>
          </ul>

          <h2>Analytics</h2>
          <p>
            We use analytics tools (for example, Google Analytics) to understand how visitors use the site and to improve performance.
            These tools may set cookies to collect aggregated usage information.
          </p>

          <h2>Affiliate links</h2>
          <p>
            Some pages contain affiliate links. If you click an affiliate link, the merchant may set cookies to track that referral.
            We may earn a commission if you make a purchase — at no extra cost to you.
          </p>

          <h2>Managing cookies</h2>
          <p>
            You can control and delete cookies in your browser settings. Most browsers allow you to:
          </p>
          <ul>
            <li>See what cookies are stored</li>
            <li>Delete cookies</li>
            <li>Block cookies entirely</li>
            <li>Block third-party cookies</li>
          </ul>
          <p>
            If you block some cookies, parts of the site may not function properly.
          </p>

          <h2>Contact</h2>
          <p>
            If you have questions about this Cookie Policy, contact us via the{" "}
            <Link to="/contact" className="font-semibold underline underline-offset-2">
              Contact page
            </Link>.
          </p>

          <hr />

          <p className="text-sm text-slate-600 dark:text-gray-300">
            See also:{" "}
            <Link to="/privacy" className="font-semibold underline underline-offset-2">Privacy Policy</Link>{" "}
            and{" "}
            <Link to="/affiliate-disclosure" className="font-semibold underline underline-offset-2">Affiliate Disclosure</Link>.
          </p>
        </div>
      </div>
    </div>
  );
}
