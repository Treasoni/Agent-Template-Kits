# Agent Template Kits

<p align="left">
  <img src="https://img.shields.io/badge/agents-portable-blue" alt="Agent portable">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/status-maintained-brightgreen" alt="Status">
</p>

一组可安装到其他项目的 Agent 工程模板，包含自学习、提示缓存、环境变量规范、可恢复 workflow、技能注册表和密钥审计。

这个仓库是“模板源”，不是需要部署的应用。通常做法是克隆本仓库，然后运行安装器，把所需能力写入另一个目标项目。

## 适用场景

- 为 Codex、Claude Code 或其他 Agent 项目初始化可复用规则和 skills。
- 在会话开始时自动读取经验库，并维护 `.learnings/`。
- 为长任务加入可恢复的 phase 状态和 workflow routing。
- 统一 `.env.example` 维护方式，检查缺失、未使用变量和可疑凭证。
- 优化 LLM 提示缓存布局，安装观测 schema 和回归样本。
- 在提交前扫描 API Key、Token、密码和私钥。

## 运行要求

| 工具 | 用途 | 要求 |
| --- | --- | --- |
| Git | 克隆模板、密钥审计 | 建议安装 |
| Python 3 | Python 安装器、hooks、注册表 | 必需 |
| Bash | Shell 安装器和检查脚本 | Linux、macOS、WSL 或 Git Bash |
| ripgrep (`rg`) | 严格 env 检查 | 使用 env 检查时必需 |
| Perl | workflow 状态和密钥检测 | 使用对应组件时必需 |

Python 脚本可直接在原生 Windows 运行。Bash 脚本可在 Linux、macOS、WSL 或 Git Bash 中使用；统一安装器会自动查找系统 Bash 和常见 Git Bash 安装位置。

## 1. 获取模板并指定目标项目

```bash
git clone https://github.com/Treasoni/Agent-Template-Kits.git
cd Agent-Template-Kits

# 要接入这些模板的项目；目录必须已存在
export TARGET=/absolute/path/to/your-project
test -d "$TARGET"
```

后续示例都在本仓库根目录执行，`$TARGET` 始终指向目标项目。

## 2. 选择 Agent Profile

Profile 决定把 skills、rules、hooks 和入口说明写到哪里。

| Profile | Skills | Rules / Config | Hooks | 入口文件 |
| --- | --- | --- | --- | --- |
| `codex` | `.agents/skills` | `.codex/rules` | `.codex/hooks` | `AGENTS.md` |
| `claude` | `.claude/skills` | `.claude/rules` | `.claude/hooks` | `CLAUDE.md` |
| `codebuddy` | `.codebuddy/skills` | `.codebuddy/rules` | `.codebuddy/hooks` | `CODEBUDDY.md` |
| `cursor` | `.cursor/skills` | `.cursor/rules` | — | `AGENTS.md` |
| `gemini` | `.gemini/skills` | `.gemini/rules` | — | `GEMINI.md` |
| `github-copilot` | `.github/skills` | `.github/instructions` | — | `.github/copilot-instructions.md` |
| `cline` | `.cline/skills` | `.clinerules` | — | `AGENTS.md` |
| `roo-code` | `.roo/skills` | `.roo/rules` | — | `AGENTS.md` |
| `windsurf` | `.windsurf/skills` | `.windsurf/rules` | — | `AGENTS.md` |
| `opencode` | `.opencode/skills` | `.opencode/rules` | — | `AGENTS.md` |
| `qwen-code` | `.qwen/skills` | `.qwen/rules` | — | `QWEN.md` |
| `generic` | `.agent/skills` | `.agent/rules` | `.agent/hooks` | `AGENTS.md` |

使用对应的 profile 名称即可，例如 CodeBuddy Code 用 `codebuddy`、Gemini CLI 用 `gemini`、GitHub Copilot 用 `github-copilot`、Qwen Code 用 `qwen-code`。未在表中的 Agent 优先选 `generic`，或在后文使用自定义 profile。

## 2.1 自动检测与统一安装（推荐）

统一安装器默认只预览，先根据目标项目已有的 agent 目录、配置和入口文件显示候选项及证据，不会猜测只含 `AGENTS.md` 的项目。

```bash
# 只检测，不修改目标项目
python3 scripts/install.py --target "$TARGET" --detect

# 采用所有检测到的 profile，仍然只预览将执行的命令
python3 scripts/install.py --target "$TARGET" --use-detected

# 手动选择 CodeBuddy；--apply 时会要求确认
python3 scripts/install.py --target "$TARGET" --profile codebuddy --apply

# 自动选择并在非交互环境执行；仅安装需要的能力
python3 scripts/install.py \
  --target "$TARGET" \
  --use-detected \
  --components self-learning,env,registry \
  --apply --yes
```

可选组件是 `self-learning`、`env`、`prompt-cache`、`workflow` 和 `registry`，默认全部安装。统一安装器会把 `prompt-cache-optimizer`、`workflow-todo-state` 和 `sync-skill-registry` 的完整 skill 一并复制到所选 profile 的 skills 目录，再生成注册表。`prompt-cache` 与 `workflow` 使用 Bash：Linux/macOS 可直接运行；Windows 下安装器会寻找 Git Bash，找不到时会明确提示安装 Git for Windows 或使用 WSL。`--overwrite` 和 `--force-workflow` 都需要显式给出，避免覆盖已有定制内容。

## 3. Codex 项目的推荐安装

下面的组合会安装自学习、env 规则、提示缓存和 workflow，最后生成技能注册表。

```bash
# 1. digest + maintain-learnings + 学习记录 + SessionStart hook
python3 templates/self-learning/install.py \
  --target "$TARGET" \
  --profile codex

# 2. 环境变量规则和检查脚本
python3 templates/env/install.py \
  --target "$TARGET" \
  --profile codex

# 3. 提示缓存 skill 和规则
bash skills/prompt-cache-optimizer/scripts/prompt-cache-bootstrap.sh \
  --apply \
  --platform codex \
  --with-skill \
  --target "$TARGET"

# 4. 可恢复 workflow、routing 规则和状态脚本
bash skills/workflow-todo-state/scripts/install.sh \
  "$TARGET" \
  --profile codex \
  --with-skill \
  --init-layout \
  --update-agents

# 5. 先预览注册表，再写入
python3 skills/sync-skill-registry/scripts/sync_skill_registry.py \
  --profile codex \
  --root "$TARGET" \
  --create --with-skill \
  --dry-run

python3 skills/sync-skill-registry/scripts/sync_skill_registry.py \
  --profile codex \
  --root "$TARGET" \
  --create --with-skill
```

安装器会创建缺失目录，但 `$TARGET` 本身必须已存在。安装完成后，建议先检查目标项目的 `git diff`，再提交。

## 4. 其他内置 Profile 与 Generic 安装

Claude Code 使用同样的组合，把 profile 替换为 `claude`：

```bash
python3 templates/self-learning/install.py --target "$TARGET" --profile claude
python3 templates/env/install.py --target "$TARGET" --profile claude
bash skills/prompt-cache-optimizer/scripts/prompt-cache-bootstrap.sh --apply --platform claude --with-skill --target "$TARGET"
bash skills/workflow-todo-state/scripts/install.sh "$TARGET" --profile claude --with-skill --init-layout --update-agents
python3 skills/sync-skill-registry/scripts/sync_skill_registry.py --profile claude --root "$TARGET" --create --with-skill --dry-run
```

其他内置 profile 也使用相同命令。例如安装到 Gemini CLI 项目：

```bash
python3 templates/self-learning/install.py --target "$TARGET" --profile gemini
python3 templates/env/install.py --target "$TARGET" --profile gemini
bash skills/prompt-cache-optimizer/scripts/prompt-cache-bootstrap.sh --apply --platform gemini --with-skill --target "$TARGET"
bash skills/workflow-todo-state/scripts/install.sh "$TARGET" --profile gemini --with-skill --init-layout --update-agents
python3 skills/sync-skill-registry/scripts/sync_skill_registry.py --profile gemini --root "$TARGET" --create --with-skill --dry-run
```

Generic profile 也可直接使用内置名称：

```bash
python3 templates/self-learning/install.py --target "$TARGET" --profile generic
python3 templates/env/install.py --target "$TARGET" --profile generic
bash skills/prompt-cache-optimizer/scripts/prompt-cache-bootstrap.sh \
  --apply \
  --platform generic \
  --with-skill \
  --target "$TARGET"
bash skills/workflow-todo-state/scripts/install.sh "$TARGET" --profile generic --with-skill --init-layout --update-agents
python3 skills/sync-skill-registry/scripts/sync_skill_registry.py --profile generic --root "$TARGET" --create --with-skill --dry-run
```

dry-run 确认无误后，去掉 `--dry-run` 再运行一次注册表命令。

## 5. 按需安装单个能力

### 自学习

```bash
python3 templates/self-learning/install.py --target "$TARGET" --profile codex
```

会安装：

- `digest` 和 `maintain-learnings` skills。
- `.learnings/RULES.md`、`ERRORS.md`、`LEARNINGS.md`。
- 会话开始读取经验库的 hook 脚本。
- 对应 Agent 的 hook 配置；既有无关 hooks 会保留。

如果只需要 skills 和学习文件，不安装 hooks：

```bash
python3 templates/self-learning/install.py --target "$TARGET" --profile codex --no-hooks
```

更多说明见 [templates/self-learning/README.md](templates/self-learning/README.md)。

### 提示缓存

推荐使用完整版，它会安装 skill 和规则：

```bash
bash skills/prompt-cache-optimizer/scripts/prompt-cache-bootstrap.sh \
  --apply \
  --platform codex \
  --with-skill \
  --target "$TARGET"
```

只需要规则和入口文件引用时，使用精简版：

```bash
bash templates/cache/prompt-cache-bootstrap.sh \
  --apply \
  --platform codex \
  --target "$TARGET"
```

审计现有配置时把 `--apply` 换成 `--check`。详见 [templates/cache/README.md](templates/cache/README.md) 和 [skills/prompt-cache-optimizer/SKILL.md](skills/prompt-cache-optimizer/SKILL.md)。

只有 agent 已连接能够自动记录 provider usage 的 API 调用后，才额外加 `--with-observability`；它会安装 `/.llm/prompt-cache/` 的 schema 和回归样本合同。直接使用 Codex 时不要加此选项，也无需手填 token 或费用。

### 环境变量规范

```bash
python3 templates/env/install.py --target "$TARGET" --profile codex
```

安装后在目标项目执行：

```bash
cd "$TARGET"
.codex/scripts/check-env-template.sh
.codex/scripts/check-env-template.sh --strict
```

检查脚本不会自动创建 `.env.example`；目标项目需要先准备自己的最小环境变量模板。默认模式会阻止缺失变量和可疑凭证；`--strict` 还会把未被代码引用的模板变量视为失败。详见 [templates/env/README.md](templates/env/README.md)。

### 可恢复 Workflow

```bash
bash skills/workflow-todo-state/scripts/install.sh \
  "$TARGET" \
  --profile codex \
  --with-skill \
  --init-layout \
  --update-agents
```

安装后：

1. 在 `.codex/workflows/<workflow-id>/` 创建 `workflow.md`、`state-template.md` 和 `routing.yaml`。
2. 运行 `.codex/scripts/sync-workflow-routing.sh`。
3. 从 state template 创建 `workspace/workflow-runs/<task>.workflow.md`。
4. 只通过 `.codex/scripts/todo-state.sh` 更新 phase 状态。

详见 [skills/workflow-todo-state/SKILL.md](skills/workflow-todo-state/SKILL.md) 和 [integration guide](skills/workflow-todo-state/references/integration.md)。

### 技能注册表

```bash
# 预览，不写文件
python3 skills/sync-skill-registry/scripts/sync_skill_registry.py \
  --profile codex \
  --root "$TARGET" \
  --create --with-skill \
  --dry-run

# 应用
python3 skills/sync-skill-registry/scripts/sync_skill_registry.py \
  --profile codex \
  --root "$TARGET" \
  --create --with-skill
```

脚本只管理生成区中标记为本地受管的 skills，会保留手工外部条目。详见 [skills/sync-skill-registry/SKILL.md](skills/sync-skill-registry/SKILL.md)。

### 密钥审计

密钥审计脚本扫描当前 Git 工作树。如果脚本位于本模板仓库，可以从目标项目调用它：

```bash
AUDITOR="$PWD/skills/security-secret-audit/scripts/audit-secrets.sh"

# 扫描目标项目当前已跟踪和未忽略文件
(cd "$TARGET" && "$AUDITOR")

# 提交前只扫描 staged 内容
(cd "$TARGET" && "$AUDITOR" --staged)

# 泄露排查：包含 Git 历史
(cd "$TARGET" && "$AUDITOR" --all)
```

报告只包含文件、行号和规则名，不输出凭证原文。详见 [skills/security-secret-audit/SKILL.md](skills/security-secret-audit/SKILL.md)。

## 6. 自定义 Agent

需要在多个安装器中复用同一布局，或路径包含 Windows 盘符冒号时，建议创建 scalar YAML profile：

```yaml
name: myagent
agent_dir: .my-agent
skills_dir: .my-agent/skills
rules_dir: .my-agent/rules
scripts_dir: .my-agent/scripts
hooks_dir: .my-agent/hooks
entry_file: INSTRUCTIONS.md
hook_config: ""
hook_template: ""
include_openai_yaml: false
env_template: codex
```

然后运行：

```bash
python3 templates/self-learning/install.py --target "$TARGET" --profile-file /path/to/myagent.yaml
python3 templates/env/install.py --target "$TARGET" --profile-file /path/to/myagent.yaml
```

提示缓存与 workflow 使用显式自定义参数：

```bash
bash skills/prompt-cache-optimizer/scripts/prompt-cache-bootstrap.sh \
  --apply \
  --platform none \
  --agent myagent,.my-agent,INSTRUCTIONS.md \
  --with-skill \
  --target "$TARGET"

bash skills/workflow-todo-state/scripts/install.sh \
  "$TARGET" \
  --agent-dir .my-agent \
  --skills-dir .my-agent/skills \
  --entry-file INSTRUCTIONS.md \
  --with-skill \
  --init-layout \
  --update-agents
```

完整的第三方 Agent 接入见 [docs/PORTABILITY.md](docs/PORTABILITY.md)。

## 7. 更新已安装的模板

先更新本模板仓库：

```bash
git pull --ff-only
```

然后按需重新运行安装器：

```bash
# 更新受管 skill 和 hook 脚本。不会覆盖 .learnings 记录或无关 hooks。
python3 templates/self-learning/install.py --target "$TARGET" --profile codex --overwrite

# 更新 env 规则和检查脚本。
python3 templates/env/install.py --target "$TARGET" --profile codex --overwrite

# 安装内容未变时可直接重复运行。
bash skills/workflow-todo-state/scripts/install.sh \
  "$TARGET" \
  --profile codex \
  --with-skill \
  --init-layout \
  --update-agents
```

如果 workflow 源码已升级且目标文件不同，安装器会拒绝直接覆盖。确认可替换后加 `--force`；旧文件会移动到带时间戳的 `.bak.*` 备份。

提示缓存安装器默认保留已有规则和观测资产。升级时应先运行 `--check`，再手工评估是否替换项目已定制的内容。

## 8. 安全行为和幂等性

- 首次操作优先使用 `--dry-run` 或 `--check`。
- self-learning 的 `--overwrite` 不覆盖 `.learnings/`，也不删除无关 hook 配置。
- env 的 `--overwrite` 会替换受管的 env 规则和检查脚本，但入口文件只更新对应 profile marker 区块。
- workflow 安装器可重复执行；已有内容不同时必须显式使用 `--force`。
- skill registry 只删除上次同步时已标记为受管、但现在已不存在的本地 skill。
- 密钥审计不输出匹配到的凭证原文。

## 9. 验证

修改本模板仓库后，在仓库根目录执行：

```bash
scripts/validate.sh
.codex/scripts/check-env-template.sh --strict
.codex/scripts/sync-workflow-routing.sh --check
skills/security-secret-audit/scripts/audit-secrets.sh
git diff --check
```

`scripts/validate.sh` 包含语法检查、临时目录安装 smoke test 和 `tests/` 回归测试。GitHub Actions 会对 push 到 `main` 和 pull request 执行同类检查。

目标项目已有 `.env.example` 时，可验证 Codex 安装内容：

```bash
cd "$TARGET"
.codex/scripts/check-env-template.sh --strict
.codex/scripts/sync-workflow-routing.sh --check
```

Claude Code 对应路径为 `.claude/scripts/`，generic profile 对应路径为 `.agent/scripts/`。

## 安装后的 Codex 目录示例

```text
target-project/
├── .agents/skills/
│   ├── digest/
│   ├── maintain-learnings/
│   ├── prompt-cache-optimizer/
│   ├── sync-skill-registry/
│   └── workflow-todo-state/
├── .codex/
│   ├── hooks/
│   ├── rules/
│   ├── scripts/
│   └── workflows/
├── .learnings/
├── workspace/workflow-runs/
├── .codex/hooks.json
└── AGENTS.md
```

仅在项目已接通自动 LLM usage 采集时，才会额外出现 `/.llm/prompt-cache/`。

## 本仓库的目录职责

```text
profiles/       内置 Agent 布局合同
templates/      可安装的规则、hook 和初始文件
skills/         可独立分发的 skill 包和工具
.agents/        本仓库自身使用的 Codex skills
.codex/         本仓库自身使用的 rules、hooks 和 workflows
scripts/        仓库级验证命令
tests/          安装、升级和状态转移回归测试
docs/           便携性和第三方 Agent 接入说明
```

## 进一步阅读

- [更新说明](CHANGELOG.md)
- [跨 Agent 与跨平台接入](docs/PORTABILITY.md)
- [Agent profile 字段说明](profiles/README.md)
- [自学习模板](templates/self-learning/README.md)
- [提示缓存模板](templates/cache/README.md)
- [环境变量模板](templates/env/README.md)
- [Workflow Todo State](skills/workflow-todo-state/SKILL.md)
- [Skill Registry](skills/sync-skill-registry/SKILL.md)
- [Security Secret Audit](skills/security-secret-audit/SKILL.md)
