# 账号与角色访问

## 能力

LiveTalking 提供基于 Cookie 的登录与两种角色。新资源接口位于 `/api/v1/`。原有演示接口保持匿名，确保 `web/` 仍可直接连麦和生成 Avatar。

## 角色

- `admin`：可开户、绑定订阅、使用管理员壳。
- `user`：只能操作自己的会话与已订阅形象；不能开户、不能列出全部形象。

无其它角色。无自助注册接口。

## 引导管理员

进程启动时若用户表为空，且环境变量 `LIVETALKING_BOOTSTRAP_ADMIN` 与 `LIVETALKING_BOOTSTRAP_PASSWORD` 均非空，则创建该管理员。二者缺一则不创建，并在日志中提示无法登录管理端。凭据不写入仓库与默认配置文件。

## 登录会话

- `POST /api/v1/auth/login`：用户名+密码，成功后设置 httpOnly、SameSite 的会话 Cookie。
- `POST /api/v1/auth/logout`：清除会话。
- `GET /api/v1/auth/me`：返回当前用户 `id`、`username`、`role`；未登录 401。
- 密码使用单向哈希存储。
- 失败登录不泄露账号是否存在的细节（统一「用户名或密码错误」）。

## 鉴权边界

需要登录的路径前缀：`/api/v1/`（`/api/v1/auth/login` 除外）。

保持匿名：`/` 静态 `web/`、`/offer`、`/whep`、`/human`、`/humanaudio`、`/api/avatar/*`、`/api/admin/config`、`/api/admin/sessions`、`/sse`。

管理员专属：创建用户、列出全部用户、绑定/解绑任意用户的订阅、列出全部形象元数据。普通用户调用返回 403。

## 用户管理（管理员）

- 创建普通用户（用户名唯一、初始密码）。
- 列出用户（不含密码哈希）。
- 禁用用户后该用户不能登录；已有 Cookie 在下次鉴权时失败。
- 本规格不包含删除用户、邮箱、验证码。
