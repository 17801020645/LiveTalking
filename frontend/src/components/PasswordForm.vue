<template>
  <div class="pw-wrap">
    <button class="btn-ghost" type="button" @click="open = !open">改密</button>
    <form v-if="open" class="glass card pw-panel" @submit.prevent="submit">
      <div class="field">
        <label>当前密码</label>
        <input v-model="currentPassword" type="password" autocomplete="current-password" />
      </div>
      <div class="field">
        <label>新密码</label>
        <input v-model="newPassword" type="password" autocomplete="new-password" />
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="ok" class="muted">已更新</p>
      <div class="row-actions">
        <button class="btn" type="submit" :disabled="saving">{{ saving ? '保存中…' : '保存' }}</button>
        <button class="btn-ghost" type="button" @click="open = false">取消</button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { api } from '../api'

const open = ref(false)
const currentPassword = ref('')
const newPassword = ref('')
const error = ref('')
const ok = ref(false)
const saving = ref(false)

async function submit() {
  error.value = ''
  ok.value = false
  saving.value = true
  try {
    await api('/api/v1/auth/password', {
      method: 'POST',
      body: JSON.stringify({
        current_password: currentPassword.value,
        new_password: newPassword.value,
      }),
    })
    currentPassword.value = ''
    newPassword.value = ''
    ok.value = true
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}
</script>
