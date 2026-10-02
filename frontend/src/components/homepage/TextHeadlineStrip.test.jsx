import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import TextHeadlineStrip from './TextHeadlineStrip';

test('reading time remains default-on but can be hidden without changing links', async () => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  const container = document.createElement('div');
  const root = createRoot(container);
  const articles = [{ id: 'story', title: 'Headline', summary: 'Short summary.', url: '/article/story/headline' }];
  const render = async props => act(async () => root.render(<MemoryRouter><TextHeadlineStrip articles={articles} {...props} /></MemoryRouter>));
  try {
    await render({});
    expect(container.textContent).toContain('1 min read');
    await render({ showReadTime: false });
    expect(container.textContent).not.toContain('min read');
    expect(container.querySelector('a').getAttribute('href')).toBe('/article/story/headline');
  } finally { act(() => root.unmount()); }
});
