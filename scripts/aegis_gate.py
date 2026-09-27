#!/usr/bin/env python3
"""Static integrity and facility-manager quality gates for an ORBIT-7 candidate."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{n}: invalid JSON: {exc}") from exc
    return rows


def fail(errors: list[str]) -> None:
    if errors:
        raise SystemExit("Aegis gate failed:\n- " + "\n- ".join(errors))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate-dir", default=str(ROOT / "_aegis_candidate"))
    args = ap.parse_args()
    candidate = Path(args.candidate_dir).resolve()

    control = load_json(ROOT / "aegis" / "config" / "nova-control.json")
    competencies = load_json(ROOT / "aegis" / "config" / "facility-manager-competencies.json")
    evals = load_jsonl(ROOT / "aegis" / "evals" / "facility-manager-core.jsonl")
    live = load_json(ROOT / "production" / "live.json")
    manifest = load_json(candidate / "manifest.json")
    records = load_jsonl(candidate / "knowledge.jsonl")

    errors: list[str] = []

    if control.get("controller_name") != "Aegis" or control.get("codename") != "ORBIT-7":
        errors.append("control identity must be Aegis / ORBIT-7")
    if control.get("knowledge_policy", {}).get("retrieval_mode") != "retrieval-first":
        errors.append("Nova knowledge policy must remain retrieval-first")
    if control.get("knowledge_policy", {}).get("fine_tuning", {}).get("enabled") is not False:
        errors.append("fine-tuning must remain disabled until a measured evaluation need is documented")

    raw_control = json.dumps(control).lower()
    forbidden_literals = ["sk-", "bearer ey", "api_key\": \""]
    if any(value in raw_control for value in forbidden_literals):
        errors.append("control config appears to contain a committed credential")

    eval_ids = [row.get("id") for row in evals]
    minimum = int(control.get("release_policy", {}).get("minimum_eval_cases", 12))
    if len(evals) < minimum:
        errors.append(f"need at least {minimum} evaluation cases")
    if len(eval_ids) != len(set(eval_ids)):
        errors.append("evaluation IDs must be unique")
    for row in evals:
        if not row.get("prompt"):
            errors.append(f"{row.get('id')}: missing prompt")
        if len(row.get("expected_behaviors", [])) < 2:
            errors.append(f"{row.get('id')}: expected_behaviors must contain at least two checks")
        if not row.get("forbidden_behaviors"):
            errors.append(f"{row.get('id')}: forbidden_behaviors must not be empty")
        if not row.get("tags"):
            errors.append(f"{row.get('id')}: tags must not be empty")

    tags = {tag for row in evals for tag in row.get("tags", [])}
    for required in {"high-risk", "bilingual", "jurisdiction", "uncertainty", "quality-verification"}:
        if required not in tags:
            errors.append(f"evaluation suite is missing required tag: {required}")

    competency_ids = [item.get("id") for item in competencies.get("competencies", [])]
    if len(competency_ids) != len(set(competency_ids)):
        errors.append("competency IDs must be unique")
    if len(competency_ids) < 10:
        errors.append("facility-manager competency map is unexpectedly small")

    live_ids = set(live.get("live_article_ids", []))
    record_ids = {r.get("article_id") for r in records}
    english_ids = {
        r.get("article_id") for r in records
        if r.get("locale") in {"en", "en-US", "en-GB"}
    }
    if not record_ids.issubset(live_ids):
        errors.append("candidate contains article IDs not admitted by production/live.json")
    if english_ids != live_ids:
        missing = sorted(live_ids - english_ids)
        extra = sorted(english_ids - live_ids)
        errors.append(f"English live coverage mismatch; missing={missing[:8]} extra={extra[:8]}")

    sha_re = re.compile(r"^[0-9a-f]{64}$")
    for row in records:
        kid = row.get("knowledge_id", "<unknown>")
        if row.get("license") != control.get("knowledge_policy", {}).get("required_license"):
            errors.append(f"{kid}: wrong or missing content license")
        if len((row.get("text") or "").strip()) < 120:
            errors.append(f"{kid}: extracted knowledge text is too short")
        if not sha_re.match(row.get("content_sha256", "")):
            errors.append(f"{kid}: missing valid content SHA-256")
        if "<script" in (row.get("text") or "").lower():
            errors.append(f"{kid}: executable markup leaked into extracted text")

    if manifest.get("controller_name") != "Aegis" or manifest.get("codename") != "ORBIT-7":
        errors.append("candidate manifest identity mismatch")
    if manifest.get("live_article_count") != len(live_ids):
        errors.append("manifest live_article_count mismatch")
    if manifest.get("english_article_count") != len(live_ids):
        errors.append("manifest English coverage mismatch")
    if manifest.get("record_count") != len(records):
        errors.append("manifest record_count mismatch")
    if not sha_re.match(manifest.get("knowledge_sha256", "")):
        errors.append("manifest knowledge hash is invalid")

    fail(errors)
    print(
        f"Aegis gate passed: {len(live_ids)} live articles, "
        f"{len(records)} locale records, {len(evals)} facility-manager evals, "
        f"{len(competency_ids)} competencies."
    )


if __name__ == "__main__":
    main()
