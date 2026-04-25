# API v1 概览（草案）

基础路径: `/api/v1`（待在 API 应用中挂载）  
当前已实现:
1. `GET /health`
2. `GET /api/v1/sources`
3. `POST /api/v1/sources`
4. `PUT /api/v1/sources/{id}`
5. `DELETE /api/v1/sources/{id}`
6. `GET /api/v1/targets`
7. `POST /api/v1/targets`
8. `PUT /api/v1/targets/{id}`
9. `DELETE /api/v1/targets/{id}`
10. `POST /api/v1/jobs/{source_id}/start`
11. `POST /api/v1/jobs/{source_id}/stop`
12. `POST /api/v1/jobs/{source_id}/restart`
13. `GET /api/v1/jobs/{source_id}/status`
14. `GET /api/v1/jobs/{source_id}/logs`

范围说明：

1. 这些接口服务于单机、本地 Docker、内网运行场景。
2. MVP 以本地控制和转接闭环为目标，不引入复杂鉴权、批量调度、外部监控或公网部署接口。
3. `metrics` 等接口在 MVP 首批开发中后置。

实现说明：

1. `sources` 当前使用本地 `SQLite` 持久化。
2. `targets` 当前支持最小 CRUD，并保护当前默认目标不被直接删除。
3. `jobs` 当前通过 API 进程内的 worker manager 管理运行状态，启动时会拉起本地子进程，并将状态快照回写本地数据库。
4. 若未显式提供 `target_id`，Source 会绑定当前默认目标。
5. 服务启动时会自动恢复 `enabled = true` 的 Source 对应任务。
6. `jobs/{source_id}/logs` 会返回本地日志文件的尾部内容，并对 RTSP 凭据做脱敏处理。
7. 异常退出任务会按本地固定延迟自动重试，直到达到最大重试次数。
