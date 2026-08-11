#!/usr/bin/env python3
"""Guard the public documentation against feature-discovery drift."""

from __future__ import annotations

import importlib.util
import re
import sys
from urllib.parse import unquote
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
GUIDE = ROOT / "docs/Agent Template Kits — 功能与使用文档.md"
HTML_GUIDE = ROOT / "docs/USER_GUIDE.html"
DOCUMENTS = (GUIDE,)


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


def check_local_links(documents: tuple[Path, ...]) -> list[str]:
    findings: list[str] = []
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for document in documents:
        text = document.read_text(encoding="utf-8")
        for target in link_pattern.findall(text):
            path_text = target.split("#", 1)[0]
            if not path_text or "://" in path_text or path_text.startswith("#"):
                continue
            resolved = (document.parent / unquote(path_text)).resolve()
            if not resolved.exists():
                findings.append(f"{document_label(document)} has a broken local link: {target}")
    return findings


def profile_rows() -> tuple[str, ...]:
    rows: list[str] = []
    for path in sorted((ROOT / "profiles").glob("*.yaml")):
        values: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if ":" in line and not line.lstrip().startswith("#"):
                key, value = line.split(":", 1)
                values[key.strip()] = value.strip().strip("\"'")
        rows.append(f"| `{values['name']}` | `{values['skills_dir']}` | `{values['rules_dir']}`")
    return tuple(rows)


def check_profile_table(document: Path) -> list[str]:
    text = document.read_text(encoding="utf-8")
    return [f"{document_label(document)} is missing profile row: {row}" for row in profile_rows() if row not in text]


def generated_html() -> str:
    path = ROOT / "scripts/render-user-guide.py"
    spec = importlib.util.spec_from_file_location("render_user_guide", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"docs: cannot load renderer from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.render_document(GUIDE.read_text(encoding="utf-8"))


def check_generated_html() -> list[str]:
    actual = HTML_GUIDE.read_text(encoding="utf-8") if HTML_GUIDE.is_file() else None
    return [] if actual == generated_html() else ["docs/USER_GUIDE.html is stale; run scripts/render-user-guide.py"]


def main() -> int:
    findings = check_documents(DOCUMENTS, component_names())
    findings.extend(check_local_links((README, GUIDE)))
    findings.extend(check_profile_table(GUIDE))
    findings.extend(check_generated_html())
    if findings:
        for finding in findings:
            print(f"docs: {finding}", file=sys.stderr)
        return 1
    print("docs: public feature coverage is current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
