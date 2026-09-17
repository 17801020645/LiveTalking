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
- 完成时间: 2026-09-17T14:25:08.214Z
- 摘要: A1–A4 均通过：未就绪才调 start-omni.sh，已就绪或 SKIP_OMNI=1 则跳过；Omni 失败仍起 8010 且不改 EdgeTTS。文档与 web/、默认模型边界均符合。

## 验收

| 编号 | 结果 | 来源 | 验收项 | 原因 |
| --- | --- | --- | --- | --- |
| A1 | passed | brief.md | A1：`start.sh` 在 8091 未就绪时会调用 `start-omni.sh`；8091 已响应 `/v1/audio/voices` 时不再拉起第二个；`SKIP_OMNI=1` 不调用 `start-omni.sh` | ensure_omni 先探测 /v1/audio/voices，失败才后台调用 start-omni.sh；探测成功打印跳过且不拉起；SKIP_OMNI=1 直接 return。单测 test_a1 与 Runtime unittest 均覆盖这三条。 |
| A2 | passed | brief.md | A2：Omni 环境缺失或启动失败时 `start.sh` 仍会启动 `app.py`（8010），并打出可观察的错误；不把 `tts` 改成 `edgetts` | 脚本缺失、子进程退出、等待超时三条路径都 return 0 后仍执行 app.py，stderr 含「仍启动 8010」；start.sh 无 --tts/edgetts。test_a2 确认 app 仍被拉起。 |
| A3 | passed | brief.md | A3：`README.md` / `README-EN.md` / `docs/omni_tts.md` 写明 `./start.sh` 会先起 Omni 再起数字人；换模型仍用 `./start-omni.sh` | README.md 写明 ./start.sh 先起 Omni（8091）再起数字人（8010），换模型仍用 ./start-omni.sh；README-EN.md 与 docs/omni_tts.md 对应表述齐全。Runtime 文档 grep 与 test_a3 通过。 |
| A4 | passed | brief.md | A4：原 `web/` 无改动；`start-omni.sh` 默认模型与双进程边界不变 | git diff --exit-code -- web/ 通过。start-omni.sh 仅改注释，默认仍是 Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice，独立 .venv-omni + exec vllm serve，与 8010 仍是双进程。 |

## 检查

| 检查 | 命令 | 工作目录 | 状态 | 退出码 | 耗时 |
| --- | --- | --- | --- | ---: | ---: |
| Omni-in-start.sh and related unit tests | -m unittest tests.test_omni_in_start_sh tests.test_omni_tts_1_7b tests.test_omni_base_clone tests.test_user_home_media tests.test_admin_enable_user | . | passed | 0 | 1679 ms |
| web/ unchanged | diff --exit-code -- web/ | . | passed | 0 | 9 ms |
| start.sh calls start-omni; README one-command start | -n START_OMNI\\|SKIP_OMNI\\|先起 Omni TTS\\|starts Omni TTS (8091) first\\|会先拉起 Omni 再起数字人 start.sh README.md README-EN.md docs/omni_tts.md | . | passed | 0 | 8 ms |

## 阻塞项

_无。_

## 风险与跳过的工作

- 单测用假 python/curl，未连真实 8091（brief 允许）
- 无 curl 时 omni_ready 恒失败，可能对已在听的 8091 再拉起一次

## 之前的迭代

| 目标周期 | 迭代 | 尝试 | 结果 | 未解决项 | 摘要 | 完成时间 |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 1 | 1 | pass | — | A1–A4 均通过：未就绪才调 start-omni.sh，已就绪或 SKIP_OMNI=1 则跳过；Omni 失败仍起 8010 且不改 EdgeTTS。文档与 web/、默认模型边界均符合。 | 2026-09-17T14:25:08.214Z |



## 结论

A1–A4 均通过：未就绪才调 start-omni.sh，已就绪或 SKIP_OMNI=1 则跳过；Omni 失败仍起 8010 且不改 EdgeTTS。文档与 web/、默认模型边界均符合。
