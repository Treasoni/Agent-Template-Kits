---
name: manifest-platform
description: Install, configure, migrate, and validate a portable manifest registry for agent workflows, skills, subagents, and hooks. Use when a project needs manifest.yaml-based discovery, artifact versioning, dependency checks, capability declarations, permission-policy review, or reusable agent-platform setup.
---

# Manifest Platform

Install the bundled registry before creating or migrating manifests:

```bash
bash .agents/skills/manifest-platform/scripts/install.sh --target .
```

Read [the manifest contract](references/manifest-contract.md) before defining a manifest, and read `assets/platform/README.md` before changing the registry layout or its commands.

## Workflow

1. Inspect the project layout and preserve unrelated changes.
2. Install the registry. Review a differing existing registry before using `--force`; never overwrite it by default.
3. Review `.codex/platform/registry.yaml`. Its defaults support Codex workflows, subagents, and hooks plus shared skills in `.agents/skills`; change only the discovery paths that do not match the target project.
4. Add `manifest.yaml` for every artifact in a configured discovery directory. Keep `metadata.name` equal to its containing directory.
5. Declare the narrowest truthful permissions. A manifest requests permissions; enforce them separately through the host runtime’s approval and tool policy.
6. Add dependency IDs only after their target manifests exist. For a Hook, retain the actual registration in `.codex/hooks.json`.
7. Run `python3 .codex/platform/manifest-registry.py --root . validate` and resolve every failure before handoff.

## Reuse

Copy or sync this entire skill folder into another project's skill directory, then run its installer against that project. The installer supplies a dependency-free validator, JSON Schema, registry policy, and reference documentation. Use `manifest-registry.py init` to create an initial manifest before refining its capabilities and permissions.

Do not treat the manifest as a sandbox. It is an auditable declaration, not a permission grant or a bypass of host policy.
