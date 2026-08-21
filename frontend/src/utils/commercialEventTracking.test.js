import {
  COMMERCIAL_EVENT_ENDPOINT,
  COMMERCIAL_SESSION_STORAGE_KEY,
  buildCommercialEventPayload,
  classifyCommercialDevice,
  createCommercialRandomId,
  getCommercialSessionKey,
  submitCommercialEvent,
} from './commercialEventTracking';


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

const identity = {
  sessionKey: 'SessionKey_1234567890',
  pageViewId: 'page_view_1234567890',
  deviceClass: 'mobile',
};


describe('commercial event transport', () => {
  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
    jest.restoreAllMocks();
  });

  test('generates and reuses a sessionStorage-only cryptographic session key', () => {
    const cryptoObject = {
      getRandomValues: jest.fn((bytes) => {
        bytes.forEach((_, index) => { bytes[index] = index + 1; });
        return bytes;
      }),
    };
    const cookieBefore = document.cookie;
    const first = getCommercialSessionKey(sessionStorage, cryptoObject);
    const second = getCommercialSessionKey(sessionStorage, cryptoObject);

    expect(first).toMatch(/^[A-Za-z0-9_-]{16,128}$/);
    expect(second).toBe(first);
    expect(cryptoObject.getRandomValues).toHaveBeenCalledTimes(1);
    expect(sessionStorage.getItem(COMMERCIAL_SESSION_STORAGE_KEY)).toBe(first);
    expect(localStorage.length).toBe(0);
    expect(document.cookie).toBe(cookieBefore);
  });

  test('fails closed when cryptographic randomness or sessionStorage is unavailable', () => {
    expect(createCommercialRandomId(16, {})).toBeNull();
    expect(getCommercialSessionKey(null, globalThis.crypto)).toBeNull();
    expect(getCommercialSessionKey({ getItem: () => { throw new Error('blocked'); } }, globalThis.crypto)).toBeNull();
  });

  test('builds exactly the backend payload and excludes prohibited reader/content data', () => {
    const result = buildCommercialEventPayload({
      eventType: 'rendered',
      metadata: {
        ...metadata,
        article_title: 'Must not leave the browser',
        destination_url: 'https://merchant.example/private',
        email: 'reader@example.com',
        user_agent: 'browser fingerprint',
      },
      ...identity,
    });

    expect(result).toEqual({
      event_type: 'rendered',
      card_id: 'energy_bills_v1',
      provider_id: 'generic_provider',
      placement_id: 'article_inline',
      article_id: 'article_123',
      article_category: 'business',
      use_case: 'energy_bills',
      destination_type: 'provider',
      destination_id: 'merchant_456',
      device_class: 'mobile',
      rule_reason_code: 'category_match',
      variant_version: 'v1',
      disclosure_version: 'affiliate_v1',
      session_key: 'SessionKey_1234567890',
      page_view_id: 'page_view_1234567890',
    });
    expect(JSON.stringify(result)).not.toMatch(/article_title|article_body|destination_url|email|user_agent|cookie|\bip\b/);
  });

  test('rejects unresolved, malformed, oversized, and article-context payloads', () => {
    expect(buildCommercialEventPayload({ eventType: 'rendered', metadata: null, ...identity })).toBeNull();
    expect(buildCommercialEventPayload({ eventType: 'hovered', metadata, ...identity })).toBeNull();
    expect(buildCommercialEventPayload({
      eventType: 'rendered',
      metadata: { ...metadata, card_id: 'unsafe/card' },
      ...identity,
    })).toBeNull();
    expect(buildCommercialEventPayload({
      eventType: 'rendered',
      metadata: { ...metadata, destination_id: 'd'.repeat(97) },
      ...identity,
    })).toBeNull();
    expect(buildCommercialEventPayload({
      eventType: 'rendered',
      metadata: { ...metadata, article_id: null },
      ...identity,
    })).toBeNull();
  });

  test('classifies only the backend-supported mobile and desktop values', () => {
    expect(classifyCommercialDevice({ matchMedia: () => ({ matches: true }) })).toBe('mobile');
    expect(classifyCommercialDevice({ matchMedia: () => ({ matches: false }) })).toBe('desktop');
    expect(classifyCommercialDevice({ innerWidth: 767 })).toBe('mobile');
    expect(classifyCommercialDevice({ innerWidth: 768 })).toBe('desktop');
  });

  test('uses ordinary JSON fetch for rendered/viewable and keepalive JSON fetch for clicked', async () => {
    const fetchImpl = jest.fn(async () => ({ ok: true }));
    const rendered = buildCommercialEventPayload({ eventType: 'rendered', metadata, ...identity });
    const clicked = buildCommercialEventPayload({ eventType: 'clicked', metadata, ...identity });

    await expect(submitCommercialEvent(rendered, { fetchImpl })).resolves.toBe(true);
    await expect(submitCommercialEvent(clicked, { fetchImpl })).resolves.toBe(true);

    expect(fetchImpl.mock.calls[0][0]).toContain(COMMERCIAL_EVENT_ENDPOINT);
    expect(fetchImpl.mock.calls[0][1]).toEqual({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(rendered),
    });
    expect(fetchImpl.mock.calls[1][1]).toEqual({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(clicked),
      keepalive: true,
    });
  });

  test('swallows synchronous, asynchronous, and unavailable transport failures', async () => {
    const event = buildCommercialEventPayload({ eventType: 'clicked', metadata, ...identity });
    await expect(submitCommercialEvent(event, { fetchImpl: null })).resolves.toBe(false);
    await expect(submitCommercialEvent(event, { fetchImpl: () => { throw new Error('offline'); } })).resolves.toBe(false);
    await expect(submitCommercialEvent(event, { fetchImpl: async () => { throw new Error('offline'); } })).resolves.toBe(false);
  });
});
