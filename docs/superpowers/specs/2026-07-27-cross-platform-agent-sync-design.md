# 跨平台 Agent 同步设计

## 目标

将现有 `multi-agent-sync` 升级为可移植的同步技能：同一项目可在
Windows、macOS、Linux 上运行，并能在 Codex、Claude Code、CodeBuddy 之间
同步 skills、rules、hooks、scripts、workflows 与 MCP 配置。同步后的项目由
CI 在三种操作系统上持续验证。

## 范围与边界

- 每个共享范围在 `.agent-sync/agents/*.yaml` 中只有一个规范来源；默认
  Codex。新增可选的 `canonical_scopes` 标量字段以按范围指定来源；缺失时保留
  现有 `canonical: true` 的全范围默认。单次同步可用 `--from <agent>` 安全地
  提升 Claude Code 或 CodeBuddy。
- 规范文件必须是可提交、可复制的相对路径文本；本机 Python 解释器、绝对路径、
  OS 专属 hook 命令和运行状态必须留在被忽略的本机目录。
- `--apply` 只更新同步器拥有的生成文件，保留目标代理的其他设置；`--check`
  只报告漂移且非零退出。
- 自动修复只涵盖生成镜像与本机配置。不得尝试重写用户编写的 hook 或脚本逻辑；
  检查到不可移植实现时应失败并给出修复位置。

## 设计

### 技能与运行时

保留 `skills/multi-agent-sync/` 为唯一 canonical package，并增加以下资源：

1. `scripts/bootstrap.py`：用 Python 标准库检测宿主系统和当前解释器，渲染
   `.agent-sync/hook-templates/<agent>.json`，再把受管 hooks 合并至各代理的
   本机配置。它在 `.agent-sync/local/` 记录主机状态，写入操作使用临时文件替换；
   失败时保留最后一份有效配置。
2. `scripts/validate_portability.py`：检查 profile、源路径、文本编码、换行符、
   禁止的机器绝对路径和共享 hook 中的 OS 专属启动方式；支持在 CI 中为
   `windows`、`macos`、`linux` 逐一验证配置。
3. 扩展 `scripts/install.py` 与 `scripts/sync_agents.py`：安装、同步和检查都只依赖
   Python 3 标准库。同步器按 scope 选择规范来源，只同步共享树；bootstrap 单独管理
   代理设置中的 `hooks` 键，二者都不删除目标专属文件。
4. 更新 `SKILL.md`、profile schema 和运行说明：Windows 使用 `py -3`，
   macOS/Linux 使用 `python3` 启动引导；运行后的 hook 始终引用引导时检测出的
   解释器，而不是假设 PATH 中存在某个命令。

`scripts/sync-runtime-skills.py` 将此 canonical package 同步至
`.agents/skills/multi-agent-sync/`，使本项目 Codex 可直接发现同一份技能。

已提交的 hook 配置迁移到 `.agent-sync/hook-templates/`。真实的
`.codex/hooks.json`、`.claude/settings.json` 与 `.codebuddy/settings.json` 成为
本机生成文件并加入忽略规则；迁移命令先备份旧配置，再只重建其 `hooks` 键。这样
任何一台机器的解释器绝对路径均不会进入 Git 历史，其他用户设置仍由合并逻辑保留。

### 数据流

1. 用户在规范来源目录修改共享资产或 `.agent-sync` 清单。
2. `sync_agents.py --check` 计算目标镜像；`--apply` 才创建或更新镜像。
3. 每台机器运行 `bootstrap.py`，从 agent 专属 hook 模板生成本机 hook 配置；该配置
   不提交。
4. `validate_portability.py` 同时验证共享源、生成前配置与本机状态的完整性。
5. CI 在三个操作系统重复安装、同步、引导与检查流程，确保不会只在开发者的
   macOS 环境成功。

### Hook 与平台约定

共享 hook 的业务逻辑使用 Python。验证器拒绝未明确隔离的 `zsh`、`bash`、
`cmd.exe`、PowerShell、`/Users/...`、Windows 盘符路径和 OS 专属工具。需要
平台分支时，由 bootstrap 根据平台生成本机启动配置，而不是把平台条件混入共享
hook 或 skill 文本。

规则、skills、workflows 和 MCP 清单保持 UTF-8 与 LF。MCP 配置只保存环境变量
引用，绝不写入令牌或真实凭证。

### 测试与 CI

先用无此技能的压力场景记录基线错误（例如沿用 `python3`、Bash 或 macOS 绝对
路径），再用更新后的技能在同题复测。代码测试覆盖：

- profile 和路径映射；
- `--check` 检出漂移、`--apply` 恢复漂移且重复执行无变化；
- 本机 hook 配置生成、原子失败保护与保留非受管设置；
- 可移植性违规的拒绝；
- Codex、Claude Code、CodeBuddy 的同步与 MCP 输出。

GitHub Actions 的 Windows、macOS、Linux 矩阵执行 Python 安装、同步、引导和
检查。现有依赖 Bash 的无关旧验证可以暂留，但跨平台代理同步的质量门禁不得依赖
Bash。

## 错误处理

缺少 Python 3、profile 不完整、不支持的 MCP 格式、本机配置不一致或检测到
不可移植的共享实现时，命令应说明文件与原因并非零退出。除显式 `--apply` 和
bootstrap 的受管本机文件外，所有失败路径均为只读。

## 兼容性

保持 `install.py`、`sync_agents.py` 已有的 `--apply`、`--check`、`--scope` 和
`--from` 接口。新增选项必须是可选的。现有 profile 路径不变；只允许新增字段时
同时保持旧 profile 可读。

## 验收标准

- canonical package 与 `.agents/skills/multi-agent-sync/` mirror 无漂移。
- 三种系统上的 CI 均能完成 install、bootstrap、sync 和 check。
- Codex、Claude Code、CodeBuddy 的受管资产内容一致，仅保留允许的路径和
  本机配置差异。
- 不可移植的共享 hook 或绝对路径能被诊断，且不会静默生成错误配置。
