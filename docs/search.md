# Search

The public Knowledge UI exposes one minimal search field.

`search/index.json` is a generated lightweight index. Search records contain:
- article_id
- locale
- title
- category/subcategory
- excerpt
- URL

The UI filters results to the currently selected language. Category pages may restrict the same index by `category_slug`.
Avoid adding complex filters unless evidence shows they are necessary.
