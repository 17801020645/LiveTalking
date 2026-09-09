<template>
  <div>
    <h2 class="page-title">首页</h2>
    <div v-if="published" class="glass card" style="max-width: 420px;">
      <img v-if="published.cover_url" class="cover" :src="published.cover_url" :alt="published.name" />
      <video v-else-if="published.preview_url" class="cover" :src="published.preview_url" muted loop autoplay playsinline />
      <div v-else class="cover" />
      <h3>{{ published.name }}</h3>
      <p class="muted">当前发布到首页的数字人。连麦将在后续版本开放。</p>
    </div>
    <div v-else class="glass empty">
      还没有发布数字人，请到「我的资产」选择一个并发布。
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../../api'

const published = ref(null)
onMounted(async () => {
  const data = await api('/api/v1/me/home')
  published.value = data.published
})
</script>
