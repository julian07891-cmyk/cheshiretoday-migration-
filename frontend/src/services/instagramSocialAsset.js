import { slugifyArticleTitle } from '../utils/articleUrl';


const MONGO_OBJECT_ID_PATTERN = /^[0-9a-f]{24}$/i;
export const INSTAGRAM_STORY_WIDTH = 1080;
export const INSTAGRAM_STORY_HEIGHT = 1920;
export const INSTAGRAM_FEED_WIDTH = 1080;
export const INSTAGRAM_FEED_HEIGHT = 1080;
export const INSTAGRAM_REELS_COVER_WIDTH = 1080;
export const INSTAGRAM_REELS_COVER_HEIGHT = 1920;
export const INSTAGRAM_FORMATS = Object.freeze([
  Object.freeze({ platform: 'instagram', format: 'story', layout: 'top-story', route: 'story' }),
  Object.freeze({ platform: 'instagram', format: 'feed', layout: 'local-news', route: 'feed' }),
  Object.freeze({ platform: 'instagram', format: 'reels-cover', layout: 'local-news', route: 'reels-cover' }),
]);


export class InstagramSocialAssetError extends Error {
  constructor(status = 500) {
    super('Instagram social asset request failed');
    this.name = 'InstagramSocialAssetError';
    this.status = Number(status) || 500;
  }
}


const fetchInstagramSvg = async ({
  apiUrl,
  mongoId,
  token,
  format,
  fetchImpl = fetch,
}) => {
  const normalizedId = String(mongoId || '').trim().toLowerCase();
  if (!MONGO_OBJECT_ID_PATTERN.test(normalizedId) || !token) {
    throw new InstagramSocialAssetError(400);
  }
  let response;
  try {
    response = await fetchImpl(
      `${String(apiUrl || '').replace(/\/$/, '')}/api/admin/social-assets/instagram/${format}/${encodeURIComponent(normalizedId)}`,
      {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: 'image/svg+xml',
        },
      }
    );
  } catch (_error) {
    throw new InstagramSocialAssetError(500);
  }
  if (!response.ok) throw new InstagramSocialAssetError(response.status);
  const contentType = String(response.headers?.get?.('content-type') || '').toLowerCase();
  if (!contentType.startsWith('image/svg+xml')) throw new InstagramSocialAssetError(500);
  return response.blob();
};


export const fetchInstagramTopStory = options => fetchInstagramSvg({ ...options, format: 'story' });
export const fetchInstagramFeed = options => fetchInstagramSvg({ ...options, format: 'feed' });
export const fetchInstagramReelsCover = options => fetchInstagramSvg({ ...options, format: 'reels-cover' });


const waitForBrandFonts = async documentRef => {
  if (!documentRef?.fonts) return;
  if (typeof documentRef.fonts.load === 'function') {
    await Promise.all([
      documentRef.fonts.load("700 88px 'Playfair Display'"),
      documentRef.fonts.load("700 28px 'Public Sans'"),
    ]);
  }
  if (documentRef.fonts.ready) await documentRef.fonts.ready;
};


const rasterizeInstagramSvg = async ({
  svgUrl,
  width,
  height,
  documentRef = document,
  ImageCtor = Image,
}) => {
  if (!String(svgUrl || '').startsWith('blob:')) {
    throw new InstagramSocialAssetError(500);
  }
  await waitForBrandFonts(documentRef);
  const image = new ImageCtor();
  await new Promise((resolve, reject) => {
    image.onload = resolve;
    image.onerror = () => reject(new InstagramSocialAssetError(500));
    image.src = svgUrl;
  });
  const canvas = documentRef.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext('2d');
  if (!context) throw new InstagramSocialAssetError(500);
  context.drawImage(image, 0, 0, width, height);
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      blob => blob ? resolve(blob) : reject(new InstagramSocialAssetError(500)),
      'image/png'
    );
  });
};


export const rasterizeInstagramStorySvg = options => rasterizeInstagramSvg({
  ...options, width: INSTAGRAM_STORY_WIDTH, height: INSTAGRAM_STORY_HEIGHT,
});
export const rasterizeInstagramFeedSvg = options => rasterizeInstagramSvg({
  ...options, width: INSTAGRAM_FEED_WIDTH, height: INSTAGRAM_FEED_HEIGHT,
});
export const rasterizeInstagramReelsCoverSvg = options => rasterizeInstagramSvg({
  ...options, width: INSTAGRAM_REELS_COVER_WIDTH, height: INSTAGRAM_REELS_COVER_HEIGHT,
});


const downloadInstagramPng = ({
  pngBlob,
  filename,
  documentRef = document,
  urlApi = URL,
  scheduleRevoke = callback => setTimeout(callback, 0),
}) => {
  const downloadUrl = urlApi.createObjectURL(pngBlob);
  const link = documentRef.createElement('a');
  link.href = downloadUrl;
  link.download = filename;
  link.click();
  scheduleRevoke(() => urlApi.revokeObjectURL(downloadUrl));
  return filename;
};


export const downloadInstagramStoryPng = ({ title, ...options }) => downloadInstagramPng({
  ...options,
  filename: `cheshire-today-${slugifyArticleTitle(title)}-instagram-story.png`,
});
export const downloadInstagramFeedPng = ({ title, ...options }) => downloadInstagramPng({
  ...options,
  filename: `cheshire-today-${slugifyArticleTitle(title)}-instagram-feed.png`,
});
export const downloadInstagramReelsCoverPng = ({ title, ...options }) => downloadInstagramPng({
  ...options,
  filename: `cheshire-today-${slugifyArticleTitle(title)}-instagram-reels-cover.png`,
});
