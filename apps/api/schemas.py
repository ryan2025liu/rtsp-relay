"""
[INPUT]: API payloads for sources and jobs
[OUTPUT]: Pydantic request and response models
[POS]: API schema layer
[DEPS]: pydantic
[PROTOCOL]:
  1. Keep models focused on local single-node relay control.
  2. Avoid premature fields for non-MVP features.
  3. Target payloads may carry playback configuration used by the Web preview links.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


JobStatus = Literal["starting", "running", "stopped", "error"]
TranscodeMode = Literal["copy", "transcode"]


class HealthResponse(BaseModel):
    status: str
    service: str


class SourceBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    source_url: str = Field(min_length=1, max_length=2000)
    stream_key: str = Field(min_length=1, max_length=200)
    target_id: str | None = Field(default=None, max_length=64)
    enabled: bool = False
    transcode_mode: TranscodeMode = "copy"


class SourceCreate(SourceBase):
    pass


class SourceUpdate(SourceBase):
    pass


class SourceRead(SourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: str
    updated_at: str
    source_url_masked: str


class TargetBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    rtmp_base_url: str = Field(min_length=1, max_length=1000)
    playback_vhost: str = Field(default="", max_length=200)
    is_default: bool = False


class TargetCreate(TargetBase):
    pass


class TargetUpdate(TargetBase):
    pass


class TargetRead(TargetBase):
    id: str


class JobRead(BaseModel):
    source_id: str
    status: JobStatus
    pid: int | None = None
    started_at: str | None = None
    updated_at: str
    last_error: str | None = None
    retry_count: int = 0


class JobLogsRead(BaseModel):
    source_id: str
    logs: str


class SourceDetailRead(BaseModel):
    source: SourceRead
    target: TargetRead
    job: JobRead
    recent_logs: str


class SettingsRead(BaseModel):
    ffmpeg_loglevel: str
    ffmpeg_extra_args: str
    max_retry_count: int
    retry_delay_seconds: float
    updated_at: str


class SettingsUpdate(BaseModel):
    ffmpeg_loglevel: str = Field(min_length=1, max_length=32)
    ffmpeg_extra_args: str = Field(default="", max_length=1000)
    max_retry_count: int = Field(ge=0, le=20)
    retry_delay_seconds: float = Field(ge=0, le=300)


class ErrorResponse(BaseModel):
    detail: str
