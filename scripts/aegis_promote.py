#!/usr/bin/env python3
"""Send a gated ORBIT-7 candidate to the configured Nova control endpoint."""
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate-dir", required=True)
    args = ap.parse_args()
    candidate = Path(args.candidate_dir).resolve()

    endpoint = os.environ.get("NOVA_CONTROL_ENDPOINT", "").strip()
    token = os.environ.get("NOVA_CONTROL_TOKEN", "").strip()
    target = os.environ.get("NOVA_DEPLOYMENT_TARGET", "nova-production").strip()

    if not endpoint or not token:
        raise SystemExit(
            "Promotion refused: NOVA_CONTROL_ENDPOINT and NOVA_CONTROL_TOKEN "
            "must be supplied through the protected GitHub environment."
        )
    if not endpoint.startswith("https://"):
        raise SystemExit("Promotion refused: NOVA_CONTROL_ENDPOINT must use HTTPS.")

    manifest = load_json(candidate / "manifest.json")
    records = load_jsonl(candidate / "knowledge.jsonl")
    control = load_json(ROOT / "aegis" / "config" / "nova-control.json")
    competencies = load_json(ROOT / "aegis" / "config" / "facility-manager-competencies.json")
    evals = load_jsonl(ROOT / "aegis" / "evals" / "facility-manager-core.jsonl")

    payload = {
        "controller_name": "Aegis",
        "codename": "ORBIT-7",
        "deployment_target": target,
        "manifest": manifest,
        "control": control,
        "competencies": competencies,
        "evaluations": evals,
        "knowledge_records": records
    }
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Aegis-ORBIT-7/1"
        }
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            response_body = response.read(4000).decode("utf-8", errors="replace")
            if response.status < 200 or response.status >= 300:
                raise SystemExit(f"Nova endpoint returned HTTP {response.status}")
            print(f"ORBIT-7 candidate promoted to {target}; HTTP {response.status}.")
            if response_body:
                print(response_body)
    except urllib.error.HTTPError as exc:
        detail = exc.read(2000).decode("utf-8", errors="replace")
        raise SystemExit(f"Nova promotion failed with HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Nova promotion connection failed: {exc.reason}") from exc


if __name__ == "__main__":
    main()
