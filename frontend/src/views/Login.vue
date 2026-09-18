<template>
  <div class="gallery login-wrap">
    <section class="monitor-panel login-monitor" :class="{ 'is-fault': Boolean(error), 'is-program': loading }">
      <span class="tally" :class="error ? 'is-fault' : (loading ? 'is-program' : 'is-idle')" aria-hidden="true" />
      <p class="monitor-name">LiveTalking</p>
      <form v-if="!forgot" class="monitor-body" @submit.prevent="submit">
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
        <button class="btn-ghost" type="button" :disabled="loading" @click="openForgot">忘记密码</button>
      </form>
      <form v-else class="monitor-body" @submit.prevent="submitForgot">
        <p class="muted">凭管理员发放的一次性令牌重设密码</p>
        <div class="field">
          <label>用户名</label>
          <input v-model="username" autocomplete="username" />
        </div>
        <div class="field">
          <label>一次性令牌</label>
          <input v-model="token" autocomplete="one-time-code" />
        </div>
        <div class="field">
          <label>新密码</label>
          <input v-model="newPassword" type="password" autocomplete="new-password" />
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <p v-if="success" class="muted">{{ success }}</p>
        <button class="btn" type="submit" :disabled="loading">{{ loading ? '提交中…' : '重设密码' }}</button>
        <button class="btn-ghost" type="button" :disabled="loading" @click="closeForgot">返回登录</button>
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
const token = ref('')
const newPassword = ref('')
const forgot = ref(false)
const error = ref('')
const success = ref('')
const loading = ref(false)
const router = useRouter()
const route = useRoute()

function goHome(role) {
  router.replace(role === 'admin' ? '/admin' : '/user')
}

function openForgot() {
  forgot.value = true
  error.value = ''
  success.value = ''
  password.value = ''
}

function closeForgot() {
  forgot.value = false
  error.value = ''
  success.value = ''
  token.value = ''
  newPassword.value = ''
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

async function submitForgot() {
  error.value = ''
  success.value = ''
  loading.value = true
  try {
    await api('/api/v1/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({
        username: username.value,
        token: token.value,
        new_password: newPassword.value,
      }),
    })
    success.value = '请使用新密码登录'
    token.value = ''
    newPassword.value = ''
  } catch (e) {
    error.value = e.message || '重置失败'
  } finally {
    loading.value = false
  }
}
</script>
