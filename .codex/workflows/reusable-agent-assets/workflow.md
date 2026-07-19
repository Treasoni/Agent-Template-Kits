# Reusable Agent Assets Workflow

Use this required workflow when the user wants materials they provide, such as skills, rules, prompts, hooks, scripts, templates, workflow notes, or agent instructions, turned into reusable project assets and placed in the correct repository location.

## Trigger Contract

Route here when the original user request asks to package, clean up, generalize, reuse, install into the project, or place supplied agent knowledge or operational instructions. Chinese trigger forms include "把我提供的 skills/rules 变成可复用", "封装成 skill", "沉淀成规则", "做成模板", "放到合适位置", and close variants.

Do not route here for read-only explanations, ordinary application feature work, installing an already curated skill, or using an existing reusable asset without editing project files.

## State Handling

1. Read `.codex/rules/workflow-routing.md`, this workflow, and the active run state file before every phase.
2. If no matching run exists, create one from `.codex/workflows/reusable-agent-assets/state-template.md` under `workspace/workflow-runs/`.
3. Update phase state only with `.codex/scripts/todo-state.sh`.
4. Name the run after the supplied asset or conversion task, not `todo.md`.

## Placement Rules

Choose the narrowest durable home for each reusable asset:

- `.agents/skills/{skill-id}/` for reusable agent skills with a `SKILL.md`, optional `references/`, `scripts/`, `assets/`, and `agents/openai.yaml`.
- `.codex/rules/{domain}/{rule-id}.md` for reusable project rules. Add only a short bootstrap pointer to `AGENTS.md` when the rule must be loaded before normal task work.
- `.codex/workflows/{workflow-id}/` for recoverable multi-step workflows. Include `workflow.md`, `state-template.md`, and `routing.yaml`, then run `.codex/scripts/sync-workflow-routing.sh`.
- `templates/{domain}/...` for reusable source templates, starter files, snippets, and artifact skeletons.
- `.codex/hooks/` plus `.codex/hooks.json` for runtime hooks. Keep hooks deterministic, safe, and executable when required.
- `.codex/scripts/` for agent-control scripts used by workflows or hooks; `scripts/` for general user-facing project utilities.
- `docs/` for durable prose guidance that is useful to humans but should not be automatically loaded as an agent rule or skill.

Prefer kebab-case IDs, stable filenames, and concise descriptions. Preserve the user's intent while removing one-off paths, secrets, personal tokens, stale examples, and project-specific assumptions that would make reuse unsafe.

## Phases

### P0 Intake And Boundaries

- Read the active state file and the user's original request.
- Inventory every supplied or referenced material path.
- Identify candidate asset types: skill, rule, workflow, template, hook, script, doc, or mixed package.
- Ask a concise question only when ownership, target runtime, or safety is genuinely ambiguous.
- Stop and block if supplied content appears to include secrets, credentials, private keys, or instructions to hide unsafe behavior.

### P1 Classification And Placement Plan

- Map each input item to exactly one primary destination from the placement rules.
- Detect related existing assets with `rg --files` and inspect targets before writing.
- Decide whether to create a new asset or update an existing one.
- Record the intended file list and validation commands in the state file notes or final output section.

### P2 Package And Normalize

- Create or update the target files using existing project style.
- For skills, include YAML frontmatter with `name` and `description`, progressive-disclosure instructions, and references only when useful.
- For rules, keep them short, imperative, and scoped to repeatable behavior.
- For workflows, include unique phase status lines, a state template, routing metadata, and explicit validation steps.
- For scripts and hooks, add minimal comments only where needed and keep behavior deterministic.
- Keep stable instructions before dynamic examples or runtime data to preserve prompt-cache friendliness.

### P3 Integrate Registries

- If a workflow was created or changed, run `.codex/scripts/sync-workflow-routing.sh` and then `.codex/scripts/sync-workflow-routing.sh --check`.
- If a shared skill under `.agents/skills/` was changed, run `python3 .agents/skills/maintain-learnings/scripts/sync_platform_skills.py --root . --skill <skill-id>`.
- If a hook was added or changed, verify `.codex/hooks.json` still points at valid files.
- If a rule needs early loading, update `AGENTS.md` with only the smallest required pointer.

### P4 Verify

- Run syntax checks for changed scripts, such as `bash -n` for shell scripts.
- Validate generated routing or registry files with their project scripts.
- Inspect `git diff --check` and the changed-file diff for accidental churn.
- Confirm no unrelated user changes were reverted.

### P5 Finish And Hand Off

- Complete the state file with final asset paths, validation results, and any skipped or blocked items.
- Tell the user which phrase now triggers the workflow, what was placed where, and how future provided materials will be handled.

## Completion Criteria

The workflow is complete only when reusable assets are in their durable locations, required registries are synchronized, validation passes or failures are reported, and the active run state is complete.
