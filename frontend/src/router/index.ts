import { createRouter, createWebHistory } from 'vue-router'

// Use lazy loading for routes
const Dashboard = () => import('@/views/Dashboard.vue')
const KnowledgeQA = () => import('@/views/KnowledgeQA.vue')
const RealTimeDiagnosis = () => import('@/views/RealTimeDiagnosis.vue')
const SopConsole = () => import('@/views/SopConsole.vue')
const Settings = () => import('@/views/Settings.vue')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard,
      meta: { title: '仪表盘', icon: 'LayoutDashboard' }
    },
    {
      path: '/knowledge',
      name: 'knowledge',
      component: KnowledgeQA,
      meta: { title: '知识问答', icon: 'MessageCircle' }
    },
    {
      path: '/diagnosis',
      name: 'diagnosis',
      component: RealTimeDiagnosis,
      meta: { title: '实时诊断', icon: 'Activity' }
    },
    {
      path: '/sop',
      name: 'sop',
      component: SopConsole,
      meta: { title: 'SOP管理台', icon: 'BookOpen' }
    },
    {
      path: '/settings',
      name: 'settings',
      component: Settings,
      meta: { title: '设置', icon: 'Settings' }
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/'
    }
  ]
})

router.beforeEach((to) => {
  document.title = `${to.meta.title || 'SOPRCA'} - SOPRCA`
})

export default router
