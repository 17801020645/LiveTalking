# 用户首页连麦

## 能力

已登录且已发布一个数字人的普通用户，可在 `/app` 用户首页建立 WebRTC，收看该形象的音视频，并发送文字或麦克风识别结果驱动口型。连接后可在 echo（复读）与 chat（LLM）之间切换，并可打断当前说话。连接后还可上传音频驱动口型、开始/停止录制并下载、按 audiotype 切换动作。未发布时不能连接。

## 首页

- 无已发布形象：提示前往「我的资产」发布；不展示开始连接按钮。
- 有已发布形象：展示名称、开始/断开、远端 video/audio、文本输入与发送、echo/chat 模式、打断。
- 连接后可用麦克风：「开始说话」采集音频，经 `GET /api/asr` WebSocket 识别；「停止识别」后若文本非空，按当前 echo/chat 自动 `POST /human`（与文字发送相同，带本次 `sessionid`）。空结果或失败只在本页提示，不发送。未连接时麦克风、发送与打断均不可用。没有 FunASR 服务器地址栏，也没有 2pass/online/offline 模式选择。
- 连接后可在同一块连麦监视器内：选择音频文件并上传播放（走现有 `/humanaudio` 或同等已有接口）；开始/停止录制，停止后可下载该 `sessionid` 录像；提交 audiotype 索引以切换自定义动作状态。未连接时这些操作不可用。
- 管理员演示连麦在 `/app/admin/live`，走 `POST /api/v1/admin/offer`，不使用 `/api/v1/me/offer`。管理员首页不建立 WebRTC。

## 信令

`POST /api/v1/me/offer`（Cookie 登录，role=user）：

- 读取该用户 `is_published=1` 的订阅；没有则 400。
- 创建会话时 `avatar` 固定为该 `avatar_id`，丢弃请求里的其它形象字段。
- 成功返回 SDP answer 与 `sessionid`，并把该 `sessionid` 绑到当前用户。
- 同一用户已有由本接口创建的会话时，拒绝新的一路（明确错误）。
- 计入全局 `max_session`。

匿名 `POST /offer` 行为不变，客户端仍可传 `avatar`。仅原站使用该接口；管理员演示台改走 `admin/offer`。

## 说话与打断

连接成功后：

- 发送：`POST /human`，`{ text, type: "echo"|"chat", interrupt: true, sessionid }`。默认模式为 echo。
- 打断：`POST /interrupt_talk`，`{ sessionid }`。
- 麦克风识别成功后走与文字发送相同的 `type`。

本接口创建的会话：上述驱动须同一用户 Cookie。未登录 401；其它用户 403。匿名 `/offer` 创建的会话仍允许匿名驱动。

## 音频、录制与动作

- 音频驱动：连接后选择音频文件并上传播放（走现有 `/humanaudio` 或同等已有接口，带本次 `sessionid`）。
- 录制：连接后开始/停止录制（现有 `/record`），停止后可下载该 `sessionid` 录像。
- 动作编排：连接后提交 audiotype 索引以切换自定义动作状态（现有 `/set_audiotype`，带本次 `sessionid`）。

对本接口创建的会话，上述请求同样须同一用户 Cookie。

用户首页不提供参考音频或参考文本。上述控件与连麦主路径放在同一块监视器框内，不是管理员演示台那种多框任务台。

## 资产

发布/取消发布、同时仅 1 个已发布，沿用既有 `/api/v1/me/avatars` 行为，本 change 不改。
