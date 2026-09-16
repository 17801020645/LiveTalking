# 目标

管理员可以把 8091 切到 `0.6B-Base` 做声音克隆：上传参考音频后，管理页能用该音色试听；数字人把 `REF_FILE` 设成克隆名并设 `omni_tts_task_type: Base` 后，文本驱动走克隆音色。默认 8091 仍是 CustomVoice + `vivian`。

# 范围

- `start-omni.sh` 默认仍 `0.6B-CustomVoice`；文档写明 `OMNI_MODEL=Qwen/Qwen3-TTS-12Hz-0.6B-Base` 与首次下载（`HF_HUB_OFFLINE=0`）
- `/app/admin/tts`：对已上传（克隆）音色合成时发 `task_type=Base`；对预设音色仍 `CustomVoice`；克隆说明不再写「本轮不部署 Base」
- 数字人 `omnitts`：`config.yaml` / `config.py` 增加 `omni_tts_task_type`（默认 `CustomVoice`），克隆连麦时改为 `Base` 并改 `REF_FILE`
- 更新 `omni-tts-serving`、`admin-tts-proxy` 与 `docs/omni_tts.md`

# 非目标

- 不把默认 8091 改成 Base，不部署 1.7B
- 不改 `web/`，不把 Omni 并进 `./start.sh`，不做 EdgeTTS 自动回退
- 不把权重提交进 Git；不要求单测连真实 8091
- 不同时跑两个 Omni 进程

# 验收示例

- A1：`start-omni.sh` 不设 `OMNI_MODEL` 时仍启动 `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice`
- A2：文档给出 Base 启动命令与首次下载方式；管理页去掉「未部署 Base」的过时说明
- A3：管理页对克隆（已上传）音色试听使用 `task_type=Base`，对预设音色使用 `CustomVoice`
- A4：配置可设 `omni_tts_task_type`（默认 `CustomVoice`）；数字人客户端把该值发给 `/v1/audio/speech`

# 约束与不变量

- 工作区：main 当前目录（`isolation: current`）
- 一个 `vllm serve` 只挂一个检查点；换 Base 须重启 8091
- 单测用假上游，不连真实 8091

# 决策

- 切片：只做 0.6B-Base 克隆路径，不做 1.7B
- 隔离：当前目录 main
- 默认检查点保持 CustomVoice
- 克隆音色试听走 Base；预设走 CustomVoice
- 数字人克隆用法：重启 Omni 为 Base，再设 `REF_FILE` + `omni_tts_task_type: Base`

# 待解决问题

无。用户已确认：默认仍 CustomVoice；`OMNI_MODEL=…-0.6B-Base` 重启后可克隆；管理页克隆试听发 Base；数字人用 `omni_tts_task_type`；不做 1.7B、不改 web/、不改默认检查点。

# 验证预期

- 单测覆盖默认模型字符串、task_type 分支、config 默认 CustomVoice
- 对照文档含 Base 启动命令
