# WordPress Import Contract

WordPress imports are generated outputs, not source content.

Uploadable JSON uses:

```json
{"articles": [...]}
```

Required canonical identity fields:
- article_id
- title
- slug
- category
- category_slug
- subcategory
- subcategory_slug

Content/SEO fields:
- excerpt
- content_html
- seo_title
- meta_description
- related_article_ids
- status = draft

Never upload planning manifests containing `article_shells`.
The current importer updates records by `article_id`, so multilingual imports require the language-aware WordPress layer before Hindi records are sent to the importer.
