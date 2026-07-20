---
workflow_id: reusable-agent-assets
workflow_name: Reusable Agent Assets
workflow_version: 1
state_file_type: workflow-run
run_id: "manifest-platform-canonical-source"
task: "Move manifest-platform into canonical distributable skills source"
created_from: ".codex/workflows/reusable-agent-assets/state-template.md"
created_at: "2026-07-20"
last_updated: "2026-07-20"
current_phase: done
current_status: complete
mode: standard
blocked_reason: ""
---

# Reusable Agent Assets - Manifest Platform Canonical Source

> 工作流：reusable-agent-assets
> 任务：将 manifest-platform 放入 canonical `skills/` 分发源
> 运行标识：manifest-platform-canonical-source
> 创建时间：2026-07-20
> 当前阶段：完成
> 状态图例：⬜ 未开始 | 🔲 进行中 | ✅ 已完成 | ⏭️ 跳过

---

## 阶段 0：Intake And Boundaries

- [x] 已读取用户原始请求和本状态文件
- [x] 已盘点用户提供或引用的所有材料：`.claude/skills/manifest-platform/`、`.agents/skills/manifest-platform/`、`skills/`、`scripts/sync-runtime-skills.py`
- [x] 已识别候选类型：可复用 skill 包及 runtime mirror 同步规则
- [x] 已确认没有需要阻塞处理的密钥、凭证或安全问题

> [P0] ✅ 已完成

---

## 阶段 1：Classification And Placement Plan

- [x] 每个输入项已映射到一个主要目标位置
- [x] 已检查 `skills/` 现有 reusable skill 包和 `scripts/sync-runtime-skills.py`
- [x] 已决定新增 `skills/manifest-platform/`，更新 runtime mirror 同步规则、skills 索引和验证脚本
- [x] 已记录计划执行的验证命令：`sync-runtime-skills.py --apply/--check`、manifest registry validate、Bash/Python 语法、`scripts/validate.sh`、`git diff --check`

> [P1] ✅ 已完成

---

## 阶段 2：Package And Normalize

- [x] 已按项目风格新增 `skills/manifest-platform/`，并更新同步脚本、README、验证脚本
- [x] 已将分发入口从 runtime-only 路径改为 canonical `skills/manifest-platform/scripts/install.sh`
- [x] 已保留 manifest registry 安装、迁移、验证和权限声明能力
- [x] 已让 `skills/manifest-platform` 成为稳定源，`.agents/skills/manifest-platform` 由同步脚本生成

> [P2] ✅ 已完成

---

## 阶段 3：Integrate Registries

- [x] 未改变 workflow 定义；已运行 `sync-workflow-routing.sh --check`
- [x] 已运行 `python3 scripts/sync-runtime-skills.py --check`
- [x] `.agent-sync/` 未安装；未直接修改跨 profile 配置
- [x] 已检查 `.codex/hooks.json` JSON 格式，并由 manifest registry validate 覆盖 hook manifest 注册
- [x] 未新增早期加载规则；`AGENTS.md` 无需变更

> [P3] ✅ 已完成

---

## 阶段 4：Verify

- [x] 已运行 `bash scripts/validate.sh`、runtime mirror check、manifest registry validate
- [x] 已检查 `git diff --check`
- [x] 已确认未回退无关用户变更；变更集中在 canonical skill、runtime mirror、同步脚本、验证脚本和本 workflow state
- [x] 已删除验证生成的 `skills/manifest-platform` Python 缓存副产物

> [P4] ✅ 已完成

---

## 阶段 5：Finish And Hand Off

- [x] 已记录最终产出路径
- [x] 已记录验证结果
- [x] 已列出触发该 workflow 的未来表达
- [x] 已完成所有范围内工作；跨 profile 同步因 `.agent-sync/` 未安装而未执行

> [P5] ✅ 已完成

---

## 异常记录

| 时间 | 阶段 | 问题描述 | 处理方式 |
|------|------|----------|----------|
| 2026-07-20 | P3 | `.agent-sync/` 未安装，无法按 multi-agent-sync 预览跨 profile skills 同步 | 本次只更新 canonical source 和 Codex runtime mirror；不手工改 `.claude` |

---

## 输入材料

- **来源路径/粘贴内容**：`.claude/skills/manifest-platform/`、`.agents/skills/manifest-platform/`
- **用户目标**：把可移植的 skill 源放到 `/Users/zhqznc/Documents/template_ai/skills`，否则其他项目无法直接移植。
- **安全或隐私注意事项**：不得引入项目专属绝对路径、凭证或远程仓库假设；runtime mirror 只能由 canonical source 同步生成。

## 放置计划

| 输入 | 类型 | 目标位置 | 处理方式 |
|------|------|----------|----------|
| `.agents/skills/manifest-platform/` | runtime skill mirror | `skills/manifest-platform/` | 复制为 canonical distributable source |
| `scripts/sync-runtime-skills.py` | sync script | 原路径 | 增加 `skills/manifest-platform` -> `.agents/skills/manifest-platform` 镜像规则 |
| `skills/README.md` | docs | 原路径 | 登记 `manifest-platform` 可分发 skill |
| `scripts/validate.sh` | validation | 原路径 | 增加 canonical manifest-platform 的语法和安装验证 |

## 最终产出

- **输出文件**：`skills/manifest-platform/`、`.agents/skills/manifest-platform/SKILL.md`、`scripts/sync-runtime-skills.py`、`scripts/validate.sh`、`skills/README.md`、本 workflow state 文件。
- **同步/验证命令**：`python3 scripts/sync-runtime-skills.py --apply`、`python3 scripts/sync-runtime-skills.py --check`、`python3 .codex/platform/manifest-registry.py --root . validate`、`bash .codex/scripts/sync-workflow-routing.sh --check`、`bash scripts/validate.sh`、`git diff --check`。
- **未来触发表达**："这个 skill 要能移植到其他项目"、"把 runtime skill 放进 skills 分发源"、"canonical skills 与 .agents/skills 同步"。
- **完成状态**：已完成；`skills/manifest-platform` 现在是可复制到其他项目的 canonical 分发包。
