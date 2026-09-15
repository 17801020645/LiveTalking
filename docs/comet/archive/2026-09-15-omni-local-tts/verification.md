---
generated_from_state_version: 17
---

# 验证

## 当前结果

- 结果: **已归档**
- 验证情况: **已完成检查，验证结果已确认**
- 目标周期: 1
- 迭代: 2
- 验证器尝试次数: 2
- 完成时间: 2026-09-15T02:08:14.978Z
- 摘要: 终验 A1–A7 全部通过：独立 .venv-omni 未污染数字人 torch 2.9.1+cu128；8091 voices 返回 10 个音色；管理页默认同机 8091；文档含切 omnitts、显存 0.15 与换模路径；默认仍为 edgetts。

## 验收

| 编号 | 结果 | 来源 | 验收项 | 原因 |
| --- | --- | --- | --- | --- |
| A1 | passed | brief.md | A1：存在独立 `.venv-omni`；LiveTalking `.venv` 中 `torch` 仍为现有 cu128 版本 | 存在独立 .venv-omni（Python 3.12.14，vllm 0.28.0，torch 2.13.0+cu132）；LiveTalking .venv 无 vllm，torch 仍为 2.9.1+cu128。Runtime livetalking-torch PASSED。 |
| A2 | passed | brief.md | A2：执行 `start-omni.sh` 后本机 `8091` 监听；`GET /v1/audio/voices` 返回成功 JSON | 本机 vllm serve 监听 0.0.0.0:8091（模型 Qwen3-TTS-12Hz-0.6B-CustomVoice）；GET /v1/audio/voices 返回含 vivian 等 10 个音色的成功 JSON。Runtime omni-voices PASSED。 |
| A3 | passed | brief.md | A3：浏览器打开 `/tts/`，服务器地址 `http://127.0.0.1:8091`，连接测试成功且语音列表非空 | http://127.0.0.1:8010/tts/index.html 默认服务器地址为 http://localhost:8091；连接测试走 GET /v1/audio/voices，列表非空。 |
| A4 | passed | brief.md | A4：管理页用预设音色合成一段中文，能播放或下载音频 | 管理页 synthesize() 对 8091 POST /v1/audio/speech，成功后可播放并下载；voices 含 vivian。先前轮次已完成中文 vivian 合成得到合法 WAV。 |
| A5 | passed | brief.md | A5：文档给出将 LiveTalking 切到 `omnitts` 的准确配置项与重启步骤；未改默认 `tts: edgetts` | docs/omni_tts.md 写明 tts: omnitts、TTS_SERVER: http://127.0.0.1:8091、REF_FILE 音色名，并需重启 ./start.sh；config.yaml 默认仍为 tts: edgetts。Runtime default-tts PASSED。 |
| A6 | passed | brief.md | A6：Omni 启动配置限制两阶段显存占用（各约 0.15），文档说明与数字人同卡时的 `nvidia-smi` 观察方法 | deploy/qwen3_tts_0.6b.yaml 两阶段 gpu_memory_utilization 均为 0.15；docs/omni_tts.md 给出同卡 nvidia-smi 观察命令。Runtime deploy-util PASSED。 |
| A7 | passed | brief.md | A7：文档写明更换 0.6B-Base / 1.7B 只需改 serve 模型 ID 与显存分数，不必改数字人渲染代码 | docs/omni_tts.md 写明换 0.6B-Base / 1.7B 只需改 OMNI_MODEL 与显存分数，不必改 Wav2Lip/WebRTC。Runtime omni-docs PASSED。 |

## 检查

| 检查 | 命令 | 工作目录 | 状态 | 退出码 | 耗时 |
| --- | --- | --- | --- | ---: | ---: |
| LiveTalking torch still 2.9.1 | -c import torch; print(torch.__version__); raise SystemExit(0 if torch.__version__.startswith('2.9.1') else 1) | . | passed | 0 | 726 ms |
| Omni voices endpoint | -fsS -m 15 http://127.0.0.1:8091/v1/audio/voices | . | passed | 0 | 13 ms |
| Default tts remains edgetts | -n ^tts: edgetts config.yaml | . | passed | 0 | 6 ms |
| Deploy yaml utilization 0.15 | -n gpu_memory_utilization: 0.15 deploy/qwen3_tts_0.6b.yaml | . | passed | 0 | 8 ms |
| Docs cover switch, nvidia-smi, model swap | -E -n OMNI_MODEL\|nvidia-smi\|0.6B-Base\|1.7B docs/omni_tts.md | . | passed | 0 | 5 ms |

## 阻塞项

_无。_

## 风险与跳过的工作

_未报告风险。_

## 之前的迭代

| 目标周期 | 迭代 | 尝试 | 结果 | 未解决项 | 摘要 | 完成时间 |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 1 | 1 | execution-error | — | Native Verifier response was invalid: Native verification cannot pass before every required check succeeds | 2026-09-09T03:01:20.112Z |
| 1 | 1 | 2 | blocked | A2 | 除 A2 因 Runtime 沙箱无法探测 8091 被阻塞外，其余验收项通过。实现本身可用。 | 2026-09-09T03:02:18.783Z |
| 1 | 1 | 3 | fail | A2 | A2 产品侧已满足（独立 curl 8091 /v1/audio/voices 成功返回音色 JSON），但 Runtime 必过检查 omni-voices 仍是复用的沙箱假阴性（exit 7 / 5ms），不能判 pass。须回到 Build，由 Runtime 重建 overlay 后重跑 omni-voices。 | 2026-09-15T02:02:59.919Z |
| 1 | 2 | 1 | recovery | — | Repair verification passed for A2; final full verification is required. | 2026-09-15T02:05:14.223Z |
| 1 | 2 | 2 | pass | — | 终验 A1–A7 全部通过：独立 .venv-omni 未污染数字人 torch 2.9.1+cu128；8091 voices 返回 10 个音色；管理页默认同机 8091；文档含切 omnitts、显存 0.15 与换模路径；默认仍为 edgetts。 | 2026-09-15T02:08:14.978Z |



## 结论

终验 A1–A7 全部通过：独立 .venv-omni 未污染数字人 torch 2.9.1+cu128；8091 voices 返回 10 个音色；管理页默认同机 8091；文档含切 omnitts、显存 0.15 与换模路径；默认仍为 edgetts。
