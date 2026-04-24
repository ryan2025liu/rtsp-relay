# Git 使用规范 (Git Conventions)

## 📋 概述

本文档定义了项目中 Git 版本控制的使用规范，包括分支策略、提交信息格式、代码审查流程等，确保版本历史清晰可追溯。

---

## 🌳 分支策略

### 主要分支

```
┌─────────────────────────────────────────────────────────────────┐
│ main/master  ─────●─────────────●─────────────●─────────────●─→ │
│                   │             │             │             │   │
│                   │  hotfix/*   │             │  hotfix/*   │   │
│                   │  ┌───●───┐  │             │  ┌───●───┐  │   │
│                   │  │       │  │             │  │       │  │   │
│ develop      ─────●──┼───────┼──●─────────────●──┼───────┼──●─→ │
│                   │  │       │  │             │  │       │  │   │
│              feature/*       release/*        feature/*         │
│              ────●────       ────●────        ────●────         │
└─────────────────────────────────────────────────────────────────┘
```

### 分支类型

| 分支类型 | 命名规则 | 来源 | 合并目标 | 说明 |
|----------|----------|------|----------|------|
| `main` | main | - | - | 生产分支，始终可部署 |
| `develop` | develop | main | main | 开发分支，集成功能 |
| `feature/*` | feature/feature-name | develop | develop | 新功能开发 |
| `bugfix/*` | bugfix/bug-description | develop | develop | Bug 修复 |
| `hotfix/*` | hotfix/issue-id | main | main + develop | 紧急修复 |
| `release/*` | release/v1.2.0 | develop | main + develop | 发布准备 |

### 分支命名规范

```
✅ 推荐格式：
feature/user-authentication
feature/JIRA-123-add-payment
bugfix/login-timeout-error
hotfix/critical-security-patch
release/v2.1.0

❌ 避免：
- 包含空格
- 使用大写字母
- 过于模糊的名称
- 个人名字（如 john-feature）
```

---

## 📝 Commit Message 规范

### 格式规范 (Conventional Commits)

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

| Type | 描述 | 示例 |
|------|------|------|
| `feat` | 新功能 | feat(auth): add password reset |
| `fix` | Bug 修复 | fix(cart): correct total calculation |
| `docs` | 文档更新 | docs(readme): update installation steps |
| `style` | 代码格式（不影响功能） | style: fix indentation |
| `refactor` | 重构（不是新功能或修复） | refactor(user): simplify validation |
| `perf` | 性能优化 | perf(query): add database index |
| `test` | 测试相关 | test(auth): add login tests |
| `chore` | 构建/工具变更 | chore(deps): update dependencies |
| `ci` | CI 配置变更 | ci: add github actions workflow |
| `revert` | 回滚提交 | revert: feat(auth): add oauth |

### Scope（可选）

```
常用 scope：
- 模块名：auth, user, cart, payment
- 层级名：api, ui, db, config
- 组件名：header, sidebar, form
```

### Subject 规则

```
✅ 推荐：
- 使用祈使语气（"add" 而非 "added"）
- 首字母小写
- 不加句号结尾
- 限制在 50 字符内

❌ 避免：
- "fix bug"（太模糊）
- "update code"（没有意义）
- "WIP"（不应提交）
```

### 完整示例

```
feat(auth): implement OAuth2 login with Google

- Add Google OAuth2 provider configuration
- Create login callback handler
- Update user model to support OAuth accounts
- Add tests for OAuth flow

Closes #123
BREAKING CHANGE: User.loginProvider is now required
```

---

## 🔀 合并策略

### Pull Request 流程

```
1. 创建功能分支
   git checkout -b feature/new-feature develop

2. 开发并提交
   git add .
   git commit -m "feat(module): add feature"

3. 推送分支
   git push origin feature/new-feature

4. 创建 Pull Request
   - 填写 PR 描述
   - 关联 Issue
   - 请求审查

5. 代码审查
   - 至少 1 人审批
   - CI 检查通过

6. 合并
   - 使用 Squash Merge 或 Rebase
   - 删除功能分支
```

### 合并方式选择

| 方式 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| Merge Commit | 大型功能 | 保留完整历史 | 历史较复杂 |
| Squash Merge | 小功能/修复 | 历史清晰 | 丢失细节 |
| Rebase | 线性历史需求 | 历史最清晰 | 需要强推 |

### PR 模板

```markdown
## 变更描述
[描述这个 PR 做了什么]

## 变更类型
- [ ] 新功能
- [ ] Bug 修复
- [ ] 文档更新
- [ ] 重构
- [ ] 性能优化
- [ ] 测试

## 测试
- [ ] 已添加测试
- [ ] 现有测试通过
- [ ] 手动测试通过

## 关联 Issue
Closes #

## 截图（如适用）

## 检查清单
- [ ] 代码符合项目规范
- [ ] 自我审查完成
- [ ] 文档已更新（如需要）
- [ ] 没有引入新的警告
```

---

## 🏷️ 版本标签

### 语义化版本 (SemVer)

```
MAJOR.MINOR.PATCH

示例：v2.1.3

MAJOR: 不兼容的 API 变更
MINOR: 向后兼容的新功能
PATCH: 向后兼容的 Bug 修复
```

### 预发布版本

```
v1.0.0-alpha.1    # 内部测试
v1.0.0-beta.1     # 公测
v1.0.0-rc.1       # 发布候选
v1.0.0            # 正式发布
```

### 标签创建

```bash
# 创建标签
git tag -a v1.2.0 -m "Release v1.2.0"

# 推送标签
git push origin v1.2.0

# 推送所有标签
git push origin --tags
```

---

## 📜 .gitignore 规范

### 基础规则

```gitignore
# 依赖目录
node_modules/
vendor/
.venv/

# 构建输出
dist/
build/
*.egg-info/

# 环境变量
.env
.env.local
.env.*.local

# IDE 配置
.idea/
.vscode/
*.swp
*.swo

# 操作系统
.DS_Store
Thumbs.db

# 日志
*.log
logs/

# 缓存
.cache/
*.pyc
__pycache__/

# 测试覆盖率
coverage/
.nyc_output/
```

### 敏感信息保护

```gitignore
# 密钥和证书
*.pem
*.key
*.p12
secrets/

# 配置文件（包含敏感信息）
config.local.json
*.secrets.yaml
```

---

## 🔒 安全实践

### 敏感信息处理

```
✅ 正确做法：
- 使用 .env 文件存储敏感信息
- 将 .env 添加到 .gitignore
- 提供 .env.example 模板

❌ 禁止：
- 提交包含密码/密钥的代码
- 提交包含真实数据的测试文件
- 提交生产环境配置
```

### 撤销敏感信息

```bash
# 如果意外提交了敏感信息
# 方法1: 立即轮换密钥（推荐）

# 方法2: 使用 git-filter-repo 清除历史
git filter-repo --invert-paths --path path/to/sensitive-file

# 方法3: 使用 BFG Repo-Cleaner
bfg --delete-files sensitive-file.txt
```

---

## 🔄 工作流程

### 日常开发流程

```bash
# 1. 更新本地 develop
git checkout develop
git pull origin develop

# 2. 创建功能分支
git checkout -b feature/my-feature

# 3. 开发（小步提交）
git add .
git commit -m "feat(module): partial implementation"

# 4. 定期同步 develop
git fetch origin develop
git rebase origin/develop

# 5. 完成后推送
git push origin feature/my-feature

# 6. 创建 PR
```

### 冲突解决

```bash
# 发生冲突时
git fetch origin develop
git rebase origin/develop

# 解决冲突后
git add .
git rebase --continue

# 如果需要中止
git rebase --abort
```

### 紧急修复流程

```bash
# 1. 从 main 创建 hotfix 分支
git checkout main
git pull origin main
git checkout -b hotfix/critical-issue

# 2. 修复并提交
git commit -m "fix: resolve critical issue"

# 3. 合并到 main
git checkout main
git merge hotfix/critical-issue
git tag -a v1.0.1 -m "Hotfix v1.0.1"
git push origin main --tags

# 4. 合并到 develop
git checkout develop
git merge hotfix/critical-issue
git push origin develop

# 5. 删除 hotfix 分支
git branch -d hotfix/critical-issue
```

---

## 📊 提交历史维护

### 保持历史整洁

```bash
# 交互式 rebase 整理提交
git rebase -i HEAD~5

# 可用操作：
# pick   = 保留提交
# reword = 修改提交信息
# squash = 合并到前一个提交
# fixup  = 合并但丢弃提交信息
# drop   = 删除提交
```

### 修改最后一次提交

```bash
# 修改提交信息
git commit --amend -m "new message"

# 添加遗漏的文件
git add forgotten-file.txt
git commit --amend --no-edit
```

---

## 📝 AI 助手指南

### Git 相关任务

AI 助手在执行 Git 操作时应该：

```
1. 遵循项目的提交规范
2. 使用有意义的提交信息
3. 不提交敏感信息
4. 不强制推送到共享分支
5. 请求必要的 git_write 权限
```

### 提交信息生成

```
当 AI 建议提交信息时：

✅ 应该：
- 使用 Conventional Commits 格式
- 清晰描述变更内容
- 关联相关 Issue

❌ 避免：
- 过于笼统的描述
- 遗漏重要变更
- 使用表情符号（除非项目允许）
```

### 需要确认的操作

```
以下操作 AI 应该先确认：

- 删除分支
- 重写历史（rebase/amend）
- 强制推送
- 合并操作
- 标签操作
```

---

## 📚 快速参考

### 常用命令

```bash
# 分支操作
git branch -a              # 查看所有分支
git checkout -b feature/x  # 创建并切换分支
git branch -d feature/x    # 删除本地分支
git push origin --delete x # 删除远程分支

# 状态查看
git status                 # 当前状态
git log --oneline -10      # 简洁历史
git diff                   # 查看差异
git stash                  # 暂存变更
git stash pop              # 恢复暂存

# 同步操作
git fetch origin           # 获取远程更新
git pull origin develop    # 拉取并合并
git push origin feature/x  # 推送分支

# 撤销操作
git checkout -- file.txt   # 撤销文件修改
git reset HEAD file.txt    # 取消暂存
git reset --hard HEAD~1    # 撤销最后一次提交
```

### Commit Message 模板

```
# feat: 新功能
feat(auth): add two-factor authentication

# fix: Bug 修复
fix(cart): prevent negative quantities

# docs: 文档更新
docs(api): add endpoint documentation

# refactor: 重构
refactor(user): extract validation logic

# test: 测试
test(payment): add integration tests

# chore: 杂项
chore(deps): update dependencies
```

---

*最后更新: 2026-01-14*
