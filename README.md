# Agent Template Kits

<p align="left">
  <img src="https://img.shields.io/badge/agents-portable-blue" alt="Agent portable">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/status-maintained-brightgreen" alt="Status">
</p>

可复用到多个 AI agent、多个项目、多个操作系统的模板集合：skills、rules、hooks、workflow state、提示缓存规范和安全审计工具。

> 此项目最初是 Claude Code 技能集合，后来重构为通用 agent template source repository。Codex 与 Claude Code 仍是一等内置 profile，但不再是边界。

## 快速开始

```bash
# 安装自学习模板到通用 agent profile
python3 templates/self-learning/install.py --target /path/to/project --profile generic

# 安装到自定义 agent 目录
python3 templates/self-learning/install.py --target /path/to/project --custom-agent myagent:.my-agent/skills:.my-agent/hooks

# 安装提示缓存规则到通用 agent profile
bash templates/cache/prompt-cache-bootstrap.sh --apply --platform none --agent generic,.agent,AGENTS.md --target /path/to/project

# 安装环境变量规则到 Codex profile
python3 templates/env/install.py --target /path/to/project --profile codex

# 安装 workflow 状态机到通用 agent profile
bash skills/workflow-todo-state/scripts/install.sh /path/to/project --agent-dir .agent --with-skill --init-layout --update-agents

# 同步技能注册表
python3 skills/sync-skill-registry/scripts/sync_skill_registry.py --profile generic --root /path/to/project --create --dry-run
```

历史默认仍可用：

```bash
python3 templates/self-learning/install.py --target /path/to/project
bash templates/cache/prompt-cache-bootstrap.sh --apply --platform both --target /path/to/project
```

## 核心理念

很多 agent 项目都需要同一组基础能力：管理技能注册表、记录经验教训、优化提示缓存、维护可恢复 workflow、审计密钥泄露。这些能力不应该被某个 agent 名称或某个操作系统绑定。

本仓库把可复用内容分成两层：

- **模板包**：具体能力，例如 `self-learning`、`prompt-cache`、`workflow-todo-state`。
- **Agent profile**：目标 agent 的目录布局和入口文件，例如 `.agents/skills + AGENTS.md`、`.claude/skills + CLAUDE.md`、`.agent/skills + AGENTS.md`。

## 内置 Profiles

| Profile | Skills | Rules / Config | Hooks | Entry |
| --- | --- | --- | --- | --- |
| `codex` | `.agents/skills` | `.codex/rules` | `.codex/hooks` | `AGENTS.md` |
| `claude` | `.claude/skills` | `.claude/rules` | `.claude/hooks` | `CLAUDE.md` |
| `generic` | `.agent/skills` | `.agent/rules` | `.agent/hooks` | `AGENTS.md` |

Python 安装器直接读取 `profiles/*.yaml`。其他 agent 可通过 `--profile-file` 接入可复用布局，也可使用 `--custom-agent name:skills_dir:hooks_dir` 或 `--agent name,agent_dir,entry_file` 进行一次性配置。

## 目录结构

```text
.
├── docs/
│   └── PORTABILITY.md
├── profiles/
│   ├── codex.yaml
│   ├── claude.yaml
│   └── generic.yaml
├── scripts/
│   └── validate.sh
├── skills/
│   ├── prompt-cache-optimizer/        # 提示缓存优化 skill 包
│   ├── security-secret-audit/         # 密钥泄露审计 skill 包
│   ├── sync-skill-registry/           # 技能注册表同步工具
│   └── workflow-todo-state/           # 可恢复 workflow 状态机模板
├── templates/
│   ├── cache/                     # 提示缓存规则模板
│   ├── env/                       # 环境变量模板与检查脚本
│   └── self-learning/             # 自学习 skill / hook 模板
└── README.md
```

## 组件

### `templates/self-learning/`

提供 `digest` 与 `maintain-learnings` 两个 skills，以及跨平台 Python hook `read_learnings.py`。默认兼容 Codex + Claude，也可安装到 `generic` 或任意自定义 agent profile。

### `templates/cache/` 与 `skills/prompt-cache-optimizer/`

安装提示缓存规则、入口文件引用、提示动态字段检查；`skills/prompt-cache-optimizer/` 还包含观测 schema 和回归样本模板。

### `skills/workflow-todo-state/`

为长任务提供命名 workflow、可恢复状态文件和 phase gate。安装器支持 `--agent-dir`，不再写死 `.claude`。

### `skills/sync-skill-registry/`

扫描任意 `<skills-dir>/*/SKILL.md`，更新 `skill-invocation.md` 中的技能表格。支持 `--profile codex|claude|generic` 和完全自定义路径。

### `skills/security-secret-audit/`

提交前或泄露排查时扫描 API Key、Token、密码、私钥等敏感信息；报告文件、行号、规则名，不输出凭证原文。

### `templates/env/`

面向不同内置 profile 的环境变量规则和 `.env.example` 检查脚本模板。通过 `templates/env/install.py` 复用到目标 agent profile。

## 复用原则

1. **先选 profile**：优先使用内置 `generic`，或者为目标 agent 指定自己的目录与入口文件。
2. **模板不绑定 OS**：Python 脚本优先；Shell 脚本使用 `/usr/bin/env bash` 或 POSIX `sh`，适合 Linux/macOS/WSL/Git Bash。
3. **平台专属内容隔离**：OpenAI UI 元数据、Claude settings、其他 agent hook 配置只放在各自 profile。
4. **安装脚本幂等**：先 dry-run 或 check，再 apply；已有规则文件默认保留。
5. **同步共享能力，不覆盖专属配置**：多 agent 目录之间只同步共享 skill 逻辑，保留各自入口文件、权限和 hook。
6. **统一验证**：改动模板或脚本后运行 `scripts/validate.sh`。

`scripts/validate.sh` 包含安装 smoke test 和 `tests/` 中的回归测试；GitHub Actions 会额外执行严格环境模板检查与密钥审计。

更多迁移和接入细节见 [docs/PORTABILITY.md](docs/PORTABILITY.md)。
