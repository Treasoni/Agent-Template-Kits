#!/usr/bin/env python3
"""Install environment-variable rules into an agent profile."""

from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path


TEMPLATE_ROOT = Path(__file__).resolve().parent
PROFILE_ROOT = TEMPLATE_ROOT.parent.parent / "profiles"
LEGACY_START_MARKER = "<!-- env-template:begin -->"
LEGACY_END_MARKER = "<!-- env-template:end -->"


@dataclass(frozen=True)
class EnvProfile:
    name: str
    agent_dir: str
    skills_dir: str
    rules_dir: str
    scripts_dir: str
    entry_file: str
    template_profile: str

    @property
    def rule_path(self) -> str:
        return f"{self.rules_dir}/common/env.md"

    @property
    def script_path(self) -> str:
        return f"{self.scripts_dir}/check-env-template.sh"


def parse_flat_yaml(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"\'')
    return values


def load_builtin_profiles() -> dict[str, EnvProfile]:
    profiles: dict[str, EnvProfile] = {}
    for path in sorted(PROFILE_ROOT.glob("*.yaml")):
        values = parse_flat_yaml(path)
        name = values.get("name", path.stem)
        rules_dir = Path(values["rules_dir"])
        agent_dir = values.get("agent_dir") or rules_dir.parent.as_posix()
        profiles[name] = EnvProfile(
            name=name,
            agent_dir=agent_dir,
            skills_dir=values.get("skills_dir") or f"{agent_dir}/skills",
            rules_dir=rules_dir.as_posix(),
            scripts_dir=values.get("scripts_dir") or f"{agent_dir}/scripts",
            entry_file=values["entry_file"],
            template_profile=values.get("env_template", name),
        )
    if profiles:
        return profiles
    return {
        "codex": EnvProfile("codex", ".codex", ".agents/skills", ".codex/rules", ".codex/scripts", "AGENTS.md", "codex"),
        "claude": EnvProfile("claude", ".claude", ".claude/skills", ".claude/rules", ".claude/scripts", "CLAUDE.md", "claude"),
        "generic": EnvProfile("generic", ".agent", ".agent/skills", ".agent/rules", ".agent/scripts", "AGENTS.md", "codex"),
    }


BUILTIN_PROFILES = load_builtin_profiles()


def load_profile_file(path: str | Path) -> EnvProfile:
    profile_path = Path(path).resolve()
    values = parse_flat_yaml(profile_path)
    name = values.get("name", profile_path.stem)
    if "rules_dir" not in values:
        raise argparse.ArgumentTypeError(f"profile is missing rules_dir: {profile_path}")
    rules_dir = Path(values["rules_dir"])
    agent_dir = values.get("agent_dir") or rules_dir.parent.as_posix()
    return EnvProfile(
        name=name,
        agent_dir=agent_dir,
        skills_dir=values.get("skills_dir") or f"{agent_dir}/skills",
        rules_dir=rules_dir.as_posix(),
        scripts_dir=values.get("scripts_dir") or f"{agent_dir}/scripts",
        entry_file=values.get("entry_file", "AGENTS.md"),
        template_profile=values.get("env_template", "codex"),
    )


def copy_text(content: str, target: Path, overwrite: bool) -> bool:
    if target.exists() and not overwrite:
        print(f"[SKIP] exists: {target}")
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    print(f"[OK] wrote: {target}")
    return True


def copy_file(source: Path, target: Path, overwrite: bool) -> bool:
    if target.exists() and not overwrite:
        print(f"[SKIP] exists: {target}")
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    print(f"[OK] copied: {target}")
    return True


def transform_for_profile(text: str, profile: EnvProfile) -> str:
    if profile.template_profile == profile.name:
        return text
    source = BUILTIN_PROFILES[profile.template_profile]
    replacements = (
        (source.rule_path, profile.rule_path),
        (source.script_path, profile.script_path),
        (f"{source.agent_dir}/rules", profile.rules_dir),
        (f"{source.agent_dir}/scripts", profile.scripts_dir),
        (f"{source.agent_dir}/skills", profile.skills_dir),
        (f"{source.agent_dir}/agents", f"{profile.agent_dir}/agents"),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def entry_markers(profile: EnvProfile) -> tuple[str, str]:
    return f"<!-- env-template:{profile.name}:begin -->", f"<!-- env-template:{profile.name}:end -->"


def entry_block(profile: EnvProfile) -> str:
    start_marker, end_marker = entry_markers(profile)
    return f"""{start_marker}
## Environment Variables

- Follow `{profile.rule_path}` whenever creating, updating, migrating, or auditing `.env`, `.env.example`, or environment-variable documentation.
- Keep committed env templates minimal, project-specific, and free of real secrets or machine-local absolute paths.
- After env template changes, run `{profile.script_path}`. Use `--strict` when you want unused documented variables to fail the check.
{end_marker}
"""


def update_entry_file(target_root: Path, profile: EnvProfile) -> None:
    entry = target_root / profile.entry_file
    block = entry_block(profile)
    start_marker, end_marker = entry_markers(profile)
    if entry.exists():
        text = entry.read_text(encoding="utf-8")
    else:
        text = "# Project Instructions\n"

    if start_marker in text:
        if end_marker not in text:
            raise SystemExit(f"entry block has no end marker: {entry}")
        before, rest = text.split(start_marker, 1)
        _, after = rest.split(end_marker, 1)
        text = before.rstrip() + "\n\n" + block.rstrip() + "\n" + after
    elif LEGACY_START_MARKER in text and profile.rule_path in text:
        if LEGACY_END_MARKER not in text:
            raise SystemExit(f"legacy entry block has no end marker: {entry}")
        before, rest = text.split(LEGACY_START_MARKER, 1)
        _, after = rest.split(LEGACY_END_MARKER, 1)
        text = before.rstrip() + "\n\n" + block.rstrip() + "\n" + after
    else:
        text = text.rstrip() + "\n\n" + block.rstrip() + "\n"

    entry.write_text(text, encoding="utf-8")
    print(f"[OK] updated: {entry}")


def parse_custom_agent(spec: str) -> EnvProfile:
    parts = spec.split(":")
    if len(parts) < 2:
        raise argparse.ArgumentTypeError("--custom-agent must look like NAME:AGENT_DIR[:ENTRY_FILE]")
    name, agent_dir, *rest = parts
    if not name or not agent_dir:
        raise argparse.ArgumentTypeError("custom agent name and directory are required")
    entry_file = rest[0] if rest and rest[0] else "AGENTS.md"
    agent_dir = agent_dir.rstrip("/")
    return EnvProfile(
        name=name,
        agent_dir=agent_dir,
        skills_dir=f"{agent_dir}/skills",
        rules_dir=f"{agent_dir}/rules",
        scripts_dir=f"{agent_dir}/scripts",
        entry_file=entry_file,
        template_profile="codex",
    )


def selected_profiles(args: argparse.Namespace) -> list[EnvProfile]:
    profiles = [BUILTIN_PROFILES[name] for name in args.profile or []]
    profiles.extend(args.profile_file or [])
    profiles.extend(args.custom_agent or [])
    if not profiles:
        profiles.append(BUILTIN_PROFILES["generic"])
    return profiles


def install_profile(target_root: Path, profile: EnvProfile, overwrite: bool, update_entry: bool) -> None:
    source_root = TEMPLATE_ROOT / profile.template_profile
    env_text = transform_for_profile((source_root / "env.md").read_text(encoding="utf-8"), profile)
    script_text = transform_for_profile(
        (source_root / "scripts" / "check-env-template.sh").read_text(encoding="utf-8"),
        profile,
    )

    print(f"\n== Installing env profile: {profile.name} ==")
    copy_text(env_text, target_root / profile.rule_path, overwrite)
    wrote_script = copy_text(script_text, target_root / profile.script_path, overwrite)
    if wrote_script:
        (target_root / profile.script_path).chmod(0o755)
    if update_entry:
        update_entry_file(target_root, profile)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default=".", help="Target project root.")
    parser.add_argument("--profile", action="append", choices=sorted(BUILTIN_PROFILES), help="Built-in profile to install.")
    parser.add_argument(
        "--profile-file",
        action="append",
        type=load_profile_file,
        metavar="PATH",
        help="Install a scalar YAML profile file. Repeatable and preferred for paths containing colons.",
    )
    parser.add_argument("--custom-agent", action="append", type=parse_custom_agent, metavar="NAME:AGENT_DIR[:ENTRY_FILE]")
    parser.add_argument("--no-entry", action="store_true", help="Do not update the profile entry file.")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing env rule/script files.")
    args = parser.parse_args()

    target_root = Path(args.target).resolve()
    if not target_root.exists():
        parser.error(f"target does not exist: {target_root}")

    for profile in selected_profiles(args):
        install_profile(target_root, profile, overwrite=args.overwrite, update_entry=not args.no_entry)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
