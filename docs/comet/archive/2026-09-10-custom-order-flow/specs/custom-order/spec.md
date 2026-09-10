# 定制订单

## 能力

已登录普通用户可创建定制订单。管理员处理订单并调用现有 Avatar 生成。生成成功后形象入库并订阅给下单用户，默认不发布到首页。

## 素材

- `video`：上传视频文件。
- `image_audio`：上传图片与音频，另附 `script_text`。
- 两种模式都可附文字说明。
- 文件保存在 `data/uploads/orders/<order_id>/`，不接受客户端传入的本机绝对路径。

## 状态

`submitted` → `accepted` → `generating` → `completed`  
`submitted` 或 `generating` 可到 `rejected`。`rejected` 后用户可基于同一需求再提交新订单（新 ID）。

管理员：

- 接单：`submitted` → `accepted`
- 驳回：写入 `reject_reason`
- 开始生成：仅 `accepted` 且存在视频文件；创建 `/api/avatar/task` 并关联 `order_id`；状态 `generating`
- 任务 completed：订单 `completed`，扫描/写入 `avatars`，插入该用户订阅 `is_published=0`
- 任务 failed：订单 `rejected`，原因取任务错误信息

## API

用户（role=user）：

- `POST /api/v1/me/orders` multipart
- `GET /api/v1/me/orders`

管理员：

- `GET /api/v1/admin/orders`
- `POST /api/v1/admin/orders/{id}/accept`
- `POST /api/v1/admin/orders/{id}/reject` `{reason}`
- `POST /api/v1/admin/orders/{id}/generate` `{model, avatar_id, ...生成参数}`

`POST /api/avatar/task` 必须登录且 role=admin。

## 界面

- 用户「定制数字人」：上传区、说明、提交、订单列表（状态与驳回原因）。
- 管理后台：订单表 + 接单/驳回/生成。Avatar 生成占位页改为可选择订单并启动生成。
