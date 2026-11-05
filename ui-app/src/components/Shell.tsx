import type { LiveStatus, User, View } from '../types'

const nav: { id: View; label: string; icon: string; tag?: string }[] = [
  { id: 'overview', label: '总览', icon: '◫' },
  { id: 'offline', label: '离线任务', icon: '▤' },
  { id: 'live', label: '实时会话', icon: '◉' },
  { id: 'assets', label: '资产库', icon: '◇' },
  { id: 'recordings', label: '录制库', icon: '▣' },
  { id: 'qc', label: '质检中心', icon: '◈' },
]

export default function Shell({ view, onView, live, jobs, user, onLogout, children }: {
  view: View; onView: (v: View) => void; live: LiveStatus; jobs: number; user: User; onLogout: () => void; children: React.ReactNode
}) {
  const titles: Record<View, string> = {
    overview: '总览', offline: '离线任务', live: '实时会话', assets: '资产库', recordings: '录制库', qc: '质检中心', settings: '系统设置',
  }
  const gpuPct = live.gpu.total_mb ? Math.round((live.gpu.used_mb / live.gpu.total_mb) * 100) : 0
  const gpuGb = (live.gpu.used_mb / 1024).toFixed(1)
  const totalGb = (live.gpu.total_mb / 1024).toFixed(1)

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">◈</div>
          <div><b>NEXUS</b><small>AVATAR OPS</small></div>
        </div>
        <nav className="nav" aria-label="主导航">
          <div className="nav-label">WORKSPACE / 01</div>
          {nav.map(item => (
            <button key={item.id} className={view === item.id ? 'active' : ''} onClick={() => onView(item.id)}>
              <span className="ico">{item.icon}</span><span>{item.label}</span>
              {item.id === 'offline' && jobs > 0 && <span className="tag">{jobs}</span>}
              {item.id === 'live' && live.active > 0 && <span className="tag">{live.active}</span>}
            </button>
          ))}
          <div className="nav-label" style={{ marginTop: 16 }}>SYSTEM / 02</div>
          <button className={view === 'settings' ? 'active' : ''} onClick={() => onView('settings')}>
            <span className="ico">⚙</span><span>系统设置</span>
          </button>
        </nav>
        <div className="sidebar-foot">
          <div className="foot-row"><span>POC BUILD</span><b>v0.1.0</b></div>
          <div className="foot-row"><span>GPU VRAM</span><b>{gpuGb} / {totalGb}G</b></div>
          <div className="mini"><i style={{ width: `${gpuPct}%` }} /></div>
          <div className="foot-row"><span>MODE</span><b className="lime">LAN / PRIORITY</b></div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="crumb">控制台 / <b>{titles[view]}</b></div>
          <div className="top-status">
            <div className="pill"><span className={`dot ${live.active ? '' : 'dim'}`} />LIVE <b>{live.active} / {live.max}</b></div>
            <div className="pill"><span className="dot cyan" />GPU <b>{gpuPct}%</b></div>
            <div className="pill"><span className="dot amber" />QUEUE <b>{jobs}</b></div>
          </div>
          <div className="operator">
            <div className="avatar-me">{user.username.slice(0, 1).toUpperCase()}</div>
            <span>{user.role === 'admin' ? '管理员' : '用户'} · {user.username}</span>
            <button className="btn ghost mini-btn" onClick={onLogout}>退出</button>
          </div>
        </header>
        <div className="content">{children}</div>
      </main>
    </div>
  )
}
