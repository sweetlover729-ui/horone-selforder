<template>
  <div class="order-detail-page">
    <!-- 顶部导航 -->
    <header class="app-header">
      <div class="app-header-inner">
        <div class="header-left" @click="router.back()">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </div>
        <div class="header-title">订单详情</div>
        <div class="header-right"></div>
      </div>
    </header>

    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading" size="32" color="#1677ff"><Loading /></el-icon>
    </div>

    <template v-else-if="order">
      <!-- 订单状态 -->
      <div class="status-banner">
        <div class="status-info">
          <div class="status-label">当前状态</div>
          <div :class="['status-value', `status-text-${order.status}`]">
            {{ getStatusText(order.status) }}
          </div>
        </div>
        <div class="status-icon">
          <el-icon size="48" :color="getStatusColor(order.status)">
            <component :is="getStatusIcon(order.status)" />
          </el-icon>
        </div>
      </div>

      <!-- 订单信息 -->
      <div class="page-container">
        <el-card class="info-card">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="订单号">{{ order.id }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatTime(order.createdAt) }}</el-descriptions-item>
            <el-descriptions-item label="服务类型">{{ order.serviceName }}</el-descriptions-item>
            <el-descriptions-item label="服务费用">
              <span class="price-highlight">{{ order.servicePrice }}元</span>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 设备信息 -->
        <el-card class="info-card">
          <template #header>
            <div class="card-header-title">设备信息</div>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="产品类型">{{ order.productName }}</el-descriptions-item>
            <el-descriptions-item label="品牌">{{ order.brandName }}</el-descriptions-item>
            <el-descriptions-item label="型号">{{ order.model }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 收件信息 -->
        <el-card class="info-card">
          <template #header>
            <div class="card-header-title">收件信息</div>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="收件人">{{ order.receiverName }}</el-descriptions-item>
            <el-descriptions-item label="联系电话">{{ order.receiverPhone }}</el-descriptions-item>
            <el-descriptions-item label="收件地址">{{ order.receiverAddress }}</el-descriptions-item>
            <el-descriptions-item v-if="order.remark" label="备注">{{ order.remark }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 快递信息 -->
        <el-card v-if="order.sendExpress || order.returnExpress" class="info-card">
          <template #header>
            <div class="card-header-title">快递信息</div>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item v-if="order.sendExpress" label="寄件快递">
              {{ order.sendExpress.company }} - {{ order.sendExpress.no }}
            </el-descriptions-item>
            <el-descriptions-item v-if="order.returnExpress" label="回寄快递">
              {{ order.returnExpress.company }} - {{ order.returnExpress.no }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 专项服务 -->
        <el-card v-if="order.specialService" class="info-card special-service-card">
          <template #header>
            <div class="card-header-title" style="color: #fa8c16">
              <el-icon><WarningFilled /></el-icon>
              专项服务待确认
            </div>
          </template>
          <div class="special-service-content">
            <div class="special-service-desc">{{ order.specialService.desc }}</div>
            <div class="special-service-price">
              报价：<span class="price-highlight">{{ order.specialService.price }}元</span>
            </div>
          </div>
          <div class="special-service-actions">
            <el-button type="primary" size="small">确认报价</el-button>
            <el-button size="small">拒绝并取消</el-button>
          </div>
        </el-card>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button
            v-if="order.status === 'confirmed' || order.status === 'received'"
            type="danger"
            plain
            style="width: 100%"
            @click="handleCancel"
          >
            取消订单
          </el-button>
          <el-button
            v-if="order.status === 'repairing' || order.status === 'ready'"
            type="primary"
            style="width: 100%"
            @click="router.push(`/order/${order.id}/tracking`)"
          >
            查看进度追踪
          </el-button>
          <el-button
            v-if="order.status === 'completed'"
            style="width: 100%"
            @click="handleViewPdf"
          >
            查看检测报告
          </el-button>
          <el-button
            v-if="order.status === 'completed'"
            style="width: 100%; margin-top: 12px"
            @click="handleFillReturnExpress"
          >
            填写回寄快递
          </el-button>
        </div>

        <!-- 联系客服 -->
        <div class="contact-bar">
          <span>如有疑问，请联系客服</span>
          <el-button text type="primary" size="small">微信客服</el-button>
          <el-button text type="primary" size="small">电话咨询</el-button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const loading = ref(true)
const order = ref(null)

const statusMap = {
  unpaid: { text: '待支付', color: '#fa8c16' },
  paid: { text: '已支付', color: '#1677ff' },
  receiving: { text: '待收货', color: '#1677ff' },
  repairing: { text: '维修中', color: '#1677ff' },
  special_service: { text: '待确认', color: '#fa8c16' },
  ready: { text: '待回寄', color: '#52c41a' },
  shipped: { text: '已回寄', color: '#52c41a' },
  completed: { text: '已完成', color: '#52c41a' },
  cancelled: { text: '已取消', color: '#86909c' },
}

const statusIcons = {
  unpaid: 'Wallet',
  paid: 'CreditCard',
  receiving: 'Van',
  repairing: 'Tools',
  special_service: 'WarningFilled',
  ready: 'Van',
  shipped: 'Van',
  completed: 'CircleCheck',
  cancelled: 'CircleClose',
}

function getStatusText(status) {
  return statusMap[status]?.text || status
}

function getStatusColor(status) {
  return statusMap[status]?.color || '#86909c'
}

function getStatusIcon(status) {
  return statusIcons[status] || 'InfoFilled'
}

function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function handleViewPdf() {
  ElMessage.info('检测报告功能开发中')
}

function handleFillReturnExpress() {
  ElMessage.info('回寄快递功能开发中')
}

async function handleCancel() {
  try {
    await ElMessageBox.confirm(
      '取消后无法恢复，确定要取消这个订单吗？',
      '确认取消',
      { confirmButtonText: '确定取消', cancelButtonText: '我再想想', type: 'warning' }
    )
  } catch {
    return
  }
  try {
    const id = route.params.id
    await request.put(`/client/orders/${id}/cancel`)
    ElMessage.success('订单已取消')
    order.value.status = 'cancelled'
  } catch (e) {
    ElMessage.error(e?.message || '取消失败')
  }
}

async function loadOrder() {
  loading.value = true
  try {
    const id = route.params.id
    const res = await request.get(`/client/orders/${id}`)
    if (res.success) {
      order.value = res.data
    }
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadOrder()
})
</script>

<style scoped>
.order-detail-page {
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

.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
}

.status-banner {
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
  padding: 32px 24px;
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-label {
  font-size: 13px;
  opacity: 0.85;
  margin-bottom: 6px;
}

.status-value {
  font-size: 22px;
  font-weight: 700;
}

.info-card {
  margin-bottom: 12px;
}

.card-header-title {
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
  display: flex;
  align-items: center;
  gap: 6px;
}

.price-highlight {
  color: #1677ff;
  font-weight: 600;
  font-size: 15px;
}

.special-service-card {
  border-color: #ffe7ba;
  background: #fff7e6;
}

.special-service-content {
  margin-bottom: 16px;
}

.special-service-desc {
  font-size: 14px;
  color: #4e5969;
  margin-bottom: 8px;
}

.special-service-price {
  font-size: 14px;
  color: #1d2129;
}

.special-service-actions {
  display: flex;
  gap: 12px;
}

.action-buttons {
  margin: 20px 0;
}

.contact-bar {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #86909c;
  padding: 16px 0;
  justify-content: center;
}
</style>
