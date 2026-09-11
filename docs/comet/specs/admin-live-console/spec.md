# 管理员核心演示台

## 能力

管理员在 `/app/admin/live` 可选择已入库形象，建立 WebRTC，收看画面，并用 echo 文字驱动口型，以及打断当前说话。

## 页面结构

两栏：左侧为形象选择、开始/断开、远端画面与连接状态；右侧为文字发送与打断。未连接时右侧禁用。错误提示显示在本页内。

## 形象选择

形象列表来自 `GET /api/v1/admin/avatars`。页面不预选第一项。未选择形象时不能开始连接。

未连接时：若该形象有 `preview_url` 则静音循环预览（封面作 poster），否则展示 `cover_url`；都没有则留空画面区。

## 连接

开始连接时，浏览器 `POST /offer`，body 含 SDP 与所选 `avatar`。成功后保存 `sessionid`，播放远端视频。断开则关闭 RTCPeerConnection。

本页不发送 `refaudio` / `reftext`。发送文字时可选择 `echo`（复读）或 `chat`（LLM）。

## 说话与打断

- 发送：`POST /human`，`{ text, type: "echo"|"chat", interrupt: true, sessionid }`
- 打断：`POST /interrupt_talk`，`{ sessionid }`

未连接时不能发送或打断。

## 与原站关系

原 `web/index.html` 保持可匿名使用。本页保留「打开 /」，用于音频上传、录制、动作编排等未迁入能力。
