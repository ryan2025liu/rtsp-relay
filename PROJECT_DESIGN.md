# SkyBrain RTSP Relay 本地 Docker 转接服务设计文档（v0.2）

## 1. 文档目标

本文档用于指导 `skybrain-rtsp-relay` 从“单容器转推工具”演进为“单机、本地 Docker、内网运行”的视频流转接服务。

本项目的目标不是建设通用视频中台，也不是复杂的网络部署系统，而是在一台本地监控服务器上稳定完成多路视频源接入、转接、转发与最小运维控制。

---

## 2. 项目定位与边界

## 2.1 项目定位

本项目是一个本地内网运行的单机服务，部署形态以 `docker compose` 为主，用于：

1. 接入本地摄像头或视频源，MVP 优先支持 `RTSP`
2. 使用 `ffmpeg` 完成拉流、必要转码与转推
3. 将流转发到指定 SRS，MVP 优先支持 `RTMP`
4. 提供最小控制能力：
   - 视频源配置
   - 推流任务启动/停止
   - 任务状态查看

## 2.2 MVP 必须坚持的约束

1. 单机运行，不做多节点部署。
2. 默认运行在内网，不做公网访问方案设计。
3. 部署方式保持极简，以单个 `docker-compose.yml` 为核心。
4. 控制面优先提供本地 API，Web 管理页仅作为可选增强，不作为前置依赖。
5. 数据持久化优先使用本地挂载卷 + SQLite，不引入重型数据库。

## 2.3 非目标（第一阶段不做）

1. 不做 AI 检测业务逻辑。
2. 不做多租户、计费、复杂权限体系。
3. 不做跨地域集群、主从调度或服务编排平台。
4. 不做完整 NVR、录像编排、回放系统。
5. 不做复杂 Web 部署链路，不做反向代理、TLS、CDN、公网暴露方案。
6. 不做 Prometheus/Grafana 等完整监控体系，MVP 只保留基础状态查看能力。

---

## 3. 总体方案

采用“本地控制面 + 本地执行面”的最小架构，所有组件均运行在同一台机器上。

## 3.1 控制面（API）

职责：

1. 管理视频源配置
2. 管理转发目标配置
3. 提供任务启停接口
4. 返回任务运行状态

实现建议：

1. 使用 `Python FastAPI`
2. 先提供 REST API
3. 业务逻辑尽量保持简单，避免抽象过度

## 3.2 执行面（Worker）

职责：

1. 根据视频源配置生成 `ffmpeg` 命令
2. 启动和停止推流进程
3. 维护任务运行状态
4. 对失败任务做简单自动重试

实现建议：

1. 每路流对应一个 `ffmpeg` 子进程
2. 先以进程内管理器实现，不引入独立任务队列
3. 状态机保持最小化：`starting -> running -> stopped/error`

## 3.3 本地持久化

职责：

1. 保存视频源配置
2. 保存推流目标配置
3. 可选保存任务状态快照

实现建议：

1. 使用 `SQLite`
2. 数据文件通过 Docker volume 或本地挂载目录持久化
3. 不在 MVP 引入 PostgreSQL

## 3.4 可选本地 Web 页

如果后续需要本地管理界面，则只做内网简易页面，用于：

1. Source 列表查看
2. Source 新增/编辑
3. Job 启停
4. Job 状态查看

约束：

1. 不做复杂前后端分离部署链路
2. 不以 Web 为 MVP 阻塞项
3. 可以晚于 API 和 Worker 实现

---

## 4. 与业务系统的关系

## 4.1 解耦原则

本项目不依赖 Agriguard 或其他业务系统代码，不引入业务仓库 SDK，只提供通用的本地流转接能力。

## 4.2 运行时契约

保留以下最小契约：

1. 推流目标协议：`rtmp://<srs-host>:1935/live/<stream_key>`
2. `stream_key` 由业务系统约定和消费
3. 控制面通过标准 API 暴露任务状态

---

## 5. MVP 核心功能

## 5.1 视频源管理

MVP 支持：

1. 新增/编辑/删除视频源
2. 最小字段集：
   - `id`
   - `name`
   - `source_url`
   - `stream_key`
   - `target_id`
   - `enabled`
   - `transcode_mode`
3. URL 脱敏显示，避免日志直接泄露密钥

可后置字段：

1. `transport`
2. 独立 `auth` 配置对象
3. 高级 profile 参数

## 5.2 转发目标管理

MVP 支持：

1. 配置一个或多个 SRS 目标
2. 每个视频源绑定一个目标
3. 支持默认目标

不在 MVP 支持：

1. 多目标并发分发
2. 复杂路由规则

## 5.3 推流任务管理

MVP 支持：

1. 启动单路任务
2. 停止单路任务
3. 查询单路任务状态
4. 容器重启后按配置恢复 `enabled` 任务

重试策略保持简单：

1. 固定间隔或轻量指数退避
2. 最大重试次数
3. 超限后标记 `error`

不在 MVP 支持：

1. 批量启停
2. 熔断系统
3. 高级调度策略

## 5.4 协议支持

MVP 必做：

1. `RTSP` 输入
2. `RTMP` 输出到 SRS
3. 必要时将 `H.265` 转为 `H.264`

后续增强：

1. `SRT`
2. `HTTP-FLV`
3. ONVIF 发现
4. 多码率转发

---

## 6. 技术选型

## 6.1 后端

MVP 固定采用：

1. `Python FastAPI`
2. `Pydantic`
3. `SQLite`

理由：

1. 开发快，适合当前单机服务目标
2. 模型和接口落地成本低
3. 易于后续迭代 Worker 编排逻辑

## 6.2 Worker

MVP 固定采用：

1. `ffmpeg`
2. Python 进程管理

理由：

1. 满足转接和转码核心需求
2. 不需要引入额外任务框架
3. 易于在单机容器内运行

## 6.3 Web

MVP 不强制要求独立 Web 技术栈。

如果需要本地界面，优先原则：

1. 轻量
2. 本地访问
3. 部署简单

---

## 7. 数据模型（MVP）

## 7.1 `stream_sources`

1. `id`
2. `name`
3. `source_url`
4. `stream_key`
5. `target_id`
6. `enabled`
7. `transcode_mode`
8. `created_at`
9. `updated_at`

## 7.2 `relay_targets`

1. `id`
2. `name`
3. `rtmp_base_url`
4. `is_default`

## 7.3 `relay_jobs`

1. `source_id`
2. `status`
3. `pid`
4. `started_at`
5. `updated_at`
6. `last_error`
7. `retry_count`

说明：

1. `profiles` 在 MVP 先不做独立表，可用内置枚举或简化字段表达
2. `metrics` 先不做时间序列表，只保留基础运行状态

---

## 8. API 设计（MVP）

基础路径：`/api/v1`

## 8.1 健康检查

1. `GET /health`

## 8.2 Source 管理

1. `GET /sources`
2. `POST /sources`
3. `PUT /sources/{id}`
4. `DELETE /sources/{id}`

## 8.3 Job 管理

1. `POST /jobs/{source_id}/start`
2. `POST /jobs/{source_id}/stop`
3. `GET /jobs/{source_id}/status`

## 8.4 可后置接口

1. `targets` CRUD
2. `restart`
3. `logs`
4. `metrics`

---

## 9. 安全与运行约束

本项目默认运行于受控内网环境，因此安全要求按“本地服务”标准控制，不按公网系统设计。

MVP 要求：

1. 默认监听内网地址或本机地址
2. 敏感 URL 在接口返回和日志中脱敏
3. 不做复杂 JWT/RBAC 鉴权体系

后续如确有需要，再增补：

1. 基础访问口令
2. 反向代理
3. TLS

---

## 10. 部署方案

## 10.1 目标部署形态

唯一主路径为单机 `Docker Compose`：

1. `relay-api`
2. `relay-worker`
3. `relay-web`
4. 局域网现成 `srs` 服务

说明：

1. `relay-worker` 在 MVP 也可以与 `relay-api` 同进程或同容器运行
2. `SQLite` 直接使用本地文件，不需要单独数据库容器
3. 本地联调不再额外起 SRS 容器，`DEFAULT_RTMP_BASE_URL` 需要指向现成局域网 SRS

## 10.2 本地目录挂载建议

1. `runtime/data`：SQLite 数据文件
2. `runtime/logs`：服务日志
3. `runtime/tmp`：临时文件

## 10.3 运维方式

MVP 运维动作保持简单：

1. `docker compose up -d`
2. `docker compose ps`
3. `docker compose logs -f`
4. `docker compose restart`

不在 MVP 引入：

1. `systemd + compose` 双层编排
2. 自动备份体系
3. 外部监控平台

---

## 11. 开发原则

1. 先做可运行，再做可扩展。
2. 先保证单路闭环，再扩多路。
3. 先 API 和 Worker，Web 后置。
4. 所有设计以“单机、本地 Docker、内网运行”为上限，不向平台化方向过早抽象。
