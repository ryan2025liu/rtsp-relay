# ADR 0002: 服务器单机 Docker 部署与 Nginx 静态管理页

## 状态

已采纳（2026-04-25）

## 背景

`docker-compose.local.yml` 将 Web 以 Vite 开发服挂载源码运行，适合本机联调。部署到内网固定主机（如与 SRS 同机）时，需要：

1. 不依赖宿主机上源码挂载的可重复运行方式。
2. 对浏览器暴露稳定的管理页与 API 端口，并与 CORS、RTMP 推流网络路径一致。

## 决策

1. 增加 **`docker-compose.server.yml`**，与 `docker-compose.local.yml` 并列；数据卷仍使用 `runtime/` 或可选宿主机绝对路径。
2. 管理页通过 **`apps/web/Dockerfile.prod` + Nginx** 提供构建后的静态资源；`VITE_API_BASE_URL` 在 **build** 阶段通过 `build.args` 注入。
3. 文档中明确：SRS 与堆栈同机时，`DEFAULT_RTMP_BASE_URL` 使用**局域网可访问的宿主机地址**，避免在 bridge 网络下误用 `127.0.0.1` 指代容器环回。

## 后果

- 仅变更 API 对外地址时，需对 `relay-web` 镜像**重新 build**；运维需在 `docs/03-operations` 中随发版说明。
- 不引入多副本编排与 Kubernetes 假设，保持与项目「单机、内网」基线一致。
