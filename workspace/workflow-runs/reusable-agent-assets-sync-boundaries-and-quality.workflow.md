---
workflow_id: reusable-agent-assets
workflow_name: Reusable Agent Assets
workflow_version: 1
state_file_type: workflow-run
run_id: "sync-boundaries-and-quality"
task: "Clarify multi-agent-sync ownership and address repository quality gaps"
created_from: ".codex/workflows/reusable-agent-assets/state-template.md"
created_at: "2026-07-20"
last_updated: "2026-07-20"
current_phase: done
current_status: complete
mode: standard
blocked_reason: ""
---

# Reusable Agent Assets - Workflow Run

> 工作流：reusable-agent-assets
> 任务：Clarify multi-agent-sync ownership and address repository quality gaps
> 运行标识：sync-boundaries-and-quality
> 创建时间：2026-07-20
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

- [x] 如涉及 workflow，已同步并检查 routing 表
- [x] 如涉及共享 skill，已运行平台 skill 同步脚本
- [x] 如涉及 hook，已检查 `.codex/hooks.json`
- [x] 如涉及早期加载规则，已最小化更新 `AGENTS.md`

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
| 2026-07-20 | P3 | 本模板仓库未配置 `.agent-sync/` runtime | 已完成 runtime skill mirror 检查；不创建未请求的跨 profile 输出。 |

---

## 输入材料

- **来源路径/粘贴内容**：`skills/multi-agent-sync/`、`.agents/skills/maintain-learnings/`、模板、安装器、CI、文档与测试。
- **用户目标**：消除职责重叠，并落实前次审查发现的 CI、源码漂移、集成、测试、文档和跨平台质量问题。
- **安全或隐私注意事项**：不写入真实凭证；保留既有用户配置与 profile 专属内容。

## 放置计划

| 输入 | 类型 | 目标位置 | 处理方式 |
|------|------|----------|----------|
| `multi-agent-sync` | skill/script | `skills/multi-agent-sync/` | 作为跨 profile 同步的唯一实现，补齐安装、说明与测试。 |
| `maintain-learnings` | skill/template | `.agents/skills/maintain-learnings/`、`templates/self-learning/skills/maintain-learnings/` | 移除跨 profile 同步职责，仅保留经验库维护。 |
| 质量检查 | script/CI/tests/docs | `.codex/`、`scripts/`、`tests/`、`README.md` | 修复 env 变量检测、补齐验证并更新文档。 |

### 已确认的改造清单

1. 删除 `maintain-learnings` 的 `sync_platform_skills.py` 及其所有调用；将跨 profile 同步统一交给 `multi-agent-sync`。
2. 新增 `scripts/sync-runtime-skills.py`，以 `skills/workflow-todo-state/` 与 `templates/self-learning/skills/maintain-learnings/` 为源，检查并同步本仓库 `.agents/skills/` 的运行时镜像。
3. 修复三份 env 检查脚本：只将未在同一文件赋值的 shell 展开视为环境变量，避免局部大写变量造成误报。
4. 将 `manifest-platform` 和 `multi-agent-sync` 增加为统一安装器的显式可选组件；默认组件集合保持不变，避免无意写入 `.agent-sync/`。
5. 为 manifest 安装器补上安全的 `--with-skill`，使其成为完整可分发组件；补充回归测试、验证脚本、跨平台 CI 矩阵和主文档。

## 最终产出

- **输出文件**：职责拆分、镜像守护、env 检查、统一安装器、manifest 安装器、回归测试、CI 与中英文档均已更新。
- **同步/验证命令**：`bash scripts/validate.sh`（15 tests）、`.codex/scripts/check-env-template.sh --strict`、`.codex/scripts/sync-workflow-routing.sh --check`、`.codex/platform/manifest-registry.py validate`、`scripts/sync-runtime-skills.py --check`、`scripts/check-docs.py`、`skills/security-secret-audit/scripts/audit-secrets.sh`、`git diff --check` 均通过。
- **完成状态**：已完成。

### 未来触发

- “把这些 Agent skills/rules 整理成可复用资产”
- “封装成 skill 并放到合适位置”
- “同步或维护共享 Agent 配置”
