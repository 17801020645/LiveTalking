# 目标

普通用户在首页连麦后，可在同一块监视器内上传音频驱动口型、开始/停止录制并下载、按 audiotype 切换动作。`README-EN.md` 对齐中文 README 的产品入口（`/app/`、本机启动、Omni）以及用户连麦能力。

# 范围

- 用户首页现有连麦监视器内：音频上传（`/humanaudio`）、开始/停止录制与下载（`/record`）、audiotype 动作切换（`/set_audiotype`）；均带本次 `sessionid`
- 未连接时这些操作不可用
- `README.md` 用户工作台说明带上音频/录制/动作
- `README-EN.md` 对齐中文的默认入口、`./start.sh` / `./start-omni.sh`、Omni 与用户连麦说明（不整篇重写 Features）
- 更新 `user-live`、`web-app-shell`

# 非目标

- 不改 `web/` HTML/JS/CSS
- 不把参考音频/参考文本迁进用户首页
- 不把用户首页改成管理员那种多框任务台
- 不改管理员演示连麦
- 不支付、不注册、不代人改密
- 不恢复幽灵 change `omni-local-tts`
- 不把 Omni 并进 `./start.sh`，不做 EdgeTTS 自动回退

# 验收示例

- A1：连接后可选音频并上传到 `/humanaudio` 且带本次 `sessionid`；未连接不能上传
- A2：连接后可开始/停止录制（`/record`）并在停止后下载；未连接不能录制
- A3：连接后可提交 audiotype 到 `/set_audiotype` 且带本次 `sessionid`；未连接不能切换
- A4：`README-EN.md` 写明默认 `/app/`、`./start.sh` 与 Omni；中文 README 用户入口含音频/录制/动作；`web/` 无改动

# 约束与不变量

- 工作区：main 当前目录（`isolation: current`）
- 复用现有匿名 `/humanaudio`、`/record`、`/set_audiotype`（与演示台相同）
- 单测不连浏览器、不真录 GPU

# 决策

- 切片：用户首页音频/录制/动作 + README-EN 对齐
- 隔离：当前目录 main
- 控件放进现有连麦监视器，仍是一块框
- 不做参考音频；接口对齐管理员演示台
- README-EN 只对齐入口与工作台说明，不整篇翻译 Features

# 待解决问题

（无）

# 验证预期

- 单测覆盖用户首页源码含上传/录制/动作，未连接禁用；README-EN 含 `/app/`
- `git diff --exit-code -- web/`
