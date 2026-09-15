# 目标

本机数字人默认走已验收的 Omni TTS（8091），不再默认 EdgeTTS。8091 健康后，Echo / Chat / 文本驱动口型使用 `vivian` 等 Omni 预设音色。仍可手工切回 EdgeTTS。

# 范围

- `config.yaml` 默认改为 `tts: omnitts`、`TTS_SERVER: http://127.0.0.1:8091`、`REF_FILE: vivian`
- `config.py` 命令行默认与上述一致，避免不读 yaml 时仍落到 EdgeTTS
- 更新 `docs/omni_tts.md` 与正式规格：默认已是 Omni，并写明切回 `edgetts` 的步骤
- 同步 `admin-tts-proxy` 规格中「数字人默认仍为 edgetts」的过时陈述

# 非目标

- 不把 `start-omni.sh` 并进 `./start.sh`；仍是两个进程
- 不实现 EdgeTTS 自动回退
- 不让 `/healthz` 探测 8091 / GPU
- 不部署 0.6B-Base / 1.7B，不改 Wav2Lip / WebRTC
- 不改自助注册、默认入口 `/app/`、报表
- 不把麦克风 ASR 迁进管理页

# 验收示例

- A1：仓库默认配置为 `tts: omnitts`、`TTS_SERVER: http://127.0.0.1:8091`、`REF_FILE: vivian`（yaml 与 `config.py` 默认一致）
- A2：8091 已启动时，重启 8010 后文本驱动会话走 Omni 客户端，而不是 EdgeTTS
- A3：8091 未启动时，文本驱动不会悄悄改用 EdgeTTS；失败可观察（日志或无语音），且进程不必退出
- A4：文档写明默认已是 Omni，以及改回 `edgetts` 并重启 8010 的步骤；不必停 8091

# 约束与不变量

- 工作区：main 当前目录（`isolation: current`）
- Omni 仍独立 `.venv-omni` + 8091；不得向数字人 `.venv` 安装 vLLM
- 不实现自动故障回退（与已归档 `omni-tts-serving` 一致）
- 单测不连接真实 8091

# 决策

- 默认音色 `vivian`（`tts/omnitts.py` 与 `docs/omni_tts.md` 已用该名；voices 列表含此音色）
- 默认上游 `http://127.0.0.1:8091`；管理员 TTS 代理继续用同一 `TTS_SERVER`，为空时的回退不变
- 保持双进程：先 `./start-omni.sh`，再 `./start.sh`
- 不合并启动脚本，不探测 Omni 健康
- 切回 EdgeTTS 仍是改配置并重启 8010

# 待解决问题

无。用户已确认：默认 TTS 为 omnitts（vivian / 8091），8091 未启动时不回退 EdgeTTS，先起 Omni 再起数字人。

# 验证预期

- 8091 在听时：核对默认配置，重启 8010，文本驱动有 Omni 声
- 可停 8091 观察失败行为（不必破坏数字人进程）
- 文档与规格不再写「默认保持 edgetts」
