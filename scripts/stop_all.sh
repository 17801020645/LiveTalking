#!/usr/bin/env bash
set -uo pipefail

for name in offline live; do
  if [ "$name" = offline ]; then PIDFILE=/tmp/offline_server.pid; else PIDFILE=/tmp/mt_app_8010.pid; fi
  if [ ! -f "$PIDFILE" ]; then
    echo "$name: no pid file"
    continue
  fi
  pid="$(cat "$PIDFILE")"
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    for _ in $(seq 1 20); do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.5
    done
    kill -9 "$pid" 2>/dev/null || true
    echo "$name stopped pid=$pid"
  else
    echo "$name: pid $pid not running"
  fi
  rm -f "$PIDFILE"
done
