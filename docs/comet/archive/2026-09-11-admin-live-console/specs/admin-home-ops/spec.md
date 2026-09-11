# 管理员首页待办

## 能力

管理员登录后，`/app/admin` 只展示运营待办。WebRTC 演示在独立页。普通用户首页行为不变。

## 汇总接口

`GET /api/v1/admin/home` 须登录且 `role=admin`。未登录 401，普通用户 403。

返回至少：

- `pending_orders`：状态为 `submitted` 的订单数量
- `active_sessions`：`session_manager` 中非空会话数
- `max_sessions`：全局会话上限
- `running_tasks`：生成任务状态为 `pending` 或 `running` 的数量

不返回密钥、Cookie、口令。

## 管理员界面

- 三张待办卡片展示上述数字。
- `pending_orders` 卡片进入管理后台（`/app/admin/ops`）。
- `running_tasks` 卡片进入 Avatar 生成（`/app/admin/avatar`）。
- 进入页面时拉取一次；本规格不要求实时推送。
- 提供「去演示连麦」入口，进入 `/app/admin/live`。
- 本页不提供选形象、开始连接、发文字或打断。

## 非范围

- 不在此页接单、驳回或启动生成
- 不强制结束会话
- 不在此页提供音频上传、录制或动作编排
