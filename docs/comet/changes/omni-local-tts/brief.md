# 目标

在本机 Ubuntu 4090 上以独立进程提供 vLLM-Omni TTS（8091），LiveTalking 通过已有 `omnitts` 客户端接入。首发 Qwen3-TTS 0.6B CustomVoice，显存受控，不破坏现有 EdgeTTS 与数字人环境。为后续换 1.7B / 克隆模型只改 serve 配置留下路径。

# 范围

- 独立 Python 环境（`.venv-omni`），安装 vLLM + vLLM-Omni，不写入 LiveTalking `.venv`
- 权重缓存到现有 `HF_HOME` / `data/hf`（或 `assets`）
- `start-omni.sh`：在 8091 拉起 `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice`，两阶段 `gpu_memory_utilization` 各约 0.15
- 管理页 `/tts/` 能对 8091 做连接测试、列音色、合成试听
- 文档说明如何把 [`config.yaml`](../../../../config.yaml) 切到 `tts: omnitts` + `TTS_SERVER` + 音色名
- 换模型 / 克隆 / 1.7B 的升级说明（本 change 不部署这些模型）

# 非目标

- 不在 Mac Studio 上部署或适配 Omni
- 不把 vLLM 装进 LiveTalking `.venv`
- 不部署 1.7B、不部署 Base 克隆模型、不实现 EdgeTTS 自动回退代码
- 不改 Wav2Lip / WebRTC / 动作编排业务逻辑
- 不把默认 `tts` 改为 omnitts（避免 8091 未启动时首页失声）

# 验收示例

- A1：存在独立 `.venv-omni`；LiveTalking `.venv` 中 `torch` 仍为现有 cu128 版本
- A2：执行 `start-omni.sh` 后本机 `8091` 监听；`GET /v1/audio/voices` 返回成功 JSON
- A3：浏览器打开 `/tts/`，服务器地址 `http://127.0.0.1:8091`，连接测试成功且语音列表非空
- A4：管理页用预设音色合成一段中文，能播放或下载音频
- A5：文档给出将 LiveTalking 切到 `omnitts` 的准确配置项与重启步骤；未改默认 `tts: edgetts`
- A6：Omni 启动配置限制两阶段显存占用（各约 0.15），文档说明与数字人同卡时的 `nvidia-smi` 观察方法
- A7：文档写明更换 0.6B-Base / 1.7B 只需改 serve 模型 ID 与显存分数，不必改数字人渲染代码

# 约束与不变量

- 仅在本机 Ubuntu + NVIDIA CUDA 上部署 Omni
- LiveTalking 继续通过 HTTP 客户端访问 TTS，不在数字人进程内加载 vLLM
- Omni 崩溃不得导致 LiveTalking 进程退出
- 磁盘权重不得提交进 git

# 决策

- 部署机只选 Ubuntu 4090，不包含 Mac（CUDA / vLLM-Omni 路径与 macOS 不一致）
- 首发模型：`Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice`（官方 4090 配方；权重小，可与 Wav2Lip 同卡）
- Omni 独立进程、端口 8091，与 8010 分离
- 默认数字人 TTS 仍为 EdgeTTS；运营商确认 8091 健康后再手工切 `omnitts`
- 克隆（Base）与 1.7B 作为后续里程碑，本 change 只留升级说明

# 待解决问题

无。用户已确认目标、范围、非目标、验收项 A1–A7 与决策。

# 验证预期

- 本机有 GPU 与网络时：启动 Omni，curl voices，管理页连接与合成
- 无 GPU 或无法下载权重时：至少核对脚本、独立 venv 约定、配置文档与默认 `tts` 未改；对应验收项记为环境阻塞而非实现错误
