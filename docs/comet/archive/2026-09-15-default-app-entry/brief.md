# 目标

默认 WebRTC 启动时，打开服务根路径进入 Vue 工作台 `/app/`（未登录到登录页，已登录按角色进壳）。原站控制台仍可匿名打开 `/index.html`。

# 范围

- 默认 transport（webrtc / `./start.sh`）：`GET /` 重定向到 `/app/`
- `/index.html` 仍提供原 `web/index.html` 控制台
- `/app/admin/live` 的麦克风 ASR 入口改为打开 `/index.html`（避免再点回 `/` 绕进 `/app/`）
- 更新 `web-app-shell`、`admin-live-console` 入口与原站链接描述
- 同步 `PRODUCT.md` 入口说明

# 非目标

- 不改原 `web/` 的 HTML/JS/CSS
- 不把麦克风 ASR 迁进 `/app`
- 不改登录、角色、Gallery、禁用用户、TTS、订单
- 不改 rtmp / rtcpush 启动时 `/` 指向对应 HTML 页的行为

# 验收示例

- A1：默认 WebRTC 下 `GET /`（不跟随跳转）返回 302/301，Location 为 `/app/` 或等价 `/app`
- A2：`GET /index.html` 仍返回原站控制台（200），不是 Vue 壳
- A3：`/app/admin/live` 的原站入口指向 `/index.html`，文案不再是「打开 /」链到 `/`
- A4：`web/` 无改动；rtmp / rtcpush 时 `GET /` 仍分别指向 `rtmpapi.html` / `rtcpushapi.html`

# 约束与不变量

- 工作区：main 当前目录（`isolation: current`）
- `/app/` 未登录进登录页、已登录按角色进壳，沿用现有 SPA 路由
- 原 `web/` 文件不被改写

# 决策

- 切片：只改默认入口与原站链接，不迁 ASR
- 隔离：当前目录 main
- 原站仍走 `/index.html`
- rtmp / rtcpush 的 `/` 特例保持不变（本切片只改默认 WebRTC 入口）

# 待解决问题

无。用户已确认：默认 WebRTC 下 `/` → `/app/`；原站走 `/index.html`；演示连麦 ASR 链到 `/index.html`；不改 `web/`、不迁 ASR；rtmp/rtcpush 的 `/` 特例保持。

# 验证预期

- 单测覆盖根路径重定向、`/index.html` 仍为原站、Live 页链接、rtmp/rtcpush 特例
- `git diff --exit-code -- web/`
