import type { AvatarInfo, LiveStatus, VoiceInfo } from '../types'
import Live from './Live'

export default function Present({ avatarId, defaultAvatarId, avatars, voices, live, notify, onExit }: {
  avatarId?: string; defaultAvatarId?: string; avatars: AvatarInfo[]; voices: VoiceInfo[]; live: LiveStatus;
  notify: (s: string) => void; onExit: () => void
}) {
  return <Live initialAvatarId={avatarId} defaultAvatarId={defaultAvatarId} mode="present" live={live} avatars={avatars} voices={voices} notify={notify} onExit={onExit} />
}
