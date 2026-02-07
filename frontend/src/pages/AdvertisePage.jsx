import React from "react";

const AdvertisePage = () => {
  return (
    <div className="bg-gray-50 dark:bg-gray-900 min-h-screen">
      <div className="container mx-auto px-4 py-10 max-w-3xl">
        <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white">
          Advertise on Cheshire Today
        </h1>
        <p className="mt-3 text-gray-700 dark:text-gray-300">
          Reach local readers across Cheshire with sponsored placements
        </p>

        <div className="mt-8 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 shadow">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Sponsorship options
          </h2>

          <ul className="mt-4 space-y-3 text-gray-700 dark:text-gray-300 list-disc list-inside">
            <li>Homepage sidebar sponsored block</li>
            <li>Category page featured placement</li>
            <li>Sponsored articles &amp; announcements</li>
            <li>Local business promotions</li>
          </ul>

          <p className="mt-6 text-gray-700 dark:text-gray-300">
            To advertise, please email:
          </p>

          <p className="mt-2 font-semibold text-amber-600">
            advertise@cheshiretoday.co.uk
          </p>
        </div>
      </div>
    </div>
  );
};

export default AdvertisePage;
