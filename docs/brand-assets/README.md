# Cheshire Today Brand Asset Library

This directory is the permanent repository for approved Cheshire Today brand masters, production exports and the supporting rules needed to use them consistently. It implements the asset-library portion of the **Cheshire Today Brand Identity & Social Media System** project while retaining the production website as the visual source of truth.

The library is for social publishing, website production, newsletters, partnerships, sponsorship and future commercial materials. It does not replace frontend design tokens or alter the website design system.

## Approved production baseline

### Colours

| Role | Value | Use |
| --- | --- | --- |
| Cheshire royal blue | `#1E3A8A` | Primary identity, mastheads and principal actions |
| Cheshire royal blue hover | `#1B357D` | Darker interaction or tonal variant |
| Editorial emerald | `#047857` | Editorial and positive-impact accent |
| Editorial emerald action | `#059669` | Secondary actions and success treatment |
| Breaking-news red | `#DC2626` | Genuine urgent or breaking-news treatment only |
| Warm paper | `#F7F4EE` | Editorial background and light artwork |
| Warm panel | `#FBFAF7` | Panels and secondary surfaces |
| Warm border | `#E6E1D8` | Editorial dividers and borders |
| Main headline | `#020617` | Headlines on light backgrounds |
| Body text | `#1E293B` | Primary body copy |
| Secondary text | `#475569` | Supporting copy and metadata |

All raster exports should use the sRGB colour space. Do not substitute generic platform blues, introduce category-specific palettes or use breaking-news red for routine content.

### Typography

- Headlines: **Playfair Display**, normally weight `700`.
- Body, labels, interfaces and calls to action: **Public Sans**, weights `400`, `500`, `600` or `700` as required.
- Email HTML may retain email-safe font fallbacks; raster social graphics should use the approved brand fonts.

Font files are not stored in this library unless licensing and redistribution have been reviewed separately.

## Asset categories

- `logos/` — approved logo and wordmark masters and exports.
- `colours/` — palette definitions and future swatch resources.
- `typography/` — typographic rules and specimen guidance.
- `social/` — platform-specific social masters and exports.
- `media-kit/` — approved partner, audience and commercial media-kit assets.
- `brand-guidelines/` — consolidated brand-guideline documents and their source assets.

The Instagram Highlight suite in `social/highlights/` is the first completed production set and is designated **Version 1.0**.

## Naming conventions

- Use lowercase kebab-case filenames.
- Use a stable descriptive base name, for example `news`, `daily-brief` or `sponsor-overview`.
- Keep the same base name for a vector master and its raster export: `asset.svg` and `asset.png`.
- Add a platform or format qualifier only when the artwork differs: `daily-brief-story.svg` or `daily-brief-feed.svg`.
- Do not add dates, spaces, `final`, `new` or editor names to production filenames.
- Use an explicit version suffix only when a published production asset is superseded, for example `news-v2.svg`. Do not overwrite an approved earlier version.

## SVG-first workflow

1. Create or update the SVG master using exact approved colours, dimensions and safe areas.
2. Keep shapes, paths and geometry editable. Avoid embedded raster artwork unless the asset requires photography.
3. Do not embed unlicensed fonts, external file references, scripts or tracking data.
4. Validate the SVG as XML and inspect it at full size and intended display size.
5. Export the production PNG directly from the approved SVG master.
6. Verify dimensions, colour space, safe-area compliance and filename parity.
7. Retain both master and export together in the appropriate directory.

## PNG export standards

- Instagram Highlight covers: `1080 × 1080 px`.
- Instagram feed and Threads portrait graphics: `1080 × 1350 px`.
- Instagram Stories and Reels working graphics: `1080 × 1920 px`.
- Facebook and landscape campaign graphics: `1200 × 630 px`.
- Export as sRGB PNG with transparency only when the design requires it.
- Preserve exact dimensions; do not upscale a smaller raster export.
- Optimise file size without changing dimensions, artwork or visible colour values.

Logo exports may use additional dimensions documented in `logos/README.md`.

## Versioning and approval

- Once an asset is used publicly, treat its SVG master and matching export as immutable.
- Corrections or redesigns require a new explicit version rather than silent replacement.
- Record the asset version, approval state and intended channels in the nearest directory README.
- Working drafts should remain outside production asset directories until reviewed.
- Only approved assets should be described as production-ready.

## Repository location

The canonical library location is:

```text
docs/brand-assets/
```

Website runtime assets remain in their existing production locations unless a separate implementation explicitly moves or integrates them. This library must not be referenced by the website merely because an asset has been added here.

## Planned assets

- Complete logo and wordmark suite.
- Social Story templates.
- Instagram feed and carousel templates.
- Reels cover templates.
- Facebook and Threads templates.
- Newsletter promotion templates.
- Brand Guidelines PDF and source document.
- Commercial Media Kit and source document.
- Sponsor and partnership presentation assets.
