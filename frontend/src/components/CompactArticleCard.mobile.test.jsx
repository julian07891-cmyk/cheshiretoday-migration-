import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter, useLocation } from 'react-router-dom';
import CompactArticleCard from './CompactArticleCard';

function LocationProbe() {
  return <output data-testid="route">{useLocation().pathname}</output>;
}

test.each([
  ['', 'Short report'], ['/fixture.jpg', 'Short report'],
  ['', 'A long Cheshire business headline '.repeat(5)],
  ['/fixture.jpg', 'A long Cheshire business headline '.repeat(5)],
  ['/fixture.jpg', '“£12m investment…”: Cheshire manufacturer announces jobs'],
])('Version B preserves complete titles, native navigation and metadata: image=%s title=%s', (image, title) => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  const host = document.createElement('div');
  const root = createRoot(host);
  const article = { id: 'fixed-1', url: '/article/fixed-1/report', title,
    category: 'Business', town: 'Chester', publishedDate: '2026-10-30T06:00:00', image };
  try {
    act(() => root.render(<MemoryRouter><CompactArticleCard article={article} variant="editorial" mobileCompact /><LocationProbe /></MemoryRouter>));
    const link = host.querySelector('a');
    expect(link.getAttribute('href')).toBe(article.url);
    expect(link.getAttribute('aria-label')).toBe(article.title);
    expect(link.querySelector('a,button,input,select,textarea,[role="button"],[tabindex]')).toBeNull();
    expect(link.className).toContain('focus-visible:outline');
    expect(link.className).toContain('dark:focus-visible:outline-blue-300');
    expect(link.tabIndex).toBe(0);
    expect(link.className).toContain('sm:block');
    expect(link.classList.contains('flow-root')).toBe(false);
    expect(link.classList.contains('flex')).toBe(true);
    expect(link.classList.contains('flex-wrap')).toBe(false);
    const textWrapper = host.querySelector('h3').parentElement;
    expect(textWrapper.className).toContain('flex-1');
    expect(textWrapper.className).toContain('min-w-0');
    expect(textWrapper.className).toContain('sm:p-4');
    expect(host.querySelector('h3').classList.contains('line-clamp-3')).toBe(true);
    expect(host.querySelector('h3').classList.contains('line-clamp-none')).toBe(false);
    const metadata = textWrapper.lastElementChild;
    expect(metadata.className).not.toContain('clear-both');
    expect(metadata.textContent).toContain('30 Oct');
    expect(metadata.textContent).toContain('1 min read');
    expect(metadata.className).not.toMatch(/truncate|line-clamp/);
    expect(host.querySelector('h3').className).toContain('text-[16px]');
    expect(host.querySelector('h3').className).toContain('leading-[1.25]');
    expect(host.querySelector('h3').className).toContain('sm:text-xl');
    expect(host.querySelector('h3').className).not.toContain('leading-[21px]');
    expect(host.querySelector('h3').textContent).toBe(article.title);
    expect(host.querySelector('h3').className).toContain('sm:line-clamp-3');
    expect(host.textContent).toContain('Chester');
    expect(host.textContent).toContain('Business');
    const labels = textWrapper.firstElementChild;
    expect(labels.className).toContain('[overflow-wrap:normal]');
    expect(labels.className).toContain('[word-break:normal]');
    expect(labels.className).toContain('flex-wrap');
    if (image) {
      const img = host.querySelector('img');
      expect(img.getAttribute('loading')).toBe('lazy');
      expect(img.parentElement.className).toContain('w-[88px]');
      expect(img.parentElement.className).toContain('h-[90px]');
      expect(img.parentElement.className).toContain('sm:h-auto');
      expect(img.parentElement.className).toContain('sm:w-auto');
      expect(img.className).toContain('object-cover');
      expect(img.parentElement.className).not.toContain('float-left');
      expect(img.parentElement.className).toContain('shrink-0');
      expect(img.parentElement.className).toContain('sm:aspect-[16/10]');
      act(() => img.dispatchEvent(new Event('error')));
      expect(img.getAttribute('src')).toContain('images.unsplash.com');
    } else expect(host.querySelector('img')).toBeNull();
    expect(article.title).toBe(title);
    act(() => link.click());
    expect(host.querySelector('[data-testid="route"]').textContent).toBe(article.url);
  } finally { act(() => root.unmount()); }
});
