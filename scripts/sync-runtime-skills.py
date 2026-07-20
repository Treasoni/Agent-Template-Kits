#!/usr/bin/env python3
"""Check or refresh this repository's runtime skill mirrors.

The distributable packages and templates below are the canonical sources.
`.agents/skills` is the local Codex runtime mirror and may contain additional
platform manifests, so the synchronizer only manages files that exist in the
canonical source.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


MIRRORS = (
    (Path("skills/manifest-platform"), Path(".agents/skills/manifest-platform")),
    (Path("skills/workflow-todo-state"), Path(".agents/skills/workflow-todo-state")),
    (Path("templates/self-learning/skills/maintain-learnings"), Path(".agents/skills/maintain-learnings")),
)
IGNORED_PARTS = {"__pycache__"}
IGNORED_NAMES = {".DS_Store"}


def managed_files(directory: Path) -> dict[Path, Path]:
    files: dict[Path, Path] = {}
    for path in directory.rglob("*"):
        if not path.is_file() or path.name in IGNORED_NAMES:
            continue
        relative = path.relative_to(directory)
        if IGNORED_PARTS.intersection(relative.parts):
            continue
        files[relative] = path
    return files


def synchronize(root: Path, apply: bool) -> list[str]:
    findings: list[str] = []
    for source_relative, target_relative in MIRRORS:
        source = root / source_relative
        target = root / target_relative
        if not source.is_dir():
            findings.append(f"[ERROR] canonical source is missing: {source_relative}")
            continue
        source_files = managed_files(source)
        for relative, source_file in sorted(source_files.items()):
            target_file = target / relative
            if target_file.is_file() and target_file.read_bytes() == source_file.read_bytes():
                continue
            action = "updated" if target_file.exists() else "created"
            findings.append(f"[DRIFT] {action}: {target_relative / relative}")
            if apply:
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, target_file)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root")
    parser.add_argument("--apply", action="store_true", help="refresh runtime mirrors; default is check-only")
    parser.add_argument("--check", action="store_true", help="explicit check-only mode")
    args = parser.parse_args()
    if args.apply and args.check:
        parser.error("--apply and --check cannot be used together")
    findings = synchronize(Path(args.root).resolve(), args.apply)
    if not findings:
        print("[OK] runtime skill mirrors are synchronized")
        return 0
    for finding in findings:
        print(finding)
    if args.apply:
        print("[OK] runtime skill mirrors refreshed")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
