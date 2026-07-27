---
name: multi-agent-sync
description: Use when synchronizing shared skills, rules, hooks, scripts, workflows, or MCP configuration across coding agents; changing shared agent files; defining agent paths; adding an agent profile; migrating hook settings; or checking synchronization drift.
---

# Multi-Agent Sync

## Required workflow

1. Inspect `.agent-sync/agents/*.yaml` before changing any shared file. Confirm
   the canonical profile and any `canonical_scopes` owner for the area being
   changed.
2. Edit only the canonical source. For MCP, edit
   `.agent-sync/mcp-servers.json`.
3. Preview the affected area with `sync_agents.py --check --scope <area>`.
   A check must run before every apply.
4. Apply that area, then run an all-scope check.
5. After synchronization, run `bootstrap.py --apply` and then
   `bootstrap.py --check`. Bootstrap renders host-local hook settings with the
   current Python interpreter while preserving unrelated settings.
6. Before handoff, run `validate_portability.py` for the target operating
   system. Resolve every finding in tracked source; do not silence the
   validator by adding a platform-specific launcher.

Supported synchronization areas are `skills`, `rules`, `hooks`, `scripts`,
`workflows`, and `mcp`.

## Source and generated targets

The bundled profiles currently declare these owners:

| Area | Canonical source | Generated targets |
| --- | --- | --- |
| `skills`, `rules` | Codex profile paths | Claude Code and CodeBuddy profile paths |
| `hooks` | Claude Code profile path | Codex and CodeBuddy profile paths |
| `scripts`, `workflows` | CodeBuddy profile paths | Codex and Claude Code profile paths |
| `mcp` | `.agent-sync/mcp-servers.json` | Profile-specific MCP files |

Never infer ownership from the currently active agent. A command-line
`--from <agent-id>` override applies only to the requested scope.

## Install and launch

Install the portable runtime before using this skill in another project.
`<skill-dir>` is the directory containing this `SKILL.md`; it need not be
inside the target repository. The installer preserves an existing MCP manifest
and requires `--force` before replacing a different runtime file.

| Platform | Python 3 launch form |
| --- | --- |
| Windows | `py -3 <script> <arguments>` |
| macOS | `python3 <script> <arguments>` |
| Linux | `python3 <script> <arguments>` |

Windows PowerShell:

```powershell
$skillDir = "<skill-dir>"
$project = "<target-project>"
py -3 "$skillDir/scripts/install.py" $project --dry-run
py -3 "$skillDir/scripts/install.py" $project --apply
py -3 "$project/.agent-sync/sync_agents.py" --root $project --check --scope <area>
py -3 "$project/.agent-sync/sync_agents.py" --root $project --apply --scope <area>
py -3 "$project/.agent-sync/sync_agents.py" --root $project --check
py -3 "$project/.agent-sync/bootstrap.py" --root $project --apply
py -3 "$project/.agent-sync/bootstrap.py" --root $project --check
py -3 "$skillDir/scripts/validate_portability.py" --root $project --platform windows
```

macOS or Linux:

```bash
skill_dir="<skill-dir>"
project="<target-project>"
python3 "$skill_dir/scripts/install.py" "$project" --dry-run
python3 "$skill_dir/scripts/install.py" "$project" --apply
python3 "$project/.agent-sync/sync_agents.py" --root "$project" --check --scope <area>
python3 "$project/.agent-sync/sync_agents.py" --root "$project" --apply --scope <area>
python3 "$project/.agent-sync/sync_agents.py" --root "$project" --check
python3 "$project/.agent-sync/bootstrap.py" --root "$project" --apply
python3 "$project/.agent-sync/bootstrap.py" --root "$project" --check
python3 "$skill_dir/scripts/validate_portability.py" --root "$project" --platform macos
```

Use `--platform linux` for a Linux handoff. When promoting an already changed
target for one area, add `--from <agent-id>` to both the scoped check and apply.
If a `SKILL.md` changed, refresh the target project's skill registry with that
project's registry command after synchronization.

## Safety rules

- Do not edit generated target copies as a source of truth.
- Keep credentials out of `mcp-servers.json`; use environment-variable references.
- Preserve target-only files and non-hook settings. Synchronization never
  deletes target files, and bootstrap replaces only the managed Python hook
  command.
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
