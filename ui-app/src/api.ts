import type { AvatarInfo, AvatarTask, Job, LiveStatus, OfflineHealth, Recording, User, VoiceInfo } from './types'

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) { super(message); this.status = status }
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  const text = await res.text()
  let data: any = null
  try { data = text ? JSON.parse(text) : null } catch { /* ignore */ }
  if (!res.ok) throw new ApiError(data?.msg || data?.error || `${res.status} ${res.statusText}`, res.status)
  if (data && data.code !== undefined && data.code !== 0) throw new Error(data.msg || 'request failed')
  return (data?.data !== undefined ? data.data : data) as T
}

const json = (body: unknown): RequestInit => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

export const api = {
  liveStatus: () => request<LiveStatus>('/api/live/status'),
  offlineHealth: () => request<OfflineHealth>('/api/offline/health'),
  jobs: () => request<Job[]>('/api/offline/jobs'),
  avatars: () => request<AvatarInfo[]>('/api/assets/avatars'),
  voices: () => request<VoiceInfo[]>('/api/assets/voices'),
  bgm: () => request<string[]>('/api/offline/bgm'),
  createJob: (body: {
    text: string; avatar_id: string; voice: string; subtitle: boolean; cover: boolean; bgm: string; priority?: number
  }) => request<{ id: string }>('/api/offline/jobs', json(body)),
  cancelJob: (id: string) => request<unknown>(`/api/offline/jobs/${id}/cancel`, { method: 'POST' }),
  deleteJob: (id: string) => request<unknown>(`/api/offline/jobs/${id}`, { method: 'DELETE' }),
  unloadOffline: () => request<unknown>('/api/offline/unload', { method: 'POST' }),
  retryJob: (id: string) => request<unknown>(`/api/offline/jobs/${id}/retry`, { method: 'POST' }),
  human: (body: { text: string; type: string; interrupt: boolean; sessionid: string }) =>
    request<unknown>('/human', json(body)),
  interrupt: (sessionid: string) =>
    request<unknown>('/interrupt_talk', json({ sessionid })),
  closeLive: (sessionid: string) =>
    request<unknown>('/api/live/close', json({ sessionid })),
  record: (sessionid: string, type: 'start_record' | 'end_record') =>
    request<unknown>('/record', json({ sessionid, type })),
  recordings: () => request<Recording[]>('/api/recordings'),
  deleteRecording: (id: string) => request<unknown>(`/api/recordings/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  me: () => request<User>('/api/v1/auth/me'),
  login: (username: string, password: string) =>
    request<unknown>('/api/v1/auth/login', json({ username, password })),
  logout: () => request<unknown>('/api/v1/auth/logout', { method: 'POST' }),
  avatarTask: (id: string) => request<AvatarTask>(`/api/avatar/task/${id}`),
  createAvatarTask: (avatarId: string, file: File) => {
    const fd = new FormData()
    fd.append('model', 'musetalk')
    fd.append('avatar_id', avatarId)
    fd.append('video_file', file)
    return request<{ task_id: string }>('/api/avatar/task', { method: 'POST', body: fd })
  },
  asr: async (blob: Blob) => {
    const fd = new FormData()
    fd.append('file', blob, 'talk.webm')
    return request<{ text: string; ms: number; duration: number; peak: number; rms: number }>(
      '/api/asr/transcribe', { method: 'POST', body: fd },
    )
  },
  avatarFrame: (id: string) => `/api/assets/avatars/${encodeURIComponent(id)}/frame`,
}

export async function offer(sdp: string, type: string, avatar: string, refaudio: string) {
  return request<{ sdp: string; type: string; sessionid: string }>('/offer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sdp, type, avatar, refaudio }),
  })
}
