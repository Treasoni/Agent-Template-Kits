#!/usr/bin/env python3
"""Guard the public documentation against feature-discovery drift."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = (
    ROOT / "README.md",
    ROOT / "docs/Agent Template Kits — 功能与使用文档.md",
)


def component_names() -> tuple[str, ...]:
    """Read the unified installer's component catalog without importing a package."""
    path = ROOT / "scripts/install.py"
    spec = importlib.util.spec_from_file_location("agent_template_install", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"docs: cannot load component catalog from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return tuple(module.COMPONENTS)


def document_label(document: Path) -> str:
    try:
        return str(document.relative_to(ROOT))
    except ValueError:
        return document.name


def check_documents(documents: tuple[Path, ...], components: tuple[str, ...]) -> list[str]:
    findings: list[str] = []
    for document in documents:
        text = document.read_text(encoding="utf-8")
        for component in components:
            if component not in text:
                findings.append(f"{document_label(document)} does not mention {component}")
    return findings


def main() -> int:
    findings = check_documents(DOCUMENTS, component_names())
    if findings:
        for finding in findings:
            print(f"docs: {finding}", file=sys.stderr)
        return 1
    print("docs: public feature coverage is current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
