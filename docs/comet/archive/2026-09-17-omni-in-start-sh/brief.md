# 目标

`./start.sh` 一次拉起本机 Omni（8091）再拉起数字人（8010）。仍是两个进程。`./start-omni.sh` 保留，用于单独起 Omni 或换模型。

# 范围

- `./start.sh`：8091 尚未就绪时后台调用 `./start-omni.sh`，等到 `/v1/audio/voices` 成功或超时后再起 8010
- 8091 已在听则不再起第二个 Omni
- Omni 环境缺失、启动失败或超时：打印明确错误，仍起 8010（不自动改 EdgeTTS）
- 本脚本拉起的 Omni 子进程：Ctrl+C 停 8010 时一并停掉；事先已在跑的 Omni 不动
- `SKIP_OMNI=1` 可跳过拉起 Omni
- 更新 `omni-tts-serving`、壳层 README 一句、`README.md` / `README-EN.md` / `docs/omni_tts.md`

# 非目标

- 不把 vLLM 装进数字人 `.venv`，不内嵌 Omni
- 不做 EdgeTTS 自动回退，不改默认检查点，不部署 1.7B-Base
- 不改 `/healthz`，不改 `web/`
- 不恢复幽灵 change `omni-local-tts`

# 验收示例

- A1：`start.sh` 在 8091 未就绪时会调用 `start-omni.sh`；8091 已响应 `/v1/audio/voices` 时不再拉起第二个；`SKIP_OMNI=1` 不调用 `start-omni.sh`
- A2：Omni 环境缺失或启动失败时 `start.sh` 仍会启动 `app.py`（8010），并打出可观察的错误；不把 `tts` 改成 `edgetts`
- A3：`README.md` / `README-EN.md` / `docs/omni_tts.md` 写明 `./start.sh` 会先起 Omni 再起数字人；换模型仍用 `./start-omni.sh`
- A4：原 `web/` 无改动；`start-omni.sh` 默认模型与双进程边界不变

# 约束与不变量

- 工作区：main 当前目录（`isolation: current`）
- 单测不连真实 8091、不真正拉起 vLLM
- 等待 `/v1/audio/voices` 有超时；超时后仍起 8010

# 决策

- 切片：把 Omni 并进 `./start.sh`
- 隔离：当前目录 main
- 已在听则跳过；失败/超时仍起 8010
- 本脚本拉起的 Omni 随 Ctrl+C 一起停；事先已运行的不杀
- `./start-omni.sh` 保留

# 待解决问题

（无）

# 验证预期

- 单测覆盖脚本分支（调用 start-omni、跳过、SKIP_OMNI、失败仍起 app.py）与 README 文案
- `git diff --exit-code -- web/`
