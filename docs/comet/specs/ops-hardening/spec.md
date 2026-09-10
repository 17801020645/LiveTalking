# 运维硬化

## 能力

LiveTalking 8010 进程可被探活，跨域不再对任意 Origin 放行凭证，Avatar 生成任务写入 SQLite。进程重启后管理员仍能看到任务历史。订单上传大小限制与全局会话上限沿用既有实现，本规格不重复定义。

## 探活

- `GET /healthz` 公开，无需登录。
- 进程能接受 HTTP 时返回 200。
- 响应为简单 JSON，例如 `{"ok": true}`。不得包含密钥、口令、会话 Token、引导管理员凭据。
- 不探测 GPU、不探测 8091、不探测外部 TTS。数据库文件不可用时仍应返回可区分的失败（非 200），但不泄露路径以外的内部细节。

## CORS

默认不再使用 `*` 作为允许 Origin。

允许的 Origin：

1. 与当前请求 Host 匹配的源（方案 + Host，含端口）。因此用 `http://127.0.0.1:8010` 或 `http://192.168.31.75:8010` 打开 `/app/` 时，浏览器带 Cookie 访问同源 API 可通过 CORS。
2. 环境变量 `LIVETALKING_CORS_ORIGINS`：逗号分隔的额外 Origin（用于 Vite 开发源等）。空则不加额外项。

对允许的 Origin：`Access-Control-Allow-Credentials` 为 true，允许常用请求头。对未允许的 Origin：不得回 `Access-Control-Allow-Origin: *`。

无 `Origin` 的请求（curl、同源导航）不受浏览器 CORS 拦截，服务端照常处理。

不改变 WebRTC ICE / SDP 语义。

## 生成任务落盘

Avatar 生成任务（`pending` / `running` / `completed` / `failed`）写入与平台共用的 SQLite，而不是只存在内存。

- 创建任务后立即落盘。
- 进度与终态更新后落盘。
- 进程重启后，`GET /api/avatar/tasks` 与 `GET /api/avatar/task/{task_id}` 仍返回已落盘记录，含 `task_id`、`model_type`、`avatar_id`、`status`、`progress`、`error_msg`、时间戳。
- 进程退出时仍为 `pending` 或 `running` 的任务，下次启动不得继续执行；列出时为 `failed`，`error_msg` 说明进程中断。
- 不自动重跑 GPU 生成。
- 本规格不要求自动清理过期任务。

## 任务接口鉴权

`POST /api/avatar/task`、`GET /api/avatar/tasks`、`GET /api/avatar/task/{task_id}`、`DELETE /api/avatar/task/{task_id}` 均须登录且 `role=admin`。未登录 401，普通用户 403。

原 `web/avatar.html` 在已登录管理员 Cookie 下仍可使用；未登录不再能列出他人任务。

## 非范围

- 不改口型生成算法与参数默认值
- 不改用户连麦、订单状态机、支付
- 不把任务历史做成独立产品报表
