#!/usr/bin/env python3
"""Guard the public documentation against feature-discovery drift."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = (
    ROOT / "README.md",
    ROOT / "docs/Agent Template Kits — 功能与使用文档.md",
    ROOT / "docs/Agent Template Kits — 功能与使用文档.html",
)
REQUIRED_FEATURES = ("multi-agent-sync", "manifest-platform")


def main() -> int:
    missing: list[str] = []
    for document in DOCUMENTS:
        text = document.read_text(encoding="utf-8")
        for feature in REQUIRED_FEATURES:
            if feature not in text:
                missing.append(f"{document.relative_to(ROOT)} does not mention {feature}")
    if missing:
        for finding in missing:
            print(f"docs: {finding}", file=sys.stderr)
        return 1
    print("docs: public feature coverage is current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
