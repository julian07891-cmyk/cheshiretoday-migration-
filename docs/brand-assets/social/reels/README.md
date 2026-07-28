# Instagram Reels Cover Template System

Version 1.0 provides production-ready SVG cover masters for Cheshire Today Instagram Reels. PNG exports are intentionally not included.

The authenticated Admin Social Publishing dialog can compose the approved Local
News Reels Cover from a stored active Local News article and download an exact
`1080 × 1920 px` PNG. It also provides deterministic Reel caption, hashtag and
post copy without treating the article image as video footage. Other masters
retain the documented manual SVG-first workflow.

## Template inventory

- `breaking-news-reel.svg` — urgent, genuinely breaking coverage.
- `local-news-reel.svg` — Cheshire and town-level reporting.
- `business-reel.svg` — business, investment and economic coverage.
- `property-reel.svg` — property, housing and built-environment coverage.
- `ai-tech-reel.svg` — AI and technology coverage.
- `newsletter-reel.svg` — Daily Brief and newsletter promotion.

## Canvas and safe area

- Canvas: `1080 × 1920 px` (`9:16`).
- Horizontal safe margin: `72 px` on both sides.
- Top safe margin: `250 px`.
- Bottom safe margin: `300 px`.
- Critical content area: `x=72–1008`, `y=250–1620`.

Every master contains a hidden `editor-guides` group with the common safe-area rectangle, centre line and spacing guides. Show it while editing and keep it hidden for export. Keep the logo, category, headline, Reel badge and CTA inside the critical content area so the cover remains legible in full-screen and cropped profile-grid views.

## Placeholder contract

Every master contains reusable groups identified with `data-placeholder`:

- `logo`
- `image`
- `category`
- `headline`
- `reel-badge`
- `cta`

Replace all bracketed labels and the image frame before export. Use approved editorial photography with a clear focal point. Do not embed remote images, tracking URLs, raster data or unlicensed artwork in a permanent master.

## Typography and colours

- Headlines: Playfair Display `700`, normally `80–90 px`.
- Category labels, Reel badges, CTAs and supporting labels: Public Sans `600–700`.
- Royal blue `#1E3A8A` is the principal identity colour.
- Editorial emerald `#047857` / `#059669` is an accent.
- Breaking red `#DC2626` is reserved for genuinely urgent coverage.
- Warm paper `#F7F4EE`, warm panel `#FBFAF7`, warm border `#E6E1D8`, headline `#020617` and supporting text `#1E293B` / `#475569` complete the approved palette.

Masters contain no gradients, filters, shadows, raster images or AI artwork.

## Editing and export workflow

1. Duplicate the appropriate SVG master; never overwrite Version 1.0.
2. Name working files in lowercase kebab-case.
3. Replace the logo, image, category, headline, Reel badge and CTA placeholders.
4. Keep essential content inside the shared safe area and verify the central profile-grid crop.
5. Show the editor guides during alignment checks, then hide them.
6. Validate XML, accessibility references, typography and exact colours.
7. Inspect at full-screen and phone-grid size.
8. Export an sRGB PNG at exactly `1080 × 1920 px`.
9. Confirm no placeholders or guides remain visible.

No PNG export belongs in `templates/`. Campaign-specific SVG and PNG files should use the same base name and live in a future approved campaign location.

## Naming conventions

- Permanent masters retain the stable filenames in `templates/`.
- Production working assets use lowercase kebab-case, for example `chester-station-upgrade-reel.svg`.
- Do not use spaces, dates, editor names, `final` or `new`.
- Future redesigns must use an explicit versioned filename or directory rather than silently replacing Version 1.0.
