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


## Global hero
Use one locked hero component across every Knowledge page type: Knowledge home, category, subcategory and article.

The visual contract is owned by `docs/assets/site.css` and must remain identical for:
- maximum hero width
- H1 size, weight, line-height and tracking
- supporting-copy width, size, line-height and spacing
- responsive title/copy scaling
- spacing to hero-level controls

Only contextual content may vary: title, supporting text, breadcrumb/context, article metadata, language controls, and search where the page genuinely requires it. Page-specific styles must not redefine the hero's visual geometry or typography.
