import { getApiUrl } from './api';


export const COMMERCIAL_SESSION_STORAGE_KEY = 'ct_commercial_session_v1';
export const COMMERCIAL_EVENT_TYPES = Object.freeze(['rendered', 'viewable', 'clicked']);
export const COMMERCIAL_EVENT_ENDPOINT = '/api/commercial-events';
export const MOBILE_MEDIA_QUERY = '(max-width: 767px)';

const IDENTIFIER_PATTERN = /^[a-z0-9_-]+$/;
const SESSION_PATTERN = /^[A-Za-z0-9_-]+$/;
const DESTINATION_TYPES = new Set(['advertiser', 'affiliate', 'guide', 'product', 'provider']);
const DEVICE_CLASSES = new Set(['mobile', 'desktop']);

const FIELD_LIMITS = Object.freeze({
  card_id: 64,
  provider_id: 48,
  placement_id: 48,
  article_id: 64,
  article_category: 32,
  use_case: 48,
  destination_id: 96,
  rule_reason_code: 64,
  variant_version: 32,
  disclosure_version: 32,
  page_view_id: 64,
});

const REQUIRED_METADATA_FIELDS = Object.freeze([
  'card_id',
  'provider_id',
  'placement_id',
  'use_case',
  'destination_type',
  'destination_id',
  'rule_reason_code',
  'variant_version',
  'disclosure_version',
]);


export const createCommercialRandomId = (byteLength = 16, cryptoObject = globalThis.crypto) => {
  if (!cryptoObject || typeof cryptoObject.getRandomValues !== 'function') return null;
  const bytes = new Uint8Array(byteLength);
  cryptoObject.getRandomValues(bytes);
  return Array.from(bytes, (value) => value.toString(16).padStart(2, '0')).join('');
};


export const getCommercialSessionKey = (
  storage,
  cryptoObject = globalThis.crypto,
) => {
  try {
    const sessionStore = storage === undefined ? globalThis.sessionStorage : storage;
    if (!sessionStore) return null;
    const existing = sessionStore.getItem(COMMERCIAL_SESSION_STORAGE_KEY);
    if (existing && existing.length >= 16 && existing.length <= 128 && SESSION_PATTERN.test(existing)) {
      return existing;
    }
    const generated = createCommercialRandomId(24, cryptoObject);
    if (!generated) return null;
    sessionStore.setItem(COMMERCIAL_SESSION_STORAGE_KEY, generated);
    return generated;
  } catch (_) {
    return null;
  }
};


export const classifyCommercialDevice = (browserWindow = globalThis.window) => {
  if (!browserWindow) return 'desktop';
  if (typeof browserWindow.matchMedia === 'function') {
    return browserWindow.matchMedia(MOBILE_MEDIA_QUERY).matches ? 'mobile' : 'desktop';
  }
  return Number(browserWindow.innerWidth) < 768 ? 'mobile' : 'desktop';
};


const normaliseIdentifier = (value, maximum, { optional = false } = {}) => {
  if (value === null || value === undefined || value === '') return optional ? null : undefined;
  if (typeof value !== 'string') return undefined;
  const normalised = value.trim().toLowerCase();
  if (!normalised || normalised.length > maximum || !IDENTIFIER_PATTERN.test(normalised)) {
    return undefined;
  }
  return normalised;
};


export const buildCommercialEventPayload = ({
  eventType,
  metadata,
  sessionKey,
  pageViewId,
  deviceClass,
}) => {
  if (!COMMERCIAL_EVENT_TYPES.includes(eventType) || !metadata || typeof metadata !== 'object') {
    return null;
  }
  if (
    typeof sessionKey !== 'string' ||
    sessionKey.length < 16 ||
    sessionKey.length > 128 ||
    !SESSION_PATTERN.test(sessionKey)
  ) {
    return null;
  }

  const identifiers = {};
  for (const [field, maximum] of Object.entries(FIELD_LIMITS)) {
    if (field === 'page_view_id') continue;
    const optional = field === 'article_id' || field === 'article_category';
    identifiers[field] = normaliseIdentifier(metadata[field], maximum, { optional });
    if (!optional && identifiers[field] === undefined) return null;
    if (optional && metadata[field] && identifiers[field] === undefined) return null;
  }

  const normalisedPageViewId = normaliseIdentifier(pageViewId, FIELD_LIMITS.page_view_id);
  if (!normalisedPageViewId || normalisedPageViewId.length < 16) return null;
  if (!DESTINATION_TYPES.has(metadata.destination_type)) return null;
  if (!DEVICE_CLASSES.has(deviceClass)) return null;
  if (identifiers.placement_id.startsWith('article_') && !identifiers.article_id) return null;
  if (REQUIRED_METADATA_FIELDS.some((field) => metadata[field] === undefined)) return null;

  return {
    event_type: eventType,
    card_id: identifiers.card_id,
    provider_id: identifiers.provider_id,
    placement_id: identifiers.placement_id,
    article_id: identifiers.article_id,
    article_category: identifiers.article_category,
    use_case: identifiers.use_case,
    destination_type: metadata.destination_type,
    destination_id: identifiers.destination_id,
    device_class: deviceClass,
    rule_reason_code: identifiers.rule_reason_code,
    variant_version: identifiers.variant_version,
    disclosure_version: identifiers.disclosure_version,
    session_key: sessionKey,
    page_view_id: normalisedPageViewId,
  };
};


export const submitCommercialEvent = (payload, { fetchImpl = globalThis.fetch } = {}) => {
  if (!payload || typeof fetchImpl !== 'function') return Promise.resolve(false);
  const api = getApiUrl().replace(/\/$/, '');
  const request = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  };
  if (payload.event_type === 'clicked') request.keepalive = true;

  return Promise.resolve()
    .then(() => fetchImpl(`${api}${COMMERCIAL_EVENT_ENDPOINT}`, request))
    .then((response) => Boolean(response?.ok))
    .catch(() => false);
};
