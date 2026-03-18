export function slugifyArticleTitle(title) {
  const raw = String(title || "").toLowerCase();
  const slug = raw.replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  return (slug || "article").slice(0, 80);
}

export function buildArticleUrl(article) {
  if (!article) return "/";

  const id = article.id || article._id;
  if (!id) return "/";

  const slug = slugifyArticleTitle(article.title || "");
  return `/article/${encodeURIComponent(id)}/${encodeURIComponent(slug)}`;
}
