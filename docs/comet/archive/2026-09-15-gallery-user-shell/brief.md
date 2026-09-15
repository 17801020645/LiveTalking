# 目标

把登录页和普通用户壳纳入已有的 Broadcast Gallery 视觉世界：暗墙、细侧栏、带 bezel / tally 的监视器框。能力、文案含义、接口与路由不变。顶栏共享「改密」浮层一并换成同一套材料。

# 范围

- `/app/login`：暗墙上居中一块监视器框，内为用户名、密码、提交
- 用户壳 `/app/user`、`/app/user/assets`、`/app/user/custom`：壳层（侧栏/顶栏）与内容区改为 Gallery；首页保持「一块监视器 + 文字连麦」，不做管理员那种三面墙
- 共享 `PasswordForm`：管理员与用户顶栏的改密浮层都改为 Gallery 语言
- 复用已有 Gallery token（`--wall` / `--bezel` / `--indigo` 等），不另起品牌色
- 更新 `web-app-shell` 正式规格中的登录页与用户壳视觉描述

# 非目标

- 不改管理员工作页内容区（首页预监墙、演示连麦、Avatar、后台、TTS 已是 Gallery）
- 不改原 `web/`，不把麦克风 ASR 迁进 `/app`
- 不把默认入口从 `/` 改到 `/app/`
- 不做支付、自助注册、禁用用户按钮、报表、图+音频自动口型
- 不从成品重扫整份 `DESIGN.md`（本轮只铺页面，不跑 Impeccable document）

# 验收示例

- A1：`/app/login` 是暗墙上的 Gallery 监视器框（可见 tally/bezel），不是浅色玻璃卡；用户名+密码登录、失败统一错误文案、成功按角色跳转仍可用
- A2：用户首页工作区是监视器框；有已发布形象时可连接、看画面、发文字；无发布时引导去资产页，不是浅色 empty 卡
- A3：我的资产为监视器框网格；发布/取消发布仍可用；无订阅时仍是 Gallery 空态
- A4：定制数字人的上传区与订单表是监视器框；提交订单与列表仍可用
- A5：顶栏改密浮层是 Gallery 语言（管理员与用户皆然）；改密接口行为不变
- A6：`web/` 无改动；现有 `/api/v1` 与 WebRTC 行为不因本 change 改变

# 约束与不变量

- 工作区：main 当前目录（`isolation: current`）
- 不改口型模型、用户 `/api/v1/me/offer`、`POST /human`、订单与发布接口
- 视觉世界已确立（Broadcast Gallery），本轮是铺到登录页与用户壳，不另开品牌

# 决策

- 切片：登录页 + 用户壳铺 Gallery；管理员内容区除共享改密浮层外不动
- 隔离：当前目录 main
- 登录页：暗墙上一块居中监视器框装表单，不是只换背景的旧玻璃卡
- 用户首页：一块监视器承接画面与文字发送，不改成三面墙
- 改密：共享组件一起换成 Gallery 语言
- 本轮不跑 Impeccable 概念赛与 `DESIGN.md` document

# 待解决问题

无。用户已确认：登录页与用户壳改成 Gallery 监视器框；登录为暗墙居中一块框；用户首页仍是单框连麦；共享改密浮层一并改；能力与接口不变。

# 验证预期

- 对照 Login / UserLayout / 用户三页 / PasswordForm 是否使用监视器框而不是浅色 `.glass.card` 作为主容器
- 回归现有 platform / user-live / orders 单测
- `git diff --exit-code -- web/`
