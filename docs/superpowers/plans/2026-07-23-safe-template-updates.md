# Safe Template Updates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add stateful, conflict-aware updates to the unified template installer.

**Architecture:** Capture file fingerprints after unified installation. For updates, render the next state in a temporary target, classify every changed path against recorded fingerprints, and apply only after explicit approval with backups.

**Tech Stack:** Python 3 standard library, Bash, unittest.

## Global Constraints

- Do not fetch remote code or modify target Git metadata.
- Preserve old `scripts/install.py --target ...` commands.
- Default updates are read-only and conflicts are fail-closed.
- Do not add third-party dependencies.

---

### Task 1: State and update regression tests

**Files:**
- Modify: `tests/test_refactor_regressions.py`

**Interfaces:**
- Consumes: `scripts/install.py` unified installer.
- Produces: assertions for install state, conflict preview, accepted backups, and
  prompt-cache default preservation.

- [x] **Step 1: Write a failing update-state test**

Install the `env` component into a temporary generic target, then assert that
`.agent-template-kits/install-state.json` exists and contains an `env` entry.
Modify the managed env rule and run `scripts/install.py update --target TARGET`.
Assert a non-zero result, a `[CONFLICT]` line, and unchanged target content.

- [x] **Step 2: Run the focused test to verify red**

Run: `python3 -m unittest -v tests.test_refactor_regressions.RefactorRegressionTests.test_unified_installer_update_detects_modified_managed_file`

Expected: fail because the install state and `update` command do not exist.

- [x] **Step 3: Write a failing accepted-update test**

Run the same update with `--accept .agent/rules/common/env.md --apply --yes`.
Assert the rule matches the source again and a timestamped backup exists below
`.agent-template-kits/backups/`.

### Task 2: Implement unified installer state and updater

**Files:**
- Modify: `scripts/install.py`

**Interfaces:**
- Produces: `snapshot_tree`, `source_version`, `write_install_state`, and the
  `update` command.

- [x] **Step 1: Add file fingerprint and state helpers**

Use SHA-256 for regular files. Exclude `.git`, `.agent-template-kits`, and
installer-generated `.bak.<timestamp>` files from snapshots. Record only files
whose hashes changed during installation.

- [x] **Step 2: Record state after successful unified installation**

Take the pre-install snapshot immediately before commands run. After all
commands succeed, merge changed paths with prior state and write JSON atomically
under the target state directory.

- [x] **Step 3: Implement update preview and conflict detection**

Copy the target to a temporary directory, run the planned commands there with
overwrite and force flags, diff the candidate snapshots, and mark paths as
conflicts unless their current hash equals the recorded hash or they are new.

- [x] **Step 4: Implement explicit apply**

Reject unaccepted conflicts. Back up every existing planned target file,
execute the same commands against the real target, compare planned file hashes
with the candidate, then refresh install state.

- [x] **Step 5: Run focused updater tests**

Run: `python3 -m unittest -v tests.test_refactor_regressions.RefactorRegressionTests.test_unified_installer_update_detects_modified_managed_file tests.test_refactor_regressions.RefactorRegressionTests.test_unified_installer_update_accepts_and_backs_up_conflict`

Expected: both pass.

### Task 3: Make prompt-cache updates explicit and document usage

**Files:**
- Modify: `skills/prompt-cache-optimizer/scripts/prompt-cache-bootstrap.sh`
- Modify: `README.md`
- Modify: `tests/test_refactor_regressions.py`

**Interfaces:**
- Produces: `--overwrite` for prompt-cache apply mode and user-facing update
  instructions.

- [x] **Step 1: Preserve the default behavior test**

Install prompt cache into a temporary target, replace its managed rule with
custom text, run the script without `--overwrite`, and assert custom text is
unchanged.

- [x] **Step 2: Add explicit overwrite behavior**

Accept `--overwrite` only with `--apply`. When set, replace existing
prompt-cache rule files, assets, and the installed skill; without it retain the
current keep-existing behavior.

- [x] **Step 3: Document the tag-to-update workflow**

Add a README update example: select a release tag, preview with
`scripts/install.py update --target`, inspect conflicts, then apply with
explicit `--accept PATH` values.

- [x] **Step 4: Run the full validation chain**

Run: `bash scripts/validate.sh && bash skills/security-secret-audit/scripts/audit-secrets.sh && git diff --check`

Expected: all tests pass, secret audit is clean, and no whitespace errors.
