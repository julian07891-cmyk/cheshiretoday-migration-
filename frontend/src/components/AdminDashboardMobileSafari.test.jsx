import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import fs from 'fs';
import path from 'path';
import AdminDashboard from './AdminDashboard';


jest.mock('@/lib/utils', () => ({
  cn: (...values) => values.filter(Boolean).join(' '),
}), { virtual: true });

jest.mock('@/components/ui/button', () => ({
  buttonVariants: () => '',
}), { virtual: true });

jest.mock('../hooks/use-toast', () => ({ toast: jest.fn() }));
jest.mock('./admin/SocialPublishingDialog', () => () => null);


const INDEX_HTML = fs.readFileSync(
  path.join(__dirname, '..', '..', 'public', 'index.html'),
  'utf8'
);
const INDEX_CSS = fs.readFileSync(
  path.join(__dirname, '..', 'index.css'),
  'utf8'
);
const DASHBOARD_SOURCE = fs.readFileSync(
  path.join(__dirname, 'AdminDashboard.jsx'),
  'utf8'
);
const DIALOG_SOURCE = fs.readFileSync(
  path.join(__dirname, 'ui', 'dialog.jsx'),
  'utf8'
);

const ARTICLE_EDITOR_MOBILE_RULE = `@media (max-width: 900px), (hover: none) and (pointer: coarse) {
    .admin-article-editor-dialog {
        top: max(1rem, env(safe-area-inset-top, 0px));
        right: max(1rem, env(safe-area-inset-right, 0px));
        bottom: auto;
        left: max(1rem, env(safe-area-inset-left, 0px));
        width: auto;
        margin-inline: auto;
        max-height: calc(100vh - max(1rem, env(safe-area-inset-top, 0px)) - max(1rem, env(safe-area-inset-bottom, 0px)));
        transform: none;
    }
}`;

const ARTICLE_EDITOR_DYNAMIC_HEIGHT_RULE = `@supports (height: 100dvh) {
    @media (max-width: 900px), (hover: none) and (pointer: coarse) {
        .admin-article-editor-dialog {
            max-height: calc(100dvh - max(1rem, env(safe-area-inset-top, 0px)) - max(1rem, env(safe-area-inset-bottom, 0px)));
        }
    }
}`;

const response = (body, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  json: async () => body,
  text: async () => JSON.stringify(body),
});

const flush = async () => {
  await act(async () => Promise.resolve());
};


describe('Admin mobile Safari safeguards', () => {
  let container;
  let root;
  let originalAbortTimeout;
  let originalFetch;
  let originalConsoleLog;
  let originalResizeObserver;

  beforeEach(() => {
    globalThis.IS_REACT_ACT_ENVIRONMENT = true;
    originalAbortTimeout = AbortSignal.timeout;
    originalFetch = global.fetch;
    originalConsoleLog = console.log;
    originalResizeObserver = global.ResizeObserver;
    AbortSignal.timeout = jest.fn(() => undefined);
    global.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
    console.log = jest.fn();
    localStorage.clear();
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
  });

  afterEach(() => {
    act(() => root.unmount());
    container.remove();
    localStorage.clear();
    AbortSignal.timeout = originalAbortTimeout;
    global.fetch = originalFetch;
    console.log = originalConsoleLog;
    global.ResizeObserver = originalResizeObserver;
    delete globalThis.IS_REACT_ACT_ENVIRONMENT;
    jest.restoreAllMocks();
  });

  test('preserves accessible viewport zoom and the mobile-safe login contract', async () => {
    global.fetch = jest.fn();
    await act(async () => root.render(<AdminDashboard onBack={jest.fn()} />));
    await flush();

    const viewport = INDEX_HTML.match(/<meta\s+name="viewport"\s+content="([^"]+)"\s*\/>/);
    expect(viewport?.[1]).toBe('width=device-width, initial-scale=1');
    expect(viewport?.[1]).not.toMatch(/maximum-scale|user-scalable/i);

    const shell = container.querySelector('[data-testid="admin-login-shell"]');
    const username = container.querySelector('[data-testid="admin-login-username"]');
    const password = container.querySelector('[data-testid="admin-login-password"]');
    const card = shell.querySelector('.max-w-md');

    expect(shell.classList.contains('admin-mobile-scope')).toBe(true);
    expect(shell.classList.contains('admin-login-shell')).toBe(true);
    expect(shell.classList.contains('min-h-screen')).toBe(true);
    expect(shell.classList.contains('items-center')).toBe(true);
    expect(card.classList.contains('w-full')).toBe(true);
    expect(username.classList.contains('text-base')).toBe(true);
    expect(password.classList.contains('text-base')).toBe(true);
    expect(username.autocomplete).toBe('username');
    expect(password.autocomplete).toBe('current-password');
    expect(username.style.minWidth).toBe('');
    expect(password.style.minWidth).toBe('');
    expect(shell.style.transform).toBe('');
  });

  test('keeps login submission and authentication request behaviour unchanged', async () => {
    global.fetch = jest.fn(async (url) => {
      if (String(url).includes('/api/admin/login')) {
        return response({ detail: 'Invalid credentials' }, 401);
      }
      return response({});
    });
    await act(async () => root.render(<AdminDashboard onBack={jest.fn()} />));
    await flush();

    const username = container.querySelector('[data-testid="admin-login-username"]');
    const password = container.querySelector('[data-testid="admin-login-password"]');
    const form = container.querySelector('form');
    const setValue = (element, value) => {
      const setter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype,
        'value'
      ).set;
      setter.call(element, value);
      element.dispatchEvent(new Event('input', { bubbles: true }));
    };

    await act(async () => {
      setValue(username, 'test-admin');
      setValue(password, 'test-password');
      form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    });

    const loginCall = global.fetch.mock.calls.find(([url]) =>
      String(url).includes('/api/admin/login')
    );
    expect(loginCall).toBeDefined();
    expect(loginCall[1].method).toBe('POST');
    expect(loginCall[1].headers).toEqual(expect.objectContaining({
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    }));
    expect(JSON.parse(loginCall[1].body)).toEqual({
      username: 'test-admin',
      password: 'test-password',
    });
  });

  test('scopes the 16px text-entry rule to mobile Admin controls', () => {
    expect(INDEX_CSS).toContain('@media (max-width: 900px), (hover: none) and (pointer: coarse)');

    const includedSelectors = [
      'input:not([type])',
      'input[type="text"]',
      'input[type="password"]',
      'input[type="email"]',
      'input[type="search"]',
      'input[type="url"]',
      'input[type="tel"]',
      'input[type="number"]',
      'textarea',
      'select',
      '[role="combobox"]',
    ];
    includedSelectors.forEach((selector) => {
      expect(INDEX_CSS).toContain(`.admin-mobile-scope ${selector}`);
    });
    expect(INDEX_CSS).toContain('font-size: 16px !important;');

    ['checkbox', 'radio', 'range', 'file', 'hidden', 'color', 'button', 'submit', 'reset', 'image']
      .forEach((type) => {
        expect(INDEX_CSS).not.toContain(`.admin-mobile-scope input[type="${type}"]`);
      });
    expect(INDEX_CSS).not.toMatch(/(^|\n)\s*(input|textarea|select)\s*\{[^}]*font-size:\s*16px/m);
  });

  test('uses dynamic viewport height, safe-area spacing and short-height scrolling', () => {
    expect(INDEX_CSS).toMatch(/\.admin-login-shell\s*\{[^}]*min-height:\s*100vh;[^}]*min-height:\s*100dvh;/s);
    expect(INDEX_CSS).toMatch(/\.admin-login-shell\s*\{[^}]*overflow-y:\s*auto;/s);
    expect(INDEX_CSS).toContain('env(safe-area-inset-top, 0px)');
    expect(INDEX_CSS).toContain('env(safe-area-inset-right, 0px)');
    expect(INDEX_CSS).toContain('env(safe-area-inset-bottom, 0px)');
    expect(INDEX_CSS).toContain('env(safe-area-inset-left, 0px)');
    expect(INDEX_CSS).toMatch(/@media \(max-height: 600px\)\s*\{\s*\.admin-login-shell\s*\{\s*align-items:\s*flex-start;/s);
  });

  test('preserves desktop dialog geometry and scopes article-editor geometry to mobile', () => {
    expect(DIALOG_SOURCE).toContain('fixed left-[50%] top-[50%]');
    expect(DIALOG_SOURCE).toContain('translate-x-[-50%] translate-y-[-50%]');
    expect(DIALOG_SOURCE).toContain('data-[state=open]:animate-in');
    expect(INDEX_CSS).toContain(ARTICLE_EDITOR_MOBILE_RULE);
    expect(INDEX_CSS).toContain(ARTICLE_EDITOR_DYNAMIC_HEIGHT_RULE);
    expect(INDEX_CSS.match(/\.admin-article-editor-dialog/g)).toHaveLength(2);
    expect(INDEX_CSS).not.toMatch(/(^|\n)\s*\[role=["']?dialog["']?\][^{]*\{[^}]*transform:\s*none/m);
  });

  test('keeps representative authenticated controls inside the Admin scope', async () => {
    localStorage.setItem('cheshire_admin_token', 'test-admin-token');
    global.fetch = jest.fn(async (url) => {
      const requestPath = String(url);
      if (requestPath.includes('/api/admin/verify')) return response({ success: true });
      if (requestPath.includes('/api/admin/stats')) return response({ articles: { by_category: {} } });
      if (requestPath.includes('/api/admin/subscribers')) return response({ subscribers: [] });
      if (requestPath.includes('/api/admin/articles')) {
        return response({
          articles: [{
            id: 'article-mobile-test',
            title: 'Mobile editor regression article',
            summary: 'A bounded test summary.',
            content: 'A bounded test article body.',
            category: 'Local News',
            author: 'Cheshire Today',
            publishedDate: '2026-08-01T08:00:00Z',
          }],
          total: 1,
        });
      }
      if (requestPath.includes('/api/admin/jobs')) return response({ jobs: [] });
      if (requestPath.includes('/api/jobs/meta/options')) {
        return response({ locations: [], categories: [], job_types: [] });
      }
      return response({});
    });

    await act(async () => root.render(<AdminDashboard onBack={jest.fn()} />));
    await flush();

    const dashboard = container.querySelector('[data-testid="admin-dashboard-shell"]');
    expect(dashboard.classList.contains('admin-mobile-scope')).toBe(true);

    await act(async () => container.querySelector('[data-testid="tab-digest"]').click());
    expect(dashboard.contains(container.querySelector('[data-testid="campaign-html-input"]'))).toBe(true);
    expect(dashboard.contains(container.querySelector('[data-testid="campaign-text-input"]'))).toBe(true);

    await act(async () => container.querySelector('[data-testid="tab-articles"]').click());
    const search = container.querySelector('[data-testid="admin-article-search"]');
    expect(dashboard.contains(search)).toBe(true);

    const articleEditButton = container.querySelector('button[title="Edit article"]');
    expect(articleEditButton).not.toBeNull();
    await act(async () => articleEditButton.click());
    const editorDialog = document.querySelector('[data-testid="admin-article-editor-dialog"]');
    const editorForm = editorDialog.querySelector('[data-testid="admin-article-editor-form"]');
    const categoryAuthorRow = editorDialog.querySelector('[data-testid="article-category-author-row"]');
    expect(editorDialog).not.toBeNull();
    expect(editorDialog.classList.contains('admin-article-editor-dialog')).toBe(true);
    expect(editorDialog.classList.contains('min-w-0')).toBe(true);
    expect(editorDialog.classList.contains('max-w-2xl')).toBe(true);
    expect(editorDialog.classList.contains('max-h-[90vh]')).toBe(true);
    expect(editorDialog.classList.contains('overflow-x-hidden')).toBe(true);
    expect(editorDialog.classList.contains('overflow-y-auto')).toBe(true);
    expect(INDEX_CSS).toContain(ARTICLE_EDITOR_MOBILE_RULE);
    expect(INDEX_CSS).toContain(ARTICLE_EDITOR_DYNAMIC_HEIGHT_RULE);
    expect(editorForm.classList.contains('min-w-0')).toBe(true);
    expect(categoryAuthorRow.classList.contains('grid-cols-1')).toBe(true);
    expect(categoryAuthorRow.classList.contains('sm:grid-cols-2')).toBe(true);

    const scopedTextEntryTestIds = [
      'article-title-input',
      'article-summary-input',
      'article-content-input',
      'article-author-input',
      'article-source-input',
      'article-source-url-input',
      'article-image-input',
      'article-tags-input',
      'article-category-select',
    ];
    scopedTextEntryTestIds.forEach((testId) => {
      const control = editorDialog.querySelector(`[data-testid="${testId}"]`);
      expect(control).not.toBeNull();
      expect(control.closest('.admin-mobile-scope')).toBe(editorDialog);
      expect(control.classList.contains('w-full')).toBe(true);
    });
    expect(editorDialog.querySelector('[data-testid="article-category-select"]')?.getAttribute('role')).toBe('combobox');
    expect(editorDialog.querySelector('[data-testid="article-featured-toggle"]')?.closest('.admin-mobile-scope')).toBe(editorDialog);

    const cancelButton = Array.from(editorDialog.querySelectorAll('button'))
      .find((button) => button.textContent.trim() === 'Cancel');
    expect(cancelButton).toBeDefined();
    await act(async () => cancelButton.click());
    await act(async () => container.querySelector('[data-testid="tab-affiliates"]').click());
    await act(async () => container.querySelector('[data-testid="add-affiliate-button"]').click());
    const affiliateDialog = document.querySelector('[role="dialog"]');
    expect(affiliateDialog).not.toBeNull();
    expect(affiliateDialog.classList.contains('admin-article-editor-dialog')).toBe(false);
  });

  test('keeps Articles, Manual Review and Archive on the single shared editor path', () => {
    expect(DASHBOARD_SOURCE.match(/handleEditArticle\(article\)/g)).toHaveLength(3);
    expect(DASHBOARD_SOURCE.match(/data-testid="admin-article-editor-dialog"/g)).toHaveLength(1);
    expect(DASHBOARD_SOURCE.match(/\/\* Add\/Edit Article Dialog \*\//g)).toHaveLength(1);
  });

  test('contains no JavaScript viewport or zoom manipulation', () => {
    expect(DASHBOARD_SOURCE).not.toMatch(/visualViewport|\.scale\s*=|style\.zoom|user-scalable|maximum-scale/);
  });
});
