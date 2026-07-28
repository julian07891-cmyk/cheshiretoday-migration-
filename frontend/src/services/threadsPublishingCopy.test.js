import {
  THREADS_CONTEXT_MAX,
  THREADS_OPENING_MAX,
  buildThreadsPost,
  validateThreadsContext,
  validateThreadsOpening,
} from './threadsPublishingCopy';


const CANONICAL_URL = 'https://cheshiretoday.co.uk/article/507f1f77bcf86cd799439011/council-investment-supports-new-jobs-in-knutsford';


test('builds the exact native Threads structure with optional verified context', () => {
  expect(buildThreadsPost({
    opening: 'A new Cheshire investment is expected to support local jobs.',
    context: 'The approved plans affect businesses and residents in Knutsford town centre.',
    canonicalUrl: CANONICAL_URL,
  })).toBe(
    `A new Cheshire investment is expected to support local jobs.\n\nThe approved plans affect businesses and residents in Knutsford town centre.\n\n${CANONICAL_URL}`
  );
  expect(buildThreadsPost({
    opening: 'A new Cheshire investment is expected to support local jobs.',
    context: '',
    canonicalUrl: CANONICAL_URL,
  })).toBe(`A new Cheshire investment is expected to support local jobs.\n\n${CANONICAL_URL}`);
});


test('requires a constrained opening and permits constrained optional context', () => {
  expect(validateThreadsOpening('')).toBe('Verified opening line is required.');
  expect(validateThreadsOpening('a'.repeat(THREADS_OPENING_MAX))).toBe('');
  expect(validateThreadsOpening('a'.repeat(THREADS_OPENING_MAX + 1))).toBe(
    'Verified opening line must be 200 characters or fewer.'
  );
  expect(validateThreadsContext('')).toBe('');
  expect(validateThreadsContext('a'.repeat(THREADS_CONTEXT_MAX))).toBe('');
  expect(validateThreadsContext('a'.repeat(THREADS_CONTEXT_MAX + 1))).toBe(
    'Verified context must be 240 characters or fewer.'
  );
});


test.each([
  'Read https://publisher.example.test/story',
  'See www.example.test/story',
  'Visit publisher.co.uk/story',
  '<strong>Important</strong>',
  'This <looks> unsafe',
  'First line\nSecond line',
])('rejects URL or tag-like editor text: %s', value => {
  expect(validateThreadsOpening(value)).toMatch(/plain text without URLs, HTML or line breaks/);
  expect(validateThreadsContext(value)).toMatch(/plain text without URLs, HTML or line breaks/);
  expect(buildThreadsPost({ opening: value, context: '', canonicalUrl: CANONICAL_URL })).toBe('');
});


test('accepts only canonical public Cheshire Today article URLs', () => {
  const opening = 'A verified local update for Cheshire readers.';
  for (const unsafeUrl of [
    'https://publisher.example.test/story',
    'https://cheshiretoday.co.uk/admin/articles/1',
    `${CANONICAL_URL}?token=secret`,
    'https://cheshiretoday.co.uk/newsletter/preferences/token',
  ]) {
    expect(buildThreadsPost({ opening, context: '', canonicalUrl: unsafeUrl })).toBe('');
  }
});


test('adds no hashtags, invented copy or article-side private data', () => {
  const opening = 'A verified local update for Cheshire readers.';
  const context = 'The published article explains the confirmed local impact.';
  const post = buildThreadsPost({ opening, context, canonicalUrl: CANONICAL_URL });
  expect(post).toBe(`${opening}\n\n${context}\n\n${CANONICAL_URL}`);
  expect(post).not.toContain('#');
  expect(post).not.toMatch(/source|image|admin|token/i);
});
