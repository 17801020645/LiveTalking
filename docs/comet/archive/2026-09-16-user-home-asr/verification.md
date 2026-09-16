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
- 完成时间: 2026-09-16T09:15:17.587Z
- 摘要: A1–A4 均通过：用户首页连麦后可用麦克风经 /api/asr 识别，停止后非空文本按 echo 带 sessionid 发送；空/失败只提示不发；README 已写麦克风说话且 web/ 未改。

## 验收

| 编号 | 结果 | 来源 | 验收项 | 原因 |
| --- | --- | --- | --- | --- |
| A1 | passed | brief.md | A1：已连接时可开始/停止麦克风；未连接时麦克风不可用 | Home.vue 连麦框有开始说话/停止识别；按钮 disabled 含 !connected，startMic 未连接或无 sessionid 直接 return。 |
| A2 | passed | brief.md | A2：停止识别后，非空文本 `POST /human`，`type=echo`，带当前 `sessionid` | stopMic 非空文本调用 sendHuman；POST /human 固定 type=echo 且带 sessionid.value，无 talkType/chat。 |
| A3 | passed | brief.md | A3：空识别或失败只在本页提示、不发送；页面没有 FunASR 地址栏 | 空结果本页提示未识别到语音并 return，不发送；失败只写本页错误。无 wssip/2pass/asr_mode/FunASR 地址栏。 |
| A4 | passed | brief.md | A4：`web/` 无改动；README 用户入口提到麦克风说话 | git diff web/ 与 README-EN 无改动；README 普通用户行写有麦克风说话。 |

## 检查

| 检查 | 命令 | 工作目录 | 状态 | 退出码 | 耗时 |
| --- | --- | --- | --- | ---: | ---: |
| User home ASR and related unit tests | -m unittest tests.test_user_home_asr tests.test_admin_live_asr tests.test_user_live tests.test_admin_live_console tests.test_gallery_user_shell tests.test_default_app_entry | . | passed | 0 | 3652 ms |
| web/ and README-EN.md unchanged | diff --exit-code -- web/ README-EN.md | . | passed | 0 | 27 ms |
| README user entry mentions microphone | -E 麦克风说话 README.md | . | passed | 0 | 7 ms |

## 阻塞项

_无。_

## 风险与跳过的工作

- 未在浏览器实点麦克风；8010 当时未监听；funasr 未安装时 /api/asr 不注册
- 生产 /app/ 需 npm run build 后才会看到 Home.vue 改动
- 验收测试是源码静态断言，不是真实 WebRTC/ASR 运行时

## 之前的迭代

| 目标周期 | 迭代 | 尝试 | 结果 | 未解决项 | 摘要 | 完成时间 |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 1 | 1 | pass | — | A1–A4 均通过：用户首页连麦后可用麦克风经 /api/asr 识别，停止后非空文本按 echo 带 sessionid 发送；空/失败只提示不发；README 已写麦克风说话且 web/ 未改。 | 2026-09-16T09:15:17.587Z |



## 结论

A1–A4 均通过：用户首页连麦后可用麦克风经 /api/asr 识别，停止后非空文本按 echo 带 sessionid 发送；空/失败只提示不发；README 已写麦克风说话且 web/ 未改。
