"""
[INPUT]: Task operations (start/stop/restart) with source config
[OUTPUT]: In-memory task status view backed by local subprocesses
[POS]: Worker task manager for the single-node relay service
[DEPS]: dataclasses, datetime, pathlib, shlex, subprocess, threading
[PROTOCOL]:
  1. State machine changes must update docs/01-architecture.
  2. This manager only targets local single-process Docker/runtime execution.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from io import TextIOWrapper
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
from threading import RLock, Timer
from urllib.parse import quote


def utc_now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


def build_rtmp_publish_url(rtmp_base_url: str, stream_key: str, playback_vhost: str) -> str:
    """Build SRS-style RTMP publish URL; optional vhost query matches HTTP playback vhost."""
    out = f"{rtmp_base_url.rstrip('/')}/{stream_key}"
    v = (playback_vhost or "").strip()
    if not v:
        return out
    joiner = "&" if "?" in out else "?"
    return f"{out}{joiner}vhost={quote(v, safe='')}"


RTSP_CREDENTIALS_PATTERN = re.compile(r"([a-zA-Z][a-zA-Z0-9+\-.]*://)([^/@:\s]+):([^/@\s]+)@")
RTSP_TOKEN_AUTH_PATTERN = re.compile(r"([a-zA-Z][a-zA-Z0-9+\-.]*://)([^/@:\s]+)@")


@dataclass(frozen=True)
class RelayRuntimeConfig:
    ffmpeg_bin: str = "ffmpeg"
    ffmpeg_loglevel: str = "info"
    ffmpeg_extra_args: str = ""
    runtime_log_dir: Path | None = None
    command_template: str = ""
    max_retry_count: int = 3
    retry_delay_seconds: float = 5.0


@dataclass(frozen=True)
class RelaySource:
    id: str
    source_url: str
    stream_key: str
    transcode_mode: str


@dataclass(frozen=True)
class RelayTarget:
    id: str
    rtmp_base_url: str
    playback_vhost: str = ""


@dataclass
class RelayJob:
    source_id: str
    status: str
    updated_at: str
    pid: int | None = None
    started_at: str | None = None
    last_error: str | None = None
    retry_count: int = 0
    command: list[str] | None = None
    log_path: str | None = None


@dataclass(frozen=True)
class RelayJobDefinition:
    source: RelaySource
    target: RelayTarget


class RelayJobManager:
    def __init__(self, config: RelayRuntimeConfig | None = None) -> None:
        self.config = config or RelayRuntimeConfig()
        self._jobs: dict[str, RelayJob] = {}
        self._definitions: dict[str, RelayJobDefinition] = {}
        self._processes: dict[str, subprocess.Popen[str]] = {}
        self._log_handles: dict[str, TextIOWrapper] = {}
        self._retry_timers: dict[str, Timer] = {}
        self._stop_requested: set[str] = set()
        self._lock = RLock()
        if self.config.runtime_log_dir is not None:
            self.config.runtime_log_dir.mkdir(parents=True, exist_ok=True)

    def start(self, source: RelaySource, target: RelayTarget) -> RelayJob:
        with self._lock:
            self._cancel_retry_timer(source.id)
            self._stop_requested.discard(source.id)
            self._definitions[source.id] = RelayJobDefinition(source=source, target=target)
            self._cleanup_finished_process(source.id)
            running = self._processes.get(source.id)
            if running is not None and running.poll() is None:
                return self._jobs[source.id]

            command = self._build_command(source=source, target=target)
            now = utc_now_iso()
            log_path = self._log_path_for(source.id)
            process, log_handle = self._spawn_process(command=command, log_path=log_path)
            previous_job = self._jobs.get(source.id)
            job = RelayJob(
                source_id=source.id,
                status="running",
                updated_at=now,
                pid=process.pid,
                started_at=now,
                last_error=None,
                retry_count=previous_job.retry_count if previous_job is not None else 0,
                command=command,
                log_path=str(log_path) if log_path is not None else None,
            )
            self._processes[source.id] = process
            if log_handle is not None:
                self._log_handles[source.id] = log_handle
            self._jobs[source.id] = job
            return job

    def stop(self, source_id: str) -> RelayJob:
        with self._lock:
            self._stop_requested.add(source_id)
            self._cancel_retry_timer(source_id)
            process = self._processes.pop(source_id, None)
            log_handle = self._log_handles.pop(source_id, None)
            now = utc_now_iso()
            if process is not None and process.poll() is None:
                self._terminate_process(process)
            if log_handle is not None and not log_handle.closed:
                log_handle.close()

            job = self._jobs.get(source_id) or RelayJob(
                source_id=source_id,
                status="stopped",
                updated_at=now,
            )
            job.status = "stopped"
            job.updated_at = now
            job.pid = None
            job.last_error = None
            self._jobs[source_id] = job
            return job

    def restart(self, source: RelaySource, target: RelayTarget) -> RelayJob:
        with self._lock:
            self._stop_requested.discard(source.id)
        self.stop(source.id)
        with self._lock:
            existing = self._jobs.get(source.id)
            if existing is not None:
                existing.retry_count = 0
        return self.start(source=source, target=target)

    def status(self, source_id: str) -> RelayJob | None:
        with self._lock:
            self._cleanup_finished_process(source_id)
            return self._jobs.get(source_id)

    def remove(self, source_id: str) -> None:
        with self._lock:
            self._stop_requested.add(source_id)
            self._cancel_retry_timer(source_id)
            process = self._processes.pop(source_id, None)
            log_handle = self._log_handles.pop(source_id, None)
            if process is not None and process.poll() is None:
                self._terminate_process(process)
            if log_handle is not None and not log_handle.closed:
                log_handle.close()
            self._definitions.pop(source_id, None)
            self._jobs.pop(source_id, None)

    def shutdown(self) -> None:
        with self._lock:
            source_ids = list(self._definitions.keys() | self._jobs.keys())
        for source_id in source_ids:
            self.remove(source_id)

    def update_runtime_settings(
        self,
        ffmpeg_loglevel: str,
        ffmpeg_extra_args: str,
        max_retry_count: int,
        retry_delay_seconds: float,
    ) -> None:
        with self._lock:
            self.config = replace(
                self.config,
                ffmpeg_loglevel=ffmpeg_loglevel,
                ffmpeg_extra_args=ffmpeg_extra_args,
                max_retry_count=max_retry_count,
                retry_delay_seconds=retry_delay_seconds,
            )

    def _cleanup_finished_process(self, source_id: str) -> None:
        process = self._processes.get(source_id)
        if process is None:
            return
        return_code = process.poll()
        if return_code is None:
            return

        job = self._jobs.get(source_id)
        now = utc_now_iso()
        if job is None:
            self._processes.pop(source_id, None)
            self._close_log_handle(source_id)
            return

        job.pid = None
        job.updated_at = now
        if job.status != "stopped":
            if return_code == 0:
                job.status = "stopped"
            else:
                job.status = "error"
                job.last_error = self._summarize_error(source_id, return_code)
                self._schedule_retry(source_id)
        self._processes.pop(source_id, None)
        self._close_log_handle(source_id)

    def _build_command(self, source: RelaySource, target: RelayTarget) -> list[str]:
        normalized_source_url = self._normalize_source_url(source.source_url)
        rtmp_out = build_rtmp_publish_url(
            target.rtmp_base_url, source.stream_key, target.playback_vhost
        )
        if self.config.command_template:
            return shlex.split(
                self.config.command_template.format(
                    source_id=source.id,
                    source_url=normalized_source_url,
                    stream_key=source.stream_key,
                    target_id=target.id,
                    rtmp_out=rtmp_out,
                    transcode_mode=source.transcode_mode,
                )
            )

        command = [
            self.config.ffmpeg_bin,
            "-hide_banner",
            "-loglevel",
            self.config.ffmpeg_loglevel,
            "-rtsp_transport",
            "tcp",
            "-i",
            normalized_source_url,
        ]

        if source.transcode_mode == "transcode":
            command.extend(
                [
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-tune",
                    "zerolatency",
                    "-pix_fmt",
                    "yuv420p",
                    "-g",
                    "50",
                    "-keyint_min",
                    "50",
                    "-sc_threshold",
                    "0",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "64k",
                ]
            )
        else:
            command.extend(["-c", "copy"])

        if self.config.ffmpeg_extra_args:
            command.extend(shlex.split(self.config.ffmpeg_extra_args))

        command.extend(["-f", "flv", rtmp_out])
        return command

    def _spawn_process(
        self,
        command: list[str],
        log_path: Path | None,
    ) -> tuple[subprocess.Popen[str], TextIOWrapper | None]:
        if log_path is None:
            return (
                subprocess.Popen(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    start_new_session=True,
                ),
                None,
            )

        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_handle = open(log_path, "a", encoding="utf-8")
        log_handle.write(f"{utc_now_iso()} INFO starting relay command\n")
        log_handle.flush()
        return (
            subprocess.Popen(
                command,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,
            ),
            log_handle,
        )

    def _log_path_for(self, source_id: str) -> Path | None:
        if self.config.runtime_log_dir is None:
            return None
        return self.config.runtime_log_dir / f"{source_id}.log"

    def _close_log_handle(self, source_id: str) -> None:
        log_handle = self._log_handles.pop(source_id, None)
        if log_handle is not None and not log_handle.closed:
            log_handle.close()

    def _cancel_retry_timer(self, source_id: str) -> None:
        timer = self._retry_timers.pop(source_id, None)
        if timer is not None:
            timer.cancel()

    def read_logs(self, source_id: str, tail: int = 200) -> str:
        with self._lock:
            log_path = self._log_path_for(source_id)
            if log_path is None or not log_path.exists():
                return ""
            content = log_path.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            selected = lines[-tail:] if tail > 0 else lines
            return "\n".join(self._sanitize_log_text(line) for line in selected)

    def _normalize_source_url(self, source_url: str) -> str:
        if "://" in source_url:
            return source_url
        return f"rtsp://{source_url}"

    def _sanitize_log_text(self, text: str) -> str:
        text = RTSP_CREDENTIALS_PATTERN.sub(r"\1\2:***@", text)
        text = RTSP_TOKEN_AUTH_PATTERN.sub(r"\1(redacted)@", text)
        return text

    def _summarize_error(self, source_id: str, return_code: int) -> str:
        logs = self.read_logs(source_id, tail=20)
        for line in reversed(logs.splitlines()):
            stripped = line.strip()
            if stripped:
                return f"ffmpeg exited with code {return_code}: {stripped[:300]}"
        return f"ffmpeg exited with code {return_code}"

    def _terminate_process(self, process: subprocess.Popen[str]) -> None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=5)
        except ProcessLookupError:
            return
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)

    def _schedule_retry(self, source_id: str) -> None:
        if source_id in self._stop_requested:
            return

        job = self._jobs.get(source_id)
        definition = self._definitions.get(source_id)
        if job is None or definition is None:
            return
        if job.retry_count >= self.config.max_retry_count:
            return

        job.retry_count += 1
        delay = self.config.retry_delay_seconds
        timer = Timer(delay, self._retry_start, args=(source_id,))
        timer.daemon = True
        self._retry_timers[source_id] = timer
        timer.start()

    def _retry_start(self, source_id: str) -> None:
        with self._lock:
            self._retry_timers.pop(source_id, None)
            if source_id in self._stop_requested:
                return
            definition = self._definitions.get(source_id)
            if definition is None:
                return
        self.start(source=definition.source, target=definition.target)
