<template>
  <div class="simulate-flow">
    <div class="page-header">
      <div class="title-row">
        <h1>模拟流程</h1>
        <span class="badge">管理员专用</span>
      </div>
      <p class="subtitle">完整模拟客户下单到完成的全流程，用于测试每个环节是否正常</p>
    </div>

    <!-- 步骤指示器 -->
    <div v-if="currentStep > 0" class="step-indicator">
      <div
        v-for="(step, idx) in steps"
        :key="idx"
        :class="['step-item', { done: idx + 1 < currentStep, active: idx + 1 === currentStep, pending: idx + 1 > currentStep }]"
      >
        <div class="step-circle">
          <span v-if="idx + 1 < currentStep">&#10003;</span>
          <span v-else>{{ idx + 1 }}</span>
        </div>
        <div class="step-label">{{ step.label }}</div>
      </div>
    </div>

    <!-- Step 0: 开始 -->
    <div v-if="currentStep === 0" class="init-panel">
      <el-card shadow="never" class="init-card">
        <template #header><span>开始模拟</span></template>
        <p>点击下方按钮，系统将自动创建一个<strong>测试订单</strong>，并以管理员身份逐步走完整个维修流程。</p>
        <p class="tips">测试订单会标记为 is_simulation=1，不会影响真实客户数据</p>
        <div class="init-actions">
          <el-button type="primary" size="large" @click="startSimulate" :loading="submitting">
            开始模拟
          </el-button>
          <el-button size="large" @click="doCleanup" :loading="cleaning">
            清理测试订单
          </el-button>
        </div>
        <div v-if="cleanupMsg" :class="['cleanup-msg', cleanupMsg.type]">{{ cleanupMsg.text }}</div>
      </el-card>
    </div>

    <!-- Step 1-7: 执行步骤 -->
    <div v-if="currentStep > 0 && currentStep <= steps.length" class="step-panel">
      <el-card shadow="never" class="current-step-card">
        <template #header>
          <div class="card-header">
            <span class="step-badge">Step {{ currentStep }} / {{ steps.length }}</span>
            <span class="step-title">{{ currentStepData.label }}</span>
            <el-tag v-if="simOrder" type="info" size="small">订单 #{{ simOrder.order_id }}</el-tag>
          </div>
        </template>

        <div class="step-desc"><p>{{ currentStepData.desc }}</p></div>

        <div class="step-content">
          <!-- Step 1: 填写订单 -->
          <template v-if="currentStep === 1">
            <div class="form-grid">
              <div class="form-item">
                <label>产品类别</label>
                <el-select v-model="formData.productType" placeholder="选择产品类别" clearable @change="onProductTypeChange">
                  <el-option v-for="pt in productTypes" :key="pt.id" :label="pt.name" :value="pt.id" />
                </el-select>
              </div>
              <div class="form-item">
                <label>品牌</label>
                <el-select v-model="formData.brand" placeholder="先选产品类别" clearable :disabled="!formData.productType" @change="onBrandChange">
                  <el-option v-for="b in brands" :key="b.id" :label="b.name" :value="b.id" />
                </el-select>
              </div>
              <div class="form-item">
                <label>型号（选填）</label>
                <el-select v-model="formData.model" placeholder="先选品牌" clearable :disabled="!formData.brand">
                  <el-option v-for="m in models" :key="m.id" :label="m.name" :value="m.id" />
                </el-select>
              </div>
              <div class="form-item">
                <label>服务类型</label>
                <el-select v-model="formData.serviceType" placeholder="选择服务" clearable>
                  <el-option v-for="st in filteredServiceTypes" :key="st.id" :label="`${st.name} (${st.base_price}元)`" :value="st.id" />
                </el-select>
              </div>
              <div class="form-item">
                <label>交付方式</label>
                <el-select v-model="formData.deliveryType" placeholder="选择交付方式">
                  <el-option label="快递寄送" value="express" />
                  <el-option label="自行到店交付" value="store" />
                </el-select>
              </div>
            </div>
            <p v-if="noServiceHint" class="no-data-hint">当前产品类别暂无服务类型，请先在数据管理中添加</p>
          </template>

          <!-- Step 2: 确认收货 -->
          <template v-if="currentStep === 2">
            <div class="form-grid">
              <div class="form-item">
                <label>快递公司</label>
                <el-select v-model="expressForm.company" placeholder="选择或输入快递公司" clearable filterable allow-create default-first-option>
                  <el-option v-for="c in courierList" :key="c" :label="c" :value="c" />
                </el-select>
              </div>
              <div class="form-item">
                <label>快递单号</label>
                <el-input v-model="expressForm.trackingNo" placeholder="输入快递单号" />
              </div>
              <div class="form-item">
                <label>外包装情况</label>
                <el-select v-model="packagingCondition" placeholder="选择外包装情况">
                  <el-option label="完好" value="完好" />
                  <el-option label="破损" value="破损" />
                </el-select>
              </div>
            </div>
            <div class="upload-section">
              <label>📸 快递未拆邮包照片（可选，对应第2步确认收货）</label>
              <input type="file" ref="receivePhotoRef" accept="image/*" @change="onFileSelected('receive')" />
              <div v-if="uploadedPhotos.receive" class="photo-preview">
                <img :src="uploadedPhotos.receive" alt="未拆邮包照片" />
              </div>
            </div>
            <div class="upload-section">
              <label>快递拆邮包照片（可选，对应第3步开箱记录）</label>
              <input type="file" ref="unboxPhotoRef" accept="image/*" @change="onFileSelected('unbox')" />
              <div v-if="uploadedPhotos.unbox" class="photo-preview">
                <img :src="uploadedPhotos.unbox" alt="拆邮包照片" />
              </div>
            </div>
          </template>

          <!-- Step 3: 设备拆解记录 -->
          <template v-if="currentStep === 3">
            <div class="upload-section">
              <label>设备拆解后状态照片（拆解后、维修保养前）</label>
              <input type="file" ref="inspectPhotoRef" accept="image/*" multiple @change="onFileSelected('inspect')" />
              <div v-if="uploadedPhotos.inspect.length" class="photo-grid">
                <img v-for="(p, i) in uploadedPhotos.inspect" :key="i" :src="p" alt="拆解状态照片" class="photo-thumb" />
              </div>
            </div>
            <el-input v-model="stepNote" rows="4" type="textarea" placeholder="填写设备拆解后检验发现，如：O型圈老化需更换，一级头漏气，二级头呼吸阻力大" />
            <p class="tips" style="margin-top:8px">提示：邮包照片已在第2步上传，此处上传设备拆解后的状态照片</p>
          </template>

          <!-- Step 4: 维修保养 -->
          <template v-if="currentStep === 4">
            <el-input v-model="stepNote" rows="4" type="textarea" placeholder="填写维修内容，如：已更换O型圈，完成一级头保养，二级头校准" />
            <div class="upload-section">
              <label>维修过程照片（可多张）</label>
              <input type="file" ref="repairPhotoRef" accept="image/*" multiple @change="onFileSelected('repair')" />
              <div v-if="uploadedPhotos.repair.length" class="photo-grid">
                <img v-for="(p, i) in uploadedPhotos.repair" :key="i" :src="p" alt="维修照片" class="photo-thumb" />
              </div>
            </div>
          </template>

          <!-- Step 5: 质检通过 -->
          <template v-if="currentStep === 5">
            <el-input v-model="stepNote" rows="4" type="textarea" placeholder="填写质检结果，如：所有项目达标，设备性能正常" />
            <div class="upload-section">
              <label>质检照片（可多张）</label>
              <input type="file" ref="qcPhotoRef" accept="image/*" multiple @change="onFileSelected('qc')" />
              <div v-if="uploadedPhotos.qc.length" class="photo-grid">
                <img v-for="(p, i) in uploadedPhotos.qc" :key="i" :src="p" alt="质检照片" class="photo-thumb" />
              </div>
            </div>
          </template>

          <!-- Step 6: 设备发出 -->
          <template v-if="currentStep === 6">
            <div class="form-grid">
              <div class="form-item">
                <label>快递公司</label>
                <el-select v-model="expressForm.company" placeholder="选择或输入快递公司" clearable filterable allow-create default-first-option>
                  <el-option v-for="c in courierList" :key="c" :label="c" :value="c" />
                </el-select>
              </div>
              <div class="form-item">
                <label>快递单号</label>
                <el-input v-model="expressForm.trackingNo" placeholder="输入快递单号" />
              </div>
            </div>
            <el-input v-model="stepNote" rows="2" type="textarea" placeholder="备注信息（可选）" class="mt-sm" />
            <div class="upload-section">
              <label>打包发出照片（可选）</label>
              <input type="file" ref="shipPhotoRef" accept="image/*" @change="onFileSelected('ship')" />
              <div v-if="uploadedPhotos.ship" class="photo-preview">
                <img :src="uploadedPhotos.ship" alt="已上传" />
              </div>
            </div>
          </template>

          <!-- Step 7: 订单完成 -->
          <template v-if="currentStep === 7">
            <el-alert type="warning" :closable="false" show-icon>
              <template #title>确认完成</template>
              <p>确认后订单将标记为已完成，系统自动推送微信通知给客户，客户即可查看和下载PDF维修报告。</p>
            </el-alert>
            <el-input v-model="stepNote" rows="2" type="textarea" placeholder="完成备注（可选）" class="mt-sm" />
          </template>
        </div>

        <div class="step-actions">
          <el-button @click="goBack">{{ currentStep > 1 ? '上一步' : '返回首页' }}</el-button>
          <el-button type="primary" @click="executeStep" :loading="submitting">
            {{ currentStep < steps.length ? '执行此步骤' : '完成全流程' }}
          </el-button>
          <el-button type="danger" plain size="small" @click="resetAll">终止模拟</el-button>
        </div>
      </el-card>

      <!-- 已完成步骤 -->
      <div v-if="history.length" class="step-history">
        <h3>已完成步骤</h3>
        <el-timeline>
          <el-timeline-item
            v-for="(h, idx) in history"
            :key="idx"
            :type="h.success ? 'success' : 'danger'"
            :timestamp="h.time"
            placement="top"
          >
            <el-card shadow="never" class="history-card">
              <template #header>
                <span>{{ h.step }}</span>
                <el-tag :type="h.success ? 'success' : 'danger'" size="small">{{ h.success ? '成功' : '失败' }}</el-tag>
              </template>
              <p>{{ h.message }}</p>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>

      <!-- 完成面板 -->
      <div v-if="flowComplete" class="complete-panel">
        <el-alert type="success" :closable="false" show-icon>
          <template #title>模拟流程完成</template>
          <p>所有步骤执行成功，PDF报告已生成，客户微信端已收到通知。</p>
        </el-alert>
        <div class="complete-actions">
          <el-button type="primary" @click="viewPdf">查看PDF报告</el-button>
          <el-button @click="resetAll">重新模拟</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import request from '@/utils/request'
import { ElMessage as B } from 'element-plus'
import { useStaffStore } from '@/stores/staff'

const steps = [
  { code: 'create', label: 'Step1: 填写订单', desc: '填写模拟订单的设备和服务信息，选择交付方式' },
  { code: 'receive', label: 'Step2: 确认收货', desc: '填写快递信息，确认收货' },
  { code: 'inspect', label: 'Step3: 设备拆解记录', desc: '全面拆解设备各组件，记录磨损/损坏情况，上传各部件照片' },
  { code: 'repair', label: 'Step4: 维修保养', desc: '按维修清单操作，更换磨损配件，填写维修记录，上传过程照片' },
  { code: 'qc', label: 'Step5: 质检通过', desc: '全面功能测试，记录测试结果，上传质检照片，系统自动生成PDF报告' },
  { code: 'ship', label: 'Step6: 设备发出', desc: '填写回寄快递信息，上传打包照片' },
  { code: 'complete', label: 'Step7: 订单完成', desc: '确认完成，微信通知接口已预留' }
]

const courierList = ['顺丰速运', '中通快递', '圆通速递', '韵达快递', '申通快递', '京东物流', 'EMS', '极兔速递']

const currentStep = ref(0)
const submitting = ref(false)
const cleaning = ref(false)
const cleanupMsg = ref(null)
const simOrder = ref(null)
const stepNote = ref('')
const history = ref([])
const flowComplete = ref(false)

const formData = ref({ productType: null, brand: null, model: null, serviceType: null, deliveryType: 'express' })
const expressForm = ref({ company: '', trackingNo: '' })
const packagingCondition = ref('完好')

const productTypes = ref([])
const serviceTypes = ref([])
const brands = ref([])
const models = ref([])

const uploadedPhotos = ref({ receive: null, unbox: null, inspect: [], repair: [], qc: [], ship: null })

const receivePhotoRef = ref(null)
const unboxPhotoRef = ref(null)
const inspectPhotoRef = ref(null)
const repairPhotoRef = ref(null)
const qcPhotoRef = ref(null)
const shipPhotoRef = ref(null)

const currentStepData = computed(() => steps[currentStep.value - 1] || {})

// 服务类型按产品类别过滤
const filteredServiceTypes = computed(() => {
  if (!formData.value.productType) return serviceTypes.value
  return serviceTypes.value.filter(st => st.product_type_id === formData.value.productType)
})
const noServiceHint = computed(() => formData.value.productType && filteredServiceTypes.value.length === 0)

onMounted(() => { loadStaticData() })

// ===== 数据加载 =====
async function loadStaticData() {
  try {
    const [ptRes, svRes] = await Promise.all([
      request.get('/admin/product-types'),
      request.get('/admin/service-types')
    ])
    productTypes.value = Array.isArray(ptRes) ? ptRes : (ptRes.data || [])
    serviceTypes.value = Array.isArray(svRes) ? svRes : (svRes.data || [])
  } catch { productTypes.value = []; serviceTypes.value = [] }
}

// 产品类别变化 → 加载品牌
async function onProductTypeChange() {
  formData.value.brand = null
  formData.value.model = null
  formData.value.serviceType = null
  brands.value = []
  models.value = []
  if (!formData.value.productType) return
  try {
    const res = await request.get('/admin/brands', { params: { type_id: formData.value.productType } })
    brands.value = Array.isArray(res) ? res : (res.data || [])
  } catch { brands.value = [] }
}

// 品牌变化 → 加载型号
async function onBrandChange() {
  formData.value.model = null
  models.value = []
  if (!formData.value.brand) return
  try {
    const res = await request.get('/admin/models', { params: { brand_id: formData.value.brand } })
    models.value = Array.isArray(res) ? res : (res.data || [])
  } catch { models.value = [] }
}

// ===== 照片上传（压缩） =====
function compressImage(file, maxWidth = 1200) {
  return new Promise((resolve) => {
    const reader = new FileReader()
    reader.onload = (ev) => {
      const img = new Image()
      img.onload = () => {
        const canvas = document.createElement('canvas')
        let w = img.width, h = img.height
        if (w > maxWidth) { h = Math.round(h * maxWidth / w); w = maxWidth }
        canvas.width = w; canvas.height = h
        canvas.getContext('2d').drawImage(img, 0, 0, w, h)
        resolve(canvas.toDataURL('image/jpeg', 0.7))
      }
      img.onerror = () => resolve(ev.target.result)
      img.src = ev.target.result
    }
    reader.readAsDataURL(file)
  })
}

function onFileSelected(step) {
  const refs = { receive: receivePhotoRef, unbox: unboxPhotoRef, inspect: inspectPhotoRef, repair: repairPhotoRef, qc: qcPhotoRef, ship: shipPhotoRef }
  const input = refs[step]?.value
  if (!input?.files?.length) return
  if (step === 'receive' || step === 'ship' || step === 'unbox') {
    const file = input.files[0]
    compressImage(file).then(compressed => { uploadedPhotos.value[step] = compressed })
  } else {
    const promises = Array.from(input.files).map(file => compressImage(file))
    Promise.all(promises).then(results => { uploadedPhotos.value[step].push(...results) })
  }
}

// ===== 核心流程 =====
async function startSimulate() {
  submitting.value = true
  try {
    const res = await request.post('/simulate/create', {})
    if (!res.success) { B.error(res.message || '创建失败'); return }
    simOrder.value = res.data
    history.value = []
    flowComplete.value = false
    currentStep.value = 1
    B.success(`模拟订单创建成功: #${res.data.order_id}`)
  } catch (e) { B.error('创建模拟订单失败: ' + (e.message || '未知错误')) }
  finally { submitting.value = false }
}

async function executeStep() {
  if (!simOrder.value) return
  submitting.value = true
  const step = steps[currentStep.value - 1]

  try {
    let payload = {}

    if (currentStep.value === 1) {
      // Step1: 填写订单
      if (!formData.value.productType) { B.warning('请选择产品类别'); submitting.value = false; return }
      if (!formData.value.serviceType) { B.warning('请选择服务类型'); submitting.value = false; return }
      payload = {
        product_type_id: formData.value.productType,
        brand_id: formData.value.brand || null,
        model_id: formData.value.model || null,
        service_type_id: formData.value.serviceType,
        delivery_type: formData.value.deliveryType || 'express'
      }
    } else if (currentStep.value === 2) {
      // Step2: 确认收货 - 快递信息 + 外包装情况 + 未拆邮包照片 + 拆邮包照片
      payload = {
        note: stepNote.value || '',
        express_company: expressForm.value.company || '',
        express_no: expressForm.value.trackingNo || '',
        packaging_condition: packagingCondition.value || '完好',
        photos: uploadedPhotos.value.receive ? [uploadedPhotos.value.receive] : [],
        unbox_photos: uploadedPhotos.value.unbox ? [uploadedPhotos.value.unbox] : []
      }
      // 保存开箱照片到临时变量，step 3执行时发送
      if (uploadedPhotos.value.unbox) {
        window._pendingUnboxPhoto = uploadedPhotos.value.unbox
      }
    } else if (currentStep.value === 3) {
      // Step3: 设备拆解记录 - 拆解后状态照片 + 检验文字
      payload = {
        note: stepNote.value || '',
        photos: uploadedPhotos.value.inspect || []
      }
    } else if (currentStep.value === 6) {
      // Step6: 设备发出 - 回寄快递
      payload = {
        note: stepNote.value || '',
        return_express_company: expressForm.value.company || '',
        return_express_no: expressForm.value.trackingNo || '',
        photos: uploadedPhotos.value.ship ? [uploadedPhotos.value.ship] : []
      }
    } else {
      // Step3-5, 7: 文字+照片
      payload = {
        note: stepNote.value || '',
        photos: getStepPhotos()
      }
    }

    const res = await request.post(`/simulate/${simOrder.value.order_id}/step/${step.code}`, payload, { timeout: 120000 })
    if (!res.success) throw new Error(res.message || '步骤执行失败')

    history.value.push({
      step: step.label,
      success: true,
      time: new Date().toLocaleString('zh-CN'),
      message: `${step.label} 执行成功`,
      nodeId: res.data?.node_id || null
    })

    if (currentStep.value < steps.length) {
      currentStep.value++
      stepNote.value = ''
      expressForm.value = { company: '', trackingNo: '' }
      uploadedPhotos.value = { receive: null, unbox: null, inspect: [], repair: [], qc: [], ship: null }
    } else {
      flowComplete.value = true
    }
  } catch (e) {
    history.value.push({
      step: step.label,
      success: false,
      time: new Date().toLocaleString('zh-CN'),
      message: '执行失败: ' + (e.message || '未知错误')
    })
    B.error('步骤执行失败: ' + (e.message || ''))
  } finally { submitting.value = false }
}

function getStepPhotos() {
  const step = steps[currentStep.value - 1].code
  if (step === 'repair') return uploadedPhotos.value.repair
  if (step === 'qc') return uploadedPhotos.value.qc
  return []
}

function goBack() {
  if (currentStep.value > 1) currentStep.value--
  else { currentStep.value = 0; simOrder.value = null; history.value = [] }
}

function resetAll() {
  currentStep.value = 0
  simOrder.value = null
  history.value = []
  flowComplete.value = false
  stepNote.value = ''
  formData.value = { productType: null, brand: null, model: null, serviceType: null, deliveryType: 'express' }
  expressForm.value = { company: '', trackingNo: '' }
  packagingCondition.value = '完好'
  uploadedPhotos.value = { receive: null, unbox: null, inspect: [], repair: [], qc: [], ship: null }
  delete window._pendingUnboxPhoto
}

async function doCleanup() {
  cleaning.value = true
  cleanupMsg.value = null
  try {
    const res = await request.post('/simulate/cleanup', {})
    cleanupMsg.value = { type: 'success', text: res.message || '清理完成' }
    B.success('清理完成')
  } catch (e) {
    cleanupMsg.value = { type: 'error', text: e.message || '清理失败' }
    B.error('清理失败')
  } finally { cleaning.value = false }
}

function viewPdf() {
  if (!simOrder.value) return
  const staffStore = useStaffStore()
  const token = staffStore.token || ''
  // 直接打开URL（不用axios），浏览器直接下载/预览PDF
  const url = `/selforder-api/console/orders/${simOrder.value.order_id}/report-pdf?token=${encodeURIComponent(token)}`
  window.open(url, '_blank')
}
</script>

<style scoped>
.simulate-flow { max-width: 900px; margin: 0 auto; padding: 24px; }
.page-header { margin-bottom: 24px; }
.title-row { display: flex; align-items: center; gap: 12px; }
.title-row h1 { font-size: 22px; font-weight: 600; margin: 0; }
.badge { background: #409eff; color: #fff; font-size: 11px; padding: 2px 8px; border-radius: 10px; }
.subtitle { color: #909399; font-size: 13px; margin-top: 6px; }

.step-indicator { display: flex; gap: 4px; margin-bottom: 24px; overflow-x: auto; padding: 12px 0; }
.step-item { display: flex; flex-direction: column; align-items: center; min-width: 70px; flex: 1; }
.step-circle { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 600; border: 2px solid #dcdfe6; color: #909399; background: #fff; }
.step-item.done .step-circle { background: #67c23a; color: #fff; border-color: #67c23a; }
.step-item.active .step-circle { background: #409eff; color: #fff; border-color: #409eff; }
.step-label { font-size: 11px; margin-top: 6px; color: #909399; text-align: center; white-space: nowrap; }
.step-item.active .step-label { color: #409eff; font-weight: 600; }

.init-panel .init-card { text-align: center; }
.init-actions { display: flex; gap: 12px; justify-content: center; margin-top: 20px; }
.tips { color: #e6a23c; font-size: 12px; margin-top: 8px; }
.cleanup-msg { margin-top: 12px; padding: 8px 12px; border-radius: 6px; font-size: 13px; }
.cleanup-msg.success { background: #f0f9eb; color: #67c23a; }
.cleanup-msg.error { background: #fef0f0; color: #f56c6c; }

.card-header { display: flex; align-items: center; gap: 10px; }
.step-badge { background: #409eff; color: #fff; font-size: 11px; padding: 2px 8px; border-radius: 10px; }
.step-title { font-weight: 600; }
.step-desc { color: #909399; font-size: 13px; margin-bottom: 16px; }

.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.form-item { display: flex; flex-direction: column; gap: 6px; }
.form-item label { font-size: 13px; font-weight: 500; color: #606266; }

.upload-section { margin-top: 16px; }
.upload-section label { font-size: 13px; font-weight: 500; color: #606266; display: block; margin-bottom: 8px; }
.upload-section input[type="file"] { font-size: 13px; }
.photo-grid { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
.photo-thumb { width: 80px; height: 80px; object-fit: cover; border-radius: 6px; border: 1px solid #ebeef5; }
.photo-preview { margin-top: 8px; }
.photo-preview img { max-width: 200px; max-height: 150px; border-radius: 6px; border: 1px solid #ebeef5; }

.no-data-hint { color: #e6a23c; font-size: 12px; margin-top: 8px; }
.mt-sm { margin-top: 12px; }

.step-actions { display: flex; gap: 12px; margin-top: 20px; }

.step-history { margin-top: 24px; }
.step-history h3 { font-size: 15px; margin-bottom: 12px; }
.history-card :deep(.el-card__header) { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; }

.complete-panel { margin-top: 24px; }
.complete-actions { display: flex; gap: 12px; margin-top: 16px; }
</style>
