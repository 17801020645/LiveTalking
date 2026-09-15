<template>
  <div class="gallery login-wrap">
    <section class="monitor-panel login-monitor" :class="{ 'is-fault': Boolean(error), 'is-program': loading }">
      <span class="tally" :class="error ? 'is-fault' : (loading ? 'is-program' : 'is-idle')" aria-hidden="true" />
      <p class="monitor-name">LiveTalking</p>
      <form class="monitor-body" @submit.prevent="submit">
        <p class="muted">登录后进入数字人工作台</p>
        <div class="field">
          <label>用户名</label>
          <input v-model="username" autocomplete="username" />
        </div>
        <div class="field">
          <label>密码</label>
          <input v-model="password" type="password" autocomplete="current-password" />
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button class="btn" type="submit" :disabled="loading">{{ loading ? '登录中…' : '登录' }}</button>
      </form>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { api } from '../api'

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const router = useRouter()
const route = useRoute()

function goHome(role) {
  router.replace(role === 'admin' ? '/admin' : '/user')
}

onMounted(async () => {
  try {
    const me = await api('/api/v1/auth/me')
    goHome(me.role)
  } catch {
    /* stay on login */
  }
})

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const me = await api('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username: username.value, password: password.value }),
    })
    const redirect = route.query.redirect
    if (typeof redirect === 'string' && redirect.startsWith('/')) {
      router.replace(redirect)
    } else {
      goHome(me.role)
    }
  } catch (e) {
    error.value = e.message || '用户名或密码错误'
  } finally {
    loading.value = false
  }
}
</script>
