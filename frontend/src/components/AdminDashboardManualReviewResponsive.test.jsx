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

const manualReviewArticle = {
  id: 'manual-review-responsive-id',
  title: 'A long Manual Review title that needs the remaining card width',
  summary: 'Preview text',
  content: 'Article content',
  category: 'VeryLongRegionalCategoryNameThatMustRemainReadableOnNarrowScreens',
  source: 'An exceptionally long verified source name that must wrap inside the card',
  source_url: 'https://example.com/source',
  location: 'AnExtremelyLongCheshireLocalityNameThatMustWrapSafely',
  image: 'https://example.com/image.jpg',
  ai_review_risk_level: 'medium',
  ai_review_recommended_action: 'a deliberately long editorial recommendation that must wrap safely',
  ai_review_result: { editor_notes: 'Check the source wording.' },
  manual_review_reason: 'Requires editorial verification',
  editorial_metadata: {
    publication_recommendation: 'Needs review',
    editorial_topic: 'Community report',
    detected_locality: 'Chester',
  },
};

const flush = async () => {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
};


describe('Admin Manual Review responsive cards', () => {
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
        return response({ articles: [manualReviewArticle], total: 1 });
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

  const renderManualReview = async () => {
    await act(async () => root.render(<AdminDashboard onBack={jest.fn()} />));
    await flush();
    await act(async () => container.querySelector('[data-testid="tab-archive"]').click());
    await flush();
  };

  test('stacks diagnostics and actions without changing the Manual Review actions', async () => {
    await renderManualReview();

    const id = manualReviewArticle.id;
    const card = container.querySelector(`[data-testid="manual-review-card-${id}"]`);
    const image = card.querySelector(`[data-testid="manual-review-image-${id}"]`);
    const summary = card.querySelector(`[data-testid="manual-review-summary-${id}"]`);
    const diagnostics = card.querySelector(`[data-testid="manual-review-diagnostics-${id}"]`);
    const actions = card.querySelector(`[data-testid="manual-review-actions-${id}"]`);
    const category = card.querySelector(`[data-testid="manual-review-category-${id}"]`);
    const source = card.querySelector(`[data-testid="manual-review-source-${id}"]`);
    const locality = card.querySelector(`[data-testid="manual-review-locality-${id}"]`);
    const riskBadge = card.querySelector(`[data-testid="manual-review-risk-badge-${id}"]`);
    const openAIDraft = card.querySelector(`[data-testid="openai-draft-manual-review-${id}"]`);

    expect(card).not.toBeNull();
    expect(card.className).toContain('w-full');
    expect(card.className).toContain('min-w-0');
    expect(card.className).toContain('max-w-full');
    expect(card.className).toContain('overflow-hidden');
    expect(card.className).toContain('grid-cols-[auto_5rem_minmax(0,1fr)]');

    expect(image.className).toContain('w-20');
    expect(image.className).toContain('h-16');
    expect(image.className).toContain('shrink-0');
    expect(image.className).not.toContain('w-full');
    expect(summary.className).toContain('min-w-0');
    expect(summary.textContent).toContain(manualReviewArticle.title);
    [category, source, locality].forEach((metadataValue) => {
      expect(metadataValue.className).toContain('min-w-0');
      expect(metadataValue.className).toContain('max-w-full');
      expect(metadataValue.className).toContain('break-words');
      expect(metadataValue.className).toContain('whitespace-normal');
    });
    expect(summary.textContent).toContain(manualReviewArticle.category);
    expect(summary.textContent).toContain(manualReviewArticle.source);
    expect(summary.textContent).toContain(manualReviewArticle.location);

    expect(diagnostics.className).toContain('col-span-full');
    expect(diagnostics.className).toContain('w-full');
    expect(diagnostics.textContent).toContain('Requires editorial verification');
    expect(diagnostics.textContent).toContain('Needs review');
    expect(diagnostics.textContent).toContain(manualReviewArticle.ai_review_recommended_action);
    expect(riskBadge.className).toContain('min-w-0');
    expect(riskBadge.className).toContain('max-w-full');
    expect(riskBadge.className).toContain('break-words');
    expect(riskBadge.className).toContain('whitespace-normal');

    expect(actions.className).toContain('col-span-full');
    expect(actions.className).toContain('grid-cols-2');
    expect(actions.textContent).toContain('Source');
    expect(actions.textContent).toContain('Edit');
    expect(actions.textContent).toContain('Create OpenAI Draft');
    expect(actions.textContent).toContain('Archive');
    expect(openAIDraft.className).toContain('col-span-2');
    expect(openAIDraft.className).toContain('sm:col-span-1');
    actions.querySelectorAll('button').forEach((button) => {
      expect(button.className).toContain('min-h-11');
      expect(button.className).toContain('w-full');
      expect(button.className).toContain('sm:w-auto');
    });

    expect(global.fetch.mock.calls.every(([, options]) => (
      !options?.method || options.method === 'GET'
    ))).toBe(true);
  });

  test('preserves the compact desktop card alignment at the sm breakpoint', async () => {
    await renderManualReview();

    const id = manualReviewArticle.id;
    const card = container.querySelector(`[data-testid="manual-review-card-${id}"]`);
    const image = card.querySelector(`[data-testid="manual-review-image-${id}"]`);
    const diagnostics = card.querySelector(`[data-testid="manual-review-diagnostics-${id}"]`);
    const actions = card.querySelector(`[data-testid="manual-review-actions-${id}"]`);

    expect(card.className).toContain('sm:grid-cols-[auto_4rem_minmax(0,1fr)]');
    expect(image.className).toContain('sm:w-16');
    expect(image.className).toContain('sm:h-12');
    expect(diagnostics.className).toContain('sm:col-start-3');
    expect(diagnostics.className).toContain('sm:col-span-1');
    expect(actions.className).toContain('sm:col-start-3');
    expect(actions.className).toContain('sm:flex');
    expect(actions.className).toContain('sm:flex-wrap');
    actions.querySelectorAll('button').forEach((button) => {
      expect(button.className).toContain('sm:min-h-0');
      expect(button.className).toContain('sm:w-auto');
    });
  });
});
