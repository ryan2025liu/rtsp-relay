# 03-operations

运维与部署文档目录。  
首批需要沉淀：
1. 单机部署手册（Docker/systemd）
2. 日志与监控排障手册
3. 升级/回滚流程
4. 日报进度：`progress-YYYY-MM-DD.md`

当前本地联调约定：
1. `relay-api` 与 `relay-web` 使用 `docker compose -f docker-compose.local.yml up -d --build` 启动
2. SRS 由局域网现成服务提供，`DEFAULT_RTMP_BASE_URL` 需要显式指向该地址
3. 若需局域网其他主机访问 Web，需要同时设置 `VITE_API_BASE_URL` 和 `RELAY_WEB_ALLOWED_ORIGINS`
4. 如本机 5173 端口被占用，可将 `RELAY_WEB_PORT` 改到空闲端口（本次验证使用 5174）
5. 若页面显示有流无画面，优先核对目标配置里的 `playback_vhost`
6. 预览窗口通过 API 同源代理拉取 HLS，避免浏览器直连 SRS 的跨域问题
7. `relay-web` 容器启动时会执行 `npm ci`，确保前端依赖自动和锁文件对齐
8. 预览链接必须使用 `VITE_API_BASE_URL` 对应的 API origin，不能相对写成前端 origin

服务器单机部署见 **`deploy-lan-server.md`**（`docker-compose.server.yml` + `deploy/env.server.example` + `apps/web/Dockerfile.prod`）。推荐部署目录 **`~/websites/rtsp-relay/`**。

管理页每 5 秒会静默刷新列表与当前通道详情（**不**再全屏「正在加载」、**不**用服务端数据覆盖正在编辑的表单），避免误以为是整页刷新；修改前端后请对 `relay-web` 重新 `build`。
