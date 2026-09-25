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


# Language tab control: bilingual article pages use the locked two-tab segmented switch.
for page in (ROOT/"docs"/"library").rglob("*.html"):
    html=page.read_text(encoding="utf-8")
    if 'class="language-switch"' not in html:
        continue
    start=html.find('class="language-switch"')
    end=html.find("</nav>", start)
    block=html[start:end]
    if 'role="tablist"' not in block:
        errors.append(f"Language tablist missing: {page.relative_to(ROOT)}")
    if block.count('role="tab"') != 2:
        errors.append(f"Language tab count failure: {page.relative_to(ROOT)}")
    if block.count('aria-selected="true"') != 1:
        errors.append(f"Language selected-tab failure: {page.relative_to(ROOT)}")

print(f"Categories: {len(cats)}")
print(f"Subcategories: {len(subs)}")
print(f"Articles: {len(ids)}")
print(f"Batches: {len(plan['batches'])}")
print(f"Live articles: {len(live.get('live_article_ids',[]))}")
print(f"Errors: {len(errors)}")
for e in errors:
    print("ERROR:",e)
sys.exit(1 if errors else 0)
