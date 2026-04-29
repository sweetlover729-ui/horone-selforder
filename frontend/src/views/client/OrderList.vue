<template>
  <div class="order-list-page">
    <!-- 顶部导航 -->
    <header class="app-header">
      <div class="app-header-inner">
        <div class="header-left" @click="router.push('/')">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </div>
        <div class="header-title">我的订单</div>
        <div class="header-right"></div>
      </div>
    </header>

    <!-- Tab 切换 -->
    <div class="tabs-container">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="全部" name="all" />
        <el-tab-pane label="进行中" name="processing" />
        <el-tab-pane label="已完成" name="completed" />
      </el-tabs>
    </div>

    <!-- 订单列表 -->
    <div class="page-container" style="padding-top: 12px">
      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading" size="32" color="#1677ff"><Loading /></el-icon>
        <div style="margin-top: 12px; color: #86909c; font-size: 13px">加载中...</div>
      </div>

      <template v-else>
        <div v-if="filteredOrders.length === 0" class="empty-state">
          <div class="empty-state-icon">
            <el-icon size="32"><Document /></el-icon>
          </div>
          <div class="empty-state-text">暂无订单</div>
          <el-button type="primary" @click="router.push('/order/create')">立即下单</el-button>
        </div>

        <div v-else class="order-list">
          <div
            v-for="order in filteredOrders"
            :key="order.id"
            class="order-card"
            @click="router.push(`/order/${order.id}/tracking`)"
          >
            <div class="order-card-header">
              <span class="order-no">{{ order.id }}</span>
              <span :class="['status-tag', `status-${order.status}`]">
                {{ getStatusText(order.status) }}
              </span>
            </div>

            <div class="order-card-body">
              <div class="order-device">
                <div class="device-type">{{ order.productName }}</div>
                <div class="device-info">
                  {{ order.brandName }} - {{ order.model }}
                </div>
              </div>

              <div class="order-service">
                <div class="service-name">{{ order.serviceName }}</div>
                <div class="service-price">{{ order.servicePrice }}元</div>
              </div>
            </div>

            <div class="order-card-footer">
              <span class="order-time">{{ formatTime(order.createdAt) }}</span>
              <div class="footer-actions">
                <el-button
                  v-if="['confirmed', 'received'].includes(order.status)"
                  type="danger"
                  size="small"
                  plain
                  @click.stop="handleCancel(order.id)"
                >
                  取消订单
                </el-button>
                <span class="order-action">查看详情 <el-icon><ArrowRight /></el-icon></span>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'
import { useRouter } from 'vue-router'

const router = useRouter()
const activeTab = ref('all')
const loading = ref(false)

// 模拟订单数据
const orders = ref([])

const statusMap = {
  unpaid: { text: '待支付', color: 'warning' },
  paid: { text: '已支付', color: 'primary' },
  receiving: { text: '待收货', color: 'primary' },
  repairing: { text: '维修中', color: 'primary' },
  special_service: { text: '待确认', color: 'warning' },
  ready: { text: '待回寄', color: 'success' },
  shipped: { text: '已回寄', color: 'success' },
  completed: { text: '已完成', color: 'success' },
  cancelled: { text: '已取消', color: 'info' },
}

function getStatusText(status) {
  return statusMap[status]?.text || status
}

const filteredOrders = computed(() => {
  if (activeTab.value === 'all') {
    return orders.value
  }
  if (activeTab.value === 'processing') {
    // 进行中 = 未完成的订单（除 cancelled 外）
    return orders.value.filter((o) => o.status !== 'completed' && o.status !== 'cancelled')
  }
  if (activeTab.value === 'completed') {
    return orders.value.filter((o) => o.status === 'completed')
  }
  return orders.value
})

function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function handleTabChange() {
  // 可以在这里触发数据刷新
}

async function loadOrders() {
  loading.value = true
  try {
    const res = await request.get('/client/orders/my')
    if (res.success) {
      orders.value = res.data || []
    }
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadOrders()
})

async function handleCancel(orderId) {
  try {
    await ElMessageBox.confirm('确定要取消这个订单吗？取消后无法恢复。', '确认取消', {
      confirmButtonText: '确定取消',
      cancelButtonText: '再想想',
      type: 'warning',
    })
    const res = await request.put(`/client/orders/${orderId}/cancel`)
    if (res.success) {
      ElMessage.success('订单已取消')
      loadOrders()
    } else {
      ElMessage.error(res.message || '取消失败')
    }
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error('取消失败，请稍后重试')
    }
  }
}
</script>

<style scoped>
.order-list-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  font-size: 14px;
  color: #1677ff;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}

.header-right {
  width: 60px;
}

.tabs-container {
  background: #fff;
  padding: 0 16px;
  border-bottom: 1px solid #e5e6eb;
}

.tabs-container :deep(.el-tabs__header) {
  margin: 0;
}

.tabs-container :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
}

.order-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.order-card {
  background: #fff;
  border-radius: 10px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #e5e6eb;
}

.order-card:hover {
  border-color: #1677ff;
  box-shadow: 0 2px 12px rgba(22, 119, 255, 0.1);
}

.order-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.order-no {
  font-size: 13px;
  color: #86909c;
  font-family: monospace;
}

.status-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-unpaid {
  background: #fff7e6;
  color: #fa8c16;
}

.status-paid,
.status-receiving,
.status-repairing {
  background: #e6f4ff;
  color: #1677ff;
}

.status-special_service {
  background: #fff7e6;
  color: #fa8c16;
}

.status-ready,
.status-shipped,
.status-completed {
  background: #f6ffed;
  color: #52c41a;
}

.status-cancelled {
  background: #f5f5f5;
  color: #86909c;
}

.order-card-body {
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.order-device {
  margin-bottom: 8px;
}

.device-type {
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 4px;
}

.device-info {
  font-size: 13px;
  color: #4e5969;
}

.order-service {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.service-name {
  font-size: 13px;
  color: #4e5969;
}

.service-price {
  font-size: 14px;
  font-weight: 600;
  color: #1677ff;
}

.order-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
}

.footer-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.order-time {
  font-size: 12px;
  color: #86909c;
}

.order-action {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #1677ff;
}
</style>
