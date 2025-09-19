from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config import AppConfig, load_config
from app.capture import CaptureService
from app.camera import get_camera
from app.db import list_media
from datetime import datetime, timezone, timedelta


class LatestResponse(BaseModel):
    image_url: str | None
    captured_at: str | None
    exposure: dict | None
    white_balance: dict | None


def get_config() -> AppConfig:
    return load_config()


_bearer_scheme = HTTPBearer(auto_error=False)


def admin_auth_dependency(
    cfg: Annotated[AppConfig, Depends(get_config)],
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> None:
    """Require Authorization: Bearer <token> for admin endpoints.

    The token is read from cfg.ui.auth.token or ADMIN_TOKEN env. We intentionally do not
    log tokens. Returns None on success, raises HTTPException otherwise.
    """
    token = cfg.ui.auth.token or os.getenv("ADMIN_TOKEN")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "admin_token_not_configured",
                "action": "Set ADMIN_TOKEN env var or ui.auth.token in config",
            },
        )

    if not creds or (creds.scheme or "").lower() != "bearer" or creds.credentials != token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "unauthorized"})


app = FastAPI(title="Skylapse API")


@app.on_event("startup")
def _mount_media() -> None:
    """Mount the static media directory for serving images/videos.

    We allow missing directory at startup (check_dir=False) and depend on requests
    to create it lazily on first capture.
    """
    cfg = load_config()
    media_dir = Path(cfg.storage.local_dir)
    app.mount("/media", StaticFiles(directory=str(media_dir), check_dir=False), name="media")


@app.get("/api/latest", response_model=LatestResponse)
def get_latest(cfg: Annotated[AppConfig, Depends(get_config)]):
    base_dir = Path(cfg.storage.local_dir)
    latest = None
    for ext in ("jpg", "jpeg", "png"):
        candidates = sorted(base_dir.rglob(f"*.{ext}")) if base_dir.exists() else []
        if candidates:
            latest = candidates[-1]
            break
    if not latest:
        return LatestResponse(image_url=None, captured_at=None, exposure=None, white_balance=None)

    # In a future step, mount static files for direct serving; placeholder for path.
    rel = latest.relative_to(base_dir)
    return LatestResponse(
        image_url=f"/media/{str(rel).replace(os.sep, '/')}",
        captured_at=None,
        exposure=None,
        white_balance=None,
    )


@app.get("/api/admin/health")
def health(cfg: Annotated[AppConfig, Depends(get_config)], _auth: Annotated[None, Depends(admin_auth_dependency)]):
    # Cross-platform disk usage
    local_dir = Path(cfg.storage.local_dir)
    disk = shutil.disk_usage(local_dir if local_dir.exists() else "/")
    return JSONResponse(
        {
            "disk_total": disk.total,
            "disk_used": disk.used,
            "disk_free": disk.free,
            "local_dir": str(local_dir),
            "status": "ok",
        }
    )


# Utilities
def _parse_iso_or_date_to_unix(value: str, *, is_upper_bound: bool = False) -> float:
    """Parse ISO8601 string or YYYY-MM-DD (UTC) to unix seconds.

    If date-only and is_upper_bound=True, returns end-of-day (next day start minus 1e-6s).
    Otherwise for date-only returns start-of-day 00:00:00Z.
    """
    v = value.strip()
    try:
        if len(v) == 10 and v[4] == '-' and v[7] == '-':
            # YYYY-MM-DD as UTC
            dt = datetime.fromisoformat(v).replace(tzinfo=timezone.utc)
            if is_upper_bound:
                dt = dt + timedelta(days=1) - timedelta(microseconds=1)
            return dt.timestamp()
        # Accept a trailing 'Z'
        if v.endswith('Z'):
            v = v[:-1] + '+00:00'
        dt = datetime.fromisoformat(v)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        raise HTTPException(status_code=400, detail={"error": "invalid_datetime", "value": value})


@app.get("/api/images")
def api_list_images(
    cfg: Annotated[AppConfig, Depends(get_config)],
    from_: str | None = None,
    to: str | None = None,
    page: int = 1,
    page_size: int = 50,
):
    from_ts = _parse_iso_or_date_to_unix(from_, is_upper_bound=False) if from_ else None
    to_ts = _parse_iso_or_date_to_unix(to, is_upper_bound=True) if to else None
    result = list_media(
        Path(cfg.storage.local_dir),
        from_ts=from_ts,
        to_ts=to_ts,
        page=page,
        page_size=min(max(page_size, 1), 200),
    )
    return result


# Placeholder admin action endpoints to be implemented later per PRD
@app.post("/api/admin/capture_once")
def capture_once(cfg: Annotated[AppConfig, Depends(get_config)], _auth: Annotated[None, Depends(admin_auth_dependency)]):
    # Initialize service with capture controls from config
    service = CaptureService(
        storage_dir=Path(cfg.storage.local_dir),
        resolution_str=cfg.capture.resolution,
        exposure_mode=cfg.capture.exposure_mode,
        awb_mode=cfg.capture.awb_mode,
        iso=cfg.capture.iso,
        shutter_speed_us=cfg.capture.shutter_speed_us,
    )
    output = service.capture_once()
    return {
        "path": str(output.path),
        "url": output.url,
        "captured_at": output.captured_at,
        "exposure_us": output.exposure_us,
    }


@app.post("/api/admin/build_timelapse")
def build_timelapse(_auth: Annotated[None, Depends(admin_auth_dependency)]):
    raise HTTPException(status_code=501, detail="Not implemented: build_timelapse")
