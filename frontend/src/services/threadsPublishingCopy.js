const CANONICAL_ARTICLE_URL = /^https:\/\/cheshiretoday\.co\.uk\/article\/[0-9a-f]{24}\/[a-z0-9-]+$/i;

export const buildThreadsPost = ({ title, canonicalUrl }) => {
  const exactTitle = typeof title === 'string' ? title.trim() : '';
  if (!exactTitle || !CANONICAL_ARTICLE_URL.test(String(canonicalUrl || ''))) return '';
  return `${exactTitle}\n\nRead the full story on Cheshire Today.\n\n${canonicalUrl}`;
};
