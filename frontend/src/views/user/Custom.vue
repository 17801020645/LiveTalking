<template>
  <div>
    <h2 class="page-title">定制数字人</h2>
    <div class="glass card" style="margin-bottom: 16px;">
      <div class="field">
        <label>素材类型</label>
        <select v-model="materialType">
          <option value="video">视频</option>
          <option value="image_audio">图片 + 音频</option>
        </select>
      </div>
      <div v-if="materialType === 'video'" class="field">
        <label>视频</label>
        <input type="file" accept="video/*" @change="video = $event.target.files[0]" />
      </div>
      <template v-else>
        <div class="field">
          <label>图片</label>
          <input type="file" accept="image/*" @change="image = $event.target.files[0]" />
        </div>
        <div class="field">
          <label>音频</label>
          <input type="file" accept="audio/*" @change="audio = $event.target.files[0]" />
        </div>
      </template>
      <div class="field">
        <label>文字说明</label>
        <input v-model="scriptText" placeholder="形象、音色或口播文案说明" />
      </div>
      <p v-if="formError" class="error">{{ formError }}</p>
      <button class="btn" type="button" :disabled="submitting" @click="submit">{{ submitting ? '提交中…' : '提交订单' }}</button>
    </div>

    <div class="glass card">
      <h3>我的订单</h3>
      <table class="table">
        <thead>
          <tr><th>ID</th><th>类型</th><th>状态</th><th>说明</th></tr>
        </thead>
        <tbody>
          <tr v-for="o in orders" :key="o.id">
            <td>{{ o.id }}</td>
            <td>{{ o.material_type }}</td>
            <td>{{ statusLabel(o) }}</td>
            <td>{{ o.reject_reason || o.script_text || '—' }}</td>
          </tr>
        </tbody>
      </table>
      <p v-if="!orders.length" class="muted">还没有订单。</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { api, apiUpload } from '../../api'

const materialType = ref('video')
const video = ref(null)
const image = ref(null)
const audio = ref(null)
const scriptText = ref('')
const formError = ref('')
const submitting = ref(false)
const orders = ref([])

const labels = {
  submitted: '已提交',
  accepted: '已接单',
  generating: '生成中',
  completed: '已交付',
  rejected: '已驳回',
}

function statusLabel(o) {
  const base = labels[o.status] || o.status
  if (o.status === 'rejected' && o.reject_reason) return `${base}：${o.reject_reason}`
  if (o.result_avatar_id) return `${base}（${o.result_avatar_id}）`
  return base
}

async function load() {
  const data = await api('/api/v1/me/orders')
  orders.value = data.orders
}

onMounted(load)

async function submit() {
  formError.value = ''
  submitting.value = true
  try {
    const fd = new FormData()
    fd.append('material_type', materialType.value)
    fd.append('script_text', scriptText.value)
    if (materialType.value === 'video') {
      if (!video.value) throw new Error('请选择视频')
      fd.append('video', video.value)
    } else {
      if (!image.value || !audio.value) throw new Error('请上传图片和音频')
      fd.append('image', image.value)
      fd.append('audio', audio.value)
    }
    await apiUpload('/api/v1/me/orders', fd)
    scriptText.value = ''
    await load()
  } catch (e) {
    formError.value = e.message
  } finally {
    submitting.value = false
  }
}
</script>
