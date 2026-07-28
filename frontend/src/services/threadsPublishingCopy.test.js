import { buildThreadsPost } from './threadsPublishingCopy';


const CANONICAL_URL = 'https://cheshiretoday.co.uk/article/507f1f77bcf86cd799439011/council-investment-supports-new-jobs-in-knutsford';


test('builds the exact ready-to-paste Threads post from stored article data', () => {
  expect(buildThreadsPost({
    title: 'Council investment supports new jobs in Knutsford',
    canonicalUrl: CANONICAL_URL,
  })).toBe(
    `Council investment supports new jobs in Knutsford\n\nRead the full story on Cheshire Today.\n\n${CANONICAL_URL}`
  );
});


test('accepts only canonical public Cheshire Today article URLs', () => {
  for (const unsafeUrl of [
    'https://publisher.example.test/story',
    'https://cheshiretoday.co.uk/admin/articles/1',
    `${CANONICAL_URL}?token=secret`,
    'https://cheshiretoday.co.uk/newsletter/preferences/token',
  ]) {
    expect(buildThreadsPost({ title: 'Verified local update', canonicalUrl: unsafeUrl })).toBe('');
  }
});


test('adds no hashtags, invented copy or article-side private data', () => {
  const title = 'A verified local update for Cheshire readers';
  const post = buildThreadsPost({ title, canonicalUrl: CANONICAL_URL });
  expect(post).toBe(`${title}\n\nRead the full story on Cheshire Today.\n\n${CANONICAL_URL}`);
  expect(post).not.toContain('#');
  expect(post).not.toMatch(/source|image|admin|token/i);
});
