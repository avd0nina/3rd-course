import { createRouter, createWebHistory } from 'vue-router'
import LoginPage from './pages/LoginPage.vue'
import TablesPage from './pages/TablesPage.vue'
import ReportsPage from './pages/ReportsPage.vue'
import NotFoundPage from './pages/NotFoundPage.vue'
import { getAuthToken } from './shared/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/tables' },
    { path: '/login', name: 'login', component: LoginPage },
    { path: '/tables', name: 'tables', component: TablesPage },
    { path: '/reports', name: 'reports', component: ReportsPage },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundPage },
  ],
})

router.beforeEach(to => {
  const token = getAuthToken()
  if (!token && to.name !== 'login') {
    return { name: 'login' }
  }
  if (token && to.name === 'login') {
    return { name: 'tables' }
  }
  return true
})

export default router
