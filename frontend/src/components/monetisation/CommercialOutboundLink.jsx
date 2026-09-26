import React from 'react';
import { useLocation } from 'react-router-dom';
import { useCommercialCardMeasurement } from '../../hooks/useCommercialCardMeasurement';

// Public editorial identifiers only; never pass URLs, tracking parameters or user data.
export const commercialKey = (value, max = 48) => String(value || '')
  .toLowerCase().replace(/[^a-z0-9_-]+/g, '-').replace(/^-+|-+$/g, '').slice(0, max) || 'unknown';

export const isAffiliateDestination = (href) => {
  try {
    const url = new URL(href);
    if (!['http:', 'https:'].includes(url.protocol)) return false;
    const host = url.hostname.toLowerCase();
    return ['awin1.com', 'www.awin1.com', 'jdoqocy.com', 'www.jdoqocy.com'].includes(host)
      || (['amazon.co.uk', 'www.amazon.co.uk'].includes(host) && url.searchParams.has('tag'))
      || (host === 'quickbooks.intuit.com' && /^aff_uk_CJ_/.test(url.searchParams.get('cid') || ''))
      || (host === 'click.123-reg.co.uk' && url.pathname === '/affiliate');
  } catch (_) {
    return false;
  }
};

export default function CommercialOutboundLink({ href, provider, destination, placement, useCase, children, className }) {
  const location = useLocation();
  const affiliate = isAffiliateDestination(href);
  const measurement = useCommercialCardMeasurement({
    navigationKey: location.key,
    metadata: {
      card_id: commercialKey(`${destination}-${provider}`, 64),
      provider_id: commercialKey(provider),
      placement_id: commercialKey(placement),
      use_case: commercialKey(useCase),
      destination_type: provider === 'amazon' ? 'product' : 'provider',
      destination_id: commercialKey(destination, 96),
      rule_reason_code: 'existing_commercial_outbound',
      variant_version: 'commercial_trust_v1',
      disclosure_version: affiliate ? 'affiliate_v1' : 'editorial_link_v1',
    },
  });
  return <a href={href} target="_blank" className={className}
    rel={affiliate ? 'sponsored noreferrer noopener' : 'noreferrer noopener'}
    ref={measurement.cardRef}
    onClick={() => {
      // Measurement must never block ordinary navigation, even on local storage/runtime failure.
      try { measurement.onCommercialClick(); } catch (_) { /* best effort */ }
    }}>{children}</a>;
}
