# NEXUS 生产化基线

当前机器是 **LAN POC**。本目录提供从 nohup 脚本迁移到可运维服务的最小基线，但**不自动把服务暴露到公网**。

## 1. 生产前必须做

1. 复制 `.env.production.example` 为 `.env`，填真实密钥；
2. 改掉 POC 默认密码：
   ```bash
   .venv/bin/python scripts/set_admin_password.py
   ```
   不设置 `NEXUS_ADMIN_PASSWORD` 时会生成随机密码，只打印一次；
3. 确认 `certs/lan.crt` / `lan.key` 仍有效；LAN 可继续用自签，公网必须换正式证书；
4. 只在 LAN 访问时保持 `TRUST_PROXY=0`、`PROD_HSTS=0`。

## 2. systemd 托管（需要 sudo）

```bash
sudo deploy/production/install.sh
systemctl status nexus-live nexus-offline nexus-backup.timer
journalctl -u nexus-live -f
```

- `nexus-live`：8010，WebRTC + UI；
- `nexus-offline`：127.0.0.1:8012，渲染 worker；
- `nexus-backup.timer`：每天 03:30 备份 SQLite 和配置，保留 7 天；
- 安装脚本会先停掉 legacy nohup 进程，再启动 systemd。

## 3. 健康检查

```bash
scripts/healthcheck.sh
curl -k https://127.0.0.1:8010/healthz
curl -k https://127.0.0.1:8010/readyz
```

- `/healthz`：进程/DB 存活；
- `/readyz`：platform DB 已初始化；
- 8012 `/healthz` 只绑定 localhost。

## 4. 备份

```bash
scripts/backup.sh
```

输出到 `data/backups/<timestamp>/`：

- `platform.db`（用户/租户/会话）；
- `jobs.db`（离线任务）；
- `config.yaml`、`requirements.txt`；
- `manifest.json`。

默认保留 7 天，`BACKUP_RETENTION_DAYS` 可调。**不备份 `.env` 密钥**，密钥请放独立密码管理器。

## 5. 公网访问（下一阶段）

当前没有公网入口，不要直接把 8010 映射到公网。需要：

1. 域名 + 正式 TLS（Caddy/Nginx 终止 TLS）；
2. Caddy 反代到 `https://127.0.0.1:8010`（自签上游需 `tls_insecure_skip_verify`）；
3. 设 `TRUST_PROXY=1`、`NEXUS_COOKIE_SECURE=1`、`PROD_HSTS=1`；
4. 为 WebRTC 配 TURN（UDP/TCP 3478、TLS 5349），否则跨 NAT 无法稳定；
5. 防火墙只放 80/443 和 TURN 端口，8010/8012 不暴露；
6. 接入监控/告警、日志轮转、备份异地化。

Caddy 模板见 `Caddyfile.example`。

## 6. 安全基线

- 登录失败 5 次/5 分钟 → 封 5 分钟（可调）；
- 同源 POST 校验；
- CSP、X-Frame-Options、nosniff、Referrer-Policy、Permissions-Policy；
- Cookie `HttpOnly`，HTTPS 下 `Secure`；
- API 不缓存；
- 8012 仅 localhost；
- 默认密码必须修改后才能公网。
