# skybrain-rtsp-relay 目录结构规范

版本: 1.0.0

## 顶层目录

```text
skybrain-rtsp-relay/
├── apps/
│   ├── api/
│   ├── web/
│   └── worker/
├── packages/
│   └── common/
├── configs/
│   ├── env/
│   ├── ffmpeg-profiles/
│   └── supervisor/
├── deploy/
│   ├── docker/
│   ├── systemd/
│   └── nginx/
├── docs/
│   ├── 00-product/
│   ├── 01-architecture/
│   ├── 02-api/
│   ├── 03-operations/
│   └── 04-adr/
├── scripts/
│   ├── dev/
│   ├── ops/
│   └── release/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── rtsp-relay/
└── runtime/
```

## 约束

1. 业务代码只放 `apps/*` 与 `packages/common`。
2. 部署资产只放 `deploy/*`，不得混入应用逻辑。
3. 设计与操作文档只放 `docs/*`，禁止散落到脚本目录。
4. 跨层依赖限制：
   - `apps/web -> apps/api`
   - `apps/api -> apps/worker`（通过任务接口）
   - `apps/worker` 不反向依赖 `apps/web`
5. 新增目录必须补 `.folder.md`（关键目录）。

## 命名规范

1. 目录名与文件名使用 kebab-case。
2. ADR 使用 `NNNN-title.md` 命名（例如 `0001-task-lifecycle.md`）。
3. API 文档按版本分文件（例如 `v1-sources.md`）。
