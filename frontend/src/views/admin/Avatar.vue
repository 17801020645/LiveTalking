<template>
  <div class="deck">
    <h2 class="page-title">Avatar 生成</h2>
    <section class="monitor-panel" :class="{ 'is-fault': Boolean(formError), 'is-program': Boolean(okMsg) }">
      <span class="tally" :class="formError ? 'is-fault' : (okMsg ? 'is-live' : 'is-idle')" aria-hidden="true" />
      <p class="monitor-name">启动生成</p>
      <div class="monitor-body">
        <p class="muted">从已接单的订单启动生成。视频与图+音频订单均可生成。</p>
        <div class="field">
          <label>已接单订单</label>
          <select v-model.number="orderId">
            <option :value="0">请选择</option>
            <option v-for="o in accepted" :key="o.id" :value="o.id">
              #{{ o.id }} {{ o.username }} {{ o.has_video ? '视频' : (o.has_image ? '图+音频' : '无素材') }}
            </option>
          </select>
        </div>
        <div class="field">
          <label>新 avatar_id</label>
          <input v-model="avatarId" placeholder="例如 user3_custom1" />
        </div>
        <p v-if="formError" class="error">{{ formError }}</p>
        <p v-if="okMsg" class="muted">{{ okMsg }}</p>
        <button class="btn" type="button" @click="generate">开始生成</button>
      </div>
    </section>
    <section class="monitor-panel" :class="{ 'is-warn': hasRunning }">
      <span class="tally" :class="hasRunning ? 'is-warn' : 'is-idle'" aria-hidden="true" />
      <p class="monitor-name">生成任务</p>
      <div class="monitor-body">
        <table class="table">
          <thead>
            <tr><th>任务</th><th>形象</th><th>状态</th><th>进度</th><th>说明</th></tr>
          </thead>
          <tbody>
            <tr v-for="t in tasks" :key="t.task_id">
              <td>{{ t.task_id.slice(0, 8) }}</td>
              <td>{{ t.avatar_id }}</td>
              <td>{{ t.status }}</td>
              <td>{{ t.progress }}%</td>
              <td>{{ t.error_msg || '—' }}</td>
            </tr>
          </tbody>
        </table>
        <p v-if="!tasks.length" class="muted">还没有任务记录。</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../../api'

const orders = ref([])
const tasks = ref([])
const orderId = ref(0)
const avatarId = ref('')
const formError = ref('')
const okMsg = ref('')

const accepted = computed(() => orders.value.filter((o) => o.status === 'accepted'))
const hasRunning = computed(() => tasks.value.some((t) => t.status === 'pending' || t.status === 'running'))

async function load() {
  const data = await api('/api/v1/admin/orders')
  orders.value = data.orders
  try {
    const listed = await api('/api/avatar/tasks')
    tasks.value = listed.tasks || []
  } catch {
    tasks.value = []
  }
}

onMounted(load)

async function generate() {
  formError.value = ''
  okMsg.value = ''
  try {
    if (!orderId.value) throw new Error('请选择订单')
    const data = await api(`/api/v1/admin/orders/${orderId.value}/generate`, {
      method: 'POST',
      body: JSON.stringify({ avatar_id: avatarId.value, model: 'wav2lip' }),
    })
    okMsg.value = `已提交任务 ${data.task_id}`
    await load()
  } catch (e) {
    formError.value = e.message
  }
}
</script>
