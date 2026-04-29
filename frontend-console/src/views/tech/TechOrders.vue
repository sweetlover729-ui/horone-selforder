<template>
  <div class="tech-orders">
    <!-- 顶部三栏Tab -->
    <div class="tab-bar">
      <div
        v-for="t in tabs"
        :key="t.key"
        class="tab-item"
        :class="{ active: activeTab === t.key }"
        @click="activeTab = t.key"
      >
        <span>{{ t.label }}</span>
        <span v-if="t.count > 0" class="tab-badge">{{ t.count }}</span>
      </div>
    </div>

    <!-- 订单列表 -->
    <div class="order-list">
      <div v-if="filteredOrders.length === 0" class="empty-state">
        <p>暂无{{ tabs.find(t => t.key === activeTab)?.label }}订单</p>
      </div>
      <div
        v-for="order in filteredOrders"
        :key="order.id"
        class="order-card"
        @click="openOrder(order)"
      >
        <div class="order-header">
          <span class="order-no">#{{ order.order_no }}</span>
          <div class="order-header-right">
            <span v-if="order.urgent_service" class="urgent-tag">加急</span>
            <span class="order-status" :class="statusClass(order.status)">
              {{ statusLabel(order.status) }}
            </span>
          </div>
        </div>
        <div class="order-info">
          <div>客户：{{ order.receiver_name || '-' }}</div>
          <div>金额：¥{{ order.total_amount || 0 }}</div>
          <div>时间：{{ order.created_at?.substring(5, 16) || '-' }}</div>
          <div v-if="activeTab === 'mine'">
            状态：{{ nodeLabel(order.status) }}
          </div>
        </div>
        <div class="order-action">
          <span v-if="activeTab === 'new'" class="btn-claim">认领任务</span>
          <span v-else-if="activeTab === 'done'" class="btn-continue">订单详情</span>
          <span v-else class="btn-continue">继续处理</span>
          <span class="arrow">&rsaquo;</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()
const activeTab = ref('new')
const myOrders = ref([])
const newOrders = ref([])
const loading = ref(false)

// Tab配置：待认领新订单 / 进行中 / 已完成
const tabs = computed(() => [
  { key: 'new',       label: '待认领',   count: newOrders.value.length },
  { key: 'mine',      label: '进行中',   count: inProgressOrders.value.length },
  { key: 'completed', label: '已完成',   count: completedOrders.value.length },
])

const inProgressOrders = computed(() =>
  myOrders.value.filter(o => ['received','inspecting','repairing','ready'].includes(o.status))
)
const completedOrders = computed(() =>
  myOrders.value.filter(o => ['shipped','completed'].includes(o.status))
)

const filteredOrders = computed(() => {
  if (activeTab.value === 'new')       return newOrders.value
  if (activeTab.value === 'mine')      return inProgressOrders.value
  return completedOrders.value
})

const statusMap = {
  pending: '待确认', confirmed: '待认领', received: '已接单',
  inspecting: '检验中', repairing: '维修中', ready: '质检通过',
  shipped: '已发出', completed: '已完成',
}
const statusLabel = (s) => statusMap[s] || s
const statusClass = (s) => {
  if (['confirmed'].includes(s)) return 'status-pending'
  if (['received','inspecting','repairing','ready'].includes(s)) return 'status-progress'
  return 'status-done'
}
const nodeLabel = (s) => statusMap[s] || s

async function loadOrders() {
  loading.value = true
  try {
    const res = await request.get('/tech/orders')
    if (res.success && res.data) {
      myOrders.value  = res.data.my_orders  || []
      newOrders.value = res.data.new_orders || []
    } else {
      myOrders.value = []
      newOrders.value = []
    }
  } catch (e) {
    console.error('loadOrders error:', e)
    myOrders.value = []
    newOrders.value = []
  } finally {
    loading.value = false
  }
}

async function openOrder(order) {
  // 待认领订单 → 先认领再跳转
  if (activeTab.value === 'new') {
    try {
      const res = await request.post(`/tech/orders/${order.id}/accept`)
      if (!res.success) {
        ElMessage.error(res.message || '认领失败')
        return
      }
      ElMessage.success(res.message || '认领成功')
      // 从待认领列表移除，加入进行中
      newOrders.value = newOrders.value.filter(o => o.id !== order.id)
      order.status = 'received'
      myOrders.value.unshift(order)
      activeTab.value = 'mine'
    } catch (e) {
      ElMessage.error('认领失败，请重试')
      return
    }
  }
  router.push(`/tech/order/${order.id}`)
}

onMounted(loadOrders)
</script>

<style scoped>
.tech-orders { padding: 0; }
.tab-bar {
  display: flex;
  background: white;
  border-bottom: 2px solid #e5e7eb;
  position: sticky;
  top: 0;
  z-index: 10;
}
.tab-item {
  flex: 1;
  text-align: center;
  padding: 12px 8px;
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  position: relative;
}
.tab-item.active {
  color: #1a3a6c;
  border-bottom: 2px solid #1a3a6c;
  margin-bottom: -2px;
}
.tab-badge {
  background: #ef4444;
  color: white;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 8px;
  margin-left: 4px;
}
.order-list { padding: 12px; }
.empty-state {
  text-align: center;
  padding: 48px 16px;
  color: #9ca3af;
  font-size: 14px;
}
.order-card {
  background: white;
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  cursor: pointer;
}
.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.order-no { font-weight: 600; font-size: 14px; color: #1f2937; }
.order-header-right {
  display: flex;
  align-items: center;
  gap: 6px;
}
.urgent-tag {
  background: #ef4444;
  color: white;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
}
.order-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
}
.status-pending { background: #fef3c7; color: #92400e; }
.status-progress { background: #dbeafe; color: #1e40af; }
.status-done { background: #d1fae5; color: #065f46; }
.order-info {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.6;
}
.order-action {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-top: 8px;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
}
.btn-claim { color: #1a3a6c; font-weight: 600; }
.btn-continue { color: #3b82f6; }
.arrow { color: #d1d5db; font-size: 18px; }
</style>
