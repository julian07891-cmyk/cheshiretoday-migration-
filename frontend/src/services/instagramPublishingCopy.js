const LOCALITY_HASHTAGS = Object.freeze({
  wilmslow: '#Wilmslow',
  knutsford: '#Knutsford',
  chester: '#Chester',
  crewe: '#Crewe',
  macclesfield: '#Macclesfield',
  congleton: '#Congleton',
  warrington: '#Warrington',
  northwich: '#Northwich',
});
const BASE_HASHTAGS = Object.freeze(['#CheshireToday', '#CheshireNews']);
const CANONICAL_ARTICLE_URL = /^https:\/\/cheshiretoday\.co\.uk\/article\/[0-9a-f]{24}\/[a-z0-9-]+$/i;

export const INSTAGRAM_HASHTAG_MAX = 4;


const exactTitle = title => typeof title === 'string' ? title.trim() : '';


export const buildInstagramStoryCaption = title => {
  const value = exactTitle(title);
  return value ? `${value}\n\nTap the link sticker to read the full story on Cheshire Today.` : '';
};


export const buildInstagramFeedCaption = title => {
  const value = exactTitle(title);
  return value ? `${value}\n\nRead the full story on Cheshire Today.` : '';
};


export const buildInstagramReelCaption = title => {
  const value = exactTitle(title);
  return value ? `${value}\n\nFind the full story on Cheshire Today.` : '';
};


export const buildInstagramHashtags = article => {
  if (!article) return '';
  const tags = [...BASE_HASHTAGS];
  const location = typeof article.location === 'string'
    ? article.location.trim().toLowerCase()
    : '';
  if (LOCALITY_HASHTAGS[location]) tags.push(LOCALITY_HASHTAGS[location]);
  if (article.category === 'Local News') tags.push('#LocalNews');
  return tags.slice(0, INSTAGRAM_HASHTAG_MAX).join(' ');
};


export const buildInstagramStoryPackage = ({ article, canonicalUrl }) => {
  const caption = buildInstagramStoryCaption(article?.title);
  const hashtags = buildInstagramHashtags(article);
  if (!caption || !hashtags || !CANONICAL_ARTICLE_URL.test(String(canonicalUrl || ''))) return '';
  return `${caption}\n\nLink sticker (editor use): ${canonicalUrl}\n\n${hashtags}`;
};


export const buildInstagramFeedPackage = ({ article }) => {
  const caption = buildInstagramFeedCaption(article?.title);
  const hashtags = buildInstagramHashtags(article);
  return caption && hashtags ? `${caption}\n\n${hashtags}` : '';
};


export const buildInstagramReelPackage = ({ article }) => {
  const caption = buildInstagramReelCaption(article?.title);
  const hashtags = buildInstagramHashtags(article);
  return caption && hashtags ? `${caption}\n\n${hashtags}` : '';
};
