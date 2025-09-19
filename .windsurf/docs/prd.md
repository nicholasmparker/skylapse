# Raspberry Pi HQ Camera Timelapse Project

## 1. Product Requirements Document (PRD)

### Project Overview

Create a robust, automated timelapse capture system using a Raspberry Pi
3B with the Raspberry Pi HQ Camera. The system will: - Continuously
capture high-quality images of mountain scenery. - Automatically adapt
to changing lighting conditions from bright daytime to deep twilight. -
Produce stunning sunset timelapses and publish them to external
services.

### Goals & Success Criteria

**Primary Goals** - **Image Quality**: Capture visually breathtaking
images at all times of day. - **Automation**: Minimal manual
intervention; self-adjusting for ambient conditions. - **Integration**:
Easy publishing to cloud storage (S3/Minio) and smart home platforms
(Home Assistant via MQTT).

**Success Metrics** - Smooth, flicker-free timelapses with accurate
color representation. - High dynamic range with minimal noise in low
light. - Reliable, configurable upload and publishing pipeline.

### Functional Requirements

-   **Automated Capture & Lighting Adjustment**: Dynamic exposure
    control with libcamera or Picamera2, sunrise/sunset scheduling,
    adaptive capture interval.
-   **Image Enhancement**: Optional image stacking and HDR for low light
    and high dynamic range.
-   **Timelapse Creation**: Assemble images into timelapse videos using
    ffmpeg with configurable frame rate and resolution.
-   **Storage & Publishing**: Configurable storage, automatic uploads to
    MinIO or S3 using boto3 or minio SDK, publish latest image/timelapse
    to Home Assistant via MQTT.
-   **Monitoring & Management**: Optional web dashboard using Flask or
    FastAPI for preview and controls, error logging and MQTT
    notifications.

### Non-Functional Requirements

-   Performance: Timelapse compilation should not interrupt ongoing
    capture.
-   Scalability: Ability to extend to multiple cameras or locations.
-   Maintainability: Modular Python codebase with clear documentation.

### Technical Architecture

See section 2 for detailed architecture and engineering requirements.

------------------------------------------------------------------------

## 2. Architecture and Engineering Requirements

### Recommended Libraries & Tools

  -----------------------------------------------------------------------
  Purpose              Library/Tool                Rationale
  -------------------- --------------------------- ----------------------
  Camera control       **Picamera2** (libcamera    Modern, supports HQ
                       backend)                    camera and low-level
                                                   control.

  Scheduling           systemd timers or cron      Reliable job
                                                   scheduling.

  Image stacking       OpenCV, numpy               Robust image alignment
                                                   and noise reduction.

  HDR merging          OpenCV HDR functions or     Enhanced dynamic
                       hdrmerge                    range.

  Timelapse video      ffmpeg                      High-quality video
                                                   rendering.

  Cloud storage        boto3 (S3) or minio SDK     Flexible cloud
                                                   integration.

  MQTT publishing      paho-mqtt                   Widely used MQTT
                                                   client.

  Web dashboard        Flask/FastAPI               Simple REST/UI
  (optional)                                       endpoints.
  -----------------------------------------------------------------------

### Data Flow

1.  **Capture Service** takes photos on a defined schedule.
2.  **Processing Pipeline**: Optional stacking/HDR; store raw and
    processed images locally.
3.  **Timelapse Builder** runs periodically (e.g., nightly) to create
    MP4.
4.  **Publisher** uploads images and video to MinIO/S3 and publishes
    MQTT messages to Home Assistant.

### Additional Considerations

-   Lens & Filters: Consider ND filters for bright midday shots,
    high-quality C-mount lens.
-   Power & Reliability: Use high-endurance SD card or external SSD,
    optional UPS HAT.
-   Weatherproofing: Enclose camera in weather-sealed housing.
-   Performance Tuning: Optimize capture resolution vs. file size.
-   Future Extensions: Light sensor for precise exposure adjustments,
    integrate external weather data.

------------------------------------------------------------------------

## 3. Development Workflow

### Environment Strategy

-   **Develop locally** in a repo with pinned dependencies and
    reproducible setup.
-   **Mock camera and cloud services** locally for fast unit testing.
-   **Hardware-in-the-loop (HIL)** integration tests and deployment on
    the Pi.

### Local Development

-   Python 3.11 with Picamera2/libcamera compatibility.
-   Dependency management: uv or poetry.
-   Pre-commit hooks: ruff, black, mypy, bandit.
-   Unit tests with mocks for Camera and cloud integrations.
-   Optional local services using docker-compose: minio and mosquitto
    for MQTT.
-   ffmpeg for timelapse assembly.

### Repository Structure

    timelapse/
      src/app/
        main.py
        capture.py
        pipeline.py
        timelapse.py
        publish.py
        config.py
      tests/
        test_capture.py
        test_pipeline.py
        fixtures/
      configs/
        config.example.yaml
      Makefile
      pyproject.toml
      README.md

### On-Device Workflow

-   Raspberry Pi OS (Bookworm 64-bit) with libcamera and dependencies.
-   Deploy code via Fabric/rsync or git pull on device.
-   Run as a systemd service for reliability.
-   Optional VS Code Remote SSH for debugging.

### Systemd Service Example

    [Unit]
    Description=Timelapse capture service
    After=network-online.target

    [Service]
    User=pi
    WorkingDirectory=/opt/timelapse
    Environment=PYTHONUNBUFFERED=1
    ExecStart=/opt/timelapse/.venv/bin/python -m app.main --config /opt/timelapse/configs/config.yaml
    Restart=always
    RestartSec=3
    AmbientCapabilities=CAP_SYS_NICE
    Nice=-5

    [Install]
    WantedBy=multi-user.target

### Testing Pyramid

-   Unit tests (local): 80--90% coverage with mocks/fixtures.
-   Integration tests (local): exercise MinIO, MQTT, ffmpeg.
-   Hardware-in-the-loop tests (on Pi): short capture bursts, verify
    exposure, file writes, ffmpeg build, MQTT messages.

### CI/CD

-   GitHub Actions: lint, type-check, unit tests, package build.
-   Optional integration tests in Ubuntu with MinIO/MQTT.
-   Deployment via self-hosted runner on Pi or SSH-based deployment
    action.

### Config and Secrets

-   YAML/TOML config for capture cadence, camera settings, storage, and
    publishing.
-   Secrets provided via environment variables or an EnvironmentFile for
    systemd.

### Observability

-   Structured logs with structlog or JSON, accessible via journalctl.
-   Optional MQTT health pings and error notifications.
-   Optional /health HTTP endpoint via FastAPI for remote checks.

------------------------------------------------------------------------

**Best Practice Summary** - Develop locally, deploy to the Pi; avoid
live-coding over SSH. - Abstract hardware and cloud behind interfaces so
most code runs with mocks. - Automate the Pi: systemd service plus
one-command deploy. - Maintain a robust testing pyramid with a small but
consistent hardware-in-the-loop suite.


---

# Addendum: Requirements Update — Web App, Config, Focus Helper


# Timelapse Project — Requirements Update (Web App, Config, Focus Helper)

This document **amends and supersedes** relevant sections of the PRD/Architecture to reflect three mandatory additions:
1) A **web app** is now **required** (simple but excellent UX).
2) A first-class **Config** section (UI + schema + storage + migrations).
3) An **Admin Focus Helper** to make lens focusing easy and precise.

---

## 1) Web App (Required)

### 1.1 Objectives
- Provide a fast, simple, and great-looking interface.
- **Home**: show the **latest image only** (no realtime stream on home).
- **Gallery**: browse stills by day/time; fast thumbnails; open full-res on demand.
- **Timelapses**: list generated MP4s; preview inline; download/share.
- **Admin**: config management, health, logs, Focus Helper, manual actions (capture, rebuild timelapse).

### 1.2 Architecture
- **Backend**: FastAPI (Python) running on the Pi.
  - Serves REST/JSON and static assets.
  - Endpoints protected with simple auth (HTTP Basic or token) configurable in env.
- **Frontend**: Lightweight SPA (SvelteKit or React + Vite) built to static assets.
  - Served by FastAPI (no separate Node server at runtime).
- **Storage**: 
  - Images/videos stored on disk (ext4/SSD) with **SQLite** (or Parquet) for metadata index (filename, ts, tags, exposure params).
  - Optional auto-upload to S3/MinIO still applies.
- **Thumbnails**:
  - On-ingest or on-demand generation using Pillow/OpenCV; cached on disk.
- **Performance**
  - Paginated, lazy-loaded gallery.
  - All full-res downloads are streamed.
  - Thumbnails limited to ~320–720px on longest edge for snappy UI.

### 1.3 API (selected)
- `GET /api/latest` → `{ image_url, captured_at, exposure, white_balance, histogram? }`
- `GET /api/images?from=YYYY-MM-DD&to=YYYY-MM-DD&page=N&page_size=M`
- `GET /api/timelapses` → list of `{id, title, started_at, ended_at, duration, url}`
- `POST /api/admin/capture_once` → triggers single capture (returns path/preview)
- `POST /api/admin/build_timelapse` → optional parameters (range, fps)
- `GET /api/admin/health` → system status (disk, cpu temp, recent errors)
- Focus Helper endpoints listed in §3.

### 1.4 UI Requirements
- **Home**: hero card with latest image (auto-refresh every 30–60s), capture metadata, link to gallery/timelapses.
- **Gallery**: calendar/day selector + timeline scroller; click for lightbox (EXIF, histogram overlay).
- **Timelapses**: table with duration/fps/size + inline HTML5 video preview.
- **Admin**: tabs for Config, Focus Helper, Logs, System. Minimal, responsive design, keyboard-friendly.

---

## 2) Config Section (First-Class)

### 2.1 Scope
- All runtime settings are **editable in the UI** and mapped to a **single canonical config schema**.
- Config changes are **validated** and **applied without restarting** where possible.

### 2.2 Schema & Validation
- **Pydantic** schema with clear types, enums, and ranges.
- Sample (abbrev):
```yaml
capture:
  mode: "auto|manual"
  interval_day_sec: 30
  interval_dusk_sec: 5
  resolution: "4056x3040"
  hdr:
    enabled: true
    exposures: [ -2, 0, +2 ]
  stacking:
    enabled: true
    frames: 5
    alignment: "ecc|orb"
publish:
  mqtt:
    enabled: true
    broker: "mqtt://..."
    topic_latest_image: "timelapse/latest_image"
storage:
  local_dir: "/data/timelapse"
  retention_days: 30
  s3:
    enabled: true
    endpoint: "https://s3.example.com"
    bucket: "timelapse"
ui:
  auth:
    type: "basic|token"
    username: "admin"
    token: "..."
```

### 2.3 Persistence & Migrations
- Store config as **`configs/config.yaml`**, keep a **shadow copy** in SQLite for history/versioning.
- **Migrations rules** (from the Rules doc) apply:
  - Version each schema change (`migrations/config/*.py`).
  - **Idempotent**: re-running migration must be safe.
  - **Dry-run** mode and **rollback** (auto-backup `config.yaml` before write).

### 2.4 UX
- **Config Editor**: form with grouped sections (Capture, Processing, Publish, Storage, UI).
- **Validation feedback** inline; disabled Save unless valid.
- **Test buttons** next to sensitive settings:
  - “Test MQTT” → publish a probe message.
  - “Test S3/MinIO” → put+get a temp object.
  - “Test Capture” → capture to a temp folder and show result.
- **Apply without restart** where supported; clear banner if a restart is recommended.

---

## 3) Admin Focus Helper (Critical)

### 3.1 Objectives
Focusing C/CS lenses on the HQ camera is tricky. Provide a **guided focusing mode** that removes guesswork.

### 3.2 Capabilities
- **Focus Mode** toggle (exclusive):
  - Temporarily switches capture loop to a **short cadence** (e.g., every 1–2s).
  - Optionally engages a **low-res preview stream** (MJPEG/WebRTC) **only in Admin** for initial rough focus.
  - Disables uploads/publishing to avoid noise during focusing.
- **Zoom & ROI (Region of Interest)**
  - Software zoom into a crop/ROI for pixel-level evaluation (no change to sensor crop unless requested).
  - Pan/offset controls for selecting the ROI.
- **Sharpness Metrics**
  - Compute and display **focus score** (e.g., variance of Laplacian or Tenengrad) over ROI, updated each frame.
  - Optional **edge map** overlay.
  - Show **history sparkline** to confirm improvement.
- **Exposure Lock Options**
  - During fine focus, allow **AE/AWB lock** to keep brightness/color constant.
- **One-Click Capture**
  - Button to capture and pin a high-res still while inspecting sharpness metrics.
- **Timeout & Safety**
  - Focus Mode auto-exits after N minutes or on Save; restores normal cadence.

### 3.3 API (Focus)
- `POST /api/admin/focus/start` → params: `{ cadence_sec, roi, software_zoom, ae_lock, awb_lock, preview: "mjpeg|off" }`
- `POST /api/admin/focus/stop`
- `GET /api/admin/focus/metrics` → `{ laplacian: float, tenengrad: float, roi, ts }`
- `POST /api/admin/focus/capture` → returns still + metrics
- `POST /api/admin/focus/roi` → update ROI/zoom

### 3.4 Implementation Notes
- Use **Picamera2**:
  - Configure a **secondary lower-res stream** or fast still capture for focus.
  - When preview is enabled, serve **MJPEG** chunks via FastAPI `StreamingResponse` behind admin auth (short-lived).
- Compute metrics with **OpenCV**; avoid heavy alignment steps in focus mode for responsiveness.
- Keep GPU/ISP usage balanced; cap FPS to protect CPU on Pi 3B.

---

## 4) Security & Privacy (Web + Admin)
- Admin routes require auth; disable Focus preview unless authenticated.
- No public streaming endpoints; **homepage shows last image only**.
- Hide geolocation/exact coordinates in public UI unless explicitly enabled.

---

## 5) QA & Acceptance Criteria (Additions)
- **Home page** shows newest still within last capture interval; auto-refresh only, no stream.
- **Gallery** loads first page < 1s on LAN; scrolling remains smooth.
- **Timelapses** list renders within 1s; playable preview for recent builds.
- **Config** validates and applies changes; all tests (MQTT/S3/Capture) succeed or show actionable error.
- **Focus Helper**:
  - Focus score increases as focus improves; ROI/zoom adjustable; preview (if enabled) remains ≥ 5 fps on Pi 3B.
  - Exiting Focus Mode restores prior cadence/config without leftover locks.

---

## 6) Dependencies & Packages (Delta)
- Backend: `fastapi`, `uvicorn`, `pydantic`, `sqlalchemy` (for config history if desired), `opencv-python`, `picamera2`, `Pillow`
- Frontend: `svelte` (or `react`) + `vite`
- Thumbs/Media: `ffmpeg`
- Auth: `python-multipart` (if needed), simple token/basic
- Optional: `jinja2` for server-rendered minimal pages

---

## 7) Ops Notes
- Add `systemd` unit for the web app (same service as capture or split into `timelapse-api.service` + `timelapse-capture.service`).
- Log HTTP access + app logs to journald (structured JSON).

