import { ref, computed, provide, onMounted, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'
import { useStaffStore } from '@/stores/staff'

export const WORKFLOW_INJECT_KEY = Symbol('techWorkflow')

const STEPS = [
  { code: 'receive', nodeCode: 'received', shortLabel: '收货', label: 'Step 1: 确认收货', desc: '检查设备包装是否完好，记录收货情况' },
  { code: 'inspect', nodeCode: 'inspect', shortLabel: '检验', label: 'Step 2: 拆件检验', desc: '拆解设备，检查内部状况，记录磨损/损坏情况' },
  { code: 'repair', nodeCode: 'repair', shortLabel: '维修', label: 'Step 3: 维修保养', desc: '按维修清单操作，更换磨损配件，填写维修记录' },
  { code: 'qc', nodeCode: 'qc', shortLabel: '质检', label: 'Step 4: 质检通过', desc: '全面功能测试，系统自动生成PDF维修报告' },
  { code: 'ship', nodeCode: 'shipped', shortLabel: '发货', label: 'Step 5: 设备发出', desc: '填写回寄快递信息，上传打包照片' },
  { code: 'complete', nodeCode: 'completed', shortLabel: '完成', label: 'Step 6: 订单完成', desc: '确认客户已收货，订单完结' }
]

const courierList = ['顺丰速运', '圆通速递', '中通快递', '韵达速递', '申通快递', '极兔速递', '京东快递', '邮政EMS', '德邦快递', '其他']
const returnCourierList = ['顺丰速运']

export function useTechWorkflow() {
  const route = useRoute()
  const router = useRouter()

  const stepIndex = ref(0)
  const subPageIndex = ref(0)
  const note = ref('')
  const photos = ref([])
  const currentNodeId = ref(null)
  const nodeData = ref(null)
  const submitting = ref(false)
  const navigating = ref(false)
  const stepSubmitted = ref(false)
  const doneSubPageIndex = ref(0)
  const navHistory = ref([])
  const previewUrl = ref('')
  const allNodes = ref([])
  const initialLoad = ref(true)
  const pdfLoading = ref(false)
  const equipmentData = ref([])
  const serviceItems = ref([])
  const selectedServiceItems = ref([])
  const serviceLoadFailed = ref(false)
  const orderData = ref(null)

  const formData = ref({
    expressCompany: '', expressNo: '', packaging: '完好',
    shipCompany: '', shipNo: ''
  })
  const localPhotos = ref({ unbox: null, unbox_opened: null, ship: null })
  const localMultiPhotos = ref({ inspect: [], repair: [], qc: [] })

  const currentStep = computed(() => STEPS[stepIndex.value] || {})
  const isLastStep = computed(() => stepIndex.value === STEPS.length - 1)

  function isStepDone(index) {
    return allNodes.value.some(n => n.node_code === STEPS[index]?.nodeCode)
  }

  // ===== 导航历史栈 =====
  function pushNav() {
    navHistory.value.push({
      stepIndex: stepIndex.value, subPageIndex: subPageIndex.value,
      doneSubPageIndex: doneSubPageIndex.value, stepSubmitted: stepSubmitted.value
    })
  }
  function goForwardSub(_oldVal, newVal) {
    pushNav()
    subPageIndex.value = newVal
  }
  function goForwardDone(_oldVal, newVal) {
    pushNav()
    doneSubPageIndex.value = newVal
  }
  function goBackDoneSub() {
    if (navHistory.value.length === 0) return
    const prev = navHistory.value.pop()
    doneSubPageIndex.value = prev.doneSubPageIndex
  }

  // ===== 数据加载 =====
  function determineCurrentStep(nodes) {
    for (let i = STEPS.length - 1; i >= 0; i--) {
      if (nodes.some(n => n.node_code === STEPS[i].nodeCode)) {
        return Math.min(i + 1, STEPS.length - 1)
      }
    }
    return 0
  }

  function parsePhotos(node) {
    if (!node.photos) return []
    try {
      const ps = typeof node.photos === 'string' ? JSON.parse(node.photos) : node.photos
      if (Array.isArray(ps)) {
        return ps.map(item => {
          if (typeof item === 'object' && item.path) {
            const path = item.path
            if (path.startsWith('orders/'))
              return { url: `/uploads/${path}`, filename: path.split('/').pop(), type: item.type || 'unknown' }
            else
              return { url: `/uploads/orders/${route.params.id}/nodes/${node.id}/${path}`, filename: path, type: item.type || 'unknown' }
          }
          if (typeof item === 'string') {
            if (item.startsWith('orders/'))
              return { url: `/uploads/${item}`, filename: item.split('/').pop(), type: 'unknown' }
            else
              return { url: `/uploads/orders/${route.params.id}/nodes/${node.id}/${item}`, filename: item, type: 'unknown' }
          }
          return null
        }).filter(Boolean)
      }
    } catch {}
    return []
  }

  function padArray(arr, length, defaultVal) {
    const result = [...arr]
    while (result.length < length) result.push(defaultVal)
    return result.slice(0, length)
  }

  function initEquipmentData(orderItems) {
    equipmentData.value = orderItems.map(item => ({
      order_item_id: item.id,
      product_type_name: item.product_type_name || '',
      brand_name: item.brand_name || '',
      model_name: item.model_name || '',
      quantity: item.quantity || 1,
      inspection_data: {
        first_stage_count: 1, first_stage_serials: [''],
        first_stage_pre_pressure: [null], first_stage_post_pressure: [null],
        second_stage_count: 1, second_stage_serials: [''],
        second_stage_pre_resistance: [null], second_stage_post_resistance: [null]
      }
    }))
  }

  function updateFirstStageArrays(item) {
    const count = item.inspection_data.first_stage_count || 0
    const current = item.inspection_data.first_stage_serials.length
    if (count > current) {
      for (let i = current; i < count; i++) {
        item.inspection_data.first_stage_serials.push('')
        item.inspection_data.first_stage_pre_pressure.push(null)
        item.inspection_data.first_stage_post_pressure.push(null)
      }
    } else if (count < current) {
      item.inspection_data.first_stage_serials = item.inspection_data.first_stage_serials.slice(0, count)
      item.inspection_data.first_stage_pre_pressure = item.inspection_data.first_stage_pre_pressure.slice(0, count)
      item.inspection_data.first_stage_post_pressure = item.inspection_data.first_stage_post_pressure.slice(0, count)
    }
  }

  function updateSecondStageArrays(item) {
    const count = item.inspection_data.second_stage_count || 0
    const current = item.inspection_data.second_stage_serials.length
    if (count > current) {
      for (let i = current; i < count; i++) {
        item.inspection_data.second_stage_serials.push('')
        item.inspection_data.second_stage_pre_resistance.push(null)
        item.inspection_data.second_stage_post_resistance.push(null)
      }
    } else if (count < current) {
      item.inspection_data.second_stage_serials = item.inspection_data.second_stage_serials.slice(0, count)
      item.inspection_data.second_stage_pre_resistance = item.inspection_data.second_stage_pre_resistance.slice(0, count)
      item.inspection_data.second_stage_post_resistance = item.inspection_data.second_stage_post_resistance.slice(0, count)
    }
  }

  async function loadEquipmentData() {
    try {
      const res = await request.get(`/orders/${route.params.id}/equipment-data`)
      if (res.success && res.data) {
        equipmentData.value = res.data.map(item => {
          const ins = item.inspection_data || {}
          const fs_cnt = ins.first_stage_count ?? 1
          const ss_cnt = ins.second_stage_count ?? 1
          return {
            ...item,
            inspection_data: {
              first_stage_count: fs_cnt,
              first_stage_serials: padArray(ins.first_stage_serials || [], fs_cnt, ''),
              first_stage_pre_pressure: padArray(ins.first_stage_pre_pressure || [], fs_cnt, null),
              first_stage_post_pressure: padArray(ins.first_stage_post_pressure || [], fs_cnt, null),
              second_stage_count: ss_cnt,
              second_stage_serials: padArray(ins.second_stage_serials || [], ss_cnt, ''),
              second_stage_pre_resistance: padArray(ins.second_stage_pre_resistance || [], ss_cnt, null),
              second_stage_post_resistance: padArray(ins.second_stage_post_resistance || [], ss_cnt, null)
            }
          }
        })
      }
    } catch (e) {
      console.error('loadEquipmentData error:', e)
    }
  }

  async function saveEquipmentData() {
    const missing = []
    for (const item of equipmentData.value) {
      const d = item.inspection_data
      const label = `${item.brand_name} ${item.model_name}`
      for (let i = 0; i < (d.first_stage_count || 0); i++) {
        if (!d.first_stage_serials[i]?.trim()) missing.push(`${label} 一级头#${i+1} 序列号`)
        if (!d.first_stage_pre_pressure[i]?.trim()) missing.push(`${label} 一级头#${i+1} 保养前中压`)
      }
      for (let i = 0; i < (d.second_stage_count || 0); i++) {
        if (!d.second_stage_serials[i]?.trim()) missing.push(`${label} 二级头#${i+1} 序列号`)
        if (!d.second_stage_pre_resistance[i]?.trim()) missing.push(`${label} 二级头#${i+1} 保养前抗阻`)
      }
    }
    if (missing.length > 0) {
      try {
        await ElMessageBox.confirm(
          `以下信息未填写，报告中该数据将显示为"-"：\n\n${missing.slice(0, 8).join('\n')}${missing.length > 8 ? '\n...等共' + missing.length + '项' : ''}\n\n是否仍要保存？`,
          '数据不完整',
          { confirmButtonText: '仍然保存', cancelButtonText: '返回补充', type: 'warning' }
        )
      } catch {
        submitting.value = false
        return
      }
    }
    submitting.value = true
    try {
      const res = await request.post(`/orders/${route.params.id}/equipment-data`, { items: equipmentData.value })
      if (res.success) {
        ElMessage.success('设备信息已保存')
        pushNav()
        subPageIndex.value = 1
        await loadOrderData()
      } else {
        ElMessage.error(res.message || '保存失败')
      }
    } catch (e) {
      ElMessage.error('保存失败: ' + (e.response?.data?.message || e.message || ''))
    } finally {
      submitting.value = false
    }
  }

  async function loadServiceItems(orderDataArg) {
    try {
      const items = orderDataArg?.items || []
      const productTypeIds = [...new Set(items.map(i => i.product_type_id).filter(Boolean))]
      if (productTypeIds.length === 0) { serviceItems.value = []; return }
      const allItems = []
      let hasAuthError = false
      for (const ptId of productTypeIds) {
        try {
          const res = await request.get(`/service-items?product_type_id=${ptId}`)
          if (res.success && res.data) allItems.push(...res.data)
        } catch (innerErr) {
          if (innerErr?.message && innerErr.message.includes('token')) hasAuthError = true
          console.error('loadServiceItems error (pt_id=' + ptId + '):', innerErr?.message || innerErr)
        }
      }
      serviceItems.value = allItems
      if (hasAuthError && allItems.length === 0) {
        serviceLoadFailed.value = true
        ElMessage.error('登录已过期，请返回订单列表后重新登录')
      } else if (allItems.length === 0 && productTypeIds.length > 0) {
        serviceLoadFailed.value = true
        ElMessage.warning('未找到该产品类别的维修检项，请先在数据管理中配置')
      } else {
        serviceLoadFailed.value = false
      }
      const repairNode = allNodes.value.find(n => n.node_code === 'repair')
      if (repairNode && repairNode.description) {
        const desc = repairNode.description
        if (desc.startsWith('维修检项：')) {
          const names = desc.replace('维修检项：', '').split('、')
          selectedServiceItems.value = allItems.filter(item => names.includes(item.name)).map(item => item.id)
        }
      }
    } catch (e) {
      serviceLoadFailed.value = true
      console.error('loadServiceItems error:', e)
      ElMessage.error('加载维修检项失败：' + (e?.message || '未知错误'))
    }
  }

  async function loadOrderData() {
    try {
      const res = await request.get(`/orders/${route.params.id}`)
      if (res.success && res.data) {
        const nodes = res.data.tracking_nodes || []
        allNodes.value = nodes
        const nc = STEPS[stepIndex.value]?.nodeCode
        const stepNodes = nodes.filter(n => n.node_code === nc)
        const node = stepNodes.length > 0 ? stepNodes[stepNodes.length - 1] : null
        currentNodeId.value = node?.id || null
        nodeData.value = node ? { ...node } : node
        if (node) { note.value = node.operate_note || ''; photos.value = parsePhotos(node) }
        else { note.value = ''; photos.value = [] }
        orderData.value = res.data
        prefillFromNodeData()
        if (stepIndex.value === 2) await loadServiceItems(res.data)
      }
    } catch (e) { console.error('loadOrderData error:', e) }
  }

  function prefillFromNodeData() {
    if (stepIndex.value === 0) {
      const ec = nodeData.value?.express_company || (orderData.value?.express_company) || ''
      const en = nodeData.value?.express_no || (orderData.value?.express_no) || ''
      if (ec) formData.value.expressCompany = ec
      if (en) formData.value.expressNo = en
      if (nodeData.value?.packaging_condition) formData.value.packaging = nodeData.value.packaging_condition
    }
    if (stepIndex.value === 4) {
      if (nodeData.value?.express_company) formData.value.shipCompany = nodeData.value.express_company
      if (nodeData.value?.express_no) formData.value.shipNo = nodeData.value.express_no
    }
  }

  async function loadOrder() {
    try {
      const res = await request.get(`/orders/${route.params.id}`)
      if (res.success && res.data) {
        const nodes = res.data.tracking_nodes || []
        allNodes.value = nodes
        if (initialLoad.value) { stepIndex.value = determineCurrentStep(nodes); initialLoad.value = false }
        const nc = STEPS[stepIndex.value]?.nodeCode
        const stepNodes = nodes.filter(n => n.node_code === nc)
        const node = stepNodes.length > 0 ? stepNodes[stepNodes.length - 1] : null
        currentNodeId.value = node?.id || null
        stepSubmitted.value = !!node
        nodeData.value = node ? { ...node } : node
        if (node) { note.value = node.operate_note || ''; photos.value = parsePhotos(node) }
        else { note.value = ''; photos.value = [] }
        if (res.data.items && res.data.items.length > 0 && equipmentData.value.length === 0) {
          initEquipmentData(res.data.items)
        }
        await loadEquipmentData()
        if (stepIndex.value >= 2) {
          const hasInspect = nodes.some(n => n.node_code === 'inspect')
          const hasRepair = nodes.some(n => n.node_code === 'repair')
          if (hasInspect && !hasRepair && equipmentData.value.length > 0) {
            const hasRealEquipData = equipmentData.value.some(item => {
              const ins = item.inspection_data || {}
              return (ins.first_stage_pre_pressure && ins.first_stage_pre_pressure.some(v => v != null)) ||
                (ins.first_stage_post_pressure && ins.first_stage_post_pressure.some(v => v != null)) ||
                (ins.second_stage_pre_resistance && ins.second_stage_pre_resistance.some(v => v != null)) ||
                (ins.second_stage_post_resistance && ins.second_stage_post_resistance.some(v => v != null))
            })
            if (!hasRealEquipData) {
              stepIndex.value = 1; subPageIndex.value = 0; stepSubmitted.value = false
            }
          }
        }
        orderData.value = res.data
        if (stepIndex.value === 0 && !stepSubmitted.value) {
          const ec = orderData.value?.express_company || ''
          const en = orderData.value?.express_no || ''
          if (ec) formData.value.expressCompany = ec
          if (en) formData.value.expressNo = en
        }
        if (stepIndex.value === 2) await loadServiceItems(res.data)
      }
    } catch (e) {
      console.error('loadOrder error:', e)
      ElMessage.error('加载订单失败')
    }
  }

  // ===== 图片处理 =====
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

  function triggerUpload(key) {
    const input = document.createElement('input')
    input.type = 'file'; input.accept = 'image/*'
    input.onchange = async (e) => {
      const file = e.target.files[0]
      if (!file) return
      ElMessage.info('正在压缩图片...')
      localPhotos.value = { ...localPhotos.value, [key]: await compressImage(file) }
    }
    input.click()
  }

  function triggerUploadMulti(key) {
    const input = document.createElement('input')
    input.type = 'file'; input.accept = 'image/*'; input.multiple = true
    input.onchange = async (e) => {
      const files = Array.from(e.target.files)
      if (!files.length) return
      ElMessage.info(`正在压缩 ${files.length} 张图片...`)
      const arr = [...localMultiPhotos.value[key]]
      for (const file of files) arr.push(await compressImage(file))
      localMultiPhotos.value[key] = arr
    }
    input.click()
  }

  async function deletePhoto(index) {
    const photo = photos.value[index]
    if (!currentNodeId.value || !photo.filename) return
    if (!confirm('确认删除此照片？')) return
    try {
      await request.delete(`/orders/${route.params.id}/nodes/${currentNodeId.value}/photo/${photo.filename}`)
      photos.value.splice(index, 1)
      ElMessage.success('照片已删除')
    } catch { ElMessage.error('删除失败') }
  }

  async function deletePhotoByType(type, indexInType) {
    const typePhotos = photos.value.filter(p => p.type === type)
    const target = typePhotos[indexInType]
    if (!target) return
    const idx = photos.value.findIndex(p => p === target)
    if (idx !== -1) await deletePhoto(idx)
  }

  // ===== 步骤提交 =====
  async function submitReceive() {
    submitting.value = true
    try {
      const photoList = []
      if (localPhotos.value.unbox) photoList.push({ type: 'unbox', data: localPhotos.value.unbox })
      if (localPhotos.value.unbox_opened) photoList.push({ type: 'unbox_opened', data: localPhotos.value.unbox_opened })
      const res = await request.put(`/orders/${route.params.id}/receive`, {
        note: note.value, express_company: formData.value.expressCompany,
        express_no: formData.value.expressNo, packaging_condition: formData.value.packaging,
        photos: photoList
      }, { timeout: 120000 })
      if (res.success) {
        ElMessage.success('确认收货成功')
        stepSubmitted.value = true
        localPhotos.value = { unbox: null, unbox_opened: null, ship: null }
        await loadOrderData()
      } else { ElMessage.error(res.message || '提交失败') }
    } catch (e) {
      ElMessage.error('提交失败: ' + (e.response?.data?.message || e.message || ''))
    } finally { submitting.value = false }
  }

  async function submitShip() {
    submitting.value = true
    try {
      const photoList = localPhotos.value.ship ? [localPhotos.value.ship] : []
      const res = await request.put(`/orders/${route.params.id}/ship`, {
        note: note.value, return_express_company: formData.value.shipCompany,
        return_express_no: formData.value.shipNo, photos: photoList
      }, { timeout: 120000 })
      if (res.success) {
        ElMessage.success('设备发出确认')
        stepSubmitted.value = true
        localPhotos.value.ship = null
        await loadOrderData()
      } else { ElMessage.error(res.message || '提交失败') }
    } catch (e) {
      ElMessage.error('提交失败: ' + (e.response?.data?.message || e.message || ''))
    } finally { submitting.value = false }
  }

  async function submitGeneric(code) {
    submitting.value = true
    try {
      const photoKeyMap = { inspect: 'inspect', repair: 'repair', qc: 'qc', complete: null }
      const photoKey = photoKeyMap[code]
      const photoList = photoKey ? (localMultiPhotos.value[photoKey] || []) : []
      const payload = { note: note.value }
      if (photoList.length > 0) payload.photos = photoList
      if (code === 'repair' && selectedServiceItems.value.length > 0) payload.selected_items = selectedServiceItems.value
      const res = await request.put(`/orders/${route.params.id}/${code}`, payload, { timeout: 120000 })
      if (res.success) {
        ElMessage.success(currentStep.value.shortLabel + ' 已提交')
        if (code === 'inspect') { pushNav(); stepSubmitted.value = true }
        else { stepSubmitted.value = true }
        if (photoKey) localMultiPhotos.value[photoKey] = []
        await loadOrderData()
      } else { ElMessage.error(res.message || '提交失败') }
    } catch (e) {
      ElMessage.error('提交失败: ' + (e.response?.data?.message || e.message || ''))
    } finally { submitting.value = false }
  }

  // ===== 导航 =====
  async function goBack() {
    if (navigating.value) return
    if (navHistory.value.length === 0) { router.push('/tech'); return }
    navigating.value = true
    const prev = navHistory.value.pop()
    stepIndex.value = prev.stepIndex
    subPageIndex.value = prev.subPageIndex
    doneSubPageIndex.value = prev.doneSubPageIndex
    stepSubmitted.value = false
    await loadOrderData()
    if (stepIndex.value === 1) await loadEquipmentData()
    navigating.value = false
  }

  async function nextStep() {
    if (stepIndex.value < STEPS.length - 1) {
      const currentState = {
        stepIndex: stepIndex.value, subPageIndex: subPageIndex.value,
        doneSubPageIndex: doneSubPageIndex.value, stepSubmitted: stepSubmitted.value
      }
      const topOfStack = navHistory.value.length > 0 ? navHistory.value[navHistory.value.length - 1] : null
      const isDuplicate = topOfStack &&
        topOfStack.stepIndex === currentState.stepIndex &&
        topOfStack.subPageIndex === currentState.subPageIndex
      if (!isDuplicate) pushNav()
      stepIndex.value++
      subPageIndex.value = 0
      const nc = STEPS[stepIndex.value]?.nodeCode
      const hasNode = allNodes.value.some(n => n.node_code === nc)
      stepSubmitted.value = hasNode
      await loadOrderData()
    }
  }

  // ===== PDF =====
  async function previewPdf() {
    pdfLoading.value = true
    try {
      const res = await request.post(`/orders/${route.params.id}/generate-report`)
      if (res.success) {
        const staffStore = useStaffStore()
        const resp = await fetch(`/selforder-api/console/orders/${route.params.id}/report-pdf`, {
          headers: { 'X-Staff-Token': staffStore.token }
        })
        if (!resp.ok) throw new Error('获取PDF失败')
        const blob = await resp.blob()
        window.open(URL.createObjectURL(blob), '_blank')
      } else { ElMessage.error(res.message || 'PDF生成失败') }
    } catch (e) {
      ElMessage.error('PDF生成失败: ' + (e.message || ''))
    } finally { pdfLoading.value = false }
  }

  async function downloadPdf() {
    pdfLoading.value = true
    try {
      const res = await request.post(`/orders/${route.params.id}/generate-report`)
      if (res.success) {
        const staffStore = useStaffStore()
        const resp = await fetch(`/selforder-api/console/orders/${route.params.id}/report-pdf?download=1`, {
          headers: { 'X-Staff-Token': staffStore.token }
        })
        if (!resp.ok) throw new Error('下载失败')
        const blob = await resp.blob()
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url; link.download = `order-${route.params.id}.pdf`; link.click()
        URL.revokeObjectURL(url)
      } else { ElMessage.error(res.message || 'PDF生成失败') }
    } catch (e) {
      ElMessage.error('PDF生成失败: ' + (e.message || ''))
    } finally { pdfLoading.value = false }
  }

  // ===== onMounted: build nav history =====
  onMounted(async () => {
    await loadOrder()
    if (stepIndex.value > 0) {
      const hasEquipmentData = equipmentData.value.length > 0 &&
        equipmentData.value.some(item => item.inspection_data && (
          (item.inspection_data.first_stage_serials && item.inspection_data.first_stage_serials.some(s => s && s.trim())) ||
          (item.inspection_data.second_stage_serials && item.inspection_data.second_stage_serials.some(s => s && s.trim())) ||
          (item.inspection_data.first_stage_pre_pressure && item.inspection_data.first_stage_pre_pressure.some(v => v != null)) ||
          (item.inspection_data.second_stage_pre_resistance && item.inspection_data.second_stage_pre_resistance.some(v => v != null)) ||
          (item.inspection_data.second_stage_post_resistance && item.inspection_data.second_stage_post_resistance.some(v => v != null))
        ))
      for (let i = 0; i < stepIndex.value; i++) {
        if (i === 1) {
          navHistory.value.push({ stepIndex: 1, subPageIndex: 0, doneSubPageIndex: 0, stepSubmitted: false })
          if (hasEquipmentData)
            navHistory.value.push({ stepIndex: 1, subPageIndex: 1, doneSubPageIndex: 0, stepSubmitted: true })
        } else {
          navHistory.value.push({ stepIndex: i, subPageIndex: 0, doneSubPageIndex: 0, stepSubmitted: true })
        }
      }
    }
  })

  // ===== Export composite object =====
  const ctx = {
    STEPS, courierList, returnCourierList,
    stepIndex, subPageIndex, doneSubPageIndex,
    stepSubmitted, navHistory, allNodes, initialLoad,
    note, photos, currentNodeId, nodeData,
    submitting, navigating,
    formData, localPhotos, localMultiPhotos,
    equipmentData, serviceItems, selectedServiceItems, serviceLoadFailed,
    orderData, previewUrl, pdfLoading,
    currentStep, isLastStep,
    // functions
    isStepDone, pushNav, goForwardSub, goForwardDone, goBackDoneSub,
    loadOrder, loadOrderData, loadEquipmentData, loadServiceItems,
    initEquipmentData, updateFirstStageArrays, updateSecondStageArrays,
    padArray, saveEquipmentData,
    parsePhotos, compressImage,
    triggerUpload, triggerUploadMulti, deletePhoto, deletePhotoByType,
    submitReceive, submitShip, submitGeneric,
    goBack, nextStep, previewPdf, downloadPdf,
    prefillFromNodeData,
    route, router
  }

  provide(WORKFLOW_INJECT_KEY, ctx)
  return ctx
}

export function useWorkflow() {
  return inject(WORKFLOW_INJECT_KEY)
}
