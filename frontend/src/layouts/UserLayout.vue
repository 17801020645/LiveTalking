<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">LiveTalking</div>
      <router-link class="nav-link" to="/user">首页</router-link>
      <router-link class="nav-link" to="/user/assets">我的资产</router-link>
      <router-link class="nav-link" to="/user/custom">定制数字人</router-link>
    </aside>
    <div class="main">
      <header class="topbar">
        <span>{{ username }}</span>
        <PasswordForm />
        <button class="btn-ghost" type="button" @click="logout">退出</button>
      </header>
      <div class="content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import PasswordForm from '../components/PasswordForm.vue'

const username = ref('')
const router = useRouter()

onMounted(async () => {
  const me = await api('/api/v1/auth/me')
  username.value = me.username
})

async function logout() {
  await api('/api/v1/auth/logout', { method: 'POST' })
  router.replace('/login')
}
</script>
