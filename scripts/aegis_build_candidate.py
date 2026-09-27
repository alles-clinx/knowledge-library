#!/usr/bin/env python3
"""Build a deterministic ORBIT-7 Nova knowledge candidate from live Knowledge sources."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TextExtractor(HTMLParser):
    BLOCK = {
        "p", "div", "section", "article", "h1", "h2", "h3", "h4",
        "li", "tr", "table", "ul", "ol", "br"
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in {"script", "style"}:
            self.skip_depth += 1
        elif not self.skip_depth and tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style"} and self.skip_depth:
            self.skip_depth -= 1
        elif not self.skip_depth and tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)


def html_to_text(value: str) -> str:
    parser = TextExtractor()
    parser.feed(value or "")
    text = "".join(parser.parts)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "_aegis_candidate"))
    args = ap.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    live = load_json(ROOT / "production" / "live.json")
    canon = load_json(ROOT / "taxonomy" / "canonical-structure.json")
    by_id = {item["article_id"]: item for item in canon["articles"]}
    live_ids = list(live.get("live_article_ids", []))

    records = []
    missing = []
    for article_id in live_ids:
        meta = by_id.get(article_id)
        if not meta:
            missing.append(f"{article_id}: missing canonical metadata")
            continue

        article_dir = ROOT / "articles" / meta["category_slug"] / article_id
        en_path = article_dir / "en.json"
        if not en_path.exists():
            missing.append(f"{article_id}: missing English source")
            continue

        for source_path in (en_path, article_dir / "hi.json"):
            if not source_path.exists():
                continue
            doc = load_json(source_path)
            if doc.get("article_id") != article_id:
                missing.append(f"{source_path}: article_id mismatch")
                continue
            content_html = doc.get("content_html", "")
            text = html_to_text(content_html)
            locale = doc.get("locale", source_path.stem)
            record = {
                "knowledge_id": f"{article_id}:{locale}",
                "article_id": article_id,
                "locale": locale,
                "language": doc.get("language"),
                "title": doc.get("title"),
                "category": doc.get("category"),
                "category_slug": doc.get("category_slug"),
                "subcategory": doc.get("subcategory"),
                "subcategory_slug": doc.get("subcategory_slug"),
                "slug": doc.get("slug"),
                "excerpt": doc.get("excerpt"),
                "text": text,
                "source_url": doc.get("canonical_url"),
                "editorial_status": doc.get("editorial_status"),
                "related_article_ids": doc.get("related_article_ids", []),
                "license": doc.get("license"),
                "attribution": doc.get("attribution"),
                "content_sha256": sha256_text(content_html),
                "source_path": source_path.relative_to(ROOT).as_posix()
            }
            records.append(record)

    if missing:
        raise SystemExit("Candidate build failed:\n- " + "\n- ".join(missing))

    records.sort(key=lambda r: (r["article_id"], r["locale"]))
    jsonl = "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in records)
    knowledge_hash = sha256_text(jsonl)

    language_counts = Counter(r["locale"] for r in records)
    category_counts = Counter(r["category"] for r in records if r.get("category"))
    english_ids = sorted({r["article_id"] for r in records if r["locale"] in {"en", "en-US", "en-GB"}})

    manifest = {
        "controller_name": "Aegis",
        "codename": "ORBIT-7",
        "manifest_version": 1,
        "source_live_version": live.get("version"),
        "source_current_batch": live.get("current_batch"),
        "live_article_count": len(live_ids),
        "english_article_count": len(english_ids),
        "record_count": len(records),
        "language_counts": dict(sorted(language_counts.items())),
        "category_counts": dict(sorted(category_counts.items())),
        "knowledge_sha256": knowledge_hash,
        "live_article_ids_sha256": sha256_text("\n".join(live_ids) + "\n")
    }

    (out / "knowledge.jsonl").write_text(jsonl, encoding="utf-8")
    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
