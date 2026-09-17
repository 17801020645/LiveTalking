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
- 完成时间: 2026-09-17T02:01:34.019Z
- 摘要: A1–A4 全部通过：默认仍 0.6B+0.6b yaml；1.7B 走独立 1.7b yaml 且两阶段 0.25；文档含启动/下载/同卡 OOM 且已去掉「本规格不部署 1.7B」；web/ 无改动。未实启 8091 不阻塞本切片验收。

## 验收

| 编号 | 结果 | 来源 | 验收项 | 原因 |
| --- | --- | --- | --- | --- |
| A1 | passed | brief.md | A1：`start-omni.sh` 不设 `OMNI_MODEL` 时仍启动 `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice`，且默认 deploy 仍是 `qwen3_tts_0.6b.yaml` | start-omni.sh 默认 MODEL 为 Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice；未设 OMNI_DEPLOY_CONFIG 且模型名不含 1.7B 时 DEPLOY_CONFIG 为 deploy/qwen3_tts_0.6b.yaml；该 yaml 两阶段均为 0.15。unittest 与默认模型行 grep 均通过。 |
| A2 | passed | brief.md | A2：`OMNI_MODEL=Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` 时脚本选用独立 1.7B deploy yaml；该 yaml 两阶段 `gpu_memory_utilization` 均为 0.25 | OMNI_MODEL 含 1.7B 且未覆盖 OMNI_DEPLOY_CONFIG 时选用独立 deploy/qwen3_tts_1.7b.yaml；该文件 stage 0/1 的 gpu_memory_utilization 均为 0.25。unittest 与 yaml grep 均通过。未实启 8091 不构成阻塞。 |
| A3 | passed | brief.md | A3：`docs/omni_tts.md` 与 `README.md` 给出 1.7B 启动命令与首次下载方式，并写明同卡更容易 OOM；不再写「本规格不部署 1.7B」 | docs/omni_tts.md 与 README.md 均给出 OMNI_MODEL=Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice 启动命令、HF_HUB_OFFLINE=0 首次下载，并写明同卡更容易 OOM；两文件均无「本规格不部署 1.7B」。Runtime grep 通过。 |
| A4 | passed | brief.md | A4：原 `web/` 无改动 | git diff --exit-code -- web/ 退出码 0；unittest test_a4_web_untouched 通过。 |

## 检查

| 检查 | 命令 | 工作目录 | 状态 | 退出码 | 耗时 |
| --- | --- | --- | --- | ---: | ---: |
| Omni 1.7B and related unit tests | -m unittest tests.test_omni_tts_1_7b tests.test_omni_base_clone tests.test_default_omnitts | . | passed | 0 | 249 ms |
| web/ unchanged | diff --exit-code -- web/ | . | passed | 0 | 8 ms |
| start-omni.sh default remains 0.6B CustomVoice | -F MODEL="${OMNI_MODEL:-Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice}" start-omni.sh | . | passed | 0 | 4 ms |
| 1.7B yaml utilization 0.25 | -c gpu_memory_utilization: 0.25 deploy/qwen3_tts_1.7b.yaml | . | passed | 0 | 3 ms |
| Docs cover 1.7B start and first download | -E OMNI_MODEL=Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice\|HF_HUB_OFFLINE=0\|同卡更容易 OOM docs/omni_tts.md README.md | . | passed | 0 | 8 ms |

## 阻塞项

_无。_

## 风险与跳过的工作

- 本切片未实际下载或启动 1.7B 权重/8091，同卡 OOM 与真实拉起未实测（规格明确不要求）。

## 之前的迭代

| 目标周期 | 迭代 | 尝试 | 结果 | 未解决项 | 摘要 | 完成时间 |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 1 | 1 | pass | — | A1–A4 全部通过：默认仍 0.6B+0.6b yaml；1.7B 走独立 1.7b yaml 且两阶段 0.25；文档含启动/下载/同卡 OOM 且已去掉「本规格不部署 1.7B」；web/ 无改动。未实启 8091 不阻塞本切片验收。 | 2026-09-17T02:01:34.019Z |



## 结论

A1–A4 全部通过：默认仍 0.6B+0.6b yaml；1.7B 走独立 1.7b yaml 且两阶段 0.25；文档含启动/下载/同卡 OOM 且已去掉「本规格不部署 1.7B」；web/ 无改动。未实启 8091 不阻塞本切片验收。
