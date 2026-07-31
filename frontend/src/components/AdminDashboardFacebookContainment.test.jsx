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


const response = (body) => ({
  ok: true,
  status: 200,
  json: async () => body,
  text: async () => JSON.stringify(body),
});


describe('Admin Facebook containment', () => {
  let container;
  let root;
  let originalAbortTimeout;
  let originalFetch;

  beforeEach(() => {
    globalThis.IS_REACT_ACT_ENVIRONMENT = true;
    originalAbortTimeout = AbortSignal.timeout;
    originalFetch = global.fetch;
    AbortSignal.timeout = jest.fn(() => undefined);
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    localStorage.setItem('cheshire_admin_token', 'test-admin-token');

    global.fetch = jest.fn(async (url) => {
      const path = String(url);
      if (path.includes('/api/admin/verify')) return response({ success: true });
      if (path.includes('/api/admin/stats')) return response({ articles: { by_category: {} } });
      if (path.includes('/api/admin/subscribers')) return response({ subscribers: [] });
      if (path.includes('/api/admin/articles')) {
        return response({
          articles: [{
            id: 'legacy-local-news-article',
            mongo_id: '64b7f9d4aabbccddeeff0011',
            title: 'A verified Local News article',
            category: 'Local News',
            publishedDate: '2026-07-31T12:00:00Z',
          }],
          total: 1,
        });
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
    delete globalThis.IS_REACT_ACT_ENVIRONMENT;
    jest.restoreAllMocks();
  });

  const clickTestId = async (testId) => {
    const target = container.querySelector(`[data-testid="${testId}"]`);
    expect(target).not.toBeNull();
    await act(async () => target.click());
  };

  test('Facebook tab is a read-only handoff to article Social Publishing', async () => {
    await act(async () => root.render(<AdminDashboard onBack={jest.fn()} />));

    const fetchCallCountBeforeOpeningFacebook = global.fetch.mock.calls.length;
    await clickTestId('tab-facebook');
    expect(global.fetch).toHaveBeenCalledTimes(fetchCallCountBeforeOpeningFacebook);

    expect(container.querySelector('[data-testid="facebook-social-publishing-handoff"]')).not.toBeNull();
    expect(container.textContent).toContain('Prepare Facebook graphics and publishing copy through Social Publishing in the Articles tab.');
    expect(container.textContent).toContain('does not publish or schedule Facebook posts automatically');
    expect(container.textContent).not.toContain('AI-prioritized');

    const visibleButtons = Array.from(container.querySelectorAll('button')).map((button) => button.textContent.trim());
    expect(visibleButtons).not.toContain('Post to Facebook');
    expect(global.fetch).not.toHaveBeenCalledWith(
      expect.stringContaining('/api/facebook/post-single'),
      expect.anything()
    );
    expect(global.fetch).not.toHaveBeenCalledWith(
      expect.stringContaining('/api/facebook/trigger-scheduled'),
      expect.anything()
    );

    await clickTestId('open-articles-social-publishing');
    expect(container.textContent).toContain('Manage your news articles');

    await clickTestId('social-publishing-64b7f9d4aabbccddeeff0011');
    expect(container.querySelector('[data-testid="social-publishing-dialog"]')?.textContent)
      .toBe('A verified Local News article');

    const forbiddenRequests = global.fetch.mock.calls.filter(([url]) =>
      String(url).includes('/api/facebook/post-single') ||
      String(url).includes('/api/facebook/trigger-scheduled')
    );
    expect(forbiddenRequests).toEqual([]);
  });
});
