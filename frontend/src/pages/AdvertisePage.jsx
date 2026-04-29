import React from "react";
import { useNavigate } from "react-router-dom";
import { getApiUrl } from "../utils/api";
import { trackEvent } from "../utils/trackEvent";

const PRICING = [
  {
    id: "local_starter",
    name: "Local Starter",
    price: "£49 / month",
    badge: "Launch price for small local businesses",
    bullets: [
      "30-day standard sponsored placement",
      "Homepage or article sponsored slot, depending on availability",
      "Link to your website, booking page or Facebook page",
    ],
    subject: "Advertising enquiry — Local Starter package",
  },
  {
    id: "local_featured",
    name: "Local Featured",
    price: "£99 / month",
    badge: "Most popular launch package",
    bullets: [
      "30-day higher-priority sponsored rotation",
      "Can appear in desktop and mobile sponsored placements",
      "Stronger rotation and better visibility when multiple advertisers are active",
    ],
    subject: "Advertising enquiry — Local Featured package",
  },
  {
    id: "local_partner",
    name: "Local Partner",
    price: "£199 / month",
    badge: "Best for regular local exposure",
    bullets: [
      "30-day priority sponsored rotation",
      "Homepage, article and selected category visibility where suitable",
      "One sponsored business spotlight per month",
    ],
    subject: "Advertising enquiry — Local Partner package",
  },
];

const AD_SLOTS = [
  {
    title: "Homepage desktop sponsor slot",
    description: "Your advert can appear in a prominent right-hand homepage sponsor slot on desktop and larger screens.",
  },
  {
    title: "Mobile homepage sponsor card",
    description: "Your advert can appear as a clearly labelled mobile sponsor card for readers browsing the homepage.",
  },
  {
    title: "Partner visibility",
    description: "Local Partner campaigns may also receive selected article, category or business spotlight visibility where suitable and agreed.",
  },
];

const AdvertisePage = () => {
  const navigate = useNavigate();
  const [showForm, setShowForm] = React.useState(false);
  const [selectedTier, setSelectedTier] = React.useState(null);
  const [submittedAdvert, setSubmittedAdvert] = React.useState(null);
  const [checkoutLoading, setCheckoutLoading] = React.useState(false);
  const [enquiryLoading, setEnquiryLoading] = React.useState(false);
  const [enquirySent, setEnquirySent] = React.useState(false);
  const [checkoutError, setCheckoutError] = React.useState("");

  const email = "news@cheshiretoday.co.uk";

  React.useEffect(() => {
    if (!showForm) return;

    const scrollY = window.scrollY || window.pageYOffset || 0;
    const originalOverflow = document.body.style.overflow;
    const originalPosition = document.body.style.position;
    const originalTop = document.body.style.top;
    const originalWidth = document.body.style.width;

    document.body.style.overflow = "hidden";
    document.body.style.position = "fixed";
    document.body.style.top = `-${scrollY}px`;
    document.body.style.width = "100%";

    return () => {
      document.body.style.overflow = originalOverflow;
      document.body.style.position = originalPosition;
      document.body.style.top = originalTop;
      document.body.style.width = originalWidth;
      window.scrollTo(0, scrollY);
    };
  }, [showForm]);

  return (
    <div className="bg-gray-50 dark:bg-gray-900 min-h-screen">
      <div className="container mx-auto px-4 py-6 md:py-10 max-w-5xl">
        <button onClick={() => navigate("/")} className="text-sm text-emerald-600 hover:underline mb-4">← Back to Home</button>
        <h1 className="text-2xl md:text-4xl font-extrabold text-gray-900 dark:text-white">
          Advertise on Cheshire Today
        </h1>
        <p className="mt-3 text-gray-700 dark:text-gray-300 max-w-3xl">
          Launch pricing for Cheshire businesses: reach local readers across the homepage and article pages with sponsored placements from £49/month. Choose a monthly package below and we’ll recommend the best fit for your area and goals.
        </p>

        <div className="mt-5 rounded-xl border border-amber-200 dark:border-amber-900/60 bg-amber-50 dark:bg-amber-950/20 p-4 md:p-5 max-w-4xl">
          <h2 className="text-lg font-extrabold text-gray-900 dark:text-white">
            How advertising works
          </h2>
          <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-gray-700 dark:text-gray-300">
            <p><strong>30-day packages:</strong> each package runs monthly and can be renewed, changed, paused or cancelled.</p>
            <p><strong>Where adverts appear:</strong> your advert can appear in available homepage and article advertising slots, including desktop and mobile placements.</p>
            <p><strong>Automatic rotation:</strong> when multiple advertisers are active, adverts rotate through available slots. Higher packages receive stronger rotation priority.</p>
            <p><strong>Manual review:</strong> all adverts are reviewed by Cheshire Today before going live to protect readers and advertisers.</p>
          </div>
        </div>

        <div className="mt-6 md:mt-8 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 md:p-6 shadow">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-wide text-amber-700 dark:text-amber-300">Advertiser package</p>
              <h2 className="mt-1 text-xl font-bold text-gray-900 dark:text-white">What your campaign includes</h2>
              <p className="mt-2 text-sm text-gray-700 dark:text-gray-300 max-w-3xl">
                Cheshire Today advertising is built for local businesses that want simple, visible promotion without intrusive popups or confusing ad networks.
              </p>
            </div>
            <span className="inline-flex shrink-0 items-center justify-center rounded-full bg-amber-100 px-4 py-2 text-sm font-semibold text-amber-800 dark:bg-amber-900/40 dark:text-amber-200">From £49/month</span>
          </div>

          <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-3 text-sm text-gray-700 dark:text-gray-300">
            <div className="rounded-lg bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 p-3">
              <strong className="text-gray-900 dark:text-white">Clear local visibility</strong>
              <p className="mt-1">Sponsored placements across available homepage and article slots.</p>
            </div>
            <div className="rounded-lg bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 p-3">
              <strong className="text-gray-900 dark:text-white">Direct traffic</strong>
              <p className="mt-1">Link readers to your website, booking page, offer page or Facebook page.</p>
            </div>
            <div className="rounded-lg bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 p-3">
              <strong className="text-gray-900 dark:text-white">Performance reporting</strong>
              <p className="mt-1">Campaign views, clicks and CTR can be reviewed from the advertiser dashboard.</p>
            </div>
            <div className="rounded-lg bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 p-3">
              <strong className="text-gray-900 dark:text-white">Simple setup</strong>
              <p className="mt-1">Send a headline, message, link and logo or image. We review before publishing.</p>
            </div>
          </div>
        </div>

        <div className="mt-6 md:mt-8 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 md:p-6 shadow">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Where your advert appears
          </h2>
          <p className="mt-2 text-sm text-gray-700 dark:text-gray-300 max-w-3xl">
            Sponsored adverts are clearly labelled and link to your website, booking page or Facebook page. Placement depends on package level, available slots and editorial suitability.
          </p>

          <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4">
            {AD_SLOTS.map((slot) => (
              <div key={slot.title} className="rounded-xl border border-amber-200 dark:border-amber-900/50 bg-amber-50/70 dark:bg-amber-950/20 p-4">
                <h3 className="text-base font-bold text-gray-900 dark:text-white">
                  {slot.title}
                </h3>
                <p className="mt-2 text-sm text-gray-700 dark:text-gray-300">
                  {slot.description}
                </p>
              </div>
            ))}
          </div>

          <div className="mt-5 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-4 text-sm text-gray-700 dark:text-gray-300">
            <p><strong>Review before payment:</strong> after you submit your advert details, we show you a summary before you continue to secure payment.</p>
            <p className="mt-2"><strong>Manual approval:</strong> payment does not make an advert live automatically. Cheshire Today reviews each advert before publication.</p>
          </div>
        </div>

        <div className="mt-6 md:mt-8 rounded-xl border border-emerald-200 dark:border-emerald-900/60 bg-emerald-50 dark:bg-emerald-950/20 p-4 md:p-6 shadow">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-wide text-emerald-700 dark:text-emerald-300">Sponsored profile option</p>
              <h2 className="mt-1 text-xl font-bold text-gray-900 dark:text-white">Sponsored Business Spotlight</h2>
              <p className="mt-2 text-sm text-gray-700 dark:text-gray-300 max-w-3xl">
                Give your business more context than a banner advert. A Business Spotlight can introduce who you are, what you offer, where you operate and why Cheshire readers should contact you.
              </p>
            </div>
            <span className="inline-flex shrink-0 items-center justify-center rounded-full bg-emerald-600 px-4 py-2 text-sm font-semibold text-white">Included with Local Partner</span>
          </div>

          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3 text-sm text-gray-700 dark:text-gray-300">
            <div className="rounded-lg bg-white/70 dark:bg-gray-900/40 border border-emerald-100 dark:border-emerald-900/50 p-3">
              <strong className="text-gray-900 dark:text-white">Best for launches</strong>
              <p className="mt-1">Useful for new services, offers, openings, events, recruitment pushes or local awareness campaigns.</p>
            </div>
            <div className="rounded-lg bg-white/70 dark:bg-gray-900/40 border border-emerald-100 dark:border-emerald-900/50 p-3">
              <strong className="text-gray-900 dark:text-white">More trust than a banner</strong>
              <p className="mt-1">Readers get a short sponsored profile alongside your website, booking page or Facebook link.</p>
            </div>
            <div className="rounded-lg bg-white/70 dark:bg-gray-900/40 border border-emerald-100 dark:border-emerald-900/50 p-3">
              <strong className="text-gray-900 dark:text-white">Clearly labelled</strong>
              <p className="mt-1">Every spotlight is reviewed before publication and clearly marked as sponsored.</p>
            </div>
          </div>

          <button
            type="button"
            className="mt-4 inline-flex w-full md:w-auto items-center justify-center rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-5 py-3 transition"
            onClick={() => {
              const tier = PRICING.find((item) => item.id === "local_partner") || PRICING[2];
              setSelectedTier(tier);
              setSubmittedAdvert(null);
              setEnquiryLoading(false);
              setEnquirySent(false);
              setCheckoutError("");
              setShowForm(true);
            }}
          >
            Enquire about Business Spotlight
          </button>
        </div>

        <div className="mt-6 md:mt-8 grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6 items-stretch">
          {PRICING.map((tier) => (
            <div
              key={tier.name}
              className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4 md:p-6 shadow flex flex-col"
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
    setSubmittedAdvert(null);
    setEnquiryLoading(false);
    setEnquirySent(false);
    setCheckoutError("");
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
          <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 px-4 py-6 overflow-y-auto overscroll-contain">
            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto overscroll-contain border border-gray-200 dark:border-gray-700 shadow-xl">
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
                    package_price: selectedTier?.price,
                    phone: form.phone.value,
                    website: form.website.value,
                    target_area: form.target_area.value,
                    message: form.message.value,
                    tier: selectedTier?.name,
                    source: "advertise_page",
                  };

                  const reviewPayload = { ...payload, package_id: selectedTier?.id };
                  setSubmittedAdvert(reviewPayload);
                  setCheckoutError("");
                  setEnquirySent(false);
                  trackEvent("advertising_details_review", { tier: selectedTier?.name });
                }}
              >
                <div className="rounded-lg border border-amber-200 dark:border-amber-900/60 bg-amber-50 dark:bg-amber-950/20 p-3 text-sm text-gray-800 dark:text-gray-200">
                  <p>Selected package: <strong>{selectedTier?.name}</strong> — <strong>{selectedTier?.price}</strong></p>
                  <p className="mt-2"><strong>Before payment:</strong> submit your advert details first. We will show you a summary and then you can continue to secure payment if everything looks right.</p>
                  <p className="mt-2">Each payment covers one 30-day campaign. Your advert is reviewed before it goes live, and the 30 days start when approved and published.</p>
                </div>
                <input name="name" required placeholder="Your name" className="w-full p-3 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800" />
                <input name="business" required placeholder="Business name" className="w-full p-3 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800" />
                <input name="email" type="email" required placeholder="Email" className="w-full p-3 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800" />
                <input name="phone" placeholder="Phone number (optional)" className="w-full p-3 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800" />
                <input name="website" required placeholder="Website, booking page or Facebook page" className="w-full p-3 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800" />
                <input name="target_area" required placeholder="Target area, e.g. Crewe, Chester, Warrington" className="w-full p-3 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800" />
                <textarea name="message" required placeholder="Tell us what you want to promote" className="w-full p-3 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800" />

                <div className="flex gap-3 pt-2">
                  <button type="submit" className="flex-1 bg-amber-600 hover:bg-amber-700 text-white rounded-lg py-3 font-semibold">
                    Review advert details
                  </button>
                  <button type="button" onClick={() => setShowForm(false)} className="flex-1 border border-gray-300 dark:border-gray-700 rounded-lg py-3">
                    Cancel
                  </button>
                </div>

                {submittedAdvert && (
                  <div className="mt-4 rounded-xl border border-emerald-200 dark:border-emerald-900/60 bg-emerald-50 dark:bg-emerald-950/20 p-4 text-sm text-gray-800 dark:text-gray-200">
                    <h4 className="font-bold text-gray-900 dark:text-white">Review before payment</h4>
                    <p className="mt-2 text-xs text-emerald-700 dark:text-emerald-300">
                      Review your details below. No email is sent and no lead is created until you choose secure payment or send an enquiry.
                    </p>
                    <div className="mt-3 space-y-1">
                      <p><strong>Package:</strong> {submittedAdvert.tier} — {submittedAdvert.package_price}</p>
                      <p><strong>Business:</strong> {submittedAdvert.business}</p>
                      <p><strong>Website/Facebook:</strong> {submittedAdvert.website}</p>
                      <p><strong>Target area:</strong> {submittedAdvert.target_area}</p>
                      <p><strong>Advert message:</strong> {submittedAdvert.message}</p>
                    </div>

                    <div className="mt-3 rounded-lg border border-amber-200 dark:border-amber-900/60 bg-amber-50 dark:bg-amber-950/20 p-3">
                      <p><strong>Where your advert can appear:</strong> available homepage and article sponsored slots, including desktop and mobile placements. Local Partner campaigns may also receive selected category or business spotlight visibility where suitable.</p>
                      <p className="mt-2"><strong>Important:</strong> payment does not make the advert live automatically. Cheshire Today reviews each advert before publication.</p>
                    </div>

                    {checkoutError && (
                      <div className="mt-3 rounded-lg border border-red-200 bg-red-50 dark:bg-red-950/20 dark:border-red-900/60 p-3 text-sm text-red-700 dark:text-red-300">
                        {checkoutError}
                      </div>
                    )}

                    <div className="mt-4 grid grid-cols-1 gap-2">
                      <button
                        type="button"
                        disabled={checkoutLoading || enquiryLoading}
                        onClick={async () => {
                          setCheckoutError("");
                          setCheckoutLoading(true);
                          try {
                            const res = await fetch(getApiUrl() + "/api/advertising/checkout", {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({
                                ...submittedAdvert,
                                package_id: submittedAdvert.package_id,
                                origin_url: window.location.origin,
                              }),
                            });
                            const data = await res.json();
                            trackEvent("advertising_checkout_start", { tier: submittedAdvert.tier });
                            if (data?.checkout_url) {
                              window.location.href = data.checkout_url;
                              return;
                            }
                            setCheckoutError(data?.detail || "Could not start advertising checkout. Please contact news@cheshiretoday.co.uk.");
                          } catch (error) {
                            setCheckoutError("Could not start advertising checkout. Please contact news@cheshiretoday.co.uk.");
                          } finally {
                            setCheckoutLoading(false);
                          }
                        }}
                        className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60 text-white rounded-lg py-3 font-semibold"
                      >
                        {checkoutLoading ? "Starting secure payment..." : "Continue to secure payment"}
                      </button>

                      <button
                        type="button"
                        disabled={checkoutLoading || enquiryLoading || enquirySent}
                        onClick={async () => {
                          setCheckoutError("");
                          setEnquiryLoading(true);
                          try {
                            const res = await fetch(getApiUrl() + "/api/leads/advertise", {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({
                                ...submittedAdvert,
                                package_id: submittedAdvert.package_id,
                                origin_url: window.location.origin,
                              }),
                            });
                            const data = await res.json();
                            if (!res.ok || !data?.success) {
                              throw new Error(data?.detail || "Could not send advertising enquiry");
                            }
                            trackEvent("advertising_enquiry_submit", { tier: submittedAdvert.tier });
                            setEnquirySent(true);
                          } catch (error) {
                            setCheckoutError("Could not send the enquiry. Please try again or contact news@cheshiretoday.co.uk.");
                          } finally {
                            setEnquiryLoading(false);
                          }
                        }}
                        className="w-full border border-amber-300 dark:border-amber-800 text-amber-800 dark:text-amber-200 hover:bg-amber-50 dark:hover:bg-amber-950/30 rounded-lg py-3 font-semibold disabled:opacity-60"
                      >
                        {enquirySent ? "Enquiry sent" : enquiryLoading ? "Sending enquiry..." : "Send enquiry instead"}
                      </button>

                      <button
                        type="button"
                        disabled={checkoutLoading || enquiryLoading}
                        onClick={() => {
                          setSubmittedAdvert(null);
                          setCheckoutError("");
                          setEnquirySent(false);
                        }}
                        className="w-full text-sm text-gray-600 dark:text-gray-300 hover:underline py-2"
                      >
                        Edit details
                      </button>
                    </div>
                  </div>
                )}
              </form>
            </div>
          </div>
        )}

        <div className="mt-8 md:mt-10 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4 md:p-6 shadow max-w-3xl">
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
