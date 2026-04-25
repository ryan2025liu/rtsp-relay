# 局域网 Linux 服务器部署（Docker）

面向单机、内网运维主机（示例：`lx@192.168.107.230`，SRS 可同机或他机）。

**systemd 自启本栈**：一般不需要。为容器写了 `restart: unless-stopped`；只要宿主机 **docker 服务**开机自启，主机重启后容器会随 Docker 起来。仅当你希望用一条 `systemctl` 在「未装 Docker 开机」等极端情况拉起栈时，才再包一层 compose 的 unit。

**反代/宿主机 Nginx**：不依赖。可浏览器 **直连** API 与 Web 映射端口。镜像内的 Nginx 只在 `relay-web` 容器里提供静态页（容器 80 → 你映射的宿主机端口，默认 `18088`），不是额外装一层公网反代。

## 1. 前置条件

1. 目标机已装 **Docker** 与 **Docker Compose 插件**（`docker compose version` 可用）。
2. 能 SSH 到目标机，并具备将代码放到目标机上的方式（`git clone` 或 `rsync`）。
3. 明确 **SRS 的地址**：若 SRS 与 relay 同机，推流请使用 **宿主机在局域网可访问的 IP**（如 `rtmp://192.168.107.230:1935/live`），**不要**在 compose 里写 `rtmp://127.0.0.1:...`（`127.0.0.1` 在 `relay-api` 容器内指向容器自身，通常无法连到宿主机上的 SRS）。

## 1.1 发布前占坑检查

默认本栈使用宿主机 **18081**（API）与 **18088**（管理页），以避开与 SRS 常用的 **1935/8080** 等冲突。改端口时务必同步 `VITE_API_BASE_URL`、`RELAY_WEB_ALLOWED_ORIGINS` 并**重建** `relay-web`。

```bash
ss -tlnp | egrep ':18081 |:18088 ' || true
# 有输出则换一组 RELAY_*_PORT 再 up --build
```

## 2. 在服务器上落盘

约定部署目录为 **`~/websites/rtsp-relay/`**（可改，以下路径按此书写）。

```bash
ssh lx@192.168.107.230
mkdir -p ~/websites && cd ~/websites
# 任选：git clone <你的仓库URL> rtsp-relay
# 或从开发机: rsync -av --filter=':- .git' ./rtsp-relay/ lx@192.168.107.230:~/websites/rtsp-relay/
cd rtsp-relay
```

## 3. 环境变量

```bash
cp deploy/env.server.example deploy/.env.server
```

按实际修改，至少检查：

| 变量 | 说明 |
| --- | --- |
| `DEFAULT_RTMP_BASE_URL` | 与 SRS 配置一致的 RTMP 基址（同机建议用局域网 IP） |
| `VITE_API_BASE_URL` | 浏览器访问的 API 根，如 `http://192.168.107.230:18081`（**无尾部斜杠**） |
| `RELAY_WEB_ALLOWED_ORIGINS` | 与 **管理页在浏览器中的 origin** 一致，如 `http://192.168.107.230:18088` |
| `RELAY_API_PORT` / `RELAY_WEB_PORT` | 与防火墙一致，默认 `18081` / `18088`（避开 **8080** 常见冲突） |

`VITE_API_BASE_URL` 在 **构建前端镜像时** 写入静态资源，修改后需对 `relay-web` 重新 `build` / `up --build`。

## 4. 启动

```bash
docker compose -f docker-compose.server.yml --env-file deploy/.env.server up -d --build
```

## 5. 验证

```bash
curl -sS http://127.0.0.1:18081/health
# 浏览器: http://192.168.107.230:18088 （与 RELAY_WEB_PORT 一致）
```

## 6. 防火墙（示例）

若使用 `ufw`，需允许映射端口，例如：

```bash
sudo ufw allow 18081/tcp
sudo ufw allow 18088/tcp
```

## 7. 数据与升级

- 数据默认落在部署目录下 `runtime/data/relay.db` 与 `runtime/logs/`；可通过 `RELAY_HOST_*_DIR` 指到独立路径（见 `deploy/env.server.example`）。
- 升级：拉取新代码后执行同一 `up -d --build`；有数据库 schema 变更时阅读当次发版说明。

## 8. 与 `docker-compose.local.yml` 的差异

| 项 | 本地 `docker-compose.local.yml` | 服务器 `docker-compose.server.yml` |
| --- | --- | --- |
| 前端 | 挂载 `apps/web` + Vite 开发服 | 多阶段构建；**仅容器内** Nginx 出静态页，**宿主机无**反代要求 |
| `VITE_API_BASE_URL` | 可运行时注入到 dev 容器 | 构建时写入 bundle，改 API 地址需**重建** `relay-web` |
| 默认同机端口 | 常映射 `5173` / `18081` | 默认 `18088` + `18081`（**不用 8080**，减少与 SRS 等冲突） |
