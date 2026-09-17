# 目标

普通用户在 `/app/user` 连麦后，能像管理员演示台一样选择 echo/chat 发文字，并能打断当前说话。麦克风识别成功后按当前模式发送。形象选择、offer、资产发布不变。

# 范围

- 用户首页：echo/chat 模式、发送走 `/human` 的对应 `type`、打断走 `/interrupt_talk`
- 麦克风停止后非空识别结果按当前 echo/chat 自动发送（不再写死 echo）
- 更新 `user-live` 与壳层用户首页一句；README 用户工作台说明同步
- 现有 `test_user_home_asr` 中写死 echo、禁止 `talkType` 的断言改为跟当前模式

# 非目标

- 不把音频上传、录制、动作编排迁进用户首页
- 不改 `web/`，不改 `/api/v1/me/offer` 形象绑定规则
- 不把 `/human` / `/interrupt_talk` 改为必须登录
- 不做支付、自助注册、删除用户、EdgeTTS 回退
- 不恢复幽灵 change `omni-local-tts`

# 验收示例

- A1：连接后可把文字以 `type=echo` 或 `type=chat` 发到 `/human`，并带本次 `sessionid`；未连接不能发送
- A2：连接后点打断请求 `/interrupt_talk` 并带本次 `sessionid`；未连接不能打断
- A3：麦克风停止后非空识别按当前模式发送；切到 chat 则 `type=chat`。空结果不发送
- A4：原 `web/` 无改动；用户首页仍无音频上传/录制/动作编排

# 约束与不变量

- 工作区：main 当前目录（`isolation: current`）
- 用户仍只能连自己已发布形象
- 单测不依赖 GPU / 真 LLM；对照源码与既有假 RTC 测试即可

# 决策

- 切片：用户首页 Chat/打断，对齐管理员说话区，不搬音频/录制/动作
- 隔离：当前目录 main
- 默认模式 echo；麦克风跟随当前模式
- 发送仍带 `interrupt: true`（与管理员相同）；另有独立打断按钮

# 待解决问题

无。用户已确认目标、范围、验收 A1–A4 与非目标。

# 验证预期

- 单测覆盖 echo/chat 与打断路径，并更新旧 ASR 写死 echo 的断言
- `git diff --exit-code -- web/`
