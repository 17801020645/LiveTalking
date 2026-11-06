# NEXUS 应用 manifests（staging）

**不要直接 apply**：当前宿主机仍占用 GPU（live ~11G + offline ~9G）。先停宿主机应用，再切 k3s。

## 构建

```bash
cd /home/banren45/workspace/01_digital_human/LiveTalking
docker build -f Dockerfile.nexus -t nexus-app:v0.6.0 .
```

把镜像导入 k3s containerd（需要 sudo）：

```bash
docker save nexus-app:v0.6.0 -o /tmp/nexus-app-v0.6.0.tar
sudo k3s ctr images import /tmp/nexus-app-v0.6.0.tar
```

> 也可以用本地 registry；当前先用导入方式。

## 切换

```bash
# 1. 维护窗口：停宿主机
./scripts/stop_all.sh

# 2. 部署（namespace 先建）
kubectl apply -f deploy/k8s/app/namespace.yaml
kubectl apply -k deploy/k8s/app

# 3. 检查
kubectl -n nexus get pods
kubectl -n nexus logs deploy/nexus-live -f

# 4. 访问（自签）
https://192.168.31.75:30810/console/
```

## 回滚

```bash
kubectl -n nexus delete -k deploy/k8s/app
./scripts/start_all.sh
```

## 当前限制

- data/models/certs 用 hostPath，便于首轮演练；后续改 PVC；
- live/offline 共用宿主机 data，SQLite 单写者；
- 无 Ingress，先用 NodePort；
- 镜像内不包含模型/data；
- 需要先停宿主机应用，避免 GPU OOM 和 SQLite 双写。
