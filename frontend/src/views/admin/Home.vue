<template>
  <div class="gallery-home">
    <p v-if="error" class="error">{{ error }}</p>
    <div class="monitor-wall" :class="{ 'is-loading': loading }">
      <router-link
        class="monitor"
        :class="{ 'is-program': isProgram('orders'), 'is-fault': Boolean(error) }"
        to="/admin/ops"
      >
        <span class="tally" :class="tallyClass('orders')" aria-hidden="true" />
        <p class="monitor-name">待处理订单</p>
        <p class="monitor-count">
          <span class="count-num">{{ display(stats.pending_orders) }}</span>
        </p>
        <p class="monitor-cap">状态为已提交，点击查看后台</p>
      </router-link>
      <router-link
        class="monitor"
        :class="{ 'is-program': isProgram('live'), 'is-fault': Boolean(error) }"
        to="/admin/live"
      >
        <span class="tally" :class="tallyClass('live')" aria-hidden="true" />
        <p class="monitor-name">活跃连麦</p>
        <p class="monitor-count">
          <span class="count-num">{{ display(stats.active_sessions) }}</span>
          <span class="count-den">/{{ display(stats.max_sessions) }}</span>
        </p>
        <p class="monitor-cap">当前进程内会话</p>
      </router-link>
      <router-link
        class="monitor"
        :class="{ 'is-program': isProgram('gen'), 'is-fault': Boolean(error) }"
        to="/admin/avatar"
      >
        <span class="tally" :class="tallyClass('gen')" aria-hidden="true" />
        <p class="monitor-name">生成中任务</p>
        <p class="monitor-count">
          <span class="count-num">{{ display(stats.running_tasks) }}</span>
        </p>
        <p class="monitor-cap">pending / running，点击查看生成页</p>
      </router-link>
    </div>
    <router-link class="program-cut" to="/admin/live">
      <svg class="cut-icon" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="6" cy="12" r="2.2" />
        <circle cx="18" cy="7" r="2.2" />
        <circle cx="18" cy="17" r="2.2" />
        <path d="M8.2 12h7.6M8.8 13.2l6.8 3.1M8.8 10.8l6.8-3.1" />
      </svg>
      去演示连麦
    </router-link>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../../api'

const error = ref('')
const loading = ref(true)
const stats = ref({
  pending_orders: 0,
  active_sessions: 0,
  max_sessions: 0,
  running_tasks: 0,
})

function display(value) {
  return loading.value ? '—' : value
}

function isProgram(kind) {
  if (error.value) return false
  if (kind === 'live') return stats.value.active_sessions > 0
  return false
}

function tallyClass(kind) {
  if (error.value) return 'is-fault'
  if (kind === 'orders') return stats.value.pending_orders > 0 ? 'is-live' : 'is-idle'
  if (kind === 'live') return stats.value.active_sessions > 0 ? 'is-program' : 'is-idle'
  if (kind === 'gen') return stats.value.running_tasks > 0 ? 'is-warn' : 'is-idle'
  return 'is-idle'
}

onMounted(async () => {
  try {
    stats.value = await api('/api/v1/admin/home')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})
</script>
