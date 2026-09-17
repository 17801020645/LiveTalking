<template>
  <div class="deck">
    <h2 class="page-title">首页</h2>
    <section
      class="monitor-panel user-live-panel"
      :class="{ 'is-program': connected, 'is-fault': Boolean(error) }"
    >
      <span class="tally" :class="connected ? 'is-live' : (error ? 'is-fault' : 'is-idle')" aria-hidden="true" />
      <p class="monitor-name">{{ published ? published.name : '连麦' }}</p>
      <div class="monitor-body">
        <template v-if="published">
          <video
            v-show="connected"
            ref="remoteVideo"
            class="cover"
            autoplay
            playsinline
          />
          <video
            v-show="!connected && published.preview_url"
            class="cover"
            :src="published.preview_url"
            :poster="published.cover_url || undefined"
            muted
            loop
            autoplay
            playsinline
          />
          <img
            v-show="!connected && !published.preview_url && published.cover_url"
            class="cover"
            :src="published.cover_url"
            :alt="published.name"
          />
          <p class="muted">{{ connected ? '已连接' : '发布到首页的数字人' }}</p>
          <p v-if="error" class="error">{{ error }}</p>
          <div class="row-actions">
            <button v-if="!connected" class="btn" type="button" :disabled="starting" @click="start">
              {{ starting ? '连接中…' : '开始连麦' }}
            </button>
            <button v-else class="btn-ghost" type="button" @click="stop">断开</button>
          </div>
          <div class="field" style="margin-top: 12px;">
            <label>发送文字</label>
            <input
              v-model="text"
              :disabled="!connected"
              @keyup.enter="sendText"
              placeholder="输入后回车发送"
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
          <div class="row-actions">
            <button
              class="btn"
              type="button"
              :disabled="!connected || listening || recognizing"
              @click="startMic"
            >
              开始说话
            </button>
            <button
              class="btn-ghost"
              type="button"
              :disabled="!connected || !listening || recognizing"
              @click="stopMic"
            >
              {{ recognizing ? '识别中…' : '停止识别' }}
            </button>
          </div>
          <div class="field">
            <label>音频文件</label>
            <input ref="audioInput" type="file" accept="audio/*" :disabled="!connected" />
          </div>
          <div class="row-actions">
            <button class="btn" type="button" :disabled="!connected || uploading" @click="uploadAudio">
              {{ uploading ? '上传中…' : '上传并播放' }}
            </button>
          </div>
          <div class="row-actions">
            <button
              class="btn"
              :class="{ 'btn-danger': recording }"
              type="button"
              :disabled="!connected"
              @click="toggleRecord"
            >
              {{ recording ? '停止录制' : '开始录制' }}
            </button>
            <button class="btn-ghost" type="button" :disabled="!sessionid || recording || !recReady" @click="downloadRecord">
              下载录像
            </button>
          </div>
          <div class="field">
            <label>Audiotype 索引</label>
            <input v-model.number="audiotype" type="number" min="2" :disabled="!connected" />
          </div>
          <div class="row-actions">
            <button class="btn" type="button" :disabled="!connected" @click="setAudiotype">切换状态</button>
          </div>
        </template>
        <p v-else class="muted">还没有发布数字人，请到「我的资产」选择一个并发布。</p>
      </div>
    </section>
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
const talkType = ref('echo')
const interrupting = ref(false)
const remoteVideo = ref(null)
const sessionid = ref('')
const listening = ref(false)
const recognizing = ref(false)
const audioInput = ref(null)
const uploading = ref(false)
const recording = ref(false)
const recReady = ref(false)
const audiotype = ref(2)
let pc = null
let interruptFlashTimer = null
let asrWs = null
let asrStream = null
let asrCtx = null
let asrProcessor = null
let asrSource = null
let asrResultWaiter = null

onMounted(async () => {
  const data = await api('/api/v1/me/home')
  published.value = data.published
})

onUnmounted(() => {
  if (interruptFlashTimer) clearTimeout(interruptFlashTimer)
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
  await abortMic()
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
  recording.value = false
  recReady.value = false
}

function asrWsUrl() {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return proto + '//' + window.location.host + '/api/asr'
}

function floatToPcm16(float32, inputRate) {
  const ratio = inputRate / 16000
  const outLen = Math.max(1, Math.floor(float32.length / ratio))
  const out = new Int16Array(outLen)
  for (let i = 0; i < outLen; i++) {
    const s = Math.max(-1, Math.min(1, float32[Math.floor(i * ratio)] || 0))
    out[i] = s < 0 ? s * 0x8000 : s * 0x7fff
  }
  return out
}

function closeAsrCapture() {
  if (asrProcessor) {
    asrProcessor.onaudioprocess = null
    try {
      asrProcessor.disconnect()
    } catch (e) {
      /* ignore */
    }
    asrProcessor = null
  }
  if (asrSource) {
    try {
      asrSource.disconnect()
    } catch (e) {
      /* ignore */
    }
    asrSource = null
  }
  if (asrCtx) {
    asrCtx.close().catch(() => {})
    asrCtx = null
  }
  if (asrStream) {
    asrStream.getTracks().forEach((t) => t.stop())
    asrStream = null
  }
}

async function abortMic() {
  listening.value = false
  recognizing.value = false
  closeAsrCapture()
  if (asrResultWaiter) {
    asrResultWaiter.reject(new Error('已取消'))
    asrResultWaiter = null
  }
  if (asrWs) {
    try {
      asrWs.close()
    } catch (e) {
      /* ignore */
    }
    asrWs = null
  }
}

async function startMic() {
  if (!connected.value || !sessionid.value || listening.value || recognizing.value) return
  error.value = ''
  try {
    asrStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    asrWs = new WebSocket(asrWsUrl())
    await new Promise((resolve, reject) => {
      asrWs.onopen = resolve
      asrWs.onerror = () => reject(new Error('本机 ASR 不可用'))
    })
    asrWs.send(
      JSON.stringify({
        chunk_size: [5, 10, 5],
        wav_name: 'h5',
        is_speaking: true,
        chunk_interval: 10,
        itn: false,
        mode: 'offline',
      }),
    )
    asrCtx = new AudioContext({ sampleRate: 16000 })
    asrSource = asrCtx.createMediaStreamSource(asrStream)
    asrProcessor = asrCtx.createScriptProcessor(4096, 1, 1)
    asrProcessor.onaudioprocess = (evt) => {
      if (!asrWs || asrWs.readyState !== WebSocket.OPEN) return
      const input = evt.inputBuffer.getChannelData(0)
      const pcm = floatToPcm16(input, asrCtx.sampleRate || 16000)
      asrWs.send(pcm.buffer)
    }
    const mute = asrCtx.createGain()
    mute.gain.value = 0
    asrSource.connect(asrProcessor)
    asrProcessor.connect(mute)
    mute.connect(asrCtx.destination)
    listening.value = true
  } catch (e) {
    await abortMic()
    error.value = e.message || '无法使用麦克风'
  }
}

async function stopMic() {
  if (!listening.value || recognizing.value) return
  listening.value = false
  recognizing.value = true
  error.value = ''
  closeAsrCapture()
  try {
    if (!asrWs || asrWs.readyState !== WebSocket.OPEN) {
      throw new Error('本机 ASR 不可用')
    }
    const resultPromise = new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('识别超时')), 20000)
      asrResultWaiter = {
        resolve: (text) => {
          clearTimeout(timer)
          asrResultWaiter = null
          resolve(text)
        },
        reject: (err) => {
          clearTimeout(timer)
          asrResultWaiter = null
          reject(err)
        },
      }
      asrWs.onmessage = (evt) => {
        let payload = {}
        try {
          payload = JSON.parse(evt.data)
        } catch (e) {
          return
        }
        if (asrResultWaiter) asrResultWaiter.resolve(payload.text || '')
      }
      asrWs.onerror = () => {
        if (asrResultWaiter) asrResultWaiter.reject(new Error('本机 ASR 不可用'))
      }
    })
    asrWs.send(
      JSON.stringify({
        chunk_size: [5, 10, 5],
        wav_name: 'h5',
        is_speaking: false,
        chunk_interval: 10,
        mode: 'offline',
      }),
    )
    const recognized = String(await resultPromise).trim()
    if (!recognized) {
      error.value = '未识别到语音'
      return
    }
    text.value = recognized
    await sendHuman(recognized)
  } catch (e) {
    if (e.message !== '已取消') error.value = e.message || '识别失败'
  } finally {
    recognizing.value = false
    if (asrWs) {
      try {
        asrWs.close()
      } catch (e) {
        /* ignore */
      }
      asrWs = null
    }
  }
}

async function sendHuman(t) {
  if (!t || !sessionid.value) return
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
}

async function postJson(path, payload, failMsg) {
  const res = await fetch(path, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const body = await res.json().catch(() => ({}))
  if (!res.ok || (typeof body.code === 'number' && body.code !== 0)) {
    throw new Error(body.msg || failMsg)
  }
  return body
}

async function uploadAudio() {
  const file = audioInput.value && audioInput.value.files && audioInput.value.files[0]
  if (!file || !sessionid.value || uploading.value) return
  uploading.value = true
  error.value = ''
  try {
    const form = new FormData()
    form.append('file', file)
    form.append('sessionid', String(sessionid.value))
    const res = await fetch('/humanaudio', {
      method: 'POST',
      credentials: 'include',
      body: form,
    })
    const body = await res.json().catch(() => ({}))
    if (!res.ok || (typeof body.code === 'number' && body.code !== 0)) {
      throw new Error(body.msg || '上传失败')
    }
  } catch (e) {
    error.value = e.message
  } finally {
    uploading.value = false
  }
}

async function toggleRecord() {
  if (!sessionid.value) return
  error.value = ''
  const type = recording.value ? 'end_record' : 'start_record'
  try {
    await postJson('/record', { type, sessionid: sessionid.value }, '录制失败')
    recording.value = !recording.value
    recReady.value = !recording.value
  } catch (e) {
    error.value = e.message
  }
}

function downloadRecord() {
  if (!sessionid.value) return
  window.open('/record/' + sessionid.value, '_blank', 'noopener')
}

async function setAudiotype() {
  if (!sessionid.value) return
  error.value = ''
  try {
    await postJson(
      '/set_audiotype',
      { audiotype: Number(audiotype.value) || 2, sessionid: sessionid.value },
      '切换失败',
    )
  } catch (e) {
    error.value = e.message
  }
}

async function sendText() {
  const t = text.value.trim()
  if (!t || !sessionid.value) return
  error.value = ''
  try {
    await sendHuman(t)
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
