# 目标

管理员在 `/app/admin/live` 连麦后可用麦克风说话，经本机 `/api/asr` 识别，停止后自动按当前 Echo/Chat 走现有 `/human` 驱动口型。不必再打开 `/index.html`。

# 范围

- 仅管理员演示连麦 `/app/admin/live`：在「说话」监视器框增加开始说话 / 停止识别
- 复用现有 `GET /api/asr` WebSocket，不改协议、不改 `web/`
- 未连接时麦克风不可用；空识别或失败在本页提示，不发送
- 去掉演示连麦上的「打开 /index.html」
- 更新 `admin-live-console` 与 `web-app-shell`

# 非目标

- 不改 `web/` HTML/JS/CSS，不搬 FunASR 完整面板（地址栏、模式单选）
- 不给用户首页加麦克风
- 不改 `/api/asr` 模型，不改登录/订单/TTS/默认入口

# 验收示例

- A1：已连接时可开始/停止麦克风；未连接时麦克风不可用
- A2：停止识别后，非空文本按当前 Echo/Chat 调用 `POST /human`（含当前 `sessionid`）
- A3：空识别或失败只在本页提示、不发送；页面没有 FunASR 地址栏
- A4：演示连麦不再出现「打开 /index.html」；`web/` 无改动

# 约束与不变量

- 工作区：main 当前目录（`isolation: current`）
- 沿用现有 `/api/asr`；funasr 未安装时端点不注册，页面提示不可用
- Gallery 说话框内增加控件，不新开第三栏

# 决策

- 切片：只做管理员演示连麦麦克风 ASR
- 隔离：当前目录 main
- 控件：开始说话 / 停止识别，与「开始录制」同类
- 停止后自动按当前 Echo/Chat 发送
- 去掉「打开 /index.html」

# 待解决问题

无。用户已确认：管理员演示连麦加开始/停止麦克风；停止后非空文本按当前 Echo/Chat 自动 `/human`；去掉「打开 /index.html」；不改 `web/`、不迁用户首页。

# 验证预期

- 单测覆盖未连接禁用、停止后 /human 载荷、空结果不发送、无 FunASR 地址、无 /index.html 链接
- `git diff --exit-code -- web/`
