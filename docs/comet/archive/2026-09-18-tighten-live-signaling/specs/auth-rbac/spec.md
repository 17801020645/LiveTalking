# 账号与角色访问

## 能力

LiveTalking 提供基于 Cookie 的登录与两种角色。新资源接口位于 `/api/v1/`。原站演示连麦 `POST /offer` 保持匿名。Avatar 生成任务接口仅管理员可调用。`/app` 里由登录用户创建的连麦会话，其驱动接口须同一用户。

## 角色

- `admin`：可开户、绑定订阅、禁用与启用普通用户、删除普通用户、为普通用户设置新密码、使用管理员壳、查看与创建生成任务、使用 TTS 代理、用 `POST /api/v1/admin/offer` 演示连麦。
- `user`：只能操作自己的会话与已订阅形象；不能开户、不能列出全部形象、不能调用生成任务或 TTS 代理，不能调用 `admin/offer`。

无其它角色。无自助注册接口。

## 引导管理员

进程启动时若用户表为空，且环境变量 `LIVETALKING_BOOTSTRAP_ADMIN` 与 `LIVETALKING_BOOTSTRAP_PASSWORD` 均非空，则创建该管理员。二者缺一则不创建，并在日志中提示无法登录管理端。凭据不写入仓库与默认配置文件。

## 登录会话

- `POST /api/v1/auth/login`：用户名+密码，成功后设置 httpOnly、SameSite 的会话 Cookie。
- `POST /api/v1/auth/logout`：清除会话。
- `GET /api/v1/auth/me`：返回当前用户 `id`、`username`、`role`；未登录 401。
- `POST /api/v1/auth/password`：已登录用户修改自己的密码。请求体含 `current_password` 与 `new_password`。当前密码错误则失败且哈希不变；新密码少于 6 个字符被拒绝。成功后当前会话 Cookie 仍有效，该用户其它会话被删除。未登录 401。
- 密码使用单向哈希存储。
- 失败登录不泄露账号是否存在的细节（统一「用户名或密码错误」）。
- `status=disabled` 的用户登录失败，文案与错误密码相同。

## 鉴权边界

需要登录的路径前缀：`/api/v1/`（`/api/v1/auth/login` 除外）、`/api/avatar/`。

保持匿名：`/` 静态 `web/`、`POST /offer`、`/whep`、`/api/admin/config`、`/api/admin/sessions`、`/sse`、`GET /healthz`。

条件匿名（视会话归属）：`POST /human`、`POST /interrupt_talk`、`POST /humanaudio`、`POST /record`、`GET /record/{sessionid}`、`POST /set_audiotype`。

- 会话由匿名 `POST /offer` 创建：仍允许匿名调用（原站）。
- 会话由 `POST /api/v1/me/offer` 或 `POST /api/v1/admin/offer` 创建：必须带创建该会话的同一用户 Cookie。未登录 401；其它用户 403。

管理员专属：创建用户、列出全部用户、绑定/解绑任意用户的订阅、禁用与启用普通用户、删除普通用户、为普通用户设置新密码、列出全部形象元数据、生成任务 CRUD、TTS 代理、`POST /api/v1/admin/offer`。普通用户调用返回 403。

## 用户管理（管理员）

- 创建普通用户（用户名唯一、初始密码）。
- 列出用户（不含密码哈希）。
- 禁用普通用户：`POST /api/v1/admin/users/{user_id}/disable`。仅 `role=user`。不能禁用当前登录账号。成功后该用户 `status=disabled`，其平台登录会话被删除；下次鉴权失败。
- 启用普通用户：`POST /api/v1/admin/users/{user_id}/enable`。仅 `role=user` 且当前 `status=disabled`。成功后 `status=active`。密码与订阅不变。不恢复已被删除的会话，用户须重新登录。对活跃用户、管理员或不存在的 id 返回明确失败（400 或 404）。
- 删除普通用户：`POST /api/v1/admin/users/{user_id}/delete`。仅 `role=user`（活跃或已禁用均可）。不能删除当前登录账号。成功后删除该用户行及其 sessions、subscriptions、orders。已生成的形象目录与形象元数据保留。对管理员或不存在的 id 返回明确失败（400 或 404）。删除后用原用户名登录失败，文案与错误密码相同。
- 代人改密：`POST /api/v1/admin/users/{user_id}/password`。仅 `role=user`（活跃或已禁用均可）。请求体 `{ "password" }`，至少 6 个字符（与开户相同）。不能给当前登录账号改密。成功后更新密码哈希，并删除该用户全部平台登录会话；`status`、订阅与订单不变。对管理员或不存在的 id 返回明确失败（400 或 404）；密码过短则失败且哈希不变。已禁用用户改密后仍不能登录，启用后须用新密码。
- 管理后台用户表：活跃普通用户显示禁用按钮；已禁用普通用户显示启用按钮；普通用户行另有删除按钮与改密按钮。禁用、启用、删除经确认；改密经确认后输入新密码。管理员行不显示这些按钮。
- 本规格不包含邮箱、验证码、忘记密码。
