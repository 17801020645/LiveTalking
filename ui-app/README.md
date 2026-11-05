# NEXUS UI v0.1（React）

> 正式前端实现，替代 `ui/` 单文件原型。数据来自现有 8010/8012 API。

## 开发

```bash
cd ui-app
npm install --cache ../../.npm-cache
npm run dev -- --host 0.0.0.0
```

Vite 代理默认指向 `192.168.31.75` 的 8010/8012；换机器改 `vite.config.ts` 的 proxy target。

## 构建 / 部署

```bash
npm run build
# 构建产物在 dist/，部署到 LiveTalking worktree 的 ui_dist/
rsync -a dist/ user@host:/path/to/LiveTalking/.worktrees/ui-v1/ui_dist/
```

生产访问：

```
https://<host>:8010/console/
```

- `base` 必须是 `/console/`；
- UI、实时信令、离线 API 同源；
- `/api/offline/*` 由 LiveTalking 进程反向代理到 8012；
- `/api/assets/*` 由 LiveTalking 进程读取 `data/avatars`；
- `/api/live/close` 用于显式关闭 WebRTC 会话（浏览器关闭时用 sendBeacon）。

## 页面

- 总览：实时/GPU/队列/QC
- 离线任务：提交、筛选、进度、下载/重试、详情
- 实时会话：WebRTC、文本、按住说话、打断、结束
- 资产库：形象/音色/BGM
- 质检中心
- 系统设置

## 已知

- 批量导入、上传形象、登录/租户 v2；
- 录制 v2；
- 第 3 路只提示，不排队；
- 自签证书需浏览器信任，麦克风才可用。
