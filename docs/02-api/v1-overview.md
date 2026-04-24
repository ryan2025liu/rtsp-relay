# API v1 概览（草案）

基础路径: `/api/v1`（待在 API 应用中挂载）  
当前已实现:
1. `GET /health`

计划实现（Sprint 1）:
1. `GET /api/v1/sources`
2. `POST /api/v1/sources`
3. `PUT /api/v1/sources/{id}`
4. `DELETE /api/v1/sources/{id}`
5. `POST /api/v1/jobs/{source_id}/start`
6. `POST /api/v1/jobs/{source_id}/stop`
7. `GET /api/v1/jobs/{source_id}/status`

范围说明：

1. 这些接口服务于单机、本地 Docker、内网运行场景。
2. MVP 以本地控制和转接闭环为目标，不引入复杂鉴权、批量调度、外部监控或公网部署接口。
3. `targets`、`logs`、`metrics` 等接口在 MVP 首批开发中后置。
