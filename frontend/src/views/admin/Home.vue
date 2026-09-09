<template>
  <div>
    <h2 class="page-title">首页</h2>
    <div class="glass card">
      <p>演示连麦仍使用原站点入口：<a href="/" target="_blank" rel="noopener">打开 /</a></p>
      <p class="muted">当前管理员：{{ username }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api'

const username = ref('')
onMounted(async () => {
  const me = await api('/api/v1/auth/me')
  username.value = me.username
})
</script>
