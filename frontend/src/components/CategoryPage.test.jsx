import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import CategoryPage from './CategoryPage';
import { categories } from '../mockData';

// Keep NewsHeader real; isolate unrelated widgets and all network access.
jest.mock('./FestiveBanner', () => () => null);
jest.mock('./WeatherWidget', () => () => null);
jest.mock('./DarkModeToggle', () => () => null);
jest.mock('./NewsFooter', () => () => null);
jest.mock('./ui/button', () => ({ Button: ({ children, variant, ...props }) => <button {...props}>{children}</button> }));
jest.mock('./ui/badge', () => ({ Badge: ({ children, ...props }) => <span {...props}>{children}</span> }));
jest.mock('../services/api', () => ({ articleService: { searchArticles: jest.fn() } }));

const LocationProbe = () => <output data-testid="location">{useLocation().pathname}</output>;
let container;
let root;
let originalFetch;

beforeEach(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  originalFetch = global.fetch;
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => ({ articles: [{
    id: 'story-1', title: 'Cheshire business investment creates jobs',
    category: 'Business', source: 'Local source', summary: 'New investment creates jobs.',
  }], total: 1 }) });
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
  global.fetch = originalFetch;
});

const renderPage = async (slug = 'finance') => {
  await act(async () => root.render(
    <HelmetProvider><MemoryRouter initialEntries={['/category/finance']}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <CategoryPage categorySlug={slug} /><LocationProbe />
    </MemoryRouter></HelmetProvider>
  ));
};
const click = async (element) => {
  expect(element).toBeTruthy();
  await act(async () => element.click());
};
const path = () => container.querySelector('[data-testid="location"]').textContent;
const headerButtons = (label) => Array.from(container.querySelectorAll('header button'))
  .filter(button => button.textContent.trim() === label);
const openMobile = async () => click(container.querySelector('header .lucide-menu').closest('button'));

describe.each(['desktop', 'mobile'])('%s real header navigation', (mode) => {
  test.each([
    ['Home', '/'], ['Local', '/category/local-news'],
    ['UK', '/category/uk-news'], ['Business', '/category/business'],
  ])('%s navigates to %s', async (label, destination) => {
    await renderPage();
    if (mode === 'mobile') await openMobile();
    const buttons = headerButtons(label);
    expect(buttons).toHaveLength(mode === 'mobile' ? 2 : 1);
    await click(buttons[mode === 'mobile' ? 1 : 0]);
    expect(path()).toBe(destination);
    expect(container.querySelector('select[aria-label="Choose location (mobile)"]')).toBeNull();
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });
});

test('category rendering, query and existing four header choices remain intact', async () => {
  await renderPage();
  expect(container.querySelector('main h1').textContent).toBe('Finance');
  expect(container.querySelector('main article').textContent).toContain('Cheshire business investment creates jobs');
  expect(global.fetch.mock.calls[0][0]).toContain('/api/articles?category=Finance&limit=30&with_total=true');
  expect(Array.from(container.querySelectorAll('header nav button')).map(b => b.textContent)).toEqual(['Home', 'Local', 'UK', 'Business']);
  await openMobile();
  expect(headerButtons('Finance')).toHaveLength(0);
  expect(headerButtons('AI & Tech')).toHaveLength(0);
});

test.each([['AI & Tech', '/category/ai-tech'], ['Finance', '/category/finance'], ['UK', '/category/uk-news']])(
  'existing %s topic link remains unchanged', async (label, destination) => {
    await renderPage('local-news');
    await click(Array.from(container.querySelectorAll('main nav button')).find(b => b.textContent === label));
    expect(path()).toBe(destination);
  }
);

test.each([['home', '/'], ['unknown', '/category/finance'], ['constructor', '/category/finance']])(
  'header ID %s is handled safely', async (id, destination) => {
    const entry = categories.find(c => c.id === 'all');
    const originalId = entry.id;
    try {
      entry.id = id;
      await renderPage();
      await click(headerButtons('Home')[0]);
      expect(path()).toBe(destination);
    } finally {
      entry.id = originalId;
    }
  }
);
