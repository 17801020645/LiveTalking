<template>
  <div>
    <h2 class="page-title">首页</h2>
    <p v-if="error" class="error">{{ error }}</p>
    <div class="stat-grid">
      <router-link class="glass card stat-card" to="/admin/ops">
        <p class="muted">待处理订单</p>
        <p class="stat-num">{{ stats.pending_orders }}</p>
        <p class="muted">状态为已提交，点击查看后台</p>
      </router-link>
      <div class="glass card stat-card">
        <p class="muted">活跃连麦</p>
        <p class="stat-num">{{ stats.active_sessions }}<span class="muted"> / {{ stats.max_sessions }}</span></p>
        <p class="muted">当前进程内会话</p>
      </div>
      <router-link class="glass card stat-card" to="/admin/avatar">
        <p class="muted">生成中任务</p>
        <p class="stat-num">{{ stats.running_tasks }}</p>
        <p class="muted">pending / running，点击查看生成页</p>
      </router-link>
    </div>
    <p class="muted">
      <router-link to="/admin/live">去演示连麦</router-link>
    </p>
    <p class="muted">当前管理员：{{ username }}</p>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../../api'

const username = ref('')
const error = ref('')
const stats = ref({
  pending_orders: 0,
  active_sessions: 0,
  max_sessions: 0,
  running_tasks: 0,
})

onMounted(async () => {
  try {
    const me = await api('/api/v1/auth/me')
    username.value = me.username
    stats.value = await api('/api/v1/admin/home')
  } catch (e) {
    error.value = e.message
  }
})
</script>
