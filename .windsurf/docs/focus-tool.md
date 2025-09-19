---
# Focus Tool Mini PRD (Sprint 1)

Owner: Skylapse
Status: Draft
---

## Goals
- Provide an intuitive, fast workflow to reach best focus on the Pi HQ camera.
- Deliver continuous visual feedback and explicit guidance (better/worse) while the user adjusts the focus ring.
- Keep exposure/white balance consistent during focusing to avoid misleading scores.

## Users & Context
- Single field operator standing by the device adjusting the manual focus ring.
- Network is local; operator uses a phone/laptop browser.

## UX Requirements
- **Focus Page**: `/focus` (also accessible from `/` with a prominent link). Auth via cookie session.
- **Live score loop**:
  - Large score readout with color indicator (Red < 100, Yellow 100–300, Green > 300; configurable).
  - Sparkline of last N scores (N=30) to visualize trend.
  - Guidance text: "Getting better" / "Getting worse" based on slope of recent scores.
  - Best-so-far badge with score + timestamp and a "Jump to best" thumbnail.
  - Optional audible cue: short beep when a new maximum is reached (toggle).
- **Controls**:
  - Start/Stop Auto (2 FPS default; 1–5 FPS range; pause if CPU > 85%).
  - Capture + Compute (single-shot).
  - Recompute (re-score last image only).
  - Lock exposure (AE off)/WB (AWB off) toggles during focus to stabilize scoring.
  - ROI selector (basic): center (default) / 3x3 grid pick (future).
- **Feedback**:
  - Direction hint: "Keep turning in the same direction" while trend is improving; "Reverse direction slightly" if trend worsens.
  - Movement hint: magnitude suggestion using normalized delta (e.g., small/medium/large) derived from variance change.
  - Recent scores list with timestamps.

## Flow
1. User opens `/focus`, logs in.
2. User enables Auto. App captures at ~2 FPS, scores each frame.
3. UI shows score, sparkline, trend arrows, and best-so-far.
4. User adjusts focus ring guided by "Better/Worse" trend.
5. When a new max is achieved, UI highlights it; user can stop Auto and lock in settings.

## Scoring Algorithm
- Current: Laplacian variance of grayscale. Fast and robust for a single frame.
- Smoothing: EMA of last K scores (K=5) for trend; show both raw and EMA on sparkline.
- Trend: slope(EMA) > +epsilon => Better; < -epsilon => Worse; else Stable.
- Normalization (optional): score_norm = score / exposure_time_ms to dampen exposure changes (only if AE not fully locked).
- ROI: First release uses full frame or central crop (50%) to reduce vignette bias. Future: user-selected ROI.

## API Changes
- **New** `POST /api/admin/focus/auto/start`
  - Body: `{ fps?: number (1..5), lock_ae?: boolean, lock_awb?: boolean, roi?: string }`
  - Starts an internal loop capturing at the requested FPS (best-effort). Returns `{ ok: true }`.
- **New** `POST /api/admin/focus/auto/stop`
  - Stops the loop. `{ ok: true }`.
- **New** `GET /api/admin/focus/frame`
  - Returns the most recent focus sample: `{ path, url, ts, width, height, score, ema, is_new_max }`.
- **Existing** `GET /api/admin/focus_score`
  - Keep for single-shot scoring (latest image).
- **Optional** `POST /api/admin/capture_and_score`
  - Single capture + score, returns same payload as `/focus/frame`.

Implementation detail: The auto loop is a lightweight cooperative task (async task or background thread) with a shared last-sample structure, guarded by a lock; never blocks request handlers.

## Configuration
- FPS default 2; max 5 to protect CPU/thermal. Configurable via env `FOCUS_FPS_MAX`.
- Trend EMA window K=5; epsilon threshold 1–3% of current baseline.
- Threshold bands configurable via env or config.
- Auto loop timeout: auto-stops after 10 minutes without user interaction.

## UI Design
- Route: `/focus` (own page under admin).
- Layout:
  - Left: Live image (latest) with timestamp overlay and optional ROI box.
  - Right: Score card (big number + color badge), trend arrows, sparkline, controls, best-so-far thumbnail and recent list.
- Controls are sticky and accessible; keyboard shortcuts (C/R/A/S for start/stop).
- Dark/light theme aware; high-contrast controls.

## Telemetry & Logging
- Log start/stop of auto focus mode with parameters (FPS, locks, ROI).
- Log each new max (score, ts, exposure/time, ROI).
- No secrets in logs.

## Risks & Mitigations
- CPU/thermal on Pi: throttle FPS dynamically based on load, cap at max FPS.
- Exposure drift: Recommend locking AE/AWB; otherwise normalize score by exposure.
- Scoring stability: Add EMA and trend thresholds; allow manual ROI to avoid bright sources dominating.

## Acceptance Criteria
- User can open `/focus`, login, enable Auto, and see score updating ~2 FPS.
- UI displays Better/Worse trend and sparkline; highlights best-so-far.
- Start/Stop works; capture-once and recompute work.
- Optionally lock AE/AWB and observe steadier scores.
- All new code covered by unit tests; CI passes; deploy succeeds on Pi.
