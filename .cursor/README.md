# Cursor AI 开发宪法 - 使用指南

**版本**: 2.0.0  
**核心理念**: 分形文档系统 (Fractal Documentation System)

> "让地图与地形保持一致，否则地形将会迷失。"

---

## 📖 简介

这是一套用于规范 Cursor AI 助手行为的开发规范体系。它基于人类软件工程的最佳实践，融合了**分形文档系统**的设计思想，确保代码与文档始终保持同步。

### 核心特性

- ✅ **分形自洽**: 每个目录都能独立讲述自己的故事
- ✅ **四级文档体系**: README → docs → .folder.md → Header
- ✅ **原子更新规则**: 代码变更必须同步文档
- ✅ **AI 行为约束**: 明确的规范和禁止行为

---

## 📁 文件结构

```
project-root/
├── .cursorrules              # 🎯 核心规则文件（Cursor 自动读取）
└── .cursor/
    ├── README.md             # 📖 本文件，使用指南
    ├── CONSTITUTION.md       # 📜 完整宪法文档（核心）
    ├── architecture.md       # 🏗️ 架构设计规范
    ├── coding-standards.md   # 💻 编码规范
    ├── ai-collaboration.md   # 🤖 AI 协作规范
    ├── directory-structure.md # 📁 目录结构规范
    ├── quality-assurance.md  # 🔍 质量保证规范
    └── git-conventions.md    # 📝 Git 使用规范
```

---

## 🚀 快速开始

### 1. 复制规范文件到新项目

```bash
# 复制规范文件
cp -r .cursor /path/to/new-project/
cp .cursorrules /path/to/new-project/
```

### 2. 填写项目配置

编辑 `.cursor/CONSTITUTION.md` 的**第 7 节**，填写项目特定信息：

```yaml
# 项目基本信息
项目名称: 你的项目名
项目类型: Web应用
主要语言: TypeScript

# 技术栈
框架: Next.js 14
数据库: PostgreSQL
ORM: Prisma
```

### 3. 创建模块文档

为每个重要目录创建 `.folder.md`：

```bash
# 快速生成模板
echo "# Folder: $(pwd)

1. **地位 (Position)**: [在系统中的角色]
2. **逻辑 (Logic)**: [核心工作流程]
3. **约束 (Constraints)**: [必须遵守的规则]
" > .folder.md
```

---

## 🌳 核心概念：分形文档系统

### 四级文档体系

```
Level 1: README.md        → 项目鸟瞰图
Level 2: docs/            → 详细设计蓝图
Level 3: .folder.md       → 模块自述文件
Level 4: 文件 Header      → 代码自文档
```

### 分形自洽原则

**每个目录都应该能够独立讲述自己的故事。**

当 AI 进入任何目录时，只需阅读该目录的 `.folder.md` 就能理解：
- 这个目录的职责是什么
- 内部的代码是如何工作的
- 有哪些必须遵守的约束

### 原子更新规则

```
代码变更 → 更新文件 Header
文件变更 → 更新 .folder.md
架构变更 → 更新 docs/
全局变更 → 更新 README.md
```

---

## 📚 规范文档索引

| 文档 | 内容 | 何时阅读 |
|------|------|---------|
| **CONSTITUTION.md** | 完整宪法，包含所有规则 | 项目初始化时 |
| **architecture.md** | 架构设计原则和模式 | 设计新功能时 |
| **coding-standards.md** | 编码风格和 Header 协议 | 编写代码时 |
| **ai-collaboration.md** | AI 行为准则和工作流 | 理解 AI 职责时 |
| **directory-structure.md** | 目录组织规范 | 创建新模块时 |
| **quality-assurance.md** | 测试和审查标准 | 质量控制时 |
| **git-conventions.md** | 提交和分支规范 | 代码提交时 |

---

## 🔑 核心规则速查

### AI 必须做的 ✅

1. 修改前先读取 `.folder.md` 理解上下文
2. 代码变更后同步更新文件 Header
3. 遵循项目现有的代码风格
4. 复杂任务使用 TODO 列表跟踪
5. 使用中文回复（代码注释用英文）

### AI 禁止做的 ❌

1. 推测未查看的代码内容
2. 跳过文档更新直接修改代码
3. 添加未要求的功能或"优化"
4. 违反分层架构原则
5. 硬编码敏感信息

### 文件 Header 协议

```python
"""
[INPUT]: (参数类型) - 输入说明
[OUTPUT]: (返回类型) - 输出说明
[POS]: 在系统中的位置和作用
[DEPS]: 主要依赖模块
[PROTOCOL]: 变更时必须同步更新此 Header
"""
```

### .folder.md 三行原则

```markdown
1. **地位**: 在系统中的角色和职责
2. **逻辑**: 核心工作流程和数据流向
3. **约束**: 必须遵守的规则和限制
```

---

## 🛠️ 实用命令

### 检查缺失的 .folder.md

```bash
find src -type d -not -path "*/node_modules/*" \
  -exec sh -c '[ ! -f "$1/.folder.md" ] && echo "Missing: $1"' _ {} \;
```

### 批量生成 .folder.md 模板

```bash
for dir in src/*/; do
  if [ ! -f "$dir.folder.md" ]; then
    echo "# Folder: $dir

1. **地位 (Position)**: 
2. **逻辑 (Logic)**: 
3. **约束 (Constraints)**: 
" > "$dir.folder.md"
    echo "Created: $dir.folder.md"
  fi
done
```

---

## ❓ 常见问题

### Q: 必须为每个文件都写 Header 吗？

A: 只需要为**关键文件**写 Header，包括：
- 服务层文件
- 核心业务逻辑
- 公共 API 接口
- 复杂的工具函数

简单的类型定义、常量文件可以省略。

### Q: .folder.md 太多怎么办？

A: 只为**重要目录**创建，包括：
- 功能模块目录（features/、modules/）
- 服务层目录（services/）
- 共享代码目录（shared/、common/）

不需要为每个子目录都创建。

### Q: 如何让 AI 更好地遵循规范？

A: 
1. 在对话开始时提醒 AI 阅读 `.cursorrules`
2. 指定需要参考的具体规范文件
3. 发现违规时及时纠正

### Q: 可以自定义规范吗？

A: 当然可以！规范是模板，根据项目需求：
- 修改 `CONSTITUTION.md` 第 7 节的项目配置
- 调整编码规范以匹配团队习惯
- 添加项目特定的约束和规则

---

## 🔄 规范更新

### 更新流程

1. 识别规范中的不足
2. 在 CONSTITUTION.md 中记录变更
3. 更新版本号
4. 通知所有相关方

### 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 2.0.0 | 2026-01-14 | 整合分形文档系统 |
| 1.0.0 | 2026-01-14 | 初始版本 |

---

## 📋 快速检查清单

### 项目初始化时

- [ ] 复制 `.cursor/` 目录和 `.cursorrules`
- [ ] 填写 `CONSTITUTION.md` 第 7 节
- [ ] 为主要目录创建 `.folder.md`
- [ ] 团队成员了解规范

### 日常开发时

- [ ] 阅读目标目录的 `.folder.md`
- [ ] 修改代码后更新 Header
- [ ] 文件变动后更新 `.folder.md`
- [ ] 提交信息遵循规范

---

**"代码会说谎，但架构不会。文档是架构的镜子。"**

*版本: 2.0.0 | 最后更新: 2026-01-14*
