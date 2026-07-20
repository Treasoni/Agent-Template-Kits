---
workflow_id: reusable-agent-assets
workflow_name: Reusable Agent Assets
workflow_version: 1
state_file_type: workflow-run
run_id: "manifest-platform-reuse"
task: "Generalize the supplied manifest-platform skill for shared reuse"
created_from: ".codex/workflows/reusable-agent-assets/state-template.md"
created_at: "2026-07-20"
last_updated: "2026-07-20"
current_phase: done
current_status: complete
mode: standard
blocked_reason: ""
---

# Reusable Agent Assets - Manifest Platform Reuse

> 工作流：reusable-agent-assets
> 任务：将提供的 manifest-platform 技能泛化为共享可复用资产
> 运行标识：manifest-platform-reuse
> 创建时间：2026-07-20
> 当前阶段：完成
> 状态图例：⬜ 未开始 | 🔲 进行中 | ✅ 已完成 | ⏭️ 跳过

---

## 阶段 0：Intake And Boundaries

- [x] 已读取用户原始请求和本状态文件
- [x] 已盘点用户提供或引用的所有材料：`SKILL.md`、界面元数据、安装器、注册表说明/策略/Schema/验证器、清单契约参考和原始 skill 清单
- [x] 已识别候选类型：可复用 skill 混合包（说明、安装脚本、引用文档和平台资产）
- [x] 已确认没有需要阻塞处理的密钥、凭证或安全问题

> [P0] ✅ 已完成

---

## 阶段 1：Classification And Placement Plan

- [x] 每个输入项已映射到一个主要目标位置
- [x] 已检查相关现有资产，确认 `.agents/skills/manifest-platform/` 不存在，且未修改工作区已有的用户变更
- [x] 已决定新建文件：skill 指令、Codex 界面元数据、安装器、清单契约参考和注册表的四个资产；跳过原 skill 自身的 `manifest.yaml`，避免将非部署目录误报为受管 artifact
- [x] 已记录计划执行的验证命令：skill frontmatter 校验、安装器 `bash -n`、临时项目的 install/init/validate、共享 skill 同步检查和 `git diff --check`

> [P1] ✅ 已完成

---

## 阶段 2：Package And Normalize

- [x] 已按项目风格创建共享 skill、界面元数据、安装器、参考和平台资产
- [x] 已移除一次性路径和 `agents.study-system/v1` 命名空间；Schema 改用不可解析的示例 URI，避免伪造外部归属
- [x] 已保留安装、迁移、清单验证和权限声明的用户意图；默认 registry 现支持共享 `.agents/skills`
- [x] 已让稳定工作流、约束和保护说明位于运行命令之前或附近，未加入动态运行时数据

> [P2] ✅ 已完成

---

## 阶段 3：Integrate Registries

- [x] 未改变 workflow；routing 表无需同步
- [x] 已将 `.agents/skills/manifest-platform` 同步到 `.claude/skills/manifest-platform` 并运行共享 skill 检查；路径替换导致的差异为预期行为
- [x] 未新增或修改 hook；`.codex/hooks.json` 无需变更
- [x] 此 skill 不需在每次普通任务预加载；`AGENTS.md` 无需变更

> [P3] ✅ 已完成

---

## 阶段 4：Verify

- [x] 已完成 Bash 语法、Python 实际运行、JSON Schema 解析、frontmatter 和两个临时项目的 install/init/validate 闭环验证
- [x] 已运行 `git diff --check`，并对未跟踪的两个 skill 目录逐文件运行 `git diff --no-index --check`
- [x] 已确认仅新增两个 skill 镜像和本工作流状态文件；已有 `.env.example`、`README.md`、`scripts/validate.sh`、`.workbuddy/`、`docs/` 未被回退或修改
- [x] `quick_validate.py` 因运行环境没有 `PyYAML` 无法启动；已用 Ruby YAML frontmatter 解析和实际安装/验证闭环替代

> [P4] ✅ 已完成

---

## 阶段 5：Finish And Hand Off

- [x] 已记录最终产出路径
- [x] 已记录验证结果
- [x] 已列出未来触发表达
- [x] 已完成所有范围内工作；原 skill 自身的 `manifest.yaml` 按计划未复制

> [P5] ✅ 已完成

---

## 异常记录

| 时间 | 阶段 | 问题描述 | 处理方式 |
|------|------|----------|----------|
| | | | |

---

## 输入材料

- **来源路径/粘贴内容**：`/Users/zhqznc/code/study-system/.codex/skills/manifest-platform/`
- **用户目标**：将该技能改造成项目内可复用的共享 skill。
- **安全或隐私注意事项**：不得复制外部项目的专有路径、凭证或未授权配置；清单权限仅作声明，不能替代宿主执行策略。

## 放置计划

| 输入 | 类型 | 目标位置 | 处理方式 |
|------|------|----------|----------|
| `SKILL.md`、界面元数据 | skill | `.agents/skills/manifest-platform/{SKILL.md,agents/openai.yaml}` | 改写为与项目无关的触发说明和用法 |
| 安装器 | script | `.agents/skills/manifest-platform/scripts/install.sh` | 保留不覆盖差异文件的保护和可选验证 |
| 注册表说明、策略、Schema、验证器 | assets | `.agents/skills/manifest-platform/assets/platform/` | 去除 `study-system` 标识；默认发现 `.agents/skills`，并允许 registry 配置覆盖 |
| 清单契约 | reference | `.agents/skills/manifest-platform/references/manifest-contract.md` | 更新通用 API 标识和项目边界说明 |
| 原 `manifest.yaml` | source metadata | 不复制 | 与宿主发现目录不一致，避免误导；契约范例保留在 reference |

## 最终产出

- **输出文件**：`.agents/skills/manifest-platform/`（含 UI metadata）和同步镜像 `.claude/skills/manifest-platform/`；本运行状态文件。
- **同步/验证命令**：平台 skill 同步 apply/check、Bash 语法检查、Schema JSON 解析、frontmatter 解析、两个临时项目的 `install --validate`、`init` 和 `validate`、`git diff --check`。
- **未来触发表达**："把这个 skill 改成可复用"、"给项目加 manifest.yaml 注册表"、"迁移并验证 workflow/skill/hook 的 manifests"、"审计 agent artifact 权限和依赖"。
- **完成状态**：已完成；`quick_validate.py` 受缺少 PyYAML 限制，等价的 frontmatter 与端到端验证已通过。
