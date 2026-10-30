import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import CompactArticleCard from './CompactArticleCard';

test.each(['', '/fixture.jpg'])('homepage compact option preserves native navigation and metadata: %s', image => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  const host = document.createElement('div');
  const root = createRoot(host);
  const article = { id: 'fixed-1', url: '/article/fixed-1/report', title: 'A long Cheshire business headline '.repeat(5),
    category: 'Business', town: 'Chester', publishedDate: '2026-10-30T06:00:00', image };
  try {
    act(() => root.render(<MemoryRouter><CompactArticleCard article={article} variant="editorial" mobileCompact /></MemoryRouter>));
    const link = host.querySelector('a');
    expect(link.getAttribute('href')).toBe(article.url);
    expect(link.className).toContain('focus-visible:outline');
    expect(link.className).toContain('sm:block');
    expect(host.querySelector('h3').textContent).toBe(article.title);
    expect(host.querySelector('h3').className).toContain('sm:line-clamp-3');
    expect(host.textContent).toContain('Chester');
    expect(host.textContent).toContain('Business');
    if (image) {
      const img = host.querySelector('img');
      expect(img.getAttribute('loading')).toBe('lazy');
      expect(img.parentElement.className).toContain('w-[88px]');
      act(() => img.dispatchEvent(new Event('error')));
      expect(img.getAttribute('src')).toContain('images.unsplash.com');
    } else expect(host.querySelector('img')).toBeNull();
  } finally { act(() => root.unmount()); }
});
