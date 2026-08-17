import React, { act } from 'react';
import { createRoot } from 'react-dom/client';

import AdminDashboard from './AdminDashboard';


jest.mock('@/lib/utils', () => ({
  cn: (...values) => values.filter(Boolean).join(' '),
}), { virtual: true });

jest.mock('@/components/ui/button', () => ({
  buttonVariants: () => '',
}), { virtual: true });

jest.mock('../hooks/use-toast', () => ({ toast: jest.fn() }));
jest.mock('./admin/SocialPublishingDialog', () => () => null);


const response = (body, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  json: async () => body,
  text: async () => JSON.stringify(body),
});

const makeArticle = (id, title, dates = {}) => ({
  id,
  title,
  summary: `${title} summary`,
  content: `${title} content`,
  category: 'Local News',
  author: 'Cheshire Today',
  source: 'Verified source',
  source_url: 'https://example.com/source',
  image: '',
  tags: [],
  featured: false,
  scope: 'cheshire',
  manual_review_reason: 'Requires editorial review',
  ...dates,
});

const manualReviewArticles = [
  makeArticle('primary', 'Primary dates', {
    publishedDate: '2026-08-15T10:00:00Z',
    created_at: '2026-08-15T10:30:00Z',
    manual_review_created_at: '2026-08-15T11:00:00Z',
  }),
  makeArticle('review-created-fallback', 'Review uses created date', {
    publishedDate: '2026-08-14T08:00:00Z',
    created_at: '2026-08-15T09:15:00Z',
  }),
  makeArticle('review-published-fallback', 'Review uses published date', {
    publishedDate: '2026-08-13T07:30:00Z',
  }),
  makeArticle('published-created-fallback', 'Published uses created date', {
    created_at: '2026-08-12T06:45:00Z',
    manual_review_created_at: '2026-08-12T07:00:00Z',
  }),
  makeArticle('missing', 'All dates missing'),
  makeArticle('malformed', 'Malformed dates', {
    publishedDate: 'not-a-date',
    created_at: 'also-not-a-date',
    manual_review_created_at: 'still-not-a-date',
  }),
];

const flush = async () => {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
};


describe('Admin Manual Review dates', () => {
  let container;
  let root;
  let originalAbortTimeout;
  let originalFetch;
  let originalResizeObserver;
  let originalConsoleLog;

  beforeEach(() => {
    globalThis.IS_REACT_ACT_ENVIRONMENT = true;
    originalAbortTimeout = AbortSignal.timeout;
    originalFetch = global.fetch;
    originalResizeObserver = global.ResizeObserver;
    originalConsoleLog = console.log;
    AbortSignal.timeout = jest.fn(() => undefined);
    global.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
    console.log = jest.fn();
    localStorage.setItem('cheshire_admin_token', 'test-admin-token');
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    global.fetch = jest.fn(async (url) => {
      const path = String(url);
      if (path.includes('/api/admin/articles/manual-review')) {
        return response({ articles: manualReviewArticles, total: manualReviewArticles.length });
      }
      if (path.includes('/api/admin/articles/archived')) {
        return response({ articles: [], total: 0 });
      }
      if (path.includes('/api/admin/archive/stats')) return response({});
      if (path.includes('/api/admin/verify')) return response({ success: true });
      if (path.includes('/api/admin/stats')) return response({ articles: { by_category: {} } });
      if (path.includes('/api/admin/subscribers')) return response({ subscribers: [] });
      if (/\/api\/admin\/articles(?:\?|$)/.test(path)) {
        return response({ articles: [], total: 0 });
      }
      if (path.includes('/api/admin/jobs')) return response({ jobs: [] });
      if (path.includes('/api/jobs/meta/options')) {
        return response({ locations: [], categories: [], job_types: [] });
      }
      return response({});
    });
  });

  afterEach(() => {
    act(() => root.unmount());
    container.remove();
    localStorage.clear();
    AbortSignal.timeout = originalAbortTimeout;
    global.fetch = originalFetch;
    global.ResizeObserver = originalResizeObserver;
    console.log = originalConsoleLog;
    delete globalThis.IS_REACT_ACT_ENVIRONMENT;
    jest.restoreAllMocks();
  });

  const renderManualReview = async () => {
    await act(async () => root.render(<AdminDashboard onBack={jest.fn()} />));
    await flush();
    await act(async () => container.querySelector('[data-testid="tab-archive"]').click());
    await flush();
  };

  test('shows defensive published and review dates without changing the card contract', async () => {
    await renderManualReview();

    expect(container.querySelector('[data-testid="manual-review-published-date-primary"]').textContent)
      .toBe('Published: 15 Aug 2026');
    expect(container.querySelector('[data-testid="manual-review-added-date-primary"]').textContent)
      .toBe('Added to review: 15 Aug 2026 · 12:00');

    expect(container.querySelector('[data-testid="manual-review-added-date-review-created-fallback"]').textContent)
      .toBe('Added to review: 15 Aug 2026 · 10:15');
    expect(container.querySelector('[data-testid="manual-review-added-date-review-published-fallback"]').textContent)
      .toBe('Added to review: 13 Aug 2026 · 08:30');
    expect(container.querySelector('[data-testid="manual-review-published-date-published-created-fallback"]').textContent)
      .toBe('Published: 12 Aug 2026');

    expect(container.querySelector('[data-testid="manual-review-published-date-missing"]').textContent)
      .toBe('Published: Date unavailable');
    expect(container.querySelector('[data-testid="manual-review-added-date-missing"]').textContent)
      .toBe('Added to review: Date unavailable');
    expect(container.querySelector('[data-testid="manual-review-dates-malformed"]').textContent)
      .not.toContain('Invalid Date');
    expect(container.querySelector('[data-testid="manual-review-dates-malformed"]').textContent)
      .toContain('Date unavailable');

    const primaryCard = container.querySelector('[data-testid="manual-review-card-primary"]');
    expect(primaryCard.textContent).toContain('Source');
    expect(primaryCard.textContent).toContain('Edit');
    expect(primaryCard.textContent).toContain('Create OpenAI Draft');
    expect(primaryCard.textContent).toContain('Archive');

    const manualReviewCalls = global.fetch.mock.calls
      .map(([url]) => String(url))
      .filter((url) => url.includes('/api/admin/articles/manual-review'));
    expect(manualReviewCalls).toEqual([
      expect.stringContaining('/api/admin/articles/manual-review?limit=100'),
    ]);

    const renderedTitles = Array.from(container.querySelectorAll('[data-testid^="manual-review-card-"] h4'))
      .map((heading) => heading.textContent);
    expect(renderedTitles).toEqual(manualReviewArticles.map((article) => article.title));
  });
});
