# 学习心得

---

_最后更新：2026-07-20；已解决记录见 `archive/2026-07-20-agent-sync-quality-gates.md`。_

## 2026-07-20

### 可复用 skill 必须有 canonical source

**类别**：correction
**优先级**：high
**状态**：pending
**范围**：workflow/reusable-agent-assets

**摘要**：用户明确要求 skill 可复用时，交付位置必须是 `skills/{skill-id}/` 这类 canonical source，而不是只放在 `.agents/skills` 或 `.claude/skills` runtime mirror。

**详情**：
- 事实：`manifest-platform` 已先放入 runtime mirror，用户指出无法从 `/Users/zhqznc/Documents/template_ai/skills` 移植到其他项目。
- 根因：工作流放置规则没有区分分发源和运行时镜像。
- 下次做法：先建立 canonical source，再运行对应同步脚本和验证；runtime mirror 只能作为生成结果。

---
