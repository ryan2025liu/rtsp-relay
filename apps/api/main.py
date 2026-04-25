"""
[INPUT]: HTTP requests
[OUTPUT]: JSON responses
[POS]: API entrypoint for control plane
[DEPS]: fastapi, pydantic
[PROTOCOL]:
  1. Any route or lifecycle change must update this header and docs/02-api.
  2. Keep this file as thin bootstrap; business logic should move to modules.
"""

from contextlib import asynccontextmanager
import sys
from pathlib import Path
import re
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from starlette.background import BackgroundTask


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apps.api.config import AppConfig, load_config
from apps.api.schemas import (
    HealthResponse,
    JobLogsRead,
    JobRead,
    SourceCreate,
    SourceDetailRead,
    SourceRead,
    SourceUpdate,
    SettingsRead,
    SettingsUpdate,
    TargetCreate,
    TargetRead,
    TargetUpdate,
)
from apps.api.service import RelayService
from apps.api.store import SQLiteStore
from apps.worker.manager import RelayJobManager, RelayRuntimeConfig


def build_service(config: AppConfig | None = None) -> RelayService:
    app_config = config or load_config()
    store = SQLiteStore(
        database_path=app_config.database_path,
        default_rtmp_base_url=app_config.default_rtmp_base_url,
        default_ffmpeg_loglevel=app_config.ffmpeg_loglevel,
        default_ffmpeg_extra_args=app_config.ffmpeg_extra_args,
        default_max_retry_count=app_config.max_retry_count,
        default_retry_delay_seconds=app_config.retry_delay_seconds,
    )
    manager = RelayJobManager(
        RelayRuntimeConfig(
            ffmpeg_bin=app_config.ffmpeg_bin,
            ffmpeg_loglevel=app_config.ffmpeg_loglevel,
            ffmpeg_extra_args=app_config.ffmpeg_extra_args,
            runtime_log_dir=app_config.runtime_log_dir,
            command_template=app_config.relay_command_template,
            max_retry_count=app_config.max_retry_count,
            retry_delay_seconds=app_config.retry_delay_seconds,
        )
    )
    relay_service = RelayService(store=store, job_manager=manager)
    relay_service.app_config = app_config
    return relay_service


def build_preview_upstream_url(target_rtmp_base_url: str, proxy_path: str, query: str) -> str:
    parsed = urlparse(target_rtmp_base_url)
    host = parsed.hostname or "127.0.0.1"
    upstream_url = f"http://{host}:8080/{proxy_path.lstrip('/')}"
    if query:
        upstream_url = f"{upstream_url}?{query}"
    return upstream_url


def filter_preview_headers(headers: httpx.Headers) -> dict[str, str]:
    allowed_headers = {
        "content-type",
        "content-length",
        "cache-control",
        "accept-ranges",
        "content-range",
        "last-modified",
        "etag",
    }
    return {
        key: value
        for key, value in headers.items()
        if key.lower() in allowed_headers
    }


def rewrite_hls_manifest(manifest_text: str, target_id: str) -> str:
    proxy_prefix = f"/api/v1/preview/{target_id}"
    rewritten_lines: list[str] = []
    for line in manifest_text.splitlines():
        if line.startswith("#"):
            line = re.sub(
                r'URI="(/[^"]+)"',
                lambda match: f'URI="{proxy_prefix}{match.group(1)}"',
                line,
            )
        elif line.startswith("/"):
            if ".m3u8" in line:
                line = f"{proxy_prefix}{line}"
            else:
                line = line.lstrip("/")
        elif line:
            if ".m3u8" in line:
                line = f"{proxy_prefix}/{line}"
        rewritten_lines.append(line)
    return "\n".join(rewritten_lines)


def create_app(service: RelayService | None = None) -> FastAPI:
    relay_service = service or build_service()
    app_config = getattr(relay_service, "app_config", load_config())
    relay_service.initialize()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        relay_service.initialize()
        try:
            yield
        finally:
            relay_service.shutdown()

    app = FastAPI(
        title="skybrain-rtsp-relay-api",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.relay_service = relay_service
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_config.web_allowed_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service="api")

    @app.get("/api/v1/sources", response_model=list[SourceRead])
    def list_sources() -> list[SourceRead]:
        return [
            SourceRead.model_validate(item)
            for item in relay_service.list_sources()
        ]

    @app.get("/api/v1/sources/{source_id}", response_model=SourceDetailRead)
    def get_source_detail(source_id: str, log_tail: int = 100) -> SourceDetailRead:
        detail = relay_service.get_source_detail(source_id=source_id, log_tail=log_tail)
        if detail is None:
            raise HTTPException(status_code=404, detail="source not found")
        return SourceDetailRead.model_validate(detail)

    @app.post("/api/v1/sources", response_model=SourceRead, status_code=201)
    def create_source(payload: SourceCreate) -> SourceRead:
        created = relay_service.create_source(payload.model_dump())
        return SourceRead.model_validate(created)

    @app.put("/api/v1/sources/{source_id}", response_model=SourceRead)
    def update_source(source_id: str, payload: SourceUpdate) -> SourceRead:
        updated = relay_service.update_source(source_id, payload.model_dump())
        if updated is None:
            raise HTTPException(status_code=404, detail="source not found")
        return SourceRead.model_validate(updated)

    @app.delete("/api/v1/sources/{source_id}", status_code=204)
    def delete_source(source_id: str) -> None:
        deleted = relay_service.delete_source(source_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="source not found")

    @app.get("/api/v1/targets", response_model=list[TargetRead])
    def list_targets() -> list[TargetRead]:
        return [TargetRead.model_validate(item) for item in relay_service.list_targets()]

    @app.get("/api/v1/targets/{target_id}", response_model=TargetRead)
    def get_target(target_id: str) -> TargetRead:
        target = relay_service.get_target(target_id)
        if target is None:
            raise HTTPException(status_code=404, detail="target not found")
        return TargetRead.model_validate(target)

    @app.get("/api/v1/settings", response_model=SettingsRead)
    def get_settings() -> SettingsRead:
        return SettingsRead.model_validate(relay_service.get_settings())

    @app.put("/api/v1/settings", response_model=SettingsRead)
    def update_settings(payload: SettingsUpdate) -> SettingsRead:
        updated = relay_service.update_settings(payload.model_dump())
        return SettingsRead.model_validate(updated)

    @app.post("/api/v1/targets", response_model=TargetRead, status_code=201)
    def create_target(payload: TargetCreate) -> TargetRead:
        created = relay_service.create_target(payload.model_dump())
        return TargetRead.model_validate(created)

    @app.put("/api/v1/targets/{target_id}", response_model=TargetRead)
    def update_target(target_id: str, payload: TargetUpdate) -> TargetRead:
        updated = relay_service.update_target(target_id, payload.model_dump())
        if updated is None:
            raise HTTPException(status_code=404, detail="target not found")
        return TargetRead.model_validate(updated)

    @app.delete("/api/v1/targets/{target_id}", status_code=204)
    def delete_target(target_id: str) -> None:
        deleted = relay_service.delete_target(target_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="target not found or protected")

    @app.api_route("/api/v1/preview/{target_id}/{proxy_path:path}", methods=["GET", "HEAD"])
    async def preview_proxy(
        target_id: str,
        proxy_path: str,
        request: Request,
    ) -> Response:
        target = relay_service.get_target(target_id)
        if target is None:
            raise HTTPException(status_code=404, detail="target not found")

        upstream_query = request.url.query
        if target.get("playback_vhost") and "vhost=" not in upstream_query:
            upstream_query = (
                f"{upstream_query}&vhost={target['playback_vhost']}"
                if upstream_query
                else f"vhost={target['playback_vhost']}"
            )

        upstream_url = build_preview_upstream_url(
            target_rtmp_base_url=target["rtmp_base_url"],
            proxy_path=proxy_path,
            query=upstream_query,
        )

        client = httpx.AsyncClient(follow_redirects=True, timeout=None)
        upstream_request = client.build_request(
            request.method,
            upstream_url,
            headers={
                key: value
                for key, value in request.headers.items()
                if key.lower() in {"range", "user-agent", "accept", "referer"}
            },
        )
        upstream_response = await client.send(upstream_request, stream=True)

        if request.method == "HEAD":
            await upstream_response.aclose()
            await client.aclose()
            return Response(
                status_code=upstream_response.status_code,
                headers=filter_preview_headers(upstream_response.headers),
            )

        content_type = upstream_response.headers.get("content-type", "")
        if proxy_path.endswith(".m3u8") or "mpegurl" in content_type:
            manifest_text = (await upstream_response.aread()).decode("utf-8", errors="replace")
            await upstream_response.aclose()
            await client.aclose()
            rewritten_manifest = rewrite_hls_manifest(manifest_text, target_id)
            manifest_headers = filter_preview_headers(upstream_response.headers)
            manifest_headers.pop("content-length", None)
            return Response(
                content=rewritten_manifest,
                status_code=upstream_response.status_code,
                media_type="application/vnd.apple.mpegurl",
                headers=manifest_headers,
            )

        async def stream_body():
            async for chunk in upstream_response.aiter_bytes():
                yield chunk

        async def close_stream() -> None:
            await upstream_response.aclose()
            await client.aclose()

        return StreamingResponse(
            stream_body(),
            status_code=upstream_response.status_code,
            headers=filter_preview_headers(upstream_response.headers),
            media_type=upstream_response.headers.get("content-type"),
            background=BackgroundTask(close_stream),
        )

    @app.post("/api/v1/jobs/{source_id}/start", response_model=JobRead)
    def start_job(source_id: str) -> JobRead:
        job = relay_service.start_job(source_id)
        if job is None:
            raise HTTPException(status_code=404, detail="source not found")
        return JobRead.model_validate(job)

    @app.post("/api/v1/jobs/{source_id}/stop", response_model=JobRead)
    def stop_job(source_id: str) -> JobRead:
        job = relay_service.stop_job(source_id)
        if job is None:
            raise HTTPException(status_code=404, detail="source not found")
        return JobRead.model_validate(job)

    @app.post("/api/v1/jobs/{source_id}/restart", response_model=JobRead)
    def restart_job(source_id: str) -> JobRead:
        job = relay_service.restart_job(source_id)
        if job is None:
            raise HTTPException(status_code=404, detail="source not found")
        return JobRead.model_validate(job)

    @app.get("/api/v1/jobs/{source_id}/status", response_model=JobRead)
    def get_job_status(source_id: str) -> JobRead:
        job = relay_service.get_job_status(source_id)
        if job is None:
            raise HTTPException(status_code=404, detail="source not found")
        return JobRead.model_validate(job)

    @app.get("/api/v1/jobs/{source_id}/logs", response_model=JobLogsRead)
    def get_job_logs(source_id: str, tail: int = 200) -> JobLogsRead:
        logs = relay_service.get_job_logs(source_id=source_id, tail=tail)
        if logs is None:
            raise HTTPException(status_code=404, detail="source not found")
        return JobLogsRead.model_validate(logs)

    return app


app = create_app()
