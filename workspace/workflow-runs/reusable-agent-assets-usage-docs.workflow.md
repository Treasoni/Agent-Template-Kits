---
workflow_id: reusable-agent-assets
workflow_name: Reusable Agent Assets
workflow_version: 1
state_file_type: workflow-run
run_id: "usage-docs"
task: "Rewrite project usage documentation"
created_from: ".codex/workflows/reusable-agent-assets/state-template.md"
created_at: "2026-07-15"
last_updated: "2026-07-15"
current_phase: done
current_status: complete
mode: standard
blocked_reason: ""
---

# Reusable Agent Assets - Usage Documentation

> 工作流：reusable-agent-assets
> 任务：重写项目使用说明
> 运行标识：usage-docs
> 创建时间：2026-07-15
> 当前阶段：完成

## 阶段 0：Intake And Boundaries

> [P0] ✅ 已完成

## 阶段 1：Classification And Placement Plan

> [P1] ✅ 已完成

## 阶段 2：Package And Normalize

> [P2] ✅ 已完成

## 阶段 3：Integrate Registries

> [P3] ⏭️ 跳过

## 阶段 4：Verify

> [P4] ✅ 已完成

## 阶段 5：Finish And Hand Off

> [P5] ✅ 已完成

## 异常记录

| 时间 | 阶段 | 问题描述 | 处理方式 |
|------|------|---------|---------|
| 2026-07-15 11:50 | P3 | 跳过阶段：only README documentation changed; no registry integration required | 继续推进到下一未完成阶段 |

## 放置计划

- 主入口：`README.md`
- 详细便携性参考：`docs/PORTABILITY.md`
- 验证：命令可执行性、链接、`scripts/validate.sh`、`git diff --check`

## 最终产出

- 输出文件：`README.md`，包含前置要求、profile 选择、Codex/Claude/generic 安装、单组件使用、自定义 Agent、升级、安全行为、验证和目录职责。
- 验证：README 本地链接通过；Codex 完整安装配方在临时项目中通过；`scripts/validate.sh` 和 8 个回归测试通过；`git diff --check` 通过。
- 完成状态：已完成。
