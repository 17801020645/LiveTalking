import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import type { AvatarInfo, AvatarTask, LiveStatus, User, VoiceInfo } from '../types'
import { Badge, Card } from './ui'

export default function Assets({ avatars, voices, bgm, user, live, refresh, notify, onOpenAvatar }: {
  avatars: AvatarInfo[]; voices: VoiceInfo[]; bgm: string[]; user: User; live: LiveStatus;
  refresh: () => void; notify: (s: string) => void; onOpenAvatar?: (id: string) => void
}) {
  const [uploading, setUploading] = useState(false)
  const [avatarId, setAvatarId] = useState('avatar_v' + new Date().toISOString().slice(5, 10).replace('-', ''))
  const [file, setFile] = useState<File | null>(null)
  const [task, setTask] = useState<AvatarTask | null>(null)
  const [tasks, setTasks] = useState<AvatarTask[]>([])
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(18)

  const sorted = useMemo(
    () => [...avatars].sort((a, b) => Number(!!b.active) - Number(!!a.active) || a.id.localeCompare(b.id)),
    [avatars],
  )
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return q ? sorted.filter(a => a.id.toLowerCase().includes(q)) : sorted
  }, [sorted, query])
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize))
  useEffect(() => { setPage(1) }, [query, pageSize])
  useEffect(() => { setPage(p => Math.min(p, totalPages)) }, [totalPages])
  const pageItems = filtered.slice((page - 1) * pageSize, page * pageSize)

  async function loadTasks() {
    if (user.role !== 'admin') return
    try { const r = await api.avatarTasks(); setTasks(r.tasks || []) } catch { /* ignore */ }
  }
  useEffect(() => { loadTasks() }, [user.role])

  async function cancelTask(id: string) {
    try { await api.cancelAvatarTask(id); notify('已取消排队任务'); loadTasks() }
    catch (e: any) { notify(`取消失败：${e.message || e}`) }
  }

  async function startUpload() {
    if (!file) return setError('请选择视频文件')
    if (!avatarId.trim()) return setError('请填写 avatar_id')
    if (live.active > 0) return setError('请先结束实时会话，避免显存不足')
    setUploading(true); setError(''); setTask(null)
    try {
      try { await api.unloadOffline() } catch { /* offline worker may be idle */ }
      const { task_id } = await api.createAvatarTask(avatarId.trim(), file)
      notify('形象生成任务已提交'); loadTasks()
      const timer = window.setInterval(async () => {
        try {
          const t = await api.avatarTask(task_id)
          setTask(t)
          if (t.status === 'completed') {
            window.clearInterval(timer); setUploading(false); notify('形象生成完成'); refresh()
          } else if (t.status === 'failed') {
            window.clearInterval(timer); setUploading(false); setError(t.error_msg || '生成失败')
          }
        } catch (e: any) {
          window.clearInterval(timer); setUploading(false); setError(e.message || '查询失败')
        }
      }, 3000)
    } catch (e: any) {
      setUploading(false); setError(e.message || String(e))
    }
  }
  return (
    <div className="page">
      <div className="page-head"><div><div className="eyebrow">ASSETS / 03</div><h1 className="h1">资产库</h1><p className="sub">形象、音色与包装素材。管理员可上传视频并生成 MuseTalk 形象。</p></div><div className="hero-actions">{user.role === 'admin' && <button className="btn primary" onClick={() => setError('')} disabled={uploading}>⇪ 上传形象</button>}</div></div>
      {user.role === 'admin' && (
        <div className="card upload-panel">
          <div className="card-head"><h3>生成形象 / UPLOAD</h3><span className="meta">MUSETALK · ADMIN</span></div>
          <div className="card-body">
            <div className="row-2">
              <div className="field"><label>avatar_id</label><input value={avatarId} onChange={e => setAvatarId(e.target.value)} placeholder="avatar_v1" /></div>
              <div className="field"><label>视频（建议 30–60s，4K/1080p）</label><input type="file" accept="video/*" onChange={e => setFile(e.target.files?.[0] || null)} /></div>
            </div>
            <div className="composer-foot">
              <span className="hint">生成前会卸载离线模型；实时会话需为 0。耗时取决于视频长度。</span>
              <button className="btn primary" onClick={startUpload} disabled={uploading}>{uploading ? '生成中…' : '开始生成'}</button>
            </div>
            {error && <div className="login-error" style={{ marginTop: 10 }}>{error}</div>}
            {task && <div className="hint" style={{ marginTop: 10 }}>任务 {task.task_id.slice(0, 8)}… · {task.status} · {task.progress}%</div>}
            {tasks.length > 0 && (
              <table className="table" style={{ marginTop: 12 }}>
                <thead><tr><th>任务</th><th>形象</th><th>状态</th><th>进度</th><th>操作</th></tr></thead>
                <tbody>
                  {tasks.slice(0, 6).map(t => (
                    <tr key={t.task_id}>
                      <td className="mono">{t.task_id.slice(0, 8)}…</td>
                      <td className="mono">{t.avatar_id}</td>
                      <td><span className="badge b-idle">{t.status}</span></td>
                      <td className="mono">{t.progress}%</td>
                      <td>{(t.status === 'pending' || t.status === 'running') && <button className="btn danger mini-btn" onClick={() => cancelTask(t.task_id)}>{t.status === 'running' ? '请求取消' : '取消'}</button>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
      <div className="grid-3" style={{ marginTop: 0, marginBottom: 14 }}>
        <Card title="音色 / VOICES" meta="EDGETTS">
          <div className="card-body">
            {voices.map(v => <div className="voice-row" key={v.id}><b>{v.name}</b><Badge tone="ok">可用</Badge><span className="mono">{v.id}</span></div>)}
            <div className="voice-row"><b>CosyVoice2 · 克隆</b><Badge tone="wait">未接</Badge><span className="mono">P4 / 需 GPU</span></div>
          </div>
        </Card>
        <Card title="包装 / PACKS" meta="BGM · 字幕">
          <div className="card-body list">
            {bgm.map(b => <div className="list-row" key={b}><b>{b}</b><Badge tone="idle">BGM</Badge><span className="mono">12%</span></div>)}
            {!bgm.length && <div className="list-row"><span className="hint">data/bgm 下暂无音乐</span></div>}
            <div className="list-row"><b>默认字幕样式</b><Badge tone="ok">Noto CJK</Badge><span className="mono">44px</span></div>
            <div className="list-row"><b>封面模板 · 标题</b><Badge tone="ok">第一句</Badge><span className="mono">JPG</span></div>
          </div>
        </Card>
      </div>

      <div className="asset-toolbar">
        <div className="asset-search">
          <span aria-hidden="true">⌕</span>
          <input value={query} onChange={e => setQuery(e.target.value)} placeholder="搜索形象 ID…" aria-label="搜索形象" />
        </div>
        <span className="asset-count">{filtered.length} 个形象{query ? ` · 匹配“${query}”` : ''}</span>
        <label className="asset-page-size">每页
          <select value={pageSize} onChange={e => setPageSize(Number(e.target.value))} aria-label="每页数量">
            <option value={12}>12</option><option value={18}>18</option><option value={24}>24</option><option value={48}>48</option>
          </select>
        </label>
      </div>

      <div className="asset-grid">
        {pageItems.map(a => (
          <div className="card asset" key={a.id}>
            <div className="cover"><img src={api.avatarFrame(a.id)} alt={a.id} loading="lazy" onError={e => { (e.currentTarget as HTMLImageElement).style.display = 'none' }} /></div>
            <h4 title={a.id}>{a.id}</h4><p>{a.width}×{a.height} · {a.frames} 帧</p>
            <div className="foot"><Badge tone="ok">可用</Badge><button className="btn ghost mini-btn" style={{ marginLeft: 'auto' }} onClick={() => onOpenAvatar?.(a.id)}>工作台 →</button></div>
          </div>
        ))}
        {!filtered.length && <div className="empty asset-empty">没有匹配的形象</div>}
      </div>

      <div className="asset-pager">
        <button className="btn ghost mini-btn" disabled={page <= 1} onClick={() => setPage(p => Math.max(1, p - 1))}>‹ 上一页</button>
        <span className="hint">第 {page} / {totalPages} 页 · 共 {filtered.length} 个</span>
        <button className="btn ghost mini-btn" disabled={page >= totalPages} onClick={() => setPage(p => Math.min(totalPages, p + 1))}>下一页 ›</button>
      </div>
    </div>
  )
}
