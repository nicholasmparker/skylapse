from __future__ import annotations

import os
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from PIL import Image

from app.camera import BaseCamera, CaptureResult, get_camera
from app.db import insert_media


@dataclass
class CaptureOutput:
    path: Path
    url: str
    captured_at: float
    exposure_us: Optional[int]


class CaptureService:
    def __init__(
        self,
        storage_dir: Path,
        camera_prefer: Optional[str] = None,
        resolution_str: Optional[str] = None,
        *,
        exposure_mode: str = "auto",
        awb_mode: str = "auto",
        iso: Optional[int] = None,
        shutter_speed_us: Optional[int] = None,
    ):
        self.storage_dir = storage_dir
        self.camera_prefer = camera_prefer or os.getenv("SKYLAPSE_CAMERA")
        self.resolution_str = resolution_str
        self.exposure_mode = exposure_mode
        self.awb_mode = awb_mode
        self.iso = iso
        self.shutter_speed_us = shutter_speed_us

    def _ensure_dir(self, dt: datetime) -> Path:
        # organize by YYYY/MM/DD
        sub = Path(dt.strftime("%Y/%m/%d"))
        out_dir = self.storage_dir / sub
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir

    def capture_once(self) -> CaptureOutput:
        cam: BaseCamera = get_camera(
            self.camera_prefer,
            self.resolution_str,
            exposure_mode=self.exposure_mode,
            awb_mode=self.awb_mode,
            iso=self.iso,
            shutter_speed_us=self.shutter_speed_us,
        )
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

        # Write JSON sidecar with metadata
        sidecar = {
            "path": str(out_path),
            "url": url,
            "captured_at_unix": result.captured_at,
            "captured_at_iso": dt.isoformat(),
            "exposure_us": result.exposure_us,
            "resolution": {
                "width": (result.resolution or (img.width, img.height))[0],
                "height": (result.resolution or (img.width, img.height))[1],
            },
            "settings": result.settings,
        }
        with (out_path.with_suffix(".json")).open("w", encoding="utf-8") as f:
            json.dump(sidecar, f, indent=2)

        # Record in SQLite media index
        size_bytes = out_path.stat().st_size
        width, height = img.width, img.height
        insert_media(
            self.storage_dir,
            path=out_path,
            url=url,
            captured_at=result.captured_at,
            size_bytes=size_bytes,
            width=width,
            height=height,
            exposure_us=result.exposure_us,
        )

        return CaptureOutput(path=out_path, url=url, captured_at=result.captured_at, exposure_us=result.exposure_us)
