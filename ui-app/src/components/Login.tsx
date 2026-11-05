import { useState } from 'react'
import { api } from '../api'
import type { User } from '../types'

export default function Login({ onSuccess }: { onSuccess: (u: User) => void }) {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      await api.login(username.trim(), password)
      const me = await api.me()
      onSuccess(me)
    } catch (err: any) {
      setError(err.message || '登录失败')
    } finally { setBusy(false) }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="brand login-brand"><div className="brand-mark">◈</div><div><b>NEXUS</b><small>AVATAR OPS</small></div></div>
        <div className="eyebrow" style={{ marginTop: 24 }}>SECURE ACCESS / POC</div>
        <h1 className="h1">登录控制台</h1>
        <p className="sub">管理员可管理任务、形象和录制；普通用户可使用离线任务与实时会话。</p>
        <form onSubmit={submit} className="login-form">
          <div className="field"><label>用户名</label><input value={username} onChange={e => setUsername(e.target.value)} autoComplete="username" /></div>
          <div className="field"><label>密码</label><input type="password" value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" autoFocus /></div>
          {error && <div className="login-error">{error}</div>}
          <button className="btn primary login-submit" disabled={busy}>{busy ? '登录中…' : '登录 →'}</button>
        </form>
        <div className="hint" style={{ marginTop: 14 }}>POC 默认账号见部署文档；登录后通过 cookie 访问同源 API。</div>
      </div>
    </div>
  )
}
