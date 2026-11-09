import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'

export type Tone = 'live' | 'run' | 'wait' | 'ok' | 'fail' | 'idle'

export function Badge({ tone = 'idle', children, className = '' }: {
  tone?: Tone; children: ReactNode; className?: string
}) {
  return <span className={`badge b-${tone} ${className}`}>{children}</span>
}

export function Progress({ value, wait = false }: { value: number; wait?: boolean }) {
  return (
    <div className={`progress${wait ? ' wait' : ''}`} role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={100}>
      <i style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </div>
  )
}

export function Card({ title, meta, actions, children, className = '' }: {
  title?: ReactNode; meta?: ReactNode; actions?: ReactNode; children: ReactNode; className?: string
}) {
  return (
    <section className={`card ${className}`}>
      {(title || meta || actions) && (
        <div className="card-head">
          {title && <h3>{title}</h3>}
          {meta && <span className="meta">{meta}</span>}
          {actions && <div className="card-actions">{actions}</div>}
        </div>
      )}
      {children}
    </section>
  )
}

export function statusTone(status?: string | null): Tone {
  if (status === 'success') return 'ok'
  if (status === 'running') return 'run'
  if (status === 'failed') return 'fail'
  if (status === 'pending') return 'wait'
  return 'idle'
}

export function qcTone(status?: string | null): Tone {
  if (status === 'pass') return 'ok'
  if (status === 'warn') return 'wait'
  if (status === 'fail') return 'fail'
  if (status === 'error') return 'fail'
  return 'idle'
}

export function VideoPreview({ src, poster, className = '', autoPlay = false }: {
  src: string; poster?: string; className?: string; autoPlay?: boolean
}) {
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')
  useEffect(() => {
    let cancelled = false
    let objectUrl = ''
    setUrl(''); setError('')
    fetch(src)
      .then(res => {
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
        return res.blob()
      })
      .then(blob => {
        if (cancelled) return
        objectUrl = URL.createObjectURL(blob)
        setUrl(objectUrl)
      })
      .catch(err => { if (!cancelled) setError(err.message || '视频加载失败') })
    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [src])
  if (error) return <div className={`video-load-error ${className}`}><span>视频加载失败</span><a className="btn ghost mini-btn" href={src} download>下载原文件</a></div>
  if (!url) return <div className={`video-loading ${className}`}><span>加载视频预览…</span></div>
  return <video className={className} src={url} poster={poster} controls autoPlay={autoPlay} playsInline preload="metadata" />
}
