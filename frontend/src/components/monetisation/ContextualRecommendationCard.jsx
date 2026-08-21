import React from 'react';

import { useCommercialCardMeasurement } from '../../hooks/useCommercialCardMeasurement';


export default function ContextualRecommendationCard({
  recommendation,
  articleId,
  articleCategory,
  navigationKey,
}) {
  const measurement = useCommercialCardMeasurement({
    navigationKey,
    enabled: Boolean(recommendation),
    metadata: recommendation ? {
      card_id: recommendation.card_id,
      provider_id: recommendation.provider_id,
      placement_id: recommendation.placement_id,
      article_id: String(articleId || '').trim().toLowerCase(),
      article_category: String(articleCategory || '').trim().toLowerCase(),
      use_case: recommendation.use_case,
      destination_type: recommendation.destination_type,
      destination_id: recommendation.destination_id,
      rule_reason_code: recommendation.rule_reason_code,
      variant_version: recommendation.variant_version,
      disclosure_version: recommendation.disclosure_version,
    } : null,
  });

  if (!recommendation) return null;

  const linkProps = recommendation.external
    ? { target: '_blank', rel: 'sponsored noopener noreferrer' }
    : {};

  return (
    <aside
      ref={measurement.cardRef}
      aria-label="Contextual recommendation"
      data-testid="contextual-recommendation-card"
      className="not-prose mt-8 rounded-xl border border-[#D8D2C7] bg-[#FBFAF7] px-5 py-5 text-slate-900 shadow-sm dark:border-gray-700 dark:bg-gray-950/40 dark:text-white sm:px-6"
    >
      <div className="text-[11px] font-bold uppercase tracking-[0.14em] text-emerald-700 dark:text-emerald-400">
        {recommendation.context_label}
      </div>
      <h2 className="mt-2 max-w-2xl font-headline text-xl font-bold leading-tight tracking-[-0.01em] text-slate-950 dark:text-white sm:text-2xl">
        {recommendation.heading}
      </h2>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-700 dark:text-slate-300 sm:text-[15px]">
        {recommendation.benefit}
      </p>
      <div className="mt-4 flex flex-col items-start gap-3 border-t border-[#E6E1D8] pt-4 dark:border-gray-800 sm:flex-row sm:items-center sm:justify-between">
        <div className="text-sm font-semibold text-slate-700 dark:text-slate-200">
          {recommendation.provider_display_name}
        </div>
        <a
          href={recommendation.destination_url}
          onClick={measurement.onCommercialClick}
          className="inline-flex min-h-11 items-center justify-center rounded-md bg-slate-900 px-4 py-2.5 text-sm font-bold text-white transition-colors hover:bg-emerald-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-700 focus-visible:ring-offset-2 dark:bg-emerald-700 dark:hover:bg-emerald-600 dark:focus-visible:ring-offset-gray-950"
          {...linkProps}
        >
          {recommendation.cta} <span aria-hidden="true" className="ml-1">→</span>
        </a>
      </div>
      <p className="mt-3 text-xs leading-5 text-slate-500 dark:text-slate-400">
        {recommendation.disclosure}
      </p>
    </aside>
  );
}
