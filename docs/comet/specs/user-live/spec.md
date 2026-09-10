# 用户首页连麦

## 能力

已登录且已发布一个数字人的普通用户，可在 `/app` 用户首页建立 WebRTC，收看该形象的音视频，并发送文字驱动口型。未发布时不能连接。

## 首页

- 无已发布形象：提示前往「我的资产」发布；不展示开始连接按钮。
- 有已发布形象：展示名称、开始/断开、远端 video/audio、文本输入与发送。
- 管理员 `/app` 首页不提供上述控件，仍链到原站点 `/`。

## 信令

`POST /api/v1/me/offer`（Cookie 登录，role=user）：

- 读取该用户 `is_published=1` 的订阅；没有则 400。
- 创建会话时 `avatar` 固定为该 `avatar_id`，丢弃请求里的其它形象字段。
- 成功返回 SDP answer 与 `sessionid`。
- 同一用户已有由本接口创建的会话时，拒绝新的一路（明确错误）。
- 计入全局 `max_session`。

匿名 `POST /offer` 行为不变，客户端仍可传 `avatar`。

## 说话

连接成功后，前端把用户输入 POST 到现有 `/human`，带 `sessionid` 与 `text`。本 change 不要求 `/human` 登录。

## 资产

发布/取消发布、同时仅 1 个已发布，沿用既有 `/api/v1/me/avatars` 行为，本 change 不改。
