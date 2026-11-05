#!/usr/bin/env bash
set -euo pipefail
CURL="${CURL:-$(command -v curl || true)}"
[ -n "$CURL" ] || { echo "curl not found" >&2; exit 1; }
fail=0
check() {
  local name="$1" url="$2"
  local code
  code="$("$CURL" -sk --max-time 5 -o /tmp/nexus-health-body -w '%{http_code}' "$url" || true)"
  if [ "$code" = "200" ]; then
    echo "OK   $name $url $code"
  else
    echo "FAIL $name $url $code" >&2
    fail=1
  fi
}
check live https://127.0.0.1:8010/healthz
check console https://127.0.0.1:8010/console/
check offline http://127.0.0.1:8012/healthz
exit "$fail"
