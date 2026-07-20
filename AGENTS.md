# Project Instructions

<!-- self-learning:start -->
## Self-Learning

- Before task work, apply `.learnings/RULES.md`, `.learnings/ERRORS.md`, and recent `.learnings/LEARNINGS.md`.
- Codex loads the learning reminder through `.codex/hooks/read_learnings.py`; keep `.codex/hooks.json` pointed at that hook.
- Record real recurring mistakes or reusable lessons in `.learnings/`, but fix the source skill, template, hook, script, or project rule before archiving resolved records.
- Shared Codex skills live under `.agents/skills/`. Keep their distributable source in sync with:

```bash
python3 scripts/sync-runtime-skills.py --check
```

- Cross-profile configuration synchronization belongs to `multi-agent-sync`. When `.agent-sync/` is installed, preview with `python3 .agent-sync/sync_agents.py --check --scope skills` and apply only the affected scope.
<!-- self-learning:end -->

<!-- prompt-cache-bootstrap:begin -->
## Prompt Cache

- Follow `.codex/rules/common/prompt-cache.md` for high-frequency prompt design.
- Keep stable instructions and output formats before dynamic user input, file excerpts, dates, IDs, and runtime state.
- Reuse canonical templates and load long context only when needed.
<!-- prompt-cache-bootstrap:end -->

<!-- workflow-todo-state:start -->
## Workflow Todo State

Named workflow state files are the source of truth for every routed workflow.

- Workflow definitions live under `.codex/workflows/{workflow-id}/`.
- Workflow state files live under `workspace/workflow-runs/` and should be named after the task, for example `payment-refactor.workflow.md`.
- Before any action that changes project files, runs project commands, or calls external services, read `.codex/rules/workflow-routing.md` and match the user's original request against its triggers and exclusions.
- When a `Required: yes` workflow matches, read its `workflow.md`, create or resume its state file, and start the current phase before doing the work. Do not take the ordinary execution path instead.
- If the route is ambiguous, ask the user before acting.
- Read the active workflow state file before starting any phase; do not skip prerequisite phases.
- Change phase state only through `.codex/scripts/todo-state.sh`.
- Use one unique phase status line per phase, for example `> [P0] ⬜ 未开始`.
- On resume after interruption, inspect the YAML frontmatter and current phase before acting.
- Each workflow directory must contain a `routing.yaml`. After creating, changing, renaming, or deleting a workflow, run `.codex/scripts/sync-workflow-routing.sh`; the update is incomplete until `.codex/scripts/sync-workflow-routing.sh --check` passes.
<!-- workflow-todo-state:end -->

<!-- env-template:codex:begin -->
## Environment Variables

- Follow `.codex/rules/common/env.md` whenever creating, updating, migrating, or auditing `.env`, `.env.example`, or environment-variable documentation.
- Keep committed env templates minimal, project-specific, and free of real secrets or machine-local absolute paths.
- After env template changes, run `.codex/scripts/check-env-template.sh`. Use `--strict` when you want unused documented variables to fail the check.
<!-- env-template:codex:end -->
