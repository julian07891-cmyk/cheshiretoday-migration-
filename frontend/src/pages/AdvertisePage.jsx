import React from "react";
import { trackEvent } from "../utils/trackEvent";

const PRICING = [
  {
    name: "Starter",
    price: "£149 / month",
    badge: "Best for local businesses",
    bullets: [
      "Sidebar sponsored block (rotating)",
      "Monthly performance snapshot (clicks + impressions)",
      "Link to your website or booking page",
    ],
    subject: "Advertising enquiry — Starter package",
  },
  {
    name: "Featured",
    price: "£299 / month",
    badge: "Most popular",
    bullets: [
      "Priority sidebar placement (higher frequency)",
      "Homepage section mention (weekly)",
      "Monthly performance snapshot (clicks + impressions)",
    ],
    subject: "Advertising enquiry — Featured package",
  },
  {
    name: "Premium",
    price: "£499 / month",
    badge: "Max exposure",
    bullets: [
      "Top-tier sidebar placement (highest frequency)",
      "Homepage + category featured placement (weekly)",
      "1 sponsored article / month (editorial-style)",
    ],
    subject: "Advertising enquiry — Premium package",
  },
];

const AdvertisePage = () => {
  const [showForm, setShowForm] = React.useState(false);
  const [selectedTier, setSelectedTier] = React.useState(null);

  const email = "advertise@cheshiretoday.co.uk";

  return (
    <div className="bg-gray-50 dark:bg-gray-900 min-h-screen">
      <div className="container mx-auto px-4 py-10 max-w-5xl">
        <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 dark:text-white">
          Advertise on Cheshire Today
        </h1>
        <p className="mt-3 text-gray-700 dark:text-gray-300 max-w-3xl">
          Reach local readers across Cheshire with sponsored placements. Choose a package below and we’ll set it up within 24–48 hours.
        </p>

        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6 items-stretch">
          {PRICING.map((tier) => (
            <div
              key={tier.name}
              className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 shadow flex flex-col"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                    {tier.name}
                  </h2>
                  <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                    {tier.badge}
                  </p>
                </div>
                <span className="text-sm font-semibold text-amber-700 bg-amber-100 dark:bg-amber-900/30 dark:text-amber-300 px-3 py-1 rounded-full">
                  {tier.price}
                </span>
              </div>

              <ul className="mt-5 space-y-2 text-gray-700 dark:text-gray-300 list-disc list-inside">
                {tier.bullets.map((b) => (
                  <li key={b}>{b}</li>
                ))}
              </ul>

              <button
  type="button"
  className="mt-auto inline-flex w-full items-center justify-center rounded-lg bg-amber-600 hover:bg-amber-700 text-white font-semibold py-3 transition"
  onClick={() => {
    setSelectedTier(tier);
    setShowForm(true);
  }}
>
  Enquire about {tier.name}
</button>
              <p className="mt-3 text-xs text-gray-500 dark:text-gray-400">
                Prices exclude VAT (if applicable). Packages can be paused or changed monthly.
              </p>
            </div>
          ))}
        </div>

        {showForm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 w-full max-w-lg border border-gray-200 dark:border-gray-700 shadow-xl">
              <div className="flex items-start justify-between gap-4">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                  Enquire about {selectedTier?.name}
                </h3>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="text-gray-500 hover:text-gray-800 dark:hover:text-white"
                  aria-label="Close"
                >
                  ✕
                </button>
              </div>

              <form
                className="mt-4 space-y-3"
                onSubmit={async (e) => {
                  e.preventDefault();
                  const form = e.target;

                  const payload = {
                    name: form.name.value,
                    business: form.business.value,
                    email: form.email.value,
                    budget: form.budget.value,
                    message: form.message.value,
                    tier: selectedTier?.name,
                    source: "advertise_page",
                  };

                  await fetch("/api/leads/advertise", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                  });

                  trackEvent("lead_submit", { tier: selectedTier?.name });
                  setShowForm(false);
                }}
              >
                <input name="name" required placeholder="Your name" className="w-full p-3 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800" />
                <input name="business" placeholder="Business name" className="w-full p-3 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800" />
                <input name="email" type="email" required placeholder="Email" className="w-full p-3 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800" />
                <select name="budget" className="w-full p-3 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800">
                  <option value="">Estimated budget</option>
                  <option>£100–£300</option>
                  <option>£300–£600</option>
                  <option>£600+</option>
                </select>
                <textarea name="message" placeholder="Tell us about your goals" className="w-full p-3 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800" />

                <div className="flex gap-3 pt-2">
                  <button type="submit" className="flex-1 bg-amber-600 hover:bg-amber-700 text-white rounded-lg py-3 font-semibold">
                    Send enquiry
                  </button>
                  <button type="button" onClick={() => setShowForm(false)} className="flex-1 border border-gray-300 dark:border-gray-700 rounded-lg py-3">
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        <div className="mt-10 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 shadow max-w-3xl">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">
            Not sure which package fits?
          </h3>
          <p className="mt-2 text-gray-700 dark:text-gray-300">
            Tell us your goal (bookings, calls, footfall, brand awareness) and your target area (e.g. Crewe, Chester, Warrington). We’ll recommend the best placement mix.
          </p>
          <p className="mt-4 text-gray-700 dark:text-gray-300">
            Email us at:
          </p>
          <p className="mt-1 font-semibold text-amber-600">
            {email}
          </p>
        </div>
      </div>
    </div>
  );
};

export default AdvertisePage;
