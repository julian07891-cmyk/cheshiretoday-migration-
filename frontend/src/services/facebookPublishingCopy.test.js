import {
  buildFacebookCaption,
  buildFacebookCampaignUrl,
  buildFacebookHashtags,
  buildFacebookPackage,
  buildNewsletterFacebookPost,
  NEWSLETTER_CAPTION,
  NEWSLETTER_HASHTAGS,
  NEWSLETTER_URL,
} from './facebookPublishingCopy';


const RUDYS_ARTICLE = {
  title: 'Plans submitted to turn former Wilmslow Barclays bank into Rudy’s Neapolitan Pizza',
  category: 'Local News',
  location: 'wilmslow',
};
const CANONICAL_URL = 'https://cheshiretoday.co.uk/article/507f1f77bcf86cd799439011/plans-submitted-to-turn-former-wilmslow-barclays-bank-into-rudys-neapolitan-pizza';


test('caption preserves the exact title and adds only the fixed CTA sentence', () => {
  expect(buildFacebookCaption(RUDYS_ARTICLE.title)).toBe(
    `${RUDYS_ARTICLE.title}\n\nRead the full story on Cheshire Today.`
  );
  expect(buildFacebookCaption('')).toBe('');
});


test('hashtags use the approved base, stored locality and Local News set', () => {
  const hashtags = buildFacebookHashtags(RUDYS_ARTICLE);
  expect(hashtags).toBe('#CheshireToday #CheshireNews #Wilmslow #LocalNews');
  expect(hashtags.split(' ')).toHaveLength(4);
});


test.each([undefined, '', 'cheshire', 'unsupported-town'])(
  'unknown or missing stored location %s adds no locality hashtag',
  location => {
    expect(buildFacebookHashtags({ ...RUDYS_ARTICLE, location })).toBe(
      '#CheshireToday #CheshireNews #LocalNews'
    );
  }
);


test('does not infer a locality from the headline', () => {
  expect(buildFacebookHashtags({ ...RUDYS_ARTICLE, location: undefined })).not.toContain('#Wilmslow');
});


test('package ordering and blank-line spacing are exact', () => {
  expect(buildFacebookPackage({ article: RUDYS_ARTICLE, canonicalUrl: CANONICAL_URL })).toBe(
    `${RUDYS_ARTICLE.title}\n\nRead the full story on Cheshire Today.\n\n${CANONICAL_URL}\n\n#CheshireToday #CheshireNews #Wilmslow #LocalNews`
  );
});


test('Facebook campaign URL is deterministic and removes arbitrary query or fragment data', () => {
  const tracked = buildFacebookCampaignUrl(`${CANONICAL_URL}?private=value#fragment`);
  expect(tracked).toBe(
    `${CANONICAL_URL}?utm_source=facebook&utm_medium=social&utm_campaign=social_publishing`
  );
  expect(tracked).not.toContain('private=value');
  expect(tracked).not.toContain('#fragment');
  expect(CANONICAL_URL).not.toContain('?');
});


test('Facebook campaign URL rejects non-Cheshire Today and malformed destinations', () => {
  expect(buildFacebookCampaignUrl('https://publisher.example/article')).toBe('');
  expect(buildFacebookCampaignUrl('not a URL')).toBe('');
});


test('package requires a title and canonical URL', () => {
  expect(buildFacebookPackage({ article: { ...RUDYS_ARTICLE, title: '' }, canonicalUrl: CANONICAL_URL })).toBe('');
  expect(buildFacebookPackage({ article: RUDYS_ARTICLE, canonicalUrl: '' })).toBe('');
});


test('Newsletter Facebook post is fixed and article independent', () => {
  expect(buildNewsletterFacebookPost()).toBe(
    `${NEWSLETTER_CAPTION}\n\n${NEWSLETTER_URL}\n\n${NEWSLETTER_HASHTAGS}`
  );
  expect(buildNewsletterFacebookPost()).toBe(
    "Get Cheshire’s latest local, business, property and AI & Tech stories delivered to your inbox.\n\nSign up free to the Cheshire Today newsletter.\n\nhttps://cheshiretoday.co.uk/newsletter\n\n#CheshireToday #CheshireNews #Newsletter"
  );
});
