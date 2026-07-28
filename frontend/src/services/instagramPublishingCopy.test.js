import {
  INSTAGRAM_HASHTAG_MAX,
  buildInstagramFeedCaption,
  buildInstagramFeedPackage,
  buildInstagramHashtags,
  buildInstagramReelCaption,
  buildInstagramReelPackage,
  buildInstagramStoryCaption,
  buildInstagramStoryPackage,
} from './instagramPublishingCopy';


const ARTICLE = Object.freeze({
  title: 'Council investment supports new jobs in Knutsford',
  category: 'Local News',
  location: 'knutsford',
  source_url: 'https://publisher.example.test/private-source',
  image: 'https://images.example.test/private-image.jpg',
  admin_url: 'https://cheshiretoday.co.uk/admin/articles/secret',
});
const CANONICAL_URL = 'https://cheshiretoday.co.uk/article/507f1f77bcf86cd799439011/council-investment-supports-new-jobs-in-knutsford';
const HASHTAGS = '#CheshireToday #CheshireNews #Knutsford #LocalNews';


test('builds exact deterministic captions for Story, Feed and Reels', () => {
  expect(buildInstagramStoryCaption(ARTICLE.title)).toBe(
    `${ARTICLE.title}\n\nTap the link sticker to read the full story on Cheshire Today.`
  );
  expect(buildInstagramFeedCaption(ARTICLE.title)).toBe(
    `${ARTICLE.title}\n\nRead the full story on Cheshire Today.`
  );
  expect(buildInstagramReelCaption(ARTICLE.title)).toBe(
    `${ARTICLE.title}\n\nFind the full story on Cheshire Today.`
  );
});


test('uses only approved deterministic hashtags with a maximum of four', () => {
  expect(buildInstagramHashtags(ARTICLE)).toBe(HASHTAGS);
  expect(buildInstagramHashtags(ARTICLE).split(' ')).toHaveLength(INSTAGRAM_HASHTAG_MAX);
  expect(INSTAGRAM_HASHTAG_MAX).toBe(4);
});


test('normalises only approved stored localities and never infers from the headline', () => {
  expect(buildInstagramHashtags({ ...ARTICLE, location: '  MACCLESFIELD ' })).toContain('#Macclesfield');
  expect(buildInstagramHashtags({ ...ARTICLE, location: 'unsupported-town' })).toBe(
    '#CheshireToday #CheshireNews #LocalNews'
  );
  expect(buildInstagramHashtags({ ...ARTICLE, location: '', title: 'Major Knutsford investment' })).not.toContain('#Knutsford');
});


test('Story package identifies the canonical URL as editor-only link-sticker data', () => {
  expect(buildInstagramStoryPackage({ article: ARTICLE, canonicalUrl: CANONICAL_URL })).toBe(
    `${ARTICLE.title}\n\nTap the link sticker to read the full story on Cheshire Today.\n\nLink sticker (editor use): ${CANONICAL_URL}\n\n${HASHTAGS}`
  );
});


test('Feed and Reel packages contain public copy only and no clickable-link claim', () => {
  expect(buildInstagramFeedPackage({ article: ARTICLE })).toBe(
    `${ARTICLE.title}\n\nRead the full story on Cheshire Today.\n\n${HASHTAGS}`
  );
  expect(buildInstagramReelPackage({ article: ARTICLE })).toBe(
    `${ARTICLE.title}\n\nFind the full story on Cheshire Today.\n\n${HASHTAGS}`
  );
  for (const value of [buildInstagramFeedPackage({ article: ARTICLE }), buildInstagramReelPackage({ article: ARTICLE })]) {
    expect(value).not.toMatch(/clickable|link in bio|https?:\/\//i);
  }
});


test('copy output never leaks source, image, Admin, token or private URLs', () => {
  const outputs = [
    buildInstagramStoryPackage({ article: ARTICLE, canonicalUrl: CANONICAL_URL }),
    buildInstagramFeedPackage({ article: ARTICLE }),
    buildInstagramReelPackage({ article: ARTICLE }),
  ];
  for (const output of outputs) {
    expect(output).not.toContain(ARTICLE.source_url);
    expect(output).not.toContain(ARTICLE.image);
    expect(output).not.toContain(ARTICLE.admin_url);
    expect(output).not.toMatch(/token=|\/preferences|\/reactivate|\/unsubscribe/i);
  }
});


test('rejects missing titles and unsafe canonical URLs safely', () => {
  for (const builder of [buildInstagramStoryCaption, buildInstagramFeedCaption, buildInstagramReelCaption]) {
    expect(builder('')).toBe('');
    expect(builder(undefined)).toBe('');
  }
  expect(buildInstagramHashtags(null)).toBe('');
  expect(buildInstagramStoryPackage({ article: ARTICLE, canonicalUrl: 'https://publisher.example.test/story' })).toBe('');
  expect(buildInstagramStoryPackage({ article: ARTICLE, canonicalUrl: 'https://cheshiretoday.co.uk/admin/article/1' })).toBe('');
  expect(buildInstagramStoryPackage({ article: ARTICLE, canonicalUrl: `${CANONICAL_URL}?token=secret` })).toBe('');
});


test('module exposes no mutable hashtag registry', async () => {
  const exports = await import('./instagramPublishingCopy');
  expect(Object.keys(exports)).not.toContain('LOCALITY_HASHTAGS');
  expect(Object.keys(exports)).not.toContain('BASE_HASHTAGS');
});
