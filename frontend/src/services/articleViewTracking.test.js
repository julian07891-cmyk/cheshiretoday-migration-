import { loadPublicArticle, recordArticleView } from "./articleViewTracking";


test("successful article load records one view using the returned Mongo ID", async () => {
  const article = { id: "64b000000000000000000001", title: "Public article" };
  const fetchImpl = jest
    .fn()
    .mockResolvedValueOnce({ ok: true, json: async () => article })
    .mockResolvedValueOnce({ ok: true });

  await expect(
    loadPublicArticle("legacy-route-id", { fetchImpl, apiBase: "https://example.test" })
  ).resolves.toEqual(article);
  await Promise.resolve();

  expect(fetchImpl).toHaveBeenNthCalledWith(
    1,
    "https://example.test/api/articles/legacy-route-id"
  );
  expect(fetchImpl).toHaveBeenNthCalledWith(
    2,
    "https://example.test/api/articles/64b000000000000000000001/view",
    { method: "POST" }
  );
});


test("failed article load sends no view request", async () => {
  const fetchImpl = jest.fn().mockResolvedValue({ ok: false, status: 404 });

  await expect(
    loadPublicArticle("missing", { fetchImpl, apiBase: "https://example.test" })
  ).rejects.toThrow("HTTP 404");

  expect(fetchImpl).toHaveBeenCalledTimes(1);
});


test("analytics failure never rejects or delays a successful article load", async () => {
  const article = { id: "64b000000000000000000000002", title: "Public article" };
  const fetchImpl = jest
    .fn()
    .mockResolvedValueOnce({ ok: true, json: async () => article })
    .mockRejectedValueOnce(new Error("analytics unavailable"));

  await expect(
    loadPublicArticle("article-id", { fetchImpl, apiBase: "https://example.test" })
  ).resolves.toEqual(article);
  await Promise.resolve();

  expect(fetchImpl).toHaveBeenCalledTimes(2);
});


test("article response completed after page cleanup sends no view request", async () => {
  const article = { id: "64b000000000000000000000003", title: "Public article" };
  const fetchImpl = jest.fn().mockResolvedValue({ ok: true, json: async () => article });

  await expect(
    loadPublicArticle("article-id", {
      fetchImpl,
      apiBase: "https://example.test",
      isActive: () => false,
    })
  ).resolves.toEqual(article);

  expect(fetchImpl).toHaveBeenCalledTimes(1);
});


test("cleanup before the scheduled analytics task prevents a stale view request", async () => {
  let active = true;
  const fetchImpl = jest.fn();

  recordArticleView("64b000000000000000000000004", {
    fetchImpl,
    apiBase: "https://example.test",
    isActive: () => active,
  });
  active = false;
  await Promise.resolve();

  expect(fetchImpl).not.toHaveBeenCalled();
});


test("navigation records only the currently active successfully loaded article", async () => {
  let resolveArticleA;
  const articleAResponse = new Promise((resolve) => {
    resolveArticleA = resolve;
  });
  const articleB = { id: "64b00000000000000000000000b", title: "Article B" };
  const fetchImpl = jest
    .fn()
    .mockReturnValueOnce(articleAResponse)
    .mockResolvedValueOnce({ ok: true, json: async () => articleB })
    .mockResolvedValue({ ok: true });
  let articleAActive = true;

  const articleALoad = loadPublicArticle("article-a", {
    fetchImpl,
    apiBase: "https://example.test",
    isActive: () => articleAActive,
  });
  articleAActive = false;
  await expect(
    loadPublicArticle("article-b", {
      fetchImpl,
      apiBase: "https://example.test",
    })
  ).resolves.toEqual(articleB);
  await Promise.resolve();

  resolveArticleA({
    ok: true,
    json: async () => ({
      id: "64b00000000000000000000000a",
      title: "Article A",
    }),
  });
  await articleALoad;
  await Promise.resolve();

  const viewRequests = fetchImpl.mock.calls.filter(([url]) => url.endsWith("/view"));
  expect(viewRequests).toEqual([
    [
      "https://example.test/api/articles/64b00000000000000000000000b/view",
      { method: "POST" },
    ],
  ]);
});


test("missing resolved Mongo ID does not send an analytics request", () => {
  const fetchImpl = jest.fn();

  recordArticleView("", { fetchImpl, apiBase: "https://example.test" });

  expect(fetchImpl).not.toHaveBeenCalled();
});
