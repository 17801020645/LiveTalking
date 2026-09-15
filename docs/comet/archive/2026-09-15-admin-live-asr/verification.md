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
- 完成时间: 2026-09-15T12:49:15.452Z
- 摘要: 管理员演示连麦麦克风 ASR 按 brief A1–A4 落地。

## 验收

| 编号 | 结果 | 来源 | 验收项 | 原因 |
| --- | --- | --- | --- | --- |
| A1 | passed | brief.md | A1：已连接时可开始/停止麦克风；未连接时麦克风不可用 | 说话框有开始说话/停止识别；未连接时按钮禁用；startMic 另要求 sessionid。 |
| A2 | passed | brief.md | A2：停止识别后，非空文本按当前 Echo/Chat 调用 `POST /human`（含当前 `sessionid`） | stopMic 经 /api/asr 取文本后 sendHuman，POST /human 带当前 talkType 与 sessionid。 |
| A3 | passed | brief.md | A3：空识别或失败只在本页提示、不发送；页面没有 FunASR 地址栏 | 空识别提示未识别到语音且不发送；失败提示在本页；无 FunASR 地址栏/2pass。 |
| A4 | passed | brief.md | A4：演示连麦不再出现「打开 /index.html」；`web/` 无改动 | Live.vue 无打开 /index.html；git diff --exit-code -- web/ 通过。 |

## 检查

| 检查 | 命令 | 工作目录 | 状态 | 退出码 | 耗时 |
| --- | --- | --- | --- | ---: | ---: |
| Admin live ASR and related unit tests | -m unittest tests.test_admin_live_asr tests.test_gallery_admin_pages tests.test_admin_live_console tests.test_user_live tests.test_default_app_entry | . | passed | 0 | 3680 ms |
| Original web/ unchanged | diff --exit-code -- web/ | . | passed | 0 | 2 ms |

## 阻塞项

_无。_

## 风险与跳过的工作

- 8010 未在听，未做浏览器点麦克风；funasr 未装时 /api/asr 不注册。

## 之前的迭代

| 目标周期 | 迭代 | 尝试 | 结果 | 未解决项 | 摘要 | 完成时间 |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 1 | 1 | pass | — | 管理员演示连麦麦克风 ASR 按 brief A1–A4 落地。 | 2026-09-15T12:49:15.452Z |



## 结论

管理员演示连麦麦克风 ASR 按 brief A1–A4 落地。
