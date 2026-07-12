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

# 查看所有可用模板
ls -d templates/*/

# 安装自学习模板到目标项目
python templates/self-learning/install.py --target /path/to/your/project

# 同步技能注册表
python sync-skill-registry/scripts/sync_skill_registry.py --dry-run
```

## 理念

每个 Claude Code 项目都需要一些基础能力：管理技能注册表、记录经验教训、优化提示缓存……这些能力与具体业务无关，可以独立抽取、复用。

本项目就是这些通用组件的**源仓库**——当你开启一个新项目时，可以把这里的东西拷贝过去，而不是从零开始。

## 目录结构

```
.
├── sync-skill-registry/        # 技能注册表同步工具
│   ├── SKILL.md                # 技能定义
│   └── scripts/
│       └── sync_skill_registry.py
├── workflow-todo-state/        # Workflow Todo State 状态机
│   ├── SKILL.md                # 技能定义
│   ├── agents/
│   │   └── openai.yaml
│   ├── references/
│   │   ├── basic-todo-template.md
│   │   └── integration.md
│   └── scripts/
│       ├── install.sh
│       └── todo-state.sh
├── templates/                  # 可移植模板包
│   ├── cache/                  #   提示缓存优化模板
│   │   ├── README.md
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

### `workflow-todo-state/` — Workflow 状态机

为多步骤 Agent 工作流提供可恢复的进度追踪。基于人类可读的 Markdown 清单 + YAML frontmatter + 确定性状态脚本。

- 将 `todo.md` 中的状态抽象为 **⬜ 未开始 / 🔲 进行中 / ✅ 已完成 / ⏭️ 跳过 / 🚫 阻塞** 五种状态
- `todo-state.sh` 脚本提供 `start`、`complete`、`skip`、`block` 等原子操作，自动校验前驱阶段
- 支持 phase gate：启动某个阶段前自动检查前置阶段是否已完成
- `block` 状态记录阻塞原因，`skip` 追加跳过原因到异常记录表

**安装方式**：

```bash
.claude/skills/workflow-todo-state/scripts/install.sh /path/to/target-project --with-skill --update-agents
```

### `templates/cache/` — 提示缓存优化模板

帮助你在 Claude Code 项目中最大化提示缓存命中率的规则和手册。

- **`prompt-cache-rules.md`**：完整规则集，包括固定前缀、延迟加载、标准提示模板结构等
- **`prompt-cache-playbook.md`**：实施手册，包含反例、推荐目录布局和上线检查清单

**使用方式**：将规则文件复制到 `.claude/rules/` 下，相关规则会自动被 Claude Code 加载。

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
2. **每个组件都自包含**：目录下有完整的 `SKILL.md`、脚本和模板，复制即可用
3. **修改 .claude/settings.json**：根据目标项目调整权限和 hooks
4. **运行 sync-skill-registry**：如果新增了技能，运行同步脚本更新注册表

## 开发指南

- 所有技能使用统一的 frontmatter 格式（name、description、category）
- 技能脚本放在对应目录的 `scripts/` 下
- 模板包需要附带安装脚本或清晰的 README 说明
