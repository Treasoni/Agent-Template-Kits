---
workflow_id: reusable-agent-assets
workflow_name: Reusable Agent Assets
workflow_version: 1
state_file_type: workflow-run
run_id: "prompt-cache-observability-20260716"
task: "将 prompt-cache-optimizer 的可观测性改为自动接入时才可选启用"
created_from: ".codex/workflows/reusable-agent-assets/state-template.md"
created_at: "2026-07-16"
last_updated: "2026-07-16"
current_phase: done
current_status: complete
mode: standard
blocked_reason: ""
---

# Reusable Agent Assets - Workflow Run

> 工作流：reusable-agent-assets
> 任务：将 prompt-cache-optimizer 的可观测性改为自动接入时才可选启用
> 运行标识：prompt-cache-observability-20260716
> 创建时间：2026-07-16
> 当前阶段：完成
> 状态图例：⬜ 未开始 | 🔲 进行中 | ✅ 已完成 | ⏭️ 跳过

---

## 阶段 0：Intake And Boundaries

- [x] 已读取用户原始请求和本状态文件
- [x] 已盘点用户提供或引用的所有材料
- [x] 已识别候选类型：skill、rule、workflow、template、hook、script、doc 或混合包
- [x] 已确认没有需要阻塞处理的密钥、凭证或安全问题

> [P0] ✅ 已完成

---

## 阶段 1：Classification And Placement Plan

- [x] 每个输入项已映射到一个主要目标位置
- [x] 已检查相关现有资产，避免覆盖用户未要求修改的内容
- [x] 已决定新建、更新或跳过的文件清单
- [x] 已记录计划执行的验证命令

> [P1] ✅ 已完成

---

## 阶段 2：Package And Normalize

- [x] 已按项目风格创建或更新目标文件
- [x] 已移除一次性路径、过期示例和不适合复用的上下文
- [x] 已保留用户意图并补足必要结构
- [x] 已让稳定说明位于动态示例和运行时数据之前

> [P2] ✅ 已完成

---

## 阶段 3：Integrate Registries

- [ ] 如涉及 workflow，已同步并检查 routing 表
- [ ] 如涉及共享 skill，已运行平台 skill 同步脚本
- [ ] 如涉及 hook，已检查 `.codex/hooks.json`
- [ ] 如涉及早期加载规则，已最小化更新 `AGENTS.md`

> [P3] ⏭️ 跳过

---

## 阶段 4：Verify

- [x] 已运行适用的语法检查或项目验证脚本
- [x] 已检查 `git diff --check`
- [x] 已确认未回退无关用户变更
- [x] 已记录任何未运行验证及原因

> [P4] ✅ 已完成

---

## 阶段 5：Finish And Hand Off

- [x] 已记录最终产出路径
- [x] 已记录验证结果
- [x] 已列出触发该 workflow 的未来表达
- [x] 已完成或说明所有跳过、阻塞项

> [P5] ✅ 已完成

---

## 异常记录

| 时间 | 阶段 | 问题描述 | 处理方式 |
|------|------|---------|---------|
| 2026-07-16 22:37 | P3 | 跳过阶段：技能位于仓库分发源 skills/，未修改 .agents/skills、workflow、hook 或早期加载规则，无注册表需要同步 | 继续推进到下一未完成阶段 |
| | | | |

---

## 输入材料

- **来源路径/粘贴内容**：`skills/prompt-cache-optimizer/`；用户反馈 `/.llm` 不能自动计算 Codex token，手填无意义。
- **用户目标**：默认不创建 `/.llm`；只有 agent 已确认可自动采集 API 调用指标时才可选启用。
- **安全或隐私注意事项**：采集不得写入原始提示词、响应、密钥或个人数据。

## 放置计划

| 输入 | 类型 | 目标位置 | 处理方式 |
|------|------|----------|----------|
| 现有 prompt-cache-optimizer | skill | `skills/prompt-cache-optimizer/SKILL.md` | 更新流程：agent 自动检查与接入；禁止手填指标。 |
| 安装脚本 | shell script | `skills/prompt-cache-optimizer/scripts/prompt-cache-bootstrap.sh` | 新增显式 `--with-observability`，默认跳过 `/.llm`。 |
| 指标说明 | reference | `skills/prompt-cache-optimizer/references/measurement.md` | 明确 schema 不是采集器，只有自动遥测时适用。 |
| 安装说明与测试 | docs/test | `README.md`、`scripts/validate.sh` | 移除默认 `/.llm` 的表述，并覆盖默认/可选两种行为。 |
| | | | |

## 最终产出

- **输出文件**：`skills/prompt-cache-optimizer/SKILL.md`、`skills/prompt-cache-optimizer/scripts/prompt-cache-bootstrap.sh`、`skills/prompt-cache-optimizer/references/measurement.md`、`README.md`、`scripts/validate.sh`。
- **同步/验证命令**：`bash -n skills/prompt-cache-optimizer/scripts/prompt-cache-bootstrap.sh`、`bash scripts/validate.sh`（通过，12 个回归测试）、Ruby YAML frontmatter 校验、`git diff --check`（通过）。`quick_validate.py` 因环境没有 `PyYAML` 未运行。
- **完成状态**：已完成。未来以“优化缓存命中”“降低 token 成本”“审计 LLM 调用”等表达触发；仅在项目 API usage 可由 agent 自动采集时启用观测性。
