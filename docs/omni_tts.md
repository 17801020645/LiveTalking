# 本机 Omni TTS（vLLM-Omni）

独立进程在 **8091** 提供 OpenAI 兼容语音接口。LiveTalking（8010）只当客户端。默认数字人仍用 EdgeTTS，避免 8091 未启动时首页失声。

仅支持 **Ubuntu + NVIDIA CUDA**。不要装进 `.venv`，不要在本机默认切 `tts: omnitts`。

## 一次性安装

```bash
./scripts/setup-omni.sh
```

会创建 `.venv-omni`，安装 `vllm==0.28.0` 与 `vllm-omni`。脚本会清掉 `PYTHONPATH`，避免系统旧 setuptools 污染独立环境。完成后核对数字人环境未被改写：

```bash
.venv/bin/python -c "import torch; print(torch.__version__)"
# 期望仍是现有 cu128 版本，例如 2.9.1+cu128
```

权重缓存在 `HF_HOME`（默认 `data/hf`，与 `./start.sh` 相同）。国内默认 `HF_ENDPOINT=https://hf-mirror.com`，并关闭 Xet（`HF_HUB_DISABLE_XET=1`）。镜像不支持 Xet，否则会连官方节点并出现 `SSL: UNEXPECTED_EOF_WHILE_READING`。本地已有快照时脚本会设 `HF_HUB_OFFLINE=1`。缺文件再拉：

```bash
HF_HUB_OFFLINE=0 HF_HUB_DISABLE_XET=1 ./start-omni.sh
```

## 启动

```bash
./start-omni.sh
```

默认模型 `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice`，监听 `0.0.0.0:8091`。脚本默认 `VLLM_USE_FLASHINFER_SAMPLER=0`（本机通常只有驱动、没有 `/usr/local/cuda` 的 nvcc）。若已装完整 CUDA Toolkit，可设 `VLLM_USE_FLASHINFER_SAMPLER=1`。

健康检查：

```bash
curl http://127.0.0.1:8091/v1/audio/voices
```

应返回含预设音色（如 `vivian`）的 JSON。

局域网浏览器访问管理页时：

1. 打开 `http://<GPU主机>:8010/tts/index.html`（不要用本机 `localhost`）。
2. TTS 服务器地址填 `http://<同一GPU主机>:8091`，不要填 `localhost:8091`（那是浏览器官机）。
3. 本机 UFW 需放行局域网到 **TCP 8091**。现有 [`setup-ufw-lan.sh`](../setup-ufw-lan.sh) 已包含该规则，改完后在 Ubuntu 上执行：

```bash
sudo bash setup-ufw-lan.sh
```

Omni 默认监听 `0.0.0.0:8091`。仅本机可设 `OMNI_HOST=127.0.0.1`。

## 管理页验收

1. 先 `./start.sh` 再打开 `http://127.0.0.1:8010/tts/index.html`（局域网用 GPU 主机 IP）。
2. 本机填 `http://127.0.0.1:8091`；局域网填 `http://<GPU主机>:8091`。
3. 连接测试成功，语音列表非空。
4. 选预设音色合成一段中文，应能播放或下载。

克隆上传需要 **Base** 模型，本轮不部署。见下文换模型。

## 把数字人切到 Omni（手工）

`config.yaml` 默认保持：

```yaml
tts: edgetts
```

8091 健康后再改同一文件（或启动参数），然后**重启** `./start.sh`：

```yaml
tts: omnitts
TTS_SERVER: http://127.0.0.1:8091
REF_FILE: vivian          # 必须是 /v1/audio/voices 里的音色名
```

等价命令行：

```bash
./start.sh --tts omnitts --TTS_SERVER http://127.0.0.1:8091 --REF_FILE vivian
```

首页文本驱动应走 Omni 声 + 口型。切回 EdgeTTS：把 `tts` 改回 `edgetts` 并重启，不必停 8091。

没有自动故障回退。Omni 崩溃不会拖垮 8010。

## 同卡显存（4090 24GB）

[`deploy/qwen3_tts_0.6b.yaml`](../deploy/qwen3_tts_0.6b.yaml) 把官方两阶段 `gpu_memory_utilization` 从 **0.3 改为 0.15**。

| 状态 | 大约占用 | 说明 |
|------|----------|------|
| 默认官方 0.3+0.3 | 空闲 ~13.5GB | 再加 Wav2Lip 容易挤爆 |
| 本仓库 0.15+0.15 | 空闲 ~5GB，推理峰值 ~10GB | 给数字人留余量 |
| Wav2Lip256 | 约 2–6GB | `batch_size` 越大越高 |

同时说话时另开终端：

```bash
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv -l 1
```

若 OOM：先把 yaml 里两阶段再降到 `0.12`，或降低 LiveTalking `batch_size`。改完 yaml 后重启 `./start-omni.sh`。

## 换模型（不必改渲染代码）

一个 `vllm serve` 只挂一个检查点。换模型只改启动参数，**不要**改 Wav2Lip / WebRTC。

| 目标 | `OMNI_MODEL` | 显存建议 | 说明 |
|------|----------------|----------|------|
| 预设音色（本轮默认） | `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice` | 两阶段 0.15 | 管理页列表 / 合成 |
| 声音克隆 | `Qwen/Qwen3-TTS-12Hz-0.6B-Base` | 可先保持 0.15，不够再升 | 管理页上传克隆；`task_type=Base` |
| 更高音质 | `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` | 升到 0.25–0.30 或单独 GPU | 同卡更容易 OOM |

示例：

```bash
OMNI_MODEL=Qwen/Qwen3-TTS-12Hz-0.6B-Base ./start-omni.sh
```

CustomVoice 检查点不能处理 Base 克隆请求，必须换对应模型并重启 8091。数字人侧仍是 `tts: omnitts` + `TTS_SERVER` + 音色名。
