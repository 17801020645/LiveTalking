import type { Job } from '../types'
import { AvatarImg, parseQc, qcText, timeAgo } from './Overview'
import { Badge, Card, qcTone } from './ui'

export default function QC({ jobs }: { jobs: Job[] }) {
  const qcJobs = jobs.filter(j => j.qc_status || j.qc_json)
  const pass = qcJobs.filter(j => j.qc_status === 'pass').length
  const warn = qcJobs.filter(j => j.qc_status === 'warn').length
  const fail = qcJobs.filter(j => j.qc_status === 'fail').length
  return (
    <div className="page">
      <div className="page-head"><div><div className="eyebrow">QUALITY / 04</div><h1 className="h1">质检中心</h1><p className="sub">人脸丢失、黑帧、闪烁与 SyncNet 口型一致性；失败任务可重试。</p></div><div className="hero-actions"><button className="btn" onClick={() => window.open('/api/offline/jobs')}>导出报告</button></div></div>
      <div className="kpis kpis-3">
        <div className="card kpi"><div className="label">PASS</div><div className="value">{pass}</div><div className="delta"><b>通过</b> · 最近任务</div></div>
        <div className="card kpi"><div className="label">WARN</div><div className="value">{warn}</div><div className="delta"><i>需人工复核</i></div></div>
        <div className="card kpi"><div className="label">FAIL</div><div className="value">{fail}</div><div className="delta"><b className="rose">失败</b> · 可重试</div></div>
      </div>
      <Card title="最近质检" meta={`${qcJobs.length} RECORDS`}>
        <div className="card-body tight">
          {qcJobs.length === 0 ? <div className="empty">暂无质检记录</div> : (
            <table className="table">
              <thead><tr><th>任务</th><th>形象</th><th>人脸</th><th>黑帧</th><th>闪烁</th><th>SyncNet</th><th>结论</th><th>时间</th></tr></thead>
              <tbody>
                {qcJobs.map(job => {
                  const qc = parseQc(job)
                  const sync = qc && typeof qc.syncnet === 'object' ? qc.syncnet : null
                  return (
                    <tr key={job.id}>
                      <td className="name">{job.text.slice(0, 18) || job.id.slice(0, 8)}</td>
                      <td><div className="avatar-cell"><span className="table-avatar"><AvatarImg id={job.avatar_id} alt={job.avatar_id} /></span><span className="mono">{job.avatar_id}</span></div></td>
                      <td className="mono">{qc?.face_missing_ratio ?? '—'}</td>
                      <td className="mono">{qc?.black_ratio ?? '—'}</td>
                      <td className="mono">{qc?.flicker_ratio ?? '—'}</td>
                      <td className="mono">{sync ? `${sync.confidence ?? '—'} / ${sync.av_offset ?? '—'}` : '—'}</td>
                      <td><Badge tone={qcTone(job.qc_status)}>{qcText(job)}</Badge></td>
                      <td className="mono">{timeAgo(job.created_at)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </Card>
    </div>
  )
}
