import type { AvatarInfo, User } from './types'

export function defaultAvatarKey(user: User): string {
  return `nexus.defaultAvatar.${user.tenant_id || 'default'}.${user.username}`
}

export function readDefaultAvatarId(user: User, avatars: AvatarInfo[]): string {
  try {
    const saved = localStorage.getItem(defaultAvatarKey(user)) || ''
    if (saved && avatars.some(a => a.id === saved)) return saved
  } catch { /* ignore */ }
  return avatars.find(a => a.active)?.id || avatars[0]?.id || ''
}
