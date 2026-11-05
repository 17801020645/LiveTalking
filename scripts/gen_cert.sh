#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p certs
IP="${1:-192.168.31.75}"
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout certs/lan.key -out certs/lan.crt -days 365 \
  -subj "/CN=$IP" \
  -addext "subjectAltName=IP:$IP,DNS:localhost"
echo "wrote certs/lan.crt certs/lan.key for $IP"
