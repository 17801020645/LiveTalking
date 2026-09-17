#!/usr/bin/env bash
# 启动 Omni TTS（8091）与 LiveTalking（8010）。用法：
#   ./start.sh
#   SKIP_OMNI=1 ./start.sh
#   ./start.sh --avatar_id wav2lip_avatar_female_model
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PYTHON="${START_SH_PYTHON:-$ROOT/.venv/bin/python}"
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

OMNI_PORT="${OMNI_PORT:-8091}"
OMNI_VOICES_URL="${OMNI_VOICES_URL:-http://127.0.0.1:${OMNI_PORT}/v1/audio/voices}"
START_OMNI="${START_OMNI:-$ROOT/start-omni.sh}"
OMNI_WAIT_SECS="${OMNI_WAIT_SECS:-180}"
OMNI_START_LOG="${OMNI_START_LOG:-$ROOT/data/omni-start.log}"
OMNI_PID=""

omni_ready() {
  command -v curl >/dev/null 2>&1 || return 1
  curl -sf --max-time 2 "$OMNI_VOICES_URL" >/dev/null 2>&1
}

cleanup_omni() {
  if [[ -n "${OMNI_PID}" ]] && kill -0 "$OMNI_PID" 2>/dev/null; then
    kill "$OMNI_PID" 2>/dev/null || true
    wait "$OMNI_PID" 2>/dev/null || true
  fi
}
trap cleanup_omni EXIT INT TERM

ensure_omni() {
  if [[ "${SKIP_OMNI:-0}" == "1" ]]; then
    echo "SKIP_OMNI=1，跳过拉起 Omni" >&2
    return 0
  fi
  if omni_ready; then
    echo "Omni 已在 ${OMNI_PORT} 监听，跳过拉起" >&2
    return 0
  fi
  if [[ ! -x "$START_OMNI" ]]; then
    echo "未找到可执行的 ${START_OMNI}，跳过拉起 Omni；仍启动 8010" >&2
    return 0
  fi
  mkdir -p "$(dirname "$OMNI_START_LOG")"
  echo "正在拉起 Omni TTS（${OMNI_PORT}）…" >&2
  "$START_OMNI" >>"$OMNI_START_LOG" 2>&1 &
  OMNI_PID=$!
  local i
  for ((i = 0; i < OMNI_WAIT_SECS; i++)); do
    if omni_ready; then
      echo "Omni 已就绪" >&2
      return 0
    fi
    if ! kill -0 "$OMNI_PID" 2>/dev/null; then
      echo "Omni 启动失败，见 ${OMNI_START_LOG}；仍启动 8010（不会改走 EdgeTTS）" >&2
      OMNI_PID=""
      return 0
    fi
    sleep 1
  done
  echo "等待 Omni 就绪超时（${OMNI_WAIT_SECS}s），见 ${OMNI_START_LOG}；仍启动 8010（不会改走 EdgeTTS）" >&2
  return 0
}

ensure_omni

"$PYTHON" app.py \
  --transport webrtc \
  --model wav2lip \
  --avatar_id wav2lip_avatar_glass_man \
  "$@"
