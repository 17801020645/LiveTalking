# 导入应用镜像到 k3s

镜像已构建在宿主机 Docker：

```
nexus-app:v0.6.1
```

k3s 使用独立 containerd，需要把镜像导入 k3s 的 containerd。

## 一次性手动导入（推荐）

```bash
# 1. 生成 tar（只做一次，约 14G）
docker save nexus-app:v0.6.1 -o /home/banren45/nexus-app-v0.6.1.tar

# 2. 导入 k3s；需要 sudo
sudo k3s ctr images import /home/banren45/nexus-app-v0.6.1.tar

# 3. 验证
sudo k3s ctr images ls | grep nexus-app
```

## 如果希望我代跑导入

不要给完整 sudo，也不要发送密码。只给这一条固定命令的临时权限：

```bash
sudo visudo -f /etc/sudoers.d/nexus-k3s-import
```

内容：

```
Cmnd_Alias NEXUS_K3S_IMPORT = /usr/local/bin/k3s ctr images import /home/banren45/nexus-app-v0.6.1.tar, /usr/local/bin/k3s ctr images ls
banren45 ALL=(root) NOPASSWD: NEXUS_K3S_IMPORT
```

然后：

```bash
sudo chmod 440 /etc/sudoers.d/nexus-k3s-import
sudo -n k3s ctr images ls
```

导入完成后删除该文件：

```bash
sudo rm /etc/sudoers.d/nexus-k3s-import
```

> 注意：`/home/banren45/nexus-app-v0.6.1.tar` 是用户可写文件，固定命令授权只能临时使用；导入完成立即删除 sudoers 文件。

## 导入后

```bash
kubectl -n nexus create secret generic nexus-env --from-env-file=.env
./scripts/stop_all.sh
kubectl apply -f deploy/k8s/app/namespace.yaml
kubectl apply -k deploy/k8s/app
```

访问：

```
https://192.168.31.75:30810/console/
```

回滚：

```bash
kubectl -n nexus delete -k deploy/k8s/app
./scripts/start_all.sh
```
