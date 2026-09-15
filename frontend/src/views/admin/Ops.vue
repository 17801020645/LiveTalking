<template>
  <div class="deck">
    <h2 class="page-title">管理后台</h2>
    <section class="monitor-panel" :class="{ 'is-program': hasSubmitted }">
      <span class="tally" :class="hasSubmitted ? 'is-live' : 'is-idle'" aria-hidden="true" />
      <p class="monitor-name">定制订单</p>
      <div class="monitor-body">
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
    </section>

    <section class="monitor-panel">
      <span class="tally is-idle" aria-hidden="true" />
      <p class="monitor-name">创建普通用户</p>
      <div class="monitor-body">
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
    </section>

    <section class="monitor-panel" :class="{ 'is-program': Boolean(selected) }">
      <span class="tally" :class="selected ? 'is-program' : 'is-idle'" aria-hidden="true" />
      <p class="monitor-name">用户与订阅</p>
      <div class="monitor-body">
        <table class="table">
          <thead>
            <tr><th>用户</th><th>角色</th><th>状态</th><th>已绑定形象</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr
              v-for="u in users"
              :key="u.id"
              :class="{ 'is-selected': selected?.id === u.id }"
              @click="select(u)"
              style="cursor: pointer"
            >
              <td>{{ u.username }}</td>
              <td>{{ u.role }}</td>
              <td>{{ u.status }}</td>
              <td>{{ (subs[u.id] || []).map(s => s.avatar_id).join(', ') || '—' }}</td>
              <td class="row-actions">
                <button
                  v-if="u.role === 'user' && u.status === 'active'"
                  class="btn-danger"
                  type="button"
                  @click.stop="disableUser(u)"
                >禁用</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section v-if="selected && selected.role === 'user'" class="monitor-panel is-program">
      <span class="tally is-program" aria-hidden="true" />
      <p class="monitor-name">为 {{ selected.username }} 绑定形象</p>
      <div class="monitor-body">
        <div v-for="a in avatars" :key="a.avatar_id" class="row-actions">
          <label>
            <input type="checkbox" :checked="boundIds.has(a.avatar_id)" @change="toggle(a.avatar_id, $event.target.checked)" />
            {{ a.name }} <span class="muted">({{ a.avatar_id }} / {{ a.status }})</span>
          </label>
        </div>
      </div>
    </section>
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
const hasSubmitted = computed(() => orders.value.some((o) => o.status === 'submitted'))

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

async function disableUser(u) {
  if (!window.confirm(`禁用用户 ${u.username}？禁用后将无法登录。`)) return
  await api(`/api/v1/admin/users/${u.id}/disable`, { method: 'POST', body: '{}' })
  if (selected.value?.id === u.id) selected.value = { ...selected.value, status: 'disabled' }
  await load()
}
</script>
