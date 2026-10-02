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
for page_path in OUT.rglob("*.html"):
    page = page_path.read_text(encoding="utf-8")
    for name, version in asset_versions.items():
        asset_url = f"{BASE_PATH}assets/{name}"
        for quote in ('"', "'"):
            page = page.replace(f"{asset_url}{quote}", f"{asset_url}?v={version}{quote}")
    page_path.write_text(page, encoding="utf-8")

# Build live search and SEO lookup directly from canonical live sources.
# This deliberately does NOT trust docs/assets/live-search.json: the renderer may
# update that file after a live promotion, which previously caused Hostinger to
# publish one deployment behind the live article set.
search_path = OUT / "assets" / "live-search.json"
records = []
missing_sources = []
for article_id in LIVE.get("live_article_ids", []):
    meta = BY_ID.get(article_id)
    if not meta:
        missing_sources.append(f"{article_id}: missing canonical metadata")
        continue
    source_dir = ROOT / "articles" / meta["category_slug"] / article_id
    for locale, filename in (("en", "en.json"), ("hi-IN", "hi.json")):
        source_path = source_dir / filename
        if not source_path.exists():
            missing_sources.append(f"{article_id}: missing {filename}")
            continue
        doc = json.loads(source_path.read_text(encoding="utf-8"))
        rel = f'library/{doc["category_slug"]}/{doc["subcategory_slug"]}/{doc["slug"]}/'
        if locale == "hi-IN":
            rel += "hi.html"
        records.append({
            "article_id": article_id,
            "locale": locale,
            "title": doc.get("title", ""),
            "category": doc.get("category", meta.get("category", "")),
            "category_slug": doc.get("category_slug", meta.get("category_slug", "")),
            "subcategory": doc.get("subcategory", meta.get("subcategory", "")),
            "subcategory_slug": doc.get("subcategory_slug", meta.get("subcategory_slug", "")),
            "excerpt": doc.get("excerpt", ""),
            "url": rel,
        })

if missing_sources:
    raise SystemExit("Hostinger build missing live sources:\n- " + "\n- ".join(missing_sources))

records.sort(key=lambda r: (r["article_id"], r["locale"]))
search_data = {
    "version": 2,
    "generated_for": "Hostinger bilingual live search",
    "record_count": len(records),
    "records": records,
}
search_path.parent.mkdir(parents=True, exist_ok=True)
search_path.write_text(
    json.dumps(search_data, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

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

def find_font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    for candidate in candidates:
        p = Path(candidate)
        if p.exists():
            return ImageFont.truetype(str(p), size=size)
    # Final fallback keeps the build from failing, though production runners install Noto.
    return ImageFont.load_default()

LATIN_REGULAR = [
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
LATIN_BOLD = [
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
DEVANAGARI_REGULAR = [
    "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansDevanagari-Regular.ttf",
]
DEVANAGARI_BOLD = [
    "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansDevanagari-Bold.ttf",
]

def font_set(locale: str, size: int, bold: bool = False):
    if locale == "hi-IN":
        candidates = DEVANAGARI_BOLD if bold else DEVANAGARI_REGULAR
        return find_font(candidates + (LATIN_BOLD if bold else LATIN_REGULAR), size)
    return find_font(LATIN_BOLD if bold else LATIN_REGULAR, size)

def text_width(draw: ImageDraw.ImageDraw, text: str, font) -> float:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]

def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines, line = [], words[0]
    for word in words[1:]:
        trial = line + " " + word
        if text_width(draw, trial, font) <= max_width:
            line = trial
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines

def social_filename(rec: dict) -> str:
    locale = "hi" if rec.get("locale") == "hi-IN" else "en"
    return f'{rec.get("article_id","article").lower()}-{locale}.png'

def social_image_url(rec: dict) -> str:
    return BASE_URL + SOCIAL_DIR + "/" + social_filename(rec)

def generate_social_card(rec: dict, target: Path) -> None:
    locale = rec.get("locale", "en")
    title = rec.get("title", "")
    category = rec.get("category", "")
    article_id = rec.get("article_id", "")
    image = Image.new("RGB", (SOCIAL_WIDTH, SOCIAL_HEIGHT), "white")
    draw = ImageDraw.Draw(image)

    # Crystal-minimal social card: no gradients, no decorative clutter.
    draw.line((72, 76, SOCIAL_WIDTH - 72, 76), fill=(20, 20, 20), width=2)
    draw.line((72, SOCIAL_HEIGHT - 82, SOCIAL_WIDTH - 72, SOCIAL_HEIGHT - 82), fill=(214, 214, 214), width=1)

    brand_font = font_set("en", 32, True)
    label_font = font_set(locale, 20, True)
    meta_font = font_set("en", 18, False)
    domain_font = font_set("en", 24, True)

    draw.text((72, 102), "Alle's ClinX", fill=(10, 10, 10), font=brand_font)
    draw.text((72, 151), category, fill=(92, 92, 92), font=label_font)
    draw.text((SOCIAL_WIDTH - 72, 109), article_id, fill=(120, 120, 120), font=meta_font, anchor="ra")

    max_title_width = SOCIAL_WIDTH - 144
    chosen_font = None
    lines = []
    for size in (68, 64, 60, 56, 52, 48, 44):
        f = font_set(locale, size, True)
        candidate = wrap_text(draw, title, f, max_title_width)
        if len(candidate) <= 4:
            chosen_font, lines = f, candidate
            break
    if chosen_font is None:
        chosen_font = font_set(locale, 42, True)
        lines = wrap_text(draw, title, chosen_font, max_title_width)[:4]

    y = 204
    line_height = int(getattr(chosen_font, "size", 48) * 1.18)
    for line in lines:
        draw.text((72, y), line, fill=(5, 5, 5), font=chosen_font)
        y += line_height

    draw.text((72, SOCIAL_HEIGHT - 59), "KNOWLEDGE", fill=(100, 100, 100), font=meta_font)
    draw.text((SOCIAL_WIDTH - 72, SOCIAL_HEIGHT - 59), "allesclinx.com/knowledge", fill=(15, 15, 15), font=domain_font, anchor="ra")

    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, format="PNG", optimize=True)

# Generate a unique 1200x630 rich-link card for every live language variant.
social_root = OUT / SOCIAL_DIR
if social_root.exists():
    shutil.rmtree(social_root)
for rec in records:
    generate_social_card(rec, social_root / social_filename(rec))

def inject_head(page: str, additions: str) -> str:
    if "</head>" not in page:
        return page
    return page.replace("</head>", additions + "\n</head>", 1)

def remove_existing(page: str, pattern: str) -> str:
    return re.sub(pattern, "", page, flags=re.I | re.S)

def meta_for_article(rec: dict, canonical_url: str, canonical_path: str) -> str:
    title = html.escape(rec.get("title", ""), quote=True)
    desc = html.escape(rec.get("excerpt", ""), quote=True)
    image_url = social_image_url(rec)
    image_alt = html.escape(f'{rec.get("title","")} — Alle\'s ClinX Knowledge', quote=True)
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
        "image": image_url,
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
        '<meta property="og:site_name" content="Alle\'s ClinX Knowledge">',
        f'<meta property="og:title" content="{title}">',
        f'<meta property="og:description" content="{desc}">',
        f'<meta property="og:url" content="{canonical_url}">',
        f'<meta property="og:image" content="{image_url}">',
        '<meta property="og:image:type" content="image/png">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{image_alt}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{title}">',
        f'<meta name="twitter:description" content="{desc}">',
        f'<meta name="twitter:image" content="{image_url}">',
        f'<meta name="twitter:image:alt" content="{image_alt}">',
        '<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False, separators=(",", ":")) + '</script>',
        '<script type="application/ld+json">' + json.dumps(breadcrumbs, ensure_ascii=False, separators=(",", ":")) + '</script>',
    ])

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

    desc = ""
    desc_patterns = (
        r'<meta[^>]+name="description"[^>]+content="([^"]*)"',
        r'<meta[^>]+content="([^"]*)"[^>]+name="description"',
        r"<meta[^>]+name='description'[^>]+content='([^']*)'",
        r"<meta[^>]+content='([^']*)'[^>]+name='description'",
    )
    for pattern in desc_patterns:
        match = re.search(pattern, page, flags=re.I)
        if match:
            desc = html.unescape(match.group(1)).strip()
            break
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
        tags.extend([
            f'<meta property="og:title" content="{esc_title}">',
            f'<meta name="twitter:title" content="{esc_title}">',
        ])
    if desc:
        esc_desc = html.escape(desc, quote=True)
        tags.extend([
            f'<meta property="og:description" content="{esc_desc}">',
            f'<meta name="twitter:description" content="{esc_desc}">',
        ])
    for schema in discovery_schema(rel, canonical, page):
        tags.append(
            '<script type="application/ld+json">'
            + json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
            + '</script>'
        )
    return "\n".join(tags)

for page_path in OUT.rglob("*.html"):
    page = page_path.read_text(encoding="utf-8")
    page = remove_existing(page, r'<meta\s+name=["\']robots["\'][^>]*>')
    page = remove_existing(page, r'<link\s+rel=["\']canonical["\'][^>]*>')
    page = remove_existing(page, r'<link\s+rel=["\']alternate["\'][^>]*hreflang=[^>]*>')
    page = remove_existing(page, r'<meta\s+property=["\']og:(?:type|site_name|title|description|url|image|image:type|image:width|image:height|image:alt)["\'][^>]*>')
    page = remove_existing(page, r'<meta\s+name=["\']twitter:(?:card|title|description|image|image:alt)["\'][^>]*>')

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
