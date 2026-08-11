#!/usr/bin/env python3
"""Validate the scalar YAML contracts in profiles/."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from profile_contract import (  # noqa: E402
    is_safe_relative_path,
    load_profiles,
    parse_flat_yaml,
    validate_profile,
    validate_profiles,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile-root",
        default=ROOT / "profiles",
        type=Path,
        help="directory containing built-in profile YAML files",
    )
    args = parser.parse_args()
    findings = validate_profiles(args.profile_root)
    if findings:
        for finding in findings:
            print(f"profiles: {finding}")
        return 1
    print("profiles: contracts are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
