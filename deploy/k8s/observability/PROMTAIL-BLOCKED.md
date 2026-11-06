# Promtail 状态

- `grafana/promtail:3.2.1` 镜像首次拉取失败（Docker Hub auth EOF），随后成功；
- 当前 Promtail 1/1 Running；
- Kubernetes SD 模式目标为空，已改用单节点静态文件模式：
  `/var/log/pods/*/*/*.log`；
- Loki 已收到日志，label 包含 `filename`、`service_name`、`stream`；
- 查询示例：
  - `{filename=~".*nexus-live.*"}`
  - `{filename=~".*nexus-offline.*"}`
- 后续可恢复 Kubernetes SD 以补充 namespace/pod 标签。
