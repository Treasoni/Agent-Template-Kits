#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  install.sh --target <project-directory> [options]

Install the Agent Platform registry into <project-directory>/<agent-dir>/platform.
Existing differing registry files are preserved unless --force is supplied.

Options:
  --agent-dir <dir>      Agent runtime directory. Default: inferred from the
                         copied skill path, falling back to .codex
  --skills-dir <dir>     Skill discovery directory. Default: shared Codex
                         skills for .codex, otherwise <agent-dir>/skills
  --workflows-dir <dir>  Workflow discovery directory. Default: <agent-dir>/workflows
  --subagents-dir <dir>  Subagent discovery directory. Default: <agent-dir>/agents
  --hooks-dir <dir>      Hook discovery directory. Default: <agent-dir>/hooks
  --hooks-config <file>  Hook registration JSON. Default: runtime-specific
                         settings for Codex and Claude, or <agent-dir>/hooks.json
  --force                Overwrite differing registry files after review
  --validate             Run the installed validator after copying
USAGE
}

TARGET=""
AGENT_DIR=""
SKILLS_DIR=""
WORKFLOWS_DIR=""
SUBAGENTS_DIR=""
HOOKS_DIR=""
HOOKS_CONFIG=""
FORCE=0
VALIDATE=0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(cd "$SCRIPT_DIR/../assets/platform" && pwd)"

detect_agent_dir() {
  case "$SCRIPT_DIR" in
    */.claude/skills/*) printf '%s\n' ".claude" ;;
    */.agent/skills/*) printf '%s\n' ".agent" ;;
    */.codex/skills/*) printf '%s\n' ".codex" ;;
    */.agents/"skills"/*) printf '%s\n' ".codex" ;;
    *) printf '%s\n' ".codex" ;;
  esac
}

require_value() {
  if [ "${2:-}" = "" ]; then
    echo "$1 requires a value" >&2
    usage >&2
    exit 2
  fi
}

trim_trailing_slash() {
  local value="$1"
  while [ "${value%/}" != "$value" ]; do
    value="${value%/}"
  done
  printf '%s' "$value"
}

ensure_project_relative() {
  local label="$1"
  local value="$2"
  case "$value" in
    ""|.|/*|..|../*|*/../*)
      echo "$label must be a project-relative path that does not contain '..': $value" >&2
      exit 2
      ;;
  esac
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target) require_value "$1" "${2:-}"; TARGET="$2"; shift 2 ;;
    --agent-dir) require_value "$1" "${2:-}"; AGENT_DIR="$2"; shift 2 ;;
    --skills-dir) require_value "$1" "${2:-}"; SKILLS_DIR="$2"; shift 2 ;;
    --workflows-dir) require_value "$1" "${2:-}"; WORKFLOWS_DIR="$2"; shift 2 ;;
    --subagents-dir) require_value "$1" "${2:-}"; SUBAGENTS_DIR="$2"; shift 2 ;;
    --hooks-dir) require_value "$1" "${2:-}"; HOOKS_DIR="$2"; shift 2 ;;
    --hooks-config) require_value "$1" "${2:-}"; HOOKS_CONFIG="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    --validate) VALIDATE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [ -z "$TARGET" ]; then
  echo "--target is required" >&2
  usage >&2
  exit 2
fi

if [ -z "$AGENT_DIR" ]; then
  AGENT_DIR="$(detect_agent_dir)"
fi
AGENT_DIR="$(trim_trailing_slash "$AGENT_DIR")"
if [ -z "$SKILLS_DIR" ]; then
  if [ "$AGENT_DIR" = ".codex" ]; then
    SKILLS_DIR=".agents"/skills
  else
    SKILLS_DIR="$AGENT_DIR/skills"
  fi
fi
WORKFLOWS_DIR="${WORKFLOWS_DIR:-$AGENT_DIR/workflows}"
SUBAGENTS_DIR="${SUBAGENTS_DIR:-$AGENT_DIR/agents}"
HOOKS_DIR="${HOOKS_DIR:-$AGENT_DIR/hooks}"
if [ -z "$HOOKS_CONFIG" ]; then
  if [ "$AGENT_DIR" = ".codex" ]; then
    HOOKS_CONFIG="$AGENT_DIR/hooks.json"
  elif [ "$AGENT_DIR" = ".claude" ]; then
    HOOKS_CONFIG=".claude/settings.json"
  else
    HOOKS_CONFIG="$AGENT_DIR/hooks.json"
  fi
fi

for pair in \
  "agent-dir:$AGENT_DIR" \
  "skills-dir:$SKILLS_DIR" \
  "workflows-dir:$WORKFLOWS_DIR" \
  "subagents-dir:$SUBAGENTS_DIR" \
  "hooks-dir:$HOOKS_DIR" \
  "hooks-config:$HOOKS_CONFIG"; do
  ensure_project_relative "${pair%%:*}" "${pair#*:}"
done

TARGET_ROOT="$(cd "$TARGET" && pwd)"
TARGET_DIR="$TARGET_ROOT/$AGENT_DIR/platform"
mkdir -p "$TARGET_DIR"

copy_or_refuse() {
  local source_file="$1"
  local target_file="$2"
  if [ -f "$target_file" ] && ! cmp -s "$source_file" "$target_file" && [ "$FORCE" -ne 1 ]; then
    echo "Refusing to overwrite $target_file; rerun with --force after reviewing it." >&2
    exit 1
  fi
  cp "$source_file" "$target_file"
}

for file in manifest-registry.py manifest.schema.json README.md; do
  copy_or_refuse "$SOURCE_DIR/$file" "$TARGET_DIR/$file"
done

REGISTRY_TMP="$(mktemp)"
trap 'rm -f "$REGISTRY_TMP"' EXIT
cat > "$REGISTRY_TMP" <<EOF
apiVersion: agent-platform/v1
discovery:
  kindDirectories:
    Workflow: $WORKFLOWS_DIR
    Skill: $SKILLS_DIR
    Subagent: $SUBAGENTS_DIR
    Hook: $HOOKS_DIR
policy:
  hooksConfig: $HOOKS_CONFIG
  allowedPermissions:
    filesystem:
      - none
      - read
      - write
    network:
      - none
      - allow
    subprocess:
      - none
      - allow
    git:
      - none
      - read
      - write
  hookEvents:
    - SessionStart
    - Stop
EOF
copy_or_refuse "$REGISTRY_TMP" "$TARGET_DIR/registry.yaml"

chmod +x "$TARGET_DIR/manifest-registry.py"
echo "Installed Agent Platform registry at ${TARGET_DIR#$TARGET_ROOT/}."
if [ "$VALIDATE" -eq 1 ]; then
  python3 "$TARGET_DIR/manifest-registry.py" --root "$TARGET_ROOT" validate
fi
