# Agent profile schema

Profiles are plain YAML mappings in `.agent-sync/agents/`. The built-in loader intentionally supports one nested `paths` mapping, so keep profiles in this shape:

```yaml
id: example-agent
name: Example Agent
canonical: false
mcp_format: project-json
paths:
  skills: .example/skills
  rules: .example/rules
  hooks: .example/hooks
  hook_config: .example/settings.json
  scripts: .example/scripts
  workflows: .example/workflows
  instructions: EXAMPLE.md
  mcp: .mcp.json
```

Required fields:

- `id`: unique lowercase identifier used for substitutions.
- `name`: display name used in generated hook text.
- `canonical`: exactly one profile must be `true`.
- `mcp_format`: `project-json` for a shared `mcpServers` JSON file, or `codex-toml` for a managed block in a TOML config.
- `paths`: all eight locations shown above.

Use a distinct project MCP path when the new Agent cannot consume `.mcp.json`. Extending the synchronizer for another MCP format is required before using a new `mcp_format` value.
