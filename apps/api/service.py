"""
[INPUT]: Source management and job control requests
[OUTPUT]: Service-layer domain operations for local relay control
[POS]: Application service layer
[DEPS]: apps.api.store, apps.worker.manager
[PROTOCOL]:
  1. Keep behavior aligned with local single-host relay service goals.
  2. Return simple domain dictionaries for API serialization.
"""

from __future__ import annotations

from apps.api.store import JobRecord, SQLiteStore, utc_now_iso
from apps.worker.manager import RelayJobManager, RelaySource, RelayTarget


class RelayService:
    def __init__(self, store: SQLiteStore, job_manager: RelayJobManager) -> None:
        self.store = store
        self.job_manager = job_manager
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        self.store.initialize()
        self.recover_enabled_jobs()
        self._initialized = True

    def shutdown(self) -> None:
        self.job_manager.shutdown()

    def list_sources(self) -> list[dict[str, object]]:
        return [record.to_dict() for record in self.store.list_sources()]

    def get_source_detail(self, source_id: str, log_tail: int = 100) -> dict[str, object] | None:
        source = self.store.get_source(source_id)
        if source is None:
            return None

        target = self._resolve_target_for_source(source.target_id)
        job = self.get_job_status(source_id)
        assert job is not None
        logs = self.job_manager.read_logs(source_id=source_id, tail=log_tail)

        return {
            "source": source.to_dict(),
            "target": target.to_dict(),
            "job": job,
            "recent_logs": logs,
        }

    def list_targets(self) -> list[dict[str, object]]:
        return [record.to_dict() for record in self.store.list_targets()]

    def get_settings(self) -> dict[str, object]:
        return self.store.get_settings().to_dict()

    def update_settings(self, payload: dict[str, object]) -> dict[str, object]:
        settings = self.store.update_settings(payload)
        self.job_manager.update_runtime_settings(
            ffmpeg_loglevel=settings.ffmpeg_loglevel,
            ffmpeg_extra_args=settings.ffmpeg_extra_args,
            max_retry_count=settings.max_retry_count,
            retry_delay_seconds=settings.retry_delay_seconds,
        )
        return settings.to_dict()

    def create_target(self, payload: dict[str, object]) -> dict[str, object]:
        target = self.store.create_target(payload)
        return target.to_dict()

    def update_target(self, target_id: str, payload: dict[str, object]) -> dict[str, object] | None:
        target = self.store.update_target(target_id, payload)
        if target is None:
            return None
        return target.to_dict()

    def delete_target(self, target_id: str) -> bool:
        return self.store.delete_target(target_id)

    def create_source(self, payload: dict[str, object]) -> dict[str, object]:
        source = self.store.create_source(payload)
        return source.to_dict()

    def update_source(self, source_id: str, payload: dict[str, object]) -> dict[str, object] | None:
        source = self.store.update_source(source_id, payload)
        if source is None:
            return None
        return source.to_dict()

    def delete_source(self, source_id: str) -> bool:
        self.job_manager.remove(source_id)
        return self.store.delete_source(source_id)

    def start_job(self, source_id: str) -> dict[str, object] | None:
        source = self.store.get_source(source_id)
        if source is None:
            return None
        return self._start_source_runtime(source_id=source.id)

    def stop_job(self, source_id: str) -> dict[str, object] | None:
        source = self.store.get_source(source_id)
        if source is None:
            return None
        runtime_job = self.job_manager.stop(source_id)
        stored = self.store.upsert_job(
            JobRecord(
                source_id=runtime_job.source_id,
                status=runtime_job.status,
                pid=runtime_job.pid,
                started_at=runtime_job.started_at,
                updated_at=runtime_job.updated_at,
                last_error=runtime_job.last_error,
                retry_count=runtime_job.retry_count,
            )
        )
        return stored.to_dict()

    def restart_job(self, source_id: str) -> dict[str, object] | None:
        source = self.store.get_source(source_id)
        if source is None:
            return None
        target = self._resolve_target_for_source(source.target_id)
        runtime_job = self.job_manager.restart(
            source=RelaySource(
                id=source.id,
                source_url=source.source_url,
                stream_key=source.stream_key,
                transcode_mode=source.transcode_mode,
            ),
            target=RelayTarget(id=target.id, rtmp_base_url=target.rtmp_base_url),
        )
        stored = self.store.upsert_job(
            JobRecord(
                source_id=runtime_job.source_id,
                status=runtime_job.status,
                pid=runtime_job.pid,
                started_at=runtime_job.started_at,
                updated_at=runtime_job.updated_at,
                last_error=runtime_job.last_error,
                retry_count=runtime_job.retry_count,
            )
        )
        return stored.to_dict()

    def recover_enabled_jobs(self) -> None:
        for source in self.store.list_enabled_sources():
            self._start_source_runtime(source_id=source.id)

    def get_job_status(self, source_id: str) -> dict[str, object] | None:
        if self.store.get_source(source_id) is None:
            return None
        runtime_job = self.job_manager.status(source_id)
        if runtime_job is not None:
            return {
                "source_id": runtime_job.source_id,
                "status": runtime_job.status,
                "pid": runtime_job.pid,
                "started_at": runtime_job.started_at,
                "updated_at": runtime_job.updated_at,
                "last_error": runtime_job.last_error,
                "retry_count": runtime_job.retry_count,
            }

        stored = self.store.get_job(source_id)
        if stored is not None:
            return stored.to_dict()

        return {
            "source_id": source_id,
            "status": "stopped",
            "pid": None,
            "started_at": None,
            "updated_at": utc_now_iso(),
            "last_error": None,
            "retry_count": 0,
        }

    def get_job_logs(self, source_id: str, tail: int = 200) -> dict[str, object] | None:
        if self.store.get_source(source_id) is None:
            return None
        return {
            "source_id": source_id,
            "logs": self.job_manager.read_logs(source_id=source_id, tail=tail),
        }

    def _start_source_runtime(self, source_id: str) -> dict[str, object] | None:
        source = self.store.get_source(source_id)
        if source is None:
            return None

        target = self._resolve_target_for_source(source.target_id)
        runtime_job = self.job_manager.start(
            source=RelaySource(
                id=source.id,
                source_url=source.source_url,
                stream_key=source.stream_key,
                transcode_mode=source.transcode_mode,
            ),
            target=RelayTarget(id=target.id, rtmp_base_url=target.rtmp_base_url),
        )
        stored = self.store.upsert_job(
            JobRecord(
                source_id=runtime_job.source_id,
                status=runtime_job.status,
                pid=runtime_job.pid,
                started_at=runtime_job.started_at,
                updated_at=runtime_job.updated_at,
                last_error=runtime_job.last_error,
                retry_count=runtime_job.retry_count,
            )
        )
        return stored.to_dict()

    def _resolve_target_for_source(self, target_id: str | None):
        target = self.store.get_target(target_id or self.store.get_default_target().id)
        if target is None:
            return self.store.get_default_target()
        return target
