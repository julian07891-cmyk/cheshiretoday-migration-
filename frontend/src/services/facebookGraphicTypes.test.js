import {
  buildGraphicTypeCaption,
  buildGraphicTypeHashtags,
} from './facebookPublishingCopy';
import { fetchFacebookTypedGraphic } from './facebookSocialAsset';


const ARTICLE = {
  mongo_id: '507f1f77bcf86cd799439011',
  title: 'Cheshire investment creates new skilled jobs',
  location: 'wilmslow',
};


test.each([
  ['business', `${ARTICLE.title}\n\nRead the full business story on Cheshire Today.`],
  ['property', `${ARTICLE.title}\n\nRead the full property story on Cheshire Today.`],
  ['ai-tech', `${ARTICLE.title}\n\nRead the full AI & Tech story on Cheshire Today.`],
  ['breaking-news', `${ARTICLE.title}\n\nLatest verified update from Cheshire Today.`],
  ['event', `${ARTICLE.title}\n\nFind out more on Cheshire Today.`],
])('%s caption is exact and deterministic', (graphicType, expected) => {
  expect(buildGraphicTypeCaption({ graphicType, article: ARTICLE })).toBe(expected);
});


test('approved type hashtags obey locality and maximum contracts', () => {
  expect(buildGraphicTypeHashtags({ graphicType: 'business', article: ARTICLE })).toBe(
    '#CheshireToday #CheshireBusiness #Wilmslow'
  );
  expect(buildGraphicTypeHashtags({ graphicType: 'property', article: ARTICLE })).toBe(
    '#CheshireToday #CheshireProperty #Wilmslow'
  );
  expect(buildGraphicTypeHashtags({ graphicType: 'ai-tech', article: ARTICLE })).toBe(
    '#CheshireToday #AITech #CheshireBusiness'
  );
  expect(buildGraphicTypeHashtags({ graphicType: 'business', article: { ...ARTICLE, location: 'unknown' } }).split(' ').length).toBeLessThanOrEqual(4);
});


test('Quote and Poll captions contain only editor copy and fixed framing', () => {
  expect(buildGraphicTypeCaption({ graphicType: 'quote', quote: 'Verified words', attribution: 'Named source' })).toBe(
    '“Verified words”\n\n— Named source'
  );
  expect(buildGraphicTypeCaption({ graphicType: 'poll', question: 'Your view?', optionA: 'Yes', optionB: 'No' })).toBe(
    'Your view?\n\nA: Yes\nB: No\n\nShare your view in the comments.'
  );
});


test.each(['business', 'property', 'ai-tech', 'breaking-news', 'event'])(
  '%s fetch uses the allow-listed authenticated GET route',
  async graphicType => {
    const blob = new Blob(['<svg/>'], { type: 'image/svg+xml' });
    const fetchImpl = jest.fn().mockResolvedValue({
      ok: true,
      headers: { get: () => 'image/svg+xml' },
      blob: () => Promise.resolve(blob),
    });
    await expect(fetchFacebookTypedGraphic({
      apiUrl: 'https://admin.example/', graphicType, mongoId: ARTICLE.mongo_id,
      token: 'secret', fetchImpl,
    })).resolves.toBe(blob);
    expect(fetchImpl).toHaveBeenCalledWith(
      `https://admin.example/api/admin/social-assets/facebook/article/${graphicType}/${ARTICLE.mongo_id}`,
      expect.objectContaining({ method: 'GET', headers: expect.objectContaining({ Authorization: 'Bearer secret' }) })
    );
  }
);


test('Quote and Poll send only their allow-listed JSON fields', async () => {
  const fetchImpl = jest.fn().mockResolvedValue({
    ok: true,
    headers: { get: () => 'image/svg+xml' },
    blob: () => Promise.resolve(new Blob(['<svg/>'], { type: 'image/svg+xml' })),
  });
  await fetchFacebookTypedGraphic({
    apiUrl: 'https://admin.example', graphicType: 'quote', mongoId: ARTICLE.mongo_id,
    token: 'secret', payload: { quote: 'Verified', attribution: 'Source' }, fetchImpl,
  });
  const [url, options] = fetchImpl.mock.calls[0];
  expect(url).toBe(`https://admin.example/api/admin/social-assets/facebook/quote/${ARTICLE.mongo_id}`);
  expect(options.method).toBe('POST');
  expect(JSON.parse(options.body)).toEqual({ quote: 'Verified', attribution: 'Source' });
  expect(options.body).not.toContain('image');
  expect(options.body).not.toContain('template');
});
