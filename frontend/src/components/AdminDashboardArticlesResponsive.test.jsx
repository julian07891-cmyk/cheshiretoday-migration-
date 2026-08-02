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


const response = (body) => ({
  ok: true,
  status: 200,
  json: async () => body,
  text: async () => JSON.stringify(body),
});

const article = {
  id: 'responsive-public-article-id',
  _id: 'responsive-public-article-id',
  mongo_id: '64b7f9d4aabbccddeeff0011',
  title: 'A long public article title that must retain the available card width',
  summary: 'Public article preview',
  content: 'Public article content',
  category: 'VeryLongCategoryNameThatMustStayInsideTheArticleCard',
  publishedDate: '2026-08-02T09:00:00Z',
  image: 'https://example.com/article-image.jpg',
  ai_review_risk_level: 'medium',
  ai_review_recommended_action: 'a deliberately long recommendation that must wrap inside the card',
  ai_review_result: { editor_notes: 'Review this article before making further changes.' },
  view_count: 24,
  author: 'Cheshire Today',
  source: 'Verified source',
  source_url: 'https://example.com/source',
  tags: [],
  featured: false,
  scope: 'cheshire',
};

const flush = async () => {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
};


describe('Admin Articles responsive rows', () => {
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

    global.fetch = jest.fn(async (url, options = {}) => {
      const path = String(url);
      if (path.includes('/api/admin/articles/manual-review')) {
        return response({ articles: [], total: 0 });
      }
      if (path.includes('/api/admin/articles/archived')) {
        return response({ articles: [], total: 0 });
      }
      if (path.includes('/api/admin/archive/stats')) return response({});
      if (path.includes('/api/admin/verify')) return response({ success: true });
      if (path.includes('/api/admin/stats')) return response({ articles: { by_category: {} } });
      if (path.includes('/api/admin/subscribers')) return response({ subscribers: [] });
      if (/\/api\/admin\/articles(?:\?|$)/.test(path)) {
        return response({ articles: [article], total: 1 });
      }
      if (path.includes('/api/admin/jobs')) return response({ jobs: [] });
      if (path.includes('/api/jobs/meta/options')) {
        return response({ locations: [], categories: [], job_types: [] });
      }
      expect(options.method || 'GET').toBe('GET');
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

  const renderArticles = async () => {
    await act(async () => root.render(<AdminDashboard onBack={jest.fn()} />));
    await flush();
    await act(async () => container.querySelector('[data-testid="tab-articles"]').click());
    await flush();
  };

  test('contains the real article metadata and actions in a mobile-safe card', async () => {
    await renderArticles();

    const row = container.querySelector(`[data-testid="article-row-${article.id}"]`);
    const image = row.querySelector(`[data-testid="article-row-image-${article.id}"]`);
    const content = row.querySelector(`[data-testid="article-row-content-${article.id}"]`);
    const title = row.querySelector(`[data-testid="article-row-title-${article.id}"]`);
    const category = row.querySelector(`[data-testid="article-row-category-${article.id}"]`);
    const aiStatus = row.querySelector(`[data-testid="article-row-ai-status-${article.id}"]`);
    const actions = row.querySelector(`[data-testid="article-row-actions-${article.id}"]`);

    expect(row).not.toBeNull();
    expect(row.className).toContain('grid');
    expect(row.className).toContain('w-full');
    expect(row.className).toContain('min-w-0');
    expect(row.className).toContain('max-w-full');
    expect(row.className).toContain('grid-cols-[auto_4rem_minmax(0,1fr)]');
    expect(row.className).toContain('overflow-hidden');

    expect(image.className).toContain('h-16');
    expect(image.className).toContain('w-16');
    expect(image.className).toContain('shrink-0');
    expect(image.className).not.toContain('w-full');
    expect(content.className).toContain('min-w-0');
    expect(content.textContent).toContain(article.title);
    expect(content.textContent).toContain(article.category);
    expect(content.textContent).toContain(article.ai_review_recommended_action);
    expect(title.textContent).toBe(article.title);
    expect(title.className).toContain('min-w-0');
    expect(title.className).toContain('break-words');
    expect(title.className).toContain('line-clamp-2');
    expect(title.className).toContain('sm:line-clamp-1');

    expect(category.textContent).toBe(article.category);
    expect(category.className).toContain('max-w-full');
    expect(category.className).toContain('whitespace-normal');
    expect(category.className).toContain('break-words');

    expect(aiStatus.className).toContain('min-w-0');
    expect(aiStatus.className).toContain('max-w-full');
    expect(aiStatus.className).toContain('whitespace-normal');
    expect(aiStatus.className).toContain('break-words');

    expect(actions.parentElement).toBe(row);
    expect(actions.className).toContain('col-span-full');
    expect(actions.className).toContain('grid-cols-3');
    expect(actions.className).toContain('w-full');
    expect(actions.className).toContain('min-w-0');
    expect(actions.className).toContain('sm:flex');
    expect(actions.className).toContain('sm:w-auto');

    const actionTitles = Array.from(actions.querySelectorAll('button'))
      .map((button) => button.getAttribute('title'));
    expect(actionTitles).toEqual([
      'Social Publishing',
      'Edit article',
      'Check with ChatGPT',
      'Force show on homepage',
      'Send article to Manual Review',
      'Archive article',
    ]);
    actions.querySelectorAll('button').forEach((button) => {
      expect(button.className).toContain('min-h-11');
      expect(button.className).toContain('w-full');
      expect(button.className).toContain('sm:min-h-0');
      expect(button.className).toContain('sm:w-auto');
    });

    expect(global.fetch.mock.calls.every(([, options]) => (
      !options?.method || options.method === 'GET'
    ))).toBe(true);
  });

  test('restores the previous horizontal row contract at the sm breakpoint', async () => {
    await renderArticles();

    const row = container.querySelector(`[data-testid="article-row-${article.id}"]`);
    const content = row.querySelector(`[data-testid="article-row-content-${article.id}"]`);
    const title = row.querySelector(`[data-testid="article-row-title-${article.id}"]`);
    const actions = row.querySelector(`[data-testid="article-row-actions-${article.id}"]`);

    expect(row.className).toContain('sm:flex');
    expect(row.className).toContain('sm:items-center');
    expect(row.className).toContain('sm:gap-4');
    expect(content.className).toContain('sm:flex-1');
    expect(title.className).toContain('sm:line-clamp-1');
    expect(actions.className).toContain('sm:flex');
    expect(actions.className).toContain('sm:items-center');
  });
});
