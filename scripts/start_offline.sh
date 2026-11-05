#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PIDFILE=/tmp/offline_server.pid
LOG=/tmp/offline_server.log
CURL="${CURL:-$(command -v curl || echo /home/banren45/.local/bin/curl)}"

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "offline already running pid=$(cat "$PIDFILE")"
  exit 0
fi

ENV_FILE="$ROOT/.env"
[ -f "$ENV_FILE" ] || ENV_FILE="$ROOT/../../.env"
set -a
. "$ENV_FILE"
set +a
export LIVE_STATUS_URL="${LIVE_STATUS_URL:-http://127.0.0.1:8010/api/live/status}"

nohup "$ROOT/.venv/bin/python" -m offline.server --port 8012 > "$LOG" 2>&1 &
echo $! > "$PIDFILE"

for _ in $(seq 1 20); do
  if "$CURL" -s --max-time 2 http://127.0.0.1:8012/api/offline/health >/dev/null 2>&1; then
    echo "offline started pid=$(cat "$PIDFILE") http://<ip>:8012/"
    exit 0
  fi
  sleep 1
done
echo "offline failed to start; tail $LOG" >&2
tail -20 "$LOG" >&2 || true
exit 1
