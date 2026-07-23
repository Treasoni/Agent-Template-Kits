#!/usr/bin/env python3
"""Detect supported agent layouts and install selected template components.

This coordinator intentionally delegates each component to its existing
installer.  It adds one cross-platform entry point with a dry-run default,
automatic profile detection, explicit profile selection, and a confirmation
gate before any target project files are changed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE_ROOT = ROOT / "profiles"
COMPONENTS = ("self-learning", "env", "prompt-cache", "workflow", "manifest-platform", "registry", "multi-agent-sync")
DEFAULT_COMPONENTS = ("self-learning", "env", "prompt-cache", "workflow", "registry")
STATE_DIRECTORY = ".agent-template-kits"
STATE_FILENAME = "install-state.json"
STATE_SCHEMA_VERSION = 2
SNAPSHOT_IGNORED_PARTS = {".git", STATE_DIRECTORY, "__pycache__"}
GLOBAL_COMPONENTS = frozenset({"multi-agent-sync"})
INSTALLER_BACKUP_PART = re.compile(r".+\.bak\.\d{14}$")


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


@dataclass(frozen=True)
class InstallSelections:
    """Profile-specific and target-wide components selected by unified installs."""

    profile_components: dict[str, tuple[str, ...]]
    global_components: tuple[str, ...]

    @property
    def components(self) -> tuple[str, ...]:
        values = [component for components in self.profile_components.values() for component in components]
        return tuple(dict.fromkeys([*values, *self.global_components]))

    def installations(self, profiles: dict[str, Profile]) -> list[tuple[Profile, tuple[str, ...]]]:
        return [(profiles[name], components) for name, components in self.profile_components.items()]


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


def child_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHON", hook_python_command())
    return env


def state_path(target: Path) -> Path:
    return target / STATE_DIRECTORY / STATE_FILENAME


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_tree(target: Path) -> dict[str, str]:
    """Return hashes for regular managed files, excluding updater metadata."""
    snapshot: dict[str, str] = {}
    for path in target.rglob("*"):
        relative = path.relative_to(target)
        if SNAPSHOT_IGNORED_PARTS.intersection(relative.parts) or any(
            INSTALLER_BACKUP_PART.fullmatch(part) for part in relative.parts
        ):
            continue
        if not path.is_file() or path.is_symlink():
            continue
        snapshot[relative.as_posix()] = sha256_file(path)
    return snapshot


def symbolic_links(target: Path) -> list[str]:
    """List links that could redirect an installer write outside the target."""
    return sorted(path.relative_to(target).as_posix() for path in target.rglob("*") if path.is_symlink())


def changed_paths(before: dict[str, str], after: dict[str, str]) -> list[str]:
    return sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))


def source_version() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(ROOT), "describe", "--tags", "--always", "--dirty"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unversioned"


def load_install_state(target: Path) -> dict[str, object] | None:
    path = state_path(target)
    if not path.is_file():
        return None
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"invalid install state: {path}: {error}") from error
    if not isinstance(state, dict):
        raise SystemExit(f"invalid install state: {path}")
    if state.get("schema_version") != STATE_SCHEMA_VERSION:
        raise SystemExit(f"unsupported install state schema: {path}")
    if not isinstance(state.get("profiles"), list) or not isinstance(state.get("components"), list):
        raise SystemExit(f"invalid install state selections: {path}")
    if not all(isinstance(name, str) for name in state["profiles"] + state["components"]):
        raise SystemExit(f"invalid install state selections: {path}")
    profile_components = state.get("profile_components")
    if not isinstance(profile_components, dict) or not all(
        isinstance(name, str) and isinstance(components, list) and all(isinstance(component, str) for component in components)
        for name, components in profile_components.items()
    ):
        raise SystemExit(f"invalid profile component state: {path}")
    if not isinstance(state.get("global_components"), list) or not all(
        isinstance(component, str) for component in state["global_components"]
    ):
        raise SystemExit(f"invalid global component state: {path}")
    if not isinstance(state.get("managed_files"), dict):
        raise SystemExit(f"invalid managed file state: {path}")
    if not all(isinstance(name, str) and isinstance(digest, str) for name, digest in state["managed_files"].items()):
        raise SystemExit(f"invalid managed file fingerprints: {path}")
    return state


def write_install_state(
    target: Path,
    selections: InstallSelections,
    before: dict[str, str],
    previous: dict[str, object] | None = None,
) -> None:
    after = snapshot_tree(target)
    previous_managed = previous.get("managed_files", {}) if previous else {}
    managed = dict(previous_managed) if isinstance(previous_managed, dict) else {}
    for relative in changed_paths(before, after):
        if relative in after:
            managed[relative] = after[relative]
        else:
            managed.pop(relative, None)
    state = {
        "schema_version": STATE_SCHEMA_VERSION,
        "source_version": source_version(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "profiles": list(selections.profile_components),
        "components": list(selections.components),
        "profile_components": {
            name: list(components) for name, components in selections.profile_components.items()
        },
        "global_components": list(selections.global_components),
        "managed_files": dict(sorted(managed.items())),
    }
    path = state_path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def copy_target_for_update(target: Path, destination: Path) -> None:
    def ignore(_directory: str, names: list[str]) -> set[str]:
        return {name for name in names if name in SNAPSHOT_IGNORED_PARTS}

    shutil.copytree(target, destination, ignore=ignore, symlinks=True)


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
        command = [
            bash,
            str(ROOT / "skills/prompt-cache-optimizer/scripts/prompt-cache-bootstrap.sh"),
            "--apply",
            "--platform",
            profile.name,
            "--with-skill",
            "--target",
            str(target),
        ]
        if getattr(args, "prompt_cache_overwrite", False):
            command.append("--overwrite")
        commands.append(command)
    if "workflow" in components:
        command = [bash, str(ROOT / "skills/workflow-todo-state/scripts/install.sh"), str(target), "--profile", profile.name, "--with-skill", "--init-layout", "--update-agents"]
        if args.force_workflow:
            command.append("--force")
        commands.append(command)
    if "manifest-platform" in components:
        command = [
            bash,
            str(ROOT / ".agents/skills/manifest-platform/scripts/install.sh"),
            "--target",
            str(target),
            "--agent-dir",
            profile.agent_dir,
            "--skills-dir",
            profile.skills_dir,
            "--workflows-dir",
            f"{profile.agent_dir}/workflows",
            "--subagents-dir",
            f"{profile.agent_dir}/agents",
            "--hooks-dir",
            profile.hooks_dir or f"{profile.agent_dir}/hooks",
            "--with-skill",
        ]
        if profile.hook_config:
            command.extend(["--hooks-config", profile.hook_config])
        if args.force_manifest_platform:
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


def all_commands_for(
    installations: list[tuple[Profile, tuple[str, ...]]],
    target: Path,
    args: argparse.Namespace,
    bash: str,
    global_components: tuple[str, ...],
) -> list[list[str]]:
    commands = [
        command
        for profile, components in installations
        for command in commands_for(profile, target, components, args, bash)
    ]
    if "multi-agent-sync" in global_components:
        command = [
            sys.executable,
            str(ROOT / "skills/multi-agent-sync/scripts/install.py"),
            str(target),
            "--apply",
        ]
        if getattr(args, "force_multi_agent_sync", False):
            command.append("--force")
        commands.append(command)
    return commands


def parse_components(raw: str, parser: argparse.ArgumentParser) -> tuple[str, ...]:
    values = tuple(item.strip() for item in raw.split(",") if item.strip())
    unknown = sorted(set(values) - set(COMPONENTS))
    if unknown:
        parser.error(f"unknown component(s): {', '.join(unknown)}; choose from {', '.join(COMPONENTS)}")
    if not values:
        parser.error("--components must name at least one component")
    return tuple(dict.fromkeys(values))


def selections_for_install(selected: list[Profile], components: tuple[str, ...]) -> InstallSelections:
    profile_components = tuple(component for component in components if component not in GLOBAL_COMPONENTS)
    global_components = tuple(component for component in components if component in GLOBAL_COMPONENTS)
    return InstallSelections(
        profile_components={profile.name: profile_components for profile in selected},
        global_components=global_components,
    )


def merge_install_selections(
    previous: dict[str, object] | None,
    current: InstallSelections,
    profiles: dict[str, Profile],
) -> InstallSelections:
    if previous is None:
        return current
    previous_components = previous["profile_components"]
    previous_global = previous["global_components"]
    if not isinstance(previous_components, dict) or not isinstance(previous_global, list):
        raise SystemExit("invalid install state selections")
    unavailable = sorted(set(previous_components) - set(profiles))
    if unavailable:
        raise SystemExit(f"install state references unavailable profile(s): {', '.join(unavailable)}")
    merged_profiles = {
        name: tuple(components) for name, components in previous_components.items()
    }
    for name, components in current.profile_components.items():
        merged_profiles[name] = tuple(dict.fromkeys([*merged_profiles.get(name, ()), *components]))
    return InstallSelections(
        profile_components=merged_profiles,
        global_components=tuple(dict.fromkeys([*previous_global, *current.global_components])),
    )


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
    parser.add_argument("--components", default=",".join(DEFAULT_COMPONENTS), help="Comma-separated components (default: core components)")
    parser.add_argument("--apply", action="store_true", help="Perform the installation; without this flag only print the plan")
    parser.add_argument("--yes", action="store_true", help="Skip the interactive confirmation required by --apply")
    parser.add_argument("--overwrite", action="store_true", help="Allow self-learning and env installers to replace copied templates")
    parser.add_argument("--no-hooks", action="store_true", help="Do not install self-learning session hooks")
    parser.add_argument("--force-workflow", action="store_true", help="Pass --force to the workflow installer")
    parser.add_argument("--force-manifest-platform", action="store_true", help="Pass --force to the manifest-platform installer")
    return parser


def install_main(argv: list[str] | None = None) -> int:
    profiles = load_profiles()
    parser = build_parser(profiles)
    args = parser.parse_args(argv)
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

    bash_required = bool({"prompt-cache", "workflow", "manifest-platform"} & set(components))
    bash = find_bash() if bash_required else "bash"
    if bash_required and not bash:
        message = "Bash is required for prompt-cache/workflow. On Windows, install Git for Windows (Git Bash) or use WSL."
        if args.apply:
            raise SystemExit(message)
        bash = "bash"
        print(f"[REQUIRES] {message}")

    current_selections = selections_for_install(selected, components)
    all_commands = all_commands_for(
        current_selections.installations(profiles),
        target,
        args,
        bash,
        current_selections.global_components,
    )
    print("\nInstall plan:")
    for command in all_commands:
        print(f"  {format_command(command)}")

    if not args.apply:
        print("\n[DRY RUN] Add --apply to run this plan. --apply asks for confirmation unless --yes is supplied.")
        return 0
    if not confirm(selected, components, target, args.yes):
        print("[CANCELLED] No files were changed.")
        return 0

    before = snapshot_tree(target)
    previous = load_install_state(target)
    recorded_selections = merge_install_selections(previous, current_selections, profiles)
    for command in all_commands:
        print(f"\n[RUN] {format_command(command)}")
        subprocess.run(command, cwd=ROOT, check=True, env=child_env())
    write_install_state(target, recorded_selections, before, previous)
    print("\n[OK] Installation complete.")
    return 0


def build_update_parser(profiles: dict[str, Profile]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview and safely apply template updates recorded by the unified installer.",
        epilog="Profiles: " + ", ".join(sorted(profiles)),
    )
    parser.add_argument("--target", required=True, help="Existing target project directory with installer state")
    parser.add_argument("--accept", action="append", default=[], metavar="PATH", help="Approve one reported conflict path; repeat as needed")
    parser.add_argument("--apply", action="store_true", help="Apply the previewed update after conflict approval")
    parser.add_argument("--yes", action="store_true", help="Skip the interactive confirmation required by --apply")
    return parser


def selections_from_state(
    state: dict[str, object],
    profiles: dict[str, Profile],
    parser: argparse.ArgumentParser,
) -> InstallSelections:
    raw_profile_components = state["profile_components"]
    raw_global_components = state["global_components"]
    if not isinstance(raw_profile_components, dict) or not isinstance(raw_global_components, list):
        parser.error("install state contains invalid component selections")
    selected_names = list(raw_profile_components)
    unknown_profiles = sorted(set(selected_names) - set(profiles))
    if unknown_profiles:
        parser.error(f"install state references unavailable profile(s): {', '.join(unknown_profiles)}")
    profile_components: dict[str, tuple[str, ...]] = {}
    for name, raw_components in raw_profile_components.items():
        if not isinstance(raw_components, list) or not all(isinstance(component, str) for component in raw_components):
            parser.error("install state contains invalid profile component selections")
        components = tuple(dict.fromkeys(raw_components))
        if set(components) & GLOBAL_COMPONENTS:
            parser.error("install state assigns a target-wide component to a profile")
        profile_components[name] = components
    global_components = tuple(dict.fromkeys(raw_global_components))
    all_components = [component for components in profile_components.values() for component in components]
    all_components.extend(global_components)
    unknown_components = sorted(set(all_components) - set(COMPONENTS))
    if unknown_components or not all_components:
        parser.error("install state contains unavailable or empty component selections")
    if set(global_components) - GLOBAL_COMPONENTS:
        parser.error("install state contains a profile-specific target-wide component")
    return InstallSelections(profile_components=profile_components, global_components=global_components)


def update_command_arguments() -> argparse.Namespace:
    return argparse.Namespace(
        overwrite=True,
        no_hooks=False,
        force_workflow=True,
        force_manifest_platform=True,
        prompt_cache_overwrite=True,
        force_multi_agent_sync=True,
    )


def run_candidate(commands: list[list[str]]) -> int:
    for command in commands:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=child_env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode:
            print(f"[ERROR] update candidate command failed: {format_command(command)}", file=sys.stderr)
            if result.stdout:
                print(result.stdout, end="", file=sys.stderr)
            if result.stderr:
                print(result.stderr, end="", file=sys.stderr)
            return result.returncode
    return 0


def action_for_path(before: dict[str, str], after: dict[str, str], relative: str) -> str:
    if relative not in before:
        return "CREATE"
    if relative not in after:
        return "REMOVE"
    return "UPDATE"


def confirm_update(target: Path, assume_yes: bool) -> bool:
    if assume_yes:
        return True
    if not sys.stdin.isatty():
        raise SystemExit("--apply without a TTY requires --yes")
    answer = input(f"Apply the approved template update to {target}? [y/N] ")
    return answer.strip().lower() in {"y", "yes"}


def backup_planned_files(target: Path, planned: list[str]) -> None:
    existing = [relative for relative in planned if (target / relative).is_file() and not (target / relative).is_symlink()]
    if not existing:
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup_root = target / STATE_DIRECTORY / "backups" / stamp
    for relative in existing:
        destination = backup_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target / relative, destination)
        print(f"[BACKUP] {relative}")


def update_main(argv: list[str] | None = None) -> int:
    profiles = load_profiles()
    parser = build_update_parser(profiles)
    args = parser.parse_args(argv)
    target = Path(args.target).expanduser().resolve()
    if not target.is_dir():
        parser.error(f"--target must be an existing directory: {target}")

    state = load_install_state(target)
    if state is None:
        print(
            f"[ERROR] no unified installer state at {state_path(target)}. "
            "Run scripts/install.py with --apply before using update.",
            file=sys.stderr,
        )
        return 1
    selections = selections_from_state(state, profiles, parser)
    bash_required = bool({"prompt-cache", "workflow", "manifest-platform"} & set(selections.components))
    bash = find_bash() if bash_required else "bash"
    if bash_required and not bash:
        raise SystemExit("Bash is required for prompt-cache/workflow. Install Git for Windows or use WSL.")

    links = symbolic_links(target)
    if links:
        print("[ERROR] update refuses targets containing symbolic links", file=sys.stderr)
        for relative in links:
            print(f"[SYMLINK] {relative}", file=sys.stderr)
        return 1

    before = snapshot_tree(target)
    managed = state["managed_files"]
    if not isinstance(managed, dict):
        raise SystemExit(f"invalid managed file state: {state_path(target)}")
    update_args = update_command_arguments()
    with tempfile.TemporaryDirectory(prefix="agent-template-kits-update-") as directory:
        candidate = Path(directory) / "target"
        copy_target_for_update(target, candidate)
        commands = all_commands_for(
            selections.installations(profiles),
            candidate,
            update_args,
            bash,
            selections.global_components,
        )
        candidate_result = run_candidate(commands)
        if candidate_result:
            return candidate_result
        candidate_after = snapshot_tree(candidate)

        planned = changed_paths(before, candidate_after)
        conflicts = [
            relative
            for relative in planned
            if (relative in managed and before.get(relative) != managed[relative])
            or (relative not in managed and relative in before)
        ]
        conflict_set = set(conflicts)
        accepted = set(args.accept)
        unknown_accepts = sorted(accepted - conflict_set)

        print(f"\nUpdate preview from template source: {source_version()}")
        if not planned:
            print("[NO CHANGES] Installed template assets already match this source.")
        for relative in planned:
            print(f"[{action_for_path(before, candidate_after, relative)}] {relative}")
        for relative in conflicts:
            print(f"[CONFLICT] {relative}")
        if unknown_accepts:
            for relative in unknown_accepts:
                print(f"[ERROR] --accept names no current conflict: {relative}", file=sys.stderr)
            return 2
        unaccepted = sorted(conflict_set - accepted)
        if unaccepted:
            print("[BLOCKED] Approve each conflict with --accept PATH before applying the update.")
            return 1
        if not args.apply:
            print("[DRY RUN] Add --apply --yes to apply this preview after reviewing it.")
            return 0
        if not confirm_update(target, args.yes):
            print("[CANCELLED] No files were changed.")
            return 0

        backup_planned_files(target, planned)
        actual_commands = all_commands_for(
            selections.installations(profiles),
            target,
            update_args,
            bash,
            selections.global_components,
        )
        for command in actual_commands:
            print(f"[RUN] {format_command(command)}")
            subprocess.run(command, cwd=ROOT, check=True, env=child_env())

        after = snapshot_tree(target)
        mismatches = changed_paths(candidate_after, after)
        if mismatches:
            for relative in mismatches:
                print(f"[ERROR] update result differs from preview: {relative}", file=sys.stderr)
            return 1
        write_install_state(target, selections, before, state)
    print("[OK] Update complete.")
    return 0


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] == "update":
        return update_main(arguments[1:])
    return install_main(arguments)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode) from error
