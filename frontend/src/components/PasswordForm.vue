<template>
  <div class="pw-wrap">
    <button class="btn-ghost" type="button" @click="open = !open">改密</button>
    <form v-if="open" class="monitor-panel pw-panel" :class="{ 'is-fault': Boolean(error), 'is-program': ok }" @submit.prevent="submit">
      <span class="tally" :class="error ? 'is-fault' : (ok ? 'is-live' : 'is-idle')" aria-hidden="true" />
      <p class="monitor-name">改密</p>
      <div class="monitor-body">
        <div class="field">
          <label for="pw-current">当前密码</label>
          <input id="pw-current" v-model="currentPassword" type="password" autocomplete="current-password" :aria-invalid="Boolean(error)" :aria-describedby="error || ok ? 'pw-status' : undefined" />
        </div>
        <div class="field">
          <label for="pw-new">新密码</label>
          <input id="pw-new" v-model="newPassword" type="password" autocomplete="new-password" :aria-invalid="Boolean(error)" :aria-describedby="error || ok ? 'pw-status' : undefined" />
        </div>
        <p v-if="error" id="pw-status" class="error" role="alert">{{ error }}</p>
        <p v-else-if="ok" id="pw-status" class="muted" role="status">已更新</p>
        <div class="row-actions">
          <button class="btn" type="submit" :disabled="saving">{{ saving ? '保存中…' : '保存' }}</button>
          <button class="btn-ghost" type="button" @click="open = false">取消</button>
        </div>
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
