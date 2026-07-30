import { getApiUrl } from "../utils/api";

export const recordArticleView = (
  mongoId,
  { fetchImpl = fetch, apiBase = getApiUrl(), isActive = () => true } = {}
) => {
  const cleanId = String(mongoId || "").trim();
  if (!cleanId) return;

  const base = String(apiBase || "").replace(/\/$/, "");
  Promise.resolve()
    .then(() => {
      if (!isActive()) return;
      return fetchImpl(`${base}/api/articles/${encodeURIComponent(cleanId)}/view`, {
        method: "POST",
      });
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
