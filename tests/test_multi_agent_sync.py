from __future__ import annotations

import importlib.util
import json
import platform
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "skills/multi-agent-sync/scripts"


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, RUNTIME / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class MultiAgentSyncTests(unittest.TestCase):
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

    def test_source_for_scope_uses_scope_override_then_global_default(self):
        sync = load_module("sync_agents", "sync_agents.py")
        codex = {"id": "codex", "canonical": True, "canonical_scopes": "skills,rules"}
        claude = {"id": "claude", "canonical": False, "canonical_scopes": "hooks"}

        self.assertEqual(sync.source_for_scope([codex, claude], "skills")["id"], "codex")
        self.assertEqual(sync.source_for_scope([codex, claude], "hooks")["id"], "claude")
        self.assertEqual(sync.source_for_scope([codex, claude], "rules", "claude")["id"], "claude")

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
            (root / ".claude/hooks").mkdir(parents=True)
            (root / ".claude/hooks/read_learnings.py").write_text(
                "print('Claude Code hook')\n",
                encoding="utf-8",
            )
            (root / ".claude/settings.json").write_text(
                '{"hooks": {"SessionStart": [{"hooks": [{"command": "source"}]}]}}\n',
                encoding="utf-8",
            )
            target_settings = {"theme": "dark", "hooks": {"Custom": [{"command": "keep"}]}}
            for config in (
                root / ".codex/hooks.json",
                root / ".codebuddy/settings.json",
            ):
                config.parent.mkdir(parents=True, exist_ok=True)
                config.write_text(
                    json.dumps(target_settings) + "\n",
                    encoding="utf-8",
                )

            sync.synchronize(root, ["hooks"], apply=True)

            self.assertTrue((root / ".codex/hooks/read_learnings.py").is_file())
            self.assertTrue((root / ".codebuddy/hooks/read_learnings.py").is_file())
            self.assertEqual(
                json.loads((root / ".codex/hooks.json").read_text(encoding="utf-8")),
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
