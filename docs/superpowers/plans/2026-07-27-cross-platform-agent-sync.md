# Cross-Platform Agent Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the repository's multi-agent synchronization skill portable across Windows, macOS, and Linux while synchronizing Codex, Claude Code, and CodeBuddy safely.

**Architecture:** Keep `skills/multi-agent-sync/` as the canonical distributable package. Its Python-only runtime will select a canonical source by scope, synchronize shared asset trees, and render machine-local hook configuration from tracked templates. A separate validator rejects platform-bound sources; the runtime skill mirror and CI matrix prevent drift.

**Tech Stack:** Python 3 standard library, `unittest`, JSON, scalar YAML profile files, GitHub Actions.

## Global Constraints

- Require Python 3.9 or later; add no third-party dependency.
- Keep canonical asset paths project-relative, UTF-8 encoded, and LF terminated.
- Let `--check` be read-only and return non-zero for drift; reserve writes for `--apply`.
- Preserve non-hook keys and unrelated hook entries in agent configuration files.
- Never commit host interpreter paths, platform-specific generated hook settings, or credentials.
- Use the canonical `skills/multi-agent-sync/` package; `.agents/skills/multi-agent-sync/` is a generated mirror.

---

### Task 1: Establish skill-behavior baseline and acceptance cases

**Files:**
- Modify: `skills/multi-agent-sync/SKILL.md`
- Create: `tests/test_multi_agent_sync.py`

**Interfaces:**
- Consumes: the current `multi-agent-sync` package without cross-platform instructions.
- Produces: three recorded baseline failure modes that become explicit acceptance cases for the updated skill.

- [ ] **Step 1: Run three fresh-context pressure scenarios without the updated skill**

  Dispatch separate agents with these exact user requests, without supplying the proposed implementation:

  ```text
  We need to copy this Codex SessionStart hook to Claude Code and CodeBuddy today. It currently runs python.exe .codex/hooks/read_learnings.py. Make it work everywhere quickly.
  ```

  ```text
  Sync my Windows Codex skills to macOS Claude Code. The source contains C:\\Users\\me and a PowerShell hook. Do not ask me questions; just copy it.
  ```

  ```text
  Our CI passed on macOS but Windows users cannot run the generated hook. Make the check green without changing the checked-in source files.
  ```

- [ ] **Step 2: Record the observed shortcuts before editing the skill**

  Capture whether the responses retain `python.exe`, absolute paths, OS-specific shells, or silently overwrite settings. Use those exact shortcuts in `SKILL.md`'s rationalization table; do not invent failures that did not occur.

- [ ] **Step 3: Add the test module skeleton**

  ```python
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
  ```

- [ ] **Step 4: Run the empty module to establish the test command**

  Run: `python3 -m unittest tests.test_multi_agent_sync -v`

  Expected: PASS with zero tests; subsequent tasks add the failing behavior tests before implementation.

- [ ] **Step 5: Commit the test scaffold and recorded skill evidence**

  ```bash
  git add tests/test_multi_agent_sync.py skills/multi-agent-sync/SKILL.md
  git commit -m "test: define cross-platform sync acceptance cases"
  ```

### Task 2: Select a canonical profile for each synchronized scope

**Files:**
- Modify: `skills/multi-agent-sync/scripts/sync_agents.py`
- Modify: `skills/multi-agent-sync/profiles/codex.yaml`
- Modify: `skills/multi-agent-sync/profiles/claude.yaml`
- Modify: `skills/multi-agent-sync/profiles/codebuddy.yaml`
- Modify: `skills/multi-agent-sync/references/profile-schema.md`
- Modify: `tests/test_multi_agent_sync.py`

**Interfaces:**
- Consumes: `load_profiles(root) -> list[dict[str, Any]]` and `SCOPES` from `sync_agents.py`.
- Produces: `source_for_scope(profiles, scope, source_id=None) -> dict[str, Any]`, used by `synchronize` for every non-MCP scope.

- [ ] **Step 1: Write failing source-selection tests**

  ```python
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
  ```

- [ ] **Step 2: Run the focused test and verify the missing interface fails**

  Run: `python3 -m unittest tests.test_multi_agent_sync.MultiAgentSyncTests.test_source_for_scope_uses_scope_override_then_global_default -v`

  Expected: FAIL with `AttributeError` for `source_for_scope`.

- [ ] **Step 3: Implement the minimal profile contract and selection function**

  ```python
  def scope_values(profile: dict[str, Any]) -> set[str]:
      raw = profile.get("canonical_scopes", "")
      return {item.strip() for item in raw.split(",") if item.strip()}

  def source_for_scope(
      profiles: list[dict[str, Any]], scope: str, source_id: str | None = None
  ) -> dict[str, Any]:
      if source_id is not None:
          match = next((p for p in profiles if p["id"] == source_id), None)
          if match is None:
              raise ValueError(f"unknown --from profile {source_id!r}")
          return match
      explicit = [p for p in profiles if scope in scope_values(p)]
      if len(explicit) == 1:
          return explicit[0]
      if len(explicit) > 1:
          raise ValueError(f"exactly one profile must own canonical scope {scope!r}")
      return next(p for p in profiles if p["canonical"] is True)
  ```

  Validate `canonical_scopes` values against `SCOPES - {"mcp"}` during profile loading. Keep `canonical: true` required so old installed profiles retain their existing behavior.

- [ ] **Step 4: Use the selector inside `synchronize`**

  Compute the source separately inside the scope loop, derive targets from that source, and keep MCP sourced only from `.agent-sync/mcp-servers.json`.

- [ ] **Step 5: Run focused tests, then the existing regression suite**

  Run: `python3 -m unittest tests.test_multi_agent_sync tests.test_refactor_regressions -v`

  Expected: PASS; a source override must affect only its requested scope unless `--from` is supplied, and MCP output remains valid for both native formats.

- [ ] **Step 6: Commit the scope-aware synchronizer**

  ```bash
  git add skills/multi-agent-sync/scripts/sync_agents.py skills/multi-agent-sync/profiles tests/test_multi_agent_sync.py
  git commit -m "feat: select agent sync source by scope"
  ```

### Task 3: Render host-local hook settings from portable templates

**Files:**
- Create: `skills/multi-agent-sync/scripts/bootstrap.py`
- Create: `skills/multi-agent-sync/assets/hook-templates/codex.json`
- Create: `skills/multi-agent-sync/assets/hook-templates/claude.json`
- Create: `skills/multi-agent-sync/assets/hook-templates/codebuddy.json`
- Modify: `skills/multi-agent-sync/scripts/install.py`
- Modify: `skills/multi-agent-sync/scripts/sync_agents.py`
- Modify: `tests/test_multi_agent_sync.py`

**Interfaces:**
- Consumes: `bootstrap.py --root PATH [--apply|--check] [--agent ID]`, profile `paths.hook_config`, and the per-agent JSON hook template.
- Produces: `.agent-sync/local/host.json` and an atomically updated agent hook configuration whose managed hooks reference `sys.executable`.

- [ ] **Step 1: Write failing template-rendering and merge tests**

  ```python
  def test_bootstrap_renders_current_python_and_preserves_other_settings(self):
      bootstrap = load_module("bootstrap", "bootstrap.py")
      desired = bootstrap.render_hook_template(
          {"hooks": {"SessionStart": [{"matcher": "", "hooks": [{"command": "{{PYTHON_EXECUTABLE}} {{HOOK_SCRIPT}}"}]}]}},
          python_executable="/opt/python",
          hook_script=".codex/hooks/read_learnings.py",
      )
      merged = bootstrap.merge_managed_hooks({"theme": "dark", "hooks": {}}, desired)

      self.assertEqual(merged["theme"], "dark")
      self.assertEqual(merged["hooks"]["SessionStart"][0]["hooks"][0]["command"], "/opt/python .codex/hooks/read_learnings.py")
  ```

- [ ] **Step 2: Run the focused test and verify it fails because `bootstrap.py` is absent**

  Run: `python3 -m unittest tests.test_multi_agent_sync.MultiAgentSyncTests.test_bootstrap_renders_current_python_and_preserves_other_settings -v`

  Expected: FAIL with `FileNotFoundError` for `bootstrap.py`.

- [ ] **Step 3: Implement atomic rendering and configuration merge**

  ```python
  def write_json_atomically(path: Path, data: dict[str, Any]) -> None:
      temp = path.with_name(path.name + ".tmp")
      temp.parent.mkdir(parents=True, exist_ok=True)
      temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
      temp.replace(path)
  ```

  `render_hook_template` must replace only `{{PYTHON_EXECUTABLE}}` and `{{HOOK_SCRIPT}}`. `merge_managed_hooks` must replace only a hook whose command contains the template's script path and preserve every other JSON key and hook entry. Record `platform.system()` and `sys.executable` in `.agent-sync/local/host.json`.

- [ ] **Step 4: Stop copying one profile's hook configuration to another**

  Remove `sync_hook_config` from the hooks scope. Continue synchronizing hook scripts through `sync_tree`; let bootstrap create each agent-native configuration from its own template.

- [ ] **Step 5: Distribute templates during install and verify CLI behavior**

  Extend `runtime_files` to copy every `assets/hook-templates/*.json` to `.agent-sync/hook-templates/`. Add a subprocess test that runs bootstrap with `--apply`, then with `--check`, and asserts the second invocation returns zero.

- [ ] **Step 6: Run focused tests**

  Run: `python3 -m unittest tests.test_multi_agent_sync -v`

  Expected: PASS; no test may depend on `python.exe`, `python3`, Bash, or the host PATH.

- [ ] **Step 7: Commit portable hook bootstrap**

  ```bash
  git add skills/multi-agent-sync/scripts skills/multi-agent-sync/assets/hook-templates tests/test_multi_agent_sync.py
  git commit -m "feat: bootstrap local agent hook settings"
  ```

### Task 4: Reject platform-bound shared sources before synchronization

**Files:**
- Create: `skills/multi-agent-sync/scripts/validate_portability.py`
- Modify: `tests/test_multi_agent_sync.py`

**Interfaces:**
- Consumes: `validate_portability.py --root PATH [--platform windows|macos|linux]`.
- Produces: `validate_tree(root: Path, platform_name: str) -> list[str]`; an empty list exits zero and each finding names its relative file and rule.

- [ ] **Step 1: Write failing tests for portable and non-portable assets**

  ```python
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
  ```

- [ ] **Step 2: Run the test and verify the missing validator fails**

  Run: `python3 -m unittest tests.test_multi_agent_sync.MultiAgentSyncTests.test_validator_reports_absolute_path_shell_hook_and_crlf -v`

  Expected: FAIL with `FileNotFoundError` for `validate_portability.py`.

- [ ] **Step 3: Implement the validator using deterministic string rules**

  Scan tracked candidate files beneath agent directories and `.agent-sync`; normalize all paths relative to the supplied root. Emit `absolute-path` for `/Users/`, `/home/`, `C:\\`, or a drive-root pattern; emit `shell-hook` when a shared hook begins with a shell shebang or invokes `zsh`, `bash`, `cmd.exe`, or PowerShell. Reject CRLF in canonical source files. Do not scan `.agent-sync/local/` or generated hook configurations.

- [ ] **Step 4: Add CLI and cross-platform simulation tests**

  Run the validator against the same fixture for `windows`, `macos`, and `linux`; assert the portable fixture passes every mode and that the invalid fixture returns exit status 1.

- [ ] **Step 5: Commit the portability gate**

  ```bash
  git add skills/multi-agent-sync/scripts/validate_portability.py tests/test_multi_agent_sync.py
  git commit -m "feat: validate portable agent assets"
  ```

### Task 5: Package the skill, migrate the repository hook, and refresh runtime mirrors

**Files:**
- Modify: `skills/multi-agent-sync/SKILL.md`
- Modify: `skills/multi-agent-sync/agents/openai.yaml`
- Modify: `skills/multi-agent-sync/references/profile-schema.md`
- Modify: `scripts/sync-runtime-skills.py`
- Create: `.agents/skills/multi-agent-sync/` (generated)
- Modify: `.gitignore`
- Delete: `.codex/hooks.json` (replaced by host-local bootstrap output)
- Modify: `AGENTS.md`
- Modify: `docs/PORTABILITY.md`

**Interfaces:**
- Consumes: the installed `.agent-sync` runtime and a host Python interpreter.
- Produces: a discoverable skill whose documented commands use `py -3` on Windows and `python3` on macOS/Linux, plus a generated Codex runtime mirror.

- [ ] **Step 1: Write failing packaging tests**

  ```python
  def test_runtime_skill_registry_manages_multi_agent_sync(self):
      registry = load_module("runtime_skill_sync", "../../../scripts/sync-runtime-skills.py")
      self.assertIn(
          (Path("skills/multi-agent-sync"), Path(".agents/skills/multi-agent-sync")),
          registry.MIRRORS,
      )
  ```

- [ ] **Step 2: Run the focused test and verify it fails before registry support exists**

  Run: `python3 -m unittest tests.test_multi_agent_sync.MultiAgentSyncTests.test_runtime_skill_registry_manages_multi_agent_sync -v`

  Expected: FAIL with an assertion that the multi-agent-sync mapping is absent.

- [ ] **Step 3: Update the canonical package documentation**

  Keep frontmatter trigger-only and under 500 characters. In the body, require profile inspection, `--check` before `--apply`, bootstrap after sync, and `validate_portability.py` before handoff. Include the exact baseline rationalizations observed in Task 1, a small source-to-target table, and Windows/macOS/Linux launch commands.

- [ ] **Step 4: Migrate the repository's tracked hook configuration safely**

  Move its SessionStart recipe into the Codex hook template, add `.codex/hooks.json`, `.claude/settings.json`, `.codebuddy/settings.json`, and `.agent-sync/local/` to `.gitignore`, and remove only the tracked `.codex/hooks.json`. Run bootstrap with `--apply` to recreate the current machine's ignored configuration before validating the hook. Update the small AGENTS.md hook pointer to require bootstrap after a fresh clone.

- [ ] **Step 5: Add the mirror mapping and generate it**

  Add `(Path("skills/multi-agent-sync"), Path(".agents/skills/multi-agent-sync"))` to `MIRRORS`, then run:

  ```bash
  python3 scripts/sync-runtime-skills.py --apply
  python3 scripts/sync-runtime-skills.py --check
  ```

- [ ] **Step 6: Run package and hook tests**

  Run: `python3 -m unittest tests.test_multi_agent_sync tests.test_refactor_regressions -v`

  Expected: PASS; the recreated hook command contains the current `sys.executable`, while no tracked source contains that absolute interpreter path.

- [ ] **Step 7: Commit the distributable package and migration**

  ```bash
  git rm --cached .codex/hooks.json
  git add skills/multi-agent-sync .agents/skills/multi-agent-sync scripts/sync-runtime-skills.py .gitignore AGENTS.md docs/PORTABILITY.md
  git commit -m "feat: package cross-platform agent sync"
  ```

### Task 6: Enforce the portable runtime in validation and CI

**Files:**
- Modify: `scripts/validate.sh`
- Modify: `.github/workflows/validate.yml`
- Modify: `tests/test_refactor_regressions.py`
- Modify: `tests/test_multi_agent_sync.py`

**Interfaces:**
- Consumes: the packaged runtime, `bootstrap.py`, `sync_agents.py`, and `validate_portability.py`.
- Produces: a CI matrix job that executes all multi-agent synchronization checks with Python on Windows, macOS, and Linux.

- [ ] **Step 1: Write a failing end-to-end temporary-project test**

  ```python
  def test_installed_runtime_bootstraps_and_checks_all_scopes(self):
      with tempfile.TemporaryDirectory() as directory:
          root = Path(directory)
          install = ROOT / "skills/multi-agent-sync/scripts/install.py"
          subprocess.run([sys.executable, str(install), str(root), "--apply"], check=True)
          runtime = root / ".agent-sync"
          source_hook = root / ".codex/hooks/read_learnings.py"
          source_hook.parent.mkdir(parents=True)
          source_hook.write_text("print('ok')\n", encoding="utf-8", newline="\n")
          subprocess.run([sys.executable, str(runtime / "sync_agents.py"), "--root", str(root), "--apply"], check=True)
          subprocess.run([sys.executable, str(runtime / "sync_agents.py"), "--root", str(root), "--check"], check=True)
          subprocess.run([sys.executable, str(runtime / "bootstrap.py"), "--root", str(root), "--apply"], check=True)
          checked = subprocess.run([sys.executable, str(runtime / "validate_portability.py"), "--root", str(root)], check=False)
      self.assertEqual(checked.returncode, 0)
  ```

- [ ] **Step 2: Run the focused test and verify the missing installed bootstrap fails**

  Run: `python3 -m unittest tests.test_multi_agent_sync.MultiAgentSyncTests.test_installed_runtime_bootstraps_and_checks_all_scopes -v`

  Expected: FAIL before the installer copies bootstrap and templates.

- [ ] **Step 3: Add portable validation commands**

  Extend `scripts/validate.sh` to compile the two new Python scripts and run their focused unit tests. In `.github/workflows/validate.yml`, add an `actions/setup-python` step and a separate `shell: pwsh`/`python` step that installs a temporary `.agent-sync` runtime, runs `sync_agents.py --check`, `bootstrap.py --check`, and `validate_portability.py`; retain the existing Bash validation as an independent legacy check.

- [ ] **Step 4: Run the complete local suite**

  Run: `bash scripts/validate.sh`

  Expected: PASS with the runtime mirror synchronized and all unit, profile, hook, and portability checks green.

- [ ] **Step 5: Inspect the final patch and commit CI enforcement**

  ```bash
  git diff --check
  git status --short
  git add scripts/validate.sh .github/workflows/validate.yml tests/test_refactor_regressions.py tests/test_multi_agent_sync.py
  git commit -m "ci: verify agent sync on all platforms"
  ```

## Final Verification

- [ ] Run `python3 scripts/sync-runtime-skills.py --check` and confirm no drift.
- [ ] Run `python3 -m unittest tests.test_multi_agent_sync tests.test_refactor_regressions -v`.
- [ ] Run `bash scripts/validate.sh`.
- [ ] Run `git diff --check` and inspect `git status --short` for only intended changes.
- [ ] Verify the CI job still has `ubuntu-latest`, `macos-latest`, and `windows-latest` in its matrix and uses Python for multi-agent checks.
