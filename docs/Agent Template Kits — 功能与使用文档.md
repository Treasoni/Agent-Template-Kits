# Agent Template Kits — 功能与使用文档

> 版本：对应仓库 `Unreleased` 发行线  
> 适用对象：需要在 AI 编程助手中引入工程化能力的开发团队  
> 文档定位：面向客户的产品功能说明 + 快速上手指南

---

## 目录

1. [产品概述](#1-产品概述)
2. [核心功能](#2-核心功能)
3. [支持的 AI 编程助手](#3-支持的-ai-编程助手)
4. [运行环境要求](#4-运行环境要求)
5. [快速开始](#5-快速开始)
6. [统一安装器详解](#6-统一安装器详解)
7. [各功能模块详解](#7-各功能模块详解)
8. [自定义 Agent 接入](#8-自定义-agent-接入)
9. [更新已安装的模板](#9-更新已安装的模板)
10. [安全与幂等性保障](#10-安全与幂等性保障)
11. [验证与质量检查](#11-验证与质量检查)
12. [常见问题](#12-常见问题)
13. [目录结构参考](#13-目录结构参考)
14. [发布流程](#14-发布流程)

---

## 1. 产品概述

Agent Template Kits 是一组**可移植、可安装**的 AI Agent 工程模板。它不是需要部署的应用，而是一套"模板源"——你将它克隆到本地，然后通过安装器把所需能力写入你的目标项目。

### 解决什么问题

| 痛点 | 本产品提供的方案 |
|------|------------------|
| AI 编程助手每次会话从零开始，不记住历史经验 | **自学习系统**：自动读取经验库，持续积累规则与纠错记录 |
| 提示词结构混乱，LLM 缓存命中率低，调用成本高 | **提示缓存优化**：规范提示布局，降低 token 消耗和延迟 |
| 环境变量管理混乱，容易泄露密钥 | **环境变量规范**：统一 `.env.example` 维护，自动检查缺失和可疑凭证 |
| 长任务中断后无法恢复，缺乏流程管控 | **可恢复 Workflow**：基于状态机的阶段管理，支持中断恢复 |
| 技能散落各处，无法统一管理 | **技能注册表**：自动扫描和同步所有 SKILL.md 元数据 |
| 提交代码前没有密钥安全检查 | **密钥审计**：扫描 Git 工作树中的 API Key、Token、密码和私钥 |
| 多个 AI 助手之间配置不同步，手动维护易出错 | **多 Agent 同步**：以一个 canonical profile 为源，自动同步到其他 Agent |
| 缺乏资产版本和权限的可验证合同 | **Manifest Platform**：为 workflow、skill、hook 建立可验证的注册表与权限合同 |

### 设计理念

- **模板源而非应用**：克隆后安装到目标项目，不改动目标项目已有结构
- **安全优先**：所有操作默认 dry-run 预览，确认后才执行
- **幂等可重复**：安装器可安全重复执行，不会覆盖已有定制内容
- **跨平台跨 Agent**：一套模板，适配 12 种主流 AI 编程助手，支持 Linux、macOS、Windows
- **可追溯更新**：通过 `install-state.json` 记录已安装的 profile、组件和文件指纹，安全更新时能区分模板变更与项目定制内容

---

## 2. 核心功能

本产品包含 **8 大功能模块**，可单独安装，也可组合使用：

### 2.1 自学习系统（Self-Learning）

让 AI 编程助手在每次会话开始时自动加载历史经验。

- **`digest` 技能**：记录本次任务中真实发生的学习点和错误
- **`maintain-learnings` 技能**：当经验库变长或错误反复出现时，先修源头（skill/模板/hook/规则），再归档已解决记录
- **自动加载 Hook**：会话启动时自动读取 `.learnings/RULES.md`、`ERRORS.md` 和最近的 `LEARNINGS.md`
- `maintain-learnings` 只维护经验库，不承担 profile 同步职责

### 2.2 提示缓存优化（Prompt Cache Optimizer）

审计并优化 LLM 提示缓存命中率、输入 token、延迟与调用成本。

- 安装提示缓存规则和入口文件引用
- 审计高频请求：检查稳定前缀、动态字段位置、不必要的全文件加载
- 可选可观测性：安装调用事件 schema（`/.llm/prompt-cache/`）和回归样本模板
- 提供设计原理、反例、指标与落地检查清单

### 2.3 环境变量规范（Env Template）

统一 `.env.example` 的创建、更新和审计方式。

- 安装规则文件和检查脚本到目标项目
- **默认模式**：阻止缺失变量和可疑凭证
- **严格模式**（`--strict`）：未被代码引用的模板变量也视为失败
- 保障环境变量模板最小化、项目专属、无真实密钥

### 2.4 可恢复 Workflow（Workflow Todo State）

为长任务提供基于状态机的可恢复工作流管理。

- 创建可复用的命名工作流定义（`workflow.md` + `routing.yaml`）
- 生成人类可读的 Markdown 清单 + 机器可读的 YAML 前置元数据
- 通过 `todo-state.sh` 脚本确定性更新阶段状态
- 支持阶段流转：`未开始 → 进行中 → 已完成 / 跳过 / 阻塞`
- 中断后可检查 YAML 前置元数据和当前阶段，安全恢复

### 2.5 技能注册表同步（Skill Registry）

自动扫描和同步所有 SKILL.md 元数据到注册表。

- 扫描 `*/SKILL.md` 的 YAML frontmatter（name, description, category）
- 自动更新 `skill-invocation.md` 中的技能表格
- 智能比较：新增、更新、删除、保留——四类操作精确处理
- 只管理受管区域，不影响手工维护的内容

### 2.6 密钥安全审计（Security Secret Audit）

在提交前扫描 Git 工作树中的暴露凭证。

- 三种扫描范围：当前文件 / staged 内容 / Git 全历史
- 检测项：API Key、Token、密码、私钥、JWT 等
- **安全输出**：报告只包含文件、行号和规则名，绝不输出凭证原文
- 退出码语义明确：`0` 通过、`2` 发现凭证、`1` 扫描器错误

### 2.7 多 Agent 同步（Multi-Agent Sync）

跨 profile 共享配置的唯一同步器。

- 以一个 canonical profile 为源，同步 skills、rules、hooks、scripts、workflows 和 MCP 配置
- 支持 6 种同步范围：`skills`、`rules`、`hooks`、`scripts`、`workflows`、`mcp`
- 先用 `--check` 审阅漂移，再只对受影响 scope 使用 `--apply`
- `bootstrap.py` 根据当前主机 Python 解释器生成本机 hook 配置（`hooks.json` / `settings.json`），这些文件被 gitignored
- `validate_portability.py` 验证交付目标平台的可移植性
- 路径安全：所有 profile 路径必须是非空、项目相对的 POSIX 路径，拒绝绝对路径、`..` 和反斜杠

### 2.8 Agent Manifest Platform

为 workflow、skill、hook 和 subagent 建立可验证的注册表与权限合同。

- 通过 `manifest-registry.py validate` 发现缺失 manifest、无效入口或不允许的权限
- 声明最窄的真实权限（manifest 请求权限，由 host 运行时强制执行）
- 支持依赖 ID 引用，但仅在被引用的 manifest 存在后才可添加
- `manifest-registry.py init` 可创建初始 manifest 供后续细化

---

## 3. 支持的 AI 编程助手

本产品内置 **12 种** Agent Profile，覆盖主流 AI 编程助手：

| Profile | Skills 目录 | Rules 目录 | Hooks | 入口文件 |
|---------|------------|-----------|-------|---------|
| `codex` | `.agents/skills` | `.codex/rules` | `.codex/hooks` | `AGENTS.md` |
| `claude` | `.claude/skills` | `.claude/rules` | `.claude/hooks` | `CLAUDE.md` |
| `codebuddy` | `.codebuddy/skills` | `.codebuddy/rules` | `.codebuddy/hooks` | `CODEBUDDY.md` |
| `cursor` | `.cursor/skills` | `.cursor/rules` | — | `AGENTS.md` |
| `gemini` | `.gemini/skills` | `.gemini/rules` | — | `GEMINI.md` |
| `github-copilot` | `.github/skills` | `.github/instructions` | — | `.github/copilot-instructions.md` |
| `cline` | `.cline/skills` | `.clinerules` | — | `AGENTS.md` |
| `roo-code` | `.roo/skills` | `.roo/rules` | — | `AGENTS.md` |
| `windsurf` | `.windsurf/skills` | `.windsurf/rules` | — | `AGENTS.md` |
| `opencode` | `.opencode/skills` | `.opencode/rules` | — | `AGENTS.md` |
| `qwen-code` | `.qwen/skills` | `.qwen/rules` | — | `QWEN.md` |
| `generic` | `.agent/skills` | `.agent/rules` | `.agent/hooks` | `AGENTS.md` |

未在列表中的 Agent 可使用 `generic` profile，或按 [第 8 节](#8-自定义-agent-接入) 创建自定义 Profile。

自动检测器会忽略仅有 `AGENTS.md` 文件的项目，因为该文件名是通用入口，不足以判断具体运行时。

---

## 4. 运行环境要求

| 工具 | 用途 | 要求 |
|------|------|------|
| **Git** | 克隆模板、密钥审计 | 建议安装 |
| **Python 3** | 安装器、hooks、注册表 | 必需 |
| **Bash** | Shell 安装器和检查脚本 | Linux、macOS、WSL 或 Git Bash |
| **ripgrep (`rg`)** | 严格 env 检查 | 使用 env 检查时必需 |
| **Perl** | workflow 状态和密钥检测 | 使用对应组件时必需 |

> **Windows 用户**：Python 脚本可直接运行（使用 `py -3` 或 `python`）。Bash 脚本需要安装 Git for Windows（提供 Git Bash）或使用 WSL。统一安装器会自动查找系统 Bash 和常见 Git Bash 安装路径；找不到时不会写入目标项目，并明确提示安装 Git for Windows 或使用 WSL。

---

## 5. 快速开始

### 第一步：获取模板

```bash
git clone https://github.com/Treasoni/Agent-Template-Kits.git
cd Agent-Template-Kits
```

### 第二步：指定目标项目

```bash
# 你的目标项目目录（必须已存在）
export TARGET=/absolute/path/to/your-project
test -d "$TARGET"
```

> **Windows 用户**：以下命令中将 `python3` 替换为 `python`。脚本同时接受 `python3` 或 `python`，生成的 hooks 在 Windows 上使用 `python.exe`。

### 第三步：自动检测并安装（推荐）

```bash
# 1. 只检测，不修改目标项目——查看自动识别结果
python3 scripts/install.py --target "$TARGET" --detect

# 2. 预览安装计划（仍不写入）
python3 scripts/install.py --target "$TARGET" --use-detected

# 3. 确认后执行安装（仅安装需要的能力）
python3 scripts/install.py \
  --target "$TARGET" \
  --use-detected \
  --components self-learning,env,registry \
  --apply --yes
```

安装完成后，建议检查目标项目的 `git diff`，确认变更内容后再提交。

---

## 6. 统一安装器详解

统一安装器（`scripts/install.py`）是跨平台的协调入口，提供以下能力：

### 6.1 可选组件

| 组件名称 | 说明 |
|----------|------|
| `self-learning` | 自学习系统（skills + hooks + 学习记录） |
| `env` | 环境变量规则和检查脚本 |
| `prompt-cache` | 提示缓存 skill 和规则 |
| `workflow` | 可恢复 workflow、routing 规则和状态脚本 |
| `registry` | 技能注册表 |
| `manifest-platform` | Agent 资产 manifest registry（显式选择） |
| `multi-agent-sync` | 跨 profile 同步 runtime（显式选择） |

默认安装前五项核心组件；后两项会额外写入 registry 或 `.agent-sync/` runtime，须显式选择。可通过 `--components` 按需组合：

```bash
python3 scripts/install.py \
  --target "$TARGET" \
  --use-detected \
  --components self-learning,env,registry \
  --apply --yes
```

统一安装器会把 `prompt-cache-optimizer`、`workflow-todo-state`、`sync-skill-registry` 和按需选择的 `manifest-platform` 复制到所选 profile 的 skills 目录。`prompt-cache`、`workflow` 与 `manifest-platform` 使用 Bash：Linux/macOS 可直接运行；Windows 下安装器会寻找 Git Bash，找不到时会明确提示。

### 6.2 安装器行为

- **默认 dry-run**：先预览将执行的命令，不修改目标项目
- **自动检测**：根据目标项目已有的 agent 目录、配置和入口文件推荐 Profile，并显示检测证据
- **手动选择**：`--profile <name>` 指定单个 Profile
- **多 Profile 支持**：可重复使用 `--profile` 安装到多个 Agent
- **确认机制**：`--apply` 时要求确认；非交互环境需显式 `--yes`
- **完整 Skill 复制**：`prompt-cache-optimizer`、`workflow-todo-state`、`sync-skill-registry` 和按需选择的 `manifest-platform` 会一并复制到目标项目
- **`--overwrite`、`--force-workflow` 和 `--force-manifest-platform`** 都需要显式给出，避免覆盖已有定制内容

### 6.3 关键参数

| 参数 | 说明 |
|------|------|
| `--target <path>` | 目标项目路径（必须已存在） |
| `--detect` | 只检测，不修改 |
| `--use-detected` | 采用所有检测到的 Profile |
| `--profile <name>` | 手动指定 Profile |
| `--components <list>` | 按需选择组件 |
| `--apply` | 执行安装（否则只预览） |
| `--yes` | 非交互环境跳过确认 |
| `--overwrite` | 覆盖已有受管内容（需显式给出） |
| `--force-workflow` | 强制覆盖不同的 workflow 文件（需显式给出） |
| `--force-manifest-platform` | 强制覆盖不同的 manifest registry 或 skill（需显式给出） |

---

## 7. 各功能模块详解

### 7.1 安装自学习系统

```bash
python3 templates/self-learning/install.py --target "$TARGET" --profile codex
```

**安装内容：**
- `digest` 和 `maintain-learnings` skills
- `.learnings/RULES.md`、`ERRORS.md`、`LEARNINGS.md`
- 会话开始读取经验库的 hook 脚本
- 对应 Agent 的 hook 配置（保留既有无关 hooks）

如不需要 hooks：
```bash
python3 templates/self-learning/install.py --target "$TARGET" --profile codex --no-hooks
```

### 7.2 安装提示缓存优化

**完整版（推荐）**——安装 skill 和规则：
```bash
bash skills/prompt-cache-optimizer/scripts/prompt-cache-bootstrap.sh \
  --apply --platform codex --with-skill --target "$TARGET"
```

**精简版**——只安装规则和入口文件引用：
```bash
bash templates/cache/prompt-cache-bootstrap.sh \
  --apply --platform codex --target "$TARGET"
```

**审计现有配置**（只读检查）：
```bash
bash templates/cache/prompt-cache-bootstrap.sh \
  --check --platform codex --target "$TARGET"
```

> 可观测性（`--with-observability`）：仅当 Agent 已接通自动 LLM usage 采集时使用。它会安装 `/.llm/prompt-cache/` 的 schema 和回归样本。直接使用 Codex 时不要加此选项，也无需手填 token 或费用。

### 7.3 安装环境变量规范

```bash
python3 templates/env/install.py --target "$TARGET" --profile codex
```

**安装后检查：**
```bash
cd "$TARGET"

# 默认模式：检查缺失变量和可疑凭证
.codex/scripts/check-env-template.sh

# 严格模式：未被代码引用的模板变量也视为失败
.codex/scripts/check-env-template.sh --strict
```

> 检查脚本不会自动创建 `.env.example`，目标项目需先准备自己的最小环境变量模板。

**本仓库自身的 `.env.example` 变量说明：**

| 变量 | 默认值 | 用途 |
|------|--------|------|
| `PYTHON` | `python3` | Python 解释器路径，Windows 下自动检测 `py -3` 或 `python.exe` |
| `PROMPT_CACHE_ASSET_DIR` | 空（使用内置资源） | 提示缓存观测 schema 与回归样本的自定义路径 |
| `PROMPT_CACHE_PROFILE_ROOT` | 空 | 独立安装器副本使用的 profile-contract 位置 |
| `WORKFLOW_PROFILE_ROOT` | 空 | 独立安装器副本使用的 workflow profile-contract 位置 |

### 7.4 安装可恢复 Workflow

```bash
bash skills/workflow-todo-state/scripts/install.sh \
  "$TARGET" \
  --profile codex \
  --with-skill \
  --init-layout \
  --update-agents
```

**安装后使用流程：**
1. 在 `.codex/workflows/<workflow-id>/` 创建 `workflow.md`、`state-template.md` 和 `routing.yaml`
2. 运行 `.codex/scripts/sync-workflow-routing.sh` 生成路由注册表
3. 从 state template 创建 `workspace/workflow-runs/<task>.workflow.md`
4. 通过 `todo-state.sh` 更新阶段状态：

```bash
# 开始阶段
.codex/scripts/todo-state.sh "${WORKFLOW_STATE_FILE}" start P1

# 完成阶段
.codex/scripts/todo-state.sh "${WORKFLOW_STATE_FILE}" complete P1

# 跳过阶段
.codex/scripts/todo-state.sh "${WORKFLOW_STATE_FILE}" skip P2 "not needed"

# 阻塞阶段
.codex/scripts/todo-state.sh "${WORKFLOW_STATE_FILE}" block P3 "waiting for user input"
```

**阶段状态流转规则：**
- `start PN`：要求前序阶段全部为"已完成"或"跳过"
- `complete PN`：要求当前阶段为"进行中"
- `skip PN`：拒绝已完成阶段，记录跳过原因
- `block PN`：标记为阻塞，记录原因
- 完成或跳过后，自动推进到下一个"未开始"阶段

### 7.5 安装技能注册表

```bash
# 预览（不写文件）
python3 skills/sync-skill-registry/scripts/sync_skill_registry.py \
  --profile codex --root "$TARGET" --create --with-skill --dry-run

# 应用
python3 skills/sync-skill-registry/scripts/sync_skill_registry.py \
  --profile codex --root "$TARGET" --create --with-skill
```

**工作原理：**
1. 扫描 `<skills-dir>/*/SKILL.md`，解析 frontmatter
2. 读取当前 `skill-invocation.md`，提取现有表格
3. 比较：新增、更新、删除（受管条目）、保留（手工条目）
4. 按分类重新生成 Markdown 表格并写入

### 7.6 密钥安全审计

从目标项目调用本仓库的审计脚本：

```bash
AUDITOR="$PWD/skills/security-secret-audit/scripts/audit-secrets.sh"

# 扫描当前已跟踪和未忽略文件
(cd "$TARGET" && "$AUDITOR")

# 提交前只扫描 staged 内容
(cd "$TARGET" && "$AUDITOR" --staged)

# 泄露排查：包含 Git 历史
(cd "$TARGET" && "$AUDITOR" --all)

# 项目安全审查：凭证泄漏 + 高置信度源码、配置和敏感文件风险
(cd "$TARGET" && "$AUDITOR" --project)

# CI 阻断模式；默认不扫描 Git 历史
(cd "$TARGET" && "$AUDITOR" --project --strict)

# 先预览，再仅补充受管的本地凭证忽略规则
(cd "$TARGET" && "$AUDITOR" --project --fix)
```

**退出码：**
| 退出码 | 含义 |
|--------|------|
| `0` | 无凭证发现；非严格项目风险作为待处理告警 |
| `2` | 发现潜在凭证，或 `--strict` 下发现项目风险，应阻止提交 |
| `1` | 扫描器错误，需排查 |

项目审查覆盖禁用 TLS 校验、shell 命令执行、宽松 CORS、全局可写权限、敏感数据日志、被追踪的凭证文件和缺少本地凭证忽略规则。报告只显示位置和规则名。`--fix` 仅添加幂等 `.gitignore` 块，不会删除凭证、轮换密钥、改写历史、暂存、提交或推送。

### 7.7 多 Agent 同步

`multi-agent-sync` 是跨 profile 共享配置的唯一同步器。显式安装 runtime 后，先预览漂移，再只应用受影响 scope：

```bash
# 1. 安装 multi-agent-sync runtime
python3 scripts/install.py \
  --target "$TARGET" \
  --profile codex \
  --components multi-agent-sync \
  --apply --yes

# 2. 预览同步漂移
python3 "$TARGET/.agent-sync/sync_agents.py" --root "$TARGET" --check --scope skills

# 3. 应用同步
python3 "$TARGET/.agent-sync/sync_agents.py" --root "$TARGET" --apply --scope skills

# 4. 生成本机 hook 配置（hooks.json / settings.json）
cd "$TARGET"
python3 .agent-sync/scripts/bootstrap.py --apply
python3 .agent-sync/scripts/bootstrap.py --check
```

**支持 6 种同步范围：** `skills`、`rules`、`hooks`、`scripts`、`workflows`、`mcp`

**bootstrap.py 说明：**
- 根据当前主机的 Python 解释器路径生成各 Agent 的 `hooks.json` 或 `settings.json`
- 这些文件已在 `.gitignore` 中，不会提交到版本控制
- 在另一台机器克隆后需重新执行 `bootstrap.py --apply`
- bootstrap 只替换受管的 Python hook 命令，保留无关设置

**跨平台验证：**
```bash
# 验证交付目标操作系统的可移植性
python3 skills/multi-agent-sync/scripts/validate_portability.py --root "$TARGET" --platform macos
python3 skills/multi-agent-sync/scripts/validate_portability.py --root "$TARGET" --platform windows
python3 skills/multi-agent-sync/scripts/validate_portability.py --root "$TARGET" --platform linux
```

> **Windows PowerShell 等价命令**：将 `python3` 替换为 `py -3`，路径使用 Windows 格式。

### 7.8 Manifest Platform

为 workflow、skill、hook 和 subagent 建立可验证的注册表与权限合同：

```bash
# 1. 安装 manifest-platform
python3 scripts/install.py \
  --target "$TARGET" \
  --profile codex \
  --components manifest-platform \
  --apply --yes

# 2. 验证 registry
python3 "$TARGET/.codex/platform/manifest-registry.py" --root "$TARGET" validate

# 3. 创建初始 manifest（可选）
python3 "$TARGET/.codex/platform/manifest-registry.py" --root "$TARGET" init
```

如 registry 或 skill 已被项目定制，先检查差异；确认可替换后才补充 `--force-manifest-platform`。

**Manifest 工作流程：**
1. 安装 registry，检查现有配置
2. 审阅 `<agent-dir>/platform/registry.yaml`，调整发现路径或 hook 注册文件
3. 为每个资产添加 `manifest.yaml`，声明能力与权限
4. 声明最窄的真实权限（manifest 请求权限，由 host 运行时强制执行）
5. 添加依赖 ID 仅在被引用的 manifest 存在之后
6. 运行 `validate` 解决所有失败项

---

## 8. 自定义 Agent 接入

如果你的 AI 编程助手不在内置列表中，可以通过以下方式接入：

### 方式一：创建 YAML Profile（推荐）

创建一个与 `profiles/*.yaml` 字段一致的 scalar YAML 文件：

```yaml
name: myagent
description: "Custom profile for MyAgent projects."
agent_dir: .my-agent
skills_dir: .my-agent/skills
rules_dir: .my-agent/rules
scripts_dir: .my-agent/scripts
hooks_dir: .my-agent/hooks
entry_file: INSTRUCTIONS.md
hook_config: ""
hook_template: ""
include_openai_yaml: false
env_template: codex
skill_registry: .my-agent/rules/common/skill-invocation.md
prompt_cache_rule: .my-agent/rules/common/prompt-cache.md
```

然后用 `--profile-file` 安装：

```bash
python3 templates/self-learning/install.py --target "$TARGET" --profile-file /path/to/myagent.yaml
python3 templates/env/install.py --target "$TARGET" --profile-file /path/to/myagent.yaml
```

### 方式二：使用命令行参数

```bash
# 自学习
python3 templates/self-learning/install.py \
  --target "$TARGET" --custom-agent myagent:.my-agent/skills:.my-agent/hooks

# 环境变量
python3 templates/env/install.py \
  --target "$TARGET" --custom-agent myagent:.my-agent:INSTRUCTIONS.md

# 提示缓存
bash skills/prompt-cache-optimizer/scripts/prompt-cache-bootstrap.sh \
  --apply --platform none \
  --agent myagent,.my-agent,INSTRUCTIONS.md \
  --with-skill --target "$TARGET"

# Workflow
bash skills/workflow-todo-state/scripts/install.sh \
  "$TARGET" \
  --agent-dir .my-agent \
  --skills-dir .my-agent/skills \
  --entry-file INSTRUCTIONS.md \
  --with-skill --init-layout --update-agents

# 技能注册表
python3 skills/sync-skill-registry/scripts/sync_skill_registry.py \
  --root "$TARGET" \
  --skills-dir .my-agent/skills \
  --registry-file .my-agent/rules/common/skill-invocation.md \
  --create --with-skill --dry-run
```

确认预览无误后，去掉 `--dry-run` 执行。

---

## 9. 更新已安装的模板

通过统一安装器完成的安装会在目标项目保存 `.agent-template-kits/install-state.json`，记录已选 profile、组件和受管文件的指纹。这让更新器能区分模板变更与项目自己的定制内容。

### 9.1 选择可信版本

先在**模板仓库**中选择要发布给用户的可信版本；这一步只更新模板源，不会修改目标项目的 Git：

```bash
git fetch --tags origin
git switch --detach v1.2.3   # 替换为你准备发布的版本标签
```

### 9.2 预览更新

更新器会把目标项目复制到临时目录，在副本上用原先的 profile 和组件生成候选结果；默认不会写入目标项目：

```bash
python3 scripts/install.py update --target "$TARGET"
```

### 9.3 处理冲突

如果输出 `[CONFLICT] path`，表示该受管文件被项目修改、删除，或新模板将覆盖一个未受管的现有文件。更新会停止，直到你逐项确认：

```bash
python3 scripts/install.py update \
  --target "$TARGET" \
  --accept .agent/rules/common/env.md \
  --accept .agent/skills/prompt-cache-optimizer/SKILL.md \
  --apply --yes
```

> 不要用通配符批量接受。每个冲突路径必须显式写为一个 `--accept`。

### 9.4 应用更新

确认无误后执行：

```bash
python3 scripts/install.py update \
  --target "$TARGET" \
  --apply --yes
```

**更新器的安全行为：**
- 应用前，把所有将改动的现有文件备份到 `.agent-template-kits/backups/<UTC 时间戳>/`
- 执行安装并核对结果是否与预览一致
- 不执行 `git pull`、`fetch`，不修改目标项目的 Git 元数据
- 拒绝包含符号链接的目标目录，防止写入越过边界
- 后续补装 profile 或组件时，更新器会维护已安装的全部选择

### 9.5 首次迁移旧项目

首次使用过旧的单独安装命令的项目没有状态文件。请先使用一次 `scripts/install.py --apply` 重新安装所需组件，之后才能用安全更新命令。

### 9.6 提示缓存升级

直接调用提示缓存安装器时仍默认保留已有规则、观测资产和 skill。只有明确给出 `--apply --overwrite` 才会替换它们。

---

## 10. 安全与幂等性保障

| 保障项 | 说明 |
|--------|------|
| **默认 dry-run** | 首次操作优先使用 `--dry-run` 或 `--check` |
| **不覆盖学习记录** | `--overwrite` 不覆盖 `.learnings/` |
| **保留无关 hooks** | self-learning 的 `--overwrite` 不删除无关 hook 配置 |
| **入口文件安全** | env 的 `--overwrite` 只更新标记区块，不影响其他内容 |
| **Workflow 可重复** | 安装器可重复执行；内容不同时需显式 `--force` |
| **注册表精确管理** | 只删除上次同步标记为受管但已不存在的 skill |
| **密钥不泄露** | 审计报告只含文件、行号和规则名，不输出凭证原文 |
| **显式覆盖** | `--overwrite`、`--force-workflow` 和 `--force-manifest-platform` 必须由用户明确指定 |
| **更新前备份** | 更新器把将改动的现有文件备份到 `.agent-template-kits/backups/<时间戳>/` |
| **冲突逐项确认** | 更新器检测到冲突时停止，每个冲突路径需显式 `--accept` |
| **符号链接保护** | 安全更新拒绝包含符号链接的目标目录 |
| **路径安全** | 多 Agent 同步要求所有路径为非空、项目相对的 POSIX 路径 |
| **MCP 凭证安全** | `mcp-servers.json` 中使用环境变量引用，不直接存放凭证 |

---

## 11. 验证与质量检查

### 模板仓库自检

```bash
# 综合验证：语法检查 + 临时目录安装 smoke test + 回归测试
scripts/validate.sh

# 环境变量模板检查
.codex/scripts/check-env-template.sh --strict

# Workflow 路由注册表检查
.codex/scripts/sync-workflow-routing.sh --check

# 密钥安全审计
skills/security-secret-audit/scripts/audit-secrets.sh

# 空白错误检查
git diff --check
```

> GitHub Actions 会对 push 到 `main` 和 pull request 执行同类检查（覆盖 Ubuntu、macOS、Windows 三平台）。

### 辅助验证脚本

```bash
# 验证 profile YAML 合同完整性
python3 scripts/validate-profiles.py

# 验证文档覆盖所有组件
python3 scripts/check-docs.py

# 将 skills/ 中规范源同步到 .agents/skills/（自身使用）
python3 scripts/sync-runtime-skills.py

# 检查 skills/ 与 .agents/skills/ 是否同步
python3 scripts/sync-runtime-skills.py --check
```

### 目标项目验证

```bash
cd "$TARGET"

# 验证 env 安装（如有 .env.example）
.codex/scripts/check-env-template.sh --strict

# 验证 workflow 路由注册表
.codex/scripts/sync-workflow-routing.sh --check
```

> Claude Code 对应路径为 `.claude/scripts/`，generic profile 对应路径为 `.agent/scripts/`。

---

## 12. 常见问题

### Q: 安装器会修改我的项目代码吗？

不会。安装器只写入 agent 配置目录（如 `.codex/`、`.claude/`）、skills 目录、学习记录目录和入口规则文件的标记区块。不会改动业务代码。建议安装后先检查 `git diff` 再提交。

### Q: 我的项目已经有 hook 配置，安装会覆盖吗？

不会。self-learning 的安装器会合并 hook 配置，保留既有的无关设置。`--overwrite` 也只更新受管的 skill 和 hook 脚本。多 Agent 同步的 `bootstrap.py` 也只替换受管的 Python hook 命令。

### Q: Windows 上可以使用吗？

可以。Python 脚本可直接在 Windows 上运行（使用 `py -3` 或 `python`）。Bash 脚本需要 Git Bash 或 WSL。统一安装器会自动查找系统 Bash 和常见 Git for Windows 路径；找不到时会明确提示，不会写入目标项目。生成的 hooks 在 Windows 上使用 `python.exe`。

### Q: 提示缓存的可观测性（`--with-observability`）什么时候用？

仅当你的 Agent 已接通能自动记录 provider usage 的 API 调用后使用。直接使用 Codex 而没有项目 API 的场景，不要加此选项，也无需手填 token 或费用。

### Q: 密钥审计能检测哪些类型的凭证？

支持检测：Provider 特定格式的 API Key、Token、密码、私钥、JWT 等。高置信度模式扫描所有文本文件；低置信度变量名检查限制在配置类文件中，避免生成代码噪声。报告绝不输出凭证原文。

### Q: 安装后如何卸载？

本产品没有专门的卸载器。删除安装时创建的目录和文件即可（如 `.codex/skills/`、`.learnings/` 等）。建议在安装前用 `--dry-run` 预览所有变更，记录将创建的文件列表。

### Q: 更新模板时我的定制内容会被覆盖吗？

不会。更新器通过 `install-state.json` 中的文件指纹区分模板变更与项目定制。如果检测到受管文件被项目修改，会标记为 `[CONFLICT]` 并停止，需要你逐个用 `--accept` 确认。应用前还会自动备份到 `.agent-template-kits/backups/`。

### Q: 多 Agent 同步的 bootstrap.py 生成的文件需要提交吗？

不需要。`hooks.json`、`settings.json` 等本机配置文件已在 `.gitignore` 中。它们包含当前主机的 Python 解释器路径，每台机器不同。在新机器克隆后需重新执行 `bootstrap.py --apply`。

---

## 13. 目录结构参考

### 安装后的目标项目（以 Codex 为例）

```text
target-project/
├── .agents/skills/
│   ├── digest/
│   ├── maintain-learnings/
│   ├── prompt-cache-optimizer/
│   ├── sync-skill-registry/
│   └── workflow-todo-state/
├── .codex/
│   ├── hooks/
│   ├── rules/
│   ├── scripts/
│   └── workflows/
├── .learnings/
├── workspace/workflow-runs/
├── .codex/hooks.json          # 由 bootstrap.py 生成（gitignored，每台主机不同）
└── AGENTS.md
```

> `.codex/hooks.json` 是受忽略的主机本地文件，由多 Agent 同步 runtime 的 `bootstrap.py` 自动生成。在克隆仓库后需先安装 `.agent-sync` 并执行 `bootstrap.py --apply` 生成该文件。

> 仅在项目已接通自动 LLM usage 采集时，才会额外出现 `/.llm/prompt-cache/`。

> 安装了 `multi-agent-sync` 的项目会额外出现 `.agent-sync/` 目录；安装了 `manifest-platform` 的项目会额外出现 `.codex/platform/` 目录。

### 本模板仓库的目录职责

```text
profiles/       内置 Agent 布局合同（12 种内置 Profile）
templates/      可安装的规则、hook 和初始文件
skills/         可独立分发的 skill 包和工具（8 个功能模块）
.agents/        本仓库自身使用的 Codex skills（由 sync-runtime-skills.py 同步 skills/ 镜像）
.codex/         本仓库自身使用的 rules、hooks 和 workflows
.agent-sync/    多 Agent 同步 runtime
scripts/        仓库级验证命令（validate.sh、install.py、sync-runtime-skills.py 等）
tests/          安装、升级和状态转移回归测试
docs/           便携性说明 + 设计方案（superpowers/）+ 完整功能文档
```

---

## 14. 发布流程

本仓库使用语义化版本和 Git 标签发布。版本标签格式为 `vX.Y.Z`：

- **主版本**（X）：破坏兼容性时递增
- **次版本**（Y）：新增兼容能力时递增
- **修订版本**（Z）：修复或文档修正时递增

### 发布前

1. 将本次面向用户的变更写入 `CHANGELOG.md`，用明确的版本标题和日期替换 `Unreleased` 下对应内容
2. 在干净工作树中运行验证：

```bash
bash scripts/validate.sh
bash skills/security-secret-audit/scripts/audit-secrets.sh
```

3. 确认两个命令均以状态码 `0` 结束，并检查 `git diff --check` 没有空白错误

### 发布

1. 提交版本、变更日志和相关文档
2. 创建带说明的标签：

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z"
```

3. 推送提交和标签：

```bash
git push origin main --follow-tags
```

4. 在托管平台发布对应 Release，并复制该版本的变更说明

> 不要为历史提交补造版本标签；从下一次经过完整验证的公开发布开始使用此流程。

---

## 进一步阅读

| 文档 | 说明 |
|------|------|
| [README.md](../README.md) | 项目主文档（技术细节） |
| [CHANGELOG.md](../CHANGELOG.md) | 更新日志 |
| [docs/PORTABILITY.md](PORTABILITY.md) | 跨 Agent 与跨平台接入指南 |
| [RELEASING.md](../RELEASING.md) | 发布流程说明 |
| [profiles/README.md](../profiles/README.md) | Agent Profile 字段说明 |
| [templates/self-learning/README.md](../templates/self-learning/README.md) | 自学习模板详解 |
| [templates/cache/README.md](../templates/cache/README.md) | 提示缓存模板详解 |
| [templates/env/README.md](../templates/env/README.md) | 环境变量模板详解 |
| [skills/workflow-todo-state/SKILL.md](../skills/workflow-todo-state/SKILL.md) | Workflow Todo State 技能文档 |
| [skills/sync-skill-registry/SKILL.md](../skills/sync-skill-registry/SKILL.md) | 技能注册表同步文档 |
| [skills/security-secret-audit/SKILL.md](../skills/security-secret-audit/SKILL.md) | 密钥安全审计文档 |
| [skills/multi-agent-sync/SKILL.md](../skills/multi-agent-sync/SKILL.md) | 多 Agent 同步文档 |
| [skills/manifest-platform/SKILL.md](../skills/manifest-platform/SKILL.md) | Manifest Platform 文档 |

---

*本文档基于 Agent Template Kits 仓库当前版本编写。如有疑问，请参阅上述进一步阅读中的对应文档。*
