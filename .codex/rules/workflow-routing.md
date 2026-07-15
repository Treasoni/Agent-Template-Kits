# Workflow Routing

Use this rule file to decide which named workflow to use and where to find active run state.

## Workflow Directory Layout

```text
.codex/workflows/{workflow-id}/workflow.md        # workflow definition
.codex/workflows/{workflow-id}/state-template.md # state file template
workspace/workflow-runs/*.workflow.md                   # active or historical run state
```

## Available Workflows

<!-- workflow-routing:generated:start -->
| Workflow ID | Required | When To Use | Positive Triggers | Excludes | Definition | State File Pattern |
| --- | --- | --- | --- | --- | --- | --- |
| `reusable-agent-assets` | yes | Turning user-provided skills, rules, prompts, hooks, scripts, templates, docs, or workflow notes into reusable agent assets and placing them in the right project location | 把我提供的skills变成可复用; 把一个我提供的skills/rules变成可以被复用; skills rules 等变成可复用; 把rules整理成可复用; 封装成skill; 沉淀成规则; 做成复用模板; 放到合适位置; reusable skill; reusable rules; package agent instructions | read-only explanation; using an existing skill without changing files; installing a curated skill; ordinary app feature work; one-off document writing | `.codex/workflows/reusable-agent-assets/workflow.md` | `workspace/workflow-runs/reusable-agent-assets-{task}.workflow.md` |
<!-- workflow-routing:generated:end -->

## Routing Rules

- Before any action that changes project files, runs project commands, or calls external services, choose the matching `workflow_id` from the table.
- Match the user's original request against positive triggers and exclusions. A matching `Required: yes` workflow cannot use the ordinary execution path.
- If multiple workflows match, choose the more specific workflow; if the route remains ambiguous, ask the user before acting.
- If a matching run already exists under `workspace/workflow-runs/`, resume it instead of creating a duplicate.
- If no run exists, create a named state file from the workflow's `state-template.md`.
- Name state files after the task or feature, not `todo.md`, unless the project has exactly one workflow.
- Every phase must read the active state file before acting.
- Phase state must be changed only through `.codex/scripts/todo-state.sh`.
- Each workflow directory must have a `routing.yaml`; it is the source of truth for the generated table above.
- After creating, changing, renaming, or deleting a workflow, run `.codex/scripts/sync-workflow-routing.sh`. Use `.codex/scripts/sync-workflow-routing.sh --check` in pre-commit or CI.

## Active Runs

| State File | Workflow ID | Task | Current Phase | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| | | | | | |
