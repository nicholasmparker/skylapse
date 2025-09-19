from __future__ import annotations

import base64
import hmac
import json
import os
import shutil
import time
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Annotated, Any

import cv2
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, Response, Security, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.camera import PICAMERA2_AVAILABLE
from app.capture import CaptureService
from app.config import AppConfig, load_config
from app.db import list_media


class LatestResponse(BaseModel):
    image_url: str | None
    captured_at: str | None
    exposure: dict[str, Any] | None
    white_balance: dict[str, Any] | None


def get_config() -> AppConfig:
    return load_config()


_bearer_scheme = HTTPBearer(auto_error=False)


def admin_auth_dependency(
    cfg: Annotated[AppConfig, Depends(get_config)],
    request: Request,
    creds: Annotated[HTTPAuthorizationCredentials | None, Security(_bearer_scheme)] = None,
) -> None:
    """Require Authorization: Bearer <token> or session cookie for admin endpoints.

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

    # First, allow a valid session cookie
    if _session_is_valid_from_request(request, token_required=bool(token)):
        return
    # Otherwise allow explicit Bearer token
    if creds and (creds.scheme or "").lower() == "bearer" and creds.credentials == token:
        return
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": "unauthorized"},
    )


app = FastAPI(
    title="Skylapse API",
    description=(
        "Admin endpoints require Authorization: Bearer <token>. "
        "Set ADMIN_TOKEN in /etc/skylapse/skylapse.env and click Authorize in this UI."
    ),
    swagger_ui_parameters={"persistAuthorization": True},
)


@app.on_event("startup")
def _mount_media() -> None:
    """Mount the static media directory for serving images/videos.

    We allow missing directory at startup (check_dir=False) and depend on requests
    to create it lazily on first capture.
    """
    cfg = load_config()
    media_dir = Path(cfg.storage.local_dir)
    app.mount("/media", StaticFiles(directory=str(media_dir), check_dir=False), name="media")
    # Mount static frontend directory if exists
    static_dir = Path(__file__).resolve().parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir), check_dir=True), name="static")


# --- Session utilities (HMAC-signed cookie) ---
SESSION_COOKIE = "skylapse_session"
SESSION_TTL_SECONDS = 12 * 60 * 60  # 12 hours


def _get_session_secret() -> str:
    secret = os.getenv("SESSION_SECRET")
    if not secret:
        # Fallback to ADMIN_TOKEN to avoid bricking login if unset.
        secret = os.getenv("ADMIN_TOKEN", "")
    return secret


def _sign(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    mac = hmac.new(_get_session_secret().encode("utf-8"), raw, sha256).digest()
    return base64.urlsafe_b64encode(raw + b"." + mac).decode("ascii")


def _unsign(token: str) -> dict[str, Any] | None:
    try:
        data = base64.urlsafe_b64decode(token.encode("ascii"))
        raw, mac = data.rsplit(b".", 1)
        exp_mac = hmac.new(_get_session_secret().encode("utf-8"), raw, sha256).digest()
        if not hmac.compare_digest(mac, exp_mac):
            return None
        obj = json.loads(raw.decode("utf-8"))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def get_session_cookie(request: Request) -> str | None:
    return request.cookies.get(SESSION_COOKIE)


def _session_is_valid_from_request(request: Request, token_required: bool) -> bool:
    raw = get_session_cookie(request)
    if not raw:
        return False
    obj = _unsign(raw)
    if not obj:
        return False
    try:
        exp = float(obj.get("exp", 0))
    except Exception:
        return False
    return exp > time.time()


def _issue_session_cookie(response: Response, subject: str) -> None:
    now = int(time.time())
    payload = {"sub": subject, "iat": now, "exp": now + SESSION_TTL_SECONDS, "v": 1}
    token = _sign(payload)
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # set True if behind HTTPS
        max_age=SESSION_TTL_SECONDS,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.set_cookie(key=SESSION_COOKIE, value="", max_age=0, expires=0, path="/")


class LoginRequest(BaseModel):
    password: str


@app.post("/api/login")
def api_login(payload: LoginRequest, response: Response) -> JSONResponse:
    password = payload.password
    ui_password = os.getenv("SKYLAPSE_UI_PASSWORD") or os.getenv("ADMIN_TOKEN")
    if not ui_password:
        raise HTTPException(status_code=503, detail={"error": "ui_password_not_configured"})
    if not password or password != ui_password:
        raise HTTPException(status_code=401, detail={"error": "invalid_credentials"})
    resp = JSONResponse({"ok": True})
    _issue_session_cookie(resp, subject="admin")
    return resp


@app.post("/api/logout")
def api_logout(response: Response) -> JSONResponse:
    resp = JSONResponse({"ok": True})
    _clear_session_cookie(resp)
    return resp


@app.get("/api/latest", response_model=LatestResponse)
def get_latest(cfg: Annotated[AppConfig, Depends(get_config)]) -> LatestResponse:
    base_dir = Path(cfg.storage.local_dir)
    # Prefer SQLite media index
    try:
        latest = list_media(base_dir, page=1, page_size=1)
        if latest and latest.get("items"):
            item = latest["items"][0]
            ts = item.get("captured_at")
            captured_iso: str | None = None
            try:
                captured_iso = datetime.fromtimestamp(float(ts), tz=UTC).isoformat()
            except Exception:
                captured_iso = None
            return LatestResponse(
                image_url=item.get("url"),
                captured_at=captured_iso,
                exposure=None,
                white_balance=None,
            )
    except Exception:
        pass

    # Fallback: scan filesystem if DB is empty/unavailable
    latest_path = None
    for ext in ("jpg", "jpeg", "png"):
        candidates = sorted(base_dir.rglob(f"*.{ext}")) if base_dir.exists() else []
        if candidates:
            latest_path = candidates[-1]
            break
    if not latest_path:
        return LatestResponse(image_url=None, captured_at=None, exposure=None, white_balance=None)

    rel = latest_path.relative_to(base_dir)
    return LatestResponse(
        image_url=f"/media/{str(rel).replace(os.sep, '/')}",
        captured_at=None,
        exposure=None,
        white_balance=None,
    )


@app.get("/")
def index() -> FileResponse:
    """Serve the simple frontend UI."""
    index_path = Path(__file__).resolve().parent / "static" / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(str(index_path))


@app.get("/focus")
def focus_page() -> FileResponse:
    """Serve the dedicated focus UI."""
    fpath = Path(__file__).resolve().parent / "static" / "focus.html"
    # Fallback to index if dedicated page missing (during migration)
    if not fpath.exists():
        return index()
    return FileResponse(str(fpath))


admin_router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(admin_auth_dependency)],
)


@admin_router.get("/health")
def health(
    cfg: Annotated[AppConfig, Depends(get_config)],
    _authz: Annotated[HTTPAuthorizationCredentials | None, Security(_bearer_scheme)] = None,
) -> JSONResponse:
    # Cross-platform disk usage
    local_dir = Path(cfg.storage.local_dir)
    disk = shutil.disk_usage(local_dir if local_dir.exists() else "/")
    # Determine intended/selected backend without initializing hardware
    prefer = os.getenv("SKYLAPSE_CAMERA")
    if prefer == "mock":
        selected_backend = "mock"
    elif prefer == "picamera2":
        selected_backend = "picamera2" if PICAMERA2_AVAILABLE else "mock"
    else:
        selected_backend = "picamera2" if PICAMERA2_AVAILABLE else "mock"

    # Most recent capture from SQLite index
    last_item: dict[str, Any] | None = None
    try:
        latest = list_media(local_dir, page=1, page_size=1)
        if latest.get("items"):
            last_item = latest["items"][0]
    except Exception:
        last_item = None

    return JSONResponse(
        {
            "disk_total": disk.total,
            "disk_used": disk.used,
            "disk_free": disk.free,
            "local_dir": str(local_dir),
            "camera": {
                "picamera2_import_ok": bool(PICAMERA2_AVAILABLE),
                "selected_backend": selected_backend,
                "prefer_env": prefer or None,
            },
            "last_capture": last_item,
            "status": "ok",
        }
    )


def _parse_iso_or_date_to_unix(value: str, *, is_upper_bound: bool = False) -> float:
    """Parse ISO8601 string or YYYY-MM-DD (UTC) to unix seconds.

    If date-only and is_upper_bound=True, returns end-of-day (next day start minus 1e-6s).
    Otherwise for date-only returns start-of-day 00:00:00Z.
    """
    v = value.strip()
    try:
        if len(v) == 10 and v[4] == "-" and v[7] == "-":
            # YYYY-MM-DD as UTC
            dt = datetime.fromisoformat(v).replace(tzinfo=UTC)
            if is_upper_bound:
                dt = dt + timedelta(days=1) - timedelta(microseconds=1)
            return dt.timestamp()
        # Accept a trailing 'Z'
        if v.endswith("Z"):
            v = v[:-1] + "+00:00"
        dt = datetime.fromisoformat(v)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.timestamp()
    except Exception as err:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_datetime", "value": value},
        ) from err


@app.get("/api/images")
def api_list_images(
    cfg: Annotated[AppConfig, Depends(get_config)],
    from_: str | None = None,
    to: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    from_ts = _parse_iso_or_date_to_unix(from_, is_upper_bound=False) if from_ else None
    to_ts = _parse_iso_or_date_to_unix(to, is_upper_bound=True) if to else None
    result: dict[str, Any] = list_media(
        Path(cfg.storage.local_dir),
        from_ts=from_ts,
        to_ts=to_ts,
        page=page,
        page_size=min(max(page_size, 1), 200),
    )
    return result


# Placeholder admin action endpoints to be implemented later per PRD
@admin_router.post("/capture_once")
def capture_once(
    cfg: Annotated[AppConfig, Depends(get_config)],
    _authz: Annotated[HTTPAuthorizationCredentials | None, Security(_bearer_scheme)] = None,
) -> dict[str, Any]:
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


@admin_router.post("/build_timelapse")
def build_timelapse(
    _authz: Annotated[HTTPAuthorizationCredentials | None, Security(_bearer_scheme)] = None,
) -> None:
    raise HTTPException(status_code=501, detail="Not implemented: build_timelapse")


@admin_router.get("/focus_score")
def focus_score(cfg: Annotated[AppConfig, Depends(get_config)]) -> dict[str, Any]:
    """Compute a focus score (Laplacian variance) on the latest image.

    Returns JSON: { path, url, width, height, score }
    """
    base_dir = Path(cfg.storage.local_dir)
    latest = list_media(base_dir, page=1, page_size=1)
    if not latest or not latest.get("items"):
        raise HTTPException(status_code=404, detail="No images available")
    item = latest["items"][0]
    img_path = Path(item["path"]).resolve()
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Latest image file not found")
    # Read via OpenCV for robust grayscale conversion
    img = cv2.imread(str(img_path))
    if img is None:
        raise HTTPException(status_code=500, detail="Failed to read image for focus computation")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    score = float(lap.var())
    return {
        "path": item["path"],
        "url": item["url"],
        "width": int(item.get("width") or img.shape[1]),
        "height": int(item.get("height") or img.shape[0]),
        "score": score,
    }


class CaptureAndScoreRequest(BaseModel):
    lock_ae: bool | None = None
    lock_awb: bool | None = None


@admin_router.post("/capture_and_score")
def capture_and_score(
    cfg: Annotated[AppConfig, Depends(get_config)],
    payload: CaptureAndScoreRequest | None = None,
) -> dict[str, Any]:
    """Capture an image and return focus score with metadata.

    Returns JSON: { path, url, ts, width, height, score }
    """
    service = CaptureService(
        storage_dir=Path(cfg.storage.local_dir),
        resolution_str=cfg.capture.resolution,
        exposure_mode=("manual" if lock_ae else cfg.capture.exposure_mode),
        awb_mode=("manual" if lock_awb else cfg.capture.awb_mode),
        iso=cfg.capture.iso,
        shutter_speed_us=cfg.capture.shutter_speed_us,
    )
    out = service.capture_once()
    img_path = Path(out.path).resolve()
    img = cv2.imread(str(img_path))
    if img is None:
        raise HTTPException(status_code=500, detail="Failed to read captured image")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    score = float(lap.var())
    return {
        "path": out.path,
        "url": out.url,
        "ts": out.captured_at,
        "width": int(img.shape[1]),
        "height": int(img.shape[0]),
        "score": score,
    }


# Include admin routes after all admin endpoints are defined
app.include_router(admin_router)
