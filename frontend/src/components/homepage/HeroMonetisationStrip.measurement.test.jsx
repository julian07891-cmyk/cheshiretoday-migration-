import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import HeroMonetisationStrip from './HeroMonetisationStrip';
import { monetisationTools } from '../../config/monetisationTools';
import { FEATURES } from '../../config/features';
import * as tracking from '../../utils/commercialEventTracking';
import * as legacy from '../../utils/trackEvent';
import { __resetCommercialMeasurementForTests } from '../../hooks/useCommercialCardMeasurement';
import { ANALYTICS_SCRIPT_IDS, __resetAnalyticsProvidersForTests, enableAnalyticsProviders, disableAnalyticsProviders } from '../../analytics/analyticsProviders';

jest.mock('../../config/features', () => ({ FEATURES: { NON_AMAZON_MONETISATION_ENABLED: true } }));

let root, container, observers, submit, visibility;
let originalObserver, originalCrypto, originalVisibility, originalWidth, originalDomain;
const events = type => submit.mock.calls.map(([payload]) => payload).filter(p => p.event_type === type);
const render = async (props = {}) => act(async () => {
  root.render(<MemoryRouter><HeroMonetisationStrip limit={2} compact focus="finance" placement="homepage_finance_guides" {...props} /></MemoryRouter>);
});
const click = async link => {
  const event = new MouseEvent('click', { bubbles: true, cancelable: true });
  let preventedByApplication;
  // Observe after React's handler, then suppress only jsdom's unsupported navigation.
  document.addEventListener('click', e => {
    preventedByApplication = e.defaultPrevented;
    e.preventDefault();
  }, { once: true });
  await act(async () => link.dispatchEvent(event));
  expect(preventedByApplication).toBe(false);
};

beforeEach(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  jest.useFakeTimers().setSystemTime(new Date('2026-09-27T12:00:00Z'));
  FEATURES.NON_AMAZON_MONETISATION_ENABLED = true;
  sessionStorage.clear();
  __resetCommercialMeasurementForTests();
  __resetAnalyticsProvidersForTests();
  Object.values(ANALYTICS_SCRIPT_IDS).forEach(id => document.getElementById(id)?.remove());
  originalDomain = process.env.REACT_APP_PLAUSIBLE_DOMAIN;
  process.env.REACT_APP_PLAUSIBLE_DOMAIN = 'example.invalid';
  originalObserver = global.IntersectionObserver;
  originalCrypto = Object.getOwnPropertyDescriptor(globalThis, 'crypto');
  originalVisibility = Object.getOwnPropertyDescriptor(document, 'visibilityState');
  originalWidth = Object.getOwnPropertyDescriptor(window, 'innerWidth');
  Object.defineProperty(globalThis, 'crypto', { configurable: true, value: { getRandomValues: bytes => bytes.fill(17) } });
  visibility = 'visible';
  Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => visibility });
  observers = [];
  global.IntersectionObserver = class {
    constructor(callback) { this.callback = callback; observers.push(this); }
    observe(target) { this.target = target; }
    disconnect() {}
    emit(ratio) { this.callback([{ target: this.target, isIntersecting: ratio > 0, intersectionRatio: ratio }]); }
  };
  submit = jest.spyOn(tracking, 'submitCommercialEvent').mockResolvedValue(true);
  jest.spyOn(console, 'log').mockImplementation(() => {});
  container = document.createElement('div'); document.body.appendChild(container);
  root = createRoot(container);
});
afterEach(() => {
  act(() => root.unmount()); container.remove();
  jest.clearAllTimers(); jest.useRealTimers(); jest.restoreAllMocks();
  global.IntersectionObserver = originalObserver;
  if (originalCrypto) Object.defineProperty(globalThis, 'crypto', originalCrypto);
  if (originalVisibility) Object.defineProperty(document, 'visibilityState', originalVisibility);
  else delete document.visibilityState;
  Object.defineProperty(window, 'innerWidth', originalWidth);
  if (originalDomain === undefined) delete process.env.REACT_APP_PLAUSIBLE_DOMAIN;
  else process.env.REACT_APP_PLAUSIBLE_DOMAIN = originalDomain;
  Object.values(ANALYTICS_SCRIPT_IDS).forEach(id => document.getElementById(id)?.remove());
  __resetAnalyticsProvidersForTests();
});

test.each([
  [{}, 'homepage_finance_guides'],
  [{ focus: '', excludeFocus: 'finance', placement: 'homepage_popular_guides' }, 'homepage_popular_guides'],
  [{ focus: '', limit: 1, sidebar: true, placement: 'homepage_sidebar_guide' }, 'homepage_sidebar_guide'],
])('only selected cards render bounded measurements once: %s', async (props, placement) => {
  await render(props);
  const hrefs = [...container.querySelectorAll('a')].map(a => a.getAttribute('href'));
  expect(hrefs).toHaveLength(props.limit || 2);
  const selected = hrefs.map(href => monetisationTools.homepage_primary.find(item => item.href === href));
  expect(events('rendered')).toHaveLength(props.limit || 2);
  expect(events('rendered').map(p => p.destination_id)).toEqual(selected.map(i => i.guideId));
  for (const payload of events('rendered')) {
    expect(payload).toEqual({
      event_type: 'rendered', card_id: payload.destination_id,
      provider_id: 'cheshire_today_guides', placement_id: placement,
      destination_type: 'guide', destination_id: expect.stringMatching(/^[a-z0-9_]+$/),
      use_case: 'guide_discovery', rule_reason_code: 'homepage_daily_rotation',
      variant_version: 'homepage_guides_v1', disclosure_version: 'homepage_affiliate_strip_v1',
      article_id: null, article_category: null, device_class: 'desktop',
      session_key: expect.any(String), page_view_id: expect.any(String),
    });
    expect(JSON.stringify(payload)).not.toMatch(/https?:|\/guides\/|\?|@/);
  }
  await render(props);
  expect(events('rendered')).toHaveLength(props.limit || 2);
});

test('sidebar measures one rendered, viewable and clicked guide with dedupe', async () => {
  await render({ focus: '', limit: 1, sidebar: true, placement: 'homepage_sidebar_guide' });
  act(() => observers[0].emit(0.5));
  act(() => jest.advanceTimersByTime(1000));
  await click(container.querySelector('a'));
  await click(container.querySelector('a'));
  for (const type of ['rendered', 'viewable', 'clicked']) {
    expect(events(type)).toHaveLength(1);
    expect(events(type)[0].placement_id).toBe('homepage_sidebar_guide');
  }
});

test('viewability requires continuous 50 percent for 1000ms and cancels on visibility loss', async () => {
  await render();
  expect(observers).toHaveLength(2);
  act(() => observers[0].emit(0.49));
  act(() => jest.advanceTimersByTime(1100));
  expect(events('viewable')).toHaveLength(0);
  act(() => observers[0].emit(0.5));
  act(() => jest.advanceTimersByTime(600));
  act(() => observers[0].emit(0.2));
  act(() => jest.advanceTimersByTime(500));
  expect(events('viewable')).toHaveLength(0);
  act(() => observers[0].emit(0.5));
  act(() => jest.advanceTimersByTime(600));
  visibility = 'hidden'; act(() => document.dispatchEvent(new Event('visibilitychange')));
  act(() => jest.advanceTimersByTime(1000));
  expect(events('viewable')).toHaveLength(0);
  visibility = 'visible'; act(() => document.dispatchEvent(new Event('visibilitychange')));
  act(() => jest.advanceTimersByTime(999));
  expect(events('viewable')).toHaveLength(0);
  act(() => jest.advanceTimersByTime(1));
  expect(events('viewable')).toHaveLength(1);
});

test('clicks dedupe across rerenders without changing native same-tab links or legacy payload', async () => {
  const legacySpy = jest.spyOn(legacy, 'trackEvent');
  await render();
  const link = container.querySelector('a');
  const href = link.getAttribute('href');
  expect(link.hasAttribute('target')).toBe(false);
  await click(link); await render(); await click(container.querySelector('a'));
  expect(events('clicked')).toHaveLength(1);
  expect(legacySpy).toHaveBeenCalledTimes(2);
  expect(legacySpy).toHaveBeenLastCalledWith('guide_click', {
    placement: 'homepage_monetisation_strip', href, start: 0, compact: true,
    title: monetisationTools.homepage_primary.find(i => i.href === href).title,
  });
});

test('real analytics consent gate stays separate from commercial measurement', async () => {
  await render(); await click(container.querySelector('a'));
  expect(events('clicked')).toHaveLength(1);
  expect(document.getElementById(ANALYTICS_SCRIPT_IDS.plausible)).toBeNull();
  const enabled = enableAnalyticsProviders();
  Object.values(ANALYTICS_SCRIPT_IDS).forEach(id => document.getElementById(id)?.dispatchEvent(new Event('load')));
  await enabled;
  window.plausible = jest.fn();
  await click(container.querySelectorAll('a')[1]);
  expect(window.plausible).toHaveBeenCalledWith('guide_click', { props: expect.objectContaining({ placement: 'homepage_monetisation_strip' }) });
  disableAnalyticsProviders(); window.plausible.mockClear();
  await click(container.querySelector('a'));
  expect(window.plausible).not.toHaveBeenCalled();
  expect(events('clicked')).toHaveLength(2);
});

test('legacy failure does not prevent first-party click or navigation', async () => {
  jest.spyOn(legacy, 'trackEvent').mockImplementation(() => { throw new Error('fixture'); });
  await render(); await click(container.querySelector('a'));
  expect(events('clicked')).toHaveLength(1);
});

test('commercial runtime failure does not prevent legacy click or navigation', async () => {
  const legacySpy = jest.spyOn(legacy, 'trackEvent');
  await render(); submit.mockImplementation(() => { throw new Error('fixture'); });
  await click(container.querySelector('a'));
  expect(legacySpy).toHaveBeenCalledTimes(1);
});

test('actual rejected transport is harmless and not retried', async () => {
  submit.mockRestore();
  const originalFetch = global.fetch;
  global.fetch = jest.fn().mockRejectedValue(new Error('offline fixture'));
  try {
    await render(); await click(container.querySelector('a')); await click(container.querySelector('a'));
    expect(global.fetch).toHaveBeenCalledTimes(3);
    expect(global.fetch.mock.calls[2][1].keepalive).toBe(true);
  } finally { global.fetch = originalFetch; }
});

test.each([390, 1440])('uses shared device classification at %ipx', async width => {
  Object.defineProperty(window, 'innerWidth', { configurable: true, value: width });
  await render();
  expect(events('rendered')).toHaveLength(2);
  expect(events('rendered').every(p => p.device_class === (width < 768 ? 'mobile' : 'desktop'))).toBe(true);
});

test('disabled feature emits no commercial events', async () => {
  FEATURES.NON_AMAZON_MONETISATION_ENABLED = false;
  await render(); expect(container.textContent).toBe(''); expect(submit).not.toHaveBeenCalled();
});

test('all homepage IDs are explicit, unique, bounded and missing placement does not invent attribution', async () => {
  const ids = monetisationTools.homepage_primary.map(i => i.guideId);
  expect(ids).toHaveLength(9);
  expect(new Set(ids).size).toBe(9);
  expect(ids.every(id => typeof id === 'string' && /^[a-z0-9_]{1,64}$/.test(id))).toBe(true);
  await render({ placement: undefined });
  expect(container.querySelectorAll('a')).toHaveLength(2);
  await click(container.querySelector('a'));
  expect(submit).not.toHaveBeenCalled();
});

test('missing or invalid explicit identifiers fail measurement closed without hiding cards', async () => {
  const original = monetisationTools.homepage_primary;
  monetisationTools.homepage_primary = original.slice(0, 2).map((item, index) => ({ ...item, guideId: index ? 'https://bad.invalid/?email=private' : undefined }));
  try {
    await render({ focus: '' });
    expect(container.querySelectorAll('a')).toHaveLength(2);
    await click(container.querySelector('a'));
    expect(submit).not.toHaveBeenCalled();
  } finally { monetisationTools.homepage_primary = original; }
});
