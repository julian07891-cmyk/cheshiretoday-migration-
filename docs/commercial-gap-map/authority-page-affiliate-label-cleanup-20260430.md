# Authority Page Affiliate Label Cleanup — 2026-04-30

## Summary

A live authority-page audit found several pages marked as:

`monetisation: affiliate`

even though they had zero approved affiliate links.

These were corrected in the live authority-page database to:

`monetisation: none`

The pages remain published and usable as guide-only pages, but they no longer show affiliate-supported labelling until real approved tracking links are added.

## Corrected pages

- `best-ai-productivity-tools-uk`
- `best-ai-tools-uk`
- `best-ai-writing-tools-uk`
- `best-business-bank-accounts-uk`
- `best-business-credit-cards-uk`
- `cost-of-buying-home-cheshire-2026`
- `council-tax-bands-cheshire`

## Verification result

After cleanup:

- Affiliate-labelled pages with zero affiliate links: `0`
- All remaining `monetisation=affiliate` pages have at least one populated `affiliate_link`
- Guide-only pages remain published with `monetisation=none`

## Operating rule confirmed

No approved tracking link = `Guide` / `monetisation: none`

Approved tracking link = `Affiliate` / `monetisation: affiliate`

## Future task

When approved tracking links are added to any guide-only page:

1. Add only approved/compliant tracking links.
2. Verify the live guide has at least one populated `affiliate_link`.
3. Change `monetisation` back to `affiliate`.
4. Confirm the affiliate disclosure appears correctly.
