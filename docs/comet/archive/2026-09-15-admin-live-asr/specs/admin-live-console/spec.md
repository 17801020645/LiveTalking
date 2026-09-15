# 管理员核心演示台

## 能力

管理员在 `/app/admin/live` 可选择已入库形象，建立 WebRTC，收看画面，并用 echo 或 chat 文字驱动口型，以及打断当前说话。连接后还可上传音频驱动口型、开始/停止录制并下载、按 audiotype 切换动作。连接后也可用麦克风说话：本机 `/api/asr` 识别，停止后自动按当前 echo/chat 发送。

## 页面结构

两栏：左侧为形象选择、可选参考音频/参考文本、开始/断开、远端画面与连接状态；右侧为说话（文字 + echo/chat + 打断 + 麦克风）、音频驱动、录制控制、动作编排。未连接时右侧操作禁用。错误提示显示在本页内。

视觉：各工作区块是 Broadcast Gallery 监视器框（tally + bezel + 暗屏），不是浅色玻璃卡。布局仍是两栏任务台，不是管理员首页的三面墙。

## 形象选择

形象列表来自 `GET /api/v1/admin/avatars`。页面不预选第一项。未选择形象时不能开始连接。

未连接时：若该形象有 `preview_url` 则静音循环预览（封面作 poster），否则展示 `cover_url`；都没有则留空画面区。

## 连接

开始连接时，浏览器 `POST /offer`，body 含 SDP 与所选 `avatar`。若填写了参考音频或参考文本，可随 offer 带上 `refaudio` / `reftext`。成功后保存 `sessionid`，播放远端视频。断开则关闭 RTCPeerConnection。

发送文字时可选择 `echo`（复读）或 `chat`（LLM）。

## 说话与打断

- 发送：`POST /human`，`{ text, type: "echo"|"chat", interrupt: true, sessionid }`
- 打断：`POST /interrupt_talk`，`{ sessionid }`
- 麦克风：连接后可「开始说话」采集音频，经 `GET /api/asr` WebSocket 识别；「停止识别」后若文本非空，按当前 echo/chat 自动发送（同一 `/human`）。空结果或失败只在本页提示，不发送。没有 FunASR 服务器地址栏，也没有 2pass/online/offline 模式选择。

未连接时不能发送、打断或使用麦克风。

## 音频、录制与动作

- 音频驱动：连接后选择音频文件并上传播放（走现有 `/humanaudio` 或同等已有接口）。
- 录制：连接后开始/停止录制，停止后可下载该 `sessionid` 录像。
- 动作编排：连接后提交 audiotype 索引以切换自定义动作状态。

## 与原站关系

原 `web/index.html` 保持可匿名使用，路径为 `/index.html`。麦克风 ASR 已在本页，不再提供「打开 /index.html」入口。
