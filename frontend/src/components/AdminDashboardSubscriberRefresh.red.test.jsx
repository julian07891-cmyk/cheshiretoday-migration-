import React, { act } from 'react';
import { createRoot } from 'react-dom/client';

import AdminDashboard from './AdminDashboard';
import { toast } from '../hooks/use-toast';

jest.mock('@/lib/utils', () => ({
  cn: (...values) => values.filter(Boolean).join(' '),
}), { virtual: true });
jest.mock('@/components/ui/button', () => ({ buttonVariants: () => '' }), { virtual: true });
jest.mock('../hooks/use-toast', () => ({ toast: jest.fn() }));
jest.mock('./admin/SocialPublishingDialog', () => () => null);

// Reuse the real-dashboard createRoot/act harness used by the existing Admin tests.
// All data and authentication below are synthetic; unexpected requests fail closed.
const TOKEN = 'test-admin-token';
const SUBSCRIBERS = '/api/admin/subscribers';
const MANAGEMENT_ID = '11111111-1111-4111-8111-111111111111';
const ARTICLE_ID = 'synthetic-saved-risk-review';
const REVIEW = `/api/admin/articles/${ARTICLE_ID}/ai-review`;
const SAVED_REVIEW = {
  risk_level: 'high',
  recommended_action: 'needs_manual_review',
  editor_notes: 'Synthetic saved risk-review result.',
};
const ARTICLE = {
  id: ARTICLE_ID,
  _id: ARTICLE_ID,
  title: 'Synthetic Cheshire business article',
  summary: 'Synthetic preview',
  content: 'Synthetic article body',
  category: 'Local News',
  publishedDate: '2026-11-13T06:00:00Z',
  source: 'Synthetic source',
  source_url: 'https://example.invalid/source',
  tags: [],
  ai_review_risk_level: 'medium',
  ai_review_recommended_action: 'review',
  ai_review_result: { editor_notes: 'Earlier synthetic review.' },
};
const response = (body, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  json: async () => body,
  text: async () => JSON.stringify(body),
});
const flush = async () => act(async () => {
  await Promise.resolve();
  await Promise.resolve();
});

describe('Admin saved-risk-review subscriber refresh contract (RED)', () => {
  let container;
  let root;
  let originalFetch;
  let originalAbortTimeout;
  let originalResizeObserver;
  let requests;
  let unexpectedRequests;
  let savedReview;
  let reviewStatus;
  let subscriberStatus;
  let subscriberActive;

  beforeEach(() => {
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
    jest.spyOn(window, 'confirm').mockReturnValue(true);
    localStorage.setItem('cheshire_admin_token', TOKEN);
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    requests = [];
    unexpectedRequests = [];
    savedReview = null;
    reviewStatus = 200;
    subscriberStatus = 200;
    subscriberActive = true;

    global.fetch = jest.fn(async (url, options = {}) => {
      const { pathname } = new URL(String(url), 'http://localhost');
      const method = options.method || 'GET';
      const request = `${method} ${pathname}`;
      requests.push(request);
      if (pathname.startsWith('/api/admin/')
          && options.headers?.Authorization !== `Bearer ${TOKEN}`) {
        unexpectedRequests.push(`Unauthenticated ${request}`);
        throw new Error('Offline fixture requires Admin authentication');
      }
      if (request === 'GET /api/admin/verify') return response({ success: true });
      if (request === 'GET /api/admin/stats') {
        return response({
          articles: { total: 1, by_category: { 'Local News': 1 } },
          subscribers: { total: 1 },
        });
      }
      if (request === `GET ${SUBSCRIBERS}`) {
        return response({ subscribers: [{
          email: 'reader@example.invalid',
          newsletter_management_id: MANAGEMENT_ID,
          active: subscriberActive,
          subscribed_at: '2026-01-01T09:00:00Z',
        }], total: 1 }, subscriberStatus);
      }
      if (request === 'GET /api/admin/articles') {
        // Never mutate a previously returned article: fresh UI evidence must come
        // from a later read or the actual POST response, not fixture aliasing.
        return response({ articles: [{
          ...ARTICLE,
          ...(savedReview ? {
            ai_review_risk_level: savedReview.risk_level,
            ai_review_recommended_action: savedReview.recommended_action,
            ai_review_result: { ...savedReview },
          } : { ai_review_result: { ...ARTICLE.ai_review_result } }),
        }], total: 1 });
      }
      if (request === 'GET /api/admin/jobs') return response({ jobs: [] });
      if (request === 'GET /api/jobs/meta/options') {
        return response({ locations: [], categories: [], job_types: [] });
      }
      if (request === `POST ${REVIEW}`) {
        if (reviewStatus !== 200) return response({ detail: 'Synthetic review refused' }, reviewStatus);
        savedReview = { ...SAVED_REVIEW };
        return response({ success: true, article_id: ARTICLE_ID, review: { ...savedReview } });
      }
      if (request === `POST ${SUBSCRIBERS}/${MANAGEMENT_ID}/unsubscribe`) {
        subscriberActive = false;
        return response({ success: true, active: false, newsletter_management_id: MANAGEMENT_ID });
      }
      unexpectedRequests.push(request);
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
    expect(unexpectedRequests).toEqual([]);
  });

  const subscriberReads = () => requests.filter((request) => request === `GET ${SUBSCRIBERS}`);
  const click = async (selector) => {
    const element = container.querySelector(selector);
    expect(element).not.toBeNull();
    await act(async () => element.click());
    await flush();
  };
  const renderDashboard = async () => {
    await act(async () => root.render(<AdminDashboard onBack={jest.fn()} />));
    await flush();
    expect(container.querySelector('[data-testid="admin-dashboard-shell"]')).not.toBeNull();
  };
  const renderArticles = async () => {
    await renderDashboard();
    await click('[data-testid="tab-articles"]');
    expect(container.querySelector(`[data-testid="article-row-${ARTICLE_ID}"]`)).not.toBeNull();
  };

  test('initial authenticated dashboard loading requests subscribers', async () => {
    await renderDashboard();
    expect(requests[0]).toBe('GET /api/admin/verify');
    expect(subscriberReads()).toEqual([`GET ${SUBSCRIBERS}`]);
  });

  test('explicit full dashboard refresh still requests subscribers', async () => {
    await renderDashboard();
    const before = subscriberReads().length;
    await click('[data-testid="admin-refresh-button"]');
    expect(subscriberReads()).toHaveLength(before + 1);
  });

  test('successful soft-unsubscribe refreshes subscribers and retains the inactive row', async () => {
    await renderDashboard();
    await click('[data-testid="tab-subscribers"]');
    const before = subscriberReads().length;
    await click(`[data-testid="unsubscribe-subscriber-${MANAGEMENT_ID}"]`);
    expect(window.confirm).toHaveBeenCalledTimes(1);
    expect(requests.filter((request) => request.startsWith('POST '))).toEqual([
      `POST ${SUBSCRIBERS}/${MANAGEMENT_ID}/unsubscribe`,
    ]);
    expect(subscriberReads()).toHaveLength(before + 1);
    const row = container.querySelector('[data-testid="subscriber-row-reader@example.invalid"]');
    expect(row).not.toBeNull();
    expect(row.textContent).toContain('Unsubscribed');
    expect(row.textContent).toContain('Reactivation requires a verified email link.');
  });

  test('successful saved risk review updates article data without reloading subscribers', async () => {
    await renderArticles();
    const boundary = requests.length;
    await click(`[data-testid="article-row-${ARTICLE_ID}"] button[title="Check with ChatGPT"]`);
    expect(requests.slice(boundary).filter((request) => request.startsWith('POST '))).toEqual([
      `POST ${REVIEW}`,
    ]); // Saved risk review, never the separate unsaved rewrite-draft endpoint.
    const row = container.querySelector(`[data-testid="article-row-${ARTICLE_ID}"]`);
    expect(row.querySelector(`[data-testid="article-row-ai-status-${ARTICLE_ID}"]`).textContent)
      .toContain(SAVED_REVIEW.risk_level);
    expect(row.textContent).toContain(SAVED_REVIEW.editor_notes);
    expect(row.textContent).toContain(SAVED_REVIEW.recommended_action);
    // Deliberately RED on fb5fc4b, only after successful fresh-article evidence.
    expect(requests.slice(boundary).filter((request) => request === `GET ${SUBSCRIBERS}`)).toEqual([]);
  });

  test.each([401, 500])('failed saved risk review (%s) stays explicit and does not refresh subscribers', async (status) => {
    await renderArticles();
    reviewStatus = status;
    const boundary = requests.length;
    await click(`[data-testid="article-row-${ARTICLE_ID}"] button[title="Check with ChatGPT"]`);
    expect(requests.slice(boundary)).toEqual([`POST ${REVIEW}`]);
    expect(toast).toHaveBeenCalledWith(expect.objectContaining({
      title: '❌ ChatGPT review failed',
      variant: 'destructive',
    }));
    expect(container.querySelector(`[data-testid="article-row-${ARTICLE_ID}"]`).textContent)
      .toContain(ARTICLE.ai_review_result.editor_notes);
  });

  test('unauthorised full refresh preserves session-expiry handling', async () => {
    await renderDashboard();
    subscriberStatus = 401;
    await click('[data-testid="admin-refresh-button"]');
    expect(localStorage.getItem('cheshire_admin_token')).toBeNull();
    expect(container.querySelector('[data-testid="admin-login-username"]')).not.toBeNull();
    expect(toast).toHaveBeenCalledWith(expect.objectContaining({ title: 'Session Expired' }));
  });
});
