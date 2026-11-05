import { useState } from 'react'
import { api } from '../api'
import type { AvatarInfo, AvatarTask, LiveStatus, User, VoiceInfo } from '../types'
import { Badge, Card } from './ui'

export default function Assets({ avatars, voices, bgm, user, live, refresh, notify }: {
  avatars: AvatarInfo[]; voices: VoiceInfo[]; bgm: string[]; user: User; live: LiveStatus;
  refresh: () => void; notify: (s: string) => void
}) {
  const [uploading, setUploading] = useState(false)
  const [avatarId, setAvatarId] = useState('avatar_v' + new Date().toISOString().slice(5, 10).replace('-', ''))
  const [file, setFile] = useState<File | null>(null)
  const [task, setTask] = useState<AvatarTask | null>(null)
  const [error, setError] = useState('')

  async function startUpload() {
    if (!file) return setError('请选择视频文件')
    if (!avatarId.trim()) return setError('请填写 avatar_id')
    if (live.active > 0) return setError('请先结束实时会话，避免显存不足')
    setUploading(true); setError(''); setTask(null)
    try {
      try { await api.unloadOffline() } catch { /* offline worker may be idle */ }
      const { task_id } = await api.createAvatarTask(avatarId.trim(), file)
      notify('形象生成任务已提交')
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
          </div>
        </div>
      )}
      <div className="asset-grid">
        {avatars.map(a => (
          <div className="card asset" key={a.id}>
            <div className="cover"><img src={api.avatarFrame(a.id)} alt={a.id} onError={e => { (e.currentTarget as HTMLImageElement).style.display = 'none' }} /></div>
            <h4>{a.id}</h4><p>{a.width}×{a.height} · {a.frames} frames</p>
            <div className="foot"><Badge tone="ok">可用</Badge><span className="hint" style={{ marginLeft: 'auto' }}>MuseTalk</span></div>
          </div>
        ))}
        <div className="card asset"><div className="cover placeholder">1080P / TODO</div><h4>avatar_v1</h4><p>1080×1920 · 待拍摄</p><div className="foot"><Badge tone="wait">待补素材</Badge><span className="hint" style={{ marginLeft: 'auto' }}>iPhone 4K</span></div></div>
      </div>
      <div className="grid-3" style={{ marginTop: 14 }}>
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
    </div>
  )
}
