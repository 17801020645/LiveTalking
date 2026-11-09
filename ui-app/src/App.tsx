import { useCallback, useEffect, useMemo, useState } from 'react'
import { api, ApiError } from './api'
import type { AvatarInfo, Job, LiveStatus, OfflineHealth, Route, User, VoiceInfo, View } from './types'
import Shell from './components/Shell'
import Overview from './components/Overview'
import Offline from './components/Offline'
import Live from './components/Live'
import Assets from './components/Assets'
import QC from './components/QC'
import Settings from './components/Settings'
import Recordings from './components/Recordings'
import Admin from './components/Admin'
import Login from './components/Login'
import Workbench from './components/Workbench'
import Capabilities from './components/Capabilities'
import Present from './components/Present'
import { readDefaultAvatarId } from './defaults'

const emptyLive: LiveStatus = { active: 0, max: 2, sessions: [], gpu: { used_mb: 0, total_mb: 0 } }
const fallbackAvatars: AvatarInfo[] = [{ id: 'avatar_ck', frames: 500, width: 720, height: 1280 }]
const fallbackVoices: VoiceInfo[] = [
  { id: 'zh-CN-XiaoxiaoNeural', name: '晓晓 · 女声', gender: 'female', provider: 'edge' },
  { id: 'zh-CN-YunxiNeural', name: '云希 · 男声', gender: 'male', provider: 'edge' },
]

const allowedViews: View[] = ['overview', 'workbench', 'capabilities', 'offline', 'live', 'present', 'assets', 'recordings', 'qc', 'admin', 'settings']

function readRoute(): Route {
  const raw = location.hash.replace(/^#/, '')
  const [head, param] = raw.split('/')
  const view = (allowedViews.includes(head as View) ? head : 'overview') as View
  let avatarId: string | undefined
  try { avatarId = param ? decodeURIComponent(param) : undefined } catch { avatarId = param || undefined }
  return { view, avatarId }
}

export default function App() {
  const [route, setRoute] = useState<Route>(readRoute)
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
      setAvatars(results[3].value.filter(a => !a.id.startsWith('wav2lip') && a.id !== '111111'))
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
    const onHash = () => setRoute(readRoute())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  const go = useCallback((v: View, avatarId?: string) => {
    const next = { view: v, avatarId }
    setRoute(next)
    location.hash = `${v}${avatarId ? `/${encodeURIComponent(avatarId)}` : ''}`
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
  const defaultAvatarId = readDefaultAvatarId(user, effectiveAvatars)
  const openLive = (avatarId?: string) => go('live', avatarId)
  const openPresent = (avatarId?: string) => go('present', avatarId)
  const openOffline = (avatarId?: string) => go('offline', avatarId)

  if (route.view === 'present') {
    return (
      <>
        <Present avatarId={route.avatarId} defaultAvatarId={defaultAvatarId} avatars={effectiveAvatars} voices={effectiveVoices} live={live} notify={notify} onExit={() => go('workbench', route.avatarId)} />
        <div className="toast" aria-live="polite">{toasts.map(t => <div key={t.id}>{t.text}</div>)}</div>
      </>
    )
  }

  return (
    <>
      <Shell view={route.view} onView={(v) => go(v)} live={live} jobs={pendingJobs} user={user} onLogout={logout}>
        {route.view === 'overview' && <Overview live={live} jobs={jobs} avatars={effectiveAvatars} onView={go} />}
        {route.view === 'workbench' && <Workbench avatarId={route.avatarId} avatars={effectiveAvatars} jobs={jobs} voices={effectiveVoices} live={live} user={user} onOpenAvatar={(id) => go('workbench', id)} onPresent={openPresent} onLive={openLive} onOffline={openOffline} onView={go} notify={notify} />}
        {route.view === 'capabilities' && <Capabilities avatars={effectiveAvatars} jobs={jobs} onWorkbench={(id) => go('workbench', id)} onOffline={(id) => go('offline', id)} onAssets={() => go('assets')} onView={go} />}
        {route.view === 'offline' && <Offline initialAvatarId={route.avatarId} defaultAvatarId={defaultAvatarId} jobs={jobs} avatars={effectiveAvatars} voices={effectiveVoices} bgm={bgm} refresh={load} notify={notify} />}
        {route.view === 'live' && <Live initialAvatarId={route.avatarId} defaultAvatarId={defaultAvatarId} live={live} avatars={effectiveAvatars} voices={effectiveVoices} notify={notify} />}
        {route.view === 'assets' && <Assets avatars={effectiveAvatars} voices={effectiveVoices} bgm={bgm} user={user} live={live} refresh={load} notify={notify} onOpenAvatar={(id) => go('workbench', id)} />}
        {route.view === 'recordings' && <Recordings user={user} notify={notify} />}
        {route.view === 'admin' && <Admin user={user} notify={notify} />}
        {route.view === 'qc' && <QC jobs={jobs} />}
        {route.view === 'settings' && <Settings live={live} user={user} notify={notify} />}
        {health && !health.worker_alive && <div className="global-warn">离线 worker 未运行</div>}
      </Shell>
      <div className="toast" aria-live="polite">
        {toasts.map(t => <div key={t.id}>{t.text}</div>)}
      </div>
    </>
  )
}
