---
name: multi-agent-sync
description: Synchronize shared skills, rules, hooks, scripts, workflows, and MCP configuration across Codex, Claude Code, CodeBuddy, and other coding agents in one project. Use when changing shared agent files, defining agent paths, adding an agent profile, or checking synchronization drift.
---

# Multi-Agent Sync

## Install The Runtime

Install the portable synchronizer before using this skill in another project:

```powershell
py skills/multi-agent-sync/scripts/install.py <target-project> --dry-run
py skills/multi-agent-sync/scripts/install.py <target-project> --apply
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

5. If a `SKILL.md` changed, refresh the skill registry after synchronization:

   ```powershell
   py .agents/skills/sync-skill-registry/scripts/sync_skill_registry.py --profile codex --root .
   py .claude/skills/sync-skill-registry/scripts/sync_skill_registry.py --profile claude --root .
   py .codebuddy/skills/sync-skill-registry/scripts/sync_skill_registry.py --profile codebuddy --root .
   ```

## Safety rules

- Do not edit generated target copies as a source of truth.
- Keep credentials out of `mcp-servers.json`; use environment-variable references.
- Preserve target-only files and non-hook settings. The synchronizer never deletes files and only replaces the `hooks` key in target settings JSON.
- Add a new Agent by creating a simple-mapping YAML profile; see [profile schema](references/profile-schema.md). Do not add a profile until its MCP format is supported by the synchronizer.
