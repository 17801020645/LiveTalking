#!/bin/bash
# LAN-only LiveTalking WebRTC. Run: sudo bash "$0"
set -euo pipefail
ufw allow from 192.168.31.0/24 to any port 8010 proto tcp comment 'LiveTalking-HTTP'
ufw allow from 192.168.31.0/24 proto udp comment 'LiveTalking-WebRTC-LAN'
ufw status numbered
