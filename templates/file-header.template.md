# 文件 Header 模板

## Python

```python
"""
[INPUT]: (db: AsyncSession, user_id: int) - 数据库会话和用户ID
[OUTPUT]: (User | None) - 用户对象或 None
[POS]: services/ 层，处理用户相关的业务逻辑
[DEPS]: models.user, repositories.user_repo
[PROTOCOL]:
  1. 一旦本文件逻辑变更，必须同步更新此 Header
  2. 更新后必须检查所属文件夹的 .folder.md 是否依然准确

示例用法:
    user = await get_user_by_id(db, 123)
    if user:
        print(user.name)
"""
```

## TypeScript / JavaScript

```typescript
/**
 * 用户服务 - 处理用户相关的业务逻辑
 *
 * [INPUT]: (userId: string, options?: QueryOptions) - 用户ID和查询选项
 * [OUTPUT]: Promise<User | null> - 用户对象或 null
 * [POS]: services/ 层，处理用户相关的业务逻辑
 * [DEPS]: @/models/user, @/repositories/user-repo
 * [PROTOCOL]:
 *   1. 一旦本文件逻辑变更，必须同步更新此 Header
 *   2. 更新后必须检查所属文件夹的 .folder.md
 *
 * @example
 * const user = await getUserById('123');
 * if (user) {
 *   console.log(user.name);
 * }
 */
```

## Go

```go
/*
Package userservice 处理用户相关的业务逻辑

[INPUT]: (ctx context.Context, userID int64) - 上下文和用户ID
[OUTPUT]: (*User, error) - 用户对象和错误
[POS]: services/ 层，处理用户相关的业务逻辑
[DEPS]: models, repositories
[PROTOCOL]:
  1. 一旦本文件逻辑变更，必须同步更新此 Header
  2. 更新后必须检查所属文件夹的 .folder.md
*/
```

## Java

```java
/**
 * 用户服务 - 处理用户相关的业务逻辑
 *
 * <p>[INPUT]: (Long userId) - 用户ID
 * <p>[OUTPUT]: Optional<User> - 用户对象
 * <p>[POS]: services/ 层，处理用户相关的业务逻辑
 * <p>[DEPS]: UserRepository, UserMapper
 * <p>[PROTOCOL]:
 *   1. 一旦本文件逻辑变更，必须同步更新此 Header
 *   2. 更新后必须检查所属文件夹的 .folder.md
 *
 * @author Team
 * @since 1.0
 */
```

## Rust

```rust
//! 用户服务 - 处理用户相关的业务逻辑
//!
//! [INPUT]: (db: &DbPool, user_id: i64) - 数据库连接池和用户ID
//! [OUTPUT]: Result<Option<User>, Error> - 用户对象或错误
//! [POS]: services/ 层，处理用户相关的业务逻辑
//! [DEPS]: models::user, repositories::user_repo
//! [PROTOCOL]:
//!   1. 一旦本文件逻辑变更，必须同步更新此 Header
//!   2. 更新后必须检查所属文件夹的 .folder.md
```

---

## 简化版本（适用于简单文件）

当文件职责简单时，可以使用简化版本：

```python
"""
[POS]: utils/ 工具函数，提供日期格式化功能
[PROTOCOL]: 变更时同步更新此 Header
"""
```

```typescript
/**
 * [POS]: utils/ 工具函数，提供日期格式化功能
 * [PROTOCOL]: 变更时同步更新此 Header
 */
```

---

## 何时需要完整 Header

**需要完整 Header**:
- 服务层文件
- 核心业务逻辑
- 公共 API 接口
- 复杂的工具函数
- 有多个依赖的模块

**可以使用简化 Header**:
- 简单的工具函数
- 类型定义文件
- 常量定义文件
- 配置文件

**可以省略 Header**:
- 测试文件
- 生成的代码
- 第三方库包装器
