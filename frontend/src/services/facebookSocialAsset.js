import { slugifyArticleTitle } from '../utils/articleUrl';


const MONGO_OBJECT_ID_PATTERN = /^[0-9a-f]{24}$/i;
export const FACEBOOK_GRAPHIC_WIDTH = 1200;
export const FACEBOOK_GRAPHIC_HEIGHT = 630;


export class FacebookSocialAssetError extends Error {
  constructor(status = 500) {
    super('Facebook social asset request failed');
    this.name = 'FacebookSocialAssetError';
    this.status = Number(status) || 500;
  }
}


export const fetchFacebookLocalGraphic = async ({
  apiUrl,
  mongoId,
  token,
  fetchImpl = fetch,
}) => {
  const normalizedId = String(mongoId || '').trim().toLowerCase();
  if (!MONGO_OBJECT_ID_PATTERN.test(normalizedId) || !token) {
    throw new FacebookSocialAssetError(400);
  }

  let response;
  try {
    response = await fetchImpl(
      `${String(apiUrl || '').replace(/\/$/, '')}/api/admin/social-assets/facebook/local-news/${encodeURIComponent(normalizedId)}`,
      {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: 'image/svg+xml',
        },
      }
    );
  } catch (_error) {
    throw new FacebookSocialAssetError(500);
  }

  if (!response.ok) throw new FacebookSocialAssetError(response.status);
  const contentType = String(response.headers?.get?.('content-type') || '').toLowerCase();
  if (!contentType.startsWith('image/svg+xml')) {
    throw new FacebookSocialAssetError(500);
  }
  return response.blob();
};


const waitForBrandFonts = async (documentRef) => {
  if (!documentRef?.fonts) return;
  if (typeof documentRef.fonts.load === 'function') {
    await Promise.all([
      documentRef.fonts.load("700 58px 'Playfair Display'"),
      documentRef.fonts.load("700 23px 'Public Sans'"),
    ]);
  }
  if (documentRef.fonts.ready) await documentRef.fonts.ready;
};


export const rasterizeFacebookSvg = async ({
  svgUrl,
  documentRef = document,
  ImageCtor = Image,
}) => {
  if (!String(svgUrl || '').startsWith('blob:')) {
    throw new FacebookSocialAssetError(500);
  }
  await waitForBrandFonts(documentRef);

  const image = new ImageCtor();
  await new Promise((resolve, reject) => {
    image.onload = resolve;
    image.onerror = () => reject(new FacebookSocialAssetError(500));
    image.src = svgUrl;
  });

  const canvas = documentRef.createElement('canvas');
  canvas.width = FACEBOOK_GRAPHIC_WIDTH;
  canvas.height = FACEBOOK_GRAPHIC_HEIGHT;
  const context = canvas.getContext('2d');
  if (!context) throw new FacebookSocialAssetError(500);
  context.drawImage(image, 0, 0, FACEBOOK_GRAPHIC_WIDTH, FACEBOOK_GRAPHIC_HEIGHT);

  const pngBlob = await new Promise((resolve, reject) => {
    canvas.toBlob(
      blob => blob ? resolve(blob) : reject(new FacebookSocialAssetError(500)),
      'image/png'
    );
  });
  return pngBlob;
};


export const downloadFacebookPng = ({
  pngBlob,
  title,
  documentRef = document,
  urlApi = URL,
  scheduleRevoke = callback => setTimeout(callback, 0),
}) => {
  const filename = `cheshire-today-${slugifyArticleTitle(title)}-facebook.png`;
  const downloadUrl = urlApi.createObjectURL(pngBlob);
  const link = documentRef.createElement('a');
  link.href = downloadUrl;
  link.download = filename;
  link.click();
  scheduleRevoke(() => urlApi.revokeObjectURL(downloadUrl));
  return filename;
};
