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


export const buildFacebookCaption = title => {
  const exactTitle = typeof title === 'string' ? title : '';
  if (!exactTitle.trim()) return '';
  return `${exactTitle}\n\nRead the full story on Cheshire Today.`;
};


export const buildFacebookHashtags = article => {
  if (!article) return '';
  const hashtags = [...BASE_HASHTAGS];
  const location = typeof article.location === 'string'
    ? article.location.trim().toLowerCase()
    : '';
  if (LOCALITY_HASHTAGS[location]) hashtags.push(LOCALITY_HASHTAGS[location]);
  if (article.category === 'Local News') hashtags.push('#LocalNews');
  return hashtags.slice(0, 4).join(' ');
};


export const buildFacebookPackage = ({ article, canonicalUrl }) => {
  const caption = buildFacebookCaption(article?.title);
  const hashtags = buildFacebookHashtags(article);
  if (!caption || !canonicalUrl || !hashtags) return '';
  return `${caption}\n\n${canonicalUrl}\n\n${hashtags}`;
};
