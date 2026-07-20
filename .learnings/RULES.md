# 铁律

从 `LEARNINGS.md` 和 `ERRORS.md` 提炼出的最高优先级规则。

---

_最后更新：2026-07-20_

## Agent 资产边界

- **职责唯一**：`maintain-learnings` 只维护 `.learnings/`；跨 profile 的 skills、rules、hooks、scripts、workflows 与 MCP 同步只由 `multi-agent-sync` 实现。
- **同步幂等**：涉及路径替换的同步器必须按路径长度从长到短替换，并以“`--apply` 后 `--check` 无漂移”作为回归条件。

## CI 质量门禁

- **严格检查先自证**：把检查命令纳入 CI 前，先在干净工作树运行其严格模式；扫描器必须排除自身的局部实现变量，并为真实的可配置变量提供模板说明。
