const SAFE_IDENTIFIER = /^[a-z0-9_-]+$/;
const MAX_EVIDENCE_CHARACTERS = 1400;

const SENSITIVE_TOPIC_PATTERN = /\b(?:death|deaths|died|fatal|fatality|fatalities|killed|bereavement|funeral|serious\s+accident|serious\s+collision|road\s+traffic\s+collision|crash|murder|manslaughter|crime|criminal|violence|violent|assault|stabbing|shooting|rape|sexual\s+offen[cs]e|sexual\s+assault|abuse|safeguarding|missing\s+(?:person|child|man|woman|boy|girl)|emergency|disaster|serious\s+health|medical\s+emergency|life[-\s]threatening|court|sentenced|sentencing|convicted|conviction|prison|jailed)\b/i;

const ACCOUNTING_TOPIC_PATTERN = /\b(?:accounting\s+software|bookkeeping\s+software|cloud\s+accounting|xero|quickbooks|freeagent|sage\s+accounting|vat\s+software|invoicing\s+software|making\s+tax\s+digital\s+software)\b/i;

export const CONTEXTUAL_RECOMMENDATIONS = Object.freeze([
  Object.freeze({
    card_id: 'accounting_software_guide_v1',
    provider_id: 'cheshire_today_guides',
    placement_id: 'article_after_body',
    use_case: 'accounting_software',
    destination_type: 'guide',
    destination_id: 'best_accounting_software_uk',
    destination_url: '/guides/best-accounting-software-uk',
    external: false,
    context_label: 'Practical guide for small businesses',
    heading: 'Compare accounting software for your business',
    benefit: 'Review UK options for bookkeeping, VAT, invoicing and financial reporting.',
    provider_display_name: 'Cheshire Today Guides',
    cta: 'Compare accounting tools',
    disclosure: 'Affiliate guide — Cheshire Today may earn commission from links in this guide.',
    rule_reason_code: 'high_confidence_accounting_topic',
    variant_version: 'v1',
    disclosure_version: 'affiliate_guide_v1',
    allowed_categories: Object.freeze(['business', 'business_finance', 'economy', 'finance']),
  }),
]);

export const normaliseContextualCategory = (value) => String(value || '')
  .trim()
  .toLowerCase()
  .replace(/[^a-z0-9]+/g, '_')
  .replace(/^_+|_+$/g, '')
  .slice(0, 32);

const boundedArticleEvidence = (article) => {
  const tags = Array.isArray(article?.tags)
    ? article.tags.slice(0, 12).map((tag) => String(tag || '').slice(0, 60))
    : [];
  return [
    String(article?.title || '').slice(0, 300),
    String(article?.summary || '').slice(0, 900),
    ...tags,
  ]
    .join(' ')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase()
    .slice(0, MAX_EVIDENCE_CHARACTERS);
};

export const isContextualRecommendationRegistryBounded = (recommendation) => {
  const identifierLimits = {
    card_id: 64,
    provider_id: 48,
    placement_id: 48,
    use_case: 48,
    destination_id: 96,
    rule_reason_code: 64,
    variant_version: 32,
    disclosure_version: 32,
  };
  return Object.entries(identifierLimits).every(([field, maximum]) => {
    const value = recommendation?.[field];
    return typeof value === 'string' && value.length > 0 && value.length <= maximum && SAFE_IDENTIFIER.test(value);
  });
};

export const selectContextualRecommendation = (article) => {
  if (!article || typeof article !== 'object') return null;
  const category = normaliseContextualCategory(article.category);
  const evidence = boundedArticleEvidence(article);
  if (!category || !evidence || SENSITIVE_TOPIC_PATTERN.test(evidence)) return null;

  const recommendation = CONTEXTUAL_RECOMMENDATIONS[0];
  if (!recommendation.allowed_categories.includes(category)) return null;
  if (!ACCOUNTING_TOPIC_PATTERN.test(evidence)) return null;
  if (!isContextualRecommendationRegistryBounded(recommendation)) return null;
  return recommendation;
};
