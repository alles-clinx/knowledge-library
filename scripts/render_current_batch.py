#!/usr/bin/env python3
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = json.loads((ROOT / "production" / "plan.json").read_text(encoding="utf-8"))
LIVE = json.loads((ROOT / "production" / "live.json").read_text(encoding="utf-8"))
CANON = json.loads((ROOT / "taxonomy" / "canonical-structure.json").read_text(encoding="utf-8"))
BY_ID = {a["article_id"]: a for a in CANON["articles"]}

TEMPLATE_EN = (ROOT / "docs/library/cleaning-housekeeping/daily-cleaning/how-to-build-a-daily-cleaning-workflow/index.html").read_text(encoding="utf-8")
TEMPLATE_HI = (ROOT / "docs/library/cleaning-housekeeping/daily-cleaning/how-to-build-a-daily-cleaning-workflow/hi.html").read_text(encoding="utf-8")

current = LIVE["current_batch"]
batch = next(b for b in PLAN["batches"] if b["batch_id"] == current)
article_ids = batch["article_ids"]
available = set(LIVE.get("live_article_ids", [])) | set(article_ids)

def esc(value):
    return html.escape(str(value), quote=True)

def route(a):
    return f'/knowledge-library/library/{a["category_slug"]}/{a["subcategory_slug"]}/{a["slug"]}/'

def split_sections(content, locale):
    matches = list(re.finditer(r'<h2 id="([^"]+)">([\s\S]*?)</h2>', content))
    first = matches[0].start() if matches else len(content)
    out = [{
        "id": "overview",
        "label": "अवलोकन" if locale == "hi-IN" else "Overview",
        "html": f'<section id="overview">{content[:first].strip()}</section>'
    }]
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        label = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        cls = ' class="references"' if re.search(r'references|संदर्भ', label, re.I) else ''
        out.append({
            "id": m.group(1),
            "label": label,
            "html": f'<section{cls} id="{m.group(1)}"><h2>{m.group(2)}</h2>{content[start:end].strip()}</section>'
        })
    return out

def replace_required(source, pattern, replacement, label):
    out, count = re.subn(pattern, replacement, source, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"Could not replace {label}")
    return out

def render(template, article, locale):
    page = template
    sections = split_sections(article["content_html"].strip(), locale)
    ref = next((s["id"] for s in sections if re.search(r'references|संदर्भ', s["label"], re.I)), sections[-1]["id"])
    is_en = locale == "en"
    base = route(article)

    page = re.sub(r'<html lang="[^"]+">', f'<html lang="{"en" if is_en else "hi"}">', page, count=1)
    page = replace_required(page, r'<title>[\s\S]*?</title>', f'<title>{esc(article["seo_title"])}</title>', "title")
    page = replace_required(page, r'<meta content="[^"]*" name="description"/>', f'<meta content="{esc(article["meta_description"])}" name="description"/>', "description")
    page = page.replace('</head>', '<link rel="stylesheet" href="/knowledge-library/assets/site.css">\n<script src="/knowledge-library/assets/site.js" defer></script>\n</head>', 1)

    breadcrumb = (
        '<nav aria-label="Breadcrumb" class="breadcrumb">'
        '<a href="/knowledge-library/">Knowledge</a><span aria-hidden="true">/</span>'
        f'<a href="/knowledge-library/library/{article["category_slug"]}/">{esc(article["category"])}</a>'
        '<span aria-hidden="true">/</span>'
        f'<a href="/knowledge-library/library/{article["category_slug"]}/{article["subcategory_slug"]}/">{esc(article["subcategory"])}</a>'
        '<span aria-hidden="true" class="current-sep">/</span>'
        f'<span aria-current="page" class="current">{esc(article["title"])}</span></nav>'
    )
    page = replace_required(page, r'<nav aria-label="Breadcrumb" class="breadcrumb">[\s\S]*?</nav>', breadcrumb, "breadcrumb")

    def lang_nav(css_class):
        en_current = ' aria-current="page"' if is_en else ''
        hi_current = ' aria-current="page"' if not is_en else ''
        en_selected = 'true' if is_en else 'false'
        hi_selected = 'false' if is_en else 'true'
        return (
            f'<nav aria-label="Article language" class="language-switch {css_class}" role="tablist">'
            f'<a href="{base}"{en_current} role="tab" aria-selected="{en_selected}" lang="en">English</a>'
            f'<a href="{base}hi.html"{hi_current} role="tab" aria-selected="{hi_selected}" lang="hi">हिन्दी</a>'
            '</nav>'
        )

    page = replace_required(page, r'<nav aria-label="Article language" class="language-switch rail-language-switch" role="tablist">[\s\S]*?</nav>', lang_nav("rail-language-switch"), "desktop language switch")
    page = replace_required(page, r'<nav aria-label="Article language" class="language-switch mobile-language-switch" role="tablist">[\s\S]*?</nav>', lang_nav("mobile-language-switch"), "mobile language switch")

    header = (
        f'<header class="article-head"><h1>{esc(article["title"])}</h1>'
        f'<p class="deck">{esc(article["excerpt"])}</p>'
        '<div aria-label="Article information" class="article-meta">'
        '<span class="article-meta-item">Team Alle\'s ClinX</span>'
        f'<a class="article-meta-item" href="#{ref}">{"Referenced sources" if is_en else "संदर्भ"}</a></div>'
        f'<p class="source-note">{"Technical claims are supported by the references at the end of the article." if is_en else "तकनीकी दावों के स्रोत लेख के अंत में दिए गए हैं।"}</p></header>'
    )
    page = replace_required(page, r'<header class="article-head">[\s\S]*?</header>', header, "article header")
    page = replace_required(page, r'<article class="article" id="article-content">[\s\S]*?</article>', '<article class="article" id="article-content">' + ''.join(s["html"] for s in sections) + '</article>', "article")

    hook_start = page.index('<div class="hook-list" id="acx-hook-list">')
    hook_close = page.index('</div></nav>', hook_start)
    first_hook = page.index('<a class="hook-item"', hook_start)
    hook_links = ''.join(f'<a class="hook-item" data-target="{s["id"]}" href="#{s["id"]}">{esc(s["label"])}</a>' for s in sections)
    page = page[:first_hook] + hook_links + page[hook_close:]

    toc = '<nav aria-label="On this page" class="toc">' + ''.join(f'<a href="#{s["id"]}">{esc(s["label"])}</a>' for s in sections) + '</nav>'
    page = replace_required(page, r'<nav aria-label="On this page" class="toc">[\s\S]*?</nav>', toc, "mobile toc")

    related = []
    for rid in article.get("related_article_ids", []):
        if rid in available and rid in BY_ID:
            related.append(BY_ID[rid])
        if len(related) == 3:
            break
    suggestions = ''.join(
        f'<a class="suggestion" href="{route(a)}"><strong>{esc(a["title"])}</strong><span>{"Related Knowledge guide." if is_en else "संबंधित Knowledge guide।"}</span></a>'
        for a in related
    )
    page = replace_required(page, r'<div class="suggestions">[\s\S]*?</div>', f'<div class="suggestions">{suggestions}</div>', "suggestions")

    progress = '<div aria-label="Article sections" class="scroll-progress-list" id="acx-scroll-progress-list" role="navigation">' + ''.join(
        f'<a class="scroll-progress-item" data-target="{s["id"]}" href="#{s["id"]}"><span aria-hidden="true" class="scroll-progress-dot"></span><span>{esc(s["label"])}</span></a>'
        for s in sections
    ) + '</div>'
    page = replace_required(page, r'<div aria-label="Article sections" class="scroll-progress-list" id="acx-scroll-progress-list" role="navigation">[\s\S]*?</div>', progress, "scroll progress")
    page = replace_required(page, r'<span class="scroll-progress-label" id="acx-scroll-progress-label">[\s\S]*?</span>', f'<span class="scroll-progress-label" id="acx-scroll-progress-label">{esc(sections[0]["label"])}</span>', "progress label")

    ids = re.findall(r'\sid="([^"]+)"', page)
    if page.count("<h1>") != 1:
        raise RuntimeError(f'{article["article_id"]}: expected one H1')
    if page.count('role="tablist"') != 2:
        raise RuntimeError(f'{article["article_id"]}: expected two language tablists')
    if len(ids) != len(set(ids)):
        raise RuntimeError(f'{article["article_id"]}: duplicate DOM id')
    if 'let activeIndex = -1;' not in page:
        raise RuntimeError(f'{article["article_id"]}: hook runtime missing')
    if 'font-size:clamp(40px,4.8vw,64px);' not in page:
        raise RuntimeError(f'{article["article_id"]}: compact hero scale missing')
    return page

rendered = 0
for article_id in article_ids:
    source_dir = ROOT / "articles" / batch["category_slug"] / article_id
    en_path = source_dir / "en.json"
    hi_path = source_dir / "hi.json"
    if not en_path.exists() or not hi_path.exists():
        continue

    en = json.loads(en_path.read_text(encoding="utf-8"))
    hi = json.loads(hi_path.read_text(encoding="utf-8"))
    out_dir = ROOT / "docs" / "library" / en["category_slug"] / en["subcategory_slug"] / en["slug"]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(render(TEMPLATE_EN, en, "en"), encoding="utf-8")
    (out_dir / "hi.html").write_text(render(TEMPLATE_HI, hi, "hi-IN"), encoding="utf-8")
    rendered += 2

search_records = []
for live_id in LIVE.get("live_article_ids", []):
    meta = BY_ID.get(live_id)
    if not meta:
        continue
    en_path = ROOT / "articles" / meta["category_slug"] / live_id / "en.json"
    if not en_path.exists():
        continue
    en = json.loads(en_path.read_text(encoding="utf-8"))
    search_records.append({
        "article_id": en["article_id"],
        "title": en["title"],
        "category": en["category"],
        "category_slug": en["category_slug"],
        "subcategory": en["subcategory"],
        "subcategory_slug": en["subcategory_slug"],
        "url": route(en).lstrip("/")
    })

(ROOT / "docs" / "assets" / "live-search.json").write_text(
    json.dumps({
        "version": 1,
        "generated_for": "GitHub Pages live site",
        "record_count": len(search_records),
        "records": search_records
    }, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8"
)

print(f"Rendered {rendered} pages for {current}.")
