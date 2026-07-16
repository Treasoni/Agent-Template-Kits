from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(*args: str, cwd: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*args],
        cwd=cwd,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class RefactorRegressionTests(unittest.TestCase):
    def test_mainstream_profiles_install_to_their_declared_layouts(self) -> None:
        profiles = {
            "codebuddy": (".codebuddy/skills", ".codebuddy/rules", ".codebuddy/scripts", "CODEBUDDY.md"),
            "cursor": (".cursor/skills", ".cursor/rules", ".cursor/scripts", "AGENTS.md"),
            "gemini": (".gemini/skills", ".gemini/rules", ".gemini/scripts", "GEMINI.md"),
            "github-copilot": (".github/skills", ".github/instructions", ".github/scripts", ".github/copilot-instructions.md"),
            "cline": (".cline/skills", ".clinerules", ".cline/scripts", "AGENTS.md"),
            "roo-code": (".roo/skills", ".roo/rules", ".roo/scripts", "AGENTS.md"),
            "windsurf": (".windsurf/skills", ".windsurf/rules", ".windsurf/scripts", "AGENTS.md"),
            "opencode": (".opencode/skills", ".opencode/rules", ".opencode/scripts", "AGENTS.md"),
            "qwen-code": (".qwen/skills", ".qwen/rules", ".qwen/scripts", "QWEN.md"),
        }

        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for profile, (skills_dir, rules_dir, scripts_dir, entry_file) in profiles.items():
                run(
                    "python3",
                    "templates/self-learning/install.py",
                    "--target",
                    str(target),
                    "--profile",
                    profile,
                    "--no-hooks",
                )
                run(
                    "python3",
                    "templates/env/install.py",
                    "--target",
                    str(target),
                    "--profile",
                    profile,
                    "--overwrite",
                )
                self.assertTrue((target / skills_dir / "digest" / "SKILL.md").is_file())
                self.assertTrue((target / rules_dir / "common" / "env.md").is_file())
                self.assertTrue((target / scripts_dir / "check-env-template.sh").is_file())
                self.assertTrue((target / entry_file).is_file())

    def test_unified_installer_detects_and_installs_codebuddy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / ".codebuddy").mkdir()
            (target / "CODEBUDDY.md").write_text("# CodeBuddy\n", encoding="utf-8")

            detection = run(
                "python3",
                "scripts/install.py",
                "--target",
                str(target),
                "--detect",
            )
            self.assertIn("codebuddy", detection.stdout)
            self.assertIn(".codebuddy", detection.stdout)

            preview = run(
                "python3",
                "scripts/install.py",
                "--target",
                str(target),
                "--profile",
                "codebuddy",
                "--components",
                "self-learning,env",
            )
            self.assertIn("[DRY RUN]", preview.stdout)
            self.assertFalse((target / ".learnings").exists())

            run(
                "python3",
                "scripts/install.py",
                "--target",
                str(target),
                "--use-detected",
                "--apply",
                "--yes",
            )
            self.assertTrue((target / ".codebuddy/skills/digest/SKILL.md").is_file())
            self.assertTrue((target / ".codebuddy/rules/common/env.md").is_file())
            self.assertTrue((target / ".codebuddy/rules/common/prompt-cache.md").is_file())
            self.assertTrue((target / ".codebuddy/scripts/todo-state.sh").is_file())
            self.assertTrue((target / ".codebuddy/rules/workflow-routing.md").is_file())
            self.assertTrue((target / ".codebuddy/rules/common/skill-invocation.md").is_file())
            settings = json.loads((target / ".codebuddy/settings.json").read_text(encoding="utf-8"))
            commands = [
                hook["command"]
                for entry in settings["hooks"]["SessionStart"]
                for hook in entry["hooks"]
            ]
            self.assertIn("python3 '.codebuddy/hooks/read_learnings.py'", commands)

    def test_mainstream_profiles_are_available_to_registry_and_shell_installers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            run(
                "python3",
                "templates/self-learning/install.py",
                "--target",
                str(target),
                "--profile",
                "github-copilot",
                "--no-hooks",
            )
            run(
                "python3",
                "skills/sync-skill-registry/scripts/sync_skill_registry.py",
                "--profile",
                "github-copilot",
                "--root",
                str(target),
                "--create",
            )
            self.assertTrue((target / ".github/instructions/common/skill-invocation.md").is_file())

            run(
                "bash",
                "templates/cache/prompt-cache-bootstrap.sh",
                "--apply",
                "--platform",
                "github-copilot",
                "--target",
                str(target),
            )
            self.assertTrue((target / ".github/instructions/common/prompt-cache.md").is_file())

            run(
                "bash",
                "skills/workflow-todo-state/scripts/install.sh",
                str(target),
                "--profile",
                "cline",
                "--with-skill",
                "--init-layout",
                "--update-agents",
            )
            self.assertTrue((target / ".cline/skills/workflow-todo-state/SKILL.md").is_file())
            self.assertTrue((target / ".clinerules/workflow-routing.md").is_file())
            self.assertTrue((target / ".cline/scripts/sync-workflow-routing.sh").is_file())

    def test_self_learning_overwrite_preserves_records_and_custom_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / ".learnings").mkdir()
            learning = target / ".learnings/LEARNINGS.md"
            learning.write_text("# User learning\n\nvaluable record\n", encoding="utf-8")
            config = target / ".codex/hooks.json"
            config.parent.mkdir()
            config.write_text(
                json.dumps(
                    {
                        "custom": {"keep": True},
                        "hooks": {
                            "SessionStart": [
                                {
                                    "matcher": "",
                                    "hooks": [{"type": "command", "command": "keep-me"}],
                                }
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )

            run(
                "python3",
                "templates/self-learning/install.py",
                "--target",
                str(target),
                "--profile",
                "codex",
                "--overwrite",
            )

            self.assertIn("valuable record", learning.read_text(encoding="utf-8"))
            merged = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(merged["custom"], {"keep": True})
            commands = [
                hook["command"]
                for entry in merged["hooks"]["SessionStart"]
                for hook in entry["hooks"]
            ]
            self.assertIn("keep-me", commands)
            self.assertIn("python3 '.codex/hooks/read_learnings.py'", commands)
            self.assertNotIn(str(target), config.read_text(encoding="utf-8"))

    def test_env_profiles_can_share_one_entry_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            run(
                "python3",
                "templates/env/install.py",
                "--target",
                str(target),
                "--profile",
                "codex",
                "--profile",
                "generic",
                "--overwrite",
            )
            entry = (target / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("<!-- env-template:codex:begin -->", entry)
            self.assertIn("<!-- env-template:generic:begin -->", entry)
            self.assertIn(".codex/rules/common/env.md", entry)
            self.assertIn(".agent/rules/common/env.md", entry)

    def test_self_learning_accepts_a_profile_file_without_adding_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            profile = target / "custom.yaml"
            profile.write_text(
                "name: custom\n"
                "skills_dir: .custom/skills\n"
                "hooks_dir: .custom/hooks\n"
                "entry_file: INSTRUCTIONS.md\n",
                encoding="utf-8",
            )
            run(
                "python3",
                "templates/self-learning/install.py",
                "--target",
                str(target),
                "--profile-file",
                str(profile),
            )
            self.assertTrue((target / ".custom/skills/digest/SKILL.md").is_file())
            self.assertFalse((target / ".agents").exists())
            self.assertFalse((target / ".claude").exists())

    def test_template_installers_keep_standalone_profile_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sandbox = Path(directory)
            self_learning = sandbox / "self-learning"
            env_template = sandbox / "env"
            shutil.copytree(ROOT / "templates/self-learning", self_learning)
            shutil.copytree(ROOT / "templates/env", env_template)
            target = sandbox / "target"
            target.mkdir()

            run(
                "python3",
                str(self_learning / "install.py"),
                "--target",
                str(target),
                "--profile",
                "generic",
            )
            run(
                "python3",
                str(env_template / "install.py"),
                "--target",
                str(target),
                "--profile",
                "generic",
            )
            self.assertTrue((target / ".agent/skills/digest/SKILL.md").is_file())
            self.assertTrue((target / ".agent/rules/common/env.md").is_file())

    def test_workflow_install_is_idempotent_after_rendering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            command = (
                "bash",
                "skills/workflow-todo-state/scripts/install.sh",
                directory,
                "--profile",
                "generic",
                "--with-skill",
                "--init-layout",
                "--update-agents",
            )
            run(*command)
            run(*command)

    def test_workflow_codex_profile_separates_skills_and_rules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run(
                "bash",
                "skills/workflow-todo-state/scripts/install.sh",
                directory,
                "--profile",
                "codex",
                "--with-skill",
                "--init-layout",
                "--update-agents",
            )
            target = Path(directory)
            self.assertTrue((target / ".agents/skills/workflow-todo-state/SKILL.md").is_file())
            self.assertTrue((target / ".codex/rules/workflow-routing.md").is_file())
            self.assertFalse((target / ".codex/skills").exists())

    def test_completed_workflow_phase_is_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "state.md"
            shutil.copy2(
                ROOT / "skills/workflow-todo-state/references/basic-state-template.md",
                state,
            )
            script = "skills/workflow-todo-state/scripts/todo-state.sh"
            run("bash", script, str(state), "start", "P0")
            run("bash", script, str(state), "complete", "P0")
            result = run("bash", script, str(state), "block", "P0", "late", check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot block completed", result.stderr)
            self.assertIn("> [P0] ✅ 已完成", state.read_text(encoding="utf-8"))

    def test_registry_removes_only_previously_managed_skills(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            skills = target / ".agent/skills/demo"
            skills.mkdir(parents=True)
            (skills / "SKILL.md").write_text(
                "---\nname: demo\ndescription: Demo skill\ncategory: Tools\n---\n# Demo\n",
                encoding="utf-8",
            )
            registry = target / ".agent/rules/common/skill-invocation.md"
            registry.parent.mkdir(parents=True)
            registry.write_text(
                "# Skill Invocation\n\n"
                "## 技能列表\n\n"
                "#### External\n\n"
                "| 技能 | 触发场景 | 关键触发词 |\n"
                "|---|---|---|\n"
                "| `external` | Manual | manual |\n\n"
                "### 1. 分析意图\n\nKeep.\n",
                encoding="utf-8",
            )
            command = (
                "python3",
                "skills/sync-skill-registry/scripts/sync_skill_registry.py",
                "--profile",
                "generic",
                "--root",
                str(target),
            )
            run(*command)
            (skills / "SKILL.md").unlink()
            run(*command)

            text = registry.read_text(encoding="utf-8")
            self.assertNotIn("`demo`", text)
            self.assertIn("`external`", text)
            self.assertIn("<!-- skill-registry:managed [] -->", text)


if __name__ == "__main__":
    unittest.main()
