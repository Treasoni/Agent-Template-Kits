#!/usr/bin/env python3
"""Detect supported agent layouts and install selected template components.

This coordinator intentionally delegates each component to its existing
installer.  It adds one cross-platform entry point with a dry-run default,
automatic profile detection, explicit profile selection, and a confirmation
gate before any target project files are changed.
"""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE_ROOT = ROOT / "profiles"
COMPONENTS = ("self-learning", "env", "prompt-cache", "workflow", "registry")


@dataclass(frozen=True)
class Profile:
    name: str
    description: str
    agent_dir: str
    skills_dir: str
    rules_dir: str
    scripts_dir: str
    hooks_dir: str
    entry_file: str
    hook_config: str


def parse_flat_yaml(path: Path) -> dict[str, str]:
    """Read the repository's scalar-only profile files without PyYAML."""
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def load_profiles() -> dict[str, Profile]:
    profiles: dict[str, Profile] = {}
    for path in sorted(PROFILE_ROOT.glob("*.yaml")):
        values = parse_flat_yaml(path)
        required = ("name", "agent_dir", "skills_dir", "rules_dir", "scripts_dir", "entry_file")
        missing = [key for key in required if not values.get(key)]
        if missing:
            raise SystemExit(f"profile {path} is missing: {', '.join(missing)}")
        profile = Profile(
            name=values["name"],
            description=values.get("description", ""),
            agent_dir=values["agent_dir"],
            skills_dir=values["skills_dir"],
            rules_dir=values["rules_dir"],
            scripts_dir=values["scripts_dir"],
            hooks_dir=values.get("hooks_dir", ""),
            entry_file=values["entry_file"],
            hook_config=values.get("hook_config", ""),
        )
        profiles[profile.name] = profile
    return profiles


def is_unambiguous_entry(entry_file: str) -> bool:
    return Path(entry_file).name not in {"AGENTS.md", "INSTRUCTIONS.md"}


def detect_profiles(target: Path, profiles: dict[str, Profile]) -> list[tuple[Profile, int, list[str]]]:
    """Return likely installed agent profiles, with transparent evidence."""
    matches: list[tuple[Profile, int, list[str]]] = []
    for profile in profiles.values():
        # generic is a destination fallback, not evidence of a specific runtime.
        if profile.name == "generic":
            continue

        score = 0
        evidence: list[str] = []

        def add_if_exists(path_text: str, weight: int, label: str) -> None:
            nonlocal score
            if path_text and (target / path_text).exists():
                score += weight
                evidence.append(label)

        # A normal runtime directory is good evidence.  .github alone is common
        # in unrelated repositories, so it is deliberately only a weak signal.
        add_if_exists(profile.agent_dir, 1 if profile.agent_dir == ".github" else 3, profile.agent_dir)
        add_if_exists(profile.skills_dir, 3, profile.skills_dir)
        add_if_exists(profile.rules_dir, 3, profile.rules_dir)
        add_if_exists(profile.scripts_dir, 1, profile.scripts_dir)
        add_if_exists(profile.hooks_dir, 2, profile.hooks_dir)
        add_if_exists(profile.hook_config, 3, profile.hook_config)
        add_if_exists(profile.entry_file, 3 if is_unambiguous_entry(profile.entry_file) else 1, profile.entry_file)

        # Score three means either an identifying runtime directory or an
        # identifying entry/config file.  This avoids guessing from AGENTS.md.
        if score >= 3:
            matches.append((profile, score, evidence))

    return sorted(matches, key=lambda item: (-item[1], item[0].name))


def find_bash() -> str | None:
    """Find Bash, including the standard Git for Windows locations."""
    if bash := shutil.which("bash"):
        return bash
    if os.name != "nt":
        return None

    roots = [os.environ.get("ProgramFiles", ""), os.environ.get("ProgramW6432", "")]
    roots.extend([os.environ.get("ProgramFiles(x86)", ""), "C:\\Program Files", "C:\\Program Files (x86)"])
    candidates = [Path(root) / "Git" / "bin" / "bash.exe" for root in roots if root]
    return next((str(path) for path in candidates if path.is_file()), None)


def format_command(command: list[str]) -> str:
    return subprocess.list2cmdline(command) if os.name == "nt" else shlex.join(command)


def hook_python_command() -> str:
    """Choose a command name that a target runtime can resolve at session start."""
    return Path(sys.executable).name if os.name == "nt" else "python3"


def commands_for(profile: Profile, target: Path, components: tuple[str, ...], args: argparse.Namespace, bash: str) -> list[list[str]]:
    commands: list[list[str]] = []
    if "self-learning" in components:
        command = [
            sys.executable,
            str(ROOT / "templates/self-learning/install.py"),
            "--target",
            str(target),
            "--profile",
            profile.name,
            "--python-command",
            hook_python_command(),
        ]
        if args.overwrite:
            command.append("--overwrite")
        if args.no_hooks:
            command.append("--no-hooks")
        commands.append(command)
    if "env" in components:
        command = [sys.executable, str(ROOT / "templates/env/install.py"), "--target", str(target), "--profile", profile.name]
        if args.overwrite:
            command.append("--overwrite")
        commands.append(command)
    if "prompt-cache" in components:
        commands.append(
            [
                bash,
                str(ROOT / "skills/prompt-cache-optimizer/scripts/prompt-cache-bootstrap.sh"),
                "--apply",
                "--platform",
                profile.name,
                "--with-skill",
                "--target",
                str(target),
            ]
        )
    if "workflow" in components:
        command = [bash, str(ROOT / "skills/workflow-todo-state/scripts/install.sh"), str(target), "--profile", profile.name, "--with-skill", "--init-layout", "--update-agents"]
        if args.force_workflow:
            command.append("--force")
        commands.append(command)
    if "registry" in components:
        commands.append(
            [
                sys.executable,
                str(ROOT / "skills/sync-skill-registry/scripts/sync_skill_registry.py"),
                "--profile",
                profile.name,
                "--root",
                str(target),
                "--create",
                "--with-skill",
            ]
        )
    return commands


def parse_components(raw: str, parser: argparse.ArgumentParser) -> tuple[str, ...]:
    values = tuple(item.strip() for item in raw.split(",") if item.strip())
    unknown = sorted(set(values) - set(COMPONENTS))
    if unknown:
        parser.error(f"unknown component(s): {', '.join(unknown)}; choose from {', '.join(COMPONENTS)}")
    if not values:
        parser.error("--components must name at least one component")
    return tuple(dict.fromkeys(values))


def confirm(selected: list[Profile], components: tuple[str, ...], target: Path, assume_yes: bool) -> bool:
    if assume_yes:
        return True
    if not sys.stdin.isatty():
        raise SystemExit("--apply without a TTY requires --yes")
    answer = input(
        f"Install {', '.join(components)} for {', '.join(profile.name for profile in selected)} into {target}? [y/N] "
    )
    return answer.strip().lower() in {"y", "yes"}


def build_parser(profiles: dict[str, Profile]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detect supported agent layouts and install selected template components.",
        epilog="Profiles: " + ", ".join(sorted(profiles)),
    )
    parser.add_argument("--target", required=True, help="Existing target project directory")
    parser.add_argument("--detect", action="store_true", help="Show detected profile candidates and their evidence")
    parser.add_argument("--use-detected", action="store_true", help="Select every automatically detected profile")
    parser.add_argument("--profile", action="append", default=[], help="Explicit profile to install; repeat for multiple profiles")
    parser.add_argument("--components", default=",".join(COMPONENTS), help="Comma-separated components (default: all)")
    parser.add_argument("--apply", action="store_true", help="Perform the installation; without this flag only print the plan")
    parser.add_argument("--yes", action="store_true", help="Skip the interactive confirmation required by --apply")
    parser.add_argument("--overwrite", action="store_true", help="Allow self-learning and env installers to replace copied templates")
    parser.add_argument("--no-hooks", action="store_true", help="Do not install self-learning session hooks")
    parser.add_argument("--force-workflow", action="store_true", help="Pass --force to the workflow installer")
    return parser


def main() -> int:
    profiles = load_profiles()
    parser = build_parser(profiles)
    args = parser.parse_args()
    target = Path(args.target).expanduser().resolve()
    if not target.is_dir():
        parser.error(f"--target must be an existing directory: {target}")
    components = parse_components(args.components, parser)

    detected = detect_profiles(target, profiles)
    if args.detect or args.use_detected:
        print(f"Detected profiles in: {target}")
        if detected:
            for profile, score, evidence in detected:
                print(f"  - {profile.name} (score {score}): {', '.join(evidence)}")
        else:
            print("  - none")

    selected_names = list(dict.fromkeys(args.profile))
    unknown = sorted(set(selected_names) - set(profiles))
    if unknown:
        parser.error(f"unknown profile(s): {', '.join(unknown)}; choose from {', '.join(sorted(profiles))}")
    if args.use_detected:
        selected_names.extend(profile.name for profile, _score, _evidence in detected)
        selected_names = list(dict.fromkeys(selected_names))

    if not selected_names:
        if args.detect:
            return 0
        parser.error("select a profile with --profile NAME or automatically select candidates with --use-detected")
    selected = [profiles[name] for name in selected_names]

    bash_required = bool({"prompt-cache", "workflow"} & set(components))
    bash = find_bash() if bash_required else "bash"
    if bash_required and not bash:
        message = "Bash is required for prompt-cache/workflow. On Windows, install Git for Windows (Git Bash) or use WSL."
        if args.apply:
            raise SystemExit(message)
        bash = "bash"
        print(f"[REQUIRES] {message}")

    all_commands = [
        command
        for profile in selected
        for command in commands_for(profile, target, components, args, bash)
    ]
    print("\nInstall plan:")
    for command in all_commands:
        print(f"  {format_command(command)}")

    if not args.apply:
        print("\n[DRY RUN] Add --apply to run this plan. --apply asks for confirmation unless --yes is supplied.")
        return 0
    if not confirm(selected, components, target, args.yes):
        print("[CANCELLED] No files were changed.")
        return 0

    for command in all_commands:
        print(f"\n[RUN] {format_command(command)}")
        subprocess.run(command, cwd=ROOT, check=True)
    print("\n[OK] Installation complete.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode) from error
