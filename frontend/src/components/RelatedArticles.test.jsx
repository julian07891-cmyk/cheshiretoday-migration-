import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import RelatedArticles from './RelatedArticles';

let root, container, oldFetch;
const item = { id: 'related-1', title: 'Related story', publishedDate: '2026-10-01' };
beforeEach(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  oldFetch = global.fetch;
  global.fetch = jest.fn();
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
});
afterEach(() => { act(() => root.unmount()); container.remove(); global.fetch = oldFetch; jest.restoreAllMocks(); });
const render = async (id, callback) => act(async () => root.render(
  <RelatedArticles articleId={id} onResultsChange={callback} limit={6} variant="sidebar" onArticleClick={() => {}} />
));

test.each([{ result: [item] }, { result: [] }])('reports selected result $result and preserves single request', async ({ result }) => {
  global.fetch.mockResolvedValue({ ok: true, json: async () => result });
  const report = jest.fn();
  await render('a', report);
  expect(report).toHaveBeenLastCalledWith(result, { articleId: 'a', loading: false });
  expect(global.fetch).toHaveBeenCalledTimes(1);
  expect(global.fetch.mock.calls[0][0]).toContain('/api/related-articles/a?limit=6');
  await render('a', jest.fn());
  expect(global.fetch).toHaveBeenCalledTimes(1);
});
test.each(['network', 'http'])('clears result on %s failure', async kind => {
  jest.spyOn(console, 'error').mockImplementation(() => {});
  if (kind === 'network') global.fetch.mockRejectedValue(new Error('offline'));
  else global.fetch.mockResolvedValue({ ok: false, json: async () => [item] });
  const report = jest.fn();
  await render('a', report);
  expect(report).toHaveBeenLastCalledWith([], { articleId: 'a', loading: false });
  expect(container.textContent).not.toContain(item.title);
});
test('resets on navigation and ignores stale response', async () => {
  let oldResolve, newResolve;
  global.fetch.mockImplementationOnce(() => new Promise(r => { oldResolve = r; }))
    .mockImplementationOnce(() => new Promise(r => { newResolve = r; }));
  const report = jest.fn();
  await render('a', report);
  await render('b', report);
  expect(report).toHaveBeenLastCalledWith([], { articleId: 'b', loading: true });
  await act(async () => oldResolve({ ok: true, json: async () => [item] }));
  expect(report).toHaveBeenLastCalledWith([], { articleId: 'b', loading: true });
  await act(async () => newResolve({ ok: true, json: async () => [] }));
  expect(report).toHaveBeenLastCalledWith([], { articleId: 'b', loading: false });
});
test('optional callback is not required', async () => {
  global.fetch.mockResolvedValue({ ok: true, json: async () => [item] });
  await render('a');
  expect(container.textContent).toContain(item.title);
});

test('unmount prevents late reporting', async () => {
  let resolve;
  global.fetch.mockImplementation(() => new Promise(r => { resolve = r; }));
  const report = jest.fn();
  await render('a', report);
  await act(async () => root.render(null));
  report.mockClear();
  await act(async () => resolve({ ok: true, json: async () => [item] }));
  expect(report).not.toHaveBeenCalled();
});
