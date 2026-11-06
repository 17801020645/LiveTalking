#!/usr/bin/env bash
set -euo pipefail
cd /app
export LIVE_STATUS_URL="${LIVE_STATUS_URL:-https://nexus-live:8010/api/live/status}"
exec /app/.venv/bin/python -m offline.server --host 0.0.0.0 --port 8012
