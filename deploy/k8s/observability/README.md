# k3s 观测组件

只读/观测类资源，放在 `nexus-monitoring` namespace，不影响应用。

```bash
kubectl apply -k deploy/k8s/observability
kubectl -n nexus-monitoring get pods,svc
```

包含：

- `node-exporter`：DaemonSet，hostNetwork，9100；
- `kube-state-metrics`：K8s 对象/Pod/Deployment/Node 状态；
- `prometheus-agent`：抓取上述指标，remote_write 到 Mac Studio `192.168.31.55:9090`。

验证：

```bash
# Agent 自身
kubectl -n nexus-monitoring logs deploy/prometheus-agent --tail=20

# Mac 上查询
curl -sG --data-urlencode 'query=node_load1' http://localhost:9090/api/v1/query
curl -sG --data-urlencode 'query=count(kube_pod_status_phase{phase="Running"})' http://localhost:9090/api/v1/query
```

限制：

- 当前没有 cAdvisor 容器 CPU/内存明细；
- 当前没有 DCGM GPU 指标；
- Agent remote_write 是明文 HTTP，仅限 LAN；公网需 TLS/认证。
