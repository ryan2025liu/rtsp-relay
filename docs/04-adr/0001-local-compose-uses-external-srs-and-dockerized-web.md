# ADR 0001: 本地 Compose 使用外部 SRS，并 Docker 化 Web

## 状态

已接受

## 背景

当前本地联调目标是验证 `relay-api`、`relay-web` 和媒体推流链路的闭环。团队已经有可用的局域网 SRS 服务，因此没有必要在本地 Compose 中重复启动一套 SRS 容器。

同时，Web 管理页已经具备稳定的本地操作入口，适合直接作为独立容器纳入联调环境，减少本机手工启动步骤。

## 决策

1. 本地 `docker-compose.local.yml` 只负责启动 `relay-api` 和 `relay-web`。
2. 推流目标通过 `DEFAULT_RTMP_BASE_URL` 显式指向局域网现成 SRS。
3. `relay-web` 采用 Docker 容器运行，并通过 `VITE_API_BASE_URL` 访问宿主机暴露的 API。

## 结果

1. 本地联调拓扑更贴近实际使用环境，且不会重复消耗 SRS 资源。
2. 前端和后端都可以通过 Docker Compose 一键启动。
3. 环境配置要求更明确，联调前必须提供可用的 SRS 地址。

## 影响

1. `README.md`、`docs/01-architecture`、`docs/03-operations` 需要同步更新。
2. 若局域网 SRS 地址发生变化，需要更新本地环境变量，而不是修改容器编排文件。
