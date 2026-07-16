# Portability Guide

本仓库的目标是让模板能迁移到不同 agent、不同仓库、不同操作系统，而不是只服务某一个本地工具。

## Agent Profile Model

每个 agent profile 只描述目标项目里的目录布局：

| 字段 | 含义 | 示例 |
| --- | --- | --- |
| `skills_dir` | skill 模板安装目录 | `.agent/skills` |
| `rules_dir` | agent 专属规则目录 | `.agent/rules` |
| `scripts_dir` | 受管检查和辅助脚本目录 | `.agent/scripts` |
| `hooks_dir` | agent hook 脚本目录 | `.agent/hooks` |
| `entry_file` | 项目入口规则文件 | `AGENTS.md` |

内置 profile：

```text
codex   -> .agents/skills + .codex/rules + .codex/hooks + AGENTS.md
claude  -> .claude/skills + .claude/rules + .claude/hooks + CLAUDE.md
codebuddy -> .codebuddy/skills + .codebuddy/rules + .codebuddy/hooks + CODEBUDDY.md
cursor  -> .cursor/skills + .cursor/rules + AGENTS.md
gemini  -> .gemini/skills + .gemini/rules + GEMINI.md
github-copilot -> .github/skills + .github/instructions + .github/copilot-instructions.md
cline   -> .cline/skills + .clinerules + AGENTS.md
roo-code -> .roo/skills + .roo/rules + AGENTS.md
windsurf -> .windsurf/skills + .windsurf/rules + AGENTS.md
opencode -> .opencode/skills + .opencode/rules + AGENTS.md
qwen-code -> .qwen/skills + .qwen/rules + QWEN.md
generic -> .agent/skills + .agent/rules + .agent/hooks + AGENTS.md
```

第三方 agent 不需要修改模板内容，只需要指定自己的目录：

```bash
python3 templates/self-learning/install.py --target . --custom-agent myagent:.my-agent/skills:.my-agent/hooks
python3 templates/env/install.py --target . --custom-agent myagent:.my-agent:INSTRUCTIONS.md
bash skills/prompt-cache-optimizer/scripts/prompt-cache-bootstrap.sh --apply --platform none --agent myagent,.my-agent,INSTRUCTIONS.md --with-skill --target .
bash skills/workflow-todo-state/scripts/install.sh . --agent-dir .my-agent --entry-file INSTRUCTIONS.md --with-skill --init-layout --update-agents
python3 skills/sync-skill-registry/scripts/sync_skill_registry.py --root . --skills-dir .my-agent/skills --registry-file .my-agent/rules/common/skill-invocation.md --create --with-skill --dry-run
```

确认注册表预览后，去掉 `--dry-run` 执行；首次应用会复制 `sync-skill-registry` skill。

需要在多个安装器中复用同一布局，或路径包含 Windows 盘符冒号时，使用与 `profiles/*.yaml` 相同的 scalar YAML profile：

```bash
python3 templates/self-learning/install.py --target . --profile-file /path/to/myagent.yaml
python3 templates/env/install.py --target . --profile-file /path/to/myagent.yaml
```

## Template Portability Rules

- Shared skill logic lives inside the skill directory.
- Agent-specific metadata stays isolated, for example `agents/openai.yaml`, `.claude/settings.json`, or a third-party hook config.
- Environment-variable rules and check scripts live under `templates/env/`; install them into the target profile rather than keeping a top-level `env/` directory.
- Entry files should contain small routing snippets and point to rule files instead of duplicating long rules.
- Generated sections must be marker-delimited or heading-delimited so scripts can update only their owned block.
- Paths stored inside templates and generated hook commands should be project-relative, not absolute.

## Operating System Rules

- Python utilities should use `pathlib` and UTF-8 reads/writes.
- Shell utilities should use `/usr/bin/env bash` only when Bash features are required.
- POSIX-compatible hooks should use `/usr/bin/env sh`.
- Avoid macOS-only commands and BSD-only flags when a Python implementation is reasonable.
- Native Windows agents should prefer Python hooks such as `read_learnings.py`; Bash scripts are expected to run in Linux, macOS, WSL, or Git Bash.
- `scripts/install.py` is the cross-platform coordinator: it uses the running Python interpreter for Python components and searches `PATH` plus common Git for Windows locations for Bash when a selected component needs it.
- CodeBuddy's `SessionStart` hook is installed as a Python command in `.codebuddy/settings.json`; on Windows, CodeBuddy itself executes hooks through Git Bash and the unified installer writes the active Python executable name rather than a Unix-only path.

## Adding A New Agent

1. Choose a project-relative agent directory, such as `.my-agent`.
2. Decide the entry file, such as `INSTRUCTIONS.md`.
3. Install templates with custom profile arguments.
4. Wire copied hook scripts into that agent's hook/config mechanism.
5. Run the check/dry-run command for each installed component.
6. Document any platform-specific metadata that must not be synchronized to other profiles.

## Compatibility Checks

Useful validation commands:

```bash
python3 -m py_compile scripts/install.py templates/self-learning/install.py templates/self-learning/hooks/read_learnings.py
python3 -m py_compile templates/env/install.py
bash -n templates/cache/prompt-cache-bootstrap.sh skills/workflow-todo-state/scripts/install.sh
bash templates/cache/prompt-cache-bootstrap.sh --check --platform none --agent generic,.agent,AGENTS.md --target /path/to/project
python3 skills/sync-skill-registry/scripts/sync_skill_registry.py --profile generic --root /path/to/project --dry-run
scripts/validate.sh
```
