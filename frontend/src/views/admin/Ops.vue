<template>
  <div>
    <h2 class="page-title">管理后台</h2>
    <div class="glass card" style="margin-bottom: 16px;">
      <h3>定制订单</h3>
      <table class="table">
        <thead>
          <tr><th>ID</th><th>用户</th><th>类型</th><th>状态</th><th>视频</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="o in orders" :key="o.id">
            <td>{{ o.id }}</td>
            <td>{{ o.username }}</td>
            <td>{{ o.material_type }}</td>
            <td>{{ o.status }}{{ o.reject_reason ? ' / ' + o.reject_reason : '' }}</td>
            <td>{{ o.has_video ? '有' : '无' }}</td>
            <td class="row-actions">
              <button v-if="o.status === 'submitted'" class="btn" type="button" @click="accept(o.id)">接单</button>
              <button v-if="['submitted','accepted','generating'].includes(o.status)" class="btn-danger" type="button" @click="reject(o.id)">驳回</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!orders.length" class="muted">暂无订单。</p>
    </div>

    <div class="glass card" style="margin-bottom: 16px;">
      <h3>创建普通用户</h3>
      <div class="field">
        <label>用户名</label>
        <input v-model="newUser" />
      </div>
      <div class="field">
        <label>初始密码</label>
        <input v-model="newPass" type="password" />
      </div>
      <p v-if="formError" class="error">{{ formError }}</p>
      <button class="btn" type="button" @click="createUser">创建</button>
    </div>

    <div class="glass card">
      <h3>用户与订阅</h3>
      <table class="table">
        <thead>
          <tr><th>用户</th><th>角色</th><th>状态</th><th>已绑定形象</th></tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id" @click="select(u)" :style="{ cursor: 'pointer', background: selected?.id === u.id ? 'rgba(67,97,238,0.08)' : '' }">
            <td>{{ u.username }}</td>
            <td>{{ u.role }}</td>
            <td>{{ u.status }}</td>
            <td>{{ (subs[u.id] || []).map(s => s.avatar_id).join(', ') || '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="selected && selected.role === 'user'" class="glass card" style="margin-top: 16px;">
      <h3>为 {{ selected.username }} 绑定形象</h3>
      <div v-for="a in avatars" :key="a.avatar_id" class="row-actions">
        <label>
          <input type="checkbox" :checked="boundIds.has(a.avatar_id)" @change="toggle(a.avatar_id, $event.target.checked)" />
          {{ a.name }} <span class="muted">({{ a.avatar_id }} / {{ a.status }})</span>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../../api'

const users = ref([])
const avatars = ref([])
const orders = ref([])
const subs = ref({})
const selected = ref(null)
const newUser = ref('')
const newPass = ref('')
const formError = ref('')

const boundIds = computed(() => new Set((subs.value[selected.value?.id] || []).map((s) => s.avatar_id)))

async function load() {
  const u = await api('/api/v1/admin/users')
  users.value = u.users
  const a = await api('/api/v1/admin/avatars')
  avatars.value = a.avatars
  const o = await api('/api/v1/admin/orders')
  orders.value = o.orders
  const next = {}
  for (const user of users.value) {
    if (user.role !== 'user') continue
    const s = await api(`/api/v1/admin/users/${user.id}/subscriptions`)
    next[user.id] = s.subscriptions
  }
  subs.value = next
}

onMounted(load)

function select(u) {
  selected.value = u
}

async function createUser() {
  formError.value = ''
  try {
    await api('/api/v1/admin/users', {
      method: 'POST',
      body: JSON.stringify({ username: newUser.value, password: newPass.value }),
    })
    newUser.value = ''
    newPass.value = ''
    await load()
  } catch (e) {
    formError.value = e.message
  }
}

async function toggle(avatarId, checked) {
  const uid = selected.value.id
  if (checked) {
    await api(`/api/v1/admin/users/${uid}/subscriptions`, {
      method: 'POST',
      body: JSON.stringify({ avatar_id: avatarId }),
    })
  } else {
    await api(`/api/v1/admin/users/${uid}/subscriptions/${encodeURIComponent(avatarId)}`, {
      method: 'DELETE',
    })
  }
  const s = await api(`/api/v1/admin/users/${uid}/subscriptions`)
  subs.value = { ...subs.value, [uid]: s.subscriptions }
}

async function accept(id) {
  await api(`/api/v1/admin/orders/${id}/accept`, { method: 'POST', body: '{}' })
  await load()
}

async function reject(id) {
  const reason = window.prompt('驳回原因')
  if (!reason) return
  await api(`/api/v1/admin/orders/${id}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  })
  await load()
}
</script>
