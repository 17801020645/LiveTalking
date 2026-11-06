#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
ENV_FILE="$ROOT/.env"
[ -f "$ENV_FILE" ] || ENV_FILE="$ROOT/../../.env"
if [ -f "$ENV_FILE" ]; then set -a; . "$ENV_FILE"; set +a; fi
export DATA_ROOT="${DATA_ROOT:-/data/apps/digital-human/data}"
export BACKUP_DIR="${BACKUP_DIR:-/data/backups/digital-human}"
exec "$ROOT/.venv/bin/python" scripts/backup.py
