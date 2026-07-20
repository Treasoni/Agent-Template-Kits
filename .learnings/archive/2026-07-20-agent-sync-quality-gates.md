# 2026-07-20 Agent Sync And Quality Gates

## 已归档：严格 env 检查与同步幂等性缺口

- **原始问题**：严格 env 检查误把脚本局部变量视为环境配置；`multi-agent-sync` 在应用后仍会因重叠路径的替换顺序报告漂移。
- **修复路径**：`.codex/scripts/check-env-template.sh`、`templates/env/*/scripts/check-env-template.sh`、`skills/multi-agent-sync/scripts/sync_agents.py`、`tests/test_refactor_regressions.py`、`scripts/validate.sh`。
- **机制修复**：局部赋值变量从 env 合同中排除；真实 profile-root 变量写入 `.env.example`；路径替换按长度从长到短进行；回归测试要求 `--apply` 后 `--check` 无漂移。
- **职责修复**：`maintain-learnings` 不再同步 profile；跨 Agent 配置统一由 `multi-agent-sync` 负责。
- **验证**：2026-07-20 运行 `bash scripts/validate.sh`（15 tests）和 `git diff --check` 均通过。

活跃铁律保留在 `.learnings/RULES.md`；详细问题已解决并归档。
