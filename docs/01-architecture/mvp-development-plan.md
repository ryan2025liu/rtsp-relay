# MVP 开发启动清单（v0.2）

## 目标

在单机本地 Docker 环境完成“可配置 + 可管理 + 可转发”的最小可用版本。

范围约束：

1. 单机运行
2. 内网访问
3. 部署方式保持为 `docker compose`
4. 先完成 API + Worker 闭环，Web 管理页后置且可选

## Sprint 1: 控制面后端基础

1. 初始化 `apps/api`（FastAPI）
2. 定义基础实体：`Source`、`Target`、`Job`
3. 提供接口：
   - `GET/POST/PUT/DELETE /api/v1/sources`
   - `POST /api/v1/jobs/{source_id}/start`
   - `POST /api/v1/jobs/{source_id}/stop`
   - `GET /api/v1/jobs/{source_id}/status`
4. 持久化使用本地 SQLite
5. API 直接联动 `apps/worker` 的进程内任务管理器

## Sprint 2: Worker 任务编排

1. 初始化 `apps/worker` 任务管理器
2. 实现 ffmpeg 命令模板化
3. 状态机：`starting -> running -> stopped/error`
4. 自动重试：轻量退避 + 最大重试
5. 日志脱敏与结构化字段输出

## Sprint 3: 本地管理页（可选）

1. 仅在 API 与 Worker 稳定后再启动 `apps/web`
2. 页面：
   - Source 列表与编辑
   - Job 状态列表与启停
3. 接入 `apps/api` 的标准接口
4. 不引入复杂前端部署链路

## Sprint 4: 联调与运维

1. 打通本地到外部 SRS 推流链路
2. 补充部署资产：
   - `docker-compose.yml`
   - 本地挂载目录约定
3. 完成运维文档初稿（启动、日志、重启、排障）

## 完成标准

1. 至少 10 路流稳定运行（按当前硬件规格可调整）。
2. 任一流断开后可自动恢复。
3. 可通过 API 完成增删改查与启停操作。
4. 如实现本地管理页，则其仅作为单机内网辅助界面。
