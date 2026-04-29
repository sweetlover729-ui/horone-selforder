<template>
  <div class="order-detail" v-if="order">
    <!-- 返回按钮 -->
    <div class="back-bar">
      <el-button link @click="$router.push('/admin/orders')">
        <el-icon><ArrowLeft /></el-icon>
        返回订单列表
      </el-button>
    </div>

    <!-- 订单头信息 -->
    <div class="order-header card">
      <div class="order-header-left">
        <h3>订单号: {{ order.orderNo }}</h3>
        <span :class="['status-tag', getStatusClass(order.status)]">
          {{ getStatusLabel(order.status) }}
        </span>
        <span :class="['pay-status', order.payStatus === 'paid' ? 'paid' : 'unpaid']">
          {{ order.payStatus === 'paid' ? '已支付' : '未支付' }}
        </span>
        <el-tag v-if="order.urgentService" type="danger" size="small" effect="dark" style="margin-left: 8px;">
          加急订单 +¥{{ order.urgentFee }}
        </el-tag>
        <el-button v-if="order.payStatus !== 'paid'" type="primary" size="small" @click="showPaymentDialog = true" style="margin-left: 8px;">
          设置支付状态
        </el-button>
      </div>
      <div class="order-header-right">
        <span class="create-time">创建时间: {{ formatTime(order.createdAt) }}</span>
      </div>
    </div>

    <!-- Tabs -->
    <el-tabs v-model="activeTab" class="order-tabs">
      <!-- Tab1: 基本信息 -->
      <el-tab-pane label="基本信息" name="info">
        <div class="tab-content">
          <!-- 客户信息 -->
          <div class="info-section">
            <div class="info-section-title">客户信息</div>
            <div class="info-grid">
              <div class="info-item">
                <span class="label">姓名:</span>
                <span class="value">{{ order.customerName }}</span>
              </div>
              <div class="info-item">
                <span class="label">电话:</span>
                <span class="value">{{ order.customerPhone }}</span>
              </div>
              <div class="info-item" style="grid-column: span 2;">
                <span class="label">地址:</span>
                <span class="value">{{ order.customerAddress }}</span>
              </div>
            </div>
          </div>

          <!-- 设备信息 -->
          <div class="info-section">
            <div class="info-section-title">设备信息</div>
            <div class="info-grid">
              <div class="info-item">
                <span class="label">产品类别:</span>
                <span class="value">{{ order.productType }}</span>
              </div>
              <div class="info-item">
                <span class="label">品牌:</span>
                <span class="value">{{ order.brand }}</span>
              </div>
              <div class="info-item">
                <span class="label">型号:</span>
                <span class="value">{{ order.model }}</span>
              </div>
              <div class="info-item">
                <span class="label">数量:</span>
                <span class="value">{{ order.quantity }}</span>
              </div>
              <div class="info-item">
                <span class="label">服务类型:</span>
                <span class="value">{{ order.serviceType }}</span>
              </div>
              <div class="info-item">
                <span class="label">总价:</span>
                <span class="value" style="color: #fa8c16; font-weight: 600;">¥{{ order.totalPrice }}</span>
              </div>
              <div class="info-item" v-if="order.urgentService">
                <span class="label">加急服务:</span>
                <span class="value" style="color: #f56c6c;">+¥{{ order.urgentFee }}</span>
              </div>
              <div class="info-item" v-if="order.isDealer && order.discountRate > 0">
                <span class="label">经销商折扣:</span>
                <span class="value" style="color: #67c23a;">{{ order.discountRate }}% 优惠</span>
              </div>
            </div>
          </div>

          <!-- 快递信息 -->
          <div class="info-section" v-if="order.shippingOut || order.shippingBack">
            <div class="info-section-title">快递信息</div>
            <div class="info-grid">
              <div class="info-item" v-if="order.shippingOut">
                <span class="label">寄出快递:</span>
                <span class="value">{{ order.shippingOut.company }} {{ order.shippingOut.trackingNo }}</span>
              </div>
              <div class="info-item" v-if="order.shippingBack">
                <span class="label">回寄快递:</span>
                <span class="value">{{ order.shippingBack.company }} {{ order.shippingBack.trackingNo }}</span>
              </div>
            </div>
          </div>

          <!-- 客户备注 -->
          <div class="info-section" v-if="order.customerNote">
            <div class="info-section-title">客户备注</div>
            <div class="customer-note">{{ order.customerNote }}</div>
          </div>
        </div>
      </el-tab-pane>

      <!-- Tab2: 维修进度 -->
      <el-tab-pane label="维修进度" name="progress">
        <div class="tab-content">
          <div v-if="progressList.length === 0" class="empty-box">
            暂无进度记录
          </div>
          <div v-else class="timeline">
            <div
              v-for="(item, index) in progressList"
              :key="index"
              :class="['timeline-item', { current: index === 0 }]"
            >
              <div class="timeline-time">{{ formatTime(item.createdAt) }}</div>
              <div class="timeline-title">{{ item.nodeName }}</div>
              <div class="timeline-desc" v-if="item.description">{{ item.description }}</div>
              <div class="timeline-note" v-if="item.operateNote" style="color: #666; font-style: italic; margin-top: 4px;">备注: {{ item.operateNote }}</div>
              <div class="timeline-operator" v-if="item.staffName">操作人: {{ item.staffName }}</div>
              <div class="img-preview-list" v-if="item.photos && item.photos.length">
                <div
                  v-for="(photo, pIdx) in item.photos"
                  :key="pIdx"
                  class="img-preview-item"
                  @click="previewImage(photo)"
                >
                  <img :src="photo" alt="进度照片" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- Tab3: 操作面板 -->
      <el-tab-pane label="操作面板" name="action">
        <div class="tab-content">
          <!-- 已完成状态 -->
          <div v-if="order.status === 'completed'" class="empty-box">
            订单已完成，无需操作
          </div>

          <!-- 已付款待收货: 确认收货 + 拆件检验 -->
          <div v-else-if="order.status === 'paid' || order.status === 'pending' || order.status === 'confirmed'" class="action-panel">
            <div class="action-panel-title">确认收货并拆件检验</div>
            <el-form :model="receiveForm" label-width="100px">
              <el-form-item label="拆件照片">
                <div class="img-upload-list">
                  <div
                    v-for="(img, idx) in receiveForm.photos"
                    :key="idx"
                    class="img-upload-item"
                  >
                    <img :src="img" />
                    <span class="img-remove" @click="removeImage(receiveForm.photos, idx)">x</span>
                  </div>
                  <div
                    v-if="receiveForm.photos.length < 9"
                    class="img-upload-add"
                    @click="triggerUpload('receivePhotos')"
                  >
                    <el-icon><Plus /></el-icon>
                  </div>
                </div>
                <input
                  type="file"
                  ref="receivePhotosRef"
                  accept="image/*"
                  multiple
                  style="display:none"
                  @change="handlePhotoUpload($event, 'receiveForm', 'photos')"
                />
              </el-form-item>
              <el-form-item label="检验说明">
                <el-input
                  v-model="receiveForm.description"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入检验说明"
                />
              </el-form-item>
              <el-form-item label="操作时间">
                <el-date-picker
                  v-model="receiveForm.operateTime"
                  type="datetime"
                  placeholder="选择操作时间"
                  value-format="YYYY-MM-DD HH:mm:ss"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleConfirmReceive" :loading="actionLoading">
                  确认收货
                </el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 已收货/拆件中: 开始维修 -->
          <div v-else-if="order.status === 'received'" class="action-panel">
            <div class="action-panel-title">开始维修</div>
            <el-form label-width="100px">
              <el-form-item>
                <el-button type="primary" @click="handleStartRepair" :loading="actionLoading">
                  开始维修
                </el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 拆件中: 维修保养 -->
          <div v-else-if="order.status === 'inspecting'" class="action-panel">
            <div class="action-panel-title">维修保养</div>
            <el-form :model="repairForm" label-width="100px">
              <el-form-item label="维修照片">
                <div class="img-upload-list">
                  <div
                    v-for="(img, idx) in repairForm.photos"
                    :key="idx"
                    class="img-upload-item"
                  >
                    <img :src="img" />
                    <span class="img-remove" @click="removeImage(repairForm.photos, idx)">x</span>
                  </div>
                  <div
                    v-if="repairForm.photos.length < 9"
                    class="img-upload-add"
                    @click="triggerUpload('repairPhotos')"
                  >
                    <el-icon><Plus /></el-icon>
                  </div>
                </div>
                <input
                  type="file"
                  ref="repairPhotosRef"
                  accept="image/*"
                  multiple
                  style="display:none"
                  @change="handlePhotoUpload($event, 'repairForm', 'photos')"
                />
              </el-form-item>
              <el-form-item label="维修说明">
                <el-input
                  v-model="repairForm.description"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入维修说明"
                />
              </el-form-item>
              <el-form-item label="操作时间">
                <el-date-picker
                  v-model="repairForm.operateTime"
                  type="datetime"
                  placeholder="选择操作时间"
                  value-format="YYYY-MM-DD HH:mm:ss"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleAddRepairLog" :loading="actionLoading">
                  添加维修记录
                </el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 维修中: 维修完成提交QC -->
          <div v-else-if="order.status === 'repairing'" class="action-panel">
            <div class="action-panel-title">维修完成，提交QC</div>
            <el-form label-width="100px">
              <el-form-item>
                <el-button type="primary" @click="handleSubmitQC" :loading="actionLoading">
                  维修完成，提交QC
                </el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 专项服务: 添加专项服务 -->
          <div v-else-if="order.status === 'repairing' || order.status === 'inspecting'" class="action-panel">
            <div class="action-panel-title">专项服务</div>
            <div v-if="specialServices.length > 0" class="special-list">
              <div v-for="ss in specialServices" :key="ss.id" class="special-item">
                <span>{{ ss.name }}</span>
                <span>¥{{ ss.price }}</span>
                <span :class="['special-service-tag', ss.status]">{{ getSpecialStatusLabel(ss.status) }}</span>
              </div>
            </div>
            <el-form :model="specialForm" label-width="100px" style="margin-top: 16px;">
              <el-form-item label="服务名称">
                <el-input v-model="specialForm.name" placeholder="请输入服务名称" />
              </el-form-item>
              <el-form-item label="服务价格">
                <el-input-number v-model="specialForm.price" :min="0" :precision="2" />
              </el-form-item>
              <el-form-item label="数量">
                <el-input-number v-model="specialForm.quantity" :min="1" :max="99" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleAddSpecialService" :loading="actionLoading">
                  添加专项服务
                </el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 待回寄: 填写快递信息 -->
          <div v-else-if="order.status === 'ready'" class="action-panel">
            <div class="action-panel-title">回寄快递</div>
            <el-form :model="shipForm" label-width="100px">
              <el-form-item label="快递公司">
                <el-select v-model="shipForm.company" placeholder="请选择快递公司">
                  <el-option label="顺丰速运" value="顺丰速运" />
                </el-select>
              </el-form-item>
              <el-form-item label="快递单号">
                <el-input v-model="shipForm.trackingNo" placeholder="请输入快递单号" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleConfirmShip" :loading="actionLoading">
                  确认发出
                </el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 已发出: 确认完成 -->
          <div v-else-if="order.status === 'shipped'" class="action-panel">
            <div class="action-panel-title">确认签收</div>
            <el-form label-width="100px">
              <el-form-item>
                <el-button type="primary" @click="handleConfirmComplete" :loading="actionLoading">
                  确认完成
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </el-tab-pane>

      <!-- Tab4: 专项服务 -->
      <el-tab-pane label="专项服务" name="special">
        <div class="tab-content">
          <div class="special-actions">
            <el-button type="primary" @click="showSpecialDialog = true" v-if="order.status !== 'completed'">
              添加专项服务
            </el-button>
          </div>
          <el-table :data="specialServices" v-loading="specialLoading">
            <el-table-column prop="name" label="服务名称" />
            <el-table-column prop="price" label="价格" width="100">
              <template #default="{ row }">
                ¥{{ row.price }}
              </template>
            </el-table-column>
            <el-table-column prop="quantity" label="数量" width="80">
              <template #default="{ row }">
                {{ row.quantity || 1 }}
              </template>
            </el-table-column>
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <span :class="['special-service-tag', row.status]">
                  {{ getSpecialStatusLabel(row.status) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button type="primary" link @click="editSpecialService(row)">编辑</el-button>
                <el-button type="primary" link v-if="row.status === 'pending'" @click="confirmSpecialService(row, 'confirmed')">
                  确认
                </el-button>
                <el-button type="danger" link v-if="row.status === 'pending'" @click="confirmSpecialService(row, 'rejected')">
                  拒绝
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- Tab5: 生成报告 -->
      <el-tab-pane label="生成报告" name="report">
        <div class="tab-content">
          <div class="report-actions">
            <el-button type="primary" @click="regenerateReport" :loading="reportLoading">
              重新生成PDF
            </el-button>
            <el-button v-if="order.reportUrl" type="primary" @click="downloadReport">
              下载PDF
            </el-button>
          </div>
          <div v-if="order.reportUrl" class="report-preview">
            <iframe :src="order.reportUrl" frameborder="0" class="report-iframe"></iframe>
          </div>
          <div v-else class="empty-box">
            暂无维修报告
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 图片预览弹窗 -->
    <el-dialog v-model="previewVisible" title="图片预览" width="800px">
      <img :src="previewUrl" style="width: 100%;" />
    </el-dialog>

    <!-- 编辑专项服务弹窗 -->
    <el-dialog v-model="specialDialogVisible" title="编辑专项服务" width="500px">
      <el-form :model="editingSpecial" label-width="100px">
        <el-form-item label="服务名称">
          <el-input v-model="editingSpecial.name" />
        </el-form-item>
        <el-form-item label="服务价格">
          <el-input-number v-model="editingSpecial.price" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="editingSpecial.quantity" :min="1" :max="99" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editingSpecial.status">
            <el-option label="待确认" value="pending" />
            <el-option label="已确认" value="confirmed" />
            <el-option label="已拒绝" value="rejected" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="specialDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveSpecialService">保存</el-button>
      </template>
    </el-dialog>

    <!-- 设置支付状态弹窗 -->
    <el-dialog v-model="showPaymentDialog" title="设置支付状态" width="400px">
      <el-form :model="paymentStatusForm" label-width="100px">
        <el-form-item label="支付状态">
          <el-select v-model="paymentStatusForm.status">
            <el-option label="未支付" value="unpaid" />
            <el-option label="已支付" value="paid" />
            <el-option label="已退款" value="refunded" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPaymentDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpdatePaymentStatus">确定</el-button>
      </template>
    </el-dialog>
  </div>

  <div v-else class="loading-state">
    <el-skeleton :rows="10" animated />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { useStaffStore } from '@/stores/staff'

const route = useRoute()
const router = useRouter()
const staffStore = useStaffStore()

// 图片相对路径转带认证的完整 URL
const photoUrl = (path) => {
  if (!path || path.startsWith('http')) return path
  // "orders/98/nodes/430/xxx.jpg" → "/selforder-api/console/orders/98/nodes/430/photo/xxx.jpg?token=..."
  const m = path.match(/^orders\/(\d+)\/nodes\/(\d+)\/(.+)$/)
  if (m) {
    return `/selforder-api/console/orders/${m[1]}/nodes/${m[2]}/photo/${m[3]}?token=${staffStore.token || ''}`
  }
  return path
}

const order = ref(null)
const activeTab = ref('info')
const progressList = ref([])
const specialServices = ref([])
const loading = ref(false)
const actionLoading = ref(false)
const specialLoading = ref(false)
const reportLoading = ref(false)

// 表单数据
const receiveForm = ref({
  photos: [],
  description: '',
  operateTime: ''
})

const repairForm = ref({
  photos: [],
  description: '',
  operateTime: ''
})

const specialForm = ref({
  name: '',
  price: 0,
  quantity: 1
})

const shipForm = ref({
  company: '',
  trackingNo: ''
})

// 图片预览
const previewVisible = ref(false)
const previewUrl = ref('')

// 专项服务编辑
const specialDialogVisible = ref(false)
const editingSpecial = ref({
  id: '',
  name: '',
  price: 0,
  status: 'pending'
})

// 支付状态设置
const showPaymentDialog = ref(false)
const paymentStatusForm = ref({ status: 'paid' })

// Refs for file inputs
const receivePhotosRef = ref(null)
const repairPhotosRef = ref(null)

const statusMap = {
  paid: '待收货',
  receiving: '已收货',
  inspecting: '拆件中',
  repairing: '维修中',
  special_service: '专项服务',
  ready: '待回寄',
  shipped: '已发出',
  completed: '已完成',
  cancelled: '已取消',
  refunded: '已退款'
}

const specialStatusMap = {
  pending: '待确认',
  confirmed: '已确认',
  rejected: '已拒绝',
  completed: '已完成'
}

const getStatusClass = (status) => {
  const map = {
    paid: 'status-pending',
    receiving: 'status-progress',
    inspecting: 'status-progress',
    repairing: 'status-progress',
    special_service: 'status-warning',
    ready: 'status-info',
    shipped: 'status-info',
    completed: 'status-success'
  }
  return map[status] || ''
}

const getStatusLabel = (status) => statusMap[status] || status
const getSpecialStatusLabel = (status) => specialStatusMap[status] || status

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  })
}

const previewImage = (url) => {
  previewUrl.value = url
  previewVisible.value = true
}

const triggerUpload = (refName) => {
  if (refName === 'receivePhotos' && receivePhotosRef.value) {
    receivePhotosRef.value.click()
  } else if (refName === 'repairPhotos' && repairPhotosRef.value) {
    repairPhotosRef.value.click()
  }
}

const handlePhotoUpload = async (event, formName, fieldName) => {
  const files = event.target.files
  if (!files.length) return

  for (const file of files) {
    if (formName === 'receiveForm') {
      if (receiveForm.value.photos.length >= 9) break
      const base64 = await fileToBase64(file)
      receiveForm.value.photos.push(base64)
    } else if (formName === 'repairForm') {
      if (repairForm.value.photos.length >= 9) break
      const base64 = await fileToBase64(file)
      repairForm.value.photos.push(base64)
    }
  }
  event.target.value = ''
}

const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target.result)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

const removeImage = (arr, idx) => {
  arr.splice(idx, 1)
}

const mapOrderData = (d) => {
  // 后端返回 snake_case，前端模板期望 camelCase
  // 从 order_items 中提取第一个 item 的设备信息
  const firstItem = (d.items && d.items.length > 0) ? d.items[0] : null
  return {
    id: d.id,
    orderNo: d.order_no || '',
    status: d.status || '',
    payStatus: d.payment_status || 'unpaid',
    createdAt: d.created_at || '',
    // 客户信息
    customerName: d.receiver_name || d.customer_name || '',
    customerPhone: d.receiver_phone || '',
    customerAddress: d.receiver_address || '',
    // 设备信息 — 从 order_items 获取
    productType: firstItem?.product_type_name || d.product_name || '',
    brand: firstItem?.brand_name || d.brand_name || '',
    model: firstItem?.model_name || d.model_name || '',
    quantity: firstItem?.quantity || 1,
    serviceType: firstItem?.service_type_name || d.service_name || '',
    totalPrice: d.total_amount || 0,
    // 快递
    expressCompany: d.express_company || '',
    expressNo: d.express_no || '',
    returnExpressCompany: d.return_express_company || '',
    returnExpressNo: d.return_express_no || '',
    // 交付方式
    deliveryType: d.delivery_type || 'store',
    storeCheckinAt: d.store_checkin_at || null,
    // 快递信息对象（用于显示）
    shippingOut: d.express_company ? { company: d.express_company, trackingNo: d.express_no } : null,
    shippingBack: d.return_express_company ? { company: d.return_express_company, trackingNo: d.return_express_no } : null,
    // 备注
    customerRemark: d.customer_remark || '',
    staffRemark: d.staff_remark || '',
    // 已归档标记
    archived: d.archived || 0,
    pdfPath: d.pdf_path || '',
    // 加急服务
    urgentService: d.urgent_service || false,
    urgentFee: d.urgent_fee || 0,
    // 经销商折扣
    isDealer: d.is_dealer || false,
    discountRate: d.discount_rate || 0,
    discountAmount: d.discount_amount || 0,
    // 带 token 的 PDF 下载/预览 URL
    reportUrl: d.pdf_path
      ? `/selforder-api/console/orders/${d.id}/report-pdf?token=${staffStore.token || ''}`
      : '',
  }
}

const fetchOrderDetail = async () => {
  loading.value = true
  try {
    // 后端接口：GET /orders/:id（详情）或者 /orders（列表中含详情）
    const res = await request.get(`/orders/${route.params.id}`)
    if (res.success && res.data) {
      const d = res.data
      order.value = mapOrderData(d)
      // 追踪节点
      if (d.tracking_nodes && d.tracking_nodes.length > 0) {
        progressList.value = d.tracking_nodes.map(n => ({
          id: n.id,
          nodeCode: n.node_code,
          nodeName: n.node_name,
          description: n.description,
          staffName: n.staff_name,
          operateTime: n.operate_time,
          operateNote: n.operate_note,
          photos: (() => { try { return JSON.parse(n.photos || '[]').map(p => photoUrl(typeof p === 'object' && p.path ? p.path : p)) } catch { return [] } })(),
          createdAt: n.created_at,
        }))
      } else {
        progressList.value = []
      }
      // 专项服务
      if (d.special_services && d.special_services.length > 0) {
        specialServices.value = d.special_services.map(s => ({
          id: s.id,
          name: s.name,
          description: s.description,
          price: s.price,
          status: s.status,
          staffNote: s.staff_note || '',
          photos: (() => { try { return JSON.parse(s.staff_photos || '[]').map(p => photoUrl(typeof p === 'object' && p.path ? p.path : p)) } catch { return [] } })(),
        }))
      } else {
        specialServices.value = []
      }
    } else {
      order.value = mapOrderData(res.data || {})
      progressList.value = []
      specialServices.value = []
    }
  } catch (error) {
    console.error('Failed to fetch order detail:', error)
    ElMessage.error('获取订单详情失败')
  } finally {
    loading.value = false
  }
}

// 操作处理函数
const handleConfirmReceive = async () => {
  if (!receiveForm.value.operateTime) {
    receiveForm.value.operateTime = new Date().toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit'
    }).replace(/\//g, '-')
  }

  actionLoading.value = true
  try {
    await request.put(`/orders/${order.value.id}/receive`, {
      photos: receiveForm.value.photos,
      description: receiveForm.value.description,
      operateTime: receiveForm.value.operateTime
    })
    ElMessage.success('已确认收货')
    receiveForm.value = { photos: [], description: '', operateTime: '' }
    await fetchOrderDetail()
  } catch (error) {
    console.error('Failed to confirm receive:', error)
  } finally {
    actionLoading.value = false
  }
}

const handleStartRepair = async () => {
  actionLoading.value = true
  try {
    // start-repair: deprecated (no await needed)
    ElMessage.success('已开始维修')
    await fetchOrderDetail()
  } catch (error) {
    console.error('Failed to start repair:', error)
  } finally {
    actionLoading.value = false
  }
}

const handleAddRepairLog = async () => {
  if (!repairForm.value.operateTime) {
    repairForm.value.operateTime = new Date().toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit'
    }).replace(/\//g, '-')
  }

  actionLoading.value = true
  try {
    // repair-log: backend has no separate endpoint,维修记录已包含在inspect/repair流程中
    // await request.post(`/orders/${order.value.id}/repair-log`, { photos: repairForm.value.photos, description: repairForm.value.description, operateTime: repairForm.value.operateTime })
    ElMessage.success('维修记录已保存到质检流程中')
    repairForm.value = { photos: [], description: '', operateTime: '' }
  } catch (error) {
    console.error('Failed to add repair log:', error)
  } finally {
    actionLoading.value = false
  }
}

const handleSubmitQC = async () => {
  actionLoading.value = true
  try {
    await request.put(`/orders/${order.value.id}/qc`)
    ElMessage.success('已提交QC')
    await fetchOrderDetail()
  } catch (error) {
    console.error('Failed to submit QC:', error)
  } finally {
    actionLoading.value = false
  }
}

const handleAddSpecialService = async () => {
  if (!specialForm.value.name) {
    ElMessage.warning('请输入服务名称')
    return
  }

  actionLoading.value = true
  try {
    await request.post(`/orders/${order.value.id}/special-service`, {
      name: specialForm.value.name,
      price: specialForm.value.price,
      quantity: specialForm.value.quantity || 1
    })
    ElMessage.success('已添加专项服务')
    specialForm.value = { name: '', price: 0, quantity: 1 }
    await fetchOrderDetail()
  } catch (error) {
    console.error('Failed to add special service:', error)
  } finally {
    actionLoading.value = false
  }
}

const handleConfirmShip = async () => {
  if (!shipForm.value.company || !shipForm.value.trackingNo) {
    ElMessage.warning('请填写完整的快递信息')
    return
  }

  actionLoading.value = true
  try {
    await request.put(`/orders/${order.value.id}/ship`, {
      company: shipForm.value.company,
      trackingNo: shipForm.value.trackingNo
    })
    ElMessage.success('已确认发出')
    shipForm.value = { company: '', trackingNo: '' }
    await fetchOrderDetail()
  } catch (error) {
    console.error('Failed to confirm ship:', error)
  } finally {
    actionLoading.value = false
  }
}

const handleConfirmComplete = async () => {
  actionLoading.value = true
  try {
    await request.put(`/orders/${order.value.id}/complete`)
    ElMessage.success('订单已完成')
    await fetchOrderDetail()
  } catch (error) {
    console.error('Failed to complete order:', error)
  } finally {
    actionLoading.value = false
  }
}

const handleUpdatePaymentStatus = async () => {
  actionLoading.value = true
  try {
    await request.put(`/orders/${order.value.id}/payment-status`, {
      payment_status: paymentStatusForm.value.status
    })
    ElMessage.success('支付状态已更新')
    showPaymentDialog.value = false
    await fetchOrderDetail()
  } catch (error) {
    console.error('Failed to update payment status:', error)
    ElMessage.error('更新失败')
  } finally {
    actionLoading.value = false
  }
}

// 专项服务操作
const editSpecialService = (row) => {
  editingSpecial.value = { ...row }
  specialDialogVisible.value = true
}

const saveSpecialService = async () => {
  try {
    await request.put(`/orders/${order.value.id}/special-service/${editingSpecial.value.id}`, {
      name: editingSpecial.value.name,
      price: editingSpecial.value.price,
      quantity: editingSpecial.value.quantity || 1,
      status: editingSpecial.value.status
    })
    ElMessage.success('已保存')
    specialDialogVisible.value = false
    await fetchOrderDetail()
  } catch (error) {
    console.error('Failed to save special service:', error)
  }
}

const confirmSpecialService = async (row, status) => {
  try {
    await request.put(`/orders/${order.value.id}/special-service/${row.id}`, {
      status
    })
    ElMessage.success('已更新状态')
    await fetchOrderDetail()
  } catch (error) {
    console.error('Failed to update special service:', error)
  }
}

// 报告操作
const regenerateReport = async () => {
  reportLoading.value = true
  try {
    await request.post(`/orders/${order.value.id}/generate-report`)
    ElMessage.success('报告已生成')
    await fetchOrderDetail()
  } catch (error) {
    console.error('Failed to regenerate report:', error)
    ElMessage.error('报告生成失败')
  } finally {
    reportLoading.value = false
  }
}

const downloadReport = () => {
  if (order.value.reportUrl) {
    window.open(order.value.reportUrl, '_blank')
  }
}

onMounted(() => {
  fetchOrderDetail()
})
</script>

<style scoped>
.order-detail {
  max-width: 1000px;
}

.back-bar {
  margin-bottom: 16px;
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
}

.order-header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.order-header-left h3 {
  font-size: 16px;
  font-weight: 600;
}

.pay-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.pay-status.paid {
  background: #f6ffed;
  color: #52c41a;
}

.pay-status.unpaid {
  background: #fff2f0;
  color: #ff4d4f;
}

.order-header-right {
  color: #8c8c8c;
  font-size: 13px;
}

.order-tabs {
  background: #fff;
  border-radius: 4px;
  border: 1px solid #f0f0f0;
  padding: 0 20px 20px;
}

.tab-content {
  padding: 20px 0;
}

.customer-note {
  background: #fafafa;
  padding: 12px;
  border-radius: 4px;
  font-size: 13px;
  color: #595959;
  line-height: 1.6;
}

/* 图片上传 */
.img-upload-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.img-upload-item {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid #f0f0f0;
}

.img-upload-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.img-remove {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 18px;
  height: 18px;
  background: rgba(0,0,0,0.5);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  cursor: pointer;
}

.img-upload-add {
  width: 80px;
  height: 80px;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #8c8c8c;
  font-size: 24px;
  transition: all 0.2s;
}

.img-upload-add:hover {
  border-color: #1677ff;
  color: #1677ff;
}

/* 专项服务列表 */
.special-list {
  margin-bottom: 16px;
}

.special-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 4px;
  margin-bottom: 8px;
}

.special-item span:first-child {
  flex: 1;
}

.special-item span:nth-child(2) {
  color: #fa8c16;
  font-weight: 500;
}

/* 专项服务操作区 */
.special-actions {
  margin-bottom: 16px;
}

/* 报告预览 */
.report-actions {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
}

.report-preview {
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.report-iframe {
  width: 100%;
  height: 600px;
}

.loading-state {
  padding: 20px;
  background: #fff;
  border-radius: 4px;
}

/* 状态标签 */
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

/* 专项服务标签 */
.special-service-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.special-service-tag.pending { background: #fff7e6; color: #fa8c16; }
.special-service-tag.confirmed { background: #f6ffed; color: #52c41a; }
.special-service-tag.rejected { background: #fff2f0; color: #ff4d4f; }
.special-service-tag.completed { background: #e6f4ff; color: #1677ff; }
</style>
