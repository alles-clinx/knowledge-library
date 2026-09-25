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

print(f"Categories: {len(cats)}")
print(f"Subcategories: {len(subs)}")
print(f"Articles: {len(ids)}")
print(f"Batches: {len(plan['batches'])}")
print(f"Live articles: {len(live.get('live_article_ids',[]))}")
print(f"Errors: {len(errors)}")
for e in errors:
    print("ERROR:",e)
sys.exit(1 if errors else 0)
