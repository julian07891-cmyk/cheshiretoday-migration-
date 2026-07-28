const URL_LIKE_PATTERN = /(?:https?:\/\/|www\.)\S+|\b[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+(?:\/\S*)?/i;
const TAG_LIKE_PATTERN = /<[^>]*>|[<>]/;
const LINE_BREAK_PATTERN = /[\r\n\t]/;
const CANONICAL_ARTICLE_URL = /^https:\/\/cheshiretoday\.co\.uk\/article\/[0-9a-f]{24}\/[a-z0-9-]+$/i;

export const THREADS_OPENING_MAX = 200;
export const THREADS_CONTEXT_MAX = 240;


const normalizedText = value => typeof value === 'string' ? value.trim() : '';


const validatePlainText = (value, { required, maximum, label }) => {
  const text = normalizedText(value);
  if (required && !text) return `${label} is required.`;
  if (!text) return '';
  if (text.length > maximum) return `${label} must be ${maximum} characters or fewer.`;
  if (URL_LIKE_PATTERN.test(text) || TAG_LIKE_PATTERN.test(text) || LINE_BREAK_PATTERN.test(text)) {
    return `${label} must be plain text without URLs, HTML or line breaks.`;
  }
  return '';
};


export const validateThreadsOpening = value => validatePlainText(value, {
  required: true,
  maximum: THREADS_OPENING_MAX,
  label: 'Verified opening line',
});


export const validateThreadsContext = value => validatePlainText(value, {
  required: false,
  maximum: THREADS_CONTEXT_MAX,
  label: 'Verified context',
});


export const buildThreadsPost = ({ opening, context, canonicalUrl }) => {
  const safeOpening = normalizedText(opening);
  const safeContext = normalizedText(context);
  if (
    validateThreadsOpening(safeOpening)
    || validateThreadsContext(safeContext)
    || !CANONICAL_ARTICLE_URL.test(String(canonicalUrl || ''))
  ) return '';
  return [safeOpening, safeContext, canonicalUrl].filter(Boolean).join('\n\n');
};
