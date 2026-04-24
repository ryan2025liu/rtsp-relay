# skybrain-rtsp-relay 开发宪法

版本: 1.0.0  
更新时间: 2026-04-25

## 1. 项目定位
1. 本项目是“本地视频流管理与转发平台”，部署在视频监控服务器。
2. 项目职责是管理视频源、编排转发任务、监控状态，并向外部标准 SRS 输出流。
3. 项目与业务系统（如 Agriguard）保持代码解耦，仅保留运行时契约。

## 2. 必须遵守的原则
1. 理解优先：改动前先阅读目标目录 `.folder.md` 和相关文件。
2. 最小变更：只实现当前需求，禁止一次性过度设计。
3. 文档同步：代码、目录、架构变更必须同步更新对应文档。
4. 默认可运维：所有功能必须可观察、可重启、可定位错误。
5. 安全优先：密钥脱敏、配置外置、最小权限。

## 3. 文档分层与更新协议
1. Level 1: `README.md`（项目总览与快速开始）
2. Level 2: `docs/`（架构、API、运维、ADR）
3. Level 3: `.folder.md`（目录职责、流程、约束）
4. Level 4: 文件 Header（关键模块输入/输出/位置）

更新触发:
1. 代码逻辑变更: 更新 Header
2. 目录结构变更: 更新 `.folder.md`
3. 接口与架构变更: 更新 `docs/02-api`、`docs/01-architecture`、`docs/04-adr`
4. 全局使用方式变化: 更新 `README.md`

## 4. 架构约束
1. 控制面: `apps/api` + `apps/web`
2. 媒体执行面: `apps/worker`（ffmpeg 任务编排）
3. 共享契约: `packages/common`
4. 部署与运行资产: `deploy/`、`configs/`、`scripts/`

分层调用:
1. `apps/web` 只调用 `apps/api`，不直接操作 worker 进程。
2. `apps/api` 通过任务管理接口调度 `apps/worker`。
3. `apps/worker` 不包含业务系统逻辑，只处理媒体任务。

## 5. 技术基线（MVP）
1. Backend: FastAPI (Python 3.11+)
2. Worker: ffmpeg + 进程编排
3. Frontend: React + Ant Design
4. DB: SQLite（MVP）+ PostgreSQL（生产可切换）
5. Stream Contract: `rtmp://<srs-host>:1935/live/<stream_key>`

## 6. API 与数据契约
1. `stream_key` 是跨系统共享主键，不允许隐式重写。
2. API 统一放在 `/api/v1/*`，返回结构必须稳定。
3. 任何破坏性 API 变更必须新增 ADR，并提供迁移说明。

## 7. 质量与测试
1. 关键路径必须覆盖:
   - 源配置增删改查
   - 任务启停重启
   - 断流自动重试
   - 推流目标不可达处理
2. 测试层次:
   - `tests/unit`
   - `tests/integration`
   - `tests/e2e`

## 8. 运维与可观测性
1. 每个任务必须暴露状态: `starting/running/stopped/error`
2. 记录统一字段: `source_id`、`stream_key`、`job_id`、`event`、`error`
3. 提供健康检查和基础 metrics 接口。

## 9. 禁止事项
1. 禁止硬编码密码/Token/RTSP 密钥。
2. 禁止在 worker 中写业务系统特定逻辑。
3. 禁止无文档更新的结构性改动。
4. 禁止把未脱敏 URL 打到公共日志。
