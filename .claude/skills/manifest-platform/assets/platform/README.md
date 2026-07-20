# Agent Platform Registry

`manifest.yaml` is the contract for every Workflow, Skill, Subagent, and Hook. The registry discovers manifests from the four configured directories in `registry.yaml`, validates their version, dependencies, and requested permissions, and checks that each Hook is registered in `.claude/hooks.json`.

The registry is declarative: permissions are requests that a runtime policy must enforce; this validator does not grant tools or bypass host approvals.

## Commands

```bash
python3 .codex/platform/manifest-registry.py --root . validate
python3 .codex/platform/manifest-registry.py --root . list
python3 .codex/platform/manifest-registry.py --root . init \
  --kind Skill --name example --entrypoint SKILL.md \
  --description "Describe the new artifact"
```

The default registry discovers Codex workflows, subagents, and hooks alongside shared skills in `.claude/skills`. Adapt `registry.yaml` if the target project uses different directories. Keep each artifact’s `manifest.yaml` inside the directory configured for its kind. During migration, an agent or hook manifest may use a relative entrypoint such as `../outline-generator.md`; entrypoints may never leave the project root.

The validator fails if a conventional `SKILL.md`, `workflow.md`, flat agent `.md`, or flat hook `.sh` in a configured directory has no matching manifest. Bump `metadata.version` using SemVer: MAJOR for an incompatible contract, MINOR for compatible capabilities or dependencies, and PATCH for metadata-only corrections.

The supported YAML subset deliberately uses mappings, block lists, quoted strings, booleans, and empty `[]`/`{}` values. This keeps the validator dependency-free. Use the JSON Schema for editor completion or a fuller YAML toolchain.
