<template>
  <div class="tracking-page">
    <!-- 顶部导航 -->
    <header class="app-header">
      <div class="app-header-inner">
        <div class="header-left" @click="router.back()">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </div>
        <div class="header-title">进度追踪</div>
        <div class="header-right"></div>
      </div>
    </header>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading" size="32" color="#1677ff"><Loading /></el-icon>
      <div style="margin-top:12px;color:#86909c;font-size:13px">加载中...</div>
    </div>

    <template v-else-if="order">
      <!-- 状态横幅 -->
      <div :class="['status-banner', `banner-${order.status}`]">
        <div class="banner-info">
          <div class="banner-label">当前状态</div>
          <div class="banner-value">{{ getStatusText(order.status) }}</div>
          <div class="banner-time" v-if="latestNode">{{ latestNode.operate_time }}</div>
        </div>
        <div class="banner-icon">
          <el-icon size="44"><component :is="getStatusIcon(order.status)" /></el-icon>
        </div>
      </div>

      <!-- 设备信息 -->
      <div class="page-container">
        <div class="device-summary">
          <div class="device-name">{{ order.product_name }} · {{ order.brand_name }} · {{ order.model_name }}</div>
          <div class="service-info">{{ order.service_name }} · <span class="price">¥{{ order.item_price }}</span></div>
        </div>

        <!-- 专项服务待确认提示 -->
        <div v-if="pendingSpecialService" class="special-alert">
          <div class="special-alert-icon"><el-icon><WarningFilled /></el-icon></div>
          <div class="special-alert-body">
            <div class="special-alert-title">专项服务待确认</div>
            <div class="special-alert-desc">{{ pendingSpecialService.name }} — 报价 ¥{{ pendingSpecialService.price }}</div>
          </div>
          <el-button type="primary" size="small" @click="showSpecialDialog = true">立即确认</el-button>
        </div>

        <!-- 追踪时间轴 -->
        <div class="tracking-timeline">
          <div
            v-for="(node, index) in trackingNodes"
            :key="index"
            :class="['timeline-item', { current: index === 0, past: index > 0 }]"
          >
            <div class="timeline-dot">
              <el-icon v-if="index === 0"><component :is="getNodeIcon(node.node_code)" /></el-icon>
              <el-icon v-else><component :is="getNodeIcon(node.node_code)" /></el-icon>
            </div>
            <div class="timeline-content">
              <div class="timeline-header">
                <span class="node-name">{{ node.node_name }}</span>
                <span v-if="node.operate_time" class="node-time">{{ node.operate_time }}</span>
              </div>
              <div v-if="node.description" class="node-desc">{{ node.description }}</div>
              <div v-if="node.staff_name" class="node-staff">操作员：{{ node.staff_name }}</div>
              <div v-if="node.photos && node.photos.length > 0" class="node-photos">
                <el-image
                  v-for="(photo, pIdx) in node.photos"
                  :key="pIdx"
                  :src="photo.startsWith('/') ? photo : '/uploads/' + photo"
                  fit="cover"
                  class="photo-thumb"
                  :preview-src-list="node.photos.map(p => p.startsWith('/') ? p : '/uploads/' + p)"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- 订单信息 -->
        <div class="order-info-card">
          <div class="info-row">
            <span class="info-label">订单号</span>
            <span class="info-value mono">{{ order.order_no }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">创建时间</span>
            <span class="info-value">{{ order.created_at }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">收件人</span>
            <span class="info-value">{{ order.receiver_name }} {{ order.receiver_phone }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">收件地址</span>
            <span class="info-value">{{ order.receiver_address }}</span>
          </div>
          <div v-if="order.express_no" class="info-row">
            <span class="info-label">寄出快递</span>
            <span class="info-value">{{ order.express_company }} · {{ order.express_no }}</span>
          </div>
          <div v-if="order.return_express_no" class="info-row">
            <span class="info-label">回寄快递</span>
            <span class="info-value">{{ order.return_express_company }} · {{ order.return_express_no }}</span>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <!-- 进行中订单：始终显示快递信息填写/修改入口（仅快递订单） -->
          <template v-if="order.status !== 'completed' && order.status !== 'cancelled' && order.delivery_type === 'express'">
            <el-button type="primary" style="width:100%" @click="openExpressDialog">
              {{ order.express_no ? '修改寄件快递' : '填写寄件快递' }}
            </el-button>
          </template>
          <!-- 已完成：只显示下载报告 -->
          <template v-if="order.status === 'completed'">
            <a
              :href="`/api/v1/client/orders/${order.id}/pdf?token=${encodeURIComponent(clientToken)}`"
              :download="`维修报告_${order.order_no}.pdf`"
              style="text-decoration:none; display:block; width:100%"
            >
              <el-button type="primary" style="width:100%">
                查看/下载检测报告
              </el-button>
            </a>
          </template>
          <!-- 进行中订单：可修改订单信息 -->
          <template v-if="order.status !== 'completed' && order.status !== 'cancelled'">
            <el-button style="width:100%;margin-top:8px" @click="showEditDialog = true">
              修改订单信息
            </el-button>
          </template>
        </div>

        <!-- 提醒文字 -->
        <div class="reminder-text" v-if="order.status !== 'completed'">
          请妥善保管您的快递单号，可通过快递公司官网追踪物流进度。
        </div>
        <div class="reminder-text success" v-else>
          维修保养已完成，请及时查看并下载检测报告。报告仅在服务器保存15天，请尽快下载保存。
        </div>
      </div>
    </template>

    <!-- 填写寄件快递 -->
    <el-dialog v-model="showExpressDialog" title="填写寄件快递" width="90%" :close-on-click-modal="false">
      <el-form label-width="80px">
        <el-form-item label="快递公司">
          <el-select
            v-model="expressForm.company"
            placeholder="请选择或输入快递公司"
            filterable allow-create default-first-option
            style="width:100%"
          >
            <el-option v-for="c in expressCompanies" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="快递单号">
          <el-input v-model="expressForm.no" placeholder="请输入快递单号" />
        </el-form-item>
        <div class="dialog-tip">请将设备寄至皓壹维修服务中心，运费由客户自理（到付）。</div>
      </el-form>
      <template #footer>
        <el-button @click="showExpressDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitExpress">确认提交</el-button>
      </template>
    </el-dialog>

    <!-- 填写回寄快递 -->
    <el-dialog v-model="showReturnDialog" title="填写回寄快递" width="90%" :close-on-click-modal="false">
      <el-form label-width="80px">
        <el-form-item label="快递公司">
          <el-input v-model="returnForm.company" placeholder="请输入快递公司" />
        </el-form-item>
        <el-form-item label="快递单号">
          <el-input v-model="returnForm.no" placeholder="请输入回寄快递单号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showReturnDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitReturnExpress">确认提交</el-button>
      </template>
    </el-dialog>

    <!-- 专项服务确认 -->
    <el-dialog v-model="showSpecialDialog" title="专项服务确认" width="90%" :close-on-click-modal="false">
      <template v-if="pendingSpecialService">
        <div class="special-detail">
          <div class="special-name">{{ pendingSpecialService.name }}</div>
          <div class="special-desc" v-if="pendingSpecialService.description">{{ pendingSpecialService.description }}</div>
          <div class="special-price">报价：<span>¥{{ pendingSpecialService.price }}</span></div>
          <div class="special-note" v-if="pendingSpecialService.staff_note">维修人员备注：{{ pendingSpecialService.staff_note }}</div>
          <div class="special-photos" v-if="pendingSpecialService.photos && pendingSpecialService.photos.length > 0">
            <el-image
              v-for="(photo, pIdx) in pendingSpecialService.photos"
              :key="pIdx"
              :src="photo"
              fit="cover"
              class="photo-full"
              :preview-src-list="pendingSpecialService.photos"
            />
          </div>
        </div>
      </template>
      <template #footer>
        <el-button @click="respondSpecial('reject')">拒绝服务</el-button>
        <el-button type="primary" @click="respondSpecial('confirm')">确认并付款</el-button>
      </template>
    </el-dialog>

    <!-- 修改订单信息 -->
    <el-dialog v-model="showEditDialog" title="修改订单信息" width="92%" :close-on-click-modal="false" top="5vh">
      <el-form label-position="top" v-if="editForm">
        <div class="edit-section-title">收件信息</div>
        <el-form-item label="收件人">
          <el-input v-model="editForm.receiver_name" placeholder="收件人姓名" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="editForm.receiver_phone" placeholder="联系电话" />
        </el-form-item>
        <el-form-item label="收件地址">
          <el-input v-model="editForm.receiver_address" type="textarea" :rows="2" placeholder="详细收件地址" />
        </el-form-item>
        <div class="edit-section-title" v-if="editForm.items && editForm.items.length">维修项目</div>
        <div v-for="(item, idx) in editForm.items" :key="idx" class="edit-item-card">
          <div class="edit-item-header">项目 {{ idx + 1 }}</div>
          <el-form-item label="品牌">
            <el-select
              v-model="item.brand_id"
              placeholder="请选择或输入品牌"
              filterable allow-create default-first-option
              style="width:100%"
              @change="(val) => { onBrandChange(val, idx); if(!val) item.brand_name = '' }"
              @clear="() => { item.brand_id = null; if(itemFilters[idx]) { itemFilters[idx].filteredModels = itemFilters[idx].filteredModels || [] } }"
            >
              <el-option v-for="b in (itemFilters[idx]?.filteredBrands || allBrands)" :key="b.id" :label="b.name" :value="b.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="型号">
            <el-select
              v-model="item.model_id"
              placeholder="请选择或输入型号"
              filterable allow-create default-first-option
              clearable
              style="width:100%"
              @change="(val) => { onModelChange(val, idx); if(!val) item.model_name = '' }"
              @clear="() => { item.model_id = null }"
            >
              <el-option v-for="m in (itemFilters[idx]?.filteredModels || allModels)" :key="m.id" :label="m.name" :value="m.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="服务类型">
            <el-select
              v-model="item.service_type_id"
              placeholder="请选择或输入服务类型"
              filterable allow-create default-first-option
              style="width:100%"
              @change="val => { if(!val) item.service_name = '' }"
            >
              <el-option v-for="s in (itemFilters[idx]?.filteredServices || allServices)" :key="s.id" :label="`${s.name}（${s.base_price}元）`" :value="s.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="备注说明">
            <el-input v-model="item.customer_note" type="textarea" :rows="2" placeholder="补充说明（如：呼吸阻力偏大）" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitEdit">保存修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const order = ref(null)
const trackingNodes = ref([])
const clientToken = computed(() => localStorage.getItem('client_token') || '')
const showExpressDialog = ref(false)
const showReturnDialog = ref(false)
const showSpecialDialog = ref(false)
const showEditDialog = ref(false)
const editForm = ref(null)
const submitting = ref(false)

const expressForm = ref({ company: '顺丰速运', no: '' })
const expressCompanies = ['顺丰速运', '京东快递', '中通快递', '圆通快递', '韵达快递', 'EMS']

// 维修项目编辑选项（全局池，供回退匹配用）
const allBrands = ref([])
const allModels = ref([])
const allServices = ref([])
// 每项维修的级联筛选状态（索引对应editForm.items）
const itemFilters = ref([]) // [{productTypeId, filteredBrands, filteredModels, filteredServices}]

async function loadAllOptions(productTypeId) {
  // 加载指定产品类型的品牌+该类型下全部型号+该类型的服务
  const [brandsRes, servicesRes] = await Promise.all([
    request.get(`/client/products/brands?type_id=${productTypeId}`),
    request.get(`/client/services?type_id=${productTypeId}`),
  ])
  const brands = brandsRes.success ? (brandsRes.data || []) : []
  const services = servicesRes.success ? (servicesRes.data || []) : []
  // 型号只加载指定产品类型（按品牌过滤，但品牌未选时先加载全部）
  const modelsRes = await request.get(`/client/products/models?product_type_id=${productTypeId}`)
  const models = modelsRes.success ? (modelsRes.data || []) : []
  return { brands, models, services }
}

function openExpressDialog() {
  // 预填已有快递信息
  expressForm.value.company = order.value.express_company || '顺丰速运'
  expressForm.value.no = order.value.express_no || ''
  showExpressDialog.value = true
}

// 品牌变化 → 筛选型号（限同产品类型+同品牌），清空已选型号
async function onBrandChange(brandId, idx) {
  if (!itemFilters.value[idx]) return
  const f = itemFilters.value[idx]
  if (typeof brandId === 'number') {
    f.filteredModels = f.filteredModels.filter(m => m.brand_id === brandId)
    const currentModel = allModels.value.find(m => m.id === editForm.value.items[idx].model_id)
    if (currentModel && currentModel.brand_id !== brandId) {
      editForm.value.items[idx].model_id = null
    }
  } else {
    // 自定义品牌名 → 型号恢复为同产品类型的全部选项
    const allOpts = await loadAllOptions(f.productTypeId)
    f.filteredModels = allOpts.models
    editForm.value.items[idx].model_id = null
  }
}

// 型号变化 → 无需联动服务（服务只按产品类型过滤）
async function onModelChange(modelId, idx) {
}

watch(showEditDialog, async (val) => {
  if (val && order.value) {
    editForm.value = {
      receiver_name: order.value.receiver_name || '',
      receiver_phone: order.value.receiver_phone || '',
      receiver_address: order.value.receiver_address || '',
      items: (order.value.items || []).map((item, idx) => {
        // 推断产品类型：优先用product_type_id，否则从brand/model反查
        const productTypeId = item.product_type_id ||
          allBrands.value.find(b => b.id === item.brand_id)?.product_type_id ||
          allModels.value.find(m => m.id === item.model_id)?.product_type_id ||
          allServices.value.find(s => s.id === item.service_type_id)?.product_type_id || 1
        return {
          id: item.id,
          product_type_id: productTypeId,
          brand_id: item.brand_id || null,
          brand_name: item.brand_name || '',
          model_id: item.model_id || null,
          model_name: item.model_name || '',
          service_type_id: item.service_type_id || null,
          service_name: item.service_name || '',
          customer_note: item.customer_note || '',
        }
      }),
    }
    // 为每项初始化级联筛选器
    itemFilters.value = editForm.value.items.map(item => ({ productTypeId: item.product_type_id }))
    // 加载全部品牌/型号/服务（用于兜底匹配）+ 按每项类型加载级联选项
    await loadAllOptions(1)
    for (let i = 0; i < editForm.value.items.length; i++) {
      const item = editForm.value.items[i]
      if (item.product_type_id) {
        const opts = await loadAllOptions(item.product_type_id)
        const f = itemFilters.value[i] || {}
        f.productTypeId = item.product_type_id
        f.filteredBrands = opts.brands
        f.filteredModels = opts.models
        f.filteredServices = opts.services
        itemFilters.value[i] = f
      }
    }
  }
})

async function submitEdit() {
  if (!editForm.value) return
  submitting.value = true
  try {
    // 处理items：el-select allow-create 时自定义文字返回字符串（非ID数字）
    const items = editForm.value.items.map(item => {
      // brand: 数字=选中的ID，字符串=自定义文字
      const brandIsNum = typeof item.brand_id === 'number'
      const modelIsNum = typeof item.model_id === 'number'
      const svcIsNum = typeof item.service_type_id === 'number'

      // 找到下拉选项中的name
      const brandObj = allBrands.value.find(b => b.id === item.brand_id)
      const modelObj = allModels.value.find(m => m.id === item.model_id)
      const svcObj = allServices.value.find(s => s.id === item.service_type_id)

      return {
        id: item.id,
        brand_id: brandIsNum ? item.brand_id : null,
        brand_name: brandIsNum ? '' : (brandObj ? brandObj.name : String(item.brand_id || '')),
        model_id: modelIsNum ? item.model_id : null,
        model_name: modelIsNum ? '' : (modelObj ? modelObj.name : String(item.model_id || '')),
        service_type_id: svcIsNum ? item.service_type_id : null,
        service_name: svcIsNum ? '' : (svcObj ? svcObj.name : String(item.service_type_id || '')),
        customer_note: item.customer_note || '',
      }
    })
    const payload = {
      receiver_name: editForm.value.receiver_name,
      receiver_phone: editForm.value.receiver_phone,
      receiver_address: editForm.value.receiver_address,
      items,
    }
    const res = await request.put(`/client/orders/${order.value.id}/edit`, payload)
    if (res.success) {
      ElMessage.success('订单信息已更新')
      showEditDialog.value = false
      loadTracking()
    }
  } finally {
    submitting.value = false
  }
}
const returnForm = ref({ company: '顺丰速运', no: '' })

const statusMap = {
  unpaid: '待支付',
  paid: '已付款，待寄件',
  receiving: '设备运输中',
  inspecting: '拆件检验中',
  repairing: '维修保养中',
  special_service: '专项服务待确认',
  ready: '维修完成，待回寄',
  shipped: '已回寄快递',
  completed: '订单已完成',
  cancelled: '已取消',
}

const statusIcons = {
  unpaid: 'Wallet',
  paid: 'Box',
  receiving: 'Van',
  inspecting: 'Search',
  repairing: 'Tools',
  special_service: 'WarningFilled',
  ready: 'CircleCheck',
  shipped: 'Van',
  completed: 'CircleCheckFilled',
  cancelled: 'CircleClose',
}

const nodeIconMap = {
  pending: 'InfoFilled',
  unpaid_paid: 'CreditCard',
  received: 'Box',
  inspecting: 'Search',
  repairing: 'Tools',
  special_request: 'WarningFilled',
  special_confirmed: 'Check',
  qc_pass: 'CircleCheckFilled',
  shipped: 'Van',
  completed: 'CircleCheckFilled',
}

function getStatusText(status) { return statusMap[status] || status }
function getStatusIcon(status) { return statusIcons[status] || 'InfoFilled' }
function getNodeIcon(code) { return nodeIconMap[code] || 'Check' }

const latestNode = computed(() => trackingNodes.value[0] || null)

const pendingSpecialService = computed(() => {
  if (!order.value || !order.value.special_service_pending) return null
  return order.value.special_service_pending
})

async function loadTracking() {
  loading.value = true
  try {
    const id = route.params.id
    const res = await request.get(`/client/orders/${id}/tracking`)
    if (res.success) {
      order.value = res.data.order
      trackingNodes.value = res.data.nodes || []
    }
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function submitExpress() {
  if (!expressForm.value.no.trim()) { ElMessage.warning('请填写快递单号'); return }
  submitting.value = true
  try {
    const res = await request.put(`/client/orders/${order.value.id}/express`, {
      express_company: expressForm.value.company,
      express_no: expressForm.value.no,
    })
    if (res.success) {
      ElMessage.success('快递信息已提交')
      showExpressDialog.value = false
      loadTracking()
    }
  } finally {
    submitting.value = false
  }
}

async function submitReturnExpress() {
  if (!returnForm.value.no.trim()) { ElMessage.warning('请填写快递单号'); return }
  submitting.value = true
  try {
    const res = await request.put(`/client/orders/${order.value.id}/return-express-client`, {
      return_express_company: returnForm.value.company,
      return_express_no: returnForm.value.no,
    })
    if (res.success) {
      ElMessage.success('回寄快递已填写')
      showReturnDialog.value = false
      loadTracking()
    }
  } finally {
    submitting.value = false
  }
}

async function respondSpecial(action) {
  submitting.value = true
  try {
    const res = await request.post(`/client/orders/${order.value.id}/special-service/respond`, {
      record_id: pendingSpecialService.value.id,
      action,
    })
    if (res.success) {
      ElMessage.success(action === 'confirm' ? '已确认专项服务' : '已拒绝服务')
      showSpecialDialog.value = false
      loadTracking()
    }
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadTracking()
})
</script>

<style scoped>
.tracking-page { min-height: 100vh; background: #f5f7fa; }
.app-header { background: #fff; border-bottom: 1px solid #e5e6eb; position: sticky; top: 0; z-index: 10; }
.app-header-inner { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; }
.header-left { display: flex; align-items: center; gap: 4px; cursor: pointer; font-size: 14px; color: #1677ff; min-width: 60px; }
.header-title { font-size: 16px; font-weight: 600; color: #1d2129; }
.header-right { min-width: 60px; }
.loading-container { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 80px 0; }

.status-banner { padding: 28px 24px; color: #fff; display: flex; justify-content: space-between; align-items: center; }
.banner-pending,.banner-unpaid { background: linear-gradient(135deg,#8c8c8c,#b0b0b0); }
.banner-paid,.banner-receiving,.banner-inspecting,.banner-repairing { background: linear-gradient(135deg,#1677ff,#4096ff); }
.banner-special_service { background: linear-gradient(135deg,#fa8c16,#ff9a3c); }
.banner-ready,.banner-shipped,.banner-completed { background: linear-gradient(135deg,#52c41a,#73d13d); }
.banner-cancelled { background: linear-gradient(135deg,#8c8c8c,#b0b0b0); }
.banner-label { font-size: 12px; opacity: 0.85; margin-bottom: 4px; }
.banner-value { font-size: 20px; font-weight: 700; }
.banner-time { font-size: 12px; opacity: 0.75; margin-top: 4px; }
.page-container { padding: 16px; }

.device-summary { background: #fff; border-radius: 10px; padding: 16px; margin-bottom: 16px; border: 1px solid #e5e6eb; }
.device-name { font-size: 15px; font-weight: 600; color: #1d2129; margin-bottom: 6px; }
.service-info { font-size: 13px; color: #4e5969; }
.price { color: #1677ff; font-weight: 600; }

.special-alert { background: #fff7e6; border: 1px solid #ffd591; border-radius: 10px; padding: 14px 16px; margin-bottom: 16px; display: flex; align-items: center; gap: 12px; }
.special-alert-icon { color: #fa8c16; font-size: 22px; flex-shrink: 0; }
.special-alert-body { flex: 1; }
.special-alert-title { font-size: 14px; font-weight: 600; color: #1d2129; margin-bottom: 2px; }
.special-alert-desc { font-size: 13px; color: #4e5969; }

.tracking-timeline { margin-bottom: 16px; }
.timeline-item { display: flex; gap: 14px; padding-bottom: 20px; position: relative; }
.timeline-item:not(:last-child)::before { content: ''; position: absolute; left: 15px; top: 32px; bottom: 0; width: 2px; background: #e5e6eb; }
.timeline-item.past::before { background: #52c41a; }
.timeline-dot { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; background: #fff; border: 2px solid #e5e6eb; color: #86909c; z-index: 1; }
.timeline-item.current .timeline-dot { background: #1677ff; border-color: #1677ff; color: #fff; }
.timeline-item.past .timeline-dot { background: #52c41a; border-color: #52c41a; color: #fff; }
.timeline-content { flex: 1; background: #fff; border-radius: 10px; padding: 14px; border: 1px solid #e5e6eb; }
.timeline-item.current .timeline-content { border-color: #1677ff; box-shadow: 0 2px 8px rgba(22,119,255,0.12); }
.timeline-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.node-name { font-size: 14px; font-weight: 600; color: #1d2129; }
.node-time { font-size: 12px; color: #86909c; }
.node-desc { font-size: 13px; color: #4e5969; margin-bottom: 4px; }
.node-staff { font-size: 12px; color: #86909c; margin-bottom: 8px; }
.node-photos { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
.photo-thumb { width: 64px; height: 64px; border-radius: 6px; cursor: pointer; }

.order-info-card { background: #fff; border-radius: 10px; border: 1px solid #e5e6eb; overflow: hidden; margin-bottom: 16px; }
.info-row { display: flex; padding: 12px 16px; border-bottom: 1px solid #f0f0f0; font-size: 13px; }
.info-row:last-child { border-bottom: none; }
.info-label { color: #86909c; width: 72px; flex-shrink: 0; }
.info-value { color: #1d2129; flex: 1; }
.mono { font-family: monospace; font-size: 12px; }

.action-buttons { margin-bottom: 16px; }
.reminder-text { font-size: 12px; color: #86909c; text-align: center; line-height: 1.6; }
.reminder-text.success { color: #52c41a; }

.dialog-tip { font-size: 12px; color: #86909c; background: #f5f7fa; padding: 10px 12px; border-radius: 6px; margin-top: 8px; }

.special-detail { }
.special-name { font-size: 16px; font-weight: 600; color: #1d2129; margin-bottom: 8px; }
.special-desc { font-size: 13px; color: #4e5969; margin-bottom: 12px; }
.special-price { font-size: 18px; font-weight: 700; color: #1677ff; margin-bottom: 12px; }
.special-note { font-size: 13px; color: #4e5969; margin-bottom: 12px; padding: 8px; background: #f5f7fa; border-radius: 6px; }
.special-photos { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
.photo-full { width: 80px; height: 80px; border-radius: 6px; cursor: pointer; }

.edit-section-title { font-size: 14px; font-weight: 600; color: #1d2129; margin: 12px 0 8px; padding-bottom: 6px; border-bottom: 1px solid #ebeef5; }
.edit-section-title:first-child { margin-top: 0; }
.edit-item-card { background: #f8f9fa; border-radius: 8px; padding: 12px; margin-bottom: 12px; }
.edit-item-header { font-size: 13px; font-weight: 500; color: #606266; margin-bottom: 8px; }
</style>
