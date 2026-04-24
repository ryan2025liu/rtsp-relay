"""
[INPUT]: Task operations (start/stop/restart) with source config
[OUTPUT]: In-memory task status view
[POS]: Worker task manager skeleton
[DEPS]: dataclasses, typing, time
[PROTOCOL]:
  1. State machine changes must update docs/01-architecture.
  2. Replace in-memory storage with persistent model in later iterations.
"""

from dataclasses import dataclass
from time import time


@dataclass
class RelayJob:
    source_id: str
    status: str
    updated_at: float
    last_error: str | None = None


class RelayJobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, RelayJob] = {}

    def start(self, source_id: str) -> RelayJob:
        job = RelayJob(source_id=source_id, status="running", updated_at=time())
        self._jobs[source_id] = job
        return job

    def stop(self, source_id: str) -> RelayJob:
        job = self._jobs.get(source_id) or RelayJob(
            source_id=source_id, status="stopped", updated_at=time()
        )
        job.status = "stopped"
        job.updated_at = time()
        self._jobs[source_id] = job
        return job

    def status(self, source_id: str) -> RelayJob | None:
        return self._jobs.get(source_id)
