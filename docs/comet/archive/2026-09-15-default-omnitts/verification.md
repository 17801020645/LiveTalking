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
- 完成时间: 2026-09-15T02:21:44.649Z
- 摘要: 默认 TTS 已改为 omnitts（8091/vivian），创建路径无 EdgeTTS 回退，失败可观察且不退出，文档含切回步骤。未重启 8010，现场听音未做。

## 验收

| 编号 | 结果 | 来源 | 验收项 | 原因 |
| --- | --- | --- | --- | --- |
| A1 | passed | brief.md | A1：仓库默认配置为 `tts: omnitts`、`TTS_SERVER: http://127.0.0.1:8091`、`REF_FILE: vivian`（yaml 与 `config.py` 默认一致） | config.yaml 为 tts: omnitts、TTS_SERVER: http://127.0.0.1:8091、REF_FILE: vivian；config.py argparse 默认值相同。parse_args 读 yaml 与跳过 yaml 时单测均得到这三项。Runtime grep 与 unittest 已过。 |
| A2 | passed | brief.md | A2：8091 已启动时，重启 8010 后文本驱动会话走 Omni 客户端，而不是 EdgeTTS | 默认 opt.tts 为 omnitts；start.sh 不覆盖 --tts；BaseAvatar 按 opt.tts 动态创建客户端，无改写为 edgetts 的路径。单测 test_a2 已过。只读探测 8091 /v1/audio/voices 返回 200 且含 vivian。未重启 8010、未做 Echo/Chat 听音，不因此判 blocked。 |
| A3 | passed | brief.md | A3：8091 未启动时，文本驱动不会悄悄改用 EdgeTTS；失败可观察（日志或无语音），且进程不必退出 | OmniTTS 创建时不探测 8091；合成失败只 logger.error/exception，不 yield、不 raise、无 sys.exit，也不改走 EdgeTTS。单测 ConnectionError 得到空 chunk。进程不必退出。 |
| A4 | passed | brief.md | A4：文档写明默认已是 Omni，以及改回 `edgetts` 并重启 8010 的步骤；不必停 8091 | docs/omni_tts.md 写明默认 tts: omnitts / 8091 / vivian，切回 tts: edgetts 后重启 ./start.sh，并含「不必停 8091」。change 内规格已同步。Runtime grep 与 test_a4 已过。web/ 无改动。 |

## 检查

| 检查 | 命令 | 工作目录 | 状态 | 退出码 | 耗时 |
| --- | --- | --- | --- | ---: | ---: |
| Default omnitts unit tests | -m unittest tests.test_default_omnitts | . | passed | 0 | 220 ms |
| config.yaml default tts omnitts 8091 vivian | -E ^tts: omnitts\|^TTS_SERVER: http://127.0.0.1:8091\|^REF_FILE: vivian config.yaml | . | passed | 0 | 8 ms |
| config.py argparse defaults omnitts 8091 vivian | -E default='omnitts'\|default="vivian"\|default='http://127.0.0.1:8091' config.py | . | passed | 0 | 6 ms |
| docs/omni_tts.md default Omni and switch back | -F 不必停 8091 docs/omni_tts.md | . | passed | 0 | 7 ms |
| Original web/ unchanged | diff --exit-code -- web/ | . | passed | 0 | 8 ms |

## 阻塞项

_无。_

## 风险与跳过的工作

- 当前 8010 可能仍是改默认前启动的进程；未重启则现场文本驱动不一定已切到 Omni。本次未做 Echo/Chat 听音。
- docs/comet/specs 主规格仍写默认 edgetts，需归档时同步；change delta 已改。

## 之前的迭代

| 目标周期 | 迭代 | 尝试 | 结果 | 未解决项 | 摘要 | 完成时间 |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 1 | 1 | pass | — | 默认 TTS 已改为 omnitts（8091/vivian），创建路径无 EdgeTTS 回退，失败可观察且不退出，文档含切回步骤。未重启 8010，现场听音未做。 | 2026-09-15T02:21:44.649Z |



## 结论

默认 TTS 已改为 omnitts（8091/vivian），创建路径无 EdgeTTS 回退，失败可观察且不退出，文档含切回步骤。未重启 8010，现场听音未做。
