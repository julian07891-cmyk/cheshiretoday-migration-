# Finance / Utility Guide Monetisation Cleanup — 2026-04-30

## Summary

Six live finance / utility guide pages were corrected in the live authority-page database from:

`monetisation: affiliate`

to:

`monetisation: none`

because they currently have no approved affiliate tracking links.

The pages remain live, published, and useful as guide-only commercial preparation pages. They are still suitable for internal routing and reader support, but should not show affiliate-supported labelling until real tracking links are added.

## Corrected live guide pages

- `best-mortgage-rates-uk`
- `best-savings-accounts-uk`
- `best-credit-cards-uk`
- `cheap-energy-tariffs-uk`
- `best-broadband-deals-uk`
- `best-isa-platforms-uk`

## Verification result

Each page was verified after update with:

- `monetisation=none`
- `status=published`
- `affiliate_links=0`

## Operating rule confirmed

No approved tracking link = `Guide` / `monetisation: none`

Approved tracking link = `Affiliate` / `monetisation: affiliate`

## Future task

When approved affiliate links become available for mortgages, savings, credit cards, energy, broadband, or ISA platforms:

1. Add approved tracking links to the relevant guide sections.
2. Verify links are live and compliant.
3. Switch that guide back to `monetisation: affiliate`.
4. Keep frontend badge as `Affiliate` only after tracking links exist.
