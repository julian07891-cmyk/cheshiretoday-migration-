import React, { act } from 'react';
import { createRoot } from 'react-dom/client';

import { CONTEXTUAL_RECOMMENDATIONS } from '../../config/contextualRecommendations';
import {
  COMMERCIAL_VIEWABILITY_DURATION_MS,
  __resetCommercialMeasurementForTests,
} from '../../hooks/useCommercialCardMeasurement';
import * as tracking from '../../utils/commercialEventTracking';
import ContextualRecommendationCard from './ContextualRecommendationCard';


let observerInstances = [];

class IntersectionObserverMock {
  constructor(callback, options) {
    this.callback = callback;
    this.options = options;
    this.observe = jest.fn();
    this.disconnect = jest.fn();
    observerInstances.push(this);
  }

  emit(target, ratio) {
    this.callback([{ target, intersectionRatio: ratio, isIntersecting: ratio > 0 }]);
  }
}


describe('ContextualRecommendationCard', () => {
  let container;
  let root;
  let submitSpy;
  let originalIntersectionObserver;
  let originalCryptoDescriptor;

  beforeEach(() => {
    globalThis.IS_REACT_ACT_ENVIRONMENT = true;
    jest.useFakeTimers();
    sessionStorage.clear();
    __resetCommercialMeasurementForTests();
    observerInstances = [];
    originalIntersectionObserver = global.IntersectionObserver;
    global.IntersectionObserver = IntersectionObserverMock;
    originalCryptoDescriptor = Object.getOwnPropertyDescriptor(globalThis, 'crypto');
    Object.defineProperty(globalThis, 'crypto', {
      configurable: true,
      value: {
        getRandomValues: (bytes) => {
          bytes.forEach((_, index) => { bytes[index] = (index + 23) % 256; });
          return bytes;
        },
      },
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
    submitSpy.mockRestore();
    sessionStorage.clear();
    delete globalThis.IS_REACT_ACT_ENVIRONMENT;
  });

  const renderCard = async (recommendation = CONTEXTUAL_RECOMMENDATIONS[0]) => {
    await act(async () => {
      root.render(
        <ContextualRecommendationCard
          recommendation={recommendation}
          articleId="ARTICLE_123"
          articleCategory="business_finance"
          navigationKey="article-navigation-1"
        />
      );
      await Promise.resolve();
    });
  };

  const eventTypes = () => submitSpy.mock.calls.map(([payload]) => payload.event_type);

  test('renders the complete text-first presentation and safe internal destination', async () => {
    const recommendation = CONTEXTUAL_RECOMMENDATIONS[0];
    await renderCard();

    expect(container.textContent).toContain(recommendation.context_label);
    expect(container.textContent).toContain(recommendation.heading);
    expect(container.textContent).toContain(recommendation.benefit);
    expect(container.textContent).toContain(recommendation.provider_display_name);
    expect(container.textContent).toContain(recommendation.cta);
    expect(container.textContent).toContain(recommendation.disclosure);
    const link = container.querySelector('a');
    expect(link.getAttribute('href')).toBe('/guides/best-accounting-software-uk');
    expect(link.hasAttribute('target')).toBe(false);
    expect(container.querySelectorAll('img')).toHaveLength(0);
    expect(container.querySelectorAll('[data-testid="contextual-recommendation-card"]')).toHaveLength(1);
  });

  test('emits bounded rendered, viewable and clicked metadata once', async () => {
    const recommendation = { ...CONTEXTUAL_RECOMMENDATIONS[0], destination_url: '#guide' };
    await renderCard(recommendation);
    const card = container.querySelector('[data-testid="contextual-recommendation-card"]');
    const link = container.querySelector('a');

    expect(eventTypes()).toEqual(['rendered']);
    expect(submitSpy.mock.calls[0][0]).toMatchObject({
      card_id: 'accounting_software_guide_v1',
      provider_id: 'cheshire_today_guides',
      placement_id: 'article_after_body',
      article_id: 'article_123',
      article_category: 'business_finance',
      destination_type: 'guide',
      destination_id: 'best_accounting_software_uk',
    });

    act(() => observerInstances[0].emit(card, 0.5));
    act(() => jest.advanceTimersByTime(COMMERCIAL_VIEWABILITY_DURATION_MS));
    act(() => link.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true })));
    act(() => link.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true })));
    expect(eventTypes()).toEqual(['rendered', 'viewable', 'clicked']);

    await renderCard(recommendation);
    expect(eventTypes()).toEqual(['rendered', 'viewable', 'clicked']);
  });

  test('keeps navigation functional when tracking reports failure', async () => {
    submitSpy.mockResolvedValue(false);
    await renderCard({ ...CONTEXTUAL_RECOMMENDATIONS[0], destination_url: '#guide' });
    const link = container.querySelector('a');
    const click = new MouseEvent('click', { bubbles: true, cancelable: true, ctrlKey: true });

    act(() => link.dispatchEvent(click));
    expect(click.defaultPrevented).toBe(false);
    expect(link.getAttribute('href')).toBe('#guide');
  });

  test('adds sponsored safety attributes for a future external destination', async () => {
    await renderCard({
      ...CONTEXTUAL_RECOMMENDATIONS[0],
      destination_url: 'https://merchant.example/offer',
      external: true,
    });
    const link = container.querySelector('a');

    expect(link.getAttribute('target')).toBe('_blank');
    expect(link.getAttribute('rel').split(' ').sort()).toEqual(
      ['noopener', 'noreferrer', 'sponsored'].sort()
    );
  });
});
