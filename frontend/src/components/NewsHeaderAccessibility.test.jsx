import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import NewsHeader from './NewsHeader';
import { articleService } from '../services/api';
import { buildArticleUrl } from '../utils/articleUrl';

jest.mock('../services/api', () => ({
  articleService: {
    searchArticles: jest.fn(),
  },
}));
jest.mock('./FestiveBanner', () => () => null);
jest.mock('./WeatherWidget', () => () => null);
jest.mock('./DarkModeToggle', () => () => null);
jest.mock('./ui/button', () => ({ Button: ({ children, ...props }) => <button {...props}>{children}</button> }));

const makeArticle = (index, overrides = {}) => ({
  id: `article-${index}`,
  title: `Cheshire search result ${index}`,
  category: 'Local News',
  image: `https://example.com/image-${index}.jpg`,
  ...overrides,
});

let container;
let root;

beforeAll(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
});

beforeEach(() => {
  jest.useFakeTimers();
  articleService.searchArticles.mockReset();
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root?.unmount());
  container?.remove();
  root = null;
  container = null;
  jest.useRealTimers();
  jest.restoreAllMocks();
});

const renderHeader = async (props = {}) => {
  await act(async () => {
    root.render(<NewsHeader categories={[]} {...props} />);
  });
};

const changeQuery = async (input, value) => {
  await act(async () => {
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(input, value);
    input.dispatchEvent(new Event('input', { bubbles: true }));
  });
};

const runDebounce = async () => {
  await act(async () => {
    jest.advanceTimersByTime(300);
    await Promise.resolve();
  });
};

const focusInput = async (input) => {
  await act(async () => input.focus());
};

const status = () => container.querySelector('[role="status"]');

test('desktop and mobile search inputs have durable names and preserve visual contracts', async () => {
  await renderHeader();

  const desktopInput = container.querySelector('input[placeholder="Search news..."]');
  expect(desktopInput).not.toBeNull();
  expect(desktopInput.getAttribute('aria-label')).toBe('Search news');
  expect(desktopInput.className).toContain('w-64');

  const mobileToggle = container.querySelector('button');
  await act(async () => mobileToggle.click());

  const inputs = container.querySelectorAll('input[placeholder="Search news..."]');
  expect(inputs).toHaveLength(2);
  expect(inputs[1].getAttribute('aria-label')).toBe('Search news');
  expect(inputs[1].className).toContain('w-full');
  expect(inputs[1].className).toContain('h-10');
});

test('results are limited native links with correct desktop and mobile destinations', async () => {
  articleService.searchArticles.mockResolvedValue(
    Array.from({ length: 6 }, (_, index) => makeArticle(index))
  );
  await renderHeader();
  const desktopInput = container.querySelector('input[aria-label="Search news"]');

  await focusInput(desktopInput);
  await changeQuery(desktopInput, 'Cheshire');
  await runDebounce();

  const desktopLinks = container.querySelectorAll('a[href^="/article/"]');
  expect(desktopLinks).toHaveLength(5);
  expect(desktopLinks[0].getAttribute('href')).toBe(buildArticleUrl(makeArticle(0)));
  expect(desktopLinks[0].tabIndex).toBe(0);
  expect(desktopLinks[0].className).toContain('gap-3');
  expect(status().textContent).toBe('5 search results');

  const mobileToggle = container.querySelector('button');
  await act(async () => mobileToggle.click());
  const allLinks = container.querySelectorAll('a[href^="/article/"]');
  expect(allLinks).toHaveLength(10);
  expect(allLinks[5].getAttribute('href')).toBe(buildArticleUrl(makeArticle(0)));
  expect(allLinks[5].className).toContain('w-full');
  expect(container.querySelectorAll('button a[href^="/article/"]')).toHaveLength(0);
});

test('ordinary activation supports SPA callbacks while modified clicks preserve browser semantics', async () => {
  const onArticleClick = jest.fn();
  const article = makeArticle(1);
  articleService.searchArticles.mockResolvedValue([article]);
  await renderHeader({ onArticleClick });
  const input = container.querySelector('input[aria-label="Search news"]');

  await focusInput(input);
  await changeQuery(input, 'Cheshire');
  await runDebounce();
  const link = container.querySelector('a[href^="/article/"]');
  expect(link.getAttribute('href')).toBe(buildArticleUrl(article));

  link.addEventListener('click', (event) => event.preventDefault(), { once: true });
  await act(async () => {
    link.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, ctrlKey: true }));
  });
  expect(onArticleClick).not.toHaveBeenCalled();
  expect(container.querySelector('a[href^="/article/"]')).not.toBeNull();

  await act(async () => link.click());
  expect(onArticleClick).toHaveBeenCalledWith(article);
  expect(container.querySelector('a[href^="/article/"]')).toBeNull();
});

test('Escape dismisses results, cancels pending state and retains input focus', async () => {
  articleService.searchArticles.mockResolvedValue([makeArticle(1)]);
  await renderHeader();
  const input = container.querySelector('input[aria-label="Search news"]');

  await focusInput(input);
  await changeQuery(input, 'Cheshire');
  await runDebounce();
  expect(container.querySelector('a[href^="/article/"]')).not.toBeNull();

  await act(async () => {
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }));
  });

  expect(container.querySelector('a[href^="/article/"]')).toBeNull();
  expect(status().textContent).toBe('');
  expect(document.activeElement).toBe(input);

  await changeQuery(input, 'Cheshire again');
  await runDebounce();
  expect(container.querySelector('a[href^="/article/"]')).not.toBeNull();
});

test('loading, singular, empty and failure states use one polite status contract', async () => {
  let resolveSearch;
  articleService.searchArticles.mockImplementationOnce(
    () => new Promise((resolve) => { resolveSearch = resolve; })
  );
  await renderHeader();
  const input = container.querySelector('input[aria-label="Search news"]');
  await focusInput(input);
  await changeQuery(input, 'First');
  await runDebounce();

  expect(status().getAttribute('aria-live')).toBe('polite');
  expect(status().textContent).toBe('Searching…');
  expect(container.querySelector('.animate-spin').getAttribute('aria-hidden')).toBe('true');

  await act(async () => resolveSearch([makeArticle(1)]));
  expect(status().textContent).toBe('1 search result');

  articleService.searchArticles.mockResolvedValueOnce([]);
  await changeQuery(input, 'Nothing');
  await runDebounce();
  expect(status().textContent).toBe('No articles found');
  expect(container.textContent).toContain('No articles found');

  jest.spyOn(console, 'error').mockImplementation(() => {});
  articleService.searchArticles.mockRejectedValueOnce(new Error('network unavailable'));
  await changeQuery(input, 'Failure');
  await runDebounce();
  expect(status().textContent).toBe('Search is unavailable. Please try again.');
  expect(container.textContent).not.toContain('No articles found');
});

test('short queries clear stale results and status without making another request', async () => {
  articleService.searchArticles.mockResolvedValue([makeArticle(1)]);
  await renderHeader();
  const input = container.querySelector('input[aria-label="Search news"]');
  await focusInput(input);

  await changeQuery(input, 'Cheshire');
  await act(async () => jest.advanceTimersByTime(299));
  expect(articleService.searchArticles).not.toHaveBeenCalled();
  await runDebounce();
  expect(articleService.searchArticles).toHaveBeenCalledTimes(1);
  expect(container.querySelector('a[href^="/article/"]')).not.toBeNull();

  await changeQuery(input, 'C');
  expect(container.querySelector('a[href^="/article/"]')).toBeNull();
  expect(status().textContent).toBe('');
  await act(async () => jest.advanceTimersByTime(300));
  expect(articleService.searchArticles).toHaveBeenCalledTimes(1);
});

test('a stale older response cannot overwrite a newer successful query', async () => {
  let resolveOld;
  let resolveNew;
  articleService.searchArticles.mockImplementation((query) => new Promise((resolve) => {
    if (query === 'Old query') resolveOld = resolve;
    if (query === 'New query') resolveNew = resolve;
  }));
  await renderHeader();
  const input = container.querySelector('input[aria-label="Search news"]');
  await focusInput(input);

  await changeQuery(input, 'Old query');
  await runDebounce();
  await changeQuery(input, 'New query');
  await runDebounce();

  const newArticle = makeArticle(2, { title: 'New query result' });
  await act(async () => resolveNew([newArticle]));
  expect(container.textContent).toContain('New query result');

  await act(async () => resolveOld([makeArticle(3, { title: 'Stale old result' })]));
  expect(container.textContent).toContain('New query result');
  expect(container.textContent).not.toContain('Stale old result');
  expect(status().textContent).toBe('1 search result');
});
