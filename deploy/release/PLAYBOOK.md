# Release Playbook · 三会话 + 一次构建

适用范围：`nexus-app` / `nexus-ui` 的 UI 与发布。发布是**可回退的滚动更新**，不是数据操作。

## 0. 角色与会话

| 会话 | 只做什么 | 输入 | 输出 |
|---|---|---|---|
| 开发会话 | 改 UI、`npm run build`、本地/hostPath 验证 | 需求 | 代码、截图、handoff |
| 发布会话 | 构建、导入、apply、smoke | handoff + tag | 镜像 tar、SMOKE PASS |
| 验收会话 | 只读 API/CLI，必要时浏览器 | ACCEPTANCE + tag | PASS/FAIL + 证据 |

不要把开发聊天全量带入发布会话。发布会话只读 `HANDOFF-TEMPLATE.md` 填好的结论稿。

## 1. 开发阶段：不构建镜像

- 只改 `ui-app/src`；
- `npm run build` + `tsc -b`；
- 用 Vite 或 `ui_dist` hostPath 看效果；
- 不重复 `docker build`、不重复导入 4.6G 镜像；
- 视觉证据最多一张桌面 + 一张移动端；无视觉变化时只用 DOM/overflow 指标。

## 2. 冻结与 handoff

开发完成后填 `deploy/release/HANDOFF-TEMPLATE.md`，最多 80 行：

- 目标 tag；
- 改动文件；
- 已跑验证；
- 已知限制；
- 需要用户执行的 import 命令。

## 3. 发布阶段：一次构建

```bash
cd /home/banren45/workspace/01_digital_human/LiveTalking
./scripts/release-image.sh v0.6.7 all tar
```

输出只有一行 JSON，包含 UI/APP 镜像和 tar。

用户执行：

```bash
sudo k3s ctr images import /home/banren45/nexus-ui-v0.6.7.tar
sudo k3s ctr images import /home/banren45/nexus-app-v0.6.7.tar
```

然后：

```bash
./scripts/apply-release.sh v0.6.7
./scripts/smoke-release.sh v0.6.7
```

`smoke-release.sh` 只输出 PASS/FAIL 摘要，不打印完整日志。

## 4. 验收阶段

先 API/CLI，再浏览器：

1. `scripts/smoke-release.sh <tag>`
2. 工作台/离线/录制只做结构性检查；
3. 仅在视觉变更时截图；
4. 数字人聊天验收只发一条短消息；ASR/TTS/渲染不消耗 LLM token。

## 5. UI / 模型镜像分离

- `nexus-app`：后端 + 模型运行时，不再包含 `ui_dist`；
- `nexus-ui`：仅 `nginx:alpine` + `ui_dist`，几十 MB；
- live Pod 的 `ui-assets` initContainer 把 UI 复制到 emptyDir，主容器挂载 `/app/ui_dist`；
- 只改 UI 时：`release-image.sh <tag> ui tar`，不需要重建 14GB app 镜像；
- 只改后端/模型时：`release-image.sh <tag> all no`。

## 6. 禁止 / 停止条件

- 不 `helm uninstall`、不删除 PVC/数据、不手动删 Pod；
- 不用 `kubectl delete` 清理失败 Pod，交给 owner 确认；
- 导入失败或新 Pod 不 Ready：停止，不 apply 下一版；
- 保留上一版镜像和 tar，回滚只切 tag。

## 7. Token 预算

- 每条命令 ≤20 行 / 2KB；
- 轮询在脚本内，打印最终摘要；
- 无视觉变化不截图；
- 发布/验收会话不携带整段开发历史；
- 应用 LLM 只有数字人聊天才消耗；部署、ASR、TTS、渲染、录制不消耗。
