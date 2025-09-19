# Skylapse – Raspberry Pi HQ Timelapse

A robust timelapse capture system for Raspberry Pi HQ Camera with a FastAPI web app.

## Quickstart (Local Dev)

- Python 3.11+
- Create venv and install dev deps:

```
make dev
```

- Run API:

```
make run
```

- Set admin token via environment to enable admin routes:

```
export ADMIN_TOKEN=change-me
```

- Configure storage dir (defaults to `/data/timelapse`):

```
export SKYLAPSE_LOCAL_DIR=/path/to/data
```

## Configuration

- Canonical file: `configs/config.yaml` (copy from `configs/config.example.yaml`).
- Env overrides:
  - `ADMIN_TOKEN` → `ui.auth.token`
  - `SKYLAPSE_LOCAL_DIR` → `storage.local_dir`
  - `SKYLAPSE_S3_ENDPOINT`, `SKYLAPSE_S3_BUCKET`

## Testing & Tooling

- Lint: `make lint`
- Format: `make fmt`
- Type-check: `make typecheck`
- Tests: `make test`

## Notes

- This is a minimal scaffold per PRD. Capture pipeline, gallery, timelapse build,
  and focus helper will be added iteratively. Admin endpoints require a token and
  will fail closed until configured (no secrets hard-coded).

## Systemd (Sketch)

Create a unit like:

```
[Unit]
Description=Skylapse API
After=network-online.target

[Service]
User=pi
WorkingDirectory=/opt/skylapse
Environment=PYTHONUNBUFFERED=1
Environment=ADMIN_TOKEN=/etc/skylapse/admin.token
ExecStart=/opt/skylapse/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Provide secrets via EnvironmentFile or exported environment variables.
