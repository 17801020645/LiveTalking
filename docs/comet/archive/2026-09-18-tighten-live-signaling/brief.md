# 目标

锁住 `/app` 连麦：管理员演示台走登录后的 `POST /api/v1/admin/offer`；用户与管理员会话的 `/human` 等驱动接口必须是同一登录用户。原站匿名 `POST /offer` 仍可用。

# 范围

- 新增 `POST /api/v1/admin/offer`：须管理员 Cookie，形象来自目录勾选
- [`frontend/src/views/admin/Live.vue`](frontend/src/views/admin/Live.vue) 改走该接口，不再打匿名 `/offer`
- offer 成功时把 `sessionid` 绑到当前用户
- `/human`、`/interrupt_talk`、`/humanaudio`、`/record`、`GET /record/{sessionid}`、`/set_audiotype`：会话来自 `me/offer` 或 `admin/offer` 时须同一登录用户；匿名 `/offer` 创建的会话仍允许匿名
- 未登录不能拿别人的 `sessionid` 驱动 `/app` 连麦
- 更新 `auth-rbac`、`admin-live-console`、`user-live`；`PRODUCT.md` 不再写管理员走匿名 `/offer`

# 非目标

- 不改 `web/` HTML/JS/CSS
- 不把匿名 `/offer` 改成必须登录
- 不收紧 `/whep`、`/sse`、`/api/admin/config`
- 不实现忘记密码
- 不恢复幽灵 change `omni-local-tts`

# 验收示例

- A1：未登录 `POST /offer` 仍可用（原站）；原 `web/` 无改动
- A2：管理员演示台用 `/api/v1/admin/offer`；未登录 401，普通用户 403
- A3：用户 `me/offer` 的 session，别人匿名 `/human`（及打断/音频/录制/动作）失败；本人 Cookie 可以
- A4：管理员 `admin/offer` 的 session，未登录或其它用户驱动失败；该管理员可以

# 约束与不变量

- 工作区：main 当前目录（`isolation: current`）
- 用户首页仍走 `/api/v1/me/offer`，形象仍强制已发布
- 管理员演示台形象仍来自 `GET /api/v1/admin/avatars`，可带 `refaudio` / `reftext`
- 单测不依赖真 WebRTC / GPU
- 未登录驱动已绑定会话：401；已登录但不是会话主人：403

# 决策

- 切片：收紧匿名信令；忘记密码留给后续 change
- 隔离：当前目录 main
- 原站匿名 `/offer` 保留；`/app` 管理员改走 `admin/offer`
- 会话归属在进程内绑定（与现有 `user_rtc_sessions` 同类），不落 SQLite
- 驱动接口按会话是否绑定决定是否要登录，而不是一律登录（否则原站会挂）

# 待解决问题

（无）

# 验证预期

- 单测覆盖：匿名 /offer 仍 200；admin/offer 鉴权；绑定会话匿名 /human 失败、主人成功
- 更新与「Live.vue 打 /offer」冲突的旧测试
- `git diff --exit-code -- web/`
