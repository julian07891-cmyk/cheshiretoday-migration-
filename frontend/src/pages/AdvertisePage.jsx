import React from "react";
import { useNavigate } from "react-router-dom";
import { getApiUrl } from "../utils/api";
import { trackEvent } from "../utils/trackEvent";

const PRICING = [
  {
    name: "Local Starter",
    price: "£49 / month",
    badge: "Launch price for small local businesses",
    bullets: [
      "Rotating sponsored placement on article/sidebar areas",
      "Link to your website, booking page or Facebook page",
      "Basic monthly snapshot where available",
    ],
    subject: "Advertising enquiry — Local Starter package",
  },
  {
    name: "Local Featured",
    price: "£99 / month",
    badge: "Most popular launch package",
    bullets: [
      "Higher-frequency sponsored placement",
      "Featured mention on relevant local/category areas",
      "Monthly performance snapshot where available",
    ],
    subject: "Advertising enquiry — Local Featured package",
  },
  {
    name: "Local Partner",
    price: "£199 / month",
    badge: "Best for regular local exposure",
    bullets: [
      "Priority sponsored placement",
      "Homepage/category visibility where suitable",
      "One sponsored business spotlight per month",
    ],
    subject: "Advertising enquiry — Local Partner package",
  },
];

const AdvertisePage = () => {
  const navigate = useNavigate();
  const [showForm, setShowForm] = React.useState(false);
  const [selectedTier, setSelectedTier] = React.useState(null);

  const email = "news@cheshiretoday.co.uk";

  return (
    <div className="bg-gray-50 dark:bg-gray-900 min-h-screen">
      <div className="container mx-auto px-4 py-10 max-w-5xl">
        <button onClick={() => navigate("/")} className="text-sm text-emerald-600 hover:underline mb-4">← Back to Home</button>
        <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 dark:text-white">
          Advertise on Cheshire Today
        </h1>
        <p className="mt-3 text-gray-700 dark:text-gray-300 max-w-3xl">
          Launch pricing for Cheshire businesses: reach local readers with sponsored placements from £49/month. Choose a package below and we’ll recommend the best fit for your area and goals.
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
                Launch pricing. Packages can be paused, changed or cancelled monthly.
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

                  await fetch(getApiUrl() + "/api/leads/advertise", {
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
