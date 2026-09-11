<template>
  <div>
    <Teleport to="body">
      <Transition name="toast">
        <div v-if="toast" class="glass live-toast" role="status">{{ toast }}</div>
      </Transition>
    </Teleport>
    <h2 class="page-title">演示连麦</h2>
    <p v-if="error" class="error">{{ error }}</p>
    <div class="live-grid">
      <div class="glass card">
        <h3>连接</h3>
        <div class="field">
          <label>形象</label>
          <select v-model="avatarId" :disabled="connected">
            <option disabled value="">请选择形象</option>
            <option v-for="a in avatars" :key="a.avatar_id" :value="a.avatar_id">
              {{ a.name || a.avatar_id }}
            </option>
          </select>
        </div>
        <video
          v-show="connected"
          ref="remoteVideo"
          class="live-video"
          autoplay
          playsinline
          muted
        />
        <video
          v-show="!connected && selected && selected.preview_url"
          class="live-video"
          :src="selected && selected.preview_url"
          :poster="selected && selected.cover_url || undefined"
          muted
          loop
          autoplay
          playsinline
        />
        <img
          v-show="!connected && selected && !selected.preview_url && selected.cover_url"
          class="live-video"
          :src="selected && selected.cover_url"
          :alt="selected && selected.name"
        />
        <div
          v-show="!connected && (!selected || (!selected.preview_url && !selected.cover_url))"
          class="live-video-slot"
        />
        <audio ref="remoteAudio" autoplay />
        <p class="muted">{{ statusText }}</p>
        <div class="row-actions">
          <button v-if="!connected" class="btn" type="button" :disabled="starting || !avatarId" @click="start">
            {{ starting ? '连接中…' : '开始连接' }}
          </button>
          <button v-else class="btn-ghost" type="button" @click="stop">断开</button>
        </div>
      </div>
      <div class="glass card">
        <h3>说话</h3>
        <p v-if="!connected" class="muted">连接后即可发送</p>
        <div class="field">
          <label>发送文字</label>
          <textarea
            v-model="text"
            :disabled="!connected"
            placeholder="输入后回车发送"
            @keydown.enter.exact.prevent="sendText"
          />
        </div>
        <div class="field">
          <label>模式</label>
          <select v-model="talkType" :disabled="!connected">
            <option value="echo">Echo 复读</option>
            <option value="chat">Chat LLM</option>
          </select>
        </div>
        <div class="row-actions">
          <button class="btn" type="button" :disabled="!connected" @click="sendText">发送</button>
          <button
            class="btn-interrupt"
            type="button"
            :disabled="!connected"
            :class="{ 'is-fired': interrupting }"
            @click="interrupt"
          >
            打断
          </button>
        </div>
        <p class="muted" style="margin-top: 16px;">
          音频上传、录制、动作编排仍使用原站点：<a href="/" target="_blank" rel="noopener">打开 /</a>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { api } from '../../api'

const error = ref('')
const avatars = ref([])
const avatarId = ref('')
const connected = ref(false)
const starting = ref(false)
const text = ref('')
const talkType = ref('echo')
const interrupting = ref(false)
const toast = ref('')
const remoteVideo = ref(null)
const remoteAudio = ref(null)
const sessionid = ref('')
let pc = null
let interruptFlashTimer = null
let toastTimer = null

const selected = computed(() => avatars.value.find((a) => a.avatar_id === avatarId.value) || null)
const statusText = computed(() => {
  if (starting.value) return '连接中…'
  if (connected.value) return sessionid.value ? `已连接 · ${sessionid.value}` : '已连接'
  if (!avatarId.value) return '请先选择形象'
  return '选择形象后开始连接'
})

onMounted(async () => {
  try {
    const listed = await api('/api/v1/admin/avatars')
    avatars.value = listed.avatars || []
  } catch (e) {
    error.value = e.message
  }
})

onUnmounted(() => {
  if (interruptFlashTimer) clearTimeout(interruptFlashTimer)
  if (toastTimer) clearTimeout(toastTimer)
  stop()
})

function showToast(msg) {
  toast.value = msg
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toast.value = ''
    toastTimer = null
  }, 2400)
}

async function start() {
  if (!avatarId.value) return
  error.value = ''
  starting.value = true
  try {
    pc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] })
    pc.addTransceiver('video', { direction: 'recvonly' })
    pc.addTransceiver('audio', { direction: 'recvonly' })
    pc.addEventListener('track', (evt) => {
      if (evt.track.kind === 'video' && remoteVideo.value) {
        remoteVideo.value.srcObject = evt.streams[0]
      }
      if (evt.track.kind === 'audio' && remoteAudio.value) {
        remoteAudio.value.srcObject = evt.streams[0]
      }
    })
    const offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    await waitIce(pc)
    const local = pc.localDescription
    const res = await fetch('/offer', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sdp: local.sdp,
        type: local.type,
        avatar: avatarId.value,
      }),
    })
    const answer = await res.json().catch(() => ({}))
    if (!res.ok || (answer.code && answer.code !== 0)) {
      throw new Error(answer.msg || '连接失败')
    }
    if (!answer.sdp) {
      throw new Error('服务端未返回画面')
    }
    sessionid.value = answer.sessionid || ''
    await pc.setRemoteDescription({ type: answer.type || 'answer', sdp: answer.sdp })
    connected.value = true
  } catch (e) {
    error.value = e.message || '连接失败'
    await stop()
  } finally {
    starting.value = false
  }
}

async function stop() {
  connected.value = false
  if (pc) {
    pc.close()
    pc = null
  }
  if (remoteVideo.value) remoteVideo.value.srcObject = null
  if (remoteAudio.value) remoteAudio.value.srcObject = null
  sessionid.value = ''
}

async function sendText() {
  const t = text.value.trim()
  if (!t || !sessionid.value) return
  error.value = ''
  try {
    const res = await fetch('/human', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: t,
        type: talkType.value,
        interrupt: true,
        sessionid: sessionid.value,
      }),
    })
    const body = await res.json().catch(() => ({}))
    if (!res.ok || (typeof body.code === 'number' && body.code !== 0)) {
      throw new Error(body.msg || '发送失败')
    }
    text.value = ''
  } catch (e) {
    error.value = e.message
  }
}

async function interrupt() {
  if (!sessionid.value || interrupting.value) return
  interrupting.value = true
  error.value = ''
  try {
    const res = await fetch('/interrupt_talk', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sessionid: sessionid.value }),
    })
    const body = await res.json().catch(() => ({}))
    if (!res.ok || (typeof body.code === 'number' && body.code !== 0)) {
      throw new Error(body.msg || '打断失败')
    }
    showToast('已停止讲话')
  } catch (e) {
    error.value = e.message
  } finally {
    if (interruptFlashTimer) clearTimeout(interruptFlashTimer)
    interruptFlashTimer = setTimeout(() => {
      interrupting.value = false
      interruptFlashTimer = null
    }, 450)
  }
}

function waitIce(peer, ms = 8000) {
  return new Promise((resolve) => {
    if (peer.iceGatheringState === 'complete') {
      resolve()
      return
    }
    const finish = () => {
      clearTimeout(timer)
      peer.removeEventListener('icegatheringstatechange', check)
      resolve()
    }
    const check = () => {
      if (peer.iceGatheringState === 'complete') finish()
    }
    const timer = setTimeout(finish, ms)
    peer.addEventListener('icegatheringstatechange', check)
  })
}
</script>
