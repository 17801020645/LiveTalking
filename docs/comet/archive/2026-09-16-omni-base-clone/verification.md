---
generated_from_state_version: 7
---

# 验证

## 当前结果

- 结果: **已归档**
- 验证情况: **已完成检查，验证结果已确认**
- 目标周期: 1
- 迭代: 1
- 验证器尝试次数: 1
- 完成时间: 2026-09-16T02:32:28.239Z
- 摘要: A1–A4 均通过：默认仍 CustomVoice，文档与管理页已接通 0.6B-Base 克隆路径，数字人通过 omni_tts_task_type 发给 speech。

## 验收

| 编号 | 结果 | 来源 | 验收项 | 原因 |
| --- | --- | --- | --- | --- |
| A1 | passed | brief.md | A1：`start-omni.sh` 不设 `OMNI_MODEL` 时仍启动 `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice` | start-omni.sh MODEL 默认为 Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice；Runtime grep -F 与 test_a1 通过。 |
| A2 | passed | brief.md | A2：文档给出 Base 启动命令与首次下载方式；管理页去掉「未部署 Base」的过时说明 | docs/omni_tts.md 含 OMNI_MODEL=…-0.6B-Base 与 HF_HUB_OFFLINE=0；Tts.vue 为「克隆须 Omni 已切到 0.6B-Base」，无「未部署 Base」。 |
| A3 | passed | brief.md | A3：管理页对克隆（已上传）音色试听使用 `task_type=Base`，对预设音色使用 `CustomVoice` | Tts.vue 对 uploadedNames 发 task_type=Base，否则 CustomVoice；platform_tts 原样转发 JSON；test_a3 通过；web/ 未改。 |
| A4 | passed | brief.md | A4：配置可设 `omni_tts_task_type`（默认 `CustomVoice`）；数字人客户端把该值发给 `/v1/audio/speech` | config.yaml/config.py 默认 omni_tts_task_type=CustomVoice；OmniTTS POST /v1/audio/speech 带该 task_type；test_a4 假上游断言 Base。 |

## 检查

| 检查 | 命令 | 工作目录 | 状态 | 退出码 | 耗时 |
| --- | --- | --- | --- | ---: | ---: |
| Omni base clone and related unit tests | -m unittest tests.test_omni_base_clone tests.test_default_omnitts tests.test_gallery_admin_pages tests.test_platform_hardening | . | passed | 0 | 2187 ms |
| Original web/ unchanged | diff --exit-code -- web/ | . | passed | 0 | 62 ms |
| start-omni.sh default remains CustomVoice | -F MODEL="${OMNI_MODEL:-Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice}" start-omni.sh | . | passed | 0 | 7 ms |
| docs cover Base clone start and first download | -E OMNI_MODEL=Qwen/Qwen3-TTS-12Hz-0.6B-Base\|HF_HUB_OFFLINE=0\|omni_tts_task_type: Base docs/omni_tts.md | . | passed | 0 | 6 ms |

## 阻塞项

_无。_

## 风险与跳过的工作

- 生产 /app/ 需 npm run build 后才看到 Tts.vue 的 task_type 分支
- 本机未下载 0.6B-Base，未对真实 8091 做克隆上传/试听
- 管理页手工输入不在 uploaded_voices 中的克隆名会走 CustomVoice
- 数字人不会按音色自动切 task_type，须改配置并重启 8010

## 之前的迭代

| 目标周期 | 迭代 | 尝试 | 结果 | 未解决项 | 摘要 | 完成时间 |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 1 | 1 | pass | — | A1–A4 均通过：默认仍 CustomVoice，文档与管理页已接通 0.6B-Base 克隆路径，数字人通过 omni_tts_task_type 发给 speech。 | 2026-09-16T02:32:28.239Z |



## 结论

A1–A4 均通过：默认仍 CustomVoice，文档与管理页已接通 0.6B-Base 克隆路径，数字人通过 omni_tts_task_type 发给 speech。
