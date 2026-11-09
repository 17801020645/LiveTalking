# Release Acceptance Matrix

每条只写 `PASS/FAIL + 一条证据`，不贴完整日志。

| 项 | 方法 | 通过标准 |
|---|---|---|
| Pod | `smoke-release.sh <tag>` | live/offline Running/true |
| 镜像 | `smoke-release.sh <tag>` | app/UI 镜像 tag 匹配 |
| 健康 | `/healthz` `/readyz` | 200 |
| 实时 | `/api/live/status` | active 可读写，max=2 |
| 离线 | `/api/offline/health` | worker_alive=true |
| UI 资源 | `/console/` | 能取到 `index-*.js` |
| 工作台 | 浏览器 | 形象列表/预览可见 |
| 视频 | 离线详情/录制 | `readyState=4`，可播放 |
| 移动端 | DOM | scrollWidth == innerWidth |
| 数据 | 只读检查 | 未删 Pod/数据；新产物在 `/data` |

## 报告模板

```text
PASS <item>
evidence: <one line>
blocker: none
next: <one line>
```
