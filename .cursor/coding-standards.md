# 编码规范 (Coding Standards)

## 📋 概述

本文档定义了项目的编码规范和最佳实践，旨在确保代码质量、可读性和可维护性。这些规范适用于 AI 助手和人类开发者。

---

## 📁 文件组织

### 文件命名

| 类型 | 命名风格 | 示例 |
|------|----------|------|
| 源代码文件 | kebab-case | `user-service.ts`, `api-client.py` |
| 类文件 | PascalCase 或 kebab-case | `UserService.java`, `user-service.ts` |
| 测试文件 | 源文件名 + test/spec | `user-service.test.ts` |
| 常量文件 | kebab-case | `constants.ts`, `config-values.py` |
| 类型定义 | kebab-case | `types.ts`, `interfaces.ts` |

### 文件长度

- **推荐**: 单个文件不超过 300 行
- **最大**: 不超过 500 行
- **超过时**: 考虑拆分职责

### 文件结构顺序

```
1. 文件 Header 注释（In/Out/Pos 协议）
2. 导入语句
   - 标准库/内置模块
   - 第三方库
   - 本地模块
3. 常量定义
4. 类型/接口定义
5. 类/函数实现
6. 导出语句（如适用）
```

### 文件 Header 协议 (In/Out/Pos Protocol)

每个关键文件**必须**在头部包含以下信息：

**Python 示例**:
```python
"""
[INPUT]: (db: AsyncSession, user_id: int) - 数据库会话和用户ID
[OUTPUT]: (User | None) - 用户对象或 None
[POS]: services/ 层，处理用户相关的业务逻辑
[DEPS]: models.user, repositories.user_repo
[PROTOCOL]:
  1. 一旦本文件逻辑变更，必须同步更新此 Header
  2. 更新后必须检查所属文件夹的 .folder.md 是否依然准确
"""
```

**TypeScript 示例**:
```typescript
/**
 * [INPUT]: (userId: string, options?: QueryOptions) - 用户ID和查询选项
 * [OUTPUT]: Promise<User | null> - 用户对象或 null
 * [POS]: services/ 层，处理用户相关的业务逻辑
 * [DEPS]: @/models/user, @/repositories/user-repo
 * [PROTOCOL]:
 *   1. 一旦本文件逻辑变更，必须同步更新此 Header
 *   2. 更新后必须检查所属文件夹的 .folder.md
 */
```

### .folder.md 协议

每个重要目录应包含 `.folder.md`，遵循**三行极简原则**：

```markdown
# Folder: /src/services

1. **地位 (Position)**: 业务逻辑层，处理核心业务规则，连接控制器和数据层
2. **逻辑 (Logic)**: 接收控制器请求 → 调用数据模型 → 执行业务规则 → 返回结果
3. **约束 (Constraints)**: 
   - 禁止直接处理 HTTP 请求/响应
   - 必须使用依赖注入
   - 所有方法必须包含错误处理
```

---

## 🏷️ 命名约定

### 通用规则

```
✅ 名称应该：
- 清晰表达意图
- 使用完整单词（避免缩写）
- 可以发音
- 可以搜索

❌ 避免：
- 单字母变量（除循环索引 i, j, k）
- 无意义的名称（temp, data, info）
- 误导性的名称
- 相似但含义不同的名称
```

### 各类型命名规范

```javascript
// 变量 - camelCase
const userName = 'John';
let orderCount = 0;

// 常量 - SCREAMING_SNAKE_CASE
const MAX_RETRY_COUNT = 3;
const API_BASE_URL = 'https://api.example.com';

// 函数 - camelCase，动词开头
function calculateTotal() {}
function getUserById() {}
function isValidEmail() {}  // 布尔返回用 is/has/can

// 类 - PascalCase
class UserService {}
class OrderRepository {}

// 接口/类型 - PascalCase
interface UserProfile {}
type OrderStatus = 'pending' | 'completed';

// 枚举 - PascalCase，成员 SCREAMING_SNAKE_CASE
enum HttpStatus {
  OK = 200,
  NOT_FOUND = 404,
}

// 私有成员 - 前缀下划线
private _internalState;
private _calculateHelper() {}
```

### 布尔变量命名

```javascript
// ✅ 推荐：使用 is/has/can/should 前缀
const isActive = true;
const hasPermission = false;
const canEdit = true;
const shouldUpdate = false;

// ❌ 避免：模糊的布尔命名
const active = true;
const permission = false;
const flag = true;
```

---

## 📐 代码格式

### 缩进与空格

- **缩进**: 使用空格，2 或 4 个空格（项目统一）
- **行宽**: 最大 100-120 字符
- **尾随空格**: 禁止
- **文件末尾**: 保留一个空行

### 大括号风格

```javascript
// ✅ 推荐：K&R 风格
if (condition) {
  doSomething();
} else {
  doOtherthing();
}

// 单行语句也使用大括号
if (condition) {
  return value;
}
```

### 空行使用

```javascript
// 函数之间：1-2 个空行
function foo() {
  // ...
}

function bar() {
  // ...
}

// 逻辑块之间：1 个空行
function processUser(user) {
  // 验证
  validateUser(user);

  // 处理
  const result = transformUser(user);

  // 保存
  saveUser(result);
}
```

---

## 🔧 函数设计

### 函数长度

- **推荐**: 不超过 20 行
- **最大**: 不超过 50 行
- **超过时**: 拆分为更小的函数

### 参数数量

```javascript
// ✅ 推荐：不超过 3-4 个参数
function createUser(name, email, role) {}

// ✅ 多参数使用对象
function createUser({ name, email, role, department, manager }) {}

// ❌ 避免：过多位置参数
function createUser(name, email, role, dept, mgr, team, loc) {}
```

### 单一职责

```javascript
// ✅ 推荐：函数只做一件事
function validateEmail(email) {
  return EMAIL_REGEX.test(email);
}

function sendWelcomeEmail(user) {
  const content = generateWelcomeContent(user);
  emailService.send(user.email, content);
}

// ❌ 避免：函数做太多事
function validateAndSendEmail(email, user) {
  if (!EMAIL_REGEX.test(email)) {
    return false;
  }
  const content = generateWelcomeContent(user);
  emailService.send(email, content);
  logEmailSent(email);
  updateUserStatus(user);
}
```

### 纯函数优先

```javascript
// ✅ 推荐：纯函数，无副作用
function calculateDiscount(price, percentage) {
  return price * (1 - percentage / 100);
}

// ⚠️ 需要副作用时，清晰标注
function saveUserToDatabase(user) {
  // 这个函数会修改数据库
  return database.insert('users', user);
}
```

---

## 💬 注释规范

### 何时写注释

```javascript
// ✅ 解释"为什么"
// 使用二分查找而非线性查找，因为数据量可能超过 100万
const index = binarySearch(sortedArray, target);

// ✅ 解释复杂的业务逻辑
// 根据公司政策，连续工作 5 年以上的员工享有额外 5 天年假
const extraDays = yearsOfService >= 5 ? 5 : 0;

// ✅ 警告潜在问题
// WARNING: 这个 API 在高并发下可能超时，考虑使用缓存
const result = await externalApi.fetchData();

// ❌ 避免：解释显而易见的代码
// 将 count 加 1
count++;
```

### 文档注释

```javascript
/**
 * 计算订单的最终价格
 *
 * @param {Order} order - 订单对象
 * @param {string} couponCode - 优惠券代码（可选）
 * @returns {number} 最终价格
 * @throws {InvalidCouponError} 当优惠券无效时
 *
 * @example
 * const finalPrice = calculateFinalPrice(order, 'SAVE20');
 */
function calculateFinalPrice(order, couponCode) {
  // ...
}
```

### TODO/FIXME 规范

```javascript
// TODO(username, 2026-01-14): 添加分页支持
// FIXME(username, 2026-01-14): 修复大数据量时的性能问题
// HACK(username, 2026-01-14): 临时方案，需要重构
// NOTE: 这里的实现依赖于外部 API 的特定行为
```

---

## ⚠️ 错误处理

### 基本原则

1. 不要忽略错误
2. 提供有意义的错误信息
3. 在适当的层级处理错误
4. 保持错误处理的一致性

### 错误处理模式

```javascript
// ✅ 推荐：具体的错误类型
class UserNotFoundError extends Error {
  constructor(userId) {
    super(`User not found: ${userId}`);
    this.name = 'UserNotFoundError';
    this.userId = userId;
  }
}

// ✅ 推荐：在边界处理错误
async function handleRequest(req, res) {
  try {
    const result = await processRequest(req);
    res.json({ success: true, data: result });
  } catch (error) {
    logger.error('Request failed', { error, requestId: req.id });
    res.status(500).json({
      success: false,
      error: { message: 'Internal server error' }
    });
  }
}

// ❌ 避免：空的 catch 块
try {
  riskyOperation();
} catch (e) {
  // 不要这样！
}
```

### 错误日志

```javascript
// ✅ 包含足够的上下文
logger.error('Failed to process order', {
  orderId: order.id,
  userId: user.id,
  error: error.message,
  stack: error.stack
});

// ❌ 不足的信息
logger.error('Error occurred');
```

---

## 🔒 安全编码

### 输入验证

```javascript
// ✅ 验证所有外部输入
function processUserInput(input) {
  if (typeof input !== 'string') {
    throw new ValidationError('Input must be a string');
  }
  if (input.length > MAX_INPUT_LENGTH) {
    throw new ValidationError('Input too long');
  }
  // 清理输入
  return sanitize(input);
}
```

### 敏感数据

```javascript
// ✅ 使用环境变量
const apiKey = process.env.API_KEY;

// ❌ 硬编码敏感信息
const apiKey = 'sk-1234567890abcdef';

// ✅ 日志中隐藏敏感信息
logger.info('User logged in', {
  userId: user.id,
  email: maskEmail(user.email)
});
```

---

## 🎯 性能考虑

### 避免的模式

```javascript
// ❌ 循环中的重复计算
for (let i = 0; i < array.length; i++) {
  const config = loadConfig();  // 每次循环都加载
}

// ✅ 提取到循环外
const config = loadConfig();
for (let i = 0; i < array.length; i++) {
  // 使用 config
}

// ❌ 不必要的深拷贝
const copy = JSON.parse(JSON.stringify(obj));

// ✅ 按需浅拷贝或使用专用库
const copy = { ...obj };
```

### 数据结构选择

```javascript
// 频繁查找 → 使用 Set 或 Map
const userIds = new Set([1, 2, 3, 4, 5]);
if (userIds.has(targetId)) { ... }

// 有序数据 + 二分查找
const sortedItems = items.sort((a, b) => a.key - b.key);
const index = binarySearch(sortedItems, target);
```

---

## 🧪 测试代码规范

### 测试命名

```javascript
// 使用描述性名称
describe('UserService', () => {
  describe('createUser', () => {
    it('should create a new user with valid data', () => {});
    it('should throw error when email is invalid', () => {});
    it('should hash password before saving', () => {});
  });
});
```

### 测试结构 (AAA 模式)

```javascript
it('should calculate discount correctly', () => {
  // Arrange - 准备
  const order = createOrder({ price: 100 });
  const discount = 20;

  // Act - 执行
  const result = calculateDiscount(order, discount);

  // Assert - 断言
  expect(result).toBe(80);
});
```

---

## 📝 AI 助手指南

在生成或修改代码时，AI 助手应该：

1. **遵循现有风格**: 查看项目中的现有代码，匹配其风格
2. **保持一致性**: 使用项目中已有的模式和约定
3. **简洁优先**: 选择最简单的解决方案
4. **可读性优先**: 代码是写给人看的
5. **适当注释**: 解释复杂逻辑，避免冗余注释
6. **错误处理**: 不忽略可能的错误情况

---

*最后更新: 2026-01-14*
