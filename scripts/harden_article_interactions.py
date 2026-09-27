#!/usr/bin/env python3
"""Normalize and harden interaction behavior across every rendered Knowledge article."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "docs"
LIBRARY = TARGET / "library"

if not LIBRARY.exists():
    raise SystemExit(f"Library directory not found: {LIBRARY}")

changed = 0
scanned = 0

for page in LIBRARY.rglob("*.html"):
    text = page.read_text(encoding="utf-8")
    if 'id="article-content"' not in text or "js-text-toggle" not in text:
        continue
    scanned += 1
    original = text

    # The reading-size variable belongs on .page (set inline by the runtime).
    # A local .article override at <=390px blocks inheritance and makes A-/A+
    # appear to work without changing the rendered article size.
    text = re.sub(
        r'\n\s*\.article\{\s*\n\s*--reading-size\s*:\s*16px\s*;\s*\n\s*\}\s*',
        "\n",
        text,
        count=1,
    )

    # Keep the controls honest at their supported 15px/21px boundaries.
    size_marker = "sizeReadouts.forEach(function(el){ el.textContent = size + 'px'; });"
    disabled_marker = "btn.disabled = size <= 15;"
    if size_marker in text and disabled_marker not in text:
        text = text.replace(
            size_marker,
            size_marker + "\n"
            "    smallerButtons.forEach(function(btn){ btn.disabled = size <= 15; });\n"
            "    largerButtons.forEach(function(btn){ btn.disabled = size >= 21; });",
            1,
        )

    # Desktop keyboard shortcuts are useful; on touch devices the equivalent
    # browser menu/share guidance is more accurate than showing Ctrl/Cmd keys.
    mobile_marker = "const isTouchDevice = window.matchMedia('(pointer: coarse)').matches;"
    apple_marker = "const isApple = /Mac|iPhone|iPad|iPod/.test(navigator.platform || navigator.userAgent);"
    if apple_marker in text and mobile_marker not in text:
        text = text.replace(apple_marker, apple_marker + "\n  " + mobile_marker, 1)

    text = text.replace(
        "status('Press ' + shortcuts.bookmark + ' to bookmark this page in your browser.');",
        "status(isTouchDevice ? 'Use your browser menu to bookmark this page.' : 'Press ' + shortcuts.bookmark + ' to bookmark this page in your browser.');",
    )
    text = text.replace(
        "status('Press ' + shortcuts.save + ' to save this page using your browser.');",
        "status(isTouchDevice ? 'Use your browser Share or menu options to save this page.' : 'Press ' + shortcuts.save + ' to save this page using your browser.');",
    )

    if text != original:
        page.write_text(text, encoding="utf-8")
        changed += 1

print(f"Interaction hardening scanned {scanned} article pages; changed {changed}.")
