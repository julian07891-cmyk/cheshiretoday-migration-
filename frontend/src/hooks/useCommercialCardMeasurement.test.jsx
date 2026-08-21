import React, { act } from 'react';
import { createRoot } from 'react-dom/client';

import * as tracking from '../utils/commercialEventTracking';
import {
  COMMERCIAL_VIEWABILITY_DURATION_MS,
  COMMERCIAL_VIEWABILITY_THRESHOLD,
  __resetCommercialMeasurementForTests,
  useCommercialCardMeasurement,
} from './useCommercialCardMeasurement';


const metadata = {
  card_id: 'energy_bills_v1',
  provider_id: 'generic_provider',
  placement_id: 'article_inline',
  article_id: 'article_123',
  article_category: 'business',
  use_case: 'energy_bills',
  destination_type: 'provider',
  destination_id: 'merchant_456',
  rule_reason_code: 'category_match',
  variant_version: 'v1',
  disclosure_version: 'affiliate_v1',
};

let observerInstances = [];
let visibilityState = 'visible';

class IntersectionObserverMock {
  constructor(callback, options) {
    this.callback = callback;
    this.options = options;
    this.observe = jest.fn();
    this.disconnect = jest.fn();
    observerInstances.push(this);
  }

  emit(target, ratio, isIntersecting = ratio > 0) {
    this.callback([{ target, intersectionRatio: ratio, isIntersecting }]);
  }
}

const Harness = ({ cardMetadata = metadata, navigationKey = 'route-a', show = true }) => {
  const measurement = useCommercialCardMeasurement({
    metadata: cardMetadata,
    navigationKey,
  });
  if (!show) return <div data-testid="empty" data-page-view={measurement.pageViewId} />;
  return (
    <a
      ref={measurement.cardRef}
      href="https://merchant.example/offer"
      target="_blank"
      rel="noopener noreferrer sponsored"
      onClick={measurement.onCommercialClick}
      data-testid="measured-card"
      data-page-view={measurement.pageViewId}
    >
      View offer
    </a>
  );
};


describe('useCommercialCardMeasurement', () => {
  let container;
  let root;
  let submitSpy;
  let originalIntersectionObserver;
  let originalVisibilityDescriptor;
  let originalCryptoDescriptor;

  beforeEach(() => {
    globalThis.IS_REACT_ACT_ENVIRONMENT = true;
    jest.useFakeTimers();
    sessionStorage.clear();
    __resetCommercialMeasurementForTests();
    observerInstances = [];
    visibilityState = 'visible';
    originalIntersectionObserver = global.IntersectionObserver;
    global.IntersectionObserver = IntersectionObserverMock;
    originalCryptoDescriptor = Object.getOwnPropertyDescriptor(globalThis, 'crypto');
    let cryptoCall = 0;
    Object.defineProperty(globalThis, 'crypto', {
      configurable: true,
      value: {
        getRandomValues: (bytes) => {
          cryptoCall += 1;
          bytes.forEach((_, index) => { bytes[index] = (index + 17 + cryptoCall) % 256; });
          return bytes;
        },
      },
    });
    originalVisibilityDescriptor = Object.getOwnPropertyDescriptor(document, 'visibilityState');
    Object.defineProperty(document, 'visibilityState', {
      configurable: true,
      get: () => visibilityState,
    });
    submitSpy = jest.spyOn(tracking, 'submitCommercialEvent').mockResolvedValue(true);
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
  });

  afterEach(() => {
    act(() => root.unmount());
    container.remove();
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
    if (originalIntersectionObserver === undefined) delete global.IntersectionObserver;
    else global.IntersectionObserver = originalIntersectionObserver;
    if (originalCryptoDescriptor) Object.defineProperty(globalThis, 'crypto', originalCryptoDescriptor);
    else delete globalThis.crypto;
    if (originalVisibilityDescriptor) {
      Object.defineProperty(document, 'visibilityState', originalVisibilityDescriptor);
    }
    submitSpy.mockRestore();
    sessionStorage.clear();
    delete globalThis.IS_REACT_ACT_ENVIRONMENT;
  });

  const renderHarness = async (props = {}) => {
    await act(async () => {
      root.render(<Harness {...props} />);
      await Promise.resolve();
    });
  };

  const events = () => submitSpy.mock.calls.map(([event]) => event.event_type);

  test('keeps page identity stable across rerender/remount and changes it for navigation', async () => {
    await renderHarness();
    const first = container.querySelector('[data-testid="measured-card"]').dataset.pageView;
    await renderHarness({ show: false });
    await renderHarness({ show: true });
    const remounted = container.querySelector('[data-testid="measured-card"]').dataset.pageView;
    expect(remounted).toBe(first);
    expect(events().filter((event) => event === 'rendered')).toHaveLength(1);

    await renderHarness({ navigationKey: 'route-b' });
    const second = container.querySelector('[data-testid="measured-card"]').dataset.pageView;
    expect(second).not.toBe(first);
    expect(events().filter((event) => event === 'rendered')).toHaveLength(2);
  });

  test('fires rendered only after a valid measured card commits and once across rerenders', async () => {
    expect(submitSpy).not.toHaveBeenCalled();
    await renderHarness();
    expect(events()).toEqual(['rendered']);
    await renderHarness({ cardMetadata: { ...metadata } });
    expect(events()).toEqual(['rendered']);

    __resetCommercialMeasurementForTests();
    submitSpy.mockClear();
    await renderHarness({ cardMetadata: null, navigationKey: 'unresolved' });
    expect(submitSpy).not.toHaveBeenCalled();

    await renderHarness({ cardMetadata: metadata, navigationKey: '' });
    expect(submitSpy).not.toHaveBeenCalled();
  });

  test('requires 50 percent continuously for 1000ms before one viewable event', async () => {
    await renderHarness();
    const card = container.querySelector('[data-testid="measured-card"]');
    const observer = observerInstances[0];
    expect(observer.options).toEqual({ threshold: [COMMERCIAL_VIEWABILITY_THRESHOLD] });

    act(() => observer.emit(card, 0.49));
    act(() => jest.advanceTimersByTime(COMMERCIAL_VIEWABILITY_DURATION_MS + 1));
    expect(events()).toEqual(['rendered']);

    act(() => observer.emit(card, 0.5));
    act(() => jest.advanceTimersByTime(600));
    await renderHarness({ cardMetadata: { ...metadata } });
    act(() => jest.advanceTimersByTime(COMMERCIAL_VIEWABILITY_DURATION_MS - 601));
    expect(events()).toEqual(['rendered']);
    act(() => jest.advanceTimersByTime(1));
    expect(events()).toEqual(['rendered', 'viewable']);

    act(() => observer.emit(card, 0));
    act(() => observer.emit(card, 1));
    act(() => jest.advanceTimersByTime(COMMERCIAL_VIEWABILITY_DURATION_MS));
    expect(events()).toEqual(['rendered', 'viewable']);
  });

  test('cancels incomplete viewability below threshold and while document is hidden', async () => {
    await renderHarness();
    const card = container.querySelector('[data-testid="measured-card"]');
    const observer = observerInstances[0];

    act(() => observer.emit(card, 0.75));
    act(() => jest.advanceTimersByTime(600));
    act(() => observer.emit(card, 0.25));
    act(() => jest.advanceTimersByTime(500));
    expect(events()).toEqual(['rendered']);

    act(() => observer.emit(card, 0.75));
    act(() => jest.advanceTimersByTime(600));
    visibilityState = 'hidden';
    act(() => document.dispatchEvent(new Event('visibilitychange')));
    act(() => jest.advanceTimersByTime(500));
    expect(events()).toEqual(['rendered']);

    visibilityState = 'visible';
    act(() => document.dispatchEvent(new Event('visibilitychange')));
    act(() => jest.advanceTimersByTime(COMMERCIAL_VIEWABILITY_DURATION_MS));
    expect(events()).toEqual(['rendered', 'viewable']);
  });

  test('clicks once without preventing normal accessible link semantics', async () => {
    await renderHarness();
    const link = container.querySelector('[data-testid="measured-card"]');
    const click = new MouseEvent('click', { bubbles: true, cancelable: true, ctrlKey: true });
    act(() => link.dispatchEvent(click));
    act(() => link.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true })));

    expect(events()).toEqual(['rendered', 'clicked']);
    expect(click.defaultPrevented).toBe(false);
    expect(link.getAttribute('href')).toBe('https://merchant.example/offer');
    expect(link.getAttribute('target')).toBe('_blank');
  });

  test('disconnects observer, removes listener, and clears timer on unmount', async () => {
    const removeSpy = jest.spyOn(document, 'removeEventListener');
    const clearSpy = jest.spyOn(global, 'clearTimeout');
    await renderHarness();
    const card = container.querySelector('[data-testid="measured-card"]');
    const observer = observerInstances[0];
    act(() => observer.emit(card, 0.75));
    act(() => root.unmount());

    expect(observer.disconnect).toHaveBeenCalled();
    expect(removeSpy).toHaveBeenCalledWith('visibilitychange', expect.any(Function));
    expect(clearSpy).toHaveBeenCalled();

    root = createRoot(container);
    removeSpy.mockRestore();
    clearSpy.mockRestore();
  });
});
