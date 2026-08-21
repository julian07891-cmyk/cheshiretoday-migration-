import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import {
  buildCommercialEventPayload,
  classifyCommercialDevice,
  createCommercialRandomId,
  getCommercialSessionKey,
  submitCommercialEvent,
} from '../utils/commercialEventTracking';


export const COMMERCIAL_VIEWABILITY_THRESHOLD = 0.5;
export const COMMERCIAL_VIEWABILITY_DURATION_MS = 1000;
export const COMMERCIAL_CLIENT_GUARD_LIMIT = 100;

const MEASUREMENT_METADATA_FIELDS = Object.freeze([
  'card_id',
  'provider_id',
  'placement_id',
  'article_id',
  'article_category',
  'use_case',
  'destination_type',
  'destination_id',
  'rule_reason_code',
  'variant_version',
  'disclosure_version',
]);

let navigationState = {
  key: null,
  pageViewId: null,
  submitted: new Map(),
};
const disabledNavigationState = {
  key: null,
  pageViewId: null,
  submitted: new Map(),
};


const stateForNavigation = (navigationKey) => {
  if (typeof navigationKey !== 'string' || !navigationKey) return disabledNavigationState;
  const safeKey = navigationKey;
  if (navigationState.key !== safeKey) {
    navigationState = {
      key: safeKey,
      pageViewId: createCommercialRandomId(16),
      submitted: new Map(),
    };
  }
  return navigationState;
};


const markOnce = (state, eventKey) => {
  if (!eventKey || state.submitted.has(eventKey)) return false;
  state.submitted.set(eventKey, true);
  if (state.submitted.size > COMMERCIAL_CLIENT_GUARD_LIMIT) {
    state.submitted.delete(state.submitted.keys().next().value);
  }
  return true;
};


const eventIdentity = (payload) => payload && [
  payload.event_type,
  payload.provider_id,
  payload.card_id,
  payload.placement_id,
  payload.destination_id,
].join('\x1f');


export const useCommercialCardMeasurement = ({
  metadata,
  navigationKey,
  enabled = true,
}) => {
  const [measuredNode, setMeasuredNode] = useState(null);
  const cardRef = useCallback((node) => setMeasuredNode(node), []);
  const currentNavigation = stateForNavigation(navigationKey);
  const pageViewId = currentNavigation.pageViewId;
  const sessionKey = getCommercialSessionKey();
  const deviceClass = classifyCommercialDevice();
  const metadataKey = MEASUREMENT_METADATA_FIELDS
    .map((field) => String(metadata?.[field] ?? ''))
    .join('\x1f');
  const metadataRef = useRef({ key: null, value: null });
  if (metadataRef.current.key !== metadataKey) {
    metadataRef.current = { key: metadataKey, value: metadata };
  }
  const stableMetadata = metadataRef.current.value;

  const payloadFor = useCallback((eventType) => {
    if (!enabled || !pageViewId || !sessionKey) return null;
    return buildCommercialEventPayload({
      eventType,
      metadata: stableMetadata,
      sessionKey,
      pageViewId,
      deviceClass,
    });
  }, [deviceClass, enabled, pageViewId, sessionKey, stableMetadata]);

  const submitOnce = useCallback((eventType) => {
    const payload = payloadFor(eventType);
    if (!payload || !markOnce(currentNavigation, eventIdentity(payload))) return false;
    void submitCommercialEvent(payload);
    return true;
  }, [currentNavigation, payloadFor]);

  useEffect(() => {
    if (!measuredNode) return undefined;
    submitOnce('rendered');
    return undefined;
  }, [measuredNode, submitOnce]);

  useEffect(() => {
    if (!measuredNode || !payloadFor('viewable') || typeof IntersectionObserver !== 'function') {
      return undefined;
    }

    let timerId = null;
    let qualifyingIntersection = false;
    let viewableComplete = false;

    const clearTimer = () => {
      if (timerId !== null) {
        clearTimeout(timerId);
        timerId = null;
      }
    };

    const beginTimer = () => {
      if (
        timerId !== null ||
        viewableComplete ||
        !qualifyingIntersection ||
        document.visibilityState !== 'visible'
      ) {
        return;
      }
      timerId = setTimeout(() => {
        timerId = null;
        if (
          qualifyingIntersection &&
          document.visibilityState === 'visible' &&
          submitOnce('viewable')
        ) {
          viewableComplete = true;
          observer.disconnect();
        }
      }, COMMERCIAL_VIEWABILITY_DURATION_MS);
    };

    const observer = new IntersectionObserver((entries) => {
      const entry = entries.find((candidate) => candidate.target === measuredNode);
      qualifyingIntersection = Boolean(
        entry?.isIntersecting && entry.intersectionRatio >= COMMERCIAL_VIEWABILITY_THRESHOLD
      );
      if (qualifyingIntersection) beginTimer();
      else clearTimer();
    }, { threshold: [COMMERCIAL_VIEWABILITY_THRESHOLD] });

    const handleVisibilityChange = () => {
      if (document.visibilityState !== 'visible') clearTimer();
      else beginTimer();
    };

    observer.observe(measuredNode);
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      clearTimer();
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      observer.disconnect();
    };
  }, [measuredNode, payloadFor, submitOnce]);

  const onCommercialClick = useCallback(() => {
    submitOnce('clicked');
  }, [submitOnce]);

  return useMemo(() => ({
    cardRef,
    onCommercialClick,
    pageViewId,
  }), [cardRef, onCommercialClick, pageViewId]);
};


export const __resetCommercialMeasurementForTests = () => {
  navigationState = { key: null, pageViewId: null, submitted: new Map() };
};
