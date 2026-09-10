<template>
  <div>
    <h2 class="page-title">首页</h2>
    <div v-if="published" class="glass card" style="max-width: 480px;">
      <video
        v-show="connected"
        ref="remoteVideo"
        class="cover"
        autoplay
        playsinline
      />
      <img
        v-show="!connected && published.cover_url"
        class="cover"
        :src="published.cover_url"
        :alt="published.name"
      />
      <video
        v-show="!connected && !published.cover_url && published.preview_url"
        class="cover"
        :src="published.preview_url"
        muted
        loop
        autoplay
        playsinline
      />
      <h3>{{ published.name }}</h3>
      <p class="muted">{{ connected ? '已连接' : '发布到首页的数字人' }}</p>
      <p v-if="error" class="error">{{ error }}</p>
      <div class="row-actions">
        <button v-if="!connected" class="btn" type="button" :disabled="starting" @click="start">
          {{ starting ? '连接中…' : '开始连麦' }}
        </button>
        <button v-else class="btn-ghost" type="button" @click="stop">断开</button>
      </div>
      <div v-if="connected" class="field" style="margin-top: 12px;">
        <label>发送文字</label>
        <input v-model="text" @keyup.enter="sendText" placeholder="输入后回车发送" />
        <button class="btn" type="button" style="margin-top: 8px;" @click="sendText">发送</button>
      </div>
    </div>
    <div v-else class="glass empty">
      还没有发布数字人，请到「我的资产」选择一个并发布。
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { api } from '../../api'

const published = ref(null)
const connected = ref(false)
const starting = ref(false)
const error = ref('')
const text = ref('')
const remoteVideo = ref(null)
const sessionid = ref('')
let pc = null

onMounted(async () => {
  const data = await api('/api/v1/me/home')
  published.value = data.published
})

onUnmounted(() => {
  stop()
})

async function start() {
  error.value = ''
  starting.value = true
  try {
    pc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] })
    pc.addTransceiver('video', { direction: 'recvonly' })
    pc.addTransceiver('audio', { direction: 'recvonly' })
    pc.addEventListener('track', (evt) => {
      if (!remoteVideo.value) return
      remoteVideo.value.srcObject = evt.streams[0]
    })
    const offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    await waitIce(pc)
    const local = pc.localDescription
    const data = await api('/api/v1/me/offer', {
      method: 'POST',
      body: JSON.stringify({
        sdp: local.sdp,
        type: local.type,
        avatar: 'ignored-client-value',
      }),
    })
    sessionid.value = data.sessionid
    await pc.setRemoteDescription({ type: data.type, sdp: data.sdp })
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
  if (sessionid.value) {
    try {
      await api('/api/v1/me/hangup', { method: 'POST' })
    } catch {
      /* ignore */
    }
    sessionid.value = ''
  }
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
        type: 'echo',
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

function waitIce(peer) {
  return new Promise((resolve) => {
    if (peer.iceGatheringState === 'complete') {
      resolve()
      return
    }
    const check = () => {
      if (peer.iceGatheringState === 'complete') {
        peer.removeEventListener('icegatheringstatechange', check)
        resolve()
      }
    }
    peer.addEventListener('icegatheringstatechange', check)
  })
}
</script>
