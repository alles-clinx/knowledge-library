# Design Policy

## Discovery pages
Knowledge, Category and Subcategory pages use the locked crystal-minimal system:
- monochrome
- text first
- generous whitespace
- hairline dividers
- one obvious search/navigation action
- no decorative arrows
- no redundant icons, badges or chips
- no gradients or heavy shadows
- same category-page system across all 13 categories

## Article pages
Use the approved Gold Standard article UI without redesigning per article.
The language switch and Open Knowledge attribution are additions to the shell, not replacements for it.

## Shared header

- Show the Alle's ClinX brand and three SVG-only controls: open-book Library, larger Search and Install.
- Do not render a Menu control or slide-out navigation on desktop or mobile.
- Keep category discovery, related guides and footer links available without a drawer.
- Keep the header fixed flush at the viewport top; hide it on deliberate downward scrolling and reveal it on upward scrolling.
- Keep it visible near the top and when its controls receive keyboard focus.
- Use a flat white header with only a hairline bottom border; no shadow, blur, rounded header corners, visible labels or Menu drawer.

## Page architecture
- Focus on Knowledge home, categories and topics, bilingual articles, and essential Privacy and Terms documents.
- Do not publish redundant About pages, a human sitemap, or duplicate policy/trust pages.
- Keep the machine-readable XML sitemap, sourced article content, and licensing information intact.
- Redirect retired URLs on the Hostinger production host.

## Eleven podcast shelf
- One homepage editorial shelf only: after Quick reads and before Browse by category.
- Show the three most recent published episodes, optional cover artwork, duration and date.
- Each card opens its official listening destination; include one Apple Podcasts show link and one small footer link.
- Do not add a podcast About page, header icon, autoplay or an embedded heavyweight player.
- Keep accessible static fallback cards and refresh from public podcast metadata daily.

## Quiet hierarchy, no ghost branding
- Remove oversized decorative "ghost" Alle's ClinX wordmarks from homepage and policy pages; let the footer itself close each page.
- Eliminate repeated section-heading, category, topic and article-row dividers. Use whitespace, typography and gentle hover backgrounds.
- Retain only barely visible separation for functional controls and table readability; focus indicators must remain accessible.
- Keep the shared footer #f9f9f9, with no dark theme or emphatic internal border.

## Eleven in-page audio playback
- Episodes render as articles with independent in-page play/pause buttons, a seek control and time readout for the active episode.
- Play actual verified HTTPS MP3 enclosure URLs from RSS.com, never pretend a link to Apple is native playback.
- Allow only one episode to play at a time; Apple Podcasts is optional secondary navigation.
- The daily metadata updater refreshes the publisher-enclosure URL along with titles, artwork and duration.

## Stationary podcast playback controls
- Keep Play and Pause as the exact same button in a fixed position within each episode card.
- Reserve the progress row's height in idle, playing and paused states; hiding the row must never resize the card or shift adjacent episode controls.
- Reserve the Play/Pause text label's width and wrap the optional Apple link predictably on small screens.
- Check geometry at desktop and 320–430px mobile widths whenever changing the podcast shelf.

## Hover consistency
- Interactive article, category and topic rows use a very subtle neutral background and about 4px of optical left inset.
- Favor content-only transforms or balanced inline padding; never move whole cards or alter their hitboxes on hover.
- Search results, footer links, article navigation and legal accordion summaries follow the same restrained language.
- The fixed header icons, audio play/pause controls, seek bar and data tables do not shift position.
- Preserve focus-visible accessibility and disable transitions for reduced-motion preferences.

## Eleven transport refinements
- Present refined thin-stroke Play/Pause SVG glyphs and a short verb together in one fixed-size monochrome, gently rounded transport button.
- Distinguish Play, Loading, Pause, Resume and unavailable audio states without changing the button's width, height or position.
- Use a quiet 4px progress track, a clear thumb, and accessible elapsed/total playback timestamps.
- Loading feedback is restrained and must respect reduced-motion settings. Maintain the browser-native audio API and single active stream.

### Quiet transport palette
- The audio control must not read as a primary CTA: use a translucent near-white visual capsule with 1px #e5e5e7 border, 8px radius, 18px outlined transport icon, and neutral dark ink.
- Playing, paused, and loading states stay within the same soft monochrome family; only the icon and short verb indicate transport state.
- Preserve the fixed 100 × 44 px hit target, keyboard focus ring, contrast, and no-shift playback layout.

## Site icon and install icons
- Use the open-book icon from the Knowledge Library header consistently across browser favicons, bookmarks, iOS touch icons, and installed app icons. Never use the CX monogram for the Knowledge Library.
- Declare the favicon and native 180px PNG touch icon in homepage HTML before JavaScript runs.
- Provide 192px PNG plus scalable SVG for PWA installs, with PNG favicon fallback.
- The shared shell adds missing favicon metadata for other Knowledge routes without removing static links or creating duplicates.
- Cache-bust icon changes and precache the new assets in service workers.

### Eleven player geometry and restraint
- Keep the button hit target at 100 × 44px, with an inset 96 × 36px visual capsule; never animate transforms, font sizes, or padding on Play/Pause/Resume.
- Reserve an internal 48px label slot to avoid optical wobble between states; keep the SVG at a fixed 18px with 1.85px line weight.
- Hover and playing states use only a small neutral tone shift, never saturated colors, large shadows, or black backgrounds.
- On touch devices, keep the full 44px target and keyboard focus ring, with no hover-dependent controls.

## Typography weight discipline
- Knowledge uses calm typography: body text 400, metadata 450–500, content titles 520–540, section headings 550, and display headings 520.
- Never set Knowledge headings or controls heavier than 560; create hierarchy through font size, spacing, line-height, and contrast rather than boldness.
- Article emphasis stays at 540, below the 550 section headings. Apply this consistently across home, discovery, reading views, search, navigation, and legal pages.
- Older published articles embed heavy font weights; central site.css typography overrides correct these without rebuilding hundreds of pages. Retain that rule when publishing future articles.
- This design policy is specific to Knowledge and should not alter other Alle's ClinX web properties.
