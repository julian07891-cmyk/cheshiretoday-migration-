import {
  FACEBOOK_GRAPHIC_HEIGHT,
  FACEBOOK_GRAPHIC_WIDTH,
  FacebookSocialAssetError,
  downloadFacebookPng,
  fetchFacebookLocalGraphic,
  rasterizeFacebookSvg,
} from './facebookSocialAsset';


test('requests only the Mongo ID with Admin authentication', async () => {
  const blob = new Blob(['<svg/>'], { type: 'image/svg+xml' });
  const fetchImpl = jest.fn().mockResolvedValue({
    ok: true,
    headers: { get: () => 'image/svg+xml' },
    blob: async () => blob,
  });
  await expect(fetchFacebookLocalGraphic({
    apiUrl: 'https://admin.example',
    mongoId: '507f1f77bcf86cd799439011',
    token: 'admin-token',
    fetchImpl,
  })).resolves.toBe(blob);
  expect(fetchImpl).toHaveBeenCalledWith(
    'https://admin.example/api/admin/social-assets/facebook/local-news/507f1f77bcf86cd799439011',
    {
      method: 'GET',
      headers: { Authorization: 'Bearer admin-token', Accept: 'image/svg+xml' },
    }
  );
  expect(fetchImpl.mock.calls[0][1]).not.toHaveProperty('body');
});


test.each([400, 404, 422, 500])('returns only a safe status for %s', async status => {
  const fetchImpl = jest.fn().mockResolvedValue({ ok: false, status });
  await expect(fetchFacebookLocalGraphic({
    apiUrl: 'https://admin.example',
    mongoId: '507f1f77bcf86cd799439011',
    token: 'admin-token',
    fetchImpl,
  })).rejects.toEqual(new FacebookSocialAssetError(status));
});


test('waits for brand fonts and rasterises at exactly 1200 by 630', async () => {
  const drawImage = jest.fn();
  const pngBlob = new Blob(['png'], { type: 'image/png' });
  const canvas = {
    width: 0,
    height: 0,
    getContext: jest.fn(() => ({ drawImage })),
    toBlob: jest.fn(callback => callback(pngBlob)),
  };
  const fonts = {
    load: jest.fn().mockResolvedValue([]),
    ready: Promise.resolve(),
  };
  const documentRef = { fonts, createElement: jest.fn(() => canvas) };
  class FakeImage {
    set src(value) {
      this.source = value;
      this.onload();
    }
  }

  await expect(rasterizeFacebookSvg({
    svgUrl: 'blob:svg-preview',
    documentRef,
    ImageCtor: FakeImage,
  })).resolves.toBe(pngBlob);
  expect(fonts.load).toHaveBeenCalledTimes(2);
  expect(canvas.width).toBe(FACEBOOK_GRAPHIC_WIDTH);
  expect(canvas.height).toBe(FACEBOOK_GRAPHIC_HEIGHT);
  expect(drawImage).toHaveBeenCalledWith(expect.any(FakeImage), 0, 0, 1200, 630);
  expect(canvas.toBlob).toHaveBeenCalledWith(expect.any(Function), 'image/png');
});


test('downloads a deterministic PNG filename and revokes its object URL', () => {
  const link = { click: jest.fn() };
  const documentRef = { createElement: jest.fn(() => link) };
  const urlApi = {
    createObjectURL: jest.fn(() => 'blob:png-download'),
    revokeObjectURL: jest.fn(),
  };
  const scheduleRevoke = jest.fn(callback => callback());
  const filename = downloadFacebookPng({
    pngBlob: new Blob(['png'], { type: 'image/png' }),
    title: 'New Jobs & Investment in Knutsford',
    documentRef,
    urlApi,
    scheduleRevoke,
  });
  expect(filename).toBe('cheshire-today-new-jobs-investment-in-knutsford-facebook.png');
  expect(link.download).toBe(filename);
  expect(link.href).toBe('blob:png-download');
  expect(link.click).toHaveBeenCalledTimes(1);
  expect(scheduleRevoke).toHaveBeenCalledTimes(1);
  expect(urlApi.revokeObjectURL).toHaveBeenCalledWith('blob:png-download');
});
