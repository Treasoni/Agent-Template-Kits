# Quality and Governance Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make public release governance, documentation coverage, profile contracts, and quality guards verifiable without changing installer behavior.

**Architecture:** Add a small, standalone profile validator rather than sharing parser code across portable installers. Make the existing documentation guard derive component identifiers from the unified installer. Add focused quality-guard tests, then include the validator in the existing full validation script.

**Tech Stack:** Python 3 standard library, Bash, Perl, unittest, GitHub Actions.

## Global Constraints

- Preserve all existing profile field names and installer command-line interfaces.
- Do not add runtime dependencies beyond Python 3, Bash, and Perl.
- Tests must not print simulated credential values.
- Keep `.env.example` restricted to actual environment inputs.

---

### Task 1: Publish governance assets

**Files:**
- Create: `LICENSE`
- Create: `RELEASING.md`
- Modify: `README.md`

**Interfaces:**
- Produces: an authoritative MIT license and a documented `vX.Y.Z` release procedure.

- [ ] **Step 1: Add the MIT license text**

Create `LICENSE` with the standard MIT grant, copyright holder `Treasoni`, and
year `2026`.

- [ ] **Step 2: Add a release procedure**

Create `RELEASING.md` with these ordered requirements:

```markdown
1. Update CHANGELOG.md under an explicit version heading.
2. Run bash scripts/validate.sh and the working-tree secret audit.
3. Commit the release changes.
4. Create an annotated vX.Y.Z tag.
5. Push the commit and tag, then publish the release notes.
```

- [ ] **Step 3: Link governance documents from the README**

Add `LICENSE` and `RELEASING.md` to the README's further-reading section.

- [ ] **Step 4: Verify the public assets exist**

Run: `test -f LICENSE && test -f RELEASING.md && rg -n 'LICENSE|RELEASING' README.md`

Expected: exit status 0.

### Task 2: Make documentation coverage data-driven

**Files:**
- Modify: `scripts/check-docs.py`
- Create: `tests/test_quality_guards.py`

**Interfaces:**
- Consumes: `scripts.install.COMPONENTS`.
- Produces: `component_names()` and a `check_documents(documents, components)`
  function that returns human-readable findings.

- [ ] **Step 1: Write failing documentation-guard tests**

Add tests that assert the real public documents pass and that a temporary
document missing `manifest-platform` produces a finding containing both the
filename and component name.

- [ ] **Step 2: Run the focused test to verify red**

Run: `python3 -m unittest -v tests.test_quality_guards.QualityGuardTests.test_document_guard_reports_missing_component`

Expected: failure because `check_documents` does not yet exist.

- [ ] **Step 3: Implement the minimal documentation guard**

Load `scripts/install.py` with `importlib.util.spec_from_file_location`, use
its `COMPONENTS` tuple, and test every component against README and the
detailed Markdown guide. Remove the unreferenced static HTML duplicate. Keep
CLI output in the existing `docs: ...` format.

- [ ] **Step 4: Run focused tests**

Run: `python3 -m unittest -v tests.test_quality_guards.QualityGuardTests.test_document_guard_reports_missing_component tests.test_quality_guards.QualityGuardTests.test_public_documents_cover_all_components`

Expected: both pass.

### Task 3: Add a profile contract validator

**Files:**
- Create: `scripts/validate-profiles.py`
- Modify: `scripts/validate.sh`
- Modify: `tests/test_quality_guards.py`

**Interfaces:**
- Consumes: scalar `profiles/*.yaml` files.
- Produces: `validate_profiles(profile_root: Path) -> list[str]`; command exits
  0 for valid contracts and 1 with one `profiles: ...` line per finding.

- [ ] **Step 1: Write failing profile-validation tests**

Add one test that validates the repository profiles and one test that writes a
temporary profile with `name: other` and verifies the filename/name mismatch
is reported.

- [ ] **Step 2: Run the focused test to verify red**

Run: `python3 -m unittest -v tests.test_quality_guards.QualityGuardTests.test_profile_validator_rejects_filename_name_mismatch`

Expected: failure because `scripts/validate-profiles.py` does not yet exist.

- [ ] **Step 3: Implement the minimal validator**

Accept exactly these fields:

```python
{
    'name', 'description', 'agent_dir', 'skills_dir', 'rules_dir',
    'scripts_dir', 'hooks_dir', 'entry_file', 'hook_config',
    'hook_template', 'include_openai_yaml', 'env_template',
    'skill_registry', 'prompt_cache_rule',
}
```

Require `name`, `description`, `agent_dir`, `skills_dir`, `rules_dir`,
`scripts_dir`, `hooks_dir`, `entry_file`, `hook_config`, `hook_template`,
`include_openai_yaml`, `env_template`, `skill_registry`, and
`prompt_cache_rule`. Require every non-empty path to be relative, free of
`..` in either POSIX or Windows path syntax. Require `scripts_dir`, non-empty `hooks_dir`, and non-empty `hook_config`
to start with `agent_dir`; require `skill_registry` and `prompt_cache_rule` to
start with `rules_dir`; and require `entry_file` to be at the project root or
start with `agent_dir`. Do not constrain `rules_dir` or `skills_dir` to
`agent_dir`, because Cline deliberately uses `.clinerules` and Codex uses
`.agents/skills`. Require
`hook_config` to be empty iff `hook_template` is empty. Limit
`include_openai_yaml` to `true` or `false`, and `env_template` to `codex` or
`claude`.

- [ ] **Step 4: Integrate with the full validator**

Add `scripts/validate-profiles.py` to `py_compile` and run it after Python
syntax checks in `scripts/validate.sh`.

- [ ] **Step 5: Run focused tests**

Run: `python3 -m unittest -v tests.test_quality_guards`

Expected: all quality-guard tests pass.

### Task 4: Cover the secret detector and validate the full change

**Files:**
- Modify: `tests/test_quality_guards.py`
- Modify: `.env.example`

**Interfaces:**
- Produces: redacted secret-detector regression coverage and an environment
  template containing only four actual environment inputs.

- [ ] **Step 1: Write a secret-detector regression test**

Create a temporary configuration file containing a synthetic OpenAI-style key
assembled from a safe prefix and repeated characters. Invoke
`detect-secrets.pl` and assert exit code 2, `openai-style-api-key` in stdout,
and that the assembled token is absent from stdout and stderr.

- [ ] **Step 2: Run the focused test to verify red**

Run: `python3 -m unittest -v tests.test_quality_guards.QualityGuardTests.test_secret_detector_redacts_values`

Expected: failure before the test is added.

- [ ] **Step 3: Keep only actual environment inputs**

Ensure `.env.example` contains exactly `PYTHON`, `PROMPT_CACHE_ASSET_DIR`,
`PROMPT_CACHE_PROFILE_ROOT`, and `WORKFLOW_PROFILE_ROOT`; do not document
shell-local paths.

- [ ] **Step 4: Verify full integration**

Run: `bash scripts/validate.sh`

Expected: exit status 0 and all unit tests pass.

- [ ] **Step 5: Verify the release safety boundary**

Run: `bash skills/security-secret-audit/scripts/audit-secrets.sh && git diff --check`

Expected: exit status 0 with no credential finding and no whitespace errors.
