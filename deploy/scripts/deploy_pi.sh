#!/usr/bin/env bash
# Idempotent deploy script for Skylapse to a Raspberry Pi.
# - Syncs source to /opt/skylapse
# - Creates/updates a Python 3.11 venv and installs runtime deps
# - Installs/updates systemd unit and restarts service
#
# Usage:
#   ./deploy/scripts/deploy_pi.sh <pi-hostname-or-ip> [user]
#
# Requirements on your Mac:
# - ssh + rsync available
# - Homebrew python3.11 for local dev is optional; target Pi needs python3.11 installed
#
set -euo pipefail

HOST=${1:-}
USER=${2:-pi}
# Optional SSH settings (can be provided via environment)
SSH_PORT=${SSH_PORT:-22}
SSH_IDENTITY=${SSH_IDENTITY:-}
SSH_OPTS=${SSH_OPTS:-}
if [[ -z "${HOST}" ]]; then
  echo "Usage: $0 <pi-hostname-or-ip> [user]" >&2
  exit 1
fi

PROJECT_NAME=skylapse
TARGET_DIR=/opt/${PROJECT_NAME}
SERVICE_NAME=skylapse-api.service
ENV_DIR=/etc/${PROJECT_NAME}
ENV_FILE=${ENV_DIR}/${PROJECT_NAME}.env
PY=python3.11

# Build SSH command with optional identity and port
SSH_BASE=(ssh -p "${SSH_PORT}" -o StrictHostKeyChecking=accept-new)
if [[ -n "${SSH_IDENTITY}" ]]; then
  SSH_BASE+=( -i "${SSH_IDENTITY}" )
fi
if [[ -n "${SSH_OPTS}" ]]; then
  # shellcheck disable=SC2206
  EXTRA_OPTS=( ${SSH_OPTS} )
  SSH_BASE+=( "${EXTRA_OPTS[@]}" )
fi

# Helper to run remote commands
run_ssh() {
  "${SSH_BASE[@]}" "${USER}@${HOST}" "$@"
}

echo "[1/6] Ensure target directories exist and python available"
run_ssh "sudo mkdir -p ${TARGET_DIR} ${ENV_DIR}; sudo chown -R ${USER}:${USER} ${TARGET_DIR}; command -v ${PY} >/dev/null || sudo apt-get update && sudo apt-get install -y python3.11 python3.11-venv"

echo "[2/6] Rsync project files (excluding venv, tests, git)"
# Exclude large/irrelevant items for deploy
rsync -az --delete \
  --exclude ".venv/" \
  --exclude "tests/" \
  --exclude ".git/" \
  --exclude "__pycache__/" \
  --exclude "node_modules/" \
  -e "ssh -p ${SSH_PORT} ${SSH_IDENTITY:+-i ${SSH_IDENTITY}} -o StrictHostKeyChecking=accept-new ${SSH_OPTS}" \
  ./ "${USER}@${HOST}:${TARGET_DIR}/"

echo "[3/6] Create venv (with system site packages) and install runtime dependencies"
# Step A: create/prepare venv and install deps
run_ssh "cd ${TARGET_DIR} && if [[ ! -d .venv ]]; then ${PY} -m venv .venv --system-site-packages; fi && . .venv/bin/activate && pip install -U pip && pip install -e . && pip uninstall -y numpy simplejpeg >/dev/null 2>&1 || true"

# Step B: verify picamera2 visibility; if missing, recreate venv and reinstall
if ! run_ssh "cd ${TARGET_DIR} && . .venv/bin/activate && python - <<'PY'
import importlib.util, sys
sys.exit(0 if importlib.util.find_spec('picamera2') else 1)
PY
"; then
  echo "[3b/6] picamera2 not visible; recreating venv with --system-site-packages"
  run_ssh "cd ${TARGET_DIR} && rm -rf .venv && ${PY} -m venv .venv --system-site-packages && . .venv/bin/activate && pip install -U pip && pip install -e . && pip uninstall -y numpy simplejpeg >/dev/null 2>&1 || true"
fi

# Removed noisy Step C: relying on --system-site-packages avoids ABI mismatch without pinning numpy.

echo "[4/6] Install systemd service (requires sudo)"
# Template the service User/Group to match the SSH USER
run_ssh "sudo sh -c '
  set -e
  sed -e \"s/^User=.*/User=${USER}/\" -e \"s/^Group=.*/Group=${USER}/\" \
    ${TARGET_DIR}/deploy/systemd/${SERVICE_NAME} > /etc/systemd/system/${SERVICE_NAME} && \
  chown root:root /etc/systemd/system/${SERVICE_NAME} && \
  chmod 644 /etc/systemd/system/${SERVICE_NAME} && \
  systemctl daemon-reload
'"

if ! run_ssh "test -f ${ENV_FILE}"; then
  echo "[5/6] Create environment file (placeholder)"
  # We will not copy secrets; create a placeholder if missing
  TMP_ENV=$(mktemp)
  cat >"${TMP_ENV}" <<EOF
# Environment for Skylapse service (keep secure: chmod 600)
ADMIN_TOKEN=change-me
# Optional overrides
# SKYLAPSE_LOCAL_DIR=/data/timelapse
# SKYLAPSE_CAMERA=picamera2
EOF
  scp -P "${SSH_PORT}" ${SSH_IDENTITY:+-i ${SSH_IDENTITY}} ${SSH_OPTS} "${TMP_ENV}" "${USER}@${HOST}:/tmp/${PROJECT_NAME}.env"
  run_ssh "sudo mv /tmp/${PROJECT_NAME}.env ${ENV_FILE} && sudo chown root:root ${ENV_FILE} && sudo chmod 600 ${ENV_FILE}"
  rm -f "${TMP_ENV}"
else
  echo "[5/6] Environment file exists; leaving unchanged (${ENV_FILE})"
fi

echo "[6/6] Enable and restart service"
run_ssh "sudo systemctl enable ${SERVICE_NAME} && sudo systemctl restart ${SERVICE_NAME} && sudo systemctl --no-pager status ${SERVICE_NAME} -n 0 || true"

echo "Deploy completed. Visit http://${HOST}:8000/ to verify."
