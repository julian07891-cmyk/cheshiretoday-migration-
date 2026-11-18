import React, { act } from 'react';
import { createRoot } from 'react-dom/client';

import AdminDashboard from './AdminDashboard';
import { toast } from '../hooks/use-toast';

jest.mock('@/lib/utils', () => ({ cn: (...values) => values.filter(Boolean).join(' ') }), { virtual: true });
jest.mock('@/components/ui/button', () => ({ buttonVariants: () => '' }), { virtual: true });
jest.mock('../hooks/use-toast', () => ({ toast: jest.fn() }));
jest.mock('./admin/SocialPublishingDialog', () => () => null);

const TOKEN = 'test-admin-token';
const REVIEW = { risk_level: 'high', risk_score: 84, recommended_action: 'needs_manual_review',
  safe_to_keep_live: false, editor_notes: 'New synthetic saved review.' };
const article = (id) => ({
  id, _id: id, title: `Synthetic article ${id}`, summary: 'Synthetic summary',
  content: 'Synthetic body', category: 'Local News', tags: [],
  publishedDate: '2026-11-13T06:00:00Z',
  ai_review_risk_level: 'medium', ai_review_recommended_action: 'review',
  ai_review_result: { editor_notes: 'Earlier synthetic review.' },
});
const response = (body, status = 200) => ({ ok: status >= 200 && status < 300, status,
  json: async () => body, text: async () => JSON.stringify(body) });
const flush = async () => act(async () => {
  await Promise.resolve();
  await Promise.resolve();
});

describe('saved AI risk-review context preservation', () => {
  let container;
  let root;
  let originalFetch;
  let originalAbortTimeout;
  let originalResizeObserver;
  let requests;
  let unexpected;
  let inventory;
  let archived;
  let nextReviews;
  let articleReadFailure;
  let malformedReview;
  let unreadableReview;

  beforeEach(() => {
    jest.useFakeTimers(); // Exercise the existing search debounce, never real sleeps.
    globalThis.IS_REACT_ACT_ENVIRONMENT = true;
    originalFetch = global.fetch;
    originalAbortTimeout = AbortSignal.timeout;
    originalResizeObserver = global.ResizeObserver;
    AbortSignal.timeout = jest.fn(() => undefined);
    global.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
    jest.spyOn(console, 'log').mockImplementation(() => {});
    localStorage.setItem('cheshire_admin_token', TOKEN);
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    requests = [];
    unexpected = [];
    inventory = [article('current')];
    archived = [article('archived'), article('archive-neighbour')];
    nextReviews = [{ ...REVIEW }];
    articleReadFailure = null;
    malformedReview = false;
    unreadableReview = false;

    global.fetch = jest.fn(async (url, options = {}) => {
      const { pathname, searchParams } = new URL(String(url), 'http://localhost');
      const method = options.method || 'GET';
      requests.push({ method, pathname, query: searchParams.toString() });
      if (pathname.startsWith('/api/admin/')
          && options.headers?.Authorization !== `Bearer ${TOKEN}`) {
        unexpected.push('missing synthetic authentication');
        throw new Error('Offline fixture requires Admin authentication');
      }
      const key = `${method} ${pathname}`;
      if (key === 'GET /api/admin/verify') return response({ success: true });
      if (key === 'GET /api/admin/stats') return response({ articles: { total: inventory.length, by_category: {} } });
      if (key === 'GET /api/admin/subscribers') return response({ subscribers: [], total: 0 });
      if (key === 'GET /api/admin/jobs') return response({ jobs: [] });
      if (key === 'GET /api/jobs/meta/options') return response({ locations: [], categories: [], job_types: [] });
      if (key === 'GET /api/admin/articles') {
        if (articleReadFailure === 'network') throw new Error('Synthetic article read failure');
        if (articleReadFailure === 401) return response({ detail: 'Synthetic expiry' }, 401);
        const search = searchParams.get('search') || '';
        const selected = inventory.filter((item) => item.title.includes(search));
        const skip = Number(searchParams.get('skip') || 0);
        const limit = Number(searchParams.get('limit') || 50);
        return response({ articles: selected.slice(skip, skip + limit).map((item) => ({
          ...item, ai_review_result: { ...item.ai_review_result },
        })), total: selected.length });
      }
      if (key === 'GET /api/admin/articles/archived') {
        const search = searchParams.get('search') || '';
        const selected = archived.filter((item) => item.title.includes(search));
        return response({ articles: selected.map((item) => ({
          ...item, ai_review_result: { ...item.ai_review_result },
        })), total: selected.length });
      }
      if (key === 'GET /api/admin/articles/manual-review') return response({ articles: [], total: 0 });
      if (key === 'GET /api/admin/articles/stats') return response({});
      if (method === 'POST' && /^\/api\/admin\/articles\/[^/]+\/ai-review$/.test(pathname)) {
        if (unreadableReview) return { ok: true, status: 200, json: async () => {
          throw new Error('Synthetic unreadable review response');
        } };
        const review = nextReviews.shift();
        if (!review && !malformedReview) {
          unexpected.push('unexpected additional review');
          throw new Error('Unexpected additional synthetic review');
        }
        // Do not mutate inventory or any previously returned article references.
        return response({ success: true, article_id: pathname.split('/')[4],
          review: malformedReview ? null : { ...review } });
      }
      if (key === 'POST /api/admin/articles/archived/openai-rewrite-draft') {
        return response({ success: true, draft: { title: 'Unsaved synthetic draft',
          summary: 'Draft preview', content: 'Draft body', editor_notes: 'Review before saving.' } });
      }
      unexpected.push(key);
      throw new Error('Unexpected offline fixture request');
    });
  });

  afterEach(() => {
    act(() => root.unmount());
    container.remove();
    localStorage.clear();
    global.fetch = originalFetch;
    AbortSignal.timeout = originalAbortTimeout;
    global.ResizeObserver = originalResizeObserver;
    delete globalThis.IS_REACT_ACT_ENVIRONMENT;
    jest.restoreAllMocks();
    jest.useRealTimers();
    expect(unexpected).toEqual([]);
  });

  const click = async (element) => {
    expect(element).not.toBeNull();
    await act(async () => element.click());
    await flush();
  };
  const button = (text) => Array.from(container.querySelectorAll('button'))
    .find((element) => element.textContent.trim() === text);
  const row = (id) => container.querySelector(`[data-testid="article-row-${id}"]`);
  const ids = () => Array.from(container.querySelectorAll('[data-testid^="article-row-"]'))
    .filter((element) => element.hasAttribute('data-testid') && element.getAttribute('data-testid')
      .match(/^article-row-(?:current|searched|neighbour|page-\d+)$/))
    .map((element) => element.getAttribute('data-testid').slice('article-row-'.length));
  const callsAfter = (boundary) => requests.slice(boundary).map(({ method, pathname }) => `${method} ${pathname}`);
  const setInput = async (input, value) => {
    expect(input).not.toBeNull();
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(input, value);
      input.dispatchEvent(new Event('input', { bubbles: true }));
    });
    await flush();
  };
  const renderArticles = async () => {
    await act(async () => root.render(<AdminDashboard onBack={jest.fn()} />));
    await flush();
    await click(container.querySelector('[data-testid="tab-articles"]'));
    await act(async () => jest.advanceTimersByTime(300));
    await flush();
  };
  const reviewArticle = (id) => click(row(id)?.querySelector('button[title="Check with ChatGPT"]'));

  test('preserves active article search, row identity and review display without another list read', async () => {
    inventory = [article('neighbour'), article('searched')];
    await renderArticles();
    await setInput(container.querySelector('[data-testid="admin-article-search"]'), 'searched');
    await act(async () => jest.advanceTimersByTime(300));
    await flush();
    expect(ids()).toEqual(['searched']);
    expect(requests.some(({ query }) => new URLSearchParams(query).get('search') === 'searched')).toBe(true);
    const boundary = requests.length;
    await reviewArticle('searched');
    expect(container.querySelector('[data-testid="admin-article-search"]').value).toBe('searched');
    expect(ids()).toEqual(['searched']);
    expect(row('searched').textContent).toContain(REVIEW.editor_notes);
    expect(row('searched').textContent).toContain(REVIEW.recommended_action);
    expect(row('searched').querySelector('[data-testid="article-row-ai-status-searched"]').textContent).toContain('high');
    expect(callsAfter(boundary)).toEqual(['POST /api/admin/articles/searched/ai-review']);
  });

  test('preserves accumulated pages and the next pagination offset', async () => {
    inventory = Array.from({ length: 101 }, (_, index) => article(`page-${index}`));
    await renderArticles();
    await click(button('Load More Articles'));
    const before = ids();
    expect(before).toEqual(inventory.slice(0, 100).map(({ id }) => id));
    const boundary = requests.length;
    await reviewArticle('page-74');
    expect(ids()).toEqual(before);
    expect(row('page-74').textContent).toContain(REVIEW.editor_notes);
    expect(row('page-0').textContent).toContain('Earlier synthetic review.');
    expect(callsAfter(boundary)).toEqual(['POST /api/admin/articles/page-74/ai-review']);
    await click(button('Load More Articles'));
    const lastRead = requests.filter(({ pathname }) => pathname === '/api/admin/articles').slice(-1)[0];
    expect(new URLSearchParams(lastRead.query).get('skip')).toBe('100');
    expect(ids()).toEqual(inventory.map(({ id }) => id));
    expect(button('Load More Articles')).toBeUndefined();
  });

  test('Archive review preserves its search and separate inventory without reloading subscribers or Articles', async () => {
    await renderArticles();
    await click(container.querySelector('[data-testid="tab-archive"]'));
    const input = container.querySelector('input[placeholder="Search archive by title, article ID, source or URL"]');
    await setInput(input, 'archived');
    await click(button('Search'));
    expect(container.textContent).toContain('1 matching article in archive');
    expect(container.textContent).not.toContain('Synthetic article archive-neighbour');
    const boundary = requests.length;
    await click(container.querySelector('button[title="Run saved ChatGPT risk review"]'));
    expect(input.value).toBe('archived');
    expect(container.textContent).toContain('Synthetic article archived');
    expect(container.textContent).toContain('1 matching article in archive');
    expect(container.querySelector('button[title="Run saved ChatGPT risk review"]')).not.toBeNull();
    expect(callsAfter(boundary)).toEqual(['POST /api/admin/articles/archived/ai-review']);
    await click(container.querySelector('[data-testid="tab-articles"]'));
    expect(ids()).toEqual(['current']);
    expect(row('current').textContent).toContain('Earlier synthetic review.');
  });

  test('repeated saved reviews show the latest result without subscriber reads', async () => {
    const second = { ...REVIEW, risk_level: 'low', risk_score: 9,
      recommended_action: 'keep_live', safe_to_keep_live: true, editor_notes: 'Second synthetic review.' };
    nextReviews.push(second);
    await renderArticles();
    const boundary = requests.length;
    await reviewArticle('current');
    expect(row('current').textContent).toContain(REVIEW.editor_notes);
    await reviewArticle('current');
    expect(row('current').textContent).toContain(second.editor_notes);
    expect(row('current').textContent).toContain(second.recommended_action);
    expect(row('current').textContent).not.toContain(REVIEW.editor_notes);
    expect(row('current').querySelector('[data-testid="article-row-ai-status-current"]').textContent).toContain('low');
    expect(callsAfter(boundary)).toEqual(Array(2).fill('POST /api/admin/articles/current/ai-review'));
  });

  test('a successful saved review does not depend on a failing article-list refresh', async () => {
    await renderArticles();
    articleReadFailure = 'network';
    const boundary = requests.length;
    await reviewArticle('current');
    expect(row('current').textContent).toContain(REVIEW.editor_notes);
    expect(callsAfter(boundary)).toEqual(['POST /api/admin/articles/current/ai-review']);
    expect(toast).toHaveBeenCalledWith(expect.objectContaining({ title: '✅ ChatGPT review complete' }));
    expect(toast).not.toHaveBeenCalledWith(expect.objectContaining({ title: 'Error Loading Data' }));
  });

  test.each(['missing saved details', 'unreadable response'])('%s remains explicit and leaves earlier article data intact', async (kind) => {
    await renderArticles();
    malformedReview = kind === 'missing saved details';
    unreadableReview = kind === 'unreadable response';
    const boundary = requests.length;
    await reviewArticle('current');
    expect(row('current').textContent).toContain('Earlier synthetic review.');
    expect(row('current').textContent).not.toContain(REVIEW.editor_notes);
    expect(toast).toHaveBeenCalledWith(expect.objectContaining({ title: '❌ ChatGPT review failed', variant: 'destructive' }));
    expect(toast).not.toHaveBeenCalledWith(expect.objectContaining({ title: '✅ ChatGPT review complete' }));
    expect(callsAfter(boundary)).toEqual(['POST /api/admin/articles/current/ai-review']);
  });

  test('article-read session expiry on explicit full refresh still clears authentication after a saved review', async () => {
    await renderArticles();
    await reviewArticle('current');
    articleReadFailure = 401;
    const boundary = requests.length;
    await click(container.querySelector('[data-testid="admin-refresh-button"]'));
    expect(callsAfter(boundary)).toContain('GET /api/admin/subscribers');
    expect(localStorage.getItem('cheshire_admin_token')).toBeNull();
    expect(container.querySelector('[data-testid="admin-login-username"]')).not.toBeNull();
    expect(toast).toHaveBeenCalledWith(expect.objectContaining({ title: 'Session Expired' }));
  });

  test('Archive draft rewriting remains unsaved and distinct from saved risk review', async () => {
    await renderArticles();
    await click(container.querySelector('[data-testid="tab-archive"]'));
    const boundary = requests.length;
    await click(container.querySelector('button[title="Rewrite with OpenAI and open draft editor"]'));
    expect(document.querySelector('[data-testid="admin-article-editor-dialog"]')).not.toBeNull();
    expect(document.querySelector('[data-testid="article-title-input"]').value).toBe('Unsaved synthetic draft');
    expect(callsAfter(boundary)).toEqual(['POST /api/admin/articles/archived/openai-rewrite-draft']);
  });
});
