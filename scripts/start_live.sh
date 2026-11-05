#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PIDFILE=/tmp/mt_app_8010.pid
LOG=/tmp/mt_app_8010.log
CURL="${CURL:-$(command -v curl || echo /home/banren45/.local/bin/curl)}"

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "live already running pid=$(cat "$PIDFILE")"
  exit 0
fi
if [ ! -f certs/lan.crt ] || [ ! -f certs/lan.key ]; then
  echo "missing certs/lan.crt or certs/lan.key" >&2
  echo "run: ./scripts/gen_cert.sh" >&2
  exit 1
fi

ENV_FILE="$ROOT/.env"
[ -f "$ENV_FILE" ] || ENV_FILE="$ROOT/../../.env"
set -a
. "$ENV_FILE"
set +a

nohup "$ROOT/.venv/bin/python" app.py \
  --transport webrtc --model musetalk --avatar_id avatar_ck \
  --tts edgetts --REF_FILE zh-CN-XiaoxiaoNeural \
  --listenport 8010 --max_session 2 \
  --ssl-cert certs/lan.crt --ssl-key certs/lan.key \
  > "$LOG" 2>&1 &
echo $! > "$PIDFILE"

for _ in $(seq 1 40); do
  if "$CURL" -sk --max-time 2 https://127.0.0.1:8010/api/live/status >/dev/null 2>&1; then
    echo "live started pid=$(cat "$PIDFILE") https://<ip>:8010/"
    exit 0
  fi
  sleep 1
done
echo "live failed to start; tail $LOG" >&2
tail -20 "$LOG" >&2 || true
exit 1
