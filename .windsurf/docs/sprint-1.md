---
# Sprint 1: Focus Tool + Auth UX

Duration: 3–5 days
Owner: Skylapse
Status: Planned
---

## Goals
- Deliver a highly-usable Focus Tool experience to assist lens focusing on-device.
- Replace raw token entry with a secure, ergonomic login (cookie-based session) aligned with our rules and PRD.
- Keep code fully compliant: tests (pytest), lint (ruff), format (black), type-checks (mypy). CI must pass before deploy.

## Scope (MVP)
- Cookie-based session auth for the admin surface (no token fields in UI).
- Focus Tool v1 UX:
  - Prominent focus score (Laplacian variance) with color indicator and thresholds.
  - Buttons: Capture + Compute, Recompute (on current/latest), and Auto-refresh toggle.
  - Small recent-scores history (last 5), timestamps.
  - Keyboard shortcuts: C = Capture + Compute; R = Recompute; A = Toggle Auto.
- Keep Recent images list; improve spacing/contrast/typography.

## Out of Scope (Sprint 2+)
- Advanced focusing heuristics (e.g., per-ROI focus, MTF50, Tenengrad).
- Multi-user accounts / RBAC.
- Full gallery and timelapse builder UI.

## Non-Functional Requirements (from rules/PRD)
- Security & Privacy: No secrets in UI; use HTTP-only, Secure, SameSite=Lax cookies.
- Idempotence: Login/logout safe to repeat.
- Tests before merge; CI passes ruff/black/mypy/pytest.
- Documentation in-repo; reproducible deploy via script. No hard-coded secrets.

## Design
### Auth
- POST `/api/login`:
  - Body: `{ "password": "..." }`.
  - Validate `password` against `SKYLAPSE_UI_PASSWORD` (fallback to `ADMIN_TOKEN` if unset).
  - On success, set `skylapse_session` cookie (HTTP-only, Secure, SameSite=Lax). TTL: 12h, rolling renewal on use.
  - Response: `{ "ok": true }`.
- POST `/api/logout`: clear cookie.
- `admin_auth_dependency` updated to accept either:
  - Valid Bearer header (for programmatic use, Swagger), OR
  - Valid session cookie `skylapse_session` (for UI).

### Focus Tool
- API: `GET /api/admin/focus_score` (existing) remains; it computes Laplacian variance on latest image.
- Optional: `POST /api/admin/capture_and_score` → capture + compute score in one call, returns same payload with `score`.
- Thresholds (configurable via env or constants):
  - Red: < 100
  - Yellow: 100–300
  - Green: > 300

### UI
- Replace token field with login modal (username not required; password-only per PRD for on-LAN admin).
- Header shows login state; buttons enabled only when logged in.
- Focus score card: big number, colored badge, buttons, auto-refresh toggle (2–3s).
- Right rail keeps recent images; improve font and spacing.

## API Changes
- New endpoints:
  - `POST /api/login` (set session cookie)
  - `POST /api/logout` (clear cookie)
  - `POST /api/admin/capture_and_score` (optional convenience)
- Admin dependency change:
  - Accept HTTP-only session cookie OR Bearer token; 401/503 behaviors unchanged.

## Configuration
- Add envs:
  - `SESSION_SECRET` (required for signing cookies)
  - `SKYLAPSE_UI_PASSWORD` (optional; if missing, fallback to `ADMIN_TOKEN`)
- Update `.env.example` and docs.

## Testing Strategy
- Unit tests:
  - Login success/failure → cookie set; subsequent admin call with cookie ok.
  - Logout clears cookie.
  - Focus score endpoint accessible with cookie; returns payload schema and numeric score.
  - Keyboard shortcuts not unit-tested; smoke via DOM presence checks optional in later web tests.
- Ensure existing tests still pass. Validate OpenAPI and admin security.

## Implementation Tasks
1) Backend Auth
- Create `POST /api/login`, `POST /api/logout` in `src/app/main.py`.
- Add cookie signer/verifier (itsdangerous or standard lib HMAC/JSON).
- Update `admin_auth_dependency` to check cookie before Bearer.
- Tests for login/cookie/unauthorized paths.

2) Focus Tool UI Overhaul
- Replace token box with login modal (simple password field + submit).
- Add focus score card UI and auto-refresh behavior.
- Add small recent-scores list under the card.
- Improve styles (spacing, contrast, typography) but keep assets minimal.

3) Optional API Shortcut
- `POST /api/admin/capture_and_score`: capture then compute and return score.
- Test happy path with mock camera.

4) Documentation
- Update `README.md` sections: auth flow, running locally, environment variables.
- Add notes in this sprint doc when deviations occur.

5) CI/Deploy
- Ensure CI green; push.
- Deploy via `deploy/scripts/deploy_pi.sh`.
- Verify on the Pi: login → focus workflow → scores update.

## Acceptance Criteria
- Able to log in from `/` and operate admin functions without entering tokens.
- Focus score visible, color-coded, and updates via Recompute and Capture + Compute.
- Auto-refresh toggles successfully and updates score/image.
- All tests pass in CI; no lint/format/type errors.
- No secrets exposed in UI or logs.

## Risks & Mitigations
- Cookie security on LAN: Require HTTP-only, SameSite=Lax; recommend HTTPS termination in front of service when exposed.
- Session fixation/expiration: time-limited signed cookies; reissue on activity.
- OpenCV performance on Pi: score computation is minimal; if needed, downscale for variance calc.

## Timeline / Checklist
- Day 1: Backend login/logout + cookie validation, unit tests.
- Day 2: UI overhaul for focus tool + login modal.
- Day 3: Optional capture_and_score + polish + docs.
- Day 4: CI, deploy, on-Pi verification.

## Rollback Plan
- If cookie-based auth causes issues, revert UI to Bearer in Swagger only (not end-user UI), keep admin endpoints operational.
