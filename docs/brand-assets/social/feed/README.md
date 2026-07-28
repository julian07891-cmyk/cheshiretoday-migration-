# Instagram Feed Template System

Version 1.0 provides production-ready square SVG master templates for Cheshire Today Instagram feed graphics. PNG exports are intentionally not included in this stage.

The authenticated Admin Social Publishing dialog can compose the approved Local
News layout from a stored active Local News article and download an exact
`1080 × 1080 px` PNG. It also provides deterministic Feed caption, hashtag and
post copy. The remaining masters retain the documented manual SVG-first workflow.

## Template inventory

- `breaking-news-square.svg` — genuinely urgent breaking-news coverage.
- `local-news-square.svg` — general Cheshire and town-level reporting.
- `business-square.svg` — business, investment and economic coverage.
- `property-square.svg` — property, housing and built-environment coverage.
- `ai-tech-square.svg` — AI and technology coverage.
- `quote-square.svg` — attributed quotation or concise editorial statement.
- `poll-square.svg` — audience question with two response placeholders.
- `newsletter-square.svg` — Daily Brief and newsletter acquisition promotion.

## Canvas and safe area

- Canvas: `1080 × 1080 px` (`1:1`).
- Safe margin: `72 px` on every side.
- Critical content area: `x=72–1008`, `y=72–1008`.
- Base spacing unit: `24 px`; primary layout gaps should normally use `24`, `48` or `72 px`.

Each template contains a hidden `editor-guides` group with the safe-area rectangle, four-column alignment grid and template-specific horizontal spacing guides. Editors may show this layer during composition; it must remain hidden for export.

## Placeholder contract

Every master contains reusable groups identified with `data-placeholder`:

- `logo`
- `image`
- `category`
- `headline`
- `cta`

The poll template also contains `poll-options`. Placeholder labels such as `[HEADLINE]` are editing aids and must be replaced before export. Image placeholders should be replaced with approved editorial photography while preserving a meaningful focal point inside the safe area.

## Typography

- Headline: Playfair Display `700`, normally `62–74 px` in square artwork.
- Category label: Public Sans `700`, approximately `19 px`, uppercase with restrained tracking.
- CTA: Public Sans `700`, approximately `22–26 px`.
- Placeholder and supporting labels: Public Sans `600`.

Keep headlines concise, use natural title case and avoid more than three lines. Playfair Display is reserved for editorial headline or quotation treatment; all functional copy remains Public Sans.

## Colour and presentation rules

Use only the approved production palette documented in the Brand Asset Library. Royal blue remains the principal identity colour. Emerald is an editorial accent. Breaking red is reserved for genuinely urgent coverage.

Templates contain no photographs, raster images, gradients, filters, shadows or AI artwork. Warm paper and warm panels provide the normal editorial surfaces; warm borders separate placeholder regions without application-style decoration.

## SVG editing and export workflow

1. Duplicate the appropriate SVG master; do not overwrite the Version 1.0 template.
2. Use a lowercase kebab-case working filename.
3. Replace every logo, image, category, headline and CTA placeholder.
4. Keep essential content within the `72 px` safe frame.
5. Show the guide layer during alignment checks, then hide it.
6. Validate XML, typography and exact colour values.
7. Inspect the graphic at full size and expected phone-grid size.
8. Export an sRGB PNG at exactly `1080 × 1080 px`.
9. Confirm no placeholder copy or guides remain visible in the export.

PNG exports should be created only from an approved SVG working master. Do not upscale a smaller raster file or add campaign exports to `templates/`.

## Naming conventions

- Permanent masters retain their stable names in `templates/`.
- Story-specific graphics use lowercase kebab-case, for example `chester-business-investment-square.svg`.
- SVG masters and PNG exports share the same base name.
- Do not use spaces, dates, editor names, `final` or `new` in production filenames.
- A future redesign must use an explicit versioned filename or directory rather than silently replacing Version 1.0.

## Social publishing recommendations

- Upload the final `1080 × 1080 px` sRGB PNG at the highest available quality.
- Review the image at grid-thumbnail and full-feed sizes before publishing.
- Put the full article context and link direction in the caption; keep the graphic concise.
- Add platform alt text describing the finished artwork and editorial image.
- Use the poll template to invite discussion, not to simulate Instagram’s interactive Story poll control.
- Do not use breaking treatment for routine crime, minor incidents or general promotion.
- Use one orientation throughout a carousel and retain the same grid, margins and typography across every slide.
