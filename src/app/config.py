from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, ValidationError


class HDRConfig(BaseModel):
    enabled: bool = False
    exposures: list[int] = Field(default_factory=lambda: [-2, 0, 2])


class StackingConfig(BaseModel):
    enabled: bool = False
    frames: int = 3
    alignment: str = Field(default="ecc")


class CaptureConfig(BaseModel):
    mode: str = Field(default="auto")  # auto|manual
    interval_day_sec: int = 30
    interval_dusk_sec: int = 5
    resolution: str = "4056x3040"
    hdr: HDRConfig = Field(default_factory=HDRConfig)
    stacking: StackingConfig = Field(default_factory=StackingConfig)


class MQTTConfig(BaseModel):
    enabled: bool = False
    broker: Optional[str] = None
    topic_latest_image: str = "timelapse/latest_image"


class S3Config(BaseModel):
    enabled: bool = False
    endpoint: Optional[str] = None
    bucket: Optional[str] = None


class StorageConfig(BaseModel):
    local_dir: str = "/data/timelapse"
    retention_days: int = 30
    s3: S3Config = Field(default_factory=S3Config)


class UIAuthConfig(BaseModel):
    type: str = "token"  # basic|token
    username: Optional[str] = None
    token: Optional[str] = None


class UIConfig(BaseModel):
    auth: UIAuthConfig = Field(default_factory=UIAuthConfig)


class PublishConfig(BaseModel):
    mqtt: MQTTConfig = Field(default_factory=MQTTConfig)


class AppConfig(BaseModel):
    capture: CaptureConfig = Field(default_factory=CaptureConfig)
    publish: PublishConfig = Field(default_factory=PublishConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    ui: UIConfig = Field(default_factory=UIConfig)


DEFAULT_CONFIG_PATH = Path(os.getenv("SKYLAPSE_CONFIG", "configs/config.yaml"))


def load_config(path: Path | str | None = None) -> AppConfig:
    """Load configuration from YAML with environment overrides.

    Environment overrides:
    - ADMIN_TOKEN: overrides ui.auth.token
    - SKYLAPSE_LOCAL_DIR: overrides storage.local_dir
    - SKYLAPSE_S3_ENDPOINT, SKYLAPSE_S3_BUCKET
    """
    cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if cfg_path.exists():
        with cfg_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}

    # Env overrides (no secrets hard-coded)
    ui_token = os.getenv("ADMIN_TOKEN")
    if ui_token:
        data.setdefault("ui", {}).setdefault("auth", {})["token"] = ui_token
    local_dir = os.getenv("SKYLAPSE_LOCAL_DIR")
    if local_dir:
        data.setdefault("storage", {})["local_dir"] = local_dir
    s3_endpoint = os.getenv("SKYLAPSE_S3_ENDPOINT")
    s3_bucket = os.getenv("SKYLAPSE_S3_BUCKET")
    if s3_endpoint or s3_bucket:
        s3 = data.setdefault("storage", {}).setdefault("s3", {})
        if s3_endpoint:
            s3["endpoint"] = s3_endpoint
        if s3_bucket:
            s3["bucket"] = s3_bucket

    try:
        return AppConfig.model_validate(data)
    except ValidationError as e:
        # Fail fast with clear error
        raise RuntimeError(f"Invalid configuration: {e}") from e
