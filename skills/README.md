# Skills

This directory contains reusable skill packages that can be copied into an
agent profile's `skills_dir`.

| Skill | Purpose |
| --- | --- |
| `digest` | Record real task learnings and errors without inventing entries. |
| `maintain-learnings` | Audit recurring learning failures, fix their source, and archive resolved records. |
| `prompt-cache-optimizer` | Audit prompt-cache layout, telemetry, and regression fixtures. |
| `security-secret-audit` | Scan staged files, working trees, or history for exposed secrets and high-confidence project-security risks. |
| `sync-skill-registry` | Generate a skill invocation registry from `*/SKILL.md` metadata. |
| `multi-agent-sync` | Synchronize shared skills and agent configuration across coding-agent profiles. |
| `manifest-platform` | Install and validate portable `manifest.yaml` registries for agent artifacts. |
| `workflow-todo-state` | Add recoverable named workflow state files and phase transitions. |

Each skill directory is self-contained: `SKILL.md`, optional `agents/`
metadata, `scripts/`, `references/`, and assets live with the skill.

This directory is the repository's canonical source. Local runtime directories
such as `.agents/skills/` and `.claude/skills/` are generated after cloning and
are not committed:

```bash
python3 scripts/sync-runtime-skills.py --apply
python3 scripts/sync-runtime-skills.py --apply --with-external
```

The second command adds external packages pinned by repository, full commit,
license, and content hash in `skills-lock.json`.
