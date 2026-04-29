<template>
  <div class="order-create-page">
    <!-- 顶部导航 -->
    <header class="app-header">
      <div class="app-header-inner">
        <div class="header-left" @click="router.push('/')">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </div>
        <div class="header-title">下单</div>
        <div class="header-right"></div>
      </div>
    </header>

    <!-- 步骤条 -->
    <div class="steps-container">
      <el-steps :active="activeStep" finish-status="success" align-center>
        <el-step title="选择品牌型号" />
        <el-step title="选择服务" />
        <el-step title="填写信息" />
        <el-step title="确认订单" />
      </el-steps>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading" size="32" color="#1677ff"><Loading /></el-icon>
      <div style="margin-top:12px;color:#86909c;font-size:13px">加载中...</div>
    </div>

    <!-- 步骤内容 -->
    <div v-else class="page-container" style="padding-top:20px">

      <!-- 步骤1：选择品牌型号 -->
      <div v-show="activeStep === 0" class="step-content">
        <!-- 产品类别：显示预填值，不可选 -->
        <div class="step-title">产品类别</div>
        <div class="category-display">{{ selectedTypeName }}</div>

        <div class="step-title" style="margin-top:20px">选择品牌</div>
        <div v-if="loadingBrands" style="text-align:center;padding:20px;color:#86909c">加载中...</div>
        <div v-else class="brand-grid">
          <div
            v-for="brand in brands"
            :key="brand.id"
            :class="['brand-card', { 'is-selected': form.brand_id === brand.id }]"
            @click="handleSelectBrand(brand)"
          >
            <div class="brand-name">{{ brand.name }}</div>
            <div class="brand-country" v-if="brand.country">{{ brand.country }}</div>
          </div>
        </div>

        <!-- 类别选择（仅当有类别选项时显示） -->
        <div v-if="form.brand_id && modelCategories.length > 0" class="model-input-area" style="margin-top:20px">
          <div class="step-title">选择类型</div>
          <div class="type-scroll">
            <div
              v-for="c in modelCategories"
              :key="c.id"
              :class="['type-chip', { 'is-active': form.category_id === c.id }]"
              @click="handleSelectCategory(c)"
            >
              {{ c.name }}
            </div>
          </div>
        </div>

        <!-- 型号选择（有类别时需选类别，无类别时直接显示） -->
        <div v-if="form.brand_id && (modelCategories.length === 0 || form.category_id)" class="model-input-area" style="margin-top:20px">
          <div class="step-title">选择型号</div>
          <el-select
            v-model="form.model_id"
            placeholder="请选择型号，或直接输入"
            filterable
            allow-create
            default-first-option
            style="width:100%"
            size="large"
          >
            <el-option label="不清楚型号，仅确认品牌" value="brand_only" style="color:#1677ff;font-weight:600" />
            <el-option v-for="m in models" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
          <div class="input-tip">如未找到型号，可直接输入设备型号名称</div>
        </div>
      </div>

      <!-- 步骤2：选择服务 -->
      <div v-show="activeStep === 1" class="step-content">
        <div class="step-title">选择服务类型</div>
        <div class="service-list">
          <div
            v-for="svc in services"
            :key="svc.id"
            :class="['service-card', { 'is-selected': form.service_type_id === svc.id }]"
            @click="handleSelectService(svc)"
          >
            <div class="service-header">
              <div class="service-name">{{ svc.name }}</div>
              <div class="service-price">
                <span class="price-num">¥{{ getServicePrice(svc) }}</span><span class="price-unit">元</span>

              </div>
            </div>
            <div class="service-desc">{{ svc.description }}</div>
            <div class="service-check"><el-icon v-if="form.service_type_id === svc.id" color="#1677ff"><Check /></el-icon></div>
          </div>
        </div>
        <!-- 加急服务 -->
        <div class="urgent-service-box" style="margin-top:20px">
          <el-checkbox v-model="form.urgent_service" size="large">
            <span style="font-weight:600;color:#f56c6c">加急服务 (+¥100)</span>
          </el-checkbox>
          <div class="urgent-desc">选择加急服务，我们将优先处理您的订单，维修时间缩短50%</div>
        </div>

        <el-alert title="专项服务说明" type="info" :closable="false" style="margin-top:16px" show-icon>
          <template #default>如有额外维修需求，维修人员检修后会发起专项服务，确认后进行维修</template>
        </el-alert>
      </div>

      <!-- 步骤3：填写信息 -->
      <div v-show="activeStep === 2" class="step-content">
        <div class="step-title">选择交付方式</div>
        <div class="delivery-options">
          <div :class="['delivery-card', { 'is-selected': form.delivery_type === 'store' }]" @click="form.delivery_type = 'store'">
            <div class="delivery-icon"><el-icon size="32" color="#1677ff"><Shop /></el-icon></div>
            <div class="delivery-name">自行到店交付</div>
            <div class="delivery-desc">客户带装备到店，省去快递麻烦</div>
          </div>
          <div :class="['delivery-card', { 'is-selected': form.delivery_type === 'express' }]" @click="form.delivery_type = 'express'">
            <div class="delivery-icon"><el-icon size="32" color="#1677ff"><Van /></el-icon></div>
            <div class="delivery-name">快递寄送</div>
            <div class="delivery-desc">贵重物品建议使用顺丰，来回运费自行承担</div>
          </div>
        </div>

        <div class="step-title" style="margin-top:24px">联系方式</div>
        <el-form ref="formRef" :model="form" :rules="formRules" label-position="top" class="receiver-form">
          <el-form-item label="姓名" prop="receiverName">
            <el-input v-model="form.receiverName" placeholder="请输入您的姓名" size="large" />
          </el-form-item>
          <el-form-item label="联系电话" prop="receiverPhone">
            <el-input v-model="form.receiverPhone" placeholder="请输入联系电话" size="large" />
          </el-form-item>
          <el-form-item v-if="form.delivery_type === 'express'" label="收件地址" prop="receiverAddress">
            <el-input v-model="form.receiverAddress" placeholder="请输入收件地址（皓壹收件地址）" size="large" />
          </el-form-item>
          <el-form-item v-if="form.delivery_type === 'store'" label="到店时间（选填）">
            <el-input v-model="form.store_time" placeholder="可选填预计到店时间，如：本周六上午" size="large" />
          </el-form-item>
          <el-form-item label="设备型号（选填）">
            <el-input v-model="form.model_input" placeholder="如不确定可留空" size="large" />
          </el-form-item>
          <el-form-item label="最后一次保养时间（选填）">
            <el-select v-model="form.last_maintenance" placeholder="请选择" size="large" style="width:100%">
              <el-option label="无" value="无" />
              <el-option label="半年内" value="半年内" />
              <el-option label="半年-1年" value="半年-1年" />
              <el-option label="1-2年" value="1-2年" />
              <el-option label="2年以上" value="2年以上" />
            </el-select>
          </el-form-item>
          <el-form-item label="故障描述（选填）">
            <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="故障描述（必填）" />
          </el-form-item>
        </el-form>

        <!-- 快递说明卡片（仅快递方式显示） -->
        <el-card v-if="form.delivery_type === 'express'" class="express-info-card">
          <div class="express-info-title"><el-icon color="#1677ff"><Van /></el-icon><span>快递说明</span></div>
          <div class="express-info-content">
            <div>贵重物品建议使用顺丰速运</div>
            <div>来回运费自行承担</div>
          </div>
        </el-card>
      </div>

      <!-- 步骤4：确认订单 -->
      <div v-show="activeStep === 3" class="step-content">
        <div class="step-title">订单确认</div>
        <el-card class="order-summary-card">
          <div class="summary-section">
            <div class="summary-label">设备信息</div>
            <div class="summary-content">
              <div class="summary-item"><span class="label">类型：</span><span class="value">{{ selectedTypeName }}</span></div>
              <div class="summary-item"><span class="label">品牌：</span><span class="value">{{ selectedBrandName }}</span></div>
              <div class="summary-item" v-if="form.category_id"><span class="label">类别：</span><span class="value">{{ selectedCategoryName }}</span></div>
              <div class="summary-item"><span class="label">型号：</span><span class="value">{{ selectedModelName }}</span></div>
            </div>
          </div>
          <el-divider />
          <div class="summary-section">
            <div class="summary-label">服务信息</div>
            <div class="summary-content">
              <div class="summary-item"><span class="label">服务类型：</span><span class="value">{{ selectedServiceName }}</span></div>
              <div class="summary-item" v-if="customerDiscount.is_dealer && customerDiscount.discount_rate < 100">
                <span class="label">原价：</span><span class="value" style="text-decoration:line-through;color:#999">¥{{ selectedServiceBasePrice + priceSurcharge }}元</span>
              </div>
              <div class="summary-item"><span class="label">应付价格：</span><span class="value price-highlight">¥{{ selectedServicePrice }}元</span></div>
              <div class="summary-item" v-if="customerDiscount.is_dealer && customerDiscount.discount_rate < 100">
                <span class="label">经销商折扣：</span><span class="value" style="color:#52c41a">{{ customerDiscount.discount_rate }}折</span>
              </div>
              <div class="summary-item" v-if="form.urgent_service"><span class="label">加急费用：</span><span class="value" style="color:#f56c6c">+¥100</span></div>
            </div>
          </div>
          <el-divider />
          <div class="summary-section">
            <div class="summary-label">交付方式</div>
            <div class="summary-content">
              <div class="summary-item">
                <span class="label">方式：</span>
                <span class="value">{{ form.delivery_type === 'store' ? '自行到店交付' : '快递寄送' }}</span>
              </div>
              <div class="summary-item" v-if="form.delivery_type === 'express'"><span class="label">收件地址：</span><span class="value">{{ form.receiverAddress }}</span></div>
            </div>
          </div>
          <el-divider />
          <div class="summary-section">
            <div class="summary-label">联系方式</div>
            <div class="summary-content">
              <div class="summary-item"><span class="label">姓名：</span><span class="value">{{ form.receiverName }}</span></div>
              <div class="summary-item"><span class="label">电话：</span><span class="value">{{ form.receiverPhone }}</span></div>
              <div class="summary-item" v-if="form.remark"><span class="label">备注：</span><span class="value">{{ form.remark }}</span></div>
            </div>
          </div>
          <el-divider />
          <div class="total-price">
            <span>应付总额</span>
            <span class="total-num">¥{{ finalTotalPrice }}</span>
          </div>
          <div v-if="form.delivery_type === 'express'" class="freight-note">运费：来回运费自行承担</div>
          <div v-else class="freight-note" style="color:#52c41a">到店交付无需支付运费</div>
        </el-card>

        <el-checkbox v-model="agreedTerms" style="margin:16px 0">
          我已阅读并同意《皓壹维修服务条款》
        </el-checkbox>
      </div>

      <!-- 底部操作 -->
      <div class="bottom-actions">
        <el-button v-if="activeStep > 0" @click="handlePrev">上一步</el-button>
        <el-button v-if="activeStep < 3" type="primary" :disabled="!canProceed" @click="handleNext">下一步</el-button>
        <el-button v-if="activeStep === 3" type="primary" :loading="submitting" :disabled="!agreedTerms" @click="handleSubmit">
          订单确认
        </el-button>
      </div>
    </div>

    <!-- 支付/预约成功弹窗 -->
    <el-dialog v-model="showSuccessDialog" title="" width="85%" :close-on-click-modal="false" align-center>
      <div class="success-content">
        <div class="success-icon">
          <el-icon size="56" color="#52c41a"><CircleCheck /></el-icon>
        </div>
        <div class="success-title">订单提交成功！</div>
        <div class="success-subtitle">
          {{ form.delivery_type === 'store' ? '请按预约时间携带设备到店' : '请将设备寄至皓壹维修服务中心' }}
        </div>

        <!-- 快递方式：填写快递单号 -->
        <template v-if="form.delivery_type === 'express'">
          <el-divider />
          <div class="express-form">
            <div class="express-form-title">填写寄件快递信息</div>
            <el-form ref="expressFormRef" :model="expressForm" label-position="top">
              <el-form-item label="快递公司">
                <el-select
                  v-model="expressForm.company"
                  placeholder="请选择或输入快递公司"
                  filterable
                  allow-create
                  default-first-option
                  style="width:100%"
                >
                  <el-option v-for="c in expressCompanies" :key="c" :label="c" :value="c" />
                </el-select>
              </el-form-item>
              <el-form-item label="快递单号" prop="no">
                <el-input v-model="expressForm.no" placeholder="请输入顺丰快递单号" />
              </el-form-item>
            </el-form>
            <div class="express-tip">请妥善保存快递单号，可通过顺丰官网追踪物流进度</div>
          </div>
        </template>

        <!-- 到店方式：显示门店信息 -->
        <template v-else>
          <el-divider />
          <div class="store-info">
            <div class="store-info-title">到店信息</div>
            <div class="store-info-item"><span class="store-info-label">地址：</span>皓壹维修服务中心（下单后可在订单详情查看）</div>
            <div class="store-info-item"><span class="store-info-label">电话：</span>请在订单详情中查看</div>
            <div class="store-info-tip">到店时请出示订单，维修人员扫码确认收货</div>
          </div>
        </template>
      </div>
      <template #footer>
        <el-button v-if="form.delivery_type === 'express'" @click="handleSkipExpress">稍后填写快递</el-button>
        <el-button type="primary" :loading="submittingExpress" @click="handleSubmitExpress">
          {{ form.delivery_type === 'express' ? '确认快递并提交' : '查看订单追踪' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { useCustomerStore } from '@/stores/customer'

const customerStore = useCustomerStore()

const router = useRouter()
const route = useRoute()

const loading = ref(true)
const loadingBrands = ref(false)
const loadingModels = ref(false)
const submitting = ref(false)
const submittingExpress = ref(false)
const showSuccessDialog = ref(false)
const agreedTerms = ref(false)

const formRef = ref()
const expressFormRef = ref()

const activeStep = ref(0)

const productTypes = ref([])
const brands = ref([])
const models = ref([])
const services = ref([])
const modelCategories = ref([]) // 配件类型列表（从models表聚合）
const selectedTypeId = ref(null)

const form = ref({
  product_type_id: null,
  brand_id: null,
  category: '',
  category_id: null,
  model_id: null,
  model_name: '',
  service_type_id: null,
  urgent_service: false,
  receiverName: '',
  receiverPhone: '',
  receiverAddress: '',
  delivery_type: 'store', // 'store' | 'express'
  store_time: '',
  model_input: '',
  last_maintenance: '',
  remark: '',
})

const expressForm = ref({ company: '顺丰速运', no: '' })
const expressCompanies = ['顺丰速运', '京东快递', '中通快递', '圆通快递', '韵达快递', 'EMS']
let createdOrderId = null

const formRules = {
  receiverName: [{ required: true, message: '请输入姓名' }],
  receiverPhone: [
    { required: true, message: '请输入联系电话' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入11位手机号码' }
  ],
  receiverAddress: [
    { required: true, message: '请输入收件地址' }
  ],
}

// 计算属性
const selectedTypeName = computed(() =>
  productTypes.value.find(t => t.id === selectedTypeId.value)?.name || '')

const selectedCategoryName = computed(() => {
  const cat = modelCategories.value.find(c => c.id === form.value.category_id)
  return cat ? cat.name : ''
})

function handleSelectCategory(cat) {
  form.value.category_id = cat.id
  form.value.category = cat.name
  form.value.model_id = null
  form.value.service_type_id = null
  serviceSurcharges.value = {}
  loadModels()
  loadServices()
  loadAllSurcharges()
}
const selectedBrandName = computed(() =>
  brands.value.find(b => b.id === form.value.brand_id)?.name || '')
const selectedModelName = computed(() => {
  if (!form.value.model_id) return ''
  if (form.value.model_id === 'brand_only') return '(客户不清楚具体型号)'
  const m = models.value.find(m => m.id === form.value.model_id)
  return m ? m.name : String(form.value.model_id)
})
const selectedServiceName = computed(() =>
  services.value.find(s => s.id === form.value.service_type_id)?.name || '')
const selectedServiceBasePrice = computed(() =>
  services.value.find(s => s.id === form.value.service_type_id)?.base_price || 0)
const serviceSurcharges = ref({}) // 品牌加价映射 {service_type_id: surcharge}
const priceSurcharge = computed(() => serviceSurcharges.value[form.value.service_type_id] || 0)

// 经销商折扣信息
const customerDiscount = ref({ is_dealer: false, discount_rate: 100 })
const discountedPrice = computed(() => {
  let price = selectedServiceBasePrice.value + priceSurcharge.value
  if (customerDiscount.value.is_dealer && customerDiscount.value.discount_rate < 100) {
    price = Math.round(price * customerDiscount.value.discount_rate / 100 * 100) / 100
  }
  return price
})
const selectedServicePrice = computed(() => discountedPrice.value)
const finalTotalPrice = computed(() => selectedServicePrice.value + (form.value.urgent_service ? 100 : 0))

function getServicePrice(svc) {
  const surcharge = serviceSurcharges.value[svc.id] || 0
  let price = svc.base_price + surcharge
  if (customerDiscount.value.is_dealer && customerDiscount.value.discount_rate < 100) {
    price = Math.round(price * customerDiscount.value.discount_rate / 100 * 100) / 100
  }
  return price
}

const canProceed = computed(() => {
  if (activeStep.value === 0) {
    if (!form.value.brand_id) return false
    // 如果有类别选项，需要先选类别
    if (modelCategories.value.length > 0 && !form.value.category_id) return false
    return !!(form.value.model_id || form.value.model_name)
  }
  if (activeStep.value === 1) return !!form.value.service_type_id
  if (activeStep.value === 2) {
    if (!form.value.receiverName || !form.value.receiverPhone) return false
    if (form.value.delivery_type === 'express' && !form.value.receiverAddress) return false
    return true
  }
  return true
})

// 数据加载
async function loadInitialData() {
  loading.value = true
  try {
    const typesRes = await request.get('/client/products/types')
    if (typesRes.success) productTypes.value = typesRes.data
    
    // 从URL获取type参数，预填产品类别
    const urlType = route.query.type
    const matchedType = productTypes.value.find(t => 
      t.name.includes(urlType === 'regulator' ? '调节器' : 
                      urlType === 'bcd' ? 'BCD' : 
                      urlType === 'computer' ? '电脑表' : '')
    )
    if (matchedType) {
      selectedTypeId.value = matchedType.id
      form.value.product_type_id = matchedType.id
      services.value = []
      await loadBrands(matchedType.id)
      // 如果该类型没有套装类别，立即加载服务
      if (!matchedType.categories) loadServices()
    } else if (productTypes.value.length > 0) {
      const defaultType = productTypes.value[0]
      selectedTypeId.value = defaultType.id
      form.value.product_type_id = defaultType.id
      services.value = []
      await loadBrands(defaultType.id)
      if (!defaultType.categories) loadServices()
    }
  } catch (e) {
    ElMessage.error('加载失败，请重试')
  } finally {
    loading.value = false
    // 已登录客户：自动填入姓名+手机号+折扣信息
    const ci = customerStore.customerInfo
    if (customerStore.isLoggedIn && ci.phone) {
      form.value.receiverName = ci.name || ''
      form.value.receiverPhone = ci.phone || ''
      // 加载经销商折扣信息
      if (ci.is_dealer !== undefined) {
        customerDiscount.value = {
          is_dealer: ci.is_dealer === 1 || ci.is_dealer === true,
          discount_rate: ci.discount_rate || 100
        }
      }
    }
  }
}

async function loadBrands(typeId) {
  loadingBrands.value = true
  try {
    const res = await request.get(`/client/products/brands?type_id=${typeId}`)
    if (res.success) brands.value = res.data
  } catch (e) { ElMessage.error('加载品牌失败') }
  finally { loadingBrands.value = false }
}

async function loadServices() {
  try {
    const params = { type_id: form.value.product_type_id }
    if (form.value.category) params.category = form.value.category
    const res = await request.get('/client/services', { params })
    if (res.success) services.value = res.data
  } catch (e) { /* continue */ }
}

async function loadModels() {
  try {
    let url = `/client/products/models?brand_id=${form.value.brand_id}&product_type_id=${form.value.product_type_id}`
    if (form.value.category_id) {
      url += `&category_id=${form.value.category_id}`
    }
    const res = await request.get(url)
    if (res.success) models.value = res.data
  } catch (e) { /* 失败则继续 */ }
}

async function loadAllSurcharges() {
  if (!form.value.product_type_id || !form.value.brand_id) {
    serviceSurcharges.value = {}
    return
  }
  try {
    const params = {
      product_type_id: form.value.product_type_id,
      brand_id: form.value.brand_id,
    }
    if (form.value.model_id && form.value.model_id !== 'brand_only') {
      params.model_id = form.value.model_id
    }
    const res = await request.get('/client/prices', { params })
    if (res.success && res.data) {
      serviceSurcharges.value = res.data
    }
  } catch (e) {
    serviceSurcharges.value = {}
  }
}

function handleSelectType(t) {
  selectedTypeId.value = t.id
  form.value.product_type_id = t.id
  form.value.category = ''
  form.value.category_id = null
  form.value.model_id = null
  form.value.brand_id = null
  form.value.service_type_id = null
  brands.value = []
  models.value = []
  services.value = []
  modelCategories.value = []
  loadBrands(t.id)
  // 如果没有类别选项，直接加载服务
  if (!t.categories) {
    loadServices()
  }
}

function handleSelectBrand(brand) {
  form.value.brand_id = brand.id
  form.value.category = ''
  form.value.category_id = null
  form.value.model_id = null
  form.value.service_type_id = null
  models.value = []
  modelCategories.value = [] // 清空配件类型
  serviceSurcharges.value = {}
  loadServices()
  loadAllSurcharges()
  loadModelCategories() // 加载配件类型
}

// 加载配件类型（从models表聚合）
async function loadModelCategories() {
  if (!form.value.brand_id || !form.value.product_type_id) return
  try {
    const res = await request.get(`/client/products/categories?brand_id=${form.value.brand_id}&product_type_id=${form.value.product_type_id}`)
    if (res.success && res.data) {
      modelCategories.value = res.data
    }
  } catch (e) {
    modelCategories.value = []
  }
}

function handleSelectService(svc) {
  form.value.service_type_id = svc.id
}

function handlePrev() { if (activeStep.value > 0) activeStep.value-- }

async function handleNext() {
  if (activeStep.value === 2) {
    const valid = await formRef.value?.validate().catch(() => false)
    if (!valid) return
  }
  if (activeStep.value < 3) activeStep.value++
}

async function handleSubmit() {
  if (!agreedTerms.value) { ElMessage.warning('请阅读并同意服务条款'); return }
  submitting.value = true
  try {
    const orderData = {
      items: [{
        product_type_id: selectedTypeId.value,
        brand_id: form.value.brand_id,
        model_id: form.value.model_id === 'brand_only' ? null : (form.value.model_id || null),
        model_name: form.value.model_id === 'brand_only' ? '' : (typeof form.value.model_id === 'string' ? form.value.model_id : (models.value.find(m => m.id === form.value.model_id)?.name || '')),
        service_type_id: form.value.service_type_id,
        category: form.value.category,
        quantity: 1,
      }],
      receiver_name: form.value.receiverName,
      receiver_phone: form.value.receiverPhone,
      receiver_address: form.value.delivery_type === 'express' ? form.value.receiverAddress : '到店交付',
      customer_remark: [form.value.model_input ? '设备型号: ' + form.value.model_input : '', form.value.last_maintenance ? '最后保养: ' + form.value.last_maintenance : '', form.value.remark ? '故障描述: ' + form.value.remark : ''].filter(Boolean).join('\n'),
      delivery_type: form.value.delivery_type,
      urgent_service: form.value.urgent_service ? 1 : 0,
    }

    const res = await request.post('/client/orders', orderData)
    if (res.success) {
      createdOrderId = res.data.id
      // 到店方式：自动完成支付（无需快递）；快递方式：需填快递单号
      if (form.value.delivery_type === 'store') {
        await request.post(`/client/orders/${createdOrderId}/pay`)
      }
      showSuccessDialog.value = true
    }
  } catch (e) {
    ElMessage.error(e.message || '提交失败')
  } finally {
    submitting.value = false
  }
}

async function handleSubmitExpress() {
  submittingExpress.value = true
  try {
    if (form.value.delivery_type === 'express') {
      if (!expressForm.value.no.trim()) { ElMessage.warning('请填写快递单号'); submittingExpress.value = false; return }
      await request.put(`/client/orders/${createdOrderId}/express`, {
        express_company: expressForm.value.company,
        express_no: expressForm.value.no,
      })
    }
    ElMessage.success(form.value.delivery_type === 'store' ? '预约成功！' : '订单提交成功！')
    showSuccessDialog.value = false
    router.push(`/order/${createdOrderId}/tracking`)
  } catch (e) {
    ElMessage.error('提交失败：' + (e.message || ''))
  } finally {
    submittingExpress.value = false
  }
}

function handleSkipExpress() {
  showSuccessDialog.value = false
  ElMessage.success('订单已提交，请尽快寄出设备并填写快递单号')
  router.push(`/order/${createdOrderId}/tracking`)
}

// 监听product_type_id变化
watch(() => form.value.product_type_id, () => {
  form.value.category = ''
  form.value.category_id = null
  form.value.model_id = null
  serviceSurcharges.value = {}
})

watch(() => form.value.model_id, () => {
  // 型号变化时重新加载加价（型号级别可能覆盖品牌级别）
  if (form.value.product_type_id && form.value.brand_id) {
    loadAllSurcharges()
  }
})

onMounted(() => { loadInitialData() })
</script>

<style scoped>
.category-display {
    background: linear-gradient(135deg, #e6f4ff, #f0f7ff);
    border: 2px solid #1677ff;
    border-radius: 12px;
    padding: 16px 24px;
    font-size: 18px;
    font-weight: 600;
    color: #1677ff;
    display: inline-block;
    margin-bottom: 16px;
}
.order-create-page { min-height: 100vh; background: #f5f7fa; }
.app-header { background: #fff; border-bottom: 1px solid #e5e6eb; position: sticky; top: 0; z-index: 10; }
.app-header-inner { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; }
.header-left { display: flex; align-items: center; gap: 4px; cursor: pointer; font-size: 14px; color: #1677ff; min-width: 60px; }
.header-title { font-size: 16px; font-weight: 600; color: #1d2129; }
.header-right { min-width: 60px; }
.loading-container { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 80px 0; }
.steps-container { background: #fff; padding: 16px; border-bottom: 1px solid #f0f0f0; }

.type-scroll { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 4px; }
.type-chip { padding: 8px 16px; border-radius: 20px; background: #f5f7fa; color: #4e5969; font-size: 13px; cursor: pointer; border: 1px solid #e5e6eb; transition: all 0.2s; }
.type-chip.is-active { background: #e6f4ff; color: #1677ff; border-color: #1677ff; }
.step-title { font-size: 14px; font-weight: 600; color: #1d2129; margin-bottom: 12px; }

.delivery-options { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 8px; }
.delivery-card { background: #fff; border: 2px solid #e5e6eb; border-radius: 12px; padding: 20px 12px; text-align: center; cursor: pointer; transition: all 0.2s; }
.delivery-card:hover { border-color: #1677ff; }
.delivery-card.is-selected { border-color: #1677ff; background: #f0f7ff; }
.delivery-icon { margin-bottom: 10px; }
.delivery-name { font-size: 14px; font-weight: 600; color: #1d2129; margin-bottom: 4px; }
.delivery-desc { font-size: 12px; color: #86909c; line-height: 1.4; }

.brand-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; }
.brand-card { background: #fff; border: 1px solid #e5e6eb; border-radius: 10px; padding: 16px; cursor: pointer; text-align: center; transition: all 0.2s; }
.brand-card:hover { border-color: #1677ff; box-shadow: 0 2px 8px rgba(22,119,255,0.1); }
.brand-card.is-selected { border-color: #1677ff; background: #e6f4ff; }
.brand-name { font-size: 14px; font-weight: 600; color: #1d2129; }
.brand-country { font-size: 12px; color: #86909c; margin-top: 4px; }
.model-input-area { background: #fff; border-radius: 10px; padding: 16px; border: 1px solid #e5e6eb; }
.input-tip { font-size: 12px; color: #86909c; margin-top: 8px; }
.page-container { padding: 16px; }

.service-list { display: flex; flex-direction: column; gap: 12px; }
.service-card { background: #fff; border: 1px solid #e5e6eb; border-radius: 10px; padding: 18px 16px; cursor: pointer; transition: all 0.2s; position: relative; }
.service-card:hover { border-color: #1677ff; }
.service-card.is-selected { border-color: #1677ff; background: #f0f7ff; }
.service-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.service-name { font-size: 15px; font-weight: 600; color: #1d2129; }
.service-price { display: flex; align-items: baseline; gap: 2px; }
.price-num { font-size: 20px; font-weight: 700; color: #1677ff; }
.price-unit { font-size: 12px; color: #86909c; }
.service-desc { font-size: 13px; color: #4e5969; line-height: 1.5; }
.service-check { position: absolute; top: 12px; right: 12px; }
.express-info-card { margin-top: 16px; background: #f0f7ff; border-color: #adc6ff; }
.express-info-title { display: flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: #1d2129; margin-bottom: 10px; }
.express-info-content { font-size: 13px; color: #4e5969; line-height: 1.8; }

.order-summary-card { margin-bottom: 16px; }
.summary-label { font-size: 13px; font-weight: 600; color: #86909c; margin-bottom: 8px; }
.summary-item { display: flex; padding: 4px 0; font-size: 14px; }
.summary-item .label { color: #86909c; width: 70px; flex-shrink: 0; }
.summary-item .value { color: #1d2129; }
.price-highlight { color: #1677ff; font-weight: 600; }
.total-price { display: flex; justify-content: space-between; align-items: center; font-size: 15px; font-weight: 600; color: #1d2129; }
.total-num { font-size: 24px; font-weight: 700; color: #1677ff; }
.freight-note { font-size: 12px; color: #86909c; text-align: right; margin-top: 4px; }

.bottom-actions { display: flex; gap: 12px; justify-content: center; margin-top: 20px; }
.bottom-actions .el-button { flex: 1; height: 44px; font-size: 15px; }

.success-content { text-align: center; }
.success-icon { margin-bottom: 12px; }
.success-title { font-size: 20px; font-weight: 700; color: #1d2129; margin-bottom: 6px; }
.success-subtitle { font-size: 13px; color: #86909c; margin-bottom: 4px; }
.express-form { text-align: left; }
.express-form-title { font-size: 14px; font-weight: 600; color: #1d2129; margin-bottom: 12px; }
.express-tip { font-size: 12px; color: #86909c; background: #f5f7fa; padding: 8px 12px; border-radius: 6px; margin-top: 8px; }
.store-info { text-align: left; }
.store-info-title { font-size: 14px; font-weight: 600; color: #1d2129; margin-bottom: 12px; }
.store-info-item { font-size: 13px; color: #4e5969; padding: 4px 0; }
.store-info-label { color: #86909c; }
.store-info-tip { font-size: 12px; color: #1677ff; background: #f0f7ff; padding: 8px 12px; border-radius: 6px; margin-top: 8px; }
</style>
