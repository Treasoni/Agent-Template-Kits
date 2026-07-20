# <PROJECT_NAME> 自学习规则

## 经验库规则

1. **任务前读取经验库**：执行任何任务前，先读取：
   - `.learnings/RULES.md`：提炼后的铁律
   - `.learnings/LEARNINGS.md`：学习心得
   - `.learnings/ERRORS.md`：错误日志

2. **错误不只记录，还要修源头**：如果同类错误反复出现，或某条规则已写入 `RULES.md` 但仍复发，使用 `maintain-learnings` 追溯并修改对应 skill、模板、hook、校验脚本或项目规则。修复并验证后，才归档或移除活跃记录。

3. **记录要短，规则要可执行**：学习记录写事实和根因；`RULES.md` 写简洁规则，例如“用 X 而非 Y”。不要把 `.learnings/` 变成冗长日志库。

4. **Hook 自动读取**：各 agent profile 通过自己的 hooks 目录运行 `read_learnings.py` 或 `read-learnings.sh`，在会话开始时注入经验库提醒。若 hook 配置不存在，先安装或合并模板中的 hook 配置。

## 推荐触发语

- “记录一下这次学习”
- “把这次错误写进 learnings”
- “learnings 太多了，帮我维护”
- “这个错误又犯了，去修源头”
