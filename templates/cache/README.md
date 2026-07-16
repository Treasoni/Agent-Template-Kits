# Prompt Cache Templates

这组文件可直接复用到任意 agent 项目中。所有 `profiles/*.yaml` 中的 Agent 都可用 `--platform <profile>` 直接安装；未知 agent 可以通过 `--agent` 指定自己的目录和入口文件。

| 文件 | 用途 |
| --- | --- |
| `prompt-cache-bootstrap.sh` | 自动安装规则、更新入口文件，并检查常见缓存破坏项 |
| `prompt-cache-rules.md` | 可复制到 `rules/prompt-cache.md` 的完整规则 |
| `AGENTS-cache-snippet.md` | 可粘贴到入口规则文件的精简规则 |
| `prompt-cache-playbook.md` | 设计原理、反例、指标与落地检查清单 |

## Quick Start

先检查目标项目，不会写入文件：

```bash
bash templates/cache/prompt-cache-bootstrap.sh --check --platform both --target /path/to/project
```

安装 Codex 和 Claude Code 两套内置规则：

```bash
bash templates/cache/prompt-cache-bootstrap.sh --apply --platform both --target /path/to/project
```

安装内置 Generic profile：

```bash
bash templates/cache/prompt-cache-bootstrap.sh --apply --platform generic --target /path/to/project
```

安装自定义 agent profile：

```bash
bash templates/cache/prompt-cache-bootstrap.sh --apply --platform none --agent myagent,.my-agent,INSTRUCTIONS.md --target /path/to/project
```

`--agent` 格式为 `name,agent_dir,entry_file[,rule_path]`。如果不传 `rule_path`，默认写入 `agent_dir/rules/common/prompt-cache.md`。

## What The Script Changes

- Built-in profile：创建其声明的 `prompt_cache_rule`，并向入口文件追加 profile 专属标记的入口规则。
- Custom profile：创建 `<agent_dir>/rules/common/prompt-cache.md`，并向 `<entry_file>` 追加带标记的入口规则。
- 检查 `prompts/` 和所选 profile 的 `prompts/` 目录中可能放错位置的时间戳、UUID、git 状态等动态字段。

脚本不会改写现有业务提示词，也不会覆盖已存在的规则文件。重复执行是安全的：它会保留现有规则，并识别已插入的入口块。

## Recommended Workflow

1. 执行 `--check` 查看缺失项和警告。
2. 执行 `--apply` 安装基础规范。
3. 把高频提示词整理到 `prompts/`，使用稳定前缀和末尾参数块。
4. 根据 `prompt-cache-playbook.md` 接入 token、缓存读取 token、延迟和费用指标。
