# 错误日志

---

_最后更新：2026-07-20；已解决记录见 `archive/2026-07-20-agent-sync-quality-gates.md`。_

## 2026-07-20

### reusable-agent-assets：复用 skill 只放入 runtime mirror

**错误**：用户明确要求 `manifest-platform` 要能复用到其他项目时，先把 skill 放在 `.agents/skills/` 和 `.claude/skills/` 运行时目录，没有同步建立 `skills/manifest-platform/` 作为 canonical distributable source。

**触发场景**：用户使用“可复用、移植到其他项目、跨项目共享”等要求创建或整理 agent skill。

**根因**：`reusable-agent-assets` workflow 的放置规则把 `.agents/skills/{skill-id}/` 描述为 reusable skill 位置，未区分 canonical source 与 runtime mirror。

**修复**：
- 已新增 `skills/manifest-platform/` 作为可复制到其他项目的 canonical 分发包。
- 已更新 `scripts/sync-runtime-skills.py`，让 `skills/manifest-platform` 同步到 `.agents/skills/manifest-platform`。
- 已更新 `reusable-agent-assets` workflow，要求用户明确复用时先确认 canonical source。

**预防措施**：
- 听到“复用、移植、跨项目共享”时，必须先检查或创建 `skills/{skill-id}/`、`templates/` 等 canonical source，再同步 runtime mirror。

---
