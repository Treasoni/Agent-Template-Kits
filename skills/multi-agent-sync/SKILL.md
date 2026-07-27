---
name: multi-agent-sync
description: Synchronize shared skills, rules, hooks, scripts, workflows, and MCP configuration across Codex, Claude Code, CodeBuddy, and other coding agents in one project. Use when changing shared agent files, defining agent paths, adding an agent profile, or checking synchronization drift.
---

# Multi-Agent Sync

## Install The Runtime

Install the portable synchronizer before using this skill in another project. Set
`$skillDir` to the directory containing this skill; do not depend on a
repository-specific `skills/` path.

```powershell
$skillDir = "<path-to-this-skill>"
py "$skillDir/scripts/install.py" <target-project> --dry-run
py "$skillDir/scripts/install.py" <target-project> --apply
```

The installer creates `<target-project>/.agent-sync/` with the synchronizer, the three common profiles, and an empty MCP manifest. It never overwrites a different runtime file unless `--force` is supplied; it never overwrites an existing MCP manifest.

Use `.agent-sync/agents/*.yaml` as the path registry. Read the relevant profile before changing shared Agent files. Exactly one profile must be the canonical source.

## Workflow

1. Select the shared area: `skills`, `rules`, `hooks`, `scripts`, `workflows`, or `mcp`.
2. Edit the canonical location declared in the canonical profile. If the current Agent already changed its own shared location, use `--from <agent-id>` to promote that Agent for this run. For MCP, edit `.agent-sync/mcp-servers.json`.
3. Preview drift:

   ```powershell
   py .agent-sync/sync_agents.py --check --scope <area>
   ```

4. Apply the generated copies, then verify all areas:

   ```powershell
   py .agent-sync/sync_agents.py --apply --scope <area>
   py .agent-sync/sync_agents.py --check
   ```

   For example, after Claude Code changes a shared skill:

   ```powershell
   py .agent-sync/sync_agents.py --apply --from claude --scope skills
   ```

5. If a `SKILL.md` changed, refresh each target project's skill registry using
   that project's own registry command, when it has one.

## Safety rules

- Do not edit generated target copies as a source of truth.
- Keep credentials out of `mcp-servers.json`; use environment-variable references.
- Preserve target-only files and non-hook settings. The synchronizer never deletes files and only replaces the `hooks` key in target settings JSON.
- Add a new Agent by creating a simple-mapping YAML profile; see [profile schema](references/profile-schema.md). Do not add a profile until its MCP format is supported by the synchronizer.

## Cross-platform rationalizations to reject

Fresh-context baseline prompts exposed the following shortcuts. They are
acceptance cases for this skill: do not adopt either shortcut when synchronizing
across operating systems.

| Observed shortcut | Required response |
| --- | --- |
| "convert the Windows-specific paths and PowerShell hook to macOS-compatible equivalents" | Do not exchange one platform-specific path or shell for another. Preserve portable source paths and use the target profile's supported hook format. |
| "run the generated hook through a POSIX shell (Git Bash)" | Do not make a Windows target depend on Git Bash merely to bypass executable-hook support. Generate a hook command Windows can execute directly while leaving canonical source files intact. |

### Baseline evidence

| Fresh-context scenario | Observed response | `python.exe` retained | Absolute path retained | OS-specific shell retained or introduced | Settings silently overwritten |
| --- | --- | --- | --- | --- | --- |
| Copy the Codex SessionStart hook to Claude Code and CodeBuddy | Proposed a shared launcher that tries `python3`, `python`, then `py`. | No | No | No | No |
| Sync Windows Codex skills to macOS Claude Code without questions | Said it would "convert the Windows-specific paths and PowerShell hook to macOS-compatible equivalents." | No | No | Yes — it proposed OS-specific conversion instead of a portable format. | No — it did not propose a settings change. |
| Make a Windows-generated hook run without changing checked-in source | Said it would "run the generated hook through a POSIX shell (Git Bash)." | No | No | Yes — Git Bash. | No |

Keep the portable-launcher goal from the first scenario, but validate the
generated command for every target profile before applying it.
