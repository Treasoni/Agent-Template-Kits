---
workflow_id: reusable-agent-assets
workflow_name: Reusable Agent Assets
workflow_version: 1
state_file_type: workflow-run
run_id: "core-refactor"
task: "Refactor installer, workflow state, profile, and validation foundations"
created_from: ".codex/workflows/reusable-agent-assets/state-template.md"
created_at: "2026-07-15"
last_updated: "2026-07-15"
current_phase: done
current_status: complete
mode: standard
blocked_reason: ""
---

# Reusable Agent Assets - Core Refactor

> 工作流：reusable-agent-assets
> 任务：重构安装器、workflow 状态、profile 配置和验证基础
> 运行标识：core-refactor
> 创建时间：2026-07-15
> 当前阶段：完成
> 状态图例：⬜ 未开始 | 🔲 进行中 | ✅ 已完成 | ⏭️ 跳过

---

## 阶段 0：Intake And Boundaries

> [P0] ✅ 已完成

## 阶段 1：Classification And Placement Plan

> [P1] ✅ 已完成

## 阶段 2：Package And Normalize

> [P2] ✅ 已完成

## 阶段 3：Integrate Registries

> [P3] ✅ 已完成

## 阶段 4：Verify

> [P4] ✅ 已完成

## 阶段 5：Finish And Hand Off

> [P5] ✅ 已完成

## 异常记录

| 时间 | 阶段 | 问题描述 | 处理方式 |
|------|------|---------|---------|

## 输入材料

- 用户目标：实施项目审查中确认的聚焦式重构。
- 范围：self-learning 安装器、workflow 安装/状态、skill registry、profile 配置、回归验证。
- 保护：不回退当前工作区中的迁移改动，不覆盖用户数据。

## 放置计划

| 输入 | 类型 | 目标位置 | 处理方式 |
|------|------|----------|----------|
| 安装器与 profile | script/config | `templates/`, `profiles/` | 安全更新并减少硬编码 |
| workflow 状态 | skill/script | `skills/workflow-todo-state/` | 修复幂等与状态转移 |
| 技能注册表 | skill/script | `skills/sync-skill-registry/` | 修复受管条目删除 |
| 验证 | tests/script | `tests/`, `scripts/validate.sh` | 增加回归覆盖 |

## 最终产出

- 输出文件：安全的 self-learning/env 安装器、profile 运行时合同、幂等 workflow 安装器、终态保护、受管 skill registry、8 个回归测试、GitHub Actions 验证。
- 同步/验证命令：`scripts/validate.sh`、`.codex/scripts/check-env-template.sh --strict`、`.codex/scripts/sync-workflow-routing.sh --check`、skill registry dry-run、secret audit、`git diff --check`。
- 未来触发表达：“重构可复用 skill/rule/template”、“封装成可复用 agent 资产”、“把这些 rules 放到合适位置”。
- 完成状态：已完成，无跳过项、无阻塞项。
