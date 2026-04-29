import { createRouter, createWebHistory } from 'vue-router'
import { useStaffStore } from '@/stores/staff'
import { ElMessage } from 'element-plus'

const routes = [
  // 登录页
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  // 默认重定向
  {
    path: '/',
    redirect: () => {
      const store = useStaffStore()
      return store.isAdmin() ? '/admin' : '/tech'
    }
  },
  // 管理后台
  {
    path: '/admin',
    component: () => import('@/views/Layout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      { path: '', name: 'Dashboard', component: () => import('@/views/Dashboard.vue') },
      { path: 'orders', name: 'OrderList', component: () => import('@/views/orders/OrderList.vue') },
      { path: 'orders/:id', name: 'OrderDetail', component: () => import('@/views/orders/OrderDetail.vue') },
      { path: 'statistics', name: 'Statistics', component: () => import('@/views/admin/Statistics.vue') },
      { path: 'hub', name: 'DataHub', component: () => import('@/views/admin/DataHub.vue') },
      { path: 'data-center', name: 'DataCenter', component: () => import('@/views/admin/DataCenter.vue') },
      { path: 'types', name: 'ProductTypes', component: () => import('@/views/admin/ProductTypes.vue') },
      { path: 'categories', name: 'Categories', component: () => import('@/views/admin/Categories.vue') },
      { path: 'brands', name: 'Brands', component: () => import('@/views/admin/Brands.vue') },
      { path: 'models', name: 'Models', component: () => import('@/views/admin/Models.vue') },
      { path: 'services', name: 'ServiceTypes', component: () => import('@/views/admin/ServiceTypes.vue') },
      { path: 'items', name: 'ServiceItems', component: () => import('@/views/admin/ServiceItems.vue') },
      { path: 'prices', name: 'PriceConfig', component: () => import('@/views/admin/PriceConfig.vue') },
      { path: 'customers', name: 'Customers', component: () => import('@/views/admin/Customers.vue') },
      { path: 'staff', name: 'Staff', component: () => import('@/views/admin/Staff.vue') },
      { path: 'profile', name: 'Profile', component: () => import('@/views/Profile.vue') },
      { path: 'simulate', name: 'SimulateFlow', component: () => import('@/views/admin/SimulateFlow.vue') }
    ]
  },
  // 技术员移动端
  {
    path: '/tech',
    component: () => import('@/views/tech/TechLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', name: 'TechOrders', component: () => import('@/views/tech/TechOrders.vue') },
      { path: 'order/:id', name: 'TechWorkflow', component: () => import('@/views/tech/TechWorkflow.vue') }
    ]
  }
]

const router = createRouter({
  history: createWebHistory('/admin'),
  routes
})

router.beforeEach((to, from, next) => {
  const store = useStaffStore()
  
  if (to.meta.requiresAuth !== false && !store.isLoggedIn()) {
    next('/login')
    return
  }
  
  if (to.meta.requiresAdmin && !store.isAdmin()) {
    ElMessage.error('没有权限访问此页面')
    next('/tech')
    return
  }
  
  if (to.path === '/login' && store.isLoggedIn()) {
    next(store.isAdmin() ? '/admin' : '/tech')
    return
  }
  
  next()
})

export default router
