#!/usr/bin/env bash
# Raspberry Pi initial setup for Skylapse
# - Installs Picamera2 and libcamera apps
# - Creates /data/timelapse storage directory
# - Creates /etc/skylapse/skylapse.env with safe defaults (no secrets)
# - Adds the service user to 'video' group for camera access
# - Idempotent: safe to run multiple times
#
# Usage (on the Pi):
#   curl -fsSL https://raw.githubusercontent.com/<your-repo>/deploy/scripts/pi_setup.sh | bash
# Or after cloning:
#   chmod +x deploy/scripts/pi_setup.sh && sudo deploy/scripts/pi_setup.sh
#
set -euo pipefail

# Configurable
# Prefer explicit SERVICE_USER; otherwise auto-detect the invoking non-root user
SERVICE_USER=${SERVICE_USER:-${SUDO_USER:-$(logname 2>/dev/null || id -un)}}
STORAGE_DIR=${STORAGE_DIR:-/data/timelapse}
ENV_DIR=/etc/skylapse
ENV_FILE=${ENV_DIR}/skylapse.env

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root (use sudo)." >&2
  exit 1
fi

log() { echo -e "[pi-setup] $*"; }

log "1/6 Update apt metadata"
apt-get update -y

log "2/6 Install Picamera2 and libcamera apps"
# Note: On Raspberry Pi OS Bookworm, these packages are provided by the RPi repo
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  python3-picamera2 \
  libcamera-apps \
  python3.11 python3.11-venv || true

# Handle potential libcamera resolver conflicts by retrying typical fix path
if ! dpkg -s python3-picamera2 >/dev/null 2>&1; then
  log "Attempting resolver fix for libcamera package conflicts"
  apt-get install -y libcamera0 || true
  apt-get install -y python3-picamera2 libcamera-apps || true
fi

log "3/6 Ensure storage directory at ${STORAGE_DIR}"
mkdir -p "${STORAGE_DIR}"
if id -u "${SERVICE_USER}" >/dev/null 2>&1; then
  chown -R "${SERVICE_USER}:${SERVICE_USER}" "${STORAGE_DIR}"
else
  log "User ${SERVICE_USER} not found; leaving ownership as-is for ${STORAGE_DIR}"
fi
chmod 755 "${STORAGE_DIR}"

log "4/6 Ensure service environment directory ${ENV_DIR}"
mkdir -p "${ENV_DIR}"
chmod 755 "${ENV_DIR}"

log "5/6 Create environment file if missing: ${ENV_FILE}"
if [[ ! -f "${ENV_FILE}" ]]; then
  umask 177 # ensure 600 permissions on created file
  cat >"${ENV_FILE}" <<EOF
# Skylapse service environment (keep this file secure: chmod 600)
# REQUIRED: Set a strong admin token for API admin routes
ADMIN_TOKEN=change-me

# Force Picamera2 on the Pi (optional; auto-detected if present)
SKYLAPSE_CAMERA=picamera2

# Storage directory for images/videos
SKYLAPSE_LOCAL_DIR=${STORAGE_DIR}

# Optional S3/MQTT settings (uncomment and configure)
# SKYLAPSE_S3_ENDPOINT=https://s3.example.com
# SKYLAPSE_S3_BUCKET=timelapse
# MQTT_BROKER=mqtt://...
EOF
  chown root:root "${ENV_FILE}"
  chmod 600 "${ENV_FILE}"
else
  log "Environment file already exists; leaving unchanged"
fi

log "6/6 Add ${SERVICE_USER} to video group for camera access (idempotent)"
if id -u "${SERVICE_USER}" >/dev/null 2>&1; then
  usermod -a -G video "${SERVICE_USER}" || true
else
  log "Skipping group update; user ${SERVICE_USER} does not exist"
fi

log "Setup complete. Next steps:"
cat <<'EON'
- Deploy the Skylapse app to /opt/skylapse with the deploy script from your Mac:
    ./deploy/scripts/deploy_pi.sh <pi-host-or-ip> [user]
- Or install the systemd unit manually after copying files:
    sudo cp deploy/systemd/skylapse-api.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable --now skylapse-api.service
- Verify service:
    systemctl status skylapse-api.service
    curl http://localhost:8000/health || curl http://localhost:8000/docs
EON
