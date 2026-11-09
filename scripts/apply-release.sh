#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAG="${1:-}"
MODE="${2:-all}"
[[ -n "$TAG" ]] || { echo "usage: $0 <tag> [all|ui]" >&2; exit 2; }
case "$MODE" in all|ui) ;; *) echo "mode must be all or ui" >&2; exit 2;; esac
export PATH="$HOME/.local/bin:$PATH"
cd "$ROOT"
python3 - "$TAG" "$MODE" <<'PY'
import sys, re
tag, mode = sys.argv[1], sys.argv[2]
for p in ['deploy/k8s/app/live.yaml','deploy/k8s/app/offline.yaml']:
    s=open(p).read()
    if mode == 'all':
        s=re.sub(r'nexus-app:[^\s"]+', 'nexus-app:'+tag, s)
    s=re.sub(r'nexus-ui:[^\s"]+', 'nexus-ui:'+tag, s)
    open(p,'w').write(s)
PY
kubectl apply -k deploy/k8s/app
kubectl -n nexus rollout status deploy/nexus-live --timeout=180s
kubectl -n nexus rollout status deploy/nexus-offline --timeout=180s
