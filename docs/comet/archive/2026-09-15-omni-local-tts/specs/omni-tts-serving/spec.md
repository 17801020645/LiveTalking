# Omni TTS 本机服务

## 能力

项目在 Ubuntu + NVIDIA GPU 上提供可选的本地 TTS：独立 vLLM-Omni 进程监听 8091，暴露 OpenAI 兼容的 `/v1/audio/voices` 与 `/v1/audio/speech`。LiveTalking 已有 `omnitts` 插件作为客户端；管理页 `/tts/` 直连该进程做音色管理与试听。

## 部署形态

- 使用独立虚拟环境 `.venv-omni`，不得向 LiveTalking `.venv` 安装 vLLM。
- 通过 `start-omni.sh` 启动，默认模型 `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice`，端口 8091。
- 两阶段 pipeline 的 `gpu_memory_utilization` 各约为 0.15，避免默认 0.3+0.3 在空闲占满 4090 导致数字人 OOM。
- 模型与 Hugging Face 缓存在 `HF_HOME`（优先 `data/hf` 或项目约定的 assets 目录），不入库。

## 与数字人的关系

- LiveTalking 默认 `tts: edgetts`。切到 Omni 时设置 `tts: omnitts`、`TTS_SERVER: http://127.0.0.1:8091`、`REF_FILE` 为 voices 列表中的音色名，并重启 8010。
- 数字人进程不内嵌 Omni；8091 不可用时，未切换配置的会话仍走 EdgeTTS。
- 不在本能力中实现自动故障回退。

## 操作者可见行为

- `/tts/` 将服务器地址指向 8091 后，连接测试成功，可刷新语音列表并合成试听。
- 局域网浏览器访问时，地址应为 GPU 主机可达的 `http://<host>:8091`，且 Omni 监听 `0.0.0.0`（若脚本默认仅本机，文档需说明）。

## 升级路径

更换 `0.6B-Base`（克隆）或 `1.7B-CustomVoice` 时，只改 serve 的模型 ID 与显存分数，不改 Wav2Lip / WebRTC 代码。不在本规格内部署这些模型。

## 非范围

- macOS / Apple Silicon 上的 Omni
- 将 vLLM 并入数字人同一 venv
- 默认把生产 TTS 改为 omnitts
