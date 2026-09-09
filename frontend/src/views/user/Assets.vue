<template>
  <div>
    <h2 class="page-title">我的资产</h2>
    <div v-if="!avatars.length" class="glass empty">还没有订阅的数字人，请联系管理员绑定。</div>
    <div class="grid">
      <div v-for="a in avatars" :key="a.avatar_id" class="glass card">
        <img v-if="a.cover_url" class="cover" :src="a.cover_url" :alt="a.name" />
        <video v-else-if="a.preview_url" class="cover" :src="a.preview_url" muted loop controls playsinline />
        <div v-else class="cover" />
        <h3>{{ a.name }}</h3>
        <span v-if="a.is_published" class="badge">已发布</span>
        <div class="row-actions">
          <button v-if="!a.is_published" class="btn" type="button" @click="publish(a.avatar_id)">发布到首页</button>
          <button v-else class="btn-ghost" type="button" @click="unpublish(a.avatar_id)">取消发布</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../../api'

const avatars = ref([])

async function load() {
  const data = await api('/api/v1/me/avatars')
  avatars.value = data.avatars
}

onMounted(load)

async function publish(id) {
  await api(`/api/v1/me/avatars/${encodeURIComponent(id)}/publish`, { method: 'POST' })
  await load()
}

async function unpublish(id) {
  await api(`/api/v1/me/avatars/${encodeURIComponent(id)}/unpublish`, { method: 'POST' })
  await load()
}
</script>
