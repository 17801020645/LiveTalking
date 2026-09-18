# 目标

把已上线 Broadcast Gallery 写进 `DESIGN.md`，并给 `/app/` 双角色壳补一层可键盘、可朗读的无障碍基线。视觉世界不换；原站 `web/` 不动。

# 范围

- 按已上线 `.gallery` CSS 重扫 `DESIGN.md`（保留 North Star 与 Named Rules，补齐 token/组件；生成 sidecar）
- `PRODUCT.md`：`/app/` 目标 WCAG 2.2 AA；定价/许可仍未决
- 登录、改密、开户等表单：`label` 与控件关联；错误可被辅助技术读到
- 管理员/用户壳：skip link、主内容地标；管理后台用户表可用键盘选中
- 状态不只靠颜色：tally 旁已有监视器名/文案时保持；选中行除高亮外有可读标记
- 更新 `web-app-shell`

# 非目标

- 不改 Gallery 配色、布局与监视器语言
- 不把 `:root` 浅色遗留写成规范
- 不改 `web/` HTML/JS/CSS，不宣称旧控制台已 AA
- 不宣称 WebRTC 连麦、媒体控件、全站对比度审计已合规
- 不做图+音频克隆、不把 GPU 探活塞进公开 `/healthz`
- 不支付、不自助注册

# 验收示例

- A1：`DESIGN.md` 不再是 seed；颜色/字体/半径与 `.gallery` 已上线 token 一致；sidecar 存在；浅色 `:root` 变量不是规范色
- A2：`PRODUCT.md` 写明 `/app/` 目标 WCAG 2.2 AA；定价/许可仍未决
- A3：登录（含忘记密码）、顶栏改密、管理后台开户的 `label` 关联对应控件；管理员与用户壳有「跳到主内容」
- A4：管理后台用户表可用键盘选中一行；选中态不只有颜色
- A5：`git diff --exit-code -- web/`；监视器框、近黑墙、Indigo 强调仍在

# 约束与不变量

- 工作区：main 当前目录（`isolation: current`）
- 幽灵 `omni-local-tts` 不恢复
- 单测不依赖浏览器/屏幕阅读器；用源码断言 + `web/` 无改动
- 无障碍基线覆盖 `/app/` 壳与登录/Ops 表单，不覆盖每条连麦控件

# 决策

- 切片：10 + 11 同一刀
- 隔离：当前目录 main
- `DESIGN.md`：refresh（从成品扫 token，保留 Overview / Named Rules）
- 无障碍：产品事实是 `/app/` WCAG 2.2 AA 目标，本刀只交壳层基线
- 规范色只取 `.gallery`，不取 `:root` 浅色遗留

# 待解决问题

（无）

# 验证预期

- 单测/源码断言覆盖 DESIGN token、PRODUCT 文案、label/`for`、skip link、用户表键盘选中
- `git diff --exit-code -- web/`
