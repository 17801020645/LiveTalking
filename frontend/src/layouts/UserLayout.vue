<template>
  <div class="shell gallery">
    <a class="skip-link" href="#main-content">跳到主内容</a>
    <aside class="sidebar" aria-label="用户导航">
      <div class="brand">LiveTalking</div>
      <nav class="rail-nav">
        <router-link class="nav-link" to="/user">
          <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M4 11.5 12 5l8 6.5V20H4z" />
            <path d="M9.5 20v-6h5v6" />
          </svg>
          首页
        </router-link>
        <router-link class="nav-link" to="/user/assets">
          <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
            <rect x="4" y="5" width="16" height="14" rx="2" />
            <path d="M8 14.5 10.5 12l3 3 2-2 2.5 2.5" />
          </svg>
          我的资产
        </router-link>
        <router-link class="nav-link" to="/user/custom">
          <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 5v14M5 12h14" />
          </svg>
          定制数字人
        </router-link>
      </nav>
    </aside>
    <div class="main">
      <header class="topbar">
        <span class="topbar-user">{{ username }}</span>
        <PasswordForm />
        <button class="btn-ghost" type="button" @click="logout">退出</button>
      </header>
      <div class="content">
        <main id="main-content" tabindex="-1">
          <router-view />
        </main>
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
