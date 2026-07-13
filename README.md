# Skill Templates & Toolkits

<p align="left">
  <img src="https://img.shields.io/badge/Claude_Code-5.0+-purple" alt="Claude Code">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/status-maintained-brightgreen" alt="Status">
</p>

可复用到其他 Claude Code 项目的技能（Skills）、规则（Rules）和模板（Templates）集合。

> 此项目最初是**考研（研究生入学考试）Claude Code 技能集合**（含路由器架构 v4.0.0、数学/英语/电子技术等 17+ 个技能），于 2026 年重构为通用的技能模板与工具集仓库。

---

**快速开始**

```bash
# 克隆到本地
git clone git@github.com:Treasoni/template_ai.git

# 查看所有可用组件
ls -d */

# 安装自学习模板到目标项目
python templates/self-learning/install.py --target /path/to/your/project

# 安装提示缓存规则（检查模式，不会写入）
bash templates/cache/prompt-cache-bootstrap.sh --check --platform both --target /path/to/project

# 安装 workflow 状态机
.claude/skills/workflow-todo-state/scripts/install.sh /path/to/target-project --with-skill --init-layout

# 同步技能注册表（预览模式）
python sync-skill-registry/scripts/sync_skill_registry.py --dry-run
```

## 理念

每个 Claude Code 项目都需要一些基础能力：管理技能注册表、记录经验教训、优化提示缓存……这些能力与具体业务无关，可以独立抽取、复用。

本项目就是这些通用组件的**源仓库**——当你开启一个新项目时，可以把这里的东西拷贝过去，而不是从零开始。

## 目录结构

```
.
├── prompt-cache-optimizer/     # 提示缓存优化技能
│   ├── SKILL.md                # 技能定义
│   ├── agents/
│   │   └── openai.yaml
│   ├── assets/
│   │   ├── llm-usage-event.schema.json
│   │   └── prompt-cache-regression-cases.json
│   ├── references/
│   │   └── measurement.md
│   └── scripts/
│       └── prompt-cache-bootstrap.sh
├── security-secret-audit/      # 密钥泄露审计工具
│   ├── SKILL.md                # 技能定义
│   ├── agents/
│   │   └── openai.yaml
│   └── scripts/
│       ├── audit-secrets.sh
│       └── detect-secrets.pl
├── sync-skill-registry/        # 技能注册表同步工具
│   ├── SKILL.md                # 技能定义
│   └── scripts/
│       └── sync_skill_registry.py
├── workflow-todo-state/        # Workflow 状态机（多工作流版）
│   ├── SKILL.md                # 技能定义
│   ├── AGENTS_s.MD             # Agents 入口片段
│   ├── agents/
│   │   └── openai.yaml
│   ├── references/
│   │   ├── basic-state-template.md        # 状态文件模板（替代旧 todo.md）
│   │   ├── workflow-routing-template.md   # 工作流路由定义模板
│   │   └── integration.md                 # 集成指南
│   └── scripts/
│       ├── install.sh
│       └── todo-state.sh
├── templates/                  # 可移植模板包
│   ├── cache/                  #   提示缓存优化模板
│   │   ├── README.md
│   │   ├── prompt-cache-bootstrap.sh  #   一键安装 & 审计脚本
│   │   ├── prompt-cache-rules.md
│   │   ├── prompt-cache-playbook.md
│   │   └── AGENTS-cache-snippet.md
│   └── self-learning/          #   自学习技能模板包
│       ├── README.md
│       ├── install.py          #   一键安装脚本
│       ├── hooks/
│       │   ├── claude-settings.json.template
│       │   ├── codex-hooks.json.template
│       │   └── read-learnings.sh
│       ├── learnings/          #   学习记录模板（空，用于初始化）
│       │   ├── ERRORS.md
│       │   ├── LEARNINGS.md
│       │   └── RULES.md
│       └── skills/
│           ├── digest/         #     会话总结技能
│           └── maintain-learnings/  # 学习记录维护技能
├── .claude/
│   └── settings.json           # Claude Code 配置（权限等）
├── .gitignore
└── README.md
```

## 组件说明

### `sync-skill-registry/` — 技能注册表同步

自动管理 `.claude/rules/common/skill-invocation.md` 中的技能表格。

- 扫描 `.claude/skills/*/SKILL.md` 中的 frontmatter（name、description、category）
- 自动增删改技能条目，保持注册表与真实技能文件一致
- 支持 `--dry-run` 预览模式

**使用方式**：将此目录和脚本复制到目标项目中，注册为 Claude Code 技能即可。

### `workflow-todo-state/` — Workflow 状态机（多工作流版）

为多步骤 Agent 工作流提供可恢复的进度追踪。**v2 升级**：从单一 `todo.md` 演进为**命名工作流 + 运行实例分离**架构。

- **工作流定义**：每个工作流在 `.claude/workflows/{workflow-id}/` 下独立管理，含 `workflow.md`、`state-template.md`、`routing.yaml`
- **运行实例**：状态文件存放在 `workspace/workflow-runs/{task}.workflow.md`，按任务命名，而非笼统的 `todo.md`
- **路由注册表**：`sync-workflow-routing.sh` 扫描所有 `routing.yaml` 生成路由表，支持 `--check` 校验模式
- **状态脚本**：`todo-state.sh` 提供 `start / complete / skip / block` 原子操作，支持 phase gate 校验
- **五种状态**：⬜ 未开始 / 🔲 进行中 / ✅ 已完成 / ⏭️ 跳过 / 🚫 阻塞

**安装方式**：

```bash
.claude/skills/workflow-todo-state/scripts/install.sh /path/to/target-project --with-skill --init-layout --update-agents
```

### `prompt-cache-optimizer/` — 提示缓存优化技能

以项目真实的提示构造、调用日志和回归样本为依据，审计并优化 LLM 提示缓存命中率。

- **`prompt-cache-bootstrap.sh`**：安装或检查规则、调用事件 schema 和回归样本
- **`references/measurement.md`**：指标接入与对比方法
- **`assets/llm-usage-event.schema.json`**：调用日志字段合同
- **`assets/prompt-cache-regression-cases.json`**：脱敏、稳定的回归样本

**工作流**：确定范围 → 安装检查 → 采集基线 → 分析优化 → 回归验证。不将缩短提示词或删除必要上下文误当成优化。

### `security-secret-audit/` — 密钥泄露审计工具

在提交前或怀疑凭据泄露时扫描 Git 仓库中的 API Key、Token、密码、私钥等敏感信息，**不输出凭证原文**。

- **`--staged`**：仅扫描已暂存的内容，适合提交前检查
- **`--history`**：扫描 Git 历史中所有文件版本，用于泄露溯源
- **`audit-secrets.sh`**：调用 `detect-secrets.pl` 执行扫描，分级报告结果

**安全规则**：发现结果按文件、行号、规则名报告，绝不泄露凭证值。清除后需重新扫描确认。

### `templates/cache/` — 提示缓存优化模板

帮助你在 Claude Code 项目中最大化提示缓存命中率的规则、手册和自动化工具。

| 文件 | 用途 |
| --- | --- |
| **`prompt-cache-bootstrap.sh`** | 一键安装规则、更新入口文件、扫描常见缓存破坏项 |
| **`prompt-cache-rules.md`** | 完整规则集，包括固定前缀、延迟加载、标准提示模板结构等 |
| **`prompt-cache-playbook.md`** | 实施手册，包含反例、推荐目录布局和上线检查清单 |
| **`AGENTS-cache-snippet.md`** | 可粘贴到 AGENTS.md 的精简入口规则 |

**快速安装**：

```bash
# 先检查目标项目（不会写文件）
bash templates/cache/prompt-cache-bootstrap.sh --check --platform both --target /path/to/project

# 确认后安装
bash templates/cache/prompt-cache-bootstrap.sh --apply --platform both --target /path/to/project
```

支持 Codex、Claude Code 或双平台。脚本幂等，重复执行安全。

### `templates/self-learning/` — 自学习技能模板包

一套完整的"让 Claude 从对话中学习"的模板，提供两个技能：

| 技能 | 功能 |
|------|------|
| **digest** | 每次会话结束后回顾，将真实的学习点和错误记录到 `.learnings/` |
| **maintain-learnings** | 审计学习记录、去重、追溯根源并修复，同步 Claude Code 和 Codex 双平台 |

**安装方式**：

```bash
python templates/self-learning/install.py --target <你的项目路径>
```

或手动将对应目录复制到目标项目的 `.claude/skills/` 和 `.agents/skills/` 下。

## 如何复用到新项目

1. **按需拷贝**：本项目不是 npm 包或 git submodule —— 它是源仓库，你应该把需要的组件 **复制** 到目标项目中
2. **优先使用安装脚本**：多数组件提供 `install.sh` 或 `*-bootstrap.sh`，支持幂等安装和 `--check` 预览模式
3. **每个组件都自包含**：目录下有完整的 `SKILL.md`、脚本和模板，复制即可用
4. **修改 .claude/settings.json**：根据目标项目调整权限和 hooks
5. **运行 sync-skill-registry**：如果新增了技能，运行同步脚本更新注册表

## 开发指南

- 所有技能使用统一的 frontmatter 格式（name、description、category）
- 技能脚本放在对应目录的 `scripts/` 下
- 模板包需要附带安装脚本或清晰的 README 说明
