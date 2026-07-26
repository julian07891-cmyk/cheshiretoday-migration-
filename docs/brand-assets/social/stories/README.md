# Instagram Story Template System

Version 1.0 provides production-ready SVG master templates for Cheshire Today Instagram Stories. PNG exports are intentionally not included in this stage.

## Canvas and safe area

- Canvas: `1080 × 1920 px` (`9:16`).
- Horizontal safe margin: `72 px` on both sides.
- Top safe margin: `250 px`.
- Bottom safe margin: `300 px`.
- Critical content area: `x=72–1008`, `y=250–1620`.

Every master contains a hidden `editor-guides` group with the common safe-area rectangle, centre alignment and template-specific spacing guides. Editors may temporarily show this group while composing artwork; it must remain hidden for export.

## Templates

- `breaking-news.svg` — urgent, genuinely breaking coverage using the approved breaking red.
- `top-story.svg` — principal editorial story treatment.
- `business.svg` — business, investment and economic coverage.
- `property.svg` — property, housing and built-environment coverage.
- `ai-tech.svg` — AI and technology coverage.
- `newsletter.svg` — Daily Brief and newsletter acquisition promotion.
- `poll.svg` — audience question with two response placeholders.
- `read-more.svg` — image-led article promotion and link-sticker support.

## Placeholder contract

Every template contains reusable groups identified with `data-placeholder`:

- `logo`
- `image`
- `category`
- `headline`
- `cta`

The poll template also contains `poll-options`. Placeholder text such as `[HEADLINE]` is an editing aid and must be replaced before export. Replace the image placeholder with approved editorial photography; do not embed remote images, tracking URLs or unlicensed artwork in the SVG master.

## Text hierarchy

- Headline: Playfair Display, normally weight `700`, approximately `76–94 px` depending on the template and headline length.
- Category label: Public Sans `700`, approximately `21–22 px`, uppercase with restrained letter spacing.
- CTA: Public Sans `700`, approximately `28–30 px`.
- Supporting placeholder labels: Public Sans `600`.

Use no more than three short headline lines. Preserve natural title case and do not set article headlines in full capitals.

## Colour contract

Templates use only the approved production palette:

- royal blue `#1E3A8A`
- editorial emerald `#047857` / `#059669`
- breaking red `#DC2626`
- warm paper `#F7F4EE`
- warm panel `#FBFAF7`
- warm border `#E6E1D8`
- main headline `#020617`
- body and supporting text `#1E293B` / `#475569`

Breaking red is reserved for genuinely urgent coverage. Emerald is an editorial accent; royal blue remains the principal Cheshire Today identity colour. Templates contain no gradients, shadows, filters, raster images or AI artwork.

## SVG editing and export workflow

1. Duplicate the appropriate SVG master; never overwrite the Version 1.0 template.
2. Use a lowercase kebab-case working name describing the story or campaign.
3. Replace the logo, image, category, headline and CTA placeholders.
4. Keep all essential content inside the common safe area.
5. Show the editor guide layer during layout checks, then hide it before export.
6. Confirm the approved fonts and exact palette values.
7. Validate the SVG as XML and inspect it at full size and phone-display size.
8. Export an sRGB PNG at exactly `1080 × 1920 px` without resizing.
9. Verify that no placeholder text or guide layer is visible in the PNG.

Production exports should live alongside the story-specific working master or in a future approved campaign subdirectory. Do not place generated campaign artwork in `templates/`.

## Naming convention

- Permanent masters retain the stable names in `templates/`.
- Story-specific working assets use lowercase kebab-case, for example `chester-station-upgrade-story.svg`.
- Use the same base name for the SVG and PNG export.
- Do not use spaces, dates, editor names, `final` or `new` in production filenames.
- A future template redesign must use an explicit versioned filename or versioned directory rather than silently replacing Version 1.0.

## Instagram upload recommendations

- Upload the final `1080 × 1920 px` sRGB PNG at the highest available quality.
- Review the Story on a phone before publication.
- Place Instagram link, poll or other interactive stickers within the safe area without covering the logo or headline.
- Keep link stickers above the bottom interface area.
- Add accessibility text and a clear supporting caption where the publishing workflow permits.
- Do not use breaking treatment for routine crime, minor incidents or general promotion.
