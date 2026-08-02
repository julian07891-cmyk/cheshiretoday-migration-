import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import AdminDashboard from './AdminDashboard';
import { toast } from '../hooks/use-toast';


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

const publicArticle = {
  id: 'public-article-id',
  mongo_id: '64b7f9d4aabbccddeeff0011',
  title: 'Public article title',
  summary: 'Public article preview',
  content: 'Public article content',
  category: 'Local News',
  author: 'Cheshire Today',
  source: 'Manual Entry',
  source_url: '',
  image: '',
  tags: ['public'],
  featured: false,
  scope: 'cheshire',
  publishedDate: '2026-08-01T08:00:00Z',
};

const manualReviewArticle = {
  id: 'manual-review-mongo-id',
  title: 'Manual Review article title',
  summary: 'Manual Review article preview',
  content: 'Manual Review article content',
  category: 'Business',
  author: 'Cheshire Today',
  source: 'Verified source',
  source_url: 'https://example.com/source',
  image: 'https://example.com/image.jpg',
  tags: ['manual', 'review'],
  featured: false,
  scope: 'cheshire',
  manual_review_reason: 'Requires editorial verification',
  publishedDate: '2026-08-01T07:00:00Z',
};

const archivedArticle = {
  ...manualReviewArticle,
  id: 'archived-manual-review-id',
  title: 'Archived Manual Review article',
  archive_reason: 'needs_manual_review',
  archive_source: 'legacy',
};

const setControlValue = (element, value) => {
  const prototype = element instanceof HTMLTextAreaElement
    ? window.HTMLTextAreaElement.prototype
    : window.HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(prototype, 'value').set.call(element, value);
  element.dispatchEvent(new Event('input', { bubbles: true }));
};

const flush = async () => {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
};


describe('Admin Manual Review publication intent safeguard', () => {
  let container;
  let root;
  let originalAbortTimeout;
  let originalFetch;
  let originalResizeObserver;
  let originalConsoleLog;
  let updateResult;
  let updateStatus;

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
    updateResult = { success: true, restored_from_manual_review: true };
    updateStatus = 200;

    global.fetch = jest.fn(async (url, options = {}) => {
      const path = String(url);
      if (options.method === 'PUT' && path.includes('/api/admin/articles/')) {
        return response(updateResult, updateStatus);
      }
      if (options.method === 'POST' && /\/api\/admin\/articles$/.test(path)) {
        return response({ success: true, article: { id: 'created-article-id' } });
      }
      if (path.includes('/api/admin/articles/manual-review')) {
        return response({ articles: [manualReviewArticle], total: 1 });
      }
      if (path.includes('/api/admin/articles/archived')) {
        return response({ articles: [archivedArticle], total: 1 });
      }
      if (path.includes('/api/admin/archive/stats')) return response({});
      if (path.includes('/api/admin/verify')) return response({ success: true });
      if (path.includes('/api/admin/stats')) return response({ articles: { by_category: {} } });
      if (path.includes('/api/admin/subscribers')) return response({ subscribers: [] });
      if (/\/api\/admin\/articles(?:\?|$)/.test(path)) {
        return response({ articles: [publicArticle], total: 1 });
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

  const renderDashboard = async () => {
    await act(async () => root.render(<AdminDashboard onBack={jest.fn()} />));
    await flush();
  };

  const click = async (element) => {
    expect(element).not.toBeNull();
    await act(async () => element.click());
    await flush();
  };

  const openArchiveTab = async () => {
    await click(container.querySelector('[data-testid="tab-archive"]'));
  };

  const getEditor = () => document.querySelector('[data-testid="admin-article-editor-dialog"]');

  const getConfirmation = () => Array.from(document.querySelectorAll('[role="dialog"]'))
    .find((dialog) => dialog.textContent.includes('Confirm Manual Review update'));

  const putCalls = () => global.fetch.mock.calls
    .filter(([, options]) => options?.method === 'PUT');

  const openEditedManualReview = async () => {
    await renderDashboard();
    await openArchiveTab();
    await click(container.querySelector('[data-testid="edit-manual-review-manual-review-mongo-id"]'));

    const editor = getEditor();
    await act(async () => {
      setControlValue(editor.querySelector('[data-testid="article-title-input"]'), 'Edited Manual Review title');
      setControlValue(editor.querySelector('[data-testid="article-summary-input"]'), 'Edited preview');
      setControlValue(editor.querySelector('[data-testid="article-content-input"]'), 'Edited article content');
      setControlValue(editor.querySelector('[data-testid="article-source-input"]'), 'Edited verified source');
      setControlValue(editor.querySelector('[data-testid="article-tags-input"]'), 'edited, secondary, tags');
    });
    return editor;
  };

  const expectEditedManualReviewPreserved = () => {
    const editor = getEditor();
    expect(editor).not.toBeNull();
    expect(editor.querySelector('[data-testid="article-title-input"]').value)
      .toBe('Edited Manual Review title');
    expect(editor.querySelector('[data-testid="article-summary-input"]').value)
      .toBe('Edited preview');
    expect(editor.querySelector('[data-testid="article-content-input"]').value)
      .toBe('Edited article content');
    expect(editor.querySelector('[data-testid="article-source-input"]').value)
      .toBe('Edited verified source');
    expect(editor.querySelector('[data-testid="article-tags-input"]').value)
      .toBe('edited, secondary, tags');
    expect(editor.querySelector('[data-testid="manual-review-publication-notice"]')).not.toBeNull();
    expect(editor.querySelector('[data-testid="submit-article-button"]').disabled).toBe(false);
  };

  const dismissConfirmation = async (method) => {
    const confirmation = getConfirmation();
    expect(confirmation).not.toBeUndefined();

    if (method === 'x') {
      const closeButton = Array.from(confirmation.querySelectorAll('button'))
        .find((button) => button.textContent.trim() === 'Close');
      await click(closeButton);
      return;
    }

    if (method === 'escape') {
      await act(async () => {
        confirmation.dispatchEvent(new KeyboardEvent('keydown', {
          key: 'Escape',
          code: 'Escape',
          bubbles: true,
          cancelable: true,
        }));
      });
      await flush();
      return;
    }

    const openOverlays = Array.from(document.querySelectorAll('[data-state="open"]'))
      .filter((element) => element.classList.contains('inset-0'));
    const confirmationOverlay = openOverlays.at(-1);
    expect(confirmationOverlay).not.toBeUndefined();
    await act(async () => {
      confirmationOverlay.dispatchEvent(new MouseEvent('pointerdown', {
        bubbles: true,
        cancelable: true,
      }));
      confirmationOverlay.dispatchEvent(new MouseEvent('click', {
        bubbles: true,
        cancelable: true,
      }));
    });
    await flush();
  };

  test('shows the Manual Review-only notice and confirmation without losing edited fields on cancel', async () => {
    const editor = await openEditedManualReview();
    expect(editor).not.toBeNull();
    expect(editor.querySelector('[data-testid="manual-review-publication-notice"]')?.textContent)
      .toBe('Updating this Manual Review article may restore it to the live site if all existing publication safeguards pass. If any safeguard still fails, it will remain in Manual Review.');
    expect(editor.querySelector('[data-testid="submit-article-button"]')?.textContent)
      .toContain('Review and Update');
    expect(editor.querySelector('[data-testid="submit-article-button"]')?.textContent)
      .not.toBe('Publish');

    await click(editor.querySelector('[data-testid="submit-article-button"]'));
    expect(getConfirmation()).not.toBeUndefined();
    expect(global.fetch.mock.calls.filter(([, options]) => options?.method === 'PUT')).toHaveLength(0);

    const confirmation = getConfirmation();
    await click(Array.from(confirmation.querySelectorAll('button'))
      .find((button) => button.textContent.trim() === 'Cancel'));

    expectEditedManualReviewPreserved();
    expect(putCalls()).toHaveLength(0);
  });

  test.each(['x', 'escape', 'outside'])('dismisses confirmation through %s without losing editor state', async (method) => {
    const editor = await openEditedManualReview();
    await click(editor.querySelector('[data-testid="submit-article-button"]'));
    expect(putCalls()).toHaveLength(0);

    await dismissConfirmation(method);

    expect(getConfirmation()).toBeUndefined();
    expectEditedManualReviewPreserved();
    expect(putCalls()).toHaveLength(0);

    await click(getEditor().querySelector('[data-testid="submit-article-button"]'));
    expect(getConfirmation()).not.toBeUndefined();
    expect(putCalls()).toHaveLength(0);
  });

  test('confirms exactly one unchanged authenticated PUT and preserves restored handling', async () => {
    await renderDashboard();
    await openArchiveTab();
    await click(container.querySelector('[data-testid="edit-manual-review-manual-review-mongo-id"]'));

    const editor = getEditor();
    await click(editor.querySelector('[data-testid="submit-article-button"]'));
    const confirmation = getConfirmation();
    const confirmButton = Array.from(confirmation.querySelectorAll('button'))
      .find((button) => button.textContent.trim() === 'Confirm update');

    await act(async () => {
      confirmButton.click();
      confirmButton.click();
    });
    await flush();

    const putCalls = global.fetch.mock.calls.filter(([, options]) => options?.method === 'PUT');
    expect(putCalls).toHaveLength(1);
    expect(putCalls[0][0]).toContain('/api/admin/articles/manual-review-mongo-id');
    expect(putCalls[0][1].headers).toEqual(expect.objectContaining({
      'Content-Type': 'application/json',
      Authorization: 'Bearer test-admin-token',
    }));
    expect(JSON.parse(putCalls[0][1].body)).toEqual({
      title: manualReviewArticle.title,
      summary: manualReviewArticle.summary,
      content: manualReviewArticle.content,
      category: manualReviewArticle.category,
      image: manualReviewArticle.image,
      author: manualReviewArticle.author,
      source: manualReviewArticle.source,
      source_url: manualReviewArticle.source_url,
      tags: manualReviewArticle.tags,
      featured: false,
      scope: 'cheshire',
    });
    expect(JSON.stringify(JSON.parse(putCalls[0][1].body))).not.toContain('manual_review');
    expect(getEditor()).toBeNull();
    expect(toast).toHaveBeenCalledWith(expect.objectContaining({ title: '✅ Article Restored' }));
  });

  test('closes and resets after a successful non-restored Manual Review update', async () => {
    updateResult = { success: true, restored_from_manual_review: false };
    await renderDashboard();
    await openArchiveTab();
    await click(container.querySelector('[data-testid="edit-manual-review-manual-review-mongo-id"]'));
    await click(getEditor().querySelector('[data-testid="submit-article-button"]'));
    await click(Array.from(getConfirmation().querySelectorAll('button'))
      .find((button) => button.textContent.trim() === 'Confirm update'));

    expect(global.fetch.mock.calls.filter(([, options]) => options?.method === 'PUT')).toHaveLength(1);
    expect(toast).not.toHaveBeenCalledWith(expect.objectContaining({ title: '✅ Article Restored' }));
    expect(global.fetch.mock.calls.filter(([url]) => String(url).includes('/manual-review')).length)
      .toBeGreaterThan(1);
    expect(getEditor()).toBeNull();

    await click(container.querySelector('[data-testid="tab-articles"]'));
    await click(container.querySelector('[data-testid="edit-article-public-article-id"]'));
    expect(getEditor().querySelector('[data-testid="manual-review-publication-notice"]')).toBeNull();
    expect(getEditor().querySelector('[data-testid="submit-article-button"]').textContent)
      .toContain('Update Article');
  });

  test('preserves fields and allows one clean retry after a failed Manual Review PUT', async () => {
    updateResult = { detail: 'Failed to save article' };
    updateStatus = 500;
    const failedEditor = await openEditedManualReview();
    await click(failedEditor.querySelector('[data-testid="submit-article-button"]'));
    await click(Array.from(getConfirmation().querySelectorAll('button'))
      .find((button) => button.textContent.trim() === 'Confirm update'));

    expect(putCalls()).toHaveLength(1);
    expectEditedManualReviewPreserved();
    expect(toast).toHaveBeenCalledWith(expect.objectContaining({ variant: 'destructive' }));

    updateResult = { success: true, restored_from_manual_review: false };
    updateStatus = 200;
    await click(getEditor().querySelector('[data-testid="submit-article-button"]'));
    expect(getConfirmation()).not.toBeUndefined();
    await click(Array.from(getConfirmation().querySelectorAll('button'))
      .find((button) => button.textContent.trim() === 'Confirm update'));

    expect(putCalls()).toHaveLength(2);
    expect(getEditor()).toBeNull();
  });

  test('leaves public, Archive and Add Article contracts direct and resets origin on close', async () => {
    await renderDashboard();
    await openArchiveTab();
    await click(container.querySelector('[data-testid="edit-manual-review-manual-review-mongo-id"]'));
    expect(getEditor().querySelector('[data-testid="manual-review-publication-notice"]')).not.toBeNull();
    await click(Array.from(getEditor().querySelectorAll('button'))
      .find((button) => button.textContent.trim() === 'Cancel'));

    await click(container.querySelector('[data-testid="tab-articles"]'));
    await click(container.querySelector('[data-testid="edit-article-public-article-id"]'));
    expect(getEditor().querySelector('[data-testid="manual-review-publication-notice"]')).toBeNull();
    expect(getEditor().querySelector('[data-testid="submit-article-button"]').textContent)
      .toContain('Update Article');
    await click(getEditor().querySelector('[data-testid="submit-article-button"]'));
    expect(getConfirmation()).toBeUndefined();
    expect(global.fetch.mock.calls.filter(([, options]) => options?.method === 'PUT')).toHaveLength(1);

    await openArchiveTab();
    await click(container.querySelector('button[title="Edit manual review article"]'));
    expect(getEditor().querySelector('[data-testid="manual-review-publication-notice"]')).toBeNull();
    expect(getEditor().querySelector('[data-testid="submit-article-button"]').textContent)
      .toContain('Update Article');
    await click(getEditor().querySelector('[data-testid="submit-article-button"]'));
    expect(getConfirmation()).toBeUndefined();
    expect(global.fetch.mock.calls.filter(([, options]) => options?.method === 'PUT')).toHaveLength(2);

    await click(Array.from(container.querySelectorAll('button'))
      .find((button) => button.textContent.trim() === 'Add Article'));
    expect(getEditor().querySelector('[data-testid="manual-review-publication-notice"]')).toBeNull();
    expect(getEditor().querySelector('[data-testid="submit-article-button"]').textContent)
      .toContain('Publish Article');
    await act(async () => {
      setControlValue(getEditor().querySelector('[data-testid="article-title-input"]'), 'New public article');
      setControlValue(getEditor().querySelector('[data-testid="article-content-input"]'), 'New public article content');
    });
    await click(getEditor().querySelector('[data-testid="submit-article-button"]'));
    expect(getConfirmation()).toBeUndefined();
    expect(global.fetch.mock.calls.filter(([, options]) => options?.method === 'POST')).toHaveLength(1);
  });
});
