import React, { useState } from "react";
import { getApiUrl } from "../../utils/api";
import { trackEvent } from "../../utils/trackEvent";

export default function NewsletterFull() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState("idle"); // idle | loading | success | error

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!email) return;

    try {
      setStatus("loading");
      trackEvent("newsletter_submit", { placement: "homepage_full" });

      const res = await fetch(getApiUrl() + "/api/newsletter/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      if (!res.ok) throw new Error("bad_status");
      setStatus("success");
      setEmail("");
    } catch (err) {
      setStatus("error");
    } finally {
      setTimeout(() => setStatus("idle"), 4000);
    }
  };

  return (
    <section className="bg-gradient-to-r from-emerald-700 to-emerald-600 rounded-2xl p-8 shadow">
      <div className="max-w-3xl mx-auto text-center">
        <h3 className="text-3xl font-extrabold text-white">
          Stay informed across Cheshire
        </h3>
        <p className="mt-3 text-white/90 text-lg">
          The most important local stories — delivered every morning.
        </p>

        <form
          onSubmit={onSubmit}
          className="mt-6 flex flex-col sm:flex-row gap-3 justify-center"
        >
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
            className="w-full sm:w-96 px-5 py-3 rounded-full text-gray-900 focus:outline-none focus:ring-4 focus:ring-emerald-300"
          />
          <button
            type="submit"
            disabled={status === "loading"}
            className="px-8 py-3 rounded-full bg-white text-emerald-700 font-bold hover:bg-gray-100 disabled:opacity-60"
          >
            {status === "loading" ? "…" : "Subscribe free"}
          </button>
        </form>

        {status === "success" && (
          <p className="mt-4 text-white font-semibold">
            ✓ Thanks — you’re subscribed.
          </p>
        )}
        {status === "error" && (
          <p className="mt-4 text-red-200 font-semibold">
            Something went wrong — please try again.
          </p>
        )}

        <p className="mt-4 text-sm text-white/80">
          No spam. Unsubscribe anytime.
        </p>
      </div>
    </section>
  );
}
