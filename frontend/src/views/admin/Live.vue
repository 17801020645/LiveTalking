<template>
  <div>
    <Teleport to="body">
      <Transition name="toast">
        <div v-if="toast" class="glass live-toast" role="status">{{ toast }}</div>
      </Transition>
    </Teleport>
    <div class="deck">
    <h2 class="page-title">演示连麦</h2>
    <p v-if="error" class="error">{{ error }}</p>
    <div class="live-grid">
      <section class="monitor-panel" :class="{ 'is-program': connected, 'is-fault': Boolean(error) }">
        <span class="tally" :class="connected ? 'is-program' : (error ? 'is-fault' : 'is-idle')" aria-hidden="true" />
        <p class="monitor-name">连接</p>
        <div class="monitor-body">
        <div class="field">
          <label>形象</label>
          <select v-model="avatarId" :disabled="connected">
            <option disabled value="">请选择形象</option>
            <option v-for="a in avatars" :key="a.avatar_id" :value="a.avatar_id">
              {{ a.name || a.avatar_id }}
            </option>
          </select>
        </div>
        <div class="field">
          <label>参考音频</label>
          <input
            v-model="refAudio"
            :disabled="connected"
            placeholder="音色名或参考音频，可选"
          />
        </div>
        <div class="field">
          <label>参考音频文本</label>
          <input
            v-model="refText"
            :disabled="connected"
            placeholder="参考文本（可选）"
          />
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
      </section>
      <div class="live-side">
      <section class="monitor-panel" :class="{ 'is-program': connected }">
        <span class="tally" :class="connected ? 'is-live' : 'is-idle'" aria-hidden="true" />
        <p class="monitor-name">说话</p>
        <div class="monitor-body">
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
        </div>
      </section>
      <section class="monitor-panel" :class="{ 'is-program': connected }">
        <span class="tally" :class="connected ? 'is-live' : 'is-idle'" aria-hidden="true" />
        <p class="monitor-name">音频驱动</p>
        <div class="monitor-body">
        <p v-if="!connected" class="muted">连接后可上传音频驱动口型</p>
        <div class="field">
          <label>音频文件</label>
          <input ref="audioInput" type="file" accept="audio/*" :disabled="!connected" />
        </div>
        <div class="row-actions">
          <button class="btn" type="button" :disabled="!connected || uploading" @click="uploadAudio">
            {{ uploading ? '上传中…' : '上传并播放' }}
          </button>
        </div>
        </div>
      </section>
      <section class="monitor-panel" :class="{ 'is-warn': recording, 'is-program': connected && !recording }">
        <span class="tally" :class="recording ? 'is-warn' : (connected ? 'is-live' : 'is-idle')" aria-hidden="true" />
        <p class="monitor-name">录制控制</p>
        <div class="monitor-body">
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
        </div>
      </section>
      <section class="monitor-panel" :class="{ 'is-program': connected }">
        <span class="tally" :class="connected ? 'is-live' : 'is-idle'" aria-hidden="true" />
        <p class="monitor-name">动作编排</p>
        <div class="monitor-body">
        <div class="field">
          <label>Audiotype 索引</label>
          <input v-model.number="audiotype" type="number" min="2" :disabled="!connected" />
        </div>
        <div class="row-actions">
          <button class="btn" type="button" :disabled="!connected" @click="setAudiotype">切换状态</button>
        </div>
        </div>
      </section>
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
const audioInput = ref(null)
const sessionid = ref('')
const refAudio = ref('')
const refText = ref('')
const uploading = ref(false)
const recording = ref(false)
const recReady = ref(false)
const audiotype = ref(2)
const listening = ref(false)
const recognizing = ref(false)
let pc = null
let interruptFlashTimer = null
let toastTimer = null
let asrWs = null
let asrStream = null
let asrCtx = null
let asrProcessor = null
let asrSource = null
let asrResultWaiter = null

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
    const offerBody = {
      sdp: local.sdp,
      type: local.type,
      avatar: avatarId.value,
    }
    if (refAudio.value.trim()) offerBody.refaudio = refAudio.value.trim()
    if (refText.value.trim()) offerBody.reftext = refText.value.trim()
    const res = await fetch('/offer', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(offerBody),
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
  await abortMic()
  connected.value = false
  if (pc) {
    pc.close()
    pc = null
  }
  if (remoteVideo.value) remoteVideo.value.srcObject = null
  if (remoteAudio.value) remoteAudio.value.srcObject = null
  sessionid.value = ''
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
    showToast('已送入音频')
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
    showToast('已切换动作')
  } catch (e) {
    error.value = e.message
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
