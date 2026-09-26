#!/usr/bin/env python3
"""Build the clean Hostinger production tree for https://allesclinx.com/knowledge/."""
from __future__ import annotations
import html
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urljoin
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "_hostinger"
DOCS = ROOT / "docs"
BASE_URL = "https://allesclinx.com/knowledge/"
BASE_PATH = "/knowledge/"
PREVIEW_IMAGE = "https://allesclinx.com/wp-content/uploads/2026/09/alles-clinx-knowledge-hub-500-resources.png"

LIVE = json.loads((ROOT / "production" / "live.json").read_text(encoding="utf-8"))
CANON = json.loads((ROOT / "taxonomy" / "canonical-structure.json").read_text(encoding="utf-8"))
LIVE_IDS = set(LIVE.get("live_article_ids", []))
BY_ID = {a["article_id"]: a for a in CANON["articles"]}

if OUT.exists():
    shutil.rmtree(OUT)
shutil.copytree(DOCS, OUT)

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

# Build live search lookup after prefix rewrite.
search_path = OUT / "assets" / "live-search.json"
search_data = json.loads(search_path.read_text(encoding="utf-8")) if search_path.exists() else {"records": []}
records = search_data.get("records", [])
by_url = {}
for rec in records:
    rel = rec.get("url", "").lstrip("/")
    public_path = BASE_PATH + rel
    by_url[public_path] = rec

def public_path_for_file(path: Path) -> str:
    rel = path.relative_to(OUT).as_posix()
    if rel == "index.html":
        return BASE_PATH
    if rel.endswith("/index.html"):
        return BASE_PATH + rel[:-10]
    return BASE_PATH + rel

def strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value or "").strip()

def inject_head(page: str, additions: str) -> str:
    if "</head>" not in page:
        return page
    return page.replace("</head>", additions + "\n</head>", 1)

def remove_existing(page: str, pattern: str) -> str:
    return re.sub(pattern, "", page, flags=re.I | re.S)

def meta_for_article(rec: dict, canonical_url: str, canonical_path: str) -> str:
    title = html.escape(rec.get("title", ""), quote=True)
    desc = html.escape(rec.get("excerpt", ""), quote=True)
    locale = rec.get("locale", "en")
    article_id = rec.get("article_id")
    meta = BY_ID.get(article_id, {})
    base = BASE_URL + f'library/{meta.get("category_slug","")}/{meta.get("subcategory_slug","")}/{meta.get("slug","")}/'
    en_url = base
    hi_url = base + "hi.html"
    lang = "hi-IN" if locale == "hi-IN" else "en"
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": rec.get("title", ""),
        "description": rec.get("excerpt", ""),
        "inLanguage": lang,
        "mainEntityOfPage": canonical_url,
        "image": PREVIEW_IMAGE,
        "publisher": {"@type": "Organization", "name": "Alle's ClinX", "url": "https://allesclinx.com/"},
        "isPartOf": {"@type": "WebSite", "name": "Alle's ClinX Knowledge", "url": BASE_URL},
        "license": "https://creativecommons.org/licenses/by/4.0/"
    }
    breadcrumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type":"ListItem","position":1,"name":"Knowledge","item":BASE_URL},
            {"@type":"ListItem","position":2,"name":rec.get("category",""),"item":BASE_URL + f'library/{meta.get("category_slug","")}/'},
            {"@type":"ListItem","position":3,"name":rec.get("subcategory",""),"item":BASE_URL + f'library/{meta.get("category_slug","")}/{meta.get("subcategory_slug","")}/'},
            {"@type":"ListItem","position":4,"name":rec.get("title",""),"item":canonical_url}
        ]
    }
    return "\n".join([
        '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">',
        f'<link rel="canonical" href="{canonical_url}">',
        f'<link rel="alternate" hreflang="en" href="{en_url}">',
        f'<link rel="alternate" hreflang="hi-IN" href="{hi_url}">',
        f'<link rel="alternate" hreflang="x-default" href="{en_url}">',
        '<meta property="og:type" content="article">',
        f'<meta property="og:title" content="{title}">',
        f'<meta property="og:description" content="{desc}">',
        f'<meta property="og:url" content="{canonical_url}">',
        f'<meta property="og:image" content="{PREVIEW_IMAGE}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{title}">',
        f'<meta name="twitter:description" content="{desc}">',
        f'<meta name="twitter:image" content="{PREVIEW_IMAGE}">',
        '<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False, separators=(",", ":")) + '</script>',
        '<script type="application/ld+json">' + json.dumps(breadcrumbs, ensure_ascii=False, separators=(",", ":")) + '</script>',
    ])

GENERIC_TEMPLATES = {"article.html", "category.html", "subcat.html"}
for page_path in OUT.rglob("*.html"):
    page = page_path.read_text(encoding="utf-8")
    page = remove_existing(page, r'<meta\s+name=["\']robots["\'][^>]*>')
    page = remove_existing(page, r'<link\s+rel=["\']canonical["\'][^>]*>')
    page = remove_existing(page, r'<link\s+rel=["\']alternate["\'][^>]*hreflang=[^>]*>')
    page = remove_existing(page, r'<meta\s+property=["\']og:(?:type|title|description|url|image)["\'][^>]*>')
    page = remove_existing(page, r'<meta\s+name=["\']twitter:(?:card|title|description|image)["\'][^>]*>')

    rel = page_path.relative_to(OUT).as_posix()
    canonical_path = public_path_for_file(page_path)
    canonical_url = "https://allesclinx.com" + canonical_path

    if rel in GENERIC_TEMPLATES:
        additions = '<meta name="robots" content="noindex,follow">'
    else:
        rec = by_url.get(canonical_path)
        if rec:
            additions = meta_for_article(rec, canonical_url, canonical_path)
        else:
            additions = "\n".join([
                '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">',
                f'<link rel="canonical" href="{canonical_url}">',
                f'<meta property="og:url" content="{canonical_url}">',
                f'<meta property="og:image" content="{PREVIEW_IMAGE}">',
                '<meta name="twitter:card" content="summary_large_image">',
                f'<meta name="twitter:image" content="{PREVIEW_IMAGE}">'
            ])
    page = inject_head(page, additions)
    page_path.write_text(page, encoding="utf-8")

# Sitemap: homepage + live category/subcategory discovery pages + both article locales.
urls = {BASE_URL}
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

# Hostinger/Apache hardening for the /knowledge/ directory.
(OUT / ".htaccess").write_text(
    "Options -Indexes\n"
    "DirectoryIndex index.html\n"
    "<IfModule mod_headers.c>\n"
    "  Header set X-Content-Type-Options \"nosniff\"\n"
    "  Header set Referrer-Policy \"strict-origin-when-cross-origin\"\n"
    "</IfModule>\n",
    encoding="utf-8"
)

print(f"Built Hostinger production tree at {OUT}")
print(f"Live articles: {len(LIVE_IDS)}; sitemap URLs: {len(urls)}; search records: {len(records)}")
