# 目标

管理员打开 `/app/admin` 即可看到运营待办：待处理订单数、活跃连麦会话数、进行中的生成任务数。连麦演示仍走原站点 `/`，不在本 change 迁入 WebRTC 控制台。

# 范围

- 管理员首页从占位改为待办卡片
- 仅管理员可拉取汇总；数字可点到管理后台或 Avatar 生成页
- 活跃会话取进程内 `session_manager`；订单与任务取 SQLite

# 非目标

- 不把原 `web/index.html` 连麦迁进 `/app/admin`
- 不强制结束会话、不支付、不改用户首页
- 不改口型模型、不自动生成 preview.mp4
- 不归档 `omni-local-tts`

# 验收示例

- A1：管理员打开首页可见待处理订单数、活跃会话数、进行中生成任务数
- A2：存在 `submitted` 订单时，待处理订单数至少为该数量；点该卡片进入管理后台
- A3：无活跃会话时活跃数为 0；有 WebRTC 会话时计数与进程内会话一致
- A4：存在 `pending`/`running` 生成任务时，「生成中」计数包含它们；点该卡片进入 Avatar 生成
- A5：普通用户或未登录访问汇总接口为 403/401；用户首页不变

# 约束与不变量

- 工作区：`.worktrees/admin-home-ops`，基于已合入 TTS/硬化的 main
- `omni-local-tts` 仍占用 main 的 current 隔离
- 单测不依赖 GPU / 8091

# 决策

- 隔离：独立 worktree
- 管理员首页：待办条，连麦仍用原 `/`
- 待处理订单 = 状态 `submitted`
- 生成中 = 任务状态 `pending` 或 `running`

# 待解决问题

（无）

# 验证预期

- 用测试库造订单/任务/假会话，不连真 WebRTC
