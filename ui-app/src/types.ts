export type View = 'overview' | 'offline' | 'live' | 'assets' | 'recordings' | 'qc' | 'settings'

export interface Job {
  id: string
  status: 'pending' | 'running' | 'success' | 'failed' | string
  stage?: string | null
  text: string
  avatar_id: string
  voice: string
  progress: number
  error?: string | null
  qc_status?: string | null
  qc_json?: string | null
  created_at: number
  output_path?: string | null
  srt_path?: string | null
  cover_path?: string | null
  subtitle?: number
  cover?: number
  bgm?: string
  priority?: number
  cancel_requested?: number
}

export interface LiveSession {
  id: string
  state?: string
}

export interface GpuInfo {
  used_mb: number
  total_mb: number
}

export interface LiveStatus {
  active: number
  max: number
  sessions: LiveSession[]
  gpu: GpuInfo
}

export interface OfflineHealth {
  worker_alive: boolean
  counts: Record<string, number>
}

export interface AvatarInfo {
  id: string
  frames: number
  width: number
  height: number
  active?: boolean
}

export interface VoiceInfo {
  id: string
  name: string
  gender: string
  provider: string
}

export interface QcResult {
  status?: string
  reasons?: string[]
  warnings?: string[]
  face_missing_ratio?: number
  black_ratio?: number
  flicker_ratio?: number
  lip_corr?: number
  syncnet?: { status?: string; confidence?: number; av_offset?: number } | string
}

export interface Recording {
  id: string
  name: string
  size: number
  mtime: number
  url: string
}

export interface AvatarTask {
  task_id: string
  model_type: string
  avatar_id: string
  status: string
  progress: number
  error_msg: string
}

export interface User {
  id: number
  username: string
  role: 'admin' | 'user' | string
  status?: string
}
