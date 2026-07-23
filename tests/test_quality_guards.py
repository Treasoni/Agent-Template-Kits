from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE_VALUES = {
    "name": "codex",
    "description": "Test profile.",
    "agent_dir": ".codex",
    "skills_dir": ".agents/skills",
    "rules_dir": ".codex/rules",
    "scripts_dir": ".codex/scripts",
    "hooks_dir": ".codex/hooks",
    "entry_file": "AGENTS.md",
    "hook_config": ".codex/hooks.json",
    "hook_template": "codex-hooks.json.template",
    "include_openai_yaml": "true",
    "env_template": "codex",
    "skill_registry": ".codex/rules/common/skill-invocation.md",
    "prompt_cache_rule": ".codex/rules/common/prompt-cache.md",
}


def load_script(module_name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(module_name, ROOT / relative_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def profile_text(**overrides: str) -> str:
    values = {**PROFILE_VALUES, **overrides}
    return "\n".join(f"{key}: {value}" for key, value in values.items()) + "\n"


class QualityGuardTests(unittest.TestCase):
    def test_public_documents_cover_all_installer_components(self) -> None:
        checker = load_script("check_docs", "scripts/check-docs.py")

        self.assertEqual(checker.check_documents(checker.DOCUMENTS, checker.component_names()), [])

    def test_document_guard_reports_missing_component(self) -> None:
        checker = load_script("check_docs", "scripts/check-docs.py")
        with tempfile.TemporaryDirectory() as directory:
            document = Path(directory) / "guide.md"
            document.write_text("self-learning\n", encoding="utf-8")

            findings = checker.check_documents((document,), ("self-learning", "manifest-platform"))

        self.assertEqual(findings, ["guide.md does not mention manifest-platform"])

    def test_repository_profiles_match_the_contract(self) -> None:
        validator = load_script("validate_profiles", "scripts/validate-profiles.py")

        self.assertEqual(validator.validate_profiles(ROOT / "profiles"), [])

    def test_profile_validator_rejects_filename_name_mismatch(self) -> None:
        validator = load_script("validate_profiles", "scripts/validate-profiles.py")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "codex.yaml"
            path.write_text(profile_text(name="other"), encoding="utf-8")

            findings = validator.validate_profiles(Path(directory))

        self.assertIn("codex.yaml: name must match filename: codex", findings)

    def test_profile_validator_rejects_windows_style_unsafe_paths(self) -> None:
        validator = load_script("validate_profiles", "scripts/validate-profiles.py")
        for unsafe_path in (r"..\escape", r"C:\escape", r"\rooted"):
            with self.subTest(unsafe_path=unsafe_path), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "codex.yaml"
                path.write_text(profile_text(skills_dir=unsafe_path), encoding="utf-8")

                findings = validator.validate_profiles(Path(directory))

            self.assertIn("codex.yaml: skills_dir must be a safe relative path", findings)

    def test_secret_detector_redacts_values(self) -> None:
        detector = ROOT / "skills/security-secret-audit/scripts/detect-secrets.pl"
        synthetic_key = "sk-" + "a" * 20
        secret_name = "_".join(("OPENAI", "API", "KEY"))
        result = subprocess.run(
            ["perl", str(detector), "--label", "fixture.env", "--path", "fixture.env"],
            input=f"{secret_name}={synthetic_key}\n",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("fixture.env:1:openai-style-api-key", result.stdout)
        self.assertFalse(synthetic_key in result.stdout)
        self.assertFalse(synthetic_key in result.stderr)


if __name__ == "__main__":
    unittest.main()
