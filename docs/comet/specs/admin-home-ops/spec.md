# 管理员首页待办

## 能力

管理员登录后，`/app/admin` 展示运营待办，而不是只给原站 `/` 的链接。连麦演示仍使用原 `/`。普通用户首页行为不变。

## 汇总接口

`GET /api/v1/admin/home` 须登录且 `role=admin`。未登录 401，普通用户 403。

返回至少：

- `pending_orders`：状态为 `submitted` 的订单数量
- `active_sessions`：`session_manager` 中非空会话数
- `max_sessions`：全局会话上限
- `running_tasks`：生成任务状态为 `pending` 或 `running` 的数量

不返回密钥、Cookie、口令。

## 管理员界面

- 三张（或同等）待办卡片展示上述三个数字。
- `pending_orders` 卡片进入管理后台（`/app/admin/ops`）。
- `running_tasks` 卡片进入 Avatar 生成（`/app/admin/avatar`）。
- 仍提供打开原站点 `/` 的链接，供演示连麦。
- 进入页面时拉取一次；本规格不要求实时推送。

## 非范围

- 不在 `/app/admin` 重建 WebRTC / 对话 / 录制控制台
- 不在此页接单、驳回或启动生成
- 不强制结束会话
