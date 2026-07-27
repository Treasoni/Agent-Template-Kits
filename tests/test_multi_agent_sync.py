from __future__ import annotations

import importlib.util
import json
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
    def test_source_for_scope_uses_scope_override_then_global_default(self):
        sync = load_module("sync_agents", "sync_agents.py")
        codex = {"id": "codex", "canonical": True, "canonical_scopes": "skills,rules"}
        claude = {"id": "claude", "canonical": False, "canonical_scopes": "hooks"}

        self.assertEqual(sync.source_for_scope([codex, claude], "skills")["id"], "codex")
        self.assertEqual(sync.source_for_scope([codex, claude], "hooks")["id"], "claude")
        self.assertEqual(sync.source_for_scope([codex, claude], "rules", "claude")["id"], "claude")

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
