#!/usr/bin/env bash
# 启动本机 vLLM-Omni TTS（默认 8091）。与 ./start.sh（8010）分进程，互不影响。
#
# 用法：
#   ./start-omni.sh
#   OMNI_MODEL=Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice ./start-omni.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PYTHON="$ROOT/.venv-omni/bin/python"
VLLM="$ROOT/.venv-omni/bin/vllm"
if [[ ! -x "$PYTHON" || ! -x "$VLLM" ]]; then
  echo "未找到 Omni 环境: $ROOT/.venv-omni" >&2
  echo "请先执行: ./scripts/setup-omni.sh" >&2
  exit 1
fi

export PATH="$ROOT/.venv-omni/bin:${PATH:-}"
# 本机 IDE/工具链可能把系统 setuptools 注入 PYTHONPATH，会污染 .venv-omni。
unset PYTHONPATH PYTHONHOME
export HF_HOME="${HF_HOME:-$ROOT/data/hf}"
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
# 仅装驱动、无系统 nvcc 时，关闭 FlashInfer sampler 的 JIT，改走 PyTorch 采样。
export VLLM_USE_FLASHINFER_SAMPLER="${VLLM_USE_FLASHINFER_SAMPLER:-0}"
mkdir -p "$HF_HOME"

MODEL="${OMNI_MODEL:-Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice}"
HOST="${OMNI_HOST:-0.0.0.0}"
PORT="${OMNI_PORT:-8091}"
DEPLOY_CONFIG="${OMNI_DEPLOY_CONFIG:-$ROOT/deploy/qwen3_tts_0.6b.yaml}"

echo "Omni TTS: model=$MODEL host=$HOST port=$PORT"
echo "  HF_HOME=$HF_HOME"
echo "  deploy=$DEPLOY_CONFIG"
echo "健康检查: curl http://127.0.0.1:${PORT}/v1/audio/voices"

exec "$VLLM" serve "$MODEL" \
  --omni \
  --host "$HOST" \
  --port "$PORT" \
  --trust-remote-code \
  --deploy-config "$DEPLOY_CONFIG" \
  "$@"
