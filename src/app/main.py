from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config import AppConfig, load_config
from app.capture import CaptureService


class LatestResponse(BaseModel):
    image_url: str | None
    captured_at: str | None
    exposure: dict | None
    white_balance: dict | None


def get_config() -> AppConfig:
    return load_config()


def admin_auth_dependency(cfg: Annotated[AppConfig, Depends(get_config)]) -> None:
    token = cfg.ui.auth.token or os.getenv("ADMIN_TOKEN")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Admin token not configured",
                "action": "Set ADMIN_TOKEN env var or ui.auth.token in config",
            },
        )


def require_admin(token_header: Annotated[str | None, Depends(lambda: os.getenv("ADMIN_TOKEN"))]):
    # Simple header-less auth placeholder; can be extended to check Authorization header.
    # For now, ensure token exists (enforced in admin_auth_dependency).
    return


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


# Placeholder admin action endpoints to be implemented later per PRD
@app.post("/api/admin/capture_once")
def capture_once(cfg: Annotated[AppConfig, Depends(get_config)], _auth: Annotated[None, Depends(admin_auth_dependency)]):
    service = CaptureService(storage_dir=Path(cfg.storage.local_dir), resolution_str=cfg.capture.resolution)
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
