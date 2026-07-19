---
workflow_id: reusable-agent-assets
workflow_name: Reusable Agent Assets
workflow_version: 1
state_file_type: workflow-run
run_id: "multi-agent-sync"
task: "Package multi-agent-sync as an installable reusable skill"
created_from: ".codex/workflows/reusable-agent-assets/state-template.md"
created_at: "2026-07-19"
last_updated: "2026-07-19"
current_phase: P0
current_status: not_started
mode: standard
blocked_reason: ""
---

# Reusable Agent Assets - Workflow Run

> 工作流：reusable-agent-assets
> 任务：{task}
> 运行标识：{run_id}
> 创建时间：{date}
> 当前阶段：阶段 0
> 状态图例：⬜ 未开始 | 🔲 进行中 | ✅ 已完成 | ⏭️ 跳过

---

## 阶段 0：Intake And Boundaries

- [ ] 已读取用户原始请求和本状态文件
- [ ] 已盘点用户提供或引用的所有材料
- [ ] 已识别候选类型：skill、rule、workflow、template、hook、script、doc 或混合包
- [ ] 已确认没有需要阻塞处理的密钥、凭证或安全问题

> [P0] ⬜ 未开始

---

## 阶段 1：Classification And Placement Plan

- [ ] 每个输入项已映射到一个主要目标位置
- [ ] 已检查相关现有资产，避免覆盖用户未要求修改的内容
- [ ] 已决定新建、更新或跳过的文件清单
- [ ] 已记录计划执行的验证命令

> [P1] ⬜ 未开始

---

## 阶段 2：Package And Normalize

- [ ] 已按项目风格创建或更新目标文件
- [ ] 已移除一次性路径、过期示例和不适合复用的上下文
- [ ] 已保留用户意图并补足必要结构
- [ ] 已让稳定说明位于动态示例和运行时数据之前

> [P2] ⬜ 未开始

---

## 阶段 3：Integrate Registries

- [ ] 如涉及 workflow，已同步并检查 routing 表
- [ ] 如涉及共享 skill，已运行平台 skill 同步脚本
- [ ] 如涉及 hook，已检查 `.codex/hooks.json`
- [ ] 如涉及早期加载规则，已最小化更新 `AGENTS.md`

> [P3] ⬜ 未开始

---

## 阶段 4：Verify

- [ ] 已运行适用的语法检查或项目验证脚本
- [ ] 已检查 `git diff --check`
- [ ] 已确认未回退无关用户变更
- [ ] 已记录任何未运行验证及原因

> [P4] ⬜ 未开始

---

## 阶段 5：Finish And Hand Off

- [ ] 已记录最终产出路径
- [ ] 已记录验证结果
- [ ] 已列出触发该 workflow 的未来表达
- [ ] 已完成或说明所有跳过、阻塞项

> [P5] ⬜ 未开始

---

## 异常记录

| 时间 | 阶段 | 问题描述 | 处理方式 |
|------|------|---------|---------|
| | | | |

---

## 输入材料

- **来源路径/粘贴内容**：
- **用户目标**：
- **安全或隐私注意事项**：

## 放置计划

| 输入 | 类型 | 目标位置 | 处理方式 |
|------|------|----------|----------|
| | | | |

## 最终产出

- **输出文件**：
- **同步/验证命令**：
- **完成状态**：
