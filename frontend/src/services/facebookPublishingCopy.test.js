import {
  buildFacebookCaption,
  buildFacebookHashtags,
  buildFacebookPackage,
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


test('package requires a title and canonical URL', () => {
  expect(buildFacebookPackage({ article: { ...RUDYS_ARTICLE, title: '' }, canonicalUrl: CANONICAL_URL })).toBe('');
  expect(buildFacebookPackage({ article: RUDYS_ARTICLE, canonicalUrl: '' })).toBe('');
});
