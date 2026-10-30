import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import TopStoriesGrid from './TopStoriesGrid';

test.each(['', '/fixture.jpg'])('Top Stories keeps its four ordered links with intrinsic mobile reflow: %s', image => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  const host = document.createElement('div');
  const root = createRoot(host);
  const stories = Array.from({ length: 5 }, (_, i) => ({
    id: `fixed-${i}`, url: `/article/fixed-${i}/report`,
    title: `Story ${i}: ${'A long Cheshire business headline '.repeat(5)}`,
    category: 'Business', location: 'Chester', publishedDate: '2026-10-30T06:00:00Z', image,
  }));
  try {
    act(() => root.render(<MemoryRouter><TopStoriesGrid stories={stories} /></MemoryRouter>));
    const links = Array.from(host.querySelectorAll('a'));
    expect(links.map(link => link.getAttribute('href'))).toEqual(stories.slice(0, 4).map(story => story.url));
    links.forEach((link, i) => {
      expect(link.classList.contains('flex-wrap')).toBe(true);
      expect(link.classList.contains('lg:grid')).toBe(true);
      expect(link.className).toContain('focus-visible:ring-2');
      expect(link.querySelector('h3').textContent).toBe(stories[i].title);
      expect(link.querySelector('h3').className).not.toContain('line-clamp');
      expect(link.querySelector('h3').parentElement.className).toContain('min-w-[min(100%,10em)]');
      expect(link.textContent).toContain('Chester');
      expect(link.textContent).toContain('min read');
      expect(link.className).toContain('dark:focus-visible:ring-offset-gray-900');
      if (image) expect(link.querySelector('img').getAttribute('loading')).toBe('lazy');
    });
  } finally { act(() => root.unmount()); }
});
