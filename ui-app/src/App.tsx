import { useCallback, useEffect, useMemo, useState } from 'react'
import { api, ApiError } from './api'
import type { AvatarInfo, Job, LiveStatus, OfflineHealth, User, VoiceInfo, View } from './types'
import Shell from './components/Shell'
import Overview from './components/Overview'
import Offline from './components/Offline'
import Live from './components/Live'
import Assets from './components/Assets'
import QC from './components/QC'
import Settings from './components/Settings'
import Recordings from './components/Recordings'
import Login from './components/Login'

const emptyLive: LiveStatus = { active: 0, max: 2, sessions: [], gpu: { used_mb: 0, total_mb: 0 } }
const fallbackAvatars: AvatarInfo[] = [{ id: 'avatar_ck', frames: 500, width: 720, height: 1280 }]
const fallbackVoices: VoiceInfo[] = [
  { id: 'zh-CN-XiaoxiaoNeural', name: '晓晓 · 女声', gender: 'female', provider: 'edge' },
  { id: 'zh-CN-YunxiNeural', name: '云希 · 男声', gender: 'male', provider: 'edge' },
]

function readView(): View {
  const h = location.hash.replace('#', '')
  return (['overview', 'offline', 'live', 'assets', 'qc', 'settings'] as View[]).includes(h as View) ? h as View : 'overview'
}

export default function App() {
  const [view, setView] = useState<View>(readView)
  const [live, setLive] = useState<LiveStatus>(emptyLive)
  const [jobs, setJobs] = useState<Job[]>([])
  const [health, setHealth] = useState<OfflineHealth | null>(null)
  const [avatars, setAvatars] = useState<AvatarInfo[]>([])
  const [voices, setVoices] = useState<VoiceInfo[]>([])
  const [bgm, setBgm] = useState<string[]>([])
  const [user, setUser] = useState<User | null>(null)
  const [authChecked, setAuthChecked] = useState(false)
  const [toasts, setToasts] = useState<{ id: number; text: string }[]>([])

  const notify = useCallback((text: string) => {
    const id = Date.now() + Math.random()
    setToasts(t => [...t, { id, text }])
    window.setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3600)
  }, [])

  const load = useCallback(async () => {
    const results = await Promise.allSettled([
      api.liveStatus(), api.jobs(), api.offlineHealth(), api.avatars(), api.voices(), api.bgm(),
    ])
    if (results[0].status === 'fulfilled') setLive(results[0].value)
    if (results[1].status === 'fulfilled') setJobs([...results[1].value].sort((a, b) => b.created_at - a.created_at))
    if (results[2].status === 'fulfilled') setHealth(results[2].value)
    if (results[3].status === 'fulfilled' && results[3].value.length) {
      // wav2lip 形象不能用于 MuseTalk/实时控制台，过滤掉
      setAvatars(results[3].value.filter(a => !a.id.startsWith('wav2lip')))
    }
    if (results[4].status === 'fulfilled' && results[4].value.length) setVoices(results[4].value)
    if (results[5].status === 'fulfilled') setBgm(results[5].value)
    const unauthorized = results.some(r => r.status === 'rejected' && r.reason instanceof ApiError && r.reason.status === 401)
    if (unauthorized) setUser(null)
  }, [])

  useEffect(() => {
    api.me().then(u => { setUser(u); setAuthChecked(true) })
      .catch(() => { setUser(null); setAuthChecked(true) })
  }, [])

  useEffect(() => {
    if (!user) return
    load()
    const id = window.setInterval(load, 3000)
    return () => window.clearInterval(id)
  }, [load, user])

  useEffect(() => {
    const onHash = () => setView(readView())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  const go = useCallback((v: View) => {
    setView(v)
    location.hash = v
    document.querySelector('.content')?.scrollTo({ top: 0 })
  }, [])

  const pendingJobs = useMemo(() => jobs.filter(j => j.status === 'pending' || j.status === 'running').length, [jobs])

  async function logout() {
    try { await api.logout() } catch { /* ignore */ }
    setUser(null)
  }

  if (!authChecked) return <div className="login-page"><div className="login-card"><div className="hint">正在检查登录状态…</div></div></div>
  if (!user) return <Login onSuccess={u => { setUser(u); }} />

  const effectiveAvatars = avatars.length ? avatars : fallbackAvatars
  const effectiveVoices = voices.length ? voices : fallbackVoices

  return (
    <>
      <Shell view={view} onView={go} live={live} jobs={pendingJobs} user={user} onLogout={logout}>
        {view === 'overview' && <Overview live={live} jobs={jobs} avatars={effectiveAvatars} onView={go} />}
        {view === 'offline' && <Offline jobs={jobs} avatars={effectiveAvatars} voices={effectiveVoices} bgm={bgm} refresh={load} notify={notify} />}
        {view === 'live' && <Live live={live} avatars={effectiveAvatars} voices={effectiveVoices} notify={notify} />}
        {view === 'assets' && <Assets avatars={effectiveAvatars} voices={effectiveVoices} bgm={bgm} user={user} live={live} refresh={load} notify={notify} />}
        {view === 'recordings' && <Recordings user={user} notify={notify} />}
        {view === 'qc' && <QC jobs={jobs} />}
        {view === 'settings' && <Settings live={live} />}
        {health && !health.worker_alive && <div className="global-warn">离线 worker 未运行</div>}
      </Shell>
      <div className="toast" aria-live="polite">
        {toasts.map(t => <div key={t.id}>{t.text}</div>)}
      </div>
    </>
  )
}
