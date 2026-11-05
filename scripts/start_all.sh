#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$DIR/start_live.sh"
"$DIR/start_offline.sh"
"$DIR/status.sh"
