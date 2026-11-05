import { api } from '../api'
import type { AvatarInfo, Job, LiveStatus, QcResult, View } from '../types'
import { Badge, Card, Progress, qcTone, statusTone } from './ui'

export function AvatarImg({ id, alt = '' }: { id: string; alt?: string }) {
  return <img src={api.avatarFrame(id)} alt={alt} loading="lazy" onError={e => { (e.currentTarget as HTMLImageElement).style.display = 'none' }} />
}

export function parseQc(job: Job): QcResult | null {
  if (!job.qc_json) return null
  try { return JSON.parse(job.qc_json) as QcResult } catch { return null }
}

export function qcText(job: Job): string {
  const qc = parseQc(job)
  if (!qc) return '待检'
  if (qc.status === 'pass') return 'pass'
  if (qc.status === 'warn') return 'warn'
  if (qc.status === 'fail') return 'fail'
  return qc.status || '待检'
}

export function timeAgo(ts: number): string {
  if (!ts) return '—'
  const d = Math.floor(Date.now() / 1000 - ts)
  if (d < 60) return '刚刚'
  if (d < 3600) return `${Math.floor(d / 60)} 分钟前`
  return new Date(ts * 1000).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

export default function Overview({ live, jobs, avatars, onView }: {
  live: LiveStatus; jobs: Job[]; avatars: AvatarInfo[]; onView: (v: View) => void
}) {
  const gpuPct = live.gpu.total_mb ? Math.round((live.gpu.used_mb / live.gpu.total_mb) * 100) : 0
  const usedGb = (live.gpu.used_mb / 1024).toFixed(1)
  const running = jobs.filter(j => j.status === 'running').length
  const waiting = jobs.filter(j => j.stage === 'waiting_live').length
  const success = jobs.filter(j => j.status === 'success').length
  const pass = jobs.filter(j => j.qc_status === 'pass').length
  const qcTotal = jobs.filter(j => j.qc_status).length
  const passRate = qcTotal ? Math.round((pass / qcTotal) * 100) : 0
  const avatar = avatars[0]?.id || 'avatar_ck'
  const liveJobs = jobs.filter(j => j.status === 'success').slice(0, 3)
  const qcJobs = jobs.filter(j => j.qc_status).slice(0, 4)

  return (
    <div className="page">
      <div className="hero">
        <div>
          <div className="eyebrow">REALTIME + OFFLINE / SINGLE NODE</div>
          <h1 className="h1">数字人运行中枢</h1>
          <p className="sub">实时会话、离线队列与 GPU 资源在同一个控制面里。实时优先，离线在 10 秒分段边界让路。</p>
        </div>
        <div className="hero-actions">
          <button className="btn" onClick={() => onView('live')}>◉ 启动实时会话</button>
          <button className="btn primary" onClick={() => onView('offline')}>＋ 新建离线任务</button>
        </div>
      </div>

      <div className="kpis">
        <div className="card kpi"><div className="label">LIVE SESSIONS</div><div className="value">{live.active} <small>/ {live.max}</small></div><div className="delta"><b>● {live.active ? '运行中' : '空闲'}</b> · 25 FPS</div></div>
        <div className="card kpi"><div className="label">GPU MEMORY</div><div className="value">{usedGb} <small>GB</small></div><div className="delta"><i>{gpuPct}%</i> · 余量 {((live.gpu.total_mb - live.gpu.used_mb) / 1024).toFixed(1)}G</div></div>
        <div className="card kpi"><div className="label">OFFLINE QUEUE</div><div className="value">{jobs.length} <small>jobs</small></div><div className="delta"><b>{running} 进行中</b> · {waiting} 等待实时</div></div>
        <div className="card kpi"><div className="label">QC PASS RATE</div><div className="value">{passRate}<small>%</small></div><div className="delta"><b>{pass}/{qcTotal || 0} 已检</b> · 最近 24h</div></div>
      </div>

      <div className="split">
        <Card title="实时会话 / LIVE OPS" meta="WS · 25 FPS" actions={<button className="btn ghost mini-btn" onClick={() => onView('live')}>进入控制台 →</button>}>
          <div className="card-body sessions">
            {live.sessions.length === 0 && (
              <div className="empty">暂无实时会话。最多支持 {live.max} 路，第 {live.max + 1} 路会明确提示已满。</div>
            )}
            {live.sessions.map((s, i) => (
              <div className="session" key={s.id}>
                <div className="thumb"><AvatarImg id={avatar} alt="" /><span className="live-badge">{i === 0 ? 'LIVE' : 'LIVE'}</span></div>
                <div>
                  <h4>{i === 0 ? '客服 · 小陈' : '讲解员 · 小陈'}</h4>
                  <p>{s.id.slice(0, 8)}… · {i === 0 ? '文本 + EdgeTTS' : '按住说话 / SenseVoice'}</p>
                  <div className="metrics"><span>状态 <b>{s.state || 'active'}</b></span><span>GPU <b>{usedGb}G</b></span></div>
                </div>
                <div className="wave" aria-hidden="true"><i /><i /><i /><i /><i /></div>
              </div>
            ))}
            <div className="list-row no-border">
              <Badge tone="wait">第 {live.max + 1} 路排队</Badge>
              <span className="hint">达到 {live.max} 路上限；第 {live.max + 1} 个连接会收到明确的“已满”提示。</span>
            </div>
          </div>
        </Card>

        <Card title="GPU / 资源" meta="RTX 4090 · 24G">
          <div className="card-body gpu-wrap">
            <div className="donut" style={{ background: `conic-gradient(var(--cyan) 0 ${Math.min(gpuPct, 60)}%, var(--violet) ${Math.min(gpuPct, 60)}% ${gpuPct}%, rgba(148,163,184,.14) ${gpuPct}% 100%)` }} role="img" aria-label={`GPU 显存使用 ${gpuPct}%`}>
              <div className="center"><b>{gpuPct}%</b><span>VRAM</span></div>
            </div>
            <div className="legend">
              <div><i />实时 + 离线 <b>{usedGb}G</b></div>
              <div><i />空闲 <b>{((live.gpu.total_mb - live.gpu.used_mb) / 1024).toFixed(1)}G</b></div>
              <div style={{ color: 'var(--dim)', fontSize: 10, lineHeight: 1.5, marginTop: 3 }}>实时优先 · 离线让路<br />不加第三个重 GPU 任务</div>
            </div>
          </div>
        </Card>
      </div>

      <div className="split">
        <Card title="离线队列" meta={`${jobs.length} JOBS · ${running} RUNNING`} actions={<button className="btn ghost mini-btn" onClick={() => onView('offline')}>全部任务 →</button>}>
          <div className="card-body tight">
            {jobs.length === 0 ? <div className="empty">暂无离线任务。新建一条文案即可开始。</div> : (
              <table className="table">
                <thead><tr><th>任务</th><th>形象</th><th>进度</th><th>状态</th><th>QC</th></tr></thead>
                <tbody>
                  {jobs.slice(0, 4).map(job => (
                    <tr key={job.id} onClick={() => onView('offline')} className="task-row">
                      <td><div className="title"><span className="avatar-dot" /><span className="name">{job.text.slice(0, 18) || '(无文案)'}</span></div><div className="mono">{timeAgo(job.created_at)}</div></td>
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

        <Card title="最近质检" meta="LAST 24H">
          <div className="card-body list">
            {qcJobs.length === 0 && <div className="empty">暂无质检记录。</div>}
            {qcJobs.map(job => (
              <div className="list-row" key={job.id}>
                <b>{job.text.slice(0, 14) || '未命名任务'}</b>
                <Badge tone={qcTone(job.qc_status)}>{qcText(job)}</Badge>
                <span className="mono">{parseQc(job)?.syncnet && typeof parseQc(job)?.syncnet === 'object' ? `conf ${(parseQc(job)!.syncnet as any).confidence}` : ''}</span>
              </div>
            ))}
            <div className="list-row no-border" style={{ paddingTop: 12 }}>
              <span className="hint">SyncNet · 人脸 · 黑帧 · 闪烁</span>
              <button className="btn ghost mini-btn" style={{ marginLeft: 'auto' }} onClick={() => onView('qc')}>质检中心 →</button>
            </div>
          </div>
        </Card>
      </div>

      {liveJobs.length > 0 && (
        <div className="hint" style={{ marginTop: 12 }}>
          最近完成：{liveJobs.map(j => j.text.slice(0, 10)).join(' · ')}
        </div>
      )}
    </div>
  )
}
