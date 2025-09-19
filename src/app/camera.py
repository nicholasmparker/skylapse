from __future__ import annotations

import io
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

try:  # Optional import; only available on Raspberry Pi
    from picamera2 import Picamera2  # type: ignore
    PICAMERA2_AVAILABLE = True
except Exception:  # pragma: no cover - not available in most dev envs
    Picamera2 = None  # type: ignore
    PICAMERA2_AVAILABLE = False


class CaptureResult:
    """Represents a captured image in-memory along with metadata."""

    def __init__(self, image: Image.Image, captured_at: float, exposure_us: Optional[int] = None):
        self.image = image
        self.captured_at = captured_at  # unix ts
        self.exposure_us = exposure_us


class BaseCamera(ABC):
    @abstractmethod
    def capture(self) -> CaptureResult:
        ...

    @abstractmethod
    def close(self) -> None:
        ...


class MockCamera(BaseCamera):
    def __init__(self, resolution: tuple[int, int] = (1280, 720)):
        self.resolution = resolution

    def capture(self) -> CaptureResult:
        w, h = self.resolution
        img = Image.new("RGB", (w, h), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        text = f"Skylapse Mock\n{ts}"
        draw.rectangle([(20, 20), (w - 20, h - 20)], outline=(200, 200, 200), width=3)
        draw.text((40, 40), text, fill=(220, 220, 220))
        return CaptureResult(img, time.time(), exposure_us=None)

    def close(self) -> None:  # pragma: no cover - nothing to do
        return


class Picamera2Camera(BaseCamera):  # pragma: no cover - exercised on device
    def __init__(self, resolution: tuple[int, int] = (4056, 3040)):
        if not PICAMERA2_AVAILABLE:
            raise RuntimeError("Picamera2 not available in this environment")
        self._picam = Picamera2()
        # Configure a still capture configuration; details can be tuned later
        config = self._picam.create_still_configuration(main={"size": resolution})
        self._picam.configure(config)
        self._picam.start()

    def capture(self) -> CaptureResult:
        # Capture image as PIL Image for consistent downstream handling
        array = self._picam.capture_array()
        img = Image.fromarray(array)
        # Exposure info if available
        exposure_time = None
        try:
            exposure_time = int(self._picam.capture_metadata().get("ExposureTime", 0))
        except Exception:
            pass
        return CaptureResult(img, time.time(), exposure_us=exposure_time)

    def close(self) -> None:
        try:
            self._picam.stop()
        finally:
            self._picam.close()


def get_camera(prefer: Optional[str] = None, resolution_str: Optional[str] = None) -> BaseCamera:
    """Factory that returns a camera instance.

    prefer: "mock" | "picamera2" | None (env SKYLAPSE_CAMERA)
    resolution_str: like "4056x3040"; if None will use sane defaults.
    """
    prefer = prefer or os.getenv("SKYLAPSE_CAMERA")
    res: Optional[tuple[int, int]] = None
    if resolution_str and "x" in resolution_str:
        try:
            w, h = resolution_str.lower().split("x")
            res = (int(w), int(h))
        except Exception:
            res = None

    if prefer == "mock":
        return MockCamera(resolution=res or (1280, 720))

    if prefer == "picamera2" or (prefer is None and PICAMERA2_AVAILABLE):
        try:
            return Picamera2Camera(resolution=res or (4056, 3040))
        except Exception:
            # Fallback to mock if hardware init fails
            return MockCamera(resolution=res or (1280, 720))

    # Default fallback
    return MockCamera(resolution=res or (1280, 720))
