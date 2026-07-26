# Facebook Template System

Version 1.0 provides production-ready landscape SVG masters for Cheshire Today Facebook editorial, audience and newsletter graphics. PNG exports are intentionally not included.

## Template inventory

- `breaking-news-facebook.svg` — genuinely urgent breaking-news coverage.
- `local-news-facebook.svg` — Cheshire and town-level reporting.
- `business-facebook.svg` — business, investment and economic coverage.
- `property-facebook.svg` — property, housing and built-environment coverage.
- `ai-tech-facebook.svg` — AI and technology coverage.
- `quote-facebook.svg` — attributed quotation or concise editorial statement.
- `poll-facebook.svg` — audience question with two response placeholders.
- `newsletter-facebook.svg` — Daily Brief and newsletter acquisition promotion.
- `event-facebook.svg` — editorially relevant event promotion with date and location fields.

## Canvas and safe area

- Canvas: `1200 × 630 px`.
- Safe margin: `72 px` on every side.
- Critical content area: `x=72–1128`, `y=72–558`.

Every master contains a hidden `editor-guides` group with the common safe-area rectangle, centre line and template-specific alignment guides. Editors may show this layer while composing artwork; it must remain hidden for export.

## Placeholder contract

Every master contains reusable groups identified with `data-placeholder`:

- `logo`
- `image`
- `category`
- `headline`
- `cta`

The poll master also contains `poll-options`. The event master also contains `event-date` and `event-location`. Replace every bracketed label and image frame before export. Use only approved editorial photography; permanent masters must not contain raster data or external resources.

## Typography

- Editorial headlines and quotations: Playfair Display `700`, normally `48–62 px`.
- Category labels, CTAs and supporting information: Public Sans `600–700`.
- Use natural title case for headlines and no more than three concise lines.
- Keep functional copy in Public Sans and reserve Playfair Display for editorial emphasis.

## Colour roles

Royal blue `#1E3A8A` remains the principal identity colour. Emerald `#047857` / `#059669` is an editorial accent. Breaking red `#DC2626` is reserved for genuinely urgent stories. Warm paper `#F7F4EE`, warm panel `#FBFAF7`, warm border `#E6E1D8`, headline `#020617` and supporting text `#1E293B` / `#475569` provide the approved editorial surfaces and hierarchy.

Facebook platform blue is not a Cheshire Today brand colour. Masters contain no gradients, filters, shadows, raster images or AI artwork.

## Editing and export workflow

1. Duplicate the appropriate SVG master; never overwrite Version 1.0.
2. Use a lowercase kebab-case working filename.
3. Replace every visible placeholder with approved content.
4. Keep essential text, logos and focal imagery inside the `72 px` safe frame.
5. Show editor guides during alignment checks, then hide them.
6. Validate XML, dimensions, IDs, accessibility references, typography and exact colours.
7. Inspect the graphic at full size, feed size and link-preview size.
8. Export an sRGB PNG at exactly `1200 × 630 px`.
9. Confirm that no placeholder text, guide layer, external reference or tracking data remains.

Do not add PNG exports or campaign artwork to `templates/`.

## Naming conventions

- Permanent masters retain the stable filenames in `templates/`.
- Production working assets use lowercase kebab-case, for example `chester-station-upgrade-facebook.svg`.
- SVG working files and PNG exports share the same base name.
- Do not use spaces, dates, editor names, `final` or `new`.
- Future redesigns require an explicit versioned filename or directory.

## Facebook publishing recommendations

- Use landscape masters for editorial posts, campaign graphics and controlled link-share artwork.
- Keep the graphic concise; place full reporting context and the article URL in the post copy.
- Check Facebook's generated link preview before publication and avoid duplicating a headline unnecessarily.
- Add useful alt text to the uploaded graphic.
- Use the poll graphic to invite discussion, not to imply a native Facebook poll control.
- Use event treatment only for events with clear editorial, civic, economic or public-interest relevance.
- Do not use breaking treatment for routine crime, minor incidents or general promotion.
