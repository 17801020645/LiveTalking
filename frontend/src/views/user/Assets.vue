<template>
  <div class="deck">
    <h2 class="page-title">我的资产</h2>
    <section v-if="!avatars.length" class="monitor-panel">
      <span class="tally is-idle" aria-hidden="true" />
      <p class="monitor-name">订阅形象</p>
      <div class="monitor-body">
        <p class="muted">还没有订阅的数字人，请联系管理员绑定。</p>
      </div>
    </section>
    <div v-else class="grid">
      <section
        v-for="a in avatars"
        :key="a.avatar_id"
        class="monitor-panel"
        :class="{ 'is-program': a.is_published }"
      >
        <span class="tally" :class="a.is_published ? 'is-program' : 'is-idle'" aria-hidden="true" />
        <p class="monitor-name">{{ a.name }}</p>
        <div class="monitor-body">
          <video
            v-if="a.preview_url"
            class="cover"
            :src="a.preview_url"
            :poster="a.cover_url || undefined"
            muted
            loop
            autoplay
            playsinline
          />
          <img v-else-if="a.cover_url" class="cover" :src="a.cover_url" :alt="a.name" />
          <div v-else class="cover" />
          <span v-if="a.is_published" class="badge">已发布</span>
          <div class="row-actions">
            <button v-if="!a.is_published" class="btn" type="button" @click="publish(a.avatar_id)">发布到首页</button>
            <button v-else class="btn-ghost" type="button" @click="unpublish(a.avatar_id)">取消发布</button>
          </div>
        </div>
      </section>
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
