#!/usr/bin/env bash
set -euo pipefail
cd /app
exec /app/.venv/bin/python app.py \
  --transport webrtc --model musetalk --avatar_id "${AVATAR_ID:-avatar_ck}" \
  --tts edgetts --REF_FILE "${REF_FILE:-zh-CN-XiaoxiaoNeural}" \
  --listenport "${LIVE_PORT:-8010}" --max_session "${MAX_SESSIONS:-2}" \
  --ssl-cert /app/certs/lan.crt --ssl-key /app/certs/lan.key
