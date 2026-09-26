#!/usr/bin/env python3
import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
errors=[]

canonical=json.loads((ROOT/"taxonomy"/"canonical-structure.json").read_text(encoding="utf-8"))
plan=json.loads((ROOT/"production"/"plan.json").read_text(encoding="utf-8"))
live=json.loads((ROOT/"production"/"live.json").read_text(encoding="utf-8"))

articles=canonical["articles"]
terms=canonical["taxonomy_terms"]
ids=[a["article_id"] for a in articles]

if len(ids)!=317:
    errors.append(f"Expected 317 articles, found {len(ids)}")
if len(set(ids))!=len(ids):
    errors.append("Duplicate canonical article IDs")

cats=[t for t in terms if t.get("type")=="category"]
subs=[t for t in terms if t.get("type")=="subcategory"]
if len(cats)!=13:
    errors.append(f"Expected 13 categories, found {len(cats)}")
if len(subs)!=107:
    errors.append(f"Expected 107 subcategories, found {len(subs)}")

seen=[]
for b in plan["batches"]:
    n=len(b["article_ids"])
    if n<1 or n>5:
        errors.append(f'{b["batch_id"]}: invalid batch size {n}')
    seen.extend(b["article_ids"])
if seen!=ids:
    errors.append("Production plan does not exactly match canonical article order")
if len(plan["batches"])!=68:
    errors.append(f'Expected 68 production batches, found {len(plan["batches"])}')

unknown=set(live.get("live_article_ids",[]))-set(ids)
if unknown:
    errors.append(f"Unknown live IDs: {sorted(unknown)}")

for c in cats:
    p=ROOT/"docs"/"library"/c["slug"]/"index.html"
    if not p.exists():
        errors.append(f"Missing category page: {p.relative_to(ROOT)}")
    for s in [x for x in subs if x.get("parent_term_id")==c["term_id"]]:
        p=ROOT/"docs"/"library"/c["slug"]/s["slug"]/"index.html"
        if not p.exists():
            errors.append(f"Missing subcategory page: {p.relative_to(ROOT)}")


# Hook navigation containment: article hook links must live inside #acx-hook-list.
for page in (ROOT/"docs"/"library").rglob("*.html"):
    html=page.read_text(encoding="utf-8")
    marker='<div class="hook-list" id="acx-hook-list">'
    if marker not in html:
        continue
    start=html.index(marker)
    close=html.find("</div>", start)
    nav_close=html.find("</nav>", start)
    if close < 0 or nav_close < 0:
        errors.append(f"Malformed hook navigation: {page.relative_to(ROOT)}")
        continue
    total=html.count('class="hook-item"')
    inside=html[start:close].count('class="hook-item"')
    if total and inside != total:
        errors.append(f"Hook navigation containment failure: {page.relative_to(ROOT)} ({inside}/{total} items inside list)")


# Hook runtime initialization: first item must be explicitly activated after layout.
for page in (ROOT/"docs"/"library").rglob("*.html"):
    html=page.read_text(encoding="utf-8")
    if 'id="acx-hook-list"' not in html:
        continue
    if "let activeIndex = -1;" not in html or "updateActiveFromScroll(true);" not in html:
        errors.append(f"Hook runtime initialization failure: {page.relative_to(ROOT)}")


# Language tab control: desktop and mobile switches sit above share tools, not in the hero.
for page in (ROOT/"docs"/"library").rglob("*.html"):
    html=page.read_text(encoding="utf-8")
    if 'class="language-switch' not in html:
        continue
    if html.count('class="language-switch rail-language-switch"') != 1:
        errors.append(f"Desktop language tabs missing/duplicated: {page.relative_to(ROOT)}")
    if html.count('class="language-switch mobile-language-switch"') != 1:
        errors.append(f"Mobile language tabs missing/duplicated: {page.relative_to(ROOT)}")
    main=html.find('<main class="page">')
    head=html.find('<header class="article-head">')
    if main >= 0 and head > main and 'language-switch' in html[main:head]:
        errors.append(f"Language tabs incorrectly placed above hero: {page.relative_to(ROOT)}")
    if html.count('role="tablist"') != 2:
        errors.append(f"Language tablist count failure: {page.relative_to(ROOT)}")
    tablists=[]
    pos=0
    while True:
        start=html.find('<nav aria-label="Article language"', pos)
        if start < 0:
            break
        end=html.find('</nav>', start)
        if end < 0:
            errors.append(f"Malformed language tablist: {page.relative_to(ROOT)}")
            break
        tablists.append(html[start:end])
        pos=end+6
    if len(tablists) != 2 or any(block.count('aria-selected="true"') != 1 for block in tablists):
        errors.append(f"Language selected-tab count failure: {page.relative_to(ROOT)}")



# Interaction contract: shared controls must be present and wired on every Gold Standard article page.
interaction_pages=0
for page in (ROOT/"docs"/"library").rglob("*.html"):
    html=page.read_text(encoding="utf-8")
    if 'id="article-content"' not in html or 'js-share-toggle' not in html:
        continue
    interaction_pages += 1
    rel=page.relative_to(ROOT)

    required_counts={
        "js-share-toggle":2,
        "js-save-toggle":2,
        "js-text-toggle":2,
        "js-share-popover":2,
        "js-save-popover":2,
        "js-text-popover":2,
        "js-copy-link":2,
        "js-smaller":2,
        "js-larger":2,
        "tool-status":2,
    }
    for token,minimum in required_counts.items():
        count=html.count(token)
        if count < minimum:
            errors.append(f"Interaction control missing: {rel} ({token} {count}/{minimum})")

    runtime_tokens=[
        "setupToggle(btn,'.js-share-popover')",
        "setupToggle(btn,'.js-save-popover')",
        "setupToggle(btn,'.js-text-popover')",
        "updateShareUrls();",
        "applySize();",
        "navigator.clipboard",
        "window.print();",
        "localStorage.setItem(sizeKey",
        'id="acx-scroll-progress-toggle"',
        "function updateActive()",
    ]
    for token in runtime_tokens:
        if token not in html:
            errors.append(f"Interaction runtime missing: {rel} ({token})")

    section_ids=set(__import__("re").findall(r'<section(?:\s+class="[^"]*")?\s+id="([^"]+)"', html))
    for target in __import__("re").findall(r'class="scroll-progress-item"[^>]*data-target="([^"]+)"', html):
        if target not in section_ids:
            errors.append(f"Scroll-progress target missing: {rel} -> #{target}")
    for target in __import__("re").findall(r'class="hook-item"[^>]*data-target="([^"]+)"', html):
        if target not in section_ids:
            errors.append(f"Hook target missing: {rel} -> #{target}")

    for button in __import__("re").findall(r'<button\b[^>]*>', html):
        if 'type="button"' not in button and 'type="submit"' not in button:
            errors.append(f"Button missing explicit type: {rel}: {button[:100]}")

site_css=(ROOT/"docs"/"assets"/"site.css").read_text(encoding="utf-8")
site_js=(ROOT/"docs"/"assets"/"site.js").read_text(encoding="utf-8")
home_html=(ROOT/"docs"/"index.html").read_text(encoding="utf-8")

bad_shell_selector='.acx-site-header,.acx-bottom-brand,.acx-search-dialog,.acx-mobile-drawer{\n  display:block;\n  position:fixed;'
if bad_shell_selector in site_css:
    errors.append("Global shell CSS regression: header/search/brand incorrectly inherit drawer hidden-state rules")

for token in [
    ".acx-site-header{",
    ".acx-site-header.is-scrolled{",
    ".acx-search-button{",
    ".acx-menu-button{",
    ".acx-mobile-drawer.is-open{",
    ".acx-search-dialog.is-open{",
    ".acx-bottom-brand{",
]:
    if token not in site_css:
        errors.append(f"Global shell style missing: {token}")

for token in [
    "menuBtn.addEventListener('click'",
    "searchBtns.forEach(function(button){button.addEventListener('click',openSearch);})",
    "closeBtn.addEventListener('click',closeSearch)",
    "input.addEventListener('input',renderSearch)",
    "loadRecords();",
]:
    if token not in site_js:
        errors.append(f"Global shell interaction runtime missing: {token}")

for token in ["data-slider-prev=", "data-slider-next=", "data-slider", "slider.addEventListener('scroll'", "button.addEventListener('click'"]:
    if token not in home_html:
        errors.append(f"Homepage interaction contract missing: {token}")

print(f"Interaction article pages: {interaction_pages}")

print(f"Categories: {len(cats)}")
print(f"Subcategories: {len(subs)}")
print(f"Articles: {len(ids)}")
print(f"Batches: {len(plan['batches'])}")
print(f"Live articles: {len(live.get('live_article_ids',[]))}")
print(f"Errors: {len(errors)}")
for e in errors:
    print("ERROR:",e)
sys.exit(1 if errors else 0)
