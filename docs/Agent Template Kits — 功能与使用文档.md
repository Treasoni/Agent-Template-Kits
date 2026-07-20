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

### 设计理念

- **模板源而非应用**：克隆后安装到目标项目，不改动目标项目已有结构
- **安全优先**：所有操作默认 dry-run 预览，确认后才执行
- **幂等可重复**：安装器可安全重复执行，不会覆盖已有定制内容
- **跨平台跨 Agent**：一套模板，适配 12 种主流 AI 编程助手

---

## 2. 核心功能

本产品包含 **8 大功能模块**，可单独安装，也可组合使用：

### 2.1 自学习系统（Self-Learning）

让 AI 编程助手在每次会话开始时自动加载历史经验。

- **`digest` 技能**：记录本次任务中真实发生的学习点和错误
- **`maintain-learnings` 技能**：当经验库变长或错误反复出现时，先修源头（skill/模板/hook/规则），再归档已解决记录
- **自动加载 Hook**：会话启动时自动读取 `.learnings/RULES.md`、`ERRORS.md` 和最近的 `LEARNINGS.md`

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

- 以一个 canonical profile 为源，同步 skills、rules、hooks、scripts、workflows 和 MCP 配置
- 先用 `--check` 审阅漂移，再只对受影响 scope 使用 `--apply`
- `maintain-learnings` 只维护经验库，不再承担 profile 同步职责

### 2.8 Agent Manifest Platform

- 为 workflow、skill、hook 和 subagent 建立可验证的版本、能力和权限合同
- 通过 registry validator 发现缺失 manifest、无效入口或不允许的权限

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

---

## 4. 运行环境要求

| 工具 | 用途 | 要求 |
|------|------|------|
| **Git** | 克隆模板、密钥审计 | 建议安装 |
| **Python 3** | 安装器、hooks、注册表 | 必需 |
| **Bash** | Shell 安装器和检查脚本 | Linux、macOS、WSL 或 Git Bash |
| **ripgrep (`rg`)** | 严格 env 检查 | 使用 env 检查时必需 |
| **Perl** | workflow 状态和密钥检测 | 使用对应组件时必需 |

> **Windows 用户**：Python 脚本可直接运行。Bash 脚本需要安装 Git for Windows（提供 Git Bash）或使用 WSL。统一安装器会自动查找系统 Bash 和常见 Git Bash 安装路径。

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

### 第三步：自动检测并安装（推荐）

```bash
# 1. 只检测，不修改目标项目——查看自动识别结果
python3 scripts/install.py --target "$TARGET" --detect

# 2. 预览安装计划（仍不写入）
python3 scripts/install.py --target "$TARGET" --use-detected

# 3. 确认后执行安装
python3 scripts/install.py \
  --target "$TARGET" \
  --use-detected \
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

### 6.2 安装器行为

- **默认 dry-run**：先预览将执行的命令，不修改目标项目
- **自动检测**：根据目标项目已有的 agent 目录、配置和入口文件推荐 Profile，并显示检测证据
- **手动选择**：`--profile <name>` 指定单个 Profile
- **多 Profile 支持**：可重复使用 `--profile` 安装到多个 Agent
- **确认机制**：`--apply` 时要求确认；非交互环境需显式 `--yes`
- **完整 Skill 复制**：`prompt-cache-optimizer`、`workflow-todo-state`、`sync-skill-registry` 和按需选择的 `manifest-platform` 会一并复制到目标项目

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

> 可观测性（`--with-observability`）：仅当 Agent 已接通自动 LLM usage 采集时使用。它会安装 `/.llm/prompt-cache/` 的 schema 和回归样本。直接使用 Codex 时不要加此选项。

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
```

**退出码：**
| 退出码 | 含义 |
|--------|------|
| `0` | 无发现，安全 |
| `2` | 发现潜在凭证，应阻止提交 |
| `1` | 扫描器错误，需排查 |

### 7.7 多 Agent 同步与 Manifest Platform

跨 profile 同步由 `multi-agent-sync` 独立完成，经验库维护仍由 `maintain-learnings` 负责：

```bash
python3 scripts/install.py --target "$TARGET" --profile codex \
  --components multi-agent-sync --apply --yes
python3 "$TARGET/.agent-sync/sync_agents.py" --root "$TARGET" --check --scope skills
python3 "$TARGET/.agent-sync/sync_agents.py" --root "$TARGET" --apply --scope skills
```

需要资产合同和权限校验时，显式安装 manifest platform：

```bash
python3 scripts/install.py --target "$TARGET" --profile codex \
  --components manifest-platform --apply --yes
python3 "$TARGET/.codex/platform/manifest-registry.py" --root "$TARGET" validate
```

---

## 8. 自定义 Agent 接入

如果你的 AI 编程助手不在内置列表中，可以通过以下方式接入：

### 方式一：创建 YAML Profile（推荐）

创建一个与 `profiles/*.yaml` 字段一致的 scalar YAML 文件：

```yaml
name: myagent
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

```bash
# 1. 更新本模板仓库
git pull --ff-only

# 2. 重新运行安装器（加 --overwrite 更新受管内容）
python3 templates/self-learning/install.py --target "$TARGET" --profile codex --overwrite
python3 templates/env/install.py --target "$TARGET" --profile codex --overwrite

# 3. Workflow 安装器可重复执行
bash skills/workflow-todo-state/scripts/install.sh \
  "$TARGET" --profile codex --with-skill --init-layout --update-agents
```

**更新安全说明：**
- self-learning 的 `--overwrite` 不覆盖 `.learnings/`，也不删除无关 hook 配置
- env 的 `--overwrite` 替换受管规则和脚本，但入口文件只更新对应 profile 标记区块
- workflow 源码升级且目标文件不同时，需显式 `--force`；旧文件自动备份到 `.bak.*`
- 提示缓存升级时应先 `--check`，再手工评估是否替换

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
| **显式覆盖** | `--overwrite` 和 `--force-workflow` 必须由用户明确指定 |

---

## 11. 验证与质量检查

### 模板仓库自检

```bash
scripts/validate.sh
.codex/scripts/check-env-template.sh --strict
.codex/scripts/sync-workflow-routing.sh --check
skills/security-secret-audit/scripts/audit-secrets.sh
git diff --check
```

`scripts/validate.sh` 包含语法检查、临时目录安装 smoke test 和 `tests/` 回归测试。

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

不会。self-learning 的安装器会合并 hook 配置，保留既有的无关设置。`--overwrite` 也只更新受管的 skill 和 hook 脚本。

### Q: Windows 上可以使用吗？

可以。Python 脚本可直接在 Windows 上运行。Bash 脚本需要 Git Bash 或 WSL。统一安装器会自动查找系统 Bash 和常见 Git for Windows 路径；找不到时会明确提示，不会写入目标项目。

### Q: 提示缓存的可观测性（`--with-observability`）什么时候用？

仅当你的 Agent 已接通能自动记录 provider usage 的 API 调用后使用。直接使用 Codex 而没有项目 API 的场景，不要加此选项，也无需手填 token 或费用。

### Q: 密钥审计能检测哪些类型的凭证？

支持检测：Provider 特定格式的 API Key、Token、密码、私钥、JWT 等。高置信度模式扫描所有文本文件；低置信度变量名检查限制在配置类文件中，避免生成代码噪声。报告绝不输出凭证原文。

### Q: 安装后如何卸载？

本产品没有专门的卸载器。删除安装时创建的目录和文件即可（如 `.codex/skills/`、`.learnings/` 等）。建议在安装前用 `--dry-run` 预览所有变更，记录将创建的文件列表。

---

## 13. 目录结构参考

### 安装后的目标项目（以 Codex 为例）

```text
your-project/
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
├── .codex/hooks.json
└── AGENTS.md
```

> 仅在项目已接通自动 LLM usage 采集时，才会额外出现 `/.llm/prompt-cache/`。

### 本模板仓库的目录职责

```text
profiles/       内置 Agent 布局合同（12 种内置 Profile）
templates/      可安装的规则、hook 和初始文件
skills/         可独立分发的 skill 包和工具（6 个功能模块）
scripts/        仓库级验证命令和统一安装器
tests/          安装、升级和状态转移回归测试
docs/           便携性和第三方 Agent 接入说明
```

---

## 进一步阅读

| 文档 | 说明 |
|------|------|
| [README.md](../README.md) | 项目主文档（技术细节） |
| [CHANGELOG.md](../CHANGELOG.md) | 更新日志 |
| [docs/PORTABILITY.md](PORTABILITY.md) | 跨 Agent 与跨平台接入指南 |
| [profiles/README.md](../profiles/README.md) | Agent Profile 字段说明 |
| [templates/self-learning/README.md](../templates/self-learning/README.md) | 自学习模板详解 |
| [templates/cache/README.md](../templates/cache/README.md) | 提示缓存模板详解 |
| [templates/env/README.md](../templates/env/README.md) | 环境变量模板详解 |
| [skills/workflow-todo-state/SKILL.md](../skills/workflow-todo-state/SKILL.md) | Workflow Todo State 技能文档 |
| [skills/sync-skill-registry/SKILL.md](../skills/sync-skill-registry/SKILL.md) | 技能注册表同步文档 |
| [skills/security-secret-audit/SKILL.md](../skills/security-secret-audit/SKILL.md) | 密钥安全审计文档 |

---

*本文档基于 Agent Template Kits 仓库当前版本编写。如有疑问，请参阅上述进一步阅读中的对应文档。*
