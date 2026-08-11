# 更新说明

## Unreleased

### 新增

- 新增 canonical skill 到本地 runtime 的生成器：支持 Codex、Claude profile，按状态清理受管旧文件，并保留手工添加的 runtime skill。
- 新增外部 skill v2 锁文件合同，固定上游仓库、完整 commit、许可证和每个 skill 的内容哈希；外部下载默认可选并缓存于项目本地。
- 新增共享 Profile 合同模块，以及由中文 Markdown 单源生成和校验 HTML 用户文档的工具。
- 新增工作流最终阶段质量门：只有验证通过，或记录 owner 与到期日的临时豁免，才允许完成。
- 新增 `codebuddy` 内置 profile：使用 `.codebuddy/skills/`、`.codebuddy/rules/`、`.codebuddy/scripts/` 与根目录 `CODEBUDDY.md`。
- CodeBuddy 自学习安装会合并 `.codebuddy/settings.json` 的 `SessionStart` hook，并保留既有的无关设置。
- 新增统一入口 `scripts/install.py`：可扫描目标项目的 agent 目录、配置和入口文件，列出检测证据后预览安装计划。
- 新增 `--use-detected` 自动选择和重复 `--profile NAME` 手动选择；默认 dry-run，`--apply` 会要求确认，非交互环境需显式 `--yes`。
- 新增 Cursor、Gemini CLI、GitHub Copilot、Cline、Roo Code、Windsurf、OpenCode、Qwen Code 等内置 profile。

### 兼容性与行为

- `skills/` 现在只保存可分发的 canonical package；`.agents/skills/`、`.claude/skills/` 和 `.codebuddy/skills/` 是 clone 后生成且不提交的本地 runtime，不再使用 tracked symlink 或 runtime 反向充当源码。
- 严格环境变量检查只扫描项目合同范围，不再把第三方 skill、文档示例或工作流状态中的大写占位符误报为项目变量。
- `security-secret-audit --project --strict` 现在是主验证和 CI 门禁；`--fix` 只维护带 marker 的 ignore block，并保留多种合法 `.env.*.example|sample|template` 文件。
- CI 覆盖 Ubuntu、macOS、Windows 与 Python 3.10/当前稳定版组合，并固定第三方 Action 到完整提交。
- 主验证要求 Python 3.10+，校验 canonical runtime source、生成文档、严格环境合同、严格安全审计和完整回归测试。
- 这是 `v0.1.0` 前的一次内部整理；尚未公开稳定的 tracked runtime symlink 布局不再兼容。
- 统一安装器现在会把 `prompt-cache-optimizer` 和 `sync-skill-registry` 完整复制到每个所选 profile 的 `skills_dir`，并在复制后生成注册表；不会再只安装规则或注册表而遗漏可调用 skill。
- Python 安装组件在 Windows、Linux 和 macOS 可运行；`prompt-cache` 与 `workflow` 组件仍需要 Bash。
- 在 Windows 上，统一安装器会先从 `PATH` 查找 Bash，再检查常见 Git for Windows 安装路径；找不到时不会写入目标项目，并提示安装 Git Bash 或使用 WSL。
- 自动检测不会仅凭通用的 `AGENTS.md` 判断运行时，避免把普通项目误识别为特定 agent。
- 现有组件的单独安装命令保持可用；`--overwrite` 和 `--force-workflow` 仍必须由用户明确指定。

### 使用方式

```bash
# 只检测，不修改目标项目
python3 scripts/install.py --target "$TARGET" --detect

# 自动选择检测到的 profile；默认仍为预览
python3 scripts/install.py --target "$TARGET" --use-detected

# 手动指定 CodeBuddy 并执行安装
python3 scripts/install.py --target "$TARGET" --profile codebuddy --apply
```

详见 [README](README.md)、[Profile 说明](profiles/README.md) 和 [跨平台说明](docs/PORTABILITY.md)。
