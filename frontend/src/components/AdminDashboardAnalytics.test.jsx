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
jest.mock('./admin/SocialPublishingDialog', () => ({ article }) => (
  article ? <div data-testid="social-publishing-dialog">{article.title}</div> : null
));


const response = (body, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  json: async () => body,
  text: async () => JSON.stringify(body),
});

const summary = {
  success: true,
  period: 'week',
  article_views: {
    available: true,
    total: 12,
    unique_articles: 2,
    top_articles: [
      {
        id: '64b7f9d4aabbccddeeff0011',
        title: 'Most read public article',
        category: 'Local News',
        views: 8,
      },
      {
        id: '64b7f9d4aabbccddeeff0012',
        title: 'Archived contract violation',
        category: 'Business',
        views: 3,
        archived: true,
      },
      {
        id: '64b7f9d4aabbccddeeff0013',
        title: 'Hidden contract violation',
        category: 'Local News',
        views: 1,
        manual_review_hidden_from_public: true,
      },
    ],
    categories: [
      { category: 'Local News', views: 8, share_percent: 66.7 },
      { category: 'Business', views: 4, share_percent: 33.3 },
    ],
  },
  newsletter: {
    available: true,
    accepted_opportunities: 300,
    send_batches: 2,
    opens: 40,
    clicks: 7,
  },
  sponsored: {
    available: true,
    scope: 'lifetime',
    impressions: 100,
    clicks: 5,
    ctr_percent: 5,
  },
  advertisers: {
    available: true,
    total: 3,
    by_status: [{ status: 'new', count: 3 }],
  },
};


describe('Admin first-party Analytics dashboard', () => {
  let container;
  let root;
  let originalAbortTimeout;
  let originalFetch;
  let analyticsResponder;

  beforeEach(() => {
    globalThis.IS_REACT_ACT_ENVIRONMENT = true;
    originalAbortTimeout = AbortSignal.timeout;
    originalFetch = global.fetch;
    AbortSignal.timeout = jest.fn(() => undefined);
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    localStorage.setItem('cheshire_admin_token', 'test-admin-token');
    analyticsResponder = async () => response(summary);

    global.fetch = jest.fn(async (url) => {
      const path = String(url);
      if (path.includes('/api/admin/verify')) return response({ success: true });
      if (path.includes('/api/admin/stats')) return response({ articles: { by_category: {} } });
      if (path.includes('/api/admin/subscribers')) return response({ subscribers: [] });
      if (path.includes('/api/admin/articles')) return response({ articles: [], total: 0 });
      if (path.includes('/api/admin/jobs')) return response({ jobs: [] });
      if (path.includes('/api/jobs/meta/options')) {
        return response({ locations: [], categories: [], job_types: [] });
      }
      if (path.includes('/api/admin/analytics/summary')) return analyticsResponder(path);
      return response({});
    });
  });

  afterEach(() => {
    act(() => root.unmount());
    container.remove();
    localStorage.clear();
    AbortSignal.timeout = originalAbortTimeout;
    global.fetch = originalFetch;
    delete globalThis.IS_REACT_ACT_ENVIRONMENT;
    jest.restoreAllMocks();
  });

  const renderDashboard = async () => {
    await act(async () => root.render(<AdminDashboard onBack={jest.fn()} />));
  };

  const clickTestId = async (testId) => {
    const target = container.querySelector(`[data-testid="${testId}"]`);
    expect(target).not.toBeNull();
    await act(async () => target.click());
  };

  test('is read-only, defaults to week, and renders verified first-party metrics', async () => {
    await renderDashboard();
    const requestCountBeforeAnalytics = global.fetch.mock.calls.length;
    await clickTestId('tab-analytics');

    const analyticsCalls = global.fetch.mock.calls.slice(requestCountBeforeAnalytics);
    expect(analyticsCalls).toHaveLength(1);
    expect(String(analyticsCalls[0][0])).toContain('/api/admin/analytics/summary?period=week');
    expect(analyticsCalls[0][1]?.method || 'GET').toBe('GET');
    expect(container.querySelector('[data-testid="analytics-period-week"]')?.getAttribute('aria-pressed')).toBe('true');
    expect(container.textContent).toContain('First-party performance across articles, newsletter and commercial activity');
    expect(container.textContent).toContain('Article views');
    expect(container.textContent).toContain('Newsletter opens');
    expect(container.textContent).toContain('Provider-accepted opportunities');
    expect(container.textContent).toContain('Sponsored placement lifetime counters');
    expect(container.textContent).toContain('Advertiser leads created in this period');
    expect(container.textContent).not.toContain('Send Breaking News Alert');
    expect(container.textContent).not.toContain('Facebook Analytics');
    expect(container.textContent).not.toContain('Archived contract violation');
    expect(container.textContent).not.toContain('Hidden contract violation');

    const articleLink = Array.from(container.querySelectorAll('a')).find(
      (link) => link.textContent === 'Most read public article'
    );
    expect(articleLink?.getAttribute('href')).toBe(
      '/article/64b7f9d4aabbccddeeff0011/most-read-public-article'
    );

    const mutatingAnalyticsCalls = analyticsCalls.filter(([, options]) =>
      ['POST', 'PUT', 'PATCH', 'DELETE'].includes(options?.method)
    );
    expect(mutatingAnalyticsCalls).toEqual([]);
    expect(global.fetch).not.toHaveBeenCalledWith(
      expect.stringContaining('/api/facebook/'),
      expect.anything()
    );
    expect(global.fetch).not.toHaveBeenCalledWith(
      expect.stringContaining('/api/push/'),
      expect.anything()
    );
  });

  test('period switching requests only the newly selected analytics period', async () => {
    await renderDashboard();
    await clickTestId('tab-analytics');
    const beforeSwitch = global.fetch.mock.calls.length;

    await clickTestId('analytics-period-month');

    const calls = global.fetch.mock.calls.slice(beforeSwitch);
    expect(calls).toHaveLength(1);
    expect(String(calls[0][0])).toContain('/api/admin/analytics/summary?period=month');
    expect(calls[0][1]?.method || 'GET').toBe('GET');
  });

  test('loading, empty, zero-CTR and endpoint failure states remain distinct', async () => {
    let resolveAnalytics;
    analyticsResponder = () => new Promise((resolve) => {
      resolveAnalytics = resolve;
    });
    await renderDashboard();
    await clickTestId('tab-analytics');

    expect(container.textContent).toContain('Loading analytics…');
    expect(container.textContent).not.toContain('Article views');

    const emptySummary = {
      ...summary,
      article_views: {
        available: true,
        total: 0,
        unique_articles: 0,
        top_articles: [],
        categories: [],
      },
      sponsored: {
        available: true,
        scope: 'lifetime',
        impressions: 0,
        clicks: 0,
        ctr_percent: null,
      },
    };
    await act(async () => resolveAnalytics(response(emptySummary)));
    expect(container.querySelector('[data-testid="analytics-empty"]')).not.toBeNull();
    expect(container.textContent).toContain('No article views were recorded for this period.');
    expect(container.textContent).toContain('CTR');
    expect(container.textContent).toContain('—');

    analyticsResponder = async () => response({ detail: 'private database exception' }, 503);
    await clickTestId('analytics-period-today');
    expect(container.querySelector('[data-testid="analytics-unavailable"]')).not.toBeNull();
    expect(container.textContent).toContain('Analytics are temporarily unavailable.');
    expect(container.textContent).not.toContain('private database exception');
  });
});
