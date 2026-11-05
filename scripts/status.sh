#!/usr/bin/env bash
set -uo pipefail
CURL="${CURL:-$(command -v curl || echo /home/banren45/.local/bin/curl)}"

echo "=== live ==="
"$CURL" -sk --max-time 3 https://127.0.0.1:8010/api/live/status || echo "live unreachable"
echo
echo "=== offline ==="
"$CURL" -s --max-time 3 http://127.0.0.1:8012/api/offline/health || echo "offline unreachable"
echo
echo "=== gpu ==="
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader || true
