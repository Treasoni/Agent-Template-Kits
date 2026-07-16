#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

log() {
  printf 'validate: %s\n' "$*"
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'validate: missing required command: %s\n' "$1" >&2
    exit 1
  fi
}

require_command python3
require_command bash

log "python syntax"
python3 -m py_compile \
  scripts/install.py \
  templates/self-learning/install.py \
  templates/self-learning/hooks/read_learnings.py \
  templates/self-learning/skills/maintain-learnings/scripts/sync_platform_skills.py \
  templates/env/install.py \
  skills/sync-skill-registry/scripts/sync_skill_registry.py

log "shell syntax"
bash -n \
  templates/cache/prompt-cache-bootstrap.sh \
  skills/prompt-cache-optimizer/scripts/prompt-cache-bootstrap.sh \
  skills/security-secret-audit/scripts/audit-secrets.sh \
  skills/workflow-todo-state/scripts/install.sh \
  skills/workflow-todo-state/scripts/todo-state.sh \
  skills/workflow-todo-state/scripts/sync-workflow-routing.sh \
  templates/self-learning/hooks/read-learnings.sh \
  templates/env/codex/scripts/check-env-template.sh \
  templates/env/claude/scripts/check-env-template.sh

if command -v perl >/dev/null 2>&1; then
  log "perl syntax"
  perl -c skills/security-secret-audit/scripts/detect-secrets.pl >/dev/null
fi

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/template-ai-validate.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT

log "self-learning generic install"
python3 templates/self-learning/install.py --target "$TMP_DIR" --profile generic --overwrite >/dev/null

log "env generic install"
python3 templates/env/install.py --target "$TMP_DIR" --profile generic --overwrite >/dev/null
test -f "$TMP_DIR/.agent/rules/common/env.md"
test -x "$TMP_DIR/.agent/scripts/check-env-template.sh"

log "prompt-cache generic install"
bash templates/cache/prompt-cache-bootstrap.sh --apply --platform none --agent generic,.agent,AGENTS.md --target "$TMP_DIR" >/dev/null
bash skills/prompt-cache-optimizer/scripts/prompt-cache-bootstrap.sh --apply --platform none --agent generic,.agent,AGENTS.md --with-skill --target "$TMP_DIR" >/dev/null
bash skills/prompt-cache-optimizer/scripts/prompt-cache-bootstrap.sh --check --platform none --agent generic,.agent,AGENTS.md --target "$TMP_DIR" >/dev/null
test -f "$TMP_DIR/.agent/skills/prompt-cache-optimizer/SKILL.md"
test ! -e "$TMP_DIR/.llm"
bash skills/prompt-cache-optimizer/scripts/prompt-cache-bootstrap.sh --apply --platform none --agent generic,.agent,AGENTS.md --with-observability --target "$TMP_DIR" >/dev/null
bash skills/prompt-cache-optimizer/scripts/prompt-cache-bootstrap.sh --check --platform none --agent generic,.agent,AGENTS.md --with-observability --target "$TMP_DIR" >/dev/null
test -f "$TMP_DIR/.llm/prompt-cache/llm-usage-event.schema.json"
test -f "$TMP_DIR/.llm/prompt-cache/regression-cases.json"

log "workflow generic install"
bash skills/workflow-todo-state/scripts/install.sh "$TMP_DIR" --agent-dir .agent --with-skill --init-layout --update-agents --force >/dev/null
mkdir -p "$TMP_DIR/.agent/workflows/demo-flow"
{
  printf '%s\n' 'workflow_id: demo-flow'
  printf '%s\n' 'required: true'
  printf '%s\n' 'when_to_use: "Demo workflow"'
  printf '%s\n' 'triggers: "demo; test"'
  printf '%s\n' 'excludes: "read-only"'
  printf '%s\n' 'state_file_pattern: "workspace/workflow-runs/demo-{task}.workflow.md"'
} > "$TMP_DIR/.agent/workflows/demo-flow/routing.yaml"
printf '%s\n' '# Demo' > "$TMP_DIR/.agent/workflows/demo-flow/workflow.md"
bash "$TMP_DIR/.agent/scripts/sync-workflow-routing.sh" >/dev/null
bash "$TMP_DIR/.agent/scripts/sync-workflow-routing.sh" --check >/dev/null

log "skill registry generic dry-run/apply"
python3 skills/sync-skill-registry/scripts/sync_skill_registry.py --profile generic --root "$TMP_DIR" --create --with-skill --dry-run >/dev/null
test ! -e "$TMP_DIR/.agent/rules/common/skill-invocation.md"
python3 skills/sync-skill-registry/scripts/sync_skill_registry.py --profile generic --root "$TMP_DIR" --create --with-skill >/dev/null
test -f "$TMP_DIR/.agent/skills/sync-skill-registry/SKILL.md"

log "learning hook"
python3 "$TMP_DIR/.agent/hooks/read_learnings.py" --project-root "$TMP_DIR" >/dev/null

log "regression tests"
python3 -m unittest discover -s tests -p 'test_*.py'

log "ok"
