# 目标

本机可用 `OMNI_MODEL=Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice ./start-omni.sh` 启动 8091（配套更高显存的 deploy yaml）。默认仍是 0.6B-CustomVoice。数字人仍走现有 omnitts 客户端与预设音色。不改 Wav2Lip / WebRTC。

# 范围

- `start-omni.sh` 不设 `OMNI_MODEL` 时仍起 `0.6B-CustomVoice` 与 `deploy/qwen3_tts_0.6b.yaml`
- 设为 1.7B-CustomVoice 时自动用配套 `deploy/qwen3_tts_1.7b.yaml`（两阶段显存高于 0.6B）；`OMNI_DEPLOY_CONFIG` 仍可覆盖
- `docs/omni_tts.md` 与 `README.md` 写明启动命令、首次下载（`HF_HUB_OFFLINE=0`）、同卡 OOM 风险
- 更新 `omni-tts-serving`；README 入口说明同步 1.7B 可选命令

# 非目标

- 不把 `./start-omni.sh` 默认改成 1.7B
- 不部署 1.7B-Base，不并进 `./start.sh`，不做 EdgeTTS 自动回退
- 不改 `web/`，不改口型模型，不改数字人默认 `REF_FILE` / `omni_tts_task_type`
- 不把权重提交进 Git；单测不拉真实 1.7B 权重、不连真实 8091
- 不同时跑两个 Omni 进程

# 验收示例

- A1：`start-omni.sh` 不设 `OMNI_MODEL` 时仍启动 `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice`，且默认 deploy 仍是 `qwen3_tts_0.6b.yaml`
- A2：`OMNI_MODEL=Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` 时脚本选用独立 1.7B deploy yaml；该 yaml 两阶段 `gpu_memory_utilization` 均为 0.25
- A3：`docs/omni_tts.md` 与 `README.md` 给出 1.7B 启动命令与首次下载方式，并写明同卡更容易 OOM；不再写「本规格不部署 1.7B」
- A4：原 `web/` 无改动

# 约束与不变量

- 工作区：main 当前目录（`isolation: current`）
- 一个 `vllm serve` 只挂一个检查点；换 1.7B 须重启 8091
- 权重不入库；单测只断言脚本/文档/yaml，不下载模型
- 1.7B-CustomVoice 仍是预设音色路径：数字人保持 `omni_tts_task_type: CustomVoice` 与 `REF_FILE: vivian`

# 决策

- 切片：Omni 1.7B-CustomVoice 可选启动
- 隔离：当前目录 main
- 默认检查点保持 0.6B-CustomVoice；1.7B 用 `OMNI_MODEL` 切换（与 Base 克隆同一模式）
- 1.7B 使用独立 deploy yaml，默认两阶段 0.25；不够再升或换卡
- 不恢复幽灵 change `omni-local-tts`

# 待解决问题

无。用户已确认目标、范围、验收 A1–A4 与非目标。

# 验证预期

- 单测/源码断言：默认仍 0.6B；1.7B 有独立 yaml 与文档命令
- `git diff --exit-code -- web/`
