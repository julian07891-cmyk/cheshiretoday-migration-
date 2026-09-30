import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import HeroMonetisationStrip from './HeroMonetisationStrip';
import { monetisationTools } from '../../config/monetisationTools';
import { FEATURES } from '../../config/features';

jest.mock('../../config/features', () => ({ FEATURES: { NON_AMAZON_MONETISATION_ENABLED: true } }));
jest.mock('../../utils/trackEvent', () => ({ trackEvent: jest.fn() }));
let container, root;
beforeEach(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  jest.useFakeTimers().setSystemTime(new Date('2026-09-27T12:00:00Z'));
  FEATURES.NON_AMAZON_MONETISATION_ENABLED = true;
  container = document.createElement('div'); document.body.appendChild(container);
  root = createRoot(container);
});
afterEach(() => { act(() => root.unmount()); container.remove(); jest.useRealTimers(); });
const render = props => act(() => root.render(<MemoryRouter><HeroMonetisationStrip {...props} /></MemoryRouter>));
const links = () => Array.from(container.querySelectorAll('a')).map(a => a.getAttribute('href'));
const finance = item => /mortgage|savings|energy|tariff|bills|credit|mobile|sim|phone/i.test(`${item.title} ${item.href}`);

test('homepage inventory excludes savings but preserves its other registry entry', () => {
  expect(monetisationTools.homepage_primary.some(i => i.href === '/guides/best-savings-accounts-uk')).toBe(false);
  expect(Object.entries(monetisationTools).some(([key, items]) => key !== 'homepage_primary' && items.some(i => i.href === '/guides/best-savings-accounts-uk'))).toBe(true);
});
test.each([{ focus: 'finance' }, { excludeFocus: 'finance' }])('two unique, deterministic cards preserve partition %j', props => {
  render({ ...props, limit: 2 }); const first = links();
  expect(first).toHaveLength(2); expect(new Set(first).size).toBe(2);
  const pool = monetisationTools.homepage_primary.filter(i => props.focus ? finance(i) : !finance(i));
  expect(first.every(href => pool.some(i => i.href === href))).toBe(true);
  act(() => root.render(null)); render({ ...props, limit: 2 });
  expect(links()).toEqual(first);
});
test('every starting position across fixed days remains unique and savings-free', () => {
  for (let day = 1; day <= 31; day++) {
    jest.setSystemTime(new Date(Date.UTC(2026, 8, day, 12)));
    for (let start = 0; start < monetisationTools.homepage_primary.length; start++) {
      act(() => root.render(null)); render({ start, limit: 2 });
      expect(links()).toHaveLength(2); expect(new Set(links()).size).toBe(2);
      expect(links()).not.toContain('/guides/best-savings-accounts-uk');
    }
  }
});
test('disabled feature renders no cards', () => {
  FEATURES.NON_AMAZON_MONETISATION_ENABLED = false; render({ limit: 2 });
  expect(links()).toEqual([]); expect(container.textContent).toBe('');
});
