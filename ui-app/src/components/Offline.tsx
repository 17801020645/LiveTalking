import { useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api'
import type { AvatarInfo, Job, VoiceInfo } from '../types'
import { AvatarImg, parseQc, qcText, timeAgo } from './Overview'
import { Badge, Card, Progress, qcTone, statusTone } from './ui'

type Filter = 'all' | 'running' | 'done' | 'failed'

export default function Offline({ jobs, avatars, voices, bgm, refresh, notify }: {
  jobs: Job[]; avatars: AvatarInfo[]; voices: VoiceInfo[]; bgm: string[];
  refresh: () => void; notify: (s: string) => void
}) {
  const [text, setText] = useState('大家好，我是数字人小陈。今天用一分钟，带你看懂我们的新产品。')
  const [avatar, setAvatar] = useState('')
  const [voice, setVoice] = useState('')
  const [subtitle, setSubtitle] = useState(true)
  const [cover, setCover] = useState(true)
  const [bgmValue, setBgmValue] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [filter, setFilter] = useState<Filter>('all')
  const [selected, setSelected] = useState<Job | null>(null)
  const [batching, setBatching] = useState(false)
  const batchRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    if (!avatar && avatars[0]) setAvatar(avatars[0].id)
    if (!voice && voices[0]) setVoice(voices[0].id)
  }, [avatars, voices, avatar, voice])

  const filtered = useMemo(() => jobs.filter(j => {
    if (filter === 'all') return true
    if (filter === 'running') return j.status === 'running' || j.status === 'pending'
    if (filter === 'done') return j.status === 'success'
    return j.status === 'failed'
  }), [jobs, filter])

  async function submit() {
    if (!text.trim()) return notify('请先输入文案')
    if (!avatar || !voice) return notify('形象/音色尚未加载')
    setSubmitting(true)
    try {
      const { id } = await api.createJob({
        text: text.trim(), avatar_id: avatar, voice,
        subtitle, cover, bgm: bgmValue,
      })
      notify(`任务已提交：${id.slice(0, 8)}…`)
      refresh()
    } catch (e: any) {
      notify(`提交失败：${e.message || e}`)
    } finally {
      setSubmitting(false)
    }
  }

  async function importBatch(file: File) {
    if (!avatar || !voice) return notify('形象/音色尚未加载')
    const raw = await file.text()
    const lines = raw.split(/\r?\n/).map(line => {
      // CSV：取第一列；跳过表头/空行
      const first = line.split(',')[0].trim().replace(/^"|"$/g, '')
      return first
    }).filter(line => line && !/^(text|文案|content)$/i.test(line))
    if (!lines.length) return notify('文件里没有可导入的文案')
    if (lines.length > 50 && !window.confirm(`共 ${lines.length} 条，确认批量提交？`)) return
    setBatching(true)
    let ok = 0
    for (const line of lines) {
      try {
        await api.createJob({ text: line, avatar_id: avatar, voice, subtitle, cover, bgm: bgmValue })
        ok++
      } catch { /* count */ }
    }
    setBatching(false)
    notify(`批量导入完成：${ok}/${lines.length}`)
    refresh()
  }

  async function retry(id: string) {
    try { await api.retryJob(id); notify('已重新入队'); refresh() }
    catch (e: any) { notify(`重试失败：${e.message || e}`) }
  }

  return (
    <div className="page">
      <div className="page-head">
        <div><div className="eyebrow">OFFLINE PIPELINE / 01</div><h1 className="h1">离线任务</h1><p className="sub">文案进入队列，按实时空闲情况自动让路；完成后可下载视频、封面与字幕。</p></div>
        <div className="hero-actions">
          <input ref={batchRef} type="file" accept=".txt,.csv" hidden onChange={e => { const f=e.target.files?.[0]; if (f) importBatch(f); e.currentTarget.value='' }} />
          <button className="btn" disabled={batching} onClick={() => batchRef.current?.click()}>{batching ? '导入中…' : '⇪ 批量导入'}</button>
        </div>
      </div>

      <div className="offline-grid">
        <Card title="新建任务 / COMPOSE" meta="EDGETTS · MUSETALK">
          <div className="card-body">
            <div className="field"><label>文案</label><textarea value={text} onChange={e => setText(e.target.value)} placeholder="输入要播报的文案…" /><div className="hint">支持 10–20000 字；长文案自动按 10 秒分段。</div></div>
            <div className="row-2">
              <div className="field"><label>形象</label><select value={avatar} onChange={e => setAvatar(e.target.value)}>{avatars.map(a => <option key={a.id} value={a.id}>{a.id} · {a.width}×{a.height}</option>)}</select></div>
              <div className="field"><label>音色</label><select value={voice} onChange={e => setVoice(e.target.value)}>{voices.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}</select></div>
            </div>
            <div className="field"><label>包装</label><div className="check-row">
              <label className="check"><input type="checkbox" checked={subtitle} onChange={e => setSubtitle(e.target.checked)} /> 烧录字幕</label>
              <label className="check"><input type="checkbox" checked={cover} onChange={e => setCover(e.target.checked)} /> 生成封面</label>
            </div></div>
            <div className="field"><label>背景音乐</label><select value={bgmValue} onChange={e => setBgmValue(e.target.value)}><option value="">无 BGM</option>{bgm.map(b => <option key={b} value={b}>{b}</option>)}</select></div>
            <div className="composer-foot">
              <span className="hint">提交后进入队列；实时忙时显示“等待实时空闲”。</span>
              <button className="btn ghost" disabled={submitting} onClick={() => notify('模板功能 v2 再做')}>存为模板</button>
              <button className="btn primary" disabled={submitting} onClick={submit}>{submitting ? '提交中…' : '提交任务 →'}</button>
            </div>
          </div>
        </Card>

        <Card>
          <div className="tabs">
            {([['all', '全部'], ['running', '进行中'], ['done', '已完成'], ['failed', '失败']] as [Filter, string][]).map(([k, label]) => (
              <button key={k} className={filter === k ? 'active' : ''} onClick={() => setFilter(k)}>{label} {k === 'all' ? jobs.length : k === 'running' ? jobs.filter(j => j.status === 'running' || j.status === 'pending').length : k === 'done' ? jobs.filter(j => j.status === 'success').length : jobs.filter(j => j.status === 'failed').length}</button>
            ))}
          </div>
          <div className="card-body tight">
            {filtered.length === 0 ? <div className="empty">该筛选下暂无任务</div> : (
              <table className="table">
                <thead><tr><th>任务</th><th>形象</th><th>进度</th><th>状态</th><th>QC</th></tr></thead>
                <tbody>
                  {filtered.map(job => (
                    <tr key={job.id} className="task-row" onClick={() => setSelected(job)}>
                      <td><div className="title"><span className="avatar-dot" /><span className="name">{job.text.slice(0, 16) || '(无文案)'}</span></div><div className="mono">{timeAgo(job.created_at)} · {job.id.slice(0, 6)}</div></td>
                      <td className="mono">{job.avatar_id}</td>
                      <td><Progress value={job.progress} wait={job.stage === 'waiting_live'} /></td>
                      <td>{job.stage === 'waiting_live' ? <Badge tone="wait">等待实时空闲</Badge> : <Badge tone={statusTone(job.status)}>{job.status === 'success' ? '完成' : job.status === 'failed' ? '失败' : job.status === 'running' ? '渲染中' : '排队中'}</Badge>}</td>
                      <td><Badge tone={qcTone(job.qc_status)}>{qcText(job)}</Badge></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </Card>
      </div>

      {selected && (
        <>
          <div className="drawer-mask show" onClick={() => setSelected(null)} />
          <aside className="drawer show" aria-label="任务详情">
            <button className="close" onClick={() => setSelected(null)} aria-label="关闭">×</button>
            <div className="eyebrow">JOB DETAIL</div>
            <h3>{selected.text.slice(0, 24) || '未命名任务'}</h3>
            <p className="sub">{selected.avatar_id} · {selected.voice} · {selected.id.slice(0, 8)}</p>
            <div className="section"><h4>状态</h4><p><Badge tone={selected.stage === 'waiting_live' ? 'wait' : statusTone(selected.status)}>{selected.stage === 'waiting_live' ? '等待实时空闲' : selected.status}</Badge> <span className="hint">{selected.progress}%</span></p>{selected.error && <p className="bad-text">{selected.error}</p>}</div>
            <div className="section"><h4>包装</h4><div className="kv"><span>字幕</span><b>{selected.subtitle ? '已开启' : '关闭'}</b></div><div className="kv"><span>封面</span><b>{selected.cover ? '已生成' : '关闭'}</b></div><div className="kv"><span>BGM</span><b>{selected.bgm || '无'}</b></div></div>
            <div className="section"><h4>质检</h4>{(() => {
              const qc = parseQc(selected)
              if (!qc) return <p className="hint">尚未质检</p>
              return <>
                <div className="kv"><span>人脸丢失</span><b>{qc.face_missing_ratio ?? '—'}</b></div>
                <div className="kv"><span>黑帧</span><b>{qc.black_ratio ?? '—'}</b></div>
                <div className="kv"><span>闪烁</span><b>{qc.flicker_ratio ?? '—'}</b></div>
                <div className="kv"><span>SyncNet</span><b>{typeof qc.syncnet === 'object' && qc.syncnet ? `${qc.syncnet.confidence ?? '—'} / ${qc.syncnet.av_offset ?? '—'}` : '—'}</b></div>
              </>
            })()}</div>
            <div className="section"><h4>操作</h4><div className="drawer-actions">
              {selected.status === 'success' && <a className="btn primary" href={`/api/offline/jobs/${selected.id}/download`}>下载视频</a>}
              {selected.status === 'success' && <a className="btn" href={`/api/offline/jobs/${selected.id}/cover`}>封面</a>}
              {selected.srt_path && <a className="btn" href={`/api/offline/jobs/${selected.id}/subtitle`}>字幕</a>}
              {(selected.status === 'failed' || selected.status === 'success') && <button className="btn" onClick={() => { retry(selected.id); setSelected(null) }}>重试</button>}
              <button className="btn ghost" onClick={() => setSelected(null)}>关闭</button>
            </div></div>
          </aside>
        </>
      )}
    </div>
  )
}
