---
workflow_id: reusable-agent-assets
workflow_name: Reusable Agent Assets
workflow_version: 1
state_file_type: workflow-run
run_id: "security-secret-audit-2026-08-11"
task: "Expand the security-secret-audit skill into a project-risk and API-leak audit with controlled remediation"
created_from: ".codex/workflows/reusable-agent-assets/state-template.md"
created_at: "2026-08-11"
last_updated: "2026-08-11"
current_phase: done
current_status: complete
mode: standard
blocked_reason: ""
---

# Reusable Agent Assets - Workflow Run

> 工作流：reusable-agent-assets
> 任务：Expand the security-secret-audit skill into a project-risk and API-leak audit with controlled remediation
> 运行标识：security-secret-audit-2026-08-11
> 创建时间：2026-08-11
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

- [x] 如涉及 workflow，已同步并检查 routing 表（未修改 workflow）
- [x] 如涉及共享 skill，已运行平台 skill 同步脚本
- [x] 如涉及 hook，已检查 `.codex/hooks.json`（未修改 hook）
- [x] 如涉及早期加载规则，已最小化更新 `AGENTS.md`（不需要早期加载规则）

> [P3] ✅ 已完成

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
|------|------|---------|
| 2026-08-11 | P4 | 完整验证与全量回归在严格 env 模板检查失败；该检查在干净 HEAD archive 中同样失败。 | 记录为既有基线问题；未扩大本次安全技能改动去修改 env 合同。 |
| | | | |

---

## 输入材料

- **来源路径/粘贴内容**：`skills/security-secret-audit/`；用户指定的 Grill-me 访谈约束。
- **用户目标**：审查项目风险和 API 泄漏风险；按风险分级实施可逆的低风险修复。
- **安全或隐私注意事项**：所有输出脱敏；默认不扫 Git 历史；不自动轮换或撤销凭证、不重写历史、不推送。

## 放置计划

| 输入 | 类型 | 目标位置 | 处理方式 |
|------|------|----------|----------|
| Security Secret Audit | 可分发 skill | `skills/security-secret-audit/` | 更新指南和扫描脚本；保持 canonical source。 |
| Project risk detector | skill script | `skills/security-secret-audit/scripts/detect-risks.pl` | 新增只输出位置和规则名的高置信度风险检测器。 |
| Runtime mirror | Codex runtime skill | `.agents/skills/security-secret-audit/` | 在同步器登记后生成。 |
| Runtime-skill registry | repository tool | `scripts/sync-runtime-skills.py` | 登记 canonical package 到 Codex runtime mirror。 |
| Regression coverage | quality tests | `tests/test_quality_guards.py` | 覆盖风险规则、脱敏、严格模式和修复预览。 |
| User documentation | README and guide | `README.md`, `skills/README.md`, `docs/Agent Template Kits — 功能与使用文档.md`, `docs/USER_GUIDE.html` | 说明新审查模式、退出码和受控修复边界。 |

## 最终产出

- **输出文件**：`skills/security-secret-audit/`，`.agents/skills/security-secret-audit/`，`scripts/sync-runtime-skills.py`，`tests/test_quality_guards.py`，`README.md`，`skills/README.md`，`docs/Agent Template Kits — 功能与使用文档.md`，`docs/USER_GUIDE.html`。
- **同步/验证命令**：`bash -n`、`perl -c`、`python3 -m unittest tests.test_quality_guards`、`python3 scripts/sync-runtime-skills.py --check`、`git diff --check`；项目完整 `scripts/validate.sh` 和全量 unittest 的既有 strict env 失败已记录。
- **未来触发**："检查项目安全风险"、"扫描 API 泄漏"、"提交前安全审查"、"排查密钥泄漏"。
- **完成状态**：完成；strict env 模板基线失败已记录，未扩大范围修改 env 合同。
