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
export const NEWSLETTER_URL = 'https://cheshiretoday.co.uk/newsletter';
export const NEWSLETTER_CAPTION = "Get Cheshire’s latest local, business, property and AI & Tech stories delivered to your inbox.\n\nSign up free to the Cheshire Today newsletter.";
export const NEWSLETTER_HASHTAGS = '#CheshireToday #CheshireNews #Newsletter';


export const buildFacebookCampaignUrl = canonicalUrl => {
  try {
    const url = new URL(canonicalUrl);
    if (url.protocol !== 'https:' || !['cheshiretoday.co.uk', 'www.cheshiretoday.co.uk'].includes(url.hostname)) return '';
    url.search = '';
    url.hash = '';
    url.searchParams.set('utm_source', 'facebook');
    url.searchParams.set('utm_medium', 'social');
    url.searchParams.set('utm_campaign', 'social_publishing');
    return url.toString();
  } catch (_error) {
    return '';
  }
};


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


export const buildNewsletterFacebookPost = () => (
  `${NEWSLETTER_CAPTION}\n\n${NEWSLETTER_URL}\n\n${NEWSLETTER_HASHTAGS}`
);


const typeCaptionSuffix = Object.freeze({
  business: 'Read the full business story on Cheshire Today.',
  property: 'Read the full property story on Cheshire Today.',
  'ai-tech': 'Read the full AI & Tech story on Cheshire Today.',
  'breaking-news': 'Latest verified update from Cheshire Today.',
  event: 'Find out more on Cheshire Today.',
});


export const buildGraphicTypeCaption = ({ graphicType, article, quote, attribution, question, optionA, optionB }) => {
  if (graphicType === 'quote') {
    if (!String(quote || '').trim() || !String(attribution || '').trim()) return '';
    return `“${String(quote).trim()}”\n\n— ${String(attribution).trim()}`;
  }
  if (graphicType === 'poll') {
    if (![question, optionA, optionB].every(value => String(value || '').trim())) return '';
    return `${String(question).trim()}\n\nA: ${String(optionA).trim()}\nB: ${String(optionB).trim()}\n\nShare your view in the comments.`;
  }
  const title = typeof article?.title === 'string' ? article.title : '';
  const suffix = typeCaptionSuffix[graphicType];
  return title.trim() && suffix ? `${title}\n\n${suffix}` : '';
};


export const buildGraphicTypeHashtags = ({ graphicType, article }) => {
  const location = typeof article?.location === 'string'
    ? LOCALITY_HASHTAGS[article.location.trim().toLowerCase()]
    : '';
  const tags = {
    business: ['#CheshireToday', '#CheshireBusiness'],
    property: ['#CheshireToday', '#CheshireProperty'],
    'ai-tech': ['#CheshireToday', '#AITech', '#CheshireBusiness'],
    'breaking-news': ['#CheshireToday', '#CheshireNews'],
    event: ['#CheshireToday', '#CheshireNews'],
    quote: ['#CheshireToday', '#CheshireNews'],
    poll: ['#CheshireToday', '#CheshireNews'],
  }[graphicType] || [];
  if (location && ['business', 'property'].includes(graphicType)) tags.push(location);
  return tags.slice(0, 4).join(' ');
};
