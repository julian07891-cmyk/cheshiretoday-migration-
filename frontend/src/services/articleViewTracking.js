import { getApiUrl } from "../utils/api";

export const buildArticleViewAttribution = ({ locationHref, referrer } = {}) => {
  try {
    const pageUrl = new URL(locationHref ?? window.location.href);
    if (
      pageUrl.searchParams.get("utm_source") !== "facebook" ||
      pageUrl.searchParams.get("utm_medium") !== "social" ||
      pageUrl.searchParams.get("utm_campaign") !== "social_publishing"
    ) return null;

    const attribution = {
      utm_source: "facebook",
      utm_medium: "social",
      utm_campaign: "social_publishing",
    };
    const rawReferrer = referrer ?? document.referrer;
    if (rawReferrer) {
      try {
        const hostname = new URL(rawReferrer).hostname;
        if (hostname && hostname.length <= 253) attribution.referrer_hostname = hostname;
      } catch (_error) {}
    }
    return { attribution };
  } catch (_error) {
    return null;
  }
};

export const recordArticleView = (
  mongoId,
  {
    fetchImpl = fetch,
    apiBase = getApiUrl(),
    isActive = () => true,
    locationHref,
    referrer,
  } = {}
) => {
  const cleanId = String(mongoId || "").trim();
  if (!cleanId) return;

  const base = String(apiBase || "").replace(/\/$/, "");
  Promise.resolve()
    .then(() => {
      if (!isActive()) return;
      const attributionBody = buildArticleViewAttribution({ locationHref, referrer });
      const options = {
        method: "POST",
      };
      if (attributionBody) {
        options.headers = { "Content-Type": "application/json" };
        options.body = JSON.stringify(attributionBody);
      }
      return fetchImpl(`${base}/api/articles/${encodeURIComponent(cleanId)}/view`, options);
    })
    .catch(() => {});
};

export const loadPublicArticle = async (
  articleId,
  { fetchImpl = fetch, apiBase = getApiUrl(), isActive = () => true } = {}
) => {
  const base = String(apiBase || "").replace(/\/$/, "");
  const response = await fetchImpl(
    `${base}/api/articles/${encodeURIComponent(articleId)}`
  );
  if (!response.ok) throw new Error(`HTTP ${response.status}`);

  const article = await response.json();
  if (isActive()) {
    recordArticleView(article?.id, { fetchImpl, apiBase: base, isActive });
  }
  return article;
};
