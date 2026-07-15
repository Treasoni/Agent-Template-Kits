# Environment Templates

Environment-variable rules are formal reusable templates. Install the
profile-specific rule and check script into the matching target profile:

| Profile | Rule Template | Check Script |
| --- | --- | --- |
| `codex` | `codex/env.md` | `codex/scripts/check-env-template.sh` |
| `claude` | `claude/env.md` | `claude/scripts/check-env-template.sh` |

The templates explain how an agent should generate, update, and audit
`.env.example` without committing real secrets or machine-local absolute paths.

## Install

Install into a Codex project:

```bash
python3 templates/env/install.py --target /path/to/project --profile codex
```

Install into the portable generic profile:

```bash
python3 templates/env/install.py --target /path/to/project --profile generic
```

Install into a custom agent directory:

```bash
python3 templates/env/install.py --target /path/to/project --custom-agent myagent:.my-agent:INSTRUCTIONS.md
```

For reusable custom layouts or Windows paths containing colons, use a scalar
YAML profile compatible with `profiles/*.yaml`:

```bash
python3 templates/env/install.py --target /path/to/project --profile-file /path/to/myagent.yaml
```

The installer writes:

- `<agent-dir>/rules/common/env.md`
- `<agent-dir>/scripts/check-env-template.sh`
- an idempotent entry block in the profile entry file unless `--no-entry` is used

For a custom agent, copy the closest profile and update only the profile paths
in the examples and ignored directories.
