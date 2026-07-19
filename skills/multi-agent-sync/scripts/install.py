#!/usr/bin/env python3
"""Install the multi-agent synchronization runtime into another project."""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from datetime import datetime
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def runtime_files(target: Path) -> list[tuple[Path, Path, bool]]:
    runtime = target / ".agent-sync"
    files = [
        (PACKAGE_ROOT / "scripts" / "sync_agents.py", runtime / "sync_agents.py", False),
        (PACKAGE_ROOT / "assets" / "mcp-servers.json", runtime / "mcp-servers.json", True),
    ]
    for profile in sorted((PACKAGE_ROOT / "profiles").glob("*.yaml")):
        files.append((profile, runtime / "agents" / profile.name, False))
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_project", help="existing project that will receive .agent-sync")
    parser.add_argument("--apply", action="store_true", help="write files; default is a dry run")
    parser.add_argument("--dry-run", action="store_true", help="explicit dry-run mode")
    parser.add_argument("--force", action="store_true", help="back up and replace different runtime files, except the MCP manifest")
    args = parser.parse_args()
    if args.apply and args.dry_run:
        parser.error("--apply and --dry-run cannot be used together")

    target = Path(args.target_project).resolve()
    if not target.is_dir():
        parser.error(f"target project does not exist: {target}")

    actions: list[tuple[str, Path, Path | None]] = []
    conflicts: list[Path] = []
    for source, destination, preserve_if_present in runtime_files(target):
        if not source.is_file():
            print(f"[ERROR] package file missing: {source}", file=sys.stderr)
            return 2
        if not destination.exists():
            actions.append(("create", destination, source))
        elif filecmp.cmp(source, destination, shallow=False):
            actions.append(("unchanged", destination, None))
        elif preserve_if_present:
            actions.append(("preserve", destination, None))
        elif args.force:
            actions.append(("replace", destination, source))
        else:
            conflicts.append(destination)

    for action, destination, _ in actions:
        print(f"[{action.upper()}] {destination}")
    if conflicts:
        for destination in conflicts:
            print(f"[CONFLICT] {destination} (use --force to back up and replace)", file=sys.stderr)
        return 1
    if not args.apply:
        print("[OK] dry run complete")
        return 0

    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    for action, destination, source in actions:
        if action in {"unchanged", "preserve"}:
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        if action == "replace":
            backup = destination.with_name(destination.name + f".bak.{stamp}")
            destination.replace(backup)
            print(f"[BACKUP] {backup}")
        shutil.copy2(source, destination)
    print("[OK] installed .agent-sync runtime")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
