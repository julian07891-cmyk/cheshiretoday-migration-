import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { ANALYTICS_CONSENT, persistAnalyticsConsent, readAnalyticsConsent } from "../analytics/analyticsConsent";
import { disableAnalyticsProviders, enableAnalyticsProviders, requestAnalyticsPageView } from "../analytics/analyticsProviders";

const AnalyticsConsentContext = createContext({
  status: ANALYTICS_CONSENT.UNKNOWN,
  openAnalyticsPreferences: () => {},
});

const EXCLUDED_PATHS = [
  "/admin", "/unsubscribe", "/newsletter/preferences", "/newsletter/reactivate",
  "/jobs/payment-success", "/advertise/payment-success", "/advertise/pay",
];
const UTM_PARAMETERS = new Set(["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"]);
const safeAttributionValue = (value) => value.length <= 100 && /^[A-Za-z0-9._~-]+$/.test(value);
const CONSENT_CHOICE_CLASS = "min-h-11 flex-1 rounded-md border-2 border-slate-800 bg-white px-4 py-2 text-sm font-semibold text-slate-900 focus:outline-none focus:ring-4 focus:ring-sky-300 dark:border-slate-100 dark:bg-slate-900 dark:text-white";

export const normalizeAnalyticsRoute = (location) => {
  const pathname = location?.pathname || "/";
  if (EXCLUDED_PATHS.some((path) => pathname === path || pathname.startsWith(`${path}/`))) return null;

  const input = new URLSearchParams(location?.search || "");
  const output = new URLSearchParams();
  [...input.entries()].sort(([left], [right]) => left.localeCompare(right)).forEach(([key, value]) => {
    const permitted = UTM_PARAMETERS.has(key) || (pathname === "/" && key === "category");
    if (permitted && safeAttributionValue(value)) output.append(key, value);
  });
  const query = output.toString();
  return query ? `${pathname}?${query}` : pathname;
};

const AnalyticsRouteTracker = ({ status }) => {
  const location = useLocation();
  const route = normalizeAnalyticsRoute(location);
  useEffect(() => {
    if (status === ANALYTICS_CONSENT.ACCEPTED && route) {
      enableAnalyticsProviders();
      requestAnalyticsPageView(route);
    }
  }, [route, status]);
  return null;
};

export const useAnalyticsConsent = () => useContext(AnalyticsConsentContext);

const AnalyticsConsentManager = ({ children }) => {
  const [status, setStatus] = useState(() => readAnalyticsConsent());
  const [preferencesOpen, setPreferencesOpen] = useState(() => readAnalyticsConsent() === ANALYTICS_CONSENT.UNKNOWN);

  useEffect(() => {
    if (status === ANALYTICS_CONSENT.REJECTED) disableAnalyticsProviders();
  }, [status]);

  const choose = useCallback((nextStatus) => {
    persistAnalyticsConsent(nextStatus);
    if (nextStatus === ANALYTICS_CONSENT.REJECTED) disableAnalyticsProviders();
    setStatus(nextStatus);
    setPreferencesOpen(false);
  }, []);
  const openAnalyticsPreferences = useCallback(() => setPreferencesOpen(true), []);
  const contextValue = useMemo(() => ({ status, openAnalyticsPreferences }), [status, openAnalyticsPreferences]);

  return (
    <AnalyticsConsentContext.Provider value={contextValue}>
      <AnalyticsRouteTracker status={status} />
      {children}
      {preferencesOpen && (
        <section aria-labelledby="analytics-consent-heading" aria-modal="false" role="dialog" className="fixed inset-x-3 bottom-3 z-[100] mx-auto max-w-2xl rounded-lg border border-neutral-300 bg-white p-4 text-neutral-900 shadow-xl dark:border-slate-600 dark:bg-slate-900 dark:text-white sm:p-5">
          <h2 id="analytics-consent-heading" className="text-lg font-bold">Analytics preferences</h2>
          <p className="mt-2 text-sm leading-6">We use optional analytics to understand how Cheshire Today is used and improve the site. You can accept or reject analytics.</p>
          {status !== ANALYTICS_CONSENT.UNKNOWN && <p className="mt-1 text-sm">Current choice: {status === ANALYTICS_CONSENT.ACCEPTED ? "accepted" : "rejected"}.</p>}
          <div className="mt-4 flex flex-col gap-2 sm:flex-row">
            <button type="button" onClick={() => choose(ANALYTICS_CONSENT.ACCEPTED)} className={CONSENT_CHOICE_CLASS}>Accept analytics</button>
            <button type="button" onClick={() => choose(ANALYTICS_CONSENT.REJECTED)} className={CONSENT_CHOICE_CLASS}>Reject analytics</button>
            {status !== ANALYTICS_CONSENT.UNKNOWN && <button type="button" onClick={() => setPreferencesOpen(false)} className="min-h-11 rounded-md px-4 py-2 text-sm font-semibold underline focus:outline-none focus:ring-4 focus:ring-sky-300">Close</button>}
          </div>
          <Link className="mt-3 inline-block text-sm underline focus:outline-none focus:ring-4 focus:ring-sky-300" to="/cookies">Cookie Policy</Link>
        </section>
      )}
    </AnalyticsConsentContext.Provider>
  );
};

export default AnalyticsConsentManager;
