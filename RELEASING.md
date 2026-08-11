# 发布流程

本仓库使用语义化版本和 Git 标签发布。版本标签格式为 `vX.Y.Z`；破坏兼容性时递增
主版本，新增兼容能力时递增次版本，修复或文档修正时递增修订版本。

## 发布前

1. 将本次面向用户的变更写入 `CHANGELOG.md`，并以明确的版本标题和日期替换
   `Unreleased` 下对应内容。
2. 在干净工作树中运行：

   ```bash
   bash scripts/validate.sh
   python3 scripts/sync-runtime-skills.py --validate --with-external --offline
   python3 scripts/render-user-guide.py --check
   bash skills/security-secret-audit/scripts/audit-secrets.sh --project --strict
   git diff --check
   ```

3. 确认所有命令均以状态码 `0` 结束。外部 skill 必须已缓存；若本地尚无缓存，先移除 `--offline` 获取并验证固定版本，再以 `--offline` 复验。
4. 确认 CI 的 Ubuntu、macOS、Windows × Python 3.10/当前稳定版矩阵全绿，且没有仍处于 active 状态的发布工作流 run。

## 发布

1. 提交版本、变更日志和相关文档。
2. 创建带说明的标签，例如：

   ```bash
   git tag -a v0.1.0 -m "Release v0.1.0"
   ```

3. 推送提交和标签：

   ```bash
   git push origin main --follow-tags
   ```

4. 在托管平台发布对应 Release，并复制该版本的变更说明。

不要为历史提交补造版本标签；从下一次经过完整验证的公开发布开始使用此流程。
