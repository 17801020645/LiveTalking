#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAG="${1:-}"
[[ -n "$TAG" ]] || { echo "usage: $0 <tag>" >&2; exit 2; }
export PATH="$HOME/.local/bin:$PATH"
cd "$ROOT"
python3 - "$TAG" <<'PY'
import sys
tag=sys.argv[1]
import re
for p in ['deploy/k8s/app/live.yaml','deploy/k8s/app/offline.yaml']:
    s=open(p).read()
    s=re.sub(r'nexus-app:[^\s"]+', 'nexus-app:'+tag, s)
    s=re.sub(r'nexus-ui:[^\s"]+', 'nexus-ui:'+tag, s)
    open(p,'w').write(s)
PY
kubectl apply -k deploy/k8s/app
kubectl -n nexus rollout status deploy/nexus-live --timeout=180s
kubectl -n nexus rollout status deploy/nexus-offline --timeout=180s
