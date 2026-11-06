#!/usr/bin/env bash
# Move Docker and/or k3s runtime data to /data. Old data is kept for rollback.
# Usage:
#   sudo bash setup-data-migration.sh --docker
#   sudo bash setup-data-migration.sh --k3s
#   sudo bash setup-data-migration.sh --dry-run
set -euo pipefail

DATA=/data
MODE="${1:---dry-run}"
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

say() { printf '\n== %s ==\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

[ -d "$DATA" ] || die "$DATA not found"
[ "$(findmnt -no FSTYPE "$DATA" 2>/dev/null)" = "ext4" ] || die "$DATA is not ext4/mounted"
if [ "${1:---dry-run}" != "--dry-run" ]; then
  [ "$(id -u)" -eq 0 ] || die "run with sudo"
  [ -x /usr/bin/rsync ] || die "rsync not installed"
fi

backup_file() {
  local f="$1"
  if [ -f "$f" ]; then
    cp -a "$f" "$f.bak.$(date +%Y%m%d-%H%M%S)"
  fi
}

docker_migrate() {
  local resume="${1:-no}"
  say "Docker: stop socket + service"
  systemctl stop docker.socket docker.service || true
  mkdir -p "$DATA/docker"
  if [ -n "$(ls -A "$DATA/docker" 2>/dev/null)" ] && [ "$resume" != "yes" ]; then
    die "$DATA/docker is not empty; use --docker-resume to continue the previous copy"
  fi

  say "Docker: copy /var/lib/docker -> $DATA/docker (old kept)"
  rsync -aHAX /var/lib/docker/ "$DATA/docker/"

  say "Docker: configure data-root"
  backup_file /etc/docker/daemon.json
  python3 - <<'PY'
import json, os
p='/etc/docker/daemon.json'
d={}
if os.path.exists(p):
    try: d=json.load(open(p))
    except Exception: d={}
d['data-root']='/data/docker'
open(p,'w').write(json.dumps(d, indent=2))
PY

  say "Docker: start"
  systemctl start docker.socket docker.service
  sleep 3
  docker info --format 'DockerRootDir={{.DockerRootDir}}' || die "Docker failed; restore /etc/docker/daemon.json.bak.* and restart"
  docker ps --format '{{.Names}} {{.Status}}' | head
}

k3s_migrate() {
  local resume="${1:-no}"
  say "k3s: stop + killall"
  systemctl stop k3s || true
  if command -v k3s-killall.sh >/dev/null 2>&1; then
    k3s-killall.sh
  elif [ -x /usr/local/bin/k3s-killall.sh ]; then
    /usr/local/bin/k3s-killall.sh
  else
    die "k3s-killall.sh not found; refusing to copy a live datastore"
  fi
  mkdir -p "$DATA/k3s"
  if [ -n "$(ls -A "$DATA/k3s" 2>/dev/null)" ] && [ "$resume" != "yes" ]; then
    die "$DATA/k3s is not empty; use --k3s-resume to continue the previous copy"
  fi

  say "k3s: copy /var/lib/rancher/k3s -> $DATA/k3s (old kept)"
  rsync -aHAX /var/lib/rancher/k3s/ "$DATA/k3s/"

  say "k3s: set data-dir"
  backup_file /etc/rancher/k3s/config.yaml
  if grep -qE '^[[:space:]]*data-dir:' /etc/rancher/k3s/config.yaml 2>/dev/null; then
    die "config.yaml already has data-dir"
  fi
  mkdir -p /etc/rancher/k3s
  printf '\ndata-dir: /data/k3s\n' >> /etc/rancher/k3s/config.yaml

  say "k3s: start"
  systemctl start k3s
  for i in $(seq 1 30); do
    if kubectl get nodes >/dev/null 2>&1; then break; fi
    sleep 2
  done
  kubectl get nodes || die "k3s failed; restore config.yaml.bak.* and restart"
  kubectl -n nexus get pods
}

case "$MODE" in
  --dry-run)
    echo "Dry run only. Available: --docker, --docker-resume, --k3s, --k3s-resume"
    findmnt -no SOURCE,TARGET,FSTYPE,OPTIONS "$DATA"
    echo "Docker root: $(docker info --format '{{.DockerRootDir}}' 2>/dev/null || echo unknown)"
    echo "Old data kept: /var/lib/docker, /var/lib/rancher/k3s"
    ;;
  --docker) docker_migrate no ;;
  --docker-resume) docker_migrate yes ;;
  --k3s) k3s_migrate no ;;
  --k3s-resume) k3s_migrate yes ;;
  *) die "usage: $0 [--dry-run|--docker|--docker-resume|--k3s|--k3s-resume]" ;;
esac
