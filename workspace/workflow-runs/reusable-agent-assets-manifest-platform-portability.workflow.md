---
workflow_id: reusable-agent-assets
workflow_name: Reusable Agent Assets
workflow_version: 1
state_file_type: workflow-run
run_id: "manifest-platform-portability"
task: "Harden manifest-platform for reuse in other projects"
created_from: ".codex/workflows/reusable-agent-assets/state-template.md"
created_at: "2026-07-20"
last_updated: "2026-07-20"
current_phase: done
current_status: complete
mode: standard
blocked_reason: ""
---

# Reusable Agent Assets - Manifest Platform Portability

> 工作流：reusable-agent-assets
> 任务：强化 manifest-platform，使其可复用到其他项目
> 运行标识：manifest-platform-portability
> 创建时间：2026-07-20
> 当前阶段：完成
> 状态图例：⬜ 未开始 | 🔲 进行中 | ✅ 已完成 | ⏭️ 跳过

---

## 阶段 0：Intake And Boundaries

- [x] 已读取用户原始请求和本状态文件
- [x] 已盘点用户提供或引用的所有材料：`SKILL.md`、`manifest.yaml`、安装脚本、registry 资产、契约参考和 UI metadata
- [x] 已识别候选类型：可复用 skill 混合包（说明、脚本、参考文档、注册表资产）
- [x] 已确认没有需要阻塞处理的密钥、凭证或安全问题

> [P0] ✅ 已完成

---

## 阶段 1：Classification And Placement Plan

- [x] 每个输入项已映射到一个主要目标位置
- [x] 已检查相关现有资产，确认 `.agents/skills/manifest-platform/` 是主版本，`.claude/skills/manifest-platform/` 是待同步镜像
- [x] 已决定更新安装器、validator、registry 文档、契约参考、skill 指令和 manifest 版本；不新增平行实现
- [x] 已记录计划执行的验证命令：Bash 语法、当前项目 registry validate、Codex/Claude/自定义 agent 目录临时项目 install/init/validate、shared skill 同步检查、`git diff --check`

> [P1] ✅ 已完成

---

## 阶段 2：Package And Normalize

- [x] 已按项目风格更新安装器、validator、registry 资产、说明文档、manifest 元数据和同步脚本
- [x] 已移除固定 `.codex/platform` / `.codex/hooks.json` 运行假设；保留 Codex 作为默认可推断布局
- [x] 已保留 manifest 安装、迁移、校验、权限声明和 hook 注册校验能力，并补足 `--agent-dir` / `--hooks-config` 等跨项目选项
- [x] 已让稳定规则和复用说明位于命令示例之前，命令示例只作为具体运行方式

> [P2] ✅ 已完成

---

## 阶段 3：Integrate Registries

- [x] 未改变 workflow 定义；已运行 `sync-workflow-routing.sh --check`
- [x] 已同步 `.agents/skills/manifest-platform` 到 `.claude/skills/manifest-platform` 并运行同步检查；仅剩平台默认路径差异 WARN
- [x] 已检查 `.codex/hooks.json` JSON 格式，并由 manifest validator 覆盖 hook manifest 注册校验
- [x] 未新增早期加载规则；`AGENTS.md` 无需变更

> [P3] ✅ 已完成

---

## 阶段 4：Verify

- [x] 已运行 Bash 语法、Python 编译、源/安装/Claude registry validate、三种临时项目安装/init/validate
- [x] 已检查 `git diff --check`
- [x] 已确认未回退无关用户变更；当前变更集中在 manifest-platform、同步脚本、安装产物和本 workflow state
- [x] 已记录 `maintain-learnings` Claude 镜像缺失为非阻塞既有缺口

> [P4] ✅ 已完成

---

## 阶段 5：Finish And Hand Off

- [x] 已记录最终产出路径
- [x] 已记录验证结果
- [x] 已列出触发该 workflow 的未来表达
- [x] 已完成所有范围内工作，并说明非阻塞镜像缺口

> [P5] ✅ 已完成

---

## 异常记录

| 时间 | 阶段 | 问题描述 | 处理方式 |
|------|------|----------|----------|
| 2026-07-20 16:22 | P3 | `maintain-learnings` 同步检查报告 `.claude/skills/maintain-learnings` 缺失 | 已记录为既有镜像缺口；本次不创建未请求的 Claude skill |

---

## 输入材料

- **来源路径/粘贴内容**：`.agents/skills/manifest-platform/`
- **用户目标**：确保 manifest-platform 可以复用到其他项目中。
- **安全或隐私注意事项**：不得引入项目专属绝对路径、凭证或依赖特定远程仓库；manifest 权限仍只是声明，不是运行时授权。

## 放置计划

| 输入 | 类型 | 目标位置 | 处理方式 |
|------|------|----------|----------|
| `.agents/skills/manifest-platform/scripts/install.sh` | script | 原路径 | 增加可配置 agent 目录，默认保持 `.codex` |
| `.agents/skills/manifest-platform/assets/platform/manifest-registry.py` | script | 原路径 | 让 registry/hook 配置路径跟随脚本安装目录和 discovery 设置 |
| README / reference / SKILL | docs | 原路径 | 补充跨项目复用步骤和非 Codex 目录说明 |
| `.claude/skills/manifest-platform/` | skill mirror | 原路径 | 由同步脚本更新镜像 |

## 最终产出

- **输出文件**：`.agents/skills/manifest-platform/`、`.claude/skills/manifest-platform/`、`.codex/platform/`、`.agents/skills/maintain-learnings/scripts/sync_platform_skills.py`、本 workflow state 文件。
- **同步/验证命令**：`install.sh --force --validate`、manifest registry source/installed/Claude validate、Codex/Claude/custom `.agent` 临时项目 install/init/validate、Bash 语法检查、Python 编译到 `/tmp`、shared skill sync checks、`sync-workflow-routing.sh --check`、`git diff --check`。
- **未来触发表达**："这个 skill 要能复用到其他项目"、"manifest-platform 支持 .claude/.agent 项目"、"给其他 agent 目录安装 manifest registry"、"校验 hook manifest 的注册文件路径"。
- **完成状态**：已完成；`maintain-learnings` Claude 镜像缺失为既有非阻塞缺口，本次未创建未请求的整套 Claude skill。
