#!/usr/bin/env python3
"""Build the clean Hostinger production tree for https://allesclinx.com/knowledge/."""
from __future__ import annotations
import hashlib
import html
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urljoin
from xml.sax.saxutils import escape as xml_escape

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "_hostinger"
DOCS = ROOT / "docs"
BASE_URL = "https://allesclinx.com/knowledge/"
BASE_PATH = "/knowledge/"
PREVIEW_IMAGE = "https://allesclinx.com/wp-content/uploads/2026/09/alles-clinx-knowledge-hub-500-resources.png"
SOCIAL_DIR = "assets/social"
SOCIAL_WIDTH = 1200
SOCIAL_HEIGHT = 630

LIVE = json.loads((ROOT / "production" / "live.json").read_text(encoding="utf-8"))
CANON = json.loads((ROOT / "taxonomy" / "canonical-structure.json").read_text(encoding="utf-8"))
LIVE_IDS = set(LIVE.get("live_article_ids", []))
BY_ID = {a["article_id"]: a for a in CANON["articles"]}

if OUT.exists():
    shutil.rmtree(OUT)
shutil.copytree(DOCS, OUT)

# Remove repository-only design/import documentation and generic preview templates.
for name in (
    "article.html", "category.html", "subcategory.html", "subcat.html",
    "content-standard.md", "design-policy.md", "search.md",
    "translation-standard.md", "wordpress-import-contract.md"
):
    target = OUT / name
    if target.exists():
        target.unlink()

live_articles = [BY_ID[i] for i in LIVE.get("live_article_ids", []) if i in BY_ID]
live_categories = {a["category_slug"] for a in live_articles}
live_subcategories = {(a["category_slug"], a["subcategory_slug"]) for a in live_articles}

# Remove category/subcategory discovery trees that do not yet contain live content.
all_categories = {a["category_slug"] for a in CANON["articles"]}
for category_slug in all_categories - live_categories:
    target = OUT / "library" / category_slug
    if target.exists():
        shutil.rmtree(target)

for category_slug in live_categories:
    all_subcats = {
        a["subcategory_slug"] for a in CANON["articles"]
        if a["category_slug"] == category_slug
    }
    live_subcats = {s for c, s in live_subcategories if c == category_slug}
    for subcat_slug in all_subcats - live_subcats:
        target = OUT / "library" / category_slug / subcat_slug
        if target.exists():
            shutil.rmtree(target)

# Never publish canonical article directories that have not passed the live gate.
for article in CANON["articles"]:
    if article["article_id"] in LIVE_IDS:
        continue
    path = OUT / "library" / article["category_slug"] / article["subcategory_slug"] / article["slug"]
    if path.exists():
        shutil.rmtree(path)

# Convert the GitHub Pages project prefix to the public Hostinger mount point.
TEXT_EXTS = {".html", ".js", ".css", ".json", ".xml", ".txt", ".md"}
for path in OUT.rglob("*"):
    if not path.is_file() or path.suffix.lower() not in TEXT_EXTS:
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    text = text.replace("/knowledge-library/", "/knowledge/")
    text = text.replace("https://alles-clinx.github.io/knowledge-library/", BASE_URL)
    path.write_text(text, encoding="utf-8")

# Give shared shell assets content-based URLs. Existing Knowledge service workers
# can otherwise keep serving an old precached CSS/JS file after deployment.
asset_versions = {
    name: hashlib.sha256((OUT / "assets" / name).read_bytes()).hexdigest()[:12]
    for name in ("site.css", "site.js", "discovery.css", "legal.css", "sitemap.js")
}
LEGAL_CANONICALS = {
    "privacy-policy/index.html": "https://allesclinx.com/privacy-policy/",
    "terms-conditions/index.html": "https://allesclinx.com/terms-conditions/",
    "cookie-policy/index.html": "https://allesclinx.com/cookie-policy/",
    "ai-data-use/index.html": "https://allesclinx.com/ai-data-use/",
    "accessibility/index.html": "https://allesclinx.com/accessibility/",
    "trust-security/index.html": "https://allesclinx.com/trust-security/",
}
STATIC_SITEMAP_PATHS = (
    "about/",
    "about/knowledge/",
    "about/tools/",
    "about/nova/",
    "about/metricon/",
    "about/checkmate/",
    "sitemap/",
)
category_names = {}
subcategory_names = {}
for item in live_articles:
    category_names[item["category_slug"]] = item["category"]
    subcategory_names[(item["category_slug"], item["subcategory_slug"])] = item["subcategory"]

def page_title_description(page: str) -> tuple[str, str]:
    title_match = re.search(r"<title>([\s\S]*?)</title>", page, flags=re.I)
    title = strip_tags(html.unescape(title_match.group(1))) if title_match else "Alle's ClinX Knowledge"
    desc_match = re.search(
        r"<meta[^>]+name=['\"]description['\"][^>]+content=['\"]([^'\"]*)['\"]",
        page,
        flags=re.I,
    )
    if not desc_match:
        desc_match = re.search(
            r"<meta[^>]+content=['\"]([^'\"]*)['\"][^>]+name=['\"]description['\"]",
            page,
            flags=re.I,
        )
    desc = html.unescape(desc_match.group(1)).strip() if desc_match else ""
    return title, desc

def discovery_schema(rel: str, canonical_url: str, page: str) -> list[dict]:
    title, desc = page_title_description(page)
    site = {"@type": "WebSite", "name": "Alle's ClinX Knowledge", "url": BASE_URL}
    if rel == "index.html":
        return [
            {"@context": "https://schema.org", **site},
            {
                "@context": "https://schema.org",
                "@type": "CollectionPage",
                "name": title,
                "description": desc,
                "url": canonical_url,
                "isPartOf": site,
            },
        ]

    parts = rel.split("/")
    if not (parts and parts[0] == "library" and parts[-1] == "index.html"):
        return []

    if len(parts) == 3:
        category_slug = parts[1]
        category = category_names.get(category_slug, title)
        crumbs = [
            {"@type": "ListItem", "position": 1, "name": "Knowledge", "item": BASE_URL},
            {"@type": "ListItem", "position": 2, "name": category, "item": canonical_url},
        ]
    elif len(parts) == 4:
        category_slug, subcategory_slug = parts[1], parts[2]
        category = category_names.get(category_slug, category_slug)
        subcategory = subcategory_names.get((category_slug, subcategory_slug), title)
        crumbs = [
            {"@type": "ListItem", "position": 1, "name": "Knowledge", "item": BASE_URL},
            {
                "@type": "ListItem",
                "position": 2,
                "name": category,
                "item": BASE_URL + f"library/{category_slug}/",
            },
            {"@type": "ListItem", "position": 3, "name": subcategory, "item": canonical_url},
        ]
    else:
        return []

    return [
        {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": title,
            "description": desc,
            "url": canonical_url,
            "isPartOf": site,
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": crumbs,
        },
    ]

def generic_meta(rel: str, canonical_url: str, page: str) -> str:
    if rel == "offline.html":
        return '<meta name="robots" content="noindex,follow">'

    canonical = LEGAL_CANONICALS.get(rel, canonical_url)
    title, desc = page_title_description(page)
    tags = [
        '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">',
        f'<link rel="canonical" href="{canonical}">',
        f'<meta property="og:url" content="{canonical}">',
        f'<meta property="og:image" content="{PREVIEW_IMAGE}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:image" content="{PREVIEW_IMAGE}">',
    ]
    if title:
        esc_title = html.escape(title, quote=True)
        tags += [
            f'<meta property="og:title" content="{esc_title}">',
            f'<meta name="twitter:title" content="{esc_title}">',
        ]
    if desc:
        esc_desc = html.escape(desc, quote=True)
        tags += [
            f'<meta property="og:description" content="{esc_desc}">',
            f'<meta name="twitter:description" content="{esc_desc}">',
        ]

    for schema in discovery_schema(rel, canonical, page):
        tags.append(
            '<script type="application/ld+json">'
            + json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
            + '</script>'
        )
    return "\n".join(tags)

for page_path in OUT.rglob("*.html"):
    page = page_path.read_text(encoding="utf-8")
    page = remove_existing(page, r"<meta\s+name=['\"]robots['\"][^>]*>")
    page = remove_existing(page, r"<link\s+rel=['\"]canonical['\"][^>]*>")
    page = remove_existing(page, r"<link\s+rel=['\"]alternate['\"][^>]*hreflang=[^>]*>")
    page = remove_existing(page, r"<meta\s+property=['\"]og:(?:type|site_name|title|description|url|image|image:type|image:width|image:height|image:alt)['\"][^>]*>")
    page = remove_existing(page, r"<meta\s+name=['\"]twitter:(?:card|title|description|image|image:alt)['\"][^>]*>")

    rel = page_path.relative_to(OUT).as_posix()
    canonical_path = public_path_for_file(page_path)
    canonical_url = "https://allesclinx.com" + canonical_path

    rec = by_url.get(canonical_path)
    if rec:
        additions = meta_for_article(rec, canonical_url, canonical_path)
    else:
        additions = generic_meta(rel, canonical_url, page)
    page = inject_head(page, additions)
    page_path.write_text(page, encoding="utf-8")

# Sitemap: homepage + selected static pages + live category/subcategory discovery pages + both article locales.
urls = {BASE_URL}
for static_path in STATIC_SITEMAP_PATHS:
    urls.add(BASE_URL + static_path)
live_meta = [BY_ID[i] for i in LIVE.get("live_article_ids", []) if i in BY_ID]
for a in live_meta:
    urls.add(BASE_URL + f'library/{a["category_slug"]}/')
    urls.add(BASE_URL + f'library/{a["category_slug"]}/{a["subcategory_slug"]}/')
for rec in records:
    rel = rec.get("url", "").lstrip("/")
    if rel:
        urls.add(BASE_URL + rel)

sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for url in sorted(urls):
    sitemap.append(f'  <url><loc>{xml_escape(url)}</loc></url>')
sitemap.append('</urlset>')
(OUT / "sitemap.xml").write_text("\n".join(sitemap) + "\n", encoding="utf-8")

categories = {}
for a in live_meta:
    categories.setdefault(a["category"], set()).add(a["category_slug"])
llms = [
    "# Alle's ClinX Knowledge",
    "",
    "> Open professional cleaning, hygiene, chemistry, safety, equipment and facility-operations knowledge.",
    "",
    f"- Canonical site: {BASE_URL}",
    f"- Sitemap: {BASE_URL}sitemap.xml",
    "- Languages: English and हिन्दी (hi-IN)",
    "- Content license: CC BY 4.0",
    "- Publisher: Alle's ClinX",
    "",
    "## Live categories",
]
for name in sorted(categories):
    slug = sorted(categories[name])[0]
    llms.append(f"- {name}: {BASE_URL}library/{slug}/")
llms += [
    "",
    "## Crawling and citation",
    "Public Knowledge pages are intended to be indexable and citable. Canonical URLs, hreflang links, structured data and sitemap entries are included in the published HTML.",
]
(OUT / "llms.txt").write_text("\n".join(llms) + "\n", encoding="utf-8")

# Subdirectory crawler hints. The authoritative robots.txt remains at the domain root.
(OUT / "robots.txt").write_text(
    "User-agent: *\n"
    "Allow: /knowledge/\n"
    "Disallow: /knowledge/offline.html\n"
    f"Sitemap: {BASE_URL}sitemap.xml\n",
    encoding="utf-8"
)

# Hostinger/Apache hardening for the /knowledge/ directory.
(OUT / ".htaccess").write_text(
    "Options -Indexes\n"
    "DirectoryIndex index.html\n"
    "AddType application/manifest+json .webmanifest\n"
    "<IfModule mod_headers.c>\n"
    "  Header set X-Content-Type-Options \"nosniff\"\n"
    "  Header set Referrer-Policy \"strict-origin-when-cross-origin\"\n"
    "  <Files \"offline.html\">\n"
    "    Header set X-Robots-Tag \"noindex, follow\"\n"
    "  </Files>\n"
    "</IfModule>\n",
    encoding="utf-8"
)

print(f"Built Hostinger production tree at {OUT}")
print(f"Live articles: {len(LIVE_IDS)}; sitemap URLs: {len(urls)}; search records: {len(records)}")
