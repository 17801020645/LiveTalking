<template>
  <div>
    <h2 class="page-title">Avatar 生成</h2>
    <div class="glass card">
      <p class="muted">从已接单的订单启动生成。没有视频的图+音频订单无法走现有抽帧管线。</p>
      <div class="field">
        <label>已接单订单</label>
        <select v-model.number="orderId">
          <option :value="0">请选择</option>
          <option v-for="o in accepted" :key="o.id" :value="o.id">
            #{{ o.id }} {{ o.username }} {{ o.has_video ? '有视频' : '无视频' }}
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
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../../api'

const orders = ref([])
const orderId = ref(0)
const avatarId = ref('')
const formError = ref('')
const okMsg = ref('')

const accepted = computed(() => orders.value.filter((o) => o.status === 'accepted'))

async function load() {
  const data = await api('/api/v1/admin/orders')
  orders.value = data.orders
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
