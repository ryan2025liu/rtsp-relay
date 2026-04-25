# skybrain-rtsp-relay

本地视频流管理与转发服务。  
目标是在单机、本地 Docker、内网环境下，把多路摄像头统一接入并转发到外部标准 SRS，供 Agriguard 等项目共享使用。

## 当前状态

1. 已有可运行基础：`rtsp-relay/`（ffmpeg 拉流转推镜像）。
2. 已完成项目宪法和正式开发目录规划。
3. 已完成首批控制面 API + 任务编排，并补齐本地 Web 管理页与 Docker 化入口。

## 代码与业务边界

1. 与其他业务项目代码解耦，不直接依赖其前后端源码。
2. 仅保留运行时契约：
   - RTMP 转发协议：`rtmp://<srs-host>:1935/live/<stream_key>`
   - `stream_key` 作为跨项目共享标识
3. 不以复杂网络部署系统为目标，MVP 坚持单机本地 Docker 运行。

## 目录总览

1. `apps/api`: 控制面后端（FastAPI）
2. `apps/worker`: 媒体任务执行与 ffmpeg 编排
3. `apps/web`: 本地 Web 管理界面（已实现，可 Docker 化运行）
4. `packages/common`: 共享契约（schema/types/errors）
5. `configs`: 环境配置、ffmpeg profile、进程配置
6. `deploy`: 部署用 env 样例等（`docker-compose.server.yml` 在根目录）
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

## 本地 Docker 联调

如果要以当前控制面 API + Web 运行本地单机版本，使用：

```bash
docker compose -f docker-compose.local.yml up -d --build
```

启动后在浏览器打开 `http://127.0.0.1:5173`。

默认会启动：

1. `relay-api`：本地控制面 API，同时在容器内执行 `ffmpeg`
2. `relay-web`：本地 Web 管理台

`relay-web` 容器启动时会执行一次 `npm ci`，确保前端依赖与 `package-lock.json` 保持一致。

联调时不再启动本地 SRS 容器，请把局域网现成 SRS 地址写入 `DEFAULT_RTMP_BASE_URL`，例如：

```bash
DEFAULT_RTMP_BASE_URL=rtmp://192.168.1.50:1935/live
```

如果需要让局域网其他主机直接打开 Web，请同时设置：

```bash
VITE_API_BASE_URL=http://192.168.126.189:18081
RELAY_WEB_ALLOWED_ORIGINS=http://192.168.126.189:5174,http://127.0.0.1:5174,http://localhost:5174
```

如果本机 `5173` 已被占用，可以把 `RELAY_WEB_PORT` 改成别的空闲端口，比如 `5174`。

如果页面里出现“有流无画面”，优先检查 SRS 目标里的 `播放 vhost` 是否和实际 SRS 一致。该字段会同时用于 HLS/FLV 播放地址与 **ffmpeg 的 RTMP 推流地址**（附加 `?vhost=`），以便与 SRS 上配置的虚拟主机一致；修改后请对任务执行一次「重启」。

本地管理页里的预览窗口会通过 API 同源代理拉取 HLS，避免浏览器直连 SRS 的跨域问题。

本地 worker 的默认恢复策略：

1. 异常退出后按固定延迟自动重试
2. 默认最多重试 `3` 次
3. 默认重试间隔 `5` 秒
4. 可通过 `RELAY_MAX_RETRY_COUNT` 和 `RELAY_RETRY_DELAY_SECONDS` 调整

常用检查：

```bash
curl -sS http://127.0.0.1:18081/health
docker compose -f docker-compose.local.yml logs -f relay-api
docker compose -f docker-compose.local.yml logs -f relay-web
```

本地排障时常用接口：

```bash
curl -sS http://127.0.0.1:18081/api/v1/sources
curl -sS http://127.0.0.1:18081/api/v1/sources/<source_id>
curl -sS http://127.0.0.1:18081/api/v1/jobs/<source_id>/logs
```

运行时数据保存在：

1. `runtime/data`：SQLite
2. `runtime/logs`：worker 日志
3. `runtime/tmp`：临时文件

## MVP 约束

1. 单机运行，不做集群化部署。
2. 内网访问，不做公网暴露与复杂反向代理。
3. 以 `docker compose` 为主部署方式；固定 Linux 主机见下「服务器部署」。
4. 本地联调优先保证 API + Worker + Web 闭环，再做更高阶增强。

## 服务器部署（内网固定主机）

用于将本栈放到内网机（如 `lx@192.168.107.230`）长期运行：使用 **`docker-compose.server.yml`**。推荐将仓库放在 **`~/websites/rtsp-relay/`** 下再执行 compose。镜像内用 Nginx 只提供**静态**管理页（**宿主机不必再装** Nginx/反代；直连端口即可），与本地 Vite 开发服不同。详见 `docs/03-operations/deploy-lan-server.md`。

1. 一般**不必**再写 systemd 管理本应用：容器为 `restart: unless-stopped`，宿主机 `docker` 服务开机自启即可在重启后自动拉起。

2. 复制并编辑 `deploy/env.server.example` 为 `deploy/.env.server`（已默认 **18081**=API、**18088**=管理页，尽量避开与 SRS 常用 **8080** 的冲突；改端口要同步 CORS 与 `VITE_API_BASE_URL` 并重建 `relay-web`）。

3. 启动（在仓库根目录）：

```bash
docker compose -f docker-compose.server.yml --env-file deploy/.env.server up -d --build
```

4. SRS 与 `relay-api` 同机时，请将 `DEFAULT_RTMP_BASE_URL` 指到 **宿主机在局域网可访问的 IP**（例如 `rtmp://192.168.107.230:1935/live`），勿使用 `rtmp://127.0.0.1/...`（在容器内 `127.0.0.1` 不指向宿主机上的 SRS）。

5. 若仅变更了 `VITE_API_BASE_URL`（管理页要连的 API 地址），需**重新 build** `relay-web` 镜像后重启。
