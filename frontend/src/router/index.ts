import { createRouter, createWebHistory } from 'vue-router'
import LandingView from '@/views/LandingView.vue'
import DashboardView from '@/views/DashboardView.vue'
import AnalyticsView from '@/views/AnalyticsView.vue'
import NewsView from '@/views/NewsView.vue'
import CryptoDetailView from '@/views/CryptoDetailView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'landing',
      component: LandingView,
      meta: { title: 'Welcome', layout: 'none' },
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView,
      meta: { title: 'Dashboard' },
    },
    {
      path: '/crypto/:symbol',
      name: 'crypto-detail',
      component: CryptoDetailView,
      meta: { title: 'Crypto Details' },
    },
    {
      path: '/analytics',
      name: 'analytics',
      component: AnalyticsView,
      meta: { title: 'Analytics' },
    },
    {
      path: '/news',
      name: 'news',
      component: NewsView,
      meta: { title: 'News & Social' },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
  scrollBehavior(to, from, savedPosition) {
    // Always scroll to top on navigation
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0, behavior: 'smooth' }
    }
  },
})

// Update document title on route change
router.beforeEach((to, from, next) => {
  const title = to.meta.title as string
  document.title = title ? `${title} - CRYPTO VIZ` : 'CRYPTO VIZ'
  next()
})

export default router
