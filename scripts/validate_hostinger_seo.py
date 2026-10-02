#!/usr/bin/env python3
"""Fail a Hostinger publish if the live Knowledge SEO surface is incomplete."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(sys.argv[1]).resolve()
BASE = "https://allesclinx.com/knowledge/"
STATIC = (
    "about/",
    "about/knowledge/",
    "about/tools/",
    "about/nova/",
    "about/metricon/",
    "about/checkmate/",
    "sitemap/",
)
LEGAL = {
    "privacy-policy/index.html": "https://allesclinx.com/privacy-policy/",
    "terms-conditions/index.html": "https://allesclinx.com/terms-conditions/",
    "cookie-policy/index.html": "https://allesclinx.com/cookie-policy/",
    "ai-data-use/index.html": "https://allesclinx.com/ai-data-use/",
    "accessibility/index.html": "https://allesclinx.com/accessibility/",
    "trust-security/index.html": "https://allesclinx.com/trust-security/",
}

live = json.loads((ROOT / "production" / "live.json").read_text(encoding="utf-8"))
canon = json.loads((ROOT / "taxonomy" / "canonical-structure.json").read_text(encoding="utf-8"))
by_id = {a["article_id"]: a for a in canon["articles"]}
live_ids = live.get("live_article_ids", [])
errors: list[str] = []

search = json.loads((OUT / "assets" / "live-search.json").read_text(encoding="utf-8"))
records = search.get("records", [])
if search.get("record_count") != len(records):
    errors.append("live-search record_count does not match records length")
if len(records) != len(live_ids) * 2:
    errors.append(f"expected {len(live_ids) * 2} bilingual search records, found {len(records)}")

seen = {(r.get("article_id"), r.get("locale")) for r in records}
for article_id in live_ids:
    for locale in ("en", "hi-IN"):
        if (article_id, locale) not in seen:
            errors.append(f"missing search record {article_id}:{locale}")

sitemap_text = (OUT / "sitemap.xml").read_text(encoding="utf-8")
sitemap_urls = set(re.findall(r"<loc>(.*?)</loc>", sitemap_text))
expected = {BASE}
expected.update(BASE + p for p in STATIC)
for article_id in live_ids:
    a = by_id[article_id]
    cat = a["category_slug"]
    sub = a["subcategory_slug"]
    slug = a["slug"]
    expected.add(BASE + f"library/{cat}/")
    expected.add(BASE + f"library/{cat}/{sub}/")
    expected.add(BASE + f"library/{cat}/{sub}/{slug}/")
    expected.add(BASE + f"library/{cat}/{sub}/{slug}/hi.html")

if sitemap_urls != expected:
    for url in sorted(expected - sitemap_urls):
        errors.append(f"sitemap missing {url}")
    for url in sorted(sitemap_urls - expected):
        errors.append(f"sitemap unexpected {url}")

def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        errors.append(label)

for article_id in live_ids:
    a = by_id[article_id]
    base_rel = Path("library") / a["category_slug"] / a["subcategory_slug"] / a["slug"]
    en_url = BASE + f'library/{a["category_slug"]}/{a["subcategory_slug"]}/{a["slug"]}/'
    hi_url = en_url + "hi.html"
    for locale, filename, url in (("en", "index.html", en_url), ("hi-IN", "hi.html", hi_url)):
        path = OUT / base_rel / filename
        if not path.exists():
            errors.append(f"missing rendered page {path.relative_to(OUT)}")
            continue
        text = path.read_text(encoding="utf-8")
        require(text, '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">', f"{article_id}:{locale} robots")
        require(text, f'<link rel="canonical" href="{url}">', f"{article_id}:{locale} canonical")
        require(text, f'<link rel="alternate" hreflang="en" href="{en_url}">', f"{article_id}:{locale} hreflang en")
        require(text, f'<link rel="alternate" hreflang="hi-IN" href="{hi_url}">', f"{article_id}:{locale} hreflang hi-IN")
        require(text, f'<link rel="alternate" hreflang="x-default" href="{en_url}">', f"{article_id}:{locale} hreflang x-default")
        require(text, '"@type":"Article"', f"{article_id}:{locale} Article schema")
        require(text, '"@type":"BreadcrumbList"', f"{article_id}:{locale} Breadcrumb schema")
        require(text, '<meta property="og:type" content="article">', f"{article_id}:{locale} Open Graph")
        social = OUT / "assets" / "social" / f'{article_id.lower()}-{"hi" if locale == "hi-IN" else "en"}.png'
        if not social.exists():
            errors.append(f"missing social card {social.relative_to(OUT)}")

offline = OUT / "offline.html"
if offline.exists():
    offline_text = offline.read_text(encoding="utf-8")
    require(offline_text, '<meta name="robots" content="noindex,follow">', "offline page noindex")
    if BASE + "offline.html" in sitemap_urls:
        errors.append("offline page must not be in sitemap")

for rel, canonical_url in LEGAL.items():
    path = OUT / rel
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8")
    require(text, f'<link rel="canonical" href="{canonical_url}">', f"{rel} root canonical")
    knowledge_url = BASE + rel.removesuffix("index.html")
    if knowledge_url in sitemap_urls:
        errors.append(f"duplicate Knowledge legal URL must not be in sitemap: {knowledge_url}")

home = (OUT / "index.html").read_text(encoding="utf-8")
require(home, '"@type":"WebSite"', "homepage WebSite schema")
require(home, '"@type":"CollectionPage"', "homepage CollectionPage schema")

cats = {(by_id[i]["category_slug"]) for i in live_ids}
subs = {(by_id[i]["category_slug"], by_id[i]["subcategory_slug"]) for i in live_ids}
for cat in cats:
    text = (OUT / "library" / cat / "index.html").read_text(encoding="utf-8")
    require(text, '"@type":"CollectionPage"', f"category {cat} CollectionPage schema")
    require(text, '"@type":"BreadcrumbList"', f"category {cat} Breadcrumb schema")
for cat, sub in subs:
    text = (OUT / "library" / cat / sub / "index.html").read_text(encoding="utf-8")
    require(text, '"@type":"CollectionPage"', f"subcategory {cat}/{sub} CollectionPage schema")
    require(text, '"@type":"BreadcrumbList"', f"subcategory {cat}/{sub} Breadcrumb schema")

robots_path = OUT / "robots.txt"
if not robots_path.exists():
    errors.append("missing /knowledge/robots.txt crawler-hint file")
else:
    robots = robots_path.read_text(encoding="utf-8")
    require(robots, f"Sitemap: {BASE}sitemap.xml", "robots sitemap directive")

for term in canon.get("taxonomy_terms", []):
    url = term.get("canonical_url", "")
    if url.startswith("/library/"):
        errors.append(f"taxonomy term canonical missing /knowledge/: {term.get('term_id')}")
for article in canon.get("articles", []):
    url = article.get("canonical_url", "")
    if url.startswith("https://allesclinx.com/library/"):
        errors.append(f"article canonical missing /knowledge/: {article.get('article_id')}")

if errors:
    raise SystemExit("Hostinger SEO validation failed:\n- " + "\n- ".join(errors[:200]))

print(json.dumps({
    "live_articles": len(live_ids),
    "search_records": len(records),
    "sitemap_urls": len(sitemap_urls),
    "categories": len(cats),
    "subcategories": len(subs),
    "status": "pass",
}, indent=2))
