# 目标

普通用户在 `/app` 首页连麦后可用麦克风说话，经本机 `/api/asr` 识别，停止后自动按现有 echo 走 `/human` 驱动口型。行为与管理员演示连麦对称，不改 `web/`。

# 范围

- 仅用户首页 `/app/user`（连麦监视器框）：连接后增加开始说话 / 停止识别
- 复用现有 `GET /api/asr` WebSocket，不改协议
- 未连接时麦克风不可用；空识别或失败在本页提示，不发送
- 停止后非空文本 `POST /human`，`type=echo`（与当前文字发送一致），带本次 `sessionid`
- 更新 `user-live`、`web-app-shell`；README 用户入口补一句麦克风说话

# 非目标

- 不改 `web/`，不搬 FunASR 完整面板
- 不给用户首页加 Echo/Chat 切换或打断、上传、录制
- 不改 `/api/asr` 模型，不改管理员演示连麦
- 不部署 1.7B、不做图+音频口型

# 验收示例

- A1：已连接时可开始/停止麦克风；未连接时麦克风不可用
- A2：停止识别后，非空文本 `POST /human`，`type=echo`，带当前 `sessionid`
- A3：空识别或失败只在本页提示、不发送；页面没有 FunASR 地址栏
- A4：`web/` 无改动；README 用户入口提到麦克风说话

# 约束与不变量

- 工作区：main 当前目录（`isolation: current`）
- 沿用现有 `/api/asr`；funasr 未安装时端点不注册，页面提示不可用
- 控件放在现有连麦监视器框内，不新开一栏
- 旧 `tests/test_admin_live_asr.py` 中「用户首页无 ASR」断言改为允许用户首页 ASR

# 决策

- 切片：用户首页麦克风 ASR
- 隔离：当前目录 main
- 停止后自动 echo 发送（用户首页现有文字发送就是 echo）
- 不增加 Chat / 打断

# 待解决问题

- 无。用户已确认目标、范围、验收 A1–A4 与非目标。

# 验证预期

- 单测覆盖未连接禁用、停止后 /human 为 echo、空结果不发送、无 FunASR 地址
- `git diff --exit-code -- web/`
