from __future__ import annotations

import importlib.util
import json
import platform
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "skills/multi-agent-sync/scripts"
PACKAGE = ROOT / "skills/multi-agent-sync"


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, RUNTIME / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def seed_declared_canonical_assets(root: Path):
    sync = load_module("sync_agents_fixture", "sync_agents.py")
    profiles = sync.load_profiles(root)
    fixtures = {
        "skills": ("fixture/SKILL.md", "# Fixture skill\n"),
        "rules": ("shared.md", "# Shared rule\n"),
        "hooks": ("read_learnings.py", "print('hook-ok')\n"),
        "scripts": ("shared.py", "print('script-ok')\n"),
        "workflows": ("fixture/workflow.md", "# Fixture workflow\n"),
    }
    for scope, (relative_path, content) in fixtures.items():
        source = sync.source_for_scope(profiles, scope)
        asset = root / source["paths"][scope] / relative_path
        asset.parent.mkdir(parents=True, exist_ok=True)
        asset.write_text(content, encoding="utf-8")
        if scope == "rules":
            instruction = root / source["paths"]["instructions"]
            instruction.write_text("# Shared instructions\n", encoding="utf-8")
    return sync, profiles


class MultiAgentSyncTests(unittest.TestCase):
    def test_runtime_skill_registry_manages_multi_agent_sync(self):
        registry = load_module(
            "runtime_skill_sync",
            "../../../scripts/sync-runtime-skills.py",
        )

        self.assertIn(
            (
                Path("skills/multi-agent-sync"),
                Path(".agents/skills/multi-agent-sync"),
            ),
            registry.MIRRORS,
        )

    def test_validator_reports_absolute_path_shell_hook_and_crlf(self):
        validator = load_module("validate_portability", "validate_portability.py")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hook = root / ".codex/hooks/demo.py"
            hook.parent.mkdir(parents=True)
            hook.write_bytes(b"#!/usr/bin/env bash\r\nopen /Users/alice/file\r\n")

            findings = validator.validate_tree(root, "windows")

        self.assertTrue(any("absolute-path" in finding for finding in findings))
        self.assertTrue(any("shell-hook" in finding for finding in findings))
        self.assertTrue(any("crlf" in finding for finding in findings))

    def test_validator_reports_shell_shebang_and_windows_drive_path(self):
        validator = load_module("validate_portability", "validate_portability.py")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hook = root / ".codebuddy/hooks/demo.py"
            hook.parent.mkdir(parents=True)
            hook.write_text("#!/bin/sh\nC:\\Users\\alice\\demo.py\n", encoding="utf-8")

            findings = validator.validate_tree(root, "linux")

        self.assertIn(".codebuddy/hooks/demo.py: absolute-path", findings)
        self.assertIn(".codebuddy/hooks/demo.py: shell-hook", findings)

    def test_validator_reports_powershell_and_pwsh_commands_and_shebangs(self):
        validator = load_module("validate_portability", "validate_portability.py")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            command_hook = root / ".codex/hooks/command.py"
            shebang_hook = root / ".codex/hooks/shebang.py"
            pwsh_command_hook = root / ".codex/hooks/pwsh-command.py"
            pwsh_shebang_hook = root / ".codex/hooks/pwsh-shebang.py"
            command_hook.parent.mkdir(parents=True)
            command_hook.write_text("powershell.exe -File demo.ps1\n", encoding="utf-8")
            shebang_hook.write_text("#!/usr/bin/powershell.exe\n", encoding="utf-8")
            pwsh_command_hook.write_text("pwsh -File demo.ps1\n", encoding="utf-8")
            pwsh_shebang_hook.write_text("#!/usr/bin/pwsh.exe\n", encoding="utf-8")

            findings = validator.validate_tree(root, "windows")

        self.assertIn(".codex/hooks/command.py: shell-hook", findings)
        self.assertIn(".codex/hooks/shebang.py: shell-hook", findings)
        self.assertIn(".codex/hooks/pwsh-command.py: shell-hook", findings)
        self.assertIn(".codex/hooks/pwsh-shebang.py: shell-hook", findings)

    def test_validator_ignores_binary_skill_assets(self):
        validator = load_module("validate_portability_binary", "validate_portability.py")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / ".agents/skills/demo/assets/example.png"
            image.parent.mkdir(parents=True)
            image.write_bytes(
                b"\x89PNG\r\n\x1a\n/Users/alice/project pwsh.exe C:\\Users\\alice"
            )

            findings = validator.validate_tree(root, "windows")

        self.assertEqual(findings, [])

    def test_validator_scans_toml_text_files(self):
        validator = load_module("validate_portability_toml", "validate_portability.py")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / ".codex/rules/shared.toml"
            config.parent.mkdir(parents=True)
            config.write_bytes(b'project = "/Users/alice/project"\r\n')

            findings = validator.validate_tree(root, "linux")

        self.assertEqual(
            findings,
            [
                ".codex/rules/shared.toml: crlf",
                ".codex/rules/shared.toml: absolute-path",
            ],
        )

    def test_validator_reports_invalid_utf8_in_recognized_text(self):
        validator = load_module("validate_portability_encoding", "validate_portability.py")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = root / ".codex/scripts/shared.py"
            script.parent.mkdir(parents=True)
            script.write_bytes(b"print('ok')\n\xff")

            findings = validator.validate_tree(root, "macos")

        self.assertEqual(findings, [".codex/scripts/shared.py: invalid-utf8"])

    def test_validator_accepts_portable_sources_on_all_platforms_and_skips_local_outputs(self):
        validator = load_module("validate_portability", "validate_portability.py")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hook = root / ".codex/hooks/demo.py"
            hook.parent.mkdir(parents=True)
            hook.write_text("#!/usr/bin/env python3\nprint('ok')\n", encoding="utf-8")

            generated_config = root / ".codex/hooks.json"
            generated_config.write_bytes(b'{"command": "C:\\\\Users\\\\alice\\\\python.exe"}\r\n')
            local_state = root / ".agent-sync/local/host.json"
            local_state.parent.mkdir(parents=True)
            local_state.write_bytes(b'{"python": "/Users/alice/python"}\r\n')

            for platform_name in ("windows", "macos", "linux"):
                self.assertEqual(validator.validate_tree(root, platform_name), [])
                checked = subprocess.run(
                    [
                        sys.executable,
                        str(RUNTIME / "validate_portability.py"),
                        "--root",
                        str(root),
                        "--platform",
                        platform_name,
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(checked.returncode, 0, checked.stderr + checked.stdout)
                self.assertIn("[OK]", checked.stdout)

    def test_validator_skips_its_packaged_copies_but_scans_adjacent_shared_files(self):
        validator = load_module("validate_portability_packaged_copies", "validate_portability.py")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packaged_validator = (
                root
                / ".agents/skills/multi-agent-sync/scripts/validate_portability.py"
            )
            adjacent_script = packaged_validator.with_name("shared_check.py")
            installed_validator = root / ".agent-sync/validate_portability.py"
            local_settings = root / ".claude/settings.local.json"
            shared_settings = root / ".claude/settings.shared.json"
            for path in (
                packaged_validator,
                adjacent_script,
                installed_validator,
                local_settings,
                shared_settings,
            ):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("path = '/Users/alice/project'\n", encoding="utf-8")

            findings = validator.validate_tree(root, "macos")

        self.assertEqual(
            findings,
            [
                ".agents/skills/multi-agent-sync/scripts/shared_check.py: absolute-path",
                ".claude/settings.shared.json: absolute-path",
            ],
        )

    def test_validator_cli_returns_one_for_invalid_source_on_each_platform(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hook = root / ".claude/hooks/demo.py"
            hook.parent.mkdir(parents=True)
            hook.write_text("powershell -File demo.ps1\n", encoding="utf-8")

            for platform_name in ("windows", "macos", "linux"):
                checked = subprocess.run(
                    [
                        sys.executable,
                        str(RUNTIME / "validate_portability.py"),
                        "--root",
                        str(root),
                        "--platform",
                        platform_name,
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )

                self.assertEqual(checked.returncode, 1, checked.stderr + checked.stdout)
                self.assertIn(".claude/hooks/demo.py", checked.stdout)
                self.assertIn("shell-hook", checked.stdout)

    def test_bootstrap_renders_current_python_and_preserves_other_settings(self):
        bootstrap = load_module("bootstrap", "bootstrap.py")
        desired = bootstrap.render_hook_template(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": "",
                            "hooks": [
                                {
                                    "command": "{{PYTHON_EXECUTABLE}} {{HOOK_SCRIPT}}",
                                }
                            ],
                        }
                    ]
                }
            },
            python_executable="/opt/python",
            hook_script=".codex/hooks/read_learnings.py",
        )
        current = {
            "theme": "dark",
            "hooks": {
                "SessionStart": [
                    {
                        "matcher": "custom-matcher",
                        "label": "keep wrapper metadata",
                        "hooks": [
                            {"command": "keep custom.py"},
                            {
                                "type": "command",
                                "command": "legacy-interpreter .codex/hooks/read_learnings.py",
                            }
                        ],
                    },
                ],
                "Custom": [{"command": "keep"}],
            },
        }
        merged = bootstrap.merge_managed_hooks(current, desired)

        self.assertEqual(merged["theme"], "dark")
        self.assertEqual(
            merged["hooks"]["SessionStart"][0]["hooks"][1]["command"],
            "/opt/python .codex/hooks/read_learnings.py",
        )
        self.assertEqual(
            merged["hooks"]["SessionStart"][0]["hooks"][0]["command"],
            "keep custom.py",
        )
        self.assertEqual(
            merged["hooks"]["SessionStart"][0]["matcher"],
            "custom-matcher",
        )
        self.assertEqual(
            merged["hooks"]["SessionStart"][0]["label"],
            "keep wrapper metadata",
        )
        self.assertEqual(merged["hooks"]["Custom"], [{"command": "keep"}])
        self.assertEqual(
            current["hooks"]["SessionStart"][0]["hooks"][1]["command"],
            "legacy-interpreter .codex/hooks/read_learnings.py",
        )

    def test_bootstrap_preserves_unrelated_matching_hook_leaf_fields(self):
        bootstrap = load_module("bootstrap_preserve_leaf_fields", "bootstrap.py")
        desired = {
            "hooks": {
                "SessionStart": [
                    {
                        "matcher": "",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "/opt/python .codex/hooks/read_learnings.py",
                            }
                        ],
                    }
                ]
            }
        }
        current = {
            "hooks": {
                "SessionStart": [
                    {
                        "matcher": "",
                        "hooks": [
                            {
                                "type": "command",
                                "command": (
                                    "legacy-interpreter "
                                    ".codex/hooks/read_learnings.py"
                                ),
                                "timeout": 45,
                                "label": "keep me",
                            }
                        ],
                    }
                ]
            }
        }

        merged = bootstrap.merge_managed_hooks(current, desired)
        managed_hook = merged["hooks"]["SessionStart"][0]["hooks"][0]

        self.assertEqual(
            managed_hook,
            {
                "type": "command",
                "command": "/opt/python .codex/hooks/read_learnings.py",
                "timeout": 45,
                "label": "keep me",
            },
        )
        self.assertEqual(
            current["hooks"]["SessionStart"][0]["hooks"][0]["command"],
            "legacy-interpreter .codex/hooks/read_learnings.py",
        )

    def test_installed_bootstrap_applies_then_checks_host_local_hooks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(
                [
                    sys.executable,
                    str(RUNTIME / "install.py"),
                    str(root),
                    "--apply",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            runtime = root / ".agent-sync"
            sync, _ = seed_declared_canonical_assets(root)
            sync.synchronize(root, list(sync.SCOPES), apply=True)
            subprocess.run(
                [
                    sys.executable,
                    str(runtime / "bootstrap.py"),
                    "--root",
                    str(root),
                    "--apply",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            checked = subprocess.run(
                [
                    sys.executable,
                    str(runtime / "bootstrap.py"),
                    "--root",
                    str(root),
                    "--check",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(checked.returncode, 0, checked.stderr + checked.stdout)
            host = json.loads((runtime / "local/host.json").read_text(encoding="utf-8"))
            self.assertEqual(host["platform"], platform.system())
            self.assertEqual(host["python_executable"], sys.executable)
            for config in (
                root / ".codex/hooks.json",
                root / ".claude/settings.json",
                root / ".codebuddy/settings.json",
            ):
                settings = json.loads(config.read_text(encoding="utf-8"))
                command = settings["hooks"]["SessionStart"][0]["hooks"][0]["command"]
                self.assertIn(sys.executable, command)

    def test_bootstrap_rejects_missing_rendered_hook_scripts_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(
                [
                    sys.executable,
                    str(RUNTIME / "install.py"),
                    str(root),
                    "--apply",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            runtime = root / ".agent-sync"

            applied = subprocess.run(
                [
                    sys.executable,
                    str(runtime / "bootstrap.py"),
                    "--root",
                    str(root),
                    "--apply",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(applied.returncode, 2, applied.stderr + applied.stdout)
            self.assertIn("hook script does not exist", applied.stderr)
            self.assertFalse((runtime / "local/host.json").exists())
            self.assertFalse((root / ".codex/hooks.json").exists())
            self.assertFalse((root / ".claude/settings.json").exists())
            self.assertFalse((root / ".codebuddy/settings.json").exists())

    def test_installed_runtime_bootstraps_and_checks_all_scopes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install = RUNTIME / "install.py"
            subprocess.run(
                [sys.executable, str(install), str(root), "--apply"],
                check=True,
                capture_output=True,
                text=True,
            )
            runtime = root / ".agent-sync"
            sync, profiles = seed_declared_canonical_assets(root)
            subprocess.run(
                [
                    sys.executable,
                    str(runtime / "sync_agents.py"),
                    "--root",
                    str(root),
                    "--apply",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(runtime / "sync_agents.py"),
                    "--root",
                    str(root),
                    "--check",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(runtime / "bootstrap.py"),
                    "--root",
                    str(root),
                    "--apply",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            bootstrap_checked = subprocess.run(
                [
                    sys.executable,
                    str(runtime / "bootstrap.py"),
                    "--root",
                    str(root),
                    "--check",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                bootstrap_checked.returncode,
                0,
                bootstrap_checked.stderr + bootstrap_checked.stdout,
            )
            for profile in profiles:
                hook_script = (
                    root
                    / profile["paths"]["hooks"]
                    / "read_learnings.py"
                )
                self.assertTrue(hook_script.is_file(), hook_script)
                config = root / profile["paths"]["hook_config"]
                settings = json.loads(config.read_text(encoding="utf-8"))
                command = settings["hooks"]["SessionStart"][0]["hooks"][0]["command"]
                expected_script = str(
                    PurePosixPath(profile["paths"]["hooks"]) / "read_learnings.py"
                )
                self.assertIn(expected_script, command)
                exercised = subprocess.run(
                    command,
                    cwd=root,
                    shell=True,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(
                    exercised.returncode,
                    0,
                    exercised.stderr + exercised.stdout,
                )
                self.assertIn("hook-ok", exercised.stdout)
            checked = subprocess.run(
                [
                    sys.executable,
                    str(runtime / "validate_portability.py"),
                    "--root",
                    str(root),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(checked.returncode, 0, checked.stderr + checked.stdout)

    def test_built_in_profiles_use_existing_codex_roots_for_all_shared_scopes(self):
        sync = load_module("sync_agents_builtin_ownership", "sync_agents.py")
        profiles = [
            sync.load_profile(path)
            for path in sorted((PACKAGE / "profiles").glob("*.yaml"))
        ]

        for scope in ("skills", "rules", "hooks", "scripts", "workflows"):
            with self.subTest(scope=scope):
                source = sync.source_for_scope(profiles, scope)
                self.assertEqual(source["id"], "codex")
                self.assertTrue((ROOT / source["paths"][scope]).is_dir())

    def test_source_for_scope_uses_scope_override_then_global_default(self):
        sync = load_module("sync_agents", "sync_agents.py")
        codex = {"id": "codex", "canonical": True, "canonical_scopes": "skills,rules"}
        claude = {"id": "claude", "canonical": False, "canonical_scopes": "hooks"}

        self.assertEqual(sync.source_for_scope([codex, claude], "skills")["id"], "codex")
        self.assertEqual(sync.source_for_scope([codex, claude], "hooks")["id"], "claude")
        self.assertEqual(sync.source_for_scope([codex, claude], "rules", "claude")["id"], "claude")

    def test_synchronize_rejects_a_missing_canonical_scope_root(self):
        sync = load_module("sync_agents_missing_root", "sync_agents.py")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(
                [
                    sys.executable,
                    str(RUNTIME / "install.py"),
                    str(root),
                    "--apply",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            with self.assertRaisesRegex(
                ValueError,
                r"canonical hooks root does not exist",
            ):
                sync.synchronize(root, ["hooks"], apply=False)

    def test_profile_paths_must_be_safe_project_relative_posix_paths(self):
        sync = load_module("sync_agents_profile_paths", "sync_agents.py")
        valid_profile = (PACKAGE / "profiles/codex.yaml").read_text(encoding="utf-8")
        invalid_values = {
            "empty": '""',
            "posix-absolute": "/outside/hooks",
            "parent-component": ".codex/../outside",
            "backslash": r".codex\hooks",
            "windows-absolute": "C:/outside/hooks",
        }

        with tempfile.TemporaryDirectory() as directory:
            profile_path = Path(directory) / "codex.yaml"
            for case, invalid_value in invalid_values.items():
                with self.subTest(case=case):
                    profile_path.write_text(
                        valid_profile.replace(
                            "  hooks: .codex/hooks",
                            f"  hooks: {invalid_value}",
                        ),
                        encoding="utf-8",
                    )
                    with self.assertRaisesRegex(ValueError, r"paths\.hooks"):
                        sync.load_profile(profile_path)

    def test_invalid_profile_path_prevents_all_sync_writes(self):
        sync = load_module("sync_agents_profile_write_guard", "sync_agents.py")
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "project"
            root.mkdir()
            subprocess.run(
                [
                    sys.executable,
                    str(RUNTIME / "install.py"),
                    str(root),
                    "--apply",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            for hook_root in (root / ".codex/hooks", root / ".claude/hooks"):
                hook_root.mkdir(parents=True)
                (hook_root / "read_learnings.py").write_text(
                    "print('hook-ok')\n",
                    encoding="utf-8",
                )
            profile_path = root / ".agent-sync/agents/codebuddy.yaml"
            profile_path.write_text(
                profile_path.read_text(encoding="utf-8").replace(
                    "  hooks: .codebuddy/hooks",
                    "  hooks: ../outside-hooks",
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, r"paths\.hooks"):
                sync.synchronize(root, ["hooks"], apply=True)

            self.assertFalse((base / "outside-hooks").exists())

    def test_from_requires_an_explicit_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(
                [
                    sys.executable,
                    str(RUNTIME / "install.py"),
                    str(root),
                    "--apply",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            checked = subprocess.run(
                [
                    sys.executable,
                    str(root / ".agent-sync/sync_agents.py"),
                    "--root",
                    str(root),
                    "--from",
                    "codex",
                    "--check",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(checked.returncode, 2, checked.stderr + checked.stdout)
        self.assertIn("--from requires at least one --scope", checked.stderr)

    def test_hooks_scope_syncs_scripts_without_copying_profile_settings(self):
        sync = load_module("sync_agents", "sync_agents.py")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(
                [
                    sys.executable,
                    str(RUNTIME / "install.py"),
                    str(root),
                    "--apply",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            (root / ".codex/hooks").mkdir(parents=True)
            (root / ".codex/hooks/read_learnings.py").write_text(
                "print('Codex hook')\n",
                encoding="utf-8",
            )
            (root / ".codex/hooks.json").write_text(
                '{"hooks": {"SessionStart": [{"hooks": [{"command": "source"}]}]}}\n',
                encoding="utf-8",
            )
            target_settings = {"theme": "dark", "hooks": {"Custom": [{"command": "keep"}]}}
            for config in (
                root / ".claude/settings.json",
                root / ".codebuddy/settings.json",
            ):
                config.parent.mkdir(parents=True, exist_ok=True)
                config.write_text(
                    json.dumps(target_settings) + "\n",
                    encoding="utf-8",
                )

            sync.synchronize(root, ["hooks"], apply=True)

            self.assertTrue((root / ".claude/hooks/read_learnings.py").is_file())
            self.assertTrue((root / ".codebuddy/hooks/read_learnings.py").is_file())
            self.assertEqual(
                json.loads((root / ".claude/settings.json").read_text(encoding="utf-8")),
                target_settings,
            )
            self.assertEqual(
                json.loads((root / ".codebuddy/settings.json").read_text(encoding="utf-8")),
                target_settings,
            )

    def test_sync_mcp_writes_json_and_codex_toml(self):
        sync = load_module("sync_agents", "sync_agents.py")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".agent-sync").mkdir()
            (root / ".agent-sync/mcp-servers.json").write_text(
                '{"mcpServers": {"demo": {"command": "python", "args": ["server.py"]}}}\n',
                encoding="utf-8",
            )
            profiles = [
                {"id": "codex", "mcp_format": "codex-toml", "paths": {"mcp": ".codex/config.toml"}},
                {"id": "claude", "mcp_format": "project-json", "paths": {"mcp": ".mcp.json"}},
            ]
            sync.sync_mcp(root, profiles, apply=True)
            self.assertIn('[mcp_servers."demo"]', (root / ".codex/config.toml").read_text(encoding="utf-8"))
            self.assertEqual(json.loads((root / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]["demo"]["command"], "python")
