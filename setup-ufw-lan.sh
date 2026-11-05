#!/bin/bash
# LAN-only BanrenTalking WebRTC + Omni TTS. Run: sudo bash "$0"
set -euo pipefail
ufw allow from 192.168.31.0/24 to any port 8010 proto tcp comment 'BanrenTalking-HTTP'
ufw allow from 192.168.31.0/24 to any port 8091 proto tcp comment 'BanrenTalking-Omni-TTS'
ufw allow from 192.168.31.0/24 proto udp comment 'BanrenTalking-WebRTC-LAN'
ufw status numbered
