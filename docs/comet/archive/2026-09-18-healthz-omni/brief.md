# 目标

`GET /healthz` 仍证明 8010 进程与数据库可用，同时报告本机 Omni（8091）是否可达。8091 挂了不得把 8010 判死。

# 范围

- `GET /healthz` 仍公开。数据库可用时 HTTP 始终 200，`ok` 为 true
- 响应增加布尔字段 `omni`：短超时请求配置的 TTS 上游 `GET /v1/audio/voices`
- 上游解析与管理员 TTS 代理相同：`LIVETALKING_TTS_UPSTREAM` 优先，否则 `TTS_SERVER`，再否则 `http://127.0.0.1:8091`
- 更新 `ops-hardening`、`omni-tts-serving`：探活会看 8091，仍不探 GPU

# 非目标

- 不探测 GPU，不改 EdgeTTS 回退，不改默认检查点
- 不改 `./start.sh`、不内嵌 Omni
- 不改 `web/` HTML/JS/CSS
- 不收紧匿名信令，不实现忘记密码
- 不恢复幽灵 change `omni-local-tts`

# 验收示例

- A1：数据库可用时，无论 Omni 是否可达，未登录 `GET /healthz` 均为 HTTP 200 且 `ok` 为 true
- A2：假上游响应 `/v1/audio/voices` 时 `omni` 为 true；指到不可达地址时 `omni` 为 false；响应不含密钥、口令、会话 Cookie、上游堆栈
- A3：原 `web/` 无改动；不探测 GPU

# 约束与不变量

- 工作区：main 当前目录（`isolation: current`）
- 单测不连真实 8091、不探测 GPU
- 探活超时须短，避免把 `/healthz` 拖成慢请求
- 数据库不可用时仍为非 200，行为与现规格一致

# 决策

- 切片：healthz 探 8091，匿名信令与忘记密码留给后续 change
- 隔离：当前目录 main
- 8091 不可达：仍 200，`omni: false`（与 `./start.sh` 失败仍起 8010 一致，避免探活把数字人进程杀掉）
- `omni` 为布尔；成功标准为上游 `/v1/audio/voices` HTTP 2xx
- 不把音色列表或内部错误写进 healthz

# 待解决问题

（无）

# 验证预期

- 单测覆盖：假上游可达时 `omni: true`、不可达时 `omni: false` 且仍 200、未登录可访问、正文无密钥
- `git diff --exit-code -- web/`
