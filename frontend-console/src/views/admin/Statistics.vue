<template>
  <div class="statistics-page">
    <div class="page-header">
      <h2>统计报表</h2>
    </div>

    <!-- 筛选区域 -->
    <div class="filter-bar">
      <el-date-picker v-model="dateRange" type="daterange" range-separator="至"
        start-placeholder="开始日期" end-placeholder="结束日期"
        value-format="YYYY-MM-DD" style="width: 260px" />
      <el-select v-model="filterProductTypeId" placeholder="产品类别" clearable style="width: 130px">
        <el-option v-for="t in productTypes" :key="t.id" :label="t.name" :value="t.id" />
      </el-select>
      <el-select v-model="filterBrandId" placeholder="品牌" clearable style="width: 130px">
        <el-option v-for="t in brands" :key="t.id" :label="t.name" :value="t.id" />
      </el-select>
      <el-select v-model="filterModelId" placeholder="型号" clearable style="width: 130px">
        <el-option v-for="t in models" :key="t.id" :label="t.name" :value="t.id" />
      </el-select>
      <el-select v-model="filterServiceTypeId" placeholder="服务类型" clearable style="width: 130px">
        <el-option v-for="t in serviceTypes" :key="t.id" :label="t.name" :value="t.id" />
      </el-select>
      <el-select v-model="filterCustomerId" placeholder="客户" clearable filterable style="width: 150px">
        <el-option v-for="c in customers" :key="c.id" :label="c.name + (c.phone ? ' (' + c.phone + ')' : '')" :value="c.id" />
      </el-select>
      <el-button type="primary" @click="loadData">查询</el-button>
    </div>

    <!-- 概览卡片 -->
    <div class="stats-grid" v-loading="loading">
      <div class="stat-card">
        <div class="stat-label">总订单数</div>
        <div class="stat-value">{{ data.total_orders }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">总收入</div>
        <div class="stat-value" style="color: #f59e0b">¥{{ formatMoney(data.total_revenue) }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">平均客单价</div>
        <div class="stat-value" style="color: #3b82f6">¥{{ formatMoney(data.avg_order_value) }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">完成率</div>
        <div class="stat-value" style="color: #10b981">{{ data.completion_rate }}%</div>
      </div>
    </div>

    <!-- 分布表格 -->
    <div class="card" v-loading="loading">
      <div class="card-header"><span class="card-title">状态分布</span></div>
      <table class="data-table">
        <thead><tr><th>状态</th><th>订单数</th><th>占比</th></tr></thead>
        <tbody>
          <tr v-for="(count, status) in data.status_breakdown" :key="status">
            <td>{{ statusLabel(status) }}</td>
            <td>{{ count }}</td>
            <td>{{ data.total_orders ? ((count / data.total_orders) * 100).toFixed(1) : 0 }}%</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="card" v-loading="loading">
      <div class="card-header"><span class="card-title">产品类别分布</span></div>
      <table class="data-table">
        <thead><tr><th>产品类别</th><th>订单数</th><th>收入</th><th>占比</th></tr></thead>
        <tbody>
          <tr v-for="row in data.product_type_breakdown" :key="row.name">
            <td>{{ row.name }}</td><td>{{ row.count }}</td>
            <td style="color: #f59e0b">¥{{ formatMoney(row.revenue) }}</td>
            <td>{{ data.total_orders ? ((row.count / data.total_orders) * 100).toFixed(1) : 0 }}%</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="card" v-loading="loading">
      <div class="card-header"><span class="card-title">品牌分布</span></div>
      <table class="data-table">
        <thead><tr><th>品牌</th><th>订单数</th><th>收入</th><th>占比</th></tr></thead>
        <tbody>
          <tr v-for="row in data.brand_breakdown" :key="row.name">
            <td>{{ row.name }}</td><td>{{ row.count }}</td>
            <td style="color: #f59e0b">¥{{ formatMoney(row.revenue) }}</td>
            <td>{{ data.total_orders ? ((row.count / data.total_orders) * 100).toFixed(1) : 0 }}%</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="card" v-loading="loading">
      <div class="card-header"><span class="card-title">服务类型分布</span></div>
      <table class="data-table">
        <thead><tr><th>服务类型</th><th>订单数</th><th>收入</th><th>占比</th></tr></thead>
        <tbody>
          <tr v-for="row in data.service_type_breakdown" :key="row.name">
            <td>{{ row.name }}</td><td>{{ row.count }}</td>
            <td style="color: #f59e0b">¥{{ formatMoney(row.revenue) }}</td>
            <td>{{ data.total_orders ? ((row.count / data.total_orders) * 100).toFixed(1) : 0 }}%</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="card" v-loading="loading">
      <div class="card-header"><span class="card-title">技师业绩</span></div>
      <table class="data-table">
        <thead><tr><th>技师</th><th>接单数</th><th>收入</th></tr></thead>
        <tbody>
          <tr v-for="row in data.staff_breakdown" :key="row.name">
            <td>{{ row.name }}</td><td>{{ row.count }}</td>
            <td style="color: #f59e0b">¥{{ formatMoney(row.revenue) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="card" v-loading="loading">
      <div class="card-header"><span class="card-title">月度趋势</span></div>
      <table class="data-table">
        <thead><tr><th>月份</th><th>订单数</th><th>收入</th></tr></thead>
        <tbody>
          <tr v-for="row in data.monthly_trend" :key="row.month">
            <td>{{ row.month }}</td><td>{{ row.count }}</td>
            <td style="color: #f59e0b">¥{{ formatMoney(row.revenue) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import request from '@/utils/request'

const loading = ref(false)
const dateRange = ref([])
const filterProductTypeId = ref('')
const filterBrandId = ref('')
const filterModelId = ref('')
const filterServiceTypeId = ref('')
const filterCustomerId = ref('')
const productTypes = ref([])
const brands = ref([])
const models = ref([])
const serviceTypes = ref([])
const customers = ref([])

const data = reactive({
  total_orders: 0, total_revenue: 0, avg_order_value: 0, completion_rate: 0,
  status_breakdown: {}, product_type_breakdown: [], brand_breakdown: [],
  service_type_breakdown: [], staff_breakdown: [], monthly_trend: []
})

const formatMoney = (v) => (!v ? '0' : Number(v).toLocaleString())

const statusLabel = (s) => ({
  pending: '待处理', paid: '待收货', receiving: '收货中', inspecting: '验货中',
  repairing: '维修中', qc: '质检中', ready: '待回寄', shipping: '回寄中',
  completed: '已完成', cancelled: '已取消', deleted: '已删除'
}[s] || s)

// 加载各筛选项（支持级联参数）
const loadProductTypes = async () => {
  try {
    const params = {}
    if (filterBrandId.value) params.brand_id = filterBrandId.value
    if (filterServiceTypeId.value) params.service_type_id = filterServiceTypeId.value
    const res = await request.get('/admin/product-types', { params })
    productTypes.value = res?.data || []
  } catch (e) { console.error('loadProductTypes', e) }
}

const loadBrands = async () => {
  try {
    const params = {}
    if (filterProductTypeId.value) params.product_type_id = filterProductTypeId.value
    if (filterServiceTypeId.value) params.service_type_id = filterServiceTypeId.value
    const res = await request.get('/admin/brands', { params })
    brands.value = res?.data || []
  } catch (e) { console.error('loadBrands', e) }
}

const loadModels = async () => {
  try {
    const params = {}
    if (filterBrandId.value) params.brand_id = filterBrandId.value
    if (filterProductTypeId.value) params.product_type_id = filterProductTypeId.value
    const res = await request.get('/admin/models', { params })
    models.value = res?.data || []
  } catch (e) { console.error('loadModels', e) }
}

const loadServiceTypes = async () => {
  try {
    const params = {}
    if (filterProductTypeId.value) params.product_type_id = filterProductTypeId.value
    if (filterBrandId.value) params.brand_id = filterBrandId.value
    const res = await request.get('/admin/service-types', { params })
    serviceTypes.value = res?.data || []
  } catch (e) { console.error('loadServiceTypes', e) }
}

// 级联watch：选产品类别 → 过滤品牌/型号/服务类型，清除下游已选值
watch(filterProductTypeId, async (val) => {
  filterBrandId.value = ''
  filterModelId.value = ''
  filterServiceTypeId.value = ''
  await Promise.all([loadBrands(), loadModels(), loadServiceTypes()])
})

// 级联watch：选品牌 → 过滤型号，清除下游已选值
watch(filterBrandId, async (val) => {
  filterModelId.value = ''
  // 品牌变化时，reload 产品类别（只显示有该品牌订单的类型）和服务类型
  await Promise.all([loadProductTypes(), loadServiceTypes()])
})

// 级联watch：选服务类型 → 过滤品牌，清除已选值
watch(filterServiceTypeId, async (val) => {
  filterBrandId.value = ''
  await loadBrands()
})

const loadCustomers = async () => {
  try {
    const res = await request.get('/admin/customers/list')
    customers.value = res?.data || []
  } catch (e) { console.error('loadCustomers', e) }
}

const loadFilters = async () => {
  // 初始加载：全部无约束
  await Promise.all([loadProductTypes(), loadBrands(), loadModels(), loadServiceTypes(), loadCustomers()])
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {}
    if (dateRange.value?.length === 2) { params.startDate = dateRange.value[0]; params.endDate = dateRange.value[1] }
    if (filterProductTypeId.value) params.product_type_id = filterProductTypeId.value
    if (filterBrandId.value) params.brand_id = filterBrandId.value
    if (filterModelId.value) params.model_id = filterModelId.value
    if (filterServiceTypeId.value) params.service_type_id = filterServiceTypeId.value
    if (filterCustomerId.value) params.customer_id = filterCustomerId.value
    const res = await request.get('/dashboard/report', { params })
    if (res?.data) Object.assign(data, res.data)
  } catch (e) { console.error('loadData', e) }
  finally { loading.value = false }
}

onMounted(() => { loadFilters(); loadData() })
</script>

<style scoped>
.statistics-page { max-width: 1100px; }
.filter-bar { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-bottom: 20px;
  background: #fff; padding: 14px 16px; border-radius: 12px; border: 1px solid #f0f0f0; }
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.stat-label { font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: .5px; margin-bottom: 8px; }
.stat-value { font-size: 28px; font-weight: 800; color: #1e293b; }
.card { background: #fff; border-radius: 12px; padding: 16px 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.card-header { margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #f0f0f0; }
.card-title { font-size: 14px; font-weight: 700; color: #1e293b; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 8px 12px; background: #f8fafc; color: #64748b; font-weight: 600; border-bottom: 1px solid #e2e8f0; }
.data-table td { padding: 8px 12px; border-bottom: 1px solid #f1f5f9; color: #334155; }
.data-table tr:hover td { background: #f8fafc; }
@media (max-width: 768px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } }
</style>
