# Agent Profiles

Profiles describe how reusable templates map into a target agent project.

| Profile | Skills | Rules | Hooks | Entry |
| --- | --- | --- | --- | --- |
| `codex` | `.agents/skills` | `.codex/rules` | `.codex/hooks` | `AGENTS.md` |
| `claude` | `.claude/skills` | `.claude/rules` | `.claude/hooks` | `CLAUDE.md` |
| `generic` | `.agent/skills` | `.agent/rules` | `.agent/hooks` | `AGENTS.md` |

These files are runtime contracts. The Python template installers read them
directly; shell tools mirror the same built-in names when they must remain
standalone. Python installers retain the same embedded defaults when an
individual template directory is copied without this repository's `profiles/`
directory. Custom scalar YAML profiles can be passed with `--profile-file`.
