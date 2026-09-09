import { createRouter, createWebHistory } from 'vue-router'
import { api } from '../api'
import Login from '../views/Login.vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import UserLayout from '../layouts/UserLayout.vue'
import AdminHome from '../views/admin/Home.vue'
import AdminAvatar from '../views/admin/Avatar.vue'
import AdminOps from '../views/admin/Ops.vue'
import AdminTts from '../views/admin/Tts.vue'
import UserHome from '../views/user/Home.vue'
import UserAssets from '../views/user/Assets.vue'
import UserCustom from '../views/user/Custom.vue'

export const router = createRouter({
  history: createWebHistory('/app/'),
  routes: [
    { path: '/login', component: Login, meta: { public: true } },
    {
      path: '/admin',
      component: AdminLayout,
      meta: { role: 'admin' },
      children: [
        { path: '', component: AdminHome },
        { path: 'avatar', component: AdminAvatar },
        { path: 'ops', component: AdminOps },
        { path: 'tts', component: AdminTts },
      ],
    },
    {
      path: '/user',
      component: UserLayout,
      meta: { role: 'user' },
      children: [
        { path: '', component: UserHome },
        { path: 'assets', component: UserAssets },
        { path: 'custom', component: UserCustom },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/login' },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.public) {
    return true
  }
  try {
    const me = await api('/api/v1/auth/me')
    if (to.meta.role && me.role !== to.meta.role) {
      return me.role === 'admin' ? '/admin' : '/user'
    }
    return true
  } catch {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
})
