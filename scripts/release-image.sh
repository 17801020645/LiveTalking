#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAG="${1:-}"
MODE="${2:-all}"   # all | ui
TAR="${3:-no}"     # tar | no
if [[ -z "$TAG" ]]; then
  echo "usage: $0 <tag> [all|ui] [tar|no]" >&2
  exit 2
fi
case "$MODE" in all|ui) ;; *) echo "mode must be all or ui" >&2; exit 2;; esac
export PATH="$HOME/.local/bin:$PATH"

cd "$ROOT/ui-app"
if ! npm run build >/tmp/nexus-ui-build.log 2>&1; then
  tail -20 /tmp/nexus-ui-build.log >&2
  echo "UI_BUILD_FAIL" >&2
  exit 1
fi
rsync -a "$ROOT/ui-app/dist/" "$ROOT/ui_dist/"

if ! docker build -f "$ROOT/Dockerfile.ui" -t "nexus-ui:$TAG" "$ROOT" >/tmp/nexus-ui-image.log 2>&1; then
  tail -20 /tmp/nexus-ui-image.log >&2
  echo "UI_IMAGE_BUILD_FAIL" >&2
  exit 1
fi

APP_IMAGE=""
if [[ "$MODE" == "all" ]]; then
  if ! docker build -f "$ROOT/Dockerfile.nexus" -t "nexus-app:$TAG" "$ROOT" >/tmp/nexus-app-image.log 2>&1; then
    tail -20 /tmp/nexus-app-image.log >&2
    echo "APP_IMAGE_BUILD_FAIL" >&2
    exit 1
  fi
  APP_IMAGE="nexus-app:$TAG"
fi

UI_TAR=""
APP_TAR=""
if [[ "$TAR" == "tar" ]]; then
  UI_TAR="/home/banren45/nexus-ui-$TAG.tar"
  docker save "nexus-ui:$TAG" -o "$UI_TAR"
  if [[ -n "$APP_IMAGE" ]]; then
    APP_TAR="/home/banren45/nexus-app-$TAG.tar"
    docker save "$APP_IMAGE" -o "$APP_TAR"
  fi
fi

printf '{"tag":"%s","ui_image":"nexus-ui:%s","app_image":"%s","ui_tar":"%s","app_tar":"%s"}\n' \
  "$TAG" "$TAG" "${APP_IMAGE:-}" "$UI_TAR" "$APP_TAR"
