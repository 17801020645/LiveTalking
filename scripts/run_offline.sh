#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
ENV_FILE="$ROOT/.env"
[ -f "$ENV_FILE" ] || ENV_FILE="$ROOT/../../.env"
if [ -f "$ENV_FILE" ]; then set -a; . "$ENV_FILE"; set +a; fi
export LIVE_STATUS_URL="${LIVE_STATUS_URL:-http://127.0.0.1:8010/api/live/status}"
exec "$ROOT/.venv/bin/python" -m offline.server \
  --host "${OFFLINE_HOST:-127.0.0.1}" --port "${OFFLINE_PORT:-8012}"
