#!/usr/bin/env bash
set -euo pipefail
TAG="${1:-}"
MODE="${2:-all}"
NS="${NS:-nexus}"
CURL="$(command -v curl || true)"
if [[ -z "$CURL" && -x /home/banren45/.local/bin/curl ]]; then CURL=/home/banren45/.local/bin/curl; fi
[[ -n "$CURL" ]] || { echo "SMOKE FAIL curl missing"; exit 1; }
BASE="${BASE:-https://127.0.0.1:8010}"
fail=0
note() { printf '%s\n' "$*"; }
bad() { note "SMOKE FAIL $*"; fail=1; }

images=$(kubectl -n "$NS" get deploy -o jsonpath='{range .items[*]}{.metadata.name}={.spec.template.spec.containers[0].image} {end}')
ui_image=$(kubectl -n "$NS" get deploy nexus-live -o jsonpath='{.spec.template.spec.initContainers[0].image}' 2>/dev/null || true)
pods=$(kubectl -n "$NS" get pods -o jsonpath='{range .items[*]}{.metadata.name}={.status.phase}/{.status.containerStatuses[0].ready} {end}' 2>/dev/null || true)
health=$("$CURL" -sk -o /dev/null -w '%{http_code}' "$BASE/healthz" || true)
ready=$("$CURL" -sk -o /dev/null -w '%{http_code}' "$BASE/readyz" || true)
ui=$("$CURL" -sk "$BASE/console/" 2>/dev/null | grep -o 'index-[^" ]*\.js' | head -1 || true)
status=$("$CURL" -sk "$BASE/api/live/status" 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin).get("data",{}); print(str(d.get("active","?"))+"/"+str(d.get("max","?")))' 2>/dev/null || true)

[[ "$health" == "200" ]] || bad "health=$health"
[[ "$ready" == "200" ]] || bad "ready=$ready"
[[ -n "$ui" ]] || bad "ui asset missing"
[[ -n "$status" ]] || bad "live status unavailable"
if [[ -n "$TAG" ]]; then
  if [[ "$MODE" == "all" ]]; then
    echo "$images" | grep -q "nexus-app:$TAG" || bad "app image not nexus-app:$TAG"
  fi
  if [[ -n "$ui_image" ]]; then
    echo "$ui_image" | grep -q "nexus-ui:$TAG" || bad "ui image not nexus-ui:$TAG"
  elif [[ "$MODE" == "all" ]]; then
    echo "$images" | grep -q "nexus-app:$TAG" || bad "neither ui nor app image matches"
  fi
fi
echo "$pods" | grep -q 'nexus-live-.*Running/true' || bad "live not ready"
echo "$pods" | grep -q 'nexus-offline-.*Running/true' || bad "offline not ready"
echo "SMOKE SUMMARY tag=${TAG:-any} mode=${MODE} live=${status:-?} health=$health ready=$ready ui=${ui:-missing}"
echo "IMAGES $images"
echo "UI_IMAGE ${ui_image:-none}"

if [[ "$fail" -ne 0 ]]; then exit 1; fi
echo "SMOKE PASS"
