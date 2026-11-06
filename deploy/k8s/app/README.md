# NEXUS 应用 manifests

## 当前状态

应用已从宿主机 nohup 切换到 k3s：

- `nexus-live`：1/1 Running，GPU 1，hostPort 8010 + NodePort 30810；
- `nexus-offline`：1/1 Running，GPU 1，ClusterIP 8012；
- GPU：time-slicing 2 份，live+offline 约 20.3G / 24G；
- 入口：`https://192.168.31.75:8010/console/` 或 `:30810`；
- 验收：2 路实时、离线任务、App `/metrics` 已通过。

## 镜像

```
nexus-app:v0.6.1
```

镜像已构建并导入 k3s。当前镜像里少了 `tts/` 和 `web/`，因此 live Pod 用 hostPath 临时挂载：

- `tts/`
- `web/`
- `ui_dist/`（包含默认形象改为 `avatar_ck` 的前端）

下一版镜像应把 `tts/`、`web/` 打进镜像，移除这三个 hostPath。

## 部署

```bash
# 镜像已导入；如果换镜像才需要重新导入
kubectl -n nexus create secret generic nexus-env --from-env-file=.env

kubectl apply -f deploy/k8s/app/namespace.yaml
kubectl apply -k deploy/k8s/app
kubectl -n nexus get pods
```

## 验收

```bash
kubectl -n nexus get pods
curl -sk https://127.0.0.1:8010/healthz
curl -sk https://127.0.0.1:30810/console/
```

浏览器：

```
https://192.168.31.75:8010/console/
```

## 回滚（需要确认；当前不执行）

回滚会删除 k3s 应用/停止 Pod，属于删除类操作，执行前确认：

```bash
kubectl -n nexus scale deploy/nexus-live --replicas=0
kubectl -n nexus scale deploy/nexus-offline --replicas=0
# 或 kubectl -n nexus delete -k deploy/k8s/app
./scripts/start_all.sh
```

> 不要在当前 k3s 应用运行时直接 `start_all.sh`，会与 hostPort 8010 / GPU 冲突。

## 仍待做

- 镜像 v0.6.2：把 tts/web 打进镜像，去掉 hostPath；
- data/models/certs 从 hostPath 迁 PVC；
- 录制/形象生成在 k3s 下验收；
- 回滚演练（删除类，需确认）。
