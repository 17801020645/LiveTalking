import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { api } from '../api'
import type { Recording, User } from '../types'
import { Badge, Card, VideoPreview } from './ui'

function fmtSize(n: number) {
  if (n > 1024 * 1024) return (n / 1024 / 1024).toFixed(1) + ' MB'
  return (n / 1024).toFixed(0) + ' KB'
}


function RecordingThumb({ url, onPlay }: { url: string; onPlay: () => void }) {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const [poster, setPoster] = useState('')
  useEffect(() => {
    setPoster('')
    const video = videoRef.current
    if (!video) return
    const seek = () => { try { video.currentTime = Math.min(0.15, (video.duration || 1) / 10) } catch { /* metadata not ready */ } }
    const snap = () => {
      if (!video.videoWidth || !video.videoHeight) return
      try {
        const canvas = document.createElement('canvas')
        canvas.width = video.videoWidth
        canvas.height = video.videoHeight
        canvas.getContext('2d')?.drawImage(video, 0, 0, canvas.width, canvas.height)
        setPoster(canvas.toDataURL('image/jpeg', 0.72))
      } catch { /* CORS / decode */ }
    }
    video.addEventListener('loadedmetadata', seek)
    video.addEventListener('seeked', snap)
    return () => {
      video.removeEventListener('loadedmetadata', seek)
      video.removeEventListener('seeked', snap)
    }
  }, [url])
  return (
    <button className="recording-thumb" onClick={onPlay} aria-label="播放录制预览">
      {poster ? <img src={poster} alt="录制画面预览" /> : <video ref={videoRef} src={`${url}#t=0.1`} muted playsInline preload="metadata" />}
      <span className="recording-play">▶</span>
    </button>
  )
}

export default function Recordings({ user, notify }: { user: User; notify: (s: string) => void }) {
  const [items, setItems] = useState<Recording[]>([])
  const [loading, setLoading] = useState(true)
  const [playing, setPlaying] = useState<Recording | null>(null)

  async function load() {
    setLoading(true)
    try { setItems(await api.recordings()) } catch (e: any) { notify(`加载录制失败：${e.message || e}`) }
    finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  function clip(id: string) {
    const start = Number(prompt('起始秒数', '0') || '0')
    const end = Number(prompt('结束秒数', '10') || '10')
    if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) return notify('时间范围无效')
    window.open(api.clipRecordingUrl(id, start, end), '_blank')
  }

  async function remove(id: string) {
    if (!confirm('删除这条录制？')) return
    try { await api.deleteRecording(id); notify('录制已删除'); load() }
    catch (e: any) { notify(`删除失败：${e.message || e}`) }
  }

  return (
    <div className="page">
      <div className="page-head">
        <div><div className="eyebrow">RECORDINGS / 06</div><h1 className="h1">录制库</h1><p className="sub">实时会话录制文件；可播放、下载，管理员可删除。</p></div>
        <div className="hero-actions"><button className="btn" onClick={load}>↻ 刷新</button></div>
      </div>
      <Card title="录制文件" meta={`${items.length} FILES`}>
        <div className="card-body tight">
          {loading ? <div className="empty">加载中…</div> : items.length === 0 ? <div className="empty">暂无录制。进入实时会话点“录制”开始。</div> : (
            <table className="table">
              <thead><tr><th>会话</th><th>大小</th><th>时间</th><th>操作</th></tr></thead>
              <tbody>
                {items.map(r => (
                  <tr key={r.id}>
                    <td><div className="recording-name"><RecordingThumb url={r.url} onPlay={() => setPlaying(r)} /><div><b>{r.id.slice(0, 12)}…</b><small className="mono">{r.name}</small></div></div></td>
                    <td className="mono">{fmtSize(r.size)}</td>
                    <td className="mono">{new Date(r.mtime * 1000).toLocaleString('zh-CN')}</td>
                    <td>
                      <button className="btn ghost mini-btn" onClick={() => setPlaying(r)}>播放</button>{' '}
                      <a className="btn ghost mini-btn" href={r.url} download>下载</a>{' '}
                      {user.role === 'admin' && <button className="btn ghost mini-btn" onClick={() => clip(r.id)}>剪辑</button>}{' '}
                      {user.role === 'admin' && <button className="btn danger mini-btn" onClick={() => remove(r.id)}>删除</button>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <div className="hint" style={{ padding: '10px 8px' }}><Badge tone="idle">MP4</Badge> 录制由 LiveTalking 的 /record 生成，保存在 data/record/。</div>
        </div>
      </Card>
      {playing && createPortal(
        <div className="media-modal" onClick={() => setPlaying(null)}>
          <div className="media-dialog" onClick={e => e.stopPropagation()}>
            <button className="media-close" onClick={() => setPlaying(null)} aria-label="关闭播放器">×</button>
            <VideoPreview className="media-video" src={playing.url} autoPlay />
            <div className="media-caption"><span>{playing.name}</span><span className="mono">{fmtSize(playing.size)}</span></div>
          </div>
        </div>, document.body)}
    </div>
  )
}
