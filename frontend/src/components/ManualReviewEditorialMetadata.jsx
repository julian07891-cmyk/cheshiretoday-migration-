import React from 'react';


const displayLabel = (value) => {
  const text = String(value || '').replace(/_/g, ' ');
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : '';
};

const ManualReviewEditorialMetadata = ({ metadata }) => {
  if (!metadata) return null;

  const facts = [
    ['Topic', metadata.editorial_topic],
    ['Locality', metadata.detected_locality],
    ['Source', displayLabel(metadata.source_type)],
    ['Rewrite status', displayLabel(metadata.rewrite_status)],
    ['Rewrite', `${metadata.rewrite_length ?? 0} characters`],
    ['Image', displayLabel(metadata.image_status)],
    ['Freshness', displayLabel(metadata.freshness_bucket)],
    ['Failed gate', displayLabel(metadata.failed_public_gate)],
    ['Duplicate', displayLabel(metadata.duplicate_status)],
  ];

  return (
    <section
      className="mt-2 rounded-md border border-amber-200/80 bg-white/70 p-2 dark:border-amber-800 dark:bg-gray-900/40"
      aria-label="Editorial assessment"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-semibold text-foreground">
          {metadata.publication_recommendation}
        </span>
        <span className="text-[11px] text-muted-foreground">
          {metadata.auto_publish_candidate
            ? 'Automatic publish candidate'
            : 'Not an automatic publish candidate'}
        </span>
      </div>
      <dl className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-[11px] sm:grid-cols-3">
        {facts.map(([label, value]) => (
          <div key={label} className="min-w-0">
            <dt className="text-muted-foreground">{label}</dt>
            <dd className="truncate font-medium text-foreground" title={String(value || '')}>
              {value || 'Not recorded'}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
};

export default ManualReviewEditorialMetadata;
