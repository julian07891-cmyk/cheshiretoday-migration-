import React from "react";

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

        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          {PRICING.map((tier) => (
            <div
              key={tier.name}
              className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 shadow"
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

              <a
                className="mt-6 inline-flex w-full items-center justify-center rounded-lg bg-amber-600 hover:bg-amber-700 text-white font-semibold py-3 transition"
                href={`mailto:${email}?subject=${encodeURIComponent(
                  tier.subject
                )}`}
              >
                Enquire about {tier.name}
              </a>

              <p className="mt-3 text-xs text-gray-500 dark:text-gray-400">
                Prices exclude VAT (if applicable). Packages can be paused or changed monthly.
              </p>
            </div>
          ))}
        </div>

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
