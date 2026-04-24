# 质量保证规范 (Quality Assurance Guidelines)

## 📋 概述

本文档定义了项目的质量保证标准和实践，确保交付的代码符合可靠性、可维护性和安全性要求。

---

## 🎯 质量目标

### 核心质量属性

| 属性 | 定义 | 目标 |
|------|------|------|
| **可靠性** | 系统按预期工作 | 99.9% 正常运行时间 |
| **可维护性** | 易于修改和扩展 | 修改影响范围可控 |
| **可测试性** | 易于测试和验证 | 80%+ 测试覆盖率 |
| **安全性** | 抵抗恶意攻击 | 零已知漏洞 |
| **性能** | 响应速度和资源效率 | 95% 请求 < 200ms |

---

## 🧪 测试策略

### 测试金字塔

```
                    /\
                   /  \
                  / E2E \         10% - 端到端测试
                 /------\
                /        \
               / 集成测试  \       20% - 集成测试
              /------------\
             /              \
            /    单元测试     \    70% - 单元测试
           /------------------\
```

### 单元测试规范

```javascript
// 测试文件位置：与源文件同目录或 tests/unit/

// ✅ 好的单元测试
describe('calculateDiscount', () => {
  // 清晰的测试名称
  it('should return 10% off when quantity >= 10', () => {
    // Arrange - 准备
    const price = 100;
    const quantity = 10;

    // Act - 执行
    const result = calculateDiscount(price, quantity);

    // Assert - 断言
    expect(result).toBe(90);
  });

  // 边界条件
  it('should return full price when quantity < 10', () => {
    expect(calculateDiscount(100, 9)).toBe(100);
  });

  // 错误情况
  it('should throw error for negative price', () => {
    expect(() => calculateDiscount(-100, 10)).toThrow();
  });
});
```

### 集成测试规范

```javascript
// 测试 API 端点
describe('POST /api/users', () => {
  beforeEach(async () => {
    await db.clear();
  });

  it('should create a new user', async () => {
    const response = await request(app)
      .post('/api/users')
      .send({ name: 'John', email: 'john@example.com' });

    expect(response.status).toBe(201);
    expect(response.body.data).toHaveProperty('id');

    // 验证数据库
    const user = await db.users.findById(response.body.data.id);
    expect(user.name).toBe('John');
  });
});
```

### 端到端测试规范

```javascript
// 使用 Playwright/Cypress
describe('User Registration Flow', () => {
  it('should allow new user to register', async () => {
    await page.goto('/register');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'SecurePass123');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('.welcome')).toContainText('Welcome');
  });
});
```

---

## 📊 测试覆盖率

### 覆盖率目标

| 指标 | 最低要求 | 推荐目标 |
|------|----------|----------|
| 行覆盖率 | 70% | 80% |
| 分支覆盖率 | 60% | 75% |
| 函数覆盖率 | 80% | 90% |

### 关键路径必须测试

```
✅ 必须 100% 覆盖：
- 认证/授权逻辑
- 支付/交易处理
- 数据验证逻辑
- 安全相关代码
- 核心业务规则
```

### 覆盖率例外

```
可以豁免的代码：
- 第三方库包装器
- 纯 UI 展示组件
- 配置文件
- 生成的代码
- 测试辅助代码
```

---

## 🔍 代码审查

### 审查清单

#### 功能性
- [ ] 代码是否实现了预期功能？
- [ ] 边界条件是否处理？
- [ ] 错误情况是否处理？

#### 可读性
- [ ] 代码是否清晰易懂？
- [ ] 命名是否有意义？
- [ ] 注释是否必要且有用？

#### 可维护性
- [ ] 代码是否遵循 DRY 原则？
- [ ] 是否有适当的抽象？
- [ ] 模块边界是否清晰？

#### 性能
- [ ] 是否有明显的性能问题？
- [ ] 是否有不必要的计算？
- [ ] 数据库查询是否优化？

#### 安全性
- [ ] 输入是否验证？
- [ ] 是否有注入风险？
- [ ] 敏感数据是否保护？

#### 测试
- [ ] 是否有足够的测试？
- [ ] 测试是否有意义？
- [ ] 边界情况是否测试？

---

## 🐛 Bug 管理

### Bug 严重等级

| 等级 | 描述 | 响应时间 | 示例 |
|------|------|----------|------|
| P0 - 紧急 | 系统不可用 | < 1小时 | 生产环境崩溃 |
| P1 - 高 | 主要功能失效 | < 4小时 | 用户无法登录 |
| P2 - 中 | 功能异常但可绕过 | < 24小时 | 导出格式错误 |
| P3 - 低 | 轻微问题 | < 1周 | 界面对齐问题 |

### Bug 修复流程

```
1. 复现问题
   ↓
2. 定位根因
   ↓
3. 编写失败测试（回归测试）
   ↓
4. 实现修复
   ↓
5. 验证测试通过
   ↓
6. 代码审查
   ↓
7. 部署验证
```

### Bug 报告模板

```markdown
## Bug 描述
[简要描述问题]

## 复现步骤
1. 步骤一
2. 步骤二
3. ...

## 预期行为
[应该发生什么]

## 实际行为
[实际发生了什么]

## 环境
- 系统: [OS/Browser]
- 版本: [App Version]
- 用户: [User Role]

## 截图/日志
[附加信息]
```

---

## 🔐 安全审查

### 安全检查清单

#### 输入验证
- [ ] 所有外部输入已验证
- [ ] 使用白名单而非黑名单
- [ ] 验证数据类型和范围

#### 认证授权
- [ ] 密码正确加密存储
- [ ] 会话管理安全
- [ ] 权限检查完整

#### 数据保护
- [ ] 敏感数据加密传输
- [ ] 敏感数据加密存储
- [ ] 日志不包含敏感信息

#### 注入防护
- [ ] SQL 使用参数化查询
- [ ] 防止 XSS 攻击
- [ ] 防止命令注入

### 常见安全漏洞

```javascript
// ❌ SQL 注入风险
const query = `SELECT * FROM users WHERE id = ${userId}`;

// ✅ 参数化查询
const query = 'SELECT * FROM users WHERE id = ?';
db.query(query, [userId]);

// ❌ XSS 风险
element.innerHTML = userInput;

// ✅ 安全渲染
element.textContent = userInput;

// ❌ 硬编码密钥
const apiKey = "sk-abc123...";

// ✅ 环境变量
const apiKey = process.env.API_KEY;
```

---

## ⚡ 性能基准

### 响应时间目标

| 操作类型 | 目标 | 最大可接受 |
|----------|------|-----------|
| API 响应 | < 100ms | < 500ms |
| 页面加载 | < 1s | < 3s |
| 数据库查询 | < 50ms | < 200ms |
| 批量操作 | < 5s | < 30s |

### 性能监控指标

```
核心指标：
- 响应时间 (P50, P95, P99)
- 吞吐量 (RPS)
- 错误率
- CPU/内存使用率

前端指标：
- LCP (Largest Contentful Paint)
- FID (First Input Delay)
- CLS (Cumulative Layout Shift)
```

### 性能测试

```javascript
// 负载测试示例
describe('Performance', () => {
  it('should handle 100 concurrent requests', async () => {
    const requests = Array(100).fill().map(() =>
      request(app).get('/api/users')
    );

    const start = Date.now();
    const responses = await Promise.all(requests);
    const duration = Date.now() - start;

    expect(responses.every(r => r.status === 200)).toBe(true);
    expect(duration).toBeLessThan(5000);
  });
});
```

---

## 📝 文档质量

### 必需文档

| 文档 | 内容 | 更新频率 |
|------|------|----------|
| README | 项目概述、快速开始 | 每次重大变更 |
| API 文档 | 端点、参数、响应 | 每次 API 变更 |
| 架构文档 | 系统设计、决策 | 架构变更时 |
| 部署文档 | 部署步骤、配置 | 部署流程变更时 |

### 代码文档标准

```javascript
/**
 * 计算用户的订阅费用
 *
 * @description 根据用户计划和使用量计算月度费用
 *
 * @param {User} user - 用户对象
 * @param {Usage} usage - 本月使用量
 * @returns {BillingResult} 计费结果
 * @throws {InvalidPlanError} 当用户计划无效时
 *
 * @example
 * const billing = calculateBilling(user, monthlyUsage);
 * console.log(billing.total); // 99.99
 */
function calculateBilling(user, usage) {
  // ...
}
```

---

## 🔄 持续集成/持续部署

### CI 管道

```yaml
# .github/workflows/ci.yml 示例
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: npm ci
      - name: Lint
        run: npm run lint
      - name: Type check
        run: npm run type-check
      - name: Test
        run: npm test -- --coverage
      - name: Build
        run: npm run build
```

### 质量门禁

```
合并前必须通过：
✅ 所有测试通过
✅ 测试覆盖率 >= 阈值
✅ 无 lint 错误
✅ 无类型错误
✅ 代码审查通过
✅ 安全扫描通过
```

---

## 📈 质量度量

### 跟踪指标

| 指标 | 描述 | 目标方向 |
|------|------|----------|
| 代码覆盖率 | 测试覆盖百分比 | ↑ |
| 缺陷密度 | 每千行代码的 bug 数 | ↓ |
| 技术债务 | 待解决的技术问题 | ↓ |
| 代码复杂度 | 圈复杂度平均值 | ↓ |
| 构建成功率 | CI 通过率 | ↑ |

### 定期审计

```
每周：
- 审查新增 bug
- 检查测试覆盖率趋势

每月：
- 代码质量报告
- 技术债务评估
- 安全漏洞扫描

每季度：
- 架构健康检查
- 性能基准测试
- 依赖更新评估
```

---

## 📝 AI 助手指南

### 质量相关任务

AI 助手在处理代码时应该：

```
1. 验证代码正确性
   - 运行相关测试
   - 检查类型错误
   - 验证功能实现

2. 确保代码质量
   - 遵循编码规范
   - 处理错误情况
   - 保持代码简洁

3. 添加适当测试
   - 新功能需要测试
   - Bug 修复需要回归测试
   - 测试覆盖关键路径

4. 报告问题
   - 发现的潜在 bug
   - 安全风险
   - 性能问题
```

### 质量检查清单

```
提交代码前：
[ ] 代码符合规范
[ ] 测试全部通过
[ ] 无 lint 警告
[ ] 无类型错误
[ ] 错误处理完整
[ ] 变更已说明
```

---

*最后更新: 2026-01-14*
