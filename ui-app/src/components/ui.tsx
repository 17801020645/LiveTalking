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
