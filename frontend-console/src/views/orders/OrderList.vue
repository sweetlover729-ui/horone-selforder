<template>
  <div class="order-list">
    <div class="page-header">
      <h2>订单管理</h2>
    </div>

    <!-- 筛选区域 -->
    <div class="filter-bar">
      <div class="status-tabs">
        <div
          v-for="tab in statusTabs"
          :key="tab.value"
          :class="['status-tab', { active: currentStatus === tab.value }]"
          @click="changeStatus(tab.value)"
        >
          {{ tab.label }}
        </div>
      </div>

      <div class="filter-right">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          @change="fetchOrders"
          style="width: 240px"
        />
        <el-select v-model="filterStaffId" placeholder="维修技师" clearable @change="fetchOrders" style="width: 120px">
          <el-option v-for="s in staffList" :key="s.id" :label="s.full_name || s.username" :value="s.id" />
        </el-select>
        <el-select v-model="filterProductTypeId" placeholder="产品类别" clearable @change="fetchOrders" style="width: 120px">
          <el-option v-for="t in productTypes" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-select v-model="filterBrandId" placeholder="品牌" clearable @change="fetchOrders" style="width: 120px">
          <el-option v-for="t in brands" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-select v-model="filterModelId" placeholder="型号" clearable @change="fetchOrders" style="width: 120px">
          <el-option v-for="t in models" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-select v-model="filterServiceTypeId" placeholder="服务类型" clearable @change="fetchOrders" style="width: 120px">
          <el-option v-for="t in serviceTypes" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
      </div>
    </div>

    <!-- 订单表格 -->
    <div class="card">
      <el-table :data="orders" v-loading="loading" @row-click="goDetail">
        <el-table-column prop="orderNo" label="订单号" width="160">
          <template #default="{ row }">
            <span>{{ row.orderNo }}</span>
            <el-tag v-if="row.urgentService" type="danger" size="small" style="margin-left: 6px;">加急</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="customerName" label="客户姓名" width="100" />
        <el-table-column label="维修技师" width="100">
          <template #default="{ row }">
            <span v-if="row.assignedStaffName" class="staff-name">{{ row.assignedStaffName }}</span>
            <span v-else class="staff-unassigned">未分配</span>
          </template>
        </el-table-column>
        <el-table-column label="设备" min-width="150">
          <template #default="{ row }">
            {{ row.productType }} / {{ row.brand }} / {{ row.model }}
          </template>
        </el-table-column>
        <el-table-column prop="serviceType" label="服务类型" width="100" />
        <el-table-column prop="totalPrice" label="总价" width="90">
          <template #default="{ row }">
            <span class="price">¥{{ row.totalPrice }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <span :class="['status-tag', getStatusClass(row.status)]">
              {{ getStatusLabel(row.status) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click.stop="$router.push(`/admin/orders/${row.id}`)">查看详情</el-button>
            <el-button v-if="row.assignedStaffId && canRelease(row.status)" type="warning" link @click.stop="handleRelease(row)">释放</el-button>
            <el-button type="danger" link @click.stop="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchOrders"
          @current-change="fetchOrders"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()
const route = useRoute()

const orders = ref([])
const loading = ref(false)
const page = ref(1)
const size = ref(10)
const total = ref(0)
const currentStatus = ref('')
const dateRange = ref([])
const filterStaffId = ref('')
const filterProductTypeId = ref('')
const filterBrandId = ref('')
const filterModelId = ref('')
const filterServiceTypeId = ref('')

// 筛选下拉框数据
const staffList = ref([])
const productTypes = ref([])
const brands = ref([])
const models = ref([])
const serviceTypes = ref([])

const statusTabs = [
  { label: '全部', value: '' },
  { label: '待收货', value: 'paid' },
  { label: '维修中', value: 'repairing' },
  { label: '待回寄', value: 'ready' },
  { label: '已完成', value: 'completed' }
]

const getStatusClass = (status) => {
  const map = {
    paid: 'status-pending', receiving: 'status-progress',
    inspecting: 'status-progress', repairing: 'status-progress',
    special_service: 'status-warning', ready: 'status-info',
    shipped: 'status-info', completed: 'status-success'
  }
  return map[status] || ''
}

const getStatusLabel = (status) => {
  const map = {
    paid: '待收货', receiving: '已收货', inspecting: '拆件中',
    repairing: '维修中', special_service: '专项服务',
    ready: '待回寄', shipped: '已发出', completed: '已完成',
    cancelled: '已取消', refunded: '已退款'
  }
  return map[status] || status
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  })
}

const loadFilters = async () => {
  try {
    const [s, pt, br, md, st] = await Promise.all([
      request.get('/admin/staff'),
      request.get('/admin/product-types'),
      request.get('/admin/brands'),
      request.get('/admin/models'),
      request.get('/admin/service-types')
    ])
    staffList.value = s?.data || s || []
    productTypes.value = pt?.data || pt || []
    brands.value = br?.data || br || []
    models.value = md?.data || md || []
    serviceTypes.value = st?.data || st || []
  } catch (e) { console.error('loadFilters', e) }
}

const changeStatus = (status) => {
  currentStatus.value = status
  page.value = 1
  fetchOrders()
}

const goDetail = (row) => {
  router.push(`/admin/orders/${row.id}`)
}

const canRelease = (status) => {
  return ['pending', 'confirmed', 'paid', 'received', 'inspecting', 'repairing'].includes(status)
}

const handleRelease = (row) => {
  ElMessageBox.confirm(
    `确认释放订单 ${row.orderNo}？\n当前技师：${row.assignedStaffName || '未知'}\n释放后其他技师可以重新接单。`,
    '释放订单确认',
    {
      confirmButtonText: '确认释放',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await request.post(`/orders/${row.id}/release`)
      ElMessage.success('订单已释放')
      fetchOrders()
    } catch (e) {
      ElMessage.error(e?.response?.data?.message || '释放失败')
    }
  }).catch(() => {})
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确认删除订单 ${row.orderNo}？`, '删除确认', {
    confirmButtonText: '确认删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await request.delete(`/orders/${row.id}`)
      ElMessage.success('订单已删除')
      fetchOrders()
    } catch (e) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const fetchOrders = async () => {
  loading.value = true
  try {
    const params = { page: page.value, size: size.value }
    if (currentStatus.value) params.status = currentStatus.value
    if (dateRange.value?.length === 2) {
      params.startDate = dateRange.value[0]
      params.endDate = dateRange.value[1]
    }
    if (filterStaffId.value) params.staff_id = filterStaffId.value
    if (filterProductTypeId.value) params.product_type_id = filterProductTypeId.value
    if (filterBrandId.value) params.brand_id = filterBrandId.value
    if (filterModelId.value) params.model_id = filterModelId.value
    if (filterServiceTypeId.value) params.service_type_id = filterServiceTypeId.value

    const res = await request.get('/orders', { params })
    const raw = res?.orders || res?.data || []
    orders.value = raw.map(o => {
      const first = (o.items && o.items.length > 0) ? o.items[0] : {}
      return {
        id: o.id,
        orderNo: o.order_no || '',
        customerName: o.receiver_name || o.customer_name || '',
        customerPhone: o.receiver_phone || o.customer_phone || '',
        assignedStaffId: o.assigned_staff_id || null,
        assignedStaffName: o.assigned_staff_name || '',
        productType: first.product_type_name || '',
        brand: first.brand_name || '',
        model: first.model_name || '',
        serviceType: first.service_type_name || '',
        totalPrice: o.total_amount || 0,
        status: o.status || '',
        createdAt: o.created_at || '',
        urgentService: o.urgent_service || false,
        urgentFee: o.urgent_fee || 0,
      }
    })
    total.value = res?.total || 0
  } catch (error) {
    console.error('Failed to fetch orders:', error)
  } finally {
    loading.value = false
  }
}

watch(() => route.query.status, (newStatus) => {
  currentStatus.value = newStatus || ''
  fetchOrders()
}, { immediate: true })

onMounted(() => {
  if (route.query.status) currentStatus.value = route.query.status
  loadFilters()
  fetchOrders()
})
</script>

<style scoped>
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  background: #fff;
  padding: 12px 16px;
  border-radius: 4px;
  border: 1px solid #f0f0f0;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-right {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.status-tabs {
  display: flex;
  gap: 4px;
}

.status-tab {
  padding: 6px 16px;
  font-size: 13px;
  color: #595959;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.15s;
}

.status-tab:hover { color: #1677ff; background: #f0f7ff; }
.status-tab.active { color: #1677ff; background: #e6f4ff; font-weight: 500; }

.price { color: #fa8c16; font-weight: 500; }

.status-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}
.status-pending { background: #fff7e6; color: #fa8c16; }
.status-progress { background: #e6f4ff; color: #1677ff; }
.status-warning { background: #fff7e6; color: #fa8c16; }
.status-info { background: #f0f7ff; color: #1677ff; }
.status-success { background: #f6ffed; color: #52c41a; }

.staff-name {
  color: #1677ff;
  font-weight: 500;
}
.staff-unassigned {
  color: #999;
  font-size: 12px;
}

.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
