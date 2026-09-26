import React from 'react';
import { act } from 'react-dom/test-utils';
import { createRoot } from 'react-dom/client';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import AuthorityPage from './AuthorityPage';
import { AffiliateWidgetSidebar, AffiliateWidgetInline, AffiliateWidgetEndArticle, AffiliateWidgetMobile, getAmazonLink } from '../components/AffiliateWidgets';
import CommercialOutboundLink, { isAffiliateDestination } from '../components/monetisation/CommercialOutboundLink';
import * as measurement from '../hooks/useCommercialCardMeasurement';
import * as tracking from '../utils/commercialEventTracking';
import { __resetCommercialMeasurementForTests } from '../hooks/useCommercialCardMeasurement';

jest.mock('../components/NewsHeader', () => () => null);
jest.mock('../components/NewsFooter', () => () => null);
jest.mock('../components/ui/badge', () => ({ Badge: ({ children }) => <span>{children}</span> }));

let root, container, submit;
beforeEach(() => {
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  sessionStorage.clear();
  sessionStorage.setItem(tracking.COMMERCIAL_SESSION_STORAGE_KEY, 'test_session_1234567890');
  __resetCommercialMeasurementForTests();
  jest.spyOn(tracking, 'createCommercialRandomId').mockReturnValue('1234567890abcdef1234567890abcdef');
  submit = jest.spyOn(tracking, 'submitCommercialEvent').mockResolvedValue(true);
});
afterEach(() => {
  act(() => root.unmount());
  container.remove();
  jest.restoreAllMocks();
  delete global.fetch;
  delete globalThis.IS_REACT_ACT_ENVIRONMENT;
});
async function render(element) {
  await act(async () => {
    root.render(<HelmetProvider><MemoryRouter initialEntries={['/guides/test-guide']}>{element}</MemoryRouter></HelmetProvider>);
  });
}
async function guide(tools, monetisation = 'affiliate') {
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => ({
    title: 'Comparison', slug: 'test-guide', monetisation, category: 'Business', sections: tools,
  }) });
  await render(<Routes><Route path="/guides/:slug" element={<AuthorityPage />} /></Routes>);
}
const tool = (name, affiliate_link = '') => ({ type: 'tool', name, content: `${name} editorial details`, affiliate_link });
const click = (node) => act(() => {
  // Cancel only the synthetic test navigation; production handlers must not cancel it.
  node.addEventListener('click', e => e.preventDefault(), { once: true });
  node.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
});

test('linked and unlinked options remain visible, ordered, without automatic endorsement', async () => {
  await guide([tool('Editorial One'), tool('Linked Two', 'https://www.awin1.com/cread.php?awinmid=1&awinaffid=2'), tool('Editorial Three')]);
  expect(container.textContent).toContain('Editorial One editorial details');
  expect(container.textContent).toContain('Editorial Three editorial details');
  expect(container.textContent).not.toMatch(/Our top pick|Why we picked|Recommended tools/);
  const outbound = [...container.querySelectorAll('a[target="_blank"]')];
  expect(outbound.length).toBeGreaterThan(0);
  expect(outbound.every(a => a.href.includes('awin1.com'))).toBe(true);
  expect(outbound.every(a => a.rel === 'sponsored noreferrer noopener')).toBe(true);
});
test('all-unlinked comparisons preserve every editorial option without outbound CTAs', async () => {
  await guide([tool('First'), tool('Second'), tool('Third'), tool('Fourth')]);
  for (const name of ['First', 'Second', 'Third', 'Fourth']) expect(container.textContent).toContain(`${name} editorial details`);
  expect(container.querySelectorAll('a[target="_blank"]')).toHaveLength(0);
  expect(container.textContent).not.toMatch(/Affiliate supported|earn commission/);
});
test('quick comparison click retains destination and emits exactly one bounded first-party click', async () => {
  const url = 'https://www.awin1.com/cread.php?awinmid=1&awinaffid=2';
  await guide([tool('First', url), tool('Second'), tool('Third')]);
  const a = [...container.querySelectorAll('a')].find(a => a.textContent.trim() === 'Visit →');
  expect(a).toBeDefined();
  expect(a.getAttribute('href')).toBe(url);
  click(a);
  const calls = submit.mock.calls.map(([p]) => p).filter(p => p.event_type === 'clicked');
  expect(calls).toHaveLength(1);
  expect(calls[0]).toMatchObject({ placement_id: 'guide_quick_comparison', destination_id: 'test-guide', provider_id: 'first' });
  expect(JSON.stringify(calls[0])).not.toMatch(/https|awinmid|awinaffid/);
});
test('plain editorial provider link is not marked sponsored', async () => {
  await guide([tool('Plain', 'https://www.create.net/')]);
  expect(container.querySelector('a[target="_blank"]').rel).toBe('noreferrer noopener');
});
test.each([undefined, '', '   '])('linked title-only provider resolves a trimmed label when name is %s', async name => {
  const url = 'https://www.awin1.com/cread.php?awinmid=1&awinaffid=2';
  const entry = Object.freeze({ type: 'tool', name, title: '  Title Provider  ', content: 'Details', affiliate_link: url });
  await guide([entry]);
  const link = container.querySelector('a[target="_blank"]');
  expect(container.textContent).toContain('Title Provider');
  expect(link).not.toBeNull();
  expect(link.getAttribute('href')).toBe(url);
  click(link);
  expect(submit.mock.calls.map(([p]) => p).filter(p => p.event_type === 'clicked')).toEqual([
    expect.objectContaining({ provider_id: 'title-provider', placement_id: 'guide_provider_list' }),
  ]);
  expect(entry.title).toBe('  Title Provider  ');
  expect(entry.name).toBe(name);
});
test('unlinked title-only provider remains visible without CTA', async () => {
  await guide([{ type: 'tool', title: '  Unlinked title  ', content: 'Editorial detail' }]);
  expect(container.textContent).toContain('Unlinked title');
  expect(container.textContent).toContain('Editorial detail');
  expect(container.querySelectorAll('a[target="_blank"]')).toHaveLength(0);
});
test('trimmed name takes precedence over title for display and measurement', async () => {
  await guide([{ ...tool('  Named provider  ', 'https://example.invalid/'), title: 'Alternate title', content: 'Details' }]);
  expect(container.textContent).toContain('Named provider');
  expect(container.textContent).not.toContain('Alternate title');
  click(container.querySelector('a[target="_blank"]'));
  expect(submit.mock.calls.map(([p]) => p).find(p => p.event_type === 'clicked').provider_id).toBe('named-provider');
});
test('unlabelled entries are omitted and mixed valid providers retain actual DOM order', async () => {
  await guide([
    tool(' First '),
    { type: 'tool', name: ' ', title: ' Second ', content: 'Details' },
    { type: 'tool', content: 'Invalid absent', affiliate_link: 'https://example.invalid/' },
    { type: 'tool', name: ' ', title: ' ', content: 'Invalid blank' },
    tool('Third'),
    { type: 'tool', title: 'Fourth', content: 'Details' },
  ]);
  const list = [...container.querySelectorAll('section')].find(s => s.textContent.includes('Comparison options'));
  const labels = [...list.querySelectorAll('.text-base.font-black')].map(n => n.textContent);
  expect(labels).toEqual(['First', 'Second', 'Third', 'Fourth']);
  expect(container.textContent).not.toMatch(/Invalid absent|Invalid blank|Our top pick/);
});
test('main provider CTA is measured, unchanged and disclosed even with stale none metadata', async () => {
  const url = 'https://www.jdoqocy.com/click-123-456';
  await guide([tool('Provider', url)], 'none');
  const a = container.querySelector('a[target="_blank"]');
  expect(a.getAttribute('href')).toBe(url);
  expect(container.textContent).toContain('Affiliate disclosure');
  click(a);
  const clicks = submit.mock.calls.map(([p]) => p).filter(p => p.event_type === 'clicked');
  expect(clicks).toHaveLength(1);
  expect(clicks[0]).toMatchObject({ placement_id: 'guide_provider_list', destination_id: 'test-guide', provider_id: 'provider' });
});
test.each([
  ['https://www.awin1.com/cread.php?awinmid=1', true],
  ['https://www.jdoqocy.com/click-1-2', true],
  ['https://quickbooks.intuit.com/uk/?cid=aff_uk_CJ_test', true],
  ['https://click.123-reg.co.uk/affiliate?url=x', true],
  ['https://www.create.net/', false],
  ['https://www.interparcel.com/', false],
  ['https://www.awin1.com.evil.example/', false],
])('commercial relationship evidence: %s', (url, expected) => expect(isAffiliateDestination(url)).toBe(expected));
test.each([
  ['https://amazon.co.uk/s?k=tools', 'amazon.co.uk'],
  ['https://www.amazon.co.uk/s?k=tools', 'www.amazon.co.uk'],
  ['https://www.amazon.co.uk/s?k=tools&tag=other', 'www.amazon.co.uk'],
  ['https://www.amazon.co.uk/s?k=tools&tag=cheshiretoday-21', 'www.amazon.co.uk'],
  ['https://www.amazon.co.uk/s?k=tools&tag=cheshiretoday-21&tag=other', 'www.amazon.co.uk'],
])('Amazon tag is singular and deterministic: %s', (input, host) => {
  const u = new URL(getAmazonLink(input));
  expect(u.hostname).toBe(host);
  expect(u.searchParams.getAll('tag')).toEqual(['cheshiretoday-21']);
  expect(u.searchParams.get('k')).toBe('tools');
});
test.each(['https://amazon.co.uk.evil.example/s?k=x', 'https://example.com/?next=amazon.co.uk', 'https://amazon.co.uk@evil.example/', 'ftp://amazon.co.uk/s', 'not a URL'])('non-Amazon or malformed input unchanged: %s', input => {
  expect(getAmazonLink(input)).toBe(input);
});
test.each([AffiliateWidgetInline, AffiliateWidgetEndArticle, AffiliateWidgetMobile])('dormant widget fallback also avoids unsupported claims', async (Widget) => {
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => ({ success: true, products: [] }) });
  await render(<Widget />);
  expect(container.textContent).not.toMatch(/£|Handpicked|Recommended|Featured Deal|4\.[0-9]/);
  expect(container.textContent).toContain('commission');
});
test('inventory failure uses truthful fallback without a real request', async () => {
  global.fetch = jest.fn().mockRejectedValue(new Error('synthetic'));
  await render(<AffiliateWidgetSidebar />);
  expect(container.textContent).toContain('Shop on Amazon');
  expect(container.textContent).not.toMatch(/£|4\.[0-9]/);
});
test('measurement failure cannot cancel normal navigation', async () => {
  jest.spyOn(measurement, 'useCommercialCardMeasurement').mockReturnValue({ cardRef: () => {}, onCommercialClick: () => { throw new Error('synthetic'); } });
  await render(<CommercialOutboundLink href="https://example.invalid/" provider="test" destination="test" placement="guide_provider_list" useCase="guide_comparison">Visit</CommercialOutboundLink>);
  const a = container.querySelector('a');
  let cancelledByApplication;
  const observer = e => { cancelledByApplication = e.defaultPrevented; e.preventDefault(); };
  document.addEventListener('click', observer);
  act(() => a.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true })));
  document.removeEventListener('click', observer);
  expect(cancelledByApplication).toBe(false);
});
test('Amazon fallback has truthful copy, no prices/ratings, disclosure and one click event', async () => {
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => ({ success: true, products: [], by_category: {} }) });
  await render(<AffiliateWidgetSidebar />);
  expect(container.textContent).not.toMatch(/£|Handpicked|Top Picks|View Deal|4\.[0-9]/);
  expect(container.textContent).toContain('Shop on Amazon');
  expect(container.textContent).toContain('We may earn commission');
  expect(container.textContent).toContain('Ad');
  const a = container.querySelector('a[target="_blank"]');
  expect(new URL(a.href).searchParams.getAll('tag')).toEqual(['cheshiretoday-21']);
  click(a);
  const calls = submit.mock.calls.map(([p]) => p).filter(p => p.event_type === 'clicked');
  expect(calls).toHaveLength(1);
  expect(calls[0]).toMatchObject({ provider_id: 'amazon', placement_id: 'homepage_sidebar', use_case: 'default' });
  expect(JSON.stringify(calls[0])).not.toMatch(/https|tag=/);
});
