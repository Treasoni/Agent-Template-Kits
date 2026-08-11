# Agent Template Kits

一组可安装到其他项目的 Agent 工程模板源仓库（template source），本身并非可部署的应用。通过安装器将自学习、提示缓存、环境变量规范、可恢复 workflow、技能注册表、多 Agent 同步等能力注入目标项目。

## 仓库布局

| 路径 | 职责 |
|------|------|
| `profiles/` | 12 个内置 Agent 布局合同（YAML） |
| `templates/` | 可安装的规则、hook 和初始文件（self-learning / env / cache） |
| `skills/` | 可独立分发的 skill 包（共 7 个） |
| `scripts/` | 仓库级工具：`install.py`（统一安装器）、`validate.sh`、`validate-profiles.py`、`check-docs.py`、`sync-runtime-skills.py` |
| `.agents/skills/` | gitignored Codex runtime adapter，由 canonical/locked source 生成 |
| `.codex/` | 本仓库自身的 rules、hooks、scripts、workflows |
| `.claude/skills/` | gitignored Claude Code runtime adapter |
| `.agent-sync/` | 可选、gitignored 的多 Agent 同步 runtime |
| `tests/` | 回归测试（`test_*_sync.py`、`test_quality_guards.py`、`test_refactor_regressions.py`） |
| `docs/` | 便携性说明、设计规划文档（superpowers/）、完整功能文档 |
| `.learnings/` | 自学习记录（RULES.md、ERRORS.md、LEARNINGS.md） |

## 验证命令

```bash
# 完整验证套件（语法检查 + smoke test + 回归测试）
./scripts/validate.sh

# 环境变量模板检查
.codex/scripts/check-env-template.sh --strict

# Workflow routing 一致性检查
.codex/scripts/sync-workflow-routing.sh --check

# 密钥审计
skills/security-secret-audit/scripts/audit-secrets.sh --project --strict

# Profile YAML 合同验证
python3 scripts/validate-profiles.py

# 文档覆盖率检查
python3 scripts/check-docs.py

# Canonical/lock source 合同检查
python3 scripts/sync-runtime-skills.py --validate

# Git diff 检查
git diff --check
```

## 测试

```bash
# 运行所有测试
python3 -m pytest tests/

# 运行特定测试文件
python3 -m pytest tests/test_quality_guards.py -v

# 运行 smoke test（通过 validate.sh）
./scripts/validate.sh
```

## 核心工作流

### 新增一个 Agent Profile

1. 在 `profiles/` 下创建 YAML 文件（参考现有 profile 结构）
2. 必须包含：`name`、`description`、`agent_dir`、`skills_dir`、`rules_dir`、`scripts_dir`、`hooks_dir`、`entry_file`、`hook_config`、`hook_template`、`include_openai_yaml`、`env_template`、`skill_registry`、`prompt_cache_rule`
3. 更新 `README.md` 中的 profile 表格
4. 验证：`python3 scripts/validate-profiles.py`

### 新增一个 Skill

1. 在 `skills/<skill-name>/` 下创建目录结构：
   - `SKILL.md`（必需，包含 frontmatter metadata）
   - `scripts/`（安装脚本或工具脚本）
   - `references/`（文档和指南）
   - `assets/`（schema、模板等）
   - `agents/openai.yaml`（可选，OpenAI 兼容配置）
2. 如需要跨 profile 分发，将 skill 加入 `multi-agent-sync` 的 sync scope
3. 运行 `python3 scripts/sync-runtime-skills.py --validate`；仅用 `--apply` 刷新 gitignored 本机 runtime
4. 更新 `README.md` 和 `docs/` 中的组件说明

### 发布流程

1. 更新 `CHANGELOG.md`
2. 确保 `./scripts/validate.sh` 通过
3. 打标签：`git tag v1.x.x && git push origin v1.x.x`

## 编码规范

- **Python 3.10+**：使用类型注解（`from __future__ import annotations`）、`pathlib.Path`、f-string
- **Bash**：使用 `#!/usr/bin/env bash`，开启 `set -euo pipefail`
- **YAML**：profile 文件不使用制表符，UTF-8 编码
- **Markdown**：中文文档用中文写，SKILL.md 用英文写；代码块标明语言
- **跨平台**：路径使用 `/`，不依赖 `~` 展开；Python 脚本优先使用 `pathlib`
- **Hook 脚本**：Python 3 编写，通过 `bootstrap.py` 生成主机本地的 hooks.json
- **安全**：密钥审计脚本永不在输出中包含凭证原文；安装器默认 `--dry-run`

## 关键约定

- `.agents/skills/`、`.claude/skills/`、`.agent-runtime/`、`.agent-sync/` 和 host settings 都是 **gitignored 生成内容**。克隆后先运行 `python3 scripts/sync-runtime-skills.py --apply`
- 安装器（`scripts/install.py`）默认 **只预览不写入**，需要显式 `--apply`
- Skill 注册表只管理它之前创建过的 entries，保留手工添加的外部条目
- Workflow routing 更新后必须运行 `sync-workflow-routing.sh --check` 通过
- `validate.sh` 在 CI（GitHub Actions）上对 push 到 main 和 PR 自动执行，覆盖 Ubuntu/macOS/Windows

## 依赖

| 工具 | 用途 | 必需 |
|------|------|------|
| Python 3.10+ | 安装器、hooks、注册表、测试 | 是 |
| Bash | Shell 安装器和检查脚本 | Linux/macOS/WSL/Git Bash |
| Git | 克隆、密钥审计（历史模式） | 推荐 |
| ripgrep (`rg`) | 严格 env 检查 | 使用 env 时 |
| Perl | workflow 状态和密钥检测 | 使用对应组件时 |


<!-- self-learning:start -->
## Self-Learning

- Before task work, apply `.learnings/RULES.md`, `.learnings/ERRORS.md`, and recent `.learnings/LEARNINGS.md`.
- Codex loads the learning reminder through `.codex/hooks/read_learnings.py`. After a fresh clone, install `.agent-sync` and run its `bootstrap.py --apply` command to create the ignored `.codex/hooks.json` for the current host.
- Record real recurring mistakes or reusable lessons in `.learnings/`, but fix the source skill, template, hook, script, or project rule before archiving resolved records.
- Shared skill sources live under `skills/`; validate and generate local runtime with:

```bash
python3 scripts/sync-runtime-skills.py --validate
python3 scripts/sync-runtime-skills.py --apply
```

- Cross-profile configuration synchronization belongs to `multi-agent-sync`. When `.agent-sync/` is installed, preview with `python3 .agent-sync/sync_agents.py --check --scope skills` and apply only the affected scope.
<!-- self-learning:end -->

<!-- prompt-cache-bootstrap:begin -->
## Prompt Cache

- Follow `.codex/rules/common/prompt-cache.md` for high-frequency prompt design.
- Keep stable instructions and output formats before dynamic user input, file excerpts, dates, IDs, and runtime state.
- Reuse canonical templates and load long context only when needed.
<!-- prompt-cache-bootstrap:end -->

<!-- workflow-todo-state:start -->
## Workflow Todo State

Named workflow state files are the source of truth while a routed workflow is active.

- Workflow definitions live under `.codex/workflows/{workflow-id}/`.
- Workflow state files live under `workspace/workflow-runs/` and should be named after the task, for example `payment-refactor.workflow.md`.
- Before any action that changes project files, runs project commands, or calls external services, read `.codex/rules/workflow-routing.md` and match the user's original request against its triggers and exclusions.
- When a `Required: yes` workflow matches, read its `workflow.md`, create or resume its state file, and start the current phase before doing the work. Do not take the ordinary execution path instead.
- If the route is ambiguous, ask the user before acting.
- Read the active workflow state file before starting any phase; do not skip prerequisite phases.
- Change phase state only through `.codex/scripts/todo-state.sh`.
- Use one unique phase status line per phase, for example `> [P0] ⬜ 未开始 {not_started}`.
- The final phase requires `quality_gate: passed`; a temporary waiver also requires an owner and due date.
- Completed run states are removed or archived according to repository policy and do not replace changelogs or release notes.
- On resume after interruption, inspect the YAML frontmatter and current phase before acting.
- Each workflow directory must contain a `routing.yaml`. After creating, changing, renaming, or deleting a workflow, run `.codex/scripts/sync-workflow-routing.sh`; the update is incomplete until `.codex/scripts/sync-workflow-routing.sh --check` passes.
<!-- workflow-todo-state:end -->

<!-- env-template:codex:begin -->
## Environment Variables

- Follow `.codex/rules/common/env.md` whenever creating, updating, migrating, or auditing `.env`, `.env.example`, or environment-variable documentation.
- Keep committed env templates minimal, project-specific, and free of real secrets or machine-local absolute paths.
- After env template changes, run `.codex/scripts/check-env-template.sh`. Use `--strict` when you want unused documented variables to fail the check.
<!-- env-template:codex:end -->
