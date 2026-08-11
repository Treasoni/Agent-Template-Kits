#!/usr/bin/env python3
"""Load and validate the repository's scalar agent-profile contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath


REQUIRED_FIELDS = {
    "name",
    "description",
    "agent_dir",
    "skills_dir",
    "rules_dir",
    "scripts_dir",
    "hooks_dir",
    "entry_file",
    "hook_config",
    "hook_template",
    "include_openai_yaml",
    "env_template",
    "skill_registry",
    "prompt_cache_rule",
}
PATH_FIELDS = {
    "agent_dir",
    "skills_dir",
    "rules_dir",
    "scripts_dir",
    "hooks_dir",
    "entry_file",
    "hook_config",
    "hook_template",
    "skill_registry",
    "prompt_cache_rule",
}


@dataclass(frozen=True)
class ProfileContract:
    name: str
    description: str
    agent_dir: str
    skills_dir: str
    rules_dir: str
    scripts_dir: str
    hooks_dir: str
    entry_file: str
    hook_config: str
    hook_template: str
    include_openai_yaml: bool
    env_template: str
    skill_registry: str
    prompt_cache_rule: str


def parse_flat_yaml(path: Path) -> tuple[dict[str, str], list[str]]:
    values: dict[str, str] = {}
    findings: list[str] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            findings.append(f"{path.name}:{line_number}: expected key: value")
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if not key:
            findings.append(f"{path.name}:{line_number}: empty key")
            continue
        if key in values:
            findings.append(f"{path.name}:{line_number}: duplicate field: {key}")
            continue
        values[key] = value.strip().strip("\"'")
    return values, findings


def is_safe_relative_path(value: str) -> bool:
    if not value or "\\" in value or "\x00" in value:
        return False
    for path in (PurePosixPath(value), PureWindowsPath(value)):
        if path.is_absolute() or path.drive or path.root or ".." in path.parts:
            return False
    return True


def has_prefix(value: str, prefix: str) -> bool:
    value_path = PurePosixPath(value)
    prefix_path = PurePosixPath(prefix)
    return value_path == prefix_path or prefix_path in value_path.parents


def validate_profile(path: Path) -> list[str]:
    values, findings = parse_flat_yaml(path)
    unknown = sorted(set(values) - REQUIRED_FIELDS)
    missing = sorted(field for field in REQUIRED_FIELDS if field not in values)
    findings.extend(f"{path.name}: unknown field: {field}" for field in unknown)
    findings.extend(f"{path.name}: missing field: {field}" for field in missing)
    if missing:
        return findings

    if values["name"] != path.stem:
        findings.append(f"{path.name}: name must match filename: {path.stem}")
    for field in PATH_FIELDS:
        value = values[field]
        if field in {"hooks_dir", "hook_config", "hook_template"} and not value:
            continue
        if not is_safe_relative_path(value):
            findings.append(f"{path.name}: {field} must be a safe relative path")

    agent_dir = values["agent_dir"]
    rules_dir = values["rules_dir"]
    for field in ("scripts_dir", "hooks_dir", "hook_config"):
        value = values[field]
        if value and is_safe_relative_path(value) and not has_prefix(value, agent_dir):
            findings.append(f"{path.name}: {field} must be inside agent_dir")
    for field in ("skill_registry", "prompt_cache_rule"):
        value = values[field]
        if is_safe_relative_path(value) and not has_prefix(value, rules_dir):
            findings.append(f"{path.name}: {field} must be inside rules_dir")

    entry_file = values["entry_file"]
    if is_safe_relative_path(entry_file) and len(PurePosixPath(entry_file).parts) > 1 and not has_prefix(entry_file, agent_dir):
        findings.append(f"{path.name}: entry_file must be at the project root or inside agent_dir")
    if bool(values["hook_config"]) != bool(values["hook_template"]):
        findings.append(f"{path.name}: hook_config and hook_template must both be set or both be empty")
    if values["include_openai_yaml"] not in {"true", "false"}:
        findings.append(f"{path.name}: include_openai_yaml must be true or false")
    if values["env_template"] not in {"codex", "claude"}:
        findings.append(f"{path.name}: env_template must be codex or claude")
    return findings


def validate_profiles(profile_root: Path) -> list[str]:
    findings: list[str] = []
    names: set[str] = set()
    profiles = sorted(profile_root.glob("*.yaml"))
    if not profiles:
        return [f"{profile_root}: no profile files found"]
    for path in profiles:
        findings.extend(validate_profile(path))
        values, _ = parse_flat_yaml(path)
        name = values.get("name")
        if name and name in names:
            findings.append(f"{path.name}: duplicate profile name: {name}")
        elif name:
            names.add(name)
    return findings


def load_profiles(profile_root: Path) -> dict[str, ProfileContract]:
    findings = validate_profiles(profile_root)
    if findings:
        raise ValueError("; ".join(findings))
    profiles: dict[str, ProfileContract] = {}
    for path in sorted(profile_root.glob("*.yaml")):
        values, _ = parse_flat_yaml(path)
        profile = ProfileContract(
            name=values["name"],
            description=values["description"],
            agent_dir=values["agent_dir"],
            skills_dir=values["skills_dir"],
            rules_dir=values["rules_dir"],
            scripts_dir=values["scripts_dir"],
            hooks_dir=values["hooks_dir"],
            entry_file=values["entry_file"],
            hook_config=values["hook_config"],
            hook_template=values["hook_template"],
            include_openai_yaml=values["include_openai_yaml"] == "true",
            env_template=values["env_template"],
            skill_registry=values["skill_registry"],
            prompt_cache_rule=values["prompt_cache_rule"],
        )
        profiles[profile.name] = profile
    return profiles
