<template>
  <div class="dashboard-page">
    <!-- 欢迎 -->
    <div class="welcome-row">
      <div class="welcome-text">
        <h1>欢迎回来，{{ userName }}</h1>
        <p>{{ todayStr }}，祝工作顺利</p>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">全部订单</div>
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-sub">累计订单</div>
      </div>
      <div class="stat-card stat-warning">
        <div class="stat-label">维修中</div>
        <div class="stat-value">{{ stats.repairing }}</div>
        <div class="stat-sub">待处理</div>
      </div>
      <div class="stat-card stat-success">
        <div class="stat-label">本月完成</div>
        <div class="stat-value">{{ stats.completed }}</div>
        <div class="stat-sub">本月</div>
      </div>
      <div class="stat-card stat-danger">
        <div class="stat-label">本月收入</div>
        <div class="stat-value">¥{{ formatMoney(stats.revenue) }}</div>
        <div class="stat-sub">已完成订单</div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="card">
      <div class="card-header">
        <span class="card-title">快捷操作</span>
      </div>
      <div class="quick-actions">
        <div class="quick-btn" @click="$router.push('/admin/orders?status=repairing')">
          <span class="quick-btn-text">处理维修订单</span>
          <span v-if="stats.repairing > 0" class="quick-badge">{{ stats.repairing }}</span>
        </div>
        <div class="quick-btn" @click="$router.push('/admin/orders?status=paid')">
          <span class="quick-btn-text">待收货</span>
          <span v-if="stats.paid > 0" class="quick-badge">{{ stats.paid }}</span>
        </div>
        <div class="quick-btn" @click="$router.push('/admin/orders?status=ready')">
          <span class="quick-btn-text">待回寄</span>
          <span v-if="stats.ready > 0" class="quick-badge">{{ stats.ready }}</span>
        </div>
        <div class="quick-btn" @click="$router.push('/admin/hub')">
          <span class="quick-btn-text">数据管理</span>
        </div>
      </div>
    </div>

    <!-- 最新订单 -->
    <div class="card">
      <div class="card-header">
        <span class="card-title">最新订单</span>
        <button class="btn btn-ghost btn-sm" @click="$router.push('/admin/orders')">查看全部 &gt;</button>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>订单号</th>
            <th>客户</th>
            <th>设备</th>
            <th>金额</th>
            <th>状态</th>
            <th>时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="o in recentOrders" :key="o.id">
            <td><span class="order-no">{{ o.order_no }}</span></td>
            <td>{{ o.receiver_name }}<br><span class="f12 text-muted">{{ o.receiver_phone }}</span></td>
            <td>
              <span class="relation-badge">{{ o.product_type_name || '—' }}</span><br>
              <span class="f12 text-muted">{{ o.brand_name }} {{ o.model_name }}</span>
            </td>
            <td><span class="price-tag">¥{{ o.total_amount }}</span></td>
            <td><span class="tag" :class="statusTag(o.status)">{{ statusLabel(o.status) }}</span></td>
            <td><span class="f12 text-muted">{{ fmt(o.created_at) }}</span></td>
            <td>
              <button class="btn btn-ghost btn-sm" @click="$router.push(`/admin/orders/${o.id}`)">查看</button>
            </td>
          </tr>
          <tr v-if="recentOrders.length === 0">
            <td colspan="7"><div class="empty-state"><div class="empty-desc">暂无订单</div></div></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import request from '@/utils/request'
import { useStaffStore } from '@/stores/staff'

const staffStore = useStaffStore()
const stats = ref({ total: 0, repairing: 0, completed: 0, revenue: 0, paid: 0, ready: 0 })
const recentOrders = ref([])

const userName = computed(() => staffStore.userInfo?.fullName || staffStore.userInfo?.username || '用户')

const todayStr = computed(() => {
  return new Date().toLocaleDateString('zh-CN', {
    year: 'numeric', month: 'long', day: 'numeric', weekday: 'long'
  })
})

const formatMoney = (v) => (!v ? '0' : Number(v).toLocaleString())

const statusLabel = (s) => ({
  pending: '待处理', paid: '待收货', receiving: '收货中',
  inspecting: '验货中', repairing: '维修中', qc: '质检中',
  ready: '待回寄', shipping: '回寄中', completed: '已完成', cancelled: '已取消'
}[s] || s)

const statusTag = (s) => ({
  pending: 'tag-warning', paid: 'tag-info', receiving: 'tag-info',
  inspecting: 'tag-primary', repairing: 'tag-danger', qc: 'tag-primary',
  ready: 'tag-success', shipping: 'tag-success', completed: 'tag-success', cancelled: 'tag-gray'
}[s] || 'tag-gray')

const fmt = (t) => t ? t.slice(5, 16).replace('T', ' ') : '—'

const loadStats = async () => {
  try {
    const res = await request.get('/dashboard/stats')
    if (res && res.success !== false) {
      const d = res.data || res
      stats.value = {
        total: d.total_orders || d.pending_count || 0,
        repairing: (d.repairing_count || 0) + (d.status_breakdown?.inspecting || 0),
        completed: d.completed_this_month || 0,
        revenue: d.month_revenue || 0,
        paid: d.status_breakdown?.paid || 0,
        ready: d.status_breakdown?.ready || 0,
      }
    }
  } catch (e) { console.error('loadStats', e) }
}

const loadRecentOrders = async () => {
  try {
    const res = await request.get('/orders?size=8')
    if (res) {
      // API 返回 {success, orders, total}，orders 是扁平订单列表（含 items）
      const raw = res.orders || res.data || []
      recentOrders.value = raw.slice(0, 8).map(o => {
        const item = (o.items && o.items.length > 0) ? o.items[0] : {}
        return {
          id: o.id,
          order_no: o.order_no,
          receiver_name: o.receiver_name || '',
          receiver_phone: o.receiver_phone || '',
          product_type_name: item.product_type_name || '',
          brand_name: item.brand_name || '',
          model_name: item.model_name || '',
          total_amount: o.total_amount || 0,
          status: o.status || '',
          created_at: o.created_at || '',
        }
      })
    }
  } catch (e) { console.error('loadOrders', e) }
}

onMounted(() => { loadStats(); loadRecentOrders() })
</script>

<style scoped>
.dashboard-page { max-width: 1100px; }

/* ===== 欢迎 ===== */
.welcome-row { margin-bottom: 24px; }
.welcome-text h1 { font-size: 22px; font-weight: 800; color: #1e293b; margin-bottom: 4px; }
.welcome-text p { font-size: 14px; color: #64748b; margin: 0; }

/* ===== 统计卡片 ===== */
.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,.08);
}
.stat-label {
  font-size: 12px; font-weight: 600; color: #64748b;
  text-transform: uppercase; letter-spacing: .5px; margin-bottom: 8px;
}
.stat-value { font-size: 30px; font-weight: 800; color: #1e293b; margin-bottom: 4px; }
.stat-sub { font-size: 12px; color: #94a3b8; }
.stat-warning .stat-value { color: #f59e0b; }
.stat-success .stat-value { color: #10b981; }
.stat-danger .stat-value { color: #ef4444; }

/* ===== 快捷操作 ===== */
.quick-btn {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px; background: #f8fafc; border-radius: 10px;
  cursor: pointer; transition: all .15s; border: 1px solid transparent;
}
.quick-btn:hover { background: #f1f5f9; border-color: #4f46e5; }
.quick-btn-text { font-size: 14px; font-weight: 600; color: #1e293b; }
.quick-badge {
  background: #ef4444; color: #fff;
  font-size: 12px; font-weight: 700;
  padding: 2px 8px; border-radius: 12px;
}

/* ===== 辅助 ===== */
.order-no {
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 12px; color: #64748b;
  background: #f3f4f6; padding: 2px 6px; border-radius: 4px;
}
.f12 { font-size: 12px; }
.text-muted { color: #64748b; }
.price-tag { font-weight: 700; color: #f59e0b; font-size: 14px; }

@media (max-width: 900px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr) !important; }
}
@media (max-width: 600px) {
  .stats-grid { grid-template-columns: 1fr !important; }
}
</style>
