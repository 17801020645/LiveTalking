import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from './api'
import type { AvatarInfo, Job, LiveStatus, OfflineHealth, VoiceInfo, View } from './types'
import Shell from './components/Shell'
import Overview from './components/Overview'
import Offline from './components/Offline'
import Live from './components/Live'
import Assets from './components/Assets'
import QC from './components/QC'
import Settings from './components/Settings'

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
  }, [])

  useEffect(() => {
    load()
    const id = window.setInterval(load, 3000)
    return () => window.clearInterval(id)
  }, [load])

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

  const effectiveAvatars = avatars.length ? avatars : fallbackAvatars
  const effectiveVoices = voices.length ? voices : fallbackVoices
  const pendingJobs = useMemo(() => jobs.filter(j => j.status === 'pending' || j.status === 'running').length, [jobs])

  return (
    <>
      <Shell view={view} onView={go} live={live} jobs={pendingJobs}>
        {view === 'overview' && <Overview live={live} jobs={jobs} avatars={effectiveAvatars} onView={go} />}
        {view === 'offline' && <Offline jobs={jobs} avatars={effectiveAvatars} voices={effectiveVoices} bgm={bgm} refresh={load} notify={notify} />}
        {view === 'live' && <Live live={live} avatars={effectiveAvatars} voices={effectiveVoices} notify={notify} />}
        {view === 'assets' && <Assets avatars={effectiveAvatars} voices={effectiveVoices} bgm={bgm} notify={notify} />}
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
