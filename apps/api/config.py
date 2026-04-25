"""
[INPUT]: Environment variables
[OUTPUT]: Runtime configuration for local API service
[POS]: Local service configuration
[DEPS]: os, pathlib, dataclasses
[PROTOCOL]:
  1. Keep defaults aligned with single-machine Docker deployment.
  2. Avoid adding multi-environment deployment complexity here.
"""

from dataclasses import dataclass
import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = ROOT_DIR / "runtime" / "data" / "relay.db"
DEFAULT_RTMP_BASE_URL = "rtmp://localhost:1935/live"
DEFAULT_LOG_DIR = ROOT_DIR / "runtime" / "logs"


@dataclass(frozen=True)
class AppConfig:
    database_path: Path
    default_rtmp_base_url: str
    ffmpeg_bin: str
    ffmpeg_loglevel: str
    ffmpeg_extra_args: str
    runtime_log_dir: Path
    relay_command_template: str
    max_retry_count: int
    retry_delay_seconds: float
    web_allowed_origins: list[str]


def load_config() -> AppConfig:
    database_path = Path(os.getenv("RELAY_DB_PATH", DEFAULT_DB_PATH))
    default_rtmp_base_url = os.getenv("DEFAULT_RTMP_BASE_URL", DEFAULT_RTMP_BASE_URL)
    ffmpeg_bin = os.getenv("RELAY_FFMPEG_BIN", "ffmpeg")
    ffmpeg_loglevel = os.getenv("RELAY_FFMPEG_LOGLEVEL", "info")
    ffmpeg_extra_args = os.getenv("RELAY_FFMPEG_EXTRA_ARGS", "")
    runtime_log_dir = Path(os.getenv("RELAY_RUNTIME_LOG_DIR", DEFAULT_LOG_DIR))
    relay_command_template = os.getenv("RELAY_COMMAND_TEMPLATE", "")
    max_retry_count = int(os.getenv("RELAY_MAX_RETRY_COUNT", "3"))
    retry_delay_seconds = float(os.getenv("RELAY_RETRY_DELAY_SECONDS", "5"))
    raw_origins = os.getenv(
        "RELAY_WEB_ALLOWED_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    )
    web_allowed_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return AppConfig(
        database_path=database_path,
        default_rtmp_base_url=default_rtmp_base_url,
        ffmpeg_bin=ffmpeg_bin,
        ffmpeg_loglevel=ffmpeg_loglevel,
        ffmpeg_extra_args=ffmpeg_extra_args,
        runtime_log_dir=runtime_log_dir,
        relay_command_template=relay_command_template,
        max_retry_count=max_retry_count,
        retry_delay_seconds=retry_delay_seconds,
        web_allowed_origins=web_allowed_origins,
    )
