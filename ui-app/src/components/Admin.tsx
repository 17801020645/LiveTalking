import { useEffect, useState } from 'react'
import { api } from '../api'
import type { AdminUser, User } from '../types'
import { Badge, Card } from './ui'

export default function Admin({ user, notify }: { user: User; notify: (s: string) => void }) {
  const [users, setUsers] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(true)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('user')
  const [tenant, setTenant] = useState('default')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function load() {
    setLoading(true)
    try { const r = await api.adminUsers(); setUsers(r.users || []) }
    catch (e: any) { setError(e.message || '加载失败') }
    finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  async function create(e: React.FormEvent) {
    e.preventDefault()
    if (!username.trim() || password.length < 6) return setError('用户名必填，密码至少 6 位')
    setBusy(true); setError('')
    try {
      await api.createUser({ username: username.trim(), password, role, tenant_id: tenant.trim() || 'default' })
      setUsername(''); setPassword(''); setRole('user'); setTenant('default')
      notify('用户/租户已创建'); load()
    } catch (err: any) { setError(err.message || '创建失败') }
    finally { setBusy(false) }
  }

  async function toggle(u: AdminUser) {
    try { await api.setUserEnabled(u.id, u.status !== 'active'); notify('状态已更新'); load() }
    catch (e: any) { notify(`操作失败：${e.message || e}`) }
  }

  async function remove(u: AdminUser) {
    if (!confirm(`删除用户 ${u.username}？`)) return
    try { await api.deleteUser(u.id); notify('用户已删除'); load() }
    catch (e: any) { notify(`删除失败：${e.message || e}`) }
  }

  return (
    <div className="page">
      <div className="page-head"><div><div className="eyebrow">TENANT / 07</div><h1 className="h1">租户与用户</h1><p className="sub">管理员创建用户、分配租户和角色；普通用户只能使用本租户数据。</p></div></div>
      {user.role !== 'admin' ? <div className="empty">仅管理员可访问</div> : (
        <>
          <Card title="新建用户 / TENANT" meta="ADMIN">
            <div className="card-body">
              <form onSubmit={create}>
                <div className="row-2">
                  <div className="field"><label>用户名</label><input value={username} onChange={e => setUsername(e.target.value)} placeholder="tenant_c" /></div>
                  <div className="field"><label>初始密码</label><input type="password" value={password} onChange={e => setPassword(e.target.value)} /></div>
                </div>
                <div className="row-2">
                  <div className="field"><label>租户</label><input value={tenant} onChange={e => setTenant(e.target.value)} placeholder="tenant-c" /></div>
                  <div className="field"><label>角色</label><select value={role} onChange={e => setRole(e.target.value)}><option value="user">普通用户</option><option value="admin">管理员</option></select></div>
                </div>
                {error && <div className="login-error">{error}</div>}
                <button className="btn primary" disabled={busy}>{busy ? '创建中…' : '创建用户'}</button>
              </form>
            </div>
          </Card>
          <Card title="用户列表" meta={`${users.length} USERS`} className="mt-card">
            <div className="card-body tight">
              {loading ? <div className="empty">加载中…</div> : (
                <table className="table">
                  <thead><tr><th>用户</th><th>角色</th><th>租户</th><th>状态</th><th>操作</th></tr></thead>
                  <tbody>
                    {users.map(u => (
                      <tr key={u.id}>
                        <td className="name">{u.username}</td>
                        <td><Badge tone={u.role === 'admin' ? 'run' : 'idle'}>{u.role}</Badge></td>
                        <td className="mono">{u.tenant_id}</td>
                        <td><Badge tone={u.status === 'active' ? 'ok' : 'fail'}>{u.status}</Badge></td>
                        <td>
                          {u.username !== user.username && <>
                            <button className="btn ghost mini-btn" onClick={() => toggle(u)}>{u.status === 'active' ? '禁用' : '启用'}</button>{' '}
                            <button className="btn danger mini-btn" onClick={() => remove(u)}>删除</button>
                          </>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </Card>
        </>
      )}
    </div>
  )
}
