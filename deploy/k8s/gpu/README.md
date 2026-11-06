# NVIDIA device plugin time-slicing

当前集群已配置：GPU allocatable 从 1 变为 2。

## 配置

```bash
kubectl apply -f deploy/k8s/gpu/time-slicing-config.yaml
kubectl -n kube-system patch ds nvidia-device-plugin-daemonset --type=json -p='[
  {"op":"add","path":"/spec/template/spec/containers/0/args","value":["--config-file=/etc/nvidia/config.yaml"]},
  {"op":"add","path":"/spec/template/spec/containers/0/volumeMounts/-","value":{"name":"config","mountPath":"/etc/nvidia/config.yaml","subPath":"config.yaml","readOnly":true}},
  {"op":"add","path":"/spec/template/spec/volumes/-","value":{"name":"config","configMap":{"name":"nvidia-device-plugin-config"}}}
]'
```

> 不要把整个目录挂到 `/etc/nvidia`。NVIDIA runtime hook 需要在 `/etc/nvidia` 下创建 application profiles，只读目录会导致 `RunContainerError`；必须用 `subPath` 只挂配置文件。

## 验证

```bash
kubectl get nodes -o jsonpath='{.items[0].status.allocatable.nvidia\.com/gpu}{"\n"}'
# 2
```

两个 GPU Pod 可同时 Running（测试已做，随后删除）。

## 约束

- time-slicing 不是显存隔离；
- live+offline 合计约 20G，24G 卡只剩约 4G；
- 不能跑第三个重 GPU 任务。

## 回滚

原始 DaemonSet YAML 备份：

```bash
ls data/backups/nvidia-device-plugin-original-20261106.yaml
kubectl replace -f data/backups/nvidia-device-plugin-original-20261106.yaml
```
