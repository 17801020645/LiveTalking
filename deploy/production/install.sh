#!/usr/bin/env bash
set -euo pipefail
if [ "$(id -u)" -ne 0 ]; then
  echo "请用 sudo 运行：sudo $0" >&2
  exit 1
fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
echo "== 停止 legacy nohup 服务 =="
if [ -x "$ROOT/scripts/stop_all.sh" ]; then "$ROOT/scripts/stop_all.sh" || true; fi
echo "== 安装 unit =="
install -m 0644 "$ROOT/deploy/production/nexus-live.service" /etc/systemd/system/nexus-live.service
install -m 0644 "$ROOT/deploy/production/nexus-offline.service" /etc/systemd/system/nexus-offline.service
install -m 0644 "$ROOT/deploy/production/nexus-backup.service" /etc/systemd/system/nexus-backup.service
install -m 0644 "$ROOT/deploy/production/nexus-backup.timer" /etc/systemd/system/nexus-backup.timer
chmod +x "$ROOT/scripts/run_live.sh" "$ROOT/scripts/run_offline.sh" "$ROOT/scripts/backup.sh"
systemctl daemon-reload
systemctl enable --now nexus-live.service nexus-offline.service nexus-backup.timer
systemctl status --no-pager nexus-live.service nexus-offline.service nexus-backup.timer
