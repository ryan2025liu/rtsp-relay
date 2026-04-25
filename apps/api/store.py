"""
[INPUT]: Source and job persistence operations
[OUTPUT]: SQLite-backed repository methods
[POS]: Local persistence layer
[DEPS]: sqlite3, pathlib, uuid, datetime
[PROTOCOL]:
  1. Persist only the minimum data needed for local Docker runtime.
  2. Keep schema simple enough to inspect and recover manually.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


def mask_source_url(url: str) -> str:
    if "@" not in url or "://" not in url:
        return url
    scheme, rest = url.split("://", 1)
    credentials, host = rest.split("@", 1)
    if ":" in credentials:
        username, _password = credentials.split(":", 1)
        return f"{scheme}://{username}:***@{host}"
    return f"{scheme}://***@{host}"


@dataclass
class SourceRecord:
    id: str
    name: str
    source_url: str
    stream_key: str
    target_id: str | None
    enabled: bool
    transcode_mode: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "source_url": self.source_url,
            "stream_key": self.stream_key,
            "target_id": self.target_id,
            "enabled": self.enabled,
            "transcode_mode": self.transcode_mode,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "source_url_masked": mask_source_url(self.source_url),
        }


@dataclass
class TargetRecord:
    id: str
    name: str
    rtmp_base_url: str
    is_default: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "rtmp_base_url": self.rtmp_base_url,
            "is_default": self.is_default,
        }


@dataclass
class JobRecord:
    source_id: str
    status: str
    pid: int | None
    started_at: str | None
    updated_at: str
    last_error: str | None
    retry_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "status": self.status,
            "pid": self.pid,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "last_error": self.last_error,
            "retry_count": self.retry_count,
        }


class SQLiteStore:
    def __init__(self, database_path: Path, default_rtmp_base_url: str) -> None:
        self.database_path = database_path
        self.default_rtmp_base_url = default_rtmp_base_url
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS relay_targets (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    rtmp_base_url TEXT NOT NULL,
                    is_default INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS stream_sources (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    stream_key TEXT NOT NULL,
                    target_id TEXT,
                    enabled INTEGER NOT NULL DEFAULT 0,
                    transcode_mode TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(target_id) REFERENCES relay_targets(id)
                );

                CREATE TABLE IF NOT EXISTS relay_jobs (
                    source_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    pid INTEGER,
                    started_at TEXT,
                    updated_at TEXT NOT NULL,
                    last_error TEXT,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY(source_id) REFERENCES stream_sources(id)
                );
                """
            )
            self._ensure_default_target(connection)
            connection.commit()

    def list_sources(self) -> list[SourceRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, name, source_url, stream_key, target_id, enabled,
                       transcode_mode, created_at, updated_at
                FROM stream_sources
                ORDER BY created_at ASC
                """
            ).fetchall()
        return [self._row_to_source(row) for row in rows]

    def get_source(self, source_id: str) -> SourceRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, name, source_url, stream_key, target_id, enabled,
                       transcode_mode, created_at, updated_at
                FROM stream_sources
                WHERE id = ?
                """,
                (source_id,),
            ).fetchone()
        return self._row_to_source(row) if row else None

    def create_source(self, payload: dict[str, Any]) -> SourceRecord:
        source_id = str(uuid4())
        now = utc_now_iso()
        target_id = payload.get("target_id") or self.get_default_target().id
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO stream_sources (
                    id, name, source_url, stream_key, target_id, enabled,
                    transcode_mode, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    payload["name"],
                    payload["source_url"],
                    payload["stream_key"],
                    target_id,
                    int(payload["enabled"]),
                    payload["transcode_mode"],
                    now,
                    now,
                ),
            )
            connection.commit()
        source = self.get_source(source_id)
        assert source is not None
        return source

    def update_source(self, source_id: str, payload: dict[str, Any]) -> SourceRecord | None:
        if self.get_source(source_id) is None:
            return None
        updated_at = utc_now_iso()
        target_id = payload.get("target_id") or self.get_default_target().id
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE stream_sources
                SET name = ?,
                    source_url = ?,
                    stream_key = ?,
                    target_id = ?,
                    enabled = ?,
                    transcode_mode = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    payload["name"],
                    payload["source_url"],
                    payload["stream_key"],
                    target_id,
                    int(payload["enabled"]),
                    payload["transcode_mode"],
                    updated_at,
                    source_id,
                ),
            )
            connection.commit()
        return self.get_source(source_id)

    def delete_source(self, source_id: str) -> bool:
        with self._connect() as connection:
            connection.execute("DELETE FROM relay_jobs WHERE source_id = ?", (source_id,))
            cursor = connection.execute(
                "DELETE FROM stream_sources WHERE id = ?",
                (source_id,),
            )
            connection.commit()
        return cursor.rowcount > 0

    def list_enabled_sources(self) -> list[SourceRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, name, source_url, stream_key, target_id, enabled,
                       transcode_mode, created_at, updated_at
                FROM stream_sources
                WHERE enabled = 1
                ORDER BY created_at ASC
                """
            ).fetchall()
        return [self._row_to_source(row) for row in rows]

    def get_default_target(self) -> TargetRecord:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, name, rtmp_base_url, is_default
                FROM relay_targets
                WHERE is_default = 1
                LIMIT 1
                """
            ).fetchone()
        assert row is not None
        return TargetRecord(
            id=row["id"],
            name=row["name"],
            rtmp_base_url=row["rtmp_base_url"],
            is_default=bool(row["is_default"]),
        )

    def list_targets(self) -> list[TargetRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, name, rtmp_base_url, is_default
                FROM relay_targets
                ORDER BY is_default DESC, name ASC
                """
            ).fetchall()
        return [self._row_to_target(row) for row in rows]

    def get_target(self, target_id: str) -> TargetRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, name, rtmp_base_url, is_default
                FROM relay_targets
                WHERE id = ?
                """,
                (target_id,),
            ).fetchone()
        return self._row_to_target(row) if row else None

    def create_target(self, payload: dict[str, Any]) -> TargetRecord:
        target_id = str(uuid4())
        is_default = bool(payload.get("is_default", False))
        with self._connect() as connection:
            if is_default:
                connection.execute("UPDATE relay_targets SET is_default = 0")
            connection.execute(
                """
                INSERT INTO relay_targets (id, name, rtmp_base_url, is_default)
                VALUES (?, ?, ?, ?)
                """,
                (
                    target_id,
                    payload["name"],
                    payload["rtmp_base_url"],
                    int(is_default),
                ),
            )
            connection.commit()
        target = self.get_target(target_id)
        assert target is not None
        return target

    def update_target(self, target_id: str, payload: dict[str, Any]) -> TargetRecord | None:
        existing = self.get_target(target_id)
        if existing is None:
            return None

        is_default = bool(payload.get("is_default", existing.is_default))
        with self._connect() as connection:
            if is_default:
                connection.execute("UPDATE relay_targets SET is_default = 0")
            connection.execute(
                """
                UPDATE relay_targets
                SET name = ?, rtmp_base_url = ?, is_default = ?
                WHERE id = ?
                """,
                (
                    payload["name"],
                    payload["rtmp_base_url"],
                    int(is_default),
                    target_id,
                ),
            )
            connection.commit()
        return self.get_target(target_id)

    def delete_target(self, target_id: str) -> bool:
        target = self.get_target(target_id)
        if target is None or target.is_default:
            return False

        default_target = self.get_default_target()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE stream_sources
                SET target_id = ?
                WHERE target_id = ?
                """,
                (default_target.id, target_id),
            )
            cursor = connection.execute(
                "DELETE FROM relay_targets WHERE id = ?",
                (target_id,),
            )
            connection.commit()
        return cursor.rowcount > 0

    def upsert_job(self, payload: JobRecord) -> JobRecord:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO relay_jobs (
                    source_id, status, pid, started_at, updated_at, last_error, retry_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    status = excluded.status,
                    pid = excluded.pid,
                    started_at = excluded.started_at,
                    updated_at = excluded.updated_at,
                    last_error = excluded.last_error,
                    retry_count = excluded.retry_count
                """,
                (
                    payload.source_id,
                    payload.status,
                    payload.pid,
                    payload.started_at,
                    payload.updated_at,
                    payload.last_error,
                    payload.retry_count,
                ),
            )
            connection.commit()
        stored = self.get_job(payload.source_id)
        assert stored is not None
        return stored

    def get_job(self, source_id: str) -> JobRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT source_id, status, pid, started_at, updated_at, last_error, retry_count
                FROM relay_jobs
                WHERE source_id = ?
                """,
                (source_id,),
            ).fetchone()
        if row is None:
            return None
        return JobRecord(
            source_id=row["source_id"],
            status=row["status"],
            pid=row["pid"],
            started_at=row["started_at"],
            updated_at=row["updated_at"],
            last_error=row["last_error"],
            retry_count=row["retry_count"],
        )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_default_target(self, connection: sqlite3.Connection) -> None:
        existing = connection.execute(
            "SELECT id FROM relay_targets WHERE is_default = 1 LIMIT 1"
        ).fetchone()
        if existing is not None:
            return
        connection.execute(
            """
            INSERT INTO relay_targets (id, name, rtmp_base_url, is_default)
            VALUES (?, ?, ?, 1)
            """,
            ("default", "Default SRS", self.default_rtmp_base_url),
        )

    def _row_to_source(self, row: sqlite3.Row) -> SourceRecord:
        return SourceRecord(
            id=row["id"],
            name=row["name"],
            source_url=row["source_url"],
            stream_key=row["stream_key"],
            target_id=row["target_id"],
            enabled=bool(row["enabled"]),
            transcode_mode=row["transcode_mode"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_target(self, row: sqlite3.Row) -> TargetRecord:
        return TargetRecord(
            id=row["id"],
            name=row["name"],
            rtmp_base_url=row["rtmp_base_url"],
            is_default=bool(row["is_default"]),
        )
