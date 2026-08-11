#!/usr/bin/env python3
"""Generate local agent runtime skills from canonical and locked sources."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from profile_contract import ProfileContract, load_profiles  # noqa: E402


STATE_VERSION = 1
STATE_PATH = Path(".agent-runtime/skills-state.json")
LOCK_PATH = Path("skills-lock.json")
IGNORED_NAMES = {".DS_Store"}


@dataclass(frozen=True)
class SkillSource:
    name: str
    path: Path
    origin: str


def skill_files(directory: Path, *, include_openai_yaml: bool = True) -> dict[Path, Path]:
    files: dict[Path, Path] = {}
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory)
        if path.is_symlink():
            raise ValueError(f"skill source contains a symlink: {directory.name}/{relative}")
        if not path.is_file() or path.name in IGNORED_NAMES or "__pycache__" in relative.parts:
            continue
        if not include_openai_yaml and relative.parts and relative.parts[0] == "agents":
            continue
        files[relative] = path
    return files


def tree_digest(directory: Path) -> str:
    digest = hashlib.sha256()
    for relative, path in skill_files(directory).items():
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def canonical_skills(source_root: Path) -> dict[str, SkillSource]:
    skills_root = source_root / "skills"
    if not skills_root.is_dir():
        raise ValueError(f"canonical skills directory is missing: {skills_root}")
    sources: dict[str, SkillSource] = {}
    symlinks: list[str] = []
    for path in sorted(skills_root.iterdir()):
        if path.is_symlink():
            symlinks.append(path.name)
            continue
        if not path.is_dir() or not (path / "SKILL.md").is_file():
            continue
        skill_files(path)
        sources[path.name] = SkillSource(path.name, path, "canonical")
    if symlinks:
        raise ValueError(
            "canonical skills must be real self-contained directories; remove runtime symlinks: "
            + ", ".join(symlinks)
        )
    if not sources:
        raise ValueError(f"no canonical skill packages found in {skills_root}")
    return sources


def load_lock(source_root: Path) -> dict[str, object]:
    path = source_root / LOCK_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid external skill lock {path}: {error}") from error
    if not isinstance(data, dict) or data.get("version") != 2:
        raise ValueError(f"{path}: expected lock version 2")
    if not isinstance(data.get("sources"), dict) or not isinstance(data.get("skills"), dict):
        raise ValueError(f"{path}: sources and skills must be objects")
    for name, raw in data["sources"].items():
        if not isinstance(name, str) or not isinstance(raw, dict):
            raise ValueError(f"{path}: invalid source entry")
        required = ("repository", "resolvedCommit", "license", "licenseFile")
        if any(not isinstance(raw.get(key), str) or not raw[key] for key in required):
            raise ValueError(f"{path}: source {name!r} must pin repository, commit, license, and license file")
        commit = raw["resolvedCommit"]
        if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit.lower()):
            raise ValueError(f"{path}: source {name!r} resolvedCommit must be a full Git SHA")
    for name, raw in data["skills"].items():
        if not isinstance(name, str) or not isinstance(raw, dict):
            raise ValueError(f"{path}: invalid skill entry")
        required = ("source", "skillPath", "contentHash")
        if any(not isinstance(raw.get(key), str) or not raw[key] for key in required):
            raise ValueError(f"{path}: skill {name!r} must pin source, path, and content hash")
        if raw["source"] not in data["sources"]:
            raise ValueError(f"{path}: skill {name!r} references unknown source {raw['source']!r}")
        skill_path = PurePosixPath(raw["skillPath"])
        if skill_path.is_absolute() or ".." in skill_path.parts or skill_path.name != "SKILL.md":
            raise ValueError(f"{path}: skill {name!r} has unsafe skillPath")
        content_hash = raw["contentHash"]
        if len(content_hash) != 64 or any(character not in "0123456789abcdef" for character in content_hash.lower()):
            raise ValueError(f"{path}: skill {name!r} contentHash must be SHA-256")
    return data


def safe_extract_zip(payload: bytes, destination: Path) -> Path:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        roots: set[str] = set()
        for member in archive.infolist():
            path = PurePosixPath(member.filename)
            if path.is_absolute() or ".." in path.parts or not path.parts:
                raise ValueError(f"unsafe archive path: {member.filename}")
            roots.add(path.parts[0])
        if len(roots) != 1:
            raise ValueError("external source archive must contain one root directory")
        archive.extractall(destination)
    root = destination / next(iter(roots))
    if not root.is_dir():
        raise ValueError("external source archive root is missing")
    return root


def cached_source(
    source_name: str,
    metadata: dict[str, str],
    cache_root: Path,
    *,
    offline: bool,
) -> Path:
    commit = metadata["resolvedCommit"]
    cache_key = source_name.replace("/", "--")
    cached = cache_root / cache_key / commit / "source"
    if cached.is_dir():
        return cached
    if offline:
        raise ValueError(f"external source is not cached for offline use: {source_name}@{commit}")

    repository = metadata["repository"].removesuffix(".git").rstrip("/")
    url = f"{repository}/archive/{commit}.zip"
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            payload = response.read()
    except (OSError, urllib.error.URLError) as error:
        raise ValueError(f"could not download {source_name}@{commit}: {error}") from error

    cached.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=cached.parent) as directory:
        extracted = safe_extract_zip(payload, Path(directory))
        license_path = extracted / metadata["licenseFile"]
        if not license_path.is_file():
            raise ValueError(f"{source_name}@{commit}: declared license file is missing")
        shutil.copytree(extracted, cached)
    return cached


def external_skills(
    source_root: Path,
    cache_root: Path,
    *,
    offline: bool,
) -> dict[str, SkillSource]:
    lock = load_lock(source_root)
    source_metadata = lock["sources"]
    sources: dict[str, Path] = {}
    results: dict[str, SkillSource] = {}
    for name, raw in sorted(lock["skills"].items()):
        source_name = raw["source"]
        if source_name not in sources:
            sources[source_name] = cached_source(
                source_name,
                source_metadata[source_name],
                cache_root,
                offline=offline,
            )
        skill_directory = sources[source_name] / PurePosixPath(raw["skillPath"]).parent
        if not (skill_directory / "SKILL.md").is_file():
            raise ValueError(f"external skill is missing: {name} ({raw['skillPath']})")
        actual_hash = tree_digest(skill_directory)
        if actual_hash != raw["contentHash"]:
            raise ValueError(
                f"external skill hash mismatch: {name}; expected {raw['contentHash']}, got {actual_hash}"
            )
        results[name] = SkillSource(name, skill_directory, f"external:{source_name}")
    return results


def snapshot(directory: Path, *, include_openai_yaml: bool) -> dict[str, str]:
    if not directory.is_dir() or directory.is_symlink():
        return {}
    return {
        relative.as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for relative, path in skill_files(directory, include_openai_yaml=include_openai_yaml).items()
    }


def source_snapshot(source: SkillSource, *, include_openai_yaml: bool) -> dict[str, str]:
    return snapshot(source.path, include_openai_yaml=include_openai_yaml)


def remove_managed_skill(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def copy_skill(source: SkillSource, target: Path, *, include_openai_yaml: bool) -> None:
    remove_managed_skill(target)
    target.mkdir(parents=True, exist_ok=True)
    for relative, source_path in skill_files(source.path, include_openai_yaml=include_openai_yaml).items():
        target_path = target / relative
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)


def load_state(target_root: Path) -> dict[str, object]:
    path = target_root / STATE_PATH
    if not path.is_file():
        return {"version": STATE_VERSION, "profiles": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid runtime skill state {path}: {error}") from error
    if not isinstance(data, dict) or data.get("version") != STATE_VERSION or not isinstance(data.get("profiles"), dict):
        raise ValueError(f"invalid runtime skill state {path}")
    return data


def write_state(target_root: Path, state: dict[str, object]) -> None:
    path = target_root / STATE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def sync_profile(
    target_root: Path,
    profile: ProfileContract,
    sources: dict[str, SkillSource],
    previous_managed: set[str],
    *,
    apply: bool,
) -> list[str]:
    findings: list[str] = []
    skills_root = target_root / profile.skills_dir
    desired = set(sources)
    for name in sorted(previous_managed - desired):
        target = skills_root / name
        if target.exists() or target.is_symlink():
            findings.append(f"stale managed skill: {profile.name}:{name}")
            if apply:
                remove_managed_skill(target)
    for name, source in sorted(sources.items()):
        target = skills_root / name
        expected = source_snapshot(source, include_openai_yaml=profile.include_openai_yaml)
        actual = snapshot(target, include_openai_yaml=profile.include_openai_yaml)
        if expected == actual and target.is_dir() and not target.is_symlink():
            continue
        action = "updated" if target.exists() or target.is_symlink() else "created"
        findings.append(f"{action}: {profile.name}:{name}")
        if apply:
            copy_skill(source, target, include_openai_yaml=profile.include_openai_yaml)
    return findings


def selected_profiles(
    source_root: Path,
    names: Iterable[str],
) -> list[ProfileContract]:
    profiles = load_profiles(source_root / "profiles")
    selected_names = list(names) or ["codex", "claude"]
    unknown = sorted(set(selected_names) - set(profiles))
    if unknown:
        raise ValueError("unknown profiles: " + ", ".join(unknown))
    return [profiles[name] for name in selected_names]


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--apply", action="store_true", help="generate or refresh managed runtime skills")
    action.add_argument("--check", action="store_true", help="check generated runtime skills without writing")
    action.add_argument("--validate", action="store_true", help="validate canonical and external source contracts only")
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT, help="template source repository")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="runtime target project")
    parser.add_argument("--profile", action="append", help="runtime profile to generate; defaults to codex and claude")
    parser.add_argument("--with-external", action="store_true", help="include skills pinned in skills-lock.json")
    parser.add_argument("--offline", action="store_true", help="require external sources to exist in the local cache")
    parser.add_argument("--cache-dir", type=Path, help="external source cache; defaults under the target project")
    args = parser.parse_args(argv)
    if args.offline and not args.with_external:
        parser.error("--offline requires --with-external")

    source_root = args.source_root.resolve()
    target_root = args.root.resolve()
    cache_root = (args.cache_dir or (target_root / ".agent-runtime/cache")).resolve()
    try:
        sources = canonical_skills(source_root)
        load_lock(source_root)
        if args.with_external:
            external = external_skills(source_root, cache_root, offline=args.offline)
            collisions = sorted(set(sources) & set(external))
            if collisions:
                raise ValueError("external skills collide with canonical packages: " + ", ".join(collisions))
            sources.update(external)
        profiles = selected_profiles(source_root, args.profile or [])
        if args.validate:
            print(
                f"[OK] runtime skill sources are valid: {len(sources)} canonical/selected packages, "
                f"{len(profiles)} profiles"
            )
            return 0

        state = load_state(target_root)
        profile_state = state["profiles"]
        findings: list[str] = []
        for profile in profiles:
            raw_previous = profile_state.get(profile.name, {})
            previous = set(raw_previous.get("managed_skills", [])) if isinstance(raw_previous, dict) else set()
            findings.extend(sync_profile(target_root, profile, sources, previous, apply=args.apply))
            if args.apply:
                profile_state[profile.name] = {"managed_skills": sorted(sources)}
        if args.apply:
            write_state(target_root, state)
    except (OSError, ValueError, urllib.error.URLError, zipfile.BadZipFile) as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 2

    if not findings:
        print("[OK] runtime skill adapters are synchronized")
        return 0
    for finding in findings:
        print(f"[DRIFT] {finding}")
    if args.apply:
        print("[OK] runtime skill adapters refreshed")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
