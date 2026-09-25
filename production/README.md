# Production System

This directory controls the 5-by-5 Knowledge production workflow.

## Hard rules

1. Work category-by-category.
2. Maximum 5 articles per batch; a category's final batch may contain fewer.
3. Do not start the next batch until the current batch passes editorial, translation, structural and responsive QA.
4. Do not mark an article live until its approved Gold Standard article preview exists.
5. Discovery pages use the locked crystal-minimal UI only.
6. Article pages use the locked Gold Standard UI only.
7. English is canonical. Hindi remains linked to the same canonical article identity and is reviewed before publication.
8. production/live.json is the live-preview gate. Planned article titles can appear in the hierarchy, but only IDs in that file are clickable.
9. GitHub is the canonical source; WordPress imports are generated outputs.

## Scale

- 13 categories
- 107 subcategories
- 317 articles
- 68 production batches
