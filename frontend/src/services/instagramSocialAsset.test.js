import {
  INSTAGRAM_FEED_HEIGHT,
  INSTAGRAM_FEED_WIDTH,
  INSTAGRAM_REELS_COVER_HEIGHT,
  INSTAGRAM_REELS_COVER_WIDTH,
  INSTAGRAM_STORY_HEIGHT,
  INSTAGRAM_STORY_WIDTH,
  InstagramSocialAssetError,
  downloadInstagramFeedPng,
  downloadInstagramReelsCoverPng,
  downloadInstagramStoryPng,
  fetchInstagramFeed,
  fetchInstagramReelsCover,
  fetchInstagramTopStory,
  rasterizeInstagramFeedSvg,
  rasterizeInstagramReelsCoverSvg,
  rasterizeInstagramStorySvg,
} from './instagramSocialAsset';


test('requests the narrow authenticated Story route using only the Mongo ID', async () => {
  const blob = new Blob(['<svg/>'], { type: 'image/svg+xml' });
  const fetchImpl = jest.fn().mockResolvedValue({
    ok: true,
    headers: { get: () => 'image/svg+xml' },
    blob: async () => blob,
  });
  await expect(fetchInstagramTopStory({
    apiUrl: 'https://admin.example',
    mongoId: '507f1f77bcf86cd799439011',
    token: 'admin-token',
    fetchImpl,
  })).resolves.toBe(blob);
  expect(fetchImpl).toHaveBeenCalledWith(
    'https://admin.example/api/admin/social-assets/instagram/story/507f1f77bcf86cd799439011',
    {
      method: 'GET',
      headers: { Authorization: 'Bearer admin-token', Accept: 'image/svg+xml' },
    }
  );
  expect(fetchImpl.mock.calls[0][1]).not.toHaveProperty('body');
  expect(fetchImpl.mock.calls[0][0]).not.toMatch(/title|image|template|svg/i);
});


test.each([
  ['Feed', fetchInstagramFeed, 'feed'],
  ['Reels Cover', fetchInstagramReelsCover, 'reels-cover'],
])('requests the narrow authenticated %s route using only the Mongo ID', async (_label, fetcher, route) => {
  const blob = new Blob(['<svg/>'], { type: 'image/svg+xml' });
  const fetchImpl = jest.fn().mockResolvedValue({
    ok: true,
    headers: { get: () => 'image/svg+xml' },
    blob: async () => blob,
  });
  await expect(fetcher({
    apiUrl: 'https://admin.example',
    mongoId: '507f1f77bcf86cd799439011',
    token: 'admin-token',
    fetchImpl,
  })).resolves.toBe(blob);
  expect(fetchImpl).toHaveBeenCalledWith(
    `https://admin.example/api/admin/social-assets/instagram/${route}/507f1f77bcf86cd799439011`,
    {
      method: 'GET',
      headers: { Authorization: 'Bearer admin-token', Accept: 'image/svg+xml' },
    }
  );
  expect(fetchImpl.mock.calls[0][1]).not.toHaveProperty('body');
  expect(fetchImpl.mock.calls[0][0]).not.toMatch(/title|image|template|svg/i);
});


test.each([400, 404, 422, 500])('maps status %s without backend details', async status => {
  const fetchImpl = jest.fn().mockResolvedValue({ ok: false, status });
  await expect(fetchInstagramTopStory({
    apiUrl: 'https://admin.example', mongoId: '507f1f77bcf86cd799439011', token: 'token', fetchImpl,
  })).rejects.toEqual(new InstagramSocialAssetError(status));
});


test('rejects invalid identifiers, missing auth and non-SVG responses', async () => {
  await expect(fetchInstagramTopStory({ mongoId: 'bad', token: 'token' })).rejects.toEqual(new InstagramSocialAssetError(400));
  await expect(fetchInstagramTopStory({ mongoId: '507f1f77bcf86cd799439011', token: '' })).rejects.toEqual(new InstagramSocialAssetError(400));
  const fetchImpl = jest.fn().mockResolvedValue({ ok: true, headers: { get: () => 'text/html' } });
  await expect(fetchInstagramTopStory({
    mongoId: '507f1f77bcf86cd799439011', token: 'token', fetchImpl,
  })).rejects.toEqual(new InstagramSocialAssetError(500));
});


test('waits for brand fonts and rasterises at exactly 1080 by 1920', async () => {
  const drawImage = jest.fn();
  const pngBlob = new Blob(['png'], { type: 'image/png' });
  const canvas = {
    width: 0, height: 0,
    getContext: jest.fn(() => ({ drawImage })),
    toBlob: jest.fn(callback => callback(pngBlob)),
  };
  const fonts = { load: jest.fn().mockResolvedValue([]), ready: Promise.resolve() };
  const documentRef = { fonts, createElement: jest.fn(() => canvas) };
  class FakeImage { set src(value) { this.onload(); } }
  await expect(rasterizeInstagramStorySvg({
    svgUrl: 'blob:story-preview', documentRef, ImageCtor: FakeImage,
  })).resolves.toBe(pngBlob);
  expect(fonts.load).toHaveBeenCalledTimes(2);
  expect(canvas.width).toBe(INSTAGRAM_STORY_WIDTH);
  expect(canvas.height).toBe(INSTAGRAM_STORY_HEIGHT);
  expect(drawImage).toHaveBeenCalledWith(expect.any(FakeImage), 0, 0, 1080, 1920);
  expect(canvas.toBlob).toHaveBeenCalledWith(expect.any(Function), 'image/png');
});


test.each([
  ['Feed', rasterizeInstagramFeedSvg, INSTAGRAM_FEED_WIDTH, INSTAGRAM_FEED_HEIGHT],
  ['Reels Cover', rasterizeInstagramReelsCoverSvg, INSTAGRAM_REELS_COVER_WIDTH, INSTAGRAM_REELS_COVER_HEIGHT],
])('rasterises %s at its exact approved dimensions', async (_label, rasterizer, width, height) => {
  const drawImage = jest.fn();
  const pngBlob = new Blob(['png'], { type: 'image/png' });
  const canvas = {
    width: 0, height: 0,
    getContext: jest.fn(() => ({ drawImage })),
    toBlob: jest.fn(callback => callback(pngBlob)),
  };
  const fonts = { load: jest.fn().mockResolvedValue([]), ready: Promise.resolve() };
  const documentRef = { fonts, createElement: jest.fn(() => canvas) };
  class FakeImage { set src(value) { this.onload(); } }
  await expect(rasterizer({
    svgUrl: 'blob:instagram-preview', documentRef, ImageCtor: FakeImage,
  })).resolves.toBe(pngBlob);
  expect(canvas.width).toBe(width);
  expect(canvas.height).toBe(height);
  expect(drawImage).toHaveBeenCalledWith(expect.any(FakeImage), 0, 0, width, height);
});


test('downloads deterministic PNG and revokes its temporary URL', () => {
  const link = { click: jest.fn() };
  const urlApi = { createObjectURL: jest.fn(() => 'blob:png'), revokeObjectURL: jest.fn() };
  expect(downloadInstagramStoryPng({
    pngBlob: new Blob(['png']),
    title: 'Council Jobs & Investment',
    documentRef: { createElement: jest.fn(() => link) },
    urlApi,
    scheduleRevoke: callback => callback(),
  })).toBe('cheshire-today-council-jobs-investment-instagram-story.png');
  expect(link.click).toHaveBeenCalled();
  expect(urlApi.revokeObjectURL).toHaveBeenCalledWith('blob:png');
});


test.each([
  [downloadInstagramFeedPng, 'cheshire-today-council-jobs-investment-instagram-feed.png'],
  [downloadInstagramReelsCoverPng, 'cheshire-today-council-jobs-investment-instagram-reels-cover.png'],
])('downloads the exact format filename and revokes its URL', (downloader, expectedFilename) => {
  const link = { click: jest.fn() };
  const urlApi = { createObjectURL: jest.fn(() => 'blob:png'), revokeObjectURL: jest.fn() };
  expect(downloader({
    pngBlob: new Blob(['png']),
    title: 'Council Jobs & Investment',
    documentRef: { createElement: jest.fn(() => link) },
    urlApi,
    scheduleRevoke: callback => callback(),
  })).toBe(expectedFilename);
  expect(link.click).toHaveBeenCalled();
  expect(urlApi.revokeObjectURL).toHaveBeenCalledWith('blob:png');
});
