from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from PIL import Image

from app.camera import BaseCamera, CaptureResult, get_camera


@dataclass
class CaptureOutput:
    path: Path
    url: str
    captured_at: float
    exposure_us: Optional[int]


class CaptureService:
    def __init__(self, storage_dir: Path, camera_prefer: Optional[str] = None, resolution_str: Optional[str] = None):
        self.storage_dir = storage_dir
        self.camera_prefer = camera_prefer or os.getenv("SKYLAPSE_CAMERA")
        self.resolution_str = resolution_str

    def _ensure_dir(self, dt: datetime) -> Path:
        # organize by YYYY/MM/DD
        sub = Path(dt.strftime("%Y/%m/%d"))
        out_dir = self.storage_dir / sub
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir

    def capture_once(self) -> CaptureOutput:
        cam: BaseCamera = get_camera(self.camera_prefer, self.resolution_str)
        try:
            result: CaptureResult = cam.capture()
        finally:
            cam.close()

        dt = datetime.fromtimestamp(result.captured_at, tz=timezone.utc)
        out_dir = self._ensure_dir(dt)
        filename = dt.strftime("%H%M%S") + ".jpg"
        out_path = out_dir / filename

        # Save JPEG
        img: Image.Image = result.image
        img.save(out_path, format="JPEG", quality=90)

        # URL under /media mount
        # media URL should mirror storage_dir path; we expose relative path from storage root
        rel_path = out_path.relative_to(self.storage_dir)
        url = "/media/" + str(rel_path).replace(os.sep, "/")
        return CaptureOutput(path=out_path, url=url, captured_at=result.captured_at, exposure_us=result.exposure_us)
