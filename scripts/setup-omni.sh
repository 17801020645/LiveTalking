#!/usr/bin/env bash
# 在独立 .venv-omni 中安装 vLLM + vLLM-Omni。不要写入 LiveTalking .venv。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v uv >/dev/null 2>&1; then
  echo "需要 uv。安装: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 1
fi

VENV="$ROOT/.venv-omni"
if [[ ! -x "$VENV/bin/python" ]]; then
  echo "创建独立环境: $VENV"
  uv venv --python 3.12 --seed "$VENV"
else
  echo "复用已有环境: $VENV"
fi

# 本机 IDE/工具链可能把系统 setuptools 注入 PYTHONPATH，导致构建 antlr4 失败。
unset PYTHONPATH PYTHONHOME

# 与官方 CUDA 配方对齐：先装匹配小版本的 vLLM，再装 vllm-omni。
# --torch-backend=auto 让 uv 选择当前驱动可用的 CUDA wheel，勿装进 .venv。
echo "安装 vllm（写入 $VENV）..."
uv pip install --python "$VENV/bin/python" "vllm==0.28.0" --torch-backend=auto

echo "预装 antlr4 与新 setuptools，避免 omegaconf 构建失败..."
uv pip install --python "$VENV/bin/python" 'setuptools>=75' wheel 'antlr4-python3-runtime==4.9.3'

echo "安装 vllm-omni..."
uv pip install --python "$VENV/bin/python" vllm-omni

echo "完成。LiveTalking .venv 未被修改。"
echo "启动: ./start-omni.sh"
