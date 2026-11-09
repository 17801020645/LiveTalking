import { useEffect, useMemo, useState } from 'react'
import type { AvatarInfo, Job, LiveStatus, User, VoiceInfo, View } from '../types'
import { AvatarImg, qcText, timeAgo } from './Overview'
import { Badge, Card, qcTone } from './ui'
import { defaultAvatarKey, readDefaultAvatarId } from '../defaults'

function read(key: string): string {
  try { return localStorage.getItem(key) || '' } catch { return '' }
}
function write(key: string, value: string) {
  try { localStorage.setItem(key, value) } catch { /* private mode */ }
}

export default function Workbench({ avatarId, avatars, jobs, voices, live, user, onOpenAvatar, onPresent, onLive, onOffline, onView, notify }: {
  avatarId?: string
  avatars: AvatarInfo[]
  jobs: Job[]
  voices: VoiceInfo[]
  live: LiveStatus
  user: User
  onOpenAvatar: (id: string) => void
  onPresent: (id: string) => void
  onLive: (id: string) => void
  onOffline: (id: string) => void
  onView: (v: View) => void
  notify: (s: string) => void
}) {
  const tenant = user.tenant_id || 'default'
  const defaultKey = defaultAvatarKey(user)
  const aliasKey = (id: string) => `nexus.avatarAlias.${tenant}.${user.username}.${id}`
  const voiceKey = (id: string) => `nexus.avatarVoice.${tenant}.${user.username}.${id}`

  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'default' | 'ready'>('all')
  const [selectedId, setSelectedId] = useState(avatarId || '')
  const [defaultId, setDefaultId] = useState(() => read(defaultKey))
  const [aliases, setAliases] = useState<Record<string, string>>({})
  const [voiceMap, setVoiceMap] = useState<Record<string, string>>({})

  useEffect(() => {
    if (avatarId && avatars.some(a => a.id === avatarId)) setSelectedId(avatarId)
  }, [avatarId, avatars])

  useEffect(() => {
    const nextAliases: Record<string, string> = {}
    const nextVoices: Record<string, string> = {}
    for (const a of avatars) {
      nextAliases[a.id] = read(aliasKey(a.id))
      nextVoices[a.id] = read(voiceKey(a.id))
    }
    setAliases(nextAliases)
    setVoiceMap(nextVoices)
  }, [avatars, tenant, user.username])

  const effectiveDefault = readDefaultAvatarId(user, avatars) || defaultId
  const selected = avatars.find(a => a.id === (selectedId || effectiveDefault)) || avatars[0]
  const selectedJobs = useMemo(
    () => selected ? jobs.filter(j => j.avatar_id === selected.id).sort((a, b) => b.created_at - a.created_at) : [],
    [jobs, selected],
  )
  const latestJob = selectedJobs[0]
  const qcJobs = selectedJobs.filter(j => j.qc_status)
  const latestQc = qcJobs[0]
  const voice = selected ? (voiceMap[selected.id] || voices[0]?.id || '') : ''

  const filtered = useMemo(() => avatars.filter(a => {
    const label = (aliases[a.id] || a.id).toLowerCase()
    if (search && !label.includes(search.toLowerCase()) && !a.id.toLowerCase().includes(search.toLowerCase())) return false
    if (filter === 'default') return a.id === effectiveDefault
    if (filter === 'ready') return a.frames > 0 && a.width > 0
    return true
  }), [avatars, aliases, search, filter, effectiveDefault])

  function select(id: string) {
    setSelectedId(id)
    onOpenAvatar(id)
  }

  function editAlias() {
    if (!selected) return
    const current = aliases[selected.id] || selected.id
    const next = window.prompt('显示名称（仅当前账号本地保存，不改服务端 ID）', current)
    if (next === null) return
    const clean = next.trim()
    write(aliasKey(selected.id), clean)
    setAliases(m => ({ ...m, [selected.id]: clean }))
    notify(clean ? '显示名称已保存' : '已恢复默认名称')
  }

  function makeDefault() {
    if (!selected) return
    write(defaultKey, selected.id)
    setDefaultId(selected.id)
    notify(`已设为当前账号的本机默认形象：${selected.id}`)
  }

  function removeAvatar() {
    if (!selected) return
    if (!window.confirm(`形象 ${selected.id} 的删除需要后端管理 API。\n\n当前版本不会删除任何文件或服务端数据，是否查看说明？`)) return
    notify('当前后端未提供形象删除接口；未删除任何文件')
  }

  function setVoice(v: string) {
    if (!selected) return
    write(voiceKey(selected.id), v)
    setVoiceMap(m => ({ ...m, [selected.id]: v }))
  }

  const status = latestQc ? qcText(latestQc) : '待检'

  return (
    <div className="page workbench-page">
      <div className="page-head">
        <div>
          <div className="eyebrow">AVATAR WORKBENCH / 00</div>
          <h1 className="h1">数字人工作台</h1>
          <p className="sub">选择一个形象，查看状态与上下文，然后直接开始对话或创建离线视频。</p>
        </div>
        <div className="hero-actions">
          <button className="btn" onClick={() => onView('assets')}>◇ 资产库</button>
          <button className="btn primary" onClick={() => selected && onPresent(selected.id)} disabled={!selected}>◉ 开始对话</button>
        </div>
      </div>

      <div className="workbench-grid">
        <Card className="wb-list" title="形象 / AVATARS" meta={`${avatars.length} TOTAL`} actions={<button className="btn ghost mini-btn" onClick={() => onView('assets')}>＋ 新建</button>}>
          <div className="wb-tools">
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="搜索形象或别名…" aria-label="搜索形象" />
            <select value={filter} onChange={e => setFilter(e.target.value as typeof filter)} aria-label="筛选形象">
              <option value="all">全部</option>
              <option value="ready">可用</option>
              <option value="default">默认</option>
            </select>
          </div>
          <div className="wb-avatar-list">
            {filtered.map(a => {
              const isSelected = selected?.id === a.id
              const isDefault = a.id === effectiveDefault
              const latest = jobs.find(j => j.avatar_id === a.id)
              return (
                <button key={a.id} className={`wb-avatar-row ${isSelected ? 'active' : ''}`} onClick={() => select(a.id)} aria-pressed={isSelected}>
                  <span className="wb-thumb"><AvatarImg id={a.id} alt={aliases[a.id] || a.id} /></span>
                  <span className="wb-avatar-copy">
                    <b>{aliases[a.id] || a.id}</b>
                    <small>{a.width}×{a.height} · {Math.round(a.frames / 25)}s</small>
                  </span>
                  <span className="wb-avatar-state">
                    {isDefault ? <Badge tone="ok">默认</Badge> : latest?.status === 'failed' ? <Badge tone="fail">异常</Badge> : <Badge tone="idle">可用</Badge>}
                  </span>
                </button>
              )
            })}
            {!filtered.length && <div className="empty">没有匹配的形象</div>}
          </div>
          <div className="wb-list-foot"><span className="hint">普通用户仅显示本租户可用形象</span><span className="mono">{user.role === 'admin' ? 'ADMIN' : 'USER'}</span></div>
        </Card>

        {selected ? (
          <div className="wb-center">
            <Card className="wb-preview-card" title="形象预览 / PREVIEW" meta={`${selected.id} · ${selected.frames} FRAMES`} actions={<Badge tone={selected.id === effectiveDefault ? 'ok' : 'idle'}>{selected.id === effectiveDefault ? 'DEFAULT' : 'READY'}</Badge>}>
              <div className="wb-stage">
                <AvatarImg id={selected.id} alt={aliases[selected.id] || selected.id} />
                <div className="wb-stage-vignette" />
                <div className="wb-stage-top"><Badge tone="live">● MUSE TALK</Badge><Badge tone="idle">{selected.width}×{selected.height}</Badge></div>
                <div className="wb-stage-bottom">
                  <div><strong>{aliases[selected.id] || selected.id}</strong><span>{Math.round(selected.frames / 25)} 秒素材 · {selected.frames} 帧</span></div>
                  <span className="mono">{selected.id === effectiveDefault ? 'DEFAULT AVATAR' : 'AVAILABLE'}</span>
                </div>
              </div>
              <div className="wb-primary-actions">
                <button className="btn primary" onClick={() => onPresent(selected.id)}>◉ 开始实时对话</button>
                <button className="btn" onClick={() => onOffline(selected.id)}>▤ 创建离线视频</button>
                <button className="btn ghost" onClick={() => onView('recordings')}>▣ 查看录制</button>
                <button className="btn ghost" onClick={() => onView('qc')}>◈ 查看质检</button>
              </div>
            </Card>
            <div className="wb-metrics">
              <div className="wb-metric"><span>实时状态</span><b>{live.active > 0 ? `${live.active} 路进行中` : '空闲'}</b><small>最多 {live.max} 路</small></div>
              <div className="wb-metric"><span>历史项目</span><b>{selectedJobs.length}</b><small>离线任务</small></div>
              <div className="wb-metric"><span>质检记录</span><b>{qcJobs.length}</b><small>{latestQc ? `最近 ${timeAgo(latestQc.created_at)}` : '尚未质检'}</small></div>
            </div>
          </div>
        ) : <Card><div className="empty">暂无形象，请先在资产库创建数字人。</div></Card>}

        {selected && (
          <Card className="wb-detail" title="属性 / CONTEXT" meta="AVATAR">
            <div className="wb-detail-head">
              <div className="wb-detail-avatar"><AvatarImg id={selected.id} alt="" /></div>
              <div><h3>{aliases[selected.id] || selected.id}</h3><p className="mono">{selected.id}</p></div>
            </div>
            <div className="wb-detail-section">
              <h4>状态</h4>
              <div className="kv"><span>形象状态</span><b><Badge tone={selected.frames > 0 ? 'ok' : 'wait'}>{selected.frames > 0 ? '可用' : '素材异常'}</Badge></b></div>
              <div className="kv"><span>分辨率</span><b>{selected.width} × {selected.height}</b></div>
              <div className="kv"><span>源视频</span><b>MuseTalk 烘焙帧</b></div>
              <div className="kv"><span>时长 / 帧数</span><b>{Math.round(selected.frames / 25)}s · {selected.frames}</b></div>
              <div className="kv"><span>默认形象</span><b>{selected.id === effectiveDefault ? '是' : '否'}</b></div>
            </div>
            <div className="wb-detail-section">
              <h4>校正 / 质检</h4>
              <div className="kv"><span>最近质检</span><b><Badge tone={qcTone(latestQc?.qc_status)}>{status}</Badge></b></div>
              <div className="kv"><span>最近任务</span><b>{latestJob ? timeAgo(latestJob.created_at) : '—'}</b></div>
              <button className="btn ghost mini-btn wb-wide" onClick={() => onView('qc')}>打开质检中心 →</button>
            </div>
            <div className="wb-detail-section">
              <h4>智能体 / 音色</h4>
              <div className="field"><label>默认音色</label><select value={voice} onChange={e => setVoice(e.target.value)}>{voices.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}</select></div>
              <p className="hint">音色偏好保存在当前浏览器，进入实时或离线时继续使用该形象。</p>
            </div>
            <div className="wb-detail-actions">
              <button className="btn" onClick={() => onLive(selected.id)}>打开运营台</button>
              <button className="btn" onClick={makeDefault} disabled={selected.id === effectiveDefault}>{selected.id === effectiveDefault ? '已是默认' : '设为默认'}</button>
              <button className="btn ghost" onClick={editAlias}>编辑名称</button>
              <button className="btn danger" onClick={removeAvatar}>删除…</button>
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}
