import type { AvatarInfo, Job, View } from '../types'
import { AvatarImg, qcText, timeAgo } from './Overview'
import { Badge, Card, Progress, qcTone, statusTone } from './ui'

const caps = [
  { key: 'create', n: '01', title: '创建数字人', desc: '上传视频，生成可用于实时与离线的 MuseTalk 形象。', icon: '◇', cta: '进入资产库' },
  { key: 'live', n: '02', title: '实时对话', desc: '选一个形象，用文本或按住说话开始一场实时会话。', icon: '◉', cta: '打开工作台' },
  { key: 'offline', n: '03', title: '离线视频', desc: '输入长文案，交给队列渲染，完成后下载成片与封面。', icon: '▤', cta: '新建离线任务' },
  { key: 'voice', n: '04', title: '声音 / 音色', desc: '试听并选择 EdgeTTS 音色；音色偏好随形象保存。', icon: '♫', cta: '查看音色' },
]

export default function Capabilities({ avatars, jobs, onWorkbench, onOffline, onAssets }: {
  avatars: AvatarInfo[]; jobs: Job[];
  onWorkbench: (id?: string) => void
  onOffline: (id?: string) => void
  onAssets: () => void
  onView: (v: View) => void
}) {
  const defaultAvatar = avatars.find(a => a.active) || avatars[0]
  const recentJobs = [...jobs].sort((a, b) => b.created_at - a.created_at).slice(0, 4)
  const recentAvatars = avatars.slice(0, 3)

  function open(key: string) {
    if (key === 'create' || key === 'voice') onAssets()
    else if (key === 'offline') onOffline(defaultAvatar?.id)
    else onWorkbench(defaultAvatar?.id)
  }

  return (
    <div className="page capabilities-page">
      <div className="page-head">
        <div><div className="eyebrow">CAPABILITY CENTER / 00</div><h1 className="h1">功能中心</h1><p className="sub">先回答“我能做什么”：创建形象、实时对话、离线视频、选择音色。其他能力不在这里堆入口。</p></div>
        <div className="hero-actions"><button className="btn" onClick={() => onWorkbench(defaultAvatar?.id)}>进入数字人工作台 →</button></div>
      </div>

      <div className="capability-grid">
        {caps.map(c => (
          <button className="card capability-card" key={c.key} onClick={() => open(c.key)}>
            <span className="capability-n">{c.n}</span>
            <span className="capability-icon">{c.icon}</span>
            <span className="capability-title">{c.title}</span>
            <span className="capability-desc">{c.desc}</span>
            <span className="capability-cta">{c.cta} →</span>
          </button>
        ))}
      </div>

      <div className="capability-lower">
        <Card title="最近数字人" meta={`${avatars.length} AVATARS`} actions={<button className="btn ghost mini-btn" onClick={() => onWorkbench(defaultAvatar?.id)}>全部 →</button>}>
          <div className="card-body">
            <div className="recent-avatar-grid">
              {recentAvatars.map(a => (
                <button className="recent-avatar" key={a.id} onClick={() => onWorkbench(a.id)}>
                  <span className="recent-avatar-img"><AvatarImg id={a.id} alt={a.id} /></span>
                  <span><b>{a.id}</b><small>{a.width}×{a.height} · {Math.round(a.frames / 25)}s</small></span>
                  {a.active ? <Badge tone="ok">默认</Badge> : <Badge tone="idle">可用</Badge>}
                </button>
              ))}
              {!recentAvatars.length && <div className="empty">还没有数字人，从“创建数字人”开始。</div>}
            </div>
            <div className="capability-note"><span>需要新的形象？</span><button className="btn ghost mini-btn" onClick={onAssets}>创建数字人 →</button></div>
          </div>
        </Card>

        <Card title="最近项目" meta="LATEST JOBS" actions={<button className="btn ghost mini-btn" onClick={() => onOffline(defaultAvatar?.id)}>离线任务 →</button>}>
          <div className="card-body tight">
            {recentJobs.length === 0 ? <div className="empty">还没有离线项目。输入一条文案即可开始。</div> : (
              <table className="table">
                <thead><tr><th>项目</th><th>形象</th><th>进度</th><th>状态</th><th>QC</th></tr></thead>
                <tbody>
                  {recentJobs.map(j => (
                    <tr key={j.id} onClick={() => onOffline(j.avatar_id)} className="task-row">
                      <td><div className="name">{j.text.slice(0, 18) || '(无文案)'}</div><div className="mono">{timeAgo(j.created_at)}</div></td>
                      <td className="mono">{j.avatar_id}</td>
                      <td><Progress value={j.progress} wait={j.stage === 'waiting_live'} /></td>
                      <td><Badge tone={statusTone(j.status)}>{j.status === 'success' ? '完成' : j.status === 'failed' ? '失败' : j.status === 'running' ? '渲染中' : '排队中'}</Badge></td>
                      <td><Badge tone={qcTone(j.qc_status)}>{qcText(j)}</Badge></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}
