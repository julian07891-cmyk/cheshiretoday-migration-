import React from "react";

export default function SectionHeader({
  title,
  eyebrow = "",
  description = "",
  meta = "",
  actionLabel = "",
  onAction,
  compact = false,
}) {
  return (
    <header className={compact ? "mb-4" : "mb-6"}>
      <div
        className="mb-4 h-px w-full bg-slate-300 dark:bg-gray-700"
        aria-hidden="true"
      />

      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="min-w-0">
          {eyebrow ? (
            <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-700 dark:text-emerald-400">
              {eyebrow}
            </p>
          ) : null}

          <h2 className="font-headline text-[1.75rem] font-bold leading-[1.05] tracking-[-0.025em] text-slate-950 sm:text-3xl dark:text-white">
            {title}
          </h2>

          {description ? (
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600 dark:text-gray-400">
              {description}
            </p>
          ) : null}
        </div>

        {(meta || (actionLabel && typeof onAction === "function")) ? (
          <div className="flex flex-wrap items-center gap-3 sm:flex-none sm:justify-end">
            {meta ? (
              <span className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] font-medium text-slate-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300">
                {meta}
              </span>
            ) : null}

            {actionLabel && typeof onAction === "function" ? (
              <button
                type="button"
                onClick={onAction}
                className="text-sm font-semibold text-[#1E3A8A] transition-colors hover:text-blue-800 hover:underline hover:underline-offset-4 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1E3A8A] focus-visible:ring-offset-2 dark:text-blue-300 dark:hover:text-blue-200 dark:focus-visible:ring-offset-gray-900"
              >
                {actionLabel}
              </button>
            ) : null}
          </div>
        ) : null}
      </div>
    </header>
  );
}
