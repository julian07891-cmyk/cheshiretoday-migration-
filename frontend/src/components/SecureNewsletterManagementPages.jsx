import React, { useEffect, useRef, useState } from "react";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle,
  Loader2,
  Mail,
} from "lucide-react";
import {
  captureNewsletterLinkState,
  confirmSecureNewsletterReactivation,
  confirmSecureNewsletterUnsubscribe,
  requestSecureNewsletterPreferencesLink,
  requestSecureNewsletterReactivationLink,
  requestSecureNewsletterUnsubscribeLink,
  secureNewsletterStateForFailure,
  updateSecureNewsletterPreferences,
  verifySecureNewsletterPreferences,
} from "../services/secureNewsletterManagement";

const EMPTY_PREFERENCES = {
  daily_brief: false,
  weekly_roundup: false,
  breaking_news: false,
};

const STATE_COPY = {
  loading: {
    title: "Checking your secure link",
    message: "Please wait while we check this link.",
  },
  invalid: {
    title: "This link is not valid",
    message: "Please request a new secure newsletter link and try again.",
  },
  retired: {
    title: "This older link has been retired",
    message: "Request a new secure newsletter link to continue.",
  },
  unavailable: {
    title: "Newsletter management is unavailable",
    message: "Please try again later.",
  },
  "reactivation-required": {
    title: "Reactivation is required",
    message: "Please request a secure reactivation link to continue.",
  },
};

const useCapturedToken = () => {
  const [linkState] = useState(() => captureNewsletterLinkState());
  return linkState;
};

const SecurePageShell = ({ title, description, children }) => (
  <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
    <Helmet>
      <title>{title} | Cheshire Today</title>
      <meta name="robots" content="noindex, nofollow, noarchive" />
      <meta name="referrer" content="no-referrer" />
    </Helmet>
    <main className="max-w-lg w-full">
      <Link
        to="/"
        className="inline-flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 mb-6 text-sm"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        Back to Cheshire Today
      </Link>
      <section className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 sm:p-8">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full mb-4">
            <Mail className="h-8 w-8 text-blue-600 dark:text-blue-400" aria-hidden="true" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            {title}
          </h1>
          <p className="text-gray-600 dark:text-gray-300">{description}</p>
        </div>
        {children}
      </section>
    </main>
  </div>
);

const FlowState = ({ state }) => {
  const copy = STATE_COPY[state];
  const isLoading = state === "loading";
  return (
    <div
      className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 text-center"
      role={isLoading ? "status" : "alert"}
      aria-live="polite"
    >
      {isLoading ? (
        <Loader2 className="h-6 w-6 animate-spin mx-auto mb-3 text-blue-600" aria-hidden="true" />
      ) : (
        <AlertCircle className="h-6 w-6 mx-auto mb-3 text-amber-600" aria-hidden="true" />
      )}
      <h2 className="font-semibold text-gray-900 dark:text-white">{copy.title}</h2>
      <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{copy.message}</p>
    </div>
  );
};

const SuccessState = ({ title, message }) => (
  <div
    className="rounded-lg border border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20 p-4 text-center"
    role="status"
    aria-live="polite"
  >
    <CheckCircle className="h-6 w-6 mx-auto mb-3 text-green-600" aria-hidden="true" />
    <h2 className="font-semibold text-green-900 dark:text-green-100">{title}</h2>
    <p className="text-sm text-green-800 dark:text-green-200 mt-1">{message}</p>
  </div>
);

const RequestLinkForm = ({ requestLink, actionLabel }) => {
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [state, setState] = useState("ready");

  const submit = async (event) => {
    event.preventDefault();
    if (submitting) {
      return;
    }
    const normalizedEmail = email.trim().toLowerCase();
    if (
      !normalizedEmail ||
      normalizedEmail.length > 254 ||
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)
    ) {
      setState("invalid");
      return;
    }

    setSubmitting(true);
    const result = await requestLink(normalizedEmail);
    if (
      result.ok &&
      result.data?.success === true &&
      typeof result.data?.message === "string"
    ) {
      setState("success");
    } else {
      setState(result.status === 503 || result.status === 0 ? "unavailable" : "invalid");
    }
    setSubmitting(false);
  };

  if (state === "success") {
    return (
      <SuccessState
        title="Check your email"
        message="If the address is eligible, an email with the next step will be sent shortly."
      />
    );
  }

  return (
    <form onSubmit={submit} className="mt-6 space-y-3">
      <label
        htmlFor={`newsletter-link-${actionLabel}`}
        className="block text-sm font-medium text-gray-800 dark:text-gray-200"
      >
        Email address
      </label>
      <input
        id={`newsletter-link-${actionLabel}`}
        type="email"
        autoComplete="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        disabled={submitting}
        required
        className="w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900"
      />
      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {submitting ? "Requesting…" : actionLabel}
      </button>
      {state !== "ready" && <FlowState state={state} />}
    </form>
  );
};

const PreferenceControls = ({ preferences, onChange, disabled }) => {
  const options = [
    ["daily_brief", "Daily Brief"],
    ["weekly_roundup", "Weekly Roundup"],
    ["breaking_news", "Breaking News"],
  ];

  return (
    <fieldset className="space-y-3" disabled={disabled}>
      <legend className="font-semibold text-gray-900 dark:text-white mb-3">
        Choose your newsletters
      </legend>
      {options.map(([key, label]) => (
        <label
          key={key}
          className="flex items-center justify-between gap-4 rounded-lg border border-gray-200 dark:border-gray-700 p-4 cursor-pointer"
        >
          <span className="text-gray-800 dark:text-gray-200">{label}</span>
          <input
            type="checkbox"
            checked={preferences[key]}
            onChange={(event) => onChange(key, event.target.checked)}
            className="h-5 w-5 rounded border-gray-300"
          />
        </label>
      ))}
    </fieldset>
  );
};

export const SecureNewsletterPreferencesPage = () => {
  const linkState = useCapturedToken();
  const token = linkState.token;
  const verificationStarted = useRef(false);
  const [state, setState] = useState(
    linkState.retired ? "retired" : token ? "loading" : "invalid",
  );
  const [preferences, setPreferences] = useState(EMPTY_PREFERENCES);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!token || verificationStarted.current) {
      return;
    }
    verificationStarted.current = true;

    const verify = async () => {
      const result = await verifySecureNewsletterPreferences(token);
      if (
        result.ok &&
        result.data?.success === true &&
        result.data.preferences &&
        typeof result.data.preferences.daily_brief === "boolean" &&
        typeof result.data.preferences.weekly_roundup === "boolean" &&
        typeof result.data.preferences.breaking_news === "boolean"
      ) {
        setPreferences({
          daily_brief: result.data.preferences.daily_brief,
          weekly_roundup: result.data.preferences.weekly_roundup,
          breaking_news: result.data.preferences.breaking_news,
        });
        setState("ready");
        return;
      }
      setState(
        secureNewsletterStateForFailure(result.status, {
          allowReactivation: true,
        }),
      );
    };

    verify();
  }, [token]);

  const updatePreference = (key, checked) => {
    setPreferences((current) => ({ ...current, [key]: checked }));
  };

  const submit = async (event) => {
    event.preventDefault();
    if (!token || submitting) {
      return;
    }
    setSubmitting(true);
    const result = await updateSecureNewsletterPreferences(token, preferences);
    if (result.ok && result.data?.success === true) {
      setState("success");
    } else {
      setState(
        secureNewsletterStateForFailure(result.status, {
          allowReactivation: true,
        }),
      );
    }
    setSubmitting(false);
  };

  return (
    <SecurePageShell
      title="Newsletter preferences"
      description="Review and update the Cheshire Today newsletters you receive."
    >
      {state === "ready" && (
        <form onSubmit={submit} className="space-y-6">
          <PreferenceControls
            preferences={preferences}
            onChange={updatePreference}
            disabled={submitting}
          />
          <button
            type="submit"
            className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={submitting}
          >
            {submitting ? "Saving…" : "Save preferences"}
          </button>
        </form>
      )}
      {state === "success" && (
        <SuccessState
          title="Preferences updated"
          message="Your newsletter preferences have been saved."
        />
      )}
      {!["ready", "success"].includes(state) && <FlowState state={state} />}
      {!["ready", "success", "loading"].includes(state) && (
        <RequestLinkForm
          requestLink={requestSecureNewsletterPreferencesLink}
          actionLabel="Request preferences link"
        />
      )}
    </SecurePageShell>
  );
};

export const SecureNewsletterUnsubscribePage = () => {
  const linkState = useCapturedToken();
  const token = linkState.token;
  const [state, setState] = useState(
    linkState.retired ? "retired" : token ? "ready" : "invalid",
  );
  const [submitting, setSubmitting] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    if (!token || submitting) {
      return;
    }
    setSubmitting(true);
    const result = await confirmSecureNewsletterUnsubscribe(token);
    setState(
      result.ok && result.data?.success === true
        ? "success"
        : secureNewsletterStateForFailure(result.status),
    );
    setSubmitting(false);
  };

  return (
    <SecurePageShell
      title="Confirm unsubscribe"
      description="Use the button below only if you want to stop all Cheshire Today newsletters."
    >
      {state === "ready" && (
        <form onSubmit={submit}>
          <button
            type="submit"
            className="w-full rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={submitting}
          >
            {submitting ? "Confirming…" : "Confirm unsubscribe"}
          </button>
        </form>
      )}
      {state === "success" && (
        <SuccessState
          title="Unsubscribe confirmed"
          message="Your newsletter unsubscribe request has been completed."
        />
      )}
      {!["ready", "success"].includes(state) && <FlowState state={state} />}
      {!["ready", "success"].includes(state) && (
        <RequestLinkForm
          requestLink={requestSecureNewsletterUnsubscribeLink}
          actionLabel="Request unsubscribe link"
        />
      )}
    </SecurePageShell>
  );
};

export const SecureNewsletterReactivationPage = () => {
  const linkState = useCapturedToken();
  const token = linkState.token;
  const [state, setState] = useState(
    linkState.retired ? "retired" : token ? "ready" : "invalid",
  );
  const [preferences, setPreferences] = useState(EMPTY_PREFERENCES);
  const [selectionConfirmed, setSelectionConfirmed] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const updatePreference = (key, checked) => {
    setPreferences((current) => ({ ...current, [key]: checked }));
  };

  const submit = async (event) => {
    event.preventDefault();
    if (!token || !selectionConfirmed || submitting) {
      return;
    }
    setSubmitting(true);
    const result = await confirmSecureNewsletterReactivation(
      token,
      preferences,
    );
    setState(
      result.ok && result.data?.success === true
        ? "success"
        : secureNewsletterStateForFailure(result.status),
    );
    setSubmitting(false);
  };

  return (
    <SecurePageShell
      title="Reactivate newsletters"
      description="Choose your newsletters, then confirm that you want to receive them again."
    >
      {state === "ready" && (
        <form onSubmit={submit} className="space-y-6">
          <PreferenceControls
            preferences={preferences}
            onChange={updatePreference}
            disabled={submitting}
          />
          <label className="flex items-start gap-3 text-sm text-gray-700 dark:text-gray-300">
            <input
              type="checkbox"
              checked={selectionConfirmed}
              onChange={(event) => setSelectionConfirmed(event.target.checked)}
              disabled={submitting}
              className="h-5 w-5 mt-0.5 rounded border-gray-300"
            />
            I confirm these newsletter preferences.
          </label>
          <button
            type="submit"
            className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={!selectionConfirmed || submitting}
          >
            {submitting ? "Confirming…" : "Confirm reactivation"}
          </button>
        </form>
      )}
      {state === "success" && (
        <SuccessState
          title="Newsletters reactivated"
          message="Your newsletter reactivation has been completed."
        />
      )}
      {!["ready", "success"].includes(state) && <FlowState state={state} />}
      {!["ready", "success"].includes(state) && (
        <RequestLinkForm
          requestLink={requestSecureNewsletterReactivationLink}
          actionLabel="Request reactivation link"
        />
      )}
    </SecurePageShell>
  );
};
