# Omni TTS 本机服务

## 能力

项目在 Ubuntu + NVIDIA GPU 上提供本地 TTS：独立 vLLM-Omni 进程监听 8091，暴露 OpenAI 兼容的 `/v1/audio/voices` 与 `/v1/audio/speech`。LiveTalking 通过 `omnitts` 插件作为客户端；管理页 `/tts/` 可直连该进程做音色管理与试听。数字人默认使用该客户端。

## 部署形态

- 使用独立虚拟环境 `.venv-omni`，不得向 LiveTalking `.venv` 安装 vLLM。
- 通过 `start-omni.sh` 启动，**默认**模型 `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice`，端口 8091，deploy 配置 `deploy/qwen3_tts_0.6b.yaml`（两阶段 `gpu_memory_utilization` 各约 0.15）。
- 声音克隆改用同一脚本、环境变量 `OMNI_MODEL=Qwen/Qwen3-TTS-12Hz-0.6B-Base`，并重启 8091。首次无本地缓存时设 `HF_HUB_OFFLINE=0` 下载。权重不入库。Base 与 0.6B CustomVoice 同级，可先保持 0.15。
- 更高音质改用同一脚本、环境变量 `OMNI_MODEL=Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice`，并重启 8091。未显式设置 `OMNI_DEPLOY_CONFIG` 时，脚本选用 `deploy/qwen3_tts_1.7b.yaml`（两阶段各约 0.25）。首次无本地缓存时设 `HF_HUB_OFFLINE=0` 下载。权重不入库。
- 一个 `vllm serve` 只挂一个检查点；CustomVoice、Base、1.7B 不能同时在同一 8091 上。
- 模型与 Hugging Face 缓存在 `HF_HOME`（优先 `data/hf` 或项目约定的 assets 目录），不入库。
- Omni 与数字人仍是两个进程。`./start.sh` 在启动 8010 之前负责拉起 Omni：若本机 `8091` 的 `/v1/audio/voices` 尚未成功，则后台调用 `./start-omni.sh`，等到该检查成功或超时后再起数字人。8091 已在听则不再拉起第二个 Omni。`SKIP_OMNI=1` 跳过拉起。换模型、单独只起 8091 仍用 `./start-omni.sh`。
- 本 `./start.sh` 拉起的 Omni 子进程随该脚本结束（Ctrl+C 停 8010）一并停止；启动前已经在跑的 Omni 不杀。
- Omni 环境缺失、启动失败或等待超时：`./start.sh` 打印明确错误，仍启动 8010。不自动改走 EdgeTTS。

## 与数字人的关系

- LiveTalking 默认 `tts: omnitts`、`TTS_SERVER: http://127.0.0.1:8091`、`REF_FILE: vivian`、`omni_tts_task_type: CustomVoice`（须为 `/v1/audio/voices` 中的音色名）。`config.py` 命令行默认与此一致。
- 8091 切到 1.7B-CustomVoice 时，数字人仍用预设音色：不必改 `REF_FILE` 与 `omni_tts_task_type`。
- 8091 已切到 Base 且要使用克隆音色时：把 `REF_FILE` 设为克隆名，并把 `omni_tts_task_type` 设为 `Base`，然后重启 8010。
- 数字人进程不内嵌 Omni。8091 不可用时，已切换为 omnitts 的会话不会自动改走 EdgeTTS；合成失败应可观察，且不得导致 LiveTalking 进程退出。
- `GET /healthz` 会短超时探测配置的 TTS 上游 `/v1/audio/voices`，结果写入布尔字段 `omni`；8091 不可达时仍返回 200（见 `ops-hardening`）。不探测 GPU。
- 不在本能力中实现自动故障回退。切回 EdgeTTS：把 `tts` 改为 `edgetts`（可清空或忽略 Omni 专用的 `TTS_SERVER` / `REF_FILE`）并重启 8010，不必停 8091。

## 操作者可见行为

- 默认 `./start.sh` 后，文本驱动（Echo / Chat 等）使用 Omni 预设音色，而不是云端 EdgeTTS。
- `/tts/` 将服务器地址指向 8091 后，连接测试成功，可刷新语音列表并合成试听。
- 局域网浏览器访问时，地址应为 GPU 主机可达的 `http://<host>:8091`，且 Omni 监听 `0.0.0.0`（若脚本默认仅本机，文档需说明）。
- 管理员 `/app/admin/tts` 仍经 8010 代理本机 8091，页面不必填写 8091。
- 8091 运行 Base 时，管理页可上传克隆音色并试听；运行 CustomVoice（含 0.6B 与 1.7B）时上传克隆会失败并显示上游原因。
- `README.md` 与 `docs/omni_tts.md` 写明 `./start.sh` 会先起 Omni 再起数字人；写明 1.7B 启动命令、首次下载，以及同卡 4090 更容易 OOM。换模型仍写 `./start-omni.sh`。

## 升级路径

- `0.6B-Base`：`OMNI_MODEL=Qwen/Qwen3-TTS-12Hz-0.6B-Base ./start-omni.sh`，显存可先保持两阶段 0.15。
- `1.7B-CustomVoice`：`OMNI_MODEL=Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice ./start-omni.sh`，使用 `deploy/qwen3_tts_1.7b.yaml`（两阶段 0.25）。同卡不够则升到 0.30 或单独 GPU。
- `1.7B-Base` 仍不在本规格内部署。

## 非范围

- macOS / Apple Silicon 上的 Omni
- 将 vLLM 并入数字人同一 venv
- EdgeTTS 自动回退
- 探测 GPU
- 部署 1.7B-Base 或同时跑两个 Omni 进程
- 把默认 8091 检查点改成 1.7B
