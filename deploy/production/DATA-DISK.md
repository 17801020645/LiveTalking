# /data 新盘与运行时迁移

## 已完成

- 新盘 `/dev/nvme1n1`：ZHITAI TiPlus7100s 2TB；
- GPT + 单分区 + ext4，label `nexus-data`；
- 挂载 `/data`，`noatime`，UUID 写入 `/etc/fstab`；
- `fstrim.timer` enabled；
- 目录：

```
/data/
├── docker/      # 待迁 Docker data-root
├── k3s/         # 待迁 k3s data-dir
├── models/      # 已复制 weights，4G
├── apps/digital-human/{data,config,logs}
├── media/
├── registry/
├── cache/
└── backups/
```

- 数字人静态数据已复制到 `/data/apps/digital-human/data`（4G，暂未切换）；
- 当前应用仍使用原 `/home/.../LiveTalking/data` 和 `/var/lib/rancher/k3s`；
- 未删除任何原数据。

## 迁移脚本

```bash
sudo bash scripts/setup-data-migration.sh --dry-run

# 首次
sudo bash scripts/setup-data-migration.sh --docker
sudo bash scripts/setup-data-migration.sh --k3s

# 如果上一次中断、/data/docker 或 /data/k3s 已有部分拷贝
sudo bash scripts/setup-data-migration.sh --docker-resume
sudo bash scripts/setup-data-migration.sh --k3s-resume
```

- `--docker`：停 Docker → rsync `/var/lib/docker` → `/data/docker` → 改 data-root → 启 Docker；
- `--k3s`：停 k3s → rsync `/var/lib/rancher/k3s` → `/data/k3s` → 加 `data-dir` → 启 k3s；
- **旧目录保留**，不删除；
- `--k3s` 会短暂停应用（8010/30810），请在无实时会话/无离线任务时执行。

## 数字人数据切换（后续）

1. 确认 k3s 数据迁移成功；
2. 停 `nexus-live` / `nexus-offline`（scale 0 或删除，删除类操作需确认）；
3. 用 SQLite backup 复制 `platform.db` 和 `jobs.db`；
4. 修改 `deploy/k8s/app/live.yaml` / `offline.yaml` hostPath 到：
   - `/data/apps/digital-human/data`
   - `/data/models/weights`
5. apply，验收；
6. 旧数据保留，确认后再删。

## 回滚

- Docker：恢复 `/etc/docker/daemon.json.bak.*`，启 Docker；旧 `/var/lib/docker` 仍在；
- k3s：恢复 `/etc/rancher/k3s/config.yaml.bak.*`，启 k3s；旧 `/var/lib/rancher/k3s` 仍在。
