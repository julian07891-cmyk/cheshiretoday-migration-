import { slugifyArticleTitle } from '../utils/articleUrl';


const MONGO_OBJECT_ID_PATTERN = /^[0-9a-f]{24}$/i;
export const INSTAGRAM_STORY_WIDTH = 1080;
export const INSTAGRAM_STORY_HEIGHT = 1920;
export const INSTAGRAM_FORMATS = Object.freeze([
  Object.freeze({ platform: 'instagram', format: 'story', layout: 'top-story' }),
]);


export class InstagramSocialAssetError extends Error {
  constructor(status = 500) {
    super('Instagram social asset request failed');
    this.name = 'InstagramSocialAssetError';
    this.status = Number(status) || 500;
  }
}


export const fetchInstagramTopStory = async ({
  apiUrl,
  mongoId,
  token,
  fetchImpl = fetch,
}) => {
  const normalizedId = String(mongoId || '').trim().toLowerCase();
  if (!MONGO_OBJECT_ID_PATTERN.test(normalizedId) || !token) {
    throw new InstagramSocialAssetError(400);
  }
  let response;
  try {
    response = await fetchImpl(
      `${String(apiUrl || '').replace(/\/$/, '')}/api/admin/social-assets/instagram/story/${encodeURIComponent(normalizedId)}`,
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


export const rasterizeInstagramStorySvg = async ({
  svgUrl,
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
  canvas.width = INSTAGRAM_STORY_WIDTH;
  canvas.height = INSTAGRAM_STORY_HEIGHT;
  const context = canvas.getContext('2d');
  if (!context) throw new InstagramSocialAssetError(500);
  context.drawImage(image, 0, 0, INSTAGRAM_STORY_WIDTH, INSTAGRAM_STORY_HEIGHT);
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      blob => blob ? resolve(blob) : reject(new InstagramSocialAssetError(500)),
      'image/png'
    );
  });
};


export const downloadInstagramStoryPng = ({
  pngBlob,
  title,
  documentRef = document,
  urlApi = URL,
  scheduleRevoke = callback => setTimeout(callback, 0),
}) => {
  const filename = `cheshire-today-${slugifyArticleTitle(title)}-instagram-story.png`;
  const downloadUrl = urlApi.createObjectURL(pngBlob);
  const link = documentRef.createElement('a');
  link.href = downloadUrl;
  link.download = filename;
  link.click();
  scheduleRevoke(() => urlApi.revokeObjectURL(downloadUrl));
  return filename;
};
