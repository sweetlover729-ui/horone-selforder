<template>
  <div class="app-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed }">
      <!-- Logo -->
      <div class="sidebar-header">
        <div class="sidebar-logo">
          <div class="logo-icon">H</div>
          <div v-if="!collapsed" class="logo-text">
            <div class="logo-name">HORONE</div>
            <div class="logo-sub">管理后台</div>
          </div>
        </div>
      </div>

      <!-- 导航 -->
      <nav class="sidebar-nav">
        <!-- 仪表盘 -->
        <div
          class="nav-item"
          :class="{ active: isActivePath('/admin') }"
          @click="goTo('/admin')"
        >
          <svg class="nav-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="13" width="18" height="8" rx="2"/><rect x="3" y="3" width="18" height="8" rx="2"/></svg>
          <span v-if="!collapsed" class="nav-label">仪表盘</span>
        </div>

        <!-- 订单管理 -->
        <div class="nav-group">
          <div
            class="nav-item nav-parent"
            :class="{ active: isGroupActive('orders'), expanded: expandedKeys.includes('orders') }"
            @click="toggleGroup('orders')"
          >
            <svg class="nav-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
            <span v-if="!collapsed" class="nav-label">订单管理</span>
            <span v-if="!collapsed" class="nav-arrow">{{ expandedKeys.includes('orders') ? '-' : '+' }}</span>
          </div>
          <div v-if="!collapsed && expandedKeys.includes('orders')" class="nav-children">
            <div class="nav-child" :class="{ active: route.path === '/admin/orders' }" @click="goTo('/admin/orders')">全部订单</div>
            <div class="nav-child" :class="{ active: route.path.includes('/admin/orders') && currentStatus === 'paid' }" @click="goTo('/admin/orders?status=paid')">待收货</div>
            <div class="nav-child" :class="{ active: route.path.includes('/admin/orders') && currentStatus === 'repairing' }" @click="goTo('/admin/orders?status=repairing')">维修中</div>
            <div class="nav-child" :class="{ active: route.path.includes('/admin/orders') && currentStatus === 'ready' }" @click="goTo('/admin/orders?status=ready')">待回寄</div>
            <div class="nav-child" :class="{ active: route.path.includes('/admin/orders') && currentStatus === 'completed' }" @click="goTo('/admin/orders?status=completed')">已完成</div>
          </div>
        </div>

        <!-- 统计报表 -->
        <div
          class="nav-item"
          :class="{ active: route.path === '/admin/statistics' }"
          @click="goTo('/admin/statistics')"
        >
          <svg class="nav-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/>
            <line x1="6" y1="20" x2="6" y2="14"/>
          </svg>
          <span v-if="!collapsed" class="nav-label">统计报表</span>
        </div>

        <!-- 数据管理 -->
        <div
          class="nav-item"
          :class="{ active: route.path === '/admin/data-center' }"
          @click="goTo('/admin/data-center')"
        >
          <svg class="nav-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
          <span v-if="!collapsed" class="nav-label">数据管理</span>
        </div>



        <!-- 客户管理 -->
        <div
          class="nav-item"
          :class="{ active: route.path === '/admin/customers' }"
          @click="goTo('/admin/customers')"
        >
          <svg class="nav-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          <span v-if="!collapsed" class="nav-label">客户管理</span>
        </div>

        <!-- 员工管理 -->
        <div
          class="nav-item"
          :class="{ active: route.path === '/admin/staff' }"
          @click="goTo('/admin/staff')"
        >
          <svg class="nav-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          <span v-if="!collapsed" class="nav-label">员工管理</span>
        </div>

        <!-- 模拟流程 -->
        <div
          class="nav-item"
          :class="{ active: route.path === '/admin/simulate' }"
          @click="goTo('/admin/simulate')"
        >
          <svg class="nav-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          <span v-if="!collapsed" class="nav-label">模拟流程</span>
        </div>

        <!-- 账号设置 -->
        <div
          class="nav-item"
          :class="{ active: route.path === '/admin/profile' }"
          @click="goTo('/admin/profile')"
        >
          <svg class="nav-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51-1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          <span v-if="!collapsed" class="nav-label">账号设置</span>
        </div>
      </nav>

      <!-- 底部用户区 -->
      <div class="sidebar-footer">
        <div v-if="!collapsed" class="user-panel">
          <div class="user-avatar">{{ userInitial }}</div>
          <div class="user-info">
            <div class="user-name">{{ userName }}</div>
            <div class="user-role">{{ userRole }}</div>
          </div>
          <button class="logout-btn" @click="logout">退出</button>
        </div>
        <div class="collapse-btn" @click="collapsed = !collapsed">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
            <path v-if="collapsed" d="M9 18l6-6-6-6"/>
            <path v-else d="M15 18l-6-6 6-6"/>
          </svg>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <div class="main-area">
      <!-- 顶部栏 -->
      <header class="topbar">
        <div class="topbar-left">
          <h1 class="page-title">{{ pageTitle }}</h1>
        </div>
        <div class="topbar-right">
          <span class="current-time">{{ currentTime }}</span>
        </div>
      </header>

      <!-- 内容 -->
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useStaffStore } from '@/stores/staff'

const router = useRouter()
const route = useRoute()
const staffStore = useStaffStore()

const collapsed = ref(false)
const expandedKeys = ref(['orders'])
const currentTime = ref('')
const currentStatus = ref('')

const userInitial = computed(() => {
  const name = staffStore.userInfo?.fullName || staffStore.userInfo?.username || 'U'
  return name.charAt(0).toUpperCase()
})
const userName = computed(() => staffStore.userInfo?.fullName || staffStore.userInfo?.username || '用户')
const userRole = computed(() => {
  const map = { admin: '管理员', technician: '维修技师', staff: '员工' }
  return map[staffStore.userInfo?.role] || '员工'
})

const pageTitle = computed(() => {
  const p = route.path
  if (p === '/admin' || p === '/admin/') return '仪表盘'
  if (p.includes('/admin/orders') && !p.includes('/admin/orders/')) return '订单管理'
  if (p.match(/^\/admin\/orders\/\d+$/)) return '订单详情'
  if (p === '/admin/hub') return '数据管理'
  if (p.startsWith('/admin/data-center')) return '数据管理'
  if (p === '/admin/types') return '产品类别'
  if (p === '/admin/brands') return '品牌'
  if (p === '/admin/models') return '型号'
  if (p === '/admin/categories') return '产品类别'
  if (p === '/admin/services') return '服务管理'
  if (p === '/admin/items') return '服务项目'
  if (p === '/admin/special') return '专项服务'
  if (p === '/admin/prices') return '价格管理'
  if (p === '/admin/staff') return '员工管理'
  if (p === '/admin/profile') return '账号设置'
  return '仪表盘'
})

const isActivePath = (basePath) => {
  if (basePath === '/admin') return route.path === '/admin' || route.path === '/admin/'
  return route.path.startsWith(basePath)
}

const isGroupActive = (key) => {
  if (key === 'orders') return route.path.includes('/admin/orders')
  if (key === 'price') return route.path === '/admin/prices'
  return false
}

const toggleGroup = (key) => {
  const idx = expandedKeys.value.indexOf(key)
  if (idx >= 0) expandedKeys.value.splice(idx, 1)
  else expandedKeys.value.push(key)
}

const goTo = (path) => {
  // Extract status from query string if present
  const statusMatch = path.match(/status=(\w+)/)
  if (statusMatch) currentStatus.value = statusMatch[1]
  else if (!path.includes('status=')) currentStatus.value = ''
  router.push(path)
}

const logout = () => { staffStore.clearAuth(); router.push('/login') }

let timer
onMounted(() => {
  // Initialize currentStatus from current route
  const statusMatch = route.fullPath.match(/status=(\w+)/)
  if (statusMatch) currentStatus.value = statusMatch[1]

  const updateTime = () => {
    const d = new Date()
    currentTime.value = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
  }
  updateTime()
  timer = setInterval(updateTime, 60000)
})
onUnmounted(() => clearInterval(timer))
</script>

<!-- ============================================================
     全局样式 (非scoped) — 所有子页面依赖的CSS类
     ============================================================ -->
<style>
/* ===== 变量 ===== */
:root {
  --sidebar-w: 240px;
  --sidebar-collapsed: 64px;
  --topbar-h: 56px;
  --primary: #4f46e5;
  --primary-light: #eef2ff;
  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
  --text: #1e293b;
  --text-secondary: #64748b;
  --bg: #f1f5f9;
  --surface: #ffffff;
  --border: #e2e8f0;
  --radius: 10px;
  --shadow: 0 1px 3px rgba(0,0,0,.08);
  --shadow-md: 0 4px 12px rgba(0,0,0,.1);
  --font: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
}

/* ===== 重置 ===== */
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: var(--font); background: var(--bg); color: var(--text); font-size: 14px; line-height: 1.5; }
a { color: var(--primary); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ===== 通用卡片 ===== */
.card {
  background: var(--surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 20px;
  margin-bottom: 16px;
}
.card-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px; gap: 12px;
}
.card-title {
  font-size: 15px; font-weight: 700; color: var(--text);
  display: flex; align-items: center; gap: 6px;
}
.card-toolbar { display: flex; align-items: center; gap: 8px; }

/* ===== 按钮 ===== */
.btn {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 7px 14px; border-radius: 7px;
  font-size: 13px; font-weight: 600; cursor: pointer;
  border: none; transition: all .15s; white-space: nowrap;
}
.btn-primary { background: var(--primary); color: #fff; }
.btn-primary:hover { background: #4338ca; }
.btn-ghost { background: transparent; color: var(--text-secondary); }
.btn-ghost:hover { background: #f1f5f9; color: var(--text); }
.btn-danger { background: #fee2e2; color: var(--danger); }
.btn-danger:hover { background: #fecaca; }
.btn-outline { background: transparent; color: var(--primary); border: 1px solid var(--primary); }
.btn-outline:hover { background: #eef2ff; }
.btn-sm { padding: 5px 10px; font-size: 12px; }

/* ===== 表格 ===== */
.data-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.data-table th {
  text-align: left; padding: 10px 12px;
  font-size: 12px; font-weight: 600; color: var(--text-secondary);
  text-transform: uppercase; letter-spacing: .5px;
  border-bottom: 2px solid var(--border);
  background: #fafafa;
}
.data-table td { padding: 12px; border-bottom: 1px solid var(--border); vertical-align: middle; }
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: #f9fafb; }

/* ===== 标签 ===== */
.tag {
  display: inline-flex; align-items: center;
  padding: 3px 9px; border-radius: 20px;
  font-size: 12px; font-weight: 600;
}
.tag-primary { background: var(--primary-light); color: var(--primary); }
.tag-success { background: #d1fae5; color: #059669; }
.tag-warning { background: #fef3c7; color: #d97706; }
.tag-info { background: #e0f2fe; color: #0369a1; }
.tag-danger { background: #fee2e2; color: #dc2626; }
.tag-gray { background: #f3f4f6; color: #6b7280; }

/* ===== 关联徽章 ===== */
.relation-badge {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 8px; border-radius: 6px;
  font-size: 12px; font-weight: 600;
  background: #e0f2fe; color: #0369a1;
}
.relation-badge.green { background: #d1fae5; color: #059669; }
.relation-badge.yellow { background: #fef3c7; color: #d97706; }

/* ===== 筛选栏 ===== */
.filter-bar {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 16px; flex-wrap: wrap;
}
.filter-right { margin-left: auto; }
.filter-select {
  padding: 7px 11px; border: 1px solid var(--border);
  border-radius: 7px; font-size: 13px;
  background: var(--surface); outline: none;
  cursor: pointer; color: var(--text);
}
.filter-select:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(79,70,229,.1); }

/* ===== 搜索框 ===== */
.search-box {
  display: flex; align-items: center; gap: 8px;
  background: #f8fafc; border-radius: 8px;
  padding: 8px 12px; border: 1px solid transparent;
  transition: all .15s;
}
.search-box:focus-within { background: #fff; border-color: var(--primary); box-shadow: 0 0 0 3px rgba(79,70,229,.1); }
.search-box input { border: none; background: none; outline: none; font-size: 13px; width: 200px; color: var(--text); }
.search-box input::placeholder { color: #9ca3af; }

/* ===== 标签页 ===== */
.tabs {
  display: flex; gap: 4px;
  border-bottom: 2px solid var(--border);
  margin-bottom: 20px;
}
.tab-item {
  padding: 10px 16px; font-size: 14px; font-weight: 600;
  cursor: pointer; color: var(--text-secondary);
  border-bottom: 2px solid transparent;
  margin-bottom: -2px; transition: all .15s;
  display: flex; align-items: center; gap: 6px;
}
.tab-item:hover { color: var(--text); }
.tab-item.active { color: var(--primary); border-bottom-color: var(--primary); }
.tab-count {
  background: var(--primary-light); color: var(--primary);
  font-size: 11px; padding: 1px 6px; border-radius: 10px; font-weight: 700;
}
.tab-content { }

/* ===== 状态标签页 ===== */
.status-tabs { display: flex; gap: 2px; border-bottom: 2px solid var(--border); margin-bottom: 16px; }
.status-tab {
  padding: 8px 14px; font-size: 13px; font-weight: 600;
  cursor: pointer; color: var(--text-secondary);
  border-bottom: 2px solid transparent; margin-bottom: -2px;
  border-radius: 6px 6px 0 0; transition: all .15s;
}
.status-tab:hover { color: var(--text); background: #f1f5f9; }
.status-tab.active { color: var(--primary); background: var(--primary-light); border-bottom-color: var(--primary); }

/* ===== 订单标签页 ===== */
.order-tabs { display: flex; gap: 4px; border-bottom: 2px solid var(--border); margin-bottom: 16px; }
.order-tab {
  padding: 8px 14px; font-size: 13px; font-weight: 600;
  cursor: pointer; color: var(--text-secondary);
  border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all .15s;
}
.order-tab:hover { color: var(--text); }
.order-tab.active { color: var(--primary); border-bottom-color: var(--primary); }

/* ===== 表单 ===== */
.form-row { display: grid; gap: 16px; margin-bottom: 16px; }
.form-row.cols-2 { grid-template-columns: 1fr 1fr; }
.form-row.cols-3 { grid-template-columns: 1fr 1fr 1fr; }
.form-field { display: flex; flex-direction: column; }
.form-label { font-size: 13px; font-weight: 600; margin-bottom: 6px; color: var(--text); }
.form-hint { font-size: 11px; color: var(--text-secondary); margin-top: 4px; }
.form-hint-inline { font-size: 11px; color: var(--text-secondary); }
.form-tip { font-size: 11px; color: var(--text-secondary); margin-top: 4px; }
.form-input {
  width: 100%; padding: 9px 12px;
  border: 1px solid #e5e7eb; border-radius: 8px;
  font-size: 14px; outline: none; transition: all .15s;
  background: var(--surface);
}
.form-input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(79,70,229,.1); }
textarea.form-input { resize: vertical; }

/* ===== 内联输入 ===== */
.inline-input {
  width: 60px; padding: 4px 8px;
  border: 1px solid #e5e7eb; border-radius: 6px;
  font-size: 13px; text-align: center; outline: none;
}
.inline-input:focus { border-color: var(--primary); }

/* ===== 快捷操作 ===== */
.quick-actions { display: flex; gap: 8px; flex-wrap: wrap; }

/* ===== 空状态 ===== */
.empty-state { text-align: center; padding: 40px 24px; color: var(--text-secondary); }
.empty-box { text-align: center; padding: 40px 24px; color: var(--text-secondary); }
.empty-desc { font-size: 13px; color: var(--text-secondary); }

/* ===== 步骤条 ===== */
.step-bar { display: flex; align-items: center; gap: 0; margin-bottom: 24px; }
.step-unit { flex: 1; display: flex; align-items: center; }
.step-circle {
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700;
  background: #e5e7eb; color: #9ca3af; flex-shrink: 0;
}
.step-unit.done .step-circle { background: var(--primary); color: #fff; }
.step-unit.active .step-circle { background: var(--primary); color: #fff; box-shadow: 0 0 0 4px rgba(79,70,229,.2); }
.step-label { font-size: 12px; margin-left: 8px; color: var(--text-secondary); white-space: nowrap; }
.step-unit.active .step-label { color: var(--primary); font-weight: 600; }
.step-line { flex: 1; height: 2px; background: #e5e7eb; margin: 0 8px; }
.step-unit.done .step-line { background: var(--primary); }

/* ===== 页面头部 ===== */
.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 24px; }
.page-header-row { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 24px; gap: 16px; }
.page-header-row h1 { font-size: 20px; font-weight: 800; margin-bottom: 4px; }
.page-header-row p { color: var(--text-secondary); font-size: 13px; }

/* ===== 网格 ===== */
.stats-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }

/* ===== 操作面板 ===== */
.action-panel { margin-bottom: 20px; }
.action-panel-title { font-size: 14px; font-weight: 700; margin-bottom: 10px; color: var(--text); }

/* ===== 价格标签 ===== */
.price-tag { font-weight: 700; color: var(--warning); font-size: 14px; }
.price-text { font-weight: 700; color: var(--warning); }

/* ===== 时间线 ===== */
.timeline { padding: 0; }
.timeline-item {
  display: flex; gap: 12px; padding-bottom: 16px;
  position: relative; font-size: 13px;
}
.timeline-item.current .timeline-dot { background: var(--primary); border-color: var(--primary); }
.timeline-dot {
  width: 10px; height: 10px; border-radius: 50%;
  border: 2px solid var(--border); background: #fff;
  flex-shrink: 0; margin-top: 4px;
}
.timeline-content { flex: 1; }
.timeline-title { font-weight: 600; color: var(--text); font-size: 13px; }
.timeline-desc { color: var(--text-secondary); font-size: 12px; margin-top: 2px; }
.timeline-time { color: var(--text-secondary); font-size: 12px; }
.timeline-operator { font-weight: 600; font-size: 12px; color: var(--primary); }

/* ===== 角色标签 ===== */
.role-tag { display: inline-flex; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; }
.role-tag.admin { background: #ede9fe; color: #7c3aed; }
.role-tag.technician { background: #e0f2fe; color: #0369a1; }
.role-tag.staff { background: #f3f4f6; color: #6b7280; }

/* ===== 客户备注 ===== */
.customer-note { font-size: 12px; color: var(--text-secondary); font-style: italic; }

/* ===== 创建时间 ===== */
.create-time { font-size: 12px; color: var(--text-secondary); }

/* ===== 特殊服务标签 ===== */
.special-service-tag {
  display: inline-flex; align-items: center;
  padding: 2px 8px; border-radius: 6px;
  font-size: 11px; font-weight: 600;
  background: #fef3c7; color: #d97706;
}
.special-list { display: flex; flex-direction: column; gap: 8px; }
.special-item { display: flex; align-items: center; justify-content: space-between; padding: 10px; background: #f9fafb; border-radius: 8px; }
.special-actions { display: flex; gap: 6px; }

/* ===== 覆盖价格网格 ===== */
.override-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.override-item { display: flex; align-items: center; justify-content: space-between; padding: 12px; background: #f8fafc; border-radius: 8px; border: 1px solid #f1f5f9; }
.override-brand { display: flex; flex-direction: column; gap: 3px; }
.override-type { font-size: 11px; color: var(--text-secondary); }
.override-price { display: flex; align-items: center; gap: 6px; }
.override-base { font-size: 12px; color: #9ca3af; text-decoration: line-through; }
.override-input {
  width: 75px; padding: 5px 8px;
  border: 1px solid #e5e7eb; border-radius: 6px;
  font-size: 14px; text-align: center; outline: none;
}
.override-input:focus { border-color: var(--primary); }
.override-diff { font-size: 11px; font-weight: 700; color: var(--warning); }
.override-legend { font-size: 12px; color: var(--text-secondary); flex: 1; }

/* ===== 支付状态 ===== */
.pay-status { display: inline-flex; padding: 3px 9px; border-radius: 6px; font-size: 12px; font-weight: 600; }
.pay-status.paid { background: #d1fae5; color: #059669; }
.pay-status.unpaid { background: #fee2e2; color: #dc2626; }

/* ===== 状态标签 ===== */
.status-tag {
  display: inline-flex; padding: 3px 9px; border-radius: 6px;
  font-size: 12px; font-weight: 600;
}

/* ===== 报告 ===== */
.report-preview { border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; background: #fafafa; }
.report-actions { display: flex; gap: 8px; margin-top: 12px; }
.report-iframe { width: 100%; border: 1px solid var(--border); border-radius: 8px; min-height: 500px; }

/* ===== 分页 ===== */
.pagination-wrap { display: flex; align-items: center; justify-content: center; margin-top: 20px; gap: 8px; }

/* ===== 加载状态 ===== */
.loading-state { text-align: center; padding: 40px; color: var(--text-secondary); }

/* ===== 提示 ===== */
.tip { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }

/* ===== 图片上传 ===== */
.img-upload-list { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
.img-upload-item { position: relative; }
.img-upload-add {
  width: 80px; height: 80px; border: 2px dashed #d1d5db;
  border-radius: 8px; display: flex; align-items: center; justify-content: center;
  cursor: pointer; font-size: 24px; color: #9ca3af; transition: all .15s;
}
.img-upload-add:hover { border-color: var(--primary); color: var(--primary); }
.img-preview-list { display: flex; flex-wrap: wrap; gap: 8px; }
.img-preview-item { position: relative; }
.img-remove {
  position: absolute; top: -6px; right: -6px;
  width: 18px; height: 18px; border-radius: 50%;
  background: var(--danger); color: #fff; border: none;
  cursor: pointer; font-size: 10px; display: flex; align-items: center; justify-content: center;
}

/* ===== 返回栏 ===== */
.back-bar {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 16px;
}

/* ===== 信息网格 ===== */
.info-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.info-section { margin-bottom: 16px; }
.info-section-title { font-size: 13px; font-weight: 700; color: var(--text); margin-bottom: 8px; }
.info-item { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid var(--border); font-size: 13px; }

/* ===== 滚动条 ===== */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #9ca3af; }

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .form-row.cols-2, .form-row.cols-3 { grid-template-columns: 1fr; }
  .info-grid { grid-template-columns: 1fr; }
  .override-grid { grid-template-columns: 1fr; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>

<!-- ============================================================
     Layout 专属样式 (scoped)
     ============================================================ -->
<style scoped>
/* ===== 主布局 ===== */
.app-layout { display: flex; height: 100vh; overflow: hidden; font-family: var(--font); }

/* ===== 侧边栏 ===== */
.sidebar {
  width: var(--sidebar-w); background: #1e293b;
  display: flex; flex-direction: column;
  transition: width .2s ease; flex-shrink: 0;
}
.sidebar.collapsed { width: var(--sidebar-collapsed); }

/* ===== Logo ===== */
.sidebar-header { padding: 20px 16px; border-bottom: 1px solid rgba(255,255,255,.08); }
.sidebar-logo { display: flex; align-items: center; gap: 12px; }
.logo-icon {
  width: 38px; height: 38px; background: var(--primary);
  border-radius: 10px; display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 18px; color: #fff; flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.3);
}
.logo-text { display: flex; flex-direction: column; }
.logo-name { color: #fff; font-weight: 700; font-size: 16px; letter-spacing: 1.5px; }
.logo-sub { color: rgba(255,255,255,.45); font-size: 11px; margin-top: 2px; font-weight: 400; }

/* ===== 导航 ===== */
.sidebar-nav { flex: 1; overflow-y: auto; overflow-x: hidden; padding: 8px 0; }
.sidebar-nav::-webkit-scrollbar { width: 0; }

.nav-item {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px; cursor: pointer;
  color: rgba(255,255,255,.55); font-size: 14px;
  transition: all .2s; position: relative;
  font-weight: 500;
  letter-spacing: 0.3px;
}
.nav-item:hover { background: rgba(255,255,255,.06); color: rgba(255,255,255,.95); }
.nav-item.active { background: rgba(79,70,229,.25); color: #fff; }
.nav-item.active::before {
  content: ''; position: absolute;
  left: 0; top: 8px; bottom: 8px;
  width: 3px; background: var(--primary);
  border-radius: 0 3px 3px 0;
}
.nav-icon-svg { width: 20px; height: 20px; flex-shrink: 0; opacity: 0.7; }
.nav-item:hover .nav-icon-svg { opacity: 0.9; }
.nav-item.active .nav-icon-svg { opacity: 1; }
.nav-label { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.nav-arrow { font-size: 12px; font-weight: 700; opacity: .4; }

.nav-children { margin-left: 20px; padding-left: 14px; border-left: 2px solid rgba(255,255,255,.06); }
.nav-child {
  padding: 10px 14px; cursor: pointer;
  color: rgba(255,255,255,.4); font-size: 13px;
  border-radius: 6px; transition: all .15s;
  font-weight: 400;
}
.nav-child:hover { background: rgba(255,255,255,.05); color: rgba(255,255,255,.85); }
.nav-child.active { background: rgba(79,70,229,.2); color: #a5b4fc; }

/* ===== 底部 ===== */
.sidebar-footer { padding: 12px; border-top: 1px solid rgba(255,255,255,.08); }
.user-panel {
  display: flex; align-items: center; gap: 8px;
  padding: 8px; background: rgba(255,255,255,.05);
  border-radius: 8px; margin-bottom: 8px;
}
.user-avatar {
  width: 30px; height: 30px; background: var(--primary);
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 700; font-size: 13px; flex-shrink: 0;
}
.user-info { flex: 1; min-width: 0; }
.user-name { color: #fff; font-size: 13px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-role { color: rgba(255,255,255,.4); font-size: 11px; }
.logout-btn {
  background: transparent; border: 1px solid rgba(239,68,68,.4);
  color: #f87171; padding: 3px 8px; border-radius: 4px;
  font-size: 11px; cursor: pointer; transition: all .15s;
}
.logout-btn:hover { background: #ef4444; color: #fff; border-color: #ef4444; }
.collapse-btn {
  display: flex; align-items: center; justify-content: center;
  padding: 6px; color: rgba(255,255,255,.3);
  cursor: pointer; transition: color .15s; border-radius: 4px;
}
.collapse-btn:hover { color: rgba(255,255,255,.8); }

/* ===== 主内容区 ===== */
.main-area { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

/* ===== 顶部栏 ===== */
.topbar {
  height: var(--topbar-h); background: var(--surface);
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px; flex-shrink: 0;
}
.topbar-left { display: flex; align-items: center; }
.page-title { font-size: 17px; font-weight: 700; color: var(--text); margin: 0; }
.topbar-right { display: flex; align-items: center; gap: 16px; }
.current-time { font-size: 13px; color: var(--text-secondary); }

/* ===== 内容 ===== */
.content { flex: 1; overflow-y: auto; padding: 24px; }

/* ===== 平板自适应：悬停展开/离开收回 ===== */
@media (max-width: 1024px) {
  .app-layout { display: block; }
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    z-index: 100;
    width: 68px;
    transition: width 0.3s ease, box-shadow 0.3s ease;
    overflow: hidden;
  }
  .sidebar:hover {
    width: var(--sidebar-w);
    box-shadow: 8px 0 30px rgba(0,0,0,0.5);
    overflow: visible;
  }
  /* 收起时隐藏文字 */
  .sidebar .nav-label,
  .sidebar .logo-text,
  .sidebar .nav-arrow,
  .sidebar .user-info,
  .sidebar .logout-btn,
  .sidebar .nav-children {
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.15s ease;
  }
  .sidebar:hover .nav-label,
  .sidebar:hover .logo-text,
  .sidebar:hover .nav-arrow,
  .sidebar:hover .user-info,
  .sidebar:hover .logout-btn {
    opacity: 1;
    pointer-events: auto;
  }
  .sidebar:hover .nav-children {
    opacity: 1;
    pointer-events: auto;
  }
  /* 收起时导航项居中 */
  .nav-item { justify-content: center; padding: 12px 8px; }
  .sidebar:hover .nav-item { justify-content: flex-start; padding: 12px 16px; }
  /* 收起时logo居中 */
  .sidebar-header { padding: 16px 8px; }
  .sidebar:hover .sidebar-header { padding: 20px 16px; }
  /* 收起时底部简化 */
  .sidebar-footer { padding: 8px; }
  .sidebar:hover .sidebar-footer { padding: 12px; }
  .collapse-btn { display: none; }
  .sidebar:hover .collapse-btn { display: flex; }
  /* 主区域留出侧边栏空间 */
  .main-area { margin-left: 68px; }
  .content { padding: 16px; }
}

@media (max-width: 768px) {
  .sidebar { width: 52px; }
  .sidebar:hover { width: var(--sidebar-w); }
  .main-area { margin-left: 52px; }
  .content { padding: 12px; }
  .topbar { padding: 0 12px; }
  .page-title { font-size: 15px; }
}
</style>
