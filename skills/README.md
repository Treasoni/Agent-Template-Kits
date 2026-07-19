# Skills

This directory contains reusable skill packages that can be copied into an
agent profile's `skills_dir`.

| Skill | Purpose |
| --- | --- |
| `prompt-cache-optimizer` | Audit prompt-cache layout, telemetry, and regression fixtures. |
| `security-secret-audit` | Scan staged files, working trees, or history for exposed secrets. |
| `sync-skill-registry` | Generate a skill invocation registry from `*/SKILL.md` metadata. |
| `multi-agent-sync` | Synchronize shared skills and agent configuration across coding-agent profiles. |
| `workflow-todo-state` | Add recoverable named workflow state files and phase transitions. |

Each skill directory is self-contained: `SKILL.md`, optional `agents/`
metadata, `scripts/`, `references/`, and assets live with the skill.
