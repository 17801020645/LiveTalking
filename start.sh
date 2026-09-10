#!/usr/bin/env bash
# 启动 LiveTalking。用法：
#   ./start.sh
#   ./start.sh --avatar_id wav2lip_avatar_female_model
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "未找到虚拟环境: $PYTHON" >&2
  echo "请先创建: uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python torch==2.9.1 torchvision==0.24.1 torchaudio==2.9.1 --index-url https://download.pytorch.org/whl/cu128 && uv pip install --python .venv/bin/python -r requirements.txt" >&2
  exit 1
fi

export PATH="$ROOT/.tools:$ROOT/.venv/bin:${PATH:-}"
export HF_HOME="${HF_HOME:-$ROOT/data/hf}"
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"

# worktree 不含 gitignored 的 data/avatars，复用主仓库形象目录
if [[ ! -e "$ROOT/data/avatars" ]]; then
  if [[ -d "$ROOT/../../data/avatars" ]]; then
    ln -sfn ../../../data/avatars "$ROOT/data/avatars"
  fi
fi

exec "$PYTHON" app.py \
  --transport webrtc \
  --model wav2lip \
  --avatar_id wav2lip_avatar_glass_man \
  "$@"
