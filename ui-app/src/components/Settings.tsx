import type { LiveStatus } from '../types'
import { Badge, Card } from './ui'

export default function Settings({ live }: { live: LiveStatus }) {
  return (
    <div className="page">
      <div className="page-head"><div><div className="eyebrow">SYSTEM / 05</div><h1 className="h1">系统设置</h1><p className="sub">当前为 POC 单机配置；生产化后会拆成控制面与 GPU 池。</p></div></div>
      <div className="settings-grid">
        <Card title="运行配置" meta="READ ONLY">
          <div className="card-body">
            <div className="kv"><span>实时端口</span><b>8010 / HTTPS</b></div>
            <div className="kv"><span>离线端口</span><b>8012 / HTTP</b></div>
            <div className="kv"><span>实时上限</span><b>{live.max} 路</b></div>
            <div className="kv"><span>离线分段</span><b>10s</b></div>
            <div className="kv"><span>实时空闲防抖</span><b>15s</b></div>
            <div className="kv"><span>GPU</span><b>{((live.gpu.used_mb || 0) / 1024).toFixed(1)} / {((live.gpu.total_mb || 0) / 1024).toFixed(1)} GB</b></div>
          </div>
        </Card>
        <Card title="已知限制" meta="POC v0.1.0">
          <div className="card-body list">
            <div className="list-row"><b>1080p 素材</b><Badge tone="wait">待拍</Badge></div>
            <div className="list-row"><b>公网 / TURN</b><Badge tone="idle">后续</Badge></div>
            <div className="list-row"><b>登录 / 租户</b><Badge tone="idle">未接</Badge></div>
            <div className="list-row"><b>多 GPU / 集群</b><Badge tone="idle">未接</Badge></div>
            <div className="list-row"><b>UI</b><Badge tone="run">v0.1</Badge></div>
          </div>
        </Card>
      </div>
    </div>
  )
}
