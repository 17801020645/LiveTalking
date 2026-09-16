# 目标

管理员在管理后台可以对已禁用的普通用户点「启用」。启用后该用户用原密码可以再登录。`README.md` 同步到当前产品入口、启动方式和 Omni 克隆用法。

# 范围

- `POST /api/v1/admin/users/{user_id}/enable`：仅 `role=user` 且当前 `disabled`；成功后 `status=active`，密码不变
- 管理后台用户表：已禁用普通用户显示启用（经确认）；活跃普通用户仍显示禁用
- `README.md` 写明默认 `/app/`、`./start.sh` / `./start-omni.sh`、Omni 默认 CustomVoice 与 0.6B-Base 克隆

# 非目标

- 不删除用户、不自助注册、不邮箱验证码、不代人改密
- 不改 `web/`，不改 `README-EN.md`
- 不做用户首页 ASR、不部署 1.7B、不做图+音频口型
- 不清理遗留 `omni-local-tts` 状态

# 验收示例

- A1：管理员对已禁用普通用户点启用（经确认）后，该行状态为 `active`，再用原密码可以登录
- A2：对活跃用户、管理员或当前登录账号调用启用失败；未登录 401，普通用户 403
- A3：活跃行仍有禁用、已禁用行有启用；管理员行没有这两个按钮
- A4：`README.md` 写明默认入口 `/app/`、本机 `./start.sh` 与 Omni 克隆；不再把 `/index.html` 写成唯一客户端入口

# 约束与不变量

- 工作区：main 当前目录（`isolation: current`）
- 启用不恢复已被删除的会话；用户需重新登录
- 单测不连浏览器；`web/` 无改动

# 决策

- 切片：启用用户 + 同步 README
- 隔离：当前目录 main
- 启用接口对称禁用：`POST .../enable`，只处理 `role=user` 且 `disabled`
- 密码与订阅保持禁用前状态
- 只改中文 `README.md`

# 待解决问题

无。用户已确认：启用接口对称禁用；启用后原密码可登录；README 同步入口与 Omni 克隆；不改 web/ 与 README-EN。

# 验证预期

- 单测覆盖启用后可登录、错误角色/状态失败、页面按钮分流
- 对照 README 含 `/app/` 与 Omni Base 克隆命令
