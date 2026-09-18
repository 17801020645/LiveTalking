<template>
  <div class="shell gallery">
    <a class="skip-link" href="#main-content">跳到主内容</a>
    <aside class="sidebar" aria-label="管理导航">
      <div class="brand">LiveTalking</div>
      <nav class="rail-nav">
        <router-link class="nav-link" to="/admin">
          <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M5 20V11M12 20V4M19 20V13" />
          </svg>
          首页
        </router-link>
        <router-link class="nav-link" to="/admin/live">
          <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="6" cy="12" r="2.2" />
            <circle cx="18" cy="7" r="2.2" />
            <circle cx="18" cy="17" r="2.2" />
            <path d="M8.2 12h7.6M8.8 13.2l6.8 3.1M8.8 10.8l6.8-3.1" />
          </svg>
          演示连麦
        </router-link>
        <router-link class="nav-link" to="/admin/avatar">
          <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="8" r="3.2" />
            <path d="M5.5 19.2c1.2-3.2 3.4-4.8 6.5-4.8s5.3 1.6 6.5 4.8" />
          </svg>
          Avatar 生成
        </router-link>
        <router-link class="nav-link" to="/admin/ops">
          <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 3.5 19 7v5.2c0 4.3-2.8 7.3-7 8.8-4.2-1.5-7-4.5-7-8.8V7z" />
          </svg>
          管理后台
        </router-link>
        <router-link class="nav-link" to="/admin/tts">
          <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M4 12h2.2l2-4 3.2 8 2.4-4.8H20" />
          </svg>
          TTS 语音管理
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
