#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
ENV_FILE="$ROOT/.env"
[ -f "$ENV_FILE" ] || ENV_FILE="$ROOT/../../.env"
if [ -f "$ENV_FILE" ]; then set -a; . "$ENV_FILE"; set +a; fi
exec "$ROOT/.venv/bin/python" app.py \
  --transport webrtc --model musetalk --avatar_id avatar_ck \
  --tts edgetts --REF_FILE zh-CN-XiaoxiaoNeural \
  --listenport "${LIVE_PORT:-8010}" --max_session "${MAX_SESSIONS:-2}" \
  --ssl-cert certs/lan.crt --ssl-key certs/lan.key
