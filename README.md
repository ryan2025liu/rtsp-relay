# skybrain-rtsp-relay

本地视频流管理与转发服务。  
目标是在单机、本地 Docker、内网环境下，把多路摄像头统一接入并转发到外部标准 SRS，供 Agriguard 等项目共享使用。

## 当前状态

1. 已有可运行基础：`rtsp-relay/`（ffmpeg 拉流转推镜像）。
2. 已完成项目宪法和正式开发目录规划。
3. 即将进入第一阶段开发（控制面 API + 任务编排，Web 管理页为后置可选项）。

## 代码与业务边界

1. 与其他业务项目代码解耦，不直接依赖其前后端源码。
2. 仅保留运行时契约：
   - RTMP 转发协议：`rtmp://<srs-host>:1935/live/<stream_key>`
   - `stream_key` 作为跨项目共享标识
3. 不以复杂网络部署系统为目标，MVP 坚持单机本地 Docker 运行。

## 目录总览

1. `apps/api`: 控制面后端（FastAPI）
2. `apps/worker`: 媒体任务执行与 ffmpeg 编排
3. `apps/web`: 本地 Web 管理界面（可选，后置实现）
4. `packages/common`: 共享契约（schema/types/errors）
5. `configs`: 环境配置、ffmpeg profile、进程配置
6. `deploy`: docker/systemd/nginx 部署资产
7. `docs`: 产品、架构、API、运维、ADR 文档
8. `scripts`: 开发、运维、发布脚本
9. `tests`: 单元/集成/e2e 测试
10. `rtsp-relay`: 现有独立 ffmpeg 镜像

## 基础转推快速开始（现有能力）

1. 准备环境变量
```bash
cp .env.example .env
```
2. 填写至少这三个变量
```bash
RTSP_RELAY_01_RTSP_URL=rtsp://...
RTSP_RELAY_01_STREAM_ID=cam-01
RTMP_RELAY_RTMP_BASE=rtmp://your-srs-host:1935/live
```
3. 启动
```bash
docker compose build
docker compose --env-file .env up -d
```
4. 查看日志
```bash
docker compose logs -f rtsp-relay-01
```

## 多路示例

```bash
cp docker-compose.streams.example.yml docker-compose.streams.yml
docker compose --env-file .env -f docker-compose.yml -f docker-compose.streams.yml up -d
```

## 开发规范入口

1. 宪法: `.cursor/CONSTITUTION.md`
2. Cursor 规则: `.cursorrules`
3. 实施设计: `PROJECT_DESIGN.md`

## 开发启动（已创建骨架）

1. 启动 API 开发服务：
```bash
bash scripts/dev/start-api.sh
```
2. 健康检查：
```bash
curl -sS http://127.0.0.1:18081/health
```

## MVP 约束

1. 单机运行，不做集群化部署。
2. 内网访问，不做公网暴露与复杂反向代理。
3. 以 `docker compose` 为主部署方式。
4. 先完成 API + Worker 闭环，再决定是否补本地 Web 管理页。
