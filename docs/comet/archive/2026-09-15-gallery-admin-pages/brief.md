# 目标

把管理员壳内除首页外的工作页（演示连麦、Avatar 生成、管理后台、TTS）纳入已有的 Broadcast Gallery 视觉世界：暗墙、细侧栏、带 bezel / tally 的监视器框。能力、文案含义、接口与路由不变。

# 范围

- `/app/admin/live`、`/app/admin/avatar`、`/app/admin/ops`、`/app/admin/tts` 的页面容器从浅色 SaaS 玻璃卡改为 Gallery 监视器框（tally + bezel + 暗屏）
- 复用管理员首页已有的 Gallery token（`--wall` / `--bezel` / `--indigo` 等），不另起品牌色
- 演示连麦保持现有两栏任务布局（连接/画面 | 说话、音频、录制、动作），不改成首页那种三面墙
- 更新 `web-app-shell` 与 `admin-live-console` 正式规格中的视觉描述

# 非目标

- 不改登录页、用户壳（首页 / 资产 / 定制）
- 不改管理员首页（已是预监墙）
- 不改原 `web/`，不把麦克风 ASR 迁进 `/app`
- 不把默认入口从 `/` 改到 `/app/`
- 不做支付、自助注册、报表、图+音频自动口型
- 不从成品重扫整份 `DESIGN.md`（本轮只铺页面，不跑 Impeccable document）

# 验收示例

- A1：`/app/admin/live` 的工作区是 Gallery 监视器框（可见 tally/bezel），不是浅色玻璃卡；选形象、连接、Echo/Chat、打断、音频上传、录制、动作编排仍可用
- A2：`/app/admin/avatar` 同样是监视器框；仍可从已接单订单启动生成并看到任务表
- A3：`/app/admin/ops` 同样是监视器框；订单、开户、订阅绑定仍可用
- A4：`/app/admin/tts` 同样是监视器框；不填 8091 仍可拉音色/试听/上传删除
- A5：登录页与用户壳仍是浅色玻璃卡片；`web/` 无改动；现有 `/api/v1` 行为不因本 change 改变

# 约束与不变量

- 工作区：main 当前目录（`isolation: current`）
- 不改口型模型、WebRTC 信令路径、TTS 代理接口
- 管理员壳已有 `gallery` 侧栏/顶栏，本轮补的是内容区，不是再换一套导航

# 决策

- 切片：其余管理页改 Gallery，不含登录页和用户端
- 隔离：当前目录 main
- 演示连麦保持两栏任务布局，用监视器框包住现有区块，不做三面墙
- 表单与表格留在框内，不把每张表拆成首页那种大数字监视器

# 待解决问题

无。用户已确认：管理员四页（连麦 / 生成 / 后台 / TTS）改成 Gallery 监视器框；能力与接口不变；登录页和用户端本轮不动。

# 验证预期

- 对照四处 Vue 是否使用监视器框而不是浅色 `.glass.card` 作为主容器
- 回归现有 platform / live / orders / tts 单测
- `git diff --exit-code -- web/`
