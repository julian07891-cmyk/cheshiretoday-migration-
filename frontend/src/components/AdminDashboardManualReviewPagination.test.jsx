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

const article = (id) => ({
  id,
  title: `Review article ${id}`,
  summary: `Summary ${id}`,
  content: `Content ${id}`,
  category: 'Local News',
  source: 'Verified source',
  source_url: `https://example.com/${id}`,
  publishedDate: '2026-08-24T06:00:00Z',
  manual_review_created_at: '2026-08-24T07:00:00Z',
  manual_review_reason: 'Requires editorial review',
});

const page = (start, count) => Array.from(
  { length: count },
  (_, index) => article(String(start + index).padStart(3, '0')),
);

const deferred = () => {
  let resolve;
  const promise = new Promise((resolvePromise) => {
    resolve = resolvePromise;
  });
  return { promise, resolve };
};

const flush = async () => {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
};


describe('Admin Manual Review pagination', () => {
  let container;
  let root;
  let originalAbortTimeout;
  let originalFetch;
  let originalResizeObserver;
  let originalConsoleLog;
  let originalConsoleError;
  let manualResponses;

  beforeEach(() => {
    globalThis.IS_REACT_ACT_ENVIRONMENT = true;
    originalAbortTimeout = AbortSignal.timeout;
    originalFetch = global.fetch;
    originalResizeObserver = global.ResizeObserver;
    originalConsoleLog = console.log;
    originalConsoleError = console.error;
    AbortSignal.timeout = jest.fn(() => undefined);
    global.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
    console.log = jest.fn();
    console.error = jest.fn();
    localStorage.setItem('cheshire_admin_token', 'test-admin-token');
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    manualResponses = [];

    global.fetch = jest.fn(async (url) => {
      const path = String(url);
      if (path.includes('/api/admin/articles/manual-review')) {
        const nextResponse = manualResponses.shift();
        if (!nextResponse) throw new Error(`Unexpected Manual Review request: ${path}`);
        return typeof nextResponse === 'function' ? nextResponse() : nextResponse;
      }
      if (path.includes('/api/admin/articles/archived')) return response({ articles: [], total: 0 });
      if (path.includes('/api/admin/archive/stats')) return response({});
      if (path.includes('/api/admin/verify')) return response({ success: true });
      if (path.includes('/api/admin/stats')) return response({ articles: { by_category: {} } });
      if (path.includes('/api/admin/subscribers')) return response({ subscribers: [] });
      if (/\/api\/admin\/articles(?:\?|$)/.test(path)) return response({ articles: [], total: 0 });
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
    console.error = originalConsoleError;
    delete globalThis.IS_REACT_ACT_ENVIRONMENT;
    jest.restoreAllMocks();
  });

  const renderManualReview = async () => {
    await act(async () => root.render(<AdminDashboard onBack={jest.fn()} />));
    await flush();
    await act(async () => container.querySelector('[data-testid="tab-archive"]').click());
    await flush();
  };

  const manualReviewCalls = () => global.fetch.mock.calls.filter(
    ([url]) => String(url).includes('/api/admin/articles/manual-review'),
  );

  const renderedIds = () => Array.from(
    container.querySelectorAll('[data-testid^="manual-review-card-"]'),
  ).map((card) => card.getAttribute('data-testid').replace('manual-review-card-', ''));

  test('loads, appends and completes ordered 100-record pages', async () => {
    manualResponses.push(
      response({ articles: page(0, 100), total: 205, skip: 0, limit: 100 }),
      response({ articles: page(100, 100), total: 205, skip: 100, limit: 100 }),
      response({ articles: page(200, 5), total: 205, skip: 200, limit: 100 }),
    );

    await renderManualReview();

    expect(manualReviewCalls()[0][0]).toContain('/manual-review?limit=100&skip=0');
    expect(manualReviewCalls()[0][1].headers.Authorization).toBe('Bearer test-admin-token');
    expect(container.querySelector('[data-testid="manual-review-count"]').textContent)
      .toBe('Showing 100 of 205');
    expect(renderedIds()).toEqual(page(0, 100).map(({ id }) => id));
    expect(container.textContent).toContain('Select loaded');

    const loadMore = container.querySelector('[data-testid="manual-review-load-more"]');
    expect(loadMore.textContent).toContain('Load 100 more');
    expect(loadMore.className).toContain('w-full');
    expect(loadMore.closest('[data-testid^="manual-review-card-"]')).toBeNull();

    await act(async () => loadMore.click());
    await flush();
    expect(manualReviewCalls()[1][0]).toContain('/manual-review?limit=100&skip=100');
    expect(renderedIds()).toEqual(page(0, 200).map(({ id }) => id));
    expect(container.querySelector('[data-testid="manual-review-count"]').textContent)
      .toBe('Showing 200 of 205');

    await act(async () => container.querySelector('[data-testid="manual-review-load-more"]').click());
    await flush();
    expect(manualReviewCalls()[2][0]).toContain('/manual-review?limit=100&skip=200');
    expect(renderedIds()).toEqual(page(0, 205).map(({ id }) => id));
    expect(container.querySelector('[data-testid="manual-review-count"]').textContent)
      .toBe('Showing 205 of 205');
    expect(container.querySelector('[data-testid="manual-review-load-more"]')).toBeNull();

    expect(manualReviewCalls().every(([, options]) => !options.method || options.method === 'GET')).toBe(true);
    const firstCard = container.querySelector('[data-testid="manual-review-card-000"]');
    expect(firstCard.textContent).toContain('Published:');
    expect(firstCard.textContent).toContain('Added to review:');
    expect(firstCard.textContent).toContain('Source');
    expect(firstCard.textContent).toContain('Edit');
    expect(firstCard.textContent).toContain('Create OpenAI Draft');
    expect(firstCard.textContent).toContain('Archive');
  });

  test('deduplicates by id and retries the same failed offset without clearing state', async () => {
    manualResponses.push(
      response({ articles: [article('a'), article('b')], total: 4, skip: 0, limit: 100 }),
      response({ detail: 'Temporary failure' }, 500),
      response({ articles: [article('b'), article('c'), article('d')], total: 4, skip: 2, limit: 100 }),
    );

    await renderManualReview();
    await act(async () => container.querySelector('[data-testid="manual-review-load-more"]').click());
    await flush();

    expect(renderedIds()).toEqual(['a', 'b']);
    expect(container.querySelector('[data-testid="manual-review-count"]').textContent)
      .toBe('Showing 2 of 4');
    const error = container.querySelector('[data-testid="manual-review-load-more-error"]');
    expect(error.textContent).toContain('Temporary failure');

    await act(async () => error.querySelector('button').click());
    await flush();

    expect(manualReviewCalls()[1][0]).toContain('skip=2');
    expect(manualReviewCalls()[2][0]).toContain('skip=2');
    expect(renderedIds()).toEqual(['a', 'b', 'c', 'd']);
    expect(container.querySelector('[data-testid="manual-review-load-more-error"]')).toBeNull();
    expect(container.querySelector('[data-testid="manual-review-count"]').textContent)
      .toBe('Showing 4 of 4');
  });

  test('guards parallel load-more activation and exposes a clear loading state', async () => {
    const pending = deferred();
    manualResponses.push(
      response({ articles: [article('a')], total: 2, skip: 0, limit: 100 }),
      () => pending.promise,
    );

    await renderManualReview();
    const loadMore = container.querySelector('[data-testid="manual-review-load-more"]');

    await act(async () => {
      loadMore.click();
      loadMore.click();
      await Promise.resolve();
    });

    expect(manualReviewCalls()).toHaveLength(2);
    expect(loadMore.disabled).toBe(true);
    expect(loadMore.textContent).toContain('Loading');

    pending.resolve(response({ articles: [article('b')], total: 2, skip: 1, limit: 100 }));
    await flush();
    expect(renderedIds()).toEqual(['a', 'b']);
  });

  test('refresh resets to offset zero and replaces previously appended pages', async () => {
    manualResponses.push(
      response({ articles: [article('a'), article('b')], total: 3, skip: 0, limit: 100 }),
      response({ articles: [article('c')], total: 3, skip: 2, limit: 100 }),
      response({ articles: [article('fresh')], total: 1, skip: 0, limit: 100 }),
    );

    await renderManualReview();
    await act(async () => container.querySelector('[data-testid="manual-review-load-more"]').click());
    await flush();
    expect(renderedIds()).toEqual(['a', 'b', 'c']);

    await act(async () => container.querySelector('[data-testid="manual-review-refresh"]').click());
    await flush();

    expect(manualReviewCalls()[2][0]).toContain('/manual-review?limit=100&skip=0');
    expect(renderedIds()).toEqual(['fresh']);
    expect(container.querySelector('[data-testid="manual-review-count"]').textContent)
      .toBe('Showing 1 of 1');
  });

  test('a successful queue mutation refetches page one', async () => {
    const defaultFetch = global.fetch.getMockImplementation();
    global.fetch.mockImplementation(async (url, options) => {
      if (String(url).includes('/api/admin/articles/a/archive')) {
        return response({ success: true });
      }
      return defaultFetch(url, options);
    });
    manualResponses.push(
      response({ articles: [article('a'), article('b')], total: 2, skip: 0, limit: 100 }),
      response({ articles: [article('b')], total: 1, skip: 0, limit: 100 }),
    );

    await renderManualReview();
    const firstCard = container.querySelector('[data-testid="manual-review-card-a"]');
    const archiveButton = Array.from(firstCard.querySelectorAll('button')).find(
      (button) => button.textContent.trim() === 'Archive',
    );
    await act(async () => archiveButton.click());
    await flush();

    expect(manualReviewCalls()[1][0]).toContain('/manual-review?limit=100&skip=0');
    expect(renderedIds()).toEqual(['b']);
    expect(container.querySelector('[data-testid="manual-review-count"]').textContent)
      .toBe('Showing 1 of 1');
  });

  test('an initial failure is explicit and retryable rather than an empty success', async () => {
    manualResponses.push(
      response({ detail: 'Initial queue failure' }, 500),
      response({ articles: [article('recovered')], total: 1, skip: 0, limit: 100 }),
    );

    await renderManualReview();
    const initialError = container.querySelector('[data-testid="manual-review-initial-error"]');
    expect(initialError.textContent).toContain('Initial queue failure');
    expect(container.textContent).not.toContain('No live manual-review articles');

    await act(async () => initialError.querySelector('button').click());
    await flush();
    expect(manualReviewCalls()[1][0]).toContain('/manual-review?limit=100&skip=0');
    expect(renderedIds()).toEqual(['recovered']);
  });
});
