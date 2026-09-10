<template>
  <div>
    <h2 class="page-title">TTS 语音管理</h2>
    <div class="glass card" style="margin-bottom: 16px;">
      <p>
        经本机 8010 代理 Omni，无需在浏览器填写上游地址。
        本机调试仍可打开原页 <a href="/tts/index.html" target="_blank" rel="noopener">/tts/</a>。
      </p>
      <p class="muted">状态：{{ statusText }}</p>
      <p v-if="formError" class="error">{{ formError }}</p>
      <div class="row-actions">
        <button class="btn" type="button" :disabled="busy" @click="refresh">刷新音色</button>
      </div>
    </div>

    <div class="glass card" style="margin-bottom: 16px;">
      <h3>音色列表</h3>
      <table class="table">
        <thead>
          <tr><th>名称</th><th>类型</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="v in presetVoices" :key="'p-' + v">
            <td>{{ v }}</td>
            <td>预设</td>
            <td><button class="btn-ghost" type="button" @click="voice = v">选用</button></td>
          </tr>
          <tr v-for="v in uploadedVoices" :key="'u-' + v.name">
            <td>{{ v.name }}</td>
            <td>已上传</td>
            <td class="row-actions">
              <button class="btn-ghost" type="button" @click="voice = v.name">选用</button>
              <button class="btn-danger" type="button" @click="removeVoice(v.name)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!presetVoices.length && !uploadedVoices.length" class="muted">还没有音色，或上游未连接。</p>
    </div>

    <div class="glass card" style="margin-bottom: 16px;">
      <h3>合成试听</h3>
      <div class="field">
        <label>音色</label>
        <input v-model="voice" placeholder="例如 vivian" />
      </div>
      <div class="field">
        <label>文本</label>
        <textarea v-model="text" placeholder="输入要合成的中文"></textarea>
      </div>
      <div class="field">
        <label>语速</label>
        <input v-model.number="speed" type="number" min="0.5" max="2" step="0.1" />
      </div>
      <button class="btn" type="button" :disabled="busy" @click="synthesize">合成</button>
      <audio v-if="audioUrl" :src="audioUrl" controls style="display:block; margin-top: 12px; width: 100%;"></audio>
    </div>

    <div class="glass card">
      <h3>上传克隆音色</h3>
      <div class="field">
        <label>音频</label>
        <input type="file" accept="audio/*" @change="audioFile = $event.target.files[0]" />
      </div>
      <div class="field">
        <label>名称</label>
        <input v-model="cloneName" />
      </div>
      <div class="field">
        <label>参考文本</label>
        <textarea v-model="refText" placeholder="与音频内容一致的文本"></textarea>
      </div>
      <p class="muted">上游若未部署 Base 克隆模型，上传会失败并显示原因。</p>
      <button class="btn" type="button" :disabled="busy" @click="upload">上传</button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { api, apiBlob, apiUpload } from '../../api'

const formError = ref('')
const busy = ref(false)
const connected = ref(false)
const voices = ref([])
const uploaded = ref([])
const voice = ref('')
const text = ref('你好，这是 LiveTalking 语音试听。')
const speed = ref(1)
const audioUrl = ref('')
const audioFile = ref(null)
const cloneName = ref('')
const refText = ref('')

const presetVoices = computed(() => voices.value)
const uploadedVoices = computed(() => uploaded.value)
const statusText = computed(() => {
  if (busy.value) return '处理中…'
  if (connected.value) return '上游已连接'
  return '上游不可用'
})

function clearAudio() {
  if (audioUrl.value) URL.revokeObjectURL(audioUrl.value)
  audioUrl.value = ''
}

onUnmounted(clearAudio)

async function refresh() {
  formError.value = ''
  busy.value = true
  try {
    const data = await api('/api/v1/admin/tts/voices')
    voices.value = data.voices || []
    uploaded.value = data.uploaded_voices || []
    connected.value = true
    if (!voice.value && voices.value.length) voice.value = voices.value[0]
  } catch (e) {
    connected.value = false
    voices.value = []
    uploaded.value = []
    formError.value = e.message
  } finally {
    busy.value = false
  }
}

async function synthesize() {
  formError.value = ''
  if (!voice.value) {
    formError.value = '请选择音色'
    return
  }
  if (!text.value.trim()) {
    formError.value = '请输入文本'
    return
  }
  busy.value = true
  try {
    clearAudio()
    const blob = await apiBlob('/api/v1/admin/tts/speech', {
      method: 'POST',
      body: JSON.stringify({
        input: text.value.trim(),
        voice: voice.value,
        response_format: 'mp3',
        speed: speed.value || 1,
        language: 'Auto',
        task_type: 'CustomVoice',
      }),
    })
    audioUrl.value = URL.createObjectURL(blob)
  } catch (e) {
    formError.value = e.message
  } finally {
    busy.value = false
  }
}

async function upload() {
  formError.value = ''
  if (!audioFile.value) {
    formError.value = '请选择音频'
    return
  }
  if (!cloneName.value.trim()) {
    formError.value = '请输入名称'
    return
  }
  if (!refText.value.trim()) {
    formError.value = '请填写参考文本'
    return
  }
  busy.value = true
  try {
    const form = new FormData()
    form.append('audio_sample', audioFile.value)
    form.append('name', cloneName.value.trim())
    form.append('consent', `consent_${Date.now()}`)
    form.append('ref_text', refText.value.trim())
    await apiUpload('/api/v1/admin/tts/voices', form)
    cloneName.value = ''
    refText.value = ''
    await refresh()
  } catch (e) {
    formError.value = e.message
  } finally {
    busy.value = false
  }
}

async function removeVoice(name) {
  if (!confirm(`确定删除音色 ${name}？`)) return
  formError.value = ''
  busy.value = true
  try {
    await api(`/api/v1/admin/tts/voices/${encodeURIComponent(name)}`, { method: 'DELETE' })
    await refresh()
  } catch (e) {
    formError.value = e.message
  } finally {
    busy.value = false
  }
}

onMounted(refresh)
</script>
