from __future__ import annotations

import os
import threading
import time
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any, cast

from PIL import Image, ImageDraw

try:  # Optional import; only available on Raspberry Pi
    from picamera2 import Picamera2  # type: ignore

    PICAMERA2_AVAILABLE = True
except Exception:  # pragma: no cover - not available in most dev envs
    Picamera2 = None
    PICAMERA2_AVAILABLE = False


class CaptureResult:
    """Represents a captured image in-memory along with metadata."""

    def __init__(
        self,
        image: Image.Image,
        captured_at: float,
        exposure_us: int | None = None,
        settings: dict[str, Any] | None = None,
        resolution: tuple[int, int] | None = None,
    ):
        self.image = image
        self.captured_at = captured_at  # unix ts
        self.exposure_us = exposure_us
        self.settings = settings or {}
        self.resolution = resolution


class BaseCamera(ABC):
    @abstractmethod
    def capture(self) -> CaptureResult: ...

    @abstractmethod
    def close(self) -> None: ...


class MockCamera(BaseCamera):
    def __init__(
        self,
        resolution: tuple[int, int] = (1280, 720),
        *,
        exposure_mode: str = "auto",
        awb_mode: str = "auto",
        iso: int | None = None,
        shutter_speed_us: int | None = None,
    ):
        self.resolution = resolution
        self._settings: dict[str, Any] = {
            "camera": "mock",
            "exposure_mode": exposure_mode,
            "awb_mode": awb_mode,
            "iso": iso,
            "shutter_speed_us": shutter_speed_us,
        }

    def capture(self) -> CaptureResult:
        w, h = self.resolution
        img = Image.new("RGB", (w, h), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
        text = f"Skylapse Mock\n{ts}"
        draw.rectangle([(20, 20), (w - 20, h - 20)], outline=(200, 200, 200), width=3)
        draw.text((40, 40), text, fill=(220, 220, 220))
        return CaptureResult(
            img,
            time.time(),
            exposure_us=cast(int | None, self._settings.get("shutter_speed_us")),
            settings=self._settings,
            resolution=self.resolution,
        )

    def close(self) -> None:  # pragma: no cover - nothing to do
        return


class Picamera2Camera(BaseCamera):  # pragma: no cover - exercised on device
    def __init__(
        self,
        resolution: tuple[int, int] = (4056, 3040),
        *,
        exposure_mode: str = "auto",
        awb_mode: str = "auto",
        iso: int | None = None,
        shutter_speed_us: int | None = None,
    ):
        if not PICAMERA2_AVAILABLE:
            raise RuntimeError("Picamera2 not available in this environment")
        self._picam = Picamera2()
        # Configure a still capture configuration; details can be tuned later
        config = self._picam.create_still_configuration(main={"size": resolution})
        self._picam.configure(config)
        # Apply basic controls
        try:
            # Exposure
            if exposure_mode == "auto":
                self._picam.set_controls({"AeEnable": True})
            else:
                controls: dict[str, Any] = {"AeEnable": False}
                if shutter_speed_us:
                    controls["ExposureTime"] = int(shutter_speed_us)
                if iso:
                    # Map ISO roughly to analogue gain; ISO 100 ~ gain 1.0, 200 ~ 2.0, etc.
                    controls["AnalogueGain"] = max(1.0, float(iso) / 100.0)
                self._picam.set_controls(controls)
            # AWB
            if awb_mode == "auto":
                self._picam.set_controls({"AwbEnable": True})
            else:
                # Leave enabled; specific gains require sensor calibration; keep simple for now
                self._picam.set_controls({"AwbEnable": True})
        except Exception:
            # Non-fatal; continue with defaults
            pass
        self._picam.start()
        self._settings = {
            "camera": "picamera2",
            "exposure_mode": exposure_mode,
            "awb_mode": awb_mode,
            "iso": iso,
            "shutter_speed_us": shutter_speed_us,
        }
        self._resolution = resolution

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
        return CaptureResult(
            img,
            time.time(),
            exposure_us=exposure_time,
            settings=self._settings,
            resolution=self._resolution,
        )

    def close(self) -> None:
        try:
            self._picam.stop()
        finally:
            self._picam.close()
            # Give the kernel a brief moment to release the device
            time.sleep(0.2)


# --- Shared Singleton Picamera2 backend ---
_PICAM_SINGLETON: Picamera2 | None = None
_PICAM_LOCK = threading.RLock()


class SharedPicamera2Camera(BaseCamera):  # pragma: no cover - exercised on device
    """Shared camera that reuses a single Picamera2 instance across captures.

    This avoids repeated open/close churn which can leave the device busy.
    """

    def __init__(
        self,
        resolution: tuple[int, int] = (4056, 3040),
        *,
        exposure_mode: str = "auto",
        awb_mode: str = "auto",
        iso: int | None = None,
        shutter_speed_us: int | None = None,
    ):
        if not PICAMERA2_AVAILABLE:
            raise RuntimeError("Picamera2 not available in this environment")
        global _PICAM_SINGLETON
        with _PICAM_LOCK:
            if _PICAM_SINGLETON is None:
                cam = Picamera2()
                config = cam.create_still_configuration(main={"size": resolution})
                cam.configure(config)
                try:
                    if exposure_mode == "auto":
                        cam.set_controls({"AeEnable": True})
                    else:
                        controls: dict[str, Any] = {"AeEnable": False}
                        if shutter_speed_us:
                            controls["ExposureTime"] = int(shutter_speed_us)
                        if iso:
                            controls["AnalogueGain"] = max(1.0, float(iso) / 100.0)
                        cam.set_controls(controls)
                    if awb_mode == "auto":
                        cam.set_controls({"AwbEnable": True})
                    else:
                        cam.set_controls({"AwbEnable": True})
                except Exception:
                    pass
                cam.start()
                _PICAM_SINGLETON = cam
        self._resolution = resolution
        self._settings = {
            "camera": "picamera2",
            "exposure_mode": exposure_mode,
            "awb_mode": awb_mode,
            "iso": iso,
            "shutter_speed_us": shutter_speed_us,
        }

    def capture(self) -> CaptureResult:
        with _PICAM_LOCK:
            assert _PICAM_SINGLETON is not None
            array = _PICAM_SINGLETON.capture_array()
        img = Image.fromarray(array)
        exposure_time = None
        try:
            with _PICAM_LOCK:
                cam = cast(Picamera2, _PICAM_SINGLETON)
                meta = cam.capture_metadata()
            exposure_time = int(meta.get("ExposureTime", 0))
        except Exception:
            pass
        return CaptureResult(
            img,
            time.time(),
            exposure_us=exposure_time,
            settings=self._settings,
            resolution=self._resolution,
        )

    def close(self) -> None:
        # No-op by design; singleton stays alive for process lifetime.
        return


def _parse_resolution(resolution_str: str | None) -> tuple[int, int] | None:
    if resolution_str and "x" in resolution_str:
        try:
            w, h = resolution_str.lower().split("x")
            return (int(w), int(h))
        except Exception:
            return None
    return None


def _init_picam_shared(
    res: tuple[int, int] | None,
    *,
    exposure_mode: str,
    awb_mode: str,
    iso: int | None,
    shutter_speed_us: int | None,
    strict: bool,
) -> BaseCamera:
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            cam = SharedPicamera2Camera(
                resolution=res or (4056, 3040),
                exposure_mode=exposure_mode,
                awb_mode=awb_mode,
                iso=iso,
                shutter_speed_us=shutter_speed_us,
            )
            print(
                {
                    "event": "camera.init",
                    "backend": "picamera2",
                    "strict": strict,
                    "attempt": attempt + 1,
                    "shared": True,
                }
            )
            return cam
        except Exception as e:
            last_err = e
            print(
                {
                    "event": "camera.init.error",
                    "backend": "picamera2",
                    "error": str(e),
                    "strict": strict,
                    "attempt": attempt + 1,
                    "shared": True,
                }
            )
            if "busy" in str(e).lower() and attempt < 2:
                time.sleep(0.3)
                continue
            break
    if strict:
        raise last_err  # type: ignore[misc]
    return MockCamera(
        resolution=res or (1280, 720),
        exposure_mode=exposure_mode,
        awb_mode=awb_mode,
        iso=iso,
        shutter_speed_us=shutter_speed_us,
    )


def get_camera(
    prefer: str | None = None,
    resolution_str: str | None = None,
    *,
    exposure_mode: str = "auto",
    awb_mode: str = "auto",
    iso: int | None = None,
    shutter_speed_us: int | None = None,
) -> BaseCamera:
    """Factory that returns a camera instance.

    prefer: "mock" | "picamera2" | None (env SKYLAPSE_CAMERA)
    resolution_str: like "4056x3040"; if None will use sane defaults.
    """
    prefer = prefer or os.getenv("SKYLAPSE_CAMERA")
    res = _parse_resolution(resolution_str)

    if prefer == "mock":
        return MockCamera(
            resolution=res or (1280, 720),
            exposure_mode=exposure_mode,
            awb_mode=awb_mode,
            iso=iso,
            shutter_speed_us=shutter_speed_us,
        )

    if prefer == "picamera2":
        return _init_picam_shared(
            res,
            exposure_mode=exposure_mode,
            awb_mode=awb_mode,
            iso=iso,
            shutter_speed_us=shutter_speed_us,
            strict=True,
        )

    if prefer is None and PICAMERA2_AVAILABLE:
        return _init_picam_shared(
            res,
            exposure_mode=exposure_mode,
            awb_mode=awb_mode,
            iso=iso,
            shutter_speed_us=shutter_speed_us,
            strict=False,
        )

    # Default fallback
    return MockCamera(
        resolution=res or (1280, 720),
        exposure_mode=exposure_mode,
        awb_mode=awb_mode,
        iso=iso,
        shutter_speed_us=shutter_speed_us,
    )
