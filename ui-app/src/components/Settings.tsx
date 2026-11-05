import { useState } from 'react'
import { api } from '../api'
import type { LiveStatus, User } from '../types'
import { Badge, Card } from './ui'

export default function Settings({ live, user, notify }: { live: LiveStatus; user: User; notify: (s: string) => void }) {
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function changePassword(e: React.FormEvent) {
    e.preventDefault()
    if (next.length < 6) return setError('新密码至少 6 个字符')
    if (next !== confirm) return setError('两次新密码不一致')
    setBusy(true); setError('')
    try {
      await api.changePassword(current, next)
      setCurrent(''); setNext(''); setConfirm('')
      notify('密码已修改，其他会话已退出')
    } catch (err: any) { setError(err.message || '修改失败') }
    finally { setBusy(false) }
  }
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
            <div className="kv"><span>当前用户</span><b>{user.username} · {user.role === 'admin' ? '管理员' : '用户'} · {user.tenant_id || 'default'}</b></div>
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
      <div style={{ marginTop: 14 }}>
        <Card title="修改密码" meta="SECURITY">
          <div className="card-body">
            <form onSubmit={changePassword}>
              <div className="row-2">
                <div className="field"><label>当前密码</label><input type="password" value={current} onChange={e => setCurrent(e.target.value)} autoComplete="current-password" /></div>
                <div className="field"><label>新密码</label><input type="password" value={next} onChange={e => setNext(e.target.value)} autoComplete="new-password" /></div>
              </div>
              <div className="field"><label>确认新密码</label><input type="password" value={confirm} onChange={e => setConfirm(e.target.value)} autoComplete="new-password" /></div>
              {error && <div className="login-error">{error}</div>}
              <button className="btn primary" disabled={busy}>{busy ? '提交中…' : '修改密码'}</button>
            </form>
          </div>
        </Card>
      </div>
    </div>
  )
}
