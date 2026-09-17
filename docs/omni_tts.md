# 本机 Omni TTS（vLLM-Omni）

独立进程在 **8091** 提供 OpenAI 兼容语音接口。LiveTalking（8010）只当客户端。数字人**默认** `tts: omnitts`，文本驱动走 Omni 预设音色 `vivian`。

仅支持 **Ubuntu + NVIDIA CUDA**。不要把 vLLM 装进 `.venv`。`./start.sh` 会先拉起 Omni 再起数字人：

```bash
./start.sh
```

8091 已在听时不会再拉起第二个 Omni。只起数字人：`SKIP_OMNI=1 ./start.sh`。换模型或单独起 8091 仍用 `./start-omni.sh`。也可分两步：

```bash
./start-omni.sh
SKIP_OMNI=1 ./start.sh
```

8091 未就绪时首页会失声，**不会**自动改回 EdgeTTS。Omni 崩溃不会拖垮 8010。

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

推荐一次拉起两进程：

```bash
./start.sh
```

只起 Omni / 换模型：

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

1. 打开 `http://<GPU主机>:8010/app/admin/tts`（管理员登录后，8010 代理本机 8091，浏览器不必直连 8091）。
2. 若仍使用原页 `http://<GPU主机>:8010/tts/index.html`：TTS 服务器地址填 `http://<同一GPU主机>:8091`，不要填 `localhost:8091`（那是浏览器官机），且本机 UFW 需放行局域网到 **TCP 8091**。现有 [`setup-ufw-lan.sh`](../setup-ufw-lan.sh) 已包含该规则，改完后在 Ubuntu 上执行：

```bash
sudo bash setup-ufw-lan.sh
```

Omni 默认监听 `0.0.0.0:8091`。仅本机可设 `OMNI_HOST=127.0.0.1`。

## 管理页验收

1. 先 `./start.sh` 再打开 `http://127.0.0.1:8010/tts/index.html`（局域网用 GPU 主机 IP）。
2. 本机填 `http://127.0.0.1:8091`；局域网填 `http://<GPU主机>:8091`。
3. 连接测试成功，语音列表非空。
4. 选预设音色合成一段中文，应能播放或下载。

声音克隆：先把 8091 换成 Base（见下文），再在 `/app/admin/tts` 上传参考音频。默认 CustomVoice 上上传会失败。

## 默认配置（Omni）

`config.yaml` 与 `config.py` 默认：

```yaml
tts: omnitts
TTS_SERVER: http://127.0.0.1:8091
REF_FILE: vivian          # 必须是 /v1/audio/voices 里的音色名
omni_tts_task_type: CustomVoice
```

`./start.sh` 会读该文件，并尝试先拉起 8091。若仍未就绪，文本驱动没有声音，不会自动改回 EdgeTTS。

8091 已切到 Base、要用克隆音色时：

```yaml
REF_FILE: <克隆音色名>
omni_tts_task_type: Base
```

然后重启 `./start.sh`。

## 切回 EdgeTTS

改同一文件（或启动参数），然后**重启** `./start.sh`，不必停 8091：

```yaml
tts: edgetts
```

等价命令行：

```bash
./start.sh --tts edgetts
```

没有自动故障回退。

## 同卡显存（4090 24GB）

[`deploy/qwen3_tts_0.6b.yaml`](../deploy/qwen3_tts_0.6b.yaml) 把官方两阶段 `gpu_memory_utilization` 从 **0.3 改为 0.15**。1.7B 用 [`deploy/qwen3_tts_1.7b.yaml`](../deploy/qwen3_tts_1.7b.yaml)（两阶段 **0.25**），同卡更容易 OOM。

| 状态 | 大约占用 | 说明 |
|------|----------|------|
| 默认官方 0.3+0.3 | 空闲 ~13.5GB | 再加 Wav2Lip 容易挤爆 |
| 本仓库 0.6B 0.15+0.15 | 空闲 ~5GB，推理峰值 ~10GB | 给数字人留余量 |
| 本仓库 1.7B 0.25+0.25 | 高于 0.6B | 同卡更容易 OOM |
| Wav2Lip256 | 约 2–6GB | `batch_size` 越大越高 |

同时说话时另开终端：

```bash
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv -l 1
```

若 OOM：0.6B 可把 yaml 两阶段再降到 `0.12`，或降低 LiveTalking `batch_size`；1.7B 可升到 0.30 或换独立 GPU。改完 yaml 后重启 `./start-omni.sh`。

## 换模型（不必改渲染代码）

一个 `vllm serve` 只挂一个检查点。换模型只改启动参数，**不要**改 Wav2Lip / WebRTC。`start-omni.sh` 看到模型名含 `1.7B` 时自动用 1.7B yaml；`OMNI_DEPLOY_CONFIG` 可覆盖。

| 目标 | `OMNI_MODEL` | 显存建议 | 说明 |
|------|----------------|----------|------|
| 预设音色（本轮默认） | `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice` | 两阶段 0.15 | 管理页列表 / 合成 |
| 声音克隆 | `Qwen/Qwen3-TTS-12Hz-0.6B-Base` | 可先保持 0.15，不够再升 | 管理页上传克隆；`task_type=Base` |
| 更高音质 | `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` | 两阶段 0.25；不够再升到 0.30 或单独 GPU | 同卡更容易 OOM |

声音克隆（首次无本地缓存时加上下载开关）：

```bash
HF_HUB_OFFLINE=0 HF_HUB_DISABLE_XET=1 OMNI_MODEL=Qwen/Qwen3-TTS-12Hz-0.6B-Base ./start-omni.sh
```

已缓存后：

```bash
OMNI_MODEL=Qwen/Qwen3-TTS-12Hz-0.6B-Base ./start-omni.sh
```

更高音质 1.7B-CustomVoice（首次无本地缓存时打开下载；数字人仍用 `vivian` + `omni_tts_task_type: CustomVoice`）：

```bash
HF_HUB_OFFLINE=0 HF_HUB_DISABLE_XET=1 OMNI_MODEL=Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice ./start-omni.sh
```

已缓存后：

```bash
OMNI_MODEL=Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice ./start-omni.sh
```

CustomVoice 检查点不能处理 Base 克隆请求，必须换对应模型并重启 8091。数字人侧：`tts: omnitts` + `TTS_SERVER` + 克隆音色名 + `omni_tts_task_type: Base`。切回预设音色则重新用默认 `./start-omni.sh`（CustomVoice），`omni_tts_task_type: CustomVoice`，`REF_FILE: vivian`。
