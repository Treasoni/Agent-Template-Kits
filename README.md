# Agent Template Kits

可安装到其他项目的 Agent 工程模板源。它提供自学习、环境变量规范、提示缓存、可恢复 workflow、技能注册表、多 Agent 同步、manifest registry 和安全审计，不是需要部署的应用。

当前目标版本：`v0.1.0` 发布候选。

## Source Of Truth

```text
skills/ + templates/ + profiles/ + docs source
                    │
                    ├── scripts/install.py ──> 目标项目
                    └── scripts/sync-runtime-skills.py ──> 本机 Agent runtime
```

- `skills/`、`templates/` 和 `profiles/` 是公共 canonical source。
- `.agents/skills/`、`.claude/skills/`、`.codebuddy/skills/` 是 gitignored runtime adapters，克隆后生成。
- `skills-lock.json` 中的第三方开发 skills 固定 upstream commit、许可证和内容哈希；它们不是公共 canonical packages。
- runtime 不得反向成为 canonical source，也不得通过 tracked symlink 暴露为 `skills/*`。

## 要求

| 工具 | 要求 |
| --- | --- |
| Python | 3.10+ |
| Git | 建议安装；安全审计需要 |
| Bash | Linux、macOS、WSL 或 Git Bash |
| ripgrep (`rg`) | strict env 检查需要 |
| Perl | workflow 状态与安全检测需要 |

## 快速开始

```bash
git clone https://github.com/Treasoni/Agent-Template-Kits.git
cd Agent-Template-Kits

export TARGET=/absolute/path/to/your-project
test -d "$TARGET"

# 自动检测，只读
python3 scripts/install.py --target "$TARGET" --detect

# 预览安装计划
python3 scripts/install.py --target "$TARGET" --use-detected

# 明确确认后安装选中的能力
python3 scripts/install.py \
  --target "$TARGET" \
  --use-detected \
  --components self-learning,env,registry \
  --apply --yes
```

安装器默认 dry-run；`--overwrite`、`--force-workflow` 和 `--force-manifest-platform` 必须显式给出。应用后先检查目标项目的 `git diff`。

## 本仓库 Runtime Bootstrap

公共 canonical core 的生成不依赖网络：

```bash
# 生成 Codex 与 Claude Code runtime adapters
python3 scripts/sync-runtime-skills.py --apply

# 检查本机 adapters
python3 scripts/sync-runtime-skills.py --check

# 可选：下载并校验锁定的第三方开发 skills
python3 scripts/sync-runtime-skills.py --apply --with-external
```

外部 source 缓存在 `.agent-runtime/cache/`。离线重建可使用 `--with-external --offline`；缓存缺失时会明确失败。

## 功能组件

| 组件 | 用途 |
| --- | --- |
| `self-learning` | 安装经验库、digest、maintain-learnings 和会话 hook |
| `env` | 安装 `.env.example` 维护规则与 strict 检查器 |
| `prompt-cache` | 安装 prompt-cache skill、规则和可选观测合同 |
| `workflow` | 安装 recoverable workflow、routing 和 quality-gated 状态脚本 |
| `registry` | 生成并维护 skill invocation registry |
| `manifest-platform` | 安装 Agent 资产 manifest registry |
| `multi-agent-sync` | 安装跨 profile 的共享配置 runtime |

安全审计是独立的 canonical skill：

```bash
# 默认凭证扫描
skills/security-secret-audit/scripts/audit-secrets.sh

# PR/CI 项目风险门禁；不扫描 Git 历史
skills/security-secret-audit/scripts/audit-secrets.sh --project --strict

# 仅在泄漏调查时扫描历史
skills/security-secret-audit/scripts/audit-secrets.sh --history
```

审计输出只包含 scope、路径、行号和规则名，不输出匹配内容。`--fix` 只维护标记的本地凭证 ignore block，且必须与 `--project` 一起使用；CI 不应运行 `--fix`。

## Profile 支持级别

- Tier 1：Codex、Claude Code、CodeBuddy。执行 Ubuntu、macOS、Windows 安装与更新验证。
- Tier 2：Cursor、Gemini、GitHub Copilot、Cline、Roo Code、Windsurf、OpenCode、Qwen Code、generic。执行 profile contract 与 Linux smoke test。

所有内置布局见 [profiles/README.md](profiles/README.md)。

## 更新已有安装

统一安装器会把受管文件指纹写入目标项目的 `.agent-template-kits/install-state.json`：

```bash
python3 scripts/install.py --target "$TARGET" --update
python3 scripts/install.py --target "$TARGET" --update --apply --yes
```

检测到用户修改的受管文件时，更新器停止并要求逐项 `--accept <path>`；应用前会写入备份目录。

## 仓库验证

```bash
scripts/validate.sh
bash .codex/scripts/check-env-template.sh --strict
bash .codex/scripts/sync-workflow-routing.sh --check
python3 scripts/validate-profiles.py
python3 scripts/sync-runtime-skills.py --validate
python3 scripts/check-docs.py
skills/security-secret-audit/scripts/audit-secrets.sh --project --strict
git diff --check
```

Workflow 最终阶段只有在 state frontmatter 设置 `quality_gate: passed` 后才能完成。临时 waiver 必须同时记录 owner 和 due date。

## 文档

- [完整功能与使用文档](docs/Agent%20Template%20Kits%20%E2%80%94%20%E5%8A%9F%E8%83%BD%E4%B8%8E%E4%BD%BF%E7%94%A8%E6%96%87%E6%A1%A3.md)
- [生成的 HTML 用户指南](docs/USER_GUIDE.html)
- [可移植性与平台差异](docs/PORTABILITY.md)
- [发布流程](RELEASING.md)
- [变更记录](CHANGELOG.md)

`docs/Agent Template Kits — 功能与使用文档.md` 是完整用户文档的 canonical source；HTML 由 `scripts/render-user-guide.py` 确定性生成。

## License

[MIT](LICENSE)
