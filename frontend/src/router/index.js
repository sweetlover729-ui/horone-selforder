import { createRouter, createWebHistory } from 'vue-router'
import { useCustomerStore } from '@/stores/customer'
import IndexView from '@/views/client/Index.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/client/Login.vue'),
    meta: { requiresAuth: false, title: '登录' },
  },
  {
    path: '/',
    name: 'Index',
    component: IndexView,
    meta: { requiresAuth: false, title: '首页' },
  },

  {
    path: '/order/create',
    name: 'OrderCreate',
    component: () => import('@/views/client/OrderCreate.vue'),
    meta: { requiresAuth: true, title: '下单' },
  },
  {
    path: '/orders',
    name: 'OrderList',
    component: () => import('@/views/client/OrderList.vue'),
    meta: { requiresAuth: true, title: '我的订单' },
  },
  {
    path: '/order/:id',
    name: 'OrderDetail',
    component: () => import('@/views/client/OrderDetail.vue'),
    meta: { requiresAuth: true, title: '订单详情' },
  },
  {
    path: '/order/:id/tracking',
    name: 'OrderTracking',
    component: () => import('@/views/client/OrderTracking.vue'),
    meta: { requiresAuth: true, title: '订单追踪' },
  },
  // 管理后台入口
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('@/views/client/AdminLogin.vue'),
    meta: { requiresAuth: false, title: '管理登录' },
  },
  // 管理后台（通过 iframe 嵌入 console）
  {
    path: '/admin/:pathMatch(.*)*',
    name: 'Admin',
    component: () => import('@/views/client/AdminFrame.vue'),
    meta: { requiresAuth: false, title: '管理后台' },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    return { top: 0 }
  },
})

router.beforeEach((to, from, next) => {
  const customerStore = useCustomerStore()
  if (to.meta.requiresAuth && !customerStore.isLoggedIn) {
    next({ path: '/login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router
